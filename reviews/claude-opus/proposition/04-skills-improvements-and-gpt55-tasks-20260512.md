---
id: claude-opus-prop-04-20260512
title: Tâches code à GPT-5.5 + améliorations skills Opus suite findings cross-LLM
date: 2026-05-12
status: proposed
agent: claude-opus
review_kind: proposition
target_agent: gpt-5.5, zack, claude-sonnet, kimi
scope: skill/, scripts/, ARCHITECTURE.md (cbp) + ~/.claude/skills/voirie/references/ (Opus skills)
synopsis: >
  Suite à l'audit écosystème skills (prop 03) et à la convergence Opus+GPT-5.5
  (prop 14) + Opus+Kimi (handoffs 2026-05-11), liste précise de 8 tâches code
  à GPT-5.5 pour adresser les findings L1-L10 et M1-M3 non résolus. En miroir,
  amélioration de mes skills personnels (pack voirie Claude) : nouvelle reference
  convergence-policy.md + extension du handoff-frontmatter aux 4 LLM.
sources:
  - reviews/claude-opus/proposition/03-skills-ecosystem-review-20260509.md
  - reviews/gpt-5.5/proposition/14-cross-host-skill-synthesis-20260511.md
  - reviews/gpt-5.5/proposition/15-internal-skill-corrections-review-20260511.md
  - /home/zack/Documents/Gestion_Projet/review/kimi/handoff/2026-05-11_kimi_review_skills_claude.md
  - /home/zack/Documents/Gestion_Projet/review/kimi/handoff/2026-05-11_kimi_review_skills_codex_chatgpt.md
  - skill/SKILL.md, scripts/validate.ts, scripts/sync-catalog.ts, skill/hosts/, skill/tests/e2e/mock_agent.py
findings_state: confirmed_current
reviewed_revision: 2d9163f+dirty
---

# Tâches code à GPT-5.5 + améliorations skills Opus

## 1. Contexte

Depuis ma proposition 03 (2026-05-09), GPT-5.5 a déposé 2 notes substantielles :

- `14-cross-host-skill-synthesis-20260511.md` : audit cross-host indépendant + roadmap P9-P12 (trigger metadata v2, evidence schema, eval harness, orchestration cross-review)
- `15-internal-skill-corrections-review-20260511.md` : corrections drift documentaire P6/P7 + verdict "ne pas rouvrir P1-P7 sauf finding externe nouveau"

GPT-5.5 a corrigé 4 fichiers documentaires (`README.md`, `hosts/claude.md`, `hosts/codex.md`, `catalog/bug_catalog.md` régénéré) mais **n'a touché aucun code skill**. Position défendable mais 10 findings (L1-L10 prop 03) et 3 findings Kimi (M1-M3 prop kimi-03) restent ouverts en code.

Convergence Opus+GPT-5.5 sur la roadmap P9-P12 = 2 familles de modèle (Anthropic + OpenAI). Convergence Opus+Kimi sur caveat E2E mock + gates scriptés = 2 familles (Anthropic + Moonshot). Sur **P10 evidence schema** et **P12 cross-review orchestration**, les 3 LLM convergent indépendamment = signal P0 maximum selon CLAUDE.md §8.3.

Cette note propose : (A) 8 tâches code précises à GPT-5.5, (B) 2 améliorations à mes skills, (C) hors scope explicite.

## 2. Section A — Tâches code à GPT-5.5 (T1-T8)

### T1 — Corriger le hardcoding 70 IDs (L4 / Kimi M3)

**Fichiers** : `scripts/validate.ts`, `scripts/sync-catalog.ts`

**Constat** :
- `scripts/validate.ts:13` : `EXPECTED_FAMILIES = "ABCDEFGHIJKLMNOPQR".split("")`
- `scripts/validate.ts:160,163` : `if (Number(metadata.pattern_count) !== 70)` et `catalog_ids.length !== 70`
- `scripts/sync-catalog.ts:69-71` : `if (ids.length !== 70) throw new Error(...)`

**Diff attendu** : remplacer `70` par une constante dérivée dynamiquement, OU documenter dans `ARCHITECTURE.md §5` que l'ajout d'une famille requiert un bump manuel de 4 constantes (+ 1 source canonique). Préférence : option B (documenter l'invariant explicite) car Phase 1 = catalogue figé.

```ts
// scripts/sync-catalog.ts proposition de diff
// AVANT
if (ids.length !== 70) {
  throw new Error(`expected 70 catalog IDs, found ${ids.length}`);
}
// APRÈS
const PHASE1_EXPECTED_IDS = 70;  // bump manuel si famille ajoutée (cf ARCHITECTURE.md §5.4)
if (ids.length !== PHASE1_EXPECTED_IDS) {
  throw new Error(
    `expected ${PHASE1_EXPECTED_IDS} catalog IDs, found ${ids.length}. ` +
    `If you added a family, bump the constant in 3 places: validate.ts:13/160/163, sync-catalog.ts:69.`
  );
}
```

Effort : 30 min. Risque : 0.

### T2 — Valider la syntaxe regex des `fires_on` (L5 / Kimi m2)

**Fichier** : `scripts/validate.ts` (zone `validateTriggers()`)

**Constat** : `validate.ts` vérifie que `fires_on` est une liste non-vide mais ne tente pas `new RegExp(pattern)` sur les valeurs. Pattern malformé = silent fail au runtime.

**Diff attendu** :

```ts
// Dans validateTriggers(), après requireNonEmptyList sur fires_on :
for (const entry of metadata.fires_on || []) {
  if (typeof entry !== "string") continue;
  const match = entry.match(/^(\w+_regex|\w+_pattern):\s*['"]?(.+?)['"]?$/);
  if (match) {
    const pattern = match[2];
    try {
      new RegExp(pattern);
    } catch (err) {
      errors.push(`${relativePath(path)}: invalid regex in fires_on '${entry}': ${err.message}`);
    }
  }
}
```

Effort : 1h (logic + 1 test unitaire qui plante avec un pattern volontairement cassé). Risque : faible.

### T3 — Créer `skill/hosts/kimi.md` (L6 / Kimi m3)

**Fichier nouveau** : `skill/hosts/kimi.md`

**Constat** : Kimi est promue reviewer régulière (CLAUDE.md §2) mais ne peut pas consommer la skill — `skill/hosts/` = `claude.md` + `codex.md` + `gstack.md` uniquement.

**Contenu attendu** (court) :

```markdown
# Host Kimi

Kimi est vise comme host compatible par artefact en Phase 1.

## Installation cible

```text
~/.kimi/skills/coding-best-practices/
```

## Notes Phase 1

- L'installation utilise le meme `skill/setup` que Claude/Codex avec `--host kimi`.
- Le pack Kimi est anglophone-first ; le `SKILL.md` francais peut introduire de la friction (cf L7).
- La parite comportementale live avec un agent Kimi reste a verifier en Phase 2.
```

Effort : 15 min + une ligne dans `skill/setup` pour reconnaître `--host kimi` (vérifier que la structure `~/.kimi/skills/` existe — c'est confirmé : `ls ~/.kimi/skills/` retourne 3 skills). Risque : 0.

### T4 — Unifier le parser frontmatter (L8 / Kimi m1)

**Fichier** : `skill/tests/e2e/mock_agent.py`

**Constat** : `mock_agent.py:18-53` réimplémente un mini-parser YAML qui diverge de `scripts/skill-lib.ts:parseSimpleYaml`. Champs frontmatter complexes peuvent diverger silencieusement.

**Diff attendu** : remplacer le parser maison par `yaml.safe_load()`.

```python
# AVANT
def parse_frontmatter(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        raise ValueError(f"{path}: missing frontmatter")
    # ... 35 lignes de parsing maison ...

# APRÈS
import yaml

def parse_frontmatter(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        raise ValueError(f"{path}: missing frontmatter")
    end = text.find("\n---", 4)
    if end == -1:
        raise ValueError(f"{path}: unterminated frontmatter")
    return yaml.safe_load(text[4:end]) or {}
```

Effort : 30 min. Risque : faible (pyyaml est déjà dans `environment.yml`).

### T5 — Helper minimal dans `skill/bin/` (L10)

**Fichier nouveau** : `skill/bin/cbp-fires` (exécutable Python)

**Constat** : `skill/bin/` est documenté dans `README.md` comme "utilitaires runtime futurs" mais reste vide. Un helper minimal exposé manuellement aux LLM consommateurs (`bash skill/bin/cbp-fires path/to/file.py` → liste les triggers applicables) résout partiellement L3 (pas de hook automatique mais helper invocable).

**Contenu attendu** : script de ~50 lignes qui parse les `fires_on` des 5 triggers et matche contre le contenu/path d'un fichier en argument. Retour : liste des triggers applicables avec leurs `calls_checks`.

Effort : 2h. Risque : faible.

### T6 — Documenter L1/L2 explicitement dans `ARCHITECTURE.md §5.3` (M1/M2 Kimi)

**Fichier** : `ARCHITECTURE.md`

**Constat** : `hosts/codex.md` mentionne maintenant "E2E P7 reste un mock déterministe, pas une preuve de comportement LLM live" (correction GPT-5.5). Mais `ARCHITECTURE.md §5.3` ne le dit pas en termes de critère d'acceptation Phase 1.

**Diff attendu** : ajouter dans `§5.3 Critères d'acceptation Phase 1` une sous-section explicite :

```markdown
### 5.3.2 Limites P7 acceptées comme boundary Phase 1

Le E2E P7 est un **routing-and-trigger-mapping proof**, pas un **live LLM compliance proof** :

- Le mock `tests/e2e/mock_agent.py` fait du substring matching déterministe sur 4 patterns plantés ; il ne charge pas SKILL.md et ne simule pas un LLM réel.
- Couverture dynamique : 4 familles sur 18 (A_atomic_write, B_cascade_failure, C_scan_loop_safe, J_bidir_test_coverage). Les 14 autres familles sont validées **uniquement statiquement** (frontmatter + sections obligatoires + orphan checks).
- Convergence Opus + Kimi sur ce caveat (handoff Kimi 2026-05-07 §M1 et proposition Opus 02 §7.3).

Acceptable en Phase 1. À renforcer en Phase 2 par : (a) au moins 1 fixture par famille, (b) au moins 1 live smoke test sur un vrai host (Claude Code, Codex ou Kimi).
```

Effort : 30 min. Risque : 0 (documentation uniquement).

### T7 — Trigger metadata v2 (P9 proposée par GPT-5.5 lui-même)

**Fichiers** : `skill/triggers/*.md` (5 fichiers) + `scripts/validate.ts` + `scripts/gen-skill-docs.ts`

**Constat** : GPT-5.5 prop 14 §1 propose d'ajouter des champs optionnels `promptSignals`, `pathPatterns`, `bashPatterns`, `toolPatterns` aux triggers. Convergence avec mon L5 (mais GPT-5.5 va plus loin avec une structure compilable).

**Critère d'acceptation** :
- Les 5 triggers existants restent valides (champs optionnels backward-compatible)
- `validate.ts` valide les nouveaux champs sans casser Phase 1
- `gen-skill-docs.ts` affiche les signaux de manière compacte

Effort estimé par GPT-5.5 : moyen. Risque : moyen (impact sur le rendu SKILL.md).

**Coordination** : T7 doit être implémenté APRÈS T2 (validation regex) pour pouvoir réutiliser le pattern.

### T8 — Resolution chemin absolu `voirie-development-checks → cbp` (M3 Kimi étendu)

**Fichiers** : `~/.codex/skills/voirie-development-checks/SKILL.md` (hors repo, mais GPT-5.5 peut écrire un wrapper local)

**Constat** : `voirie-development-checks` (Codex skill, autre repo voirie) référence cbp par chemin absolu `/home/zack/Documents/Divers/Dict_AI_Coding/skill/SKILL.md`. Mon prop 03 §6 propose 3 options.

**Action proposée à GPT-5.5** : préparer côté cbp une **copie versionnée minimale** dans `skill/exports/coding-best-practices-summary.md` (~3 KB) que `voirie-development-checks` pourrait référencer par chemin relatif si copiée localement. Découple le contrat externe.

Effort : 1h (écriture du summary). Risque : 0 (additif).

### Synthèse des tâches T1-T8

| # | Finding | Fichiers | Effort | Risque | Priorité |
|---|---------|----------|--------|--------|----------|
| T1 | L4/M3 hardcoding 70 | scripts/validate.ts, scripts/sync-catalog.ts | 30min | 0 | Avant `phase1-accepted` |
| T2 | L5/m2 fires_on regex | scripts/validate.ts | 1h | Faible | Avant `phase1-accepted` |
| T3 | L6/m3 hosts/kimi.md | skill/hosts/kimi.md, skill/setup | 15min | 0 | Avant `phase1-accepted` |
| T4 | L8/m1 parser frontmatter | skill/tests/e2e/mock_agent.py | 30min | Faible | Avant `phase1-accepted` |
| T5 | L10 bin/ helper | skill/bin/cbp-fires | 2h | Faible | Phase 1.5 |
| T6 | M1/M2 documenter | ARCHITECTURE.md §5.3 | 30min | 0 | Avant `phase1-accepted` |
| T7 | L5 / P9 GPT-5.5 trigger metadata v2 | skill/triggers/*.md + scripts/ | Moyen | Moyen | Phase 2 entry |
| T8 | M3 Kimi étendu | skill/exports/ | 1h | 0 | Avant `phase1-accepted` |

**Total estimé pour les 6 tâches "Avant phase1-accepted"** : ~3h30. C'est faisable dans une session GPT-5.5 ciblée.

## 3. Section B — Améliorations à mes skills (pack voirie Claude)

Mes skills personnels sont dans `~/.claude/skills/voirie/`. Ils servent à mon rôle de reviewer/orchestrateur sur les projets voirie ET cbp (par référence cross-projet). Suite aux findings de cette session, deux améliorations applicables :

### O1 — Nouvelle reference `convergence-policy.md`

**Fichier nouveau** : `~/.claude/skills/voirie/references/convergence-policy.md`

**Motivation** : CLAUDE.md (Dict_AI_Coding) §8.3 codifie la convergence inter-LLM par nombre de signatures, mais pas par **familles de modèle**. Or notre setup actuel a 4 LLM de 3 familles (Anthropic = Opus + Sonnet, OpenAI = GPT-5.5, Moonshot = Kimi). Le signal change selon que la convergence traverse les familles.

**Contenu** : codifier le niveau de signal selon le nombre de familles convergentes (1 famille = faible, 2 = fort, 3+ = P0 max). Avec règles de propagation au merge-policy.

Effort : 30 min. Appliqué dans cette session (voir §5).

### O2 — Extension du `handoff-frontmatter.md` aux 4 LLM

**Fichier** : `~/.claude/skills/voirie/references/handoff-frontmatter.md`

**Motivation** : le frontmatter actuel a `codex_handoff_consumed` (champ qui trace quel handoff Codex est référencé). Avec l'arrivée de Kimi et GPT-5.5 dans le bus, il faut généraliser. Aussi : intégrer le pattern `findings_state` du `repo-review-snapshot` Codex (mon A3).

**Diff** : ajouter champs optionnels `kimi_handoff_consumed`, `gpt55_handoff_consumed`, `sonnet_handoff_consumed`, `findings_state` (4 labels).

Effort : 15 min. Appliqué dans cette session (voir §5).

## 4. Section C — Hors scope explicite

Pour éviter le scope creep, je liste ce qui **n'est pas** demandé à GPT-5.5 dans cette proposition :

- L3 (pas de hook runtime) — GPT-5.5 prop 14 P9 propose une alternative additive (trigger metadata v2) qui suffit Phase 1. Le hook PreToolUse vrai reste Phase 3+.
- L7 (SKILL.md français) — décision Zack hors code. Phase 2 candidate.
- L9 (pas de bench / golden findings) — couvert par GPT-5.5 P11 (eval harness). Phase 2.
- B1 prop 03 (cbp en routing skill + 5 sous-skills) — réorganisation lourde, Phase 2 entry.
- B2 prop 03 (quad-llm-review-orchestrator) — Phase 2 entry.
- B3 prop 03 (dual lens engineering + meta-llm) — Phase 2 mid.
- Modification de `voirie-development-checks` côté pack Codex voirie — autre repo, autre owner.

## 5. Améliorations appliquées dans cette session

J'applique O1 et O2 en parallèle de cette proposition, donc les fichiers existent au moment où vous lisez ceci :

- ✏️ Création : `~/.claude/skills/voirie/references/convergence-policy.md`
- ✏️ Édition : `~/.claude/skills/voirie/references/handoff-frontmatter.md` (ajout 4 champs)

Voir les deux fichiers pour le contenu canonique.

## 6. Demandes de sign-off

| Acteur | Demande | Bloquant ? |
|--------|---------|------------|
| **GPT-5.5** | Accepter ou contester T1-T8. Implémenter T1+T2+T3+T4+T6+T8 avant `phase1-accepted`. | Oui pour 6 tâches |
| **Sonnet** | Review line-by-line des 17 checks et 4 triggers non spot-checkés (reste de mon prop 02 §7.2). | Oui pour P8 convergence Anthropic |
| **Kimi** | Si ces 6 tâches sont implémentées, mes findings + les vôtres (M1/M2/M3) sont adressés ou explicitement documentés comme boundary Phase 1. Confirmation acceptée ? | Non bloquant mais valeur ajoutée |
| **Zack** | Arbitrage Q1-Q3 prop 05 voirie + accord sur l'ordre Phase 1.5 vs Phase 2 entry. | Oui pour tag final |

## 7. Validation effectuée pour ce document

- ✅ Lecture directe de : `scripts/validate.ts`, `scripts/sync-catalog.ts`, `skill/hosts/{claude,codex}.md`, `skill/tests/e2e/mock_agent.py`, `skill/README.md`, ~/.claude/skills/voirie/references/{finding-schema,handoff-frontmatter,merge-policy}.md dans cette session
- ✅ Validations reproduites : `bun run validate` OK, 19 tests OK, E2E_OK (cf prop 02 et confirmation 11 mai par GPT-5.5 prop 15)
- ✅ Cross-validation Kimi 2026-05-11 + GPT-5.5 14/15 effectuée
- ✅ Aucun `file:line` cité sans relecture
- ✅ Convergence inter-famille notée explicitement quand présente

---

*Soumis par Claude Opus 4.7 le 2026-05-12 pour suite par GPT-5.5 (implémentation T1-T8), Sonnet (P8 line-by-line) et arbitrage Zack.*
