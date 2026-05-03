# TODOS — Phase 1 skill coding-best-practices

**Implementer** : GPT-5.5 (double casquette : impl + reviewer stratégique)
**Reviewers stratégiques** : Claude Opus 4.7 (orchestrateur) + Claude Sonnet (lecture ligne-par-ligne)
**Reviewer indépendant optionnel** : Kimi délégué
**Décideur final** : Zack

Backlog ordonné. Suivre la séquence sauf si la dépendance est explicitement levée.

---

## P0 — Décisions architecturales bloquantes

> **Pas une ligne de code avant que ces 6 décisions soient tranchées.**
> À publier dans `reviews/global_handoff/00-architecture-decisions-YYYYMMDD.md`.

- [ ] **D1** — Réutiliser gstack comme socle ? Cherry-pick ou fork ? — Position Opus 4.7 : cherry-pick `gen-skill-docs.ts` + `hosts/`. À arbitrer Zack.
- [ ] **D2** — 18 fichiers checks (par famille) ou 78 (par sous-pattern) ? — Position Opus 4.7 : 18.
- [ ] **D3** — Auto-fix Phase 1 : seulement mécaniques sans risque ? — Position Opus 4.7 : oui, ASK pour le reste (Fix-First Heuristic).
- [ ] **D4** — Multi-LLM portability dès Phase 1 ou Phase 2 ? — Position Opus 4.7 : Claude Code en priorité Phase 1, Codex/Factory/OpenCode out-of-the-box via SKILL.md, ChatGPT/Kimi en Phase 2.
- [ ] **D5** — Catalogue : symlink vers `findings/01_bug_catalog.md` ou copie dans `skill/` ? — Position Opus 4.7 : symlink + IDs stables (A1...R2) pour migration Phase 2.
- [ ] **D6** — Validation runtime : statique ou dynamique en Phase 1 ? — Position Opus 4.7 : statique seulement.

**Open question pour Zack** :
- [ ] **Q1** — Nom final de la skill (`coding-best-practices` / `code-quality` / `bug-shield` / autre) ?
- [ ] **Q2** — Repo séparé ou monorepo (rester dans `Dict_AI_Coding/`) ?
- [ ] **Q3** — License (MIT comme gstack, ou privée) ?
- [ ] **Q4** — `git init` dans `Dict_AI_Coding/` autorisé ? (pas un repo git pour l'instant)
- [ ] **Q5** — Premier projet de démo E2E : repo planté ad-hoc OU test direct sur Depollution_Sols ?

---

## P1 — Scaffolding (après P0)

- [ ] Créer la structure `skill/` (cf `ARCHITECTURE.md` §3.1)
  - `skill/SKILL.md.tmpl`
  - `skill/checks/`
  - `skill/triggers/`
  - `skill/scripts/`
  - `skill/tests/`
  - `skill/bin/`
  - `skill/hosts/`
- [ ] Premier `skill/SKILL.md.tmpl` minimal (frontmatter + placeholders pour TOC + checks + triggers)
- [ ] `skill/hosts/claude.md` (config pour Claude Code)
- [ ] Fichier `skill/README.md` qui explique qui veut savoir : (a) ce qu'est la skill, (b) comment l'installer, (c) comment elle s'utilise

**Livrable** : `reviews/claude-opus/proposition/02-scaffolding-YYYYMMDD.md` avec frontmatter + validation + diff.

---

## P2 — Checks par famille (18 fichiers)

Ordre de priorité (par fréquence du catalogue) :

- [ ] `checks/A_atomic_write.md` (🔴 TRÈS HAUTE, 3 sous-patterns)
- [ ] `checks/B_cascade_failure.md` (🔴 TRÈS HAUTE, 3)
- [ ] `checks/D_iteration_semantics.md` (🔴 TRÈS HAUTE, 5)
- [ ] `checks/E_llm_hallucination.md` (🔴 TRÈS HAUTE, 4) — **clé pour la skill**
- [ ] `checks/J_bidir_test_coverage.md` (🔴 TRÈS HAUTE, 4)
- [ ] `checks/L_bash_specific.md` (🟠 HAUTE, 10)
- [ ] `checks/K_architecture_smells.md` (🟠 HAUTE, 6)
- [ ] `checks/G_input_filtering.md` (🟠 HAUTE, 4)
- [ ] `checks/H_silent_override.md` (🟠 HAUTE, 4)
- [ ] `checks/F_race_conditions.md` (🟠 HAUTE, 3)
- [ ] `checks/C_scan_loop_safe.md` (🟠 HAUTE, 2)
- [ ] `checks/I_irreversible_ops.md` (🟠 HAUTE, 2)
- [ ] `checks/Q_numerical_precision.md` (⚪ FAIBLE-MOYENNE, 5)
- [ ] `checks/M_drift_detection.md` (🟡 MOYENNE, 4)
- [ ] `checks/P_contract_consistency.md` (🟡 MOYENNE, 4)
- [ ] `checks/N_input_validation.md` (🟡 MOYENNE, 3)
- [ ] `checks/O_intrusive_nonportable.md` (🟡 MOYENNE, 2)
- [ ] `checks/R_audit_trail.md` (🟡 MOYENNE, 2)

Format de chaque fichier : voir `ARCHITECTURE.md` §3.2 pour le template exact.

**Livrables** : un commit par 3-5 fichiers. Frontmatter + validation à chaque PR.

---

## P3 — Triggers contextuels (5 fichiers)

- [ ] `triggers/on_write_state_file.md` → fire `A_atomic_write`, `B_cascade_failure`
- [ ] `triggers/on_write_test.md` → fire `J_bidir_test_coverage`
- [ ] `triggers/on_write_scan_loop.md` → fire `C_scan_loop_safe`
- [ ] `triggers/on_review_claim.md` → fire `E_llm_hallucination` (vérifier que `file:line` cité a été lu)
- [ ] `triggers/on_destructive_op.md` → fire `I_irreversible_ops` (cohérent avec `/careful` de gstack)

**Livrable** : `reviews/claude-opus/proposition/04-triggers-YYYYMMDD.md`.

---

## P4 — Génération + validation

- [ ] Cherry-pick `scripts/gen-skill-docs.ts` depuis gstack (adapter aux paths du projet)
- [ ] `scripts/validate.ts` : vérifie frontmatter de tous `checks/` et `triggers/`, vérifie que tous les checks référencés par les triggers existent, vérifie qu'aucun fichier n'est orphelin
- [ ] `bun run gen:skill-docs` produit `SKILL.md` à partir du `.tmpl` + `checks/` + `triggers/`
- [ ] `bun run validate` retourne exit 0 sur le repo

**Livrable** : `reviews/claude-opus/proposition/05-gen-and-validate-YYYYMMDD.md`.

---

## P5 — Tests unitaires

- [ ] `skill/tests/test_check_atomic_write.py` — fixture avec un script Python plant un `path.write_text(json...)`, vérifie que le check fire et propose le fix
- [ ] `skill/tests/test_check_cascade_failure.py`
- [ ] `skill/tests/test_check_scan_loop.py`
- [ ] `skill/tests/test_check_bidir_test.py`
- [ ] `skill/tests/test_check_llm_hallucination.py` (la plus subtile : doit détecter qu'un `file:line` cité dans un message LLM n'a pas été lu dans la session)
- [ ] `skill/tests/test_validate.py` — vérifie que `validate.ts` rejette un check sans frontmatter, un trigger qui référence un check inexistant, etc.

**Livrable** : `reviews/claude-opus/proposition/06-tests-YYYYMMDD.md` avec sortie `python3 -m unittest discover` dans le frontmatter.

---

## P6 — Setup + installation

- [ ] `skill/setup` (bash exécutable, inspiré du `gstack/setup`) :
  - Vérifie dépendances (bun, jq, etc.)
  - Crée symlinks vers `~/.claude/skills/coding-best-practices/`
  - Crée symlinks vers `~/.codex/skills/coding-best-practices/` si Codex présent
  - Run `gen:skill-docs` + `validate`
  - Idempotent
- [ ] `skill/uninstall` (cleanup propre)

**Livrable** : `reviews/claude-opus/proposition/07-setup-YYYYMMDD.md`.

---

## P7 — Démo E2E

- [ ] Créer `skill/test/fixtures/planted-bugs/` avec un fichier Python contenant 3 bugs plantés (A1 atomic_write, C1 scan_loop, J2 bidir_test)
- [ ] Script `skill/test/e2e/run.sh` qui :
  1. Installe la skill localement
  2. Démarre Claude Code (ou un mock)
  3. Demande à Claude d'auditer le fichier planté
  4. Vérifie que les 3 checks fire
- [ ] Capture vidéo ou log structuré du résultat (preuve)

**Livrable** : `reviews/claude-opus/proposition/08-e2e-demo-YYYYMMDD.md`.

---

## P8 — Reviews croisées + sign-off

- [ ] Sign-off Opus 4.7 (orchestrateur) → `reviews/claude-opus/proposition/01-phase1-signoff-YYYYMMDD.md`
- [ ] Sign-off Sonnet (co-reviewer ligne-par-ligne) → `reviews/claude-sonnet/proposition/01-phase1-signoff-YYYYMMDD.md`
- [ ] **Convergence requise** : les deux Claude doivent signer ; divergence → handoff Zack
- [ ] Délégation review indépendante Kimi (optionnelle, fortement recommandée pour indépendance famille de modèle) → `reviews/kimi/proposition/01-phase1-review-YYYYMMDD.md`
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

*(à peupler au fur et à mesure)*

---

*Créé le 2026-05-03 par Claude Opus 4.7 (supervisor + orchestrateur).*
