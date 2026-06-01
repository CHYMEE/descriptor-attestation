"""
Deployment-matched descriptor prior for journal-extension predictor training.

Replaces conference_baseline.qem.predictor.sample_descriptors() (whose hardcoded
prior T1 in U(30, 120) us, T2 = T1*U(0.4, 1.0), gate_err in U(5e-4, 5e-3),
readout in U(0.01, 0.05) -- does not match real IBM Heron r2 deployment ranges
and which produced F5 in FINDINGS.md: 100% Type I false-positive rate on real
hardware in the 2026-05-13 federation scale sweep).

Bounds derived from 20 qubit-observations across 5 calibration snapshots:
  - conference Kingston 2026-04-29 (hardcoded in run.json conference_calibration)
  - Phase 1 Kingston 2026-05-06   (results/phase1/.../run.json)
  - Phase 2 Kingston 2026-05-13   (results/phase2/.../ibm_kingston/run.json)
  - Phase 2 Fez 2026-05-13        (results/phase2/.../ibm_fez/run.json)
  - Phase 2 Marrakesh 2026-05-13  (results/phase2/.../ibm_marrakesh/run.json)

This module imports NoiseDescriptor from the read-only conference baseline;
it does NOT modify conference code.
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import List

import numpy as np

# Make the read-only conference baseline importable without modifying it.
_REPO_ROOT = Path(__file__).resolve().parents[2]
_BASELINE_SRC = _REPO_ROOT / "conference_baseline" / "src"
if str(_BASELINE_SRC) not in sys.path:
    sys.path.insert(0, str(_BASELINE_SRC))

from qem.descriptor import NoiseDescriptor


# ---------------------------------------------------------------------------
# Deployment-matched prior bounds (see module docstring for derivation).
# Tunable here; no other call site should reach into these constants.
# ---------------------------------------------------------------------------
T1_LO_US = 50.0
T1_HI_US = 500.0
T2_RATIO_LO = 0.1
T2_RATIO_HI = 1.8
GATE_ERR_LO = 1e-4
GATE_ERR_HI = 8e-4
READOUT_ERR_LO = 0.005
READOUT_ERR_HI = 0.05
T2_PHYSICAL_MARGIN_US = 1e-6  # T2 clamped to 2*T1 - this margin


def sample_descriptors_deployment(n: int, seed: int = 0) -> List[NoiseDescriptor]:
    """
    Sample n NoiseDescriptors from a prior calibrated to observed IBM Heron r2
    deployment ranges. Drop-in replacement for conference_baseline's
    sample_descriptors() in build_training_data calls.

    Prior bounds derived from 20 qubit-observations across 5 calibration
    snapshots (conference Kingston 2026-04-29, Phase 1 Kingston 2026-05-06,
    Phase 2 Kingston/Fez/Marrakesh 2026-05-13):

      T1:          U(100, 500) us  -- observed range 115-443 us
      T2:          T1 * U(0.1, 1.8) -- constructive form guarantees T2 <= 2*T1;
                   observed T2/T1 ratios 0.10-2.105 (one outlier above 1.8 excluded),
                   median 0.89
      gate_error:  U(1e-4, 8e-4)   -- observed range 1.07e-4-7.72e-4
      readout_err: U(0.005, 0.05)  -- observed range 0.0059-0.0396

    Returns List[NoiseDescriptor] (same type as conference sample_descriptors).
    """
    rng = np.random.default_rng(seed)
    out: List[NoiseDescriptor] = []
    for _ in range(n):
        t1 = rng.uniform(T1_LO_US, T1_HI_US, 4)
        t2 = t1 * rng.uniform(T2_RATIO_LO, T2_RATIO_HI, 4)
        # Safety net: enforce qiskit-aer's hard physical constraint T2 <= 2*T1.
        # With T2_RATIO_HI=1.8 this never triggers, but the clamp protects against
        # future widening of the ratio bounds beyond 2.0.
        t2 = np.minimum(t2, 2.0 * t1 - T2_PHYSICAL_MARGIN_US)
        gate = rng.uniform(GATE_ERR_LO, GATE_ERR_HI, 4)
        readout = rng.uniform(READOUT_ERR_LO, READOUT_ERR_HI, 4)
        out.append(NoiseDescriptor(
            t1_times=t1.tolist(),
            t2_times=t2.tolist(),
            gate_errors=gate.tolist(),
            readout_errors=readout.tolist(),
        ))
    return out
