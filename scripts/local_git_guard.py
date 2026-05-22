#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent.parent
DEFAULT_POLICY = ROOT / "ops" / "local_git_policy.json"


@dataclass(frozen=True)
class LocalRoot:
    name: str
    path: str
    classification: str
    reason: str


def now_local() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def atomic_write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(f"{path.suffix}.tmp.{os.getpid()}")
    tmp.write_text(content, encoding="utf-8")
    tmp.replace(path)


def save_json(path: Path, payload: dict[str, Any]) -> None:
    atomic_write_text(path, json.dumps(payload, indent=2, ensure_ascii=False) + "\n")


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def leaf_hash(kind: str, rel_path: str, digest: str) -> str:
    return sha256_bytes(f"{kind}\x00{rel_path}\x00{digest}".encode("utf-8"))


def compute_merkle_root(leaf_hashes: list[str]) -> str:
    if not leaf_hashes:
        return sha256_bytes(b"")
    level = list(leaf_hashes)
    while len(level) > 1:
        if len(level) % 2 == 1:
            # CVE-2012-2459 mitigation: use a deterministic padding hash
            # that can never collide with a legitimate leaf hash.
            level.append(sha256_bytes(b"__MERKLE_PAD__"))
        next_level: list[str] = []
        for index in range(0, len(level), 2):
            next_level.append(sha256_bytes((level[index] + level[index + 1]).encode("ascii")))
        level = next_level
    return level[0]


def resolve_repo_root(repo_root: str | None = None) -> Path:
    if repo_root:
        return Path(repo_root).expanduser().resolve()
    return ROOT


def resolve_policy_path(repo_root: Path, policy_file: str | None) -> Path:
    if policy_file:
        return Path(policy_file).expanduser().resolve()
    return repo_root / DEFAULT_POLICY.relative_to(ROOT)


def git_lines(repo_root: Path, *args: str) -> list[str]:
    process = subprocess.run(
        ["git", *args],
        cwd=repo_root,
        text=True,
        capture_output=True,
        check=False,
    )
    if process.returncode != 0:
        raise RuntimeError((process.stderr or process.stdout).strip() or f"git {' '.join(args)} failed")
    return [line.strip() for line in process.stdout.splitlines() if line.strip()]


def git_add(repo_root: Path, paths: list[Path]) -> None:
    if not paths:
        return
    subprocess.run(
        ["git", "add", "--", *[str(path.relative_to(repo_root)) for path in paths]],
        cwd=repo_root,
        text=True,
        capture_output=True,
        check=True,
    )


def git_rev_parse(repo_root: Path) -> str:
    try:
        return git_lines(repo_root, "rev-parse", "HEAD")[0]
    except Exception:
        return "unavailable"


def git_status_short(repo_root: Path) -> list[str]:
    try:
        return git_lines(repo_root, "status", "--short")
    except Exception:
        return []


def load_policy(repo_root: Path, policy_path: Path) -> dict[str, Any]:
    payload = load_json(policy_path)
    errors: list[str] = []
    if payload.get("policy_name") != "local_git_manifested":
        errors.append("policy_name must be local_git_manifested")
    roots = payload.get("local_roots")
    if not isinstance(roots, list) or not roots:
        errors.append("local_roots must be a non-empty list")
    for key in ("manifest_dir", "summary_manifest", "pushable_manifest", "ignore_rules"):
        if key not in payload:
            errors.append(f"missing policy key: {key}")
    if errors:
        raise RuntimeError("invalid local_git policy: " + "; ".join(errors))
    return payload


def policy_local_roots(policy: dict[str, Any]) -> list[LocalRoot]:
    roots: list[LocalRoot] = []
    for item in policy["local_roots"]:
        roots.append(
            LocalRoot(
                name=item["name"],
                path=item["path"].rstrip("/"),
                classification=item["classification"],
                reason=item["reason"],
            )
        )
    return roots


def root_manifest_path(repo_root: Path, policy: dict[str, Any], local_root: LocalRoot) -> Path:
    return repo_root / policy["manifest_dir"] / f"{local_root.name}.json"


def summary_manifest_path(repo_root: Path, policy: dict[str, Any]) -> Path:
    return repo_root / policy["summary_manifest"]


def pushable_manifest_path(repo_root: Path, policy: dict[str, Any]) -> Path:
    return repo_root / policy["pushable_manifest"]


def canonical_local_roots(policy: dict[str, Any]) -> list[str]:
    return [root.path for root in policy_local_roots(policy)]


def under_prefix(rel_path: str, prefixes: list[str]) -> bool:
    for prefix in prefixes:
        normalized = prefix.rstrip("/")
        if rel_path == normalized or rel_path.startswith(normalized + "/"):
            return True
    return False


def ensure_ignore_rules(repo_root: Path, policy: dict[str, Any]) -> list[str]:
    ignore_path = repo_root / ".gitignore"
    if not ignore_path.exists():
        return [".gitignore is missing"]
    lines = ignore_path.read_text(encoding="utf-8").splitlines()
    errors: list[str] = []
    for rule in policy["ignore_rules"]:
        if rule not in lines:
            errors.append(f"missing ignore rule in .gitignore: {rule}")
    return errors


def tracked_local_git_violations(repo_root: Path, local_roots: list[LocalRoot]) -> list[str]:
    violations: list[str] = []
    for root in local_roots:
        violations.extend(git_lines(repo_root, "ls-files", "--cached", "--", root.path))
    return sorted(set(violations))


def staged_local_git_violations(repo_root: Path, local_roots: list[LocalRoot]) -> list[str]:
    staged = git_lines(repo_root, "diff", "--cached", "--name-status")
    prefixes = [root.path for root in local_roots]
    violations: set[str] = set()
    for line in staged:
        if "\t" not in line:
            continue
        status, rel_path = line.split("\t", 1)
        if status == "D":
            continue
        if under_prefix(rel_path, prefixes):
            violations.add(rel_path)
    return sorted(violations)


def walk_local_root(repo_root: Path, local_root: LocalRoot) -> dict[str, Any]:
    root_path = repo_root / local_root.path
    directories: list[dict[str, str]] = []
    files: list[dict[str, Any]] = []
    symlinks: list[dict[str, Any]] = []
    leaves: list[str] = []

    if not root_path.exists():
        return {
            "version": "1",
            "policy_name": "local_git_manifested",
            "root_name": local_root.name,
            "root_path": local_root.path,
            "classification": local_root.classification,
            "reason": local_root.reason,
            "generated_at_utc": now_utc(),
            "generated_at_local": now_local(),
            "exists": False,
            "directory_count": 0,
            "file_count": 0,
            "symlink_count": 0,
            "total_bytes": 0,
            "merkle_root": compute_merkle_root([]),
            "directories": [],
            "files": [],
            "symlinks": [],
        }

    for path in sorted(root_path.rglob("*")):
        rel = path.relative_to(root_path).as_posix()
        if path.is_symlink():
            target = str(path.readlink())
            digest = sha256_bytes(target.encode("utf-8"))
            entry = {
                "path": rel,
                "target": target,
                "sha256": digest,
                "leaf_hash": leaf_hash("symlink", rel, digest),
            }
            symlinks.append(entry)
            leaves.append(entry["leaf_hash"])
            continue
        if path.is_dir():
            directories.append({"path": rel})
            continue
        if not path.is_file():
            continue
        digest = sha256_file(path)
        entry = {
            "path": rel,
            "size_bytes": path.stat().st_size,
            "sha256": digest,
            "leaf_hash": leaf_hash("file", rel, digest),
        }
        files.append(entry)
        leaves.append(entry["leaf_hash"])

    return {
        "version": "1",
        "policy_name": "local_git_manifested",
        "root_name": local_root.name,
        "root_path": local_root.path,
        "classification": local_root.classification,
        "reason": local_root.reason,
        "generated_at_utc": now_utc(),
        "generated_at_local": now_local(),
        "exists": True,
        "directory_count": len(directories),
        "file_count": len(files),
        "symlink_count": len(symlinks),
        "total_bytes": sum(entry["size_bytes"] for entry in files),
        "merkle_root": compute_merkle_root(leaves),
        "directories": directories,
        "files": files,
        "symlinks": symlinks,
    }


def pushable_entry(repo_root: Path, rel_path: str) -> dict[str, Any] | None:
    full_path = repo_root / rel_path
    if full_path.is_symlink():
        target = str(full_path.readlink())
        digest = sha256_bytes(target.encode("utf-8"))
        return {
            "path": rel_path,
            "kind": "symlink",
            "size_bytes": len(target.encode("utf-8")),
            "sha256": digest,
            "target": target,
            "leaf_hash": leaf_hash("symlink", rel_path, digest),
        }
    if not full_path.is_file():
        return None
    digest = sha256_file(full_path)
    return {
        "path": rel_path,
        "kind": "file",
        "size_bytes": full_path.stat().st_size,
        "sha256": digest,
        "leaf_hash": leaf_hash("file", rel_path, digest),
    }


def build_pushable_manifest(repo_root: Path, policy: dict[str, Any]) -> dict[str, Any]:
    local_prefixes = canonical_local_roots(policy)
    excluded_prefixes = [item.rstrip("/") for item in policy.get("exclude_from_pushable_manifest", [])]
    tracked = git_lines(repo_root, "ls-files", "--cached")
    entries: list[dict[str, Any]] = []
    for rel_path in tracked:
        if under_prefix(rel_path, local_prefixes):
            continue
        if under_prefix(rel_path, excluded_prefixes):
            continue
        entry = pushable_entry(repo_root, rel_path)
        if entry is not None:
            entries.append(entry)
    entries.sort(key=lambda item: item["path"])
    git_head = git_rev_parse(repo_root)
    reviewed_revision = f"{git_head}+dirty" if git_status_short(repo_root) else git_head
    return {
        "version": "1",
        "policy_name": "local_git_manifested",
        "generated_at_utc": now_utc(),
        "generated_at_local": now_local(),
        "git_head": git_head,
        "reviewed_revision": reviewed_revision,
        "file_selection": "git ls-files --cached minus local_git roots and excluded manifest self",
        "file_count": len(entries),
        "total_bytes": sum(entry["size_bytes"] for entry in entries),
        "merkle_root": compute_merkle_root([entry["leaf_hash"] for entry in entries]),
        "files": entries,
    }


def global_local_merkle_root(items: list[dict[str, Any]]) -> str:
    leaves = [
        sha256_bytes(
            (
                f"{item['name']}\x00{item['path']}\x00{item['merkle_root']}\x00"
                f"{item['file_count']}\x00{item['symlink_count']}\x00{item['total_bytes']}"
            ).encode("utf-8")
        )
        for item in items
    ]
    return compute_merkle_root(leaves)


def build_summary_manifest(
    repo_root: Path,
    policy: dict[str, Any],
    root_manifests: list[dict[str, Any]],
    pushable_manifest: dict[str, Any],
) -> dict[str, Any]:
    items = [
        {
            "name": item["root_name"],
            "path": item["root_path"],
            "classification": item["classification"],
            "manifest_path": str(
                root_manifest_path(
                    repo_root,
                    policy,
                    LocalRoot(item["root_name"], item["root_path"], item["classification"], item["reason"]),
                ).relative_to(repo_root)
            ),
            "exists": item["exists"],
            "directory_count": item["directory_count"],
            "file_count": item["file_count"],
            "symlink_count": item["symlink_count"],
            "total_bytes": item["total_bytes"],
            "merkle_root": item["merkle_root"],
        }
        for item in root_manifests
    ]
    git_head = git_rev_parse(repo_root)
    reviewed_revision = f"{git_head}+dirty" if git_status_short(repo_root) else git_head
    return {
        "version": "1",
        "policy_name": "local_git_manifested",
        "generated_at_utc": now_utc(),
        "generated_at_local": now_local(),
        "git_head": git_head,
        "reviewed_revision": reviewed_revision,
        "local_roots": items,
        "global_local_merkle_root": global_local_merkle_root(items),
        "pushable_manifest_path": str(pushable_manifest_path(repo_root, policy).relative_to(repo_root)),
        "pushable_merkle_root": pushable_manifest["merkle_root"],
    }


def build_manifests(repo_root: Path, policy: dict[str, Any], *, stage_manifests: bool) -> list[Path]:
    written: list[Path] = []
    root_specs = policy_local_roots(policy)
    root_manifests = [walk_local_root(repo_root, root) for root in root_specs]
    for root, manifest in zip(root_specs, root_manifests):
        path = root_manifest_path(repo_root, policy, root)
        save_json(path, manifest)
        written.append(path)
    pushable = build_pushable_manifest(repo_root, policy)
    pushable_path = pushable_manifest_path(repo_root, policy)
    save_json(pushable_path, pushable)
    written.append(pushable_path)
    summary = build_summary_manifest(repo_root, policy, root_manifests, pushable)
    summary_path = summary_manifest_path(repo_root, policy)
    save_json(summary_path, summary)
    written.append(summary_path)
    if stage_manifests:
        git_add(repo_root, written)
    return written


def compare_payload(expected: dict[str, Any], actual: dict[str, Any], label: str) -> list[str]:
    errors: list[str] = []
    keys = ("exists", "directory_count", "file_count", "symlink_count", "total_bytes", "merkle_root")
    for key in keys:
        if expected.get(key) != actual.get(key):
            errors.append(f"{label}: mismatch for {key}: manifest={expected.get(key)} current={actual.get(key)}")
    if expected.get("directories") != actual.get("directories"):
        errors.append(f"{label}: directory inventory mismatch")
    if expected.get("files") != actual.get("files"):
        errors.append(f"{label}: file inventory mismatch")
    if expected.get("symlinks") != actual.get("symlinks"):
        errors.append(f"{label}: symlink inventory mismatch")
    return errors


def verify_manifests(repo_root: Path, policy: dict[str, Any]) -> list[str]:
    errors = ensure_ignore_rules(repo_root, policy)
    local_roots = policy_local_roots(policy)
    tracked_violations = tracked_local_git_violations(repo_root, local_roots)
    if tracked_violations:
        errors.append("tracked files remain under local_git roots: " + ", ".join(tracked_violations[:20]))
    staged_violations = staged_local_git_violations(repo_root, local_roots)
    if staged_violations:
        errors.append("staged files detected under local_git roots: " + ", ".join(staged_violations[:20]))

    root_manifests: list[dict[str, Any]] = []
    for root in local_roots:
        manifest_path = root_manifest_path(repo_root, policy, root)
        if not manifest_path.exists():
            errors.append(f"missing root manifest: {manifest_path.relative_to(repo_root)}")
            continue
        manifest = load_json(manifest_path)
        current = walk_local_root(repo_root, root)
        errors.extend(compare_payload(manifest, current, root.path))
        root_manifests.append(manifest)

    pushable_path = pushable_manifest_path(repo_root, policy)
    if not pushable_path.exists():
        errors.append(f"missing pushable manifest: {pushable_path.relative_to(repo_root)}")
        pushable = None
    else:
        pushable = load_json(pushable_path)
        current_pushable = build_pushable_manifest(repo_root, policy)
        errors.extend(compare_payload(pushable, current_pushable, "pushable_tracked"))

    summary_path = summary_manifest_path(repo_root, policy)
    if not summary_path.exists():
        errors.append(f"missing summary manifest: {summary_path.relative_to(repo_root)}")
    elif pushable is not None and len(root_manifests) == len(local_roots):
        summary = load_json(summary_path)
        current_summary = build_summary_manifest(repo_root, policy, root_manifests, pushable)
        for key in ("global_local_merkle_root", "pushable_merkle_root", "local_roots"):
            if summary.get(key) != current_summary.get(key):
                errors.append(f"summary manifest mismatch for {key}")
    return errors


def install_hooks(repo_root: Path, set_hooks_path: bool) -> None:
    pre_commit = repo_root / ".githooks" / "pre-commit"
    pre_push = repo_root / ".githooks" / "pre-push"
    if not pre_commit.exists() or not pre_push.exists():
        raise RuntimeError("tracked hook files are missing under .githooks/")
    if set_hooks_path:
        subprocess.run(
            ["git", "config", "core.hooksPath", ".githooks"],
            cwd=repo_root,
            text=True,
            capture_output=True,
            check=True,
        )


def cmd_build_manifests(args: argparse.Namespace) -> int:
    repo_root = resolve_repo_root(args.repo_root)
    policy = load_policy(repo_root, resolve_policy_path(repo_root, args.policy_file))
    written = build_manifests(repo_root, policy, stage_manifests=args.stage_manifests)
    for path in written:
        print(path.relative_to(repo_root))
    return 0


def cmd_verify(args: argparse.Namespace) -> int:
    repo_root = resolve_repo_root(args.repo_root)
    policy = load_policy(repo_root, resolve_policy_path(repo_root, args.policy_file))
    errors = verify_manifests(repo_root, policy)
    if errors:
        for item in errors:
            print(f"LOCAL_GIT_ERROR: {item}", file=sys.stderr)
        return 1 if args.strict else 0
    print("LOCAL_GIT_OK")
    return 0


def cmd_hook_check(args: argparse.Namespace) -> int:
    repo_root = resolve_repo_root(args.repo_root)
    policy = load_policy(repo_root, resolve_policy_path(repo_root, args.policy_file))
    if args.refresh:
        build_manifests(repo_root, policy, stage_manifests=args.stage_manifests)
    errors = verify_manifests(repo_root, policy)
    if errors:
        print(f"[{args.hook}] local_git guard FAILED", file=sys.stderr)
        for item in errors:
            print(f"  - {item}", file=sys.stderr)
        return 1 if args.strict else 0
    print(f"[{args.hook}] local_git guard OK")
    return 0


def cmd_install_hooks(args: argparse.Namespace) -> int:
    repo_root = resolve_repo_root(args.repo_root)
    install_hooks(repo_root, set_hooks_path=args.set_hooks_path)
    print(repo_root / ".githooks")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="local_git_guard")
    subparsers = parser.add_subparsers(dest="command", required=True)

    build = subparsers.add_parser("build-manifests")
    build.add_argument("--repo-root")
    build.add_argument("--policy-file")
    build.add_argument("--stage-manifests", action="store_true")
    build.set_defaults(func=cmd_build_manifests)

    verify = subparsers.add_parser("verify")
    verify.add_argument("--repo-root")
    verify.add_argument("--policy-file")
    verify.add_argument("--strict", action="store_true")
    verify.set_defaults(func=cmd_verify)

    hook = subparsers.add_parser("hook-check")
    hook.add_argument("--repo-root")
    hook.add_argument("--policy-file")
    hook.add_argument("--hook", choices=("pre-commit", "pre-push"), required=True)
    hook.add_argument("--refresh", action="store_true")
    hook.add_argument("--stage-manifests", action="store_true")
    hook.add_argument("--strict", action="store_true")
    hook.set_defaults(func=cmd_hook_check)

    install = subparsers.add_parser("install-hooks")
    install.add_argument("--repo-root")
    install.add_argument("--set-hooks-path", action="store_true")
    install.set_defaults(func=cmd_install_hooks)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
