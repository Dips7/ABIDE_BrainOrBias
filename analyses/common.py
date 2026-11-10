"""Shared code for the v2 "Brain or Bias?" analyses.

Implements the pre-specified design in RESEARCH_PROPOSAL_ABIDE.md (tag
``analysis-plan-v2``): data loading, confound sets C0-C3, brain feature groups,
leakage-free pipelines, repeated cross-validation, within-group permutation of
the brain block, and site-cluster bootstrap intervals.

All preprocessing is fitted inside training folds only.
"""

from __future__ import annotations

import hashlib
import os
from dataclasses import dataclass

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.feature_selection import VarianceThreshold
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import GridSearchCV, LeaveOneGroupOut, StratifiedKFold
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.svm import LinearSVC

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_PATH = os.path.join(REPO_ROOT, "abide_freesurfer_tabular_dataset.csv")
MANIFEST_PATH = os.path.join(REPO_ROOT, "feature_manifest_174.csv")
DATA_SHA256 = "9c84f601fd22a7aaa1780983d42fa884c3ef9d38878a32e465a37bcd42d99b3c"

# Fixed seeds (pre-specified as "fixed seeds"; values recorded here).
REPEAT_SEEDS = tuple(20261110 + r for r in range(10))
PERMUTATION_SEED = 51110001
BOOTSTRAP_SEED = 51120001

# ---------------------------------------------------------------- variable sets
TARGET = "ASD_DIAGNOSIS"
SITE = "SITE_ID"
INSTITUTION = "INSTITUTION_ID"

DEMO_NUM = ["AGE_AT_SCAN", "SEX", "IntraCranialVol"]
COGNITION = ["FIQ"]
MOTION = ["func_mean_fd"]
T1_QUALITY = ["anat_cnr", "anat_snr", "anat_efc", "anat_fber", "anat_fwhm", "anat_qi1"]
RATER_FLAG = ["RATER_FAIL_ANY"]
RATER_COLS = ["qc_rater_1", "qc_anat_rater_2", "qc_anat_rater_3"]

CONFOUND_SETS = {
    "C0": DEMO_NUM,
    "C1": DEMO_NUM + COGNITION,
    "C2": DEMO_NUM + MOTION + T1_QUALITY + RATER_FLAG,
    "C3": DEMO_NUM + COGNITION + MOTION + T1_QUALITY + RATER_FLAG,
}


def sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def load_data(path: str = DATA_PATH, verify_hash: bool = True) -> pd.DataFrame:
    """Load the canonical ABIDE I table and derive analysis variables."""
    if verify_hash:
        digest = sha256_file(path)
        if digest != DATA_SHA256:
            raise ValueError(f"Dataset hash mismatch: {digest}")
    df = pd.read_csv(path, low_memory=False).copy()
    num_cols = DEMO_NUM + COGNITION + MOTION + T1_QUALITY
    for c in num_cols:
        df[c] = pd.to_numeric(df[c], errors="coerce")
        df.loc[df[c] == -9999, c] = np.nan
    df[INSTITUTION] = df[SITE].str.replace("_1", "", regex=False).str.replace("_2", "", regex=False)
    fails = df[RATER_COLS].astype(str).eq("fail")
    df["RATER_FAIL_COUNT"] = fails.sum(axis=1).astype(int)
    df["RATER_FAIL_ANY"] = (df["RATER_FAIL_COUNT"] >= 1).astype(float)
    df[TARGET] = df[TARGET].astype(int)
    return df.reset_index(drop=True)


def brain_groups(path: str = MANIFEST_PATH) -> dict[str, list[str]]:
    """Return the 174 brain features and the three pre-specified compartments."""
    m = pd.read_csv(path)
    comp = m["anatomical_compartment"]
    thickness = m.loc[comp.str.startswith("Cortical Thickness"), "feature_name"].tolist()
    area = m.loc[comp.str.startswith("Cortical Surface Area"), "feature_name"].tolist()
    cortical = set(thickness) | set(area)
    subcortical = [f for f in m["feature_name"] if f not in cortical]
    allf = m["feature_name"].tolist()
    assert len(allf) == 174 and len(thickness) == 70 and len(area) == 70 and len(subcortical) == 34
    return {"all": allf, "thickness": thickness, "area": area, "subcortical": subcortical}


# ---------------------------------------------------------------- pipelines
def make_classifier(family: str, C: float = 0.1, seed: int = 0):
    if family == "l1":
        return LogisticRegression(penalty="l1", solver="liblinear", C=C, random_state=seed)
    if family == "enet":
        return LogisticRegression(penalty="elasticnet", solver="saga", l1_ratio=0.5, C=C,
                                  max_iter=2500, tol=1e-3, random_state=seed)
    if family == "svm":
        return LinearSVC(C=C, max_iter=20000, random_state=seed)
    raise ValueError(family)


def make_pipeline(confounds: list[str], brain: list[str] | None, family: str = "l1",
                  C: float = 0.1, seed: int = 0, use_site: bool = True,
                  harmonize: bool = False) -> Pipeline:
    """Confound (+ brain) model. Mirrors the benchmark's matched pipelines; confound
    numerics additionally get missing-value indicators (no-op when nothing is missing).
    ``harmonize=True`` applies in-fold ComBat (harmonize.ComBatHarmonizer) to the brain
    block only, protecting age and sex (Aim 2)."""
    if brain and harmonize:
        from harmonize import ComBatHarmonizer
        brain_pipe = Pipeline([("combat", ComBatHarmonizer(list(brain))),
                               ("vt", VarianceThreshold(threshold=1e-5)),
                               ("scl", StandardScaler())])
        transformers = [
            ("num", Pipeline([("imp", SimpleImputer(strategy="median", add_indicator=True)),
                              ("scl", StandardScaler())]), list(confounds)),
        ]
        if use_site:
            transformers.append(("cat", OneHotEncoder(drop="first", handle_unknown="ignore"), [SITE]))
        transformers.append(("brain", brain_pipe, list(brain) + [SITE, "AGE_AT_SCAN", "SEX"]))
        return Pipeline([("pre", ColumnTransformer(transformers)),
                         ("clf", make_classifier(family, C=C, seed=seed))])
    transformers = [
        ("num", Pipeline([("imp", SimpleImputer(strategy="median", add_indicator=True)),
                          ("scl", StandardScaler())]), list(confounds)),
    ]
    if use_site:
        transformers.append(("cat", OneHotEncoder(drop="first", handle_unknown="ignore"), [SITE]))
    if brain:
        transformers.append(("brain", Pipeline([("imp", SimpleImputer(strategy="median")),
                                                 ("vt", VarianceThreshold(threshold=1e-5)),
                                                 ("scl", StandardScaler())]), list(brain)))
    return Pipeline([("pre", ColumnTransformer(transformers)),
                     ("clf", make_classifier(family, C=C, seed=seed))])


def make_tuned_pipeline(confounds, brain, family="l1", seed=0, inner_seed=0):
    """Nested-tuning variant (S6): inner 5-fold grid over C."""
    base = make_pipeline(confounds, brain, family=family, seed=seed)
    inner = StratifiedKFold(n_splits=5, shuffle=True, random_state=inner_seed)
    return GridSearchCV(base, {"clf__C": [0.01, 0.03, 0.1, 0.3, 1.0]},
                        scoring="roc_auc", cv=inner, n_jobs=1)


def _scores(model, X):
    if hasattr(model, "predict_proba"):
        try:
            return model.predict_proba(X)[:, 1]
        except AttributeError:
            pass
    return model.decision_function(X)


# ---------------------------------------------------------------- cross-validation
def kfold_splits(y: np.ndarray, seeds=REPEAT_SEEDS, n_splits: int = 5):
    """List (one per repeat) of lists of (train_idx, test_idx)."""
    out = []
    for s in seeds:
        cv = StratifiedKFold(n_splits=n_splits, shuffle=True, random_state=s)
        out.append(list(cv.split(np.zeros(len(y)), y)))
    return out


def loio_splits(groups: np.ndarray):
    return [list(LeaveOneGroupOut().split(np.zeros(len(groups)), groups=groups))]


def oof_scores(df: pd.DataFrame, model_factory, splits) -> np.ndarray:
    """Out-of-fold scores, shape (n_repeats, n_subjects)."""
    y = df[TARGET].to_numpy()
    out = np.full((len(splits), len(df)), np.nan)
    for r, folds in enumerate(splits):
        for tr, te in folds:
            m = model_factory()
            m.fit(df.iloc[tr], y[tr])
            out[r, te] = _scores(m, df.iloc[te])
    assert not np.isnan(out).any()
    return out


def pooled_auc(y: np.ndarray, scores: np.ndarray) -> np.ndarray:
    """Pooled out-of-fold AUC for each repeat."""
    return np.array([roc_auc_score(y, s) for s in np.atleast_2d(scores)])


@dataclass
class DeltaResult:
    auc_conf: np.ndarray   # per repeat
    auc_brain: np.ndarray  # per repeat

    @property
    def delta(self) -> np.ndarray:
        return self.auc_brain - self.auc_conf

    def summary(self) -> dict:
        d = self.delta
        return {
            "auc_conf_mean": float(self.auc_conf.mean()),
            "auc_brain_mean": float(self.auc_brain.mean()),
            "delta_mean": float(d.mean()),
            "delta_min": float(d.min()),
            "delta_max": float(d.max()),
            "n_repeats": int(len(d)),
        }


# ---------------------------------------------------------------- permutation
def permute_within(groups: np.ndarray, rng: np.random.Generator) -> np.ndarray:
    """Index array that permutes subjects only within each group label."""
    groups = np.asarray(groups)
    idx = np.arange(len(groups))
    for g in np.unique(groups):
        members = np.flatnonzero(groups == g)
        idx[members] = rng.permutation(members)
    return idx


def with_permuted_block(df: pd.DataFrame, cols: list[str], idx: np.ndarray) -> pd.DataFrame:
    out = df.copy()
    out[cols] = df[cols].to_numpy()[idx]
    return out


def permutation_p(observed: float, null: np.ndarray) -> float:
    null = np.asarray(null)
    return float((1 + np.sum(null >= observed)) / (1 + len(null)))


# ---------------------------------------------------------------- bootstrap
def cluster_bootstrap_delta(y, s_conf, s_brain, clusters, n_boot=2000, seed=BOOTSTRAP_SEED,
                            alpha=0.05) -> dict:
    """Percentile interval for AUC_brain - AUC_conf, resampling whole clusters (sites)."""
    y = np.asarray(y)
    clusters = np.asarray(clusters)
    labels = np.unique(clusters)
    members = {c: np.flatnonzero(clusters == c) for c in labels}
    rng = np.random.default_rng(seed)
    deltas = []
    for _ in range(n_boot):
        pick = rng.choice(labels, size=len(labels), replace=True)
        idx = np.concatenate([members[c] for c in pick])
        if len(np.unique(y[idx])) < 2:
            continue
        deltas.append(roc_auc_score(y[idx], s_brain[idx]) - roc_auc_score(y[idx], s_conf[idx]))
    deltas = np.array(deltas)
    lo, hi = np.quantile(deltas, [alpha / 2, 1 - alpha / 2])
    return {"lo": float(lo), "hi": float(hi), "n_valid": int(len(deltas)), "n_boot": int(n_boot)}


def cluster_bootstrap_delta_repeats(y, S_conf, S_brain, clusters, n_boot=2000, seed=BOOTSTRAP_SEED,
                                    alpha=0.05) -> dict:
    """Percentile interval for the *reported* statistic: the mean over repeats of
    per-repeat pooled ΔAUC. Each bootstrap draw resamples whole clusters once and
    applies the same draw to every repeat (corrects DEVIATIONS.md D1)."""
    y = np.asarray(y)
    S_conf, S_brain = np.atleast_2d(S_conf), np.atleast_2d(S_brain)
    clusters = np.asarray(clusters)
    labels = np.unique(clusters)
    members = {c: np.flatnonzero(clusters == c) for c in labels}
    rng = np.random.default_rng(seed)
    deltas = []
    for _ in range(n_boot):
        pick = rng.choice(labels, size=len(labels), replace=True)
        idx = np.concatenate([members[c] for c in pick])
        if len(np.unique(y[idx])) < 2:
            continue
        yi = y[idx]
        d = [roc_auc_score(yi, sb[idx]) - roc_auc_score(yi, sc[idx]) for sc, sb in zip(S_conf, S_brain)]
        deltas.append(float(np.mean(d)))
    deltas = np.array(deltas)
    lo, hi = np.quantile(deltas, [alpha / 2, 1 - alpha / 2])
    return {"lo": float(lo), "hi": float(hi), "n_valid": int(len(deltas)), "n_boot": int(n_boot)}


def rank_average(scores: np.ndarray) -> np.ndarray:
    """Average per-subject out-of-fold scores across repeats after rank-normalising
    each repeat (puts SVM decision values and probabilities on a common scale)."""
    from scipy.stats import rankdata
    scores = np.atleast_2d(scores)
    return np.mean([rankdata(s) / len(s) for s in scores], axis=0)
