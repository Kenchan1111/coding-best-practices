---
trigger: on_write_test
phase: before_test_edit
intent: Make tests prove the invariant instead of only covering the happy path.
fires_on:
  - file_path_regex: '(tests?|spec|__tests__)/|test_.*\.py$|.*\.(test|spec)\.(js|ts|tsx)$'
  - code_pattern: 'assert|expect|pytest|unittest|describe\(|it\('
  - user_request: 'add test|write test|fix tests|coverage|regression'
calls_checks:
  - J_bidir_test_coverage
  - D_iteration_semantics
  - N_input_validation
  - Q_numerical_precision
  - P_contract_consistency
suppress_when:
  - snapshot_update_only
  - formatting_only_test_change
preflight_budget: 60s
---

# Trigger - Write Test

## Activation rule

If the next edit creates or changes tests, run this trigger before writing assertions.

The goal is to prevent tests that pass accidentally, mock the thing they claim to test, or cover only one branch of a bidirectional behavior.

## 60-second preflight

1. Load `J_bidir_test_coverage` for every behavior with sides, directions, inverses, thresholds, or modes.
2. Load `D_iteration_semantics` when testing `latest`, sorting, slices, tie-breakers, or first-rule-wins behavior.
3. Load `N_input_validation` when tests exercise invalid IDs, raw user input, coercion, or client metadata.
4. Load `Q_numerical_precision` for statistics, quantiles, digest length, nondetects, or sparse-data labels.
5. Load `P_contract_consistency` when tests protect public schemas, enum/status values, action lists, or config precedence.

## Required LLM behavior

Before applying the test edit, name the failing invariant:

```text
Test preflight: invariant=<specific behavior>; should_fail_before_fix=<yes|no|unknown>; checks=<J,D,N,Q,P subset>.
```

If `should_fail_before_fix=unknown`, do not present the test as regression proof.

## Do not trigger

- Pure snapshot refreshes where no assertion logic changes.
- Formatting-only changes in existing test files.
