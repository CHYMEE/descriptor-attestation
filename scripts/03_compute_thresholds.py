"""Compute Hoeffding term and per-device epsilon table.

Reads the cached per-device epsilon decomposition produced for §5.B and
reports the manuscript completeness table (Kingston / Fez / Marrakesh
eps_pred, eps_model, eps_device, max_dev_hw, margin).

Run:
    python scripts/03_compute_thresholds.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "conference_baseline_snapshot" / "src"))

from descriptor_attestation import hoeffding_bound  # noqa: E402


def main() -> int:
    src = ROOT / "data" / "raw" / "calibration" / "per_device_epsilon_demo.json"
    payload = json.loads(src.read_text())
    eps_h_cfg = float(payload["config"]["epsilon_Hoeffding"])
    eps_h_recomputed = float(hoeffding_bound(50, 1024, 0.01))
    assert abs(eps_h_cfg - eps_h_recomputed) < 1e-9, (
        f"epsilon_Hoeffding mismatch: cached={eps_h_cfg}, "
        f"recomputed={eps_h_recomputed}"
    )

    lines = [
        "# Section 5.B - Per-device completeness table",
        "",
        f"epsilon_Hoeffding (N=50, S=1024, delta=0.01) = {eps_h_cfg:.6f} "
        f"(manuscript: 0.1341)",
        "",
        "| Device | eps_pred | eps_model | eps_device | max_dev_hw | Margin | Verdict |",
        "|---|---:|---:|---:|---:|---:|---|",
    ]
    csv = ["device,eps_pred,eps_model,eps_device,max_dev_hw,margin,verdict"]
    headline = []
    for entry in payload["per_device"]:
        dev = entry["device"]
        eps_pred = entry["epsilon_pred"]
        eps_model = entry["epsilon_model"]
        eps_dev = entry["epsilon_device"]
        max_dev = entry["max_dev_hw"]
        margin = eps_dev - max_dev
        verdict = "Pass" if margin >= -1e-9 else "FAIL"
        lines.append(
            f"| {dev} | {eps_pred:.4f} | {eps_model:.4f} | {eps_dev:.4f} | "
            f"{max_dev:.4f} | {margin:+.4f} | {verdict} |"
        )
        csv.append(f"{dev},{eps_pred:.6f},{eps_model:.6f},{eps_dev:.6f},"
                    f"{max_dev:.6f},{margin:+.6f},{verdict}")
        headline.append(
            f"  {dev:14s} eps_pred={eps_pred:.4f} eps_model={eps_model:.4f} "
            f"eps_device={eps_dev:.4f} max_dev={max_dev:.4f} margin={margin:+.4f}"
        )

    out_md = ROOT / "tables" / "generated" / "section5B_completeness_table.md"
    out_csv = ROOT / "tables" / "generated" / "section5B_completeness_table.csv"
    out_md.parent.mkdir(parents=True, exist_ok=True)
    out_md.write_text("\n".join(lines), encoding="utf-8")
    out_csv.write_text("\n".join(csv), encoding="utf-8")

    print("[03] Per-device completeness (Section 5.B):")
    for line in headline:
        print(line)
    print(f"     epsilon_Hoeffding(50, 1024, 0.01) = {eps_h_cfg:.6f}")
    print(f"     -> {out_md.relative_to(ROOT)}, {out_csv.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
