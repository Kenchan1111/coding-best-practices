---
family: P
name: contract_consistency
severity: medium
languages: [python, bash, javascript, typescript, yaml]
triggers:
  - public_api_contract
  - schema_mapping
  - config_merge
  - client_visible_list
patterns_matched:
  - 'status values differ across catalog and docs'
  - 'duplicate term exposed to client'
  - 'result schema drops plan metadata'
  - 'multi-file YAML merge without missing-file warning'
fix_pattern: contract_cross_check
gstack_integration: api_contract_specialist
---

# P - Contract and convention consistency

## When this check applies

Use this check when the same status, action, schema, metadata, term list, or config convention appears in multiple files or is exposed to clients.

## Avoid

```python
documentation_status = "available_initial"
catalog_status = "available"
```

If both are public, clients can lose an audited nuance.

## Required review steps

1. Search for sibling values before changing or adding a public enum/status/action.
2. Check lists exposed to clients for duplicates at module load or validation time.
3. Verify result schemas preserve metadata required by the caller or UI.
4. For multi-file config merges, document precedence and warn when expected files are absent.
5. Add a test that would fail if the convention drifts across files.

## Preferred fixes

```python
assert len(rule["terms"]) == len(set(rule["terms"]))
```

```python
class PlanResult(BaseModel):
    step_results: list[StepResult]
    metadata: PlanMetadata
```

## Fix-first classification

AUTO-FIX duplicate-list guards and tests when behavior is obvious.

ASK when status semantics, schema shape, or config precedence affects clients.

## Sources catalogue

- P1: status naming drifted between catalog and documentation.
- P2: duplicate internal terms leaked to client-visible matches.
- P3: result schema dropped plan metadata.
- P4: multi-file YAML merge used implicit precedence and silent missing files.
- gstack relation: aligns with API Contract specialist and Enum & Value Completeness.
