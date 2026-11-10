# Aim 2 Results: Generalization to Unseen Institutions and In-Fold Harmonization

**Plan:** `RESEARCH_PROPOSAL_ABIDE.md` @ tag `analysis-plan-v2`. The code and clarifications 11–16 (`../DEVIATIONS.md`) were committed before the run (`b8715f5`).
**Run:** 2026-11-10, Python 3.11.16, scikit-learn 1.9.1; runtime 64 s. Primary family: L1 logistic, C = 0.1.
**Raw outputs:** `results/aim2_results.json`, `results/table_loio.csv`, `results/table_per_institution.csv`, `results/table_kfold_harmonization.csv`; SHA-256 hashes in `results/OUTPUT_SHA256.txt`.
**Consistency check:** the unharmonized LOIO ΔAUC_full (0.02754) reproduces the Aim 1 value exactly.

LOIO = leave-one-institution-out (17 institutions). C₀ = age, sex, eTIV, site. C₃ = C₀ + IQ + head motion + T1 quality + rater flag.

---

## 1. H2 verdict: **MET** (formal criterion: LOIO ΔAUC_full > 0)

| Quantity | Value |
| :--- | :--- |
| Pooled LOIO ΔAUC_full (C₃ + Brain vs C₃) | **0.0275** [0.0019, 0.0561] (institution bootstrap) |
| Random-effects mean of per-institution ΔAUC (HKSJ) | **0.0358** [0.0138, 0.0578], p = 0.003 |
| Institutions with ΔAUC > 0 | **14 / 17** |
| Heterogeneity (descriptive) | τ² = 0.000, I² = 0%, Q = 8.41 (16 df); 95% prediction interval [0.014, 0.058] |

After confound control, the small brain increment holds up across institutions: it is positive in 14 of 17, and the prediction interval for a new institution stays above zero.

**Caveat on the heterogeneity estimate.** Per-institution DeLong SEs are large (0.035–0.155, sites of 26–175 subjects), so this analysis has little power to detect heterogeneity. Q = 8.4 is below its expected value of 16. τ² = 0 means heterogeneity was **not detectable at this precision**; it does not show the sites are homogeneous.

## 2. Confound control makes the signal more consistent across sites

| Model | Per-institution ΔAUC range | I² | τ² | 95% prediction interval |
| :--- | :---: | :---: | :---: | :---: |
| C₀ + Brain vs C₀ (unadjusted) | −0.117 to +0.296 | 23% | 0.0021 | **[−0.035, 0.187]** (includes 0; corrected 2026-11-10 from a rounding error, [−0.036, 0.188]) |
| C₃ + Brain vs C₃ (adjusted) | −0.029 to +0.171 | 0% | 0.0000 | **[0.014, 0.058]** |

The unadjusted brain increment varies widely between institutions: from −0.12 at Caltech to +0.30 at Max Munich. Its prediction interval includes zero, so for a new site the unadjusted model's benefit cannot be relied on. Adding IQ, motion and quality makes the increment **smaller and more consistent**. This fits Aim 1: much of the unadjusted, site-varying signal comes from site-varying confounds.

## 3. In-fold ComBat harmonization (brain block only; age and sex protected; diagnosis not protected)

| Design | Level | ΔAUC raw | ΔAUC ComBat | AUC (C + Brain), ComBat |
| :--- | :---: | :---: | :---: | :---: |
| 5-fold × 10 (all sites seen in training) | C₀ | 0.0914 [0.062, 0.124] | **0.1125** [0.079, 0.149] | 0.633 |
| 5-fold × 10 | C₃ | 0.0342 [0.016, 0.060] | **0.0463** [0.025, 0.080] | **0.672** |
| LOIO (held-out site self-estimated, label-free) | C₀ | 0.0852 [0.037, 0.135] | **0.1090** [0.062, 0.156] | 0.622 |
| LOIO | C₃ | 0.0275 [0.002, 0.056] | **0.0411** [0.016, 0.070] | 0.653 |

For C₃ with ComBat, the LOIO meta-analysis gives mu = 0.0460 [0.020, 0.072], I² = 0%, PI [0.020, 0.072].

**Interpretation**

- Removing site-specific location and scale effects from the FreeSurfer features raises the adjusted brain increment by about 0.012–0.014 AUC, in both designs.
- The gain also appears in 5-fold CV, where every site's parameters come from training data. So it is not explained by the transductive estimation used for held-out sites under LOIO (clarification 11).
- With harmonization, the adjusted increment (0.041–0.046) is clearly above the 0.03 smallest effect of interest. **This does not change the Aim 1 verdict.** H1 was pre-specified on the unharmonized model and the rule is not revisited. It is a secondary result that will be reported as such.

## 4. Implications for the paper

1. **The adjusted signal generalizes across sites.** It is positive at unseen institutions in pooled LOIO and in the meta-analysis, and its prediction interval excludes zero.
2. **Confound adjustment changes the picture across sites.** The unadjusted brain increment looks larger but is site-dependent (its prediction interval includes zero). The adjusted increment is smaller but consistent.
3. **Harmonization helps modestly.** In-fold ComBat adds about +0.012 AUC; it is a sensible default for the Aim 3 localization models.
4. **Practical value remains low.** The best model reaches AUC 0.67. The results are descriptive (Path A), and the heterogeneity analysis has little power.
