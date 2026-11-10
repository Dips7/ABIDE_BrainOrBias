"""Calibration and decision-curve helpers (Aim 3, RESEARCH_PROPOSAL_ABIDE.md §4.6)."""

from __future__ import annotations

import numpy as np
import statsmodels.api as sm


def _logit(p, eps=1e-6):
    p = np.clip(np.asarray(p, dtype=float), eps, 1 - eps)
    return np.log(p / (1 - p))


def calibration(y, p) -> dict:
    """Calibration-in-the-large (intercept with logit(p) as offset), calibration
    slope (logistic regression of y on logit(p)), and Brier score."""
    y = np.asarray(y, dtype=float)
    lp = _logit(p)
    fam = sm.families.Binomial()
    intercept = sm.GLM(y, np.ones((len(y), 1)), family=fam, offset=lp).fit().params[0]
    slope_fit = sm.GLM(y, sm.add_constant(lp), family=fam).fit()
    return {"cal_intercept": float(intercept), "cal_slope": float(slope_fit.params[1]),
            "brier": float(np.mean((np.asarray(p) - y) ** 2))}


def net_benefit(y, p, thresholds) -> np.ndarray:
    """Net benefit of treating subjects with p >= t, for each threshold t."""
    y = np.asarray(y).astype(bool)
    p = np.asarray(p, dtype=float)
    n = len(y)
    out = []
    for t in thresholds:
        pos = p >= t
        tp = np.sum(pos & y) / n
        fp = np.sum(pos & ~y) / n
        out.append(tp - fp * t / (1 - t))
    return np.array(out)


def net_benefit_treat_all(y, thresholds) -> np.ndarray:
    prev = float(np.mean(y))
    t = np.asarray(thresholds, dtype=float)
    return prev - (1 - prev) * t / (1 - t)
