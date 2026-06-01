"""Reproduce attack-detection breakdown (Section 5.C).

Reads attack-sweep records and computes per-anchor / per-attack-type
detection counts with Wilson / Clopper-Pearson 95% CIs.

Run:
    python scripts/04_run_attack_analysis.py
"""
from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "conference_baseline_snapshot" / "src"))

from descriptor_attestation.statistics import binomial_ci  # noqa: E402

ANCHORS = ("phase1_anchor", "phase2_anchor")
ATTACK_FAMILIES = ("uniform_rho", "single_param", "two_param", "random_direction")


def main() -> int:
    src = ROOT / "data" / "raw" / "attacks" / "attack_sweep_records.json"
    payload = json.loads(src.read_text())

    lines = [
        "# Section 5.C - Attack-detection rates (per-device-eps baseline)",
        "",
        "Wilson 95% CI when n >= 20 AND k not in {0, n}; "
        "Clopper-Pearson otherwise.",
        "",
    ]
    csv = ["anchor,attack_family,n,k,rate,ci_lo,ci_hi,method"]
    headline_lines = []

    for anchor in ANCHORS:
        a = payload["per_anchor"][anchor]
        records = a["records"]
        tot = Counter()
        det = Counter()
        for r in records:
            tot[r["attack_type"]] += 1
            if r["flagged_per_device_epsilon"]:
                det[r["attack_type"]] += 1

        # Aggregate
        agg_n = sum(tot.values())
        agg_k = sum(det.values())
        agg_ci, agg_method = binomial_ci(agg_k, agg_n)
        lines += [
            f"## {anchor}",
            "",
            "| Attack family | k/n | Rate | 95% CI | Method |",
            "|---|---|---:|---|---|",
        ]
        for fam in ATTACK_FAMILIES:
            n = tot[fam]
            k = det[fam]
            ci, method = binomial_ci(k, n)
            rate = k / n if n else 0.0
            lines.append(
                f"| {fam} | {k}/{n} | {rate:.4f} | "
                f"[{ci[0]:.4f}, {ci[1]:.4f}] | {method} |"
            )
            csv.append(f"{anchor},{fam},{n},{k},{rate:.6f},"
                       f"{ci[0]:.6f},{ci[1]:.6f},{method}")
        lines.append(
            f"| **AGGREGATE** | **{agg_k}/{agg_n}** | {agg_k/agg_n:.4f} | "
            f"[{agg_ci[0]:.4f}, {agg_ci[1]:.4f}] | {agg_method} |"
        )
        csv.append(f"{anchor},AGGREGATE,{agg_n},{agg_k},{agg_k/agg_n:.6f},"
                   f"{agg_ci[0]:.6f},{agg_ci[1]:.6f},{agg_method}")
        lines.append("")
        headline_lines.append(
            f"  {anchor}: {agg_k}/{agg_n} detected "
            f"(per-family: uniform_rho={det['uniform_rho']}/{tot['uniform_rho']}, "
            f"single_param={det['single_param']}/{tot['single_param']}, "
            f"two_param={det['two_param']}/{tot['two_param']}, "
            f"random_direction={det['random_direction']}/{tot['random_direction']})"
        )

    out_md = ROOT / "tables" / "generated" / "section5C_attack_detection_table.md"
    out_csv = ROOT / "tables" / "generated" / "section5C_attack_detection_table.csv"
    out_md.parent.mkdir(parents=True, exist_ok=True)
    out_md.write_text("\n".join(lines), encoding="utf-8")
    out_csv.write_text("\n".join(csv), encoding="utf-8")

    print("[04] Attack detection (Section 5.C):")
    for line in headline_lines:
        print(line)
    print(f"     -> {out_md.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
