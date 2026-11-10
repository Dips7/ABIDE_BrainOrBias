# Data Dictionary: ABIDE Neurostructural Dataset
**Project:** Machine Learning Evaluation of Macroscale Neurostructural Morphometry for Autism Spectrum Disorder  
**Reference Dataset:** `abide_freesurfer_tabular_dataset.csv` (SHA-256: `9c84f601fd22a7aaa1780983d42fa884c3ef9d38878a32e465a37bcd42d99b3c`)  
**Feature Count:** 174 FreeSurfer Morphometric Features + 3 Nuisance Covariates + Metadata  
**Total Columns:** 188

---

## 1. Study Identifiers & Clinical Targets

| Column Name | Data Type | Units / Coding | Description |
| :--- | :---: | :--- | :--- |
| `SUB_ID` | Integer | Unique numeric ID | Participant unique identification number (50001–51607). |
| `SITE_ID` | String | Categorical string | Data collection center identifier (17 international institutions, e.g., `NYU`, `UCLA_1`, `PITT`). |
| `DX_GROUP` | Integer | `1 = ASD`, `2 = Control` | Binary diagnostic classification group (Primary ML Target). |
| `DSM_IV_TR` | Integer | 0 = TDC, 1 = Autism, 2 = Asperger, 3 = PDD-NOS | Specific clinical DSM-IV-TR diagnostic subcategory. |

---

## 2. Demographic & Nuisance Covariates

| Column Name | Data Type | Units / Coding | Description |
| :--- | :---: | :--- | :--- |
| `AGE_AT_SCAN` | Float | Years (decimal) | Chronological participant age at time of MRI acquisition (range: 6.5–64.0 years). |
| `SEX` | Integer | `1 = Male`, `2 = Female` | Biological sex of the participant. |
| `IntraCranialVol` | Float | $\text{mm}^3$ | Estimated Total Intracranial Volume (`eTIV`) computed by FreeSurfer. |
| `FIQ` | Float | Standard score | Full-Scale Intelligence Quotient (standardized IQ score; mean 100, SD 15). |
| `VIQ` | Float | Standard score | Verbal Intelligence Quotient. |
| `PIQ` | Float | Standard score | Performance Intelligence Quotient. |
| `HANDEDNESS_CATEGORY` | String | `R`, `L`, `Ambi` | Handedness dominance category. |

---

## 3. Standardized Psychometric Measures

| Column Name | Data Type | Range / Coding | Description |
| :--- | :---: | :--- | :--- |
| `ADOS_TOTAL` | Float | 0–23 | Autism Diagnostic Observation Schedule (generic overall total score). |
| `ADOS_GOTHAM_SEVERITY` | Float | 1–10 | ADOS Gotham Calibrated Severity Score (standardized cross-module autism severity). |
| `ADOS_COMM` | Float | 0–10 | ADOS Communication subscale score. |
| `ADOS_SOCIAL` | Float | 0–14 | ADOS Reciprocal Social Interaction subscale score. |

---

## 4. FreeSurfer Macroscale Morphometry Features (174 Metrics)

Features were extracted using the Preprocessed Connectomes Project (PCP) FreeSurfer v5.1 pipeline from the Desikan-Killiany cortical parcellation and subcortical segmentation:

### A. Cortical Thickness (70 Features; Unit: mm)
- 34 Left Hemisphere regions: `lh_<region>_thickness` (e.g., `lh_bankssts_thickness`, `lh_superiorfrontal_thickness`, `lh_precuneus_thickness`)
- 34 Right Hemisphere regions: `rh_<region>_thickness` (e.g., `rh_bankssts_thickness`, `rh_superiorfrontal_thickness`, `rh_precuneus_thickness`)
- 2 Hemisphere Mean Thickness: `lh_MeanThickness_thickness`, `rh_MeanThickness_thickness`

### B. Cortical Surface Area (70 Features; Unit: $\text{mm}^2$)
- 34 Left Hemisphere regions: `lh_<region>_area` (e.g., `lh_bankssts_area`, `lh_superiorfrontal_area`, `lh_precuneus_area`)
- 34 Right Hemisphere regions: `rh_<region>_area` (e.g., `rh_bankssts_area`, `rh_superiorfrontal_area`, `rh_precuneus_area`)
- 2 Hemisphere Total Surface Area: `lh_WhiteSurfArea_area`, `rh_WhiteSurfArea_area`

### C. Subcortical and Ventricular Volumes (34 Features; Unit: $\text{mm}^3$)
- Bilateral Subcortical Nuclei: Thalamus, Caudate, Putamen, Pallidum, Hippocampus, Amygdala, Accumbens area (`Left-Thalamus-Proper`, `Right-Thalamus-Proper`, `Left-Hippocampus`, `Right-Hippocampus`, `Left-Amygdala`, `Right-Amygdala`, etc.)
- Ventricular Spaces: Lateral Ventricles, Inferior Lateral Ventricles, 3rd Ventricle, 4th Ventricle (`Left-Lateral-Ventricle`, `Right-Lateral-Ventricle`, `3rd-Ventricle`, `4th-Ventricle`)
- Global Structures: Brain Stem (`Brain-Stem`), Total Gray Matter (`TotalGrayVol`), Cortical White Matter (`CorticalWhiteMatterVol`)

