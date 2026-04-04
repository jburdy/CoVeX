# Story 1.1: Set up initial project from starter template

Status: review

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a developer,
I want initialiser CoVeX avec le starter `fastapi/fastapi-new` et la structure de base cible,
so that l equipe peut implementer les stories suivantes sur une fondation conforme a l architecture.

## Acceptance Criteria

1. **Given** un workspace vide pour l implementation **When** le starter `fastapi/fastapi-new` est initialise (`uvx fastapi-new covex`) **Then** la base projet est creee avec dependances et outillage de dev standard **And** la structure permet d ajouter `backend/src/main.py` et `playground/src/app.py` selon l architecture cible.
2. **Given** la base projet est creee **When** les fichiers de configuration minimum (`.env.example`, YAML de config) sont poses **Then** les points d entree de l application peuvent demarrer localement **And** aucune logique metier non necessaire n est implementee dans cette story.
3. **Given** l architecture impose une progression incrementale **When** cette story est terminee **Then** elle fournit uniquement la fondation technique immediate requise **And** elle n introduit pas de travail massif hors besoin des stories suivantes.
4. **Given** la story est prete pour handoff **When** l equipe relit les artefacts de demarrage **Then** les conventions de nommage et structure (snake_case, boundaries feature-first) sont appliquees **And** les stories Epic 1 suivantes peuvent demarrer sans blocage d infrastructure.

## Tasks / Subtasks

- [x] Initialiser le projet avec le starter officiel (AC: 1)
  - [x] Executer `uvx fastapi-new covex` a la racine du repository de travail (ne pas ecraser des fichiers existants)
  - [x] Verifier que le squelette genere est present et demarre via les commandes de dev du starter
  - [x] Conserver le scope strictement bootstrap (pas de logique d analyse, scoring, routage)
- [x] Poser la structure cible backend/playground conforme architecture (AC: 1, 4)
  - [x] Creer/valider `backend/src/main.py` comme entrypoint API
  - [x] Creer/valider `playground/src/app.py` comme entrypoint Playground
  - [x] Preparer l ossature feature-first de base (dossiers sans implementation metier avancee)
- [x] Installer la configuration minimale runtime (AC: 2)
  - [x] Ajouter `.env.example` (racine et sous-projets si necessaire)
  - [x] Ajouter `config/analysis_profiles.yaml`, `config/inference_engines.yaml`, `config/routing.yaml` avec placeholders valides
  - [x] S assurer qu aucun secret n est committe (variables uniquement, pas de valeurs sensibles)
- [x] Mettre en place CI baseline greenfield (AC: 3, 4)
  - [x] Ajouter `.github/workflows/ci.yml` avec lint backend, tests backend, verification de lancement playground
  - [x] Verifier que la pipeline passe sur un run minimal
  - [x] Garder la CI legere (pas de deploiement automatique MVP)
- [x] Verifications de non-regression et readiness stories suivantes (AC: 2, 3, 4)
  - [x] Confirmer que backend et playground demarrent localement
  - [x] Verifier que conventions `snake_case` + structure feature-first sont respectees
  - [x] Documenter limites MVP initiales (no-auth, stateless, pas de DB/cache)

## Dev Notes

- Cette story est la fondation technique uniquement; toute logique metier CoVeX (score, decision, routage, adaptateurs inference) est hors scope ici.
- L objectif est de livrer un bootstrap propre, testable, et coherent avec l architecture pour debloquer Stories 1.2+.

### Developer Context Section

- **Objectif business Epic 1:** rendre le flux d analyse completude operationnel local-first de bout en bout; Story 1.1 doit seulement preparer l infrastructure immediate.
- **Dependances inter-stories:** 1.2 (scoring/decision), 1.3 (routage), 1.4 (adaptateur inference), 1.5 (erreurs API), 1.6 (mecanisme retire) dependent d une base projet stable creee ici.
- **Bornes de scope strictes:** ne pas implementer d endpoint metier final au-dela de la verification de demarrage; ne pas introduire de design final UI complet; ne pas anticiper les details d epics 2-4.
- **Risque principal a eviter:** creer une "grosse fondation" qui retarde les stories suivantes (sur-ingenierie).

### Technical Requirements

- Initialisation obligatoire par `uvx fastapi-new covex`.
- Projet Python 3.14 cible, FastAPI + NiceGUI, configuration YAML.
- Mode stateless strict: aucune base interne, aucune persistance metier, aucun cache MVP.
- Contrat API futur en `snake_case`; conventions de nommage Python en `snake_case`, classes en `PascalCase`.
- Gestion secrets hors code/fichiers config versionnes.

### Architecture Compliance

- Respecter separation nette: `api` -> `service` -> `inference adapter` (pas de logique inference dans les handlers API).
- Respecter structure `backend/` et `playground/` distinctes avec boundaries explicites.
- Conserver no-auth applicatif MVP (usage reseau de confiance), sans ajouter middleware securite avancee dans cette story.
- Garder erreurs FastAPI par defaut pour MVP (pas d envelope custom globale).
- Preparer CI legere (lint/test/build-check) sans deploiement auto.

### Library/Framework Requirements

- **FastAPI:** baseline recommandee `0.128.x`; la release `0.128.8` est disponible (docs/internal changes), compatible avec l orientation architecture. [Source: webfetch GitHub Releases fastapi/fastapi, 2026-02-11]
- **Pydantic:** utiliser v2 uniquement; FastAPI `0.128.0+` supprime le support `pydantic.v1`, point critique avec Python 3.14. [Source: webfetch fastapi release 0.128.0]
- **NiceGUI:** baseline architecture `3.7.1`; `3.7.0` contient des correctifs securite importants (XSS/path traversal), a prendre en compte meme en MVP demo. [Source: webfetch GitHub Releases zauberzeug/nicegui]
- **Ollama (later stories):** versions recentes `0.15.x/0.16.0` montrent evolutions API/CLI; pour cette story, uniquement preparer integration future via config et adaptateur dedie. [Source: webfetch GitHub Releases ollama/ollama]
- **Python:** 3.14 stable (serie maintenance active), aligner dependances sur compatibilite 3.14 des le bootstrap.

### File Structure Requirements

- Arborescence cible minimale a respecter:
  - `covex/` (projet genere)
  - `backend/src/main.py`
  - `playground/src/app.py`
  - `config/analysis_profiles.yaml`, `config/inference_engines.yaml`, `config/routing.yaml`
  - `.env.example` (root + sous-projets si utile)
  - `.github/workflows/ci.yml`
- Pattern feature-first attendu pour les modules futurs:
  - `backend/src/analysis/`, `backend/src/analysis-profiles/`, `backend/src/inference/`, `backend/src/health/`, `backend/src/common/`
  - `playground/src/playground/`, `playground/src/api_client/`, `playground/src/ui/`
- Tests miroirs feature-first sous `backend/tests/`.

### Testing Requirements

- Verifier demarrage local backend et playground depuis leurs entrypoints.
- Ajouter tests/verification CI baseline:
  - lint backend
  - tests backend de smoke
  - verification import/run playground
- Verifier explicitement qu aucun texte utilisateur n est persiste (NFR stateless) dans ce bootstrap.
- Verifier que les fichiers de configuration YAML sont parseables et charges sans crash.

### Latest Tech Information

- FastAPI recentre ses versions recentes autour de Pydantic v2, avec corrections Python 3.14 deja integrees dans la branche `0.128.x`; eviter tout code legacy `pydantic.v1`.
- NiceGUI `3.7.0+` corrige des vulnerabilites de securite (XSS/path traversal) qui doivent etre considerees des la base de projet pour ne pas propager de patterns risques.
- Ollama evolue rapidement (`0.15.x` -> `0.16.0` pre-release): ne pas figer des appels ad hoc dans les handlers; isoler via adaptateur pour absorber changements futurs sans impact API.

### Project Structure Notes

- Le repository actuel contient deja des scripts et artefacts a la racine (`covex_test_runner.py`, `lm_models.*`, docs BMAD); eviter toute collision avec le nouveau squelette `covex/`.
- Si des fichiers homonymes existent deja, privilegier une strategie non destructive (creation dans sous-dossier dedie, puis integration explicite).
- Le flux de travail recommande est incremental: bootstrap minimal maintenant, implementation metier dans stories suivantes.

### References

- Story 1.1 et ACs: [Source: _bmad-output/planning-artifacts/epics.md#Story 1.1]
- Exigence starter/commande init: [Source: _bmad-output/planning-artifacts/epics.md#Additional Requirements]
- PRD scope MVP, NFRs et stack de reference: [Source: _bmad-output/planning-artifacts/prd.md#Product Scope], [Source: _bmad-output/planning-artifacts/prd.md#Non-Functional Requirements], [Source: _bmad-output/planning-artifacts/prd.md#Reference implementation (MVP)]
- Contraintes architecture, patterns et structure cible: [Source: _bmad-output/planning-artifacts/architecture.md#Selected Starter: fastapi/fastapi-new], [Source: _bmad-output/planning-artifacts/architecture.md#Implementation Patterns & Consistency Rules], [Source: _bmad-output/planning-artifacts/architecture.md#Complete Project Directory Structure]
- UX constraints MVP (responsive/a11y/ton): [Source: _bmad-output/planning-artifacts/ux-design-specification.md#Responsive Design & Accessibility]
- Releases techniques recentes:
  - [Source: https://github.com/fastapi/fastapi/releases]
  - [Source: https://github.com/zauberzeug/nicegui/releases]
  - [Source: https://github.com/ollama/ollama/releases]

### Project Context Reference

- Aucun fichier `project-context.md` n a ete detecte dans le workspace (`**/project-context.md`).
- Contexte projet derive des artefacts PRD/Architecture/UX et du fichier `_bmad-output/implementation-artifacts/sprint-status.yaml`.

### Story Completion Status

- Story context cree avec statut `ready-for-dev`.
- Note de completion: Ultimate context engine analysis completed - comprehensive developer guide created.

## Dev Agent Record

### Agent Model Used

openai/gpt-5.3-codex

### Debug Log References

- Analyse exhaustive des artefacts: `epics.md`, `prd.md`, `architecture.md`, `ux-design-specification.md`, `sprint-status.yaml`.
- Recherche technologique: releases FastAPI/NiceGUI/Ollama.

### Implementation Plan

- Initialiser le starter officiel dans `covex/` sans ecraser les artefacts existants.
- Poser une ossature backend/playground minimale avec entrypoints Python et dossiers feature-first vides.
- Ajouter configuration runtime parseable (`.env.example` + YAML placeholders) sans secrets.
- Ajouter CI greenfield minimale (lint/tests backend + verification import playground) et valider localement.
- Completer des tests smoke backend et de validation YAML pour couvrir ACs et edge cases bootstrap.

### Completion Notes List

- Story creee automatiquement depuis la premiere entree `backlog` de `sprint-status.yaml`.
- Epic `epic-1` doit etre marque `in-progress` avec cette creation.
- Bootstrap initialise via `uvx fastapi-new covex`; CLI FastAPI verifiee (`uv run fastapi --help`) dans le projet genere.
- Entree API minimale ajoutee (`backend/src/main.py`) et entree Playground NiceGUI ajoutee (`playground/src/app.py`).
- Ossature feature-first preparee: backend (`analysis`, `prompts`, `inference`, `health`, `common`) et playground (`playground`, `api_client`, `ui`).
- Configuration runtime ajoutee: `.env.example` (racine + backend + playground), `config/analysis_profiles.yaml`, `config/inference_engines.yaml`, `config/routing.yaml`.
- Tests ajoutes et executes: smoke API + verification stateless + validation parse YAML (`3 passed`).
- Qualite validee: lint backend/playground `ruff check` OK; verification import playground OK.
- Limites MVP explicites conservees: no-auth applicatif, stateless strict, aucune DB/cache, aucune logique metier d analyse/scoring/routage.

### File List

- _bmad-output/implementation-artifacts/1-1-set-up-initial-project-from-starter-template.md
- _bmad-output/implementation-artifacts/sprint-status.yaml
- backend/pyproject.toml
- backend/src/analysis/__init__.py
- backend/src/common/__init__.py
- backend/src/health/__init__.py
- backend/src/inference/__init__.py
- backend/src/main.py
- backend/src/analysis-profiles/__init__.py
- backend/tests/test_backend_smoke.py
- backend/tests/test_config_yaml.py
- config/inference_engines.yaml
- config/analysis_profiles.yaml
- config/routing.yaml
- playground/.env.example
- playground/pyproject.toml
- playground/src/__init__.py
- playground/src/api_client/__init__.py
- playground/src/app.py
- playground/src/playground/__init__.py
- playground/src/ui/__init__.py

## Change Log

- 2026-02-12: Bootstrap initial CoVeX livre avec starter `fastapi-new`, ossature backend/playground feature-first, configuration runtime minimale, CI baseline et tests smoke de readiness.
