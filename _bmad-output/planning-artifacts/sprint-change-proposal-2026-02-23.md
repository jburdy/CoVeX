# Sprint Change Proposal - Simplification de l'Implémentation

**Date:** 2026-02-23  
**Auteur:** JBU  
**Type:** Simplification pour présentation de défense

---

## 1. Résumé du Problème

L'implémentation actuelle de CoVeX est jugée **trop verbose** (~4000 lignes de code) et sera difficile à présenter lors de la défense devant les experts. L'objectif est de **simplifier au maximum** tout en **conservant toutes les fonctionnalités actuelles** (pas de régression).

### Métriques actuelles
- Backend: ~3180 lignes Python
- Playground: ~795 lignes Python
- **Total: ~3975 lignes**

---

## 2. Analyse d'Impact

### Impact Épique
Les épiques existants restent valides. Aucune modification de scope fonctionnel n'est requise.

### Impact sur les Artefacts
| Artefact | Impact | Action |
|----------|--------|--------|
| `epics.md` | Aucun | - |
| `architecture.md` | Mise à jour mineure | Documenter les simplifications |
| `prd.md` | Aucun | - |

---

## 3. Approche Recommandée

**Option 1: Ajustement Direct** (Recommandée)

Simplifier le code existant par:
1. Suppression de fonctionnalités non essentielles (shadow mode, mecanisme retire complexe)
2. Consolidation du code dupliqué
3. Réduction de la complexité des adaptateurs
4. Simplification du runtime timeline playground

**Estimation d'effort:** Moyen  
**Niveau de risque:** Faible  
**Impact timeline:** Réduction du temps de présentation

Note d'archive: cette proposition a ete depassee par le nettoyage ulterieur du depot. `backend/src/extraction/` et `langextract` ont ete supprimes.

---

## 4. Propositions de Modification Détaillées

### 4.1 Backend - Moteur d'Extraction (extraction/engine.py)

**Fichier:** `backend/src/extraction/engine.py` (115 lignes)

**Problème:** Système de shadow comparison avec LangExtract qui ajoute de la complexité sans valeur fonctionnelle pour la défense.

**Modification propuesta:**

```
ANCIEN:
- run_langextract_extraction() - ~45 lignes
- build_shadow_comparison_payload() - ~30 lignes  
- _ensure_langextract_is_installed() - ~5 lignes
- _resolve_expected_keys() - ~18 lignes
- _deduplicate() - ~7 lignes

NOUVEAU:
- Supprimer entièrement le fichier ou le réduire à l'essentiel
- Le résultat d'analyse viene uniquement du moteur d'inference principal
```

**Impact:** -80 lignes  
**Rationale:** Le shadow comparison n'est pas nécessaire pour le MVP. Le scoring vient du LLM via l'inférence.

---

### 4.2 Backend - Adaptateur d'Inférence (inference/adapter.py)

**Fichier:** `backend/src/inference/adapter.py` (362 lignes)

**Problème:** 
1. Méthode `_call_client` avec cascade de try/except pour compatibilité arrière (lignes 172-227)
2. Système de mecanisme retire complexe (gestion provider + recovery + seuils)
3. Normalisation de métriques excessive

**Modification proposta:**

```python
# _call_client - Simplifier à une seule signature
def _call_client(
    self,
    *,
    text: str,
    prompt: str,
    provider_key: str,
    provider_params: dict,
) -> dict[str, object]:
    return self._client(
        text=text,
        prompt=prompt,
        timeout=self._timeout_sec,
        provider_key=provider_key,
        config_dir=self._config_dir,
        provider_params=provider_params,
    )

# Supprimer la logique de mecanisme retire complexe si un seul provider est utilisé
# Garder seulement la gestion d'erreur de base
```

**Impact:** -150 lignes  
**Rationale:** Supposer une signature unique pour le client. Le mecanisme retire n'est pas critique pour la défense.

---

### 4.3 Backend - Fonctions de Dédoublonnage Dupliquées

**Problème:** La fonction `_deduplicate` apparaît dans plusieurs fichiers:
- `analysis/routing.py` (lignes 239-246)
- `extraction/engine.py` (lignes 108-115)

**Modification:** Extraire dans un module utilitaire commun.

**Impact:** -10 lignes (en supprimant la duplication)

---

### 4.4 Backend - Configuration Runtime (common/config_runtime.py)

**Fichier:** `backend/src/common/config_runtime.py` (~200+ lignes)

**Problème:** Système complexe de reload dynamique de configuration qui ajoute de la complexité.

**Simplification proposée:**
- Réduire le nombre de recharges dynamiques
- Simplifier la gestion des snapshots

**Impact:** -50 lignes

---

### 4.5 Playground - Runtime Timeline (playground/page.py)

**Fichier:** `playground/src/playground/page.py` (307 lignes)

**Problème:** 
- Système de "runtime timeline" très détaillé pour le suivi technique (lignes 238-255)
- Messages de debug excessifs pour une présentation

**Modification:**
```python
# Supprimer les fonctions:
# - _start_runtime_timeline()
# - _append_runtime_step()

# Remplacer par un simple indicateur de chargement
```

**Impact:** -40 lignes  
**Rationale:** Pas nécessaire pour la défense. Juste un indicateur "Analyse en cours..." suffit.

---

### 4.6 Playground - Vérification de Routage

**Fichier:** `playground/src/playground/page.py` (lignes 220-235)

**Problème:** Fonction `_render_routing_check` qui affiche des détails techniques de validation.

**Simplification:** Supprimer ou masquer cette fonctionnalité en mode production.

**Impact:** -15 lignes

---

### 4.7 Tests - Réduction

**Problème:** Les tests unitaires ajoutent du volume.

**Option:** 
- Conserver uniquement les tests critiques (core business logic)
- Réduire ou supprimer les tests d'intégration verbose

**Impact:** Variable selon stratégie

---

## 5. Récapitulatif des Simplifications

| Composant | Lignes Actuelles | Réduction Proposed | Lignes Cibles |
|-----------|------------------|-------------------|---------------|
| extraction/engine.py | 115 | -90 | 25 |
| inference/adapter.py | 362 | -150 | 212 |
| config_runtime.py | ~200 | -50 | 150 |
| playground/page.py | 307 | -55 | 252 |
| Code dupliqué | - | -15 | - |
| **TOTAL** | **~1000** | **~360** | **~640** |

**Réduction estimée: ~360 lignes (~35% de simplification)**

---

## 6. Plan de Migration

### Phase 1: Nettoyage Backend (30 min)
1. Supprimer extraction/engine.py ou extraire seulement le nécessaire
2. Simplifier inference/adapter.py
3. Consolider les fonctions utilitaires

### Phase 2: Nettoyage Playground (15 min)
1. Supprimer runtime timeline
2. Simplifier les messages d'erreur

### Phase 3: Validation (15 min)
1. Exécuter les tests existants
2. Vérifier que l'API fonctionne toujours
3. Tester le Playground

---

## 7. Critères de Succès

- [ ] Toutes les fonctionnalités PRD保持 (pas de régression)
- [ ] Lignes de code réduites de ~30-40%
- [ ] API REST fonctionnelle (POST /analyze)
- [ ] Playground fonctionnel
- [ ] Tests critiques passent

---

## 8. Handoff

**Portée:** Moyenne (modérée)  
**Responsable:** Équipe développement  
**Livrables:**
- Code simplifié
- Tests de non-régression passent

---

## Questions pour Validation

1. Le système de mecanisme retire entre providers est-il critique pour la défense ?
2. Voulez-vous garder la timeline technique en mode masqué ?
3. Quelle stratégie pour les tests unitaires ?
