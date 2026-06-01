"""Generate the locked witness ensemble.

Reproduces the 50-witness Clifford+Pauli ensemble used across all journal
experiments. Deterministic from configs/witness_config.yaml (seed=42).
Saves the witness-set descriptor to data/processed/witnesses.json.

Run:
    python scripts/01_generate_witnesses.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "conference_baseline_snapshot" / "src"))

import yaml  # type: ignore
from qem import WitnessSet  # type: ignore


def main() -> int:
    cfg = yaml.safe_load((ROOT / "configs" / "witness_config.yaml").read_text())
    ws = WitnessSet.generate(
        n=cfg["n_witnesses"],
        depth=cfg["depth"],
        n_qubits=cfg["n_qubits"],
        seed=cfg["seed"],
    )
    info = {
        "n_witnesses": len(ws),
        "depth": cfg["depth"],
        "n_qubits": cfg["n_qubits"],
        "seed": cfg["seed"],
        "pauli_labels": [p.to_label() for p in ws.paulis],
    }
    out_path = ROOT / "data" / "processed" / "witnesses.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(info, indent=2), encoding="utf-8")
    print(f"[01] Generated {len(ws)} witnesses (seed={cfg['seed']}). "
          f"Saved to {out_path.relative_to(ROOT)}.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
