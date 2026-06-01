"""
Device abstraction for federated QEM.
"""
from typing import Optional
import numpy as np
from qiskit import QuantumCircuit
from qiskit_aer import AerSimulator
from .descriptor import NoiseDescriptor


class QuantumDevice:
    def __init__(self, true_descriptor: NoiseDescriptor, claimed_descriptor: Optional[NoiseDescriptor] = None, device_id: str = "device_0"):
        self.device_id = device_id
        self.true_descriptor = true_descriptor
        self.claimed_descriptor = claimed_descriptor or true_descriptor
        self.simulator = AerSimulator(method='density_matrix', noise_model=true_descriptor.to_qiskit_noise_model())

    @property
    def is_honest(self) -> bool:
        return self.true_descriptor.distance(self.claimed_descriptor) < 1e-6

    def run_circuit(self, circuit: QuantumCircuit, shots: int = 1000) -> dict:
        circuit = circuit.copy()
        if not any(instr.operation.name == 'measure' for instr in circuit):
            circuit.measure_all()
        job = self.simulator.run(circuit, shots=shots)
        return job.result().get_counts()

    def get_probability_vector(self, circuit: QuantumCircuit, shots: int = 1000) -> np.ndarray:
        if circuit.num_qubits != 4:
            raise ValueError(f"Expected 4-qubit circuit, got {circuit.num_qubits}")
        counts = self.run_circuit(circuit, shots)
        probs = np.zeros(16, dtype=np.float32)
        total_shots = sum(counts.values())
        for bitstring, count in counts.items():
            index = int(bitstring.replace(' ', ''), 2)
            probs[index] = count / total_shots
        return probs

    def get_claimed_descriptor_vector(self) -> np.ndarray:
        return self.claimed_descriptor.to_vector()


def create_honest_device(descriptor: NoiseDescriptor, device_id: str = "honest") -> QuantumDevice:
    return QuantumDevice(descriptor, device_id=device_id)
