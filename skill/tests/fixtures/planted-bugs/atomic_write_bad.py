from pathlib import Path
import json


def save_state(path: Path, state: dict) -> None:
    path.write_text(json.dumps(state), encoding="utf-8")
