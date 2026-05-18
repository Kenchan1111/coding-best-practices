---
id: 14-cross-host-skill-synthesis-20260511
title: Synthèse cross-host des skills Claude/Codex/Kimi pour améliorer coding-best-practices
date: 2026-05-11
status: proposed
agent: gpt-5.5
scope: skill-roadmap
synopsis: "Inventaire des skills disponibles dans ~/.claude, ~/.codex et ~/.kimi, distillation des mécanismes utiles pour gstack/coding-best-practices, et proposition d'adaptation sélective sans importer aveuglément les caches de plugins."
---

# Synthèse cross-host des skills disponibles

## Contexte

Zack demande de regarder les skills disponibles pour ChatGPT/Codex, Claude et Kimi dans :

- `~/.codex`
- `~/.claude`
- `~/.kimi`

Objectif : en tirer le meilleur pour améliorer `coding-best-practices` et son augmentation de gstack, sans créer une seconde plomberie concurrente.

Inspection faite en lecture seule. Les répertoires de sessions, logs, caches runtime, auth et secrets n'ont pas été inspectés comme source de contenu.

## Inventaire observé

Total observé : 417 fichiers `SKILL.md` hors sessions/cache runtime sensible.

Répartition :

- `claude_user_active` : 7
- `claude_marketplace` : 28
- `codex_system_active` : 5
- `codex_user_active` : 12
- `codex_plugin_cache` : 362
- `kimi_user_active` : 3

Distinction importante :

- Les skills actifs locaux sont les seuls candidats directs à l'adaptation.
- Le marketplace Claude et le cache temporaire Codex sont des sources d'idées, pas une racine de confiance.
- Les 362 skills du cache Codex ne doivent pas être importés automatiquement dans gstack.

## Ce qu'il faut reprendre

### 1. Déclencheurs plus riches

Source principale : skill Vercel `observability` et plusieurs skills Claude.

Le format actuel de `skill/triggers/*.md` est sain, mais il reste principalement textuel :

- `fires_on`
- `calls_checks`
- `suppress_when`
- `preflight_budget`

Amélioration proposée :

- Ajouter des métadonnées host-neutral comme `promptSignals`, `pathPatterns`, `bashPatterns`, `toolPatterns`.
- Garder le texte lisible, mais compiler ces champs vers des instructions adaptées à Claude, Codex, Kimi et gstack.
- Faire valider que les nouveaux champs restent courts et ne déclenchent pas toutes les checks trop souvent.

But : réduire le risque que le LLM ignore la skill pendant le coding.

### 2. Preuve avant conclusion

Sources principales :

- Codex `repo-change-guard`
- Codex `repo-review-snapshot`
- Superpowers `verification-before-completion`
- Superpowers `systematic-debugging`

Mécanisme à reprendre :

- Toute conclusion de type "fait", "corrigé", "sign-off", "aucun bug" doit pointer vers une preuve fraîche.
- Pour les reviews, un finding doit être classé selon l'état de preuve : `confirmed`, `supported_by_code_path`, `suspected`, `not_reproduced`.
- Pour les changements, la clôture doit inclure les commandes exécutées et le statut.

Adaptation à `coding-best-practices` :

- Renforcer `E_llm_hallucination` et `on_review_claim` avec un champ `evidence_state`.
- Ajouter une gate de completion légère dans la doc host gstack/Codex.
- Ne pas forcer un outil externe en Phase 1 ; rester dans le contrat de skill lisible.

### 3. Séparation raw findings / synthèse

Sources principales :

- Kimi `dual-ultrareview-orchestrator`
- Kimi `software-ultrareview`

Mécanisme à reprendre :

- Garder les findings bruts par reviewer jusqu'à la synthèse.
- Ne pas fusionner trop tôt les avis Opus, Sonnet, GPT-5.5 et Kimi.
- Dédupliquer seulement à la fin, par root cause, fichier/ligne, repro et impact.
- Ne jamais moyenner la sévérité : garder la sévérité la plus forte si elle est justifiée.

Adaptation à gstack :

- Formaliser un output machine lisible pour les reviews : `findings_machine.json`.
- Garder le format humain existant dans `reviews/*`.
- Ajouter une convention de synthèse avec contradictions explicites.

### 4. Évaluation A/B des skills

Sources principales :

- Claude `skill-creator`
- Claude agents `comparator`, `analyzer`, `grader`
- Codex `plugin-eval`

Mécanisme à reprendre :

- Tester une variante de skill contre une baseline sur le même prompt.
- Comparer à l'aveugle avant de savoir quelle variante est laquelle.
- Séparer le comparator, l'analyzer et le grader.
- Ajouter des métriques déterministes quand possible.

Lien avec Meta-Harness / ASI-Evolve :

- Cette couche est le pont réaliste avant un moteur ML.
- On n'a pas besoin de commencer par RL.
- On a besoin d'abord de traces, variantes, métriques, et sorties comparables.

### 5. Sécurité d'import et confiance

Sources principales :

- Codex security-scan phases
- Garde existante du repo sur Bun/Conda/signatures

Règles proposées :

- Ne jamais installer automatiquement une skill issue d'un cache temporaire.
- Ne pas exécuter les scripts embarqués d'une skill tierce sans lecture ciblée et validation.
- Refuser les skills qui demandent des outils trop larges sans justification, par exemple Bash global + réseau + écriture.
- Pour les packages, continuer à utiliser Conda/Bun dans l'environnement isolé et garder l'audit dépendances.

## Ce qu'il ne faut pas reprendre tel quel

- Les skills de connecteurs marketplace hors besoin projet, par exemple Gmail, Slack, Twilio, Vercel, etc.
- Les prompts trop longs qui chargent tout le corpus en contexte.
- Les hooks bloquants trop génériques qui empêchent le travail normal.
- Les skills qui confondent review, orchestration, auto-fix et arbitrage utilisateur.
- Les caches de plugins comme source canonique.

## Proposition de roadmap

### P9 — Trigger metadata v2

Livrable :

- Étendre `skill/triggers/*.md` avec des champs optionnels `promptSignals`, `pathPatterns`, `bashPatterns`, `toolPatterns`.
- Adapter `scripts/validate.ts` pour valider ces champs sans casser Phase 1.
- Adapter `scripts/gen-skill-docs.ts` pour afficher ces signaux de manière compacte.
- Ajouter tests unitaires.

Critère d'acceptation :

- Les 5 triggers existants restent valides.
- Le `SKILL.md` généré reste court et ne pousse pas à charger les 18 checks d'un coup.

### P10 — Review evidence schema

Livrable :

- Ajouter un schéma minimal pour `evidence_state`.
- Renforcer `on_review_claim` et `E_llm_hallucination`.
- Documenter le mapping vers les reviews multi-LLM.

Critère d'acceptation :

- Un finding avec `file:line` sans lecture courante doit être dégradé en question ouverte.
- Un sign-off sans preuve fraîche doit être refusé par la discipline de sortie.

### P11 — Skill eval harness

Livrable :

- Créer une première boucle d'évaluation A/B locale sur fixtures plantées.
- Comparer baseline `SKILL.md` vs variante.
- Produire un résultat machine lisible : score, verdict, raisons, artefacts.

Critère d'acceptation :

- Le harness doit pouvoir dire "variante meilleure", "baseline meilleure" ou "inconclusif".
- Les métriques doivent être inspectables et non seulement un jugement LLM.

### P12 — Orchestration cross-review

Livrable :

- Ajouter un contrat de synthèse qui garde séparés les findings bruts Opus/Sonnet/GPT-5.5/Kimi.
- Définir la déduplication finale et les contradictions.
- Préparer `findings_machine.json` sans remplacer les notes Markdown humaines.

Critère d'acceptation :

- Aucun avis individuel n'est écrasé par la synthèse.
- Les contradictions restent visibles jusqu'à arbitrage Zack.

## Avis GPT-5.5

La meilleure adaptation n'est pas d'importer des skills. C'est d'importer des mécanismes :

- déclenchement contextuel plus robuste,
- preuve avant conclusion,
- séparation raw/synthèse,
- évaluation A/B,
- sécurité d'installation et de dépendances.

La priorité pratique est P9 puis P10. P11 vient ensuite pour préparer Meta-Harness/ASI-Evolve proprement. P12 peut avancer en parallèle avec Opus/Sonnet/Kimi, mais ne doit pas bloquer l'amélioration des triggers.

## Points à faire valider

- Zack : valider si P9/P10 deviennent la suite directe après P8 ou si on garde P8 sign-off avant toute extension.
- Opus 4.7 : vérifier que cette roadmap ne dilue pas le rôle d'orchestration existant.
- Sonnet : review ligne-par-ligne des nouveaux champs de trigger avant implémentation.
- Kimi : valider que le schéma evidence/synthèse conserve l'indépendance des findings bruts.
