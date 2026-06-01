"""Build Figure 2 for Section 5.C (Attack detection) of the QST journal paper.

Per-attack-type detection rates with 95% confidence intervals, grouped by
hardware anchor (phase 1: 2026-05-06, phase 2: 2026-05-13). Visualizes
that detection is structured by attack family rather than uniform.

Source data: results/phase3/section5A_inputs/task1_binomial_cis.json
             (8 attack_sweep cells; aggregate and federation rows ignored)
Output:      figures/section5C_attack_detection.{pdf,png}
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D


# Publication-bold defaults: heavier strokes, bold weights, vector-safe fonts.
# Matches the Section 5.B figure script.
plt.rcParams.update({
    "font.family": "sans-serif",
    "font.sans-serif": ["DejaVu Sans", "Arial", "Helvetica"],
    "font.weight": "bold",
    "font.size": 10,
    "axes.labelweight": "bold",
    "axes.labelsize": 12,
    "axes.linewidth": 1.6,
    "axes.edgecolor": "#1a1a1a",
    "xtick.labelsize": 10.5,
    "ytick.labelsize": 9.5,
    "xtick.major.width": 1.4,
    "ytick.major.width": 1.4,
    "xtick.major.size": 5.5,
    "ytick.major.size": 5.5,
    "xtick.color": "#1a1a1a",
    "ytick.color": "#1a1a1a",
    "legend.fontsize": 10,
    "savefig.dpi": 300,
    "pdf.fonttype": 42,
    "ps.fonttype": 42,
})


PROJECT_ROOT = Path(__file__).resolve().parents[2]
JSON_PATH = (
    PROJECT_ROOT
    / "data" / "processed" / "section5A"
    / "task1_binomial_cis.json"
)
FIG_DIR = PROJECT_ROOT / "figures" / "final"
PDF_PATH = FIG_DIR / "section5C_attack_detection.pdf"
PNG_PATH = FIG_DIR / "section5C_attack_detection.png"

ATTACK_ORDER = ["uniform_rho", "single_param", "two_param", "random_direction"]
ANCHORS = ["phase1_anchor", "phase2_anchor"]

VALUE_TOL = 1e-4

# Canonical expected values, updated 2026-05-15 to match the authoritative
# JSON. Phase-2 single_param / two_param / random_direction k values were
# revised from an earlier stale spec.
CANONICAL = {
    ("phase1_anchor", "uniform_rho"):
        dict(n=9,  k=0, rate=0.0000, ci_lo=0.0000, ci_hi=0.3363,
             method="clopper_pearson"),
    ("phase1_anchor", "single_param"):
        dict(n=12, k=0, rate=0.0000, ci_lo=0.0000, ci_hi=0.2646,
             method="clopper_pearson"),
    ("phase1_anchor", "two_param"):
        dict(n=4,  k=0, rate=0.0000, ci_lo=0.0000, ci_hi=0.6024,
             method="clopper_pearson"),
    ("phase1_anchor", "random_direction"):
        dict(n=60, k=0, rate=0.0000, ci_lo=0.0000, ci_hi=0.0596,
             method="clopper_pearson"),
    ("phase2_anchor", "uniform_rho"):
        dict(n=9,  k=4, rate=0.4444, ci_lo=0.1370, ci_hi=0.7879,
             method="clopper_pearson"),
    ("phase2_anchor", "single_param"):
        dict(n=12, k=2, rate=0.1667, ci_lo=0.0209, ci_hi=0.4841,
             method="clopper_pearson"),
    ("phase2_anchor", "two_param"):
        dict(n=4,  k=1, rate=0.2500, ci_lo=0.0063, ci_hi=0.8059,
             method="clopper_pearson"),
    ("phase2_anchor", "random_direction"):
        dict(n=60, k=2, rate=0.0333, ci_lo=0.0092, ci_hi=0.1136,
             method="wilson"),
}

COL_PHASE1 = "#F06292"      # bright pink (Material Pink 300)
COL_PHASE2 = "#AD1457"      # deep magenta (Material Pink 900)
COL_PHASE1_EDGE = "#8E2A4B"
COL_PHASE2_EDGE = "#4A0820"
COL_TEXT = "#1A1A1A"        # near-black for annotations
COL_BASELINE = "#3F3F3F"    # near-black gray for y=0 reference


def parse_category(cat: str):
    """Match: attack_sweep:<anchor>:<attack_type>:detection_rate_per_device_eps."""
    parts = cat.split(":")
    if len(parts) != 4 or parts[0] != "attack_sweep":
        return None
    if parts[3] != "detection_rate_per_device_eps":
        return None
    anchor, attack = parts[1], parts[2]
    if anchor not in ANCHORS or attack not in ATTACK_ORDER:
        return None
    return anchor, attack


def load_and_verify():
    if not JSON_PATH.is_file():
        print(f"ERROR: JSON not found at {JSON_PATH}", file=sys.stderr)
        sys.exit(1)

    payload = json.loads(JSON_PATH.read_text())
    cells = {}
    for entry in payload["entries"]:
        key = parse_category(entry["category"])
        if key is None:
            continue
        cells[key] = entry

    missing = set(CANONICAL) - set(cells)
    if missing:
        print(f"ERROR: cells missing from JSON: {sorted(missing)}",
              file=sys.stderr)
        sys.exit(1)

    records = {}
    for key, canon in CANONICAL.items():
        entry = cells[key]
        actual = dict(
            n=int(entry["n"]),
            k=int(entry["k"]),
            rate=float(entry["rate"]),
            ci_lo=float(entry["ci_lo"]),
            ci_hi=float(entry["ci_hi"]),
            method=str(entry["method"]),
        )
        for fld in ("n", "k"):
            if actual[fld] != canon[fld]:
                print(
                    f"ERROR: {key} {fld}: JSON={actual[fld]}, "
                    f"canonical={canon[fld]}. Aborting.",
                    file=sys.stderr,
                )
                sys.exit(1)
        for fld in ("rate", "ci_lo", "ci_hi"):
            if abs(actual[fld] - canon[fld]) > VALUE_TOL:
                print(
                    f"ERROR: {key} {fld}: JSON={actual[fld]:.6f}, "
                    f"canonical={canon[fld]:.4f} (tol {VALUE_TOL}). "
                    f"Aborting.",
                    file=sys.stderr,
                )
                sys.exit(1)
        if actual["method"] != canon["method"]:
            print(
                f"ERROR: {key} method: JSON={actual['method']}, "
                f"canonical={canon['method']}. Aborting.",
                file=sys.stderr,
            )
            sys.exit(1)
        records[key] = actual
    return records


def build_figure(records):
    fig, ax = plt.subplots(figsize=(8.4, 5.0))

    x_offset = 0.20
    phase_props = {
        "phase1_anchor": dict(
            color=COL_PHASE1, edge=COL_PHASE1_EDGE,
            marker="o", offset=-x_offset, markersize=13,
        ),
        "phase2_anchor": dict(
            color=COL_PHASE2, edge=COL_PHASE2_EDGE,
            marker="s", offset=+x_offset, markersize=12,
        ),
    }

    # Baseline reference line at y=0, thicker and darker than default.
    ax.axhline(0.0, color=COL_BASELINE, linestyle=":",
               linewidth=2.0, alpha=0.75, zorder=1)

    for anchor, props in phase_props.items():
        for ai, attack in enumerate(ATTACK_ORDER):
            cell = records[(anchor, attack)]
            rate = cell["rate"]
            ci_lo = cell["ci_lo"]
            ci_hi = cell["ci_hi"]
            # yerr expects (below, above) offsets from the marker.
            yerr = [[max(rate - ci_lo, 0.0)], [max(ci_hi - rate, 0.0)]]
            x = ai + props["offset"]
            ax.errorbar(
                [x], [rate], yerr=yerr,
                marker=props["marker"], markersize=props["markersize"],
                markerfacecolor=props["color"],
                markeredgecolor=props["edge"], markeredgewidth=1.4,
                color=props["color"],
                capsize=7, capthick=2.2, elinewidth=2.6,
                alpha=0.95, linestyle="none", zorder=3,
            )
            # k/n annotation above the upper CI cap. Single neutral color
            # for all cells so anchor identity is signaled by marker only.
            y_offset = 0.04 if rate == 0.0 else 0.03
            ax.text(
                x, ci_hi + y_offset, f"{cell['k']}/{cell['n']}",
                ha="center", va="bottom",
                fontsize=11, fontweight="bold", color=COL_TEXT,
            )

    ax.set_xticks(list(range(len(ATTACK_ORDER))))
    ax.set_xticklabels(ATTACK_ORDER, fontweight="bold")
    for label in ax.get_yticklabels():
        label.set_fontweight("bold")
    ax.set_ylabel("detection rate", fontweight="bold")
    ax.set_ylim(0.0, 1.0)
    ax.set_yticks([0.0, 0.2, 0.4, 0.6, 0.8, 1.0])
    ax.set_xlim(-0.5, len(ATTACK_ORDER) - 0.5)
    ax.yaxis.grid(True, alpha=0.28, linestyle=":", linewidth=1.0,
                  color="#666666")
    ax.set_axisbelow(True)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_linewidth(1.6)
    ax.spines["bottom"].set_linewidth(1.6)

    legend_handles = [
        Line2D(
            [0], [0], marker="o", color="w",
            markerfacecolor=COL_PHASE1, markeredgecolor=COL_PHASE1_EDGE,
            markersize=14, markeredgewidth=1.4,
            label="phase 1 anchor (2026-05-06)",
        ),
        Line2D(
            [0], [0], marker="s", color="w",
            markerfacecolor=COL_PHASE2, markeredgecolor=COL_PHASE2_EDGE,
            markersize=13, markeredgewidth=1.4,
            label="phase 2 anchor (2026-05-13)",
        ),
    ]
    # Legend placed ABOVE the axes so it cannot occlude any annotation,
    # error bar, or marker. The phase-2 two_param CI reaches ci_hi=0.806,
    # which would risk collision with an inside-axes legend.
    legend = ax.legend(
        handles=legend_handles,
        loc="lower center", bbox_to_anchor=(0.5, 1.02),
        ncol=2, frameon=False, fontsize=10.5,
        handletextpad=0.6, columnspacing=3.0,
    )
    for txt in legend.get_texts():
        txt.set_fontweight("bold")

    fig.tight_layout(pad=0.9)
    return fig


def main():
    records = load_and_verify()
    fig = build_figure(records)

    FIG_DIR.mkdir(parents=True, exist_ok=True)
    fig.savefig(PDF_PATH, dpi=300, bbox_inches="tight")
    fig.savefig(PNG_PATH, dpi=300, bbox_inches="tight")
    plt.close(fig)

    print("Figure saved to figures/section5C_attack_detection.{pdf,png}")
    print("Detection rates and CIs per cell:")
    for anchor in ANCHORS:
        ph = "p1" if anchor == "phase1_anchor" else "p2"
        for attack in ATTACK_ORDER:
            cell = records[(anchor, attack)]
            print(
                f"  {ph} {attack:18s} "
                f"k/n={cell['k']}/{cell['n']:<3d} "
                f"rate={cell['rate']:.4f}  "
                f"CI=[{cell['ci_lo']:.4f}, {cell['ci_hi']:.4f}]  "
                f"({cell['method']})"
            )
    return 0


if __name__ == "__main__":
    sys.exit(main())
