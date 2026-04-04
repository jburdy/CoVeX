# Story 2.4: Activer la prise en compte des changements de configuration sans redemarrage

> Note 2026-03-14: artefact BMAD historique. Certaines references internes
> (tests, modules, `criteria`, hot reload, pages playground) peuvent ne plus
> correspondre exactement au depot courant. Pour l'etat actuel, se fier a
> `README.md`, `docs/ARCHITECTURE.md` et `docs/ANALYSIS_PROFILES_METIER.md`.


Status: review

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a configurateur,
I want que les changements de prompts et modeles soient pris en compte rapidement sans redemarrer CoVeX,
so that je puisse iterer sur la qualite metier en continu.

## Acceptance Criteria

1. **Given** un ajout, une modification ou une suppression dans les fichiers de configuration prompts et modeles **When** le mecanisme de reload est declenche **Then** les changements deviennent actifs en moins de 5 secondes **And** aucune recompilation ni redeploiement n est necessaire.
2. **Given** un reload de configuration est en cours **When** des requetes d analyse arrivent simultanement **Then** le service reste stable et repond sans etat incoherent **And** la transition entre ancienne et nouvelle configuration est atomique.
3. **Given** une nouvelle configuration invalide est detectee lors du reload **When** la validation echoue **Then** le systeme conserve la derniere configuration valide **And** il journalise explicitement la raison du rejet.
4. **Given** une modification de prompt est appliquee **When** une requete `POST /analyze` suivante est executee **Then** la nouvelle version du prompt est utilisee immediatement **And** le comportement est observable via `profile_used` et traces techniques.
5. **Given** une modification du modele actif est appliquee **When** une nouvelle analyse est lancee **Then** le nouveau modele est pris en compte sans redemarrage **And** `model_used` confirme le changement effectif.

## Tasks / Subtasks

- [x] Introduire un runtime config manager avec snapshots atomiques pour modeles/analysis-profiles/routing (AC: 1, 2, 3)
  - [x] Ajouter un module dedie (`backend/src/common/config_runtime.py` ou equivalent) qui maintient le dernier snapshot valide
  - [x] Definir un contrat de chargement unique: `load -> validate -> commit atomique` (jamais de demi-etat)
  - [x] Ajouter horodatage/version interne du snapshot pour debug et tests
- [x] Brancher les couches metier sur ce snapshot au lieu de relire YAML a chaque appel (AC: 1, 2, 4, 5)
  - [x] Remplacer les points de chargement direct (`load_models_config`, `load_prompts_config`, routing) par une lecture runtime centralisee
  - [x] Garantir que `analysis/service.py`, `analysis/resolution.py`, `analysis/routing.py`, `inference/adapter.py` lisent tous la meme version active
  - [x] Preserver les signatures API existantes et le contrat FastAPI MVP
- [x] Implementer le declenchement de reload sans redemarrage (AC: 1)
  - [x] Ajouter un mecanisme deterministe (polling mtime leger ou watcher) avec SLA < 5s
  - [x] Eviter toute boucle bloquante dans le thread request/response
  - [x] Ajouter logs de transition (ancien snapshot -> nouveau snapshot)
- [x] Gerer explicitement les echecs de reload avec rollback automatique (AC: 3)
  - [x] En cas d invalidite YAML/schema/references, conserver le snapshot precedent
  - [x] Journaliser raison precise sans exposer de secrets
  - [x] Rendre visible l etat via logs techniques exploitables
- [x] Verifier la coherence fonctionnelle sur prompt/model changes (AC: 4, 5)
  - [x] Valider qu un changement de prompt est visible sur la requete suivante via `profile_used`
  - [x] Valider qu un changement de modele actif est visible sur la requete suivante via `model_used`
  - [x] S assurer que la fusion de params provider reste deterministic avec la nouvelle config
- [x] Ajouter couverture de tests de concurrence + non-regression (AC: 1, 2, 3, 4, 5)
  - [x] Tests unitaires runtime manager (commit atomique, rollback, versioning)
  - [x] Tests integration API `POST /analyze` pendant reload concurrent
  - [x] Tests de delai max de prise en compte (< 5s) avec horodatage controle

## Dev Notes

- Cette story est le pivot d Epic 2: apres 2.1 (modeles), 2.2 (prompts), 2.3 (resolution), il faut rendre ces configurations dynamiques sans casser la stabilite runtime.
- Le risque principal est le split-brain de configuration (routing sur ancienne config, inference sur nouvelle): imposer un snapshot unique partage.
- Reuse obligatoire: ne pas dupliquer la validation YAML/Pydantic deja en place dans `inference/models_config.py` et `prompts/repository.py`.

### Developer Context Section

- **Contexte Epic 2:** evoluer metier via configuration uniquement, sans redemarrage et sans modification de code.
- **Valeur business 2.4:** iteration metier rapide (prompts/modeles) sans interruption de service.
- **Chainage stories:**
  - Story 2.1 a verrouille la validite de `inference_engines.yaml` et la coherence provider/model.
  - Story 2.2 a verrouille la validite de `analysis_profiles.yaml` et l exposition des prompts.
  - Story 2.3 a centralise la resolution runtime (`analysis/resolution.py`) et les metadata `profile_used/model_used`.

### Technical Requirements

- Introduire un snapshot runtime immutable regroupant au minimum:
  - models config valide,
  - prompts runtime valides,
  - routing config valide,
  - metadonnees de version (`loaded_at`, `revision`).
- Pipeline obligatoire de reload: `detect change -> parse -> validate -> commit atomique`.
- Si validation echoue:
  - aucune mutation du snapshot actif,
  - log explicite de cause,
  - service continue avec la derniere config valide.
- Contrat de coherence multi-requetes:
  - une requete voit une seule version du snapshot du debut a la fin,
  - aucune lecture croisee entre versions.
- SLA story:
  - prise en compte d un changement valide en < 5 secondes.

### Architecture Compliance

- Respecter feature-first + snake_case.
- Garder les boundaries:
  - API: `backend/src/analysis/api.py`,
  - metier: `backend/src/analysis/service.py`,
  - config loaders: `backend/src/inference/models_config.py`, `backend/src/analysis-profiles/repository.py`,
  - inference: `backend/src/inference/adapter.py`.
- Interdictions:
  - pas de hot-reload via restart process,
  - pas de cache metier persistant,
  - pas de logique de reload dispersee dans plusieurs features.

### Library/Framework Requirements

- **FastAPI 0.128.x:** conserver la couche API actuelle; aucun changement de contrat endpoint.
- **Pydantic 2.12.x:** conserver la validation stricte des configs; reutiliser les modeles existants.
- **Uvicorn 0.40.x:** aucun mecanisme de reload serveur requis pour cette story (reload applicatif uniquement).
- **HTTPX 0.28.1:** aucun impact direct attendu; ne pas contourner l adaptateur inference.
- **Watch strategy:** privilegier un mecanisme simple et testable (polling mtime ou watcher dedie) garantissant < 5s.

### File Structure Requirements

- Fichiers cibles probables:
  - `backend/src/common/` (nouveau module runtime config)
  - `backend/src/analysis/service.py`
  - `backend/src/analysis/resolution.py`
  - `backend/src/analysis/routing.py`
  - `backend/src/inference/adapter.py`
  - `backend/src/analysis-profiles/service.py`
  - `backend/src/main.py` (wiring init runtime)
- Fichiers de configuration observes par reload:
  - `config/inference_engines.yaml`
  - `config/analysis_profiles.yaml`
  - `config/routing.yaml`
- Tests cibles:
  - `backend/tests/analysis/test_service.py`
  - `backend/tests/analysis/test_routing.py`
  - `backend/tests/inference/test_adapter.py`
  - `backend/tests/test_config_yaml.py`
  - `backend/tests/common/test_config_runtime.py` (nouveau)

### Testing Requirements

- AC1: test de propagation changement config < 5s sans redemarrage process.
- AC2: test de concurrence (requetes en parallele pendant reload) sans incoherence.
- AC3: test config invalide -> rollback snapshot precedent + log.
- AC4: test prompt modifie -> `profile_used` et comportement analyses immediatement mis a jour.
- AC5: test modele modifie -> `model_used` mis a jour immediatement.
- Ajouter test anti-regression sur atomicite (pas de lecture partielle entre deux commits).

### Previous Story Intelligence

- Story 2.3 a deja centralise la resolution dans `analysis/resolution.py` et impose la fusion deterministic des params provider.
- Story 2.3 a aussi stabilise la coherence des metadata (`profile_used`, `model_used`, `latency_sec`, `tokens_*`) via tests.
- La nouvelle logique de reload doit proteger ces invariants; ne pas les recalculer via chemins paralleles.

### Git Intelligence Summary

- Les 5 derniers commits confirment la progression: 1.5 erreurs API -> 1.6 mecanisme retire -> 2.1 config modeles -> 2.2 config prompts -> 2.3 resolution runtime.
- Les modules les plus actifs et critiques pour 2.4 sont deja identifies: `analysis/service.py`, `analysis/resolution.py`, `analysis/routing.py`, `inference/adapter.py`, `prompts/*`.
- Pattern d execution observe: commit story + mise a jour `sprint-status.yaml` + tests backend avant passage en review.

### Latest Tech Information

- FastAPI `0.128.8` (ligne 0.128.x): pas de breaking change majeur pour ce scope; maintenir la compatibilite de l app actuelle. [Source: https://fastapi.tiangolo.com/release-notes/]
- Pydantic `2.12.5`: patch stable, pertinent pour validation stricte sous Python 3.14; continuer a s appuyer sur `model_validate`. [Source: https://docs.pydantic.dev/latest/changelog/]
- Uvicorn `0.40.0`: support Python 3.9 retire; alignement OK avec stack recente. Pour cette story, reload applicatif > reload serveur. [Source: https://uvicorn.dev/release-notes/]
- HTTPX `0.28.1`: correctif SSL important de 0.28.1, conserver cette base pour les appels inference. [Source: https://github.com/encode/httpx/releases]
- Option watcher Python: `watchfiles 1.1.1` existe si mecanisme event-driven requis; toutefois une strategie simple testable reste prioritaire en MVP. [Source: https://pypi.org/project/watchfiles/]

### Project Structure Notes

- Aucun `project-context.md` detecte via `**/project-context.md`.
- Contexte utilise: `epics.md`, `architecture.md`, `prd.md`, `ux-design-specification.md`, `sprint-status.yaml`, story precedente `2-3-*.md`, historique git recent.

### References

- Story 2.4 et AC: [Source: `_bmad-output/planning-artifacts/epics.md#Story 2.4`]
- FR/NFR relies (FR10, FR15, NFR9): [Source: `_bmad-output/planning-artifacts/prd.md#Functional Requirements`], [Source: `_bmad-output/planning-artifacts/prd.md#Non-Functional Requirements`]
- Boundaries, patterns, structure: [Source: `_bmad-output/planning-artifacts/architecture.md#Implementation Patterns & Consistency Rules`], [Source: `_bmad-output/planning-artifacts/architecture.md#Project Structure & Boundaries`]
- UX erreurs et preservation etat: [Source: `_bmad-output/planning-artifacts/ux-design-specification.md#Feedback Patterns`]
- Story precedente 2.3: [Source: `_bmad-output/implementation-artifacts/2-3-appliquer-la-resolution-prompt-vers-modele-et-parametres-provider.md`]
- Git recent: [Source: `git log` local (dfdccfc, 38da8de, 23661d5, 21e106a, 7e1313e)]

### Story Completion Status

- Story context cree avec statut `ready-for-dev`.
- Note de completion: Ultimate context engine analysis completed - comprehensive developer guide created.

## Dev Agent Record

### Agent Model Used

openai/gpt-5.3-codex

### Debug Log References

- Artefacts analyses: `epics.md`, `architecture.md`, `prd.md`, `ux-design-specification.md`, `sprint-status.yaml`.
- Story precedente analysee: `2-3-appliquer-la-resolution-prompt-vers-modele-et-parametres-provider.md`.
- Historique git recent analyse: 5 derniers commits + fichiers modifies.
- Veille technique effectuee: FastAPI, Pydantic, Uvicorn, HTTPX, watchfiles.

### Implementation Plan

- Introduire un gestionnaire runtime central (`RuntimeConfigManager`) avec snapshot immutable, version/revision, horodatage et commit atomique sous lock.
- Basculer la resolution metier (`analysis/service.py`, `analysis/resolution.py`, `analysis/routing.py`) vers une lecture unique du snapshot actif par requete.
- Aligner l adaptateur inference (`inference/adapter.py`) sur le meme `ModelsConfig` du snapshot pour eviter toute lecture croisee entre versions.
- Ajouter les tests unitaires/integration pour commit, rollback, polling, changements prompt/modele, et stabilite API en concurrence.

### Completion Notes List

- Runtime config manager ajoute avec pipeline `detect change -> parse -> validate -> commit atomique` et rollback automatique en cas d erreur.
- `analysis/service.py` recharge via manager runtime a chaque fenetre de polling, puis injecte le meme snapshot dans resolution/routing/inference pour coherence de version.
- `analysis/resolution.py` et `analysis/routing.py` supportent le snapshot runtime partage; `inference/adapter.py` accepte le `ModelsConfig` actif de la requete.
- Logs techniques ajoutes pour commits de snapshot et rejets de reload (`Config reload rejected`) avec conservation de la derniere version valide.
- Tests ajoutes: runtime manager (revision, rollback, polling), API concurrente pendant reload, propagation prompt/model sur requete suivante.
- Validation complete executee: `pytest` (88 passes) + `ruff check src tests` (OK).

### File List

- _bmad-output/implementation-artifacts/2-4-activer-la-prise-en-compte-des-changements-de-configuration-sans-redemarrage.md
- _bmad-output/implementation-artifacts/sprint-status.yaml
- backend/src/common/config_runtime.py
- backend/src/analysis-profiles/service.py
- backend/src/analysis/routing.py
- backend/src/analysis/resolution.py
- backend/src/analysis/service.py
- backend/src/inference/adapter.py
- backend/tests/common/test_config_runtime.py
- backend/tests/analysis/test_service.py
- backend/tests/analysis/test_api.py

## Change Log

- 2026-02-12: Story 2.4 creee en statut ready-for-dev avec contexte implementation complet (reload atomique, rollback, concurrence, tests et garde-fous architecture).
- 2026-02-12: Implementation terminee - runtime config manager atomique, wiring snapshot unique cross-features, rollback explicite, et couverture de tests AC1-AC5.
