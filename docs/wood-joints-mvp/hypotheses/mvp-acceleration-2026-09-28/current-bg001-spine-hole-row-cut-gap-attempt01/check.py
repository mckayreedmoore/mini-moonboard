#!/usr/bin/env python3
"""Reproduce the pinned one-sided cut-force ambiguity for the BG001 spine row."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[5]
BASE = Path("docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28")
SOURCES = {
    "corner_demand_report": (
        BASE / "current-corner-native-demand-export-attempt03/corner-demand-report.json",
        "812a62fa3cd96a8983649c84a8c78a8d176d639465c887b11d1827a3f8f1ee17",
    ),
    "source_model": (
        BASE / "current-springa-selected-floor-a12-rear-attempt03/model.json",
        "8a90452d8afa1f1722b3253b18d5aeec72c432033a22d5d0828082022cc1cda8",
    ),
    "section_geometry": (
        BASE / "current-corner-local-wood-screen-attempt01/section-screen.json",
        "22209a82b0bda6dfc5c140ccc4e481717e0e7c71d30a5827271c81ac71070564",
    ),
}
MEMBER = "knee_outer_left_spine"
AXIS = "knee_outer_left_post_1"
LATERAL_ROW = f"{AXIS}/plane-35"
SECTION_TOL_MM = 1e-8


def read_pinned(name: str) -> dict:
    rel, expected = SOURCES[name]
    path = ROOT / rel
    raw = path.read_bytes()
    actual = hashlib.sha256(raw).hexdigest()
    if actual != expected:
        raise SystemExit(f"{name} SHA-256 mismatch: {actual}")
    return json.loads(raw)


def member_action(row: dict) -> tuple[list[float], list[float]] | None:
    if row["first"] == MEMBER:
        return row["first_point_global_xyz_mm"], row["force_on_first_xyz_n"]
    if row["second"] == MEMBER:
        return row["second_point_global_xyz_mm"], row["force_on_second_xyz_n"]
    return None


def main() -> None:
    report = read_pinned("corner_demand_report")
    model = read_pinned("source_model")
    section_screen = read_pinned("section_geometry")

    if report.get("status") != "PASS_NUMERICAL_CORNER_DEMAND_REPORT_ONLY":
        raise SystemExit("source demand report status changed")
    source_case = report["authenticated_source_case"]
    if source_case.get("case_id") != "a12-rear":
        raise SystemExit("source case changed")
    if source_case.get("input_model_json_sha256") != SOURCES["source_model"][1]:
        raise SystemExit("report is not bound to the pinned source model")
    if report.get("actual_case_demand_usable_for_conditional_joint_checks") is not True:
        raise SystemExit("source report no longer marks this case usable for conditional checks")
    if report.get("qualification_boundary", {}).get("complete_joint_accepted") is not False:
        raise SystemExit("qualification boundary changed")

    increment = next(
        row for row in report["increments"]
        if row["time"] == 1.0 and row["load_factor"] == 1.0
    )
    if not all(increment["response_audit_gates"].values()):
        raise SystemExit("full-load response increment has a failed root response gate")
    if increment.get("all_five_corner_bodies_raw_and_interval_balance_passed") is not True:
        raise SystemExit("five-body corner balance is not passed")

    geometry_row = next(
        row for row in section_screen["candidate_net_section_inputs"]
        if row["member_id"] == MEMBER and AXIS in row["applies_to_axes"]
    )
    if geometry_row["section_plane"] != "XY at each distinct modeled X-bore center; normal to proposed +Z grain":
        raise SystemExit("candidate cut description changed")

    mesh = model["body_geometry"][MEMBER]["geometry_record"]["geometry_diagnostics"]
    if mesh.get("native_member_mesh") != "GROSS_RECTANGULAR_C3D20":
        raise SystemExit("native mesh geometry changed")
    if mesh.get("gross_cut_and_bore_stiffness_modeled") is not False:
        raise SystemExit("gross-cut/bore omission status changed")

    interface_rows = increment["all_corner_interfaces"]
    target = next(row for row in interface_rows if row["source_connection_name"] == LATERAL_ROW)
    target_action = member_action(target)
    if target_action is None:
        raise SystemExit("target connector no longer acts on the candidate member")
    cut_z = float(target_action[0][2])

    # The cut coordinate comes from the mapped bore-center connector and must
    # correspond to the declared candidate axis row, not a datum resultant.
    axis_geom = next(
        row for row in model["connection_attachment_rows"]
        if row.get("axis_id") == AXIS
    )
    if axis_geom.get("first") != MEMBER or axis_geom.get("lateral_spring_name") != LATERAL_ROW:
        raise SystemExit("candidate lateral carrier/body binding changed")
    if abs(float(axis_geom["point_xyz_mm"][2]) - cut_z) > SECTION_TOL_MM:
        raise SystemExit("axis attachment and connector section coordinates disagree")

    on_plane = []
    for row in interface_rows:
        action = member_action(row)
        if action and abs(float(action[0][2]) - cut_z) <= SECTION_TOL_MM:
            point, force = action
            on_plane.append({
                "role": row["role"],
                "source_connection_name": row["source_connection_name"],
                "source_row_ids": row["source_row_ids"],
                "member_point_global_xyz_mm": point,
                "force_on_member_xyz_n": force,
                "force_normal_to_cut_N": float(force[2]),
            })
    if not any(row["source_connection_name"] == LATERAL_ROW for row in on_plane):
        raise SystemExit("expected lateral connector is not coincident with the candidate cut")

    body_nodes = set(model["physical_body_nodes"][MEMBER])
    node_coords = model["nodes"]
    nodal_loads = model["physical_external_loads"]

    def side_sum(include_plane: bool) -> dict:
        total_fz = 0.0
        radius_fz = 0.0
        nodal_count = 0
        interface_count = 0
        for node in body_nodes:
            point = node_coords[str(node)]
            is_below = point[2] < cut_z - SECTION_TOL_MM
            is_on = abs(point[2] - cut_z) <= SECTION_TOL_MM
            if is_below or (include_plane and is_on):
                total_fz += float(nodal_loads.get(str(node), [0.0, 0.0, 0.0])[2])
                nodal_count += 1
        for row in interface_rows:
            action = member_action(row)
            if action is None:
                continue
            point, force = action
            is_below = point[2] < cut_z - SECTION_TOL_MM
            is_on = abs(float(point[2]) - cut_z) <= SECTION_TOL_MM
            if is_below or (include_plane and is_on):
                total_fz += float(force[2])
                radius = row.get("force_rounding_radius_xyz_n", [0.0, 0.0, 0.0])
                radius_fz += abs(float(radius[2]))
                interface_count += 1
        return {
            "sum_external_Fz_N": total_fz,
            "one_sided_section_resultant_N_positive_tension_on_lower_piece": -total_fz,
            "reported_interface_Fz_rounding_radius_sum_N": radius_fz,
            "included_source_nodal_load_count": nodal_count,
            "included_interface_action_count": interface_count,
        }

    below = side_sum(include_plane=False)
    at_or_below = side_sum(include_plane=True)
    delta = at_or_below["sum_external_Fz_N"] - below["sum_external_Fz_N"]
    target_fz = float(target_action[1][2])
    if abs(delta - sum(row["force_normal_to_cut_N"] for row in on_plane)) > 1e-6:
        raise SystemExit("one-sided free-body change does not equal the coincident point actions")
    if abs(target_fz + 260.9994) > 1e-6:
        raise SystemExit("pinned BG001 connector force changed")

    output = {
        "schema": "current_member_section_cut_distribution_gap/v1",
        "status": "BLOCKED_LOCAL_SECTION_DEMAND_DISTRIBUTION",
        "scope": "a12-rear, BG001 knee_outer_left_post_1, knee_outer_left_spine only",
        "sources": {
            name: {"path": str(path), "sha256": sha}
            for name, (path, sha) in SOURCES.items()
        },
        "candidate_cut": {
            "member": MEMBER,
            "axis_id": AXIS,
            "plane": "global XY at bore center, normal +Z",
            "z_mm": cut_z,
            "candidate_net_area_mm2": geometry_row["candidate_net_area_mm2"],
            "gross_envelope_area_mm2": geometry_row["gross_envelope_area_mm2"],
            "uniform_axial_stress_coefficient_MPa_per_N": geometry_row["uniform_tension_stress_coefficient"]["MPa_per_N_for_uniform_globalZ_tension"],
            "native_mesh": mesh["native_member_mesh"],
            "gross_cut_and_bore_stiffness_modeled": mesh["gross_cut_and_bore_stiffness_modeled"],
        },
        "actions_coincident_with_cut": on_plane,
        "lower_piece_free_body_with_all_plane_actions_excluded": below,
        "lower_piece_free_body_with_all_plane_actions_included": at_or_below,
        "plane_action_change_N": delta,
        "interpretation": {
            "whole_body_wrench_used_as_section_action": False,
            "section_resultant_usable": False,
            "reason": "The native carrier reports the lateral bolt-bearing resultant as a point force exactly on the candidate net-section plane; the gross rectangular member mesh omits the bore. Assigning that point resultant to either side changes the inferred one-sided axial action by its full 260.9994 N. The physical bearing/traction distribution across the bore and through the member is not resolved.",
            "minimum_next_input": "Resolved bolt/bore bearing transfer through the timber (or a section resultant/stress recovery from an actual-bore member model with that transfer resolved), at this cut; then bind member-specific adjusted net-tension strength and combined section-action method before a resistance comparison.",
            "splitting_capacity_or_pass_calculated": False,
            "mechanical_acceptance": False,
        },
    }
    out_path = Path(__file__).with_name("check.json")
    out_path.write_text(json.dumps(output, indent=2, sort_keys=True) + "\n")
    print(json.dumps(output, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
