# Section 5.E - Held-out calibration threshold characterization

## Experiment 1: Leave-one-out K=2

| Config | Calibration | Held-out | Passes | Mean margin | 95% bootstrap CI |
|---|---|---|---:|---:|---|
| C1 | {Kingston, Fez} | Marrakesh | 30/30 | +0.0556 | [+0.0525, +0.0587] |
| C2 | {Kingston, Marrakesh} | Fez | 0/30 | -0.0189 | [-0.0205, -0.0172] |
| C3 | {Fez, Marrakesh} | Kingston | 30/30 | +0.0684 | [+0.0657, +0.0711] |

## Experiment 2: K=3 calibration, 5 synthetic test descriptors x 30 instances

> Scope of the K=3 result: this is an empirical sufficiency statement
> for the evaluated Heron r2 calibration set, not a universal lower
> bound on calibration-set size. K=3 is not stated as a formal
> requirement, and the result does not assert generalisation beyond
> the deployment prior or to non-Heron-r2 architectures.

| Test desc seed | Passes | Mean margin | 95% bootstrap CI |
|---|---:|---:|---|
| 100 | 30/30 | +0.1117 | [+0.1065, +0.1165] |
| 101 | 30/30 | +0.1076 | [+0.1020, +0.1137] |
| 102 | 30/30 | +0.1082 | [+0.1026, +0.1139] |
| 103 | 30/30 | +0.1064 | [+0.1006, +0.1126] |
| 104 | 30/30 | +0.1072 | [+0.1027, +0.1116] |
| **AGGREGATE** | **150/150** | +0.1082 | [+0.1057, +0.1106] |