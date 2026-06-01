"""
Hardware validation for the Witness Protocol on real IBM Quantum devices.

Two modes:

  * Inspect (default, no hardware time spent)
      Authenticates, lists backends, prints calibration for the picked qubits,
      and exits. Useful as Stage A/B of the validation plan.

  * Submit (with --submit flag, BURNS HARDWARE TIME)
      Trains the synthetic-data predictor, transpiles N witness circuits onto
      the chosen physical qubits, batches them in a single SamplerV2 job,
      compares predicted-vs-measured Pauli expectations, and writes a scatter
      plot + npz data dump to results/hardware/.

Auth: this script never asks for a token. The caller must have run
QiskitRuntimeService.save_account(...) beforehand, or set the QISKIT_IBM_TOKEN
environment variable that QiskitRuntimeService picks up.
"""
import argparse
import warnings
warnings.filterwarnings('ignore')

from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

from qiskit_ibm_runtime import QiskitRuntimeService

from qem import (
    WitnessSet, WitnessPredictor, sample_descriptors, build_training_data,
)
from qem.hardware import (
    extract_descriptor_from_backend, pick_qubits,
    measure_witnesses_on_backend, print_calibration_summary,
)


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument('--backend', default=None,
                   help='IBM backend name (e.g. ibm_brisbane). If omitted, picks least-busy operational.')
    p.add_argument('--qubits', nargs=4, type=int, default=None,
                   help='4 physical qubits to use (default: pick by calibration score)')
    p.add_argument('--n_witnesses', type=int, default=20,
                   help='How many witness circuits to submit (default 20 to save free-tier minutes)')
    p.add_argument('--depth', type=int, default=5)
    p.add_argument('--shots', type=int, default=512,
                   help='Shots per witness circuit (default 512; 1024 doubles cost)')
    p.add_argument('--submit', action='store_true',
                   help='ACTUALLY submit to hardware. Without this flag the script is inspect-only.')
    p.add_argument('--seed', type=int, default=42,
                   help='Public seed for the witness set')
    p.add_argument('--train_descriptors', type=int, default=100)
    p.add_argument('--train_shots', type=int, default=2048)
    return p.parse_args()


def main():
    args = parse_args()

    print("Connecting to IBM Quantum ...")
    service = QiskitRuntimeService(channel='ibm_quantum_platform')

    if args.backend:
        backend = service.backend(args.backend)
    else:
        backend = service.least_busy(operational=True, simulator=False)
    print(f"Using backend: {backend.name}  ({backend.num_qubits} qubits, "
          f"basis = {sorted(backend.target.operation_names)[:6]}...)")

    qubits = args.qubits or pick_qubits(backend, n=4)
    print()
    print_calibration_summary(backend, qubits)

    descriptor = extract_descriptor_from_backend(backend, qubits)
    print(f"\nExtracted 16-param descriptor:")
    print(f"  T1 (us) = {[f'{t:.1f}' for t in descriptor.t1_times]}")
    print(f"  T2 (us) = {[f'{t:.1f}' for t in descriptor.t2_times]}")
    print(f"  gate    = {[f'{e:.5f}' for e in descriptor.gate_errors]}")
    print(f"  readout = {[f'{e:.4f}' for e in descriptor.readout_errors]}")

    if not args.submit:
        print("\n[inspect-only] Done. Rerun with --submit to actually run on hardware.")
        return

    # ------- Submit path: builds witness set, trains predictor, runs hardware ------- #
    print(f"\nGenerating {args.n_witnesses} witnesses (depth={args.depth}, seed={args.seed}) ...")
    ws = WitnessSet.generate(n=args.n_witnesses, depth=args.depth, seed=args.seed)

    print(f"Training synthetic-noise predictor ({args.train_descriptors} descriptors x "
          f"{args.train_shots} shots) ...")
    train_descs = sample_descriptors(args.train_descriptors, seed=args.seed + 1)
    X, Y = build_training_data(train_descs, ws, shots=args.train_shots)
    predictor = WitnessPredictor().fit(X, Y)
    train_residual = float(np.abs(predictor.model.predict(X) - Y).mean())
    print(f"  Train residual (mean abs): {train_residual:.4f}")

    predicted = predictor.predict(descriptor)
    print(f"  Predicted Pauli expectations: range = [{predicted.min():.3f}, {predicted.max():.3f}], "
          f"mean = {predicted.mean():.3f}")

    print(f"\nSubmitting {len(ws)} witness circuits to {backend.name}, shots={args.shots} ...")
    print(f"  expected hardware budget = ~{len(ws) * args.shots / 1000:.1f}k shots, "
          f"queue + execution may take several minutes.")
    measured = measure_witnesses_on_backend(ws, backend, qubits, shots=args.shots)

    residuals = np.abs(measured - predicted)
    correlation = float(np.corrcoef(predicted, measured)[0, 1])
    rmse = float(np.sqrt(np.mean((predicted - measured) ** 2)))
    print(f"\nResults:")
    print(f"  Measured range:    [{measured.min():.3f}, {measured.max():.3f}]")
    print(f"  Mean abs residual: {residuals.mean():.4f}")
    print(f"  Max abs residual:  {residuals.max():.4f}")
    print(f"  RMSE:              {rmse:.4f}")
    print(f"  Pearson r:         {correlation:.4f}")

    out_dir = Path(__file__).parent.parent / "results" / "hardware"
    out_dir.mkdir(parents=True, exist_ok=True)

    fig, ax = plt.subplots(figsize=(6, 6))
    ax.scatter(predicted, measured, alpha=0.75, s=50, color='C0', edgecolor='black', linewidth=0.5)
    ax.plot([-1, 1], [-1, 1], 'k--', alpha=0.5, label='perfect prediction')
    ax.set_xlabel('Predicted (synthetic 16-param noise model)')
    ax.set_ylabel(f'Measured ({backend.name})')
    ax.set_title(f'Witness Protocol on Real Hardware\n'
                 f'qubits={list(qubits)}, N={len(ws)}, S={args.shots},  r={correlation:.3f}, RMSE={rmse:.3f}')
    ax.set_xlim(-1.05, 1.05)
    ax.set_ylim(-1.05, 1.05)
    ax.set_aspect('equal')
    ax.grid(True, alpha=0.3)
    ax.legend(loc='upper left')
    plot_path = out_dir / "hardware_validation.png"
    fig.tight_layout()
    fig.savefig(plot_path, dpi=150)
    print(f"\nSaved plot: {plot_path}")

    np.savez(
        out_dir / "hardware_validation.npz",
        backend_name=backend.name,
        qubits=np.array(list(qubits)),
        predicted=predicted,
        measured=measured,
        residuals=residuals,
        correlation=correlation,
        rmse=rmse,
        descriptor_t1=np.array(descriptor.t1_times),
        descriptor_t2=np.array(descriptor.t2_times),
        descriptor_gate=np.array(descriptor.gate_errors),
        descriptor_ro=np.array(descriptor.readout_errors),
        train_residual=train_residual,
        n_witnesses=args.n_witnesses,
        depth=args.depth,
        shots=args.shots,
    )
    print(f"Saved data: {out_dir / 'hardware_validation.npz'}")


if __name__ == "__main__":
    main()
