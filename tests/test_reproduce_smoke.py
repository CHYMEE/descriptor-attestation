"""Smoke test for scripts/03..07_*.py (no AerSim required).

These scripts read cached data only; they should run in < 5 seconds total
and write expected outputs to tables/generated/.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

QUICK_SCRIPTS = [
    "scripts/03_compute_thresholds.py",
    "scripts/04_run_attack_analysis.py",
    "scripts/05_run_heldout_calibration.py",
    "scripts/06_run_scaling_analysis.py",
    "scripts/07_run_baselines.py",
]


def _run(script: str):
    return subprocess.run(
        [sys.executable, "-W", "ignore", script],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        timeout=60,
    )


def test_each_table_script_exits_zero():
    for script in QUICK_SCRIPTS:
        result = _run(script)
        assert result.returncode == 0, (
            f"{script} failed: {result.stderr[-400:]}"
        )


def test_expected_output_files_exist():
    expected = [
        "tables/generated/section5B_completeness_table.md",
        "tables/generated/section5C_attack_detection_table.md",
        "tables/generated/section5D_scaling_table.md",
        "tables/generated/section5E_threshold_table.md",
        "tables/generated/section5F_baselines_table.md",
    ]
    # Run the scripts to ensure outputs land.
    for script in QUICK_SCRIPTS:
        _run(script)
    for rel in expected:
        path = ROOT / rel
        assert path.is_file(), f"missing {rel}"
        assert path.stat().st_size > 0, f"empty {rel}"
