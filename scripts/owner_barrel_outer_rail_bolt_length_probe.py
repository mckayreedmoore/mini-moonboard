"""Detached nominal bolt-length screen on the current -85 outer-rail viewer pose.

No viewer solids or source axes are changed. All lengths and bores are
provisional envelopes, not hardware selection or drilling instructions.
"""

import json
import math

import cadquery as cq

from scripts import owner_barrel_rail_layout as rail
from scripts import owner_layout_protected as protected
from scripts.center_posts_outward_owner_layout import build_layout as post_layout
from scripts.export_owner_barrel_scene import build_viewer_assembly
from scripts.owner_barrel_native_connector_inventory import build_inventory
from scripts.simple_owner_duty_ledger import selected_duties

SCHEMA = "owner_barrel_outer_rail_bolt_length_probe/v1"
FAMILIES = frozenset({"bottom_outer", "lower_outer", "upper_outer"})
LENGTHS_MM = {"6_in": 152.4, "7_in": 177.8}
HIT_TOL_MM3 = protected.HIT_TOL_MM3


def _hits(shape, targets):
    return {
        name: round(volume, 6)
        for name, target in targets.items()
        if (volume := protected._volume(shape, target)) > HIT_TOL_MM3
    }


def _cylinder_caps_along(shape, start, direction):
    """Recover the actual modeled machine-bore ends from its planar caps."""
    caps = [face.Center() for face in shape.Faces() if face.geomType() == "PLANE"]
    if len(caps) != 2 or any(
        (point - start).cross(direction).Length > 1e-3 for point in caps
    ):
        raise ValueError("Current machine-bore axis or cap geometry changed")
    return sorted((point - start).dot(direction) for point in caps)


def _far_side_along(receiver, start, direction):
    """Use actual receiving timber; verify its far X plane crosses this axis."""
    if abs(direction.x) < 0.999999:
        raise ValueError("Outer rail bolt is no longer X-directed")
    far = max(
        (vertex.Center() - start).dot(direction) for vertex in receiver.Vertices()
    )
    if not receiver.isInside(start + direction * (far - 0.1), 1e-5):
        raise ValueError("Receiving wood far side does not cross bolt axis")
    return far


def _screen_length(
    length, bolt, barrel_far_wall, bore_end, far_side, assembly, fixed, neighbors
):
    start = cq.Vector(*bolt["start_mm"])
    direction = cq.Vector(*bolt["direction_xyz"])
    tip = start + direction * length
    receiver = assembly["wood"][bolt["receiving_member"]]
    shaft = cq.Solid.makeCylinder(bolt["diameter_mm"] / 2, length, start, direction)
    extension_length = max(0.0, length - bore_end)
    extension = (
        cq.Solid.makeCylinder(
            rail.MACHINE_BORE_DIAMETER_MM / 2,
            extension_length,
            start + direction * bore_end,
            direction,
        )
        if extension_length > 1e-6
        else None
    )
    unrelated = {
        name: shape
        for name, shape in assembly["wood"].items()
        if name not in {bolt["entry_member"], bolt["receiving_member"]}
    }

    def collisions(shape):
        if shape is None:
            return {
                "unrelated_wood": {},
                "fixed_protected": {},
                "neighbor_viewer_hardware": {},
            }
        return {
            "unrelated_wood": _hits(shape, unrelated),
            "fixed_protected": protected.hits({"trial": shape}, fixed)["trial"],
            "neighbor_viewer_hardware": _hits(shape, neighbors),
        }

    return {
        "nominal_length_mm": length,
        "tip_xyz_mm": [round(value, 6) for value in tip.toTuple()],
        "tip_past_assumed_barrel_axis_mm": round(
            length - bolt["provisional_axis_point_from_bolt_start_mm"], 6
        ),
        "reaches_assumed_barrel_axis": (
            length >= bolt["provisional_axis_point_from_bolt_start_mm"]
        ),
        "tip_past_modeled_barrel_far_wall_mm": round(length - barrel_far_wall, 6),
        "nominal_tip_beyond_modeled_barrel_body": length > barrel_far_wall,
        "remaining_receiving_wood_to_far_side_mm": round(far_side - length, 6),
        "tip_inside_receiving_wood": receiver.isInside(tip, 1e-5),
        "required_machine_bore_extension_mm": round(extension_length, 6),
        "modeled_bore_depth_past_nominal_tip_mm": round(max(0.0, bore_end - length), 6),
        "bore_extension_outside_receiving_wood_mm3": round(
            max(
                0.0,
                extension.Volume() - protected._volume(extension, receiver),
            ),
            6,
        )
        if extension is not None
        else 0.0,
        "shaft_hits_mm3": collisions(shaft),
        "bore_extension_hits_mm3": collisions(extension),
    }


def probe(assembly=None):
    """Screen six exact outer stations without changing the viewer or wood."""
    assembly = build_viewer_assembly() if assembly is None else assembly
    duties = selected_duties()
    stations = tuple(
        name for name, duty in duties.items() if duty["family"] in FAMILIES
    )
    expected = {
        f"{station}_barrel_{index}_bolt": station
        for station in stations
        for index in (1, 2)
    }
    if (
        len(stations) != 6
        or len(expected) != 12
        or any(
            assembly["bolt_station"].get(name) != station
            for name, station in expected.items()
        )
        or any(
            assembly["barrel_station"].get(name.removesuffix("_bolt")) != station
            for name, station in expected.items()
        )
        or any(
            assembly["station_modes"].get(station) != "direct" for station in stations
        )
        or any(
            assembly["station_dispositions"].get(station) != "REVISE"
            for station in stations
        )
        or assembly["diagnostics"]["producer_diagnostics"]["outer_top8"][
            "viewer_trial_outer_header_forward_y_mm"
        ]
        != -85.0
    ):
        raise ValueError(
            "Exact current -85 viewer outer-rail station ownership changed"
        )

    inventory = build_inventory(assembly=assembly, placement=post_layout())
    fixed = protected.inventory()
    if (
        fixed["counts"]["panel_screws"] != 66
        or fixed["counts"]["frame_bolts"] != 12
        or set(fixed["solids"]["panel_screws"]) != set(inventory["fixed_panel_screws"])
        or set(fixed["solids"]["frame_bolts"]) != set(inventory["retained_frame_bolts"])
        or set(inventory["modeled_shaft_reach_shortfalls_mm"]) != set(expected)
    ):
        raise ValueError("Current fixed/protected or 5-in shaft inventory changed")
    shaft_diameters = {inventory["bolts"][name]["diameter_mm"] for name in expected}
    if len(shaft_diameters) != 1:
        raise ValueError("Outer-rail shaft diameters are inconsistent")
    shaft_diameter = shaft_diameters.pop()

    output = {}
    for name, station in expected.items():
        bolt = inventory["bolts"][name]
        source = assembly["bolts"][name]
        if (
            bolt["station"] != station
            or not math.isclose(source.length, 127.0, abs_tol=1e-6)
            or bolt["modeled_shaft_shortfall_mm"] <= 0
        ):
            raise ValueError(f"{name}: current 5-in outer shaft changed")
        start = cq.Vector(*bolt["start_mm"])
        direction = cq.Vector(*bolt["direction_xyz"])
        barrel = inventory["barrels"][bolt["barrel_name"]]
        barrel_axis = cq.Vector(*barrel["body_axis_xyz_unoriented_provisional"])
        if abs(barrel_axis.dot(direction)) > 1e-6:
            raise ValueError(f"{name}: modeled barrel is no longer crosswise")
        # ponytail: the current cylinder is crossed at its midpoint, so its
        # downstream envelope wall is one recovered body radius past the axis.
        barrel_far_wall = (
            bolt["provisional_axis_point_from_bolt_start_mm"]
            + barrel["body_diameter_mm_provisional"] / 2
        )
        bore = assembly["drilling_paths"][f"{bolt['barrel_name']}/machine_bore"]
        bore_start, bore_end = _cylinder_caps_along(bore, start, direction)
        if (
            bore_end <= bolt["provisional_axis_point_from_bolt_start_mm"]
            or abs(
                bore.Volume()
                - math.pi
                * (rail.MACHINE_BORE_DIAMETER_MM / 2) ** 2
                * (bore_end - bore_start)
            )
            > 1e-3
        ):
            raise ValueError(f"{name}: current machine-bore envelope changed")
        far_side = _far_side_along(
            assembly["wood"][bolt["receiving_member"]], start, direction
        )
        neighbors = {
            f"barrel/{other}": shape
            for other, shape in assembly["barrels"].items()
            if other != bolt["barrel_name"]
        }
        neighbors.update(
            {
                f"bolt/{other}/{role}": shape
                for other, stack in assembly["stacks"].items()
                if other != name
                for role, shape in stack.items()
            }
        )
        output[name] = {
            "station": station,
            "family": duties[station]["family"],
            "entry_member": bolt["entry_member"],
            "receiving_member": bolt["receiving_member"],
            "barrel_name": bolt["barrel_name"],
            "modeled_5in_shortfall_mm": round(bolt["modeled_shaft_shortfall_mm"], 6),
            "assumed_barrel_axis_from_start_mm": round(
                bolt["provisional_axis_point_from_bolt_start_mm"], 6
            ),
            "modeled_barrel_far_wall_from_start_mm": round(barrel_far_wall, 6),
            "existing_machine_bore_end_from_start_mm": round(bore_end, 6),
            "receiving_wood_far_side_from_start_mm": round(far_side, 6),
            "alternatives": {
                label: _screen_length(
                    length,
                    bolt,
                    barrel_far_wall,
                    bore_end,
                    far_side,
                    assembly,
                    fixed,
                    neighbors,
                )
                for label, length in LENGTHS_MM.items()
            },
        }

    return {
        "schema": SCHEMA,
        "status": "detached_nominal_geometry_sensitivity_only",
        "viewer_pose": inventory["viewer_pose"],
        "source_inventory_fingerprint_sha256": inventory[
            "inventory_fingerprint_sha256"
        ],
        "stations": {
            station: {
                "bolt_names": sorted(
                    name for name, owner in expected.items() if owner == station
                )
            }
            for station in stations
        },
        "bolts": output,
        "fixed_inventory": fixed["counts"],
        "modeled_bore_diameter_mm": rail.MACHINE_BORE_DIAMETER_MM,
        "modeled_shaft_diameter_mm": shaft_diameter,
        "modeled_radial_bore_clearance_mm": round(
            (rail.MACHINE_BORE_DIAMETER_MM - shaft_diameter) / 2, 6
        ),
        "retail_lead": {
            "store": "Home Depot",
            "brand": "Everbilt",
            "model": "807396",
            "description": "1/4-20 x 7-in hex bolt",
            "url": "https://www.homedepot.com/p/204281599",
        },
        "limits": (
            "Nominal cylindrical shafts on current axes and only the added machine-bore "
            "segments are screened. The barrel-axis point, bore diameter, and washer "
            "offset are provisional viewer assumptions. The 7-in nominal tip "
            "passes the modeled barrel body's far wall; nominal radial bore "
            "clearance and zero modeled axial tip clearance do not establish fit. "
            "Positive volume intersections are interference evidence; zero hits "
            "are not tolerance, head/washer, thread, strength, or drill approval. "
            "Matching thread engagement and a deeper machine bore with tip "
            "clearance require separate verification."
        ),
        "selected_hardware": False,
        "thread_engagement_verified": False,
        "delivered_length_verified": False,
        "head_washer_fit_verified": False,
        "capacity_verified": False,
        "drilling_released": False,
        "fabrication_released": False,
    }


if __name__ == "__main__":
    print(json.dumps(probe(), indent=2, sort_keys=True))
