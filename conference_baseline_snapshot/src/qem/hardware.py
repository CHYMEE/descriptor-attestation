"""
Hardware interface for running the Witness Protocol on real IBM Quantum devices.

Provides three things:

  1. extract_descriptor_from_backend(backend, qubits) -> NoiseDescriptor
     Reads T1, T2, single-qubit gate error, and readout error for the given four
     physical qubits and packs them into our 16-parameter descriptor.

  2. pick_qubits(backend, n=4) -> List[int]
     Returns a connected n-qubit chain with the best calibration (longest mean
     T1/T2, smallest gate errors).

  3. measure_witnesses_on_backend(witness_set, backend, qubits, shots) -> np.ndarray
     Transpiles each witness circuit (with basis change + measurement) onto the
     given physical qubits, batches them in a single SamplerV2 job, and returns
     the (N,) array of empirical Pauli expectation values.

This module never reads or writes IBM credentials. The caller is responsible
for instantiating QiskitRuntimeService with a saved account or env var.
"""
from typing import List, Optional, Sequence
import numpy as np
from qiskit import QuantumCircuit, transpile

from .descriptor import NoiseDescriptor
from .witness import WitnessSet


def _qubit_t1_t2_us(target, q: int) -> tuple:
    """Pull (T1, T2) in microseconds from a backend target. Falls back to (50.0, 30.0) if missing."""
    try:
        qprop = target.qubit_properties[q]
        t1 = (qprop.t1 or 50e-6) * 1e6
        t2 = (qprop.t2 or 30e-6) * 1e6
        return float(t1), float(t2)
    except (AttributeError, IndexError, KeyError, TypeError):
        return 50.0, 30.0


def _qubit_gate_error(target, q: int) -> float:
    """Single-qubit gate error: try sx, then x, then rz; default 1e-3."""
    for name in ("sx", "x", "rz", "id"):
        try:
            instr = target[name][(q,)]
            if instr is not None and instr.error is not None and instr.error > 0:
                return float(instr.error)
        except (KeyError, TypeError, AttributeError):
            continue
    return 1e-3


def _qubit_readout_error(target, q: int, backend=None) -> float:
    """Readout error: try target['measure'], then backend.properties().readout_error; default 0.02."""
    try:
        instr = target["measure"][(q,)]
        if instr is not None and instr.error is not None and instr.error >= 0:
            return float(instr.error)
    except (KeyError, TypeError, AttributeError):
        pass
    if backend is not None:
        try:
            return float(backend.properties().readout_error(q))
        except Exception:
            pass
    return 0.02


def extract_descriptor_from_backend(backend, qubits: Sequence[int]) -> NoiseDescriptor:
    """Read calibration for the four selected physical qubits and return our 16-param descriptor."""
    if len(qubits) != 4:
        raise ValueError(f"Expected 4 qubits, got {len(qubits)}")
    target = backend.target

    t1_times, t2_times, gate_errors, readout_errors = [], [], [], []
    for q in qubits:
        t1, t2 = _qubit_t1_t2_us(target, q)
        # Enforce qiskit-aer's T2 <= 2*T1 in case calibration drift puts it above
        t2 = min(t2, 2.0 * t1 - 1e-6)
        t1_times.append(t1)
        t2_times.append(t2)
        gate_errors.append(_qubit_gate_error(target, q))
        readout_errors.append(_qubit_readout_error(target, q, backend))

    return NoiseDescriptor(
        t1_times=t1_times,
        t2_times=t2_times,
        gate_errors=gate_errors,
        readout_errors=readout_errors,
    )


def _qubit_score(target, q: int) -> float:
    t1, t2 = _qubit_t1_t2_us(target, q)
    err = _qubit_gate_error(target, q)
    ro = _qubit_readout_error(target, q)
    # Higher is better: long coherence, small errors.
    return (t1 + t2) - 1e4 * err - 1e3 * ro


def pick_qubits(backend, n: int = 4) -> List[int]:
    """Pick n contiguously-connected qubits scoring highest on combined calibration metrics."""
    cm = backend.coupling_map
    if cm is None:
        return list(range(n))
    target = backend.target

    adj = {}
    for a, b in cm.get_edges():
        adj.setdefault(a, set()).add(b)
        adj.setdefault(b, set()).add(a)

    best_path: Optional[List[int]] = None
    best_score = -np.inf

    def dfs(path: List[int], visited: set):
        nonlocal best_path, best_score
        if len(path) == n:
            score = sum(_qubit_score(target, q) for q in path)
            if score > best_score:
                best_score = score
                best_path = list(path)
            return
        for nb in adj.get(path[-1], set()):
            if nb in visited:
                continue
            visited.add(nb)
            path.append(nb)
            dfs(path, visited)
            path.pop()
            visited.remove(nb)

    for start in sorted(adj, key=lambda q: -_qubit_score(target, q))[:8]:
        # Only seed DFS from the 8 best-scoring qubits to bound runtime.
        dfs([start], {start})

    if best_path is None:
        return list(range(n))
    return best_path


def measure_witnesses_on_backend(
    witness_set: WitnessSet,
    backend,
    qubits: Sequence[int],
    shots: int = 1024,
    sampler=None,
    optimization_level: int = 1,
) -> np.ndarray:
    """
    Run all witnesses on `backend` mapped to physical `qubits`, return (N,) array of
    Pauli expectations in [-1, 1].

    Submits as a single batched SamplerV2 PUB-list job. Caller may pass a pre-built
    sampler (e.g., to share a Session); otherwise a one-off sampler is created in
    backend mode.
    """
    if len(qubits) != witness_set.circuits[0].num_qubits:
        raise ValueError(f"qubits length {len(qubits)} != witness circuit width")

    transpiled = []
    for circ, pauli in zip(witness_set.circuits, witness_set.paulis):
        prepared = WitnessSet._apply_basis_change(circ, pauli)
        prepared.measure_all()
        t = transpile(prepared, backend, initial_layout=list(qubits), optimization_level=optimization_level)
        transpiled.append(t)

    if sampler is None:
        from qiskit_ibm_runtime import SamplerV2
        sampler = SamplerV2(mode=backend)

    job = sampler.run(transpiled, shots=shots)
    print(f"  submitted job {job.job_id()}; waiting for result ...")
    result = job.result()

    expectations = np.zeros(len(witness_set), dtype=np.float32)
    for i, pub_result in enumerate(result):
        # SamplerV2 PUB result: data registers keyed by classical-register name.
        # measure_all() creates a register named 'meas'.
        try:
            counts = pub_result.data.meas.get_counts()
        except AttributeError:
            # Fallback: take the only register present.
            data = pub_result.data
            reg_name = list(data._fields if hasattr(data, '_fields') else dir(data))
            reg = next((getattr(data, n) for n in reg_name if hasattr(getattr(data, n, None), 'get_counts')), None)
            if reg is None:
                raise RuntimeError(f"Could not extract counts from PUB result {i}: {pub_result}")
            counts = reg.get_counts()
        expectations[i] = WitnessSet._expectation(counts, witness_set.paulis[i])

    return expectations


def print_calibration_summary(backend, qubits: Sequence[int]) -> None:
    """Print a one-line-per-qubit calibration summary for human inspection."""
    target = backend.target
    print(f"Backend: {backend.name}  |  selected qubits: {list(qubits)}")
    print(f"  q   T1(us)  T2(us)  gate_err   readout_err")
    for q in qubits:
        t1, t2 = _qubit_t1_t2_us(target, q)
        ge = _qubit_gate_error(target, q)
        re = _qubit_readout_error(target, q, backend)
        print(f"  {q:<3} {t1:6.1f}  {t2:6.1f}  {ge:.5f}    {re:.4f}")
