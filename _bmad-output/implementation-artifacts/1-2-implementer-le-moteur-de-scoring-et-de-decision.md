# Story 1.2: Implementer le moteur de scoring et de decision

> Note 2026-03-14: artefact BMAD historique. Certaines references internes
> (tests, modules, `criteria`, hot reload, pages playground) peuvent ne plus
> correspondre exactement au depot courant. Pour l'etat actuel, se fier a
> `README.md`, `docs/ARCHITECTURE.md` et `docs/ANALYSIS_PROFILES_METIER.md`.


Status: review

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a product owner,
I want que CoVeX calcule un score de completude et une decision a partir d un texte et d un prompt,
so that les utilisateurs recoivent un verdict actionnable et coherent.

## Acceptance Criteria

1. **Given** un texte valide et un prompt metier resolu **When** l analyse est executee **Then** le systeme calcule un `score` entier entre 0 et 100 **And** il derive `decision` selon les seuils MVP (`KO <= 30`, `PARTIEL 31-70`, `OK > 70`).
2. **Given** une analyse terminee **When** la reponse est construite **Then** `justification` explique la raison du score en langage clair **And** pour un score < 70, elle mentionne explicitement les elements manquants.
3. **Given** plusieurs analyses identiques sur un meme texte/prompt **When** elles sont executees dans les memes conditions **Then** la variation de score reste limitee et compatible avec les objectifs de reproductibilite **And** la decision reste coherente avec le score retourne.
4. **Given** un texte incomplet vs partiel vs complet pour un meme prompt **When** les trois analyses sont executees **Then** les scores respectent une progression monotone (incomplet < partiel < complet) **And** les decisions suivent les seuils attendus.
5. **Given** des erreurs de format de sortie modele **When** le service traite le resultat d inference **Then** il applique une validation defensive avant reponse API **And** il retourne une erreur maitrisee si le resultat ne peut pas etre interprete proprement.

## Tasks / Subtasks

- [x] Ajouter la logique de scoring metier 0-100 (AC: 1, 4)
  - [x] Implementer le calcul de score dans `backend/src/analysis/scoring.py`
  - [x] Garantir la borne stricte `0 <= score <= 100`
  - [x] Couvrir la monotonicite incomplet/partiel/complet par tests unitaires
- [x] Ajouter la logique de decision KO/PARTIEL/OK (AC: 1, 3, 4)
  - [x] Implementer les seuils MVP dans `backend/src/analysis/decision.py`
  - [x] Garantir la coherence deterministe `score -> decision`
  - [x] Ajouter tests de frontieres (30/31/70/71)
- [x] Produire une justification exploitable et stable (AC: 2, 3)
  - [x] Standardiser la generation de `justification` depuis le resultat d analyse
  - [x] Garantir mention explicite des elements manquants si score < 70
  - [x] Ajouter tests de non-regression sur la structure de justification
- [x] Integrer au service d analyse sans casser le contrat API (AC: 1, 2, 5)
  - [x] Faire orchestrer scoring+decision+justification par `backend/src/analysis/service.py`
  - [x] Garder `backend/src/analysis/api.py` limite a validation I/O et mapping erreurs
  - [x] Preserver schema de reponse (`score`, `decision`, `justification`)
- [x] Ajouter validation defensive des sorties inference (AC: 5)
  - [x] Rejeter proprement les sorties non interpretables (format invalide, champs manquants)
  - [x] Retourner erreur maitrisee conforme contrat (500 ou 503 selon cause)
  - [x] Logger contexte technique utile sans fuite de texte utilisateur brut
- [x] Completer la couverture de tests et verification locale (AC: 1-5)
  - [x] Tests unitaires `scoring` et `decision`
  - [x] Tests service `analysis` (cas nominal, bords, erreurs format)
  - [x] Tests API `POST /analyze` pour coherence contrat + erreurs maitrisees

## Dev Notes

- Cette story introduit le coeur metier de CoVeX: calcul du score, derivation de decision, justification actionnable.
- Le scope reste concentre sur le moteur de scoring/decision; le routage auto (1.3) et l adaptateur inference robuste (1.4) restent des stories distinctes.

### Developer Context Section

- **Objectif Epic 1:** livrer un flux de verdict completude exploitable de bout en bout en local-first, en commencant par un moteur de scoring fiable et testable.
- **Valeur business immediate:** fournir un verdict actionnable coherent pour reduire les allers-retours de clarification.
- **Dependances:** s appuyer sur la fondation 1.1 (structure backend/playground, config, CI, tests smoke) sans la contourner.
- **Contraintes de scope:** pas de persistance, pas d auth applicative, pas de refonte UX; uniquement logique scoring/decision/justification + integration API.

### Technical Requirements

- Le resultat principal doit contenir `score` (entier 0..100), `decision` (`KO|PARTIEL|OK`), `justification` (texte clair).
- Les seuils MVP sont non negociables: `KO <= 30`, `PARTIEL 31-70`, `OK > 70`.
- La logique doit rester deterministic pour un meme input dans les memes conditions (variation limitee, decision stable).
- Si sortie inference non interpretable, appliquer validation defensive et erreur maitrisee.
- Respect strict `snake_case` partout (payloads JSON, params, code Python).

### Architecture Compliance

- Conserver la separation `api.py -> service.py -> scoring.py/decision.py`.
- Ne pas injecter de logique inference brute dans les handlers API.
- Garder reponses succes typees directes, et erreurs FastAPI par defaut en MVP.
- Garder architecture stateless stricte: aucune DB interne, aucun cache MVP, aucune persistence des textes analyses.
- Integrer les tests sous structure miroir feature-first (`backend/tests/analysis/`).

### Library/Framework Requirements

- **FastAPI:** conserver compatibilite de la branche `0.128.x`; les versions recentes renforcent la trajectoire Pydantic v2 uniquement. [Source: https://fastapi.tiangolo.com/release-notes/]
- **Pydantic:** utiliser v2 (`2.12.5` reference), ne pas utiliser les patterns v1 legacy sur Python 3.14. [Source: https://pypi.org/project/pydantic/, Source: https://github.com/pydantic/pydantic/releases]
- **Uvicorn:** base runtime `0.40.0` compatible Python 3.14; eviter des hypotheses Python<3.10. [Source: https://pypi.org/project/uvicorn/, Source: https://uvicorn.dev/release-notes/]
- **HTTPX:** reference `0.28.1`; attention aux deprecations SSL/proxies introduites en `0.28.0`. [Source: https://github.com/encode/httpx/releases, Source: https://pypi.org/project/httpx/]

### File Structure Requirements

- Fichiers cibles de cette story (backend):
  - `backend/src/analysis/scoring.py`
  - `backend/src/analysis/decision.py`
  - `backend/src/analysis/service.py`
  - `backend/src/analysis/api.py`
  - `backend/src/analysis/schemas.py`
- Tests cibles:
  - `backend/tests/analysis/test_scoring.py`
  - `backend/tests/analysis/test_service.py`
  - `backend/tests/analysis/test_api.py`
- Respecter l arborescence definie par architecture; ne pas creer de chemins alternatifs hors feature.

### Testing Requirements

- Couvrir les frontieres de seuil (`30/31/70/71`) et les bornes score (`0`, `100`, hors bornes rejects/normalisation).
- Verifier monotonicite sur triplets de cas (incomplet < partiel < complet) pour un prompt donne.
- Verifier reproductibilite: executions identiques gardent decision stable et variation score acceptable.
- Verifier validation defensive des reponses inference (formats invalides -> erreur maitrisee).
- Verifier contrat API `POST /analyze`: schema et codes d erreur explicites attendus.

### Previous Story Intelligence

- Story 1.1 a deja pose la base technique: structure feature-first backend/playground, CI legere, fichiers de config, tests smoke.
- Patterns etablis a conserver:
  - no-auth MVP,
  - stateless strict,
  - boundaries nettes entre couches,
  - conventions `snake_case`.
- Eviter de recreer un nouveau bootstrap: reutiliser les modules places en 1.1 et etendre uniquement la feature `analysis`.
- Les tests et lint passent deja en baseline; ne pas degrader ce point (ajouter tests story-specifiques plutot que contourner).

### Git Intelligence Summary

- Commits recents confirment le style incremental:
  - `1a2d3d1 set up story 1.1 bootstrap foundation`
  - `3565748 create-story`
  - `f56b710 sprint-planning`
- Fichiers modifies en 1.1 montrent exactement ou etendre le travail (`backend/src/analysis/*`, `backend/tests/*`, config YAML, CI).
- Convention de commit observee: message court en imperative, focalise sur intention de livraison.

### Latest Tech Information

- FastAPI continue de stabiliser la branche `0.128.x`; pas de changement bloquant majeur pour ce story scope, mais rester sur Pydantic v2 natif.
- Pydantic v2.12.x inclut ajustements Python 3.14; eviter tout melange de patterns v1 dans nouveaux modeles/schemas.
- Uvicorn `0.40.0` supporte les versions Python cibles modernes et retire le support Python 3.9.
- HTTPX `0.28.x` a retire certains arguments depreciees (`proxies`, `app`) et ajuste SSL; garder l usage standard et explicite.

### Project Structure Notes

- Le repo contient deja les artefacts BMAD et le story 1.1; creer les nouveaux elements dans `backend/src/analysis/` et `backend/tests/analysis/` uniquement.
- Aucun `project-context.md` detecte; les contraintes proviennent de `epics.md`, `prd.md`, `architecture.md`, `ux-design-specification.md`, et de l historique story 1.1.

### References

- Story 1.2 details et AC: [Source: _bmad-output/planning-artifacts/epics.md#Story 1.2]
- Exigences FR/NFR et KPI: [Source: _bmad-output/planning-artifacts/prd.md#Functional Requirements], [Source: _bmad-output/planning-artifacts/prd.md#Non-Functional Requirements], [Source: _bmad-output/planning-artifacts/prd.md#Validation & KPIs]
- Contraintes architecture et structure: [Source: _bmad-output/planning-artifacts/architecture.md#Implementation Patterns & Consistency Rules], [Source: _bmad-output/planning-artifacts/architecture.md#Complete Project Directory Structure]
- Contraintes UX de restitution (hierarchie resultat): [Source: _bmad-output/planning-artifacts/ux-design-specification.md#Experience Principles]
- Story precedente (learnings): [Source: _bmad-output/implementation-artifacts/1-1-set-up-initial-project-from-starter-template.md]

### Project Context Reference

- Aucun fichier `project-context.md` trouve via pattern `**/project-context.md`.
- Contexte derive des artefacts de planification + `sprint-status.yaml`.

### Story Completion Status

- Story context cree avec statut `ready-for-dev`.
- Note de completion: Ultimate context engine analysis completed - comprehensive developer guide created.

## Dev Agent Record

### Agent Model Used

openai/gpt-5.3-codex

### Debug Log References

- Analyse artefacts: `epics.md`, `prd.md`, `architecture.md`, `ux-design-specification.md`, `sprint-status.yaml`.
- Analyse story precedente: `1-1-set-up-initial-project-from-starter-template.md`.
- Analyse git recente: 5 derniers commits + fichiers modifies.
- Veille technique: FastAPI/Pydantic/NiceGUI/Uvicorn/HTTPX releases.
- Execution TDD: `uv run pytest` (echec initial sur modules analysis absents), puis implementation minimale et validation complete.
- Validation qualite: `uv run pytest` (25 passes) et `uv run ruff check` (OK).

### Completion Notes List

- Story selection automatique depuis premier statut `backlog` dans `sprint-status.yaml`: `1-2-implementer-le-moteur-de-scoring-et-de-decision`.
- Story file genere avec guide dev complet pour implementation sans ambiguite.
- Statut story force a `ready-for-dev` dans ce document et dans `sprint-status.yaml`.
- Plan technique applique: separation `api -> service -> scoring/decision`, schema Pydantic v2, et mapping explicite des erreurs `500/503`.
- Moteur de scoring deterministic ajoute avec bornage strict 0..100, seuils MVP KO/PARTIEL/OK, et justification stable orientee elements manquants sous 70.
- Validation defensive de sortie inference ajoutee (structure et types requis), avec logs techniques sans exposition du texte utilisateur brut.
- Couverture de tests completee avec suites unitaires, service et API autour de `POST /analyze` (cas nominal, frontieres, erreurs format et indisponibilite inference).

### File List

- backend/src/main.py
- backend/src/analysis/api.py
- backend/src/analysis/decision.py
- backend/src/analysis/scoring.py
- backend/src/analysis/schemas.py
- backend/src/analysis/service.py
- backend/tests/analysis/test_api.py
- backend/tests/analysis/test_scoring.py
- backend/tests/analysis/test_service.py
- _bmad-output/implementation-artifacts/1-2-implementer-le-moteur-de-scoring-et-de-decision.md
- _bmad-output/implementation-artifacts/sprint-status.yaml

## Change Log

- 2026-02-12: Implementation story 1.2 completee (scoring/decision/justification, validation defensive inference, endpoint `POST /analyze`, tests unitaires+service+API, statut passe a `review`).
