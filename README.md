# Brain or Bias? Structural MRI Classification of Autism in ABIDE I

**Status: project closed (v1.0-final, 2026-11-10).** All analyses in the v2 plan are complete and a manuscript draft is written. The work is descriptive and exploratory (Path A). External validation (ABIDE II) and the follow-up inference simulation were closed as out of scope, not left pending. See [`STATUS_REGISTER.md`](STATUS_REGISTER.md) for the authoritative status.

**Licence:** the ABIDE-derived data are under CC BY-NC-SA 3.0. They are not public domain, and commercial use is prohibited without separate licensing.

---

## What this project found

Using ABIDE I FreeSurfer v6 morphometry (N = 1,035; 505 autistic, 530 typically developing; 17 institutions; 174 features):

| Question | Result |
| :--- | :--- |
| How much do brain features add over age, sex, head size and site? | ΔAUC **0.091** [0.062, 0.124] |
| …after also adjusting for IQ, head motion and scan quality? | ΔAUC **0.034** [0.016, 0.060]. IQ, motion and quality remove **63%** of the increment |
| Do the confounds alone do better than the conventionally adjusted brain model? | Yes: AUC **0.626** vs 0.612 |
| Is the residual signal real? (pre-specified H1) | **Robust signal**, at the margin of the 0.03 threshold. Permutation p = 0.001; positive at unseen institutions (leave-one-institution-out ΔAUC 0.028). Five of six sensitivity analyses fall just below 0.03 |
| Does it generalize across sites? (H2) | Positive at 14 of 17 institutions; 95% prediction interval [0.014, 0.058]. In-fold ComBat raises it to about 0.04–0.05 |
| Where is it? (exploratory) | Diffuse across thickness, area and subcortical/ventricular volumes. Detected under age 18 (0.040); not detected in adults (0.004, wide interval). Six stable features, led by lateral ventricle volume and right insula area |
| Is it clinically useful? | No. The best model's AUC is about 0.66–0.67, and net benefit improves by at most about 3 per 100 people |

**Bottom line:** about two-thirds of the sMRI signal that a typical ABIDE classifier attributes to the brain is shared with IQ, head motion and image quality. The small residual is reproducible but far from diagnostic.

---

## Where to look

| You want | Go to |
| :--- | :--- |
| Reporting checklist | [`manuscript/TRIPOD_AI_CHECKLIST.md`](manuscript/TRIPOD_AI_CHECKLIST.md) (Manuscript submitted directly to journal) |
| The analysis plan (fixed at git tag `analysis-plan-v2` before analysis) | [`RESEARCH_PROPOSAL_ABIDE.md`](RESEARCH_PROPOSAL_ABIDE.md) |
| Every choice the plan left open, and the one deviation | [`analyses/DEVIATIONS.md`](analyses/DEVIATIONS.md) |
| Results per aim | [`analyses/aim1/RESULTS.md`](analyses/aim1/RESULTS.md) (confound attenuation), [`analyses/aim2/RESULTS.md`](analyses/aim2/RESULTS.md) (site generalization, ComBat), [`analyses/aim3/RESULTS.md`](analyses/aim3/RESULTS.md) (localization, calibration) |
| Figures | [`analyses/figures/`](analyses/figures/) |
| Data provenance and variables | [`FEATURE_MANIFEST_AND_COHORT_FLOW.md`](FEATURE_MANIFEST_AND_COHORT_FLOW.md), [`DATA_DICTIONARY.md`](DATA_DICTIONARY.md), [`feature_manifest_174.csv`](feature_manifest_174.csv) |
| How to reproduce, including on Windows | [`REPRODUCIBILITY_GUIDE.md`](REPRODUCIBILITY_GUIDE.md) |

---

## Reproduce the v2 results

From the repository root, with the environment in [`REPRODUCIBILITY_GUIDE.md`](REPRODUCIBILITY_GUIDE.md):

```bash
python analyses/aim1_confound_attenuation.py        # ~15 min
python analyses/aim1_intervals_corrected.py
python analyses/aim2_site_generalization.py         # ~1 min
python analyses/aim3_localization.py                # ~15 min
python analyses/make_figures.py
python manuscript/check_numbers.py                  # checks all 192 reported metrics against canonical results
python -m pytest analyses/tests/ -q
```

Each aim writes `results/OUTPUT_SHA256.txt`. To verify a folder without re-running it, use `sha256sum -c OUTPUT_SHA256.txt` inside that folder. The input dataset `abide_freesurfer_tabular_dataset.csv` has SHA-256 `9c84f601fd22a7aaa1780983d42fa884c3ef9d38878a32e465a37bcd42d99b3c`, and the scripts check it on load.

---

## Repository map

- `analyses/`: Shared modules (`common.py`, `harmonize.py`, `meta.py`, `evaluation.py`), aim-specific scripts, regression tests, and canonical results.
- `manuscript/`: TRIPOD+AI checklist, automated numerical verification audit (`check_numbers.py`), and cohort tables.
- `abide_freesurfer_tabular_dataset.csv`: Primary ABIDE I FreeSurfer v6 analysis dataset ($N = 1,035$).
- `feature_manifest_174.csv`: Complete anatomical dictionary for all 174 morphometry features.

**Archive**
- [`archive/RESEARCH_PROPOSAL_ABIDE_v1.md`](archive/RESEARCH_PROPOSAL_ABIDE_v1.md): the v1 proposal.
- [`archive/interim_reports/`](archive/interim_reports/): phase reviews, interim completion reports, the superseded status register, two supervisor reviews of the external runner, and the feasibility-stage README with its full benchmark tables. These files were moved at closure; their relative links were updated, and their content is otherwise unchanged.

---

## Closed, not pursued

These items need external parties or data:
- ABIDE II validation, which needs the curators' subject crosswalk and two-rater visual QC (PREREQ_02/03);
- the prospective M = 2000 inference simulation, with independent statistical review (GATE-03/08);
- visual QC of raw images.

None of these were self-certified. The manuscript lists them as future work.

---

## Citation

**Authors:** Dipesh Gurung¹, Binod Bhattarai¹ (corresponding), Prof. Dr. R. N. Thakur²
¹ Department of Computer Science, Noida International University, Greater Noida, India
² Lord Buddha Education Foundation, Kathmandu, Nepal

> Gurung D, Bhattarai B, Thakur RN. *Brain or Bias? Confound Control Removes Most of the Structural MRI Classification Signal for Autism in ABIDE I* — analysis code and results (v1.0). 2026. GitHub: https://github.com/Dips7/ABIDE_BrainOrBias.

Machine-readable citation metadata is in [`CITATION.cff`](CITATION.cff).
