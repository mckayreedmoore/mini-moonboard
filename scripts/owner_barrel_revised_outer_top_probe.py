"""Finite integrated collision screen of the revised barrel viewer's outer/top eight.

Uncut wood, nominal cutters and finite hardware envelopes are diagnostic only.
Missing viewer heads/washers are supplemented as explicitly provisional solids;
no delivered fastener, bit, driver or assembly sequence is qualified here.
"""

import json
from functools import lru_cache

import cadquery as cq

from scripts import export_owner_barrel_scene as viewer
from scripts import owner_barrel_outer_top_layout as outer
from scripts import owner_layout_protected as protected
from scripts import simple_cross_dowel_continuation as hardware
from scripts import simple_owner_duty_ledger as ledger
from scripts.owner_barrel_layout_assembly import FAMILY_STATIONS

SOURCE_ID = "owner-barrel-revised-outer-top-probe-v1"
TOL_MM3 = 1.0
HEAD_HEIGHT_MM = outer.VIEWER_HEADER_HEAD_HEIGHT_MM
HEAD_OD_MM = outer.VIEWER_HEADER_HEAD_OD_MM
WASHER_OD_MM = outer.VIEWER_HEADER_WASHER_OD_MM
WASHER_THICKNESS_MM = hardware.WASHER_THICKNESS_SENSITIVITY_MM


def _hits(shape, targets):
    return {
        name: round(volume, 6)
        for name, target in targets.items()
        if (volume := protected._volume(shape, target)) > TOL_MM3
    }


def _supplemental_stack(bolt):
    """Screen a nominal head/washer absent from the viewer; not selected stock."""
    axis = bolt.direction.normalized()
    return {
        "head": cq.Solid.makeCylinder(
            HEAD_OD_MM / 2, HEAD_HEIGHT_MM, bolt.start, -axis
        ),
        "washer": cq.Solid.makeCylinder(
            WASHER_OD_MM / 2, WASHER_THICKNESS_MM, bolt.start, axis
        ),
    }


def _station_geometry(assembly, station):
    """Keep exact station/row ownership while augmenting absent nominal heads."""
    physical, paths, rows = {}, {}, {}
    barrels = sorted(
        name for name, owner in assembly["barrel_station"].items() if owner == station
    )
    if len(barrels) != 2:
        raise ValueError(f"{station}: expected two barrel rows")
    for index, prefix in enumerate(barrels, 1):
        bolt_name = f"{prefix}_bolt"
        if (
            assembly["barrel_station"].get(prefix) != station
            or assembly["bolt_station"].get(bolt_name) != station
        ):
            raise ValueError(f"{station}: missing or misassigned row {index}")
        stack = dict(assembly["stacks"][bolt_name])
        if "shaft" not in stack or set(stack) - {"shaft", "head", "washer"}:
            raise ValueError(f"{station}: unexpected bolt stack at row {index}")
        if {"head", "washer"} <= set(stack):
            source = "viewer"
        elif set(stack) == {"shaft"}:
            stack.update(_supplemental_stack(assembly["bolts"][bolt_name]))
            source = "supplemental_provisional_envelope_not_in_viewer"
        else:
            raise ValueError(f"{station}: partial head/washer inventory")
        row_physical = {f"barrel/{prefix}": assembly["barrels"][prefix]}
        row_physical.update(
            {f"bolt/{bolt_name}/{role}": shape for role, shape in stack.items()}
        )
        row_drill = {
            f"drill/{name}": shape
            for name, shape in assembly["drilling_paths"].items()
            if name.startswith(f"{prefix}/")
        }
        row_access = {
            f"access/{name}": shape
            for name, shape in assembly["access_paths"].items()
            if name.startswith(f"{prefix}/")
        }
        if len(row_drill) not in (2, 3) or len(row_access) != 2:
            raise ValueError(f"{station}: incomplete path inventory at row {index}")
        if station in viewer.OUTER_HEADER_STATIONS:
            if source != "viewer" or f"drill/{prefix}/counterbore" not in row_drill:
                raise ValueError(f"{station}: recessed viewer stack missing")
        elif len(row_drill) != 2:
            raise ValueError(f"{station}: unexpected bore inventory at row {index}")
        if station in FAMILY_STATIONS["outer_top8"]:
            required_drill = {
                f"drill/{prefix}/{role}" for role in ("machine_bore", "barrel_bore")
            }
            required_access = {
                f"access/{prefix}/{role}" for role in ("bolt_access", "barrel_access")
            }
            if (
                not required_drill <= set(row_drill)
                or set(row_access) != required_access
            ):
                raise ValueError(f"{station}: revised outer/top path names changed")
        physical.update(row_physical)
        paths.update(row_drill | row_access)
        rows[str(index)] = {
            "prefix": prefix,
            "head_washer_source": source,
            "physical_roles": ("barrel", *stack),
            "path_roles": tuple(name.split("/")[-1] for name in row_drill | row_access),
            "bolt_driver_key": f"access/{prefix}/bolt_access",
        }
    return physical, paths, rows


def _neighbor_hits(station, physical, paths, geometry, families, *, same_family):
    """Report all unlike-station physical/path combinations, including path pairs."""
    categories = {
        "physical_to_physical": {},
        "path_to_physical": {},
        "physical_to_path": {},
        "path_to_path": {},
    }
    for other, (other_physical, other_paths, _) in geometry.items():
        if other == station or (families[other] == families[station]) != same_family:
            continue
        for label, sources, targets in (
            ("physical_to_physical", physical, other_physical),
            ("path_to_physical", paths, other_physical),
            ("physical_to_path", physical, other_paths),
            ("path_to_path", paths, other_paths),
        ):
            for name, shape in sources.items():
                for target, volume in _hits(shape, targets).items():
                    categories[label][f"{name}|{target}"] = volume
    return categories


@lru_cache(maxsize=1)
def probe():
    """Screen the revised viewer assembly without changing its producer or scene."""
    assembly = viewer.build_viewer_assembly()
    fixed = protected.inventory()
    duties = ledger.selected_duties()
    stations = FAMILY_STATIONS["outer_top8"]
    families = assembly["diagnostics"]["station_family"]
    if (
        set(families) != set(duties)
        or set(stations)
        != {name for name, family in families.items() if family == "outer_top8"}
        or len(assembly["panel_connections"]) != 66
        or len(assembly["frame_connections"]) != 12
        or any(assembly["release_flags"].values())
    ):
        raise ValueError("Revised viewer inventory or release boundary changed")
    geometry = {station: _station_geometry(assembly, station) for station in duties}
    results = {}
    viewer_stacks = supplemental_stacks = 0
    for station in stations:
        physical, paths, rows = geometry[station]
        all_shapes = physical | paths
        own = set(duties[station]["timber"])
        unrelated = {
            name: shape for name, shape in assembly["wood"].items() if name not in own
        }
        fixed_hits = {
            key: hits for key, hits in protected.hits(all_shapes, fixed).items() if hits
        }
        wood_hits = {
            name: hits
            for name, shape in all_shapes.items()
            if (hits := _hits(shape, unrelated))
        }
        for row in rows.values():
            if row["head_washer_source"] == "viewer":
                viewer_stacks += 1
            else:
                supplemental_stacks += 1
            if station in viewer.OUTER_HEADER_STATIONS:
                rim_name = f"base_side_{duties[station]['side']}"
                driver = paths[row["bolt_driver_key"]]
                rim_hit = protected._volume(driver, assembly["wood"][rim_name])
                if rim_hit <= TOL_MM3:
                    raise ValueError(
                        f"{station}: expected installed-rim driver blockage vanished"
                    )
                row["outer_header_bolt_driver"] = {
                    "installed_side_rim_hit_mm3": round(rim_hit, 6),
                    "installed_state": "blocked_by_side_rim",
                    "rim_removed_unrelated_wood_hits_mm3": _hits(
                        driver,
                        {
                            name: shape
                            for name, shape in unrelated.items()
                            if name != rim_name
                        },
                    ),
                    "rim_removed_side_rim_excluded": True,
                    "rim_removed_state": "conditional_unverified",
                    "rim_removal_verified": False,
                }
        results[station] = {
            "family": families[station],
            "rows": rows,
            "fixed_protected_hits_mm3": fixed_hits,
            "unrelated_wood_hits_mm3": wood_hits,
            "same_family_neighbor_hits_mm3": _neighbor_hits(
                station, physical, paths, geometry, families, same_family=True
            ),
            "cross_family_hits_mm3": _neighbor_hits(
                station, physical, paths, geometry, families, same_family=False
            ),
            "disposition": "REVISE",
        }
    if viewer_stacks != 4 or supplemental_stacks != 12:
        raise ValueError("Revised outer/top head/washer coverage changed")
    return {
        "source_id": SOURCE_ID,
        "source_assembly": "export_owner_barrel_scene.build_viewer_assembly",
        "baseline": "compact-floor-flush-kerf-right",
        "inventory": {
            "stations": len(stations),
            "rows": viewer_stacks + supplemental_stacks,
            "viewer_head_washer_rows": viewer_stacks,
            "supplemental_provisional_head_washer_rows": supplemental_stacks,
            "fixed_panel_screws": len(assembly["panel_connections"]),
            "retained_frame_bolts": len(assembly["frame_connections"]),
            "protected": fixed["counts"],
        },
        "trial_basis": {
            "barrel_model_provisional": assembly["hardware_basis"]["barrel_model"],
            "barrel_od_mm_nominal": assembly["hardware_basis"]["barrel_od_mm"],
            "barrel_length_mm_nominal": assembly["hardware_basis"]["barrel_length_mm"],
            "washer_od_mm_provisional": WASHER_OD_MM,
            "washer_thickness_mm_provisional": WASHER_THICKNESS_MM,
            "head_od_mm_provisional": HEAD_OD_MM,
            "head_height_mm_provisional": HEAD_HEIGHT_MM,
            "machine_bore_diameter_mm_provisional": outer.MACHINE_BORE_D_MM,
            "counterbore_diameter_mm_provisional": outer.VIEWER_HEADER_WASHER_OD_MM,
            "counterbore_depth_mm_provisional": outer.VIEWER_HEADER_RECESS_MM,
            "straight_tool_diameter_mm_provisional": 20.0,
            "straight_tool_length_mm_provisional": 40.0,
            "hold_rear_projection_mm_provisional": fixed["hold_rear_projection_mm"],
            "hold_rear_projection_is_provisional": True,
            "delivered_hardware_verified": False,
        },
        "collision_scope": (
            "fixed_protected",
            "unrelated_wood",
            "same_family_neighbor",
            "cross_family",
        ),
        "stations": results,
        "limits": (
            "Nominal finite envelopes only; protected hold projections and all supplemental "
            "heads/washers are provisional. Viewer bores are uncut paths, not instructions. "
            "The installed side rim blocks outer-header drivers; the rim-removed state "
            "excludes only that rim, not sequence, handling, tolerances, delivered hardware, "
            "strength, or repeatability. All reported intersections require interpretation."
        ),
        "layout_approved": False,
        "drilling_released": False,
        "fabrication_released": False,
        "structural_released": False,
    }


if __name__ == "__main__":
    print(json.dumps(probe(), indent=2, sort_keys=True))
