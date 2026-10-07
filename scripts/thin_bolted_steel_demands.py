"""Consume one compatible thin-frame state without repeating frozen method runs."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PACKET = ROOT / "docs/wood-joints-mvp/hypotheses/hl35-candidate/thin-frame-comparison"
METHODS = PACKET / "steel-resistance-methods-v4.json"
METHODS_SHA256 = "d00ff10eb875c0d093f6c0e811a7b1e2ef850f6d3ec846b6b910eb2c4cdabf19"
GENERALIZED_RESIDUAL_CAP_N = 1e-5
BODY_GLOBAL_FORCE_CAP_N = 1e-4
BODY_GLOBAL_MOMENT_CAP_NMM = .1


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validate_demand_state(demand: dict) -> dict:
    """Require one converged producer state; numerical validity is not acceptance."""
    if demand.get("schema") != "thin_bolted_compatible_elastic_frame/v1":
        raise ValueError("only a compatible elastic state is admissible")
    response = demand.get("response", {})
    if response.get("converged") is not True:
        raise ValueError("unconverged demand field")
    if response.get("physical_residual_uses_unmodified_laws") is not True:
        raise ValueError("unmodified physical-law residual is required")
    residual = response.get("gradient_inf_n")
    tolerance = response.get("generalized_residual_tolerance_n")
    if not isinstance(tolerance, (int, float)) or not math.isfinite(tolerance) or not 0 < tolerance <= GENERALIZED_RESIDUAL_CAP_N:
        raise ValueError("missing or excessive generalized residual criterion")
    if not isinstance(residual, (int, float)) or not math.isfinite(residual) or not 0 <= residual <= tolerance:
        raise ValueError("demand residual does not meet the bounded producer criterion")
    closure = validate_stored_equilibrium(demand)
    identity = {key: demand.get(key) for key in
                ("case_id", "accessory_placement", "parameters", "geometry_cache_sha256")}
    if any(value is None for value in identity.values()) or not isinstance(identity["parameters"], dict):
        raise ValueError("missing complete state identity")
    expected = "thin-v4-" + hashlib.sha256(json.dumps(identity, sort_keys=True,
                                                       separators=(",", ":")).encode()).hexdigest()[:24]
    if demand.get("state_id") != expected:
        raise ValueError("state identity does not bind the declared parameters")
    attachments = demand.get("attachment_actions")
    contacts = demand.get("flange_contact_actions")
    if not isinstance(attachments, list) or len(attachments) != 72 or not isinstance(contacts, list) or len(contacts) != 288:
        raise ValueError("complete 72-port attachment and 288-corner flange contact tables are required")
    used = set()
    contact_ids = set()
    for table, rows in (("attachment", attachments), ("contact", contacts)):
        for row in rows:
            if any(row.get(key) != identity[key] for key in ("case_id", "accessory_placement")) or row.get("state_id") != expected:
                raise ValueError("action belongs to another parameter/accessory state")
            if table == "attachment":
                port = (row.get("axis_id"), row.get("angle_id"), row.get("flange"))
                if None in port or port in used:
                    raise ValueError("missing or duplicate attachment identity")
                used.add(port)
            else:
                if row.get("kind") != "flange_contact" or not row.get("id") or row["id"] in contact_ids:
                    raise ValueError("missing, duplicate or nonflange contact identity")
                if any(not row.get(key) for key in ("angle_id", "flange", "receiver")):
                    raise ValueError("missing contact angle/flange/receiver identity")
                contact_ids.add(row["id"])
            for key in ("point_xyz_mm", "force_on_receiver_xyz_n", "moment_on_receiver_at_point_xyz_nmm"):
                values = row.get(key)
                if not isinstance(values, list) or len(values) != 3 or any(
                        not isinstance(value, (int, float)) or not math.isfinite(value) for value in values):
                    raise ValueError("nonfinite or missing action vector")
    return identity | {"state_id": expected, "physical_law_gradient_inf_n": residual,
                       "generalized_residual_tolerance_n": tolerance, "stored_equilibrium": closure,
                       "attachment_count": len(attachments), "flange_contact_count": len(contacts)}


def vector3(value) -> list:
    if not isinstance(value, list) or len(value) != 3 or any(
            not isinstance(v, (int, float)) or not math.isfinite(v) for v in value):
        raise ValueError("missing or nonfinite equilibrium vector")
    return value


def validate_stored_equilibrium(demand: dict) -> dict:
    """Recheck every supplied closure vector under fixed, documented upper caps."""
    criterion = demand.get("equilibrium_verification", {})
    force_tol, moment_tol = criterion.get("force_tolerance_n"), criterion.get("moment_tolerance_nmm")
    for value, cap in ((force_tol, BODY_GLOBAL_FORCE_CAP_N), (moment_tol, BODY_GLOBAL_MOMENT_CAP_NMM)):
        if not isinstance(value, (int, float)) or not math.isfinite(value) or not 0 < value <= cap:
            raise ValueError("missing or excessive physical wrench closure criterion")
    rows = demand.get("body_equilibrium_residuals")
    if not isinstance(rows, list) or len(rows) != 62 or len({r.get("body") for r in rows}) != 62:
        raise ValueError("all 62 unique body residuals are required")
    force_max = max(math.sqrt(sum(v * v for v in vector3(r.get("force_xyz_n")))) for r in rows)
    moment_max = max(math.sqrt(sum(v * v for v in vector3(r.get("moment_about_reference_xyz_nmm")))) for r in rows)
    global_force = math.sqrt(sum(v * v for v in vector3(demand.get("global_equilibrium_residual_force_n"))))
    global_moment = math.sqrt(sum(v * v for v in vector3(demand.get("global_equilibrium_residual_moment_nmm"))))
    if force_max > force_tol or global_force > force_tol or moment_max > moment_tol or global_moment > moment_tol:
        raise ValueError("body or global physical wrench closure failed")
    if demand.get("usable_conditional_actions") is not True or criterion.get("all_body_and_global_checks_pass") is not True:
        raise ValueError("producer did not issue usable conditional actions")
    return {"body_count": 62, "maximum_body_force_norm_n": force_max,
            "maximum_body_moment_about_reference_norm_nmm": moment_max,
            "global_force_norm_n": global_force, "global_moment_norm_nmm": global_moment,
            "force_tolerance_n": force_tol, "moment_tolerance_nmm": moment_tol}


def small_washer_axial_references(methods: dict, demand: dict, layout: dict) -> list[dict]:
    """Reuse frozen unit coefficients for the single-shaft axial component only."""
    axes = {row["id"]: row for row in layout["installed_axes"]}
    actions = {row["axis_id"]: row for row in demand["attachment_actions"]
               if len(axes[row["axis_id"]]["attachments"]) == 1}
    result = []
    for washer in methods["washer_reference_inputs"]:
        if not washer["small_washer_product"]:
            continue
        axis_id = washer["axis_id"]
        if len(axes[axis_id]["attachments"]) != 1 or axis_id not in actions:
            raise ValueError("small washer requires one authenticated physical-shaft attachment")
        axis = vector3(axes[axis_id]["attachments"][0]["axis_xyz"])
        length = math.sqrt(sum(v * v for v in axis))
        inward_force = sum(f * a / length for f, a in zip(vector3(actions[axis_id]["force_on_receiver_xyz_n"]), axis, strict=True))
        opening_restraint = max(-inward_force, 0.)
        closing = max(inward_force, 0.)
        magnitude = abs(inward_force)
        sensitivities = []
        for profile_id in washer["bearing_circle_sensitivity_profile_ids"]:
            profile = methods["washer_bending_profiles"][profile_id]
            unit = profile["unit_axial_two_face_bending"]
            if unit["axial_n"] != 1.:
                raise ValueError("frozen washer response must be a one-newton unit coefficient")
            coefficient = unit["required_fy_mpa_at_sampled_bending_first_yield"]
            sensitivities.append({"frozen_profile_id": profile_id,
                                  "assumed_circular_bearing_diameter_mm": profile["assumed_circular_bearing_diameter_mm"],
                                  "required_fy_mpa_opening_component_reference": opening_restraint * coefficient,
                                  "required_fy_mpa_absolute_projection_diagnostic": magnitude * coefficient,
                                  "actual_bearing_circle_verified": False})
        wood = washer["nominal_wood_annulus_reference"]
        result.append({"state_id": demand["state_id"], "axis_id": axis_id, "role": washer["role"],
                       "support_material": washer["support_material"],
                       "signed_force_on_receiver_along_flange_inward_axis_n": inward_force,
                       "opening_restraint_component_n": opening_restraint,
                       "closing_component_n": closing, "absolute_axial_projection_diagnostic_n": magnitude,
                       "absolute_projection_inferred_as_physical_bolt_tension": False,
                       "closing_shaft_force_capture_or_bilateral_spring_artifact_unresolved": closing > 1e-7,
                       "reused_frozen_plate_sensitivities": sensitivities,
                       "nominal_wood_full_annulus_opening_component_reference_index": opening_restraint / (wood["wood_bearing_reference_lbf"] * 4.4482216152605)
                       if wood else None,
                       "nominal_wood_full_annulus_absolute_projection_diagnostic_index": magnitude / (wood["wood_bearing_reference_lbf"] * 4.4482216152605)
                       if wood else None,
                       "own_end_moments_available": False, "unknown_own_end_moments_zero_filled": False,
                       "combined_axial_and_moment_washer_index": None,
                       "actual_contact_or_material_capacity_verified": False, "complete_joint_acceptance": False})
    return result


def consume(demand_path: Path) -> dict:
    """Bind issued coefficients and compare only the newly supplied flange field."""
    if sha(METHODS) != METHODS_SHA256:
        raise ValueError("issued method evidence changed")
    methods = json.loads(METHODS.read_text())
    for relative, expected in methods["source_sha256"].items():
        if sha(ROOT / relative) != expected:
            raise ValueError(f"issued method dependency changed: {relative}")
    demand = json.loads(demand_path.read_text())
    identity = validate_demand_state(demand)
    from scripts.thin_bolted_steel_resistance import (
        LAYOUT,
        LAYOUT_SHA,
        compare_flange_actions,
    )

    if demand.get("candidate") != methods["candidate"] or demand.get("source_sha256", {}).get(
            str(LAYOUT.relative_to(ROOT))) != LAYOUT_SHA:
        raise ValueError("demand source does not authenticate the frozen thin candidate")
    for required in ("scripts/thin_bolted_frame_mechanics.py", "scripts/thin_bolted_panel_mechanics.py",
                     "scripts/thin_bolted_steel_resistance.py"):
        if required not in demand["source_sha256"]:
            raise ValueError(f"missing compatible producer binding: {required}")
    for relative, expected in demand["source_sha256"].items():
        if sha(ROOT / relative) != expected:
            raise ValueError(f"compatible producer dependency changed: {relative}")
    audit_path = ROOT / "scripts/thin_bolted_equilibrium_audit.py"
    audit_sha = sha(audit_path)
    from scripts.thin_bolted_equilibrium_audit import audit_state

    independent_audit = audit_state(demand)
    if independent_audit.get("independent_equilibrium_and_contact_checks_pass") is not True:
        raise ValueError("independent source/body/global/contact audit failed")
    if sha(audit_path) != audit_sha:
        raise ValueError("independent audit helper changed during consumption")
    comparison = compare_flange_actions(demand["attachment_actions"], demand["flange_contact_actions"])
    if len(comparison["cases"]) != 1 or comparison["cases"][0]["missing_flange_actions"]:
        raise ValueError("candidate flange comparison is incomplete")
    washer_components = small_washer_axial_references(methods, demand, json.loads(LAYOUT.read_text()))
    return {"schema": "thin_bolted_fresh_steel_demands/v1", "candidate": methods["candidate"],
            "status": "CONDITIONAL_FRESH_FLANGE_COMPONENT_COMPARISON", "state": identity,
            "source_sha256": {str(METHODS.relative_to(ROOT)): METHODS_SHA256,
                              str(demand_path.resolve().relative_to(ROOT)): sha(demand_path),
                              str(Path(__file__).relative_to(ROOT)): sha(Path(__file__)),
                              str(audit_path.relative_to(ROOT)): audit_sha},
            "demand_producer_source_sha256": demand["source_sha256"],
            "frozen_method_source_sha256": methods["source_sha256"],
            "independent_equilibrium_and_contact_audit": independent_audit,
            "fresh_demand_comparison": comparison,
            "small_washer_same_state_axial_component_references": washer_components,
            "unchanged_unit_responses_recomputed": False,
            "prior_demand_or_pass_transferred": False,
            "nominal_catalog_fy_mpa_scenario": methods["material_and_product_gates"]["catalog_fy_mpa_scenario"],
            "limits": ["Same-state point translation/contact actions are a conditional compatible surrogate.",
                       "Nominal sampled strip yield and required Fu are component diagnostics, not authenticated fitting capacities.",
                       "Actual heel/hole geometry, shared-shaft bending, washer own-end moments/contact and hardware properties remain unresolved.",
                       "The physical residual check does not prove unique force allocation, refinement or complete failure-mode coverage."],
            "release": methods["release"], "complete_joint_acceptance": False,
            "fabrication_release": False, "climbing_release": False}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--demands", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    if args.out.exists():
        raise FileExistsError("preserve issued fresh component evidence")
    report = consume(args.demands)
    args.out.write_text(json.dumps(report, indent=2, allow_nan=False) + "\n")
    print(json.dumps({"output": str(args.out), "state_id": report["state"]["state_id"],
                      "case": report["fresh_demand_comparison"]["cases"][0]}, indent=2))


if __name__ == "__main__":
    main()
