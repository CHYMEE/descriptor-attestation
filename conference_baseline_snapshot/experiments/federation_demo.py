"""
Phase 3 headline experiment: naive FedAvg vs. attested FedAvg.

A 3-device federation runs a fixed 4-qubit Clifford target circuit (GHZ-4).
Two devices are honest; one is genuinely degraded but claims an honest-looking
descriptor.

Threat model. The liar samples a descriptor from the honest prior (its CLAIM)
and then runs with that descriptor's gate and readout errors multiplied by an
inflation factor (its TRUE state). With inflation = 1.0 the liar is identical
to an honest device; at higher inflation it operates much worse than it claims
and so contaminates a naive average. Witness measurements expose the gap
between claim and reality, allowing attested FedAvg to drop the liar.

We report TVD between the aggregated probability vector and the noise-free
ideal, sweeping the inflation factor.
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
    Coordinator, total_variation_distance,
)


SEED = 42
N_WITNESSES = 50
WITNESS_DEPTH = 5
TRAIN_DESCRIPTORS = 50
TRAIN_SHOTS = 1024
WITNESS_SHOTS = 1024
TARGET_SHOTS = 1024
DELTA = 0.05
TRIALS_PER_MAGNITUDE = 15
INFLATION_FACTORS = np.array([1.0, 1.5, 2.0, 3.0, 5.0])  # liar's true errors = factor x claimed
MAX_ERROR_RATE = 0.5  # cap inflated gate/readout errors so they stay physical


def build_target_circuit() -> QuantumCircuit:
    qc = QuantumCircuit(4)
    qc.h(0)
    qc.cx(0, 1)
    qc.cx(1, 2)
    qc.cx(2, 3)
    return qc


def ideal_probs(qc: QuantumCircuit) -> np.ndarray:
    sv = Statevector.from_instruction(qc)
    return np.abs(sv.data) ** 2


def main():
    print(f"Generating {N_WITNESSES} witnesses ...")
    ws = WitnessSet.generate(n=N_WITNESSES, depth=WITNESS_DEPTH, seed=SEED)

    print(f"Training predictor on {TRAIN_DESCRIPTORS} descriptors ...")
    train_descs = sample_descriptors(TRAIN_DESCRIPTORS, seed=SEED + 1)
    X, Y = build_training_data(train_descs, ws, shots=TRAIN_SHOTS)
    predictor = WitnessPredictor().fit(X, Y)
    train_residual = float(np.abs(predictor.model.predict(X) - Y).mean())
    print(f"  Predictor train residual: {train_residual:.4f}")

    coord = Coordinator(ws, predictor, delta=DELTA)
    target = build_target_circuit()
    ideal = ideal_probs(target)
    print(f"Target ideal: |0000> mass = {ideal[0]:.3f}, |1111> mass = {ideal[15]:.3f}")

    n_total = len(INFLATION_FACTORS) * TRIALS_PER_MAGNITUDE * 3
    fresh_descs = sample_descriptors(n_total, seed=SEED + 2)
    desc_idx = 0

    naive_mean = np.zeros(len(INFLATION_FACTORS))
    naive_std = np.zeros(len(INFLATION_FACTORS))
    attested_mean = np.zeros(len(INFLATION_FACTORS))
    attested_std = np.zeros(len(INFLATION_FACTORS))
    flag_rate_liar = np.zeros(len(INFLATION_FACTORS))
    flag_rate_honest = np.zeros(len(INFLATION_FACTORS))

    for fi, inflation in enumerate(INFLATION_FACTORS):
        naive_tvds = []
        attested_tvds = []
        liar_flags = 0
        honest_flags = 0
        for trial in range(TRIALS_PER_MAGNITUDE):
            d_h0 = fresh_descs[desc_idx];        desc_idx += 1
            d_h1 = fresh_descs[desc_idx];        desc_idx += 1
            d_liar_claim = fresh_descs[desc_idx]; desc_idx += 1

            honest0 = create_honest_device(d_h0, device_id=f"honest0_x{inflation:.1f}_t{trial}")
            honest1 = create_honest_device(d_h1, device_id=f"honest1_x{inflation:.1f}_t{trial}")

            # Liar: claim = honest-looking; truth = claim with inflated gate + readout errors
            liar_true_vec = d_liar_claim.to_vector().copy()
            liar_true_vec[8:16] = np.minimum(liar_true_vec[8:16] * inflation, MAX_ERROR_RATE)
            d_liar_true = NoiseDescriptor.from_vector(liar_true_vec)
            liar = QuantumDevice(d_liar_true, d_liar_claim, device_id=f"liar_x{inflation:.1f}_t{trial}")

            submissions = coord.collect(
                [honest0, honest1, liar], target,
                witness_shots=WITNESS_SHOTS, target_shots=TARGET_SHOTS,
            )

            naive_probs = coord.naive_fedavg(submissions)
            attested_probs, flagged = coord.attested_fedavg(submissions, witness_shots=WITNESS_SHOTS)

            naive_tvds.append(total_variation_distance(naive_probs, ideal))
            attested_tvds.append(total_variation_distance(attested_probs, ideal))

            # flagged is in the same order as submissions: [honest0, honest1, liar]
            honest_flags += int(flagged[0]) + int(flagged[1])
            liar_flags += int(flagged[2])

        naive_mean[fi] = float(np.mean(naive_tvds))
        naive_std[fi] = float(np.std(naive_tvds))
        attested_mean[fi] = float(np.mean(attested_tvds))
        attested_std[fi] = float(np.std(attested_tvds))
        flag_rate_liar[fi] = liar_flags / TRIALS_PER_MAGNITUDE
        flag_rate_honest[fi] = honest_flags / (2 * TRIALS_PER_MAGNITUDE)
        print(
            f"  inflation={inflation:.1f}x: naive TVD = {naive_mean[fi]:.4f} (+/- {naive_std[fi]:.4f}),  "
            f"attested TVD = {attested_mean[fi]:.4f} (+/- {attested_std[fi]:.4f}),  "
            f"liar flag rate = {flag_rate_liar[fi]:.2f}, honest flag rate = {flag_rate_honest[fi]:.2f}"
        )

    out_dir = Path(__file__).parent.parent / "results" / "phase3"
    out_dir.mkdir(parents=True, exist_ok=True)

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 4.5))

    ax1.errorbar(INFLATION_FACTORS, naive_mean, yerr=naive_std, fmt='o-', linewidth=2, markersize=8,
                 color='C3', label='Naive FedAvg', capsize=4)
    ax1.errorbar(INFLATION_FACTORS, attested_mean, yerr=attested_std, fmt='s-', linewidth=2, markersize=8,
                 color='C0', label='Attested FedAvg', capsize=4)
    ax1.set_xlabel('Liar noise inflation factor  (true / claimed errors)')
    ax1.set_ylabel('TVD vs. noiseless ideal')
    ax1.set_title('Federated Aggregation: Naive vs. Attested')
    ax1.legend()
    ax1.grid(True, alpha=0.3)

    ax2.plot(INFLATION_FACTORS, flag_rate_liar, 'o-', color='C3', linewidth=2, markersize=8, label='Liar flagged')
    ax2.plot(INFLATION_FACTORS, flag_rate_honest, 's-', color='C0', linewidth=2, markersize=8, label='Honest device flagged')
    ax2.axhline(DELTA, color='gray', linestyle=':', label=f'Hoeffding FPR bound (δ={DELTA})')
    ax2.set_xlabel('Liar noise inflation factor  (true / claimed errors)')
    ax2.set_ylabel('Flag rate')
    ax2.set_title('Attestation Outcomes by Device Type')
    ax2.set_ylim(-0.02, 1.05)
    ax2.legend()
    ax2.grid(True, alpha=0.3)

    fig.tight_layout()
    plot_path = out_dir / "federation_demo.png"
    fig.savefig(plot_path, dpi=150)
    print(f"\nSaved plot: {plot_path}")

    np.savez(
        out_dir / "federation_demo.npz",
        inflation_factors=INFLATION_FACTORS,
        naive_mean=naive_mean, naive_std=naive_std,
        attested_mean=attested_mean, attested_std=attested_std,
        flag_rate_liar=flag_rate_liar,
        flag_rate_honest=flag_rate_honest,
        ideal=ideal,
        delta=DELTA,
        n_witnesses=N_WITNESSES,
        target_shots=TARGET_SHOTS,
        witness_shots=WITNESS_SHOTS,
        trials=TRIALS_PER_MAGNITUDE,
    )
    print(f"Saved data: {out_dir / 'federation_demo.npz'}")


if __name__ == "__main__":
    main()
