# Dict_AI_Coding Worktree Cleanup Architecture

## Goal

Prepare and execute worktree cleanup without deleting information, without
collapsing the current collaboration bus, and without hiding active source
behind ignore rules.

This repo is a live skill-development workspace. A large part of the tree is
either active source (`skill/`, `scripts/`, `ops/`, `systemd/`, governance
docs) or active evidence/sync state (`reviews/`, `change_sessions/`,
`knowledge/80_summaries/`, `mcp/`). Cleanup must therefore be policy-driven,
not "remove what looks noisy".

## Current Operating State

The cleanup protocol starts from these facts:

- `change_sessions/`, `review_sessions/`, `knowledge/80_summaries/`, and
  `mcp/` are already under the active `local_git_manifested` boundary.
- `reviews/` remains pushable and is still part of the live review bus.
- `gstack/` and `dictionary-of-ai-coding/` are ignored `reference_clone`
  surfaces, not repo source.
- Python caches and similar rebuildable outputs are ignored
  `compiled_noise`, but are not deleted by default.
- Baseline counts drift quickly in this repo because proof sessions and review
  digests are generated locally. Batch 0 must therefore recapture the live
  baseline instead of trusting historical counts.

## Legal Cleanup Actions

Normal cleanup batches may only do one of the following:

- keep a path in place
- move a path to a manifest-backed archive
- leave a path for later arbitration
- keep a path local-only via the existing `local_git_manifested` policy

Default policy: never delete.

The following are outside the protocol unless the user explicitly requests them
for a narrow target:

- `git clean -fdx`
- `git reset --hard`
- broad `rm -rf`
- broad `git checkout --`
- broad `git restore`

## Authority Classes

- `canonical_source`: source of truth to edit when behavior or policy changes.
- `managed_projection`: synchronized/generated copy; do not edit directly.
- `generated_evidence`: generated artifact kept because it proves review,
  change, sync, or guard execution.
- `runtime_state`: local mutable state for services or watchers.
- `reference_clone`: external repo clone used for analysis, ignored by Git.
- `compiled_noise`: bytecode or cache output, fully rebuildable.
- `archive_candidate`: movable only after freeze, manifest, and validation.
- `local_git_manifested`: local payload kept on disk while its structural
  manifests remain pushable.

## Mandatory Preflight

No cleanup batch may begin before this preflight is complete.

### 1. Freeze safety

Create a reversible safety point first:

- a dedicated safety branch, or
- a Git bundle, or
- both

### 2. Confirm canonical source is frozen

Before any archive move, confirm that active source is already committed or
otherwise explicitly frozen:

- `skill/`
- `scripts/`
- `ops/`
- `systemd/`
- setup/install surfaces
- governance docs and `findings/`

Archive-first protects against destructive cleanup mistakes. It does not repair
missing history on live source.

### 3. Refresh local-git evidence if local proof drifted

If a new local proof session, summary, or MCP artifact was created since the
last manifest refresh:

```bash
python3 scripts/local_git_guard.py build-manifests
python3 scripts/local_git_guard.py verify --strict
```

Cleanup must not proceed from a stale `local_git` boundary.

### 4. Reconfirm the execution dependency map

Before moving any path, verify that the current dependency cartography still
matches the repo:

- `ops/worktree_authority_map.md`
- `ops/worktree_generated_artifacts_map.md`
- `ops/worktree_execution_dependencies_map.md`
- `ops/worktree_cleanup_batches.md`

If a candidate path is still consumed by an active entrypoint, it leaves the
cleanup batch and returns to arbitration.

## Validation Gate

Minimum validation before Batch 0 and after every executed batch:

- `python3 -m unittest discover -s skill/tests -p 'test_*.py'`
- `node scripts/validate.ts`
- `node scripts/gen-skill-docs.ts --dry-run`
- `python3 scripts/sync_reviews.py --once`
- `python3 scripts/local_git_guard.py verify --strict`
- `git diff --check`

If a future batch changes watcher/service surfaces, also validate the installed
user service contract manually before closeout.

## Archive-First Layout

If a real archive batch is executed, use this layout:

```text
archive/
  worktree_cleanup/
    <batch_id>/
      manifest.json
      notes.md
      payload/
        <original relative paths preserved here>
```

Every archived item must have:

- an original path
- an archived path
- a classification
- a written reason
- a restore rule

`archive/worktree_cleanup/` is not automatically part of the current
`local_git_manifested` boundary. If cleanup starts creating archive payloads
there, that boundary decision must be documented explicitly.

## Non-Goals For The Current Cleanup Preparation

- no document deletion
- no cleanup-by-memory
- no review note overwrite
- no broad archive of `reviews/`
- no extension of the local-only boundary to `reviews/`
- no physical movement of source, evidence, or clones in this preparation lot
