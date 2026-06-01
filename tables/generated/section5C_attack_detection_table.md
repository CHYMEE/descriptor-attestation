# Section 5.C - Attack-detection rates (per-device-eps baseline)

Wilson 95% CI when n >= 20 AND k not in {0, n}; Clopper-Pearson otherwise.

## phase1_anchor

| Attack family | k/n | Rate | 95% CI | Method |
|---|---|---:|---|---|
| uniform_rho | 0/9 | 0.0000 | [0.0000, 0.3363] | clopper_pearson |
| single_param | 0/12 | 0.0000 | [0.0000, 0.2646] | clopper_pearson |
| two_param | 0/4 | 0.0000 | [0.0000, 0.6024] | clopper_pearson |
| random_direction | 0/60 | 0.0000 | [0.0000, 0.0596] | clopper_pearson |
| **AGGREGATE** | **0/85** | 0.0000 | [0.0000, 0.0425] | clopper_pearson |

## phase2_anchor

| Attack family | k/n | Rate | 95% CI | Method |
|---|---|---:|---|---|
| uniform_rho | 4/9 | 0.4444 | [0.1370, 0.7880] | clopper_pearson |
| single_param | 2/12 | 0.1667 | [0.0209, 0.4841] | clopper_pearson |
| two_param | 1/4 | 0.2500 | [0.0063, 0.8059] | clopper_pearson |
| random_direction | 2/60 | 0.0333 | [0.0092, 0.1136] | wilson |
| **AGGREGATE** | **9/85** | 0.1059 | [0.0567, 0.1891] | wilson |
