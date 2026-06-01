"""Verify epsilon_Hoeffding and per-device threshold values."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "conference_baseline_snapshot" / "src"))

from descriptor_attestation import hoeffding_bound


def test_hoeffding_50_1024_001():
    """Manuscript: epsilon_H(N=50, S=1024, delta=0.01) approx 0.1341."""
    val = hoeffding_bound(50, 1024, 0.01)
    assert abs(val - 0.1341228766430842) < 1e-9, (
        f"expected 0.13412..., got {val}"
    )


def test_per_device_epsilon_table():
    """Verify cached per-device epsilon decomposition matches manuscript."""
    src = (ROOT / "data" / "raw" / "calibration"
           / "per_device_epsilon_demo.json")
    payload = json.loads(src.read_text())
    expected = {
        "ibm_kingston":  {"eps_pred": 0.0357, "eps_model": 0.0000,
                          "eps_device": 0.1698, "max_dev_hw": 0.1193},
        "ibm_fez":       {"eps_pred": 0.0376, "eps_model": 0.0092,
                          "eps_device": 0.1809, "max_dev_hw": 0.1809},
        "ibm_marrakesh": {"eps_pred": 0.0386, "eps_model": 0.0000,
                          "eps_device": 0.1727, "max_dev_hw": 0.1233},
    }
    for entry in payload["per_device"]:
        dev = entry["device"]
        exp = expected[dev]
        for key, src_key in [
            ("eps_pred", "epsilon_pred"),
            ("eps_model", "epsilon_model"),
            ("eps_device", "epsilon_device"),
            ("max_dev_hw", "max_dev_hw"),
        ]:
            actual = float(entry[src_key])
            target = exp[key]
            assert abs(actual - target) < 1e-3, (
                f"{dev} {src_key}: cached={actual:.4f}, "
                f"manuscript={target:.4f}"
            )
