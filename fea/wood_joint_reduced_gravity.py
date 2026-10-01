"""Condense current frame hardware gravity onto its physical receiver bodies.

The 50 timber, block and panel source solids retain a separate distributed
self-weight input at their true source mass centers. Omitted connector parts
are mapped to one or more current receiving member bodies by their physical
role and signed occupied intervals. Every emitted body wrench preserves the
source component's exact global gravity force and first moment. The receiver
split is an explicit conditional load-transfer model, not an accepted joint
law or a prediction of fastener force distribution.

Run with ``.venv/bin/python fea/wood_joint_reduced_gravity.py --check`` for the
focused inventory and conservation check. No native solver is run.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from collections import defaultdict
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
MODEL_INPUTS_PATH = Path(
    "docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/"
    "reduced-static-attempt01/model-inputs.json"
)
MASS_CENTROIDS_PATH = Path(
    "docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/"
    "current-mass-centroids-attempt01/mass-centroids.json"
)
MASS_TOPOLOGY_PATH = Path(
    "docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/"
    "current-mass-topology-map-attempt03/source-topology-map.json"
)

PINNED_SHA256 = {
    MODEL_INPUTS_PATH: "178ab4f9352c8b1f11525ffc6680efa5733ba74cedd609874e9a1966624740f9",
    MASS_CENTROIDS_PATH: "4c107b76d42d2a6f49b81c4857ba20bb236920932a7c34392c63e70d0882099a",
    MASS_TOPOLOGY_PATH: "308a329a0b40db454d5b0e27c9ec2eca92d66eec96bfb222df5f7b7185bef4d4",
}

G_M_S2 = 9.80665
DEFAULT_INTERVAL_SAMPLE_MM = 2.0
SECTION_EDGE_MARGIN_MM = 1.0
WRENCH_REL_TOL = 1.0e-8
SCHEMA = "wood_joint_reduced_body_gravity/v1"


def _read_pinned(path: Path) -> tuple[dict[str, Any], str]:
    raw = (ROOT / path).read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    expected = PINNED_SHA256[path]
    if digest != expected:
        raise ValueError(f"Pinned source changed: {path}; expected {expected}, got {digest}")
    return json.loads(raw), digest


def _add(a: list[float], b: list[float]) -> list[float]:
    return [x + y for x, y in zip(a, b, strict=True)]


def _sub(a: list[float], b: list[float]) -> list[float]:
    return [x - y for x, y in zip(a, b, strict=True)]


def _scale(a: list[float], value: float) -> list[float]:
    return [x * value for x in a]


def _dot(a: list[float], b: list[float]) -> float:
    return sum(x * y for x, y in zip(a, b, strict=True))


def _norm(a: list[float]) -> float:
    return math.sqrt(_dot(a, a))


def _unit(a: list[float]) -> list[float]:
    length = _norm(a)
    if length <= 0.0 or not math.isfinite(length):
        raise ValueError(f"Invalid axis vector: {a}")
    return [value / length for value in a]


def _cross(a: list[float], b: list[float]) -> list[float]:
    return [a[1] * b[2] - a[2] * b[1],
            a[2] * b[0] - a[0] * b[2],
            a[0] * b[1] - a[1] * b[0]]


def _close(actual: list[float], expected: list[float], tol: float = WRENCH_REL_TOL) -> None:
    if len(actual) != len(expected) or any(
        abs(a - b) > tol * max(1.0, abs(a), abs(b))
        for a, b in zip(actual, expected, strict=True)
    ):
        raise AssertionError(f"Source wrench mismatch: {actual} != {expected}")


def _gravity(mass_kg: float) -> list[float]:
    return [0.0, 0.0, -mass_kg * G_M_S2]


def _moment_about_origin(point: list[float], force: list[float]) -> list[float]:
    return _cross(point, force)


def _global_wrench(load: dict[str, Any]) -> tuple[list[float], list[float]]:
    force = load["force_xyz_n"]
    moment = _add(_cross(load["application_point_xyz_mm"], force),
                  load["couple_xyz_nmm_about_application_point"])
    return force, moment


def _bounds_line_range(point: list[float], direction: list[float],
                       bounds: list[float], low: float, high: float) -> tuple[float, float] | None:
    """Clip against STEP AABB stored as [xmin,xmax,ymin,ymax,zmin,zmax]."""
    lo, hi = low, high
    for index in range(3):
        a, b = bounds[index * 2], bounds[index * 2 + 1]
        component = direction[index]
        if abs(component) < 1.0e-14:
            if point[index] < a - 1.0e-8 or point[index] > b + 1.0e-8:
                return None
            continue
        t0, t1 = (a - point[index]) / component, (b - point[index]) / component
        lo, hi = max(lo, min(t0, t1)), min(hi, max(t0, t1))
        if hi <= lo:
            return None
    return lo, hi


def _member_shape(member: dict[str, Any], cache: dict[str, Any]) -> Any:
    member_id = member["member_id"]
    if member_id in cache:
        return cache[member_id]
    try:
        import cadquery as cq
    except ImportError as error:
        raise RuntimeError(
            "Retained-bolt and screw receiver intervals need the pinned CAD geometry; "
            "run this module with .venv/bin/python."
        ) from error
    binding = member["current_finished_step_binding"]
    path = ROOT / binding["path"]
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    if digest != binding["file_sha256"]:
        raise ValueError(f"Receiver STEP source changed: {binding['path']}")
    shape = cq.importers.importStep(str(path)).val()
    if not shape.isValid() or len(shape.Solids()) != 1:
        raise ValueError(f"Expected one valid STEP solid for {member_id}: {binding['path']}")
    cache[member_id] = shape
    return shape


def _gross_section_occupied(shape: Any, point: list[float], direction: list[float],
                             bore_omission_radius_mm: float) -> bool:
    """Test gross section occupancy while allowing a centered fastener bore.

    The section plane is cut through the BRep normal to the source axis. If the
    axis lies in solid wood it is occupied. If it lies in a CAD bore, the point
    remains inside the enclosing gross-section outer loop; smaller closed loops
    for the bore itself are ignored. A radius-scaled minimum outer-loop area
    avoids counting the bore loop as gross wood and does not create a fake
    shaft-cylinder Boolean intersection.
    """
    import cadquery as cq
    from OCP.BRepAlgoAPI import BRepAlgoAPI_Section

    vector = cq.Vector(*point)
    if shape.isInside(vector, 1.0e-6):
        return True
    plane = cq.Face.makePlane(10000.0, 10000.0, vector, cq.Vector(*direction))
    section_operation = BRepAlgoAPI_Section(shape.wrapped, plane.wrapped, False)
    section_operation.Build()
    if not section_operation.IsDone():
        raise RuntimeError("Current receiver section query did not complete")
    section = cq.Shape.cast(section_operation.Shape())
    if not section.Edges():
        return False
    wires = cq.Wire.combine(section.Edges(), tol=0.01)
    normal = _unit(direction)
    helper = [1.0, 0.0, 0.0] if abs(normal[0]) < 0.8 else [0.0, 1.0, 0.0]
    u_axis = _unit(_cross(normal, helper))
    v_axis = _cross(normal, u_axis)
    point2 = (0.0, 0.0)
    minimum_outer_area = max(500.0, 16.0 * math.pi * bore_omission_radius_mm ** 2)

    def inside_polygon(vertices: list[tuple[float, float]]) -> bool:
        inside = False
        previous = vertices[-1]
        px, py = point2
        for current in vertices:
            x1, y1 = previous
            x2, y2 = current
            cross = (px - x1) * (y2 - y1) - (py - y1) * (x2 - x1)
            if abs(cross) <= 1.0e-7 and min(x1, x2) - 1.0e-7 <= px <= max(x1, x2) + 1.0e-7 and min(y1, y2) - 1.0e-7 <= py <= max(y1, y2) + 1.0e-7:
                return True
            if (y1 > py) != (y2 > py):
                crossing_x = x1 + (py - y1) * (x2 - x1) / (y2 - y1)
                if px < crossing_x:
                    inside = not inside
            previous = current
        return inside

    for wire in wires:
        if not wire.IsClosed():
            continue
        polygon: list[tuple[float, float]] = []
        for vertex in wire.Vertices():
            relative = _sub([vertex.X, vertex.Y, vertex.Z], point)
            polygon.append((_dot(relative, u_axis), _dot(relative, v_axis)))
        if len(polygon) < 3:
            continue
        twice_area = abs(sum(
            polygon[index][0] * polygon[(index + 1) % len(polygon)][1]
            - polygon[(index + 1) % len(polygon)][0] * polygon[index][1]
            for index in range(len(polygon))
        ))
        if twice_area * 0.5 < minimum_outer_area:
            continue
        if inside_polygon(polygon):
            return True
    return False


def _gross_receiver_intervals(
    center: list[float],
    direction: list[float],
    half_length_mm: float,
    receiver_ids: list[str],
    members: dict[str, dict[str, Any]],
    shape_cache: dict[str, Any],
    bore_omission_radius_mm: float,
    sample_step_mm: float,
) -> list[dict[str, Any]]:
    """Measure current receiver gross intervals by BRep cross-section.

    Each sample is bounded first by the pinned receiver STEP AABB. Transitions
    are refined by bisection. Holes are omitted from the gross occupancy test,
    with the omission radius tied to the source fastener envelope.
    """
    direction = _unit(direction)
    output: list[dict[str, Any]] = []
    for receiver_id in receiver_ids:
        member = members[receiver_id]
        bounds = member["graph_finished_geometry_summary"]["bounds_xyz_mm"]
        sample_range = _bounds_line_range(center, direction, bounds,
                                          -half_length_mm, half_length_mm)
        if sample_range is None:
            output.append({"receiver_member_id": receiver_id, "intervals_mm": [],
                           "occupied_length_mm": 0.0,
                           "interval_basis": "pinned_finished_STEP_gross_section_no_overlap_with_source_axis"})
            continue
        shape = _member_shape(member, shape_cache)
        low, high = sample_range

        def occupied(s: float) -> bool:
            point = [center[i] + s * direction[i] for i in range(3)]
            return _gross_section_occupied(shape, point, direction, bore_omission_radius_mm)

        count = max(1, int(math.ceil((high - low) / sample_step_mm)))
        samples = [low + (high - low) * index / count for index in range(count + 1)]
        states = [occupied(sample) for sample in samples]

        def refine_transition(a: float, b: float, state_at_a: bool) -> float:
            for _ in range(28):
                middle = (a + b) / 2.0
                if occupied(middle) == state_at_a:
                    a = middle
                else:
                    b = middle
                if b - a <= 0.005:
                    break
            return (a + b) / 2.0

        intervals: list[list[float]] = []
        start: float | None = low if states[0] else None
        for index in range(1, len(samples)):
            before, after = states[index - 1], states[index]
            if before == after:
                continue
            boundary = refine_transition(samples[index - 1], samples[index], before)
            if after:
                start = boundary
            else:
                if start is None:
                    raise AssertionError(f"Interval transition lacks a start for {receiver_id}")
                intervals.append([start, boundary])
                start = None
        if start is not None:
            intervals.append([start, high])
        intervals = [row for row in intervals if row[1] - row[0] > 0.01]
        output.append({
            "receiver_member_id": receiver_id,
            "intervals_mm": intervals,
            "occupied_length_mm": sum(end - start for start, end in intervals),
            "interval_basis": "current_pinned_finished_STEP_cross_sections_with_explicit_central_bore_omission",
            "interval_sample_step_mm": sample_step_mm,
            "transition_refinement_mm": 0.005,
            "bore_omission_radius_mm": bore_omission_radius_mm,
            "aabb_prefilter_bounds_xyz_mm": bounds,
        })
    return output


def _candidate_intervals(connection: dict[str, Any]) -> list[dict[str, Any]]:
    axis = connection["source_record"]["geometry"]
    result = []
    for row in axis["wood_receiver_intervals"]:
        raw_intervals = row["intersection_solid_intervals_from_underhead_mm"]
        if not raw_intervals:
            raise AssertionError(f"Candidate receiver has no source shaft occupancy: {connection['axis_id']}")
        # Candidate intervals are already signed from the source-defined
        # underhead datum in the head-to-nut direction.
        result.append({
            "receiver_member_id": row["receiver_id"],
            "intervals_mm": raw_intervals,
            "occupied_length_mm": sum(end - start for start, end in raw_intervals),
            "interval_basis": "frozen_current_candidate_bolt_wood_receiver_intervals_from_model_inputs",
            "interval_coordinate": "from_underhead_along_axis_head_to_nut",
        })
    if {row["receiver_member_id"] for row in result} != set(connection["receiver_member_ids"]):
        raise AssertionError(f"Candidate source intervals do not cover its receivers: {connection['axis_id']}")
    return result


def _axis_for_source(source: dict[str, Any],
                     connection: dict[str, Any],
                     source_rows: dict[str, dict[str, Any]],
                     source_entity: dict[str, Any]) -> tuple[list[float], list[float], float]:
    """Return component axis center, role-oriented unit vector and length."""
    kind = connection["kind"]
    axis_id = connection["axis_id"]
    if kind == "candidate_bolt":
        geometry = connection["source_record"]["geometry"]
        return (geometry["shaft_center_global_xyz_mm"],
                _unit(geometry["axis_head_to_nut_global"]),
                geometry["modeled_underhead_to_tip_mm"])
    if kind == "retained_bolt":
        record = connection["source_record"]
        shaft = source_rows[f"{axis_id}/shaft"]
        head = source_rows[f"{axis_id}/head"]
        nut = source_rows[f"{axis_id}/nut"]
        axis = _unit(record["axis_global_xyz"])
        head_to_nut_signed = _dot(_sub(nut["mass_center_global_xyz_mm"],
                                       head["mass_center_global_xyz_mm"]), axis)
        if abs(head_to_nut_signed) < 1.0:
            raise AssertionError(f"Retained-bolt head/nut source centroids do not orient {axis_id}")
        oriented_axis = axis if head_to_nut_signed > 0.0 else _scale(axis, -1.0)
        length = record["source_occupied_length_mm"]
        return shaft["mass_center_global_xyz_mm"], oriented_axis, length
    if kind == "panel_screw":
        screw = source_rows[axis_id]
        length = source_entity["current_cad_axis_envelope_length_mm"]
        return (screw["mass_center_global_xyz_mm"],
                _unit(connection["source_record"]["axis_global_xyz"]), length)
    raise AssertionError(f"Unknown physical axis family: {kind}")


def _interval_center(interval: list[float]) -> float:
    return (interval[0] + interval[1]) / 2.0


def _interval_end_roles(intervals: list[dict[str, Any]],
                        head_station: float,
                        nut_station: float,
                        source_name: str) -> tuple[str, str]:
    nonempty = [row for row in intervals if row["occupied_length_mm"] > 0.01]
    if len(nonempty) < 2:
        raise AssertionError(f"Need two positive current receiver intervals for head/nut routing: {source_name}")
    ordered = sorted(nonempty, key=lambda row: min(a for a, _ in row["intervals_mm"]))
    first_start = min(a for a, _ in ordered[0]["intervals_mm"])
    last_end = max(b for _, b in ordered[-1]["intervals_mm"])
    if not (head_station < first_start + 5.0 and nut_station > last_end - 5.0):
        raise AssertionError(
            f"Source role centroids do not bracket the signed receiver intervals for {source_name}: "
            f"head={head_station:.3f}, first={first_start:.3f}, last={last_end:.3f}, nut={nut_station:.3f}"
        )
    return ordered[0]["receiver_member_id"], ordered[-1]["receiver_member_id"]


def _receiver_weights(intervals: list[dict[str, Any]],
                      receivers: list[str], source_name: str) -> list[dict[str, Any]]:
    by_id = {row["receiver_member_id"]: row for row in intervals}
    if set(by_id) != set(receivers):
        raise AssertionError(f"Interval receiver set mismatch for {source_name}: {set(by_id)} != {set(receivers)}")
    lengths = {receiver: by_id[receiver]["occupied_length_mm"] for receiver in receivers}
    positive_total = sum(length for length in lengths.values() if length > 0.01)
    if positive_total <= 0.0 or any(length <= 0.01 for length in lengths.values()):
        raise AssertionError(f"A physical receiver has no positive gross occupied length: {source_name} {lengths}")
    return [{
        "receiver_member_id": receiver,
        "occupancy_length_mm": lengths[receiver],
        "weight": lengths[receiver] / positive_total,
        "source_intervals": by_id[receiver]["intervals_mm"],
        "interval_basis": by_id[receiver]["interval_basis"],
    } for receiver in receivers]


def _station_point(center: list[float], direction: list[float],
                   station: float, axis_origin_shift: float = 0.0) -> list[float]:
    """Map an axis coordinate to global XYZ; shift maps source datum to station zero."""
    return _add(center, _scale(direction, station + axis_origin_shift))


def _interval_weighted_midpoint(intervals: list[list[float]]) -> float:
    lengths = [max(0.0, end - start) for start, end in intervals]
    total = sum(lengths)
    if total <= 0.0:
        raise ValueError("A receiver needs positive occupied interval length")
    return sum(((start + end) * 0.5) * length
               for (start, end), length in zip(intervals, lengths, strict=True)) / total


def _load_contribution(source: dict[str, Any], member_ref: list[float],
                       application_point: list[float], receiver_id: str, weight: float,
                       allocation_basis: str) -> dict[str, Any]:
    force = _gravity(source["mass_kg"] * weight)
    source_point = source["mass_center_global_xyz_mm"]
    application_couple = _cross(_sub(source_point, application_point), force)
    body_reference_couple = _cross(_sub(source_point, member_ref), force)
    return {
        "source_name": source["name"],
        "source_entity_id": source["source_mass_entity"]["id"],
        "source_entity_kind": source["source_mass_entity"]["kind"],
        "source_group": source["group"],
        "source_component_role": source["source_mass_entity"].get("component_role"),
        "source_axis_id": source["source_mass_entity"].get("axis_id"),
        "source_mass_kg": source["mass_kg"],
        "mass_share_kg": source["mass_kg"] * weight,
        "allocation_weight": weight,
        "receiver_member_id": receiver_id,
        "body_reference_xyz_mm": member_ref,
        "application_point_xyz_mm": application_point,
        "source_centroid_xyz_mm": source_point,
        "force_xyz_n": force,
        "couple_xyz_nmm_about_application_point": application_couple,
        "audit_couple_xyz_nmm_about_body_reference": body_reference_couple,
        "allocation_basis": allocation_basis,
        "source_role_basis": source["source_mass_entity"].get("component_role"),
        "application_point_basis": "Point lies on the source hardware axis at the receiving wood interval midpoint, or at its outer wood-seat boundary for a head/nut component. It is a local load application coordinate, not a new node or constraint.",
        "wrench_reference_limit": "Use application_point_xyz_mm and its couple for transfer into the receiver node cloud. The body-centroid couple is audit-only; applying the whole source component wrench there would suppress local member section demand.",
    }


def _group_body_loads(contributions: list[dict[str, Any]],
                      member_points: dict[str, list[float]]) -> list[dict[str, Any]]:
    groups: dict[str, dict[str, Any]] = {}
    for item in contributions:
        member_id = item["receiver_member_id"]
        if member_id not in groups:
            point = member_points[member_id]
            groups[member_id] = {
                "member_id": member_id,
                "body_reference_xyz_mm": point,
                "hardware_mass_share_kg": 0.0,
                "hardware_force_xyz_n": [0.0, 0.0, 0.0],
                "audit_moment_about_global_origin_xyz_nmm": [0.0, 0.0, 0.0],
                "hardware_source_names": [],
                "application_loads": [],
            }
        group = groups[member_id]
        force, moment = _global_wrench(item)
        group["hardware_mass_share_kg"] += item["mass_share_kg"]
        group["hardware_force_xyz_n"] = _add(group["hardware_force_xyz_n"], force)
        group["audit_moment_about_global_origin_xyz_nmm"] = _add(
            group["audit_moment_about_global_origin_xyz_nmm"], moment)
        group["hardware_source_names"].append(item["source_name"])
        group["application_loads"].append(item)
    return [groups[key] for key in sorted(groups)]


def compile_body_gravity(
    model_inputs: dict[str, Any] | None = None,
    mass_centroids: dict[str, Any] | None = None,
    mass_topology: dict[str, Any] | None = None,
    *,
    section_step_mm: float = DEFAULT_INTERVAL_SAMPLE_MM,
    include_receiver_extremes: bool = True,
) -> dict[str, Any]:
    """Compile the 586 omitted connector-hardware source rows onto receiver bodies.

    Member self-weight remains for the caller's distributed body-gravity path;
    T-nuts remain for the separate hold-face path. Candidate-bolt receiver
    spans use the frozen shaft/wood intervals. Retained-bolt and screw spans
    absent from the JSON contract use current finished STEP gross sections with
    explicit central-bore omission.
    """
    if section_step_mm <= 0.0 or section_step_mm > 2.0:
        raise ValueError("section_step_mm must be >0 and <=2 mm for a stable gross interval map")
    pins: dict[str, str] = {}
    if model_inputs is None:
        model_inputs, pins[str(MODEL_INPUTS_PATH)] = _read_pinned(MODEL_INPUTS_PATH)
    if mass_centroids is None:
        mass_centroids, pins[str(MASS_CENTROIDS_PATH)] = _read_pinned(MASS_CENTROIDS_PATH)
    if mass_topology is None:
        mass_topology, pins[str(MASS_TOPOLOGY_PATH)] = _read_pinned(MASS_TOPOLOGY_PATH)
    if model_inputs["revision_id"] != mass_centroids["revision_id"] or model_inputs["revision_id"] != mass_topology["revision_id"]:
        raise AssertionError("Gravity source revisions do not match")
    if len(model_inputs["members"]) != 50 or len(mass_centroids["rows"]) != 778 or len(mass_topology["physical_mass_rows"]) != 778:
        raise AssertionError("Expected 50 source bodies and the complete 778-row mass inventory")

    source_rows = {row["name"]: row for row in mass_centroids["rows"]}
    topology_rows = {row["inventory_name"]: row for row in mass_topology["physical_mass_rows"]}
    if set(source_rows) != set(topology_rows):
        raise AssertionError("Mass centroid and topology inventories differ")
    members = {row["member_id"]: row for row in model_inputs["members"]}
    member_points = {name: source_rows[name]["mass_center_global_xyz_mm"] for name in members}
    connections = {row["axis_id"]: row for row in model_inputs["connections"]}
    if len(connections) != 170:
        raise AssertionError("Expected 170 current physical axis records")
    shape_cache: dict[str, Any] = {}
    rows_out: list[dict[str, Any]] = []
    body_contributions: list[dict[str, Any]] = []
    sensitivity_extremes: list[dict[str, Any]] = []
    by_axis: dict[str, list[str]] = defaultdict(list)
    axis_intervals_cache: dict[str, dict[str, Any]] = {}
    member_self_weight_mass = 0.0
    tnut_mass = 0.0
    total_source_mass = 0.0
    total_source_force = [0.0, 0.0, 0.0]
    total_source_moment = [0.0, 0.0, 0.0]
    member_self_weight_count = 0
    tnut_count = 0
    model_hardware_rows = {row["source_name"]: row for row in model_inputs["unassigned_hardware_gravity"]}
    if len(model_hardware_rows) != 586:
        raise AssertionError("Expected 586 model-input hardware rows")

    for name, source in source_rows.items():
        topology_row = topology_rows[name]
        entity = topology_row["source_mass_entity"]
        if source["mass_kg"] != topology_row["mass_kg"]:
            raise AssertionError(f"Source mass mismatch: {name}")
        _close(source["mass_center_global_xyz_mm"], topology_row["mass_center_global_xyz_mm"])
        force = _gravity(source["mass_kg"])
        _close(force, source["gravity_force_global_xyz_n"])
        _close(force, topology_row["gravity_force_global_xyz_n"])
        source_point = source["mass_center_global_xyz_mm"]
        source_moment = _moment_about_origin(source_point, force)
        _close(source_moment, source["gravity_moment_about_global_origin_nmm"])
        _close(source_moment, topology_row["gravity_moment_about_global_origin_nmm"])
        receivers = entity["current_graph_member_references"]
        if not receivers or any(receiver not in members for receiver in receivers):
            raise AssertionError(f"Mass source has an unresolved current member receiver: {name}")
        total_source_mass += source["mass_kg"]
        total_source_force = _add(total_source_force, force)
        total_source_moment = _add(total_source_moment, source_moment)
        kind = entity["kind"]
        if kind == "current_physical_member_solid":
            if len(receivers) != 1 or receivers[0] != name:
                raise AssertionError(f"Physical source body does not map to itself: {name}")
            member_self_weight_mass += source["mass_kg"]
            member_self_weight_count += 1
            continue

        if kind == "current_physical_tnut_component":
            if len(receivers) != 1:
                raise AssertionError(f"T-nut source does not have one panel receiver: {name}")
            tnut_mass += source["mass_kg"]
            tnut_count += 1
            continue

        if kind not in ("current_candidate_hardware_component",
                        "current_retained_frame_hardware_component",
                        "current_panel_screw_axis_envelope_proxy"):
            raise AssertionError(f"Unsupported omitted source mass kind: {name}: {kind}")
        source_for_load = {**source, "source_mass_entity": entity}
        if name not in model_hardware_rows:
            raise AssertionError(f"Hardware source is absent from reduced-model unassigned inventory: {name}")
        model_row = model_hardware_rows[name]
        _close([source["mass_kg"]], [model_row["mass_kg"]])
        _close(source_point, model_row["point_xyz_mm"])
        _close(force, model_row["force_xyz_n"])
        axis_id = entity.get("axis_id")
        connection = connections.get(axis_id)
        if connection is None or set(connection["receiver_member_ids"]) != set(receivers):
            raise AssertionError(f"Hardware source has no matching physical connection: {name}")
        by_axis[axis_id].append(name)
        ckind = connection["kind"]
        if kind == "current_candidate_hardware_component" and ckind != "candidate_bolt":
            raise AssertionError(f"Candidate hardware/source connection mismatch: {name}")
        if kind == "current_retained_frame_hardware_component" and ckind != "retained_bolt":
            raise AssertionError(f"Retained hardware/source connection mismatch: {name}")
        if kind == "current_panel_screw_axis_envelope_proxy" and ckind != "panel_screw":
            raise AssertionError(f"Panel screw/source connection mismatch: {name}")

        cached_axis = axis_intervals_cache.get(axis_id)
        if cached_axis is None:
            center, axis_direction, physical_length = _axis_for_source(
                source, connection, source_rows, entity
            )
            underhead_shift = -physical_length / 2.0 if ckind == "candidate_bolt" else 0.0
            if ckind == "candidate_bolt":
                receiver_intervals = _candidate_intervals(connection)
                head = source_rows[f"{axis_id}/head"]
                nut = source_rows[f"{axis_id}/nut"]
                # The frozen candidate coordinate begins at the underhead and points head-to-nut.
                head_station = _dot(_sub(head["mass_center_global_xyz_mm"], center), axis_direction) + physical_length / 2.0
                nut_station = _dot(_sub(nut["mass_center_global_xyz_mm"], center), axis_direction) + physical_length / 2.0
                head_receiver, nut_receiver = _interval_end_roles(
                    receiver_intervals, head_station, nut_station, axis_id
                )
            elif ckind == "retained_bolt":
                record = connection["source_record"]
                receiver_intervals = _gross_receiver_intervals(
                    center, axis_direction, physical_length / 2.0, receivers,
                    members, shape_cache, record["source_occupied_diameter_mm"] / 2.0,
                    section_step_mm
                )
                head = source_rows[f"{axis_id}/head"]
                nut = source_rows[f"{axis_id}/nut"]
                head_station = _dot(_sub(head["mass_center_global_xyz_mm"], center), axis_direction)
                nut_station = _dot(_sub(nut["mass_center_global_xyz_mm"], center), axis_direction)
                head_receiver, nut_receiver = _interval_end_roles(
                    receiver_intervals, head_station, nut_station, axis_id
                )
            else:
                # The screw vector may point outward. The source centroid and axis
                # are treated as an undirected 63.5 mm envelope; actual current
                # panel and wood IDs identify which gross interval belongs to which.
                proxy_volume_mm3 = source["mass_kg"] / source["density_kg_m3"] * 1.0e9
                proxy_radius = math.sqrt(proxy_volume_mm3 / (math.pi * physical_length))
                receiver_intervals = _gross_receiver_intervals(
                    center, axis_direction, physical_length / 2.0, receivers,
                    members, shape_cache, proxy_radius, section_step_mm
                )
                panel_id = connection["source_record"]["panel_member"]
                wood_id = connection["source_record"]["receiver_member"]
                if {panel_id, wood_id} != set(receivers):
                    raise AssertionError(f"Screw panel/wood receiver labels disagree: {axis_id}")
                for receiver_id in (panel_id, wood_id):
                    interval = next(row for row in receiver_intervals if row["receiver_member_id"] == receiver_id)
                    if interval["occupied_length_mm"] <= 0.01:
                        raise AssertionError(f"Screw lacks positive gross occupancy for {receiver_id}: {axis_id}")
                head_receiver = nut_receiver = None
            cached_axis = {
                "center": center,
                "axis_direction": axis_direction,
                "physical_length": physical_length,
                "underhead_shift": underhead_shift,
                "receiver_intervals": receiver_intervals,
                "head_receiver": head_receiver,
                "nut_receiver": nut_receiver,
            }
            axis_intervals_cache[axis_id] = cached_axis
        center = cached_axis["center"]
        axis_direction = cached_axis["axis_direction"]
        physical_length = cached_axis["physical_length"]
        underhead_shift = cached_axis["underhead_shift"]
        receiver_intervals = cached_axis["receiver_intervals"]
        head_receiver = cached_axis["head_receiver"]
        nut_receiver = cached_axis["nut_receiver"]
        receiver_weights = _receiver_weights(receiver_intervals, receivers, name)
        routing_basis = {
            "candidate_bolt": "Head/head washer maps to the receiver at the signed underhead-side wood seat; nut/nut washer maps to the opposite wood seat. Shaft mass shares use positive current receiver interval lengths.",
            "retained_bolt": "Head/nut sides are oriented from source component centroids, then mapped to the first/last current finished-STEP gross receiver intervals. Shaft mass shares use their positive lengths.",
            "panel_screw": "The source screw-axis envelope is apportioned by current panel/backer gross-section occupancy; the raw vector sign is not interpreted as penetration direction.",
        }[ckind]

        role = entity.get("component_role")
        if ckind in ("candidate_bolt", "retained_bolt"):
            if role in ("head", "head_washer"):
                selected_receiver = head_receiver
                receiver_weights = [{
                    "receiver_member_id": selected_receiver,
                    "occupancy_length_mm": next(row["occupied_length_mm"] for row in receiver_intervals
                                                 if row["receiver_member_id"] == selected_receiver),
                    "weight": 1.0,
                    "source_intervals": next(row["intervals_mm"] for row in receiver_intervals
                                              if row["receiver_member_id"] == selected_receiver),
                    "interval_basis": "source-role-oriented head outer receiver interval",
                    "station_mm": min(start for start, _ in next(row["intervals_mm"] for row in receiver_intervals
                                                                       if row["receiver_member_id"] == selected_receiver)),
                    "seat_kind": "head-side outer wood-seat boundary",
                }]
            elif role in ("nut", "nut_washer"):
                selected_receiver = nut_receiver
                receiver_weights = [{
                    "receiver_member_id": selected_receiver,
                    "occupancy_length_mm": next(row["occupied_length_mm"] for row in receiver_intervals
                                                 if row["receiver_member_id"] == selected_receiver),
                    "weight": 1.0,
                    "source_intervals": next(row["intervals_mm"] for row in receiver_intervals
                                              if row["receiver_member_id"] == selected_receiver),
                    "interval_basis": "source-role-oriented nut outer receiver interval",
                    "station_mm": max(end for _, end in next(row["intervals_mm"] for row in receiver_intervals
                                                                   if row["receiver_member_id"] == selected_receiver)),
                    "seat_kind": "nut-side outer wood-seat boundary",
                }]
            elif role == "shaft":
                for route in receiver_weights:
                    route["station_mm"] = _interval_weighted_midpoint(route["source_intervals"])
                    route["seat_kind"] = "receiver occupied-interval length centroid"
            else:
                raise AssertionError(f"Unrecognized bolt component role {role}: {name}")
        else:
            for route in receiver_weights:
                route["station_mm"] = _interval_weighted_midpoint(route["source_intervals"])
                route["seat_kind"] = "receiver occupied-interval length centroid"

        contributions = []
        for route in receiver_weights:
            receiver_id = route["receiver_member_id"]
            application_point = _station_point(center, axis_direction, route["station_mm"], underhead_shift)
            contribution = _load_contribution(
                source_for_load, member_points[receiver_id], application_point, receiver_id, route["weight"],
                f"{routing_basis} Receiver interval length={route['occupancy_length_mm']} mm; {route['interval_basis']}."
            )
            contribution["receiver_occupancy_length_mm"] = route["occupancy_length_mm"]
            contribution["receiver_signed_intervals_mm"] = route["source_intervals"]
            contribution["source_axis_center_xyz_mm"] = center
            contribution["source_axis_unit_direction_global"] = axis_direction
            contribution["receiver_application_station_mm"] = route["station_mm"]
            contribution["receiver_application_point_basis"] = route["seat_kind"]
            contributions.append(contribution)
            body_contributions.append(contribution)
        source_f = [0.0, 0.0, 0.0]
        source_m = [0.0, 0.0, 0.0]
        for contribution in contributions:
            f, m = _global_wrench(contribution)
            source_f = _add(source_f, f)
            source_m = _add(source_m, m)
        _close(source_f, force)
        _close(source_m, source_moment)

        alternatives = []
        if include_receiver_extremes and len(receivers) > 1:
            primary_points = {item["receiver_member_id"]: item["application_point_xyz_mm"]
                              for item in contributions}
            for receiver_id in receivers:
                interval_row = next(row for row in receiver_intervals if row["receiver_member_id"] == receiver_id)
                station = primary_points.get(receiver_id)
                if station is None:
                    station_value = _interval_weighted_midpoint(interval_row["intervals_mm"])
                    station = _station_point(center, axis_direction, station_value, underhead_shift)
                application_point_extreme = station
                extreme = _load_contribution(
                    source_for_load, member_points[receiver_id], application_point_extreme, receiver_id, 1.0,
                    "Sensitivity extreme: this entire source component is carried at a local point on the named receiver interval; exact source wrench retained."
                )
                extreme["receiver_signed_intervals_mm"] = interval_row["intervals_mm"]
                extreme["source_axis_center_xyz_mm"] = center
                extreme["source_axis_unit_direction_global"] = axis_direction
                alternatives.append(extreme)
                sensitivity_extremes.append({
                    "variant_id": f"{name}/all_to/{receiver_id}",
                    "source_name": name,
                    "receiver_member_id": receiver_id,
                    "allocation_weight": 1.0,
                    "application_point_xyz_mm": extreme["application_point_xyz_mm"],
                    "force_xyz_n": extreme["force_xyz_n"],
                    "couple_xyz_nmm_about_application_point": extreme["couple_xyz_nmm_about_application_point"],
                    "body_reference_xyz_mm": extreme["body_reference_xyz_mm"],
                    "exact_global_source_wrench_retained": True,
                    "interpretation": "Alternate body-transfer extreme for uncertainty sensitivity; not a preferred physical split.",
                })

        rows_out.append({
            "name": name,
            "group": source["group"],
            "source_entity_id": entity["id"],
            "source_entity_kind": kind,
            "source_component_role": role,
            "source_axis_id": axis_id,
            "mass_kg": source["mass_kg"],
            "source_mass_center_global_xyz_mm": source_point,
            "source_gravity_force_global_xyz_n": force,
            "source_gravity_moment_about_global_origin_xyz_nmm": source_moment,
            "current_receiver_member_ids": receivers,
            "representation": "source_component_body_wrench_condensation",
            "allocation_basis": routing_basis,
            "receiver_intervals": receiver_intervals,
            "body_load_contributions": contributions,
            "alternate_receiver_extremes": alternatives,
            "unmodeled_response": "The positive length split and role-selected outer-face routing do not determine bolt bending, bearing pressure, friction, contact activation, connector stiffness, or joint force recovery.",
        })

    if len(rows_out) != 586 or len({row["name"] for row in rows_out}) != 586:
        raise AssertionError("The compiler must resolve all 586 unassigned hardware rows exactly once")
    if set(model_hardware_rows) != {row["name"] for row in rows_out}:
        raise AssertionError("Resolved hardware source rows differ from model-input deferred rows")
    if sum(len(row["body_load_contributions"]) for row in rows_out) == 0:
        raise AssertionError("No omitted hardware body loads were generated")
    hardware_force = [0.0, 0.0, 0.0]
    hardware_moment = [0.0, 0.0, 0.0]
    hardware_mass = 0.0
    for load in body_contributions:
        f, m = _global_wrench(load)
        hardware_force = _add(hardware_force, f)
        hardware_moment = _add(hardware_moment, m)
        hardware_mass += load["mass_share_kg"]
    _close(hardware_force, [0.0, 0.0, -hardware_mass * G_M_S2])
    _close([hardware_mass], [sum(row["mass_kg"] for row in rows_out)])
    _close(total_source_force, mass_topology["gravity_force_global_xyz_n"])
    _close(total_source_moment, mass_topology["gravity_moment_about_global_origin_nmm"])
    _close([total_source_mass], [mass_topology["modeled_mass_kg"]])

    body_loads = _group_body_loads(body_contributions, member_points)
    return {
        "schema": SCHEMA,
        "candidate": model_inputs["candidate"],
        "revision_id": model_inputs["revision_id"],
        "status": "SOURCE_BOUND_CONDITIONAL_HARDWARE_BODY_LOAD_MAP",
        "mechanical_acceptance": False,
        "native_solve_run": False,
        "units": {"mass": "kg", "length": "mm", "force": "N", "moment": "N mm"},
        "gravity_m_s2": G_M_S2,
        "source_sha256": pins,
        "receiver_step_sha256": {
            member_id: members[member_id]["current_finished_step_binding"]["file_sha256"]
            for member_id in sorted(shape_cache)
        },
        "inventory_summary": {
            "source_rows_total": len(source_rows),
            "distributed_member_self_weight_rows_excluded_from_this_map": member_self_weight_count,
            "tnut_rows_delegated_to_hold_face_load_path": tnut_count,
            "omitted_hardware_rows": len(rows_out),
            "omitted_hardware_source_axis_count": len(by_axis),
            "omitted_hardware_condensed_mass_kg": sum(row["mass_kg"] for row in rows_out),
            "body_receiver_contribution_count": len(body_contributions),
            "receiver_extreme_variant_count": len(sensitivity_extremes),
            "omitted_hardware_force_xyz_n": hardware_force,
            "omitted_hardware_moment_about_global_origin_xyz_nmm": hardware_moment,
            "member_self_weight_mass_kg_excluded": member_self_weight_mass,
            "tnut_mass_kg_delegated": tnut_mass,
            "all_778_source_rows_mass_kg": total_source_mass,
        },
        "equilibrium": {
            "all_778_source_force_xyz_n": total_source_force,
            "all_778_source_moment_about_global_origin_xyz_nmm": total_source_moment,
            "all_778_source_force_and_first_moment_match": True,
            "omitted_hardware_force_xyz_n": hardware_force,
            "omitted_hardware_moment_about_global_origin_xyz_nmm": hardware_moment,
            "omitted_hardware_force_and_first_moment_match": True,
        },
        "body_loads": body_loads,
        "source_rows": rows_out,
        "receiver_extreme_sensitivities": sensitivity_extremes,
        "limits": [
            "This compiler emits only the 586 omitted hardware source rows. Apply the 50 timber/block/panel source masses as distributed body/member gravity at their true source centroids using the separate body-self-weight routine; do not replace section bending with a point load at an envelope reference.",
            "Candidate-bolt receiver lengths use the frozen current shaft/wood intervals. Retained-bolt and screw spans use pinned finished BREP sections; a centerline inside a bore is treated as gross material occupancy only when the section boundary lies within the inferred shaft/bore radius plus margin. The bore is explicitly omitted from this gross support calculation.",
            "Head and nut components are routed to the outer receivers from signed source intervals. Shaft mass uses positive receiver occupied-length proportions. These are conditional static gravity transfer choices; actual bolt bending and force sharing remain unmodeled.",
            "Screw proxy mass is split by current gross panel/backer occupied lengths along its undirected 63.5 mm envelope. Its vector sign is not taken to define penetration direction; the physical panel and wood receiver IDs label the interval owners.",
            "All source component force shares plus body-reference couples preserve each source row's exact global gravity force and first moment. Body reference points are wrench references only; the parent model must distribute each wrench over native receiver body nodes.",
            "Per-source all-to-each-receiver extremes are provided to bound transfer uncertainty. They preserve each source wrench but do not prove a physical end-share or supply connection stiffness.",
            "The 142 T-nut source rows are validated against the frozen inventory but delegated to the hold-face point-wrench path. No accessory 25 kg scenario is included here; continue to apply the separate source-bound scenarios from wood_joint_reduced_loads.py.",
        ],
    }


def _envelope_reference(member: dict[str, Any]) -> list[float]:
    descriptor = member.get("reduced_geometry_descriptor") or {}
    if all(key in descriptor for key in ("start", "end")):
        return [(a + b) / 2.0 for a, b in zip(descriptor["start"], descriptor["end"], strict=True)]
    bounds = member["graph_finished_geometry_summary"]["bounds_xyz_mm"]
    return [(bounds[i * 2] + bounds[i * 2 + 1]) / 2.0 for i in range(3)]


def focused_check() -> dict[str, Any]:
    result = compile_body_gravity()
    info = result["inventory_summary"]
    if (info["source_rows_total"] != 778 or info["omitted_hardware_rows"] != 586
            or info["distributed_member_self_weight_rows_excluded_from_this_map"] != 50
            or info["tnut_rows_delegated_to_hold_face_load_path"] != 142):
        raise AssertionError("Mass-source partition failed")
    if info["receiver_extreme_variant_count"] == 0:
        raise AssertionError("Expected explicit receiver-transfer extremes")
    if not result["equilibrium"]["omitted_hardware_force_and_first_moment_match"]:
        raise AssertionError("Hardware gravity wrench does not match frozen source")
    for row in result["source_rows"]:
        if abs(sum(load["mass_share_kg"] for load in row["body_load_contributions"])
               - row["mass_kg"]) > 1.0e-10:
            raise AssertionError(f"Source mass split failed: {row['name']}")
        for load in row["body_load_contributions"]:
            if len(load["application_point_xyz_mm"]) != 3 or len(load["couple_xyz_nmm_about_application_point"]) != 3:
                raise AssertionError(f"No local application wrench: {row['name']}")
    return {
        "status": "PASS_HARDWARE_SOURCE_COVERAGE_LOCAL_APPLICATION_AND_WRENCH_CONSERVATION",
        "source_rows_total": info["source_rows_total"],
        "distributed_member_self_weight_rows_excluded": info["distributed_member_self_weight_rows_excluded_from_this_map"],
        "tnut_rows_delegated": info["tnut_rows_delegated_to_hold_face_load_path"],
        "omitted_hardware_rows": info["omitted_hardware_rows"],
        "omitted_hardware_mass_kg": info["omitted_hardware_condensed_mass_kg"],
        "omitted_hardware_axis_count": info["omitted_hardware_source_axis_count"],
        "body_receiver_contributions": info["body_receiver_contribution_count"],
        "receiver_extreme_variants": info["receiver_extreme_variant_count"],
        "omitted_hardware_force_xyz_n": result["equilibrium"]["omitted_hardware_force_xyz_n"],
        "omitted_hardware_moment_about_global_origin_xyz_nmm": result["equilibrium"]["omitted_hardware_moment_about_global_origin_xyz_nmm"],
        "body_reference_couple_is_audit_only": True,
        "native_solve_run": False,
        "mechanical_acceptance": False,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--check", action="store_true", help="run source and equilibrium checks")
    mode.add_argument("--json", action="store_true", help="emit the complete body gravity map")
    args = parser.parse_args()
    print(json.dumps(compile_body_gravity() if args.json else focused_check(), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
