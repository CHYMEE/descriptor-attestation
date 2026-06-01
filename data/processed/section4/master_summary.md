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

## Value 3 — Soundness condition (threshold-sensitive form)

**The operative soundness condition is threshold-sensitive, not the loose g-only bound used in earlier drafts.** For the FN rate to satisfy `Pr[accept | malicious] <= delta_FN`, the per-witness shot count S must satisfy

```
S * Delta_star^2 >= 2 * ln(1 / delta_FN),    where Delta_star := g_star - r_infty(d_hw) - tau > 0.
```

Here `g_star = (1 - rho) * ||W d_hw||_inf` is the predicted per-witness deviation magnitude (the same `g` reported below for context); `r_infty(d_hw)` is the residual hardware-mismatch term carried in the per-device-eps construction (the saturation floor below which deviations are indistinguishable from honest noise); and `tau` is the operating tolerance the protocol allocates between Hoeffding shot noise and detection margin. The condition is feasible only when `Delta_star > 0`, i.e. when the attack-induced deviation exceeds the residual + tolerance budget — a threshold-sensitivity statement absent from the loose g-only bound.

The g values below are reported as inputs to the corrected condition, **not as standalone evidence of detection certainty**. Recomputing the soundness margin requires per-device `r_infty(d_hw)` and the operating `tau` (deferred to follow-up work).

| Backend | rho | g | Note |
|---|---:|---:|---|
| ibm_kingston | 0.2 | 0.087557 | input to corrected condition |
| ibm_kingston | 0.3 | 0.076612 | input to corrected condition |
| ibm_kingston | 0.4 | 0.065667 | input to corrected condition |
| ibm_kingston | 0.5 | 0.054723 | input to corrected condition |
| ibm_fez | 0.2 | 0.108087 | input to corrected condition |
| ibm_fez | 0.3 | 0.094576 | input to corrected condition |
| ibm_fez | 0.4 | 0.081065 | input to corrected condition |
| ibm_fez | 0.5 | 0.067555 | input to corrected condition |
| ibm_marrakesh | 0.2 | 0.097943 | input to corrected condition |
| ibm_marrakesh | 0.3 | 0.085700 | input to corrected condition |
| ibm_marrakesh | 0.4 | 0.073457 | input to corrected condition |
| ibm_marrakesh | 0.5 | 0.061214 | input to corrected condition |

The "1.000000 detection bound" column previously reported here used the older loose form `1 - exp(-2NS*g^2/4)` and overstated detection certainty by ignoring `r_infty(d_hw)` and `tau`. It has been removed; soundness margins under the corrected condition are deferred to follow-up theoretical work.

### Headline cell (Kingston, rho = 0.4)

- g = (1 - rho) * ||W d_hw||_inf = 0.6 * 0.109446 = 0.065667
- Corrected condition requires `S * Delta_star^2 >= 2 * ln(1 / delta_FN)` with `Delta_star = g_star - r_infty(d_hw) - tau`. With g_star = 0.065667 and S = 1024, the condition is satisfiable for delta_FN = 0.05 only if `r_infty(d_hw) + tau < g_star - sqrt(2 ln(20) / S) = 0.065667 - 0.0764`, i.e. would require `r_infty + tau < -0.0107`, which is infeasible. **The Kingston rho=0.4 attack does not satisfy the corrected sufficient soundness condition at S=1024**; the earlier "1.000000" saturation was an artefact of the loose bound, not a genuine soundness guarantee.
- Empirical: `uniform_rho_0.40` at phase 2 anchor has max_dev = 0.17532; B0 flagged = True, B2 flagged = True. The empirical flag does not imply the sufficient soundness condition holds — it only confirms that under this specific predictor instance and shot RNG the max-deviation crossed the per-device threshold.

## Headline numbers for §4 prose

| Quantity | Value |
|---|---:|
| ||W|| (spectral) | 5.2240 |
| ||d_hw||_inf (Kingston) | 511.5262 |
| ||W*d_hw||_inf (Kingston) | 0.109446 |
| Kingston rho=0.4 g_star (input to corrected soundness condition) | 0.065667 |

## Verification log

- Predictor instance: trained inline at 2026-05-19T07:17:50.801987+00:00, locked config (seeds 42 / 43, 100 deployment-prior descriptors x 2048 train shots).
- Predictor weight matrix shape: (50, 16).
- Norm sanity: ||W||_F / sqrtN = 0.838121 <= ||W||_2 = 5.224022: True.
- Kingston rho=0.4 g_star value: 0.065667 (input to corrected condition; the older `1 - exp(-2NS*g^2/4) = 1.0` saturation has been retracted).
- §5.C empirical comparison: see `empirical_comparison_kingston_rho_0p4` block in values.json.

## Operating-regime soundness condition (canonical form)

For a uniform_rho attack at scale rho on a device with hardware descriptor d_hw, the protocol satisfies `Pr[accept | attack] <= delta_FN` if

  **S * Delta_star^2 >= 2 * ln(1 / delta_FN),    with Delta_star = g_star - r_infty(d_hw) - tau > 0.**

This replaces the earlier loose form `N * S * (g^*)^2 / 4 >= ln(2 / delta_FN)` which (a) was not threshold-sensitive — it did not subtract the residual hardware-mismatch floor `r_infty(d_hw)` or the operating tolerance `tau` from g_star — and (b) generated apparent "exponential headroom" that does not survive the corrected derivation. The corrected condition is the operative one for §4.
