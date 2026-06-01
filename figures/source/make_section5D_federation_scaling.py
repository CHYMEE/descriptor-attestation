"""Build Figure 3 for Section 5.D (Federation scaling) of the QST paper.

Two panels:
- Left:  Type I error rate vs N with Wilson 95% upper CIs and the
         delta=0.05 reference line. Annotations above each marker
         report the Wilson upper bound to 4 decimals.
- Right: per-device flag attribution across 30 replication trials at
         each N. All 23 flag events at every N are contributed
         exclusively by ibm_fez; ibm_kingston, ibm_marrakesh, and
         aersim (pooled) report zero. This is the mechanism panel.

Color palette per user (2026-05-15): purple, teal, blue, pink.
Assignments are semantic — Fez gets pink (it carries the signal),
Kingston blue, Marrakesh teal, aersim purple (different category from
the three real devices).

Sources:
  results/phase3/section5A_inputs/task5b_aggregated_scaling.json
  results/phase3/section5A_inputs/section5A_replication_full_trial_dump.json
Output:
  figures/section5D_federation_scaling.{pdf,png}
"""
from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Patch


# Publication-bold defaults, matching the Section 5.B / 5.C figure scripts.
plt.rcParams.update({
    "font.family": "sans-serif",
    "font.sans-serif": ["DejaVu Sans", "Arial", "Helvetica"],
    "font.weight": "bold",
    "font.size": 10,
    "axes.labelweight": "bold",
    "axes.labelsize": 11,
    "axes.titlesize": 11.5,
    "axes.titleweight": "bold",
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
    "legend.fontsize": 10,
    "savefig.dpi": 300,
    "pdf.fonttype": 42,
    "ps.fonttype": 42,
})


PROJECT_ROOT = Path(__file__).resolve().parents[2]
T5B_PATH = (
    PROJECT_ROOT
    / "data" / "processed" / "section5D"
    / "task5b_aggregated_scaling.json"
)
DUMP_PATH = (
    PROJECT_ROOT
    / "data" / "processed" / "section5D"
    / "replication_full_trial_dump.json"
)
FIG_DIR = PROJECT_ROOT / "figures" / "final"
PDF_PATH = FIG_DIR / "section5D_federation_scaling.pdf"
PNG_PATH = FIG_DIR / "section5D_federation_scaling.png"

N_VALUES = [3, 5, 8]
VALUE_TOL = 1e-4

# Canonical expected left-panel values.
CANONICAL_LEFT = {
    3: dict(n=90,  k=23, rate=0.2556, wilson_upper=0.3544),
    5: dict(n=150, k=23, rate=0.1533, wilson_upper=0.2196),
    8: dict(n=240, k=23, rate=0.0958, wilson_upper=0.1397),
}

# Canonical expected right-panel values — Fez exclusivity is load-bearing.
CANONICAL_RIGHT = {
    N: {"ibm_fez": 23, "ibm_kingston": 0, "ibm_marrakesh": 0, "aersim": 0}
    for N in N_VALUES
}

# Per-device colors (user-selected: purple, teal, blue, pink).
COL_FEZ = "#C2185B"            # deep pink/magenta (Material Pink 800)
COL_FEZ_EDGE = "#5C0F2A"
COL_KINGSTON = "#1565C0"       # deep blue (Material Blue 800)
COL_KINGSTON_EDGE = "#0A2E5C"
COL_MARRAKESH = "#00838F"      # deep teal (Material Cyan 800)
COL_MARRAKESH_EDGE = "#003E47"
COL_AERSIM = "#6A1B9A"         # deep purple (Material Purple 800)
COL_AERSIM_EDGE = "#38005C"

# Left-panel auxiliary colors.
COL_LEFT_MARKER = "#1A1A1A"    # near-black for the rate marker + error bar
COL_DELTA_REF = "#C62828"      # deep red for the delta=0.05 threshold


def load_left():
    if not T5B_PATH.is_file():
        print(f"ERROR: JSON not found at {T5B_PATH}", file=sys.stderr)
        sys.exit(1)
    payload = json.loads(T5B_PATH.read_text())
    per_n = {int(e["N"]): e for e in payload["per_N"]}

    records = {}
    for N in N_VALUES:
        if N not in per_n:
            print(f"ERROR: per_N missing N={N}", file=sys.stderr)
            sys.exit(1)
        entry = per_n[N]
        actual = dict(
            n=int(entry["n_device_evaluations"]),
            k=int(entry["k_flagged"]),
            rate=float(entry["type_I_rate"]),
            wilson_upper=float(entry["wilson_upper_ci"]),
        )
        canon = CANONICAL_LEFT[N]
        for fld in ("n", "k"):
            if actual[fld] != canon[fld]:
                print(
                    f"ERROR: N={N} {fld}: JSON={actual[fld]}, "
                    f"canonical={canon[fld]}. Aborting.",
                    file=sys.stderr,
                )
                sys.exit(1)
        for fld in ("rate", "wilson_upper"):
            if abs(actual[fld] - canon[fld]) > VALUE_TOL:
                print(
                    f"ERROR: N={N} {fld}: JSON={actual[fld]:.6f}, "
                    f"canonical={canon[fld]:.4f} (tol {VALUE_TOL}). "
                    f"Aborting.",
                    file=sys.stderr,
                )
                sys.exit(1)
        records[N] = actual
    return records


def load_right():
    if not DUMP_PATH.is_file():
        print(f"ERROR: JSON not found at {DUMP_PATH}", file=sys.stderr)
        sys.exit(1)
    payload = json.loads(DUMP_PATH.read_text())

    attribution = {N: Counter() for N in N_VALUES}
    for trial in payload["per_trial"]:
        for N_str, fed in trial["federation_per_N"].items():
            N = int(N_str)
            if N not in attribution:
                continue
            for dev in fed["devices"]:
                if dev["flagged"]:
                    dev_id = dev["id"]
                    bucket = ("aersim"
                              if dev_id.startswith("aersim")
                              else dev_id)
                    attribution[N][bucket] += 1

    # Verify Fez-only exclusivity. Any non-Fez flag aborts.
    for N in N_VALUES:
        canon = CANONICAL_RIGHT[N]
        for bucket, expected in canon.items():
            actual = attribution[N].get(bucket, 0)
            if actual != expected:
                print(
                    f"ERROR: N={N} {bucket}: JSON={actual}, "
                    f"canonical={expected}. Aborting.",
                    file=sys.stderr,
                )
                sys.exit(1)
        for bucket, count in attribution[N].items():
            if bucket not in canon and count > 0:
                print(
                    f"ERROR: N={N} unexpected device {bucket} with "
                    f"{count} flag(s). Aborting.",
                    file=sys.stderr,
                )
                sys.exit(1)

    return {N: dict(attribution[N]) for N in N_VALUES}


def build_figure(left, right):
    fig, (axL, axR) = plt.subplots(
        1, 2, figsize=(10.0, 4.2),
        gridspec_kw={"wspace": 0.30},
    )

    # ============================================================
    # LEFT PANEL — Type I rate vs N with Wilson 95% upper CIs.
    # ============================================================
    x = np.array(N_VALUES, dtype=float)
    rates = np.array([left[N]["rate"] for N in N_VALUES])
    uppers = np.array([left[N]["wilson_upper"] for N in N_VALUES])

    axL.errorbar(
        x, rates,
        yerr=[np.zeros_like(rates), uppers - rates],
        marker="o", markersize=12,
        markerfacecolor=COL_LEFT_MARKER, markeredgecolor="black",
        markeredgewidth=1.4, color=COL_LEFT_MARKER,
        capsize=7, capthick=2.2, elinewidth=2.6,
        alpha=0.95, linestyle="none", zorder=3,
    )

    axL.axhline(
        0.05, color=COL_DELTA_REF, linestyle=(0, (6, 4)),
        linewidth=2.4, zorder=2, label=r"$\delta = 0.05$",
    )

    for N, upper in zip(N_VALUES, uppers):
        axL.text(
            float(N), upper + 0.018,
            f"<= {upper:.4f}",
            ha="center", va="bottom",
            fontsize=10, fontweight="bold", color=COL_LEFT_MARKER,
        )

    axL.set_xticks(N_VALUES)
    axL.set_xticklabels([f"N={N}" for N in N_VALUES])
    for label in axL.get_xticklabels():
        label.set_fontweight("bold")
    for label in axL.get_yticklabels():
        label.set_fontweight("bold")
    axL.set_ylabel("Type I error rate")
    axL.set_xlabel("Federation size N")
    axL.set_ylim(0.0, 0.45)
    axL.set_xlim(min(N_VALUES) - 1.0, max(N_VALUES) + 1.0)
    axL.yaxis.grid(True, alpha=0.25, linestyle=":", linewidth=1.0,
                   color="#666666")
    axL.set_axisbelow(True)
    axL.spines["top"].set_visible(False)
    axL.spines["right"].set_visible(False)
    axL.spines["left"].set_linewidth(1.6)
    axL.spines["bottom"].set_linewidth(1.6)

    legL = axL.legend(
        loc="lower right", framealpha=0.92,
        edgecolor="0.4", fontsize=10,
    )
    for txt in legL.get_texts():
        txt.set_fontweight("bold")

    # ============================================================
    # RIGHT PANEL — Per-device flag attribution at each N.
    # ============================================================
    devices = [
        ("ibm_fez",       COL_FEZ,       COL_FEZ_EDGE),
        ("ibm_kingston",  COL_KINGSTON,  COL_KINGSTON_EDGE),
        ("ibm_marrakesh", COL_MARRAKESH, COL_MARRAKESH_EDGE),
        ("aersim",        COL_AERSIM,    COL_AERSIM_EDGE),
    ]
    bar_width = 0.18
    offsets = np.array([-0.27, -0.09, 0.09, 0.27])

    x_pos = np.array(N_VALUES, dtype=float)
    for i, (dev_id, color, edge) in enumerate(devices):
        counts = np.array([right[N].get(dev_id, 0) for N in N_VALUES])
        xs = x_pos + offsets[i]
        axR.bar(
            xs, counts, width=bar_width,
            color=color, edgecolor=edge, linewidth=1.4,
            alpha=0.95, zorder=3,
        )
        for xi, c in zip(xs, counts):
            if c > 0:
                axR.text(
                    xi, c + 0.7, f"{c}",
                    ha="center", va="bottom",
                    fontsize=11, fontweight="bold", color=edge,
                )

    axR.set_xticks(N_VALUES)
    axR.set_xticklabels([f"N={N}" for N in N_VALUES])
    for label in axR.get_xticklabels():
        label.set_fontweight("bold")
    for label in axR.get_yticklabels():
        label.set_fontweight("bold")
    axR.set_ylabel("Flag count across 30 trials")
    axR.set_xlabel("Federation size N")
    axR.set_ylim(0, 30)
    axR.set_yticks([0, 5, 10, 15, 20, 25, 30])
    axR.set_xlim(min(N_VALUES) - 1.0, max(N_VALUES) + 1.0)
    axR.yaxis.grid(True, alpha=0.25, linestyle=":", linewidth=1.0,
                   color="#666666")
    axR.set_axisbelow(True)
    axR.spines["top"].set_visible(False)
    axR.spines["right"].set_visible(False)
    axR.spines["left"].set_linewidth(1.6)
    axR.spines["bottom"].set_linewidth(1.6)

    legR_handles = [
        Patch(facecolor=COL_FEZ, edgecolor=COL_FEZ_EDGE,
              linewidth=1.4, label="ibm_fez"),
        Patch(facecolor=COL_KINGSTON, edgecolor=COL_KINGSTON_EDGE,
              linewidth=1.4, label="ibm_kingston"),
        Patch(facecolor=COL_MARRAKESH, edgecolor=COL_MARRAKESH_EDGE,
              linewidth=1.4, label="ibm_marrakesh"),
        Patch(facecolor=COL_AERSIM, edgecolor=COL_AERSIM_EDGE,
              linewidth=1.4, label="aersim (pooled)"),
    ]
    # Above the panel so the legend cannot occlude the Fez bars
    # (which reach y=23 at every N).
    legR = axR.legend(
        handles=legR_handles,
        loc="lower center", bbox_to_anchor=(0.5, 1.02),
        ncol=4, frameon=False, fontsize=9.5,
        handletextpad=0.4, columnspacing=1.4,
    )
    for txt in legR.get_texts():
        txt.set_fontweight("bold")

    fig.tight_layout(pad=0.8)
    return fig


def main():
    left = load_left()
    right = load_right()
    fig = build_figure(left, right)

    FIG_DIR.mkdir(parents=True, exist_ok=True)
    fig.savefig(PDF_PATH, dpi=300, bbox_inches="tight")
    fig.savefig(PNG_PATH, dpi=300, bbox_inches="tight")
    plt.close(fig)

    print("Figure saved to figures/section5D_federation_scaling.{pdf,png}")
    print("Left panel: Type I rates and Wilson 95% upper CIs")
    for N in N_VALUES:
        rec = left[N]
        verdict = ("fails delta=0.05" if rec["wilson_upper"] > 0.05
                   else "passes delta=0.05")
        print(
            f"  N={N}:  rate={rec['rate']:.4f}  "
            f"upper={rec['wilson_upper']:.4f}  ({verdict})"
        )
    print("Right panel: per-device flag attribution (counts at N=3/5/8)")
    for bucket in ("ibm_fez", "ibm_kingston", "ibm_marrakesh", "aersim"):
        counts = " / ".join(f"{right[N].get(bucket, 0):>2d}"
                            for N in N_VALUES)
        print(f"  {bucket:14s} {counts}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
