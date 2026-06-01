"""
Build Fig. 4 (Contribution 2: Witness Protocol Theorem Validation) and Table III.

Panels:
  (a) Detection rate vs claim/true error ratio with Wilson 95% CIs and Hoeffding
      false-positive bound delta = 0.05 -> proves the theorem's FPR promise.
  (b) Mean max-deviation across 50 witnesses vs claim/true error ratio with the
      Hoeffding epsilon line -> proves the test statistic crosses the threshold
      at the predicted operating point.
  (c) Robustness ablation: false-positive rate (honest) and detection rate
      (3x spoof) across 11 configurations spanning depth, witness count N, and
      detection shots S -> proves invariance to the tunable knobs.

Outputs PNG (300 dpi) + vector PDF for LaTeX. Table III printed to stdout.
"""
import warnings
warnings.filterwarnings('ignore')

from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

plt.rcParams.update({
    'font.family': 'sans-serif',
    'font.sans-serif': ['DejaVu Sans', 'Arial'],
    'font.size': 9,
    'font.weight': 'normal',
    'axes.titlesize': 10.5,
    'axes.titleweight': 'bold',
    'axes.labelsize': 9.5,
    'axes.labelweight': 'bold',
    'xtick.labelsize': 8.5,
    'ytick.labelsize': 8.5,
    'legend.fontsize': 8.5,
    'legend.frameon': True,
    'legend.framealpha': 0.92,
    'legend.edgecolor': '0.4',
    'lines.linewidth': 2.0,
    'lines.markersize': 7,
    'lines.markeredgewidth': 0.9,
    'axes.linewidth': 1.1,
    'axes.grid': True,
    'grid.alpha': 0.28,
    'grid.linewidth': 0.7,
    'patch.linewidth': 0.9,
    'savefig.dpi': 300,
    'savefig.bbox': 'tight',
    'savefig.pad_inches': 0.05,
    'pdf.fonttype': 42,
    'ps.fonttype': 42,
})

COL_DETECT = '#1F4E9C'   # deep blue
COL_DELTA  = '#D62728'   # red (delta line)
COL_STAT   = '#2F8F4D'   # green (test statistic)
COL_EPS    = '#D62728'   # red (epsilon line)
COL_FPR    = '#D62728'   # red (FPR bars)
COL_DET    = '#1F4E9C'   # blue (detection bars)
COL_BASE   = '#444444'

PROJ = Path(__file__).parent.parent
PHASE2_NPZ = PROJ / "results" / "phase2_cameraready" / "witness_detection.npz"
ABLATIONS_NPZ = PROJ / "results" / "ablations" / "ablations.npz"
OUT_DIR = PROJ / "results" / "contribution2"


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    if not PHASE2_NPZ.exists():
        raise FileNotFoundError(f"Need {PHASE2_NPZ}")
    if not ABLATIONS_NPZ.exists():
        raise FileNotFoundError(f"Need {ABLATIONS_NPZ}")

    p2 = np.load(PHASE2_NPZ)
    ab = np.load(ABLATIONS_NPZ)

    fig, axes = plt.subplots(1, 3, figsize=(11.5, 3.6))

    # ---- (a) Theorem validation: detection rate + Wilson CIs ------------ #
    ax = axes[0]
    mags = p2['magnitudes']
    rates = p2['detection_rates']
    lo = p2['detection_ci_lo']
    hi = p2['detection_ci_hi']
    yerr_lo = rates - lo
    yerr_hi = hi - rates
    ax.errorbar(mags, rates, yerr=[yerr_lo, yerr_hi],
                fmt='o-', color=COL_DETECT, ecolor=COL_DETECT,
                linewidth=2.0, markersize=7, capsize=4, capthick=1.4,
                markeredgecolor='black', markeredgewidth=0.8,
                label='Empirical detection rate (95% Wilson CI)')
    ax.axhline(float(p2['delta']), color=COL_DELTA, linestyle='--', linewidth=1.6,
               label=f'Hoeffding FPR bound (δ={float(p2["delta"]):.2f})')
    # annotate the FPR upper bound at honest endpoint
    ax.annotate(f'FPR ≤ {hi[0]:.3f}',
                xy=(float(mags[0]), float(rates[0]) + (hi[0] - rates[0])),
                xytext=(0.85, 0.18),
                fontsize=8.5, fontweight='bold', color=COL_DETECT,
                ha='center',
                arrowprops=dict(arrowstyle='->', color=COL_DETECT, lw=1.0))
    ax.invert_xaxis()
    ax.set_xlabel('Claim / true error ratio  (1.0 = honest)')
    ax.set_ylabel('Detection rate')
    ax.set_title('(a) Theorem validation', loc='left')
    ax.set_ylim(-0.03, 1.05)
    ax.legend(loc='upper left')

    # ---- (b) Test statistic vs Hoeffding threshold ---------------------- #
    ax = axes[1]
    mmd = p2['mean_max_dev']
    eps = float(p2['epsilon'])
    ax.plot(mags, mmd, 's-', color=COL_STAT,
            linewidth=2.0, markersize=7,
            markeredgecolor='black', markeredgewidth=0.8,
            label='Mean max-deviation')
    ax.axhline(eps, color=COL_EPS, linestyle='--', linewidth=1.6,
               label=f'Hoeffding ε = {eps:.3f}')
    # crossing annotation
    cross_idx = int(np.argmin(np.abs(mmd - eps)))
    ax.annotate('Crossing',
                xy=(float(mags[cross_idx]), float(mmd[cross_idx])),
                xytext=(0.7, eps - 0.02),
                fontsize=8.5, fontweight='bold', color=COL_STAT,
                ha='center',
                arrowprops=dict(arrowstyle='->', color=COL_STAT, lw=1.0))
    ax.invert_xaxis()
    ax.set_xlabel('Claim / true error ratio  (1.0 = honest)')
    ax.set_ylabel('Mean max-deviation')
    ax.set_title('(b) Test statistic vs. threshold', loc='left')
    ax.legend(loc='upper left')

    # ---- (c) Robustness ablation ---------------------------------------- #
    ax = axes[2]

    blocks = [
        ("Depth",
         [str(int(v)) for v in ab['depths']],
         ab['depth_fprs'], ab['depth_detections']),
        ("N witnesses",
         [str(int(v)) for v in ab['n_values']],
         ab['n_fprs'], ab['n_detections']),
        ("Shots",
         [str(int(v)) for v in ab['shot_values']],
         ab['shot_fprs'], ab['shot_detections']),
    ]

    # Build a single x-axis with three groups separated by gaps
    labels = []
    fprs_all = []
    dets_all = []
    block_starts = []
    sep_positions = []
    cursor = 0
    for name, lab, fpr, det in blocks:
        block_starts.append((cursor, cursor + len(lab) - 1, name))
        for v, f, d in zip(lab, fpr, det):
            labels.append(v)
            fprs_all.append(float(f))
            dets_all.append(float(d))
            cursor += 1
        sep_positions.append(cursor - 0.5)
        cursor += 1  # gap between blocks
        labels.append('')
        fprs_all.append(np.nan)
        dets_all.append(np.nan)
    # remove trailing gap
    labels = labels[:-1]
    fprs_all = fprs_all[:-1]
    dets_all = dets_all[:-1]
    x = np.arange(len(labels))
    width = 0.38

    # Plot bars (skipping NaNs which are visual gaps)
    valid = ~np.isnan(np.asarray(fprs_all, dtype=float))
    ax.bar(x[valid] - width/2, np.asarray(fprs_all)[valid], width,
           color=COL_FPR, edgecolor='black', linewidth=0.6, label='FPR (honest)')
    ax.bar(x[valid] + width/2, np.asarray(dets_all)[valid], width,
           color=COL_DET, edgecolor='black', linewidth=0.6, label='Detection (3× spoof)')
    ax.axhline(float(p2['delta']), color=COL_BASE, linestyle=':', linewidth=1.2,
               label=f'δ = {float(p2["delta"]):.2f}')

    ax.set_xticks(x)
    ax.set_xticklabels(labels, fontsize=7.5)
    ax.set_ylim(-0.02, 1.12)
    ax.set_ylabel('Rate')
    ax.set_title('(c) Robustness across knobs', loc='left')
    ax.legend(loc='center right', fontsize=8)

    # Group labels at the bottom
    ymin = ax.get_ylim()[0]
    for start, end, name in block_starts:
        mid = (start + end) / 2
        ax.text(mid, ymin - 0.16, name, ha='center', va='top',
                fontsize=8.5, fontweight='bold', color='black',
                transform=ax.transData)
    # vertical separators between groups (at gap positions, except last)
    for sx in sep_positions[:-1]:
        ax.axvline(sx + 0.5, color='0.6', linewidth=0.8, linestyle='-', alpha=0.5)

    fig.tight_layout(pad=0.6)

    png_path = OUT_DIR / "contribution2_figure.png"
    pdf_path = OUT_DIR / "contribution2_figure.pdf"
    fig.savefig(png_path, dpi=300)
    fig.savefig(pdf_path)
    print(f"Saved figure (PNG, 300 dpi): {png_path}")
    print(f"Saved figure (PDF, vector):  {pdf_path}")

    # ---- Table III printed in markdown form ----------------------------- #
    print()
    print("Table III - Robustness ablation")
    print("=" * 64)
    print(f"{'Parameter':<22} | {'Setting':>9} | {'FPR (honest)':>13} | {'Detection (3x spoof)':>21}")
    print("-" * 64)
    for name, lab, fpr, det in blocks:
        for v, f, d in zip(lab, fpr, det):
            print(f"{name:<22} | {v:>9} | {float(f):>13.3f} | {float(d):>21.3f}")
    print()
    print("Headline (Phase 2 camera-ready, N=50, depth=5, S=1024, T=100 trials):")
    print(f"  predictor train residual = {float(p2['train_residual']):.4f}")
    print(f"  Hoeffding eps            = {float(p2['epsilon']):.4f}")
    print(f"  honest FPR upper bound   = {float(p2['detection_ci_hi'][0]):.4f}  (Wilson 95% CI)")
    print(f"  detection at ratio=0.4   = {float(p2['detection_rates'][-1]):.3f}")

    np.savez(
        OUT_DIR / "contribution2_data.npz",
        magnitudes=p2['magnitudes'],
        detection_rates=p2['detection_rates'],
        detection_ci_lo=p2['detection_ci_lo'],
        detection_ci_hi=p2['detection_ci_hi'],
        mean_max_dev=p2['mean_max_dev'],
        epsilon=p2['epsilon'],
        delta=p2['delta'],
        depths=ab['depths'], depth_fprs=ab['depth_fprs'], depth_detections=ab['depth_detections'],
        n_values=ab['n_values'], n_fprs=ab['n_fprs'], n_detections=ab['n_detections'],
        shot_values=ab['shot_values'], shot_fprs=ab['shot_fprs'], shot_detections=ab['shot_detections'],
    )
    print(f"\nSaved combined data: {OUT_DIR / 'contribution2_data.npz'}")


if __name__ == "__main__":
    main()
