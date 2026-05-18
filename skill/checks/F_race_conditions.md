---
family: F
name: race_conditions
severity: high
languages: [python, bash, javascript, typescript]
triggers:
  - id_generation
  - concurrent_write
  - multi_worker_state
  - file_lock
patterns_matched:
  - 'timestamp-second ID without random suffix'
  - 'module-level singleton used as mutable app state'
  - 'flock fd inherited by child process'
  - 'shared state without explicit lock or transaction'
fix_pattern: collision_resistant_ids_and_explicit_locks
gstack_integration: review_race_conditions
---

# F - Race conditions and concurrency

## When this check applies

Use this check when code creates IDs, writes shared files, holds locks, stores mutable process state, or runs under multiple workers, processes, shells, or async tasks.

## Avoid

```python
anchor_id = f"{compact_timestamp()}__{backend}__{root[:16]}"
```

Timestamp-to-the-second IDs collide when two processes create the same payload in the same second.

```python
dataset_store = InMemoryDatasetStore()
```

A module-level singleton becomes one store per worker under multi-worker servers.

## Required review steps

1. Identify every shared resource: file, index, socket, in-memory store, lock, DB row, or external command.
2. Check whether IDs remain unique under same-second concurrent runs with identical payloads.
3. For web apps, verify state is not hidden in per-process globals when multiple workers can serve requests.
4. For lock files, verify descriptors are not inherited across `fork`, `exec`, or child shell commands.
5. Require a test or reproduction plan that exercises two concurrent writers when the risk is real.

## Preferred fixes

Use collision-resistant IDs:

```python
anchor_id = f"{compact_timestamp()}__{secrets.token_hex(4)}__{backend}__{root[:16]}"
```

Use dependency injection for app state instead of module-level mutable singletons:

```python
def get_store() -> DatasetStore:
    return app.state.dataset_store
```

Close inherited lock descriptors before spawning children:

```bash
exec 200>"$lock_file"
flock 200
some_child_command 200>&-
```

## Fix-first classification

ASK by default. Race-condition fixes often change persistence, process model, or API semantics.

AUTO-FIX only for local mechanical hardening such as adding random suffixes to new internal IDs or closing an inherited lock fd where behavior is already clear.

## Sources catalogue

- F1: timestamp-second IDs collided and overwrote anchors.
- F2: module-level singleton broke under multi-worker `uvicorn`.
- F3: fd 200 lock inherited by child process.
- gstack relation: plugs into `/review` Race Conditions & Concurrency critical category.
