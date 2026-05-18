from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SKILL = ROOT / "skill"


def parse_frontmatter(path: Path) -> tuple[dict[str, object], str]:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        raise AssertionError(f"{path}: missing frontmatter")

    end = text.find("\n---", 4)
    if end == -1:
        raise AssertionError(f"{path}: unterminated frontmatter")

    raw = text[4:end]
    body = text[text.find("\n", end + 4) + 1 :]
    metadata: dict[str, object] = {}
    current_key: str | None = None

    for line in raw.splitlines():
        if not line.strip():
            continue
        match = re.match(r"^([A-Za-z0-9_-]+):(?:\s*(.*))?$", line)
        if match:
            key, value = match.groups()
            value = (value or "").strip()
            current_key = key
            if not value:
                metadata[key] = []
            elif value.startswith("[") and value.endswith("]"):
                metadata[key] = [
                    item.strip().strip("'\"")
                    for item in value[1:-1].split(",")
                    if item.strip()
                ]
                current_key = None
            else:
                metadata[key] = value.strip("'\"")
                current_key = None
            continue

        item = re.match(r"^\s*-\s*(.+)$", line)
        if item and current_key:
            metadata.setdefault(current_key, [])
            assert isinstance(metadata[current_key], list)
            metadata[current_key].append(item.group(1).strip().strip("'\""))

    return metadata, body


def load_check(stem: str) -> tuple[dict[str, object], str]:
    return parse_frontmatter(SKILL / "checks" / f"{stem}.md")


def load_trigger(stem: str) -> tuple[dict[str, object], str]:
    return parse_frontmatter(SKILL / "triggers" / f"{stem}.md")


def frontmatter_list(metadata: dict[str, object], key: str) -> list[str]:
    value = metadata.get(key)
    if not isinstance(value, list):
        raise AssertionError(f"{key} must be a list")
    return [str(item) for item in value]


def lower_join(items: list[str]) -> str:
    return "\n".join(items).lower()


def find_file_line_citations(text: str) -> list[tuple[str, int]]:
    pattern = re.compile(r"(?<![\w/])([A-Za-z0-9_./-]+\.[A-Za-z0-9_]+):(\d+)")
    return [(match.group(1), int(match.group(2))) for match in pattern.finditer(text)]


def unread_citations(text: str, read_paths: set[str]) -> list[tuple[str, int]]:
    normalized_reads = {path.strip("./") for path in read_paths}
    missing = []
    for path, line in find_file_line_citations(text):
        normalized = path.strip("./")
        if normalized not in normalized_reads and Path(normalized).name not in normalized_reads:
            missing.append((path, line))
    return missing
