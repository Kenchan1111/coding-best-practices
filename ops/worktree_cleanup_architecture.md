# Dict_AI_Coding Worktree Cleanup Architecture

## Goal

Clean the Dict_AI_Coding worktree without losing source, review evidence, or
synchronization state.

This repo is currently a skill-development repo, not a simple documentation
checkout. A large part of the untracked tree is active product surface:
`skill/`, `scripts/`, `reviews/`, `knowledge/`, `mcp/`, and
`change_sessions/` must not be treated as disposable noise.

## Current Snapshot

- date_local: 2026-05-18
- branch: `feature/skill-phase1-scaffolding`
- git_head: `2d9163f9dccca00b78f7d69c379714a72fa46962`
- reviewed_revision: `2d9163f9dccca00b78f7d69c379714a72fa46962+dirty`
- tracked_modified: 7 files
- untracked_not_ignored: 148 files
- ignored: 23 entries

## Legal Cleanup Actions

Only these actions are allowed during normal cleanup batches:

- keep in place
- move to an archive with a manifest
- mark for later arbitration
- manifest as local-only payload while preserving hashes

Default policy: never delete. If a path should leave the active worktree, archive
it with a manifest first. `git clean -fdx`, `git reset --hard`, broad `rm -rf`,
broad `git checkout --`, and broad `git restore` are outside the cleanup
protocol.

## Authority Classes

- `canonical_source`: source of truth to edit when behavior changes.
- `managed_projection`: synchronized or generated copy; do not edit directly.
- `generated_evidence`: generated artifact kept because it proves a review,
  change, or synchronization event.
- `runtime_state`: local mutable state for services and watchers.
- `reference_clone`: external repo clone used for analysis, ignored by Git.
- `compiled_noise`: bytecode or cache output, fully rebuildable.
- `archive_candidate`: safe only after freeze, manifest, and approval.
- `local_git_manifest_candidate`: local payload that should stay on disk but
  may later be represented by pushable manifests.

## Mandatory Preflight

Before any archive move or local-git migration:

- create a safety branch or Git bundle
- commit or otherwise freeze `canonical_source` surfaces
- generate an inventory of the exact paths to move or manifest
- write an archive or local-manifest policy before moving files
- run validation before and after the batch
- leave review evidence in place until the sync bus policy is explicit

## Validation Gate

Minimum checks for this repo:

- `python3 -m unittest discover -s skill/tests -p 'test_*.py'`
- `node scripts/validate.ts`
- `node scripts/gen-skill-docs.ts --dry-run`
- `python3 scripts/sync_reviews.py --once`

If a future batch changes setup or service files, also validate the user service
unit manually before closing the batch.

## Non-Goals For The First Cleanup Pass

- no document deletion
- no cache deletion
- no review note overwrite
- no broad archive of `reviews/`
- no `.gitignore` hiding of active source before the local-only manifest policy
  is decided
- no migration of `mcp/`, `knowledge/`, or `change_sessions/` without a guard
  equivalent to the Depollution_Sols `local_git_manifested` policy
