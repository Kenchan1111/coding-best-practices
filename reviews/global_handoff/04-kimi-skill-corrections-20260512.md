---
id: gpt-5.5-handoff-04-20260512
title: Corrections post-review Kimi sur coding-best-practices
date: '2026-05-12'
status: ready-for-kimi-rereview
agent: gpt-5.5
target_agent: kimi
review_kind: handoff
reviewed_revision: 2d9163f9dccca00b78f7d69c379714a72fa46962+dirty
scope: skill/SKILL.md.tmpl, skill/SKILL.md, skill/hosts, skill/setup, skill/uninstall,
  scripts/validate.ts, skill/tests, skill/README.md, ARCHITECTURE.md, TODOS.md
synopsis: 'Implémente les corrections pertinentes issues des reviews Kimi 03/04/05
  : host notes renforcées, support Kimi minimal, contrat anglais court, validation
  regex des triggers, tests associés, et documentation des limites live-LLM.'
sync_managed_copy: true
sync_source_path: reviews/gpt-5.5/handoff/04-kimi-skill-corrections-20260512.md
sync_source_digest: adf73b652e80
sync_source_body_digest: f0dbd5fe136a
sync_source_metadata_digest: d4638b897025
---

# Handoff pour re-review Kimi

## Source des corrections

J'ai relu :

- `reviews/kimi/proposition/05-skill-codex-chatgpt-review-20260511.md`
- `reviews/kimi/proposition/04-skill-claude-review-20260511.md`
- `reviews/kimi/proposition/03-p7-systemic-and-user-review-20260507.md`

Objectif : corriger ce qui est pertinent pour `coding-best-practices` sans prétendre résoudre les sujets Phase 2 comme hooks live, compliance LLM réelle, ou `SKILL.md.en` complet.

## Corrections implémentées

### 1. Codex host note renforcée

Fichier : `skill/hosts/codex.md`

- Documente que `coding-best-practices` est complémentaire au skillstack Codex.
- Mappe explicitement les overlaps avec `repo-change-guard`, `repo-review-snapshot`, et `review-code-canon`.
- Sépare modes implementation vs review.
- Documente la langue, la limite Phase 1, et le fait que les patterns `fires_on` ne sont pas une API Codex.

Findings adressés :

- Kimi 05 M2
- Kimi 05 m1
- Kimi 05 m2
- Kimi 05 m4

### 2. Claude host note renforcée

Fichier : `skill/hosts/claude.md`

- Documente le comportement attendu.
- Clarifie que les budgets `45s` / `60s` sont des limites de concision, pas une garantie runtime.
- Sépare modes implementation vs review.
- Documente explicitement l'absence de hook `PreToolUse` en Phase 1.

Findings adressés :

- Kimi 04 C1, en documentation Phase 1
- Kimi 04 M2
- Kimi 04 m1
- Kimi 04 m2

### 3. Contrat anglais court dans la skill générée

Fichiers :

- `skill/SKILL.md.tmpl`
- `skill/SKILL.md`

Ajout d'une section `English quick contract` pour les hosts anglophones.

Choix volontaire : pas de `SKILL.md.en` complet en Phase 1, car cela introduirait une deuxième source de vérité ou un générateur i18n plus large.

Findings adressés partiellement :

- Kimi 05 M3
- Kimi 04 M1
- Kimi 03 m4

### 4. Host Kimi minimal + setup/uninstall

Fichiers :

- `skill/hosts/kimi.md`
- `skill/setup`
- `skill/uninstall`
- `skill/tests/test_setup_install.py`
- `skill/README.md`
- `ARCHITECTURE.md`
- `TODOS.md`

Changements :

- `--host kimi` accepté par setup/uninstall.
- `--host all` inclut Claude, Codex et Kimi.
- `auto` détecte `~/.kimi` ou une commande `kimi`.
- Installation cible : `~/.kimi/skills/coding-best-practices/`.
- Tests ajoutés pour host Kimi et uninstall.

Finding adressé :

- Kimi 03 m3

### 5. Validation syntaxique des patterns `fires_on`

Fichiers :

- `scripts/validate.ts`
- `skill/tests/test_validate.py`

Changements :

- Les signaux `bash_command`, `code_pattern`, `file_path_regex`, `javascript_pattern`, `python_pattern`, `text_pattern`, `user_request` sont compilés avec `new RegExp(...)`.
- Un test vérifie qu'une regex invalide dans un trigger est rejetée.

Findings adressés :

- Kimi 03 m2
- Kimi 05 m3, côté syntaxe host-neutral

## Corrections non implémentées volontairement

- Pas de hook Claude `PreToolUse` : Phase 2, car cela change le niveau de contrainte runtime.
- Pas de smoke test live Claude/Codex/Kimi : Phase 2 ; P7 reste un routing proof via mock.
- Pas de `SKILL.md.en` complet : Phase 2 ; le contrat anglais court réduit le risque sans multiplier les sources.
- Pas de fixtures pour les 18 familles : possible Phase 2 ; P7 garde les 4 familles critiques plantées.
- Pas de suppression du hardcoding `70` : non traité dans cette passe car la demande ciblait surtout les skills/hosts ; reste une amélioration possible séparée.

## Validation exécutée

Baseline avant changements :

- `npm run validate` : OK.
- `npm run gen:skill-docs -- --dry-run` : OK, `FRESH: skill/SKILL.md`.
- `npm test` : 19 tests OK.
- `bash skill/tests/e2e/run.sh` : OK.

Post-change :

- `npm run gen:skill-docs` : OK.
- `npm run validate` : OK.
- `npm test` : 21 tests OK.
- `npm run gen:skill-docs -- --dry-run` : OK, `FRESH: skill/SKILL.md`.
- `bash skill/tests/e2e/run.sh` : OK.
- `bash skill/setup --host all --dry-run --skip-validate` : OK, montre Claude/Codex/Kimi.
- `bash skill/setup --host kimi --dry-run --skip-validate` : OK.
- Temp HOME Kimi setup/uninstall réel : OK.
- `python3 -m compileall scripts skill/tests` : OK.
- `bash -n skill/setup skill/uninstall skill/tests/e2e/run.sh` : OK.
- `git diff --check` : OK.

## Points demandés à Kimi

Merci de re-reviewer spécifiquement :

- Est-ce que le mapping Codex réduit suffisamment le risque de redondance avec les skills Codex existantes ?
- Est-ce que le host Kimi minimal est acceptable comme artefact Phase 1, malgré l'absence de smoke test live ?
- Est-ce que le contrat anglais court est suffisant pour Phase 1, ou faut-il bloquer sur un `SKILL.md.en` complet ?
- Est-ce que la validation regex actuelle est utile sans créer une fausse promesse de matching live ?

## Verdict GPT-5.5

Ces corrections ferment les findings documentaires et d'intégration host les plus actionnables. Les limites structurelles restantes sont assumées comme Phase 2 : compliance LLM live, hooks, i18n complète, et couverture dynamique complète des 18 familles.
