"""Detached PB05 common-length, eight-station geometry screen; no release."""

import json
import math
from dataclasses import replace
from itertools import combinations
from unittest.mock import patch

from scripts import simple_pb03_bottom_outer_pair as bottom
from scripts import simple_pb03_cross_family as cross
from scripts import simple_pb03_lower_center_pair as lower
from scripts import simple_pb03_upper_outer_pair as upper
from scripts import simple_pb04_native as pb04
from scripts import simple_pb05_narrow_outer_screen as narrow
from scripts import simple_pb05_native as pb05

SIX_INCH_MM = 152.4
NET_END_ALLOWANCE_MM = 3.0
GRAIN_END_ALLOWANCE_MM = 4 * lower.BOLT_DIAMETER_MM
STATIONS = (*lower.TARGET_STATIONS, *pb05.OUTER_STATIONS)
SPECS = {**lower.STATION_SPECS, **upper.STATION_SPECS, **bottom.STATION_SPECS}


def _openings(geometry):
    """Provisional end reserves for every bore and no-pocket washer seat."""
    rows = {}
    for bolt in geometry.bolts:
        washer_diameter = (
            narrow.hardware.WASHER_OUTSIDE_DIAMETER_MM
            if geometry.station in pb05.OUTER_STATIONS
            and bolt.members[0] == geometry.upright_name
            else lower.WASHER_DIAMETER_MM
        )
        n = (
            lower.UPRIGHT_N_OFFSETS_MM[int(bolt.name.rsplit("_", 1)[1]) - 1]
            if bolt.members[0] == geometry.upright_name
            else geometry.report["rail_bore_n_offset_mm"]
        )
        for role, radius in (
            ("bore", lower.BORE_DIAMETER_MM / 2),
            ("washer", washer_diameter / 2),
        ):
            rows[f"{bolt.name}/{role}"] = {
                "near_net_mm": round(n - radius, 6),
                "far_net_mm": round(geometry.block_length_mm - n - radius, 6),
                "near_center_mm": round(n, 6),
                "far_center_mm": round(geometry.block_length_mm - n, 6),
            }
    return rows


def _end_gates(geometry, openings):
    end_clear = all(
        min(row["near_net_mm"], row["far_net_mm"]) >= NET_END_ALLOWANCE_MM
        and (
            not name.endswith("/bore")
            or min(row["near_center_mm"], row["far_center_mm"])
            >= GRAIN_END_ALLOWANCE_MM
        )
        for name, row in openings.items()
    )
    tool_end_clear = all(
        row["near_center_mm"] - lower.TOOL_DIAMETER_MM / 2 >= NET_END_ALLOWANCE_MM
        and row["far_center_mm"] - lower.TOOL_DIAMETER_MM / 2 >= NET_END_ALLOWANCE_MM
        for name, row in openings.items()
        if name.endswith("/bore")
    )
    butt = geometry.report["butt_faces_x_mm"]["upright"]
    sign = 1 if geometry.rail_extension_direction == "right" else -1
    offsets = sorted(
        sign * (bolt.start.x - butt)
        for bolt in geometry.bolts
        if bolt.members[0] == geometry.rail_name
    )
    width = geometry.report["block_dimensions_mm"][0]
    thickness = geometry.report["block_dimensions_mm"][1]
    radius = lower.TOOL_DIAMETER_MM / 2
    x_reserves = [min(x - radius, width - x - radius) for x in offsets]
    return (
        {
            "provisional_grain_end": end_clear,
            "provisional_bolt_edge": min(
                *(min(x, width - x) for x in offsets), thickness / 2
            )
            >= 1.5 * lower.BOLT_DIAMETER_MM,
            "tool_n_end": tool_end_clear,
            "rail_tool_x_edge": min(x_reserves) >= NET_END_ALLOWANCE_MM
            and offsets[1] - offsets[0] >= lower.TOOL_DIAMETER_MM,
        },
        offsets,
        x_reserves,
    )


def _envelope(geometry):
    """Broad-phase bounds for all solids used by the exact pair screen."""
    boxes = [
        shape.BoundingBox()
        for shape in (
            geometry.block,
            *geometry.bores.values(),
            *(shape for stack in geometry.stacks.values() for shape in stack.values()),
            *(shape for ends in geometry.tools.values() for shape in ends.values()),
        )
    ]
    return tuple(
        (
            min(getattr(box, axis + "min") for box in boxes),
            max(getattr(box, axis + "max") for box in boxes),
        )
        for axis in "xyz"
    )


def _envelopes_overlap(first, second):
    return all(
        left[0] <= right[1] and right[0] <= left[1]
        for left, right in zip(first, second, strict=True)
    )


def _nominal_stack(geometry, bolt):
    """Check whole 8/5-in shafts; retain generic seats except outer uprights."""
    if (
        geometry.station in pb05.OUTER_STATIONS
        and bolt.members[0] == geometry.upright_name
    ):
        return narrow._installed_upright(bolt)
    stack = dict(geometry.stacks[bolt.name])
    direction = bolt.direction.normalized()
    near = bolt.start + direction * lower.END_ALLOWANCE_MM
    length = (
        8 * narrow.hardware.MM_PER_IN
        if bolt.members[0] == geometry.upright_name
        else 5 * narrow.hardware.MM_PER_IN
    )
    stack["shaft"] = narrow.hardware._cylinder(
        (near - direction * 2.0).toTuple(),
        direction.toTuple(),
        length,
        lower.BOLT_DIAMETER_MM,
    )
    return stack


def screen(length_mm=SIX_INCH_MM):
    """Rebuild all eight at one stock length and check their simultaneous envelope."""
    if not math.isfinite(length_mm) or length_mm <= 0:
        raise ValueError("common block length must be positive and finite")
    module = pb05.PB05Native()
    reference = module.pb03_geometries()
    parts, finished, panels, _, connections = lower._source_inventory()
    panel_axes = tuple(module.panel_connections())
    frame_axes = tuple(
        row
        for row in module.connections()
        if row.kind == "bolt" and not row.name.startswith("pb03_")
    )
    source_frame = tuple(row for row in connections if row.kind == "bolt")
    if (
        module.KEY != pb05.SOURCE_ID
        or module.ACTIVE_FINGERPRINT != lower.EXPECTED_PB02_FINGERPRINT
        or set(reference) != set(STATIONS)
        or len(panel_axes) != 66
        or tuple(map(narrow._signature, panel_axes))
        != tuple(map(narrow._signature, panels))
        or len(frame_axes) != 12
        or tuple(map(narrow._signature, frame_axes))
        != tuple(map(narrow._signature, source_frame))
        or len(module.legacy_proxy_stations()) != 14
    ):
        raise ValueError("PB05 source or fixed kerf-right axes changed")
    axes = lower._fixed_axis_solids(panel_axes)
    geometries = {}
    for names, width, offsets in (
        (lower.TARGET_STATIONS, lower.BLOCK_X_MM, lower.RAIL_X_OFFSETS_MM),
        (pb05.OUTER_STATIONS, pb05.BLOCK_X_MM, pb05.RAIL_X_OFFSETS_MM),
    ):
        # ponytail: the shared PB03 builder reads these two producer constants.
        with (
            patch.object(lower, "BLOCK_X_MM", width),
            patch.object(lower, "RAIL_X_OFFSETS_MM", offsets),
        ):
            geometries.update(
                {
                    name: lower._build_station(
                        SPECS[name],
                        parts,
                        finished,
                        axes,
                        rail_n_offset_mm=(
                            pb04.SELECTED_OFFSET_MM
                            if name in upper.TARGET_STATIONS
                            else lower.RAIL_N_OFFSET_MM
                        ),
                        block_length_mm=length_mm,
                    )
                    for name in names
                }
            )
    if any(
        tuple(map(narrow._signature, geometry.bolts))
        != tuple(map(narrow._signature, reference[name].bolts))
        for name, geometry in geometries.items()
    ):
        raise ValueError("shortening moved a PB05 bolt axis")
    # ponytail: retain existing generic seats, but screen the whole nominal shafts.
    installed = {
        name: replace(
            geometry,
            stacks={
                bolt.name: _nominal_stack(geometry, bolt) for bolt in geometry.bolts
            },
        )
        for name, geometry in geometries.items()
    }
    fixed = {
        **{f"panel_axis/{name}": shape for name, shape in axes.items()},
        **{f"frame_axis/{row.name}": narrow._axis(row) for row in frame_axes},
        **{
            f"panel/{name}": shape
            for name, shape in finished.items()
            if name.startswith(("main_", "kicker_"))
        },
    }
    pair_hits = {}
    envelopes = {name: _envelope(row) for name, row in installed.items()}
    exact_pairs = 0
    for first, second in combinations(STATIONS, 2):
        if not _envelopes_overlap(envelopes[first], envelopes[second]):
            continue
        exact_pairs += 1
        pair = cross.screen_cross_family(
            {first: installed[first]}, {second: installed[second]}
        )
        hits = {
            key: value
            for key, value in pair.items()
            if key.endswith("hits_mm3") and value
        }
        if hits:
            pair_hits[f"{first}|{second}"] = hits
    station_rows = {}
    for name, geometry in installed.items():
        openings = _openings(geometry)
        end_gates, x_offsets, x_reserves = _end_gates(geometry, openings)
        local = geometry.report
        other_stacks = {
            f"{bolt}/{role}": shape
            for bolt, components in geometry.stacks.items()
            for role, shape in components.items()
        }
        # Local builder checks generic stack and fixed panel axes. Check the
        # installed outer envelopes against all fixed solids and other bolts.
        installed_hits = {}
        for bolt, components in geometry.stacks.items():
            unrelated = {
                **fixed,
                **{
                    f"own/{key}": shape
                    for key, shape in other_stacks.items()
                    if not key.startswith(bolt + "/")
                },
                **{
                    f"own_bore/{key}": shape
                    for key, shape in geometry.bores.items()
                    if key != bolt
                },
            }
            for role, shape in components.items():
                hits = narrow._hits(shape, unrelated)
                if hits:
                    installed_hits[f"{bolt}/{role}"] = hits
        fixed_hits = {
            "block": narrow._hits(geometry.block, fixed),
            "bores": {
                key: hits
                for key, shape in geometry.bores.items()
                if (hits := narrow._hits(shape, fixed))
            },
            "tools": {
                f"{bolt}/{end}": hits
                for bolt, ends in geometry.tools.items()
                for end, shape in ends.items()
                if (hits := narrow._hits(shape, fixed))
            },
        }
        gates = {
            "contact_and_complete_bores": local["contact_verified"]
            and local["complete_bores"],
            "local_collision_and_access": local["collision_clear"]
            and local["access_clear"],
            "installed_and_fixed_clear": not installed_hits
            and not any(fixed_hits.values()),
            **end_gates,
        }
        station_rows[name] = {
            "block_dimensions_mm": local["block_dimensions_mm"],
            "installed_shaft_volumes_mm3": {
                bolt.name: geometry.stacks[bolt.name]["shaft"].Volume()
                for bolt in geometry.bolts
            },
            "rail_x_offsets_from_butt_mm": x_offsets,
            "rail_tool_x_edge_reserves_mm": x_reserves,
            "end_openings_mm": openings,
            "local_hits_mm3": narrow._nonempty(
                {
                    key: value
                    for key, value in local.items()
                    if key.endswith("_hits_mm3")
                }
            ),
            "installed_hits_mm3": installed_hits,
            "fixed_hits_mm3": narrow._nonempty(fixed_hits),
            "gates": gates,
        }
    required_length = max(
        max(
            row["near_center_mm"] + GRAIN_END_ALLOWANCE_MM
            if name.endswith("/bore")
            else 0,
            row["near_center_mm"] + lower.TOOL_DIAMETER_MM / 2 + NET_END_ALLOWANCE_MM
            if name.endswith("/bore")
            else 0,
            2 * row["near_center_mm"] - row["near_net_mm"] + NET_END_ALLOWANCE_MM,
        )
        for station in station_rows.values()
        for name, row in station["end_openings_mm"].items()
    )
    passed = not pair_hits and all(
        all(row["gates"].values()) for row in station_rows.values()
    )
    return {
        "schema": "simple_pb05_short_block_screen/v1",
        "source_id": pb05.SOURCE_ID,
        "common_length_mm": length_mm,
        "provisional_minimum_end_length_mm": round(required_length, 6),
        "inventory": {
            "stations": len(geometries),
            "outer_blocks": 6,
            "center_blocks": 2,
            "panel_kicker_axes": len(panel_axes),
            "frame_bolt_axes": len(frame_axes),
            "new_bolt_axes": sum(len(row.bolts) for row in geometries.values()),
            "counterbores": 0,
        },
        "stations": station_rows,
        "station_pairs": {
            "total": len(STATIONS) * (len(STATIONS) - 1) // 2,
            "exact": exact_pairs,
            "separated_by_envelope": len(STATIONS) * (len(STATIONS) - 1) // 2
            - exact_pairs,
        },
        "simultaneous_pair_hits_mm3": pair_hits,
        "decision": "PASS_GEOMETRY_ONLY" if passed else "REVISE",
        "provisional_nds_basis": (
            "4D bolt-center, 1.5D bolt-edge, and 3-mm net-opening/tool-edge "
            "geometry screens only"
        ),
        "force_transfer": False,
        "strength_checked": False,
        "drilling_released": False,
        "fabrication_released": False,
    }


if __name__ == "__main__":
    print(json.dumps(screen(), indent=2, sort_keys=True))
