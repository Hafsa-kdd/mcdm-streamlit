"""État de l'application : problème de décision, projet exemple, persistance des réponses."""
from dataclasses import dataclass, field

import numpy as np
import pandas as pd
import streamlit as st

MEASURE_NUM = "Valeur chiffrée"
MEASURE_QUALI = "Appréciation"
MEASURE_PAIR = "Comparaison deux à deux"
GOAL_MAX = "Le plus élevé possible"
GOAL_MIN = "Le plus bas possible"

# Échelle d'appréciation proposée pour les critères qualitatifs (score = position + 1)
QUALI_SCALE = ["Très faible", "Faible", "Moyen", "Bon", "Excellent"]

# Échelle de Saaty (1 à 9) en langage courant
SAATY = {
    1: "Autant l'un que l'autre",
    2: "Très légèrement plus important",
    3: "Un peu plus important",
    4: "Plus important",
    5: "Nettement plus important",
    6: "Beaucoup plus important",
    7: "Très nettement plus important",
    8: "Largement plus important",
    9: "Infiniment plus important",
}

# Même échelle, formulée pour comparer deux options sur un critère
SAATY_BETTER = {
    1: "Équivalentes",
    2: "Très légèrement meilleure",
    3: "Un peu meilleure",
    4: "Meilleure",
    5: "Nettement meilleure",
    6: "Beaucoup meilleure",
    7: "Très nettement meilleure",
    8: "Largement meilleure",
    9: "Infiniment meilleure",
}


@dataclass
class Problem:
    title: str = ""
    alternatives: list = field(default_factory=list)
    criteria: list = field(default_factory=list)
    benefit: list = field(default_factory=list)      # True = à maximiser
    qualitative: list = field(default_factory=list)  # True = critère d'appréciation
    pairwise: list = field(default_factory=list)     # True = options comparées deux à deux (AHP)
    units: list = field(default_factory=list)
    X: np.ndarray | None = None                      # None tant que la matrice est incomplète
    local: dict = field(default_factory=dict)        # critère -> résultat AHP des comparaisons d'options

    @property
    def is_defined(self):
        return len(self.alternatives) >= 2 and len(self.criteria) >= 2

    @property
    def is_complete(self):
        return self.is_defined and self.X is not None


EXAMPLE = {
    "title": "Choisir une nouvelle voiture",
    "alternatives": ["Voiture A", "Voiture B", "Voiture C", "Voiture D"],
    "criteria": [
        ("Prix", MEASURE_NUM, GOAL_MIN, "k€"),
        ("Consommation", MEASURE_NUM, GOAL_MIN, "L/100 km"),
        ("Confort", MEASURE_PAIR, GOAL_MAX, ""),
        ("Sécurité", MEASURE_QUALI, GOAL_MAX, ""),
    ],
    "values": {
        "Prix": [24, 27, 21, 30],
        "Consommation": [6.2, 5.1, 7.0, 5.6],
        "Sécurité": ["Bon", "Bon", "Moyen", "Excellent"],
    },
    # Comparaisons pré-remplies des options sur le confort : (a, b) -> (option préférée, intensité)
    "confort": {
        ("Voiture A", "Voiture B"): ("Voiture B", 3),
        ("Voiture A", "Voiture C"): ("Voiture A", 3),
        ("Voiture A", "Voiture D"): (None, 1),
        ("Voiture B", "Voiture C"): ("Voiture B", 5),
        ("Voiture B", "Voiture D"): ("Voiture B", 3),
        ("Voiture C", "Voiture D"): ("Voiture D", 3),
    },
    # Réponses AHP pré-remplies : (critère a, critère b) -> (critère préféré, intensité)
    "ahp": {
        ("Prix", "Consommation"): ("Prix", 2),
        ("Prix", "Confort"): ("Prix", 3),
        ("Prix", "Sécurité"): ("Sécurité", 2),
        ("Consommation", "Confort"): ("Consommation", 2),
        ("Consommation", "Sécurité"): ("Sécurité", 3),
        ("Confort", "Sécurité"): ("Sécurité", 4),
    },
}


def pair_keys(prefix, a, b):
    """Clés de session d'une question « a ou b ? » et de son intensité."""
    return f"{prefix}_choice_{a}|{b}", f"{prefix}_level_{a}|{b}"


CRITERIA_PREFIX = "w_ahp"
EQUAL = "="  # réponse « autant l'un que l'autre »


def options_prefix(criterion):
    return f"w_alt_{criterion}"


def _preset(prefix, answers):
    for (a, b), (winner, level) in answers.items():
        k_choice, k_level = pair_keys(prefix, a, b)
        st.session_state[k_choice] = winner or EQUAL
        if winner:
            st.session_state[k_level] = level


def load_project(example=True):
    """Réinitialise l'application, vide ou avec le projet exemple."""
    version = st.session_state.get("version", 0) + 1
    st.session_state.clear()
    st.session_state["version"] = version

    if not example:
        st.session_state["w_title"] = ""
        st.session_state["alts_base"] = pd.DataFrame({"Option": ["", ""]})
        st.session_state["crits_base"] = pd.DataFrame(
            {"Critère": ["", ""], "Mesure": [MEASURE_NUM] * 2, "Objectif": [GOAL_MAX] * 2, "Unité": ["", ""]})
        st.session_state["values"] = {}
        return

    ex = EXAMPLE
    st.session_state["w_title"] = ex["title"]
    st.session_state["alts_base"] = pd.DataFrame({"Option": ex["alternatives"]})
    st.session_state["crits_base"] = pd.DataFrame(ex["criteria"], columns=["Critère", "Mesure", "Objectif", "Unité"])
    st.session_state["values"] = {(alt, crit): vals[i]
                                  for crit, vals in ex["values"].items()
                                  for i, alt in enumerate(ex["alternatives"])}
    _preset(CRITERIA_PREFIX, ex["ahp"])
    _preset(options_prefix("Confort"), ex["confort"])


def init():
    if "version" not in st.session_state:
        load_project(example=True)
    # Streamlit oublie la valeur d'un widget qui n'est pas affiché pendant un rechargement
    # (ex. les questions BWM quand on est sur AHP). On la ré-enregistre pour la conserver.
    for k in list(st.session_state):
        if k.startswith("w_"):
            st.session_state[k] = st.session_state[k]


def default(key, value):
    """Fixe la valeur initiale d'un widget (une seule fois) et renvoie sa clé."""
    st.session_state.setdefault(key, value)
    return key
