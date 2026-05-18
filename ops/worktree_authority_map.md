# Dict_AI_Coding Worktree Authority Map

## Goal

Classify the current worktree by authority, not by whether Git already tracks a
path. In this repo, "untracked" often means "new active implementation".

## Canonical Source

These paths are active source and should be versioned or otherwise frozen before
cleanup:

- `skill/`: the `coding-best-practices` skill payload, generated `SKILL.md`,
  template, host notes, checks, triggers, setup, uninstall, fixtures, and tests.
- `scripts/`: generator, validator, catalog sync, review sync, watcher, and
  knowledge helper.
- `systemd/dict-ai-coding-review-sync-watch.service`: source unit for the user
  watcher installation.
- `install-review-sync-user-service.sh`: installer for the systemd user unit.
- `package.json`: Node/npm command contract for validation and docs generation.
- `environment.yml` and `environment.lock.linux-64.txt`: reproducible Conda
  environment evidence for the repo.
- `REVIEW_SYNC.md`: review synchronization operating contract.
- `CLAUDE.md`, `ARCHITECTURE.md`, `TODOS.md`, `ONBOARDING_*.md`,
  `findings/*.md`: project governance, roadmap, and source bug catalogue.

## Review Bus Authority

The review bus has mixed authority:

- `reviews/gpt-5.5/proposition/*.md`: GPT-5.5 source proposals.
- `reviews/gpt-5.5/handoff/*.md`: GPT-5.5 source handoffs unless frontmatter
  says `sync_managed_copy: true`.
- `reviews/gpt-5.5/corrections/*.md`: GPT-5.5 source corrections.
- `reviews/claude-opus/proposition/*.md`: Opus source proposals.
- `reviews/claude-sonnet/proposition/*.md`: Sonnet source proposals.
- `reviews/kimi/proposition/*.md`: Kimi source proposals.
- `reviews/global_handoff/*.md`: shared handoff reservoir and sync hub.
- peer handoff copies under other agents: `managed_projection` when frontmatter
  has `sync_managed_copy: true`.

Rule: do not edit a managed projection as source. Edit the source note, then let
`scripts/sync_reviews.py` propagate.

## Generated Evidence

These paths are generated but still valuable evidence:

- `mcp/repo-change-guard/*`: change sessions, closeouts, receipts, and proof
  artifacts from repo-change-guard.
- `change_sessions/*`: compatibility or imported change receipts.
- `mcp/catalog.json`: generated MCP/review catalog.
- `knowledge/80_summaries/*.md`: generated team review digest, changelog, and
  latest summary.

These are not disposable. They are candidates for a future
`local_git_manifested` policy if the repo should not push raw local evidence.

## Runtime State

Current runtime state is mostly outside the repo:

- installed user service under `~/.config/systemd/user/`
- systemd runtime logs and process state

The repo-local service file remains canonical source, not runtime state.

## Reference Clones

These are ignored external repo clones used for analysis:

- `gstack/`
- `dictionary-of-ai-coding/`

They have their own `.git` directories and should stay ignored. They should not
be committed inside this repo. If long-term provenance is needed, record their
remote URL and commit hash in a small tracked manifest rather than tracking
their payload.

## Compiled Noise

These are fully rebuildable and strongest archive-or-ignore candidates:

- `scripts/__pycache__/`
- `skill/tests/__pycache__/`
- `skill/tests/e2e/__pycache__/`
- `skill/tests/fixtures/planted-bugs/__pycache__/`

Even these should not be deleted by default. If they must leave the active
worktree, move them to a manifest-backed archive, or keep them ignored as local
rebuildable cache.

## Open Arbitration Points

- whether `reviews/`, `knowledge/`, `mcp/`, and `change_sessions/` remain
  tracked payloads or become `local_git_manifested`
- whether `gstack/` should stay as a local ignored clone or be replaced by a
  tracked reference manifest
- whether generated review summaries should be committed or treated as local
  projections
