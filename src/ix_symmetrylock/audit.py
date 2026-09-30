"""Recompute fields and gates from archived geometry and proposed currents."""

import json
from pathlib import Path

import numpy as np

from .control import Limits, gate
from .evidence import file_hash, verify_manifest
from .field import basis, toroidal_backbone
from .geometry import Coil, Surface
from .metrics import evaluate


def audit(bundle):
    root = Path(bundle)
    verify_manifest(root, json.loads((root / "manifest.json").read_text()))
    sources = json.loads((root / "source_hashes.json").read_text())
    source_root = Path(__file__).parent
    for name, digest in sources.items():
        path = (source_root / name).resolve()
        if not path.is_relative_to(source_root.resolve()) or file_hash(path) != digest:
            raise ValueError(f"executed package identity differs: {name}")
    result = json.loads((root / "campaign.json").read_text())
    config = result["config"]
    if result["authority"] != "VACUUM_FIELD_CORRECTION_SCREEN":
        raise ValueError("unsupported campaign authority")
    if (
        result["hardware_authority"]
        or result["symmetry_is_boozer_QA"]
        or result["reactor_promotion"]["reactor_promoted"]
    ):
        raise ValueError("invalid authority escalation")
    with np.load(root / "geometry.npz", allow_pickle=False) as archive:
        coils = [
            Coil(str(name), v)
            for name, v in zip(archive["names"], archive["vertices_m"], strict=True)
        ]
        displaced = [
            Coil(f"fault_{k}", v) for k, v in enumerate(archive["displaced_fault_vertices_m"])
        ]
        count = 0
        for prefix, before_key, after_key in [
            ("training", "before", "after"),
            ("validation", "validation_before", "validation_after"),
        ]:
            shape = tuple(
                config["training_grid"] if prefix == "training" else config["validation_grid"]
            )
            surface = Surface(archive[f"{prefix}_points_m"], archive[f"{prefix}_normals"], shape)
            response = basis(coils, surface.points)
            b0 = config["axis_backbone_T"]
            backbone = toroidal_backbone(surface.points, config["major_radius_m"], b0)
            faults = {
                "none": np.zeros_like(backbone),
                "matched": np.einsum("pik,k->pi", response, archive["matched_fault_amp_turn"]),
                "displaced": np.einsum(
                    "pik,k->pi",
                    basis(displaced, surface.points),
                    archive["displaced_fault_amp_turn"],
                ),
            }
            for case in result["cases"]:
                command = np.asarray(case["proposal"]["currents_amp_turn"])
                indices = case["actuator_indices"]
                bg = backbone + faults[case["fault_model"]]
                after_field = bg + np.einsum("pik,k->pi", response[:, :, indices], command)
                before = evaluate(bg, surface, b0)
                after = evaluate(after_field, surface, b0)
                expected_before = (
                    case["proposal"][before_key] if prefix == "training" else case[before_key]
                )
                expected_after = (
                    case["proposal"][after_key] if prefix == "training" else case[after_key]
                )
                for key in before:
                    if not np.isclose(before[key], expected_before[key], rtol=1e-7, atol=1e-13):
                        raise ValueError(f"initial metric mismatch: {case['name']}/{prefix}/{key}")
                    if not np.isclose(after[key], expected_after[key], rtol=1e-7, atol=1e-13):
                        raise ValueError(f"final metric mismatch: {case['name']}/{prefix}/{key}")
                reasons = gate(
                    before,
                    after,
                    command,
                    Limits(**case["limits"]),
                    case["proposal"]["solver_success"],
                )
                expected = (
                    case["proposal"]["rejection_reasons"]
                    if prefix == "training"
                    else case["validation_rejection_reasons"]
                )
                if reasons != expected:
                    raise ValueError(f"rejection mismatch: {case['name']}/{prefix}")
                if prefix == "training" and case["proposal"]["accepted"] != (not reasons):
                    raise ValueError(f"acceptance mismatch: {case['name']}/{prefix}")
                if prefix == "validation":
                    accepted = case["proposal"]["accepted"] and not reasons
                    if case["local_field_screen_pass"] != accepted:
                        raise ValueError(f"acceptance mismatch: {case['name']}/{prefix}")
                count += 1
    return {
        "recomputed_case_grids": count,
        "source_hashes_matched": len(sources),
        "authority": "VACUUM_FIELD_RECOMPUTATION_ONLY",
        "experimental_validation": False,
        "authenticated_identity": False,
    }
