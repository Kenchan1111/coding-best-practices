# Dict_AI_Coding Worktree Execution Dependencies Map

## Goal

Map how executable workflows depend on scripts, skill assets, review notes,
state files, local-only evidence, and service files. This complements the
authority and artifact maps by showing which files must stay together for the
repo to keep working.

## Dependency Legend

- `entrypoint`: directly executed by operator, service, or package script
- `library`: imported or reused by an entrypoint
- `state`: file consumed or produced during execution
- `evidence`: proof or receipt required by a workflow or guard
- `optional`: reachable only in non-primary workflows

## Skill Authoring And Validation Cluster

### Entrypoints

- `node scripts/sync-catalog.ts`
- `node scripts/gen-skill-docs.ts`
- `node scripts/validate.ts`
- `python3 -m unittest discover -s skill/tests -p 'test_*.py'`
- `skill/setup`
- `skill/uninstall`

### Libraries and supporting files

- `scripts/skill-lib.ts`
- `findings/01_bug_catalog.md`
- `skill/SKILL.md.tmpl`
- `skill/catalog/bug_catalog.md`
- `skill/checks/*.md`
- `skill/triggers/*.md`
- `skill/hosts/*.md`
- `skill/README.md`
- `skill/bin/README.md`
- `package.json`

### Required state and evidence

- `skill/SKILL.md` as generated output
- `environment.yml` and `environment.lock.linux-64.txt` when Conda fallback is
  needed by setup
- `skill/tests/*` including:
  - `skill/tests/frontmatter_utils.py`
  - `skill/tests/e2e/mock_agent.py`
  - `skill/tests/e2e/run.sh`

### Execution graph

1. `scripts/sync-catalog.ts` reads `findings/01_bug_catalog.md`
2. it writes `skill/catalog/bug_catalog.md`
3. `scripts/gen-skill-docs.ts` forces catalog freshness, reads the template and
   trigger/check docs, then writes `skill/SKILL.md`
4. `scripts/validate.ts` checks the structure and canonical drift of the skill
   surfaces
5. `skill/setup` runs generated-doc and validation steps before linking the
   skill into host directories
6. `skill/uninstall` removes only managed links and does not change repo source

### Cleanup relevance

- `skill/` and `scripts/*.ts` are a single runtime cluster; cleanup must not
  archive generated outputs without keeping the authoring inputs together
- `skill/bin/README.md` is structure/documentation, not throwaway placeholder

## Review Sync Cluster

### Entrypoints

- `python3 scripts/sync_reviews.py`
- `python3 scripts/sync_reviews.py --once`

### Libraries and supporting files

- `scripts/knowledge_os.py`
- `REVIEW_SYNC.md`
- `skill/tests/test_knowledge_os.py`

### Required state and evidence

- `reviews/<agent>/handoff/*.md`
- `reviews/<agent>/proposition/*.md`
- `reviews/<agent>/corrections/*.md`
- `reviews/global_handoff/*.md`
- `knowledge/80_summaries/*.md`
- `mcp/catalog.json`

### Execution graph

1. source agents write notes under their own `reviews/<agent>/...` trees
2. `scripts/sync_reviews.py` discovers agents via `knowledge_os.py`
3. source handoffs are collected into `reviews/global_handoff/`
4. global handoffs are diffused as managed copies to peers
5. summaries are regenerated under `knowledge/80_summaries/`
6. `mcp/catalog.json` is refreshed for navigation/catalog consumers

### Cleanup relevance

- `reviews/`, `knowledge/80_summaries/`, and `mcp/catalog.json` form one live
  workflow, even though only part of it is local-only
- moving `reviews/` would change real sync behavior, not just documentation

## Review Watcher And Service Cluster

### Entrypoints

- `python3 scripts/sync_reviews_watch.py`
- installed user service generated from
  `systemd/dict-ai-coding-review-sync-watch.service`
- `bash install-review-sync-user-service.sh`

### Libraries and supporting files

- `scripts/sync_reviews.py`
- `scripts/knowledge_os.py`
- `systemd/dict-ai-coding-review-sync-watch.service`
- `install-review-sync-user-service.sh`
- `skill/tests/test_sync_reviews_watch.py`

### Required state and evidence

- repo-root Markdown and receipt sidecars watched by the watcher
- `reviews/` trees
- `reviews/global_handoff/`
- local generated summaries and catalog after sync runs

### Execution graph

1. the installer templates `{{REPO_DIR}}` into the user service file
2. the service launches `scripts/sync_reviews_watch.py`
3. watcher mode monitors repo Markdown/receipt events, excluding caches and
   generated summaries
4. relevant changes trigger `scripts/sync_reviews.py --once`

### Cleanup relevance

- moving `reviews/`, watcher sources, or the service template would break live
  automation
- `knowledge/80_summaries/` is intentionally skipped as a watched source

## Local-Git Integrity Cluster

### Entrypoints

- `python3 scripts/local_git_guard.py build-manifests`
- `python3 scripts/local_git_guard.py verify --strict`
- `python3 scripts/local_git_guard.py install-hooks --set-hooks-path`
- `.githooks/pre-commit`
- `.githooks/pre-push`

### Libraries and supporting files

- `scripts/local_git_guard.py`
- `ops/local_git_policy.json`
- `ops/local_git_manifests/index.json`
- `ops/local_git_manifests/*.json`
- `.gitignore`
- `skill/tests/test_local_git_guard.py`

### Required state and evidence

- local-only payload roots:
  - `change_sessions/`
  - `review_sessions/`
  - `knowledge/80_summaries/`
  - `mcp/`
- tracked Git index state for pushable files

### Execution graph

1. the policy defines the local-only roots and ignore rules
2. `build-manifests` inventories each local-only root plus pushable tracked
   files
3. manifests are written under `ops/local_git_manifests/`
4. hooks refresh/verify manifests and block payload leakage

### Cleanup relevance

- cleanup batches must treat the current local-git boundary as an invariant
- a new local proof session or summary is expected to create manifest drift
  until manifests are rebuilt
- `review_sessions/` can be absent without indicating breakage

## Guard-Produced Proof Cluster

### Entrypoints

- external `repo-change-guard` workflow
- external `repo-review-snapshot` workflow

### Repo-local outputs they depend on

- `change_sessions/*`
- `review_sessions/*`
- `mcp/repo-change-guard/*`
- review note receipt sidecars under `reviews/`

### Execution graph

1. the external guard or snapshot tool opens a session
2. it records scope, checks, and worktree state into local proof trees
3. sealed notes or closeouts may produce receipt sidecars
4. local-git manifests must be refreshed if these outputs changed

### Cleanup relevance

- the producing tool may live outside this repo, but the outputs are still part
  of this repo's cleanup surface
- cleanup must preserve proof directories even when they are ignored by Git

## Non-Execution Reference Surfaces

These paths are useful for analysis but are not required by the repo runtime:

- `gstack/`
- `dictionary-of-ai-coding/`

Cleanup may relocate them later without breaking product or sync execution,
provided provenance is preserved.

## Dependency Findings Relevant To Cleanup

- `skill/` plus `scripts/{sync-catalog,gen-skill-docs,validate}.ts` is one
  coupled authoring cluster and is not an archive candidate.
- `reviews/`, `knowledge/80_summaries/`, and `mcp/catalog.json` form a live
  review-sync graph; they are not independent clutter.
- `change_sessions/`, `review_sessions/`, and `mcp/repo-change-guard/` are
  local proof surfaces, not disposable scratch output.
- watcher/service automation depends on the repo-root path layout staying
  stable.
- `gstack/` and `dictionary-of-ai-coding/` are the safest future non-source
  relocation candidates because nothing in the repo runtime imports them.
