# Impact des modèles sur les profils d'analyse

## 1. Objet de l'analyse

Cette note propose une lecture synthétique, rédigée dans une forme compatible
avec un rapport académique, de l'effet du choix du modèle d'inférence sur les
performances des profils CoVeX. L'enjeu n'est pas seulement de comparer des
modèles entre eux, mais d'établir dans quelle mesure la qualité dépend du type
de profil métier traité.

L'hypothèse examinée est la suivante : dans un système d'analyse documentaire
guidé par profils, il n'existe pas de modèle universellement optimal ; la
performance résulte plutôt d'une adéquation entre un profil, une structure de
texte, un schéma d'extraction et un moteur donné.

## 2. Protocole retenu

L'analyse repose sur le benchmark exhaustif généré par
`tools/research/select_engines_by_cost.py` et restitué dans
`artifacts/evaluation/engine_selection_report.md`.

Le protocole utilisé est le suivant :

- jeu de données : `datasets/golden_dataset.jsonl` ;
- mode d'exécution : `--exhaustive` (avec cache validé) ;
- nombre de profils : `11` ;
- nombre de moteurs comparés : `9` ;
- seuil de qualification : `90%` de *band match rate*.

Le critère principal est la concordance avec la bande de décision attendue
(`KO`, `PARTIEL`, `OK`) plutôt que l'égalité stricte du score numérique. Ce
choix est cohérent avec l'objectif applicatif de CoVeX : dans la pratique, la
stabilité décisionnelle importe davantage qu'une stricte identité de score.

## 3. Résultat général

Le benchmark confirme que l'impact du modèle est significatif et différencié
selon les profils. Les résultats ne soutiennent pas l'idée d'une hiérarchie
simple dans laquelle le modèle le plus grand ou le plus coûteux serait toujours
le meilleur. Ils montrent au contraire que la performance dépend fortement de la
nature du texte à traiter et du type de complétude attendu.

Trois familles de profils se dégagent nettement.

La première regroupe les profils pour lesquels
`remote_groq_llama31_8b_instant` constitue le meilleur compromis entre coût,
latence et qualité. C'est le cas de `demandes_achat`, `tickets_support_it`,
`suivi_scolaire`, `cr_intervention`, `demandes_devis_construction`,
`suivi_projet`, `validation_qualite` et `rapports_chantier`. Sur ces profils,
le moteur atteint le seuil de qualité tout en conservant une latence très faible,
généralement inférieure à une demi-seconde par cas.

La seconde regroupe les profils pour lesquels `remote_groq_gpt_oss_20b`
constitue le meilleur compromis : `demandes_absence_rh` et
`demandes_evolution_produit`. Avec un `cost_score` de 2, ce moteur se situe
juste au-dessus de Groq 8B en termes de coût, mais produit une qualité
supérieure sur ces deux profils exigeant une lecture sémantique plus fine.

La troisième concerne `demandes_citoyennes`, profil pour lequel
`remote_openrouter_mistral_small_32_24b` reste préférable. Sur cette tâche,
le modèle gère mieux les cas où la complétude dépend d'une interprétation
nuancée de la demande, de la présence d'implicites ou de la distinction entre
information utile et formulation accessoire.

## 4. Lecture par type de profil

Les profils dominés par Groq 8B ont en commun une structure relativement compacte et
des attentes informationnelles bien délimitées. Les textes y contiennent souvent
des indices explicites, facilement alignables avec quelques critères stables :
symptôme, urgence, action déjà tentée, référence de lot, prochaine étape, ou
décision formelle. Dans ce contexte, un modèle léger et rapide suffit à produire
une classification fiable.

`remote_groq_gpt_oss_20b` se distingue sur deux profils à mi-chemin entre la
structure compacte et la nuance sémantique. Dans `demandes_absence_rh`, il
produit une lecture contextuelle fiable à 100% là où Groq 8B échoue sur certains
cas (erreur d'exécution et 60% de band match). Dans `demandes_evolution_produit`,
il évite les surclassifications de cas partiels que Groq 8B commet.

À l'inverse, `demandes_citoyennes` reste mieux servi par
`remote_openrouter_mistral_small_32_24b`. Ce profil est celui où l'évaluation
porte le plus sur la distinction entre une requête traitable et une formulation
trop vague, ce qui semble bénéficier d'un modèle plus robuste sémantiquement.

## 5. Comparaison des familles de modèles

Du point de vue global, `remote_groq_llama31_8b_instant` constitue le moteur le
plus économique, avec `8/11` profils qualifiés à `cost_score=1` et une latence
inférieure à 0,5 s par cas. `remote_groq_gpt_oss_20b` ajoute deux profils
supplémentaires pour un `cost_score` légèrement plus élevé (2), ce qui porte la
couverture combinée de la famille Groq à `10/11` profils.
`remote_openrouter_mistral_small_32_24b` reste indispensable pour un profil
résiduel (`demandes_citoyennes`) et atteint `10/11` profils qualifiés en
autonomie, à `cost_score=3`.

Le résultat important n'est donc pas qu'un moteur remplace tous les autres, mais
qu'un moteur très économique peut devenir optimal sur une large part des profils
lorsque ceux-ci sont bien spécifiés, et qu'un second moteur léger et peu coûteux
permet de couvrir la majorité des cas restants.

Les modèles distants plus coûteux ne produisent pas ici de gain proportionnel à
leur prix. `remote_openrouter_llama33_70b` obtient de bons résultats, mais sans avantage
fonctionnel suffisant pour justifier sa latence et son coût supérieurs.
`remote_google_gemini25_flash` atteint plusieurs bons scores, mais reste dominé
dans le compromis final par Groq ou Mistral Small selon les profils.

Les modèles locaux montrent une image plus contrastée. `local_gemma3` reste
crédible sur plusieurs profils et atteint `8/11` profils qualifiés. En revanche,
les latences observées sont nettement plus élevées. `local_ministral` et
`local_mistral_nemo` peuvent être performants sur certains profils, mais leur
coût opérationnel en temps de réponse est important. Enfin, `local_phi4_mini`
présente une stabilité insuffisante dans ce cadre expérimental, avec erreurs de
sortie JSON, timeouts et un seul profil qualifié sur l'ensemble du benchmark.

## 6. Exemples révélateurs

Plusieurs cas illustrent concrètement la manière dont le choix du modèle modifie
la décision produite.

Dans `demandes_evolution_produit`, Groq 8B surévalue un cas partiel
(`TC-EVO-002`) et le classe en `OK`, tandis que `remote_groq_gpt_oss_20b` et
Mistral Small restent dans la bande attendue. L'écart ne relève donc pas d'un
simple bruit de score, mais d'une différence d'interprétation de la complétude
métier.

Dans `demandes_citoyennes`, Groq 8B échoue sur `TC-CIT-009` en accordant trop de
complétude à une demande encore insuffisamment exploitable. `remote_groq_gpt_oss_20b`
présente également des erreurs sur ce profil (40%), ce qui confirme que
Mistral Small reste indispensable ici.

Dans `demandes_absence_rh`, Groq 8B est pénalisé à la fois par un écart de
classification et par une erreur d'exécution (`Source tokens and extraction tokens
cannot be empty`). `remote_groq_gpt_oss_20b` produit 100% de band match sur ce
profil, sans erreur de sortie. Ce contraste illustre que la qualité en production
dépend autant de la robustesse opérationnelle que du score brut.

Dans `rapports_chantier`, le passage d'un moteur local à Groq 8B conserve la
qualité attendue tout en réduisant fortement la latence. Ce résultat a une portée
pratique importante, car il transforme non seulement la qualité perçue par
l'utilisateur, mais aussi la capacité de montée en charge du système.

## 7. Portée pour la configuration de CoVeX

L'enseignement principal de ce benchmark est que la sélection du moteur doit se
faire au niveau du profil et non au niveau global de l'application. La bonne
unité de décision n'est pas le modèle seul, mais le couple `profil x modèle`.

Cette conclusion justifie une stratégie de routage différencié :

- utiliser `remote_groq_llama31_8b_instant` pour les profils bien structurés,
  lorsque la rapidité constitue un avantage net sans perte de qualité ;
- utiliser `remote_groq_gpt_oss_20b` pour les profils nécessitant une lecture
  sémantique légèrement plus fine, mais dont le coût reste minimal ;
- utiliser `remote_openrouter_mistral_small_32_24b` pour le profil résiduel
  (`demandes_citoyennes`) qui requiert une évaluation plus nuancée de la
  suffisance informationnelle.

Pour un rapport académique, ce résultat est particulièrement intéressant, car il
montre que l'optimisation d'un système LLM appliqué ne relève pas seulement du
choix du meilleur modèle en moyenne. Elle repose sur une spécialisation
contextualisée, appuyée par des mesures empiriques par tâche.

## 8. Limites

Cette analyse doit être interprétée avec prudence.

Premièrement, le nombre de cas par profil reste limité. Le benchmark est adapté à
une décision d'ingénierie, mais il ne constitue pas à lui seul une validation
statistique exhaustive.

Deuxièmement, la métrique principale porte sur la justesse de la bande de
décision, et non sur une évaluation détaillée de chaque extraction textuelle.
L'analyse décrit donc prioritairement la stabilité du jugement, pas toute la
finesse du comportement génératif.

Troisièmement, certaines erreurs reflètent aussi la robustesse du format de
sortie, du parseur JSON ou des conventions de prompt. Les résultats observés ne
doivent donc pas être attribués uniquement à la capacité intrinsèque du modèle.

## 9. Conclusion

L'étude met en évidence un effet net du choix du modèle sur la qualité des profils
CoVeX. Cet effet n'est ni uniforme, ni monotone avec la taille ou le coût des
modèles. Les meilleurs résultats sont obtenus lorsqu'un moteur est sélectionné en
fonction du profil métier considéré.

En synthèse, trois conclusions peuvent être retenues.

Premièrement, les tâches structurées et fortement contraintes peuvent être prises
en charge avec une excellente efficacité par un petit modèle distant très peu
coûteux. Deuxièmement, certaines tâches plus nuancées nécessitent un moteur
légèrement plus capable sur le plan sémantique, mais il n'est pas nécessaire de
recourir à des modèles très coûteux : un intermédiaire comme `remote_groq_gpt_oss_20b`
(`cost_score=2`) suffit pour deux profils sur trois.
Troisièmement, les modèles locaux restent utiles comme alternative technique,
mais ils n'offrent pas ici le même niveau de stabilité opérationnelle que les
meilleurs moteurs distants.

Au total, CoVeX illustre une logique de spécialisation pragmatique : la qualité
maximale n'est pas obtenue par uniformisation du moteur, mais par sélection
contextualisée du modèle le plus adapté à chaque profil.
