# Deviations and Implementation Clarifications

Reference plan: `RESEARCH_PROPOSAL_ABIDE.md` at git tag `analysis-plan-v2` (commit `a851dcc`).

This file records every place where the code had to make a choice the plan did not specify, and every departure from the plan. All entries below were written **before** the full Aim 1 run was inspected. (A 4-permutation smoke test was run only to check that the code works; its p-value, which cannot go below 0.2, was not used.)

## Implementation clarifications (choices the plan left open)

| # | Plan section | Clarification |
| :-: | :--- | :--- |
| 1 | 4.3 | Repeat seeds are 20261110–20261119 (10 repeats of stratified 5-fold). Permutation seed 51110001; bootstrap seed 51120001. |
| 2 | 4.2 | "Rater-fail flag" = at least one of `qc_rater_1`, `qc_anat_rater_2`, `qc_anat_rater_3` equals `fail`. `maybe` counts as not failed. |
| 3 | 3, 4.1 | Confound numerics: median imputation with missing-value indicators (`SimpleImputer(add_indicator=True)`), then standardization. Brain features are preprocessed exactly as in the benchmark (median imputation, variance filter 1e-5, standardization, no indicators). Site is one-hot coded with `SITE_ID` (20 labels), as in the benchmark. |
| 4 | 4.1 | The linear SVM uses C = 0.1, the same C as the other families; the plan named the SVM but did not give its C. Its AUC uses decision-function scores. |
| 5 | 4.4 | The permutation uses `SITE_ID` (20 acquisition sites) as the shuffling group. Age tertiles for the stratified check are computed on the full sample. |
| 6 | 4.4 | The site-cluster bootstrap resamples the 20 `SITE_ID` clusters with replacement. Scores are the per-subject out-of-fold scores, rank-normalized within each repeat and then averaged across the 10 repeats. The plan's phrase "sites kept stratified by diagnosis" is implemented as discarding any resample that lacks one class; every site contains both classes, so the number of valid resamples is reported. |
| 7 | 4.7 | "LOIO ΔAUC_full" is the pooled out-of-fold AUC difference (C₃ + Brain minus C₃) over one leave-one-institution-out pass across the 17 institutions. |
| 8 | 4.5 | S3 motion decile cut-off: computed on the full sample (the value is recorded in the results). Subjects with missing `func_mean_fd` (n = 1) are kept. |
| 9 | 4.5 | S6: inner 5-fold grid over C ∈ {0.01, 0.03, 0.1, 0.3, 1}, tuned separately for the confound model and the brain model. |
| 10 | 4.3 | AUC is computed on the pooled out-of-fold predictions within each repeat and then averaged over the 10 repeats. The permutation statistic is the same quantity. The confound model's predictions are not recomputed for each permutation, because permuting the brain block does not change its inputs. |

### Aim 2 clarifications (written and committed before the Aim 2 run)

| # | Plan section | Clarification |
| :-: | :--- | :--- |
| 11 | 4.3 (3) | **Unseen sites under LOIO.** The plan asked for "a reference-batch approach" for the held-out site and said to report 5-fold only if leakage could not be avoided. Implementation: the training-fold covariate betas, grand mean and pooled variance standardize the held-out rows. The held-out site's location/scale EB parameters are then estimated from **its own rows' features, age and sex only. No diagnosis labels are used.** This is label-free but uses the unlabeled feature distribution of the held-out site (transductive), and is reported as such. Harmonized 5-fold results, where every site is present in training, are reported alongside. |
| 12 | 4.3 (3) | ComBat is implemented in-house (`analyses/harmonize.py`), because neuroCombat 0.2.12 has no fit/apply split; its `neuroCombatFromTraining` is marked under development and does not use each subject's own covariates. Our version matches `neuroCombat` on the full data (rtol 1e-4; `tests/test_aim2.py`). Settings: parametric EB; age and sex as linear covariates; median imputation before ComBat; features with zero training variance passed through unchanged. |
| 13 | 4.3 (3) | ComBat is applied to the **brain block only**. The confound model is unchanged (site one-hot kept), so harmonized ΔAUC compares the harmonized brain model with the same confound model. |
| 14 | 2 (H2) | The plan gave no numeric threshold for "limited between-site heterogeneity". To avoid choosing one after seeing the data, the formal H2 criterion is only **LOIO ΔAUC_full > 0** (unharmonized, primary). τ², I², Q and the 95% prediction interval are reported descriptively. |
| 15 | 4.4 | The per-institution ΔAUC variance is the paired DeLong variance (mid-ranks for ties). Meta-analysis: DerSimonian–Laird τ² with the HKSJ-adjusted CI (t, k − 1 df) and a prediction interval mu ± t(k − 2) · √(τ² + SE²_HKSJ). This is validated against statsmodels `combine_effects` (`tests/test_aim2.py`). |
| 16 | 4.4 | The pooled LOIO ΔAUC interval comes from a 2,000-draw bootstrap over the 17 institutions, applied to the single LOIO pass. |

### Aim 3 clarifications (written and committed before the Aim 3 run)

| # | Plan section | Clarification |
| :-: | :--- | :--- |
| 17 | 4.6 | Compartment models use the C₃ confound set with the thickness (70), area (70) or subcortical/ventricular/cerebellar (34) block alone. Each gets a within-site permutation of **that block only**: 1,000 permutations, `SITE_ID` groups, seeds 51110011–13. These p-values are exploratory and not adjusted for multiplicity (§4.4). The primary models are unharmonized; ComBat versions are reported as secondary (point estimate and interval, no permutation). |
| 18 | 4.6 | Age strata are defined by `AGE_AT_SCAN` < 18.0 vs ≥ 18.0, each with its own 10 × 5-fold CV. Site one-hot coding covers the sites present in the stratum. Results are reported at C₀ and C₃. No ComBat here: several sites contribute only a few adults, which leaves too few rows per site in training folds. |
| 19 | 4.6 | Stability selection uses 100 stratified half-samples (`StratifiedShuffleSplit`, train_size 0.5, seed 51130001). The full C₃ + Brain L1 pipeline (C = 0.1, unharmonized) is refitted on each. A feature counts as "selected" when its coefficient is non-zero. **"Consistent sign" means the same sign in every refit that selects it.** A feature is "stable" if it is selected in ≥ 70% of refits with a consistent sign. |
| 20 | 4.6 | Calibration intercept (logistic, with logit(p) as offset), calibration slope and Brier score are computed per repeat on pooled out-of-fold probabilities and then averaged over the 10 repeats. The same applies to decision-curve net benefit, over thresholds 0.05–0.95. This follows the per-repeat convention adopted in D1. |
| 21 | 4.6 | Atlas figure: `ggseg` 0.1 (bundled Desikan–Killiany and aseg outlines, matplotlib). Colour shows selection frequency, signed by the direction of the coefficient. |

## Additions (outputs not in the plan, all descriptive)

| # | Addition |
| :-: | :--- |
| A1 | A table of single-variable AUCs (IQ, motion, each T1 quality measure, rater flag), reported as max(AUC, 1 − AUC) with the direction of the difference. |
| A2 | Sensitivity analyses S1–S6 also report ΔAUC₀ (the unadjusted brain increment) for context. |
| A3 | The LOIO ΔAUC at level C₀ is reported for comparison with the C₃ value. |

## Deviations from the plan

### D1. Bootstrap intervals rebuilt for the reported statistic (2026-11-10, after the Aim 1 run)

**Problem found after the run.** In clarification 6, the intervals were computed from repeat-averaged scores. Averaging out-of-fold scores across the 10 repeats acts like an ensemble, so its ΔAUC is larger than the reported point estimate (the mean of per-repeat pooled ΔAUC). For the primary C₃ model the two are 0.0383 and 0.0342; for C₀ they are 0.1006 and 0.0914. As a result, some intervals did not contain their own point estimate (e.g. S1/C₀: estimate 0.0758, interval [0.0794, 0.1545]).

**Correction.** `aim1_intervals_corrected.py` recomputes the same deterministic out-of-fold predictions; all point estimates match the original run exactly. Each bootstrap draw resamples the 20 sites once and applies that draw to all 10 repeats, and the per-repeat ΔAUC is averaged. The interval therefore describes the reported statistic. Output: `aim1/results/table_intervals_corrected.csv`. **The corrected intervals are the ones reported.** The original columns `delta_ci_lo` / `delta_ci_hi` in `table_hierarchy.csv` and `table_sensitivity.csv` are kept unchanged for transparency.

**Effect on conclusions.** None on the H1 verdict: the Section 4.7 rule uses the point estimate, the permutation p-value and the LOIO ΔAUC, none of which involve the bootstrap. The corrected intervals are slightly lower and narrower.
