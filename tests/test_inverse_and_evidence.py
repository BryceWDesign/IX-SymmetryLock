import tempfile
import unittest
from pathlib import Path

import numpy as np

from ix_symmetrylock.accounting import PLANT_LOADS, dt_source, plant_balance
from ix_symmetrylock.control import Limits, correct, gate
from ix_symmetrylock.evidence import (
    REACTOR_GATES,
    build_manifest,
    finite_behavior_groups,
    promotion_receipt,
    verify_manifest,
)
from ix_symmetrylock.field import basis, toroidal_backbone
from ix_symmetrylock.geometry import torus, trim_array
from ix_symmetrylock.inverse import controllability, d_optimal_next, nullspace
from ix_symmetrylock.metrics import evaluate


class InverseTests(unittest.TestCase):
    def test_nullspace_projector(self):
        c = np.array([[1.0, 1.0, 0.0]])
        z, _, rank = nullspace(c)
        self.assertEqual(rank, 1)
        np.testing.assert_allclose(c @ z, 0, atol=1e-15)
        p = z @ z.T
        np.testing.assert_allclose(p @ p, p, atol=1e-15)

    def test_correctable_and_uncorrectable_residual(self):
        j = np.array([[1.0, 0.0], [0.0, 1.0], [0.0, 0.0]])
        r = np.array([3.0, 4.0, 12.0])
        result = controllability(j, r)
        np.testing.assert_allclose(result["parallel"], [3, 4, 0])
        np.testing.assert_allclose(result["perpendicular"], [0, 0, 12])
        np.testing.assert_allclose(j @ result["step"], -result["parallel"])
        self.assertAlmostEqual(result["unreachable_fraction"], 12 / 13)

    def test_symmetry_projection_changes_reachable_space(self):
        result = controllability(np.eye(3), np.array([2.0, 3.0, 4.0]), np.array([[1.0, 0.0, 0.0]]))
        np.testing.assert_allclose(result["step"], [0, -3, -4])
        self.assertEqual(result["safe_mode_count"], 2)
        self.assertAlmostEqual(result["perpendicular"][0], 2)

    def test_no_safe_modes(self):
        result = controllability(np.eye(2), np.ones(2), np.eye(2))
        self.assertEqual(result["safe_mode_count"], 0)
        self.assertEqual(result["unreachable_fraction"], 1)

    def test_information_ranking_penalizes_noise(self):
        candidates = np.array([[1.0, 0.0], [2.0, 0.0], [0.0, 1.0]])
        ranking, gains = d_optimal_next(candidates, np.eye(2), np.array([1.0, 10.0, 0.5]))
        self.assertEqual(list(ranking), [2, 0, 1])
        self.assertGreater(gains[2], gains[0])

    def test_information_bad_prior(self):
        with self.assertRaises(ValueError):
            d_optimal_next(np.eye(2), np.zeros((2, 2)), np.ones(2))

    def test_current_symmetry_and_nan_gates(self):
        metrics = {
            "normal_rms_over_B0": 0.01,
            "geometric_strength_variation_rms_over_B0": 0.02,
            "minimum_field_T": 0.03,
        }
        reasons = gate(metrics, metrics, np.array([100.0]), Limits())
        self.assertIn("CURRENT_LIMIT", reasons)
        self.assertIn("GEOMETRIC_SYMMETRY_LIMIT", reasons)
        self.assertIn("NORMAL_FIELD_LIMIT", reasons)
        self.assertIn("INSUFFICIENT_REDUCTION", reasons)
        self.assertIn(
            "SOLVER_DID_NOT_CONVERGE", gate(metrics, metrics, np.array([0]), Limits(), False)
        )
        bad = dict(metrics, minimum_field_T=float("nan"))
        self.assertIn("NONFINITE_METRIC", gate(metrics, bad, np.array([0]), Limits()))

    def test_bounded_inverse_known_fault(self):
        surface = torus(nphi=12, ntheta=8)
        response = basis(trim_array(nphi=4, ntheta=2), surface.points)
        current = np.zeros(8)
        current[0] = 40
        bg = toroidal_backbone(surface.points) + np.einsum("pik,k->pi", response, current)
        result = correct(response, bg, surface, 0.03)
        self.assertTrue(result["accepted"], result["rejection_reasons"])
        self.assertLess(
            result["after"]["normal_rms_over_B0"], result["before"]["normal_rms_over_B0"] * 0.01
        )
        self.assertFalse(result["hardware_authority"])

    def test_saturation_is_rejected(self):
        surface = torus(nphi=12, ntheta=8)
        response = basis(trim_array(nphi=4, ntheta=2), surface.points)
        bg = toroidal_backbone(surface.points) + response[:, :, 0] * 70
        result = correct(response, bg, surface, 0.03, Limits(current_amp_turn=0.1))
        self.assertFalse(result["accepted"])
        self.assertLessEqual(np.max(np.abs(result["currents_amp_turn"])), 0.1 * (1 + 1e-8))

    def test_nonfinite_inputs_and_limits_rejected(self):
        for kwargs in [{"current_amp_turn": 0}, {"symmetry_rms": np.nan}, {"ridge": -1}]:
            with self.assertRaises(ValueError):
                Limits(**kwargs)
        with self.assertRaises(ValueError):
            controllability(np.array([[np.nan]]), np.ones(1))

    def test_perfect_measurement_not_reactor_credit(self):
        surface = torus()
        metrics = evaluate(toroidal_backbone(surface.points), surface, 0.03)
        self.assertLess(metrics["normal_rms_over_B0"], 1e-15)
        self.assertFalse(promotion_receipt({})["reactor_promoted"])


class EvidenceTests(unittest.TestCase):
    def test_manifest_detects_tampering(self):
        with tempfile.TemporaryDirectory() as directory:
            p = Path(directory) / "result.json"
            p.write_text("{}")
            m = build_manifest(directory, [p])
            self.assertEqual(verify_manifest(directory, m), 1)
            p.write_text('{"pass":true}')
            with self.assertRaises(ValueError):
                verify_manifest(directory, m)

    def test_manifest_path_escape_blocked(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(ValueError):
                verify_manifest(
                    directory,
                    {"schema": "ix-symmetrylock.integrity.v1", "files": {"../outside": "x"}},
                )

    def test_empty_manifest_rejected(self):
        with self.assertRaises(ValueError):
            verify_manifest(".", {"schema": "ix-symmetrylock.integrity.v1", "files": {}})

    def test_missing_solver_records_fail_closed(self):
        result = promotion_receipt({})
        self.assertFalse(result["reactor_promoted"])
        self.assertTrue(all(r["status"] == "NOT_RUN" for r in result["gates"].values()))

    def test_forged_pass_labels_do_not_promote(self):
        result = promotion_receipt({g: {"status": "PASS"} for g in REACTOR_GATES})
        self.assertFalse(result["reactor_promoted"])
        self.assertTrue(all(r["status"] == "UNVERIFIED_EXTERNAL" for r in result["gates"].values()))

    def test_finite_behavior_equality_is_exact(self):
        groups = finite_behavior_groups({"a": [True, 1], "b": [True, 1], "c": [True, 1.001]})
        self.assertEqual(groups, [["a", "b"], ["c"]])

    def test_dt_energy_and_particles_close(self):
        result = dt_source(1e15, 0.6)
        self.assertAlmostEqual(
            result["alpha_birth_W"] + result["neutron_birth_W"], result["fusion_W"]
        )
        self.assertAlmostEqual(
            result["alpha_deposited_W"] + result["alpha_escape_W"], result["alpha_birth_W"]
        )
        self.assertEqual(result["tritons_consumed_per_second"], result["neutrons_per_second"])

    def test_unknown_load_blocks_net_electric_claim(self):
        result = plant_balance(1000, 0.4, {})
        self.assertFalse(result["closed"])
        self.assertIsNone(result["net_electric_W"])

    def test_complete_load_accounting(self):
        result = plant_balance(1000, 0.4, dict.fromkeys(PLANT_LOADS, 10))
        self.assertEqual(result["net_electric_W"], 340)
        self.assertTrue(result["closed"])

    def test_negative_and_nonfinite_energy_input(self):
        for rate in [-1, float("nan")]:
            with self.assertRaises(ValueError):
                dt_source(rate, 0.5)
        with self.assertRaises(ValueError):
            plant_balance(100, 0.4, {"magnets_W": -1})


if __name__ == "__main__":
    unittest.main()
