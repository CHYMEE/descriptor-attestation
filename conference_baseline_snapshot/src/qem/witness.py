"""
Witness Protocol: random Clifford circuits with random Pauli observables.

Each witness yields a scalar expectation value in [-1, 1], suitable for
classical prediction and Hoeffding-bound attestation.
"""
from dataclasses import dataclass
from typing import List
import numpy as np
from qiskit import QuantumCircuit
from qiskit.quantum_info import random_clifford, Pauli

from .device import QuantumDevice


PAULI_CHARS = np.array(['I', 'X', 'Y', 'Z'])


def _random_clifford_circuit(n_qubits: int, depth: int, rng: np.random.Generator) -> QuantumCircuit:
    """Depth-d random Clifford circuit: alternating 1Q-Clifford and CX layers."""
    qc = QuantumCircuit(n_qubits)
    for _ in range(depth):
        for q in range(n_qubits):
            cliff = random_clifford(1, seed=int(rng.integers(2**31 - 1)))
            qc.compose(cliff.to_circuit(), [q], inplace=True)
        order = rng.permutation(n_qubits)
        for i in range(0, n_qubits - 1, 2):
            qc.cx(int(order[i]), int(order[i + 1]))
    return qc


def _random_nonidentity_pauli(n_qubits: int, rng: np.random.Generator) -> Pauli:
    """Sample a random Pauli string excluding all-identity."""
    while True:
        label = ''.join(PAULI_CHARS[rng.integers(0, 4, size=n_qubits)])
        if label != 'I' * n_qubits:
            return Pauli(label)


@dataclass
class WitnessSet:
    """Collection of N random Clifford circuits, each paired with a random Pauli observable."""
    circuits: List[QuantumCircuit]
    paulis: List[Pauli]
    seed: int

    @classmethod
    def generate(cls, n: int = 50, depth: int = 5, n_qubits: int = 4, seed: int = 42) -> 'WitnessSet':
        rng = np.random.default_rng(seed)
        circuits = [_random_clifford_circuit(n_qubits, depth, rng) for _ in range(n)]
        paulis = [_random_nonidentity_pauli(n_qubits, rng) for _ in range(n)]
        return cls(circuits=circuits, paulis=paulis, seed=seed)

    def __len__(self) -> int:
        return len(self.circuits)

    def measure(self, device: QuantumDevice, shots: int = 1000) -> np.ndarray:
        """Run all witnesses on `device`, return array of expectation values in [-1, 1]."""
        out = np.zeros(len(self), dtype=np.float32)
        for i, (circ, pauli) in enumerate(zip(self.circuits, self.paulis)):
            prepared = self._apply_basis_change(circ, pauli)
            counts = device.run_circuit(prepared, shots=shots)
            out[i] = self._expectation(counts, pauli)
        return out

    @staticmethod
    def _apply_basis_change(circ: QuantumCircuit, pauli: Pauli) -> QuantumCircuit:
        """Append basis-rotation gates so the Pauli becomes diagonal in Z."""
        qc = circ.copy()
        label = pauli.to_label().lstrip('+-')
        n = len(label)
        for i, ch in enumerate(label):
            q = n - 1 - i  # qiskit label is big-endian; q=0 is rightmost char
            if ch == 'X':
                qc.h(q)
            elif ch == 'Y':
                qc.sdg(q)
                qc.h(q)
        return qc

    @staticmethod
    def _expectation(counts: dict, pauli: Pauli) -> float:
        """Compute <P> from Z-basis counts after basis change."""
        label = pauli.to_label().lstrip('+-')  # big-endian; label[0] = highest-index qubit
        total = sum(counts.values())
        acc = 0.0
        for bitstring, c in counts.items():
            bits = bitstring.replace(' ', '')  # also big-endian
            eigenvalue = 1
            for ch, b in zip(label, bits):
                if ch != 'I':
                    eigenvalue *= -1 if b == '1' else 1
            acc += eigenvalue * c
        return acc / total
