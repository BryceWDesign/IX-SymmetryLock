# Solver-backed continuation

The next decisive work is a single verified equilibrium, not a more elaborate reactor picture.

1. Select a reproducible external QA reference equilibrium with explicit license, coil/boundary inputs and known provenance. Solve finite-pressure force balance using DESC or VMEC-family tooling; compare independent implementations where feasible.
2. Convert solved surfaces and total-field strength to Boozer coordinates. Check resolution and harmonic conventions. Replace the geometric PoC inequality with a justified QS inequality plus transform, topology and orbit constraints.
3. Evaluate the actual coil set through an established implementation such as SIMSOPT and independently compare its Biot-Savart field with this segment evaluator. Determine the coil/plasma clearance and winding-pack field, not just centerlines.
4. Form physically scaled sensitivities of real residuals. Analyze attainable corrections with bounded currents and nonlinear re-solves. An unreachable local residual is a signal to change degrees of freedom, not a global impossibility proof.
5. Test coil/boundary/support co-design with qualified geometry and structural evaluators. Current modes that improve normal field cannot automatically be credited with alpha confinement, stability or stress benefits.
6. Add particle orbits, neoclassical transport, gyrokinetics, MHD, divertor/ash, neutronics/TBR, material lifetime and a causal burn/fuel/plant ledger.
7. Run matched architecture comparisons only after the models and engineering burdens have comparable authority: ideal axisymmetric reference, externally transformed QA, and bootstrap-assisted QA.
8. Conduct independent physical measurements and qualification under a separate engineering program. Research code remains advisory until a real safety and authority design is established.

No step above is represented by an empty executable adapter or a prewritten PASS record in this release. The full unresolved functional inventory is in `BOM/FULL_BOM.csv`.
