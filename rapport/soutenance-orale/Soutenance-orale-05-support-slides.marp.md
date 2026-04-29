---
marp: true
paginate: true
theme: default
size: 16:9
title: CoVeX
description: CoVeX | Vérification de la complétude des saisies textuelles métier
footer: HES-Arc / Tebicom SA | CoVeX | J. Burdy
style: |
  section {
    font-family: "Aptos", "Avenir Next", Arial, sans-serif;
    font-size: 29px;
    line-height: 1.32;
    padding: 56px 64px;
    color: #0f172a;
    background: linear-gradient(180deg, #f8fbfd 0%, #ffffff 100%);
  }
  section::before {
    content: "";
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    height: 10px;
    background: linear-gradient(90deg, #0f3d5e 0%, #0f766e 55%, #d6a44d 100%);
  }
  h1, h2, h3 {
    color: #0f2f4a;
    margin: 0 0 0.35em 0;
  }
  h1 {
    font-size: 1.8em;
    letter-spacing: -0.02em;
  }
  h2 {
    font-size: 1.08em;
  }
  h3 {
    font-size: 0.8em;
    margin-bottom: 0.5em;
  }
  p, li {
    color: #243447;
  }
  strong {
    color: #0f766e;
  }
  blockquote {
    margin: 24px 0 0 0;
    border-left: 6px solid #0f766e;
    background: #eef8f7;
    padding: 16px 18px;
    border-radius: 12px;
  }
  code {
    background: rgba(15, 61, 94, 0.08);
    border-radius: 8px;
    padding: 0.15em 0.35em;
  }
  .pseudo-code {
    background: #0b1f33;
    color: #e0f2fe;
    border-radius: 16px;
    padding: 20px 22px;
    font-size: 0.68em;
    line-height: 1.38;
    white-space: pre-wrap;
    box-shadow: 0 18px 40px rgba(15, 23, 42, 0.14);
  }
  .pseudo-code code {
    background: transparent;
    color: inherit;
    padding: 0;
  }
  .eyebrow {
    text-transform: uppercase;
    letter-spacing: 0.14em;
    font-size: 0.46em;
    font-weight: 800;
    color: #0f766e;
    margin-bottom: 1.1em;
  }
  .lead {
    background:
      radial-gradient(circle at top right, rgba(214, 164, 77, 0.22), transparent 28%),
      linear-gradient(135deg, #0b1f33 0%, #0f3d5e 55%, #0f766e 100%);
    color: #ffffff;
  }
  .lead::before {
    display: none;
  }
  .lead h1,
  .lead h2,
  .lead h3,
  .lead p,
  .lead li,
  .lead strong,
  .lead a,
  .lead blockquote {
    color: #ffffff;
  }
  .lead .eyebrow {
    color: #b8fff0;
  }
  .lead blockquote {
    background: #eef8f7;
    border-left-color: #0f766e;
    color: #0f2f4a;
  }
  .cards-2,
  .cards-3,
  .cards-4,
  .metric-grid {
    display: grid;
    gap: 20px;
    margin-top: 8px;
  }
  .cards-2 {
    grid-template-columns: 1fr 1fr;
  }
  .cards-3,
  .metric-grid {
    grid-template-columns: repeat(3, 1fr);
  }
  .cards-4 {
    grid-template-columns: repeat(2, 1fr);
  }
  .card,
  .metric-card {
    background: #ffffff;
    border: 1px solid #dbe4ee;
    border-radius: 18px;
    padding: 20px 22px;
  }
  .card h3,
  .metric-card h3 {
    color: #0f3d5e;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    font-size: 0.56em;
  }
  .metric-value {
    font-size: 1.8em;
    font-weight: 800;
    line-height: 1;
    color: #0f766e;
    margin-bottom: 10px;
  }
  .muted {
    margin-top: 16px;
    font-size: 0.76em;
    color: #475569;
  }
  .compact-list {
    columns: 2;
    column-gap: 26px;
    font-size: 0.72em;
    line-height: 1.28;
    padding-left: 20px;
  }
  .example-list {
    font-size: 0.72em;
    line-height: 1.28;
    padding-left: 20px;
  }
  .example-list li {
    margin-bottom: 10px;
  }
  .accent-line {
    margin-top: 22px;
    font-size: 1.02em;
    font-weight: 700;
    color: #0f2f4a;
  }
  .engine-selection {
    display: grid;
    grid-template-columns: 1.18fr 0.82fr;
    gap: 24px;
    align-items: stretch;
    margin-top: 20px;
  }
  .selection-steps,
  .cost-score-box {
    background: #ffffff;
    border: 1px solid #dbe4ee;
    border-radius: 18px;
    padding: 18px 20px;
  }
  .selection-steps h3,
  .cost-score-box h3 {
    color: #0f3d5e;
    font-size: 0.56em;
    letter-spacing: 0.06em;
    text-transform: uppercase;
  }
  .step-line {
    display: grid;
    grid-template-columns: 34px 1fr;
    gap: 10px;
    align-items: start;
    margin-top: 10px;
  }
  .step-number {
    width: 34px;
    height: 34px;
    border-radius: 999px;
    background: #0f766e;
    color: #ffffff;
    display: grid;
    place-items: center;
    font-size: 0.54em;
    font-weight: 800;
  }
  .step-line strong {
    display: block;
    color: #0f3d5e;
    font-size: 0.62em;
  }
  .step-line span {
    display: block;
    color: #475569;
    font-size: 0.54em;
    line-height: 1.24;
  }
  .cost-formula {
    display: grid;
    grid-template-columns: 1fr auto 1fr auto 1.25fr;
    gap: 12px;
    align-items: stretch;
    margin-top: 12px;
  }
  .cost-component {
    border: 1px solid #dbe4ee;
    border-radius: 16px;
    padding: 14px 12px;
    background: #f8fbfd;
    text-align: center;
    min-height: 116px;
    display: flex;
    flex-direction: column;
    justify-content: center;
  }
  .cost-component.strong {
    background: #ecf8f6;
    border-color: #b7ddd9;
  }
  .cost-component strong {
    display: block;
    color: #0f766e;
    font-size: 0.62em;
  }
  .cost-component span {
    display: block;
    margin-top: 5px;
    color: #475569;
    font-size: 0.48em;
    line-height: 1.18;
  }
  .cost-plus {
    display: grid;
    place-items: center;
    color: #0f3d5e;
    font-size: 1.1em;
    font-weight: 800;
  }
  .sovereignty-choices {
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: 6px;
    margin-top: 8px;
  }
  .sovereignty-choice {
    background: #ffffff;
    border: 1px solid #c6e5e1;
    border-radius: 10px;
    padding: 5px 6px;
    color: #0f3d5e;
    font-size: 0.44em;
    font-weight: 800;
  }
  .cost-note {
    margin-top: 12px;
    color: #475569;
    font-size: 0.54em;
    line-height: 1.28;
  }
  .engine-objective {
    margin-top: 20px;
    border-left: 6px solid #0f766e;
    background: #eef8f7;
    border-radius: 12px;
    padding: 14px 18px;
    color: #243447;
    font-size: 0.9em;
    line-height: 1.25;
  }
  .engine-objective strong {
    color: #0f2f4a;
  }
  .opening-agenda {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 14px;
    margin-top: 18px;
    position: relative;
  }
  .opening-agenda::before {
    content: "";
    position: absolute;
    top: 21px;
    left: 7%;
    right: 7%;
    height: 3px;
    background: linear-gradient(90deg, #0f3d5e 0%, #0f766e 70%, #d6a44d 100%);
    border-radius: 999px;
  }
  .opening-agenda-label {
    margin-top: 44px;
    font-size: 0.52em;
    font-weight: 800;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    color: #0f766e;
  }
  .opening-agenda-item {
    position: relative;
    text-align: center;
    padding-top: 54px;
  }
  .opening-agenda-number {
    position: absolute;
    top: 0;
    left: 50%;
    transform: translateX(-50%);
    font-size: 0.5em;
    font-weight: 800;
    color: #ffffff;
    background: #0f766e;
    border: 2px solid #d6a44d;
    border-radius: 999px;
    width: 46px;
    height: 46px;
    display: grid;
    place-items: center;
  }
  .opening-agenda-item h3 {
    color: #0f3d5e;
    font-size: 0.58em;
    margin: 0 0 0.35em 0;
    text-transform: uppercase;
    letter-spacing: 0.06em;
  }
  .opening-agenda-item p {
    font-size: 0.52em;
    line-height: 1.22;
    margin: 0;
    color: #243447;
  }
  .pill {
    display: inline-block;
    padding: 6px 12px;
    border-radius: 999px;
    font-size: 0.54em;
    font-weight: 800;
    letter-spacing: 0.05em;
    margin-right: 8px;
  }
  .pill.ko {
    background: #fee2e2;
    color: #991b1b;
  }
  .pill.partial {
    background: #ffedd5;
    color: #9a3412;
  }
  .pill.ok {
    background: #dcfce7;
    color: #166534;
  }
  .architecture-visual {
    display: block;
    width: 100%;
    max-height: 610px;
    object-fit: contain;
    margin: 0 auto;
    border-radius: 16px;
  }
  .closing-grid {
    display: grid;
    grid-template-columns: 0.78fr 1.22fr;
    gap: 36px;
    align-items: center;
    height: 100%;
  }
  .demo-screenshot {
    display: block;
    width: 100%;
    max-height: 570px;
    object-fit: contain;
    background: #ffffff;
    border-radius: 18px;
  }
---

<!-- _class: lead -->

<div class="eyebrow">Travail de CAS en intelligence artificielle appliquée en entreprise</div>

# CoVeX

## Vérification de la complétude des saisies textuelles métier par IA


Julien Burdy - Avril 2026

<div class="opening-agenda-label">Déroulé de la présentation</div>

<div class="opening-agenda">
  <div class="opening-agenda-item">
    <span class="opening-agenda-number">1</span>
    <h3>Enjeu métier</h3>
    <p>qualité des saisies</p>
  </div>
  <div class="opening-agenda-item">
    <span class="opening-agenda-number">2</span>
    <h3>Solution</h3>
    <p>profils et scoring</p>
  </div>
  <div class="opening-agenda-item">
    <span class="opening-agenda-number">3</span>
    <h3>Conception</h3>
    <p>architecture, optimisations</p>
  </div>
  <div class="opening-agenda-item">
    <span class="opening-agenda-number">4</span>
    <h3>Conclusion</h3>
    <p>illustration en direct</p>
  </div>
</div>

<!--
Temps cible : 1:00
Message : poser le sujet, la promesse et le fil directeur.
-->

---

<div class="eyebrow">Contexte</div>

# Des textes saisis, pas toujours exploitables

<div class="cards-2">
  <div class="card">
    <h3>À la saisie</h3>
    <ul>
      <li>messages trop courts</li>
      <li>contexte absent</li>
      <li>informations critiques manquantes</li>
    </ul>
  </div>
  <div class="card">
    <h3>En aval</h3>
    <ul>
      <li>relances et clarifications</li>
      <li>erreurs de traitement</li>
      <li>perte de valeur de la donnée</li>
    </ul>
  </div>
</div>

<blockquote>
Le besoin n'est pas de mieux écrire, mais de mieux capturer l'information.
</blockquote>

<!--
Temps cible : 1:30
Exemples possibles : ticket IT "ça marche pas", demande d'achat sans budget ni urgence.
-->

---

<div class="eyebrow">Corpus métier</div>

# Contextes variés

<div class="cards-2">
  <div class="card">
    <h3>Profils du golden dataset</h3>
    <ul class="compact-list">
      <li>support IT</li>
      <li>demandes d'achat</li>
      <li>comptes-rendus d'intervention</li>
      <li>demandes citoyennes</li>
      <li>devis construction</li>
      <li>rapports chantier</li>
      <li>suivi scolaire</li>
      <li>absences RH</li>
      <li>suivi projet</li>
      <li>évolutions produit</li>
      <li>validation qualité</li>
    </ul>
  </div>
  <div class="card">
    <h3>Demandes incomplètes typiques</h3>
    <ul class="example-list">
      <li>« ça marche pas »</li>
      <li>« Il me faut une souris »</li>
      <li>« Je déménage bientôt dans votre commune »</li>
      <li>« Je serai absent bientôt pour un mariage »</li>
      <li>« Intervention terminée, mais il reste quelques points à reprendre »</li>
    </ul>
  </div>
</div>

<!--
Temps cible : 1:15
Message : montrer que le problème n'est pas propre à l'IT ; il traverse plusieurs métiers.
-->

---

<div class="eyebrow">Problématique</div>

# Quadruple tension

<div class="cards-4">
  <div class="card">
    <h3>Tension 1</h3>
    <p>La complétude dépend du <strong>contexte</strong></p>
  </div>
  <div class="card">
    <h3>Tension 2</h3>
    <p>Préserver la <strong>fluidité de saisie</strong> actuelle</p>
  </div>
  <div class="card">
    <h3>Tension 3</h3>
    <p>Garder une <strong>maîtrise des données</strong></p>
  </div>
  <div class="card">
    <h3>Tension 4</h3>
    <p>Éviter le <strong>blocage injustifié</strong></p>
  </div>
</div>

<!--
Temps cible : 1:30
Formule utile : précision métier, fluidité, souveraineté, prudence.
-->

---

<div class="eyebrow">Réponse</div>

# Le principe de CoVeX

<div class="cards-3">
  <div class="card">
    <h3>Entrée</h3>
    <p><code>text</code><br><code>profile_id</code></p>
  </div>
  <div class="card">
    <h3>Analyse</h3>
    <p>- assemblage prompt / few-shot<br>- appel moteur<br>- extraction + scoring</p>
  </div>
  <div class="card">
    <h3>Sortie</h3>
    <p><code>OK</code> / <code>PARTIEL</code> / <code>KO</code><br>éléments manquants / extractions</p>
  </div>
</div>

<blockquote>CoVeX est un <strong>service d'analyse intégrable</strong>, pas une application autonome.</blockquote>

<!--
Temps cible : 1:30
-->

---

<img class="architecture-visual" src="CoVeX-Archi.png" alt="Architecture CoVeX en trois couches">

<!--
Temps cible : 1:15
Message : montrer l'intégration par API, le backend FastAPI, la configuration YAML et la sortie JSON.
-->

---

<div class="eyebrow">Optimisation</div>

# Algorithme de sélection de moteur

<div class="engine-selection">

  <div class="cost-score-box">
    <h3>Composition possible du <code>cost_score</code></h3>
    <div class="cost-formula">
      <div class="cost-component"><strong>Budget</strong><span>prix d'inférence</span></div>
      <div class="cost-plus">+</div>
      <div class="cost-component"><strong>Latence</strong><span>vitesse attendue (a)sync?</span></div>
      <div class="cost-plus">+</div>
      <div class="cost-component strong">
        <strong>Souveraineté</strong><span>selon affinité et sensibilité</span>
        <div class="sovereignty-choices">
          <div class="sovereignty-choice">On-prem</div>
          <div class="sovereignty-choice">Europe</div>
          <div class="sovereignty-choice">US</div>
          <div class="sovereignty-choice">Chine</div>
        </div>
      </div>
    </div>
    <p class="cost-note">La pondération est configurable : une donnée sensible peut privilégier la maîtrise géographique plutôt que le prix ou la vitesse.</p>
  </div>

  <div class="selection-steps">
    <h3>Algorithme</h3>
    <div class="step-line">
      <div class="step-number">1</div>
      <div><strong>Profil</strong><span>partir du besoin métier</span></div>
    </div>
    <div class="step-line">
      <div class="step-number">2</div>
      <div><strong>Tri</strong><span>ordonner par <code>cost_score</code></span></div>
    </div>
    <div class="step-line">
      <div class="step-number">3</div>
      <div><strong>Test</strong><span>rejouer le <code>golden dataset</code></span></div>
    </div>
    <div class="step-line">
      <div class="step-number">4</div>
      <div><strong>Choix</strong><span>retenir le premier moteur suffisant</span></div>
    </div>
  </div>

</div>

<div class="engine-objective">
  <strong>Objectif :</strong> choisir le plus petit moteur qui suffit pour le profil.
</div>

<!--
Temps cible : 2:00
-->

---

<div class="eyebrow">Conclusion / Enseignements</div>

# Conclusion

  <div class="cards-2">
    <div class="card">
    <h3>Conclusion</h3>
    <ul>
      <li>Évaluation prometteuse, mais à confirmer sur un corpus plus large.</li>
      <li>CoVeX doit guider l’utilisateur, sans blocage automatique.</li>
      <li>La complétude n’est pas universelle et dépend du métier, du contexte et de l’usage.</li>
    </ul> 
    </div>
      <div class="card">
    <h3>Erreurs assumées</h3>
        <ul>
      <li>L’utilisation de BMad a été un apport et un apprentissage majeurs pour le cadrage du projet, mais sa rigueur a entraîné une <b>surspécification</b> qui a complexifié l'exercice. </li>
      <li>BMad utilisé depuis dans l'entreprise.</li>
    </ul>
    
</div>
</div>

<!--
Temps cible : 1:00
-->

---

<!-- _class: lead -->

<div class="closing-grid">
  <div>
<div class="eyebrow">Échange</div>

# Questions

Merci pour votre attention.

<blockquote>CoVeX: Rendre visibles les manquements avant la dette informationnelle.</blockquote>
  </div>
  <div>
    <img class="demo-screenshot" src="PlayGroundScreen.png" alt="Capture du playground CoVeX">
  </div>
</div>



<!--
Slide de transition vers les 10 minutes de questions avec démonstration live.
-->
