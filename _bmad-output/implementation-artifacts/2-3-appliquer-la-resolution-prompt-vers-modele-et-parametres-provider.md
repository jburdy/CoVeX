# Story 2.3: Appliquer la resolution prompt vers modele et parametres provider

> Note 2026-03-14: artefact BMAD historique. Certaines references internes
> (tests, modules, `criteria`, hot reload, pages playground) peuvent ne plus
> correspondre exactement au depot courant. Pour l'etat actuel, se fier a
> `README.md`, `docs/ARCHITECTURE.md` et `docs/ANALYSIS_PROFILES_METIER.md`.


Status: review

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a integrateur technique,
I want que chaque analyse applique automatiquement le bon modele et les bons parametres d inference selon le prompt selectionne,
so that le comportement de CoVeX soit previsible et coherent entre domaines metier.

## Acceptance Criteria

1. **Given** un prompt metier selectionne (manuellement ou via routage) **When** une analyse est lancee **Then** le systeme resolve le modele associe a ce prompt **And** il utilise ce modele pour l inference.
2. **Given** des parametres provider par defaut sont definis **When** le modele associe est utilise **Then** les parametres d inference applicables sont fusionnes correctement (defaults + overrides autorises) **And** les priorites de surcharge sont deterministes et documentees.
3. **Given** un prompt ne definit pas explicitement de modele **When** la resolution est effectuee **Then** le systeme applique une strategie de mecanisme retire de configuration (modele actif ou global) **And** `model_used` reste coherent avec la resolution effective.
4. **Given** des parametres incompatibles avec le provider cible **When** la validation runtime est faite **Then** le systeme retourne une erreur maitrisee et explicite **And** l execution n utilise pas de configuration partiellement invalide.
5. **Given** une analyse terminee **When** la reponse est construite **Then** les metadonnees techniques exposees refletent exactement la configuration appliquee **And** cela permet diagnostic et reproductibilite cote integration.

## Tasks / Subtasks

- [x] Centraliser la resolution `prompt -> modele -> provider_key` dans un service unique (AC: 1, 3)
  - [x] Ajouter/renforcer une fonction de resolution deterministic dans `backend/src/analysis/service.py` ou un module dedie `analysis/resolution.py`
  - [x] Interdire toute resolution parallele dans handlers API ou adaptateur inference
  - [x] Garantir que `profile_id` explicite reste prioritaire sur l auto-routage
- [x] Fusionner les parametres provider de maniere deterministic et tracee (AC: 2)
  - [x] Definir l ordre de priorite explicite: defaults provider -> modele -> override prompt/runtime
  - [x] Implementer une fusion immuable (pas de mutation d objets partages)
  - [x] Documenter les cles autorisees et ignorer/rejeter les cles incompatibles selon policy MVP
- [x] Implementer le mecanisme retire de resolution quand un prompt n a pas de modele explicite (AC: 3)
  - [x] Appliquer mecanisme retire vers modele actif/global provenant de `models_config`
  - [x] S assurer que `model_used` correspond toujours au modele reellement execute
  - [x] Journaliser la branche de resolution (explicite/mecanisme retire) sans exposer de secret
- [x] Ajouter validation runtime defensive des parametres provider (AC: 4)
  - [x] Rejeter les combinaisons invalides avant appel inference
  - [x] Retourner une erreur maitrisee et stable (`500` ou `503` selon nature), format FastAPI MVP
  - [x] Verifier qu aucun etat partiel n est applique si validation echoue
- [x] Garantir la coherence des metadonnees techniques de sortie (AC: 5)
  - [x] Aligner `model_used`, `profile_used`, `latency_sec`, `tokens_in`, `tokens_out` avec le chemin effectif
  - [x] Ajouter des tests de non-regression sur la coherence metadata vs config appliquee
  - [x] Verifier que la reponse reste conforme au contrat `/analyze` sans champs parasites

## Dev Notes

- Cette story est le chainon entre la config (stories 2.1/2.2) et l execution inference. Le risque principal est une resolution implicite non deterministic qui rend les resultats non reproductibles.
- Le DEV agent doit privilegier la reutilisation des modules existants (`models_config`, `prompts/service`) et eviter d introduire une nouvelle couche de parsing/validation YAML.

### Developer Context Section

- **Objectif Epic 2:** permettre des changements metier (prompts/modeles/parametres) sans code, tout en gardant un comportement stable et explicable a l execution.
- **Valeur business story 2.3:** garantir que deux analyses equivalentes utilisent la meme resolution de configuration et produisent des metadonnees fiables pour diagnostic/integration.
- **Contexte des stories precedentes:**
  - Story 2.1 a etabli la source de verite modeles (`backend/src/inference/models_config.py`).
  - Story 2.2 a etabli la source de verite prompts (`backend/src/analysis-profiles/*`) et l endpoint `GET /analysis-profiles`.
  - Story 2.4 traitera le hot-reload; ne pas introduire ici de logique de watcher complexe.

### Technical Requirements

- Resolution deterministic obligatoire a chaque analyse:
  - entree: `profile_id` explicite ou prompt issu du routage,
  - sortie: `resolved_model`, `resolved_provider`, `resolved_params`.
- Ordre de priorite de fusion des parametres a rendre explicite et teste:
  1. defaults provider
  2. parametres du modele
  3. override autorise (prompt/runtime)
- Mecanisme retire obligatoire quand `prompt.model` est absent:
  - utiliser modele actif/global valide,
  - garder traçabilite via logs + `model_used`.
- Validation runtime defensive des parametres:
  - types et plages des valeurs,
  - compatibilite provider,
  - rejet atomique en cas d incoherence.
- Contrat API a respecter:
  - pas de changement breaking sur `POST /analyze`,
  - champs metadata en `snake_case`,
  - erreurs FastAPI MVP sans envelope custom.

### Architecture Compliance

- Respecter les conventions `snake_case` et l organisation feature-first.
- Garder les boundaries:
  - API: `backend/src/analysis/api.py` (validation HTTP + mapping erreurs),
  - metier: `backend/src/analysis/service.py`,
  - configuration: `backend/src/analysis-profiles/*` et `backend/src/inference/models_config.py`,
  - inference: `backend/src/inference/adapter.py`.
- Interdictions:
  - pas de logique provider dans handlers API,
  - pas de duplication de logique de fusion/validation dans plusieurs modules,
  - pas de persistance de texte utilisateur ni cache metier MVP.

### Library/Framework Requirements

- **FastAPI 0.128.x:** conserver compatibilite de la ligne actuelle, aucun changement d architecture HTTP.
- **Pydantic 2.12.x:** utiliser models/validators v2 pour validation stricte des structures runtime.
- **HTTPX 0.28.1:** ne pas contourner l adaptateur existant; rester compatible avec ses semantics SSL et timeout.
- **NiceGUI 3.7.1 / Quasar 2.18.x:** hors scope direct backend, mais conserver les metadata attendues par l UI details panel.

### File Structure Requirements

- Fichiers cibles prioritaires:
  - `backend/src/analysis/service.py`
  - `backend/src/analysis/routing.py`
  - `backend/src/inference/adapter.py`
  - `backend/src/inference/models_config.py`
  - `backend/src/analysis-profiles/service.py`
- Fichiers potentiellement touches selon implementation:
  - `backend/src/analysis/schemas.py`
  - `backend/src/common/errors.py`
  - `backend/src/main.py` (wiring, si necessaire)
- Tests a creer/etendre:
  - `backend/tests/analysis/test_service.py`
  - `backend/tests/analysis/test_routing.py`
  - `backend/tests/inference/test_adapter.py`
  - `backend/tests/test_config_yaml.py`

### Testing Requirements

- Couvrir resolution explicite et auto-routage vers modele attendu (AC1).
- Couvrir fusion params avec ordre de priorite et absence de mutation partagee (AC2).
- Couvrir mecanisme retire quand prompt sans modele + verification `model_used` (AC3).
- Couvrir parametres incompatibles -> erreur maitrisee, sans etat partiel (AC4).
- Couvrir coherence metadata retournees vs configuration appliquee (AC5).
- Ajouter tests anti-regression pour eviter la reintroduction de logique de resolution dupliquee.

### Previous Story Intelligence

- Story 2.2 a deja introduit une couche prompts centralisee; s y brancher directement pour recuperer prompt/model mapping.
- Les patterns de stories 1.4-1.6 montrent que l adaptateur inference est le bon point pour conserver resilience (timeouts/mecanisme retire) sans polluer la couche API.
- Le workflow recent privilegie des commits atomiques par story avec tests miroirs par feature; conserver cette cadence.

### Git Intelligence Summary

- Les 5 derniers commits confirment la sequence technique: robustesse inference (1.4-1.6) -> config modeles (2.1) -> config prompts (2.2).
- Les fichiers les plus pertinents pour 2.3 sont deja actifs dans l historique recent: `analysis/service.py`, `analysis/routing.py`, `inference/adapter.py`, `prompts/service.py`, `tests/analysis/*`, `tests/inference/*`.
- Convention observee: mise a jour conjointe story file + `sprint-status.yaml` + couverture tests avant passage en `review`.

### Latest Tech Information

- FastAPI release notes indiquent une ligne stable `0.128.x` (latest notes `0.128.8`), sans changement bloquant pour ce scope. [Source: https://fastapi.tiangolo.com/release-notes/]
- Pydantic `2.12.5` reste la reference doc courante; pertinence forte pour validation stricte sous Python 3.14. [Source: https://docs.pydantic.dev/latest/changelog/]
- NiceGUI `3.7.1` est la derniere release PyPI et suit Python >=3.10; utile pour verifier compatibilite des metadata UI attendues. [Source: https://pypi.org/project/nicegui/]
- HTTPX `0.28.1` est la derniere release stable connue; attention aux deprecations SSL introduites en 0.28.0 dans toute evolution client. [Source: https://github.com/encode/httpx/releases]

### Project Structure Notes

- Aucun `project-context.md` detecte via le pattern `**/project-context.md`.
- Contexte source utilise: `epics.md`, `architecture.md`, `prd.md`, `ux-design-specification.md`, `sprint-status.yaml`, story precedente `2-2-*.md`, et historique git recent.

### References

- Story 2.3 et AC: [Source: _bmad-output/planning-artifacts/epics.md#Story 2.3]
- FR/NFR associees (FR14, FR8, FR9, NFR7, NFR9, NFR13, NFR14): [Source: _bmad-output/planning-artifacts/prd.md#Functional Requirements], [Source: _bmad-output/planning-artifacts/prd.md#Non-Functional Requirements]
- Boundaries, patterns et structure cible: [Source: _bmad-output/planning-artifacts/architecture.md#Implementation Patterns & Consistency Rules], [Source: _bmad-output/planning-artifacts/architecture.md#Project Structure & Boundaries]
- Contraintes UX de feedback/erreurs/metadata techniques: [Source: _bmad-output/planning-artifacts/ux-design-specification.md#Feedback Patterns], [Source: _bmad-output/planning-artifacts/ux-design-specification.md#TechnicalDetailsExpansion]
- Story precedente: [Source: _bmad-output/implementation-artifacts/2-2-gerer-les-prompts-metier-via-configuration.md]
- Historique git recent: [Source: git log local (38da8de, 23661d5, 21e106a, 7e1313e, 9dd6b34)]

### Story Completion Status

- Story context cree avec statut `ready-for-dev`.
- Note de completion: Ultimate context engine analysis completed - comprehensive developer guide created.

## Dev Agent Record

### Agent Model Used

openai/gpt-5.3-codex

### Debug Log References

- Artefacts analyses: `epics.md`, `architecture.md`, `prd.md`, `ux-design-specification.md`, `sprint-status.yaml`.
- Story precedente analysee: `2-2-gerer-les-prompts-metier-via-configuration.md`.
- Historique git recent analyse: 5 derniers commits et fichiers modifies.
- Veille technique effectuee: FastAPI, Pydantic, NiceGUI, HTTPX.

### Implementation Plan

- Centraliser la resolution runtime dans `analysis/resolution.py` avec une sortie unique: `profile_used`, `provider_key`, `model_used`, `provider_params` et branche `explicit/mecanisme retire`.
- Etendre les schemas config (`inference_engines.yaml`, `analysis_profiles.yaml`) pour porter les parametres provider et appliquer une fusion immuable et deterministic.
- Faire valider les parametres au runtime dans l adaptateur inference avant tout appel reseau pour garantir un rejet atomique.
- Aligner la couche API/service sur la resolution effective et couvrir AC1-AC5 avec tests unitaires + integration API.

### Completion Notes List

- Story 2.3 contextualisee en guide d implementation complet et actionnable pour dev-agent.
- Guardrails explicites ajoutes pour eviter duplication de logique et resolution non deterministic.
- Contraintes architecture, tests et metadata tracees avec references directes aux artefacts source.
- Statut story fixe a `ready-for-dev` conformement au workflow.
- Resolution centralisee implementee via `backend/src/analysis/resolution.py` avec mecanisme retire explicite vers modele actif/global et logs de branche sans secret.
- Fusion deterministic des parametres implementee (defaults provider -> model params -> overrides prompt/runtime) avec copie immuable.
- Validation runtime defensive ajoutee dans l adaptateur inference: cles autorisees, compatibilite provider, types/plages, rejet atomique avant appel inference.
- Contrat `/analyze` et metadata techniques verifies via tests: `model_used`, `profile_used`, `latency_sec`, `tokens_in`, `tokens_out` restent coherents avec le chemin d execution.
- Validation executee: `uv run pytest -q` (82 passed) et `uv run ruff check` (OK).

### File List

- _bmad-output/implementation-artifacts/2-3-appliquer-la-resolution-prompt-vers-modele-et-parametres-provider.md
- backend/src/analysis/api.py
- backend/src/analysis/resolution.py
- backend/src/analysis/routing.py
- backend/src/analysis/schemas.py
- backend/src/analysis/service.py
- backend/src/inference/adapter.py
- backend/src/inference/client.py
- backend/src/inference/models_config.py
- backend/src/analysis-profiles/schemas.py
- backend/src/analysis-profiles/service.py
- backend/tests/analysis/test_api.py
- backend/tests/analysis/test_resolution.py
- backend/tests/analysis/test_service.py
- backend/tests/inference/test_adapter.py
- _bmad-output/implementation-artifacts/sprint-status.yaml

## Change Log

- 2026-02-12: Implementation Story 2.3 completee - resolution prompt->modele/provider centralisee, fusion + validation runtime des parametres provider, mecanisme retire deterministic et couverture tests AC1-AC5.

## Senior Developer Review (AI)

### Review Summary
- **Reviewer:** JBU
- **Date:** 2026-02-23
- **Outcome:** Approved

### Findings

#### High Severity
- None

#### Medium Severity
- **Chaîne try/except dans adapter.py:** Réutilise le code identifié dans 2-1 (188-227). À refactorer dans une PR ultérieure.

#### Low Severity
- **Ordre de fusion non documenté:** Le code `_merge_provider_params` implémente l'ordre priority mais aucun commentaire ne documente cette ordre dans le code.

### Verification
- ✅ Tests unitaires: 82 passent
- ✅ Lint (ruff): All checks passed
- ✅ AC1-AC5 fully implemented
- ✅ File List: tous les fichiers existants
- ✅ Resolution centralisée dans resolution.py

### Notes
- La résolution est deterministic et bien tracée
- Le mecanisme retire vers le modèle actif fonctionne correctement
- Les métadonnées techniques (`model_used`, `profile_used`, etc.) sont cohérentes
- La validation runtime des paramètres est en place
