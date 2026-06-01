"""
Build Fig. 1 (Methods/Setup) showing the actual quantum circuits and hardware
qubit allocation used in the witness protocol.

Three labeled sub-panels:
  (a) Example random-Clifford witness circuit (depth 5 layers, 4 qubits) with the
      basis-change rotation appended for one random Pauli observable + final
      Z-basis measurement.
  (b) Federation target circuit: 4-qubit GHZ state preparation.
  (c) Hardware qubit allocation: linear chain [15, 14, 13, 12] on ibm_kingston
      with their per-qubit calibration (T1, T2, gate err, readout err) overlaid.

Outputs PNG (300 dpi) + vector PDF for LaTeX. Both a combined figure and three
single-panel figures are emitted.
"""
import warnings
warnings.filterwarnings('ignore')

from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
import matplotlib.patches as mpatches

from qiskit import QuantumCircuit

from qem import WitnessSet
from qem.witness import _random_clifford_circuit, _random_nonidentity_pauli


PROJ = Path(__file__).parent.parent
OUT_DIR = PROJ / "results" / "methods_figure"
HARDWARE_NPZ = PROJ / "results" / "hardware" / "hardware_validation.npz"


# 2026 publication style (matches contribution figures)
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
    'xtick.labelsize': 8.2,
    'ytick.labelsize': 8.2,
    'legend.fontsize': 7.6,
    'savefig.dpi': 300,
    'savefig.bbox': 'tight',
    'savefig.pad_inches': 0.04,
    'pdf.fonttype': 42,
    'ps.fonttype': 42,
})

WONG_BLUE    = '#0072B2'
WONG_VERMILL = '#D55E00'
WONG_GREEN   = '#009E73'
WONG_ORANGE  = '#E69F00'
WONG_SKY     = '#56B4E9'


def build_example_witness_circuit():
    """One random Clifford witness with basis rotation + measurement (seed=42, idx=0)."""
    rng = np.random.default_rng(42)
    qc = _random_clifford_circuit(n_qubits=4, depth=5, rng=rng)
    pauli = _random_nonidentity_pauli(n_qubits=4, rng=rng)
    # Apply basis change so the Pauli becomes diagonal in Z (mirrors WitnessSet._apply_basis_change)
    prepared = qc.copy()
    label = pauli.to_label().lstrip('+-')
    n = len(label)
    # Mark a barrier so the diagram visually separates Clifford / basis change
    prepared.barrier(label='basis')
    for i, ch in enumerate(label):
        q = n - 1 - i
        if ch == 'X':
            prepared.h(q)
        elif ch == 'Y':
            prepared.sdg(q)
            prepared.h(q)
    prepared.measure_all()
    return prepared, pauli, qc


def build_target_circuit():
    qc = QuantumCircuit(4, name='GHZ-4')
    qc.h(0)
    qc.cx(0, 1)
    qc.cx(1, 2)
    qc.cx(2, 3)
    return qc


def draw_circuit_panel(ax, circuit, title, fold=-1):
    """Render a qiskit circuit into a matplotlib Axes."""
    # Qiskit's mpl drawer creates its own figure; we render to a temp fig then
    # composite the rasterized image into our axes.
    from qiskit.visualization import circuit_drawer
    tmp_fig = circuit_drawer(circuit, output='mpl', style='iqp', fold=fold)
    tmp_fig.canvas.draw()
    buf = np.asarray(tmp_fig.canvas.buffer_rgba())
    plt.close(tmp_fig)
    ax.imshow(buf)
    ax.set_axis_off()
    ax.set_title(title, loc='left', fontweight='bold', fontsize=10)


def draw_hardware_panel(ax, hw, title='(c) Hardware qubits on ibm_kingston'):
    """Linear-chain diagram of selected hardware qubits with calibration overlays."""
    qubits = [int(q) for q in hw['qubits']]
    t1s = list(hw['descriptor_t1'])
    t2s = list(hw['descriptor_t2'])
    gates = list(hw['descriptor_gate'])
    readouts = list(hw['descriptor_ro'])

    n = len(qubits)
    spacing = 1.9                              # widen so per-qubit text doesn't overlap
    xs = np.arange(n) * spacing
    y = 0.0
    node_r = 0.32

    # Edges (linear chain)
    for i in range(n - 1):
        ax.plot([xs[i] + node_r, xs[i + 1] - node_r], [y, y],
                color='#888888', linewidth=2.5, zorder=1)
        ax.text((xs[i] + xs[i + 1]) / 2, y + 0.22, 'CX',
                ha='center', va='bottom', fontsize=7.5,
                color='#444444', style='italic')

    # Nodes
    for i, q in enumerate(qubits):
        circle = mpatches.Circle((xs[i], y), node_r,
                                 facecolor=WONG_BLUE, edgecolor='black',
                                 linewidth=1.0, zorder=3)
        ax.add_patch(circle)
        ax.text(xs[i], y, f'Q{q}',
                ha='center', va='center',
                color='white', fontweight='bold', fontsize=10, zorder=4)

    # Calibration as a 4-row table below the chain — same y for each row across qubits
    row_labels = [r'$T_1$ (μs)', r'$T_2$ (μs)', 'gate', 'readout']
    row_values = [
        [f"{t1s[i]:.0f}" for i in range(n)],
        [f"{t2s[i]:.0f}" for i in range(n)],
        [f"{gates[i]*1e3:.2f}e-3" for i in range(n)],
        [f"{readouts[i]*100:.1f}%" for i in range(n)],
    ]
    base_y = -0.55
    row_dy = 0.32
    for r, (lab, vals) in enumerate(zip(row_labels, row_values)):
        ax.text(-0.95, base_y - r * row_dy, lab,
                ha='right', va='center', fontsize=8, color='#222222', fontweight='bold')
        for i, v in enumerate(vals):
            ax.text(xs[i], base_y - r * row_dy, v,
                    ha='center', va='center', fontsize=8,
                    family='monospace', color='#222222')

    ax.set_xlim(-1.5, xs[-1] + 0.6)
    ax.set_ylim(base_y - (len(row_labels) - 1) * row_dy - 0.35, 0.85)
    ax.set_aspect('equal')
    ax.set_axis_off()
    ax.set_title(title, loc='left', fontweight='bold', fontsize=10)


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    if not HARDWARE_NPZ.exists():
        raise FileNotFoundError(f"Need {HARDWARE_NPZ}")
    hw = np.load(HARDWARE_NPZ, allow_pickle=True)

    witness_circ, pauli, _ = build_example_witness_circuit()
    target_circ = build_target_circuit()
    print(f"Example witness Pauli observable: {pauli.to_label()}")

    # ---- Combined 3-panel figure ---- #
    fig = plt.figure(figsize=(8.5, 4.4))
    gs = fig.add_gridspec(2, 2, height_ratios=[1.4, 1.0],
                          hspace=0.45, wspace=0.18)

    ax_witness = fig.add_subplot(gs[0, :])     # top row spans both cols
    draw_circuit_panel(ax_witness, witness_circ,
                       title=f'(a) Example witness circuit  (depth=5 layers, Pauli observable {pauli.to_label()})')

    ax_target = fig.add_subplot(gs[1, 0])
    draw_circuit_panel(ax_target, target_circ,
                       title='(b) Federation target: GHZ-4')

    ax_hw = fig.add_subplot(gs[1, 1])
    draw_hardware_panel(ax_hw, hw)

    fig.savefig(OUT_DIR / "methods_figure.png", dpi=300)
    fig.savefig(OUT_DIR / "methods_figure.pdf")
    plt.close(fig)
    print(f"Saved combined: methods_figure.{{png, pdf}}")

    # ---- Individual single-panel figures ---- #
    # (a) witness circuit alone
    f, a = plt.subplots(figsize=(7.0, 2.4))
    draw_circuit_panel(a, witness_circ,
                       title=f'(a) Example witness circuit (Pauli {pauli.to_label()})')
    f.savefig(OUT_DIR / "methods_panel_a_witness_circuit.png", dpi=300)
    f.savefig(OUT_DIR / "methods_panel_a_witness_circuit.pdf")
    plt.close(f)

    # (b) target circuit alone
    f, a = plt.subplots(figsize=(3.4, 2.0))
    draw_circuit_panel(a, target_circ, title='(b) Target circuit: GHZ-4')
    f.savefig(OUT_DIR / "methods_panel_b_target_circuit.png", dpi=300)
    f.savefig(OUT_DIR / "methods_panel_b_target_circuit.pdf")
    plt.close(f)

    # (c) hardware qubits alone
    f, a = plt.subplots(figsize=(4.6, 2.4))
    draw_hardware_panel(a, hw, title='(c) Hardware qubits on ibm_kingston')
    f.savefig(OUT_DIR / "methods_panel_c_hardware_qubits.png", dpi=300)
    f.savefig(OUT_DIR / "methods_panel_c_hardware_qubits.pdf")
    plt.close(f)
    print("Saved single-panels: methods_panel_a/b/c.{png, pdf}")


if __name__ == "__main__":
    main()
