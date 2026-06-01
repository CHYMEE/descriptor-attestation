# Section 5.B - Per-device completeness table

epsilon_Hoeffding (N=50, S=1024, delta=0.01) = 0.134123 (manuscript: 0.1341)

| Device | eps_pred | eps_model | eps_device | max_dev_hw | Margin | Verdict |
|---|---:|---:|---:|---:|---:|---|
| ibm_kingston | 0.0357 | 0.0000 | 0.1698 | 0.1193 | +0.0506 | Pass |
| ibm_fez | 0.0376 | 0.0092 | 0.1809 | 0.1809 | +0.0000 | Pass |
| ibm_marrakesh | 0.0386 | 0.0000 | 0.1727 | 0.1233 | +0.0495 | Pass |