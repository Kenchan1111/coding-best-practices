# Dict_AI_Coding Worktree Cleanup Batches

## Goal

Turn the archive-first cleanup architecture and the worktree cartographies into
an executable sequence without deleting information or destabilizing the review
bus.

This document is operational. It assumes:

- cleanup is reversible
- no direct deletion is allowed in normal batches
- the current `local_git_manifested` boundary is already active
- `reviews/` remains pushable until a separate arbitration changes that policy

## Global Preconditions

Before any executed batch:

1. create a safety freeze:
   - branch, bundle, or both
2. confirm `canonical_source` is already committed or otherwise frozen
3. refresh and verify local manifests if local evidence changed:
   - `python3 scripts/local_git_guard.py build-manifests`
   - `python3 scripts/local_git_guard.py verify --strict`
4. rerun the minimum guard basket:
   - `python3 -m unittest discover -s skill/tests -p 'test_*.py'`
   - `node scripts/validate.ts`
   - `node scripts/gen-skill-docs.ts --dry-run`
   - `python3 scripts/sync_reviews.py --once`
   - `git diff --check`

## Global Stop Rules

Stop the batch immediately if:

- a candidate path is still consumed by an active entrypoint in
  `ops/worktree_execution_dependencies_map.md`
- local manifests drift unexpectedly after a move
- `reviews/` or other source notes would need to be overwritten
- a path has no restore rule
- a path is still under policy arbitration

## Batch 0 - Freeze and Baseline Capture

### Intent

Re-establish a trustworthy baseline before any archive motion begins.

### Scope

Freeze, not archive:

- `skill/`
- `scripts/`
- `ops/`
- `systemd/`
- setup/install surfaces
- governance docs and `findings/`
- source review notes that are meant to remain versioned

### Required actions

- capture the exact starting revision
- confirm that ignored/local-only trees are classified, not mistaken for noise
- verify the current local-git boundary
- record any pending arbitration before later batches run

### Output

- a restorable baseline
- a live validation snapshot
- no file movement

## Batch A - Compiled Noise Only

### Intent

Handle the safest rebuildable surfaces first.

### Candidate paths

- `scripts/__pycache__/`
- `skill/tests/__pycache__/`
- `skill/tests/e2e/__pycache__/`
- `skill/tests/fixtures/planted-bugs/__pycache__/`
- other ignored cache/bytecode surfaces matched by `.gitignore`

### Explicit exclusions

- no source under `skill/`
- no `reviews/`
- no `change_sessions/`
- no `knowledge/80_summaries/`
- no `mcp/`

### Default action

- keep ignored caches in place by default
- if a cleaner worktree is desired, move caches to a manifest-backed archive
- do not delete

### Post-batch validation

- rerun the minimum guard basket
- ensure no active script now points at an archived cache path

## Batch B - Local-Git Boundary Verification

### Intent

Treat the existing local-only boundary as a cleanup invariant.

### Scope

Verify only:

- `change_sessions/`
- `review_sessions/`
- `knowledge/80_summaries/`
- `mcp/`
- `ops/local_git_manifests/*`

### Required actions

- rebuild manifests if any local evidence changed
- verify strict consistency
- confirm that no tracked or staged payload leaked under local-only roots
- confirm that `review_sessions/` may legitimately be absent

### Output

- a green `local_git` boundary that later batches may rely on

### Blockers

- do not change the boundary in this batch
- do not move `reviews/` here

## Batch C - Reference Clone Handling

### Intent

Reduce repo-root clutter from external clones without touching product source or
protocol evidence.

### Candidates

- `gstack/`
- `dictionary-of-ai-coding/`

### Default rule

- keep ignored locally if they remain useful
- archive only if the operator explicitly wants a cleaner active tree
- never commit the clone payloads to this repo

### Required manifest details if archived

- remote/provenance note
- observed commit hash when available
- reason for relocation
- restore rule back to repo root or another declared reference location

### Post-batch validation

- rerun the minimum guard basket
- confirm no live script depends on clone contents

## Batch D - Review Bus And Other Blocked Surfaces

### Intent

List surfaces that are not cleanup candidates until governance changes.

### Explicitly blocked surfaces

- `reviews/`
- `reviews/global_handoff/`
- peer managed copies
- source proposals, handoffs, and corrections
- local-git policy files themselves
- active source under `skill/`, `scripts/`, `ops/`, `systemd/`

### Rule

- this batch moves nothing
- it records pending decisions only

## Batch E - Future Archive Candidates

### Intent

Define how a later archive wave must behave once a new candidate is approved.

### Approval requirements

Every approved archive candidate must have:

- a fixed classification
- a written reason
- a restore rule
- a batch manifest entry
- post-batch validation proof

No document, review artifact, or evidence payload is pre-approved for archive
just because it is old.

## Archive Manifest Minimum

Every executed archive batch must produce:

- `archive/worktree_cleanup/<batch_id>/manifest.json`
- `archive/worktree_cleanup/<batch_id>/notes.md`
- `archive/worktree_cleanup/<batch_id>/payload/...`

Each manifest entry must contain:

- `original_path`
- `archived_path`
- `classification`
- `reason`
- `restore_rule`

## What This Runbook Does Not Do

- it does not execute file moves by itself
- it does not settle the `reviews/` authority question
- it does not widen the `local_git_manifested` boundary
- it does not authorize destructive cleanup
