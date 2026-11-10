"""Aim 2: generalization to unseen institutions and in-fold ComBat harmonization
(RESEARCH_PROPOSAL_ABIDE.md §2 H2, §4.3 items 2-3, §4.4 heterogeneity; tag
analysis-plan-v2). Primary family: L1 logistic, C = 0.1.

    .venv-win/Scripts/python.exe analyses/aim2_site_generalization.py
"""

from __future__ import annotations

import json
import os
import platform
import subprocess
import sys
import time
import warnings

os.environ["PYTHONWARNINGS"] = "ignore"
warnings.filterwarnings("ignore")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from joblib import Parallel, delayed  # noqa: E402

import common as cm  # noqa: E402
from meta import delong_paired_delta, random_effects_hksj  # noqa: E402

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "aim2", "results")


def fit_pair(df, level, brain, splits, harmonize):
    cols = cm.CONFOUND_SETS[level]
    sc = cm.oof_scores(df, lambda: cm.make_pipeline(cols, None), splits)
    sb = cm.oof_scores(df, lambda: cm.make_pipeline(cols, brain, harmonize=harmonize), splits)
    return sc, sb


def loio_block(df, level, brain, harmonize):
    y = df[cm.TARGET].to_numpy()
    inst = df[cm.INSTITUTION].to_numpy()
    sc, sb = fit_pair(df, level, brain, cm.loio_splits(inst), harmonize)
    sc, sb = sc[0], sb[0]
    pooled = cm.DeltaResult(cm.pooled_auc(y, sc), cm.pooled_auc(y, sb))
    ci = cm.cluster_bootstrap_delta_repeats(y, sc, sb, inst)
    per = []
    for i in np.unique(inst):
        m = inst == i
        r = delong_paired_delta(y[m], sc[m], sb[m])
        per.append({"institution": i, "n": int(m.sum()), "n_asd": int(y[m].sum()),
                    "auc_conf": r["auc_a"], "auc_brain": r["auc_b"], "delta": r["delta"],
                    "se_delong": r["se"]})
    per = pd.DataFrame(per)
    ma = random_effects_hksj(per["delta"], per["se_delong"] ** 2)
    return {"level": level, "harmonized": harmonize,
            "pooled_auc_conf": float(pooled.auc_conf[0]), "pooled_auc_brain": float(pooled.auc_brain[0]),
            "pooled_delta": float(pooled.delta[0]), "pooled_ci_lo": ci["lo"], "pooled_ci_hi": ci["hi"],
            "meta": ma}, per, (sc, sb)


def kfold_block(df, level, brain, harmonize):
    y = df[cm.TARGET].to_numpy()
    sc, sb = fit_pair(df, level, brain, cm.kfold_splits(y), harmonize)
    res = cm.DeltaResult(cm.pooled_auc(y, sc), cm.pooled_auc(y, sb))
    ci = cm.cluster_bootstrap_delta_repeats(y, sc, sb, df[cm.SITE].to_numpy())
    return {"design": "5fold_x10", "level": level, "harmonized": harmonize, **res.summary(),
            "ci_lo": ci["lo"], "ci_hi": ci["hi"]}


def main():
    t0 = time.time()
    os.makedirs(OUT, exist_ok=True)
    df = cm.load_data()
    brain = cm.brain_groups()["all"]
    try:
        head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=cm.REPO_ROOT, text=True).strip()
    except Exception:
        head = None
    import sklearn
    meta = {"plan_tag": "analysis-plan-v2", "git_head_at_run": head, "python": platform.python_version(),
            "scikit_learn": sklearn.__version__, "dataset_sha256": cm.DATA_SHA256,
            "repeat_seeds": list(cm.REPEAT_SEEDS), "bootstrap_seed": cm.BOOTSTRAP_SEED}

    jobs = [("loio", lvl, h) for lvl in ("C0", "C3") for h in (False, True)]
    jobs += [("kfold", lvl, h) for lvl in ("C0", "C3") for h in (False, True)]

    def run(kind, lvl, h):
        if kind == "loio":
            return kind, lvl, h, loio_block(df, lvl, brain, h)
        return kind, lvl, h, kfold_block(df, lvl, brain, h)

    out = Parallel(n_jobs=len(jobs))(delayed(run)(*j) for j in jobs)
    loio_rows, per_tables, kfold_rows = [], [], []
    for kind, lvl, h, res in out:
        tag = f"{lvl}_{'combat' if h else 'raw'}"
        if kind == "loio":
            summary, per, _ = res
            loio_rows.append(summary)
            per.insert(0, "model", tag)
            per_tables.append(per)
        else:
            kfold_rows.append(res)
        print(f"{kind} {tag} done ({time.time()-t0:.0f}s)", flush=True)

    loio_rows.sort(key=lambda r: (r["level"], r["harmonized"]))
    kfold_rows.sort(key=lambda r: (r["level"], r["harmonized"]))
    primary = next(r for r in loio_rows if r["level"] == "C3" and not r["harmonized"])
    h2 = {
        "criterion_loio_delta_full_gt_0": primary["pooled_delta"] > 0,
        "loio_delta_full": primary["pooled_delta"],
        "heterogeneity_reported_descriptively": {k: primary["meta"][k] for k in
                                                 ("tau2", "I2", "Q", "pi_lo", "pi_hi", "mu", "ci_lo", "ci_hi")},
        "note": "The plan gave no numeric threshold for 'limited heterogeneity'; reported "
                "descriptively (DEVIATIONS.md clarification 14).",
    }
    results = {"meta": meta, "loio": loio_rows, "kfold": kfold_rows, "h2": h2,
               "runtime_s": round(time.time() - t0, 1)}
    with open(os.path.join(OUT, "aim2_results.json"), "w") as f:
        json.dump(results, f, indent=2)
    pd.concat(per_tables).to_csv(os.path.join(OUT, "table_per_institution.csv"), index=False)
    flat = [{k: v for k, v in r.items() if k != "meta"} | {f"meta_{k}": v for k, v in r["meta"].items()}
            for r in loio_rows]
    pd.DataFrame(flat).to_csv(os.path.join(OUT, "table_loio.csv"), index=False)
    pd.DataFrame(kfold_rows).to_csv(os.path.join(OUT, "table_kfold_harmonization.csv"), index=False)
    files = sorted(f for f in os.listdir(OUT) if f != "OUTPUT_SHA256.txt")
    with open(os.path.join(OUT, "OUTPUT_SHA256.txt"), "w", newline="\n") as f:
        for fn in files:
            f.write(f"{cm.sha256_file(os.path.join(OUT, fn))}  {fn}\n")
    print(json.dumps(h2, indent=2))
    print(f"total {time.time()-t0:.0f}s")


if __name__ == "__main__":
    main()
