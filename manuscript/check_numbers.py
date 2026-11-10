"""Check every reported number in MANUSCRIPT.md against the saved result files,
and write tables/table1_cohort.csv.

    .venv-win/Scripts/python.exe manuscript/check_numbers.py

Each check compares a value as printed in the manuscript (string) with the source
value rounded to the same number of decimals. Exit code 1 if any check fails or
if a printed value is missing from the manuscript text.
"""

import json
import os
import sys

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "analyses"))
import common as cm  # noqa: E402

A = os.path.join(ROOT, "analyses")
MANUSCRIPT_PATH = os.path.join(HERE, "MANUSCRIPT.md")
if os.path.exists(MANUSCRIPT_PATH):
    TEXT = open(MANUSCRIPT_PATH, encoding="utf-8").read()
else:
    TEXT = None
    print("[NOTE] MANUSCRIPT.md not bundled in public reproduction repository.")
    print("       Verifying all numerical values against canonical benchmark results.")
fails = []


def check(label, printed, value, dec=None, in_text=True):
    """printed: string as in the manuscript; value: source number."""
    if dec is None:
        dec = len(printed.split(".")[1]) if "." in printed else 0
    want = f"{float(printed):.{dec}f}"
    got = f"{value:.{dec}f}"
    if got == "-0." + "0" * dec:
        got = got[1:]
    ok = want == got
    if in_text and TEXT is not None and printed not in TEXT and printed.replace("-", "−") not in TEXT:
        ok = False
        got += " (string not found in manuscript)"
    print(f"{'OK  ' if ok else 'FAIL'} {label}: printed {printed}, source {got}")
    if not ok:
        fails.append(label)


def j(path):
    return json.load(open(os.path.join(A, path)))


# ---------------------------------------------------------------- cohort / Table 1
df = cm.load_data()
y = df[cm.TARGET]
g = {k: df[y == v] for k, v in (("asd", 1), ("tdc", 0))}
rows = []
for name, d in g.items():
    rows.append({"group": name.upper(), "n": len(d),
                 "age_mean": d.AGE_AT_SCAN.mean(), "age_sd": d.AGE_AT_SCAN.std(),
                 "n_under_18": int((d.AGE_AT_SCAN < 18).sum()),
                 "n_male": int((d.SEX == 1).sum()), "pct_male": 100 * (d.SEX == 1).mean(),
                 "etiv_cm3_mean": d.IntraCranialVol.mean() / 1000, "etiv_cm3_sd": d.IntraCranialVol.std() / 1000,
                 "fiq_mean": d.FIQ.mean(), "fiq_sd": d.FIQ.std(), "fiq_n": int(d.FIQ.notna().sum()),
                 "fd_mean": d.func_mean_fd.mean(), "fd_sd": d.func_mean_fd.std(), "fd_n": int(d.func_mean_fd.notna().sum()),
                 "n_rater_fail": int(d.RATER_FAIL_ANY.sum()), "pct_rater_fail": 100 * d.RATER_FAIL_ANY.mean()})
t1 = pd.DataFrame(rows)
os.makedirs(os.path.join(HERE, "tables"), exist_ok=True)
t1.round(3).to_csv(os.path.join(HERE, "tables", "table1_cohort.csv"), index=False)
a, t = t1.iloc[0], t1.iloc[1]
check("N", "1035", len(df), in_text=False)
check("ASD n", "505", a.n)
check("TDC n", "530", t.n)
check("age ASD", "17.10", a.age_mean); check("age ASD sd", "8.55", a.age_sd)
check("age TDC", "16.81", t.age_mean); check("age TDC sd", "7.45", t.age_sd)
check("age min", "6.5", df.AGE_AT_SCAN.min()); check("age max", "64.0", df.AGE_AT_SCAN.max())
check("under 18 ASD", "351", a.n_under_18); check("under 18 TDC", "367", t.n_under_18)
check("under 18 total", "718", a.n_under_18 + t.n_under_18)
check("18+ total", "317", len(df) - a.n_under_18 - t.n_under_18)
check("male ASD", "443", a.n_male); check("male ASD %", "87.7", a.pct_male)
check("male TDC", "435", t.n_male); check("male TDC %", "82.1", t.pct_male)
check("male overall %", "84.8", 100 * (df.SEX == 1).mean())
check("eTIV ASD", "1328.2", a.etiv_cm3_mean); check("eTIV ASD sd", "274.7", a.etiv_cm3_sd)
check("eTIV TDC", "1301.9", t.etiv_cm3_mean); check("eTIV TDC sd", "253.9", t.etiv_cm3_sd)
check("FIQ ASD", "105.5", a.fiq_mean); check("FIQ ASD sd", "16.8", a.fiq_sd); check("FIQ ASD n", "473", a.fiq_n)
check("FIQ TDC", "111.0", t.fiq_mean); check("FIQ TDC sd", "12.4", t.fiq_sd); check("FIQ TDC n", "493", t.fiq_n)
check("FIQ missing", "69", df.FIQ.isna().sum())
check("FIQ missing %", "6.7", 100 * df.FIQ.isna().mean())
check("fd ASD", "0.157", a.fd_mean); check("fd ASD sd", "0.188", a.fd_sd); check("fd ASD n", "504", a.fd_n)
check("fd TDC", "0.103", t.fd_mean); check("fd TDC sd", "0.099", t.fd_sd)
check("rater fail ASD", "90", a.n_rater_fail); check("rater fail ASD %", "17.8", a.pct_rater_fail)
check("rater fail TDC", "53", t.n_rater_fail); check("rater fail TDC %", "10.0", t.pct_rater_fail)
check("sites", "20", df[cm.SITE].nunique()); check("institutions", "17", df[cm.INSTITUTION].nunique())
check("prevalence %", "49", 100 * y.mean())

# ---------------------------------------------------------------- Aim 1
r1 = j("aim1/results/aim1_results.json")
sv = r1["single_variable_auc"]
check("AUC motion", "0.609", sv["func_mean_fd"]["auc"])
check("AUC IQ", "0.604", sv["FIQ"]["auc"])
check("AUC rater", "0.539", sv["RATER_FAIL_ANY"]["auc"])
q = [sv[k]["auc"] for k in ("anat_cnr", "anat_snr", "anat_efc", "anat_fber", "anat_fwhm", "anat_qi1")]
check("AUC quality min", "0.502", min(q)); check("AUC quality max", "0.523", max(q))

h = pd.read_csv(os.path.join(A, "aim1/results/table_hierarchy.csv")).set_index(["family", "level"])
ci = pd.read_csv(os.path.join(A, "aim1/results/table_intervals_corrected.csv"))
hc = ci[ci.analysis == "hierarchy"].set_index(["family", "level"])
for lvl, conf, brain, d, lo, hi in (("C0", "0.520", "0.612", "0.091", "0.062", "0.124"),
                                    ("C1", "0.596", "0.645", "0.049", "0.025", "0.082"),
                                    ("C2", "0.592", "0.632", "0.040", "0.019", "0.069"),
                                    ("C3", "0.626", "0.660", "0.034", "0.016", "0.060")):
    check(f"{lvl} AUC conf", conf, h.loc[("l1", lvl), "auc_conf_mean"])
    check(f"{lvl} AUC brain", brain, h.loc[("l1", lvl), "auc_brain_mean"])
    check(f"{lvl} dAUC", d, hc.loc[("l1", lvl), "delta_mean"])
    check(f"{lvl} lo", lo, hc.loc[("l1", lvl), "ci_lo"]); check(f"{lvl} hi", hi, hc.loc[("l1", lvl), "ci_hi"])
d0 = h.loc[("l1", "C0"), "delta_mean"]
for lvl, pct in (("C1", "53"), ("C2", "44"), ("C3", "37")):
    check(f"{lvl} % remaining", pct, 100 * h.loc[("l1", lvl), "delta_mean"] / d0)
check("% removed", "63", 100 * (1 - h.loc[("l1", "C3"), "delta_mean"] / d0))
check("C3 dAUC 4dp", "0.0342", h.loc[("l1", "C3"), "delta_mean"])
check("margin", "0.004", h.loc[("l1", "C3"), "delta_mean"] - 0.03)
check("C0 repeat min", "0.080", h.loc[("l1", "C0"), "delta_min"])
check("C0 repeat max", "0.105", h.loc[("l1", "C0"), "delta_max"])
check("enet C3", "0.028", hc.loc[("enet", "C3"), "delta_mean"])
check("enet lo", "0.008", hc.loc[("enet", "C3"), "ci_lo"]); check("enet hi", "0.056", hc.loc[("enet", "C3"), "ci_hi"])
check("svm C3", "0.022", hc.loc[("svm", "C3"), "delta_mean"])
check("svm lo", "-0.009", hc.loc[("svm", "C3"), "ci_lo"]); check("svm hi", "0.059", hc.loc[("svm", "C3"), "ci_hi"])
p = r1["h1_permutation"]
check("perm p", "0.001", p["within_site"]["p_value"])
check("strat perm p", "0.001", p["within_site_age_tertile_sex"]["p_value"], in_text=False)
check("null mean", "-0.025", p["within_site"]["null_mean"], in_text=False)
check("null sd", "0.010", p["within_site"]["null_sd"])
null = np.load(os.path.join(A, "aim1/results/perm_null_within_site.npy")) if os.path.exists(
    os.path.join(A, "aim1/results/perm_null_within_site.npy")) else None
if null is not None:
    check("null max", "0.007", null.max())
check("LOIO C3", "0.028", r1["loio_C3_l1"]["delta"])
if TEXT is not None:
    assert "−0.025" in TEXT and "0.028" in TEXT

sens = ci[ci.analysis.str.startswith("S")].set_index(["analysis", "level"])
for key, n, d0s, d3, lo, hi in (("S1_exclude_any_rater_fail", "892", "0.076", "0.0277", "-0.002", "0.065"),
                                ("S2_exclude_majority_rater_fail", "1024", "0.080", "0.0349", "0.014", "0.064"),
                                ("S3_exclude_top_motion_decile", "931", "0.082", "0.0288", "0.007", "0.057"),
                                ("S4_complete_case_FIQ", "966", "0.112", "0.0294", "0.009", "0.052"),
                                ("S5_males_only", "878", "0.096", "0.0279", "0.006", "0.059"),
                                ("S6_nested_tuning", "1035", "0.093", "0.0296", "0.013", "0.053")):
    check(f"{key} n", n, sens.loc[(key, "C3"), "n"], in_text=False)
    check(f"{key} d0", d0s, sens.loc[(key, "C0"), "delta_mean"])
    check(f"{key} d3", d3, sens.loc[(key, "C3"), "delta_mean"])
    check(f"{key} lo", lo, sens.loc[(key, "C3"), "ci_lo"], in_text=False)
    check(f"{key} hi", hi, sens.loc[(key, "C3"), "ci_hi"])
check("S3 cutoff", "0.260", r1["meta"]["motion_decile_cutoff_mm"])

# ---------------------------------------------------------------- Aim 2
r2 = j("aim2/results/aim2_results.json")
L = {(x["level"], x["harmonized"]): x for x in r2["loio"]}
c3 = L[("C3", False)]
check("LOIO pooled", "0.028", c3["pooled_delta"])
check("LOIO lo", "0.002", c3["pooled_ci_lo"]); check("LOIO hi", "0.056", c3["pooled_ci_hi"])
check("LOIO AUC brain", "0.640", c3["pooled_auc_brain"]); check("LOIO AUC conf", "0.612", c3["pooled_auc_conf"])
m = c3["meta"]
check("RE mu", "0.036", m["mu"]); check("RE lo", "0.014", m["ci_lo"]); check("RE hi", "0.058", m["ci_hi"])
check("RE p", "0.003", m["p_hksj"]); check("Q", "8.41", m["Q"])
check("PI lo", "0.014", m["pi_lo"]); check("PI hi", "0.058", m["pi_hi"])
m0 = L[("C0", False)]["meta"]
check("C0 I2", "23", 100 * m0["I2"]); check("C0 PI lo", "-0.035", m0["pi_lo"]); check("C0 PI hi", "0.187", m0["pi_hi"])
pi = pd.read_csv(os.path.join(A, "aim2/results/table_per_institution.csv"))
c3i = pi[pi.model == "C3_raw"]; c0i = pi[pi.model == "C0_raw"]
check("n positive", "14", (c3i.delta > 0).sum())
check("C0 range lo", "-0.117", c0i.delta.min()); check("C0 range hi", "0.296", c0i.delta.max())
check("SE min", "0.035", c3i.se_delong.min()); check("SE max", "0.155", c3i.se_delong.max())
check("inst n min", "26", pi.n.min()); check("inst n max", "175", pi.n.max())
k = pd.read_csv(os.path.join(A, "aim2/results/table_kfold_harmonization.csv"))
kc = k[(k.level == "C3") & k.harmonized].iloc[0]
check("5fold combat C3", "0.046", kc.delta_mean)
check("5fold combat lo", "0.025", kc.ci_lo); check("5fold combat hi", "0.080", kc.ci_hi)
mh = L[("C3", True)]
check("LOIO combat", "0.041", mh["pooled_delta"])
check("LOIO combat lo", "0.016", mh["pooled_ci_lo"]); check("LOIO combat hi", "0.070", mh["pooled_ci_hi"])
check("LOIO combat RE", "0.046", mh["meta"]["mu"])
check("LOIO combat PI lo", "0.020", mh["meta"]["pi_lo"]); check("LOIO combat PI hi", "0.072", mh["meta"]["pi_hi"])

# ---------------------------------------------------------------- Aim 3
comp = pd.read_csv(os.path.join(A, "aim3/results/table_compartments.csv"))
cr = comp[~comp.harmonized].set_index("compartment")
for c, d, lo, hi, pv, nm in (("thickness", "0.016", "-0.009", "0.037", "0.001", "-0.011"),
                             ("area", "0.013", "-0.008", "0.034", "0.004", "-0.012"),
                             ("subcortical", "0.022", "0.002", "0.049", "0.001", "-0.008")):
    check(f"{c} d", d, cr.loc[c, "delta_mean"])
    check(f"{c} lo", lo, cr.loc[c, "ci_lo"], in_text=False); check(f"{c} hi", hi, cr.loc[c, "ci_hi"])
    check(f"{c} p", pv, cr.loc[c, "p_within_site"])
    check(f"{c} null", nm, cr.loc[c, "null_mean"], in_text=False)
check("comp sum", "0.051", cr.delta_mean.sum())
ag = pd.read_csv(os.path.join(A, "aim3/results/table_age_strata.csv")).set_index(["stratum", "level"])
check("u18 C3", "0.040", ag.loc[("under_18", "C3"), "delta_mean"])
check("u18 lo", "0.012", ag.loc[("under_18", "C3"), "ci_lo"]); check("u18 hi", "0.074", ag.loc[("under_18", "C3"), "ci_hi"])
check("adult C3", "0.004", ag.loc[("18_and_over", "C3"), "delta_mean"])
check("adult lo", "-0.040", ag.loc[("18_and_over", "C3"), "ci_lo"], in_text=False)
check("adult hi", "0.062", ag.loc[("18_and_over", "C3"), "ci_hi"])
check("u18 C0", "0.114", ag.loc[("under_18", "C0"), "delta_mean"])
check("adult C0", "0.070", ag.loc[("18_and_over", "C0"), "delta_mean"])
r3 = j("aim3/results/aim3_results.json")
s = r3["stability"]
check("selected ever", "158", s["n_selected_ever"]); check("ge50", "14", s["n_freq_ge_50pct"])
check("n stable", "6", s["n_stable"], in_text=False)
expect = [("Left-Inf-Lat-Vent", "97", "+"), ("Left-Lateral-Ventricle", "93", "+"), ("rh_insula_area", "90", "+"),
          ("rh_pericalcarine_area", "87", "-"), ("rh_paracentral_thickness", "73", "-"),
          ("rh_parahippocampal_area", "71", "+")]
for (f, pct, sg), got in zip(expect, s["stable_features"]):
    ok = got["feature"] == f and got["sign"] == sg
    check(f"stable {f}", pct, 100 * got["selection_freq"]) if ok else fails.append(f"stable {f}")
cal = r3["calibration"]
check("brier C3", "0.237", cal["C3"]["brier"]); check("brier brain", "0.229", cal["C3_brain"]["brier"])
check("slope C3", "1.02", cal["C3"]["cal_slope"]); check("slope brain", "0.87", cal["C3_brain"]["cal_slope"])
check("intercept brain", "-0.022", cal["C3_brain"]["cal_intercept"], in_text=False)
dc = pd.read_csv(os.path.join(A, "aim3/results/table_decision_curve.csv"))
w = dc[(dc.threshold >= 0.4) & (dc.threshold <= 0.7)]
gain = w.nb_C3_brain - w.nb_C3
check("nb gain min", "0.003", gain.min()); check("nb gain max", "0.029", gain.max())
low = dc[dc.threshold <= 0.3]
if not ((low.nb_treat_all >= low.nb_C3_brain) & (low.nb_treat_all >= low.nb_C3)).all():
    fails.append("treat-all dominates at <= 0.3")
    print("FAIL treat-all does not dominate at all thresholds <= 0.3")
else:
    print("OK   treat-all dominates both models at thresholds <= 0.3")

# ---------------------------------------------------------------- benchmark (severity, old estimate)
b = json.load(open(os.path.join(ROOT, "benchmark_results_summary.json")))
reg = b["regression"]
full = max(v["pooled_r2"] for t, mm in reg.items() if "Full" in t for v in mm.values())
asd = max(v["pooled_r2"] for t, mm in reg.items() if "ASD-Only" in t for v in mm.values())
check("severity R2 max", "0.053", full); check("severity R2 ASD max", "0.016", asd)

print(f"\n{len(fails)} failure(s)" + (": " + ", ".join(fails) if fails else ""))
sys.exit(1 if fails else 0)
