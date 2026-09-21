"""Detached outer-base full-section cleat screen against kerf-right PB05."""

import json

import cadquery as cq

from scripts import simple_pb03_lower_center_pair as lower
from scripts import simple_pb05_native as pb05

TARGET_STATIONS = ("clip_angle_base_left", "clip_angle_base_right")
EXPECTED_LEGACY = (
    "clip_single_top_left_1",
    "clip_single_top_right_2",
    "clip_timber_header_outer_left",
    "clip_timber_header_outer_right",
    "clip_split_top_center_left",
    "clip_split_base_center_left",
    "clip_split_header_center_left",
    "clip_split_top_center_right",
    *TARGET_STATIONS,
    "clip_horizontal_bottom_left_2",
    "clip_horizontal_upper_left_2",
    "clip_horizontal_bottom_right_1",
    "clip_horizontal_upper_right_1",
)
CLEAT_THICKNESS_MM = 38.1
CLEAT_DEPTH_MM = 139.7
CLEAT_HEIGHT_MM = 139.7


def _axis(row):
    return cq.Solid.makeCylinder(row.diameter / 2, row.length, row.start, row.direction)


def _hits(shape, targets):
    return {
        name: round(volume, 6)
        for name, other in targets.items()
        if (volume := lower._intersection_volume(shape, other)) > lower.TOL_MM3
    }


def _cleat(station, header, side):
    """A vertical-grain 2×6, seated on header and against inner side-rim face."""
    hb, sb = header.BoundingBox(), side.BoundingBox()
    left = station.endswith("left")
    if abs(hb.zmax - sb.zmin) > 1e-6 or abs(sb.ymin - hb.ymin) > 1e-5:
        raise ValueError(f"{station}: source header/side bearing faces changed")
    x0 = sb.xmax if left else sb.xmin - CLEAT_THICKNESS_MM
    block = cq.Solid.makeBox(
        CLEAT_THICKNESS_MM,
        CLEAT_DEPTH_MM,
        CLEAT_HEIGHT_MM,
        cq.Vector(x0, hb.ymin, hb.zmax),
    )
    prefix = "pb05_outer_base_left" if left else "pb05_outer_base_right"
    side_start_x = sb.xmin if left else sb.xmax
    side_direction = (1.0, 0.0, 0.0) if left else (-1.0, 0.0, 0.0)
    specs = [
        (
            f"{prefix}_side_{index}",
            (side_start_x, hb.ymin + CLEAT_DEPTH_MM / 2, hb.zmax + rise),
            side_direction,
            sb.xlen + CLEAT_THICKNESS_MM,
            (f"base_side_{'left' if left else 'right'}", prefix + "_cleat"),
        )
        for index, rise in enumerate((38.1, 101.6), 1)
    ]
    specs += [
        (
            f"{prefix}_header_{index}",
            (x0 + CLEAT_THICKNESS_MM / 2, hb.ymin + offset, hb.zmin),
            (0.0, 0.0, 1.0),
            hb.zlen + CLEAT_HEIGHT_MM,
            ("base_header", prefix + "_cleat"),
        )
        for index, offset in enumerate((35.0, 104.7), 1)
    ]
    bolts, stacks, bores, tools = [], {}, {}, {}
    for name, start, direction, grip, members in specs:
        bolt, stack, bore, access = lower._stack(name, start, direction, grip, members)
        bolts.append(bolt)
        stacks[name], bores[name], tools[name] = stack, bore, access
    return {
        "block": block,
        "bolts": bolts,
        "stacks": stacks,
        "bores": bores,
        "tools": tools,
    }


def screen(module=None):
    module = pb05.PB05Native() if module is None else module
    if (
        module.KEY != pb05.SOURCE_ID
        or module.ACTIVE_FINGERPRINT != lower.EXPECTED_PB02_FINGERPRINT
    ):
        raise ValueError("PB05 source identity changed")
    legacy = tuple(module.legacy_proxy_stations())
    if legacy != EXPECTED_LEGACY:
        raise ValueError("PB05 exact legacy station inventory changed")
    stations = {row[0]: row for row in module.stations()}
    wood = {part.name: part.shape for part in module.wood_parts()}
    parts = {part.name: part.shape for part in module.parts()}
    reference = module.pb03_geometries()
    connections = tuple(module.connections())
    panel_axes = tuple(module.panel_connections())
    frame = tuple(
        row
        for row in connections
        if row.kind == "bolt" and not row.name.startswith("pb03_")
    )
    target_sds = tuple(
        row
        for row in connections
        if any(row.name.startswith(name + "_") for name in TARGET_STATIONS)
    )
    other_sds = tuple(
        row
        for row in connections
        if row.kind == "screw"
        and row.name.startswith("clip_")
        and not any(row.name.startswith(name + "_") for name in TARGET_STATIONS)
    )
    if (
        len(reference) != 8
        or len(frame) != 12
        or len(panel_axes) != 66
        or len(target_sds) != 12
        or len(other_sds) != 72
        or any(row.kind != "screw" for row in target_sds)
        or not all(name in stations and name in parts for name in TARGET_STATIONS)
    ):
        raise ValueError("PB05 protected geometry or retained duties changed")
    pair = {}
    for name in TARGET_STATIONS:
        beam, upright = stations[name][4:]
        if beam != "base_header" or upright != f"base_side_{name.rsplit('_', 1)[1]}":
            raise ValueError("outer-base station members changed")
        pair[name] = _cleat(name, wood[beam], wood[upright])
    pb05_names = {item.block_name for item in reference.values()}
    families = {
        "pb05_blocks": {name: wood[name] for name in pb05_names},
        "pb05_bores": {
            f"{station}/{name}": shape
            for station, item in reference.items()
            for name, shape in item.bores.items()
        },
        "pb05_stacks": {
            f"{station}/{name}/{role}": shape
            for station, item in reference.items()
            for name, stack in item.stacks.items()
            for role, shape in stack.items()
        },
        "pb05_tools": {
            f"{station}/{name}/{end}": shape
            for station, item in reference.items()
            for name, ends in item.tools.items()
            for end, shape in ends.items()
        },
        "frame_bolt_axes": {row.name: _axis(row) for row in frame},
        "panel_kicker_axes": {row.name: _axis(row) for row in panel_axes},
        "panels": {
            name: shape
            for name, shape in wood.items()
            if name.startswith(("main_", "kicker_"))
        },
        "target_legacy_axes": {row.name: _axis(row) for row in target_sds},
        "target_legacy_angles": {name: parts[name] for name in TARGET_STATIONS},
        "other_legacy_axes": {row.name: _axis(row) for row in other_sds},
        "other_legacy_angles": {
            name: parts[name] for name in legacy if name not in TARGET_STATIONS
        },
        "unrelated_timber": {
            name: shape
            for name, shape in wood.items()
            if name not in pb05_names
            and not name.startswith(("main_", "kicker_"))
            and name not in ("base_header", "base_side_left", "base_side_right")
        },
    }
    features = {}
    for station, item in pair.items():
        features[f"block/{station}"] = item["block"]
        features.update(
            {f"bore/{station}/{name}": shape for name, shape in item["bores"].items()}
        )
        features.update(
            {
                f"stack/{station}/{name}/{role}": shape
                for name, stack in item["stacks"].items()
                for role, shape in stack.items()
            }
        )
        features.update(
            {
                f"tool/{station}/{name}/{end}": shape
                for name, ends in item["tools"].items()
                for end, shape in ends.items()
            }
        )
    # ponytail: one exact-volume pass covers every protected PB05 solid and axis.
    collisions = {
        family: {
            f"{feature}|{target}": volume
            for feature, shape in features.items()
            for target, volume in _hits(shape, solids).items()
        }
        for family, solids in families.items()
    }
    own = {}
    for station, item in pair.items():
        for bolt in item["bolts"]:
            for host in bolt.members:
                shape = item["block"] if host.endswith("_cleat") else wood[host]
                own[f"{station}/{bolt.name}/{host}"] = round(
                    lower._intersection_volume(item["bores"][bolt.name], shape), 6
                )
    base_frame = tuple(row for row in module._base_connections if row.kind == "bolt")
    panel_names = {row.name for row in panel_axes}
    base_panel = tuple(
        row for row in module._base_connections if row.name in panel_names
    )
    source_preserved = (
        tuple(map(pb05._axis, frame)) == tuple(map(pb05._axis, base_frame))
        and tuple(map(pb05._axis, panel_axes)) == tuple(map(pb05._axis, base_panel))
        and len(legacy) == 14
        and len(target_sds) == 12
        and len(other_sds) == 72
    )
    if not source_preserved:
        raise ValueError("PB05 frame or panel axes changed")
    return {
        "schema": "simple_pb05_next_legacy_pair/v1",
        "source_id": pb05.SOURCE_ID,
        "legacy_stations_exact": list(legacy),
        "candidate_stations": list(TARGET_STATIONS),
        "inventory": {
            "pb05_blocks": len(reference),
            "original_frame_bolts": len(frame),
            "panel_kicker_axes": len(panel_axes),
            "target_legacy_sds_axes_retained": len(target_sds),
            "other_legacy_sds_axes_retained": len(other_sds),
            "candidate_blocks": len(pair),
            "candidate_bolts": sum(len(item["bolts"]) for item in pair.values()),
        },
        "stations": {
            name: {
                "full_section_mm": [CLEAT_THICKNESS_MM, CLEAT_DEPTH_MM],
                "grain_length_mm": CLEAT_HEIGHT_MM,
                "block_box_mm": [
                    round(v, 6)
                    for v in (
                        item["block"].BoundingBox().xmin,
                        item["block"].BoundingBox().xmax,
                        item["block"].BoundingBox().ymin,
                        item["block"].BoundingBox().ymax,
                        item["block"].BoundingBox().zmin,
                        item["block"].BoundingBox().zmax,
                    )
                ],
                "bolt_grips_mm": {bolt.name: bolt.grip for bolt in item["bolts"]},
            }
            for name, item in pair.items()
        },
        "bore_host_intersections_mm3": own,
        "collision_hits_mm3": collisions,
        "source_preserved": source_preserved,
        "obstructions": [family for family, hits in collisions.items() if hits],
        "decision": "REVISE",
        "reason": "Both full-section cleats intersect PB05 bottom-outer blocks and bottom rails; installed retail stacks and joint resistance remain unresolved.",
        "native_source_changed": False,
        "strength_checked": False,
        "drilling_released": False,
        "fabrication_released": False,
    }


if __name__ == "__main__":
    print(json.dumps(screen(), indent=2, sort_keys=True))
