"""Vacuum field-line integrator with explicit escape and B_phi guards."""

import numpy as np


def trace(field, major, start_rz, turns=8, steps_per_turn=128, wall_minor=0.2):
    if turns < 1 or steps_per_turn < 8 or major <= 0 or wall_minor <= 0:
        raise ValueError("invalid trace settings")
    y = np.asarray(start_rz, dtype=float)
    if y.shape != (2,) or not np.all(np.isfinite(y)):
        raise ValueError("invalid starting point")
    h = 2 * np.pi / steps_per_turn
    trajectory = [y.copy()]

    def rhs(phi, rz):
        radius, z = rz
        if radius <= 0:
            raise ValueError("field line reached cylindrical axis")
        c, s = np.cos(phi), np.sin(phi)
        b = np.asarray(field(np.array([[radius * c, radius * s, z]])), dtype=float)[0]
        if b.shape != (3,) or not np.all(np.isfinite(b)):
            raise ValueError("invalid field evaluator")
        br = b[0] * c + b[1] * s
        bp = -b[0] * s + b[1] * c
        if abs(bp) < 1e-12:
            raise ValueError("B_phi too small for toroidal-angle integration")
        return radius * np.array([br, b[2]]) / bp

    escaped = False
    for k in range(turns * steps_per_turn):
        phi = k * h
        k1 = rhs(phi, y)
        k2 = rhs(phi + h / 2, y + h * k1 / 2)
        k3 = rhs(phi + h / 2, y + h * k2 / 2)
        k4 = rhs(phi + h, y + h * k3)
        y = y + h * (k1 + 2 * k2 + 2 * k3 + k4) / 6
        trajectory.append(y.copy())
        if np.hypot(y[0] - major, y[1]) > wall_minor:
            escaped = True
            break
    path = np.array(trajectory)
    theta = np.unwrap(np.arctan2(path[:, 1], path[:, 0] - major))
    elapsed_phi = h * (len(path) - 1)
    return {
        "trajectory_rz_m": path,
        "finite_trace_iota": float((theta[-1] - theta[0]) / elapsed_phi),
        "escaped": escaped,
        "turns_completed": elapsed_phi / (2 * np.pi),
    }
