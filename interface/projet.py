"""Onglet 1 : définir la décision, les options et les critères."""
import streamlit as st

from . import style
from .state import GOAL_MAX, GOAL_MIN, MEASURE_NUM, MEASURE_PAIR, MEASURE_QUALI, Problem


def _clean_names(series):
    return [str(v).strip() for v in series if v is not None and str(v).strip() not in ("", "nan", "None")]


def render():
    v = st.session_state["version"]

    with st.container(key="card_title"):
        style.section(1, "Quelle décision devez-vous prendre ?")
        st.text_input("Intitulé de la décision", key="w_title",
                      placeholder="Ex. : choisir un fournisseur, un logiciel, un site d'implantation…")

    col1, col2 = st.columns([1, 2], gap="medium")
    with col1, st.container(key="card_alts"):
        style.section(2, "Les options à comparer", "Ajoutez une ligne par option (au moins 2).")
        alts_df = st.data_editor(
            st.session_state["alts_base"], key=f"ed_alts_{v}", num_rows="dynamic",
            hide_index=True, width="stretch",
            column_config={"Option": st.column_config.TextColumn("Option", required=True)},
        )
    with col2, st.container(key="card_crits"):
        style.section(3, "Vos critères de choix", "Ce qui compte pour vous dans cette décision (au moins 2).")
        crits_df = st.data_editor(
            st.session_state["crits_base"], key=f"ed_crits_{v}", num_rows="dynamic",
            hide_index=True, width="stretch",
            column_config={
                "Critère": st.column_config.TextColumn("Critère", required=True),
                "Mesure": st.column_config.SelectboxColumn(
                    "Comment l'évaluer ?", options=[MEASURE_NUM, MEASURE_QUALI, MEASURE_PAIR],
                    default=MEASURE_NUM, required=True,
                    help="Valeur chiffrée : un prix, une durée, une distance…\n"
                         "Appréciation : de « Très faible » à « Excellent ».\n"
                         "Comparaison deux à deux : vous comparez les options par paires (méthode AHP), "
                         "idéal pour un critère difficile à chiffrer."),
                "Objectif": st.column_config.SelectboxColumn(
                    "Objectif", options=[GOAL_MAX, GOAL_MIN], default=GOAL_MAX, required=True,
                    help="Pour un prix ou un délai, on cherche la valeur la plus basse possible."),
                "Unité": st.column_config.TextColumn("Unité", help="Facultatif : €, jours, km…"),
            },
        )
        n_alts = len(_clean_names(alts_df["Option"]))
        st.caption("Pour une appréciation ou une comparaison deux à deux, la colonne « Objectif » est ignorée : "
                   "vous indiquez directement quelle option est la meilleure. "
                   f"Avec {n_alts} options, une comparaison deux à deux demande "
                   f"{n_alts * (n_alts - 1) // 2} question(s) par critère.")

    problem = Problem(title=st.session_state["w_title"].strip())
    problem.alternatives = _clean_names(alts_df["Option"])
    rows = crits_df[crits_df["Critère"].notna() & (crits_df["Critère"].astype(str).str.strip() != "")]
    problem.criteria = [str(c).strip() for c in rows["Critère"]]
    problem.qualitative = [m == MEASURE_QUALI for m in rows["Mesure"]]
    problem.pairwise = [m == MEASURE_PAIR for m in rows["Mesure"]]
    problem.benefit = [q or p or g != GOAL_MIN
                       for q, p, g in zip(problem.qualitative, problem.pairwise, rows["Objectif"])]
    problem.units = ["" if u is None or str(u) == "nan" else str(u).strip() for u in rows["Unité"]]

    errors = []
    if len(set(problem.alternatives)) != len(problem.alternatives):
        errors.append("Deux options portent le même nom.")
    if len(set(problem.criteria)) != len(problem.criteria):
        errors.append("Deux critères portent le même nom.")
    for e in errors:
        st.error(e)
    if errors:
        problem.alternatives, problem.criteria = [], []
    elif problem.is_defined:
        st.success(f"{len(problem.alternatives)} options et {len(problem.criteria)} critères définis. "
                   "Étape suivante : l'onglet **Évaluations**.", icon=":material/arrow_forward:")
    else:
        st.info("Définissez au moins 2 options et 2 critères pour continuer.")
    return problem
