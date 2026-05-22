---
id: kimi-prop-06-20260521
title: Review code intransigeante — swarm mode, tous composants
date: 2026-05-21
status: proposed
agent: kimi
review_kind: proposition
target_agent: gpt-5.5
scope: scripts/*.ts, scripts/*.py, skill/setup, skill/uninstall, skill/tests/*.py, skill/bin/, skill/hosts/*.md
synopsis: >
  Review intransigeante du code complet apres durcissement pre-signoff du 2026-05-21.
  18 findings : 5 critiques, 6 majeurs, 7 moderes.
  Incoherence handoff/code, bug Merkle CVE-2012-2459 dans le repo lui-meme,
  hardcoding reliquats, stubs vides, parsers divergents, et absence de tests
  sur local_git_guard.py.
---

# Review code intransigeante — swarm mode

**Kimi — review systemique, mode swarm, tous composants**

Date : 2026-05-21
Cible : etat courant du repo (`8267365d+dirty` selon handoff GPT-5.5)
Mandat : examiner les handoffs de ChatGPT/GPT-5.5, le code complet, et faire un raise de toutes les incoherences, POC, stubs, code incomplet, mauvais piping, ou logique incomplete.

---

## 1. Executive summary

Les 36 tests Python passent. La validation statique passe. Le E2E mock passe. Cela ne veut pas dire que le code est sain.

**5 findings critiques** dont 1 **bug de securite cryptographique** (Merkle duplicate-last, CVE-2012-2459) present dans le code du repo alors que la skill pretend le detecter (K6). **2 reliquats de hardcoding** que le handoff du 21 mai pretend fermes mais qui sont toujours presents. **1 stub vide** (`skill/bin/`). **1 omission d'agent** (kimi absent de `DEFAULT_AGENTS`).

Le verdict est clair : **le repo n'est pas pret pour `phase1-accepted` sans correction des 5 findings critiques.**

---

## 2. Findings par severite

### Tableau synthetique

| # | Severite | Composant | Finding | Effort |
|---|----------|-----------|---------|--------|
| C1 | **CRITIQUE** | `scripts/sync-catalog.ts:55` | Hardcoding `70` reliquat ; handoff du 21 mai pretend l'avoir supprime | 5 min |
| C2 | **CRITIQUE** | `scripts/skill-lib.ts:11` | `EXPECTED_FAMILIES` hardcode A-R ; scalabilite cassee | 10 min |
| C3 | **CRITIQUE** | `scripts/local_git_guard.py:68-69` | Bug Merkle duplicate-last (CVE-2012-2459) — exactement K6 du catalogue | 30 min |
| C4 | **CRITIQUE** | `scripts/knowledge_os.py:17` | `DEFAULT_AGENTS` omet `kimi` ; le reviewer systemique est invisible pour le sync | 1 min |
| C5 | **CRITIQUE** | `skill/bin/` | Repertoire vide (seul `.gitkeep`) ; stub non documente | 1 min |
| M1 | **MAJEUR** | `skill/tests/e2e/mock_agent.py` | POC deterministe, pas E2E ; aucune preuve de comportement LLM | Documenter comme POC |
| M2 | **MAJEUR** | `scripts/skill-lib.ts:66-99` vs `skill/tests/frontmatter_utils.py` | Deux parsers frontmatter differents ; risque de divergence | Unifier ou tester cross-parser |
| M3 | **MAJEUR** | `scripts/local_git_guard.py` | 582 lignes, zero test unitaire dans le repo | Ajouter tests |
| M4 | **MAJEUR** | `scripts/gen-skill-docs.ts:22-25` | Couplage fort avec sync-catalog.ts via `execFileSync` ; crash opaque | Gerer l'erreur |
| M5 | **MAJEUR** | `scripts/sync_reviews.py:570-572` | `variant_notes` et `warnings` ne retournent pas exit 1 | Corriger la logique |
| M6 | **MAJEUR** | `skill/tests/frontmatter_utils.py:15-27` | `_normalize_value` corrompt les dicts mono-cle legitimes | Refactoriser |
| m1 | **MODERE** | `skill/setup:216` | `ln -sfn` sans verification que la cible est un repertoire | Ajouter un check |
| m2 | **MODERE** | `skill/SKILL.md.tmpl:24-28` | Contrat anglais de 3 lignes ; insuffisant pour host anglophone | Etendre |
| m3 | **MODERE** | `scripts/skill-lib.ts:66-99` | Parser YAML simpliste ne gere pas nested objects | Documenter la limitation |
| m4 | **MODERE** | `skill/hosts/*.md` | Notes host bien meilleures mais encore sans section "Troubleshooting" | Ajouter |
| m5 | **MODERE** | `scripts/sync-catalog.ts:15` | Path canonique hardcode `findings/01_bug_catalog.md` | Utiliser une constante centralisee |
| m6 | **MODERE** | `skill/tests/e2e/run.sh` | Pas de verification que `python3` a `pyyaml` installe | Documenter dependance |
| m7 | **MODERE** | `scripts/local_git_guard.py:68-69` | Le Merkle duplicate-last n'est pas seulement esthetique ; il cree des collisions | Corriger K6 |

---

## 3. Findings detailles

### C1 — Hardcoding `70` reliquat dans sync-catalog.ts

**Fichier** : `scripts/sync-catalog.ts:55`
**Code** :
```typescript
if (ids.length !== 70) {
  throw new Error(`expected 70 catalog IDs, found ${ids.length}`);
}
```

**Handoff GPT-5.5 du 2026-05-21** dit explicitement :
> "le check ne repose plus sur un `70` duplique"

**Constat** : le `70` n'est plus duplique (il n'est plus dans validate.ts), mais il est **toujours present** dans sync-catalog.ts. Le handoff est **factuellement incorrect** sur ce point.

**Impact** : si on ajoute une famille S au catalogue, sync-catalog.ts plantera avec "expected 70 catalog IDs, found 71".

**Fix** : remplacer par une extraction dynamique ou une comparaison avec le nombre attendu deduit du catalogue source.

---

### C2 — EXPECTED_FAMILIES hardcode A-R

**Fichier** : `scripts/skill-lib.ts:11`
**Code** :
```typescript
export const EXPECTED_FAMILIES = "ABCDEFGHIJKLMNOPQR".split("");
```

**Constat** : les familles sont prescrites, pas deduites. Si le catalogue source ajoute une famille S, il faut modifier le code source.

**Impact** : scalabilite cassee. L'invariant "ajouter une famille au catalogue" necessite un changement de code dans 3 fichiers (skill-lib.ts, sync-catalog.ts, validate.ts via EXPECTED_FAMILIES).

**Fix** : deduire EXPECTED_FAMILIES de `extractCatalogIds(sourceContent)` ou documenter explicitement que l'ajout d'une famille requiert un bump manuel.

---

### C3 — Bug Merkle duplicate-last (CVE-2012-2459) dans local_git_guard.py

**Fichier** : `scripts/local_git_guard.py:68-69`
**Code** :
```python
if len(level) % 2 == 1:
    level.append(level[-1])
```

**Constat** : c'est **exactement** le pattern K6 du catalogue (`checks/K_architecture_smells.md`) :
> "K6. Doublon Bitcoin dans Merkle tree (CVE-2012-2459 pattern)"

Le repo qui construit une skill pour detecter ce bug **contient le bug lui-meme**.

**Impact** : collision Merkle. Si le dernier leaf est identique a l'avant-dernier, l'ajout du duplicate-last cree une ambiguite : un arbre avec N leaves et un arbre avec N-1 leaves (si le dernier etait deja identique) peuvent avoir la meme root.

**Fix** : utiliser une feuille de padding differente (ex: hash vide, ou prefixe de type) comme specifie dans la mitigation CVE-2012-2459.

**Validation** : `grep -n "level.append" scripts/local_git_guard.py`

---

### C4 — knowledge_os.py omet kimi dans DEFAULT_AGENTS

**Fichier** : `scripts/knowledge_os.py:17`
**Code** :
```python
DEFAULT_AGENTS = ("claude-opus", "claude-sonnet", "gpt-5.5")
```

**Constat** : Kimi est reviewer regulier depuis `CLAUDE.md §2` et `ONBOARDING_KIMI.md`. Pourtant le systeme de sync des reviews ne le decouvre pas par defaut.

**Impact** : les reviews deposees par Kimi dans `reviews/kimi/` ne sont pas synchronisees dans le rapport global et le digest a moins que `discover_agents()` ne tombe sur le repertoire existant. Si `reviews/kimi/` n'existe pas encore, Kimi est invisible.

**Fix** : ajouter `"kimi"` a `DEFAULT_AGENTS`.

---

### C5 — skill/bin/ est un repertoire vide

**Fichier** : `skill/bin/.gitkeep`

**Constat** : `ARCHITECTURE.md §3.1` et `skill/README.md` mentionnent `bin/` comme "utilitaires runtime futurs". Il est vide depuis le scaffolding P1.

**Impact** : stub non documente. Un utilisateur qui inspecte la skill voit un repertoire vide et se demande s'il manque quelque chose.

**Fix** : soit ajouter un README dans `bin/` expliquant qu'il est reserve Phase 2+, soit supprimer le repertoire et le recreer quand necessaire.

---

### M1 — mock_agent.py est un POC, pas un E2E

**Fichier** : `skill/tests/e2e/mock_agent.py`

**Constat** : Le fichier fait du substring matching deterministe (`"write_text(json.dumps" in text`). Il ne lit pas les checks, n'interprete pas les triggers, et ne simule pas un LLM.

**Impact** : Le handoff du 21 mai dit "P7 prouve le routing d'artefact via mock, pas la compliance live". C'est honnete, mais le fichier est nomme `mock_agent.py` et place dans `tests/e2e/`, ce qui suggere a tort qu'il s'agit d'un test E2E.

**Fix** : Renommer en `routing_harness.py` ou `artifact_loader_mock.py` pour eviter la confusion.

---

### M2 — Deux parsers frontmatter divergents

**Fichiers** :
- `scripts/skill-lib.ts:66-99` — parser YAML simpliste custom (pas de nested objects, pas de vrais types)
- `skill/tests/frontmatter_utils.py:30-45` — `yaml.safe_load` (vrai parser YAML)

**Constat** : Le parser TS ne gere pas les nested objects, les floats, les booleans, ou les multi-line strings. Le parser Python gere tout ca. Si un check ajoute un champ frontmatter complexe, le TS parser va produire une chaine brute au lieu de la structure attendue.

**Impact** : Risque de faux positifs/negatifs dans validate.ts. Ex: un champ `threshold: 0.5` devient la chaine `"0.5"` dans le parser TS, mais le nombre `0.5` dans le parser Python.

**Fix** : Utiliser un parser YAML robuste cote TS (ex: `js-yaml`) ou documenter explicitement que le frontmatter est limite au sous-ensemble supporte par `parseSimpleYaml`.

---

### M3 — local_git_guard.py sans tests

**Fichier** : `scripts/local_git_guard.py` (582 lignes)

**Constat** : Script critique qui gere des manifestes Merkle, des hooks git, des politiques de push, et des verifications d'integrite. Aucun test unitaire dans le repo.

**Impact** : Le bug C3 (Merkle duplicate-last) n'a pas ete detecte par les tests car il n'y en a pas. Toute regression dans ce script ne sera detectee qu'en production.

**Fix** : Ajouter `tests/test_local_git_guard.py` avec des tests sur `compute_merkle_root`, `walk_local_root`, `compare_payload`, et `verify_manifests`.

---

### M4 — Couplage fort gen-skill-docs.ts -> sync-catalog.ts

**Fichier** : `scripts/gen-skill-docs.ts:22-25`
**Code** :
```typescript
function ensureCatalog() {
  execFileSync(process.execPath, [join(ROOT, "scripts/sync-catalog.ts")], {
    cwd: ROOT,
    stdio: "inherit",
  });
}
```

**Constat** : Si `sync-catalog.ts` echoue (ex: C1 trigger), `gen-skill-docs.ts` crash avec une stack trace opaque. Pas de gestion d'erreur, pas de message utilisateur clair.

**Impact** : Experience developpeur degradee.

**Fix** : Wrapper dans un try/catch avec message explicite : "Catalog sync failed. Run `node scripts/sync-catalog.ts` manually to see the error."

---

### M5 — sync_reviews.py ne retourne pas 1 sur variant_notes

**Fichier** : `scripts/sync_reviews.py:570-572`
**Code** :
```python
if errors:
    return 1
return 0
```

**Constat** : Les `variant_notes` (conflits de synchronisation) et `warnings` ne declenchent pas un returncode 1. Un CI qui execute `sync_reviews.py` verdira meme si des conflits ont ete detectes.

**Impact** : Faux vert en CI. Des conflits de review peuvent passer inapercus.

**Fix** : `return 1 if (errors or variant_notes) else 0` ou ajouter un flag `--strict`.

---

### M6 — _normalize_value corrompt les dicts mono-cle

**Fichier** : `skill/tests/frontmatter_utils.py:15-27`
**Code** :
```python
if isinstance(item, dict) and len(item) == 1:
    key, scalar = next(iter(item.items()))
    normalized.append(f"{key}: {_render_scalar(scalar)}")
```

**Constat** : C'est un hack specifique au format `code_pattern: 'assert|expect'` des triggers. Si un frontmatter legitime contient un dict mono-cle (ex: `config: {timeout: 30}`), il sera transforme en chaine `"config: {'timeout': 30}"`.

**Impact** : Corruption silencieuse de donnees frontmatter. Difficile a debugger.

**Fix** : Normaliser seulement les items de listes connues comme `fires_on`, pas tous les dicts mono-cle.

---

### m1-m7 — Voir tableau synthetique ci-dessus

---

## 4. Convergence avec reviews precedentes

| Finding | Kimi 03 P8 | Opus 03 ecosysteme | GPT-5.5 15 interne | Statut post-durcissement 21 mai |
|---------|-----------|-------------------|-------------------|--------------------------------|
| Hardcoding 70 | M3 | L4 | Pretend corrige | **C1 — TOUJOURS PRESENT** |
| Parser frontmatter duplique | m1 | L8 | Corrige (frontmatter_utils.py) | **M2 — PARTIEL** (TS vs Python divergent) |
| E2E mock = routing | M1 | L1 | Documente | **M1 — ACCEPTE** mais mal nomme |
| Pas de host Kimi | m3 | L6 | Corrige | **C4 — PARTIEL** (host OK, mais invisible pour sync) |
| Francais sur hosts anglophones | m4 | L7 | Contrat anglais court | **m2 — PARTIEL** |
| Regex sans validation | m2 | L5 | Corrige | **CORRIGE** |
| skill/bin/ vide | — | L10 | Non traite | **C5 — NOUVEAU** |
| Merkle K6 dans local_git_guard | — | — | Non traite | **C3 — NOUVEAU, GRAVISSIME** |
| knowledge_os.py sans kimi | — | — | Non traite | **C4 — NOUVEAU** |
| local_git_guard sans tests | — | — | Non traite | **M3 — NOUVEAU** |

---

## 5. Verdict

| Categorie | Verdict |
|-----------|---------|
| Tests unitaires | Passent (36/36) |
| Validation statique | Passe |
| E2E mock | Passe (routing proof) |
| Coherence handoff/code | **C1 : handoff du 21 mai ment sur le hardcoding** |
| Securite cryptographique | **C3 : CVE-2012-2459 dans le repo** |
| Completeness | **C5 : stub vide, M3 : pas de tests local_git_guard** |
| Sync gouvernance | **C4 : kimi invisible pour knowledge_os** |
| Qualite code | M2, M4, M5, M6 |

**Verdict global** : **5 findings critiques bloquants pour `phase1-accepted`.** Le plus grave est C3 (le repo commet le bug qu'il pretend detecter). Le plus trompeur est C1 (le handoff du 21 mai declare un fix qui n'existe pas).

**Recommandation** :
1. Corriger C3 immediatement (Merkle duplicate-last).
2. Corriger C1 (supprimer le 70 hardcode).
3. Corriger C2 (deduire EXPECTED_FAMILIES ou documenter la friction).
4. Corriger C4 (ajouter kimi a DEFAULT_AGENTS).
5. Traiter C5 (documenter ou supprimer skill/bin/).
6. Re-lancer les 36 tests + validation + E2E apres corrections.
7. **Seulement apres ces 5 corrections**, le repo sera pret pour sign-off P8.

---

*Kimi — review systemique intransigeante, swarm mode, 2026-05-21*
