# Story 1.5: Standardiser la gestion d erreurs API explicites

> Note 2026-03-14: artefact BMAD historique. Certaines references internes
> (tests, modules, `criteria`, hot reload, pages playground) peuvent ne plus
> correspondre exactement au depot courant. Pour l'etat actuel, se fier a
> `README.md`, `docs/ARCHITECTURE.md` et `docs/ANALYSIS_PROFILES_METIER.md`.


Status: review

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As an integrateur API,
I want des erreurs HTTP explicites et stables selon les cas metier et techniques,
so that mon systeme tiers puisse gerer les echecs sans ambiguite.

## Acceptance Criteria

1. **Given** une requete invalide (schema, champ requis manquant, texte vide) **When** `POST /analyze` est appele **Then** l API retourne `400` **And** le message permet de corriger la requete sans inspection serveur.
2. **Given** un prompt explicitement demande mais introuvable **When** la requete est traitee **Then** l API retourne `404` **And** la cause indique clairement l identifiant de prompt non resolu.
3. **Given** une indisponibilite du moteur d inference **When** l analyse est demandee **Then** l API retourne `503` **And** la reponse reste concise, sans fuite de details internes.
4. **Given** une erreur interne non recuperable hors indisponibilite moteur **When** le traitement echoue **Then** l API retourne `500` **And** le format d erreur est coherent avec le reste de l API MVP.
5. **Given** une erreur est retournee au client **When** l incident est journalise cote serveur **Then** les logs contiennent le contexte utile au diagnostic **And** ils n incluent pas de texte utilisateur brut persiste de facon durable.

## Tasks / Subtasks

- [x] Stabiliser la translation d erreurs metier/techniques vers les statuts HTTP cibles (AC: 1, 2, 3, 4)
  - [x] Cartographier explicitement les exceptions de `analysis/service.py` et `analysis/routing.py` vers `400`, `404`, `503`, `500`
  - [x] Garder les erreurs FastAPI de validation d entree comme source de verite pour les payloads invalides (`422` natif) sauf decision explicite de conversion
  - [x] Si conversion `422 -> 400` est retenue pour alignement produit, la centraliser dans `backend/src/main.py` avec handler unique et message stable
- [x] Uniformiser les messages d erreur exposes au client (AC: 1, 2, 3, 4)
  - [x] Garantir des messages courts, actionnables, et sans details d implementation
  - [x] Inclure l identifiant de prompt introuvable dans le cas `404` quand disponible
  - [x] Verifier qu aucune erreur ne fuit stack trace, secret, ou texte utilisateur brut
- [x] Renforcer la journalisation serveur orientee diagnostic sans persistance sensible (AC: 5)
  - [x] Journaliser categorie d erreur, route, statut, et identifiant de prompt (si present)
  - [x] Exclure le contenu integral de `text` des logs application
  - [x] Conserver la separation message client (court) vs message technique serveur (detaille)
- [x] Couvrir les cas d erreur par tests API et service (AC: 1-5)
  - [x] Ajouter tests pour requete invalide, prompt inconnu, indisponibilite inference, erreur interne, et non-fuite de details
  - [x] Verifier la stabilite du format JSON d erreur FastAPI sur chaque code cible
  - [x] Ajouter tests de non-regression sur le contrat de succes (`score`, `decision`, `justification`, metadonnees optionnelles)

## Dev Notes

- Cette story ferme le trou d ambiguite d integration en rendant la semantique d erreur API deterministic et exploitable cote clients tiers.
- Le scope est backend/API uniquement; aucun changement de logique fonctionnelle de scoring n est attendu.

### Developer Context Section

- **Objectif Epic 1:** consolider `POST /analyze` comme contrat fiable, y compris sur chemins d echec, pour integrateurs et futur Playground.
- **Valeur business immediate:** reduction des retries aveugles et des erreurs de traitement cote systemes tiers grace a des statuts HTTP predictibles.
- **Dependances amont:**
  - Story 1.2 a etabli le contrat de succes et la couche API/service.
  - Story 1.3 a introduit les erreurs de resolution de prompt (`PromptNotFoundError`, `PromptResolutionError`).
  - Story 1.4 a introduit les erreurs d indisponibilite/inference (`InferenceServiceUnavailableError`, `InferenceInternalError`).
- **Dependances de config:** conserver l usage de `config/analysis_profiles.yaml`, `config/inference_engines.yaml`, `config/routing.yaml` comme source de verite runtime.
- **Contraintes de scope:** pas de DB, pas de persistance texte, pas de security middleware additionnel, pas de changement de contrat de succes.

### Technical Requirements

- Conserver le pipeline `analysis/api.py -> analysis/service.py -> inference/adapter.py` sans contournement direct dans les handlers.
- Couvrir explicitement les scenarii d erreur suivants:
  - requete invalide (payload non conforme / texte vide)
  - prompt explicite introuvable
  - indisponibilite moteur d inference (timeout/down)
  - erreur interne non recuperable
- Garantir la coherence semantique des statuts:
  - `404` pour prompt explicitement introuvable
  - `503` pour indisponibilite de dependance inference
  - `500` pour erreur interne non recuperable
  - `400` cible produit pour requete invalide (avec arbitrage explicite si validation FastAPI native conserve `422`)
- Les messages client doivent rester stables et actionnables; aucun detail sensible (stack, secret, texte brut utilisateur).
- Les logs serveur doivent aider au diagnostic (categorie, cause, contexte technique) sans persistance de donnees metier sensibles.

### Architecture Compliance

- Respecter les conventions `snake_case` (payloads JSON, variables Python, noms de fonctions/fichiers).
- Garder le format succes en payload direct Pydantic; ne pas introduire de wrapper global `{data: ...}`.
- Rester aligne avec l approche MVP: erreurs FastAPI comme base, avec eventuel handler global minimal si alignement `400` requis.
- Maintenir structure feature-first et tests miroirs:
  - `backend/src/analysis/*`
  - `backend/src/inference/*`
  - `backend/tests/analysis/*`
- Preserver architecture stateless stricte (aucune persistence interne du texte utilisateur).

### Library/Framework Requirements

- **FastAPI:** base projet actuelle `0.128.x`; latest stable detectee `0.129.0` (PyPI, 2026-02-12). Implementer sans APIs experimentales et rester compatible 0.128/0.129.
- **Pydantic:** `2.12.5` (changelog officiel), garder patterns v2 (`BaseModel`, `Field`, validation explicite).
- **Uvicorn:** `0.40.0`; Python 3.9 est retire. Garder CI/runtime sur Python >= 3.10.
- **HTTPX:** stable `0.28.1`; branche `1.0.dev*` existante, ne pas introduire migration majeure dans cette story.
- **NiceGUI:** hors scope direct backend, mais version projet `3.7.1`; eviter downgrade sous `3.7.0` (correctifs securite XSS/path traversal publies).

### File Structure Requirements

- Fichiers backend cibles prioritaires:
  - `backend/src/analysis/api.py`
  - `backend/src/analysis/service.py`
  - `backend/src/analysis/errors.py`
  - `backend/src/main.py` (uniquement si handler global d erreur requis)
- Fichiers de tests a etendre:
  - `backend/tests/analysis/test_api.py`
  - `backend/tests/analysis/test_service.py`
- Fichiers potentiellement impactes (si clarte necessaire):
  - `backend/src/analysis/schemas.py` (seulement si precision de contraintes d entree/sortie)
  - `backend/src/inference/adapter.py` (seulement pour normalisation de mapping d erreurs)

### Testing Requirements

- Verifier codes d erreur cibles sur `POST /analyze` pour AC1-AC4.
- Verifier le contenu de `detail` (court, actionnable, sans fuite sensible) pour chaque code d erreur.
- Verifier qu un prompt introuvable explicite renvoie `404` avec signal utile a l integrateur.
- Verifier qu indisponibilite inference renvoie `503` et qu erreur interne non recuperable renvoie `500`.
- Verifier absence de texte utilisateur brut dans les logs/messages client lors d erreurs.
- Verifier non-regression du contrat de succes (fields et coherence `score -> decision`).

### Previous Story Intelligence

- Story 1.4 a deja etabli une distinction importante entre indisponibilite moteur (`503`) et erreur interne (`500`); reutiliser cette separation sans la diluer.
- Story 1.4 a renforce la hygiene de messages client (pas de details sensibles) et l instrumentation logs; conserver cette posture sur toutes les erreurs API.
- Story 1.3 a formalise la resolution de prompt avec exceptions dediees; le mapping `PromptNotFoundError -> 404` doit rester stable.
- Les tests existants couvrent deja une partie des chemins d erreur; cette story doit fermer les angles morts et harmoniser les assertions de format/message.

### Git Intelligence Summary

- `9dd6b34` (story 1.4): introduction de l adaptateur inference et des mappings `500/503`, plus enrichissement tests API/service.
- `ce2fbda` (story 1.3): ajout du routage prompt et des erreurs de resolution (`analysis/errors.py`, `analysis/routing.py`).
- `43a6e4d` (story 1.2): base du contrat `POST /analyze` et de la structure `analysis/{api,service,schemas}`.
- `1a2d3d1` (story 1.1): fondation projet + CI + structure feature-first.
- Consequence implementation: concentrer 1.5 sur la couche API/errors/tests, sans refactor large de scoring/routing.

### Latest Tech Information

- FastAPI `0.129.0` est publie (2026-02-12); compatible Python >= 3.10. Les releases 0.128.x/0.129.x restent proches pour l usage MVP courant.
- Pydantic `2.12.5` est la reference stable actuelle; correctifs sur robustesse de serialisation/compatibilite Python recentes.
- Uvicorn `0.40.0` retire Python 3.9; aligner env local et CI sur >= 3.10.
- HTTPX stable reste `0.28.1`; la branche `1.0.dev` existe mais n est pas cible MVP.
- NiceGUI `3.7.0+` integre des correctifs securite (XSS sur `ui.markdown`, path traversal upload). Conserver `3.7.1` cote projet.

### Project Structure Notes

- Aucun fichier `project-context.md` detecte via le pattern `**/project-context.md`.
- Le contexte de travail provient de `epics.md`, `prd.md`, `architecture.md`, `ux-design-specification.md`, `sprint-status.yaml`, story 1.4 et historique git recent.

### References

- Story 1.5 et AC: [Source: _bmad-output/planning-artifacts/epics.md#Story 1.5]
- Contrat API, FR/NFR: [Source: _bmad-output/planning-artifacts/prd.md#API Specifications], [Source: _bmad-output/planning-artifacts/prd.md#Functional Requirements], [Source: _bmad-output/planning-artifacts/prd.md#Non-Functional Requirements]
- Patterns architecture et erreurs MVP: [Source: _bmad-output/planning-artifacts/architecture.md#API & Communication Patterns], [Source: _bmad-output/planning-artifacts/architecture.md#Error Handling Patterns], [Source: _bmad-output/planning-artifacts/architecture.md#Implementation Patterns & Consistency Rules]
- Contraintes UX erreurs: [Source: _bmad-output/planning-artifacts/ux-design-specification.md#Feedback Patterns]
- Story precedente et learnings: [Source: _bmad-output/implementation-artifacts/1-4-integrer-l-adaptateur-d-inference-locale-avec-timeouts-et-metriques.md]
- Veille technique: [Source: https://pypi.org/project/fastapi/], [Source: https://fastapi.tiangolo.com/release-notes/], [Source: https://docs.pydantic.dev/latest/changelog/], [Source: https://uvicorn.dev/release-notes/], [Source: https://pypi.org/project/httpx/], [Source: https://github.com/zauberzeug/nicegui/releases/tag/v3.7.1], [Source: https://newreleases.io/project/pypi/nicegui/release/3.7.0]

### Story Completion Status

- Story context cree avec statut `ready-for-dev`.
- Note de completion: Ultimate context engine analysis completed - comprehensive developer guide created.

## Dev Agent Record

### Agent Model Used

openai/gpt-5.3-codex

### Debug Log References

- Analyse artefacts: `epics.md`, `prd.md`, `prd-validation-report*.md`, `architecture.md`, `ux-design-specification.md`, `sprint-status.yaml`.
- Analyse story precedente: `1-4-integrer-l-adaptateur-d-inference-locale-avec-timeouts-et-metriques.md`.
- Analyse git recente: 5 derniers commits + fichiers modifies.
- Veille technique: FastAPI, Pydantic, Uvicorn, HTTPX, NiceGUI release/security notes.
- Execution implementation: `uv run pytest tests/analysis/test_api.py -q`, `uv run pytest tests/analysis/test_service.py tests/analysis/test_api.py -q`, `uv run pytest -q`, `uv run ruff check .`.

### Implementation Plan

- Centraliser la conversion de validation FastAPI `422 -> 400` avec un handler unique dans `backend/src/main.py`.
- Uniformiser la translation d erreurs metier/inference dans `backend/src/analysis/api.py` vers messages clients stables (`404`, `503`, `500`) et ajouter un mecanisme retire `500` pour erreurs inattendues.
- Ajouter des logs diagnostiques structures (categorie, route, statut, profile_id) sans persistance du texte utilisateur brut.
- Renforcer les tests API pour couvrir les cas `400`, `404`, `500`, la non-fuite d informations sensibles, et la stabilite du format de reponse d erreur.

### Completion Notes List

- Story 1.5 contextualisee pour implementation backend centree sur la stabilite du contrat d erreur API.
- Guardrails explicites ajoutes pour prevenir fuite d informations sensibles et ambiguite des statuts HTTP.
- Dependencies/story learnings precedentes integrees pour limiter regressions et rework.
- Handler global de validation ajoute dans `main.py` pour convertir les erreurs de payload invalide en `400` avec detail stable et actionnable.
- Mapping d erreurs API harmonise dans `analysis/api.py` avec messages clients coherents, `profile_id` inclus sur `404`, et mecanisme retire `500` generique sans fuite de details internes.
- Journalisation serveur normalisee sur les erreurs API (`category`, `status`, `route`, `profile_id`, `error_type`) sans logguer le texte utilisateur.
- Tests API et regression etendus sur les codes cibles et le contrat de reponse; suite backend complete et lint passes.

### File List

- _bmad-output/implementation-artifacts/1-5-standardiser-la-gestion-d-erreurs-api-explicites.md
- _bmad-output/implementation-artifacts/sprint-status.yaml
- backend/src/analysis/api.py
- backend/src/main.py
- backend/tests/analysis/test_api.py

## Change Log

- 2026-02-12: Story 1.5 creee avec contexte complet, guardrails architecture, intelligence git/historique, et veille technique recente; statut positionne `ready-for-dev`.
- 2026-02-12: Implementation Story 1.5 terminee - conversion validation `422->400`, messages d erreur API stabilises (`400/404/503/500`), logs diagnostiques sans texte utilisateur brut, et couverture de tests API et regression renforcee; statut positionne `review`.
