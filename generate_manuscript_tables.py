#!/usr/bin/env python3
"""Reproducible Manuscript Table Generation Script.

Extracts canonical demographics and benchmark metrics directly from:
- abide_freesurfer_tabular_dataset.csv (SHA-256: 9c84f601...)
- benchmark_results_summary.json (SHA-256: c27bc429...)
- vv_audit/obuchowski_validation/summary.json & gate_decisions.json

Outputs machine-readable CSV and JSON tables to `manuscript_tables/`.
"""
import json
from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path(__file__).parent
TABLES_DIR = ROOT / "manuscript_tables"
TABLES_DIR.mkdir(parents=True, exist_ok=True)


def generate_table1_demographics():
    df = pd.read_csv(ROOT / "abide_freesurfer_tabular_dataset.csv")
    
    total_n = len(df)
    asd_mask = (df["DX_GROUP"] == 1)
    tdc_mask = (df["DX_GROUP"] == 2)
    
    t1_data = []
    
    # Sample Size
    t1_data.append({
        "Metric": "Sample Size (N)",
        "Overall": str(total_n),
        "ASD": str(asd_mask.sum()),
        "TDC": str(tdc_mask.sum())
    })
    
    # Age at Scan
    t1_data.append({
        "Metric": "Age at Scan (years, Mean ± SD)",
        "Overall": f"{df['AGE_AT_SCAN'].mean():.2f} ± {df['AGE_AT_SCAN'].std():.2f}",
        "ASD": f"{df.loc[asd_mask, 'AGE_AT_SCAN'].mean():.2f} ± {df.loc[asd_mask, 'AGE_AT_SCAN'].std():.2f}",
        "TDC": f"{df.loc[tdc_mask, 'AGE_AT_SCAN'].mean():.2f} ± {df.loc[tdc_mask, 'AGE_AT_SCAN'].std():.2f}"
    })
    t1_data.append({
        "Metric": "Age Range (min - max)",
        "Overall": f"{df['AGE_AT_SCAN'].min():.1f} - {df['AGE_AT_SCAN'].max():.1f}",
        "ASD": f"{df.loc[asd_mask, 'AGE_AT_SCAN'].min():.1f} - {df.loc[asd_mask, 'AGE_AT_SCAN'].max():.1f}",
        "TDC": f"{df.loc[tdc_mask, 'AGE_AT_SCAN'].min():.1f} - {df.loc[tdc_mask, 'AGE_AT_SCAN'].max():.1f}"
    })
    
    # Sex
    n_male_asd = (df.loc[asd_mask, "SEX"] == 1).sum()
    n_fem_asd = (df.loc[asd_mask, "SEX"] == 2).sum()
    n_male_tdc = (df.loc[tdc_mask, "SEX"] == 1).sum()
    n_fem_tdc = (df.loc[tdc_mask, "SEX"] == 2).sum()
    t1_data.append({
        "Metric": "Sex (Male / Female)",
        "Overall": f"{(df['SEX'] == 1).sum()} / {(df['SEX'] == 2).sum()}",
        "ASD": f"{n_male_asd} / {n_fem_asd}",
        "TDC": f"{n_male_tdc} / {n_fem_tdc}"
    })
    t1_data.append({
        "Metric": "Male Proportion (%)",
        "Overall": f"{(df['SEX'] == 1).mean() * 100:.1f}%",
        "ASD": f"{n_male_asd / asd_mask.sum() * 100:.1f}%",
        "TDC": f"{n_male_tdc / tdc_mask.sum() * 100:.1f}%"
    })
    
    # Full-Scale IQ (filtering -9999 missing sentinel values)
    fiq_valid = df.loc[df["FIQ"] > 0, "FIQ"]
    fiq_asd = df.loc[asd_mask & (df["FIQ"] > 0), "FIQ"]
    fiq_tdc = df.loc[tdc_mask & (df["FIQ"] > 0), "FIQ"]
    t1_data.append({
        "Metric": "Full-Scale IQ (Mean ± SD)",
        "Overall": f"{fiq_valid.mean():.1f} ± {fiq_valid.std():.1f} (n={len(fiq_valid)})",
        "ASD": f"{fiq_asd.mean():.1f} ± {fiq_asd.std():.1f} (n={len(fiq_asd)})",
        "TDC": f"{fiq_tdc.mean():.1f} ± {fiq_tdc.std():.1f} (n={len(fiq_tdc)})"
    })
    
    # Estimated Total Intracranial Volume (eTIV / cm3)
    t1_data.append({
        "Metric": "Estimated Total Intracranial Volume (cm3, Mean ± SD)",
        "Overall": f"{df['IntraCranialVol'].mean() / 1000.0:.1f} ± {df['IntraCranialVol'].std() / 1000.0:.1f}",
        "ASD": f"{df.loc[asd_mask, 'IntraCranialVol'].mean() / 1000.0:.1f} ± {df.loc[asd_mask, 'IntraCranialVol'].std() / 1000.0:.1f}",
        "TDC": f"{df.loc[tdc_mask, 'IntraCranialVol'].mean() / 1000.0:.1f} ± {df.loc[tdc_mask, 'IntraCranialVol'].std() / 1000.0:.1f}"
    })
    
    # Acquisition Sites vs Institutions
    n_acq_sites = df["SITE_ID"].nunique()
    # Institutional groupings map LEUVEN_1/2 -> LEUVEN, UCLA_1/2 -> UCLA, UM_1/2 -> UM
    inst_series = df["SITE_ID"].apply(lambda s: s.rsplit("_", 1)[0] if s.endswith(("_1", "_2")) else s)
    n_institutions = inst_series.nunique()
    t1_data.append({
        "Metric": "Acquisition Protocol Labels (Count)",
        "Overall": str(n_acq_sites),
        "ASD": str(df.loc[asd_mask, "SITE_ID"].nunique()),
        "TDC": str(df.loc[tdc_mask, "SITE_ID"].nunique())
    })
    t1_data.append({
        "Metric": "Institutional Centers (Count)",
        "Overall": str(n_institutions),
        "ASD": str(inst_series[asd_mask].nunique()),
        "TDC": str(inst_series[tdc_mask].nunique())
    })

    df_t1 = pd.DataFrame(t1_data)
    df_t1.to_csv(TABLES_DIR / "table1_cohort_demographics.csv", index=False)
    with open(TABLES_DIR / "table1_cohort_demographics.json", "w") as f:
        json.dump(t1_data, f, indent=2)
    print("Generated Table 1: Demographics")
    return df_t1


def generate_table2_benchmark_5fold():
    with open(ROOT / "benchmark_results_summary.json") as f:
        bench = json.load(f)
    
    models = bench["classification_5fold"]
    t2_data = []
    
    key_models = [
        ("Baseline_Demo (Age+Sex)", "Demographic Baseline (Age+Sex, L2 C=1.0)"),
        ("Baseline_Matched_L1_Logistic (Nuisance)", "Matched Nuisance Baseline (Age+Sex+eTIV+Site, L1 C=0.1)"),
        ("Brain_L1_Logistic (Age+Sex+Brain)", "Primary Brain L1 Logistic (Age+Sex+Brain, Fixed L1 C=0.1)"),
        ("Brain_Matched_L1_Logistic (Nuisance+Brain)", "Brain Matched L1 Logistic (Age+Sex+eTIV+Site+Brain, Fixed L1 C=0.1)"),
        ("Brain_ElasticNet (Age+Sex+Brain)", "Brain ElasticNet (Age+Sex+Brain, C=0.1, l1=0.5)"),
        ("Brain_Random_Forest (Age+Sex+Brain)", "Brain Random Forest (Age+Sex+Brain, 150 trees, depth 6)"),
        ("Brain_Gradient_Boosting (Age+Sex+Brain)", "Brain Gradient Boosting (Age+Sex+Brain, 100 trees, lr 0.05)")
    ]
    
    for mkey, display_name in key_models:
        if mkey in models:
            m = models[mkey]
            t2_data.append({
                "Model Architecture": display_name,
                "Mean Fold AUC ± SD": f"{m['mean_fold_auc']:.4f} ± {m['sd_fold_auc']:.4f}",
                "Pooled OOF AUC": f"{m['pooled_oof_auc']:.4f}",
                "Pooled OOF AUC 95% CI": f"[{m['oof_auc_95ci'][0]:.4f}, {m['oof_auc_95ci'][1]:.4f}]",
                "Pooled Delta AUC": f"{m['pooled_delta_auc']:+.4f}" if m['pooled_delta_auc'] != 0.0 else "Reference",
                "Delta AUC 95% CI": f"[{m['delta_auc_95ci'][0]:.4f}, {m['delta_auc_95ci'][1]:.4f}]" if m['pooled_delta_auc'] != 0.0 else "N/A"
            })
            
    df_t2 = pd.DataFrame(t2_data)
    df_t2.to_csv(TABLES_DIR / "table2_benchmark_5fold_cv.csv", index=False)
    with open(TABLES_DIR / "table2_benchmark_5fold_cv.json", "w") as f:
        json.dump(t2_data, f, indent=2)
    print("Generated Table 2: 5-Fold Stratified CV Benchmark")
    return df_t2


def generate_table3_loio():
    with open(ROOT / "benchmark_results_summary.json") as f:
        bench = json.load(f)
        
    loio = bench["classification_loio"]
    t3_data = [
        {
            "Model Architecture": "Demographic Baseline (Age+Sex)",
            "Institutions Evaluated": loio["institutions_evaluated"],
            "Mean Fold AUC ± SD": f"{loio['mean_demo_auc']:.4f} ± {loio['sd_demo_auc']:.4f}",
            "Min Institution AUC": f"{min(inst['auc_demo'] for inst in loio['institution_level_metrics']):.4f}",
            "Max Institution AUC": f"{max(inst['auc_demo'] for inst in loio['institution_level_metrics']):.4f}"
        },
        {
            "Model Architecture": "Primary Brain L1 Logistic",
            "Institutions Evaluated": loio["institutions_evaluated"],
            "Mean Fold AUC ± SD": f"{loio['mean_brain_l1_auc']:.4f} ± {loio['sd_brain_l1_auc']:.4f}",
            "Min Institution AUC": f"{min(inst['auc_brain_l1'] for inst in loio['institution_level_metrics']):.4f}",
            "Max Institution AUC": f"{max(inst['auc_brain_l1'] for inst in loio['institution_level_metrics']):.4f}"
        },
        {
            "Model Architecture": "Brain ElasticNet",
            "Institutions Evaluated": loio["institutions_evaluated"],
            "Mean Fold AUC ± SD": f"{loio['mean_brain_enet_auc']:.4f} ± {loio['sd_brain_enet_auc']:.4f}",
            "Min Institution AUC": f"{min(inst['auc_brain_enet'] for inst in loio['institution_level_metrics']):.4f}",
            "Max Institution AUC": f"{max(inst['auc_brain_enet'] for inst in loio['institution_level_metrics']):.4f}"
        },
        {
            "Model Architecture": "Brain Random Forest",
            "Institutions Evaluated": loio["institutions_evaluated"],
            "Mean Fold AUC ± SD": f"{loio['mean_brain_rf_auc']:.4f} ± {loio['sd_brain_rf_auc']:.4f}",
            "Min Institution AUC": f"{min(inst['auc_brain_rf'] for inst in loio['institution_level_metrics']):.4f}",
            "Max Institution AUC": f"{max(inst['auc_brain_rf'] for inst in loio['institution_level_metrics']):.4f}"
        }
    ]
    df_t3 = pd.DataFrame(t3_data)
    df_t3.to_csv(TABLES_DIR / "table3_loio_cross_validation.csv", index=False)
    with open(TABLES_DIR / "table3_loio_cross_validation.json", "w") as f:
        json.dump(t3_data, f, indent=2)
    print("Generated Table 3: Leave-One-Institution-Out CV")
    return df_t3


def generate_table4_simulation_gate():
    # 1. Authoritative configuration sources
    with open(ROOT / "vv_audit/obuchowski_validation/obuchowski_config.json") as f:
        ob_cfg = json.load(f)
    with open(ROOT / "vv_audit/obuchowski_validation/gate_decisions.json") as f:
        gate = json.load(f)
    with open(ROOT / "vv_audit/obuchowski_validation/truth_cache.json") as f:
        truth = json.load(f).get("truth_cache", {})

    from calibrate_monte_carlo_gate import CONFIG as GATE_DESIGN_CFG

    regions = GATE_DESIGN_CFG["regions"]
    scenario_cfg_map = {sc["id"]: sc for sc in ob_cfg["scenarios"]}
    verdicts = gate.get("check_verdicts", {})
    cutoffs = gate.get("cutoffs", {})

    # Design boundary definitions from calibrate_monte_carlo_gate.py
    # type1: target <= 0.055, unacceptable >= 0.070
    # coverage_twosided: target [0.935, 0.965], unacceptable <= 0.915 or >= 0.985
    # coverage_onesided: target >= 0.935, unacceptable <= 0.915
    type1_reg = regions["type1"]
    cov2_reg = regions["coverage_twosided"]
    cov1_reg = regions["coverage_onesided"]

    dim_design_specs = {
        "type1": {
            "name": "Type I Error",
            "p_target": f"<= {type1_reg['acc_max']*100:.1f}%",
            "p_unacc": f">= {type1_reg['unacc_min']*100:.1f}%",
            "pass_rule": f"k <= {cutoffs['type1']['k_pass']}",
            "fail_rule": f"k >= {cutoffs['type1']['k_fail']}"
        },
        "cov2": {
            "name": "Two-Sided Coverage",
            "p_target": f"{cov2_reg['target']*100:.1f}% [{cov2_reg['acc_lo']*100:.1f}%, {cov2_reg['acc_hi']*100:.1f}%]",
            "p_unacc": f"<= {cov2_reg['unacc_lo']*100:.1f}% or >= {cov2_reg['unacc_hi']*100:.1f}%",
            "pass_rule": f"{cutoffs['cov2']['k_pass_lo']} <= k <= {cutoffs['cov2']['k_pass_hi']}",
            "fail_rule": f"k <= {cutoffs['cov2']['k_fail_lo']} or k >= {cutoffs['cov2']['k_fail_hi']}"
        },
        "cov1": {
            "name": "One-Sided Coverage",
            "p_target": f">= {cov1_reg['acc_min']*100:.1f}%",
            "p_unacc": f"<= {cov1_reg['unacc_max']*100:.1f}%",
            "pass_rule": f"k >= {cutoffs['cov1']['k_pass']}",
            "fail_rule": f"k <= {cutoffs['cov1']['k_fail']}"
        }
    }

    t4_data = []
    # Build dynamically from scenario definitions in obuchowski_config.json
    for sc_id, sc_info in scenario_cfg_map.items():
        k_clusters = sc_info["k"]
        n_subs = sc_info["n"]
        sc_type = sc_info["type"]
        if sc_type == "null":
            delta_desc = "Null (Delta=0.000)"
        else:
            dt_val = truth.get(sc_id, {}).get("delta_true", sc_info.get("delta_target", 0.0))
            delta_desc = f"Alt (Delta={dt_val:.4f})"

        for dim in sc_info["checks"]:
            chk_name = f"{sc_id}_{dim}"
            spec = dim_design_specs[dim]
            v = verdicts.get(chk_name, {})

            t4_data.append({
                "Check ID": chk_name,
                "Scenario": f"{sc_id} (K={k_clusters}, N={n_subs}, {delta_desc})",
                "Dimension": spec["name"],
                "Replicates (M)": ob_cfg.get("m_replicates", 1500),
                "Observed Count (k)": v.get("count", "N/A"),
                "Empirical Rate": f"{v.get('rate', 0.0) * 100:.2f}%",
                "Population Target": spec["p_target"],
                "Unacceptable Boundary": spec["p_unacc"],
                "PASS Cutoff": spec["pass_rule"],
                "FAIL Cutoff": spec["fail_rule"],
                "Verdict": v.get("verdict", "N/A")
            })

    df_t4 = pd.DataFrame(t4_data)
    df_t4.to_csv(TABLES_DIR / "table4_obuchowski_simulation_gate.csv", index=False)
    with open(TABLES_DIR / "table4_obuchowski_simulation_gate.json", "w") as f:
        json.dump(t4_data, f, indent=2)
    print("Generated Table 4: Simulation Gate Results (authoritative design boundaries & dynamic config)")
    return df_t4


def generate_table5_scen04_sensitivity():
    # Record-derived coverage calculation: reads replicates.jsonl and calculates coverage across truth uncertainty
    replicates_path = ROOT / "vv_audit/obuchowski_validation/replicates.jsonl"
    summary_path = ROOT / "vv_audit/obuchowski_validation/summary.json"
    gate_path = ROOT / "vv_audit/obuchowski_validation/gate_decisions.json"

    with open(summary_path) as f:
        summary = json.load(f)
    with open(gate_path) as f:
        gate = json.load(f)

    truth_scen04 = summary["truth_cache"]["SCEN_04"]
    delta_true = float(truth_scen04["delta_true"])
    se_truth = float(truth_scen04["se_mean"])
    delta_lower = delta_true - 1.959964 * se_truth
    delta_upper = delta_true + 1.959964 * se_truth

    # Stream SCEN_04 records from replicates.jsonl
    scen04_recs = []
    with open(replicates_path, "r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            rec = json.loads(line)
            if rec.get("scenario_id") == "SCEN_04" and rec.get("status") == "OK":
                scen04_recs.append(rec)

    total_m = len(scen04_recs)
    assert total_m == 1500, f"Expected 1500 valid SCEN_04 records, found {total_m}"

    # Calculate coverage at each evaluation point
    cov_nominal = sum(1 for r in scen04_recs if r["normal_ci_two_sided"][0] <= delta_true <= r["normal_ci_two_sided"][1])
    cov_lower = sum(1 for r in scen04_recs if r["normal_ci_two_sided"][0] <= delta_lower <= r["normal_ci_two_sided"][1])
    cov_upper = sum(1 for r in scen04_recs if r["normal_ci_two_sided"][0] <= delta_upper <= r["normal_ci_two_sided"][1])

    # Cross-check against saved summary outputs
    saved_scen04_cov2 = gate["check_verdicts"]["SCEN_04_cov2"]["count"]
    assert cov_nominal == saved_scen04_cov2, f"Nominal coverage discrepancy: record-derived {cov_nominal} != saved {saved_scen04_cov2}"

    # Binomial gate cutoffs for cov2 at M=1500
    pass_cutoff_lo = gate["cutoffs"]["cov2"]["k_pass_lo"]
    pass_cutoff_hi = gate["cutoffs"]["cov2"]["k_pass_hi"]
    fail_cutoff_lo = gate["cutoffs"]["cov2"]["k_fail_lo"]
    fail_cutoff_hi = gate["cutoffs"]["cov2"]["k_fail_hi"]

    def decide_cov2(k):
        if pass_cutoff_lo <= k <= pass_cutoff_hi:
            return "PASS"
        if k <= fail_cutoff_lo or k >= fail_cutoff_hi:
            return "FAIL"
        return "INCONCLUSIVE"

    conditions = [
        ("Estimated Numerical Truth Mean (Delta_true)", delta_true, cov_nominal),
        ("Lower 95% Confidence Bound (Delta_true - 1.96*SE)", delta_lower, cov_lower),
        ("Upper 95% Confidence Bound (Delta_true + 1.96*SE)", delta_upper, cov_upper)
    ]

    t5_data = []
    for cond_name, d_val, k_cov in conditions:
        verdict = decide_cov2(k_cov)
        rate = (k_cov / total_m) * 100
        t5_data.append({
            "Evaluation Condition": cond_name,
            "Delta Value": f"{d_val:.6f}",
            "Replicates Evaluated (M)": total_m,
            "Covered Replicates (k)": k_cov,
            "Empirical Coverage Rate": f"{rate:.2f}%",
            "PASS Rule": f"{pass_cutoff_lo} <= k <= {pass_cutoff_hi}",
            "FAIL Rule": f"k <= {fail_cutoff_lo} or k >= {fail_cutoff_hi}",
            "Verdict": verdict
        })

    df_t5 = pd.DataFrame(t5_data)
    df_t5.to_csv(TABLES_DIR / "table5_truth_sensitivity_scen04.csv", index=False)
    with open(TABLES_DIR / "table5_truth_sensitivity_scen04.json", "w") as f:
        json.dump(t5_data, f, indent=2)
    print("Generated Table 5: SCEN_04 Sensitivity Analysis (record-derived from replicates.jsonl)")
    return df_t5


if __name__ == "__main__":
    generate_table1_demographics()
    generate_table2_benchmark_5fold()
    generate_table3_loio()
    generate_table4_simulation_gate()
    generate_table5_scen04_sensitivity()
    print("All manuscript tables successfully generated!")
