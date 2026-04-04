# Configuration des Moteurs d'Inférence (`inference_engines.yaml`)

Ce document décrit la structure et le rôle du fichier de configuration `config/inference_engines.yaml`. Ce fichier centralise la définition de tous les modèles de langage (LLM) utilisables par l'application CoVeX, qu'ils soient exécutés localement (via Ollama) ou hébergés à distance (via des API tierces comme Groq, OpenRouter, Google, etc.).

## Structure Globale

Le fichier YAML principal est composé de deux clés à la racine :

- `default_inference_engine` (chaîne de caractères) : Identifiant de la clé du moteur d'inférence à utiliser par défaut si aucun n'est spécifié. (ex: `"remote_groq_llama31_8b_instant"`).
- `inference_engines` (dictionnaire) : Contient la déclaration détaillée de chaque moteur d'inférence disponible.

## Paramètres d'un Moteur d'Inférence

Chaque entrée sous `inference_engines` représente un moteur. La clé de l'entrée est l'identifiant interne utilisé dans le code et les profils d'analyse.

### Champs Communs

- `type` (obligatoire) : Définit la nature du moteur. Valeurs acceptées : `"local"` ou `"remote"`.
- `model` (obligatoire) : Le nom exact du modèle tel qu'attendu par l'API cible (ex: `"llama3.1:8b"` pour Ollama, `"gemini-3.1-flash-lite-preview"` pour Google).
- `justification` (recommandé) : Une brève description justifiant le choix de ce modèle (compromis coût/performance, capacité de contexte, etc.).
- `cost_score` (recommandé) : Un score relatif entier estimant le coût ou la lourdeur du modèle. Plus la valeur est élevée, plus le modèle est "coûteux" (voir section détaillée ci-dessous). Optionnel dans le schema Pydantic (`int | None`), mais attendu pour que les scripts d'evaluation fonctionnent correctement.
- `base_url` (recommandé) : L'URL de base de l'API compatible (ex: `"http://127.0.0.1:11434"`, `"https://openrouter.ai/api/v1"`). Optionnel dans le schema Pydantic ; pour les moteurs locaux sans `base_url`, le backend replie sur `http://127.0.0.1:11434` par defaut.

### Champs Spécifiques (Local)

- `timeout_sec` (optionnel) : Délai d'expiration de la requête en secondes (ex: `120`). Utile pour les modèles locaux qui peuvent mettre du temps à générer ou charger en mémoire.

### Champs Spécifiques (Distant / Remote)

- `auth_env_var` (obligatoire pour `remote`) : Le nom de la variable d'environnement contenant la clé d'API requise pour l'authentification (ex: `"COVEX_OPENROUTER_API_KEY"`). Cette conception permet de ne pas coder en dur les secrets dans le YAML.

## La Notion de `cost_score`

Le paramètre `cost_score` est un indicateur clé utilisé par CoVeX pour ordonner ou comparer les modèles.

- **Pour les modèles locaux (`local`)** : Le score est une estimation abstraite basée sur la taille des poids du modèle (paramètres), l'occupation mémoire prévue et la latence sur une machine de développement standard. (ex: Un modèle 4B aura un score de `7`, un modèle 14B un score de `18`).
- **Pour les modèles distants (`remote`)** : Le score est une approximation relative dérivée de la tarification réelle des API (prix par million de tokens en entrée/sortie). (ex: Groq Llama 3.1 8B a un score de `1`, tandis que des modèles plus avancés ont des scores autour de `20` à `28`).

L'échelle permet une comparaison ordonnée du moins cher/léger au plus cher/lourd.

## Exemples

### Modèle Local (Ollama)

```yaml
local_llama31:
  type: "local"
  model: "llama3.1:8b"
  justification: "Base locale économique et stable pour extraction simple."
  cost_score: 10
  base_url: "http://127.0.0.1:11434"
  timeout_sec: 120
```

### Modèle Distant (OpenRouter)

```yaml
remote_openrouter_mistral_small_32_24b:
  type: "remote"
  model: "mistralai/mistral-small-3.2-24b-instruct"
  justification: "Bon compromis distant entre prix contenu et sorties régulières."
  cost_score: 3
  base_url: "https://openrouter.ai/api/v1"
  auth_env_var: "COVEX_OPENROUTER_API_KEY"
```

## Bonnes Pratiques

- Ne placez jamais de clés d'API directement dans ce fichier. Utilisez toujours `auth_env_var` et le fichier `.env` local.
- Lors de l'ajout d'un nouveau modèle, assurez-vous d'évaluer de manière cohérente son `cost_score` par rapport aux modèles déjà existants.
- Les identifiants (`keys`) sous `inference_engines` doivent rester uniques et descriptifs.
