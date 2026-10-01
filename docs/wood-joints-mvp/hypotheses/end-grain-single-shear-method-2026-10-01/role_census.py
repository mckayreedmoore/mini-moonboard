#!/usr/bin/env python3
"""Authenticate and census ten end-grain-axis bolt demands; assign no NDS roles."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import math
import sys
from pathlib import Path
from typing import Any

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
PACKETS = ROOT / "docs/wood-joints-mvp/hypotheses"
PRODUCER_PATH = PACKETS / "remaining-single-shear-reference-2026-10-01/produce.py"
REGISTER_PATH = Path("/tmp/remaining-single-shear-reference-2026-10-01.json")
PRODUCER_SHA = "5f2a7fdca2ef0c56c661fa10e4122189f8a7a1ae0725062cb8c56d95dd911edf"
REGISTER_SHA = "6551861db1112c91b87c5705bbceb3bb26f55f0d7e70029a74d828519425145e"
CANDIDATE = "compact-floor-flush-wood-joints-development"
REVISION = "led-clearance-2x6-runner-seated-blocks-v1"
CASES = ("a1-rear", "a12-rear", "k12-rear")
FACTORS = (0.1, 0.2, 0.3, 0.45, 0.675, 0.925, 1.0)
EXPECTED_AXES = {
    "center_post_header_left_1", "center_post_header_left_2",
    "center_post_header_right_1", "center_post_header_right_2",
    "center_principal_header_left_1", "center_principal_header_left_2",
    "center_principal_header_right_1", "center_principal_header_right_2",
    "knee_outer_right_inner_header_1", "knee_outer_right_inner_header_2",
}
AXIS_TOL = 1e-8
VECTOR_TOL = 1e-7
GEOMETRY_TOL_MM = 1e-6
TIE_EPSILON_N = 1e-9


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_module(name: str, path: Path, expected_sha: str):
    require(path.is_file() and sha(path) == expected_sha, f"pinned source changed: {path}")
    spec = importlib.util.spec_from_file_location(name, path)
    require(spec is not None and spec.loader is not None, f"cannot import source: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def finite_vector(values: list[float], label: str) -> list[float]:
    require(len(values) == 3, f"{label} must have three components")
    vector = [float(value) for value in values]
    require(all(math.isfinite(value) for value in vector), f"nonfinite {label}")
    return vector


def unit(vector: list[float]) -> list[float]:
    values = finite_vector(vector, "vector")
    magnitude = math.sqrt(math.fsum(value * value for value in values))
    require(magnitude > 0.0 and math.isfinite(magnitude), "zero or invalid vector")
    return [value / magnitude for value in values]


def dot(a: list[float], b: list[float]) -> float:
    return math.fsum(left * right for left, right in zip(a, b, strict=True))


def norm(vector: list[float]) -> float:
    return math.sqrt(math.fsum(value * value for value in vector))


def close(a: float, b: float, tolerance: float = VECTOR_TOL) -> bool:
    return math.isfinite(a) and math.isfinite(b) and math.isclose(
        a, b, rel_tol=1e-10, abs_tol=tolerance
    )


def close_vector(actual: list[float], expected: list[float], tolerance: float) -> bool:
    return len(actual) == len(expected) == 3 and all(
        close(float(a), float(b), tolerance)
        for a, b in zip(actual, expected, strict=True)
    )


def angle_to_grain_degrees(force: list[float], grain: list[float]) -> float | None:
    magnitude = norm(force)
    if magnitude <= TIE_EPSILON_N:
        return None
    cosine = abs(dot(unit(force), unit(grain)))
    return math.degrees(math.acos(max(-1.0, min(1.0, cosine))))


def parallel_grain_receiver(axis: list[float], receivers: list[dict[str, Any]]) -> str:
    axis_unit = unit(axis)
    alignments = {
        row["receiver_id"]: abs(dot(axis_unit, unit(row["source_descriptor_grain_axis_unit_global_xyz"])))
        for row in receivers
    }
    parallel = [name for name, value in alignments.items() if value >= 1.0 - AXIS_TOL]
    transverse = [name for name, value in alignments.items() if value <= AXIS_TOL]
    require(len(receivers) == 2 and len(parallel) == len(transverse) == 1,
            "expected one parallel-grain and one perpendicular-grain receiver")
    return parallel[0]


def validate_register_identity(register: dict[str, Any]) -> None:
    require(
        register.get("schema") == "remaining_candidate_single_shear_reference/v1"
        and register.get("status") == "PASS_SOURCE_BOUND_UNADJUSTED_REFERENCE_ARITHMETIC_ONLY"
        and register.get("producer_sha256") == PRODUCER_SHA
        and register.get("candidate") == CANDIDATE
        and register.get("geometry_revision_id") == REVISION
        and register.get("claim_limits", {}).get("joint_accepted") is False,
        "parent single-shear register identity or claim boundary changed",
    )
    require(
        register.get("counts", {}).get("same_state_bolt_rows") == 1092
        and register.get("counts", {}).get("same_state_lateral_planes_checked") == 1092
        and register.get("counts", {}).get("end_grain_or_axis_orientation_excluded_axes") == 10
        and register.get("counts", {}).get("end_grain_or_axis_orientation_excluded_state_rows") == 210,
        "parent single-shear state inventory changed",
    )


def validate_state(source: dict[str, Any], axis: dict[str, Any]) -> None:
    axis_id = axis["axis_id"]
    receiver_ids = axis["receiver_ids_underhead_to_tip"]
    require(source["axis_id"] == axis_id, "source state axis mismatch")
    require(source["joint_accepted"] is False, "upstream record acceptance boundary changed")
    require(source["single_shear_reference_exclusion"] == "EXCLUDED_END_GRAIN_APPLICABILITY_UNESTABLISHED"
            and source["single_shear_reference_assignments"] is None
            and source["demand_to_reference_ratios_unadjusted_only"] is None,
            "end-grain state acquired a reference or ratio")
    force0 = finite_vector(source["actual_lateral_force_on_receiver_0_N"], "receiver-0 force")
    force1 = finite_vector(source["actual_lateral_force_on_receiver_1_N"], "receiver-1 force")
    require(close_vector(force0, [-value for value in force1], VECTOR_TOL),
            "source lateral endpoint forces do not close")
    resultant = norm(force0)
    require(close(resultant, float(source["actual_lateral_resultant_N"])),
            "source lateral resultant does not match its vector")
    receiver_map = {row["receiver_id"]: row for row in axis["receivers"]}
    require(set(receiver_map) == set(receiver_ids), "axis receiver order/map differs")
    force_map = {receiver_ids[0]: force0, receiver_ids[1]: force1}
    for receiver_id in receiver_ids:
        grain = receiver_map[receiver_id]["source_descriptor_grain_axis_unit_global_xyz"]
        calculated = angle_to_grain_degrees(force_map[receiver_id], grain)
        reported = source["actual_lateral_angle_to_grain_deg_by_receiver"][receiver_id]
        require(calculated is not None and close(calculated, float(reported), 1e-7),
                "actual signed-plane load-to-grain angle differs")
    tie = float(source["same_state_signed_outer_tie_N_once"])
    require(math.isfinite(tie) and tie >= -TIE_EPSILON_N,
            "invalid separately reported same-state tension-only tie")
    tie_sources = source["same_state_tie_source_row_ids"]
    require(isinstance(tie_sources, list) and len(tie_sources) == 1,
            "outer tie source identity is not singular")
    plane_sources = source["lateral_plane_source_row_ids"]
    require(isinstance(plane_sources, list) and len(plane_sources) == 2
            and len(set(plane_sources)) == 2,
            "lateral plane source components are not a two-row pair")
    finite_vector(source["lateral_plane_point_xyz_mm"], "lateral plane point")


def reauthenticate_source_files(demand: Any, register: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    require(demand.FREEZE.is_file() and sha(demand.FREEZE) == demand.FREEZE_SHA,
            "three-case source freeze hash changed")
    freeze = json.loads(demand.FREEZE.read_text(encoding="utf-8"))
    source_cases = register["source_acceptance"]["source_cases"]
    require(
        freeze.get("candidate") == CANDIDATE
        and freeze.get("geometry_revision_id") == REVISION
        and set(freeze.get("cases", {})) == set(CASES)
        and source_cases == freeze["cases"],
        "case freeze/source-file inventory differs from parent register",
    )
    require(register["source_acceptance"]["three_case_freeze_sha256"] == demand.FREEZE_SHA,
            "register does not bind current three-case freeze")
    raw_models = {}
    for case in CASES:
        pins = source_cases[case]
        for name, pin in pins.items():
            source_path = ROOT / pin["path"]
            require(source_path.is_file() and sha(source_path) == pin["sha256"],
                    f"changed {case} source file: {name}")
        model = json.loads((ROOT / pins["model"]["path"]).read_text(encoding="utf-8"))
        response = json.loads((ROOT / pins["response"]["path"]).read_text(encoding="utf-8"))
        require(
            model.get("candidate") == response.get("candidate") == CANDIDATE
            and model.get("geometry_revision_id") == response.get("geometry_revision_id") == REVISION
            and model.get("case_id") == response.get("case_id") == case
            and len(response.get("increments", [])) == len(FACTORS),
            f"wrong frozen model/response identity for {case}",
        )
        raw_models[case] = model
    return freeze, raw_models


def axis_census(
    connection: dict[str, Any],
    basis: dict[str, Any],
    geometry: Any,
) -> dict[str, Any]:
    source = connection["source_record"]
    source_geometry = source["geometry"]
    receivers = basis["receivers"]
    parallel_id = parallel_grain_receiver(
        basis["modeled_bolt_axis_unit_global_xyz"], receivers
    )
    clearance = {row["receiver_id"]: row for row in connection["receiver_clearance_geometry"]}
    require(set(clearance) == set(basis["receiver_ids_underhead_to_tip"]),
            f"current source member inventory differs for {basis['axis_id']}")
    stock_members = []
    for receiver in receivers:
        member = receiver["receiver_id"]
        row = clearance[member]
        stock_members.append({
            "source_stock_member_id": member,
            "member_kind": receiver["grain_map"]["member_kind"],
            "grain_map_path": receiver["grain_map"]["path"],
            "grain_map_sha256": receiver["grain_map"]["sha256"],
            "finished_step_path": row["receiver_step_path"],
            "finished_step_sha256": row["receiver_step_sha256"],
            "coaxial_bore_result_status": row["result_status"],
        })
    seats = list(geometry.source_seats(connection))
    seats_by_role = {row["role"]: row for row in seats}
    require(set(seats_by_role) == {"head", "nut"}, "modeled head/nut seat roles changed")
    require(
        seats_by_role["head"]["member"] == receivers[0]["receiver_id"]
        and seats_by_role["nut"]["member"] == receivers[-1]["receiver_id"],
        f"modeled endpoint seat orientation differs from receiver order: {basis['axis_id']}",
    )
    association_order_flags = [
        bool(row.get("physical_head_to_nut_order_established"))
        for row in source.get("geometric_member_pair_associations", [])
    ]
    require(association_order_flags and not any(association_order_flags),
            "physical head/nut order unexpectedly became established by geometry association")

    intervals = [receiver["modeled_interval_from_underhead_mm"] for receiver in receivers]
    seam_station = float(intervals[0][1])
    axis = basis["modeled_bolt_axis_unit_global_xyz"]
    origin = [
        float(source_geometry["shaft_center_global_xyz_mm"][k])
        - axis[k] * float(source_geometry["modeled_underhead_to_tip_mm"]) / 2.0
        for k in range(3)
    ]
    calculated_seam = [origin[k] + seam_station * axis[k] for k in range(3)]
    return {
        **basis,
        "current_geometry": {
            "family": source["family"],
            "trial_id": source.get("trial_id"),
            "station_id": source.get("station_id"),
            "source_receiver_member_ids": source["receiver_member_ids"],
            "scene_modeled_component_role_ids": source.get("scene_modeled_component_role_ids", []),
            "stock_members_underhead_to_tip": stock_members,
            "interface_point_xyz_mm": calculated_seam,
            "modeled_underhead_to_tip_length_mm": float(
                source_geometry["modeled_underhead_to_tip_mm"]
            ),
        },
        "head_seat": {
            "member": seats_by_role["head"]["member"],
            "point_xyz_mm": list(seats_by_role["head"]["point"].toTuple()),
            "is_model_endpoint_role": True,
        },
        "nut_seat": {
            "member": seats_by_role["nut"]["member"],
            "point_xyz_mm": list(seats_by_role["nut"]["point"].toTuple()),
            "is_model_endpoint_role": True,
        },
        "physical_head_nut_order_established": False,
        "parallel_grain_receiver_id": parallel_id,
    }


def build_census(source_report: Path) -> dict[str, Any]:
    require(sha(PRODUCER_PATH) == PRODUCER_SHA, "pinned final52 producer changed")
    require(source_report.is_file() and sha(source_report) == REGISTER_SHA,
            "pinned final52 parent output missing or changed")
    register = json.loads(source_report.read_text(encoding="utf-8"))
    validate_register_identity(register)
    final = load_module("end_grain_pinned_remaining_single_shear", PRODUCER_PATH, PRODUCER_SHA)
    pins = final.pin_sources()
    require(register.get("source_sha256") == pins,
            "parent output source-pin inventory differs from frozen producer")

    demand = final.load_module(
        "end_grain_pinned_demand_source",
        final.DEMAND_PATH,
        final.PINS["remaining_demand_producer"][1],
    )
    right = final.load_module(
        "end_grain_pinned_plane_checker",
        final.RIGHT_PATH,
        final.PINS["right_plane_checker"][1],
    )
    geometry_pins, connections, primary, upper = final.load_geometry_and_partition(demand, right)
    require(register.get("geometry_input_pins") == geometry_pins,
            "parent output geometry source pins differ")
    maps = final.load_grain_maps()
    geometry = demand.load_method("geometry")
    base, _ = geometry.methods()
    _, _model, _, _, checked_geometry_pins = base.checked_inputs()
    require(checked_geometry_pins == geometry_pins, "geometry input pins changed during census")
    expected_axes = {row["axis_id"] for row in connections}
    require(len(expected_axes) == 52, "wrong two-receiver source cohort")

    axis_metadata = register["axis_geometry_and_grain"]
    require(set(axis_metadata) == expected_axes, "parent axis grain/interval inventory changed")
    source_cases = register["source_acceptance"]["source_cases"]
    freeze, raw_models = reauthenticate_source_files(demand, register)
    del freeze
    for case, native in raw_models.items():
        require(set(native["body_geometry"]) >= {
            receiver["receiver_id"]
            for axis in axis_metadata.values() for receiver in axis["receivers"]
        }, f"source model body geometry incomplete: {case}")
        for connection in connections:
            basis = final.axis_basis(connection, native["body_geometry"], maps)
            axis_id = connection["axis_id"]
            require(basis == axis_metadata[axis_id],
                    f"parent source grain/interval record differs from current model: {axis_id}")

    state_rows = register["state_rows"]
    excluded_rows = [row for row in state_rows if row["axis_id"] in EXPECTED_AXES]
    keys = {(row["case_id"], row["increment_index"], row["axis_id"]) for row in excluded_rows}
    expected_keys = {
        (case, index, axis_id)
        for case in CASES for index in range(len(FACTORS)) for axis_id in EXPECTED_AXES
    }
    require(len(excluded_rows) == 210 and keys == expected_keys,
            "ten end-grain axes do not cover exactly three cases × seven increments")
    require(len(state_rows) == 1092, "parent final52 state register changed")

    connection_by_id = {row["axis_id"]: row for row in connections}
    census_axes = {}
    for axis_id in sorted(EXPECTED_AXES):
        source_rows = sorted(
            (row for row in excluded_rows if row["axis_id"] == axis_id),
            key=lambda row: (CASES.index(row["case_id"]), row["increment_index"]),
        )
        basis = axis_metadata[axis_id]
        require(basis["single_shear_applicability_exclusion"]
                == "EXCLUDED_END_GRAIN_APPLICABILITY_UNESTABLISHED",
                f"wrong retained method exclusion for {axis_id}")
        require(len(source_rows) == 21, f"incomplete same-axis source state count: {axis_id}")
        for row in source_rows:
            require(row["load_factor"] == FACTORS[row["increment_index"]],
                    f"wrong state load factor for {axis_id}")
            validate_state(row, basis)
        census_axis = axis_census(connection_by_id[axis_id], basis, geometry)
        interface_points = [
            finite_vector(row["lateral_plane_point_xyz_mm"], "plane point")
            for row in source_rows
        ]
        require(all(close_vector(point, interface_points[0], GEOMETRY_TOL_MM)
                    for point in interface_points)
                and close_vector(
                    interface_points[0],
                    census_axis["current_geometry"]["interface_point_xyz_mm"],
                    GEOMETRY_TOL_MM,
                ), f"source plane points do not identify modeled seam: {axis_id}")
        census_axes[axis_id] = census_axis

    require(primary == register["source_acceptance"]["primary_axes_excluded"]
            and upper == register["source_acceptance"]["upper_axes_excluded"],
            "primary or upper exclusion inventory changed")
    return {
        "schema": "end_grain_single_shear_role_census/v1",
        "producer_sha256": sha(Path(__file__).resolve()),
        "source_sha256": REGISTER_SHA,
        "source_pins": {
            "source_report": {
                "path": source_report.as_posix(), "sha256": REGISTER_SHA,
            },
            "remaining_single_shear_producer": {
                "path": PRODUCER_PATH.relative_to(ROOT).as_posix(), "sha256": PRODUCER_SHA,
            },
            "source_method_pins_reauthenticated": pins,
            "three_case_freeze_sha256": demand.FREEZE_SHA,
            "case_source_files": source_cases,
            "geometry_input_pins": geometry_pins,
        },
        "axes": census_axes,
        "states": sorted(
            excluded_rows,
            key=lambda row: (
                CASES.index(row["case_id"]),
                row["increment_index"],
                row["axis_id"],
            ),
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-report", type=Path, default=REGISTER_PATH)
    args = parser.parse_args()
    print(json.dumps(build_census(args.source_report), indent=2, allow_nan=False))


if __name__ == "__main__":
    main()
