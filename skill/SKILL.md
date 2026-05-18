---
name: coding-best-practices
version: 0.1.0
description: |
  Extension gstack-compatible qui surface les patterns d'erreurs LLM documentes
  dans ce repo quand le contexte les rend pertinents : ecriture de fichiers
  d'etat, tests, boucles de scan, operations destructrices, et claims de review
  avec file:line.
allowed-tools:
  - Read
  - Grep
  - Bash
triggers:
  - writing code
  - writing tests
  - reviewing code
---
<!-- AUTO-GENERATED from SKILL.md.tmpl - do not edit directly -->
<!-- Regenerate: node scripts/gen-skill-docs.ts -->

# coding-best-practices

Cette skill augmente gstack en aidant un agent de coding a charger les checks pertinents au bon moment.
Elle ne remplace pas les tests, la review humaine, ni la convergence inter-LLM.

## English quick contract

Use this skill as a contextual guardrail, not as an autonomous enforcement hook.
Before editing code, tests, scan loops, persistent state, destructive operations, or publishing a review claim, identify the matching trigger, load only the referenced checks, and state the requested preflight decision.
The time budgets in triggers are cognitive budgets, not enforceable timers.

## Perimetre Phase 1

- Catalogue statique issu de `findings/01_bug_catalog.md`
- 18 familles de checks
- Triggers contextuels
- Validation statique
- Smoke test dynamique avant acceptation
- Compatibilite avec la plomberie gstack existante

## Hors perimetre Phase 1

- Base de donnees persistante
- Moteur ML ou RL
- Knowledge graph
- Memoire cross-projet
- Plugin IDE

## Runtime workflow

1. Avant un edit ou une review, identifier si un trigger ci-dessous s'applique.
2. Si oui, lire le fichier `triggers/<trigger>.md`.
3. Lire ensuite les fichiers `checks/<check>.md` listes dans `calls_checks`.
4. Produire la phrase de preflight demandee par le trigger avant de coder ou publier le finding.
5. Appliquer Fix-First : AUTO-FIX seulement pour les corrections mecaniques et reversibles ; ASK pour securite, donnees, domaine, user-visible ou >20 lignes.

Ne pas charger les 18 checks d'un coup. Charger seulement ceux appeles par le trigger actif.
Les budgets `45s` / `60s` sont des limites d'attention indicatives ; ils ne prouvent pas qu'un host LLM respecte un timer.

## Catalogue

- Source portable : `catalog/bug_catalog.md`
- Source canonique : `findings/01_bug_catalog.md`
- Digest source : `b3724cf239f0`
- Couverture : 70 IDs documentes, familles A, B, C, D, E, F, G, H, I, J, K, L, M, N, O, P, Q, R
- Lire le catalogue seulement quand un check demande la preuve source ou le detail historique.

## Triggers

### on_destructive_op

- Fichier : `triggers/on_destructive_op.md`
- Phase : `before_destructive_edit_or_command`
- Intent : Avoid irreversible data loss and preserve auditability.
- Checks : `I_irreversible_ops`, `H_silent_override`, `R_audit_trail`, `A_atomic_write`, `M_drift_detection`, `G_shell_token_filtering`, `L_bash_specific`, `F_race_conditions`
- Signaux principaux :
  - bash_command: 'rm -r|rm -rf|git reset --hard|git checkout \.|git restore \.|mv |truncate|DROP TABLE|DROP DATABASE'
  - python_pattern: 'shutil\.move|unlink\(|rmtree\(|remove\(|replace\('
  - code_pattern: 'overwrite|delete|promote|archive|truncate|drop|reset'

# Trigger - Destructive Operation

## Activation rule

If the next edit or command deletes, moves, overwrites, truncates, promotes, resets, or replaces data that might be source, user input, review evidence, state, or proof, run this trigger before acting.

This trigger complements gstack `/careful` and `/guard`. It applies to code changes too, not only shell commands.

## 45-second preflight

1. Load `I_irreversible_ops` and identify the source of truth that could be lost.
2. Load `H_silent_override` if an explicit user ID, mode, catalog, or action can be replaced by automatic behavior.
3. Load `R_audit_trail` if original parameters or timestamps are dropped during the operation.
4. Load `A_atomic_write` if the operation replaces a state or proof file.
5. Load `M_drift_detection` if the operation changes a catalog, latest snapshot, or baseline.
6. Load `G_shell_token_filtering` if the operation is shell-mediated or sandboxed.
7. Load `L_bash_specific` if the operation is inside a Bash script or pipeline.
8. Load `F_race_conditions` if concurrent writers, locks, or child processes are involved.

## Required LLM behavior

Before acting, write:

```text
Destructive preflight: target=<path/id>; reversible=<yes|no>; backup_or_copy=<yes|no>; checks=<I,H,R,A,M,G,L,F subset>; approval=<not_needed|needed|already_explicit>.
```

If `reversible=no` and approval is not explicit for the exact target, ask the user.

## Do not trigger

- Cleanup of generated build artifacts such as `node_modules`, `dist`, `build`, `.pytest_cache`, `__pycache__`, or coverage output.
- Deletion of files created by the same failed command when the target is exact, untracked, and non-source.

### on_review_claim

- Fichier : `triggers/on_review_claim.md`
- Phase : `before_publishing_review`
- Intent : Prevent file:line hallucinations, stale fixes, and unreproduced review claims.
- Checks : `E_llm_hallucination`, `J_bidir_test_coverage`, `P_contract_consistency`, `D_iteration_semantics`, `K_architecture_smells`
- Signaux principaux :
  - user_request: 'review|audit|check my diff|finding|sign-off|handoff|correction'
  - text_pattern: '[A-Za-z0-9_./-]+:\d+'
  - text_pattern: 'already fixed|reproduce|does not exist|bug at|line'

# Trigger - Review Claim

## Activation rule

If the next response publishes a review finding, correction, handoff, or sign-off with a `file:line`, code behavior claim, reproduction example, or proposed refix, run this trigger before writing the claim.

This trigger must fire even if the reviewer is confident. Confidence from memory is not evidence.

## 60-second preflight

1. Load `E_llm_hallucination` for every cited `file:line`.
2. Read the cited file around the cited line in the current session.
3. Search whether the proposed fix already exists before recommending it.
4. If the claim is about test adequacy, load `J_bidir_test_coverage`.
5. If the claim is about public values, status, schema, or config precedence, load `P_contract_consistency`.
6. If the claim is about latest/first/sort/slice/iteration, load `D_iteration_semantics`.
7. If the claim is about architecture, layering, side effects, public contracts, or refactoring, load `K_architecture_smells`.

## Required LLM behavior

Each finding must include an evidence state:

```text
Evidence: read=<file:line or range>; reproduced=<command|not_run>; stale_fix_search=<done|not_applicable>.
```

If the file was not read in the current session, do not cite a line number. Downgrade to an open question.

## Do not trigger

- High-level planning notes without file claims.
- User-visible summaries that do not assert code behavior or line evidence.

### on_write_scan_loop

- Fichier : `triggers/on_write_scan_loop.md`
- Phase : `before_loop_edit`
- Intent : Keep batch scans complete, deterministic, and inspectable when one item is malformed.
- Checks : `C_scan_loop_safe`, `D_iteration_semantics`, `B_cascade_failure`, `M_drift_detection`, `A_atomic_write`, `O_intrusive_nonportable`
- Signaux principaux :
  - code_pattern: 'for .* in .*glob|for .* in sorted\(|walk\(|iterdir\(|read_text\(\)'
  - code_pattern: 'yaml\.safe_load|frontmatter|parse.*markdown|load_review_documents|scan_'
  - file_path_regex: '(scan|sync|archive|catalog|index|loader|collector).*'

# Trigger - Write Scan Loop

## Activation rule

If the next edit scans files, parses many documents, loads frontmatter, indexes a directory, or aggregates records from a batch, run this trigger before writing the loop.

This is a coding-time trigger. It is too late after the loop shape is already committed.

## 45-second preflight

1. Load `C_scan_loop_safe` and decide whether one bad item should skip, warn, or hard-fail.
2. Load `D_iteration_semantics` if the loop selects latest, first, sorted, sliced, or first-match results.
3. Load `B_cascade_failure` if scan errors affect process exit status or downstream pipeline success.
4. Load `M_drift_detection` if the scan produces a latest snapshot or catalog.
5. Load `A_atomic_write` if the scan writes generated state after reading.
6. Load `O_intrusive_nonportable` if the scanner depends on cwd, terminal behavior, or import path hacks.

## Required LLM behavior

Before applying the edit, state the failure mode:

```text
Scan-loop preflight: bad_item_policy=<skip+report|hard_fail|not_applicable>; ordering=<deterministic|needs_tie_breaker>; checks=<C,D,B,M,A,O subset>.
```

If the policy is `skip+report`, the output must include the skipped path and error count.

## Do not trigger

- Loops over fixed in-memory lists with no parsing or IO.
- Parsers where fail-fast is an explicit contract and caller handles the failure.

### on_write_state_file

- Fichier : `triggers/on_write_state_file.md`
- Phase : `before_edit_or_bash`
- Intent : Prevent corrupt, stale, or misleading persisted state.
- Checks : `A_atomic_write`, `B_cascade_failure`, `M_drift_detection`, `R_audit_trail`, `F_race_conditions`
- Signaux principaux :
  - file_path_regex: '(latest|index|catalog|manifest|state|baseline|timeline|digest|anchor).*\.(json|ya?ml|ndjson|db|sqlite)$'
  - python_pattern: '\.write_text\(.*json|json\.dump|open\(.+, ["'']w'
  - javascript_pattern: 'writeFileSync|writeFile\(.*JSON\.stringify'
  - bash_command: 'jq .* >|cat .* >|echo .* >'

# Trigger - Write State File

## Activation rule

If the next edit or command writes trusted state, proof, index, catalog, manifest, baseline, digest, or run pointer, stop before editing and run this preflight.

Do not wait for review time. This trigger is useful only before the write path is implemented.

## 45-second preflight

1. Classify the target: `state`, `proof`, `cache`, `fixture`, or `log`.
2. If `state` or `proof`, load `A_atomic_write` and require temp-file plus replace semantics.
3. Load `B_cascade_failure` if a later command or user will treat this write as success.
4. Load `M_drift_detection` if this write overwrites a latest snapshot or generated catalog.
5. Load `R_audit_trail` if values are dropped, normalized, promoted, or transformed before writing.
6. Load `F_race_conditions` if more than one process, worker, or command can write the same target.

## Required LLM behavior

Before applying the edit, write a one-line internal decision in the working note or review output:

```text
State-write preflight: target=<state|proof|cache|fixture|log>; checks=<A,B,M,R,F subset>; decision=<atomic|append-only|safe-cache|ask>.
```

If the decision is `ask`, ask the user before changing persistence semantics.

## Do not trigger

- Append-only logs where partial last lines are acceptable.
- Test fixtures under `tests/fixtures/`.
- Caches that are explicitly documented as fully regenerable and never authoritative.

### on_write_test

- Fichier : `triggers/on_write_test.md`
- Phase : `before_test_edit`
- Intent : Make tests prove the invariant instead of only covering the happy path.
- Checks : `J_bidir_test_coverage`, `D_iteration_semantics`, `N_input_validation`, `Q_numerical_precision`, `P_contract_consistency`
- Signaux principaux :
  - file_path_regex: '(tests?|spec|__tests__)/|test_.*\.py$|.*\.(test|spec)\.(js|ts|tsx)$'
  - code_pattern: 'assert|expect|pytest|unittest|describe\(|it\('
  - user_request: 'add test|write test|fix tests|coverage|regression'

# Trigger - Write Test

## Activation rule

If the next edit creates or changes tests, run this trigger before writing assertions.

The goal is to prevent tests that pass accidentally, mock the thing they claim to test, or cover only one branch of a bidirectional behavior.

## 60-second preflight

1. Load `J_bidir_test_coverage` for every behavior with sides, directions, inverses, thresholds, or modes.
2. Load `D_iteration_semantics` when testing `latest`, sorting, slices, tie-breakers, or first-rule-wins behavior.
3. Load `N_input_validation` when tests exercise invalid IDs, raw user input, coercion, or client metadata.
4. Load `Q_numerical_precision` for statistics, quantiles, digest length, nondetects, or sparse-data labels.
5. Load `P_contract_consistency` when tests protect public schemas, enum/status values, action lists, or config precedence.

## Required LLM behavior

Before applying the test edit, name the failing invariant:

```text
Test preflight: invariant=<specific behavior>; should_fail_before_fix=<yes|no|unknown>; checks=<J,D,N,Q,P subset>.
```

If `should_fail_before_fix=unknown`, do not present the test as regression proof.

## Do not trigger

- Pure snapshot refreshes where no assertion logic changes.
- Formatting-only changes in existing test files.

## Checks

### A_atomic_write

- Fichier : `checks/A_atomic_write.md`
- Famille : `A`
- Nom : `atomic_write`
- Severite : `critical`
- Integration gstack : `review_critical_pass`
- Quand lire : Use this check before writing trusted state: `latest.json`, `index.json`, `catalog.json`, manifests, run pointers, audit indexes, timelines, or any file read by a later step as authoritative state.
- Fix-First : AUTO-FIX only when adding or reusing a small existing helper for a new write path.

### B_cascade_failure

- Fichier : `checks/B_cascade_failure.md`
- Famille : `B`
- Nom : `cascade_failure`
- Severite : `critical`
- Integration gstack : `review_critical_pass`
- Quand lire : Use this check for CLI entrypoints, batch jobs, sync scripts, pipelines, and save/export flows where one failed step can make downstream evidence stale or misleading.
- Fix-First : ASK for critical orchestration behavior, because changing failure propagation can alter user-visible workflows.

### C_scan_loop_safe

- Fichier : `checks/C_scan_loop_safe.md`
- Famille : `C`
- Nom : `scan_loop_safe`
- Severite : `high`
- Integration gstack : `review_batch_resilience`
- Quand lire : Use this check when code scans many files, parses many documents, indexes archives, loads frontmatter, or processes a batch where one corrupt item should not prevent all later items from being seen.
- Fix-First : AUTO-FIX simple exclusions like `README.md` and per-item error collection when the caller already supports warnings.

### D_iteration_semantics

- Fichier : `checks/D_iteration_semantics.md`
- Famille : `D`
- Nom : `iteration_semantics`
- Severite : `critical`
- Integration gstack : `review_critical_pass`
- Quand lire : Use this check when code selects `latest`, `first`, `best`, `last`, classifies by ordered rules, parses structured text by slices, or aggregates records after sorting.
- Fix-First : ASK by default. Iteration fixes can change business verdicts, regulatory outputs, or user-visible classifications.

### E_llm_hallucination

- Fichier : `checks/E_llm_hallucination.md`
- Famille : `E`
- Nom : `llm_hallucination`
- Severite : `critical`
- Integration gstack : `review_claim_gate`
- Quand lire : Use this check before publishing any review finding, handoff, correction note, or architectural claim that cites a file, line number, code behavior, reproduction example, or already-existing fix.
- Fix-First : AUTO-FIX stale citations and remove false claims immediately.

### F_race_conditions

- Fichier : `checks/F_race_conditions.md`
- Famille : `F`
- Nom : `race_conditions`
- Severite : `high`
- Integration gstack : `review_race_conditions`
- Quand lire : Use this check when code creates IDs, writes shared files, holds locks, stores mutable process state, or runs under multiple workers, processes, shells, or async tasks.
- Fix-First : ASK by default. Race-condition fixes often change persistence, process model, or API semantics.

### G_shell_token_filtering

- Fichier : `checks/G_shell_token_filtering.md`
- Famille : `G`
- Nom : `shell_token_filtering`
- Severite : `high`
- Integration gstack : `review_shell_injection_and_guard`
- Quand lire : Use this check when code filters shell commands, extracts shell payloads, classifies text by substring, selects a sandbox, or relies on allowlists before executing user or LLM-controlled input.
- Fix-First : ASK for security policy, sandbox fallback, and command execution changes.

### H_silent_override

- Fichier : `checks/H_silent_override.md`
- Famille : `H`
- Nom : `silent_override`
- Severite : `high`
- Integration gstack : `review_llm_trust_boundary`
- Quand lire : Use this check when code receives explicit user input, regulatory parameters, selected modes, IDs, limits, or spec-listed actions, then changes or drops them automatically.
- Fix-First : ASK by default. User intent, compliance mode, and spec behavior are user-visible.

### I_irreversible_ops

- Fichier : `checks/I_irreversible_ops.md`
- Famille : `I`
- Nom : `irreversible_ops`
- Severite : `high`
- Integration gstack : `careful_guard_destructive_ops`
- Quand lire : Use this check before moving, deleting, overwriting, promoting, truncating, or replacing user-visible data, review notes, datasets, or proof artifacts.
- Fix-First : ASK by default. Irreversible operations require owner intent.

### J_bidir_test_coverage

- Fichier : `checks/J_bidir_test_coverage.md`
- Famille : `J`
- Nom : `bidir_test_coverage`
- Severite : `critical`
- Integration gstack : `review_testing_specialist`
- Quand lire : Use this check when adding or reviewing tests for functions with directions, sides, thresholds, parsers, classifiers, converters, or any behavior that has symmetric branches.
- Fix-First : AUTO-FIX missing local tests for mechanical branches when the expected behavior is already explicit.

### K_architecture_smells

- Fichier : `checks/K_architecture_smells.md`
- Famille : `K`
- Nom : `architecture_smells`
- Severite : `high`
- Integration gstack : `review_maintainability_specialist`
- Quand lire : Use this check when LLM-generated code grows large, duplicates blocks, mixes planning and execution, hides IO in pure-looking functions, or exposes untyped public API contracts.
- Fix-First : ASK for refactors, public API schemas, planner/executor separation, and proof algorithms.

### L_bash_specific

- Fichier : `checks/L_bash_specific.md`
- Famille : `L`
- Nom : `bash_specific`
- Severite : `high`
- Integration gstack : `review_bash_specific`
- Quand lire : Use this check when writing or reviewing Bash scripts, especially scripts with `set -euo pipefail`, pipelines, `sudo`, desktop notifications, network inspection, associative arrays, or `flock`.
- Fix-First : AUTO-FIX most local Bash mechanics when behavior is clear.

### M_drift_detection

- Fichier : `checks/M_drift_detection.md`
- Famille : `M`
- Nom : `drift_detection`
- Severite : `medium`
- Integration gstack : `canary_and_health`
- Quand lire : Use this check when code writes latest snapshots, catalogs, summaries, baselines, service state, or reusable caches that can drift from source files or backing rows.
- Fix-First : AUTO-FIX adding digests, changelog entries, and disappeared-record reporting when no behavior changes.

### N_input_validation

- Fichier : `checks/N_input_validation.md`
- Famille : `N`
- Nom : `input_validation`
- Severite : `medium`
- Integration gstack : `review_type_coercion_and_trust_boundary`
- Quand lire : Use this check for CLI prompts, API request parameters, imported metadata, file IDs, dates, numeric thresholds, user-selected roles, and any value crossing from user/client/LLM into trusted state.
- Fix-First : AUTO-FIX small boundary validations where the expected error behavior already exists.

### O_intrusive_nonportable

- Fichier : `checks/O_intrusive_nonportable.md`
- Famille : `O`
- Nom : `intrusive_nonportable`
- Severite : `medium`
- Integration gstack : `devex_and_distribution`
- Quand lire : Use this check when code clears terminals, mutates import paths, assumes a current working directory, emits terminal control sequences, or depends on local shell/terminal behavior.
- Fix-First : AUTO-FIX local non-portable terminal behavior when the intended output is clear.

### P_contract_consistency

- Fichier : `checks/P_contract_consistency.md`
- Famille : `P`
- Nom : `contract_consistency`
- Severite : `medium`
- Integration gstack : `api_contract_specialist`
- Quand lire : Use this check when the same status, action, schema, metadata, term list, or config convention appears in multiple files or is exposed to clients.
- Fix-First : AUTO-FIX duplicate-list guards and tests when behavior is obvious.

### Q_numerical_precision

- Fichier : `checks/Q_numerical_precision.md`
- Famille : `Q`
- Nom : `numerical_precision`
- Severite : `medium`
- Integration gstack : `review_domain_numerics`
- Quand lire : Use this check when code implements statistical methods, approximations, quantiles, digest lengths, sparse-data screening, nondetect handling, or defensibility labels.
- Fix-First : ASK by default. Numerical conventions and defensibility thresholds are domain decisions.

### R_audit_trail

- Fichier : `checks/R_audit_trail.md`
- Famille : `R`
- Nom : `audit_trail`
- Severite : `medium`
- Integration gstack : `review_auditability`
- Quand lire : Use this check when code transforms user inputs, drops parameters, normalizes records, falls back timestamps, builds evidence, or emits event sequences.
- Fix-First : AUTO-FIX preserving discarded values in metadata when it does not change behavior.
