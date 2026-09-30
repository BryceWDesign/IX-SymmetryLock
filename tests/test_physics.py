import unittest

import numpy as np

from ix_symmetrylock.field import basis, biot_savart, toroidal_backbone
from ix_symmetrylock.geometry import Coil, circle, torus, trim_array
from ix_symmetrylock.metrics import boozer_qa_residual, geometric_variation, strength_jacobian
from ix_symmetrylock.tracing import trace


class FieldTests(unittest.TestCase):
    def test_large_point_batches_equal_small_evaluation(self):
        coil = circle("loop", [0, 0, 0], [0, 0, 1], 0.1)
        p = np.array([[0.02, 0.01, 0.05]])
        result = biot_savart(coil, np.tile(p, (2051, 1)))
        expected = np.tile(biot_savart(coil, p), (2051, 1))
        np.testing.assert_allclose(result, expected, atol=1e-18)

    def test_circular_loop_axis_against_analytic(self):
        radius = 0.13
        coil = circle("loop", [0, 0, 0], [0, 0, 1], radius, 768)
        z = np.array([0.0, 0.03, 0.2])
        field = biot_savart(coil, np.column_stack([z * 0, z * 0, z]))
        analytic = 2 * np.pi * 1e-7 * radius**2 / (radius**2 + z**2) ** 1.5
        np.testing.assert_allclose(field[:, 2], analytic, rtol=1e-5)
        np.testing.assert_allclose(field[:, :2], 0, atol=1e-18)

    def test_reverse_path_reverses_field(self):
        coil = circle("loop", [0, 0, 0], [0, 0, 1], 0.1)
        p = np.array([[0.02, 0.01, 0.05]])
        np.testing.assert_allclose(
            biot_savart(Coil("reversed", coil.vertices[::-1]), p), -biot_savart(coil, p), atol=1e-18
        )

    def test_rotation_covariance(self):
        angle = 0.71
        rotation = np.array(
            [[np.cos(angle), -np.sin(angle), 0], [np.sin(angle), np.cos(angle), 0], [0, 0, 1]]
        )
        coil = circle("loop", [0.1, 0, 0], [0, 1, 1], 0.04)
        p = np.array([[0.2, 0.1, 0.2]])
        np.testing.assert_allclose(
            biot_savart(Coil("rotated", coil.vertices @ rotation.T), p @ rotation.T),
            biot_savart(coil, p) @ rotation.T,
            rtol=1e-12,
        )

    def test_far_field_inverse_cube(self):
        coil = circle("loop", [0, 0, 0], [0, 0, 1], 0.01)
        f = biot_savart(coil, np.array([[0, 0, 1.0], [0, 0, 2.0]]))[:, 2]
        self.assertAlmostEqual(f[0] / f[1], 8, delta=0.001)

    def test_polygon_convergence(self):
        p = np.array([[0.0, 0.0, 0.03]])
        exact = 2 * np.pi * 1e-7 * 0.1**2 / (0.1**2 + 0.03**2) ** 1.5
        errors = [
            abs(biot_savart(circle("loop", [0, 0, 0], [0, 0, 1], 0.1, n), p)[0, 2] - exact)
            for n in [16, 32, 64]
        ]
        self.assertGreater(errors[0], errors[1] * 3)
        self.assertGreater(errors[1], errors[2] * 3)

    def test_filament_collision_rejected(self):
        coil = circle("loop", [0, 0, 0], [0, 0, 1], 0.1)
        with self.assertRaises(ValueError):
            biot_savart(coil, coil.vertices[:1])

    def test_backbone_has_zero_normal_field_and_geometric_variation(self):
        s = torus()
        b = toroidal_backbone(s.points)
        np.testing.assert_allclose(np.sum(b * s.normals, axis=1), 0, atol=1e-17)
        np.testing.assert_allclose(geometric_variation(b, s.shape, 0.03), 0, atol=1e-14)

    def test_strength_derivative_finite_difference(self):
        s = torus(nphi=8, ntheta=8)
        a = basis(trim_array(nphi=2, ntheta=2), s.points)
        u = np.array([3.0, -2.0, 1.0, 4.0])
        b = toroidal_backbone(s.points) + np.einsum("pik,k->pi", a, u)
        analytic = strength_jacobian(b, a, s.shape, 0.03)
        h = 0.001
        for k in range(4):
            numeric = (
                geometric_variation(b + a[:, :, k] * h, s.shape, 0.03)
                - geometric_variation(b - a[:, :, k] * h, s.shape, 0.03)
            ) / (2 * h)
            np.testing.assert_allclose(analytic[:, k], numeric, atol=1e-12, rtol=1e-5)

    def test_backbone_no_transform_negative_control(self):
        r = trace(toroidal_backbone, 0.5, [0.56, 0.0], turns=3)
        self.assertFalse(r["escaped"])
        self.assertAlmostEqual(r["finite_trace_iota"], 0, places=12)

    def test_trace_known_helical_manufactured_field(self):
        def field(points):
            radius = np.linalg.norm(points[:, :2], axis=1)
            er = points[:, :2] / radius[:, None]
            b = np.zeros_like(points)
            br = -0.3 * points[:, 2] / radius
            b[:, :2] = br[:, None] * er + np.column_stack([-er[:, 1], er[:, 0]])
            b[:, 2] = 0.3 * (radius - 0.5) / radius
            return b

        r = trace(field, 0.5, [0.56, 0.0], turns=8)
        self.assertAlmostEqual(r["finite_trace_iota"], 0.3, places=7)

    def test_trace_vanishing_phi_rejected(self):
        with self.assertRaises(ValueError):
            trace(lambda p: np.zeros_like(p), 0.5, [0.56, 0.0])

    def test_qa_external_coefficient_score(self):
        self.assertEqual(boozer_qa_residual([(0, 0, 2.0, 0.0), (1, 0, 0.4, 0.0)]), 0)
        q = boozer_qa_residual([(0, 0, 2.0, 0.0), (1, 2, 0.4, 0.0)])
        self.assertAlmostEqual(q, np.sqrt(0.08 / 4.08))

    def test_qa_invalid_spectrum_rejected(self):
        for modes in [[], [(0, 0, 0.0, 0.0)], [(0, 0, 1.0, 2.0)], [(1, 2, np.nan, 0.0)]]:
            with self.assertRaises(ValueError):
                boozer_qa_residual(modes)

    def test_invalid_geometry_rejected(self):
        with self.assertRaises(ValueError):
            circle("bad", [0, 0, 0], [0, 0, 0], 0.1)
        with self.assertRaises(ValueError):
            torus(minor=0.6)
        with self.assertRaises(ValueError):
            Coil("bad", np.zeros((10, 3)))


if __name__ == "__main__":
    unittest.main()
