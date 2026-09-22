"""Audit the current viewer's 48 nominal barrel-bolt axial stacks.

This reads assembled solids and diagnostic bolt axes, not producer defaults or
retail thread drawings. A centered thread axis is only a CAD assumption.
"""

import json
from math import isclose, pi

import cadquery as cq
from OCP.BRepAdaptor import BRepAdaptor_Surface

from scripts import simple_owner_duty_ledger as ledger
from scripts.export_owner_barrel_scene import build_viewer_assembly

SCHEMA = "owner_barrel_installed_stack_audit/v1"
MM_TOL = 1e-4
OUTER_RAIL_FAMILIES = frozenset({"bottom_outer", "lower_outer", "upper_outer"})


def _rounded(value):
    return round(float(value), 4)


def _xyz(point):
    return [_rounded(value) for value in point.toTuple()]


def _cylinder(shape, label):
    """Recover real cylinder direction, diameter and cap span from the solid."""
    faces = [face for face in shape.Faces() if face.geomType() == "CYLINDER"]
    if len(faces) != 1:
        raise ValueError(f"{label}: expected one cylindrical surface")
    cylinder = BRepAdaptor_Surface(faces[0].wrapped).Cylinder()
    direction = cylinder.Axis().Direction()
    axis = cq.Vector(direction.X(), direction.Y(), direction.Z()).normalized()
    vertices = [vertex.Center() for vertex in shape.Vertices()]
    if len(vertices) < 2:
        raise ValueError(f"{label}: no finite cap vertices")
    ordinates = [vertex.dot(axis) for vertex in vertices]
    length = max(ordinates) - min(ordinates)
    diameter = 2 * cylinder.Radius()
    if (
        length <= 0
        or diameter <= 0
        or not isclose(shape.Volume(), pi * (diameter / 2) ** 2 * length, rel_tol=1e-6)
    ):
        raise ValueError(f"{label}: not a full finite cylinder")
    return axis, length, diameter, vertices


def _axial_caps(vertices, shaft_start, direction):
    ordinates = [(vertex - shaft_start).dot(direction) for vertex in vertices]
    return min(ordinates), max(ordinates)


def _coaxial(shape, shaft_start, direction):
    return (shape.Center() - shaft_start).cross(direction).Length


def _classify(reach_axis_mm, tip_mm, bore_cap_mm):
    """Keep independent failure flags; a bore overrun can coexist with short reach."""
    short = tip_mm < reach_axis_mm - MM_TOL
    overrun = tip_mm > bore_cap_mm + MM_TOL
    flags = []
    if short:
        flags.append("SHORT_OF_ASSUMED_BARREL_AXIS")
    if overrun:
        flags.append("BEYOND_MODELED_MACHINE_BORE")
    if not flags:
        flags.append("AXIS_REACHED_WITHIN_MODELED_BORE")
    return flags


def _row(assembly, bolt_name):
    if not bolt_name.endswith("_bolt"):
        raise ValueError(f"{bolt_name}: no matching barrel name")
    barrel_name = bolt_name.removesuffix("_bolt")
    if assembly["bolt_station"][bolt_name] != assembly["barrel_station"][barrel_name]:
        raise ValueError(f"{bolt_name}: bolt/barrel station ownership differs")
    bolt = assembly["bolts"][bolt_name]
    barrel = assembly["barrels"][barrel_name]
    stack = assembly["stacks"][bolt_name]
    paths = assembly["drilling_paths"]
    path_names = [
        name
        for name in (f"{barrel_name}/machine_bore", f"{barrel_name}/bolt_bore")
        if name in paths
    ]
    if len(path_names) != 1 or "shaft" not in stack:
        raise ValueError(f"{bolt_name}: expected one machine bore and shaft solid")
    direction = bolt.direction.normalized()
    shaft_start = bolt.start
    shaft_axis, shaft_length, shaft_od, shaft_vertices = _cylinder(
        stack["shaft"], f"{bolt_name}/shaft"
    )
    if (
        abs(shaft_axis.dot(direction)) < 1 - MM_TOL
        or not isclose(shaft_length, bolt.length, abs_tol=MM_TOL)
        or not isclose(shaft_od, bolt.diameter, abs_tol=MM_TOL)
        or _coaxial(stack["shaft"], shaft_start, direction) > MM_TOL
    ):
        raise ValueError(f"{bolt_name}: connection/shaft solid mismatch")
    shaft_near, shaft_tip = _axial_caps(shaft_vertices, shaft_start, direction)
    if abs(shaft_near) > MM_TOL or abs(shaft_tip - bolt.length) > MM_TOL:
        raise ValueError(f"{bolt_name}: shaft start/tip mismatch")

    barrel_axis, barrel_length, barrel_od, _ = _cylinder(barrel, f"{barrel_name}/body")
    if (
        abs(barrel_axis.dot(direction)) > MM_TOL
        or _coaxial(barrel, shaft_start, direction) > MM_TOL
    ):
        raise ValueError(f"{barrel_name}: assumed center is not on bolt axis")
    barrel_center = barrel.Center()
    reach_axis = (barrel_center - shaft_start).dot(direction)
    barrel_radius = barrel_od / 2
    near_wall = reach_axis - barrel_radius
    far_wall = reach_axis + barrel_radius
    # Necessary axial overlap only; real thread runout and internal barrel
    # thread geometry are not supplied by the retail listings.
    possible_body_overlap = max(0.0, min(shaft_tip, far_wall) - near_wall)
    threaded_end_length_to_near_wall = max(0.0, shaft_tip - near_wall)
    duty = ledger.selected_duties()[assembly["bolt_station"][bolt_name]]
    outer_rail_setback = None
    if duty["family"] in OUTER_RAIL_FAMILIES:
        rail = assembly["wood"][duty["timber"][0]].BoundingBox()
        outer_rail_setback = min(
            abs(barrel_center.x - rail.xmin), abs(rail.xmax - barrel_center.x)
        )

    bore = paths[path_names[0]]
    bore_axis, bore_length, bore_od, bore_vertices = _cylinder(bore, path_names[0])
    if (
        abs(bore_axis.dot(direction)) < 1 - MM_TOL
        or _coaxial(bore, shaft_start, direction) > MM_TOL
    ):
        raise ValueError(f"{bolt_name}: machine bore not coaxial with shaft")
    bore_near, bore_cap = _axial_caps(bore_vertices, shaft_start, direction)
    if not isclose(bore_cap - bore_near, bore_length, abs_tol=MM_TOL):
        raise ValueError(f"{bolt_name}: machine bore cap span mismatch")

    flags = _classify(reach_axis, shaft_tip, bore_cap)
    return {
        "station": assembly["bolt_station"][bolt_name],
        "bolt_name": bolt_name,
        "barrel_name": barrel_name,
        "shaft_start_xyz_mm": _xyz(shaft_start),
        "shaft_axis_xyz": _xyz(direction),
        "shaft_length_mm": _rounded(shaft_length),
        "shaft_tip_xyz_mm": _xyz(shaft_start + direction * shaft_tip),
        "shaft_od_mm": _rounded(shaft_od),
        "barrel_body_center_xyz_mm": _xyz(barrel_center),
        "barrel_body_length_mm": _rounded(barrel_length),
        "barrel_body_od_mm": _rounded(barrel_od),
        "outer_rail_barrel_setback_from_nearest_end_mm": (
            _rounded(outer_rail_setback) if outer_rail_setback is not None else None
        ),
        "assumed_thread_axis_reach_mm": _rounded(reach_axis),
        "reach_to_barrel_near_wall_mm": _rounded(near_wall),
        "reach_to_barrel_far_wall_mm": _rounded(far_wall),
        "maximum_body_overlap_with_fully_threaded_shaft_mm": _rounded(
            possible_body_overlap
        ),
        "bolt_end_thread_length_needed_to_reach_near_wall_mm": _rounded(
            threaded_end_length_to_near_wall
        ),
        "tip_past_assumed_axis_mm": _rounded(shaft_tip - reach_axis),
        "tip_past_barrel_far_wall_mm": _rounded(shaft_tip - reach_axis - barrel_radius),
        "machine_bore_path": path_names[0],
        "machine_bore_od_mm": _rounded(bore_od),
        "machine_bore_near_cap_from_shaft_start_mm": _rounded(bore_near),
        "machine_bore_far_cap_from_shaft_start_mm": _rounded(bore_cap),
        "machine_bore_far_cap_xyz_mm": _xyz(shaft_start + direction * bore_cap),
        "tip_to_bore_far_cap_clearance_mm": _rounded(bore_cap - shaft_tip),
        "minimum_added_bore_depth_to_tip_mm": _rounded(max(0, shaft_tip - bore_cap)),
        "head_present_in_assembly": "head" in stack,
        "washer_present_in_assembly": "washer" in stack,
        "nominal_axial_flags": flags,
        "thread_engagement": "UNKNOWN",
    }


def build_report(assembly=None):
    """Audit current viewer state; never infer a complete installed-stack pass."""
    assembly = build_viewer_assembly() if assembly is None else assembly
    bolts, barrels = assembly["bolts"], assembly["barrels"]
    expected_barrels = {name.removesuffix("_bolt") for name in bolts}
    if (
        len(bolts) != 48
        or len(barrels) != 48
        or expected_barrels != set(barrels)
        or set(assembly["stacks"]) != set(bolts)
        or set(assembly["bolt_station"].values())
        != set(assembly["barrel_station"].values())
        or len(assembly["panel_connections"]) != 66
        or len(assembly["frame_connections"]) != 12
    ):
        raise ValueError("Current 48-bolt viewer inventory changed")
    rows = [_row(assembly, name) for name in sorted(bolts)]
    short = [
        row["bolt_name"]
        for row in rows
        if "SHORT_OF_ASSUMED_BARREL_AXIS" in row["nominal_axial_flags"]
    ]
    overrun = [
        row["bolt_name"]
        for row in rows
        if "BEYOND_MODELED_MACHINE_BORE" in row["nominal_axial_flags"]
    ]
    within = [
        row["bolt_name"]
        for row in rows
        if row["nominal_axial_flags"] == ["AXIS_REACHED_WITHIN_MODELED_BORE"]
    ]
    absent_head = [
        row["bolt_name"] for row in rows if not row["head_present_in_assembly"]
    ]
    absent_washer = [
        row["bolt_name"] for row in rows if not row["washer_present_in_assembly"]
    ]
    return {
        "schema": SCHEMA,
        "source": "scripts.export_owner_barrel_scene.build_viewer_assembly()",
        "source_basis": "CURRENT working-tree producer composition, not exported JSON",
        "row_count": len(rows),
        "rows": rows,
        "counts": {
            "short_of_assumed_barrel_axis": len(short),
            "beyond_modeled_machine_bore": len(overrun),
            "axis_reached_within_modeled_bore": len(within),
            "head_absent": len(absent_head),
            "washer_absent": len(absent_washer),
            "thread_engagement_unknown": len(rows),
        },
        "named_exceptions": {
            "short_of_assumed_barrel_axis": short,
            "beyond_modeled_machine_bore": overrun,
            "head_absent": absent_head,
            "washer_absent": absent_washer,
        },
        "overall_pass": False,
        "fit_qualified": False,
        "structural_released": False,
        "drilling_released": False,
        "fabrication_released": False,
        "limits": (
            "Nominal CAD axis/solids only. Barrel-body midpoint is a provisional "
            "thread-axis proxy; delivered barrel thread location, bolt thread span, "
            "engagement, head/washer dimensions, tolerances, tools, reassembly, "
            "joint resistance and whole-frame strength remain unverified. "
            "A positive tip-to-bore clearance is not an installed-fit PASS."
        ),
    }


if __name__ == "__main__":
    print(json.dumps(build_report(), indent=2))
