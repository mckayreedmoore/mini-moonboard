"""Prepare a source-only station and section-plane plan for the right corner.

This module consumes already loaded JSON-like records. It does not read files,
import CAD, replay a model, or turn source actions into section resultants.
"""

from __future__ import annotations

import hashlib
import json
import math
from collections import defaultdict
from collections.abc import Mapping, Sequence
from typing import Any

CANDIDATE = "compact-floor-flush-wood-joints-development"
REVISION = "led-clearance-2x6-runner-seated-blocks-v1"
CASE_IDS = ("a1-rear", "a12-rear", "k12-rear")
MEMBERS = frozenset(
    {
        "base_header",
        "base_post_outer_right",
        "base_side_right",
        "knee_outer_right_spine",
        "knee_outer_right_inner_frame_block",
    }
)
AXIS_RECEIVERS = {
    "knee_outer_right_inner_header_1": frozenset(
        {"base_header", "knee_outer_right_inner_frame_block"}
    ),
    "knee_outer_right_inner_header_2": frozenset(
        {"base_header", "knee_outer_right_inner_frame_block"}
    ),
    "knee_outer_right_post_1": frozenset(
        {"base_post_outer_right", "knee_outer_right_spine"}
    ),
    "knee_outer_right_post_2": frozenset(
        {"base_post_outer_right", "knee_outer_right_spine"}
    ),
    "knee_outer_right_side_1": frozenset(
        {
            "base_side_right",
            "knee_outer_right_inner_frame_block",
            "knee_outer_right_spine",
        }
    ),
    "knee_outer_right_side_2": frozenset(
        {
            "base_side_right",
            "knee_outer_right_inner_frame_block",
            "knee_outer_right_spine",
        }
    ),
}

FRAME_TOLERANCE = 1.0e-6
AXIS_PARALLEL_TOLERANCE = 1.0e-6
AXIS_LINE_TOLERANCE_MM = 1.0e-5
POINT_TOLERANCE_MM = 1.0e-8
LINEAR_TOLERANCE_MM = 1.0e-5
PLANE_COINCIDENCE_TOLERANCE_MM = 1.0e-6
EXPECTED_INTERFACE_COUNT = 338


class PlanRefusal(ValueError):
    """A saved source identity, frame, or station relation is not exact."""


def require(condition: bool, message: str) -> None:
    if not condition:
        raise PlanRefusal(message)


def _finite(value: Any, label: str) -> float:
    require(
        isinstance(value, (int, float)) and not isinstance(value, bool),
        f"{label} must be numeric",
    )
    result = float(value)
    require(math.isfinite(result), f"{label} must be finite")
    return result


def _vec3(value: Any, label: str) -> list[float]:
    require(
        isinstance(value, Sequence)
        and not isinstance(value, (str, bytes))
        and len(value) == 3,
        f"{label} must be a three-vector",
    )
    return [_finite(value[index], f"{label}[{index}]") for index in range(3)]


def _dot(first: Sequence[float], second: Sequence[float]) -> float:
    return math.fsum(a * b for a, b in zip(first, second, strict=True))


def _sub(first: Sequence[float], second: Sequence[float]) -> list[float]:
    return [a - b for a, b in zip(first, second, strict=True)]


def _cross(first: Sequence[float], second: Sequence[float]) -> list[float]:
    return [
        first[1] * second[2] - first[2] * second[1],
        first[2] * second[0] - first[0] * second[2],
        first[0] * second[1] - first[1] * second[0],
    ]


def _norm(vector: Sequence[float]) -> float:
    return math.sqrt(_dot(vector, vector))


def _same_vector(
    actual: Any, expected: Any, label: str, tolerance: float = LINEAR_TOLERANCE_MM
) -> None:
    first = _vec3(actual, label)
    second = _vec3(expected, label)
    require(
        _norm(_sub(first, second)) <= tolerance,
        f"{label} differs between saved sources",
    )


def _same_number(
    actual: Any, expected: Any, label: str, tolerance: float = LINEAR_TOLERANCE_MM
) -> None:
    first = _finite(actual, label)
    second = _finite(expected, label)
    require(abs(first - second) <= tolerance, f"{label} differs between saved sources")


def _index_records(rows: Any, field: str, label: str) -> dict[str, dict[str, Any]]:
    require(isinstance(rows, list), f"{label} must be a list")
    result: dict[str, dict[str, Any]] = {}
    for index, row in enumerate(rows):
        require(isinstance(row, Mapping), f"{label}[{index}] must be an object")
        identity = row.get(field)
        require(
            isinstance(identity, str) and identity,
            f"{label}[{index}] has no {field}",
        )
        require(identity not in result, f"{label} has duplicate {field} {identity}")
        result[identity] = dict(row)
    return result


def _unit_frame(
    grain: Any, section_u: Any, section_v: Any, label: str
) -> tuple[list[float], list[float], list[float]]:
    g = _vec3(grain, f"{label} grain")
    u = _vec3(section_u, f"{label} section_u")
    v = _vec3(section_v, f"{label} section_v")
    for name, axis in (("grain", g), ("section_u", u), ("section_v", v)):
        require(
            abs(_norm(axis) - 1.0) <= FRAME_TOLERANCE,
            f"{label} {name} axis is not unit",
        )
    require(
        abs(_dot(g, u)) <= FRAME_TOLERANCE
        and abs(_dot(g, v)) <= FRAME_TOLERANCE
        and abs(_dot(u, v)) <= FRAME_TOLERANCE,
        f"{label} frame is not orthogonal",
    )
    require(
        abs(_dot(_cross(g, u), v) - 1.0) <= FRAME_TOLERANCE,
        f"{label} frame is not right-handed",
    )
    return g, u, v


def _stock_coordinates(
    point: Sequence[float], origin: Sequence[float], axes: Sequence[Sequence[float]]
) -> list[float]:
    relative = _sub(point, origin)
    return [_dot(relative, axis) for axis in axes]


def _stock_direction(
    direction: Sequence[float], axes: Sequence[Sequence[float]]
) -> list[float]:
    return [_dot(direction, axis) for axis in axes]


def _parallel_departure(first: Sequence[float], second: Sequence[float]) -> float:
    cosine = min(1.0, abs(_dot(first, second)))
    return math.sqrt(max(0.0, 1.0 - cosine * cosine))


def _line_distance(
    point: Sequence[float], datum: Sequence[float], direction: Sequence[float]
) -> float:
    offset = _sub(point, datum)
    along = _dot(offset, direction)
    return _norm([offset[index] - along * direction[index] for index in range(3)])


def _validate_report_identity(report: Mapping[str, Any], label: str) -> None:
    require(report.get("candidate") == CANDIDATE, f"{label} candidate differs")
    revision = report.get("geometry_revision_id", report.get("revision"))
    require(revision == REVISION, f"{label} revision differs")


def _member_frames(
    surfaces: Mapping[str, Any],
    envelopes: Mapping[str, Any],
    models_by_case: Mapping[str, Mapping[str, Any]],
) -> dict[str, dict[str, Any]]:
    surface_rows = _index_records(
        surfaces.get("records"), "member_id", "surface records"
    )
    envelope_rows = _index_records(
        envelopes.get("records"), "member_id", "stock envelope records"
    )
    frames: dict[str, dict[str, Any]] = {}

    for member_id in sorted(MEMBERS):
        require(
            member_id in surface_rows, f"missing finished surface member {member_id}"
        )
        require(
            member_id in envelope_rows, f"missing stock envelope member {member_id}"
        )
        surface = surface_rows[member_id]
        envelope = envelope_rows[member_id]
        stock = surface.get("stock_frame")
        step = surface.get("step_binding")
        proposed = envelope.get("proposed_frame")
        require(
            isinstance(stock, Mapping), f"{member_id} surface stock frame is missing"
        )
        require(
            isinstance(step, Mapping), f"{member_id} surface STEP binding is missing"
        )
        require(isinstance(proposed, Mapping), f"{member_id} envelope frame is missing")
        require(
            proposed.get("status") == "CONTAINED",
            f"{member_id} proposed stock frame is not contained",
        )
        require(
            stock.get("basis_source") == "reviewed proposed stock envelope g/q/r basis",
            f"{member_id} stock frame basis source is unsupported",
        )
        require(
            stock.get("datum_status")
            == "proposed minimum g/q/r corner; not a delivered-stock datum",
            f"{member_id} stock frame datum status is ambiguous",
        )

        basis = stock.get("basis_columns_global_xyz")
        require(
            isinstance(basis, Sequence)
            and not isinstance(basis, (str, bytes))
            and len(basis) == 3,
            f"{member_id} stock frame must contain g/q/r basis columns",
        )
        origin = _vec3(stock.get("origin_global_xyz_mm"), f"{member_id} stock origin")
        grain, section_u, section_v = _unit_frame(
            basis[0], basis[1], basis[2], f"{member_id} proposed g/q/r"
        )
        axes = (grain, section_u, section_v)
        for key, expected in (
            ("grain_axis_global_xyz", grain),
            ("section_q_axis_global_xyz", section_u),
            ("section_r_axis_global_xyz", section_v),
        ):
            _same_vector(
                proposed.get(key),
                expected,
                f"{member_id} envelope {key}",
                FRAME_TOLERANCE,
            )

        step_path = step.get("path")
        step_sha = step.get("file_sha256")
        step_size = step.get("size_bytes")
        require(
            isinstance(step_path, str) and step_path,
            f"{member_id} STEP path is missing",
        )
        require(
            isinstance(step_sha, str)
            and len(step_sha) == 64
            and all(character in "0123456789abcdef" for character in step_sha),
            f"{member_id} STEP digest is malformed",
        )
        require(
            isinstance(step_size, int) and step_size > 0,
            f"{member_id} STEP size is missing",
        )
        require(
            step.get("solid_count") == 1, f"{member_id} STEP is not one saved solid"
        )
        require(
            envelope.get("current_finished_step_path") == step_path
            and envelope.get("current_finished_step_sha256") == step_sha
            and envelope.get("current_finished_step_size_bytes") == step_size,
            f"{member_id} envelope STEP binding differs from surface register",
        )
        require(
            envelope.get("current_finished_solid_count") == 1,
            f"{member_id} envelope does not describe one current solid",
        )
        bounds = envelope.get("original_stock_containment", {}).get(
            "proposed_stock_bounds_g_q_r_mm"
        )
        require(
            isinstance(bounds, Sequence)
            and not isinstance(bounds, (str, bytes))
            and len(bounds) == 3,
            f"{member_id} stock envelope bounds are missing",
        )
        projected_origin = [_dot(origin, axis) for axis in axes]
        for index, bound in enumerate(bounds):
            require(
                isinstance(bound, Sequence)
                and not isinstance(bound, (str, bytes))
                and len(bound) == 2,
                f"{member_id} stock envelope bound {index} is malformed",
            )
            _same_number(
                projected_origin[index],
                _finite(bound[0], f"{member_id} stock bound minimum {index}"),
                f"{member_id} stock origin projection {index}",
            )

        first_model_geometry: dict[str, Any] | None = None
        for case_id in CASE_IDS:
            model = models_by_case[case_id]
            bodies = model.get("body_geometry")
            require(
                isinstance(bodies, Mapping), f"{case_id} model body geometry is missing"
            )
            body = bodies.get(member_id)
            require(isinstance(body, Mapping), f"{case_id} model lacks {member_id}")
            geometry = body.get("geometry_record")
            require(
                isinstance(geometry, Mapping),
                f"{case_id}/{member_id} geometry record is missing",
            )
            descriptor = geometry.get("source_descriptor")
            diagnostics = geometry.get("geometry_diagnostics")
            require(
                isinstance(descriptor, Mapping),
                f"{case_id}/{member_id} source descriptor is missing",
            )
            require(
                isinstance(diagnostics, Mapping),
                f"{case_id}/{member_id} geometry diagnostics are missing",
            )
            require(
                descriptor.get("member_id") == member_id
                and descriptor.get("step_path") == step_path
                and descriptor.get("step_sha256") == step_sha
                and diagnostics.get("geometry_source") == step_path
                and diagnostics.get("geometry_sha256") == step_sha,
                f"{case_id}/{member_id} source model STEP binding differs",
            )

            model_grain = _vec3(
                geometry.get("axis"), f"{case_id}/{member_id} model grain"
            )
            model_u = _vec3(
                geometry.get("section_u"), f"{case_id}/{member_id} model section_u"
            )
            model_v = _vec3(
                geometry.get("section_v"), f"{case_id}/{member_id} model section_v"
            )
            _unit_frame(
                model_grain, model_u, model_v, f"{case_id}/{member_id} model frame"
            )
            _same_vector(
                model_grain,
                grain,
                f"{case_id}/{member_id} model grain",
                FRAME_TOLERANCE,
            )
            # The source mesh reports (g, -r, q); the stock envelope reports (g, q, r).
            _same_vector(
                model_u,
                [-value for value in section_v],
                f"{case_id}/{member_id} model section_u",
                FRAME_TOLERANCE,
            )
            _same_vector(
                model_v,
                section_u,
                f"{case_id}/{member_id} model section_v",
                FRAME_TOLERANCE,
            )

            start = _vec3(geometry.get("start"), f"{case_id}/{member_id} model start")
            end = _vec3(geometry.get("end"), f"{case_id}/{member_id} model end")
            length = _finite(
                descriptor.get("length_mm"), f"{case_id}/{member_id} model length"
            )
            require(length > 0.0, f"{case_id}/{member_id} model length is not positive")
            _same_vector(
                _sub(end, start),
                [value * length for value in model_grain],
                f"{case_id}/{member_id} model start/end grain interval",
            )
            current_geometry = {
                "start_global_xyz_mm": start,
                "end_global_xyz_mm": end,
                "grain_axis_global_xyz": model_grain,
                "section_u_global_xyz": model_u,
                "section_v_global_xyz": model_v,
                "length_mm": length,
            }
            if first_model_geometry is None:
                first_model_geometry = current_geometry
            else:
                for key, value in current_geometry.items():
                    if key.endswith(("xyz_mm", "xyz")):
                        _same_vector(
                            value,
                            first_model_geometry[key],
                            f"{case_id}/{member_id} case-invariant {key}",
                        )
                    else:
                        _same_number(
                            value,
                            first_model_geometry[key],
                            f"{case_id}/{member_id} case-invariant {key}",
                        )

        require(
            first_model_geometry is not None,
            f"{member_id} has no source model geometry",
        )
        frames[member_id] = {
            "member_id": member_id,
            "origin_global_xyz_mm": origin,
            "grain_axis_global_xyz": grain,
            "section_u_global_xyz": section_u,
            "section_v_global_xyz": section_v,
            "step_path": step_path,
            "step_sha256": step_sha,
            "step_size_bytes": step_size,
            "frame_source": "saved proposed stock g/q/r frame from finished-surface and stock-envelope reports",
            "datum_status": stock["datum_status"],
            "source_model_geometry": first_model_geometry,
        }
    return frames


def _interface_groups_from_model(
    model: Mapping[str, Any], label: str
) -> dict[str, dict[str, Any]]:
    rows = model.get("raw_source_carrier_law_inventory_rows")
    require(isinstance(rows, list), f"{label} source interface inventory is missing")
    groups: dict[str, dict[str, Any]] = {}
    for source_index, raw in enumerate(rows):
        require(
            isinstance(raw, Mapping),
            f"{label} source interface row {source_index} is malformed",
        )
        name = raw.get("name")
        owner = raw.get("physical_owner")
        require(isinstance(name, str) and name, f"{label} source interface has no name")
        require(isinstance(owner, Mapping), f"{label}/{name} owner is missing")
        first, second = owner.get("first"), owner.get("second")
        require(
            isinstance(first, str)
            and isinstance(second, str)
            and raw.get("first_body") == first
            and raw.get("second_body") == second,
            f"{label}/{name} source owner endpoints disagree",
        )
        if first not in MEMBERS and second not in MEMBERS:
            continue
        group = groups.setdefault(name, {"owner": dict(owner), "source_indices": []})
        require(
            group["owner"] == dict(owner),
            f"{label}/{name} has conflicting owner metadata",
        )
        group["source_indices"].append(source_index)
    require(
        len(groups) == EXPECTED_INTERFACE_COUNT,
        f"{label} selected interface identity count is {len(groups)}, expected {EXPECTED_INTERFACE_COUNT}",
    )
    return groups


def _interface_inventory(
    boundary_report: Mapping[str, Any],
    models_by_case: Mapping[str, Mapping[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    case_reports = boundary_report.get("cases")
    require(
        isinstance(case_reports, Mapping), "whole-boundary case records are missing"
    )
    require(set(case_reports) == set(CASE_IDS), "whole-boundary case set differs")
    reference: dict[str, dict[str, Any]] | None = None
    scalar_count: int | None = None

    for case_id in CASE_IDS:
        case_report = case_reports[case_id]
        require(
            isinstance(case_report, Mapping),
            f"whole-boundary {case_id} record is malformed",
        )
        model = models_by_case[case_id]
        model_groups = _interface_groups_from_model(model, case_id)
        inventory = case_report.get("inventory")
        require(
            isinstance(inventory, list),
            f"whole-boundary {case_id} inventory is missing",
        )
        require(
            case_report.get("interface_count") == EXPECTED_INTERFACE_COUNT
            and len(inventory) == EXPECTED_INTERFACE_COUNT,
            f"whole-boundary {case_id} does not preserve 338 interface identities",
        )
        report_groups = _index_records(
            inventory, "source_connection_name", f"whole-boundary {case_id} interfaces"
        )
        require(
            set(report_groups) == set(model_groups),
            f"{case_id} interface names differ from its model",
        )
        for name, group in model_groups.items():
            report_row = report_groups[name]
            require(
                report_row.get("owner") == group["owner"]
                and report_row.get("source_indices") == group["source_indices"],
                f"{case_id}/{name} boundary identity differs from model source rows",
            )
        current_scalar_count = sum(
            len(group["source_indices"]) for group in model_groups.values()
        )
        require(
            case_report.get("scalar_source_count") == current_scalar_count,
            f"{case_id} scalar source count differs from model rows",
        )
        if reference is None:
            reference = model_groups
            scalar_count = current_scalar_count
        else:
            require(
                set(model_groups) == set(reference),
                f"{case_id} interface identities differ across model cases",
            )
            require(
                current_scalar_count == scalar_count,
                f"{case_id} scalar source count differs across model cases",
            )
            for name, group in model_groups.items():
                original = reference[name]
                require(
                    group["owner"] == original["owner"]
                    and group["source_indices"] == original["source_indices"],
                    f"{case_id}/{name} physical interface differs across model cases",
                )
        datums = case_report.get("reporting_datums_xyz_mm")
        require(isinstance(datums, Mapping), f"{case_id} reporting datums are missing")
        for member_id in sorted(MEMBERS):
            geometry = model["body_geometry"][member_id]["geometry_record"]
            expected = [
                (a + b) / 2.0
                for a, b in zip(
                    _vec3(geometry["start"], f"{case_id}/{member_id} start"),
                    _vec3(geometry["end"], f"{case_id}/{member_id} end"),
                    strict=True,
                )
            ]
            _same_vector(
                datums.get(member_id),
                expected,
                f"{case_id}/{member_id} reporting datum",
            )

    require(reference is not None, "whole-boundary interface reference is empty")
    identities: list[dict[str, Any]] = []
    point_candidates: list[dict[str, Any]] = []
    used_scalar_indices: set[int] = set()
    in_scope_endpoint_count = 0

    for name in sorted(reference):
        group = reference[name]
        owner = group["owner"]
        indices = group["source_indices"]
        require(
            all(
                isinstance(index, int) and not isinstance(index, bool)
                for index in indices
            ),
            f"{name} scalar source indices are malformed",
        )
        require(
            not used_scalar_indices.intersection(indices),
            f"{name} reuses scalar source indices",
        )
        used_scalar_indices.update(indices)
        endpoints: list[dict[str, Any]] = []
        for endpoint in ("first", "second"):
            member_id = owner[endpoint]
            point_value = owner.get(f"{endpoint}_point", owner.get("point"))
            point = _vec3(point_value, f"{name}/{endpoint} point")
            in_scope = member_id in MEMBERS
            endpoint_key = f"interface:{name}:endpoint:{endpoint}"
            endpoint_row = {
                "endpoint": endpoint,
                "member_id": member_id,
                "point_global_xyz_mm": point,
                "in_scope": in_scope,
            }
            if in_scope:
                in_scope_endpoint_count += 1
                endpoint_row["point_identity_key"] = endpoint_key
                point_candidates.append(
                    {
                        "identity_key": endpoint_key,
                        "kind": "interface_endpoint",
                        "member_id": member_id,
                        "point_global_xyz_mm": point,
                        "source_identity": {
                            "source_connection_name": name,
                            "endpoint": endpoint,
                            "source_role": owner.get("role"),
                            "source_indices": list(indices),
                            "source_cases": list(CASE_IDS),
                        },
                    }
                )
            endpoints.append(endpoint_row)
        identities.append(
            {
                "identity_key": f"interface:{name}",
                "source_connection_name": name,
                "source_indices": list(indices),
                "source_scalar_count": len(indices),
                "source_cases": list(CASE_IDS),
                "source_owner": owner,
                "endpoints": endpoints,
            }
        )

    require(
        len(identities) == EXPECTED_INTERFACE_COUNT,
        "whole-boundary interface identity coverage is incomplete",
    )
    require(
        in_scope_endpoint_count == 380,
        f"whole-boundary in-scope endpoint count is {in_scope_endpoint_count}, expected 380",
    )
    return identities, point_candidates


def _load_node_inventory(
    models_by_case: Mapping[str, Mapping[str, Any]],
) -> list[dict[str, Any]]:
    reference: dict[tuple[str, int], list[float]] | None = None
    source_cases: dict[tuple[str, int], list[str]] = defaultdict(list)
    for case_id in CASE_IDS:
        model = models_by_case[case_id]
        loads = model.get("physical_body_loads")
        body_nodes = model.get("physical_body_nodes")
        all_nodes = model.get("nodes")
        require(
            isinstance(loads, Mapping), f"{case_id} physical body loads are missing"
        )
        require(
            isinstance(body_nodes, Mapping),
            f"{case_id} physical body node sets are missing",
        )
        require(
            isinstance(all_nodes, Mapping), f"{case_id} node coordinates are missing"
        )
        current: dict[tuple[str, int], list[float]] = {}
        for member_id in sorted(MEMBERS):
            load_map = loads.get(member_id)
            node_list = body_nodes.get(member_id)
            require(
                isinstance(load_map, Mapping),
                f"{case_id}/{member_id} loads are missing",
            )
            require(
                isinstance(node_list, list),
                f"{case_id}/{member_id} body node list is missing",
            )
            normalized_body_nodes: set[int] = set()
            for raw_node in node_list:
                require(
                    isinstance(raw_node, int)
                    and not isinstance(raw_node, bool)
                    and raw_node > 0,
                    f"{case_id}/{member_id} body node ID is malformed",
                )
                require(
                    raw_node not in normalized_body_nodes,
                    f"{case_id}/{member_id} has duplicate body nodes",
                )
                normalized_body_nodes.add(raw_node)
            for raw_node, raw_load in load_map.items():
                require(
                    isinstance(raw_node, str) and raw_node.isdigit(),
                    f"{case_id}/{member_id} load node key is malformed",
                )
                node_id = int(raw_node)
                require(
                    str(node_id) == raw_node and node_id > 0,
                    f"{case_id}/{member_id} load node ID is noncanonical",
                )
                require(
                    node_id in normalized_body_nodes,
                    f"{case_id}/{member_id} load node is outside its body node set",
                )
                _vec3(raw_load, f"{case_id}/{member_id}/node{node_id} load vector")
                point = _vec3(
                    all_nodes.get(raw_node), f"{case_id}/node{node_id} coordinates"
                )
                key = (member_id, node_id)
                require(
                    key not in current, f"{case_id} duplicates load node identity {key}"
                )
                current[key] = point
        if reference is None:
            reference = current
        else:
            require(
                set(current) == set(reference),
                f"{case_id} physical load node IDs differ across cases",
            )
            for key, point in current.items():
                _same_vector(
                    point,
                    reference[key],
                    f"{case_id}/{key} node coordinates",
                    POINT_TOLERANCE_MM,
                )
        for key in current:
            source_cases[key].append(case_id)

    require(reference is not None, "physical body load node inventory is empty")
    result: list[dict[str, Any]] = []
    for (member_id, node_id), point in sorted(reference.items()):
        require(
            source_cases[(member_id, node_id)] == list(CASE_IDS),
            f"load node {node_id} is absent from a source case",
        )
        result.append(
            {
                "identity_key": f"load:{member_id}:node:{node_id}",
                "kind": "physical_body_load_node",
                "member_id": member_id,
                "node_id": node_id,
                "point_global_xyz_mm": point,
                "source_cases": list(source_cases[(member_id, node_id)]),
                "source_identity": {
                    "node_id": node_id,
                    "source_cases": list(source_cases[(member_id, node_id)]),
                },
            }
        )
    return result


def _selected_axes(
    axis_features: Mapping[str, Any],
    surfaces: Mapping[str, Any],
    frames: Mapping[str, Mapping[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    groups = axis_features.get("source_axis_groups")
    require(isinstance(groups, Mapping), "axis-feature source groups are missing")
    candidate_group = groups.get("candidate_bolt_axes")
    require(isinstance(candidate_group, Mapping), "candidate bolt axes are missing")
    axes = candidate_group.get("axes")
    require(isinstance(axes, list), "candidate bolt axis rows are missing")
    selected: dict[str, dict[str, Any]] = {}
    for row in axes:
        require(isinstance(row, Mapping), "candidate bolt axis row is malformed")
        axis_id = row.get("axis_id")
        if axis_id not in AXIS_RECEIVERS:
            continue
        require(axis_id not in selected, f"duplicate selected bolt axis {axis_id}")
        require(
            row.get("axis_group") == "candidate_bolt_axes",
            f"{axis_id} source axis group differs",
        )
        selected[axis_id] = dict(row)
    require(
        set(selected) == set(AXIS_RECEIVERS),
        "six selected right-corner axes are incomplete",
    )

    surface_rows = _index_records(
        surfaces.get("records"), "member_id", "surface records"
    )
    feature_maps: dict[str, dict[str, dict[str, Any]]] = {}
    for member_id in MEMBERS:
        records = surface_rows[member_id].get("features")
        feature_maps[member_id] = _index_records(
            records, "feature_id", f"{member_id} features"
        )

    memberships: list[dict[str, Any]] = []
    bore_candidates: list[dict[str, Any]] = []
    selected_axis_rows: list[dict[str, Any]] = []
    used_features: set[tuple[str, str]] = set()
    for axis_id in sorted(selected):
        axis = selected[axis_id]
        source_fields = axis.get("source_axis_fields")
        require(
            isinstance(source_fields, Mapping),
            f"{axis_id} source axis fields are missing",
        )
        datum = _vec3(
            source_fields.get("datum_global_xyz_mm"), f"{axis_id} source axis datum"
        )
        direction = _vec3(
            source_fields.get("direction_global_xyz"),
            f"{axis_id} source axis direction",
        )
        require(
            abs(_norm(direction) - 1.0) <= FRAME_TOLERANCE,
            f"{axis_id} source direction is not unit",
        )
        extent = source_fields.get("finite_interval_from_datum_mm")
        require(
            isinstance(extent, Sequence)
            and not isinstance(extent, (str, bytes))
            and len(extent) == 2,
            f"{axis_id} modeled source interval is malformed",
        )
        interval = [_finite(value, f"{axis_id} source interval") for value in extent]
        require(
            interval[0] < interval[1],
            f"{axis_id} modeled source interval is not increasing",
        )
        semantics = source_fields.get("finite_extent_source_semantics")
        require(
            isinstance(semantics, Mapping),
            f"{axis_id} finite extent source semantics are missing",
        )
        selected_axis_rows.append(
            {
                "axis_id": axis_id,
                "axis_group": "candidate_bolt_axes",
                "source_axis_fields": {
                    "datum_global_xyz_mm": datum,
                    "direction_global_xyz": direction,
                    "finite_interval_from_datum_mm": interval,
                    "axis_length_mm": _finite(
                        source_fields.get("axis_length_mm"),
                        f"{axis_id} source axis length",
                    ),
                    "occupied_diameter_mm": _finite(
                        source_fields.get("occupied_diameter_mm"),
                        f"{axis_id} source diameter",
                    ),
                    "finite_extent_source_semantics": dict(semantics),
                },
            }
        )
        raw_memberships = axis.get("receiver_memberships")
        require(
            isinstance(raw_memberships, list),
            f"{axis_id} receiver memberships are missing",
        )
        members_for_axis: list[str] = []
        for raw_membership in raw_memberships:
            require(
                isinstance(raw_membership, Mapping),
                f"{axis_id} receiver membership is malformed",
            )
            membership = dict(raw_membership)
            member_id = membership.get("receiver_member_id")
            require(
                member_id in MEMBERS,
                f"{axis_id} has an out-of-scope receiver {member_id}",
            )
            members_for_axis.append(member_id)
            frame = frames[member_id]
            require(
                membership.get("binding_status")
                == "bound_to_current_finished_stock_frame"
                and membership.get("match_status") == "matched_bore_patch",
                f"{axis_id}/{member_id} receiver membership is not bound/matched",
            )
            matched_ids = membership.get("matched_feature_ids")
            require(
                isinstance(matched_ids, list)
                and len(matched_ids) == 1
                and isinstance(matched_ids[0], str),
                f"{axis_id}/{member_id} must match exactly one bore feature",
            )
            feature_id = matched_ids[0]
            feature_key = (member_id, feature_id)
            require(
                feature_key not in used_features,
                f"finished bore feature is reused: {feature_key}",
            )
            used_features.add(feature_key)
            diagnostics = membership.get("diagnostics")
            require(
                isinstance(diagnostics, Mapping),
                f"{axis_id}/{member_id} match diagnostics are missing",
            )
            require(
                diagnostics.get("eligible_bore_patches") == 1
                and diagnostics.get("coaxial_cylinder_features") == 1,
                f"{axis_id}/{member_id} bore match is ambiguous",
            )
            cylinder_candidates = membership.get("cylinder_surface_candidates")
            require(
                isinstance(cylinder_candidates, list)
                and len(cylinder_candidates) == 1
                and isinstance(cylinder_candidates[0], Mapping),
                f"{axis_id}/{member_id} cylinder candidates are missing or ambiguous",
            )
            candidate = cylinder_candidates[0]
            require(
                candidate.get("association_status") == "eligible_bore_patch"
                and candidate.get("feature_id") == feature_id
                and candidate.get("surface_kind") == "CYLINDER"
                and candidate.get("material_side_geometry") == "bore_like"
                and candidate.get("finite_interval_status")
                == "contained_in_source_finite_interval",
                f"{axis_id}/{member_id} candidate is not a contained bore patch",
            )

            binding = membership.get("current_finished_step_binding")
            require(
                isinstance(binding, Mapping),
                f"{axis_id}/{member_id} STEP binding is missing",
            )
            for field, expected in (
                ("path", frame["step_path"]),
                ("file_sha256", frame["step_sha256"]),
                ("size_bytes", frame["step_size_bytes"]),
                ("solid_count", 1),
            ):
                require(
                    binding.get(field) == expected,
                    f"{axis_id}/{member_id} STEP {field} differs",
                )

            membership_stock = membership.get("stock_frame")
            require(
                isinstance(membership_stock, Mapping),
                f"{axis_id}/{member_id} stock frame is missing",
            )
            member_surface = surface_rows[member_id]
            surface_stock = member_surface["stock_frame"]
            _same_vector(
                membership_stock.get("origin_global_xyz_mm"),
                frame["origin_global_xyz_mm"],
                f"{axis_id}/{member_id} membership stock origin",
            )
            membership_basis = membership_stock.get("basis_columns_global_xyz")
            require(
                isinstance(membership_basis, Sequence)
                and not isinstance(membership_basis, (str, bytes))
                and len(membership_basis) == 3,
                f"{axis_id}/{member_id} membership stock basis is malformed",
            )
            for index, expected in enumerate(
                (
                    frame["grain_axis_global_xyz"],
                    frame["section_u_global_xyz"],
                    frame["section_v_global_xyz"],
                )
            ):
                _same_vector(
                    membership_basis[index],
                    expected,
                    f"{axis_id}/{member_id} membership stock basis {index}",
                    FRAME_TOLERANCE,
                )
            surface_basis = surface_stock.get("basis_columns_global_xyz")
            require(
                isinstance(surface_basis, Sequence)
                and not isinstance(surface_basis, (str, bytes))
                and len(surface_basis) == 3,
                f"{axis_id}/{member_id} surface stock basis is malformed",
            )
            for basis_index in range(3):
                _same_vector(
                    membership_basis[basis_index],
                    surface_basis[basis_index],
                    f"{axis_id}/{member_id} membership/surface basis {basis_index}",
                    FRAME_TOLERANCE,
                )

            axis_stock = membership.get("axis_in_stock_frame")
            require(
                isinstance(axis_stock, Mapping),
                f"{axis_id}/{member_id} stock coordinates are missing",
            )
            expected_datum_stock = _stock_coordinates(
                datum,
                frame["origin_global_xyz_mm"],
                (
                    frame["grain_axis_global_xyz"],
                    frame["section_u_global_xyz"],
                    frame["section_v_global_xyz"],
                ),
            )
            expected_direction_stock = _stock_direction(
                direction,
                (
                    frame["grain_axis_global_xyz"],
                    frame["section_u_global_xyz"],
                    frame["section_v_global_xyz"],
                ),
            )
            _same_vector(
                axis_stock.get("datum_stock_gqr_mm"),
                expected_datum_stock,
                f"{axis_id}/{member_id} source datum stock coordinates",
            )
            _same_vector(
                axis_stock.get("direction_stock_gqr"),
                expected_direction_stock,
                f"{axis_id}/{member_id} source direction stock coordinates",
                FRAME_TOLERANCE,
            )

            feature = feature_maps[member_id].get(feature_id)
            require(
                feature is not None,
                f"{axis_id}/{member_id} matched feature is absent from surfaces",
            )
            require(
                feature.get("surface_kind") == "CYLINDER",
                f"{axis_id}/{member_id} match is not cylindrical",
            )
            cylinder = feature.get("cylinder")
            require(
                isinstance(cylinder, Mapping),
                f"{axis_id}/{member_id} cylinder metadata is missing",
            )
            require(
                cylinder.get("material_side_geometry") == "bore_like",
                f"{axis_id}/{member_id} feature is not bore-like",
            )
            radius = _finite(
                cylinder.get("radius_mm"), f"{axis_id}/{member_id} bore radius"
            )
            require(radius > 0.0, f"{axis_id}/{member_id} bore radius is not positive")
            center = _vec3(
                cylinder.get("centroid_global_xyz_mm"),
                f"{axis_id}/{member_id} bore centroid",
            )
            _same_vector(
                feature.get("centroid_global_xyz_mm"),
                center,
                f"{axis_id}/{member_id} feature/cylinder centroid",
                POINT_TOLERANCE_MM,
            )
            cylinder_axis = _vec3(
                cylinder.get("axis_unit_global_xyz"),
                f"{axis_id}/{member_id} cylinder direction",
            )
            require(
                abs(_norm(cylinder_axis) - 1.0) <= FRAME_TOLERANCE,
                f"{axis_id}/{member_id} cylinder direction is not unit",
            )
            parallel_departure = _parallel_departure(cylinder_axis, direction)
            require(
                parallel_departure <= AXIS_PARALLEL_TOLERANCE,
                f"{axis_id}/{member_id} cylinder is not parallel to source axis",
            )
            distance = _line_distance(center, datum, direction)
            require(
                distance <= AXIS_LINE_TOLERANCE_MM,
                f"{axis_id}/{member_id} bore center is off source axis line: {distance:.9g} mm",
            )
            _same_number(
                candidate.get("line_distance_mm"),
                distance,
                f"{axis_id}/{member_id} source axis/bore line distance",
                AXIS_LINE_TOLERANCE_MM,
            )
            _same_number(
                candidate.get("axis_direction_sine_error"),
                parallel_departure,
                f"{axis_id}/{member_id} axis parallel departure",
                AXIS_PARALLEL_TOLERANCE,
            )
            expected_center_stock = _stock_coordinates(
                center,
                frame["origin_global_xyz_mm"],
                (
                    frame["grain_axis_global_xyz"],
                    frame["section_u_global_xyz"],
                    frame["section_v_global_xyz"],
                ),
            )
            _same_vector(
                cylinder.get("centroid_stock_gqr_mm"),
                expected_center_stock,
                f"{axis_id}/{member_id} bore center stock coordinates",
            )
            cylinder_axis_stock = _stock_direction(
                cylinder_axis,
                (
                    frame["grain_axis_global_xyz"],
                    frame["section_u_global_xyz"],
                    frame["section_v_global_xyz"],
                ),
            )
            _same_vector(
                cylinder.get("axis_unit_stock_gqr"),
                cylinder_axis_stock,
                f"{axis_id}/{member_id} cylinder stock direction",
                FRAME_TOLERANCE,
            )

            source_station = _dot(
                _sub(datum, frame["origin_global_xyz_mm"]),
                frame["grain_axis_global_xyz"],
            )
            center_station = _dot(
                _sub(center, frame["origin_global_xyz_mm"]),
                frame["grain_axis_global_xyz"],
            )
            identity_key = f"receiver_bore:{axis_id}:{member_id}:{feature_id}"
            bore_candidates.append(
                {
                    "identity_key": identity_key,
                    "kind": "receiver_bore_center",
                    "member_id": member_id,
                    "point_global_xyz_mm": center,
                    "source_identity": {
                        "axis_id": axis_id,
                        "receiver_member_id": member_id,
                        "feature_id": feature_id,
                        "source_cases": list(CASE_IDS),
                    },
                }
            )
            memberships.append(
                {
                    "axis_id": axis_id,
                    "receiver_member_id": member_id,
                    "feature_id": feature_id,
                    "binding_status": membership["binding_status"],
                    "match_status": membership["match_status"],
                    "source_axis_datum_global_xyz_mm": datum,
                    "source_axis_direction_global_xyz": direction,
                    "source_axis_interval_from_datum_mm": interval,
                    "source_axis_datum_grain_station_mm": source_station,
                    "saved_bore_center_global_xyz_mm": center,
                    "saved_bore_center_grain_station_mm": center_station,
                    "bore_center_minus_source_axis_datum_station_mm": center_station
                    - source_station,
                    "source_axis_to_saved_bore_center_line_distance_mm": distance,
                    "cylinder_axis_parallel_departure": parallel_departure,
                    "cylinder_radius_mm": radius,
                    "finished_step_binding": {
                        "path": frame["step_path"],
                        "sha256": frame["step_sha256"],
                        "size_bytes": frame["step_size_bytes"],
                    },
                    "point_identity_key": identity_key,
                }
            )
        require(
            len(members_for_axis) == len(set(members_for_axis))
            and frozenset(members_for_axis) == AXIS_RECEIVERS[axis_id],
            f"{axis_id} receiver membership set differs from the current map",
        )
        require(
            len(members_for_axis) == len(AXIS_RECEIVERS[axis_id]),
            f"{axis_id} receiver membership count differs from the current map",
        )

    require(
        len(memberships) == 14,
        "right-corner axis plan must contain fourteen memberships",
    )
    require(
        len(bore_candidates) == 14,
        "each receiver membership needs one saved bore center",
    )
    return selected_axis_rows, memberships, bore_candidates


def _canonical_bytes(value: Any) -> bytes:
    return (
        json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n"
    ).encode("utf-8")


def _merge_section_planes(
    candidates: Sequence[Mapping[str, Any]],
    frames: Mapping[str, Mapping[str, Any]],
) -> tuple[list[dict[str, Any]], dict[str, str]]:
    """Merge complete-link same-member station groups without dropping identities."""
    by_member: dict[str, list[dict[str, Any]]] = defaultdict(list)
    seen_identities: set[str] = set()
    for candidate in candidates:
        require(isinstance(candidate, Mapping), "station candidate must be an object")
        member_id = candidate.get("member_id")
        identity_key = candidate.get("identity_key")
        require(member_id in MEMBERS, "station candidate has an out-of-scope member")
        require(
            isinstance(identity_key, str) and identity_key,
            "station identity key is missing",
        )
        require(
            identity_key not in seen_identities,
            f"duplicate station identity {identity_key}",
        )
        seen_identities.add(identity_key)
        point = _vec3(candidate.get("point_global_xyz_mm"), f"{identity_key} point")
        frame = frames[member_id]
        station = _dot(
            _sub(point, frame["origin_global_xyz_mm"]), frame["grain_axis_global_xyz"]
        )
        item = dict(candidate)
        item["point_global_xyz_mm"] = point
        item["grain_station_mm"] = station
        by_member[member_id].append(item)

    planes: list[dict[str, Any]] = []
    identity_to_plane: dict[str, str] = {}
    for member_id in sorted(by_member):
        rows = sorted(
            by_member[member_id],
            key=lambda row: (row["grain_station_mm"], row["identity_key"]),
        )
        groups: list[list[dict[str, Any]]] = []
        for row in rows:
            row_station = _finite(row["grain_station_mm"], "station candidate")
            compatible: list[list[dict[str, Any]]] = []
            partial_matches = 0
            for group in groups:
                distances = [
                    abs(
                        row_station - _finite(item["grain_station_mm"], "group station")
                    )
                    for item in group
                ]
                if all(
                    distance <= PLANE_COINCIDENCE_TOLERANCE_MM for distance in distances
                ):
                    compatible.append(group)
                elif any(
                    distance <= PLANE_COINCIDENCE_TOLERANCE_MM for distance in distances
                ):
                    partial_matches += 1
            require(
                partial_matches == 0,
                f"ambiguous transitive station grouping for {member_id} near {row_station:.12g} mm",
            )
            require(
                len(compatible) <= 1,
                f"ambiguous station group membership for {member_id} near {row_station:.12g} mm",
            )
            if compatible:
                compatible[0].append(row)
            else:
                groups.append([row])

        frame = frames[member_id]
        for group in groups:
            identities = sorted(row["identity_key"] for row in group)
            digest = hashlib.sha256(_canonical_bytes(identities)).hexdigest()[:16]
            plane_id = f"{member_id}:section:{digest}"
            stations = [row["grain_station_mm"] for row in group]
            identities_rows = []
            for row in sorted(group, key=lambda item: item["identity_key"]):
                source_identity = row.get("source_identity")
                require(
                    isinstance(source_identity, Mapping),
                    f"{row['identity_key']} source identity is missing",
                )
                identities_rows.append(
                    {
                        "identity_key": row["identity_key"],
                        "kind": row["kind"],
                        **dict(source_identity),
                        "origin_global_xyz_mm": list(row["point_global_xyz_mm"]),
                        "grain_station_mm": row["grain_station_mm"],
                    }
                )
            plane_station = math.fsum(stations) / len(stations)
            first_point = group[0]["point_global_xyz_mm"]
            first_station = _dot(
                _sub(first_point, frame["origin_global_xyz_mm"]),
                frame["grain_axis_global_xyz"],
            )
            plane_origin = [
                first_point[index]
                + frame["grain_axis_global_xyz"][index]
                * (plane_station - first_station)
                for index in range(3)
            ]
            plane = {
                "plane_id": plane_id,
                "member_id": member_id,
                "plane_origin_global_xyz_mm": plane_origin,
                "grain_axis_global_xyz": list(frame["grain_axis_global_xyz"]),
                "section_u_global_xyz": list(frame["section_u_global_xyz"]),
                "section_v_global_xyz": list(frame["section_v_global_xyz"]),
                "grain_station_mm": plane_station,
                "station_spread_mm": max(stations) - min(stations),
                "coincidence_tolerance_mm": PLANE_COINCIDENCE_TOLERANCE_MM,
                "source_identity_count": len(group),
                "source_identities": identities_rows,
            }
            planes.append(plane)
            for identity in identities:
                require(
                    identity not in identity_to_plane,
                    f"station identity is assigned twice: {identity}",
                )
                identity_to_plane[identity] = plane_id
    planes.sort(
        key=lambda row: (row["member_id"], row["grain_station_mm"], row["plane_id"])
    )
    require(
        set(identity_to_plane) == seen_identities,
        "a station identity was dropped during plane grouping",
    )
    return planes, identity_to_plane


def build_plan(
    surfaces: Mapping[str, Any],
    axis_features: Mapping[str, Any],
    envelopes: Mapping[str, Any],
    boundary_report: Mapping[str, Any],
    models_by_case: Mapping[str, Mapping[str, Any]],
) -> dict[str, Any]:
    """Build a source-only station and plane plan from already loaded records."""
    for label, report, schema in (
        (
            "finished surfaces",
            surfaces,
            "wood_joint_current_finished_feature_register/v1",
        ),
        (
            "axis features",
            axis_features,
            "wood_joint_axis_finished_feature_register/v1",
        ),
        (
            "stock envelopes",
            envelopes,
            "wood_joint_proposed_starting_stock_envelopes/v1",
        ),
    ):
        require(isinstance(report, Mapping), f"{label} report must be an object")
        require(report.get("schema") == schema, f"{label} schema differs")
        _validate_report_identity(report, label)
    require(
        isinstance(boundary_report, Mapping), "whole-boundary report must be an object"
    )
    _validate_report_identity(boundary_report, "whole-boundary report")
    require(
        boundary_report.get("status")
        == "PASS_RIGHT_FIVE_BODY_BOUNDARY_RECONSTRUCTION_ONLY",
        "whole-boundary report status differs",
    )
    require(
        set(boundary_report.get("members", [])) == set(MEMBERS),
        "whole-boundary report member scope differs",
    )
    require(isinstance(models_by_case, Mapping), "models_by_case must be an object")
    require(
        set(models_by_case) == set(CASE_IDS), "three source model records are required"
    )
    for case_id in CASE_IDS:
        model = models_by_case[case_id]
        require(isinstance(model, Mapping), f"{case_id} source model must be an object")
        require(
            model.get("schema") == "current_springa_selected_floor_input_model/v1",
            f"{case_id} model schema differs",
        )
        require(
            model.get("case_id") == case_id, f"{case_id} model case identity differs"
        )
        _validate_report_identity(model, f"{case_id} source model")

    require(
        set(boundary_report.get("cases", {})) == set(CASE_IDS),
        "whole-boundary report case set differs",
    )
    states = boundary_report.get("states")
    require(
        isinstance(states, list)
        and boundary_report.get("state_count") == len(states) == 21,
        "whole-boundary report does not contain its 21 source states",
    )
    observed_states: set[tuple[str, int]] = set()
    for state in states:
        require(isinstance(state, Mapping), "whole-boundary state record is malformed")
        case_id, increment = state.get("case_id"), state.get("increment_index")
        require(case_id in CASE_IDS, "whole-boundary state has an unknown case")
        require(
            isinstance(increment, int) and not isinstance(increment, bool),
            "state increment is malformed",
        )
        key = (case_id, increment)
        require(key not in observed_states, f"duplicate whole-boundary state {key}")
        observed_states.add(key)
    expected_states = {(case_id, index) for case_id in CASE_IDS for index in range(7)}
    require(
        observed_states == expected_states,
        "whole-boundary state coverage is incomplete",
    )

    frames = _member_frames(surfaces, envelopes, models_by_case)
    selected_axes, memberships, bore_points = _selected_axes(
        axis_features, surfaces, frames
    )
    interfaces, interface_points = _interface_inventory(boundary_report, models_by_case)
    load_points = _load_node_inventory(models_by_case)
    point_candidates = [*interface_points, *load_points, *bore_points]
    planes, identity_to_plane = _merge_section_planes(point_candidates, frames)

    point_inventory: list[dict[str, Any]] = []
    for candidate in point_candidates:
        member_id = candidate["member_id"]
        point = candidate["point_global_xyz_mm"]
        identity_key = candidate["identity_key"]
        source_identity = candidate["source_identity"]
        point_inventory.append(
            {
                "identity_key": identity_key,
                "kind": candidate["kind"],
                "member_id": member_id,
                **dict(source_identity),
                "point_global_xyz_mm": list(point),
                "grain_station_mm": _dot(
                    _sub(point, frames[member_id]["origin_global_xyz_mm"]),
                    frames[member_id]["grain_axis_global_xyz"],
                ),
                "section_plane_id": identity_to_plane[identity_key],
            }
        )
    point_inventory.sort(key=lambda row: row["identity_key"])
    point_by_identity = {row["identity_key"]: row for row in point_inventory}
    require(
        len(point_by_identity) == len(point_inventory), "duplicate point identity key"
    )

    for interface in interfaces:
        for endpoint in interface["endpoints"]:
            identity_key = endpoint.get("point_identity_key")
            if identity_key is not None:
                require(
                    identity_key in point_by_identity,
                    f"interface endpoint has no station row: {identity_key}",
                )
                endpoint["section_plane_id"] = point_by_identity[identity_key][
                    "section_plane_id"
                ]
    for membership in memberships:
        identity_key = membership["point_identity_key"]
        membership["section_plane_id"] = identity_to_plane[identity_key]
    point_kind_counts: dict[str, int] = defaultdict(int)
    for point in point_inventory:
        point_kind_counts[point["kind"]] += 1
    plane_counts: dict[str, int] = defaultdict(int)
    for plane in planes:
        plane_counts[plane["member_id"]] += 1

    require(len(selected_axes) == 6, "right-corner plan must contain six axes")
    require(
        len(interfaces) == EXPECTED_INTERFACE_COUNT,
        "right-corner plan must retain 338 interfaces",
    )
    require(
        len(interface_points) == 380,
        "right-corner plan must contain 380 in-scope interface endpoints",
    )
    require(
        len(load_points) == 508,
        "right-corner plan must contain 508 physical body-load nodes",
    )
    require(
        len(bore_points) == 14,
        "right-corner plan must contain fourteen matched bore centers",
    )
    require(len(point_inventory) == 902, "right-corner point inventory is incomplete")

    return {
        "schema": "wood_joint_right_corner_finished_section_plan/v1",
        "candidate": CANDIDATE,
        "geometry_revision_id": REVISION,
        "status": "SOURCE_GEOMETRY_AND_STATION_PLAN_ONLY",
        "source_boundary_report_status": boundary_report.get("status"),
        "claim_limits": [
            "This is a saved-source coordinate and section-station plan; it performs no resultant or mechanical calculation.",
            "It establishes no stress, common strain, actual splitting, integrated traction, resistance, joint acceptance, or criterion pass.",
            "Saved model loads are used only to identify physical_body_loads node locations; their force values are not evaluated here.",
            "Proposed stock-frame origins are analytical datums, not observed delivered-stock datums.",
            "No CAD geometry is imported or replayed, and no physical cuts or drilling are approved.",
        ],
        "counts": {
            "members": len(frames),
            "selected_axes": len(selected_axes),
            "receiver_memberships": len(memberships),
            "physical_interface_identities": len(interfaces),
            "in_scope_interface_endpoints": len(interface_points),
            "physical_body_load_nodes": len(load_points),
            "matched_receiver_bore_centers": len(bore_points),
            "point_inventory": len(point_inventory),
            "unique_section_planes": len(planes),
            "section_planes_by_member": dict(sorted(plane_counts.items())),
            "source_cases": len(CASE_IDS),
        },
        "member_frames_and_step_bindings": [
            frames[member_id] for member_id in sorted(frames)
        ],
        "selected_axes": selected_axes,
        "axis_memberships": sorted(
            memberships, key=lambda row: (row["axis_id"], row["receiver_member_id"])
        ),
        "interface_identities": interfaces,
        "point_inventory": point_inventory,
        "section_planes": planes,
    }
