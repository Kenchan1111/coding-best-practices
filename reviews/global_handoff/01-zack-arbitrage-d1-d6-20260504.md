---
id: global-handoff-01-20260504
title: Arbitrage Zack D1-D6 et autorisation de demarrage P1
date: 2026-05-04
status: accepted
agent: gpt-5.5
review_kind: handoff
target_agent: claude-opus
scope: D1-D6, P0 closure, P1 start
synopsis: >
  Handoff durable actant l'arbitrage D1-D6 et l'autorisation de demarrer P1.
  Il integre la convergence Opus 4.7 + GPT-5.5 + Sonnet, puis les corrections
  documentaires appliquees avant le scaffolding.
sources:
  - reviews/gpt-5.5/proposition/01-onboarding-acknowledgment-20260503.md
  - reviews/claude-opus/proposition/01-ack-q1-q5-and-synthesis-d1-d6-20260503.md
  - reviews/claude-sonnet/proposition/01-onboarding-and-d5-d6-review-20260504.md
  - ARCHITECTURE.md
  - TODOS.md
---

# Decision

Zack autorise le lancement du developpement de la skill `coding-best-practices` le 2026-05-04.

Cette autorisation clot P0 pour D1-D6.

# D1-D6 arbitrages

| Decision | Arbitrage |
|---|---|
| D1 | Cherry-pick minimal de gstack : `gen-skill-docs.ts`, `hosts/`, `slop-scan.config.json`. Pas de fork complet. |
| D2 | 18 fichiers checks par famille, sous-patterns en sections internes. |
| D3 | Auto-fix seulement pour les mecaniques sans risque. ASK pour les cas ambigus ou user-visible. |
| D4 | Portabilite d'artefact en Phase 1. Parite comportementale multi-host en Phase 2. |
| D5 | Catalogue en copie generee dans `skill/catalog/`, source canonique `findings/01_bug_catalog.md`. |
| D6 | Validation statique pendant l'implementation + smoke test dynamique obligatoire avant `accepted`. |

# Corrections documentaires appliquees avant P1

- `ARCHITECTURE.md` : statut passe a `accepted-for-P1`
- `ARCHITECTURE.md` : D5 mis a jour vers copie generee
- `ARCHITECTURE.md` : D6 mis a jour vers statique + smoke test dynamique
- `ARCHITECTURE.md` et onboarding : compteur aligne sur 70 sous-patterns documentes
- `TODOS.md` : P0 coche, livrables GPT-5.5 corriges, chemins `skill/tests/` corriges
- Famille G renommee `shell_token_filtering` pour eviter la confusion avec N `input_validation`

# Conditions de demarrage P1

GPT-5.5 peut demarrer `P1` scaffolding.

Contraintes a respecter :
- pas de code DB, RL, knowledge graph ou cross-project memory en Phase 1
- livrable P1 dans `reviews/gpt-5.5/proposition/06-scaffolding-YYYYMMDD.md`
- validation minimale : `python3 -m compileall scripts` + `python3 scripts/sync_reviews.py`
- si du code skill est ajoute : tests locaux pertinents dans `skill/tests/`
