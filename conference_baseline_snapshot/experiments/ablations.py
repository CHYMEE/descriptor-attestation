"""
Ablation studies for the Witness Protocol.

Three panels in one figure, sweeping one knob at a time and holding the others
fixed at the headline configuration. Each ablation point reports two metrics:
  - empirical false-positive rate (honest device, claimed = true)
  - detection rate at 3x noise inflation (liar's true gate+readout = 3x claimed)

Headline config (held fixed except for the swept axis):
  witness depth = 5,  N_witnesses = 50,  detect shots = 1024,
  100 train descriptors, 2048 train shots,  delta = 0.05,  30 trials per point.
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
    detect,
)


SEED = 42
N_QUBITS = 4
TRAIN_DESCRIPTORS = 100
TRAIN_SHOTS = 2048
DELTA = 0.05
TRIALS = 30
INFLATION = 3.0
MAX_ERROR_RATE = 0.5

DEFAULT_DEPTH = 5
DEFAULT_N = 50
DEFAULT_SHOTS = 1024

DEPTHS = [2, 5, 10]
N_VALUES = [25, 50, 100]
SHOT_VALUES = [256, 512, 1024, 2048, 4096]


def evaluate_point(witness_set, predictor, detect_shots, n_trials, descs_iter):
    """Run TRIALS honest + TRIALS liar attestations; return (fpr, detection_rate)."""
    honest_flags = 0
    liar_flags = 0
    for _ in range(n_trials):
        d_honest = next(descs_iter)
        # honest: claim == true
        honest_dev = QuantumDevice(d_honest, d_honest, device_id="h")
        honest_meas = witness_set.measure(honest_dev, shots=detect_shots)
        if detect(d_honest, honest_meas, predictor, shots=detect_shots, delta=DELTA).flagged:
            honest_flags += 1

        # liar: claim sampled from prior; true gate+readout inflated
        d_claim = next(descs_iter)
        liar_true_vec = d_claim.to_vector().copy()
        liar_true_vec[8:16] = np.minimum(liar_true_vec[8:16] * INFLATION, MAX_ERROR_RATE)
        d_liar_true = NoiseDescriptor.from_vector(liar_true_vec)
        liar_dev = QuantumDevice(d_liar_true, d_claim, device_id="l")
        liar_meas = witness_set.measure(liar_dev, shots=detect_shots)
        if detect(d_claim, liar_meas, predictor, shots=detect_shots, delta=DELTA).flagged:
            liar_flags += 1

    return honest_flags / n_trials, liar_flags / n_trials


def run_ablation_axis(name, values, get_witnesses, get_detect_shots, train_seed_offset, descs_seed_offset):
    """For each value, build witness set, train predictor, evaluate (fpr, detection_rate)."""
    fprs = np.zeros(len(values))
    detections = np.zeros(len(values))
    for i, v in enumerate(values):
        ws = get_witnesses(v)
        train_descs = sample_descriptors(TRAIN_DESCRIPTORS, seed=SEED + 100 * train_seed_offset + i)
        X, Y = build_training_data(train_descs, ws, shots=TRAIN_SHOTS)
        predictor = WitnessPredictor().fit(X, Y)
        train_residual = float(np.abs(predictor.model.predict(X) - Y).mean())

        descs = iter(sample_descriptors(2 * TRIALS, seed=SEED + 200 * descs_seed_offset + i))
        fpr, det = evaluate_point(ws, predictor, get_detect_shots(v), TRIALS, descs)
        fprs[i] = fpr
        detections[i] = det
        print(f"  {name}={v}: train_residual={train_residual:.4f},  FPR(honest)={fpr:.3f},  detection(3x)={det:.3f}")
    return fprs, detections


def main():
    print("[Ablation studies]")
    print(f"Common config: TRAIN_DESCRIPTORS={TRAIN_DESCRIPTORS}, TRAIN_SHOTS={TRAIN_SHOTS}, "
          f"TRIALS={TRIALS}, INFLATION={INFLATION}x")

    print("\nAblation 1/3: witness circuit depth (N=50, shots=1024) ...")
    depth_fprs, depth_dets = run_ablation_axis(
        "depth", DEPTHS,
        get_witnesses=lambda d: WitnessSet.generate(n=DEFAULT_N, depth=d, seed=SEED),
        get_detect_shots=lambda d: DEFAULT_SHOTS,
        train_seed_offset=1, descs_seed_offset=1,
    )

    print("\nAblation 2/3: number of witnesses (depth=5, shots=1024) ...")
    n_fprs, n_dets = run_ablation_axis(
        "N", N_VALUES,
        get_witnesses=lambda n: WitnessSet.generate(n=n, depth=DEFAULT_DEPTH, seed=SEED),
        get_detect_shots=lambda n: DEFAULT_SHOTS,
        train_seed_offset=2, descs_seed_offset=2,
    )

    print("\nAblation 3/3: detection shots (depth=5, N=50; predictor trained once) ...")
    ws_fixed = WitnessSet.generate(n=DEFAULT_N, depth=DEFAULT_DEPTH, seed=SEED)
    train_descs = sample_descriptors(TRAIN_DESCRIPTORS, seed=SEED + 301)
    X, Y = build_training_data(train_descs, ws_fixed, shots=TRAIN_SHOTS)
    predictor = WitnessPredictor().fit(X, Y)
    train_residual = float(np.abs(predictor.model.predict(X) - Y).mean())
    print(f"  shared predictor train_residual = {train_residual:.4f}")
    shot_fprs = np.zeros(len(SHOT_VALUES))
    shot_dets = np.zeros(len(SHOT_VALUES))
    for i, s in enumerate(SHOT_VALUES):
        descs = iter(sample_descriptors(2 * TRIALS, seed=SEED + 400 + i))
        fpr, det = evaluate_point(ws_fixed, predictor, s, TRIALS, descs)
        shot_fprs[i] = fpr
        shot_dets[i] = det
        print(f"  shots={s}: FPR(honest)={fpr:.3f},  detection(3x)={det:.3f}")

    out_dir = Path(__file__).parent.parent / "results" / "ablations"
    out_dir.mkdir(parents=True, exist_ok=True)

    fig, axes = plt.subplots(1, 3, figsize=(15, 4.5))
    panel_data = [
        ("Witness circuit depth", DEPTHS, depth_fprs, depth_dets, axes[0]),
        ("Number of witnesses N", N_VALUES, n_fprs, n_dets, axes[1]),
        ("Detection shots S", SHOT_VALUES, shot_fprs, shot_dets, axes[2]),
    ]
    for title, xs, fprs, dets, ax in panel_data:
        ax.plot(xs, fprs, 'o-', color='C3', linewidth=2, markersize=8, label='FPR (honest)')
        ax.plot(xs, dets, 's-', color='C0', linewidth=2, markersize=8, label=f'Detection rate ({INFLATION:.0f}x liar)')
        ax.axhline(DELTA, color='gray', linestyle=':', label=f'δ={DELTA}')
        ax.set_xlabel(title)
        ax.set_ylabel('Rate')
        ax.set_title(f'Ablation: {title}')
        ax.set_ylim(-0.02, 1.05)
        ax.grid(True, alpha=0.3)
        ax.legend(loc='center right')
        if title.startswith("Detection shots"):
            ax.set_xscale('log', base=2)

    fig.tight_layout()
    plot_path = out_dir / "ablations.png"
    fig.savefig(plot_path, dpi=150)
    print(f"\nSaved plot: {plot_path}")

    np.savez(
        out_dir / "ablations.npz",
        depths=np.array(DEPTHS), depth_fprs=depth_fprs, depth_detections=depth_dets,
        n_values=np.array(N_VALUES), n_fprs=n_fprs, n_detections=n_dets,
        shot_values=np.array(SHOT_VALUES), shot_fprs=shot_fprs, shot_detections=shot_dets,
        delta=DELTA, trials=TRIALS, inflation=INFLATION,
        train_descriptors=TRAIN_DESCRIPTORS, train_shots=TRAIN_SHOTS,
    )


if __name__ == "__main__":
    main()
