"""Corrected site-cluster bootstrap intervals for Aim 1 (DEVIATIONS.md, D1).

The original Aim 1 run built intervals from repeat-averaged scores, which
estimate a slightly larger, ensemble-like ΔAUC than the reported point estimate
(the mean of per-repeat pooled ΔAUC). This script recomputes the same
deterministic out-of-fold predictions and builds intervals for the reported
statistic itself. The original outputs in aim1/results/ are left unchanged.

    .venv-win/Scripts/python.exe analyses/aim1_intervals_corrected.py
"""

import os
import sys
import warnings

os.environ["PYTHONWARNINGS"] = "ignore"
warnings.filterwarnings("ignore")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import pandas as pd  # noqa: E402
from joblib import Parallel, delayed  # noqa: E402

import common as cm  # noqa: E402

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "aim1", "results")


def subsets(df):
    fd_cut = df["func_mean_fd"].quantile(0.9)
    return {
        "full_cohort": df[cm.TARGET].notna(),
        "S1_exclude_any_rater_fail": df["RATER_FAIL_COUNT"] == 0,
        "S2_exclude_majority_rater_fail": df["RATER_FAIL_COUNT"] < 2,
        "S3_exclude_top_motion_decile": ~(df["func_mean_fd"] > fd_cut),
        "S4_complete_case_FIQ": df["FIQ"].notna(),
        "S5_males_only": df["SEX"] == 1,
    }


def one(df, g, analysis, mask, family, level, tuned=False):
    sub = df.loc[mask.to_numpy()].reset_index(drop=True)
    y = sub[cm.TARGET].to_numpy()
    sp = cm.kfold_splits(y)
    cols = cm.CONFOUND_SETS[level]
    mk = cm.make_tuned_pipeline if tuned else cm.make_pipeline
    sc = cm.oof_scores(sub, lambda: mk(cols, None, family), sp)
    sb = cm.oof_scores(sub, lambda: mk(cols, g["all"], family), sp)
    res = cm.DeltaResult(cm.pooled_auc(y, sc), cm.pooled_auc(y, sb))
    ci = cm.cluster_bootstrap_delta_repeats(y, sc, sb, sub[cm.SITE].to_numpy())
    return {"analysis": analysis, "family": family, "level": level, "n": int(len(sub)),
            "delta_mean": res.summary()["delta_mean"], "ci_lo": ci["lo"], "ci_hi": ci["hi"],
            "boot_valid": ci["n_valid"]}


def main():
    df = cm.load_data()
    g = cm.brain_groups()
    full = subsets(df)["full_cohort"]
    jobs = [("hierarchy", full, fam, lvl, False) for fam in ("l1", "enet", "svm") for lvl in cm.CONFOUND_SETS]
    jobs += [(name, m, "l1", lvl, False) for name, m in subsets(df).items() if name != "full_cohort"
             for lvl in ("C0", "C3")]
    jobs += [("S6_nested_tuning", full, "l1", lvl, True) for lvl in ("C0", "C3")]
    rows = Parallel(n_jobs=-1)(delayed(one)(df, g, *j) for j in jobs)
    out = pd.DataFrame(rows)
    path = os.path.join(OUT, "table_intervals_corrected.csv")
    out.to_csv(path, index=False)
    print(out.round(4).to_string())


if __name__ == "__main__":
    main()
