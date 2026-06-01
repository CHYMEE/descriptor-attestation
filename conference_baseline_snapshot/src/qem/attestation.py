"""
Detection theorem for the Witness Protocol.

For each witness i, the device returns an empirical expectation X_i in [-1, 1]
estimated from S shots. Under an honest device with claimed descriptor d,
E[X_i] = predictor(d)_i. By Hoeffding's inequality (range = 2),

    P(|X_i - E[X_i]| >= eps) <= 2 * exp(-S * eps^2 / 2).

Applying a union bound across N witnesses, the probability that ANY witness
deviates by more than eps is bounded by 2N * exp(-S * eps^2 / 2). Solving for
eps at confidence level 1 - delta:

    eps = sqrt( 2 * ln(2N / delta) / S )

A device is flagged as dishonest iff max_i |measured_i - predicted_i| > eps.
By construction, the false-positive rate against honest devices is <= delta.
"""
from dataclasses import dataclass
from typing import Union
import numpy as np

from .descriptor import NoiseDescriptor
from .predictor import WitnessPredictor


def hoeffding_bound(n_witnesses: int, shots: int, delta: float = 0.05) -> float:
    """Per-witness deviation threshold s.t. P(max_i |Xi - E[Xi]| > eps) <= delta (union bound, range=2)."""
    if not (0 < delta < 1):
        raise ValueError("delta must be in (0, 1)")
    return float(np.sqrt(2.0 * np.log(2.0 * n_witnesses / delta) / shots))


@dataclass
class AttestationResult:
    flagged: bool
    epsilon: float
    max_deviation: float
    deviations: np.ndarray   # (N,) absolute deviations per witness
    predicted: np.ndarray    # (N,)
    measured: np.ndarray     # (N,)


def detect(
    claimed: Union[NoiseDescriptor, np.ndarray],
    measured: np.ndarray,
    predictor: WitnessPredictor,
    shots: int,
    delta: float = 0.05,
) -> AttestationResult:
    """
    Run the attestation decision: flag if any witness deviates beyond the Hoeffding threshold.

    Args:
        claimed: descriptor the device claims (drives the predictor)
        measured: (N,) empirical Pauli expectations from running witnesses on the device
        predictor: trained WitnessPredictor
        shots: per-witness shot count used to obtain `measured`
        delta: target false-positive rate against honest devices
    """
    measured = np.asarray(measured, dtype=np.float64)
    predicted = predictor.predict(claimed).astype(np.float64)
    deviations = np.abs(measured - predicted)
    epsilon = hoeffding_bound(len(measured), shots, delta)
    return AttestationResult(
        flagged=bool(deviations.max() > epsilon),
        epsilon=epsilon,
        max_deviation=float(deviations.max()),
        deviations=deviations,
        predicted=predicted,
        measured=measured,
    )
