"""Local linear controllability and first-order symmetry-safe modes."""

import numpy as np

from .geometry import finite_array


def nullspace(matrix, rtol=1e-8):
    a = finite_array(matrix)
    if a.ndim != 2 or not 0 < rtol < 1:
        raise ValueError("invalid matrix or relative tolerance")
    _, s, vh = np.linalg.svd(a, full_matrices=True)
    rank = int(np.sum(s > (s[0] * rtol if len(s) and s[0] else 0)))
    return vh[rank:].T, s, rank


def controllability(jacobian, residual, lock_jacobian=None, rtol=1e-8):
    j = finite_array(jacobian)
    r = finite_array(residual)
    if j.ndim != 2 or r.shape != (j.shape[0],):
        raise ValueError("invalid response/residual dimensions")
    if lock_jacobian is None:
        z = np.eye(j.shape[1])
        lock_rank = 0
    else:
        c = finite_array(lock_jacobian)
        if c.ndim != 2 or c.shape[1] != j.shape[1]:
            raise ValueError("lock/actuator dimensions disagree")
        z, _, lock_rank = nullspace(c, rtol)
    reduced = j @ z
    if reduced.shape[1]:
        u, s, _ = np.linalg.svd(reduced, full_matrices=False)
        rank = int(np.sum(s > (s[0] * rtol if len(s) and s[0] else 0)))
        parallel = u[:, :rank] @ (u[:, :rank].T @ r)
        step = -z @ np.linalg.lstsq(reduced, r, rcond=rtol)[0]
    else:
        s = np.zeros(0)
        rank = 0
        parallel = np.zeros_like(r)
        step = np.zeros(j.shape[1])
    perpendicular = r - parallel
    return {
        "rank": rank,
        "lock_rank": lock_rank,
        "safe_mode_count": z.shape[1],
        "singular_values": s,
        "parallel": parallel,
        "perpendicular": perpendicular,
        "step": step,
        "unreachable_fraction": (
            0.0
            if np.linalg.norm(r) < 1e-14
            else float(np.linalg.norm(perpendicular) / np.linalg.norm(r))
        ),
    }


def d_optimal_next(candidates, information, noise_std):
    """Rank a next measurement by log-determinant information gain.

    Caller supplies a positive-definite prior information matrix and sensor
    Jacobians. This is an identification advisor, not a hardware command.
    """
    a = finite_array(candidates)
    info = finite_array(information)
    sigma = finite_array(noise_std)
    if a.ndim != 2 or info.shape != (a.shape[1], a.shape[1]):
        raise ValueError("invalid identification dimensions")
    if sigma.shape != (len(a),) or np.any(sigma <= 0):
        raise ValueError("noise must be positive per candidate")
    if not np.allclose(info, info.T) or np.min(np.linalg.eigvalsh(info)) <= 0:
        raise ValueError("prior information must be positive definite")
    scaled = a / sigma[:, None]
    gain = np.log1p(np.einsum("ki,ik->k", scaled, np.linalg.solve(info, scaled.T)))
    return np.argsort(-gain, kind="stable"), gain
