---
family: D
name: iteration_semantics
severity: critical
languages: [python, bash, javascript, typescript]
triggers:
  - sorted_iteration
  - latest_selection
  - markdown_section_parse
  - classification_rules
patterns_matched:
  - 'latest variable assigned only once while iterating ascending'
  - 'fixed slice like lines[1:6] for structured content'
  - 'sort by date without stable tie-breaker'
  - 'first matching rule wins without documenting order'
fix_pattern: explicit_iteration_invariant
gstack_integration: review_critical_pass
---

# D - Iteration semantics

## When this check applies

Use this check when code selects `latest`, `first`, `best`, `last`, classifies by ordered rules, parses structured text by slices, or aggregates records after sorting.

## Avoid

```python
latest_by_kind = {}
for event in sorted(events, key=lambda item: item["date"]):
    if event["kind"] not in latest_by_kind:
        latest_by_kind[event["kind"]] = event
```

This keeps the first event in ascending order, despite the variable name `latest_by_kind`.

## Required review steps

1. Write the loop invariant in plain language: what is kept after each iteration?
2. Check whether sort direction matches variable names like `latest`, `oldest`, `best`, or `current`.
3. Replace magic slices with marker-based parsing, bounds checks, or explicit section extraction.
4. For same-date or same-score records, require a deterministic tie-breaker.
5. For `first-rule-wins`, document why order is load-bearing and emit an ambiguity signal when multiple rules match.

## Preferred fixes

```python
for event in sorted(events, key=lambda item: item["date"]):
    latest_by_kind[event["kind"]] = event
```

or:

```python
for event in reversed(sorted(events, key=lambda item: item["date"])):
    latest_by_kind.setdefault(event["kind"], event)
```

Use the version that makes the invariant obvious in the surrounding code.

## Fix-first classification

ASK by default. Iteration fixes can change business verdicts, regulatory outputs, or user-visible classifications.

AUTO-FIX only for clearly dead slices or missing tie-breakers in non-user-visible helper code with tests.

## Sources catalogue

- D1: `latest` implemented as `first`.
- D2: fixed markdown slices without bounds or structure.
- D3: date-only sort made verdicts unstable.
- D4: lower/upper branch semantics not both tested.
- D5: first-rule-wins order was load-bearing but undocumented.
- gstack relation: extends `/review` enum/value completeness with Python/CLI iteration invariants.
