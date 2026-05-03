# Méthodologie de travail multi-LLM — règles distillées des observations

Ce document distille les **méta-règles de processus** observées dans les trois repos sources (forensic-evidence, Depollution_Sols, Notebook_LLM_Tana) qui distinguent le travail multi-LLM productif du travail multi-LLM bruyant. Elles s'appliquent à **toute session** de coding/review dans ce projet.

---

## 1. La règle d'Opus 4.7 — vérifier avant de réclamer

Source : `Depollution_Sols/review/opus4.7/corrections/05_2026-05-02_consolidated_peer_review_phases_49_50.md`

> *"Aucun finding n'est repris sans vérification indépendante."*

### Application concrète

Avant de citer un `file:line` dans un ticket, une review, ou un commentaire :
1. **Lire le fichier** dans la session courante (pas de mémoire d'une session antérieure)
2. **Reproduire** : si c'est un bug comportemental, exécuter un script Python/shell qui le déclenche
3. **Citer la sortie réelle**, pas une sortie inférée

### Exemples de violations observées (à NE PAS reproduire)

- **T15 (Opus 4.7 lui-même)** a cité un bloc de code à `catalog.py:358-362` qui n'existait pas. Reproduit puis fermé après vérification.
- **T14 (Opus 4.7 lui-même)** a proposé une boucle de test qui était déjà présente à `tests/test_api.py:168-170`. Fermé.
- **T16 (Opus 4.7 lui-même)** listait des exemples (`HVAC sample monitoring`) qui ne reproduisaient pas le bug. Remplacés par les vrais cas reproductibles (`EVCO-1`, `ATCE-Lab`, `DCAtl`).

**Coût économisé par la règle** : 3 tickets invalides évités, ~30k tokens orchestrateur pour la vérification, mais évite des PRs qui auraient été rejetées.

---

## 2. Les 4 métriques qu'un ticket doit avoir

Source : `forensic-evidence-20260327/reviews/active/codex/proposition/102-gpt55-review-note-discipline-and-code-review-skill-20260502.md`

Tout ticket de review substantiel inclut :

1. **Reviewed artifact or scope** — quel fichier, quelle PR, quelle phase
2. **Verdict** — approve / fix-needed / reject avec justification
3. **Findings ou non-findings** — liste explicite, y compris "rien à signaler sur X"
4. **Validation performed** — commande exacte, résultat (`168 tests OK`)
5. **Next recommended step**

Les "small conversational checks" n'ont pas besoin de note. Mais tout ce qui touche **architecture, roadmap, code quality, safety, runtime behavior, sync/document governance** doit produire une note durable.

---

## 3. Convergence inter-LLM = signal fort, divergence = épistémologie

Source : `forensic-evidence-20260327/reviews/active/kimi/proposition/66-synthese-comparative-findings-20260424.md`

### Convergences observées

Quand 2+ LLM trouvent indépendamment le même bug :
- **Cascade failure** — Kimi C1 + Sonnet E1
- **Race condition anchor_id** — Kimi C3 + Sonnet G1
- **Auto-bascule heavy_metal régulatoire** — Opus 4.7 sub-agents methodo + engineering + GPT-5.5

→ **Signal très fort**. Priorité P0/P1 confirmée.

### Divergences observées

- Sévérité de F3 (ND fraction) : sub-agent en HIGH sur scenario qui en réalité tombait en `failed_preconditions`. Orchestrateur recadre en P1 avec scenario silencieux à 44% NDs.
- Position pratique sur cut-off : Kimi *"préservation preuves d'abord"* vs Opus 4.7 *"cut-off urgent"*.

→ **Signal d'épistémologie à creuser**. Documenter les deux positions, laisser l'humain trancher.

### Règle d'application

- **Reviewer (moi)** : flag les convergences en P0 ; flag les divergences en "à arbitrer" ; ne pas trancher unilatéralement quand 2 LLM compétents divergent.
- **Implementer (Opus 4.7 coding)** : ne pas implémenter sur divergence sans arbitrage explicite (par moi ou par Zack).

---

## 4. Profils LLM et délégation appropriée

Synthèse des profils observés dans les 3 repos :

| LLM | Force | Faiblesse | Rôle préféré |
|-----|-------|-----------|--------------|
| Claude Sonnet 4.6 | Lecture statique ligne-par-ligne ultra-précise. Patches concrets. | Manque parfois les invariants systémiques de haut niveau. | **Lead reviewer technique**, deep code review |
| Claude Opus 4.7 | Orchestrateur qui se vérifie. Reproduction Python systématique. Auto-amende ses propres tickets invalides. | Sans vérification → hallucine code:line + propose fixes pour code déjà corrigé. | **Orchestrateur multi-agent + investigateur forensique** |
| Kimi | Vues systémiques, contrats, invariants. Tableaux comparatifs. | Plus high-level, peut manquer les défauts ligne-par-ligne. | **Reviewer systémique + synthèse comparative** |
| ChatGPT | Implémenteur Python/Bash, PR handoffs. | Peu de surface review observée. | **Implémenteur pipelines** |
| Codex | Implémentation MVP propre, atomic_writes, type hints, conventions. Discipline de note. | Schéma minimal initial, tests dédiés à ajouter en phase 2. | **Implémenteur disciplined** |
| Gemini | Implémentation rapide de specs. | Optimise vitesse au détriment robustesse (`os.system('clear')`, slicing fixe, missing actions). | Implémenter SOUS review stricte |
| GPT-5.5 | Ultrareview full-app dual-skill (engineering + domaine). Bugs à impact métier. | Pas observé en mode implémentation. | **Auditeur transversal** |

### Application dans CE projet

- **Opus 4.7 (cette instance)** : reviewer stratégique + orchestrateur. Synthétise les findings cross-LLM, vérifie par reproduction. Sign-off final côté reviewers.
- **Sonnet (co-reviewer)** : lecture statique ligne-par-ligne du code produit par GPT-5.5. Convergence avec Opus = signal P0.
- **GPT-5.5 (double casquette)** : implémenteur + reviewer stratégique full-app. Quand il review le travail d'Opus/Sonnet/architecture, c'est une voix indépendante. Quand il review sa propre impl, c'est self-review (ne compte pas pour la convergence).
- **Kimi délégué (optionnel)** : 2e revue épistémologique sur décisions majeures, indépendance famille de modèle (différent des Claude).
- **Zack** : décideur final sur divergence inter-LLM ou actions irréversibles.

---

## 5. Discipline de commits

Source : `gstack/CLAUDE.md` "Commit style" + observations cross-repo

- **Toujours bisect** : chaque commit = un changement logique
- Renommage/déplacement séparé des changements de comportement
- Test infra séparé des test implementations
- Template change séparé du regen output
- Refactor mécanique séparé d'une nouvelle feature

**Rationale** : si on doit revert, on revert le bug, pas la moitié du refactor qui marche.

---

## 6. Le tradeoff fenêtre de cache vs vérification

Source : observations forensic + Notebook

Quand un agent vérifie chaque finding par reproduction, le coût token explose (~30k extra par session). Mais : 3 tickets invalides évités vaut largement les 30k tokens. **Le coût de réviser un ticket invalide en aval est plus élevé que le coût de le vérifier en amont.**

### Application

- En mode review : toujours vérifier (acceptez les 30k tokens)
- En mode implémentation rapide : pas besoin de re-vérifier le findings d'un reviewer disciplined ; on peut faire confiance s'il a documenté la validation

---

## 7. Append-only pour les artefacts de gouvernance

Source : `forensic-evidence-20260327/CLAUDE.md` + `Notebook_LLM_Tana/scripts/sync_reviews.py`

Les fichiers suivants doivent être append-only (jamais réécrits) :
- Reviews / handoffs (avec timestamp)
- Changelogs
- Audit trails
- Hash chains d'événements

Ne JAMAIS :
- Réécrire un handoff (ajoute un nouveau fichier daté)
- Effacer une entrée du changelog
- Reconstruire une timeline (cassée la chaîne de causalité)

---

## 8. Frontmatter obligatoire sur tout document de review

Format observé dans les 3 repos :

```yaml
---
id: <agent>-<type>-<NN>
title: Titre concis
date: YYYY-MM-DD
status: draft | proposed | applied | accepted | archived
agent: claude-sonnet | claude-opus | kimi | chatgpt | codex | gemini | gpt-5.5
review_kind: proposition | corrections | handoff
target_agent: <destinataire>
scope: <fichiers concernés>
synopsis: >
  Description en 2-3 phrases. Ce que contient le doc, pourquoi il est important,
  ce qui ne peut pas être reconstitué sans le lire en entier.
must_read: true   # optionnel — pour références fondamentales
sources:
  - path/to/source1.md
---
```

**Champs obligatoires** : `id`, `title`, `date`, `status`, `agent`, `synopsis`. Le script de sync retourne exit 1 sur frontmatter incomplet.

---

## 9. La règle "search before building"

Source : `gstack/ETHOS.md`

Avant de concevoir une solution touchant à la concurrence, des patterns infra, ou tout ce qui pourrait avoir un built-in :

1. Search "{runtime} {thing} built-in"
2. Search "{thing} best practice {current year}"
3. Check official runtime/framework docs

3 niveaux : tried-and-true (Layer 1), new-and-popular (Layer 2), first-principles (Layer 3). **Prize Layer 3 above all.**

### Application au catalogue

L'erreur LLM la plus chère, c'est de **réimplémenter ce qui existe déjà** (pattern K2 du catalogue : `_normalize_string_list` dupliqué de `_coerce_str_list`). Toujours grep avant de coder.

---

## 10. Suppressions explicites — réduire le bruit

Source : `gstack/review/checklist.md:170-180`

Liste explicite de "DO NOT flag" :
- "X is redundant with Y" quand la redondance est inoffensive et aide la lisibilité
- "Add a comment explaining why this threshold was chosen" — les thresholds changent, les comments rotten
- "This assertion could be tighter" si elle couvre déjà le comportement
- "Regex doesn't handle edge case X" si X n'arrive jamais en pratique
- "Test exercises multiple guards simultaneously" — c'est OK
- ANYTHING déjà adressé dans le diff qu'on review

→ Tout reviewer dans CE projet doit publier sa propre liste de suppressions au démarrage. Pas de bruit de complétisme.

---

*Document produit le 2026-05-03 par distillation des reviews multi-LLM observées. À enrichir au fur et à mesure que de nouveaux patterns de méthodologie émergent.*
