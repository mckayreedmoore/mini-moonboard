"""Recessed outer-header barrel-bolt head: finite fit screen, not a cut plan.

The side rim is present for installed fit and absent only for a conditional
driver-access screen. Neither the assembly sequence nor hardware is approved.
"""

import json

import cadquery as cq

from scripts import owner_barrel_outer_top_layout as outer
from scripts import owner_layout_protected as protected
from scripts import simple_cross_dowel_continuation as hardware
from scripts.owner_barrel_layout_assembly import build_assembly

SOURCE_ID = "owner-barrel-outer-header-recess-probe-v1"
WASHER_OD_MM = 25.4  # Provisional geometric envelope, not selected hardware.
HEAD_OD_MM = 11.0
HEAD_HEIGHT_MM = 4.0
COUNTERBORE_DIAMETER_MM = 25.4
HEAD_BELOW_TOP_MM = 1.0  # Positive nominal cover; not a tolerance allowance.
TOOL_DIAMETER_MM = 20.0  # Provisional straight-driver envelope.
TOOL_LENGTH_MM = 40.0
TOL_MM3 = 1.0


def _hits(shape, targets):
    return {
        name: round(volume, 6)
        for name, target in targets.items()
        if (volume := protected._volume(shape, target)) > TOL_MM3
    }


def _row(side, index, row, assembly):
    wood = assembly["wood"]
    header = wood["base_header"]
    rim = wood[f"base_side_{side}"]
    top = header.BoundingBox().zmax
    x, y, _ = row["machine_start_xyz_mm"]
    washer_t = hardware.WASHER_THICKNESS_SENSITIVITY_MM
    recess = washer_t + HEAD_HEIGHT_MM + HEAD_BELOW_TOP_MM
    seat_z = top - recess
    washer = outer._cylinder(
        cq.Vector(x, y, seat_z), cq.Vector(0, 0, 1), washer_t, WASHER_OD_MM
    )
    head = outer._cylinder(
        cq.Vector(x, y, seat_z + washer_t),
        cq.Vector(0, 0, 1),
        HEAD_HEIGHT_MM,
        HEAD_OD_MM,
    )
    shaft = outer._cylinder(
        cq.Vector(x, y, seat_z + washer_t),
        cq.Vector(0, 0, -1),
        hardware.BOLT_LENGTH_MM,
        hardware.THREAD_MAJOR_MM,
    )
    counterbore = outer._cylinder(
        cq.Vector(x, y, top),
        cq.Vector(0, 0, -1),
        recess,
        COUNTERBORE_DIAMETER_MM,
    )
    pilot = outer._cylinder(
        cq.Vector(x, y, seat_z),
        cq.Vector(0, 0, -1),
        hardware.BOLT_LENGTH_MM - washer_t,
        outer.MACHINE_BORE_D_MM,
    )
    tool = outer._cylinder(
        cq.Vector(x, y, seat_z + washer_t + HEAD_HEIGHT_MM),
        cq.Vector(0, 0, 1),
        TOOL_LENGTH_MM,
        TOOL_DIAMETER_MM,
    )
    original_shaft = outer._cylinder(
        cq.Vector(x, y, top + washer_t),
        cq.Vector(0, 0, -1),
        hardware.BOLT_LENGTH_MM,
        hardware.THREAD_MAJOR_MM,
    )
    name = f"barrel_trial_clip_timber_header_outer_{side}_{index}"
    own = {"base_header", f"base_post_outer_{side}"}
    unrelated = {key: value for key, value in wood.items() if key not in own}
    physical = {"shaft": shaft, "washer": washer, "head": head}
    fixed_shapes = physical | {"counterbore": counterbore, "pilot": pilot}
    fixed_hits = {
        key: hits for key, hits in protected.hits(fixed_shapes).items() if hits
    }
    unrelated_hits = {
        key: hits
        for key, shape in fixed_shapes.items()
        if (hits := _hits(shape, unrelated))
    }
    other_hardware = {
        f"barrel/{key}": value
        for key, value in assembly["barrels"].items()
        if not key.startswith(name)
    }
    other_hardware.update(
        {
            f"bolt/{key}/{role}": shape
            for key, roles in assembly["stacks"].items()
            if not key.startswith(name)
            for role, shape in roles.items()
        }
    )
    neighbor_hits = {
        key: hits
        for key, shape in fixed_shapes.items()
        if (hits := _hits(shape, other_hardware))
    }
    header_bore_volume = counterbore.intersect(header).Volume()
    tip_z = seat_z + washer_t - hardware.BOLT_LENGTH_MM
    axis_z = row["axis_xyz_mm"][2]
    barrel = assembly["barrels"][name]
    return {
        "original_shaft_side_rim_hit_mm3": round(
            protected._volume(original_shaft, rim), 6
        ),
        "recessed_stack_side_rim_hit_mm3": round(
            sum(protected._volume(shape, rim) for shape in physical.values()), 6
        ),
        "counterbore_side_rim_hit_mm3": round(protected._volume(counterbore, rim), 6),
        "tool_side_rim_hit_when_assembled_mm3": round(protected._volume(tool, rim), 6),
        "tool_other_wood_hits_with_rim_removed_mm3": _hits(
            tool, {key: shape for key, shape in unrelated.items() if shape is not rim}
        ),
        "fixed_protected_hits_mm3": fixed_hits,
        "unrelated_wood_hits_mm3": unrelated_hits,
        "neighbor_hardware_hits_mm3": neighbor_hits,
        "counterbore_header_coverage": round(
            header_bore_volume / counterbore.Volume(), 6
        ),
        "counterbore_header_side_margin_mm": round(
            min(x - header.BoundingBox().xmin, header.BoundingBox().xmax - x)
            - COUNTERBORE_DIAMETER_MM / 2,
            6,
        ),
        "header_thickness_below_recess_mm": round(
            seat_z - header.BoundingBox().zmin, 6
        ),
        "machine_bore_meets_barrel": pilot.intersect(barrel).Volume() > TOL_MM3,
        "tip_beyond_barrel_axis_mm": round(axis_z - tip_z, 6),
        "disposition": "REVISE",
    }


def probe(assembly=None):
    """Compare four recessed rows with the current full kerf-right assembly."""
    assembly = build_assembly() if assembly is None else assembly
    if (
        len(assembly["panel_connections"]) != 66
        or len(assembly["frame_connections"]) != 12
    ):
        raise ValueError("Fixed source connection inventory changed")
    rows = {
        f"{side}/{index}": _row(side, index, row, assembly)
        for side in ("left", "right")
        for index, row in enumerate(outer._header_outer(side, assembly["wood"]), 1)
    }
    return {
        "source_id": SOURCE_ID,
        "inventory": {
            "rows": len(rows),
            "fixed_panel_screws": len(assembly["panel_connections"]),
            "retained_frame_bolts": len(assembly["frame_connections"]),
        },
        "trial": {
            "washer_od_mm": WASHER_OD_MM,
            "washer_thickness_mm": hardware.WASHER_THICKNESS_SENSITIVITY_MM,
            "head_od_mm": HEAD_OD_MM,
            "head_height_mm": HEAD_HEIGHT_MM,
            "counterbore_diameter_mm": COUNTERBORE_DIAMETER_MM,
            "head_below_header_top_mm": HEAD_BELOW_TOP_MM,
            "counterbore_depth_mm": round(
                hardware.WASHER_THICKNESS_SENSITIVITY_MM
                + HEAD_HEIGHT_MM
                + HEAD_BELOW_TOP_MM,
                6,
            ),
            "driver_envelope_diameter_mm": TOOL_DIAMETER_MM,
            "side_rim_must_be_removed_for_driver": True,
            "delivered_head_washer_driver_verified": False,
        },
        "rows": rows,
        "limits": (
            "Nominal finite screen only. Rim-removal sequence, actual hardware, "
            "counterbore net section, wood/barrel resistance, and complete joint "
            "load path are unqualified. No drilling dimensions are released."
        ),
        "layout_approved": False,
        "drilling_released": False,
        "fabrication_released": False,
        "structural_released": False,
    }


if __name__ == "__main__":
    print(json.dumps(probe(), indent=2, sort_keys=True))
