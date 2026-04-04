---
stepsCompleted:
  - step-01-validate-prerequisites
  - step-02-design-epics
  - step-03-create-stories
  - step-04-final-validation
inputDocuments:
  - _bmad-output/planning-artifacts/prd.md
  - _bmad-output/planning-artifacts/architecture.md
  - _bmad-output/planning-artifacts/ux-design-specification.md
---

> Note 2026-03-14: artefact BMAD historique. Certaines references internes
> (tests, modules, `criteria`, hot reload, pages playground) peuvent ne plus
> correspondre exactement au depot courant. Pour l'etat actuel, se fier a
> `README.md`, `docs/ARCHITECTURE.md` et `docs/ANALYSIS_PROFILES_METIER.md`.


# CoVeX - Epic Breakdown

## Overview

This document provides the complete epic and story breakdown for CoVeX, decomposing the requirements from the PRD, UX Design, and Architecture requirements into implementable stories.

## Requirements Inventory

### Functional Requirements

FR1: Soumettre un texte libre pour analyse de completude.
FR2: Fournir un identifiant de contexte explicite et obligatoire pour executer l'analyse.
FR3: Refuser toute analyse si aucun contexte explicite valide n'est fourni.
FR4: Produire un score de completude (0-100).
FR5: Produire une decision basee sur le score (KO <=30 / PARTIEL 31-70 / OK >70).
FR6: Produire une justification textuelle expliquant le score.
FR7: Definir les modeles SLM/LLM disponibles via un fichier de configuration.
FR8: Specifier le provider par modele (local/cloud).
FR9: Definir les parametres d'inference par defaut par provider.
FR10: Changer le modele actif sans modification de code.
FR11: Creer des profils d'analyse metier via des fichiers de configuration.
FR12: Definir les criteres de completude dans un prompt.
FR13: Associer une description a chaque prompt.
FR14: Associer un modele specifique a un prompt.
FR15: Prendre en compte les changements de prompts (ajout/modification/suppression) sans redemarrage.
FR16: Valider que le contexte fourni correspond a un prompt metier connu et actif.
FR17: Exposer les prompts disponibles pour permettre une selection explicite.
FR18: Refuser toute analyse si le contexte demande n'existe pas ou n'est pas actif.
FR19: Appeler l'endpoint /analyze via POST avec text et optionnellement un identifiant de contexte.
FR20: Recevoir une reponse JSON structuree (score, decision, justification) avec metadonnees optionnelles.
FR21: Recevoir des codes d'erreur explicites (400, 404, 500, 503).
FR22: Saisir un texte dans une zone de texte dediee.
FR23: Selectionner explicitement un contexte (prompt metier) parmi les prompts disponibles avant toute analyse.
FR24: Lancer une analyse via un bouton.
FR25: Afficher le score avec un indicateur visuel (couleur selon decision).
FR26: Afficher la decision (KO/PARTIEL/OK).
FR27: Afficher la justification textuelle.
FR28: Afficher le modele utilise pour l'analyse.
FR29: Afficher le prompt charge (nom et contenu).
FR30: Afficher la duree de l'inference.
FR31: Afficher les compteurs de tokens (entree et sortie).
FR32: Afficher le contexte selectionne et effectivement applique.
FR33: Communiquer avec un moteur d'inference local.
FR34: Communiquer avec un moteur d'inference distant.
FR35: Envoyer un prompt et recevoir une reponse du modele.
FR36: Mesurer les metriques d'inference (duree, tokens).
FR37: Appeler l'endpoint /health via GET pour verifier la disponibilite du service (Nice-to-Have).
FR38: Appeler l'endpoint /analysis-profiles via GET pour lister les prompts disponibles (Nice-to-Have).

### NonFunctional Requirements

NFR1: Latence d'inference end-to-end < 5 secondes (API /analyze).
NFR2: Latence de validation et resolution du contexte explicite < 500 ms.
NFR3: Temps de reponse Playground < 3 secondes.
NFR4: Aucune donnee transmise a des serveurs externes en mode local.
NFR5: Aucune persistence des textes analyses cote CoVeX.
NFR6: Secrets et cles API geres hors code et hors fichiers de configuration.
NFR7: Reponse API conforme au JSON Schema documente.
NFR8: Detection automatique indisponibilite moteur d'inference avec erreur 503.
NFR9: Changement de modele/prompt sans redemarrage (< 5s).
NFR10: Configuration modeles via fichiers (0 ligne de code pour changer de modele).
NFR11: Configuration prompts via fichiers (0 ligne de code pour nouveau prompt).
NFR12: Documentation API auto-generee (OpenAPI) accessible.
NFR13: Gestion gracieuse des erreurs moteur d'inference (timeout/down) avec message explicite.
NFR14: Mecanisme retire defini si modele principal indisponible (bascule + notification via model_used).

### Additional Requirements

- Starter template architecture a utiliser: fastapi/fastapi-new.
- Commande d'initialisation du projet: uvx fastapi-new covex.
- Le premier story d'implementation doit initialiser le projet avec ce starter template.
- Architecture stateless stricte: aucune base interne, aucune persistance metier, aucun cache MVP.
- Separation nette endpoints API / logique metier / adaptateurs inference / configuration prompts-modeles.
- Endpoints cibles MVP: POST /analyze, GET /health, GET /analysis-profiles (health/analysis-profiles Nice-to-Have).
- Contrat API REST JSON en snake_case, reponses succes typees, erreurs FastAPI par defaut.
- Adaptateur inference synchrone avec timeouts et mecanisme retire standardises.
- Configuration runtime via .env + YAML (analysis_profiles.yaml, inference_engines.yaml).
- Logging texte minimal MVP; observabilite etendue reportee post-MVP.
- No-auth applicatif en MVP (usage reseau de confiance uniquement).
- Playground Playground NiceGUI/Quasar en route unique, etat local, page monolithique MVP.
- Rester utilisable desktop et mobile (>=375px), focus desktop-first.
- Accessibilite basique: navigation clavier, labels explicites, focus visible, pas couleur seule.
- Hierarchie UX stable: Score -> Decision -> Justification -> Details techniques (opt-in).
- Mapping visuel de decision: KO negative, PARTIEL warning, OK positive.
- Experience demo-ready: boutons d'exemples pre-remplis et details techniques depliables.
- Gestion erreurs UX neutre: service indisponible sans perte de texte utilisateur.
- Integration interne playground->backend uniquement via client API dedie.
- Respect strict des conventions de nommage snake_case et organisation feature-first.

### FR Coverage Map

FR1: Epic 1 - Soumission texte
FR2: Epic 1 - Contexte d'analyse
FR3: Epic 1 - Validation du contexte explicite obligatoire
FR4: Epic 1 - Score de completude 0-100
FR5: Epic 1 - Decision KO/PARTIEL/OK
FR6: Epic 1 - Justification exploitable
FR7: Epic 2 - Definition des modeles via configuration
FR8: Epic 2 - Selection provider par modele
FR9: Epic 2 - Parametres d'inference par defaut
FR10: Epic 2 - Changement de modele sans code
FR11: Epic 2 - Creation de profils d'analyse metier via fichiers
FR12: Epic 2 - Definition des criteres de completude
FR13: Epic 2 - Description associee a chaque prompt
FR14: Epic 2 - Association modele specifique par prompt
FR15: Epic 2 - Prise en compte des changements prompts sans redemarrage
FR16: Epic 1 - Validation du prompt explicitement demande
FR17: Epic 4 - Exposition des prompts disponibles
FR18: Epic 1 - Rejet des contextes inconnus ou inactifs
FR19: Epic 1 - Endpoint POST /analyze
FR20: Epic 1 - Reponse JSON structuree avec metadonnees
FR21: Epic 1 - Gestion des codes d'erreur explicites
FR22: Epic 3 - Saisie texte dans le Playground
FR23: Epic 3 - Selection explicite du contexte
FR24: Epic 3 - Declenchement de l'analyse via bouton
FR25: Epic 3 - Affichage visuel du score
FR26: Epic 3 - Affichage de la decision
FR27: Epic 3 - Affichage de la justification
FR28: Epic 3 - Affichage du modele utilise
FR29: Epic 3 - Affichage du prompt charge
FR30: Epic 3 - Affichage de la duree d'inference
FR31: Epic 3 - Affichage des tokens entree/sortie
FR32: Epic 3 - Affichage du contexte applique
FR33: Epic 1 - Communication moteur d'inference local
FR34: Epic 2 - Communication moteur d'inference distant configurable
FR35: Epic 1 - Envoi prompt et reception reponse modele
FR36: Epic 1 - Mesure des metriques d'inference
FR37: Epic 4 - Endpoint GET /health
FR38: Epic 4 - Endpoint GET /analysis-profiles

## Epic List

### Epic 1: Analyse de completude utilisable de bout en bout (MVP local-first)
Permettre a un utilisateur (ou systeme tiers) de soumettre un texte et recevoir un verdict exploitable (score, decision, justification) de maniere fiable en mode local.
**FRs covered:** FR1, FR2, FR3, FR4, FR5, FR6, FR16, FR18, FR19, FR20, FR21, FR33, FR35, FR36

### Epic 2: Configuration metier dynamique (modeles + prompts sans code)
Permettre au configurateur d'adapter CoVeX a ses domaines metier via fichiers de configuration, sans redemarrage ni modification de code.
**FRs covered:** FR7, FR8, FR9, FR10, FR11, FR12, FR13, FR14, FR15, FR34

### Epic 3: Experience Playground demonstrable et actionnable
Permettre aux decideurs et utilisateurs de tester rapidement CoVeX via une interface claire, avec feedback interpretable et details techniques en option.
**FRs covered:** FR22, FR23, FR24, FR25, FR26, FR27, FR28, FR29, FR30, FR31, FR32

### Epic 4: Exploitabilite operationnelle (endpoints utilitaires MVP)
Permettre la verification de disponibilite du service et la decouverte des prompts disponibles pour faciliter integration et exploitation.
**FRs covered:** FR37, FR38

## Epic 1: Analyse de completude utilisable de bout en bout (MVP local-first)

Permettre a un utilisateur (ou systeme tiers) de soumettre un texte et recevoir un verdict exploitable (score, decision, justification) de maniere fiable en mode local.

### Story 1.1: Set up initial project from starter template

As a developer,
I want initialiser CoVeX avec le starter `fastapi/fastapi-new` et la structure de base cible,
So that l equipe peut implementer les stories suivantes sur une fondation conforme a l architecture.

**FRs implemented:** FR19, FR33

**Acceptance Criteria:**

**Given** un workspace vide pour l implementation
**When** le starter `fastapi/fastapi-new` est initialise (`uvx fastapi-new covex`)
**Then** la base projet est creee avec dependances et outillage de dev standard
**And** la structure permet d ajouter `backend/src/main.py` et `playground/src/app.py` selon l architecture cible

**Given** la base projet est creee
**When** les fichiers de configuration minimum (`.env.example`, YAML de config) sont poses
**Then** les points d entree de l application peuvent demarrer localement
**And** aucune logique metier non necessaire n est implementee dans cette story

**Given** l architecture impose une progression incrementale
**When** cette story est terminee
**Then** elle fournit uniquement la fondation technique immediate requise
**And** elle n introduit pas de travail massif hors besoin des stories suivantes

**Given** la story est prete pour handoff
**When** l equipe relit les artefacts de demarrage
**Then** les conventions de nommage et structure (snake_case, boundaries feature-first) sont appliquees
**And** les stories Epic 1 suivantes peuvent demarrer sans blocage d infrastructure

### Story 1.2: Implementer le moteur de scoring et de decision

As a product owner,
I want que CoVeX calcule un score de completude et une decision a partir d un texte et d un prompt,
So that les utilisateurs recoivent un verdict actionnable et coherent.

**FRs implemented:** FR1, FR4, FR5, FR6

**Acceptance Criteria:**

**Given** un texte valide et un prompt metier resolu
**When** l analyse est executee
**Then** le systeme calcule un `score` entier entre 0 et 100
**And** il derive `decision` selon les seuils MVP (`KO <= 30`, `PARTIEL 31-70`, `OK > 70`)

**Given** une analyse terminee
**When** la reponse est construite
**Then** `justification` explique la raison du score en langage clair
**And** pour un score < 70, elle mentionne explicitement les elements manquants

**Given** plusieurs analyses identiques sur un meme texte/prompt
**When** elles sont executees dans les memes conditions
**Then** la variation de score reste limitee et compatible avec les objectifs de reproductibilite
**And** la decision reste coherente avec le score retourne

**Given** un texte incomplet vs partiel vs complet pour un meme prompt
**When** les trois analyses sont executees
**Then** les scores respectent une progression monotone (incomplet < partiel < complet)
**And** les decisions suivent les seuils attendus

**Given** des erreurs de format de sortie modele
**When** le service traite le resultat d inference
**Then** il applique une validation defensive avant reponse API
**And** il retourne une erreur maitrisee si le resultat ne peut pas etre interprete proprement

### Story 1.3: Valider et resoudre un contexte metier explicitement fourni

As an utilisateur ou integrateur API,
I want fournir un `profile_id` explicite et valide pour lancer l analyse,
So that CoVeX applique uniquement le contexte demande sans inference implicite.

**FRs implemented:** FR2, FR3, FR16, FR18

**Acceptance Criteria:**

**Given** une requete `POST /analyze` avec un `profile_id` valide
**When** l analyse est executee
**Then** le systeme charge exactement le prompt demande
**And** il renseigne `profile_used` avec cette meme valeur dans la reponse

**Given** une requete `POST /analyze` sans `profile_id`
**When** elle est recue
**Then** le systeme retourne une erreur `400`
**And** aucun prompt par defaut n est applique

**Given** une requete `POST /analyze` avec un `profile_id` inconnu ou inactif
**When** elle est traitee
**Then** le systeme retourne une erreur `404`
**And** la cause indique clairement le contexte demande non resolu

**Given** un `profile_id` explicite est fourni par le client
**When** l analyse est executee
**Then** aucun routage automatique n est impose
**And** le prompt explicitement demande est prioritaire

**Given** la reponse de succes est retournee
**When** les metadonnees sont examinees
**Then** `routing_confidence` est absent du contrat
**And** `profile_used` suffit a tracer le contexte applique

### Story 1.4: Integrer l adaptateur d inference locale avec timeouts et metriques

As a integrateur plateforme,
I want que CoVeX appelle un moteur d inference local via un adaptateur encapsule avec timeout,
So that le service reste fiable, mesurable et conforme aux objectifs de performance.

**FRs implemented:** FR33, FR35, FR36

**Acceptance Criteria:**

**Given** une analyse est demandee
**When** le service appelle le moteur d inference local via l adaptateur
**Then** l appel est encapsule hors des handlers API
**And** la couche API ne depend que du service metier

**Given** un appel inference aboutit
**When** la reponse est retournee a l API
**Then** les metriques `latency_sec`, `tokens_in`, `tokens_out` sont renseignees quand disponibles
**And** elles sont integrees dans la reponse sans casser le contrat minimal

**Given** le moteur local ne repond pas avant le delai configure
**When** le timeout est atteint
**Then** l adaptateur interrompt proprement l appel
**And** le service retourne une erreur maitrisee compatible `503` ou `500` selon la cause

**Given** des erreurs transientes cote moteur (reseau local, reponse invalide)
**When** l adaptateur les detecte
**Then** elles sont journalisees de facon exploitable
**And** le message client reste clair, court et sans details techniques sensibles

**Given** un volume de requetes MVP normal
**When** les mesures de performance sont observees
**Then** le design permet d atteindre les cibles de latence (`/analyze` et validation contexte)
**And** les points de mesure sont suffisamment explicites pour verification KPI

### Story 1.5: Standardiser la gestion d erreurs API explicites

As an integrateur API,
I want des erreurs HTTP explicites et stables selon les cas metier et techniques,
So that mon systeme tiers puisse gerer les echecs sans ambiguite.

**FRs implemented:** FR19, FR20, FR21

**Acceptance Criteria:**

**Given** une requete invalide (schema, champ requis manquant, texte vide)
**When** `POST /analyze` est appele
**Then** l API retourne `400`
**And** le message permet de corriger la requete sans inspection serveur

**Given** un prompt explicitement demande mais introuvable
**When** la requete est traitee
**Then** l API retourne `404`
**And** la cause indique clairement l identifiant de prompt non resolu

**Given** une indisponibilite du moteur d inference
**When** l analyse est demandee
**Then** l API retourne `503`
**And** la reponse reste concise, sans fuite de details internes

**Given** une erreur interne non recuperable hors indisponibilite moteur
**When** le traitement echoue
**Then** l API retourne `500`
**And** le format d erreur est coherent avec le reste de l API MVP

**Given** une erreur est retournee au client
**When** l incident est journalise cote serveur
**Then** les logs contiennent le contexte utile au diagnostic
**And** ils n incluent pas de texte utilisateur brut persiste de facon durable

### Story 1.6: Mettre en place le mecanisme retire inference du modele principal

As a product owner,
I want que CoVeX bascule automatiquement vers un modele de mecanisme retire quand le modele principal est indisponible,
So that le service reste disponible et exploitable sans intervention manuelle immediate.

**FRs implemented:** FR20, FR21

**Acceptance Criteria:**

**Given** le modele principal echoue de maniere repetee (ex: 3 erreurs consecutives) ou depasse le timeout defini
**When** une nouvelle analyse est demandee
**Then** le systeme bascule automatiquement vers le modele de mecanisme retire configure
**And** l analyse continue sans interruption applicative

**Given** un mecanisme retire est utilise
**When** la reponse de succes est retournee
**Then** le champ `model_used` indique explicitement le modele effectivement utilise
**And** cette information est exploitable par UI et integrateurs API

**Given** le modele principal redevient disponible
**When** la strategie de reprise definie est satisfaite
**Then** le systeme peut revenir au modele principal selon la politique configuree
**And** ce comportement reste deterministic et journalise

**Given** modele principal et mecanisme retire sont indisponibles
**When** une analyse est demandee
**Then** l API retourne une erreur maitrisee (`503`)
**And** le message informe clairement de l indisponibilite du service d inference

**Given** la strategie de mecanisme retire est active
**When** les NFR de fiabilite sont verifies
**Then** la bascule est testable de bout en bout
**And** elle respecte les contraintes de souverainete (pas de cloud non opt-in en MVP local)

## Epic 2: Configuration metier dynamique (modeles + prompts sans code)

Permettre au configurateur d adapter CoVeX a ses domaines metier via fichiers de configuration, sans redemarrage ni modification de code.

### Story 2.1: Charger et valider la configuration des modeles

As a configurateur,
I want definir les modeles disponibles dans un fichier de configuration valide,
So that je puisse changer le modele actif sans modifier le code applicatif.

**FRs implemented:** FR7, FR8, FR9, FR10

**Acceptance Criteria:**

**Given** un fichier `inference_engines.yaml` conforme est present
**When** le service demarre
**Then** la liste des modeles est chargee en memoire
**And** chaque modele expose son provider et ses parametres utiles

**Given** un modele est marque actif dans la configuration
**When** une analyse est executee sans override specifique
**Then** ce modele est utilise par defaut
**And** `model_used` reflete effectivement ce choix

**Given** une configuration modele invalide (champ manquant, type invalide, doublon d identifiant)
**When** le chargement est tente
**Then** le service rejette la configuration avec erreur explicite
**And** aucune configuration partiellement incoherente n est appliquee

**Given** un changement du modele actif est fait uniquement dans la configuration
**When** la configuration est re-evaluee selon la strategie de reload
**Then** le nouveau modele devient actif sans changement de code
**And** la transition reste tracable dans les logs techniques

### Story 2.2: Gerer les profils d'analyse metier via configuration

As a expert metier,
I want creer et maintenir des profils d'analyse metier dans des fichiers de configuration,
So that CoVeX evalue la completude selon mes criteres de domaine.

**FRs implemented:** FR11, FR12, FR13

**Acceptance Criteria:**

**Given** un fichier `analysis_profiles.yaml` conforme
**When** le service charge la configuration
**Then** chaque prompt est disponible avec son `name`, sa `description` et ses criteres
**And** les prompts sont consultables par les composants qui en dependent

**Given** un prompt inclut des criteres de completude (critiques/importants/souhaitables ou equivalent)
**When** il est valide au chargement
**Then** les regles sont structurees et exploitables par le moteur d analyse
**And** les poids ou attributs incoherents sont refuses avec message explicite

**Given** un prompt reference un modele specifique
**When** ce modele existe dans la configuration modeles
**Then** l association prompt vers modele est acceptee
**And** elle est resolue de facon deterministic lors de l analyse

**Given** un prompt reference un modele inexistant ou un schema prompt invalide
**When** la validation est executee
**Then** la configuration est rejetee proprement
**And** l erreur indique le prompt en cause pour correction rapide

**Given** une integration demande la liste des profils d'analyse disponibles
**When** `GET /analysis-profiles` (nice-to-have) ou la couche interne de consultation est appelee
**Then** les prompts actifs sont retournes de maniere stable
**And** aucune information sensible interne n est exposee

### Story 2.3: Appliquer la resolution prompt vers modele et parametres provider

As a integrateur technique,
I want que chaque analyse applique automatiquement le bon modele et les bons parametres d inference selon le prompt selectionne,
So that le comportement de CoVeX soit previsible et coherent entre domaines metier.

**FRs implemented:** FR14, FR8, FR9

**Acceptance Criteria:**

**Given** un prompt metier explicitement selectionne
**When** une analyse est lancee
**Then** le systeme resolve le modele associe a ce prompt
**And** il utilise ce modele pour l inference

**Given** des parametres provider par defaut sont definis
**When** le modele associe est utilise
**Then** les parametres d inference applicables sont fusionnes correctement (defaults + overrides autorises)
**And** les priorites de surcharge sont deterministes et documentees

**Given** un prompt ne definit pas explicitement de modele
**When** la resolution est effectuee
**Then** le systeme applique une strategie de mecanisme retire de configuration (modele actif ou global)
**And** `model_used` reste coherent avec la resolution effective

**Given** des parametres incompatibles avec le provider cible
**When** la validation runtime est faite
**Then** le systeme retourne une erreur maitrisee et explicite
**And** l execution n utilise pas de configuration partiellement invalide

**Given** une analyse terminee
**When** la reponse est construite
**Then** les metadonnees techniques exposees refletent exactement la configuration appliquee
**And** cela permet diagnostic et reproductibilite cote integration

### Story 2.4: Activer la prise en compte des changements de configuration sans redemarrage

As a configurateur,
I want que les changements de prompts et modeles soient pris en compte rapidement sans redemarrer CoVeX,
So that je puisse iterer sur la qualite metier en continu.

**FRs implemented:** FR10, FR15

**Acceptance Criteria:**

**Given** un ajout, une modification ou une suppression dans les fichiers de configuration prompts et modeles
**When** le mecanisme de reload est declenche
**Then** les changements deviennent actifs en moins de 5 secondes
**And** aucune recompilation ni redeploiement n est necessaire

**Given** un reload de configuration est en cours
**When** des requetes d analyse arrivent simultanement
**Then** le service reste stable et repond sans etat incoherent
**And** la transition entre ancienne et nouvelle configuration est atomique

**Given** une nouvelle configuration invalide est detectee lors du reload
**When** la validation echoue
**Then** le systeme conserve la derniere configuration valide
**And** il journalise explicitement la raison du rejet

**Given** une modification de prompt est appliquee
**When** une requete `POST /analyze` suivante est executee
**Then** la nouvelle version du prompt est utilisee immediatement
**And** le comportement est observable via `profile_used` et traces techniques

**Given** une modification du modele actif est appliquee
**When** une nouvelle analyse est lancee
**Then** le nouveau modele est pris en compte sans redemarrage
**And** `model_used` confirme le changement effectif

### Story 2.5: Supporter un provider d inference distant configurable

As a responsable technique,
I want configurer un provider d inference distant en plus du moteur local,
So that CoVeX puisse fonctionner dans des contextes ou l inference locale n est pas suffisante.

**FRs implemented:** FR34, FR8

**Acceptance Criteria:**

**Given** un provider distant est defini dans la configuration modeles
**When** un modele associe a ce provider est selectionne
**Then** CoVeX appelle correctement le provider distant via l adaptateur
**And** le contrat de sortie reste identique a celui du mode local

**Given** le mode local-first est actif en MVP
**When** aucune option cloud n est explicitement activee
**Then** aucune requete inference n est envoyee vers le cloud
**And** la souverainete locale est preservee par defaut

**Given** des credentials provider sont requis
**When** le service est configure
**Then** les secrets sont lus depuis l environnement (pas en clair dans code ou config)
**And** une erreur explicite est retournee si les secrets manquent

**Given** une erreur cote provider distant (timeout, auth, quota, indisponibilite)
**When** une analyse est executee
**Then** le systeme retourne une erreur maitrisee conforme au contrat API
**And** les logs techniques permettent le diagnostic sans exposer de secret

**Given** une analyse reussie via provider distant
**When** la reponse est renvoyee
**Then** `model_used` et metadonnees techniques permettent d identifier le chemin d execution
**And** la decision et la justification restent au meme niveau de qualite attendu

## Epic 3: Experience Playground demonstrable et actionnable

Permettre aux decideurs et utilisateurs de tester rapidement CoVeX via une interface claire, avec feedback interpretable et details techniques en option.

### Story 3.1: Construire le Playground de saisie et lancement d analyse

As a utilisateur demo,
I want saisir un texte, choisir explicitement un contexte et lancer l analyse en un clic,
So that je puisse evaluer rapidement la completude d une demande sans ambiguite sur le prompt applique.

**FRs implemented:** FR22, FR23, FR24

**Acceptance Criteria:**

**Given** la page Playground est ouverte
**When** l interface est affichee
**Then** elle contient une zone de saisie texte, un selecteur de contexte, et un bouton principal `Analyser`
**And** aucun mode `Auto` n est disponible

**Given** au moins un prompt est disponible
**When** l utilisateur ouvre le selecteur de contexte
**Then** il voit la liste des profils d'analyse metier disponibles
**And** il doit choisir un prompt explicite avant toute analyse

**Given** le champ texte est vide
**When** l utilisateur tente de lancer l analyse
**Then** l action est bloquee avec un retour explicite
**And** aucune requete API inutile n est envoyee

**Given** un texte valide est saisi
**When** l utilisateur clique sur `Analyser`
**Then** la requete est envoyee vers l API avec le contexte choisi
**And** l etat UI passe en mode traitement jusqu a reception du resultat

**Given** aucun contexte n est selectionne
**When** l utilisateur tente de lancer l analyse
**Then** l action est bloquee avec un retour explicite
**And** aucun appel API n est emis

### Story 3.2: Afficher le resultat principal de maniere lisible et actionnable

As a utilisateur final,
I want voir clairement le score, la decision et la justification apres chaque analyse,
So that je comprenne rapidement ce qui est exploitable et ce qui manque.

**FRs implemented:** FR25, FR26, FR27

**Acceptance Criteria:**

**Given** une analyse reussie
**When** le resultat est affiche
**Then** l UI presente la hierarchie `score -> decision -> justification`
**And** cette hierarchie reste stable a chaque execution

**Given** un score retourne par l API
**When** la decision correspondante est determinee
**Then** l indicateur visuel applique le mapping couleur attendu (`KO=negative`, `PARTIEL=warning`, `OK=positive`)
**And** la decision est aussi visible textuellement (pas couleur seule)

**Given** une decision `KO` ou `PARTIEL`
**When** la justification est affichee
**Then** les elements manquants sont comprehensibles et orientent la correction
**And** l utilisateur peut modifier son texte puis relancer sans perdre le contexte de travail

**Given** plusieurs analyses consecutives dans la meme session
**When** un nouveau resultat arrive
**Then** l affichage est remplace proprement sans incoherence UI
**And** les valeurs affichees correspondent strictement a la derniere reponse API

**Given** une reponse API partielle (metadonnees absentes mais champs minimaux presents)
**When** le panneau principal est rendu
**Then** l affichage reste fonctionnel avec `score`, `decision`, `justification`
**And** aucune erreur front ne bloque l utilisateur

### Story 3.3: Afficher les details techniques en mode opt-in

As a decideur technique,
I want consulter les details techniques de l analyse uniquement quand j en ai besoin,
So that je gagne en confiance sans surcharger l interface principale.

**FRs implemented:** FR28, FR29, FR30, FR31, FR32

**Acceptance Criteria:**

**Given** un resultat d analyse est disponible
**When** l utilisateur ouvre le panneau de details
**Then** les informations techniques pertinentes s affichent (modele utilise, prompt utilise, latence, tokens)
**And** le panneau est ferme par defaut

**Given** certaines metadonnees ne sont pas fournies par l API
**When** le panneau est affiche
**Then** l UI degrade proprement sans erreur
**And** seuls les champs disponibles sont montres

**Given** l utilisateur alterne analyses et ouverture ou fermeture du panneau
**When** un nouveau resultat arrive
**Then** les details affiches correspondent au dernier appel
**And** aucune ancienne valeur stale n est conservee visuellement

**Given** l utilisateur n ouvre pas le panneau
**When** il utilise le Playground en mode standard
**Then** le flux principal reste simple et rapide
**And** la comprehension du resultat ne depend pas des details techniques

**Given** un resultat d analyse est disponible
**When** `profile_used` est present
**Then** cette information est visible dans le panneau
**And** aucune metadonnee de routage automatique n est affichee

### Story 3.4: Gerer proprement les etats UX (loading, erreurs, preservation saisie)

As a utilisateur operationnel,
I want que l interface reste claire et robuste pendant les chargements et en cas d erreur API,
So that je puisse continuer sans perdre mon travail.

**FRs implemented:** FR24, FR27

**Acceptance Criteria:**

**Given** une analyse est en cours
**When** l utilisateur a clique sur `Analyser`
**Then** le bouton principal passe en etat de chargement ou desactivation
**And** les doubles soumissions involontaires sont evitees

**Given** une erreur API survient (`400`, `404`, `500`, `503`)
**When** la reponse d erreur est recue
**Then** un message utilisateur court et explicite est affiche
**And** aucune stack trace technique n apparait dans l UI

**Given** une indisponibilite temporaire du service
**When** l erreur est presentee a l utilisateur
**Then** l interface propose implicitement une action de reprise (corriger ou reessayer)
**And** la saisie texte courante est conservee

**Given** une erreur survient apres des resultats precedents valides
**When** l UI se met a jour
**Then** l etat d erreur est visible sans casser la structure de la page
**And** la prochaine analyse peut etre relancee sans rafraichir l application

**Given** un retour a la normale apres erreur
**When** une nouvelle analyse reussit
**Then** l etat d erreur est nettoye correctement
**And** le resultat courant s affiche normalement

### Story 3.5: Assurer responsive et accessibilite basique du Playground

As a utilisateur mobile ou clavier-only,
I want utiliser le Playground facilement sur differentes tailles d ecran et avec navigation clavier,
So that l experience reste inclusive et exploitable en demo comme en usage quotidien.

**FRs implemented:** FR22, FR25

**Acceptance Criteria:**

**Given** le Playground est ouvert sur mobile (>=375px), tablet et desktop
**When** la page est rendue
**Then** les composants restent lisibles et utilisables sans chevauchement
**And** le flux principal conserve la hierarchie `input -> action -> resultat -> details`

**Given** un ecran mobile
**When** les actions sont affichees
**Then** les boutons se repositionnent en pile ou wrap de facon ergonomique
**And** la cible tactile reste suffisante pour interaction confortable

**Given** une navigation clavier-only
**When** l utilisateur parcourt la page via Tab et Shift+Tab
**Then** l ordre de focus est logique (contexte, textarea, actions, resultat, details)
**And** l etat de focus est visible sur les elements interactifs

**Given** des indicateurs de decision colores
**When** le resultat est affiche
**Then** l information est aussi fournie textuellement (`KO`, `PARTIEL`, `OK`)
**And** la comprehension ne depend pas de la couleur seule

**Given** un lecteur d ecran ou verification a11y basique
**When** les champs principaux sont annonces
**Then** les labels de saisie et de contexte sont explicites
**And** le changement de resultat est percevable pour l utilisateur

## Epic 4: Exploitabilite operationnelle (endpoints utilitaires MVP)

Permettre la verification de disponibilite du service et la decouverte des prompts disponibles pour faciliter integration et exploitation.

### Story 4.1: Exposer un endpoint health check fiable

As a exploitant technique,
I want verifier rapidement si CoVeX est disponible via `GET /health`,
So that je puisse monitorer le service et diagnostiquer un incident de disponibilite.

**FRs implemented:** FR37

**Acceptance Criteria:**

**Given** le service API est demarre
**When** `GET /health` est appele
**Then** une reponse `200` est retournee si le service est operationnel
**And** le payload indique un statut explicite (ex: `status`)

**Given** le moteur d inference est indisponible
**When** `GET /health` est appele
**Then** la reponse reflete cet etat de dependance de facon exploitable
**And** elle permet de distinguer API up vs inference down

**Given** une integration de supervision interroge periodiquement l endpoint
**When** les reponses sont analysees
**Then** le format reste stable dans le temps
**And** il est suffisamment simple pour checks automatises

**Given** une erreur interne affecte la verification de sante
**When** l endpoint est execute
**Then** l erreur est geree proprement sans stack trace client
**And** les logs serveur contiennent le contexte de diagnostic

### Story 4.2: Exposer la liste des profils d'analyse disponibles via API

As an integrateur API,
I want recuperer les profils d'analyse metier actifs via `GET /analysis-profiles`,
So that je puisse configurer l UI cliente et les integrations avec des options a jour.

**FRs implemented:** FR38

**Acceptance Criteria:**

**Given** des prompts actifs sont charges dans la configuration
**When** `GET /analysis-profiles` est appele
**Then** l API retourne la liste des profils d'analyse disponibles
**And** chaque entree contient au minimum les metadonnees utiles (`name`, `description` ou equivalent)

**Given** aucun prompt n est disponible
**When** `GET /analysis-profiles` est execute
**Then** l API retourne une reponse valide avec liste vide
**And** le contrat reste stable pour les consommateurs

**Given** un changement de configuration prompts est applique (ajout, modification, suppression)
**When** `GET /analysis-profiles` est appele apres reload
**Then** la liste retournee reflete l etat courant sans redemarrage
**And** les integrations voient rapidement les nouvelles options

**Given** une erreur interne survient pendant la lecture des prompts
**When** l endpoint est appele
**Then** une erreur maitrisee est retournee selon le contrat API
**And** aucune information sensible de configuration n est exposee

**Given** une integration UI utilise cette liste
**When** elle affiche les options de contexte
**Then** les noms sont exploitables pour selection utilisateur
**And** la liste retournee permet une selection explicite cote UI sans mode implicite concurrent
