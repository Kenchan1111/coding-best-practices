---
family: R
name: audit_trail
severity: medium
languages: [python, bash, javascript, typescript]
triggers:
  - data_transformation
  - parameter_drop
  - event_timestamp
  - evidence_generation
patterns_matched:
  - 'original parameters popped without preservation'
  - 'discarded threshold parameters not recorded'
  - 'invalid timestamp falls back to 1970-01-01'
  - 'corrupt event sorted as first event'
fix_pattern: preserve_originals_and_flag_fallbacks
gstack_integration: review_auditability
---

# R - Audit trail preservation

## When this check applies

Use this check when code transforms user inputs, drops parameters, normalizes records, falls back timestamps, builds evidence, or emits event sequences.

## Avoid

```python
params.pop("threshold_value", None)
params.pop("catalog_id", None)
params.pop("usage_code", None)
```

Dropping original parameters prevents a reviewer from reconstructing the request.

```python
timestamp = parse_timestamp(raw) or "1970-01-01"
```

Invalid timestamps become false earliest events.

## Required review steps

1. Preserve original user inputs when transformed values affect outcomes.
2. Record why a parameter was dropped, ignored, or superseded.
3. Treat invalid timestamps as invalid, not as epoch defaults, unless the output clearly marks them as fallback.
4. Ensure event ordering cannot make corrupt records look authoritative.
5. Include audit metadata in the result object, not only logs.

## Preferred fixes

```python
evidence.discarded_threshold_parameters = {
    "threshold_value": params.get("threshold_value"),
    "catalog_id": params.get("catalog_id"),
    "usage_code": params.get("usage_code"),
    "reason": "mode switched to prediction_limit",
}
```

```python
if timestamp is None:
    event.timestamp_valid = False
    event.sequence_sort_key = None
```

## Fix-first classification

AUTO-FIX preserving discarded values in metadata when it does not change behavior.

ASK when changing timestamp sorting, event validity, or evidence semantics.

## Sources catalogue

- R1: auto-switch popped original parameters without preserving them.
- R2: timestamp fallback `1970-01-01` created false earliest events.
- gstack relation: auditability extension for review, canary, and evidence workflows.
