"""
ABIDE I FreeSurfer Tabular Dataset Builder (Audited & Pinned Version)
Author: Neuroimaging & Machine Learning Research Team
Date: November 2026

Description:
    Downloads phenotypic data from the Preprocessed Connectomes Project (PCP)
    and FreeSurfer v6 aggregated structural metrics from dfsp-spirit/abide_preproc_smri_freesurfer6.
    
    Provenance & Licensing:
    - Phenotypic Data: ABIDE I Consortium via PCP (https://github.com/preprocessed-connectomes-project/abide)
      Commit Pinned: fda1ec5d3f53eb97d94352e779f37c3ce46caee1
    - FreeSurfer v6 Derivatives: Curated by dfsp-spirit (https://github.com/dfsp-spirit/abide_preproc_smri_freesurfer6)
      Commit Pinned: 869ca75f49cd3e799035109819c43cc6a779156e
      License: Creative Commons Attribution-NonCommercial-ShareAlike 3.0 Unported (CC BY-NC-SA 3.0).
               Not public domain. Commercial use prohibited without separate licensing.
"""

import os
import hashlib
import pandas as pd
import numpy as np

DATA_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_FILE = os.path.join(DATA_DIR, "abide_freesurfer_tabular_dataset.csv")

# Pinned commit URLs for exact reproducibility
PCP_COMMIT = "fda1ec5d3f53eb97d94352e779f37c3ce46caee1"
FS_COMMIT = "869ca75f49cd3e799035109819c43cc6a779156e"

PHENO_URL = f"https://raw.githubusercontent.com/preprocessed-connectomes-project/abide/{PCP_COMMIT}/Phenotypic_V1_0b_preprocessed1.csv"
BASE_FS_URL = f"https://raw.githubusercontent.com/dfsp-spirit/abide_preproc_smri_freesurfer6/{FS_COMMIT}/stats/"

FS_FILES = {
    "lh_thickness": BASE_FS_URL + "lh.aparc_table_thickness.tsv",
    "rh_thickness": BASE_FS_URL + "rh.aparc_table_thickness.tsv",
    "lh_area": BASE_FS_URL + "lh.aparc_table_area.tsv",
    "rh_area": BASE_FS_URL + "rh.aparc_table_area.tsv",
    "aseg": BASE_FS_URL + "aseg_table.tsv"
}


def build_and_validate_dataset():
    print("=" * 70)
    print("ABIDE I Tabular Dataset Construction & Validation Pipeline")
    print("=" * 70)

    # 1. Ingest Phenotypic Data
    print(f"Step 1: Downloading phenotypic data (Commit {PCP_COMMIT[:8]})...")
    df_pheno_raw = pd.read_csv(PHENO_URL)
    n_pheno_raw = len(df_pheno_raw)
    print(f"  Loaded {n_pheno_raw} raw phenotypic rows.")
    
    # Assertions on phenotypic table
    assert df_pheno_raw["SUB_ID"].is_unique, "Assertion Error: SUB_ID is not unique in phenotypic data!"
    
    # Audit FILE_ID: 77 participants have unassigned filenames in the PCP release (coded as 'no_filename')
    unscanned_mask = df_pheno_raw["FILE_ID"] == "no_filename"
    n_unscanned = unscanned_mask.sum()
    print(f"  Participants with unassigned filenames in PCP release (FILE_ID == 'no_filename'): {n_unscanned}")
    
    df_pheno = df_pheno_raw[~unscanned_mask].copy().reset_index(drop=True)
    assert df_pheno["FILE_ID"].is_unique, "Assertion Error: FILE_ID is not unique after filtering 'no_filename'!"
    assert len(df_pheno) == 1035, f"Expected 1,035 imaged phenotypic rows, got {len(df_pheno)}!"
    
    # Validate DX_GROUP values
    valid_dx = {1, 2}
    actual_dx = set(df_pheno["DX_GROUP"].unique())
    assert actual_dx.issubset(valid_dx), f"Unexpected DX_GROUP labels found: {actual_dx - valid_dx}"

    # 2. Ingest FreeSurfer v6 Derivatives
    print(f"Step 2: Downloading FreeSurfer v6 aggregated tables (Commit {FS_COMMIT[:8]})...")
    fs_tables = {}
    for name, url in FS_FILES.items():
        print(f"  Fetching {name}...")
        df_tbl = pd.read_csv(url, sep="\t")
        subj_col = df_tbl.columns[0]
        df_tbl = df_tbl.rename(columns={subj_col: "FILE_ID"})
        assert df_tbl["FILE_ID"].is_unique, f"Assertion Error: FILE_ID not unique in {name}!"
        fs_tables[name] = df_tbl

    # 3. Merge FreeSurfer tables
    print("Step 3: Merging FreeSurfer tables (thickness, area, subcortex)...")
    df_fs = fs_tables["lh_thickness"]
    for name in ["rh_thickness", "lh_area", "rh_area", "aseg"]:
        pre_len = len(df_fs)
        df_fs = pd.merge(df_fs, fs_tables[name], on="FILE_ID", how="inner")
        assert len(df_fs) == pre_len, f"Row count changed during FreeSurfer merge of {name}!"

    n_fs_subjects = len(df_fs)
    print(f"  FreeSurfer matrix assembled: {n_fs_subjects} subjects with complete reconstruction.")

    # 4. Merge Phenotypic with FreeSurfer Derivatives
    print("Step 4: Joining phenotypic data with FreeSurfer derivatives on FILE_ID...")
    merged_df = pd.merge(df_pheno, df_fs, on="FILE_ID", how="inner")
    n_merged = len(merged_df)
    
    # Cohort Flow Accounting
    dropped_count = n_pheno_raw - n_merged
    print("\n--- Cohort Flow & Attribution Accounting ---")
    print(f"  Original ABIDE I PCP Phenotypic Records: {n_pheno_raw}")
    print(f"  FreeSurfer v6 Reconstructed Subjects:   {n_fs_subjects}")
    print(f"  Matched & Validated Analysis Cohort:    {n_merged}")
    print(f"  Unassigned in PCP / Omitted upstream:   {dropped_count} (unassigned FILE_ID in upstream PCP phenotypic table)")
    assert n_merged == 1035, f"Expected 1,035 matched subjects, got {n_merged}!"

    # 5. Diagnostic Outcome Mapping & Verification
    # Explicit mapping: DX_GROUP 1 -> ASD (1), DX_GROUP 2 -> TDC (0)
    merged_df["ASD_DIAGNOSIS"] = merged_df["DX_GROUP"].map({1: 1, 2: 0})
    assert merged_df["ASD_DIAGNOSIS"].notnull().all(), "Null values produced during ASD_DIAGNOSIS mapping!"
    
    n_asd = (merged_df["ASD_DIAGNOSIS"] == 1).sum()
    n_tdc = (merged_df["ASD_DIAGNOSIS"] == 0).sum()
    print(f"  ASD Participants:  {n_asd}")
    print(f"  TDC Participants:  {n_tdc}")

    # 6. Demographic Auditing
    ages = merged_df["AGE_AT_SCAN"]
    n_pediatric = (ages < 18).sum()
    n_adult = (ages >= 18).sum()
    print(f"\n--- Age Demographic Breakdown ---")
    print(f"  Age Range:       {ages.min():.2f} to {ages.max():.2f} years (Median: {ages.median():.2f})")
    print(f"  Pediatric (<18): {n_pediatric} participants")
    print(f"  Adults (>=18):   {n_adult} participants")

    # 7. Site Auditing
    n_sites = merged_df["SITE_ID"].nunique()
    print(f"\n--- Acquisition Site Breakdown ---")
    print(f"  Unique Acquisition Labels (SITE_ID): {n_sites}")
    print(f"  Site Labels: {sorted(merged_df['SITE_ID'].unique().tolist())}")

    # Save to CSV
    merged_df.to_csv(OUTPUT_FILE, index=False)
    
    # Compute SHA-256 Checksum
    with open(OUTPUT_FILE, "rb") as f:
        sha256_hash = hashlib.sha256(f.read()).hexdigest()

    print("\n" + "=" * 70)
    print(f"Dataset successfully built and validated: {OUTPUT_FILE}")
    print(f"SHA-256 Checksum: {sha256_hash}")
    print("=" * 70)
    
    return merged_df, sha256_hash


if __name__ == "__main__":
    build_and_validate_dataset()
