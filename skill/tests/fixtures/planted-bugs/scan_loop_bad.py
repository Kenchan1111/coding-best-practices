from pathlib import Path
import yaml


def scan_archive(root: Path) -> list[dict]:
    documents = []
    for path in sorted(root.glob("*.md")):
        documents.append(yaml.safe_load(path.read_text(encoding="utf-8")))
    return documents
