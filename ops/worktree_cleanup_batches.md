# Dict_AI_Coding Worktree Cleanup Batches

## Goal

Define the cleanup order for this repo. The order intentionally avoids hiding
active untracked source behind `.gitignore` before the source is frozen.

## Batch 0 - Freeze And Source Commit

Status: required before archive moves.

Actions:

- create `safety/worktree-cleanup-YYYYMMDD` or a Git bundle
- commit or otherwise freeze canonical source surfaces
- include `skill/`, `scripts/`, `systemd/`, setup files, governance docs,
  `findings/`, and source review notes
- run the validation gate before and after the freeze

Do not perform `git clean` during this batch.

## Batch A - Compiled Noise Archive

Status: safe after Batch 0.

Candidate paths:

- `scripts/__pycache__/`
- `skill/tests/__pycache__/`
- `skill/tests/e2e/__pycache__/`
- `skill/tests/fixtures/planted-bugs/__pycache__/`

Preferred action:

- keep ignored in place by default
- if the active worktree must be cleared, move the cache directories to a
  manifest-backed archive
- do not delete cache directories as part of normal cleanup

Restore rule:

- restore from archive if provenance matters
- rerun Python tests to regenerate caches if only runtime bytecode is needed

## Batch B - Local-Git Manifest Boundary

Status: implemented for evidence roots; review bus still pending.

Implemented local-only roots:

- `change_sessions/`
- `review_sessions/`
- `knowledge/80_summaries/`
- `mcp/`

Implemented pieces:

- a policy file such as `ops/local_git_policy.json`
- generated manifests under `ops/local_git_manifests/`
- pre-commit and pre-push verification hooks
- `.gitignore` entries only after manifests exist

Rationale:

- preserves filenames, sizes, hashes, and Merkle-style roots without pushing raw
  collaboration payloads

## Batch C - Review Bus Normalization

Status: blocked until review bus policy is final.

Rules to preserve:

- source-agent notes are authoritative
- managed projections are identified by `sync_managed_copy: true`
- `reviews/global_handoff/` remains the shared reservoir until a replacement is
  designed
- no handoff or proposition is overwritten

Potential future cleanup:

- replace redundant peer copies with manifests
- keep `global_handoff` as generated integration surface
- keep source proposals and corrections versioned

## Batch D - Reference Clone Policy

Status: optional.

Current ignored clones:

- `gstack/`
- `dictionary-of-ai-coding/`

Preferred action:

- keep ignored locally
- add a tracked reference manifest only if long-term reproducibility matters

Do not commit these clones directly. `gstack/` is large and contains its own
dependency tree.

## Batch E - Archive Candidates

Status: none approved yet.

No document or review artifact is currently approved for archive.

If future archive candidates appear, each batch must include:

- `manifest.json`
- original path
- archived path
- classification
- reason
- restore rule
- validation result after the move
