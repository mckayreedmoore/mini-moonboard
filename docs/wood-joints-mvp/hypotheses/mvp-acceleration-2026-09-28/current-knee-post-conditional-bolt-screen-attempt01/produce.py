"""Conditional individual-bolt and demand-map screen for current BG001.

This reuses the reviewed NDS screen's calculation function and the repository's
TR12 single-shear helper. It is deliberately not a joint-capacity calculation.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import math
from pathlib import Path
from typing import Any


HERE = Path(__file__).resolve().parent
ROOT = next(parent for parent in HERE.parents if (parent / ".git").exists())
ACCEL = HERE.parent
GEOMETRY = ACCEL / "bolt-groups" / "bolt-groups.json"
NDS_SCREEN = ACCEL / "nds-screen" / "produce.py"
NDS_REFERENCE = ACCEL / "nds-screen" / "single-bolt-scenarios.json"
DOWEL_HELPER = ROOT / "fea" / "dowel_yield.py"
OUTPUT = HERE / "conditional-screen.json"

MM_PER_IN = 25.4
LBF_TO_N = 4.4482216152605
NDS_PDF_SHA256 = "5fc837523ff10acc097a162718700a9b4ba64e627d2b0023439146d42fe4ee2a"
NDS_PDF_URL = (
    "https://awc.org/wp-content/uploads/2026/08/"
    "AWC_NDS2024_withCommentary_20250328_WebsiteChapter-12-%E2%80%93-"
    "Dowel-type-fasteners.pdf"
)
EXPECTED_AXES = ("knee_outer_left_post_1", "knee_outer_left_post_2")
EXPECTED_MEMBERS = ("base_post_outer_left", "knee_outer_left_spine")
CASE_IDS = ("a12-rear", "a12-forward", "a12-left", "k12-right", "k12-rear", "a1-rear")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_nds_calculator():
    spec = importlib.util.spec_from_file_location("reviewed_nds_screen", NDS_SCREEN)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load reviewed NDS producer: {NDS_SCREEN}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def close(a: float, b: float, *, abs_tol: float = 1e-8) -> bool:
    return math.isclose(a, b, rel_tol=1e-10, abs_tol=abs_tol)


def expected_reference_mode_iv(diameter_in: float, fe_psi: float,
                               bolt_yield_psi: float, theta_deg: float) -> float:
    # Independent closed-form check used by the reviewed producer.
    return (diameter_in**2 / (3.2 * (1 + 0.25 * theta_deg / 90))
            * math.sqrt(2 * fe_psi * bolt_yield_psi / 6))


def group_map(vy_n: float, vz_n: float, mx_n_mm: float,
              pitch_mm: float) -> list[dict[str, float | str]]:
    """Return equal-stiffness lateral bolt actions whose wrench is (Vy,Vz,Mx).

    Bolt 1 is the lower-Z axis and bolt 2 is the higher-Z axis. The map uses
    signed wrench components on the connected side; opposite cut-side actions
    reverse all signs.
    """
    z_offsets = (-pitch_mm / 2, pitch_mm / 2)
    polar_sum_mm2 = sum(z * z for z in z_offsets)
    result = []
    for axis_id, z in zip(EXPECTED_AXES, z_offsets):
        fy = vy_n / 2 - mx_n_mm * z / polar_sum_mm2
        fz = vz_n / 2
        result.append({
            "axis_id": axis_id,
            "z_offset_from_group_centroid_mm": z,
            "F_y_N": fy,
            "F_z_N": fz,
            "lateral_resultant_N": math.hypot(fy, fz),
        })
    return result


def validate_equilibrium(pitch_mm: float) -> dict[str, Any]:
    checks = []
    examples = (
        (0.0, 0.0, 1000.0),       # 1 N m about x
        (37.25, -82.5, 12345.0),  # mixed signed input for independent closure
        (-21.0, 63.0, -4300.0),
    )
    for vy, vz, mx in examples:
        actions = group_map(vy, vz, mx, pitch_mm)
        sum_fy = sum(row["F_y_N"] for row in actions)
        sum_fz = sum(row["F_z_N"] for row in actions)
        sum_mx = sum(-row["z_offset_from_group_centroid_mm"] * row["F_y_N"]
                     for row in actions)
        assert close(sum_fy, vy)
        assert close(sum_fz, vz)
        assert close(sum_mx, mx)
        checks.append({
            "input_wrench_Vy_N_Vz_N_Mx_N_mm": [vy, vz, mx],
            "recovered_Vy_N_Vz_N_Mx_N_mm": [sum_fy, sum_fz, sum_mx],
            "equilibrium_passed": True,
        })
    torsion = group_map(0.0, 0.0, 1000.0, pitch_mm)
    expected_couple_n = 1000 / pitch_mm
    assert close(torsion[0]["F_y_N"], expected_couple_n)
    assert close(torsion[1]["F_y_N"], -expected_couple_n)
    return {
        "equilibrium_checks": checks,
        "1_N_m_Mx_torsional_pair_N": [torsion[0]["F_y_N"], torsion[1]["F_y_N"]],
        "all_checks_passed": True,
    }


def produce() -> dict[str, Any]:
    geometry = json.loads(GEOMETRY.read_text())
    assert geometry["candidate"] == "compact-floor-flush-wood-joints-development"
    axis_rows = [row for row in geometry["candidate_axes"]
                 if row["group_id"] == "BG001"]
    assert tuple(sorted(row["axis_id"] for row in axis_rows)) == EXPECTED_AXES
    axes = {row["axis_id"]: row for row in axis_rows}
    assert all(tuple(row["receiver_member_ids"]) == EXPECTED_MEMBERS
               for row in axis_rows)

    spacing_rows = [row for row in geometry["candidate_group_center_spacing"]
                    if row["group_id"] == "BG001"]
    assert len(spacing_rows) == 1
    spacing = spacing_rows[0]
    pitch_mm = spacing["axis_normal_center_spacing_components"][
        "perpendicular_inter_axis_pitch_mm"]
    p1 = axes[EXPECTED_AXES[0]]["shaft_center_global_xyz_mm"]
    p2 = axes[EXPECTED_AXES[1]]["shaft_center_global_xyz_mm"]
    assert close(p2[0] - p1[0], 0.0)
    assert close(p2[1] - p1[1], 0.0)
    assert close(p2[2] - p1[2], pitch_mm)
    centroid = [(p1[i] + p2[i]) / 2 for i in range(3)]

    diameters_mm = [axes[axis_id]["modeled_shaft_diameter_mm"]
                    for axis_id in EXPECTED_AXES]
    assert close(diameters_mm[0], diameters_mm[1])
    diameter_mm = diameters_mm[0]
    diameter_in = diameter_mm / MM_PER_IN
    assert close(diameter_in, 0.25)

    # The source's receiver intervals are geometric proposals; equal interval
    # lengths make main/side role order immaterial to these symmetric cases.
    intervals_by_member: dict[str, list[float]] = {}
    for member in EXPECTED_MEMBERS:
        intervals = [axes[axis_id]["geometric_receiver_order_proposal"]
                     ["receiver_intervals_from_underhead_mm"][member]
                     for axis_id in EXPECTED_AXES]
        lengths = [abs(interval[1] - interval[0]) for interval in intervals]
        assert close(lengths[0], lengths[1])
        intervals_by_member[member] = lengths
    member_lengths_mm = {member: values[0]
                         for member, values in intervals_by_member.items()}
    assert all(close(value, 38.1) for value in member_lengths_mm.values())
    main_length_in = member_lengths_mm[EXPECTED_MEMBERS[0]] / MM_PER_IN
    side_length_in = member_lengths_mm[EXPECTED_MEMBERS[1]] / MM_PER_IN

    grain_rows = [row for row in geometry["candidate_axis_receiver_grain_angles"]
                  if row["group_id"] == "BG001"
                  and row["axis_id"] in EXPECTED_AXES]
    proposed_grains = {tuple(row["source_proposed_grain_unit_global_xyz"])
                       for row in grain_rows}
    assert proposed_grains == {(0.0, 0.0, 1.0)}
    assert len(grain_rows) == 4
    assert all(close(row["axis_to_grain_angle_deg_unsigned"], 90.0)
               for row in grain_rows)

    nds = load_nds_calculator()
    cases = (
        {
            "case_id": "global_y_lateral_load_perpendicular_to_proposed_grain",
            "global_lateral_direction": "+/-Y",
            "load_to_grain_angle_deg": 90,
            "bearing_fe_psi_both_members": 4450,
            "theta_deg": 90,
        },
        {
            "case_id": "global_z_lateral_load_parallel_to_proposed_grain",
            "global_lateral_direction": "+/-Z",
            "load_to_grain_angle_deg": 0,
            "bearing_fe_psi_both_members": 5600,
            "theta_deg": 0,
        },
    )
    single_bolt_scenarios = []
    for case in cases:
        fe = case["bearing_fe_psi_both_members"]
        result = nds.calculate(
            diameter_in, main_length_in, side_length_in, fe, fe,
            case["theta_deg"],
        )
        independent_iv = expected_reference_mode_iv(
            diameter_in, fe, 45000, case["theta_deg"])
        assert close(result["reference_values_lbf"]["IV"], independent_iv)
        single_bolt_scenarios.append({
            **case,
            "main_member": EXPECTED_MEMBERS[0],
            "side_member": EXPECTED_MEMBERS[1],
            "main_bearing_length_in": main_length_in,
            "side_bearing_length_in": side_length_in,
            "main_bearing_psi": fe,
            "side_bearing_psi": fe,
            "yield_values_lbf": result["yield_values_lbf"],
            "reference_values_lbf": result["reference_values_lbf"],
            "governing_mode": result["governing_mode"],
            "reference_lateral_lbf": result["reference_lateral_lbf"],
            "reference_lateral_N": result["reference_lateral_lbf"] * LBF_TO_N,
            "independent_mode_IV_lbf": independent_iv,
            "status": "conditional unadjusted individual-bolt reference only",
        })
    y_reference_n = single_bolt_scenarios[0]["reference_lateral_N"]
    z_reference_n = single_bolt_scenarios[1]["reference_lateral_N"]
    torsion_coefficient_n_per_nm = 1000 / pitch_mm

    equilibrium = validate_equilibrium(pitch_mm)
    assert close(torsion_coefficient_n_per_nm, 23.781212841855)

    source_sha = geometry.get("source_sha256_observed", {})
    for relative_path, expected_hash in source_sha.items():
        source_path = ROOT / relative_path
        assert source_path.exists(), f"Missing pinned geometry source: {relative_path}"
        assert sha256(source_path) == expected_hash, (
            f"Geometry source pin changed: {relative_path}")

    axes_ordered = [axes[axis_id] for axis_id in EXPECTED_AXES]
    return {
        "artifact": "current BG001 conditional individual-bolt and demand-map screen",
        "status": "conditional screen only; mechanical_acceptance=false",
        "candidate": geometry["candidate"],
        "geometry_revision_id": geometry.get("geometry_revision_id"),
        "group": {
            "group_id": "BG001",
            "axis_ids_lower_to_higher_z": list(EXPECTED_AXES),
            "receiver_members": list(EXPECTED_MEMBERS),
            "axis_unit_global_xyz": axes_ordered[0]["axis_head_to_nut_unit_global_xyz"],
            "proposed_grain_unit_global_xyz_both_members": [0.0, 0.0, 1.0],
            "bolt_axis_to_proposed_grain_angle_deg": 90.0,
            "modeled_diameter_mm": diameter_mm,
            "modeled_diameter_in": diameter_in,
            "modeled_inter_axis_pitch_mm": pitch_mm,
            "axis_centers_global_xyz_mm": {
                EXPECTED_AXES[0]: p1,
                EXPECTED_AXES[1]: p2,
            },
            "group_centroid_global_xyz_mm": centroid,
            "receiver_intervals_from_underhead_mm": {
                member: axes_ordered[0]["geometric_receiver_order_proposal"]
                ["receiver_intervals_from_underhead_mm"][member]
                for member in EXPECTED_MEMBERS
            },
            "modeled_receiver_length_mm_by_member": member_lengths_mm,
            "modeled_receiver_length_in_by_member": {
                member: value / MM_PER_IN
                for member, value in member_lengths_mm.items()
            },
            "physical_head_to_nut_order_verified": False,
            "delivered_stock_observed": False,
        },
        "conditional_single_bolt_basis": {
            "diameter_in": diameter_in,
            "main_and_side_bearing_lengths_in": [main_length_in, side_length_in],
            "interface_gap_in": 0.0,
            "bolt_bending_yield_psi_assumption": 45000,
            "wood_specific_gravity_scenario": 0.50,
            "fe_parallel_to_grain_psi_assumption": 5600,
            "fe_perpendicular_to_grain_psi_assumption": 4450,
            "shank_assumption": "full-body smooth 1/4-inch diameter through both modeled receiver bearing lengths",
            "material_status": "conditional scenario only; actual wood and bolt are unobserved",
            "scenarios": single_bolt_scenarios,
            "limits": [
                "Six NDS/TR12 single-shear yield modes are evaluated for each direction.",
                "Reference values are unadjusted individual-fastener values, not adjusted resistance.",
                "Equal 38.1 mm receiver lengths and identical Fe inputs make unresolved main/side order immaterial here.",
                "Full-body shank, effective bearing lengths, and zero interface gap are assumptions, not delivered-part or fit findings.",
            ],
        },
        "equal_stiffness_two_bolt_lateral_demand_map": {
            "assumption": "two identical lateral stiffnesses, rigid group translation/rotation, no axial action, no clearances, and no group resistance claim",
            "axes": "global X/Y/Z; bolt axes parallel global X; bolt spacing along global Z",
            "wrench_reference_point_global_xyz_mm": centroid,
            "input_units": {"V_y": "N", "V_z": "N", "M_x": "N mm"},
            "axis_order_and_z_offsets_mm": {
                EXPECTED_AXES[0]: -pitch_mm / 2,
                EXPECTED_AXES[1]: pitch_mm / 2,
            },
            "polar_sum_z_squared_mm2": pitch_mm**2 / 2,
            "bolt_demand_equations": {
                EXPECTED_AXES[0]: "F_y = V_y/2 + M_x/p; F_z = V_z/2",
                EXPECTED_AXES[1]: "F_y = V_y/2 - M_x/p; F_z = V_z/2",
                "p_mm": pitch_mm,
                "Mx_sign_basis": "right-hand positive global X moment; signs are for bolt forces reconstructing the signed group wrench",
            },
            "sensitivity_coefficients": {
                "per_1_N_Vy_each_bolt_Fy_N": [0.5, 0.5],
                "per_1_N_Vz_each_bolt_Fz_N": [0.5, 0.5],
                "per_1_N_m_Mx_each_bolt_Fy_N": [torsion_coefficient_n_per_nm, -torsion_coefficient_n_per_nm],
                "per_1_N_mm_Mx_each_bolt_Fy_N": [1 / pitch_mm, -1 / pitch_mm],
            },
            "individual_component_to_reference_coefficients": {
                "Fy_abs_over_perpendicular_reference_per_1_N_Vy_each_bolt": 0.5 / y_reference_n,
                "Fy_abs_over_perpendicular_reference_per_1_N_m_Mx_each_bolt": torsion_coefficient_n_per_nm / y_reference_n,
                "Fz_abs_over_parallel_reference_per_1_N_Vz_each_bolt": 0.5 / z_reference_n,
                "interpretation": "direction-specific single-bolt reference ratios only; do not add, combine, or read them as a group interaction or pass result",
            },
            "individual_bolt_reference_values_N": {
                "global_y_perpendicular_to_proposed_grain": y_reference_n,
                "global_z_parallel_to_proposed_grain": z_reference_n,
            },
            "equilibrium_reproduction": equilibrium,
        },
        "missing_signed_group_wrench": {
            "status": "missing from current accepted demand evidence; no values populated",
            "group_id": "BG001",
            "interface": "force and moment exerted on knee_outer_left_spine by base_post_outer_left; opposite sign on the other side of the cut",
            "reference_point_global_xyz_mm": centroid,
            "axes": "global axis-aligned X/Y/Z; X is the modeled bolt axis",
            "units": {"F_x_F_y_F_z": "N", "M_x_M_y_M_z": "N mm"},
            "force_components": ["F_x", "V_y", "V_z"],
            "moment_components": ["M_x", "M_y", "M_z"],
            "six_case_signed_values": {
                case_id: {"F_x_N": None, "V_y_N": None, "V_z_N": None,
                          "M_x_N_mm": None, "M_y_N_mm": None, "M_z_N_mm": None}
                for case_id in CASE_IDS
            },
            "lateral_map_uses_only": ["V_y", "V_z", "M_x"],
            "reason": "The six-case demand register reports no path-complete joint demand subset; the c11 one-case branch is explicitly diagnostic and not an accepted demand.",
        },
        "compatibility_exclusions": {
            "F_x": "bolt-axis axial action (tension/separation or compression/contact) is outside the single-shear dowel-yield helper and is not mapped",
            "M_y": "a two-row axial tie couple could be kinematically formed across the Z pitch, but bolt tension, washers, wood anchorage, seat contact, and transfer are unqualified and the action is not mapped",
            "M_z": "the collinear-Z bolt pair has no axial-force lever arm for M_z; any contribution would require unresolved contact, bearing, or additional geometry",
            "combined_lateral_loading": "component-to-reference ratios are separate axis-only comparisons; no combined shear interaction equation is adopted",
        },
        "checks_still_missing": [
            {
                "check": "signed BG001 group wrench and load path",
                "available": "bolt group centroid and geometry only",
                "missing": "accepted six-case cut wrench [F_x,V_y,V_z,M_x,M_y,M_z] at the stated point, with case, cut-side, and sign convention",
            },
            {
                "check": "group action / NDS row and load sharing",
                "available": "two modeled axes and 42.05 mm center pitch; geometry inventory marks Cg/force null and load-aligned row not assessed",
                "missing": "verified hole stations, loaded-row orientation, applicable NDS group factors, and defensible stiffness/clearance load split",
            },
            {
                "check": "spacing, end distance, and edge distance",
                "available": "inter-axis pitch only, along proposed vertical grain Z",
                "missing": "dimensioned/observed hole centers and all end/edge distances on each actual receiver, evaluated for each load direction",
            },
            {
                "check": "splitting, row shear, tear-out, and net section",
                "available": "none established by bolt-group geometry inventory",
                "missing": "receiver-specific geometry and material basis with signed load direction and applicable criteria",
            },
            {
                "check": "washers, head/nut bearing, and local crushing",
                "available": "no qualification in the single-shear model",
                "missing": "delivered washer/head/nut dimensions, material, seating, bearing areas, and force/washer bending demand",
            },
            {
                "check": "bolt fit, thread exposure, and layer engagement",
                "available": "modeled 1/4-inch shaft envelope and 38.1 mm receiver intervals",
                "missing": "delivered bolt shank/thread layout, actual hole and gap, bearing planes, and usable engagement through the two members",
            },
            {
                "check": "wood basis and adjustments",
                "available": "conditional SG 0.50, Fe 5600/4450 psi scenario",
                "missing": "actual species/grade/moisture and applicable load-duration, wet-service, temperature, and other adjustment factors",
            },
            {
                "check": "complete connection transfer",
                "available": "geometric member-pair association",
                "missing": "validated contact/seat/bolt path carrying the full wrench through the connected members and into downstream supports",
            },
        ],
        "sources": {
            "geometry_inventory": {
                "path": str(GEOMETRY.relative_to(ROOT)),
                "sha256": sha256(GEOMETRY),
                "revision": geometry.get("geometry_revision_id"),
                "upstream_source_sha256_observed": source_sha,
            },
            "reviewed_nds_screen_producer": {
                "path": str(NDS_SCREEN.relative_to(ROOT)),
                "sha256": sha256(NDS_SCREEN),
                "function_reused": "calculate",
            },
            "dowel_yield_helper": {
                "path": str(DOWEL_HELPER.relative_to(ROOT)),
                "sha256": sha256(DOWEL_HELPER),
            },
            "reviewed_nds_reference_scenarios": {
                "path": str(NDS_REFERENCE.relative_to(ROOT)),
                "sha256": sha256(NDS_REFERENCE),
                "NDS_2024_chapter_12_pdf_url": NDS_PDF_URL,
                "NDS_2024_chapter_12_pdf_sha256": NDS_PDF_SHA256,
            },
            "demand_coverage_basis": {
                "path": str((ACCEL / "demand-coverage-register-2026-09-29.md").relative_to(ROOT)),
                "sha256": sha256(ACCEL / "demand-coverage-register-2026-09-29.md"),
                "finding": "no path-complete member or joint demand subset; c11 response is a single diagnostic branch, not accepted forces",
            },
        },
        "verification": {
            "geometry_identity_pitch_lengths_and_grain_checked": True,
            "all_six_lateral_yield_modes_reused_from_reviewed_producer": True,
            "mode_IV_independently_recomputed_for_both_actual_length_scenarios": True,
            "equal_stiffness_group_map_signed_force_and_moment_equilibrium_checked": True,
            "mechanical_acceptance": False,
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    actions = parser.add_mutually_exclusive_group(required=True)
    actions.add_argument("--write", action="store_true")
    actions.add_argument("--verify", action="store_true")
    args = parser.parse_args()
    content = json.dumps(produce(), indent=2, sort_keys=True) + "\n"
    if args.write:
        OUTPUT.write_text(content)
        print("Wrote conditional BG001 screen; NDS mode IV and signed group equilibrium checks passed.")
    else:
        assert OUTPUT.read_text() == content, "Screen differs from recomputed source-pinned result"
        print("Verified source pins, actual modeled receiver lengths, two NDS scenarios, and equilibrium checks.")


if __name__ == "__main__":
    main()
