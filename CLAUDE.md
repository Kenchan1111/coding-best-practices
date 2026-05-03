# CLAUDE.md — règles du projet skill coding-best-practices

Ce fichier gouverne **toute session** de tout LLM (Claude Sonnet, Claude Opus 4.7, ChatGPT, Codex, Kimi, Gemini, GPT-5.5) qui travaille dans ce répertoire.

---

## 1. Mission du projet

Construire une **skill de coding portable multi-LLM** ancrée dans un catalogue empirique d'erreurs LLM (78 sous-patterns dans 18 familles) extrait de 3 repos sources (~4760 .md analysés en échantillonnage haut-signal).

**Vision long terme** :
- Skill portable : Claude Code, Codex, OpenCode, ChatGPT custom GPT, Kimi
- Base de données interne (knowledge graph des bugs vus, fixes appliqués, LLM impliqués)
- Moteur RL : pondération des règles selon hit rate
- Mémoire cross-projet (le LLM ne réoublie pas où on en est quand on change de projet)
- Structure git interne à la DB

**Phase 1 (en cours)** : skill de coding statique ancrée sur le catalogue. Voir `ARCHITECTURE.md`.

---

## 2. Rôles dans le projet

| Rôle | Qui | Mandat |
|------|-----|--------|
| **Owner / décideur final** | Zack | Tranche en cas de divergence inter-LLM. Toute action irréversible passe par lui. |
| **Reviewer stratégique + orchestrateur** | Claude Opus 4.7 (cette instance) | Revue stratégique, synthèse cross-LLM, vérification reproduction. Profil observé : orchestrateur qui s'auto-amende. |
| **Co-reviewer stratégique** | Claude Sonnet | Lecture statique ligne-par-ligne, défauts d'implémentation concrets. Profil observé : surgical precision sur 5 modules forensic. |
| **Implementer + reviewer stratégique** | GPT-5.5 (double casquette) | Écrit le code de la skill. **Aussi** : apporte sa perspective stratégique full-app dual-skill (engineering + domaine). Profil observé : ultrareview avec findings à impact métier. |
| **Reviewer systémique + perspective utilisateur** | Kimi | Revue systémique (invariants, contrats, garanties manquantes), tableaux comparatifs, **perspective end-user de la skill** (Kimi est un consommateur potentiel du skill). Indépendance épistémologique (famille de modèle différente des Claude et OpenAI). |

Chaque rôle écrit ses outputs dans `reviews/<agent>/{proposition,corrections,handoff}/`.

**Discipline de double casquette pour GPT-5.5** :
- Quand GPT-5.5 review le travail des autres (Opus 4.7 / Sonnet / l'architecture) → c'est une voix indépendante, **compte pour la convergence inter-LLM**
- Quand GPT-5.5 review sa propre implémentation → **ne compte pas** pour la convergence (self-review). La validation reste à charge des deux Claude reviewers.

---

## 3. Documents canoniques (ordre de lecture)

Toute session démarre par cette séquence :

1. **`CLAUDE.md`** (ce fichier) — règles du projet
2. **`findings/01_bug_catalog.md`** — 18 familles, 78 sous-patterns, top 10 par fréquence
3. **`findings/02_gstack_review.md`** — audit gstack + couverture vs catalogue
4. **`findings/03_methodology.md`** — règles de processus distillées des observations
5. **`ARCHITECTURE.md`** — design de la skill v1
6. **`TODOS.md`** — backlog ordonné
7. **`ONBOARDING_<TON_LLM>.md`** — uniquement le tien :
   - `ONBOARDING_OPUS47.md` (cette session, supervisor + orchestrateur)
   - `ONBOARDING_SONNET.md` (co-reviewer stratégique ligne-par-ligne)
   - `ONBOARDING_GPT55.md` (implementer + reviewer stratégique double casquette)
   - `ONBOARDING_KIMI.md` (reviewer systémique + perspective end-user)

Documents supplémentaires (lazy load) :
- `reviews/<agent>/...` — reviews croisées
- `gstack/` — repo de référence cloné, à consulter pour les patterns d'infrastructure
- `dictionary-of-ai-coding/` — repo de référence cloné, vocabulaire d'AI coding

---

## 4. Conventions absolues (ne pas déroger)

### 4.1 Frontmatter sur tout doc de review

```yaml
---
id: <agent>-<type>-<NN>-<YYYYMMDD>
title: Titre concis
date: YYYY-MM-DD
status: draft | proposed | applied | accepted | archived
agent: claude-sonnet | claude-opus | kimi | chatgpt | codex | gemini | gpt-5.5
review_kind: proposition | corrections | handoff
target_agent: <destinataire>
scope: <fichiers concernés>
synopsis: >
  Description en 2-3 phrases. Pourquoi le doc existe.
must_read: true   # uniquement pour références fondamentales
---
```

### 4.2 Append-only

Reviews, handoffs, changelogs, audit trails — **jamais réécrits**. Ajouter un fichier daté.

### 4.3 Atomic writes sur tout fichier d'état

Tout `path.write_text()` qui touche un état persistant (DB, index, catalog) passe par :

```python
def atomic_write(path: Path, content: str) -> None:
    tmp = path.with_suffix(f".tmp.{os.getpid()}")
    tmp.write_text(content, encoding="utf-8")
    tmp.replace(path)  # atomique sur POSIX
```

### 4.4 Cascade explicite

Tout `main()` qui orchestre des étapes capture explicitement les erreurs de chaque étape et propage le returncode. Aucun `return 0` final sans `try/except` autour des sous-appels.

### 4.5 Scan-loop par item

Tout `for path in glob(...): work(path)` doit avoir un `try/except` autour de `work(path)`, pas autour du `for`. Un fichier corrompu ne tue pas la boucle.

### 4.6 Tests bidirectionnels

Tout test d'un comportement bidirectionnel (upper/lower, asc/desc, encode/decode, get/set) couvre les deux directions explicitement. Pas de test "side=upper" tout seul.

### 4.7 Voix française

Le projet est en français. Toutes les docs (CLAUDE.md, findings/, ARCHITECTURE.md, TODOS.md, reviews) en français. Le code et les noms d'identifiants en anglais (convention universelle). Les commentaires de code en français OK si le contexte projet l'est.

### 4.8 Pas d'emojis dans le code

Emojis OK dans les docs si ça aide la lisibilité (🔴/🟠/🟡/⚪ pour fréquences, ✅/⚠️/❌ pour status). **Jamais dans le code source.**

---

## 5. Méta-règles de processus (depuis `findings/03_methodology.md`)

### 5.1 Vérifier avant de réclamer

Avant de citer un `file:line` ou affirmer qu'un bug existe :
1. Lire le fichier dans la session courante
2. Reproduire (script Python ou commande shell)
3. Citer la sortie réelle

**Aucun finding n'est repris sans vérification indépendante** (règle d'Opus 4.7).

### 5.2 Search before building

Avant de coder un helper, grep le repo pour vérifier qu'il n'existe pas déjà. Avant de proposer un pattern, vérifier le runtime/framework built-in.

### 5.3 Convergence vs divergence inter-LLM

- Convergence (2+ LLM trouvent le même bug indépendamment) → **P0/P1, signal fort**
- Divergence → **à arbitrer**, ne pas trancher unilatéralement, exposer les deux positions

### 5.4 Bisect commits

Chaque commit = un changement logique unique, indépendamment revertable. Renames séparés des refactors. Tests séparés du code testé.

### 5.5 Pas de re-fix d'un bug déjà fixé

Avant de proposer un fix, grep le code pour la solution actuelle. Souvent le fix est déjà appliqué et le ticket de review est obsolète.

---

## 6. Suppressions explicites — DO NOT flag

Le bruit de complétisme nuit. Ne pas signaler :

- Redondances inoffensives qui aident la lisibilité (`present?` redondant avec `length > 20`)
- "Add a comment explaining why this threshold was chosen" — les thresholds changent, les comments rotten
- "Test exercises multiple guards simultaneously" — c'est OK
- "Regex doesn't handle edge case X" si X n'arrive jamais en pratique
- ANYTHING déjà adressé dans le diff qu'on review (lire le full diff avant de commenter)
- Eval threshold changes — tunés empiriquement, changent
- Différences de style entre fichiers existants si la convention n'est pas explicitement documentée

---

## 7. Tonalité éditoriale

- **Pas de marketing**. Pas de "robust", "comprehensive", "delve", "fundamental", "nuanced".
- **Pas d'em-dashes** dans les docs durables (utiliser virgules, points, "...").
- **Phrases courtes**. Mix punch + 2-3 phrases.
- **Numbers réels**. Pas de "fast" mais "~30s sur 30K pages".
- **Verdicts clairs**. "Bien conçu" ou "c'est un mess". Pas d'hésitation diplomatique.
- **Ne pas vendre la skill** — décrire ce qu'elle fait, ses limites, son périmètre.

Inspiration : voix observée dans `gstack/CLAUDE.md` "CHANGELOG style" — directe, factuelle, anti-marketing.

---

## 8. Communication entre rôles

### 8.1 Implementer → Reviewers

Quand GPT-5.5 (impl) finit un block de travail, il dépose une note dans :
```
reviews/gpt-5.5/proposition/NN-titre-YYYYMMDD.md
```

Format minimum : `id`, `title`, `date`, `status`, `agent`, `synopsis`, `validation performed`, `next step`.

GPT-5.5 peut **aussi** déposer des notes stratégiques (sa double casquette) dans le même dossier, sur le travail d'Opus/Sonnet/architecture.

### 8.2 Reviewers → Implementer

Quand Opus 4.7 (orchestrateur) répond, dépose dans :
```
reviews/claude-opus/corrections/NN-titre-YYYYMMDD.md
```

Quand Sonnet (co-reviewer ligne-par-ligne) répond, dépose dans :
```
reviews/claude-sonnet/corrections/NN-titre-YYYYMMDD.md
```

### 8.3 Convergence requise

Tout merge ou décision architecturale majeure doit avoir **les deux sign-offs Claude** (Opus 4.7 + Sonnet) OU un sign-off + arbitrage Zack. Sinon, status reste `proposed`, jamais `accepted`.

**Convergence inter-LLM** = signal P0 (cf `findings/03_methodology.md` §3) :
- Opus 4.7 + Sonnet d'accord → fort (même famille Anthropic)
- Opus 4.7 + Sonnet + GPT-5.5 (en mode review d'autres) d'accord → très fort (2 familles)
- Opus 4.7 + Sonnet + GPT-5.5 + Kimi d'accord → **maximal** (3 familles de modèle représentées : Anthropic, OpenAI, Moonshot)

### 8.4 Décisions ouvertes → Zack

Quand reviewer + implementer divergent, ouvrir une question dans `reviews/global_handoff/NN-question-pour-zack-YYYYMMDD.md` avec les deux positions exposées.

---

## 9. Périmètre Phase 1 — éviter le scope creep

La Phase 1 est **explicitement limitée** à :
- Une skill `coding-best-practices` (nom de travail) au format Claude Skills
- Lecture du catalogue + dérivation de checks contextuels
- Format SKILL.md + .tmpl régénérable
- Compatible installation `~/.claude/skills/` ET `~/.codex/skills/`
- Pas de DB persistante en Phase 1
- Pas de RL en Phase 1
- Pas de knowledge graph en Phase 1

Les phases 2 (DB), 3 (RL), 4 (knowledge graph), 5 (cross-project) sont **explicitement hors scope** Phase 1. Voir `ARCHITECTURE.md` pour le séquencement.

Si un travail Phase 1 nécessite un teaser de Phase 2+, le documenter en `ARCHITECTURE.md` mais ne pas l'implémenter.

---

## 10. Tests et validation

Avant tout handoff Implementer → Reviewer :

```bash
# Format SKILL.md valide
# (à définir une fois qu'on a le validator — gstack en a un)

# Tests unitaires si on en a écrit
python3 -m unittest discover -s skill/tests -p 'test_*.py'

# Compilation Python pour les scripts générateurs
python3 -m compileall skill/scripts/
```

Sortie attendue dans le frontmatter du handoff :
```yaml
validation:
  - "python3 -m unittest discover -s skill/tests -p 'test_*.py' → 12 tests OK"
  - "python3 -m compileall skill/scripts/ → OK"
```

---

## 11. Mises à jour de ce fichier

`CLAUDE.md` est append-only par convention douce : on n'efface pas une règle, on la marque `# DEPRECATED YYYY-MM-DD: <raison>` et on ajoute la nouvelle. Permet à un reviewer de comprendre l'historique.

Toute modification de `CLAUDE.md` requiert un sign-off explicite d'au moins un reviewer Claude (Opus 4.7 ou Sonnet) ou de Zack.

---

*Dernière mise à jour : 2026-05-03 — création initiale*
