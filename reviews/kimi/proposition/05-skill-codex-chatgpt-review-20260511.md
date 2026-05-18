---
id: kimi-prop-05-20260511
title: Review systemique de coding-best-practices sous l'angle ChatGPT / Codex
date: 2026-05-11
status: proposed
agent: kimi
review_kind: proposition
target_agent: claude-opus
scope: skill/SKILL.md, skill/hosts/codex.md, skill/checks/*.md, skill/triggers/*.md, skill/setup, ~/.codex/skills/.system/*
synopsis: >
  Review dediee a l'experience Codex / ChatGPT comme consommateur de la skill
  coding-best-practices. 7 findings (0 critique, 3 majeurs, 4 moderes).
  Verdict : skill portable en artefact mais a risque de conflit avec le
  skillstack Codex existant ; la parite comportementale n'est pas prouvée.
---

# Review systemique — coding-best-practices sous l'angle ChatGPT / Codex

**Kimi — review systemique, angle consommateur Codex / ChatGPT**

Date : 2026-05-11
Cible : `skill/` (coding-best-practices) telle qu'installée dans `~/.codex/skills/`
Contexte additionnel : skills Codex deja actives (`repo-change-guard`, `repo-review-snapshot`, `review-code-canon`, `depollution-methodology-guard`, `.system/*`)

---

## 1. Executive summary

La skill `coding-best-practices` est techniquement installable dans `~/.codex/skills/`. Le format SKILL.md est lisible sans dependance Claude-only. Cependant, l'ecosysteme Codex de l'utilisateur contient deja **5 skills actives** qui couvrent en partie le meme perimetre.

Le risque principal est la **redondance non coordonnee** : `repo-change-guard` et `repo-review-snapshot` imposent deja des protocoles de preuve et de snapshot qui ne referencent pas `coding-best-practices`. Si Codex charge les deux, l'utilisateur obtient des instructions qui peuvent se contredire ou se doubler.

---

## 2. Findings

| # | Severite | Composant | Finding | Effort |
|---|----------|-----------|---------|--------|
| M1 | **MAJEUR** | `skill/hosts/codex.md` | Parite comportementale non prouvée ; aucun E2E sur Codex reelle | Phase 2 : smoke test Codex live |
| M2 | **MAJEUR** | Ecosysteme Codex | Redondance avec `repo-change-guard` (preuve avant conclusion) et `repo-review-snapshot` (labels review) | Phase 1.5 : mapper les overlaps |
| M3 | **MAJEUR** | `skill/SKILL.md` | Francais sur un host optimise pour l'anglais ; risque de moins bonne adherence | Phase 1.5 : SKILL.md.en ou note langue |
| m1 | **MODERE** | `skill/hosts/codex.md` | Host note trop minimaliste (4 lignes) ; pas de guide d'utilisation Codex-specifique | Etendre avec comportement attendu |
| m2 | **MODERE** | `skill/setup` | Le setup installe cbp comme symlink, mais Codex peut avoir deja des skills systeme (`repo-change-guard`, etc.) qui prennent la priorite | Documenter la precedence |
| m3 | **MODERE** | `skill/triggers/*.md` | Les patterns `fires_on` (regex Python/JS) ne sont pas testes sur le moteur de matching de Codex | Ajouter validation regex cross-host |
| m4 | **MODERE** | `skill/checks/*.md` | Checks D, E, J (iteration, hallucination, test) sont plus adaptes a un reviewer humain ou Claude qu'a un agent Codex en mode implementation | Clarifier le role cible |

---

### M1 — Parite comportementale non prouvée sur Codex

**Description** : `skill/hosts/codex.md:13` dit "La parite comportementale avec Claude est Phase 2". Aucun test n'a ete fait pour verifier que Codex lit, comprend et applique les triggers de cbp.

**Cause systemique** : Le E2E P7 est un mock Python deterministe. Il ne prouve rien sur le comportement d'un agent Codex reel.

**Impact** : L'utilisateur peut croire que cbp protege egalement Codex, alors qu'aucune preuve n'existe.

**Recommandation** :
- Phase 2 : smoke test manuel sur Codex avec un fichier plante.
- Phase 1 : documenter explicitement dans `hosts/codex.md` que la skill est "installee mais non validee comportementale".

---

### M2 — Redondance avec le skillstack Codex existant

**Description** : L'utilisateur a deja les skills suivantes dans `~/.codex/skills/` :
- `repo-change-guard` : impose une boucle de preuve avant toute conclusion d'implementation
- `repo-review-snapshot` : impose un snapshot et des labels review (`confirmed_current`, etc.)
- `review-code-canon` : impose des standards de review et d'implementation
- `depollution-methodology-guard` : gate methodologique pour changements scientifiques

Ces skills entrent en overlap avec cbp :

| Skill Codex existante | Overlap avec cbp |
|-----------------------|------------------|
| `repo-change-guard` | `B_cascade_failure` (preuve avant conclusion), `A_atomic_write` (validation post-change) |
| `repo-review-snapshot` | `E_llm_hallucination` (preuve de lecture), `J_bidir_test_coverage` (validation tests) |
| `review-code-canon` | `K_architecture_smells` (quality), `G_shell_token_filtering` (security) |

**Risque** : Codex recoit des instructions contradictoires ou redondantes. Ex : `repo-change-guard` dit "ne pas conclure sans closeout" ; cbp dit "produire la phrase de preflight". Ce ne sont pas des contradictions, mais ils ne se referencent pas.

**Recommandation** :
- Phase 1.5 : ajouter dans `hosts/codex.md` une section "Relation avec les skills Codex existantes" qui mappe cbp vers `repo-change-guard` et `repo-review-snapshot`.
- Option : integrer cbp comme une **sous-skill** ou **reference** de `review-code-canon` plutot que comme skill independante.

---

### M3 — SKILL.md en francais sur host anglophone

**Description** : Meme finding que pour Claude (M1), mais plus aigu pour Codex car l'ecosysteme Codex/OpenAI est quasi-exclusivement anglophone.

**Risque** : Codex pourrait ignorer des nuances ou mal interpreter les triggers en francais.

**Recommandation** : Priorite plus haute que pour Claude. Un `SKILL.md.en` ou un resume anglais dans `hosts/codex.md` est necessaire avant de pretendre a la portabilite.

---

### m1 — Host note Codex trop minimaliste

**Description** : `skill/hosts/codex.md` fait 16 lignes, comme `claude.md`. Il ne guide pas l'utilisateur Codex sur :
- Comment savoir si la skill est active
- Quels triggers sont les plus utiles en mode implementation
- Comment eviter les conflits avec `repo-change-guard`

**Recommandation** : Etendre a ~50 lignes avec une section "Integration avec votre skillstack Codex".

---

### m2 — Precedence non documentee avec les skills systeme Codex

**Description** : Codex charge les skills dans un ordre qui peut donner la priorite aux skills systeme (`.system/*`) ou aux skills utilisateur. L'utilisateur ne sait pas si cbp sera lue avant ou apres `repo-change-guard`.

**Recommandation** : Documenter dans `hosts/codex.md` que cbp est conçu comme **complementaire**, pas comme remplacement, et qu'elle doit etre lue en conjonction avec les skills existantes.

---

### m3 — Patterns `fires_on` non valides sur le moteur Codex

**Description** : Les triggers utilisent des regex et patterns (`python_pattern`, `bash_command`, etc.) qui sont des conventions textuelles. `validate.ts` verifie leur presence mais pas leur syntaxe.

**Risque** : Si Codex a un moteur de matching different de Claude, les patterns pourraient ne pas declencher.

**Recommandation** : Ajouter un champ `codex_pattern` ou `host_neutral_pattern` dans les triggers pour Phase 2, et valider la syntaxe regex dans `validate.ts`.

---

### m4 — Checks mal adaptes au mode implementation Codex

**Description** : Certains checks (E_llm_hallucination, J_bidir_test_coverage, D_iteration_semantics) sont plus utiles pour un **reviewer** que pour un **implementer**. Or Codex est principalement utilise pour ecrire du code.

**Exemple** : `E_llm_hallucination` demande de verifier chaque `file:line` cite avant de publier un finding. En mode implementation, Codex ne publie pas de review, il ecrit du code.

**Recommandation** : Dans `hosts/codex.md`, lister les checks pertinents par mode de travail Codex :
- Mode implementation : A, B, C, F, G, H, I, K, L, N, O
- Mode review : D, E, J, M, P, Q, R

---

## 3. Perspective end-user (Codex / ChatGPT)

Si j'etais un utilisateur de Codex qui installe cette skill :

| Aspect | Note /5 | Commentaire |
|--------|---------|-------------|
| Facilite d'installation | 5 | `bash skill/setup --host codex --yes` suffit. |
| Clarte du contenu | 3 | Francais penalise sur Codex anglophone. |
| Pertinence des checks | 4 | Pertinents mais partiellement doubles par `repo-change-guard`. |
| Efficacite reelle | 2 | Aucune preuve que Codex les applique. |
| Integration ecosysteme | 2 | Risque de redondance avec skills existantes. |

**Score end-user Codex : 16/25**

Le score est plus bas que Claude a cause de la langue et de la redondance avec le skillstack existant.

---

## 4. Comparaison avec les skills Codex existantes

| Criteres | cbp | repo-change-guard | repo-review-snapshot | review-code-canon |
|----------|-----|-------------------|----------------------|-------------------|
| Portee | 18 familles bugs LLM | Boucle de preuve implementation | Snapshot review + labels | Standards review + code quality |
| Contrainte | Aucune (texte) | Protocole obligatoire | Protocole obligatoire | Standards obligatoires |
| Preuve | E2E mock | Closeout sealed | Receipt valide | Checklist exhaustive |
| Langue | Francais | Anglais | Anglais | Anglais |
| Couverture | Generique LLM | Generique repo | Generique repo | Generique engineering |

**Constat** : cbp apporte une valeur unique (catalogue empirique de bugs LLM) mais sous-performe sur la contrainte et la langue par rapport aux skills Codex existantes.

---

## 5. Convergence avec autres reviews

- **Opus L1-L3** (E2E mock, pas de hook, pas de compliance LLM) : confirme M1.
- **Opus L7** (francais sur hosts anglophones) : confirme M3.
- **GPT-5.5 P9-P10** (trigger metadata v2, review evidence schema) : propose des solutions pour m2 et m3.
- **Kimi M3 P8** (absence de host Kimi) : meme constat pour Codex : le host note est une coquille vide.

---

## 6. Verdict

| Criteres | Verdict |
|----------|---------|
| Installation Codex | ✅ Fonctionnelle |
| Contenu pour Codex | ⚠️ Pertinent mais en francais |
| Contrainte / garantie | ❌ Absente |
| Integration ecosysteme | ⚠️ Redondance non mappee |
| Parite comportementale | ❌ Non prouvée |

**Verdict global** : La skill est **techniquement portable** vers Codex mais **pas encore utile** dans l'etat actuel. Trois blockers :
1. La langue (francais)
2. L'absence de preuve de comportement
3. La redondance non documentee avec `repo-change-guard` et `repo-review-snapshot`

**Recommandation** :
- Avant de promouvoir Codex comme host supporte : corriger M3 (francais) et M2 (mapping ecosysteme).
- Phase 2 : smoke test live sur Codex pour valider M1.

---

*Kimi — review systemique angle Codex/ChatGPT, 2026-05-11*
