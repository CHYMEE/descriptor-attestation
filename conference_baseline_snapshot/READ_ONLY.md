# conference_baseline/ — read-only reference

**Do not modify any file in this directory.**

This is a frozen snapshot of the conference repository (`AQC-QEM-Team11`), copied here as the reproducibility baseline for the journal extension. It is the reference point against which all journal experiments are compared.

## Provenance
- **Source:** the original conference repository (path redacted for public release)
- **Copied:** 2026-05-06
- **Selection rule:** code and minimal config needed to re-run the conference experiments. Excluded: `results/`, archive folders, build artifacts (`__pycache__/`, `*.egg-info/`), virtualenvs, slides/notes, and the empty `notebooks/` directory.
- **Included exception:** trained model weights under `weights/` (`best_model_weights.pth`, `best_model_weights_updated.pth`) were copied so experiments are runnable without retraining.

## Rules
1. **No edits.** If a fix or change is needed, copy the file out into the journal codebase and modify it there.
2. **No new files.** This directory should remain a frozen reflection of the conference state.
3. **Reference only.** Import from here at your own risk; prefer copying logic into the journal package once it diverges.
