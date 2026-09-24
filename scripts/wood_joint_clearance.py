"""WJ-03 nominal clearance and evidence export for mirrored outer nodes."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path

import cadquery as cq
from OCP.BRepTools import BRepTools

from mini_moonboard.floor_flush_width import KERF_RIGHT, variant
from mini_moonboard.wood_joint_frame import (
    BRIDGE_LENGTH_MM,
    CANDIDATE,
    LEGACY_DUTIES,
    LINK_LENGTH_MM,
    ORDINARY_REAR_ENVELOPE_MM,
    SPINE_LENGTH_MM,
    TOOL_DIAMETER_MM,
    TOOL_LENGTH_MM,
    access_shapes,
    bolt_axis_stroke_shapes,
    build_outer_nodes,
    detached_hardware_removal_shapes,
    installed_stack_shapes,
)
from mini_moonboard.wood_joint_geometry import bolt_stack_report, washer_support_report
from mini_moonboard.wood_joint_panel_machining import (
    PANEL_CONNECTION_COUNT,
    RIGHT_PANEL_NAMES,
    candidate_panel_replacements,
)
from scripts.owner_layout_protected import inventory as protected_inventory

ROOT = Path(__file__).resolve().parents[1]
SOURCE_INVENTORY = ROOT / "docs/wood-joints-mvp/source-inventory.json"
INTERFACES_OUTPUT = ROOT / "docs/wood-joints-mvp/interfaces.json"
CLEARANCE_OUTPUT = ROOT / "docs/wood-joints-mvp/clearance.json"
HARDWARE_OUTPUT = ROOT / "docs/wood-joints-mvp/hardware.json"
HIT_TOLERANCE_MM3 = 1e-6

ORIGINAL_SIX_CLASH_SIGNATURES = (
    "block/clip_timber_header_outer_left|bolt/clip_angle_base_left_header/shaft",
    "block/clip_timber_header_outer_left|bolt/clip_angle_base_left_header/head",
    "block/clip_timber_header_outer_left|bolt/clip_angle_base_left_header/near_washer",
    "block/clip_timber_header_outer_right|bolt/clip_angle_base_right_header/shaft",
    "block/clip_timber_header_outer_right|bolt/clip_angle_base_right_header/head",
    "block/clip_timber_header_outer_right|bolt/clip_angle_base_right_header/near_washer",
)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _canonical_sha256(value: object) -> str:
    def normalized(item):
        if isinstance(item, dict):
            return {key: normalized(row) for key, row in item.items()}
        if isinstance(item, (list, tuple)):
            return [normalized(row) for row in item]
        if isinstance(item, float):
            result = round(item, 6)
            return 0.0 if result == 0.0 else result
        return item

    return hashlib.sha256(
        json.dumps(normalized(value), sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def _producer_binding(command: str) -> dict:
    dependencies = (
        "scripts/wood_joint_clearance.py",
        "docs/panel-insert-reference.json",
        "mini_moonboard/base_frame.py",
        "mini_moonboard/floor_flush_width.py",
        "mini_moonboard/insert_frame.py",
        "mini_moonboard/panel_grid_v2.py",
        "mini_moonboard/wood_joint_frame.py",
        "mini_moonboard/wood_joint_geometry.py",
        "mini_moonboard/wood_joint_panel_machining.py",
        "scripts/owner_layout_protected.py",
    )
    return {
        "command": command,
        "dependency_sha256": {name: _sha256(ROOT / name) for name in dependencies},
        "input_artifact_sha256": {
            "docs/wood-joints-mvp/source-inventory.json": _sha256(SOURCE_INVENTORY)
        },
    }


def _wj03_protected_inventory(source=None) -> dict:
    """Use the retained purchased panel-screw length, not the CAD source length."""
    source = variant(KERF_RIGHT) if source is None else source
    base = protected_inventory()
    inventory = json.loads(
        (ROOT / "docs/wood-joints-mvp/source-inventory.json").read_text()
    )
    records = {row["axis_id"]: row for row in inventory["fixed_panel_kicker_screws"]}
    connections = {row.name: row for row in source.panel_connections()}
    if set(records) != set(connections) or len(records) != 66:
        raise ValueError("WJ-03 retained panel-screw inventory changed")
    purchased = {}
    for axis_id, record in records.items():
        row = connections[axis_id]
        if record["source_occupied_diameter_mm"] != row.diameter:
            raise ValueError(f"Panel-screw occupied diameter changed: {axis_id}")
        purchased[axis_id] = cq.Solid.makeCylinder(
            row.diameter / 2,
            record["shop_purchased_length_mm"],
            row.start,
            row.direction.normalized(),
        )
    retained_components = {}
    retained_tools = {}
    retained_withdrawal = {}
    for row in source.connections():
        if row.kind != "bolt":
            continue
        dimensions = source.bolt_dimensions(row)
        direction = row.direction.normalized()
        roles = ("shaft", "head_washer", "nut_washer", "head", "nut")
        components = row.components()
        if len(components) != len(roles):
            raise ValueError(f"Retained frame-bolt stack changed: {row.name}")
        retained_components.update(
            {
                f"{row.name}/{role}": shape
                for role, shape in zip(roles, components, strict=True)
            }
        )
        retained_tools[f"{row.name}/head_tool"] = cq.Solid.makeCylinder(
            TOOL_DIAMETER_MM / 2,
            TOOL_LENGTH_MM,
            row.start - direction * TOOL_LENGTH_MM,
            direction,
        )
        nut_side = row.start + direction * (
            row.grip + dimensions["washer_thickness_mm"] + 2.0
        )
        retained_tools[f"{row.name}/nut_tool"] = cq.Solid.makeCylinder(
            TOOL_DIAMETER_MM / 2,
            TOOL_LENGTH_MM,
            nut_side,
            direction,
        )
        shaft_start = row.start - direction * row.length
        retained_withdrawal[f"{row.name}/shaft_withdrawal"] = cq.Solid.makeCylinder(
            row.diameter / 2,
            2 * row.length,
            shaft_start,
            direction,
        )
        retained_withdrawal[f"{row.name}/head_withdrawal"] = cq.Solid.makeCylinder(
            max(row.diameter, dimensions["washer_od_mm"]) / 2,
            row.length,
            shaft_start,
            direction,
        )
    target_duties = {duty for duties in LEGACY_DUTIES.values() for duty in duties}
    target_sds = {
        axis["axis_id"]
        for row in inventory["legacy_duties"]
        if row["legacy_station_id"] in target_duties
        for axis in row["legacy_sds_axes"]
    }
    panel_axes = set(connections)
    retained_sds = {
        row.name: cq.Solid.makeCylinder(
            row.diameter / 2,
            row.length,
            row.start,
            row.direction.normalized(),
        )
        for row in source.connections()
        if row.kind == "screw"
        and row.name not in panel_axes
        and row.name not in target_sds
    }
    retained_connectors = {
        part.name: part.shape
        for part in source.parts()
        if part.name.startswith("clip_") and part.name not in target_duties
    }
    if len(retained_sds) != 120 or len(retained_connectors) != 20:
        raise ValueError("WJ-03 retained legacy connector inventory changed")
    solids = {
        **{key: value for key, value in base["solids"].items() if key != "frame_bolts"},
        "panel_screws": purchased,
        "frame_bolt_components": retained_components,
        "frame_bolt_tools": retained_tools,
        "frame_bolt_withdrawal": retained_withdrawal,
        "retained_legacy_sds": retained_sds,
        "retained_legacy_connectors": retained_connectors,
    }
    bounds = {
        family: {name: shape.BoundingBox() for name, shape in rows.items()}
        for family, rows in solids.items()
    }
    return {
        **base,
        "solids": solids,
        "bounds": bounds,
        "counts": {family: len(rows) for family, rows in solids.items()},
        "panel_screw_screen": {
            "count": len(purchased),
            "purchased_length_mm": 63.5,
            "diameter_basis": (
                "source occupied screw-shank CAD diameter; not a pilot, bit, "
                "published Hillman resistance diameter, or installation rule"
            ),
        },
        "retained_frame_bolt_screen": {
            "arrangements": 12,
            "installed_components": len(retained_components),
            "tool_sweeps": len(retained_tools),
            "withdrawal_sweeps": len(retained_withdrawal),
            "product_status": "source provisional dimensions; delivered hardware and tools unobserved",
        },
        "retained_legacy_screen": {
            "connector_bodies": len(retained_connectors),
            "sds_envelopes": len(retained_sds),
            "removed_target_connector_bodies": len(target_duties),
            "removed_target_sds_envelopes": len(target_sds),
        },
    }


def _protected_hits_exact(
    candidate_solids: dict[str, cq.Shape], protected: dict
) -> dict[str, dict[str, dict[str, float]]]:
    return {
        candidate: {
            family: collisions
            for family, members in protected["solids"].items()
            if (
                collisions := {
                    name: round(volume, 9)
                    for name, fixed in members.items()
                    if (volume := _volume(shape, fixed)) > HIT_TOLERANCE_MM3
                }
            )
        }
        for candidate, shape in candidate_solids.items()
    }


def _volume(first: cq.Shape, second: cq.Shape) -> float:
    a, b = first.BoundingBox(), second.BoundingBox()
    if (
        a.xmax <= b.xmin
        or b.xmax <= a.xmin
        or a.ymax <= b.ymin
        or b.ymax <= a.ymin
        or a.zmax <= b.zmin
        or b.zmax <= a.zmin
    ):
        return 0.0
    return first.intersect(second).Volume()


def _hits(
    features: dict[str, cq.Shape], obstacles: dict[str, cq.Shape]
) -> dict[str, float]:
    return {
        f"{feature}|{obstacle}": round(volume, 6)
        for feature, shape in features.items()
        for obstacle, other in obstacles.items()
        if (volume := _volume(shape, other)) > HIT_TOLERANCE_MM3
    }


def _bounds(shape: cq.Shape) -> list[float]:
    BRepTools.Clean_s(shape.wrapped)
    box = shape.BoundingBox()
    return [
        _rounded(value, 6)
        for value in (box.xmin, box.xmax, box.ymin, box.ymax, box.zmin, box.zmax)
    ]


def _vector(value) -> list[float]:
    return [_rounded(component, 6) for component in value.toTuple()]


def _rounded(value: float, digits: int = 6) -> float:
    result = round(value, digits)
    return 0.0 if abs(result) < 10 ** (-digits) else result


def _local_n_extents(shapes, datum: cq.Vector) -> dict[str, float]:
    transform = cq.Matrix()
    transform.rotateX(math.radians(-50.0))
    datum_n = datum.transform(transform).z
    bounds = []
    for shape in shapes:
        BRepTools.Clean_s(shape.wrapped)
        bounds.append(shape.transformShape(transform).BoundingBox())
    minimum = min(box.zmin for box in bounds) - datum_n
    maximum = max(box.zmax for box in bounds) - datum_n
    return {
        "n_min_mm": _rounded(minimum),
        "n_max_mm": _rounded(maximum),
        "span_mm": _rounded(maximum - minimum),
        "rearward_projection_mm": _rounded(maximum),
        "rearward_additional_over_ordinary_mm": _rounded(
            maximum - ORDINARY_REAR_ENVELOPE_MM
        ),
    }


def _local_extrema(shape: cq.Shape, datum: cq.Vector) -> dict[str, dict[str, float]]:
    transform = cq.Matrix()
    transform.rotateX(math.radians(-50.0))
    BRepTools.Clean_s(shape.wrapped)
    box = shape.transformShape(transform).BoundingBox()
    local_datum = datum.transform(transform)
    result = {}
    for name, minimum, maximum, offset in (
        ("X", box.xmin, box.xmax, local_datum.x),
        ("T", box.ymin, box.ymax, local_datum.y),
        ("N", box.zmin, box.zmax, local_datum.z),
    ):
        result[name] = {
            "min_mm": _rounded(minimum - offset),
            "max_mm": _rounded(maximum - offset),
            "span_mm": _rounded(maximum - minimum),
        }
    return result


def _minimum_z(shapes) -> float:
    result = []
    for shape in shapes:
        BRepTools.Clean_s(shape.wrapped)
        result.append(shape.BoundingBox().zmin)
    return min(result)


def _floor_plane_clearances(
    part_shapes,
    installed_shapes,
    tool_shapes,
    stroke_shapes,
    detached_shapes,
    retained_frame_bolt_shapes,
) -> dict[str, float]:
    """Keep each floor envelope tied to its named geometry family."""
    body_hardware = [*part_shapes, *installed_shapes]
    return {
        "connector_body": _minimum_z(part_shapes),
        "installed_hardware_only": _minimum_z(installed_shapes),
        "permanent_body_and_installed_hardware": _minimum_z(body_hardware),
        "tool_only": _minimum_z(tool_shapes),
        "body_hardware_and_tool": _minimum_z([*body_hardware, *tool_shapes]),
        "bolt_stroke_only": _minimum_z(stroke_shapes),
        "body_and_bolt_stroke": _minimum_z([*part_shapes, *stroke_shapes]),
        "detached_hardware_only": _minimum_z(detached_shapes),
        "body_hardware_and_detached_path": _minimum_z(
            [*body_hardware, *detached_shapes]
        ),
        **{
            family: _minimum_z(shapes)
            for family, shapes in retained_frame_bolt_shapes.items()
        },
    }


def _part_record(part) -> dict:
    record = {
        "part_id": part.id,
        "stock_product": part.stock_product,
        "actual_dimensions_mm": list(part.actual_dimensions_mm),
        "material": part.material,
        "grain_axis_global_xyz": _vector(part.grain_axis),
        "uncut_bounds_xyz_mm": _bounds(part.uncut_shape),
        "finished_bounds_xyz_mm": _bounds(part.finished_shape),
        "modification_ids": [cut.id for cut in part.modifications],
        "bore_ids": [cut.id for cut in part.modifications if cut.kind == "bore"],
        "modification_bounds_xyz_mm": {
            cut.id: _bounds(cut.removed_shape) for cut in part.modifications
        },
        "uncut_volume_mm3": round(part.uncut_shape.Volume(), 6),
        "finished_volume_mm3": round(part.finished_shape.Volume(), 6),
        "source_sha256": part.source_sha256,
        "fabrication_method": part.fabrication_method,
    }
    record["finished_geometry_sha256"] = _canonical_sha256(record)
    return record


def _interface_record(interface) -> dict:
    frame = interface.frame
    return {
        "interface_id": interface.id,
        "body_ids": list(interface.body_ids),
        "legacy_duties": list(interface.legacy_duties),
        "contact_face_ids": list(interface.contact_face_ids),
        "contact_frame": {
            "origin_global_xyz_mm": _vector(frame.origin),
            "x_global_xyz": _vector(frame.x),
            "t_global_xyz": _vector(frame.t),
            "n_global_xyz": _vector(frame.n),
        },
        "force_reference_point_global_xyz_mm": _vector(interface.force_reference_point),
        "behavior": interface.behavior,
        "bolt_group_ids": list(interface.bolt_group_ids),
        "bolt_penetration_order": list(interface.bolt_penetration_order),
        "separates_for_move": interface.separates_for_move,
        "access_sequence": list(interface.access_sequence),
    }


def interface_document(nodes=None) -> dict:
    nodes = build_outer_nodes() if nodes is None else nodes
    owners = []
    parts = []
    interfaces = []
    source_parts = {}
    for node in nodes.values():
        owners.append(
            {
                "owner_id": node.owner_id,
                "side": node.side,
                "legacy_duties": list(node.duties),
                "source_hosts": list(node.source_hosts),
                "part_ids": list(node.parts),
                "interface_ids": [row.id for row in node.interfaces],
                "replacement_path_complete_for_layout": True,
                "strength_complete": False,
            }
        )
        parts.extend(_part_record(part) for part in node.parts.values())
        source_parts.update(node.source_host_parts)
        interfaces.extend(_interface_record(row) for row in node.interfaces)
    binding = next(iter(nodes.values())).source_binding
    source_records = [_part_record(source_parts[name]) for name in sorted(source_parts)]
    geometry_fingerprint = _canonical_sha256(
        {
            "parts": {row["part_id"]: row["finished_geometry_sha256"] for row in parts},
            "source_hosts": {
                row["part_id"]: row["finished_geometry_sha256"]
                for row in source_records
            },
            "interfaces": interfaces,
        }
    )
    return {
        "schema": "wood_joint_outer_interfaces/v1",
        "candidate": CANDIDATE,
        "scope": "WJ-03 mirrored outer nodes only",
        "duty_owners": owners,
        "parts": parts,
        "changed_source_hosts": source_records,
        "interfaces": interfaces,
        "source_binding": {
            "source_commit": json.loads(SOURCE_INVENTORY.read_text())["source_commit"],
            "source_inventory_sha256": binding.inventory_sha256,
            "runtime_module_sha256": binding.runtime_module_sha256,
            "uncut_part_shapes_sha256": binding.uncut_part_shapes_sha256,
            "uncut_host_shape_sha256": binding.uncut_host_shape_sha256,
            "duty_host_mapping": {
                name: list(hosts) for name, hosts in binding.duty_host_mapping.items()
            },
            "fixed_screw_axes_sha256": binding.fixed_screw_axes_sha256,
            "frame_bolt_axes_sha256": binding.frame_bolt_axes_sha256,
        },
        "geometry_fingerprint_sha256": geometry_fingerprint,
        "producer": _producer_binding(
            "uv run python -m scripts.wood_joint_clearance --write"
        ),
        "counts": {
            "legacy_duties": 4,
            "nodes": 2,
            "cut_wood_parts": len(parts),
            "changed_source_hosts": len(source_records),
            "source_host_bores": sum(len(row["bore_ids"]) for row in source_records),
            "interfaces": len(interfaces),
        },
        "release_flags": {
            "layout_accepted": False,
            "hardware_selected": False,
            "drilling_released": False,
            "fabrication_released": False,
            "structural_released": False,
        },
    }


def hardware_document(nodes=None) -> dict:
    nodes = build_outer_nodes() if nodes is None else nodes
    records = []
    for node in nodes.values():
        for stack in node.stacks.values():
            report = bolt_stack_report(stack)
            records.append(
                {
                    "bolt_id": stack.id,
                    "side": node.side,
                    "candidate_specification": stack.hardware.candidate_sku,
                    "steel_diameter_mm": stack.hardware.steel_diameter_mm,
                    "cad_occupied_diameter_mm": stack.hardware.cad_occupied_diameter_mm,
                    "provisional_drill_diameter_mm": stack.hardware.drill_diameter_mm,
                    "under_head_length_mm": stack.hardware.under_head_length_mm,
                    "wood_grip_mm": report.grip_mm,
                    "required_under_head_length_mm": report.required_under_head_length_mm,
                    "length_margin_mm": report.length_margin_mm,
                    "provisional_thread_envelope_passes": report.nut_on_usable_thread,
                    "stack_length_passes": report.passes,
                    "penetration_order": [layer.body_id for layer in stack.layers],
                    "head_origin_global_xyz_mm": list(stack.head_seat.center.toTuple()),
                    "axis_global_xyz": list(stack.direction.toTuple()),
                    "head_washer_od_mm": stack.hardware.washer_od_mm,
                    "nut_washer_od_mm": stack.hardware.washer_od_mm,
                    "required_tip_projection_mm": stack.required_tip_projection_mm,
                    "procurement_selected": False,
                }
            )
    lengths = {}
    for record in records:
        key = str(record["under_head_length_mm"])
        lengths[key] = lengths.get(key, 0) + 1
    binding = next(iter(nodes.values())).source_binding
    geometry_fingerprint = _canonical_sha256(records)
    return {
        "schema": "wood_joint_outer_hardware/v1",
        "candidate": CANDIDATE,
        "scope": "WJ-03 nominal installed geometry; procurement unselected",
        "bolts": records,
        "source_binding": {
            "source_commit": json.loads(SOURCE_INVENTORY.read_text())["source_commit"],
            "source_inventory_sha256": binding.inventory_sha256,
            "uncut_part_shapes_sha256": binding.uncut_part_shapes_sha256,
            "fixed_screw_axes_sha256": binding.fixed_screw_axes_sha256,
            "frame_bolt_axes_sha256": binding.frame_bolt_axes_sha256,
        },
        "geometry_fingerprint_sha256": geometry_fingerprint,
        "producer": _producer_binding(
            "uv run python -m scripts.wood_joint_clearance --write"
        ),
        "counts": {
            "bolts_total": len(records),
            "bolts_per_node": 10,
            "washers_total": 2 * len(records),
            "nuts_total": len(records),
            "nominal_length_counts_mm": lengths,
        },
        "limits": [
            "Provisional thread intervals support geometry checks only.",
            "No bolt grade, SKU, delivered shank/thread transition, washer product, nut product, drill bit, or resistance is selected.",
            "Occupied CAD diameter, drill diameter, and steel resistance diameter remain separate fields.",
        ],
        "connector_stock_summary": {
            "nominal_stock": "one 8-ft 4x4 geometrically supplies all six cut parts before saw kerf and defects",
            "required_clear_length_before_kerf_mm": round(
                2 * (SPINE_LENGTH_MM + BRIDGE_LENGTH_MM + LINK_LENGTH_MM), 3
            ),
            "purchased_stock_length_mm": 2438.4,
            "yield_is_geometry_only": True,
        },
        "hardware_selected": False,
        "drilling_released": False,
        "structural_released": False,
    }


def _screen_node(node, wood, protected) -> dict:
    part_shapes = {name: part.finished_shape for name, part in node.parts.items()}
    geometry = {
        **{f"wood/{name}": shape for name, shape in wood.items()},
        **{f"connector/{name}": shape for name, shape in part_shapes.items()},
    }
    kicker_name = f"wood/kicker_{node.side}"
    panel_off_geometry = {
        name: shape for name, shape in geometry.items() if name != kicker_name
    }
    part_wood_hits = _hits(part_shapes, wood)
    connector_pair_hits = {}
    part_ids = tuple(part_shapes)
    for index, first in enumerate(part_ids):
        for second in part_ids[index + 1 :]:
            connector_pair_hits.update(
                _hits({first: part_shapes[first]}, {second: part_shapes[second]})
            )
    fixed_part_hits = {
        name: rows
        for name, rows in _protected_hits_exact(part_shapes, protected).items()
        if rows
    }
    retained_hardware = {
        family: protected["solids"][family]
        for family in ("panel_screws", "frame_bolt_components")
    }
    source_host_hardware_hits = {
        name: rows
        for name, rows in _protected_hits_exact(
            {
                name: part.finished_shape
                for name, part in node.source_host_parts.items()
            },
            {"solids": retained_hardware},
        ).items()
        if rows
    }

    installed = {key: installed_stack_shapes(row) for key, row in node.stacks.items()}
    tools = {key: access_shapes(row) for key, row in node.stacks.items()}
    strokes = {key: bolt_axis_stroke_shapes(row) for key, row in node.stacks.items()}
    detached = {
        key: detached_hardware_removal_shapes(row) for key, row in node.stacks.items()
    }
    all_installed = {
        f"{bolt_id}/{role}": shape
        for bolt_id, rows in installed.items()
        for role, shape in rows.items()
    }
    body_shapes = {**wood, **part_shapes}
    washer_reports = {}
    panel_on_detached_hits = {}
    failures = {
        "part_source_wood_positive_volume": part_wood_hits,
        "connector_connector_positive_volume": connector_pair_hits,
        "part_protected": fixed_part_hits,
        "source_host_retained_hardware": source_host_hardware_hits,
        "hardware_geometry": {},
        "hardware_cross_bolt": {},
        "hardware_protected": {},
        "tool_geometry": {},
        "tool_other_hardware": {},
        "tool_protected": {},
        "bolt_axis_stroke_geometry": {},
        "bolt_axis_stroke_other_hardware": {},
        "bolt_axis_stroke_protected": {},
        "detached_hardware_geometry": {},
        "detached_hardware_other_hardware": {},
        "detached_hardware_protected": {},
        "washer_seat_support": {},
    }
    bolt_reports = {}
    for bolt_id, stack in node.stacks.items():
        own_installed = {
            f"{bolt_id}/{role}": shape for role, shape in installed[bolt_id].items()
        }
        own_tools = {
            f"{bolt_id}/{role}": shape for role, shape in tools[bolt_id].items()
        }
        own_strokes = {
            f"{bolt_id}/{role}": shape for role, shape in strokes[bolt_id].items()
        }
        own_detached = {
            f"{bolt_id}/{role}": shape for role, shape in detached[bolt_id].items()
        }
        other_installed = {
            name: shape
            for name, shape in all_installed.items()
            if not name.startswith(f"{bolt_id}/")
        }
        hardware_geometry = _hits(own_installed, geometry)
        tool_geometry = _hits(own_tools, geometry)
        tool_hardware = _hits(own_tools, other_installed)
        stroke_geometry = _hits(own_strokes, geometry)
        stroke_hardware = _hits(own_strokes, other_installed)
        panel_on_detached_hits.update(_hits(own_detached, geometry))
        detached_geometry = _hits(own_detached, panel_off_geometry)
        detached_hardware = _hits(own_detached, other_installed)
        protected_hardware = {
            key: value
            for key, value in _protected_hits_exact(own_installed, protected).items()
            if value
        }
        protected_tool = {
            key: value
            for key, value in _protected_hits_exact(own_tools, protected).items()
            if value
        }
        protected_stroke = {
            key: value
            for key, value in _protected_hits_exact(own_strokes, protected).items()
            if value
        }
        protected_detached = {
            key: value
            for key, value in _protected_hits_exact(own_detached, protected).items()
            if value
        }
        failures["hardware_geometry"].update(hardware_geometry)
        failures["hardware_protected"].update(protected_hardware)
        failures["tool_geometry"].update(tool_geometry)
        failures["tool_other_hardware"].update(tool_hardware)
        failures["tool_protected"].update(protected_tool)
        failures["bolt_axis_stroke_geometry"].update(stroke_geometry)
        failures["bolt_axis_stroke_other_hardware"].update(stroke_hardware)
        failures["bolt_axis_stroke_protected"].update(protected_stroke)
        failures["detached_hardware_geometry"].update(detached_geometry)
        failures["detached_hardware_other_hardware"].update(detached_hardware)
        failures["detached_hardware_protected"].update(protected_detached)

        support = {}
        for end, seat in (("head", stack.head_seat), ("nut", stack.nut_seat)):
            report = washer_support_report(
                seat, body_shapes[seat.body_id], stack.hardware
            )
            support[end] = {
                "body_id": report.body_id,
                "support_fraction": round(report.support_fraction, 9),
                "unsupported_area_mm2": round(report.unsupported_area_mm2, 9),
                "full_seat": report.full_seat,
            }
            if not report.full_seat:
                failures["washer_seat_support"][f"{bolt_id}/{end}"] = support[end]
        washer_reports[bolt_id] = support
        stack_report = bolt_stack_report(stack)
        bolt_reports[bolt_id] = {
            "grip_mm": stack_report.grip_mm,
            "required_under_head_length_mm": stack_report.required_under_head_length_mm,
            "available_under_head_length_mm": stack_report.available_under_head_length_mm,
            "length_margin_mm": stack_report.length_margin_mm,
            "nut_on_provisional_usable_thread": stack_report.nut_on_usable_thread,
            "stack_length_passes": stack_report.passes,
            "washer_support": support,
            "installed_envelope_bounds_xyz_mm": {
                role: _bounds(shape) for role, shape in installed[bolt_id].items()
            },
            "access_sweep_bounds_xyz_mm": {
                role: _bounds(shape) for role, shape in tools[bolt_id].items()
            },
            "access_sweep_result": {
                "geometry_hits": tool_geometry,
                "other_installed_hardware_hits": tool_hardware,
                "protected_geometry_hits": protected_tool,
                "passes_nominal_screen": not (
                    tool_geometry or tool_hardware or protected_tool
                ),
            },
            "straight_bolt_insertion_and_reverse_withdrawal": {
                "sweep_bounds_xyz_mm": {
                    role: _bounds(shape) for role, shape in strokes[bolt_id].items()
                },
                "geometry_hits": stroke_geometry,
                "other_installed_hardware_hits": stroke_hardware,
                "protected_geometry_hits": protected_stroke,
                "passes_nominal_screen": not (
                    stroke_geometry or stroke_hardware or protected_stroke
                ),
            },
            "detached_hardware_removal": {
                "panel_state": f"kicker_{node.side} removed before node nut removal",
                "sweep_bounds_xyz_mm": {
                    role: _bounds(shape) for role, shape in detached[bolt_id].items()
                },
                "geometry_hits": detached_geometry,
                "other_installed_hardware_hits": detached_hardware,
                "protected_geometry_hits": protected_detached,
                "passes_nominal_screen": not (
                    detached_geometry or detached_hardware or protected_detached
                ),
            },
            "hardware_clearance_result": {
                "geometry_hits": hardware_geometry,
                "protected_geometry_hits": protected_hardware,
                "passes_nominal_screen": not (hardware_geometry or protected_hardware),
            },
        }

    bolt_ids = tuple(installed)
    for index, first in enumerate(bolt_ids):
        for second in bolt_ids[index + 1 :]:
            failures["hardware_cross_bolt"].update(
                _hits(
                    {f"{first}/{k}": v for k, v in installed[first].items()},
                    {f"{second}/{k}": v for k, v in installed[second].items()},
                )
            )

    floor_member = wood[f"base_floor_{node.side}"].BoundingBox()
    spine = node.parts[f"knee_outer_{node.side}_spine"].finished_shape.BoundingBox()
    bridge = node.parts[
        f"knee_outer_{node.side}_rear_bridge"
    ].finished_shape.BoundingBox()
    header = wood["base_header"].BoundingBox()
    bottom_rail = wood[f"base_rail_bottom_{node.side}"]
    link = node.parts[f"knee_outer_{node.side}_under_header_link"].finished_shape
    kicker_number = "1" if node.side == "left" else "10"
    kicker_obstacles = tuple(
        shape
        for family in ("tnuts", "hold_hole_and_trial_projection")
        for name, shape in protected["solids"][family].items()
        if name == f"hold_tnut_kicker_{kicker_number}"
    )
    post_box = wood[f"base_post_outer_{node.side}"].BoundingBox()
    datum = cq.Vector(
        post_box.xmin if node.side == "left" else post_box.xmax,
        header.ymax,
        header.zmin,
    )
    installed_shapes = list(all_installed.values())
    tool_shapes = [shape for rows in tools.values() for shape in rows.values()]
    stroke_shapes = [shape for rows in strokes.values() for shape in rows.values()]
    detached_shapes = [shape for rows in detached.values() for shape in rows.values()]
    retained_frame_bolt_shapes = {
        "retained_frame_bolt_installed_components": list(
            protected["solids"]["frame_bolt_components"].values()
        ),
        "retained_frame_bolt_tool_sweeps": list(
            protected["solids"]["frame_bolt_tools"].values()
        ),
        "retained_frame_bolt_withdrawal_sweeps": list(
            protected["solids"]["frame_bolt_withdrawal"].values()
        ),
    }
    local_n_envelopes = {
        "connector_body": _local_n_extents(part_shapes.values(), datum),
        "installed_hardware_only": _local_n_extents(installed_shapes, datum),
        "permanent_body_and_installed_hardware": _local_n_extents(
            [*part_shapes.values(), *installed_shapes], datum
        ),
        "tool_only": _local_n_extents(tool_shapes, datum),
        "body_hardware_and_tool": _local_n_extents(
            [*part_shapes.values(), *installed_shapes, *tool_shapes], datum
        ),
        "bolt_stroke_only": _local_n_extents(stroke_shapes, datum),
        "body_and_bolt_stroke": _local_n_extents(
            [*part_shapes.values(), *stroke_shapes], datum
        ),
        "detached_hardware_only": _local_n_extents(detached_shapes, datum),
        "body_hardware_and_detached_path": _local_n_extents(
            [*part_shapes.values(), *installed_shapes, *detached_shapes], datum
        ),
    }
    connector_minimum_z = _minimum_z(part_shapes.values())
    physical_shapes = [*part_shapes.values(), *all_installed.values()]
    minimum_z = _minimum_z(physical_shapes)
    floor_clearances = _floor_plane_clearances(
        list(part_shapes.values()),
        installed_shapes,
        tool_shapes,
        stroke_shapes,
        detached_shapes,
        retained_frame_bolt_shapes,
    )
    named_clearances = {
        "connector_body_to_base_floor_member_vertical_mm": round(
            spine.zmin - floor_member.zmax, 6
        ),
        "connector_body_to_floor_plane_z0_mm": round(connector_minimum_z, 6),
        "connector_and_installed_hardware_to_floor_plane_z0_mm": round(minimum_z, 6),
        "floor_plane_clearance_by_family_mm": {
            key: _rounded(value) for key, value in floor_clearances.items()
        },
        "header_tool_to_bottom_rail_exact_mm": round(
            min(
                shape.distance(bottom_rail)
                for key, row in tools.items()
                if "_header_" in key
                for shape in row.values()
            ),
            6,
        ),
        "side_tool_to_bottom_rail_exact_mm": round(
            min(
                shape.distance(bottom_rail)
                for key, row in tools.items()
                if "_side_" in key
                for shape in row.values()
            ),
            6,
        ),
        "post_nut_tool_to_shifted_link_exact_mm": round(
            min(
                row["nut"].distance(link)
                for key, row in tools.items()
                if "_post_" in key
            ),
            6,
        ),
        "bridge_link_tool_to_outer_kicker_hardware_exact_mm": round(
            min(
                shape.distance(obstacle)
                for key, row in tools.items()
                if "_bridge_link_" in key
                for shape in row.values()
                for obstacle in kicker_obstacles
            ),
            6,
        ),
        "rear_bridge_to_header_rear_mm": round(header.ymin - bridge.ymax, 6),
        "local_frame": {
            "datum_name": "outer post/header-front-bottom corner",
            "origin_global_xyz_mm": _vector(datum),
            "x_global_xyz": [1.0, 0.0, 0.0],
            "t_global_xyz": [
                0.0,
                _rounded(math.cos(math.radians(50.0)), 12),
                _rounded(math.sin(math.radians(50.0)), 12),
            ],
            "n_global_xyz": [
                0.0,
                _rounded(-math.sin(math.radians(50.0)), 12),
                _rounded(math.cos(math.radians(50.0)), 12),
            ],
            "right_handed": True,
        },
        "ordinary_rear_envelope_mm": ORDINARY_REAR_ENVELOPE_MM,
        "local_n_envelopes_mm": local_n_envelopes,
    }
    return {
        "owner_id": node.owner_id,
        "side": node.side,
        "legacy_duties": list(node.duties),
        "distinct_source_hosts": list(node.source_hosts),
        "part_bounds_xyz_mm": {
            part_id: _bounds(part.finished_shape)
            for part_id, part in node.parts.items()
        },
        "part_face_widths_mm": {
            part_id: {
                "global_x": round(part.uncut_shape.BoundingBox().xlen, 6),
                "global_y": round(part.uncut_shape.BoundingBox().ylen, 6),
                "global_z": round(part.uncut_shape.BoundingBox().zlen, 6),
            }
            for part_id, part in node.parts.items()
        },
        "connector_part_local_extrema": {
            part_id: _local_extrema(part.finished_shape, datum)
            for part_id, part in node.parts.items()
        },
        "changed_source_host_local_extrema": {
            part_id: _local_extrema(part.finished_shape, datum)
            for part_id, part in node.source_host_parts.items()
        },
        "contact_areas_mm2": {
            key: round(value, 3) for key, value in node.contact_areas_mm2.items()
        },
        "installed_hardware_count": len(node.stacks),
        "bolt_reports": bolt_reports,
        "washer_support_reports": washer_reports,
        "nominal_tool": {
            "diameter_mm": TOOL_DIAMETER_MM,
            "length_mm": TOOL_LENGTH_MM,
            "both_ends_screened": True,
        },
        "named_clearances": named_clearances,
        "failure_groups": failures,
        "panel_on_detached_path_hits": panel_on_detached_hits,
        "nominal_interference_free": not any(failures.values()),
        "kicker_panel_removal_sequence_verified": False,
        "floor_contact": min(floor_clearances.values()) <= 0.0,
        "reverse_removal_sequence": [
            f"Remove kicker_{node.side} and its retained screws before removing node nuts; validate that panel operation in WJ-03 before layout advancement.",
            "Confirm operator open space and selected real tools before loosening node hardware.",
            "Support three connector pieces, remove ten nuts/washers, withdraw ten bolts, and separate bridge, link, and spine.",
        ],
    }


def _validated_panel_replacements(source, panel_replacements=None) -> dict:
    if getattr(source, "option", None) != KERF_RIGHT:
        raise ValueError("WJ-03 panel replacements require the kerf-right source")
    if panel_replacements is None:
        panel_replacements = candidate_panel_replacements(
            source,
            current_parts=source.parts(),
            uncut_parts=source.uncut_wood_parts(),
        )
    if set(panel_replacements) != RIGHT_PANEL_NAMES:
        raise ValueError(
            "WJ-03 panel replacement map must contain exactly the three right panels"
        )
    for name, part in panel_replacements.items():
        if getattr(part, "name", None) != name or getattr(part, "shape", None) is None:
            raise ValueError(f"Invalid WJ-03 panel replacement: {name}")
    if len(source.panel_connections()) != PANEL_CONNECTION_COUNT:
        raise ValueError("WJ-03 panel replacement source must retain all panel axes")
    return panel_replacements


def build_clearance_report(nodes=None, *, source=None, panel_replacements=None) -> dict:
    nodes = build_outer_nodes() if nodes is None else nodes
    source = variant(KERF_RIGHT) if source is None else source
    panel_replacements = _validated_panel_replacements(source, panel_replacements)
    wood = {part.name: part.shape for part in source.uncut_wood_parts()}
    wood.update({name: part.shape for name, part in panel_replacements.items()})
    source_hosts = {
        name: part.finished_shape
        for node in nodes.values()
        for name, part in node.source_host_parts.items()
    }
    wood.update(source_hosts)
    protected = _wj03_protected_inventory(source)
    rows = {side: _screen_node(node, wood, protected) for side, node in nodes.items()}
    clear = all(row["nominal_interference_free"] for row in rows.values())
    envelope_keys = tuple(
        next(iter(rows.values()))["named_clearances"]["local_n_envelopes_mm"]
    )
    projections = {
        key: {
            metric: max(
                row["named_clearances"]["local_n_envelopes_mm"][key][metric]
                for row in rows.values()
            )
            for metric in (
                "n_max_mm",
                "span_mm",
                "rearward_projection_mm",
                "rearward_additional_over_ordinary_mm",
            )
        }
        for key in envelope_keys
    }
    binding = next(iter(nodes.values())).source_binding
    report = {
        "schema": "wood_joint_outer_clearance/v1",
        "candidate": CANDIDATE,
        "scope": "WJ-03 mirrored outer nodes only",
        "source_inventory": {
            "fixed_panel_kicker_screws": len(source.panel_connections()),
            "retained_frame_bolts": len(
                [row for row in source.connections() if row.kind == "bolt"]
            ),
            "protected_counts": protected["counts"],
            "panel_screw_screen": protected["panel_screw_screen"],
            "retained_frame_bolt_screen": protected["retained_frame_bolt_screen"],
            "retained_legacy_screen": protected["retained_legacy_screen"],
        },
        "source_binding": {
            "source_commit": json.loads(SOURCE_INVENTORY.read_text())["source_commit"],
            "source_inventory_sha256": binding.inventory_sha256,
            "runtime_module_sha256": binding.runtime_module_sha256,
            "uncut_part_shapes_sha256": binding.uncut_part_shapes_sha256,
            "uncut_host_shape_sha256": binding.uncut_host_shape_sha256,
            "fixed_screw_axes_sha256": binding.fixed_screw_axes_sha256,
            "frame_bolt_axes_sha256": binding.frame_bolt_axes_sha256,
        },
        "original_six_clash_signatures": {
            signature: "absent_replaced_topology"
            for signature in ORIGINAL_SIX_CLASH_SIGNATURES
        },
        "nodes": rows,
        "original_six_clashes_absent": True,
        "replacement_nominal_interference_free": clear,
        "advance_layout": False,
        "tolerance_aware_clearance_complete": False,
        "decision": "revise_named_constraint",
        "rear_projection_summary_mm": projections,
        "named_constraint_revisions": [
            {
                "constraint": "outer-node installed rear envelope",
                "existing_mm": ORDINARY_REAR_ENVELOPE_MM,
                "required_mm": projections["permanent_body_and_installed_hardware"][
                    "rearward_projection_mm"
                ],
                "additional_projection_mm": projections[
                    "permanent_body_and_installed_hardware"
                ]["rearward_additional_over_ordinary_mm"],
                "reason": "The exact canonical local-N maximum of connector bodies plus installed hardware controls the permanent envelope.",
            },
            {
                "constraint": "outer-node temporary bolt insertion envelope",
                "existing_mm": ORDINARY_REAR_ENVELOPE_MM,
                "required_mm": projections["body_and_bolt_stroke"][
                    "rearward_projection_mm"
                ],
                "additional_projection_mm": projections["body_and_bolt_stroke"][
                    "rearward_additional_over_ordinary_mm"
                ],
                "reason": "Straight head-side insertion and reverse withdrawal require temporary open space.",
            },
        ],
        "open_geometry_and_mechanics_risks": [
            "Several provisional rows use approximately 4D rather than the proposal's non-universal 7D search target.",
            "Header bolt centers have a 19.05 mm center-to-edge distance in the 38.1 mm header thickness direction.",
            "Eccentric complete-node mechanics, compression-only contact reversal, splitting, net sections, and group action are unverified.",
            "A purchased bolt product and its delivered shank/thread transition are unselected.",
            "Kicker removal before node-nut removal, operator open space, and panel-off access remain sequence gates despite clear nominal cylindrical tool and bolt-axis sweeps.",
        ],
        "limits": [
            "Nominal finished solids, full provisional bolt stacks, washer seats, fixed protected solids, straight bolt strokes, detached hardware paths, and 50 mm tool approaches were screened at 1e-6 mm3 positive-volume tolerance.",
            "The 6.35 mm base-floor-member gap, 146.05 mm connector-to-floor gap, 126.251 mm installed-envelope-to-floor gap, and 19.0 mm minimum nominal tool clearance are geometry results, not accepted product or fabrication tolerances.",
            "Delivered hardware, actual tool dimensions, wiring bends, tolerance stack, wood resistance, bolt resistance, and complete-frame behavior remain unverified.",
        ],
        "layout_accepted": False,
        "geometry_accepted": False,
        "drilling_released": False,
        "fabrication_released": False,
        "structural_released": False,
        "climbing_released": False,
    }
    report["geometry_fingerprint_sha256"] = _canonical_sha256(
        {"nodes": rows, "rear_projection_summary_mm": projections}
    )
    report["producer"] = _producer_binding(
        "uv run python -m scripts.wood_joint_clearance --write"
    )
    return report


def write_outputs() -> None:
    nodes = build_outer_nodes()
    INTERFACES_OUTPUT.write_text(json.dumps(interface_document(nodes), indent=2) + "\n")
    HARDWARE_OUTPUT.write_text(json.dumps(hardware_document(nodes), indent=2) + "\n")
    CLEARANCE_OUTPUT.write_text(
        json.dumps(build_clearance_report(nodes), indent=2) + "\n"
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--write", action="store_true", help="write checked-in WJ-03 JSON"
    )
    args = parser.parse_args()
    if args.write:
        write_outputs()
    else:
        print(json.dumps(build_clearance_report(), indent=2))


if __name__ == "__main__":
    main()
