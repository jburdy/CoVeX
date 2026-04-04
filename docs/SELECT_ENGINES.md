# Documentation de l'Outil de Recherche `select_engines_by_cost.py`

Le script `select_engines_by_cost.py` est un outil de **recherche et d'évaluation** qui permet de tester et de classer les différents moteurs d'inférence configurés dans CoVeX par rapport au jeu de données de référence ("Golden Dataset").

L'objectif principal du script est d'identifier, pour chaque profil d'analyse (ex: résumé médical, extraction RH...), le moteur le moins cher (le plus petit `cost_score`) capable d'atteindre un certain seuil de qualité (taux de concordance ou *band match rate*).

## 1. Comment l'exécuter

Le script doit être exécuté depuis la racine du dépôt en utilisant le projet `backend` :

```bash
uv run --project backend python tools/research/select_engines_by_cost.py
```

### Options de ligne de commande :
- `--threshold <float>` : Le seuil minimal de réussite (band match rate) requis pour qu'un moteur soit considéré comme qualifié. (Défaut : `0.9` soit 90%).
- `--remote-workers <int>` : Le nombre de requêtes parallèles à envoyer aux APIs distantes (Défaut : `4`). *Note : l'évaluation des moteurs locaux se fait toujours séquentiellement pour éviter la saturation d'Ollama.*
- `--refresh` : Force le ré-exécution de tous les tests, même si le résultat est déjà présent dans le cache.
- `--exhaustive` : Force le test de tous les moteurs candidats sur tous les profils, même si un moteur moins coûteux a déjà atteint le seuil de qualification.

## 2. Principe de Fonctionnement

1. **Chargement des données** : Le script lit le Golden Dataset (`datasets/golden_dataset.jsonl`) et charge les profils d'analyse.
2. **Liste des candidats** : Il lit le fichier `tools/research/engine_candidates.txt` pour savoir quels moteurs évaluer.
3. **Tri par coût** : Les moteurs candidats sont triés par leur `cost_score` croissant (du moins cher au plus cher).
4. **Évaluation (Stratégie "Early Exit")** : 
   - Par défaut, pour un profil donné, le script teste les moteurs en partant du moins cher. 
   - Dès qu'un moteur atteint ou dépasse le `threshold` de qualité, le script arrête d'évaluer les moteurs plus coûteux pour ce profil (sauf si `--exhaustive` est passé).
5. **Mise en cache** : Les résultats sont mis en cache par "empreinte" (profil, texte, paramètres, moteur). Si un cas de test n'a pas changé, le script réutilise le résultat du cache sans rappeler l'API LLM, économisant du temps et de l'argent.

## 3. Fichiers et Artefacts Générés

L'exécution du script génère ou met à jour plusieurs fichiers dans le dossier `artifacts/evaluation/` :

- **`engine_case_results.jsonl`** : Le cache "case-level". Il contient le résultat brut de chaque requête d'inférence jamais exécutée.
- **`engine_selection_results.csv`** : Un fichier CSV synthétique reprenant les statistiques globales pour chaque couple (profil, moteur) testé (taux de réussite, latence moyenne, coût, etc.).
- **`engine_worst_cases.csv`** : Un rapport listant les textes du jeu de données qui échouent systématiquement, peu importe le moteur utilisé. Très utile pour repérer des problèmes dans les prompts ou le dataset.
- **`engine_selection_report.md`** : Un rapport lisible (Markdown) généré automatiquement, formaté pour la lecture humaine, détaillant le palmarès et le meilleur moteur retenu par profil.

## 4. Gestion des Erreurs Systémiques

Le script détecte les "erreurs systémiques" (comme une clé d'API invalide, des erreurs `connection refused` pour Ollama, etc.). Si une erreur systémique survient :
- Le script arrête immédiatement de tester le moteur en question pour éviter le gaspillage de requêtes.
- Les erreurs systémiques ne sont pas écrites dans le cache persistant, ce qui permet de relancer le script de manière fluide une fois le problème de connexion résolu.

## 5. Lecture analytique des résultats

Pour une synthèse rédigée à destination d'un rapport académique sur l'impact des
modèles selon les profils métier, voir `docs/IMPACT_MODELES_PROFILS.md`.
