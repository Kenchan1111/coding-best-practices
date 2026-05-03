# ARCHITECTURE.md — Skill coding-best-practices, design v1

**Version** : 0.1 (draft initial, sujet à arbitrage Zack)
**Date** : 2026-05-03
**Auteur** : Claude Opus 4.7 (supervisor + orchestrateur)
**Statut** : `proposed` — attend sign-off Sonnet co-reviewer + GPT-5.5 implementer + Zack avant implémentation

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

Une skill au format **Claude Skills** (compatible Codex/OpenCode via host adapters), nommée `coding-best-practices` (nom à arbitrer), qui :

1. **Charge le catalogue** des 18 familles / 78 sous-patterns au démarrage
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
│   └── (18 familles, source)      # Symlink ou copie de findings/01_bug_catalog.md
├── checks/
│   ├── atomic_write.md            # Famille A
│   ├── cascade_failure.md         # Famille B
│   ├── scan_loop_safe.md          # Famille C
│   ├── iteration_semantics.md     # Famille D
│   ├── llm_hallucination.md       # Famille E ← clé
│   ├── race_conditions.md         # Famille F
│   ├── input_filtering.md         # Famille G
│   ├── silent_override.md         # Famille H
│   ├── irreversible_ops.md        # Famille I
│   ├── bidir_test_coverage.md     # Famille J
│   ├── architecture_smells.md     # Famille K
│   ├── bash_specific.md           # Famille L
│   ├── drift_detection.md         # Famille M
│   ├── input_validation.md        # Famille N
│   ├── intrusive_nonportable.md   # Famille O
│   ├── contract_consistency.md    # Famille P
│   ├── numerical_precision.md     # Famille Q
│   └── audit_trail.md             # Famille R
├── triggers/
│   ├── on_write_state_file.md     # Quand le LLM écrit un fichier d'état
│   ├── on_write_test.md
│   ├── on_write_scan_loop.md
│   ├── on_review_claim.md
│   └── on_destructive_op.md
├── scripts/
│   ├── gen-skill-docs.ts          # Génère SKILL.md depuis le template
│   └── validate.ts                # Valide le format
├── tests/
│   └── test_*.py                  # Tests unitaires des checks
├── bin/
│   └── (utilitaires CLI)
└── hosts/
    ├── claude.md                   # Config pour Claude Code
    ├── codex.md
    └── opencode.md
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
fires_on:
  - bash_command: 'jq.*>'
  - python_pattern: '\.write_text\(json'
  - python_pattern: 'open\(.+, ["\'](w|wb)["\']'
calls_checks:
  - atomic_write
  - cascade_failure
---

# Trigger : écriture d'un fichier d'état

Au moment où le LLM est sur le point d'écrire un fichier qui contient
un état persistant (DB JSON, index, catalog), surface les checks
`atomic_write` et `cascade_failure` AVANT que l'écriture ne soit
exécutée.

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
  Repose sur un catalogue empirique de 78 sous-patterns dans 18 familles
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

**Position proposée** : OUI pour l'infrastructure (gen-skill-docs, validation, hosts/, slop-scan), NON pour le contenu des checks.

- Fork `gstack/` ou en tirer juste `scripts/gen-skill-docs.ts` + `scripts/host-config.ts` ?
- **Tradeoff** : fork = propre mais on pull pas leurs updates. Cherry-pick = leger mais drift à gérer.
- **Recommandation** : cherry-pick `gen-skill-docs.ts` + structure `hosts/`, ne pas forker l'intégralité. À arbitrer avec Zack.

### D2 — Format des checks : un fichier par famille ou un fichier par sous-pattern ?

**Position proposée** : un fichier par famille (18 fichiers), avec sous-patterns en sections internes. Plus maintenable que 78 fichiers.

### D3 — Phase 1 inclut-elle l'auto-fix ?

**Position proposée** : auto-fix UNIQUEMENT pour les patterns mécaniques sans risque (ajout de `|| true` après grep, suppression code mort flagrant). Tout ce qui touche comportement user-visible → ASK.

Reproduire le Fix-First Heuristic de gstack (`gstack/review/checklist.md:144-167`).

### D4 — Multi-LLM portability dès Phase 1 ou seulement Phase 2 ?

**Position proposée** : Phase 1 cible Claude Code en priorité, mais le format SKILL.md est compatible Codex/Factory/OpenCode out of the box. **Pas d'effort actif** sur ChatGPT custom GPT / Kimi en Phase 1 — laisser Phase 2.

### D5 — Le catalogue est-il dans la skill ou externe ?

**Position proposée** : symlink depuis `skill/catalog/` vers `findings/01_bug_catalog.md`. La skill embarque le contenu, mais la source de vérité reste `findings/`. Quand Phase 2 introduit la DB, la DB sera populée depuis le catalogue.

### D6 — Validation runtime de la skill : statique ou dynamique ?

**Position proposée** : Phase 1 = validation **statique uniquement** (frontmatter valide, links non-cassés, py_compile, unittest). Phase 2 explorera la validation dynamique (skill se teste sur des fixtures de bugs plantés).

---

## 5. Critères de succès Phase 1

La Phase 1 est `accepted` quand :

1. ✅ `bun test` (ou `python3 -m unittest`) passe
2. ✅ La skill installe via `./setup` dans `~/.claude/skills/coding-best-practices/`
3. ✅ Un test E2E sur un fichier planté (bug A1 atomic_write) déclenche le check correspondant
4. ✅ Convergence sur "ready" : Opus 4.7 + Sonnet (les deux Claude reviewers obligatoires), idéalement aussi GPT-5.5 (review d'autoscope) et Kimi délégué (indépendance famille de modèle)
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

## 7. Questions ouvertes pour arbitrage

1. **Nom final de la skill** : `coding-best-practices` ? `code-quality` ? `bug-shield` ? Quelque chose en français ? — pour Zack
2. **Repo séparé ou monorepo** : la skill vit dans ce repo `Dict_AI_Coding/` ou on en fait un repo dédié ? — pour Zack
3. **License** : MIT comme gstack ? Privée pour l'instant ? — pour Zack
4. **gstack fork ou cherry-pick** : voir D1 — pour Zack
5. **Première démo** : quel projet test ? Un repo planté avec bugs de chaque famille ? Ou tester direct sur Depollution_Sols ? — à coordonner avec GPT-5.5 (impl)

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
