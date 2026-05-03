---
id: gpt-5.5-handoff-00-20260503
title: Arbitrage Zack sur Q1-Q5, D1-D6 laissés ouverts pour discussion
date: 2026-05-03
status: accepted
agent: gpt-5.5
review_kind: handoff
target_agent: claude-opus
scope: architecture decisions, q1-q5 arbitration, phase-1 sequencing
synopsis: >
  Handoff à Claude Opus 4.7 après arbitrage explicite de Zack sur Q1-Q5.
  Les cinq questions ouvertes du P0 sont tranchées. Les décisions D1-D6 ne
  sont pas encore arbitrées et doivent faire l'objet d'une discussion dédiée
  avant démarrage de P1.
sources:
  - reviews/gpt-5.5/proposition/01-onboarding-acknowledgment-20260503.md
  - TODOS.md
  - ARCHITECTURE.md
---

# Contexte

Zack a validé les recommandations GPT-5.5 sur `Q1-Q5` le `2026-05-03` dans cette session.

Information supplémentaire côté owner :
- un repo distant a été créé
- aucune licence n'a été ajoutée pour l'instant

# Arbitrage Zack sur Q1-Q5

## Q1 — Nom final de la skill

Décision Zack : **`coding-best-practices`** pour la Phase 1.

Effet :
- conserver le nom courant dans la doc et l'arborescence
- éviter un churn de naming avant le premier livrable

## Q2 — Repo séparé ou monorepo

Décision Zack : **monorepo** dans `Dict_AI_Coding/` pour toute la Phase 1.

Effet :
- `findings/`, `ARCHITECTURE.md`, `TODOS.md`, `reviews/` et `skill/` restent co-localisés
- pas de split repo avant stabilisation du premier livrable

## Q3 — Licence

Décision Zack : **pas de licence pour l'instant**.

État réel :
- le repo distant a été créé sans licence, conformément à cette décision

Effet :
- le projet reste en posture privée / chantier méthodologique
- la décision de publication reste reportée après la Phase 1

## Q4 — `git init` autorisé ?

Décision Zack : **oui**.

Effet :
- l'initialisation git locale est autorisée
- le raccord au repo distant est maintenant possible
- la discipline branches / commits bisectables / PRs peut devenir réelle

Note :
- aucune action git n'a encore été exécutée dans cette session

## Q5 — Premier projet de démo E2E

Décision Zack : **fixture plantée ad hoc d'abord**, `Depollution_Sols` ensuite.

Effet :
- la première preuve E2E isole la qualité de la skill
- le test sur un repo réel vient dans un second temps

# Ce qui reste ouvert

## D1-D6

Décision Zack : **non arbitrés à ce stade**. Discussion requise avant le démarrage de `P1`.

Conséquence pratique :
- ne pas lancer le scaffolding Phase 1 comme si P0 était clos
- garder `status` des décisions architecturales à ouvert / en discussion

# Proposition de cadrage pour la discussion D1-D6

Priorité de discussion recommandée :

1. `D1` réutilisation gstack, car cela conditionne la plomberie et le coût de maintenance
2. `D5` catalogue en symlink vs copie générée, car cela conditionne la portabilité réelle
3. `D6` validation statique seule vs statique + smoke test dynamique, car cela conditionne le critère d'acceptation
4. `D2`, `D3`, `D4` ensuite, sauf objection reviewer

Position GPT-5.5 déjà déposée :
- `D1` : cherry-pick minimal, pas fork
- `D2` : 18 fichiers par famille
- `D3` : auto-fix mécanique seulement
- `D4` : portabilité d'artefact oui, parité comportementale non en Phase 1
- `D5` : copie générée dans `skill/catalog/`, pas symlink pur
- `D6` : validation statique pendant l'implémentation, smoke test dynamique obligatoire avant `accepted`

# Next step recommandé

1. Claude Opus 4.7 accuse réception de l'arbitrage Zack sur `Q1-Q5`
2. Claude Opus 4.7 prépare la synthèse courte des options sur `D1-D6`
3. Discussion Zack + Claude sur `D1-D6`
4. Une fois `D1-D6` arbitrés, publication du document d'architecture bloquante P0, puis seulement démarrage de `P1`
