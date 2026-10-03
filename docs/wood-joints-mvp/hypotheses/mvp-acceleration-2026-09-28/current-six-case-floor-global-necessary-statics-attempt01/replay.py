#!/usr/bin/env python3
"""Replay a source-pinned, normal-only whole-frame floor feasibility screen."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[5]
PACKET = Path(__file__).resolve().parent
BASE = Path("docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28")
PINS_PATH = PACKET / "source-pins.json"
OUTPUT = PACKET / "screen.json"
EXPECTED_PINS_SHA256 = "c2a99b84a2e98dbd69d1819e6193b56e81a70b1bcaee447be6be71f291d892bb"
EXPECTED_CASES = ["a12-rear", "a12-forward", "a12-left", "k12-right", "k12-rear", "a1-rear"]
FORCE_GUARD_N = 1.0e-8
MOMENT_GUARD_NMM = 1.0e-6
PLANE_GUARD_MM = 1.0e-9
NORMAL_GUARD = 1.0e-12
HULL_BOUNDARY_GUARD_MM = 1.0e-6


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")


def assert_close(actual: list[float], expected: list[float], guard: float, label: str) -> float:
    if len(actual) != len(expected):
        raise AssertionError(f"{label}: vector lengths differ")
    residual = max(
        (abs(float(a) - float(b)) for a, b in zip(actual, expected, strict=True)),
        default=0.0,
    )
    if residual > guard:
        raise AssertionError(f"{label}: max residual {residual:.17g} exceeds {guard:.17g}")
    return residual


def sum_vectors(rows: list[list[float]]) -> list[float]:
    return [sum(float(row[axis]) for row in rows) for axis in range(3)]


def cross(a: list[float], b: list[float]) -> list[float]:
    return [
        a[1] * b[2] - a[2] * b[1],
        a[2] * b[0] - a[0] * b[2],
        a[0] * b[1] - a[1] * b[0],
    ]


def source_path(case_id: str) -> Path:
    case_dir = (
        BASE / "current-springa-frame-input-adapter-attempt01" / case_id
        if case_id == "a12-rear"
        else BASE / "current-springa-six-case-frame-input-adapter-attempt01" / case_id
    )
    return case_dir / "model.json"


def load_pins() -> tuple[dict[str, Any], dict[str, str]]:
    observed_pins_sha = sha256_file(PINS_PATH)
    if observed_pins_sha != EXPECTED_PINS_SHA256:
        raise ValueError(f"source-pins.json changed: {observed_pins_sha} != {EXPECTED_PINS_SHA256}")
    pins = json.loads(PINS_PATH.read_text(encoding="utf-8"))
    if pins.get("schema") != "current_six_case_floor_global_necessary_statics_source_pins/v1":
        raise ValueError("unexpected source-pins schema")
    observed: dict[str, str] = {}
    for row in pins.get("files", []):
        path = str(row["path"])
        live = ROOT / path
        digest = sha256_file(live)
        if digest != row["sha256"]:
            raise ValueError(f"pinned source changed: {path}: {digest} != {row['sha256']}")
        observed[path] = digest
    if len(observed) != len(pins.get("files", [])):
        raise ValueError("duplicate source paths in source-pins.json")
    return pins, observed


def convex_hull(points: list[tuple[float, float]]) -> list[tuple[float, float]]:
    """Monotone-chain CCW hull, retaining only the extreme vertices."""
    unique = sorted(set((float(x), float(y)) for x, y in points))
    if len(unique) < 3:
        raise ValueError("floor footprint has fewer than three unique XY points")

    def turn(origin: tuple[float, float], a: tuple[float, float], b: tuple[float, float]) -> float:
        return (a[0] - origin[0]) * (b[1] - origin[1]) - (a[1] - origin[1]) * (b[0] - origin[0])

    lower: list[tuple[float, float]] = []
    for point in unique:
        while len(lower) >= 2 and turn(lower[-2], lower[-1], point) <= 0.0:
            lower.pop()
        lower.append(point)
    upper: list[tuple[float, float]] = []
    for point in reversed(unique):
        while len(upper) >= 2 and turn(upper[-2], upper[-1], point) <= 0.0:
            upper.pop()
        upper.append(point)
    result = lower[:-1] + upper[:-1]
    if len(result) < 3:
        raise ValueError("floor footprint points are collinear")
    signed_area2 = sum(
        result[i][0] * result[(i + 1) % len(result)][1]
        - result[(i + 1) % len(result)][0] * result[i][1]
        for i in range(len(result))
    )
    if signed_area2 <= 0.0:
        raise ValueError("floor footprint hull is not counter-clockwise")
    return result


def edge_signed_distances(
    point: tuple[float, float], hull: list[tuple[float, float]]
) -> list[float]:
    distances: list[float] = []
    for index, start in enumerate(hull):
        end = hull[(index + 1) % len(hull)]
        dx = end[0] - start[0]
        dy = end[1] - start[1]
        length = math.hypot(dx, dy)
        cross_value = dx * (point[1] - start[1]) - dy * (point[0] - start[0])
        distances.append(cross_value / length)
    return distances


def classify_hull_point(point: tuple[float, float], hull: list[tuple[float, float]]) -> dict[str, Any]:
    distances = edge_signed_distances(point, hull)
    minimum = min(distances)
    if minimum > HULL_BOUNDARY_GUARD_MM:
        status = "inside"
    elif minimum >= -HULL_BOUNDARY_GUARD_MM:
        status = "boundary"
    else:
        status = "outside"
    return {
        "status": status,
        "signed_distances_to_hull_supporting_edges_mm": distances,
        "minimum_signed_hull_edge_distance_mm": minimum,
        "limiting_edge_index": distances.index(minimum),
    }


def run_rectangle_oracle() -> dict[str, Any]:
    hull = convex_hull([(0.0, 0.0), (10.0, 0.0), (10.0, 5.0), (0.0, 5.0)])
    cases = [
        {"name": "inside", "point_xy_mm": [5.0, 2.5], "expected_status": "inside", "expected_margin_mm": 2.5},
        {"name": "boundary", "point_xy_mm": [10.0, 2.5], "expected_status": "boundary", "expected_margin_mm": 0.0},
        {"name": "outside", "point_xy_mm": [10.1, 2.5], "expected_status": "outside", "expected_margin_mm": -0.1},
    ]
    for row in cases:
        result = classify_hull_point(tuple(row["point_xy_mm"]), hull)
        if result["status"] != row["expected_status"]:
            raise AssertionError(f"rectangle oracle {row['name']}: wrong classification {result['status']}")
        if not math.isclose(
            result["minimum_signed_hull_edge_distance_mm"],
            row["expected_margin_mm"],
            rel_tol=0.0,
            abs_tol=1.0e-12,
        ):
            raise AssertionError(f"rectangle oracle {row['name']}: wrong signed margin")
        row["observed_status"] = result["status"]
        row["observed_margin_mm"] = result["minimum_signed_hull_edge_distance_mm"]
    return {
        "status": "PASS_RECTANGULAR_FOOTPRINT_INSIDE_OUTSIDE_BOUNDARY_ORACLE",
        "rectangle_vertices_ccw_xy_mm": [[x, y] for x, y in hull],
        "cases": cases,
    }


def validate_floor_geometry(models: dict[str, dict[str, Any]]) -> tuple[list[dict[str, Any]], list[tuple[float, float]]]:
    canonical_rows: list[dict[str, Any]] | None = None
    base_node_points: set[tuple[float, float, float]] | None = None
    for case_id in EXPECTED_CASES:
        model = models[case_id]
        cells = [row for row in model["contact_cell_ownership"] if row.get("kind") == "floor_normal"]
        if len(cells) != 100:
            raise ValueError(f"{case_id}: expected 100 physical floor normal cells, found {len(cells)}")
        if len({row["name"] for row in cells}) != 100:
            raise ValueError(f"{case_id}: duplicate physical floor normal cell names")
        cells_by_name = {str(row["name"]): row for row in cells}
        normalized = []
        for name, row in sorted(cells_by_name.items()):
            point = [float(value) for value in row["point_xyz_mm"]]
            normal = [float(value) for value in row["normal_xyz"]]
            if len(point) != 3 or len(normal) != 3:
                raise ValueError(f"{case_id}/{name}: floor point or normal is not a 3-vector")
            normal_length = math.sqrt(sum(value * value for value in normal))
            if abs(normal_length - 1.0) > NORMAL_GUARD or normal[2] <= 0.0:
                raise ValueError(f"{case_id}/{name}: floor normal is not unit length and upward")
            if abs(normal[0]) > NORMAL_GUARD or abs(normal[1]) > NORMAL_GUARD or abs(normal[2] - 1.0) > NORMAL_GUARD:
                raise ValueError(f"{case_id}/{name}: source normal is not the required global +Z direction")
            if not all(math.isfinite(value) for value in point + normal):
                raise ValueError(f"{case_id}/{name}: non-finite floor geometry")
            normalized.append(
                {
                    "name": name,
                    "point_xyz_mm": point,
                    "normal_xyz": normal,
                    "source_area_mm2": float(row["area_mm2"]),
                    "source_floor_patch_index": int(row["source_floor_patch_index"]),
                }
            )
        zs = [row["point_xyz_mm"][2] for row in normalized]
        if max(zs) - min(zs) > PLANE_GUARD_MM or max(abs(z) for z in zs) > PLANE_GUARD_MM:
            raise ValueError(f"{case_id}: source support points are not coplanar at global Z=0")

        normal_bindings = [
            row
            for row in model["nonlinear_native_carrier_bindings"]
            if row.get("physical_owner", {}).get("role") == "floor_normal"
        ]
        if len(normal_bindings) != 100 or len({row["name"] for row in normal_bindings}) != 100:
            raise ValueError(f"{case_id}: expected 100 unique source unilateral normal bindings")
        bindings_by_name = {str(row["name"]): row for row in normal_bindings}
        if set(bindings_by_name) != set(cells_by_name):
            raise ValueError(f"{case_id}: floor cell geometry and normal-binding names differ")
        for name, cell in cells_by_name.items():
            binding = bindings_by_name[name]
            owner = binding["physical_owner"]
            if owner.get("second") != "floor" or binding.get("force_law") != "k * max(q_mm, 0)":
                raise ValueError(f"{case_id}/{name}: source binding is not the expected unilateral floor normal")
            if owner.get("point") != cell["point_xyz_mm"] or owner.get("scalar_normal") != cell["normal_xyz"]:
                raise ValueError(f"{case_id}/{name}: carrier binding disagrees with physical contact ownership")
            if binding.get("numerical_axis_global_xyz") != cell["normal_xyz"]:
                raise ValueError(f"{case_id}/{name}: numerical carrier axis disagrees with physical normal")

        support_nodes = model["floor_support_nodes"]
        if len(support_nodes) != 100 or len(set(support_nodes)) != 100:
            raise ValueError(f"{case_id}: expected 100 unique floor support nodes")
        support_points = {tuple(float(v) for v in model["nodes"][str(int(node))]) for node in support_nodes}
        cell_points = {tuple(row["point_xyz_mm"]) for row in normalized}
        if support_points != cell_points:
            raise ValueError(f"{case_id}: support nodes do not exactly match physical floor points")

        signature = [
            {
                "name": row["name"],
                "point_xyz_mm": row["point_xyz_mm"],
                "normal_xyz": row["normal_xyz"],
                "source_area_mm2": row["source_area_mm2"],
                "source_floor_patch_index": row["source_floor_patch_index"],
            }
            for row in normalized
        ]
        if canonical_rows is None:
            canonical_rows = signature
            base_node_points = support_points
        elif signature != canonical_rows or support_points != base_node_points:
            raise ValueError(f"{case_id}: floor geometry differs from the other source load cases")

    assert canonical_rows is not None
    hull = convex_hull([(row["point_xyz_mm"][0], row["point_xyz_mm"][1]) for row in canonical_rows])
    return canonical_rows, hull


def nodal_wrench(model: dict[str, Any]) -> tuple[list[float], list[float]]:
    force = [0.0, 0.0, 0.0]
    moment = [0.0, 0.0, 0.0]
    nodes = model["nodes"]
    loads = model["physical_external_loads"]
    for node in sorted(loads, key=lambda value: int(value)):
        applied = [float(value) for value in loads[node]]
        xyz = [float(value) for value in nodes[str(int(node))]]
        applied_moment = cross(xyz, applied)
        for axis in range(3):
            force[axis] += applied[axis]
            moment[axis] += applied_moment[axis]
    return force, moment


def build_report() -> dict[str, Any]:
    pins, observed_pin_hashes = load_pins()
    pin_map = {row["path"]: row["sha256"] for row in pins["files"]}
    upstream_pins_path = BASE / "current-gravity-settle-climber-ramp-scenario-attempt01" / "source-pins.json"
    upstream_pins = json.loads((ROOT / upstream_pins_path).read_text(encoding="utf-8"))
    upstream_pin_map = {row["path"]: row["sha256"] for row in upstream_pins["files"]}

    register_path = BASE / "current-six-case-source-load-register-attempt01" / "register.json"
    decomposition_path = BASE / "current-gravity-settle-climber-ramp-scenario-attempt01" / "decomposition.json"
    register_sha = observed_pin_hashes[register_path.as_posix()]
    decomposition_sha = observed_pin_hashes[decomposition_path.as_posix()]
    upstream_pins_sha = observed_pin_hashes[upstream_pins_path.as_posix()]
    register = json.loads((ROOT / register_path).read_text(encoding="utf-8"))
    decomposition = json.loads((ROOT / decomposition_path).read_text(encoding="utf-8"))
    register_cases = {row["case_id"]: row for row in register["cases"]}
    decomposition_cases = {row["case_id"]: row for row in decomposition["cases"]}

    if register.get("status") != "PASS_FRESH_SIX_CASE_SOURCE_LOAD_WRENCH_REGISTER":
        raise ValueError("source load register status is not the expected input-only pass")
    if register.get("same_nonload_signature_across_all_six_cases") is not True:
        raise ValueError("source register does not confirm common non-load model signature")
    if register.get("case_id_order") != EXPECTED_CASES or list(register_cases) != EXPECTED_CASES:
        raise ValueError("source register case order changed")
    if decomposition.get("status") != "PASS_SIX_CASE_SOURCE_LOAD_DECOMPOSITION_AND_EXACT_RECOMPOSITION":
        raise ValueError("validated gravity/climber decomposition status changed")
    if decomposition.get("source_pins_sha256") != upstream_pins_sha:
        raise ValueError("decomposition no longer binds the pinned source inventory")
    if decomposition.get("source_load_register_sha256") != register_sha:
        raise ValueError("decomposition no longer binds the source load register")
    if decomposition.get("source_case_ids") != EXPECTED_CASES or list(decomposition_cases) != EXPECTED_CASES:
        raise ValueError("decomposition case order changed")

    models: dict[str, dict[str, Any]] = {}
    model_paths: dict[str, str] = {}
    for case_id in EXPECTED_CASES:
        path = source_path(case_id)
        path_text = path.as_posix()
        if path_text not in pin_map or path_text not in upstream_pin_map:
            raise ValueError(f"{case_id}: load-only model is not pinned by both source inventories")
        if pin_map[path_text] != upstream_pin_map[path_text]:
            raise ValueError(f"{case_id}: local and upstream model pins differ")
        model = json.loads((ROOT / path).read_text(encoding="utf-8"))
        if model.get("case_id") != case_id:
            raise ValueError(f"{case_id}: input model case ID mismatch")
        if model.get("geometry_revision_id") != "led-clearance-2x6-runner-seated-blocks-v1":
            raise ValueError(f"{case_id}: geometry revision mismatch")
        if model.get("candidate") != "compact-floor-flush-wood-joints-development":
            raise ValueError(f"{case_id}: candidate mismatch")
        if model.get("input_only") is not True or model.get("native_solve_executed") is not False:
            raise ValueError(f"{case_id}: input model is not explicitly load-only")
        if model.get("source_model_pin", {}).get("rejected_response_forces_read") is not False:
            raise ValueError(f"{case_id}: source model does not explicitly exclude rejected response forces")
        if model.get("source_model_pin", {}).get("historical_active_states_reused") is not False:
            raise ValueError(f"{case_id}: source model reused a historical active state")
        if model.get("source_load_emission_audit", {}).get("historical_response_forces_read") is not False:
            raise ValueError(f"{case_id}: source load emission audit does not exclude response forces")
        if model.get("source_model_inputs_sha256") != register_cases[case_id].get("source_model_inputs_sha256"):
            raise ValueError(f"{case_id}: model input signature differs from the source register")
        if model.get("source_sha256") != register_cases[case_id].get("source_sha256"):
            raise ValueError(f"{case_id}: model source hash inventory differs from the source register")
        if decomposition_cases[case_id].get("historical_response_forces_read") is not False:
            raise ValueError(f"{case_id}: validated decomposition includes response forces")
        models[case_id] = model
        model_paths[case_id] = path_text

    floor_points, hull = validate_floor_geometry(models)
    oracle = run_rectangle_oracle()
    hull_area = 0.5 * sum(
        hull[i][0] * hull[(i + 1) % len(hull)][1]
        - hull[(i + 1) % len(hull)][0] * hull[i][1]
        for i in range(len(hull))
    )

    case_results: list[dict[str, Any]] = []
    for case_id in EXPECTED_CASES:
        model = models[case_id]
        register_case = register_cases[case_id]
        decomposition_case = decomposition_cases[case_id]
        body_wrenches = model["physical_body_wrenches"]
        registered_body_rows = {row["body"]: row for row in register_case["physical_body_wrenches"]}
        if len(body_wrenches) != 50 or len(registered_body_rows) != 50:
            raise ValueError(f"{case_id}: expected 50 physical-body source wrenches")
        if set(body_wrenches) != set(registered_body_rows):
            raise ValueError(f"{case_id}: model/register physical-body domains differ")
        force_rows: list[list[float]] = []
        moment_rows: list[list[float]] = []
        for body in sorted(body_wrenches):
            wrench = body_wrenches[body]
            register_wrench = registered_body_rows[body]
            f = [float(value) for value in wrench["force_xyz_n"]]
            m = [float(value) for value in wrench["moment_about_global_origin_xyz_nmm"]]
            if f != [float(value) for value in register_wrench["force_xyz_n"]]:
                raise ValueError(f"{case_id}/{body}: model and register force rows differ")
            if m != [float(value) for value in register_wrench["moment_about_global_origin_xyz_nmm"]]:
                raise ValueError(f"{case_id}/{body}: model and register first-moment rows differ")
            force_rows.append(f)
            moment_rows.append(m)
        source_force = sum_vectors(force_rows)
        source_moment = sum_vectors(moment_rows)

        nodal_force, nodal_moment = nodal_wrench(model)
        body_vs_nodal_force = assert_close(
            source_force, nodal_force, FORCE_GUARD_N, f"{case_id} body/nodal force closure"
        )
        body_vs_nodal_moment = assert_close(
            source_moment, nodal_moment, MOMENT_GUARD_NMM, f"{case_id} body/nodal first-moment closure"
        )
        assembly = model["case_assembly_audit"]
        body_vs_audit_force = assert_close(
            source_force, assembly["global_force_xyz_n"], FORCE_GUARD_N, f"{case_id} body/audit force closure"
        )
        body_vs_audit_moment = assert_close(
            source_moment,
            assembly["global_moment_about_origin_xyz_nmm"],
            MOMENT_GUARD_NMM,
            f"{case_id} body/audit first-moment closure",
        )
        decomposition_force = [float(value) for value in decomposition_case["registered_total_force_xyz_N"]]
        decomposition_moment = [
            float(value) for value in decomposition_case["registered_total_moment_about_origin_xyz_Nmm"]
        ]
        body_vs_decomposition_force = assert_close(
            source_force, decomposition_force, FORCE_GUARD_N, f"{case_id} body/decomposition force closure"
        )
        body_vs_decomposition_moment = assert_close(
            source_moment,
            decomposition_moment,
            MOMENT_GUARD_NMM,
            f"{case_id} body/decomposition first-moment closure",
        )

        gravity_force = [float(value) for value in decomposition_case["gravity_force_xyz_N"]]
        climber_force = [float(value) for value in decomposition_case["climber_force_xyz_N"]]
        gravity_moment = [float(value) for value in decomposition_case["gravity_moment_about_origin_xyz_Nmm"]]
        climber_moment = [float(value) for value in decomposition_case["climber_moment_about_origin_xyz_Nmm"]]
        component_force = [gravity_force[i] + climber_force[i] for i in range(3)]
        component_moment = [gravity_moment[i] + climber_moment[i] for i in range(3)]
        component_force_residual = assert_close(
            component_force, source_force, FORCE_GUARD_N, f"{case_id} gravity/climber force recomposition"
        )
        component_moment_residual = assert_close(
            component_moment, source_moment, MOMENT_GUARD_NMM, f"{case_id} gravity/climber first-moment recomposition"
        )

        normal_total = -source_force[2]
        if normal_total <= 0.0:
            raise ValueError(f"{case_id}: source vertical resultant does not require upward compression")
        cop_x = source_moment[1] / normal_total
        cop_y = -source_moment[0] / normal_total
        hull_result = classify_hull_point((cop_x, cop_y), hull)
        reaction_moment = [cop_y * normal_total, -cop_x * normal_total, 0.0]
        force_balance_residual = [0.0, 0.0, 0.0]
        moment_balance_residual = [0.0, 0.0, 0.0]
        for axis in range(3):
            force_balance_residual[axis] = source_force[axis] + (normal_total if axis == 2 else 0.0)
            moment_balance_residual[axis] = source_moment[axis] + reaction_moment[axis]

        case_results.append(
            {
                "case_id": case_id,
                "load_only_model_path": model_paths[case_id],
                "load_only_model_sha256": pin_map[model_paths[case_id]],
                "physical_body_source_wrench_count": len(body_wrenches),
                "global_datum": "source model global origin [0,0,0] mm; X/Y horizontal, +Z upward",
                "source_force_xyz_N": source_force,
                "source_moment_about_global_origin_xyz_Nmm": source_moment,
                "decomposition_components": {
                    "gravity_force_xyz_N": gravity_force,
                    "gravity_moment_about_global_origin_xyz_Nmm": gravity_moment,
                    "climber_force_xyz_N": climber_force,
                    "climber_moment_about_global_origin_xyz_Nmm": climber_moment,
                },
                "required_upward_normal_resultant_N": normal_total,
                "required_center_of_pressure_xyz_mm": [cop_x, cop_y, 0.0],
                "footprint_hull_status": hull_result["status"],
                "signed_distances_to_hull_supporting_edges_mm": hull_result[
                    "signed_distances_to_hull_supporting_edges_mm"
                ],
                "minimum_signed_hull_edge_distance_mm": hull_result["minimum_signed_hull_edge_distance_mm"],
                "limiting_hull_edge_index": hull_result["limiting_edge_index"],
                "normal_reaction_resultant_xyz_N": [0.0, 0.0, normal_total],
                "normal_reaction_moment_about_origin_xyz_Nmm": reaction_moment,
                "external_plus_normal_resultant_force_residual_xyz_N": force_balance_residual,
                "external_plus_normal_resultant_moment_residual_xyz_Nmm": moment_balance_residual,
                "unresolved_by_normal_only_screen": {
                    "external_horizontal_force_xyz_N": [source_force[0], source_force[1], 0.0],
                    "external_yaw_moment_z_Nmm": source_moment[2],
                    "interpretation": "Requires separate tangential/yaw equilibrium treatment; this packet does not qualify friction or tangential capacity.",
                },
                "source_closure_residuals": {
                    "max_abs_force_body_sum_vs_source_nodal_map_N": body_vs_nodal_force,
                    "max_abs_first_moment_body_sum_vs_source_nodal_map_Nmm": body_vs_nodal_moment,
                    "max_abs_force_body_sum_vs_assembly_audit_N": body_vs_audit_force,
                    "max_abs_first_moment_body_sum_vs_assembly_audit_Nmm": body_vs_audit_moment,
                    "max_abs_force_body_sum_vs_validated_decomposition_N": body_vs_decomposition_force,
                    "max_abs_first_moment_body_sum_vs_validated_decomposition_Nmm": body_vs_decomposition_moment,
                    "max_abs_force_gravity_plus_climber_recomposition_N": component_force_residual,
                    "max_abs_first_moment_gravity_plus_climber_recomposition_Nmm": component_moment_residual,
                    "validated_decomposition_reported_force_residual_N": decomposition_case[
                        "total_force_residual_N"
                    ],
                    "validated_decomposition_reported_first_moment_residual_Nmm": decomposition_case[
                        "total_first_moment_residual_Nmm"
                    ],
                },
            }
        )

    if any(row["footprint_hull_status"] == "outside" for row in case_results):
        status = "GLOBAL_NORMAL_RESULTANT_OBSTRUCTION_IN_AT_LEAST_ONE_CASE"
    else:
        status = "PASS_SIX_CASE_GLOBAL_NORMAL_REACTION_NECESSARY_SCREEN"

    return {
        "schema": "current_six_case_floor_global_necessary_statics_screen/v1",
        "status": status,
        "producer_sha256": sha256_file(Path(__file__).resolve()),
        "source_pins_sha256": sha256_file(PINS_PATH),
        "source_dependencies": {
            "source_load_register_path": register_path.as_posix(),
            "source_load_register_sha256": register_sha,
            "validated_decomposition_path": decomposition_path.as_posix(),
            "validated_decomposition_sha256": decomposition_sha,
            "upstream_source_pins_path": upstream_pins_path.as_posix(),
            "upstream_source_pins_sha256": upstream_pins_sha,
            "case_ids": EXPECTED_CASES,
            "rejected_response_forces_used": False,
            "native_solve_executed": False,
        },
        "scope": "Solver-independent global necessary screen for nonnegative vertical normal reactions on the pinned flat floor; computes load-only source wrenches and CoP, without adopting response forces.",
        "method": {
            "support_plane_global_z_mm": 0.0,
            "source_moment_datum": "global origin [0,0,0] mm",
            "floor_normal_direction_global_xyz": [0.0, 0.0, 1.0],
            "required_total_upward_normal_N": "N = -Fz",
            "required_center_of_pressure_xy_mm": "(My/N, -Mx/N)",
            "necessary_condition": "For nonnegative point-normal reactions, CoP must lie in the convex hull of the 100 physical source floor points.",
            "hull_algorithm": "pure-Python monotone chain, counter-clockwise vertices; no external geometry or LP solver",
            "signed_hull_distance_definition": "Minimum normalized signed distance to any CCW hull supporting line; positive is inside, near zero is boundary, negative is outside. This is not source contact-law compatibility.",
            "numeric_guards": {
                "source_force_closure_roundoff_N": FORCE_GUARD_N,
                "source_first_moment_closure_roundoff_Nmm": MOMENT_GUARD_NMM,
                "support_plane_tolerance_mm": PLANE_GUARD_MM,
                "normal_component_tolerance": NORMAL_GUARD,
                "hull_boundary_classification_tolerance_mm": HULL_BOUNDARY_GUARD_MM,
                "meaning": "Roundoff and geometric classification guards only; not structural acceptance limits.",
            },
            "normal_only_residual_scope": "Vertical force and overturning moments about X/Y are balanced by the required normal resultant. Fx, Fy, and Mz are listed as unresolved and require separate tangential/yaw analysis.",
        },
        "floor_geometry": {
            "physical_floor_point_count": len(floor_points),
            "unique_physical_floor_point_count": len({tuple(row["point_xyz_mm"]) for row in floor_points}),
            "matching_unilateral_normal_binding_count_per_model": 100,
            "matching_support_node_count_per_model": 100,
            "all_six_case_floor_geometry_identical": True,
            "global_z_min_mm": min(row["point_xyz_mm"][2] for row in floor_points),
            "global_z_max_mm": max(row["point_xyz_mm"][2] for row in floor_points),
            "normal_directions_global_xyz": sorted({tuple(row["normal_xyz"]) for row in floor_points}),
            "footprint_convex_hull_vertex_count": len(hull),
            "footprint_convex_hull_area_mm2": hull_area,
            "footprint_convex_hull_vertices_ccw_xy_mm": [[x, y] for x, y in hull],
            "physical_floor_points": floor_points,
        },
        "rectangle_oracle": oracle,
        "cases": case_results,
        "limits": [
            "This is a necessary whole-frame resultant screen only; an outside CoP would rule out nonnegative upward normal reactions on the pinned footprint, while an inside CoP does not establish source contact-law or displacement compatibility.",
            "No local contact state, contact history, gap closure, tangential force, friction capacity, yaw restraint, floor condition, actual support, or physical failure is established.",
            "No timber/joint/hardware strength or frame acceptance is evaluated.",
            "No rejected response forces, contact masks, native solve, geometry change, or support experiment is used.",
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--write", action="store_true", help="write a fresh source-bound screen")
    group.add_argument("--verify", action="store_true", help="compare recomputed screen byte-for-byte")
    args = parser.parse_args()
    result = build_report()
    observed = json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n"
    if args.write:
        OUTPUT.write_text(observed, encoding="utf-8")
        print(f"WROTE {OUTPUT.relative_to(ROOT)}")
    else:
        if not OUTPUT.is_file():
            raise SystemExit(f"missing {OUTPUT.relative_to(ROOT)}; run with --write")
        expected = OUTPUT.read_text(encoding="utf-8")
        if expected != observed:
            raise SystemExit("FAIL: recomputed floor normal statics screen differs from screen.json")
        print("PASS: source pins, 100 floor points/normals, six source wrenches, oracle, and CoP screen")
    print(f"status={result['status']} floor_points={result['floor_geometry']['physical_floor_point_count']} hull_vertices={result['floor_geometry']['footprint_convex_hull_vertex_count']} cases={len(result['cases'])}")
    for row in result["cases"]:
        x, y, _ = row["required_center_of_pressure_xyz_mm"]
        print(
            f"{row['case_id']}: N={row['required_upward_normal_resultant_N']:.9f} N "
            f"CoP=({x:.6f},{y:.6f}) mm {row['footprint_hull_status']} "
            f"margin={row['minimum_signed_hull_edge_distance_mm']:.6f} mm"
        )


if __name__ == "__main__":
    main()
