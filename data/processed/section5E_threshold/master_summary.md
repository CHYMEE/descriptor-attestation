# Section 5.E threshold characterization

Generated: 2026-05-20T03:23:08.898796+00:00

Locked config: N=50, S=1024, delta=0.01, eps_Hoeffding = 0.134123.
Honest baselines: `results/phase2/20260513T023922Z_multi_backend/<backend>/run.npz`.
Predictor instances: 30 (predictor_seed = 1..30).

## Experiment 1 — Leave-one-out K=2

| Config | Calibration | Test | Passes | Mean margin | 95% bootstrap CI on mean |
|---|---|---|---:|---:|---|
| C1 | {Kingston, Fez} | Marrakesh | 30/30 | +0.0556 | [+0.0525, +0.0587] |
| C2 | {Kingston, Marrakesh} | Fez | 0/30 | -0.0189 | [-0.0205, -0.0172] |
| C3 | {Fez, Marrakesh} | Kingston | 30/30 | +0.0684 | [+0.0657, +0.0711] |

## Experiment 2 — K=3 calibration, synthetic test descriptors

Calibration set: {Kingston, Fez, Marrakesh}. Test: 5 deployment-prior synthetic descriptors at seeds 100..104.

> **Scope of the K=3 result.** The K=3 result is an *empirical sufficiency statement for the evaluated Heron r2 calibration set*, not a universal lower bound on calibration-set size. It does not assert that K ≥ 3 is formally required, nor that K=3 generalises across architectures or beyond the deployment prior. Out-of-distribution generalisation to a 4th real backend is not tested here (no 4th Heron r2 backend is available on the IBM Quantum Open plan).

| Test desc seed | Passes | Mean margin | 95% bootstrap CI |
|---|---:|---:|---|
| 100 | 30/30 | +0.1117 | [+0.1065, +0.1165] |
| 101 | 30/30 | +0.1076 | [+0.1020, +0.1137] |
| 102 | 30/30 | +0.1082 | [+0.1026, +0.1139] |
| 103 | 30/30 | +0.1064 | [+0.1006, +0.1126] |
| 104 | 30/30 | +0.1072 | [+0.1027, +0.1116] |

**Aggregate (150 cells)**: 150/150 pass, mean margin = +0.1082, 95% bootstrap CI = [+0.1057, +0.1106].

## Sanity check (Config 2 reproduction)

- Config 2 mean: **-0.0189** (existing Section 5.E reported ~-0.0195).
- Config 2 passes: **0/30** (existing Section 5.E reported 0/30).
- Sanity passed: **True**.
