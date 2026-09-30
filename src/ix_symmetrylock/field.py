"""Exact finite straight-segment Biot-Savart fields for closed polygon coils."""

import numpy as np

from .geometry import finite_array

MU0_OVER_4PI = 1e-7  # conventional engineering permeability, T m / A


def biot_savart(coil, points, clearance=1e-7):
    """T per ampere-turn. Raise near a filament; never silently soften it."""
    points = finite_array(points)
    if points.ndim != 2 or points.shape[1] != 3:
        raise ValueError("points must be N by 3")
    if not np.isfinite(clearance) or clearance <= 0:
        raise ValueError("clearance must be positive")
    if len(points) > 1024:
        return np.concatenate(
            [
                biot_savart(coil, points[k : k + 1024], clearance)
                for k in range(0, len(points), 1024)
            ]
        )
    start = coil.vertices
    end = np.roll(start, -1, axis=0)
    dl = end - start
    a = points[:, None, :] - start
    b = points[:, None, :] - end
    t = np.clip(np.einsum("psi,si->ps", a, dl) / np.einsum("si,si->s", dl, dl), 0, 1)
    distance = np.linalg.norm(a - t[..., None] * dl, axis=2)
    if np.any(distance < clearance):
        raise ValueError("evaluation point intersects filament clearance")
    na = np.linalg.norm(a, axis=2)
    nb = np.linalg.norm(b, axis=2)
    ab = na * nb
    denominator = ab * (ab + np.einsum("psi,psi->ps", a, b))
    # Collinear points beyond a segment have zero field. The denominator is
    # positive there. Interior collinear points were rejected by clearance.
    if np.any(denominator <= 0):
        raise ValueError("ill-conditioned segment geometry")
    factor = (na + nb) / denominator
    result = MU0_OVER_4PI * np.sum(np.cross(a, b) * factor[..., None], axis=1)
    return finite_array(result)


def basis(coils, points):
    if not coils:
        raise ValueError("empty coil basis")
    return np.stack([biot_savart(c, points) for c in coils], axis=-1)


def toroidal_backbone(points, major=0.5, axis_field=0.03):
    """Ideal B_phi=B0 R0/R, NOT a solved or buildable primary coil system."""
    points = finite_array(points)
    r2 = np.sum(points[:, :2] ** 2, axis=1)
    if np.any(r2 <= 0) or axis_field <= 0:
        raise ValueError("backbone requires R>0 and B0>0")
    out = np.zeros_like(points)
    out[:, 0] = -axis_field * major * points[:, 1] / r2
    out[:, 1] = axis_field * major * points[:, 0] / r2
    return out
