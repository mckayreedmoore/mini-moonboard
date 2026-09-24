"""Bounded tool-envelope screen for the two upper WJ-05 center header bolts.

The catalog candidates and poses below support a nominal geometry review only.
They do not establish tool fit, usable access, delivered-part clearance, torque,
installation sequence, connection resistance, or release.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import cadquery as cq

from mini_moonboard.wood_joint_panel_machining import candidate_panel_replacements
from mini_moonboard.wood_joint_wj04_config import WJ04_TRIAL
from scripts import wood_joint_wj04_tool_access as shared_tool_access
from scripts import wood_joint_wj05_center_node_probe as center_probe
from scripts import wood_joints_wj05_center_backer_transfer_probe as backer_trial

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = ROOT / "docs/wood-joints-mvp/wj05-center-tools.json"
SCHEMA = "wood_joint_wj05_center_tools/v1"
HIT_TOLERANCE_MM3 = 1e-6
STROKE_DEGREES = 5.0
SOCKET_PRODUCT_ID = "gearwrench_80112_7_16"
SOCKET_PRODUCT_URL = (
    "https://www.gearwrench.com/all-tools/ratchets-sockets/chrome-sockets/"
    "80112-14-drive-6-point-standard-sae-socket-716"
)
SOCKET_AF_IN = "7/16"
SOCKET_AF_MM = 11.1125
SOCKET_OD_MM = 15.6972
SOCKET_LENGTH_MM = 24.511
SOCKET_DEPTH_MM = 12.4968
SOCKET_BOLT_CLEARANCE_MM = 5.588

EXTENSION_PRODUCT_ID = "koken_2760_75_1_4_drive"
EXTENSION_PRODUCT_URL = "https://kokenusa.com/products/extension-bar-1-4-dr-75mm"
EXTENSION_OD_MM = 12.3
EXTENSION_LENGTH_MM = 75.0

RATCHET_PRODUCT_ID = "gearwrench_81025_1_4_drive"
RATCHET_PRODUCT_URL = (
    "https://www.gearwrench.com/all-tools/ratchets-sockets/ratchets-drive-tools/"
    "81025-14-drive-72-tooth-quick-release-locking-flex-slim-head-ratchet-6"
)
RATCHET_HEAD_WIDTH_MM = 18.542
RATCHET_HEAD_THICKNESS_MM = 12.446
RATCHET_OVERALL_LENGTH_MM = 152.4

TOOL_PIN_PATHS = (
    "scripts/wood_joint_wj05_center_tools.py",
    "scripts/wood_joint_wj04_tool_access.py",
    "mini_moonboard/wood_joint_wj04_config.py",
)
STATION_IDS = tuple(
    f"center_principal_header_{side}_2" for side in ("left", "right")
)
REPLACED_CENTER_LEGACY_DUTIES = frozenset(
    {
        "clip_split_header_center_left",
        "clip_split_header_center_right",
        "clip_split_base_center_left",
        "clip_split_base_center_right",
    }
)


@dataclass(frozen=True)
class MaterializedCenterToolGeometry:
    """Source-bound WJ-05 solids consumed by the small tool-route screen."""

    trial_id: str
    source_fingerprints_sha256: dict[str, str]
    tool_source_fingerprints_sha256: dict[str, str]
    station_axes: dict[str, dict[str, Any]]
    installed_by_axis: dict[str, dict[str, cq.Shape]]
    obstacle_groups: dict[str, dict[str, cq.Shape]]
    retained_legacy_inventory: dict[str, Any]
    floor_z_mm: float


def _vector(value: Any, name: str) -> cq.Vector:
    try:
        result = cq.Vector(value)
    except (TypeError, ValueError, OverflowError) as error:
        raise ValueError(f"{name} must be a three-component vector") from error
    if not all(math.isfinite(component) for component in result.toTuple()):
        raise ValueError(f"{name} must be finite")
    if result.Length <= 1e-9:
        raise ValueError(f"{name} must be nonzero")
    return result.normalized()


def _valid_solid(shape: cq.Shape, name: str) -> cq.Shape:
    if not isinstance(shape, cq.Shape) or not shape.isValid() or not shape.Solids():
        raise ValueError(f"{name} must be valid solid geometry")
    return shape


def _projection_bounds(shape: cq.Shape, axis: cq.Vector) -> tuple[float, float]:
    bounds = shape.BoundingBox()
    corners = (
        cq.Vector(x, y, z)
        for x in (bounds.xmin, bounds.xmax)
        for y in (bounds.ymin, bounds.ymax)
        for z in (bounds.zmin, bounds.zmax)
    )
    projections = [point.dot(axis) for point in corners]
    return min(projections), max(projections)


def _round_vector(value: cq.Vector) -> list[float]:
    return [round(component, 9) for component in value.toTuple()]


def _shape_bounds(shape: cq.Shape) -> list[float]:
    bounds = shape.BoundingBox()
    return [
        round(value, 6)
        for value in (
            bounds.xmin,
            bounds.xmax,
            bounds.ymin,
            bounds.ymax,
            bounds.zmin,
            bounds.zmax,
        )
    ]


def _tool_source_fingerprints() -> dict[str, str]:
    return {
        path: hashlib.sha256((ROOT / path).read_bytes()).hexdigest()
        for path in TOOL_PIN_PATHS
    }


def _retained_legacy_hardware(
    model: Any,
    inventory: dict[str, Any],
) -> tuple[dict[str, cq.Shape], dict[str, cq.Shape], dict[str, Any]]:
    """Materialize 20 retained connector bodies and 120 retained SDS axes.

    Source inventory names select the four replaced center duties. Source model
    bodies/connections supply geometry; each retained axis is checked against
    its inventory datum and occupied envelope before being accepted.
    """
    duty_rows = inventory.get("legacy_duties", [])
    duty_ids = [row.get("legacy_station_id") for row in duty_rows]
    if len(duty_rows) != 24 or len(set(duty_ids)) != 24:
        raise ValueError("source inventory must contain 24 unique legacy duties")
    replaced_rows = [
        row
        for row in duty_rows
        if row.get("legacy_family") in {"header_center", "base_center"}
    ]
    replaced_ids = {row["legacy_station_id"] for row in replaced_rows}
    if replaced_ids != REPLACED_CENTER_LEGACY_DUTIES:
        raise ValueError("source inventory center-duty identities changed")
    all_axis_rows = [
        axis for row in duty_rows for axis in row.get("legacy_sds_axes", [])
    ]
    axis_rows = {row["axis_id"]: row for row in all_axis_rows}
    if len(all_axis_rows) != 144 or len(axis_rows) != 144:
        raise ValueError("source inventory must contain 144 unique legacy SDS axes")
    target_axis_ids = {
        axis["axis_id"]
        for row in replaced_rows
        for axis in row["legacy_sds_axes"]
    }
    if len(target_axis_ids) != 24:
        raise ValueError("four replaced center duties must own 24 legacy SDS axes")

    connector_parts = {
        part.name: part.shape
        for part in model.parts()
        if part.name.startswith("clip_")
    }
    if set(connector_parts) != set(duty_ids):
        raise ValueError("source model legacy connector identities changed")
    retained_duties = set(duty_ids) - replaced_ids
    retained_connectors = {
        name: _valid_solid(connector_parts[name], f"legacy connector {name}")
        for name in retained_duties
    }
    if len(retained_connectors) != 20:
        raise ValueError("expected exactly 20 retained legacy connector bodies")

    expected_axis_ids = set(axis_rows)
    source_connections = {
        connection.name: connection
        for connection in model.connections()
        if connection.kind == "screw" and connection.name in expected_axis_ids
    }
    if set(source_connections) != expected_axis_ids:
        raise ValueError("source model legacy SDS axis identities changed")

    retained_sds: dict[str, cq.Shape] = {}
    for axis_id, row in axis_rows.items():
        connection = source_connections[axis_id]
        expected_origin = cq.Vector(*row["origin_global_xyz_mm"])
        expected_direction = _vector(row["axis_global_xyz"], f"{axis_id}.inventory axis")
        if (connection.start - expected_origin).Length > 1e-6:
            raise ValueError(f"source SDS origin changed: {axis_id}")
        if (connection.direction.normalized() - expected_direction).Length > 1e-8:
            raise ValueError(f"source SDS direction changed: {axis_id}")
        if not math.isclose(
            connection.length,
            row["source_occupied_length_mm"],
            rel_tol=0.0,
            abs_tol=1e-6,
        ) or not math.isclose(
            connection.diameter,
            row["source_occupied_diameter_mm"],
            rel_tol=0.0,
            abs_tol=1e-6,
        ):
            raise ValueError(f"source SDS envelope changed: {axis_id}")
        if axis_id not in target_axis_ids:
            retained_sds[axis_id] = cq.Solid.makeCylinder(
                connection.diameter / 2,
                connection.length,
                connection.start,
                connection.direction.normalized(),
            )
    if len(retained_sds) != 120:
        raise ValueError("expected exactly 120 retained legacy SDS axes")

    summary = {
        "source_inventory_duty_count": len(duty_rows),
        "source_inventory_legacy_sds_axis_count": len(all_axis_rows),
        "replaced_center_duty_ids": sorted(replaced_ids),
        "excluded_replaced_center_sds_axis_count": len(target_axis_ids),
        "retained_connector_body_count": len(retained_connectors),
        "retained_sds_axis_count": len(retained_sds),
        "retained_connector_ids": sorted(retained_connectors),
        "retained_sds_axis_ids": sorted(retained_sds),
        "geometry_basis": (
            "inventory-selected source-model connector bodies and SDS axis "
            "envelopes; only four replaced center duties are excluded"
        ),
    }
    return retained_connectors, retained_sds, summary


def _qualified_obstacles(
    groups: dict[str, dict[str, cq.Shape]],
) -> dict[str, cq.Shape]:
    result: dict[str, cq.Shape] = {}
    for group, shapes in groups.items():
        for name, shape in shapes.items():
            key = f"{group}/{name}"
            if key in result:
                raise ValueError(f"duplicate obstacle ID: {key}")
            result[key] = shape
    return result


def _ratchet_envelope(
    drive_face: cq.Vector,
    outward: cq.Vector,
    inward_heading: cq.Vector,
) -> cq.Shape:
    """Build the inline ratchet's catalog-sized conservative exterior envelope."""
    outward = _vector(outward, "outward")
    inward = _vector(inward_heading, "inward_heading")
    if abs(outward.dot(inward)) > 1e-8:
        raise ValueError("ratchet handle heading must be in the bolt-face plane")

    radius = RATCHET_HEAD_WIDTH_MM / 2
    handle_center_distance = RATCHET_OVERALL_LENGTH_MM - 2 * radius
    if handle_center_distance <= 0:
        raise ValueError("ratchet overall length must exceed its head width")
    plane = cq.Plane(origin=drive_face, xDir=inward, normal=outward)
    handle = (
        cq.Workplane(plane)
        .box(
            handle_center_distance,
            RATCHET_HEAD_WIDTH_MM,
            RATCHET_HEAD_THICKNESS_MM,
            centered=(False, True, False),
        )
        .val()
    )
    head = cq.Solid.makeCylinder(
        radius,
        RATCHET_HEAD_THICKNESS_MM,
        drive_face,
        outward,
    )
    handle_tip_center = drive_face + inward * handle_center_distance
    handle_tip = cq.Solid.makeCylinder(
        radius,
        RATCHET_HEAD_THICKNESS_MM,
        handle_tip_center,
        outward,
    )
    result = cq.Compound.makeCompound((head, handle, handle_tip))
    return _valid_solid(result, "ratchet external envelope")


def _station_tool_shapes(
    axis: dict[str, Any],
    head: cq.Shape,
    nut: cq.Shape,
) -> tuple[dict[str, cq.Shape], dict[str, Any]]:
    """Return one seated socket/extension/ratchet and inboard nut wrench."""
    side = axis.get("side")
    if side not in ("left", "right"):
        raise ValueError("station axis must name left or right side")
    axis_point = cq.Vector(*axis["origin_global_xyz_mm"])
    bolt_direction = _vector(axis["direction_global_xyz"], "bolt direction")
    outward = -bolt_direction
    if abs(abs(outward.z) - 1.0) > 1e-8:
        raise ValueError("upper header tool stations require a vertical bolt axis")
    inward = cq.Vector(1 if side == "left" else -1, 0, 0)

    head_min, head_max = _projection_bounds(head, outward)
    head_height = head_max - head_min
    if not math.isclose(
        head_height,
        center_probe.HEAD_HEIGHT_MM,
        rel_tol=0.0,
        abs_tol=1e-6,
    ):
        raise ValueError("installed head height no longer matches center producer")
    axis_projection = axis_point.dot(outward)
    bearing_face = axis_point + outward * (head_min - axis_projection)
    outer_face = axis_point + outward * (head_max - axis_projection)

    # The socket OAL is measured from the seated mouth at the head bearing
    # plane. Its first head-height span contains the intended bolt-head
    # occupancy; do not add the head height a second time to the catalog OAL.
    socket_terminal = bearing_face + outward * SOCKET_LENGTH_MM
    socket_occupancy = cq.Solid.makeCylinder(
        SOCKET_OD_MM / 2,
        SOCKET_LENGTH_MM,
        bearing_face,
        outward,
    )
    socket_body = cq.Solid.makeCylinder(
        SOCKET_OD_MM / 2,
        SOCKET_LENGTH_MM,
        bearing_face,
        outward,
    )
    barrel_beyond_head_length = SOCKET_LENGTH_MM - head_height
    if barrel_beyond_head_length <= 0:
        raise ValueError("catalog socket OAL must exceed the installed head height")
    socket_barrel = cq.Solid.makeCylinder(
        SOCKET_OD_MM / 2,
        barrel_beyond_head_length,
        outer_face,
        outward,
    )
    extension_start = socket_terminal
    extension_terminal = extension_start + outward * EXTENSION_LENGTH_MM
    extension = cq.Solid.makeCylinder(
        EXTENSION_OD_MM / 2,
        EXTENSION_LENGTH_MM,
        extension_start,
        outward,
    )
    ratchet = _ratchet_envelope(extension_terminal, outward, inward)

    nut_outward = bolt_direction
    nut_center = shared_tool_access._seated_tool_center(
        axis_point,
        nut_outward,
        nut,
        WJ04_TRIAL.fasteners.tools[0].head_thickness_mm,
    )
    counterhold = shared_tool_access.build_catalog_wrench_envelope(
        nut_center,
        nut_outward.toTuple(),
        inward.toTuple(),
        WJ04_TRIAL.fasteners.tools[0],
        offset_degrees=0.0,
    )

    shapes = {
        "socket_bearing_face_seated_occupancy": _valid_solid(
            socket_occupancy, "socket seated external occupancy"
        ),
        "socket_product_body": _valid_solid(socket_body, "socket body envelope"),
        "socket_barrel_beyond_head": _valid_solid(
            socket_barrel, "socket barrel beyond head envelope"
        ),
        "extension_body": _valid_solid(extension, "extension body envelope"),
        "ratchet_inline_body": ratchet,
        "nut_side_counterhold": _valid_solid(counterhold, "counterhold envelope"),
    }
    bearing_projection = bearing_face.dot(outward)
    head_outer_projection = outer_face.dot(outward)
    socket_terminal_projection = socket_terminal.dot(outward)
    extension_terminal_projection = extension_terminal.dot(outward)
    nut_min, nut_max = _projection_bounds(nut, nut_outward)
    wrench_min, wrench_max = _projection_bounds(counterhold, nut_outward)
    return shapes, {
        "side": side,
        "axis_id": axis["axis_id"],
        "bolt_axis_xyz": _round_vector(bolt_direction),
        "head_tool_outward_axis_xyz": _round_vector(outward),
        "nut_tool_outward_axis_xyz": _round_vector(nut_outward),
        "inward_handle_heading_xyz": _round_vector(inward),
        "head_bearing_face_xyz_mm": _round_vector(bearing_face),
        "head_outer_face_xyz_mm": _round_vector(outer_face),
        "head_height_mm": round(head_height, 6),
        "socket_external_occupancy": {
            "axial_datum": "installed head bearing face; not head outer face",
            "bearing_face_projection_mm": round(bearing_projection, 6),
            "head_outer_face_projection_mm": round(head_outer_projection, 6),
            "socket_product_body_start_projection_mm": round(bearing_projection, 6),
            "socket_drive_end_projection_mm": round(
                socket_terminal_projection, 6
            ),
            "head_hex_depth_in_seated_proxy_mm": round(head_height, 6),
            "catalog_socket_body_length_mm": SOCKET_LENGTH_MM,
            "catalog_oal_already_includes_head_depth": True,
            "barrel_length_beyond_head_mm": round(barrel_beyond_head_length, 6),
            "catalog_outside_diameter_mm": SOCKET_OD_MM,
            "internal_profile_or_fit_modeled": False,
        },
        "extension_external_envelope": {
            "drive_face_start_projection_mm": round(
                socket_terminal_projection, 6
            ),
            "ratchet_drive_face_projection_mm": round(
                extension_terminal_projection, 6
            ),
            "catalog_length_mm": EXTENSION_LENGTH_MM,
            "catalog_outside_diameter_mm": EXTENSION_OD_MM,
            "socket_to_extension_square_drive_engagement_mm": None,
            "extension_to_ratchet_square_drive_engagement_mm": None,
            "external_mating_planes_coincident": True,
        },
        "ratchet_external_envelope": {
            "drive_face_projection_mm": round(extension_terminal_projection, 6),
            "body_thickness_mm": RATCHET_HEAD_THICKNESS_MM,
            "head_and_conservative_handle_width_mm": RATCHET_HEAD_WIDTH_MM,
            "overall_length_mm": RATCHET_OVERALL_LENGTH_MM,
            "handle_heading": "inward across the frame, toward global X=0",
            "flex_head_pose": "fixed inline pose; no flex-head articulation is swept",
        },
        "counterhold_seating": {
            "target_hex_axial_bounds_mm": [round(nut_min, 6), round(nut_max, 6)],
            "wrench_slab_axial_bounds_mm": [round(wrench_min, 6), round(wrench_max, 6)],
            "target_hex_height_mm": round(nut_max - nut_min, 6),
            "wrench_head_thickness_mm": WJ04_TRIAL.fasteners.tools[0].head_thickness_mm,
            "slab_centered_within_target_hex_height": math.isclose(
                wrench_min + wrench_max,
                nut_min + nut_max,
                rel_tol=0.0,
                abs_tol=1e-6,
            )
            and wrench_min >= nut_min - 1e-6
            and wrench_max <= nut_max + 1e-6,
            "jaw_profile_or_engagement_modeled": False,
        },
    }


def _floor_screen(shape: cq.Shape, floor_z_mm: float) -> dict[str, Any]:
    bounds = shape.BoundingBox()
    gap = bounds.zmin - floor_z_mm
    return {
        "shape_bounds_xyz_mm": _shape_bounds(shape),
        "analytical_floor_z_mm": round(floor_z_mm, 6),
        "minimum_nominal_gap_mm": round(gap, 6),
        "below_analytical_floor": gap < -1e-6,
        "floor_contact_or_support_qualified": False,
    }


def _screen_operation(
    candidate_shapes: dict[str, cq.Shape],
    obstacles: dict[str, cq.Shape],
    *,
    floor_z_mm: float,
    excluded_target_ids: tuple[str, ...] = (),
    exclusion_scope: str,
) -> dict[str, Any]:
    result = shared_tool_access.collision_report(
        candidate_shapes,
        obstacles,
        excluded_target_ids=excluded_target_ids,
        exclusion_scope=exclusion_scope,
    )
    return {
        **result,
        "floor_screen": {
            name: _floor_screen(shape, floor_z_mm)
            for name, shape in candidate_shapes.items()
        },
        "hit_obstacle_groups": sorted(
            {
                name.split("/", 1)[0]
                for hit_map in result["external_envelope_hits_mm3"].values()
                for name in hit_map
            }
        ),
    }


def build_tool_report(geometry: MaterializedCenterToolGeometry) -> dict[str, Any]:
    """Screen both upper-header row-2 tool routes against supplied solids."""
    if geometry.trial_id != center_probe.TRIAL_ID:
        raise ValueError("geometry trial ID must match the frozen center producer")
    if set(geometry.station_axes) != set(STATION_IDS):
        raise ValueError("geometry must contain exactly both upper-header row-2 axes")
    if set(geometry.installed_by_axis) < set(STATION_IDS):
        raise ValueError("geometry is missing an installed target stack")
    if not math.isfinite(geometry.floor_z_mm):
        raise ValueError("floor datum must be finite")

    obstacles = _qualified_obstacles(geometry.obstacle_groups)
    stations: dict[str, Any] = {}
    for station_id in STATION_IDS:
        axis = geometry.station_axes[station_id]
        if axis.get("axis_id") != station_id:
            raise ValueError("station mapping key must match its source axis ID")
        installed = geometry.installed_by_axis[station_id]
        for role in ("head", "shaft", "nut"):
            if role not in installed:
                raise ValueError(f"{station_id} is missing installed {role}")

        tool_shapes, pose = _station_tool_shapes(
            axis, installed["head"], installed["nut"]
        )
        head_id = f"candidate_installed_hardware/{station_id}/head"
        shaft_id = f"candidate_installed_hardware/{station_id}/shaft"
        nut_id = f"candidate_installed_hardware/{station_id}/nut"
        for target_id in (head_id, shaft_id, nut_id):
            if target_id not in obstacles:
                raise ValueError(f"tool target obstacle is missing: {target_id}")

        head_exclusions = (head_id, shaft_id)
        nut_exclusions = (nut_id, shaft_id)
        access_scope = (
            "Only the intended head and its own shaft are excluded for socket/"
            "extension occupancy. Washers, nuts, every other installed stack, "
            "all finished wood, fixed axes and protected solids remain obstacles."
        )
        counterhold_scope = (
            "Only the intended nut and its own shaft are excluded for the "
            "counterhold envelope. Washers, head, other installed hardware, "
            "finished wood, fixed axes and protected solids remain obstacles."
        )
        static_assembly = {
            name: tool_shapes[name]
            for name in (
                "socket_bearing_face_seated_occupancy",
                "extension_body",
                "ratchet_inline_body",
            )
        }
        station_obstacles = obstacles
        operations: dict[str, Any] = {
            "seated_socket_extension_and_inline_ratchet": _screen_operation(
                static_assembly,
                station_obstacles,
                floor_z_mm=geometry.floor_z_mm,
                excluded_target_ids=head_exclusions,
                exclusion_scope=access_scope,
            ),
            "nut_side_counterhold_seated_within_hex_height": _screen_operation(
                {"nut_side_counterhold": tool_shapes["nut_side_counterhold"]},
                station_obstacles,
                floor_z_mm=geometry.floor_z_mm,
                excluded_target_ids=nut_exclusions,
                exclusion_scope=counterhold_scope,
            ),
        }
        stroke_shapes: dict[int, cq.Shape] = {}
        axis_direction = cq.Vector(*axis["direction_global_xyz"]).normalized()
        pivot = cq.Vector(*axis["origin_global_xyz_mm"])
        for angle in (-STROKE_DEGREES, STROKE_DEGREES):
            swept_ratchet = shared_tool_access.rotational_sweep(
                tool_shapes["ratchet_inline_body"],
                pivot,
                axis_direction,
                angle,
            )
            stroke_shapes[angle] = swept_ratchet
            operation_id = f"ratchet_bounded_stroke_{angle:+g}_degrees"
            operations[operation_id] = _screen_operation(
                {
                    "socket_bearing_face_seated_occupancy": tool_shapes[
                        "socket_bearing_face_seated_occupancy"
                    ],
                    "extension_body": tool_shapes["extension_body"],
                    "ratchet_continuous_stroke_envelope": swept_ratchet,
                },
                station_obstacles,
                floor_z_mm=geometry.floor_z_mm,
                excluded_target_ids=head_exclusions,
                exclusion_scope=(
                    access_scope
                    + " The ratchet sweep is an analytic AABB enclosure for a "
                    "single bounded stroke; it is not a full rotation."
                ),
            )
        operations["ratchet_stroke_vs_nut_counterhold"] = {
            f"{angle:+g}_degree_stroke": _screen_operation(
                {"ratchet_continuous_stroke_envelope": shape},
                {"counterhold/nut_side_wrench": tool_shapes["nut_side_counterhold"]},
                floor_z_mm=geometry.floor_z_mm,
                exclusion_scope=(
                    "No tool is excluded. This compares the bounded ratchet "
                    "stroke proxy with the simultaneous nut-side counterhold."
                ),
            )
            for angle, shape in stroke_shapes.items()
        }
        af = SOCKET_AF_MM
        head_bounds = WJ04_TRIAL.fasteners.head.across_flats_range_mm
        nut_bounds = WJ04_TRIAL.fasteners.nut.across_flats_range_mm
        stations[station_id] = {
            "axis": axis,
            "tool_pose_and_seating": pose,
            "operations": operations,
            "nominal_hex_width_reference": {
                "socket_and_counterhold_nominal_af_mm": af,
                "source_head_af_bounds_mm": list(head_bounds),
                "source_nut_af_bounds_mm": list(nut_bounds),
                "nominal_width_within_both_source_ranges": (
                    head_bounds[0] <= af <= head_bounds[1]
                    and nut_bounds[0] <= af <= nut_bounds[1]
                ),
                "fit_or_received_hardware_verified": False,
            },
        }

    return {
        "schema": SCHEMA,
        "trial_id": geometry.trial_id,
        "source_fingerprints_sha256": geometry.source_fingerprints_sha256,
        "tool_source_fingerprints_sha256": geometry.tool_source_fingerprints_sha256,
        "retained_legacy_hardware_inventory": geometry.retained_legacy_inventory,
        "stations": stations,
        "tool_candidates": {
            "socket": {
                "candidate_id": SOCKET_PRODUCT_ID,
                "manufacturer": "GEARWRENCH",
                "product_url": SOCKET_PRODUCT_URL,
                "drive_square": "1/4 in",
                "nominal_opening": SOCKET_AF_IN,
                "point_count": 6,
                "overall_length_mm": SOCKET_LENGTH_MM,
                "outside_diameter_mm": SOCKET_OD_MM,
                "published_wrench_depth_mm": SOCKET_DEPTH_MM,
                "published_bolt_clearance_mm": SOCKET_BOLT_CLEARANCE_MM,
                "selected": False,
                "internal_profile_and_fit_verified": False,
            },
            "extension": {
                "candidate_id": EXTENSION_PRODUCT_ID,
                "manufacturer": "Ko-ken",
                "product_url": EXTENSION_PRODUCT_URL,
                "drive_square_input_and_output": "1/4 in",
                "overall_length_mm": EXTENSION_LENGTH_MM,
                "outside_diameter_mm": EXTENSION_OD_MM,
                "selected": False,
            },
            "ratchet": {
                "candidate_id": RATCHET_PRODUCT_ID,
                "manufacturer": "GEARWRENCH",
                "product_url": RATCHET_PRODUCT_URL,
                "drive_square": "1/4 in",
                "head_width_mm": RATCHET_HEAD_WIDTH_MM,
                "head_thickness_mm": RATCHET_HEAD_THICKNESS_MM,
                "overall_length_mm": RATCHET_OVERALL_LENGTH_MM,
                "tooth_swing_degrees": STROKE_DEGREES,
                "stroke_cases_degrees": [-STROKE_DEGREES, STROKE_DEGREES],
                "selected": False,
                "flex_head_articulation_modeled": False,
            },
            "nut_side_counterhold": {
                "candidate_id": WJ04_TRIAL.fasteners.tools[0].candidate_id,
                "manufacturer": WJ04_TRIAL.fasteners.tools[0].manufacturer,
                "source_urls": list(WJ04_TRIAL.fasteners.tools[0].source_urls),
                "nominal_opening_in": WJ04_TRIAL.fasteners.tools[0].wrench_size_in,
                "head_width_mm": WJ04_TRIAL.fasteners.tools[0].head_width_mm,
                "head_thickness_mm": WJ04_TRIAL.fasteners.tools[0].head_thickness_mm,
                "overall_length_mm": WJ04_TRIAL.fasteners.tools[0].overall_length_mm,
                "catalog_head_offsets_degrees": list(
                    WJ04_TRIAL.fasteners.tools[0].head_offsets_degrees
                ),
                "modeled_global_offset_degrees": 0.0,
                "inward_heading_is_a_pose_proxy": True,
                "selected": False,
                "jaw_profile_or_engagement_verified": False,
            },
        },
        "screen_basis": {
            "scope": "upper-header row-2 installed head-side tools at both mirrored center stations",
            "obstacles": sorted(geometry.obstacle_groups),
            "timber_obstacle_status": (
                "Raw source-derived frame timber has candidate WJ-05 bores, but "
                "some retained source openings may be absent from host solids. "
                "Treat timber hits conservatively until machining integration "
                "restores retained openings."
            ),
            "noninstalled_backer_tool_envelopes": (
                "Excluded as tools rather than physical obstacles; active backer "
                "installed shafts, washers, heads and nuts remain included."
            ),
            "analytical_floor_z_mm": geometry.floor_z_mm,
            "socket_ratchet_drive_engagement": (
                "Catalog parts have nominally matching 1/4-in square drives. "
                "External mating planes are coincident in the model; drive-tang "
                "engagement depths, internal geometry, backlash and clearance "
                "are unknown and not modeled."
            ),
            "ratchet_envelope": (
                "Inline fixed pose. Catalog head width and thickness bound the "
                "whole handle envelope; the handle-width extension is conservative. "
                "Both signed 5-degree strokes use the shared analytic AABB sweep."
            ),
            "ordinary_counterhold_pose": (
                "FACOM catalog envelope is centered axially within the nut hex "
                "height and headed inward; jaw shape and contact are not modeled."
            ),
            "tool_installation_sequence_verified": False,
            "tolerance_or_manual_clearance_applied": False,
        },
        "claims": {
            "nominal_envelope_screen_only": True,
            "physical_access_established": False,
            "tool_fit_established": False,
            "tool_selected": False,
            "torque_or_fastener_turning_established": False,
            "installation_or_removal_sequence_established": False,
            "structural_resistance_assigned": False,
            "engineering_or_fabrication_release": False,
        },
        "release_flags": {
            "drilling_released": False,
            "fabrication_released": False,
            "structural_released": False,
            "rating_claimed": False,
        },
    }


def materialize_center_geometry() -> MaterializedCenterToolGeometry:
    """Build the frozen center producer's shapes for a later authorized screen.

    This is deliberately separate from module import and is not called by the
    focused adapter tests. It rebuilds the producer's source-bound geometry
    when the parent grants the serialized CAD/report slot.
    """
    inventory = json.loads(center_probe.SOURCE_INVENTORY.read_text())
    (
        model,
        _source_wood,
        source_parts,
        _backers,
        backer_bolts,
        _backer_bores,
        backer_stacks,
        backer_tools,
        _counterbores,
    ) = backer_trial._source_and_candidate()
    replacements = candidate_panel_replacements(
        model,
        current_parts=model.parts(),
        uncut_parts=model.uncut_wood_parts(),
    )
    for name, part in replacements.items():
        source_parts[name] = part.shape

    parts = center_probe._candidate_parts(source_parts)
    axes = [
        axis
        for side in center_probe.SIDES
        for axis in (
            center_probe._upper_fastener_axes(side)
            + center_probe._lower_fastener_axes(side)
        )
    ]
    station_axes = {
        axis["axis_id"]: axis for axis in axes if axis["axis_id"] in STATION_IDS
    }
    if set(station_axes) != set(STATION_IDS):
        raise ValueError("frozen producer no longer exposes both expected header axes")
    finished = center_probe._finished_trial_parts(axes, parts)

    fixed_rows = inventory["fixed_panel_kicker_screws"]
    if len(fixed_rows) != 66 or len({row["axis_id"] for row in fixed_rows}) != 66:
        raise ValueError("expected the retained 66 fixed panel/kicker axes")
    fixed_axes = {
        row["axis_id"]: center_probe._inventory_axis_shape(row, fixed_screw=True)
        for row in fixed_rows
    }
    _frame_records, retained_frame_shapes = center_probe._source_frame_bolt_records(
        model, inventory["starting_frame_bolts"]
    )
    backer_installed, _backer_tool_envelopes = center_probe._active_backer_components(
        backer_bolts,
        backer_stacks,
        backer_tools,
    )
    protected = center_probe.protected_inventory()
    protected_shapes = {
        f"{family}/{name}": shape
        for family, shapes in protected["solids"].items()
        for name, shape in shapes.items()
    }
    retained_connectors, retained_sds, retained_legacy_inventory = (
        _retained_legacy_hardware(model, inventory)
    )
    installed_by_axis = {
        axis["axis_id"]: {
            role: shape
            for role, shape in center_probe._fastener_shapes(axis).items()
            if role not in ("bore", "head_tool", "nut_tool")
        }
        for axis in axes
    }
    candidate_hardware = {
        f"{axis_id}/{role}": shape
        for axis_id, roles in installed_by_axis.items()
        for role, shape in roles.items()
    }
    obstacle_groups = {
        "center_trial_timber_conservative": finished,
        "protected": protected_shapes,
        "fixed_66_panel_kicker_axes": fixed_axes,
        "retained_frame_bolt_components_and_axes": retained_frame_shapes,
        "active_wj05_backer_installed_hardware": backer_installed,
        "retained_legacy_connector_bodies": retained_connectors,
        "retained_legacy_sds_axes": retained_sds,
        "candidate_installed_hardware": candidate_hardware,
    }
    tool_pins = _tool_source_fingerprints()
    return MaterializedCenterToolGeometry(
        trial_id=center_probe.TRIAL_ID,
        source_fingerprints_sha256=center_probe._source_bindings(),
        tool_source_fingerprints_sha256=tool_pins,
        station_axes=station_axes,
        installed_by_axis=installed_by_axis,
        obstacle_groups=obstacle_groups,
        retained_legacy_inventory=retained_legacy_inventory,
        floor_z_mm=0.0,
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true", help="write the JSON report")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args(argv)
    report = build_tool_report(materialize_center_geometry())
    encoded = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.write:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(encoded)
    else:
        print(encoded, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
