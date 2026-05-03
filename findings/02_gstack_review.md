# Revue de gstack — sécurité + couverture vs catalogue

**Repo** : https://github.com/garrytan/gstack (cloné dans `gstack/`)
**Auteur** : Garry Tan (président YC)
**Licence** : MIT
**Date de revue** : 2026-05-03
**Reviewer** : Claude Opus 4.7 (supervision stratégique + orchestrateur)

---

## 1. Audit sécurité — VERDICT : SAIN, INSTALLATION AUTORISÉE

### Patterns sécurité positifs observés

- `setup` : `set -e` + `umask 077` (restrictions fichiers owner-only)
- **Aucune installation auto** de Bun. Si Bun absent, le script affiche un message recommandant l'installation manuelle **avec vérification SHA256**, puis exit.
- Tous les `eval "$(...)"` évaluent la sortie de **binaires locaux** (`gstack-slug`), jamais une URL distante.
- Test `test/audit-compliance.test.ts:63` vérifie explicitement l'absence de patterns `curl|bash` non-vérifiés dans les messages.
- Skills s'installent dans `~/.claude/skills/`, `~/.codex/skills/`, `~/.factory/skills/`, etc. — pas de touch hors de `$HOME`.
- Stack de sécurité multicouches contre prompt injection (`browse/src/security-classifier.ts`) :
  - L1-L3 : datamarking + hidden-element strip + ARIA regex + URL blocklist + envelope wrapping
  - L4 : TestSavantAI ONNX classifier (112MB)
  - L4b : Claude Haiku transcript classifier
  - L5 : canary tokens
  - L6 : ensemble verdict combiner
- `~/.gstack/security/attempts.jsonl` — log des tentatives bloquées, salted SHA256 + domain seulement
- WebSocket auth via `Sec-WebSocket-Protocol` (pas cookies), avec dual-token model

### Patterns à connaître mais non bloquants

- `scripts/setup-scc.sh:44` fait un `sudo pacman -S` (install d'un linter de comptage de lignes). Optionnel.
- Compiled binaries `browse/dist/browse` et `design/dist/design` (~58MB chacun, Mach-O arm64). CLAUDE.md du repo dit qu'ils sont *trackés par erreur historique* et ne fonctionnent que sur Mac arm64 — `setup` rebuild from source de toute façon.
- Configuration ngrok pour tunnels (`pair-agent`) — désactivable, séparation listeners locale/tunnel avec allowlist.

### Conclusion sécurité

Code public, MIT, signé par une figure publique vérifiable. Patterns de sécurité explicites et défensifs. **Aucun signal malveillant détecté.** Installation et adoption sans risque pour notre projet.

---

## 2. Couverture des 18 familles du catalogue

### Légende
- ✅ **Fort** : adressé directement avec patterns concrets
- ⚠️ **Partiel** : adressé indirectement ou seulement pour un sous-cas
- ❌ **Non** : absent

| # | Famille | Notre fréq | gstack | Localisation gstack |
|---|---------|:----------:|:-----:|---------------------|
| 1 | A. Atomicité / crash-safety | 🔴 | ⚠️ | `safeUnlink/safeKill` (cleanup) ; pas d'atomic-write helper |
| 2 | B. Cascade `main()` returns 0 | 🔴 | ⚠️ | `/investigate` "Iron Law: no fixes without root cause" |
| 3 | D. Erreurs sémantiques d'itération | 🔴 | ⚠️ | `/review` Pass 1 "Enum & Value Completeness" |
| 4 | E. Hallucination LLM | 🔴 | ✅ | `review/checklist.md:66` *"use Grep to find all references… Read each match… requires reading code OUTSIDE the diff"* + ETHOS "Search before building" |
| 5 | J. Couverture tests insuffisante | 🔴 | ✅ | `review/specialists/testing.md` parallèle + `/qa` + `/qa-only` |
| 6 | C. Scan-loop crash sur item unique | 🟠 | ❌ | — |
| 7 | F. Race conditions | 🟠 | ✅ | `review/checklist.md:44-49` "Race Conditions & Concurrency" Pass 1 |
| 8 | G. Filtrage / shell incomplet | 🟠 | ✅ Python ⚠️ Bash | `review/checklist.md:56-59` "Shell Injection (Python-specific)" |
| 9 | H. Override silencieux user intent | 🟠 | ⚠️ | "LLM Output Trust Boundary" couvre LLM→DB, pas user-explicit-override |
| 10 | I. Destruction irréversible | 🟠 | ✅✅ | `/careful` + `/guard` + `/freeze` — guardrails pré-`Bash` sur `rm -rf`, `DROP TABLE`, force-push, `git reset --hard`, `kubectl delete` |
| 11 | K. Architecture / layering smells | 🟠 | ⚠️ | `review/specialists/maintainability.md` + `/devex-review` |
| 12 | L. Erreurs Bash spécifiques | 🟠 | ❌ | gstack très Web/Python-orienté |
| 13 | M. Drift detection / persistance | 🟡 | ⚠️ | `/canary` post-deploy monitoring |
| 14 | N. Validation d'inputs | 🟡 | ⚠️ | `review/checklist.md:50-54` "LLM Output Trust Boundary" : email regex, URL parse, allowlist SSRF |
| 15 | O. Intrusives / non-portables | 🟡 | ❌ | — |
| 16 | P. Contracts incohérents | 🟡 | ✅ | `review/specialists/api-contract.md` + "Type Coercion at Boundaries" |
| 17 | Q. Précision numérique | ⚪ | ❌ | hors scope gstack |
| 18 | R. Audit trail / transformations | 🟡 | ❌ | — |

**Score global** : ~10/18 familles couvertes (6 fortes, 5 partielles), **manque les 6-7 patterns Python/CLI/scientifiques** spécifiques à nos repos sources.

---

## 3. Patterns que gstack ajoute (intéressants à intégrer)

Présents dans gstack mais ABSENTS de notre catalogue initial — à considérer pour enrichir :

| # | Pattern gstack | Source | Intérêt pour nos projets |
|---|----------------|--------|--------------------------|
| G1 | **slop-scan** intégré | `slop-scan.config.json` + `bun run slop` | Détecte empty catches autour file ops, `return await` redondants, exception untyped |
| G2 | **LLM Output Trust Boundary** | `review/checklist.md:50-54` | Validation format email/URL générés par LLM avant DB, allowlist SSRF |
| G3 | **Time Window Safety** | `review/checklist.md:95-97` | Date-key lookups supposant "today" = 24h |
| G4 | **Type Coercion at Boundaries** | `review/checklist.md:99-101` | Hash digest mismatch JSON↔JS sur types numérique vs string |
| G5 | **LLM Prompt Issues** | `review/checklist.md:84-87` | Listes 0-indexed dans prompts (LLMs renvoient 1-indexed), token-limits qui driftent |
| G6 | **Distribution & CI/CD** | `review/checklist.md:108-114` | Secrets `${{secrets.X}}` non hardcodés, version tag format |
| G7 | **Fix-First Heuristic** | `review/checklist.md:144-167` | Règle AUTO-FIX vs ASK selon réversibilité + sévérité |
| G8 | **Two-pass review** | `review/checklist.md:36-119` | CRITICAL d'abord (5 cats), INFORMATIONAL ensuite, SPECIALIST en parallèle |
| G9 | **Suppressions explicites** | `review/checklist.md:170-180` | Liste "DO NOT flag" pour réduire le bruit |
| G10 | **Prompt injection multicouches** | `browse/src/security-classifier.ts` | Canary + ML classifier + transcript classifier ensemble |
| G11 | **Fix-First Bisect commits** | `gstack/CLAUDE.md` | Chaque commit = un changement logique, indépendamment revertable |
| G12 | **Compression effort table** | `gstack/CLAUDE.md` | Tableau human-team vs CC+gstack pour estimation honnête |

---

## 4. Patterns que NOTRE catalogue a et que gstack RATE

Lacunes spécifiques pour nos projets (Python/CLI/forensic/scientific) :

1. **Atomic-write `tmp+rename`** sur fichiers d'état JSON (pattern systémique chez Zack, absent du checklist gstack)
2. **`main()` returns 0 sur cascade** d'étapes silencieuses (Kimi C1 + Sonnet E1)
3. **Scan-loop sans `try/except` par item** (un YAML corrompu kill toute la boucle E3)
4. **"latest" qui est en fait "first"** sémantique d'itération (F1)
5. **Race conditions sur IDs basés timestamp seconde** sans microsecondes/random (G1)
6. **Shell control tokens `>`, `<`, `>>`, `>&`** filtrage POSIX (gstack vise Python `subprocess shell=True`)
7. **Test bidirectionnel** (si tu testes upper, teste lower)
8. **Override silencieux d'inputs régulatoires explicites** (Wallonia/Annexe 1)
9. **Bash-spécifiques** (declare -A + pipefail, double sudo, fd 200, notify-send sans DBus, resolvectl monitor)
10. **Audit trail perdu** lors de transformations (pop catalog_id sans le préserver)
11. **Précision numérique** (t-distrib plafonné, KM left-continuous, Merkle leaves SHA256[:12])
12. **Hallucination de file:line** (E1 catalog) — gstack a la règle "Search before building" mais pas l'enforcement strict "tu as lu le fichier dans cette session ?"
13. **Refixer un bug déjà corrigé** (E2 catalog) — pas de check explicite

---

## 5. Recommandation stratégique

**À adopter de gstack** :
- L'infrastructure de skills (host configs, gen-skill-docs, validation framework)
- Le format `SKILL.md` + `.tmpl` (templating qui régénère)
- `/careful`, `/guard`, `/freeze` — destructive command guardrails
- Le pattern two-pass review + specialist subagents
- Le slop-scan + sa philosophie "AI quality, not AI hiding"
- Le Fix-First Heuristic
- Les Suppressions explicites

**À NE PAS adopter tel quel** :
- Le checklist `/review` qui est très Rails/Django/Prisma — il faut une variante Python/CLI/scientific
- L'ETHOS personnel de Garry Tan (philosophical fit, à adapter)
- Les skills business/CEO (`/office-hours`, `/plan-ceo-review`) — pas notre cas

**Move recommandé** : prendre gstack comme **socle de plomberie** (infrastructure de skills, hooks, registration, slop-scan, prompt-injection guards), et y greffer **3-5 skills custom** pour les patterns non-couverts (atomic-state, scan-safe, bidir-test, no-phantom-cite, bash-safe).

---

*Document produit le 2026-05-03 dans le cadre de la revue stratégique. Mise à jour à prévoir si gstack publie une version majeure.*
