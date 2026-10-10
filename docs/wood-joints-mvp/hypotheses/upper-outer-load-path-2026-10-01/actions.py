#!/usr/bin/env python3
"""Build point-action receiver and section-wrench records for both top outer cleats.

This is a source-bound equilibrium reconstruction. It does not recover finite-
element half-body tractions, calculate capacity, or accept a joint.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]

CANDIDATE = "compact-floor-flush-wood-joints-development"
REVISION = "led-clearance-2x6-runner-seated-blocks-v1"
CASES = ("a12-rear", "a1-rear", "k12-rear")
BLOCKS = {
    "top_outer_left_cleat": {
        "prefix": "top_outer/clip_single_top_left_1/",
        "hosts": ("base_rail_top", "base_side_left"),
    },
    "top_outer_right_cleat": {
        "prefix": "top_outer/clip_single_top_right_2/",
        "hosts": ("base_rail_top", "base_side_right"),
    },
}
EXPECTED_LOAD_FACTORS = (0.1, 0.2, 0.3, 0.45, 0.675, 0.925, 1.0)
INCREMENT_GATES = (
    "mpc_interval_checks_passed",
    "retained_bilateral_checks_passed",
    "springa_law_checks_passed",
    "selected_floor_complementarity_passed",
    "inactive_floor_tangent_no_restraint_or_reaction_passed",
    "raw_balance_passed",
    "rounding_interval_balance_passed",
)
PLANE_CLASSIFICATION_TOLERANCE_MM = 1e-6

UPPER_JOINTS = "docs/wood-joints-mvp/hypotheses/upper-frame-joint-review-2026-09-30/upper-joints.json"
GEOMETRY_JSON = "docs/wood-joints-mvp/hypotheses/upper-block-strength-2026-10-01/geometry.json"
UPPER_PRODUCER = "docs/wood-joints-mvp/hypotheses/upper-frame-joint-review-2026-09-30/produce.py"
GEOMETRY_PRODUCER = "docs/wood-joints-mvp/hypotheses/upper-block-strength-2026-10-01/geometry.py"

# The values here are independent pins. The inherited freeze files are useful
# provenance, but they are not allowed to silently redefine this packet's inputs.
PINNED_SHA256 = {
    UPPER_JOINTS: "0fc5f9ce9c92effcb01d3213c38b33282c281539dab9d48cb06f33e15c1994a6",
    GEOMETRY_JSON: "2ba66f4242b59e73a7dfc14a0b21d20d1f2710b9f835d60fce569eb73353fe91",
    UPPER_PRODUCER: "d650e2abcbbcd4633ecf41d7ccb44daba4063ca4c281d9792f7204bafd6fa2a6",
    GEOMETRY_PRODUCER: "ea1273e95833192624afd4b3b6408a3065158cc302924ed702032c2896f42680",
    "docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/current-springa-selected-floor-a12-rear-attempt03/model.json": "8a90452d8afa1f1722b3253b18d5aeec72c432033a22d5d0828082022cc1cda8",
    "docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/current-springa-selected-floor-a12-rear-attempt03/response.json": "892dadeed0b20d809ce5250d3cd1c3deb31697f69208d8bbefb5f702160e1274",
    "docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/current-springa-selected-floor-a1-rear-attempt02/model.json": "72d043e1a70702d8d464c21a039e897036e17c95e368ec776063584dac74f5fd",
    "docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/current-springa-selected-floor-a1-rear-attempt02/response-zero-u-token.json": "257b5b743369fcc2242537b7ccfe81f2efba0a195ef044624d7b67da6a09678c",
    "docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/current-k12-rear-spr489-direct-native-attempt01/model.json": "8f1d9bce9b62b18b3694f81816ef5c4c7cbe5e94b4c459a640fce7a98db68dbd",
    "docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/current-k12-rear-spr489-direct-native-attempt01/response.json": "42ffb135d47bd3bd28874e886682b4f07175ee060fb383b6e3c128e5102073c6",
    "docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/current-full-frame-member-solids-attempt01/bundle/members/top_outer_left_cleat.step": "c4ecd881a9dc2e78195d028bf360cc42da86e97129ac44db7fafd7c77f50ba88",
    "docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/current-full-frame-member-solids-attempt01/bundle/members/top_outer_right_cleat.step": "70b94b711f629b6b1d955083c7eafddb07b104c04878c46ae032ba4c953be25c",
}

CASE_SOURCE_PATHS = {
    "a12-rear": {
        "model": "docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/current-springa-selected-floor-a12-rear-attempt03/model.json",
        "response": "docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/current-springa-selected-floor-a12-rear-attempt03/response.json",
    },
    "a1-rear": {
        "model": "docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/current-springa-selected-floor-a1-rear-attempt02/model.json",
        "response": "docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/current-springa-selected-floor-a1-rear-attempt02/response-zero-u-token.json",
    },
    "k12-rear": {
        "model": "docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/current-k12-rear-spr489-direct-native-attempt01/model.json",
        "response": "docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/current-k12-rear-spr489-direct-native-attempt01/response.json",
    },
}


class SourceRefusal(ValueError):
    """Raised when an input or source ownership contract is not exact."""


def sha256_file(path: Path) -> str:
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def canonical_json(value: Any) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n").encode("utf-8")


def _reject_constant(value: str) -> None:
    raise SourceRefusal(f"non-standard/non-finite JSON number: {value}")


def load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(), parse_constant=_reject_constant)
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise SourceRefusal(f"cannot parse pinned JSON {path}: {exc}") from exc


def verify_pinned_sources(root: Path = ROOT) -> dict[str, Any]:
    records = []
    for relative, expected in sorted(PINNED_SHA256.items()):
        path = root / relative
        if not path.is_file():
            raise SourceRefusal(f"required pinned source is missing: {relative}")
        actual = sha256_file(path)
        if actual != expected:
            raise SourceRefusal(
                f"pinned source changed: {relative}: expected {expected}, got {actual}"
            )
        records.append({"path": relative, "sha256": expected})
    return {"schema": "upper-outer-load-path-source-pins/v1", "sources": records}


def _finite_number(value: Any, label: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise SourceRefusal(f"{label} must be a finite number")
    result = float(value)
    if not math.isfinite(result):
        raise SourceRefusal(f"{label} must be finite")
    return result


def _vector(value: Any, label: str) -> list[float]:
    if not isinstance(value, (list, tuple)) or len(value) != 3:
        raise SourceRefusal(f"{label} must contain exactly three components")
    return [_finite_number(component, f"{label}[{index}]") for index, component in enumerate(value)]


def add(a: list[float], b: list[float]) -> list[float]:
    return [x + y for x, y in zip(a, b, strict=True)]


def sub(a: list[float], b: list[float]) -> list[float]:
    return [x - y for x, y in zip(a, b, strict=True)]


def scale(a: list[float], scalar: float) -> list[float]:
    return [scalar * x for x in a]


def dot(a: list[float], b: list[float]) -> float:
    return math.fsum(x * y for x, y in zip(a, b, strict=True))


def cross(a: list[float], b: list[float]) -> list[float]:
    return [
        a[1] * b[2] - a[2] * b[1],
        a[2] * b[0] - a[0] * b[2],
        a[0] * b[1] - a[1] * b[0],
    ]


def norm(a: list[float]) -> float:
    return math.sqrt(dot(a, a))


def unit(a: list[float], label: str = "vector") -> list[float]:
    length = norm(a)
    if not math.isfinite(length) or length <= 0:
        raise SourceRefusal(f"{label} has no finite direction")
    return scale(a, 1.0 / length)


def vector_sum(rows: list[list[float]]) -> list[float]:
    if not rows:
        return [0.0, 0.0, 0.0]
    return [math.fsum(row[index] for row in rows) for index in range(3)]


def wrench_at_point(
    point_xyz_mm: list[float],
    force_n: list[float],
    force_radius_n: list[float],
    datum_xyz_mm: list[float],
) -> dict[str, list[float]]:
    point = _vector(point_xyz_mm, "wrench point")
    force = _vector(force_n, "wrench force")
    radius = _vector(force_radius_n, "wrench force rounding radius")
    datum = _vector(datum_xyz_mm, "wrench datum")
    if any(component < 0 for component in radius):
        raise SourceRefusal("force rounding radius must be nonnegative")
    arm = sub(point, datum)
    moment = cross(arm, force)
    moment_radius = [
        abs(arm[1]) * radius[2] + abs(arm[2]) * radius[1],
        abs(arm[2]) * radius[0] + abs(arm[0]) * radius[2],
        abs(arm[0]) * radius[1] + abs(arm[1]) * radius[0],
    ]
    return {
        "force_n": force,
        "moment_nmm": moment,
        "force_rounding_radius_n": radius,
        "moment_rounding_radius_nmm": moment_radius,
    }


def sum_wrenches(wrenches: list[dict[str, list[float]]]) -> dict[str, list[float]]:
    keys = (
        "force_n",
        "moment_nmm",
        "force_rounding_radius_n",
        "moment_rounding_radius_nmm",
    )
    return {key: vector_sum([wrench[key] for wrench in wrenches]) for key in keys}


def negate_wrench(wrench: dict[str, list[float]]) -> dict[str, list[float]]:
    return {
        "force_n": scale(wrench["force_n"], -1.0),
        "moment_nmm": scale(wrench["moment_nmm"], -1.0),
        "force_rounding_radius_n": list(wrench["force_rounding_radius_n"]),
        "moment_rounding_radius_nmm": list(wrench["moment_rounding_radius_nmm"]),
    }


def _max_abs(values: list[float]) -> float:
    return max((abs(value) for value in values), default=0.0)


def _require_close(a: list[float], b: list[float], tolerance: float, label: str) -> None:
    residual = sub(a, b)
    if _max_abs(residual) > tolerance:
        raise SourceRefusal(f"{label} differs by {residual}; tolerance {tolerance}")


def _point_for_endpoint(row: dict[str, Any], body: str) -> list[float]:
    if row["first"] == body:
        key = "first_point"
    elif row["second"] == body:
        key = "second_point"
    else:
        raise SourceRefusal(f"body {body} is not an endpoint of connection {row.get('name')}")
    point = row.get(key, row.get("point"))
    if point is None:
        raise SourceRefusal(f"connection endpoint {key} is missing")
    return _vector(point, f"connection endpoint {key}")


def _force_for_endpoint(row: dict[str, Any], body: str) -> list[float]:
    if row["first"] == body:
        key = "force_on_first_xyz_n"
    elif row["second"] == body:
        key = "force_on_second_xyz_n"
    else:
        raise SourceRefusal(f"body {body} is not an endpoint of connection {row.get('name')}")
    return _vector(row.get(key), f"connection {key}")


def _check_connection_source(name: str, row: dict[str, Any], model: dict[str, Any]) -> None:
    if row.get("name", name) != name:
        raise SourceRefusal(f"connection name disagrees with its response key: {name}")
    if not isinstance(row.get("first"), str) or not isinstance(row.get("second"), str):
        raise SourceRefusal(f"connection {name} has ambiguous endpoint ownership")
    if row["first"] == row["second"]:
        raise SourceRefusal(f"connection {name} repeats an endpoint body")
    owned = model.get("connection_ownership", {}).get(name)
    if not isinstance(owned, dict):
        raise SourceRefusal(f"connection {name} is missing from the source ownership map")
    if (owned.get("first"), owned.get("second")) != (row["first"], row["second"]):
        raise SourceRefusal(f"connection {name} endpoint order/ownership changed")
    if owned.get("role") != row.get("role"):
        raise SourceRefusal(f"connection {name} role disagrees with the source model")
    for body, side in ((row["first"], "first"), (row["second"], "second")):
        actual_point = _point_for_endpoint(row, body)
        expected_point = owned.get(f"{side}_point", owned.get("point"))
        if expected_point is None:
            raise SourceRefusal(f"source model has no {side} attachment point for {name}")
        _require_close(
            actual_point,
            _vector(expected_point, f"source-model {side} attachment point"),
            1e-8,
            f"connection {name} {side} attachment point",
        )
    first_force = _force_for_endpoint(row, row["first"])
    second_force = _force_for_endpoint(row, row["second"])
    _require_close(first_force, scale(second_force, -1.0), 1e-10, f"connection {name} paired forces")
    radius = _vector(row.get("force_rounding_radius_xyz_n"), f"connection {name} rounding radius")
    if any(component < 0 for component in radius):
        raise SourceRefusal(f"connection {name} has negative rounding radius")
    if "half-last-place" not in str(row.get("force_precision_basis", "")):
        raise SourceRefusal(f"connection {name} is missing its RF rounding basis")
    source_ids = row.get("source_row_ids")
    inventory = row.get("source_inventory_rows")
    if not isinstance(source_ids, list) or not source_ids or len(set(source_ids)) != len(source_ids):
        raise SourceRefusal(f"connection {name} has missing or duplicate source row identifiers")
    if not isinstance(inventory, list) or [item.get("source_row_id") for item in inventory] != source_ids:
        raise SourceRefusal(f"connection {name} source inventory IDs are ambiguous")
    if any(item.get("source_connection_name") != name for item in inventory):
        raise SourceRefusal(f"connection {name} source inventory names disagree")


def _expected_sources(upper: dict[str, Any], case: str) -> dict[str, Any]:
    case_records = upper.get("source_cases")
    if not isinstance(case_records, dict) or set(case_records) != set(CASES):
        raise SourceRefusal("upper-joints.json case inventory changed or is incomplete")
    record = case_records[case]
    expected = CASE_SOURCE_PATHS[case]
    for label in ("model", "response"):
        source = record.get(label)
        if not isinstance(source, dict):
            raise SourceRefusal(f"upper-joints source case {case} lacks {label}")
        if source.get("path") != expected[label]:
            raise SourceRefusal(f"upper-joints source path changed for {case} {label}")
        if source.get("sha256") != PINNED_SHA256[expected[label]]:
            raise SourceRefusal(f"upper-joints source digest changed for {case} {label}")
    return record


def _check_release_boundary(source: dict[str, Any], label: str) -> None:
    for key in (
        "complete_joint_resistance_established",
        "six_case_envelope_established",
        "drilling_released",
        "fabrication_released",
        "structural_released",
        "reviewed_geometry_changed",
        "native_solve_executed_by_this_packet",
    ):
        if source.get(key) is not False:
            raise SourceRefusal(f"{label} has an unexpected {key} claim")


def _check_target_inventory(upper: dict[str, Any], geometry: dict[str, Any]) -> None:
    if upper.get("candidate") != CANDIDATE or upper.get("geometry_revision_id") != REVISION:
        raise SourceRefusal("upper-joints candidate or reviewed revision changed")
    _check_release_boundary(upper, "upper-joints source")
    counts = upper.get("counts", {})
    expected_counts = {
        "cases": 3,
        "increments_per_case": 7,
        "upper_blocks": 4,
        "physical_bolts": 16,
        "bolt_action_records": 336,
        "complete_block_balance_records": 84,
    }
    for key, expected in expected_counts.items():
        if counts.get(key) != expected:
            raise SourceRefusal(f"upper-joints count {key} changed")
    if upper.get("schema") != "upper-frame-joint-review/v1":
        raise SourceRefusal("upper-joints source schema changed")
    if geometry.get("candidate") != CANDIDATE or geometry.get("geometry_revision_id") != REVISION:
        raise SourceRefusal("geometry candidate or reviewed revision changed")
    _check_release_boundary(geometry, "upper-block geometry source")
    if geometry.get("schema") != "upper-block-geometry-applicability-inventory/v1":
        raise SourceRefusal("upper-block geometry source schema changed")
    section_map = {row.get("block"): row for row in geometry.get("block_exact_sections", [])}
    for block in BLOCKS:
        section_set = section_map.get(block)
        if not isinstance(section_set, dict):
            raise SourceRefusal(f"exact section inventory is missing {block}")
        if section_set.get("exact_geometry_available") is not True:
            raise SourceRefusal(f"exact section geometry is not available for {block}")
        if section_set.get("sampled_section_count") != 5 or len(section_set.get("sampled_sections", [])) != 5:
            raise SourceRefusal(f"{block} does not have exactly five source sections")
        if section_set.get("member_force_moment_to_sampled_sections") != (
            "open; no section is assigned a force or moment by this geometry inventory"
        ):
            raise SourceRefusal(f"{block} section load-attribution boundary changed")
        step_path = section_set.get("finished_step")
        if step_path not in PINNED_SHA256 or section_set.get("finished_step_sha256") != PINNED_SHA256[step_path]:
            raise SourceRefusal(f"{block} finished STEP identity changed")
        if not isinstance(section_set.get("declared_grain_global_xyz"), list):
            raise SourceRefusal(f"{block} section normal/grain direction is missing")


def _source_balance_row(
    upper: dict[str, Any], block: str, case: str, increment_index: int
) -> dict[str, Any]:
    rows = [
        row
        for row in upper.get("block_balances", [])
        if row.get("block") == block
        and row.get("case") == case
        and row.get("increment_index") == increment_index
    ]
    if len(rows) != 1:
        raise SourceRefusal(f"expected one source balance row for {block} {case} {increment_index}")
    return rows[0]


def _model_load_actions(
    model: dict[str, Any], block: str, load_factor: float, datum: list[float]
) -> list[dict[str, Any]]:
    physical_loads = model.get("physical_body_loads", {}).get(block)
    if not isinstance(physical_loads, dict) or len(physical_loads) != 20:
        raise SourceRefusal(f"{block} source body-load inventory must contain 20 nodal actions")
    nodes = model.get("nodes", {})
    actions = []
    for node_id, reference_force in sorted(physical_loads.items(), key=lambda item: int(item[0])):
        if node_id not in nodes:
            raise SourceRefusal(f"{block} source body-load node {node_id} has no coordinate")
        point = _vector(nodes[node_id], f"body-load node {node_id} coordinate")
        force = scale(_vector(reference_force, f"body-load node {node_id} force"), load_factor)
        radius = [0.0, 0.0, 0.0]
        actions.append(
            {
                "action_id": f"body-load:{block}:node-{node_id}",
                "source_name": f"physical_body_loads[{block}][{node_id}]",
                "source_type": "discrete_source_body_load",
                "node_id": node_id,
                "point_xyz_mm": point,
                "force_n": force,
                "force_rounding_radius_n": radius,
                "wrench_at_block_datum": wrench_at_point(point, force, radius, datum),
            }
        )
    return actions


def _connection_actions(
    incident: dict[str, dict[str, Any]],
    model: dict[str, Any],
    block: str,
    datum: list[float],
    host_order: tuple[str, ...],
) -> tuple[list[dict[str, Any]], dict[str, list[dict[str, Any]]]]:
    expected_roles = {
        "candidate_bolt_lateral_plane": 4,
        "physical_bolt_outer_seat_tension": 4,
        "timber_or_panel_contact": 8,
    }
    role_counts = {role: 0 for role in expected_roles}
    row_ids: set[str] = set()
    actions = []
    by_host: dict[str, list[dict[str, Any]]] = {host: [] for host in host_order}
    for name, row in sorted(incident.items()):
        _check_connection_source(name, row, model)
        role = row.get("role")
        if role not in expected_roles:
            raise SourceRefusal(f"unexpected connection role {role!r} for {name}")
        role_counts[role] += 1
        if block not in (row["first"], row["second"]):
            raise SourceRefusal(f"connection {name} does not have the target block as an endpoint")
        host = row["second"] if row["first"] == block else row["first"]
        if host not in by_host:
            raise SourceRefusal(f"connection {name} has unexpected receiver host {host}")
        block_point = _point_for_endpoint(row, block)
        receiver_point = _point_for_endpoint(row, host)
        block_force = _force_for_endpoint(row, block)
        receiver_force = _force_for_endpoint(row, host)
        radius = _vector(row["force_rounding_radius_xyz_n"], f"{name} rounding radius")
        ids = list(row["source_row_ids"])
        if row_ids.intersection(ids):
            raise SourceRefusal(f"duplicate source row ownership in {block}: {ids}")
        row_ids.update(ids)
        block_wrench = wrench_at_point(block_point, block_force, radius, datum)
        receiver_wrench = wrench_at_point(receiver_point, receiver_force, radius, datum)
        pair_force_residual = add(block_force, receiver_force)
        _require_close(pair_force_residual, [0.0, 0.0, 0.0], 1e-10, f"{name} paired force")
        action = {
            "source_name": name,
            "role": role,
            "axis_id": row.get("axis_id"),
            "host": host,
            "source_row_ids": ids,
            "force_precision_basis": row["force_precision_basis"],
            "block_endpoint": {
                "body": block,
                "point_xyz_mm": block_point,
                "force_n": block_force,
                "force_rounding_radius_n": radius,
                "wrench_at_block_datum": block_wrench,
            },
            "receiver_endpoint": {
                "body": host,
                "point_xyz_mm": receiver_point,
                "force_n": receiver_force,
                "force_rounding_radius_n": radius,
                "wrench_transported_to_block_datum": receiver_wrench,
            },
            "paired_force_residual_n": pair_force_residual,
            "paired_moment_sum_at_block_datum_nmm": add(
                block_wrench["moment_nmm"], receiver_wrench["moment_nmm"]
            ),
        }
        actions.append(action)
        by_host[host].append(action)
    if role_counts != expected_roles:
        raise SourceRefusal(f"{block} connection roles/counts changed: {role_counts}")
    if len(actions) != 16 or len(by_host) != 2 or any(not values for values in by_host.values()):
        raise SourceRefusal(f"{block} receiver ownership is incomplete")
    return actions, by_host


def _aggregate_endpoint_wrenches(
    rows: list[dict[str, Any]], endpoint_key: str, wrench_key: str
) -> dict[str, list[float]]:
    return sum_wrenches([row[endpoint_key][wrench_key] for row in rows])


def _assert_source_receiver_groups(
    balance: dict[str, Any], by_host: dict[str, list[dict[str, Any]]]
) -> dict[str, Any]:
    source = balance.get("receiver_actions_on_block")
    if not isinstance(source, dict) or set(source) != set(by_host):
        raise SourceRefusal("receiver group names disagree with source block balance")
    groups = {}
    for host, actions in sorted(by_host.items()):
        names = [row["source_name"] for row in actions]
        if len(names) != len(set(names)):
            raise SourceRefusal(f"duplicate receiver action name for {host}")
        expected = source[host]
        if len(expected.get("source_names", [])) != len(set(expected.get("source_names", []))):
            raise SourceRefusal(f"source receiver group {host} has duplicate action ownership")
        if set(names) != set(expected.get("source_names", [])):
            raise SourceRefusal(f"receiver action membership changed for {host}")
        block_wrench = _aggregate_endpoint_wrenches(actions, "block_endpoint", "wrench_at_block_datum")
        receiver_wrench = _aggregate_endpoint_wrenches(
            actions, "receiver_endpoint", "wrench_transported_to_block_datum"
        )
        _require_close(block_wrench["force_n"], _vector(expected["force_n"], "source receiver force"), 1e-8, f"{host} block receiver force")
        _require_close(
            block_wrench["moment_nmm"],
            _vector(expected["moment_at_block_datum_nmm"], "source receiver moment"),
            1e-6,
            f"{host} block receiver moment",
        )
        groups[host] = {
            "action_count": len(actions),
            "source_names": sorted(names),
            "block_actions_on_receiver": block_wrench,
            "receiver_actions_transported_to_block_datum": receiver_wrench,
            "source_block_receiver_resultant": {
                "force_n": expected["force_n"],
                "moment_at_block_datum_nmm": expected["moment_at_block_datum_nmm"],
            },
            "reproduces_source_block_receiver_resultant": True,
        }
    return groups


def _whole_body_resultant(
    connection_actions: list[dict[str, Any]], body_load_actions: list[dict[str, Any]]
) -> dict[str, list[float]]:
    wrenches = [row["block_endpoint"]["wrench_at_block_datum"] for row in connection_actions]
    wrenches.extend(row["wrench_at_block_datum"] for row in body_load_actions)
    return sum_wrenches(wrenches)


def _check_whole_body_balance(
    resultant: dict[str, list[float]],
    source_upper: dict[str, Any],
    source_response: dict[str, Any],
    block: str,
) -> dict[str, Any]:
    source_response_row = source_response.get("physical_balance", {}).get("body_equilibrium", {}).get(block)
    if not isinstance(source_response_row, dict):
        raise SourceRefusal(f"response is missing physical balance for {block}")
    datum = _vector(source_response_row.get("reference_xyz_mm"), "response body-balance datum")
    _require_close(datum, _vector(source_upper["datum_xyz_mm"], "upper block-balance datum"), 1e-10, f"{block} balance datum")
    source_force = _vector(source_response_row["force_residual_xyz_n"], "response force residual")
    source_moment = _vector(source_response_row["moment_residual_xyz_nmm"], "response moment residual")
    source_force_radius = _vector(source_response_row["force_rounding_radius_xyz_n"], "response force radius")
    source_moment_radius = _vector(source_response_row["moment_rounding_radius_xyz_nmm"], "response moment radius")
    _require_close(resultant["force_n"], source_force, 1e-8, f"{block} whole-body force residual")
    _require_close(resultant["moment_nmm"], source_moment, 1e-6, f"{block} whole-body moment residual")
    _require_close(resultant["force_rounding_radius_n"], source_force_radius, 1e-12, f"{block} whole-body force interval")
    _require_close(resultant["moment_rounding_radius_nmm"], source_moment_radius, 1e-10, f"{block} whole-body moment interval")
    _require_close(resultant["force_n"], _vector(source_upper["force_residual_n"], "upper force residual"), 1e-8, f"{block} frozen upper force residual")
    _require_close(resultant["moment_nmm"], _vector(source_upper["moment_residual_nmm"], "upper moment residual"), 1e-6, f"{block} frozen upper moment residual")
    _require_close(resultant["force_rounding_radius_n"], _vector(source_upper["force_rounding_radius_n"], "upper force radius"), 1e-12, f"{block} frozen upper force interval")
    _require_close(resultant["moment_rounding_radius_nmm"], _vector(source_upper["moment_rounding_radius_nmm"], "upper moment radius"), 1e-10, f"{block} frozen upper moment interval")
    if source_upper.get("source_load_node_count") != 20 or source_upper.get("incident_connection_count") != 16:
        raise SourceRefusal(f"{block} source balance inventory is incomplete")
    if source_response_row.get("printed_resultants_passed") is not True or source_response_row.get("interval_resultants_passed") is not True:
        raise SourceRefusal(f"{block} source whole-body balance gate changed")
    if _max_abs(resultant["force_n"]) > 0.1 or _max_abs(resultant["moment_nmm"]) > 2.0:
        raise SourceRefusal(f"{block} source whole-body resultants exceed the source audit tolerances")
    if any(abs(x) > r + 1e-9 for x, r in zip(resultant["force_n"], resultant["force_rounding_radius_n"], strict=True)):
        raise SourceRefusal(f"{block} force residual is outside its propagated interval")
    if any(abs(x) > r + 1e-6 for x, r in zip(resultant["moment_nmm"], resultant["moment_rounding_radius_nmm"], strict=True)):
        raise SourceRefusal(f"{block} moment residual is outside its propagated interval")
    return {
        "datum_xyz_mm": datum,
        "computed_external_wrench": resultant,
        "source_response_residual": {
            "force_n": source_force,
            "moment_nmm": source_moment,
            "force_rounding_radius_n": source_force_radius,
            "moment_rounding_radius_nmm": source_moment_radius,
        },
        "source_upper_residual_reproduced": True,
        "source_rounding_intervals_reproduced": True,
        "within_unchanged_source_audit_tolerances": True,
    }


def _wrench_transport_to_datum(
    wrench_at_old_datum: dict[str, list[float]],
    old_datum_xyz_mm: list[float],
    new_datum_xyz_mm: list[float],
) -> dict[str, list[float]]:
    arm = sub(old_datum_xyz_mm, new_datum_xyz_mm)
    moved_moment = add(wrench_at_old_datum["moment_nmm"], cross(arm, wrench_at_old_datum["force_n"]))
    moved_moment_radius = add(
        wrench_at_old_datum["moment_rounding_radius_nmm"],
        [
            abs(arm[1]) * wrench_at_old_datum["force_rounding_radius_n"][2]
            + abs(arm[2]) * wrench_at_old_datum["force_rounding_radius_n"][1],
            abs(arm[2]) * wrench_at_old_datum["force_rounding_radius_n"][0]
            + abs(arm[0]) * wrench_at_old_datum["force_rounding_radius_n"][2],
            abs(arm[0]) * wrench_at_old_datum["force_rounding_radius_n"][1]
            + abs(arm[1]) * wrench_at_old_datum["force_rounding_radius_n"][0],
        ],
    )
    return {
        "force_n": list(wrench_at_old_datum["force_n"]),
        "moment_nmm": moved_moment,
        "force_rounding_radius_n": list(wrench_at_old_datum["force_rounding_radius_n"]),
        "moment_rounding_radius_nmm": moved_moment_radius,
    }


def section_traces(
    point_actions: list[dict[str, Any]],
    plane_origin_xyz_mm: list[float],
    plane_normal_global_xyz: list[float],
    plane_classification_tolerance_mm: float = PLANE_CLASSIFICATION_TOLERANCE_MM,
) -> dict[str, Any]:
    """Partition point actions and report both one-sided source-point traces.

    An action within the plane tolerance is assigned in full to opposite halves
    in the two distinct one-sided traces; it is never split between halves.
    """
    origin = _vector(plane_origin_xyz_mm, "section plane origin")
    normal = unit(_vector(plane_normal_global_xyz, "section plane normal"), "section plane normal")
    tolerance = _finite_number(plane_classification_tolerance_mm, "plane classification tolerance")
    if tolerance <= 0:
        raise SourceRefusal("plane classification tolerance must be positive")
    ids = [row.get("action_id") for row in point_actions]
    if any(not isinstance(action_id, str) or not action_id for action_id in ids):
        raise SourceRefusal("section action has no stable source identifier")
    if len(ids) != len(set(ids)):
        raise SourceRefusal("section point-action ownership contains duplicate IDs")
    classified = []
    for row in point_actions:
        point = _vector(row.get("point_xyz_mm"), f"{row['action_id']} point")
        signed_distance = dot(sub(point, origin), normal)
        if not math.isfinite(signed_distance):
            raise SourceRefusal(f"{row['action_id']} has non-finite cut coordinate")
        if signed_distance < -tolerance:
            side = "negative"
        elif signed_distance > tolerance:
            side = "positive"
        else:
            side = "on_plane"
        datum_wrench = row.get("wrench_at_block_datum")
        if datum_wrench is None:
            radius = _vector(row.get("force_rounding_radius_n", [0, 0, 0]), "section action radius")
            force = _vector(row.get("force_n"), "section action force")
            datum_wrench = wrench_at_point(point, force, radius, origin)
        else:
            datum_wrench = _wrench_transport_to_datum(
                datum_wrench,
                _vector(row["wrench_datum_xyz_mm"], "action wrench datum"),
                origin,
            )
        classified.append({"action_id": row["action_id"], "side": side, "wrench": datum_wrench})

    all_external = sum_wrenches([row["wrench"] for row in classified])
    on_plane_ids = sorted(row["action_id"] for row in classified if row["side"] == "on_plane")
    traces = {}
    for trace_name, positive_sides in (
        ("approached_from_negative_coordinate", {"positive", "on_plane"}),
        ("approached_from_positive_coordinate", {"positive"}),
    ):
        positive_rows = [row for row in classified if row["side"] in positive_sides]
        negative_rows = [row for row in classified if row["side"] not in positive_sides]
        positive_external = sum_wrenches([row["wrench"] for row in positive_rows])
        negative_external = sum_wrenches([row["wrench"] for row in negative_rows])
        partition_external = sum_wrenches([positive_external, negative_external])
        partition_residual_force = sub(partition_external["force_n"], all_external["force_n"])
        partition_residual_moment = sub(partition_external["moment_nmm"], all_external["moment_nmm"])
        _require_close(partition_external["force_n"], all_external["force_n"], 1e-10, "section force partition")
        _require_close(partition_external["moment_nmm"], all_external["moment_nmm"], 1e-8, "section moment partition")
        positive_cut = negate_wrench(positive_external)
        negative_cut = negate_wrench(negative_external)
        combined_half_balance = sum_wrenches([positive_cut, negative_cut, all_external])
        _require_close(combined_half_balance["force_n"], [0.0, 0.0, 0.0], 1e-10, "section two-half force closure")
        _require_close(combined_half_balance["moment_nmm"], [0.0, 0.0, 0.0], 1e-8, "section two-half moment closure")
        traces[trace_name] = {
            "positive_side_action_ids": sorted(row["action_id"] for row in positive_rows),
            "negative_side_action_ids": sorted(row["action_id"] for row in negative_rows),
            "on_plane_actions_assigned_to": "positive" if "on_plane" in positive_sides else "negative",
            "positive_side_external_wrench": positive_external,
            "negative_side_external_wrench": negative_external,
            "cut_wrench_on_positive_side_material": positive_cut,
            "cut_wrench_on_negative_side_material": negative_cut,
            "partition_external_wrench": partition_external,
            "partition_minus_whole_external_residual": {
                "force_n": partition_residual_force,
                "moment_nmm": partition_residual_moment,
            },
            "two_cut_side_reactions_plus_whole_external_residual": combined_half_balance,
        }
    return {
        "point_action_model": True,
        "plane_classification_tolerance_mm": tolerance,
        "on_plane_action_ids": on_plane_ids,
        "on_plane_action_count": len(on_plane_ids),
        "whole_point_action_wrench_at_plane": all_external,
        "one_sided_traces": traces,
        "actual_finite_element_half_body_traction_established": False,
    }


def _section_action_rows(
    connection_actions: list[dict[str, Any]], body_load_actions: list[dict[str, Any]], datum: list[float]
) -> list[dict[str, Any]]:
    rows = []
    for action in connection_actions:
        block_endpoint = action["block_endpoint"]
        rows.append(
            {
                "action_id": f"receiver:{action['source_name']}:on:{block_endpoint['body']}",
                "source_name": action["source_name"],
                "source_type": "receiver_point_resultant",
                "point_xyz_mm": block_endpoint["point_xyz_mm"],
                "force_n": block_endpoint["force_n"],
                "force_rounding_radius_n": block_endpoint["force_rounding_radius_n"],
                "wrench_at_block_datum": block_endpoint["wrench_at_block_datum"],
                "wrench_datum_xyz_mm": datum,
            }
        )
    for action in body_load_actions:
        rows.append(
            {
                "action_id": action["action_id"],
                "source_name": action["source_name"],
                "source_type": action["source_type"],
                "point_xyz_mm": action["point_xyz_mm"],
                "force_n": action["force_n"],
                "force_rounding_radius_n": action["force_rounding_radius_n"],
                "wrench_at_block_datum": action["wrench_at_block_datum"],
                "wrench_datum_xyz_mm": datum,
            }
        )
    return rows


def _section_records(
    geometry: dict[str, Any],
    block: str,
    point_actions: list[dict[str, Any]],
    source_whole_body: dict[str, Any],
) -> list[dict[str, Any]]:
    section_set = next((row for row in geometry["block_exact_sections"] if row["block"] == block), None)
    if section_set is None:
        raise SourceRefusal(f"exact section geometry is missing {block}")
    grain = unit(_vector(section_set["declared_grain_global_xyz"], f"{block} declared grain"), f"{block} grain")
    source_datum = _vector(source_whole_body["datum_xyz_mm"], "block balance datum")
    output = []
    for section in section_set["sampled_sections"]:
        origin = _vector(section.get("plane_origin_xyz_mm"), f"{section.get('sample_id')} plane origin")
        sample_normal = _vector(section.get("plane_normal_global_xyz", grain), "section plane normal")
        if abs(dot(unit(sample_normal), grain) - 1.0) > 1e-7:
            raise SourceRefusal(f"section {section.get('sample_id')} normal does not follow declared grain")
        trace = section_traces(point_actions, origin, sample_normal)
        expected_whole = _wrench_transport_to_datum(
            source_whole_body["computed_external_wrench"], source_datum, origin
        )
        actual_whole = trace["whole_point_action_wrench_at_plane"]
        _require_close(actual_whole["force_n"], expected_whole["force_n"], 1e-8, "section whole-body force transport")
        _require_close(actual_whole["moment_nmm"], expected_whole["moment_nmm"], 1e-6, "section whole-body moment transport")
        output.append(
            {
                "sample_id": section["sample_id"],
                "sample_kind": section["sample_kind"],
                "grain_coordinate_mm": _finite_number(section["grain_coordinate_mm"], "section grain coordinate"),
                "plane_origin_xyz_mm": origin,
                "plane_normal_global_xyz": unit(sample_normal),
                "area_mm2": _finite_number(section["area_mm2"], "section area"),
                "material_component_count": section["material_component_count"],
                "source_geometry_method": section["method"],
                "point_action_wrench_and_traces": trace,
                "whole_body_external_wrench_transported_from_block_datum": expected_whole,
                "whole_body_transport_reproduced": True,
            }
        )
    if len(output) != 5 or len({row["sample_id"] for row in output}) != 5:
        raise SourceRefusal(f"{block} sampled-section inventory is missing or duplicated")
    return output


def _check_source_state(
    upper: dict[str, Any], geometry: dict[str, Any], case: str, model: dict[str, Any], response: dict[str, Any]
) -> None:
    if model.get("candidate") != CANDIDATE or response.get("candidate") != CANDIDATE:
        raise SourceRefusal(f"{case} source candidate changed")
    if model.get("geometry_revision_id") != REVISION or response.get("geometry_revision_id") != REVISION:
        raise SourceRefusal(f"{case} source geometry revision changed")
    if model.get("case_id") != case or response.get("case_id") != case:
        raise SourceRefusal(f"{case} source case identity changed")
    for key in ("qualified_for_design", "complete_joint_validated"):
        if model.get(key) is not False:
            raise SourceRefusal(f"{case} source model has unexpected {key} claim")
    for source in (model, response):
        for key in ("drilling_released", "fabrication_released", "structural_released"):
            if source.get(key) not in (None, False):
                raise SourceRefusal(f"{case} source has unexpected {key} claim")
    for key in (
        "qualified_for_design",
        "mechanical_acceptance",
        "joint_demand_accepted",
        "floor_capacity_established",
        "friction_qualified",
    ):
        if response.get(key) is not False:
            raise SourceRefusal(f"{case} source response has unexpected {key} claim")
    if response.get("complete_joint_validated") not in (None, False):
        raise SourceRefusal(f"{case} source response has unexpected complete-joint claim")
    increments = response.get("increments")
    if not isinstance(increments, list) or len(increments) != 7:
        raise SourceRefusal(f"{case} source must have seven response increments")
    if [increment.get("load_factor") for increment in increments] != list(EXPECTED_LOAD_FACTORS):
        raise SourceRefusal(f"{case} source increment/load-factor sequence changed")
    for index, increment in enumerate(increments):
        if any(increment.get(gate) is not True for gate in INCREMENT_GATES):
            raise SourceRefusal(f"{case} increment {index} no longer has all source response gates")
    if response.get("source_input_model_json_sha256") != PINNED_SHA256[CASE_SOURCE_PATHS[case]["model"]]:
        raise SourceRefusal(f"{case} response no longer binds the pinned input model")
    if set(upper.get("source_cases", {})) != set(CASES):
        raise SourceRefusal("upper-joints source case inventory changed")
    if not geometry.get("block_exact_sections"):
        raise SourceRefusal("geometry source has no exact section records")


def _build_state(
    upper: dict[str, Any],
    geometry: dict[str, Any],
    case: str,
    increment_index: int,
    model: dict[str, Any],
    response: dict[str, Any],
    block: str,
) -> dict[str, Any]:
    cfg = BLOCKS[block]
    increment = response["increments"][increment_index]
    load_factor = _finite_number(increment.get("load_factor"), f"{case} load factor")
    source_balance = _source_balance_row(upper, block, case, increment_index)
    datum = _vector(source_balance.get("datum_xyz_mm"), f"{block} source datum")
    physical_balance = increment.get("physical_balance", {}).get("body_equilibrium", {}).get(block)
    if not isinstance(physical_balance, dict):
        raise SourceRefusal(f"{block} is missing source physical balance in {case}")
    _require_close(_vector(physical_balance.get("reference_xyz_mm"), "response balance datum"), datum, 1e-10, f"{block} response datum")
    all_connections = increment.get("physical_connection_forces")
    if not isinstance(all_connections, dict):
        raise SourceRefusal(f"{case} increment has no physical connection resultants")
    incident = {
        name: row
        for name, row in all_connections.items()
        if block in (row.get("first"), row.get("second"))
    }
    if len(incident) != 16:
        raise SourceRefusal(f"{block} {case} {increment_index} expected 16 incident connections, got {len(incident)}")
    expected_source_names = {
        name for group in source_balance.get("receiver_actions_on_block", {}).values() for name in group.get("source_names", [])
    }
    if len(expected_source_names) != 16 or set(incident) != expected_source_names:
        raise SourceRefusal(f"{block} {case} {increment_index} action ownership differs from frozen source balance")
    connection_actions, by_host = _connection_actions(incident, model, block, datum, cfg["hosts"])
    source_groups = _assert_source_receiver_groups(source_balance, by_host)
    body_load_actions = _model_load_actions(model, block, load_factor, datum)
    if source_balance.get("source_load_node_count") != len(body_load_actions):
        raise SourceRefusal(f"{block} source body-load count changed")
    whole = _whole_body_resultant(connection_actions, body_load_actions)
    whole_balance = _check_whole_body_balance(whole, source_balance, increment, block)
    points = _section_action_rows(connection_actions, body_load_actions, datum)
    sections = _section_records(geometry, block, points, whole_balance)
    action_row_count = len(connection_actions) + len(body_load_actions)
    if action_row_count != 36:
        raise SourceRefusal(f"{block} point-action count changed")
    return {
        "block": block,
        "case": case,
        "increment_index": increment_index,
        "load_factor": load_factor,
        "source_balance_datum_xyz_mm": datum,
        "receiver_actions": connection_actions,
        "receiver_group_resultants": source_groups,
        "source_discrete_body_loads": body_load_actions,
        "whole_body_equilibrium": whole_balance,
        "exact_geometry_section_wrenches": sections,
        "source_point_action_count": action_row_count,
        "source_incident_connection_count": len(connection_actions),
        "source_body_load_node_count": len(body_load_actions),
        "receiver_groups_reproduce_frozen_source": True,
    }


def build_report(root: Path = ROOT) -> tuple[dict[str, Any], dict[str, Any]]:
    pins_document = verify_pinned_sources(root)
    upper = load_json(root / UPPER_JOINTS)
    geometry = load_json(root / GEOMETRY_JSON)
    _check_target_inventory(upper, geometry)
    step_by_block = {
        section["block"]: section["finished_step_sha256"]
        for section in geometry["block_exact_sections"]
        if section.get("block") in BLOCKS
    }
    for block in BLOCKS:
        expected_step = PINNED_SHA256[next(path for path in PINNED_SHA256 if path.endswith(f"{block}.step"))]
        if step_by_block.get(block) != expected_step:
            raise SourceRefusal(f"{block} exact section source STEP digest changed")
    report_states = []
    for case in CASES:
        source_refs = _expected_sources(upper, case)
        model = load_json(root / source_refs["model"]["path"])
        response = load_json(root / source_refs["response"]["path"])
        _check_source_state(upper, geometry, case, model, response)
        for block in BLOCKS:
            for increment_index in range(7):
                report_states.append(
                    _build_state(upper, geometry, case, increment_index, model, response, block)
                )
    expected_states = len(BLOCKS) * len(CASES) * 7
    state_ids = [
        (row["block"], row["case"], row["increment_index"])
        for row in report_states
    ]
    if len(report_states) != expected_states or len(set(state_ids)) != expected_states:
        raise SourceRefusal("state inventory is incomplete or contains duplicate ownership")
    report = {
        "schema": "upper-outer-point-action-load-path/v1",
        "status": "SOURCE_BOUND_POINT_ACTION_EQUILIBRIUM_RECONSTRUCTION",
        "candidate": CANDIDATE,
        "geometry_revision_id": REVISION,
        "source_report": {"path": UPPER_JOINTS, "sha256": PINNED_SHA256[UPPER_JOINTS]},
        "geometry_report": {"path": GEOMETRY_JSON, "sha256": PINNED_SHA256[GEOMETRY_JSON]},
        "source_pin_count": len(pins_document["sources"]),
        "producer_sha256": sha256_file(HERE / "actions.py"),
        "counts": {
            "blocks": len(BLOCKS),
            "cases": len(CASES),
            "increments_per_case": 7,
            "same_state_records": expected_states,
            "receiver_point_action_rows": sum(row["source_incident_connection_count"] for row in report_states),
            "discrete_body_load_rows": sum(row["source_body_load_node_count"] for row in report_states),
            "exact_section_state_records": sum(len(row["exact_geometry_section_wrenches"]) for row in report_states),
            "cut_side_traces": sum(
                2 * len(row["exact_geometry_section_wrenches"]) for row in report_states
            ),
        },
        "method_boundary": {
            "receiver_actions": "Individual simultaneous response point resultants; lateral, outer-seat axial-tie, and contact actions retain their own source rows and signs.",
            "axial_endpoint_points": "Use each response row's first_point/second_point when present, matching the source model ownership map.",
            "body_loads": "Preserve each discrete source physical_body_loads force at its source node and scale it by that response increment's load factor.",
            "section_actions": "A point-action equilibrium reference at the named response attachment points and source body-load nodes. Attachment equations map those actions to finite-element nodes; a source point may not represent the actual force on a cut half-body when interpolation support straddles the cut.",
            "on_plane_action_rule": "Report two one-sided traces. Assign each on-plane point action in full to opposite half-bodies in the two traces; never split an action.",
            "uncertainty": "Propagate only the frozen RF force rounding radii by component and the corresponding lever-arm moment bounds; no coordinate, constitutive, model-form, or response uncertainty is added.",
            "region_allocation": "No uniform or area-based allocation among connected cut-face regions.",
            "capacity_and_acceptance": "No section stress, regional force distribution, capacity, complete-joint resistance, or acceptance is calculated.",
        },
        "claim_boundary": {
            "complete_joint_resistance_established": False,
            "six_case_envelope_established": False,
            "native_solve_executed_by_this_packet": False,
            "actual_finite_element_half_body_tractions_established": False,
            "section_capacity_calculated": False,
            "drilling_released": False,
            "fabrication_released": False,
            "structural_released": False,
        },
        "states": report_states,
    }
    return report, pins_document


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verify", action="store_true", help="replay and byte-compare ignored report and source pins")
    args = parser.parse_args()
    report, pins = build_report()
    report_bytes = canonical_json(report)
    pins_bytes = canonical_json(pins)
    report_path = HERE / "actions.json"
    pins_path = HERE / "source-pins.json"
    if args.verify:
        if not pins_path.exists() or pins_path.read_bytes() != pins_bytes:
            raise SystemExit("source-pins.json is missing or differs from the independent source-pin replay")
        if not report_path.exists() or report_path.read_bytes() != report_bytes:
            raise SystemExit("actions.json is missing or differs from source-bound replay")
    else:
        pins_path.write_bytes(pins_bytes)
        report_path.write_bytes(report_bytes)
    print(
        json.dumps(
            {
                "mode": "verify" if args.verify else "write",
                "status": report["status"],
                "counts": report["counts"],
                "actions_json_sha256": hashlib.sha256(report_bytes).hexdigest(),
                "source_pins_json_sha256": hashlib.sha256(pins_bytes).hexdigest(),
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
