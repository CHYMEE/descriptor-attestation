"""Verify Wilson, Clopper-Pearson, McNemar, bootstrap mean-CI."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "conference_baseline_snapshot" / "src"))

from descriptor_attestation.statistics import (
    wilson_ci,
    clopper_pearson_ci,
    binomial_ci,
    mcnemar_exact_two_sided,
    bootstrap_mean_ci,
)


def test_wilson_known_values():
    # n=85, k=20 (Section 5.F, B2 phase 2) -> manuscript CI [0.158, 0.336]
    lo, hi = wilson_ci(20, 85)
    assert 0.155 < lo < 0.162
    assert 0.330 < hi < 0.340


def test_clopper_pearson_known_values():
    # n=4, k=1 (Section 5.F two_param B0 phase 2) -> CI [0.006, 0.806]
    lo, hi = clopper_pearson_ci(1, 4)
    assert 0.004 < lo < 0.008
    assert 0.800 < hi < 0.810


def test_binomial_ci_selector_uses_wilson_for_large_n():
    (_, _), method = binomial_ci(20, 85)
    assert method == "wilson"


def test_binomial_ci_selector_uses_cp_for_small_n():
    (_, _), method = binomial_ci(0, 4)
    assert method == "clopper_pearson"


def test_binomial_ci_selector_uses_cp_for_k_zero():
    (_, _), method = binomial_ci(0, 85)
    assert method == "clopper_pearson"


def test_mcnemar_b2_vs_b0_manuscript():
    # Section 5.F B2 vs B0: n10=0, n01=13 -> p = 2*0.5^13 = 2.4e-4
    p = mcnemar_exact_two_sided(0, 13)
    assert 0.00024 < p < 0.00025


def test_mcnemar_b3_vs_b0_manuscript():
    # Section 5.F B3 vs B0: n10=6, n01=29 -> p ~ 1.2e-4
    p = mcnemar_exact_two_sided(6, 29)
    assert 0.0001 < p < 0.0002


def test_bootstrap_mean_ci_deterministic_seed():
    # Same seed -> identical CIs.
    vals = [-0.02, -0.018, -0.022, -0.019, -0.021] * 6
    lo1, hi1 = bootstrap_mean_ci(vals, seed=46)
    lo2, hi2 = bootstrap_mean_ci(vals, seed=46)
    assert lo1 == lo2 and hi1 == hi2
