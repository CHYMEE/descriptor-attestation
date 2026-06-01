"""
Build Fig. 5 (Contribution 3: Real-world deployment) and Table IV.

Contribution 3 combines two real-world validations:
  (a) Federation use case (3-device, simulated): naive vs. attested aggregation
      TVD vs. liar inflation factor.
  (b) Per-device attestation outcomes: liar flag rate vs. honest flag rate vs.
      inflation, with the Hoeffding FPR bound delta = 0.05.
  (c) Hardware validation on ibm_kingston (Heron r2): scatter of predicted
      (synthetic 16-param noise model) vs. measured (real device) Pauli
      expectations across 50 witnesses, with Pearson r and RMSE annotated.

Outputs PNG (300 dpi) + vector PDF for LaTeX. Table IV printed to stdout.
"""
import warnings
warnings.filterwarnings('ignore')

from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

# 2026 modern publication style: Wong colorblind-safe palette + clean spines + no
# marker edges + subtle horizontal-only grid + modern typography.
plt.rcParams.update({
    'font.family': 'sans-serif',
    'font.sans-serif': ['Inter', 'IBM Plex Sans', 'Helvetica', 'Arial', 'DejaVu Sans'],
    'font.size': 9,
    'font.weight': 'normal',
    'axes.titlesize': 10,
    'axes.titleweight': 'bold',
    'axes.titlepad': 8,
    'axes.titlelocation': 'left',
    'axes.labelsize': 9,
    'axes.labelweight': 'normal',
    'axes.labelpad': 3,
    'xtick.labelsize': 8.2,
    'ytick.labelsize': 8.2,
    'xtick.direction': 'out',
    'ytick.direction': 'out',
    'xtick.major.width': 0.8,
    'ytick.major.width': 0.8,
    'legend.fontsize': 7.6,
    'legend.frameon': True,
    'legend.framealpha': 0.96,
    'legend.edgecolor': '#cccccc',
    'legend.borderpad': 0.35,
    'legend.handlelength': 1.5,
    'legend.handletextpad': 0.5,
    'legend.borderaxespad': 0.4,
    'lines.linewidth': 2.0,
    'lines.markersize': 6.5,
    'lines.markeredgewidth': 0.0,
    'axes.spines.top': False,
    'axes.spines.right': False,
    'axes.linewidth': 0.9,
    'axes.edgecolor': '#5a5a5a',
    'axes.grid': True,
    'axes.axisbelow': True,
    'grid.alpha': 0.20,
    'grid.linewidth': 0.6,
    'grid.color': '#9a9a9a',
    'grid.linestyle': '-',
    'patch.linewidth': 0.0,
    'figure.facecolor': 'white',
    'axes.facecolor': 'white',
    'savefig.dpi': 300,
    'savefig.bbox': 'tight',
    'savefig.pad_inches': 0.03,
    'savefig.facecolor': 'white',
    'pdf.fonttype': 42,
    'ps.fonttype': 42,
})

# Wong colorblind-safe palette (Nature standard)
WONG_BLUE    = '#0072B2'
WONG_VERMILL = '#D55E00'
WONG_GREEN   = '#009E73'
WONG_ORANGE  = '#E69F00'
WONG_SKY     = '#56B4E9'
WONG_PURPLE  = '#CC79A7'
WONG_BLACK   = '#000000'

COL_NAIVE   = WONG_VERMILL
COL_ATTEST  = WONG_BLUE
COL_LIAR    = WONG_VERMILL
COL_HONEST  = WONG_BLUE
COL_DELTA   = '#666666'
COL_HW      = WONG_GREEN
COL_DIAG    = '#9a9a9a'
COL_BASE    = '#666666'

PROJ = Path(__file__).parent.parent
PHASE3_NPZ = PROJ / "results" / "phase3_cameraready" / "federation_demo.npz"
HARDWARE_NPZ = PROJ / "results" / "hardware" / "hardware_validation.npz"
OUT_DIR = PROJ / "results" / "contribution3"


def draw_panel_a(ax, p3, title='(a) Federation aggregation'):
    """Naive vs. attested TVD with +103% callout."""
    inflation = p3['inflation_factors']
    ax.errorbar(inflation, p3['naive_mean'], yerr=p3['naive_std'],
                fmt='o-', color=COL_NAIVE, ecolor=COL_NAIVE,
                linewidth=2.0, markersize=6.5, capsize=3.5, capthick=1.2,
                label='Naive FedAvg', zorder=4)
    ax.errorbar(inflation, p3['attested_mean'], yerr=p3['attested_std'],
                fmt='s-', color=COL_ATTEST, ecolor=COL_ATTEST,
                linewidth=2.0, markersize=6.5, capsize=3.5, capthick=1.2,
                label='Attested FedAvg (ours)', zorder=5)
    ax.axhline(float(p3['naive_mean'][0]), color=COL_BASE, linestyle=':', linewidth=1.3,
               label='Honest baseline')
    pct = 100.0 * (float(p3['naive_mean'][-1]) - float(p3['naive_mean'][0])) / float(p3['naive_mean'][0])
    ax.annotate(f'+{pct:.0f}%',
                xy=(float(inflation[-1]) - 0.08, float(p3['naive_mean'][-1])),
                xytext=(3.45, float(p3['naive_mean'][-1]) - 0.018),
                fontsize=10, fontweight='bold', color=COL_NAIVE,
                ha='center',
                arrowprops=dict(arrowstyle='-|>', color=COL_NAIVE, lw=1.0,
                                shrinkA=0, shrinkB=2))
    ax.set_xlabel('Liar noise inflation factor')
    ax.set_ylabel('TVD vs. ideal')
    ax.set_title(title)
    ax.legend(loc='upper left', fontsize=7.5)


def draw_panel_b(ax, p3, title='(b) Attestation outcomes'):
    """Liar vs. honest flag rates."""
    inflation = p3['inflation_factors']
    ax.plot(inflation, p3['flag_rate_liar'], 'o-', color=COL_LIAR,
            linewidth=2.0, markersize=6.5, label='Liar flagged')
    ax.plot(inflation, p3['flag_rate_honest'], 's-', color=COL_HONEST,
            linewidth=2.0, markersize=6.5, label='Honest device flagged')
    ax.axhline(float(p3['delta']), color=COL_DELTA, linestyle=':', linewidth=1.3,
               label=f'Hoeffding FPR (δ={float(p3["delta"]):.2f})')
    sat_idx = int(np.argmax(np.asarray(p3['flag_rate_liar']) >= 1.0))
    if p3['flag_rate_liar'][sat_idx] >= 1.0:
        ax.annotate(f'100% at ≥{float(inflation[sat_idx]):.1f}×',
                    xy=(float(inflation[sat_idx]), 1.0),
                    xytext=(float(inflation[sat_idx]) + 0.55, 0.78),
                    fontsize=8.5, fontweight='bold', color=COL_LIAR,
                    ha='left',
                    arrowprops=dict(arrowstyle='-|>', color=COL_LIAR, lw=1.0,
                                    shrinkA=0, shrinkB=2))
    ax.set_xlabel('Liar noise inflation factor')
    ax.set_ylabel('Flag rate')
    ax.set_title(title)
    ax.set_ylim(-0.04, 1.08)
    ax.legend(loc='center right', fontsize=7.5)


def draw_panel_c(ax, hw, title='(c) Hardware validation'):
    """Predicted vs. measured Pauli expectations on real backend."""
    predicted = np.asarray(hw['predicted'])
    measured = np.asarray(hw['measured'])
    r = float(hw['correlation'])
    rmse = float(hw['rmse'])
    backend_name = str(hw['backend_name'])

    ax.plot([-1, 1], [-1, 1], '--', color=COL_DIAG, linewidth=1.2, alpha=0.85,
            label='y = x  (perfect)')
    ax.scatter(predicted, measured, s=42, color=COL_HW, alpha=0.78,
               edgecolor='white', linewidth=0.8,
               label=f'Witness (N={len(predicted)})')
    ax.text(0.04, 0.96, f"r = {r:.3f}\nRMSE = {rmse:.3f}",
            transform=ax.transAxes,
            fontsize=9.5, fontweight='bold',
            verticalalignment='top',
            bbox=dict(boxstyle='round,pad=0.35', facecolor='white',
                      edgecolor='#cccccc', linewidth=0.9, alpha=0.96))
    ax.set_xlim(-1.05, 1.05)
    ax.set_ylim(-1.05, 1.05)
    ax.set_aspect('equal', adjustable='box')
    ax.set_xlabel('Predicted (16-param model)')
    ax.set_ylabel(f'Measured ({backend_name})')
    ax.set_title(title)
    ax.legend(loc='lower right', fontsize=7.5)


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    if not PHASE3_NPZ.exists():
        raise FileNotFoundError(f"Need {PHASE3_NPZ}")
    if not HARDWARE_NPZ.exists():
        raise FileNotFoundError(f"Need {HARDWARE_NPZ}")

    p3 = np.load(PHASE3_NPZ)
    hw = np.load(HARDWARE_NPZ, allow_pickle=True)
    inflation = p3['inflation_factors']
    predicted = np.asarray(hw['predicted'])
    measured = np.asarray(hw['measured'])
    r = float(hw['correlation'])
    rmse = float(hw['rmse'])
    backend_name = str(hw['backend_name'])

    # ---------- (1) Combined 3-panel figure (textwidth) ---------- #
    fig, axes = plt.subplots(1, 3, figsize=(8.5, 2.85))
    draw_panel_a(axes[0], p3)
    draw_panel_b(axes[1], p3)
    draw_panel_c(axes[2], hw)
    fig.tight_layout(pad=0.7, w_pad=1.2)
    fig.savefig(OUT_DIR / "contribution3_figure.png", dpi=300)
    fig.savefig(OUT_DIR / "contribution3_figure.pdf")
    plt.close(fig)
    print(f"Saved combined: contribution3_figure.{{png, pdf}}")

    # ---------- (2) Individual single-panel figures ---------- #
    # Sized for single-column placement (~3.5in wide).
    panel_specs = [
        ('panel_a_federation',  draw_panel_a, p3, '(a) Federation aggregation', (3.5, 2.7)),
        ('panel_b_attestation', draw_panel_b, p3, '(b) Attestation outcomes',   (3.5, 2.7)),
        ('panel_c_hardware',    draw_panel_c, hw, '(c) Hardware validation',    (3.4, 3.4)),  # square for scatter
    ]
    for name, fn, data, title, fsize in panel_specs:
        f, a = plt.subplots(figsize=fsize)
        fn(a, data, title=title)
        f.tight_layout(pad=0.4)
        f.savefig(OUT_DIR / f"contribution3_{name}.png", dpi=300)
        f.savefig(OUT_DIR / f"contribution3_{name}.pdf")
        plt.close(f)
        print(f"Saved single-panel: contribution3_{name}.{{png, pdf}}")

    # ---- Table IV (markdown) -------------------------------------------- #
    print()
    print("Table IV - Real-world deployment summary")
    print("=" * 72)
    print()
    print("Part A. Federated aggregation (3 devices: 2 honest + 1 liar)")
    print(f"{'Inflation':>10} | {'Naive TVD':>13} | {'Attested TVD':>14} | {'Liar flagged':>13} | {'Honest flagged':>15}")
    print("-" * 72)
    for i, f in enumerate(inflation):
        n, ns = float(p3['naive_mean'][i]), float(p3['naive_std'][i])
        a, as_ = float(p3['attested_mean'][i]), float(p3['attested_std'][i])
        lf = float(p3['flag_rate_liar'][i])
        hf = float(p3['flag_rate_honest'][i])
        print(f"{float(f):>9.1f}x | {n:>5.3f}+/-{ns:.3f} | {a:>5.3f}+/-{as_:.3f}  | {lf:>13.2f} | {hf:>15.2f}")
    print()
    print(f"Part B. Hardware validation on {backend_name} (Heron r2)")
    qubits = list(hw['qubits'])
    print(f"  Qubits used:        {qubits}")
    print(f"  Witnesses:          {int(hw['n_witnesses'])}  (depth={int(hw['depth'])}, shots={int(hw['shots'])})")
    print(f"  Pearson r:          {r:.4f}")
    print(f"  RMSE:               {rmse:.4f}")
    print(f"  Mean abs residual:  {float(np.mean(np.abs(predicted - measured))):.4f}")
    print(f"  Max abs residual:   {float(np.max(np.abs(predicted - measured))):.4f}")
    print(f"  Train residual (synthetic baseline): {float(hw['train_residual']):.4f}")

    np.savez(
        OUT_DIR / "contribution3_data.npz",
        inflation=inflation,
        naive_mean=p3['naive_mean'], naive_std=p3['naive_std'],
        attested_mean=p3['attested_mean'], attested_std=p3['attested_std'],
        flag_rate_liar=p3['flag_rate_liar'],
        flag_rate_honest=p3['flag_rate_honest'],
        delta=p3['delta'],
        hw_predicted=predicted, hw_measured=measured,
        hw_correlation=r, hw_rmse=rmse,
        backend=backend_name, qubits=np.array(qubits),
    )
    print(f"\nSaved combined data: {OUT_DIR / 'contribution3_data.npz'}")


if __name__ == "__main__":
    main()
