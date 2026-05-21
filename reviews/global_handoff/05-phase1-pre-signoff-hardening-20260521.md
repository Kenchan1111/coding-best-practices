---
id: gpt-5.5-handoff-05-20260521
title: Durcissement pre-signoff Phase 1 sur coding-best-practices
date: '2026-05-21'
status: ready-for-review
agent: gpt-5.5
target_agent: claude-opus, claude-sonnet, kimi, zack
review_kind: handoff
reviewed_revision: 8267365d040afca499f04500f6feecb5767783ea+dirty
scope: scripts/skill-lib.ts, scripts/sync-catalog.ts, scripts/validate.ts, skill/tests,
  skill/README.md, ARCHITECTURE.md, TODOS.md
synopsis: 'Durcissement pre-signoff limite a Phase 1 : suppression du hardcoding du
  catalogue, parseur frontmatter YAML partage pour tests/E2E mock, tests de derive
  supplementaires, et rappel documentaire explicite sur la limite du mock P7.'
sync_managed_copy: true
sync_source_path: reviews/gpt-5.5/handoff/05-phase1-pre-signoff-hardening-20260521.md
sync_source_digest: d621181442e9
sync_source_body_digest: 8d2f857b7e71
sync_source_metadata_digest: c90f1e6332ec
---

# Handoff P8-ready apres durcissement pre-signoff

## Objet de cette passe

Cette passe n'ouvre pas Phase 2 et ne change pas le comportement fonctionnel de
la skill. Elle ferme les deux reliquats techniques encore credibles avant
`phase1-accepted` :

1. hardcoding du compte catalogue dans `scripts/validate.ts` / `scripts/sync-catalog.ts`
2. divergence de parsing frontmatter entre `skill/tests/test_helpers.py` et `skill/tests/e2e/mock_agent.py`

Le statut gouvernance reste inchangé : **P1-P7 livres, P8 reviews/sign-offs en
attente**.

## Corrections implementees

### 1. Catalogue derive de la source canonique

Fichiers :

- `scripts/skill-lib.ts`
- `scripts/sync-catalog.ts`
- `scripts/validate.ts`
- `skill/tests/test_sync_catalog.py`
- `skill/tests/test_validate.py`

Changements :

- `extractCatalogIds()` est centralise dans `scripts/skill-lib.ts`
- `sync-catalog.ts` et `validate.ts` reutilisent la meme extraction
- `validate.ts` compare maintenant `pattern_count` **et** `catalog_ids` a
  `findings/01_bug_catalog.md`
- le check ne repose plus sur un `70` duplique
- nouveaux tests pour verrouiller :
  - sync OK contre la source canonique
  - rejet d'une derive d'IDs sans `--accept-id-change`
  - rejet d'un `pattern_count` ou de `catalog_ids` incoherents

Effet :

- plus de faux vert possible si le nombre reste bon mais que la liste d'IDs
  derive
- une seule source de verite fonctionnelle : `findings/01_bug_catalog.md`

### 2. Parser frontmatter YAML partage

Fichiers :

- `skill/tests/frontmatter_utils.py`
- `skill/tests/test_helpers.py`
- `skill/tests/e2e/mock_agent.py`
- `skill/tests/test_frontmatter_utils.py`

Changements :

- ajout d'un helper YAML partage pour parser le frontmatter Markdown
- `test_helpers.py` et `mock_agent.py` consomment le meme helper
- normalisation compatibilite conservee pour les listes de signaux type
  `code_pattern: ...`
- nouveau test pour :
  - frontmatter valide avec listes YAML
  - frontmatter non-mapping rejete explicitement

Effet :

- fin de la divergence de parsing entre tests unitaires et harness E2E
- contrat plus proche du parseur YAML deja utilise ailleurs dans le repo

### 3. Documentation de boundary P7/P8 maintenue explicite

Fichiers :

- `skill/README.md`
- `ARCHITECTURE.md`
- `TODOS.md`

Changements :

- ajout d'une note explicite : le mock P7 prouve le chargement de l'artefact et
  le mapping checks/triggers, pas la compliance live d'un host reel
- ajout d'une entree `Done` 2026-05-21 pour ce durcissement pre-signoff
- aucun changement de scope Phase 1 / Phase 2

## Validation executee

Post-change sur l'etat courant :

- `python3 -m unittest discover -s skill/tests -p 'test_*.py'` : **36 tests OK**
- `node scripts/validate.ts` : **OK**
- `node scripts/gen-skill-docs.ts --dry-run` : **Catalog sync OK - 70 IDs, 18 families** puis **FRESH**
- `python3 scripts/sync_reviews.py --once` : **OK, 0 variantes, 0 derives**
- `bash skill/tests/e2e/run.sh` : **E2E_OK**
- `git diff --check` : **OK**

## Ce qui reste ouvert

- sign-off Opus 4.7
- sign-off Sonnet
- review Kimi optionnelle mais utile comme troisieme famille de modele
- arbitrage final Zack
- tag `phase1-accepted`

## Demande aux reviewers

Merci de reviewer **l'etat courant du code**, pas uniquement les notes anciennes,
en ciblant :

- est-ce que la suppression du hardcoding catalogue est suffisante pour P8
- est-ce que le parser YAML partage ne casse aucun contrat implicite des
  triggers/checks
- est-ce que le boundary P7 mock est maintenant documente de facon assez nette
  pour eviter un tag trompeur

## Verdict GPT-5.5

Le repo est maintenant dans un meilleur etat pour la revue P8 que lors des
notes du 2026-05-07 / 2026-05-12 : les deux reliquats techniques encore
plausibles avant `phase1-accepted` sont fermes, sans elargir le scope.
