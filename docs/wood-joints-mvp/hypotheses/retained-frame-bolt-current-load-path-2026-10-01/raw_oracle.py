#!/usr/bin/env python3
"""Independently check retained frame-bolt forces against frozen native DATs.

This script reads the produced report, the frozen models and native DAT files,
and the pinned physical-connector projection contract. It does not import the
report producer or any response parser. It checks only the twelve retained
frame-bolt axes; the separate candidate axes remain outside this oracle.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

REPOSITORY_ROOT = Path(__file__).resolve().parents[4]
FREEZE_PATH = Path(
    "docs/wood-joints-mvp/hypotheses/upper-frame-joint-review-2026-09-30/freeze.json"
)
PROJECTION_PATH = Path(
    "docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/"
    "current-frame-physical-connector-projection-contract-attempt01/"
    "projection-contract.json"
)
PINNED_FREEZE_SHA256 = (
    "d4ba1c78eb358d25e32819201e9c59e05d425a06d9e4e5cca3dc09d7139ffd73"
)
PINNED_PROJECTION_SHA256 = (
    "4ceca771e26e1f1d0bf8efca8e3d77dc6d94194553d95e1fd75652ecf2f3f2d3"
)
EXPECTED_CASES = {"a1-rear", "a12-rear", "k12-rear"}
EXPECTED_RECEIVER_BODIES = {
    "base_floor_left",
    "base_floor_right",
    "base_post_outer_left",
    "base_post_outer_right",
    "base_side_left",
    "base_side_right",
    "lumber_leg_left",
    "lumber_leg_right",
}
EPSILON = sys.float_info.epsilon
FORCE_TOKEN = re.compile(r"^[+-]?\d\.\d{6}E[+-]\d{2}$")
FORCE_HEADER = re.compile(
    r"^\s*forces\s*\([^\n]*?\btime\s+([0-9.EeDd+-]+)\s*$",
    re.MULTILINE | re.IGNORECASE,
)


class OracleError(ValueError):
    """Raised when frozen source data or the produced report does not reconcile."""


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise OracleError(message)


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _read_bytes(relative_path: str | Path) -> bytes:
    path = Path(relative_path)
    if not path.is_absolute():
        path = REPOSITORY_ROOT / path
    try:
        return path.read_bytes()
    except OSError as error:
        raise OracleError(f"Cannot read {path}: {error}") from error


def _read_json(relative_path: str | Path) -> tuple[dict[str, Any], str]:
    raw = _read_bytes(relative_path)
    try:
        parsed = json.loads(raw)
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise OracleError(f"Invalid JSON in {relative_path}: {error}") from error
    _require(isinstance(parsed, dict), f"Expected an object in {relative_path}")
    return parsed, _sha256(raw)


def _finite_number(value: Any, label: str) -> float:
    _require(
        isinstance(value, (int, float)) and not isinstance(value, bool),
        f"{label} is not numeric",
    )
    result = float(value)
    _require(math.isfinite(result), f"{label} is not finite")
    return result


def _vector(value: Any, label: str) -> list[float]:
    _require(isinstance(value, list) and len(value) == 3, f"{label} must have three entries")
    return [_finite_number(item, f"{label}[{index}]") for index, item in enumerate(value)]


def _vec_add(left: list[float], right: list[float]) -> list[float]:
    return [left[i] + right[i] for i in range(3)]


def _vec_sub(left: list[float], right: list[float]) -> list[float]:
    return [left[i] - right[i] for i in range(3)]


def _vec_scale(scalar: float, value: list[float]) -> list[float]:
    return [scalar * item for item in value]


def _vec_abs(value: list[float]) -> list[float]:
    return [abs(item) for item in value]


def _vec_sum(vectors: list[list[float]]) -> list[float]:
    result = [0.0, 0.0, 0.0]
    for vector in vectors:
        result = _vec_add(result, vector)
    return result


def _dot(left: list[float], right: list[float]) -> float:
    return sum(left[i] * right[i] for i in range(3))


def _cross(left: list[float], right: list[float]) -> list[float]:
    return [
        left[1] * right[2] - left[2] * right[1],
        left[2] * right[0] - left[0] * right[2],
        left[0] * right[1] - left[1] * right[0],
    ]


def _cross_roundoff_scale(left: list[float], right: list[float]) -> list[float]:
    return [
        abs(left[1] * right[2]) + abs(left[2] * right[1]),
        abs(left[2] * right[0]) + abs(left[0] * right[2]),
        abs(left[0] * right[1]) + abs(left[1] * right[0]),
    ]


def _arithmetic_tolerance(*values: float, scale: float = 1.0) -> float:
    finite_values = [abs(float(value)) for value in values if math.isfinite(float(value))]
    return 256.0 * EPSILON * max([1.0, abs(scale), *finite_values])


def _assert_scalar_close(
    actual: Any,
    expected: float,
    label: str,
    *,
    absolute_tolerance: float | None = None,
    scale: float = 1.0,
) -> None:
    value = _finite_number(actual, label)
    tolerance = (
        absolute_tolerance
        if absolute_tolerance is not None
        else _arithmetic_tolerance(value, expected, scale=scale)
    )
    _require(abs(value - expected) <= tolerance, f"{label}: {value!r} != {expected!r} (tol {tolerance:g})")


def _assert_vector_close(
    actual: Any,
    expected: list[float],
    label: str,
    *,
    absolute_tolerance: float | None = None,
    scales: list[float] | None = None,
) -> None:
    values = _vector(actual, label)
    if scales is None:
        scales = [1.0, 1.0, 1.0]
    _require(len(scales) == 3, f"{label} tolerance scales are malformed")
    for index in range(3):
        tolerance = (
            absolute_tolerance
            if absolute_tolerance is not None
            else _arithmetic_tolerance(values[index], expected[index], scale=scales[index])
        )
        _require(
            abs(values[index] - expected[index]) <= tolerance,
            f"{label}[{index}]: {values[index]!r} != {expected[index]!r} (tol {tolerance:g})",
        )


def _assert_intersects(
    actual: Any,
    expected: float,
    actual_radius: Any,
    expected_radius: float,
    label: str,
) -> None:
    value = _finite_number(actual, label)
    radius_a = _finite_number(actual_radius, f"{label} radius")
    _require(radius_a >= 0.0 and expected_radius >= 0.0, f"{label}: negative interval radius")
    tolerance = _arithmetic_tolerance(value, expected, scale=max(radius_a, expected_radius, 1.0))
    _require(
        abs(value - expected) <= radius_a + expected_radius + tolerance,
        f"{label}: intervals do not intersect ({value:g} ± {radius_a:g}, "
        f"{expected:g} ± {expected_radius:g})",
    )


def _assert_vector_intersects(
    actual: Any,
    expected: list[float],
    actual_radius: Any,
    expected_radius: list[float],
    label: str,
) -> None:
    values = _vector(actual, label)
    radii = _vector(actual_radius, f"{label} radius")
    _require(all(radius >= 0.0 for radius in radii + expected_radius), f"{label}: negative interval radius")
    for index in range(3):
        tolerance = _arithmetic_tolerance(
            values[index], expected[index], scale=max(radii[index], expected_radius[index], 1.0)
        )
        _require(
            abs(values[index] - expected[index]) <= radii[index] + expected_radius[index] + tolerance,
            f"{label}[{index}]: intervals do not intersect "
            f"({values[index]:g} ± {radii[index]:g}, "
            f"{expected[index]:g} ± {expected_radius[index]:g})",
        )


def _number_token(token: str, label: str) -> tuple[float, float]:
    _require(FORCE_TOKEN.fullmatch(token) is not None, f"{label}: unsupported native force token {token!r}")
    value = float(token)
    _require(math.isfinite(value), f"{label}: non-finite native force token {token!r}")
    mantissa, exponent_text = token.split("E", 1)
    exponent = int(exponent_text)
    decimal_places = len(mantissa.split(".", 1)[1])
    radius = 0.5 * (10.0 ** (exponent - decimal_places))
    return value, radius


def _parse_force_blocks(data: str, label: str) -> dict[float, dict[str, Any]]:
    """Parse every nodal RF block directly from the pinned DAT text."""
    matches = list(FORCE_HEADER.finditer(data))
    _require(bool(matches), f"{label}: no native nodal forces blocks found")
    blocks: dict[float, dict[str, Any]] = {}
    for match in matches:
        time_token = match.group(1).replace("D", "E").replace("d", "e")
        try:
            time_value = float(time_token)
        except ValueError as error:
            raise OracleError(f"{label}: invalid force-block time {time_token!r}") from error
        _require(math.isfinite(time_value), f"{label}: non-finite force-block time")
        _require(time_value not in blocks, f"{label}: duplicate force block at time {time_value:g}")
        values: dict[int, list[float]] = {}
        radii: dict[int, list[float]] = {}
        tokens_by_node: dict[int, list[str]] = {}
        started = False
        for line_number, line in enumerate(data[match.end() :].splitlines(), start=1):
            fields = line.split()
            if fields and fields[0].isdigit():
                _require(len(fields) == 4, f"{label}: malformed RF row after header at line offset {line_number}")
                node = int(fields[0])
                _require(node not in values, f"{label}: duplicate RF node {node} at time {time_value:g}")
                parsed = [_number_token(token, f"{label} node {node}") for token in fields[1:]]
                values[node] = [entry[0] for entry in parsed]
                radii[node] = [entry[1] for entry in parsed]
                tokens_by_node[node] = list(fields[1:])
                started = True
            elif not started and not line.strip():
                continue
            elif started:
                break
            else:
                raise OracleError(f"{label}: unexpected text before RF rows at time {time_value:g}: {line!r}")
        _require(bool(values), f"{label}: empty RF block at time {time_value:g}")
        blocks[time_value] = {"values": values, "radii": radii, "tokens": tokens_by_node}
    return blocks


def _raw_component(block: dict[str, Any], node: int, dof: int, label: str) -> tuple[float, float]:
    _require(dof in (1, 2, 3), f"{label}: invalid native translational DOF {dof}")
    _require(node in block["values"], f"{label}: native force block lacks node {node}")
    index = dof - 1
    return block["values"][node][index], block["radii"][node][index]


def _raw_vector(block: dict[str, Any], node: int, label: str) -> tuple[list[float], list[float]]:
    _require(node in block["values"], f"{label}: native force block lacks node {node}")
    return list(block["values"][node]), list(block["radii"][node])


def _require_source_pin(
    record: Any,
    kind: str,
    repository_root: Path,
    label: str,
) -> tuple[dict[str, Any], str]:
    _require(isinstance(record, dict), f"{label}: missing {kind} pin")
    relative_path = record.get("path")
    expected_hash = record.get("sha256")
    _require(isinstance(relative_path, str), f"{label}: {kind} pin has no path")
    _require(isinstance(expected_hash, str) and len(expected_hash) == 64, f"{label}: {kind} pin has no SHA-256")
    path = repository_root / relative_path
    try:
        content = path.read_bytes()
    except OSError as error:
        raise OracleError(f"{label}: cannot read pinned {kind} {path}: {error}") from error
    actual_hash = _sha256(content)
    _require(actual_hash == expected_hash, f"{label}: pinned {kind} SHA-256 changed for {relative_path}")
    if kind == "model":
        try:
            parsed = json.loads(content)
        except json.JSONDecodeError as error:
            raise OracleError(f"{label}: invalid pinned model JSON: {error}") from error
        _require(isinstance(parsed, dict), f"{label}: pinned model is not an object")
        return parsed, actual_hash
    if kind == "native_data":
        return {"text": content.decode("utf-8")}, actual_hash
    if kind == "all_body_audit":
        try:
            parsed = json.loads(content)
        except json.JSONDecodeError as error:
            raise OracleError(f"{label}: invalid frozen all-body audit JSON: {error}") from error
        _require(isinstance(parsed, dict), f"{label}: frozen all-body audit is not an object")
        return parsed, actual_hash
    raise OracleError(f"{label}: unsupported pinned source kind {kind}")


def _dict_key(value: Any, key: str, label: str) -> dict[str, Any]:
    _require(isinstance(value, dict), f"{label} is not an object")
    result = value.get(key)
    _require(isinstance(result, dict), f"{label}.{key} is not an object")
    return result


def _projection_rows(projection: dict[str, Any]) -> dict[tuple[str, str, int], dict[str, Any]]:
    _require(
        projection.get("schema") == "current_frame_physical_connector_projection_contract/v1",
        "Pinned connector projection has an unexpected schema",
    )
    _require(projection.get("case_id") == "a12-rear", "Pinned connector projection is not the a12-rear source contract")
    _require(projection.get("candidate") == "compact-floor-flush-wood-joints-development", "Projection candidate changed")
    _require(projection.get("geometry_revision_id") == "led-clearance-2x6-runner-seated-blocks-v1", "Projection geometry revision changed")
    rows = projection.get("rows")
    _require(isinstance(rows, list), "Pinned connector projection has no row list")
    result: dict[tuple[str, str, int], dict[str, Any]] = {}
    for row in rows:
        _require(isinstance(row, dict), "Pinned connector projection contains a malformed row")
        ownership = row.get("ownership")
        if not isinstance(ownership, dict) or ownership.get("role") not in {
            "retained_bolt_lateral_plane",
            "physical_bolt_outer_seat_tension",
        }:
            continue
        key = (
            str(row.get("row_id")),
            str(row.get("source_group")),
            int(row.get("source_inventory_row_index", -1)),
        )
        _require(key not in result, f"Projection repeats source row {key}")
        result[key] = row
    return result


def _projection_match(
    rows: dict[tuple[str, str, int], dict[str, Any]],
    connection_name: str,
    source_row_id: str,
    inventory_index: int,
    label: str,
) -> dict[str, Any]:
    key = (connection_name, source_row_id, inventory_index)
    row = rows.get(key)
    _require(row is not None, f"{label}: source is absent from pinned projection row_id/source_group map: {key}")
    return row


def _vector_record(value: Any, key: str, label: str) -> list[float]:
    record = _dict_key(value, key, label)
    return _vector(record, f"{label}.{key}")


def _build_source_map(
    models: dict[str, dict[str, Any]],
    projection: dict[str, Any],
) -> tuple[dict[str, dict[str, list[dict[str, Any]]]], set[str]]:
    projection_rows = _projection_rows(projection)
    projection_lateral_count = sum(
        1
        for row in projection_rows.values()
        if row.get("ownership", {}).get("role") == "retained_bolt_lateral_plane"
    )
    _require(projection_lateral_count == 24, f"Projection retained-lateral row count changed: {projection_lateral_count}")

    result: dict[str, dict[str, list[dict[str, Any]]]] = {}
    reference_signature: dict[tuple[str, str, int], tuple[Any, ...]] | None = None
    for case_id, model in models.items():
        _require(model.get("candidate") == "compact-floor-flush-wood-joints-development", f"{case_id}: model candidate changed")
        _require(model.get("geometry_revision_id") == "led-clearance-2x6-runner-seated-blocks-v1", f"{case_id}: model geometry revision changed")
        _require(model.get("case_id") == case_id, f"{case_id}: model case binding changed")
        springs = model.get("springs")
        bindings = model.get("unilateral_springa_bindings")
        _require(isinstance(springs, list) and isinstance(bindings, list), f"{case_id}: missing source spring inventories")
        case_axes: dict[str, dict[str, list[dict[str, Any]]]] = defaultdict(lambda: {"lateral": [], "axial": []})
        signature: dict[tuple[str, str, int], tuple[Any, ...]] = {}

        for spring in springs:
            owner = spring.get("physical_owner")
            if not isinstance(owner, dict) or owner.get("role") != "retained_bolt_lateral_plane":
                continue
            connection_name = str(spring.get("name", ""))
            source_row_id = str(spring.get("source_row_id", ""))
            inventory_index = int(spring.get("source_inventory_row_index", -1))
            group = str(spring.get("group", ""))
            dof = int(spring.get("dof", -1))
            nodes = [int(node) for node in spring.get("nodes", [])]
            label = f"{case_id} {source_row_id}"
            _require(source_row_id == group, f"{label}: native source row id/group disagree")
            _require(len(nodes) == 2 and dof in (2, 3), f"{label}: malformed retained SPRING2 source")
            projected = _projection_match(projection_rows, connection_name, source_row_id, inventory_index, label)
            _require(projected.get("family") == "bilateral_spring2", f"{label}: projection family changed")
            connector = projected.get("source_connector")
            _require(isinstance(connector, dict), f"{label}: projection omits SPRING2 connector map")
            _require(list(map(int, connector.get("nodes", []))) == nodes, f"{label}: projection endpoint nodes changed")
            _require(int(connector.get("dof", -1)) == dof, f"{label}: projection local DOF changed")
            _require(int(projected.get("source_element", -1)) == int(spring.get("element", -2)), f"{label}: projection element changed")
            projected_owner = projected["ownership"]
            _require(projected_owner.get("role") == "retained_bolt_lateral_plane", f"{label}: projection ownership role changed")
            _require(projected_owner.get("first_body") == owner.get("first"), f"{label}: projection first body changed")
            _require(projected_owner.get("second_body") == owner.get("second"), f"{label}: projection second body changed")
            direction = _vector(projected_owner.get("direction_global_xyz"), f"{label} projection direction")
            force_basis = owner.get("force_basis")
            _require(isinstance(force_basis, list) and len(force_basis) == 3, f"{label}: missing physical source force basis")
            _assert_vector_close(direction, _vector(force_basis[dof - 1], f"{label} source force-basis row"), f"{label} source/projection direction", absolute_tolerance=1e-12)
            point = _vector(owner.get("point"), f"{label} source point")
            _assert_vector_close(point, _vector(projected_owner.get("point_mm"), f"{label} projection point"), f"{label} source/projection point", absolute_tolerance=1e-8)
            axis_id = str(owner.get("axis_id", ""))
            _require(bool(axis_id), f"{label}: missing retained axis identity")
            source = {
                "axis_id": axis_id,
                "source_row_id": source_row_id,
                "source_group": group,
                "source_inventory_row_index": inventory_index,
                "connection_name": connection_name,
                "family": "bilateral_spring2",
                "source_nodes": nodes,
                "local_dof": dof,
                "direction": direction,
                "owner": owner,
                "projected_row": projected,
                "first_point": point,
                "second_point": point,
            }
            case_axes[axis_id]["lateral"].append(source)
            signature[(connection_name, source_row_id, inventory_index)] = (
                axis_id,
                tuple(nodes),
                dof,
                tuple(direction),
            )

        retained_axes = set(case_axes)
        _require(len(retained_axes) == 12, f"{case_id}: expected twelve retained frame-bolt axes, found {len(retained_axes)}")
        _require(sum(len(value["lateral"]) for value in case_axes.values()) == 24, f"{case_id}: expected 24 retained SPRING2 channels")

        axial_matches: set[str] = set()
        for binding in bindings:
            owner = binding.get("physical_owner")
            if not isinstance(owner, dict) or owner.get("role") != "physical_bolt_outer_seat_tension":
                continue
            axis_id = str(owner.get("axis_id", ""))
            if axis_id not in retained_axes:
                continue
            connection_name = str(binding.get("name", ""))
            source_row_id = str(binding.get("source_row_id", ""))
            inventory_index = int(binding.get("source_inventory_row_index", -1))
            group = str(binding.get("group", ""))
            nodes = [int(node) for node in binding.get("springa_nodes", [])]
            label = f"{case_id} {source_row_id}"
            _require(source_row_id == group, f"{label}: SPRINGA source row id/group disagree")
            _require(len(nodes) == 2, f"{label}: malformed SPRINGA native nodes")
            projected = _projection_match(projection_rows, connection_name, source_row_id, inventory_index, label)
            _require(projected.get("family") == "unilateral_springa", f"{label}: projection family changed")
            projected_owner = projected.get("ownership", {})
            _require(projected_owner.get("role") == "physical_bolt_outer_seat_tension", f"{label}: projection ownership role changed")
            _require(projected_owner.get("first_body") == owner.get("first"), f"{label}: projection first body changed")
            _require(projected_owner.get("second_body") == owner.get("second"), f"{label}: projection second body changed")
            _require(int(projected.get("source_element", -1)) == int(binding.get("source_element", -2)), f"{label}: projection element changed")
            preserved = binding.get("physical_action_on_first_body")
            _require(isinstance(preserved, dict), f"{label}: missing preserved physical first-body action")
            _require(int(preserved.get("sign", 0)) == 1, f"{label}: retained SPRINGA scalar sign changed")
            numerical_axis = _vector(binding.get("numerical_axis_global_xyz"), f"{label} numerical qghost axis")
            direction = _vector(preserved.get("unit_direction_global_xyz"), f"{label} preserved physical direction")
            scalar_normal = _vector(owner.get("scalar_normal"), f"{label} preserved scalar normal")
            _assert_vector_close(direction, scalar_normal, f"{label} physical/scalar direction", absolute_tolerance=1e-12)
            _assert_vector_close(direction, numerical_axis, f"{label} numerical/physical direction", absolute_tolerance=1e-12)
            _assert_vector_close(direction, _vector(projected_owner.get("direction_global_xyz"), f"{label} projection direction"), f"{label} source/projection direction", absolute_tolerance=1e-12)
            first_point = _vector(owner.get("first_point"), f"{label} first-body point")
            second_point = _vector(owner.get("second_point"), f"{label} second-body point")
            _assert_vector_close(first_point, _vector(projected_owner.get("point_mm"), f"{label} projection point"), f"{label} first source/projection point", absolute_tolerance=1e-8)
            _require(binding.get("ground_endpoint_is_numerical_only") is True, f"{label}: numerical ground is no longer marked numerical-only")
            source = {
                "axis_id": axis_id,
                "source_row_id": source_row_id,
                "source_group": group,
                "source_inventory_row_index": inventory_index,
                "connection_name": connection_name,
                "family": "unilateral_springa",
                "source_nodes": nodes,
                "local_dof": None,
                "direction": direction,
                "numerical_axis": numerical_axis,
                "owner": owner,
                "binding": binding,
                "projected_row": projected,
                "first_point": first_point,
                "second_point": second_point,
            }
            case_axes[axis_id]["axial"].append(source)
            _require(axis_id not in axial_matches, f"{case_id}: duplicate outer-seat tie for {axis_id}")
            axial_matches.add(axis_id)
            signature[(connection_name, source_row_id, inventory_index)] = (
                axis_id,
                tuple(nodes),
                1,
                tuple(direction),
            )

        _require(axial_matches == retained_axes, f"{case_id}: retained outer-seat ties do not match lateral axes")
        for axis_id, channels in case_axes.items():
            channels["lateral"].sort(key=lambda row: row["source_inventory_row_index"])
            channels["axial"].sort(key=lambda row: row["source_inventory_row_index"])
            _require(len(channels["lateral"]) == 2, f"{case_id} {axis_id}: expected two lateral components")
            _require(len(channels["axial"]) == 1, f"{case_id} {axis_id}: expected one outer-seat tension channel")
            lateral_owner = channels["lateral"][0]["owner"]
            axial_owner = channels["axial"][0]["owner"]
            _require(lateral_owner.get("first") == axial_owner.get("first"), f"{case_id} {axis_id}: first receiver changed across source rows")
            _require(lateral_owner.get("second") == axial_owner.get("second"), f"{case_id} {axis_id}: second receiver changed across source rows")

        if reference_signature is None:
            reference_signature = signature
        else:
            _require(signature == reference_signature, f"{case_id}: retained source channel mapping differs across frozen models")
        result[case_id] = dict(case_axes)

    axes = set(next(iter(result.values())))
    _require(len(axes) == 12, "Frozen retained source map does not contain twelve axes")
    return result, axes


def _check_report_source_pin(
    report: dict[str, Any],
    case_id: str,
    kind: str,
    frozen_pin: dict[str, Any],
) -> None:
    cases = report.get("case_sources")
    _require(isinstance(cases, dict), "Produced report omits case source pins")
    source_case = cases.get(case_id)
    _require(isinstance(source_case, dict), f"Produced report omits source pins for {case_id}")
    declared = source_case.get(kind)
    _require(isinstance(declared, dict), f"Produced report omits {case_id} {kind} pin")
    _require(declared.get("path") == frozen_pin.get("path"), f"Produced report {case_id} {kind} path differs from freeze")
    _require(declared.get("sha256") == frozen_pin.get("sha256"), f"Produced report {case_id} {kind} SHA differs from freeze")


def _check_report_input_pin(report: dict[str, Any], path: Path, expected_sha256: str) -> None:
    input_pins = report.get("input_pins")
    _require(isinstance(input_pins, dict), "Produced report omits input_pins")
    pin = input_pins.get(str(path))
    _require(isinstance(pin, dict), f"Produced report omits pinned input {path}")
    _require(pin.get("sha256") == expected_sha256, f"Produced report pin changed for {path}")


def _validate_frozen_datum_constancy(
    audit_records: dict[str, dict[str, Any]],
) -> dict[str, list[float]]:
    reference: dict[str, list[float]] = {}
    increments_seen = 0
    for case_id, audit in audit_records.items():
        increments = audit.get("increments")
        _require(isinstance(increments, list) and len(increments) == 7, f"{case_id}: frozen datum source must contain seven increments")
        for increment in increments:
            increments_seen += 1
            body_equilibrium = increment.get("body_equilibrium")
            _require(isinstance(body_equilibrium, dict), f"{case_id}: frozen datum source has no body equilibrium map")
            for member in EXPECTED_RECEIVER_BODIES:
                body_row = _dict_key(body_equilibrium, member, f"{case_id} frozen body equilibrium")
                datum = _vector(body_row.get("reference_xyz_mm"), f"{case_id} {member} frozen reference datum")
                if member in reference:
                    _assert_vector_close(datum, reference[member], f"{case_id} {member} frozen datum constancy", absolute_tolerance=1e-9)
                else:
                    reference[member] = datum
    _require(increments_seen == 21 and set(reference) == EXPECTED_RECEIVER_BODIES, "Frozen source audit does not bind all 168 receiver datum references")
    return reference


def _assert_metadata_vector(
    record: Any,
    key: str,
    expected: list[float],
    label: str,
    tolerance: float = 1e-9,
) -> None:
    _require(isinstance(record, dict), f"{label}: metadata record is not an object")
    _assert_vector_close(record.get(key), expected, label + "." + key, absolute_tolerance=tolerance)


def _check_source_metadata(report_channel: dict[str, Any], source: dict[str, Any], label: str) -> None:
    for key in ("source_row_id", "source_inventory_row_index", "family", "connection_name", "source_nodes", "local_dof"):
        expected = {
            "source_row_id": source["source_row_id"],
            "source_inventory_row_index": source["source_inventory_row_index"],
            "family": source["family"],
            "connection_name": source["connection_name"],
            "source_nodes": source["source_nodes"],
            "local_dof": source["local_dof"],
        }[key]
        _require(report_channel.get(key) == expected, f"{label}: report {key} differs from frozen source")
    _assert_metadata_vector(report_channel, "direction_global_xyz", source["direction"], label, tolerance=1e-12)


def _check_report_channel(
    report_channel: dict[str, Any],
    source: dict[str, Any],
    block: dict[str, Any],
    state_label: str,
) -> dict[str, Any]:
    label = f"{state_label} {source['source_row_id']}"
    _check_source_metadata(report_channel, source, label)
    direction = source["direction"]
    if source["family"] == "bilateral_spring2":
        first_node, second_node = source["source_nodes"]
        dof = source["local_dof"]
        rf_first, radius_first = _raw_component(block, first_node, dof, label + " first endpoint RF")
        rf_second, radius_second = _raw_component(block, second_node, dof, label + " second endpoint RF")
        raw_pair_residual = rf_first + rf_second
        pair_radius = radius_first + radius_second
        _require(
            abs(raw_pair_residual) <= pair_radius + _arithmetic_tolerance(rf_first, rf_second),
            f"{label}: native SPRING2 endpoint RF tokens do not satisfy action/reaction within rounding radii",
        )
        scalar_first = -rf_first
        scalar_radius = radius_first
        raw_second_scalar = -rf_second
        raw_second_radius = radius_second
    else:
        q_node, ground_node = source["source_nodes"]
        q_force, q_radius = _raw_vector(block, q_node, label + " qghost RF")
        ground_force, ground_radius = _raw_vector(block, ground_node, label + " numerical-ground RF")
        numerical_axis = source["numerical_axis"]
        scalar_first = _dot(q_force, numerical_axis)
        scalar_radius = _dot(_vec_abs(numerical_axis), q_radius)
        ground_scalar = _dot(ground_force, numerical_axis)
        ground_scalar_radius = _dot(_vec_abs(numerical_axis), ground_radius)
        for component in range(3):
            residual = q_force[component] + ground_force[component]
            allowed = q_radius[component] + ground_radius[component]
            _require(
                abs(residual) <= allowed + _arithmetic_tolerance(q_force[component], ground_force[component]),
                f"{label}: qghost and numerical-ground RF tokens fail vector action/reaction at component {component}",
            )
        _require(
            abs(scalar_first + ground_scalar) <= scalar_radius + ground_scalar_radius
            + _arithmetic_tolerance(scalar_first, ground_scalar),
            f"{label}: qghost scalar does not oppose the numerical-ground RF projection",
        )
        raw_second_scalar = -scalar_first
        raw_second_radius = scalar_radius

    _assert_scalar_close(
        report_channel.get("scalar_force_on_first_N"), scalar_first, label + " reported scalar force"
    )
    _assert_scalar_close(
        report_channel.get("scalar_radius_N"), scalar_radius, label + " reported scalar radius"
    )
    expected_first = _vec_scale(scalar_first, direction)
    expected_radius = [abs(direction[index]) * scalar_radius for index in range(3)]
    _assert_vector_close(
        report_channel.get("force_on_first_xyz_n"), expected_first, label + " reported first-body force"
    )
    _assert_vector_close(
        report_channel.get("force_rounding_radius_xyz_n"), expected_radius, label + " reported force radius"
    )
    raw_second = _vec_scale(raw_second_scalar, direction)
    raw_second_radius_xyz = [abs(direction[index]) * raw_second_radius for index in range(3)]
    return {
        "source": source,
        "scalar_first": scalar_first,
        "scalar_radius": scalar_radius,
        "direction": direction,
        "force_first": expected_first,
        "force_radius": expected_radius,
        "raw_second_force": raw_second,
        "raw_second_radius": raw_second_radius_xyz,
    }


def _find_channel_report(
    bolt_state: dict[str, Any],
    sources: list[dict[str, Any]],
    label: str,
) -> dict[tuple[str, int], dict[str, Any]]:
    channels = bolt_state.get("scalar_channels")
    _require(isinstance(channels, list), f"{label}: missing scalar_channels")
    expected_keys = {
        (source["source_row_id"], source["source_inventory_row_index"])
        for source in sources
    }
    _require(len(channels) == 3, f"{label}: expected three source scalar channels")
    result: dict[tuple[str, int], dict[str, Any]] = {}
    for channel in channels:
        _require(isinstance(channel, dict), f"{label}: malformed scalar channel")
        key = (str(channel.get("source_row_id")), int(channel.get("source_inventory_row_index", -1)))
        _require(key not in result, f"{label}: duplicate scalar channel {key}")
        result[key] = channel
    _require(set(result) == expected_keys, f"{label}: scalar channel source inventory differs from frozen 2+1 map")
    return result


def _sum_channel_force(channels: list[dict[str, Any]], side: str) -> tuple[list[float], list[float]]:
    sign = 1.0 if side == "first" else -1.0
    forces = [_vec_scale(sign, channel["force_first"]) for channel in channels]
    radii = [channel["force_radius"] for channel in channels]
    return _vec_sum(forces), _vec_sum(radii)


def _sum_channel_moment(
    channels: list[dict[str, Any]],
    point: list[float],
    datum: list[float],
    side: str,
) -> tuple[list[float], list[float], list[float]]:
    sign = 1.0 if side == "first" else -1.0
    lever = _vec_sub(point, datum)
    moment_vectors: list[list[float]] = []
    origin_vectors: list[list[float]] = []
    datum_scales = [0.0, 0.0, 0.0]
    origin_scales = [0.0, 0.0, 0.0]
    datum_radii = [0.0, 0.0, 0.0]
    origin_radii = [0.0, 0.0, 0.0]
    for channel in channels:
        force = _vec_scale(sign, channel["force_first"])
        moment_vectors.append(_cross(lever, force))
        origin_vectors.append(_cross(point, force))
        dscale = _cross_roundoff_scale(lever, force)
        oscale = _cross_roundoff_scale(point, force)
        for component in range(3):
            datum_scales[component] += dscale[component]
            origin_scales[component] += oscale[component]
            coefficient_datum = _cross(lever, channel["direction"])[component]
            coefficient_origin = _cross(point, channel["direction"])[component]
            datum_radii[component] += abs(coefficient_datum) * channel["scalar_radius"]
            origin_radii[component] += abs(coefficient_origin) * channel["scalar_radius"]
    return _vec_sum(moment_vectors), _vec_sum(origin_vectors), datum_radii + origin_radii


def _check_interface_action(
    action: dict[str, Any],
    channel_rows: list[dict[str, Any]],
    source_owner: dict[str, Any],
    axis_id: str,
    interface_type: str,
    label: str,
) -> tuple[list[float], list[float]]:
    expected_first, expected_radius = _sum_channel_force(channel_rows, "first")
    expected_second = _vec_scale(-1.0, expected_first)
    _require(action.get("axis_id") == axis_id, f"{label}: axis id changed")
    _require(action.get("role") == source_owner.get("role"), f"{label}: physical role changed")
    _require(action.get("first") == source_owner.get("first"), f"{label}: first physical receiver changed")
    _require(action.get("second") == source_owner.get("second"), f"{label}: second physical receiver changed")
    _assert_metadata_vector(action, "axis", _vector(source_owner.get("axis"), label + " source bolt axis"), label)
    if interface_type == "lateral":
        point = _vector(source_owner.get("point"), label + " source point")
        _assert_metadata_vector(action, "point", point, label)
        basis = source_owner.get("force_basis")
        _require(isinstance(basis, list) and len(basis) == 3, f"{label}: missing reported lateral force basis")
        for index in range(3):
            _assert_vector_close(action.get("force_basis", [None] * 3)[index], _vector(basis[index], label + " source basis"), f"{label} force basis[{index}]", absolute_tolerance=1e-12)
    else:
        first_point = _vector(source_owner.get("first_point"), label + " source first point")
        second_point = _vector(source_owner.get("second_point"), label + " source second point")
        _assert_metadata_vector(action, "first_point", first_point, label)
        _assert_metadata_vector(action, "second_point", second_point, label)
        _assert_metadata_vector(action, "point", first_point, label)
        _assert_metadata_vector(action, "scalar_normal", _vector(source_owner.get("scalar_normal"), label + " scalar normal"), label, tolerance=1e-12)
    _assert_vector_close(action.get("force_on_first_xyz_n"), expected_first, label + " first-body interface force")
    _assert_vector_close(action.get("force_on_second_xyz_n"), expected_second, label + " second-body interface force")
    _assert_vector_close(action.get("force_rounding_radius_xyz_n"), expected_radius, label + " interface force radius")
    _require(
        action.get("source_row_ids") == [row["source"]["source_row_id"] for row in channel_rows],
        f"{label}: source row ids changed",
    )
    inventory_rows = action.get("source_inventory_rows")
    _require(isinstance(inventory_rows, list) and len(inventory_rows) == len(channel_rows), f"{label}: source inventory coverage changed")
    for row, source_row in zip(inventory_rows, channel_rows):
        _require(row.get("source_inventory_row_index") == source_row["source"]["source_inventory_row_index"], f"{label}: source inventory row index changed")
        _require(row.get("source_row_id") == source_row["source"]["source_row_id"], f"{label}: source inventory row id changed")
        _require(row.get("source_connection_name") == source_row["source"]["connection_name"], f"{label}: source connection name changed")
    pair_residual = _vec_add(
        _vector(action.get("force_on_first_xyz_n"), label + " first action"),
        _vector(action.get("force_on_second_xyz_n"), label + " second action"),
    )
    pair_radius = _vec_scale(2.0, _vector(action.get("force_rounding_radius_xyz_n"), label + " action radius"))
    for component in range(3):
        _require(abs(pair_residual[component]) <= pair_radius[component] + _arithmetic_tolerance(pair_residual[component]), f"{label}: reported physical actions fail action/reaction")
    return expected_first, expected_radius


def _check_interface_report_row(
    interface_actions: dict[str, Any],
    connection_name: str,
    expected_action: dict[str, Any],
    expected_first: list[float],
    expected_radius: list[float],
    label: str,
) -> None:
    row = interface_actions.get(connection_name)
    _require(isinstance(row, dict), f"{label}: retained interface row missing from full boundary")
    for key in ("first", "second", "role", "axis_id", "source_row_ids", "source_inventory_rows", "public_connector_name"):
        _require(row.get(key) == expected_action.get(key), f"{label}: full-boundary row {key} differs from retained axis action")
    _assert_vector_close(row.get("force_on_first_xyz_n"), expected_first, label + " full-boundary first force")
    _assert_vector_close(row.get("force_on_second_xyz_n"), _vec_scale(-1.0, expected_first), label + " full-boundary second force")
    _assert_vector_close(row.get("force_rounding_radius_xyz_n"), expected_radius, label + " full-boundary force radius")


def _check_individual_wrenches(
    receiver: dict[str, Any],
    role_expectations: list[dict[str, Any]],
    datum: list[float],
    side: str,
    label: str,
) -> None:
    rows = receiver.get("individual_interface_wrenches")
    _require(isinstance(rows, list) and len(rows) == 2, f"{label}: expected two retained source interface wrenches")
    by_role: dict[str, dict[str, Any]] = {}
    for row in rows:
        _require(isinstance(row, dict), f"{label}: malformed individual interface wrench")
        role = str(row.get("role"))
        _require(role not in by_role, f"{label}: duplicate individual wrench role {role}")
        by_role[role] = row
    _require(set(by_role) == {entry["role"] for entry in role_expectations}, f"{label}: individual wrench roles differ from the 2+1 source channels")
    for entry in role_expectations:
        row = by_role[entry["role"]]
        _assert_vector_close(row.get("point_xyz_mm"), entry["point"], label + " source wrench point", absolute_tolerance=1e-8)
        _assert_vector_close(row.get("force_xyz_n"), entry["force"], label + " source wrench force")
        expected_datum_moment = _cross(_vec_sub(entry["point"], datum), entry["force"])
        expected_origin_moment = _cross(entry["point"], entry["force"])
        datum_scale = _cross_roundoff_scale(_vec_sub(entry["point"], datum), entry["force"])
        origin_scale = _cross_roundoff_scale(entry["point"], entry["force"])
        _assert_vector_close(row.get("moment_about_reporting_datum_xyz_nmm"), expected_datum_moment, label + " source wrench datum moment", scales=datum_scale)
        _assert_vector_close(row.get("moment_about_origin_xyz_nmm"), expected_origin_moment, label + " source wrench origin moment", scales=origin_scale)


def _check_combined_receiver_actions(
    bolt_state: dict[str, Any],
    axis_id: str,
    channels: list[dict[str, Any]],
    owner: dict[str, Any],
    source_datum_by_body: dict[str, list[float]],
    label: str,
) -> None:
    combined = bolt_state.get("combined_receiver_actions")
    _require(isinstance(combined, dict) and set(combined) == {"first", "second"}, f"{label}: combined receiver actions must have first/second entries")
    lateral = [row for row in channels if row["source"]["family"] == "bilateral_spring2"]
    axial = [row for row in channels if row["source"]["family"] == "unilateral_springa"]
    _require(len(lateral) == 2 and len(axial) == 1, f"{label}: combined action does not cover two lateral and one axial source")
    role_channels = [
        {"role": "retained_bolt_lateral_plane", "channels": lateral, "owner": lateral[0]["source"]["owner"]},
        {"role": "physical_bolt_outer_seat_tension", "channels": axial, "owner": axial[0]["source"]["owner"]},
    ]
    for side in ("first", "second"):
        row = combined[side]
        _require(isinstance(row, dict), f"{label}: malformed {side} combined receiver action")
        receiver_name = str(owner.get(side, ""))
        _require(row.get("receiver_member_id") == receiver_name, f"{label}: {side} receiver member changed")
        expected_datum = source_datum_by_body.get(receiver_name)
        _require(expected_datum is not None, f"{label}: missing authenticated datum for {receiver_name}")
        _assert_vector_close(row.get("reporting_datum_xyz_mm"), expected_datum, f"{label} {side} authenticated datum", absolute_tolerance=1e-9)
        force_terms: list[list[float]] = []
        force_radius_terms: list[list[float]] = []
        datum_moment_terms: list[list[float]] = []
        origin_moment_terms: list[list[float]] = []
        datum_moment_scales = [0.0, 0.0, 0.0]
        origin_moment_scales = [0.0, 0.0, 0.0]
        datum_moment_radii = [0.0, 0.0, 0.0]
        origin_moment_radii = [0.0, 0.0, 0.0]
        individual_expectations: list[dict[str, Any]] = []
        for group in role_channels:
            source_owner = group["owner"]
            point = _vector(
                source_owner.get("point") if group["role"] == "retained_bolt_lateral_plane"
                else source_owner.get("first_point" if side == "first" else "second_point"),
                f"{label} {side} {group['role']} point",
            )
            group_force, _ = _sum_channel_force(group["channels"], side)
            force_terms.append(group_force)
            individual_expectations.append({"role": group["role"], "point": point, "force": group_force})
            datum_moment, origin_moment, radii = _sum_channel_moment(group["channels"], point, expected_datum, side)
            datum_moment_terms.append(datum_moment)
            origin_moment_terms.append(origin_moment)
            datum_moment_radii = _vec_add(datum_moment_radii, radii[:3])
            origin_moment_radii = _vec_add(origin_moment_radii, radii[3:])
            for channel in group["channels"]:
                force_radius_terms.append(channel["force_radius"])
                force_for_side = channel["force_first"] if side == "first" else _vec_scale(-1.0, channel["force_first"])
                dscale = _cross_roundoff_scale(_vec_sub(point, expected_datum), force_for_side)
                oscale = _cross_roundoff_scale(point, force_for_side)
                datum_moment_scales = _vec_add(datum_moment_scales, dscale)
                origin_moment_scales = _vec_add(origin_moment_scales, oscale)
        expected_force = _vec_sum(force_terms)
        expected_force_radius = _vec_sum(force_radius_terms)
        expected_datum_moment = _vec_sum(datum_moment_terms)
        expected_origin_moment = _vec_sum(origin_moment_terms)
        _assert_vector_close(row.get("force_xyz_n"), expected_force, f"{label} {side} combined signed force")
        _assert_vector_close(row.get("force_radius_xyz_n"), expected_force_radius, f"{label} {side} combined force radius")
        _assert_vector_close(
            row.get("moment_about_reporting_datum_xyz_nmm"),
            expected_datum_moment,
            f"{label} {side} combined datum moment",
            scales=datum_moment_scales,
        )
        _assert_vector_close(
            row.get("moment_about_origin_xyz_nmm"),
            expected_origin_moment,
            f"{label} {side} combined origin moment",
            scales=origin_moment_scales,
        )
        _assert_vector_close(
            row.get("moment_radius_about_reporting_datum_xyz_nmm"),
            datum_moment_radii,
            f"{label} {side} datum moment radius",
        )
        _assert_vector_close(
            row.get("moment_radius_about_origin_xyz_nmm"),
            origin_moment_radii,
            f"{label} {side} origin moment radius",
        )
        _check_individual_wrenches(row, individual_expectations, expected_datum, side, f"{label} {side}")
        transported_origin = _vec_add(expected_datum_moment, _cross(expected_datum, expected_force))
        transport_scale = _vec_add(datum_moment_scales, _cross_roundoff_scale(expected_datum, expected_force))
        _assert_vector_close(
            row.get("moment_about_origin_xyz_nmm"),
            transported_origin,
            f"{label} {side} datum-to-origin moment transport",
            scales=transport_scale,
        )


def _audit_one_state(
    report_state: dict[str, Any],
    case_id: str,
    increment_index: int,
    native_time: float,
    block: dict[str, Any],
    all_body_increment: dict[str, Any],
    source_axes: dict[str, dict[str, list[dict[str, Any]]]],
    report: dict[str, Any],
) -> int:
    load_factor = _finite_number(report_state.get("load_factor"), f"{case_id} report load factor")
    _assert_scalar_close(load_factor, native_time, f"{case_id} report/native load factor", absolute_tolerance=6e-8)
    _require(report_state.get("increment_index") == increment_index, f"{case_id} load factor {load_factor:g}: increment index changed")
    body_balances = report_state.get("body_balances")
    _require(isinstance(body_balances, dict) and set(body_balances) == EXPECTED_RECEIVER_BODIES, f"{case_id} state: body balance inventory changed")
    audit_body_eq = all_body_increment.get("body_equilibrium")
    _require(isinstance(audit_body_eq, dict), f"{case_id} frozen source audit increment lacks body equilibrium map")
    case_record = _dict_key(report.get("cases"), case_id, "report.cases")
    report_datums = case_record.get("reporting_datums_xyz_mm")
    _require(isinstance(report_datums, dict) and set(report_datums) == EXPECTED_RECEIVER_BODIES, f"{case_id}: report datum map differs from the eight authenticated receivers")
    source_datum_by_body: dict[str, list[float]] = {}
    for member in EXPECTED_RECEIVER_BODIES:
        source_record = _dict_key(audit_body_eq, member, f"{case_id} frozen body equilibrium")
        source_datum = _vector(source_record.get("reference_xyz_mm"), f"{case_id} {member} authenticated audit reference")
        source_datum_by_body[member] = source_datum
        _assert_vector_close(report_datums.get(member), source_datum, f"{case_id} case reporting datum {member}", absolute_tolerance=1e-9)
        _assert_vector_close(
            body_balances[member].get("datum_global_xyz_mm"),
            source_datum,
            f"{case_id} state reporting datum {member}",
            absolute_tolerance=1e-9,
        )
    _require(
        isinstance(case_record.get("reporting_datum_source"), str)
        and case_record["reporting_datum_source"].startswith("authenticated all-body audit reference"),
        f"{case_id}: report does not identify authenticated all-body audit datum source",
    )

    bolt_states = report_state.get("bolt_states")
    _require(isinstance(bolt_states, dict) and set(bolt_states) == set(source_axes), f"{case_id} state: retained bolt-state axis inventory changed")
    interface_actions = report_state.get("interface_actions")
    _require(isinstance(interface_actions, dict), f"{case_id} state: full boundary interface_actions is missing")
    checks = 0
    for axis_id, source_set in source_axes.items():
        label = f"{case_id} load {load_factor:g} axis {axis_id}"
        bolt_state = _dict_key(bolt_states, axis_id, f"{case_id} bolt_states")
        all_sources = source_set["lateral"] + source_set["axial"]
        channel_reports = _find_channel_report(bolt_state, all_sources, label)
        channel_results: list[dict[str, Any]] = []
        for source in all_sources:
            source_key = (source["source_row_id"], source["source_inventory_row_index"])
            channel = channel_reports[source_key]
            channel_results.append(_check_report_channel(channel, source, block, label))
            checks += 1

        lateral_results = [
            next(result for result in channel_results if result["source"]["source_inventory_row_index"] == source["source_inventory_row_index"])
            for source in source_set["lateral"]
        ]
        axial_result = next(result for result in channel_results if result["source"]["family"] == "unilateral_springa")
        bolt_lateral = bolt_state.get("lateral_interface_action")
        bolt_axial = bolt_state.get("axial_interface_action")
        _require(isinstance(bolt_lateral, dict) and isinstance(bolt_axial, dict), f"{label}: missing saved lateral/axial interface action")
        lateral_owner = source_set["lateral"][0]["owner"]
        axial_owner = source_set["axial"][0]["owner"]
        lateral_force, lateral_radius = _check_interface_action(bolt_lateral, lateral_results, lateral_owner, axis_id, "lateral", label + " lateral interface")
        axial_force, axial_radius = _check_interface_action(bolt_axial, [axial_result], axial_owner, axis_id, "axial", label + " axial interface")
        _check_interface_report_row(
            interface_actions,
            source_set["lateral"][0]["connection_name"],
            bolt_lateral,
            lateral_force,
            lateral_radius,
            label + " lateral full-boundary interface",
        )
        _check_interface_report_row(
            interface_actions,
            source_set["axial"][0]["connection_name"],
            bolt_axial,
            axial_force,
            axial_radius,
            label + " axial full-boundary interface",
        )
        _check_combined_receiver_actions(
            bolt_state,
            axis_id,
            channel_results,
            lateral_owner,
            source_datum_by_body,
            label,
        )
    return checks


def audit(report_path: Path) -> dict[str, Any]:
    try:
        report_bytes = report_path.read_bytes()
    except OSError as error:
        raise OracleError(f"Cannot read produced report {report_path}: {error}") from error
    report_hash = _sha256(report_bytes)
    try:
        report = json.loads(report_bytes)
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise OracleError(f"Produced report is not valid JSON: {error}") from error
    _require(isinstance(report, dict), "Produced report root is not an object")
    _require(report.get("schema") == "current_retained_frame_bolt_load_path/v1", "Produced report schema changed")
    _require(report.get("candidate") == "compact-floor-flush-wood-joints-development", "Produced report candidate changed")
    _require(report.get("geometry_revision_id") == "led-clearance-2x6-runner-seated-blocks-v1", "Produced report geometry revision changed")
    for flag in (
        "native_solve_executed",
        "qualified_for_design",
        "mechanical_acceptance",
        "joint_demand_accepted",
        "floor_capacity_established",
        "friction_qualified",
        "joint_accepted",
        "fabrication_release",
    ):
        _require(report.get(flag) is False, f"Produced report must preserve {flag}=false")

    freeze, freeze_hash = _read_json(FREEZE_PATH)
    _require(freeze_hash == PINNED_FREEZE_SHA256, "Pinned upper-frame freeze SHA-256 changed")
    _check_report_input_pin(report, FREEZE_PATH, PINNED_FREEZE_SHA256)
    _require(freeze.get("schema") == "upper-frame-review-freeze/v1", "Frozen upper-frame review schema changed")
    _require(freeze.get("candidate") == "compact-floor-flush-wood-joints-development", "Frozen candidate changed")
    _require(freeze.get("geometry_revision_id") == "led-clearance-2x6-runner-seated-blocks-v1", "Frozen geometry revision changed")
    _require(freeze.get("scope") == "Four uppermost cleats, sixteen existing bolts. Conditional source responses only. No solver run, model edit or acceptance.", "Frozen source scope changed")
    cases = freeze.get("cases")
    _require(isinstance(cases, dict) and set(cases) == EXPECTED_CASES, "Frozen source case inventory changed")

    projection_bytes = _read_bytes(PROJECTION_PATH)
    projection_hash = _sha256(projection_bytes)
    _require(projection_hash == PINNED_PROJECTION_SHA256, "Pinned physical-connector projection SHA-256 changed")
    _check_report_input_pin(report, PROJECTION_PATH, PINNED_PROJECTION_SHA256)
    try:
        projection = json.loads(projection_bytes)
    except json.JSONDecodeError as error:
        raise OracleError(f"Pinned physical-connector projection JSON is invalid: {error}") from error
    _require(isinstance(projection, dict), "Pinned physical-connector projection is not an object")

    models: dict[str, dict[str, Any]] = {}
    dat_blocks: dict[str, dict[float, dict[str, Any]]] = {}
    audit_records: dict[str, dict[str, Any]] = {}
    input_hashes: dict[str, Any] = {
        str(FREEZE_PATH): freeze_hash,
        str(PROJECTION_PATH): projection_hash,
        "report": report_hash,
        "cases": {},
    }
    for case_id in sorted(EXPECTED_CASES):
        case_freeze = cases[case_id]
        model, model_hash = _require_source_pin(case_freeze.get("model"), "model", REPOSITORY_ROOT, case_id)
        native_data, native_hash = _require_source_pin(case_freeze.get("native_data"), "native_data", REPOSITORY_ROOT, case_id)
        all_body_audit, audit_hash = _require_source_pin(case_freeze.get("all_body_audit"), "all_body_audit", REPOSITORY_ROOT, case_id)
        _check_report_source_pin(report, case_id, "model", case_freeze["model"])
        _check_report_source_pin(report, case_id, "native_data", case_freeze["native_data"])
        _check_report_source_pin(report, case_id, "all_body_audit", case_freeze["all_body_audit"])
        models[case_id] = model
        dat_blocks[case_id] = _parse_force_blocks(native_data["text"], case_id + " frozen native DAT")
        audit_records[case_id] = all_body_audit
        input_hashes["cases"][case_id] = {
            "model": {"path": case_freeze["model"]["path"], "sha256": model_hash},
            "native_data": {"path": case_freeze["native_data"]["path"], "sha256": native_hash},
            "all_body_audit": {"path": case_freeze["all_body_audit"]["path"], "sha256": audit_hash},
        }

    _validate_frozen_datum_constancy(audit_records)
    source_maps, retained_axes = _build_source_map(models, projection)
    _require(set(report.get("axis_register", {})) == retained_axes, "Produced report retained axis register differs from frozen twelve-axis source")
    candidate_axes = report.get("candidate_bolt_axis_ids_separate")
    _require(isinstance(candidate_axes, list) and len(candidate_axes) == 92 and len(set(candidate_axes)) == 92, "Produced report must keep the separate 92 candidate axes distinct")
    _require(not (set(candidate_axes) & retained_axes), "Produced report mixes candidate axes with the retained-frame raw oracle scope")
    _require(set(report.get("cases", {})) == EXPECTED_CASES, "Produced report case inventory changed")
    _require(report.get("receiver_bodies") == sorted(EXPECTED_RECEIVER_BODIES), "Produced report receiver-body set changed")

    expected_counts = {
        "retained_axes": 12,
        "candidate_axes_separate": 92,
        "states": 21,
        "bolt_states": 252,
        "combined_receiver_wrenches": 504,
        "physical_interface_actions_retained": 504,
        "complete_body_states": 168,
        "scalar_retained_channel_states": 756,
    }
    counts = report.get("counts")
    _require(isinstance(counts, dict), "Produced report counts are missing")
    for key, expected in expected_counts.items():
        _require(counts.get(key) == expected, f"Produced report count {key} must be {expected}")
    _require(counts.get("receiver_memberships") == 24, "Produced report receiver-membership count changed")

    report_states = report.get("states")
    _require(isinstance(report_states, list) and len(report_states) == 21, "Produced report must contain 21 native source states")
    states_by_case: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for state in report_states:
        _require(isinstance(state, dict), "Produced report contains a malformed state")
        case_id = state.get("case_id")
        _require(case_id in EXPECTED_CASES, f"Produced report contains unknown case state {case_id!r}")
        states_by_case[str(case_id)].append(state)

    checked_channels = 0
    checked_states = 0
    checked_datums = 0
    for case_id in sorted(EXPECTED_CASES):
        blocks = dat_blocks[case_id]
        times = sorted(blocks)
        _require(len(times) == 7, f"{case_id}: frozen DAT must contain seven retained load states")
        state_rows = states_by_case.get(case_id, [])
        _require(len(state_rows) == 7, f"{case_id}: report must contain seven states")
        state_rows.sort(key=lambda row: _finite_number(row.get("load_factor"), f"{case_id} load factor"))
        audit_increments = audit_records[case_id].get("increments")
        _require(isinstance(audit_increments, list) and len(audit_increments) == 7, f"{case_id}: frozen all-body audit must contain seven increments")
        audit_by_time: dict[float, dict[str, Any]] = {}
        for increment in audit_increments:
            _require(isinstance(increment, dict), f"{case_id}: malformed frozen all-body audit increment")
            time_value = _finite_number(increment.get("time"), f"{case_id} all-body audit time")
            _require(time_value not in audit_by_time, f"{case_id}: duplicate frozen all-body audit time")
            audit_by_time[time_value] = increment
        _require(set(audit_by_time) == set(times), f"{case_id}: frozen all-body audit and DAT time sets differ")
        for index, (state, native_time) in enumerate(zip(state_rows, times)):
            matching_audit = audit_by_time[native_time]
            _assert_scalar_close(
                matching_audit.get("load_factor"),
                native_time,
                f"{case_id} frozen all-body audit load factor",
                absolute_tolerance=6e-8,
            )
            checked_channels += _audit_one_state(
                state,
                case_id,
                index,
                native_time,
                blocks[native_time],
                matching_audit,
                source_maps[case_id],
                report,
            )
            checked_states += 1
            checked_datums += len(EXPECTED_RECEIVER_BODIES)

    _require(checked_channels == 21 * 36, f"Raw oracle checked {checked_channels} channels; expected 756")
    return {
        "schema": "retained_frame_bolt_raw_oracle/v1",
        "status": "PASS_RAW_TOKEN_FORCE_AND_WRENCH_RECONCILIATION",
        "report_path": str(report_path.resolve()),
        "report_sha256": report_hash,
        "input_hashes": input_hashes,
        "scope": {
            "retained_axis_count": 12,
            "candidate_axis_count_separate": 92,
            "states": checked_states,
            "spring2_channel_states": 21 * 24,
            "springa_channel_states": 21 * 12,
            "raw_channel_states": checked_channels,
            "combined_endpoint_wrenches": 21 * 12 * 2,
            "authenticated_receiver_datums": checked_datums,
        },
        "native_solve_executed": False,
        "qualified_for_design": False,
        "mechanical_acceptance": False,
        "joint_demand_accepted": False,
        "floor_capacity_established": False,
        "friction_qualified": False,
        "joint_accepted": False,
        "fabrication_release": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report", required=True, type=Path, help="produced retained-frame report JSON")
    args = parser.parse_args()
    try:
        result = audit(args.report)
    except OracleError as error:
        print(f"raw_oracle: FAIL: {error}", file=sys.stderr)
        return 1
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
