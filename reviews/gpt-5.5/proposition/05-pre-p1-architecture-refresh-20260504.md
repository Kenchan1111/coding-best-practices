---
id: gpt-5.5-proposition-05-20260504
title: Refresh architecture pre-P1 et corrections de regression documentaire
date: 2026-05-04
status: proposed
agent: gpt-5.5
review_kind: proposition
target_agent: claude-opus
scope: CLAUDE.md, ARCHITECTURE.md, TODOS.md, findings/01_bug_catalog.md, onboardings
synopsis: >
  Review pre-P1 apres relecture des documents canoniques et des notes Opus/Sonnet.
  Les regressions bloqueuses etaient documentaires : D5/D6 encore obsoletes dans
  ARCHITECTURE.md/TODOS.md, compteur 78 non aligne avec le catalogue actuel,
  et chemins de livrables pointant vers Claude au lieu de GPT-5.5.
reviewed_revision: 2d9163f9dccca00b78f7d69c379714a72fa46962+dirty
validation:
  - "date -> 2026-05-04 17:23:14 CEST"
  - "git status --short -> dirty, plusieurs fichiers untracked + corrections docs courantes"
  - "git rev-parse HEAD -> 2d9163f9dccca00b78f7d69c379714a72fa46962"
  - "rg sous-patterns A1...R2 -> 70 entrees documentees"
  - "rg formulations obsoletes dans docs canoniques -> 0 match"
  - "python3 -m compileall scripts -> OK"
  - "python3 scripts/sync_reviews.py -> OK, 7 propositions, 0 variantes, 0 derives"
sources:
  - CLAUDE.md
  - ARCHITECTURE.md
  - TODOS.md
  - findings/01_bug_catalog.md
  - reviews/claude-opus/proposition/01-ack-q1-q5-and-synthesis-d1-d6-20260503.md
  - reviews/claude-sonnet/proposition/01-onboarding-and-d5-d6-review-20260504.md
---

# Findings

## confirmed_current - D5 obsolète dans ARCHITECTURE.md

Impact : risque de scaffold en symlink alors que D5 converge vers copie generee.

Correction appliquee :
- layout `skill/catalog/bug_catalog.md`
- D5 documente comme copie generee
- ajout de `scripts/sync-catalog.ts`

## confirmed_current - D6 obsolète dans ARCHITECTURE.md

Impact : contradiction avec le critere E2E deja present en Phase 1.

Correction appliquee :
- D6 documente comme validation statique + smoke test dynamique obligatoire
- critere E2E precise : trigger + diagnostic attendu + absence de faux positif atomicite

## confirmed_current - compteur 78 vs 70

Impact : promesse produit fausse dans `CLAUDE.md`, `ARCHITECTURE.md` et onboardings.

Evidence :
- denombrement courant A1...R2 + L1...L10 : 70 sous-patterns documentes

Correction appliquee :
- wording aligne sur "70 sous-patterns documentes"
- `findings/01_bug_catalog.md` note que 78 etait une estimation non reconciliee

## confirmed_current - chemins de livrables P1-P7 pointaient vers Claude

Impact : le workflow pouvait deposer les handoffs d'implementation au mauvais endroit.

Correction appliquee :
- livrables P1-P7 corriges vers `reviews/gpt-5.5/proposition/`

## confirmed_current - famille G nommee trop generiquement

Impact : confusion possible entre G filtrage shell et N validation d'input API.

Correction appliquee :
- `input_filtering.md` remplace par `shell_token_filtering.md`

# Residual risks

- `P1` n'a pas encore de code. Le repo est pret pour scaffolding, pas pour sign-off Phase 1.
- Kimi n'a pas encore depose sa review systemique. Non-bloquant pour P1 selon arbitrage Zack, mais utile avant P2/P5.
- Les fichiers recents de sync/review restent non suivis dans git au moment de cette note.

# Verdict

Ready pour demarrer `P1` scaffolding.
