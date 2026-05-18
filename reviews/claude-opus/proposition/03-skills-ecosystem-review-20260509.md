---
id: claude-opus-prop-03-20260509
title: Audit écosystème skills + adaptations recommandées pour cbp et repos pairs
date: 2026-05-09
status: proposed
agent: claude-opus
review_kind: proposition
target_agent: zack, claude-sonnet, gpt-5.5, kimi
scope: ~/.claude/skills, ~/.codex/skills, ~/.kimi/skills, skill/, repos pairs (Gestion_Projet, Depollution_Sols, Notebook_LLM_Tana, GROK-CLI)
synopsis: >
  Audit des 23 skills installés sur la machine, vue d'ensemble par plateforme,
  10 limites identifiées sur coding-best-practices (L1-L10), 10 adaptations
  recommandées classées par ROI (A1-A4, B1-B3, C1-C3), cross-validation des
  findings Kimi 2026-05-11 (4 confirmés/étendus), propositions miroir déposées
  dans 4 repos pairs pour partage des leçons.
sources:
  - ~/.claude/skills/voirie/**/*
  - ~/.codex/skills/{repo-change-guard,repo-review-snapshot,review-code-canon,voirie/*}/SKILL.md
  - ~/.kimi/skills/{dual-ultrareview-orchestrator,software-ultrareview,depollution-ultrareview}/SKILL.md
  - /home/zack/Documents/Gestion_Projet/review/kimi/handoff/2026-05-11_kimi_review_skills_claude.md
  - /home/zack/Documents/Gestion_Projet/review/kimi/handoff/2026-05-11_kimi_review_skills_codex_chatgpt.md
  - skill/SKILL.md, skill/checks/*.md, skill/triggers/*.md, skill/setup, skill/uninstall
validation:
  - "23 SKILL.md lus directement, pas par mémoire"
  - "Cross-validation Kimi 2026-05-11 effectuée sur 2 reviews"
  - "Convergence Opus+Kimi inter-famille notée explicitement quand présente"
---

# Audit écosystème skills + adaptations recommandées

## 1. Mandat

Zack a demandé une analyse honnête de l'écosystème skills disponible sur la machine et des adaptations possibles pour améliorer code et review sur ce repo. Note miroir à déposer dans `reviews/claude-opus/proposition/` ici et `review/claude/proposition/` des repos pairs ayant une structure de review.

## 2. Inventaire écosystème (23 skills installés)

| Plateforme | Path | Skills présents |
|------------|------|------------------|
| Claude | `~/.claude/skills/` | `coding-best-practices` (lien vers ce repo), `voirie` (1 racine + 6 sub) |
| Codex | `~/.codex/skills/` | `coding-best-practices`, `repo-change-guard`, `repo-review-snapshot`, `review-code-canon`, `depollution-methodology-guard`, `voirie` + 7 sub |
| Kimi | `~/.kimi/skills/` | `depollution-ultrareview`, `software-ultrareview`, `dual-ultrareview-orchestrator` |
| Custom | Repos divers | TenderWatch `REVIEW.md`, Nemoclaw `docs/update-docs`, GROK-CLI forensic |

Trouvaille majeure : `voirie-development-checks` (Codex) est un **wrapper de cbp pour le projet voirie**. Notre skill a donc un consommateur réel hors test → contrainte de stabilité externe.

## 3. Limites cbp identifiées (L1-L10)

| # | Limite | Sévérité | Détail (file:line lus dans cette session) |
|---|--------|----------|-------------------------------------------|
| L1 | E2E ≠ compliance LLM | Majeur | `mock_agent.py:87-133` fait du substring matching. Prouve routing artefact, pas compliance live. |
| L2 | 4 fixtures sur 18 familles | Majeur | `result.json` summary `checks_fired = [A,B,C,J]`. 14 familles validées seulement statiquement. |
| L3 | Aucun hook runtime | Majeur structurel | Pas de `.claude/hooks` ou PreToolUse hook. Triggers = texte. Discrétion complète du LLM consommateur. |
| L4 | Hardcoding 70 IDs | Modéré | `validate.ts:13,160,163` + `sync-catalog.ts:69`. Ajouter famille S = bump × 4. |
| L5 | `fires_on` sans validation regex | Modéré | `validate.ts` vérifie liste non vide, pas `new RegExp(pattern)`. |
| L6 | Pas de host Kimi | Modéré | `skill/hosts/` = `claude.md` + `gstack.md`. Kimi promue reviewer mais non-consommatrice possible. |
| L7 | SKILL.md en français sur hosts anglophones | Modéré | 20838 bytes, friction sémantique sur Codex/Kimi anglophones. |
| L8 | Parser frontmatter dupliqué | Modéré | `mock_agent.py:18-53` ≠ `skill-lib.ts:parseSimpleYaml`. Faux négatifs E2E possibles. |
| L9 | Pas de bench / golden findings | Modéré | Tests structurels. Aucun test sémantique de contenu (ex : `E_llm_hallucination` cohérent ?). |
| L10 | `skill/bin/` vide | Mineur | Dossier créé, aucun helper exposé. |

L1+L3 ensemble = limite centrale honnête : skill = artefact de knowledge portable, pas automatisme behavioral.

## 4. Cross-validation Kimi (handoffs 2026-05-11)

Kimi a publié 2 reviews skill le 11 mai (`Gestion_Projet/review/kimi/handoff/2026-05-11_kimi_review_skills_{claude,codex_chatgpt}.md`). Cross-validation systématique (méthodologie voirie-code-review : `confirm / affiner / réfuter / étendre`).

### Findings additionnels Kimi vs ma liste

| Finding Kimi | Statut vs Opus | Détail |
|--------------|----------------|--------|
| Pas de mode swarm parallèle | **Étend** mon L3 | Je notais "pas de hook runtime". Kimi pointe en plus l'absence de sharding parallèle multi-agents pour les reviews (pattern dual-ultrareview). Vrai gap. |
| Pas de merge-policy formalisée | **Nouveau** | CLAUDE.md §8.3 dit "convergence inter-LLM" mais pas de policy `merged_same_issue / linked / kept_separate / dropped_duplicate` codée. Je l'avais évoqué dans B2 mais pas isolé comme finding. |
| Pas de contradiction resolver / severity calibrator | **Nouveau** | Aucun agent neutre pour trancher. Aujourd'hui c'est Zack ad hoc. |
| `workbook-integrity-guard` (Codex) a BLOQUÉ des livraisons | **Confirme** ma reco B2 | Kimi documente 10 sessions où le gate a fait exit 1 → correction motivée. Preuve d'impact d'un gate scripté. Notre L1 (mock = routing pas behavior) est validé négativement : sans gate scripté, pas d'impact mesurable. |
| `voirie-development-checks` réfère cbp par CHEMIN ABSOLU `/home/zack/Documents/Divers/Dict_AI_Coding/skill/SKILL.md` | **Étend** mon L4 | Je notais hardcoding 70 IDs. Kimi pointe le chemin absolu non-versionné. C'est plus grave : si le repo cbp bouge, voirie-development-checks casse silencieusement. Contrat externe rompable. |
| "5 skills avec gates > 15 skills avec checklists" | **Confirme** ma reco priorité gate scripté | Leçon distillée alignée. |

### Convergence Opus + Kimi inter-famille (signal P0)

CLAUDE.md §8.3 : convergence Anthropic + Moonshot = signal P0 (2 familles de modèle). Sur ces 3 points nous convergeons :

1. **Le caveat "E2E mock = routing, pas compliance LLM"** (mon L1 = Kimi M1 du 2026-05-07 répété).
2. **Priorité aux gates scriptés sur les checklists réflexives** (mon B2/B3 = Kimi conclusion §5).
3. **Le gap "discipline humaine vs automatisme"** (mon L3 = Kimi limites §6.1).

## 5. Recommandations (10 adaptations classées par ROI)

### A. Quick wins (1-3 jours)

| # | Adaptation | Source | Effort | Gain |
|---|------------|--------|--------|------|
| A1 | Adopter `repo-review-snapshot` pour toute review future | Codex skill | 2h | Labels `confirmed_current / partially_closed / historical_closed / not_reproduced`. Élimine les findings obsolètes. |
| A2 | Adopter `repo-change-guard` (closeout sealed) pour jalons P1-P7 et futurs | Codex skill, déjà partiellement utilisé par GPT-5.5 | 4h | Tag `phase1-accepted` honnête, machine-checkable. |
| A3 | Intégrer les 4 labels review dans notre finding-schema | Codex `repo-review-snapshot/references/output-contract.md` | 1h | Lecture cross-LLM lisible (Sonnet/Kimi/GPT-5.5/Opus convergent sur un même schéma). |
| A4 | Importer `review-code-canon` comme référence dans cbp | Codex skill | 1h | Canon de review partagé avec Codex, évite duplication CLAUDE.md §5. |

### B. Structurel (1-2 semaines, Phase 2 entry)

| # | Adaptation | Détail |
|---|------------|--------|
| B1 | Décliner cbp en routing skill + 5 sous-skills (pattern voirie) | `cbp-state-file`, `cbp-test`, `cbp-scan-loop`, `cbp-review-claim`, `cbp-destructive`. Chaque < 5 KB. Routing par `description` autodescriptif. Résout L1 partiellement et L3. |
| B2 | Adapter `dual-ultrareview-orchestrator` en `quad-llm-review-orchestrator` | 4 reviewers de 3 familles. Codifie CLAUDE.md §8.3 en exécutable. Merge policy + severity calibration + contradictions explicites. |
| B3 | Créer `engineering-ultrareview` + `meta-llm-ultrareview` (dual lens) | Lens engineering classique × lens spécifique catalogue 18 familles. Résout les overlaps (Sonnet F3/L10). |

### C. Long terme (Phase 3+)

| # | Adaptation | Détail |
|---|------------|--------|
| C1 | Hook PreToolUse minimal (`.claude/hooks`) | Matche `fires_on` regex, injecte rappel trigger. Hors scope skills, résout L3 vraiment. |
| C2 | `cbp-cross-project` (mémoire inter-repos) | Pattern `~/.kimi/memory/` + sessions. Phase 5 vision long terme. |
| C3 | Adapter `voirie-sync-review` comme base pour notre `REVIEW_SYNC.md` | Au lieu d'inventer le sync bus, reprendre le pattern Codex avec receipts MCP. |

### Priorisation suggérée pour `phase1-accepted`

- **Avant tag** : A1 + A2 + A3 (résout les blockers §7 de ma proposition 02).
- **Démarrage Phase 2** : B2 (orchestrator) prioritaire car c'est ce qui définit le projet.
- **Phase 2 mid** : B1 (sous-skills) + B3 (dual lens) + C3 (sync base).
- **Phase 3+** : C1, C2.

## 6. Le gap "chemin absolu development-checks"

Trouvaille Kimi qui mérite action immédiate. Aujourd'hui `voirie-development-checks/SKILL.md` (Codex) référence :

```text
/home/zack/Documents/Divers/Dict_AI_Coding/skill/SKILL.md
```

C'est un chemin absolu utilisateur-spécifique, non versionné. Si :
- Zack renomme le repo → voirie casse silencieusement
- Un autre dev clone voirie → la skill ne trouve pas la référence
- Le path absolu est exposé dans une PR → fuite mineure

Trois corrections possibles, ordonnées par robustesse :
1. **Internaliser** : copier le contenu pertinent de cbp dans `voirie-development-checks/references/coding-best-practices.md` (versionné). Adoption manuelle des updates.
2. **Variable env** : remplacer par `${CODING_BEST_PRACTICES_DIR:-~/Documents/Divers/Dict_AI_Coding}/skill/SKILL.md`.
3. **Package portable** : publier cbp comme paquet installable (`bun publish` / npm equivalent), `voirie-development-checks` le résout via le PATH. Phase 2.

Recommandation : **option 1** d'ici `phase1-accepted` (résout aussi L4 hardcoding 70 — le contrat externe est explicite).

## 7. Propositions miroir déposées dans les repos pairs

Note de proposition adaptée déposée dans :

- `/home/zack/Documents/Gestion_Projet/review/claude/proposition/05_2026-05-09_skills_ecosystem_audit_voirie.md` — gaps Kimi confirmés cross-LLM + 4 scripts manquants prioritaires + résolution chemin absolu.
- `/home/zack/Documents/Depollution_Sols /review/claude/proposition/06_2026-05-09_skills_ecosystem_handoff_cbp.md` — présentation cbp + adoption via `depollution-development-checks` (pattern voirie) + ce qu'on apprend de leur dual-ultrareview.
- `/home/zack/Documents/Notebook_LLM_Tana/review/claude/proposition/2026-05-09__skills_ecosystem_proposition.md` — Tana n'a pas de SKILL.md custom mais bénéficie de cbp triggers `on_write_state_file` + `on_write_scan_loop` (workflows mcp/, synchro/).
- `/home/zack/GROK-CLI/forensic-evidence-20260327/reviews/active/claude-opus/proposition/49-skills-ecosystem-audit-cross-repo-20260509.md` — structure review riche + forensique. Reco : adoption `repo-review-snapshot` pour les findings forensiques (labels `confirmed_current` etc.).

## 8. Verdict global

L'écosystème skills disponible contient déjà 60-70 % de la vision Phase 2-3 que `ARCHITECTURE.md` projette. Le projet a sous-utilisé les patterns Codex (`repo-change-guard`, `repo-review-snapshot`, `review-code-canon`) et Kimi (`dual-ultrareview-orchestrator`, `software-ultrareview`) qui sont déjà testés et installés.

**Pour la skill cbp** : Phase 1 OK comme knowledge base + plomberie validée. Trois caveats à porter au tag `phase1-accepted` (mes L1, L2, L3 + Kimi M1, M2, M3 convergent). Adoption Phase 1.5 des A1+A2+A3 = pratique.

**Pour le projet multi-LLM** : la convergence Opus + Kimi sur 3 points (caveat E2E, priorité gates scriptés, discipline vs automatisme) est inter-famille = signal P0. Cette note marque la convergence ; reste sign-off Sonnet pour la triangle Anthropic et GPT-5.5 pour quad.

**Pour les repos pairs** : 4 propositions miroir déposées. Chacune adaptée au scope du repo (pas généralistes). Voir §7.

## 9. Validation effectuée

- ✅ 23 SKILL.md lus dans cette session
- ✅ Cross-validation Kimi 2026-05-11 effectuée sur les 2 reviews skill
- ✅ Convergence inter-famille notée explicitement quand présente
- ✅ Findings file:line vérifiés en lisant le code (mock_agent.py:87-133, validate.ts:13/160/163, sync-catalog.ts:69)
- ✅ Aucun finding repris d'une review antérieure sans relecture

---

*Soumis par Claude Opus 4.7 le 2026-05-09. Sign-off attendus : Sonnet pour convergence Anthropic, GPT-5.5 pour quad. Zack pour arbitrage priorité Phase 1.5 vs Phase 2 entry.*
