---
family: M
name: drift_detection
severity: medium
languages: [python, bash, javascript, typescript]
triggers:
  - persisted_snapshot
  - catalog_generation
  - service_runtime
  - baseline_reuse
patterns_matched:
  - 'latest snapshot overwrites history'
  - 'no changelog for disappeared records'
  - 'digest missing from catalog'
  - 'baseline row exists but backing rows missing'
  - 'service has no restart story after reboot'
fix_pattern: append_only_changelog_and_consistency_guard
gstack_integration: canary_and_health
---

# M - Persistence and drift detection

## When this check applies

Use this check when code writes latest snapshots, catalogs, summaries, baselines, service state, or reusable caches that can drift from source files or backing rows.

## Avoid

```python
write_latest(current_documents)
```

If the latest view overwrites prior state, disappeared or modified documents can vanish without trace.

## Required review steps

1. Verify there is an append-only history or changelog for changes between snapshots.
2. Store a digest for each document or record when drift matters.
3. Detect disappeared records, not only newly added records.
4. When reusing a baseline, check both the state marker and the backing rows or files.
5. For long-lived local services, define restart behavior after reboot.

## Preferred fixes

```python
drift = compare_catalog(previous, current)
append_changelog(drift)
write_latest(current)
```

```python
if domain_state_exists and not repo_files_exist:
    raise BaselineInconsistent("domain state exists without repo files")
```

## Fix-first classification

AUTO-FIX adding digests, changelog entries, and disappeared-record reporting when no behavior changes.

ASK when the fix changes cache reuse, service lifecycle, or recovery policy.

## Sources catalogue

- M1: no service restart after reboot.
- M2: latest catalog overwrote history and hid disappeared propositions.
- M3: missing document digests prevented modification detection.
- M4: baseline reuse did not verify backing rows.
- gstack relation: complements `/canary`, `/health`, and review operational checks.
