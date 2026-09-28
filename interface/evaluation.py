"""Onglet 2 : évaluer chaque option sur chaque critère."""
import numpy as np
import pandas as pd
import streamlit as st

from . import pairwise, style
from .state import QUALI_SCALE, SAATY_BETTER, options_prefix


def _label(problem, j):
    crit, unit = problem.criteria[j], problem.units[j]
    arrow = "↑" if problem.benefit[j] else "↓"
    return f"{crit} ({unit}) {arrow}" if unit else f"{crit} {arrow}"


def _table(problem, cols):
    """Tableau des critères chiffrés et d'appréciation. Renvoie la matrice (m x len(cols)) ou None."""
    values = st.session_state["values"]
    # Tableau pré-rempli avec les réponses déjà données (retrouvées par nom d'option et de critère)
    data, column_config = {}, {}
    for j in cols:
        crit, quali = problem.criteria[j], problem.qualitative[j]
        col = []
        for alt in problem.alternatives:
            val = values.get((alt, crit))
            if quali:
                col.append(val if val in QUALI_SCALE else None)
            else:
                col.append(float(val) if isinstance(val, (int, float)) and not pd.isna(val) else None)
        data[crit] = pd.Series(col, dtype=object if quali else float)
        column_config[crit] = (st.column_config.SelectboxColumn(_label(problem, j), options=QUALI_SCALE) if quali
                               else st.column_config.NumberColumn(_label(problem, j), format="%.2f"))
    base = pd.DataFrame(data)
    base.index = problem.alternatives

    crits = [problem.criteria[j] for j in cols]
    signature = hash((tuple(problem.alternatives), tuple(crits), tuple(problem.qualitative[j] for j in cols)))
    with st.container(key="card_matrix"):
        style.section(4, "Évaluez chaque option",
                      "Pour chaque option, indiquez sa valeur ou votre appréciation sur chaque critère. "
                      "↑ : plus c'est élevé, mieux c'est — ↓ : plus c'est bas, mieux c'est.")
        edited = st.data_editor(base, key=f"ed_matrix_{st.session_state['version']}_{signature}",
                                column_config=column_config, width="stretch")

    for alt in problem.alternatives:
        for crit in crits:
            values[(alt, crit)] = edited.at[alt, crit]

    missing = int(edited.isna().sum().sum())
    if missing:
        st.warning(f"Il reste {missing} case(s) à remplir dans le tableau.", icon=":material/edit:")
        return None
    return np.column_stack([
        [QUALI_SCALE.index(v) + 1 for v in edited[c]] if problem.qualitative[j] else edited[c].astype(float)
        for j, c in zip(cols, crits)
    ])


def _pairwise(problem, j, num):
    """Comparaisons des options deux à deux sur le critère j. Renvoie les priorités locales."""
    crit, alts = problem.criteria[j], problem.alternatives
    with st.container(key=f"card_pair_{j}"):
        style.section(num, f"Comparez les options sur « {crit} »",
                      f"{len(alts) * (len(alts) - 1) // 2} question(s) : pour chaque paire, "
                      "indiquez quelle option est la meilleure sur ce critère, et de combien.")
        A = pairwise.questions(
            alts, options_prefix(crit),
            ask=lambda a, b: f"Sur le critère **{crit}** : **{a}** ou **{b}** ?",
            how_much=lambda w, o: f"De combien **{w}** est-elle meilleure que **{o}** ?",
            scale=SAATY_BETTER, equal_label="Équivalentes")
        res = pairwise.feedback(A, alts, "meilleure que")
    problem.local[crit] = res
    return res["weights"]


def render(problem):
    if not problem.is_defined:
        st.info("Commencez par définir vos options et vos critères dans l'onglet **Projet**.")
        return

    n = len(problem.criteria)
    table_cols = [j for j in range(n) if not problem.pairwise[j]]
    pair_cols = [j for j in range(n) if problem.pairwise[j]]

    X = np.empty((len(problem.alternatives), n))
    complete = True
    if table_cols:
        T = _table(problem, table_cols)
        if T is None:
            complete = False
        else:
            X[:, table_cols] = T
    for k, j in enumerate(pair_cols, start=1):
        # Priorités locales AHP : elles remplacent la colonne du critère dans la matrice de décision
        X[:, j] = _pairwise(problem, j, f"4.{k}" if table_cols else str(4 + k - 1))

    if not complete:
        return
    constant = [c for j, c in enumerate(problem.criteria) if np.ptp(X[:, j]) < 1e-12]
    if constant:
        st.info(f"Toutes les options ont la même évaluation sur : {', '.join(constant)}. "
                "Ce critère ne les départage pas.", icon=":material/info:")
    problem.X = X
    st.success("Évaluations complètes. Étape suivante : l'onglet **Importance des critères**.",
               icon=":material/arrow_forward:")
