# ARCHITECTURE.md — Skill coding-best-practices, design v1

**Version** : 0.1 (Phase 1, Q1-Q5 et D1-D6 arbitrées)
**Date** : 2026-05-03
**Auteur** : Claude Opus 4.7 (supervisor + orchestrateur)
**Statut** : `P7-delivered/P8-review-pending` — D1-D6 arbitrées par Zack le 2026-05-04, P1-P7 livrées, P8 reviews croisées en attente

---

## 1. Vision long terme (5 phases)

```
Phase 1 (NOW)         Phase 2              Phase 3              Phase 4              Phase 5
┌──────────────┐      ┌──────────────┐     ┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│ Skill statique│ ──→ │ DB interne   │ ──→ │ Moteur RL    │ ──→ │ Knowledge    │ ──→ │ Cross-projet │
│ catalogue +  │      │ bugs vus +   │     │ pondération  │     │ graph + git  │     │ memory cross-│
│ checks       │      │ fixes        │     │ règles par   │     │ interne DB   │     │ session      │
│ contextuels  │      │ + LLM source │     │ hit rate     │     │              │     │              │
└──────────────┘      └──────────────┘     └──────────────┘     └──────────────┘     └──────────────┘
```

**Cette doc couvre Phase 1 en détail.** Les phases 2-5 sont esquissées en §6 pour informer les choix Phase 1 (éviter de fermer des portes), mais pas implémentées.

---

## 2. Phase 1 — Périmètre exact

### 2.1 Ce qu'on construit

Une extension de skill au format **gstack-compatible / Claude Skills** (compatible Codex via host adapter Phase 1), nommée `coding-best-practices`, qui :

1. **Charge le catalogue** des 18 familles / 70 sous-patterns documentés au démarrage
2. **Détecte le contexte** de chaque opération (langage cible, type d'opération : write file / write test / scan loop / review claim)
3. **Surface les checks pertinents** au bon moment (pas tous à la fois)
4. **Auto-fix mécaniques** quand possible (suppression code mort, ajout de `|| true` après grep, ajout d'atomic_write helper)
5. **Demande à l'humain** sur les cas ambigus (sécurité, design, > 20 lignes, comportement user-visible)

### 2.2 Ce qu'on ne construit PAS en Phase 1

- ❌ Base de données persistante
- ❌ Knowledge graph
- ❌ Moteur RL ou apprentissage
- ❌ Mémoire cross-projet
- ❌ Git interne à la DB
- ❌ Hooks pré-commit (laisser au CLI host)
- ❌ Plugin VS Code / IDE

---

## 3. Architecture Phase 1

### 3.1 Layout fichier

```
skill/
├── SKILL.md.tmpl                  # Template source de vérité
├── SKILL.md                       # Généré, ne pas éditer à la main
├── catalog/
│   └── bug_catalog.md             # Copie générée depuis findings/01_bug_catalog.md
├── checks/
│   ├── A_atomic_write.md          # Famille A
│   ├── B_cascade_failure.md       # Famille B
│   ├── C_scan_loop_safe.md        # Famille C
│   ├── D_iteration_semantics.md   # Famille D
│   ├── E_llm_hallucination.md     # Famille E, clé
│   ├── F_race_conditions.md       # Famille F
│   ├── G_shell_token_filtering.md # Famille G
│   ├── H_silent_override.md       # Famille H
│   ├── I_irreversible_ops.md      # Famille I
│   ├── J_bidir_test_coverage.md   # Famille J
│   ├── K_architecture_smells.md   # Famille K
│   ├── L_bash_specific.md         # Famille L
│   ├── M_drift_detection.md       # Famille M
│   ├── N_input_validation.md      # Famille N
│   ├── O_intrusive_nonportable.md # Famille O
│   ├── P_contract_consistency.md  # Famille P
│   ├── Q_numerical_precision.md   # Famille Q
│   └── R_audit_trail.md           # Famille R
├── triggers/
│   ├── on_write_state_file.md     # Quand le LLM écrit un fichier d'état
│   ├── on_write_test.md
│   ├── on_write_scan_loop.md
│   ├── on_review_claim.md
│   └── on_destructive_op.md
├── tests/
│   └── test_*.py                  # Tests unitaires des checks
├── bin/
│   └── (utilitaires CLI)
└── hosts/
    ├── claude.md                   # Config pour Claude Code
    ├── codex.md
    ├── gstack.md
    └── kimi.md
scripts/
├── gen-skill-docs.ts              # Génère skill/SKILL.md depuis le template
├── sync-catalog.ts                # Génère skill/catalog/ depuis findings/01_bug_catalog.md
└── validate.ts                    # Valide le format
```

### 3.2 Format d'un check (un fichier = une famille)

```markdown
---
family: A
name: atomic_write
severity: critical
languages: [python, bash, javascript, typescript]
triggers:
  - file_write_to_state
  - json_write
patterns_matched:
  - 'path.write_text(json.dumps('
  - 'open(.+, "w")'
fix_pattern: tmp_rename
---

# A — Écritures atomiques sur fichiers d'état

## Quand ce check s'applique

Tout `write_text` / `open(..., "w")` / `fs.writeFileSync` qui touche un fichier
contenant état persistant (DB JSON, index, catalog, manifest).

## Le pattern à éviter

```python
path.write_text(json.dumps(state))   # ❌ pas atomique
```

## Le fix mécanique

```python
def atomic_write(path: Path, content: str) -> None:
    tmp = path.with_suffix(f".tmp.{os.getpid()}")
    tmp.write_text(content, encoding="utf-8")
    tmp.replace(path)

atomic_write(path, json.dumps(state))   # ✅
```

## Pourquoi

Crash mid-write = fichier tronqué = état corrompu silencieusement. Les autres composants qui lisent ce fichier croient à une corruption normale et se fallback sur empty state, perdant tous les records antérieurs.

## Sources catalogue

- A1, A2, A3 (`findings/01_bug_catalog.md`)
- Convergence Sonnet 4.6 + Kimi sur cinq modules forensic (D2, E2, G2, G3)
```

### 3.3 Format d'un trigger

```markdown
---
trigger: on_write_state_file
phase: before_edit_or_bash
intent: Prevent corrupt, stale, or misleading persisted state.
fires_on:
  - bash_command: 'jq.*>'
  - python_pattern: '\.write_text\(json'
  - python_pattern: 'open\(.+, ["\'](w|wb)["\']'
calls_checks:
  - A_atomic_write
  - B_cascade_failure
  - M_drift_detection
suppress_when:
  - append_only_log
  - throwaway_test_fixture
preflight_budget: 45s
---

# Trigger : écriture d'un fichier d'état

Au moment où le LLM est sur le point d'écrire un fichier qui contient
un état persistant (DB JSON, index, catalog), surface les checks
`atomic_write` et `cascade_failure` AVANT que l'écriture ne soit
exécutée.

Les triggers Phase 1 doivent rester courts et opérationnels. Ils contiennent :
- un contexte d'activation concret (`fires_on`)
- les checks à charger (`calls_checks`)
- les cas où ne pas déclencher (`suppress_when`)
- une phrase de preflight que le LLM doit produire avant l'edit

Ne pas surface ces checks pour :
- Logs append-only
- Tests fixtures (déjà dans test/)
- Fichiers de cache régénérables
```

### 3.4 SKILL.md final (extrait)

Le template `SKILL.md.tmpl` agrège tout en un fichier que Claude Code charge :

```markdown
---
name: coding-best-practices
version: 0.1.0
description: |
  Surface les patterns d'erreurs LLM connus AU BON MOMENT (pas tous d'un coup).
  Triggered automatiquement quand tu écris du code touchant un fichier d'état,
  un test, une boucle de scan, ou quand tu cites un fichier:ligne dans une review.
  Repose sur un catalogue empirique de 70 sous-patterns documentés dans 18 familles
  observés sur 4760+ fichiers de notes LLM réelles.
allowed-tools:
  - Read
  - Grep
  - Bash
triggers:
  - "writing code"
  - "writing test"
  - "review this"
hooks:
  PreToolUse:
    - matcher: "Write|Edit"
      hooks:
        - type: command
          command: "bash ${CLAUDE_SKILL_DIR}/bin/check-context.sh"
---

# /coding-best-practices

[contenu généré depuis triggers/ + checks/]
```

---

## 4. Décisions architecturales clés

### D1 — Réutiliser gstack comme socle ?

**Décision P0** : OUI pour l'infrastructure gstack (gen-skill-docs, validation, hosts/, slop-scan, review/careful/guard), NON pour le contenu des checks.

- Fork `gstack/` ou en tirer juste `scripts/gen-skill-docs.ts` + `scripts/host-config.ts` ?
- **Tradeoff** : fork = propre mais on pull pas leurs updates. Cherry-pick = leger mais drift à gérer.
- **Décision Zack 2026-05-04** : augmenter gstack sans fork complet pour Phase 1. Le clone `gstack/` reste la référence et le contenu produit ici doit rester greffable au pipeline gstack.
- **Implication pratique** : ne pas développer une seconde architecture concurrente. Tout script ou format nouveau doit être justifié par rapport à `gstack/scripts/gen-skill-docs.ts`, `gstack/hosts/`, `gstack/review/`, `gstack/careful/` et `gstack/guard/`.

### D2 — Format des checks : un fichier par famille ou un fichier par sous-pattern ?

**Décision P0** : un fichier par famille (18 fichiers), avec sous-patterns en sections internes. Plus maintenable que 70 fichiers.

### D3 — Phase 1 inclut-elle l'auto-fix ?

**Décision P0** : auto-fix UNIQUEMENT pour les patterns mécaniques sans risque (ajout de `|| true` après grep, suppression code mort flagrant). Tout ce qui touche comportement user-visible → ASK.

Reproduire le Fix-First Heuristic de gstack (`gstack/review/checklist.md:144-167`).

### D4 — Multi-LLM portability dès Phase 1 ou seulement Phase 2 ?

**Décision P0** : Phase 1 produit un artefact SKILL.md installable sur Claude Code, Codex, Factory et OpenCode. La parité comportementale par host est Phase 2.

### D5 — Le catalogue est-il dans la skill ou externe ?

**Décision P0** : copie générée dans `skill/catalog/`. La source de vérité reste `findings/01_bug_catalog.md`. `scripts/sync-catalog.ts` matérialise une copie portable et vérifie que les IDs A1...R2 restent stables entre runs.

### D6 — Validation runtime de la skill : statique ou dynamique ?

**Décision P0** : validation statique pendant l'implémentation, plus smoke test dynamique obligatoire avant `accepted`. Le smoke test doit vérifier le diagnostic attendu, pas seulement l'exécution du trigger.

---

## 5. Critères de succès Phase 1

La Phase 1 est `accepted` quand :

1. ✅ `bun test` (ou `python3 -m unittest`) passe
2. ✅ La skill installe via `./setup` dans `~/.claude/skills/coding-best-practices/`
3. ✅ Un test E2E sur un fichier planté (bug A1 atomic_write) déclenche `on_write_state_file`, produit un diagnostic famille A / write_text direct, et ne fire pas sur un fichier sans bug d'atomicité
4. ✅ Convergence sur "ready" : Opus 4.7 + Sonnet (les deux Claude reviewers obligatoires), idéalement aussi GPT-5.5 (review d'autoscope) et Kimi (review systémique)
5. ✅ Un sign-off explicite Zack
6. ✅ La skill ne contredit pas une règle existante de `CLAUDE.md` projet

Pas accepted si :
- Une famille du catalogue n'est pas représentée (au moins 1 check par famille, même minimal)
- Validation runtime non implémentée (au minimum `bun run validate` ou équivalent)
- Aucun test unitaire

---

## 6. Esquisse Phase 2-5 (informative, non implémentée)

### Phase 2 — Base de données interne

**Schema initial proposé** (à arbitrer) :

```sql
-- Bugs observés et corrigés
CREATE TABLE bug_observations (
    id INTEGER PRIMARY KEY,
    family TEXT NOT NULL,             -- A, B, C, ..., R
    sub_pattern TEXT NOT NULL,        -- A1, A2, ..., R2
    project_id TEXT NOT NULL,         -- slug du projet
    file_path TEXT NOT NULL,
    file_line INTEGER,
    introduced_by TEXT,               -- LLM source ou "human"
    detected_by TEXT,                 -- LLM ou "human"
    fixed_by TEXT,
    fix_commit_sha TEXT,
    detected_at TEXT NOT NULL,        -- ISO 8601 UTC
    fixed_at TEXT,
    severity TEXT,
    notes TEXT
);

-- Sessions LLM
CREATE TABLE sessions (
    id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL,
    llm TEXT NOT NULL,
    started_at TEXT NOT NULL,
    ended_at TEXT,
    handoff_artifact_path TEXT
);

-- Edges entre bugs (e.g., "bug B causé par fix A incomplet")
CREATE TABLE bug_edges (
    src_bug_id INTEGER NOT NULL,
    dst_bug_id INTEGER NOT NULL,
    relation TEXT NOT NULL,           -- "caused_by", "duplicate_of", "fixed_by", "regressed_into"
    PRIMARY KEY (src_bug_id, dst_bug_id, relation)
);

-- Hit rate par check (pour Phase 3 RL)
CREATE TABLE check_hits (
    check_id TEXT NOT NULL,
    project_id TEXT NOT NULL,
    fired_at TEXT NOT NULL,
    was_real_bug INTEGER NOT NULL,    -- 0 ou 1, basé sur le verdict humain ou test
    file_path TEXT
);
```

**Décision Phase 1** : on stocke le catalogue de manière à pouvoir le **migrer vers cette DB en Phase 2**. → Le catalogue doit avoir des IDs stables (A1, A2, ... R2), des champs structurés (severity, languages, patterns), pas du markdown libre.

### Phase 3 — Moteur RL

Pondération des checks par hit rate. Si `atomic_write` fire 100× et capture 95 vrais bugs, le check garde priorité haute. Si `q_numerical_precision` fire 50× et capture 1 vrai bug, baisser sa priorité.

**Algorithme proposé** : Thompson Sampling sur le triplet (check, project, language). Update à chaque feedback humain.

**Décision Phase 1** : prévoir le `check_hits` schema mais ne pas l'instrumenter encore.

### Phase 4 — Knowledge graph + git interne

Le graph stocke :
- Nodes : bugs, fichiers, fonctions, sessions, LLM
- Edges : `caused_by`, `fixed_by`, `regressed_into`, `referenced_in_review`, `introduced_by`

Le "git interne" = chaque commit dans la DB est append-only avec hash chain (comme la timeline forensic). Permet de re-lire l'évolution du projet sans avoir besoin du git externe.

### Phase 5 — Cross-projet memory

Quand le LLM change de projet, la skill charge automatiquement :
- Le project_state du projet courant (depuis la DB)
- Les bugs récents de ce projet
- Les sessions précédentes pour ce LLM sur ce projet
- Le LLM "se souvient" de "où on en était"

C'est ici que la skill devient ce que l'utilisateur a décrit : *"les LLM ne réoublient pas où on en est quand on change de projet"*.

---

## 7. Décisions arbitrées avant P1

1. **Nom final** : `coding-best-practices`
2. **Repo** : monorepo `Dict_AI_Coding/` pendant Phase 1
3. **License** : pas de licence pendant Phase 1
4. **Git** : repo initialisé, distant `Kenchan1111/coding-best-practices`
5. **Démo E2E** : fixture plantée d'abord, `Depollution_Sols` ensuite
6. **D1-D6** : tranchées par Zack le 2026-05-04, voir `reviews/global_handoff/01-zack-arbitrage-d1-d6-20260504.md`

---

## 8. Sequencing Phase 1 (proposé)

| Étape | Owner | Durée estimée (CC+gstack) | Livrable |
|-------|-------|---------------------------|----------|
| 1. Lecture obligatoire (CLAUDE.md + 3 findings + ARCHITECTURE.md + son onboarding) | GPT-5.5 (impl) + Sonnet (co-reviewer) | 30 min chacun | Notes de prise en charge dans `reviews/<agent>/proposition/01-onboarding-ack-YYYYMMDD.md` |
| 2. Décision sur D1-D6 + Q1-Q5 | Opus 4.7 (orchestre) + Sonnet (co-rev) + GPT-5.5 (avis stratégique) + Zack (tranche) | 1 heure | `reviews/global_handoff/00-architecture-decisions-YYYYMMDD.md` |
| 3. Scaffolding `skill/` (dossiers + SKILL.md.tmpl vide) | GPT-5.5 | 30 min | `skill/` peuplé |
| 4. 18 fichiers `checks/<family>.md` (à partir du catalogue) | GPT-5.5 | 4 heures | `skill/checks/*.md` |
| 5. 5 fichiers `triggers/*.md` | GPT-5.5 | 2 heures | `skill/triggers/*.md` |
| 6. `scripts/gen-skill-docs.ts` (cherry-pick depuis gstack) | GPT-5.5 | 1 heure | SKILL.md généré |
| 7. Tests unitaires des checks | GPT-5.5 | 2 heures | `skill/tests/test_*.py` |
| 8. `setup` script | GPT-5.5 | 1 heure | Install dans `~/.claude/skills/` |
| 9. E2E test (planted bug fixture) | GPT-5.5 | 2 heures | Démo qui marche |
| 10. Review continue (au fil des PRs, pas à la fin) | Sonnet (line-by-line) + Opus 4.7 (synthèse) | parallèle | `reviews/claude-{sonnet,opus}/corrections/<NN>-pr-<PR>-YYYYMMDD.md` |
| 11. Sign-off Opus 4.7 + Sonnet | Reviewers | 1 heure | Convergence dans `reviews/global_handoff/01-phase1-convergence-YYYYMMDD.md` |
| 12. Review indépendante Kimi (optionnelle) | délégation Opus 4.7 | 1 heure | `reviews/kimi/proposition/01-phase1-review-YYYYMMDD.md` |
| 13. Sign-off final Zack | Zack | 30 min | Tag git `phase1-accepted` |

**Total estimé** : ~15 heures CC+gstack pour atteindre Phase 1 acceptée.

---

*Document `proposed`. Sign-off attendu : Sonnet (co-reviewer) + GPT-5.5 (implementer en mode strategic-review d'autres) + Zack (décideur). Review indépendante optionnelle : Kimi délégué.*
