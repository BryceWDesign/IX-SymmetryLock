# Validation protocol and limits

## Reproducible challenge

The default geometry has major radius 0.5 m, evaluation minor radius 0.1 m and local loop centers on a 0.19 m winding minor radius. Each of 24 trim loops has radius 0.035 m and 96 straight segments. The ideal toroidal backbone is 0.03 T at the major radius.

Matched fault: +55 AT at trim index 0 and -35 AT at index 10. The displaced fault uses the same two paths shifted by [4,-3,2] mm in Cartesian coordinates. The optimizer receives resulting fields, not the fault currents or inverse solution. A matched-in-span case is a recovery control, not independent evidence of discovery. The displaced case is the less trivial reconstruction challenge.

Training grid: 24 by 12 (288 points). Validation grid: 37 by 19 (703 points) with a half-cell angular offset, never supplied to the optimizer. This is held-out numerical interpolation, not independent experimental validation. Additional offset grids of 49x25, 97x49 and 145x73 points re-evaluate the displaced locked command without reoptimization. The last two normal-field RMS estimates must agree within 5 percent; the actual convergence is reported in the result.

Default current cap is 80 AT per available loop; geometric strength RMS cap is 5e-4 of fixed B0; normal RMS cap is 1e-3 of B0; required reduction is at least 50 percent on each grid for nontrivial initial residuals. The fault is already below the absolute normal cap, so the improvement gate supplies the meaningful correction requirement. No arbitrary improvement percentage is called fusion progress.

All paired cases use the same fault, grid, ridge and 300-iteration budget. Unlocked cases omit only the symmetry constraint; both modes still face the same acceptance tests. The default geometric cap is inactive in the displaced case and produces no measured advantage over the unlocked solution. A 1e-6 cap is an intentional tight-limit stress test, chosen to exercise rejection; it is not claimed to be a physical QA requirement. In the executed campaign both tight cases fail; the locked solver also exhausts its iteration budget.

The missing-channel case removes index 0. The 12-loop case retains even-numbered toroidal stations, and therefore lacks the nearby fault-index-10 actuator. The result shows why this basis matters for this spatial challenge. It does not prove doubling coils always improves confinement or performance.

## Numerical verification

- Circular-loop axis formula, path-reversal sign and rotation covariance.
- Far-field inverse-cube behavior and polygon refinement.
- Geometric symmetry Jacobian checked against central differences.
- SVD residual decomposition and orthogonal projector identities.
- Current, nonfinite input, solver failure and metric rejection checks.
- Manufactured helical field-line transform and zero-transform backbone.
- Tampering, path escape, missing evidence and fabricated PASS labels.
- Energy/particle source closure and unknown recirculating-load rejection.
- CLI and complete campaign contract checked after execution.

The 24, 48, 96 and 192 segment fields are compared with a separately constructed 384-segment reference on validation points. That tests a circular-path approximation, not all possible coil CAD geometries or winding-pack effects.

## Assumed uncertainty

The command from the displaced locked case stays fixed. Each trim loop receives an independent 0.5 mm standard-deviation rigid Cartesian translation; actual current gains receive independent 0.5 percent standard-deviation errors. Twelve samples use seed 20260929. Fault paths remain fixed. There is no adaptive reoptimization during the uncertainty screen.

These assumptions exclude correlated support distortion, non-Gaussian errors, probe uncertainty, missing calibration, dynamics, mutual inductance and temperature-dependent drift. Twelve passes out of twelve are not a certified reliability level or confidence interval. Any new configuration needs fresh convergence, grid and uncertainty checks.

## Physical promotion

A useful correction to a vacuum reference does not provide rotational transform or nested finite-pressure surfaces. The analytic backbone can have zero normal error while its transform is zero, which is why it is included as a negative control. v0.1 reactor promotion always remains false, even when external JSON claims PASS. Production promotion needs verified solver outputs and independent analysis, not status labels.
