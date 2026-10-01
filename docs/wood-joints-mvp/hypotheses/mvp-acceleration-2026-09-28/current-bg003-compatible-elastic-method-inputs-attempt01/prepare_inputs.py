#!/usr/bin/env python3
"""Build a source-pinned BG003 elastic-method input register (no solver)."""

from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path


HERE = Path(__file__).resolve().parent
REPO = next(p for p in HERE.parents if (p / "AGENTS.md").is_file())
BASE = Path("docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28")

PINNED = {
    "a12-rear": {
        "path": BASE / "current-corner-native-demand-export-attempt03/corner-demand-report.json",
        "sha256": "812a62fa3cd96a8983649c84a8c78a8d176d639465c887b11d1827a3f8f1ee17",
        "status": "PASS_NUMERICAL_CORNER_DEMAND_REPORT_ONLY",
    },
    "a1-rear": {
        "path": BASE / "current-corner-a1-rear-case-bound-export-attempt01/corner-demand-report.json",
        "sha256": "2b498383b319aeb31e74c3b329e0758330b8b39d0a8e1b4788437db06453bfce",
        "status": "PASS_NUMERICAL_CORNER_DEMAND_REPORT_ONLY",
    },
    "k12-rear": {
        "path": BASE / "current-corner-k12-rear-case-bound-export-attempt01/corner-demand-report.json",
        "sha256": "a78ca15d9d888dbddf6963be34a2f5e57159b0df77ef6b754cf631dbba8c10d0",
        "status": "PASS_K12_REAR_NUMERICAL_CORNER_DEMAND_REPORT_ONLY",
    },
}

GEOMETRY_PATH = BASE / "current-knee-three-member-transfer-attempt01/calculation.json"
GEOMETRY_SHA256 = "fb7fba30fdcdabf44c90a5ac7cfe167b6a9f659af8543a8070066f15ad45c5b1"
METHOD_PATH = BASE / "current-bg003-continuous-dowel-method-candidate-attempt01/README.md"
METHOD_SHA256 = "c3e39a756bcfdeb95e6dd1a3221116ae76db992fc6f8e45471f2b93bfff20ee9"
PROFILE_PATH = BASE / "current-bg003-piecewise-bearing-profile-feasibility-attempt01/profile-check.json"
PROFILE_SHA256 = "215bfecdd74e11688a5289c85c3179b79dbb7751c67376ff4def955f8fd6bb9e"

EXPECTED_AXES = ["knee_outer_left_side_1", "knee_outer_left_side_2"]
EXPECTED_MEMBERS = {
    "knee_outer_left_spine",
    "base_side_left",
    "knee_outer_left_inner_frame_block",
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_pinned(path: Path, expected: str) -> tuple[Path, str, dict]:
    absolute = REPO / path
    actual = sha256(absolute)
    if actual != expected:
        raise SystemExit(f"source pin changed: {path}: {actual} != {expected}")
    return absolute, actual, json.loads(absolute.read_text())


def check_close_zero(values: list[float], tol: float) -> None:
    if any(not math.isfinite(x) or abs(x) > tol for x in values):
        raise SystemExit(f"source wrench balance outside {tol}: {values}")


def cross(a: list[float], b: list[float]) -> list[float]:
    return [
        a[1] * b[2] - a[2] * b[1],
        a[2] * b[0] - a[0] * b[2],
        a[0] * b[1] - a[1] * b[0],
    ]


def build_case(case_id: str, pin: dict, geometry: dict) -> dict:
    source_path, source_hash, report = read_pinned(pin["path"], pin["sha256"])
    if report.get("case_id") != case_id or report.get("status") != pin["status"]:
        raise SystemExit(f"wrong report identity/status for {case_id}")
    if report.get("actual_case_demand_usable_for_conditional_joint_checks") is not True:
        raise SystemExit(f"report is not marked usable for conditional demands: {case_id}")
    increments = report.get("increments")
    if not isinstance(increments, list) or len(increments) != 7:
        raise SystemExit(f"expected 7 authenticated increments for {case_id}")

    stages = []
    max_force_residual = 0.0
    max_moment_residual = 0.0
    max_midpoint_transform_residual = 0.0
    max_source_action_reconstruction_force_residual = 0.0
    max_source_action_reconstruction_moment_residual = 0.0
    modeled = geometry["modeled_geometry_inputs"]
    intervals = modeled["receiver_intervals_from_underhead_mm"]
    member_order = geometry["modeled_order_head_to_nut_proposal"]
    midpoint_s = {member: sum(intervals[member]) / 2.0 for member in member_order}
    for ordinal, inc in enumerate(increments, 1):
        gates = inc.get("response_audit_gates")
        if not isinstance(gates, dict) or not gates or not all(v is True for v in gates.values()):
            raise SystemExit(f"failed/missing response gate at {case_id} increment {ordinal}")
        if inc.get("all_five_corner_bodies_raw_and_interval_balance_passed") is not True:
            raise SystemExit(f"five-body balance failed at {case_id} increment {ordinal}")

        group = inc.get("primary_physical_bolt_groups", {}).get("BG003")
        if not isinstance(group, dict) or group.get("physical_bolt_count") != 2:
            raise SystemExit(f"missing BG003 source group at {case_id} increment {ordinal}")
        bolts = group.get("bolts")
        if not isinstance(bolts, list) or [b.get("axis_id") for b in bolts] != EXPECTED_AXES:
            raise SystemExit(f"unexpected BG003 axes/order at {case_id} increment {ordinal}")

        packed_bolts = []
        for bolt in bolts:
            wrenches = bolt.get("physical_member_wrenches_at_axis_datum")
            if not isinstance(wrenches, dict) or set(wrenches) != EXPECTED_MEMBERS:
                raise SystemExit(f"missing per-member wrench at {case_id}/{bolt['axis_id']}")
            actions = bolt.get("actions")
            if not isinstance(actions, list) or len(actions) != 3:
                raise SystemExit(f"expected tie plus two lateral plane actions for {case_id}/{bolt['axis_id']}")
            roles = sorted(a.get("role") for a in actions)
            if roles != [
                "candidate_bolt_lateral_plane",
                "candidate_bolt_lateral_plane",
                "physical_bolt_outer_seat_tension",
            ]:
                raise SystemExit(f"unexpected source action roles for {case_id}/{bolt['axis_id']}: {roles}")

            reconstructed = {
                member: {"force_xyz_n": [0.0, 0.0, 0.0], "moment_xyz_nmm": [0.0, 0.0, 0.0]}
                for member in EXPECTED_MEMBERS
            }
            axis_point = bolt["axis_datum_global_xyz_mm"]
            for action in actions:
                for side in ("first", "second"):
                    member = action[side]
                    point = action[f"{side}_point_global_xyz_mm"]
                    force = action[f"force_on_{side}_xyz_n"]
                    lever = [point[i] - axis_point[i] for i in range(3)]
                    moment = cross(lever, force)
                    for i in range(3):
                        reconstructed[member]["force_xyz_n"][i] += force[i]
                        reconstructed[member]["moment_xyz_nmm"][i] += moment[i]
            for member in EXPECTED_MEMBERS:
                for i in range(3):
                    f_res = reconstructed[member]["force_xyz_n"][i] - wrenches[member]["force_xyz_n"][i]
                    m_res = reconstructed[member]["moment_xyz_nmm"][i] - wrenches[member]["moment_xyz_nmm"][i]
                    max_source_action_reconstruction_force_residual = max(
                        max_source_action_reconstruction_force_residual, abs(f_res)
                    )
                    max_source_action_reconstruction_moment_residual = max(
                        max_source_action_reconstruction_moment_residual, abs(m_res)
                    )
                    if abs(f_res) > 1e-8 or abs(m_res) > 1e-7:
                        raise SystemExit(f"point actions do not reconstruct source wrench: {case_id}/{bolt['axis_id']}/{member}")

            # The first side plane fixes the modeled interval origin. The tie
            # endpoints independently check the first and final interval ends.
            spine_to_middle = next(
                a for a in actions
                if a.get("role") == "candidate_bolt_lateral_plane"
                and a.get("first") == member_order[0]
                and a.get("second") == member_order[1]
            )
            tie = next(a for a in actions if a.get("role") == "physical_bolt_outer_seat_tension")
            underhead_x = spine_to_middle["first_point_global_xyz_mm"][0] - intervals[member_order[0]][1]
            if abs(underhead_x + intervals[member_order[0]][0] - tie["first_point_global_xyz_mm"][0]) > 1e-6:
                raise SystemExit(f"source tie head point disagrees with modeled interval start: {case_id}/{bolt['axis_id']}")
            if abs(underhead_x + intervals[member_order[2]][1] - tie["second_point_global_xyz_mm"][0]) > 1e-6:
                raise SystemExit(f"source tie nut point disagrees with modeled interval end: {case_id}/{bolt['axis_id']}")

            midpoint_points = {
                member: [underhead_x + midpoint_s[member], axis_point[1], axis_point[2]]
                for member in member_order
            }
            midpoint_wrenches = {}
            for member in member_order:
                source_wrench = wrenches[member]
                force = source_wrench["force_xyz_n"]
                moment = source_wrench["moment_xyz_nmm"]
                r_mid_from_axis = [midpoint_points[member][i] - axis_point[i] for i in range(3)]
                shift = cross(r_mid_from_axis, force)
                midpoint_moment = [moment[i] - shift[i] for i in range(3)]
                midpoint_wrenches[member] = {
                    "force_xyz_n": force,
                    "moment_xyz_nmm": midpoint_moment,
                    "reference_global_xyz_mm": midpoint_points[member],
                    "translation_rule": "M_mid = M_axis - (r_mid-r_axis) cross F; derived rigid-body wrench shift, not a separately sourced moment",
                }
                restored = [midpoint_moment[i] + shift[i] for i in range(3)]
                max_midpoint_transform_residual = max(
                    max_midpoint_transform_residual,
                    *(abs(restored[i] - moment[i]) for i in range(3)),
                )

            force_residual = [
                sum(w["force_xyz_n"][i] for w in wrenches.values()) for i in range(3)
            ]
            moment_residual = [
                sum(w["moment_xyz_nmm"][i] for w in wrenches.values()) for i in range(3)
            ]
            check_close_zero(force_residual, 1e-8)
            check_close_zero(moment_residual, 1e-7)
            max_force_residual = max(max_force_residual, *(abs(x) for x in force_residual))
            max_moment_residual = max(max_moment_residual, *(abs(x) for x in moment_residual))

            packed_bolts.append(
                {
                    "axis_id": bolt["axis_id"],
                    "axis_datum_global_xyz_mm": bolt["axis_datum_global_xyz_mm"],
                    "head_to_nut_unit_global_xyz": bolt["head_to_nut_unit_global_xyz"],
                    "source_actions_with_exact_points_and_signed_vectors": actions,
                    "physical_member_wrenches_at_axis_datum": wrenches,
                    "derived_receiver_reference_points_global_xyz_mm": midpoint_points,
                    "derived_member_wrenches_at_receiver_interval_midpoints": midpoint_wrenches,
                    "wrench_sum_residual_xyz_n": force_residual,
                    "wrench_sum_residual_xyz_nmm": moment_residual,
                    "wrench_interpretation": "external member resultants at the bolt axis datum; not internal bolt shear/moment or a substitute beam load distribution",
                }
            )

        stages.append(
            {
                "increment_ordinal": ordinal,
                "time": inc["time"],
                "load_factor": inc["load_factor"],
                "response_audit_gates": gates,
                "all_five_corner_bodies_raw_and_interval_balance_passed": True,
                "BG003_bolts": packed_bolts,
            }
        )

    if "authenticated_source_case" in report:
        raw = report["authenticated_source_case"]
        auth = {
            key: raw[key]
            for key in (
                "case_id",
                "case_record_sha256",
                "source_case_manifest_sha256",
                "input_model_json_sha256",
                "response_audit_json_sha256",
                "audited_deck_sha256",
                "audited_native_data_sha256",
                "external_case_context_sha256",
                "native_dat_sha256",
                "parent_report_serialization_sha256",
                "response_audit_sha256",
                "response_auditor_sha256",
                "response_status",
                "selected_input_deck_sha256",
                "selected_input_model_sha256",
                "source_case_register_sha256",
            )
            if key in raw
        }
        execution = raw.get("adjacent_native_execution_evidence", {}).get("execution", {})
        if execution:
            auth["adjacent_native_execution"] = {
                key: execution[key] for key in ("run_id", "container_confirmed_terminal", "native_solve_executed", "returncode")
                if key in execution
            }
        acceptance = raw.get("adjacent_native_execution_evidence", {}).get("parent_response_acceptance_binding", {})
        body_audit = acceptance.get("parent_all_body_audit", {})
        if body_audit:
            auth["parent_all_body_audit"] = {
                key: body_audit[key]
                for key in (
                    "status",
                    "sha256",
                    "source_model_sha256",
                    "source_response_sha256",
                    "increment_count",
                    "physical_body_count_per_increment",
                    "all_body_and_global_resultants_passed",
                )
                if key in body_audit
            }
    else:
        raw = report.get("fresh_source_case", {})
        auth = {
            key: raw[key]
            for key in (
                "case_record_sha256",
                "fresh_case_load_and_body_wrench_match_register",
                "historical_response_forces_used",
                "load_register_not_modified_or_used_as_response",
                "source_model_inputs_sha256",
            )
            if key in raw
        }

    return {
        "case_id": case_id,
        "report_status": report["status"],
        "report_path": str(pin["path"]),
        "report_sha256": source_hash,
        "candidate": report.get("candidate"),
        "geometry_revision_id": report.get("geometry_revision_id"),
        "source_case_authentication_from_report": auth,
        "conditional_response_scope": report.get("selected_floor_response_scope"),
        "increment_count": len(stages),
        "increments": stages,
        "maximum_BG003_member_wrench_sum_residual": {
            "force_N": max_force_residual,
            "moment_Nmm": max_moment_residual,
            "midpoint_transform_round_trip_Nmm": max_midpoint_transform_residual,
            "source_action_to_member_wrench_reconstruction_force_N": max_source_action_reconstruction_force_residual,
            "source_action_to_member_wrench_reconstruction_moment_Nmm": max_source_action_reconstruction_moment_residual,
        },
        "scope_limit": "case-specific conditional source demands only; no demand transfer between cases and no BG003 capacity/pass conclusion",
    }


def main() -> None:
    geometry_path, geometry_hash, geometry = read_pinned(GEOMETRY_PATH, GEOMETRY_SHA256)
    method_path = REPO / METHOD_PATH
    if sha256(method_path) != METHOD_SHA256:
        raise SystemExit("continuous-dowel method candidate source pin changed")
    profile_path, profile_hash, _ = read_pinned(PROFILE_PATH, PROFILE_SHA256)

    geom = geometry["modeled_geometry_inputs"]
    if geometry.get("group_id") != "BG003" or geometry.get("axis_ids") != EXPECTED_AXES:
        raise SystemExit("unexpected pinned BG003 geometry identity")
    if geom.get("modeled_axis_diameter_mm") != 6.35:
        raise SystemExit("unexpected modeled fastener diameter")

    d = geom["modeled_axis_diameter_mm"]
    inertia = math.pi * d**4 / 64.0
    midpoint_s = {
        member: sum(limits) / 2.0
        for member, limits in geom["receiver_intervals_from_underhead_mm"].items()
    }
    density_low, density_high = 350.0, 550.0
    literature = {
        "source": "Gikonyo et al. (2024), Eq. 4(c-d), based on the cited embedment database; density inputs are illustrative literature bounds, not source-case material data",
        "source_url": "https://www.diva-portal.org/smash/get/diva2%3A1829333/FULLTEXT02.pdf",
        "equations": {
            "kf_el_parallel_N_per_mm3": "0.1374 * rho_kg_per_m3 - 12.9",
            "kf_el_perpendicular_N_per_mm3": "0.0922 * rho_kg_per_m3 - 18.20",
        },
        "density_interval_kg_per_m3": [density_low, density_high],
        "resulting_moduli_N_per_mm3": {
            "parallel": [0.1374 * density_low - 12.9, 0.1374 * density_high - 12.9],
            "perpendicular": [0.0922 * density_low - 18.20, 0.0922 * density_high - 18.20],
        },
        "limitations": [
            "The cited study's parameter equations draw on a database mainly covering solid timber and glulam, not these delivered BG003 members.",
            "No actual BG003 density, moisture, initial embedment curve, or directional foundation modulus is present in the pinned case sources.",
            "The study's Table 2 validation subset (462 kg/m3 CLT) reports 97.8 N/mm3 parallel and 49.0 N/mm3 perpendicular; the perpendicular value was estimated from a general embedment ratio, not directly tested on that subset.",
            "The 2024 study's 0.28 mm initial-slip/10%-stiffness detail is a validation specimen feature, not a BG003 clearance or contact input.",
            "Do not infer density from the conditional NDS specific-gravity scenario G=0.50 or use Fe as stiffness.",
        ],
    }

    result = {
        "schema": "bg003_compatible_elastic_method_inputs/v1",
        "status": "INPUT_REGISTER_AND_METHOD_FEASIBILITY_ONLY_NO_BG003_ELASTIC_SOLUTION",
        "finding": "A per-bolt elastic proxy can use one continuous beam and three independent rigid receivers, with the source member wrenches applied as external receiver loads. With positive bilateral foundation stiffness and EI, its energy system is well-posed modulo common transverse rigid-motion gauges; the source wrenches are self-equilibrated and do no work on those modes. No BG003 elastic response is computed here because no case-applicable steel/foundation stiffness set or physical contact state is pinned. The usual fixed-foundation BOEF form would instead require wood reference motion.",
        "source_pins": {
            "three_member_geometry": {
                "path": str(GEOMETRY_PATH),
                "sha256": geometry_hash,
            },
            "prior_continuous_dowel_method_candidate": {
                "path": str(METHOD_PATH),
                "sha256": METHOD_SHA256,
            },
            "prior_constructed_bearing_profile_result": {
                "path": str(PROFILE_PATH),
                "sha256": profile_hash,
                "interpretation": "prior statically admissible chosen profile only; not a measured elastic law or constitutive input",
            },
            "case_reports": {
                case_id: {"path": str(pin["path"]), "sha256": pin["sha256"]}
                for case_id, pin in PINNED.items()
            },
        },
        "geometry_and_available_conditional_scenarios": {
            "group_id": geometry["group_id"],
            "axis_ids": geometry["axis_ids"],
            "modeled_stack_order_head_to_nut": geometry["modeled_order_head_to_nut_proposal"],
            "axis_direction_global_xyz": geom["axis_direction_global_xyz"],
            "diameter_mm": d,
            "solid_circular_section_second_moment_mm4": inertia,
            "steel_bending_stiffness": "E_s * pi * d^4 / 64; no product-specific E_s is pinned",
            "receiver_intervals_from_underhead_mm": geom["receiver_intervals_from_underhead_mm"],
            "receiver_interval_midpoints_from_underhead_mm": midpoint_s,
            "raw_modeled_bearing_lengths_mm": geom["raw_modeled_bearing_lengths_mm"],
            "proposed_grain_vectors_global_xyz": geom["proposed_grain_vectors_global_xyz"],
            "proposed_main_grain_angle_degrees_from_positive_z": geom["main_proposed_grain_angle_from_global_positive_z_degrees"],
            "modeled_interface_interval_gaps_mm": geom["modeled_interface_interval_gaps_mm"],
            "physical_order_or_stock_grain_verified": geom["physical_order_or_stock_grain_verified"],
            "active_contact_or_bearing_law_verified": geom["active_contact_or_bearing_law_verified"],
            "conditional_material_hardware_scenario_only": geometry["conditional_scenario_inputs"],
            "material_values_not_supplied": [
                "member density and moisture content",
                "directional initial embedment/foundation stiffness for each receiver",
                "actual bolt elastic modulus or delivered bolt product",
                "actual gap/contact side and actual wood compliance (the local proxy declares receivers rigid)",
            ],
        },
        "published_elastic_embedment_inputs_non_adopted": literature,
        "linear_operator_and_units": {
            "origin": "Euler-Bernoulli equilibrium plus linear Winkler springs. The fixed-foundation equation below is the conventional form; the free-receiver proxy uses the same beam/foundation energy and adds rigid transverse degrees of freedom for each receiver.",
            "equation": "E_s I * w''''(s) + K_line,j * (w(s) - u_wood,j(s)) = p_beam(s), s in receiver interval j",
            "w_and_u_wood": "2-component transverse displacement in the global Y-Z plane [mm]",
            "E_s_I": "circular isotropic steel flexural rigidity, equal about both transverse axes [N mm^2]",
            "K_line": "2x2 transverse line-foundation stiffness matrix [N/mm^2]; if derived from a 2x2 embedment stress/displacement tangent K_f [N/mm^3], K_line = d * K_f",
            "p_beam": "externally applied transverse beam load per axial length [N/mm]; a point force is represented with a Dirac delta and total force [N]",
            "member_segment_equivalent_spring": "dF = f_h(u) * d * ds; f_h in [N/mm^2], d and ds in [mm], dF in [N]",
            "grain_rotation_candidate": "K_global = R(theta) * diag(k_f,parallel, k_f,perpendicular) * R(theta)^T is a possible linear matrix assumption, not validated for the BG003 oblique/mixed contact state by the cited parallel/perpendicular tests.",
            "free_rigid_receiver_energy_proxy": "Pi = 1/2*integral(E_s*I*|w''|^2 ds) + 1/2*sum_j integral((w-u_j)^T*K_line,j*(w-u_j) ds) - sum_j(F_j dot u_j(mid) + M_j(mid) dot theta_j). For s along +X, u_j(s)=u_j(mid)+theta_j cross ((s-s_mid)*e_X), retaining global Y-Z components.",
            "free_receiver_dofs": "Each receiver has independent transverse translation (u_y,u_z) and bending rotation (theta_y,theta_z) at its interval midpoint. Wrench moments are rigid-body shifted from the source axis datum to these midpoints in inputs.json. Axial translation/tension and torsion are outside the lateral beam model.",
            "external_load_mapping": "In this local proxy, apply each source member wrench to its rigid receiver body; do not also apply the source interface point actions or member wrenches as beam loads. Distributed foundation reactions are the solved internal transfer between the bolt and receivers.",
        },
        "known_answer_operator_fixture": {
            "name": "infinite_2d_EB_beam_point_force_rotated_linear_foundation",
            "purpose": "small analytic check of Euler-Bernoulli signs, units, matrix rotation, and cross-axis coupling; synthetic values only, not candidate material or geometry parameters",
            "domain_and_boundary": "infinite beam on uniform bilateral linear foundation; displacement and derivatives decay at both infinities",
            "EI_N_mm2": 1.0,
            "K_line_global_N_per_mm2": [[2.5, 1.5], [1.5, 2.5]],
            "K_line_eigenvalues_N_per_mm2": [4.0, 1.0],
            "eigenbasis_rotation_degrees": 45.0,
            "point_force_at_s0_global_N": [1.0, 0.0],
            "green_function": "g_k(s) = exp(-beta*abs(s))*(cos(beta*abs(s))+sin(beta*abs(s)))/(8*EI*beta^3), beta=(k/(4*EI))^(1/4)",
            "expected_midpoint_displacement_global_mm": [0.23927669529663687, -0.11427669529663687],
            "comparison_rule": "For each foundation eigenvalue k, project P onto its eigenvector, multiply by g_k(0), and rotate back. A scalar Y/Z implementation that omits the off-diagonal K terms must fail this expected result.",
            "does_not_test": ["finite three-receiver interfaces", "wood constitutive validity", "compression-only contact", "clearance", "axial tie", "strength or capacity"],
        },
        "well_posedness_assessment": {
            "source_wrenches_well_pose_declared_free_receiver_proxy": True,
            "pinned_inputs_define_numerical_BG003_response": False,
            "free_receiver_proxy_assumptions": "One isolated bolt; three independent rigid timber receivers; positive bilateral linear foundation over all three pinned intervals; finite Euler-Bernoulli beam with natural free-end conditions at modeled interval ends; use transverse components of the source wrenches as receiver loads. This is not actual timber compliance or a shared two-bolt joint model.",
            "reason": "Under that declared energy model, the source wrenches are a complete generalized load vector; unknown receiver translations/rotations are solved with the continuous beam. The source wrenches must not be reapplied as beam loads or prescribed spring reactions. A fixed-foundation model would need prescribed u_wood(s). A numerical BG003 response still needs case-applicable EI and foundation stiffness values.",
            "necessary_gauge_compatibility": "For every increment and bolt, the three source member wrench sum at their common axis datum is zero to floating-point precision. Hence the load is orthogonal to common rigid translation/slope modes. This verifies gauge compatibility only; it does not fix the relative-response magnitude without EI and K_line.",
            "free_rigid_body_modes": "The transverse EB-plus-free-receiver energy has four common null modes: Y/Z translation and Y/Z slope (rigid rotations about Z/Y). Fix w(s0)=0 and w'(s0)=0 only as a gauge and verify zero gauge reaction; these are not physical supports. Additional null modes arise if a required foundation direction or interval has zero active stiffness.",
            "superposition": "Circular isotropic steel gives equal EI in both bending planes. Component superposition is exact only for a linear fixed contact state and a foundation matrix diagonal in the chosen axes (or after solving its coupled matrix operator). An oblique anisotropic foundation produces cross terms; compression-only contact, gaps, seating, or nonlinear embedment changes the active set and invalidates ordinary load superposition.",
            "published_biaxial_scope": "The cited 2024 BoF study models orthogonal grain-parallel/perpendicular spring directions and explicitly limits its validation/loading discussion to parallel or perpendicular in-plane loading. It does not validate this BG003 40-degree, unequal, non-collinear vector response.",
            "axial_and_contact_omissions": [
                "The source outer-seat tie force is axial along +X; a lateral Euler-Bernoulli foundation equation does not carry or qualify that axial force.",
                "No installed preload is specified or credited.",
                "Zero modeled gaps and grain directions are proposals; actual contact side, clearance, initial seating, and physical receiver order remain unverified.",
                "No end restraint, shaft overhang, washer/seat compliance, or wood-body stiffness is defined for the three-receiver beam boundary-value problem.",
            ],
        },
        "stop_conditions_before_a_BG003_solution": [
            "Pin an explicit steel E and applicable shaft section/product/continuity scenario; the axis diameter alone does not establish delivered section or end conditions.",
            "Provide a case-applicable directional initial bearing stiffness law for each member (and a justified off-axis 2x2 coupling law for the 40-degree middle grain frame), or keep stiffness as clearly labelled non-adopted sensitivities.",
            "Declare whether the next calculation is fixed-foundation (then provide wood reference motions) or the free rigid-receiver proxy (then apply source member wrenches only as receiver loads and do not reuse interface actions as beam loads).",
            "Define actual contact/gaps and the active set, or explicitly keep the calculation bilateral and label it only as that mathematical scenario; do not present it as the physical unilateral joint.",
            "Keep shared timber deformation across the two bolts, axial tie force, preload, bearing strength, yielding, splitting, group action, and design resistance outside this per-bolt lateral proxy unless separately sourced and checked.",
            "First reproduce the analytic fixture above and verify vector equilibrium/interface continuity on a finite three-receiver fixture before any case response is computed.",
        ],
        "cases": [build_case(case_id, pin, geometry) for case_id, pin in PINNED.items()],
        "disposition": "The source data support a well-posed conditional per-bolt free-receiver proxy if its positive bilateral spring and rigid-receiver assumptions are declared. No BG003 elastic response was computed because the pinned sources do not provide an actual E_s/foundation-stiffness set or physical contact state. The proxy is not a shared two-bolt timber solution; the arbitrary bearing profile remains a separate statically admissible idealization.",
    }

    out = HERE / "inputs.json"
    out.write_text(json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n")
    print(f"wrote {out.relative_to(REPO)}")
    print(f"cases={len(result['cases'])}; BG003 physical bolts/case=2; increments/case=7")
    print("maximum wrench sum residuals: " + json.dumps({
        c["case_id"]: c["maximum_BG003_member_wrench_sum_residual"] for c in result["cases"]
    }, sort_keys=True))


if __name__ == "__main__":
    main()
