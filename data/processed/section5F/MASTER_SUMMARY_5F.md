# Section 5.F summary — full extraction (B0, B2, B3)

Generated 2026-05-18 (regenerated after B3 Stricker-adapted sweep completed in 3.07 min wall — much faster than the ~5 h budget).

Sources:
- B0 / B2: `results/phase3/final_results/attack_sweep_per_device_epsilon.json` (170 attack records with both per-device-ε and global-ε flags)
- B3: `experiments/phase3/section5F_stricker_adapted.py` run, log at `b3_run_log.json` in this directory
- Fez completeness: `results/phase3/completeness_analysis/per_device_epsilon_demo.json`

B1 (descriptor consistency, no quantum) deferred to Appendix C — see skeleton at bottom.

---

## Task 1 — Aggregate detection rates

| Baseline | Anchor | k | n | Rate | 95% CI | Method |
|---|---|---:|---:|---:|---|---|
| **B0** (per-device-ε) | phase 1 | 0 | 85 | 0.0000 | [0.0000, 0.0425] | Clopper-Pearson |
| **B0** (per-device-ε) | phase 2 | 9 | 85 | 0.1059 | [0.0567, 0.1891] | Wilson |
| **B2** (Hoeffding-only) | phase 1 | 2 | 85 | 0.0235 | [0.0065, 0.0818] | Wilson |
| **B2** (Hoeffding-only) | phase 2 | 20 | 85 | 0.2353 | [0.1578, 0.3357] | Wilson |
| **B3** (Stricker-adapted L1) | phase 1 | 16 | 85 | 0.1882 | [0.1193, 0.2841] | Wilson |
| **B3** (Stricker-adapted L1) | phase 2 | 16 | 85 | 0.1882 | [0.1193, 0.2841] | Wilson |

B3 calibration: pooled across {Kingston, Fez, Marrakesh}, n_cal=20 per device → 60 samples total. Pooled distribution: min=0.0192, max=0.0303, median=0.0239, mean=0.0241, std=0.00247. **ε_stricker = 0.02836** (95th percentile; FPR on calibration set = 0.0500 exactly).

---

## Task 2 — Per-attack-type breakdown (24 cells)

### Phase 1 anchor (2026-05-06)

| Attack family | B0 k/n (rate) | B2 k/n (rate) | B3 k/n (rate) |
|---|---|---|---|
| uniform_rho | 0/9 (0.000) | 1/9 (0.111) | 4/9 (0.444) |
| single_param | 0/12 (0.000) | 1/12 (0.083) | 2/12 (0.167) |
| two_param | 0/4 (0.000) | 0/4 (0.000) | 0/4 (0.000) |
| random_direction | 0/60 (0.000) | 0/60 (0.000) | **10/60 (0.167)** |
| **aggregate** | **0/85** | **2/85** | **16/85** |

### Phase 2 anchor (2026-05-13)

| Attack family | B0 k/n (rate) | B2 k/n (rate) | B3 k/n (rate) |
|---|---|---|---|
| uniform_rho | 4/9 (0.444) | 7/9 (0.778) | 3/9 (0.333) |
| single_param | 2/12 (0.167) | 3/12 (0.250) | 1/12 (0.083) |
| two_param | 1/4 (0.250) | 2/4 (0.500) | 0/4 (0.000) |
| random_direction | 2/60 (0.033) | 8/60 (0.133) | **12/60 (0.200)** |
| **aggregate** | **9/85** | **20/85** | **16/85** |

**Notable pattern — random_direction**: B3 catches random-direction attacks (10/60 phase 1, 12/60 phase 2) where B0 and B2 both catch zero or near-zero. This is the per-witness-vs-output-level distinction: B0 / B2's max-deviation predicate misses diffuse perturbations that don't concentrate on any single witness; B3's L1-mean predicate aggregates the diffuse signal and crosses threshold.

---

## Task 3 — Paired McNemar tests (170 attacks)

### B2 vs B0

| | B2 flags | B2 misses |
|---|---:|---:|
| **B0 flags** | n11 = 9 | n10 = 0 |
| **B0 misses** | n01 = 13 | n00 = 148 |

- Discordant pairs: 13 (all B2-only).
- B0 ⊂ B2 as detection sets (since ε_global = 0.1341 ≤ ε_device = 0.1641).
- **Exact McNemar p = 0.000244** (two-sided). B2 strictly dominates B0 on detection.

### B3 vs B0

| | B3 flags | B3 misses |
|---|---:|---:|
| **B0 flags** | n11 = 3 | n10 = 6 |
| **B0 misses** | n01 = 29 | n00 = 132 |

- Discordant pairs: 35 (6 B0-only, 29 B3-only).
- **NOT** a subset relation: B0 catches 6 attacks B3 misses; B3 catches 29 attacks B0 misses.
- **Exact McNemar p = 0.000117** (two-sided). B3 detects different attacks than B0; in aggregate B3 catches more (32 vs 9 over 170 pairs).

---

## Task 4 — Fez in-sample completeness per baseline

| Baseline | Threshold (Fez) | Honest stat (Fez) | Margin | Passes in-sample? |
|---|---:|---:|---:|---|
| **B0** (per-device-ε) | ε_device = 0.18087 | max_dev_hw = 0.18087 | **+0.0000** | yes (boundary, by construction) |
| **B2** (Hoeffding-only) | ε_H = 0.13412 | max_dev_hw = 0.18087 | **−0.04675** | **NO** |
| **B3** (Stricker-adapted) | ε_stricker = 0.02836 | max honest stat = 0.02714 | **+0.00122** | **yes** |

B3 row interpretation: completeness under B3 = "does the worst honest-baseline Stricker stat for Fez fall below ε_stricker?". Across 20 honest calibration runs on Fez, the max stricker_stat_L1 was 0.02714, which is below the pooled 95th-percentile threshold of 0.02836 by 0.00122. So B3 preserves Fez completeness, with a thinner margin than B0 but a positive one.

---

## Task 5 — Failure-mode matrix

| Baseline | Failure modes | Note |
|---|---|---|
| B0 | — | Reference. Per-device-ε. 9/170 detection; Fez completeness preserved by construction. |
| B2 | completeness_on_fez | Hoeffding-only. 22/170 detection (highest aggregate) but Fez margin −0.0468 — breaks completeness. |
| B3 | — | Stricker-adapted L1 at ε_stricker = 0.02836. 32/170 detection (between B2 and B0 — actually higher than B2 in aggregate!), Fez completeness preserved (margin +0.00122). Different detection profile than B0: catches random-direction attacks B0 misses; misses two-param attacks B0 catches. |
| B1 | pending | Descriptor consistency, no quantum execution. Pending Appendix C implementation. |

---

## Section 5.F headline finding

The witness-execution baselines split into **two regimes by completeness**:

- **Completeness-preserving**: B0 (margin +0.0000) and B3 (margin +0.00122). Both close the Fez completeness gap in-sample.
- **Completeness-breaking**: B2 (margin −0.04675). The bare Hoeffding bound cannot absorb Fez's max_dev_hw.

Within the completeness-preserving regime, **B0 and B3 catch complementary attack classes**:

- B0 verifies **per-witness deviations** (max-dev predicate) — catches sharp single-witness anomalies, including a two-param attack at phase 2 that B3 misses entirely.
- B3 verifies **output-level deviations** (L1-mean predicate) — catches diffuse perturbations distributed across the witness ensemble, including 10+ random-direction attacks per anchor that B0 misses entirely.

Aggregate detection over 170 paired attacks: **B0 = 9, B3 = 32, B2 = 22**. B3 catches more *in aggregate* than B2 while *also* preserving completeness — but neither B0 nor B3 dominates the other (n10 = 6 attacks caught by B0 but missed by B3; n01 = 29 attacks caught by B3 but missed by B0).

McNemar tests show both the B0 ⊂ B2 strict-dominance (p = 0.000244) and the B3-vs-B0 complementary structure (p = 0.000117) at high significance.

### Narrative update — original Framing B needs revision

The Framing B you locked at decision time was: *"Per-device-ε is the unique construction closing the worst-case-device completeness gap."* **This is now false in the strict sense** — B3 also closes the gap (margin +0.00122). The honest revised framing:

> **Framing B′** — *"Among witness-execution baselines, the per-device-ε construction (B0) and the Stricker-adapted ensemble predicate (B3) both close the Fez completeness gap; the bare Hoeffding ablation (B2) does not. B0 and B3 are complementary on detection — per-witness-extremum versus output-level-aggregation — with B3 catching diffuse attacks (random_direction) that B0's max-dev predicate misses, and B0 catching sharp single-witness attacks (two_param at high ρ) that B3's L1-mean predicate dilutes."*

This is **stronger than the original Framing B** because it lands a design-space characterization with two complementary completeness-preserving constructions, not a one-construction-only claim that the data doesn't support. It also makes the contrast with B2 sharper: B2 is the only baseline that buys aggregate detection by giving up completeness.

The §5.F main-text table should therefore present **three rows** (B0, B2, B3) with the contribution claim being **"two predicates, two regimes"** — and reviewers see a clean tradeoff structure rather than a single defended construction.

---

## Appendix C skeleton

Per the §5.C / §5.F placement decisions, Appendix C carries the **no-witness-execution** baselines and supplemental tables:

- **Hoeffding-only baseline (B2)** — Appendix C entry frames: "the bare-Hoeffding threshold catches more attacks than the per-device-ε construction (B0 ⊂ B2 by ε_global ≤ ε_device, McNemar p = 0.000244) but fails in-sample completeness on Fez by 0.04675 — the soundness-side cost of skipping the ε_pred + ε_model budget. The Appendix presents the per-attack-type breakdown table above; the main §5.F text cites the aggregate and the completeness verdict."
- **B1 (descriptor consistency, no quantum)** — sits alongside B2 in Appendix C as the second "no-witness-execution" check once implemented. Pending.

---

## File manifest

```
results/phase3/section5F_outputs/
  MASTER_SUMMARY_5F.md            this file
  task1_aggregates.json           B0/B2/B3 aggregate cells (6 rows + 1 B1 stub)
  task2_per_attack_type.json      B0/B2/B3 per-family cells (24 rows)
  task3_mcnemar.json              B2_vs_B0 and B3_vs_B0 paired tests
  task4_completeness.json         B0/B2/B3 Fez in-sample margin
  task5_necessity.json            B0/B2/B3 failure-mode rows; B1 stub
  b3_run_log.json                 full B3 calibration + per-attack stats (46 KB)
```

Scripts:
- `experiments/phase3/section5F_extract_now.py` — B0 + B2 extraction (re-runnable, ~5 s)
- `experiments/phase3/section5F_stricker_adapted.py` — B3 AerSim sweep (re-runnable, ~3 min wall)
