"""Source-bound WJ-05 center cleat fit comparison; diagnostic only.

The probe checks a lower full 4x4 post/header cleat and a shortened rear 4x4
principal/header cleat with a conditional open wire-relief cut. It checks
nominal fit, proposed ordinary-bolt envelopes, fixed panel/kicker axes,
retained frame bolts, WJ-05 backer hardware, source-wire clearance, and tool
envelopes. It assigns no resistance and releases no drilling or fabrication.
"""

from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path

import cadquery as cq

from mini_moonboard.wood_joint_panel_machining import candidate_panel_replacements
from scripts import wood_joints_wj05_center_backer_transfer_probe as backer_trial
from scripts.owner_layout_protected import inventory as protected_inventory

ROOT = Path(__file__).resolve().parents[1]
SOURCE_INVENTORY = ROOT / "docs/wood-joints-mvp/source-inventory.json"

TRIAL_ID = "wj05-center-node-rear-4x4-upper-l82-wire-relief-v2"
ANGLE_DEG = 50.0
ANGLE_RAD = math.radians(ANGLE_DEG)
GRAIN_T = (0.0, math.cos(ANGLE_RAD), math.sin(ANGLE_RAD))
GRAIN_N = (0.0, -math.sin(ANGLE_RAD), math.cos(ANGLE_RAD))

# One 4x4 block outside each shifted center post.
LOWER_CLEAT_BOUNDS_RIGHT_MM = (
    (199.05, 287.95),
    (-175.7, -86.8),
    (110.0, 238.9),
)
LOWER_CLEAT_GRAIN_AXIS = (0.0, 0.0, 1.0)

# One full-section 4x4 block outside each center principal. The horizontal
# Z=277 end cut seats on the header. S=T+cot(50 deg)*N measures distance along
# grain from that cut; raw stock includes T=-cot(50 deg)*139.7 through
# T=82-cot(50 deg)*50.8.
UPPER_CLEAT_X_RIGHT_MM = (89.05, 177.95)
UPPER_CLEAT_N_MM = (50.8, 139.7)
UPPER_CLEAT_GRAIN_LENGTH_MM = 82.0
UPPER_CLEAT_GRAIN_T_MIN_MM = (
    -math.cos(ANGLE_RAD) / math.sin(ANGLE_RAD) * UPPER_CLEAT_N_MM[1]
)
UPPER_CLEAT_GRAIN_T_MAX_MM = (
    UPPER_CLEAT_GRAIN_LENGTH_MM
    - math.cos(ANGLE_RAD) / math.sin(ANGLE_RAD) * UPPER_CLEAT_N_MM[0]
)
UPPER_CLEAT_RAW_GRAIN_LENGTH_MM = (
    UPPER_CLEAT_GRAIN_T_MAX_MM - UPPER_CLEAT_GRAIN_T_MIN_MM
)
UPPER_CLEAT_ORIGIN_YZ_MM = (-41.49733120798, 277.0)
UPPER_PRINCIPAL_ROW_STATIONS_MM = (24.5, 57.5)
UPPER_PRINCIPAL_ROW_N_MM = 95.25
UPPER_HEADER_BOLT_X_MM = (116.0, 151.0)
UPPER_HEADER_BOLT_Y_MM = -139.4
UPPER_WIRE_RELIEF_T_MM = 30.0
UPPER_WIRE_RELIEF_N_MAX_MM = (
    UPPER_CLEAT_GRAIN_LENGTH_MM - UPPER_WIRE_RELIEF_T_MM
) * math.tan(ANGLE_RAD)
MIN_SOURCE_WIRE_CLEARANCE_MM = 2.0

BOLT_DIAMETER_MM = 6.35
BORE_DIAMETER_MM = 7.3
HEAD_DIAMETER_MM = 12.827
HEAD_HEIGHT_MM = 4.7752
WASHER_DIAMETER_MM = 16.256
WASHER_THICKNESS_MM = 1.651
NUT_DIAMETER_MM = 12.827
NUT_HEIGHT_MM = 5.7404
THREAD_PAST_NUT_MM = 3.175
TOOL_DIAMETER_MM = 25.4
TOOL_LENGTH_MM = 50.0
GEOMETRY_TOL_MM3 = 0.01
FOUR_D_MM = 4.0 * BOLT_DIAMETER_MM
FIVE_D_MM = 5.0 * BOLT_DIAMETER_MM
THREE_AND_HALF_D_MM = 3.5 * BOLT_DIAMETER_MM

SIDES = ("left", "right")
FIXED_PANEL_MEMBERS = frozenset(
    {
        "main_lower_left",
        "main_lower_right",
        "main_upper_left",
        "main_upper_right",
    }
)
FIXED_KICKER_MEMBERS = frozenset({"kicker_left", "kicker_right"})
RELEASE_FLAGS = {
    "drilling_released": False,
    "fabrication_released": False,
    "structural_released": False,
    "rating_claimed": False,
}


def _bounds(shape: cq.Shape) -> list[float]:
    box = shape.BoundingBox()
    return [
        round(value, 5)
        for value in (box.xmin, box.xmax, box.ymin, box.ymax, box.zmin, box.zmax)
    ]


def _overlapping_bounds(a, b) -> bool:
    return not (
        a.xmax < b.xmin
        or b.xmax < a.xmin
        or a.ymax < b.ymin
        or b.ymax < a.ymin
        or a.zmax < b.zmin
        or b.zmax < a.zmin
    )


def _volume(first: cq.Shape, second: cq.Shape) -> float:
    a, b = first.BoundingBox(), second.BoundingBox()
    if not _overlapping_bounds(a, b):
        return 0.0
    return first.intersect(second).Volume()


def _hits(shape: cq.Shape, targets: dict[str, cq.Shape]) -> dict[str, float]:
    result = {}
    bounds = shape.BoundingBox()
    for name, other in targets.items():
        if _overlapping_bounds(bounds, other.BoundingBox()):
            volume = _volume(shape, other)
            if volume > GEOMETRY_TOL_MM3:
                result[name] = round(volume, 6)
    return result


def _cylinder(
    radius: float,
    length: float,
    start: tuple[float, float, float],
    direction: tuple[float, float, float],
) -> cq.Shape:
    return cq.Solid.makeCylinder(
        radius,
        length,
        cq.Vector(*start),
        cq.Vector(*direction).normalized(),
    )


def _mirror_x(shape: cq.Shape) -> cq.Shape:
    return cq.Workplane(obj=shape).mirror("YZ").val()


def _upper_cleat_wire_relief() -> cq.Shape:
    """Open triangular wire-relief cut; not a housed or interlocking joint."""
    y0, z0 = UPPER_CLEAT_ORIGIN_YZ_MM
    cosine, sine = math.cos(ANGLE_RAD), math.sin(ANGLE_RAD)
    plane = cq.Plane(
        origin=(UPPER_CLEAT_X_RIGHT_MM[0], y0, z0),
        xDir=(0.0, cosine, sine),
        normal=(1.0, 0.0, 0.0),
    )
    n_min = UPPER_CLEAT_N_MM[0]
    t_max_at_n_min = UPPER_CLEAT_GRAIN_LENGTH_MM - cosine / sine * n_min
    return (
        cq.Workplane(plane)
        .polyline(
            [
                (UPPER_WIRE_RELIEF_T_MM, n_min),
                (t_max_at_n_min, n_min),
                (UPPER_WIRE_RELIEF_T_MM, UPPER_WIRE_RELIEF_N_MAX_MM),
            ]
        )
        .close()
        .extrude(UPPER_CLEAT_X_RIGHT_MM[1] - UPPER_CLEAT_X_RIGHT_MM[0])
        .val()
    )


def _upper_cleat_right(*, apply_wire_relief: bool = True) -> cq.Shape:
    y0, z0 = UPPER_CLEAT_ORIGIN_YZ_MM
    cosine, sine = math.cos(ANGLE_RAD), math.sin(ANGLE_RAD)
    plane = cq.Plane(
        origin=(UPPER_CLEAT_X_RIGHT_MM[0], y0, z0),
        xDir=(0.0, cosine, sine),
        normal=(1.0, 0.0, 0.0),
    )
    n_min, n_max = UPPER_CLEAT_N_MM
    t_min_at_n_min = -cosine / sine * n_min
    t_max_at_n_min = UPPER_CLEAT_GRAIN_LENGTH_MM + t_min_at_n_min
    t_max_at_n_max = UPPER_CLEAT_GRAIN_LENGTH_MM - cosine / sine * n_max
    t_min_at_n_max = -cosine / sine * n_max
    stock_shape = (
        cq.Workplane(plane)
        .polyline(
            [
                (t_min_at_n_min, n_min),
                (t_max_at_n_min, n_min),
                (t_max_at_n_max, n_max),
                (t_min_at_n_max, n_max),
            ]
        )
        .close()
        .extrude(UPPER_CLEAT_X_RIGHT_MM[1] - UPPER_CLEAT_X_RIGHT_MM[0])
        .val()
    )
    if not apply_wire_relief:
        return stock_shape
    return stock_shape.cut(_upper_cleat_wire_relief()).clean()


def _upper_local_tn(y: float, z: float) -> tuple[float, float]:
    y0, z0 = UPPER_CLEAT_ORIGIN_YZ_MM
    dy, dz = y - y0, z - z0
    cosine, sine = math.cos(ANGLE_RAD), math.sin(ANGLE_RAD)
    return cosine * dy + sine * dz, -sine * dy + cosine * dz


def _candidate_parts(source_parts: dict[str, cq.Shape]) -> dict[str, cq.Shape]:
    lower_right = cq.Solid.makeBox(
        LOWER_CLEAT_BOUNDS_RIGHT_MM[0][1] - LOWER_CLEAT_BOUNDS_RIGHT_MM[0][0],
        LOWER_CLEAT_BOUNDS_RIGHT_MM[1][1] - LOWER_CLEAT_BOUNDS_RIGHT_MM[1][0],
        LOWER_CLEAT_BOUNDS_RIGHT_MM[2][1] - LOWER_CLEAT_BOUNDS_RIGHT_MM[2][0],
        cq.Vector(
            LOWER_CLEAT_BOUNDS_RIGHT_MM[0][0],
            LOWER_CLEAT_BOUNDS_RIGHT_MM[1][0],
            LOWER_CLEAT_BOUNDS_RIGHT_MM[2][0],
        ),
    )
    upper_right = _upper_cleat_right()
    candidates = {
        "center_post_cleat_right": lower_right,
        "center_post_cleat_left": cq.Solid.makeBox(
            LOWER_CLEAT_BOUNDS_RIGHT_MM[0][1] - LOWER_CLEAT_BOUNDS_RIGHT_MM[0][0],
            LOWER_CLEAT_BOUNDS_RIGHT_MM[1][1] - LOWER_CLEAT_BOUNDS_RIGHT_MM[1][0],
            LOWER_CLEAT_BOUNDS_RIGHT_MM[2][1] - LOWER_CLEAT_BOUNDS_RIGHT_MM[2][0],
            cq.Vector(
                -LOWER_CLEAT_BOUNDS_RIGHT_MM[0][1],
                LOWER_CLEAT_BOUNDS_RIGHT_MM[1][0],
                LOWER_CLEAT_BOUNDS_RIGHT_MM[2][0],
            ),
        ),
        "center_principal_cleat_right": upper_right,
        "center_principal_cleat_left": _mirror_x(upper_right),
    }
    return source_parts | candidates


def _finished_trial_parts(
    axes: list[dict], parts: dict[str, cq.Shape]
) -> dict[str, cq.Shape]:
    """Cut only proposed clearance bores into each named receiver member."""
    result = dict(parts)
    for axis in axes:
        bore = _fastener_shapes(axis)["bore"]
        for owner in axis["intended_receivers"]:
            result[owner] = result[owner].cut(bore).clean()
    return result


def _axis_record(
    axis_id: str,
    start: tuple[float, float, float],
    direction: tuple[float, float, float],
    length: float,
    owners: tuple[str, str],
    interface_id: str,
    connection_group: str,
    side: str,
) -> dict:
    return {
        "axis_id": axis_id,
        "interface_id": interface_id,
        "connection_group": connection_group,
        "side": side,
        "origin_global_xyz_mm": [round(v, 9) for v in start],
        "direction_global_xyz": [round(v, 9) for v in direction],
        "wood_grip_mm": round(length, 6),
        "bolt_body_diameter_mm": BOLT_DIAMETER_MM,
        "clearance_bore_diameter_mm": BORE_DIAMETER_MM,
        "intended_receivers": list(owners),
        "candidate_sku": None,
        "capacity_assigned": False,
    }


def _axis_screen_metadata(axis: dict) -> dict:
    axis_id = axis["axis_id"]
    point = axis["origin_global_xyz_mm"]
    if axis_id.startswith("center_principal_"):
        if "header" not in axis_id:
            row_index = int(axis_id.rsplit("_", 1)[1]) - 1
            grain_station = UPPER_PRINCIPAL_ROW_STATIONS_MM[row_index]
            n_center = UPPER_PRINCIPAL_ROW_N_MM
            t_center = grain_station - math.cos(ANGLE_RAD) / math.sin(ANGLE_RAD) * n_center
            return {
                "cleat_cross_grain_edge_distances_mm": [
                    n_center - UPPER_CLEAT_N_MM[0],
                    UPPER_CLEAT_N_MM[1] - n_center,
                ],
                "grain_end_distances_mm": [
                    grain_station,
                    UPPER_CLEAT_GRAIN_LENGTH_MM - grain_station,
                ],
                "nearest_grain_end_conditional_3p5D_margin_mm": round(
                    min(
                        grain_station,
                        UPPER_CLEAT_GRAIN_LENGTH_MM - grain_station,
                    )
                    - THREE_AND_HALF_D_MM,
                    6,
                ),
                "nearest_grain_end_conditional_7D_margin_mm": round(
                    min(
                        grain_station,
                        UPPER_CLEAT_GRAIN_LENGTH_MM - grain_station,
                    )
                    - 7.0 * BOLT_DIAMETER_MM,
                    6,
                ),
                "crossgrain_ray_to_horizontal_seat_geometry_only_mm": round(
                    grain_station * math.tan(ANGLE_RAD), 6
                ),
                "signed_T_distance_to_relief_plane_mm": round(
                    t_center - UPPER_WIRE_RELIEF_T_MM, 6
                ),
                "principal_row_pitch_mm": round(
                    UPPER_PRINCIPAL_ROW_STATIONS_MM[1]
                    - UPPER_PRINCIPAL_ROW_STATIONS_MM[0],
                    6,
                ),
                "principal_row_pitch_minus_5D_mm": round(
                    UPPER_PRINCIPAL_ROW_STATIONS_MM[1]
                    - UPPER_PRINCIPAL_ROW_STATIONS_MM[0]
                    - FIVE_D_MM,
                    6,
                ),
                "conditional_screens_mm": {
                    "4D_edge": FOUR_D_MM,
                    "3.5D_grain_end": THREE_AND_HALF_D_MM,
                    "5D_pair_spacing": FIVE_D_MM,
                },
                "note": "Geometry only. The horizontal seat is oblique to grain; NDS edge/end applicability requires signed actions and a supported oblique termination method.",
            }
        x = point[0]
        side = axis["side"]
        z_top = 277.0 + math.sin(ANGLE_RAD) * UPPER_CLEAT_GRAIN_LENGTH_MM
        n_at_entry = _upper_local_tn(point[1], 277.0)[1]
        n_at_top = _upper_local_tn(point[1], z_top)[1]
        if side == "right":
            x_edges = [x - UPPER_CLEAT_X_RIGHT_MM[0], UPPER_CLEAT_X_RIGHT_MM[1] - x]
        else:
            x_edges = [
                x + UPPER_CLEAT_X_RIGHT_MM[1],
                -UPPER_CLEAT_X_RIGHT_MM[0] - x,
            ]
        return {
            "cleat_x_edge_distances_mm": x_edges,
            "header_y_edge_distances_mm": [point[1] + 175.7, -36.0 - point[1]],
            "cleat_entry_local_N_edge_distances_mm": [
                n_at_entry - UPPER_CLEAT_N_MM[0],
                UPPER_CLEAT_N_MM[1] - n_at_entry,
            ],
            "cleat_exit_local_N_edge_distances_mm": [
                n_at_top - UPPER_CLEAT_N_MM[0],
                UPPER_CLEAT_N_MM[1] - n_at_top,
            ],
            "cleat_axis_path_min_local_N_edge_distance_mm": min(
                n_at_entry - UPPER_CLEAT_N_MM[0],
                UPPER_CLEAT_N_MM[1] - n_at_top,
            ),
            "conditional_screens_mm": {
                "4D_edge": FOUR_D_MM,
                "5D_pair_spacing": FIVE_D_MM,
            },
            "note": "Vertical axis has flat Z end seats; side-edge categories remain conditional on signed actions.",
        }
    if axis_id.startswith("center_post_") and "header" not in axis_id:
        z = point[2]
        return {
            "post_and_cleat_y_edge_distances_mm": [44.45, 95.25],
            "cleat_z_end_distances_mm": [z - 110.0, 238.9 - z],
            "conditional_screens_mm": {
                "4D_edge": FOUR_D_MM,
                "3.5D_grain_end": THREE_AND_HALF_D_MM,
                "5D_pair_spacing": FIVE_D_MM,
            },
            "note": "Geometry-only screen; governing wood side and loaded edge require signed joint actions.",
        }
    y = point[1]
    x = point[0]
    if axis["side"] == "right":
        x_edges = [x - 199.05, 287.95 - x]
    else:
        x_edges = [x + 287.95, -199.05 - x]
    return {
        "cleat_x_edge_distances_mm": x_edges,
        "cleat_y_edge_distances_mm": [y + 175.7, -86.8 - y],
        "header_y_edge_distances_mm": [y + 175.7, -36.0 - y],
        "conditional_screens_mm": {
            "4D_edge": FOUR_D_MM,
            "5D_pair_spacing": FIVE_D_MM,
        },
        "note": "Vertical header axes are parallel to cleat Z grain; complete parallel-grain bolt-group behavior is unassessed.",
    }


def _upper_fastener_axes(side: str) -> list[dict]:
    sign = 1.0 if side == "right" else -1.0
    principal = f"base_principal_center_{side}"
    cleat = f"center_principal_cleat_{side}"
    x_start = 50.95 if side == "right" else -50.95
    y0, z0 = UPPER_CLEAT_ORIGIN_YZ_MM
    n_center = UPPER_PRINCIPAL_ROW_N_MM
    rows = []
    for index, grain_station in enumerate(UPPER_PRINCIPAL_ROW_STATIONS_MM, 1):
        t = grain_station - math.cos(ANGLE_RAD) / math.sin(ANGLE_RAD) * n_center
        y = y0 + math.cos(ANGLE_RAD) * t - math.sin(ANGLE_RAD) * n_center
        z = z0 + math.sin(ANGLE_RAD) * t + math.cos(ANGLE_RAD) * n_center
        rows.append(
            _axis_record(
                f"center_principal_{side}_{index}",
                (x_start, y, z),
                (sign, 0.0, 0.0),
                127.0,
                (principal, cleat),
                f"clip_split_base_center_{side}",
                f"principal_to_upper_cleat_{side}",
                side,
            )
        )
    x_rows = (
        UPPER_HEADER_BOLT_X_MM
        if side == "right"
        else tuple(-value for value in UPPER_HEADER_BOLT_X_MM)
    )
    y_row = UPPER_HEADER_BOLT_Y_MM
    z_top = 277.0 + math.sin(ANGLE_RAD) * UPPER_CLEAT_GRAIN_LENGTH_MM
    for index, x in enumerate(x_rows, 1):
        rows.append(
            _axis_record(
                f"center_principal_header_{side}_{index}",
                (x, y_row, 238.9),
                (0.0, 0.0, 1.0),
                z_top - 238.9,
                ("base_header", cleat),
                f"clip_split_base_center_{side}",
                f"header_to_upper_cleat_{side}",
                side,
            )
        )
    return rows


def _lower_fastener_axes(side: str) -> list[dict]:
    shift_sign = 1.0 if side == "right" else -1.0
    post = f"base_post_center_{side}"
    cleat = f"center_post_cleat_{side}"
    post_edge = 160.95 if side == "right" else -160.95
    direction = (shift_sign, 0.0, 0.0)
    rows = []
    for index, z in enumerate((145.0, 195.0), 1):
        rows.append(
            _axis_record(
                f"center_post_{side}_{index}",
                (post_edge, -131.25, z),
                direction,
                127.0,
                (post, cleat),
                f"clip_split_header_center_{side}",
                f"post_to_lower_cleat_{side}",
                side,
            )
        )
    x = 244.0 * shift_sign
    for index, y in enumerate((-148.75, -113.75), 1):
        rows.append(
            _axis_record(
                f"center_post_header_{side}_{index}",
                (x, y, 110.0),
                (0.0, 0.0, 1.0),
                167.0,
                (cleat, "base_header"),
                f"clip_split_header_center_{side}",
                f"header_to_lower_cleat_{side}",
                side,
            )
        )
    return rows


def _fastener_shapes(axis: dict) -> dict[str, cq.Shape]:
    start = cq.Vector(*axis["origin_global_xyz_mm"])
    direction = cq.Vector(*axis["direction_global_xyz"])
    grip = axis["wood_grip_mm"]
    far = start + direction * grip
    washer_t = WASHER_THICKNESS_MM
    full_length = grip + 2 * washer_t + NUT_HEIGHT_MM + THREAD_PAST_NUT_MM
    shaft_start = start - direction * washer_t
    head_outer = start - direction * (washer_t + HEAD_HEIGHT_MM)
    nut_outer = far + direction * (washer_t + NUT_HEIGHT_MM)
    return {
        "bore": cq.Solid.makeCylinder(
            BORE_DIAMETER_MM / 2, grip, start, direction
        ),
        "shaft": cq.Solid.makeCylinder(
            BOLT_DIAMETER_MM / 2, full_length, shaft_start, direction
        ),
        "head_washer": cq.Solid.makeCylinder(
            WASHER_DIAMETER_MM / 2,
            washer_t,
            start - direction * washer_t,
            direction,
        ).cut(
            cq.Solid.makeCylinder(
                BOLT_DIAMETER_MM / 2,
                washer_t,
                start - direction * washer_t,
                direction,
            )
        ),
        "head": cq.Solid.makeCylinder(
            HEAD_DIAMETER_MM / 2,
            HEAD_HEIGHT_MM,
            head_outer,
            direction,
        ),
        "nut_washer": cq.Solid.makeCylinder(
            WASHER_DIAMETER_MM / 2, washer_t, far, direction
        ).cut(cq.Solid.makeCylinder(BOLT_DIAMETER_MM / 2, washer_t, far, direction)),
        "nut": cq.Solid.makeCylinder(
            NUT_DIAMETER_MM / 2,
            NUT_HEIGHT_MM,
            far + direction * washer_t,
            direction,
        ),
        "head_tool": cq.Solid.makeCylinder(
            TOOL_DIAMETER_MM / 2,
            TOOL_LENGTH_MM,
            head_outer - direction * TOOL_LENGTH_MM,
            direction,
        ),
        "nut_tool": cq.Solid.makeCylinder(
            TOOL_DIAMETER_MM / 2,
            TOOL_LENGTH_MM,
            nut_outer,
            direction,
        ),
    }


def _washer_support(
    member: cq.Shape,
    face_point: cq.Vector,
    inward: cq.Vector,
) -> float:
    probe = cq.Solid.makeCylinder(
        WASHER_DIAMETER_MM / 2,
        0.02,
        face_point + inward * 0.001,
        inward,
    )
    return _volume(probe, member) / probe.Volume()


def _axis_checks(
    axes: list[dict], parts: dict[str, cq.Shape]
) -> tuple[list[dict], dict[str, dict[str, float]]]:
    records = []
    all_shapes = {}
    for axis in axes:
        shapes = _fastener_shapes(axis)
        all_shapes[axis["axis_id"]] = shapes
        bore = shapes["bore"]
        owners = axis["intended_receivers"]
        received = {
            owner: _volume(bore, parts[owner]) / bore.Volume() for owner in owners
        }
        other_parts = {name: shape for name, shape in parts.items() if name not in owners}
        unintended = _hits(bore, other_parts)
        start = cq.Vector(*axis["origin_global_xyz_mm"])
        direction = cq.Vector(*axis["direction_global_xyz"])
        end = start + direction * axis["wood_grip_mm"]
        records.append(
            {
                **axis,
                "distance_screen": _axis_screen_metadata(axis),
                "receiver_volume_fraction": {
                    name: round(value, 9) for name, value in received.items()
                },
                "intended_receivers_complete": abs(sum(received.values()) - 1.0)
                < 1e-7
                and all(value > 0.0 for value in received.values()),
                "unintended_wood_axis_intersections_mm3": unintended,
                "head_washer_support_fraction": round(
                    _washer_support(parts[owners[0]], start, direction), 9
                ),
                "nut_washer_support_fraction": round(
                    _washer_support(parts[owners[1]], end, -direction), 9
                ),
                "nominal_underhead_length_screen_mm": round(
                    axis["wood_grip_mm"]
                    + 2 * WASHER_THICKNESS_MM
                    + NUT_HEIGHT_MM
                    + THREAD_PAST_NUT_MM,
                    6,
                ),
            }
        )
    pair_hits = {}
    flat_shapes = {
        f"{axis_id}/{role}": shape
        for axis_id, roles in all_shapes.items()
        for role, shape in roles.items()
        if role in {"bore", "shaft", "head", "nut", "head_washer", "nut_washer"}
    }
    names = list(flat_shapes)
    for index, name in enumerate(names):
        for other in names[index + 1 :]:
            first_axis = name.split("/", 1)[0]
            second_axis = other.split("/", 1)[0]
            if first_axis == second_axis:
                continue
            volume = _volume(flat_shapes[name], flat_shapes[other])
            if volume > GEOMETRY_TOL_MM3:
                pair_hits[f"{name}/{other}"] = round(volume, 6)
    return records, {"new_fastener_component_pair_hits_mm3": pair_hits}


def _axis_relief_distance_records(
    axes: list[dict], relief: cq.Shape
) -> list[dict]:
    records = []
    for axis in axes:
        if not axis["axis_id"].startswith("center_principal_"):
            continue
        side_relief = relief if axis["side"] == "right" else _mirror_x(relief)
        start = cq.Vector(*axis["origin_global_xyz_mm"])
        direction = cq.Vector(*axis["direction_global_xyz"])
        end = start + direction * axis["wood_grip_mm"]
        centerline = cq.Edge.makeLine(start, end)
        shapes = _fastener_shapes(axis)
        roles = ("shaft", "head_washer", "head", "nut_washer", "nut")
        records.append(
            {
                "axis_id": axis["axis_id"],
                "axis_centerline_min_distance_to_removed_wedge_mm": round(
                    centerline.distance(side_relief), 6
                ),
                "installed_component_min_distance_to_removed_wedge_mm": {
                    role: round(shapes[role].distance(side_relief), 6)
                    for role in roles
                },
                "tool_envelopes_included": False,
            }
        )
    return records


def _inventory_axis_shape(row: dict, *, fixed_screw: bool) -> cq.Shape:
    direction = cq.Vector(*row["axis_global_xyz"]).normalized()
    length = row["shop_purchased_length_mm"] if fixed_screw else row["source_occupied_length_mm"]
    diameter = row["source_occupied_diameter_mm"]
    return cq.Solid.makeCylinder(
        diameter / 2,
        length,
        cq.Vector(*row["origin_global_xyz_mm"]),
        direction,
    )


def _collision_map(
    candidates: dict[str, cq.Shape], targets: dict[str, cq.Shape]
) -> dict[str, dict[str, float]]:
    return {
        candidate_id: _hits(shape, targets)
        for candidate_id, shape in candidates.items()
    }


def _bbox_distance(first: cq.Shape, second: cq.Shape) -> float:
    a, b = first.BoundingBox(), second.BoundingBox()
    dx = max(0.0, a.xmin - b.xmax, b.xmin - a.xmax)
    dy = max(0.0, a.ymin - b.ymax, b.ymin - a.ymax)
    dz = max(0.0, a.zmin - b.zmax, b.zmin - a.zmax)
    return math.sqrt(dx * dx + dy * dy + dz * dz)


def _source_wire_clearance(
    candidates: dict[str, cq.Shape], wires: dict[str, cq.Shape]
) -> dict:
    """Prove the 2 mm source-shape wire gap or return a fail-closed result."""
    result = {}
    for candidate_id, candidate in candidates.items():
        exact_near_pairs = {}
        pruned_bbox_lower_bounds = []
        violations = {}
        for wire_id, wire in wires.items():
            bbox_gap = _bbox_distance(candidate, wire)
            if bbox_gap >= MIN_SOURCE_WIRE_CLEARANCE_MM:
                pruned_bbox_lower_bounds.append(bbox_gap)
                continue
            exact_gap = candidate.distance(wire)
            exact_near_pairs[wire_id] = exact_gap
            if exact_gap < MIN_SOURCE_WIRE_CLEARANCE_MM:
                violations[wire_id] = round(exact_gap, 6)

        lower_bounds = pruned_bbox_lower_bounds + list(exact_near_pairs.values())
        minimum_proven_gap = min(lower_bounds) if lower_bounds else None
        passed = bool(wires) and not violations and minimum_proven_gap is not None
        result[candidate_id] = {
            "required_clearance_mm": MIN_SOURCE_WIRE_CLEARANCE_MM,
            "minimum_proven_clearance_lower_bound_mm": round(minimum_proven_gap, 6)
            if minimum_proven_gap is not None
            else None,
            "near_pairs_exact_distance_mm": {
                wire_id: round(distance, 6)
                for wire_id, distance in exact_near_pairs.items()
            },
            "far_pairs_bbox_lower_bound_count": len(pruned_bbox_lower_bounds),
            "far_pairs_minimum_bbox_lower_bound_mm": round(
                min(pruned_bbox_lower_bounds), 6
            )
            if pruned_bbox_lower_bounds
            else None,
            "below_required_clearance_mm": violations,
            "distance_gate_passed": passed,
        }
    return result


def _has_hits(value) -> bool:
    if isinstance(value, dict):
        return any(_has_hits(item) for item in value.values())
    if isinstance(value, (list, tuple)):
        return any(_has_hits(item) for item in value)
    return bool(value)


def _source_frame_bolt_records(model, rows: list[dict]) -> tuple[list[dict], dict[str, cq.Shape]]:
    source_rows = {row["axis_id"]: row for row in rows}
    actual = {connection.name: connection for connection in model.connections() if connection.kind == "bolt"}
    if set(actual) != set(source_rows):
        raise ValueError("The 12 retained source frame-bolt identities changed")
    shapes = {}
    records = []
    for bolt_id, row in source_rows.items():
        connection = actual[bolt_id]
        axis = _inventory_axis_shape(row, fixed_screw=False)
        components = connection.components()
        for index, component in enumerate(components, 1):
            shapes[f"{bolt_id}/installed_component_{index}"] = component
        shapes[f"{bolt_id}/source_occupied_axis"] = axis
        records.append(
            {
                "axis_id": bolt_id,
                "members": row["members"],
                "origin_global_xyz_mm": row["origin_global_xyz_mm"],
                "axis_global_xyz": row["axis_global_xyz"],
                "source_occupied_length_mm": row["source_occupied_length_mm"],
                "source_occupied_diameter_mm": row["source_occupied_diameter_mm"],
                "candidate_recheck_status": row["candidate_recheck_status"],
                "installed_component_count": len(components),
            }
        )
    return records, shapes


def _active_backer_components(
    bolts: dict[str, cq.Shape],
    stacks: dict[str, dict[str, cq.Shape]],
    tools: dict[str, dict[str, cq.Shape]],
) -> tuple[dict[str, cq.Shape], dict[str, cq.Shape]]:
    installed = {}
    tool_envelopes = {}
    for bolt_id, shape in bolts.items():
        installed[f"{bolt_id}/shaft"] = shape
    for bolt_id, components in stacks.items():
        for role, shape in components.items():
            installed[f"{bolt_id}/{role}"] = shape
    for bolt_id, components in tools.items():
        for role, shape in components.items():
            tool_envelopes[f"{bolt_id}/{role}"] = shape
    return installed, tool_envelopes


def _source_bindings() -> dict[str, str]:
    wiring_reference = ROOT / "docs/round-service-wiring-reference.json"
    wiring_reference_data = json.loads(wiring_reference.read_text())
    route_reference = ROOT / wiring_reference_data["route_reference"]
    paths = (
        SOURCE_INVENTORY,
        ROOT / "mini_moonboard/floor_flush_width.py",
        ROOT / "mini_moonboard/compact_floor_flush_frame.py",
        ROOT / "mini_moonboard/wood_joint_panel_machining.py",
        ROOT / "mini_moonboard/round_service_wiring.py",
        ROOT / "mini_moonboard/hold_tnut_reinforcement.py",
        wiring_reference,
        route_reference,
        ROOT / "scripts/wood_joints_wj05_center_backer_transfer_probe.py",
        ROOT / "scripts/owner_layout_protected.py",
        Path(__file__),
    )
    return {
        str(path.relative_to(ROOT)): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in paths
    }


def _fixed_axis_member_counts(rows: list[dict]) -> dict[str, int]:
    counts = {"panel_axes": 0, "kicker_axes": 0}
    for row in rows:
        panel_member = row.get("panel_member")
        if panel_member in FIXED_PANEL_MEMBERS:
            counts["panel_axes"] += 1
        elif panel_member in FIXED_KICKER_MEMBERS:
            counts["kicker_axes"] += 1
        else:
            raise ValueError(f"Unrecognized fixed panel/kicker member: {panel_member!r}")
    if sum(counts.values()) != len(rows):
        raise ValueError("Fixed panel/kicker member counts do not sum to source records")
    return counts


def _bolt_spacing(axis_rows: list[dict]) -> dict[str, dict[str, float]]:
    groups: dict[str, list[dict]] = {}
    for row in axis_rows:
        groups.setdefault(row["connection_group"], []).append(row)
    result = {}
    for interface, rows in groups.items():
        centers = [cq.Vector(*row["origin_global_xyz_mm"]) for row in rows]
        distances = [
            (first - second).Length
            for index, first in enumerate(centers)
            for second in centers[index + 1 :]
        ]
        result[interface] = {
            "minimum_center_spacing_mm": round(min(distances), 6)
            if distances
            else 0.0,
            "minimum_center_spacing_multiple_D": round(min(distances) / BOLT_DIAMETER_MM, 6)
            if distances
            else 0.0,
        }
    return result


def build_report() -> dict:
    inventory = json.loads(SOURCE_INVENTORY.read_text())
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
    # The shared kerf adapter relocates some right-panel bores with their
    # panels. Restore only the source-defined fixed panel datums in this local
    # prototype map; active producers and source inventory remain untouched.
    current_model_parts = model.parts()
    panel_replacements = candidate_panel_replacements(
        model,
        current_parts=current_model_parts,
        uncut_parts=model.uncut_wood_parts(),
    )
    for name, part in panel_replacements.items():
        source_parts[name] = part.shape
    parts = _candidate_parts(source_parts)
    candidates = {
        name: shape
        for name, shape in parts.items()
        if name.startswith(("center_post_cleat_", "center_principal_cleat_"))
    }
    axes = [
        axis
        for side in SIDES
        for axis in (_upper_fastener_axes(side) + _lower_fastener_axes(side))
    ]
    axis_records, fastener_pair_checks = _axis_checks(axes, parts)
    finished_parts = _finished_trial_parts(axes, parts)

    fixed_rows = inventory["fixed_panel_kicker_screws"]
    if len(fixed_rows) != 66 or len({row["axis_id"] for row in fixed_rows}) != 66:
        raise ValueError("Expected the unchanged 66 fixed panel/kicker axes")
    fixed_member_counts = _fixed_axis_member_counts(fixed_rows)
    fixed_shapes = {
        row["axis_id"]: _inventory_axis_shape(row, fixed_screw=True)
        for row in fixed_rows
    }

    frame_records, frame_shapes = _source_frame_bolt_records(
        model, inventory["starting_frame_bolts"]
    )
    backer_installed_shapes, backer_tool_shapes = _active_backer_components(
        backer_bolts, backer_stacks, backer_tools
    )
    protected = protected_inventory()
    protected_shapes = {
        f"{family}/{name}": shape
        for family, solids in protected["solids"].items()
        for name, shape in solids.items()
    }
    wire_shapes = protected["solids"].get("wires", {})
    upper_candidate_shapes = {
        name: shape
        for name, shape in candidates.items()
        if name.startswith("center_principal_cleat_")
    }
    source_wire_clearance = _source_wire_clearance(
        upper_candidate_shapes, wire_shapes
    )
    wire_clearance_conflicts = {
        name: record["below_required_clearance_mm"]
        for name, record in source_wire_clearance.items()
        if record["below_required_clearance_mm"]
    }
    source_wire_gap_passed = bool(source_wire_clearance) and all(
        record["distance_gate_passed"] for record in source_wire_clearance.values()
    )
    wire_relief_shape = _upper_cleat_wire_relief()
    upper_unrelieved_shape = _upper_cleat_right(apply_wire_relief=False)
    wire_relief_removed_volume = upper_unrelieved_shape.Volume() - candidates[
        "center_principal_cleat_right"
    ].Volume()
    wire_relief_polygon_tn = [
        [UPPER_WIRE_RELIEF_T_MM, UPPER_CLEAT_N_MM[0]],
        [
            UPPER_CLEAT_GRAIN_LENGTH_MM
            - math.cos(ANGLE_RAD) / math.sin(ANGLE_RAD) * UPPER_CLEAT_N_MM[0],
            UPPER_CLEAT_N_MM[0],
        ],
        [UPPER_WIRE_RELIEF_T_MM, UPPER_WIRE_RELIEF_N_MAX_MM],
    ]
    axis_to_relief_clearances = _axis_relief_distance_records(
        axes, wire_relief_shape
    )

    new_fastener_shapes = {
        f"{axis['axis_id']}/{role}": shape
        for axis in axes
        for role, shape in _fastener_shapes(axis).items()
    }
    bore_shapes = {
        name: shape for name, shape in new_fastener_shapes.items() if name.endswith("/bore")
    }
    physical_hardware = {
        name: shape
        for name, shape in new_fastener_shapes.items()
        if not name.endswith(("/bore", "/head_tool", "/nut_tool"))
    }
    tool_shapes = {
        name: shape
        for name, shape in new_fastener_shapes.items()
        if name.endswith(("/head_tool", "/nut_tool"))
    }

    candidate_wood_hits = _collision_map(
        candidates,
        {
            name: shape
            for name, shape in parts.items()
            if name not in candidates
        },
    )
    candidate_candidate_hits = {}
    names = list(candidates)
    for index, first in enumerate(names):
        for second in names[index + 1 :]:
            volume = _volume(candidates[first], candidates[second])
            if volume > GEOMETRY_TOL_MM3:
                candidate_candidate_hits[f"{first}/{second}"] = round(volume, 6)

    fixed_hits = _collision_map(candidates, fixed_shapes)
    frame_axis_hits = _collision_map(candidates, {
        name: shape for name, shape in frame_shapes.items() if name.endswith("/source_occupied_axis")
    })
    frame_component_hits = _collision_map(candidates, {
        name: shape for name, shape in frame_shapes.items() if not name.endswith("/source_occupied_axis")
    })
    backer_installed_hits = _collision_map(candidates, backer_installed_shapes)
    backer_tool_hits = _collision_map(candidates, backer_tool_shapes)
    service_hits = _collision_map(candidates, protected_shapes)
    axes_by_id = {axis["axis_id"]: axis for axis in axes}
    tool_wood_hits = {}
    for tool_id, shape in tool_shapes.items():
        axis_id, tool_role = tool_id.rsplit("/", 1)
        intended_owner = (
            axes_by_id[axis_id]["intended_receivers"][0]
            if tool_role == "head_tool"
            else axes_by_id[axis_id]["intended_receivers"][1]
        )
        targets = {
            name: target
            for name, target in parts.items()
            if name != intended_owner
        }
        hits = _hits(shape, targets)
        if hits:
            tool_wood_hits[tool_id] = hits
    frame_axis_shapes = {
        name: shape
        for name, shape in frame_shapes.items()
        if name.endswith("/source_occupied_axis")
    }
    tool_backer_installed_hits = _collision_map(tool_shapes, backer_installed_shapes)
    tool_backer_tool_hits = _collision_map(tool_shapes, backer_tool_shapes)
    bore_fixed_hits = _collision_map(bore_shapes, fixed_shapes)
    bore_retained_hits = _collision_map(bore_shapes, frame_axis_shapes)
    bore_backer_hits = _collision_map(bore_shapes, backer_installed_shapes)
    bore_backer_tool_hits = _collision_map(bore_shapes, backer_tool_shapes)
    hardware_service_hits = _collision_map(physical_hardware, protected_shapes)
    hardware_fixed_hits = _collision_map(physical_hardware, fixed_shapes)
    hardware_retained_hits = _collision_map(physical_hardware, frame_axis_shapes)
    hardware_backer_hits = _collision_map(physical_hardware, backer_installed_shapes)
    hardware_backer_tool_hits = _collision_map(physical_hardware, backer_tool_shapes)
    tool_fixed_hits = _collision_map(tool_shapes, fixed_shapes)
    tool_retained_hits = _collision_map(tool_shapes, frame_axis_shapes)
    tool_service_hits = _collision_map(tool_shapes, protected_shapes)
    installed_hardware_wood_hits = _collision_map(
        physical_hardware,
        finished_parts,
    )

    fixed_identity = [
        {
            "axis_id": row["axis_id"],
            "origin_global_xyz_mm": row["origin_global_xyz_mm"],
            "axis_global_xyz": row["axis_global_xyz"],
            "shop_purchased_length_mm": row["shop_purchased_length_mm"],
            "candidate_finished_receiver_member": row[
                "candidate_finished_receiver_member"
            ],
        }
        for row in fixed_rows
    ]
    fixed_identity_sha256 = hashlib.sha256(
        json.dumps(fixed_identity, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()

    upper_bounds = _bounds(candidates["center_principal_cleat_right"])
    lower_bounds = _bounds(candidates["center_post_cleat_right"])
    y0, z0 = UPPER_CLEAT_ORIGIN_YZ_MM
    z_top = z0 + math.sin(ANGLE_RAD) * UPPER_CLEAT_GRAIN_LENGTH_MM
    y_bottom_min = y0 - UPPER_CLEAT_N_MM[1] / math.sin(ANGLE_RAD)
    y_bottom_max = y0 - UPPER_CLEAT_N_MM[0] / math.sin(ANGLE_RAD)
    header_overlap_y = max(
        0.0,
        min(y_bottom_max, -36.0) - max(y_bottom_min, -175.7),
    )
    relief_contact_area = wire_relief_removed_volume / (
        UPPER_CLEAT_X_RIGHT_MM[1] - UPPER_CLEAT_X_RIGHT_MM[0]
    )
    principal_side_contact_area = (
        (UPPER_CLEAT_N_MM[1] - UPPER_CLEAT_N_MM[0])
        * UPPER_CLEAT_GRAIN_LENGTH_MM
        - relief_contact_area
    )
    header_axis_records = [
        row
        for row in axis_records
        if row["axis_id"].startswith("center_principal_header_")
    ]
    header_4d_min_distance = min(
        min(row["distance_screen"]["cleat_x_edge_distances_mm"])
        for row in header_axis_records
    )
    header_4d_min_distance = min(
        header_4d_min_distance,
        *(
            min(row["distance_screen"]["header_y_edge_distances_mm"])
            for row in header_axis_records
        ),
        *(
            row["distance_screen"]["cleat_axis_path_min_local_N_edge_distance_mm"]
            for row in header_axis_records
        ),
    )

    geometry_conflicts = {
        "new_cleat_solid_overlaps_existing_wood_mm3": candidate_wood_hits,
        "left_right_cleat_solid_overlaps_mm3": candidate_candidate_hits,
        "candidate_cleats_hit_fixed_66_axes_mm3": fixed_hits,
        "candidate_cleats_hit_retained_12_bolt_axes_mm3": frame_axis_hits,
        "candidate_cleats_hit_retained_12_installed_hardware_mm3": frame_component_hits,
        "candidate_cleats_hit_active_wj05_backer_installed_parts_mm3": backer_installed_hits,
        "candidate_cleats_hit_active_wj05_backer_tool_envelopes_mm3": backer_tool_hits,
        "candidate_cleats_hit_protected_services_mm3": service_hits,
        "upper_cleat_source_wire_clearance_below_2mm": wire_clearance_conflicts,
        "new_tool_access_vs_existing_wood_mm3": tool_wood_hits,
        "new_tool_access_vs_active_backer_installed_parts_mm3": tool_backer_installed_hits,
        "new_tool_access_vs_active_backer_tool_envelopes_mm3": tool_backer_tool_hits,
        "proposed_bores_vs_fixed_66_axes_mm3": bore_fixed_hits,
        "proposed_bores_vs_retained_12_axes_mm3": bore_retained_hits,
        "proposed_bores_vs_active_backer_installed_parts_mm3": bore_backer_hits,
        "proposed_bores_vs_active_backer_tool_envelopes_mm3": bore_backer_tool_hits,
        "installed_fastener_parts_vs_fixed_66_axes_mm3": hardware_fixed_hits,
        "installed_fastener_parts_vs_retained_12_axes_mm3": hardware_retained_hits,
        "installed_fastener_parts_vs_active_backer_installed_parts_mm3": hardware_backer_hits,
        "installed_fastener_parts_vs_active_backer_tool_envelopes_mm3": hardware_backer_tool_hits,
        "installed_fastener_parts_vs_protected_services_mm3": hardware_service_hits,
        "new_tool_access_vs_fixed_66_axes_mm3": tool_fixed_hits,
        "new_tool_access_vs_retained_12_axes_mm3": tool_retained_hits,
        "new_tool_access_vs_protected_services_mm3": tool_service_hits,
        "installed_new_fastener_parts_vs_finished_wood_mm3": installed_hardware_wood_hits,
        **fastener_pair_checks,
    }
    geometry_clear = (
        not _has_hits(geometry_conflicts)
        and source_wire_gap_passed
        and all(
            all(
                abs(fraction - 1.0) < 1e-7
                for fraction in row["receiver_volume_fraction"].values()
            )
            and row["head_washer_support_fraction"] >= 1.0 - 1e-7
            and row["nut_washer_support_fraction"] >= 1.0 - 1e-7
            and not row["unintended_wood_axis_intersections_mm3"]
            for row in axis_records
        )
    )

    return {
        "schema": "wood_joint_wj05_center_node_probe/v1",
        "trial_id": TRIAL_ID,
        "candidate": "compact-floor-flush-wood-joints-development",
        "scope": "one-side source-bound center-node geometry fit comparison with mirror checks",
        "status": "nominal_geometry_clear_diagnostic" if geometry_clear else "blocked_nominal_geometry_diagnostic",
        "source_fingerprints_sha256": _source_bindings(),
        "fixed_panel_kicker_axis_identity": {
            "count": len(fixed_rows),
            "unique_count": len({row["axis_id"] for row in fixed_rows}),
            **fixed_member_counts,
            "axes_moved": 0,
            "identity_sha256": fixed_identity_sha256,
            "all_source_axis_ids_retained": len(fixed_shapes) == 66,
        },
        "retained_starting_frame_bolts": {
            "count": len(frame_records),
            "axis_ids": [row["axis_id"] for row in frame_records],
            "records": frame_records,
            "candidate_recheck_status": "required_for_every_retained_bolt",
        },
        "candidate_connectors": {
            "right_lower_post_header_cleat": {
                "bounds_xyz_mm": lower_bounds,
                "stock_cross_section_mm": [88.9, 88.9],
                "grain_axis_global": list(LOWER_CLEAT_GRAIN_AXIS),
                "nominal_grain_length_mm": 128.9,
                "contact_areas_mm2": {
                    "moved_right_post": round(88.9 * 128.9, 3),
                    "base_header": round(88.9 * 88.9, 3),
                },
                "interfaces": [
                    "base_post_center_right / center_post_cleat_right",
                    "center_post_cleat_right / base_header",
                ],
            },
            "right_upper_principal_header_cleat": {
                "bounds_xyz_mm": upper_bounds,
                "nominal_stock": "ordinary full-section 4x4 solid timber, grain parallel to center principal T",
                "stock_blank_local_X_N_T_mm": [
                    88.9,
                    UPPER_CLEAT_N_MM[1] - UPPER_CLEAT_N_MM[0],
                    round(UPPER_CLEAT_RAW_GRAIN_LENGTH_MM, 6),
                ],
                "finished_local_X_N_grain_length_mm": [
                    88.9,
                    UPPER_CLEAT_N_MM[1] - UPPER_CLEAT_N_MM[0],
                    UPPER_CLEAT_GRAIN_LENGTH_MM,
                ],
                "grain_axis_global": [round(v, 9) for v in GRAIN_T],
                "finished_local_N_interval_mm": list(UPPER_CLEAT_N_MM),
                "horizontal_bottom_seat_z_mm": 277.0,
                "horizontal_top_seat_z_mm": round(z_top, 6),
                "principal_side_contact_area_mm2": round(principal_side_contact_area, 3),
                "principal_side_contact_area_removed_by_wire_relief_mm2": round(
                    relief_contact_area, 3
                ),
                "header_top_contact_area_mm2": round(88.9 * header_overlap_y, 3),
                "header_overlap_y_interval_mm": [
                    round(max(y_bottom_min, -175.7), 6),
                    round(min(y_bottom_max, -36.0), 6),
                ],
                "interfaces": [
                    "base_principal_center_right / center_principal_cleat_right",
                    "center_principal_cleat_right / base_header",
                ],
                "header_bolt_minimum_conditional_4D_margin_mm": round(
                    header_4d_min_distance - FOUR_D_MM, 6
                ),
                "wire_relief": {
                    "local_axes": "T along grain; N cross grain; coordinates relative to upper-cleat origin",
                    "rule": "remove only the triangular material with T >= 30 mm; retain material outside this local N interval",
                    "triangle_TN_vertices_mm": wire_relief_polygon_tn,
                    "through_global_X_mm": list(UPPER_CLEAT_X_RIGHT_MM),
                    "removed_volume_mm3": round(wire_relief_removed_volume, 6),
                    "source_wire_clearance_gate_mm": MIN_SOURCE_WIRE_CLEARANCE_MM,
                    "physical_harness_and_install_sweep_status": "not modeled or cleared by display-wire geometry",
                },
            },
            "mirrored_left_geometry_checked": True,
            "one_piece_C_saddle": {
                "status": "not_modeled_stock_path_not_established",
                "reason": "A continuous one-piece rear saddle needs a stock envelope spanning separated principal and moved-post interfaces; the obvious backstrap exceeds ordinary 4x6 width and front-face through-bolts would need a separate panel-plane/tool-access design. No custom or built-up stock is assumed.",
            },
        },
        "provisional_fastener_axes": axis_records,
        "upper_relief_installed_hardware_clearances": axis_to_relief_clearances,
        "upper_relief_source_wire_clearance": source_wire_clearance,
        "minimum_pair_spacing_by_interface": _bolt_spacing(axes),
        "geometry_conflicts": geometry_conflicts,
        "assembly_sequence": {
            "candidate_connector_transport": "two separate removable timber cleats per side; keep each cleat and its bolts removable",
            "tool_access_basis": f"{TOOL_DIAMETER_MM:g} mm diameter by {TOOL_LENGTH_MM:g} mm axial cylinder is a clearance proxy, not a wrench swing or selected product",
            "floor_sequence": "Preassemble and torque accessible center connections on stable raised supports before setting the frame at the floor; verify the active backer bottom-seat insertion sweep and real tool swing first. Nominal model does not qualify supports, clearances, or a floor anchor.",
        },
        "conclusion": {
            "geometry_fit_clear": geometry_clear,
            "complete_center_load_path": False,
            "capacity_assigned": False,
            "wood_grade_and_condition_observed": False,
            "hardware_sku_selected": False,
            "engineering_or_fabrication_release": False,
            "unimplemented_duties": [
                "clip_split_header_center_left",
                "clip_split_header_center_right",
                "clip_split_base_center_left",
                "clip_split_base_center_right",
            ],
            "remaining_gates": [
                "source-bound fit, receiver, bore, end-stack, service, fixed-axis and tool clearances",
                "fresh per-fastener actions and contact/bearing model for the complete node",
                "parallel-grain bolt and perpendicular-to-grain member checks with applicable edge/spacing categories",
                "bolt SKU, delivered thread transition, washer/nut fit, installation access and procurement",
                "member-specific cuts and inspected material; no inherited WJ-03/WJ-04 capacity",
            ],
        },
        "release_flags": dict(RELEASE_FLAGS),
    }


def main() -> None:
    print(json.dumps(build_report(), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
