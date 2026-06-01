# Reproducibility guide

This document gives step-by-step instructions for reproducing every numerical claim in the manuscript from cached data.

## Software environment

Tested with:

- Python 3.13.5
- numpy 2.x, scipy 1.13+, scikit-learn 1.5+, matplotlib 3.9+
- qiskit 2.x, qiskit-aer 0.17+
- pytest 8.x

Install via conda (recommended):

```bash
conda env create -f environment.yml
conda activate descriptor-attestation
```

Or pip:

```bash
pip install -r requirements.txt
```

## Locked random seeds

| Seed name | Value | Purpose |
|---|---:|---|
| `witness.seed` | 42 | Witness ensemble construction (random Cliffords + Pauli observables) |
| `predictor.desc_sampling_seed` | 43 | Training descriptors sampled from deployment prior |
| Bootstrap (Pearson r) | 42 | Section 5.A CIs |
| Bootstrap (RMSE) | 43 | Section 5.A CIs |
| Bootstrap (ε_pred) | 44 | Section 5.A CIs |
| Random-direction attacks | 44 | Direction sampling |
| Bootstrap (paired diff) | 45 | Section 5.A CIs |
| Bootstrap (margin mean) | 46 | Section 5.E / threshold-characterization CIs |
| Synthetic test descriptors | 100, 101, 102, 103, 104 | Section 5.E Experiment 2 |
| Jitter for strip plot | 46 | Section 5.E Figure 4 |
| Predictor instance IDs | 1..30 | Held-out test + threshold characterization |

All other randomness comes from `qiskit-aer` per-shot RNG which is **intentionally unseeded** in `QuantumDevice.run_circuit`. This is the documented variance source for the 30-instance replications in Section 5.A / 5.E.

## One-command reproduction

```bash
bash scripts/reproduce_all.sh
```

Expected wall time: **~5–10 minutes**, dominated by ~70 s of AerSim density-matrix simulation in script `02_train_predictor.py`. Scripts 03–07 each take < 1 s (cached-JSON reads only).

## Expected outputs and tolerances

| Manuscript value | Reproduced by | Expected | Tolerance |
|---|---|---|---|
| ε_Hoeffding(50, 1024, 0.01) | `03_compute_thresholds.py` | 0.1341 | 1e-9 |
| Kingston eps_pred | `03_compute_thresholds.py` | 0.0357 | 1e-3 |
| Kingston eps_device | `03_compute_thresholds.py` | 0.1698 | 1e-3 |
| Kingston max_dev_hw | `03_compute_thresholds.py` | 0.1193 | 1e-3 |
| Kingston margin | `03_compute_thresholds.py` | +0.0506 | 1e-3 |
| Fez eps_pred / eps_model / eps_device / max_dev_hw / margin | `03_compute_thresholds.py` | 0.0376 / 0.0092 / 0.1809 / 0.1809 / +0.0000 | 1e-3 |
| Marrakesh eps_pred / eps_model / eps_device / max_dev_hw / margin | `03_compute_thresholds.py` | 0.0386 / 0.0000 / 0.1727 / 0.1233 / +0.0495 | 1e-3 |
| Attack detection phase 1 aggregate | `04_run_attack_analysis.py` | 0/85 | exact |
| Attack detection phase 2 aggregate | `04_run_attack_analysis.py` | 9/85 | exact |
| Phase 2 uniform_rho / single_param / two_param / random_direction | `04_run_attack_analysis.py` | 4/9 / 2/12 / 1/4 / 2/60 | exact |
| Federation Type-I at N=3 | `06_run_scaling_analysis.py` | k=23/n=90, rate 0.2556, Wilson upper 0.3544 | 1e-4 |
| Federation Type-I at N=5 | `06_run_scaling_analysis.py` | 23/150, 0.1533, 0.2196 | 1e-4 |
| Federation Type-I at N=8 | `06_run_scaling_analysis.py` | 23/240, 0.0958, 0.1397 | 1e-4 |
| Held-out K=2 C1 (Marrakesh held) | `05_run_heldout_calibration.py` | 30/30 pass, mean +0.0556 | 1e-3 |
| Held-out K=2 C2 (Fez held) | `05_run_heldout_calibration.py` | 0/30 pass, mean -0.0189, CI [-0.0205, -0.0172] | 1e-3 |
| Held-out K=2 C3 (Kingston held) | `05_run_heldout_calibration.py` | 30/30 pass, mean +0.0684 | 1e-3 |
| Held-out K=3 synthetic aggregate (empirical sufficiency, not a universal K≥3 condition; see scope note below) | `05_run_heldout_calibration.py` | 150/150 pass, mean +0.1082, CI [+0.1057, +0.1106] | 1e-3 |
| B0 aggregate (170 attacks) | `07_run_baselines.py` | 9/170 | exact |
| B2 aggregate | `07_run_baselines.py` | 22/170 | exact |
| B3 aggregate | `07_run_baselines.py` | 32/170 | exact |
| Fez completeness B0 / B2 / B3 | `07_run_baselines.py` | +0.00000 / −0.04675 / +0.00122 | 1e-3 |
| McNemar B2 vs B0 | `07_run_baselines.py` | p = 2.44e-4 | 1e-5 |
| McNemar B3 vs B0 | `07_run_baselines.py` | p = 1.17e-4 | 1e-5 |
| Figures 5.B / 5.C / 5.D / 5.E | `08_make_figures.py` | PDF + PNG in `figures/final/` | n/a |

## Scope of the K=3 result

The Section 5.E Experiment 2 K=3 result (150/150 pass, mean margin +0.1082) is reported as an **empirical sufficiency statement for the evaluated Heron r2 calibration set**, not as a universal lower bound on calibration-set size. The repository does not assert that K ≥ 3 is a formal requirement of the protocol, nor that the K=3 result generalises across architectures or beyond the deployment prior. A 4th real-backend out-of-distribution test is not in scope (no 4th Heron r2 backend is available on the IBM Quantum Open plan).

## Section 4 operating-regime soundness condition

The repository uses the threshold-sensitive form of the operating-regime soundness condition:

```
S * Delta_star^2 >= 2 * ln(1 / delta_FN),    Delta_star = g_star - r_infty(d_hw) - tau > 0.
```

Older drafts that quoted `N * S * (g^*)^2 / 4` style bounds — and claims of "exponential headroom" derived from them — are superseded by the threshold-sensitive form. The cached `data/processed/section4/master_summary.md` reports `g_star` values per backend × rho as inputs to the corrected condition; the bound column previously labelled "1.000000 detection lower bound" has been retracted.

## Variance notes

- Script `02_train_predictor.py` retrains the predictor against the deployment prior with AerSim per-shot RNG **unseeded**. The trained-weight values vary slightly across runs (the documented source of per-instance variance reported in Section 5.A). The norm `‖W‖_2` reported by Section 4 is ~5.22 with ~5% across-instance variance.
- Tests in `tests/test_thresholds.py` and `tests/test_attacks.py` validate against **cached** data with exact comparisons; tests in `tests/test_statistics.py` validate closed-form CI / McNemar values.

## Hardware

Reproduction does not require IBM Quantum access. Optional fresh-run scripts (in `scripts/optional_ibm_runs/`, if populated) require:

- An IBM Quantum account (Open plan suffices for ≤ 156-qubit Heron r2 backends).
- Saved credentials via `QiskitRuntimeService.save_account(...)`.
- ~15 s of QPU per 50-witness ensemble at 1024 shots per device (per the empirical Heron r2 cost anchor).

## Troubleshooting

- **`ModuleNotFoundError: No module named 'qem'`** — the `descriptor_attestation` package wires `conference_baseline_snapshot/src/` onto `sys.path` at import time. Make sure you ran `pip install -e .` from the repo root, OR import via `import sys; sys.path.insert(0, "src"); from descriptor_attestation import ...`.
- **AerSim Unicode warnings about `u1`, `u2`, `u3` instruction errors** — harmless artifact of how qiskit-aer attaches per-gate noise to deprecated U gates. Filter with `python -W ignore`.
- **Figure script writes to `figures/` not `figures/final/`** — the figure-source scripts under `figures/source/` write to `PROJECT_ROOT / "figures" / "final"`. If you copied a figure script out of context, the path resolution changes.
- **Predictor training timeout** — AerSim density-matrix at 4 qubits, depth 5, 2048 shots × 100 descriptors should take ~70 s. If much longer, check `qiskit-aer` version (0.17+ required).
