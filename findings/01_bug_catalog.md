# Catalogue des erreurs de coding récurrentes des LLM

**Source** : reviews/handoffs/corrections produits par Claude Sonnet 4.6, Claude Opus 4.7, ChatGPT, Codex, Kimi, Gemini, GPT-5.5 dans trois repos :
- `/home/zack/GROK-CLI/forensic-evidence-20260327/` (3 653 .md)
- `/home/zack/Documents/Depollution_Sols /` (668 .md, attention espace de fin)
- `/home/zack/Documents/Notebook_LLM_Tana/` (439 .md)

**Méthode** : échantillonnage haut-signal — lecture intégrale des fichiers signés LLM à la racine, des `reviews/active/<agent>/{proposition,corrections}/` les plus chargés en findings, des `team_review_*` et `global_handoff/*` de Notebook. Les ~4 760 fichiers n'ont pas été lus exhaustivement ; les patterns ci-dessous représentent les concentrations les plus denses observées sur l'échantillon.

**Frequencies notation** :
- 🔴 **TRÈS HAUTE** (5+ occurrences distinctes documentées + pattern systémique reconnu)
- 🟠 **HAUTE** (3-5 occurrences ou identifié comme systémique)
- 🟡 **MOYENNE** (1-3 occurrences mais clair)
- ⚪ **FAIBLE** (1 occurrence isolée mais utile)

---

## TOP 10 patterns par fréquence (résumé exécutif)

| Rang | Pattern | Fréq | Familles concernées |
|------|---------|------|---------------------|
| 1 | **Écritures non-atomiques sur fichiers d'état** | 🔴 | Python, Bash, JSON state |
| 2 | **Cascade silencieuse : `main()` retourne 0 sur échec interne** | 🔴 | Python orchestration |
| 3 | **Hallucination de code : citer fichier:ligne qui n'existe pas, ou refixer un bug déjà corrigé** | 🔴 | Reviews multi-LLM |
| 4 | **"Latest" qui est en fait "First" + slicing fixe sans bornes** | 🔴 | Sémantique d'itération |
| 5 | **Pas de `try/except` par item dans une scan-loop : un fichier corrompu kill toute la boucle** | 🟠 | Python scans |
| 6 | **Substring matching sans word-boundary → faux positifs** | 🟠 | Classifieurs textuels |
| 7 | **Override silencieux d'un input explicite utilisateur** | 🟠 | Logique métier, sécurité |
| 8 | **Race conditions sur IDs basés sur timestamp à la seconde** | 🟠 | Multi-process file I/O |
| 9 | **Filtrage shell incomplet (manque `>`, `<`, `>>`)** | 🟠 | Sandbox/sécurité |
| 10 | **Tests qui ne couvrent qu'une branche d'un comportement bidirectionnel** | 🟠 | Test coverage |

---

## A. Atomicité et crash-safety 🔴 TRÈS HAUTE

Pattern systémique **explicitement nommé "contradiction architecturale"** par Sonnet 4.6 (Depollution & forensic).

### A1. Écritures non-atomiques sur fichiers d'état
- **Description** : `path.write_text(json.dumps(...))` direct sur des fichiers de confiance (latest.json, index.json, catalog, manifest). Si le process est interrompu (crash, kill -9, signal, plein disque), le fichier reste tronqué ou pointe vers un run inexistant.
- **Commis par** : Codex (implémentation initiale), corrigé/identifié par Sonnet & Kimi
- **Identifié par** : Claude Sonnet 4.6 (forensic D2/E2/G2/G3) ; Kimi (forensic C2)
- **Occurrences** : 8+ writes recensés rien que dans 5 modules de forensic-evidence (`repo_tamper_proof.py`, `forensic_doc_archive.py`, `repo_anchor_runtime.py`, `repo_timeline_runtime.py`)
- **Fichier exemple** : `reviews/active/claude-sonnet/proposition/63-deep-code-review-sync-app-20260424.md:69-87`
- **Fix** : `tmp_path.write_text(...) ; tmp_path.replace(path)` — atomique sur POSIX

### A2. JSON corrompu silencieusement remplacé par état vide
- **Description** : `try: load_index() except json.JSONDecodeError: return empty_index()` — corruption silencieuse, perte totale des records antérieurs au prochain run.
- **Commis par** : Codex
- **Identifié par** : Sonnet 4.6
- **Fichier** : `repo_anchor_runtime.py:159` cité dans `63-deep-code-review-sync-app-20260424.md:357-360`

### A3. Pas de hash chain immuable — timeline réécrite à chaque run
- **Description** : `events.ndjson` réécrit complètement à chaque sync. La hash chain perd sa propriété d'immuabilité. `chattr +a` impossible.
- **Identifié par** : Sonnet 4.6 (F2 doc 63)

---

## B. Propagation d'erreur défaillante / cascade masquée 🔴 TRÈS HAUTE

### B1. `main()` retourne 0 même quand une étape interne plante
- **Description** : enchaînement `archive → anchor → timeline → inspector` ; si `build_tamper_proof()` lève, la fonction n'attrape pas, mais `main()` finit avec `return 0`. Le pipeline aval croit succès et continue sur preuve non-régénérée.
- **Commis par** : Codex
- **Identifié par** : Kimi (C1, doc `BUGS_AND_GAPS.md`) ET Sonnet 4.6 (E1, doc 63) — convergence inter-LLM
- **Fichier** : `forensic_doc_archive.py:670` ; `forensic_review_sync.py`

### B2. `subprocess.run` sans `try/except CalledProcessError`
- **Description** : `make briefing` échoue → `CalledProcessError` non gérée → crash brut au lieu de message utilisateur.
- **Commis par** : Gemini (implémentation `morning.py`)
- **Identifié par** : Kimi (`review_implementations_specs_0006_0007.md`, F4)
- **Fichier** : `Notebook_LLM_Tana/scripts/morning.py`

### B3. `save_document()` sans `try/except OSError`
- **Description** : disque plein ou permissions → exception Python brute remontée à l'utilisateur final.
- **Identifié par** : Kimi sur impl Gemini, corrigé par Claude (C3, `2026-04-19__corrections_specs_0006_0007.md`)

---

## C. Crash sur item unique tue toute la boucle 🟠 HAUTE

### C1. Pas de `try/except` par fichier dans une scan-loop
- **Description** : `scan_archive()` itère sur tous les fichiers ; si un seul `.md` a un YAML malformé, `yaml.safe_load` lève et **tous les fichiers suivants alphabétiquement ne sont pas catalogués**. Un attaquant qui peut écrire un `.md` corrompu désactive l'archivage.
- **Commis par** : Codex
- **Identifié par** : Sonnet 4.6 (E3, doc 63)
- **Fichier** : `forensic_doc_archive.py:317-320`

### C2. `load_review_documents` inclut README.md → exit 1 permanent
- **Description** : un `README.md` dans `review/{agent}/proposition/` n'a pas de frontmatter conforme, le scan retourne exit 1 en boucle.
- **Commis par** : auteur initial du sync
- **Identifié et fixé par** : Claude (Depollution, repris dans Notebook via global_handoff)

---

## D. Erreurs sémantiques d'itération 🔴 TRÈS HAUTE

### D1. "latest" qui est en fait "first"
- **Description** : `latest_by_kind` itère sur events triés ASC et insère seulement si la clé n'est pas présente → garde le **premier** événement, pas le dernier. Tout CLI consommateur croit voir le dernier run mais voit le premier.
- **Commis par** : Codex
- **Identifié par** : Sonnet 4.6 (F1, doc 63)
- **Fix** : `for event in reversed(events)` ou overwrite à chaque tour

### D2. Slicing fixe `[1:6]`, `[2:7]` sans bornes ni structure
- **Description** : parser des sections markdown par index numérique ; si la structure change ou la section a moins de lignes, `IndexError` ou affichage tronqué.
- **Commis par** : Gemini (`morning.py`)
- **Identifié par** : Kimi (F3, F5)
- **Corrigé par** : Claude (Notebook `corrections_specs_0006_0007`, C5)

### D3. Tri par date seul → ordre instable change le verdict
- **Description** : `sort by date` puis `aggregation_mode='latest'` prend le dernier en ordre d'apparition. Deux mesures du même jour peuvent flipper `compliant ↔ exceeds_threshold` selon l'ordre de lecture du CSV.
- **Commis par** : auteur du moteur statistique
- **Identifié par** : GPT-5.5 (`03_2026-05-02_full_app_dual_skill_ultrareview_findings.md`, finding #5)

### D4. `side=lower` calculé avec le même signe que `upper`
- **Description** : prediction limit lower/upper avec `+ k_factor * std` dans les deux branches ; le k_factor négatif annule en partie mais donne **lower = upper**. Test ne couvrait que upper.
- **Commis par** : auteur initial
- **Identifié et fixé par** : Claude (`Depollution_Sols /review/claude/corrections/01_2026-04-25_prediction_limit_lower_side_bug.md`)
- **Leçon** : test seulement upper → bug lower silent. **Toujours tester les deux directions des comportements bidirectionnels.**

### D5. `first-rule-wins` sans documentation de l'ordre
- **Description** : `classify_analyte` itère `_FAMILY_RULES` et retourne la première famille qui matche. L'ordre du fichier devient load-bearing sans indication. Signal `multi_match`/`ambiguous` jamais émis.
- **Identifié par** : Opus 4.7 via sub-agent engineering (F5, doc 05)

---

## E. Hallucination LLM-spécifique 🔴 TRÈS HAUTE

Pattern **propre aux LLM dans le rôle de reviewer**. Documenté explicitement par Opus 4.7 dans son auto-amendement.

### E1. Citer code à un fichier:ligne qui n'existe pas
- **Description** : T15 dans `corrections/04` cite un bloc `for method in METHOD_CATALOG: method.status = ...` à `catalog.py:358-362`. Vérification : ce bloc n'existe pas. L'alignement est fait par inlining direct (23 occurrences de `status="available_initial"`).
- **Commis par** : Opus 4.7 (sub-agent ou passe précédente)
- **Identifié par** : Opus 4.7 lui-même via reproduction Python (`05_2026-05-02_consolidated_peer_review_phases_49_50.md`)
- **Fix process** : *"Aucun finding n'est repris sans vérification indépendante."*

### E2. Refixer un bug déjà corrigé
- **Description** : T14 (corrections/04) propose une boucle exhaustive pour vérifier `status == implementation_status` ; cette boucle existe déjà dans `tests/test_api.py:168-170`. T12 (corrections/03) propose de typer `PipelineMaturity` en Enum ; déjà fait à `api/schemas.py:84-87`.
- **Commis par** : Opus 4.7
- **Identifié par** : Opus 4.7 lui-même + 2 sub-agents (peer review)

### E3. Reproduction example qui ne reproduit pas
- **Description** : T16 listait `HVAC sample monitoring`, `barbiturate background`, `trace metal background` comme exemples du substring-matching bug ; aucun ne reproduit. Les vrais cas reproductibles sont `EVCO-1`, `ATCE-Lab`, `DCAtl`.
- **Commis par** : Opus 4.7
- **Identifié par** : Opus 4.7 lui-même via exécution Python directe

### E4. Imports opaques cachant la dépendance
- **Description** : `shutil_move = __import__("shutil").move` au lieu de `import shutil`. Pattern fragile, opaque, et signe d'un LLM qui réinvente.
- **Commis par** : auteur initial (Claude probable)
- **Identifié et fixé par** : Claude (Depollution → Notebook)

---

## F. Race conditions et concurrence 🟠 HAUTE

### F1. ID basé sur timestamp à la seconde + même payload
- **Description** : `anchor_id = "{compact_timestamp()}__{backend}__{root[:16]}"` — granularité 1s. Deux processus dans la même seconde avec même Merkle root → même `anchor_id` → écriture concurrente écrase le record du second, l'index pointe vers l'un, l'autre est perdu.
- **Commis par** : Codex
- **Identifié par** : Kimi (C3) ET Sonnet 4.6 (G1)
- **Fix** : `compact_timestamp() + secrets.token_hex(4)`

### F2. Singleton module-level avec multi-worker uvicorn
- **Description** : `dataset_store = InMemoryDatasetStore()` au top-level. Chaque worker uvicorn a son propre store ; un dataset ingéré dans un worker invisible aux autres. Tests impossibles sans partager le state global.
- **Identifié par** : Claude (`Depollution_Sols /review/claude/corrections/01_2026-04-19_code_corrections.md`, C3)
- **Fix** : FastAPI `Depends(get_store)` + `app.dependency_overrides` en test

### F3. Pas de `flock` / fd 200 non fermé avant fork
- **Description** : `flock` sur fd 200 ; si on fork un enfant sans fermer fd 200 avec `200>&-`, l'enfant hérite du verrou.
- **Documenté dans** : `forensic-evidence-20260327/CLAUDE.md:198-209` (règles absolues)

---

## G. Filtrage / contrôle d'entrée incomplet 🟠 HAUTE

### G1. Tokens shell de contrôle incomplets
- **Description** : `SHELL_CONTROL_TOKENS = ("&&", "||", ";", "|", "$(", "`")` — manque `>`, `>>`, `<`, `>&`. Permet `bash -lc "cat /etc/shadow > /tmp/exfil"` de passer le filtre.
- **Commis par** : Codex
- **Identifié par** : Sonnet 4.6 (H1, doc 63)

### G2. Substring matching sans word-boundary
- **Description** : `term in haystack` sur termes courts (≤3 chars) → `EVCO-1` matche `vc`, `ATCE-Lab` matche `tce`, `DCAtl` matche `dca`.
- **Identifié par** : Opus 4.7 + sub-agents (F4, doc 05)
- **Fix** : `\b` regex pour termes courts, substring pour les longs

### G3. Whitelist de shells incomplète
- **Description** : `extract_shell_payload` reconnaît seulement `bash -c|-lc|-ic|-l|-i`. `dash`, `ksh`, `fish`, `bash --` non reconnus → retourne `None` → filtre désactivé pour ces shells.
- **Identifié par** : Sonnet 4.6 (H3, doc 63)

### G4. Sandbox dégradée à `none` exécute quand même
- **Description** : si `systemd-run` ET `bwrap` sont indisponibles, `selection.selected = "none"`. La commande **est exécutée sans sandbox** ; la politique `network=deny` n'est pas appliquée. Loggé mais permis.
- **Identifié par** : Sonnet 4.6 (H2, doc 63)
- **Fix** : refuser si `policy.network.default == "deny"` et `selected == "none"`

---

## H. Override silencieux de l'intent utilisateur 🟠 HAUTE

### H1. Auto-bascule heavy_metal écrase `catalog_id` explicite
- **Description** : Client envoie `catalog_id=wallonia_decret_sols_annexe1_2018, usage_code=III` (compliance fixe). Code détecte `family=heavy_metal` et bascule en `prediction_limit` (background-vs-future), pop `catalog_id`/`usage_code`/`threshold_value`. **Faux négatif réglementaire silencieux.**
- **Identifié par** : Opus 4.7 (F1, P0) ET GPT-5.5 (finding #1) — convergence inter-LLM
- **Sévérité** : "régulatoirement faux", pas seulement surprenant

### H2. Filtre pré-comparaison masque les suppressions
- **Description** : `RETIRED_ARCHIVE_PREFIXES = ("chatgpt_review/", "kimi-review/")` filtre les entrées **avant** la comparaison current/previous. Un fichier sous ces préfixes qui disparaît n'est jamais détecté comme manquant.
- **Identifié par** : Sonnet 4.6 (E4, doc 63)

### H3. Drop silencieux au-delà de `MAX_INDEX_RECORDS=200`
- **Description** : records 201+ supprimés de l'index sans log, sans signal. Les `.json` persistent en disque mais inaccessibles via l'API normale.
- **Identifié par** : Sonnet 4.6 (G4, doc 63)

### H4. Spec liste 4 actions, implémentation en propose 3
- **Description** : spec-2026-0007 liste `[link, archive, redistill, skip]` ; menu Gemini propose `[l, a, s]`. `redistill` manquant.
- **Commis par** : Gemini
- **Identifié par** : Kimi (`review_implementations_specs_0006_0007.md`)

---

## I. Destruction de données / opérations irréversibles 🟠 HAUTE

### I1. `shutil.move` au lieu de `shutil.copy2`
- **Description** : `promote_document` déplace au lieu de copier → la source dans `review/{agent}/proposition/` est définitivement perdue.
- **Commis par** : Claude initial
- **Identifié et fixé par** : Claude (Depollution puis Notebook via handoff)
- **Fichier** : `Notebook_LLM_Tana/review/claude/corrections/2026-04-19__corrections_sync_reviews_knowledge_os.md` (C1)
- **Fix** : `copy2` + champ `promoted_to:` dans frontmatter pour traçabilité

### I2. Overwrite silencieux de `dataset_id`
- **Description** : `dataset_id` choisi par client ; deux POST avec même ID écrasent sans warning. Plans déjà construits pointent vers une ancienne révision invisible.
- **Identifié par** : GPT-5.5 (finding #4)
- **Fix proposé** : snapshot hash + revision count

---

## J. Couverture de tests insuffisante 🔴 TRÈS HAUTE

### J1. Aucun répertoire `tests/`
- **Identifié par** : Claude (`Depollution_Sols /review/claude/corrections/01_2026-04-19_code_corrections.md`, C8)

### J2. Test couvre une seule direction d'un comportement bidirectionnel
- **Description** : `prediction_limit_single` testé pour `side="upper"` exclusivement. Le bug `side="lower"` est silencieux pendant des semaines.
- **Identifié par** : Claude lui-même rétrospectivement
- **Leçon** : *"Ajouter systématiquement les deux directions dans les tests de méthodes bidirectionnelles."*

### J3. Test paramètres incorrects passent par accident
- **Description** : test du seuil ND fraction visait 50% mais data utilisée est à 44% → assertion `passed=False` était fausse, le test passait.
- **Identifié par** : Opus 4.7 (F3, doc 05)

### J4. Tests passent en mockant ce qu'ils devraient tester
- **Documenté en doctrine** : `forensic-evidence-20260327/CLAUDE.md` & `internal/CONTEXT.md` Knowledge OS

---

## K. Architecture / layering smells dans code généré par LLM 🟠 HAUTE

### K1. Fichier monolithique massif
- **Description** : `methods/executors.py` à 2446 lignes contenant 11 exécuteurs + tous les helpers stats (student-t, KM, kendall) en bloc.
- **Identifié par** : Claude (Depollution C1)
- **Fix** : découpe par famille (`diagnostics.py`, `nd.py`, `trend.py`, etc.)

### K2. Code dupliqué littéralement N fois
- **Description** : `DatasetSummary(...)` construit 3 fois identiquement dans `main.py`. `_normalize_string_list` dupliqué de `_coerce_str_list` caractère pour caractère.
- **Identifié par** : Claude (C2) ET Kimi (proposition 08, P2)

### K3. Side-effect dans fonction au nom pur
- **Description** : `update_index()` fait un I/O disque (`load_backend_state`). Le caller s'attend à une transformation mémoire pure.
- **Identifié par** : Sonnet 4.6 (G5, doc 63)

### K4. Planning function fait aussi de l'execution
- **Description** : `build_adaptive_analysis_plan_from_template` exécute un step `data_profile` synchrone pendant le build. Couples planning et execution.
- **Identifié par** : Opus 4.7 (F10, doc 05)

### K5. `dict[str, Any]` non typé dans contrat API public
- **Description** : `metadata: dict = Field(default_factory=dict)` exposé au client → renames silencieux, pas de validation Pydantic, pas de schema OpenAPI.
- **Identifié par** : Opus 4.7 sub-agent engineering (F8, doc 05)
- **Fix** : modèles Pydantic dédiés `AdaptiveBuildMetadata`, `AnalyteContext`

### K6. Doublon Bitcoin dans Merkle tree (CVE-2012-2459 pattern)
- **Description** : `if len(hashes) % 2: hashes.append(hashes[-1])` — vulnérabilité connue.
- **Identifié par** : Sonnet 4.6 (D4, doc 63)

---

## L. Erreurs Bash spécifiques 🟠 HAUTE

Recensées dans la section *"Bugs résolus (ne pas réintroduire)"* de `forensic-evidence-20260327/CLAUDE.md` — c'est une liste **historique** des bugs déjà commis ET résolus, conservée pour ne pas les refaire.

| # | Bug | Cause | Fix |
|---|-----|-------|-----|
| L1 | Crash silencieux sur `grep` | `set -euo pipefail` + `grep` retournant exit 1 | `{ grep -c ... \|\| true; }` |
| L2 | `local` hors fonction | Crash bash | Variables simples dans le while |
| L3 | Guardian parsait 3 champs IFS | Variables manquantes | 4 champs (name\|script\|args\|needs_sudo) |
| L4 | Double sudo sans TTY | `sudo` à l'intérieur d'un script lancé avec sudo | Vérifier `id -u` au début |
| L5 | `notify-send` plante sans DBus | Pas de session graphique | `2>/dev/null \|\| true` |
| L6 | `resolvectl monitor` déclenche polkit | Popup auth | Ne JAMAIS l'utiliser |
| L7 | `ss -tnp` ne montre pas TIME_WAIT | Filtre par défaut | `ss -tanp` (mais perd PID) |
| L8 | Trust `ss` seul | Binaire user-space hookable | Cross-check `/proc/net/tcp` |
| L9 | `declare -A` dans subshell pipe | Variables perdues | Hors subshell |
| L10 | fd 200 non fermé avant fork | Enfant hérite du flock | `200>&-` avant exec |

---

## M. Persistance / drift detection manquante 🟡 MOYENNE

### M1. Pas de service systemd pour redémarrage post-reboot
- **Identifié par** : Kimi (`BUGS_AND_GAPS.md` C1)

### M2. Catalog réécrit complètement → historique effacé
- **Description** : `team_review_latest.md` ne garde que le snapshot courant. Si une proposition disparaît entre deux syncs, aucune trace.
- **Identifié et fixé par** : Claude (handoff Depollution → Notebook : ajout `team_review_changelog.md` append-only + `write_catalog` retournant `list[str]` des dérives)

### M3. Pas de hash chain pour détecter modifications de documents
- **Identifié et fixé par** : Claude — ajout `file_digest()` SHA-256 tronqué à 12 chars dans le catalog

### M4. Baseline DB cohérence non vérifiée
- **Description** : guard partiel vérifie présence d'une `domain_state` row, mais pas que les `repo_files` correspondants existent. Une DB corrompue (rows deleted, state row preserved) pouvait reuse une baseline incohérente sans alarme.
- **Identifié et fixé par** : Codex (`100-repo-files-reused-baseline-consistency-20260501.md`)

---

## N. Validation d'inputs manquante 🟡 MOYENNE

### N1. Pas de vérification d'existence d'un ID utilisateur
- **Description** : `target_id = input("ID cible > ")` puis `save_document` sans vérifier que `target_id` existe dans le catalogue. Lien fantôme créé.
- **Identifié par** : Kimi (F6 sur Gemini)
- **Fixé par** : Claude (C2 corrections)

### N2. Coercition de paramètres incohérente
- **Description** : `ParameterCoercionError` pour les dates, mais `float(...)` brut pour les numériques → `ValueError` raw remonte au client.
- **Identifié par** : GPT-5.5 (finding #8)

### N3. `point_metadata` client traité comme autoritaire
- **Description** : un `role: "upgradient"` venu du client persiste tel quel et drive l'auto-bascule compliance.
- **Identifié par** : GPT-5.5 (finding #7)

---

## O. Erreurs intrusives / non-portables 🟡 MOYENNE

### O1. `os.system('clear')` dans script TUI
- **Description** : séquences d'échappement polluent une sortie redirigée ; effets de bord variables selon le terminal.
- **Commis par** : Gemini
- **Identifié par** : Kimi (F2)
- **Fix appliqué** : `print("\n" * 50)` (Claude C6)

### O2. `sys.path` pointant sur ROOT au lieu de `ROOT / "scripts"`
- **Description** : import fonctionne par effet de bord (cwd du script) mais comportement implicite et fragile.
- **Commis par** : Gemini
- **Identifié et fixé par** : Claude (C4, C8)

---

## P. Conventions/contracts incohérents 🟡 MOYENNE

### P1. Statuts incohérents catalogue vs documentation
- **Description** : `documentation.py` dit `available_initial`, `catalog.py` dit `available`. L'API expose le second, le frontend ne voit jamais la nuance EPA-auditée vs V1-non-auditée.
- **Identifié par** : Kimi (proposition 08 P1)

### P2. Élément dupliqué dans liste exposée au client
- **Description** : `matched_terms = ['benzene', 'benzene']` parce que `"benzene"` apparaît deux fois dans la term-list interne.
- **Identifié par** : Opus 4.7 sub-agent (F9)
- **Fix** : `assert len(rule["terms"]) == len(set(rule["terms"]))` au load module

### P3. Schema `PlanResult` perd les métadonnées du plan
- **Description** : `AnalysisPlan` a `label`, `analyte_id`, `metadata` ; `PlanResult` n'a que `step_results`. Métadonnées `adaptive_build`, `compliance_mode`, `pipeline_id` invisibles au client final.
- **Identifié par** : Kimi (proposition 08 P4)

### P4. Trônage YAML silencieux sur multi-fichier
- **Description** : 3 YAML mergés (`repo.spec`, `workspace.spec`, `user-space.spec`) avec priorité implicite ; si `workspace.spec.yaml` absent, aucune alerte.
- **Identifié par** : Sonnet 4.6 (H4)

---

## Q. Précision numérique / convention statistique non documentée ⚪ FAIBLE-MOYENNE

### Q1. `_student_t_cdf` plafonne à t=12 retournant 1.0
- **Description** : pour `dof=1` (Cauchy), `P(T ≤ 12) ≈ 0.974`, pas 1.0.
- **Identifié par** : Claude (C6)

### Q2. KM `cdf_estimate` left-continuous, quantile décalé d'un cran
- **Identifié par** : Claude (C7)

### Q3. Merkle leaves sur `digest[:12]` (48 bits) alors que la spec annonce SHA256
- **Identifié par** : Sonnet 4.6 (D3)

### Q4. ND fraction guard absent dans `background_characterization`
- **Description** : 44% NDs + 5 detects → status `ok`, mean/std calculés sur detects seuls, prédiction limit biaisée. Aucun warning.
- **Identifié par** : Opus 4.7 sub-agent methodology (F3)

### Q5. Trend seasonal ok sur série 4 obs / 2 saisons
- **Description** : screening output présenté comme defensible alors que data trop sparse.
- **Identifié par** : GPT-5.5 (finding #6)

---

## R. Audit trail perdu lors de transformations 🟡 MOYENNE

### R1. Auto-bascule pop les paramètres originaux sans les conserver
- **Description** : pop `threshold_value`/`catalog_id`/`usage_code` ; reviewer ne peut pas reconstruire la demande originale.
- **Identifié par** : Opus 4.7 (F7, doc 05)
- **Fix** : conserver dans `evidence.discarded_threshold_parameters`

### R2. Timestamp fallback `1970-01-01` crée faux "premiers événements"
- **Description** : events sans timestamp valide placés en tête du tri ; `sequence_number=1` peut être un event corrompu.
- **Identifié par** : Sonnet 4.6 (F3, doc 63)

---

## Observations transverses sur les LLM

### Profils observés (sur cet échantillon)

| LLM | Force observée | Faiblesse observée |
|-----|----------------|---------------------|
| **Claude Sonnet 4.6** | Lecture statique ligne-par-ligne ultra-précise. 18 findings dans 5 modules (doc 63) avec patches concrets. Repère les défauts d'implémentation. | Peut manquer les invariants systémiques de haut niveau (Kimi C1 cascade visible code mais non identifiée comme garantie manquante) |
| **Claude Opus 4.7** | **Rôle d'orchestrateur qui se vérifie lui-même** : reproduit chaque finding en Python avant de le valider, ferme ses propres tickets invalides (T14, T15, T12). Premier LLM observé à documenter explicitement *"Aucun finding n'est repris sans vérification indépendante."* | Sans vérification, hallucine code:line + propose fixes pour code déjà corrigé. Sub-agents methodology/engineering ont produit findings de qualité variable (F3 mal calibré, exemples non-reproductibles) — l'orchestrateur les a recadrés. |
| **Kimi** | Vues systémiques, contrats, invariants. Identifie les garanties manquantes (cascade C1 avant que Sonnet ne lise le code). Tableaux de synthèse comparatifs. | Plus high-level, peut manquer les défauts d'implémentation ligne-par-ligne. |
| **ChatGPT** | Rôle d'implémenteur Python/Bash dans forensic. PR handoff. | Peu de surface review observée dans l'échantillon. |
| **Codex** | Implémentation MVP propre — réutilise `atomic_write` quand il existe, atomic_writes, type hints, conventions. Discipline de note (proposition `100`, `102`). | Initial pass : `dict[str, object]` non-typé, schema MVP minimal sans tests dédiés (Phase B), TUI non implémenté. |
| **Gemini** | Implémentation rapide de specs (`morning.py`, `close_loops.py`). | Ratés répétés : `os.system('clear')`, slicing fixe, pas de gestion d'erreur subprocess, action `redistill` manquante par rapport à la spec, `sys.path` mal pointé. **Pattern : optimise vitesse au détriment de la robustesse.** |
| **GPT-5.5** | Ultrareview full-app dual-skill (engineering + domain expert). Trouve les bugs à impact métier (units ignorés, dataset_id mutable, role-tag client autoritaire). | Pas observé en mode implémentation. |

### Patterns LLM-spécifiques (vs bugs "humains")

1. **Hallucination de citations code** (E1, E3) — symptôme propre aux reviewers LLM travaillant de mémoire ; absent quand le LLM lit + reproduit avant de conclure.
2. **Refixer un bug déjà corrigé** (E2) — symptôme de session sans contexte du repo état actuel.
3. **Reuse silencieux de code dupliqué littéralement** (K2) — quand un LLM ré-écrit au lieu d'importer parce qu'il "ne voit pas" l'helper existant.
4. **Override silencieux d'inputs explicites** (H1, H2) — LLM optimise pour le "happy path" qu'il a vu, écrase les cas d'override sans warning.
5. **`first-rule-wins` sans documentation de l'ordre** (D5) — LLM produit du code "load-bearing implicit" : l'ordre du fichier devient une API non-documentée.

### Convergences inter-LLM (signal de qualité épistémique)

Quand 2+ LLM trouvent indépendamment le même bug, le signal est très fort :
- **Cascade failure / `main()` returns 0** — Kimi (C1) + Sonnet (E1)
- **Race condition anchor_id** — Kimi (C3) + Sonnet (G1)
- **Auto-bascule heavy_metal regulatoire** — Opus 4.7 sub-agents methodo + engineering + GPT-5.5

### Divergences

- Sévérité : Opus 4.7 sub-agent classait F3 (ND fraction) en HIGH avec un scenario qui en réalité tombait en `failed_preconditions` ; orchestrateur recadre P1 avec un vrai scenario silencieux à 44% NDs.
- Position pratique : Kimi conseillait *"préservation preuves d'abord, cut-off ensuite"* vs Opus 4.7 *"cut-off urgent d'abord"*.

### LLM représentés / sous-représentés

- **Très présents** : Claude (Sonnet + Opus), Kimi, Codex, ChatGPT
- **Moyennement présents** : GPT-5.5, Gemini (souvent en cible de review, peu en reviewer)
- **Absents/marginaux dans l'échantillon** : Grok, Mistral, modèles open-source — pas de notes signées trouvées

---

## Implications pour la skill de coding

Ces patterns donnent une base de **règles préventives** pour la skill :

### Règles "always"
1. Tout `write_text` sur fichier d'état → `tmp+rename`
2. Tout `subprocess.run` → `try/except CalledProcessError`
3. Tout scan-loop → `try/except` par item, pas pour la boucle entière
4. Tout test bidirectionnel → couverture des deux directions
5. Tout ID basé sur timestamp → ajouter `secrets.token_hex(N)`
6. Tout filtre shell → inclure `>`, `>>`, `<`, `>&` + whitelist shells explicite
7. Tout substring matching sur termes ≤3 chars → word-boundary regex
8. Toute fonction nommée pure → pas d'I/O disque
9. Tout dict de contrat API → modèle Pydantic typé
10. Tout `shutil.move` sur fichier source → suspecté ; préférer `copy2` + flag `promoted_to`

### Règles "never"
1. Ne jamais retourner 0 dans `main()` sans avoir capturé toutes les exceptions des steps internes
2. Ne jamais filtrer des entrées **avant** une comparaison de drift
3. Ne jamais drop silencieusement au-delà d'une limite
4. Ne jamais override un input utilisateur explicite sans warning + entry dans un audit trail
5. Ne jamais croire que `latest_by_kind` se nomme correctement — vérifier l'itération
6. Ne jamais citer un fichier:ligne sans avoir lu le fichier dans la session courante
7. Ne jamais re-proposer un fix sans avoir grep le code pour la solution actuelle
8. Ne jamais utiliser `os.system('clear')` — `print("\n"*N)` ou rien
9. Ne jamais utiliser `__import__("module").attr` — préférer `import module`
10. Ne jamais set `set -euo pipefail` sans `|| true` après chaque `grep`

### Process meta-règles (apprises d'Opus 4.7)
1. Reviewer : reproduire chaque finding (script Python ou commande) avant de le valider
2. Reviewer : grep le code pour le pattern proposé avant de proposer un fix
3. Reviewer : lire le fichier:ligne cité avant d'écrire le ticket
4. Implementer : `py_compile` + `unittest discover` sur le scope changé avant handoff
5. Tout ticket cite : artifact reviewé, verdict, validation effectuée, next step
6. Convergence inter-LLM = signal fort ; divergence = signal d'épistémologie à creuser

---

*Document produit le 2026-05-03 par lecture haut-signal des trois repos. Échantillon non-exhaustif. À enrichir au fur et à mesure de l'extension de la skill.*
