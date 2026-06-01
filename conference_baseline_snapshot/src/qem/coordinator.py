"""
Coordinator for measurements-style federation.

Each participating device submits:
  - its claimed noise descriptor,
  - witness-set Pauli expectation values (used for attestation),
  - a target-circuit probability vector (the thing being aggregated).

The coordinator can either average all submissions equally (naive FedAvg) or
drop submissions whose witnesses fail attestation (attested FedAvg).
"""
from dataclasses import dataclass
from typing import List, Sequence, Tuple
import numpy as np
from qiskit import QuantumCircuit

from .descriptor import NoiseDescriptor
from .device import QuantumDevice
from .witness import WitnessSet
from .predictor import WitnessPredictor
from .attestation import detect


@dataclass
class DeviceSubmission:
    device_id: str
    claimed: NoiseDescriptor
    witness_meas: np.ndarray   # (N,) Pauli expectations from the witness set
    target_probs: np.ndarray   # (16,) probability vector for the target circuit


class Coordinator:
    """Collects submissions and runs naive/attested aggregation."""

    def __init__(self, witness_set: WitnessSet, predictor: WitnessPredictor, delta: float = 0.05):
        self.witness_set = witness_set
        self.predictor = predictor
        self.delta = delta

    def collect(
        self,
        devices: Sequence[QuantumDevice],
        target_circuit: QuantumCircuit,
        witness_shots: int = 1024,
        target_shots: int = 1024,
    ) -> List[DeviceSubmission]:
        out: List[DeviceSubmission] = []
        for dev in devices:
            out.append(DeviceSubmission(
                device_id=dev.device_id,
                claimed=dev.claimed_descriptor,
                witness_meas=self.witness_set.measure(dev, shots=witness_shots),
                target_probs=dev.get_probability_vector(target_circuit, shots=target_shots),
            ))
        return out

    @staticmethod
    def naive_fedavg(submissions: Sequence[DeviceSubmission]) -> np.ndarray:
        return np.mean(np.stack([s.target_probs for s in submissions]), axis=0)

    def attested_fedavg(
        self,
        submissions: Sequence[DeviceSubmission],
        witness_shots: int,
    ) -> Tuple[np.ndarray, List[bool]]:
        """
        Drop flagged submissions, average the rest.

        Returns (aggregated_probs, flagged_per_device). If every device is
        flagged, falls back to the naive average so the protocol always returns
        a result.
        """
        flagged: List[bool] = []
        kept: List[np.ndarray] = []
        for s in submissions:
            res = detect(s.claimed, s.witness_meas, self.predictor, shots=witness_shots, delta=self.delta)
            flagged.append(res.flagged)
            if not res.flagged:
                kept.append(s.target_probs)
        if not kept:
            return self.naive_fedavg(submissions), flagged
        return np.mean(np.stack(kept), axis=0), flagged


def total_variation_distance(p: np.ndarray, q: np.ndarray) -> float:
    """TVD(p, q) = 1/2 * sum |p_i - q_i|."""
    return float(0.5 * np.sum(np.abs(np.asarray(p, dtype=np.float64) - np.asarray(q, dtype=np.float64))))
