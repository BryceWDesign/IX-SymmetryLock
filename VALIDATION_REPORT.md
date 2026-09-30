# Local validation report

Executed 2026-09-29, Python 3.12.14, NumPy 2.3.5, SciPy 1.17.0, Matplotlib 3.10.8 and Ruff 0.12.12, Linux.

| Check | Result |
|---|---|
| Unit/integration/CLI tests | 45 passed, 0 failed |
| Ruff lint | PASS |
| Ruff format check | PASS |
| Nine-case campaign contract | PASS, including intentional rejections |
| Output manifest | PASS, unsigned file integrity |
| Archived field/gate audit | 18 case/grid combinations recomputed; 13 package hashes matched |
| Independent surface refinement | 145x73 points; final normal RMS change approximately 0.00524% versus 97x49 |
| Source wheel build and isolated-target install | PASS |
| Installed-wheel campaign and field audit | PASS |
| Reactor promotion | FALSE |
| Windows and Python 3.11/3.13 execution | Not executed locally |
| GitHub Actions | Included; remote run not performed |

The local command log is `results/validation/unittest.log`; the CLI campaign summary and validation metadata are also preserved. Wheel build and full installed-package campaign logs are preserved in the same folder.

A quality pass means the intended implementation, correction and rejection checks reproduce. The locked tight-limit case fails to converge and is correctly rejected. It is not reported as a successful optimizer result.

The published correction percentage is model-specific and applies to one displaced-fault vacuum field challenge. It is not alpha confinement, fusion gain, plant efficiency or evidence that this architecture beats StellaratorForge.
