"""Finite outer/top barrel-trial conflicts in the exact owner-review assembly.

This reports geometry only. Candidate bores are envelopes, not wood cuts or a
drilling plan; a clear finite screen cannot qualify hardware or structure.
"""

import json
from itertools import combinations

from scripts import owner_layout_protected as protected
from scripts import simple_owner_duty_ledger as ledger
from scripts.owner_barrel_layout_assembly import FAMILY_STATIONS, build_assembly

SOURCE_ID = "owner-barrel-outer-top-protected-probe-v1"
TOL_MM3 = 1.0


def _hits(candidate, targets):
    return {
        name: round(volume, 6)
        for name, target in targets.items()
        if (volume := protected._volume(candidate, target)) > TOL_MM3
    }


def _station_rows(assembly, station):
    barrels = {
        f"barrel/{name}": shape
        for name, shape in assembly["barrels"].items()
        if assembly["barrel_station"][name] == station
    }
    bolts = {
        f"bolt/{name}/{role}": shape
        for name, roles in assembly["stacks"].items()
        if assembly["bolt_station"][name] == station
        for role, shape in roles.items()
    }
    prefix = f"barrel_trial_{station}_"
    paths = {
        f"drill/{name}": shape
        for name, shape in assembly["drilling_paths"].items()
        if name.startswith(prefix)
    }
    paths.update(
        {
            f"access/{name}": shape
            for name, shape in assembly["access_paths"].items()
            if name.startswith(prefix)
        }
    )
    if len(barrels) != 2 or len(bolts) != 2 or len(paths) != 8:
        raise ValueError(f"{station}: incomplete outer/top trial inventory")
    return barrels | bolts, paths


def probe(assembly=None):
    """Screen eight station inventories without changing any candidate pose."""
    assembly = build_assembly() if assembly is None else assembly
    stations = FAMILY_STATIONS["outer_top8"]
    duties = ledger.selected_duties()
    fixed = protected.inventory()
    if set(stations) != {
        name
        for name, family in assembly["diagnostics"]["station_family"].items()
        if family == "outer_top8"
    }:
        raise ValueError("Outer/top integrated duty partition changed")
    rows, result = {}, {}
    for station in stations:
        physical, paths = _station_rows(assembly, station)
        all_shapes = physical | paths
        fixed_hits = {
            name: hits
            for name, hits in protected.hits(all_shapes, fixed).items()
            if hits
        }
        unrelated = {
            name: shape
            for name, shape in assembly["wood"].items()
            if name not in duties[station]["timber"]
        }
        wood_hits = {
            name: hits
            for name, shape in all_shapes.items()
            if (hits := _hits(shape, unrelated))
        }
        rows[station] = (physical, paths)
        result[station] = {
            "fixed_protected_hits_mm3": fixed_hits,
            "unrelated_wood_hits_mm3": wood_hits,
            "disposition": "REVISE" if fixed_hits or wood_hits else "UNVERIFIED",
        }

    same_family_physical, same_family_paths = {}, {}
    for first, second in combinations(stations, 2):
        first_physical, first_paths = rows[first]
        second_physical, second_paths = rows[second]
        for first_name, first_shape in first_physical.items():
            for second_name, second_shape in second_physical.items():
                if (volume := protected._volume(first_shape, second_shape)) > TOL_MM3:
                    same_family_physical[f"{first_name}|{second_name}"] = round(
                        volume, 6
                    )
        for path_name, path_shape in first_paths.items():
            same_family_paths.update(
                {
                    f"{path_name}|{name}": round(volume, 6)
                    for name, shape in second_physical.items()
                    if (volume := protected._volume(path_shape, shape)) > TOL_MM3
                }
            )
        for path_name, path_shape in second_paths.items():
            same_family_paths.update(
                {
                    f"{path_name}|{name}": round(volume, 6)
                    for name, shape in first_physical.items()
                    if (volume := protected._volume(path_shape, shape)) > TOL_MM3
                }
            )
    return {
        "source_id": SOURCE_ID,
        "baseline": "compact-floor-flush-kerf-right",
        "inventory": {
            "stations": len(stations),
            "fixed_panel_screws": len(assembly["panel_connections"]),
            "retained_frame_bolts": len(assembly["frame_connections"]),
            "protected": fixed["counts"],
        },
        "stations": result,
        "same_family_physical_hits_mm3": same_family_physical,
        "same_family_path_to_physical_hits_mm3": same_family_paths,
        "cross_family_physical_hits_mm3": assembly["diagnostics"][
            "cross_family_physical_hits_mm3"
        ],
        "cross_family_path_hits_mm3": assembly["diagnostics"][
            "cross_family_drill_access_hits_mm3"
        ],
        "limits": (
            "Nominal finite geometry only; same-station intended contacts, delivered "
            "heads/washers/tool sweeps, actual hold-bolt lengths, thread engagement, "
            "wood strength and joint forces are not qualified"
        ),
        "layout_approved": False,
        "drilling_released": False,
        "fabrication_released": False,
        "structural_released": False,
    }


if __name__ == "__main__":
    print(json.dumps(probe(), indent=2, sort_keys=True))
