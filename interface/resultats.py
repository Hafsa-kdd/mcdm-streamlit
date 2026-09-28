"""Onglet 4 : classement des options, synthèse et robustesse du résultat."""
import numpy as np
import pandas as pd
import streamlit as st

from mcdm import ahp_synthesis, topsis, waspas, wpm, wsm

from . import charts, style
from .state import default

METHODS = {
    "TOPSIS": ("TOPSIS", "Recommandé : retient l'option la plus proche de l'idéal et la plus éloignée du pire."),
    "WSM": ("Somme pondérée", "La plus simple : moyenne des performances pondérée par l'importance des critères."),
    "WPM": ("Produit pondéré", "Pénalise davantage les options qui ont un point très faible."),
    "WASPAS": ("WASPAS", "Combine la somme et le produit pondérés."),
    "AHP": ("AHP", "Priorités finales : somme des priorités locales de chaque option, pondérées par "
                   "l'importance des critères. Idéal si vous avez comparé les options deux à deux."),
}
MEDALS = ["🥇", "🥈", "🥉"]


def _compute(method, problem, weights, lam=0.5):
    X, b = problem.X, problem.benefit
    if method == "TOPSIS":
        return topsis(X, weights, b)
    if method == "WSM":
        return wsm(X, weights, b)
    if method == "WPM":
        return wpm(X, weights, b)
    if method == "AHP":
        return ahp_synthesis(X, weights, b)
    return waspas(X, weights, b, lam)


def _ranks(scores):
    return pd.Series(scores).rank(ascending=False, method="min").astype(int).to_numpy()


def _profile(problem):
    # Performance de chaque option sur chaque critère ramenée entre 0 (la pire) et 1 (la meilleure)
    X = problem.X
    lo, hi = X.min(axis=0), X.max(axis=0)
    span = np.where(hi - lo == 0, 1, hi - lo)
    P = np.where(problem.benefit, (X - lo) / span, (hi - X) / span)
    P[:, hi - lo == 0] = 1
    return P


def render(problem, weights, weight_info):
    if not problem.is_complete:
        st.info("Complétez d'abord les onglets **Projet** et **Évaluations**.")
        return
    if weights is None:
        st.info("Indiquez l'importance de vos critères dans l'onglet **Importance des critères**.")
        return

    with st.container(key="card_rank_method"):
        style.section(7, "Méthode de classement")
        method = st.radio("Méthode", list(METHODS), key=default("w_rank_method", "TOPSIS"), horizontal=True,
                          format_func=lambda m: METHODS[m][0], label_visibility="collapsed")
        st.caption(METHODS[method][1])
        if any(problem.pairwise) and method != "AHP":
            st.info("Vous avez comparé des options deux à deux : la méthode **AHP** applique la démarche "
                    "complète (priorités locales puis priorités finales).", icon=":material/lightbulb:")
        lam = 0.5
        if method == "WASPAS":
            lam = st.slider("Part de la somme pondérée (λ)", 0.0, 1.0, key=default("w_lambda", 0.5), step=0.05)

    # Toutes les méthodes sont calculées pour vérifier la robustesse du classement
    results = {}
    for m in METHODS:
        try:
            results[m] = _compute(m, problem, weights, lam)
        except ValueError as e:
            results[m] = e
    res = results[method]
    if isinstance(res, ValueError):
        st.error(f"Cette méthode ne peut pas être appliquée à vos données : {res} "
                 "Choisissez une autre méthode (TOPSIS accepte les valeurs nulles).")
        return

    alts, crits = problem.alternatives, problem.criteria
    scores = res["scores"]
    order = np.argsort(-scores)
    best, second = order[0], order[1]
    winners = {m: alts[int(np.argmax(r["scores"]))] for m, r in results.items() if not isinstance(r, ValueError)}
    agree = sum(w == alts[best] for w in winners.values())
    gap = (scores[best] - scores[second]) / scores[best] if scores[best] else 0

    # ------------------------------------------------------------ indicateurs clés
    k1, k2, k3, k4 = st.columns(4, gap="small")
    with k1:
        style.kpi("Option recommandée", alts[best], f"Score {scores[best]:.3f}", gradient=True)
    with k2:
        style.kpi("Avance sur la 2e", f"{gap:.1%}", f"devant {alts[second]}")
    with k3:
        style.kpi("Robustesse", f"{agree}/{len(winners)}", "méthodes d'accord sur la 1re place")
    with k4:
        top = int(np.argmax(weights))
        style.kpi("Critère décisif", crits[top], f"{weights[top]:.0%} de la décision")

    # ------------------------------------------------------------ synthèse
    P = _profile(problem)
    strengths = [c for j, c in enumerate(crits) if P[best, j] >= 0.999]
    weaknesses = [c for j, c in enumerate(crits) if P[best, j] <= 0.34]
    priorities = ", ".join(f"{crits[j]} ({weights[j]:.0%})" for j in np.argsort(-weights)[:3])
    with st.container(key="card_summary"):
        style.section(8, "Notre recommandation")
        title = f" pour « {problem.title} »" if problem.title else ""
        text = (f"Compte tenu de vos priorités — {priorities} —, la meilleure option{title} est "
                f"**{alts[best]}**, suivie de **{alts[second]}**.")
        if strengths:
            text += f"\n\n**Points forts** de {alts[best]} : meilleure option sur {', '.join(strengths)}."
        if weaknesses:
            text += f"\n\n**Points de vigilance** : parmi les moins bonnes sur {', '.join(weaknesses)}."
        if agree == len(winners):
            text += "\n\n✅ Toutes les méthodes de classement désignent la même option : le résultat est **robuste**."
        else:
            others = sorted({w for w in winners.values() if w != alts[best]})
            text += (f"\n\n⚠️ Selon la méthode utilisée, {', '.join(others)} peut aussi arriver en tête : "
                     "les options sont proches, regardez le détail avant de trancher.")
        if gap < 0.03:
            text += "\n\nL'écart avec la deuxième option est faible (moins de 3 %)."
        st.markdown(text)

    # ------------------------------------------------------------ graphiques
    c1, c2 = st.columns(2, gap="medium")
    with c1, st.container(key="card_scores"):
        style.section(9, "Classement")
        st.plotly_chart(charts.scores_bar(alts, scores), width="stretch", config={"displayModeBar": False})
    with c2, st.container(key="card_radar"):
        style.section(10, "Profil des meilleures options", "0 = la moins bonne, 1 = la meilleure sur ce critère")
        podium = order[:3]
        st.plotly_chart(charts.radar(crits, {alts[i]: P[i] for i in podium}), width="stretch",
                        config={"displayModeBar": False})

    # ------------------------------------------------------------ tableau détaillé
    with st.container(key="card_table"):
        style.section(11, "Tableau comparatif", f"Importance des critères : {weight_info}")
        table = pd.DataFrame({
            "Rang": [MEDALS[r - 1] if r <= 3 else str(r) for r in _ranks(scores)],
            "Option": alts,
            "Score": scores,
        })
        for m, r in results.items():
            table[f"Rang {METHODS[m][0]}"] = "—" if isinstance(r, ValueError) else _ranks(r["scores"]).astype(str)
        table = table.iloc[order]
        st.dataframe(table, hide_index=True, width="stretch", column_config={
            "Score": st.column_config.ProgressColumn("Score", format="%.4f", min_value=0,
                                                     max_value=float(scores.max()) or 1.0)})
        st.download_button("Exporter les résultats (CSV)", icon=":material/download:",
                           data=table.to_csv(index=False, sep=";").encode("utf-8-sig"),
                           file_name="resultats_decision.csv", mime="text/csv")

    with st.expander("Détail des calculs (pour les experts)", icon=":material/calculate:"):
        st.write("Matrice de décision (appréciations converties en notes de 1 à 5, "
                 "comparaisons deux à deux converties en priorités locales) :")
        st.dataframe(pd.DataFrame(problem.X, index=alts, columns=crits))
        st.write("Matrice normalisée :")
        st.dataframe(pd.DataFrame(res["R"], index=alts, columns=crits).round(4))
        if method == "TOPSIS":
            st.write("Matrice normalisée pondérée et solutions idéales :")
            st.dataframe(pd.DataFrame(res["V"], index=alts, columns=crits).round(4))
            st.dataframe(pd.DataFrame([res["ideal_pos"], res["ideal_neg"]], index=["Idéal A+", "Anti-idéal A−"],
                                      columns=crits).round(4))
            st.dataframe(pd.DataFrame({"Distance à A+": res["d_pos"], "Distance à A−": res["d_neg"],
                                       "Proximité C*": scores}, index=alts).round(4))
        if problem.local:
            st.write("Cohérence des comparaisons d'options (par critère) :")
            st.dataframe(pd.DataFrame({label: [r[k] for r in problem.local.values()]
                                       for k, label in (("lambda_max", "λ max"), ("CI", "CI"), ("CR", "CR"))},
                                      index=list(problem.local)).round(4))
        if method == "AHP":
            st.write("Contribution de chaque critère à la priorité finale (w_j × p_ij) :")
            st.dataframe(pd.DataFrame(res["R"] * weights, index=alts, columns=crits)
                         .assign(**{"Priorité finale": scores}).round(4))
        if method == "WASPAS":
            st.dataframe(pd.DataFrame({"WSM": res["WSM"], "WPM": res["WPM"], "WASPAS": scores},
                                      index=alts).round(4))
