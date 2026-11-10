# Aim 3 Results: Where Does the Confound-Adjusted Signal Lie?

Plan: `RESEARCH_PROPOSAL_ABIDE.md` §4.6 at tag `analysis-plan-v2`. Implementation choices: `analyses/DEVIATIONS.md` clarifications 17–21, committed before the run.
Run: `analyses/aim3_localization.py`, git HEAD `8e7c391`, Python 3.11.16, scikit-learn 1.9.1, 1,000 permutations, 850 s. Output hashes: `results/OUTPUT_SHA256.txt` (all verify OK).

**All Aim 3 analyses are exploratory and descriptive.** P-values are not adjusted for multiplicity (§4.4). Coefficients are conditional associations within a model that also contains age, sex, eTIV, site, IQ, motion and T1 quality. They are not group differences, and they are not causal.

Primary model throughout: C₃ confounds + brain block, L1 logistic (C = 0.1), unharmonized, 10 × stratified 5-fold. Intervals are site-cluster bootstrap intervals computed per repeat (D1 convention).

## 1. Compartments

Each block is added **on its own** to the C₃ confound model (AUC 0.626).

| Compartment | Features | ΔAUC | 95% CI | Within-site perm. p | Null mean | ComBat ΔAUC [95% CI] |
| :--- | :-: | :-: | :-: | :-: | :-: | :-: |
| Cortical thickness | 70 | 0.016 | [−0.009, 0.037] | 0.001 | −0.011 | 0.028 [−0.006, 0.058] |
| Cortical area | 70 | 0.013 | [−0.008, 0.034] | 0.004 | −0.012 | 0.008 [−0.018, 0.032] |
| Subcortical / ventricular / cerebellar | 34 | **0.022** | **[0.002, 0.049]** | 0.001 | −0.008 | 0.026 [0.005, 0.055] |
| *All 174 (Aim 1, for reference)* | 174 | *0.034* | *[0.016, 0.060]* | *0.001* | | |

- **No single compartment carries the signal.** Every block is below the 0.03 SESOI. The subcortical block, with the fewest features, has the largest increment and is the only one whose interval excludes zero.
- **The permutation p-values and the intervals answer different questions.** For thickness and area the permutation p is small while the bootstrap CI includes 0. The permutation null is centred near **−0.011, not 0**, because adding 70 features of pure noise makes an L1 model *worse*. The permutation therefore tests "better than an equally large block of uninformative features" (yes, for all three). The CI tests "better than the confound model alone" (only clearly for the subcortical block). Both are reported; the manuscript must not quote the p-values alone.
- The parts do not add up to the whole: 0.016 + 0.013 + 0.022 = 0.051, against 0.034 for the full block. The compartments overlap in what they explain, and the full model also pays a larger penalty for more features.
- ComBat (secondary) raises the thickness increment and lowers the area increment. Neither change alters the pattern.

## 2. Age strata

Each stratum is analysed in its own 10 × 5-fold CV (clarification 18).

| Stratum | n (ASD) | Sites | Level | AUC confounds | ΔAUC | 95% CI |
| :--- | :-: | :-: | :-: | :-: | :-: | :-: |
| < 18 years | 718 (351) | 17 | C₀ | 0.511 | 0.114 | [0.075, 0.153] |
| | | | **C₃** | 0.630 | **0.040** | **[0.012, 0.074]** |
| ≥ 18 years | 317 (154) | 12 | C₀ | 0.477 | 0.070 | [0.033, 0.112] |
| | | | **C₃** | 0.572 | **0.004** | **[−0.040, 0.062]** |

- In children and adolescents the confound-adjusted increment (0.040) is above the SESOI, and its interval excludes 0.
- In adults the adjusted increment is **not detected** (0.004). The interval is wide (n = 317, 12 sites) and still allows an effect as large as the one in under-18s. **This is not evidence that the effect is absent in adults**, and no formal age × brain interaction was tested, so the two strata should not be described as "different".
- The unadjusted increment exists in both strata. In adults the confounds remove nearly all of it, versus about two-thirds in under-18s.

## 3. Stability selection

Settings: 100 stratified half-samples of the full C₃ + Brain L1 model. "Stable" means selected in ≥ 70% of refits, with the same sign in all of them.

158 of the 174 features are selected at least once; 14 are selected in ≥ 50% of refits; **6 are stable**:

| Feature | Compartment | Selection freq. | Sign (+ = higher odds of ASD) |
| :--- | :--- | :-: | :-: |
| Left inferior lateral ventricle | subcortical | 0.97 | + |
| Left lateral ventricle | subcortical | 0.93 | + |
| Right insula area | area | 0.90 | + |
| Right pericalcarine area | area | 0.87 | − |
| Right paracentral thickness | thickness | 0.73 | − |
| Right parahippocampal area | area | 0.71 | + |

Next below the threshold are right cuneus area (0.69, −) and left entorhinal thickness (0.68, −). The 70% cut-off is a convention, so features just below it should not be treated as qualitatively different.

Interpretation limits:

- Signs are **conditional on eTIV and the other confounds**. For example, "+" for the lateral ventricle means a larger ventricle *for a given head size, age, sex, site, IQ, motion and image quality*.
- L1 selects one of several correlated features, so a feature's absence does not mean it is unrelated to diagnosis.
- Stability selection here uses the full sample. It describes which features the model leans on. It does not validate them on held-out data.

Full table: `results/table_stability_selection.csv`. Figures: `figures/fig_atlas_*.png`.

## 4. Calibration and decision curve

Values below are out-of-fold, per repeat, averaged over 10 repeats.

| Model | Calibration intercept | Calibration slope | Brier |
| :--- | :-: | :-: | :-: |
| C₃ confounds | −0.038 | 1.02 | 0.237 |
| C₃ + Brain | −0.022 | **0.87** | 0.229 |

- Adding brain features makes predictions slightly too extreme (slope 0.87 < 1). This is mild overfitting, as expected from 174 features at C = 0.1. Calibration-in-the-large is fine.

Net benefit at key thresholds (prevalence in sample 0.488):

| Threshold | C₃ | C₃ + Brain | Gain | Classify all |
| :-: | :-: | :-: | :-: | :-: |
| 0.3 | 0.262 | 0.263 | 0.001 | **0.268** |
| 0.4 | 0.144 | 0.173 | 0.029 | 0.147 |
| 0.5 | 0.089 | 0.109 | 0.020 | −0.024 |
| 0.6 | 0.060 | 0.064 | 0.004 | −0.280 |
| 0.7 | 0.024 | 0.044 | 0.021 | −0.707 |

- Between thresholds 0.4 and 0.7, brain features add a small net benefit over the confound model: 0.003–0.029 across all thresholds in that range, i.e. about 0–3 additional correct ASD classifications per 100 people without extra false positives.
- At thresholds ≤ 0.3 neither model beats "classify all".
- The sample is about 49% ASD, unlike any clinical population, so these numbers **do not** describe clinical utility. They are reported because §4.6 asks for them, and they are consistent with the small AUC increment.

## 5. Summary for the manuscript

1. The confound-adjusted signal is **diffuse**. It is spread across thickness, area and subcortical/ventricular volumes, and no compartment alone reaches the SESOI. The subcortical/ventricular block is the most robust single block.
2. The signal is **concentrated in under-18s** (0.040 [0.012, 0.074]). In adults it was not detected, with an interval too wide to rule out a similar effect.
3. A handful of features are consistently selected, led by **left lateral and inferior lateral ventricle volume (+)** and **right insula area (+)**. They are conditional associations in a penalized model, not localized group differences.
4. Adding brain features improves the Brier score slightly, introduces mild overconfidence, and adds at most about 3 net correct classifications per 100 people. This is not clinical utility.

## Figures (`analyses/figures/`, from `analyses/make_figures.py`)

| File | Content |
| :--- | :--- |
| `fig_attenuation.png` | Aim 1: ΔAUC across C₀–C₃ with corrected intervals and the SESOI line |
| `fig_forest_loio.png` | Aim 2: per-institution ΔAUC, random-effects mean and prediction interval (C₀ vs C₃) |
| `fig_atlas_thickness.png`, `fig_atlas_area.png` | Aim 3: signed selection frequency on Desikan–Killiany (top row right hemisphere, bottom row left) |
| `fig_atlas_subcortical.png` | Aim 3: signed selection frequency on aseg. ggseg 0.1 renders the cerebellum and brainstem in fixed black; their values are in the CSV |
| `fig_decision_curve.png` | Aim 3: net benefit, C₃ vs C₃ + Brain vs classify-all/none |
