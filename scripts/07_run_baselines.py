"""Reproduce the Section 5.F baseline-comparison table (B0 / B2 / B3).

Reads:
  data/processed/section5F/task1_aggregates.json
  data/processed/section5F/task3_mcnemar.json
  data/processed/section5F/task4_completeness.json

Writes tables/generated/section5F_baselines_table.{md,csv}.

Run:
    python scripts/07_run_baselines.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "conference_baseline_snapshot" / "src"))


def main() -> int:
    base = ROOT / "data" / "processed" / "section5F"
    t1 = json.loads((base / "task1_aggregates.json").read_text())
    t3 = json.loads((base / "task3_mcnemar.json").read_text())
    t4 = json.loads((base / "task4_completeness.json").read_text())

    # Build aggregate table B0/B2/B3 x phase1/phase2
    by_pair = {(e["baseline"], e["anchor"]): e for e in t1["entries"]}

    lines = [
        "# Section 5.F - Baseline comparison",
        "",
        "## Aggregate detection (170 paired attacks: 85 phase 1 + 85 phase 2)",
        "",
        "| Baseline | Phase | k/n | Rate | 95% CI | Method |",
        "|---|---|---|---:|---|---|",
    ]
    csv = ["baseline,anchor,n,k,rate,ci_lo,ci_hi,method"]
    headline = []

    for baseline in ("B0", "B2", "B3"):
        for anchor in ("phase1_anchor", "phase2_anchor"):
            if (baseline, anchor) not in by_pair:
                continue
            e = by_pair[(baseline, anchor)]
            lines.append(
                f"| {baseline} | {anchor.replace('_anchor','')} | "
                f"{e['k']}/{e['n']} | {e['rate']:.4f} | "
                f"[{e['ci_95_lo']:.4f}, {e['ci_95_hi']:.4f}] | {e['method']} |"
            )
            csv.append(f"{baseline},{anchor},{e['n']},{e['k']},"
                       f"{e['rate']:.6f},{e['ci_95_lo']:.6f},"
                       f"{e['ci_95_hi']:.6f},{e['method']}")
        # Compute combined aggregate per baseline
        rows = [by_pair[(baseline, a)] for a in ("phase1_anchor", "phase2_anchor")
                if (baseline, a) in by_pair]
        if len(rows) == 2:
            agg_n = rows[0]["n"] + rows[1]["n"]
            agg_k = rows[0]["k"] + rows[1]["k"]
            headline.append(f"  {baseline}: {agg_k}/{agg_n} aggregate")

    lines += ["", "## Paired McNemar tests (vs B0)", ""]
    lines += ["| Comparison | n11 | n10 | n01 | n00 | discordant | exact McNemar p |",
              "|---|---:|---:|---:|---:|---:|---:|"]
    csv_mc = ["comparison,n11,n10,n01,n00,discordant,p_value"]
    for c in t3.get("comparisons", [t3]):
        if "comparison" not in c:
            continue
        cid = c["comparison"]
        # n10/n01 keys vary by which baseline we compared
        n10 = c.get("n10_b0_only_flag", c.get("n10", 0))
        n01 = c.get("n01_b2_only_flag",
                    c.get("n01_b3_only_flag", c.get("n01", 0)))
        n11 = c["n11_both_flag"]
        n00 = c["n00_neither_flag"]
        disc = c.get("discordant_pairs", n10 + n01)
        p = c["mcnemar_exact_p_value_two_sided"]
        lines.append(
            f"| {cid} | {n11} | {n10} | {n01} | {n00} | {disc} | {p:.6g} |"
        )
        csv_mc.append(f"{cid},{n11},{n10},{n01},{n00},{disc},{p:.6g}")
        headline.append(f"  {cid}: discordant=({n10},{n01}), p={p:.4g}")

    lines += ["", "## In-sample completeness on Fez", ""]
    lines += ["| Baseline | Margin | Passes in-sample? |",
              "|---|---:|---|"]
    for e in t4["entries"]:
        verdict = "yes" if e.get("passes_in_sample") else "**no**"
        margin = e.get("margin", float("nan"))
        lines.append(f"| {e['baseline']} | {margin:+.5f} | {verdict} |")
        headline.append(
            f"  {e['baseline']} Fez margin = {margin:+.5f} "
            f"({'pass' if e.get('passes_in_sample') else 'FAIL'})"
        )

    out_md = ROOT / "tables" / "generated" / "section5F_baselines_table.md"
    out_csv = ROOT / "tables" / "generated" / "section5F_baselines_table.csv"
    out_csv2 = ROOT / "tables" / "generated" / "section5F_mcnemar_table.csv"
    out_md.parent.mkdir(parents=True, exist_ok=True)
    out_md.write_text("\n".join(lines), encoding="utf-8")
    out_csv.write_text("\n".join(csv), encoding="utf-8")
    out_csv2.write_text("\n".join(csv_mc), encoding="utf-8")
    print("[07] Baseline comparison (Section 5.F):")
    for line in headline:
        print(line)
    print(f"     -> {out_md.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
