---
id: gpt-5.5-proposition-07-20260504
title: P2 premier lot de checks et cadrage gstack-compatible
date: 2026-05-04
status: proposed
agent: gpt-5.5
review_kind: proposition
target_agent: claude-opus
scope: skill/checks/A-B-D-E-J, skill/hosts/gstack.md, docs P1/P2
synopsis: >
  Premier lot P2 : cinq familles critiques materialisees en checks Markdown,
  avec correction de cadrage pour expliciter que la skill augmente gstack au
  lieu de creer une plomberie concurrente.
validation:
  - "frontmatter checks A/B/D/E/J parse OK"
  - "python3 -m compileall scripts -> OK"
  - "python3 scripts/sync_reviews.py twice -> 0 variantes, 0 derives on second run"
---

# Contenu livre

- `skill/checks/A_atomic_write.md`
- `skill/checks/B_cascade_failure.md`
- `skill/checks/D_iteration_semantics.md`
- `skill/checks/E_llm_hallucination.md`
- `skill/checks/J_bidir_test_coverage.md`
- `skill/hosts/gstack.md`

# Correction de cadrage

Le rappel de Zack est integre : la cible n'est pas une skill isolee qui remplace gstack.

Position retenue :
- `gstack/` reste la reference de plomberie
- Phase 1 produit du contenu greffable sur `gstack/scripts/gen-skill-docs.ts`, `gstack/hosts/`, `gstack/review/`, `gstack/careful/`, `gstack/guard/`
- le clone `gstack/` n'est pas modifie comme source durable sans decision explicite de fork upstream

# Checks implementes

## A - Atomic writes

Gap gstack documente : gstack a des guardrails destructifs, mais pas de check dedie sur ecriture atomique de state JSON.

Le check couvre A1-A3 : direct write, JSON corrompu remplace par empty state, timeline reecrite.

## B - Cascade failure

Le check couvre les pipelines CLI qui retournent succes apres echec interne, `subprocess.run` mal gere, et save/export sans gestion `OSError`.

## D - Iteration semantics

Le check couvre latest-vs-first, slices fixes, tri instable, first-rule-wins et invariants d'iteration.

## E - LLM hallucination

Check cle de la skill : aucun finding avec `file:line` ne doit etre emis sans lecture du fichier dans la session courante.

Il renforce la discipline gstack "Search before building" par une gate explicite sur les claims de review.

## J - Bidirectional test coverage

Le check complete le testing specialist gstack avec les regles catalogue : tester les deux directions, verifier que les donnees exercent vraiment le seuil, ne pas mocker le comportement sous test.

# Limites

- Pas encore de triggers P3.
- Pas encore de generateur P4.
- Pas encore de tests unitaires P5.
- Les checks sont actionnables pour LLM humain-in-the-loop, mais pas encore executables par moteur statique.
