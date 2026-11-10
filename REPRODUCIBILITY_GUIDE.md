# Reproducibility Guide & Execution Reference
**Project:** Machine Learning Evaluation of Macroscale Neurostructural Morphometry for Autism Spectrum Disorder  
**Subproject Directory:** `ABIDE_Neurostructural_ML_Proposal/`  
**Date of Reference:** November 2026  
**Active Python Environment:** Python 3.11.16 (`/Users/dips/.venvs/econometric_hybrid_20261103/bin/python3`)  
**Core Dependencies:** NumPy 2.4.6, SciPy 1.17.1, Scikit-Learn 1.9.1, Pandas 3.0.6, Joblib 1.6.0, Pytest 9.1.1  
**Master Release Inventory:** [`RELEASE_INVENTORY.json`](RELEASE_INVENTORY.json)

---

## 1. Verified Read-Only Audit & Reproduction Commands

All commands below are non-destructive, read-only verification procedures that inspect saved canonical evidence without modifying any locked models, datasets, or simulation streams. Execute these from the `ABIDE_Neurostructural_ML_Proposal` directory.

### Step 1: Independent Post-Run Audit of Preserved Records
Verifies that all 4 canonical benchmark artifacts match their immutable SHA-256 hashes and recalculates the joint 8-check gate decisions directly from the 6,000 preserved Monte Carlo replicates:
```bash
PYTHONPATH=".:vv_audit/obuchowski_validation:vv_audit/method_resolution" \
  /Users/dips/.venvs/econometric_hybrid_20261103/bin/python3 \
  vv_audit/obuchowski_validation/independent_audit.py
```
*Expected Output:*
- Canonical benchmark files: 4/4 match (`abide_freesurfer_tabular_dataset.csv` matches `9c84f601fd22a7aa...`).
- Replicate stream: 6,000 / 6,000 valid records, 0 schema failures, 6,000 unique keys.
- Recalculated Suite Decision: `INCONCLUSIVE` (6 PASS, 2 INCONCLUSIVE, 0 FAIL).
- Sensitivity Analysis: SCEN_04 truth uncertainty bounds coverage at 1390–1391 replicates ($92.67\% - 92.73\%$).

---

### Step 2: Operational Manifest Pre-Flight Verification
Verifies that all runner scripts, simulation configuration, and estimator code match the locked SHA-256 hashes in `operational_runner_manifest.json`:
```bash
PYTHONPATH=".:vv_audit/obuchowski_validation:vv_audit/method_resolution" \
  /Users/dips/.venvs/econometric_hybrid_20261103/bin/python3 \
  vv_audit/obuchowski_validation/VALIDATION_RUNNER.py --validate-only
```
*Expected Output:* `VALIDATE_ONLY: OK` (exit code 0).

---

### Step 3: Run the Full Unit and Safety Test Suite (159 Tests)
Executes all regression, operational hardening, schema, QC, and external validation safety tests:
```bash
/Users/dips/.venvs/econometric_hybrid_20261103/bin/pytest -v
```
*Current test count (verified 2026-11-10 by collection):*

| Test module | Tests |
| :--- | :---: |
| `external_validation/test_external_intake_runner.py` | 52 |
| `external_validation/test_external_validation_pipeline.py` | 18 |
| `qc_workflow/test_qc_workflow.py` | 11 |
| `vv_audit/inconclusive_resolution/test_prospective_m2000_runner.py` | 31 |
| `vv_audit/inconclusive_resolution/candidate_methods/test_candidate_student_t_estimator.py` | 14 |
| `vv_audit/inconclusive_resolution/pilots/test_resolution_pilots.py` | 6 |
| `vv_audit/obuchowski_validation/test_operational_hardening_suite.py` | 11 |
| `vv_audit/obuchowski_validation/test_record_schema.py` | 15 |
| `vv_audit/obuchowski_validation/fixture_gate_test.py` | 1 |
| **Total** | **159** |

On Windows, see [Windows setup](#windows-setup) below: 73 run and pass, and the 86 POSIX-dependent tests are skipped or not collected.

*Historical breakdown (earlier 56-test release, kept for reference):*
- `external_validation/test_external_validation_pipeline.py`: **18 passed** (cryptographic model verification, label-free prediction generation, outcome validation, cluster checks, empty/malformed prerequisite register rejection, mandatory evidence hash checks, legitimate curator/reviewer resolution).
- `qc_workflow/test_qc_workflow.py`: **11 passed** (linkage, Euler log parsing, site-relative CNR MAD thresholds, blinded packets, duplicate rejection, missing image asset flagging, PIL image decoding & corruption rejection, metadata stripping, per-packet image isolation, 0600 key permissions).
- `vv_audit/obuchowski_validation/fixture_gate_test.py`: **1 passed** (gate decision logic verification, 0 warnings).
- `vv_audit/obuchowski_validation/test_operational_hardening_suite.py`: **11 passed** (checkpoint/resume equality, refusal to overwrite, duplicate replicate detection, corrupted line detection, manifest tampering rejection, missing checkpoint metadata rejection, seed dictionary validation).
- `vv_audit/obuchowski_validation/test_record_schema.py`: **15 passed** (status-dependent record schema validations).
*Total: 56 passed in ~3 seconds (0 failures, 0 warnings).*

---

### Step 4: Regenerate Machine-Readable Manuscript Tables
Regenerates all demographic and numerical benchmark tables directly from canonical raw data and saved prediction artifacts:
```bash
/Users/dips/.venvs/econometric_hybrid_20261103/bin/python3 generate_manuscript_tables.py
```
*Generated Deliverables in `manuscript_tables/`:*
- `table1_cohort_demographics.csv` & `.json` ($N=1,035$; 505 ASD, 530 TDC; age $16.95 \pm 8.00$; 84.8% male; FIQ $108.3 \pm 15.0$).
- `table2_benchmark_5fold_cv.csv` & `.json` (Brain L1 pooled OOF AUC = 0.5950, Matched Nuisance = 0.5246, $\Delta\text{AUC} = +0.0704$).
- `table3_loio_cross_validation.csv` & `.json` (17 institutions, Brain L1 mean fold AUC = 0.6128 ± 0.0599).
- `table4_obuchowski_simulation_gate.csv` & `.json` (8 checks, 6 PASS, 2 INCONCLUSIVE, 0 FAIL).
- `table5_truth_sensitivity_scen04.csv` & `.json` (1389 to 1391 covered replicates across 95% truth CI).

---

## Windows setup

The pinned runtime is macOS (`/Users/dips/...`). The `.venv/` folder shipped with the project is a macOS environment holding the older benchmark pins, and it does not work on Windows. To verify the project on Windows, build a separate environment from [`requirements-runtime.txt`](requirements-runtime.txt), which matches the runners' hard-coded version checks (Python 3.11.16, scikit-learn 1.9.1, NumPy 2.4.6, SciPy 1.17.1):

```bash
uv venv .venv-win --python 3.11.16
uv pip install --python .venv-win/Scripts/python.exe -r requirements-runtime.txt
```

Run the test suite (from Git Bash):
```bash
.venv-win/Scripts/python.exe -m pytest -q -rs
```
*Expected on Windows:* `73 passed, 44 skipped`. The two modules `test_prospective_m2000_runner.py` (31 tests) and `test_operational_hardening_suite.py` (11 tests) are not collected.

**Why tests are skipped.** The external intake runner, `VALIDATION_RUNNER.py` and `PROSPECTIVE_M2000_RUNNER.py` are POSIX-only by design. They use `fcntl` locks, `resource` limits, symlink defences and Unix `0600` permissions, and they are hash-locked in the release manifests, so they are not patched for Windows. The root [`conftest.py`](conftest.py) turns a failure into a skip only when its cause is one of those missing POSIX features, and prints the reason with `-rs`. Every other failure is still reported. To run all 159 tests, use WSL, Linux or macOS.

Run the independent audit (Step 1) on Windows. It is read-only and runs fully:
```bash
PYTHONPATH=".;vv_audit/obuchowski_validation;vv_audit/method_resolution" .venv-win/Scripts/python.exe vv_audit/obuchowski_validation/independent_audit.py
```
*Expected:* `ALL AUDIT CHECKS PASSED`. Note the `;` path separator on Windows. Step 2 (`VALIDATION_RUNNER.py --validate-only`) imports `resource` and needs a POSIX host.

---

## 2. Artifact Versioning and Model Objects

The repository maintains an explicit separation between historical benchmark artifacts and deployment-ready pipeline objects:

| Artifact Path | Version Role | Description |
| :--- | :---: | :--- |
| `discovery_pipeline/frozen_models_v2/` | **CURRENT DEPLOYMENT (v2)** | Fold-isolated pipelines (`sklearn.pipeline.Pipeline`) containing imputer, selector, scaler, and L1 classifier. |
| `discovery_pipeline/discovery_lock_manifest_v2.json` | **ACTIVE LOCK (v2)** | Immutable SHA-256 hashes binding all v2 pipeline objects. |
| `discovery_pipeline/frozen_models_v1_superseded/` | **HISTORICAL (v1)** | Superseded models where preprocessing occurred outside cross-validation folds. Retained strictly for audit provenance. |
| `discovery_pipeline/discovery_lock_manifest_v1_superseded.json` | **HISTORICAL LOCK (v1)** | Hashes for superseded v1 models. |
| `vv_audit/obuchowski_validation/run_manifest.json` | **HISTORICAL LOCK** | Pre-run manifest (`FROZEN_PRE_RUN`, `launched=false`) preserved bit-for-bit from original experiment. |
| `vv_audit/obuchowski_validation/operational_runner_manifest.json` | **ACTIVE OPERATIONAL LOCK** | Manifest binding current operational runner code. |

---

## 3. Separated Artifact-Writing Commands (Gated / Restricted)

> [!WARNING]
> Do NOT execute the commands below merely to verify documentation. The locked models in `frozen_models_v2/` and the simulation records in `replicates.jsonl` are already frozen and audited. Running these commands will re-train models or require isolated temporary output directories.

If re-training discovery models in a separate isolated directory:
```bash
# Must specify isolated output directory to avoid overwriting locked production models
PYTHONPATH="." /Users/dips/.venvs/econometric_hybrid_20261103/bin/python3 \
  discovery_pipeline/train_discovery_models.py
```

If testing simulation runs, always pass `--output-dir <temp_dir>` and small `--m-reps` to avoid touching production simulation records:
```bash
PYTHONPATH=".:vv_audit/obuchowski_validation:vv_audit/method_resolution" \
  /Users/dips/.venvs/econometric_hybrid_20261103/bin/python3 \
  vv_audit/obuchowski_validation/VALIDATION_RUNNER.py \
  --run-full --output-dir /tmp/test_sim --m-reps 2 --r-truth 10
```

---

## 4. Licensing & Data Use Terms

- **Source Dataset:** Preprocessed Connectomes Project (PCP) ABIDE I FreeSurfer v6 tabular extraction.
- **License:** Creative Commons Attribution-NonCommercial-ShareAlike 3.0 Unported (CC BY-NC-SA 3.0).
- **Restrictions:** All patient data is strictly de-identified. Commercial exploitation, individual re-identification attempts, or redistribution outside permitted Open Science repositories is strictly prohibited.
