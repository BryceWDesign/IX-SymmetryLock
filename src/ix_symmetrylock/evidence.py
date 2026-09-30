"""File integrity and strict, model-bound promotion receipts."""

import hashlib
import json
from pathlib import Path

REACTOR_GATES = (
    "finite_beta_equilibrium",
    "boozer_quasisymmetry",
    "rotational_transform",
    "magnetic_surface_topology",
    "alpha_confinement",
    "neoclassical_transport",
    "turbulent_transport",
    "mhd_stability",
    "coil_winding_and_structure",
    "quench_and_cryogenics",
    "divertor_and_ash",
    "materials_lifetime",
    "neutronics_and_tritium",
    "fuel_cycle",
    "plant_power_balance",
)


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def file_hash(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write_json(path, value):
    Path(path).write_text(json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n")


def build_manifest(root, paths):
    root = Path(root).resolve()
    entries = {}
    for path in paths:
        p = Path(path).resolve()
        relative = p.relative_to(root).as_posix()
        entries[relative] = file_hash(p)
    return {
        "schema": "ix-symmetrylock.integrity.v1",
        "files": entries,
        "authentication": "UNSIGNED_FILE_INTEGRITY_ONLY",
    }


def verify_manifest(root, manifest):
    root = Path(root).resolve()
    if manifest.get("schema") != "ix-symmetrylock.integrity.v1":
        raise ValueError("unknown manifest schema")
    if not isinstance(manifest.get("files"), dict) or not manifest["files"]:
        raise ValueError("empty manifest")
    for relative, digest in manifest["files"].items():
        p = (root / relative).resolve()
        if not p.is_relative_to(root):
            raise ValueError("manifest path escapes bundle")
        if not p.is_file() or file_hash(p) != digest:
            raise ValueError(f"integrity failure: {relative}")
    return len(manifest["files"])


def promotion_receipt(records):
    """Version 0.1 cannot promote a reactor regardless of imported labels.

    External solver records can be indexed for review, but not blessed by a
    JSON status. Solver verification and cross-code comparison are unimplemented.
    """
    if not isinstance(records, dict):
        raise ValueError("records must be an object")
    return {
        "schema": "ix-symmetrylock.promotion.v1",
        "reactor_promoted": False,
        "reason": "V0_1_HAS_NO_VALIDATED_REACTOR_EVALUATOR",
        "gates": {
            g: {
                "status": "NOT_RUN" if g not in records else "UNVERIFIED_EXTERNAL",
                "record_supplied": g in records,
            }
            for g in REACTOR_GATES
        },
        "fusion_demonstrated": False,
        "net_electricity_demonstrated": False,
    }


def finite_behavior_groups(outcomes):
    """Exact equality on a finite declared battery only; no continuous equivalence."""
    groups = {}
    for name, behavior in outcomes.items():
        key = canonical(behavior)
        groups.setdefault(key, []).append(name)
    return list(groups.values())
