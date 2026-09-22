"""Audit the barrel viewer's nominal barrel-bolt axial stacks.

This reads assembled solids and diagnostic bolt axes, not producer defaults or
retail thread drawings. A centered thread axis is only a CAD assumption.
"""

import json
from math import isclose, isfinite, pi

import cadquery as cq
from OCP.BRepAdaptor import BRepAdaptor_Surface

from scripts import simple_owner_duty_ledger as ledger
from scripts.export_owner_barrel_scene import build_integrated_viewer_assembly

SCHEMA = "owner_barrel_installed_stack_audit/v3"
MM_TOL = 1e-4
OUTER_RAIL_FAMILIES = frozenset({"bottom_outer", "lower_outer", "upper_outer"})
TRIAL_BORE_TIP_CLEARANCE_MM = 2.0
PARTIAL_THREAD_COMPARATOR_MM = 19.05  # 3/4 in nominal male end thread


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


def _thread_body_overlap(near_wall, far_wall, tip, end_thread_length):
    """Optimistic axial common length of male end thread and barrel body."""
    if (
        not all(
            isfinite(value) for value in (near_wall, far_wall, tip, end_thread_length)
        )
        or far_wall <= near_wall
        or end_thread_length < 0
    ):
        raise ValueError("Require a finite barrel interval and nonnegative thread span")
    return max(0.0, min(tip, far_wall) - max(tip - end_thread_length, near_wall))


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
        "partial_thread_comparator_body_overlap_mm": _rounded(
            _thread_body_overlap(
                near_wall, far_wall, shaft_tip, PARTIAL_THREAD_COMPARATOR_MM
            )
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


def _family_axial_windows(rows):
    """Group necessary centerline reach and conservative no-overrun sensitivities."""
    grouped = {}
    duties = ledger.selected_duties()
    for row in rows:
        family = duties[row["station"]]["family"]
        grouped.setdefault(family, []).append(row)
    result = {}
    for family, members in sorted(grouped.items()):
        minimum = max(row["assumed_thread_axis_reach_mm"] for row in members)
        far_wall = min(row["reach_to_barrel_far_wall_mm"] for row in members)
        bore_cap = min(
            row["machine_bore_far_cap_from_shaft_start_mm"]
            - TRIAL_BORE_TIP_CLEARANCE_MM
            for row in members
        )
        maximum = min(far_wall, bore_cap)
        lengths = sorted({row["shaft_length_mm"] for row in members})
        result[family] = {
            "pair_count": len(members),
            "current_nominal_lengths_mm": lengths,
            "minimum_length_to_assumed_axis_mm": _rounded(minimum),
            "maximum_length_without_far_wall_overrun_mm": _rounded(far_wall),
            "maximum_length_with_existing_bore_and_trial_clearance_mm": (
                _rounded(bore_cap)
            ),
            "trial_bore_tip_clearance_mm": TRIAL_BORE_TIP_CLEARANCE_MM,
            "limiting_nominal_length_mm": _rounded(maximum),
            "nominal_window_exists": minimum <= maximum + MM_TOL,
            "current_lengths_within_nominal_window": all(
                minimum - MM_TOL <= length <= maximum + MM_TOL for length in lengths
            ),
            "minimum_additional_bore_depth_for_current_trial_mm": _rounded(
                max(
                    0.0,
                    *(
                        TRIAL_BORE_TIP_CLEARANCE_MM
                        - row["tip_to_bore_far_cap_clearance_mm"]
                        for row in members
                    ),
                )
            ),
            "maximum_current_far_wall_overrun_mm": _rounded(
                max(0.0, *(row["tip_past_barrel_far_wall_mm"] for row in members))
            ),
            "thread_engagement_qualified": False,
        }
    return result


def build_report(assembly=None):
    """Audit the integrated scene by default; outward-post history is explicit."""
    assembly = build_integrated_viewer_assembly() if assembly is None else assembly
    bolts, barrels = assembly["bolts"], assembly["barrels"]
    expected_barrels = {name.removesuffix("_bolt") for name in bolts}
    placement = assembly.get("post_placement")
    expected_count = 46 if placement == "integrated" else 48
    if (
        placement not in ("integrated", "outward")
        or len(bolts) != expected_count
        or len(barrels) != expected_count
        or expected_barrels != set(barrels)
        or set(assembly["stacks"]) != set(bolts)
        or set(assembly["bolt_station"].values())
        != set(assembly["barrel_station"].values())
        or len(assembly["panel_connections"]) != 66
        or len(assembly["frame_connections"]) != 12
    ):
        raise ValueError("Current barrel viewer inventory changed")
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
    thread_comparator = {
        "source": (
            "Aspen Grade 5 1/4-20 hex-cap specifications for 4, 5 and 6 in; "
            "not the selected Everbilt product specification"
        ),
        "source_urls": {
            "4_in": "https://www.aspenfasteners.com/1-4-20-x-4-hex-head-cap-screws-bolts-coarse-thread-grade-5-steel-yellow-cadmium-plating-ms90725-dfars/",
            "5_in": "https://www.aspenfasteners.com/1-4-20-x-5-hex-head-cap-screws-bolts-unc-coarse-thread-grade-5-steel-zinc-made-in-u-s-a/",
            "6_in": "https://www.aspenfasteners.com/content/2D_PDF/product80/BO016-1420X6.PDF",
        },
        "nominal_end_thread_length_mm": PARTIAL_THREAD_COMPARATOR_MM,
        "near_wall_not_reached_bolts": [
            row["bolt_name"]
            for row in rows
            if row["bolt_end_thread_length_needed_to_reach_near_wall_mm"]
            > PARTIAL_THREAD_COMPARATOR_MM + MM_TOL
        ],
        "zero_nominal_body_thread_overlap_bolts": [
            row["bolt_name"]
            for row in rows
            if row["partial_thread_comparator_body_overlap_mm"] <= MM_TOL
        ],
        "less_than_1mm_nominal_body_thread_overlap_bolts": [
            row["bolt_name"]
            for row in rows
            if row["partial_thread_comparator_body_overlap_mm"] < 1.0 - MM_TOL
        ],
        "thread_engagement_qualified": False,
        "limits": (
            "Optimistic axial body overlap assumes a full-form male thread to "
            "the nominal thread start and female thread throughout the barrel "
            "body. It ignores bolt-tip chamfer, thread runout, internal thread "
            "location, fit tolerances, strength and actual Everbilt thread span. "
            "Zero overlap in this comparator is not a measured product verdict."
        ),
    }
    return {
        "schema": SCHEMA,
        "source": (
            "scripts.export_owner_barrel_scene.build_integrated_viewer_assembly()"
            if placement == "integrated"
            else "scripts.export_owner_barrel_scene.build_viewer_assembly()"
        ),
        "source_basis": "Live producer composition, not exported JSON",
        "row_count": len(rows),
        "rows": rows,
        "family_axial_windows": _family_axial_windows(rows),
        "partial_thread_comparator": thread_comparator,
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
            "A positive tip-to-bore clearance is not an installed-fit PASS. "
            "The family windows use an illustrative 2 mm bore-tip allowance "
            "and no far-wall overrun; neither is a product requirement or "
            "a claim that an off-the-shelf length exists."
        ),
    }


if __name__ == "__main__":
    print(json.dumps(build_report(), indent=2))
