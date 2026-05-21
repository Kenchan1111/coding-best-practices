from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml


def _render_scalar(value: Any) -> str:
    if isinstance(value, str):
        return value
    return str(value)


def _normalize_value(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): _normalize_value(item) for key, item in value.items()}
    if isinstance(value, list):
        normalized: list[Any] = []
        for item in value:
            if isinstance(item, dict) and len(item) == 1:
                key, scalar = next(iter(item.items()))
                normalized.append(f"{key}: {_render_scalar(scalar)}")
            else:
                normalized.append(_normalize_value(item))
        return normalized
    return value


def parse_frontmatter_file(path: Path) -> tuple[dict[str, Any], str]:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        raise ValueError(f"{path}: missing frontmatter")

    end = text.find("\n---", 4)
    if end == -1:
        raise ValueError(f"{path}: unterminated frontmatter")

    raw = text[4:end]
    body = text[text.find("\n", end + 4) + 1 :]
    payload = _normalize_value(yaml.safe_load(raw) or {})
    if not isinstance(payload, dict):
        raise ValueError(f"{path}: frontmatter must decode to a mapping")

    return payload, body
