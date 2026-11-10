# Aim 1 Results: Confound Attenuation of the sMRI Autism Signal

**Plan:** `RESEARCH_PROPOSAL_ABIDE.md` @ tag `analysis-plan-v2` (commit `a851dcc`). The code was committed before the run (`325845d`).
**Run:** 2026-11-10, Windows, Python 3.11.16, scikit-learn 1.9.1, numpy 2.4.6, scipy 1.17.1; runtime 853 s; 1,000 permutations per null.
**Raw outputs:** `results/aim1_results.json`, `results/table_hierarchy.csv`, `results/table_sensitivity.csv`, `results/table_intervals_corrected.csv`, permutation nulls (`results/perm_null_*.npy`), out-of-fold predictions; SHA-256 hashes in `results/OUTPUT_SHA256.txt`.
**Intervals:** 95% site-cluster bootstrap (2,000 draws over the 20 sites), descriptive only. They are taken from `table_intervals_corrected.csv` (see `../DEVIATIONS.md`, D1).

N = 1,035 (505 ASD / 530 TDC). All AUCs are pooled out-of-fold values, averaged over 10 repeats of stratified 5-fold cross-validation.

---

## 1. Pre-specified H1 verdict: **ROBUST SIGNAL** (at the margin of the smallest effect of interest)

| Criterion (Section 4.7) | Required | Observed | Met |
| :--- | :--- | :--- | :---: |
| ΔAUC_full (C₃ + Brain vs C₃, L1) | ≥ 0.030 | **0.0342** [0.0164, 0.0596] | ✓ (margin 0.004) |
| Within-site permutation p | < 0.05 | **0.001** (smallest possible; null max 0.0073) | ✓ |
| LOIO ΔAUC_full | > 0 | **0.0275** | ✓ |

The stratified permutation check (shuffling within site × age tertile × sex) agrees: p = 0.001, null max 0.015.

**What this means.** After controlling for site, age, sex, intracranial volume, IQ, head motion, T1 image quality and rater QC flags, the 174 FreeSurfer features still add information about diagnosis. This is very unlikely to be chance. **However, the size of that increment sits at the pre-specified threshold, not clearly above it** (see Section 4).

## 2. Single variables (descriptive)

| Variable | AUC alone | Direction |
| :--- | :---: | :--- |
| Head motion (`func_mean_fd`, n = 1,034) | **0.609** | higher in ASD |
| Full-scale IQ (`FIQ`, n = 966) | **0.604** | lower in ASD |
| Rater QC fail flag | 0.539 | more common in ASD |
| T1 quality measures (CNR, SNR, EFC, FBER, FWHM, QI1) | 0.502–0.523 | — |

## 3. Attenuation profile (comparator hierarchy)

| Level | Confounds | AUC confounds | AUC + Brain | **ΔAUC** [95% CI] | % of C₀ increment left |
| :--- | :--- | :---: | :---: | :---: | :---: |
| C₀ | age, sex, eTIV, site | 0.520 | 0.612 | **0.0914** [0.062, 0.124] | 100% |
| C₁ | C₀ + IQ | 0.596 | 0.645 | **0.0486** [0.025, 0.082] | 53% |
| C₂ | C₀ + motion + quality | 0.592 | 0.632 | **0.0402** [0.019, 0.069] | 44% |
| C₃ | all confounds | **0.626** | 0.660 | **0.0342** [0.016, 0.060] | **37%** |

**Key observations**

- **The confounds alone (C₃, AUC 0.626) outperform the unadjusted brain model (C₀ + Brain, AUC 0.612).**
- Controlling for IQ removes about half of the apparent brain increment. Controlling for motion and quality removes a similar share. Together they remove **63%** of it.
- In leave-one-institution-out testing, the increment falls from 0.0852 (C₀) to **0.0275** (C₃).
- The best model (C₃ + Brain) reaches AUC 0.66, still far below what diagnosis would require.

**Robustness across model families (C₃):**

| Family | ΔAUC [95% CI] |
| :--- | :---: |
| L1 logistic (primary) | 0.0342 [0.016, 0.060] |
| ElasticNet | 0.0278 [0.008, 0.056] |
| Linear SVM | 0.0219 [−0.009, 0.059] |

The attenuation pattern from C₀ to C₃ is the same in all three families.

## 4. Sensitivity analyses (L1, ΔAUC at C₃; C₀ shown for context)

| Analysis | n | ΔAUC₀ | **ΔAUC₃** [95% CI] |
| :--- | :---: | :---: | :---: |
| Primary | 1,035 | 0.091 | **0.0342** [0.016, 0.060] |
| S1 Exclude any rater fail | 892 | 0.076 | **0.0277** [−0.002, 0.065] |
| S2 Exclude majority rater fail | 1,024 | 0.080 | **0.0349** [0.014, 0.064] |
| S3 Exclude top motion decile (> 0.260 mm) | 931 | 0.082 | **0.0288** [0.007, 0.057] |
| S4 Complete-case IQ | 966 | 0.112 | **0.0294** [0.009, 0.052] |
| S5 Males only | 878 | 0.096 | **0.0279** [0.006, 0.059] |
| S6 Nested tuning of C | 1,035 | 0.093 | **0.0296** [0.013, 0.053] |

**Interpretation.**

- The adjusted increment is consistent across specifications: 0.028–0.035 in every analysis.
- **Five of the six sensitivity analyses fall just below the 0.03 threshold**, as do the ElasticNet and SVM estimates and the LOIO estimate (0.0275).
- The S1 interval (rater-failed scans removed) and the SVM interval both include zero.

The primary specification meets the pre-specified rule, so the formal verdict stands. The honest summary is this: **a small anatomical signal reliably survives confound control, but its size is at or just below the smallest effect we pre-specified as meaningful.**

## 5. Note on the permutation null

The null distribution is centred **below** zero (mean −0.0245, SD 0.0095). Adding 174 features that carry no information beyond site makes an L1 model slightly worse than the confound-only model. The test therefore compares the real brain features with *equally many uninformative features*, which is the right comparison for "do these features carry information?". It also means that ΔAUC = 0 is itself about 2.6 null SDs above the null mean.

## 6. Implications for the paper

1. The headline result is the **attenuation**: about two-thirds of the commonly reported brain increment can be attributed to IQ, head motion and data quality.
2. The remaining signal is real (p = 0.001 under two permutation schemes) but **small**: about +0.03 AUC.
3. Aim 3 (localization) is worth doing, because a signal remains to localize. Its results should be presented as describing a small effect.
4. These are descriptive results from a discovery cohort (Path A); there is no external replication.
