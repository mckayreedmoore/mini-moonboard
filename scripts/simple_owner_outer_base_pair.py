"""Detached mirrored outer-base 4x4 pair in the 139.7-mm header envelope."""

import hashlib
import json
from dataclasses import replace
from pathlib import Path

import cadquery as cq

from scripts import owner_layout_protected as protected_3d
from scripts import simple_owner_duty_ledger as ledger
from scripts import simple_pb03_lower_center_pair as lower
from scripts import simple_pb03_outer_counterbore_revision as retail
from scripts import simple_pb05_narrow_outer_screen as narrow
from scripts import simple_pb05_outer_base_4d_search as prior
from scripts import simple_pb07_outer_rail_native as pb07
from scripts import simple_pb09_owner_layout_screen as pb09

SOURCE_ID = "owner-outer-base-139p7-pair-v2"
TARGETS = ("clip_angle_base_left", "clip_angle_base_right")
SECTION_MM = 88.9
GRAIN_LENGTH_Y_MM = 60.0
SIDE_Y_MM = -149.5
HEADER_Y_MM = -141.2


def _volume(first, second):
    return lower._intersection_volume(first, second)


def _hits(features, protected):
    return {
        f"{feature}|{target}": round(volume, 6)
        for feature, shape in features.items()
        for target, other in protected.items()
        if (volume := _volume(shape, other)) > lower.TOL_MM3
    }


def _pair(station, wood):
    side_name = station.rsplit("_", 1)[1]
    left = side_name == "left"
    header = wood["base_header"]
    side = wood[f"base_side_{side_name}"]
    hb, sb = header.BoundingBox(), side.BoundingBox()
    if abs(hb.zmax - sb.zmin) > 1e-6 or abs(hb.ymin - sb.ymin) > 1e-6:
        raise ValueError(f"{station}: same-side original bearing changed")
    if abs(hb.ylen - 139.7) > 1e-6:
        raise ValueError("Outer-base header is not the approved 139.7-mm envelope")
    x0 = sb.xmax if left else sb.xmin - SECTION_MM
    z0 = hb.zmax
    # ponytail: rotate ordinary full-section stock; only crosscut its Y grain.
    block = cq.Solid.makeBox(
        SECTION_MM, GRAIN_LENGTH_Y_MM, SECTION_MM, cq.Vector(x0, hb.ymin, z0)
    )
    side_start = (sb.xmin if left else sb.xmax, SIDE_Y_MM, z0 + SECTION_MM / 2)
    specs = (
        (
            f"{station}_side",
            side_start,
            (1.0 if left else -1.0, 0.0, 0.0),
            sb.xlen + SECTION_MM,
            (f"base_side_{side_name}", "trial_cleat"),
        ),
        (
            f"{station}_header",
            (x0 + SECTION_MM / 2, HEADER_Y_MM, hb.zmin),
            (0.0, 0.0, 1.0),
            hb.zlen + SECTION_MM,
            ("base_header", "trial_cleat"),
        ),
    )
    bolts = {
        name: lower._stack(name, start, direction, grip, members)
        for name, start, direction, grip, members in specs
    }
    margins = {
        "side_y_rear": SIDE_Y_MM - hb.ymin,
        "side_y_front": hb.ymin + GRAIN_LENGTH_Y_MM - SIDE_Y_MM,
        "header_y_rear": HEADER_Y_MM - hb.ymin,
        "header_y_front": hb.ymin + GRAIN_LENGTH_Y_MM - HEADER_Y_MM,
        "header_x_each": SECTION_MM / 2,
        "side_z_each": SECTION_MM / 2,
    }
    contact = {
        "header": _volume(block.translate((0, 0, -0.1)), header) / 0.1,
        "side": _volume(block.translate((-0.1 if left else 0.1, 0, 0)), side) / 0.1,
    }
    return block, bolts, margins, contact, ("base_header", f"base_side_{side_name}")


def _installed(bolt, stack, side):
    length = retail.BOLT_LENGTH_MM if side else 152.4
    direction = bolt.direction.normalized()
    installed = dict(stack)
    installed["shaft"] = cq.Solid.makeCylinder(
        bolt.diameter / 2,
        length,
        bolt.start + direction * (lower.END_ALLOWANCE_MM - retail.WASHER_EACH_SIDE_MM),
        direction,
    )
    required = (
        bolt.grip
        + 2 * retail.WASHER_EACH_SIDE_MM
        + retail.NUT_HEIGHT_MM
        + retail.TWO_THREAD_PROJECTION_MM
    )
    tip = length - bolt.grip - retail.WASHER_EACH_SIDE_MM
    return installed, {
        "wood_grip_mm": round(bolt.grip, 6),
        "nominal_length_mm": length,
        "required_length_mm": round(required, 6),
        "length_margin_mm": round(length - required, 6),
        "tip_beyond_wood_mm": round(tip, 6),
        "tip_in_far_tool": 2.0 <= tip <= 2.0 + lower.TOOL_DEPTH_MM,
        "nut_on_listed_thread": (
            bolt.grip + 2 * retail.WASHER_EACH_SIDE_MM
            >= retail.BOLT_LENGTH_MM - retail.BOLT_LISTED_THREAD_LENGTH_MM
            if side
            else None
        ),
    }


def screen(module=None):
    """Screen one mirrored proposal against PB09; report open 3D/strength gates."""
    module = pb07.PB07Native() if module is None else module
    if (
        module.KEY != pb07.SOURCE_ID
        or pb09.SOURCE_ID != "pb09-owner-139p7-ten-block-layout-v1"
    ):
        raise ValueError("Owner-layout source identity changed")
    geometry, finished, panel_axes, frame, legacy, sds, alignment = pb09._build(module)
    if (
        set(TARGETS) - legacy
        or len(legacy) != 12
        or len(sds) != 72
        or not all(alignment.values())
    ):
        raise ValueError("Outer-base PB09 legacy inventory changed")
    original_duties = ledger.selected_duties()
    expected_sds = {
        axis for station in TARGETS for axis in original_duties[station]["sds_axes"]
    }
    if {
        row.name
        for row in sds
        if any(row.name.startswith(station + "_") for station in TARGETS)
    } != expected_sds or any(
        original_duties[station]["timber"]
        != ("base_header", f"base_side_{station.rsplit('_', 1)[1]}")
        for station in TARGETS
    ):
        raise ValueError("Selected-baseline outer-base SDS/timber duty changed")
    wood, _, panels, _, _ = lower._source_inventory()
    if len(panels) != 66 or len(panel_axes) != 66:
        raise ValueError("Fixed panel axes changed")
    original_frame = tuple(
        row for row in module._base_connections if row.kind == "bolt"
    )
    if (
        len(frame) != 12
        or len(original_frame) != 12
        or tuple(map(narrow._signature, frame))
        != tuple(map(narrow._signature, original_frame))
    ):
        raise ValueError("Retained frame bolts changed")
    installed_pb09 = {
        name: replace(
            row,
            stacks={bolt.name: pb07._nominal_stack(row, bolt) for bolt in row.bolts},
        )
        for name, row in geometry.items()
    }
    parts = {part.name: part.shape for part in module.parts()}
    finite_protected = protected_3d.inventory()
    if len(finite_protected["solids"]["panel_screws"]) != len(panel_axes) or len(
        finite_protected["solids"]["frame_bolts"]
    ) != len(frame):
        raise ValueError("Finite protected axes changed")
    protected = {
        **{f"pb09_block/{name}": row.block for name, row in installed_pb09.items()},
        **{
            f"pb09_bore/{name}/{bolt}": shape
            for name, row in installed_pb09.items()
            for bolt, shape in row.bores.items()
        },
        **{
            f"pb09_stack/{name}/{bolt}/{role}": shape
            for name, row in installed_pb09.items()
            for bolt, stack in row.stacks.items()
            for role, shape in stack.items()
        },
        **{
            f"pb09_tool/{name}/{bolt}/{end}": shape
            for name, row in installed_pb09.items()
            for bolt, tools in row.tools.items()
            for end, shape in tools.items()
        },
        **{f"panel_axis/{name}": shape for name, shape in panel_axes.items()},
        **{f"frame_axis/{row.name}": narrow._axis(row) for row in frame},
        **{f"legacy_clip/{name}": parts[name] for name in legacy - set(TARGETS)},
        **{
            f"legacy_sds/{row.name}": narrow._axis(row)
            for row in sds
            if not any(row.name.startswith(target + "_") for target in TARGETS)
        },
        **{
            f"other_timber/{name}": shape
            for name, shape in finished.items()
            if name not in {"base_header", "base_side_left", "base_side_right"}
        },
    }
    rows = {}
    for station in TARGETS:
        block, bolts, margins, contact, timber = _pair(station, wood)
        side = station.rsplit("_", 1)[1]
        bottom_outer = installed_pb09[
            "clip_horizontal_bottom_left_1"
            if side == "left"
            else "clip_horizontal_bottom_right_2"
        ]
        near_tools = [
            ends["near"]
            for name, ends in bottom_outer.tools.items()
            if "_rail_" in name
        ]
        if len(near_tools) != 2:
            raise ValueError("PB09 bottom-outer near-tool inventory changed")
        tool_y_gap = min(
            tool.BoundingBox().ymin - block.BoundingBox().ymax for tool in near_tools
        )
        features = {"block": block}
        stacks = {}
        bores = {}
        for name, (bolt, stack, bore, tools) in bolts.items():
            installed, report = _installed(bolt, stack, name.endswith("_side"))
            stacks[name] = report
            bores[name] = bore
            features[f"bore/{name}"] = bore
            features.update(
                {f"stack/{name}/{role}": shape for role, shape in installed.items()}
            )
            features.update(
                {f"tool/{name}/{end}": shape for end, shape in tools.items()}
            )
        side_host = wood[timber[1]]
        host_bores = {
            "side_receiver": _volume(bores[f"{station}_side"], side_host),
            "side_block": _volume(bores[f"{station}_side"], block),
            "header_receiver": _volume(bores[f"{station}_header"], wood["base_header"]),
            "header_block": _volume(bores[f"{station}_header"], block),
        }
        cross = _hits(
            {
                key: value
                for key, value in features.items()
                if key.startswith(("bore/", "stack/", "tool/"))
                and f"{station}_side" in key
            },
            {
                key: value
                for key, value in features.items()
                if key.startswith(("bore/", "stack/")) and f"{station}_header" in key
            },
        )
        finite_hits = {
            name: hits
            for name, hits in protected_3d.hits(
                {f"{station}/{name}": shape for name, shape in features.items()},
                finite_protected,
            ).items()
            if hits
        }
        rows[station] = {
            "timber": list(timber),
            "block_box_mm": list(prior._box(block)),
            "within_139p7_header_y_envelope": (
                block.BoundingBox().ymin
                >= wood["base_header"].BoundingBox().ymin - 1e-6
                and block.BoundingBox().ymax
                <= wood["base_header"].BoundingBox().ymax + 1e-6
            ),
            "bottom_outer_near_tool_y_gap_mm": round(tool_y_gap, 6),
            "same_side_contact": all(area > 0 for area in contact.values()),
            "contact_area_mm2": {
                key: round(value, 3) for key, value in contact.items()
            },
            "complete_host_bores": all(value > 0 for value in host_bores.values()),
            "host_bore_volume_mm3": {
                key: round(value, 6) for key, value in host_bores.items()
            },
            "edge_margins_mm": {key: round(value, 3) for key, value in margins.items()},
            "conditional_4d_edges": min(margins.values()) >= prior.FOUR_D_MM - 1e-6,
            "nominal_stacks": stacks,
            "protected_hits_mm3": _hits(features, protected),
            "finite_protected_hits_mm3": finite_hits,
            "own_cross_hits_mm3": cross,
        }
    clear = all(
        row["within_139p7_header_y_envelope"]
        and row["bottom_outer_near_tool_y_gap_mm"] > 0
        and row["same_side_contact"]
        and row["complete_host_bores"]
        and row["conditional_4d_edges"]
        and not row["protected_hits_mm3"]
        and not row["finite_protected_hits_mm3"]
        and not row["own_cross_hits_mm3"]
        and all(
            stack["length_margin_mm"] >= 0 and stack["tip_in_far_tool"]
            for stack in row["nominal_stacks"].values()
        )
        for row in rows.values()
    )
    return {
        "source_id": SOURCE_ID,
        "parent_source_id": pb09.SOURCE_ID,
        "parent_source_sha256": hashlib.sha256(
            Path(pb09.__file__).read_bytes()
        ).hexdigest(),
        "inventory": {
            "panel_screw_axes": len(panel_axes),
            "retained_frame_bolt_axes": len(frame),
            "pb09_blocks": len(geometry),
            "other_legacy_duties": len(legacy) - len(TARGETS),
        },
        "finite_protected_counts": finite_protected["counts"],
        "provisional_hold_rear_projection_mm": finite_protected[
            "hold_rear_projection_mm"
        ],
        "stations": rows,
        "protected_gates": {
            "finite_3d_solids_screened": True,
            "delivered_hold_bolt_length": None,
            "wiring_bend_radius": None,
            "hardware_heads": None,
            "delivered_hardware_and_assembly": None,
            "center_posts_plus_kicker_backing": None,
        },
        "decision": "ADVANCE_GEOMETRY_ONLY" if clear else "REVISE",
        "strength_checked": False,
        "drilling_released": False,
        "fabrication_released": False,
    }


if __name__ == "__main__":
    print(json.dumps(screen(), indent=2, sort_keys=True))
