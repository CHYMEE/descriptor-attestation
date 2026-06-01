# Data dictionary

## Descriptors (16-dimensional)

Every hardware descriptor `d ∈ R^16` represents the noise characteristics of a 4-qubit subsystem. Components:

| Indices | Field | Symbol | Unit | Range (deployment prior) |
|---|---|---|---|---|
| 0..3 | T1 relaxation times | T1 | μs | U(50, 500) |
| 4..7 | T2 dephasing times | T2 | μs | T1 × U(0.1, 1.8), clamped to ≤ 2·T1 |
| 8..11 | Gate-error probabilities | pg | dimensionless | U(1e-4, 8e-4) |
| 12..15 | Readout-error probabilities | pr | dimensionless | U(5e-3, 5e-2) |

Conference-paper convention is preserved: the `NoiseDescriptor.to_vector()` method (in `conference_baseline_snapshot/src/qem/descriptor.py`) concatenates `[T1; T2; pg; pr]` in that order.

## Witness outputs

A "witness" is a random Clifford circuit on 4 qubits at depth 5, paired with a random non-identity 4-qubit Pauli observable. The witness ensemble has 50 elements (`N=50`), generated deterministically from `numpy.random.default_rng(42)`.

The witness output `μ_i ∈ [-1, 1]` is the expectation value of the Pauli observable measured at the end of the Clifford circuit. Honest hardware produces `μ_i = Tr(P_i · N_d(|0⟩⟨0|^4))` (where `N_d` is the noise channel parameterised by descriptor `d`), estimated empirically from `S` measurement shots.

## Attack families

| Family | n attacks | Construction |
|---|---:|---|
| `uniform_rho` | 9 | Scale all 16 descriptor components by single factor ρ ∈ {0.2, 0.3, …, 1.0}. ρ=1.0 is the honest sanity-check case. |
| `single_param` | 12 | Scale exactly one of {T1, T2, gate, readout} (across all 4 qubits) by ρ ∈ {0.2, 0.5, 0.8}; other three fields stay honest. |
| `two_param` | 4 | Jointly scale one coupled pair {(T1, T2), (gate, readout)} by same ρ ∈ {0.5, 0.8}. |
| `random_direction` | 60 | Add fractional per-dimension perturbation `p_i = m · d_true,i · u_i` where `u` is a Gaussian-sampled unit vector in R^16 and m ∈ {0.25, 0.5, 1.0}. Seed=44, 20 directions × 3 magnitudes. |

Per anchor: 9 + 12 + 4 + 60 = **85 attacks**.

All four families apply a post-construction `T2 ≤ 2·T1 - 1e-6` per-qubit clamp before the predictor sees the claimed descriptor.

## Phase anchors

| Anchor | Hardware snapshot date | Anchor device |
|---|---|---|
| `phase1_anchor` | 2026-05-06 | ibm_kingston (cached calibration) |
| `phase2_anchor` | 2026-05-13 | ibm_kingston (cached calibration, 7 days later) |

Both anchors use the same single backend (Kingston), at two different calibration timestamps. The two-anchor design captures real-hardware drift between snapshots.

## File schemas

### `data/raw/hardware/<backend>/run.npz`

NumPy NPZ with five arrays:

- `descriptor_t1_us` — shape (4,), T1 in microseconds.
- `descriptor_t2_us` — shape (4,), T2 in microseconds.
- `descriptor_gate_err` — shape (4,), gate-error probability.
- `descriptor_readout_err` — shape (4,), readout-error probability.
- `measured` — shape (50,), sample-mean Pauli expectation over `S=1024` shots, per witness.

### `data/raw/hardware/<backend>/run.json`

Calibration metadata: anchor timestamp, backend name, witness-set hash, shot count. Contains no IBM job IDs (those were stripped before release).

### `data/raw/calibration/per_device_epsilon_demo.json`

Per-device ε decomposition for Section 5.B. Top-level keys: `experiment`, `purpose`, `timestamp_utc`, `config` (with `epsilon_Hoeffding` and `aersim_mu_shots`), `per_device` (list of 3 entries with `epsilon_pred`, `epsilon_model`, `epsilon_device`, `max_dev_hw`, `passes_at_device_epsilon`).

### `data/raw/attacks/attack_sweep_records.json`

170 attack records (85 per anchor). Per-record fields: `attack_id`, `attack_type`, `max_deviation`, `flagged_per_device_epsilon` (B0 flag), `flagged_global_epsilon` (B2 flag), `attack_undetected_*` (negations).

Aggregate fields per anchor: `n_attacks`, `n_undetected_per_dev_eps`, `n_undetected_global_eps`, `overall_detection_rate_per_dev_eps`, `overall_detection_rate_global_eps`, `by_type` (per-family breakdown).

### `data/processed/section5A/task1_binomial_cis.json`

15 binomial-CI entries (Wilson when n≥20 AND k∉{0,n}, otherwise Clopper-Pearson) covering attack-detection cells + federation Type-I cells. Per entry: `category` (colon-separated key), `n`, `k`, `rate`, `ci_lo`, `ci_hi`, `method`, `source`.

### `data/processed/section5D/task5b_aggregated_scaling.json`

Federation-scaling test for N ∈ {3, 5, 8}. Per N: `n_trials`, `n_device_evaluations`, `k_flagged`, `type_I_rate`, `wilson_upper_ci`, `wilson_lower_ci`, `clopper_pearson_upper_ci`, `clopper_pearson_lower_ci`, `threshold_delta`, `passes_wilson_upper_le_delta`.

### `data/processed/section5D/replication_full_trial_dump.json`

Per-trial detail for the 30-instance federation replication. Used by the §5.D right-panel figure (per-device flag attribution).

### `data/processed/section5E/task4_replicated.json`

30-instance K=2 held-out test on Fez. Top-level: `n_trials`, `n_pass`, `n_fail`, `fail_fraction`, `fail_fraction_wilson_95ci`, `single_instance_reference_margin` (the original single-instance −0.0092 from Task 4), `margin_distribution` (mean, median, std, min, max, values, bootstrap CI).

### `data/processed/section5E_threshold/experiment1_values.json`

3 K=2 LOO configurations × 30 instances = 90 records. Per-record: `config_id` (C1/C2/C3), `calib_backends`, `test_backend`, `predictor_seed`, `eps_model_heldout`, `eps_pred_test`, `max_dev_test`, `eps_device_test`, `margin`, `passes`.

### `data/processed/section5E_threshold/experiment2_values.json`

K=3 calibration × 5 synthetic test descriptors × 30 instances = 150 records. Per-record: `predictor_seed`, `test_desc_seed`, `physical`, `eps_model_K3`, `eps_pred_star`, `max_dev_star`, `eps_device_star`, `margin`, `passes`.

### `data/processed/section5F/task1_aggregates.json`

B0/B2/B3 × phase1/phase2 = 6 aggregate cells. Per-cell: `baseline`, `anchor`, `n`, `k`, `rate`, `ci_95_lo`, `ci_95_hi`, `method`.

### `data/processed/section5F/task3_mcnemar.json`

Two paired-McNemar comparisons (B2 vs B0, B3 vs B0). Per-comparison: `n11_both_flag`, `n10_*_only_flag`, `n01_*_only_flag`, `n00_neither_flag`, `discordant_pairs`, `mcnemar_exact_p_value_two_sided`.

### `data/processed/section5F/task4_completeness.json`

Per-baseline in-sample Fez completeness margin. Per-entry: `baseline`, `device`, `margin`, `passes_in_sample`.
