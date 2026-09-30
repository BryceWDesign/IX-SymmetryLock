# Local evaluation and GitHub handoff

Extract the ZIP and open a terminal in the `IX-SymmetryLock` folder containing `pyproject.toml`. Start with `PROOF_OF_CONCEPT.md`, then run the proof yourself.

## Windows PowerShell

Python 3.11, 3.12 or 3.13 is required. These commands do not require activation or a PowerShell execution-policy change.

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-validation.txt
.\.venv\Scripts\python.exe -m pip install -e . --no-deps
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
.\.venv\Scripts\python.exe -m ruff check src tests scripts
.\.venv\Scripts\python.exe -m ruff format --check src tests scripts
.\.venv\Scripts\python.exe -m ix_symmetrylock poc --output results/local
.\.venv\Scripts\python.exe scripts/check_campaign.py results/local
.\.venv\Scripts\python.exe -m ix_symmetrylock verify results/local
.\.venv\Scripts\python.exe -m ix_symmetrylock audit results/local
.\.venv\Scripts\python.exe scripts/plot_campaign.py results/local
```

Dependencies are downloaded by pip. This is a source handoff, not an offline installer with bundled Python/native wheels. `requirements-validation.txt` pins the directly used validation versions; its transitive plotting packages are documented, not hash-locked.

## Linux/macOS

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements-validation.txt
.venv/bin/python -m pip install -e . --no-deps
.venv/bin/python -m unittest discover -s tests -v
.venv/bin/python -m ruff check src tests scripts
.venv/bin/python -m ruff format --check src tests scripts
.venv/bin/python -m ix_symmetrylock poc --output results/local
.venv/bin/python scripts/check_campaign.py results/local
.venv/bin/python -m ix_symmetrylock audit results/local
```

## GitHub push

No GitHub repository was created, changed or published by this handoff. For a new repository, create an empty `IX-SymmetryLock` under your own account, without an auto-generated README or license. Then, from the extracted source folder:

```powershell
git init
git branch -M main
git add -A
git commit -m "Initial release: IX-SymmetryLock v0.1.0"
git remote add origin https://github.com/BryceWDesign/IX-SymmetryLock.git
git push -u origin main
```

These initialization commands apply to a fresh folder. If the destination already has history, clone it and review the differences; do not overwrite its history or force-push.

After GitHub Actions succeeds, tag the tested commit:

```powershell
git tag -a v0.1.0 -m "IX-SymmetryLock v0.1.0 research proof of concept"
git push origin v0.1.0
```

The included workflow runs Linux and Windows with Python 3.11-3.13. Its remote status is unknown until it actually runs. The supplied local validation report identifies exactly which environment was exercised.

Suggested repository description: "Auditable symmetry-constrained magnetic-error correction research: explicit coil fields, bounded inverse correction, controllability, independent-grid tests and fail-closed evidence."

The source is evaluation-only under `LICENSE`, adapted from your StellaratorForge license. Third-party dependencies keep their original terms. The BOM is a complete research inventory with unresolved reactor quantities, not a buildable fusion specification.
