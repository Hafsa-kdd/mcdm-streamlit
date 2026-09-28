import numpy as np
from scipy.optimize import linprog

# Indice de consistance aléatoire (RI) de Saaty, indexé par la taille n de la matrice
RI = {1: 0.0, 2: 0.0, 3: 0.58, 4: 0.90, 5: 1.12, 6: 1.24, 7: 1.32, 8: 1.41, 9: 1.45, 10: 1.56}  # valeurs du cours

# Indice de consistance de BWM (Rezaei 2015), indexé par a_BW
BWM_CI = {1: 0.0, 2: 0.44, 3: 1.00, 4: 1.63, 5: 2.30, 6: 3.00, 7: 3.73, 8: 4.47, 9: 5.23}


def ahp(A):
   
    A = np.asarray(A, dtype=float)  # A : matrice de comparaison par paires (n x n), réciproque (a_ji = 1 / a_ij)
    n = A.shape[0]
    if A.shape != (n, n):
        raise ValueError("La matrice de comparaison doit être carrée.")
    if np.any(A <= 0):
        raise ValueError("Les jugements de la matrice AHP doivent être strictement positifs.")

    col_sum = A.sum(axis=0)
    normalized = A / col_sum
    w = normalized.mean(axis=1)

    lambda_max = float(col_sum @ w)
    ci = (lambda_max - n) / (n - 1) if n > 2 else 0.0
    ri = RI.get(n, 1.56)
    cr = ci / ri if ri > 0 else 0.0

    return {
        "weights": w,
        "normalized": normalized,
        "lambda_max": lambda_max,
        "CI": ci,
        "RI": ri,
        "CR": cr,
        "consistent": cr < 0.1,
    }


def ahp_worst_judgment(A, w):
    # Repère le jugement le plus éloigné des poids obtenus (utile quand CR >= 0.1).
    # Renvoie (i, j, valeur cohérente suggérée w_i / w_j).
    A, w = np.asarray(A, dtype=float), np.asarray(w, dtype=float)
    ratio = A * w[None, :] / w[:, None]           # = 1 si le jugement a_ij est parfaitement cohérent
    deviation = np.maximum(ratio, 1 / ratio)
    np.fill_diagonal(deviation, 0)
    i, j = np.unravel_index(np.argmax(deviation), A.shape)
    return int(i), int(j), float(w[i] / w[j])


def bwm(best, worst, bo, ow):

    bo = np.asarray(bo, dtype=float)
    ow = np.asarray(ow, dtype=float)
    n = len(bo)
    if best == worst:
        raise ValueError("Le meilleur et le pire critère doivent être différents.")

    A_ub, b_ub = [], []
    for j in range(n):
        # Écart au meilleur critère :  ±(w_B - a_Bj w_j) - xi <= 0
        row = np.zeros(n + 1)
        row[best] += 1
        row[j] -= bo[j]
        row[n] = -1
        A_ub.append(row.copy())
        row[:n] *= -1
        A_ub.append(row)
        # Écart au pire critère :  ±(w_j - a_jW w_W) - xi <= 0
        row = np.zeros(n + 1)
        row[j] += 1
        row[worst] -= ow[j]
        row[n] = -1
        A_ub.append(row.copy())
        row[:n] *= -1
        A_ub.append(row)
    b_ub = np.zeros(len(A_ub))

    A_eq = [np.r_[np.ones(n), 0]]
    b_eq = [1]
    c = np.r_[np.zeros(n), 1]  # minimiser xi

    res = linprog(c, A_ub=A_ub, b_ub=b_ub, A_eq=A_eq, b_eq=b_eq,
                  bounds=[(0, None)] * (n + 1), method="highs")
    if not res.success:
        raise ValueError(f"Le programme linéaire BWM n'a pas convergé : {res.message}")

    w, xi = res.x[:n], res.x[n]
    a_bw = int(round(bo[worst]))
    ci = BWM_CI.get(a_bw, 0.0)
    return {
        "weights": w,
        "xi": xi,
        "CR": xi / ci if ci > 0 else 0.0,
        "A_ub": np.array(A_ub),
    }


def entropy(X):
    
    X = np.asarray(X, dtype=float)
    m = X.shape[0]
    if m < 2:
        raise ValueError("L'entropie nécessite au moins 2 alternatives.")
    if np.any(X < 0):
        raise ValueError("L'entropie nécessite des valeurs positives ou nulles.")

    P = X / X.sum(axis=0)
    with np.errstate(divide="ignore", invalid="ignore"):
        plogp = np.where(P > 0, P * np.log(P), 0.0)  # convention 0 * ln 0 = 0
    E = -plogp.sum(axis=0) / np.log(m)
    d = 1 - E
    if d.sum() == 0:
        raise ValueError("Tous les critères ont une entropie de 1 : aucun ne discrimine les alternatives.")

    return {"weights": d / d.sum(), "P": P, "E": E, "d": d}


def critic(X, benefit):
    X = np.asarray(X, dtype=float)
    benefit = np.asarray(benefit, dtype=bool)
    xmin, xmax = X.min(axis=0), X.max(axis=0)
    span = np.where(xmax - xmin == 0, 1, xmax - xmin)
    R = np.where(benefit, (X - xmin) / span, (xmax - X) / span)

    sigma = R.std(axis=0, ddof=1)
    with np.errstate(divide="ignore", invalid="ignore"):
        corr = np.corrcoef(R, rowvar=False)
    corr = np.nan_to_num(corr)  # critère constant : corrélation indéfinie -> 0
    C = sigma * (1 - corr).sum(axis=0)
    if C.sum() == 0:
        raise ValueError("Tous les critères sont constants : CRITIC ne peut pas les pondérer.")

    return {"weights": C / C.sum(), "R": R, "sigma": sigma, "corr": corr, "C": C}
