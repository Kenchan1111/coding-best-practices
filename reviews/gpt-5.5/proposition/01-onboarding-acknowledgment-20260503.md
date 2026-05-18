---
id: gpt-5.5-proposition-01-20260503
title: Prise en charge GPT-5.5 et positions initiales sur l'architecture Phase 1
date: 2026-05-03
status: proposed
agent: gpt-5.5
review_kind: proposition
target_agent: claude-opus
scope: onboarding, architecture, todos, phase-1 sequencing
synopsis: >
  Note de prise en charge après lecture des documents canoniques du projet.
  Elle fixe la compréhension du rôle GPT-5.5, les points validés, les points
  qui demandent arbitrage Zack, et la position stratégique sur D1-D6 et Q1-Q5.
sources:
  - CLAUDE.md
  - findings/01_bug_catalog.md
  - findings/02_gstack_review.md
  - findings/03_methodology.md
  - ARCHITECTURE.md
  - TODOS.md
  - ONBOARDING_GPT55.md
---

# Validation effectuée

Lu dans cette session :
- `CLAUDE.md`
- `findings/01_bug_catalog.md`
- `findings/02_gstack_review.md`
- `findings/03_methodology.md`
- `ARCHITECTURE.md`
- `TODOS.md`
- `ONBOARDING_GPT55.md`

Vérifications d'état repo :
- `git status --short` → `fatal: not a git repository (or any of the parent directories): .git`
- `ls -la .git` → répertoire présent mais vide
- `find skill -maxdepth 2` → `skill/` existe déjà mais n'est pas encore scaffoldé

# Findings de prise en charge

## Ce que je valide

1. Le split des rôles est plus propre que la version précédente. La règle "GPT-5.5 compte pour la convergence seulement quand il review autre chose que sa propre impl" est saine.
2. Le backlog P0 → P8 est cohérent. Le vrai verrou est P0, pas le scaffolding.
3. Le catalogue a assez de densité pour justifier une skill contextuelle, pas un simple checklist statique.
4. Le move "prendre gstack comme plomberie, pas comme contenu métier" est le bon niveau de réutilisation.

## Ce que je questionne

1. `D5` en mode symlink pur fragilise la portabilité Phase 1. Une skill installée hors de ce repo doit rester autonome.
2. `D6` en mode purement statique est trop faible pour le sign-off final. Le projet prévoit déjà une démo E2E en `P7`. Il faut l'assumer comme exigence minimale de fin de phase.
3. Le workflow git documenté suppose un repo initialisé, alors que l'état réel est un `.git/` vide. Il faut régler `Q4` avant de parler de branches, PRs et bisect commits.

## Ce qui manque encore

1. Une décision explicite sur la forme de vérité du catalogue en Phase 1 : markdown libre enrichi ou markdown généré depuis un index structuré.
2. Une règle de numérotation des fichiers de review quand plusieurs agents déposent des notes le même jour. Le risque est faible, mais la convention gagnerait à être explicitée.
3. Une clarification sur la publication externe. Le choix de licence dépend du moment où le repo sort du statut de chantier privé.

# Décisions D1-D6

## D1 — Réutiliser gstack comme socle ?

Position : **oui, cherry-pick minimal, pas fork**.

Justification :
- Le repo a besoin de la plomberie, pas de l'idéologie complète de gstack.
- Le scope utile en Phase 1 est limité : `gen-skill-docs`, patterns `hosts/`, validation, et inspiration setup.
- Un fork complet augmente la surface de drift, le bruit review, et le coût de maintenance sans aider le catalogue métier.

Décision concrète proposée :
- Réutiliser `scripts/gen-skill-docs.ts`
- S'inspirer de `hosts/` et du `setup`
- Ne pas embarquer les skills gstack non pertinentes

## D2 — 18 fichiers checks ou 78 ?

Position : **18 fichiers par famille**, avec IDs stables `A1...R2` à l'intérieur.

Justification :
- 78 fichiers ferait exploser le coût éditorial sans gain clair en Phase 1.
- Les reviewers et futurs utilisateurs pensent d'abord en familles, puis en sous-patterns.
- Les IDs stables internes suffisent pour migrer vers une structure plus fine plus tard.

## D3 — Auto-fix en Phase 1 ?

Position : **oui, uniquement pour les fixes mécaniques, réversibles, à faible ambiguïté**.

Justification :
- C'est aligné avec le Fix-First Heuristic.
- Les familles `A`, `L` et certains cas de `J` se prêtent à des suggestions ou patches mécaniques.
- Tout ce qui change le comportement métier, les contrats, ou le sens statistique doit rester en `ASK`.

Règle pratique proposée :
- Auto-fix si le patch est local, lisible, et ne change pas l'intent fonctionnel
- Sinon, surface le check et demande confirmation

## D4 — Portabilité multi-LLM dès Phase 1 ?

Position : **portabilité d'artefact oui, parité comportementale non**.

Justification :
- Le repo peut viser Claude Code en premier tout en gardant une arborescence compatible `~/.claude/skills/` et `~/.codex/skills/`.
- ChatGPT custom GPT et Kimi demandent un travail de packaging/runtime différent. Les promettre dès Phase 1 dilue le focus.

Décision concrète proposée :
- Phase 1 : Claude prioritaire, Codex compatible par layout/setup
- Phase 2 : adapters plus actifs pour autres hôtes

## D5 — Symlink ou copie du catalogue ?

Position : **source de vérité dans `findings/`, copie générée dans `skill/catalog/`**.

Justification :
- Le symlink est pratique en monorepo, mais mauvais pour la portabilité et l'installation autonome.
- Une copie générée garde une source unique tout en produisant un artefact distribuable.
- Cela évite les surprises si la skill est symlinkée dans `~/.claude/skills/` ou `~/.codex/skills/`.

Décision concrète proposée :
- `findings/01_bug_catalog.md` reste source
- un script génère `skill/catalog/bug_catalog.md` ou une vue structurée équivalente
- les IDs stables restent inchangés

## D6 — Validation statique ou dynamique ?

Position : **statique comme gate de développement, plus un smoke test dynamique obligatoire avant acceptation**.

Justification :
- La validation statique seule ne dit pas si les triggers surfacent réellement les bons checks.
- Le projet a déjà prévu une démo E2E. Il faut la traiter comme critère d'acceptation, pas comme bonus.

Décision concrète proposée :
- `validate` + tests unitaires pendant l'implémentation
- 1 fixture plantée minimale obligatoire avant `accepted`
- pas de matrice dynamique large en Phase 1

# Q1-Q5 — recommandations pour Zack

## Q1 — Nom final de la skill

Recommandation : **garder `coding-best-practices` en Phase 1**.

Raison :
- C'est descriptif, neutre, et déjà présent dans toute la doc.
- Renommer maintenant crée du churn sans bénéfice produit.

## Q2 — Repo séparé ou monorepo ?

Recommandation : **monorepo pour toute la Phase 1**.

Raison :
- Le catalogue, l'architecture, les reviews et la skill évoluent ensemble.
- Séparer trop tôt casse la traçabilité entre findings et implémentation.

## Q3 — Licence

Recommandation : **privée pendant la Phase 1, décision de publication ensuite**.

Raison :
- Le repo est encore en chantier méthodologique.
- Il vaut mieux figer le contenu et clarifier la provenance des éléments réutilisés avant de publier.

## Q4 — `git init` autorisé ?

Recommandation : **oui, et tôt**, après validation Zack.

Raison :
- La discipline de branches, commits bisectables et PRs n'est pas réelle sans repo git.
- L'état actuel montre un `.git/` vide. Il faut le transformer en vrai repo avant de démarrer P1.

## Q5 — Premier projet de démo E2E

Recommandation : **fixture plantée ad hoc d'abord, `Depollution_Sols` ensuite seulement**.

Raison :
- Une fixture contrôlée isole la qualité de la skill.
- Tester d'abord sur `Depollution_Sols` mélange signal outil et bruit domaine.

# Premier livrable proposé

Si Zack valide `Q1-Q5` dans le sens ci-dessus, mon premier livrable de code sera :

1. `P1` scaffolding complet de `skill/`
2. `SKILL.md.tmpl` minimal
3. `README.md` d'installation et périmètre
4. squelette `hosts/claude.md` et `hosts/codex.md`
5. stratégie `catalog/` en copie générée depuis `findings/01_bug_catalog.md`

Branche proposée après `git init` :
- `feature/skill-phase1-scaffolding`

Commit initial proposé :
- `scaffold skill layout and generated catalog source wiring`

# Next step recommandé

1. Zack tranche `Q1-Q5`
2. Opus 4.7 synthétise `D1-D6` + `Q1-Q5` dans `reviews/global_handoff/00-architecture-decisions-20260503.md`
3. Après convergence Claude ou arbitrage Zack, démarrage `P1`
