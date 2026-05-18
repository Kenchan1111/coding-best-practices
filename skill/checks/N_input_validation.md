---
family: N
name: input_validation
severity: medium
languages: [python, bash, javascript, typescript]
triggers:
  - user_input
  - api_parameter
  - client_metadata
  - parameter_coercion
patterns_matched:
  - 'user supplied ID saved without existence check'
  - 'float(...) raw ValueError at API boundary'
  - 'client metadata treated as authoritative'
  - 'inconsistent coercion error types'
fix_pattern: validate_at_boundary
gstack_integration: review_type_coercion_and_trust_boundary
---

# N - Input validation at boundaries

## When this check applies

Use this check for CLI prompts, API request parameters, imported metadata, file IDs, dates, numeric thresholds, user-selected roles, and any value crossing from user/client/LLM into trusted state.

## Avoid

```python
target_id = input("ID cible > ")
save_document(target_id, payload)
```

This creates links to IDs that may not exist.

```python
threshold = float(request.threshold)
```

Raw conversion errors leak implementation details and create inconsistent API behavior.

## Required review steps

1. Validate existence for user-selected IDs before saving references.
2. Normalize coercion errors into a project-specific error type.
3. Treat client metadata as claims, not authority, when it can drive compliance, role, or mode selection.
4. Validate numeric, date, enum, and URL fields consistently at the boundary.
5. Add tests for invalid input, missing IDs, and malicious or contradictory metadata.

## Preferred fixes

```python
if target_id not in catalog:
    raise ValidationError(f"unknown target_id: {target_id}")
```

```python
try:
    value = float(raw_value)
except ValueError as exc:
    raise ParameterCoercionError("threshold must be numeric") from exc
```

## Fix-first classification

AUTO-FIX small boundary validations where the expected error behavior already exists.

ASK when validation changes accepted inputs, migration behavior, or domain semantics.

## Sources catalogue

- N1: user-provided ID was not checked before saving.
- N2: numeric coercion raised raw `ValueError` while dates used domain errors.
- N3: client `point_metadata` drove trusted auto-selection.
- gstack relation: aligns with Type Coercion at Boundaries and LLM Output Trust Boundary.
