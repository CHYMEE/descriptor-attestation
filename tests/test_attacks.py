"""Verify attack-family counts and Section 5.C detection numbers."""
from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "conference_baseline_snapshot" / "src"))


def test_attack_family_counts():
    src = ROOT / "data" / "raw" / "attacks" / "attack_sweep_records.json"
    payload = json.loads(src.read_text())
    expected = {
        "uniform_rho": 9,
        "single_param": 12,
        "two_param": 4,
        "random_direction": 60,
    }
    for anchor in ("phase1_anchor", "phase2_anchor"):
        records = payload["per_anchor"][anchor]["records"]
        counts = Counter(r["attack_type"] for r in records)
        assert counts == expected, (
            f"{anchor} family counts {counts} != expected {expected}"
        )


def test_phase2_detection_counts():
    src = ROOT / "data" / "raw" / "attacks" / "attack_sweep_records.json"
    payload = json.loads(src.read_text())
    records = payload["per_anchor"]["phase2_anchor"]["records"]
    by_fam = Counter()
    for r in records:
        if r["flagged_per_device_epsilon"]:
            by_fam[r["attack_type"]] += 1
    # Manuscript: 4/9 uniform, 2/12 single, 1/4 two, 2/60 random
    assert by_fam["uniform_rho"] == 4
    assert by_fam["single_param"] == 2
    assert by_fam["two_param"] == 1
    assert by_fam["random_direction"] == 2
    # Aggregate phase 2 = 9
    assert sum(by_fam.values()) == 9


def test_phase1_detection_counts_zero():
    src = ROOT / "data" / "raw" / "attacks" / "attack_sweep_records.json"
    payload = json.loads(src.read_text())
    records = payload["per_anchor"]["phase1_anchor"]["records"]
    flagged = sum(1 for r in records if r["flagged_per_device_epsilon"])
    # Manuscript: 0/85 detection at phase 1 under per-device-eps.
    assert flagged == 0
