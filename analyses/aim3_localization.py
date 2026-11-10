"""Aim 3: where does the confound-adjusted signal lie? (RESEARCH_PROPOSAL_ABIDE.md §4.6,
tag analysis-plan-v2). Primary model: C3 + brain block, L1 logistic, C = 0.1, unharmonized.

    .venv-win/Scripts/python.exe analyses/aim3_localization.py [--n-perm 1000]
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

os.environ["PYTHONWARNINGS"] = "ignore"
os.environ.setdefault("OMP_NUM_THREADS", "1")
warnings.filterwarnings("ignore")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from joblib import Parallel, delayed  # noqa: E402
from sklearn.model_selection import StratifiedShuffleSplit  # noqa: E402

import common as cm  # noqa: E402
from aim1_confound_attenuation import permutation_test  # noqa: E402
from evaluation import calibration, net_benefit, net_benefit_treat_all  # noqa: E402

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "aim3", "results")
STABILITY_SEED = 51130001
N_HALF = 100
STABLE_FREQ = 0.70
THRESHOLDS = np.round(np.arange(0.05, 0.951, 0.01), 2)


def delta_block(df, conf_cols, brain_cols, harmonize=False):
    y = df[cm.TARGET].to_numpy()
    sp = cm.kfold_splits(y)
    sc = cm.oof_scores(df, lambda: cm.make_pipeline(conf_cols, None), sp)
    sb = cm.oof_scores(df, lambda: cm.make_pipeline(conf_cols, brain_cols, harmonize=harmonize), sp)
    res = cm.DeltaResult(cm.pooled_auc(y, sc), cm.pooled_auc(y, sb))
    ci = cm.cluster_bootstrap_delta_repeats(y, sc, sb, df[cm.SITE].to_numpy())
    return res, sc, sb, {**res.summary(), "ci_lo": ci["lo"], "ci_hi": ci["hi"], "n": int(len(df)),
                         "n_asd": int(y.sum())}


def stability_selection(df, brain_cols):
    y = df[cm.TARGET].to_numpy()
    sss = StratifiedShuffleSplit(n_splits=N_HALF, train_size=0.5, random_state=STABILITY_SEED)
    coefs = []
    for tr, _ in sss.split(np.zeros(len(y)), y):
        m = cm.make_pipeline(cm.CONFOUND_SETS["C3"], brain_cols)
        m.fit(df.iloc[tr], y[tr])
        names = m.named_steps["pre"].get_feature_names_out()
        coef = pd.Series(m.named_steps["clf"].coef_.ravel(), index=names)
        coefs.append(coef.reindex([f"brain__{b}" for b in brain_cols]).fillna(0.0).to_numpy())
    C = np.vstack(coefs)
    sel = C != 0
    rows = []
    for j, f in enumerate(brain_cols):
        s = sel[:, j]
        n_sel = int(s.sum())
        pos = int((C[s, j] > 0).sum())
        agree = max(pos, n_sel - pos) / n_sel if n_sel else np.nan
        rows.append({"feature": f, "selection_freq": n_sel / N_HALF,
                     "sign": ("+" if pos >= n_sel - pos else "-") if n_sel else "",
                     "sign_agreement": agree,
                     "mean_coef_when_selected": float(C[s, j].mean()) if n_sel else 0.0,
                     "stable": bool(n_sel / N_HALF >= STABLE_FREQ and agree == 1.0)})
    return pd.DataFrame(rows)


def calibration_block(df, sc, sb):
    y = df[cm.TARGET].to_numpy()
    cal = {"C3": [], "C3_brain": []}
    nb = {"C3": [], "C3_brain": []}
    for r in range(sc.shape[0]):
        for name, s in (("C3", sc[r]), ("C3_brain", sb[r])):
            cal[name].append(calibration(y, s))
            nb[name].append(net_benefit(y, s, THRESHOLDS))
    cal_summary = {k: {m: float(np.mean([c[m] for c in v])) for m in v[0]} for k, v in cal.items()}
    curve = pd.DataFrame({"threshold": THRESHOLDS,
                          "nb_C3": np.mean(nb["C3"], axis=0),
                          "nb_C3_brain": np.mean(nb["C3_brain"], axis=0),
                          "nb_treat_all": net_benefit_treat_all(y, THRESHOLDS),
                          "nb_treat_none": 0.0})
    return cal_summary, curve


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n-perm", type=int, default=1000)
    args = ap.parse_args()
    t0 = time.time()
    os.makedirs(OUT, exist_ok=True)
    df = cm.load_data()
    g = cm.brain_groups()
    C3 = cm.CONFOUND_SETS["C3"]
    try:
        head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=cm.REPO_ROOT, text=True).strip()
    except Exception:
        head = None
    import sklearn
    results = {"meta": {"plan_tag": "analysis-plan-v2", "git_head_at_run": head,
                        "python": platform.python_version(), "scikit_learn": sklearn.__version__,
                        "dataset_sha256": cm.DATA_SHA256, "n_perm": args.n_perm,
                        "stability_seed": STABILITY_SEED, "n_half_samples": N_HALF,
                        "stable_freq": STABLE_FREQ}}

    # ---- 1. compartment models (+ within-site permutation of that compartment)
    comp_rows = []
    y = df[cm.TARGET].to_numpy()
    sp = cm.kfold_splits(y)
    for i, comp in enumerate(("thickness", "area", "subcortical")):
        res, sc, sb, row = delta_block(df, C3, g[comp])
        null = permutation_test(df, C3, g[comp], sp, res.auc_conf, df[cm.SITE].to_numpy(),
                                args.n_perm, cm.PERMUTATION_SEED + 10 + i)
        np.save(os.path.join(OUT, f"perm_null_{comp}.npy"), null)
        row.update({"compartment": comp, "n_features": len(g[comp]), "harmonized": False,
                    "p_within_site": cm.permutation_p(row["delta_mean"], null),
                    "null_mean": float(null.mean()), "null_q95": float(np.quantile(null, 0.95))})
        comp_rows.append(row)
        _, _, _, row_h = delta_block(df, C3, g[comp], harmonize=True)
        row_h.update({"compartment": comp, "n_features": len(g[comp]), "harmonized": True})
        comp_rows.append(row_h)
        print(f"compartment {comp}: dAUC={row['delta_mean']:.4f} p={row['p_within_site']:.4f} "
              f"({time.time()-t0:.0f}s)", flush=True)
    results["compartments"] = comp_rows

    # ---- 2. age strata (separate CV within each)
    age_rows = []
    for name, mask in (("under_18", df["AGE_AT_SCAN"] < 18.0), ("18_and_over", df["AGE_AT_SCAN"] >= 18.0)):
        sub = df.loc[mask.to_numpy()].reset_index(drop=True)
        for lvl in ("C0", "C3"):
            _, _, _, row = delta_block(sub, cm.CONFOUND_SETS[lvl], g["all"])
            row.update({"stratum": name, "level": lvl, "n_sites": int(sub[cm.SITE].nunique())})
            age_rows.append(row)
        print(f"age {name} done", flush=True)
    results["age_strata"] = age_rows

    # ---- 3. stability selection
    stab = stability_selection(df, g["all"])
    comp_of = {f: c for c in ("thickness", "area", "subcortical") for f in g[c]}
    stab.insert(1, "compartment", stab["feature"].map(comp_of))
    stab = stab.sort_values("selection_freq", ascending=False)
    stab.to_csv(os.path.join(OUT, "table_stability_selection.csv"), index=False)
    results["stability"] = {"n_stable": int(stab["stable"].sum()),
                            "stable_features": stab.loc[stab["stable"], ["feature", "compartment", "selection_freq",
                                                                         "sign"]].to_dict("records"),
                            "n_selected_ever": int((stab["selection_freq"] > 0).sum()),
                            "n_freq_ge_50pct": int((stab["selection_freq"] >= 0.5).sum())}
    print(f"stability: {results['stability']['n_stable']} stable features", flush=True)

    # ---- 4. calibration and decision curve (primary C3 vs C3 + brain)
    _, sc, sb, _ = delta_block(df, C3, g["all"])
    cal, curve = calibration_block(df, sc, sb)
    curve.to_csv(os.path.join(OUT, "table_decision_curve.csv"), index=False)
    key = curve[curve["threshold"].isin([0.3, 0.4, 0.5, 0.6, 0.7])]
    results["calibration"] = cal
    results["decision_curve_key_thresholds"] = key.round(5).to_dict("records")
    results["meta"]["runtime_s"] = round(time.time() - t0, 1)

    with open(os.path.join(OUT, "aim3_results.json"), "w") as f:
        json.dump(results, f, indent=2, default=float)
    pd.DataFrame(comp_rows).to_csv(os.path.join(OUT, "table_compartments.csv"), index=False)
    pd.DataFrame(age_rows).to_csv(os.path.join(OUT, "table_age_strata.csv"), index=False)
    files = sorted(f for f in os.listdir(OUT) if f != "OUTPUT_SHA256.txt")
    with open(os.path.join(OUT, "OUTPUT_SHA256.txt"), "w", newline="\n") as f:
        for fn in files:
            f.write(f"{cm.sha256_file(os.path.join(OUT, fn))}  {fn}\n")
    print(f"total {time.time()-t0:.0f}s")


if __name__ == "__main__":
    main()
