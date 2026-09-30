"""Bounded inverse correction with full nonlinear total-field rechecking."""

from dataclasses import dataclass

import numpy as np
from scipy.optimize import minimize

from .geometry import finite_array
from .metrics import evaluate, geometric_variation, strength_jacobian


@dataclass(frozen=True)
class Limits:
    current_amp_turn: float = 80.0
    symmetry_rms: float = 0.0005
    normal_rms: float = 0.001
    min_reduction: float = 0.5
    ridge: float = 1e-7
    max_iterations: int = 300

    def __post_init__(self):
        values = [self.current_amp_turn, self.symmetry_rms, self.normal_rms, self.ridge]
        if not all(np.isfinite(values)) or min(values[:3]) <= 0 or self.ridge < 0:
            raise ValueError("invalid current, symmetry, normal or regularization limits")
        if not 0 <= self.min_reduction < 1 or self.max_iterations < 1:
            raise ValueError("invalid reduction or iteration limit")


def gate(before, after, currents, limits, solver_success=True):
    reasons = []
    if not all(np.isfinite(list(before.values()))):
        reasons.append("NONFINITE_BASELINE_METRIC")
    if not solver_success:
        reasons.append("SOLVER_DID_NOT_CONVERGE")
    if not np.all(np.isfinite(currents)):
        reasons.append("NONFINITE_COMMAND")
    elif np.max(np.abs(currents), initial=0) > limits.current_amp_turn * (1 + 1e-8):
        reasons.append("CURRENT_LIMIT")
    if not all(np.isfinite(list(after.values()))):
        reasons.append("NONFINITE_METRIC")
        return reasons
    if after["geometric_strength_variation_rms_over_B0"] > limits.symmetry_rms * (1 + 1e-6):
        reasons.append("GEOMETRIC_SYMMETRY_LIMIT")
    if after["normal_rms_over_B0"] > limits.normal_rms:
        reasons.append("NORMAL_FIELD_LIMIT")
    if before["normal_rms_over_B0"] > limits.normal_rms * 0.01:
        if after["normal_rms_over_B0"] > before["normal_rms_over_B0"] * (1 - limits.min_reduction):
            reasons.append("INSUFFICIENT_REDUCTION")
    if after["minimum_field_T"] <= 0:
        reasons.append("VANISHING_FIELD")
    return reasons


def correct(response, background, surface, b0, limits=None, locked=True):
    """Optimize ampere-turns. Output is a proposal with zero device authority.

    response: P x 3 x K, tesla/ampere-turn. background includes the ideal
    backbone and injected fault. The solver sees fields, never fault currents.
    """
    limits = Limits() if limits is None else limits
    a = finite_array(response)
    bg = finite_array(background)
    if a.ndim != 3 or a.shape[:2] != bg.shape or bg.shape != surface.points.shape:
        raise ValueError("invalid field response dimensions")
    if a.shape[2] == 0 or not np.isfinite(b0) or b0 <= 0:
        raise ValueError("no actuator or invalid field scale")
    scale = limits.current_amp_turn
    a = a * scale
    j = np.einsum("pik,pi->pk", a, surface.normals) / b0
    r0 = np.einsum("pi,pi->p", bg, surface.normals) / b0
    norm = max(np.mean(r0**2), limits.normal_rms**2)

    def objective(u):
        r = r0 + j @ u
        return (
            0.5 * np.mean(r**2) / norm + 0.5 * limits.ridge * np.dot(u, u),
            j.T @ r / (len(r) * norm) + limits.ridge * u,
        )

    def symmetry_constraint(u):
        field = bg + np.einsum("pik,k->pi", a, u)
        v = geometric_variation(field, surface.shape, b0)
        c = strength_jacobian(field, a, surface.shape, b0)
        denom = limits.symmetry_rms**2
        return 1 - np.mean(v**2) / denom, -2 * c.T @ v / (len(v) * denom)

    constraints = []
    if locked:
        constraints = [
            {
                "type": "ineq",
                "fun": lambda u: symmetry_constraint(u)[0],
                "jac": lambda u: symmetry_constraint(u)[1],
            }
        ]
    result = minimize(
        objective,
        np.zeros(a.shape[2]),
        jac=True,
        method="SLSQP",
        bounds=[(-1, 1)] * a.shape[2],
        constraints=constraints,
        options={"maxiter": limits.max_iterations, "ftol": 1e-11},
    )
    currents = result.x * scale
    final = bg + np.einsum("pik,k->pi", a, result.x)
    before = evaluate(bg, surface, b0)
    after = evaluate(final, surface, b0)
    reasons = gate(before, after, currents, limits, bool(result.success))
    return {
        "currents_amp_turn": currents,
        "before": before,
        "after": after,
        "accepted": not reasons,
        "rejection_reasons": reasons,
        "solver_success": bool(result.success),
        "solver_message": str(result.message),
        "iterations": int(result.nit),
        "locked": locked,
        "hardware_authority": False,
    }
