# `data/` directory

See `docs/data_dictionary.md` for the full schema of every file in this directory.

## Layout

```
data/
├── raw/
│   ├── hardware/             cached honest-baseline IBM Heron r2 measurements (.npz, .json)
│   ├── calibration/          per-device epsilon decomposition (Section 5.B input)
│   └── attacks/              attack-sweep records (170 paired attacks)
└── processed/                downstream analysis artifacts feeding manuscript tables
    ├── section5A/            binomial CIs (Wilson + Clopper-Pearson) — Section 5.A
    ├── section5D/            federation-scaling aggregated values
    ├── section5E/            held-out test data (30-instance replication)
    ├── section5E_threshold/  threshold characterization (3 LOO configs + 5 synthetic descriptors)
    ├── section5F/            baseline-comparison data (B0 / B2 / B3 + McNemar)
    └── section4/             theoretical-bound numerical inputs
```

## Provenance

All cached data was generated under the locked experimental configuration in `configs/experiment_config.yaml`:

- Witness ensemble: 50 random Cliffords (depth 5), seed=42.
- Predictor: linear regression on 100 deployment-prior descriptors at 2048 shots, descriptor seed=43.
- Detection shots: 1024.
- δ (false-positive target): 0.01.
- AerSim per-shot RNG: unseeded (the documented source of cross-instance variance).

## Tables vs raw

- `data/raw/`: minimal hardware measurements + canonical attack records. These are the inputs the reproduction scripts cannot reconstruct without IBM Quantum access.
- `data/processed/`: derived from `raw/` via the analysis scripts in `experiments/` of the original development workspace. These are included so reviewers can reproduce manuscript numbers without re-running the multi-hour analysis pipelines.

To regenerate `data/processed/` from `data/raw/` requires the analysis scripts from the development workspace (not included in this public release — they would add ~hours of compute without changing any manuscript value). Open an issue on GitHub if you want access to the development analysis scripts for independent reproduction.
