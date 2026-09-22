"""Finite rim-on service screen for the four outer-top rim-touching stations.

Only matching nominal bores are virtually relieved in receiving wood during
withdrawal. The viewer wood is uncut, and this is not a tool or drilling plan.
"""

import json
from math import pi

import cadquery as cq

from scripts import owner_layout_protected as protected
from scripts.export_owner_barrel_scene import build_viewer_assembly
from scripts.simple_owner_duty_ledger import selected_duties

SCHEMA = "owner_barrel_rim_outer_top_service_probe/v1"
FAMILIES = frozenset({"top_outer", "base_outer_side"})
STATIONS = tuple(
    name for name, duty in selected_duties().items() if duty["family"] in FAMILIES
)
EXTRACTION_CLEARANCE_MM = 10.0
ACCESS_DIAMETER_MM = 20.0
ACCESS_LENGTH_MM = 40.0
HIT_TOL_MM3 = protected.HIT_TOL_MM3


def _hits(shape, targets):
    return {
        name: round(volume, 6)
        for name, target in targets.items()
        if (volume := protected._volume(shape, target)) > HIT_TOL_MM3
    }


def _swept_cylinder(start, direction, length, diameter, withdrawal):
    """Union of straight axial positions; no rotation, grip, or tool sweep."""
    return cq.Solid.makeCylinder(
        diameter / 2,
        length + withdrawal,
        start - direction * withdrawal,
        direction,
    )


def _axial_span(shape, direction):
    positions = [vertex.Center().dot(direction) for vertex in shape.Vertices()]
    return max(positions) - min(positions)


def _service_paths(assembly, station, barrel_name):
    bolt_name = f"{barrel_name}_bolt"
    if (
        assembly["barrel_station"].get(barrel_name) != station
        or assembly["bolt_station"].get(bolt_name) != station
    ):
        raise ValueError(f"{barrel_name}: current viewer ownership changed")
    bolt = assembly["bolts"][bolt_name]
    body = assembly["barrels"][barrel_name]
    stack = assembly["stacks"][bolt_name]
    machine_bore = assembly["drilling_paths"][f"{barrel_name}/machine_bore"]
    barrel_bore = assembly["drilling_paths"][f"{barrel_name}/barrel_bore"]
    bolt_access = assembly["access_paths"][f"{barrel_name}/bolt_access"]
    barrel_access = assembly["access_paths"][f"{barrel_name}/barrel_access"]
    bolt_direction = bolt.direction.normalized()
    # The barrel-entry side differs between the two families and mirrors by
    # side. Derive inward direction from the actual body and access envelope.
    barrel_direction = (body.Center() - barrel_access.Center()).normalized()
    body_length = assembly["hardware_basis"]["barrel_length_mm"]
    body_diameter = assembly["hardware_basis"]["barrel_od_mm"]
    body_start = body.Center() - barrel_direction * (body_length / 2)
    access_length = _axial_span(barrel_access, barrel_direction)
    barrel_entry = barrel_access.Center() + barrel_direction * (access_length / 2)
    barrel_recess = (body_start - barrel_access.Center()).dot(barrel_direction) - (
        access_length / 2
    )
    # The access cylinder is 40 mm long and starts at the entry face, pointing
    # outward. Thus its center is 20 mm outside that face.
    if (
        set(stack) != {"shaft", "washer", "head"}
        or abs(body.Volume() - pi * (body_diameter / 2) ** 2 * body_length) > 1e-3
        or abs(stack["shaft"].Volume() - pi * (bolt.diameter / 2) ** 2 * bolt.length)
        > 1e-3
        or abs(
            bolt_access.Volume() - pi * (ACCESS_DIAMETER_MM / 2) ** 2 * ACCESS_LENGTH_MM
        )
        > 1e-3
        or abs(
            barrel_access.Volume()
            - pi * (ACCESS_DIAMETER_MM / 2) ** 2 * ACCESS_LENGTH_MM
        )
        > 1e-3
        or abs(_axial_span(bolt_access, bolt_direction) - ACCESS_LENGTH_MM) > 1e-5
        or abs(access_length - ACCESS_LENGTH_MM) > 1e-5
        or (bolt_access.Center() - bolt.start).dot(bolt_direction) >= 0
        or (barrel_bore.Center() - barrel_access.Center()).dot(barrel_direction) <= 0
        or (barrel_bore.Center() - barrel_access.Center())
        .cross(barrel_direction)
        .Length
        > 1e-5
        or abs(
            min(
                vertex.Center().dot(barrel_direction)
                for vertex in barrel_bore.Vertices()
            )
            - barrel_entry.dot(barrel_direction)
        )
        > 1e-5
        or (barrel_entry - barrel_bore.Center()).cross(barrel_direction).Length > 1e-5
        or barrel_recess < -1e-5
    ):
        raise ValueError(f"{barrel_name}: current outer-top service path changed")
    barrel_recess = max(0.0, barrel_recess)
    bolt_withdrawal = bolt.length + EXTRACTION_CLEARANCE_MM
    barrel_withdrawal = barrel_recess + body_length + EXTRACTION_CLEARANCE_MM
    return {
        "barrel_name": barrel_name,
        "bolt_name": bolt_name,
        "bolt_direction_xyz": [round(v, 6) for v in bolt_direction.toTuple()],
        "barrel_direction_xyz": [round(v, 6) for v in barrel_direction.toTuple()],
        "barrel_recess_mm": round(barrel_recess, 6),
        "bolt_withdrawal_mm": bolt_withdrawal,
        "barrel_withdrawal_mm": round(barrel_withdrawal, 6),
        "machine_bore": machine_bore,
        "barrel_bore": barrel_bore,
        "paths": {
            "bolt_driver": bolt_access,
            "bolt_withdrawal": _swept_cylinder(
                bolt.start, bolt_direction, bolt.length, bolt.diameter, bolt_withdrawal
            ),
            "barrel_access": barrel_access,
            "barrel_withdrawal": _swept_cylinder(
                body_start,
                barrel_direction,
                body_length,
                body_diameter,
                barrel_withdrawal,
            ),
        },
    }


def _candidate_hardware(assembly, station, row, operation):
    """Retain other stations; unscrew both station bolts before barrel removal."""
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
    """Screen current-viewer paths with each side rim and all panels installed."""
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
        len(STATIONS) != 4
        or len(assembly["panel_connections"]) != 66
        or len(assembly["frame_connections"]) != 12
        or fixed["counts"]["panel_screws"] != 66
        or fixed["counts"]["frame_bolts"] != 12
        or {row.name for row in assembly["panel_connections"]}
        != set(fixed["solids"]["panel_screws"])
        or {row.name for row in assembly["frame_connections"]}
        != set(fixed["solids"]["frame_bolts"])
        or not set(panels) <= set(assembly["wood"])
        or set(assembly["station_dispositions"]) != set(duties)
        or any(
            assembly["diagnostics"]["station_family"].get(name) != "outer_top8"
            for name in STATIONS
        )
    ):
        raise ValueError("Current viewer or fixed outer-top inventory changed")
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
        barrels = sorted(
            name
            for name, owner in assembly["barrel_station"].items()
            if owner == station
        )
        if len(barrels) != 2:
            raise ValueError(f"{station}: expected two barrel rows")
        rows = {}
        for barrel_name in barrels:
            row = _service_paths(assembly, station, barrel_name)
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
            rows[barrel_name] = {
                "bolt": row["bolt_name"],
                "bolt_direction_xyz": row["bolt_direction_xyz"],
                "barrel_direction_xyz": row["barrel_direction_xyz"],
                "barrel_recess_mm": row["barrel_recess_mm"],
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
            "rim_on_nominal_service_clear": all(
                item["finite_status"] == "CLEAR_FINITE_ONLY"
                for row in rows.values()
                for item in row["operations"].values()
            ),
            "rows": rows,
        }
    return {
        "schema": SCHEMA,
        "viewer_source": (
            "scripts.export_owner_barrel_scene.build_integrated_viewer_assembly"
            if assembly.get("post_placement") == "integrated"
            else "scripts.export_owner_barrel_scene.build_viewer_assembly"
        ),
        "station_count": len(output),
        "station_names": list(STATIONS),
        "fixed_inventory": fixed["counts"],
        "fixed_panel_axes_preserved": 66,
        "fixed_frame_bolt_axes_preserved": 12,
        "panel_shapes_checked_in_place": list(panels),
        "stations": output,
        "assumptions": [
            "Both bolts at a station are removed before either barrel is withdrawn",
            "Matching bolt/thread occupancy is intentional and omitted from blockers",
            "Only eight side-rim receiver screws on the active side may be removed",
            "All panels, other wood, frame bolts, other screws and neighbor hardware remain",
            "Only receiving wood is virtually relieved by its matching nominal bore for extraction",
            "Ten millimeters of extra straight travel; no delivered hardware or tool geometry",
        ],
        "limits": (
            "Finite nominal shaft/body and cylindrical access envelopes only. Missing "
            "delivered head/washer fit, real tool sweep, extraction grip, tolerances, strength, "
            "repeated service and safe panel support are not verified. No wood is drilled."
        ),
        "rim_removal_verified": False,
        "tool_sweep_verified": False,
        "drilling_released": False,
        "fabrication_released": False,
        "structural_released": False,
    }


if __name__ == "__main__":
    print(json.dumps(probe(), indent=2, sort_keys=True))
