"""
Defense baseline comparison for descriptor spoofing in federated QEM.

Same threat model as experiments/phase3_cameraready.py: 3 devices (2 honest, 1 liar
whose true gate+readout errors are inflated by `factor` while its claim is sampled
from the honest prior). Per trial, we collect the same submissions (witness
measurements + target probability vector) and compute aggregated probability vectors
under FOUR defense strategies:

  1. Naive            — equal-weight mean across all submissions (no defense)
  2. Median           — element-wise median across submissions, renormalized
  3. Trimmed mean     — drop the submission whose prob vector is farthest from the
                        centroid in L2; average the remaining two
  4. Witness attested — drop submissions flagged by the witness protocol; average rest

Metric: TVD between aggregated and noiseless ideal of GHZ-4. Story: defenses 1-3
either fail or barely help; only witness attestation tracks the honest baseline
across spoofing magnitudes. This experimentally demonstrates that statistical
filtering on submissions cannot substitute for a quantum-native attestation
primitive.
"""
import warnings
warnings.filterwarnings('ignore')

from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

from qiskit import QuantumCircuit
from qiskit.quantum_info import Statevector

from qem import (
    NoiseDescriptor, QuantumDevice, create_honest_device,
    WitnessSet, WitnessPredictor, sample_descriptors, build_training_data,
    Coordinator, total_variation_distance, detect,
)


SEED = 42
N_WITNESSES = 50
WITNESS_DEPTH = 5
TRAIN_DESCRIPTORS = 200
TRAIN_SHOTS = 4096
WITNESS_SHOTS = 1024
TARGET_SHOTS = 1024
DELTA = 0.05
TRIALS_PER_FACTOR = 50
INFLATION_FACTORS = np.array([1.0, 1.5, 2.0, 3.0, 5.0])
MAX_ERROR_RATE = 0.5


def build_target_circuit() -> QuantumCircuit:
    qc = QuantumCircuit(4)
    qc.h(0); qc.cx(0, 1); qc.cx(1, 2); qc.cx(2, 3)
    return qc


def naive_aggregate(prob_vectors):
    return np.mean(np.stack(prob_vectors), axis=0)


def median_aggregate(prob_vectors):
    """Element-wise median; renormalize since median does not preserve sum=1."""
    m = np.median(np.stack(prob_vectors), axis=0)
    s = m.sum()
    return m / s if s > 0 else m


def trimmed_mean_aggregate(prob_vectors):
    """Drop the vector whose L2 distance to the mean-of-all is largest; avg the rest."""
    arr = np.stack(prob_vectors)
    centroid = arr.mean(axis=0)
    distances = np.linalg.norm(arr - centroid, axis=1)
    keep = np.argsort(distances)[:-1]
    return arr[keep].mean(axis=0)


def attested_aggregate(submissions, predictor, witness_shots):
    """Drop flagged submissions, average the rest. Falls back to naive if all flagged."""
    kept = []
    for s in submissions:
        res = detect(s.claimed, s.witness_meas, predictor, shots=witness_shots, delta=DELTA)
        if not res.flagged:
            kept.append(s.target_probs)
    if not kept:
        return naive_aggregate([s.target_probs for s in submissions])
    return np.mean(np.stack(kept), axis=0)


def main():
    print("[Defense baseline comparison]")
    ws = WitnessSet.generate(n=N_WITNESSES, depth=WITNESS_DEPTH, seed=SEED)
    print(f"Generated {N_WITNESSES} witnesses (depth={WITNESS_DEPTH}).")

    print(f"Training predictor on {TRAIN_DESCRIPTORS} descriptors x {TRAIN_SHOTS} shots ...")
    train_descs = sample_descriptors(TRAIN_DESCRIPTORS, seed=SEED + 1)
    X, Y = build_training_data(train_descs, ws, shots=TRAIN_SHOTS)
    predictor = WitnessPredictor().fit(X, Y)
    train_residual = float(np.abs(predictor.model.predict(X) - Y).mean())
    print(f"  Predictor train residual: {train_residual:.4f}")

    coord = Coordinator(ws, predictor, delta=DELTA)
    target = build_target_circuit()
    ideal = np.abs(Statevector.from_instruction(target).data) ** 2

    n_total = len(INFLATION_FACTORS) * TRIALS_PER_FACTOR * 3
    fresh_descs = sample_descriptors(n_total, seed=SEED + 2)
    desc_idx = 0

    methods = ['naive', 'median', 'trimmed_mean', 'attested']
    tvd_mean = {m: np.zeros(len(INFLATION_FACTORS)) for m in methods}
    tvd_std = {m: np.zeros(len(INFLATION_FACTORS)) for m in methods}

    for fi, inflation in enumerate(INFLATION_FACTORS):
        per_trial = {m: [] for m in methods}
        for trial in range(TRIALS_PER_FACTOR):
            d_h0 = fresh_descs[desc_idx];        desc_idx += 1
            d_h1 = fresh_descs[desc_idx];        desc_idx += 1
            d_liar_claim = fresh_descs[desc_idx]; desc_idx += 1

            honest0 = create_honest_device(d_h0, device_id=f"h0_x{inflation:.1f}_t{trial}")
            honest1 = create_honest_device(d_h1, device_id=f"h1_x{inflation:.1f}_t{trial}")

            liar_true_vec = d_liar_claim.to_vector().copy()
            liar_true_vec[8:16] = np.minimum(liar_true_vec[8:16] * inflation, MAX_ERROR_RATE)
            d_liar_true = NoiseDescriptor.from_vector(liar_true_vec)
            liar = QuantumDevice(d_liar_true, d_liar_claim, device_id=f"liar_x{inflation:.1f}_t{trial}")

            submissions = coord.collect(
                [honest0, honest1, liar], target,
                witness_shots=WITNESS_SHOTS, target_shots=TARGET_SHOTS,
            )
            probs_list = [s.target_probs for s in submissions]

            per_trial['naive'].append(total_variation_distance(naive_aggregate(probs_list), ideal))
            per_trial['median'].append(total_variation_distance(median_aggregate(probs_list), ideal))
            per_trial['trimmed_mean'].append(total_variation_distance(trimmed_mean_aggregate(probs_list), ideal))
            per_trial['attested'].append(total_variation_distance(
                attested_aggregate(submissions, predictor, WITNESS_SHOTS), ideal))

        line = f"  inflation={inflation:.1f}x:"
        for m in methods:
            tvd_mean[m][fi] = float(np.mean(per_trial[m]))
            tvd_std[m][fi] = float(np.std(per_trial[m]))
            line += f"  {m}={tvd_mean[m][fi]:.4f}+/-{tvd_std[m][fi]:.4f}"
        print(line)

    out_dir = Path(__file__).parent.parent / "results" / "defense_comparison"
    out_dir.mkdir(parents=True, exist_ok=True)

    fig, ax = plt.subplots(figsize=(8, 5))
    style = {
        'naive':         dict(color='C3', marker='o', linestyle='-', label='Naive (no defense)'),
        'median':        dict(color='C1', marker='^', linestyle='--', label='Element-wise median'),
        'trimmed_mean':  dict(color='C5', marker='D', linestyle='--', label='Trimmed mean (drop max-dev)'),
        'attested':      dict(color='C0', marker='s', linestyle='-', label='Witness attestation (ours)'),
    }
    for m in methods:
        ax.errorbar(INFLATION_FACTORS, tvd_mean[m], yerr=tvd_std[m],
                    linewidth=2, markersize=7, capsize=4, **style[m])
    ax.set_xlabel('Liar noise inflation factor  (true / claimed errors)')
    ax.set_ylabel('TVD vs. noiseless ideal')
    ax.set_title(f'Defense Baselines vs. Witness Attestation  (T={TRIALS_PER_FACTOR})')
    ax.grid(True, alpha=0.3)
    ax.legend(loc='upper left')
    fig.tight_layout()
    plot_path = out_dir / "defense_comparison.png"
    fig.savefig(plot_path, dpi=150)
    print(f"\nSaved plot: {plot_path}")

    np.savez(
        out_dir / "defense_comparison.npz",
        inflation_factors=INFLATION_FACTORS,
        **{f"{m}_mean": tvd_mean[m] for m in methods},
        **{f"{m}_std": tvd_std[m] for m in methods},
        ideal=ideal,
        delta=DELTA,
        n_witnesses=N_WITNESSES,
        target_shots=TARGET_SHOTS,
        witness_shots=WITNESS_SHOTS,
        trials=TRIALS_PER_FACTOR,
        train_residual=train_residual,
    )
    print(f"Saved data: {out_dir / 'defense_comparison.npz'}")


if __name__ == "__main__":
    main()
