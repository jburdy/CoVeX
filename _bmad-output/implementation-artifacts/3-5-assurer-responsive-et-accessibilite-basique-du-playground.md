# Story 3.5: Assurer responsive et accessibilite basique du Playground

> Note 2026-03-14: artefact BMAD historique. Certaines references internes
> (tests, modules, `criteria`, hot reload, pages playground) peuvent ne plus
> correspondre exactement au depot courant. Pour l'etat actuel, se fier a
> `README.md`, `docs/ARCHITECTURE.md` et `docs/ANALYSIS_PROFILES_METIER.md`.


Status: review

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a utilisateur mobile ou clavier-only,
I want utiliser le Playground facilement sur differentes tailles d ecran et avec navigation clavier,
so that l experience reste inclusive et exploitable en demo comme en usage quotidien.

## Acceptance Criteria

1. **Given** le Playground est ouvert sur mobile (>=375px), tablet et desktop **When** la page est rendue **Then** les composants restent lisibles et utilisables sans chevauchement **And** le flux principal conserve la hierarchie `input -> action -> resultat -> details`.
2. **Given** un ecran mobile **When** les actions sont affichees **Then** les boutons se repositionnent en pile ou wrap de facon ergonomique **And** la cible tactile reste suffisante pour interaction confortable.
3. **Given** une navigation clavier-only **When** l utilisateur parcourt la page via Tab et Shift+Tab **Then** l ordre de focus est logique (contexte, textarea, actions, resultat, details) **And** l etat de focus est visible sur les elements interactifs.
4. **Given** des indicateurs de decision colores **When** le resultat est affiche **Then** l information est aussi fournie textuellement (`KO`, `PARTIEL`, `OK`) **And** la comprehension ne depend pas de la couleur seule.
5. **Given** un lecteur d ecran ou verification a11y basique **When** les champs principaux sont annonces **Then** les labels de saisie et de contexte sont explicites **And** le changement de resultat est percevable pour l utilisateur.

## Tasks / Subtasks

- [x] Adapter la mise en page Playground pour mobile/tablet/desktop sans rupture de hierarchie (AC: 1)
  - [x] Ajuster les conteneurs `ui.row`/`ui.column` pour eviter chevauchements et conserver `input -> action -> resultat -> details`
  - [x] Verifier que la structure reste stable avec et sans resultat, et en etat d erreur
  - [x] Maintenir un rendu exploitable a partir de 375px
- [x] Rendre les actions ergonomiques sur mobile (AC: 2)
  - [x] Faire passer les boutons en wrap/pile selon breakpoint
  - [x] Garantir des cibles tactiles suffisantes (>=44x44 logique Quasar)
  - [x] Conserver `Analyser` comme action primaire clairement visible
- [x] Fiabiliser la navigation clavier et la visibilite du focus (AC: 3)
  - [x] Confirmer un ordre de tabulation logique depuis contexte jusqu aux details
  - [x] Ajouter/renforcer les attributs/labels necessaires pour elements interactifs
  - [x] Valider que le focus natif Quasar reste visible sur les controles critiques
- [x] Verrouiller l accessibilite du resultat principal (AC: 4)
  - [x] Conserver le libelle texte explicite de decision en plus du code couleur
  - [x] Verifier les cas `KO`, `PARTIEL`, `OK` dans le panneau resultat
- [x] Renforcer l annoncabilite des champs et du resultat pour a11y basique (AC: 5)
  - [x] Verifier labels explicites sur selecteur contexte et zone de saisie
  - [x] Ajouter un mecanisme simple pour rendre perceptible la mise a jour resultat
- [x] Couvrir AC1-AC5 avec tests front cibles
  - [x] Ajouter des tests de layout/composition pour petits et grands ecrans
  - [x] Ajouter des tests de navigation clavier/focus visibles sur controles principaux
  - [x] Ajouter des tests sur libelles textuels de decision et labels de champs

## Dev Notes

- Story 3.5 termine l Epic 3 cote UX en posant les garde-fous responsive/a11y sur un flux deja stabilise par 3.1 a 3.4.
- Le but est d eviter les regressions de demonstration: UI inutilisable sur mobile, ordre de focus incoherent, ou signal de decision uniquement couleur.
- Cette story ne change pas le contrat metier/API; elle durcit presentation, ergonomie et accessibilite basique.

### Developer Context Section

- Contexte Epic 3: apres saisie/lancement (3.1), rendu resultat (3.2), details opt-in (3.3) et robustesse erreurs/loading (3.4), 3.5 finalise l experience inclusive.
- Valeur metier: garantir une demo fiable en desktop/projecteur et un usage acceptable en mobile/keyboard-only.
- Dependances amont:
  - 3.1 a etabli le flux `prepare_submission` et la structure de base de la page.
  - 3.2 a impose la hierarchie UX `score -> decision -> justification`.
  - 3.3 a ajoute les details techniques opt-in avec anti-stale state.
  - 3.4 a stabilise loading/erreurs/preservation de saisie.
- Impact aval: cloture de l Epic 3 avec un socle UI pret pour stories d exploitation API (Epic 4).

### Technical Requirements

- Conserver `playground/src/playground/page.py` comme orchestrateur de la page et des interactions de soumission.
- Adapter la composition des actions/resultat pour comportement responsive sans dupliquer la logique metier.
- Maintenir les labels explicites et l ordre de tabulation logique sur les controles principaux.
- Assurer que l affichage de decision reste double-canal (texte + couleur) dans tous les etats.
- Garder la preservation de saisie et les transitions d etat existantes (pas de reset involontaire du texte).

### Architecture Compliance

- Respecter la frontiere `UI -> api_client -> backend`; aucun appel HTTP direct hors `playground/src/api_client/client.py`.
- Conserver un etat local page-level (`playground/src/playground/state.py`), sans store global ni event bus.
- Garder les conventions `snake_case` pour Python, et coherence des payloads JSON deja en place.
- Limiter les changements a la couche playground Playground; pas de modification du contrat backend `/analyze`.

### Library/Framework Requirements

- NiceGUI/Quasar: utiliser composants natifs (`row`, `column`, `button`, `select`, `textarea`, `expansion`) avec classes de layout responsive.
- Quasar a11y baseline: conserver focus visible natif et labels explicites sur les champs interactifs.
- Mapping visuel decision: garder `negative/warning/positive` et texte `KO/PARTIEL/OK` associe.

### File Structure Requirements

- Fichiers cibles principaux:
  - `playground/src/playground/page.py`
  - `playground/src/playground/components.py`
  - `playground/src/playground/state.py` (si un champ de presentation/focus est necessaire)
- Fichiers de tests cibles:
  - `playground/tests/test_playground_components.py`
  - `playground/tests/test_playground_page_submission.py`

### Testing Requirements

- AC1: verifier lisibilite/utilisabilite de la page aux largeurs 375, 768, 1024+ sans chevauchement ni inversion de hierarchie.
- AC2: verifier que les actions passent en wrap/pile sur mobile et restent actionnables.
- AC3: verifier ordre Tab/Shift+Tab et focus visible sur contexte, textarea, actions, resultat/details.
- AC4: verifier que les decisions restent explicites par texte et pas seulement par couleur.
- AC5: verifier labels explicites et perceptibilite de la mise a jour resultat en scenario lecteur d ecran basique.

### Previous Story Intelligence

- Story 3.4 confirme que la robustesse UX repose sur `state.is_submitting`, messages courts, et reactivation garantie en `finally`; 3.5 doit preserver ce comportement.
- Story 3.4 a etabli une cartographie claire des erreurs API (`400/404/500/503`) et des tests front cibles; ne pas regresser ces garanties.
- Story 3.3 a verrouille le panneau details opt-in et le pattern anti-stale (`state.last_result`) qui doivent rester compatibles avec les ajustements responsive.
- Story 3.2 a fixe la hierarchie resultat principale; 3.5 ajuste la forme, pas cet ordre d information.

### Git Intelligence Summary

- `d1166dd` (story 3.4): renforce loading/erreurs/preservation saisie dans `playground/src/playground/page.py` et `playground/src/api_client/client.py`.
- `6e5f87f` (story 3.3): introduit details techniques opt-in et tests correspondants; base directe pour valider rendu responsive/details.
- `3d60705` (story 3.2): stabilise panneau resultat et mapping decision/couleur; a conserver en priorite.
- `fefde74` (story 3.1): pose structure playground + api_client + tests; sert de reference d architecture front.

### Latest Tech Information

- FastAPI: `0.129.0` est publie, avec abandon Python 3.9 (>=3.10 requis). [Source: https://fastapi.tiangolo.com/release-notes/]
- Uvicorn: `0.40.0` retire aussi Python 3.9; garder coherence runtime backend. [Source: https://uvicorn.dev/release-notes/]
- NiceGUI: `3.7.1` est la release recente; `3.7.0` corrige des failles XSS/path traversal, donc eviter versions anterieures. [Source: https://data.safetycli.com/packages/pypi/nicegui/changelog]
- HTTPX: `0.28.1` corrige un cas SSL; `0.28.0` deprecie certaines options SSL (`verify` string, `cert`). [Source: https://github.com/encode/httpx/blob/master/CHANGELOG.md]

### Project Structure Notes

- Aucun `project-context.md` trouve via `**/project-context.md`.
- Structure projet observee compatible architecture:
  - `playground/src/playground/page.py`
  - `playground/src/playground/components.py`
  - `playground/src/playground/state.py`
  - `playground/src/api_client/client.py`
  - `playground/tests/test_playground_components.py`
  - `playground/tests/test_playground_page_submission.py`
- Aucun conflit structurel detecte pour cette story.

### References

- Story 3.5 et AC: [Source: `_bmad-output/planning-artifacts/epics.md#Story 3.5`]
- Contraintes UX responsive/a11y: [Source: `_bmad-output/planning-artifacts/ux-design-specification.md#Responsive Design & Accessibility`], [Source: `_bmad-output/planning-artifacts/ux-design-specification.md#Flow Optimization Principles`]
- Contraintes architecture patterns/boundaries: [Source: `_bmad-output/planning-artifacts/architecture.md#Implementation Patterns & Consistency Rules`], [Source: `_bmad-output/planning-artifacts/architecture.md#Project Structure & Boundaries`]
- Contrat API et formats: [Source: `_bmad-output/planning-artifacts/prd.md#API Specifications`]
- Learnings story precedente: [Source: `_bmad-output/implementation-artifacts/3-4-gerer-proprement-les-etats-ux-loading-erreurs-preservation-saisie.md`]

### Story Completion Status

- Story context cree avec statut `ready-for-dev`.
- Note de completion: Ultimate context engine analysis completed - comprehensive developer guide created.

## Dev Agent Record

### Agent Model Used

openai/gpt-5.3-codex

### Debug Log References

- Artefacts analyses: `_bmad-output/planning-artifacts/epics.md`, `_bmad-output/planning-artifacts/prd.md`, `_bmad-output/planning-artifacts/architecture.md`, `_bmad-output/planning-artifacts/ux-design-specification.md`, `_bmad-output/implementation-artifacts/sprint-status.yaml`.
- Story precedente analysee: `_bmad-output/implementation-artifacts/3-4-gerer-proprement-les-etats-ux-loading-erreurs-preservation-saisie.md`.
- Git intelligence: `git log -5 --pretty=format:'COMMIT %h%nTITLE %s%n' --name-status`.
- Veille technique: release notes FastAPI/Uvicorn et changelogs NiceGUI/HTTPX.

### Implementation Plan

- Passer en TDD sur les exigences responsive/a11y: ecrire d abord les tests cibles AC1-AC5, puis adapter les composants.
- Structurer les controles Playground pour conserver la hierarchie input -> action -> resultat -> details sur tous breakpoints.
- Renforcer accessibilite clavier (tabindex/labels/focus visible) et annoncabilite resultat via region live.
- Valider non-regression avec suites playground et backend + lint configure.

### Completion Notes List

- Story 3.5 preparee pour implementation avec guardrails explicites responsive + accessibilite basique.
- Risques de regression identifies et cadrage strict des surfaces de modification playground.
- Exigences de tests AC1-AC5 formalisees pour eviter les regressions silencieuses UX.
- Implementation livree: ordre logique contexte -> textarea -> action, bouton principal responsive avec cible tactile >=44px, labels explicites et classes de focus visibles sur controles critiques.
- Accessibilite resultat renforcee: maintien texte decision (`KO`, `PARTIEL`, `OK`) + ajout d une region live (`role=status`, `aria-live=polite`) mise a jour a chaque nouvelle analyse.
- Tests ajoutes et valides pour focus/tab order, contraintes mobile et annoncabilite resultat; suites playground/backend et lint executees sans regression.

### File List

- _bmad-output/implementation-artifacts/3-5-assurer-responsive-et-accessibilite-basique-du-playground.md
- _bmad-output/implementation-artifacts/sprint-status.yaml
- playground/src/playground/components.py
- playground/src/playground/page.py
- playground/tests/test_playground_components.py
- playground/tests/test_playground_page_submission.py

## Change Log

- 2026-02-13: Story 3.5 implementee (responsive + a11y Playground), tests AC1-AC5 ajoutes/etendus, statut passe a `review`.
