"""
Phase 2 headline experiment: empirical detection rate vs. Hoeffding bound.

Sweeps the claimed/true error ratio (1.0 = honest, < 1.0 = device under-reports
gate and readout errors) and measures the witness-protocol detection rate.

At ratio = 1.0 the empirical false-positive rate must lie at or below delta,
which is the Hoeffding-bound guarantee. As the spoofing magnitude grows, the
detection rate climbs toward 1, demonstrating the protocol's power.
"""
import warnings
warnings.filterwarnings('ignore')

from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

from qem import (
    NoiseDescriptor, QuantumDevice,
    WitnessSet, WitnessPredictor, sample_descriptors, build_training_data,
    hoeffding_bound, detect,
)


SEED = 42
N_WITNESSES = 50
WITNESS_DEPTH = 5
TRAIN_DESCRIPTORS = 50
TRAIN_SHOTS = 1024
DETECT_SHOTS = 1024
DELTA = 0.05
TRIALS_PER_MAGNITUDE = 25
MAGNITUDES = np.array([1.0, 0.9, 0.8, 0.7, 0.6, 0.5, 0.4])  # 1.0 = honest, 0.4 = claims 2.5x better


def main():
    print(f"Generating {N_WITNESSES} witnesses (depth={WITNESS_DEPTH}, seed={SEED}) ...")
    ws = WitnessSet.generate(n=N_WITNESSES, depth=WITNESS_DEPTH, seed=SEED)

    print(f"Training predictor on {TRAIN_DESCRIPTORS} descriptors x {len(ws)} witnesses, {TRAIN_SHOTS} shots ...")
    train_descs = sample_descriptors(TRAIN_DESCRIPTORS, seed=SEED + 1)
    X, Y = build_training_data(train_descs, ws, shots=TRAIN_SHOTS)
    predictor = WitnessPredictor().fit(X, Y)
    train_residual = float(np.abs(predictor.model.predict(X) - Y).mean())
    print(f"  Predictor train residual (mean abs): {train_residual:.4f}")

    eps = hoeffding_bound(N_WITNESSES, DETECT_SHOTS, DELTA)
    print(f"Hoeffding eps (N={N_WITNESSES}, S={DETECT_SHOTS}, delta={DELTA}): {eps:.4f}")

    # Pre-sample test descriptors so each trial gets a fresh device
    n_test = len(MAGNITUDES) * TRIALS_PER_MAGNITUDE
    test_descs = sample_descriptors(n_test, seed=SEED + 2)

    print(f"Sweeping {len(MAGNITUDES)} magnitudes x {TRIALS_PER_MAGNITUDE} trials = {n_test} attestations ...")
    detection_rates = np.zeros(len(MAGNITUDES))
    mean_max_dev = np.zeros(len(MAGNITUDES))

    for mi, mag in enumerate(MAGNITUDES):
        flags = 0
        max_devs = []
        for trial in range(TRIALS_PER_MAGNITUDE):
            true_d = test_descs[mi * TRIALS_PER_MAGNITUDE + trial]
            claimed_vec = true_d.to_vector().copy()
            claimed_vec[8:16] *= mag  # under-report gate (8:12) + readout (12:16) errors
            claimed_d = NoiseDescriptor.from_vector(claimed_vec)

            dev = QuantumDevice(true_d, claimed_d, device_id=f"m{mag:.2f}_t{trial}")
            measured = ws.measure(dev, shots=DETECT_SHOTS)
            res = detect(claimed_d, measured, predictor, shots=DETECT_SHOTS, delta=DELTA)
            flags += int(res.flagged)
            max_devs.append(res.max_deviation)

        detection_rates[mi] = flags / TRIALS_PER_MAGNITUDE
        mean_max_dev[mi] = float(np.mean(max_devs))
        print(f"  ratio={mag:.2f}: detection={detection_rates[mi]:.2f} ({flags}/{TRIALS_PER_MAGNITUDE}),  mean max-dev={mean_max_dev[mi]:.4f}")

    # Outputs
    out_dir = Path(__file__).parent.parent / "results" / "phase2"
    out_dir.mkdir(parents=True, exist_ok=True)

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 4.5))

    ax1.plot(MAGNITUDES, detection_rates, 'o-', color='C0', linewidth=2, markersize=8, label='Empirical detection rate')
    ax1.axhline(DELTA, color='C3', linestyle='--', label=f'Hoeffding FPR bound (δ={DELTA})')
    ax1.set_xlabel('Claimed / true error ratio  (1.0 = honest)')
    ax1.set_ylabel('Detection rate')
    ax1.set_title(f'Witness Protocol Detection (N={N_WITNESSES}, S={DETECT_SHOTS})')
    ax1.invert_xaxis()
    ax1.set_ylim(-0.02, 1.05)
    ax1.legend(loc='center right')
    ax1.grid(True, alpha=0.3)

    ax2.plot(MAGNITUDES, mean_max_dev, 's-', color='C2', linewidth=2, markersize=7, label='Mean max-deviation')
    ax2.axhline(eps, color='C3', linestyle='--', label=f'Hoeffding ε = {eps:.3f}')
    ax2.set_xlabel('Claimed / true error ratio  (1.0 = honest)')
    ax2.set_ylabel('Max-deviation across witnesses')
    ax2.set_title('Test Statistic vs. Threshold')
    ax2.invert_xaxis()
    ax2.legend(loc='upper right')
    ax2.grid(True, alpha=0.3)

    fig.tight_layout()
    plot_path = out_dir / "witness_detection.png"
    fig.savefig(plot_path, dpi=150)
    print(f"\nSaved plot: {plot_path}")

    np.savez(
        out_dir / "witness_detection.npz",
        magnitudes=MAGNITUDES,
        detection_rates=detection_rates,
        mean_max_dev=mean_max_dev,
        epsilon=eps,
        delta=DELTA,
        n_witnesses=N_WITNESSES,
        detect_shots=DETECT_SHOTS,
        trials=TRIALS_PER_MAGNITUDE,
        train_residual=train_residual,
    )
    print(f"Saved data: {out_dir / 'witness_detection.npz'}")


if __name__ == "__main__":
    main()
