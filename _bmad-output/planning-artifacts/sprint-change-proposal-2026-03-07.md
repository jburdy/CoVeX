# Sprint Change Proposal - Correct Course

> Note 2026-03-14: artefact BMAD historique. Certaines references internes
> (tests, modules, `criteria`, hot reload, pages playground) peuvent ne plus
> correspondre exactement au depot courant. Pour l'etat actuel, se fier a
> `README.md`, `docs/ARCHITECTURE.md` et `docs/ANALYSIS_PROFILES_METIER.md`.


Date: 2026-03-07
Project: CoVeX
Prepared for: JBU
Workflow: correct-course

## 1. Issue Summary

### Problem Statement

CoVeX changes product direction: automatic routing of business prompts is removed from the target scope.
From now on, every analysis must use an explicit and mandatory context selection provided by the user interface or the API caller.
No static default prompt may be applied when context is missing.

### Discovery Context

This issue is treated as a product-wide strategic pivot rather than a defect isolated to one implementation story.
The strongest trigger artifact is Story 1.3 in the current epic plan, because it explicitly introduces automatic business-context routing that is now out of scope.

### Evidence

- The PRD still defines automatic routing requirements (`FR3`, `FR16`, `FR17`, `FR18`) and optional context submission.
- The architecture still models an `input -> routing -> analysis` flow and includes `routing.yaml`.
- The UX specification still promotes `Auto` as the default mode in the Playground.
- The current epic plan includes Story `1.3-ajouter-le-routage-automatique-de-contexte-metier`.
- Sprint tracking still shows Story 1.3 as `review`, which conflicts with the new product direction.

## 2. Impact Analysis

### Epic Impact

#### Epic 1

Epic 1 remains valid but must be re-scoped.
Its purpose changes from end-to-end analysis with optional routing to end-to-end analysis with explicit and validated context selection.

#### Epic 2

Epic 2 remains valid, but configuration scope must remove routing-specific configuration and focus on prompt governance, model selection, and explicit prompt-to-model resolution.

#### Epic 3

Epic 3 is materially affected.
The Playground can no longer expose `Auto` mode or permit analysis without a user-selected context.

#### Epic 4

Epic 4 becomes more important because `/analysis-profiles` is no longer a nice-to-have convenience only.
It becomes a key enabler for explicit context selection in UI and external integrations.

### Story Impact

#### Invalidated or materially changed stories

- `Story 1.3` must be replaced entirely.
- `Story 2.3` must remove any reference to routing-based prompt resolution.
- `Story 3.1` must remove `Auto` and require prompt selection before submit.
- `Story 3.3` must remove `routing_confidence` and detected-context display.
- `Story 4.2` must be reprioritized upward.

#### Sprint planning impact

- The story currently tracked as `1-3-ajouter-le-routage-automatique-de-contexte-metier` can no longer remain a valid review candidate.
- Stories already in review that assume routing behavior require content review before acceptance.

### Artifact Conflicts

#### PRD

Conflicts exist in:

- Product scope
- Functional requirements
- API schema
- Playground requirements
- Non-functional requirements tied to routing latency
- Glossary definitions related to automatic routing

#### Architecture

Conflicts exist in:

- Primary data flow
- Component responsibilities
- Configuration inventory (`routing.yaml`)
- Request and response schemas
- Integration flow descriptions

#### UX Specification

Conflicts exist in:

- Core interaction flow
- `Auto` default behavior
- User mental model
- Technical details panel content
- Journey diagrams based on automatic detection

#### Secondary Technical Documents

Conflicts exist in:

- `docs/api-contracts-backend.md`
- `docs/architecture-backend.md`
- `docs/architecture-playground.md`
- `docs/integration-architecture.md`
- `/_bmad-output/implementation-artifacts/sprint-status.yaml`

### Technical Impact

- Remove routing engine behavior from backend design.
- Remove default-prompt behavior.
- Make `profile_id` mandatory in the `/analyze` contract.
- Remove `routing_confidence` from the success payload.
- Remove `routing.yaml` from target architecture and implementation plan.
- Shift prompt discovery responsibility to `/analysis-profiles` and to explicit caller behavior.

## 3. Recommended Approach

### Selected Path

Recommended approach: Hybrid of Direct Adjustment + targeted MVP review.

### Why this path

This change does not invalidate CoVeX's core value proposition.
It removes one cross-cutting capability that is now considered undesirable and replaces it with a stricter, more deterministic product rule.
The product can continue on the current trajectory if the planning artifacts, architecture contract, and sprint backlog are corrected before more implementation continues.

### Alternatives considered

#### Option 1 - Direct Adjustment

- Viability: Yes
- Effort: Medium
- Risk: Medium

Strong option because it preserves current momentum while aligning artifacts and backlog quickly.

#### Option 2 - Potential Rollback

- Viability: Yes
- Effort: High
- Risk: High

Possible only if review-stage implementation already deeply embeds routing behavior.
This is more disruptive and should be minimized.

#### Option 3 - MVP Review Only

- Viability: Yes
- Effort: Medium
- Risk: Low

Useful, but insufficient by itself because backlog and technical artifacts also need direct correction.

### Effort Estimate

- Planning/documentation correction: Medium
- Backlog and sprint reorganization: Medium
- Technical rework risk: Medium, depending on implementation already completed in Story 1.3 and UI assumptions

### Risk Assessment

- Main risk: implementation work in review may still encode auto-routing assumptions
- Secondary risk: API consumers and Playground behavior may diverge if contracts are not updated together
- Mitigation: update PRD, architecture, epic stories, and sprint-status as a single coordinated package

### Timeline Impact

- Short-term slowdown for artifact correction and backlog cleanup
- Medium-term simplification of implementation and lower ambiguity
- Net effect: acceptable if corrected before more stories are finalized

## 4. Detailed Change Proposals

### A. Stories

#### Story: 1.3 Ajouter le routage automatique de contexte métier
Section: Story title, intent, acceptance criteria

OLD:
- Story 1.3: Ajouter le routage automatique de contexte métier
- As an utilisateur sans expertise technique,
- I want que CoVeX detecte automatiquement le meilleur prompt métier quand je ne précise pas de contexte,
- So that j'obtienne une analyse pertinente sans configuration manuelle.

NEW:
- Story 1.3: Valider et résoudre un contexte métier explicitement fourni
- As an utilisateur ou intégrateur API,
- I want fournir un `profile_id` explicite et valide pour lancer l'analyse,
- So that CoVeX applique uniquement le contexte demandé sans inférence implicite.

Additional acceptance criteria updates:
- Missing `profile_id` returns `400`
- Unknown or inactive `profile_id` returns `404`
- Successful response includes `profile_used` equal to the requested context
- `routing_confidence` is removed from the contract

Rationale: The existing story directly conflicts with the new product rule and must be replaced, not merely edited.

#### Story: 2.3 Appliquer la résolution prompt vers modèle et paramètres provider
Section: Acceptance criteria

OLD:
- Resolution may happen manually or via routing

NEW:
- Resolution happens only from the explicitly requested prompt

Rationale: Model resolution must depend on explicit prompt selection only.

#### Story: 3.1 Construire le Playground de saisie et lancement d'analyse
Section: Acceptance criteria

OLD:
- Context selector offers explicit prompt or `Auto`
- `Auto` is the default value
- No `profile_id` is sent when `Auto` is used

NEW:
- Context selector is mandatory and has no `Auto` mode
- Analyze action stays blocked until a valid context is selected
- Every submit sends an explicit `profile_id`

Rationale: The UI must enforce the new mandatory product rule.

#### Story: 3.3 Afficher les détails techniques en mode opt-in
Section: Acceptance criteria

OLD:
- Show detected context and `routing_confidence` when available

NEW:
- Show `profile_used`, `model_used`, `latency_sec`, `tokens_in`, `tokens_out`
- Remove detected context and `routing_confidence`

Rationale: Technical transparency should match the actual system behavior.

#### Story: 4.2 Exposer la liste des profils d'analyse disponibles via API
Section: Priority / role in MVP

OLD:
- Nice-to-have utility endpoint

NEW:
- Operationally important endpoint for explicit context selection in UI and API integrations

Rationale: Prompt discovery becomes a primary enabler instead of a convenience.

### B. PRD

#### PRD Functional Requirements
Section: Functional Requirements - Analyse de Complétude (Core)

OLD:
- FR2: Spécifier un identifiant de contexte (flux/domaine/métier) pour orienter l'analyse
- FR3: Router automatiquement vers un prompt métier si aucun contexte n'est fourni
- FR16: Déterminer un contexte (...) et retourner un niveau de confiance
- FR17: Sélectionner automatiquement un prompt métier (...)
- FR18: Utiliser un modèle dédié pour le routage

NEW:
- FR2: Fournir un identifiant de contexte explicite et obligatoire pour exécuter une analyse
- FR3: Refuser toute analyse si aucun contexte explicite valide n'est fourni
- FR16: Valider que le contexte fourni correspond à un prompt actif connu
- FR17: Exposer les prompts disponibles pour permettre une sélection explicite
- FR18: Refuser toute analyse si le contexte demandé n'existe pas ou n'est pas actif

Rationale: The product moves from inferred context to explicit context validation.

#### PRD API Schema
Section: Request/Response `/analyze`

OLD:
- `profile_id` optional
- `biz_id` optional
- `routing_confidence` optional in response

NEW:
- `profile_id` required
- remove `biz_id` from MVP contract unless separately justified
- remove `routing_confidence`
- `profile_used` becomes the explicit prompt actually applied

Rationale: The API must encode the new contract unambiguously.

#### PRD Playground Scope
Section: Playground UI

OLD:
- Sélection du contexte (...) ou routage automatique
- Afficher le contexte détecté (si routage automatique utilisé)

NEW:
- Sélection explicite et obligatoire du contexte avant analyse
- Afficher le contexte sélectionné et appliqué

Rationale: The user experience must reflect explicit choice, not invisible automation.

### C. Architecture

#### Architecture Data Flow
Section: Main flow and API communication pattern

OLD:
- `input -> routage (optionnel) -> analyse -> scoring -> réponse structurée`

NEW:
- `input -> validation du contexte explicite -> chargement du prompt -> analyse -> scoring -> réponse structurée`

Rationale: Routing is removed from the system's target behavior.

#### Architecture Configuration
Section: Runtime configuration and directory structure

OLD:
- `.env` + YAML (`analysis_profiles.yaml`, `inference_engines.yaml`, `routing.yaml`)

NEW:
- `.env` + YAML (`analysis_profiles.yaml`, `inference_engines.yaml`)

Rationale: `routing.yaml` is no longer a valid target artifact.

#### Architecture API Contract
Section: `/analyze` schema and integration notes

OLD:
- Optional context, routing-derived fields allowed

NEW:
- Required `profile_id`
- `400` when missing
- `404` when unknown or inactive
- no routing-derived response fields

Rationale: API behavior becomes deterministic and externally controlled.

### D. UX / UI Specification

#### UX Core Interaction
Section: Core interaction and context selection

OLD:
- `Auto` is promoted as the default selector state
- user may analyze without explicit context selection

NEW:
- no `Auto` state
- initial selector state is empty and blocking
- helper text explains that context selection is required before analysis

Rationale: The UI should teach and enforce the new product behavior.

#### UX Journeys
Section: Journey diagrams and flow descriptions

OLD:
- Auto-detection appears in primary journeys

NEW:
- all journeys begin with explicit context choice or with upstream API caller-selected context

Rationale: Existing journey narratives currently normalize an invalid product behavior.

### E. Sprint Planning / Tracking

#### sprint-status.yaml
Section: development_status

OLD:
- `1-3-ajouter-le-routage-automatique-de-contexte-metier: review`

NEW:
- remove or replace with `1-3-valider-et-resoudre-un-contexte-metier-explicitement-fourni: backlog`
- review dependent stories for content alignment before acceptance

Rationale: Sprint tracking must not continue to validate obsolete scope.

## 5. Implementation Handoff

### Scope Classification

Moderate

This is not a full product reset, but it does require coordinated artifact updates, backlog correction, and review of in-flight implementation assumptions.

### Handoff Recipients

- Product Owner / Scrum Master
- Development team

### Responsibilities

#### Product Owner / Scrum Master

- Update epics and stories to remove routing scope
- Re-sequence Story 4.2 higher in delivery order
- Replace Story 1.3 and align dependent stories
- Update sprint-status tracking after approval

#### Development Team

- Remove routing assumptions from API, UI, and configuration implementation
- Enforce required explicit `profile_id`
- Remove `routing_confidence` and default-prompt behavior
- Review work already in `review` state for invalidated assumptions

### Success Criteria

- No artifact still describes automatic routing as target behavior
- `/analyze` requires explicit context in planning and implementation
- Playground blocks analysis until context is selected
- `/analysis-profiles` is positioned as the source of available contexts
- sprint planning no longer tracks obsolete routing work as valid scope

## Proposed Next Actions After Approval

1. Update PRD sections and FR catalog
2. Update architecture flow, configuration model, and API contract
3. Update epic/story definitions and replace Story 1.3
4. Update `sprint-status.yaml` to reflect approved change set
5. Route backlog reorganization to PO/SM and implementation cleanup to dev team
