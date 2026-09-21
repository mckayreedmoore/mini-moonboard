"""Isolated PB03 outer-upright counterbore geometry; no strength or release."""

import json
import math
from itertools import combinations

import cadquery as cq

from scripts import simple_pb03_bottom_outer_pair as bottom
from scripts import simple_pb03_lower_center_pair as lower
from scripts import simple_pb03_upper_outer_pair as upper
from scripts.simple_pb03_native import SOURCE_ID as PB03_SOURCE_ID
from scripts.simple_pb03_native import PB03Native

MM_PER_IN = 25.4
BOLT_LENGTH_MM = 8.0 * MM_PER_IN
BOLT_LISTED_THREAD_LENGTH_MM = 6.0 * MM_PER_IN
ORIGINAL_GRIP_MM = 9.0 * MM_PER_IN
WASHER_EACH_SIDE_MM = 0.065 * MM_PER_IN
WASHER_OUTSIDE_DIAMETER_MM = 0.734 * MM_PER_IN
NUT_HEIGHT_MM = 0.226 * MM_PER_IN
NUT_MAX_ACROSS_CORNERS_MM = 0.505 * MM_PER_IN
THREAD_PITCH_MM = MM_PER_IN / 20.0
TWO_THREAD_PROJECTION_MM = 2.0 * THREAD_PITCH_MM
FORSTNER_DIAMETER_MM = 1.0 * MM_PER_IN
SOCKET_DIAMETER_MM = 0.75 * MM_PER_IN
TOOL_APPROACH_MM = 3.0 * MM_PER_IN
HARDWARE_SOURCES = {
    "bolt": "https://www.homedepot.com/p/204281626",
    "washer_dimensions": (
        "https://images.thdstatic.com/catalog/pdfImages/"
        "4a/4a362438-0e50-481c-af25-7f98aa28c057.pdf"
    ),
    "nut_dimensions": (
        "https://brassland.com/resources/tools/asme-b18-2-2-hex-nut-dimensions/"
    ),
    "forstner_bit": "https://www.homedepot.com/p/100098841",
}
TARGET_STATIONS = (
    *lower.LOWER_OUTER_STATIONS,
    *upper.TARGET_STATIONS,
    *bottom.TARGET_STATIONS,
)


def _required_depth_mm():
    return (
        ORIGINAL_GRIP_MM
        + 2 * WASHER_EACH_SIDE_MM
        + NUT_HEIGHT_MM
        + TWO_THREAD_PROJECTION_MM
        - BOLT_LENGTH_MM
    )


def _cylinder(point, direction, length, diameter):
    return cq.Solid.makeCylinder(
        diameter / 2,
        length,
        cq.Vector(*point),
        cq.Vector(*direction),
    )


def _volume_hits(shape, solids, *, exclude=()):
    excluded = set(exclude)
    return {
        name: round(volume, 6)
        for name, other in solids.items()
        if name not in excluded
        and (volume := lower._intersection_volume(shape, other)) > lower.TOL_MM3
    }


def _axis_geometry_signature(row):
    return (
        row.name,
        row.start.toTuple(),
        row.direction.toTuple(),
        row.length,
        row.diameter,
        row.kind,
        row.grip,
    )


def _same_box(first, second):
    left, right = first.BoundingBox(), second.BoundingBox()
    return all(
        math.isclose(getattr(left, name), getattr(right, name), abs_tol=1.0e-6)
        for name in ("xmin", "xmax", "ymin", "ymax", "zmin", "zmax")
    )


def screen(*, forstner_diameter_mm=FORSTNER_DIAMETER_MM):
    """Screen detached pockets against the authenticated eight-station source."""
    minimum_seat_diameter = max(
        WASHER_OUTSIDE_DIAMETER_MM,
        NUT_MAX_ACROSS_CORNERS_MM,
        SOCKET_DIAMETER_MM,
    )
    if (
        not math.isfinite(forstner_diameter_mm)
        or forstner_diameter_mm < minimum_seat_diameter
    ):
        raise ValueError("Forstner diameter cannot clear the washer and socket")

    module = PB03Native()
    geometries = module.pb03_geometries()
    if (
        module.KEY != PB03_SOURCE_ID
        or module.ACTIVE_FINGERPRINT != lower.EXPECTED_PB02_FINGERPRINT
        or not set(TARGET_STATIONS) <= set(geometries)
    ):
        raise ValueError("PB03 counterbore source identity changed")

    panel_axes = tuple(module.panel_connections())
    original_panel_axes = tuple(module.raw.panel_connections())
    fixed_axes_unchanged = (
        len(panel_axes) == len(original_panel_axes) == 66
        and len({row.name for row in panel_axes}) == 66
        and tuple(map(_axis_geometry_signature, panel_axes))
        == tuple(map(_axis_geometry_signature, original_panel_axes))
    )
    fixed_axis_solids = lower._fixed_axis_solids(panel_axes)
    all_parts = {part.name: part.shape for part in module.wood_parts()}
    panel_parts = {
        name: shape
        for name, shape in all_parts.items()
        if name.startswith(("main_", "kicker_"))
    }
    timber_parts = {
        name: shape for name, shape in all_parts.items() if name not in panel_parts
    }
    all_bores = {
        f"{station}/{name}": bore
        for station, geometry in geometries.items()
        for name, bore in geometry.bores.items()
    }
    all_stacks = {
        f"{station}/{name}/{role}": shape
        for station, geometry in geometries.items()
        for name, stack in geometry.stacks.items()
        for role, shape in stack.items()
    }

    depth = _required_depth_mm()
    pockets = {}
    approach_tools = {}
    socket_tools = {}
    counterbored_blocks = {}
    target_upright_bolts = []
    target_rail_bolts = []
    for station in TARGET_STATIONS:
        geometry = geometries[station]
        upright_bolts = [
            bolt for bolt in geometry.bolts if bolt.members[0] == geometry.upright_name
        ]
        rail_bolts = [
            bolt for bolt in geometry.bolts if bolt.members[0] == geometry.rail_name
        ]
        if len(upright_bolts) != 2 or len(rail_bolts) != 2:
            raise ValueError(f"{station}: PB03 outer bolt inventory changed")
        target_upright_bolts.extend(upright_bolts)
        target_rail_bolts.extend(rail_bolts)
        station_pockets = []
        for bolt in upright_bolts:
            direction = bolt.direction.normalized()
            wood_start = bolt.start + direction * lower.END_ALLOWANCE_MM
            outer_face = wood_start + direction * bolt.grip
            pocket = _cylinder(
                outer_face.toTuple(),
                (-direction).toTuple(),
                depth,
                forstner_diameter_mm,
            )
            key = f"{station}/{bolt.name}"
            pockets[key] = pocket
            station_pockets.append(pocket)
            approach_tools[key] = _cylinder(
                outer_face.toTuple(),
                direction.toTuple(),
                TOOL_APPROACH_MM,
                forstner_diameter_mm,
            )
            seat = outer_face - direction * depth
            socket_tools[key] = _cylinder(
                seat.toTuple(),
                direction.toTuple(),
                depth,
                SOCKET_DIAMETER_MM,
            )
        revised = geometry.block
        for pocket in station_pockets:
            revised = revised.cut(pocket)
        counterbored_blocks[station] = revised

    if len(pockets) != 12:
        raise ValueError("PB03 counterbore inventory changed")

    pocket_unintended_bore_hits = {}
    pocket_preserved_stack_hits = {}
    pocket_unrelated_timber_hits = {}
    pocket_panel_hits = {}
    pocket_fixed_axis_hits = {}
    tool_obstruction_hits = {}
    socket_outside_pocket = {}
    intended_bores_open = {}
    pocket_inside_block = {}
    unintended_bore_clearances = []
    for key, pocket in pockets.items():
        station, bolt_name = key.split("/", 1)
        geometry = geometries[station]
        own_bore = f"{station}/{bolt_name}"
        pocket_unintended_bore_hits.update(
            {
                f"{key}|{name}": volume
                for name, volume in _volume_hits(
                    pocket, all_bores, exclude=(own_bore,)
                ).items()
            }
        )
        intended_bores_open[key] = (
            lower._intersection_volume(pocket, all_bores[own_bore]) > lower.TOL_MM3
        )
        for name, bore in all_bores.items():
            if name != own_bore:
                unintended_bore_clearances.append(pocket.distance(bore))
        own_stack_prefix = f"{station}/{bolt_name}/"
        preserved_stacks = {
            name: shape
            for name, shape in all_stacks.items()
            if not name.startswith(own_stack_prefix)
        }
        pocket_preserved_stack_hits.update(
            {
                f"{key}|{name}": volume
                for name, volume in _volume_hits(pocket, preserved_stacks).items()
            }
        )
        unrelated_timber = {
            name: shape
            for name, shape in timber_parts.items()
            if name != geometry.block_name
        }
        pocket_unrelated_timber_hits.update(
            {
                f"{key}|{name}": volume
                for name, volume in _volume_hits(pocket, unrelated_timber).items()
            }
        )
        pocket_panel_hits.update(
            {
                f"{key}|{name}": volume
                for name, volume in _volume_hits(pocket, panel_parts).items()
            }
        )
        pocket_fixed_axis_hits.update(
            {
                f"{key}|{name}": volume
                for name, volume in _volume_hits(pocket, fixed_axis_solids).items()
            }
        )
        pocket_inside_block[key] = math.isclose(
            lower._intersection_volume(pocket, geometry.block),
            pocket.Volume(),
            abs_tol=lower.TOL_MM3,
        )

        approach = approach_tools[key]
        obstructions = {
            **{f"timber/{name}": shape for name, shape in unrelated_timber.items()},
            **{f"panel/{name}": shape for name, shape in panel_parts.items()},
            **{f"axis/{name}": shape for name, shape in fixed_axis_solids.items()},
            **{f"stack/{name}": shape for name, shape in preserved_stacks.items()},
        }
        tool_obstruction_hits.update(
            {
                f"{key}|{name}": volume
                for name, volume in _volume_hits(approach, obstructions).items()
            }
        )
        outside = socket_tools[key].cut(pocket).Volume()
        if outside > lower.TOL_MM3:
            socket_outside_pocket[key] = round(outside, 6)

    pocket_pair_clearances = [
        first.distance(second) for first, second in combinations(pockets.values(), 2)
    ]
    pocket_pair_hits = {
        f"{first_name}|{second_name}": round(volume, 6)
        for (first_name, first), (second_name, second) in combinations(
            pockets.items(), 2
        )
        if (volume := lower._intersection_volume(first, second)) > lower.TOL_MM3
    }
    block_shapes_preserved = all(
        _same_box(geometries[name].block, counterbored_blocks[name])
        for name in TARGET_STATIONS
    )
    quarter_inch_shafts_preserved = all(
        math.isclose(bolt.diameter, lower.BOLT_DIAMETER_MM, abs_tol=1.0e-9)
        and math.isclose(bolt.grip, ORIGINAL_GRIP_MM, abs_tol=1.0e-9)
        for bolt in target_upright_bolts
    )
    rail_stacks_preserved = len(target_rail_bolts) == 12 and all(
        math.isclose(bolt.diameter, lower.BOLT_DIAMETER_MM, abs_tol=1.0e-9)
        and math.isclose(bolt.grip, 38.1 + lower.BLOCK_T_MM, abs_tol=1.0e-9)
        for bolt in target_rail_bolts
    )
    source_geometry_preserved = (
        block_shapes_preserved
        and tuple(name for name in geometries if name in TARGET_STATIONS)
        == TARGET_STATIONS
    )
    collision_results = (
        pocket_unintended_bore_hits,
        pocket_preserved_stack_hits,
        pocket_unrelated_timber_hits,
        pocket_panel_hits,
        pocket_fixed_axis_hits,
        tool_obstruction_hits,
        socket_outside_pocket,
        pocket_pair_hits,
    )
    all_geometry_checks_pass = (
        source_geometry_preserved
        and quarter_inch_shafts_preserved
        and rail_stacks_preserved
        and fixed_axes_unchanged
        and all(pocket_inside_block.values())
        and all(intended_bores_open.values())
        and not any(collision_results)
    )
    revised_grip = ORIGINAL_GRIP_MM - depth
    unthreaded_length_mm = BOLT_LENGTH_MM - BOLT_LISTED_THREAD_LENGTH_MM
    far_wood_face_from_under_head_mm = WASHER_EACH_SIDE_MM + revised_grip
    thread_beyond_wood_mm = BOLT_LENGTH_MM - far_wood_face_from_under_head_mm
    required_thread_beyond_wood_mm = (
        WASHER_EACH_SIDE_MM + NUT_HEIGHT_MM + TWO_THREAD_PROJECTION_MM
    )
    listed_thread_length_pass = (
        far_wood_face_from_under_head_mm >= unthreaded_length_mm - 1.0e-9
        and thread_beyond_wood_mm >= required_thread_beyond_wood_mm - 1.0e-9
    )
    all_geometry_checks_pass = all_geometry_checks_pass and listed_thread_length_pass
    result = {
        "schema": "simple_pb03_outer_counterbore_revision/v1",
        "pb03_source_id": PB03_SOURCE_ID,
        "pb02_source_fingerprint": module.ACTIVE_FINGERPRINT,
        "hardware_sources": HARDWARE_SOURCES,
        "target_stations": list(TARGET_STATIONS),
        "inventory": {
            "stations": len(TARGET_STATIONS),
            "upright_bolts": len(target_upright_bolts),
            "counterbores": len(pockets),
            "unchanged_rail_stacks": len(target_rail_bolts),
            "fixed_panel_kicker_axes": len(panel_axes),
        },
        "stack_basis": {
            "bolt_product": "Everbilt 800696",
            "retailer": "Home Depot",
            "bolt_nominal_size": "1/4-20 x 8 in",
            "bolt_listing_basis": "ASTM A307; six-inch listed thread length",
            "bolt_nominal_length_mm": BOLT_LENGTH_MM,
            "bolt_listed_thread_length_mm": BOLT_LISTED_THREAD_LENGTH_MM,
            "original_wood_grip_mm": ORIGINAL_GRIP_MM,
            "washer_each_side_mm": WASHER_EACH_SIDE_MM,
            "washer_outside_diameter_mm": WASHER_OUTSIDE_DIAMETER_MM,
            "nut_height_mm": NUT_HEIGHT_MM,
            "nut_max_across_corners_mm": NUT_MAX_ACROSS_CORNERS_MM,
            "two_thread_projection_mm": TWO_THREAD_PROJECTION_MM,
            "required_counterbore_depth_mm": depth,
            "revised_wood_grip_mm": revised_grip,
            "stack_length_mm": (
                revised_grip
                + 2 * WASHER_EACH_SIDE_MM
                + NUT_HEIGHT_MM
                + TWO_THREAD_PROJECTION_MM
            ),
            "thread_start_from_under_head_mm": unthreaded_length_mm,
            "far_wood_face_from_under_head_mm": far_wood_face_from_under_head_mm,
            "thread_beyond_wood_mm": thread_beyond_wood_mm,
            "required_thread_beyond_wood_mm": required_thread_beyond_wood_mm,
            "listed_thread_length_pass": listed_thread_length_pass,
            "forstner_diameter_mm": forstner_diameter_mm,
            "socket_envelope_diameter_mm": SOCKET_DIAMETER_MM,
            "dimensional_scope": (
                "Bolt is an ordinary-retailer product lead. The two 0.065-in "
                "washers follow Home Depot's published Everbilt "
                "washer table; 0.226 in is the published ASME B18.2.2 maximum "
                "finished-nut thickness. The socket is a conservative envelope; "
                "companion parts remain unselected."
            ),
        },
        "source_geometry_preserved": source_geometry_preserved,
        "external_block_boxes_preserved": block_shapes_preserved,
        "quarter_inch_shafts_preserved": quarter_inch_shafts_preserved,
        "rail_stacks_preserved": rail_stacks_preserved,
        "fixed_axes_unchanged": fixed_axes_unchanged,
        "pocket_unintended_bore_hits_mm3": pocket_unintended_bore_hits,
        "pocket_preserved_stack_hits_mm3": pocket_preserved_stack_hits,
        "pocket_unrelated_timber_hits_mm3": pocket_unrelated_timber_hits,
        "pocket_panel_hits_mm3": pocket_panel_hits,
        "pocket_fixed_axis_hits_mm3": pocket_fixed_axis_hits,
        "pocket_to_pocket_hits_mm3": pocket_pair_hits,
        "counterbore_tool_obstruction_hits_mm3": tool_obstruction_hits,
        "socket_outside_pocket_mm3": socket_outside_pocket,
        "all_counterbores_inside_blocks": all(pocket_inside_block.values()),
        "all_intended_bores_open_into_pockets": all(intended_bores_open.values()),
        "governing_ligaments_mm": {
            "axial_wood_beyond_pocket": lower.BLOCK_X_MM - depth,
            "pocket_to_block_edge": lower.BLOCK_T_MM / 2 - forstner_diameter_mm / 2,
            "between_counterbores": min(
                abs(left - right) - forstner_diameter_mm
                for left, right in combinations(lower.UPRIGHT_N_OFFSETS_MM, 2)
            ),
            "pocket_to_unintended_bore": min(unintended_bore_clearances),
            "nearest_other_counterbore": min(pocket_pair_clearances),
        },
        "all_geometry_checks_pass": all_geometry_checks_pass,
        "decision": (
            "PASS_ISOLATED_GEOMETRY_ONLY"
            if all_geometry_checks_pass
            else "REVISE_GEOMETRY"
        ),
        "strength_checked": False,
        "active_design_integrated": False,
        "exact_companion_hardware_selected": False,
        "qualified_for_design": False,
        "drilling_released": False,
        "fabrication_released": False,
        "structural_released": False,
    }
    return result


if __name__ == "__main__":
    print(json.dumps(screen(), indent=2, sort_keys=True))
