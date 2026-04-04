# Story 3.1: Construire le Playground de saisie et lancement d analyse

> Note 2026-03-14: artefact BMAD historique. Certaines references internes
> (tests, modules, `criteria`, hot reload, pages playground) peuvent ne plus
> correspondre exactement au depot courant. Pour l'etat actuel, se fier a
> `README.md`, `docs/ARCHITECTURE.md` et `docs/ANALYSIS_PROFILES_METIER.md`.


Status: review

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a utilisateur demo,
I want saisir un texte, choisir un contexte (ou Auto) et lancer l analyse en un clic,
so that je puisse evaluer rapidement la completude d une demande.

## Acceptance Criteria

1. **Given** la page Playground est ouverte **When** l interface est affichee **Then** elle contient une zone de saisie texte, un selecteur de contexte, et un bouton principal `Analyser` **And** la valeur par defaut du contexte est `Auto`.
2. **Given** au moins un prompt est disponible **When** l utilisateur ouvre le selecteur de contexte **Then** il voit la liste des profils d'analyse metier disponibles **And** il peut choisir un prompt explicite ou laisser `Auto`.
3. **Given** le champ texte est vide **When** l utilisateur tente de lancer l analyse **Then** l action est bloquee avec un retour explicite **And** aucune requete API inutile n est envoyee.
4. **Given** un texte valide est saisi **When** l utilisateur clique sur `Analyser` **Then** la requete est envoyee vers l API avec le contexte choisi **And** l etat UI passe en mode traitement jusqu a reception du resultat.
5. **Given** le contexte `Auto` est selectionne **When** la requete est construite **Then** aucun `profile_id` force n est envoye **And** le routage automatique cote backend est laisse actif.

## Tasks / Subtasks

- [x] Mettre en place la page Playground MVP avec structure verticale unique (AC: 1)
  - [x] Creer la zone de saisie texte principale et le selecteur de contexte
  - [x] Ajouter le bouton primaire `Analyser` avec hierarchie visuelle claire
  - [x] Initialiser la valeur de contexte a `Auto`
- [x] Integrer la source de prompts pour alimenter le selecteur de contexte (AC: 2)
  - [x] Recuperer les prompts actifs via client API dedie
  - [x] Afficher les options metier + `Auto` sans ambiguite
  - [x] Gerer l etat liste vide proprement
- [x] Implementer la validation UI avant soumission (AC: 3)
  - [x] Bloquer l action si texte vide
  - [x] Afficher un feedback utilisateur explicite et neutre
  - [x] Eviter tout appel API quand validation echoue
- [x] Implementer le flux de soumission vers `POST /analyze` (AC: 4, 5)
  - [x] Construire la payload avec `profile_id` uniquement si contexte explicite
  - [x] Envoyer la requete via `playground/src/api_client/client.py`
  - [x] Passer l UI en etat `is_submitting` pendant le traitement puis restaurer l etat
- [x] Poser les tests minimaux backend/playground cibles pour verrouiller le contrat (AC: 1, 2, 3, 4, 5)
  - [x] Verifier payload en mode `Auto` (pas de `profile_id`)
  - [x] Verifier payload avec prompt explicite
  - [x] Verifier blocage sur texte vide

## Dev Notes

- Story 3.1 ouvre Epic 3 (Playground) et doit livrer une boucle d interaction minimale mais complete: `saisie -> selection contexte -> lancement analyse`.
- Le scope est volontairement limite a l orchestration d entree et a l envoi API; l affichage resultat detaille arrive en story 3.2/3.3.
- Garder l implementation simple et lisible pour ne pas casser le rythme de livraison MVP demo-first.

### Developer Context Section

- **Contexte Epic 3:** experience demonstrable et actionnable pour decideurs et utilisateurs, avec UX epuree et feedback rapide.
- **Valeur business 3.1:** rendre le produit testable immediatement en demo avec une interaction claire en un clic.
- **Dependances amont:** stories Epic 1 et 2 ont deja stabilise `POST /analyze`, routage `Auto`, configuration prompts et metadonnees de base.
- **Dependances aval:** stories 3.2, 3.3, 3.4 et 3.5 reutiliseront cette base UI et son flux de soumission.

### Technical Requirements

- Utiliser un flux de soumission deterministe: validation locale -> construction payload -> appel API -> gestion etat loading.
- Respecter le contrat API JSON en `snake_case`; ne pas introduire de transformation ad hoc cote UI.
- En mode `Auto`, ne pas envoyer `profile_id`; en mode explicite, envoyer l identifiant tel que retourne par `/analysis-profiles`.
- Preserver la saisie utilisateur pendant les transitions d etat UI.
- Maintenir une implementation stateless cote CoVeX (aucune persistance texte, aucun cache metier).

### Architecture Compliance

- Playground consomme le backend uniquement via `playground/src/api_client/client.py`.
- UI monolithique MVP avec etat local (pas de store global, pas d event bus).
- Respect strict des conventions `snake_case` (code Python, payloads, metadonnees).
- Pas de logique inference dans la couche UI; l UI orchestre et affiche uniquement.

### Library/Framework Requirements

- NiceGUI/Quasar pour composants UI standards (`ui.textarea`, `ui.select`, `ui.button`, `ui.card`).
- FastAPI: conserver le contrat `POST /analyze` deja en place (pas de changement d endpoint).
- Pydantic/FastAPI schema: payload validee par contrat existant, pas de champ supplementaire hors spec.
- HTTP client playground: reutiliser le client API existant, pas de duplication de logique transport.

### File Structure Requirements

- Cibles playground principales:
  - `playground/src/app.py`
  - `playground/src/playground/page.py`
  - `playground/src/playground/state.py`
  - `playground/src/playground/actions.py`
  - `playground/src/playground/components.py`
  - `playground/src/api_client/client.py`
  - `playground/src/api_client/schemas.py`
- Cibles tests/validation probables:
  - `backend/tests/analysis-profiles/test_api.py` (si ajustement contrat prompts)
  - `backend/tests/analysis/test_api.py` (si verification payload analyze)

### Testing Requirements

- AC1: verifier presence des 3 blocs UI obligatoires (textarea, selecteur contexte, bouton `Analyser`) et contexte par defaut `Auto`.
- AC2: verifier que les prompts disponibles sont affiches et selectionnables.
- AC3: verifier blocage submission texte vide + absence d appel API.
- AC4: verifier qu un texte valide declenche l appel API et active l etat loading.
- AC5: verifier construction payload en mode `Auto` sans `profile_id`.

### Library Framework Requirements

- FastAPI latest note: `0.129.0` retire Python 3.9, aligner environnement sur Python >= 3.10. [Source: https://fastapi.tiangolo.com/release-notes/]
- Pydantic latest stable: `2.12.5`, inclut correctifs 2.12.x et compatibilite Python recentes. [Source: https://docs.pydantic.dev/latest/changelog/]
- Uvicorn latest stable: `0.40.0`, retrait Python 3.9 et support Python 3.14 de la serie recente. [Source: https://uvicorn.dev/release-notes/]
- NiceGUI latest stable: `3.7.1`; mettre au moins `3.7.0+` pour inclure correctifs securite XSS/path traversal. [Source: https://pypi.org/project/nicegui/], [Source: https://newreleases.io/project/pypi/nicegui/release/3.7.0]
- HTTPX baseline de reference: `0.28.1`; attention aux deprecations SSL de `0.28.0` si evolution client. [Source: https://github.com/encode/httpx/releases]

### Project Structure Notes

- Aucun fichier `project-context.md` detecte via le pattern `**/project-context.md`.
- Sources de contexte utilisees: `epics.md`, `prd.md`, `architecture.md`, `ux-design-specification.md`, `sprint-status.yaml`.

### References

- Story 3.1 et AC: [Source: `_bmad-output/planning-artifacts/epics.md#Story 3.1`]
- FR22/FR23/FR24 et scope Playground: [Source: `_bmad-output/planning-artifacts/prd.md#Playground UI`]
- Contraintes architecture UI/API et structure: [Source: `_bmad-output/planning-artifacts/architecture.md#Project Structure & Boundaries`], [Source: `_bmad-output/planning-artifacts/architecture.md#Implementation Patterns & Consistency Rules`]
- Exigences UX d interaction, hierarchie et feedback: [Source: `_bmad-output/planning-artifacts/ux-design-specification.md#Core User Experience`], [Source: `_bmad-output/planning-artifacts/ux-design-specification.md#UX Consistency Patterns`]

### Story Completion Status

- Story context cree avec statut `ready-for-dev`.
- Note de completion: Ultimate context engine analysis completed - comprehensive developer guide created.

## Dev Agent Record

### Agent Model Used

openai/gpt-5.3-codex

### Debug Log References

- Artefacts analyses: `epics.md`, `prd.md`, `architecture.md`, `ux-design-specification.md`, `sprint-status.yaml`.
- Veille technique effectuee: FastAPI, Pydantic, Uvicorn, NiceGUI, HTTPX.
- Commandes validation executees: `uv run --project . pytest` (backend), `uv run --project . --with pytest pytest` (playground), `uv run --project . ruff check` (backend), `uv run --project . --with ruff ruff check` (playground).

### Completion Notes List

- Implante la page Playground MVP NiceGUI avec textarea, select de contexte et bouton `Analyser` (contexte `Auto` par defaut).
- Ajoute le client playground `ApiClient` pour `/analysis-profiles` et `POST /analyze`, avec gestion d erreurs de transport et validation minimale de schema.
- Implante le flux de soumission deterministic: validation locale, payload conditionnelle (`profile_id` omis en mode `Auto`), etat `is_submitting`, feedback utilisateur.
- Ajoute les tests playground couvrant AC1-AC5 cibles: options contexte, payload Auto/explicite, blocage texte vide, et non-appel API sur validation invalide.
- Validation complete executee: 98 tests backend OK, 6 tests playground OK, lint backend/playground OK.

### File List

- _bmad-output/implementation-artifacts/3-1-construire-le-playground-de-saisie-et-lancement-d-analyse.md
- _bmad-output/implementation-artifacts/sprint-status.yaml
- playground/pyproject.toml
- playground/src/app.py
- playground/src/api_client/client.py
- playground/src/api_client/schemas.py
- playground/src/playground/actions.py
- playground/src/playground/components.py
- playground/src/playground/page.py
- playground/src/playground/state.py
- playground/tests/test_playground_actions.py
- playground/tests/test_playground_components.py
- playground/tests/test_playground_page_submission.py

## Change Log

- 2026-02-13: Implementation story 3.1 completee (Playground MVP, client API playground, validation UI, flux de soumission, tests playground, validations regression/lint).

## Senior Developer Review (AI)

### Review Summary
- **Reviewer:** JBU
- **Date:** 2026-02-23
- **Outcome:** Approved

### Findings

#### High Severity
- None

#### Medium Severity
- **Gestion d'erreur basique:** La fonction `_map_api_error_message` retourne des messages génériques pour certains codes d'erreur. Pourrait être enrichie avec plus de détails (en gardant la sécurité).

#### Low Severity
- **Couverture tests:** Tests playground couvrent les AC principaux mais pas les cas limites UI (ex: réseaulent de la fenêtre pendant loading).

### Verification
- ✅ Tests backend: 107 passent
- ✅ Tests playground: 29 passent
- ✅ Lint backend: All checks passed
- ✅ AC1-AC5 fully implemented
- ✅ File List: tous les fichiers existants
- ✅ Payload Auto mode: pas de profile_id envoyé

### Notes
- Le Playground MVP est bien structuré
- La validation texte vide fonctionne
- Le flux de soumission est deterministic
- L'état `is_submitting` est correctement géré
- Les demos examples sont bien intégrés
