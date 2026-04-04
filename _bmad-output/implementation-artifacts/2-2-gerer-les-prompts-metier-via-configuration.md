# Story 2.2: Gerer les profils d'analyse metier via configuration

> Note 2026-03-14: artefact BMAD historique. Certaines references internes
> (tests, modules, `criteria`, hot reload, pages playground) peuvent ne plus
> correspondre exactement au depot courant. Pour l'etat actuel, se fier a
> `README.md`, `docs/ARCHITECTURE.md` et `docs/ANALYSIS_PROFILES_METIER.md`.


Status: review

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a expert metier,
I want creer et maintenir des profils d'analyse metier dans des fichiers de configuration,
so that CoVeX evalue la completude selon mes criteres de domaine.

## Acceptance Criteria

1. **Given** un fichier `analysis_profiles.yaml` conforme **When** le service charge la configuration **Then** chaque prompt est disponible avec son `name`, sa `description` et ses criteres **And** les prompts sont consultables par les composants qui en dependent.
2. **Given** un prompt inclut des criteres de completude (critiques/importants/souhaitables ou equivalent) **When** il est valide au chargement **Then** les regles sont structurees et exploitables par le moteur d analyse **And** les poids ou attributs incoherents sont refuses avec message explicite.
3. **Given** un prompt reference un modele specifique **When** ce modele existe dans la configuration modeles **Then** l association prompt vers modele est acceptee **And** elle est resolue de facon deterministic lors de l analyse.
4. **Given** un prompt reference un modele inexistant ou un schema prompt invalide **When** la validation est executee **Then** la configuration est rejetee proprement **And** l erreur indique le prompt en cause pour correction rapide.
5. **Given** une integration demande la liste des profils d'analyse disponibles **When** `GET /analysis-profiles` (nice-to-have) ou la couche interne de consultation est appelee **Then** les prompts actifs sont retournes de maniere stable **And** aucune information sensible interne n est exposee.

## Tasks / Subtasks

- [x] Introduire un module central de chargement/validation des prompts (AC: 1, 2, 4)
  - [x] Definir schema Pydantic v2 strict pour `analysis_profiles.yaml` (name, description, criteria, model association)
  - [x] Charger YAML en mode sur (`yaml.safe_load`) puis valider integralement avant exposition runtime
  - [x] Rejeter explicitement champs manquants, types invalides, IDs dupliques, poids incoherents
- [x] Connecter la resolution prompt -> modele avec la config modeles existante (AC: 3)
  - [x] Reutiliser `backend/src/inference/models_config.py` (Story 2.1) comme source de verite pour verifier les references modeles
  - [x] Garantir une resolution deterministic (meme prompt => meme modele effectif dans le meme etat de config)
  - [x] Propager l information au flux d analyse sans casser le contrat `/analyze`
- [x] Stabiliser l exposition des prompts pour usage API/UI (AC: 1, 5)
  - [x] Ajouter un service/repository prompts unique au lieu de duplication dans handlers
  - [x] Normaliser la projection des prompts retournes (metadonnees autorisees uniquement)
  - [x] Preparer la compatibilite `GET /analysis-profiles` sans coupler la logique metier aux details HTTP
- [x] Ajouter les guardrails de non-regression et de securite (AC: 2, 3, 4, 5)
  - [x] Etendre tests unitaires prompts/inference pour chemins valides/invalides
  - [x] Verifier absence d exposition de donnees sensibles dans payloads et messages d erreur
  - [x] Verifier qu aucune configuration partielle n est appliquee apres echec validation

## Dev Notes

- Story 2.2 s appuie directement sur Story 2.1: la validation de config modeles est deja centralisee, il faut maintenant appliquer la meme rigueur aux prompts et au mapping prompt->modele.
- Eviter absolument la duplication de parseurs YAML ou de logique de resolution dans plusieurs couches.

### Developer Context Section

- **Objectif Epic 2:** rendre la configuration metier (prompts + modeles) modifiable sans changement de code, sans redemarrage force, avec comportement deterministic.
- **Valeur business immediate:** un expert metier peut ajuster les criteres de completude en fichier et obtenir des analyses coherentes sans intervention dev.
- **Contexte story precedent (2.1):**
  - `backend/src/inference/models_config.py` centralise parsing/validation/coherence des modeles.
  - `backend/src/inference/client.py`, `adapter.py`, `timeouts.py` utilisent deja cette source de verite.
  - `config/inference_engines.yaml` et tests inference associes sont en place.
- **Impact story courante:** introduire une source de verite equivalente pour `analysis_profiles.yaml` et brancher proprement la resolution vers les modeles valides.

### Technical Requirements

- Validation stricte des prompts au chargement (Pydantic v2), sans acceptance permissive.
- Le schema prompt doit couvrir au minimum: identifiant stable, description metier, criteres structures, reference modele optionnelle.
- Regles de coherence obligatoires:
  - references modeles dans prompts resolvables via config modeles validee,
  - structure des criteres exploitable par le moteur de scoring (pas de formats ambigus),
  - contraintes de poids/attributs enforcees.
- En cas d erreur:
  - rejet complet de la configuration prompts candidate,
  - message explicite et actionnable,
  - aucun etat partiellement mis a jour.
- Prioriser reutilisation de l existant (Story 2.1) plutot que nouvelle logique parallele.

### Architecture Compliance

- Respecter strictement `snake_case` pour Python, JSON et clefs de config.
- Maintenir les boundaries feature-first:
  - API handlers sous `backend/src/*/api.py`,
  - logique metier dans `service.py`,
  - lecture/validation config dans modules dedies (`repository.py`/`*_config.py`).
- Garder l adaptateur inference hors handlers API (pas de logique provider dans routes).
- Conserver architecture stateless: aucune persistance de texte utilisateur, aucun cache metier MVP.
- Garder format erreurs FastAPI MVP cote API; details techniques uniquement dans logs.

### Library/Framework Requirements

- **FastAPI:** rester compatible ligne `0.128.x`; pas d upgrade impose dans cette story.
- **Pydantic:** v2 uniquement (coherence Python 3.14 et architecture en place).
- **PyYAML:** utiliser `yaml.safe_load` pour tout chargement de config.
- **HTTPX/adapter inference:** ne pas modifier contrats reseau; cette story porte sur config prompts et resolution.
- **NiceGUI/Quasar:** aucune modification UI requise ici; livrer une couche backend exploitable par l UI existante.

### File Structure Requirements

- Fichiers cibles prioritaires:
  - `backend/src/analysis-profiles/repository.py`
  - `backend/src/analysis-profiles/service.py`
  - `backend/src/analysis-profiles/schemas.py`
  - `config/analysis_profiles.yaml`
- Fichiers possiblement a etendre selon implementation:
  - `backend/src/analysis/service.py` (integration de la resolution)
  - `backend/src/inference/models_config.py` (interfaces de verification partagees)
  - `backend/src/analysis-profiles/api.py` (si exposition `GET /analysis-profiles` activee)
- Tests a creer/etendre:
  - `backend/tests/analysis-profiles/test_service.py`
  - `backend/tests/analysis-profiles/test_api.py`
  - `backend/tests/analysis/test_service.py`
  - `backend/tests/test_config_yaml.py`

### Testing Requirements

- Verifier chargement de prompts valides avec exposition `name`, `description`, criteres.
- Verifier rejet des prompts invalides (schema, types, poids, references modeles inconnues).
- Verifier coherence prompt->modele sur le flux d analyse (`model_used` conforme a la resolution effective).
- Verifier stabilite de la liste de prompts retournee (ordre/payloads predictibles selon conventions projet).
- Verifier absence d exposition de secrets ou details sensibles dans erreurs et endpoints.
- Ajouter tests de non-regression pour prevenir duplication de logique config entre prompts/inference.

### Previous Story Intelligence

- Story 2.1 a etabli une base solide de validation stricte de config; reutiliser ses patterns (source de verite unique, erreurs explicites, tests defensifs) est indispensable.
- Les fichiers `inference/client.py`, `inference/adapter.py`, `inference/timeouts.py` ont deja ete refactorises vers une resolution deterministic: garder cette logique alignée pour prompts.
- Le scope 2.1 a explicitement reporte le watcher/reload complet a Story 2.4: ne pas glisser ce scope ici.

### Git Intelligence Summary

- Les 5 derniers commits montrent une progression incrementale avec commits stories atomiques (`1.3` a `2.1`) et mises a jour paralleles story file + `sprint-status.yaml`.
- Patterns de fichiers recurrents et pertinents pour 2.2:
  - backend: `analysis/*`, `inference/*`, `prompts/*`,
  - tests miroirs par feature sous `backend/tests/*`,
  - config sous `config/*.yaml`.
- Convention de travail observee: introduire module dedie puis brancher progressivement les consommateurs et couvrir par tests de non-regression.

### Latest Tech Information

- FastAPI: la branche `0.128.x` reste active; garder compatibilite API interne sur cette ligne pour limiter regressions. [Source: https://fastapi.tiangolo.com/release-notes/]
- Pydantic: serie `2.12.x` en cours; Python 3.14 impose de rester en v2 pour eviter incompatibilites v1. [Source: https://docs.pydantic.dev/latest/changelog/]
- NiceGUI: version `3.7.1` publiee (2026-02-05), incluant correctifs securite majeurs en `3.7.0`; utile pour prochaines stories UI mais hors scope direct 2.2. [Source: https://pypi.org/project/nicegui/]
- HTTPX: `0.28.1` est la derniere release stable connue; attention aux deprecations SSL introduites en `0.28.0` si evolution client future. [Source: https://github.com/encode/httpx/releases]

### Project Structure Notes

- Aucun `project-context.md` detecte via le pattern `**/project-context.md`.
- Contexte utilise pour cette story: `epics.md`, `architecture.md`, `prd.md`, `ux-design-specification.md`, `sprint-status.yaml`, story 2.1 et historique git recent.

### References

- Story 2.2 et AC: [Source: _bmad-output/planning-artifacts/epics.md#Story 2.2]
- FR/NFR de configuration prompts/modeles: [Source: _bmad-output/planning-artifacts/prd.md#Configuration des Prompts Metier], [Source: _bmad-output/planning-artifacts/prd.md#Non-Functional Requirements]
- Guardrails architecture/boundaries: [Source: _bmad-output/planning-artifacts/architecture.md#Implementation Patterns & Consistency Rules], [Source: _bmad-output/planning-artifacts/architecture.md#Project Structure & Boundaries]
- Contraintes UX/erreurs/transparence: [Source: _bmad-output/planning-artifacts/ux-design-specification.md#Feedback Patterns]
- Intelligence story precedente: [Source: _bmad-output/implementation-artifacts/2-1-charger-et-valider-la-configuration-des-modeles.md]
- Historique commits: [Source: git log local (commits 23661d5, 21e106a, 7e1313e, 9dd6b34, ce2fbda)]

### Story Completion Status

- Story context cree avec statut `ready-for-dev`.
- Note de completion: Ultimate context engine analysis completed - comprehensive developer guide created.

## Dev Agent Record

### Agent Model Used

openai/gpt-5.3-codex

### Debug Log References

- Artefacts analyses: `epics.md`, `prd.md`, `architecture.md`, `ux-design-specification.md`, `sprint-status.yaml`.
- Story precedente analysee: `2-1-charger-et-valider-la-configuration-des-modeles.md`.
- Historique git recent analyse: 5 derniers commits avec fichiers modifies.
- Veille technique: FastAPI release notes, changelog Pydantic, release PyPI NiceGUI, releases HTTPX.
- Implementation: `uv run pytest tests/analysis-profiles/test_prompts_service.py tests/analysis-profiles/test_prompts_api.py tests/analysis/test_routing.py tests/analysis/test_service.py tests/test_config_yaml.py`.
- Validation complete: `uv run pytest` (75 tests), `uv run ruff check`.

### Completion Notes List

- Story 2.2 contextualisee avec exigences implementation-ready, guardrails architecture et anti-regression.
- Alignement explicite avec patterns et learnings de Story 2.1 pour eviter duplication de logique config.
- Informations techniques recentes ajoutees pour limiter decisions basees sur versions obsoletees.
- Module prompts central implemente avec schema Pydantic v2 strict (`PromptCriterion`, `PromptDefinition`, `PromptsConfig`) + validation coherence modeles via `models_config`.
- Chargement YAML securise avec detection des cles dupliquees, rejet des schemas invalides, et absence d etat partiel en cas d echec.
- Resolution prompt->modele branchee dans le routage et le flux d analyse (`provider_key` propage vers l adaptateur inference) sans changer le contrat `POST /analyze`.
- Exposition stabilisee des prompts via service unique + endpoint `GET /analysis-profiles` limite aux metadonnees autorisees.
- Couverture test etendue (prompts service/api, routing, analyse, config) avec suite complete verte (75/75) et lint vert.
- Definition of Done (checklist dev-story): PASS, toutes les gates qualite/documentation/statut sont satisfaites.

### File List

- _bmad-output/implementation-artifacts/2-2-gerer-les-prompts-metier-via-configuration.md
- backend/src/analysis/routing.py
- backend/src/analysis/service.py
- backend/src/inference/adapter.py
- backend/src/main.py
- backend/src/analysis-profiles/__init__.py
- backend/src/analysis-profiles/api.py
- backend/src/analysis-profiles/repository.py
- backend/src/analysis-profiles/schemas.py
- backend/src/analysis-profiles/service.py
- backend/tests/analysis/test_routing.py
- backend/tests/analysis/test_service.py
- backend/tests/analysis-profiles/test_prompts_api.py
- backend/tests/analysis-profiles/test_prompts_service.py
- backend/tests/test_config_yaml.py
- config/analysis_profiles.yaml
- config/routing.yaml
- _bmad-output/implementation-artifacts/sprint-status.yaml

## Change Log

- 2026-02-12: Story 2.2 creee avec contexte complet, intelligence git + story precedente, et statut `ready-for-dev`.
- 2026-02-12: Implementation completee - module prompts central, validation stricte, resolution prompt->modele, endpoint `GET /analysis-profiles`, tests et lint passes; statut passe a `review`.

## Senior Developer Review (AI)

### Review Summary
- **Reviewer:** JBU
- **Date:** 2026-02-23
- **Outcome:** Approved

### Findings

#### High Severity
- None

#### Medium Severity
- **Dependencies sur story 2-1:** Le module prompts依赖于 `inference/models_config.py` pour la validation des références modèles. Si 2.1 change d'interface, cela peut impacter 2-2.

#### Low Severity
- **潜在重复:** La logique de validation des poids de critères (total <= 1.0) est implémentée dans `prompts/schemas.py` mais pourrait être réutilisée ailleurs.

### Verification
- ✅ Tests unitaires: 107 passent
- ✅ Lint (ruff): All checks passed
- ✅ AC1-AC5 fully implemented
- ✅ File List: tous les fichiers existants
- ✅ Validation cohérence prompt->modele fonctionne

### Notes
- Schema Pydantic v2 strict bien implémenté
- Endpoint `GET /analysis-profiles` expose uniquement les métadonnées autorisées
- Pas d'exposition de secrets dans les erreurs
- Configuration partiellement invalide est bien rejettée atomiquement
