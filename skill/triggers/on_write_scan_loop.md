---
trigger: on_write_scan_loop
phase: before_loop_edit
intent: Keep batch scans complete, deterministic, and inspectable when one item is malformed.
fires_on:
  - code_pattern: 'for .* in .*glob|for .* in sorted\(|walk\(|iterdir\(|read_text\(\)'
  - code_pattern: 'yaml\.safe_load|frontmatter|parse.*markdown|load_review_documents|scan_'
  - file_path_regex: '(scan|sync|archive|catalog|index|loader|collector).*'
calls_checks:
  - C_scan_loop_safe
  - D_iteration_semantics
  - B_cascade_failure
  - M_drift_detection
  - A_atomic_write
  - O_intrusive_nonportable
suppress_when:
  - fixed_small_list_no_io
  - explicit_fail_fast_parser
preflight_budget: 45s
---

# Trigger - Write Scan Loop

## Activation rule

If the next edit scans files, parses many documents, loads frontmatter, indexes a directory, or aggregates records from a batch, run this trigger before writing the loop.

This is a coding-time trigger. It is too late after the loop shape is already committed.

## 45-second preflight

1. Load `C_scan_loop_safe` and decide whether one bad item should skip, warn, or hard-fail.
2. Load `D_iteration_semantics` if the loop selects latest, first, sorted, sliced, or first-match results.
3. Load `B_cascade_failure` if scan errors affect process exit status or downstream pipeline success.
4. Load `M_drift_detection` if the scan produces a latest snapshot or catalog.
5. Load `A_atomic_write` if the scan writes generated state after reading.
6. Load `O_intrusive_nonportable` if the scanner depends on cwd, terminal behavior, or import path hacks.

## Required LLM behavior

Before applying the edit, state the failure mode:

```text
Scan-loop preflight: bad_item_policy=<skip+report|hard_fail|not_applicable>; ordering=<deterministic|needs_tie_breaker>; checks=<C,D,B,M,A,O subset>.
```

If the policy is `skip+report`, the output must include the skipped path and error count.

## Do not trigger

- Loops over fixed in-memory lists with no parsing or IO.
- Parsers where fail-fast is an explicit contract and caller handles the failure.
