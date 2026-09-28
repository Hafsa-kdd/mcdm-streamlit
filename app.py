"""Décidia — outil d'aide à la décision multicritère.

Lancer avec :  streamlit run app.py
"""
import streamlit as st

from interface import evaluation, ponderation, projet, resultats, state, style

st.set_page_config(page_title="MCDM — Aide à la décision", page_icon="🟣", layout="wide")
state.init()
style.inject()

with st.sidebar:
    style.brand()

style.hero(st.session_state.get("w_title") or "Nouvelle décision",
           "Comparez vos options pas à pas et obtenez une recommandation argumentée.")

tabs = st.tabs([":material/assignment: Projet", ":material/edit_note: Évaluations",
                ":material/balance: Importance des critères", ":material/emoji_events: Résultats"])
with tabs[0]:
    problem = projet.render()
with tabs[1]:
    evaluation.render(problem)
with tabs[2]:
    weights, weight_info = ponderation.render(problem)
with tabs[3]:
    resultats.render(problem, weights, weight_info)

# Barre latérale : avancement du projet (affichée après les calculs pour refléter l'état réel)
with st.sidebar:
    st.caption("AVANCEMENT")
    style.step("Projet", f"{len(problem.alternatives)} options · {len(problem.criteria)} critères",
               problem.is_defined)
    style.step("Évaluations", "Complètes" if problem.is_complete else "À compléter", problem.is_complete)
    style.step("Importance des critères", weight_info or "À définir", weights is not None)
    style.step("Résultats", "Disponibles" if problem.is_complete and weights is not None else "En attente",
               problem.is_complete and weights is not None)
    st.divider()
    st.button("Nouveau projet", icon=":material/add:", width="stretch", type="primary",
              on_click=state.load_project, kwargs={"example": False})
    st.button("Charger l'exemple", icon=":material/directions_car:", width="stretch",
              on_click=state.load_project, kwargs={"example": True})
