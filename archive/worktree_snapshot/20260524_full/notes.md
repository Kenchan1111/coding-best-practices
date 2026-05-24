# Full Worktree Snapshot 20260524

## Purpose

This branch stores a reconstructible archive snapshot of local workspace payloads that are intentionally not part of the product branch. The product branch remains governed by `local_git_manifested`; this snapshot is a backup/restoration artifact, not a policy change.

## Source

- base_branch: `feature/skill-phase1-scaffolding`
- base_commit: `366f611c6cca8fac2dc0fe247ca9e88554652375`
- snapshot_branch: `snapshot/full-worktree-20260524`
- combined_payload_sha256: `f7e4bae8e98f610b783c5d8a7da2574d0c0bf1d15af11f709017e2f9246da24e`

## Included Payloads

- `change_sessions/`
- `knowledge/`
- `mcp/`
- Python cache directories observed in the worktree
- `dictionary-of-ai-coding/`, including its `.git` directory
- `gstack/`, including its `.git` directory and local modifications

## Restore

From this directory:

```bash
cat payload.tar.zst.part-* > payload.tar.zst
tar --zstd -xf payload.tar.zst -C /path/to/restore
```

Expected reconstruction model:

1. Check out the base commit in a target directory.
2. Extract the payload archive on top of that checkout.
3. Verify nested repositories with `git -C gstack status --short` and `git -C dictionary-of-ai-coding status --short`.

## Notes

- Chunks are kept below GitHub's single-file size limit target.
- `gstack/` is intentionally captured as archive payload because it is a modified nested Git repository, not a normal tracked subtree.
- This snapshot does not convert nested repositories into submodules.
