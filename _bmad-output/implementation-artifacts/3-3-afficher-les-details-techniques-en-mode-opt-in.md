# Story 3.3: Afficher les details techniques en mode opt-in

> Note 2026-03-14: artefact BMAD historique. Certaines references internes
> (tests, modules, `criteria`, hot reload, pages playground) peuvent ne plus
> correspondre exactement au depot courant. Pour l'etat actuel, se fier a
> `README.md`, `docs/ARCHITECTURE.md` et `docs/ANALYSIS_PROFILES_METIER.md`.


Status: review

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a decideur technique,
I want consulter les details techniques de l analyse uniquement quand j en ai besoin,
so that je gagne en confiance sans surcharger l interface principale.

## Acceptance Criteria

1. **Given** un resultat d analyse est disponible **When** l utilisateur ouvre le panneau de details **Then** les informations techniques pertinentes s affichent (modele utilise, prompt utilise, latence, tokens, contexte detecte si disponible) **And** le panneau est ferme par defaut.
2. **Given** certaines metadonnees ne sont pas fournies par l API **When** le panneau est affiche **Then** l UI degrade proprement sans erreur **And** seuls les champs disponibles sont montres.
3. **Given** l utilisateur alterne analyses et ouverture ou fermeture du panneau **When** un nouveau resultat arrive **Then** les details affiches correspondent au dernier appel **And** aucune ancienne valeur stale n est conservee visuellement.
4. **Given** l utilisateur n ouvre pas le panneau **When** il utilise le Playground en mode standard **Then** le flux principal reste simple et rapide **And** la comprehension du resultat ne depend pas des details techniques.
5. **Given** un contexte auto est applique cote backend **When** `profile_used` et `routing_confidence` sont presents **Then** ces informations sont visibles dans le panneau **And** elles sont formatees de facon lisible pour revue integration.

## Tasks / Subtasks

- [x] Ajouter un panneau de details techniques opt-in dans le Playground (AC: 1, 4)
  - [x] Utiliser un composant de type `ui.expansion` ferme par defaut dans `playground/src/playground/components.py`
  - [x] Garder la hierarchie principale `score -> decision -> justification` intacte hors panneau
- [x] Etendre le schema playground pour supporter les metadonnees techniques optionnelles (AC: 1, 2, 5)
  - [x] Ajouter dans `playground/src/api_client/schemas.py` les champs optionnels `model_used`, `latency_sec`, `tokens_in`, `tokens_out`, `routing_confidence`
  - [x] Mapper ces champs dans `playground/src/api_client/client.py` sans casser la compatibilite payload minimal
- [x] Afficher uniquement les metadonnees disponibles et formater proprement (AC: 2, 5)
  - [x] Ne pas afficher de placeholders trompeurs si un champ est absent
  - [x] Formater `routing_confidence` avec precision lisible (ex: 0.83) et latence en secondes
- [x] Garantir la coherence sur analyses consecutives (AC: 3)
  - [x] Re-rendre le contenu du panneau depuis `state.last_result` a chaque succes API
  - [x] Verifier qu aucune valeur precedente ne persiste quand la nouvelle reponse ne contient pas un champ
- [x] Ajouter les tests playground cibles pour AC1-AC5
  - [x] Tests de rendu panneau ferme par defaut puis ouvrable
  - [x] Tests de degradation propre avec metadonnees partielles
  - [x] Tests de remplacement complet des details sur analyses successives
  - [x] Tests de visibilite `profile_used` + `routing_confidence` en mode auto

## Dev Notes

- Story 3.3 etend 3.2 sans changer le coeur UX: le resultat principal reste immediat et lisible, les details restent facultatifs.
- L implementation doit prevenir la reinvention: reutiliser le flux existant `ApiClient -> PlaygroundState -> render` sans pipeline parallele.
- Le but est la confiance technique pour decideurs/integrateurs, sans bruit pour les utilisateurs qui ne consultent pas le panneau.

### Developer Context Section

- **Contexte Epic 3:** experience Playground demonstrable, avec feedback interpretable et transparence progressive.
- **Valeur business 3.3:** augmenter la credibilite technique (integration/revue) sans degradations de simplicite pour les usages standards.
- **Dependance amont:** 3.2 a verrouille le panneau principal et son rendu stable; 3.3 ne doit pas casser ce contrat.
- **Dependance aval:** 3.4 capitalisera sur ce socle pour loading/erreurs/preservation de saisie avec comportement robuste.

### Technical Requirements

- Conserver le pattern actuel de soumission: `_handle_submit` met a jour `state.last_result`, puis rend l UI.
- Etendre `AnalyzeResult` playground avec champs optionnels deja exposes par backend (`model_used`, `latency_sec`, `tokens_in`, `tokens_out`, `routing_confidence`, `profile_used`).
- Afficher des details uniquement si disponibles, sans exception ni mecanisme retire incoherent.
- Rendre le panneau de details independant de la comprehension principale: aucune information critique AC 3.2 ne doit migrer dedans.
- Eviter toute logique metier dans le playground: le panneau presente la telemetrie et la resolution deja calculees par l API.

### Architecture Compliance

- Respecter la frontiere de transport via `playground/src/api_client/client.py` uniquement.
- Maintenir etat local page-level (`PlaygroundState`) sans store global ni event bus.
- Garder conventions `snake_case` pour champs JSON et code Python.
- Respecter l organisation feature-first existante (`playground/*`, `api_client/*`, tests miroirs).

### Library/Framework Requirements

- NiceGUI/Quasar: utiliser `ui.expansion` pour progressive disclosure, ferme par defaut.
- FastAPI/Pydantic: ne pas modifier le contrat backend dans cette story; seulement consommer ses champs optionnels.
- HTTP client playground: conserver strategie actuelle basee sur `urllib` et mapping defensif.

### File Structure Requirements

- Fichiers playground cibles:
  - `playground/src/playground/components.py`
  - `playground/src/playground/page.py`
  - `playground/src/playground/state.py`
  - `playground/src/playground/actions.py`
- Fichiers API client cibles:
  - `playground/src/api_client/schemas.py`
  - `playground/src/api_client/client.py`
- Tests cibles:
  - `playground/tests/test_playground_components.py`
  - `playground/tests/test_playground_page_submission.py`

### Testing Requirements

- AC1: verifier que le panneau details est ferme par defaut et expose les champs techniques quand ouvert.
- AC2: verifier que les payloads partiels n entrainent pas d erreur et n affichent que les champs presents.
- AC3: verifier remplacement complet des details lors d analyses consecutives.
- AC4: verifier que le panneau principal reste autonome et comprehensible sans ouvrir les details.
- AC5: verifier affichage lisible de `profile_used` et `routing_confidence` quand routage auto actif.

### Previous Story Intelligence

- 3.2 a etabli la structure stable du panneau principal dans `components.py` avec placeholders initiaux et ordre fixe.
- 3.2 a centralise le mapping decision/couleur via `get_decision_color`; conserver ce pattern pour eviter duplications.
- 3.2 a deja des tests de remplacement de resultat et payload minimal; etendre ces tests au panneau details plutot que recreer un nouveau harness.
- Les completion notes 3.2 confirment une mise a jour atomique du resultat; reutiliser ce comportement pour eliminer les valeurs stale en details.

### Git Intelligence Summary

- `3d60705` (story 3.2) montre que les zones de changement front legitimes sont `playground/src/playground/*` et tests associes.
- `fefde74` (story 3.1) montre que `api_client/schemas.py` et `api_client/client.py` sont deja les points d extension du contrat API pour UI.
- Les stories 2.3-2.5 ont enrichi les metadonnees backend; 3.3 doit les exploiter cote UI sans toucher la logique metier backend.
- Pattern equipe etabli: mise a jour story artifact + sprint status + tests dans le meme increment.

### Latest Tech Information

- FastAPI `0.129.0` introduit un changement majeur: Python 3.9 retire; rester sur Python >=3.10. [Source: https://fastapi.tiangolo.com/release-notes/]
- Pydantic `2.12.5` est la baseline stable de patch de la serie 2.12.x. [Source: https://docs.pydantic.dev/latest/changelog/]
- Uvicorn `0.40.0` retire Python 3.9; alignement runtime backend requis. [Source: https://uvicorn.dev/release-notes/]
- NiceGUI `3.7.1` est la version recente; la serie 3.7.0 inclut des correctifs securite (XSS/path traversal), donc eviter versions precedentes. [Source: https://pypi.org/project/nicegui/]
- HTTPX `0.28.1` corrige un cas SSL et la serie 0.28 deprecie certains anciens usages SSL (`verify` string, `cert`). [Source: https://github.com/encode/httpx/releases]

### Project Structure Notes

- Aucun `project-context.md` detecte avec le pattern `**/project-context.md`.
- Sources principales utilisees pour cette story: `epics.md`, `architecture.md`, `prd.md`, `ux-design-specification.md`, `sprint-status.yaml`, story 3.2 et code playground courant.

### References

- Story 3.3 + AC officiels: [Source: `_bmad-output/planning-artifacts/epics.md#Story 3.3`]
- Contraintes UX details opt-in et progressive disclosure: [Source: `_bmad-output/planning-artifacts/ux-design-specification.md#Core User Experience`], [Source: `_bmad-output/planning-artifacts/ux-design-specification.md#Component Strategy`], [Source: `_bmad-output/planning-artifacts/ux-design-specification.md#UX Consistency Patterns`]
- Contrat API et metadonnees optionnelles: [Source: `_bmad-output/planning-artifacts/prd.md#API Specifications`], [Source: `backend/src/analysis/schemas.py`]
- Boundaries et structure cible: [Source: `_bmad-output/planning-artifacts/architecture.md#Project Structure & Boundaries`], [Source: `_bmad-output/planning-artifacts/architecture.md#Implementation Patterns & Consistency Rules`]
- Learnings story precedente: [Source: `_bmad-output/implementation-artifacts/3-2-afficher-le-resultat-principal-de-maniere-lisible-et-actionnable.md`]

### Story Completion Status

- Story context cree avec statut `ready-for-dev`.
- Note de completion: Ultimate context engine analysis completed - comprehensive developer guide created.

## Dev Agent Record

### Agent Model Used

openai/gpt-5.3-codex

### Implementation Plan

- Etendre le contrat playground `AnalyzeResult` et le mapping `ApiClient.analyze` pour consommer les metadonnees backend optionnelles sans casser les payloads minimaux.
- Ajouter un panneau `ui.expansion` ferme par defaut et conserver hors panneau la hierarchie principale `score -> decision -> justification`.
- Centraliser le rendu details dans `_format_technical_details` et re-rendre a chaque succes API depuis `state.last_result` pour eviter les valeurs stale.
- Couvrir AC1-AC5 avec tests de composant et tests de soumission (degradation payload partiel, remplacements consecutifs, affichage routage auto).

### Debug Log References

- Artefacts analyses: `_bmad-output/planning-artifacts/epics.md`, `_bmad-output/planning-artifacts/prd.md`, `_bmad-output/planning-artifacts/architecture.md`, `_bmad-output/planning-artifacts/ux-design-specification.md`, `_bmad-output/implementation-artifacts/sprint-status.yaml`.
- Story precedente analysee: `_bmad-output/implementation-artifacts/3-2-afficher-le-resultat-principal-de-maniere-lisible-et-actionnable.md`.
- Git intelligence: `git log --oneline -5` et `git show --name-only --pretty=format:'COMMIT %h%nTITLE %s%n' -5`.
- Veille technique: release notes/changelogs FastAPI, Pydantic, Uvicorn, NiceGUI, HTTPX.
- Verification locale: `uv run --with pytest pytest tests/test_playground_components.py tests/test_playground_page_submission.py`, `uv run --with pytest pytest`, `uv run ruff check src tests`.

### Completion Notes List

- Story 3.3 preparee avec guardrails explicites pour details techniques opt-in sans regressions UX 3.1/3.2.
- Contexte de code reel integre (schemas playground incomplets vs contrat backend enrichi) pour orienter une implementation precise.
- Exigences anti-stale, anti-duplication et tests AC1-AC5 formalisees pour fiabiliser l execution dev-agent.
- `AnalyzeResult` et `ApiClient.analyze` acceptent maintenant `model_used`, `latency_sec`, `tokens_in`, `tokens_out`, `routing_confidence` en optionnel sans casser les reponses minimales.
- Le panneau `Details techniques` est en opt-in (`ui.expansion`, ferme par defaut) et la vue principale reste `score -> decision -> justification`.
- Le rendu details est regenere a chaque analyse via `state.last_result` avec suppression implicite des champs absents pour eviter tout stale state.
- Les tests playground couvrent panneau ferme par defaut, metadata partielle, remplacement complet sur analyses successives, et visibilite `profile_used` + `routing_confidence`.

### File List

- _bmad-output/implementation-artifacts/3-3-afficher-les-details-techniques-en-mode-opt-in.md
- _bmad-output/implementation-artifacts/sprint-status.yaml
- playground/src/api_client/schemas.py
- playground/src/api_client/client.py
- playground/src/playground/components.py
- playground/src/playground/page.py
- playground/tests/test_playground_components.py
- playground/tests/test_playground_page_submission.py

### Change Log

- 2026-02-13: Implante Story 3.3 (details techniques opt-in), etend le mapping metadonnees API optionnelles, ajoute rendu anti-stale et tests AC1-AC5; statut passe a `review`.
