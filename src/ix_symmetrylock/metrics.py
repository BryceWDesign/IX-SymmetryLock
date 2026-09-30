"""Geometric-angle strength variation is deliberately NOT named QA."""

import numpy as np


def remove_toroidal_mean(values, shape):
    a = values.reshape(*shape, *values.shape[1:])
    return (a - a.mean(axis=0, keepdims=True)).reshape(values.shape)


def geometric_variation(field, shape, b0):
    strength = np.linalg.norm(field, axis=1)
    return remove_toroidal_mean(strength, shape) / b0


def strength_jacobian(field, response, shape, b0):
    strength = np.linalg.norm(field, axis=1)
    if np.any(strength < b0 * 1e-6):
        raise ValueError("vanishing magnetic field")
    j = np.einsum("pi,pik->pk", field / strength[:, None], response) / b0
    return remove_toroidal_mean(j, shape)


def evaluate(field, surface, b0):
    normal = np.einsum("pi,pi->p", field, surface.normals) / b0
    variation = geometric_variation(field, surface.shape, b0)
    return {
        "normal_rms_over_B0": float(np.sqrt(np.mean(normal**2))),
        "normal_max_over_B0": float(np.max(np.abs(normal))),
        "geometric_strength_variation_rms_over_B0": float(np.sqrt(np.mean(variation**2))),
        "minimum_field_T": float(np.min(np.linalg.norm(field, axis=1))),
    }


def boozer_qa_residual(modes):
    """For independently supplied real Boozer Fourier (m,n,cos,sin) tuples.

    Full-torus n convention. This only scores coefficients; it neither solves
    an equilibrium nor establishes that the caller really used Boozer angles.
    """
    power = total = 0.0
    seen = set()
    for m, n, cosine, sine in modes:
        if not isinstance(m, int) or not isinstance(n, int):
            raise ValueError("mode indices must be integers")
        if m < 0 or (m == 0 and n < 0) or (m, n) in seen:
            raise ValueError("use unique real Fourier modes with m>=0 and n>=0 when m=0")
        seen.add((m, n))
        if not np.isfinite(cosine) or not np.isfinite(sine):
            raise ValueError("nonfinite coefficient")
        if m == 0 and n == 0:
            if sine != 0:
                raise ValueError("zero-mode sine must be zero")
            term = cosine**2
        else:
            term = 0.5 * (cosine**2 + sine**2)
        total += term
        if n != 0:
            power += term
    if total <= 0:
        raise ValueError("empty or zero spectrum")
    return float(np.sqrt(power / total))
