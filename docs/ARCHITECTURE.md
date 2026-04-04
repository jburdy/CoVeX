# Architecture CoVeX

## Vue d'ensemble

CoVeX est un monorepo Python organise autour de deux applications :

- `backend/` : API FastAPI qui expose l'analyse.
- `playground/` : interface NiceGUI de demonstration.
- `config/` : configuration partagee des profils et des moteurs.
- `datasets/golden_dataset.jsonl` : corpus local utilise pour les exemples du
  playground et pour les scripts d'évaluation manuelle.
- `tools/` : scripts manuels de smoke test, d'évaluation et de recherche.

Le prototype actuel n'a ni base de données, ni authentification, ni persistance
utilisateur. Toute analyse doit fournir un `profile_id` explicite : il n'y a
pas de routage automatique des profils.

## Backend

`backend/src/main.py` assemble l'application FastAPI :

- charge le `.env` racine le plus proche ;
- configure les logs ;
- enregistre le routeur `analysis` ;
- expose `GET /` ;
- transforme les erreurs de validation FastAPI en `400` stable.

Modules principaux :

- `backend/src/analysis.py` : route `POST /analyze`, orchestration de
  l'analyse, calcul du score et de la décision, journalisation detaillee.
- `backend/src/analysis_profiles_config.py` : chargement de
  `config/analysis_profiles.yaml` et construction des profils runtime.
- `backend/src/inference.py` : chargement de
  `config/inference_engines.yaml`, resolution du moteur, appel `langextract`,
  normalisation des extractions.
- `backend/src/settings.py` : chargement de l'environnement et configuration
  des loggers applicatifs.

### Contrat HTTP

- `GET /` retourne `{"status": "ok", "service": "covex-backend-bootstrap"}`.

- `POST /analyze` attend `text` et `profile_id`, et accepte en option
  `inference_engine`.
- La réponse de `POST /analyze` contient `score`, `decision`, `justification`,
  `profile_used`, `covered_elements`, `missing_elements`, `extractions`, ainsi
  que `latency_sec` et `model_used` quand ces informations sont disponibles.

Codes d'erreur observes :

- `400` : requête invalide.
- `404` : profil inconnu.
- `503` : moteur d'inférence indisponible.
- `500` : autre erreur interne, y compris une configuration moteur invalide.

### Flux d'une analyse

1. Validation du payload HTTP.
2. Chargement du profil depuis `config/analysis_profiles.yaml`.
3. Chargement de la configuration des moteurs depuis
   `config/inference_engines.yaml`.
4. Resolution du moteur : surcharge de requête, sinon moteur du profil, sinon
   moteur par defaut.
5. Construction d'un prompt a partir de `name`, `description` et
   `coverage_item`, puis injection des `le_few_shot`.
6. Execution de `langextract` via un moteur Ollama local ou un endpoint distant
   OpenAI-compatible.
7. Production de `covered_elements`, `missing_elements` et `extractions`.
8. Calcul du score pondere sur 100 et de la décision finale.

Regle de décision actuelle :

- `KO` si `score <= 30`.
- `PARTIEL` si `score <= 70` ou s'il reste au moins un élément manquant.
- `OK` seulement si `score > 70` et qu'aucun élément n'est manquant.

### Runtime et observabilite

- Les YAML `config/analysis_profiles.yaml` et `config/inference_engines.yaml`
  sont charges une fois puis mis en cache en mémoire dans le backend.
- Il n'y a pas de hot reload applicatif de ces deux fichiers dans
  l'implementation actuelle : un redémarrage de l'API est nécessaire pour
  prendre en compte une modification.
- Les logs applicatifs sont ecrits dans `logs/app-YYYY-MM-DD.log`.
- Les traces detaillees d'analyse sont ecrites dans
  `logs/bee-YY-MM-DD-<engine>-<profile>.log`.
- Hors production, ces traces detaillees sont toujours emises. En production,
  elles dependent de `COVEX_PROMPT_TRACE_ENABLED`.

## Playground

Le playground actuel repose sur trois fichiers :

- `playground/src/app.py` : point d'entree NiceGUI et page `/`.
- `playground/src/playground.py` : construction UI, chargement des exemples,
  validation locale, soumission et rendu du résultat.
- `playground/src/api_client.py` : client HTTP minimal vers le backend.

Comportement actuel :

- le playground lit localement `config/analysis_profiles.yaml` ;
- il lit aussi `config/inference_engines.yaml` pour proposer les moteurs ;
- il synchronise automatiquement le moteur selectionne avec
  `inference_engine_key` du profil quand un profil est choisi ;
- il charge les exemples du fichier `datasets/golden_dataset.jsonl` portant le
  tag `playground` ;
- il envoie `text`, `profile_id` et, si besoin, `inference_engine` a
  `POST /analyze` ;
- il affiche le score, la décision, les éléments couverts avec leurs
  extractions, les éléments manquants et quelques métadonnées techniques.

Important :

- la page `/golden-dataset` permet de consulter et editer le golden dataset local ;

- il n'existe pas de fichier `playground/src/golden_dataset_editor.py` ;
- il n'y a pas de dossier `playground/tests/` dans le dépôt actuel.

## Configuration

### `config/analysis_profiles.yaml`

Chaque entree sous `profiles:` decrit un profil d'analyse avec :

- `name` ;
- `description` ;
- `coverage_item` ;
- `le_few_shot` optionnels ;
- `inference_engine_key` optionnel.

### `config/inference_engines.yaml`

Le fichier definit :

- `default_inference_engine` ;
- `inference_engines.<key>.type` (`local` ou `remote`) ;
- `model` ;
- `justification` et `cost_score` eventuels ;
- `base_url`, `auth_env_var`, `timeout_sec` eventuels.

Le backend lit dynamiquement la variable d'authentification indiquee par
`auth_env_var`. Les exemples actifs du dépôt utilisent notamment
`COVEX_GROQ_API_KEY`, `COVEX_OPENROUTER_API_KEY` et `COVEX_GOOGLE_API_KEY`.

Variables d'environnement effectivement lues par le code :

- `APP_ENV` ;
- `LOG_LEVEL` ;
- `COVEX_PROMPT_TRACE_ENABLED` ;
- les variables de secret referencees par `auth_env_var` ;
- `COVEX_PLAYGROUND_RELOAD` pour le mode reload du playground.

## Tests et scripts

Tests backend présents dans le dépôt :

- `backend/tests/test_backend_smoke.py`
- `backend/tests/test_api_error_visibility.py`
- `backend/tests/test_config_yaml.py`
- `backend/tests/test_analysis_logging.py`
- `backend/tests/test_inference_errors.py`
- `backend/tests/test_engine_selection_cache.py`
- `backend/tests/analysis_profiles/` (suite de tests dédiés aux profils)
- `backend/tests/common/test_settings_logging.py`

Scripts manuels utiles :

- `tools/validation/api_smoke.py` : smoke test HTTP du backend ; accepte
  `--brain-engine` pour forcer un moteur sur tous les appels `POST /analyze`.
- `tools/validation/backend_runner.py` : demarrage, attente et arret du backend
  pour les scripts manuels.
- `tools/evaluation/run_dataset_evaluation.py` : rejeu du golden dataset contre
  l'API backend.
- `tools/research/select_engines_by_cost.py` : évaluation exploratoire des
  moteurs en important directement les modules backend depuis la racine du
  dépôt ; le script ecrit ses résultats dans
  `artifacts/evaluation/engine_selection_results.csv` et génère automatiquement
  le rapport Markdown `artifacts/evaluation/engine_selection_report.md` en fin
  d'exécution, sans modifier `config/analysis_profiles.yaml`.
- `tools/research/render_engine_selection_report.py` : génération du rapport
  Markdown à partir du CSV d'évaluation ; aussi appelé automatiquement par
  `select_engines_by_cost.py`, mais peut être exécuté séparément si besoin.

Le chemin valide au quotidien reste surtout :

- `ruff check` et `pytest` côté backend ;
- `tools/validation/api_smoke.py` pour un controle HTTP de bout en bout ;
- `tools/evaluation/run_dataset_evaluation.py` pour rejouer le dataset contre
  l'API.

Les scripts de `tools/research/` sont des outils exploratoires et ne font pas
partie du chemin runtime valide par les tests actuels, même s'ils sont de
nouveau executables depuis la racine du dépôt.

## Hors scope actuel

- pas d'authentification ;
- pas de base de données ;
- pas de persistance utilisateur ;
- pas de routage automatique des profils ;
- pas d'editeur de dataset intégré au playground.

Le projet reste un prototype centre sur la clarte du flux d'analyse plutot que
sur une architecture produit complete.
