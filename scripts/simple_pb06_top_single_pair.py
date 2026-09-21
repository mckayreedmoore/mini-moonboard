"""Detached full-section top-outer pair on actual PB06 geometry; no release."""

import json
from unittest.mock import patch

import cadquery as cq

from scripts import simple_pb03_lower_center_pair as lower
from scripts import simple_pb06_upper_center_native as pb06
from scripts.simple_pb06_horizontal_bottom_pair import _margin

TARGET_STATIONS = ("clip_single_top_left_1", "clip_single_top_right_2")
BLOCK_X_MM = 95.25
RAIL_X_OFFSETS_MM = (26.0, 70.0)
SPECS = {
    name: lower.StationSpec(
        name,
        side,
        "right" if side == "left" else "left",
        "left" if side == "left" else "right",
        f"base_side_{side}",
        "base_rail_top",
        f"pb06_top_single_{side}_block",
        f"pb06_top_single_{side}",
    )
    for name, side in zip(TARGET_STATIONS, ("left", "right"), strict=True)
}


def _axis(row):
    return cq.Solid.makeCylinder(row.diameter / 2, row.length, row.start, row.direction)


def _hits(features, obstacles):
    return {
        f"{name}|{target}": round(volume, 6)
        for name, shape in features.items()
        for target, other in obstacles.items()
        if (volume := lower._intersection_volume(shape, other)) > lower.TOL_MM3
    }


def _features(item):
    """Use complete nominal shafts, not the shorter generic bore envelope."""
    result = {f"block/{item.station}": item.block}
    nominal = {}
    for bolt in item.bolts:
        length = 203.2 if bolt.members[0] == item.upright_name else 127.0
        nominal[bolt.name] = length
        axis = bolt.direction.normalized()
        start = bolt.start + axis * (lower.END_ALLOWANCE_MM - 2.0)
        result[f"shaft/{bolt.name}"] = cq.Solid.makeCylinder(
            lower.BOLT_DIAMETER_MM / 2, length, start, axis
        )
        result[f"bore/{bolt.name}"] = item.bores[bolt.name]
        for role, shape in item.stacks[bolt.name].items():
            if role != "shaft":
                result[f"stack/{bolt.name}/{role}"] = shape
        for end, shape in item.tools[bolt.name].items():
            result[f"tool/{bolt.name}/{end}"] = shape
    return result, nominal


def screen(module=None):
    """Screen only this pair; the twelve target SDS remain in PB06 itself."""
    module = pb06.PB06Native() if module is None else module
    source = pb06.screen(module)
    if module.KEY != pb06.SOURCE_ID or source["inventory"]["blocks"] != 10:
        raise ValueError("PB06 ten-block source changed")
    stations = {row[0]: row for row in module.stations()}
    for name, spec in SPECS.items():
        if stations[name][4:] != (spec.rail_name, spec.upright_name):
            raise ValueError(f"{name}: top station members changed")
    wood = {part.name: part.shape for part in module.wood_parts()}
    parts = {part.name: part.shape for part in module.parts()}
    rows = tuple(module.connections())
    target = tuple(
        row
        for row in rows
        if any(row.name.startswith(name + "_") for name in TARGET_STATIONS)
    )
    other = tuple(
        row
        for row in rows
        if row.kind == "screw" and row.name.startswith("clip_") and row not in target
    )
    frame = tuple(
        row for row in rows if row.kind == "bolt" and not row.name.startswith("pb03_")
    )
    panels = tuple(module.panel_connections())
    if (len(target), len(other), len(frame), len(panels)) != (12, 60, 12, 66):
        raise ValueError("PB06 protected axis inventory changed")
    with (
        patch.object(lower, "BLOCK_X_MM", BLOCK_X_MM),
        patch.object(lower, "RAIL_X_OFFSETS_MM", RAIL_X_OFFSETS_MM),
    ):
        pair = {
            name: lower._build_station(
                spec,
                wood,
                wood,
                lower._fixed_axis_solids(panels),
                rail_n_offset_mm=80.159,
            )
            for name, spec in SPECS.items()
        }
    reference = module.pb03_geometries()
    if len(reference) != 10:
        raise ValueError("PB06 existing block inventory changed")
    protected_common = {
        "existing_blocks": {row.block_name: row.block for row in reference.values()},
        "existing_bores": {
            name: shape
            for item in reference.values()
            for name, shape in item.bores.items()
        },
        "existing_stacks": {
            f"{name}/{role}": shape
            for item in reference.values()
            for name, stack in item.stacks.items()
            for role, shape in stack.items()
        },
        "existing_tools": {
            f"{name}/{end}": shape
            for item in reference.values()
            for name, ends in item.tools.items()
            for end, shape in ends.items()
        },
        "frame_axes": {row.name: _axis(row) for row in frame},
        "panel_axes": {row.name: _axis(row) for row in panels},
        "panels": {
            name: shape
            for name, shape in wood.items()
            if name.startswith(("main_", "kicker_"))
        },
        "retained_legacy_axes": {row.name: _axis(row) for row in other},
        "retained_legacy_angles": {
            name: parts[name]
            for name in module.legacy_proxy_stations()
            if name not in TARGET_STATIONS
        },
    }
    features = {name: _features(item) for name, item in pair.items()}
    hits = {}
    for station, (items, _) in features.items():
        item = pair[station]
        unrelated = {
            name: shape
            for name, shape in wood.items()
            if name not in (item.rail_name, item.upright_name)
            and not name.startswith(("main_", "kicker_"))
        }
        opposite = next(name for name in TARGET_STATIONS if name != station)
        protected = {
            **protected_common,
            "unrelated_wood": unrelated,
            "other_trial": features[opposite][0],
        }
        hits[station] = {
            family: _hits(items, obstacles) for family, obstacles in protected.items()
        }
    margins = {
        station: {
            bolt.name: {
                "receiver": _margin(
                    wood[bolt.members[0]],
                    bolt.start.toTuple(),
                    "x" if bolt.members[0] == item.upright_name else "t",
                ),
                "block": _margin(
                    item.block,
                    bolt.start.toTuple(),
                    "x" if bolt.members[0] == item.upright_name else "t",
                ),
            }
            for bolt in item.bolts
        }
        for station, item in pair.items()
    }
    minimum = min(
        value
        for station in margins.values()
        for bolt in station.values()
        for member in bolt.values()
        for value in member.values()
    )
    local_clear = all(
        item.report["contact_verified"]
        and item.report["complete_bores"]
        and item.report["collision_clear"]
        and item.report["access_clear"]
        for item in pair.values()
    )
    collision_clear = not any(
        family for station in hits.values() for family in station.values()
    )
    decision = (
        "ADVANCE_GEOMETRY_ONLY"
        if local_clear and collision_clear and minimum >= 4 * lower.BOLT_DIAMETER_MM
        else "REVISE"
    )
    return {
        "schema": "simple_pb06_top_single_pair/v1",
        "pb06_source_fingerprint_sha256": source["source_fingerprint_sha256"],
        "target_stations": list(TARGET_STATIONS),
        "inventory": {
            "existing_blocks": 10,
            "candidate_blocks": 2,
            "candidate_bolts": 8,
            "target_sds_axes_retained": 12,
            "other_sds_axes_retained": 60,
            "frame_axes": 12,
            "panel_kicker_axes": 66,
        },
        "candidate_full_section_mm": [
            BLOCK_X_MM,
            lower.BLOCK_T_MM,
            lower.BLOCK_LENGTH_MM,
        ],
        "local": {name: item.report for name, item in pair.items()},
        "protected_hits_mm3": hits,
        "receiving_member_margins_mm": margins,
        "minimum_signed_margin_mm": minimum,
        "conditional_4d_target_mm": 4 * lower.BOLT_DIAMETER_MM,
        "full_nominal_shaft_lengths_mm": {
            bolt: length
            for _, lengths in features.values()
            for bolt, length in lengths.items()
        },
        "decision": decision,
        "strength_checked": False,
        "exact_retail_hardware_selected": False,
        "drilling_released": False,
        "fabrication_released": False,
    }


if __name__ == "__main__":
    print(json.dumps(screen(), indent=2, sort_keys=True))
