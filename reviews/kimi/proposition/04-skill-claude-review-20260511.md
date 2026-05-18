---
id: kimi-prop-04-20260511
title: Review systemique de coding-best-practices sous l'angle Claude Code
date: 2026-05-11
status: proposed
agent: kimi
review_kind: proposition
target_agent: claude-opus
scope: skill/SKILL.md, skill/hosts/claude.md, skill/checks/*.md, skill/triggers/*.md, skill/setup
synopsis: >
  Review dediee a l'experience Claude Code comme consommateur de la skill
  coding-best-practices. 6 findings (1 critique, 2 majeurs, 3 moderes).
  Verdict : skill utile mais non contraignante ; le risque de non-lecture
  par Claude est le gap structurel central.
---

# Review systemique — coding-best-practices sous l'angle Claude Code

**Kimi — review systemique, angle consommateur Claude Code**

Date : 2026-05-11
Cible : `skill/` (coding-best-practices) telle qu'installée dans `~/.claude/skills/`

---

## 1. Executive summary

La skill `coding-best-practices` est bien calibree pour Claude Code en tant qu'artefact de connaissance. Les 18 familles couvrent les patterns les plus frequents observes dans les reviews multi-LLM. Les triggers contextuels evitent le bruit d'une activation permanente.

Le probleme structurel est que **la skill n'est pas contraignante**. Claude Code peut l'ignorer silencieusement. Il n'existe pas de hook PreToolUse, pas de gate scriptee, et pas de verification que les checks ont ete lus avant une action. La skill repose entierement sur la discipline du LLM consommateur.

---

## 2. Findings

| # | Severite | Composant | Finding | Effort |
|---|----------|-----------|---------|--------|
| C1 | **CRITIQUE** | `skill/hosts/claude.md` | Aucun mecanisme de garantie que Claude lit la skill avant d'ecrire du code | Hors scope Phase 1 ; documenter explicitement |
| M1 | **MAJEUR** | `skill/SKILL.md` | Document en francais ; Claude Code est optimise pour l'anglais | Phase 1.5 : ajouter SKILL.md.en ou host note |
| M2 | **MAJEUR** | `skill/triggers/*.md` | Les preflight budgets (45s, 60s) ne sont pas verifiables par Claude | Documenter comme convention, pas contrainte |
| m1 | **MODERE** | `skill/hosts/claude.md` | Host note trop minimaliste (4 lignes) | Etendre avec comportement attendu et limites |
| m2 | **MODERE** | `skill/checks/*.md` | Certains checks sont plus adaptes a Codex qu'a Claude (ex: E_llm_hallucination vise le reviewer, pas l'implementer) | Clarifier le role cible par check |
| m3 | **MODERE** | `skill/setup` | Installation claude uniquement par symlink ; pas de verification que Claude Code charge la skill | Ajouter un test de chargement minimal |

---

### C1 — Aucune garantie de lecture par Claude Code

**Description** : La skill est installee comme un fichier SKILL.md dans `~/.claude/skills/`. Claude Code peut choisir de ne pas le charger, ou de ne pas suivre ses instructions. Il n'y a pas de hook, pas de gate, pas de verification.

**Cause systemique** : `skill/hosts/claude.md:16` dit explicitement "Les hooks Claude restent hors scope Phase 1". C'est une limitation honnete, mais elle rend la skill **optionnelle par construction**.

**Impact** : Un utilisateur qui installe cette skill n'a aucune preuve qu'elle ameliore la qualite du code produit par Claude. Le E2E mock P7 prouve le routing, pas la compliance.

**Recommandation** :
- Phase 1 : documenter clairement dans `skill/hosts/claude.md` que la skill est un "artefact de connaissance", pas un "automatisme behavioral".
- Phase 2 : explorer les hooks Claude (`PreToolUse`) pour rendre les triggers contraignants.

---

### M1 — SKILL.md en francais

**Description** : L'integralite de `SKILL.md` est en francais (hors code et identifiants). Claude Code est principalement entraine sur du corpus anglophone.

**Risque** : Degradation de la pertinence des instructions. Des nuances comme "ne pas charger les 18 checks d'un coup" pourraient etre moins bien suivies qu'en anglais.

**Recommandation** :
- Phase 1.5 : produire un `SKILL.md.en` parallele ou ajouter une section langue dans `hosts/claude.md`.
- Alternative : tester la skill en francais sur un echantillon de prompts pour mesurer le taux de declenchement.

---

### M2 — Preflight budgets non verifiables

**Description** : Chaque trigger specifie un budget temporel ("45-second preflight", "60-second preflight"). Claude Code n'a pas de mecanisme pour respecter ce budget.

**Risque** : C'est une convention humaine qui cree une fausse attente de controle. Si un utilisateur lit la skill, il croit que le LLM va passer 45 secondes en preflight. En realite, Claude decide seul.

**Recommandation** : Remplacer les budgets temporels par des criteres de qualite ("avant d'ecrire, verifier X, Y, Z") plutot que des durees.

---

### m1 — Host note Claude trop minimaliste

**Description** : `skill/hosts/claude.md` fait 16 lignes. Il ne documente pas :
- Comment Claude est cense utiliser la skill
- Quels triggers sont les plus importants
- Les limites connues
- La langue de la skill

**Recommandation** : Etendre a ~40 lignes avec une section "Comportement attendu" et "Caveats".

---

### m2 — Checks mal cibles pour le role d'implementer

**Description** : Certains checks comme `E_llm_hallucination` sont concus pour le **reviewer**, pas l'**implementer**. Or Claude Code est souvent utilise en mode implementer.

**Exemple** : Le trigger `on_review_claim` demande de verifier chaque `file:line` avant publication. Si Claude est en train d'ecrire du code (mode implementer), ce trigger ne s'applique pas. Mais si Claude fait une review interne de son propre code, il pourrait l'utiliser.

**Recommandation** : Dans `hosts/claude.md`, clarifier quels checks s'appliquent en mode implementer vs mode reviewer.

---

### m3 — Pas de test de chargement Claude

**Description** : `skill/setup` cree un symlink mais ne verifie pas que Claude Code charge effectivement la skill.

**Recommandation** : Ajouter un test minimal qui verifie que `~/.claude/skills/coding-best-practices/SKILL.md` est lisible et que son frontmatter est valide.

---

## 3. Perspective end-user (Claude)

Si j'etais un utilisateur de Claude Code qui installe cette skill :

| Aspect | Note /5 | Commentaire |
|--------|---------|-------------|
| Facilite d'installation | 5 | `bash skill/setup --host claude --yes` suffit. |
| Clarte du contenu | 4 | Bien structure, mais francais peut freiner. |
| Pertinence des checks | 5 | Les 18 familles sont solides et empiriques. |
| Efficacite reelle | 2 | Je n'ai aucune preuve que Claude les utilise. |
| Bruit | 4 | Les triggers contextuels limitent le bruit. |

**Score end-user Claude : 20/25**

Le point faible est l'efficacite reelle : la skill est un guide, pas un garde-fou.

---

## 4. Convergence avec autres reviews

- **Opus L3** (pas de hook runtime) : confirme mon C1.
- **Kimi M1 P8** (E2E mock = routing, pas compliance) : confirme mon C1.
- **GPT-5.5 P9** (trigger metadata v2) : propose une solution partielle pour C1 via signaux enrichis.

---

## 5. Verdict

| Criteres | Verdict |
|----------|---------|
| Installation Claude | ✅ Fonctionnelle |
| Contenu pour Claude | ✅ Pertinent |
| Contrainte / garantie | ❌ Absente |
| Langue | ⚠️ Francais OK mais pas optimal |
| Host note | ⚠️ Trop minimaliste |

**Verdict global** : La skill est **utile comme artefact de connaissance** pour Claude Code, mais elle ne resout pas le probleme central de la discipline LLM. Recommandation : accepter pour Phase 1, prioriser les hooks ou un mecanisme de gate en Phase 2.

---

*Kimi — review systemique angle Claude, 2026-05-11*
