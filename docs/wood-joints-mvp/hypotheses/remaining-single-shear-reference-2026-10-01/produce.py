#!/usr/bin/env python3
"""Emit source-bound unadjusted single-shear references; accept no joint."""

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
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
PACKETS = ROOT / "docs/wood-joints-mvp/hypotheses"
DEMAND_PATH = PACKETS / "remaining-candidate-washer-demands-2026-10-01/produce.py"
RIGHT_PATH = PACKETS / "right-corner-signed-load-path-2026-10-01/produce.py"
GEOMETRY_MAP_PATH = (
    ROOT / "docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/"
    "current-frame-timber-material-frame-map-attempt01/current-frame-timber-material-frame-map.json"
)
BLOCK_MAP_PATH = (
    ROOT / "docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/"
    "current-block-material-frame-map-attempt02/material-frame-map.json"
)
NDS_PRODUCER_PATH = PACKETS / "mvp-acceleration-2026-09-28/nds-screen/produce.py"
NDS_SCENARIO_PATH = PACKETS / "mvp-acceleration-2026-09-28/nds-screen/single-bolt-scenarios.json"
YIELD_HELPER_PATH = ROOT / "fea/dowel_yield.py"
FE_HELPER_PATH = ROOT / "mini_moonboard/bolted_timber_checks.py"

PINS = {
    "remaining_demand_producer": (
        DEMAND_PATH,
        "0c58a7dc6c82ccc2624ee9d3355e2840f738be01961ddaf3f64486700e89e6c9",
    ),
    "right_plane_checker": (
        RIGHT_PATH,
        "13989f42845210caadb15c1cf3903a47c2634b866195dc0c5f2156ea9605f2ea",
    ),
    "frame_grain_map": (
        GEOMETRY_MAP_PATH,
        "f867b4926ed23c9f356005c134778e138c8b1230547f0b69be7c3f9bc2a42409",
    ),
    "block_grain_map": (
        BLOCK_MAP_PATH,
        "8705b8f100a2d3355c236fc19e6798bb7ad4862ba2d51826cf63a88db1285480",
    ),
    "single_bolt_method": (
        NDS_PRODUCER_PATH,
        "21d3b2b254b1ceb9a6cf777b98eb492b52f989cc019afa2209b92be3e4a3cdb0",
    ),
    "single_bolt_scenarios": (
        NDS_SCENARIO_PATH,
        "130041246af11fc8e3568a7091f585d0d75581b2e1fbb3a3f4b97b750d68a7ea",
    ),
    "single_shear_helper": (
        YIELD_HELPER_PATH,
        "d6c318e75c1a720d0b91f810a892e8309ef89735f66f48820ee853b753f8fe45",
    ),
    "dowel_bearing_helper": (
        FE_HELPER_PATH,
        "a1414547d9eaa3d60e81482b4a2cac2d49e88f31aafa341dca5be9ec8ef4aa13",
    ),
}

CANDIDATE = "compact-floor-flush-wood-joints-development"
REVISION = "led-clearance-2x6-runner-seated-blocks-v1"
CASES = ("a1-rear", "a12-rear", "k12-rear")
FACTORS = (0.1, 0.2, 0.3, 0.45, 0.675, 0.925, 1.0)
MODES = ("Im", "Is", "II", "IIIm", "IIIs", "IV")
PERMUTED_MODES = {"Im": "Is", "Is": "Im", "II": "II", "IIIm": "IIIs", "IIIs": "IIIm", "IV": "IV"}
N_PER_LBF = 4.4482216152605
MM_PER_IN = 25.4
GEOMETRY_TOL = 1e-6
VECTOR_TOL = 1e-8
AXIS_PERP_TOL = 1e-8
SIGN_EPSILON = 1e-9

REFERENCE_BASIS = {
    "diameter_in": 0.25,
    "bolt_bending_yield_psi": 45000.0,
    "wood_specific_gravity": 0.5,
    "Fe_parallel_psi": 5600.0,
    "Fe_perpendicular_psi": 4450.0,
    "interface_gap_in": 0.0,
    "shank": "smooth full-diameter quarter-inch scenario through each bearing interval",
}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def close(a: float, b: float, *, rel: float = 1e-10, absolute: float = 1e-8) -> bool:
    return math.isfinite(a) and math.isfinite(b) and math.isclose(
        a, b, rel_tol=rel, abs_tol=absolute
    )


def close_vector(
    actual: list[float], expected: list[float], message: str, *, tolerance: float = VECTOR_TOL
) -> None:
    require(len(actual) == len(expected) == 3, message)
    require(
        all(
            close(float(a), float(b), rel=1e-10, absolute=tolerance)
            for a, b in zip(actual, expected, strict=True)
        ),
        message,
    )


def unit(vector: list[float]) -> list[float]:
    require(len(vector) == 3, "expected a three-vector")
    values = [float(value) for value in vector]
    require(all(math.isfinite(value) for value in values), "nonfinite vector")
    magnitude = math.sqrt(math.fsum(value * value for value in values))
    require(magnitude > 0.0 and math.isfinite(magnitude), "zero or invalid vector")
    return [value / magnitude for value in values]


def dot(a: list[float], b: list[float]) -> float:
    return math.fsum(x * y for x, y in zip(a, b, strict=True))


def norm(vector: list[float]) -> float:
    return math.sqrt(math.fsum(value * value for value in vector))


def angle_to_grain_degrees(force: list[float], grain_axis: list[float]) -> float:
    """Acute angle between a signed lateral vector and an unoriented grain axis."""
    cosine = abs(dot(unit(force), unit(grain_axis)))
    return math.degrees(math.acos(max(-1.0, min(1.0, cosine))))


def load_module(name: str, path: Path, expected_sha: str | None = None):
    if expected_sha is not None:
        require(sha(path) == expected_sha, f"changed pinned source: {path}")
    spec = importlib.util.spec_from_file_location(name, path)
    require(spec is not None and spec.loader is not None, f"cannot import source: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def pin_sources() -> dict[str, dict[str, str]]:
    pins = {}
    for name, (path, expected) in PINS.items():
        require(path.is_file() and sha(path) == expected, f"pinned source changed: {name}")
        pins[name] = {"path": path.relative_to(ROOT).as_posix(), "sha256": expected}
    return pins


def basis_sources() -> tuple[dict[str, Any], Any, Any]:
    properties = json.loads(NDS_SCENARIO_PATH.read_text(encoding="utf-8"))
    inputs = properties.get("inputs", {})
    require(properties.get("mechanical_acceptance") is False, "scenario acceptance boundary changed")
    require(
        inputs.get("diameter_in") == REFERENCE_BASIS["diameter_in"]
        and inputs.get("bolt_bending_yield_psi") == REFERENCE_BASIS["bolt_bending_yield_psi"]
        and inputs.get("wood_specific_gravity_scenario") == REFERENCE_BASIS["wood_specific_gravity"]
        and inputs.get("gap_in") == REFERENCE_BASIS["interface_gap_in"]
        and inputs.get("bearing_basis")
        == "Explicit rounded Fe: parallel 5600 psi, perpendicular 4450 psi"
        and "Full-body smooth" in inputs.get("shank_basis", ""),
        "pinned single-bolt reference assumptions changed",
    )
    nds_source = properties["sources"]["NDS_2024_chapter_12"]
    require(
        nds_source.get("downloaded_pdf_sha256")
        == "5fc837523ff10acc097a162718700a9b4ba64e627d2b0023439146d42fe4ee2a",
        "pinned NDS Chapter 12 PDF identity changed",
    )
    nds_method = load_module(
        "remaining_single_shear_nds_method",
        NDS_PRODUCER_PATH,
        PINS["single_bolt_method"][1],
    )
    fe_helper = load_module(
        "remaining_single_shear_fe_helper",
        FE_HELPER_PATH,
        PINS["dowel_bearing_helper"][1],
    )
    require(
        close(fe_helper.dfl_dowel_bearing_psi(0.25, 0.0), 5600.0)
        and close(fe_helper.dfl_dowel_bearing_psi(0.25, 90.0), 4450.0),
        "pinned bearing helper no longer matches the scenario endpoints",
    )
    return properties, nds_method, fe_helper


def single_shear_reference(
    nds_method: Any,
    *,
    main_length_in: float,
    side_length_in: float,
    main_fe_psi: float,
    side_fe_psi: float,
    theta_degrees: float,
) -> dict[str, Any]:
    result = nds_method.calculate(
        REFERENCE_BASIS["diameter_in"],
        main_length_in,
        side_length_in,
        main_fe_psi,
        side_fe_psi,
        theta_degrees,
    )
    require(
        set(result["reference_values_lbf"]) == set(MODES)
        and set(result["yield_values_lbf"]) == set(MODES),
        "single-shear helper did not return six modes",
    )
    references = {mode: float(result["reference_values_lbf"][mode]) for mode in MODES}
    yields = {mode: float(result["yield_values_lbf"][mode]) for mode in MODES}
    require(
        all(math.isfinite(value) and value > 0.0 for value in (*references.values(), *yields.values())),
        "invalid single-shear result",
    )
    governing = min(references, key=references.get)
    require(result["governing_mode"] == governing, "single-shear governing mode differs")

    diameter = REFERENCE_BASIS["diameter_in"]
    fyb = REFERENCE_BASIS["bolt_bending_yield_psi"]
    k_theta = 1.0 + 0.25 * theta_degrees / 90.0
    ratio_fe = main_fe_psi / side_fe_psi
    direct_iv = (
        diameter**2
        / (3.2 * k_theta)
        * math.sqrt(2.0 * main_fe_psi * fyb / (3.0 * (1.0 + ratio_fe)))
    )
    require(
        close(references["IV"], direct_iv, rel=1e-11, absolute=1e-10),
        "independent single-shear Mode IV check failed",
    )
    return {
        "yield_modes_lbf": yields,
        "unadjusted_reference_modes_lbf": references,
        "unadjusted_reference_modes_N": {
            mode: value * N_PER_LBF for mode, value in references.items()
        },
        "governing_mode": governing,
        "governing_unadjusted_reference_N": references[governing] * N_PER_LBF,
        "independent_mode_IV_lbf": direct_iv,
    }


def load_geometry_and_partition(demand_module: Any, right_module: Any):
    geometry = demand_module.load_method("geometry")
    base, _ = geometry.methods()
    _, model, _, _, geometry_pins = base.checked_inputs()
    connections, primary, upper = geometry.partition(base, model)
    two_receiver = []
    three_receiver = []
    for connection in connections:
        receivers = connection["source_record"]["geometry"]["wood_receiver_intervals"]
        if len(receivers) == 2:
            two_receiver.append(connection)
        elif len(receivers) == 3:
            three_receiver.append(connection)
        else:
            raise ValueError(f"unexpected receiver count for {connection['axis_id']}")
    require(len(connections) == 54 and len(primary) == 6 and len(upper) == 32,
            "primary/upper/remaining partition changed")
    require(len(two_receiver) == 52, "expected exactly 52 two-receiver axes")
    require(
        {row["axis_id"] for row in three_receiver}
        == {"knee_outer_right_side_1", "knee_outer_right_side_2"},
        "only the two continuous right-side axes may remain three-receiver exclusions",
    )
    right_simple = set(right_module.AXES)
    require(
        (right_simple - {"knee_outer_right_side_1", "knee_outer_right_side_2"})
        <= {row["axis_id"] for row in two_receiver},
        "simple right-corner axis was omitted from the two-receiver cohort",
    )
    return geometry_pins, two_receiver, primary, upper


def load_grain_maps() -> dict[str, dict[str, Any]]:
    frame = json.loads(GEOMETRY_MAP_PATH.read_text(encoding="utf-8"))
    blocks = json.loads(BLOCK_MAP_PATH.read_text(encoding="utf-8"))
    require(
        frame.get("geometry_revision_id") == REVISION
        and frame.get("status") == "conditional_source_bound_current_timber_grain_map_geometry_crosschecked"
        and frame.get("release") is not True,
        "frame grain map candidate/revision/status changed",
    )
    require(
        blocks.get("candidate") == CANDIDATE
        and blocks.get("geometry_revision_id") == REVISION
        and blocks.get("status") == "conditional_source_bound_candidate_block_frames_geometry_only"
        and blocks.get("release") is not True,
        "block grain map candidate/revision/status changed",
    )
    return {
        "frame": {row["member_id"]: row for row in frame["members"]},
        "block": {row["part_id"]: row for row in blocks["members"]},
    }


def receiver_basis(
    receiver: dict[str, Any],
    axis: list[float],
    body_geometry: dict[str, Any],
    maps: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    member = receiver["receiver_id"]
    current = receiver["current_shaft_intersection_solid_intervals_from_underhead_mm"]
    long_probe = receiver["intersection_solid_intervals_from_underhead_mm"]
    require(
        len(current) == len(long_probe) == 1
        and len(current[0]) == len(long_probe[0]) == 2,
        f"receiver interval is not one contiguous modeled span: {member}",
    )
    start, end = (float(value) for value in current[0])
    full_start, full_end = (float(value) for value in long_probe[0])
    require(
        all(math.isfinite(value) for value in (start, end, full_start, full_end))
        and start < end
        and abs(start - full_start) <= GEOMETRY_TOL
        and abs(end - full_end) <= GEOMETRY_TOL,
        f"current and source receiver intervals disagree: {member}",
    )
    body = body_geometry[member]
    descriptor = body["geometry_record"]["source_descriptor"]
    map_name = "frame" if descriptor.get("member_kind") == "timber" else "block"
    map_path, map_sha = PINS[f"{map_name}_grain_map"]
    expected_relative = map_path.relative_to(ROOT).as_posix()
    require(
        descriptor.get("material_frame_map") == expected_relative
        and descriptor.get("material_frame_map_sha256") == map_sha,
        f"model grain descriptor is not bound to pinned map: {member}",
    )
    map_row = maps[map_name].get(member)
    require(map_row is not None, f"grain map lacks source receiver: {member}")
    assignment = map_row["conditional_grain_assignment"]
    map_vector = (
        assignment["proposed_global_xyz"] if map_name == "frame"
        else assignment["grain_direction_global_xyz"]
    )
    model_grain = unit(descriptor["grain_global_xyz"])
    mapped_grain = unit(map_vector)
    alignment = dot(model_grain, mapped_grain)
    require(abs(abs(alignment) - 1.0) <= 1e-8, f"model/map grain axes disagree: {member}")
    require(
        descriptor.get("member_id") == member
        and body["geometry_record"].get("name") == member,
        f"source descriptor member identity differs: {member}",
    )
    return {
        "receiver_id": member,
        "modeled_bearing_length_mm": end - start,
        "modeled_bearing_length_in": (end - start) / MM_PER_IN,
        "modeled_interval_from_underhead_mm": [start, end],
        "bolt_axis_unit_global_xyz": unit(axis),
        "source_descriptor_grain_axis_unit_global_xyz": model_grain,
        "pinned_map_grain_axis_unit_global_xyz": mapped_grain,
        "source_descriptor_map_alignment_dot": alignment,
        "grain_assignment_observed": False,
        "grain_map": {
            "path": expected_relative,
            "sha256": map_sha,
            "member_kind": descriptor["member_kind"],
        },
    }


def axis_basis(
    connection: dict[str, Any],
    body_geometry: dict[str, Any],
    maps: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    source_geometry = connection["source_record"]["geometry"]
    receivers = source_geometry["wood_receiver_intervals"]
    axis = unit(source_geometry["axis_head_to_nut_global"])
    receiver_rows = [receiver_basis(row, axis, body_geometry, maps) for row in receivers]
    starts = [row["modeled_interval_from_underhead_mm"][0] for row in receiver_rows]
    require(starts == sorted(starts), f"receiver order is not underhead-to-tip: {connection['axis_id']}")
    require(
        abs(receiver_rows[0]["modeled_interval_from_underhead_mm"][1]
            - receiver_rows[1]["modeled_interval_from_underhead_mm"][0]) <= GEOMETRY_TOL,
        f"two receiver intervals do not meet: {connection['axis_id']}",
    )
    require(
        all(abs(dot(axis, row["bolt_axis_unit_global_xyz"])) >= 1.0 - 1e-10
            for row in receiver_rows),
        f"receiver bolt axis changed: {connection['axis_id']}",
    )
    axis_grain_dots = [
        abs(dot(axis, row["source_descriptor_grain_axis_unit_global_xyz"]))
        for row in receiver_rows
    ]
    exclusion = applicability_exclusion(axis, receiver_rows)
    return {
        "axis_id": connection["axis_id"],
        "receiver_ids_underhead_to_tip": [row["receiver_id"] for row in receiver_rows],
        "modeled_bolt_axis_unit_global_xyz": axis,
        "modeled_shaft_diameter_mm": float(source_geometry["modeled_shaft_diameter_mm"]),
        "receivers": receiver_rows,
        "absolute_bolt_axis_grain_dots": axis_grain_dots,
        "single_shear_applicability_exclusion": exclusion,
        "interval_length_interpretation": "CAD/source modeled current-shaft intersection; not measured stock or a capacity length",
    }


def applicability_exclusion(axis: list[float], receivers: list[dict[str, Any]]) -> str | None:
    dots = [
        abs(dot(unit(axis), unit(row["source_descriptor_grain_axis_unit_global_xyz"])))
        for row in receivers
    ]
    if any(value >= 1.0 - AXIS_PERP_TOL for value in dots):
        return "EXCLUDED_END_GRAIN_APPLICABILITY_UNESTABLISHED"
    if any(value > AXIS_PERP_TOL for value in dots):
        return "EXCLUDED_BOLT_AXIS_NOT_PERPENDICULAR_TO_ALL_GRAINS"
    return None


def make_reference_assignments(
    nds_method: Any,
    fe_helper: Any,
    axis: dict[str, Any],
    forces_by_receiver: dict[str, list[float]],
) -> dict[str, Any]:
    receiver_rows = axis["receivers"]
    assignments = []
    for main_index, side_index in ((0, 1), (1, 0)):
        main = receiver_rows[main_index]
        side = receiver_rows[side_index]
        main_force = forces_by_receiver[main["receiver_id"]]
        side_force = forces_by_receiver[side["receiver_id"]]
        main_angle = angle_to_grain_degrees(
            main_force, main["source_descriptor_grain_axis_unit_global_xyz"]
        )
        side_angle = angle_to_grain_degrees(
            side_force, side["source_descriptor_grain_axis_unit_global_xyz"]
        )
        theta = max(main_angle, side_angle)
        main_fe = float(fe_helper.dfl_dowel_bearing_psi(0.25, main_angle))
        side_fe = float(fe_helper.dfl_dowel_bearing_psi(0.25, side_angle))
        ref = single_shear_reference(
            nds_method,
            main_length_in=main["modeled_bearing_length_in"],
            side_length_in=side["modeled_bearing_length_in"],
            main_fe_psi=main_fe,
            side_fe_psi=side_fe,
            theta_degrees=theta,
        )
        assignments.append({
            "assignment": "receiver_0_as_main" if main_index == 0 else "receiver_1_as_main",
            "main_receiver": main["receiver_id"],
            "side_receiver": side["receiver_id"],
            "main_actual_lateral_angle_to_grain_deg": main_angle,
            "side_actual_lateral_angle_to_grain_deg": side_angle,
            "max_angle_theta_deg": theta,
            "main_Fe_psi": main_fe,
            "side_Fe_psi": side_fe,
            **ref,
        })
    by_name = {row["assignment"]: row for row in assignments}
    first = by_name["receiver_0_as_main"]
    second = by_name["receiver_1_as_main"]
    for mode in MODES:
        swapped = PERMUTED_MODES[mode]
        require(
            close(first["unadjusted_reference_modes_lbf"][mode],
                  second["unadjusted_reference_modes_lbf"][swapped])
            and close(first["yield_modes_lbf"][mode], second["yield_modes_lbf"][swapped]),
            f"single-shear main/side permutation closure failed for {mode}",
        )
    require(
        close(first["governing_unadjusted_reference_N"],
              second["governing_unadjusted_reference_N"]),
        "single-shear governing reference changed under receiver-role permutation",
    )
    differences = {
        "reference_modes_lbf_receiver_0_main_minus_receiver_1_main": {
            mode: first["unadjusted_reference_modes_lbf"][mode]
            - second["unadjusted_reference_modes_lbf"][mode]
            for mode in MODES
        },
        "governing_reference_N_receiver_0_main_minus_receiver_1_main": (
            first["governing_unadjusted_reference_N"]
            - second["governing_unadjusted_reference_N"]
        ),
        "governing_mode_receiver_0_main": first["governing_mode"],
        "governing_mode_receiver_1_main": second["governing_mode"],
        "permutation_mode_map_closure_passed": True,
    }
    return {"scenarios": assignments, "assignment_difference": differences}


def state_reference_fields(
    nds_method: Any,
    fe_helper: Any,
    axis: dict[str, Any],
    forces_by_receiver: dict[str, list[float]],
) -> tuple[str | None, dict[str, Any] | None, dict[str, float] | None,
           dict[str, float] | None]:
    lateral_resultant = norm(next(iter(forces_by_receiver.values())))
    angles = None
    if lateral_resultant > SIGN_EPSILON:
        angles = {
            receiver["receiver_id"]: angle_to_grain_degrees(
                forces_by_receiver[receiver["receiver_id"]],
                receiver["source_descriptor_grain_axis_unit_global_xyz"],
            )
            for receiver in axis["receivers"]
        }
    exclusion = axis["single_shear_applicability_exclusion"]
    if exclusion is not None:
        return exclusion, None, None, angles
    if lateral_resultant <= SIGN_EPSILON:
        return "EXCLUDED_ZERO_LATERAL_RESULTANT_DIRECTION_UNDEFINED", None, None, angles
    assignments = make_reference_assignments(nds_method, fe_helper, axis, forces_by_receiver)
    ratios = {
        row["assignment"]: lateral_resultant / row["governing_unadjusted_reference_N"]
        for row in assignments["scenarios"]
    }
    for row in assignments["scenarios"]:
        row["actual_resultant_to_governing_reference"] = ratios[row["assignment"]]
    assignments["demand_to_reference_ratios_unadjusted_only"] = ratios
    return None, assignments, ratios, angles


def produce(support_report: Path) -> dict[str, Any]:
    pins = pin_sources()
    demand = load_module(
        "remaining_single_shear_demand_source",
        DEMAND_PATH,
        PINS["remaining_demand_producer"][1],
    )
    right = load_module(
        "remaining_single_shear_right_plane_source",
        RIGHT_PATH,
        PINS["right_plane_checker"][1],
    )
    _, nds_method, fe_helper = basis_sources()
    properties = json.loads(NDS_SCENARIO_PATH.read_text(encoding="utf-8"))
    require(
        properties["inputs"]["diameter_in"] == REFERENCE_BASIS["diameter_in"]
        and properties["inputs"]["bolt_bending_yield_psi"] == REFERENCE_BASIS["bolt_bending_yield_psi"]
        and properties["inputs"]["wood_specific_gravity_scenario"] == REFERENCE_BASIS["wood_specific_gravity"],
        "single-shear reference basis differs from pinned source properties",
    )
    demand_result = demand.produce(support_report)
    require(
        demand_result["producer_sha256"] == PINS["remaining_demand_producer"][1]
        and demand_result["status"] == "PASS_THREE_CASE_SIGNED_TIE_JOIN_ONLY"
        and demand_result["counts"] == {
            "axes": 54, "cases": 3, "increments_per_case": 7,
            "tie_states": 1134, "seat_states": 2268,
        },
        "remaining-54 accepted tie join changed",
    )
    geometry_pins, selected, primary, upper = load_geometry_and_partition(demand, right)
    maps = load_grain_maps()
    axis_ids = {connection["axis_id"] for connection in selected}
    axis_metadata: dict[str, dict[str, Any]] = {}
    for case_pin in demand_result["source_cases"].values():
        native = json.loads((ROOT / case_pin["model"]["path"]).read_text(encoding="utf-8"))
        for connection in selected:
            basis = axis_basis(connection, native["body_geometry"], maps)
            prior = axis_metadata.setdefault(connection["axis_id"], basis)
            require(prior == basis, "receiver geometry/grain metadata changed across source cases")
    require(len(axis_metadata) == 52, "incomplete axis grain/interval records")

    tie_rows = {
        (row["case_id"], int(row["increment_index"]), row["axis_id"]): row
        for row in demand_result["tie_states"] if row["axis_id"] in axis_ids
    }
    require(len(tie_rows) == 1092, "incomplete same-state tie join for two-receiver cohort")

    state_rows = []
    plane_checks = 0
    excluded_state_rows = 0
    cases = demand_result["source_cases"]
    require(set(cases) == set(CASES), "three-case source identity changed")
    for case in CASES:
        source = cases[case]
        native = json.loads((ROOT / source["model"]["path"]).read_text(encoding="utf-8"))
        response = json.loads((ROOT / source["response"]["path"]).read_text(encoding="utf-8"))
        springs = {row["source_row_id"]: row for row in native["springs"]}
        inventory = native["raw_source_carrier_law_inventory_rows"]
        require(len(springs) == len(native["springs"]), "duplicate native spring identity")
        require(
            response["case_id"] == case
            and response["candidate"] == CANDIDATE
            and response["geometry_revision_id"] == REVISION
            and len(response["increments"]) == len(FACTORS),
            f"native response identity or state coverage changed: {case}",
        )
        for index, increment in enumerate(response["increments"]):
            require(increment["load_factor"] == FACTORS[index], "source load-factor order changed")
            components = {
                row["source_row_id"]: row
                for row in increment["retained_bilateral_spring2_components"]
            }
            require(
                len(components) == len(increment["retained_bilateral_spring2_components"]),
                "duplicate lateral source-component identity",
            )
            plane_by_axis: dict[str, tuple[str, dict[str, Any]]] = {}
            for name, action in increment["physical_connection_forces"].items():
                if (action.get("role") == "candidate_bolt_lateral_plane"
                        and action.get("axis_id") in axis_ids):
                    require(action["axis_id"] not in plane_by_axis, "duplicate lateral plane for axis/state")
                    plane_by_axis[action["axis_id"]] = (name, action)
            require(set(plane_by_axis) == axis_ids, "missing lateral plane for axis/state")

            for axis_id in sorted(axis_ids):
                connection = next(row for row in selected if row["axis_id"] == axis_id)
                basis = axis_metadata[axis_id]
                receiver_ids = basis["receiver_ids_underhead_to_tip"]
                name, action = plane_by_axis[axis_id]
                expected_owner = springs[action["source_row_ids"][0]]["physical_owner"]
                force_on_first, force_radius = right.checked_plane(
                    action, springs, components, inventory, expected_owner
                )
                plane_checks += 1
                require(
                    [action["first"], action["second"]] == receiver_ids,
                    f"plane receiver order differs from geometry: {axis_id}",
                )
                require(
                    name.startswith(axis_id + "/plane-")
                    and all(row["source_connection_name"] == name
                            for row in action["source_inventory_rows"]),
                    f"plane map key and source inventory name differ: {axis_id}",
                )
                close_vector(action["axis"], basis["modeled_bolt_axis_unit_global_xyz"],
                             f"plane bolt axis differs from geometry: {axis_id}")

                source_geometry = connection["source_record"]["geometry"]
                spans = [row["modeled_interval_from_underhead_mm"] for row in basis["receivers"]]
                seam = spans[0][1]
                require(abs(seam - spans[1][0]) <= GEOMETRY_TOL, "receiver seam is not continuous")
                origin = [
                    float(source_geometry["shaft_center_global_xyz_mm"][k])
                    - basis["modeled_bolt_axis_unit_global_xyz"][k]
                    * float(source_geometry["modeled_underhead_to_tip_mm"]) / 2.0
                    for k in range(3)
                ]
                expected_point = [
                    origin[k] + seam * basis["modeled_bolt_axis_unit_global_xyz"][k]
                    for k in range(3)
                ]
                close_vector(action["point"], expected_point,
                             f"lateral plane datum differs from joined receiver seam: {axis_id}",
                             tolerance=GEOMETRY_TOL)
                forces_by_receiver = {
                    receiver_ids[0]: [float(value) for value in force_on_first],
                    receiver_ids[1]: [-float(value) for value in force_on_first],
                }
                lateral_resultant = norm(force_on_first)
                exclusion, assignments, ratio, angles = state_reference_fields(
                    nds_method, fe_helper, basis, forces_by_receiver
                )
                tie = tie_rows[(case, index, axis_id)]
                demand_tie = float(tie["signed_tie_N"])
                require(math.isfinite(demand_tie) and demand_tie >= -SIGN_EPSILON,
                        f"invalid signed outer tie: {case}/{axis_id}/{index}")
                require(
                    tie["source_tie"]["role"] == "physical_bolt_outer_seat_tension",
                    "wrong same-state physical tie source",
                )

                if exclusion is not None:
                    excluded_state_rows += 1

                state_rows.append({
                    "case_id": case,
                    "increment_index": index,
                    "load_factor": increment["load_factor"],
                    "axis_id": axis_id,
                    "lateral_plane_source_name": name,
                    "lateral_plane_source_row_ids": list(action["source_row_ids"]),
                    "lateral_plane_point_xyz_mm": list(action["point"]),
                    "actual_lateral_force_on_receiver_0_N": forces_by_receiver[receiver_ids[0]],
                    "actual_lateral_force_on_receiver_1_N": forces_by_receiver[receiver_ids[1]],
                    "actual_lateral_force_rounding_radius_N": force_radius,
                    "actual_lateral_resultant_N": lateral_resultant,
                    "actual_lateral_angle_to_grain_deg_by_receiver": angles,
                    "same_state_signed_outer_tie_N_once": demand_tie,
                    "same_state_tie_source_row_ids": tie["source_tie"]["source_row_ids"],
                    "single_shear_reference_exclusion": exclusion,
                    "single_shear_reference_assignments": assignments,
                    "demand_to_reference_ratios_unadjusted_only": ratio,
                    "joint_accepted": False,
                })

    require(plane_checks == 1092 and len(state_rows) == 1092,
            "not all 52×21 source plane states were reconstructed")
    expected_excluded_axes = {
        "center_post_header_left_1", "center_post_header_left_2",
        "center_post_header_right_1", "center_post_header_right_2",
        "center_principal_header_left_1", "center_principal_header_left_2",
        "center_principal_header_right_1", "center_principal_header_right_2",
        "knee_outer_right_inner_header_1", "knee_outer_right_inner_header_2",
    }
    excluded_axes = {
        axis_id for axis_id, basis in axis_metadata.items()
        if basis["single_shear_applicability_exclusion"] is not None
    }
    require(excluded_axes == expected_excluded_axes,
            "end-grain/bolt-axis applicability exclusion set changed")
    require(excluded_state_rows == 210,
            "expected exactly ten named non-side-grain axes across 21 states")
    state_rows.sort(key=lambda row: (CASES.index(row["case_id"]), row["increment_index"], row["axis_id"]))
    return {
        "schema": "remaining_candidate_single_shear_reference/v1",
        "status": "PASS_SOURCE_BOUND_UNADJUSTED_REFERENCE_ARITHMETIC_ONLY",
        "producer_sha256": sha(Path(__file__)),
        "candidate": CANDIDATE,
        "geometry_revision_id": REVISION,
        "reference_basis": {
            **REFERENCE_BASIS,
            "bearing_lengths": "individual CAD/source current-shaft receiver intervals; both main/side assignments are scenario comparisons",
            "Fe_method": "pinned mini_moonboard.bolted_timber_checks.dfl_dowel_bearing_psi at actual signed-plane resultant angle to each proposed grain axis",
            "single_shear_method": "pinned fea.dowel_yield.single_shear via the pinned NDS scenario producer; all six TR12 reference modes",
            "yield_reduction_terms": {"Im": 4, "Is": 4, "II": 3.6, "IIIm": 3.2, "IIIs": 3.2, "IV": 3.2},
            "theta_reduction": "Ktheta = 1 + 0.25 * max(receiver load-to-grain angles) / 90 degrees",
            "angle_and_bearing_scope": "D=1/4 inch, SG=0.50 rounded Fe endpoints; source-matched conditional scenario, not adopted property or material inspection",
            "end_grain_scope": "End-grain-axis rows are excluded from this reused side-grain single-shear reference; potentially applicable end-grain provisions are not assessed or adopted here.",
            "external_NDS_source": properties["sources"]["NDS_2024_chapter_12"],
            "actual_hardware_or_stock_observed": False,
        },
        "source_acceptance": {
            "remaining_demand_status": demand_result["status"],
            "remaining_demand_producer_sha256": demand_result["producer_sha256"],
            "three_case_freeze_sha256": demand_result["freeze_sha256"],
            "source_cases": demand_result["source_cases"],
            "accepted_tie_states_source_checked": 1134,
            "retained_bilateral_planes_checked": plane_checks,
            "primary_axes_excluded": primary,
            "upper_axes_excluded": upper,
            "continuous_right_side_axes_excluded": [
                "knee_outer_right_side_1", "knee_outer_right_side_2"
            ],
        },
        "source_sha256": pins,
        "geometry_input_pins": geometry_pins,
        "counts": {
            "remaining_candidate_axes": 54,
            "two_receiver_axes": 52,
            "three_receiver_excluded_axes": 2,
            "source_cases": 3,
            "increments_per_case": 7,
            "same_state_bolt_rows": len(state_rows),
            "same_state_lateral_planes_checked": plane_checks,
            "end_grain_or_axis_orientation_excluded_axes": len(excluded_axes),
            "end_grain_or_axis_orientation_excluded_state_rows": excluded_state_rows,
            "rows_with_unadjusted_references": len(state_rows) - excluded_state_rows,
        },
        "axis_geometry_and_grain": axis_metadata,
        "state_rows": state_rows,
        "claim_limits": {
            "joint_accepted": False,
            "adopted_capacity": False,
            "complete_joint": False,
            "adjustments_applied": False,
            "Ceg_applied": False,
            "Cg_applied": False,
            "end_grain_reference_computed": False,
            "end_grain_method_assessed": False,
            "same_state_tie_added_to_lateral_demand": False,
            "six_case_envelope_established": False,
            "stiffness_established": False,
            "splitting_or_tearout_qualified": False,
            "stock_or_hardware_inspected": False,
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--support-report", required=True, type=Path)
    args = parser.parse_args()
    print(json.dumps(produce(args.support_report), indent=2, allow_nan=False))


if __name__ == "__main__":
    main()
