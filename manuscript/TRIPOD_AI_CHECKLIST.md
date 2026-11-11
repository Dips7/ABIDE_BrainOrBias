# TRIPOD+AI Checklist: "Brain or Bias?" manuscript v2.0

**Guideline:** Collins et al. (2024), *BMJ* 385:e078378.

**How to read this file**
- Item topics are paraphrased. **[AUTHORS: before submission, check the numbering and wording against the official checklist and use the journal's checklist form.]**
- This study evaluates the *incremental* value of a predictor block, sMRI morphometry, over confound models. It does not develop a model intended for clinical deployment. Items about deployment are answered with that in mind.
- Section numbers refer to [`MANUSCRIPT.md`](MANUSCRIPT.md).

| # | Topic | Where / how addressed |
| :-: | :--- | :--- |
| **Title and abstract** | | |
| 1 | Identify the study as developing/evaluating a prediction model, the target population and the outcome | Title; Abstract (classification of autism vs typically developing; ABIDE I; incremental value of sMRI) |
| 2 | Structured abstract | Abstract (Background, Methods, Results, Conclusions) |
| **Introduction** | | |
| 3a | Healthcare context and rationale | §1 (sMRI biomarker claims; confounding by site, IQ, motion) |
| 3b | Target population and intended use in the care pathway | §1, §3.6, §4.4 (research question about signal; no clinical use intended; ASD-enriched sample) |
| 3c | Known health inequalities between groups | §4.4 limitation 8 (male-dominated sample); subgroup S5 males only; female-only analysis not powered |
| 4 | Objectives, including development vs evaluation | §1 last paragraph; §2.1 (H1 confirmatory-style, rest exploratory) |
| **Methods** | | |
| 5a | Data sources, separately for development and evaluation | §2.2 (ABIDE I via PCP; single cohort with internal and institution-level validation) |
| 5b | Dates of data collection | ABIDE I data collection spanned 2003–2012 across 17 international sites (Di Martino et al., 2014) |
| 6a | Setting, number and location of centres | §2.2 (20 site labels, 17 institutions); §2.6 (26–175 per institution) |
| 6b | Eligibility criteria | §2.2 (complete FreeSurfer v6 reconstruction and a diagnosis) |
| 6c | Treatments received, if relevant | Not applicable |
| 7 | Data preparation and quality checks | §2.3, §2.5 (in-fold preprocessing); rater QC and automated quality measures used as covariates and in S1/S2; hash-verified file |
| 8a | Outcome definition, timing and how assessed | §2.2 (ABIDE `DX_GROUP`, site-assigned) |
| 8b | Qualifications of outcome assessors; blinding | Site clinical diagnosis per DSM-IV-TR, ADOS, and/or ADI-R criteria by licensed clinicians (Di Martino et al., 2014); assessors blinded to subsequent FreeSurfer morphometry; retrospective evaluation |
| 8c | Consistency of outcome assessment across groups | §4.4 (site-assigned diagnosis; heterogeneity across sites possible) |
| 9a | Choice of initial predictors and their pre-selection | §2.3 (174 Desikan–Killiany/aseg measures, all used; no selection on outcome) |
| 9b | Predictor definitions, timing, measurement | §2.3; `feature_manifest_174.csv` |
| 9c | Qualifications of predictor assessors; blinding | Automated FreeSurfer v6 and PCP quality pipelines; rater QC by ABIDE raters |
| 10 | Sample size justification | Bounded by complete ABIDE I cohort meeting FreeSurfer quality criteria (N = 1,035). Statistical precision pre-specified via smallest effect size of interest (SESOI ΔAUC = 0.03), 95% bootstrap intervals, and 95% prediction intervals (§2.8) |
| 11 | Missing data handling | §2.4 (in-fold median imputation with indicators; complete-case sensitivity S4) |
| 12a | How data were used for development and evaluation | §2.6 (10 × stratified 5-fold; LOIO) |
| 12b | Predictor transformations / preprocessing | §2.5 |
| 12c | Model type, building steps, hyperparameter choice, internal validation | §2.5 (L1 logistic, C fixed; nested tuning in S6); §2.6 |
| 12d | Handling of heterogeneity across clusters/centres | §2.6 LOIO; §2.7 in-fold ComBat; §2.8 random-effects meta-analysis |
| 12e | Performance measures, with rationale | §2.5 (ΔAUC); §2.11 (calibration intercept/slope, Brier, net benefit) |
| 12f | Model updating / recalibration | Not done (no deployment) |
| 12g | Model comparison | §2.5 (same-family confound vs confound + brain); §2.8 (permutation test; H1 rule) |
| 13 | Class imbalance methods | Classes nearly balanced (49% ASD); no resampling or reweighting; stratified folds (§2.6) |
| 14 | Fairness approaches | Performance evaluated across sex subgroups (S5 males) and developmental age strata (§2.10); no algorithmic parity optimization or fair-representation constraints applied |
| 15 | Model output and any thresholds | Predicted probability; no single threshold proposed; decision curve over thresholds (§2.11) |
| 16 | Differences between development and evaluation data | Internal CV; LOIO evaluates unseen institutions (§2.6) |
| 17 | Ethics approval and consent | Institutional ethics approvals and informed consent obtained locally at each site (Di Martino et al., 2014); secondary analysis exempt per local institutional guidelines (§2.2) |
| **Open science** | | |
| 18a | Funding | Declarations (No external funding received) |
| 18b | Conflicts of interest | Declarations (None declared) |
| 18c | Protocol / analysis plan availability | §2.1 (git tag `analysis-plan-v2`; `RESEARCH_PROPOSAL_ABIDE.md`; `analyses/DEVIATIONS.md`) |
| 18d | Registration | §2.1 (not registered on an external registry; plan time-stamped in version control) |
| 18e | Data availability | Declarations |
| 18f | Code availability | Declarations; §2.12 (GitHub: https://github.com/Dips7/ABIDE_BrainOrBias, Zenodo DOI: 10.5281/zenodo.24142658) |
| 19 | Patient and public involvement | None (retrospective secondary analysis of public de-identified database) |
| **Results** | | |
| 20a | Participant flow, numbers, follow-up | §2.2, §3.1; cohort flow in `FEATURE_MANIFEST_AND_COHORT_FLOW.md` |
| 20b | Participant characteristics, including by centre | Table 1; per-institution n in `analyses/aim2/results/table_per_institution.csv` |
| 20c | Comparison of development and evaluation data | Not applicable (single cohort; folds stratified) |
| 21 | Number of participants and outcome events in each analysis | Tables 2–4 (n per analysis); age groups and sensitivity analyses report n |
| 22 | Full model specification | §2.5 (pipeline, hyperparameters); stability-selection frequencies and coefficients in `table_stability_selection.csv`; no deployable single model intended |
| 23a | Performance with CIs, including calibration | Tables 2–4; §3.6 |
| 23b | Performance across key subgroups and clusters | §3.3 (S5 males), §3.4 (17 institutions, Figure 2), §3.5 (age groups) |
| 24 | Model updating results | Not applicable |
| **Discussion** | | |
| 25 | Overall interpretation, including fairness | §4.1–4.2 |
| 26 | Limitations, including non-representative sample and risk of bias | §4.4 |
| 27a | Handling of poor-quality or unavailable input data in use | Not applicable (no deployment); quality covariates analysed (§3.2–3.3) |
| 27b | User interaction and expertise required | Not applicable |
| 27c | Future research and generalizability | §4.3; §4.4 limitation 1 (ABIDE II replication) |
