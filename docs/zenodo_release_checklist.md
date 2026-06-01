# Zenodo release checklist

## Pre-release

- [ ] **Rotate the IBM Quantum API token** that was exposed earlier (if applicable). Generate a new IBM Cloud IAM key, then `QiskitRuntimeService.save_account(token="<new>", overwrite=True)`.
- [ ] **Verify `git status` shows no committed secrets**: `git log -p | grep -iE 'token|secret|api[_-]?key|password'` should return nothing.
- [ ] **Scrub absolute paths**: `grep -rE 'C:\\\\Users|/home/[a-z]+' . --include='*.py' --include='*.json' --include='*.md'` should only hit cached JSONs in `data/processed/section*/` (which we treat as informational metadata, not committed paths).
- [ ] **Run the full test suite**: `pytest -q` — all green.
- [ ] **Run `bash scripts/reproduce_all.sh` in a fresh clone**: every manuscript table and figure regenerates.
- [ ] **Verify the LICENSE attribution**: MIT, copyright year, contributor names finalised.
- [ ] **Update `CITATION.cff`** with final author list and pre-print/DOI placeholders.

## GitHub release

1. Push to `github.com/CHYMEE/descriptor-attestation`:
   ```bash
   git remote add origin git@github.com:CHYMEE/descriptor-attestation.git
   git push -u origin main
   ```
2. Add a `README.md` badge for the build status (optional) and licence:
   ```markdown
   [![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
   ```
3. Create a GitHub release: **Releases → Draft new release**.
   - Tag: `v0.1.0` (semantic version matching `CITATION.cff`).
   - Title: `descriptor-attestation v0.1.0 — QST submission snapshot`.
   - Description: short summary + link to `docs/qst_review_guide.md`.
4. Verify the release tarball includes all expected directories.

## Linking to Zenodo

1. Sign in at [zenodo.org](https://zenodo.org) (preferably with the GitHub-linked account).
2. Go to **Settings → GitHub** and toggle the `CHYMEE/descriptor-attestation` repository ON.
3. Trigger Zenodo by creating the GitHub release (step 3 above) — Zenodo auto-imports tagged releases.
4. Wait ~1 minute for Zenodo to process. The Zenodo record will be at `zenodo.org/record/<id>` with a DOI of the form `10.5281/zenodo.<id>`.
5. **Edit the Zenodo record** to set:
   - License: MIT
   - Communities: (optional) "Quantum Computing", "Quantum Error Mitigation"
   - Related identifiers: link to the QST manuscript DOI once the journal assigns it.
   - Keywords: as in `CITATION.cff`.

## Update `CITATION.cff` and README with the DOI

1. Once Zenodo issues the DOI, edit `CITATION.cff`:
   ```yaml
   doi: "10.5281/zenodo.XXXXXXX"
   identifiers:
     - type: doi
       value: "10.5281/zenodo.XXXXXXX"
       description: "Zenodo archive of the v0.1.0 release"
   ```
2. Update `README.md` "Citation" section with the actual DOI, replacing the `TBD` placeholder.
3. Commit and push these edits. Optionally tag v0.1.1 if you want the DOI'd version itself to reference the DOI (chicken-and-egg: Zenodo always archives the **previous** state, so the DOI in `CITATION.cff` will only appear in the next release. This is fine for QST review purposes — the paper's Data Availability section just needs to cite `10.5281/zenodo.XXXXXXX` once you have it).

## Update the manuscript's Data Availability section

Paste into the paper:

> The code and cached results used to reproduce all tables and figures of this paper are archived at Zenodo with DOI [`10.5281/zenodo.XXXXXXX`](https://doi.org/10.5281/zenodo.XXXXXXX) and mirrored on GitHub at [`github.com/CHYMEE/descriptor-attestation`](https://github.com/CHYMEE/descriptor-attestation). Reproduction requires only Python 3.10+ with `numpy`, `scipy`, `scikit-learn`, `matplotlib`, and `qiskit-aer`; no IBM Quantum credentials are needed.

## Post-release maintenance

- Future tagged releases (`v0.1.1`, `v0.2.0`, …) will be auto-archived by Zenodo with new DOIs. The Zenodo "concept DOI" (resolving to the latest version) is stable; the version-specific DOIs are also stable.
- If you discover an error post-release that requires data/code changes, prefer creating a new patch release rather than amending the existing tag.
- Keep `CITATION.cff` valid (lint via [cffconvert](https://github.com/citation-file-format/cffconvert)).
