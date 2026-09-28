# Aide à la décision multicritère (MCDM)

Application Streamlit qui guide pas à pas un décideur pour comparer des options selon plusieurs critères et obtenir une recommandation argumentée.

## Méthodes implémentées

| Étape | Méthodes |
|---|---|
| Pondération des critères | AHP, BWM (Best-Worst), Entropie, CRITIC, poids manuels |
| Évaluation des options | Valeur chiffrée, appréciation (Très faible → Excellent), comparaison deux à deux (AHP) |
| Classement | TOPSIS, WSM, WPM, WASPAS, synthèse AHP |

## Lancer l'application

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Organisation du code

```
app.py                  point d'entrée : onglets et barre latérale
.streamlit/config.toml  thème (couleurs, police)
mcdm/                   méthodes de calcul (indépendantes de l'interface)
  weighting.py          AHP, BWM, Entropie, CRITIC
  ranking.py            WSM, WPM, WASPAS, TOPSIS, synthèse AHP
interface/              interface Streamlit
  state.py              état de l'application, projet exemple
  style.py              CSS et composants visuels
  charts.py             graphiques Plotly
  pairwise.py           questionnaire de comparaisons deux à deux
  projet.py             onglet 1 : options et critères
  evaluation.py         onglet 2 : évaluations
  ponderation.py        onglet 3 : importance des critères
  resultats.py          onglet 4 : classement et recommandation
```
