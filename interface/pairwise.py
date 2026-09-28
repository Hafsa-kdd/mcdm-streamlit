"""Questionnaire de comparaisons par paires (AHP), réutilisé pour les critères et pour les options."""
from itertools import combinations

import numpy as np
import streamlit as st

from mcdm import ahp, ahp_worst_judgment

from .state import EQUAL, default, pair_keys


def questions(items, prefix, ask, how_much, scale, equal_label):
    """Pose une question par paire d'éléments et renvoie la matrice de comparaison réciproque.

    ask(a, b)             -> texte de la question « lequel ? »
    how_much(gagnant, autre) -> texte de la question « de combien ? »
    scale                 -> libellés de l'échelle de 1 à 9
    """
    n = len(items)
    A = np.ones((n, n))
    grid = st.columns(2, gap="medium")
    for k, (i, j) in enumerate(combinations(range(n), 2)):
        a, b = items[i], items[j]
        k_choice, k_level = pair_keys(prefix, a, b)
        with grid[k % 2], st.container(border=True):
            st.markdown(ask(a, b))
            choice = st.radio("Choix", [a, EQUAL, b], key=default(k_choice, EQUAL), horizontal=True,
                              format_func=lambda x: equal_label if x == EQUAL else x,
                              label_visibility="collapsed")
            if choice == EQUAL:
                continue
            other = b if choice == a else a
            level = st.select_slider(how_much(choice, other), options=list(range(2, 10)),
                                     key=default(k_level, 3), format_func=lambda x: f"{x} · {scale[x]}")
            A[i, j] = level if choice == a else 1 / level
            A[j, i] = 1 / A[i, j]
    return A


def feedback(A, items, comparative):
    """Calcule les priorités AHP, affiche le verdict de cohérence et renvoie le résultat de ahp().

    comparative : ex. « plus important que », « meilleure que ».
    """
    res = ahp(A)
    if res["consistent"]:
        st.success(f"Réponses cohérentes (ratio de cohérence {res['CR']:.1%} < 10 %).",
                   icon=":material/check_circle:")
    else:
        i, j, suggested = ahp_worst_judgment(A, res["weights"])
        if suggested < 1:
            i, j, suggested = j, i, 1 / suggested
        st.warning(
            f"Vos réponses se contredisent un peu (ratio de cohérence {res['CR']:.1%}, il devrait rester "
            f"sous 10 %). Revoyez en priorité la comparaison **{items[i]} / {items[j]}** : d'après vos "
            f"autres réponses, **{items[i]}** serait environ **{max(1, round(suggested))} fois** "
            f"{comparative} **{items[j]}**.", icon=":material/warning:")
    return res
