---
family: H
name: silent_override
severity: high
languages: [python, bash, javascript, typescript]
triggers:
  - explicit_user_input
  - regulatory_parameter
  - pre_diff_filter
  - index_limit
patterns_matched:
  - 'explicit catalog_id popped or ignored'
  - 'auto mode switch overrides user selection'
  - 'filter before comparing previous/current state'
  - 'MAX_INDEX_RECORDS truncates without warning'
  - 'spec action missing from implementation menu'
fix_pattern: preserve_explicit_intent_or_ask
gstack_integration: review_llm_trust_boundary
---

# H - Silent override of explicit user intent

## When this check applies

Use this check when code receives explicit user input, regulatory parameters, selected modes, IDs, limits, or spec-listed actions, then changes or drops them automatically.

## Avoid

```python
if family == "heavy_metal":
    params.pop("catalog_id", None)
    params.pop("usage_code", None)
    mode = "prediction_limit"
```

This silently converts a fixed regulatory compliance request into a background-vs-future analysis.

## Required review steps

1. Identify every user-supplied field and decide whether it is explicit intent, defaultable context, or derived metadata.
2. If code overrides explicit intent, require an ASK path, warning, or returned diagnostic.
3. Compare previous/current state before applying ignore filters when deletions must be detected.
4. If records are truncated by a limit, require a count, warning, and retrieval path for omitted records.
5. Cross-check spec-listed actions against implementation menus and command handlers.

## Preferred fixes

Preserve explicit parameters unless the user confirms the switch:

```python
if explicit_catalog_id and inferred_mode != requested_mode:
    raise UserDecisionRequired(
        "catalog_id was explicit; confirm before switching analysis mode"
    )
```

Emit visible metadata when a filter intentionally hides changes:

```python
result.filtered_count = len(filtered)
result.filter_reason = "retired archive prefix"
```

## Fix-first classification

ASK by default. User intent, compliance mode, and spec behavior are user-visible.

AUTO-FIX only for adding diagnostics, preserving metadata, or making an existing warning visible without changing the selected behavior.

## Sources catalogue

- H1: heavy-metal auto-switch silently dropped explicit regulatory inputs.
- H2: pre-comparison filter masked deletions.
- H3: index limit dropped records without log or signal.
- H4: spec listed four actions but implementation exposed three.
- gstack relation: expands LLM Output Trust Boundary from generated data validation to explicit user-intent preservation.
