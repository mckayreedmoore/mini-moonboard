"""Detached PB06 bottom-center full-section bolted-cleat geometry trial."""

import json

import cadquery as cq

from scripts import simple_pb03_lower_center_pair as lower
from scripts import simple_pb06_upper_center_native as pb06
from scripts import simple_rail_joint_comparison as rail_basis

TARGET_STATIONS = (
    "clip_horizontal_bottom_left_2",
    "clip_horizontal_bottom_right_1",
)
SPECS = {
    name: lower.StationSpec(
        name,
        side,
        side,
        "right" if side == "left" else "left",
        f"base_principal_center_{side}",
        f"base_rail_bottom_{side}",
        f"pb06_bottom_center_{side}_block",
        f"pb06_bottom_center_{side}",
    )
    for name, side in zip(TARGET_STATIONS, ("left", "right"), strict=True)
}


def _axis(row):
    return cq.Solid.makeCylinder(row.diameter / 2, row.length, row.start, row.direction)


def _hits(shape, obstacles):
    return {
        name: round(volume, 6)
        for name, other in obstacles.items()
        if (volume := lower._intersection_volume(shape, other)) > lower.TOL_MM3
    }


def _margin(shape, point, through_axis):
    """Signed projected distance to each face; cut-angle capacity remains unchecked."""
    vertices = shape.Vertices()
    axes = ((1, 0, 0), (0, *rail_basis.T), (0, *rail_basis.N))
    out = {}
    for label, axis in zip(("x", "t", "n"), axes, strict=True):
        if label == through_axis:
            continue
        values = [v.Center().dot(cq.Vector(*axis)) for v in vertices]
        coordinate = cq.Vector(*point).dot(cq.Vector(*axis))
        out[f"{label}_low"] = round(coordinate - min(values), 6)
        out[f"{label}_high"] = round(max(values) - coordinate, 6)
    return out


def screen(module=None):
    """Keep both legacy duties live while checking a detached two-cleat option."""
    module = pb06.PB06Native() if module is None else module
    source = pb06.screen(module)
    if module.KEY != pb06.SOURCE_ID or source["inventory"]["blocks"] != 10:
        raise ValueError("PB06 ten-block source changed")
    stations = {row[0]: row for row in module.stations()}
    if set(TARGET_STATIONS) - set(stations):
        raise ValueError("PB06 bottom-center legacy stations absent")
    wood = {part.name: part.shape for part in module.wood_parts()}
    parts = {part.name: part.shape for part in module.parts()}
    rows = tuple(module.connections())
    target_sds = tuple(
        row
        for row in rows
        if any(row.name.startswith(station + "_") for station in TARGET_STATIONS)
    )
    other_sds = tuple(
        row
        for row in rows
        if row.kind == "screw"
        and row.name.startswith("clip_")
        and row not in target_sds
    )
    frame = tuple(
        row for row in rows if row.kind == "bolt" and not row.name.startswith("pb03_")
    )
    panel = tuple(module.panel_connections())
    if (len(target_sds), len(other_sds), len(frame), len(panel)) != (12, 60, 12, 66):
        raise ValueError("PB06 protected axes or legacy duties changed")
    for station, spec in SPECS.items():
        if stations[station][4:] != (spec.rail_name, spec.upright_name):
            raise ValueError(f"{station}: target members changed")
    fixed = lower._fixed_axis_solids(panel)
    pair = {
        station: lower._build_station(spec, wood, wood, fixed, rail_n_offset_mm=80.159)
        for station, spec in SPECS.items()
    }
    reference = module.pb03_geometries()
    if len(reference) != 10:
        raise ValueError("PB06 block inventory changed")
    protected = {
        "ten_blocks": {row.block_name: row.block for row in reference.values()},
        "ten_block_bores": {
            name: shape
            for item in reference.values()
            for name, shape in item.bores.items()
        },
        "ten_block_stacks": {
            f"{name}/{role}": shape
            for item in reference.values()
            for name, stack in item.stacks.items()
            for role, shape in stack.items()
        },
        "frame_axes": {row.name: _axis(row) for row in frame},
        "panel_axes": fixed,
        "panels": {
            name: shape
            for name, shape in wood.items()
            if name.startswith(("main_", "kicker_"))
        },
        "other_legacy_axes": {row.name: _axis(row) for row in other_sds},
        "other_legacy_angles": {
            name: parts[name]
            for name in module.legacy_proxy_stations()
            if name not in TARGET_STATIONS
        },
    }
    features = {}
    for station, item in pair.items():
        features[f"block/{station}"] = item.block
        features.update({f"bore/{name}": shape for name, shape in item.bores.items()})
        features.update(
            {
                f"stack/{name}/{role}": shape
                for name, stack in item.stacks.items()
                for role, shape in stack.items()
            }
        )
        features.update(
            {
                f"tool/{name}/{end}": shape
                for name, ends in item.tools.items()
                for end, shape in ends.items()
            }
        )
    hits = {
        family: {
            f"{feature}|{name}": volume
            for feature, shape in features.items()
            for name, volume in _hits(shape, obstacles).items()
        }
        for family, obstacles in protected.items()
    }
    margins = {}
    block_margins = {}
    for station, item in pair.items():
        margins[station] = {
            bolt.name: _margin(
                wood[bolt.members[0]],
                bolt.start.toTuple(),
                "x" if bolt.members[0] == item.upright_name else "t",
            )
            for bolt in item.bolts
        }
        block_margins[station] = {
            bolt.name: _margin(
                item.block,
                bolt.start.toTuple(),
                "x" if bolt.members[0] == item.upright_name else "t",
            )
            for bolt in item.bolts
        }
    local_clear = all(
        item.report["collision_clear"]
        and item.report["access_clear"]
        and item.report["complete_bores"]
        for item in pair.values()
    )
    clearance = local_clear and not any(hits.values())
    minimum = min(
        value
        for station in (*margins.values(), *block_margins.values())
        for bolt in station.values()
        for value in bolt.values()
    )
    decision = (
        "ADVANCE_GEOMETRY_ONLY"
        if clearance and minimum >= 4 * lower.BOLT_DIAMETER_MM
        else "REVISE"
    )
    constraints = [
        f"{station}/{bolt}: incomplete nominal bore through both intended members"
        for station, item in pair.items()
        for bolt, complete in item.report["complete_bores_by_bolt"].items()
        if not complete
    ]
    constraints += [
        f"{station}: nominal cleat intersects {name} ({volume} mm3)"
        for station, item in pair.items()
        for name, volume in item.report["block_unrelated_timber_hits_mm3"].items()
    ]
    if minimum < 4 * lower.BOLT_DIAMETER_MM:
        constraints.append("signed projected host/cleat margin below conditional 4D")
    constraints += [
        f"protected {family}: {len(entries)} candidate intersections"
        for family, entries in hits.items()
        if entries
    ]
    return {
        "schema": "simple_pb06_horizontal_bottom_pair/v1",
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
        "local": {station: item.report for station, item in pair.items()},
        "protected_hits_mm3": hits,
        "signed_member_edge_margins_mm": margins,
        "signed_cleat_edge_margins_mm": block_margins,
        "minimum_signed_member_edge_margin_mm": minimum,
        "conditional_4d_target_mm": 4 * lower.BOLT_DIAMETER_MM,
        "nominal_washer_diameter_mm": lower.WASHER_DIAMETER_MM,
        "nominal_washer_seats_by_projection": minimum >= lower.WASHER_DIAMETER_MM / 2,
        "binding_constraints": constraints,
        "decision": decision,
        "strength_checked": False,
        "exact_retail_hardware_selected": False,
        "drilling_released": False,
        "fabrication_released": False,
    }


if __name__ == "__main__":
    print(json.dumps(screen(), indent=2, sort_keys=True))
