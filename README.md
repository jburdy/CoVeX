# CoVeX

Prototype d'analyse de textes métier base sur des profils explicites.

## Structure

```text
CoVeX/
├── backend/
│   ├── src/
│   │   ├── main.py
│   │   ├── settings.py
│   │   ├── analysis.py
│   │   ├── analysis_profiles_config.py
│   │   └── inference.py
│   └── tests/
├── playground/
│   └── src/
│       ├── app.py
│       ├── api_client.py
│       └── playground.py
├── config/
│   ├── analysis_profiles.yaml
│   └── inference_engines.yaml
├── datasets/
│   └── golden_dataset.jsonl
├── docs/
│   ├── ARCHITECTURE.md
│   └── ANALYSIS_PROFILES_METIER.md
├── tools/
│   ├── validation/
│   │   ├── api_smoke.py
│   │   └── backend_runner.py
│   ├── evaluation/
│   │   ├── engine_case_store.py
│   │   ├── evaluation_models.py
│   │   └── run_dataset_evaluation.py
│   └── research/
│       ├── engine_candidates.txt
│       ├── render_engine_selection_report.py
│       ├── select_engines_by_cost.md
│       └── select_engines_by_cost.py
├── artifacts/
│   └── evaluation/
├── sAPI_kill.sh
├── sAPI_start.sh
├── sPlayGround_start.sh
└── README.md
```

## Lancer le projet

Initialisation depuis la racine du depot :

```bash
cp .env.example .env
uv sync --all-groups --project backend
uv sync --all-groups --project playground
```

Lancement recommande depuis la racine du depot :

```bash
uv run --project backend uvicorn main:app --app-dir backend/src --reload
uv run --project playground python playground/src/app.py
```

Wrappers shell disponibles :

- `./sAPI_start.sh` lance le backend en mode reload.
- `./sAPI_kill.sh` arrete un backend actif sur le port `8000`.
- `./sPlayGround_start.sh` lance le playground avec `COVEX_PLAYGROUND_RELOAD=1`.

URLs locales par defaut :

- API : `http://127.0.0.1:8000`
- UI : `http://127.0.0.1:8080`

## Validation

Validation backend :

```bash
cd backend && uv run ruff check src tests && uv run pytest
```

Validation playground :

```bash
cd playground && uv run ruff check src
```

Scripts manuels utiles depuis la racine du depot :

```bash
uv run --project backend python tools/validation/api_smoke.py
uv run --project backend python tools/evaluation/run_dataset_evaluation.py --limit 3
uv run --project backend python tools/research/select_engines_by_cost.py
```

- `tools/validation/` regroupe des scripts de verification HTTP et leurs
  helpers.
- `tools/evaluation/` rejoue le dataset contre l'API.
- `tools/research/` contient des scripts exploratoires, hors chemin de
  validation principal.
- Les artefacts generes vont dans `artifacts/evaluation/`, notamment le cache
  case-level `engine_case_results.jsonl`, la synthese
  `engine_selection_results.csv`, le rapport Markdown et les `engine_worst_cases`.
- Les visualisations HTML LangExtract generees pendant une analyse sont
  sauvegardees dans `artifacts/langextract_html/`.

## Fonctionnement

- Toute analyse requiert un `profile_id` explicite ; il n'y a pas de routage
  automatique.

- `POST /analyze` retourne `score`, `decision`, `justification`,
  `covered_elements`, `missing_elements`, `extractions` et quelques metadonnees
  techniques.
- Le playground lit les profils directement depuis `config/analysis_profiles.yaml`.
- Le dataset `datasets/golden_dataset.jsonl` alimente les exemples du
  playground et les scripts d'evaluation.

## Configuration

- `config/analysis_profiles.yaml` contient les profils d'analyse, leurs
  `coverage_item`, leurs `le_few_shot` et, si besoin,
  `inference_engine_key`.
- `config/inference_engines.yaml` contient le moteur par defaut et le catalogue
  des moteurs locaux ou distants.
- Le moteur par defaut actuel est `remote_groq_llama31_8b_instant`.
- Le backend charge ces deux YAML au demarrage puis les garde en cache : apres
  modification, il faut redémarrer l'API pour prendre en compte les changements.

### Activer vite un provider distant de demo

- Pour utiliser le moteur distant par defaut actuel, renseigner
  `COVEX_GROQ_API_KEY` dans `.env`.
- Pour utiliser `remote_google_gemini25_flash`, renseigner `COVEX_GOOGLE_API_KEY`,
  puis selectionner ce moteur dans le playground ou le passer via
  `inference_engine`.
- Pour les autres moteurs distants, renseigner la variable indiquee par
  `auth_env_var` dans `config/inference_engines.yaml`.
- Si vous changez `config/inference_engines.yaml` ou
  `config/analysis_profiles.yaml`, redemarrez le backend puis rechargez le
  playground.

## Documentation

- Vue d'ensemble technique : `docs/ARCHITECTURE.md`
- Guide metier des profils : `docs/ANALYSIS_PROFILES_METIER.md`
- Artefacts BMAD : `_bmad-output/`
