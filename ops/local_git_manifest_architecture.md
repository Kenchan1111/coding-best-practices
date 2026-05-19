# Dict_AI_Coding Local Git Manifest Architecture

## Goal

Keep local evidence payloads on disk without pushing their raw contents to the
remote repository.

This repo now distinguishes:

- `pushable_versioned`: tracked source and documentation intended for GitHub
- `local_git_manifested`: local payload kept in the worktree but represented by
  pushable manifests
- `generated_rebuildable`: caches or bytecode that can be rebuilt locally

## Local-Only Roots

The canonical list lives in [local_git_policy.json](./local_git_policy.json).

Current roots:

- `change_sessions/`
- `review_sessions/`
- `knowledge/80_summaries/`
- `mcp/`

These roots stay present on the workstation. The policy does not delete them and
does not archive them by default.

## Pushable Artifacts

The payload bodies stay local, but these artifacts are pushable:

- [local_git_policy.json](./local_git_policy.json)
- `ops/local_git_manifests/index.json`
- `ops/local_git_manifests/<root>.json`
- `ops/local_git_manifests/pushable_tracked.json`
- `scripts/local_git_guard.py`
- `.githooks/pre-commit`
- `.githooks/pre-push`
- tests for the guard

## Integrity Model

The guard maintains two deterministic manifest layers:

1. one manifest per local-only root
2. one manifest for pushable tracked files, excluding local-only roots and the
   manifest directory itself

Each manifest records:

- exact relative paths
- file sizes
- SHA-256 digests
- symlink targets when applicable
- a Merkle root over the manifest leaves

This preserves structural evidence without pushing the local payload bodies.

## Enforcement

The guard script is [local_git_guard.py](/home/zack/Documents/Divers/Dict_AI_Coding/scripts/local_git_guard.py:1).

Git hooks call it automatically:

- [pre-commit](/home/zack/Documents/Divers/Dict_AI_Coding/.githooks/pre-commit:1)
- [pre-push](/home/zack/Documents/Divers/Dict_AI_Coding/.githooks/pre-push:1)

### Bootstrap In A Clone

Run once per clone:

`python3 scripts/local_git_guard.py install-hooks --set-hooks-path`

This sets `core.hooksPath=.githooks` in local Git config.

### Pre-commit

- refreshes local manifests
- stages updated manifest files
- rejects tracked or staged leakage under local-only roots

### Pre-push

- verifies manifests are current
- rejects push if local-only roots drifted without refreshed manifests

## Migration Rule

When a new path becomes `local_git_manifested`:

1. add it to `ops/local_git_policy.json`
2. add its ignore rule to `.gitignore`
3. if already tracked, remove it from the Git index with `git rm --cached`
4. rebuild manifests
5. commit the policy and manifests, not the payload body

## Current Boundary Choice

`reviews/` is intentionally not part of this local-only policy yet. The review
bus remains pushable until its authority model is arbitrated across models.
