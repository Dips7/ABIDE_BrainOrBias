# Research Proposal (v2)

## Brain or Bias? Decomposing Structural-MRI Classification of Autism into Neuroanatomical, Site, Cognitive and Head-Motion Components in ABIDE I

**Version:** 2.0 (2026-11-10). Supersedes v1, which is archived at [`archive/RESEARCH_PROPOSAL_ABIDE_v1.md`](archive/RESEARCH_PROPOSAL_ABIDE_v1.md).
**Scope:** a self-contained study of ABIDE I, completed by the project team. It needs no new data, no external reviewers and no external approvals.
**Status:** this document is the analysis plan. It is to be committed and tagged (`analysis-plan-v2`) **before** any Aim 1–3 analysis is run.

---

## Abstract

Structural MRI (sMRI) classifiers for autism spectrum disorder (ASD) usually report modest accuracy. It is rarely tested whether that accuracy reflects neuroanatomy or variables that differ between groups for other reasons. Our completed feasibility benchmark on ABIDE I (N = 1,035; 505 ASD, 530 typically developing controls [TDC]; 17 institutions) found the following:

- 174 FreeSurfer morphometric features gave a pooled out-of-fold AUC of 0.595.
- The increment over an age + sex + site + intracranial-volume baseline was ΔAUC = +0.070.

A descriptive look at the same cohort shows that single non-anatomical variables do at least as well:

- full-scale IQ: AUC 0.604 (ASD mean 105.5 vs TDC 111.0);
- in-scanner head motion (resting-state mean framewise displacement): AUC 0.609 (0.157 vs 0.103 mm);
- scans flagged "fail" by at least one quality rater: 17.8% of ASD vs 10.0% of TDC.

Head motion is known to bias FreeSurfer thickness and volume estimates. The apparent brain signal may therefore be partly a cognitive and data-quality signal.

This project asks **how much of the sMRI classification signal for autism survives explicit control for site, IQ, head motion and scan quality, and where in the brain any remaining signal lies.** Before any analysis is run we fix:

- a hierarchy of comparator models;
- a valid permutation-based inference strategy that avoids the small-cluster estimator our earlier simulation found unreliable;
- decision rules for interpreting each outcome.

Every outcome is informative. A signal that holds up identifies reproducible anatomy. A signal that disappears is an important caution for the field.

---

## 1. Background and Rationale

1. **The effect sizes are small.** Large-sample work shows that brain-phenotype associations are small and unstable in samples of hundreds (Marek et al., 2022). An earlier ABIDE analysis found few robust anatomical differences in autism (Haar et al., 2016).
2. **Groups differ on variables that affect the measurement.** ASD samples typically have lower IQ and move more in the scanner. Motion systematically lowers FreeSurfer grey-matter and thickness estimates (Reuter et al., 2015). A classifier can learn these differences without learning autism-specific anatomy.
3. **Site effects are strong in multi-site data.** Site effects can be harmonized (Johnson et al., 2007; Fortin et al., 2018). However, harmonization must be fitted inside training folds, without using diagnosis labels, or it leaks information.
4. **What this project has already found:**
   - The completed benchmark (see [`README.md`](README.md)) gave the effect sizes above.
   - A 6,000-cohort simulation (`vv_audit/obuchowski_validation/`) showed that the standard clustered paired-AUC estimator does **not** keep its stated error rates with about 12 sites. Its verdict was INCONCLUSIVE: 6.4% Type I error and 92.7% coverage.
   - This proposal therefore uses permutation and resampling inference that does not rely on that estimator.

**The gap:** no ABIDE I sMRI classification study we know of reports a pre-specified, step-by-step breakdown of the classification signal into contributions from site, IQ, head motion and scan quality.

---

## 2. Research Questions and Hypotheses

**Primary question (Aim 1).** After adjusting for site, demographics, IQ, head motion and scan quality, do the 174 morphometric features still improve classification of ASD vs TDC?

- **H1 (primary):** ΔAUC_full > 0, where ΔAUC_full = AUC(C₃ + Brain) − AUC(C₃) and C₃ is the full confound set (Section 4.2).

**Secondary questions**

- **Aim 2 (generalization):** Does any remaining signal carry over to institutions the model has not seen, and is it improved by harmonization fitted inside the training folds?
  - **H2:** the leave-one-institution-out (LOIO) ΔAUC_full is greater than 0, and the per-site estimates show limited between-site heterogeneity.
- **Aim 3 (localization):** Which feature types (cortical thickness, surface area, subcortical volume) and which age groups (under 18, 18 and over) carry the remaining signal, and which individual features are selected consistently?
  - **H3:** the signal is concentrated in a stable subset of features rather than spread thinly across the feature set.

**Not a hypothesis test:** severity regression (ADOS) is reported descriptively from the existing benchmark as a negative result. It is not developed further.

---

## 3. Data

| Item | Specification |
| :--- | :--- |
| Source | ABIDE I phenotypes via the Preprocessed Connectomes Project; FreeSurfer v6 tables (pinned upstream commits; see [`FEATURE_MANIFEST_AND_COHORT_FLOW.md`](FEATURE_MANIFEST_AND_COHORT_FLOW.md)) |
| File | `abide_freesurfer_tabular_dataset.csv`, SHA-256 `9c84f601…99b3c` (verified) |
| Cohort | N = 1,035 (505 ASD / 530 TDC); 878 male / 157 female; 20 site labels, 17 institutions |
| Brain features | 174 FreeSurfer measures: 70 cortical thickness, 70 surface area, 34 subcortical/ventricular volumes ([`feature_manifest_174.csv`](feature_manifest_174.csv)) |
| Cognition | `FIQ` (available for 966) |
| Motion | `func_mean_fd` (mean framewise displacement during resting-state fMRI, available for 1,034). This measures the participant's tendency to move during the session, not motion in the T1 scan itself. |
| T1 image-quality measures | `anat_cnr`, `anat_snr`, `anat_efc`, `anat_fber`, `anat_fwhm`, `anat_qi1` (automated measures from the Preprocessed Connectomes Project, available for 1,034) |
| Rater QC | `qc_rater_1`, `qc_anat_rater_2`, `qc_anat_rater_3` (OK / maybe / fail) |
| Licence | CC BY-NC-SA 3.0 (not public domain; non-commercial use only) |

**Missing data.** Missing IQ, motion and quality values are imputed with the median inside each training fold, and a missing-value indicator is added. A complete-case analysis is run as a sensitivity check. Values coded −9999 are treated as missing.

---

## 4. Methods

### 4.1 Fixed modelling choices (set before running)

- **Primary classifier:** L1-penalized logistic regression, C = 0.1, fitted in a scikit-learn pipeline: median imputation → variance filter → standardization → classifier. All steps are fitted on training folds only. These are the settings of the existing benchmark, chosen before any of the new analyses.
- **Secondary classifiers (robustness only):** ElasticNet logistic (C = 0.1, l1_ratio = 0.5) and a linear SVM. Each brain model is compared only with a confound model from the **same family and with the same settings**.
- **Nested tuning (sensitivity only):** inner 5-fold grid search over C ∈ {0.01, 0.03, 0.1, 0.3, 1}.

### 4.2 Comparator hierarchy

| Model | Covariates | Question it answers |
| :--- | :--- | :--- |
| C₀ | Age, sex, eTIV, site (one-hot) | Reproduces the existing matched baseline |
| C₁ | C₀ + FIQ | What IQ adds |
| C₂ | C₀ + motion + T1 quality measures + rater-fail flag | What motion and data quality add |
| **C₃** | C₀ + FIQ + motion + quality | **Full confound set** |
| Cₖ + Brain | Cₖ + 174 FreeSurfer features | Increment from brain features at each level |

The **attenuation profile** is the sequence ΔAUC₀ → ΔAUC₁ → ΔAUC₂ → ΔAUC₃. It shows how much of the brain increment each confound accounts for.

*Note on interpretation:* IQ may be partly a feature of autism itself, not purely a confound. ΔAUC₃ is therefore read as "anatomical information beyond what IQ and motion already carry", not as a corrected "true" brain effect. ΔAUC₂, which leaves IQ out, is reported alongside it.

### 4.3 Validation designs

1. **Repeated stratified 5-fold cross-validation:** 10 repeats with fixed seeds. AUC is computed on the pooled out-of-fold predictions within each repeat. We report the mean and the range across repeats.
2. **Leave-one-institution-out (LOIO):** 17 folds. We report the pooled LOIO AUC and per-institution AUCs.
3. **Harmonization arm (Aim 2):** ComBat is fitted on the training fold only. Age and sex are the protected covariates; diagnosis is **not** protected, because that would require test-set labels. Test-fold data are adjusted using the training-fold estimates. Under LOIO, the held-out site has no training-fold estimates, so it is adjusted with a reference-batch approach. If this cannot be done without leakage, the harmonization arm is reported for 5-fold CV only.

### 4.4 Inference (avoids the small-cluster estimator)

- **Primary test of H1: conditional permutation of the brain features within site.** The 174-feature block is shuffled across participants *within each site*, 1,000 times, and the full cross-validated ΔAUC_full is recomputed each time. This keeps the relationships between site and anatomy, and between the confounds and diagnosis. Under the null, brain features carry no information about diagnosis beyond site. The p-value is (1 + #{null ≥ observed}) / 1001.
  - *Known limitation:* shuffling also breaks the link between brain features and the confounds within each site. This is stated as a limitation. As a check, a stratified version shuffles within site × age-tertile × sex.
- **Uncertainty intervals:** percentile intervals from 2,000 bootstrap resamples of whole sites, applied to pooled out-of-fold predictions. Each resample is a whole-site draw, with sites kept stratified by diagnosis. These are **descriptive**: with 17 institutions they are expected to be approximate, consistent with the earlier simulation finding.
- **Heterogeneity across sites (Aim 2):** random-effects meta-analysis of per-institution ΔAUC with the Hartung–Knapp–Sidik–Jonkman adjustment, which suits small numbers of sites. We report τ², I² and a 95% prediction interval.
- **Multiplicity:** H1 is the only confirmatory-style test. All other analyses are labelled exploratory, and their p-values are not corrected for multiple testing and are not interpreted as tests.

### 4.5 Sensitivity analyses (Aim 1)

| ID | Variation |
| :--- | :--- |
| S1 | Exclude scans failed by any rater (n ≈ 892 retained) |
| S2 | Exclude scans failed by at least 2 of 3 raters |
| S3 | Exclude the highest motion decile (`func_mean_fd`) |
| S4 | Complete-case analysis for IQ (n = 966) |
| S5 | Males only (n = 878) |
| S6 | Nested hyperparameter tuning instead of fixed C |

### 4.6 Localization (Aim 3)

- **Compartment models:** C₃ + thickness only; C₃ + area only; C₃ + subcortical only. Each gets its own ΔAUC and its own within-site permutation test.
- **Age groups:** under 18 (n = 718) and 18 or over (n = 317), each fitted separately within its own cross-validation.
- **Stability selection:** 100 half-sample refits of the C₃ + Brain L1 model. For each feature we report how often it is selected and the sign of its coefficient. A feature counts as "stable" if it is selected in at least 70% of refits with a consistent sign. Results are shown on the Desikan–Killiany atlas.
- **Model performance reporting:** calibration (intercept and slope) and a decision curve for the C₃ + Brain model. These support the clinical-utility discussion.

### 4.7 Pre-specified interpretation rules for H1

| Outcome | Rule | Interpretation |
| :--- | :--- | :--- |
| **Robust signal** | ΔAUC_full ≥ 0.03, permutation p < 0.05, and LOIO ΔAUC_full > 0 | Anatomy adds information beyond site, IQ, motion and quality; Aim 3 describes where |
| **Attenuated signal** | p < 0.05, but ΔAUC_full < 0.03 or LOIO ΔAUC_full ≤ 0 | Some signal remains, but it is too small or too site-specific to matter in practice |
| **Explained** | p ≥ 0.05 | Within the precision of this study, the brain increment is accounted for by the confounds |

The cut-off of 0.03 is a pre-specified smallest effect of interest. It is about 40% of the unadjusted increment of 0.070.

---

## 5. Reuse of Existing Assets

| Asset | Role in v2 |
| :--- | :--- |
| Feasibility benchmark (`run_abide_ml_benchmark.py`, `benchmark_results_summary.json`) | Reproduces C₀. Frozen; not re-run or edited. |
| Frozen discovery models (`discovery_pipeline/frozen_models_v2/`) | Kept as a historical reference; not used for new results |
| Obuchowski simulation (`vv_audit/obuchowski_validation/`) | Reported as a methodological finding; the reason for the inference design in Section 4.4 |
| External intake runner (`external_validation/`) | Archived as a tool for anyone who later obtains ABIDE II access; outside this project's scope |
| QC tooling (`qc_workflow/`) | Not used (no raw images in scope) |

New code goes in `analyses/`, with one script per aim, fixed seeds and a lock file of SHA-256 hashes for its outputs. The frozen historical artifacts and their manifests are not modified.

---

## 6. Explicitly Out of Scope

The following items need external parties or data and are **closed as not pursued**. They are not left pending.

- Validation on ABIDE II (needs the curators' subject-to-site crosswalk and two-rater visual QC: PREREQ_02/03)
- The prospective M = 2000 inference simulation and its independent statistician review (GATE-03/08)
- Visual QC of raw images and reconstruction from raw scans
- SHAP projected onto 3D surfaces, TabNet and stacked ensembles (they add complexity without answering the research question)

The manuscript will present these as future work for groups with ABIDE II access.

---

## 7. Work Plan (8 weeks)

| Week | Work | Output |
| :---: | :--- | :--- |
| 0 | Commit and tag this plan (`analysis-plan-v2`) | Analysis plan fixed before any analysis |
| 1 | Shared code in `analyses/`: data loading, confound sets, pipelines, CV, permutation engine, unit tests | Tested codebase |
| 2–3 | **Aim 1:** comparator hierarchy, attenuation profile, permutation test of H1, sensitivity analyses S1–S6 | `analyses/aim1/` results and tables |
| 4 | **Aim 2:** LOIO, in-fold ComBat, random-effects meta-analysis across sites | `analyses/aim2/` and forest plot |
| 5 | **Aim 3:** compartment models, age groups, stability selection, calibration and decision curve | `analyses/aim3/` and atlas figure |
| 6–7 | Rewrite the manuscript around the attenuation result; TRIPOD+AI checklist; figures; references | Submission-ready manuscript |
| 8 | Project closure: final README, archive the interim reports, tag `v1.0-final`, optional Zenodo DOI | Closed and citable project |

---

## 8. Expected Outcomes and Their Value

- **Robust signal:** a confound-controlled, site-validated estimate of the anatomical signal in autism, with the specific stable features identified.
- **Attenuated or explained:** a concrete demonstration that a typical ABIDE sMRI classifier's accuracy can be accounted for by IQ, head motion and site. Together with the inference simulation, this gives methods guidance for multi-site neuroimaging machine learning.

**Target venues:** *NeuroImage: Clinical*, *Human Brain Mapping*, *Biological Psychiatry: Cognitive Neuroscience and Neuroimaging*, or *Autism Research*.

---

## 9. Risks and Mitigations

| Risk | Mitigation |
| :--- | :--- |
| `func_mean_fd` comes from the functional scan, not the T1 | State it as a participant-level motion proxy; T1 quality measures and rater flags are included alongside it in C₂ |
| Adjusting for IQ removes part of the autism phenotype | Report ΔAUC₂ (without IQ) and ΔAUC₃ (with IQ) side by side (Section 4.2) |
| The permutation null is approximate (shuffling also breaks brain–confound links) | Stratified check shuffling within site × age × sex; limitation stated |
| Limited power with 17 sites | Pre-specified smallest effect of interest, prediction intervals, no claims of equivalence |
| Analytical flexibility | Plan tagged in git before analysis; any deviation logged in `analyses/DEVIATIONS.md` |

---

## 10. References

1. Di Martino, A., et al. (2014). The autism brain imaging data exchange. *Molecular Psychiatry*, 19(6), 659–667.
2. Marek, S., et al. (2022). Reproducible brain-wide association studies require thousands of individuals. *Nature*, 603, 654–660.
3. Haar, S., Berman, S., Behrmann, M., & Dinstein, I. (2016). Anatomical abnormalities in autism? *Cerebral Cortex*, 26(4), 1440–1452.
4. Reuter, M., et al. (2015). Head motion during MRI acquisition reduces gray matter volume and thickness estimates. *NeuroImage*, 107, 107–115.
5. Johnson, W. E., Li, C., & Rabinovic, A. (2007). Adjusting batch effects in microarray expression data using empirical Bayes methods. *Biostatistics*, 8(1), 118–127.
6. Fortin, J.-P., et al. (2018). Harmonization of cortical thickness measurements across scanners and sites. *NeuroImage*, 167, 104–120.
7. Ojala, M., & Garriga, G. C. (2010). Permutation tests for studying classifier performance. *Journal of Machine Learning Research*, 11, 1833–1863.
8. IntHout, J., Ioannidis, J. P. A., & Borm, G. F. (2014). The Hartung-Knapp-Sidik-Jonkman method for random effects meta-analysis is straightforward and considerably outperforms the standard DerSimonian-Laird method. *BMC Medical Research Methodology*, 14, 25.
9. Obuchowski, N. A. (1997). Nonparametric analysis of clustered ROC curve data. *Biometrics*, 53(2), 567–578.
10. Meinshausen, N., & Bühlmann, P. (2010). Stability selection. *Journal of the Royal Statistical Society: Series B*, 72(4), 417–473.
11. Collins, G. S., et al. (2024). TRIPOD+AI statement. *BMJ*, 385, e078378.
12. Gotham, K., et al. (2009). Standardizing ADOS scores for a measure of severity in autism spectrum disorders. *Journal of Autism and Developmental Disorders*, 39(5), 693–705.
