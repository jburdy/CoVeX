# Story 2.1: Charger et valider la configuration des modeles

> Note 2026-03-14: artefact BMAD historique. Certaines references internes
> (tests, modules, `criteria`, hot reload, pages playground) peuvent ne plus
> correspondre exactement au depot courant. Pour l'etat actuel, se fier a
> `README.md`, `docs/ARCHITECTURE.md` et `docs/ANALYSIS_PROFILES_METIER.md`.


Status: review

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a configurateur,
I want definir les modeles disponibles dans un fichier de configuration valide,
so that je puisse changer le modele actif sans modifier le code applicatif.

## Acceptance Criteria

1. **Given** un fichier `inference_engines.yaml` conforme est present **When** le service demarre **Then** la liste des modeles est chargee en memoire **And** chaque modele expose son provider et ses parametres utiles.
2. **Given** un modele est marque actif dans la configuration **When** une analyse est executee sans override specifique **Then** ce modele est utilise par defaut **And** `model_used` reflete effectivement ce choix.
3. **Given** une configuration modele invalide (champ manquant, type invalide, doublon d identifiant) **When** le chargement est tente **Then** le service rejette la configuration avec erreur explicite **And** aucune configuration partiellement incoherente n est appliquee.
4. **Given** un changement du modele actif est fait uniquement dans la configuration **When** la configuration est re-evaluee selon la strategie de reload **Then** le nouveau modele devient actif sans changement de code **And** la transition reste tracable dans les logs techniques.

## Tasks / Subtasks

- [x] Introduire un chargeur/validateur de configuration modeles unique et reutilisable (AC: 1, 3)
  - [x] Definir des schemas Pydantic v2 pour `inference_engines.yaml` (default_provider, providers, mecanisme retire, parametres provider)
  - [x] Charger YAML via `yaml.safe_load` puis valider strictement le payload
  - [x] Rejeter explicitement les champs critiques absents, types invalides et references incoherentes
  - [x] Ajouter des erreurs explicites exploitables en logs sans fuite de secrets
- [x] Raccorder la selection du modele actif a l execution d inference (AC: 2)
  - [x] Remplacer les chemins implicites/placeholder par une resolution deterministic basee sur config validee
  - [x] Garantir que `model_used` retourne correspond exactement au modele effectivement utilise
  - [x] Preserver le contrat `POST /analyze` existant et la separation `analysis -> inference adapter -> inference client`
- [x] Poser les guardrails de non-regression sur la config (AC: 1, 2, 3)
  - [x] Etendre les tests unitaires inference pour couvrir config valide/invalide et mapping du modele actif
  - [x] Ajouter des tests de validation de schema (manquant/type incorrect/id duplique/reference inconnue)
  - [x] Verifier qu aucune config partielle n est acceptee si validation KO
- [x] Preparer la base pour le reload sans redemarrage (AC: 4, handoff Story 2.4)
  - [x] Encapsuler la logique de lecture/validation pour etre re-evaluable sans effets de bord
  - [x] Journaliser les transitions de configuration de facon concise et stable
  - [x] Ne pas implementer le watcher de fichier dans cette story (scope Story 2.4)

## Dev Notes

- Cette story ouvre Epic 2: la priorite est de rendre la configuration modeles fiable, validable et source unique de verite.
- Le code actuel contient deja `config/inference_engines.yaml` et une lecture YAML cote inference; cette story doit consolider et fiabiliser cette base plutot que dupliquer des parseurs.

### Developer Context Section

- **Objectif Epic 2:** activer la personnalisation metier par fichiers sans modification de code ni hardcode des modeles.
- **Valeur business immediate:** changement de modele actif par edition config, sans redeploiement de code.
- **Contexte existant utile:**
  - `backend/src/inference/client.py` lit deja `inference_engines.yaml` mais avec validation permissive insuffisante.
  - `backend/src/inference/adapter.py` et `backend/src/analysis/service.py` transportent deja `model_used` jusqu a la reponse API.
  - `config/inference_engines.yaml` existe avec structure placeholder (`providers`, `mecanisme retire`, `default_provider`).
- **Contrainte de scope:** implementer chargement/validation robuste et resolution du modele actif; garder le hot-reload complet pour Story 2.4.

### Technical Requirements

- Utiliser une validation stricte de configuration (Pydantic v2) avant toute utilisation runtime.
- Imposer une coherence minimale:
  - `default_provider` doit etre resolvable,
  - chaque provider doit avoir un identifiant, un type connu, et les parametres requis,
  - les references mecanisme retire (`primary_provider`, `mecanisme retire_provider`) doivent pointer vers des providers existants.
- En cas d invalidite:
  - ne jamais appliquer une configuration partielle,
  - lever une erreur explicite,
  - conserver un comportement deterministic cote API (pas d etat ambigu).
- Eviter la reinvention:
  - centraliser le parsing/validation dans un module dedie,
  - reutiliser ce module depuis `inference/client.py`, `inference/adapter.py` et futurs points de reload.

### Architecture Compliance

- Respecter `snake_case` pour code Python, YAML keys et JSON.
- Respecter l organisation feature-first backend existante (`analysis`, `inference`, `common`, `prompts`, `health`).
- Garder les frontieres:
  - API dans `backend/src/analysis/api.py`,
  - orchestration metier dans `backend/src/analysis/service.py`,
  - details configuration/inference dans `backend/src/inference/*`.
- Ne pas introduire DB/cache/persistence de textes utilisateur (stateless strict).
- Conserver erreurs FastAPI MVP cote API; les details techniques restent cote logs.

### Library/Framework Requirements

- **FastAPI:** architecture cible documentee sur la ligne `0.128.x`; ne pas coupler cette story a un upgrade framework.
- **Pydantic:** utiliser v2 (required avec Python 3.14); ne pas utiliser `pydantic.v1`.
- **PyYAML:** conserver `yaml.safe_load` exclusivement pour eviter les risques de deserialization.
- **Runtime inference:** rester compatible avec l adaptateur/mecanisme retire existant (`inference/adapter.py`, `inference/mecanisme retire.py`).

### File Structure Requirements

- Fichiers cibles prioritaires:
  - `backend/src/inference/client.py`
  - `backend/src/inference/adapter.py`
  - `backend/src/inference/mecanisme retire.py` (si adaptation de validation mecanisme retire necessaire)
  - `config/inference_engines.yaml`
- Fichiers recommandables a creer pour eviter duplication:
  - `backend/src/inference/models_config.py` (schemas + validation + chargement) ou equivalent dans `inference/`.
- Fichiers de tests a etendre:
  - `backend/tests/test_config_yaml.py`
  - `backend/tests/inference/test_adapter.py`
  - ajouter des tests dedies config modeles sous `backend/tests/inference/`.

### Testing Requirements

- Verifier qu une configuration valide charge correctement et expose les valeurs attendues.
- Verifier que `default_provider` est effectivement celui utilise sans override et que `model_used` le reflete.
- Verifier erreurs explicites pour:
  - champ obligatoire manquant,
  - type invalide,
  - identifiant duplique,
  - reference provider inconnue,
  - fichier YAML mal forme.
- Verifier qu aucune configuration partielle n est appliquee apres echec validation.
- Verifier non-regression du contrat `/analyze` (succes + metadonnees optionnelles).

### Latest Tech Information

- FastAPI release notes indiquent la branche `0.128.x` active; garder la compatibilite de code sur cette ligne pour limiter le risque de regression.
- FastAPI confirme la fin du support Pydantic v1 sur versions recentes (notamment Python 3.14); rester strictement sur Pydantic v2.
- Les bonnes pratiques YAML en Python imposent `safe_load` pour eviter le parsing dangereux de contenu non fiable.

### Project Structure Notes

- Aucun `project-context.md` detecte via `**/project-context.md`.
- Contexte utilise pour cette story: `epics.md`, `architecture.md`, `prd.md`, `ux-design-specification.md`, `sprint-status.yaml`, code backend actuel (`analysis/*`, `inference/*`) et configs `config/*.yaml`.

### References

- Story 2.1 et AC: [Source: _bmad-output/planning-artifacts/epics.md#Story 2.1]
- FR/NFR de configuration dynamique: [Source: _bmad-output/planning-artifacts/prd.md#Configuration des Modeles], [Source: _bmad-output/planning-artifacts/prd.md#Non-Functional Requirements]
- Boundaries architecture/patterns: [Source: _bmad-output/planning-artifacts/architecture.md#Implementation Patterns & Consistency Rules], [Source: _bmad-output/planning-artifacts/architecture.md#Project Structure & Boundaries]
- Exigences UX/API transverses (erreurs claires, preserv. saisie): [Source: _bmad-output/planning-artifacts/ux-design-specification.md#Feedback Patterns]
- Baseline implementation actuelle: [Source: backend/src/inference/client.py], [Source: backend/src/inference/adapter.py], [Source: backend/src/analysis/service.py], [Source: config/inference_engines.yaml], [Source: backend/tests/test_config_yaml.py]
- Veille technique: [Source: https://fastapi.tiangolo.com/release-notes/], [Source: https://fastapi.tiangolo.com/how-to/migrate-from-pydantic-v1-to-pydantic-v2/], [Source: https://pyyaml.org/wiki/PyYAMLDocumentation]

### Story Completion Status

- Story context cree avec statut `ready-for-dev`.
- Note de completion: Ultimate context engine analysis completed - comprehensive developer guide created.

## Dev Agent Record

### Agent Model Used

openai/gpt-5.3-codex

### Debug Log References

- Analyse artefacts: `epics.md`, `prd.md`, `architecture.md`, `ux-design-specification.md`, `sprint-status.yaml`.
- Analyse code existant: `backend/src/analysis/*`, `backend/src/inference/*`, `config/*.yaml`, `backend/tests/*`.
- Veille technique: FastAPI release notes, migration Pydantic v2, recommandations YAML safe loading.
- Execution tests/qualite: `uv run pytest`, `uv run pytest tests/inference/test_models_config.py tests/inference/test_adapter.py tests/test_config_yaml.py`, `uv run ruff check src tests`.

### Implementation Plan

- Creer un module unique `inference/models_config.py` pour centraliser parsing YAML, validation stricte Pydantic v2 et coherence runtime.
- Brancher ce module dans `inference/client.py`, `inference/adapter.py` et `inference/timeouts.py` pour supprimer les chemins permissifs implicites.
- Rendre la resolution du modele actif deterministic via `default_provider` + mapping provider, sans casser le contrat `POST /analyze`.
- Ajouter des tests de non-regression et de validation schema couvrant AC 1/2/3 et la base de reload AC 4.

### Completion Notes List

- Story 2.1 contextualisee pour implementation robuste et sans duplication du chargement de configuration modeles.
- Guardrails explicites ajoutes pour prevenir mauvaises bibliotheques, mauvaises localisations de fichiers, et regressions API.
- Contraintes architecture, NFR, et patterns existants integres pour accelerer `dev-story` sur Epic 2.
- Ajout de `backend/src/inference/models_config.py` avec schemas Pydantic v2 stricts, detection de cles YAML dupliquees, validation de coherence (`default_provider`, providers, mecanisme retire) et erreurs explicites `ModelsConfigurationError`.
- Migration des points runtime vers la config validee: `inference/client.py` (selection provider deterministic), `inference/adapter.py` (propagation `config_dir`, mapping modele actif), `inference/timeouts.py` (timeout derive du provider actif valide).
- Base de reload preparee via logique pure re-evaluable + `log_config_transition` (format stable et concis), sans watcher de fichier (hors scope Story 2.4).
- Couverture tests et non-regression: nouveaux tests `test_models_config.py`, extension `test_adapter.py` et `test_config_yaml.py`; suite complete backend et lint passes.

### File List

- _bmad-output/implementation-artifacts/2-1-charger-et-valider-la-configuration-des-modeles.md
- _bmad-output/implementation-artifacts/sprint-status.yaml
- backend/src/inference/models_config.py
- backend/src/inference/client.py
- backend/src/inference/adapter.py
- backend/src/inference/timeouts.py
- backend/tests/inference/test_models_config.py
- backend/tests/inference/test_adapter.py
- backend/tests/test_config_yaml.py
- config/inference_engines.yaml

## Change Log

- 2026-02-12: Story 2.1 creee avec contexte complet, exigences techniques, guardrails architecture, references de code existant, et statut `ready-for-dev`.
- 2026-02-12: Implementation Story 2.1 terminee: validation stricte config modeles (Pydantic v2), resolution deterministic du modele actif, guardrails de tests, et statut passe a `review`.

## Senior Developer Review (AI)

### Review Summary
- **Reviewer:** JBU
- **Date:** 2026-02-23
- **Outcome:** Approved with notes

### Findings

#### High Severity
- None

#### Medium Severity
- **Chaîne try/except excessive dans adapter.py (188-227):** Le code utilise 7 niveaux de try/except imbriqués pour gérer la compatibilité backward du client. Suggestion: créer une fonction wrapper utilisant `inspect` pour gérer les signatures dynamiquement.

#### Low Severity
- **AC4 partiellement implémentée:** La task "Preparer la base pour le reload sans redemarrage" est marquée [x] mais le watcher n'est pas implémenté (scope Story 2.4 explicitement). Le code contient `log_config_transition()` mais pas de mécanisme de rechargement automatique. Le comportement est conforme aux attentes de scope.

### Verification
- ✅ Tests unitaires: 107 passent
- ✅ Lint (ruff): All checks passed
- ✅ AC1-AC3 fully implemented
- ✅ AC4: base préparationnelle en place (hors scope watcher)
- ✅ File List: tous les fichiers existants

### Notes
- La validation stricte Pydantic v2 est bien implémentée
- La gestion des erreurs est explicite et sans fuite de secrets
- La résolution du modele actif est deterministic
- La structure est conforme aux conventions snake_case et feature-first
