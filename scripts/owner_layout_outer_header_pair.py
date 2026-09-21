"""Same-side outer header/post block pose for owner layout review only.

This retains the selected kerf-right timber. It does not replace the two
brackets in a native assembly or establish a structural joint resistance.
"""

import json

import cadquery as cq

from mini_moonboard import compact_floor_flush_frame as source
from scripts import simple_pb03_lower_center_pair as joints

STATIONS = (
    "clip_timber_header_outer_left",
    "clip_timber_header_outer_right",
)
BLOCK_X_MM = 139.7
BLOCK_Y_MM = 88.9
BLOCK_Z_MM = 139.7
BLOCK_Y0_MM = -150.3
BLOCK_Z0_MM = 99.2
POST_BOLT_Y_MM = -125.0
POST_BOLT_Z_MM = (160.0, 200.0)
HEADER_BOLT_Y_MM = -80.0
HEADER_BOLT_X_FROM_POST_MM = (66.1, 106.1)


def _bounds(shape):
    box = shape.BoundingBox()
    return (box.xmin, box.xmax, box.ymin, box.ymax, box.zmin, box.zmax)


def _candidate(side, wood):
    post = wood[f"base_post_outer_{side}"]
    header = wood["base_header"]
    post_box = post.BoundingBox()
    header_box = header.BoundingBox()
    if abs(header_box.zmin - post_box.zmax) > 1e-6:
        raise ValueError("Outer post/header contact datum changed")
    left = side == "left"
    x0 = post_box.xmax if left else post_box.xmin - BLOCK_X_MM
    block = cq.Solid.makeBox(
        BLOCK_X_MM,
        BLOCK_Y_MM,
        BLOCK_Z_MM,
        cq.Vector(x0, BLOCK_Y0_MM, BLOCK_Z0_MM),
    )
    post_direction = (1.0, 0.0, 0.0) if left else (-1.0, 0.0, 0.0)
    post_start_x = post_box.xmin if left else post_box.xmax
    bolt_specs = [
        (
            f"outer_header_{side}_post_{index}",
            (post_start_x, POST_BOLT_Y_MM, z),
            post_direction,
            post_box.xlen + BLOCK_X_MM,
            (f"base_post_outer_{side}", f"outer_header_{side}_block"),
        )
        for index, z in enumerate(POST_BOLT_Z_MM, 1)
    ]
    bolt_specs.extend(
        (
            f"outer_header_{side}_header_{index}",
            (
                post_box.xmax + offset if left else post_box.xmin - offset,
                HEADER_BOLT_Y_MM,
                BLOCK_Z0_MM,
            ),
            (0.0, 0.0, 1.0),
            BLOCK_Z_MM + header_box.zlen,
            (f"outer_header_{side}_block", "base_header"),
        )
        for index, offset in enumerate(HEADER_BOLT_X_FROM_POST_MM, 1)
    )
    bolts = {
        name: joints._stack(name, start, direction, grip, members)
        for name, start, direction, grip, members in bolt_specs
    }
    post_contact = joints._contact_area(block, post, (-1, 0, 0) if left else (1, 0, 0))
    header_contact = joints._contact_area(block, header, (0, 0, 1))
    return block, bolts, post_contact, header_contact


def screen():
    """Check a bounded pose, preserving every old connection as history."""
    wood = {part.name: part.shape for part in source.uncut_wood_parts()}
    stations = {row[0]: row for row in source.stations()}
    if set(STATIONS) - set(stations):
        raise ValueError("Selected outer header/post duties changed")
    source_connections = source.connections()
    panel_axes = tuple(
        row
        for row in source_connections
        if row.name.startswith(("round_panel_", "round_kicker_", "kicker_header_"))
    )
    frame_bolts = tuple(row for row in source_connections if row.kind == "bolt")
    if len(panel_axes) != 66 or len(frame_bolts) != 12:
        raise ValueError("Selected protected axis inventory changed")
    rows = {}
    for side in ("left", "right"):
        station = f"clip_timber_header_outer_{side}"
        clip = stations[station]
        block, bolts, post_contact, header_contact = _candidate(side, wood)
        post = wood[f"base_post_outer_{side}"]
        header = wood["base_header"]
        unrelated = {
            name: round(volume, 6)
            for name, shape in wood.items()
            if name not in {"base_header", f"base_post_outer_{side}"}
            if (volume := joints._intersection_volume(block, shape)) > joints.TOL_MM3
        }
        complete = True
        bore_coverage = {}
        for name, (bolt, _stack, bore, _tools) in bolts.items():
            intended = (post, block) if "_post_" in name else (block, header)
            core = cq.Solid.makeCylinder(
                joints.BORE_DIAMETER_MM / 2,
                bolt.grip,
                bolt.start + bolt.direction.normalized() * joints.END_ALLOWANCE_MM,
                bolt.direction,
            )
            coverage = (
                sum(joints._intersection_volume(core, member) for member in intended)
                / core.Volume()
            )
            bore_coverage[name] = round(coverage, 7)
            if coverage < 0.999999:
                complete = False
            if abs(bolt.grip - 177.8) > 1e-6:
                raise ValueError(f"{name}: wood grip changed")
        bx = _bounds(block)
        rows[station] = {
            "block_bounds_xyz_mm": [round(value, 6) for value in bx],
            "same_side_as_original_clip": (
                bx[0] >= post.BoundingBox().xmax - 1e-6
                if side == "left"
                else bx[1] <= post.BoundingBox().xmin + 1e-6
            )
            and (clip[2].x > 0 if side == "left" else clip[2].x < 0),
            "post_contact_area_mm2": round(post_contact, 3),
            "header_contact_area_mm2": round(header_contact, 3),
            "complete_bores": complete,
            "nominal_core_bore_coverage": bore_coverage,
            "unrelated_timber_hits_mm3": unrelated,
            "bolts": list(bolts),
            "limitation": "Full nominal core bores are present; tool, installed-stack, end/edge and strength checks remain open.",
        }
    return {
        "schema": "owner_layout_outer_header_pair/v1",
        "stations": list(STATIONS),
        "candidate_blocks": 2,
        "candidate_bolts": sum(len(row["bolts"]) for row in rows.values()),
        "source_panel_kicker_axes": len(panel_axes),
        "source_frame_bolts": len(frame_bolts),
        "block_section_mm": [BLOCK_X_MM, BLOCK_Y_MM, BLOCK_Z_MM],
        "block_y_bounds_mm": [BLOCK_Y0_MM, round(BLOCK_Y0_MM + BLOCK_Y_MM, 6)],
        "block_z_bounds_mm": [BLOCK_Z0_MM, round(BLOCK_Z0_MM + BLOCK_Z_MM, 6)],
        "pairs": rows,
        "decision": "GEOMETRY_TRIAL_ONLY",
        "hold_tnut_led_clearance_checked": False,
        "installed_stack_and_tool_checked": False,
        "legacy_angle_removed_from_candidate": False,
        "drilling_released": False,
        "structural_released": False,
    }


if __name__ == "__main__":
    print(json.dumps(screen(), indent=2, sort_keys=True))
