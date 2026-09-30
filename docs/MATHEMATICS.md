# Mathematical contract

## Explicit coil field

For closed polygon vertices x_k, the code evaluates the exact field of each straight segment and sums them:

B(x) = mu0/(4 pi) sum_k integral_segment I dl cross (x - x') / |x - x'|^3.

For vectors a=x-start and b=x-end, the segment contribution per ampere-turn is

(mu0/(4 pi)) (a cross b) (|a|+|b|) / [|a||b| (|a||b|+a dot b)].

The implementation rejects points within the filament clearance. It does not regularize a singular filament into a fictitious winding pack. Polygon refinement tests isolate the remaining circle discretization error. `mu0/(4 pi)=1e-7` is the conventional engineering approximation, not an assertion that post-2019 SI permeability is exact.

B_total = B_backbone + B_fault + sum_k I_k B_k.

The backbone is B_phi=B0 R0/R and B_R=B_Z=0. Its magnitude varies poloidally on the circular torus but not toroidally. It has zero rotational transform. It supplies no validated primary coil construction.

## Residual and geometric symmetry inequality

At fixed geometric-angle surface samples, define

r_p = B_total(x_p) dot n_p / B0.

Let D subtract the toroidal-angle mean independently at each poloidal angle. Define

c = D |B_total| / B0, and q_geom = sqrt(mean(c^2)).

RMS values use equally weighted geometric-angle samples, not area- or volume-weighted integrals. The inequality q_geom <= q_max is checked on the training and held-out grids. q_geom is not quasisymmetry in Boozer coordinates and is not evaluated throughout the plasma volume. The fixed B0 denominator prevents the objective from being improved just by redefining the field scale.

The bounded problem is

min_I 1/2 mean(r^2)/s + lambda/2 ||I/Imax||^2,
subject to |I_k| <= Imax and, when locked, mean(c^2) <= q_max^2.

Here s=max(mean(r_initial^2), normal_limit^2). SLSQP uses analytic current derivatives of the explicitly computed field. Currents are scaled to [-1,1]. A success flag is necessary but insufficient: all declared output gates and the independent grid must also pass.

The magnitude derivative is

d |B| / d I_k = (B/|B|) dot B_k.

The code differentiates the toroidal-mean subtraction and tests the derivative against central differences. No plasma-boundary or coil-shape derivative is claimed.

## Inverse failure correction and local controllability

For a residual vector r and response J, the unconstrained correction solves J delta_I approximately -r. SVD identifies the locally reachable column space.

r_parallel = U_rank U_rank^T r; r_perpendicular = r-r_parallel.

This is a local, linear, unbounded statement. A residual in the column space can still be unreachable under current, geometry, nonlinear or engineering limits. Saturation in the campaign demonstrates that distinction. Relative numerical rank tolerance is 1e-8, in the stated normalized metric.

For an exact first-order lock C delta_I=0, let Z be an orthonormal basis for ker(C). The reduced response is J Z, and the actuator projector is P=Z Z^T. The default real-coil challenge gives zero safe modes when every sampled geometric-strength deviation is required to remain exactly fixed to first order. That is an executed rejection of an over-restrictive formulation, not a missing result. Finite inequality tolerance is therefore tested separately; it is not renamed exact symmetry preservation.

SVD modes are mathematical combinations. Without independent physical interpretation they are not labeled alpha-confinement, divertor or stability actuators.

## External QA spectrum scoring

`boozer_qa_residual` accepts unique real Fourier coefficients for

|B|(psi,theta_B,zeta_B) = sum [cosine_mn cos(m theta_B-n zeta_B) + sine_mn sin(m theta_B-n zeta_B)].

The mode convention uses full-torus n, not n multiplied silently by a field-period count. QA permits n=0. The score is sqrt(power_in_n_nonzero / total_power), using coefficient-squared power and a factor 1/2 for each nonconstant real harmonic. The routine computes this number only. It cannot verify that the coordinates came from a solved equilibrium, that surfaces exist, or that the spectrum truncation is adequate. The PoC does not call it on the geometric grid.

## Information gain

For assumed positive-definite prior information F, candidate measurement response a and noise sigma, the next-measurement score is

log(det(F + a a^T/sigma^2)/det(F)) = log(1 + a^T F^-1 a/sigma^2).

These are recommendations under explicit assumed sensor noise, not executed system identification. No physical measurements have been acquired.

## Conditional energy accounting

A supplied D-T reaction rate R creates alpha birth power R*3.5 MeV and neutron birth power R*14.1 MeV. Alpha deposited and escaped fractions sum to alpha birth power. D/T consumption and He/neutron production share R. No R is inferred from a visually attractive field.

Net electric power is returned only when recovered heat, conversion efficiency and every named recirculating load are supplied. It remains conditional accounting; it does not create or validate those input values.
