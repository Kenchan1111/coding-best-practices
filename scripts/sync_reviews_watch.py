#!/usr/bin/env python3
from __future__ import annotations

import argparse
import ctypes
import errno
import json
import os
import select
import struct
import subprocess
import sys
import time
from pathlib import Path

from knowledge_os import GLOBAL_HANDOFF_DIR, ROOT, discover_agents

SYNC_SCRIPT = ROOT / "scripts" / "sync_reviews.py"
WATCH_SUFFIXES = (".md", ".md.receipt.json", ".md.change-receipt.json")
SKIP_DIR_NAMES = {
    ".git",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    "__pycache__",
    "node_modules",
}
SKIP_RELATIVE_DIRS = {
    ("knowledge", "80_summaries"),
}

INOTIFY_MASK = (
    0x00000008  # IN_CLOSE_WRITE
    | 0x00000040  # IN_MOVED_FROM
    | 0x00000080  # IN_MOVED_TO
    | 0x00000100  # IN_CREATE
    | 0x00000200  # IN_DELETE
    | 0x00000400  # IN_DELETE_SELF
    | 0x00000800  # IN_MOVE_SELF
)
IN_CREATE = 0x00000100
IN_MOVED_TO = 0x00000080
IN_ISDIR = 0x40000000
IN_IGNORED = 0x00008000
EVENT_STRUCT = struct.Struct("iIII")


def _is_under_skipped_dir(path: Path) -> bool:
    try:
        relative_parts = path.relative_to(ROOT).parts
    except ValueError:
        relative_parts = path.parts
    for skipped in SKIP_RELATIVE_DIRS:
        if relative_parts[: len(skipped)] == skipped:
            return True
    return any(part in SKIP_DIR_NAMES for part in relative_parts)


def is_watch_filename(path: Path) -> bool:
    if _is_under_skipped_dir(path):
        return False
    if ".tmp." in path.name:
        return False
    return any(path.name.endswith(suffix) for suffix in WATCH_SUFFIXES)


def should_watch_path(path: Path) -> bool:
    if not path.is_file():
        return False
    return is_watch_filename(path)


def file_fingerprint(path: Path) -> list[int] | None:
    try:
        stat_result = path.stat()
    except FileNotFoundError:
        return None
    return [stat_result.st_mtime_ns, stat_result.st_size]


def iter_watch_paths(root: Path = ROOT):
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [name for name in dirnames if name not in SKIP_DIR_NAMES]
        base = Path(dirpath)
        for filename in filenames:
            path = base / filename
            if should_watch_path(path):
                yield path


class InotifyUnavailable(RuntimeError):
    pass


class InotifyTree:
    def __init__(self, root: Path):
        self.root = root
        try:
            self.libc = ctypes.CDLL("libc.so.6", use_errno=True)
        except OSError as exc:
            raise InotifyUnavailable(str(exc)) from exc
        self.libc.inotify_init1.argtypes = [ctypes.c_int]
        self.libc.inotify_init1.restype = ctypes.c_int
        self.libc.inotify_add_watch.argtypes = [ctypes.c_int, ctypes.c_char_p, ctypes.c_uint32]
        self.libc.inotify_add_watch.restype = ctypes.c_int

        fd = self.libc.inotify_init1(os.O_NONBLOCK | os.O_CLOEXEC)
        if fd < 0:
            error = ctypes.get_errno()
            raise InotifyUnavailable(os.strerror(error))
        self.fd = fd
        self.watch_paths: dict[int, Path] = {}

    def close(self) -> None:
        os.close(self.fd)

    def add_watch(self, path: Path) -> None:
        if _is_under_skipped_dir(path):
            return
        wd = self.libc.inotify_add_watch(self.fd, os.fsencode(path), INOTIFY_MASK)
        if wd < 0:
            error = ctypes.get_errno()
            if error in {errno.ENOENT, errno.ENOTDIR, errno.EACCES}:
                return
            raise OSError(error, os.strerror(error), str(path))
        self.watch_paths[wd] = path

    def add_tree(self, path: Path) -> None:
        if _is_under_skipped_dir(path) or not path.is_dir():
            return
        for dirpath, dirnames, _filenames in os.walk(path):
            dirnames[:] = [name for name in dirnames if name not in SKIP_DIR_NAMES]
            self.add_watch(Path(dirpath))

    def wait_for_relevant_event(self, timeout: float | None = None) -> bool:
        ready, _write_ready, _errors = select.select([self.fd], [], [], timeout)
        if not ready:
            return False

        relevant = False
        while True:
            try:
                payload = os.read(self.fd, 65536)
            except BlockingIOError:
                break
            if not payload:
                break

            offset = 0
            while offset + EVENT_STRUCT.size <= len(payload):
                wd, mask, _cookie, name_length = EVENT_STRUCT.unpack_from(payload, offset)
                offset += EVENT_STRUCT.size
                raw_name = payload[offset: offset + name_length].rstrip(b"\0")
                offset += name_length

                if mask & IN_IGNORED:
                    self.watch_paths.pop(wd, None)
                    continue

                base_path = self.watch_paths.get(wd)
                if base_path is None:
                    continue

                event_path = base_path / os.fsdecode(raw_name) if raw_name else base_path
                if (mask & IN_ISDIR) and (mask & (IN_CREATE | IN_MOVED_TO)):
                    self.add_tree(event_path)
                if is_watch_filename(event_path):
                    relevant = True

        return relevant


def capture_snapshot() -> dict[str, object]:
    snapshot: dict[str, object] = {
        "__agents__": list(discover_agents()),
        "__global_handoff_exists__": GLOBAL_HANDOFF_DIR.exists(),
        "__files__": {},
    }
    files: dict[str, list[int]] = snapshot["__files__"]  # type: ignore[assignment]

    for path in sorted(iter_watch_paths(ROOT)):
        fingerprint = file_fingerprint(path)
        if fingerprint is None:
            continue
        files[path.relative_to(ROOT).as_posix()] = fingerprint

    return snapshot


def sync_once() -> int:
    result = subprocess.run([sys.executable, str(SYNC_SCRIPT), "--once"], check=False, cwd=str(ROOT))
    return result.returncode


def run_initial_sync() -> None:
    initial_returncode = sync_once()
    if initial_returncode != 0:
        print(
            "Initial review sync failed "
            f"(returncode={initial_returncode}) - watcher will stay alive and wait for new changes.",
            file=sys.stderr,
            flush=True,
        )


def watch_poll_loop(poll_seconds: float, debounce_seconds: float) -> int:
    print(
        "Review sync watcher started in polling mode - "
        f"poll={poll_seconds}s debounce={debounce_seconds}s root={ROOT}",
        flush=True,
    )
    print(
        "Watching repo Markdown and review receipt sidecars: "
        f"suffixes={','.join(WATCH_SUFFIXES)}",
        flush=True,
    )

    run_initial_sync()
    last_applied = capture_snapshot()
    pending_snapshot: str | None = None
    pending_since = 0.0

    while True:
        current = capture_snapshot()
        current_serialized = json.dumps(current, sort_keys=True)
        applied_serialized = json.dumps(last_applied, sort_keys=True)

        if current_serialized == applied_serialized:
            pending_snapshot = None
            pending_since = 0.0
            time.sleep(poll_seconds)
            continue

        if pending_snapshot != current_serialized:
            pending_snapshot = current_serialized
            pending_since = time.monotonic()
            time.sleep(poll_seconds)
            continue

        if time.monotonic() - pending_since < debounce_seconds:
            time.sleep(poll_seconds)
            continue

        print("Change detected in repo Markdown/review sources - running sync.", flush=True)
        returncode = sync_once()
        last_applied = capture_snapshot()
        pending_snapshot = None
        pending_since = 0.0
        if returncode != 0:
            print(
                "Review sync failed "
                f"(returncode={returncode}) - waiting for the next source change before retrying.",
                file=sys.stderr,
                flush=True,
            )
        time.sleep(poll_seconds)


def watch_inotify_loop(debounce_seconds: float) -> int:
    print(
        "Review sync watcher started in inotify mode - "
        f"debounce={debounce_seconds}s root={ROOT}",
        flush=True,
    )
    print(
        "Watching repo Markdown and review receipt sidecars: "
        f"suffixes={','.join(WATCH_SUFFIXES)}",
        flush=True,
    )

    run_initial_sync()
    tree = InotifyTree(ROOT)
    try:
        tree.add_tree(ROOT)
        while True:
            if not tree.wait_for_relevant_event():
                continue

            quiet_since = time.monotonic()
            while True:
                remaining = max(0.0, debounce_seconds - (time.monotonic() - quiet_since))
                if remaining == 0.0:
                    break
                if tree.wait_for_relevant_event(timeout=remaining):
                    quiet_since = time.monotonic()

            print("Change detected in repo Markdown/review sources - running sync.", flush=True)
            returncode = sync_once()
            if returncode != 0:
                print(
                    "Review sync failed "
                    f"(returncode={returncode}) - waiting for the next source change before retrying.",
                    file=sys.stderr,
                    flush=True,
                )
    finally:
        tree.close()


def watch_loop(poll_seconds: float, debounce_seconds: float, backend: str) -> int:
    if backend in {"auto", "inotify"}:
        try:
            return watch_inotify_loop(debounce_seconds)
        except InotifyUnavailable as exc:
            if backend == "inotify":
                print(f"inotify unavailable: {exc}", file=sys.stderr, flush=True)
                return 1
            print(f"inotify unavailable, falling back to polling: {exc}", file=sys.stderr, flush=True)
    return watch_poll_loop(poll_seconds, debounce_seconds)


def main() -> int:
    parser = argparse.ArgumentParser(description="Watcher auto pour la sync review du repo.")
    parser.add_argument(
        "--backend",
        choices=("auto", "inotify", "poll"),
        default="auto",
        help="Backend de surveillance. auto utilise inotify si disponible, sinon polling.",
    )
    parser.add_argument("--poll-seconds", type=float, default=2.0, help="Intervalle de polling en secondes.")
    parser.add_argument(
        "--debounce-seconds",
        type=float,
        default=1.0,
        help="Fenetre de debounce avant sync.",
    )
    args = parser.parse_args()
    return watch_loop(args.poll_seconds, args.debounce_seconds, args.backend)


if __name__ == "__main__":
    sys.exit(main())
