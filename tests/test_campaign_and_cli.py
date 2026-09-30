import contextlib
import io
import json
import shutil
import tempfile
import unittest
from pathlib import Path

import numpy as np

from ix_symmetrylock.audit import audit
from ix_symmetrylock.campaign import load_config, run
from ix_symmetrylock.cli import main
from ix_symmetrylock.evidence import file_hash

ROOT = Path(__file__).resolve().parents[1]


class CampaignTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temporary = tempfile.TemporaryDirectory()
        cls.bundle = Path(cls.temporary.name) / "evidence"
        config = json.loads((ROOT / "configs/poc.json").read_text())
        config["uncertainty_samples"] = 1
        config_path = Path(cls.temporary.name) / "config.json"
        config_path.write_text(json.dumps(config))
        cls.result = run(config_path, cls.bundle)
        cls.cases = {c["name"]: c for c in cls.result["cases"]}

    @classmethod
    def tearDownClass(cls):
        cls.temporary.cleanup()

    def test_displaced_fault_improves_independent_grid(self):
        c = self.cases["displaced_fault_locked"]
        self.assertTrue(c["local_field_screen_pass"])
        self.assertLess(
            c["validation_after"]["normal_rms_over_B0"],
            c["validation_before"]["normal_rms_over_B0"] * 0.25,
        )

    def test_missing_channel_and_saturation_reject(self):
        for name in ["one_channel_unavailable", "current_saturation", "twelve_actuator_basis"]:
            self.assertFalse(self.cases[name]["local_field_screen_pass"])

    def test_tight_lock_does_not_silently_promote(self):
        for name in ["tight_symmetry_locked", "tight_symmetry_unlocked"]:
            self.assertFalse(self.cases[name]["local_field_screen_pass"])
        self.assertFalse(self.result["reactor_promotion"]["reactor_promoted"])

    def test_csv_only_commands_available_channels(self):
        case = self.cases["one_channel_unavailable"]
        self.assertNotIn(0, case["actuator_indices"])
        self.assertEqual(len(case["proposal"]["currents_amp_turn"]), 23)
        self.assertTrue((self.bundle / "currents.csv").is_file())

    def test_recompute_archived_fields_and_gates(self):
        result = audit(self.bundle)
        self.assertEqual(result["recomputed_case_grids"], 18)
        self.assertFalse(result["experimental_validation"])

    def test_recomputation_detects_forged_metric_even_with_updated_hash(self):
        with tempfile.TemporaryDirectory() as directory:
            copied = Path(directory) / "bundle"
            shutil.copytree(self.bundle, copied)
            path = copied / "campaign.json"
            result = json.loads(path.read_text())
            result["cases"][2]["validation_after"]["normal_rms_over_B0"] = 0.01
            path.write_text(json.dumps(result))
            manifest_path = copied / "manifest.json"
            manifest = json.loads(manifest_path.read_text())
            manifest["files"]["campaign.json"] = file_hash(path)
            manifest_path.write_text(json.dumps(manifest))
            with self.assertRaisesRegex(ValueError, "final metric mismatch"):
                audit(copied)

    def test_geometry_archive_contains_actual_paths_and_independent_samples(self):
        with np.load(self.bundle / "geometry.npz", allow_pickle=False) as a:
            self.assertEqual(a["vertices_m"].shape, (24, 96, 3))
            self.assertEqual(len(a["training_points_m"]), 288)
            self.assertEqual(len(a["validation_points_m"]), 703)

    def test_cli_verifies_bundle_and_detects_tampering(self):
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(main(["verify", str(self.bundle)]), 0)
        path = self.bundle / "config.json"
        original = path.read_bytes()
        try:
            path.write_bytes(original + b" ")
            with contextlib.redirect_stderr(io.StringIO()):
                self.assertEqual(main(["verify", str(self.bundle)]), 2)
        finally:
            path.write_bytes(original)

    def test_unknown_and_malformed_config_rejected(self):
        c = json.loads((ROOT / "configs/poc.json").read_text())
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "bad.json"
            for changes in [
                {"pretend_equilibrium_pass": True},
                {"coil_segments": 0},
                {"axis_backbone_T": float("nan")},
                {"training_grid": [1, 2]},
                {"symmetry_coordinates": "BOOZER"},
            ]:
                path.write_text(json.dumps(c | changes))
                with self.assertRaises(ValueError):
                    load_config(path)


if __name__ == "__main__":
    unittest.main()
