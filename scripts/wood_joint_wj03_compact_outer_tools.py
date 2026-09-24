"""Bounded tool and removal screens for the compact WJ-03 outer trial.

Catalog tools remain unselected candidates. All collision shapes are external
envelope proxies; their overlap is not proof of physical impossibility, and
their clearance is not proof of access.
"""

from __future__ import annotations

import hashlib
import math
from collections import defaultdict
from collections.abc import Mapping
from fractions import Fraction
from pathlib import Path
from typing import Any

import cadquery as cq

from mini_moonboard.wood_joint_frame import bolt_axis_stroke_shapes
from mini_moonboard.wood_joint_wj04_config import WJ04_TRIAL
from mini_moonboard.wood_joint_wj05_socket import (
    KOKEN_PRODUCT_URL,
    KOKEN_SOCKET_LENGTH_MM,
    KOKEN_SOCKET_OUTSIDE_DIAMETER_MM,
    KOKEN_SOCKET_STUD_CLEARANCE_DEPTH_MM,
)
from scripts.wood_joint_wj04_tool_access import (
    _seated_tool_center,
    build_catalog_wrench_envelope,
    collision_report,
    full_nut_removal_envelope,
    translation_sweep,
    wrench_reindex_path,
)

ROOT_SCHEMA = "wood_joint_wj03_compact_outer_tool_access/v1"
ROOT = Path(__file__).resolve().parents[1]
TOOL_REPORT_PIN_PATHS = (
    "scripts/wood_joint_wj03_compact_outer_tools.py",
    "scripts/wood_joint_wj03_compact_outer_access.py",
    "scripts/wood_joint_wj04_tool_access.py",
    "mini_moonboard/wood_joint_frame.py",
    "mini_moonboard/wood_joint_wj04_config.py",
    "mini_moonboard/wood_joint_wj05_socket.py",
)
STACK_COUNT = 20
HIT_TOLERANCE_MM3 = 1e-6
GEOMETRY_TOLERANCE_MM = 1e-6
TOOL = WJ04_TRIAL.fasteners.tools[0]
HEAD_BOUNDS = WJ04_TRIAL.fasteners.head
NUT_BOUNDS = WJ04_TRIAL.fasteners.nut
SOCKET_OUTPUT_SIZE_IN = "7/16"
SOCKET_OUTPUT_MM = float(Fraction(SOCKET_OUTPUT_SIZE_IN) * 25.4)


def _vec(value: Any, name: str) -> cq.Vector:
    try:
        vector = cq.Vector(value)
    except (TypeError, ValueError, OverflowError) as error:
        raise ValueError(f"{name} must be a three-component vector") from error
    if not all(math.isfinite(component) for component in vector.toTuple()):
        raise ValueError(f"{name} must be finite")
    if vector.Length <= 1e-9:
        raise ValueError(f"{name} must be nonzero")
    return vector.normalized()


def _shape(value: Any, name: str) -> cq.Shape:
    if isinstance(value, cq.Workplane):
        value = value.val()
    if not isinstance(value, cq.Shape) or not value.isValid() or not value.Solids():
        raise ValueError(f"{name} must be valid solid geometry")
    return value


def _flatten_shapes(value: Any, prefix: str) -> dict[str, cq.Shape]:
    if isinstance(value, cq.Shape):
        return {prefix: _shape(value, prefix)}
    if isinstance(value, cq.Workplane):
        return {prefix: _shape(value, prefix)}
    if isinstance(value, Mapping):
        result: dict[str, cq.Shape] = {}
        for key, item in value.items():
            result.update(_flatten_shapes(item, f"{prefix}/{key}"))
        return result
    if isinstance(value, (tuple, list)):
        result = {}
        for index, item in enumerate(value):
            result.update(_flatten_shapes(item, f"{prefix}/{index}"))
        return result
    if value is None:
        return {}
    raise TypeError(f"{prefix} contains unsupported {type(value).__name__}")


def _json_safe(value: Any) -> Any:
    if hasattr(value, "__dataclass_fields__"):
        return {
            name: _json_safe(getattr(value, name))
            for name in value.__dataclass_fields__
        }
    if isinstance(value, Mapping):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, (tuple, list)):
        return [_json_safe(item) for item in value]
    if isinstance(value, cq.Vector):
        return [round(component, 9) for component in value.toTuple()]
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    return str(value)


def _tool_source_pins() -> dict[str, str]:
    return {
        name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest()
        for name in TOOL_REPORT_PIN_PATHS
    }


def _installed_key(installed: Mapping[str, cq.Shape], stack_id: str, role: str) -> str:
    suffix = f"/{stack_id}/{role}"
    matches = [key for key in installed if key.endswith(suffix)]
    if len(matches) != 1:
        raise ValueError(f"expected one installed {role} envelope for {stack_id}")
    return matches[0]


def _projection_bounds(shape: cq.Shape, axis: cq.Vector) -> tuple[float, float]:
    bounds = shape.BoundingBox()
    corners = [
        cq.Vector(x, y, z)
        for x in (bounds.xmin, bounds.xmax)
        for y in (bounds.ymin, bounds.ymax)
        for z in (bounds.zmin, bounds.zmax)
    ]
    projections = [corner.dot(axis) for corner in corners]
    return min(projections), max(projections)


def _face_datum(
    seat_center: Any,
    outward: cq.Vector,
    target: cq.Shape,
    candidate: cq.Shape,
) -> dict[str, Any]:
    target_inner, target_outer = _projection_bounds(target, outward)
    candidate_inner, candidate_outer = _projection_bounds(candidate, outward)
    target_midplane = (target_inner + target_outer) / 2
    overlap = max(
        0.0, min(target_outer, candidate_outer) - max(target_inner, candidate_inner)
    )
    return {
        "datum": "target fastener axial midplane; wrench slab lies within modeled fastener height",
        "outward_axis_xyz": [round(value, 9) for value in outward.toTuple()],
        "target_inboard_face_projection_mm": round(target_inner, 9),
        "target_outer_face_projection_mm": round(target_outer, 9),
        "target_midplane_projection_mm": round(target_midplane, 9),
        "wrench_axial_min_projection_mm": round(candidate_inner, 9),
        "wrench_axial_max_projection_mm": round(candidate_outer, 9),
        "wrench_axial_overlap_mm": round(overlap, 9),
        "nominal_tool_slab_thickness_mm": round(candidate_outer - candidate_inner, 9),
        "axial_overlap_is_proxy_geometry_only": True,
        "wrench_is_contained_within_modeled_fastener_height": (
            candidate_inner >= target_inner - GEOMETRY_TOLERANCE_MM
            and candidate_outer <= target_outer + GEOMETRY_TOLERANCE_MM
        ),
        "actual_jaw_contact_or_hex_engagement_verified": False,
        "published_wrench_dimension_tolerance_available": TOOL.published_dimension_tolerances,
        "seat_center_xyz_mm": [
            round(value, 9) for value in cq.Vector(seat_center).toTuple()
        ],
    }


def _face_reference(axis: cq.Vector) -> cq.Vector:
    cardinal = min(
        (cq.Vector(1, 0, 0), cq.Vector(0, 1, 0), cq.Vector(0, 0, 1)),
        key=lambda candidate: abs(candidate.dot(axis)),
    )
    return (cardinal - axis * cardinal.dot(axis)).normalized()


def _wrench_motion_poses(
    seated: cq.Shape,
    center: Any,
    outward: cq.Vector,
    reference: cq.Vector,
    heading: float,
    stroke_degrees: float,
    reindex_degrees: float,
    lift_mm: float,
) -> dict[str, cq.Shape]:
    """Return actual endpoint poses matching the existing conservative sweeps."""
    center = cq.Vector(center)
    after_stroke = seated.rotate(
        center.toTuple(), (center + outward).toTuple(), stroke_degrees
    )
    after_stroke_handle = _handle_axis(outward, reference, heading + stroke_degrees)
    lifted = after_stroke.translate(after_stroke_handle * lift_mm)
    reindexed = lifted.rotate(
        center.toTuple(), (center + outward).toTuple(), reindex_degrees
    )
    reindexed_handle = _handle_axis(
        outward, reference, heading + stroke_degrees + reindex_degrees
    )
    reseated = reindexed.translate(-reindexed_handle * lift_mm)
    return {
        "seated_start_pose": seated,
        "stroke_terminal_pose": after_stroke,
        "open_end_exit_terminal_pose": lifted,
        "detached_reindex_terminal_pose": reindexed,
        "reseat_terminal_pose": reseated,
    }


def _handle_axis(outward: cq.Vector, reference: cq.Vector, heading: float) -> cq.Vector:
    side = outward.cross(reference).normalized()
    angle = math.radians(heading)
    return (reference * math.cos(angle) + side * math.sin(angle)).normalized()


def _socket_envelopes(
    axis_point: Any,
    outward: cq.Vector,
    target: cq.Shape,
    travel_mm: float = 0.0,
) -> dict[str, Any]:
    """Build signed, face-seated socket outside proxies for a cardinal axis."""
    point = cq.Vector(axis_point)
    inner, outer = _projection_bounds(target, outward)
    engagement_face = point + outward * (inner - point.dot(outward))
    outer_face = point + outward * (outer - point.dot(outward))
    radius = KOKEN_SOCKET_OUTSIDE_DIAMETER_MM / 2

    def cylinder(start: cq.Vector, length: float) -> cq.Solid:
        return cq.Solid.makeCylinder(radius, length, start, outward)

    target_height = (
        _projection_bounds(target, outward)[1] - _projection_bounds(target, outward)[0]
    )
    seated = cylinder(engagement_face, KOKEN_SOCKET_LENGTH_MM)
    approach_start = outer_face
    approach_start_shape = cylinder(approach_start, KOKEN_SOCKET_LENGTH_MM)
    approach_sweep = cylinder(engagement_face, KOKEN_SOCKET_LENGTH_MM + target_height)
    removal_terminal = engagement_face + outward * max(0.0, travel_mm)
    removal_sweep = cylinder(
        engagement_face, KOKEN_SOCKET_LENGTH_MM + max(0.0, travel_mm)
    )
    return {
        "seated_external_envelope": seated,
        "approach_start_envelope": approach_start_shape,
        "approach_start_point": approach_start,
        "approach_terminal_point": outer_face,
        "approach_sweep_envelope": approach_sweep,
        "removal_terminal_envelope": cylinder(removal_terminal, KOKEN_SOCKET_LENGTH_MM),
        "removal_sweep_envelope": removal_sweep,
        "seat_datum": {
            "datum": "target bearing/inboard face; positive axis spans the target toward the socket drive end",
            "outward_axis_xyz": [round(value, 9) for value in outward.toTuple()],
            "target_bearing_face_projection_mm": round(inner, 9),
            "target_outer_face_projection_mm": round(outer, 9),
            "socket_seating_face_projection_mm": round(engagement_face.dot(outward), 9),
            "seat_plane_error_mm": round(engagement_face.dot(outward) - inner, 9),
            "approach_start_axis_projection_mm": round(approach_start.dot(outward), 9),
            "seated_terminal_axis_projection_mm": round(
                engagement_face.dot(outward), 9
            ),
            "removal_terminal_axis_projection_mm": round(
                removal_terminal.dot(outward), 9
            ),
            "approach_distance_mm": round(target_height, 9),
            "axial_removal_travel_mm": round(max(0.0, travel_mm), 9),
        },
    }


def _catalog_tool_record() -> dict[str, Any]:
    nominal_af = float(Fraction(TOOL.wrench_size_in) * 25.4)
    return {
        "compatibility_reference_bounds": {
            "head": _json_safe(HEAD_BOUNDS),
            "nut": _json_safe(NUT_BOUNDS),
            "washer": _json_safe(WJ04_TRIAL.fasteners.washer),
            "bolt_body_reference": _json_safe(WJ04_TRIAL.fasteners.bolts[0]),
            "selection_status": "source bounds used for nominal compatibility screens only; no WJ-03 outer fastener is selected",
        },
        "facom_open_end_wrench": {
            "candidate_id": TOOL.candidate_id,
            "manufacturer": TOOL.manufacturer,
            "description": TOOL.description,
            "nominal_opening_in": TOOL.wrench_size_in,
            "nominal_opening_mm": round(nominal_af, 6),
            "head_width_mm": TOOL.head_width_mm,
            "head_thickness_mm": TOOL.head_thickness_mm,
            "overall_length_mm": TOOL.overall_length_mm,
            "synthetic_heading_samples_degrees": list(TOOL.head_offsets_degrees),
            "source_urls": list(TOOL.source_urls),
            "selected": False,
            "actual_tool_geometry_present": False,
            "catalog_product_candidate": True,
            "modeled_shape": "conservative external envelope: circular heads plus full-width rectangular handle",
            "fit_torque_and_handle_sweep_verified": False,
        },
        "koken_socket": {
            "candidate_id": "koken_3305a_7_16",
            "product": "Ko-ken 3305A-7/16",
            "output_size_in": SOCKET_OUTPUT_SIZE_IN,
            "output_size_mm": round(SOCKET_OUTPUT_MM, 6),
            "outside_diameter_mm": KOKEN_SOCKET_OUTSIDE_DIAMETER_MM,
            "overall_length_mm": KOKEN_SOCKET_LENGTH_MM,
            "stud_clearance_depth_mm": KOKEN_SOCKET_STUD_CLEARANCE_DEPTH_MM,
            "source_urls": [KOKEN_PRODUCT_URL],
            "selected": False,
            "actual_tool_geometry_present": False,
            "catalog_product_candidate": True,
            "modeled_shape": "maximum listed outside diameter as a cylinder over full length",
            "drive_size": "3/8-in square",
            "ratchet_extension_and_hand_envelopes": "not modeled",
            "internal_profile_and_fit_verified": False,
        },
    }


def _stack_compatibility(stack: Any) -> dict[str, Any]:
    hardware = stack.hardware
    nominal_af = float(Fraction(TOOL.wrench_size_in) * 25.4)
    af_compatible = (
        HEAD_BOUNDS.across_flats_range_mm[0]
        <= nominal_af
        <= HEAD_BOUNDS.across_flats_range_mm[1]
        and NUT_BOUNDS.across_flats_range_mm[0]
        <= nominal_af
        <= NUT_BOUNDS.across_flats_range_mm[1]
        and SOCKET_OUTPUT_MM == nominal_af
    )
    model_compatible = (
        "1/4-20" in hardware.candidate_sku
        and abs(hardware.steel_diameter_mm - 6.35) <= GEOMETRY_TOLERANCE_MM
        and hardware.head_diameter_mm
        <= HEAD_BOUNDS.across_corners_range_mm[1] + GEOMETRY_TOLERANCE_MM
        and hardware.nut_diameter_mm
        <= NUT_BOUNDS.across_corners_max_mm + GEOMETRY_TOLERANCE_MM
        and hardware.head_height_mm >= TOOL.head_thickness_mm
        and hardware.nut_height_mm >= TOOL.head_thickness_mm
    )
    tip = (
        cq.Vector(stack.under_head_origin)
        + cq.Vector(stack.direction) * hardware.under_head_length_mm
    )
    nut_outer_face = cq.Vector(stack.nut_seat.center) + cq.Vector(
        stack.direction
    ).normalized() * (hardware.washer_thickness_mm + hardware.nut_height_mm)
    nut_stud_projection = max(
        0.0, (tip - nut_outer_face).dot(cq.Vector(stack.direction).normalized())
    )
    socket_depth_clear = (
        nut_stud_projection
        <= KOKEN_SOCKET_STUD_CLEARANCE_DEPTH_MM + GEOMETRY_TOLERANCE_MM
    )
    return {
        "catalog_nominal_size_matches_1_4_hex_bounds": bool(af_compatible),
        "wrench_nominal_af_mm": round(nominal_af, 6),
        "head_across_flats_bounds_mm": list(HEAD_BOUNDS.across_flats_range_mm),
        "nut_across_flats_bounds_mm": list(NUT_BOUNDS.across_flats_range_mm),
        "modeled_head_across_corners_max_mm": hardware.head_diameter_mm,
        "modeled_nut_across_corners_max_mm": hardware.nut_diameter_mm,
        "hardware_description": hardware.candidate_sku,
        "nominal_envelope_compatible": bool(af_compatible and model_compatible),
        "actual_hex_faces_present_in_geometry": False,
        "actual_tool_fit_verified": False,
        "nut_tip_projection_past_outer_face_mm": round(nut_stud_projection, 6),
        "socket_stud_clearance_depth_mm": KOKEN_SOCKET_STUD_CLEARANCE_DEPTH_MM,
        "socket_stud_clearance_envelope_compatible": bool(socket_depth_clear),
        "interpretation": "Nominal size and cylindrical stack envelope match catalog bounds; no selected hardware hex geometry or tool fit is established.",
    }


def _obstacle_class(name: str, panel_ids: set[str]) -> str:
    if name.startswith("tool_pair/"):
        return "tool_pair"
    if name.startswith("staged_panels/"):
        return "staged_panel"
    if name.startswith("protected/"):
        return "protected_geometry"
    if name.startswith(("installed_hardware/", "wj05_bolts/", "wj05_stacks/")):
        return "other_stack"
    suffix = name.removeprefix("finished_wood/")
    if name.startswith("finished_wood/") and (suffix in panel_ids or "panel" in suffix):
        return "installed_panel"
    return "finished_body"


def _floor_bounds(shape: cq.Shape, floor_z_mm: float) -> dict[str, Any]:
    minimum = shape.BoundingBox().zmin
    clearance = minimum - floor_z_mm
    return {
        "minimum_z_mm": round(minimum, 6),
        "floor_z_mm": round(floor_z_mm, 6),
        "clearance_mm": round(clearance, 6),
        "below_analytical_floor": clearance < -GEOMETRY_TOLERANCE_MM,
        "penetration_depth_mm": round(max(0.0, -clearance), 6),
    }


def _geometry_maps(
    geometry: Any,
) -> tuple[dict[str, cq.Shape], dict[str, str], set[str]]:
    panel_ids = set(geometry.panels)
    staged_panel_ids = {
        panel_id
        for panel_id in panel_ids
        if any(
            name.startswith(f"staged/{panel_id}/") for name in geometry.staged_panels
        )
    }
    finished_source = {
        name: shape
        for name, shape in geometry.finished_wood.items()
        if name not in staged_panel_ids
    }
    finished = _flatten_shapes(finished_source, "finished_wood")
    protected_inventory = geometry.protected
    if not isinstance(protected_inventory, Mapping) or not isinstance(
        protected_inventory.get("solids"), Mapping
    ):
        raise TypeError("geometry.protected must expose its solid map")
    solids = protected_inventory["solids"]
    retained_protected: dict[str, Any] = {}
    for family in (
        "tnuts",
        "lights",
        "wires",
        "panel_screws",
        "frame_bolts",
        "frame_bolt_components",
        "retained_legacy_sds",
        "retained_legacy_connectors",
    ):
        rows = solids.get(family, {})
        if not isinstance(rows, Mapping):
            raise TypeError(f"protected solid family {family} must be a map")
        if family == "tnuts":
            rows = {
                name: shape
                for name, shape in rows.items()
                if geometry.tnut_owners.get(name) not in staged_panel_ids
            }
        elif family == "panel_screws":
            rows = {
                name: shape
                for name, shape in rows.items()
                if "panel_lower" not in name and "kicker" not in name
            }
        retained_protected[family] = rows
    protected = _flatten_shapes(retained_protected, "protected")
    staged = _flatten_shapes(geometry.staged_panels, "staged_panels")
    wj03_hardware = _flatten_shapes(geometry.installed_hardware, "installed_hardware")
    wj05_bolts = _flatten_shapes(geometry.wj05_bolts, "wj05_bolts")
    wj05_stacks = _flatten_shapes(geometry.wj05_stacks, "wj05_stacks")
    maps = {
        "finished_wood": finished,
        "protected": protected,
        "staged_panels": staged,
        "installed_hardware": wj03_hardware,
        "wj05_bolts": wj05_bolts,
        "wj05_stacks": wj05_stacks,
    }
    obstacles = {
        name: shape for mapping in maps.values() for name, shape in mapping.items()
    }
    classes = {name: _obstacle_class(name, panel_ids) for name in obstacles}
    return obstacles, classes, panel_ids


def build_tool_report(geometry: Any) -> dict[str, Any]:
    """Screen all twenty compact outer bolt stacks against supplied geometry.

    This function consumes a source-bound geometry materialization. It never
    creates or edits candidate wood. Each collision uses only sequentially
    justified same-stack exclusions; all unrelated stacks, protected geometry,
    finished wood and panel stages remain obstacles.
    """
    stacks = getattr(geometry, "stacks", None)
    if not isinstance(stacks, Mapping) or len(stacks) != STACK_COUNT:
        raise ValueError(f"geometry must provide exactly {STACK_COUNT} outer stacks")
    if any(stack_id != stack.id for stack_id, stack in stacks.items()):
        raise ValueError("stack mapping keys must equal each BoltStack.id")
    floor_z = float(geometry.floor_z_mm)
    if not math.isfinite(floor_z):
        raise ValueError("floor_z_mm must be finite")
    installed = _flatten_shapes(geometry.installed_hardware, "installed_hardware")
    obstacles, obstacle_classes, panel_ids = _geometry_maps(geometry)
    for stack_id in stacks:
        for role in ("shaft", "head", "head_washer", "nut_washer", "nut"):
            _installed_key(installed, stack_id, role)

    aggregate: dict[str, dict[str, list[dict[str, Any]]]] = defaultdict(
        lambda: defaultdict(list)
    )
    floor_hits: list[dict[str, Any]] = []

    def screen(
        stack_id: str,
        candidate_id: str,
        operation: str,
        shapes: Mapping[str, cq.Shape],
        obstacle_shapes: Mapping[str, cq.Shape],
        exclusion_scope: str,
        excluded: tuple[str, ...] = (),
    ) -> dict[str, Any]:
        result = collision_report(
            shapes,
            obstacle_shapes,
            excluded_target_ids=excluded,
            exclusion_scope=exclusion_scope,
        )
        for shape_name, hit_rows in result["external_envelope_hits_mm3"].items():
            for obstacle_name, volume in hit_rows.items():
                category = obstacle_classes.get(
                    obstacle_name, _obstacle_class(obstacle_name, panel_ids)
                )
                aggregate[category][obstacle_name].append(
                    {
                        "stack_id": stack_id,
                        "tool_candidate": candidate_id,
                        "operation": operation,
                        "candidate_shape": shape_name,
                        "intersection_mm3": volume,
                    }
                )
        floor_rows = {
            name: _floor_bounds(shape, floor_z) for name, shape in shapes.items()
        }
        for shape_name, floor_result in floor_rows.items():
            if floor_result["below_analytical_floor"]:
                floor_hits.append(
                    {
                        "stack_id": stack_id,
                        "tool_candidate": candidate_id,
                        "operation": operation,
                        "candidate_shape": shape_name,
                        **floor_result,
                    }
                )
        return {**result, "floor_screen": floor_rows}

    stack_reports: dict[str, Any] = {}
    for stack_id, stack in stacks.items():
        hardware = stack.hardware
        direction = _vec(stack.direction, f"{stack_id}.direction")
        if max(abs(value) for value in direction.toTuple()) < 1.0 - 1e-8:
            raise ValueError(
                f"{stack_id} requires a cardinal bolt axis for exact face seating"
            )
        head_outward = -direction
        nut_outward = direction
        target_keys = {
            role: _installed_key(installed, stack_id, role)
            for role in ("shaft", "head", "head_washer", "nut", "nut_washer")
        }
        target_shapes = {role: installed[key] for role, key in target_keys.items()}
        compatibility = _stack_compatibility(stack)
        head_center = _seated_tool_center(
            stack.head_seat.center,
            head_outward,
            target_shapes["head"],
            TOOL.head_thickness_mm,
        )
        nut_center = _seated_tool_center(
            stack.nut_seat.center,
            nut_outward,
            target_shapes["nut"],
            TOOL.head_thickness_mm,
        )
        reference = _face_reference(nut_outward)
        heading_cases = []

        if compatibility["nominal_envelope_compatible"]:
            for heading in TOOL.head_offsets_degrees:
                head_wrench = build_catalog_wrench_envelope(
                    head_center,
                    head_outward.toTuple(),
                    reference,
                    TOOL,
                    offset_degrees=heading,
                )
                nut_wrench = build_catalog_wrench_envelope(
                    nut_center,
                    nut_outward.toTuple(),
                    reference,
                    TOOL,
                    offset_degrees=heading,
                )
                motion = wrench_reindex_path(
                    nut_wrench,
                    nut_center,
                    nut_outward.toTuple(),
                    _handle_axis(nut_outward, reference, heading),
                    head_width_mm=TOOL.head_width_mm,
                )
                head_seat_datum = _face_datum(
                    stack.head_seat.center,
                    head_outward,
                    target_shapes["head"],
                    head_wrench,
                )
                nut_seat_datum = _face_datum(
                    stack.nut_seat.center,
                    nut_outward,
                    target_shapes["nut"],
                    nut_wrench,
                )
                head_report = screen(
                    stack_id,
                    TOOL.candidate_id,
                    "head_counterhold_seat",
                    {"seated_start_pose": head_wrench},
                    obstacles,
                    excluded=(target_keys["head"], target_keys["shaft"]),
                    exclusion_scope=(
                        "Only the engaged head and its own shaft are excluded for intended contact; both washers, nut, wood, other stacks, protected volumes and staged panels remain obstacles."
                    ),
                )
                poses = _wrench_motion_poses(
                    nut_wrench,
                    nut_center,
                    nut_outward,
                    reference,
                    heading,
                    motion["stroke_degrees"],
                    motion["reindex_degrees"],
                    motion["open_end_exit_distance_mm"],
                )
                motion_steps = {
                    "nut_stroke": {
                        "start_pose": poses["seated_start_pose"],
                        "terminal_pose": poses["stroke_terminal_pose"],
                        "swept_envelope": motion["stroke_sweep"],
                    },
                    "open_end_exit": {
                        "start_pose": poses["stroke_terminal_pose"],
                        "terminal_pose": poses["open_end_exit_terminal_pose"],
                        "swept_envelope": motion["lateral_unseat_sweep"],
                    },
                    "detached_reindex": {
                        "start_pose": poses["open_end_exit_terminal_pose"],
                        "terminal_pose": poses["detached_reindex_terminal_pose"],
                        "swept_envelope": motion["detached_reindex_sweep"],
                    },
                    "reseat": {
                        "start_pose": poses["detached_reindex_terminal_pose"],
                        "terminal_pose": poses["reseat_terminal_pose"],
                        "swept_envelope": motion["lateral_reseat_sweep"],
                    },
                }
                nut_reports = {}
                paired_motion_reports = {}
                for step_name, poses_and_sweep in motion_steps.items():
                    nut_reports[step_name] = screen(
                        stack_id,
                        TOOL.candidate_id,
                        f"nut_{step_name}",
                        poses_and_sweep,
                        obstacles,
                        excluded=(target_keys["nut"], target_keys["shaft"]),
                        exclusion_scope=(
                            "Only the engaged nut and its own shaft are excluded for intended open-end contact; washers, opposite head, wood, other stacks, protected volumes and staged panels remain obstacles."
                        ),
                    )
                    paired_motion_reports[step_name] = screen(
                        stack_id,
                        TOOL.candidate_id,
                        f"nut_{step_name}_against_head_counterhold",
                        {"moving_nut_tool_sweep": poses_and_sweep["swept_envelope"]},
                        {"tool_pair/head_counterhold": head_wrench},
                        exclusion_scope="No tool is excluded. The fixed head counterhold and moving nut-tool envelope are compared as broad proxies; overlap does not establish real tool interference.",
                    )
                pair_report = screen(
                    stack_id,
                    TOOL.candidate_id,
                    "nut_tool_vs_head_counterhold_tool",
                    {"nut_tool": nut_wrench},
                    {"tool_pair/head_counterhold": head_wrench},
                    exclusion_scope="Neither candidate tool is excluded; reported overlap is a broad-envelope interaction, not proof of physical collision.",
                )
                heading_cases.append(
                    {
                        "synthetic_heading_proxy_degrees": heading,
                        "requires_two_wrench_units_for_counterhold": True,
                        "head_counterhold": head_report,
                        "head_seat_datum": head_seat_datum,
                        "nut_seat_datum": nut_seat_datum,
                        "nut_stroke_reindex_reseat": nut_reports,
                        "counterhold_vs_nut_motion": paired_motion_reports,
                        "tool_pair_screen": pair_report,
                        "motion": {
                            "stroke_degrees": motion["stroke_degrees"],
                            "reindex_degrees": motion["reindex_degrees"],
                            "open_end_exit_distance_mm": motion[
                                "open_end_exit_distance_mm"
                            ],
                            "open_end_exit_motion_is_unverified_proxy": True,
                            "heading_is_catalog_jaw_orientation": False,
                        },
                    }
                )

        direction_vec = cq.Vector(direction)
        tip = (
            cq.Vector(stack.under_head_origin)
            + direction_vec * hardware.under_head_length_mm
        )
        nut_start = (
            cq.Vector(stack.nut_seat.center)
            + direction_vec * hardware.washer_thickness_mm
        )
        nut_travel = max(0.0, (tip - nut_start).dot(direction_vec) + 0.01)
        nut_washer_start = cq.Vector(stack.nut_seat.center)
        nut_washer_travel = max(0.0, (tip - nut_washer_start).dot(direction_vec))
        nut_terminal = target_shapes["nut"].translate(nut_outward * nut_travel)
        nut_sweep = translation_sweep(target_shapes["nut"], nut_outward * nut_travel)
        nut_motion_report = screen(
            stack_id,
            "moving_hardware",
            "nut_translation_after_unthreading",
            {
                "seated_start_pose": target_shapes["nut"],
                "terminal_pose_past_bolt_tip": nut_terminal,
                "axial_translation_sweep": nut_sweep,
            },
            obstacles,
            excluded=(target_keys["nut"], target_keys["shaft"]),
            exclusion_scope=(
                "The moving target nut and its own shaft are excluded after unthreading. Washers and all other geometry remain obstacles; delivered-thread behavior is unverified."
            ),
        )
        nut_motion_report["translation"] = {
            "axis_xyz": [round(value, 9) for value in nut_outward.toTuple()],
            "travel_mm": round(nut_travel, 9),
            "sequence_condition": "after nut is fully unthreaded",
        }
        facom_removal = None
        facom_removal_counterhold = None
        if compatibility["nominal_envelope_compatible"]:
            wrench_removal = full_nut_removal_envelope(
                nut_center, nut_outward.toTuple(), TOOL, nut_travel
            )
            terminal_wrench = nut_wrench.translate(nut_outward * nut_travel)
            facom_removal = screen(
                stack_id,
                TOOL.candidate_id,
                "full_turn_axial_nut_removal_tool_proxy",
                {
                    "seated_start_pose": nut_wrench,
                    "terminal_pose_past_bolt_tip": terminal_wrench,
                    "full_turn_axial_sweep": wrench_removal,
                },
                obstacles,
                excluded=(target_keys["nut"], target_keys["shaft"]),
                exclusion_scope="Only target nut and its own shaft are excluded for intended unthreading. Both washers and all other geometry remain obstacles.",
            )
            facom_removal_counterhold = screen(
                stack_id,
                TOOL.candidate_id,
                "full_turn_axial_nut_removal_against_head_counterhold",
                {"full_turn_axial_nut_tool_envelope": wrench_removal},
                {"tool_pair/head_counterhold": head_wrench},
                exclusion_scope="No tool is excluded. The full-turn nut-tool envelope and seated head counterhold are broad proxy shapes; overlap does not establish real tool interference.",
            )
        nut_washer_terminal = target_shapes["nut_washer"].translate(
            nut_outward * nut_washer_travel
        )
        nut_washer_sweep = translation_sweep(
            target_shapes["nut_washer"], nut_outward * nut_washer_travel
        )
        nut_washer_report = screen(
            stack_id,
            "moving_hardware",
            "nut_washer_slide_after_nut_removal",
            {
                "seated_start_pose": target_shapes["nut_washer"],
                "terminal_pose_at_bolt_tip": nut_washer_terminal,
                "axial_translation_sweep": nut_washer_sweep,
            },
            obstacles,
            excluded=(
                target_keys["nut_washer"],
                target_keys["nut"],
                target_keys["shaft"],
            ),
            exclusion_scope=(
                "The moving washer, already removed same-stack nut, and same-stack shaft are excluded for this axial slide. Source-bound minimum washer ID and maximum shaft diameter allow the modeled axial pass; thread peaks, delivered parts and received clearance remain unverified. Other stack parts and all wood remain obstacles."
            ),
        )
        nut_washer_id_min = WJ04_TRIAL.fasteners.washer.inner_diameter_range_mm[0]
        shaft_diameter_max = WJ04_TRIAL.fasteners.bolts[0].body_diameter_range_mm[1]
        if nut_washer_id_min <= shaft_diameter_max:
            raise ValueError(
                "source washer ID bound does not clear source shaft diameter"
            )
        nut_washer_report["axial_sliding_clearance"] = {
            "washer_min_inner_diameter_mm": nut_washer_id_min,
            "shaft_max_diameter_mm": shaft_diameter_max,
            "minimum_radial_clearance_mm": round(
                (nut_washer_id_min - shaft_diameter_max) / 2, 6
            ),
            "source_bounds_allow_modeled_axial_slide": True,
            "thread_major_diameter_and_received_clearance_verified": False,
            "delivered_parts_and_assembly_clearance_verified": False,
        }
        nut_washer_report["translation"] = {
            "axis_xyz": [round(value, 9) for value in nut_outward.toTuple()],
            "travel_mm": round(nut_washer_travel, 9),
            "sequence_condition": "after nut removal; slide washer to bolt tip",
        }
        bolt_strokes = bolt_axis_stroke_shapes(stack)
        withdrawal_vector = -direction_vec * hardware.under_head_length_mm
        bolt_start = {
            "shaft_start_pose": target_shapes["shaft"],
            "head_start_pose": target_shapes["head"],
        }
        bolt_terminal = {
            "shaft_terminal_pose": target_shapes["shaft"].translate(withdrawal_vector),
            "head_terminal_pose": target_shapes["head"].translate(withdrawal_vector),
        }
        bolt_report = screen(
            stack_id,
            "moving_hardware",
            "bolt_axis_withdrawal_after_nut_and_nut_washer_removal",
            {**bolt_start, **bolt_terminal, **bolt_strokes},
            obstacles,
            excluded=tuple(target_keys.values()),
            exclusion_scope=(
                "All same-stack installed hardware is already removed. Finished wood and its bores, all other stacks, protected geometry and staged panels remain obstacles. Thread-end condition is not verified."
            ),
        )
        bolt_report["translation"] = {
            "axis_xyz": [round(value, 9) for value in (-direction_vec).toTuple()],
            "travel_mm": hardware.under_head_length_mm,
            "sequence_condition": "after nut and nut washer removal",
            "nominal_full_form_thread_end_verified": False,
        }
        head_washer_travel = hardware.washer_thickness_mm + 0.01
        head_washer_outward = head_outward
        head_washer_terminal = target_shapes["head_washer"].translate(
            head_washer_outward * head_washer_travel
        )
        head_washer_sweep = translation_sweep(
            target_shapes["head_washer"], head_washer_outward * head_washer_travel
        )
        head_washer_report = screen(
            stack_id,
            "moving_hardware",
            "head_washer_release_after_bolt_withdrawal",
            {
                "seated_start_pose": target_shapes["head_washer"],
                "terminal_pose_clear_of_seat": head_washer_terminal,
                "axial_translation_sweep": head_washer_sweep,
            },
            obstacles,
            excluded=tuple(target_keys.values()),
            exclusion_scope="The moving washer and all same-stack hardware are already removed or moving in sequence; all wood, other stacks, protected volumes and staged panels remain obstacles. Manual pickup clearance is not modeled.",
        )
        head_washer_report["translation"] = {
            "axis_xyz": [round(value, 9) for value in head_washer_outward.toTuple()],
            "travel_mm": round(head_washer_travel, 9),
            "sequence_condition": "after bolt withdrawal",
        }

        socket_stacks = {}
        if compatibility["nominal_envelope_compatible"]:
            for role, outward, seat, target in (
                (
                    "head",
                    head_outward,
                    stack.head_seat.center,
                    target_shapes["head"],
                ),
                (
                    "nut",
                    nut_outward,
                    stack.nut_seat.center,
                    target_shapes["nut"],
                ),
            ):
                if (
                    role == "nut"
                    and not compatibility["socket_stud_clearance_envelope_compatible"]
                ):
                    socket_stacks[role] = {
                        "status": "not_screened_catalog_stud_clearance_depth_below_modeled_tip_projection",
                        "tip_projection_mm": compatibility[
                            "nut_tip_projection_past_outer_face_mm"
                        ],
                        "stud_clearance_depth_mm": KOKEN_SOCKET_STUD_CLEARANCE_DEPTH_MM,
                    }
                    continue
                socket_shapes = _socket_envelopes(
                    seat,
                    outward,
                    target,
                    nut_travel if role == "nut" else 0.0,
                )
                socket_excluded = (
                    target_keys[role],
                    target_keys["shaft"],
                )
                socket_rows = {
                    "coaxial_socket_approach": screen(
                        stack_id,
                        "koken_3305a_7_16",
                        "coaxial_socket_approach",
                        {
                            "approach_start_pose": socket_shapes[
                                "approach_start_envelope"
                            ],
                            "seated_terminal_pose": socket_shapes[
                                "seated_external_envelope"
                            ],
                            "approach_sweep": socket_shapes["approach_sweep_envelope"],
                        },
                        obstacles,
                        excluded=socket_excluded,
                        exclusion_scope="Only engaged target hex and its own shaft are excluded for intended socket occupancy; washers, other stacks and all surrounding geometry remain obstacles. The proxy models outside occupancy, not the internal profile.",
                    )
                }
                if role == "nut":
                    socket_rows["socket_and_nut_axial_removal"] = screen(
                        stack_id,
                        "koken_3305a_7_16",
                        "socket_and_nut_axial_removal",
                        {
                            "seated_start_pose": socket_shapes[
                                "seated_external_envelope"
                            ],
                            "terminal_pose_past_bolt_tip": socket_shapes[
                                "removal_terminal_envelope"
                            ],
                            "axial_removal_sweep": socket_shapes[
                                "removal_sweep_envelope"
                            ],
                        },
                        obstacles,
                        excluded=socket_excluded,
                        exclusion_scope="Only target nut and own shaft are excluded during the coaxial external-envelope motion; washers and all other geometry remain obstacles. This starts after unthreading; ratchet, extension, internal profile, turning motion and hand are absent.",
                    )
                socket_stacks[role] = {
                    "status": "catalog_outside_envelope_only",
                    "seat_datum": socket_shapes["seat_datum"],
                    "operations": socket_rows,
                    "nut_turn_and_reindex": "not screened; no ratchet, extension or handle candidate is selected or modeled",
                }

        stack_reports[stack_id] = {
            "hardware": {
                "candidate_sku": hardware.candidate_sku,
                "under_head_length_mm": hardware.under_head_length_mm,
                "grip_mm": stack.grip_mm,
                "direction_xyz": [round(value, 9) for value in direction.toTuple()],
                "thread_runout_verified": False,
                "delivered_hardware_selected": False,
            },
            "tool_dimension_compatibility": compatibility,
            "facom_open_end_tool": {
                "status": "candidate_envelope_screened"
                if compatibility["nominal_envelope_compatible"]
                else "not_screened_stack_dimensions_not_nominally_compatible",
                "heading_cases": heading_cases,
                "full_nut_removal_tool_envelope": facom_removal,
                "full_nut_removal_against_head_counterhold": facom_removal_counterhold,
                "nut_detachment": nut_motion_report,
                "nut_washer_detachment": nut_washer_report,
                "head_washer_release_after_bolt_withdrawal": head_washer_report,
                "bolt_withdrawal": bolt_report,
                "nut_thread_engagement_and_full_form_thread_end_verified": False,
                "manual_part_retrieval_verified": False,
            },
            "koken_socket_candidate": socket_stacks,
            "assembly_sequence": [
                "counterhold bolt head while nut is turned and reindexed",
                "unthread and remove nut, then slide nut washer to bolt tip",
                "withdraw bolt axially after nut and nut washer removal",
                "release head washer after bolt withdrawal",
            ],
        }

    return {
        "schema": ROOT_SCHEMA,
        "trial_id": geometry.trial_id,
        "floor_datum": geometry.floor_datum,
        "source_binding": _json_safe(geometry.source_binding),
        "source_pins": {
            "geometry_materializer_inputs": _json_safe(geometry.source_pins),
            "tool_report_producer_and_direct_dependencies": _tool_source_pins(),
            "coverage": "partial; direct report/helper and geometry materializer inputs are hashed, but this is not a recursive dependency closure",
        },
        "tool_candidates": _catalog_tool_record(),
        "stack_count": len(stack_reports),
        "stacks": stack_reports,
        "unmodeled_preconditions": [
            "Removable holds and their projecting hold bolts have been removed; their removal and staged handling are not modeled.",
            "No installation torque, hand clearance, thread engagement, delivered tool fit, or received part dimensions are verified.",
            "Only four lower/kicker panels are staged; retained panel screws and fixed assemblies follow the source inventory.",
        ],
        "overlap_summary_by_class": {
            category: {
                obstacle: rows for obstacle, rows in sorted(obstacles_for_class.items())
            }
            for category, obstacles_for_class in sorted(aggregate.items())
        },
        "analytical_floor": {
            "z_mm": floor_z,
            "datum": geometry.floor_datum,
            "below_floor_envelopes": floor_hits,
            "interpretation": "Analytical plane comparison only; no physical floor shape, level, or friction is modeled.",
        },
        "interpretation": (
            "FACOM and Ko-ken entries are dimensioned catalog candidates, not selected or received tools. The Ko-ken dimensions screen its external envelope only; no ratchet or extension is selected. CAD screens include seated, terminal and swept proxy poses where provided. Overlap is not proof of physical blockage; clearance is not proof of tool fit, torque, access, installation sequence, full-form threads or part retrieval."
        ),
        "release_claims": {
            "tool_selected": False,
            "physical_access_established": False,
            "assembly_sequence_verified": False,
            "drilling_released": False,
            "fabrication_released": False,
            "structural_released": False,
        },
    }
