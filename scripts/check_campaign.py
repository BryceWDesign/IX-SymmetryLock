"""Check scientific acceptance and negative controls, not exact float snapshots."""

import json
import sys
from pathlib import Path


def check(bundle):
    result = json.loads((Path(bundle) / "campaign.json").read_text())
    cases = {c["name"]: c for c in result["cases"]}
    for name in ["nominal", "matched_fault_locked", "displaced_fault_locked"]:
        if not cases[name]["local_field_screen_pass"]:
            raise ValueError(f"positive correction control failed: {name}")
    for name in [
        "one_channel_unavailable",
        "current_saturation",
        "twelve_actuator_basis",
        "tight_symmetry_locked",
        "tight_symmetry_unlocked",
    ]:
        if cases[name]["local_field_screen_pass"]:
            raise ValueError(f"negative control unexpectedly passed: {name}")
    if cases["matched_fault_locked"]["validation_after"]["normal_rms_over_B0"] > 1e-6:
        raise ValueError("matched fault not recovered")
    displaced = cases["displaced_fault_locked"]
    ratio = (
        displaced["validation_after"]["normal_rms_over_B0"]
        / displaced["validation_before"]["normal_rms_over_B0"]
    )
    if ratio > 0.25:
        raise ValueError("displaced correction regressed")
    if result["reactor_promotion"]["reactor_promoted"]:
        raise ValueError("invalid reactor promotion")
    if result["symmetry_is_boozer_QA"] or result["hardware_authority"]:
        raise ValueError("invalid authority escalation")
    if abs(result["backbone_negative_control"]["finite_trace_iota"]) > 1e-10:
        raise ValueError("backbone must have zero transform")
    errors = [c["relative_field_l2_error_to_384_segments"] for c in result["polygon_convergence"]]
    if not all(a > b > 0 for a, b in zip(errors, errors[1:], strict=False)):
        raise ValueError("polygon convergence failed")
    refinement = result["surface_grid_refinement"]
    if any(x["rejection_reasons"] for x in refinement):
        raise ValueError("refined independent grid correction failed")
    previous = refinement[-2]["after"]["normal_rms_over_B0"]
    last = refinement[-1]["after"]["normal_rms_over_B0"]
    if abs(last - previous) / last > 0.05:
        raise ValueError("normal-field RMS is not stable within 5% on the last two grids")
    print("Campaign acceptance, rejection, convergence and claim boundaries verified.")


if __name__ == "__main__":
    check(sys.argv[1] if len(sys.argv) > 1 else "results/poc")
