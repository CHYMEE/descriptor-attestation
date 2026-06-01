"""
Classical predictor for the Witness Protocol.

A multi-output linear regressor that maps a 16-parameter noise descriptor to the
N expected Pauli expectation values produced by a fixed witness set.
"""
from typing import List, Tuple, Union
import numpy as np
from sklearn.linear_model import LinearRegression

from .descriptor import NoiseDescriptor
from .device import QuantumDevice, create_honest_device
from .witness import WitnessSet


class WitnessPredictor:
    """Linear regression: descriptor (16) -> witness expectations (N)."""

    def __init__(self):
        self.model = LinearRegression()
        self._fitted = False

    def fit(self, descriptors: np.ndarray, expectations: np.ndarray) -> 'WitnessPredictor':
        """descriptors: (M, 16); expectations: (M, N) — true <P> per witness per descriptor."""
        self.model.fit(descriptors, expectations)
        self._fitted = True
        return self

    def predict(self, descriptor: Union[NoiseDescriptor, np.ndarray]) -> np.ndarray:
        if not self._fitted:
            raise RuntimeError("Predictor must be fit before predict")
        vec = descriptor.to_vector() if isinstance(descriptor, NoiseDescriptor) else np.asarray(descriptor)
        return self.model.predict(vec.reshape(1, -1))[0]


def sample_descriptors(n: int, seed: int = 0) -> List[NoiseDescriptor]:
    """Sample n descriptors from a realistic IBM-hardware-like prior."""
    rng = np.random.default_rng(seed)
    out = []
    for _ in range(n):
        t1 = rng.uniform(30, 120, 4)
        # qiskit-aer requires T2 <= 2*T1; sample T2 as a fraction of T1 to stay physical.
        t2 = t1 * rng.uniform(0.4, 1.0, 4)
        out.append(NoiseDescriptor(
            t1_times=t1.tolist(),
            t2_times=t2.tolist(),
            gate_errors=rng.uniform(0.0005, 0.005, 4).tolist(),
            readout_errors=rng.uniform(0.01, 0.05, 4).tolist(),
        ))
    return out


def build_training_data(
    descriptors: List[NoiseDescriptor],
    witness_set: WitnessSet,
    shots: int = 2048,
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Run the witness set against an honest device built from each descriptor.
    Returns X: (M, 16), Y: (M, N).

    Training shots are higher than detection shots so the regression sees clean targets.
    """
    X = np.stack([d.to_vector() for d in descriptors])
    Y = np.zeros((len(descriptors), len(witness_set)), dtype=np.float32)
    for i, d in enumerate(descriptors):
        dev = create_honest_device(d, device_id=f"train_{i}")
        Y[i] = witness_set.measure(dev, shots=shots)
    return X, Y
