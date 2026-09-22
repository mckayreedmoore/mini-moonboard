"""Detached 60 mm outer-rail barrel-setback trial for ordinary 6 in bolts.

This does not edit the owner viewer, selected candidate, or protected axes.
The Hillman barrel and bolt dimensions remain nominal, unqualified envelopes.
"""

import json

import cadquery as cq

from scripts import owner_barrel_rail_layout as rail
from scripts import owner_layout_protected as protected
from scripts.export_owner_barrel_scene import build_viewer_assembly
from scripts.simple_owner_duty_ledger import selected_duties

SCHEMA = "owner_barrel_outer_rail_setback_probe/v1"
FAMILIES = frozenset({"bottom_outer", "lower_outer", "upper_outer"})
TRIAL_SETBACK_MM = 60.0
TRIAL_BOLT_LENGTH_MM = 152.4
HIT_TOL_MM3 = protected.HIT_TOL_MM3


def _overlap(first, second):
    a, b = first.BoundingBox(), second.BoundingBox()
    if any(
        high <= low
        for low, high in (
            (max(a.xmin, b.xmin), min(a.xmax, b.xmax)),
            (max(a.ymin, b.ymin), min(a.ymax, b.ymax)),
            (max(a.zmin, b.zmin), min(a.zmax, b.zmax)),
        )
    ):
        return 0.0
    volume = protected._volume(first, second)
    return round(volume, 6) if volume > HIT_TOL_MM3 else 0.0


def _row_record(row):
    direction = row["bolt_direction"]
    start = (
        row["wood_seat"] - direction * rail.continuation.WASHER_THICKNESS_SENSITIVITY_MM
    )
    axis = (row["thread_center"] - start).dot(direction)
    barrel_far_wall = axis + rail.continuation.BARREL_OD_MM / 2
    bore_end = max(
        (vertex.Center() - start).dot(direction)
        for vertex in row["machine_bore"].Vertices()
    )
    tip = start + direction * TRIAL_BOLT_LENGTH_MM
    shaft = cq.Solid.makeCylinder(
        rail.continuation.THREAD_MAJOR_MM / 2,
        TRIAL_BOLT_LENGTH_MM,
        start,
        direction,
    )
    return {
        "barrel": row["barrel"],
        "shaft": shaft,
        "record": {
            "axis_from_bolt_start_mm": round(axis, 6),
            "barrel_far_wall_from_bolt_start_mm": round(barrel_far_wall, 6),
            "machine_bore_end_from_bolt_start_mm": round(bore_end, 6),
            "nominal_length_window_for_axis_to_far_wall_mm": [
                round(axis, 6),
                round(barrel_far_wall, 6),
            ],
            "nominal_tip_past_axis_mm": round(TRIAL_BOLT_LENGTH_MM - axis, 6),
            "nominal_tip_to_barrel_far_wall_mm": round(
                barrel_far_wall - TRIAL_BOLT_LENGTH_MM, 6
            ),
            "nominal_tip_to_machine_bore_end_mm": round(
                bore_end - TRIAL_BOLT_LENGTH_MM, 6
            ),
            "smallest_nominal_longitudinal_margin_mm": round(
                min(
                    TRIAL_BOLT_LENGTH_MM - axis,
                    barrel_far_wall - TRIAL_BOLT_LENGTH_MM,
                ),
                6,
            ),
            "tip_xyz_mm": [round(value, 6) for value in tip.toTuple()],
            "barrel_setback_from_butt_mm": TRIAL_SETBACK_MM,
        },
    }


def probe(assembly=None):
    """Compare six trial stations with other current-viewer hardware."""
    assembly = build_viewer_assembly() if assembly is None else assembly
    duties = selected_duties()
    stations = tuple(
        name for name, duty in duties.items() if duty["family"] in FAMILIES
    )
    if (
        len(stations) != 6
        or len(assembly["panel_connections"]) != 66
        or len(assembly["frame_connections"]) != 12
        or any(assembly["station_modes"].get(name) != "direct" for name in stations)
        or assembly["diagnostics"]["producer_diagnostics"]["outer_top8"][
            "viewer_trial_outer_header_forward_y_mm"
        ]
        != -85.0
    ):
        raise ValueError("Exact current owner barrel viewer inventory changed")
    built = rail.build_geometry(
        wood=assembly["wood"],
        stations=stations,
        barrel_setback_mm=TRIAL_SETBACK_MM,
        bolt_length_mm=TRIAL_BOLT_LENGTH_MM,
        cut_wood=False,
    )
    base_screen = rail.screen(built)
    trial_physical = {}
    records = {}
    for station in stations:
        pose = built["stations"][station]
        screen = base_screen["stations"][station]
        if len(pose["rows"]) != 2:
            raise ValueError(f"{station}: expected two distinct barrel rows")
        records[station] = {
            "source_status": screen["geometry_status"],
            "source_bolt_lengths_mm": screen["nominal_bolt_lengths_mm"],
            "direct_butt_available": screen["direct_butt_available"],
            "barrels_contained_in_rail": screen["barrels_contained_in_rail"],
            "machine_bore_meets_barrel_bore": screen["machine_bore_meets_barrel_bore"],
            "protected_hits_mm3": screen["protected_hits_mm3"],
            "unrelated_wood_hits_mm3": screen["unrelated_wood_hits_mm3"],
            "rows": {},
        }
        for row in pose["rows"]:
            result = _row_record(row)
            name = row["name"]
            trial_physical[f"barrel/{name}"] = (station, result["barrel"])
            trial_physical[f"bolt/{name}_bolt/shaft"] = (station, result["shaft"])
            records[station]["rows"][name] = result["record"]

    retained_physical = {
        f"barrel/{name}": (assembly["barrel_station"][name], shape)
        for name, shape in assembly["barrels"].items()
        if assembly["barrel_station"][name] not in stations
    }
    retained_physical.update(
        {
            f"bolt/{name}/{role}": (assembly["bolt_station"][name], shape)
            for name, stack in assembly["stacks"].items()
            if assembly["bolt_station"][name] not in stations
            for role, shape in stack.items()
        }
    )
    peer_hits = {}
    for name, (station, shape) in trial_physical.items():
        for other, (owner, target) in {**trial_physical, **retained_physical}.items():
            if owner == station or other <= name and other in trial_physical:
                continue
            if volume := _overlap(shape, target):
                peer_hits[f"{name}|{other}"] = volume

    fixed = protected.inventory()
    geometry_clear = (
        all(
            row["source_status"] == "DIRECT_TRIAL_GEOMETRY_ONLY"
            and all(
                bolt["nominal_tip_past_axis_mm"] > 0
                and bolt["nominal_tip_to_barrel_far_wall_mm"] > 0
                and bolt["nominal_tip_to_machine_bore_end_mm"] > 0
                for bolt in row["rows"].values()
            )
            for row in records.values()
        )
        and not peer_hits
    )
    return {
        "schema": SCHEMA,
        "status": "detached_nominal_geometry_sensitivity_only",
        "trial_barrel_setback_from_butt_mm": TRIAL_SETBACK_MM,
        "trial_bolt_length_mm": TRIAL_BOLT_LENGTH_MM,
        "stations": records,
        "trial_bolt_count": len(trial_physical) // 2,
        "fixed_inventory": fixed["counts"],
        "peer_hardware_hits_mm3": peer_hits,
        "nominal_geometry_clear": geometry_clear,
        "retail_lead": {
            "store": "Home Depot",
            "brand": "Everbilt",
            "model": "805436",
            "description": "1/4-20 x 6-in fully threaded galvanized hex bolt",
            "url": "https://www.homedepot.com/p/204633311",
        },
        "limits": (
            "A nominal 6-in trial on shifted axes only. Thread engagement, actual "
            "barrel thread-axis location, delivered dimensions, Grade A307 joint "
            "resistance, tolerance, wood breakout, service tooling, repeated "
            "demounting, backer attachment, and whole-frame forces are unverified."
        ),
        "selected_hardware": False,
        "thread_engagement_verified": False,
        "capacity_verified": False,
        "drilling_released": False,
        "fabrication_released": False,
    }


if __name__ == "__main__":
    print(json.dumps(probe(), indent=2, sort_keys=True))
