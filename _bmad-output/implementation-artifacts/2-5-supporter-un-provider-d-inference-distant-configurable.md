# Story 2.5: Supporter un provider d inference distant configurable

> Note 2026-03-14: artefact BMAD historique. Certaines references internes
> (tests, modules, `criteria`, hot reload, pages playground) peuvent ne plus
> correspondre exactement au depot courant. Pour l'etat actuel, se fier a
> `README.md`, `docs/ARCHITECTURE.md` et `docs/ANALYSIS_PROFILES_METIER.md`.


Status: review

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a responsable technique,
I want configurer un provider d inference distant en plus du moteur local,
so that CoVeX puisse fonctionner dans des contextes ou l inference locale n est pas suffisante.

## Acceptance Criteria

1. **Given** un provider distant est defini dans la configuration modeles **When** un modele associe a ce provider est selectionne **Then** CoVeX appelle correctement le provider distant via l adaptateur **And** le contrat de sortie reste identique a celui du mode local.
2. **Given** le mode local-first est actif en MVP **When** aucune option cloud n est explicitement activee **Then** aucune requete inference n est envoyee vers le cloud **And** la souverainete locale est preservee par defaut.
3. **Given** des credentials provider sont requis **When** le service est configure **Then** les secrets sont lus depuis l environnement (pas en clair dans code ou config) **And** une erreur explicite est retournee si les secrets manquent.
4. **Given** une erreur cote provider distant (timeout, auth, quota, indisponibilite) **When** une analyse est executee **Then** le systeme retourne une erreur maitrisee conforme au contrat API **And** les logs techniques permettent le diagnostic sans exposer de secret.
5. **Given** une analyse reussie via provider distant **When** la reponse est renvoyee **Then** `model_used` et metadonnees techniques permettent d identifier le chemin d execution **And** la decision et la justification restent au meme niveau de qualite attendu.

## Tasks / Subtasks

- [x] Etendre la configuration modeles pour supporter un provider `remote_gemini25` operationnel (AC: 1, 2, 3)
  - [x] Conserver `ProviderConfig.type` avec `remote` et valider strictement les champs necessaires (`base_url`, `endpoint`, `model`)
  - [x] Definir une option explicite d activation cloud (ex: flag de provider ou variable d environnement) qui garde le mode local-first par defaut
  - [x] Verifier qu un provider `remote_gemini25` mal configure echoue au chargement avec message explicite (sans fuite de secret)
- [x] Implementer l appel distant dans `inference/client.py` via le meme contrat d adaptateur que le local (AC: 1, 4, 5)
  - [x] Conserver la sortie canonique (`covered_elements`, `missing_elements`, `coverage_ratio`, metriques optionnelles)
  - [x] Ajouter la gestion auth (token/cle) via variables d environnement uniquement
  - [x] Mapper proprement les erreurs HTTP/reseau (timeout/auth/quota/5xx) vers erreurs metier existantes
- [x] Garantir la souverainete locale par defaut et l absence d appel cloud implicite (AC: 2)
  - [x] Verrouiller le chemin distant derriere une activation explicite
  - [x] Conserver le comportement local pour les providers `placeholder` et `local`
  - [x] Ajouter des assertions de non-appel distant dans les tests de non-regression
- [x] Preserver les garanties de resolution et de runtime config existantes (AC: 1, 5)
  - [x] Reutiliser `analysis/resolution.py` pour selectionner `provider_key` et fusionner les params
  - [x] Ne pas dupliquer la logique de reload atomique de `common/config_runtime.py`
  - [x] Verifier que `model_used`, `latency_sec`, `tokens_in`, `tokens_out` restent coherents avec le provider `remote_gemini25`
- [x] Ajouter la couverture de tests unitaires/integration pour le provider distant (AC: 1, 2, 3, 4, 5)
  - [x] Tests `inference/client.py` pour succes distant, erreurs auth, timeout, indisponibilite, format invalide
  - [x] Tests `analysis/service.py` pour propagation des erreurs 503/500 et preservation du contrat de reponse
  - [x] Tests de configuration pour credentials manquants et cloud non active (garde-fous local-first)

## Dev Notes

- Story 2.5 complete l Epic 2 apres 2.1/2.2/2.3/2.4 en ajoutant le chemin distant configurable sans casser les invariants MVP (stateless, contrat API stable, local-first par defaut).
- Le principal risque est un contournement implicite du mode local-first; tout chemin cloud doit etre explicitement active et testable.
- Le second risque est la divergence de contrat entre `remote_gemini25` et les providers locaux; l adaptateur doit normaliser les metriques et erreurs de la meme maniere.

### Developer Context Section

- **Contexte Epic 2:** configuration metier sans code, et maintenant extension du provider `remote_gemini25` sans regressions sur l execution locale.
- **Valeur business 2.5:** resilier l analyse quand l inference locale n est pas suffisante, tout en gardant la souverainete par defaut.
- **Chainage stories:**
  - Story 2.3 a centralise la resolution prompt -> provider/model + params.
  - Story 2.4 a impose un snapshot runtime atomique pour modeles/analysis-profiles/routing.
  - Story 2.5 doit reutiliser ces fondations, pas les contourner.

### Technical Requirements

- Garder un contrat de sortie unique pour `LocalInferenceAdapter.infer(...)` quel que soit le provider (`local`, `placeholder`, `remote`).
- Les secrets provider distant doivent etre lus via environnement (ex: `os.getenv`) et jamais stockes dans `config/inference_engines.yaml`.
- Erreurs distantes a mapper en erreurs metier existantes:
  - timeout/reseau/indisponibilite -> `InferenceAdapterServiceUnavailableError`
  - format reponse invalide -> `InferenceAdapterInternalError`
- Conserver la validation stricte des params (`ALLOWED_PROVIDER_PARAMS`, `allowed_params`) pour eviter les derives provider-specifiques.
- Respecter les SLA existants et ne pas introduire de blocage hors timeout configure.

### Architecture Compliance

- Respect strict des boundaries:
  - `analysis/service.py` orchestre sans details transport.
  - `inference/adapter.py` reste facade metier vers le client.
  - `inference/client.py` gere transport HTTP.
  - `inference/models_config.py` reste source de verite schema/validation.
- Maintenir `snake_case` partout (code, JSON, query params).
- Ne pas introduire de persistance, cache metier, ou etat global non controle.

### Library/Framework Requirements

- FastAPI: conserver contrat API et mapping erreurs actuel (pas de rupture endpoint).
- Pydantic: continuer `ConfigDict(extra="forbid", strict=True)` pour proteger les configs provider.
- Uvicorn: aucun besoin de reload serveur pour ce scope (reload applicatif deja gere par runtime snapshot).
- HTTP client: rester compatible avec la pile actuelle basee `urllib.request` (ou equivalent interne) tant que le contrat et les tests sont preserves.

### File Structure Requirements

- Fichiers cibles probables:
  - `backend/src/inference/client.py`
  - `backend/src/inference/adapter.py`
  - `backend/src/inference/models_config.py`
  - `backend/src/analysis/service.py`
  - `backend/src/analysis/resolution.py`
  - `backend/tests/inference/test_adapter.py`
  - `backend/tests/analysis/test_service.py`
  - `backend/tests/inference/test_client.py` (nouveau si necessaire)
  - `backend/tests/test_config_yaml.py`
  - `config/inference_engines.yaml`

### Testing Requirements

- AC1: test bout-en-bout d un provider `remote_gemini25` valide avec sortie normalisee identique au mode local.
- AC2: test cloud desactive par defaut -> aucun appel distant effectif.
- AC3: test credentials manquants -> erreur explicite sans exposition de secret.
- AC4: test erreurs distantes (timeout/auth/quota/down) -> mapping stable vers contrat API (`503`/`500`).
- AC5: test succes distant -> `model_used` et metriques techniques exposes correctement.

### Previous Story Intelligence

- Story 2.4 a impose `RuntimeConfigManager` et `RuntimeConfigSnapshot`; 2.5 doit consommer ce snapshot, pas relire des configs de maniere ad hoc.
- Story 2.4 a deja verrouille atomicite/rollback; 2.5 ne doit pas reintroduire de split-brain entre routing, resolution et inference.
- Story 2.4 a deja stabilise les metadonnees runtime; 2.5 doit les maintenir identiques quand provider=`remote_gemini25`.

### Git Intelligence Summary

- Historique recent coherent et progressif: 2.1 -> 2.2 -> 2.3 -> 2.4, avec focus sur config, resolution et runtime coherence.
- Fichiers critiques repetitifs dans les 5 derniers commits: `analysis/service.py`, `analysis/resolution.py`, `analysis/routing.py`, `inference/adapter.py`, `inference/client.py`, `inference/models_config.py`.
- Pattern de livraison etabli: story file complet + mise a jour `sprint-status.yaml` + tests backend associes.

### Latest Tech Information

- FastAPI `0.129.0` est publie avec rupture Python 3.9 (stack moderne requise). [Source: https://github.com/fastapi/fastapi/releases]
- Pydantic `2.12.5` est la reference stable recente de la branche 2.12. [Source: https://docs.pydantic.dev/latest/changelog/]
- Uvicorn `0.40.0` retire Python 3.9 et confirme l alignement avec stack recente. [Source: https://uvicorn.dev/release-notes/]
- HTTPX `0.28.1` documente un correctif SSL notable; utile si evolution future du client HTTP. [Source: https://github.com/encode/httpx/releases]

### Project Structure Notes

- Aucun `project-context.md` detecte via pattern `**/project-context.md`.
- Contexte exploite: `epics.md`, `architecture.md`, `prd.md`, `ux-design-specification.md`, `sprint-status.yaml`, story precedente `2-4-*.md`, code actuel backend, et historique git recent.

### References

- Story 2.5 + AC: [Source: `_bmad-output/planning-artifacts/epics.md#Story 2.5`]
- Contraintes FR/NFR (FR34, FR8, NFR4, NFR6, NFR8, NFR14): [Source: `_bmad-output/planning-artifacts/prd.md#Functional Requirements`], [Source: `_bmad-output/planning-artifacts/prd.md#Non-Functional Requirements`]
- Boundaries/patterns: [Source: `_bmad-output/planning-artifacts/architecture.md#Implementation Patterns & Consistency Rules`], [Source: `_bmad-output/planning-artifacts/architecture.md#Project Structure & Boundaries`]
- UX erreur/neutralite/preservation saisie: [Source: `_bmad-output/planning-artifacts/ux-design-specification.md#Feedback Patterns`]
- Intelligence story precedente: [Source: `_bmad-output/implementation-artifacts/2-4-activer-la-prise-en-compte-des-changements-de-configuration-sans-redemarrage.md`]
- Code actuel du chemin inference: [Source: `backend/src/inference/adapter.py`], [Source: `backend/src/inference/client.py`], [Source: `backend/src/inference/models_config.py`]

### Story Completion Status

- Story context cree avec statut `ready-for-dev`.
- Note de completion: Ultimate context engine analysis completed - comprehensive developer guide created.

## Dev Agent Record

### Agent Model Used

openai/gpt-5.3-codex

### Debug Log References

- Artefacts analyses: `epics.md`, `architecture.md`, `prd.md`, `ux-design-specification.md`, `sprint-status.yaml`.
- Story precedente analysee: `2-4-activer-la-prise-en-compte-des-changements-de-configuration-sans-redemarrage.md`.
- Historique git recent analyse: 5 derniers commits + fichiers modifies.
- Veille technique effectuee: FastAPI, Pydantic, Uvicorn, HTTPX.

### Implementation Plan

- Etendre `ProviderConfig` pour durcir la validation du provider `remote_gemini25` (champs requis et auth env var).
- Introduire un gate explicite `cloud_enabled` pour bloquer tout appel distant implicite.
- Implementer le chemin HTTP du provider `remote_gemini25` dans `inference/client.py` avec header d authentification via variable d environnement.
- Mapper proprement les erreurs HTTP/reseau vers erreurs metier deja consommees par l adaptateur/service.
- Renforcer les tests unitaires/integration (client, config, service) pour succes, garde-fous local-first, erreurs 503/500.

### Completion Notes List

- Provider `remote_gemini25` supporte avec validation stricte (`base_url`, `endpoint`, `auth_env_var`) et activation explicite `cloud_enabled`.
- Chemin distant implemente dans `inference/client.py` avec authentification via environnement uniquement (`Bearer`), sans secret en config.
- Mapping erreurs du provider `remote_gemini25` ajoute: auth/quota/5xx/reseau/timeout vers erreurs metier maitrisees, sans fuite de secret.
- Contrat de sortie canonique conserve et metadonnees techniques (`model_used`, `tokens_*`, `latency_sec`) preservees.
- Garde-fou local-first ajoute: cloud desactive => aucun appel distant effectif.
- Validation complete executee: `uv run pytest` (98 passed) et `uv run ruff check src tests` (OK).

### File List

- backend/src/inference/models_config.py
- backend/src/inference/client.py
- backend/tests/inference/test_client.py
- backend/tests/inference/test_models_config.py
- backend/tests/analysis/test_service.py
- config/inference_engines.yaml
- _bmad-output/implementation-artifacts/2-5-supporter-un-provider-d-inference-distant-configurable.md
- _bmad-output/implementation-artifacts/sprint-status.yaml

## Change Log

- 2026-02-13: Ajout du support `remote_gemini25` avec activation explicite cloud, auth via environnement, mapping erreurs distant, et couverture de tests associee.
