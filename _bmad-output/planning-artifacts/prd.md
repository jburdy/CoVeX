---
stepsCompleted:
  - step-01-init
  - step-02-discovery
  - step-03-success
  - step-04-journeys
  - step-05-domain
  - step-06-innovation
  - step-07-project-type
  - step-08-scoping
  - step-09-functional
  - step-10-nonfunctional
  - step-11-polish
  - step-12-complete
status: complete
completedAt: 2025-01-31
date: 2025-01-31
inputDocuments:
  - _bmad-output/planning-artifacts/product-brief-CoVeX.md
  - _instructions/Proposition_Officielle.md
  - docs/ARCHITECTURE.md
  - _bmad-output/planning-artifacts/covex-test-scenarios.yaml
  - tests_benchs/covex_test_runner.py
  - tests_benchs/benchmark_run.py
documentCounts:
  briefs: 1
  research: 0
  brainstorming: 0
  projectDocs: 6
workflowType: 'prd'
projectType: 'greenfield'
classification:
  projectType: 'API Backend + Web App'
  domain: 'Général / Productivité & Qualité de Données'
  complexity: 'medium'
  projectContext: 'greenfield'
  characteristics:
    deployment: 'cloud-ready (container ou venv local)'
    modelStrategy: 'SLM-first, LLM-capable'
    configuration: 'fichier de configuration (changement modèle sans code)'
    dataSovereignty: 'local-first, cloud en option'
    targetHardware: 'MacBook Air M4 32GB'
---

> Note 2026-03-14: artefact BMAD historique. Certaines références internes
> (tests, modules, `criteria`, hot reload, pages playground) peuvent ne plus
> correspondre exactement au dépôt courant. Pour l'état actuel, se fier a
> `README.md`, `docs/ARCHITECTURE.md` et `docs/ANALYSIS_PROFILES_METIER.md`.


# Product Requirements Document - CoVeX

> Note de lecture pour le rapport final (mise à jour dépôt 2026-03-07) : ce PRD capture le périmètre cible et plusieurs hypothèses initiales. Pour decrire l'artefact reel, il faut le confronter a `docs/ARCHITECTURE.md`, au code et aux tests. Les ecarts les plus structurants du dépôt actuel sont le `profile_id` explicite, l'absence de routage automatique dans le flux nominal, et une implementation centree sur un prototype backend/playground simple plutot que sur un benchmark SLM/LLM comme livrable principal.

**Complétude Vérification eXpert**

| Attribut | Valeur |
|----------|--------|
| **Author** | JBU |
| **Date** | 2025-01-31 |
| **Version** | 1.0 - MVP |
| **Status** | Complete |

## Executive Summary

### Le Problème

Les organisations accumulent une dette informationelle invisible : tickets incomplets, demandes vagues, comptes-rendus inexploitables. Cette dette génère des allers-retours coûteux, une perte de contexte, et des données inutilisables pour l'IA/analytics.

### La Solution

**CoVeX** est un moteur d'analyse de "complétude" des textes libres. Il utilise des Small Language Models (SLM) locaux pour évaluer si un texte contient les informations nécessaires à son traitement, et guide l'utilisateur vers une version exploitable.

### Vision

Rendre chaque texte libre actionnable dès la première soumission, via une évaluation de complétude configurable, local-first, et intégrable facilement.

### Différenciateur Clé

| Aspect | Solutions existantes | CoVeX |
|--------|---------------------|-------|
| **Focus** | Forme (grammaire, style) | **Fond** (informations présentes) |
| **Souveraineté** | Cloud obligatoire | **100% local possible** |
| **Adaptation** | Générique | **Configurable par métier** (configuration) |
| **Coût** | API payantes | **SLM gratuits** |

### Hypothèse à Valider (MVP)

> *"Un SLM local (1-4B paramètres) peut-il juger efficacement la complétude d'un texte métier ?"*

### Cibles MVP

- **Latence** : < 5 secondes sur MacBook M4
- **Validation** : 6 cas d'usage sur 3 secteurs (Enterprise, Communes, BTP)
- **Qualité** : Scores jugés "cohérents" par évaluateur métier

## Success Criteria

### User Success

| Persona | Critère de Succès | Cible |
|---------|-------------------|-------|
| **GO/VOX** (Terrain/Communicant) | Réduction des allers-retours de clarification | **-50%** (baseline: moyenne 3.2 itérations/demande avant CoVeX) |
| **ZAP** (Direct) | Feedback immédiat vs attente humaine | **< 1 heure** (vs 5 jours) |
| **NEW/CIT/MOA** (Découvreurs) | Guidage constructif dès la première soumission | Justification claire fournie |
| **Configurateur** | Changement de modèle/prompt sans code | Modification de configuration uniquement |

**Moment "Aha!"** : L'utilisateur reçoit un feedback actionnable (score + justification) avant même qu'un humain n'ait vu sa demande.

### Business Success

| Objectif | Métrique | Cible MVP |
|----------|----------|-----------|
| **Auditabilité** | Score de Complétude disponible comme métrique | 100% des textes analysés scorés |
| **Préservation du savoir** | Richesse contextuelle des tickets | Mesurable (baseline → post-CoVeX) |
| **Exploitation data** | Données exploitables sans nettoyage manuel | Dashboards/RAG alimentables directement |

### Technical Success

| Critère | Cible MVP |
|---------|-----------|
| **Latence d'inférence** | **1-5 secondes** (MacBook M4) |
| **Souveraineté** | **0 donnée cloud** en mode local par défaut |
| **Qualité d'évaluation** | Corrélation avec évaluation humaine ≥ 0.80 (Pearson) |
| **Stabilité** | Fonctionnement sur machine standard sans ressources cloud |

### Measurable Outcomes

- **Pilote** : 6 cas d'usage validés sur 3 secteurs (Enterprise, Communes, BTP)
- **Validation métier** : Résultats jugés "utiles et actionnables" par évaluateur expert
- **Performance** : Latence < 5 sec sur hardware cible

## Product Scope

### MVP - Minimum Viable Product

**Moteur Core :**
- Analyse de complétude via SLM local
- API REST/JSON : `POST /analyze` → score + décision + justification
- Consommation modulaire : une intégration peut n'utiliser que `score`/`decision` (sans afficher la justification) tout en conservant le même endpoint
- Configuration des modèles et profils d'analyse métier via fichiers de configuration
- Support d'un moteur d'inférence local ou distant

**Playground UI :**
- Saisie d'un texte à analyser (exemples proposés)
- Sélection explicite et obligatoire du contexte (prompt métier)
- Affichage du scoring complet (score, décision, justification)
- Détails techniques (modèle, durée, tokens in/out, prompt chargé)

**Nice-to-Have MVP (si temps disponible) :**
- API `/health` (monitoring)
- API `/analysis-profiles` (liste des profils d'analyse disponibles)
- Support d'un provider cloud configurable (mécanisme de secours (fallback))

**Hors scope MVP :**
- Mode Batch (analyse en lot)
- Interface web de création/édition des prompts
- Intégrations natives (plugins tiers)
- Fine-tuning de modèles
- MCP / gRPC

### Growth Features (Phase 2)

- Mode Batch (analyse en lot, exécution nuit/off-peak)
- Support d'un provider cloud configurable (mécanisme de secours (fallback) transparent)
- API `/health` et `/analysis-profiles`
- Interface web pour Configurateurs (création prompts sans édition manuelle de fichiers)
- Dashboards de suivi qualité temps réel

### Vision (Phase 3+)

- Intégrations natives (ITSM, ticketing, CRM)
- MCP (Model Context Protocol)
- gRPC (si pertinent)
- Reformulation active (proposition automatique de correction)
- Auto-apprentissage (amélioration via feedbacks réels)
- Multi-modèles par contexte explicitement sélectionné

## User Journeys

### Journey 1 : ZAP - Le Direct (Mode Assistance Synchrone)

**Persona :** Marc, 42 ans, responsable logistique dans une PME industrielle. Pragmatique, efficace, déteste perdre du temps.

**Scène d'ouverture :**
Marc doit commander en urgence des pièces de rechange pour une machine en panne. Il ouvre le portail de demandes d'achat et tape rapidement : *"Besoin roulements pour machine atelier, urgent."*

**Action montante :**
En moins de 2 secondes, CoVeX analyse sa demande. Le score s'affiche : **35/100 - PARTIEL**. 

La justification apparaît : *"Demande incomplète : référence exacte des roulements non précisée, quantité souhaitée absente, budget estimé non indiqué, délai souhaité manquant."*

Marc comprend immédiatement. En 30 secondes, il complète : *"Commande de 4 roulements SKF 6205-2RS pour presse hydraulique HYDR-003 atelier 2. Budget max 150€ HT. Livraison express souhaitée sous 48h - production bloquée."*

Nouveau score : **92/100 - OK**. Sa demande part directement au service achats.

**Résolution :**
Au lieu d'attendre 3 jours qu'un acheteur lui renvoie un email "Merci de préciser la référence", Marc a soumis une demande exploitable en moins de 2 minutes. La commande est passée le jour même.

**Capabilities révélées :** Analyse temps réel, feedback instantané, exemples contextuels, scoring visible.

---

### Journey 2 : GO - Le Terrain (Mode Scoring Asynchrone)

**Persona :** Sophie, 28 ans, technicienne support IT niveau 2. Enchaîne les interventions, toujours entre deux tickets.

**Scène d'ouverture :**
Sophie vient de résoudre un problème d'imprimante réseau. Entre deux interventions, elle ferme le ticket rapidement : *"Imprimante remise en service. Problème réseau."*

**Action montante :**
Sophie passe au ticket suivant sans attendre. En arrière-plan, CoVeX analyse son compte-rendu : **28/100 - KO**.

Dans le workflow (système tiers), le ticket est marqué "Incomplet". Le score/décision/justification sont stockés par le système tiers (CoVeX reste stateless et ne persiste pas le texte analysé) : *"CR insuffisant pour capitalisation. Manque : diagnostic précis, actions réalisées, cause racine, temps passé."*

**Climax :**
En fin de journée, le superviseur consulte le dashboard qualité. Il voit que 3 tickets de Sophie sont marqués "Incomplets" avec leurs justifications. Il lui envoie une notification groupée.

Sophie prend 10 minutes pour enrichir ses 3 CR : *"Imprimante HP LaserJet Pro M404 (IP 192.168.1.45) inaccessible. Diagnostic : câble réseau défectueux sur switch baie 2 port 12. Action : remplacement câble Cat6. Test impression OK. Durée : 25min."*

**Résolution :**
Sophie n'a pas été bloquée dans son travail terrain. Le feedback arrive en différé, au moment opportun. Les tickets enrichis alimentent désormais la base de connaissances pour les futurs diagnostics similaires.

**Capabilities révélées :** Scoring asynchrone, marquage workflow, dashboard qualité, notifications groupées, non-blocage utilisateur.

---

### Journey 3 : CIT - Le Citoyen (Mode Assistance Guidée)

**Persona :** Fatima, 35 ans, habitante qui déménage dans une nouvelle commune. Peu familière avec les démarches administratives en ligne.

**Scène d'ouverture :**
Fatima doit signaler son changement d'adresse pour les listes électorales. Elle trouve le formulaire en ligne et écrit : *"Je déménage, merci de mettre à jour mon adresse."*

**Action montante :**
CoVeX analyse sa demande : **22/100 - KO**.

Un message bienveillant s'affiche : *"Votre demande nécessite quelques précisions pour être traitée. Voici ce qu'il nous faut :"*
- Votre nom complet
- Ancienne adresse
- Nouvelle adresse complète
- Date du déménagement
- Pièce justificative (facture, bail...)

Un exemple est proposé : *"Je soussignée Marie DUPONT, actuellement inscrite au 12 rue des Lilas 75020 Paris, souhaite signaler mon déménagement au 8 avenue Victor Hugo 69003 Lyon à compter du 15 février 2025. Ci-joint mon nouveau bail."*

**Climax :**
Fatima comprend ce qu'on attend d'elle. Elle complète sa demande avec toutes les informations et joint son bail. Score : **88/100 - OK**.

**Résolution :**
Sa demande est complète dès le premier envoi. Pas de courrier de relance 3 semaines plus tard, pas de coup de fil au service concerné. Elle reçoit sa confirmation d'inscription sous 5 jours.

**Capabilities révélées :** Guidage bienveillant, liste de pièces requises, exemples adaptés au contexte public.

---

### Journey 4 : Configurateur (Setup des Profils d'analyse métier)

**Persona :** Thomas, 45 ans, responsable qualité IT. Doit définir ce qu'est un "bon" ticket de support pour son équipe.

**Scène d'ouverture :**
Thomas veut que CoVeX évalue les tickets selon les critères qualité de son service. Il ouvre le fichier `prompts/ticket-support-it`.

**Action montante :**
Il rédige son prompt métier en langage naturel :
```text
name: ticket-support-it
description: Evaluation des tickets support IT niveau 1-2
criteria:
  - Description claire du probleme rencontre
  - Environnement technique (OS, application, version)
  - Etapes de reproduction si applicable
  - Impact utilisateur (bloquant/genant/mineur)
  - Actions deja tentees par l'utilisateur
```

**Climax :**
Thomas ouvre le Playground, selectionne son nouveau prompt, et teste avec un vrai ticket de sa base. Il voit le score, la justification, et ajuste ses criteres jusqu'a obtenir une evaluation coherente avec son expertise.

**Resolution :**
En 30 minutes, Thomas a configure CoVeX pour son contexte metier specifique. Pas de developpement, pas de ticket a l'IT. Demain, tous les tickets de son equipe seront evalues selon SES criteres.

**Capabilities revelees :** Configuration via fichiers, Playground pour test, profils d'analyse metier personnalisables, autonomie du Configurateur.

---

### Journey 5 : Integrateur API (Connexion Systeme Tiers)

**Persona :** Karim, 32 ans, developpeur dans une ESN. Doit connecter le CRM client a CoVeX.

**Scene d'ouverture :**
Karim a recu la documentation API de CoVeX. Il doit integrer l'analyse de completude dans le formulaire de reclamation client du CRM.

**Action montante :**
Il teste l'API via curl :
```bash
curl -X POST http://localhost:8000/analyze \
  -H "Content-Type: application/json" \
  -d '{"text": "Produit casse", "prompt": "reclamation-client"}'
```

Reponse en 1.8 secondes :
```json
{
  "score": 18,
  "decision": "KO",
  "justification": "Reclamation trop vague pour traitement. Manque: reference produit, date d'achat, description du defaut. Exemple: Reclamation pour mixeur ref MX-2000 achete le 12/01/2025..."
}
```

**Climax :**
Karim integre l'appel API dans le formulaire CRM. Si `décision != "OK"`, le formulaire affiche la justification avant soumission. Le client corrige, re-soumet, et seules les reclamations completes arrivent au service client.

**Resolution :**
L'integration est faite en une demi-journee. Le service client ne recoit plus de reclamations inexploitables. Le taux de "premier contact resolutif" augmente de 40%.

**Capabilities revelees :** API REST simple, reponse JSON structuree, integration facile, latence compatible temps reel.

---

### Journey 6 : VOX - Le Communicant (Demande d'Evolution Technique)

**Persona :** NathaLie, 48 ans, cheffe de projet digitalisation dans une collectivite. Excellente a l'oral, ses ecrits vont parfois "droit au but" un peu trop vite.

**Scene d'ouverture :**
NathaLie sort d'une reunion avec le service urbanisme. Ils ont besoin d'une evolution sur la GED du projet "Demat'Urba". Elle ouvre le portail de demandes IT et tape entre deux reunions : *"Il faudrait pouvoir classer automatiquement les permis de construire par commune dans la GED. Merci."*

**Action montante :**
CoVeX analyse sa demande : **31/100 - PARTIEL**.

La justification s'affiche : *"Demande d'evolution incomplete pour prise en charge par l'equipe de developpement : contexte projet absent, besoin metier non decrit, comportement actuel vs souhaite non precise, criteres de classement flous, volumetrie non indiquee, priorite et echeance manquantes."*

Un exemple est propose :
*"**Projet :** Demat'Urba (ref. PRJ-2024-087)*
*Demande d'evolution GED : classement automatique des permis de construire.*

*Contexte : Actuellement, les 1 200 PC/an sont classes manuellement par les agents dans des dossiers par commune (32 communes). Temps estime : 5 min/dossier = 100h/an.*

*Besoin : A l'import d'un PC, lecture automatique du champ 'commune' (metadonnee XML CERFA) et classement dans le dossier GED correspondant. Si commune non reconnue → dossier 'A classer manuellement' + alerte agent.*

*Priorite : Moyenne. Souhait de livraison avant la periode haute (mars-juin).*
*Impact si non fait : Maintien de la charge manuelle, risque d'erreurs de classement.*"

**Climax :**
NathaLie realise que sa demande initiale aurait genere 3 allers-retours avec le developpeur ("C'est quoi le champ commune ?", "Combien de communes ?", "C'est urgent ou pas ?"). Elle prend 5 minutes pour reformuler en s'inspirant de l'exemple.

Nouveau score : **87/100 - OK**. Le developpeur recoit une demande qu'il peut estimer et planifier directement.

**Resolution :**
Le developpeur Lucas ouvre la demande. Tout est la : contexte, besoin, volumetrie, priorite. Il peut immediatement estimer (2 jours de dev) et proposer un creneau. Pas de reunion de "clarification", pas d'emails ping-pong. Le projet Demat'Urba avance.

**Capabilities revelees :** Adaptation au contexte technique (demande de dev), vocabulaire metier dans les criteres, exemples structures type "specification legere", reduction des allers-retours inter-equipes.

---

### Journey Requirements Summary

| Journey | Mode | Capabilities Cles |
|---------|------|-------------------|
| **ZAP** | Synchrone | Analyse temps reel (< 2s), feedback instantane, exemples contextuels |
| **GO** | Asynchrone | Scoring differe, marquage workflow, non-blocage utilisateur |
| **CIT** | Guide | Guidage bienveillant, checklist pieces requises, ton adapte |
| **VOX** | Synchrone | Vocabulaire metier, exemples structures type spec |
| **Configurateur** | Configuration | Fichiers de configuration, Playground test, autonomie sans code |
| **Integrateur** | API | REST/JSON, latence < 2s, integration simple |

**Personas additionnels** (couverts par les journeys ci-dessus) :
- **NEW** (Decouvreur) : Meme pattern que CIT - mode guide avec ton pedagogique
- **MOA** (Maitre d'Ouvrage BTP) : Meme pattern que ZAP/VOX - mode synchrone pour demandes de devis
- **OPS** (Operationnel Chantier) : Meme pattern que GO - mode asynchrone pour rapports terrain

**Modes d'interaction :**
1. **Synchrone/Bloquant** : Feedback immediat avant soumission (ZAP, CIT, VOX)
2. **Asynchrone/Non-bloquant** : Scoring en arriere-plan pour workflow aval (GO)
3. **Configuration** : Setup des profils d'analyse metier via fichier de configuration + test Playground
4. **Integration** : Consommation API depuis systemes tiers

## Functional Requirements

### Analyse de Completude (Core)

- **FR1:** Soumettre un texte libre pour analyse de completude
- **FR2:** Fournir un identifiant de contexte explicite et obligatoire pour executer une analyse
- **FR3:** Refuser toute analyse si aucun contexte explicite valide n'est fourni
- **FR4:** Produire un score de completude (0-100)
- **FR5:** Produire une decision basee sur le score (KO ≤30 / PARTIEL 31-70 / OK >70)
- **FR6:** Produire une justification textuelle expliquant le score

#### Acceptance Criteria (FRs cles)

| FR | Critere d'Acceptation |
|----|----------------------|
| **FR2** | Given un texte et un `profile_id` valide, When le systeme analyse, Then il applique exactement le contexte demande |
| **FR4** | Given un texte et un prompt, When le systeme analyse, Then il retourne un entier 0-100 (jamais null, jamais hors bornes) en < 5 secondes |
| **FR6** | Given un score calcule, When le systeme genere la justification, Then elle contient : (1) raison du score, (2) elements manquants si score < 70, (3) au moins 20 caracteres |
| **FR15** | Given un prompt ajoute/modifie/supprime dans la configuration, When le systeme recoit une requete `/analysis-profiles` ou `/analyze`, Then le changement est pris en compte sans redemarrage en < 5s |
| **FR3** | Given une requete sans `profile_id`, When le systeme analyse, Then il retourne une erreur explicite sans appliquer de prompt par defaut |

### Configuration des Modeles

- **FR7:** Definir les modeles SLM/LLM disponibles via un fichier de configuration
- **FR8:** Specifier le provider par modele (local/cloud)
- **FR9:** Definir les parametres d'inference par defaut par provider
- **FR10:** Changer le modele actif sans modification de code

### Configuration des Profils d'analyse metier

- **FR11:** Creer des profils d'analyse metier via des fichiers de configuration
- **FR12:** Definir les criteres de completude dans un prompt
- **FR13:** Associer une description a chaque prompt
- **FR14:** Associer un modele specifique a un prompt
- **FR15:** Prendre en compte les changements de prompts (ajout/modification/suppression) sans redemarrage

### Validation du Contexte Explicite

- **FR16:** Valider que le contexte fourni correspond a un prompt metier connu et actif
- **FR17:** Exposer les prompts disponibles pour permettre une selection explicite cote UI ou appelant API
- **FR18:** Refuser toute analyse si le contexte demande n'existe pas ou n'est pas actif

### API REST

- **FR19:** Appeler l'endpoint `/analyze` via POST avec `text` et optionnellement un identifiant de contexte
- **FR20:** Recevoir une reponse JSON structuree (score, decision, justification) avec metadonnees optionnelles (ex: model_used, latency_sec, tokens_in, tokens_out, profile_used)
- **FR21:** Recevoir des codes d'erreur explicites (400, 404, 500, 503)
- **FR37:** Appeler l'endpoint `/health` via GET pour verifier la disponibilite du service (Nice-to-Have)
- **FR38:** Appeler l'endpoint `/analysis-profiles` via GET pour lister les prompts disponibles (Nice-to-Have)

### Playground UI

- **FR22:** Saisir un texte dans une zone de texte dediee
- **FR23:** Selectionner explicitement un contexte (prompt metier) parmi les prompts disponibles avant toute analyse
- **FR24:** Lancer une analyse via un bouton
- **FR25:** Afficher le score avec un indicateur visuel (couleur selon decision)
- **FR26:** Afficher la decision (KO/PARTIEL/OK)
- **FR27:** Afficher la justification textuelle
- **FR28:** Afficher le modele utilise pour l'analyse
- **FR29:** Afficher le prompt charge (nom et contenu)
- **FR30:** Afficher la duree de l'inference
- **FR31:** Afficher les compteurs de tokens (entree et sortie)
- **FR32:** Afficher le contexte selectionne et effectivement applique

### Infrastructure LLM

- **FR33:** Communiquer avec un moteur d'inference local
- **FR34:** Communiquer avec un moteur d'inference distant
- **FR35:** Envoyer un prompt et recevoir une reponse du modele
- **FR36:** Mesurer les metriques d'inference (duree, tokens)

## Non-Functional Requirements

### Performance

| ID | Requirement | Cible | Mesure |
|----|-------------|-------|--------|
| **NFR1** | Latence d'inference end-to-end | < 5 secondes | Timer API `/analyze` |
| **NFR2** | Latence de validation et resolution du contexte explicite | < 500 ms | Timer etape validation contexte |
| **NFR3** | Temps de reponse Playground (rendu UI) | < 3 secondes | Temps total user-visible |

#### Performance gates (source de verite)

| Metrique | Seuil | Cible (MVP) | Stretch | Mesure |
|---------|-------|-------------|---------|--------|
| Latence `/analyze` end-to-end | p95 < 10s | p95 < 2s | p95 < 1s | Start: requete recue; Stop: reponse envoyee; 100 requetes |
| Latence validation contexte explicite | p95 < 1s | p95 < 500ms | p95 < 250ms | Start: debut validation; Stop: prompt resolu |
| Temps de reponse Playground (rendu UI) | p95 < 5s | p95 < 3s | p95 < 2s | Temps total user-visible |

### Securite & Souverainete

| ID | Requirement | Cible | Mesure |
|----|-------------|-------|--------|
| **NFR4** | Aucune donnee transmise a des serveurs externes en mode local | 100% | Audit trafic reseau |
| **NFR5** | Aucune persistence des textes analyses cote CoVeX | 0 stockage | Pas de BDD/fichiers pour les inputs (audit code/FS/logs) |
| **NFR6** | Secrets et cles API geres hors code et hors fichiers de configuration | 100% | Pas de secrets en clair dans code/config |

### Integration

| ID | Requirement | Cible | Mesure |
|----|-------------|-------|--------|
| **NFR7** | Reponse API conforme au JSON Schema documente | 100% | Validation JSON Schema |
| **NFR8** | Detection automatique si le moteur d'inference est indisponible | Erreur 503 | Test: moteur indisponible → appel `/analyze` retourne 503 |
| **NFR9** | Changement de modele/prompt sans redemarrage | Prise en compte < 5s | Test: modifier la configuration, puis verifier l'effet sur `/analyze` |

### Maintenabilite

| ID | Requirement | Cible | Mesure |
|----|-------------|-------|--------|
| **NFR10** | Configuration modeles via fichiers de configuration (pas de code) | 0 ligne de code pour changer de modele | Audit des fichiers de configuration |
| **NFR11** | Configuration prompts via fichiers de configuration (pas de code) | 0 ligne de code pour nouveau prompt | Audit des fichiers de configuration |
| **NFR12** | Documentation API auto-generee (OpenAPI) | Documentation accessible | Verifier une specification OpenAPI et une documentation consultable |

### Fiabilite

| ID | Requirement | Cible | Mesure |
|----|-------------|-------|--------|
| **NFR13** | Gestion gracieuse des erreurs moteur d'inference (timeout, down) | Message explicite sans stack trace technique | Erreur lisible par non-dev, cause identifiable |
| **NFR14** | Mecanisme retire defini si modele principal indisponible | Bascule automatique + notification | Test: simuler indisponibilite, verifier bascule et retour `model_used` |

#### Strategie de Mecanisme retire (NFR14 detail)

| Phase | Comportement | Configuration |
|-------|--------------|---------------|
| **MVP** | Mecanisme retire vers un modele secondaire local (meme moteur d'inference) | Configuration: modele secondaire configurable |
| **Post-MVP** | Mecanisme retire vers un provider cloud configurable (opt-in) si moteur local indisponible | Configuration: provider cloud configurable |

**Declenchement automatique :** Si le modele principal retourne erreur 3x consecutives ou timeout > 30s, le systeme bascule sur le mecanisme de secours (fallback) sans intervention utilisateur. L'utilisateur est notifie du changement via le champ `model_used` dans la reponse. |

## Technical Architecture

### Stack Technique

| Composant | Technologie | Justification |
|-----------|-------------|---------------|
| **API Backend** | Python + framework API HTTP | Ecosysteme ML, async natif, OpenAPI auto |
| **Playground UI** | UI web (Python) | Python natif, simple, adapte demo |
| **LLM Local** | Moteur d'inference local | Standard de facto pour SLM locaux |
| **LLM Cloud** | Provider cloud configurable (optionnel) | Mecanisme retire transparent post-MVP |
| **Configuration** | Fichiers de configuration | Lisible, editable sans code |
| **Containerisation** | Runtime de conteneurs | Cloud-ready, compatible Docker |

### Reference implementation (MVP)

Cette section liste des choix techniques de reference (non normatifs) pour concretiser l'implementation.

- Langage: Python 3.14
- Framework API: FastAPI
- UI Playground: NiceGUI
- Moteur d'inference local: vLLM-MLX, Ollama
- Mecanisme retire cloud (post-MVP, opt-in): OpenRouter
- Format configuration: YAML
- Containerisation: Podman
- Reverse proxy (option): Traefik
- Modele SLM (exemple): gemma3:4b, qwen3.5:9b, ministral-3:8b

### API Specifications

#### Endpoints MVP

| Endpoint | Methode | Description | Entree | Sortie |
|----------|---------|-------------|--------|--------|
| `/analyze` | POST | Analyse de completude | text, prompt?, id? | score, decision, justification |
| `/health` | GET | Health check (Nice-to-Have) | - | status, version |
| `/analysis-profiles` | GET | Liste prompts (Nice-to-Have) | - | liste d'objets (name, description) |

#### Data Schemas

**Request `/analyze` :**
```json
{
  "text": "string (required) - Texte a analyser",
  "profile_id": "string (required) - Nom du prompt metier explicitement selectionne"
}
```

**Response `/analyze` :**
```json
{
  "score": "integer 0-100",
  "decision": "enum: KO | PARTIEL | OK",
  "justification": "string - Explication du score",
  "model_used": "string (optional)",
  "latency_sec": "number (optional)",
  "tokens_in": "integer (optional)",
  "tokens_out": "integer (optional)",
  "profile_used": "string - Prompt effectivement applique"
}
```

#### Error Codes

| Code | Signification |
|------|---------------|
| 200 | Analyse reussie |
| 400 | Requete invalide (text manquant) |
| 404 | Prompt non trouve |
| 500 | Erreur interne (modele indisponible, etc.) |
| 503 | Service indisponible (moteur d'inference non demarre) |

### Deployment Modes

| Mode | Description | Usage |
|------|-------------|-------|
| **Local venv** | Python + moteur d'inference local sur machine | Developpement, tests |
| **Container** | Image autonome | Demo, deploiement cloud |

### Authentication & Rate Limits

**MVP :** 
- Pas d'authentification - deploiement local uniquement ou derriere reverse proxy
- Pas de rate limiting - usage local/demo

**Post-MVP :** 
- API Key simple si exposition externe
- Rate limiting selon cas d'usage production

### Web App Requirements (Playground)

**Browser matrix (MVP):** Chrome (latest), Safari (latest sur macOS)

**Responsive design (MVP):** le Playground reste utilisable sur mobile (>= 375px) et desktop (>= 1280px)

**Accessibility level (MVP):** accessibilite basique (navigation clavier, labels de champs, focus visible), sans objectif de certification WCAG

**SEO strategy (MVP):** N/A (Playground de demonstration, non destine a l'indexation)

### Playground Features (MVP)

**Zone principale :**
1. **Zone de saisie** : Textarea pour le texte a analyser
2. **Selecteur de contexte** : Dropdown des prompts disponibles, selection obligatoire avant analyse
3. **Bouton Analyser** : Lance l'appel API

**Affichage resultat :**
4. **Score** : Valeur 0-100 avec indicateur visuel (couleur KO/PARTIEL/OK)
5. **Decision** : Badge KO / PARTIEL / OK
6. **Justification** : Texte explicatif du modele
7. **Contexte applique** : Prompt explicitement selectionne et utilise

**Details techniques (panneau depliable) :**
8. **Modele utilise** : Nom du SLM/LLM
9. **Prompt charge** : Nom et contenu du prompt metier
10. **Duree** : Temps d'inference
11. **Compteurs de tokens** : Tokens en entree / Tokens en sortie

## Profils d'analyse metier de Reference

CoVeX MVP couvre **6 domaines metier** repartis sur **3 secteurs** :

### Secteur Entreprise (IT/Interne)

| ID | Prompt | Domaine | Elements Critiques |
|----|--------|---------|-------------------|
| **PROMPT-001** | Ticket Support IT | Support Informatique | Identification equipement, Description probleme |
| **PROMPT-002** | Demande d'Achat Interne | Achats / Approvisionnement | Nature article, Justification besoin |
| **PROMPT-003** | CR d'Intervention Terrain | Maintenance / Services | Identification client/site, Actions realisees |

### Secteur Communes (Service Public)

| ID | Prompt | Domaine | Elements Critiques |
|----|--------|---------|-------------------|
| **PROMPT-004** | Demande Citoyenne | Service Public / Mairies | Nature demande, Identification demandeur |

### Secteur Construction (BTP)

| ID | Prompt | Domaine | Elements Critiques |
|----|--------|---------|-------------------|
| **PROMPT-005** | Demande de Devis Construction | BTP / Travaux | Nature travaux, Localisation chantier |
| **PROMPT-006** | Rapport de Chantier | BTP / Suivi Travaux | Identification chantier, Date et periode |

### Structure d'un Prompt Metier

Chaque prompt definit 3 niveaux d'elements avec ponderation (s'inspirer de LangExtract) :

```text
elements_Evaluation:
  critiques:      # Absence = score < 30 (KO)
    - id: "element_id"
      label: "Libelle affiche"
      poids: 20
  importants:     # Absence = score < 60 (PARTIEL)
    - id: "element_id"
      label: "Libelle affiche"
      poids: 12
  souhaitables:   # Pour score > 80
    - id: "element_id"
      label: "Libelle affiche"
      poids: 6
```

## Validation & KPIs

### Echelle de Scoring

| Plage | Decision | Label | Description |
|-------|----------|-------|-------------|
| 0-30 | **KO** | Inutilisable | Informations critiques manquantes, reecriture complete requise |
| 31-70 | **PARTIEL** | Exploitable avec effort | Clarifications necessaires, traitement possible mais ralenti |
| 71-100 | **OK** | Acceptable | Informations essentielles presentes, traitement standard |

### KPI-001 : Qualite d'Evaluation

| Metrique | Description | Seuil Min | Cible | Excellent |
|----------|-------------|-----------|-------|-----------|
| **Correlation Score** | Coefficient Pearson scores CoVeX vs experts | 0.80 | 0.90 | 0.95 |
| **Accord Decision** | % decisions identiques CoVeX/experts | 85% | 92% | 98% |

### KPI-002 : Coherence Interne

| Metrique | Description | Critere |
|----------|-------------|---------|
| **Monotonie Score** | Score(min) < Score(partiel) < Score(complet) | PASS 100% triplets |
| **Resistance Bruit** | Score(verbeux_hors_sujet) < Score(partiel_pertinent) | PASS 100% paires |
| **Coherence Score/Decision** | Decision conforme aux seuils | 100% |
| **Reproductibilite** | Ecart-type scores sur N executions identiques | < 5 points |

### KPI-003 : Performance Technique

| Metrique | Description | Seuil Min | Cible | Excellent |
|----------|-------------|-----------|-------|-----------|
| **Latence Inference** | Temps de reponse API `/analyze` (p95) | < 10s | < 5s | < 1s |
| **Consommation Memoire** | Pic RAM pendant inference | < 16 GB | < 12 GB | < 8 GB |
| **Souverainete** | Requetes vers cloud en mode local | 0 | 0 | 0 |

### KPI-004 : Valeur Metier

| Metrique | Description | Seuil Min | Cible | Excellent |
|----------|-------------|-----------|-------|-----------|
| **Reduction Iterations** | Baisse allers-retours clarification | -30% | -50% | -70% |
| **Progression Score Moyen** | Amelioration score moyen sur periode | +15 pts | +25 pts | +35 pts |
| **First-Time-Right** | % soumissions OK des premier envoi | 40% | 60% | 80% |
| **Satisfaction Utilisateur** | Score NPS | +20 | +40 | +60 |

### KPI-005 : Qualite du Feedback

| Metrique | Description | Seuil Min | Cible | Excellent |
|----------|-------------|-----------|-------|-----------|
| **Pertinence Justification** | Note experts sur justifications (1-5) | 3.5 | 4.0 | 4.5 |
| **Absence Hallucination** | % evaluations sans erreur factuelle | 95% | 99% | 100% |

### Framework de Validation

Un framework de test automatise existe : `covex_test_runner.py`

**Capacites :**
- Execution des 37 scenarios de test definis dans `covex-test-scenarios.yaml`
- Validation automatique des KPIs (monotonie, resistance bruit, reproductibilite)
- Generation de rapports HTML/JSON
- Mode mock pour tests sans moteur reel

**Usage :**
```bash
python covex_test_runner.py                    # Tous les tests
python covex_test_runner.py --domain tickets   # Un seul domaine
python covex_test_runner.py --scenario TC-IT-001  # Un seul scenario
python covex_test_runner.py --kpi              # Validation KPI uniquement
python covex_test_runner.py --report           # Genere rapport HTML
```

## Innovation & Risks

### Innovation Areas

| Innovation | Description | Niveau |
|------------|-------------|--------|
| 🎯 **Scoring de Completude** | Mesurer la qualite informationnelle (pas la grammaire) | **Pionnier** |
| 🧠 **SLM pour analyse semantique** | Modeles 1-8B pour juger la completude | **Hypothese a valider** |
| 🔒 **Souverainete + IA** | Analyse IA niveau LLM, 100% locale | **Combinaison rare** |
| 🔄 **Auto-amelioration** | CoVeX aide a creer ses propres prompts | **Boucle vertueuse** |

### Competitive Landscape

| Categorie | Solutions existantes | Positionnement CoVeX |
|-----------|---------------------|---------------------|
| **Correcteurs** | Grammarly, Antidote | ❌ Forme, pas fond |
| **LLM Cloud** | ChatGPT, Claude API | ❌ Pas souverains, couteux |
| **Quality Gates** | Formulaires obligatoires | ❌ Rigides, pas intelligents |
| **CoVeX** | - | ✅ Fond + Souverain + Configurable |

### Risk Mitigation

| Risque | Impact | Mitigation |
|--------|--------|------------|
| **SLM insuffisant** | Scoring peu fiable | Mecanisme retire cloud (provider configurable, opt-in) ; changement modele via configuration |
| **Latence trop elevee** | UX degradee | Benchmark precoce ; modeles legers (1-4B) |
| **Prompts mal definis** | Mauvaise evaluation | CoVeX aide a creer/ameliorer les prompts |
| **Concept non compris** | Adoption faible | 6 cas d'usage concrets sur 3 secteurs |

### Validation Approach

| Hypothese | Validation | Critere de succes |
|-----------|------------|-------------------|
| SLM suffisant pour completude | Benchmark 6 cas d'usage | Correlation acceptable avec jugement humain |
| Profils d'analyse metier efficaces | Tests vrais textes | Score discriminant complet/incomplet |
| Latence acceptable | Mesures MacBook M4 | < 5 secondes |

## Implementation Priorities

### MVP Development Order

1. **Core Engine** : Integration moteur d'inference + logique de scoring
2. **API REST** : Endpoint `/analyze`
3. **Configuration** : Modèles + profils d'analyse métier
4. **Playground UI** : Interface web de base
5. **Tests** : Validation sur les 6 cas d'usage

### External Dependencies

| Dépendance | Criticité | Mecanisme retire |
|------------|-----------|----------|
| **Moteur d'inférence local** | Haute | Provider cloud configurable (post-MVP, opt-in) |
| **Modele SLM** | Haute | Changement via configuration |
| **UI Playground** | Moyenne | Gradio, Streamlit |

### MVP Resources

- 1 développeur Python full-stack
- MacBook Air M4 32GB (hardware cible)
- Moteur d'inférence local + un modèle SLM (ou SLM équivalent)

### Critères de Succès MVP

| Critère | Validation |
|---------|------------|
| **Fonctionnel** | Playground permet de tester un texte et voir score + justification |
| **Performance** | Latence < 5 sec sur MacBook M4 |
| **Qualité** | Scores jugés "cohérents" par évaluateur métier |
| **Technique** | Configuration modèle/prompt modifiable sans code |

## Glossaire

| Terme | Définition |
|-------|------------|
| **Complétude** | Mesure de la présence des informations nécessaires au traitement d'un texte. Ne concerne pas la forme (grammaire, style) mais le fond (informations présentes). |
| **SLM (Small Language Model)** | Modèle de langage de petite taille (1-4 milliards de paramètres) exécutable localement sur hardware standard (MacBook M4). |
| **LLM (Large Language Model)** | Modèle de langage de grande taille (>7B paramètres) généralement exécuté en cloud. Ex: GPT-4, Claude, Mistral-Large. |
| **Profil d'analyse métier** | Configuration (fichier) définissant les critères de complétude pour un domaine spécifique (ex: ticket support, demande citoyenne). |
| **Score de complétude** | Valeur numérique 0-100 indiquant le niveau de complétude d'un texte par rapport aux critères du prompt métier. |
| **Décision** | Classification du texte basée sur le score : KO (≤30), PARTIEL (31-70), OK (>70). |
| **Justification** | Explication textuelle générée par le SLM expliquant le score attribué et les éléments manquants. |
| **Sélection explicite du contexte** | Obligation de fournir un prompt métier valide avant toute analyse, sans inférence automatique par CoVeX. |
| **Moteur d'inférence** | Service local permettant d'exécuter des SLM/LLM en mode API. |
| **Provider cloud** | Service cloud d'API permettant d'accéder à différents LLM (mécanisme de secours (fallback) cloud post-MVP, opt-in). |
| **Souveraineté des données** | Garantie que les données analysées restent sur l'infrastructure de l'utilisateur (pas de transfert vers cloud tiers). |
| **Dette textuelle** | Accumulation de textes incomplets, vagues ou inexploitables dans les systèmes d'information (tickets, demandes, CR). |
