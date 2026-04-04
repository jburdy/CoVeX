# Story 3.2: Afficher le resultat principal de maniere lisible et actionnable

> Note 2026-03-14: artefact BMAD historique. Certaines references internes
> (tests, modules, `criteria`, hot reload, pages playground) peuvent ne plus
> correspondre exactement au depot courant. Pour l'etat actuel, se fier a
> `README.md`, `docs/ARCHITECTURE.md` et `docs/ANALYSIS_PROFILES_METIER.md`.


Status: review

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a utilisateur final,
I want voir clairement le score, la decision et la justification apres chaque analyse,
so that je comprenne rapidement ce qui est exploitable et ce qui manque.

## Acceptance Criteria

1. **Given** une analyse reussie **When** le resultat est affiche **Then** l UI presente la hierarchie `score -> decision -> justification` **And** cette hierarchie reste stable a chaque execution.
2. **Given** un score retourne par l API **When** la decision correspondante est determinee **Then** l indicateur visuel applique le mapping couleur attendu (`KO=negative`, `PARTIEL=warning`, `OK=positive`) **And** la decision est aussi visible textuellement (pas couleur seule).
3. **Given** une decision `KO` ou `PARTIEL` **When** la justification est affichee **Then** les elements manquants sont comprehensibles et orientent la correction **And** l utilisateur peut modifier son texte puis relancer sans perdre le contexte de travail.
4. **Given** plusieurs analyses consecutives dans la meme session **When** un nouveau resultat arrive **Then** l affichage est remplace proprement sans incoherence UI **And** les valeurs affichees correspondent strictement a la derniere reponse API.
5. **Given** une reponse API partielle (metadonnees absentes mais champs minimaux presents) **When** le panneau principal est rendu **Then** l affichage reste fonctionnel avec `score`, `decision`, `justification` **And** aucune erreur front ne bloque l utilisateur.

## Tasks / Subtasks

- [x] Implementer le panneau resultat principal avec hierarchie fixe `score -> decision -> justification` (AC: 1)
  - [x] Structurer un conteneur resultat stable (reserve dans le layout) pour eviter reflow brutal entre analyses
  - [x] Rendre explicitement les trois niveaux dans le meme ordre a chaque refresh
- [x] Appliquer le mapping visuel de decision conforme UX/architecture (AC: 2)
  - [x] Mapper `KO` vers `negative`, `PARTIEL` vers `warning`, `OK` vers `positive`
  - [x] Conserver un libelle textuel explicite (`KO`, `PARTIEL`, `OK`) en plus de la couleur
- [x] Afficher une justification actionnable pour guider la correction (AC: 3)
  - [x] Prioriser la lisibilite de la justification (phrase claire + liste manquants si disponible)
  - [x] Garantir que l edition du texte reste possible sans reset de saisie
- [x] Assurer la coherence sur analyses consecutives (AC: 4)
  - [x] Remplacer proprement l etat resultat precedent par le nouveau sans valeurs stale
  - [x] Verifier que les donnees affichees proviennent toujours de la derniere reponse API
- [x] Gerer les reponses partielles sans bloquer le flux principal (AC: 5)
  - [x] Rendre robustes les composants si metadonnees techniques absentes
  - [x] Conserver l affichage des champs minimaux `score`, `decision`, `justification`
- [x] Ajouter/ajuster les tests playground cibles pour verrouiller AC1-AC5
  - [x] Tests de rendu et ordre visuel du panneau principal
  - [x] Tests mapping decision/couleur + texte
  - [x] Tests de remplacement propre sur analyses successives
  - [x] Tests de tolerance aux payloads partiels

## Dev Notes

- Story 3.2 etend directement le flux cree en 3.1: apres soumission, l utilisateur doit obtenir un verdict lisible et actionnable sans surcharge technique.
- Le scope 3.2 couvre uniquement le resultat principal. Les details techniques opt-in restent la responsabilite de la story 3.3.
- Priorite UX: clarte immediate pour demos decideurs (effet de comprehension instantanee), tout en restant robuste sur reponses partielles.

### Developer Context Section

- **Contexte Epic 3:** fournir une experience Playground demonstrable, avec feedback interpretable pour decideurs et utilisateurs non techniques.
- **Valeur business 3.2:** transformer une simple execution API en resultat comprenable et actionnable au premier coup d oeil.
- **Dependances amont:** 3.1 a deja livre la saisie, la selection de contexte et l orchestration de `POST /analyze`.
- **Dependances aval:** 3.3 reutilisera ce panneau principal pour y adosser les details techniques opt-in, 3.4 gerera les etats erreurs/loading complets.

### Technical Requirements

- Conserver une hierarchie de rendu strictement stable: `score` puis `decision` puis `justification`.
- Mapper la decision selon les seuils metier MVP (`KO <= 30`, `PARTIEL 31-70`, `OK > 70`) et afficher la decision textuelle en permanence.
- Considerer le panneau principal comme prioritaire: aucune dependance obligatoire a des metadonnees optionnelles (`model_used`, `tokens_*`, etc.).
- Assurer la mise a jour atomique de l etat resultat pour eviter melange ancien/nouveau sur analyses consecutives.
- Preserver la saisie utilisateur existante pendant l affichage resultat (pas de reset implicite du textarea).

### Architecture Compliance

- Respecter la frontiere playground -> backend via `playground/src/api_client/client.py` uniquement (pas d appels HTTP ad hoc dans composants).
- Maintenir un etat local NiceGUI (pas de store global ni event bus) coherent avec la page monolithique MVP.
- Respecter les conventions `snake_case` pour schemas/metadonnees et code Python.
- Ne pas deplacer la logique metier de scoring/decision dans l UI: l UI affiche et guide, le backend decide.

### Library/Framework Requirements

- NiceGUI/Quasar: utiliser les composants standards (`ui.label`, `ui.badge`, `ui.card`, `ui.column`) et le mapping couleur natif `negative|warning|positive`.
- FastAPI/Pydantic: ne pas changer le contrat de `POST /analyze`; consommer les champs minimaux tels que fournis.
- API client playground existant: reutiliser les schemas et parseurs deja introduits en 3.1 pour eviter duplications.

### File Structure Requirements

- Fichiers playground prioritairement concernes:
  - `playground/src/playground/components.py`
  - `playground/src/playground/state.py`
  - `playground/src/playground/page.py`
  - `playground/src/playground/actions.py`
- Point d integration transport:
  - `playground/src/api_client/client.py`
  - `playground/src/api_client/schemas.py`
- Tests playground probables:
  - `playground/tests/test_playground_components.py`
  - `playground/tests/test_playground_page_submission.py`

### Testing Requirements

- AC1: verifier que l ordre visuel reste `score -> decision -> justification` pour chaque resultat recu.
- AC2: verifier mapping de decision vers couleur Quasar et presence du libelle textuel.
- AC3: verifier qu un resultat `KO`/`PARTIEL` expose une justification comprenable sans bloquer la reedition du texte.
- AC4: verifier qu une seconde analyse remplace integralement la premiere sans artefacts stale.
- AC5: verifier qu un payload partiel (sans metadonnees optionnelles) n empeche pas l affichage des champs minimaux.

### Previous Story Intelligence

- Story precedente 3.1 a etabli un socle fiable: selecteur `Auto`, validation texte vide, et construction payload conditionnelle `profile_id`.
- Le pattern de separation `actions.py` (orchestration), `state.py` (etat), `components.py` (rendu) est deja en place et doit etre conserve.
- Les tests playground 3.1 couvrent deja le flux de soumission; 3.2 doit etendre ces tests sur le rendu resultat plutot que reimplanter la soumission.
- La story 3.1 a deja valide la robustesse minimale du client API; reutiliser ces primitives evite la reinvention et les regressions.

### Git Intelligence Summary

- Commit `fefde74` montre que le playground Playground est actif dans `playground/src/playground/*` et `playground/src/api_client/*`; 3.2 doit rester concentree sur ces zones.
- Les commits `2.2` a `2.5` ont stabilise le backend (`analysis`, `prompts`, `inference`) et le contrat d analyse; eviter d introduire des changements backend inutiles pour 3.2.
- Pattern recurrent observe: chaque story met a jour son artefact d implementation + `sprint-status.yaml` + tests associes; suivre ce pattern pour coherence de livraison.

### Latest Tech Information

- FastAPI: la release `0.129.0` retire Python 3.9; conserver un runtime Python >= 3.10 pour alignement outillage. [Source: https://fastapi.tiangolo.com/release-notes/]
- Pydantic: reference stable `2.12.5`; conserver compatibilite des models/schemas avec la serie 2.12.x. [Source: https://docs.pydantic.dev/latest/changelog/]
- Uvicorn: `0.40.0` (Python >= 3.10) et support Python 3.14 dans la serie recente; eviter configuration obsolete 3.9. [Source: https://uvicorn.dev/release-notes/]
- NiceGUI: version recente `3.7.1`; appliquer les patchs de la serie 3.7.x pour reduire le risque de bugs UI connus en versions plus anciennes. [Source: https://github.com/zauberzeug/nicegui/releases]
- HTTPX: baseline `0.28.1`; prendre en compte les ajustements SSL/deprecations de la serie 0.28 lors d evolutions du client. [Source: https://github.com/encode/httpx/releases]

### Project Structure Notes

- Aucun fichier `project-context.md` detecte dans le repository avec le pattern `**/project-context.md`.
- Sources primaires utilisees pour cette story: `epics.md`, `architecture.md`, `prd.md`, `ux-design-specification.md`, `sprint-status.yaml`, story `3.1`.

### References

- Story 3.2 + AC officiels: [Source: `_bmad-output/planning-artifacts/epics.md#Story 3.2`]
- Contraintes UX de hierarchie, mapping visuel et lisibilite: [Source: `_bmad-output/planning-artifacts/ux-design-specification.md#Core User Experience`], [Source: `_bmad-output/planning-artifacts/ux-design-specification.md#UX Consistency Patterns`]
- Contrat API minimal et champs optionnels: [Source: `_bmad-output/planning-artifacts/prd.md#API Specifications`]
- Boundaries playground/API et structure cible: [Source: `_bmad-output/planning-artifacts/architecture.md#Project Structure & Boundaries`], [Source: `_bmad-output/planning-artifacts/architecture.md#Implementation Patterns & Consistency Rules`]
- Learnings story precedente: [Source: `_bmad-output/implementation-artifacts/3-1-construire-le-playground-de-saisie-et-lancement-d-analyse.md`]

### Story Completion Status

- Story context cree avec statut `ready-for-dev`.
- Note de completion: Ultimate context engine analysis completed - comprehensive developer guide created.

## Dev Agent Record

### Agent Model Used

openai/gpt-5.3-codex

### Debug Log References

- Artefacts analyses: `_bmad-output/planning-artifacts/epics.md`, `_bmad-output/planning-artifacts/prd.md`, `_bmad-output/planning-artifacts/architecture.md`, `_bmad-output/planning-artifacts/ux-design-specification.md`, `_bmad-output/implementation-artifacts/sprint-status.yaml`.
- Story precedente analysee: `_bmad-output/implementation-artifacts/3-1-construire-le-playground-de-saisie-et-lancement-d-analyse.md`.
- Git intelligence: `git log --oneline -5` et `git show --name-only --pretty=format:'COMMIT %h%nTITLE %s%n' -5`.
- Veille technique: FastAPI, Pydantic, Uvicorn, NiceGUI, HTTPX (release notes/changelogs officiels).

### Implementation Plan

- Creer un panneau resultat NiceGUI stable dans `playground/components.py` avec ordre fixe `Score -> Decision -> Justification`.
- Centraliser le mapping decision vers couleur Quasar dans `playground/actions.py` pour garder une logique testable et simple.
- Mettre a jour `_handle_submit` dans `playground/page.py` pour rendre le resultat de facon atomique a chaque reponse API.
- Etendre les tests playground pour verrouiller ordre visuel, mapping couleur+texte, remplacement sur analyses consecutives et tolerance payloads partiels.

### Completion Notes List

- Story 3.2 preparee avec guide implementable, contraintes techniques explicites et anti-patterns evites.
- Guardrails architecture/playground et tests cibles formalises pour limiter regressions UX dans Epic 3.
- Contexte recent (story 3.1 + commits) integre pour favoriser reutilisation des patterns existants.
- Implementation 3.2 livree: panneau principal stable avec hierarchie `Score -> Decision -> Justification` et placeholders initiaux pour limiter les variations de layout.
- Mapping decision applique via `KO=negative`, `PARTIEL=warning`, `OK=positive` tout en conservant le libelle textuel visible en permanence.
- Rendu resultat rendu atomique sur chaque succes API; la derniere reponse remplace integralement la precedente sans artefacts stale.
- Saisie utilisateur preservee pendant l affichage resultat (aucun reset implicite du textarea).
- Tests playground ajoutes/etendus pour couvrir AC1-AC5, plus regression complete backend/playground et lint Ruff passes.

### File List

- _bmad-output/implementation-artifacts/3-2-afficher-le-resultat-principal-de-maniere-lisible-et-actionnable.md
- _bmad-output/implementation-artifacts/sprint-status.yaml
- playground/src/playground/actions.py
- playground/src/playground/components.py
- playground/src/playground/page.py
- playground/tests/test_playground_components.py
- playground/tests/test_playground_page_submission.py

## Change Log

- 2026-02-13: Implementation Story 3.2 completee (panneau resultat principal, mapping decision/couleur, rendu atomique, tests AC1-AC5, validations backend/playground + lint).
