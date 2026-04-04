# Plan de migration profonde vers LangExtract (CoVeX)

> Note 2026-03-14: artefact BMAD historique. Certaines references internes
> (tests, modules, `criteria`, hot reload, pages playground) peuvent ne plus
> correspondre exactement au depot courant. Pour l'etat actuel, se fier a
> `README.md`, `docs/ARCHITECTURE.md` et `docs/ANALYSIS_PROFILES_METIER.md`.


Note d'archive: ce plan n'est plus d'actualite. Le depot a depuis supprime `langextract`, les feature flags d'extraction et `backend/src/extraction/`, et conserve uniquement le flux d'inference/scoring courant.

Date: 2026-02-18
Projet: CoVeX
Auteur: quick-dev (mode direct)

## 1) Objectif de la refonte

Remplacer la logique d'extraction/scoring fragile actuelle (matching lexical + parsing JSON heterogene) par une architecture robuste basee sur LangExtract, tout en preservant la stabilite des contrats API/UI et la politique de mecanisme retire provider.

Resultat attendu:
- extraction structuree fiable, traçable et testable,
- nettoyage des heuristiques legacy redondantes,
- separation claire des responsabilites (validation du contexte, extraction, scoring, exposition API),
- migration progressive sans rupture fonctionnelle.

## 2) Constat technique actuel

Points forts a conserver:
- architecture modulaire `analysis/*`, `inference/*`, `prompts/*`,
- gestion runtime des configs (`inference_engines.yaml`, `analysis_profiles.yaml`) avec reload a chaud,
- gestion d'erreurs API explicite et stable,
- metriques techniques exposees au playground (tokens, latence, prompt, model used).

Points faibles a corriger:
- extraction basee sur JSON provider parfois non robuste,
- mecanisme retire de simulation fonde sur matching de mots-cles,
- duplication de logique de tokenisation/extraction (`_extract_requirements` dans plusieurs modules),
- coupling trop fort entre prompt texte et logique d'extraction legacy,
- semantique metier limitee aux IDs de criteres.

## 3) Principes de migration

1. Compatibility-first: conserver le contrat `/analyze` durant toute la migration.
2. Strangler pattern: introduire une nouvelle couche extraction sans casser l'existant.
3. Feature-flag: bascule progressive legacy -> LangExtract par configuration.
4. Auditabilite: logs structurés et comparables avant/apres.
5. Test-first sur les interfaces critiques.

## 3.1) Gouvernance des donnees et journalisation (obligatoire)

Classification minimale:
- `S0 Public`: informations non sensibles.
- `S1 Interne`: informations techniques internes non personnelles.
- `S2 Sensible`: donnees metier potentiellement identifiantes.
- `S3 Critique`: PII, secrets, credentials, contenu utilisateur brut.

Regles de redaction:
- Interdiction de journaliser en clair tout champ `S3` (`user_text`, prompt complet, headers auth, payloads bruts provider).
- Pour `S2`, journalisation uniquement en forme reduite (hash, longueur, type, compteurs).
- Allowlist stricte des champs techniques persistants (status, latence, tokens agrégés, provider alias).

Retention et acces:
- Aucun log runtime sensible versionne dans Git.
- Retention courte (TTL) en stockage runtime hors repository.
- Acces restreint (least privilege) et traçabilite de consultation.

Controle qualite:
- Test automatique qui echoue si `user_text` ou payload brut apparait dans logs persistants.
- Verification CI interdisant la modification des fichiers de logs versionnes.

## 4) Architecture cible

### 4.1 Nouveau module `extraction`

Ajouter un namespace dedie:
- `backend/src/extraction/engine.py` (orchestration LangExtract)
- `backend/src/extraction/schemas.py` (resultats canoniques)
- `backend/src/extraction/config.py` (resolution du profil d'extraction)
- `backend/src/extraction/mappers.py` (mapping vers contrat interne CoVeX)
- `backend/src/extraction/errors.py` (erreurs extraction explicites)

### 4.2 Contrat interne canonique

Definir un resultat extraction unique, independant du provider:
- `entities`: liste d'objets extraits,
- `missing_entities`: ecarts structurels,
- `coverage_ratio`: ratio calcule de maniere deterministe,
- `trace`: provenance, offsets/source spans, modele utilise,
- `metrics`: latence/tokens normalises.

### 4.3 Integration `analysis`

`analysis/service.py` devient orchestrateur:
- validation contexte explicite (prompt/provider) conservee,
- appel moteur extraction (legacy ou LangExtract selon flag),
- calcul score/decision/justification via pipeline stable,
- retour `AnalysisResult` compatible.

## 5) Evolution des configurations

### 5.1 `analysis_profiles.yaml`

Faire evoluer chaque prompt d'une liste de criteres vers un profil d'extraction:
- conserver `criteria` pour retrocompatibilite initiale,
- ajouter section `extraction`:
  - `prompt_description`,
  - `classes` attendues,
  - `attributes` par classe,
  - `examples` few-shot,
  - `scoring_rules` (poids, obligations, contraintes).

### 5.2 `inference_engines.yaml`

Ajouter options necessaires LangExtract:
- mode d'execution (`provider_adapter`),
- parametrage modele extraction (temperature stricte, max tokens, etc.),
- garde-fous de timeout/reties au niveau extraction.

### 5.3 Selection explicite du contexte

Conserver la selection explicite du domaine via `profile_id`, sans reintroduire de routage automatique dans la migration LangExtract.

## 6) Plan d'implementation par phases

### Phase 0 - Preparation (safe)

Objectif:
- preparer le terrain sans changer le comportement production.

Actions:
1. Ajouter dependance `langextract` dans `backend/pyproject.toml`.
2. Introduire modules `extraction/*` avec interfaces et tests unitaires de base.
3. Ajouter feature flag runtime (ex: `COVEX_EXTRACTION_ENGINE=legacy|langextract`).

Definition of Done:
- build/tests verts,
- aucun changement fonctionnel observable sur `/analyze`.

### Phase 1 - Double execution (shadow mode)

Objectif:
- comparer legacy vs LangExtract sans impacter la reponse API.

Actions:
1. Executer LangExtract en parallele de legacy (non bloquant).
2. Journaliser ecarts (coverage, missing, latency, tokens).
3. Ajouter rapport comparatif simple en logs/app telemetry.
4. Appliquer la redaction S2/S3 sur toute telemetrie shadow.

Definition of Done:
- comparaison stable sur scenarios de reference,
- absence de regression perf critique.

Seuils minimaux de sortie de phase:
- precision extraction >= baseline - 2 points sur dataset de reference.
- recall extraction >= baseline - 2 points sur dataset de reference.
- latence p95 <= baseline + 20%.
- taux de mecanisme retire force <= 3% des requetes de test.

### Phase 2 - Activation controlee

Objectif:
- basculer certains prompts/domaines vers LangExtract.

Actions:
1. Activer LangExtract prompt par prompt (parametre config).
2. Garder mecanisme retire vers legacy si erreur extraction critique.
3. Mettre a jour tests integration API + UI sur prompts migrés.

Definition of Done:
- domaines pilotes stables,
- erreur/mecanisme retire explicites et non silencieux,
- playground inchange dans son contrat.

### Phase 3 - Nettoyage legacy

Objectif:
- supprimer la dette technique obsolete.

Actions:
1. Supprimer parsing JSON ad hoc et simulation matching mots-cles.
2. Eliminer duplications `_extract_requirements` et fonctions analogues.
3. Rationaliser `inference/client.py` et `analysis/routing.py` autour de la validation explicite du contexte et des nouveaux points d'extension.
4. Durcir validations schema extraction.

Definition of Done:
- legacy retire ou strictement archive,
- architecture simplifiee et documentee.

### Phase 4 - Durcissement final

Objectif:
- finaliser qualite, observabilite, documentation.

Actions:
1. Stabiliser messages d'erreurs/metriques pour exploitation ops.
2. Actualiser `docs/quick-start.md` et guide de debug extraction.
3. Ajouter scenarios de non-regression YAML axes extraction/selection-explicite/mecanisme retire.

Definition of Done:
- documentation complete,
- pipeline CI vert,
- migration declaree terminee.

## 7) Impacts par couche

Backend API:
- Contrat de sortie conserve (`score`, `decision`, `justification`, metadata).
- Eventuellement enrichi de details d'extraction non bloquants (optionnels).

Playground:
- aucune rupture obligatoire,
- potentielle extension d'affichage pour traces extraction (optionnel).

Config/ops:
- nouveaux champs de config extraction,
- procedure de bascule rollback documentee.

## 8) Strategie de tests

Unitaires:
- validation schemas extraction,
- mapping extraction -> score/decision,
- erreurs et mecanisme retire.

Integration backend:
- `/analyze` sur prompts majeurs,
- tests de bascule engine legacy/langextract,
- test de compatibilite payload playground.

Regression business:
- scenarios YAML existants + nouveaux cas limites.

Non-fonctionnels:
- latence mediane/p95,
- stabilite en erreurs provider,
- comportement en timeout.

Reproductibilite:
- dataset de reference versionne (golden set) avec cas nominaux + edge cases.
- version de modele cible figee pour les benchmarks de migration.
- checksum de configuration (`inference_engines.yaml`, `analysis_profiles.yaml`) capture a chaque run.
- seed/parametres de generation fixes pour campagnes comparatives.
- rapport comparatif legacy vs LangExtract archive a chaque jalon.

## 9) Risques et mitigations

Risque: degradation de precision sur certains prompts.
Mitigation: shadow mode + seuil de qualite avant activation.

Risque: dependance provider/SDK non stable.
Mitigation: abstraction `extraction/engine.py` + mecanisme retire explicite.

Risque: inflation de latence.
Mitigation: tuning params, timeouts, circuit breaker, limites de chunking.

Risque: complexite de config.
Mitigation: schema config valide et exemples minimaux par domaine.

## 10) Backlog de taches concret (ordre recommande)

1. Ajouter dependance LangExtract + lockfile.
2. Creer `extraction/schemas.py` et `extraction/errors.py`.
3. Creer `extraction/engine.py` (MVP extraction simple).
4. Integrer engine dans `analysis/service.py` via feature flag.
5. Ajouter tests unitaires extraction + integration API.
6. Implementer shadow mode et logs de comparaison.
7. Migrer 1er domaine pilote (`tickets_support_it`).
8. Migrer les autres domaines.
9. Supprimer heuristiques legacy.
10. Mettre a jour docs et scenarios de validation.

## 11) Critères d'acceptation de la refonte

- La logique centrale d'extraction est basee sur LangExtract.
- Le contrat API actuel reste compatible pour le playground.
- Le mecanisme retire est explicite, testable, et observable.
- Les heuristiques legacy fragiles sont supprimees apres migration.
- Les tests couvrent extraction, validation du contexte explicite, mecanisme retire, et non-regression UI/API.
- La documentation utilisateur et technique est a jour.

Seuils quantifies obligatoires:
- disponibilite API `/analyze` >= 99.5% sur campagne de validation.
- taux d'erreur 5xx <= 0.5% sur scenarios de regression.
- divergence score legacy vs LangExtract <= 5 points sur 95% du golden set.
- p95 latence bout-en-bout <= 1.20x baseline avant migration.

## 11.1) Protocoles de benchmark et validation

Chaque phase de migration doit produire un artefact de validation contenant:
- version du code + date + hash commit,
- version modele/provider utilisee,
- snapshot des configs et checksum,
- resultats precision/recall/F1,
- latence p50/p95,
- taux mecanisme retire et taux erreurs.

Sans cet artefact, la phase n'est pas considerée terminee.

## 12) Recommandation d'execution

Demarrer par une PR "Phase 0 + debut Phase 1" pour reduire le risque:
- scaffolding extraction,
- feature flag,
- execution shadow,
- tests de non-regression.

Puis enchaîner des PRs courtes par domaine metier, avant nettoyage final.
