# Story 1.4: Integrer l adaptateur d inference locale avec timeouts et metriques

> Note 2026-03-14: artefact BMAD historique. Certaines references internes
> (tests, modules, `criteria`, hot reload, pages playground) peuvent ne plus
> correspondre exactement au depot courant. Pour l'etat actuel, se fier a
> `README.md`, `docs/ARCHITECTURE.md` et `docs/ANALYSIS_PROFILES_METIER.md`.


Status: review

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a integrateur plateforme,
I want que CoVeX appelle un moteur d inference local via un adaptateur encapsule avec timeout,
so that le service reste fiable, mesurable et conforme aux objectifs de performance.

## Acceptance Criteria

1. **Given** une analyse est demandee **When** le service appelle le moteur d inference local via l adaptateur **Then** l appel est encapsule hors des handlers API **And** la couche API ne depend que du service metier.
2. **Given** un appel inference aboutit **When** la reponse est retournee a l API **Then** les metriques `latency_sec`, `tokens_in`, `tokens_out` sont renseignees quand disponibles **And** elles sont integrees dans la reponse sans casser le contrat minimal.
3. **Given** le moteur local ne repond pas avant le delai configure **When** le timeout est atteint **Then** l adaptateur interrompt proprement l appel **And** le service retourne une erreur maitrisee compatible `503` ou `500` selon la cause.
4. **Given** des erreurs transientes cote moteur (reseau local, reponse invalide) **When** l adaptateur les detecte **Then** elles sont journalisees de facon exploitable **And** le message client reste clair, court et sans details techniques sensibles.
5. **Given** un volume de requetes MVP normal **When** les mesures de performance sont observees **Then** le design permet d atteindre les cibles de latence (`/analyze` et routage) **And** les points de mesure sont suffisamment explicites pour verification KPI.

## Tasks / Subtasks

- [x] Introduire un adaptateur inference local dedie et l integrer au pipeline d analyse (AC: 1)
  - [x] Creer `backend/src/inference/adapter.py` pour encapsuler les appels moteur et normaliser les erreurs techniques
  - [x] Ajouter ou etendre `backend/src/inference/client.py` pour le transport HTTP vers moteur local
  - [x] Connecter `backend/src/analysis/service.py` a l adaptateur (pas d appel moteur direct depuis `analysis/api.py`)
- [x] Exposer les metriques d inference dans la reponse sans rupture de contrat (AC: 2)
  - [x] Etendre les schemas `AnalyzeResponse` avec metadonnees optionnelles (`latency_sec`, `tokens_in`, `tokens_out`, `model_used` si disponible)
  - [x] Mapper les champs metriques de la reponse moteur vers le contrat API en `snake_case`
  - [x] Conserver compatibilite avec reponses partielles (metadonnees absentes)
- [x] Mettre en place la gestion de timeout et la translation d erreurs (AC: 3, 4)
  - [x] Centraliser timeout(s) dans `backend/src/inference/timeouts.py` ou equivalent coherent
  - [x] Convertir timeout/indisponibilite moteur en erreurs maitrisees (`503`) et erreurs internes non recuperables en `500`
  - [x] Journaliser les details techniques cote serveur sans persister ni exposer le texte brut utilisateur
- [x] Verifier la tenue performance et observabilite MVP (AC: 5)
  - [x] Instrumenter la mesure `latency_sec` sur le segment inference
  - [x] Verifier que le chemin d execution reste compatible avec les cibles NFR (`/analyze` p95 cible < 2s, routage p95 cible < 500ms)
  - [x] Documenter clairement les points de mesure utilises en tests
- [x] Couvrir les parcours par tests unitaires et API (AC: 1-5)
  - [x] Tests adaptateur: succes, timeout, erreur transiente, reponse invalide, metriques partielles
  - [x] Tests service/API: mapping metriques, mapping erreurs `500/503`, non-regression score/decision/justification
  - [x] Tests de robustesse: absence de fuite d informations sensibles dans messages client

## Dev Notes

- Cette story solidifie la couche d execution inference introduite dans le flux Epic 1 pour rendre `/analyze` fiable et mesurable.
- Le scope reste backend/API et respect strict de l architecture stateless locale-first.

### Developer Context Section

- **Objectif Epic 1:** fiabiliser l execution inference locale pour alimenter le scoring/decision sans couplage API direct au moteur.
- **Valeur business immediate:** reduction des incidents operationnels, diagnostic plus simple, meilleures garanties de latence percue.
- **Dependances amont:** story 1.2 (pipeline scoring/decision) et story 1.3 (resolution de prompt/routage) deja en place.
- **Dependances de config:** conserver l usage de `config/inference_engines.yaml`, `config/analysis_profiles.yaml`, `config/routing.yaml` comme source de verite runtime.
- **Contraintes de scope:** aucune persistance, aucune auth applicative, aucun changement du contrat minimal de sortie.

### Technical Requirements

- L adaptateur inference doit etre la seule porte d entree vers le moteur local depuis la logique metier.
- Le service d analyse doit recevoir un resultat inference structure, puis produire `score`, `decision`, `justification` avec metadonnees optionnelles.
- Le timeout inference doit etre explicite, configurable, et applique de facon consistante pour eviter blocage prolonges.
- Les erreurs moteur doivent etre classees de facon deterministe:
  - indisponibilite/timeout/dependance externe -> `503`
  - erreur interne non recuperable -> `500`
- Les champs metriques (`latency_sec`, `tokens_in`, `tokens_out`) doivent etre tolerants aux absences sans casser le schema de succes.
- Aucune fuite d information sensible dans les erreurs client (pas de stack trace, pas de details internes, pas de texte utilisateur brut).

### Architecture Compliance

- Respecter `api.py -> service.py -> inference/adapter.py -> inference/client.py`.
- Ne pas imploser la logique d adaptation dans `analysis/api.py`.
- Conserver conventions `snake_case` partout (payloads, modules, fonctions, variables).
- Respecter structure feature-first (`analysis`, `inference`, `common`) et tests miroirs sous `backend/tests/`.
- Conserver succes API type direct (Pydantic) et format d erreurs FastAPI MVP.
- Maintenir stateless strict (pas de DB interne, pas de cache MVP, pas de persistance texte).

### Library/Framework Requirements

- **FastAPI:** reference architecture `0.128.8`; latest stable observee `0.129.0` (PyPI, 2026-02-12). Rester compatible `0.128.x/0.129.x` sans APIs experimentales.
- **Pydantic:** `2.12.5` (PyPI/changelog), garder patterns v2 pour schemas et serialisation.
- **Uvicorn:** `0.40.0`, Python `>=3.10`; garder alignement runtime et commandes locales.
- **HTTPX:** stable `0.28.1`; presence de pre-releases `1.0.dev*`, donc eviter migration majeure non necessaire dans cette story.
- **NiceGUI (impact aval UI):** `3.7.1`; conserver compatibilite metadonnees affichees, en tenant compte des correctifs securite 3.7.0+.

### File Structure Requirements

- Backend cibles prioritaires:
  - `backend/src/inference/adapter.py`
  - `backend/src/inference/client.py`
  - `backend/src/inference/timeouts.py`
  - `backend/src/analysis/service.py`
  - `backend/src/analysis/schemas.py`
  - `backend/src/analysis/api.py`
- Backend potentiels (si utile pour clarte):
  - `backend/src/inference/schemas.py`
  - `backend/src/analysis/errors.py` (reutiliser celui deja present si pertinent)
- Tests a couvrir/etendre:
  - `backend/tests/inference/test_adapter.py`
  - `backend/tests/analysis/test_service.py`
  - `backend/tests/analysis/test_api.py`

### Testing Requirements

- Cibler AC1-AC5 explicitement en tests automatises.
- Verifier non-couplage API->moteur (pas d appel direct moteur depuis handlers).
- Verifier mapping metriques en succes complet et succes partiel (metadonnees absentes).
- Verifier timeouts et indisponibilites renvoient des erreurs maitrisees (`503`) et cas internes (`500`).
- Verifier logs serveur exploitables sans fuite de donnees utilisateur sensibles.
- Verifier non-regression de 1.2/1.3: coherence `score -> decision -> justification` et metadonnees de routage deja en place.

### Previous Story Intelligence

- Story 1.3 a deja impose une separation claire `analysis/api.py` vs `analysis/service.py` avec erreurs metier centralisees; conserver ce pattern.
- Le contrat API est deja enrichi (`profile_used`, `routing_confidence`) et doit rester stable avec ajout des metriques inference.
- Les tests de story 1.3 ont introduit des verifications robustes de codes d erreur; reutiliser ce socle pour timeout/transient errors.
- Le module `backend/src/analysis/errors.py` existe deja: privilegier extension/reuse plutot que duplication d exceptions.

### Git Intelligence Summary

- `ce2fbda` (story 1.3) a ajoute `backend/src/analysis/routing.py`, `backend/src/analysis/errors.py`, et etendu `api/service/schemas` + tests.
- `43a6e4d` (story 1.2) a etabli les modules coeur `analysis/{api,service,schemas,scoring,decision}` et les tests feature-first associes.
- `1a2d3d1` (story 1.1) a pose la structure projet, la config YAML et le squelette backend/playground.
- Consequence pratique: implementer 1.4 dans `inference/` + integration minimale dans `analysis/service.py` pour limiter les regressions.

### Latest Tech Information

- FastAPI `0.129.0` publie le 2026-02-12 (latest stable), architecture reference actuelle `0.128.8` reste proche.
- Pydantic `2.12.5` (latest stable) inclut correctifs de robustesse, dont points autour Python 3.14.
- Uvicorn `0.40.0` confirme support Python 3.14 et abandon Python 3.9; aligner environnement local/CI.
- HTTPX stable reste `0.28.1` avec pre-releases `1.0.dev*`; ne pas introduire incompatibilites 1.0 dans MVP.
- NiceGUI `3.7.1` est latest stable; version 3.7.0 corrige des vulnerabilites de securite importantes (XSS markdown, path traversal upload).

### Project Structure Notes

- Aucun fichier `project-context.md` detecte via pattern `**/project-context.md`.
- Le contexte de reference provient de `epics.md`, `architecture.md`, `prd.md`, `ux-design-specification.md`, `sprint-status.yaml`, et de l historique git recent.

### References

- Story 1.4 et AC: [Source: _bmad-output/planning-artifacts/epics.md#Story 1.4]
- FR/NFR et KPI performance: [Source: _bmad-output/planning-artifacts/prd.md#Functional Requirements], [Source: _bmad-output/planning-artifacts/prd.md#Non-Functional Requirements], [Source: _bmad-output/planning-artifacts/prd.md#Performance gates (source de verite)]
- Contraintes architecture et structure: [Source: _bmad-output/planning-artifacts/architecture.md#API & Communication Patterns], [Source: _bmad-output/planning-artifacts/architecture.md#Project Structure & Boundaries], [Source: _bmad-output/planning-artifacts/architecture.md#Implementation Patterns & Consistency Rules]
- Contraintes UX sur erreurs et details techniques: [Source: _bmad-output/planning-artifacts/ux-design-specification.md#Feedback Patterns], [Source: _bmad-output/planning-artifacts/ux-design-specification.md#Component Strategy]
- Story precedente: [Source: _bmad-output/implementation-artifacts/1-3-ajouter-le-routage-automatique-de-contexte-metier.md]
- Veille technique: [Source: https://pypi.org/project/fastapi/], [Source: https://fastapi.tiangolo.com/release-notes/], [Source: https://pypi.org/project/pydantic/], [Source: https://docs.pydantic.dev/latest/changelog/], [Source: https://pypi.org/project/uvicorn/], [Source: https://uvicorn.dev/release-notes/], [Source: https://pypi.org/project/httpx/], [Source: https://github.com/encode/httpx/releases], [Source: https://pypi.org/project/nicegui/], [Source: https://newreleases.io/project/pypi/nicegui/release/3.7.0]

### Story Completion Status

- Story context cree avec statut `ready-for-dev`.
- Note de completion: Ultimate context engine analysis completed - comprehensive developer guide created.

## Dev Agent Record

### Agent Model Used

openai/gpt-5.3-codex

### Implementation Plan

- Introduire une couche `inference/adapter.py` comme porte d entree unique du moteur pour la logique metier, avec normalisation des erreurs techniques.
- Ajouter `inference/client.py` pour supporter le transport HTTP vers moteur local, avec mecanisme retire `placeholder` compatible MVP et timeout externe configurable.
- Centraliser la resolution de timeout dans `inference/timeouts.py` via config (`config/inference_engines.yaml`) et variable d environnement.
- Connecter `analysis/service.py` a l adaptateur et enrichir `AnalysisResult` avec metadonnees optionnelles de performance (`latency_sec`, tokens, modele).
- Mettre a jour `analysis/api.py` + `analysis/schemas.py` pour exposer les metriques sans rupture de contrat.
- Couvrir AC1-AC5 via tests adaptateur, service et API, puis valider avec suite complete + lint.

### Debug Log References

- Analyse artefacts: `epics.md`, `prd.md`, `prd-validation-report*.md`, `architecture.md`, `ux-design-specification.md`, `sprint-status.yaml`.
- Analyse story precedente: `1-3-ajouter-le-routage-automatique-de-contexte-metier.md`.
- Analyse git recente: 5 derniers commits + fichiers modifies.
- Veille technique: PyPI/release notes FastAPI, Pydantic, Uvicorn, HTTPX, NiceGUI.
- Execution tests (red/green): `uv run pytest tests/inference/test_adapter.py tests/analysis/test_service.py tests/analysis/test_api.py`.
- Validation regression + qualite: `uv run pytest` et `uv run ruff check src tests`.

### Completion Notes List

- Ajout d un adaptateur inference dedie (`inference/adapter.py`) place entre service metier et client moteur, avec journalisation technique et normalisation erreurs 503/500.
- Ajout d un client inference (`inference/client.py`) avec transport HTTP configurable et mecanisme retire `placeholder` pour conserver le comportement local MVP sans moteur distant.
- Ajout d un module timeout centralise (`inference/timeouts.py`) lisant `config/inference_engines.yaml` et `COVEX_INFERENCE_TIMEOUT_SEC`.
- Integration de l adaptateur dans `analysis/service.py`; suppression de tout appel moteur direct depuis `analysis/api.py`.
- Enrichissement du contrat API (`AnalyzeResponse`) avec metadonnees optionnelles `latency_sec`, `tokens_in`, `tokens_out`, `model_used` en `snake_case`.
- Couverture tests et robustesse: nouveaux tests adaptateur + extensions service/API pour timeouts, erreurs transientes, reponses invalides, metriques partielles, absence de fuite de details sensibles.
- Validation finale reussie: `46 passed` sur `uv run pytest` et `ruff` sans erreur.

### File List

- _bmad-output/implementation-artifacts/1-4-integrer-l-adaptateur-d-inference-locale-avec-timeouts-et-metriques.md
- _bmad-output/implementation-artifacts/sprint-status.yaml
- backend/src/analysis/api.py
- backend/src/analysis/schemas.py
- backend/src/analysis/service.py
- backend/src/inference/adapter.py
- backend/src/inference/client.py
- backend/src/inference/timeouts.py
- backend/tests/analysis/test_api.py
- backend/tests/analysis/test_service.py
- backend/tests/inference/test_adapter.py

## Change Log

- 2026-02-12: Implementation story 1.4 completee (adaptateur inference, client HTTP local, timeouts centralises, metriques API optionnelles, mapping erreurs 500/503, tests AC1-AC5, validation lint + regression).
