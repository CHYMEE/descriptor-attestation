"""
Simplified quantum noise descriptor for ICMIC 2026 conference paper.
"""
from dataclasses import dataclass, field
from typing import List
import numpy as np
from qiskit_aer.noise import NoiseModel, thermal_relaxation_error, depolarizing_error, ReadoutError


@dataclass
class NoiseDescriptor:
    """16-parameter noise descriptor for 4-qubit systems."""
    t1_times: List[float] = field(default_factory=lambda: [50.0, 50.0, 50.0, 50.0])
    t2_times: List[float] = field(default_factory=lambda: [30.0, 30.0, 30.0, 30.0])
    gate_errors: List[float] = field(default_factory=lambda: [0.001, 0.001, 0.001, 0.001])
    readout_errors: List[float] = field(default_factory=lambda: [0.02, 0.02, 0.02, 0.02])

    def to_vector(self) -> np.ndarray:
        return np.array(self.t1_times + self.t2_times + self.gate_errors + self.readout_errors, dtype=np.float32)

    @classmethod
    def from_vector(cls, vector: np.ndarray) -> 'NoiseDescriptor':
        return cls(
            t1_times=vector[0:4].tolist(),
            t2_times=vector[4:8].tolist(),
            gate_errors=vector[8:12].tolist(),
            readout_errors=vector[12:16].tolist()
        )

    def to_qiskit_noise_model(self) -> NoiseModel:
        noise_model = NoiseModel()
        for qubit in range(4):
            thermal_error = thermal_relaxation_error(self.t1_times[qubit], self.t2_times[qubit], 0.05)
            noise_model.add_quantum_error(thermal_error, ['u1', 'u2', 'u3'], [qubit])
            gate_error = depolarizing_error(self.gate_errors[qubit], 1)
            noise_model.add_quantum_error(gate_error, ['u1', 'u2', 'u3'], [qubit])
            readout_error = ReadoutError([[1 - self.readout_errors[qubit], self.readout_errors[qubit]],
                                        [self.readout_errors[qubit], 1 - self.readout_errors[qubit]]])
            noise_model.add_readout_error(readout_error, [qubit])
        return noise_model

    def distance(self, other: 'NoiseDescriptor') -> float:
        return np.linalg.norm(self.to_vector() - other.to_vector())
