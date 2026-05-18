---
reviewer: GPT-5.5
date: 2026-05-07
scope: gstack gbrain integration + upstream gbrain API/code spot-check
status: proposed
---

# GBrain Implementation Review

## Scope

- GStack local repo reviewed at `bf65487162ce5e4330efc43632ca945b640ebc16`.
- Upstream `garrytan/gbrain` cloned read-only to `/tmp/gbrain-review` at `bfab1ded089662823e24e3a1e09e874dc16ae88d`.
- Public doc checked: <https://github.com/garrytan/gstack/blob/main/USING_GBRAIN_WITH_GSTACK.md>.

## Findings

### High - GStack emits invalid GBrain CLI save/read commands

`gstack/scripts/resolvers/gbrain.ts:21-25` tells agents to run `gbrain search` then `gbrain get_page "<page_slug>"`; `gstack/scripts/resolvers/gbrain.ts:41-62` tells agents to persist with `gbrain put_page --title ... --tags ...`.

Upstream GBrain exposes operation names `get_page` / `put_page` for MCP, but CLI aliases are `gbrain get <slug>` and `gbrain put <slug> < stdin`:

- `/tmp/gbrain-review/src/core/operations.ts:322-356` defines op `get_page` with CLI hint `get`.
- `/tmp/gbrain-review/src/core/operations.ts:359-507` defines op `put_page` with required params `slug` and `content`, CLI hint `put`, and stdin content.
- `/tmp/gbrain-review/src/cli.ts:824-840` documents `get`, `put`, `search`, `query`.

Impact: if MCP is not registered, generated GStack skills fall back to shell commands that do not match upstream GBrain. Saves and follow-up page reads can silently fail or be treated as transient failures, so the "brain compounds" loop does not actually persist outputs.

Fix direction: update the resolver to either call MCP tool names explicitly when MCP is available, or emit valid CLI fallback:

```bash
gbrain get "<slug>"
gbrain put "<slug>" <<'EOF'
---
title: ...
tags: [...]
---
...
EOF
```

Add a golden/validation test that generated skills do not contain `gbrain put_page` or `gbrain get_page` inside Bash snippets.

### High - Secret URL is passed through argv despite the documented invariant

`gstack/USING_GBRAIN_WITH_GSTACK.md:204-210` and `gstack/setup-gbrain/SKILL.md.tmpl:593-599` state that DB URLs must be env-only, never argv. But `gstack/setup-gbrain/SKILL.md.tmpl:375-390` captures `GBRAIN_URL` and invokes:

```bash
gstack-gbrain-source-wireup --strict ${GBRAIN_URL:+--database-url "$GBRAIN_URL"}
```

The helper accepts `--database-url` at `gstack/bin/gstack-gbrain-source-wireup:58-66` and prioritizes it at `gstack/bin/gstack-gbrain-source-wireup:71-78`.

Impact: Supabase pooler URLs contain the database password. Passing them as an argv flag can expose them through shell history, terminal scrollback, process listings, audit tools, and crash reports. This directly contradicts the security model the docs ask reviewers/users to trust.

Fix direction: remove `--database-url` from the public helper path. Use `GBRAIN_DATABASE_URL="$GBRAIN_URL" gstack-gbrain-source-wireup --strict` or let the helper read `~/.gbrain/config.json` internally. Add a validation test that rejects `--database-url` in setup templates/docs for secret-bearing URLs.

### Medium - Sync/import wrapper can report success after failed subprocesses

`gstack/bin/gstack-gbrain-sync.ts:158-174` runs `spawnSync("gbrain", importArgs, ...)` and then returns `ok: true` without inspecting `status`, `error`, `signal`, or timeout. The same function also ignores the `gbrain embed --stale` result.

Impact: the state file can record an apparently successful sync even when `gbrain import` failed. Downstream reviewers/operators then see false-positive health, while the brain was not indexed.

Fix direction: check `spawnSync` results with a shared helper. Treat non-zero status, `error`, signal, and timeout as failed stage summaries. Add a test with a fake `gbrain` that exits non-zero.

### Medium - Context loader likely treats installed gbrain as missing

`gstack/bin/gstack-brain-context-load.ts:193-200` checks availability using `execFileSync("command", ["-v", "gbrain"])`. `command` is normally a shell builtin, not an external executable. A local Node probe returned `ERR:EPERM`, and on ordinary Node this commonly fails with no external `command` binary.

Impact: the deterministic context loader can skip vector/list queries even when `gbrain` is installed. Current tests allow either OK or SKIP, so this regression is not pinned.

Fix direction: use `execFileSync("sh", ["-c", "command -v gbrain"], ...)` or a direct PATH scan. Add a fake PATH test where `gbrain` exists and the loader must not SKIP.

### Medium - Default context claims repo isolation but one query omits repo filter

`gstack/bin/gstack-brain-context-load.ts:365-368` says each default query carries a `repo:{repo_slug}` filter. The third default query at `gstack/bin/gstack-brain-context-load.ts:388-394` filters only `{ type: "timeline", content_contains: "{skill_name}" }`.

Impact: default skill-name events can bleed across repositories, which contradicts the cross-repo contamination guard documented in the comment.

Fix direction: add `"tags_contains": "repo:{repo_slug}"` to `skill-name-events` and add a manifest/default test that every default query includes the repo tag unless explicitly annotated cross-repo.

### Medium - Secret scanning fails open when gitleaks is absent

`gstack/lib/gstack-memory-helpers.ts:15-17` calls this a "fail-safe" default, but `secretScanFile()` returns `scanner: "missing"` with no findings at `gstack/lib/gstack-memory-helpers.ts:147-153`. `gstack/bin/gstack-memory-ingest.ts:862-870` blocks only when scanner is `gitleaks` and findings are present.

Impact: if `gitleaks` is not installed, transcripts and memory artifacts are still sent to GBrain. That is a privacy leak risk, especially because gstack memory sync is explicitly sold as secret-scanned.

Fix direction: make missing/error scanner a hard skip unless the user passes an explicit unsafe override. Count `skipped_unscanned` separately from `skipped_secret`.

## Positive Architecture Notes

- Upstream GBrain has a better trust split than the current GStack fallback text: CLI aliases are human-local, MCP tools use operation names and scopes, and `put_page` has subagent namespace enforcement.
- GStack's per-remote trust policy is well covered by tests; `git@github.com:foo/bar.git` normalization was checked locally and collapses to `github.com/foo/bar`.
- The Supabase provision wrapper is mostly disciplined: PAT and DB password are env-based, curl stderr is captured, retry classes are explicit, and the URL verifier rejects direct Supabase `db.*:5432` URLs.

## Validation

- `conda run -n coding-best-practices bun test test/gbrain-repo-policy.test.ts test/gstack-brain-context-load.test.ts test/gstack-gbrain-source-wireup.test.ts` passed: 53 tests, 0 failures.
- Local probe: `gstack/bin/gstack-gbrain-repo-policy normalize git@github.com:foo/bar.git` returned `github.com/foo/bar`.
- Upstream GBrain tests were not run because the read-only clone in `/tmp/gbrain-review` did not install dependencies.
