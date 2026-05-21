from __future__ import annotations

import re
from pathlib import Path

from frontmatter_utils import parse_frontmatter_file

ROOT = Path(__file__).resolve().parents[2]
SKILL = ROOT / "skill"


def parse_frontmatter(path: Path) -> tuple[dict[str, object], str]:
    try:
        return parse_frontmatter_file(path)
    except ValueError as exc:
        raise AssertionError(str(exc)) from exc


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
