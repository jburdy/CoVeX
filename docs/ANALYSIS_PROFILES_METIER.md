# Profils d'analyse CoVeX - guide métier

## Objectif

Ce document aide un expert métier non technique a comprendre ce qu'est un
profil d'analyse CoVeX et a modifier correctement
`config/analysis_profiles.yaml`.

Dans ce fichier, chaque entree sous `profiles:` correspond a un profil, par
exemple `tickets_support_it:` ou `demandes_achat:`.

Attention : dans l'implementation actuelle, le champ principal des critères
s'appelle `coverage_item` et non `criteria`.

## Idee simple

Un profil d'analyse est une grille de lecture pour un type de document.

Exemples :

- un ticket support IT n'attend pas les mêmes informations qu'une demande
  d'achat ;
- un compte-rendu d'intervention n'attend pas les mêmes informations qu'un
  suivi projet ;
- chaque profil dit a CoVeX ce qu'il faut chercher dans le texte.

Le système ne choisit pas le profil tout seul : l'API et le playground doivent
envoyer un `profile_id` explicite.

## Comment CoVeX utilise un profil aujourd'hui

1. L'utilisateur ou le playground choisit un `profile_id`.
2. Le backend charge le profil correspondant dans
   `config/analysis_profiles.yaml`.
3. CoVeX construit un prompt a partir du `name`, de la `description` et de la
   liste `coverage_item`.
4. Les `le_few_shot`, s'ils existent, sont aussi transformes en
   exemples structures pour aider l'extraction.
5. Le moteur retourne des extractions dont CoVeX deduit les
   `covered_elements` et les `missing_elements`.
6. Le backend calcule un score pondere sur 100.
7. Le backend produit la décision finale.

Regle de décision actuelle :

- `KO` si `score <= 30` ;
- `PARTIEL` si `score <= 70` ou s'il reste au moins un critère manquant ;
- `OK` seulement si `score > 70` et qu'aucun critère n'est manquant.

Point important : les poids influencent le score, mais un critère manquant
empeche quand même d'obtenir `OK` dans l'implementation actuelle, même si son
poids est faible.

## Anatomie d'un profil

Exemple minimal realiste :

```yaml
profiles:
  demandes_subvention:
    name: "Demande de subvention"
    description: "Analyse des demandes de subvention associative"
    inference_engine_key: "remote_groq_llama31_8b_instant"
    le_few_shot:
      - text: "L'association ABC demande 10000 CHF pour un projet jeunesse."
        extractions:
          - criterion_id: "association"
            extraction_text: "L'association ABC"
          - criterion_id: "budget"
            extraction_text: "10000 CHF"
    coverage_item:
      - id: "association"
        expected_info: "Association ou porteur de la demande clairement identifie."
        weight: 0.25
      - id: "projet"
        expected_info: "Projet ou action financee clairement decrite."
        weight: 0.25
      - id: "budget"
        expected_info: "Montant demande ou budget exploitable."
        weight: 0.25
      - id: "calendrier"
        expected_info: "Date ou periode de realisation."
        weight: 0.25
```

Sens des champs :

- `demandes_subvention` : c'est le `profile_id`. Il identifie le profil de
  maniere stable dans l'API, le playground, le dataset et les scripts.
- `name` : c'est le libelle lisible du profil.
- `description` : c'est le resume metier du cas d'usage ; il est aussi utilise
  dans le prompt envoye au moteur.
- `coverage_item` : c'est la liste des criteres de couverture.
- `coverage_item[].id` : identifiant canonique du critere.
- `coverage_item[].expected_info` : description de ce qu'il faut trouver dans le
  texte pour considerer le critere comme couvert.
- `coverage_item[].weight` : poids utilise dans le calcul du score.
- `le_few_shot` : exemples optionnels montrant au moteur quel extrait de
  texte doit etre rattaché a quel critere.
- `le_few_shot[].criterion_id` : identifiant du critere auquel
  l'extraction d'exemple se rattaché.
- `inference_engine_key` : moteur par defaut pour ce profil.

## Ce que le code valide reellement

Le backend accepte un profil seulement si :

- le fichier contient une racine `profiles:` ;
- chaque profil contient `name`, `description` et `coverage_item` ;
- `coverage_item` contient au moins un element ;
- chaque element de `coverage_item` contient un `id`, un `expected_info` et un
  `weight` ;
- chaque `weight` est strictement superieur a `0` et inferieur ou egal a `1` ;
- si `le_few_shot` est present, chaque exemple contient un `text`
  non vide ;
- si des extractions d'exemple sont presentes, chaque extraction contient un
  `criterion_id` et un `extraction_text` non vides ;
- si `inference_engine_key` est present, sa valeur est une chaine non vide ;
- les champs inattendus sont refuses dans les profils, les criteres, les
  exemples et les extractions d'exemple.

## Ce que le code ne valide pas automatiquement

Les points suivants sont importants, mais ils ne sont pas controles par le code
actuel :

- deux criteres d'un meme profil peuvent encore partager le meme `id` sans etre
  bloques a la charge ;
- la somme des `weight` n'est pas verifiee ;
- le format du `profile_id` n'est pas impose ;
- les `criterion_id` presents dans `le_few_shot` ne sont pas verifies
  contre la liste `coverage_item` ;
- `inference_engine_key` n'est pas compare a `config/inference_engines.yaml`
  lors du chargement du profil ;
- les doublons de cles YAML ne sont pas explicitement rejetes par le chargeur
  actuel.

En pratique, il faut donc relire le fichier avec attention meme si le schema se
charge sans erreur.

## Bien choisir le `profile_id`

Le `profile_id` est un identifiant stable. Il est reutilise dans l'API, dans le
playground, dans `datasets/golden_dataset.jsonl` et dans plusieurs scripts de
validation.

Bonnes pratiques :

- utiliser des mots simples, courts et stables ;
- preferer `snake_case` en minuscules ;
- eviter les espaces, les accents et la ponctuation decorative dans cet
  identifiant technique ;
- ne pas renommer un `profile_id` existant juste pour changer le libelle
  visible : dans ce cas, modifier `name` et garder le `profile_id`.

## Bien choisir les criteres `coverage_item`

Un bon critere correspond a une information metier utile pour juger la qualite
ou la completude d'un texte.

Un critere utile est :

- observable dans le texte ;
- assez precis pour eviter les interpretations floues ;
- distinct des autres criteres ;
- utile a la decision metier.

Exemples de bons `id` :

- `adresse`
- `budget`
- `urgence`
- `technicien`

Exemples d'`id` a eviter :

- `info`
- `autre`
- `details_importants`
- `a_preciser`

Conseil pratique : si un critere est subtil ou si le moteur a tendance a mal le
reconnaitre, ajouter un ou deux `le_few_shot` bien choisis aide plus
qu'un long commentaire technique.

## Comment repartir les poids

Le score est calcule ainsi :

```text
score = somme des poids couverts / somme des poids du profil * 100
```

Exemples simples :

- 4 criteres de meme importance : `0.25` chacun ;
- 1 critere majeur et 3 criteres secondaires : `0.4`, `0.2`, `0.2`, `0.2`.

Conseils pratiques :

- si vous debutez, commencez par des poids egaux ;
- visez idealement une somme totale de `1.0` meme si ce n'est pas impose par le
  code ;
- gardez une logique facile a expliquer en revue metier ;
- souvenez-vous qu'un critere manquant empeche `OK`, quel que soit son poids.

## Modifier un profil existant ou en creer un nouveau

Modifiez un profil existant si :

- le type de document reste le meme ;
- la decision metier attendue reste globalement la meme ;
- vous ajustez surtout le vocabulaire, un critere ou la priorisation.

Creez un nouveau profil si :

- le document correspond a un autre cas d'usage ;
- les informations attendues changent fortement ;
- la grille de lecture metier n'est plus la meme ;
- vous avez besoin d'un moteur par defaut differenciant et assume.

## Ce qu'il vaut mieux ne pas modifier seul

Les champs `inference_engine_key` reste un champ technique.

En pratique :

- gardez `inference_engine_key` si vous n'avez pas de raison claire de le
  changer ;
- si vous le changez, verifiez que la cle existe bien dans
  `config/inference_engines.yaml`.

## Effet pratique d'une modification

Le backend charge `config/analysis_profiles.yaml` une fois puis garde cette
configuration en memoire.

Concretement :

- une modification du YAML n'est pas reprise automatiquement par une API deja
  lancee ;
- il faut redémarrer le backend pour prendre en compte un changement ;
- si le fichier est invalide au prochain chargement, les routes qui dependent
  des profils peuvent echouer.

Le playground peut aussi necessiter un rafraichissement de page pour relire ses
options locales et ses exemples.

## Checklist avant validation

Avant d'enregistrer une modification, verifier que :

- le `profile_id` est stable et clairement nomme ;
- chaque critere `coverage_item` est explicite et non redondant ;
- les poids sont coherents et totalisent idealement `1.0` ;
- les `le_few_shot`, s'il y en a, correspondent a de vrais cas utiles ;
- `inference_engine_key` existe bien si vous l'avez change ;
- le backend a ete redémarré puis controle via un smoke
  test.

## Resume en une phrase

Un bon profil d'analyse CoVeX est une grille metier claire et stable, decrite
avec `coverage_item`, des critères explicites, des poids lisibles et, si
nécessaire, quelques exemples d'extraction bien choisis.
