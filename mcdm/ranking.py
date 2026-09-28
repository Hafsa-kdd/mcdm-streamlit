
import numpy as np


def _check(X, w, benefit):
    X = np.asarray(X, dtype=float)
    w = np.asarray(w, dtype=float)
    benefit = np.asarray(benefit, dtype=bool)
    if X.shape[1] != len(w) or len(w) != len(benefit):
        raise ValueError("Dimensions incohérentes entre la matrice, les poids et les types de critères.")
    return X, w, benefit


def swm_normalize(X, benefit):
    # Normalisation linéaire : x_ij / max_j (critère positif), min_j / x_ij (critère négatif)
    if np.any(X <= 0):
        raise ValueError("Les méthodes WSM/WPM/WASPAS nécessitent des valeurs strictement positives.")
    return np.where(benefit, X / X.max(axis=0), X.min(axis=0) / X)


def wsm(X, w, benefit):
    X, w, benefit = _check(X, w, benefit)
    R = swm_normalize(X, benefit)
    return {"scores": R @ w, "R": R}


def wpm(X, w, benefit):
    X, w, benefit = _check(X, w, benefit)
    R = swm_normalize(X, benefit)
    return {"scores": np.prod(R ** w, axis=1), "R": R}


def waspas(X, w, benefit, lam=0.5):
    s, p = wsm(X, w, benefit), wpm(X, w, benefit)
    return {"scores": lam * s["scores"] + (1 - lam) * p["scores"],
            "WSM": s["scores"], "WPM": p["scores"], "R": s["R"]}


def topsis(X, w, benefit):
    X, w, benefit = _check(X, w, benefit)
    norm = np.sqrt((X ** 2).sum(axis=0))
    if np.any(norm == 0):
        raise ValueError("Un critère a toutes ses valeurs nulles : normalisation impossible.")

    R = X / norm                                          # 1) normalisation vectorielle
    V = R * w                                             # 2) matrice pondérée
    v_pos = np.where(benefit, V.max(axis=0), V.min(axis=0))   # 3) idéal positif
    v_neg = np.where(benefit, V.min(axis=0), V.max(axis=0))   #    idéal négatif
    d_pos = np.sqrt(((V - v_pos) ** 2).sum(axis=1))       # 4) séparations
    d_neg = np.sqrt(((V - v_neg) ** 2).sum(axis=1))
    denom = d_pos + d_neg
    cc = np.divide(d_neg, denom, out=np.zeros_like(denom), where=denom > 0)  # 5) proximité

    return {"scores": cc, "R": R, "V": V, "ideal_pos": v_pos, "ideal_neg": v_neg,
            "d_pos": d_pos, "d_neg": d_neg}


def ahp_synthesis(X, w, benefit):
    # Synthèse AHP : P_i = sum_j w_j * p_ij, avec p_ij les priorités locales (chaque colonne somme à 1).
    # Les colonnes issues de comparaisons par paires sont déjà des priorités et restent inchangées.
    # Pour les valeurs mesurées : p_ij = x_ij / sum_i x_ij, et 1/x_ij pour un critère à minimiser.
    X, w, benefit = _check(X, w, benefit)
    if np.any(X < 0) or np.any(X[:, ~benefit] == 0):
        raise ValueError("AHP nécessite des valeurs positives (et non nulles pour un critère à minimiser).")
    V = np.where(benefit, X, 1 / np.where(X == 0, 1, X))
    total = V.sum(axis=0)
    if np.any(total == 0):
        raise ValueError("Un critère a toutes ses valeurs nulles : priorités impossibles à calculer.")
    R = V / total
    return {"scores": R @ w, "R": R}
