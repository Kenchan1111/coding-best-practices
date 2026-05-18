---
family: K
name: architecture_smells
severity: high
languages: [python, bash, javascript, typescript]
triggers:
  - large_file
  - duplicated_code
  - public_api_contract
  - planning_execution_boundary
patterns_matched:
  - 'single file contains many executors and helpers'
  - 'literal duplicate construction blocks'
  - 'function name suggests pure transform but performs IO'
  - 'planning function executes runtime step'
  - 'public API uses dict[str, Any]'
fix_pattern: split_by_contract_boundary
gstack_integration: review_maintainability_specialist
---

# K - Architecture and layering smells

## When this check applies

Use this check when LLM-generated code grows large, duplicates blocks, mixes planning and execution, hides IO in pure-looking functions, or exposes untyped public API contracts.

## Avoid

```python
def update_index(index: dict) -> dict:
    state = load_backend_state()
    ...
```

The name suggests an in-memory transform, but the function performs disk IO.

```python
metadata: dict = Field(default_factory=dict)
```

Public API contracts with untyped dictionaries hide schema drift from clients and OpenAPI.

## Required review steps

1. Check whether file size is a symptom of mixed responsibilities, not just length.
2. Search for literal duplicate construction blocks before adding a third copy.
3. Verify function names reveal side effects: IO, network, DB, subprocess, cache mutation.
4. Keep planning/building separate from execution. A planner should not run data profiling unless that is explicit in its contract.
5. For public APIs, require typed request/response models instead of `dict[str, Any]` when fields are stable.
6. Flag known vulnerable algorithm shortcuts such as duplicate-last Merkle tree leaves when the artifact is used as proof.

## Preferred fixes

Split by responsibility, not by arbitrary line count:

```text
executors/
  diagnostics.py
  nd.py
  trend.py
  prediction.py
```

Rename side-effectful functions when extraction is too large for the current patch:

```python
load_and_update_index(...)
```

This is weaker than decoupling, but more honest than a pure-looking name.

## Fix-first classification

ASK for refactors, public API schemas, planner/executor separation, and proof algorithms.

AUTO-FIX only for small duplicate helper extraction or honest renaming when behavior is unchanged.

## Sources catalogue

- K1: monolithic executor file mixed many responsibilities.
- K2: literal duplicate construction and normalization code.
- K3: pure-looking function performed disk IO.
- K4: planning function executed a runtime step.
- K5: public API used untyped `dict`.
- K6: Merkle duplicate-last pattern inherited a known vulnerability class.
- gstack relation: complements maintainability specialist and `/devex-review`.
