# `tables/` directory

`tables/generated/` is populated by scripts 03 through 07 (called in sequence by `scripts/reproduce_all.sh`). Each script writes one or more Markdown + CSV files reporting the manuscript-quoted numbers.

| Output | Generator |
|---|---|
| `section5B_completeness_table.{md,csv}` | `scripts/03_compute_thresholds.py` |
| `section5C_attack_detection_table.{md,csv}` | `scripts/04_run_attack_analysis.py` |
| `section5E_threshold_table.{md,csv}` | `scripts/05_run_heldout_calibration.py` |
| `section5D_scaling_table.{md,csv}` | `scripts/06_run_scaling_analysis.py` |
| `section5F_baselines_table.{md,csv}` | `scripts/07_run_baselines.py` |
| `section5F_mcnemar_table.csv` | `scripts/07_run_baselines.py` |

The directory is recreated on each `reproduce_all.sh` run. Both Markdown (reviewer-friendly) and CSV (machine-readable) versions of each table are produced.
