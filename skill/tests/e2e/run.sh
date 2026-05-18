#!/usr/bin/env bash
# Deterministic E2E harness for coding-best-practices.
set -euo pipefail
umask 077

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
SKILL_DIR="$(cd "$SCRIPT_DIR/../.." && pwd -P)"
PROJECT_ROOT="$(cd "$SKILL_DIR/.." && pwd -P)"
FIXTURE_DIR="$SKILL_DIR/tests/fixtures/planted-bugs"
OUTPUT_DIR=""
AGENT="mock"

usage() {
  cat <<'USAGE'
Usage: skill/tests/e2e/run.sh [options]

Runs a deterministic installed-skill E2E smoke check.

Options:
  --agent <mock>          Agent backend. Phase 1 supports mock only.
  --output-dir <path>     Directory for result.json and setup logs.
  -h, --help              Show this help.
USAGE
}

die() {
  printf 'ERROR: %s\n' "$*" >&2
  exit 1
}

while [ $# -gt 0 ]; do
  case "$1" in
    --agent)
      [ $# -lt 2 ] && die "missing value for --agent"
      AGENT="$2"
      shift 2
      ;;
    --agent=*)
      AGENT="${1#--agent=}"
      shift
      ;;
    --output-dir)
      [ $# -lt 2 ] && die "missing value for --output-dir"
      OUTPUT_DIR="$2"
      shift 2
      ;;
    --output-dir=*)
      OUTPUT_DIR="${1#--output-dir=}"
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      die "unknown option: $1"
      ;;
  esac
done

[ "$AGENT" = "mock" ] || die "unsupported --agent '$AGENT'; Phase 1 supports mock only"
[ -d "$FIXTURE_DIR" ] || die "missing fixture dir: $FIXTURE_DIR"

if [ -z "$OUTPUT_DIR" ]; then
  OUTPUT_DIR="$(mktemp -d "${TMPDIR:-/tmp}/coding-best-practices-e2e.XXXXXX")"
fi
mkdir -p "$OUTPUT_DIR"
OUTPUT_DIR="$(cd "$OUTPUT_DIR" && pwd -P)"

export HOME="$OUTPUT_DIR/home"
mkdir -p "$HOME"

SETUP_LOG="$OUTPUT_DIR/setup.log"
RESULT_JSON="$OUTPUT_DIR/result.json"

(
  cd "$PROJECT_ROOT"
  bash "$SKILL_DIR/setup" --host all --yes --skip-validate --quiet
) >"$SETUP_LOG" 2>&1

INSTALLED_SKILL="$HOME/.codex/skills/coding-best-practices"
[ -L "$INSTALLED_SKILL" ] || die "setup did not create Codex skill symlink: $INSTALLED_SKILL"

python3 "$SCRIPT_DIR/mock_agent.py" \
  --skill-dir "$INSTALLED_SKILL" \
  --fixture-dir "$FIXTURE_DIR" \
  --output "$RESULT_JSON" >"$OUTPUT_DIR/mock-agent.log" 2>&1

python3 - "$RESULT_JSON" <<'PY'
import json
import sys

path = sys.argv[1]
payload = json.load(open(path, encoding="utf-8"))
summary = payload["summary"]
required = {"A_atomic_write", "B_cascade_failure", "C_scan_loop_safe"}
fired = set(summary["checks_fired"])
missing = sorted(required - fired)
if missing:
    raise SystemExit(f"missing required check hits: {missing}")
if "on_write_state_file" not in summary["triggers_fired"]:
    raise SystemExit("on_write_state_file trigger did not fire")
if summary["clean_control_findings"] != 0:
    raise SystemExit("clean atomic-write control produced findings")

atomic_hits = [
    item
    for fixture in payload["fixtures"]
    for item in fixture["findings"]
    if item["check"] == "A_atomic_write"
]
if not atomic_hits:
    raise SystemExit("no A_atomic_write finding emitted")
if "write_text(json.dumps" not in atomic_hits[0]["diagnostic"]:
    raise SystemExit("A_atomic_write finding lacks direct write_text diagnostic")
PY

printf 'E2E_OK output_dir=%s result=%s\n' "$OUTPUT_DIR" "$RESULT_JSON"
