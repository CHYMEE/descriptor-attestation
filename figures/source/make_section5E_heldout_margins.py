"""Build Figure 4 for Section 5.E (Deployment calibration) of the QST paper.

Strip plot of held-out test margins across 30 predictor instances on
ibm_fez. Each marker is one predictor instance; all 30 lie below the
pass/fail threshold (y = 0). Reference lines show the mean margin, the
95% bootstrap CI on the mean, and the original single-instance Task 4
margin for cross-reference.

The figure communicates the 30/30 failure of the held-out test on Fez:
under every predictor instance, max_dev_hw(Fez) > eps_device_heldout, so
the per-device-eps construction calibrated on Kingston + Marrakesh does
not generalize to Fez out-of-sample.

Sources:
  results/phase3/section5A_inputs/task4_replicated.json
  results/phase3/section5A_inputs/task4_heldout_test.json
Output:
  figures/section5E_heldout_margins.{pdf,png}
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.legend_handler import HandlerTuple
from matplotlib.lines import Line2D
from matplotlib.patches import Patch


# Publication-bold rcParams, matching the Section 5.B / 5.C / 5.D figures.
plt.rcParams.update({
    "font.family": "sans-serif",
    "font.sans-serif": ["DejaVu Sans", "Arial", "Helvetica"],
    "font.weight": "bold",
    "font.size": 10,
    "axes.labelweight": "bold",
    "axes.labelsize": 11,
    "axes.linewidth": 1.6,
    "axes.edgecolor": "#1a1a1a",
    "xtick.labelsize": 10,
    "ytick.labelsize": 9.5,
    "xtick.major.width": 1.4,
    "ytick.major.width": 1.4,
    "xtick.major.size": 5.0,
    "ytick.major.size": 5.0,
    "xtick.color": "#1a1a1a",
    "ytick.color": "#1a1a1a",
    "legend.fontsize": 8,
    "savefig.dpi": 300,
    "pdf.fonttype": 42,
    "ps.fonttype": 42,
})


PROJECT_ROOT = Path(__file__).resolve().parents[2]
T4_REPL_PATH = (
    PROJECT_ROOT
    / "data" / "processed" / "section5E"
    / "task4_replicated.json"
)
T4_SINGLE_PATH = (
    PROJECT_ROOT
    / "data" / "processed" / "section5E"
    / "task4_heldout_test.json"
)
FIG_DIR = PROJECT_ROOT / "figures" / "final"
PDF_PATH = FIG_DIR / "section5E_heldout_margins.pdf"
PNG_PATH = FIG_DIR / "section5E_heldout_margins.png"

VALUE_TOL = 1e-4
JITTER_SEED = 46

CANONICAL = dict(
    n_trials=30,
    n_fail=30,
    mean=-0.0195,
    median=-0.0193,
    std=0.0067,
    min=-0.0331,
    max=-0.0058,
    boot_ci=(-0.0218, -0.0172),
    single_instance=-0.0092,
)

# Colors — magenta strip markers (Section 5.C phase-2 continuity);
# dark gray for mean + CI band; medium gray for the single-instance ref;
# near-black for the pass/fail threshold.
COL_MARKER = "#AD1457"          # Material Pink 900 (dark magenta)
COL_MARKER_EDGE = "black"
COL_MEAN = "#444444"
COL_REFERENCE = "#888888"
COL_THRESHOLD = "#1a1a1a"
COL_ANNOTATION = "#AD1457"      # matches the strip cluster


def load_and_verify():
    if not T4_REPL_PATH.is_file():
        print(f"ERROR: JSON not found at {T4_REPL_PATH}", file=sys.stderr)
        sys.exit(1)
    if not T4_SINGLE_PATH.is_file():
        print(f"ERROR: JSON not found at {T4_SINGLE_PATH}", file=sys.stderr)
        sys.exit(1)

    repl = json.loads(T4_REPL_PATH.read_text())
    single = json.loads(T4_SINGLE_PATH.read_text())

    md = repl["margin_distribution"]
    values = [float(v) for v in md["values"]]

    if len(values) != CANONICAL["n_trials"]:
        print(
            f"ERROR: expected {CANONICAL['n_trials']} margin values, "
            f"got {len(values)}. Aborting.",
            file=sys.stderr,
        )
        sys.exit(1)

    summary = dict(
        n_trials=int(repl["n_trials"]),
        n_fail=int(repl["n_fail"]),
        mean=float(md["mean"]),
        median=float(md["median"]),
        std=float(md["std"]),
        min=float(md["min"]),
        max=float(md["max"]),
        boot_ci=(float(md["bootstrap_mean_ci_95"][0]),
                 float(md["bootstrap_mean_ci_95"][1])),
        single_instance=float(single["margin"]),
    )

    for fld in ("n_trials", "n_fail"):
        if summary[fld] != CANONICAL[fld]:
            print(
                f"ERROR: {fld} = {summary[fld]}, "
                f"canonical {CANONICAL[fld]}. Aborting.",
                file=sys.stderr,
            )
            sys.exit(1)
    for fld in ("mean", "median", "std", "min", "max", "single_instance"):
        if abs(summary[fld] - CANONICAL[fld]) > VALUE_TOL:
            print(
                f"ERROR: {fld} = {summary[fld]:.6f}, "
                f"canonical {CANONICAL[fld]:.4f} (tol {VALUE_TOL}). "
                f"Aborting.",
                file=sys.stderr,
            )
            sys.exit(1)
    for i, end in enumerate(("lower", "upper")):
        if abs(summary["boot_ci"][i] - CANONICAL["boot_ci"][i]) > VALUE_TOL:
            print(
                f"ERROR: boot_ci_{end} = {summary['boot_ci'][i]:.6f}, "
                f"canonical {CANONICAL['boot_ci'][i]:.4f} "
                f"(tol {VALUE_TOL}). Aborting.",
                file=sys.stderr,
            )
            sys.exit(1)

    return values, summary


def build_figure(values, summary):
    fig, ax = plt.subplots(figsize=(5.0, 4.0))

    x_center = 0.5
    rng = np.random.default_rng(JITTER_SEED)
    jitter = rng.uniform(-0.08, 0.08, size=len(values))
    xs = x_center + jitter

    # Bootstrap CI band (drawn first so markers paint on top).
    ci_lo, ci_hi = summary["boot_ci"]
    ax.fill_between(
        [0.2, 0.8], ci_lo, ci_hi,
        color=COL_MEAN, alpha=0.18, linewidth=0, zorder=1,
    )

    # Mean margin line.
    ax.hlines(
        summary["mean"], 0.2, 0.8,
        colors=COL_MEAN, linewidth=1.2, linestyle="-", zorder=2,
    )

    # Strip markers — the 30 per-instance margins.
    ax.scatter(
        xs, values, s=60, marker="o",
        color=COL_MARKER, edgecolor=COL_MARKER_EDGE,
        linewidth=0.4, alpha=0.75, zorder=3,
    )

    # Pass/fail threshold at y = 0 (spans full x range).
    ax.hlines(
        0.0, 0.0, 1.0,
        colors=COL_THRESHOLD, linewidth=1.5, linestyle="-", zorder=2,
    )

    # Headline annotation just above the cluster max.
    ax.text(
        x_center, summary["max"] + 0.003,
        "30/30 instances fail",
        ha="center", va="bottom",
        fontsize=9, fontweight="bold", color=COL_ANNOTATION,
    )

    # Axes styling.
    ax.set_xticks([x_center])
    ax.set_xticklabels(["ibm_fez held-out (30 instances)"])
    for label in ax.get_xticklabels():
        label.set_fontweight("bold")
    for label in ax.get_yticklabels():
        label.set_fontweight("bold")
    ax.set_ylabel("Held-out margin", fontweight="bold")
    ax.set_xlim(0.0, 1.0)
    ax.set_ylim(-0.040, 0.005)
    ax.set_yticks([-0.04, -0.03, -0.02, -0.01, 0.00])
    ax.yaxis.grid(True, alpha=0.22, linestyle=":", linewidth=1.0,
                  color="#666666")
    ax.set_axisbelow(True)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_linewidth(1.6)
    ax.spines["bottom"].set_linewidth(1.6)

    # Three-entry legend: instance markers, pass threshold, and the
    # mean + bootstrap CI as one combined handle (line over band).
    marker_handle = Line2D(
        [0], [0], marker="o", color="w",
        markerfacecolor=COL_MARKER, markeredgecolor=COL_MARKER_EDGE,
        markersize=8, markeredgewidth=0.4, alpha=0.85,
    )
    threshold_handle = Line2D(
        [0], [0], color=COL_THRESHOLD, linewidth=1.5,
    )
    mean_ci_handle = (
        Line2D([0], [0], color=COL_MEAN, linewidth=1.2),
        Patch(facecolor=COL_MEAN, alpha=0.18, linewidth=0),
    )

    leg = ax.legend(
        handles=[marker_handle, threshold_handle, mean_ci_handle],
        labels=[
            "instance margins (n = 30)",
            "pass/fail threshold (y = 0)",
            "mean +/- bootstrap 95% CI",
        ],
        handler_map={tuple: HandlerTuple(ndivide=None, pad=0.6)},
        loc="lower right",
        fontsize=8, framealpha=0.92, edgecolor="0.4",
    )
    for txt in leg.get_texts():
        txt.set_fontweight("bold")

    fig.tight_layout(pad=0.5)
    return fig, jitter[:5]


def main():
    values, summary = load_and_verify()
    fig, jitter_first5 = build_figure(values, summary)

    FIG_DIR.mkdir(parents=True, exist_ok=True)
    fig.savefig(PDF_PATH, dpi=300, bbox_inches="tight")
    fig.savefig(PNG_PATH, dpi=300, bbox_inches="tight")
    plt.close(fig)

    print("Figure saved to figures/section5E_heldout_margins.{pdf,png}")
    print("Held-out test summary:")
    print(f"  Trials:   {summary['n_trials']}")
    fail_pct = 100.0 * summary["n_fail"] / summary["n_trials"]
    print(f"  Failures: {summary['n_fail']} ({fail_pct:.0f}%)")
    ci_lo, ci_hi = summary["boot_ci"]
    print(
        f"  Mean margin: {summary['mean']:.4f} "
        f"[bootstrap 95% CI: {ci_lo:.4f}, {ci_hi:.4f}]"
    )
    print(
        f"  Range:    [{summary['min']:.4f}, {summary['max']:.4f}]"
    )
    print(
        f"  Single-instance reference: {summary['single_instance']:.4f}"
    )
    print(f"  Jitter seed: {JITTER_SEED}")
    print(
        "  Jitter first 5: "
        + " ".join(f"{j:+.4f}" for j in jitter_first5)
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
