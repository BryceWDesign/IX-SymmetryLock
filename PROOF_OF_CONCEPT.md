# Executed proof of concept

Run date: 2026-09-29. Authority: vacuum magnetic-error correction screen. Geometric angles, not Boozer quasisymmetry. All currents are proposals with no hardware authority.

## Primary independent-grid results

| Case | Initial normal RMS/B0 | Final normal RMS/B0 | Reduction | Decision |
|---|---:|---:|---:|---|
| nominal | 4.0665599e-17 | 4.0665599e-17 | nominal | PASS_LOCAL_SCREEN |
| matched_fault_locked | 7.0038747e-05 | 3.8704385e-09 | 99.9945% | PASS_LOCAL_SCREEN |
| displaced_fault_locked | 6.5552111e-05 | 5.3971298e-06 | 91.7667% | PASS_LOCAL_SCREEN |
| displaced_fault_unlocked | 6.5552111e-05 | 5.3971298e-06 | 91.7667% | PASS_LOCAL_SCREEN |
| one_channel_unavailable | 7.0038747e-05 | 4.8879895e-05 | 30.2102% | REJECT |
| current_saturation | 7.0038747e-05 | 6.0627518e-05 | 13.4372% | REJECT |
| twelve_actuator_basis | 6.5552111e-05 | 4.5453489e-05 | 30.6605% | REJECT |
| tight_symmetry_locked | 6.5552111e-05 | 5.3771588e-06 | 91.7971% | REJECT |
| tight_symmetry_unlocked | 6.5552111e-05 | 5.3971298e-06 | 91.7667% | REJECT |

Decisions require both training and held-out gates. Default current cap: 80 AT, geometric variation cap: 5e-4 B0, normal RMS cap: 1e-3 B0, required correction: 50 percent. The fault starts below the absolute normal cap; the reduction gate is therefore essential.

## Independent surface refinement

| Grid | Initial normal RMS/B0 | Final normal RMS/B0 | Reduction | Rejection reasons |
|---|---:|---:|---:|---|
| 49 x 25 | 7.1892276e-05 | 5.2043203e-06 | 92.76095% | none |
| 97 x 49 | 7.4336901e-05 | 4.8898292e-06 | 93.42207% | none |
| 145 x 73 | 7.4338505e-05 | 4.8900854e-06 | 93.42187% | none |

The same displaced-fault command reduces normal-field RMS by **93.4219%** on the 10,585-point grid. The last two final normal RMS estimates differ by **0.005239%**. No command was reoptimized on these grids. The coarser 703-point result is retained, rather than replacing it silently.

## What did not work

The one-channel outage, current cap reduction to 5 AT, and 12-actuator basis do not meet the required reduction. Unbounded controllability does not prevent saturation failure.

Both tight-symmetry cases fail their 1e-6 geometric variation limit. The locked run exhausts 300 iterations and violates the constraint. Its small normal-field improvement is not accepted.

The full exact first-order geometric lock leaves zero safe actuator modes in the default response. This is an over-restrictive formulation for these paths, not a proof that all symmetry-constrained control is impossible.

Under the default tolerance the locked and unlocked displaced corrections are identical. No default-regime benefit from locking is demonstrated. No matched performance superiority over StellaratorForge is established.

## Numerical and uncertainty checks

- 24 segments: relative field L2 error 0.010634664 against an independently constructed 384-segment loop.
- 48 segments: relative field L2 error 0.00263237001 against an independently constructed 384-segment loop.
- 96 segments: relative field L2 error 0.000627051173 against an independently constructed 384-segment loop.
- 192 segments: relative field L2 error 0.000125425053 against an independently constructed 384-segment loop.

The assumed uncertainty screen passes 12/12 draws, using 0.5 mm independent loop translations and 0.5 percent independent current-gain errors. Twelve draws are not a qualified reliability result.

The ideal backbone traces without escape in this short test but has zero rotational transform. Its zero normal field is therefore not a fusion-confinement result.

## Reproduce and audit

```text
python -m ix_symmetrylock poc --output results/local
python scripts/check_campaign.py results/local
python -m ix_symmetrylock verify results/local
python -m ix_symmetrylock audit results/local
```

The audit independently recomputes the 18 primary case/grid evaluations from archived paths and proposals. Source hashes must match. Integrity remains unsigned; neither hashes nor replays authenticate a physical experiment.

The raw campaign, geometry, currents, settings and plots are in `results/poc/`. Reactor promotion remains **false**, and every reactor physics gate is **NOT_RUN**.
