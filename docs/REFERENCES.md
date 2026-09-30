# Checked scientific and software references

Checked 2026-09-29. These references establish methods and scope, not IX-SymmetryLock performance or novelty. No future-paper result from prior conversation is credited to this release.

1. E. Rodriguez, E. Paul and A. Bhattacharjee, **Measures of quasisymmetry for stellarators**, 2021 preprint, 2022 journal article. https://arxiv.org/abs/2109.13080 . Discusses multiple QS measures and their limitations; supports using additional physical metrics and QS inequality constraints. Its coefficients/coordinates cannot be replaced by ordinary geometric angles without changing the problem.
2. **SIMSOPT coil optimization documentation**, versioned tutorial. https://simsopt.readthedocs.io/v1.1.1/example_coils.html . Uses explicit filament coils, Biot-Savart fields and normal-field error, with regularization and field-scale restrictions. This repository supplies its own small implementation rather than copying tutorial code or claiming a SIMSOPT integration.
3. **DESC stellarator code suite documentation**. https://desc-docs.readthedocs.io/en/stable/ . External equilibrium/optimization tool for a future solver-backed stage; not installed or executed as part of this release.
4. **Max Planck Institute for Plasma Physics, Wendelstein 7-X**. https://www.ipp.mpg.de/w7x . Distinguishes an optimized stellarator research machine and its power-plant suitability objective from an energy-producing reactor.

Local dependencies and their legal notices are recorded in `BOM/SOFTWARE_BOM.json` and `BOM/third_party_notices/`. These are actual installed-distribution records rather than web-derived package guesses.
