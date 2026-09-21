"""Bounded full-section 2x2 outer-base cleat trial; no structural release."""

import json

import cadquery as cq

from scripts import simple_pb03_lower_center_pair as lower
from scripts import simple_pb05_native as pb05
from scripts import simple_pb05_next_legacy_pair as source

TARGET_STATIONS = source.TARGET_STATIONS
SECTION_MM = 38.1
LENGTH_MM = 30.0
FRONT_Y_MM = -175.7
SIDE_BOLT_Y_MM = -163.0
HEADER_BOLT_Y_MM = -151.0
SIDE_BOLT_Z_MM = 292.0
CONDITIONAL_4D_MM = 4 * lower.BOLT_DIAMETER_MM


def _axis(row):
    return cq.Solid.makeCylinder(row.diameter / 2, row.length, row.start, row.direction)


def _hits(features, obstacles):
    return {
        f"{name}|{target}": round(volume, 6)
        for name, shape in features.items()
        for target, other in obstacles.items()
        if (volume := lower._intersection_volume(shape, other)) > lower.TOL_MM3
    }


def _cleat(station, header, side):
    hb, sb = header.BoundingBox(), side.BoundingBox()
    left = station.endswith("left")
    if abs(hb.zmax - sb.zmin) > 1e-6 or abs(sb.ymin - hb.ymin) > 1e-5:
        raise ValueError(f"{station}: source bearing faces changed")
    x0 = sb.xmax if left else sb.xmin - SECTION_MM
    block = cq.Solid.makeBox(
        SECTION_MM, SECTION_MM, LENGTH_MM, cq.Vector(x0, FRONT_Y_MM, hb.zmax)
    )
    prefix = f"pb05_outer_base_{'left' if left else 'right'}"
    side_direction = (1.0, 0.0, 0.0) if left else (-1.0, 0.0, 0.0)
    header_x = x0 + (25.3 if left else 12.8)
    specs = (
        (
            f"{prefix}_side",
            (sb.xmin if left else sb.xmax, SIDE_BOLT_Y_MM, SIDE_BOLT_Z_MM),
            side_direction,
            sb.xlen + SECTION_MM,
            (f"base_side_{'left' if left else 'right'}", f"{prefix}_cleat"),
        ),
        (
            f"{prefix}_header",
            (header_x, HEADER_BOLT_Y_MM, hb.zmin),
            (0.0, 0.0, 1.0),
            hb.zlen + LENGTH_MM,
            ("base_header", f"{prefix}_cleat"),
        ),
    )
    bolts, bores, stacks, tools = [], {}, {}, {}
    for name, start, direction, grip, members in specs:
        bolt, stack, bore, access = lower._stack(name, start, direction, grip, members)
        bolts.append(bolt)
        bores[name], stacks[name], tools[name] = bore, stack, access
    # ponytail: report the limiting nominal edge margins; structural adequacy is separate.
    edges = {
        "side_y_front": SIDE_BOLT_Y_MM - FRONT_Y_MM,
        "side_y_back": FRONT_Y_MM + SECTION_MM - SIDE_BOLT_Y_MM,
        "side_z_bottom": SIDE_BOLT_Z_MM - hb.zmax,
        "side_z_top": hb.zmax + LENGTH_MM - SIDE_BOLT_Z_MM,
        "header_x_left": header_x - x0,
        "header_x_right": x0 + SECTION_MM - header_x,
        "header_y_front": HEADER_BOLT_Y_MM - FRONT_Y_MM,
        "header_y_back": FRONT_Y_MM + SECTION_MM - HEADER_BOLT_Y_MM,
    }
    return {
        "block": block,
        "bolts": bolts,
        "bores": bores,
        "stacks": stacks,
        "tools": tools,
        "edge_margins_mm": edges,
    }


def screen(module=None):
    module = pb05.PB05Native() if module is None else module
    if (
        module.KEY != pb05.SOURCE_ID
        or module.ACTIVE_FINGERPRINT != lower.EXPECTED_PB02_FINGERPRINT
    ):
        raise ValueError("PB05 source identity changed")
    legacy = tuple(module.legacy_proxy_stations())
    if legacy != source.EXPECTED_LEGACY:
        raise ValueError("PB05 exact legacy stations changed")
    stations = {row[0]: row for row in module.stations()}
    wood = {part.name: part.shape for part in module.wood_parts()}
    parts = {part.name: part.shape for part in module.parts()}
    reference = module.pb03_geometries()
    connections = tuple(module.connections())
    panel = tuple(module.panel_connections())
    frame = tuple(
        row
        for row in connections
        if row.kind == "bolt" and not row.name.startswith("pb03_")
    )
    original_frame = tuple(
        row for row in module._base_connections if row.kind == "bolt"
    )
    panel_names = {row.name for row in panel}
    original_panel = tuple(
        row for row in module._base_connections if row.name in panel_names
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
    preserved = (
        len(reference) == 8
        and len(frame) == len(original_frame) == 12
        and len(panel) == len(original_panel) == 66
        and len(target_sds) == 12
        and len(other_sds) == 72
        and all(row.kind == "screw" for row in target_sds)
        and tuple(map(pb05._axis, frame)) == tuple(map(pb05._axis, original_frame))
        and tuple(map(pb05._axis, panel)) == tuple(map(pb05._axis, original_panel))
    )
    if not preserved:
        raise ValueError("PB05 protected source axes changed")
    pair = {}
    for station in TARGET_STATIONS:
        if station not in stations or station not in parts:
            raise ValueError("PB05 target station changed")
        beam, upright = stations[station][4:]
        if beam != "base_header" or upright != f"base_side_{station.rsplit('_', 1)[1]}":
            raise ValueError("PB05 outer-base members changed")
        pair[station] = _cleat(station, wood[beam], wood[upright])
    features = {}
    for station, item in pair.items():
        features[f"block/{station}"] = item["block"]
        for name, shape in item["bores"].items():
            features[f"bore/{station}/{name}"] = shape
        for name, stack in item["stacks"].items():
            for role, shape in stack.items():
                features[f"stack/{station}/{name}/{role}"] = shape
        for name, ends in item["tools"].items():
            for end, shape in ends.items():
                features[f"tool/{station}/{name}/{end}"] = shape
    block_names = {item.block_name for item in reference.values()}
    families = {
        "pb05_blocks": {name: wood[name] for name in block_names},
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
        "lower_rails": {
            name: wood[name]
            for name in ("base_rail_bottom_left", "base_rail_bottom_right")
        },
        "retained_header_angles": {
            name: parts[name]
            for name in (
                "clip_timber_header_outer_left",
                "clip_timber_header_outer_right",
            )
        },
        "frame_bolt_axes": {row.name: _axis(row) for row in frame},
        "panel_kicker_axes": {row.name: _axis(row) for row in panel},
        "panels": {
            name: shape
            for name, shape in wood.items()
            if name.startswith(("main_", "kicker_"))
        },
        "other_legacy_axes": {row.name: _axis(row) for row in other_sds},
        "other_legacy_angles": {
            name: parts[name] for name in legacy if name not in TARGET_STATIONS
        },
        "other_timber": {
            name: shape
            for name, shape in wood.items()
            if name not in block_names
            and name not in ("base_header", "base_side_left", "base_side_right")
            and not name.startswith(("main_", "kicker_"))
            and name not in ("base_rail_bottom_left", "base_rail_bottom_right")
        },
    }
    collisions = {
        name: _hits(features, obstacles) for name, obstacles in families.items()
    }
    edge_minimum = min(
        margin for item in pair.values() for margin in item["edge_margins_mm"].values()
    )
    gates = {
        "protected_cad_clear": not any(collisions.values()),
        "nominal_washer_seats": edge_minimum >= lower.WASHER_DIAMETER_MM / 2 - 1e-6,
        "conditional_4d_edge_target": edge_minimum >= CONDITIONAL_4D_MM - 1e-6,
    }
    return {
        "schema": "simple_pb05_outer_base_revision/v1",
        "source_id": pb05.SOURCE_ID,
        "source_preserved": preserved,
        "inventory": {
            "original_frame_bolts": len(frame),
            "panel_kicker_axes": len(panel),
            "other_legacy_sds_axes": len(other_sds),
            "pb05_blocks": len(reference),
            "candidate_cleats": len(pair),
            "candidate_bolts": sum(len(item["bolts"]) for item in pair.values()),
        },
        "stations": {
            name: {
                "full_section_mm": [SECTION_MM, SECTION_MM],
                "grain_length_mm": LENGTH_MM,
                "block_box_mm": [
                    round(value, 6)
                    for value in (
                        item["block"].BoundingBox().xmin,
                        item["block"].BoundingBox().xmax,
                        item["block"].BoundingBox().ymin,
                        item["block"].BoundingBox().ymax,
                        item["block"].BoundingBox().zmin,
                        item["block"].BoundingBox().zmax,
                    )
                ],
                "bolt_grips_mm": {bolt.name: bolt.grip for bolt in item["bolts"]},
                "edge_margins_mm": item["edge_margins_mm"],
                "conditional_4d_target_mm": CONDITIONAL_4D_MM,
            }
            for name, item in pair.items()
        },
        "collisions": collisions,
        "obstructions": [name for name, hits in collisions.items() if hits],
        "gates": gates,
        "minimum_cleat_edge_margin_mm": round(edge_minimum, 6),
        "decision": "REVISE",
        "reason": (
            "The shortened 2x2 trial lacks conditional 4D bolt-edge margins; "
            "complete joint resistance and purchased stacks are unverified."
        ),
        "strength_checked": False,
        "drilling_released": False,
        "fabrication_released": False,
    }


if __name__ == "__main__":
    print(json.dumps(screen(), indent=2, sort_keys=True))
