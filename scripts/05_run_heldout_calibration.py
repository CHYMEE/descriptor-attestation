"""Reproduce the Section 5.E held-out calibration tables.

Reads:
  - data/processed/section5E/task4_replicated.json  (30-instance K=2 on Fez)
  - data/processed/section5E_threshold/experiment1_values.json
      (K=2 LOO across all 3 configs)
  - data/processed/section5E_threshold/experiment2_values.json
      (K=3 calibration with 5 synthetic test descriptors x 30 instances)

Writes:
  tables/generated/section5E_threshold_table.{md,csv}

Run:
    python scripts/05_run_heldout_calibration.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "conference_baseline_snapshot" / "src"))


def main() -> int:
    e1 = json.loads(
        (ROOT / "data" / "processed" / "section5E_threshold"
         / "experiment1_values.json").read_text()
    )
    e2 = json.loads(
        (ROOT / "data" / "processed" / "section5E_threshold"
         / "experiment2_values.json").read_text()
    )

    pretty_dev = {"ibm_kingston": "Kingston", "ibm_fez": "Fez",
                  "ibm_marrakesh": "Marrakesh"}

    lines = [
        "# Section 5.E - Held-out calibration threshold characterization",
        "",
        "## Experiment 1: Leave-one-out K=2",
        "",
        "| Config | Calibration | Held-out | Passes | Mean margin | 95% bootstrap CI |",
        "|---|---|---|---:|---:|---|",
    ]
    csv = ["experiment,config,calib,test,n,passes,mean_margin,ci_lo,ci_hi"]
    headline = []

    for cid in sorted(e1["summary"].keys()):
        s = e1["summary"][cid]
        calib = "{" + ", ".join(pretty_dev[b] for b in s["calib_backends"]) + "}"
        test = pretty_dev[s["test_backend"]]
        ci = s["bootstrap_95_ci_mean"]
        lines.append(
            f"| {cid} | {calib} | {test} | "
            f"{s['passes']}/{s['n_instances']} | "
            f"{s['mean_margin']:+.4f} | [{ci[0]:+.4f}, {ci[1]:+.4f}] |"
        )
        csv.append(
            f"experiment1,{cid},{calib},{test},{s['n_instances']},"
            f"{s['passes']},{s['mean_margin']:+.6f},{ci[0]:+.6f},{ci[1]:+.6f}"
        )
        headline.append(
            f"  {cid} ({calib} -> held-out {test}): "
            f"{s['passes']}/{s['n_instances']} pass, "
            f"mean={s['mean_margin']:+.4f}"
        )

    lines += [
        "",
        "## Experiment 2: K=3 calibration, 5 synthetic test descriptors x 30 instances",
        "",
        "| Test desc seed | Passes | Mean margin | 95% bootstrap CI |",
        "|---|---:|---:|---|",
    ]
    for k in sorted(e2["summary"]["per_descriptor"].keys()):
        s = e2["summary"]["per_descriptor"][k]
        ci = s["bootstrap_95_ci_mean"]
        lines.append(
            f"| {k.replace('seed_', '')} | {s['passes']}/{s['n_instances']} "
            f"| {s['mean_margin']:+.4f} | "
            f"[{ci[0]:+.4f}, {ci[1]:+.4f}] |"
        )
        csv.append(
            f"experiment2,{k},K3,synthetic,{s['n_instances']},"
            f"{s['passes']},{s['mean_margin']:+.6f},{ci[0]:+.6f},{ci[1]:+.6f}"
        )

    agg = e2["summary"]["aggregate"]
    if agg:
        ci = agg["bootstrap_95_ci_mean"]
        lines.append(
            f"| **AGGREGATE** | **{agg['passes']}/{agg['n_cells']}** | "
            f"{agg['mean_margin']:+.4f} | "
            f"[{ci[0]:+.4f}, {ci[1]:+.4f}] |"
        )
        csv.append(
            f"experiment2,AGGREGATE,K3,synthetic,{agg['n_cells']},"
            f"{agg['passes']},{agg['mean_margin']:+.6f},{ci[0]:+.6f},{ci[1]:+.6f}"
        )
        headline.append(
            f"  K=3 synthetic aggregate: {agg['passes']}/{agg['n_cells']} pass, "
            f"mean margin={agg['mean_margin']:+.4f}"
        )

    out_md = ROOT / "tables" / "generated" / "section5E_threshold_table.md"
    out_csv = ROOT / "tables" / "generated" / "section5E_threshold_table.csv"
    out_md.parent.mkdir(parents=True, exist_ok=True)
    out_md.write_text("\n".join(lines), encoding="utf-8")
    out_csv.write_text("\n".join(csv), encoding="utf-8")
    print("[05] Held-out calibration (Section 5.E):")
    for line in headline:
        print(line)
    print(f"     -> {out_md.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
