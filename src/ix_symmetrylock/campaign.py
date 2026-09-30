"""Reproducible explicit-coil challenge, ablations, and uncertainty screen."""

import csv
import importlib.metadata
import json
import platform
from dataclasses import asdict, replace
from pathlib import Path

import numpy as np

from .control import Limits, correct, gate
from .evidence import build_manifest, finite_behavior_groups, promotion_receipt, write_json
from .field import basis, biot_savart, toroidal_backbone
from .geometry import Coil, torus, trim_array
from .inverse import controllability, d_optimal_next
from .metrics import evaluate, strength_jacobian
from .tracing import trace


def plain(value):
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, np.generic):
        return value.item()
    if isinstance(value, dict):
        return {k: plain(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [plain(v) for v in value]
    return value


def load_config(path):
    c = json.loads(Path(path).read_text())
    required = {
        "schema",
        "major_radius_m",
        "evaluation_minor_radius_m",
        "winding_minor_radius_m",
        "trim_radius_m",
        "toroidal_stations",
        "poloidal_stations",
        "coil_segments",
        "axis_backbone_T",
        "training_grid",
        "validation_grid",
        "validation_offset",
        "current_limit_amp_turn",
        "symmetry_rms_limit",
        "normal_rms_limit",
        "minimum_normal_reduction",
        "ridge",
        "max_iterations",
        "uncertainty_seed",
        "uncertainty_samples",
        "coil_position_sigma_m",
        "current_relative_sigma",
        "declared_authority",
        "symmetry_coordinates",
    }
    if set(c) != required or c["schema"] != "ix-symmetrylock.poc.v1":
        raise ValueError("unknown config schema or missing/extra keys")
    for key in required - {
        "schema",
        "declared_authority",
        "symmetry_coordinates",
        "training_grid",
        "validation_grid",
    }:
        if not isinstance(c[key], (int, float)) or not np.isfinite(c[key]):
            raise ValueError(f"invalid numeric config: {key}")
    if c["toroidal_stations"] != 8 or c["poloidal_stations"] != 3:
        raise ValueError("this declared campaign requires an 8 by 3 actuator layout")
    if not 0 < c["evaluation_minor_radius_m"] < c["winding_minor_radius_m"]:
        raise ValueError("winding surface must be outside evaluation surface")
    if c["winding_minor_radius_m"] + c["trim_radius_m"] >= c["major_radius_m"]:
        raise ValueError("coil array intersects cylindrical axis")
    for key in ["coil_segments", "max_iterations", "uncertainty_seed", "uncertainty_samples"]:
        if not isinstance(c[key], int) or c[key] < (8 if key == "coil_segments" else 1):
            raise ValueError(f"invalid integer config: {key}")
    for key in ["training_grid", "validation_grid"]:
        if (
            not isinstance(c[key], list)
            or len(c[key]) != 2
            or any(not isinstance(x, int) or x < 4 for x in c[key])
        ):
            raise ValueError("invalid grid")
    if min(c["coil_position_sigma_m"], c["current_relative_sigma"]) < 0:
        raise ValueError("negative uncertainty")
    if c["axis_backbone_T"] <= 0 or c["trim_radius_m"] <= 0:
        raise ValueError("invalid field or loop radius")
    if c["declared_authority"] != "VACUUM_FIELD_CORRECTION_SCREEN":
        raise ValueError("unsupported authority")
    if c["symmetry_coordinates"] != "FIXED_GEOMETRIC_ANGLES_NOT_BOOZER":
        raise ValueError("campaign does not use Boozer coordinates")
    return c


def run(config_path, output):
    c = load_config(config_path)
    out = Path(output)
    out.mkdir(parents=True, exist_ok=True)
    r0 = c["major_radius_m"]
    b0 = c["axis_backbone_T"]
    coils = trim_array(
        r0,
        c["winding_minor_radius_m"],
        c["trim_radius_m"],
        c["toroidal_stations"],
        c["poloidal_stations"],
        c["coil_segments"],
    )
    train = torus(r0, c["evaluation_minor_radius_m"], *c["training_grid"])
    validation = torus(
        r0, c["evaluation_minor_radius_m"], *c["validation_grid"], offset=c["validation_offset"]
    )
    a = basis(coils, train.points)
    av = basis(coils, validation.points)
    backbone = toroidal_backbone(train.points, r0, b0)
    backbone_v = toroidal_backbone(validation.points, r0, b0)
    fault_currents = np.zeros(len(coils))
    fault_currents[0], fault_currents[10] = 55.0, -35.0
    displaced = [
        Coil(coils[i].name + "_displaced", coils[i].vertices + np.array([0.004, -0.003, 0.002]))
        for i in [0, 10]
    ]
    fault = np.einsum("pik,k->pi", a, fault_currents)
    fault_v = np.einsum("pik,k->pi", av, fault_currents)
    fd = sum(
        current * biot_savart(coil, train.points)
        for current, coil in zip([55, -35], displaced, strict=True)
    )
    fdv = sum(
        current * biot_savart(coil, validation.points)
        for current, coil in zip([55, -35], displaced, strict=True)
    )
    limits = Limits(
        c["current_limit_amp_turn"],
        c["symmetry_rms_limit"],
        c["normal_rms_limit"],
        c["minimum_normal_reduction"],
        c["ridge"],
        c["max_iterations"],
    )
    every = np.arange(len(coils))
    twelve = np.array([i for i in every if i // 3 % 2 == 0])
    # Identical fault, grids, solver and iteration budget in each paired ablation.
    specs = [
        ("nominal", np.zeros_like(fault), np.zeros_like(fault_v), every, limits, True),
        ("matched_fault_locked", fault, fault_v, every, limits, True),
        ("displaced_fault_locked", fd, fdv, every, limits, True),
        ("displaced_fault_unlocked", fd, fdv, every, limits, False),
        ("one_channel_unavailable", fault, fault_v, every[1:], limits, True),
        ("current_saturation", fault, fault_v, every, replace(limits, current_amp_turn=5.0), True),
        ("twelve_actuator_basis", fd, fdv, twelve, limits, True),
        ("tight_symmetry_locked", fd, fdv, every, replace(limits, symmetry_rms=1e-6), True),
        ("tight_symmetry_unlocked", fd, fdv, every, replace(limits, symmetry_rms=1e-6), False),
    ]
    cases = []
    for name, f, fv, indices, case_limits, locked in specs:
        bg, bgv = backbone + f, backbone_v + fv
        proposal = correct(a[:, :, indices], bg, train, b0, case_limits, locked)
        command = proposal["currents_amp_turn"]
        before_v = evaluate(bgv, validation, b0)
        after_field_v = bgv + np.einsum("pik,k->pi", av[:, :, indices], command)
        after_v = evaluate(after_field_v, validation, b0)
        heldout_reasons = gate(before_v, after_v, command, case_limits, proposal["solver_success"])
        j = np.einsum("pik,pi->pk", a[:, :, indices], train.normals) / b0
        residual = np.einsum("pi,pi->p", bg, train.normals) / b0
        ctrl = controllability(j, residual)
        lock_j = strength_jacobian(bg, a[:, :, indices], train.shape, b0)
        exact_local_lock = controllability(j, residual, lock_j)
        cases.append(
            {
                "name": name,
                "fault_model": (
                    "none"
                    if name == "nominal"
                    else "displaced"
                    if name
                    in {
                        "displaced_fault_locked",
                        "displaced_fault_unlocked",
                        "twelve_actuator_basis",
                        "tight_symmetry_locked",
                        "tight_symmetry_unlocked",
                    }
                    else "matched"
                ),
                "limits": asdict(case_limits),
                "actuator_indices": indices,
                "proposal": proposal,
                "validation_before": before_v,
                "validation_after": after_v,
                "validation_rejection_reasons": heldout_reasons,
                "local_field_screen_pass": proposal["accepted"] and not heldout_reasons,
                "linear_controllability": ctrl,
                "exact_first_order_geometric_lock": exact_local_lock,
            }
        )

    # Robustness: commanded currents stay fixed, model paths and command gains
    # vary. This is prediction under assumed uncertainty, not experimental data.
    rng = np.random.default_rng(c["uncertainty_seed"])
    command = cases[2]["proposal"]["currents_amp_turn"]
    surface_refinement = []
    for nphi, ntheta in [(49, 25), (97, 49), (145, 73)]:
        refined = torus(r0, c["evaluation_minor_radius_m"], nphi, ntheta, offset=0.5)
        refined_response = basis(coils, refined.points)
        refined_fault = sum(
            current * biot_savart(coil, refined.points)
            for current, coil in zip([55, -35], displaced, strict=True)
        )
        refined_bg = toroidal_backbone(refined.points, r0, b0) + refined_fault
        refined_after = refined_bg + np.einsum("pik,k->pi", refined_response, command)
        initial_metrics = evaluate(refined_bg, refined, b0)
        final_metrics = evaluate(refined_after, refined, b0)
        surface_refinement.append(
            {
                "grid": [nphi, ntheta],
                "offset": 0.5,
                "case": "displaced_fault_locked",
                "before": initial_metrics,
                "after": final_metrics,
                "rejection_reasons": gate(initial_metrics, final_metrics, command, limits),
            }
        )
    uncertainty = []
    for i in range(c["uncertainty_samples"]):
        perturbed = [
            Coil(coil.name, coil.vertices + rng.normal(0, c["coil_position_sigma_m"], 3))
            for coil in coils
        ]
        actual_current = command * (1 + rng.normal(0, c["current_relative_sigma"], len(command)))
        actual_field = (
            backbone_v
            + fdv
            + np.einsum("pik,k->pi", basis(perturbed, validation.points), actual_current)
        )
        metrics = evaluate(actual_field, validation, b0)
        reasons = gate(cases[2]["validation_before"], metrics, actual_current, limits)
        uncertainty.append({"sample": i, "metrics": metrics, "rejection_reasons": reasons})

    jv = np.einsum("pik,pi->pk", av, validation.normals) / b0
    prior = np.eye(len(coils)) * 1e-6
    ranked, gains = d_optimal_next(jv, prior, np.full(len(jv), 0.0001))
    reference = trace(
        lambda p: toroidal_backbone(p, r0, b0),
        r0,
        [r0 + 0.06, 0.0],
        turns=8,
        wall_minor=c["evaluation_minor_radius_m"],
    )
    del reference["trajectory_rz_m"]
    reference["meaning"] = "zero-transform negative control, NOT a fusion candidate"

    # Polygon approximation convergence is independent of correction fitting.
    convergence = []
    source = coils[0]
    high = trim_array(r0, c["winding_minor_radius_m"], c["trim_radius_m"], 8, 3, 384)[0]
    high_field = biot_savart(high, validation.points)
    for segments in [24, 48, 96, 192]:
        candidate = trim_array(r0, c["winding_minor_radius_m"], c["trim_radius_m"], 8, 3, segments)[
            0
        ]
        error = np.linalg.norm(biot_savart(candidate, validation.points) - high_field)
        convergence.append(
            {
                "segments": segments,
                "relative_field_l2_error_to_384_segments": float(
                    error / np.linalg.norm(high_field)
                ),
            }
        )
    archive = {
        "names": np.array([coil.name for coil in coils]),
        "vertices_m": np.stack([coil.vertices for coil in coils]),
        "training_points_m": train.points,
        "training_normals": train.normals,
        "validation_points_m": validation.points,
        "validation_normals": validation.normals,
        "matched_fault_amp_turn": fault_currents,
        "displaced_fault_vertices_m": np.stack([coil.vertices for coil in displaced]),
        "displaced_fault_amp_turn": np.array([55.0, -35.0]),
    }
    np.savez_compressed(out / "geometry.npz", **archive)
    with (out / "currents.csv").open("w", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["case", "coil", "proposed_amp_turn", "screen_pass", "hardware_authority"])
        for case in cases:
            for index, current in zip(
                case["actuator_indices"], case["proposal"]["currents_amp_turn"], strict=True
            ):
                writer.writerow(
                    [
                        case["name"],
                        coils[index].name,
                        f"{current:.12g}",
                        case["local_field_screen_pass"],
                        False,
                    ]
                )
    result = plain(
        {
            "schema": "ix-symmetrylock.campaign.v1",
            "config": c,
            "authority": "VACUUM_FIELD_CORRECTION_SCREEN",
            "symmetry_is_boozer_QA": False,
            "primary_magnet_model": "IDEAL_ANALYTIC_TOROIDAL_BACKBONE",
            "hardware_authority": False,
            "cases": cases,
            "uncertainty": {
                "assumptions": "independent Gaussian path translations and gain errors",
                "samples": uncertainty,
                "passed": sum(not u["rejection_reasons"] for u in uncertainty),
            },
            "active_identification_advisor": {
                "top_five_validation_point_indices": ranked[:5],
                "top_five_logdet_gains": gains[ranked[:5]],
                "prior_information_diagonal": 1e-6,
                "assumed_normal_measurement_noise_over_B0": 0.0001,
                "measurement_executed": False,
            },
            "backbone_negative_control": reference,
            "polygon_convergence": convergence,
            "surface_grid_refinement": surface_refinement,
            "total_trim_centerline_length_m": sum(coil.length_m for coil in coils),
            "single_trim_centerline_length_m": source.length_m,
            "finite_behavior_groups": finite_behavior_groups(
                {
                    case["name"]: [
                        case["local_field_screen_pass"],
                        case["proposal"]["rejection_reasons"],
                        case["validation_rejection_reasons"],
                    ]
                    for case in cases
                }
            ),
            "reactor_promotion": promotion_receipt({}),
            "runtime": {
                "python": platform.python_version(),
                "numpy": importlib.metadata.version("numpy"),
                "scipy": importlib.metadata.version("scipy"),
            },
        }
    )
    write_json(out / "campaign.json", result)
    write_json(out / "config.json", c)
    package_root = Path(__file__).parent
    sources = sorted(package_root.glob("*.py"))
    write_json(
        out / "source_hashes.json",
        {p.name: __import__("hashlib").sha256(p.read_bytes()).hexdigest() for p in sources},
    )
    files = [
        out / name
        for name in [
            "geometry.npz",
            "currents.csv",
            "campaign.json",
            "config.json",
            "source_hashes.json",
        ]
    ]
    write_json(out / "manifest.json", build_manifest(out, files))
    return result
