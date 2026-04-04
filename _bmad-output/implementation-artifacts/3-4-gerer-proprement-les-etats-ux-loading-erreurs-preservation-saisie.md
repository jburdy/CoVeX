# Story 3.4: Gerer proprement les etats UX (loading, erreurs, preservation saisie)

> Note 2026-03-14: artefact BMAD historique. Certaines references internes
> (tests, modules, `criteria`, hot reload, pages playground) peuvent ne plus
> correspondre exactement au depot courant. Pour l'etat actuel, se fier a
> `README.md`, `docs/ARCHITECTURE.md` et `docs/ANALYSIS_PROFILES_METIER.md`.


Status: review

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a utilisateur operationnel,
I want que l interface reste claire et robuste pendant les chargements et en cas d erreur API,
so that je puisse continuer sans perdre mon travail.

## Acceptance Criteria

1. **Given** une analyse est en cours **When** l utilisateur a clique sur `Analyser` **Then** le bouton principal passe en etat de chargement ou desactivation **And** les doubles soumissions involontaires sont evitees.
2. **Given** une erreur API survient (`400`, `404`, `500`, `503`) **When** la reponse d erreur est recue **Then** un message utilisateur court et explicite est affiche **And** aucune stack trace technique n apparait dans l UI.
3. **Given** une indisponibilite temporaire du service **When** l erreur est presentee a l utilisateur **Then** l interface propose implicitement une action de reprise (corriger ou reessayer) **And** la saisie texte courante est conservee.
4. **Given** une erreur survient apres des resultats precedents valides **When** l UI se met a jour **Then** l etat d erreur est visible sans casser la structure de la page **And** la prochaine analyse peut etre relancee sans rafraichir l application.
5. **Given** un retour a la normale apres erreur **When** une nouvelle analyse reussit **Then** l etat d erreur est nettoye correctement **And** le resultat courant s affiche normalement.

## Tasks / Subtasks

- [x] Fiabiliser l etat de soumission pendant l appel API (AC: 1)
  - [x] Ajouter un garde-fou `if state.is_submitting: return` en entree de `_handle_submit` pour bloquer les doubles clics tres rapides
  - [x] Conserver la desactivation explicite de `submit_button` pendant l analyse et la reactivation garantie en `finally`
  - [x] Maintenir un feedback utilisateur court en cours de traitement (`Analyse en cours...`) sans casser le layout
- [x] Introduire une gestion d erreurs UX explicite par classe d erreur API (AC: 2, 4)
  - [x] Etendre `ApiClientError` pour exposer le code HTTP et/ou une categorie d erreur exploitable par l UI
  - [x] Mapper `400/404/500/503` vers des messages courts, actionnables et non techniques dans `playground/page.py`
  - [x] Garantir qu aucune stack trace brute n est affichee cote UI
- [x] Preserver la saisie et permettre une reprise immediate (AC: 3, 4)
  - [x] Verifier que `state.text` n est jamais reinitialise sur erreur
  - [x] Laisser l utilisateur corriger le texte ou relancer immediatement sans rafraichissement
  - [x] Conserver la structure principale de la page meme en etat d erreur
- [x] Assurer le retour propre a l etat nominal apres erreur (AC: 5)
  - [x] Nettoyer l etat d erreur des qu une analyse suivante reussit
  - [x] Rafraichir completement le rendu resultat avec la derniere reponse API (sans valeurs stale)
  - [x] Conserver la hierarchie UX stable `score -> decision -> justification -> details`
- [x] Couvrir AC1-AC5 avec des tests front cibles
  - [x] Ajouter des tests de non double-soumission et de desactivation/reactivation bouton
  - [x] Ajouter des tests de mapping des erreurs `400/404/500/503` vers messages UX
  - [x] Ajouter des tests de preservation saisie apres erreur et reprise sans reload
  - [x] Ajouter des tests de transition erreur -> succes avec nettoyage d etat

## Dev Notes

- Story 3.4 est la couche de robustesse UX de l Epic 3: elle ne cree pas de nouvelle logique metier, elle fiabilise le flux deja pose par 3.1 (saisie/submit), 3.2 (resultat principal) et 3.3 (details opt-in).
- Le risque principal a prevenir est la regression UX: bouton non reactive, message flou, perte de saisie, ou etat stale apres erreurs consecutives.
- L implementation doit rester minimale et deterministe: etat local page-level, messages courts, aucune orchestration globale.

### Developer Context Section

- Contexte Epic 3: Story 3.4 couvre la robustesse operationnelle du Playground avant la story 3.5 (responsive/a11y), avec priorite a la continuite d usage en cas d erreur API.
- Valeur metier: reduire la friction demo/utilisateur en garantissant un cycle court `analyser -> corriger/reessayer` sans perte de travail.
- Dependances amont:
  - 3.1 a etabli `prepare_submission` + payload `Auto`/`profile_id`.
  - 3.2 a fixe la hierarchie d affichage `score/decision/justification`.
  - 3.3 a ajoute les details techniques opt-in et le rendu anti-stale.
- Dependance aval: 3.5 reutilisera ce comportement stable pour verifier UX mobile + navigation clavier sans effets de bord.

### Technical Requirements

- Conserver `_handle_submit` comme point unique de soumission dans `playground/src/playground/page.py`.
- Implementer un anti-double-submit (`state.is_submitting`) avant tout appel reseau.
- Etendre `ApiClientError` (`playground/src/api_client/client.py`) pour transporter au minimum `status_code` et un message brut optionnel.
- Mapper explicitement en UI:
  - `400` -> requete invalide (texte/champs)
  - `404` -> prompt introuvable
  - `503` -> service d inference indisponible (reessayer)
  - `500`/autres -> erreur interne temporaire
- Toujours conserver `state.text` et permettre une relance immediate depuis le meme ecran.
- Sur succes apres erreur, effacer le message d erreur precedent et afficher `Analyse terminee.`

### Architecture Compliance

- Respecter la frontiere `UI -> api_client -> backend` (aucun appel HTTP direct hors `api_client/client.py`).
- Garder l etat local dans `PlaygroundState` uniquement (pas de store global, pas d event bus).
- Preserver les conventions `snake_case` pour le code Python, les payloads JSON et les variables d etat.
- Ne pas modifier le contrat backend `/analyze` dans cette story: adaptation uniquement cote playground.
- Conserver succes direct + erreurs API existantes, sans envelope custom front ad hoc.

### Library/Framework Requirements

- NiceGUI/Quasar: maintenir feedback simple (label/message) et desactivation explicite du bouton durant la soumission.
- Contrat FastAPI: prendre en charge les codes `400/404/500/503` deja exposes par l API.
- Transport playground: conserver `urllib` existant avec parsing defensif des erreurs HTTP.

### File Structure Requirements

- Fichiers a modifier prioritairement:
  - `playground/src/playground/page.py`
  - `playground/src/playground/state.py` (si un champ d etat d erreur explicite est necessaire)
  - `playground/src/api_client/client.py`
  - `playground/src/api_client/schemas.py` (uniquement si besoin de typer une erreur enrichie)
- Fichiers de tests cibles:
  - `playground/tests/test_playground_page_submission.py`
  - `playground/tests/test_playground_components.py` (si impact rendu)

### Testing Requirements

- AC1: verifier que les doubles soumissions sont bloquees et que le bouton revient toujours en etat actif en sortie.
- AC2: verifier le mapping UX des erreurs `400/404/500/503` avec messages courts et sans trace technique.
- AC3: verifier la conservation de `state.text` et la possibilite de reessai immediat apres erreur.
- AC4: verifier que l erreur est visible sans casser la structure de la page et sans necessiter reload.
- AC5: verifier la transition erreur -> succes (message d erreur nettoye, resultat courant rendu normalement).

### Previous Story Intelligence

- 3.3 a confirme que le rendu resultat doit etre regenere depuis `state.last_result` a chaque succes pour eviter tout stale state.
- 3.3 a etabli un pattern de tests front robustes via faux controls (`_FakeControls`) dans `test_playground_page_submission.py`; il faut etendre ce pattern, pas en creer un nouveau.
- 3.2/3.3 utilisent deja `get_decision_color` et la hierarchie stable du panneau principal; 3.4 ne doit pas deplacer cette logique.
- Les stories precedentes montrent que la surface legitime de changement front est `playground/*` + `api_client/*` + tests associes.

### Git Intelligence Summary

- `6e5f87f` (story 3.3) a introduit details techniques opt-in et anti-stale: 3.4 doit conserver ces garanties en scenario d erreur.
- `3d60705` (story 3.2) a verrouille lisibilite du resultat principal et mapping decision/couleur.
- `fefde74` (story 3.1) a etabli le flux de soumission et l usage de `ApiClient`; toute evolution d erreurs doit rester sur cette frontiere.
- Pattern recent de l equipe: update story artifact + sprint-status + tests dans le meme increment.

### Latest Tech Information

- FastAPI: la serie recente inclut `0.129.0` avec rupture Python 3.9 (support >=3.10). [Source: https://fastapi.tiangolo.com/release-notes/]
- Uvicorn: `0.40.0` supprime aussi Python 3.9; coherence runtime backend requise. [Source: https://github.com/Kludex/uvicorn/releases]
- NiceGUI: `3.7.1` est la release recente; la serie `3.7.0` corrige des vulnerabilites (XSS/path traversal). [Source: https://pypi.org/project/nicegui/]
- HTTPX: `0.28.1` corrige un cas SSL; en `0.28`, deprecations SSL (`verify` string / `cert`) a connaitre si evolution transport future. [Source: https://github.com/encode/httpx/releases]

### Project Structure Notes

- Aucun `project-context.md` trouve via le pattern `**/project-context.md`.
- Structure observee conforme aux stories precedentes: front sous `playground/src/playground/*` et transport sous `playground/src/api_client/*`.
- Pas de conflit structurel detecte pour 3.4; l implementation doit rester dans ces modules pour limiter les regressions.

### References

- Story 3.4 officielle et AC: [Source: `_bmad-output/planning-artifacts/epics.md#Story 3.4`]
- Contraintes UX erreurs/loading/preservation: [Source: `_bmad-output/planning-artifacts/ux-design-specification.md#Flow Optimization Principles`], [Source: `_bmad-output/planning-artifacts/ux-design-specification.md#UX Consistency Patterns`]
- Contraintes architecture (etat local, frontieres): [Source: `_bmad-output/planning-artifacts/architecture.md#Implementation Patterns & Consistency Rules`], [Source: `_bmad-output/planning-artifacts/architecture.md#Project Structure & Boundaries`]
- Contrat API et erreurs attendues: [Source: `_bmad-output/planning-artifacts/prd.md#API Specifications`], [Source: `backend/src/analysis/api.py`]
- Learnings story precedente: [Source: `_bmad-output/implementation-artifacts/3-3-afficher-les-details-techniques-en-mode-opt-in.md`]

### Story Completion Status

- Story context cree avec statut `ready-for-dev`.
- Note de completion: Ultimate context engine analysis completed - comprehensive developer guide created.

## Dev Agent Record

### Agent Model Used

openai/gpt-5.3-codex

### Debug Log References

- Artefacts analyses: `_bmad-output/planning-artifacts/epics.md`, `_bmad-output/planning-artifacts/prd.md`, `_bmad-output/planning-artifacts/architecture.md`, `_bmad-output/planning-artifacts/ux-design-specification.md`, `_bmad-output/implementation-artifacts/sprint-status.yaml`.
- Story precedente analysee: `_bmad-output/implementation-artifacts/3-3-afficher-les-details-techniques-en-mode-opt-in.md`.
- Git intelligence: `git log --oneline -5` et `git show --name-only --pretty=format:'COMMIT %h%nTITLE %s%n' -5`.
- Veille technique: releases/changelogs FastAPI, Uvicorn, NiceGUI, HTTPX.

### Implementation Plan

- Introduire une garde d entree dans `_handle_submit` pour bloquer toute double soumission quand `state.is_submitting` est deja actif.
- Etendre `ApiClientError` avec `status_code` et `raw_message`, puis enrichir la capture `HTTPError` avec extraction defensive de `detail` JSON.
- Mapper explicitement les erreurs `400/404/500/503` en messages UX courts dans `playground/page.py` sans exposer de details techniques.
- Conserver le cycle UX existant (`Analyse en cours...`, reactivation bouton en `finally`, rendu resultat stable) et verifier la reprise immediate apres erreur.
- Etendre les tests front pour couvrir AC1-AC5 sur double soumission, mapping erreurs, preservation saisie et transition erreur -> succes.

### Completion Notes List

- Story 3.4 preparee comme guide d implementation centree robustesse UX (loading + erreurs + preservation saisie) sans changement de logique metier core.
- Guardrails anti-regression explicites pour conserver les acquis 3.1/3.2/3.3.
- Couverture de tests ciblee AC1-AC5 definie pour eviter les regressions silencieuses sur le flux de soumission.
- Implementation `_handle_submit` renforcee avec garde anti-double-submit, maintien du feedback `Analyse en cours...` et reactivation bouton garantie via `finally`.
- `ApiClientError` expose maintenant `status_code`/`raw_message`; les erreurs HTTP conservent le code pour permettre un mapping UX deterministe cote UI.
- Mapping UX implemente: `400` requete invalide, `404` prompt introuvable, `503` indisponibilite temporaire, `500/autres` erreur interne temporaire; aucune trace technique affichee.
- Tests front AC1-AC5 ajoutes et verifies, dont preservation de `state.text` apres erreur et reprise immediate sans rechargement.
- Validation complete executee: `uv run pytest` (backend: 98 passed), `uv run ruff check src tests` (backend OK), `uv run --with pytest pytest` (playground: 15 passed), `uv run --with ruff ruff check src tests` (playground OK).

### File List

- _bmad-output/implementation-artifacts/3-4-gerer-proprement-les-etats-ux-loading-erreurs-preservation-saisie.md
- _bmad-output/implementation-artifacts/sprint-status.yaml
- playground/src/api_client/client.py
- playground/src/playground/page.py
- playground/tests/test_playground_page_submission.py

## Change Log

- 2026-02-13: Story 3.4 implementee (robustesse UX loading/erreurs/reprise), couverture de tests AC1-AC5 completee et statut passe a `review`.
