"""WJ-06 nominal face-cleat screen for residual wood-joint duties.

Geometry diagnostic only. It assigns every duty outside WJ-03/WJ-04, leaves
WJ-05 center duties with their owner, and searches one-piece solid-wood corner
cleats where actual host faces form an orthogonal pair.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path

import cadquery as cq

from mini_moonboard.floor_flush_width import KERF_RIGHT, variant
from mini_moonboard.hold_tnut_reinforcement import datums as hold_datums
from mini_moonboard.wood_joint_frame import _make_parts as make_wj03_trial_parts
from mini_moonboard.wood_joint_frame import validate_source_binding

ROOT = Path(__file__).resolve().parents[1]
INVENTORY_PATH = ROOT / "docs/wood-joints-mvp/source-inventory.json"
OUT_JSON = ROOT / "docs/wood-joints-mvp/wj06-residual-probe.json"
OUT_MD = ROOT / "docs/wood-joints-mvp/wj06-residual-probe.md"
CANDIDATE = "compact-floor-flush-wood-joints-development"
WJ03_DUTIES = {
    f"clip_timber_header_outer_{side}" for side in ("left", "right")
} | {f"clip_angle_base_{side}" for side in ("left", "right")}
WJ04_DUTY = "clip_horizontal_lower_right_1"
WJ05_DUTIES = {
    f"clip_split_header_center_{side}" for side in ("left", "right")
} | {f"clip_split_base_center_{side}" for side in ("left", "right")}
EXCLUDED_DIAGNOSTIC_DUTIES = WJ03_DUTIES | {WJ04_DUTY}
WIDTHS_MM = (38.1, 63.5, 88.9)
GRAIN_LENGTH_MM = 88.9
AXIS_D_MM = 6.35
AXIS_EDGE_OFFSET_MM = 25.4
HIT_MM3 = 1e-6
TOOL_D_MM = 25.4
TOOL_L_MM = 50.0
X = cq.Vector(1, 0, 0)
T = cq.Vector(0, math.cos(math.radians(50)), math.sin(math.radians(50)))
N = cq.Vector(0, -math.sin(math.radians(50)), math.cos(math.radians(50)))


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _unit(value: cq.Vector) -> cq.Vector:
    if value.Length < 1e-9:
        raise ValueError("Zero vector in face map")
    return value.normalized()


def _vec(value: cq.Vector) -> list[float]:
    return [round(v, 9) for v in value.toTuple()]


def _box(shape: cq.Shape) -> cq.BoundBox:
    return shape.BoundingBox()


def _bounds(shape: cq.Shape) -> list[float]:
    b = _box(shape)
    return [round(v, 6) for v in (b.xmin, b.xmax, b.ymin, b.ymax, b.zmin, b.zmax)]


def _disjoint(a: cq.BoundBox, b: cq.BoundBox) -> bool:
    return (
        a.xmax <= b.xmin or b.xmax <= a.xmin
        or a.ymax <= b.ymin or b.ymax <= a.ymin
        or a.zmax <= b.zmin or b.zmax <= a.zmin
    )


def _volume(a: cq.Shape, b: cq.Shape) -> float:
    if _disjoint(_box(a), _box(b)):
        return 0.0
    return a.intersect(b).Volume()


def _hits(shape: cq.Shape, obstacles: dict[str, cq.Shape]) -> dict[str, float]:
    bounds = _box(shape)
    result = {}
    for name, other in obstacles.items():
        if _disjoint(bounds, _box(other)):
            continue
        volume = shape.intersect(other).Volume()
        if volume > HIT_MM3:
            result[name] = round(volume, 6)
    return result


def _faces(shape: cq.Shape) -> dict[str, tuple[cq.Face, dict]]:
    rows = []
    for face in shape.Faces():
        if face.geomType() != "PLANE":
            continue
        center = face.Center()
        normal = _unit(face.normalAt())
        rows.append((face, {
            "center_global_xyz_mm": list(center.toTuple()),
            "normal_global_xyz": list(normal.toTuple()),
            "area_mm2": face.Area(),
        }))
    rows.sort(key=lambda item: (
        tuple(round(v, 8) for v in item[1]["center_global_xyz_mm"]),
        tuple(round(v, 8) for v in item[1]["normal_global_xyz"]),
        round(item[1]["area_mm2"], 8),
    ))
    return {
        f"planar_face_{index:02d}": (face, {**row, "face_id": f"planar_face_{index:02d}"})
        for index, (face, row) in enumerate(rows, 1)
    }


def _axis_face(host_id: str, axes: list[dict], face_map: dict[str, tuple[cq.Face, dict]]):
    choices_by_axis = []
    for axis in axes:
        if axis["members"][1] != host_id:
            raise ValueError(f"Axis host differs from duty host: {axis['axis_id']}")
        start = cq.Vector(*axis["origin_global_xyz_mm"])
        direction = _unit(cq.Vector(*axis["axis_global_xyz"]))
        end = start + direction * axis["source_occupied_length_mm"]
        choices = []
        for face, row in face_map.values():
            normal = _unit(cq.Vector(*row["normal_global_xyz"]))
            if abs(abs(normal.dot(direction)) - 1) > 1e-7:
                continue
            center = face.Center()
            d0 = abs((start - center).dot(normal))
            d1 = abs((end - center).dot(normal))
            choices.append((min(d0, d1), face, row, d0, d1, normal.dot(direction)))
        if not choices:
            raise ValueError(f"No parallel source face for {axis['axis_id']}")
        choices_by_axis.append((axis, min(choices, key=lambda row: row[0])))
    counts: dict[str, int] = {}
    for _, choice in choices_by_axis:
        face_id = choice[2]["face_id"]
        counts[face_id] = counts.get(face_id, 0) + 1
    face_id = max(counts, key=counts.get)
    if counts[face_id] != len(axes):
        raise ValueError(f"Legacy axes split across host faces: {counts}")
    selected = next(choice for _, choice in choices_by_axis if choice[2]["face_id"] == face_id)
    return selected[1], selected[2], {
        "host_member": host_id,
        "physical_face_id": face_id,
        "face_normal_global_xyz": [round(v, 9) for v in selected[2]["normal_global_xyz"]],
        "face_center_global_xyz_mm": [round(v, 6) for v in selected[2]["center_global_xyz_mm"]],
        "face_area_mm2": round(selected[2]["area_mm2"], 6),
        "axis_ids": [axis["axis_id"] for axis, _ in choices_by_axis],
        "axis_face_gap_mm": [round(choice[0], 6) for _, choice in choices_by_axis],
        "axis_normal_alignment": [round(choice[5], 9) for _, choice in choices_by_axis],
    }


def _project(face: cq.Face, axis: cq.Vector) -> tuple[float, float]:
    values = [vertex.Center().dot(axis) for vertex in face.Vertices()]
    return min(values), max(values)


def _common_frame(face_a: cq.Face, row_a: dict, face_b: cq.Face, row_b: dict, axes: list[dict], wa: float, wb: float):
    na = _unit(cq.Vector(*row_a["normal_global_xyz"]))
    nb = _unit(cq.Vector(*row_b["normal_global_xyz"]))
    if abs(na.dot(nb)) > 1e-5:
        return None, {"mapping_status": "nonorthogonal_source_faces", "normal_dot": round(na.dot(nb), 9)}
    edge = _unit(na.cross(nb))
    da, db = na.dot(face_a.Center()), nb.dot(face_b.Center())
    corner = na * da + nb * db
    ea, eb = _project(face_a, edge), _project(face_b, edge)
    common = (max(ea[0], eb[0]), min(ea[1], eb[1]))
    group_center = sum(cq.Vector(*axis["origin_global_xyz_mm"]).dot(edge) for axis in axes) / len(axes)
    if common[1] - common[0] >= GRAIN_LENGTH_MM:
        ec = min(max(group_center, common[0] + GRAIN_LENGTH_MM / 2), common[1] - GRAIN_LENGTH_MM / 2)
    else:
        ec = (common[0] + common[1]) / 2
    origin = corner + edge * (ec - GRAIN_LENGTH_MM / 2)
    plane = cq.Plane(origin=origin, xDir=na, normal=edge)
    body = cq.Workplane(plane).box(wa, wb, GRAIN_LENGTH_MM, centered=(False, False, False)).val()
    contact_a = contact_b = None
    for face in body.Faces():
        if face.geomType() != "PLANE":
            continue
        normal = _unit(face.normalAt())
        center = face.Center()
        if normal.dot(-na) > 1 - 1e-7 and abs(center.dot(na) - da) < 1e-5:
            contact_a = face
        if normal.dot(-nb) > 1 - 1e-7 and abs(center.dot(nb) - db) < 1e-5:
            contact_b = face
    if contact_a is None or contact_b is None:
        return None, {"mapping_status": "candidate_contact_faces_not_found"}
    area_a = face_a.intersect(contact_a).Area()
    area_b = face_b.intersect(contact_b).Area()
    expected_a, expected_b = wb * GRAIN_LENGTH_MM, wa * GRAIN_LENGTH_MM
    da_range, db_range = _project(face_a, nb), _project(face_b, na)
    frame = {
        "mapping_status": "orthogonal_source_face_pair",
        "face_a_normal_global_xyz": _vec(na),
        "face_b_normal_global_xyz": _vec(nb),
        "common_edge_axis_global_xyz": _vec(edge),
        "interface_corner_global_xyz_mm": _vec(corner),
        "cleat_origin_global_xyz_mm": _vec(origin),
        "cleat_dimensions_mm": [wa, wb, GRAIN_LENGTH_MM],
        "common_face_edge_range_mm": [round(common[0], 6), round(common[1], 6)],
        "source_axis_group_edge_center_mm": round(group_center, 6),
        "cleat_center_edge_coordinate_mm": round(ec, 6),
        "face_a_available_span_mm": round(max(0, da_range[1] - db), 6),
        "face_b_available_span_mm": round(max(0, db_range[1] - da), 6),
        "face_a_contact_area_mm2": round(area_a, 6),
        "face_a_contact_fraction": round(min(1, area_a / expected_a), 6) if expected_a else 0,
        "face_b_contact_area_mm2": round(area_b, 6),
        "face_b_contact_fraction": round(min(1, area_b / expected_b), 6) if expected_b else 0,
        "cleat_bounds_global_xyz_mm": _bounds(body),
        "interface_datum_local_N_extents_mm": [
            round(min((v.Center() - corner).dot(N) for v in body.Vertices()), 6),
            round(max((v.Center() - corner).dot(N) for v in body.Vertices()), 6),
        ],
    }
    return body, frame


def _through_bolts(body: cq.Shape, frame: dict, hosts: tuple[str, str], wood: dict[str, cq.Shape], protected: dict[str, dict[str, cq.Shape]], wj03: dict[str, cq.Shape], wj04: dict[str, cq.Shape]):
    """Build four provisional straight bolt corridors, two through each host.

    Corridors span the cleat and the full projected depth of their intended
    host. Hardware stacks are not selected or modeled; this checks axes only.
    """
    corner = cq.Vector(*frame["interface_corner_global_xyz_mm"])
    na = cq.Vector(*frame["face_a_normal_global_xyz"])
    nb = cq.Vector(*frame["face_b_normal_global_xyz"])
    edge = cq.Vector(*frame["common_edge_axis_global_xyz"])
    ec = frame["cleat_center_edge_coordinate_mm"]
    wa, wb, _ = frame["cleat_dimensions_mm"]
    result = []
    shapes = {}
    for label, host_id, normal, transverse, cleat_thickness, plane_datum, second_width in (
        ("face_a", hosts[0], na, nb, wa, corner.dot(na), wb),
        ("face_b", hosts[1], nb, na, wb, corner.dot(nb), wa),
    ):
        host = wood[host_id]
        host_projections = [vertex.Center().dot(normal) for vertex in host.Vertices()]
        near = max(host_projections)
        far = min(host_projections)
        host_depth = plane_datum - far
        interface_mismatch = abs(near - plane_datum)
        direction = -normal
        for index, offset in enumerate((-AXIS_EDGE_OFFSET_MM, AXIS_EDGE_OFFSET_MM), 1):
            axis_id = f"{label}_through_bolt_{index}"
            start = (
                corner
                + normal * cleat_thickness
                + transverse * (second_width / 2)
                + edge * (ec + offset)
            )
            shaft_length = cleat_thickness + max(0.0, host_depth)
            shaft = cq.Solid.makeCylinder(AXIS_D_MM / 2, shaft_length, start, direction)
            projected_body_length = _volume(shaft, body) / (math.pi * (AXIS_D_MM / 2) ** 2)
            projected_host_length = _volume(shaft, host) / (math.pi * (AXIS_D_MM / 2) ** 2)
            other_wood = _hits(shaft, {name: shape for name, shape in wood.items() if name not in hosts})
            protected_hits = {
                family: hits for family, shapes_by_family in protected.items()
                if (hits := _hits(shaft, shapes_by_family))
            }
            record = {
                "axis_id": axis_id,
                "intended_host_member": host_id,
                "axis_diameter_mm": AXIS_D_MM,
                "origin_global_xyz_mm": _vec(start),
                "axis_global_xyz": _vec(direction),
                "edge_station_offset_from_cleat_center_mm": offset,
                "cleat_thickness_mm": cleat_thickness,
                "host_projected_depth_mm": round(host_depth, 6),
                "interface_face_projected_mismatch_mm": round(interface_mismatch, 6),
                "shaft_occupied_length_mm": round(shaft_length, 6),
                "nominal_bolt_length_mm_unselected": round(shaft_length, 1),
                "cleat_axis_intersection_length_mm": round(projected_body_length, 6),
                "host_axis_intersection_length_mm": round(projected_host_length, 6),
                "other_source_wood_hits_mm3": other_wood,
                "fixed_axis_and_service_hits_mm3": protected_hits,
                "wj03_trial_body_hits_mm3": _hits(shaft, wj03),
                "wj04_trial_body_hits_mm3": _hits(shaft, wj04),
                "through_path_geometry_status": (
                    "nominal_full_depth_corridor"
                    if interface_mismatch <= 0.01 and host_depth > 0 and abs(projected_host_length - host_depth) <= 0.05
                    else "host_face_or_full_depth_corridor_unresolved"
                ),
                "unresolved_hardware": "nut, washer, edge distance, tool access, and installed length not screened; no hardware size selected",
            }
            result.append(record)
            shapes[axis_id] = shaft
    for index, record in enumerate(result):
        peer_hits = {}
        for peer in result[index + 1:]:
            overlap = _volume(shapes[record["axis_id"]], shapes[peer["axis_id"]])
            if overlap > HIT_MM3:
                peer_hits[peer["axis_id"]] = round(overlap, 6)
        record["other_provisional_bolt_axis_hits_mm3"] = peer_hits
    return result, shapes


def _wj04_body(wood: dict[str, cq.Shape]) -> cq.Shape:
    rail = wood["base_rail_service_lower_right"]
    principal = wood["base_principal_center_right"]
    x0 = principal.BoundingBox().xmax
    t1 = max(v.Center().dot(T) for v in rail.Vertices())
    n0 = min(v.Center().dot(N) for v in rail.Vertices())
    n1 = max(v.Center().dot(N) for v in rail.Vertices())
    shape = cq.Solid.makeBox(95.25, 38.1, n1 - (n0 + 20.0))
    return shape.rotate((0, 0, 0), (1, 0, 0), 50).translate(
        cq.Vector(x0, 0, 0) + T * t1 + N * (n0 + 20.0)
    )


def _obstacles(source, inventory: dict) -> dict[str, dict[str, cq.Shape]]:
    parts = source.parts()
    tnuts = {p.name: p.shape for p in parts if p.name.startswith("hold_tnut_")}
    electrical = source.electrical_parts()
    lights = {p.name: p.shape for p in electrical if p.kind == "light"}
    wires = {p.name: p.shape for p in electrical if p.kind == "wire"}
    hold_paths = {}
    for datum in hold_datums(source):
        hold_paths[datum["name"]] = cq.Solid.makeCylinder(
            11.1125 / 2,
            50.8,
            cq.Vector(*datum["rear_seating_xyz_mm"]),
            -cq.Vector(*datum["barrel_into_panel_direction"]),
        )
    panel_rows = {row.name: row for row in source.panel_connections()}
    if len(panel_rows) != 66:
        raise ValueError("Expected exactly 66 fixed panel/kicker screw axes")
    panel_axes = {}
    for record in inventory["fixed_panel_kicker_screws"]:
        row = panel_rows[record["axis_id"]]
        panel_axes[row.name] = cq.Solid.makeCylinder(
            row.diameter / 2,
            record["shop_purchased_length_mm"],
            row.start,
            row.direction.normalized(),
        )
    frame_components = {}
    frame_access = {}
    for row in source.connections():
        if row.kind != "bolt":
            continue
        roles = ("shaft", "head_washer", "nut_washer", "head", "nut")
        components = row.components()
        if len(components) != 5:
            raise ValueError(f"Unexpected source bolt stack: {row.name}")
        frame_components.update({f"{row.name}/{role}": shape for role, shape in zip(roles, components, strict=True)})
        direction = row.direction.normalized()
        dim = source.bolt_dimensions(row)
        frame_access[f"{row.name}/head_tool"] = cq.Solid.makeCylinder(
            TOOL_D_MM / 2, TOOL_L_MM, row.start - direction * TOOL_L_MM, direction
        )
        nut_side = row.start + direction * (row.grip + dim["washer_thickness_mm"] + 2.0)
        frame_access[f"{row.name}/nut_tool"] = cq.Solid.makeCylinder(
            TOOL_D_MM / 2, TOOL_L_MM, nut_side, direction
        )
        frame_access[f"{row.name}/withdrawal"] = cq.Solid.makeCylinder(
            row.diameter / 2, 2 * row.length, row.start - direction * row.length, direction
        )
    if len(frame_components) != 60:
        raise ValueError("Expected five installed components on each of 12 starting bolts")
    return {
        "fixed_66_hillman_axes_63p5mm": panel_axes,
        "retained_12_frame_bolt_components": frame_components,
        "retained_12_frame_bolt_tools_withdrawals": frame_access,
        "tnuts": tnuts,
        "hold_hole_and_provisional_projection": hold_paths,
        "lights": lights,
        "wires": wires,
    }


def _trial_obstacle_hits(body: cq.Shape, hosts: tuple[str, str], wood: dict[str, cq.Shape], protected: dict[str, dict[str, cq.Shape]], wj03: dict[str, cq.Shape], wj04: dict[str, cq.Shape]):
    host_penetration = {}
    for host in hosts:
        v = _volume(body, wood[host])
        if v > HIT_MM3:
            host_penetration[host] = round(v, 6)
    other_wood = _hits(body, {name: shape for name, shape in wood.items() if name not in hosts})
    protected_hits = {
        family: hits for family, shapes in protected.items()
        if (hits := _hits(body, shapes))
    }
    return host_penetration, other_wood, protected_hits, _hits(body, wj03), _hits(body, wj04)


def _record_duty(duty: dict, wood, face_maps, protected, wj03, wj04):
    duty_id = duty["legacy_station_id"]
    hosts = tuple(duty["legacy_host_members"])
    axes = duty["legacy_sds_axes"]
    first = [a for a in axes if a["axis_role"] == "beam"]
    second = [a for a in axes if a["axis_role"] == "upright"]
    base = {
        "legacy_station_id": duty_id,
        "legacy_family": duty["legacy_family"],
        "side": duty["side"],
        "legacy_host_members": list(hosts),
        "legacy_sds_axis_ids": [a["axis_id"] for a in axes],
        "legacy_sds_axis_count": len(axes),
    }
    try:
        face_a, row_a, bind_a = _axis_face(hosts[0], first, face_maps[hosts[0]])
        face_b, row_b, bind_b = _axis_face(hosts[1], second, face_maps[hosts[1]])
    except ValueError as exc:
        return {
            **base,
            "replacement_owner": (
                f"wj05_center_node_{duty['side']}" if duty_id in WJ05_DUTIES else f"wj06_{duty_id}"
            ),
            "face_binding_status": "failed",
            "mapping_constraint": str(exc),
            "trial_variants": [],
            "candidate_layout_accepted": False,
        }, {}
    faces = [{"axis_group": "beam", **bind_a}, {"axis_group": "upright", **bind_b}]
    if duty_id in WJ05_DUTIES:
        return {
            **base,
            "replacement_owner": f"wj05_center_node_{duty['side']}",
            "replacement_topology": "integrated center node: header/principal and moved-post/header interfaces",
            "face_binding_status": "source-axis-to-planar-faces-bound",
            "interface_faces": faces,
            "placement_status": "excluded_from_generic_cleat_search_wj05_owned",
            "geometry_dependency": "WJ-05 must co-design moved center posts, both fixed center-kicker receivers, both inner kicker edge supports, and backer-to-frame paths.",
            "trial_variants": [],
            "candidate_layout_accepted": False,
        }, {}

    variants = []
    live_shapes = {}
    for wa in WIDTHS_MM:
        for wb in WIDTHS_MM:
            trial_id = f"wj06_{duty_id}_{wa:g}x{wb:g}x{GRAIN_LENGTH_MM:g}"
            body, frame = _common_frame(face_a, row_a, face_b, row_b, axes, wa, wb)
            if body is None:
                variants.append({
                    "trial_id": trial_id,
                    "dimensions_mm": [wa, wb, GRAIN_LENGTH_MM],
                    "mapping": frame,
                })
                continue
            host_pen, other_wood, p_hits, wj03_hits, wj04_hits = _trial_obstacle_hits(
                body, hosts, wood, protected, wj03, wj04
            )
            bolt_records, bolt_shapes = _through_bolts(
                body, frame, hosts, wood, protected, wj03, wj04
            )
            frame.update({
                "host_penetration_mm3": host_pen,
                "other_source_wood_hits_mm3": other_wood,
                "fixed_axis_and_service_hits_mm3": p_hits,
                "wj03_trial_body_hits_mm3": wj03_hits,
                "wj04_trial_body_hits_mm3": wj04_hits,
                "candidate_through_bolt_axes": bolt_records,
            })
            variants.append({
                "trial_id": trial_id,
                "dimensions_mm": [wa, wb, GRAIN_LENGTH_MM],
                "mapping": frame,
            })
            live_shapes[trial_id] = body
            live_shapes.update({f"{trial_id}::bolt::{axis_id}": shape for axis_id, shape in bolt_shapes.items()})

    mappable = [v for v in variants if v["mapping"].get("mapping_status") == "orthogonal_source_face_pair"]
    if not mappable:
        return {
            **base,
            "replacement_owner": f"wj06_{duty_id}",
            "replacement_topology": "one-piece solid-sawn orthogonal face cleat",
            "face_binding_status": "source-axis-to-planar-faces-bound",
            "interface_faces": faces,
            "placement_status": "generic_shape_not_mappable",
            "mapping_constraint": "No candidate cleat face pair mapped to both actual interface faces.",
            "trial_variants": variants,
            "candidate_layout_accepted": False,
        }, live_shapes

    def score(record):
        m = record["mapping"]
        h = len(m.get("host_penetration_mm3", {}))
        h += len(m.get("other_source_wood_hits_mm3", {}))
        h += sum(len(v) for v in m.get("fixed_axis_and_service_hits_mm3", {}).values())
        h += len(m.get("wj03_trial_body_hits_mm3", {}))
        h += len(m.get("wj04_trial_body_hits_mm3", {}))
        for bolt in m.get("candidate_through_bolt_axes", []):
            h += int(bolt["through_path_geometry_status"] != "nominal_full_depth_corridor")
            h += len(bolt["other_source_wood_hits_mm3"])
            h += sum(len(v) for v in bolt["fixed_axis_and_service_hits_mm3"].values())
            h += len(bolt["wj03_trial_body_hits_mm3"])
            h += len(bolt["wj04_trial_body_hits_mm3"])
            h += len(bolt["other_provisional_bolt_axis_hits_mm3"])
        support = min(m.get("face_a_contact_fraction", 0), m.get("face_b_contact_fraction", 0))
        volume = math.prod(record["dimensions_mm"])
        return h, -support, volume

    best = min(mappable, key=score)
    return {
        **base,
        "replacement_owner": f"wj06_{duty_id}",
        "replacement_topology": "one-piece solid-sawn orthogonal face cleat with two provisional ordinary through-bolts per face",
        "face_binding_status": "source-axis-to-planar-faces-bound",
        "interface_faces": faces,
        "placement_status": "diagnostic_trial_generated",
        "selected_trial_id": best["trial_id"],
        "selected_trial": best,
        "selected_trial_bounds_global_xyz_mm": best["mapping"]["cleat_bounds_global_xyz_mm"],
        "candidate_layout_accepted": False,
        "trial_variants": variants,
    }, live_shapes


def _report_markdown(report: dict) -> str:
    lines = [
        "# WJ-06 residual-duty cleat geometry diagnostic",
        "",
        "Status: diagnostic geometry only; no duty accepted.",
        "",
        "Reproduce with: uv run python -m scripts.wood_joint_wj06_residual_probe --write",
        "",
        (
            f"Coverage: {report['coverage']['residual_duty_count']} residual duties and "
            f"{report['coverage']['residual_legacy_sds_axis_count']} legacy SDS axes. "
            f"{report['coverage']['generic_cleat_trial_duty_count']} duties received nine "
            "face-cleat size trials; "
            f"{report['coverage']['wj05_center_dependency_count']} center duties remain "
            "assigned to WJ-05."
        ),
        "",
        (
            "Each generic trial uses a single solid-sawn timber block, grain along the "
            "common edge of the two actual host faces, no primary-member housing, and four "
            "provisional through-bolt axes. Occupied dimensions are CAD trial values only."
        ),
        "",
        "| Duty | Host pair | Source face pair | Trial result | Selected body blockers |",
        "|---|---|---|---|---:|",
    ]
    for duty in report["duties"]:
        pair = ", ".join(duty["legacy_host_members"])
        if not duty.get("interface_faces"):
            lines.append(f"| {duty['legacy_station_id']} | {pair} | unbound | {duty.get('placement_status', duty.get('face_binding_status'))} | — |")
            continue
        face_pair = " / ".join(face["physical_face_id"] for face in duty["interface_faces"])
        if duty.get("selected_trial"):
            selected = duty["selected_trial"]["mapping"]
            count = len(selected.get("host_penetration_mm3", {}))
            count += len(selected.get("other_source_wood_hits_mm3", {}))
            count += sum(len(h) for h in selected.get("fixed_axis_and_service_hits_mm3", {}).values())
            count += len(selected.get("wj03_trial_body_hits_mm3", {}))
            count += len(selected.get("wj04_trial_body_hits_mm3", {}))
            outcome = duty["selected_trial_id"]
        else:
            count = "—"
            outcome = duty.get("placement_status", "unresolved")
        lines.append(f"| {duty['legacy_station_id']} | {pair} | {face_pair} | {outcome} | {count} |")
    lines.extend([
        "",
        "The static obstacle screen includes all source wood, 66 purchased-length Hillman axis envelopes, 12 starting frame-bolt stacks plus nominal tool/withdrawal envelopes, T-nuts, provisional hold projections, lights, wires, and both WJ-03 trial nodes plus the revised WJ-04 cleat.",
        "",
        "## Limits",
        "",
        "- WJ-05 owns four center duties and must close moved-post/header, principal/header, both fixed center-kicker receiver paths, both inner-edge supports, and backer-to-frame attachment.",
        "- WJ-03 owners remain knee_outer_left and knee_outer_right; their geometry stays diagnostic with unresolved removal sequence and local-N exception.",
        "- WJ-04 owner remains its lower-right workhorse diagnostic: 95.25 × 38.1 × 119.7 mm provisional cleat, 6×6 blank dimensional lead, 6.352 mm nominal 50 mm tool gap, and open bolt edge/length/tolerance/mechanics checks.",
        "- Every trial remains nominal. Washer/nut products, bolt length and thread, tool access, tolerance fit, manufacturing, and transport remain unresolved.",
        "- No strength, stiffness, resistance, case pass, drilling, fabrication, structural, or climbing claim.",
        "",
        "Machine-readable JSON records all axes, all nine size variants per generic duty, face bindings, dimensions, collision volumes, source hashes, and explicit owner/dependency status.",
    ])
    return "\n".join(lines) + "\n"


def build_report() -> dict:
    inventory = json.loads(INVENTORY_PATH.read_text())
    if inventory["candidate"] != CANDIDATE:
        raise ValueError("Wood-joint candidate authority changed")
    duties = inventory["legacy_duties"]
    if len(duties) != 24 or sum(len(d["legacy_sds_axes"]) for d in duties) != 144:
        raise ValueError("Expected 24 legacy duties and 144 SDS axes")
    residual = [d for d in duties if d["legacy_station_id"] not in EXCLUDED_DIAGNOSTIC_DUTIES]
    if len(residual) != 19 or sum(len(d["legacy_sds_axes"]) for d in residual) != 114:
        raise ValueError("Expected 19 residual duties and 114 old SDS axes")
    source = variant(KERF_RIGHT)
    binding = validate_source_binding(source)
    wood = {part.name: part.shape for part in source.uncut_wood_parts()}
    face_maps = {name: _faces(shape) for name, shape in wood.items()}
    records = {row["part_id"]: row for row in inventory["parts"]}
    for name in wood:
        if set(face_maps[name]) != {face["face_id"] for face in records[name]["actual_planar_faces"]}:
            raise ValueError(f"Live planar faces drifted for {name}")
    protected = _obstacles(source, inventory)
    wj03_bodies = {}
    for side in ("left", "right"):
        wj03_bodies.update(make_wj03_trial_parts(side, wood))
    wj04_bodies = {"wj04_revised_workhorse_cleat": _wj04_body(wood)}
    result_rows = []
    chosen_shapes = {}
    chosen_axis_shapes = {}
    variants_by_owner = {}
    for duty in residual:
        record, live_shapes = _record_duty(duty, wood, face_maps, protected, wj03_bodies, wj04_bodies)
        result_rows.append(record)
        owner_id = record["replacement_owner"]
        variants_by_owner[owner_id] = live_shapes
        if record.get("selected_trial_id"):
            chosen_shapes[duty["legacy_station_id"]] = live_shapes[record["selected_trial_id"]]
            selected_mapping = record["selected_trial"]["mapping"]
            chosen_axis_shapes[duty["legacy_station_id"]] = {
                bolt["axis_id"]: live_shapes[f"{record['selected_trial_id']}::bolt::{bolt['axis_id']}"]
                for bolt in selected_mapping.get("candidate_through_bolt_axes", [])
            }

    # Screen each variant against every other owner's selected body. This is a
    # bounded neighbor check, not a combinatorial global placement search.
    for record in result_rows:
        owner_variants = variants_by_owner.get(record["replacement_owner"], {})
        for trial_variant in record.get("trial_variants", []):
            body = owner_variants.get(trial_variant["trial_id"])
            if body is None:
                continue
            others = {name: shape for name, shape in chosen_shapes.items() if name != record["legacy_station_id"]}
            trial_variant["neighbor_selected_body_hits_mm3"] = _hits(body, others)
            other_selected_axes = {
                f"{owner}/{axis_id}": shape
                for owner, axes_by_owner in chosen_axis_shapes.items()
                if owner != record["legacy_station_id"]
                for axis_id, shape in axes_by_owner.items()
            }
            for bolt in trial_variant["mapping"].get("candidate_through_bolt_axes", []):
                bolt_shape = owner_variants.get(
                    f"{trial_variant['trial_id']}::bolt::{bolt['axis_id']}"
                )
                if bolt_shape is None:
                    continue
                bolt["neighbor_selected_body_hits_mm3"] = _hits(bolt_shape, others)
                bolt["neighbor_selected_bolt_axis_hits_mm3"] = _hits(bolt_shape, other_selected_axes)
        if record.get("selected_trial"):
            selected_id = record["selected_trial_id"]
            selected_variant = next(v for v in record["trial_variants"] if v["trial_id"] == selected_id)
            record["selected_trial"]["neighbor_selected_body_hits_mm3"] = selected_variant.get("neighbor_selected_body_hits_mm3", {})

    coverage = {
        "source_legacy_duty_count": 24,
        "source_legacy_sds_axis_count": 144,
        "excluded_wj03_duty_count": 4,
        "excluded_wj03_sds_axis_count": 24,
        "excluded_wj04_duty_count": 1,
        "excluded_wj04_sds_axis_count": 6,
        "residual_duty_count": 19,
        "residual_legacy_sds_axis_count": 114,
        "owner_assignment_count": len(result_rows),
        "generic_cleat_trial_duty_count": sum(d["legacy_station_id"] not in WJ05_DUTIES for d in residual),
        "generic_cleat_trial_variant_count": sum(d["legacy_station_id"] not in WJ05_DUTIES for d in residual) * len(WIDTHS_MM) ** 2,
        "provisional_through_bolt_axis_count": sum(d["legacy_station_id"] not in WJ05_DUTIES for d in residual) * len(WIDTHS_MM) ** 2 * 4,
        "wj05_center_dependency_count": sum(d["legacy_station_id"] in WJ05_DUTIES for d in residual),
        "fixed_hillman_axes_screened": len(inventory["fixed_panel_kicker_screws"]),
        "starting_frame_bolt_arrangements_screened": len(inventory["starting_frame_bolts"]),
        "every_owner_has_exact_legacy_axis_ids": all(len(d["legacy_sds_axis_ids"]) == 6 for d in result_rows),
    }
    live_hashes = {
        name: _sha(ROOT / name)
        for name in (
            "scripts/wood_joint_wj06_residual_probe.py",
            "scripts/wood_joint_inventory.py",
            "scripts/wood_joint_wj04_probe.py",
            "scripts/wood_joint_clearance.py",
            "mini_moonboard/wood_joint_frame.py",
            "mini_moonboard/wood_joint_geometry.py",
            "mini_moonboard/connection_geometry.py",
            "mini_moonboard/floor_flush_width.py",
            "mini_moonboard/compact_floor_flush_frame.py",
            "mini_moonboard/hold_tnut_reinforcement.py",
        )
    }
    return {
        "schema": "wood_joint_wj06_residual_probe/v1",
        "candidate": CANDIDATE,
        "status": "diagnostic_only",
        "producer_command": "uv run python -m scripts.wood_joint_wj06_residual_probe --write",
        "source_binding": {
            "source_commit": inventory["source_commit"],
            "source_inventory_sha256": _sha(INVENTORY_PATH),
            "inventory_source_hashes_sha256": inventory["source_hashes_sha256"],
            "inventory_runtime_module_hashes_sha256": inventory["source_runtime_module_hashes_sha256"],
            "live_validation": {
                "inventory_sha256": binding.inventory_sha256,
                "uncut_part_shapes_sha256": binding.uncut_part_shapes_sha256,
                "fixed_screw_axes_sha256": binding.fixed_screw_axes_sha256,
                "frame_bolt_axes_sha256": binding.frame_bolt_axes_sha256,
            },
            "producer_and_dependency_sha256": live_hashes,
        },
        "coverage": coverage,
        "search": {
            "topology": "one-piece solid-sawn orthogonal face cleat",
            "primary_member_housings": False,
            "grain_axis": "actual shared edge of the two physical interface faces",
            "cross_dimensions_mm": list(WIDTHS_MM),
            "grain_length_mm": GRAIN_LENGTH_MM,
            "variants_per_generic_duty": len(WIDTHS_MM) ** 2,
            "provisional_through_bolts_per_trial": 4,
            "bolt_policy": "ordinary through-bolts with metal nuts and washers; axis placement diagnostic only",
        },
        "obstacle_counts": {
            "whole_source_wood_parts": len(wood),
            "fixed_66_hillman_axis_envelopes": len(protected["fixed_66_hillman_axes_63p5mm"]),
            "retained_frame_bolt_components": len(protected["retained_12_frame_bolt_components"]),
            "retained_frame_bolt_access_envelopes": len(protected["retained_12_frame_bolt_tools_withdrawals"]),
            "tnuts": len(protected["tnuts"]),
            "hold_paths": len(protected["hold_hole_and_provisional_projection"]),
            "lights": len(protected["lights"]),
            "wires": len(protected["wires"]),
            "wj03_trial_wood_bodies": len(wj03_bodies),
            "wj04_trial_wood_bodies": len(wj04_bodies),
        },
        "diagnostic_owners": [
            {
                "owner_id": f"knee_outer_{side}",
                "duty_ids": sorted(d for d in WJ03_DUTIES if d.endswith(f"_{side}")),
                "status": "partial_diagnostic",
                "body_envelope_local_n_exception_mm": 86.018477,
                "sequence_status": "open",
            }
            for side in ("left", "right")
        ] + [{
            "owner_id": "wj04_workhorse_clip_horizontal_lower_right_1",
            "duty_ids": [WJ04_DUTY],
            "status": "diagnostic_revise",
            "cleat_dimensions_mm": [95.25, 38.1, 119.7],
            "stock_lead": "solid 6x6 crosscut/rip; grade, kerf, yield unverified",
            "nominal_50mm_tool_gap_mm": 6.352,
            "limits": ["rail end/edge and bolt length margins open", "tolerance, access, and mechanics open"],
        }],
        "duties": result_rows,
        "limits": [
            "Owner assignment gives full bookkeeping coverage; it does not prove complete load path or acceptance.",
            "WJ-05 owns all four center duties and both fixed center-kicker receiver/inner-edge paths.",
            "Nominal body fit and collision checks do not include fabrication tolerances, full installed bolt stacks, tool access, or disassembly.",
            "Candidate bolt axes are provisional; no hardware SKU, resistance, stiffness, or capacity is selected.",
            "All 66 Hillman axes and all 12 frame-bolt arrangements remain fixed and are screened as source obstacles.",
            "No old angle capacity or case result transfers; no drilling, fabrication, structural, or climbing release.",
        ],
        "drilling_released": False,
        "fabrication_released": False,
        "structural_released": False,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    result = build_report()
    payload = json.dumps(result, indent=2, sort_keys=True) + "\n"
    markdown = _report_markdown(result)
    if args.write:
        OUT_JSON.write_text(payload)
        OUT_MD.write_text(markdown)
    else:
        print(markdown)


if __name__ == "__main__":
    main()
