---
family: J
name: bidir_test_coverage
severity: critical
languages: [python, bash, javascript, typescript]
triggers:
  - test_write
  - test_review
  - bidirectional_behavior
  - parameterized_logic
patterns_matched:
  - 'tests directory missing'
  - 'only upper branch tested'
  - 'one direction of inverse behavior tested'
  - 'test data does not match asserted threshold'
  - 'mock replaces the behavior under test'
fix_pattern: bidirectional_regression_test
gstack_integration: review_testing_specialist
---

# J - Test coverage for bidirectional and parameterized behavior

## When this check applies

Use this check when adding or reviewing tests for functions with directions, sides, thresholds, parsers, classifiers, converters, or any behavior that has symmetric branches.

Examples: `upper/lower`, `left/right`, `enable/disable`, `parse/render`, `serialize/deserialize`, `accept/reject`, `before/after`.

## Required review steps

1. Verify the repo has a test location and the changed behavior has at least one regression test.
2. For bidirectional behavior, require both directions in the same review scope.
3. Check that test data actually exercises the asserted threshold or branch.
4. Ensure the test would fail before the fix.
5. Do not mock the unit, parser, or external boundary that the test claims to validate.

## Avoid

```python
def test_prediction_limit_upper():
    assert prediction_limit(values, side="upper") > mean
```

This misses `side="lower"` and can let the symmetric branch rot silently.

## Preferred test shape

```python
def test_prediction_limit_covers_both_sides():
    upper = prediction_limit(values, side="upper")
    lower = prediction_limit(values, side="lower")

    assert upper > mean
    assert lower < mean
```

For thresholds, include data that sits on both sides of the boundary, not only a happy-path value.

## Fix-first classification

AUTO-FIX missing local tests for mechanical branches when the expected behavior is already explicit.

ASK when expected behavior is domain-specific, regulatory, numerical, or not documented.

## Sources catalogue

- J1: no `tests/` directory.
- J2: only one direction of bidirectional behavior tested.
- J3: incorrect test parameters passed accidentally.
- J4: tests mocked the behavior they claimed to verify.
- gstack relation: complements `gstack/review/specialists/testing.md` with catalog-specific bidirectional rules.
