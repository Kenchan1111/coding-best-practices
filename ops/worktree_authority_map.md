# Dict_AI_Coding Worktree Authority Map

## Goal

Classify the worktree by authority and operational role, not by whether Git
currently tracks a path. In this repo, "untracked" or "ignored" can still mean
"active local protocol surface".

## Canonical Source

These paths are active source and must be treated as primary authority:

- `skill/`: the `coding-best-practices` skill payload, generated `SKILL.md`,
  template, checks, triggers, hosts, setup/uninstall, support notes, and
  tests.
- `scripts/`: catalog sync, validation, generated-doc rendering, review sync,
  watcher, knowledge helpers, and local-git guard tooling.
- `ops/`: cleanup policy, local-git policy, authority maps, dependency maps,
  and cleanup runbooks.
- `systemd/dict-ai-coding-review-sync-watch.service`: source user unit for the
  review watcher.
- `install-review-sync-user-service.sh`: installer for the user systemd unit.
- `package.json`: Node/npm command contract.
- `environment.yml` and `environment.lock.linux-64.txt`: reproducible Conda
  environment contract.
- `REVIEW_SYNC.md`: source operating contract for review synchronization.
- `CLAUDE.md`, `ARCHITECTURE.md`, `TODOS.md`, `ONBOARDING_*.md`,
  `findings/*.md`: governance, roadmap, onboarding, and source bug catalogue.
- `.githooks/pre-commit` and `.githooks/pre-push`: enforced Git boundary
  behavior for the repo clone.

Rule: cleanup never archives or hides `canonical_source` in an initial pass.

## Review Bus Authority

The review bus has mixed authority and must be handled path-by-path:

- `reviews/<agent>/proposition/*.md`: source proposal notes owned by that
  agent.
- `reviews/<agent>/handoff/*.md`: source handoffs unless frontmatter marks them
  as `sync_managed_copy: true`.
- `reviews/<agent>/corrections/*.md`: source corrections owned by that agent.
- `reviews/global_handoff/*.md`: shared synchronization reservoir and active
  integration surface.
- peer handoff copies under other agents: `managed_projection` when frontmatter
  carries `sync_managed_copy: true`.
- `*.md.receipt.json` sidecars: `generated_evidence` proving sealing or review
  note integrity.

Rule: do not edit a managed projection as source. Edit the source note, then
let `scripts/sync_reviews.py` propagate.

## Generated Evidence Kept On Disk

These paths are generated, but remain operationally important:

- `change_sessions/*`: local change-proof sessions, snapshots, closeouts, and
  receipts.
- `review_sessions/*`: future local review-proof sessions; the root may be
  absent until a review snapshot creates it.
- `mcp/repo-change-guard/*`: historical sealed proof sessions and closeouts.
- `knowledge/80_summaries/*.md`: generated digest, latest view, and changelog
  for team review state.
- `mcp/catalog.json`: generated catalog/index surface for review consumers.
- `ops/local_git_manifests/*.json`: pushable structural evidence describing the
  local-only payload roots.

These are not disposable output. They are either already under the active
`local_git_manifested` boundary or are the pushable manifests that describe
that boundary.

## Runtime State

Current runtime state is mostly outside the repo:

- installed user service under `~/.config/systemd/user/`
- systemd runtime state and logs
- running watcher process state

Repo-local service files remain `canonical_source`, not runtime state.

## Reference Clones

These are ignored external repo clones used for analysis:

- `gstack/`
- `dictionary-of-ai-coding/`

They have their own `.git` directories and are not source for this repo. If
long-term provenance is needed, record remote URL and commit hash in a tracked
reference note rather than versioning the payload.

## Compiled Noise

These are the strongest cleanup candidates once archive policy is executed:

- `scripts/__pycache__/`
- `skill/tests/__pycache__/`
- `skill/tests/e2e/__pycache__/`
- `skill/tests/fixtures/planted-bugs/__pycache__/`
- other ignored bytecode/test-cache surfaces matched by `.gitignore`

Even these remain "keep or archive", not "delete by default".

## Future Archive Surface

If a real cleanup batch later archives files, authority is split as follows:

- `archive/worktree_cleanup/<batch>/manifest.json`: `generated_evidence`
- `archive/worktree_cleanup/<batch>/notes.md`: `generated_evidence`
- `archive/worktree_cleanup/<batch>/payload/...`: archived copies of the moved
  items; each item keeps its original classification in the manifest

This archive surface is not active yet and is not part of the current
`local_git_manifested` boundary by default.

## Open Arbitration Points

- whether `reviews/` should remain pushable forever or later join a local-only
  collaboration boundary
- whether `gstack/` and `dictionary-of-ai-coding/` should stay as ignored local
  clones or gain a small tracked provenance manifest
- whether future cleanup archives should themselves become local-only payload
  roots or remain ordinary tracked structure plus local payload
