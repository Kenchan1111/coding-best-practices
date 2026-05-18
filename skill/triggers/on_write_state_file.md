---
trigger: on_write_state_file
phase: before_edit_or_bash
intent: Prevent corrupt, stale, or misleading persisted state.
fires_on:
  - file_path_regex: '(latest|index|catalog|manifest|state|baseline|timeline|digest|anchor).*\.(json|ya?ml|ndjson|db|sqlite)$'
  - python_pattern: '\.write_text\(.*json|json\.dump|open\(.+, ["'']w'
  - javascript_pattern: 'writeFileSync|writeFile\(.*JSON\.stringify'
  - bash_command: 'jq .* >|cat .* >|echo .* >'
calls_checks:
  - A_atomic_write
  - B_cascade_failure
  - M_drift_detection
  - R_audit_trail
  - F_race_conditions
suppress_when:
  - append_only_log
  - throwaway_test_fixture
  - explicitly_regenerable_cache
preflight_budget: 45s
---

# Trigger - Write State File

## Activation rule

If the next edit or command writes trusted state, proof, index, catalog, manifest, baseline, digest, or run pointer, stop before editing and run this preflight.

Do not wait for review time. This trigger is useful only before the write path is implemented.

## 45-second preflight

1. Classify the target: `state`, `proof`, `cache`, `fixture`, or `log`.
2. If `state` or `proof`, load `A_atomic_write` and require temp-file plus replace semantics.
3. Load `B_cascade_failure` if a later command or user will treat this write as success.
4. Load `M_drift_detection` if this write overwrites a latest snapshot or generated catalog.
5. Load `R_audit_trail` if values are dropped, normalized, promoted, or transformed before writing.
6. Load `F_race_conditions` if more than one process, worker, or command can write the same target.

## Required LLM behavior

Before applying the edit, write a one-line internal decision in the working note or review output:

```text
State-write preflight: target=<state|proof|cache|fixture|log>; checks=<A,B,M,R,F subset>; decision=<atomic|append-only|safe-cache|ask>.
```

If the decision is `ask`, ask the user before changing persistence semantics.

## Do not trigger

- Append-only logs where partial last lines are acceptable.
- Test fixtures under `tests/fixtures/`.
- Caches that are explicitly documented as fully regenerable and never authoritative.
