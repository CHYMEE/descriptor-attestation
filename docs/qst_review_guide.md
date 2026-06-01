# QST reviewer guide

This guide maps every manuscript section, table, and figure to the repository script that regenerates it. **QPU access is not required for any of these reproductions** — all hardware measurements are cached.

## Reproduction in one command

```bash
conda env create -f environment.yml
conda activate descriptor-attestation
bash scripts/reproduce_all.sh
```

Expected wall time: 5–10 minutes (dominated by ~70 s of classical AerSim density-matrix simulation in step 02).

## Manuscript → repository mapping

### Section 3 — Preliminaries

| Object | Source |
|---|---|
| Noise descriptor `d ∈ R^16` (T1, T2, pg, pr per qubit) | `conference_baseline_snapshot/src/qem/descriptor.py::NoiseDescriptor` |
| Witness ensemble (50 random Cliffords + Paulis, seed=42) | `conference_baseline_snapshot/src/qem/witness.py::WitnessSet` |
| Predictor (multi-output linear regression) | `conference_baseline_snapshot/src/qem/predictor.py::WitnessPredictor` |
| Deployment prior `π_synth` | `src/descriptor_attestation/deployment_prior.py::sample_descriptors_deployment` |
| Attestation predicate `max_i\|μ̂_i - P(d)_i\| > ε_device` | `conference_baseline_snapshot/src/qem/attestation.py::detect` |

### Section 4 — Theoretical guarantees

| Manuscript value | Reproduction |
|---|---|
| ε_Hoeffding(N=50, S=1024, δ=0.01) = 0.1341 | `python scripts/03_compute_thresholds.py` (top of stdout) |
| Predictor norms ‖W‖_2 / ‖W‖_F / ‖W‖_∞ | `python scripts/02_train_predictor.py` (writes `data/processed/predictor_norms.json`) |

The Theorem 2 detection lower-bound evaluation tables that appear in §4 (`g(ρ) = (1-ρ)·‖W·d_hw‖_∞`) are not regenerated in scripts 01-08 but the cached values used in the paper are at `data/processed/section4/values.json`.

### Section 5.A — Statistical methodology

The CI conventions (Wilson when n ≥ 20 and k ∉ {0, n}; Clopper-Pearson otherwise) are implemented in `src/descriptor_attestation/statistics.py::binomial_ci`. Unit-tested in `tests/test_statistics.py`.

### Section 5.B — Per-device completeness

| Manuscript table row | Reproduction |
|---|---|
| Kingston ε_pred=0.0357, ε_model=0.0000, ε_device=0.1698, max_dev=0.1193, margin=+0.0506 | `python scripts/03_compute_thresholds.py` |
| Fez 0.0376, 0.0092, 0.1809, 0.1809, +0.0000 | same |
| Marrakesh 0.0386, 0.0000, 0.1727, 0.1233, +0.0495 | same |
| Figure 5.B (per-device completeness dumbbell plot) | `python scripts/08_make_figures.py` → `figures/final/section5B_completeness.{pdf,png}` |

### Section 5.C — Attack detection

| Manuscript value | Reproduction |
|---|---|
| Phase 1 aggregate 0/85 | `python scripts/04_run_attack_analysis.py` |
| Phase 2 aggregate 9/85 | same |
| Phase 2 per-family: uniform_rho 4/9, single_param 2/12, two_param 1/4, random_direction 2/60 | same |
| Figure 5.C (per-family detection with anchor-stratified CIs) | `python scripts/08_make_figures.py` → `figures/final/section5C_attack_detection.{pdf,png}` |

### Section 5.D — Federation scaling

| Manuscript value | Reproduction |
|---|---|
| N=3 k/n=23/90, type-I rate 0.2556, Wilson upper 0.3544 | `python scripts/06_run_scaling_analysis.py` |
| N=5 23/150, 0.1533, 0.2196 | same |
| N=8 23/240, 0.0958, 0.1397 | same |
| All Type-I rates fail δ=0.05 threshold | same (`passes` column = false) |
| Figure 5.D (Type-I vs N + per-device flag attribution) | `python scripts/08_make_figures.py` → `figures/final/section5D_federation_scaling.{pdf,png}` |

### Section 5.E — Held-out calibration (deployment)

| Manuscript value | Reproduction |
|---|---|
| K=2 LOO C1 ({Kingston, Fez} → Marrakesh): 30/30 pass, mean +0.0556 | `python scripts/05_run_heldout_calibration.py` |
| K=2 LOO C2 ({Kingston, Marrakesh} → Fez): 0/30, mean -0.0189, CI [-0.0205, -0.0172] | same |
| K=2 LOO C3 ({Fez, Marrakesh} → Kingston): 30/30, mean +0.0684 | same |
| K=3 synthetic 150/150, mean +0.1082, CI [+0.1057, +0.1106] | same |
| Figure 5.E (held-out margins strip plot) | `python scripts/08_make_figures.py` → `figures/final/section5E_heldout_margins.{pdf,png}` |

### Section 5.F — Baseline comparison

| Manuscript value | Reproduction |
|---|---|
| B0 aggregate 9/170, Fez margin +0.0000, completeness yes | `python scripts/07_run_baselines.py` |
| B2 aggregate 22/170, Fez margin -0.04675, completeness **no** | same |
| B3 aggregate 32/170, Fez margin +0.00122, completeness yes | same |
| B2 vs B0 paired McNemar: n10=0, n01=13, p = 2.4e-4 | same |
| B3 vs B0 paired McNemar: n10=6, n01=29, p = 1.2e-4 | same |
| B0 ∪ B3 union: 38/170 | derived from McNemar (n11 + n10 + n01 = 3 + 6 + 29 = 38) |

## QPU access independence

**No fresh IBM Quantum jobs are needed.** Every cached hardware measurement is provided as `data/raw/hardware/<backend>/run.npz`. The optional folder `scripts/optional_ibm_runs/` (if present) contains scripts that submit fresh jobs to IBM Quantum — these require valid credentials and **are not run by default**. The manuscript figures and tables are reproducible entirely from the cached `data/` directory.

## Tests

Reviewers can verify reproduction integrity via:

```bash
pytest -q
```

The test suite asserts (a) ε_Hoeffding closed-form value, (b) per-device completeness table values within 1e-3 of cached JSON, (c) Wilson + Clopper-Pearson + McNemar primitives, (d) attack-family counts (9/12/4/60), (e) end-to-end smoke test that scripts 03-07 execute cleanly and produce expected output files.
