"""
Build Fig. 3 (Contribution 1) and Table II for the ICMIC paper.

Panels:
  (a) Naive TVD vs. liar inflation factor (harm)
  (b) Stealth: histogram of error-rate L2 distance from honest centroid for
      (i) honest population, (ii) liar claim, (iii) liar true at 5x
  (c) Defense comparison: TVD vs. inflation across naive / median / trimmed-mean /
      witness attestation

Outputs PNG (300 dpi) and PDF (vector) for LaTeX. Table II is printed to stdout in
markdown-ready form for direct paste.
"""
import warnings
warnings.filterwarnings('ignore')

from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

# Publication-quality defaults for LaTeX inclusion.
plt.rcParams.update({
    'font.family': 'sans-serif',
    'font.sans-serif': ['DejaVu Sans', 'Arial'],
    'font.size': 9,
    'font.weight': 'normal',           # regular ticks/legend; bold reserved for titles/labels
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

# Saturated, high-contrast palette (colorblind-considerate distinct hues)
COL_NAIVE   = '#D62728'  # vivid red
COL_ATTEST  = '#1F4E9C'  # deep blue
COL_MEDIAN  = '#FF8C00'  # orange
COL_TRIM    = '#7B3FBF'  # purple
COL_HONEST  = '#2A8FBD'  # blue-cyan (panel b honest)
COL_CLAIM   = '#27AE60'  # green     (panel b claim)
COL_TRUE    = '#C0392B'  # crimson   (panel b true)
COL_BASE    = '#444444'  # dark grey (baseline ref line)

from qem import sample_descriptors


PROJ = Path(__file__).parent.parent
PHASE3_NPZ = PROJ / "results" / "phase3_cameraready" / "federation_demo.npz"
DEFENSE_NPZ = PROJ / "results" / "defense_comparison" / "defense_comparison.npz"
OUT_DIR = PROJ / "results" / "contribution1"


def stealth_data(n=2000, factor=5.0, max_error=0.5, seed_h=2026, seed_l=2027):
    """Compute error-rate L2 distances for the stealth panel."""
    honest = sample_descriptors(n, seed=seed_h)
    honest_err = np.stack([d.to_vector()[8:16] for d in honest])
    centroid = honest_err.mean(axis=0)
    honest_l2 = np.linalg.norm(honest_err - centroid, axis=1)

    liars = sample_descriptors(n, seed=seed_l)
    claim_err = np.stack([d.to_vector()[8:16] for d in liars])
    true_err = np.minimum(claim_err * factor, max_error)

    claim_l2 = np.linalg.norm(claim_err - centroid, axis=1)
    true_l2 = np.linalg.norm(true_err - centroid, axis=1)
    return honest_l2, claim_l2, true_l2


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    if not PHASE3_NPZ.exists():
        raise FileNotFoundError(f"Need {PHASE3_NPZ}")
    if not DEFENSE_NPZ.exists():
        raise FileNotFoundError(f"Need {DEFENSE_NPZ} (run experiments/defense_comparison.py first)")

    p3 = np.load(PHASE3_NPZ)
    df = np.load(DEFENSE_NPZ)
    inflation = df['inflation_factors']

    # 9 x 3.2 inches at 300 dpi -> ~2700 x 960 px; spans full text width in 2-col papers
    fig, axes = plt.subplots(1, 3, figsize=(11.5, 3.6))

    # ---- (a) Harm curve --------------------------------------------------- #
    ax = axes[0]
    ax.errorbar(p3['inflation_factors'], p3['naive_mean'], yerr=p3['naive_std'],
                fmt='o-', color=COL_NAIVE, ecolor=COL_NAIVE,
                linewidth=2.0, markersize=7, capsize=4, capthick=1.4,
                markeredgecolor='black', markeredgewidth=0.8,
                label='Naive aggregation')
    ax.axhline(p3['naive_mean'][0], color=COL_BASE, linestyle=':', linewidth=1.5,
               label='Honest baseline')
    # Annotate +103% number directly on the figure
    x_last, y_last = float(p3['inflation_factors'][-1]), float(p3['naive_mean'][-1])
    pct = 100.0 * (y_last - float(p3['naive_mean'][0])) / float(p3['naive_mean'][0])
    ax.annotate(f'+{pct:.0f}%',
                xy=(x_last - 0.05, y_last - 0.003),
                xytext=(3.6, y_last + 0.012),
                fontsize=11, fontweight='bold', color=COL_NAIVE,
                ha='center',
                arrowprops=dict(arrowstyle='->', color=COL_NAIVE, lw=1.2))
    ax.set_xlabel('Liar noise inflation factor')
    ax.set_ylabel('TVD vs. noiseless ideal')
    ax.set_title('(a) Threat impact', loc='left')
    ax.set_ylim(top=0.275)
    ax.legend(loc='upper left')

    # ---- (b) Stealth histogram ------------------------------------------- #
    ax = axes[1]
    h_l2, c_l2, t5_l2 = stealth_data(n=2000, factor=5.0)
    bins = np.linspace(0, max(t5_l2.max(), 0.4), 45)
    ax.hist(h_l2, bins=bins, alpha=0.55, color=COL_HONEST, label='Honest population',
            density=True, edgecolor='black', linewidth=0.5)
    ax.hist(c_l2, bins=bins, alpha=0.55, color=COL_CLAIM, label="Liar's claim",
            density=True, edgecolor='black', linewidth=0.5)
    ax.hist(t5_l2, bins=bins, alpha=0.65, color=COL_TRUE, label="Liar's true (5x)",
            density=True, edgecolor='black', linewidth=0.5)
    # Annotate stealth ratio (position after legend so we can use ylim)
    ymax = ax.get_ylim()[1]
    ax.annotate('Claim = Honest\n(stealth = 1.0×)',
                xy=(0.025, ymax * 0.55),
                xytext=(0.12, ymax * 0.42),
                fontsize=8.5, fontweight='bold', color='black',
                ha='left', va='center',
                arrowprops=dict(arrowstyle='->', color='black', lw=1.1))
    ax.annotate('True (5×) = 11.5× away',
                xy=(0.26, 8),
                xytext=(0.25, ymax * 0.30),
                fontsize=8.5, fontweight='bold', color=COL_TRUE,
                ha='center', va='center',
                arrowprops=dict(arrowstyle='->', color=COL_TRUE, lw=1.1))
    ax.set_xlabel('Error-rate L2 distance from honest centroid')
    ax.set_ylabel('Density')
    ax.set_title('(b) Stealth', loc='left')
    ax.legend(loc='upper right')

    # ---- (c) Defense comparison ----------------------------------------- #
    ax = axes[2]
    style = {
        'naive':        dict(color=COL_NAIVE,  marker='o', linestyle='-',  label='Naive', zorder=4),
        'median':       dict(color=COL_MEDIAN, marker='^', linestyle='--', label='Median', zorder=3),
        'trimmed_mean': dict(color=COL_TRIM,   marker='D', linestyle='--', label='Trimmed mean', zorder=3),
        'attested':     dict(color=COL_ATTEST, marker='s', linestyle='-',  label='Witness attestation (ours)', zorder=5),
    }
    for m in ['naive', 'median', 'trimmed_mean', 'attested']:
        ax.errorbar(inflation, df[f'{m}_mean'], yerr=df[f'{m}_std'],
                    linewidth=2.0, markersize=7, capsize=3.5, capthick=1.3,
                    markeredgecolor='black', markeredgewidth=0.7, **style[m])
    ax.set_xlabel('Liar noise inflation factor')
    ax.set_ylabel('TVD vs. noiseless ideal')
    ax.set_title('(c) Defense baselines vs. ours', loc='left')
    ax.legend(loc='upper left', fontsize=8)

    fig.tight_layout(pad=0.6)

    png_path = OUT_DIR / "contribution1_figure.png"
    pdf_path = OUT_DIR / "contribution1_figure.pdf"
    fig.savefig(png_path, dpi=300)
    fig.savefig(pdf_path)  # vector
    print(f"Saved figure (PNG, 300 dpi): {png_path}")
    print(f"Saved figure (PDF, vector):  {pdf_path}")

    # Table II - print as markdown for paste into paper
    print()
    print("Table II - Defense baseline comparison")
    print("=" * 72)
    print(f"{'Defense':<22} | {'TVD @1.0x':>10} | {'TVD @3.0x':>10} | {'TVD @5.0x':>10}")
    print("-" * 72)
    label = {
        'naive': 'Naive (no defense)',
        'median': 'Element-wise median',
        'trimmed_mean': 'Trimmed mean',
        'attested': 'Witness attestation',
    }
    idx_1 = int(np.argmin(np.abs(inflation - 1.0)))
    idx_3 = int(np.argmin(np.abs(inflation - 3.0)))
    idx_5 = int(np.argmin(np.abs(inflation - 5.0)))
    for m in ['naive', 'median', 'trimmed_mean', 'attested']:
        v = df[f'{m}_mean']
        s = df[f'{m}_std']
        print(f"{label[m]:<22} | {v[idx_1]:>5.3f}+/-{s[idx_1]:.3f} | {v[idx_3]:>5.3f}+/-{s[idx_3]:.3f} | {v[idx_5]:>5.3f}+/-{s[idx_5]:.3f}")
    print()

    # Stealth table summary
    print("Table II.b - Stealth quantification (error-rate L2 distance, N=2000)")
    print("=" * 60)
    for f in [1.0, 2.0, 5.0]:
        h_l2, c_l2, t_l2 = stealth_data(n=2000, factor=f)
        ratio = t_l2.mean() / h_l2.mean()
        below = float((h_l2 >= t_l2.mean()).mean())
        print(f"  inflation={f:.1f}x: claim_L2={c_l2.mean():.4f}, true_L2={t_l2.mean():.4f}, "
              f"true/within = {ratio:.2f},  frac honest >= true = {below:.3f}")

    np.savez(
        OUT_DIR / "contribution1_data.npz",
        inflation=inflation,
        naive_mean=df['naive_mean'], naive_std=df['naive_std'],
        median_mean=df['median_mean'], median_std=df['median_std'],
        trimmed_mean_mean=df['trimmed_mean_mean'], trimmed_mean_std=df['trimmed_mean_std'],
        attested_mean=df['attested_mean'], attested_std=df['attested_std'],
    )
    print(f"\nSaved combined data: {OUT_DIR / 'contribution1_data.npz'}")


if __name__ == "__main__":
    main()
