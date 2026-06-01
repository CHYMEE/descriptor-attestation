"""Closed-form statistical primitives used across the journal extension.

All functions are deterministic given their inputs (or take an explicit
RNG seed for bootstrap). No statsmodels dependency.
"""
from __future__ import annotations

import math
from typing import Tuple

import numpy as np
from scipy.stats import beta, binom, norm


def wilson_ci(k: int, n: int, alpha: float = 0.05) -> Tuple[float, float]:
    """Wilson score interval. Use when n >= 20 and k not in {0, n}."""
    if n == 0:
        return (0.0, 1.0)
    z = norm.ppf(1 - alpha / 2)
    p = k / n
    denom = 1.0 + z ** 2 / n
    center = (p + z ** 2 / (2 * n)) / denom
    half = (z / denom) * math.sqrt(p * (1 - p) / n + z ** 2 / (4 * n ** 2))
    return (max(0.0, center - half), min(1.0, center + half))


def clopper_pearson_ci(k: int, n: int, alpha: float = 0.05) -> Tuple[float, float]:
    """Clopper-Pearson exact interval. Use when n < 20 or k in {0, n}."""
    if n == 0:
        return (0.0, 1.0)
    lo = 0.0 if k == 0 else float(beta.ppf(alpha / 2, k, n - k + 1))
    hi = 1.0 if k == n else float(beta.ppf(1 - alpha / 2, k + 1, n - k))
    return (lo, hi)


def binomial_ci(k: int, n: int, alpha: float = 0.05) -> Tuple[Tuple[float, float], str]:
    """Wilson when n >= 20 AND k not in {0, n}; otherwise Clopper-Pearson.

    Returns ((lo, hi), method_label).
    """
    if n >= 20 and k not in (0, n):
        return wilson_ci(k, n, alpha), "wilson"
    return clopper_pearson_ci(k, n, alpha), "clopper_pearson"


def mcnemar_exact_two_sided(b: int, c: int) -> float:
    """Exact two-sided McNemar p-value on discordant counts (b, c).

    p = 2 * P(X <= min(b,c) | X ~ Binomial(b+c, 0.5)), capped at 1.
    """
    n = b + c
    if n == 0:
        return 1.0
    smaller = min(b, c)
    one_tail = sum(binom.pmf(i, n, 0.5) for i in range(smaller + 1))
    return float(min(1.0, 2.0 * one_tail))


def bootstrap_mean_ci(
    values, n_boot: int = 2000, alpha: float = 0.05, seed: int = 46
) -> Tuple[float, float]:
    """Percentile bootstrap CI on the mean of `values`."""
    arr = np.asarray(values, dtype=np.float64)
    if arr.size == 0:
        return (float("nan"), float("nan"))
    rng = np.random.default_rng(seed)
    means = np.empty(n_boot, dtype=np.float64)
    for i in range(n_boot):
        idx = rng.integers(0, arr.size, size=arr.size)
        means[i] = arr[idx].mean()
    lo = float(np.percentile(means, 100 * alpha / 2))
    hi = float(np.percentile(means, 100 * (1 - alpha / 2)))
    return (lo, hi)
