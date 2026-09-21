"""Detached upper-center pair against actual PB04 solids; geometry only."""

import json
import math

import cadquery as cq

from scripts import simple_pb03_cross_family as cross
from scripts import simple_pb03_lower_center_pair as lower
from scripts import simple_pb03_outer_counterbore_revision as pocket
from scripts import simple_pb03_upper_center_pair as upper_center
from scripts import simple_pb04_native as pb04


def _hits(first, others):
    return {
        name: round(volume, 6)
        for name, second in others.items()
        if (volume := lower._intersection_volume(first, second)) > lower.TOL_MM3
    }


def _axis(row):
    return cq.Solid.makeCylinder(row.diameter / 2, row.length, row.start, row.direction)


def _signature(row):
    return (
        row.name,
        row.start.toTuple(),
        row.direction.toTuple(),
        row.length,
        row.diameter,
        row.members,
        row.kind,
        row.grip,
    )


def _same_shape(first, second):
    return first.distance(second) < 1e-8 and math.isclose(
        first.Volume(), second.Volume(), abs_tol=1e-5
    )


def build_inputs():
    """Reuse PB03's complete pair builder; leave all PB04 legacy stations in place."""
    return upper_center.build_pair(), pb04.PB04Native()


def screen(*, pair=None, module=None, reference=None):
    """Screen every new solid/axis against actual PB04 inventory and fixed work."""
    if pair is None or module is None:
        if pair is not None or module is not None:
            raise ValueError("candidate pair and PB04 module must be supplied together")
        pair, module = build_inputs()
    if (
        module.KEY != pb04.SOURCE_ID
        or module.ACTIVE_FINGERPRINT != lower.EXPECTED_PB02_FINGERPRINT
    ):
        raise ValueError("PB04 source identity changed")
    reference = module.pb03_geometries() if reference is None else reference
    if set(pair) != set(upper_center.TARGET_STATIONS) or len(reference) != 8:
        raise ValueError("upper-center or PB04 station inventory changed")

    actual_parts = {part.name: part.shape for part in module.wood_parts()}
    source_parts, source_finished, source_panels, _, source_connections = (
        lower._source_inventory()
    )
    panel_axes = tuple(module.panel_connections())
    source_panel_by_name = {row.name: row for row in source_panels}
    frame_axes = tuple(
        row
        for row in module.connections()
        if row.kind == "bolt" and not row.name.startswith("pb03_")
    )
    source_frame = tuple(row for row in source_connections if row.kind == "bolt")
    legacy = tuple(
        row
        for row in module.connections()
        if any(
            row.name.startswith(station + "_")
            for station in upper_center.TARGET_STATIONS
        )
    )
    main_panels = {
        name: shape for name, shape in actual_parts.items() if name.startswith("main_")
    }
    all_panels = {
        name: shape
        for name, shape in actual_parts.items()
        if name.startswith(("main_", "kicker_"))
    }
    fixed_axes = lower._fixed_axis_solids(panel_axes)
    receiver_support = lower._receiver_support(panel_axes, source_parts)
    pockets, expected_cut = pocket.build_counterbored_blocks(reference)
    upper_outer = pb04.upper_revision.upper.TARGET_STATIONS
    block_names = {item.block_name for item in reference.values()}
    actual_blocks = {name: actual_parts[name] for name in block_names}
    cuts_match = all(
        _same_shape(actual_blocks[item.block_name], expected_cut.get(name, item.block))
        for name, item in reference.items()
    )

    # ponytail: one exact intersection loop covers blocks, bores, hardware, and tools.
    candidate_features = {
        f"block/{station}": item.block for station, item in pair.items()
    }
    candidate_features.update(
        {
            f"bore/{station}/{name}": shape
            for station, item in pair.items()
            for name, shape in item.bores.items()
        }
    )
    candidate_features.update(
        {
            f"stack/{station}/{name}/{role}": shape
            for station, item in pair.items()
            for name, stack in item.stacks.items()
            for role, shape in stack.items()
        }
    )
    candidate_features.update(
        {
            f"tool/{station}/{name}/{end}": shape
            for station, item in pair.items()
            for name, tools in item.tools.items()
            for end, shape in tools.items()
        }
    )
    families = {
        "pb04_blocks": {name: shape for name, shape in actual_blocks.items()},
        "pb04_bores": {
            f"{station}/{name}": shape
            for station, item in reference.items()
            for name, shape in item.bores.items()
        },
        "pb04_stacks": {
            f"{station}/{name}/{role}": shape
            for station, item in reference.items()
            for name, stack in item.stacks.items()
            for role, shape in stack.items()
        },
        "pb04_tools": {
            f"{station}/{name}/{end}": shape
            for station, item in reference.items()
            for name, tools in item.tools.items()
            for end, shape in tools.items()
        },
        "pb04_counterbores": pockets,
        "frame_bolt_axes": {row.name: _axis(row) for row in frame_axes},
        "panel_kicker_axes": fixed_axes,
        "main_panel_solids": main_panels,
        "kicker_solids": {
            name: shape
            for name, shape in all_panels.items()
            if name.startswith("kicker_")
        },
        "unrelated_timber": {
            name: shape
            for name, shape in source_finished.items()
            if name not in all_panels
            and name
            not in {
                member
                for item in pair.values()
                for member in (item.upright_name, item.rail_name)
            }
        },
    }
    collisions = {}
    for family, solids in families.items():
        collisions[family] = {
            f"{feature}|{name}": volume
            for feature, shape in candidate_features.items()
            for name, volume in _hits(shape, solids).items()
        }

    local = {station: item.report for station, item in pair.items()}
    pair_interactions = cross.screen_cross_family(
        {upper_center.TARGET_STATIONS[0]: pair[upper_center.TARGET_STATIONS[0]]},
        {upper_center.TARGET_STATIONS[1]: pair[upper_center.TARGET_STATIONS[1]]},
    )
    local_clear = all(
        row["collision_clear"] and row["access_clear"] and row["contact_verified"]
        for row in local.values()
    )
    source_preserved = (
        len(legacy) == 12
        and all(row.kind == "screw" for row in legacy)
        and len(frame_axes) == len(source_frame) == 12
        and tuple(map(_signature, frame_axes)) == tuple(map(_signature, source_frame))
        and len(panel_axes) == len(source_panel_by_name) == 66
        and all(
            _signature(row) == _signature(source_panel_by_name[row.name])
            for row in panel_axes
        )
        and len(main_panels) == 4
        and len(all_panels) == 6
        and all(
            _same_shape(shape, source_finished[name])
            for name, shape in all_panels.items()
        )
        and len(actual_blocks) == 8
        and len(pockets) == 12
        and cuts_match
        and all(
            reference[name].report["rail_bore_n_offset_mm"] == pb04.SELECTED_OFFSET_MM
            for name in upper_outer
        )
    )
    nearest_clearance = {
        "candidate_block_to_upper_outer_block": min(
            candidate.block.distance(actual_blocks[reference[name].block_name])
            for candidate in pair.values()
            for name in upper_outer
        ),
        "candidate_block_to_upper_outer_counterbore": min(
            candidate.block.distance(shape)
            for candidate in pair.values()
            for key, shape in pockets.items()
            if key.split("/", 1)[0] in upper_outer
        ),
    }
    gates = {
        "source_preserved": source_preserved,
        "candidate_inventory": sum(len(item.bolts) for item in pair.values()) == 8
        and all(
            len(item.bolts)
            == len(item.bores)
            == len(item.stacks)
            == len(item.tools)
            == 4
            for item in pair.values()
        ),
        "complete_candidate_bores": all(
            row["complete_bores"] for row in local.values()
        ),
        "fixed_receivers_supported": len(receiver_support) == 66
        and all(receiver_support.values()),
        "local_geometry_clear": local_clear,
        "pair_geometry_clear": pair_interactions[
            "all_cross_family_collision_gates_pass"
        ],
        "pb04_and_fixed_geometry_clear": not any(collisions.values()),
    }
    return {
        "schema": "simple_pb04_upper_center_detached/v1",
        "source_id": pb04.SOURCE_ID,
        "candidate_stations": list(pair),
        "pb04_block_names": sorted(actual_blocks),
        "shifted_upper_outer_rail_row_mm": pb04.SELECTED_OFFSET_MM,
        "nearest_clearance_mm": nearest_clearance,
        "inventory": {
            "legacy_stations_retained": len(upper_center.TARGET_STATIONS),
            "legacy_sds_axes_retained": len(legacy),
            "candidate_blocks": len(pair),
            "candidate_bolt_axes": sum(len(item.bolts) for item in pair.values()),
            "pb04_blocks": len(actual_blocks),
            "pb04_counterbored_blocks": len(expected_cut),
            "original_frame_bolt_axes": len(frame_axes),
            "fixed_panel_kicker_axes": len(panel_axes),
            "main_panel_solids": len(main_panels),
        },
        "stations": local,
        "pair_interactions": pair_interactions,
        "collision_hits_mm3": collisions,
        "gates": gates,
        "geometry_decision": "ADVANCE_GEOMETRY_ONLY"
        if all(gates.values())
        else "REVISE_GEOMETRY",
        "strength_checked": False,
        "installed_retail_stacks_checked": False,
        "drilling_released": False,
        "fabrication_released": False,
    }


if __name__ == "__main__":
    print(json.dumps(screen(), indent=2, sort_keys=True))
