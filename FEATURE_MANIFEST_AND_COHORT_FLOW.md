# ABIDE I Feature Manifest, Cohort Accounting & Provenance (Audited Round 4)

**Dataset File:** `abide_freesurfer_tabular_dataset.csv`  
**Machine-Readable Feature Manifest:** `feature_manifest_174.csv`  
**Feature Rankings (Full-Sample L1):** `feature_rankings_l1.csv`  
**Environment Specification:** `environment_info.json`  
**Dataset SHA-256 Checksum:** `9c84f601fd22a7aaa1780983d42fa884c3ef9d38878a32e465a37bcd42d99b3c`  
**Date of Audit & Compilation:** 4 November 2026

---

## 1. Upstream Data Provenance & Licensing

* **Phenotypic Records:** Sourced from the Autism Brain Imaging Data Exchange I (ABIDE I) via the Preprocessed Connectomes Project (PCP).  
  * Repository: `https://github.com/preprocessed-connectomes-project/abide`  
  * Pinned Commit SHA: `fda1ec5d3f53eb97d94352e779f37c3ce46caee1`
* **FreeSurfer v6 Aggregated Morphometry Tables:** Sourced from the community-curated FreeSurfer v6.0 reconstruction release by `dfsp-spirit`.  
  * Repository: `https://github.com/dfsp-spirit/abide_preproc_smri_freesurfer6`  
  * Pinned Commit SHA: `869ca75f49cd3e799035109819c43cc6a779156e`  
  * **License:** **Creative Commons Attribution-NonCommercial-ShareAlike 3.0 Unported (CC BY-NC-SA 3.0)**.  
    * *Notice:* This derivative dataset is **not** in the public domain. Commercial use is strictly prohibited without separate licensing, and adaptations must be shared under equivalent terms.

---

## 2. Cohort Flow & Demographic Accounting

```
Total ABIDE I Phenotypic Records in PCP Release: N = 1,112
  │
  ├──> Omitted from PCP imaging table: N = 77 participants with FILE_ID == 'no_filename'
  │    (Unassigned structural filenames in upstream PCP release; specific cause unverified)
  │
  └──> Imaged Phenotypic Candidates: N = 1,035 (100% unique SUB_ID and FILE_ID)
        │
        └──> FreeSurfer v6 Derivative Matrix (dfsp-spirit): N = 1,035
              │
              └──> Matched Master Analysis Cohort: N = 1,035
                    ├── ASD Participants: N = 505 (48.8%)
                    └── Typically Developing Controls (TDC): N = 530 (51.2%)
```

### Exact Demographic Breakdown (Recomputed from Dataset)
* **Age Distribution:** 6.47 to 64.00 years (Mean: **16.953804**; Sample SD: **8.001663**; Median: 14.53 years).
  * **Pediatric & Adolescent (< 18.0 years):** **718 participants** (351 ASD, 367 TDC).
  * **Adults ($\ge 18.0$ years):** **317 participants** (154 ASD, 163 TDC).
* **Sex:** **878 coded Male** (`SEX = 1`, 84.8%), **157 coded Female** (`SEX = 2`, 15.2%).
* **Acquisition Centers & Institutions:**
  * **20 Acquisition Labels (`SITE_ID`):** `CALTECH`, `CMU`, `KKI`, `LEUVEN_1`, `LEUVEN_2`, `MAX_MUN`, `NYU`, `OHSU`, `OLIN`, `PITT`, `SBL`, `SDSU`, `STANFORD`, `TRINITY`, `UCLA_1`, `UCLA_2`, `UM_1`, `UM_2`, `USM`, `YALE`.
  * **17 Contributing Institutions (`INSTITUTION_ID`):** Collapsing sibling acquisition labels (`LEUVEN_1/2` $\rightarrow$ `LEUVEN`, `UCLA_1/2` $\rightarrow$ `UCLA`, `UM_1/2` $\rightarrow$ `UM`) yields the 17 contributing institutions of the official ABIDE I release.

---

## 3. Comprehensive Feature Accounting (174 Morphometric Features)

The feature space consists of exactly 174 numerical columns documented in [`feature_manifest_174.csv`](file:///Users/dips/Library/CloudStorage/OneDrive-LordBuddhaEducationFoundation/Working%20Paper/ABIDE_Neurostructural_ML_Proposal/feature_manifest_174.csv):

### A. Cortical Thickness (70 features, mm)
* **Desikan–Killiany Bilateral Parcels (68 features: 34 LH, 34 RH):**
  Regional mean thickness for `bankssts`, `caudalanteriorcingulate`, `caudalmiddlefrontal`, `cuneus`, `entorhinal`, `fusiform`, `inferiorparietal`, `inferiortemporal`, `isthmuscingulate`, `lateraloccipital`, `lateralorbitofrontal`, `lingual`, `medialorbitofrontal`, `middletemporal`, `parahippocampal`, `paracentral`, `parsopercularis`, `parsorbitalis`, `parstriangularis`, `pericalcarine`, `postcentral`, `posteriorcingulate`, `precentral`, `precuneus`, `rostralanteriorcingulate`, `rostralmiddlefrontal`, `superiorfrontal`, `superiorparietal`, `superiortemporal`, `supramarginal`, `frontalpole`, `temporalpole`, `transversetemporal`, `insula`.
* **Hemispheric Mean Thickness (2 features):**
  `lh_MeanThickness_thickness`, `rh_MeanThickness_thickness`.

### B. Cortical Surface Area (70 features, $\text{mm}^2$)
* **Desikan–Killiany Bilateral Parcels (68 features: 34 LH, 34 RH):**
  Corresponding regional surface areas across the 34 bilateral parcels.
* **Hemispheric Total White Surface Area (2 features):**
  `lh_WhiteSurfArea_area`, `rh_WhiteSurfArea_area`.

### C. Subcortical, Ventricular, Cerebellar & Brainstem Segmentations (34 features, $\text{mm}^3$)
* **Subcortical Gray Matter Nuclei (14 features):**
  Bilateral Thalamus Proper, Caudate, Putamen, Pallidum, Hippocampus, Amygdala, and Nucleus Accumbens (`Left-Accumbens-area`, `Right-Accumbens-area`).
* **Ventral Diencephalon (2 features):** `Left-VentralDC`, `Right-VentralDC`.
* **Ventricular, CSF & Choroid Spaces (7 features):**
  `Left-Lateral-Ventricle`, `Right-Lateral-Ventricle`, `Left-Inf-Lat-Vent`, `Right-Inf-Lat-Vent`, `Left-choroid-plexus`, `Right-choroid-plexus`, `CSF`.
* **Cerebellar & Brainstem Compartments (5 features):**
  `Left-Cerebellum-White-Matter`, `Right-Cerebellum-White-Matter`, `Left-Cerebellum-Cortex`, `Right-Cerebellum-Cortex`, `Brain-Stem`.
* **White Matter Hypointensities (4 features, constant zero):**
  `Left-WM-hypointensities`, `Right-WM-hypointensities`, `Left-non-WM-hypointensities`, `Right-non-WM-hypointensities` (all 4 exhibit variance = 0 in this derivative release).
* **Vessel Volumes (2 features):**
  `Left-vessel`, `Right-vessel`.

### D. Global Macrostructural Covariates
* `IntraCranialVol` (Estimated Total Intracranial Volume, eTIV/eICV in $\text{mm}^3$; evaluated in nuisance models).
* `TotalGrayVol` (Total gray matter volume in $\text{mm}^3$; present in tabular dataset, available for planned future models, not included in current benchmark).

### E. Full-Sample L1 Feature Rankings Artifact (`feature_rankings_l1.csv`)
* **Model Configuration:** Unadjusted full-sample L1-penalized Logistic Regression ($C=0.1$, `liblinear`) fit on Age + Sex + 174 FreeSurfer morphometry features.
* **Feature Retention:** **172 retained predictors** (170 brain morphometry features + Age + Sex; `VarianceThreshold(1e-5)` dropped the 4 constant-zero hypointensity labels).
* **Sparsity Breakdown:** Exactly **56 non-zero coefficients** and **116 zero coefficients**.
* **Methodological Framing:** Documented strictly as descriptive conditional model log-odds in an unadjusted exploratory full-sample model, not as the adjusted out-of-fold classifier, validated biomarkers, or causal neurobiology.

---

## 4. Phenotypic Target Accounting

### 1. Categorical Diagnostic Outcome: `ASD_DIAGNOSIS`
* Binary target: `1 = Autism Spectrum Disorder (ASD)` ($N = 505$), `0 = Typically Developing Control (TDC)` ($N = 530$).

### 2. Continuous Symptom Severity Targets (Exact Script Checks)
* **Classic ADOS Total (`ADOS_TOTAL`):**
  * Raw observational sum across communication and reciprocal social interaction domains.
  * Valid non-missing cases ($\ge 0$): **$N = 371$ participants** (**351 ASD**, **20 TDC** [7 TDC scored 0]).
  * Score Distribution: Range: 0 to 22 (Median: 11.0; Mean: **11.210243**; Sample SD: **4.390284**).
* **Gotham Calibrated Severity Score (`ADOS_GOTHAM_SEVERITY`):**
  * Standardized calibrated severity metric (1–10 scale) accounting for age and language module (Gotham et al., 2009).
  * Valid cases (scores 1–10): **$N = 246$ participants** (**236 ASD**, **10 TDC**).
  * Score Distribution: Range: 1 to 10 (Median: 7.0; Mean: **6.813008**; Sample SD: **2.362460**).
