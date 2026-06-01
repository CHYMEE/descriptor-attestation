# Section 4 — theoretical-guarantees numerical extraction

Generated: 2026-05-19T07:17:50.801987+00:00

All values derived from existing artifacts under the locked predictor config (seeds 42 / 43, 100 / 2048 deployment-prior training). Predictor instance regenerated for this extraction (~68s, train_residual = 0.01617).

## Value 1 — Predictor weight matrix norms

`W in R^50x16` (rows = N=50 witnesses, cols = 16 descriptor components).

| Norm | Value |
|---|---:|
| ||W||_2 (spectral / largest singular value) | **5.224022** |
| ||W||_F (Frobenius) | 5.926412 |
| ||W||_inf (induced, max row sum) | 6.710999 |
| ||W||_F / sqrtN (sanity lower bound for ||W||_2) | 0.838121 |

Sanity check ||W||_2 >= ||W||_F / sqrtN satisfied: True.

## Value 2 — Hardware descriptor norms

Loaded from `results/phase2/20260513T023922Z_multi_backend/<backend>/run.npz` (phase 2 anchor, 2026-05-13 calibration).

| Backend | ||d_hw||_2 | ||d_hw||_inf | ||W*d_hw||_inf |
|---|---:|---:|---:|
| ibm_kingston | 1015.2795 | 511.5262 | 0.109446 |
| ibm_fez | 512.7101 | 328.8610 | 0.135109 |
| ibm_marrakesh | 563.5586 | 300.7047 | 0.122429 |

||d_hw||_inf is dominated by T2 components (μs scale ~10^2–10^3); gate and readout errors (10⁻⁴ and 10⁻^2 scale respectively) contribute negligibly to ||*||_inf and ||*||_2.

## Value 3 — Theorem 2 detection lower bound

Predicate: `g(rho, W, d_hw) = (1 - rho) * ||W d_hw||_inf`, and `Pr[reject | uniform_rho attack at rho] >= 1 - exp(-2NS*g^2/4)` with N=50, S=1024.

| Backend | rho | g | Detection lower bound |
|---|---:|---:|---:|
| ibm_kingston | 0.2 | 0.087557 | 1.000000 |
| ibm_kingston | 0.3 | 0.076612 | 1.000000 |
| ibm_kingston | 0.4 | 0.065667 | 1.000000 |
| ibm_kingston | 0.5 | 0.054723 | 1.000000 |
| ibm_fez | 0.2 | 0.108087 | 1.000000 |
| ibm_fez | 0.3 | 0.094576 | 1.000000 |
| ibm_fez | 0.4 | 0.081065 | 1.000000 |
| ibm_fez | 0.5 | 0.067555 | 1.000000 |
| ibm_marrakesh | 0.2 | 0.097943 | 1.000000 |
| ibm_marrakesh | 0.3 | 0.085700 | 1.000000 |
| ibm_marrakesh | 0.4 | 0.073457 | 1.000000 |
| ibm_marrakesh | 0.5 | 0.061214 | 1.000000 |

### Headline cell (Kingston, rho = 0.4)

- Predicted detection lower bound (Theorem 2): **1.000000**
- g = (1 - rho)*||W d_hw||_inf = 0.6 * 0.109446 = 0.065667
- Empirical: `uniform_rho_0.40` at phase 2 anchor has max_dev = 0.17532; B0 flagged = True, B2 flagged = True

## Headline numbers for §4 prose

| Quantity | Value |
|---|---:|
| ||W|| (spectral) | 5.2240 |
| ||d_hw||_inf (Kingston) | 511.5262 |
| ||W*d_hw||_inf (Kingston) | 0.109446 |
| Theorem 2 predicted detection at rho=0.4 (Kingston) | 1.000000 |

## Verification log

- Predictor instance: trained inline at 2026-05-19T07:17:50.801987+00:00, locked config (seeds 42 / 43, 100 deployment-prior descriptors x 2048 train shots).
- Predictor weight matrix shape: (50, 16).
- Norm sanity: ||W||_F / sqrtN = 0.838121 <= ||W||_2 = 5.224022: True.
- Kingston rho=0.4 bound in [0, 1]: True.
- §5.C empirical comparison: see `empirical_comparison_kingston_rho_0p4` block in values.json.
