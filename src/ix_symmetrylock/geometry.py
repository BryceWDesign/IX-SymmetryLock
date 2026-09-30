"""Explicit SI coil paths and geometric-angle sampling, not flux coordinates."""

from dataclasses import dataclass

import numpy as np


def finite_array(value, shape=None):
    a = np.asarray(value, dtype=float)
    if not np.all(np.isfinite(a)) or (shape is not None and a.shape != shape):
        raise ValueError("invalid shape or nonfinite array")
    return a


@dataclass(frozen=True)
class Coil:
    name: str
    vertices: np.ndarray

    def __post_init__(self):
        a = finite_array(self.vertices)
        if a.ndim != 2 or a.shape[1] != 3 or len(a) < 8:
            raise ValueError("coil requires at least eight 3-D vertices")
        if np.any(np.linalg.norm(np.roll(a, -1, axis=0) - a, axis=1) < 1e-10):
            raise ValueError("zero length coil segment")
        a = a.copy()
        a.setflags(write=False)
        object.__setattr__(self, "vertices", a)

    @property
    def length_m(self):
        return float(
            np.linalg.norm(np.roll(self.vertices, -1, axis=0) - self.vertices, axis=1).sum()
        )


def circle(name, center, normal, radius, segments=96):
    center = finite_array(center, (3,))
    normal = finite_array(normal, (3,))
    if np.linalg.norm(normal) == 0 or radius <= 0 or not np.isfinite(radius):
        raise ValueError("invalid circle")
    if not isinstance(segments, int) or segments < 8:
        raise ValueError("segments must be an integer >= 8")
    normal = normal / np.linalg.norm(normal)
    seed = np.eye(3)[np.argmin(np.abs(normal))]
    e1 = np.cross(normal, seed)
    e1 /= np.linalg.norm(e1)
    e2 = np.cross(normal, e1)
    t = np.arange(segments) * 2 * np.pi / segments
    return Coil(name, center + radius * (np.cos(t)[:, None] * e1 + np.sin(t)[:, None] * e2))


def trim_array(major=0.5, winding_minor=0.19, radius=0.035, nphi=8, ntheta=3, segments=96):
    """Small local loops, none encircling the toroidal plasma cross-section."""
    result = []
    for i in range(nphi):
        phi = 2 * np.pi * i / nphi
        er = np.array([np.cos(phi), np.sin(phi), 0.0])
        for j in range(ntheta):
            theta = 2 * np.pi * j / ntheta
            normal = np.cos(theta) * er + np.array([0, 0, np.sin(theta)])
            center = major * er + winding_minor * normal
            result.append(circle(f"trim_{i:02d}_{j:02d}", center, normal, radius, segments))
    return result


@dataclass(frozen=True)
class Surface:
    points: np.ndarray
    normals: np.ndarray
    shape: tuple


def torus(major=0.5, minor=0.1, nphi=24, ntheta=12, offset=0.0):
    if not 0 < minor < major or min(nphi, ntheta) < 4:
        raise ValueError("invalid torus or sampling")
    phi = 2 * np.pi * (np.arange(nphi) + offset) / nphi
    theta = 2 * np.pi * (np.arange(ntheta) + offset) / ntheta
    ph, th = np.meshgrid(phi, theta, indexing="ij")
    er = np.stack([np.cos(ph), np.sin(ph), np.zeros_like(ph)], axis=-1)
    ez = np.zeros_like(er)
    ez[..., 2] = 1
    normal = np.cos(th)[..., None] * er + np.sin(th)[..., None] * ez
    return Surface(
        (major * er + minor * normal).reshape(-1, 3), normal.reshape(-1, 3), (nphi, ntheta)
    )
