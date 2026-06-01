"""Regenerate manuscript figures from cached data.

Calls the four figure scripts in figures/source/. Each script reads its
inputs from data/raw/calibration/ or data/processed/<section>/ and
writes to figures/final/.

Run:
    python scripts/08_make_figures.py
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FIGSRC = ROOT / "figures" / "source"

FIG_SCRIPTS = [
    FIGSRC / "make_section5B_completeness.py",
    FIGSRC / "make_section5C_attack_detection.py",
    FIGSRC / "make_section5D_federation_scaling.py",
    FIGSRC / "make_section5E_heldout_margins.py",
]


def main() -> int:
    failures = []
    for path in FIG_SCRIPTS:
        if not path.is_file():
            print(f"[08] SKIP: {path.name} not found", file=sys.stderr)
            failures.append(path.name)
            continue
        print(f"[08] Running {path.name} ...", flush=True)
        # Use the same Python interpreter; ignore warnings; capture output.
        proc = subprocess.run(
            [sys.executable, "-W", "ignore", str(path)],
            cwd=str(ROOT),
            capture_output=True,
            text=True,
        )
        if proc.returncode != 0:
            print(f"     FAIL ({path.name}): exit {proc.returncode}",
                  file=sys.stderr)
            print(proc.stderr[-500:], file=sys.stderr)
            failures.append(path.name)
        else:
            print(f"     OK  ({path.name})")
    if failures:
        print(f"[08] {len(failures)} figure script(s) failed: {failures}",
              file=sys.stderr)
        return 1
    print("[08] All figures regenerated to figures/final/.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
