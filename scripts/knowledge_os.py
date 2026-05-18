#!/usr/bin/env python3
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
import hashlib
import os
import re
from typing import Any, Iterable

import yaml

ROOT = Path(__file__).resolve().parent.parent
REVIEW_ROOT = ROOT / "reviews"
GLOBAL_HANDOFF_DIR = REVIEW_ROOT / "global_handoff"
DEFAULT_AGENTS = ("claude-opus", "claude-sonnet", "gpt-5.5")
RESERVED_REVIEW_DIRS = {"global_handoff"}
REVIEW_KINDS = ("handoff", "corrections", "proposition")

STATUS_ALIASES = {
    "accepted": "accepted",
    "active": "active",
    "applied": "applied",
    "approved": "approved",
    "archived": "archived",
    "blocked": "blocked",
    "draft": "draft",
    "proposed": "proposed",
    "proposal": "proposed",
    "proposition": "proposed",
    "ready-for-review": "ready-for-review",
    "rejected": "rejected",
}


def atomic_write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(f"{path.suffix}.tmp.{os.getpid()}")
    tmp.write_text(content, encoding="utf-8")
    tmp.replace(path)


def file_digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()[:12]


def discover_agents() -> tuple[str, ...]:
    discovered: list[str] = []
    seen: set[str] = set()

    for agent in DEFAULT_AGENTS:
        if agent not in seen:
            discovered.append(agent)
            seen.add(agent)

    if REVIEW_ROOT.exists():
        for path in sorted(REVIEW_ROOT.iterdir()):
            if not path.is_dir():
                continue
            if path.name.startswith(".") or path.name in RESERVED_REVIEW_DIRS:
                continue
            if path.name not in seen:
                discovered.append(path.name)
                seen.add(path.name)

    return tuple(discovered)


def _extract_first_paragraph(body: str, max_chars: int = 280) -> str:
    for line in body.splitlines():
        stripped = line.strip()
        if stripped and not stripped.startswith("#"):
            return stripped[:max_chars] + ("..." if len(stripped) > max_chars else "")
    return ""


@dataclass
class Document:
    path: Path
    metadata: dict[str, Any]
    body: str
    title: str
    has_frontmatter: bool = False

    @property
    def relative_path(self) -> str:
        try:
            return str(self.path.relative_to(ROOT))
        except ValueError:
            return str(self.path)

    @property
    def stable_id(self) -> str:
        value = self.metadata.get("id")
        if value:
            return str(value)
        return self.path.stem.split("__", maxsplit=1)[0]

    @property
    def synopsis(self) -> str:
        value = self.metadata.get("synopsis")
        if value:
            return str(value).strip()
        return _extract_first_paragraph(self.body)


def normalize_data(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: normalize_data(item) for key, item in value.items()}
    if isinstance(value, list):
        return [normalize_data(item) for item in value]
    if isinstance(value, datetime):
        return value.isoformat(timespec="minutes")
    if isinstance(value, date):
        return value.isoformat()
    return value


def parse_frontmatter(path: Path) -> tuple[dict[str, Any], str, bool]:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---"):
        return {}, text, False

    lines = text.splitlines(keepends=True)
    if not lines or lines[0].strip() != "---":
        return {}, text, False

    end_index = None
    for index, line in enumerate(lines[1:], start=1):
        if line.strip() == "---":
            end_index = index
            break

    if end_index is None:
        return {}, text, False

    raw_frontmatter = "".join(lines[1:end_index])
    body = "".join(lines[end_index + 1:]).lstrip("\n")
    payload = yaml.safe_load(raw_frontmatter) or {}
    if not isinstance(payload, dict):
        payload = {}

    return normalize_data(payload), body, True


def extract_title(text: str, fallback: str) -> str:
    match = re.search(r"^#\s+(.+?)\s*$", text, flags=re.MULTILINE)
    if match:
        return match.group(1).strip()
    return fallback


def find_metadata_line(text: str, labels: Iterable[str]) -> str | None:
    for label in labels:
        pattern = rf"^\*{{0,2}}{re.escape(label)}\*{{0,2}}\s*:\s*(.+?)\s*$"
        match = re.search(pattern, text, flags=re.IGNORECASE | re.MULTILINE)
        if match:
            return match.group(1).strip()
    return None


def normalize_status(value: Any, default: str = "draft") -> str:
    if value is None:
        return default
    normalized = str(value).strip().lower()
    return STATUS_ALIASES.get(normalized, normalized or default)


def infer_review_metadata(path: Path, body: str) -> dict[str, Any]:
    default_status = "proposed" if "proposition" in path.parts else "draft"
    return {
        "id": path.stem,
        "title": extract_title(body, path.stem.replace("_", " ")),
        "date": find_metadata_line(body, ("Date", "date")),
        "status": normalize_status(
            find_metadata_line(body, ("Statut", "Status")), default=default_status
        ),
        "author": find_metadata_line(body, ("Auteur", "Author")),
    }


def load_markdown_document(
    path: Path,
    infer_review: bool = False,
    extra_metadata: dict[str, Any] | None = None,
) -> Document:
    metadata, body, has_frontmatter = parse_frontmatter(path)

    if infer_review:
        metadata = {**infer_review_metadata(path, body), **metadata}

    if extra_metadata:
        metadata = {**metadata, **extra_metadata}

    metadata = normalize_data(metadata)
    title = str(metadata.get("title") or extract_title(body, path.stem.replace("_", " ")))

    return Document(
        path=path,
        metadata=metadata,
        body=body,
        title=title,
        has_frontmatter=has_frontmatter,
    )


def load_review_documents(kind: str = "proposition", agents: Iterable[str] | None = None) -> list[Document]:
    documents: list[Document] = []
    active_agents = tuple(agents) if agents is not None else discover_agents()

    for agent in active_agents:
        review_dir = REVIEW_ROOT / agent / kind
        if not review_dir.exists():
            continue
        for path in sorted(review_dir.glob("*.md")):
            if path.name.startswith(".") or path.stem.upper() == "README":
                continue
            documents.append(
                load_markdown_document(
                    path,
                    infer_review=True,
                    extra_metadata={"agent": agent, "review_kind": kind},
                )
            )

    return documents


def parse_date_like(value: Any) -> datetime | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value
    if isinstance(value, date):
        return datetime.combine(value, datetime.min.time())

    text = str(value).strip()
    if not text:
        return None

    for fmt in (
        "%Y-%m-%d",
        "%Y-%m-%d %H:%M",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d-%H-%M",
        "%Y-%m-%dT%H:%M",
        "%Y-%m-%dT%H:%M:%S",
    ):
        try:
            return datetime.strptime(text, fmt)
        except ValueError:
            continue

    return None


def markdown_link(target: Path, source_file: Path, label: str | None = None) -> str:
    relative = os.path.relpath(target, start=source_file.parent)
    return f"[{label or target.stem}]({relative.replace(os.sep, '/')})"


def render_markdown_document(metadata: dict[str, Any], body: str) -> str:
    normalized = normalize_data(metadata)
    frontmatter = yaml.safe_dump(
        normalized,
        sort_keys=False,
        allow_unicode=True,
    ).strip()
    return f"---\n{frontmatter}\n---\n\n{body.rstrip()}\n"
