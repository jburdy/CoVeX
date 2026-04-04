---
stepsCompleted: [1, 2, 3, 4, 5]
inputDocuments:
  - _instructions/Proposition_Officielle.md
  - docs/ARCHITECTURE.md
date: 2026-01-31
author: JBU
---

# Product Brief: CoVeX

> Note de lecture pour le rapport final (mise à jour dépôt 2026-03-07) : ce brief documente surtout la vision et les hypothèses de depart. L'artefact effectivement versionne a depuis ete simplifie et recentre : selection explicite du `profile_id`, absence de routage automatique en production, configuration de providers locaux et distants, et benchmark SLM/LLM traite comme outillage annexe plutot que comme coeur du prototype.

<!-- Content will be appended sequentially through collaborative workflow steps -->

## Executive Summary

CoVeX (Complétude Vérification eXpert) s'attaque au problème de la dette informationelle dans les entreprises : l'accumulation de données non structurées inévitable et incomplètes qui entrave les opérations, le pilotage et la préservation du savoir. CoVeX est une solution souveraine utilisant des SLM (Small Language Models) pour analyser, scorer et améliorer la complétude des textes libres. Elle offre une approche modulaire (du simple scoring invisible à l'assistance active) adaptée aux PME soucieuses de la confidentialité et des coûts, permettant aux managers de définir eux-mêmes leurs critères de qualité via des profils d'analyse métier spécifiques.

---

## Core Vision

### Problem Statement

Les zones de texte libre (tickets, rapports, notes, mémos) souffrent souvent d'un manque de fond et de contexte ("lazy writing"), créant une dette qui se paie cher : perte de temps opérationnel pour clarifier, impossibilité de créer des dashboards fiables, et perte irréversible de connaissance en l'absence des collaborateurs.

### Problem Impact

Inefficience opérationnelle (allers-retours), perte de capital informationnel, et blocage des initiatives data (RAG, Analytics) faute de données de qualité.

### Why Existing Solutions Fall Short

Les correcteurs classiques gèrent la forme, pas le fond. Les LLM cloud posent des problèmes de confidentialité, de coût et manquent souvent du contexte métier spécifique nécessaire pour juger de la "complétude".

### Proposed Solution

Un moteur d'analyse qui évalue (score) la complétude des textes selon des critères métier définis par l'utilisateur. Il agit de manière flexible : soit comme un indicateur passif de qualité pour les processus avals, soit comme un assistant actif alertant le rédacteur en cas de score insuffisant.

### Key Differentiators

Utilisation de SLM (efficience, coût, local), souveraineté des données, et une architecture "User Prompt" permettant aux métiers de définir eux-mêmes ce qu'est un texte "complet" pour leur contexte spécifique.

---

## Target Users

### Primary Users

#### Contexte Entreprise (Support IT & Interne)
*   **GO - "Le Terrain"** 🔧 : Technicien support/intervention qui enchaîne les missions. Le reporting est secondaire face à l'action. CoVeX agit en arrière-plan sans le bloquer, marquant le ticket/CR comme "Incomplet" pour le workflow aval. → *Domaine : Tickets Support IT & Comptes-Rendus d'Intervention*
*   **VOX - "Le Communicant"** 🎙️ : Chef de projet ou manager dont la force est l'échange oral. Ses écrits manquent parfois de contexte car l'essentiel passe par la conversation. CoVeX l'aide à capturer ce savoir tacite. → *Domaine : Comptes-Rendus, Notes de suivi*
*   **ZAP - "Le Direct"** ➡️ : Demandeur interne qui va droit au but. Préfère un retour immédiat et constructif ("élément X à préciser") plutôt qu'un délai d'attente. CoVeX lui offre un feedback instantané. → *Domaine : Demandes d'Achat, Tickets Support IT (en tant que demandeur)*
*   **NEW - "Le Découvreur"** 🔍 : Nouvel utilisateur ou client externe qui navigue dans un environnement nouveau. A besoin d'un guidage bienveillant pour savoir quelles informations fournir. CoVeX l'accompagne dans sa prise en main. → *Domaine : Demandes via portail externe, Premiers contacts*

#### Contexte Communes (Service Public)
*   **CIT - "Le Citoyen"** 🏠 : Habitant effectuant une démarche administrative (déménagement, urbanisme, signalement voirie, demande de document...). Souvent peu familier avec les procédures, il a besoin d'un guidage clair sur les pièces à fournir. CoVeX l'aide à constituer un dossier complet dès le premier envoi. → *Domaine : Demandes Citoyennes, Signalements, Démarches administratives*

#### Contexte Construction (BTP)
*   **MOA - "Le Maître d'Ouvrage"** 🏗️ : Client particulier ou professionnel avec un projet de construction/rénovation (extension, devis, permis...). Exprime son besoin mais manque souvent de précisions techniques. CoVeX l'aide à formuler une demande exploitable par l'entreprise. → *Domaine : Demandes de Devis, Projets Construction*
*   **OPS - "L'Opérationnel"** 🛠️ : Chef de chantier ou conducteur de travaux documentant l'avancement terrain. Pris par l'action, ses rapports sont parfois trop succincts. CoVeX garantit une traçabilité complète pour le suivi de projet. → *Domaine : Rapports de Chantier, Journaux de bord terrain*

### Secondary Users

*   **L'Expert Métier / Manager (Le Configurateur)** : Définit les critères de complétude via les "User Prompts" en langage naturel.


### User Journey

1.  **Saisie** : L'utilisateur (GO/VOX/ZAP/NEW/CIT/MOA/OPS) remplit un champ texte libre (ticket, demande, rapport, formulaire citoyen, devis...).
2.  **Analyse** : Le moteur CoVeX évalue le texte via un prompt métier adapté au contexte (IT, Communes, Construction).
3.  **Mode "Assistance" (synchrone)** : Pour **ZAP/NEW/CIT/MOA**, retour immédiat (score + justification) pour corriger instantanément.
4.  **Mode "Scoring" (asynchrone)** : Pour **GO/VOX/OPS**, CoVeX ne bloque pas la saisie; il marque le contenu comme "Incomplet" et alimente le workflow aval (tri, priorité, contrôle qualité, relance).
5.  **Résultat** : La donnée est exploitable dès sa création (Dashboard, RAG) et la qualité devient pilotable.

---

## Success Metrics

*   **Réduction des Itérations de Clarification (User Success)** : Diminution drastique du nombre d'allers-retours (emails/téléphones) nécessaires entre le rédacteur (GO/VOX) et l'exécutant pour compléter un dossier. L'objectif est le "First Time Right".
*   **Accélération du Temps de Traitement (User Success)** : Pour **ZAP**, passage d'un délai de rejet de plusieurs jours (traitement humain) à un rejet instantané constructif (secondes), permettant une soumission valide dans la foulée.

### Business Objectives

*   **Auditabilité de la Qualité (Data Quality)** : Le "Score de Complétude" devient une métrique d'entreprise fiable et suivie. L'objectif est d'atteindre un niveau de qualité permettant l'exploitation directe des données (Dashboards, RAG) sans nettoyage manuel préalable.
*   **Préservation du Savoir** : Augmentation de la richesse contextuelle des tickets fermés, rendant le capital informationnel de l'entreprise indépendant des départs individuels.

### Key Performance Indicators

*   **Qualité d'évaluation** : Concordance élevée entre le score attribué par CoVeX et une évaluation de référence (expert humain / grille métier) sur la vérification de complétude (ex: corrélation élevée sur un score 0-100, ou précision élevée sur une décision "OK/KO").
*   **Latence d'Inférence** : Le temps d'analyse par le SLM local doit être compatible avec l'expérience utilisateur (quelques secondes max), tout en garantissant la souveraineté (0 donnée envoyée au cloud).
*   **Taux de Complétude Moyen** : Progression mesurable du score moyen des saisies (tickets/demandes) sur la période pilote.

---

## MVP Scope

### Core Features

*   **Moteur d'Analyse Locale (SLM Core)** : Intégration et orchestration d'un modèle de langage léger (type Mistral/Qwen/Gemma) tournant localement.
*   **API de Complétude** : Interface REST/JSON permettant d'envoyer un texte et de recevoir en retour un score (0-100), une décision à trois niveaux (KO ≤30 / PARTIEL 31-70 / OK >70), et une justification.
*   **Gestion des Profils d'analyse métier** : Système permettant de définir et charger des "User Prompts" spécifiques.
*   **Playground UI** : Interface web légère permettant de tester le moteur et de visualiser les résultats.
*   **Consommation Modulaire** : Possibilité d'utiliser le service en mode "scoring only", "détection + justification" ou "filtrage/assistance" selon le contexte d'intégration.

### Out of Scope for MVP

*   **Intégrations Natives** : Pas de plugins directs pour des outils tiers.
*   **Fine-tuning de Modèles** : Utilisation de modèles "off-the-shelf" optimisés via le prompting uniquement.

### MVP Success Criteria

*   **Démonstration Fonctionnelle** : Capacité à traiter avec succès 5 cas d'usage couvrant 3 secteurs :
    
    **Secteur Entreprise (IT/Interne) :**
    1. **Tickets Support IT** (personas GO rédacteur, ZAP demandeur, NEW nouvel arrivant)
    2. **Demandes d'Achat** (personas ZAP, NEW)
    3. **Comptes-Rendus d'Intervention/Projet** (personas GO, VOX)
    
    **Secteur Communes (Service Public) :**
    4. **Demandes Citoyennes** (persona CIT) — déménagement, urbanisme, signalements...
    
    **Secteur Construction (BTP) :**
    5. **Demandes de Devis / Rapports Chantier** (personas MOA, OPS)
    
*   **Validation Métier** : Résultats jugés utiles et actionnables par un évaluateur métier (score + justification) sur un jeu d'exemples.
*   **Stabilité Locale** : Fonctionnement sur une machine standard sans ressources cloud.

### Future Vision

*   **Standardisation MCP** : Implémentation du Model Context Protocol.
*   **Reformulation Active** : Proposition automatique de correction intégrée.
*   **Auto-apprentissage** : Amélioration des critères basée sur les feedbacks réels.

---

## Project Constraints & Compliance

### Project Directives (CoVeX)

*   **Souveraineté des données** : Priorité au local; éviter les API cloud externes.
*   **SLM d'abord** : Favoriser des modèles légers locaux, optimisés par prompting.
*   **Architecture simple** : Prototype monolithique ou modulaire simple.
*   **Formats de sortie imposés** : `score + decision + justification`.

---

## Deliverables (From Project Proposal)

*   **Prototype logiciel** : moteur local + API + UI de playground.
*   **Rapport technique** : architecture et retour d'experience sur BMad/Vibe Coding.
