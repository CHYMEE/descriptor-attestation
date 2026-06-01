"""Reproduce the Section 5.D federation-scaling table.

Reads task5b_aggregated_scaling.json and reports per-N Type-I rate +
Wilson upper CI vs delta=0.05.

Run:
    python scripts/06_run_scaling_analysis.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "conference_baseline_snapshot" / "src"))


def main() -> int:
    src = ROOT / "data" / "processed" / "section5D" / "task5b_aggregated_scaling.json"
    payload = json.loads(src.read_text())

    lines = [
        "# Section 5.D - Federation scaling (Type I error rate vs N)",
        "",
        "| N | n_device_evals | k_flagged | Type I rate | Wilson upper 95% CI | "
        "Passes (<=0.05)? |",
        "|---:|---:|---:|---:|---:|---|",
    ]
    csv = ["N,n_device_evals,k_flagged,type_I_rate,wilson_upper,passes"]
    headline = []

    for entry in payload["per_N"]:
        N = entry["N"]
        n = entry["n_device_evaluations"]
        k = entry["k_flagged"]
        rate = entry["type_I_rate"]
        upper = entry["wilson_upper_ci"]
        passes = "yes" if entry["passes_wilson_upper_le_delta"] else "**no**"
        lines.append(
            f"| {N} | {n} | {k} | {rate:.4f} | {upper:.4f} | {passes} |"
        )
        csv.append(f"{N},{n},{k},{rate:.6f},{upper:.6f},"
                   f"{entry['passes_wilson_upper_le_delta']}")
        headline.append(
            f"  N={N}: k/n={k}/{n}, type_I_rate={rate:.4f}, "
            f"Wilson upper={upper:.4f} ({'pass' if entry['passes_wilson_upper_le_delta'] else 'fail'})"
        )

    out_md = ROOT / "tables" / "generated" / "section5D_scaling_table.md"
    out_csv = ROOT / "tables" / "generated" / "section5D_scaling_table.csv"
    out_md.parent.mkdir(parents=True, exist_ok=True)
    out_md.write_text("\n".join(lines), encoding="utf-8")
    out_csv.write_text("\n".join(csv), encoding="utf-8")
    print("[06] Federation scaling (Section 5.D):")
    for line in headline:
        print(line)
    print(f"     -> {out_md.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
