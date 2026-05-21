#!/usr/bin/env python3
"""Deterministic E2E stand-in for a coding agent using this skill.

The mock does not claim to prove real LLM behavior. It proves that an installed
skill artifact can be loaded and that the planted-bug contexts map to the
expected triggers/checks before a real-host smoke run is attempted.
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import sys
from typing import Any

TESTS_DIR = Path(__file__).resolve().parents[1]
if str(TESTS_DIR) not in sys.path:
    sys.path.insert(0, str(TESTS_DIR))

from frontmatter_utils import parse_frontmatter_file


def atomic_write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(f"{path.suffix}.tmp.{os.getpid()}")
    tmp.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    tmp.replace(path)


def finding(
    *,
    path: Path,
    trigger: str,
    check: str,
    diagnostic: str,
    evidence: str,
    metadata: dict[str, Any],
) -> dict[str, Any]:
    return {
        "path": str(path),
        "trigger": trigger,
        "check": check,
        "family": str(metadata.get("family", "")),
        "severity": str(metadata.get("severity", "")),
        "diagnostic": diagnostic,
        "evidence": evidence,
    }


def audit_file(path: Path, checks: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    text = path.read_text(encoding="utf-8")
    hits: list[dict[str, Any]] = []

    if "write_text(json.dumps" in text:
        hits.append(
            finding(
                path=path,
                trigger="on_write_state_file",
                check="A_atomic_write",
                metadata=checks["A_atomic_write"],
                diagnostic="direct write_text(json.dumps(...)) on trusted state without tmp+replace",
                evidence="write_text(json.dumps",
            )
        )

    if "subprocess.run(" in text and "check=True" not in text and "return 0" in text:
        hits.append(
            finding(
                path=path,
                trigger="manual_audit_or_review",
                check="B_cascade_failure",
                metadata=checks["B_cascade_failure"],
                diagnostic="subprocess.run result is unchecked and main() still returns 0",
                evidence="subprocess.run + return 0",
            )
        )

    if "for path in sorted(" in text and "yaml.safe_load" in text and "except" not in text:
        hits.append(
            finding(
                path=path,
                trigger="on_write_scan_loop",
                check="C_scan_loop_safe",
                metadata=checks["C_scan_loop_safe"],
                diagnostic="batch scan parses YAML without per-item skip+report handling",
                evidence="for path in sorted + yaml.safe_load",
            )
        )

    if 'side="upper"' in text and 'side="lower"' not in text and "def test_" in text:
        hits.append(
            finding(
                path=path,
                trigger="on_write_test",
                check="J_bidir_test_coverage",
                metadata=checks["J_bidir_test_coverage"],
                diagnostic="bidirectional branch has only the upper-side regression test",
                evidence='side="upper" without side="lower"',
            )
        )

    return hits


def build_clean_control() -> dict[str, Any]:
    clean_text = """from pathlib import Path
import json
import os


def atomic_write(path: Path, content: str) -> None:
    tmp = path.with_suffix(f"{path.suffix}.tmp.{os.getpid()}")
    tmp.write_text(content, encoding="utf-8")
    tmp.replace(path)


def save_state(path: Path, state: dict) -> None:
    atomic_write(path, json.dumps(state))
"""
    return {"path": "inline:atomic_write_good.py", "text": clean_text, "findings": []}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--skill-dir", required=True)
    parser.add_argument("--fixture-dir", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    skill_link = Path(args.skill_dir).absolute()
    skill_dir = skill_link.resolve()
    fixture_dir = Path(args.fixture_dir).resolve()
    output = Path(args.output).resolve()

    skill_md = skill_dir / "SKILL.md"
    if not skill_md.is_file():
        raise SystemExit(f"missing installed skill file: {skill_md}")

    required_checks = [
        "A_atomic_write",
        "B_cascade_failure",
        "C_scan_loop_safe",
        "J_bidir_test_coverage",
    ]
    checks = {
        name: parse_frontmatter_file(skill_dir / "checks" / f"{name}.md")[0]
        for name in required_checks
    }

    fixture_reports = []
    all_findings: list[dict[str, Any]] = []
    skipped: list[dict[str, str]] = []
    for path in sorted(fixture_dir.glob("*.py")):
        try:
            findings = audit_file(path, checks)
        except Exception as exc:  # pragma: no cover - defensive E2E evidence.
            skipped.append({"path": str(path), "error": str(exc)})
            continue
        fixture_reports.append({"path": str(path), "findings": findings})
        all_findings.extend(findings)

    clean_control = build_clean_control()
    checks_fired = sorted({item["check"] for item in all_findings})
    triggers_fired = sorted({item["trigger"] for item in all_findings})

    payload = {
        "agent": "mock",
        "claim_boundary": "deterministic harness proof, not real LLM behavior proof",
        "skill_loaded": True,
        "skill_link": str(skill_link),
        "skill_dir": str(skill_dir),
        "skill_md": str(skill_md),
        "fixture_dir": str(fixture_dir),
        "fixtures": fixture_reports,
        "skipped": skipped,
        "clean_control": clean_control,
        "summary": {
            "fixture_count": len(fixture_reports),
            "finding_count": len(all_findings),
            "checks_fired": checks_fired,
            "triggers_fired": triggers_fired,
            "required_checks_present": sorted(required_checks),
            "clean_control_findings": len(clean_control["findings"]),
        },
    }
    atomic_write_json(output, payload)
    print(json.dumps(payload["summary"], sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
