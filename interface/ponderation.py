"""Onglet 3 : déterminer l'importance (le poids) de chaque critère."""
import numpy as np
import pandas as pd
import streamlit as st

from mcdm import bwm, critic, entropy

from . import charts, pairwise, style
from .state import CRITERIA_PREFIX, SAATY, default

METHODS = {
    "AHP": ("Comparer les critères deux à deux",
            "Le plus précis : une question pour chaque paire de critères (méthode AHP)."),
    "BWM": ("Désigner le plus et le moins important",
            "Plus rapide : moins de questions pour un résultat fiable (méthode Best-Worst)."),
    "ENT": ("Laisser les données décider — Entropie",
            "Un critère pèse plus s'il différencie bien les options."),
    "CRITIC": ("Laisser les données décider — CRITIC",
               "Tient compte de l'écart entre les options et des critères redondants."),
    "MAN": ("Fixer les poids moi-même",
            "Vous indiquez directement l'importance de chaque critère sur 10."),
}


def _ahp(problem):
    crits = problem.criteria
    n = len(crits)
    st.write(f"Répondez aux **{n * (n - 1) // 2} questions** ci-dessous. "
             "Il n'y a pas de bonne ou de mauvaise réponse : seules vos priorités comptent.")
    A = pairwise.questions(
        crits, CRITERIA_PREFIX,
        ask=lambda a, b: f"**{a}** ou **{b}** : lequel compte le plus pour vous ?",
        how_much=lambda w, o: f"De combien **{w}** est-il plus important que **{o}** ?",
        scale=SAATY, equal_label="Autant l'un que l'autre")
    res = pairwise.feedback(A, crits, "plus important que")
    return res["weights"], f"AHP — cohérence {res['CR']:.1%}"


def _pick(label, options, key, fallback):
    if st.session_state.get(key) not in options:
        st.session_state[key] = fallback
    return st.selectbox(label, options, key=key)


def _bwm(problem):
    crits = problem.criteria
    c1, c2 = st.columns(2)
    with c1:
        best = _pick("Quel est le critère **le plus** important ?", crits, "w_bwm_best", crits[0])
    with c2:
        worst = _pick("Quel est le critère **le moins** important ?", crits, "w_bwm_worst", crits[-1])
    if best == worst:
        st.error("Choisissez deux critères différents.")
        return None, ""

    fmt = lambda x: f"{x} · {SAATY[x]}"
    b, w = crits.index(best), crits.index(worst)
    bo, ow = np.ones(len(crits)), np.ones(len(crits))
    col_bo, col_ow = st.columns(2, gap="medium")
    with col_bo, st.container(border=True):
        st.markdown(f"À quel point **{best}** est-il plus important…")
        for j, c in enumerate(crits):
            if j != b:
                bo[j] = st.select_slider(f"…que **{c}** ?", options=list(range(1, 10)), format_func=fmt,
                                         key=default(f"w_bwm_bo_{best}|{c}", 5 if j == w else 3))
    with col_ow, st.container(border=True):
        st.markdown(f"À quel point chaque critère est-il plus important que **{worst}** ?")
        for j, c in enumerate(crits):
            if j not in (b, w):
                ow[j] = st.select_slider(f"**{c}**", options=list(range(1, 10)), format_func=fmt,
                                         key=default(f"w_bwm_ow_{c}|{worst}", 3))
        ow[b] = bo[w]  # déjà demandé dans la colonne de gauche
        st.caption(f"{best} par rapport à {worst} : déjà indiqué à gauche ({int(bo[w])}).")

    if bo.max() > bo[w]:
        st.warning(f"Attention : un critère est jugé encore moins important que **{worst}** "
                   "par rapport au meilleur. Vérifiez vos réponses.", icon=":material/warning:")
    res = bwm(b, w, bo, ow)
    if res["CR"] < 0.1:
        st.success(f"Vos réponses sont cohérentes (ratio de cohérence {res['CR']:.1%}).",
                   icon=":material/check_circle:")
    else:
        st.warning(f"Vos réponses manquent un peu de cohérence (ratio {res['CR']:.1%}). "
                   "Les poids restent utilisables, mais n'hésitez pas à les revoir.", icon=":material/warning:")
    return res["weights"], f"BWM — cohérence {res['CR']:.1%}"


def _manual(problem):
    st.write("Donnez une note d'importance de 0 à 10 à chaque critère. "
             "Les poids sont ensuite calculés automatiquement (ils totalisent 100 %).")
    cols = st.columns(min(len(problem.criteria), 3), gap="medium")
    scores = np.array([
        cols[j % len(cols)].slider(c, 0, 10, key=default(f"w_man_{c}", 5))
        for j, c in enumerate(problem.criteria)
    ], dtype=float)
    if scores.sum() == 0:
        st.error("Au moins un critère doit avoir une importance supérieure à 0.")
        return None, ""
    return scores / scores.sum(), "Poids fixés manuellement"


def render(problem):
    """Renvoie (poids, description de la méthode) ou (None, '') si les poids ne sont pas disponibles."""
    if not problem.is_defined:
        st.info("Commencez par définir vos options et vos critères dans l'onglet **Projet**.")
        return None, ""

    with st.container(key="card_method"):
        style.section(5, "Quels critères comptent le plus pour vous ?",
                      "Choisissez la façon dont vous souhaitez exprimer vos priorités.")
        method = st.radio("Méthode", list(METHODS), key=default("w_weight_method", "AHP"),
                          format_func=lambda m: METHODS[m][0], captions=[d for _, d in METHODS.values()],
                          label_visibility="collapsed")

    weights, info = None, ""
    with st.container(key="card_questions"):
        try:
            if method == "AHP":
                weights, info = _ahp(problem)
            elif method == "BWM":
                weights, info = _bwm(problem)
            elif method == "MAN":
                weights, info = _manual(problem)
            elif problem.X is None:
                st.info("Cette méthode calcule les poids à partir de vos évaluations : "
                        "complétez d'abord l'onglet **Évaluations**.")
            elif method == "ENT":
                weights, info = entropy(problem.X)["weights"], "Entropie (calcul objectif)"
                st.write("Les poids sont calculés automatiquement à partir de vos évaluations.")
            else:
                weights, info = critic(problem.X, problem.benefit)["weights"], "CRITIC (calcul objectif)"
                st.write("Les poids sont calculés automatiquement à partir de vos évaluations.")
        except ValueError as e:
            st.error(f"Calcul impossible : {e}")
            return None, ""

    if weights is None:
        return None, ""

    with st.container(key="card_weights"):
        style.section(6, "Importance de chaque critère")
        c1, c2 = st.columns([3, 2], gap="large")
        c1.plotly_chart(charts.weights_donut(problem.criteria, weights), width="stretch",
                        config={"displayModeBar": False})
        c2.dataframe(pd.DataFrame({"Critère": problem.criteria, "Poids": weights * 100}),
                     hide_index=True, width="stretch",
                     column_config={"Poids": st.column_config.ProgressColumn(
                         "Poids", format="%.1f %%", min_value=0, max_value=100)})
        st.success("Étape suivante : l'onglet **Résultats**.", icon=":material/arrow_forward:")
    return weights, info
