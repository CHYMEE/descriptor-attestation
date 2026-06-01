"""Train the linear-regression predictor under the locked deployment prior.

Re-trains the WitnessPredictor on 100 deployment-prior descriptors at 2048
shots (deterministic descriptor sampling; AerSim per-shot RNG is unseeded
in qiskit-aer, so the trained weights vary slightly across runs — this is
the source of the documented across-instance variance in §5.A / §5.E).

Saves predictor weights + bias to data/processed/predictor.npz, plus the
spectral / Frobenius / L-infinity norms used in §4.

Wall: ~60-70s (dominated by AerSim density-matrix simulation).

Run:
    python scripts/02_train_predictor.py
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "conference_baseline_snapshot" / "src"))

import yaml  # type: ignore
from qem import WitnessSet, WitnessPredictor, build_training_data  # type: ignore
from descriptor_attestation.deployment_prior import sample_descriptors_deployment


def main() -> int:
    cfg = yaml.safe_load((ROOT / "configs" / "experiment_config.yaml").read_text())
    ws = WitnessSet.generate(
        n=cfg["witness"]["n_witnesses"],
        depth=cfg["witness"]["depth"],
        seed=cfg["witness"]["seed"],
    )
    descs = sample_descriptors_deployment(
        cfg["predictor"]["n_train_descriptors"],
        seed=cfg["predictor"]["desc_sampling_seed"],
    )
    t0 = time.time()
    X, Y = build_training_data(descs, ws, shots=cfg["predictor"]["train_shots"])
    pred = WitnessPredictor().fit(X, Y)
    train_seconds = time.time() - t0
    W = np.asarray(pred.model.coef_, dtype=np.float64)
    b = np.asarray(pred.model.intercept_, dtype=np.float64)
    train_residual = float(np.abs(pred.model.predict(X) - Y).mean())

    norms = {
        "spectral": float(np.linalg.norm(W, ord=2)),
        "frobenius": float(np.linalg.norm(W, ord="fro")),
        "inf": float(np.linalg.norm(W, ord=np.inf)),
        "frobenius_over_sqrt_n": float(np.linalg.norm(W, ord="fro") / np.sqrt(W.shape[0])),
    }
    out_npz = ROOT / "data" / "processed" / "predictor.npz"
    out_json = ROOT / "data" / "processed" / "predictor_norms.json"
    out_npz.parent.mkdir(parents=True, exist_ok=True)
    np.savez(out_npz, W=W, b=b)
    out_json.write_text(json.dumps({
        "train_residual": train_residual,
        "train_seconds": train_seconds,
        "W_shape": list(W.shape),
        "b_shape": list(b.shape),
        "norms": norms,
    }, indent=2), encoding="utf-8")
    print(f"[02] Predictor trained in {train_seconds:.1f}s, "
          f"train_residual={train_residual:.5f}.")
    print(f"     ||W||_2={norms['spectral']:.4f} ||W||_F={norms['frobenius']:.4f} "
          f"||W||_inf={norms['inf']:.4f}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
