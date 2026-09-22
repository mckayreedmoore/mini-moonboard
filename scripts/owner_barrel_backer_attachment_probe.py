"""Detached nominal backer/header cross-dowel placement screen; no release."""

import json
import math

import cadquery as cq

from scripts import owner_layout_protected as protected
from scripts.center_posts_outward_owner_layout import build_layout as post_layout
from scripts.export_owner_barrel_scene import build_viewer_assembly
from scripts.owner_barrel_native_connector_inventory import build_inventory

SCHEMA = "owner_barrel_backer_attachment_probe/v1"
BACKERS = ("inner_kicker_backer_left", "inner_kicker_backer_right")
HEADER = "base_header"
ROWS = (("rear", -35.0, 20.0, -100.0), ("front", -20.0, 35.0, -65.0))
SHAFT_DIAMETER_MM = 6.35
NOMINAL_BOLT_LENGTH_MM = 88.9  # 3 1/2 in trial, not a selected store item.
MACHINE_BORE_DIAMETER_MM = 7.5
BARREL_DIAMETER_MM = 10.0076
BARREL_LENGTH_MM = 16.002
WASHER_DIAMETER_MM = 22.0
WASHER_THICKNESS_MM = 2.0
HEAD_DIAMETER_MM = 11.0
HEAD_HEIGHT_MM = 4.0
TOOL_DIAMETER_MM = 20.0
TOOL_LENGTH_MM = 30.0
BORE_TIP_ALLOWANCE_MM = 2.0
HIT_TOL_MM3 = protected.HIT_TOL_MM3


def _cylinder(point, direction, length, diameter):
    return cq.Solid.makeCylinder(
        diameter / 2, length, cq.Vector(*point), cq.Vector(*direction)
    )


def _hits(shape, targets):
    return {
        name: round(volume, 6)
        for name, target in targets.items()
        if (volume := protected._volume(shape, target)) > HIT_TOL_MM3
    }


def _bounds(shape):
    box = shape.BoundingBox()
    return [
        round(value, 6)
        for value in (box.xmin, box.xmax, box.ymin, box.ymax, box.zmin, box.zmax)
    ]


def _existing_hardware(assembly):
    solids = {f"barrel/{name}": shape for name, shape in assembly["barrels"].items()}
    solids.update(
        {
            f"bolt/{name}/{role}": shape
            for name, stack in assembly["stacks"].items()
            for role, shape in stack.items()
        }
    )
    return solids


def probe(assembly=None):
    """Screen two diagonal bolt/barrel pairs per existing backer, unchanged CAD."""
    assembly = build_viewer_assembly() if assembly is None else assembly
    placement = post_layout()
    source = build_inventory(assembly=assembly, placement=placement)
    fixed = protected.inventory()
    if (
        set(BACKERS) - set(assembly["wood"])
        or source["viewer_pose"]["outer_header_forward_y_mm"] != -85.0
        or len(source["fixed_panel_screws"]) != 66
        or len(source["retained_frame_bolts"]) != 12
        or fixed["counts"]["panel_screws"] != 66
        or fixed["counts"]["frame_bolts"] != 12
        or set(fixed["solids"]["panel_screws"]) != set(source["fixed_panel_screws"])
        or set(fixed["solids"]["frame_bolts"]) != set(source["retained_frame_bolts"])
    ):
        raise ValueError("Current viewer backers or protected 66/12 inventory changed")
    wood = assembly["wood"]
    header_box = wood[HEADER].BoundingBox()
    if not math.isclose(header_box.zmax, 277.0, abs_tol=1e-5):
        raise ValueError("Current header top changed")
    existing = _existing_hardware(assembly)
    candidates = {}
    solids = {}
    for side in ("left", "right"):
        backer_name = f"inner_kicker_backer_{side}"
        backer = wood[backer_name]
        box = backer.BoundingBox()
        if (
            not math.isclose(box.zmax, header_box.zmin, abs_tol=1e-5)
            or not math.isclose(box.zmin, 0.0, abs_tol=1e-5)
            or not math.isclose(box.ymin, -124.9, abs_tol=1e-5)
            or not math.isclose(box.ymax, -36.0, abs_tol=1e-5)
            or not math.isclose(box.xlen, 88.9, abs_tol=1e-5)
        ):
            raise ValueError(f"{backer_name}: source timber contact changed")
        for label, left_x, right_x, y in ROWS:
            x = left_x if side == "left" else right_x
            if (
                x - box.xmin <= WASHER_DIAMETER_MM / 2
                or box.xmax - x <= WASHER_DIAMETER_MM / 2
            ):
                raise ValueError(
                    f"{backer_name}: trial washer exits nominal backer width"
                )
            name = f"{backer_name}/{label}"
            # The assumed barrel thread axis is at z=200; the rear-entry bore
            # crosses it in Y. Neither assumption is a drilling dimension.
            seat_z, axis_z = header_box.zmax, 200.0
            barrel_start_y = y - BARREL_LENGTH_MM / 2
            barrel = _cylinder(
                (x, barrel_start_y, axis_z),
                (0, 1, 0),
                BARREL_LENGTH_MM,
                BARREL_DIAMETER_MM,
            )
            cross_bore = _cylinder(
                (x, box.ymin, axis_z),
                (0, 1, 0),
                y + BARREL_LENGTH_MM / 2 - box.ymin,
                BARREL_DIAMETER_MM,
            )
            shaft_start_z = seat_z + WASHER_THICKNESS_MM
            nominal_tip_z = shaft_start_z - NOMINAL_BOLT_LENGTH_MM
            modeled_barrel_far_wall_z = axis_z - BARREL_DIAMETER_MM / 2
            modeled_bore_end_z = seat_z - NOMINAL_BOLT_LENGTH_MM - BORE_TIP_ALLOWANCE_MM
            shaft = _cylinder(
                (x, y, shaft_start_z),
                (0, 0, -1),
                NOMINAL_BOLT_LENGTH_MM,
                SHAFT_DIAMETER_MM,
            )
            machine_bore = _cylinder(
                (x, y, seat_z),
                (0, 0, -1),
                NOMINAL_BOLT_LENGTH_MM + BORE_TIP_ALLOWANCE_MM,
                MACHINE_BORE_DIAMETER_MM,
            )
            washer = _cylinder(
                (x, y, seat_z),
                (0, 0, 1),
                WASHER_THICKNESS_MM,
                WASHER_DIAMETER_MM,
            )
            head = _cylinder(
                (x, y, shaft_start_z),
                (0, 0, 1),
                HEAD_HEIGHT_MM,
                HEAD_DIAMETER_MM,
            )
            driver = _cylinder(
                (x, y, shaft_start_z + HEAD_HEIGHT_MM),
                (0, 0, 1),
                TOOL_LENGTH_MM,
                TOOL_DIAMETER_MM,
            )
            barrel_driver = _cylinder(
                (x, box.ymin, axis_z),
                (0, -1, 0),
                TOOL_LENGTH_MM,
                TOOL_DIAMETER_MM,
            )
            shapes = {
                "shaft": shaft,
                "machine_bore": machine_bore,
                "barrel": barrel,
                "cross_bore": cross_bore,
                "washer": washer,
                "head": head,
                "bolt_driver": driver,
                "barrel_driver": barrel_driver,
            }
            solids[name] = shapes
            unintended_wood = {
                key: value
                for key, value in wood.items()
                if key not in {HEADER, backer_name}
            }
            checks = {}
            for role, shape in shapes.items():
                checks[role] = {
                    "unrelated_wood_mm3": _hits(shape, unintended_wood),
                    "protected_mm3": protected.hits({role: shape}, fixed)[role],
                    "existing_viewer_hardware_mm3": _hits(shape, existing),
                }
            entry = {
                "backer": backer_name,
                "host": HEADER,
                "point_xy_mm": [round(x, 6), y],
                "barrel_axis_xyz_mm": [round(x, 6), y, axis_z],
                "backer_bounds_xyz_mm": _bounds(backer),
                "seat_to_assumed_axis_mm": seat_z - axis_z,
                "nominal_shaft_reach_past_axis_mm": round(
                    NOMINAL_BOLT_LENGTH_MM - WASHER_THICKNESS_MM - (seat_z - axis_z),
                    6,
                ),
                "nominal_tip_to_backer_bottom_mm": round(nominal_tip_z - box.zmin, 6),
                "nominal_tip_z_mm": round(nominal_tip_z, 6),
                "modeled_barrel_far_wall_z_mm": round(modeled_barrel_far_wall_z, 6),
                "nominal_tip_past_modeled_barrel_far_wall_mm": round(
                    modeled_barrel_far_wall_z - nominal_tip_z, 6
                ),
                "modeled_bore_end_z_mm": round(modeled_bore_end_z, 6),
                "modeled_bore_depth_past_nominal_tip_mm": round(
                    nominal_tip_z - modeled_bore_end_z, 6
                ),
                "barrel_bore_from_rear_mm": round(
                    y + BARREL_LENGTH_MM / 2 - box.ymin, 6
                ),
                "machine_bore_depth_from_header_top_mm": (
                    NOMINAL_BOLT_LENGTH_MM + BORE_TIP_ALLOWANCE_MM
                ),
                "nominal_margin_to_backer_x_edges_mm": round(
                    min(x - box.xmin, box.xmax - x), 6
                ),
                "nominal_margin_to_backer_y_edges_mm": round(
                    min(y - box.ymin, box.ymax - y), 6
                ),
                "intended_header_bore_mm3": round(
                    protected._volume(machine_bore, wood[HEADER]), 6
                ),
                "intended_backer_bore_mm3": round(
                    protected._volume(machine_bore, backer), 6
                ),
                "barrel_body_inside_backer_mm3": round(
                    protected._volume(barrel, backer), 6
                ),
                "barrel_body_mm3": round(barrel.Volume(), 6),
                "cross_bore_meets_machine_bore_mm3": round(
                    protected._volume(cross_bore, machine_bore), 6
                ),
                "screen": checks,
            }
            candidates[name] = entry
    mutual = {}
    for first, first_shapes in solids.items():
        for second, second_shapes in solids.items():
            if first >= second:
                continue
            mutual[f"{first}|{second}"] = {
                f"{role_a}|{role_b}": round(volume, 6)
                for role_a, shape_a in first_shapes.items()
                for role_b, shape_b in second_shapes.items()
                # Driver cylinders are used sequentially, not occupied together.
                if not (role_a.endswith("driver") and role_b.endswith("driver"))
                if (volume := protected._volume(shape_a, shape_b)) > HIT_TOL_MM3
            }
    obstacles = {
        name: {
            role: checks
            for role, checks in row["screen"].items()
            if any(checks.values())
        }
        for name, row in candidates.items()
    }
    return {
        "schema": SCHEMA,
        "status": "detached_geometry_screen_only",
        "viewer_pose": source["viewer_pose"],
        "backers": {name: _bounds(wood[name]) for name in BACKERS},
        "header_bounds_xyz_mm": _bounds(wood[HEADER]),
        "fixed_inventory_counts": fixed["counts"],
        "candidate_hardware": {
            "per_backer_bolt_barrel_pairs": 2,
            "trial_nominal_bolt_length_mm": NOMINAL_BOLT_LENGTH_MM,
            "trial_shaft_diameter_mm": SHAFT_DIAMETER_MM,
            "trial_barrel_od_mm": BARREL_DIAMETER_MM,
            "trial_barrel_length_mm": BARREL_LENGTH_MM,
            "trial_washer_od_mm": WASHER_DIAMETER_MM,
        },
        "candidates": candidates,
        "mutual_candidate_hits_mm3": {
            key: value for key, value in mutual.items() if value
        },
        "nonempty_existing_obstacles": {
            key: value for key, value in obstacles.items() if value
        },
        "finite_clearance_screen_passed": not any(mutual.values())
        and not any(obstacles.values()),
        "retail_fit_verified": False,
        "thread_engagement_verified": False,
        "head_tool_fit_verified": False,
        "structural_capacity_verified": False,
        "complete_assembly_sequence_verified": False,
        "drilling_released": False,
        "fabrication_released": False,
    }


if __name__ == "__main__":
    print(json.dumps(probe(), indent=2, sort_keys=True))
