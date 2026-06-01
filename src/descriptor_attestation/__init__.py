"""descriptor-attestation: reproduction package.

Thin wrapper that re-exports the conference-baseline qem modules from the
snapshot subdirectory, plus journal-extension utilities for thresholds,
attacks, statistics, baselines, and plotting.

Public API:
  Re-exported from conference_baseline_snapshot.src.qem (frozen):
    NoiseDescriptor, QuantumDevice, create_honest_device, WitnessSet,
    WitnessPredictor, build_training_data, hoeffding_bound, detect
  Journal-extension submodules:
    deployment_prior  - broader-T1 prior used for journal predictor training
    statistics        - Wilson / Clopper-Pearson / McNemar / bootstrap mean CI
"""
from __future__ import annotations

import sys
from pathlib import Path

# Make the bundled conference snapshot importable so users don't need
# `pip install -e conference_baseline_snapshot/`. This keeps the journal
# extension fully self-contained.
_PROJECT_ROOT = Path(__file__).resolve().parents[2]
_SNAPSHOT_SRC = _PROJECT_ROOT / "conference_baseline_snapshot" / "src"
if _SNAPSHOT_SRC.is_dir():
    sys.path.insert(0, str(_SNAPSHOT_SRC))

from qem import (  # type: ignore  # noqa: E402
    WitnessSet,
    WitnessPredictor,
    build_training_data,
)
from qem.attestation import hoeffding_bound, detect  # type: ignore  # noqa: E402
from qem.descriptor import NoiseDescriptor  # type: ignore  # noqa: E402
from qem.device import QuantumDevice, create_honest_device  # type: ignore  # noqa: E402

from . import deployment_prior, statistics  # noqa: F401, E402

__all__ = [
    "NoiseDescriptor",
    "QuantumDevice",
    "create_honest_device",
    "WitnessSet",
    "WitnessPredictor",
    "build_training_data",
    "hoeffding_bound",
    "detect",
    "deployment_prior",
    "statistics",
]
__version__ = "0.1.0"
