---
family: I
name: irreversible_ops
severity: high
languages: [python, bash, javascript, typescript]
triggers:
  - destructive_file_op
  - promote_document
  - client_selected_id
  - overwrite_existing_record
patterns_matched:
  - 'shutil.move used for promotion'
  - 'client supplied ID overwrites existing record'
  - 'write without revision or snapshot hash'
  - 'source document removed during workflow'
fix_pattern: copy_then_mark_or_version
gstack_integration: careful_guard_destructive_ops
---

# I - Irreversible operations

## When this check applies

Use this check before moving, deleting, overwriting, promoting, truncating, or replacing user-visible data, review notes, datasets, or proof artifacts.

## Avoid

```python
shutil.move(source, promoted_path)
```

Promotion should not destroy the source review note.

```python
store[dataset_id] = payload
```

If `dataset_id` is client-selected, this silently overwrites an earlier dataset.

## Required review steps

1. Identify whether the source is still needed for traceability, rollback, or review.
2. Prefer copy plus metadata over move when promoting documents.
3. If an ID comes from the client, check existence before writing.
4. For overwrites, require revision numbers, snapshot hashes, or explicit replace confirmation.
5. Align destructive shell operations with gstack `/careful` and `/guard` behavior.

## Preferred fixes

```python
shutil.copy2(source, promoted_path)
mark_promoted(source, promoted_to=promoted_path)
```

```python
if dataset_id in store:
    raise ConflictError(f"dataset_id already exists: {dataset_id}")
```

## Fix-first classification

ASK by default. Irreversible operations require owner intent.

AUTO-FIX only for replacing `move` with `copy2` when the source is clearly supposed to remain as audit evidence.

## Sources catalogue

- I1: `shutil.move` removed source review documents during promotion.
- I2: client-selected `dataset_id` overwrote prior data silently.
- gstack relation: maps to `/careful`, `/guard`, and destructive command preflight.
