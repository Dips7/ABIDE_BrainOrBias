"""Figures for the v2 manuscript, built only from saved result tables.

    .venv-win/Scripts/python.exe analyses/make_figures.py

Outputs: analyses/figures/*.png
"""

import os
import warnings

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

warnings.filterwarnings("ignore")
# ggseg 0.1 uses matplotlib.cm.get_cmap, which newer matplotlib versions removed.
if not hasattr(matplotlib.cm, "get_cmap"):
    matplotlib.cm.get_cmap = matplotlib.colormaps.get_cmap
import ggseg  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
FIG = os.path.join(HERE, "figures")
INK, MUTED, GRID = "#1f2328", "#59636e", "#d0d7de"
BLUE, ORANGE, GREY = "#2f6db5", "#c4612f", "#8c959f"

plt.rcParams.update({"font.size": 10, "axes.edgecolor": MUTED, "axes.labelcolor": INK,
                     "xtick.color": MUTED, "ytick.color": MUTED, "axes.spines.top": False,
                     "axes.spines.right": False, "figure.dpi": 150})


def _save(fig, name):
    fig.savefig(os.path.join(FIG, name), bbox_inches="tight", facecolor="white")
    plt.close(fig)


def atlas_maps(stab):
    """Signed selection frequency on Desikan-Killiany (thickness, area) and aseg."""
    signed = stab["selection_freq"] * np.where(stab["sign"] == "-", -1.0, 1.0)
    signed = pd.Series(signed.to_numpy(), index=stab["feature"])
    for comp, suffix in (("thickness", "_thickness"), ("area", "_area")):
        data = {}
        for f, v in signed.items():
            if f.endswith(suffix) and "Mean" not in f and "WhiteSurf" not in f:
                hemi = "left" if f.startswith("lh_") else "right"
                data[f"{f[3:-len(suffix)]}_{hemi}"] = float(v)
        ggseg.plot_dk(data, cmap="RdBu_r", vminmax=[-1, 1], background="white", edgecolor=INK,
                      bordercolor=GRID, figsize=(12, 6), fontsize=14,
                      ylabel="selection frequency (signed: + higher odds of ASD)",
                      # ggseg 0.1 layout: top row = right hemisphere, bottom row = left
                      title=f"Stability selection, cortical {comp} (C3 + brain, 100 half-samples)\n"
                            "top: right hemisphere · bottom: left hemisphere · lateral | medial")
        _save(plt.gcf(), f"fig_atlas_{comp}.png")
    data = {}
    for f, v in signed.items():
        key = f.replace("-Thalamus-Proper", "-Thalamus")
        data[key] = float(v)
    ggseg.plot_aseg(data, cmap="RdBu_r", vminmax=[-1, 1], background="white", edgecolor=INK,
                    bordercolor=GRID, figsize=(12, 6), fontsize=14,
                    ylabel="selection frequency (signed)",
                    title="Stability selection, subcortical volumes")
    fig = plt.gcf()
    fig.axes[0].text(0.0, -0.02, "Cerebellum and brainstem (black) are not rendered by ggseg 0.1; "
                     "see table_stability_selection.csv. Ventricles shown in coronal view.",
                     transform=fig.axes[0].transAxes, fontsize=9, color=MUTED, va="top")
    _save(fig, "fig_atlas_subcortical.png")


def attenuation(aim1):
    t = pd.read_csv(os.path.join(aim1, "table_intervals_corrected.csv"))
    t = t[(t["analysis"] == "hierarchy") & (t["family"] == "l1")].set_index("level").loc[["C0", "C1", "C2", "C3"]]
    labels = ["C0\nage, sex,\neTIV, site", "C1\n+ IQ", "C2\n+ motion,\nquality", "C3\nall"]
    fig, ax = plt.subplots(figsize=(6.2, 3.6))
    x = np.arange(4)
    ax.errorbar(x, t["delta_mean"], yerr=[t["delta_mean"] - t["ci_lo"], t["ci_hi"] - t["delta_mean"]],
                fmt="o", color=BLUE, ecolor=BLUE, capsize=4, ms=7, lw=1.5)
    ax.axhline(0.03, color=ORANGE, ls="--", lw=1)
    ax.text(-0.3, 0.031, "smallest effect of interest (0.03)", color=ORANGE, fontsize=8, va="bottom",
            ha="left")
    ax.axhline(0, color=GRID, lw=1)
    for xi, v in zip(x, t["delta_mean"]):
        ax.text(xi + 0.12, v, f"{v:.3f}", va="center", fontsize=8, color=INK)
    ax.set_xticks(x, labels)
    ax.set_ylabel("ΔAUC from adding 174 brain features")
    ax.set_title("Brain increment shrinks as confounds are added", loc="left", fontsize=11, color=INK)
    ax.grid(axis="y", color=GRID, lw=0.6)
    _save(fig, "fig_attenuation.png")


def forest(aim2):
    p = pd.read_csv(os.path.join(aim2, "table_per_institution.csv"))
    import json
    r = json.load(open(os.path.join(aim2, "aim2_results.json")))
    meta = {(x["level"], x["harmonized"]): x["meta"] for x in r["loio"]}
    fig, axes = plt.subplots(1, 2, figsize=(9, 5.6), sharey=True)
    for ax, (model, lvl, title) in zip(axes, (("C0_raw", "C0", "Unadjusted (C0)"),
                                              ("C3_raw", "C3", "Confound-adjusted (C3)"))):
        d = p[p["model"] == model].sort_values("institution", ascending=False).reset_index(drop=True)
        y = np.arange(len(d)) + 2
        ax.errorbar(d["delta"], y, xerr=1.96 * d["se_delong"], fmt="s", color=GREY, ecolor=GRID,
                    ms=4, capsize=0, lw=1.2)
        m = meta[(lvl, False)]
        ax.errorbar([m["mu"]], [0.5], xerr=[[m["mu"] - m["ci_lo"]], [m["ci_hi"] - m["mu"]]],
                    fmt="D", color=BLUE, ms=7, capsize=4, lw=1.6)
        ax.plot([m["pi_lo"], m["pi_hi"]], [0, 0], color=ORANGE, lw=3, solid_capstyle="butt")
        ax.axvline(0, color=INK, lw=0.8)
        ax.set_title(f"{title}\nmean {m['mu']:.3f}, I² {m['I2']*100:.0f}%", loc="left", fontsize=10, color=INK)
        ax.set_xlabel("ΔAUC at held-out institution")
        ax.grid(axis="x", color=GRID, lw=0.6)
        ax.set_yticks(list(y) + [0.5, 0], list(d["institution"]) + ["RE mean (HKSJ)", "95% PI"])
    _save(fig, "fig_forest_loio.png")


def decision_curve(aim3):
    c = pd.read_csv(os.path.join(aim3, "table_decision_curve.csv"))
    c = c[(c["threshold"] >= 0.2) & (c["threshold"] <= 0.8)]
    fig, ax = plt.subplots(figsize=(6.2, 3.8))
    ax.plot(c["threshold"], c["nb_C3_brain"], color=BLUE, lw=2, label="C3 + brain")
    ax.plot(c["threshold"], c["nb_C3"], color=ORANGE, lw=1.6, ls="--", label="C3 confounds only")
    ax.plot(c["threshold"], c["nb_treat_all"], color=GREY, lw=1.2, label="classify all as ASD")
    ax.axhline(0, color=INK, lw=0.8, label="classify none")
    ax.set_ylim(-0.1, max(0.5, c[["nb_C3_brain", "nb_C3"]].max().max() + 0.05))
    ax.set_xlabel("threshold probability")
    ax.set_ylabel("net benefit")
    ax.set_title("Decision curve (out-of-fold, mean of 10 repeats)", loc="left", fontsize=11, color=INK)
    ax.legend(frameon=False, fontsize=8)
    ax.grid(color=GRID, lw=0.6)
    _save(fig, "fig_decision_curve.png")


def main():
    os.makedirs(FIG, exist_ok=True)
    aim1 = os.path.join(HERE, "aim1", "results")
    aim2 = os.path.join(HERE, "aim2", "results")
    aim3 = os.path.join(HERE, "aim3", "results")
    attenuation(aim1)
    forest(aim2)
    if os.path.exists(os.path.join(aim3, "table_stability_selection.csv")):
        atlas_maps(pd.read_csv(os.path.join(aim3, "table_stability_selection.csv")))
        decision_curve(aim3)
    print(sorted(os.listdir(FIG)))


if __name__ == "__main__":
    main()
