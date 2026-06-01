#!/usr/bin/env bash
# Reproduce the manuscript tables and figures from cached data.
#
# Prerequisite: `conda env create -f environment.yml && conda activate descriptor-attestation`
#   (or `pip install -r requirements.txt`).
#
# Expected wall time:
#   Scripts 01, 03-08: < 5 minutes total (read cached JSONs / npz only).
#   Script 02 (predictor training): ~60-70 seconds (AerSim density-matrix).
#   Figure scripts (08): ~30 seconds total.

set -euo pipefail

cd "$(dirname "${BASH_SOURCE[0]}")/.."
ROOT=$(pwd)
echo "Reproducing in: $ROOT"
echo

echo "===== 01: Generate witnesses ====="
python scripts/01_generate_witnesses.py
echo

echo "===== 02: Train predictor (~70s) ====="
python -W ignore scripts/02_train_predictor.py
echo

echo "===== 03: Compute thresholds (Section 5.B) ====="
python scripts/03_compute_thresholds.py
echo

echo "===== 04: Attack analysis (Section 5.C) ====="
python scripts/04_run_attack_analysis.py
echo

echo "===== 05: Held-out calibration (Section 5.E) ====="
python scripts/05_run_heldout_calibration.py
echo

echo "===== 06: Federation scaling (Section 5.D) ====="
python scripts/06_run_scaling_analysis.py
echo

echo "===== 07: Baselines (Section 5.F) ====="
python scripts/07_run_baselines.py
echo

echo "===== 08: Regenerate figures ====="
python scripts/08_make_figures.py
echo

echo "===== DONE ====="
echo "Tables:  $(ls tables/generated/ 2>/dev/null | wc -l) files in tables/generated/"
echo "Figures: $(ls figures/final/ 2>/dev/null | wc -l) files in figures/final/"
