"""Tests for analyses/harmonize.py (ComBat) and analyses/meta.py (DeLong, HKSJ)."""

import os
import sys
import warnings

import numpy as np
import pandas as pd
import pytest
from sklearn.metrics import roc_auc_score

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import common as cm  # noqa: E402
from harmonize import ComBatHarmonizer  # noqa: E402
from meta import delong_paired_delta, random_effects_hksj  # noqa: E402

COV = ["AGE_AT_SCAN", "SEX"]


@pytest.fixture(scope="module")
def abide():
    df = cm.load_data()
    g = cm.brain_groups()
    feats = [f for f in g["all"] if df[f].var() > 1e-12 and df[f].notna().all()]
    return df, feats


def test_combat_matches_neurocombat_on_full_data(abide):
    neuroCombat = pytest.importorskip("neuroCombat").neuroCombat
    df, feats = abide
    feats = feats[:40]
    covars = df[[cm.SITE] + COV].copy()
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        ref = neuroCombat(dat=df[feats].to_numpy().T, covars=covars, batch_col=cm.SITE,
                          continuous_cols=COV)["data"].T
    ours = ComBatHarmonizer(feats).fit(df).transform(df)
    np.testing.assert_allclose(ours, ref, rtol=1e-4, atol=1e-6 * np.abs(ref).max())


def test_combat_seen_site_rows_are_independent(abide):
    df, feats = abide
    tr, te = df.iloc[::2], df.iloc[1::2]
    h = ComBatHarmonizer(feats[:20]).fit(tr)
    batch = h.transform(te)
    one = h.transform(te.iloc[[5]])
    np.testing.assert_allclose(one[0], batch[5])


def test_combat_fit_ignores_labels(abide):
    df, feats = abide
    a = ComBatHarmonizer(feats[:20]).fit(df, df[cm.TARGET]).transform(df)
    b = ComBatHarmonizer(feats[:20]).fit(df, 1 - df[cm.TARGET]).transform(df)
    np.testing.assert_array_equal(a, b)


def test_combat_unseen_site_uses_only_its_own_rows(abide):
    df, feats = abide
    held = df[cm.INSTITUTION] == "NYU"
    h = ComBatHarmonizer(feats[:20]).fit(df[~held])
    te = df[held]
    alone = h.transform(te)
    mixed = h.transform(pd.concat([te, df[~held].iloc[:50]]))
    np.testing.assert_allclose(alone, mixed[: len(te)])
    assert np.isfinite(alone).all()


def test_combat_removes_synthetic_site_shift():
    rng = np.random.default_rng(0)
    n, sites = 400, np.repeat(["A", "B", "C", "D"], 100)
    shift = {"A": 0.0, "B": 2.0, "C": -1.5, "D": 1.0}
    age = rng.uniform(6, 40, n)
    X = pd.DataFrame({"SITE_ID": sites, "AGE_AT_SCAN": age, "SEX": rng.integers(1, 3, n)})
    for j in range(10):
        X[f"f{j}"] = 0.05 * age + rng.normal(0, 1, n) + np.array([shift[s] for s in sites])
    feats = [f"f{j}" for j in range(10)]
    H = ComBatHarmonizer(feats).fit(X).transform(X)
    site_means = pd.DataFrame(H).groupby(sites).mean()
    raw_means = X[feats].groupby(sites).mean()
    assert site_means.std().max() < 0.25 * raw_means.std().min()
    # age effect is preserved
    assert np.corrcoef(H[:, 0], age)[0, 1] > 0.3


def test_combat_passes_constant_features_through():
    X = pd.DataFrame({"SITE_ID": list("aabb") * 5, "AGE_AT_SCAN": np.arange(20.0),
                      "SEX": [1, 2] * 10, "c": 0.0, "v": np.random.default_rng(1).normal(size=20)})
    H = ComBatHarmonizer(["c", "v"]).fit(X).transform(X)
    assert (H[:, 0] == 0).all()


def test_delong_auc_and_variance():
    rng = np.random.default_rng(2)
    y = rng.integers(0, 2, 300)
    a = rng.normal(size=300) + 0.3 * y
    b = a + rng.normal(scale=0.7, size=300) + 0.3 * y
    r = delong_paired_delta(y, a, b)
    assert r["auc_a"] == pytest.approx(roc_auc_score(y, a))
    assert r["auc_b"] == pytest.approx(roc_auc_score(y, b))
    boots = []
    for _ in range(1500):
        i = rng.integers(0, 300, 300)
        boots.append(roc_auc_score(y[i], b[i]) - roc_auc_score(y[i], a[i]))
    assert r["var"] == pytest.approx(np.var(boots), rel=0.2)


def test_hksj_matches_statsmodels_reference():
    eff = np.array([0.1, 0.3, 0.2, 0.5])
    var = np.array([0.01, 0.02, 0.015, 0.03])
    r = random_effects_hksj(eff, var)
    # statsmodels.stats.meta_analysis.combine_effects(method_re="dl"), "random effect wls" row
    assert r["mu"] == pytest.approx(0.236519, abs=1e-6)
    assert r["se_hksj"] == pytest.approx(0.079604, abs=1e-6)
    assert r["tau2"] == pytest.approx(0.007875, abs=1e-9)
    assert r["I2"] == pytest.approx(0.318182, abs=1e-6)
    assert r["Q"] == pytest.approx(4.4, abs=1e-9)
    assert r["pi_lo"] < r["ci_lo"] < r["mu"] < r["ci_hi"] < r["pi_hi"]
