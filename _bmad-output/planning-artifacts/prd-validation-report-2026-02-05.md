---
validationTarget: '/Users/jb/Documents/CoVeX/_bmad-output/planning-artifacts/prd.md'
validationDate: '2026-02-05T19:30:39+01:00'
inputDocuments:
  - /Users/jb/Documents/CoVeX/_bmad-output/planning-artifacts/prd.md
  - /Users/jb/Documents/CoVeX/_bmad-output/planning-artifacts/product-brief-CoVeX.md
  - /Users/jb/Documents/CoVeX/lm_models.py
  - /Users/jb/Documents/CoVeX/lm_inference_engines.yaml
  - /Users/jb/Documents/CoVeX/_bmad-output/planning-artifacts/covex-test-scenarios.yaml
  - /Users/jb/Documents/CoVeX/covex_test_runner.py
validationStepsCompleted:
  - step-v-01-discovery
  - step-v-02-format-detection
  - step-v-03-density-validation
  - step-v-04-brief-coverage-validation
  - step-v-05-measurability-validation
  - step-v-06-traceability-validation
  - step-v-07-implementation-leakage-validation
  - step-v-08-domain-compliance-validation
  - step-v-09-project-type-validation
  - step-v-10-smart-validation
  - step-v-11-holistic-quality-validation
  - step-v-12-completeness-validation
validationStatus: COMPLETE
holisticQualityRating: '4/5 - Good'
overallStatus: Warning
---

> Note 2026-03-14: artefact BMAD historique. Certaines references internes
> (tests, modules, `criteria`, hot reload, pages playground) peuvent ne plus
> correspondre exactement au depot courant. Pour l'etat actuel, se fier a
> `README.md`, `docs/ARCHITECTURE.md` et `docs/ANALYSIS_PROFILES_METIER.md`.


# PRD Validation Report

Note historique: ce rapport valide une version anterieure du PRD. La cible actuelle est supersedee par le changement approuve dans `/_bmad-output/planning-artifacts/sprint-change-proposal-2026-03-07.md`, avec suppression du routage automatique et contexte explicite obligatoire.

**PRD Being Validated:** /Users/jb/Documents/CoVeX/_bmad-output/planning-artifacts/prd.md
**Validation Date:** 2026-02-05T18:18:22+01:00

## Input Documents

- /Users/jb/Documents/CoVeX/_bmad-output/planning-artifacts/prd.md
- /Users/jb/Documents/CoVeX/_bmad-output/planning-artifacts/product-brief-CoVeX.md
- /Users/jb/Documents/CoVeX/lm_models.py
- /Users/jb/Documents/CoVeX/lm_inference_engines.yaml
- /Users/jb/Documents/CoVeX/_bmad-output/planning-artifacts/covex-test-scenarios.yaml
- /Users/jb/Documents/CoVeX/covex_test_runner.py

## Validation Findings

Les resultats sont presents dans les sections ci-dessous (Format Detection → Completeness Validation) ainsi que dans les addendums "Fixes Applied (Post-Validation)".

## Format Detection

**PRD Structure:**
- Executive Summary
- Success Criteria
- Product Scope
- User Journeys
- Functional Requirements
- Non-Functional Requirements
- Technical Architecture
- Profils d'analyse metier de Référence
- Validation & KPIs
- Innovation & Risks
- Implementation Priorities
- Glossaire

**BMAD Core Sections Present:**
- Executive Summary: Present
- Success Criteria: Present
- Product Scope: Present
- User Journeys: Present
- Functional Requirements: Present
- Non-Functional Requirements: Present

**Format Classification:** BMAD Standard
**Core Sections Present:** 6/6

## Information Density Validation

**Anti-Pattern Violations:**

**Conversational Filler:** 25 occurrences
- L368: "L'Utilisateur peut" - **FR1:** L'Utilisateur peut soumettre un texte libre pour analyse de complétude
- L369: "L'Utilisateur peut" - **FR2:** L'Utilisateur peut spécifier un identifiant de contexte (flux/domaine/métier) pour orienter l'analyse
- L370: "Le Système peut" - **FR3:** Le Système peut router automatiquement vers un prompt métier parmi les prompts disponibles si l'identifiant de contexte n'est pas fourni
- L371: "Le Système peut" - **FR4:** Le Système peut analyser un texte et produire un score de complétude (0-100)
- L372: "Le Système peut" - **FR5:** Le Système peut déterminer une décision basée sur le score (KO ≤30 / PARTIEL 31-70 / OK >70)
- L373: "Le Système peut" - **FR6:** Le Système peut générer une justification textuelle expliquant le score
- L396: "Le Système peut" - **FR15:** Le Système peut charger dynamiquement les prompts disponibles
- L400: "Le Système peut" - **FR16:** Le Système peut analyser un texte pour déterminer son contexte (type de demande)
- L401: "Le Système peut" - **FR17:** Le Système peut sélectionner automatiquement un prompt métier parmi les prompts disponibles selon le contexte détecté
- L402: "Le Système peut" - **FR18:** Le Système peut utiliser un modèle dédié pour le routage
- L414: "L'Utilisateur peut" - **FR22:** L'Utilisateur peut saisir un texte dans une zone de texte dédiée
- L415: "L'Utilisateur peut" - **FR23:** L'Utilisateur peut sélectionner un contexte (prompt métier) parmi les prompts disponibles OU laisser le routage automatique
- L416: "L'Utilisateur peut" - **FR24:** L'Utilisateur peut lancer une analyse via un bouton
- L417: "L'Utilisateur peut" - **FR25:** L'Utilisateur peut voir le score avec un indicateur visuel (couleur selon décision)
- L418: "L'Utilisateur peut" - **FR26:** L'Utilisateur peut voir la décision (KO/PARTIEL/OK)
- L419: "L'Utilisateur peut" - **FR27:** L'Utilisateur peut voir la justification textuelle
- L420: "L'Utilisateur peut" - **FR28:** L'Utilisateur peut voir le modèle utilisé pour l'analyse
- L421: "L'Utilisateur peut" - **FR29:** L'Utilisateur peut voir le prompt chargé (nom et contenu)
- L422: "L'Utilisateur peut" - **FR30:** L'Utilisateur peut voir la durée de l'inférence
- L423: "L'Utilisateur peut" - **FR31:** L'Utilisateur peut voir les compteurs de tokens (entrée et sortie)
- L424: "L'Utilisateur peut" - **FR32:** L'Utilisateur peut voir le contexte détecté (si routage automatique utilisé)
- L428: "Le Système peut" - **FR33:** Le Système peut communiquer avec un serveur Ollama local
- L429: "Le Système peut" - **FR34:** Le Système peut communiquer avec un serveur Ollama distant
- L430: "Le Système peut" - **FR35:** Le Système peut envoyer un prompt et recevoir une réponse du modèle
- L431: "Le Système peut" - **FR36:** Le Système peut mesurer les métriques d'inférence (durée, tokens)

**Wordy Phrases:** 0 occurrences

**Redundant Phrases:** 0 occurrences

**Total Violations:** 25

**Severity Assessment:** Critical

**Recommendation:**
"PRD requires significant revision to improve information density. Every sentence should carry weight without filler."

**Note (apres corrections):** Les FR33/FR34 et plusieurs NFRs ont ete generalises (moteur d'inference / provider cloud configurable). Relancer la validation pour obtenir une densite/leakage a jour.

## Product Brief Coverage

**Product Brief:** product-brief-CoVeX.md

### Coverage Map

**Vision Statement:** Fully Covered

**Target Users:** Fully Covered

**Problem Statement:** Fully Covered

**Key Features:** Fully Covered

**Goals/Objectives:** Fully Covered

**Differentiators:** Fully Covered

**Constraints:** Partially Covered
- Moderate gap: Le Product Brief explicite "architecture simple" (monolithique ou modulaire simple) n'apparait pas comme contrainte/guardrail explicite dans le PRD.
- Moderate gap: Le Product Brief insiste "eviter les API cloud externes" alors que le PRD mentionne OpenRouter en Nice-to-Have / post-MVP. A clarifier explicitement: opt-in, desactive par defaut, et posture de conformite/souverainete.

**Note (apres corrections):** Le PRD a ete modifie pour decrire un "provider cloud configurable (opt-in)" plutot que de citer un fournisseur.

### Coverage Summary

**Overall Coverage:** Elevee (tous les axes clefs couverts; contraintes partiellement explicitees)
**Critical Gaps:** 0
**Moderate Gaps:** 2 (contraintes)
**Informational Gaps:** 1 (persona "Integrateur API" ajoute par le PRD)

**Recommendation:**
"Consider addressing moderate gaps for complete coverage."

## Measurability Validation

### Functional Requirements

**Total FRs Analyzed:** 38

**Format Violations:** 0

**Subjective Adjectives Found:** 0

**Vague Quantifiers Found:** 0

**Implementation Leakage:** 11 (etat initial; PRD corrige ensuite)
- L385 (FR7): "SLM/LLM" + "via fichier YAML"
- L387 (FR9): noms de parametres (temperature, max_output_tokens, top_p, seed)
- L392 (FR11): "via fichiers YAML"
- L402 (FR18): "utiliser un modele dedie" (solution imposee vs capacite)
- L406 (FR19): details HTTP (endpoint `/analyze` via POST)
- L407 (FR20): details d'implementation/format (JSON + champs)
- L408 (FR21): details protocolaires (codes 400/404/500/503)
- L409 (FR37): endpoint `/health` via GET
- L410 (FR38): endpoint `/analysis-profiles` via GET
- L428 (FR33): technologie specifique (Ollama)
- L429 (FR34): technologie specifique (Ollama)

**FR Violations Total:** 11

### Non-Functional Requirements

**Total NFRs Analyzed:** 14 (etat initial; PRD corrige ensuite)

**Missing Metrics:** 14
- Exemple L439 (NFR1): "end-to-end" non borne (conditions, percentiles, definition start/stop)
- Exemple L441 (NFR3): "user-visible" non defini (protocole de mesure)
- Exemple L471 (NFR13): formulation subjective sans metrique testable

**Incomplete Template:** 14
- Toutes les NFRs manquent d'un contexte explicite et souvent d'une definition precise de la metrique/protocole

**Missing Context:** 14
- Les NFRs ne precisent pas systematiquement le pourquoi/qui/conditions d'execution

**NFR Violations Total:** 42

### Overall Assessment

**Total Requirements:** 51
**Total Violations:** 53

**Severity:** Critical

**Recommendation:**
"Many requirements are not measurable or testable. Requirements must be revised to be testable for downstream work."

## Traceability Validation

### Chain Validation

**Executive Summary → Success Criteria:** Gaps Identified
- Les differentiations "fond vs forme" et "cout (SLM gratuits)" ne sont pas directement mesurees comme criteres de succes.

**Success Criteria → User Journeys:** Gaps Identified
- Les criteres business (auditabilite, preservation du savoir, exploitation data) sont seulement implicites (principalement Journey GO via dashboard), sans chainage complet.
- La qualite d'evaluation (Pearson >= 0.80) et la stabilite sont des outcomes techniques, pas representes en parcours.

**User Journeys → Functional Requirements:** Gaps Identified
- Journey GO: "dashboard qualite", "notifications groupees", "marquage workflow Incomplet" ne sont pas couverts par des FR explicites (depend d'un systeme tiers, mais le contrat n'est pas specifie).
- Journeys ZAP/CIT/VOX mentionnent checklist/exemples; FR6 ne garantit que "justification" non structuree.

**Scope → FR Alignment:** Intact (avec un gap)
- OpenRouter mecanisme retire est mentionne en scope (Nice-to-Have / post-MVP) mais n'a pas de FR correspondant (seulement NFR14 detail).

### Orphan Elements

**Orphan Functional Requirements:** 0

**Unsupported Success Criteria:** 2
- Qualite d'evaluation: correlation Pearson >= 0.80
- Stabilite: fonctionnement sur machine standard sans ressources cloud

**User Journeys Without FRs:** 3 (elements)
- GO: dashboard qualite
- GO: notifications groupees
- GO: marquage workflow "Incomplet" (contrat d'integration non specifie)

### Traceability Matrix

- Couverture globale FR→Journeys: bonne (pas de FR orphelins)
- Points faibles: Journeys sur-promettent (dashboard/notifications/checklists) vs exigences; succes business/techniques manquent de mecanismes de mesure/trace dans les parcours.

**Total Traceability Issues:** 8

**Severity:** Warning

**Recommendation:**
"Traceability gaps identified - strengthen chains to ensure all requirements are justified."

## Implementation Leakage Validation

### Leakage by Category

**Playground Frameworks:** 0 violations

**Backend Frameworks:** 1 violation
- L465-L466 (NFR12): "FastAPI" (framework specifique) et "Swagger" (outil/UI specifique)

**Databases:** 0 violations

**Cloud Platforms:** 2 violations
- L479 (NFR14 detail): "OpenRouter" et reference provider/modele specifique (openrouter/mistral-7b)

**Infrastructure:** 0 violations

**Libraries:** 0 violations

**Other Implementation Details:** 8 violations
- L385 (FR7), L392 (FR11), L449 (NFR6), L457 (NFR9), L463 (NFR10), L464 (NFR11): "YAML" (format impose) / variables d'environnement (mecanisme) / audit `lm_inference_engines.yaml` (fichier specifique)
- L428-L429 (FR33-FR34), L456 (NFR8), L471 (NFR13): "Ollama" (runtime specifique)
- L465 (NFR12): endpoint fixe `/docs`
- L478-L479 (NFR14 detail): cles de config (mecanisme retire_model/cloud_mecanisme retire) et modeles (gemma3:4b)
- L456 (NFR8): "health check au demarrage + par requete" (strategie d'implementation)
- L448 (NFR5): "stateless" (jargon acceptable mais peut etre reformule en resultat: aucune persistence)

### Summary

**Total Implementation Leakage Violations:** 11 (etat initial; PRD corrige ensuite)

**Severity:** Critical

**Recommendation:**
"Extensive implementation leakage found. Requirements specify HOW instead of WHAT. Remove all implementation details - these belong in architecture, not PRD."

## Domain Compliance Validation

**Domain:** General / Productivite & Qualite de Donnees
**Complexity:** Low (general/standard)
**Assessment:** N/A - No special domain compliance requirements

**Note:** This PRD is for a standard domain without regulatory compliance requirements.

## Project-Type Compliance Validation

**Project Type:** API Backend + Web App

### Required Sections

**endpoint_specs:** Present
**auth_model:** Present
**data_schemas:** Present
**error_codes:** Present
**rate_limits:** Present
**api_docs:** Present
**browser_matrix:** Present
**responsive_design:** Present
**performance_targets:** Present
**seo_strategy:** Present
**accessibility_level:** Present

### Excluded Sections (Should Not Be Present)

N/A (project type maps to combined api_backend + web_app; no excluded sections applied)

### Compliance Summary

**Required Sections:** 11/11 present
**Excluded Sections Present:** 0 (should be 0)
**Compliance Score:** 100%

**Severity:** Pass

**Recommendation:**
"All required sections for this project type are present. No excluded sections found."

## SMART Requirements Validation

**Total Functional Requirements:** 38

### Scoring Summary

**All scores >= 3:** 94.7% (36/38)
**All scores >= 4:** 47.4% (18/38)
**Overall Average Score:** 4.04/5.0

### Scoring Table

| FR # | Specific | Measurable | Attainable | Relevant | Traceable | Average | Flag |
|------|----------|------------|------------|----------|-----------|--------|------|
| FR1 | 4 | 4 | 5 | 5 | 4 | 4.4 |  |
| FR2 | 4 | 3 | 5 | 5 | 4 | 4.2 |  |
| FR3 | 4 | 4 | 4 | 5 | 4 | 4.2 |  |
| FR4 | 5 | 5 | 4 | 5 | 5 | 4.8 |  |
| FR5 | 5 | 5 | 5 | 5 | 5 | 5.0 |  |
| FR6 | 4 | 4 | 4 | 5 | 4 | 4.2 |  |
| FR7 | 4 | 3 | 5 | 5 | 4 | 4.2 |  |
| FR8 | 4 | 3 | 5 | 5 | 4 | 4.2 |  |
| FR9 | 4 | 3 | 4 | 4 | 3 | 3.6 |  |
| FR10 | 4 | 3 | 4 | 5 | 4 | 4.0 |  |
| FR11 | 4 | 3 | 5 | 5 | 4 | 4.2 |  |
| FR12 | 3 | 3 | 5 | 5 | 4 | 4.0 |  |
| FR13 | 4 | 4 | 5 | 4 | 4 | 4.2 |  |
| FR14 | 4 | 4 | 4 | 4 | 4 | 4.0 |  |
| FR15 | 3 | 2 | 3 | 5 | 3 | 3.2 | X |
| FR16 | 3 | 2 | 4 | 5 | 3 | 3.4 | X |
| FR17 | 4 | 3 | 4 | 5 | 4 | 4.0 |  |
| FR18 | 3 | 3 | 4 | 4 | 3 | 3.4 |  |
| FR19 | 4 | 4 | 5 | 5 | 5 | 4.6 |  |
| FR20 | 4 | 4 | 4 | 5 | 5 | 4.4 |  |
| FR21 | 4 | 4 | 4 | 4 | 5 | 4.2 |  |
| FR22 | 4 | 4 | 5 | 4 | 4 | 4.2 |  |
| FR23 | 4 | 4 | 5 | 4 | 4 | 4.2 |  |
| FR24 | 4 | 4 | 5 | 4 | 4 | 4.2 |  |
| FR25 | 4 | 3 | 5 | 4 | 3 | 3.8 |  |
| FR26 | 4 | 4 | 5 | 4 | 4 | 4.2 |  |
| FR27 | 4 | 4 | 5 | 4 | 4 | 4.2 |  |
| FR28 | 4 | 4 | 5 | 4 | 4 | 4.2 |  |
| FR29 | 4 | 4 | 4 | 3 | 4 | 3.8 |  |
| FR30 | 4 | 4 | 5 | 4 | 4 | 4.2 |  |
| FR31 | 4 | 3 | 3 | 3 | 3 | 3.2 |  |
| FR32 | 4 | 3 | 4 | 4 | 3 | 3.6 |  |
| FR33 | 3 | 3 | 4 | 5 | 4 | 3.8 |  |
| FR34 | 3 | 3 | 4 | 4 | 3 | 3.4 |  |
| FR35 | 4 | 3 | 4 | 5 | 4 | 4.0 |  |
| FR36 | 4 | 3 | 4 | 4 | 4 | 3.8 |  |
| FR37 | 4 | 4 | 5 | 3 | 4 | 4.0 |  |
| FR38 | 4 | 4 | 5 | 4 | 4 | 4.2 |  |

**Legend:** 1=Poor, 3=Acceptable, 5=Excellent
**Flag:** X = Score < 3 in one or more categories

### Improvement Suggestions

**Low-Scoring FRs:**

**FR15:** "charger dynamiquement" est ambigu (quand? comment? quel SLA). Precisier le comportement observable (hot-reload vs au demarrage) + delai max + comportement en cas de YAML invalide.

**FR16:** "determiner le contexte" manque d'output attendu et de criteres de qualite. Ajouter `profile_used` + `routing_confidence` et une regle de mecanisme retire si confiance trop basse, plus une cible de qualite sur dataset de validation.

### Overall Assessment

**Severity:** Pass

**Recommendation:**
"Functional Requirements demonstrate good SMART quality overall."

## Holistic Quality Assessment

### Document Flow & Coherence

**Assessment:** Good

**Strengths:**
- Narratif clair (probleme → solution → scope → journeys → FR/NFR → arch → KPIs → risques)
- Journeys concrets et persuasifs (ZAP/GO/CIT/VOX/Configurateur/Integrateur)
- Format Markdown propre (tables, sections, schemas)

**Areas for Improvement:**
- Autorite/status incoherents (frontmatter "status: complete" vs tableau PRD "Status: Draft")
- Definitions/gates disperses (latence: <2s vs AC FR4 <10s vs KPI-003)
- Mix narration (exemples) vs exigences normatives (risque de sur-promesse)

### Dual Audience Effectiveness

**For Humans:**
- Executive-friendly: Excellent
- Developer clarity: Good (mais AC incomplete)
- Designer clarity: Good
- Stakeholder decision-making: Good

**For LLMs:**
- Machine-readable structure: Good (IDs, headers)
- UX readiness: Good (journeys riches)
- Architecture readiness: Good (stack + interfaces)
- Epic/Story readiness: Adequate (traceabilite + AC manquants)

**Dual Audience Score:** 3.5/5

### BMAD PRD Principles Compliance

| Principle | Status | Notes |
|-----------|--------|-------|
| Information Density | Partial | FRs repetitifs + quelques formulations "peut"; narratif utile mais non separe du normatif |
| Measurability | Partial | KPIs presentes, mais plusieurs definitions/protocoles manquent; gates incoherents |
| Traceability | Partial | IDs ok, mais matrix Journey→FR/NFR→KPI absente; certains elements de journeys non couverts |
| Domain Awareness | Met | Domaine general; bonnes considerations local-first/sovereignty |
| Zero Anti-Patterns | Partial | Implementation leakage notable + incoherences de statut |
| Dual Audience | Partial | Humain tres bon; couche machine-first a renforcer |
| Markdown Format | Met | Structure stable et exploitable |

**Principles Met:** 2/7

### Overall Quality Rating

**Rating:** 4/5 - Good

**Scale:**
- 5/5 - Excellent: Exemplary, ready for production use
- 4/5 - Good: Strong with minor improvements needed
- 3/5 - Adequate: Acceptable but needs refinement
- 2/5 - Needs Work: Significant gaps or issues
- 1/5 - Problematic: Major flaws, needs substantial revision

### Top 3 Improvements

1. **Ajouter une matrice de traceabilite**
   Lier explicitement Journey/Capability → FR/NFR → KPI → tests (ex: `covex-test-scenarios.yaml`) pour auditabilite et extraction LLM.

2. **Canonicaliser les metriques et gates MVP**
   Definir une seule source de verite pour latence/routage/qualite (seuil vs cible vs excellent) et aligner FR/AC/NFR/KPI.

3. **Separer "exemples" vs "normatif" + corriger l'autorite du document**
   Ajouter une section "Normative Requirements (MVP)" (MUST/SHOULD + AC complets) et rendre coherent le statut PRD (Draft vs Complete) en deplacant le frontmatter workflow si besoin.

### Summary

**This PRD is:** solide et convaincant pour des humains, et proche d'etre "audit-grade" une fois la couche mesurable/traceable/anti-leakage durcie.

**To make it great:** Focus on the top 3 improvements above.

## Completeness Validation

### Template Completeness

**Template Variables Found:** 0
No template variables remaining ✓

### Content Completeness by Section

**Executive Summary:** Incomplete
- Vision explicite existe plutot dans `## Product Scope` (Vision Phase 3+), pas formulee comme "vision statement" dans l'Executive Summary.

**Success Criteria:** Incomplete
- Plusieurs criteres restent vagues (ex: "Mesurable (baseline → post-CoVeX)", "utiles et actionnables") sans protocole de mesure.

**Product Scope:** Complete

**User Journeys:** Complete

**Functional Requirements:** Complete

**Non-Functional Requirements:** Incomplete
- Presence de targets, mais definitions/protocoles de mesure souvent incomplets.

### Section-Specific Completeness

**Success Criteria Measurability:** Some measurable

**User Journeys Coverage:** Yes - covers all user types

**FRs Cover MVP Scope:** Yes

**NFRs Have Specific Criteria:** Some

### Frontmatter Completeness

**stepsCompleted:** Present
**classification:** Present
**inputDocuments:** Present
**date:** Missing (aucun champ `date:`; `completedAt` existe)

**Frontmatter Completeness:** 3/4

### Completeness Summary

**Overall Completeness:** 80% (Warning)

**Critical Gaps:** 0
**Minor Gaps:** 3 (notation d'accolades interpretable comme placeholders; `date` manquant en frontmatter; sections Success/NFR partiellement mesurables)

**Severity:** Warning

**Recommendation:**
"PRD has minor completeness gaps. Address minor gaps for complete documentation."

## Fixes Applied (Post-Validation)

AppliedAt: 2026-02-05T18:51:08+01:00

### Fix Set 2: Implementation Leakage (FR/NFR)

- Generalise les mentions de technologie/format dans `## Functional Requirements` et `## Non-Functional Requirements` (ex: YAML/Ollama/OpenRouter/FastAPI/Swagger) en formulations "capability".
- Conserve l'intention (API contract, mecanisme retire, doc OpenAPI), sans imposer de framework/provider dans les exigences.

### Fix Set 1: Authority/Status Alignment

- Aligne le tableau PRD (Status) avec le frontmatter workflow: `Status: Complete`.
- Ajoute `date: 2025-01-31` en frontmatter pour completer les metadonnees.
- Remplace "Modification YAML uniquement" par "Modification de configuration uniquement" dans Success Criteria (Configurateur).

### Fix Set 3: FR15 / FR16 Measurability

- FR15: reformule pour etre observable (prise en compte des changements sans redemarrage).
- FR16: definit un output mesurable (`profile_used`, `routing_confidence`) + regle de mecanisme retire.
- Ajoute des criteres d'acceptation pour FR15 et FR16 dans la table AC.

**Note:** Les severites/compteurs dans ce rapport (density/measurability/leakage/SMART/completeness) refletent l'etat AVANT ces correctifs. Pour des chiffres a jour, relancer la validation.

AdditionalAppliedAt: 2026-02-05T18:53:21+01:00

- PRD: remplace les notations d'API en accolades dans la table des endpoints (evite confusion "template placeholders").
- Rapport: corrige un caractere parasite dans les lignes "All scores >= ...".

AdditionalAppliedAt: 2026-02-05T19:01:48+01:00

- PRD: neutralise les mentions de techno/format hors exigences (YAML/Ollama/OpenRouter/FastAPI/Swagger) en les remplacant par des formulations generiques.
- PRD: ajoute une phrase de vision explicite dans `## Executive Summary`.

AdditionalAppliedAt: 2026-02-05T19:02:30+01:00

- Rapport: supprime le placeholder "[Findings will be appended as validation progresses]".

AdditionalAppliedAt: 2026-02-05T19:03:51+01:00

- Rapport: met a jour quelques sections pour refleter les corrections PRD (FR count, note post-fix, et template placeholders).

AdditionalAppliedAt: 2026-02-05T19:09:46+01:00

- PRD: ajoute une section "Reference implementation (MVP)" et deplace les choix techno hors des exigences.
- PRD: neutralise les mentions techno restantes hors exigences (NiceGUI/Podman/Traefik/Python 3.14/gemma3:1b) en les releguant a la reference.
- PRD: densifie la formulation des FRs (suppression des "L'Utilisateur peut / Le Systeme peut").
- Rapport: ajoute une section de revalidation post-fix (density/leakage/SMART/completeness).

AdditionalAppliedAt: 2026-02-05T19:24:59+01:00

- PRD: aligne le gate de performance FR4 sur la cible MVP/NFR1 (AC FR4 < 2s au lieu de < 10s).

AdditionalAppliedAt: 2026-02-05T19:30:39+01:00

- PRD: harmonise la typographie (accents) et ajoute une table unique "Performance gates" (Seuil/Cible/Stretch) comme source de verite.
- Rapport: met a jour la revalidation full post-fix (performance gate resolved; severites a jour).

## Revalidation (Post-Fix)

RevalidatedAt: 2026-02-05T19:30:39+01:00

### Quick Results (Post-Fix)

- Information Density: Pass (0 occurrences "L'Utilisateur peut" / "Le Systeme peut" dans les FRs)
- Implementation Leakage (FR/NFR): Pass (0 violations techno/framework/provider)
- SMART Quality (FRs): Warning
  - Total FRs: 38
  - All scores >= 3: 81.6% (31/38)
  - All scores >= 4: 55.3% (21/38)
  - Overall average: 4.13/5.0
  - Flagged FRs: FR2, FR9, FR18, FR31, FR33, FR34, FR35
- Completeness: Pass (template placeholders: 0; frontmatter keys present)

**Note:** Les sections Measurability/Traceability/Project-Type/Holistic ci-dessus restent des constats historiques (etat initial). Une revalidation complete (toutes les etapes) est necessaire pour recalculer l'ensemble des severites.

## Revalidation (Full, Post-Fix)

RevalidatedAt: 2026-02-05T19:30:39+01:00

### Updated Severities

- Information Density: Pass
- Product Brief Coverage: Pass
- Measurability (FRs & NFRs): Warning
- Traceability: Warning
- Implementation Leakage: Warning
- Project-Type Compliance (api_backend + web_app): Pass
- Holistic Quality: 4/5 - Good
- Completeness: Pass

### Critical Issues (Post-Fix)

- None
