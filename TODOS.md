# TODOS — Phase 1 skill coding-best-practices

**Implementer** : GPT-5.5 (double casquette : impl + reviewer stratégique)
**Reviewers stratégiques** : Claude Opus 4.7 (orchestrateur) + Claude Sonnet (lecture ligne-par-ligne)
**Reviewer systémique** : Kimi (invariants + perspective utilisateur)
**Décideur final** : Zack

Backlog ordonné. Suivre la séquence sauf si la dépendance est explicitement levée.

---

## P0 — Décisions architecturales bloquantes

> **Tranché le 2026-05-04 par Zack.**
> Voir `reviews/global_handoff/01-zack-arbitrage-d1-d6-20260504.md`.

- [x] **D1** — Augmenter gstack comme socle : greffe compatible `gen-skill-docs`, `hosts/`, `slop-scan`, `review/careful/guard`, sans fork complet en Phase 1.
- [x] **D2** — 18 fichiers checks par famille, sous-patterns en sections internes.
- [x] **D3** — Auto-fix Phase 1 seulement pour les mécaniques sans risque ; ASK pour le reste.
- [x] **D4** — Portabilité d'artefact en Phase 1 ; parité comportementale multi-host en Phase 2.
- [x] **D5** — Catalogue : copie générée dans `skill/catalog/`, source canonique `findings/01_bug_catalog.md`.
- [x] **D6** — Validation statique pendant l'implémentation + smoke test dynamique obligatoire avant `accepted`.

**Questions arbitrées par Zack** :
- [x] **Q1** — Nom final de la skill : `coding-best-practices`.
- [x] **Q2** — Monorepo `Dict_AI_Coding/` pour Phase 1.
- [x] **Q3** — Pas de licence pour l'instant.
- [x] **Q4** — `git init` autorisé et effectué.
- [x] **Q5** — Premier projet de démo E2E : fixture plantée ad hoc, puis `Depollution_Sols`.

---

## P1 — Scaffolding (après P0)

- [x] Créer la structure `skill/` (cf `ARCHITECTURE.md` §3.1)
  - `skill/SKILL.md.tmpl`
  - `skill/checks/`
  - `skill/triggers/`
  - `skill/scripts/`
  - `skill/tests/`
  - `skill/bin/`
  - `skill/hosts/`
- [x] Premier `skill/SKILL.md.tmpl` minimal (frontmatter + placeholders pour TOC + checks + triggers)
- [x] `skill/hosts/claude.md` (config pour Claude Code)
- [x] `skill/hosts/codex.md` (config pour Codex)
- [x] `skill/hosts/gstack.md` (contrat de greffe avec gstack)
- [x] Fichier `skill/README.md` qui explique qui veut savoir : (a) ce qu'est la skill, (b) comment l'installer, (c) comment elle s'utilise

**Livrable** : `reviews/gpt-5.5/proposition/06-scaffolding-YYYYMMDD.md` avec frontmatter + validation + diff.

---

## P2 — Checks par famille (18 fichiers)

Ordre de priorité (par fréquence du catalogue) :

- [x] `checks/A_atomic_write.md` (🔴 TRÈS HAUTE, 3 sous-patterns)
- [x] `checks/B_cascade_failure.md` (🔴 TRÈS HAUTE, 3)
- [x] `checks/D_iteration_semantics.md` (🔴 TRÈS HAUTE, 5)
- [x] `checks/E_llm_hallucination.md` (🔴 TRÈS HAUTE, 4) — **clé pour la skill**
- [x] `checks/J_bidir_test_coverage.md` (🔴 TRÈS HAUTE, 4)
- [x] `checks/L_bash_specific.md` (🟠 HAUTE, 10)
- [x] `checks/K_architecture_smells.md` (🟠 HAUTE, 6)
- [x] `checks/G_shell_token_filtering.md` (🟠 HAUTE, 4)
- [x] `checks/H_silent_override.md` (🟠 HAUTE, 4)
- [x] `checks/F_race_conditions.md` (🟠 HAUTE, 3)
- [x] `checks/C_scan_loop_safe.md` (🟠 HAUTE, 2)
- [x] `checks/I_irreversible_ops.md` (🟠 HAUTE, 2)
- [x] `checks/Q_numerical_precision.md` (⚪ FAIBLE-MOYENNE, 5)
- [x] `checks/M_drift_detection.md` (🟡 MOYENNE, 4)
- [x] `checks/P_contract_consistency.md` (🟡 MOYENNE, 4)
- [x] `checks/N_input_validation.md` (🟡 MOYENNE, 3)
- [x] `checks/O_intrusive_nonportable.md` (🟡 MOYENNE, 2)
- [x] `checks/R_audit_trail.md` (🟡 MOYENNE, 2)

Format de chaque fichier : voir `ARCHITECTURE.md` §3.2 pour le template exact.

**Livrables** : un commit par 3-5 fichiers. Frontmatter + validation à chaque PR.

---

## P3 — Triggers contextuels (5 fichiers)

- [x] `triggers/on_write_state_file.md` → fire `A_atomic_write`, `B_cascade_failure`
- [x] `triggers/on_write_test.md` → fire `J_bidir_test_coverage`
- [x] `triggers/on_write_scan_loop.md` → fire `C_scan_loop_safe`
- [x] `triggers/on_review_claim.md` → fire `E_llm_hallucination` (vérifier que `file:line` cité a été lu)
- [x] `triggers/on_destructive_op.md` → fire `I_irreversible_ops` (cohérent avec `/careful` de gstack)

**Livrable** : `reviews/gpt-5.5/proposition/08-triggers-YYYYMMDD.md`.

---

## P4 — Génération + validation

- [x] Adapter le pipeline `gstack/scripts/gen-skill-docs.ts` et ses resolvers au layout `skill/` sans diverger inutilement
- [x] `scripts/sync-catalog.ts` : génère `skill/catalog/bug_catalog.md` depuis `findings/01_bug_catalog.md`, avec vérification des IDs stables
- [x] `scripts/validate.ts` : vérifie frontmatter de tous `checks/` et `triggers/`, vérifie que tous les checks référencés par les triggers existent, vérifie qu'aucun fichier n'est orphelin
- [x] `bun run gen:skill-docs` produit `SKILL.md` à partir du `.tmpl` + `checks/` + `triggers/` (script prêt ; validé localement via `npm run gen:skill-docs -- --dry-run`, Bun absent)
- [x] `bun run validate` retourne exit 0 sur le repo

**Livrable** : `reviews/gpt-5.5/proposition/09-gen-and-validate-YYYYMMDD.md`.

---

## P5 — Tests unitaires

- [x] `skill/tests/test_check_atomic_write.py` — fixture avec un script Python plant un `path.write_text(json...)`, vérifie que le check fire et propose le fix
- [x] `skill/tests/test_check_cascade_failure.py`
- [x] `skill/tests/test_check_scan_loop.py`
- [x] `skill/tests/test_check_bidir_test.py`
- [x] `skill/tests/test_check_llm_hallucination.py` (la plus subtile : doit détecter qu'un `file:line` cité dans un message LLM n'a pas été lu dans la session)
- [x] `skill/tests/test_validate.py` — vérifie que `validate.ts` rejette un check sans frontmatter, un trigger qui référence un check inexistant, etc.

**Livrable** : `reviews/gpt-5.5/proposition/10-tests-YYYYMMDD.md` avec sortie `python3 -m unittest discover` dans le frontmatter.

---

## P6 — Setup + installation

- [x] `skill/setup` (bash exécutable, inspiré du `gstack/setup`) :
  - Vérifie dépendances Bun/Node/Python directes ou via Conda env `coding-best-practices`
  - Crée symlinks vers `~/.claude/skills/coding-best-practices/`
  - Crée symlinks vers `~/.codex/skills/coding-best-practices/` si Codex présent
  - Crée symlinks vers `~/.kimi/skills/coding-best-practices/` si Kimi présent
  - Run `gen:skill-docs` + `validate`
  - Idempotent
  - Refuse d'écraser une cible non gérée
- [x] `skill/uninstall` (cleanup propre des seuls liens gérés)

**Livrable** : `reviews/gpt-5.5/proposition/11-setup-YYYYMMDD.md`.

---

## P7 — Démo E2E

- [x] Fixtures plantées déjà créées dans `skill/tests/fixtures/planted-bugs/` pendant P5
- [x] Script `skill/tests/e2e/run.sh` qui :
  1. Installe la skill localement
  2. Démarre Claude Code (ou un mock)
  3. Demande à Claude d'auditer le fichier planté
  4. Vérifie que les 3 checks fire
- [x] Capture vidéo ou log structuré du résultat (preuve)

**Livrable** : `reviews/gpt-5.5/proposition/12-e2e-demo-YYYYMMDD.md`.

---

## P8 — Reviews croisées + sign-off

- [ ] Sign-off Opus 4.7 (orchestrateur) → `reviews/claude-opus/proposition/01-phase1-signoff-YYYYMMDD.md`
- [ ] Sign-off Sonnet (co-reviewer ligne-par-ligne) → `reviews/claude-sonnet/proposition/01-phase1-signoff-YYYYMMDD.md`
- [ ] **Convergence requise** : les deux Claude doivent signer ; divergence → handoff Zack
- [ ] Review systémique Kimi (fortement recommandée, non-bloquante sauf finding critique) → `reviews/kimi/proposition/01-phase1-review-YYYYMMDD.md`
- [ ] Sign-off final Zack
- [ ] Tag git `phase1-accepted`

---

## Backlog Phase 2+ (rappel — NE PAS implémenter en Phase 1)

- DB schema interne (cf `ARCHITECTURE.md` §6.1)
- Moteur RL Thompson Sampling sur `check_hits`
- Knowledge graph + git interne
- Cross-projet memory
- Plugin ChatGPT custom GPT
- Plugin Kimi
- Validation runtime dynamique (planted-bug fixtures auto-tested)

---

## Conventions sur ce TODOS.md

- Append-only sur les sections `## Done` (créer en bas du fichier quand un item bouge de `[ ]` à `[x]`)
- Ne jamais effacer un item, le déplacer en `## Done` avec date d'achèvement
- Toute nouvelle decision Pn doit pointer vers la review correspondante
- Mise à jour obligatoire après chaque livrable

---

## Done

### 2026-05-04

- P0 Q1-Q5 arbitrées par Zack. Voir `reviews/global_handoff/00-zack-arbitrage-q1-q5-20260503.md`.
- P0 D1-D6 arbitrées par Zack. Voir `reviews/global_handoff/01-zack-arbitrage-d1-d6-20260504.md`.
- P1 scaffolding livré. Voir `reviews/gpt-5.5/proposition/06-scaffolding-20260504.md`.
- Correction de cadrage P1 : la cible est une augmentation gstack-compatible, pas une skill isolée concurrente.
- P2 premier lot livré : checks A, B, D, E, J. Voir `reviews/gpt-5.5/proposition/07-p2-core-checks-gstack-alignment-20260504.md`.
- P2 second lot livré : checks F, G, H, K, L. Voir `reviews/gpt-5.5/proposition/07b-p2-high-checks-gstack-alignment-20260504.md`.
- P2 clôturé : 18 checks A-R livrés. Voir `reviews/gpt-5.5/proposition/07c-p2-complete-checks-20260504.md`.
- P3 triggers contextuels livrés. Voir `reviews/gpt-5.5/proposition/08-triggers-20260504.md`.
- P4 génération + validation livrées côté Node/NPM ; validation littérale Bun en attente car Bun absent de l'environnement. Voir `reviews/gpt-5.5/proposition/09-gen-and-validate-20260504.md`.
- P5 tests unitaires livrés : 13 tests OK. Voir `reviews/gpt-5.5/proposition/10-tests-20260504.md`.

### 2026-05-05

- P4 validation littérale Bun clôturée via Conda env `coding-best-practices` : `bun run validate`, `bun run gen:skill-docs -- --dry-run` et `bun run test` OK. Voir `reviews/gpt-5.5/proposition/09-gen-and-validate-20260504.md`.
- Correction de suivi P7 : les fixtures plantées existent déjà depuis P5 ; P7 doit maintenant livrer le harness E2E et la preuve, pas recréer les fixtures.
- P6 setup/install/uninstall livré et installé en symlink Claude/Codex. Voir `reviews/gpt-5.5/proposition/11-setup-20260505.md`.

### 2026-05-06

- P7 E2E déterministe livré : `skill/tests/e2e/run.sh` installe la skill dans un HOME temporaire, lance un mock agent, vérifie A/B/C sur fixtures plantées et produit un `result.json` structuré. Voir `reviews/gpt-5.5/proposition/12-e2e-demo-20260506.md`.

### 2026-05-12

- Corrections post-review Kimi : host Kimi minimal, setup/uninstall Kimi, notes Claude/Codex renforcées, contrat anglais court dans `SKILL.md`, validation regex des triggers. Voir `reviews/gpt-5.5/handoff/04-kimi-skill-corrections-20260512.md`.

---

*Créé le 2026-05-03 par Claude Opus 4.7 (supervisor + orchestrateur).*
