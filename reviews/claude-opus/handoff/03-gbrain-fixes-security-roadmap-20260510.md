---
id: 03-gbrain-fixes-security-roadmap-20260510
title: 03-gbrain-fixes-security-roadmap-20260510
status: draft
sync_managed_copy: true
sync_source_path: reviews/global_handoff/03-gbrain-fixes-security-roadmap-20260510.md
sync_source_digest: a1ab3352a284
sync_source_body_digest: 30017734d21f
sync_source_metadata_digest: ff7d18bed0f0
---

## Task Snapshot

- task_session_id: 20260507T235259+0200_gstack
- objective: Fix gbrain integration correctness and security defects found during review
- reviewed_at_local: 2026-05-07T23:52:59.946508+02:00
- cwd: /home/zack/Documents/Divers/Dict_AI_Coding/gstack
- repo_root: /home/zack/Documents/Divers/Dict_AI_Coding/gstack
- git_head: bf65487162ce5e4330efc43632ca945b640ebc16
- reviewed_revision: bf65487162ce5e4330efc43632ca945b640ebc16
- dirty_at_start: False
- expected_files:
  - scripts/resolvers/gbrain.ts
  - setup-gbrain/SKILL.md.tmpl
  - setup-gbrain/SKILL.md
  - USING_GBRAIN_WITH_GSTACK.md
  - bin/gstack-gbrain-source-wireup
  - bin/gstack-gbrain-sync.ts
  - bin/gstack-brain-context-load.ts
  - lib/gstack-memory-helpers.ts
  - bin/gstack-memory-ingest.ts
  - test/gstack-gbrain-source-wireup.test.ts
  - test/gstack-brain-context-load.test.ts
  - test/gstack-gbrain-sync.test.ts
  - test/memory-ingest.test.ts
  - test/skill-validation.test.ts
- risks:
  - preserve gbrain MCP compatibility while fixing CLI fallbacks
  - keep Supabase credentials out of argv/log output
  - do not turn transient sync failures into false success
  - avoid cross-repo context leakage
  - fail closed on unscanned memory content unless explicit unsafe opt-in
- baseline_checks:
  - `conda run -n coding-best-practices bun test test/gstack-gbrain-source-wireup.test.ts test/gstack-brain-context-load.test.ts test/gstack-gbrain-sync.test.ts test/gstack-memory-ingest.test.ts test/skill-validation.test.ts` (phase=baseline, status=failed, exit=1, duration=10.040s)
- baseline_skip_reason: none
- post_change_checks:
  - `conda run -n coding-best-practices bun test test/gstack-gbrain-source-wireup.test.ts test/gstack-brain-context-load.test.ts test/gstack-gbrain-sync.test.ts test/gstack-memory-ingest.test.ts` (phase=post-change, status=passed, exit=0, duration=8.374s)
  - `conda run -n coding-best-practices bun test test/skill-validation.test.ts` (phase=post-change, status=passed, exit=0, duration=5.158s)
  - `conda run -n coding-best-practices bun run scripts/gen-skill-docs.ts --dry-run` (phase=post-change, status=passed, exit=0, duration=4.041s)
  - `conda run -n coding-best-practices bun audit --audit-level=high` (phase=post-change, status=failed, exit=1, duration=4.359s)
- changed_files:
  - CHANGELOG.md
  - README.md
  - USING_GBRAIN_WITH_GSTACK.md
  - bin/gstack-brain-context-load.ts
  - bin/gstack-gbrain-source-wireup
  - bin/gstack-gbrain-sync.ts
  - bin/gstack-memory-ingest.ts
  - bun.lock
  - lib/gstack-memory-helpers.ts
  - package.json
  - scripts/resolvers/gbrain.ts
  - setup-gbrain/SKILL.md
  - setup-gbrain/SKILL.md.tmpl
  - setup-gbrain/memory.md
  - test/gstack-brain-context-load.test.ts
  - test/gstack-gbrain-source-wireup.test.ts
  - test/gstack-gbrain-sync.test.ts
  - test/gstack-memory-ingest.test.ts
  - test/skill-validation.test.ts
- receipt_sidecar: /home/zack/Documents/Divers/Dict_AI_Coding/reviews/gpt-5.5/handoff/03-gbrain-fixes-security-roadmap-20260510.md.change-receipt.json

## Change Summary

- outcome: gbrain integration defects fixed for CLI correctness, secret handling, sync failure semantics, memory-ingest scanning, and dependency hardening. The patch is ready for cross-review, with one explicit dependency audit residual on `fast-uri`.
- key_changes:
  - Replaced invalid shell fallback snippets and runtime calls that used MCP operation names (`put_page`, `get_page`, `list_pages`) with supported gbrain CLI aliases (`put`, `get`, `list`) while keeping MCP terminology in docs where it is actually MCP-only.
  - Removed database URL passing through argv: `gstack-gbrain-source-wireup` now rejects `--database-url` and uses `GBRAIN_DATABASE_URL` / `DATABASE_URL` / config-file fallback instead.
  - Fixed false-success sync paths: dry-run works without a local gbrain binary, real `gbrain import`, `gbrain embed --stale`, and curated sync failures now mark the stage as failed.
  - Made gbrain sync and memory-ingest state writes atomic through temp-file plus rename semantics.
  - Changed memory ingestion to fail closed when gitleaks is unavailable unless `--allow-unscanned` or `GSTACK_MEMORY_INGEST_ALLOW_UNSCANNED=1` is explicitly set.
  - Added a `basic-ftp@5.3.1` Bun override to remove the audited high-risk `basic-ftp@5.2.0` transitive path while preserving the 7-day minimum-release-age install discipline.
  - Updated generated `setup-gbrain/SKILL.md`, user docs, changelog notes, and tests to reflect the corrected CLI/security contract.
- validation:
  - Baseline failed before the fix on `gstack-gbrain-sync` dry-run because it skipped with "gbrain CLI not in PATH" instead of previewing `gbrain import`.
  - Post-change gbrain tests passed: `conda run -n coding-best-practices bun test test/gstack-gbrain-source-wireup.test.ts test/gstack-brain-context-load.test.ts test/gstack-gbrain-sync.test.ts test/gstack-memory-ingest.test.ts`.
  - Full `test/skill-validation.test.ts` passed: 326 tests, including the gbrain command-safety guard.
  - Generated Claude-host skills are fresh: `conda run -n coding-best-practices bun run scripts/gen-skill-docs.ts --dry-run`.
  - Bun install was performed with integrity verification enabled, `--frozen-lockfile`, `--ignore-scripts`, `--minimum-release-age=604800`, and the npm registry pinned.
  - `bun pm untrusted` still reports blocked lifecycle scripts for `onnxruntime-node@1.24.3` and `protobufjs@7.5.5`; they were not trusted or executed.
  - `bun why basic-ftp` now resolves the transitive Puppeteer path to `basic-ftp@5.3.1`, removing the previous 4 high `basic-ftp` audit findings.
  - `rg` found no direct imports of the audited vulnerable packages in changed gbrain runtime surfaces.

## Residual Risks

- `bun audit --audit-level=high` still fails on `fast-uri@3.1.0` through `@anthropic-ai/claude-agent-sdk -> @modelcontextprotocol/sdk -> ajv -> fast-uri`: 2 high advisories remain.
- I did not force `fast-uri@3.1.2` because npm metadata shows it was published on 2026-05-05T08:31:31Z, which is still younger than the 7-day release-age policy on 2026-05-10. Earliest policy-compliant retry: 2026-05-12T08:31:31Z.
- `bun pm scan` is not configured because there is no `[install.security] scanner` in `bunfig.toml`; `bun audit` is the available scanner used here.
- The package-level test command was attempted and failed outside the core gbrain scope: one existing golden mismatch for `ship/SKILL.md` / Factory ship output and missing Playwright browser binaries under `~/.cache/ms-playwright`. This does not invalidate the targeted gbrain tests, but it blocks a clean full-suite sign-off.
- The CLI fallback for `gstack-brain-context-load` cannot express `content_contains` with current gbrain CLI `list`; it keeps repo/type/tag filtering and should move richer predicates to MCP once the MCP path is wired.

## Roadmap Recommendation

- G0: Merge these fixes only after Opus/Sonnet review the changed gbrain runtime surfaces and explicitly accept the temporary `fast-uri` residual.
- G1: Re-run `bun audit` after 2026-05-12T08:31:31Z and add a controlled `fast-uri@3.1.2` override if the advisory remains unresolved upstream.
- G2: Keep gbrain rollout read-only first: index docs, reviews, handoffs, and session summaries without automatic writeback into repo state.
- G3: Enable supervised writeback only after secret scanning is reliably available, fail-closed behavior is accepted, and every write has source path, digest, session id, repo tag, and audit trail.
- G4: Add observability for agent behavior before ML optimization: per-run traces, trigger firings, selected context, gbrain query stats, skipped-source counts, and review outcomes.
- G5: Use Meta-Harness / ASI-Evolve-style optimization only after G0-G4 produce deterministic traces and scoring. Do not optimize Markdown prompts blindly before the evaluation harness can distinguish useful context from noise.
