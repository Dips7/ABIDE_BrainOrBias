"""ComBat harmonization (Johnson et al., 2007; Fortin et al., 2018) that is fitted on
training data and applied to held-out data, for use inside a scikit-learn pipeline.

Design (Aim 2, RESEARCH_PROPOSAL_ABIDE.md §4.3):
* batch = SITE_ID; protected covariates = age and sex only. Diagnosis is NOT
  protected (that would need test labels).
* Location/scale model, parametric empirical Bayes, matching neuroCombat 0.2.12
  conventions (validated in tests/test_aim2.py).
* fit() estimates the covariate betas, grand mean, pooled variance and the per-site
  EB parameters from training rows only.
* transform() standardises new rows with the training estimates. Sites seen in
  training use their stored EB parameters. A site not seen in training (LOIO) gets
  its own EB parameters estimated from its rows' features, age and sex, using the
  training standardisation and **no diagnosis labels** (reference-batch-style
  extension; see analyses/DEVIATIONS.md, clarification 11).
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator, TransformerMixin


def _aprior(d):
    m, s2 = np.mean(d), np.var(d, ddof=1)
    return (2 * s2 + m ** 2) / s2


def _bprior(d):
    m, s2 = np.mean(d), np.var(d, ddof=1)
    return (m * s2 + m ** 3) / s2


def _eb_site(sdat: np.ndarray, conv: float = 1e-4, max_iter: int = 1000):
    """Parametric EB estimates for one site. sdat: (n_site, p) standardised data."""
    g_hat = sdat.mean(axis=0)
    d_hat = sdat.var(axis=0, ddof=1)
    d_hat[d_hat == 0] = 1.0
    g_bar = g_hat.mean()
    t2 = g_hat.var(ddof=1)
    a, b = _aprior(d_hat), _bprior(d_hat)
    n = sdat.shape[0]
    g_old, d_old = g_hat.copy(), d_hat.copy()
    for _ in range(max_iter):
        g_new = (t2 * n * g_hat + d_old * g_bar) / (t2 * n + d_old)
        sum2 = ((sdat - g_new) ** 2).sum(axis=0)
        d_new = (0.5 * sum2 + b) / (n / 2.0 + a - 1.0)
        change = max(np.max(np.abs(g_new - g_old) / np.abs(g_old)),
                     np.max(np.abs(d_new - d_old) / d_old))
        g_old, d_old = g_new, d_new
        if change <= conv:
            break
    return g_new, d_new


class ComBatHarmonizer(BaseEstimator, TransformerMixin):
    """Harmonise ``feature_cols`` across ``batch_col``, protecting ``covariate_cols``.

    Input is a DataFrame holding all of these columns; output is a float array of the
    harmonised features (in ``feature_cols`` order). Missing feature values are
    median-imputed using training medians first. Features with zero training
    variance are passed through unchanged.
    """

    def __init__(self, feature_cols, batch_col="SITE_ID", covariate_cols=("AGE_AT_SCAN", "SEX"),
                 min_site_n: int = 2):
        self.feature_cols = feature_cols
        self.batch_col = batch_col
        self.covariate_cols = covariate_cols
        self.min_site_n = min_site_n

    # ---------------------------------------------------------------- helpers
    def _cov(self, X: pd.DataFrame) -> np.ndarray:
        return X[list(self.covariate_cols)].to_numpy(dtype=float)

    def _feat(self, X: pd.DataFrame) -> np.ndarray:
        F = np.array(X[list(self.feature_cols)].to_numpy(dtype=float), copy=True)
        if hasattr(self, "medians_"):
            r, c = np.where(np.isnan(F))
            F[r, c] = self.medians_[c]
        return F

    def _standardise(self, F, C):
        return (F - self.grand_mean_ - C @ self.beta_cov_) / np.sqrt(self.var_pooled_)

    # ---------------------------------------------------------------- API
    def fit(self, X: pd.DataFrame, y=None):
        F = X[list(self.feature_cols)].to_numpy(dtype=float)
        self.medians_ = np.nanmedian(F, axis=0)
        F = self._feat(X)
        C = self._cov(X)
        batch = X[self.batch_col].astype(str).to_numpy()
        self.batches_ = np.unique(batch)
        counts = np.array([(batch == b).sum() for b in self.batches_])
        if counts.min() < self.min_site_n:
            raise ValueError(f"ComBat needs >= {self.min_site_n} training rows per site")
        B = (batch[:, None] == self.batches_[None, :]).astype(float)
        design = np.hstack([B, C])
        coef, *_ = np.linalg.lstsq(design, F, rcond=None)
        nb = len(self.batches_)
        self.grand_mean_ = (counts / counts.sum()) @ coef[:nb]
        self.beta_cov_ = coef[nb:]
        resid = F - design @ coef
        var = (resid ** 2).mean(axis=0)
        self.passthrough_ = var <= 1e-12
        var[self.passthrough_] = 1.0
        self.var_pooled_ = var
        S = self._standardise(F, C)
        self.gamma_star_, self.delta_star_ = {}, {}
        for b in self.batches_:
            g, d = _eb_site(S[batch == b][:, ~self.passthrough_])
            self.gamma_star_[b], self.delta_star_[b] = g, d
        self.n_unseen_sites_ = 0
        return self

    def transform(self, X: pd.DataFrame) -> np.ndarray:
        F = self._feat(X)
        C = self._cov(X)
        batch = X[self.batch_col].astype(str).to_numpy()
        S = self._standardise(F, C)
        out = F.copy()
        keep = ~self.passthrough_
        mean_part = self.grand_mean_ + C @ self.beta_cov_
        for b in np.unique(batch):
            rows = batch == b
            if b in self.gamma_star_:
                g, d = self.gamma_star_[b], self.delta_star_[b]
            else:
                if rows.sum() < self.min_site_n:
                    raise ValueError(f"Unseen site {b!r} has < {self.min_site_n} rows")
                g, d = _eb_site(S[rows][:, keep])  # label-free, test site's own rows
            adj = (S[rows][:, keep] - g) / np.sqrt(d)
            out[np.ix_(rows, keep)] = adj * np.sqrt(self.var_pooled_[keep]) + mean_part[rows][:, keep]
        return out

    def get_feature_names_out(self, input_features=None):
        return np.asarray(self.feature_cols, dtype=object)
