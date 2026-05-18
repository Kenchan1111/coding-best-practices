---
id: gpt-5.5-proposition-07c-20260504
title: P2 cloture des 18 checks A-R
date: 2026-05-04
status: proposed
agent: gpt-5.5
review_kind: proposition
target_agent: claude-opus
scope: skill/checks A-R, TODOS.md
synopsis: >
  Cloture P2 : les 18 familles du catalogue sont materialisees en checks Markdown
  avec frontmatter stable, sources catalogue, classification Fix-First et point
  d'integration gstack.
validation:
  - "frontmatter des 18 checks parse OK"
  - "python3 -m compileall scripts -> OK"
  - "python3 scripts/sync_reviews.py twice -> 0 variantes, 0 derives on second run"
---

# Contenu livre

Les 18 checks P2 existent dans `skill/checks/` :

- `A_atomic_write.md`
- `B_cascade_failure.md`
- `C_scan_loop_safe.md`
- `D_iteration_semantics.md`
- `E_llm_hallucination.md`
- `F_race_conditions.md`
- `G_shell_token_filtering.md`
- `H_silent_override.md`
- `I_irreversible_ops.md`
- `J_bidir_test_coverage.md`
- `K_architecture_smells.md`
- `L_bash_specific.md`
- `M_drift_detection.md`
- `N_input_validation.md`
- `O_intrusive_nonportable.md`
- `P_contract_consistency.md`
- `Q_numerical_precision.md`
- `R_audit_trail.md`

# Discipline gstack

Chaque check est ecrit comme contenu greffable a gstack :

- frontmatter stable pour generation future
- `gstack_integration` explicite
- pas de moteur statique concurrent
- pas de modification durable du clone `gstack/`
- classification AUTO-FIX vs ASK coherente avec Fix-First

# Ce qui reste avant une skill utilisable

P2 fournit la matiere, pas encore le comportement runtime.

Restent :
- P3 triggers contextuels
- P4 generation + validation
- P5 tests unitaires
- P6 setup
- P7 smoke test dynamique
