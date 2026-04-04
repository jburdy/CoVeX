# Référence de l'API CoVeX

Ce document décrit l'API REST exposée par le backend de l'application CoVeX (FastAPI). L'API permet de lister les profils d'analyse disponibles et d'exécuter une analyse métier sur un texte donné.

Par défaut, le backend s'exécute sur `http://127.0.0.1:8000`.

---

## 1. Vérification de l'état du service

Vérifie que le service est démarré et fonctionnel.

**Requête :**
`GET /`

**Réponse (200 OK) :**
```json
{
  "status": "ok",
  "service": "covex-backend-bootstrap"
}
```

---


## 2. Analyser un texte

Exécute une analyse sur un texte donné en utilisant un profil d'analyse spécifique. Fait appel au moteur d'inférence (LLM) sous-jacent.

**Requête :**
`POST /analyze`

**En-têtes :**
- `Content-Type: application/json`

**Corps de la requête :**

| Champ | Type | Obligatoire | Description |
| :--- | :--- | :--- | :--- |
| `text` | string | Oui | Le texte brut à analyser (ex: contenu d'un document ou d'une retranscription). Doit contenir au moins 1 caractère. |
| `profile_id` | string | Oui | L'identifiant du profil d'analyse à utiliser (ex: `"medical_summary"`). |
| `inference_engine` | string | Non | Surcharge la clé du moteur d'inférence configuré par défaut (ex: `"remote_groq_llama31_8b_instant"`). |

*Exemple de requête :*
```json
{
  "text": "Le patient Jean Dupont s'est présenté ce jour pour des douleurs abdominales. Le diagnostic retenu est une appendicite aiguë.",
  "profile_id": "medical_summary",
  "inference_engine": "local_llama31"
}
```

**Réponse (200 OK) :**

La réponse contient le score calculé, la décision finale, ainsi que les éléments extraits par le LLM.

| Champ | Type | Description |
| :--- | :--- | :--- |
| `score` | integer | Score de couverture compris entre 0 et 100, calculé selon les poids des critères. |
| `decision` | string | Décision finale : `"OK"` (complet), `"PARTIEL"` (éléments manquants) ou `"KO"` (score insuffisant). |
| `justification` | string | Explication de la décision (liste des éléments manquants si applicable). |
| `profile_used` | string | Identifiant du profil utilisé. |
| `latency_sec` | float | (Optionnel) Temps d'exécution de l'inférence. |
| `model_used` | string | (Optionnel) Nom exact du modèle utilisé par le fournisseur. |
| `covered_elements`| array | Liste des IDs des critères considérés comme présents. |
| `missing_elements`| array | Liste des IDs des critères considérés comme absents. |
| `extractions` | array | Liste d'objets contenant l'extrait de texte précis justifiant la présence d'un critère. |

*Exemple de réponse :*
```json
{
  "score": 100,
  "decision": "OK",
  "justification": "Completude satisfaisante.",
  "profile_used": "medical_summary",
  "latency_sec": 1.45,
  "model_used": "llama3.1:8b",
  "covered_elements": [
    "patient_name",
    "diagnosis"
  ],
  "missing_elements": [],
  "extractions": [
    {
      "criterion_id": "patient_name",
      "extraction_text": "Jean Dupont"
    },
    {
      "criterion_id": "diagnosis",
      "extraction_text": "appendicite aiguë"
    }
  ]
}
```

**Erreurs possibles :**
- `400 Bad Request` : Si les champs obligatoires sont manquants ou mal formatés.
- `404 Not Found` : Si le `profile_id` demandé n'existe pas dans la configuration.
- `503 Service Unavailable` : Si le moteur d'inférence (LLM) est injoignable ou renvoie une erreur.
- `500 Internal Server Error` : Pour toute autre erreur interne non gérée.
