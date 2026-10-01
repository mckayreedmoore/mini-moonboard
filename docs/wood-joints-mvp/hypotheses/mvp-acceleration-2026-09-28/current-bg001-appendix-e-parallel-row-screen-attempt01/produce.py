#!/usr/bin/env python3
"""Reproduce a bounded BG001 Appendix E directional reference screen.

This calculation reports parallel-to-grain components and conditional reference
capacities. It is deliberately not a mixed-action connection acceptance check.
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
import math
import sys
from pathlib import Path
from typing import Any


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[4]
ACCEL = REPO / "docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28"

REPORT_REL = Path(
    "docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/"
    "current-corner-native-demand-export-attempt03/corner-demand-report.json"
)
MODEL_REL = Path(
    "docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/"
    "current-springa-selected-floor-a12-rear-attempt03/model.json"
)
RESPONSE_REL = Path(
    "docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/"
    "current-springa-selected-floor-a12-rear-attempt03/response.json"
)
SECTION_REL = Path(
    "docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/"
    "current-corner-local-wood-screen-attempt01/section-screen.json"
)
HELPER_REL = Path("mini_moonboard/bolted_timber_checks.py")
BASIS_REL = Path("docs/wood-joints-mvp/wood-limit-state-basis.md")
NDS_SCREEN_REL = Path("docs/wood-joints-mvp/mvp-acceleration-2026-09-28/nds-screen/screen.json")

EXPECTED_SHA256 = {
    REPORT_REL.as_posix(): "812a62fa3cd96a8983649c84a8c78a8d176d639465c887b11d1827a3f8f1ee17",
    MODEL_REL.as_posix(): "8a90452d8afa1f1722b3253b18d5aeec72c432033a22d5d0828082022cc1cda8",
    RESPONSE_REL.as_posix(): "892dadeed0b20d809ce5250d3cd1c3deb31697f69208d8bbefb5f702160e1274",
    SECTION_REL.as_posix(): "22209a82b0bda6dfc5c140ccc4e481717e0e7c71d30a5827271c81ac71070564",
    HELPER_REL.as_posix(): "a1414547d9eaa3d60e81482b4a2cac2d49e88f31aafa341dca5be9ec8ef4aa13",
    BASIS_REL.as_posix(): "1110e664a88f704773a463e83a2aeac3954b978048d811e4bff1effa55aa7c2e",
    NDS_SCREEN_REL.as_posix(): "1ac9e05f15e1863f62e101bb595e1902440dd9e537a172c43a3dee50ddbb6005",
}

N_PER_LBF = 4.4482216152605
MM_PER_IN = 25.4
NDS_FT_BASE_PSI = 575.0
NDS_FV_BASE_PSI = 180.0
NDS_APPENDIX_PDF_SHA256 = "99b0a54e7133b3cf6dd156d8fe864c1717c951487bf5baa99c34da9a68a6bbb7"
NDS_APPENDIX_PDF_URL = (
    "https://web-media.awc.org/wp-content/uploads/2021/12/17210019/"
    "AWC_NDS2024_withCommentary_20240719_AWCWebsite_Appendix.pdf"
)
NDS_ERRATA_URL = "https://awc.org/wp-content/uploads/2026/03/2024-NDS-Errata-and-Addenda-03.23.26.pdf"
NDS_ERRATA_SHA256 = "b3f4f8b3b2e2ffa5eb618de9e1182614c329d9e4a135096667364dc9a8e473c0"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text())


def close(actual: float, expected: float, *, abs_tol: float = 1e-8) -> bool:
    return math.isclose(actual, expected, rel_tol=1e-10, abs_tol=abs_tol)


def add_vectors(left: list[float], right: list[float]) -> list[float]:
    return [a + b for a, b in zip(left, right, strict=True)]


def vector_norm(vector: list[float]) -> float:
    return math.sqrt(math.fsum(value * value for value in vector))


def load_helper():
    path = REPO / HELPER_REL
    spec = importlib.util.spec_from_file_location("pinned_bolted_timber_checks", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load pinned helper {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def main() -> None:
    source_hashes: dict[str, str] = {}
    for rel, expected in EXPECTED_SHA256.items():
        path = REPO / rel
        actual = sha256(path)
        if actual != expected:
            raise SystemExit(f"source hash mismatch: {rel}: {actual} != {expected}")
        source_hashes[rel] = actual

    local_errata = Path("/tmp/AWC-NDS2024-errata-2026.pdf")
    if local_errata.exists() and sha256(local_errata) != NDS_ERRATA_SHA256:
        raise SystemExit("local NDS errata source hash mismatch")

    report = load_json(REPO / REPORT_REL)
    model = load_json(REPO / MODEL_REL)
    section = load_json(REPO / SECTION_REL)
    response = load_json(REPO / RESPONSE_REL)
    nds_screen = load_json(REPO / NDS_SCREEN_REL)

    if report.get("schema") != "current_corner_native_demand_report/v1":
        raise SystemExit("unexpected demand-report schema")
    if report.get("status") != "PASS_NUMERICAL_CORNER_DEMAND_REPORT_ONLY":
        raise SystemExit("source demand report is not in its expected conditional state")
    if report.get("candidate") != "compact-floor-flush-wood-joints-development":
        raise SystemExit("candidate changed")
    if report.get("geometry_revision_id") != "led-clearance-2x6-runner-seated-blocks-v1":
        raise SystemExit("geometry revision changed")
    if report.get("case_id") != "a12-rear":
        raise SystemExit("screen is pinned to the wrong case")
    if report.get("source_response_forces_promoted") is not True:
        raise SystemExit("source response force promotion is not proven")
    if report.get("actual_case_demand_usable_for_conditional_joint_checks") is not True:
        raise SystemExit("source demand report does not authorize conditional demand use")
    if report.get("qualification_boundary", {}).get("complete_joint_accepted") is not False:
        raise SystemExit("source report acceptance boundary changed")

    authenticated = report["authenticated_source_case"]
    if authenticated.get("input_model_json_sha256") != source_hashes[MODEL_REL.as_posix()]:
        raise SystemExit("report is no longer bound to the pinned source model")
    if authenticated.get("response_audit_json_sha256") != source_hashes[RESPONSE_REL.as_posix()]:
        raise SystemExit("report is no longer bound to the pinned response audit")
    terminal = authenticated["adjacent_native_execution_evidence"]["execution"]
    if terminal.get("returncode") != 0 or terminal.get("native_solve_executed") is not True:
        raise SystemExit("the source case lacks its pinned converged execution record")

    root_gates = report["response_audit_root_gates"]
    if not root_gates or not all(value is True for value in root_gates.values()):
        raise SystemExit("one or more top-level response gates are not true")
    final = next(
        (row for row in report["increments"] if close(row["load_factor"], 1.0)), None
    )
    if final is None or not close(final["time"], 1.0):
        raise SystemExit("the full-factor increment is missing")
    if not all(value is True for value in final["response_audit_gates"].values()):
        raise SystemExit("one or more full-factor response gates are not true")
    if response.get("schema") != "current_springa_selected_floor_physical_response_audit/v1":
        raise SystemExit("unexpected source response-audit schema")

    if model.get("case_id") != "a12-rear" or model.get("candidate") != report["candidate"]:
        raise SystemExit("model/report case identity mismatch")
    if model.get("geometry_revision_id") != report["geometry_revision_id"]:
        raise SystemExit("model/report geometry revision mismatch")
    if model.get("complete_joint_validated") is not False:
        raise SystemExit("model acceptance boundary changed")

    group = final["primary_physical_bolt_groups"]["BG001"]
    if group.get("physical_bolt_count") != 2 or group.get("lateral_plane_count") != 2:
        raise SystemExit("BG001 bolt-group topology changed")
    bolts = group.get("bolts", [])
    expected_axes = {"knee_outer_left_post_1", "knee_outer_left_post_2"}
    if {row["axis_id"] for row in bolts} != expected_axes:
        raise SystemExit("BG001 axis inventory changed")

    members = ("knee_outer_left_spine", "base_post_outer_left")
    member_actions: dict[str, list[float]] = {member: [0.0, 0.0, 0.0] for member in members}
    per_bolt: list[dict[str, Any]] = []
    lateral_action_count = 0
    axial_tie_sum_by_member = {member: [0.0, 0.0, 0.0] for member in members}
    axis_z: list[float] = []
    for bolt in bolts:
        axis_z.append(float(bolt["axis_datum_global_xyz_mm"][2]))
        action_by_role = {action["role"]: action for action in bolt["actions"]}
        if set(action_by_role) != {"candidate_bolt_lateral_plane", "physical_bolt_outer_seat_tension"}:
            raise SystemExit(f"unexpected action decomposition on {bolt['axis_id']}")
        lateral = action_by_role["candidate_bolt_lateral_plane"]
        axial = action_by_role["physical_bolt_outer_seat_tension"]
        if lateral["first"] != members[0] or lateral["second"] != members[1]:
            raise SystemExit(f"unexpected BG001 lateral action ordering on {bolt['axis_id']}")
        lateral_action_count += 1
        first_force = [float(value) for value in lateral["force_on_first_xyz_n"]]
        second_force = [float(value) for value in lateral["force_on_second_xyz_n"]]
        if any(not close(a, -b, abs_tol=1e-7) for a, b in zip(first_force, second_force, strict=True)):
            raise SystemExit(f"BG001 lateral action is not equal/opposite on {bolt['axis_id']}")
        member_actions[members[0]] = add_vectors(member_actions[members[0]], first_force)
        member_actions[members[1]] = add_vectors(member_actions[members[1]], second_force)
        axial_first = [float(value) for value in axial["force_on_first_xyz_n"]]
        axial_second = [float(value) for value in axial["force_on_second_xyz_n"]]
        if any(not close(a, -b, abs_tol=1e-7) for a, b in zip(axial_first, axial_second, strict=True)):
            raise SystemExit(f"BG001 seat tie action is not equal/opposite on {bolt['axis_id']}")
        axial_tie_sum_by_member[members[0]] = add_vectors(axial_tie_sum_by_member[members[0]], axial_first)
        axial_tie_sum_by_member[members[1]] = add_vectors(axial_tie_sum_by_member[members[1]], axial_second)
        cross = [first_force[0], first_force[1], 0.0]
        per_bolt.append(
            {
                "axis_id": bolt["axis_id"],
                "axis_z_mm": bolt["axis_datum_global_xyz_mm"][2],
                "force_on_spine_xyz_N": first_force,
                "force_on_post_xyz_N": second_force,
                "spine_parallel_component_along_plus_Z_N": first_force[2],
                "spine_cross_grain_resultant_component_N": vector_norm(cross),
                "spine_parallel_to_crossgrain_angle_deg": math.degrees(
                    math.atan2(vector_norm(cross), abs(first_force[2]))
                ),
            }
        )
    if lateral_action_count != 2:
        raise SystemExit("expected two BG001 lateral bolt-plane actions")

    # The native input supplies +Z proposed grain for both members. Confirm it
    # in each source body record rather than inferring it from the row direction.
    body_data: dict[str, dict[str, Any]] = {}
    for member in members:
        body = model["body_geometry"][member]["geometry_record"]
        descriptor = body["source_descriptor"]
        grain = descriptor["grain_global_xyz"]
        if not all(close(float(value), expected) for value, expected in zip(grain, (0.0, 0.0, 1.0), strict=True)):
            raise SystemExit(f"{member}: proposed grain vector changed")
        body_data[member] = body

    # The section screen binds one modeled 7.5 mm bore at each spine hole plane.
    section_row = next(
        row for row in section["candidate_net_section_inputs"]
        if row["member_id"] == "knee_outer_left_spine"
        and "knee_outer_left_post_1" in row["applies_to_axes"]
    )
    bore_diameter_mm = float(section["modeled_geometry_inputs"]["modeled_bore_diameter_mm_from_profile_void_intervals"])
    thickness_mm = float(body_data[members[0]]["width_mm"])
    width_mm = float(body_data[members[0]]["depth_mm"])
    if not close(thickness_mm, 38.1) or not close(width_mm, 139.7) or not close(bore_diameter_mm, 7.5):
        raise SystemExit("BG001 spine section or modeled bore geometry changed")
    if not close(thickness_mm, float(body_data[members[1]]["width_mm"])):
        raise SystemExit("BG001 post thickness at bolt axis differs from the pinned geometry")
    if not close(thickness_mm * (width_mm - bore_diameter_mm), section_row["candidate_net_area_mm2"]):
        raise SystemExit("reconstructed spine net section does not match the pinned section screen")

    if not close(min(axis_z), 171.45) or not close(max(axis_z), 213.5):
        raise SystemExit("BG001 bolt-center locations changed")
    pitch_mm = max(axis_z) - min(axis_z)
    if not close(pitch_mm, 42.05):
        raise SystemExit("BG001 row pitch changed")

    helper = load_helper()
    row_results: list[dict[str, Any]] = []
    for member in members:
        force = member_actions[member]
        parallel_signed = force[2]  # both source-bound grain vectors are +Z
        if abs(parallel_signed) < 1e-7:
            raise SystemExit(f"{member}: no parallel demand to screen")
        start_z = float(body_data[member]["start"][2])
        end_z = float(body_data[member]["end"][2])
        if parallel_signed < 0:
            loaded_end = "negative_Z_member_start"
            nearest_loaded_bolt_z = min(axis_z)
            end_distance_mm = nearest_loaded_bolt_z - start_z
        else:
            loaded_end = "positive_Z_member_end"
            nearest_loaded_bolt_z = max(axis_z)
            end_distance_mm = end_z - nearest_loaded_bolt_z
        if end_distance_mm <= 0:
            raise SystemExit(f"{member}: row force does not point toward a member end")
        s_critical_mm = min(end_distance_mm, pitch_mm)
        thickness_in = thickness_mm / MM_PER_IN
        end_distance_in = end_distance_mm / MM_PER_IN
        pitch_in = pitch_mm / MM_PER_IN
        row_reference_lbf = helper.dfl_parallel_row_tear_out_reference_lbf(
            thickness_in, 2, end_distance_in, pitch_in
        )
        demand_lbf = abs(parallel_signed) / N_PER_LBF
        cross_y = force[1]
        cross_x = force[0]
        row_results.append(
            {
                "member_id": member,
                "proposed_grain_global_xyz": [0.0, 0.0, 1.0],
                "signed_group_parallel_force_along_plus_Z_N": parallel_signed,
                "parallel_component_demand_N": abs(parallel_signed),
                "parallel_component_demand_lbf": demand_lbf,
                "group_cross_grain_force_xyz_N": [cross_x, cross_y, 0.0],
                "group_cross_grain_resultant_N": math.hypot(cross_x, cross_y),
                "group_parallel_to_crossgrain_angle_deg": math.degrees(
                    math.atan2(math.hypot(cross_x, cross_y), abs(parallel_signed))
                ),
                "loaded_end_direction": loaded_end,
                "loaded_end_distance_mm": end_distance_mm,
                "row_pitch_mm": pitch_mm,
                "critical_spacing_mm": s_critical_mm,
                "member_thickness_along_bolt_axis_mm": thickness_mm,
                "member_width_mm": width_mm,
                "n_bolts_in_row": 2,
                "row_reference_method": "NDS-2024 Appendix E.3-1/E.3.1, E.3-2; one row, two shear lines",
                "base_reference_inputs": {
                    "Fv_psi": NDS_FV_BASE_PSI,
                    "Fv_adjusted_factors_applied": [],
                    "adjusted_Fv_prime": "unresolved; apply the NDS Chapter 4 sawn-lumber factors when material and service inputs are established",
                },
                "base_unadjusted_row_reference_lbf": row_reference_lbf,
                "base_unadjusted_row_reference_N": row_reference_lbf * N_PER_LBF,
                "component_ratio_to_base_unadjusted_reference": demand_lbf / row_reference_lbf,
                "ratio_interpretation": "reference-only component ratio; not an adjusted capacity ratio or DCR",
            }
        )

    # Candidate E.2 net-tension section at a spine X-bore center. This is a
    # geometry-only net-area/reference comparison, not a recovered cut force.
    net_tension_lbf = helper.dfl_net_parallel_tension_reference_lbf(
        thickness_mm / MM_PER_IN,
        width_mm / MM_PER_IN,
        (bore_diameter_mm / MM_PER_IN,),
    )
    net_area_mm2 = thickness_mm * (width_mm - bore_diameter_mm)
    spine_demand_lbf = abs(member_actions[members[0]][2]) / N_PER_LBF
    net_tension = {
        "member_id": members[0],
        "section_plane": section_row["section_plane"],
        "candidate_net_area_mm2": net_area_mm2,
        "pinned_section_screen_net_area_mm2": section_row["candidate_net_area_mm2"],
        "one_modeled_bore_diameter_mm": bore_diameter_mm,
        "proposed_grain_direction": "+Z",
        "base_reference_inputs": {"Ft_psi": NDS_FT_BASE_PSI, "Ft_adjusted_factors_applied": []},
        "base_unadjusted_net_tension_reference_lbf": net_tension_lbf,
        "base_unadjusted_net_tension_reference_N": net_tension_lbf * N_PER_LBF,
        "same_parallel_component_demand_lbf": spine_demand_lbf,
        "component_ratio_to_base_unadjusted_reference": spine_demand_lbf / net_tension_lbf,
        "qualification": "candidate E.2 net-section reference only; adjustment/applicability incomplete",
    }

    if nds_screen.get("scenario_id") != "ordinary-two-member-1-4in-bolt-45ksi-fyb":
        raise SystemExit("pinned NDS source-screen identity changed")

    output = {
        "schema": "current_bg001_appendix_e_parallel_row_screen/v1",
        "status": "CONDITIONAL_PARALLEL_COMPONENT_SCREEN_ONLY",
        "mechanical_acceptance": False,
        "candidate": report["candidate"],
        "geometry_revision_id": report["geometry_revision_id"],
        "case_id": report["case_id"],
        "increment": {"time": final["time"], "load_factor": final["load_factor"]},
        "source_hashes": source_hashes,
        "standard_source": {
            "standard": "2024 National Design Specification for Wood Construction, Appendix E, E.1-E.3 and E.6 example",
            "appendix_pdf_url": NDS_APPENDIX_PDF_URL,
            "appendix_pdf_sha256": NDS_APPENDIX_PDF_SHA256,
            "appendix_printed_pages": [174, 175],
            "appendix_pdf_pages_zero_based": [8, 9],
            "solid_sawn_adjustment_path": "NDS Chapter 4 §4.3 / Table 4.3.1; Fv prime must use the applicable sawn-lumber factors when inputs are established",
            "cvr_scope_review": {
                "errata_url": NDS_ERRATA_URL,
                "errata_pdf_sha256": NDS_ERRATA_SHA256,
                "checked_on": "2026-09-30",
                "finding": "March 2026 errata §5.3.10 is in Chapter 5 and addresses Fvx/Fvy for structural glued-laminated timber; Chapter 4 §4.3/Table 4.3.1 governs sawn-lumber adjustments and supplies no basis here to import that Cvr factor",
                "cvr_applied": False,
            },
            "base_strength_source": "pinned project basis and existing dfl_*_reference helpers: conditional dry DF-L No.2 base Ft=575 psi, Fv=180 psi",
            "historical_2018_commentary_not_used_as_2024_authority": True,
        },
        "method_applicability": {
            "appendix_e1_scope": "single fastener/group of closely spaced fasteners loaded parallel to grain; local failure may be net section or fastener-row tear-out",
            "parallel_component_calculation_is_defensible": True,
            "full_appendix_e1_loading_condition_proven_for_real_BG001": False,
            "reason_full_condition_unproven": "BG001 has substantial, oppositely signed cross-grain actions at its individual bolt planes and separate axial outer-seat ties; no Appendix E mixed-action interaction is asserted.",
            "loaded_end_row_reference_more_direct_than_assumed_hole_cut_force": "E.3 is a group loaded-end row path computed from the signed group force, proposed grain, row, and loaded-end geometry. Appendix E.6 also compares local wood capacities to connection group load; a separate continuum cut-force resultant at the modeled hole-center plane is not required for this nominal group reference calculation.",
            "hole_center_plane_role": "candidate E.2 net-section capacity section only; it is not asserted as the unique or governing internal member cut",
            "component_ratios_are_not_DCRs": True,
        },
        "material_scenario": {
            "species_grade": "Douglas Fir-Larch No. 2, proposed conditional scenario",
            "service_scenario": "dry, proposed conditional scenario",
            "proposed_grain_vectors_global_xyz": {member: [0.0, 0.0, 1.0] for member in members},
            "material_geometry_hardware_observed": False,
            "base_values": {"Ft_psi": NDS_FT_BASE_PSI, "Fv_psi": NDS_FV_BASE_PSI},
        },
        "bg001_group_resultants": {
            "physical_bolt_count": group["physical_bolt_count"],
            "lateral_plane_count": group["lateral_plane_count"],
            "per_bolt_lateral_actions": per_bolt,
            "lateral_plane_force_on_spine_xyz_N": member_actions[members[0]],
            "lateral_plane_force_on_post_xyz_N": member_actions[members[1]],
            "separate_axial_outer_seat_tie_resultant_on_spine_xyz_N": axial_tie_sum_by_member[members[0]],
            "separate_axial_outer_seat_tie_resultant_on_post_xyz_N": axial_tie_sum_by_member[members[1]],
        },
        "row_tear_out_component_screens": row_results,
        "spine_candidate_net_section_reference": net_tension,
        "required_unresolved_checks": [
            "complete mixed parallel/cross-grain/axial bolt-group interaction and cross-grain splitting",
            "adjusted Ft and Fv values with every applicable 2024 NDS factor and the actual material/service inputs",
            "fastener lateral-yield, bolt axial/tie, washer-seat bearing, and their applicable interaction",
            "complete member Chapter 3 section actions and net-section checks across the entire BG001/BG003/BG045 load path",
            "actual finished section, bore and cut geometry, grain, species/grade, moisture, and delivered fastener",
            "six-case demands and required engagement/material/floor sensitivities",
        ],
        "claim_limits": [
            "No PASS, FAIL, capacity acceptance, or fabrication/climbing release is made.",
            "Only the source-bound a12-rear full-factor BG001 bolt-plane parallel component is compared to conditional references.",
            "The E.3 results are unadjusted base one-row, two-shear-line component references; all applicable solid-sawn Fv adjustments remain pending.",
            "The E.2 spine area is a candidate geometry-only section through one modeled bore; no actual member cut force is inferred from the whole-body wrench.",
            "Do not sum or transfer any capacities to BG003 or BG045, the retained LEG/RUNNER arrangements, or other cases.",
        ],
    }

    output_path = HERE / "screen.json"
    output_path.write_text(json.dumps(output, indent=2, sort_keys=True) + "\n")
    print(f"wrote {output_path.relative_to(REPO)}")
    for row in row_results:
        print(
            row["member_id"],
            f"parallel={row['parallel_component_demand_N']:.6f} N",
            f"base E.3={row['base_unadjusted_row_reference_N']:.3f} N",
            f"base-reference ratio={row['component_ratio_to_base_unadjusted_reference']:.6f}",
        )
    print(
        "spine E.2 base reference",
        f"{net_tension['base_unadjusted_net_tension_reference_N']:.3f} N",
    )


if __name__ == "__main__":
    main()
