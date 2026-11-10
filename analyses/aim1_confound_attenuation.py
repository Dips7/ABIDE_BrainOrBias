"""Aim 1: confound attenuation of the sMRI classification signal (pre-specified in
RESEARCH_PROPOSAL_ABIDE.md, Sections 4.1-4.5 and 4.7; tag analysis-plan-v2).

Outputs go to analyses/aim1/results/. Run from the repository root:

    .venv-win/Scripts/python.exe analyses/aim1_confound_attenuation.py [--n-perm 1000]
"""

from __future__ import annotations

import argparse
import json
import os
import platform
import subprocess
import sys
import time
import warnings

import numpy as np
import pandas as pd
from joblib import Parallel, delayed
from sklearn.metrics import roc_auc_score

warnings.filterwarnings("ignore")
os.environ["PYTHONWARNINGS"] = "ignore"  # inherited by joblib worker processes
os.environ.setdefault("OMP_NUM_THREADS", "1")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common as cm  # noqa: E402

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "aim1", "results")
PRIMARY = dict(family="l1", confounds="C3")
SESOI = 0.03  # pre-specified smallest effect size of interest (Section 4.7)


def delta_for(df, conf_cols, brain_cols, family, splits, tuned=False):
    y = df[cm.TARGET].to_numpy()
    if tuned:
        f_conf = lambda: cm.make_tuned_pipeline(conf_cols, None, family)  # noqa: E731
        f_brain = lambda: cm.make_tuned_pipeline(conf_cols, brain_cols, family)  # noqa: E731
    else:
        f_conf = lambda: cm.make_pipeline(conf_cols, None, family)  # noqa: E731
        f_brain = lambda: cm.make_pipeline(conf_cols, brain_cols, family)  # noqa: E731
    s_conf = cm.oof_scores(df, f_conf, splits)
    s_brain = cm.oof_scores(df, f_brain, splits)
    res = cm.DeltaResult(cm.pooled_auc(y, s_conf), cm.pooled_auc(y, s_brain))
    return res, s_conf, s_brain


def with_interval(df, res, s_conf, s_brain):
    y = df[cm.TARGET].to_numpy()
    out = res.summary()
    ci = cm.cluster_bootstrap_delta(y, cm.rank_average(s_conf), cm.rank_average(s_brain),
                                    df[cm.SITE].to_numpy())
    out.update({"delta_ci_lo": ci["lo"], "delta_ci_hi": ci["hi"], "boot_valid": ci["n_valid"],
                "n": int(len(df)), "n_asd": int(df[cm.TARGET].sum())})
    return out


def _one_perm(df, conf_cols, brain_cols, splits, auc_conf, perm_groups, seed_seq):
    rng = np.random.default_rng(seed_seq)
    idx = cm.permute_within(perm_groups, rng)
    dfp = cm.with_permuted_block(df, brain_cols, idx)
    y = df[cm.TARGET].to_numpy()
    s = cm.oof_scores(dfp, lambda: cm.make_pipeline(conf_cols, brain_cols, "l1"), splits)
    return float((cm.pooled_auc(y, s) - auc_conf).mean())


def permutation_test(df, conf_cols, brain_cols, splits, auc_conf, perm_groups, n_perm, seed):
    seqs = np.random.SeedSequence(seed).spawn(n_perm)
    null = Parallel(n_jobs=-1)(delayed(_one_perm)(df, conf_cols, brain_cols, splits, auc_conf,
                                                  perm_groups, s) for s in seqs)
    return np.array(null)


def git_head():
    try:
        return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=cm.REPO_ROOT, text=True).strip()
    except Exception:
        return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n-perm", type=int, default=1000)
    args = ap.parse_args()
    os.makedirs(OUT, exist_ok=True)
    t0 = time.time()

    df = cm.load_data()
    g = cm.brain_groups()
    y = df[cm.TARGET].to_numpy()
    splits = cm.kfold_splits(y)
    results = {"meta": {
        "plan_tag": "analysis-plan-v2", "git_head_at_run": git_head(),
        "python": platform.python_version(), "platform": platform.platform(),
        "dataset_sha256": cm.DATA_SHA256, "repeat_seeds": list(cm.REPEAT_SEEDS),
        "permutation_seed": cm.PERMUTATION_SEED, "bootstrap_seed": cm.BOOTSTRAP_SEED,
        "n_perm": args.n_perm, "sesoi": SESOI,
    }}
    import sklearn, scipy  # noqa: E401
    results["meta"]["versions"] = {"numpy": np.__version__, "pandas": pd.__version__,
                                   "scikit_learn": sklearn.__version__, "scipy": scipy.__version__}

    # ---- descriptive single-variable AUCs (no fitting; max(AUC, 1-AUC))
    single = {}
    for c in cm.COGNITION + cm.MOTION + cm.T1_QUALITY + cm.RATER_FLAG:
        m = df[c].notna().to_numpy()
        a = roc_auc_score(y[m], df.loc[m, c])
        single[c] = {"auc": float(max(a, 1 - a)), "direction": "higher_in_ASD" if a >= 0.5 else "lower_in_ASD",
                     "n": int(m.sum())}
    results["single_variable_auc"] = single
    print("single-variable AUCs done", flush=True)

    # ---- comparator hierarchy for each model family
    hierarchy = []
    oof_primary = {}
    for family in ("l1", "enet", "svm"):
        for k, cols in cm.CONFOUND_SETS.items():
            res, s_conf, s_brain = delta_for(df, cols, g["all"], family, splits)
            row = {"family": family, "level": k, **with_interval(df, res, s_conf, s_brain)}
            hierarchy.append(row)
            if family == "l1":
                oof_primary[k] = (s_conf, s_brain, res)
            print(f"hierarchy {family} {k}: dAUC={row['delta_mean']:.4f}", flush=True)
    results["hierarchy"] = hierarchy

    # attenuation profile (primary family)
    d = {k: float(oof_primary[k][2].delta.mean()) for k in cm.CONFOUND_SETS}
    results["attenuation_profile_l1"] = {
        **{f"delta_{k}": v for k, v in d.items()},
        **{f"pct_of_C0_remaining_{k}": (v / d["C0"] * 100 if d["C0"] else None) for k, v in d.items()},
    }

    # ---- H1: within-site permutation of the brain block (primary), plus stratified check
    s_conf3, _, res3 = oof_primary["C3"]
    auc_conf3 = res3.auc_conf
    observed = float(res3.delta.mean())
    perm = {}
    tert = pd.qcut(df["AGE_AT_SCAN"], 3, labels=False).astype(str)
    strata = {
        "within_site": df[cm.SITE].to_numpy(),
        "within_site_age_tertile_sex": (df[cm.SITE] + "|" + tert + "|" + df["SEX"].astype(str)).to_numpy(),
    }
    for i, (name, grp) in enumerate(strata.items()):
        null = permutation_test(df, cm.CONFOUND_SETS["C3"], g["all"], splits, auc_conf3, grp,
                                args.n_perm, cm.PERMUTATION_SEED + i)
        perm[name] = {"observed_delta": observed, "p_value": cm.permutation_p(observed, null),
                      "null_mean": float(null.mean()), "null_sd": float(null.std(ddof=1)),
                      "null_q95": float(np.quantile(null, 0.95)), "n_perm": int(len(null))}
        np.save(os.path.join(OUT, f"perm_null_{name}.npy"), null)
        print(f"permutation {name}: p={perm[name]['p_value']:.4f} ({time.time()-t0:.0f}s)", flush=True)
    results["h1_permutation"] = perm

    # ---- LOIO delta for the H1 rule (primary family, C3)
    loio = cm.loio_splits(df[cm.INSTITUTION].to_numpy())
    res_l, sc_l, sb_l = delta_for(df, cm.CONFOUND_SETS["C3"], g["all"], "l1", loio)
    results["loio_C3_l1"] = {"auc_conf": float(res_l.auc_conf[0]), "auc_brain": float(res_l.auc_brain[0]),
                             "delta": float(res_l.delta[0])}
    res_l0, _, _ = delta_for(df, cm.CONFOUND_SETS["C0"], g["all"], "l1", loio)
    results["loio_C0_l1"] = {"auc_conf": float(res_l0.auc_conf[0]), "auc_brain": float(res_l0.auc_brain[0]),
                             "delta": float(res_l0.delta[0])}
    print("LOIO done", flush=True)

    # ---- sensitivity analyses S1-S6 (primary family, C3; C0 shown for context)
    fd_cut = df["func_mean_fd"].quantile(0.9)
    subsets = {
        "S1_exclude_any_rater_fail": df["RATER_FAIL_COUNT"] == 0,
        "S2_exclude_majority_rater_fail": df["RATER_FAIL_COUNT"] < 2,
        "S3_exclude_top_motion_decile": ~(df["func_mean_fd"] > fd_cut),
        "S4_complete_case_FIQ": df["FIQ"].notna(),
        "S5_males_only": df["SEX"] == 1,
    }
    sens = []
    for name, mask in subsets.items():
        sub = df.loc[mask.to_numpy()].reset_index(drop=True)
        sp = cm.kfold_splits(sub[cm.TARGET].to_numpy())
        for k in ("C0", "C3"):
            res, sc, sb = delta_for(sub, cm.CONFOUND_SETS[k], g["all"], "l1", sp)
            sens.append({"analysis": name, "level": k, **with_interval(sub, res, sc, sb)})
        print(f"{name} done", flush=True)
    for k in ("C0", "C3"):
        res, sc, sb = delta_for(df, cm.CONFOUND_SETS[k], g["all"], "l1", splits, tuned=True)
        sens.append({"analysis": "S6_nested_tuning", "level": k, **with_interval(df, res, sc, sb)})
    print("S6 done", flush=True)
    results["sensitivity"] = sens
    results["meta"]["motion_decile_cutoff_mm"] = float(fd_cut)

    # ---- pre-specified H1 verdict (Section 4.7)
    p = perm["within_site"]["p_value"]
    loio_d = results["loio_C3_l1"]["delta"]
    if p >= 0.05:
        verdict = "EXPLAINED"
    elif observed >= SESOI and loio_d > 0:
        verdict = "ROBUST SIGNAL"
    else:
        verdict = "ATTENUATED SIGNAL"
    results["h1_verdict"] = {"verdict": verdict, "delta_full": observed, "p_within_site": p,
                             "loio_delta_full": loio_d, "sesoi": SESOI}
    results["meta"]["runtime_s"] = round(time.time() - t0, 1)

    # ---- write outputs
    with open(os.path.join(OUT, "aim1_results.json"), "w") as f:
        json.dump(results, f, indent=2)
    pd.DataFrame(hierarchy).to_csv(os.path.join(OUT, "table_hierarchy.csv"), index=False)
    pd.DataFrame(sens).to_csv(os.path.join(OUT, "table_sensitivity.csv"), index=False)
    oof = df[["SUB_ID", cm.SITE, cm.INSTITUTION, cm.TARGET]].copy()
    for k, (sc, sb, _) in oof_primary.items():
        oof[f"{k}_conf_mean_prob"] = sc.mean(axis=0)
        oof[f"{k}_brain_mean_prob"] = sb.mean(axis=0)
    oof.to_csv(os.path.join(OUT, "oof_l1_repeat_mean.csv"), index=False)

    files = sorted(f for f in os.listdir(OUT) if f != "OUTPUT_SHA256.txt")
    with open(os.path.join(OUT, "OUTPUT_SHA256.txt"), "w", newline="\n") as f:
        for fn in files:
            f.write(f"{cm.sha256_file(os.path.join(OUT, fn))}  {fn}\n")
    print(json.dumps(results["h1_verdict"], indent=2))
    print(f"total {time.time()-t0:.0f}s")


if __name__ == "__main__":
    main()
