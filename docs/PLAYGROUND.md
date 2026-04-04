# Documentation du Playground CoVeX

Le **Playground** est une interface utilisateur web (TUI) développée avec [NiceGUI](https://nicegui.io/). Il sert d'environnement de test et de validation pour l'API CoVeX, permettant aux utilisateurs d'interagir facilement avec les différents profils d'analyse et moteurs d'inférence (LLMs) sans avoir à écrire de requêtes HTTP manuellement.

## 1. Démarrer le Playground

Le Playground s'exécute dans son propre environnement Python isolé, défini par le projet `playground`.

Depuis la racine du dépôt, lancez la commande suivante :

```bash
uv run --project playground python src/app.py
```

L'interface sera alors accessible dans votre navigateur à l'adresse par défaut : **http://127.0.0.1:8080**

*(Note : Assurez-vous que le backend API tourne simultanément sur `http://127.0.0.1:8000` pour que le Playground puisse analyser les textes, car il agit comme un client de cette API).*

## 2. Fonctionnalités et Pages

L'application est divisée en trois pages principales :

### A. La page Playground (Route : `/`)
C'est l'interface principale de test des requêtes d'analyse. 

**Fonctionnalités :**
- **Sélection du profil d'analyse :** Un menu déroulant permet de choisir parmi les profils configurés dans le backend (ex: compte-rendu médical).
- **Moteur d'inférence (Optionnel) :** Permet de surcharger le LLM par défaut pour le profil sélectionné et d'en tester un autre (local ou distant).
- **Texte source :** Une zone de texte libre pour coller le contenu à analyser.
- **Exemples de saisie :** Une section extensible propose des exemples pré-remplis issus du "Golden Dataset" pour tester rapidement des cas types (OK, PARTIEL, KO).
- **Résultats de l'analyse :** Après soumission, la page affiche :
  - **Score** : De 0 à 100.
  - **Décision** : `OK` (vert), `PARTIEL` (orange), ou `KO` (rouge).
  - **Éléments couverts et extraits** : Tableau listant les critères trouvés et la citation exacte extraite du texte.
  - **Éléments manquants** : Liste des critères non trouvés.
  - **Métadonnées techniques** : Informations sur l'usage des tokens (entrée/sortie), la latence de l'API et le modèle exact utilisé par le fournisseur.



### B. La page Analysis Profiles (Route : `/analysis-profiles`)
Cette page affiche la liste des profils d'analyse disponibles, tels qu'ils sont chargés depuis le fichier de configuration `config/analysis_profiles.yaml`. Pour chaque profil, elle présente : l'identifiant, la description, le moteur d'inférence par défaut (`inference_engine_key`), les critères de couverture (`coverage_item`) avec leur poids, et les exemples d'extraction (`le_few_shot`) si présents. La page est en lecture seule.

### C. La page Golden Dataset (Route : `/golden-dataset`)
Cette page permet de consulter le jeu de données de référence (le *Golden Dataset*). Ce jeu de données est stocké au format `.jsonl` (JSON Lines).

**Fonctionnalités :**
- **Visualisation :** Un tableau récapitule toutes les entrées du dataset (ID, Profil, Décision attendue, Tags, Texte).

**Important :** Cette page est en **lecture seule**. Il n'existe pas de formulaire d'édition ou de création intégré au playground. Pour modifier le dataset, il faut éditer directement le fichier `datasets/golden_dataset.jsonl`. Le tag `playground` sur une entrée lui permet d'apparaître dans les exemples rapides de la page principale.

## 3. Architecture Technique

- **Framework UI :** Le Playground utilise **NiceGUI**, un framework Python permettant de construire des interfaces web sans écrire de HTML/JS.
- **Client API (`api_client.py`) :** Le Playground ne fait aucune inférence par lui-même. Il communique de manière asynchrone avec le backend FastAPI (`POST /analyze`).
- **Rechargement à chaud (Hot-Reload) :** Pour les développeurs, le rechargement automatique de l'UI à chaque modification du code peut être activé en définissant la variable d'environnement `COVEX_PLAYGROUND_RELOAD=1`.
