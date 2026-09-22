"""Finite rim-on service screen for the six outer rail barrel stations.

The viewer supplies uncut wood and nominal hardware/path envelopes. Intended
pilot bores are subtracted only from their receiving timber for withdrawal
screens; this does not mean the wood has been drilled or the joint qualified.
"""

import json
from math import pi

import cadquery as cq

from scripts import owner_barrel_coordinates as coordinates
from scripts import owner_barrel_rail_layout as rail
from scripts import owner_layout_protected as protected
from scripts.export_owner_barrel_scene import build_viewer_assembly
from scripts.simple_owner_duty_ledger import selected_duties

SCHEMA = "owner_barrel_rim_rail_service_probe/v1"
FAMILIES = frozenset({"bottom_outer", "lower_outer", "upper_outer"})
STATIONS = tuple(
    name for name, duty in selected_duties().items() if duty["family"] in FAMILIES
)
EXTRACTION_CLEARANCE_MM = 10.0
HIT_TOL_MM3 = protected.HIT_TOL_MM3


def _hits(shape, targets):
    return {
        name: round(volume, 6)
        for name, target in targets.items()
        if (volume := protected._volume(shape, target)) > HIT_TOL_MM3
    }


def _swept_cylinder(start, direction, length, diameter, withdrawal):
    """Union envelope of straight axial translations, not a real tool sweep."""
    return cq.Solid.makeCylinder(
        diameter / 2,
        length + withdrawal,
        start - direction * withdrawal,
        direction,
    )


def _service_paths(assembly, station, index):
    barrel_name = f"{station}_barrel_{index}"
    bolt_name = f"{barrel_name}_bolt"
    bolt = assembly["bolts"][bolt_name]
    body = assembly["barrels"][barrel_name]
    direction = bolt.direction.normalized()
    # The rail producer enters the minus-T face on row 1, plus-T on row 2.
    barrel_direction = cq.Vector(0, *coordinates.T) * (1 if index == 1 else -1)
    barrel_bore = assembly["drilling_paths"][f"{barrel_name}/barrel_bore"]
    machine_bore = assembly["drilling_paths"][f"{barrel_name}/machine_bore"]
    bolt_access = assembly["access_paths"][f"{barrel_name}/bolt_access"]
    barrel_access = assembly["access_paths"][f"{barrel_name}/barrel_access"]
    body_length = assembly["hardware_basis"]["barrel_length_mm"]
    body_diameter = assembly["hardware_basis"]["barrel_od_mm"]
    if (
        assembly["barrel_station"].get(barrel_name) != station
        or assembly["bolt_station"].get(bolt_name) != station
        or abs(body.Volume() - pi * (body_diameter / 2) ** 2 * body_length) > 1e-3
        or (barrel_access.Center() - body.Center()).dot(barrel_direction) >= 0
        or abs(direction.x) < 0.999999
        or abs(
            bolt_access.Volume()
            - pi * (rail.ACCESS_DIAMETER_MM / 2) ** 2 * rail.ACCESS_LENGTH_MM
        )
        > 1e-3
        or abs(
            barrel_access.Volume()
            - pi * (rail.ACCESS_DIAMETER_MM / 2) ** 2 * rail.ACCESS_LENGTH_MM
        )
        > 1e-3
    ):
        raise ValueError(f"{barrel_name}: current viewer rail path convention changed")
    bolt_withdrawal = bolt.length + EXTRACTION_CLEARANCE_MM
    # From recessed body to entry face, then the complete body plus clearance.
    barrel_withdrawal = rail.BARREL_RECESS_MM + body_length + EXTRACTION_CLEARANCE_MM
    body_start = body.Center() - barrel_direction * (body_length / 2)
    paths = {
        "bolt_driver": bolt_access,
        "bolt_withdrawal": _swept_cylinder(
            bolt.start, direction, bolt.length, bolt.diameter, bolt_withdrawal
        ),
        "barrel_access": barrel_access,
        "barrel_withdrawal": _swept_cylinder(
            body_start,
            barrel_direction,
            body_length,
            body_diameter,
            barrel_withdrawal,
        ),
    }
    return {
        "barrel_name": barrel_name,
        "bolt_name": bolt_name,
        "paths": paths,
        "machine_bore": machine_bore,
        "barrel_bore": barrel_bore,
        "bolt_withdrawal_mm": bolt_withdrawal,
        "barrel_withdrawal_mm": barrel_withdrawal,
    }


def _candidate_hardware(assembly, station, row, operation):
    """Keep neighbors installed; both bolts are out before barrel extraction."""
    other = {
        f"barrel/{name}": shape
        for name, shape in assembly["barrels"].items()
        if name != row["barrel_name"]
    }
    other.update(
        {
            f"bolt/{name}/{role}": shape
            for name, stack in assembly["stacks"].items()
            if name != row["bolt_name"]
            and not (
                operation.startswith("barrel_")
                and assembly["bolt_station"][name] == station
            )
            for role, shape in stack.items()
        }
    )
    return other


def _wood_hits(path, wood, participants, bore=None):
    hits = {}
    for name, shape in wood.items():
        target = shape.cut(bore) if bore is not None and name in participants else shape
        if target.Volume() <= HIT_TOL_MM3:
            continue
        if (volume := protected._volume(path, target)) > HIT_TOL_MM3:
            hits[name] = round(volume, 6)
    return hits


def probe(assembly=None, fixed=None):
    """Check nominal rim-on service envelopes, preserving every fixed axis."""
    assembly = build_viewer_assembly() if assembly is None else assembly
    fixed = protected.inventory() if fixed is None else fixed
    duties = selected_duties()
    panels = (
        "main_lower_left",
        "main_lower_right",
        "main_upper_left",
        "main_upper_right",
        "kicker_left",
        "kicker_right",
    )
    if (
        len(STATIONS) != 6
        or len(assembly["panel_connections"]) != 66
        or len(assembly["frame_connections"]) != 12
        or not set(panels) <= set(assembly["wood"])
        or set(assembly["station_dispositions"]) != set(duties)
        or any(
            assembly["diagnostics"]["station_family"].get(name) != "rail10"
            for name in STATIONS
        )
    ):
        raise ValueError("Current viewer or fixed rail inventory changed")
    output = {}
    for station in STATIONS:
        duty = duties[station]
        side = duty["side"]
        rim_name = f"base_side_{side}"
        if rim_name not in duty["timber"]:
            raise ValueError(f"{station}: no side-rim member")
        removed_screws = sorted(
            row.name for row in assembly["panel_connections"] if rim_name in row.members
        )
        if len(removed_screws) != 8:
            raise ValueError(f"{station}: expected eight removable rim screws")
        service_fixed = {
            family: {
                name: shape
                for name, shape in members.items()
                if family != "panel_screws" or name not in removed_screws
            }
            for family, members in fixed["solids"].items()
        }
        rows = {}
        for index in (1, 2):
            row = _service_paths(assembly, station, index)
            operations = {}
            for operation, path in row["paths"].items():
                bore = (
                    row["machine_bore"]
                    if operation == "bolt_withdrawal"
                    else row["barrel_bore"]
                    if operation == "barrel_withdrawal"
                    else None
                )
                wood_hits = _wood_hits(path, assembly["wood"], duty["timber"], bore)
                fixed_hits = {
                    family: hits
                    for family, members in service_fixed.items()
                    if (hits := _hits(path, members))
                }
                hardware_hits = _hits(
                    path, _candidate_hardware(assembly, station, row, operation)
                )
                operations[operation] = {
                    "other_wood_hits_mm3": wood_hits,
                    "fixed_protected_hits_mm3": fixed_hits,
                    "neighbor_hardware_hits_mm3": hardware_hits,
                    "finite_status": (
                        "BLOCKED_NOMINAL"
                        if wood_hits or fixed_hits or hardware_hits
                        else "CLEAR_FINITE_ONLY"
                    ),
                }
            rows[row["barrel_name"]] = {
                "bolt": row["bolt_name"],
                "bolt_nominal_length_mm": assembly["bolts"][row["bolt_name"]].length,
                "bolt_straight_withdrawal_mm": row["bolt_withdrawal_mm"],
                "barrel_straight_withdrawal_mm": row["barrel_withdrawal_mm"],
                "operations": operations,
            }
        output[station] = {
            "family": duty["family"],
            "side": side,
            "members": list(duty["timber"]),
            "temporarily_removed_panel_screws": removed_screws,
            "frame_bolts_left_in_place": True,
            "panel_shapes_left_in_place": True,
            "rows": rows,
            "rim_on_nominal_service_clear": all(
                item["finite_status"] == "CLEAR_FINITE_ONLY"
                for row in rows.values()
                for item in row["operations"].values()
            ),
        }
    return {
        "schema": SCHEMA,
        "viewer_source": "scripts.export_owner_barrel_scene.build_viewer_assembly",
        "station_count": len(output),
        "station_names": list(STATIONS),
        "fixed_inventory": fixed["counts"],
        "fixed_panel_axes_preserved": 66,
        "fixed_frame_bolt_axes_preserved": 12,
        "panel_shapes_checked_in_place": list(panels),
        "stations": output,
        "assumptions": [
            "Both bolts at a station are removed before either barrel is withdrawn",
            "Matching bolt/barrel thread occupancy is intentional and omitted from blocker comparisons",
            "Only the eight side-rim receiver screws on the active side may be temporarily removed",
            "All panels, other frame wood, retained frame bolts, other screws and neighbor trial hardware remain",
            "Nominal cylindrical access and axial withdrawal envelopes; receiving wood is virtually relieved only by its modeled pilot bore",
            "Ten millimeters of nominal extra extraction travel; no delivered hardware or tool geometry",
        ],
        "limits": (
            "Finite intersections are screening evidence only. No continuous real tool sweep, "
            "bit fit, head/washer access, toleranced removal, strength, or safe assembly is proved."
        ),
        "rim_removal_verified": False,
        "tool_sweep_verified": False,
        "drilling_released": False,
        "fabrication_released": False,
        "structural_released": False,
    }


if __name__ == "__main__":
    print(json.dumps(probe(), indent=2, sort_keys=True))
