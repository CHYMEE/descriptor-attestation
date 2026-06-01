# Section 5.F - Baseline comparison

## Aggregate detection (170 paired attacks: 85 phase 1 + 85 phase 2)

| Baseline | Phase | k/n | Rate | 95% CI | Method |
|---|---|---|---:|---|---|
| B0 | phase1 | 0/85 | 0.0000 | [0.0000, 0.0425] | clopper_pearson |
| B0 | phase2 | 9/85 | 0.1059 | [0.0567, 0.1891] | wilson |
| B2 | phase1 | 2/85 | 0.0235 | [0.0065, 0.0818] | wilson |
| B2 | phase2 | 20/85 | 0.2353 | [0.1578, 0.3357] | wilson |
| B3 | phase1 | 16/85 | 0.1882 | [0.1193, 0.2841] | wilson |
| B3 | phase2 | 16/85 | 0.1882 | [0.1193, 0.2841] | wilson |

## Paired McNemar tests (vs B0)

| Comparison | n11 | n10 | n01 | n00 | discordant | exact McNemar p |
|---|---:|---:|---:|---:|---:|---:|
| B2_vs_B0 | 9 | 0 | 13 | 148 | 13 | 0.000244141 |
| B3_vs_B0 | 3 | 6 | 29 | 132 | 35 | 0.000116842 |

## In-sample completeness on Fez

| Baseline | Margin | Passes in-sample? |
|---|---:|---|
| B0 | +0.00000 | yes |
| B2 | -0.04675 | **no** |
| B3 | +0.00122 | yes |