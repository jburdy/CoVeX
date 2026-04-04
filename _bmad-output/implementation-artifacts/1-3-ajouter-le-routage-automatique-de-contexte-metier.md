# Story 1.3: Ajouter le routage automatique de contexte metier

> Note 2026-03-14: artefact BMAD historique. Certaines references internes
> (tests, modules, `criteria`, hot reload, pages playground) peuvent ne plus
> correspondre exactement au depot courant. Pour l'etat actuel, se fier a
> `README.md`, `docs/ARCHITECTURE.md` et `docs/ANALYSIS_PROFILES_METIER.md`.


Status: review

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As an utilisateur sans expertise technique,
I want que CoVeX detecte automatiquement le meilleur prompt metier quand je ne precise pas de contexte,
so that j obtienne une analyse pertinente sans configuration manuelle.

## Acceptance Criteria

1. **Given** une requete `POST /analyze` sans `profile_id` **When** le routage automatique est execute **Then** le systeme selectionne un prompt metier parmi ceux disponibles **And** il renseigne `profile_used` dans la reponse.
2. **Given** un routage automatique termine **When** la reponse est retournee **Then** elle inclut `routing_confidence` dans l intervalle `0..1` **And** la valeur est exploitable par les consommateurs API/UI.
3. **Given** un score de confiance de routage inferieur au seuil MVP (`0.7`) **When** le prompt final est choisi **Then** le systeme bascule sur le prompt par defaut configure **And** `profile_used` reflete ce mecanisme retire de routage.
4. **Given** un `profile_id` explicite est fourni par le client **When** l analyse est executee **Then** aucun routage automatique n est impose **And** le prompt explicitement demande est prioritaire.
5. **Given** aucun prompt metier valide n est disponible en configuration **When** une requete sans `profile_id` arrive **Then** le systeme retourne une erreur maitrisee et explicite **And** aucun comportement implicite non trace n est applique.

## Tasks / Subtasks

- [x] Introduire la resolution de prompt avec mode explicite vs automatique (AC: 1, 4)
  - [x] Ajouter un service de routage dans `backend/src/analysis/` (module dedie ou extension de `service.py`) qui retourne `profile_used` et `routing_confidence`
  - [x] Prioriser `profile_id` explicite si fourni et valide; court-circuiter tout routage automatique
  - [x] Charger la liste des profils d'analyse actifs depuis la configuration (source unique)
- [x] Ajouter la logique de mecanisme retire de routage sur seuil de confiance (AC: 2, 3)
  - [x] Appliquer un seuil configurable (MVP: `0.7`) avec mecanisme retire vers `default_route`/prompt par defaut
  - [x] Garantir `routing_confidence` borne entre `0.0` et `1.0`
  - [x] Reporter `profile_used` effectif (prompt route ou mecanisme retire)
- [x] Etendre le contrat API `POST /analyze` sans casser l existant (AC: 1, 2, 4)
  - [x] Faire evoluer `AnalyzeRequest` pour accepter `profile_id` optionnel (compat migration: gerer `prompt` legacy si necessaire)
  - [x] Etendre `AnalyzeResponse` avec `profile_used` et `routing_confidence` optionnels
  - [x] Garder les champs MVP deja relies (`score`, `decision`, `justification`) inchanges
- [x] Gerer les cas d erreur de routage et de configuration (AC: 5)
  - [x] Retourner une erreur maitrisee si aucun prompt resolvable (404 ou 500 selon cause validee dans le service)
  - [x] Journaliser le contexte technique utile sans fuite du texte brut utilisateur
  - [x] Interdire les comportements implicites non traces
- [x] Couvrir le flux par tests unitaires/service/API (AC: 1-5)
  - [x] Tests service: selection auto, seuil, mecanisme retire, priorite explicite, cas sans prompt valide
  - [x] Tests API: schema reponse avec `profile_used` et `routing_confidence`, codes d erreur attendus
  - [x] Tests de non-regression pour garantir coherence score/decision/justification apres integration routage

## Dev Notes

- Cette story ajoute l intelligence de selection de contexte metier au-dessus du moteur de scoring deja livre en 1.2.
- Le scope reste backend/API: aucune refonte UI ici, mais les metadonnees doivent etre directement consommables par le Playground.

### Developer Context Section

- **Objectif Epic 1:** completer le flux `POST /analyze` en mode "auto-context" pour que l utilisateur puisse analyser sans connaitre le `profile_id`.
- **Valeur business immediate:** reduction de friction utilisateur et meilleure pertinence du verdict sans configuration manuelle.
- **Dependances:** reutiliser la logique 1.2 (`analysis/service.py`, `analysis/api.py`, `analysis/schemas.py`) et les configs `config/analysis_profiles.yaml` + `config/routing.yaml`.
- **Contraintes de scope:** pas de persistance, pas d auth, pas de changement d architecture globale; uniquement routage + enrichissement reponse + erreurs maitrisees.

### Technical Requirements

- Supporter deux modes stricts:
  - `profile_id` fourni -> mode explicite prioritaire (pas de routage automatique).
  - `profile_id` absent -> mode auto avec calcul `routing_confidence`.
- Toujours produire un `profile_used` effectif apres resolution (route ou mecanisme retire).
- Garantir `routing_confidence` dans `[0.0, 1.0]`; appliquer mecanisme retire si `< 0.7`.
- Garder la sortie principale compatible (`score`, `decision`, `justification`) et ajouter les metadonnees sans rupture.
- Rester deterministic pour un meme input + meme configuration.

### Architecture Compliance

- Preserver la separation `api.py -> service.py -> composants metier`; ne pas noyer la logique de routage dans le handler FastAPI.
- Respecter l architecture stateless: aucune DB/cache interne et aucune persistance durable des textes.
- Respecter le pattern feature-first dans `backend/src/analysis/` et `backend/tests/analysis/`.
- Conserver les formats API MVP: succes type via Pydantic, erreurs FastAPI maitrisees.
- Rester en `snake_case` partout (payloads, champs JSON, variables, modules).

### Library/Framework Requirements

- **FastAPI:** architecture reference `0.128.8`; latest stable observee `0.129.0` (PyPI, 2026-02-12). Garder compatibilite `0.128.x`/`0.129.x` sans utiliser d API experimentales.
- **Pydantic:** garder v2 (`2.12.5`) pour les schemas request/response; ne pas reintroduire des patterns v1.
- **Uvicorn:** reference `0.40.0` (support Python 3.14, Python <3.10 retire) a respecter pour l execution locale.
- **HTTPX:** reference `0.28.1`; attention aux changements 0.28.0 (`proxies`/`app` retires) si un client HTTP est introduit pour le routage futur.
- **NiceGUI (impact consommateur UI):** baseline `3.7.1`; conserver les champs de reponse attendus par le panneau details, avec vigilance sur patchs securite 3.7.0+.

### File Structure Requirements

- Fichiers backend cibles (minimaux):
  - `backend/src/analysis/schemas.py`
  - `backend/src/analysis/api.py`
  - `backend/src/analysis/service.py`
- Fichiers backend potentiels (si extraction de responsabilite):
  - `backend/src/analysis/routing.py`
  - `backend/src/analysis/errors.py` (ou exceptions dans `service.py` si coherence conservee)
- Configuration exploitee (lecture, pas de hardcode):
  - `config/analysis_profiles.yaml`
  - `config/routing.yaml`
- Tests a etendre:
  - `backend/tests/analysis/test_service.py`
  - `backend/tests/analysis/test_api.py`

### Testing Requirements

- Verifier les parcours AC 1-5 de facon explicite en tests.
- Verifier priorite stricte du `profile_id` explicite sur le routage auto.
- Verifier mecanisme retire si `routing_confidence < 0.7` et coherence de `profile_used`.
- Verifier bornes de `routing_confidence` (`0.0`, `1.0`, hors bornes rejects/normalisation).
- Verifier erreurs maitrisees quand config prompts/routing invalide ou vide.
- Verifier non-regression de 1.2: coherence `score -> decision`, schema de base, mapping erreurs existant.

### Previous Story Intelligence

- Story 1.2 a etabli les patterns utiles: `api -> service`, validation defensive des sorties inference, tests feature-first.
- Le contrat actuel `AnalyzeRequest(text, prompt)` doit evoluer proprement vers un mode avec `profile_id` optionnel, sans casser les usages existants d un coup.
- Les tests existants valident deja les erreurs `500/503`; reutiliser cette logique pour les erreurs de routage/configuration plutot que dupliquer des chemins.
- Le simulateur d inference actuel attend un prompt texte; la resolution de `profile_id` devra produire un prompt concret avant appel inference.

### Git Intelligence Summary

- Commit recent cle: `43a6e4d implement story 1.2 scoring and analysis API` a introduit `analysis/{api,service,schemas,scoring,decision}` et leurs tests.
- Commit `1a2d3d1 set up story 1.1 bootstrap foundation` a fixe la structure feature-first et les fichiers de config racine.
- Les modifications recentes se concentrent deja dans `backend/src/analysis/` et `backend/tests/analysis/`; continuer dans cette zone reduit le risque de regression.
- Style de commits observe: messages imperatifs courts, alignes sur l intention de livraison.

### Latest Tech Information

- FastAPI `0.129.0` est publie (PyPI) avec trajectoire continue 0.128.x -> 0.129.x; garder version pinnee et tester le contrat OpenAPI apres changement de schemas.
- Pydantic `2.12.5` stabilise le support Python 3.14 et corrige des regressions de serialisation; pertinent pour l ajout de champs optionnels de reponse.
- Uvicorn `0.40.0` retire Python 3.9; alignement deja coherent avec la base projet moderne.
- HTTPX reste en `0.28.1` (stable) avec pre-releases `1.0.dev*`; eviter migration non necessaire dans cette story.
- NiceGUI `3.7.1` suit un correctif securite 3.7.0 (XSS markdown, path traversal upload); utile pour la consommation sure des metadonnees affichees en UI.

### Project Structure Notes

- Le code existant montre `AnalyzeRequest.prompt` obligatoire; la migration vers `profile_id` doit etre gerable sans rupture brutale.
- Les configs `config/analysis_profiles.yaml` et `config/routing.yaml` sont encore placeholders; ajouter des garde-fous explicites pour "configuration incomplete".
- Aucun fichier `project-context.md` detecte; le contexte provient des artefacts BMAD et du code de la branche.

### References

- Story 1.3 et AC: [Source: _bmad-output/planning-artifacts/epics.md#Story 1.3]
- Exigences FR/NFR: [Source: _bmad-output/planning-artifacts/prd.md#Functional Requirements], [Source: _bmad-output/planning-artifacts/prd.md#Non-Functional Requirements]
- Contraintes architecture/patterns: [Source: _bmad-output/planning-artifacts/architecture.md#Implementation Patterns & Consistency Rules], [Source: _bmad-output/planning-artifacts/architecture.md#Project Structure & Boundaries]
- Contraintes UX de restitution details: [Source: _bmad-output/planning-artifacts/ux-design-specification.md#Experience Principles], [Source: _bmad-output/planning-artifacts/ux-design-specification.md#Component Strategy]
- Story precedente: [Source: _bmad-output/implementation-artifacts/1-2-implementer-le-moteur-de-scoring-et-de-decision.md]
- Veille technique: [Source: https://pypi.org/project/fastapi/], [Source: https://fastapi.tiangolo.com/release-notes/], [Source: https://pypi.org/project/pydantic/], [Source: https://docs.pydantic.dev/latest/changelog/], [Source: https://pypi.org/project/uvicorn/], [Source: https://uvicorn.dev/release-notes/], [Source: https://pypi.org/project/httpx/], [Source: https://github.com/encode/httpx/releases], [Source: https://pypi.org/project/nicegui/]

### Project Context Reference

- Aucun fichier `project-context.md` trouve via pattern `**/project-context.md`.
- Contexte derive de `epics.md`, `architecture.md`, `prd.md`, `ux-design-specification.md`, `sprint-status.yaml`, et du code courant.

### Story Completion Status

- Story context cree avec statut `ready-for-dev`.
- Note de completion: Ultimate context engine analysis completed - comprehensive developer guide created.

## Dev Agent Record

### Agent Model Used

openai/gpt-5.3-codex

### Debug Log References

- Analyse artefacts: `epics.md`, `prd.md`, `architecture.md`, `ux-design-specification.md`, `sprint-status.yaml`.
- Analyse code existant: `backend/src/analysis/{api.py,service.py,schemas.py}`, `backend/tests/analysis/{test_api.py,test_service.py}`, `config/{analysis_profiles.yaml,routing.yaml,inference_engines.yaml}`.
- Analyse story precedente: `1-2-implementer-le-moteur-de-scoring-et-de-decision.md`.
- Analyse git recente: 5 derniers commits + fichiers modifies.
- Veille technique: pages officielles FastAPI/Pydantic/Uvicorn/HTTPX/NiceGUI (versions stables et changements critiques).

### Implementation Plan

- Ajouter un module de routage dedie pour charger `config/analysis_profiles.yaml` et `config/routing.yaml`, resoudre le prompt effectif et calculer `routing_confidence`.
- Integrer la resolution de prompt dans `analysis.service.analyze_text` en conservant le pipeline inference -> score -> decision existant.
- Etendre `analysis.schemas` et `analysis.api` pour supporter `profile_id` optionnel, mecanisme retire legacy `prompt`, metadonnees de routage, et erreurs maitrisees `404/500`.
- Couvrir les parcours AC 1-5 avec tests de routage, service et API, puis lancer regression complete + lint.

### Completion Notes List

- Story selection automatique depuis premier statut `backlog` dans `sprint-status.yaml`: `1-3-ajouter-le-routage-automatique-de-contexte-metier`.
- Story file genere avec guide dev complet pour implementation sans ambiguite.
- Statut story fixe a `ready-for-dev` dans ce document et dans `sprint-status.yaml`.
- Resolution de prompt implementee avec mode explicite (`profile_id`) prioritaire, mode auto base configuration, mecanisme retire par seuil configurable et metadata `profile_used`/`routing_confidence`.
- Contrat API `POST /analyze` etendu: `AnalyzeRequest` accepte `profile_id` optionnel (avec compat `prompt` legacy), `AnalyzeResponse` expose les metadonnees de routage sans casser `score/decision/justification`.
- Gestion d erreurs maitrisee ajoutee pour routage/configuration (`404` prompt inconnu, `500` absence de prompt resolvable), avec journalisation technique sans fuite de texte brut utilisateur.
- Tests ajoutes/etendus (`test_routing.py`, `test_service.py`, `test_api.py`) + regression backend complete et lint validates (`37 passed`, `ruff check` OK).

### File List

- _bmad-output/implementation-artifacts/1-3-ajouter-le-routage-automatique-de-contexte-metier.md
- _bmad-output/implementation-artifacts/sprint-status.yaml
- backend/src/analysis/api.py
- backend/src/analysis/errors.py
- backend/src/analysis/routing.py
- backend/src/analysis/schemas.py
- backend/src/analysis/service.py
- backend/tests/analysis/test_api.py
- backend/tests/analysis/test_routing.py
- backend/tests/analysis/test_service.py

### Change Log

- 2026-02-12: Implementation completee de Story 1.3 (routage auto/explicite, mecanisme retire seuil, extension contrat API, erreurs maitrisees, couverture tests et validations qualite).
