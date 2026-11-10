"""Unit tests for analyses/common.py."""

import os
import sys

import numpy as np
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import common as cm  # noqa: E402


@pytest.fixture(scope="module")
def df():
    return cm.load_data()


@pytest.fixture(scope="module")
def groups():
    return cm.brain_groups()


def test_load_data_cohort_and_derived_columns(df):
    assert len(df) == 1035
    assert df[cm.TARGET].sum() == 505
    assert df[cm.INSTITUTION].nunique() == 17
    assert df[cm.SITE].nunique() == 20
    assert int(df["RATER_FAIL_ANY"].sum()) == 143
    assert df["FIQ"].notna().sum() == 966
    assert df["func_mean_fd"].notna().sum() == 1034
    assert not (df[cm.CONFOUND_SETS["C3"]] == -9999).any().any()


def test_load_data_rejects_wrong_hash(tmp_path):
    p = tmp_path / "bad.csv"
    p.write_text("a,b\n1,2\n")
    with pytest.raises(ValueError, match="hash mismatch"):
        cm.load_data(str(p))


def test_brain_groups_partition(groups):
    parts = groups["thickness"] + groups["area"] + groups["subcortical"]
    assert sorted(parts) == sorted(groups["all"])
    assert len(set(parts)) == 174


def test_confound_sets_are_nested():
    c = cm.CONFOUND_SETS
    assert set(c["C0"]) < set(c["C1"]) < set(c["C3"])
    assert set(c["C0"]) < set(c["C2"]) < set(c["C3"])
    assert set(c["C3"]) == set(c["C1"]) | set(c["C2"])


def test_c0_reproduces_published_benchmark(df, groups):
    """C0 and C0+Brain with the benchmark's seed (42) must reproduce the frozen
    benchmark_results_summary.json pooled OOF AUCs."""
    y = df[cm.TARGET].to_numpy()
    splits = cm.kfold_splits(y, seeds=(42,))
    conf = cm.oof_scores(df, lambda: cm.make_pipeline(cm.CONFOUND_SETS["C0"], None, seed=42), splits)
    brain = cm.oof_scores(df, lambda: cm.make_pipeline(cm.CONFOUND_SETS["C0"], groups["all"], seed=42), splits)
    assert cm.pooled_auc(y, conf)[0] == pytest.approx(0.5245918176723332, abs=1e-9)
    assert cm.pooled_auc(y, brain)[0] == pytest.approx(0.5949785167195965, abs=1e-9)


def test_permute_within_preserves_groups():
    rng = np.random.default_rng(0)
    g = np.array(list("aaabbbbcc"))
    idx = cm.permute_within(g, rng)
    assert sorted(idx) == list(range(len(g)))
    assert (g[idx] == g).all()


def test_permuted_block_leaves_other_columns(df, groups):
    rng = np.random.default_rng(1)
    idx = cm.permute_within(df[cm.SITE].to_numpy(), rng)
    p = cm.with_permuted_block(df, groups["all"], idx)
    others = cm.CONFOUND_SETS["C3"] + [cm.SITE, cm.TARGET]
    assert p[others].equals(df[others])
    assert not p[groups["all"]].equals(df[groups["all"]])
    # every subject's brain row comes from someone at the same site
    assert (df[cm.SITE].to_numpy()[idx] == df[cm.SITE].to_numpy()).all()


def test_permutation_p():
    assert cm.permutation_p(1.0, np.zeros(999)) == pytest.approx(1 / 1000)
    assert cm.permutation_p(-1.0, np.zeros(999)) == pytest.approx(1.0)


def test_cluster_bootstrap_is_deterministic_and_brackets_zero_for_identical_scores():
    rng = np.random.default_rng(3)
    y = np.tile([0, 1], 100)
    s = rng.random(200)
    clusters = np.repeat(np.arange(10), 20)
    a = cm.cluster_bootstrap_delta(y, s, s, clusters, n_boot=200, seed=5)
    b = cm.cluster_bootstrap_delta(y, s, s, clusters, n_boot=200, seed=5)
    assert a == b
    assert a["lo"] == 0.0 and a["hi"] == 0.0


def test_svm_and_enet_pipelines_fit(df, groups):
    y = df[cm.TARGET].to_numpy()
    sub = df.iloc[:300]
    for fam in ("enet", "svm"):
        m = cm.make_pipeline(cm.CONFOUND_SETS["C3"], groups["subcortical"], family=fam)
        m.fit(sub, y[:300])
        assert cm._scores(m, sub).shape == (300,)


def test_repeat_bootstrap_brackets_reported_statistic():
    rng = np.random.default_rng(7)
    y = np.tile([0, 1], 150)
    clusters = np.repeat(np.arange(15), 20)
    S_conf = rng.random((3, 300))
    S_brain = S_conf + 0.6 * y + 0.3 * rng.random((3, 300))
    from sklearn.metrics import roc_auc_score as A
    point = np.mean([A(y, b) - A(y, c) for c, b in zip(S_conf, S_brain)])
    ci = cm.cluster_bootstrap_delta_repeats(y, S_conf, S_brain, clusters, n_boot=300, seed=1)
    assert ci["lo"] <= point <= ci["hi"]
    assert ci == cm.cluster_bootstrap_delta_repeats(y, S_conf, S_brain, clusters, n_boot=300, seed=1)
