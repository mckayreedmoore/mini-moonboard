"""Bounded 4D outer-base cleat search on the unchanged kerf-right PB05 model.

This is a geometric screen, not a joint-strength or drilling approval.
"""

import json

import cadquery as cq

from scripts import simple_pb03_lower_center_pair as lower
from scripts import simple_pb03_outer_counterbore_revision as retail
from scripts import simple_pb05_native as pb05
from scripts import simple_pb05_outer_base_revision as prior

FOUR_D_MM = 4 * lower.BOLT_DIAMETER_MM
STOCK = (("2x4-flat", 38.1, 88.9), ("2x4-edge", 88.9, 38.1), ("4x4", 88.9, 88.9))
FOUR_BY_FOUR_Y0_MM = -203.2
CLEAT_LENGTH_MM = 63.5
SIDE_Y_MM = -149.5
HEADER_Y_MM = -140.5


def _box(shape):
    b = shape.BoundingBox()
    return (b.xmin, b.xmax, b.ymin, b.ymax, b.zmin, b.zmax)


def _overlap(first, second):
    return lower._intersection_volume(first, second)


def _pair(station, wood):
    left = station.endswith("left")
    side = wood[f"base_side_{'left' if left else 'right'}"]
    header = wood["base_header"]
    sb, hb = side.BoundingBox(), header.BoundingBox()
    x0 = sb.xmax if left else sb.xmin - 88.9
    z0 = hb.zmax
    cleat = cq.Solid.makeBox(
        88.9, 88.9, CLEAT_LENGTH_MM, cq.Vector(x0, FOUR_BY_FOUR_Y0_MM, z0)
    )
    side_x = sb.xmin if left else sb.xmax
    side_direction = (1.0, 0.0, 0.0) if left else (-1.0, 0.0, 0.0)
    specs = (
        (
            f"{station}_side",
            (side_x, SIDE_Y_MM, z0 + CLEAT_LENGTH_MM / 2),
            side_direction,
            sb.xlen + 88.9,
            (f"base_side_{'left' if left else 'right'}", "trial_cleat"),
        ),
        (
            f"{station}_header",
            (x0 + 44.45, HEADER_Y_MM, hb.zmin),
            (0.0, 0.0, 1.0),
            hb.zlen + CLEAT_LENGTH_MM,
            ("base_header", "trial_cleat"),
        ),
    )
    bolts = {
        name: lower._stack(name, start, direction, grip, members)
        for name, start, direction, grip, members in specs
    }
    margins = {
        "side_receiver_y_front": SIDE_Y_MM - sb.ymin,
        "side_receiver_y_back": sb.ymax - SIDE_Y_MM,
        "side_receiver_z_end": z0 + CLEAT_LENGTH_MM / 2 - sb.zmin,
        "side_cleat_y_front": SIDE_Y_MM - FOUR_BY_FOUR_Y0_MM,
        "side_cleat_y_back": FOUR_BY_FOUR_Y0_MM + 88.9 - SIDE_Y_MM,
        "side_cleat_z_bottom": CLEAT_LENGTH_MM / 2,
        "side_cleat_z_top": CLEAT_LENGTH_MM / 2,
        "header_receiver_y_front": HEADER_Y_MM - hb.ymin,
        "header_receiver_y_back": hb.ymax - HEADER_Y_MM,
        "header_cleat_y_front": HEADER_Y_MM - FOUR_BY_FOUR_Y0_MM,
        "header_cleat_y_back": FOUR_BY_FOUR_Y0_MM + 88.9 - HEADER_Y_MM,
        "header_cleat_x_left": 44.45,
        "header_cleat_x_right": 44.45,
    }
    return cleat, bolts, margins


def screen(module=None):
    module = pb05.PB05Native() if module is None else module
    if (
        module.KEY != pb05.SOURCE_ID
        or module.ACTIVE_FINGERPRINT != lower.EXPECTED_PB02_FINGERPRINT
    ):
        raise ValueError("PB05 source identity changed")
    if tuple(module.legacy_proxy_stations()) != prior.source.EXPECTED_LEGACY:
        raise ValueError("PB05 legacy duties changed")
    wood = {item.name: item.shape for item in module.wood_parts()}
    parts = {item.name: item.shape for item in module.parts()}
    reference = module.pb03_geometries()
    frame = tuple(
        row
        for row in module.connections()
        if row.kind == "bolt" and not row.name.startswith("pb03_")
    )
    panel = tuple(module.panel_connections())
    original_frame = tuple(
        row for row in module._base_connections if row.kind == "bolt"
    )
    original_panel = tuple(
        row
        for row in module._base_connections
        if row.name in {axis.name for axis in panel}
    )
    if (
        len(reference) != 8
        or len(frame) != 12
        or len(panel) != 66
        or tuple(map(pb05._axis, frame)) != tuple(map(pb05._axis, original_frame))
        or tuple(map(pb05._axis, panel)) != tuple(map(pb05._axis, original_panel))
    ):
        raise ValueError("PB05 protected source axes changed")
    # A single full-section 2x4 is below 2*4D in one plan dimension, regardless of rotation.
    stock = {
        name: {"section_mm": [x, y], "4d_plan_possible": min(x, y) >= 2 * FOUR_D_MM}
        for name, x, y in STOCK
    }
    protected = {
        **{
            f"pb05_block/{item.block_name}": wood[item.block_name]
            for item in reference.values()
        },
        **{
            f"pb05_bore/{station}/{name}": shape
            for station, item in reference.items()
            for name, shape in item.bores.items()
        },
        **{
            f"pb05_stack/{station}/{name}/{role}": shape
            for station, item in reference.items()
            for name, stack in item.stacks.items()
            for role, shape in stack.items()
        },
        **{
            f"pb05_tool/{station}/{name}/{end}": shape
            for station, item in reference.items()
            for name, ends in item.tools.items()
            for end, shape in ends.items()
        },
        **{f"panel_axis/{axis.name}": prior._axis(axis) for axis in panel},
        **{f"frame_axis/{axis.name}": prior._axis(axis) for axis in frame},
        **{
            f"other_legacy_axis/{axis.name}": prior._axis(axis)
            for axis in module.connections()
            if axis.kind == "screw"
            and axis.name.startswith("clip_")
            and not any(
                axis.name.startswith(name + "_") for name in prior.TARGET_STATIONS
            )
        },
        **{
            f"lower_rail/{name}": wood[name]
            for name in ("base_rail_bottom_left", "base_rail_bottom_right")
        },
        **{
            f"retained_angle/{name}": parts[name]
            for name in (
                "clip_timber_header_outer_left",
                "clip_timber_header_outer_right",
            )
        },
        **{
            f"legacy_angle/{name}": parts[name]
            for name in module.legacy_proxy_stations()
            if name not in prior.TARGET_STATIONS
        },
        **{
            f"other_timber/{name}": shape
            for name, shape in wood.items()
            if name
            not in {
                "base_header",
                "base_side_left",
                "base_side_right",
                "base_rail_bottom_left",
                "base_rail_bottom_right",
            }
            and name not in {item.block_name for item in reference.values()}
            and not name.startswith(("main_", "kicker_"))
        },
        **{
            f"panel/{name}": shape
            for name, shape in wood.items()
            if name.startswith(("main_", "kicker_"))
        },
    }
    rows = {}
    for station in prior.TARGET_STATIONS:
        cleat, bolts, margins = _pair(station, wood)
        features = {"cleat": cleat}
        bolt_stack = {}
        for name, (bolt, stack, bore, tools) in bolts.items():
            features[f"bore/{name}"] = bore
            installed = dict(stack)
            # Full nominal purchased lengths, not the shorter analytical grip cylinder.
            direction = bolt.direction.normalized()
            nominal_length = retail.BOLT_LENGTH_MM if name.endswith("_side") else 127.0
            installed["shaft"] = cq.Solid.makeCylinder(
                bolt.diameter / 2,
                nominal_length,
                bolt.start
                + direction * (lower.END_ALLOWANCE_MM - retail.WASHER_EACH_SIDE_MM),
                direction,
            )
            required = (
                bolt.grip
                + 2 * retail.WASHER_EACH_SIDE_MM
                + retail.NUT_HEIGHT_MM
                + retail.TWO_THREAD_PROJECTION_MM
            )
            tip_from_far_wood = nominal_length - bolt.grip - retail.WASHER_EACH_SIDE_MM
            bolt_stack[name] = {
                "wood_grip_mm": round(bolt.grip, 6),
                "nominal_under_head_length_mm": nominal_length,
                "two_washers_mm": round(2 * retail.WASHER_EACH_SIDE_MM, 6),
                "nut_height_mm": round(retail.NUT_HEIGHT_MM, 6),
                "two_thread_allowance_mm": round(retail.TWO_THREAD_PROJECTION_MM, 6),
                "required_length_mm": round(required, 6),
                "length_margin_mm": round(nominal_length - required, 6),
                "tip_beyond_wood_mm": round(tip_from_far_wood, 6),
                "tip_beyond_nut_mm": round(
                    nominal_length - (required - retail.TWO_THREAD_PROJECTION_MM), 6
                ),
                "tip_within_40mm_far_tool": 2.0
                <= tip_from_far_wood
                <= 2.0 + lower.TOOL_DEPTH_MM,
                "nut_start_after_listed_8in_thread_start": (
                    bolt.grip + 2 * retail.WASHER_EACH_SIDE_MM
                    >= retail.BOLT_LENGTH_MM - retail.BOLT_LISTED_THREAD_LENGTH_MM
                    if name.endswith("_side")
                    else None
                ),
            }
            features.update(
                {f"stack/{name}/{role}": shape for role, shape in installed.items()}
            )
            features.update(
                {f"tool/{name}/{end}": shape for end, shape in tools.items()}
            )
        collisions = {
            f"{feature}|{target}": round(volume, 6)
            for feature, shape in features.items()
            for target, obstacle in protected.items()
            if (volume := _overlap(shape, obstacle)) > lower.TOL_MM3
        }
        side_name, header_name = f"{station}_side", f"{station}_header"
        side_hardware = {
            key: shape
            for key, shape in features.items()
            if key.startswith(f"stack/{side_name}/")
        }
        header_hardware = {
            key: shape
            for key, shape in features.items()
            if key.startswith(f"stack/{header_name}/")
        }
        own_cross = {
            f"{left}|{right}": round(volume, 6)
            for left, a in {
                f"bore/{side_name}": features[f"bore/{side_name}"],
                **side_hardware,
            }.items()
            for right, b in {
                f"bore/{header_name}": features[f"bore/{header_name}"],
                **header_hardware,
            }.items()
            if (volume := _overlap(a, b)) > lower.TOL_MM3
        }
        own_cross.update(
            {
                f"{tool}|{part}": round(volume, 6)
                for tool, a in features.items()
                if tool.startswith("tool/")
                for part, b in features.items()
                if part.startswith("stack/")
                and part.split("/")[1] != tool.split("/")[1]
                if (volume := _overlap(a, b)) > lower.TOL_MM3
            }
        )
        side_host = wood[f"base_side_{'left' if station.endswith('left') else 'right'}"]
        host_bore_volume = {
            "side_receiver": _overlap(features[f"bore/{side_name}"], side_host),
            "side_cleat": _overlap(features[f"bore/{side_name}"], cleat),
            "header_receiver": _overlap(
                features[f"bore/{header_name}"], wood["base_header"]
            ),
            "header_cleat": _overlap(features[f"bore/{header_name}"], cleat),
        }
        # Each target is still occupied by its old angle/SDS until this candidate is selected.
        rows[station] = {
            "cleat_box_mm": [round(value, 3) for value in _box(cleat)],
            "edge_margins_mm": {key: round(value, 3) for key, value in margins.items()},
            "conditional_4d_edges": min(margins.values()) >= FOUR_D_MM,
            "bolt_grips_mm": {
                name: bolt.grip for name, (bolt, _, _, _) in bolts.items()
            },
            "nominal_bolt_stacks": bolt_stack,
            "side_6in_length_shortfall_mm": round(
                bolt_stack[f"{station}_side"]["required_length_mm"] - 152.4, 6
            ),
            "protected_collisions": collisions,
            "cross_bolt_collisions": own_cross,
            "host_bore_volume_mm3": {
                key: round(value, 6) for key, value in host_bore_volume.items()
            },
            "header_contact_area_mm2": round(
                _overlap(cleat.translate((0, 0, -0.1)), wood["base_header"]) / 0.1, 3
            ),
            "side_contact_area_mm2": round(
                _overlap(
                    cleat.translate((-0.1 if station.endswith("left") else 0.1, 0, 0)),
                    side_host,
                )
                / 0.1,
                3,
            ),
        }
    return {
        "schema": "simple_pb05_outer_base_4d_search/v1",
        "source_id": pb05.SOURCE_ID,
        "stock_screen": stock,
        "four_d_target_mm": FOUR_D_MM,
        "stations": rows,
        "decision": "GEOMETRY_PASS_CONDITIONAL"
        if all(
            row["conditional_4d_edges"]
            and not row["protected_collisions"]
            and not row["cross_bolt_collisions"]
            and all(volume > 0 for volume in row["host_bore_volume_mm3"].values())
            and row["header_contact_area_mm2"] > 0
            and row["side_contact_area_mm2"] > 0
            and all(
                stack["length_margin_mm"] >= 0 and stack["tip_within_40mm_far_tool"]
                for stack in row["nominal_bolt_stacks"].values()
            )
            for row in rows.values()
        )
        else "REVISE",
        "reason": "A forward-shifted ordinary 4x4 is a nominal no-interference, 4D-edge candidate only; local capacity, purchased hardware, and assembly sequence remain open.",
        "strength_checked": False,
        "drilling_released": False,
        "fabrication_released": False,
    }


if __name__ == "__main__":
    print(json.dumps(screen(), indent=2, sort_keys=True))
