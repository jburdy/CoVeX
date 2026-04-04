# select_engines_by_cost

## Objet

Petit POC académique pour tester une liste fixe de moteurs sur `datasets/golden_dataset.jsonl` et identifier, sans rien modifier dans la config, le moteur le moins cher qui passe à 100% pour chaque profil.

## Fichiers liés

- Script: `tools/research/select_engines_by_cost.py`
- Liste des moteurs autorisés: `tools/research/engine_candidates.txt`
- Résultats persistants: `artifacts/evaluation/engine_selection_results.csv`
- Rapport lisible mobile: `artifacts/evaluation/engine_selection_report.md`

## Simplifications volontaires

- Plus de CLI longue: dataset, config, timeout, résultats et liste des moteurs sont hardcodés dans le script.
- Plus de mode `--only-local`.
- Les moteurs testés sont uniquement ceux présents dans `tools/research/engine_candidates.txt`.
- Le timeout par inférence est fixé à 30 secondes.

## Fonctionnement

- Le script lit les profils depuis `config/analysis_profiles.yaml` mais ne l'écrit jamais.
- Il charge le dataset depuis `datasets/golden_dataset.jsonl`.
- Il lit la liste des moteurs à tester depuis `tools/research/engine_candidates.txt`.
- Il teste moteur par moteur, puis tous les profils encore non résolus pour ce moteur.
- Chaque tentative est écrite dans `artifacts/evaluation/engine_selection_results.csv` pour permettre la reprise.
- Le CSV expose notamment `status`, `elapsed_total_sec`, `first_failed_case_id`, `expected_decision` et `actual_decision` pour être lisible sans ambiguïté.
- L'évaluation se fait maintenant par bandes de score avec marge, et non plus par comparaison stricte du label `KO` / `PARTIEL` / `OK`.
- Si une tentative existe déjà pour un couple `(profile_id, engine_key)`, elle est réutilisée.
- La selection finale prend, pour chaque profil, le premier moteur de la liste triée par coût qui a un succès complet.
- Si aucun moteur ne passe pour un profil, le `inference_engine_key` existant est conservé.

## État actuel

- La liste de moteurs cibles dépend directement du contenu courant de
  `tools/research/engine_candidates.txt`.
- Le script reste un POC de bench et non un outil produit.
- Le CSV sert à la fois de persistence de reprise et d'historique de comparaison.

## Commande

```bash
uv run --project backend python tools/research/select_engines_by_cost.py
```

## Notes pour un futur LLM

- Si tu veux tester d'autres moteurs, ajoute simplement une ligne par moteur dans `tools/research/engine_candidates.txt`.
- Garde le timeout a 30 secondes max par inférence sauf demande explicite contraire.
- Preserve l'approche moteur-par-moteur pour éviter de recharger les modèles trop souvent.
- Garde le script simple: ici on privilégie la lisibilité et l'expérimentation rapide.
