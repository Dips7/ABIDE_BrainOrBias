"""Per-site paired AUC variance (DeLong et al., 1988) and random-effects
meta-analysis with the Hartung-Knapp-Sidik-Jonkman adjustment (IntHout et al., 2014)."""

from __future__ import annotations

import numpy as np
from scipy import stats


def _placements(pos: np.ndarray, neg: np.ndarray):
    """DeLong structural components with mid-rank tie handling."""
    v10 = ((pos[:, None] > neg[None, :]) + 0.5 * (pos[:, None] == neg[None, :])).mean(axis=1)
    v01 = ((pos[:, None] > neg[None, :]) + 0.5 * (pos[:, None] == neg[None, :])).mean(axis=0)
    return v10, v01


def delong_paired_delta(y, s_a, s_b) -> dict:
    """ΔAUC = AUC(s_b) - AUC(s_a) on the same subjects, with DeLong variance."""
    y = np.asarray(y).astype(bool)
    comps = []
    aucs = []
    for s in (np.asarray(s_a), np.asarray(s_b)):
        v10, v01 = _placements(s[y], s[~y])
        comps.append((v10, v01))
        aucs.append(v10.mean())
    m, n = y.sum(), (~y).sum()
    V10 = np.vstack([comps[0][0], comps[1][0]])
    V01 = np.vstack([comps[0][1], comps[1][1]])
    S10 = np.cov(V10)
    S01 = np.cov(V01)
    S = S10 / m + S01 / n
    contrast = np.array([-1.0, 1.0])
    var = float(contrast @ S @ contrast)
    return {"auc_a": float(aucs[0]), "auc_b": float(aucs[1]), "delta": float(aucs[1] - aucs[0]),
            "var": var, "se": float(np.sqrt(max(var, 0.0))), "n_pos": int(m), "n_neg": int(n)}


def random_effects_hksj(effects, variances, alpha: float = 0.05) -> dict:
    """DerSimonian-Laird tau^2 with HKSJ-adjusted CI and a prediction interval."""
    y = np.asarray(effects, dtype=float)
    v = np.asarray(variances, dtype=float)
    k = len(y)
    w = 1.0 / v
    mu_fe = np.sum(w * y) / np.sum(w)
    q = float(np.sum(w * (y - mu_fe) ** 2))
    c = np.sum(w) - np.sum(w ** 2) / np.sum(w)
    tau2 = max(0.0, (q - (k - 1)) / c)
    i2 = max(0.0, (q - (k - 1)) / q) if q > 0 else 0.0
    wr = 1.0 / (v + tau2)
    mu = float(np.sum(wr * y) / np.sum(wr))
    var_hksj = float(np.sum(wr * (y - mu) ** 2) / ((k - 1) * np.sum(wr)))
    se = float(np.sqrt(var_hksj))
    t1 = stats.t.ppf(1 - alpha / 2, k - 1)
    t2 = stats.t.ppf(1 - alpha / 2, k - 2)
    pi_half = t2 * np.sqrt(tau2 + var_hksj)
    p = float(2 * stats.t.sf(abs(mu / se), k - 1)) if se > 0 else float("nan")
    return {"k": int(k), "mu": mu, "se_hksj": se, "ci_lo": mu - t1 * se, "ci_hi": mu + t1 * se,
            "p_hksj": p, "tau2": float(tau2), "tau": float(np.sqrt(tau2)), "Q": q, "I2": float(i2),
            "pi_lo": float(mu - pi_half), "pi_hi": float(mu + pi_half), "mu_fixed": float(mu_fe)}
