"""Detached mirrored forward outer-header block trial; geometry only."""

import json
from functools import lru_cache

import cadquery as cq

from mini_moonboard.floor_flush_width import KERF_RIGHT, variant
from scripts import center_posts_outward_owner_layout as posts
from scripts import owner_corner_layout_assembly as scene
from scripts import owner_layout_outer_header_pair as original
from scripts import owner_layout_protected as protected
from scripts import simple_owner_outer_base_pair as outer_base
from scripts import simple_pb03_lower_center_pair as joints

BLOCK_X_MM = 55.0
BLOCK_Z0_MM = 103.5
BLOCK_REAR_Y_MM = -120.0
BLOCK_FRONT_Y_MM = -40.0
POST_BOLT_Y_MM = -80.0
POST_BOLT_Z_MM = (130.0, 170.0)
HEADER_BOLT_Y_MM = (-93.0, -67.0)
HEADER_BOLT_X_FROM_POST_MM = 30.0
HIT_TOL_MM3 = 1.0


def _hits(features, obstacles):
    return {
        f"{name}|{target}": round(volume, 6)
        for name, shape in features.items()
        for target, other in obstacles.items()
        if (volume := joints._intersection_volume(shape, other)) > HIT_TOL_MM3
    }


def _candidate(side, wood):
    """Keep post/header faces and four-bolt topology in compact solid stock."""
    old_block, old_bolts, _, _ = original._candidate(side, wood)
    old_box = old_block.BoundingBox()
    post_box = wood[f"base_post_outer_{side}"].BoundingBox()
    header_box = wood["base_header"].BoundingBox()
    left = side == "left"
    block = cq.Solid.makeBox(
        BLOCK_X_MM,
        BLOCK_FRONT_Y_MM - BLOCK_REAR_Y_MM,
        header_box.zmin - BLOCK_Z0_MM,
        cq.Vector(
            old_box.xmin if left else old_box.xmax - BLOCK_X_MM,
            BLOCK_REAR_Y_MM,
            BLOCK_Z0_MM,
        ),
    )
    bolts = {}
    for index, z in enumerate(POST_BOLT_Z_MM, 1):
        name = f"outer_header_{side}_post_{index}"
        bolts[name] = joints._stack(
            name,
            (post_box.xmin if left else post_box.xmax, POST_BOLT_Y_MM, z),
            (1.0 if left else -1.0, 0.0, 0.0),
            post_box.xlen + BLOCK_X_MM,
            old_bolts[name][0].members,
        )
    for index, y in enumerate(HEADER_BOLT_Y_MM, 1):
        name = f"outer_header_{side}_header_{index}"
        bolts[name] = joints._stack(
            name,
            (
                post_box.xmax + HEADER_BOLT_X_FROM_POST_MM
                if left
                else post_box.xmin - HEADER_BOLT_X_FROM_POST_MM,
                y,
                BLOCK_Z0_MM,
            ),
            (0.0, 0.0, 1.0),
            header_box.zlen + header_box.zmin - BLOCK_Z0_MM,
            old_bolts[name][0].members,
        )
    return block, bolts


@lru_cache(maxsize=1)
def screen():
    """Screen nominal CAD occupancy; no capacity, tolerance, or drilling claim."""
    model = variant(KERF_RIGHT)
    source_connections = model.connections()
    panel = model.panel_connections()
    frame = tuple(row for row in source_connections if row.kind == "bolt")
    if len(panel) != 66 or len(frame) != 12:
        raise ValueError("Fixed source axis inventory changed")
    placement = posts.build_layout()
    source_wood = {part.name: part.shape for part in model.uncut_wood_parts()}
    center_x = []
    for side in ("left", "right"):
        box = source_wood[f"base_post_center_{side}"].BoundingBox()
        center_x.append(
            round(placement["post_shift_x_mm"][side] + (box.xmin + box.xmax) / 2, 6)
        )
    if center_x != [-180.0, 180.0]:
        raise ValueError("Owner center-post pose changed")
    assembly = scene.build_assembly()
    wood = assembly["wood"]
    fixed = protected.inventory()
    rows = {}
    for side in ("left", "right"):
        station = f"clip_timber_header_outer_{side}"
        base_station = f"clip_angle_base_{side}"
        block, bolts = _candidate(side, wood)
        base_block, base_bolts, _, _, _ = outer_base._pair(base_station, wood)
        base_stacks = {
            f"{name}/{role}": shape
            for name, (_, stack, _, _) in base_bolts.items()
            for role, shape in stack.items()
        }
        base_tools = {
            f"{name}/{end}": shape
            for name, (_, _, _, tools) in base_bolts.items()
            for end, shape in tools.items()
        }
        features = {"block": block}
        host_coverage = {}
        host_other_hits = {}
        receiver = {
            "post": wood[f"base_post_outer_{side}"],
            "header": wood["base_header"],
        }
        for name, (bolt, stack, bore, tools) in bolts.items():
            kind = "post" if "_post_" in name else "header"
            core = cq.Solid.makeCylinder(
                joints.BORE_DIAMETER_MM / 2,
                bolt.grip,
                bolt.start + bolt.direction.normalized() * joints.END_ALLOWANCE_MM,
                bolt.direction,
            )
            host_coverage[name] = (
                round(
                    (
                        joints._intersection_volume(core, block)
                        + joints._intersection_volume(core, receiver[kind])
                    )
                    / core.Volume(),
                    7,
                )
                >= 0.999999
            )
            features[f"bore/{name}"] = bore
            features.update(
                {f"stack/{name}/{role}": shape for role, shape in stack.items()}
            )
            features.update(
                {f"tool/{name}/{end}": shape for end, shape in tools.items()}
            )
            host_other_hits[name] = _hits(
                {"bore": core},
                {
                    key: value
                    for key, value in wood.items()
                    if key not in {"base_header", f"base_post_outer_{side}"}
                },
            )
        other_blocks = {
            name: shape for name, shape in assembly["blocks"].items() if name != station
        }
        other_stacks = {
            f"{name}/{role}": shape
            for name, stack in assembly["stacks"].items()
            if assembly["diagnostics"]["bolt_station"][name] != station
            for role, shape in stack.items()
        }
        other_bores = {
            name: shape
            for name, shape in assembly["bores"].items()
            if assembly["diagnostics"]["bolt_station"][name] != station
        }
        # Base-specific rows give the exact six originally reported stack clashes.
        base_hit = _hits({"block": block}, base_stacks)
        base_tool_hit = _hits({"block": block}, base_tools)
        cross_hit = _hits(
            features,
            {
                **{f"block/{key}": value for key, value in other_blocks.items()},
                **{f"stack/{key}": value for key, value in other_stacks.items()},
                **{f"bore/{key}": value for key, value in other_bores.items()},
            },
        )
        finite = {
            name: hit for name, hit in protected.hits(features, fixed).items() if hit
        }
        bb = block.BoundingBox()
        header_bb = wood["base_header"].BoundingBox()
        rows[side] = {
            "block_y_mm": [round(bb.ymin, 6), round(bb.ymax, 6)],
            "local_n_mm": round(bb.ylen, 6),
            "inside_rear_2x6_envelope": bb.ymin >= header_bb.ymin - 1e-6
            and bb.ymax <= header_bb.ymax + 1e-6,
            "post_contact_mm2": round(
                joints._contact_area(
                    block, receiver["post"], (-1, 0, 0) if side == "left" else (1, 0, 0)
                ),
                3,
            ),
            "header_contact_mm2": round(
                joints._contact_area(block, receiver["header"], (0, 0, 1)), 3
            ),
            "host_bore_coverage": host_coverage,
            "nonreceiver_bore_hits_mm3": {
                name: hits for name, hits in host_other_hits.items() if hits
            },
            "outer_base_stack_hits_mm3": base_hit,
            "outer_base_tool_hits_mm3": base_tool_hit,
            "cross_scene_hits_mm3": cross_hit,
            "finite_protected_hits_mm3": finite,
            "block_vs_outer_base_block_mm3": round(
                joints._intersection_volume(block, base_block), 6
            ),
        }
    clear = all(
        row["inside_rear_2x6_envelope"]
        and row["local_n_mm"] <= 139.7
        and row["post_contact_mm2"] > 0
        and row["header_contact_mm2"] > 0
        and all(row["host_bore_coverage"].values())
        and not row["nonreceiver_bore_hits_mm3"]
        and not row["outer_base_stack_hits_mm3"]
        and not row["outer_base_tool_hits_mm3"]
        and not row["cross_scene_hits_mm3"]
        and not row["finite_protected_hits_mm3"]
        for row in rows.values()
    )
    return {
        "schema": "outer_header_forward_pose_trial/v1",
        "source_inventory": {
            "panel_kicker_axes": len(panel),
            "frame_bolt_axes": len(frame),
        },
        "center_posts_x_mm": center_x,
        "sides": rows,
        "decision": "NOMINAL_GEOMETRY_CLEAR_ONLY" if clear else "REVISE",
        "limitations": [
            "Uncut wood and generic bolt/tool envelopes",
            "No purchased bolt length, tolerance, load path, or drilling check",
        ],
        "drilling_released": False,
        "structural_released": False,
    }


if __name__ == "__main__":
    print(json.dumps(screen(), indent=2, sort_keys=True))
