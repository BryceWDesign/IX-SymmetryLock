# Implemented architecture

IX-SymmetryLock v0.1.0 is a magnetic-error correction research package. It is not a whole-device fusion solver. It has no I/O path to a physical actuator.

1. `geometry.py` constructs explicit closed polygon conductor centerlines and a toroidal evaluation surface, all in SI units.
2. `field.py` computes the vacuum field of every straight filament segment. Current is linear; total field magnitude is not. The primary field is an explicitly idealized analytic toroidal backbone.
3. `metrics.py` evaluates normal-field error and toroidal variation of total field strength at fixed geometric angles. It also scores externally supplied Boozer coefficients, a separate input domain.
4. `control.py` solves a current-bounded inverse correction problem with an optional nonlinear geometric symmetry inequality. It re-evaluates the total field and rejects infeasible or unconverged proposals.
5. `inverse.py` computes local reachable and unreachable residual components, exact first-order nullspaces, and D-optimal measurement recommendations.
6. `campaign.py` runs paired controls, disabled channels, saturation, independent-grid validation, assumed geometry/current uncertainty and polygon convergence.
7. `evidence.py` writes unsigned integrity manifests, indexes unverified external evidence, groups exact finite decision outcomes and permanently blocks reactor promotion in this release.
8. `accounting.py` derives D-T source energy and particle counts from one externally supplied reaction rate, and refuses a net-electric result when any required plant load is unknown.
9. `audit.py` independently recomputes the 18 primary case/grid records from archived paths and currents and matches executed package hashes.
10. `tracing.py` traces vacuum field lines with B_phi and wall guards. The campaign uses the ideal backbone as a zero-transform negative control.

The field evaluator is physics-based magnetostatics for infinitesimal polygon filaments. The primary field, sampling surface, fault injections and uncertainty assumptions remain idealized. No calibrated measurements or finite-beta force balance are supplied.

No full equilibrium, Q>1, particle-confinement, structural, breeding or power-plant result can be inferred from this pipeline. External solver APIs are not implemented here. There are no empty adapter functions presented as integrations.

The 12-versus-24 comparison changes the available local loop basis while keeping the injected challenge, solver budget and grids fixed. It is a basis-specific controllability comparison. It is not a tokamak-versus-stellarator tournament. Exact axisymmetric, externally transformed QA and bootstrap-assisted QA architectures remain future solver-backed candidates.
