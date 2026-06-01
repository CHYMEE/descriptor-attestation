"""Build Figure 1 for Section 5.B (Completeness) of the QST journal paper.

Anchor visualization of the per-device completeness bound from Theorem 1,
rendered as a vertical dumbbell plot. For each of the three real IBM
Heron r2 backends, plots:

  - a filled circle at max_dev_hw(d)            (measured)
  - a filled diamond at epsilon_device(d)       (per-device bound)
  - a gray segment connecting the two           (length = margin)
  - a shared horizontal dashed reference line at epsilon_Hoeffding

The legend is placed above the axes (ncol=3) so it cannot occlude any
data element. The Fez pair collapses to overlapping markers, making the
in-sample tautology (margin = +0.0000) visually unmistakable.

Source data is loaded from a single predictor-instance JSON (instance A).
Do NOT mix with values from Task 3 bootstrap output or any other JSON: those
correspond to a different predictor instance and pairing them would produce
incoherent per-device values.

NOTE on source path: the original drafting spec referenced
results/phase3/final_results/per_device_epsilon_demo.json, but the file
actually lives in results/phase3/completeness_analysis/. The canonical
path is the one used below.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import Patch


# Publication-bold defaults: heavier strokes, bold weights, vector-safe fonts.
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
    / "data" / "raw" / "calibration"
    / "per_device_epsilon_demo.json"
)
FIG_DIR = PROJECT_ROOT / "figures" / "final"
PDF_PATH = FIG_DIR / "section5B_completeness.pdf"
PNG_PATH = FIG_DIR / "section5B_completeness.png"

DEVICE_ORDER = ["ibm_kingston", "ibm_fez", "ibm_marrakesh"]

EPSILON_H_EXPECTED = 0.1341
EPSILON_H_TOL = 1e-3
VALUE_TOL = 1e-4

CANONICAL = {
    "ibm_kingston":  {"max_dev_hw": 0.1193, "epsilon_pred": 0.0357,
                      "epsilon_model": 0.0000, "epsilon_device": 0.1698},
    "ibm_fez":       {"max_dev_hw": 0.1809, "epsilon_pred": 0.0376,
                      "epsilon_model": 0.0092, "epsilon_device": 0.1809},
    "ibm_marrakesh": {"max_dev_hw": 0.1233, "epsilon_pred": 0.0386,
                      "epsilon_model": 0.0000, "epsilon_device": 0.1727},
}

COL_BAR = "#1565C0"        # vivid, paper-grade blue (Material 800)
COL_THR = "#C62828"        # vivid, deep red
COL_HOEFF = "#3F3F3F"      # near-black gray for the reference line
COL_CONNECT = "#4A5560"    # dark slate connector
COL_TEXT = "#1A1A1A"       # near-black for annotations (uniform across devices)


def load_and_verify():
    if not JSON_PATH.is_file():
        print(f"ERROR: JSON not found at {JSON_PATH}", file=sys.stderr)
        sys.exit(1)

    payload = json.loads(JSON_PATH.read_text())
    per_device = {entry["device"]: entry for entry in payload["per_device"]}

    missing = [d for d in DEVICE_ORDER if d not in per_device]
    if missing:
        print(f"ERROR: devices missing from JSON: {missing}", file=sys.stderr)
        sys.exit(1)

    records = []
    for device in DEVICE_ORDER:
        entry = per_device[device]
        for field in ("max_dev_hw", "epsilon_pred",
                      "epsilon_model", "epsilon_device"):
            actual = float(entry[field])
            expected = CANONICAL[device][field]
            if abs(actual - expected) > VALUE_TOL:
                print(
                    f"ERROR: {device}.{field} = {actual:.6f}, expected "
                    f"{expected:.4f} (tol {VALUE_TOL}). Aborting.",
                    file=sys.stderr,
                )
                sys.exit(1)
        records.append({
            "device": device,
            "max_dev_hw": float(entry["max_dev_hw"]),
            "epsilon_pred": float(entry["epsilon_pred"]),
            "epsilon_model": float(entry["epsilon_model"]),
            "epsilon_device": float(entry["epsilon_device"]),
        })

    eps_h = float(payload["config"]["epsilon_Hoeffding"])
    if abs(eps_h - EPSILON_H_EXPECTED) > EPSILON_H_TOL:
        print(
            f"ERROR: epsilon_Hoeffding = {eps_h:.6f}, expected "
            f"{EPSILON_H_EXPECTED} (tol {EPSILON_H_TOL}). Aborting.",
            file=sys.stderr,
        )
        sys.exit(1)

    return records, eps_h


def build_figure(records, eps_h):
    fig, ax = plt.subplots(figsize=(8.4, 5.0))

    x_positions = list(range(len(records)))
    margins = []

    for xi, rec in zip(x_positions, records):
        max_dev = rec["max_dev_hw"]
        eps_d = rec["epsilon_device"]
        margin = eps_d - max_dev
        margins.append(margin)

        # Connector visualizes the margin; zero-length for Fez.
        ax.plot(
            [xi, xi], [max_dev, eps_d],
            color=COL_CONNECT, linewidth=3.6,
            solid_capstyle="round", zorder=1,
        )
        # Measured value (filled circle). Drawn larger than the threshold
        # diamond so the blue ring remains visible at Fez where both
        # markers share a y-coordinate.
        ax.scatter(
            [xi], [max_dev], s=300, marker="o",
            color=COL_BAR, edgecolor="#0A2E5C", linewidth=1.4,
            zorder=3,
        )
        # Per-device threshold (filled diamond, smaller and drawn above
        # the circle).
        ax.scatter(
            [xi], [eps_d], s=130, marker="D",
            color=COL_THR, edgecolor="#5C0F0F", linewidth=1.4,
            zorder=4,
        )

        # Margin annotation, placed to the right of each threshold diamond
        # at the same y. Single neutral color across all devices so the
        # Fez "+0.0000" is not misread as a failure callout: emphasis comes
        # from the bullseye marker overlap, not from color.
        ax.annotate(
            f"{margin:+.4f}",
            xy=(xi + 0.24, eps_d),
            fontsize=12, color=COL_TEXT, fontweight="bold",
            ha="left", va="center",
        )

    ax.axhline(eps_h, color=COL_HOEFF, linestyle=(0, (6, 4)),
               linewidth=2.2, zorder=0)

    ax.set_xticks(x_positions)
    ax.set_xticklabels([r["device"] for r in records], fontweight="bold")
    for label in ax.get_yticklabels():
        label.set_fontweight("bold")
    ax.set_ylabel("max-deviation magnitude", fontweight="bold")
    ax.set_ylim(0.0, 0.22)
    ax.set_yticks([0.00, 0.05, 0.10, 0.15, 0.20])
    ax.set_xlim(-0.5, len(records) - 0.5)
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
            markerfacecolor=COL_BAR, markeredgecolor="#0A2E5C",
            markersize=14, markeredgewidth=1.4,
            label="measured",
        ),
        Line2D(
            [0], [0], marker="D", color="w",
            markerfacecolor=COL_THR, markeredgecolor="#5C0F0F",
            markersize=10, markeredgewidth=1.4,
            label="epsilon_device(d)",
        ),
        Line2D(
            [0], [0], color=COL_HOEFF, linestyle=(0, (6, 4)),
            linewidth=2.2,
            label="Hoeffding (eps_H = 0.134)",
        ),
    ]
    # Legend placed ABOVE the axes so it cannot occlude any data element.
    legend = ax.legend(
        handles=legend_handles,
        loc="lower center", bbox_to_anchor=(0.5, 1.02),
        ncol=3, frameon=False, fontsize=10.5,
        handletextpad=0.6, columnspacing=2.4,
    )
    for txt in legend.get_texts():
        txt.set_fontweight("bold")

    fig.tight_layout(pad=0.9)
    return fig, margins


def main():
    records, eps_h = load_and_verify()
    fig, margins = build_figure(records, eps_h)

    FIG_DIR.mkdir(parents=True, exist_ok=True)
    fig.savefig(PDF_PATH, dpi=300, bbox_inches="tight")
    fig.savefig(PNG_PATH, dpi=300, bbox_inches="tight")
    plt.close(fig)

    print("Figure saved to figures/section5B_completeness.{pdf,png}")
    print("Margins computed from JSON:")
    for rec, m in zip(records, margins):
        label = rec["device"] + ":"
        print(f"  {label:14s} {m:+.4f}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
