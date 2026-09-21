"""CD-01 direct PB-01 cross-dowel geometry sensitivity; never a drill schedule."""

import json
from dataclasses import dataclass

import cadquery as cq

from mini_moonboard.floor_flush_width import KERF_RIGHT, variant
from scripts.simple_rail_joint_comparison import (
    RAIL,
    UPRIGHT,
    N,
    T,
    _has_hits,
    _purchased_hillman_solids,
    _read_panel_axes,
    _screw_envelope_hits,
)

NEIGHBOR = "base_rail_service_upper_right"
TOLERANCE_MM3 = 0.01
MACHINE_BOLT_NOMINAL_DIAMETER_MM = 6.35
MACHINE_BOLT_TRIAL_BORE_DIAMETER_MM = 7.5

# These values define a reproducible geometry sensitivity only. Home Depot's
# public 801914 listing controls none of them.
TRIAL_BARREL_OUTSIDE_DIAMETER_MM = 10.0
TRIAL_BARREL_LENGTH_MM = 16.0
TRIAL_THREAD_AXIS_FROM_BARREL_END_MM = 8.0
TRIAL_MACHINE_BOLT_LENGTH_MM = 127.0

BARREL_X_FROM_BUTT_MM = 70.0
ROW_N_MM = (265.0, 310.0)
ACCESS_DIAMETER_MM = 20.0
ACCESS_LENGTH_MM = 40.0


@dataclass(frozen=True)
class FastenerPose:
    name: str
    n_mm: float
    entry_face: str
    barrel_insertion_depth_mm: float
    thread_axis_from_barrel_end_mm: float


def _cylinder(point, axis, length, diameter):
    return cq.Solid.makeCylinder(
        diameter / 2, length, cq.Vector(*point), cq.Vector(*axis)
    )


def _xyz(x, t, n):
    return (x, t * T[0] + n * N[0], t * T[1] + n * N[1])


def _local_bounds(shape):
    vertices = shape.Vertices()
    return {
        "x": (min(v.X for v in vertices), max(v.X for v in vertices)),
        "t": (
            min(v.Y * T[0] + v.Z * T[1] for v in vertices),
            max(v.Y * T[0] + v.Z * T[1] for v in vertices),
        ),
        "n": (
            min(v.Y * N[0] + v.Z * N[1] for v in vertices),
            max(v.Y * N[0] + v.Z * N[1] for v in vertices),
        ),
    }


def _panel_axes():
    rows = _read_panel_axes()
    historical = {
        row["name"]: _cylinder(
            tuple(float(row[f"start_{axis}_mm"]) for axis in "xyz"),
            tuple(float(row[f"direction_{axis}"]) for axis in "xyz"),
            float(row["occupied_length_mm"]),
            float(row["occupied_diameter_mm"]),
        )
        for row in rows
    }
    metadata, purchased = _purchased_hillman_solids(rows)
    return historical, metadata, purchased


def _hits(shape, others):
    return {
        name: round(shape.intersect(other).Volume(), 3)
        for name, other in others.items()
        if shape.intersect(other).Volume() > TOLERANCE_MM3
    }


def _contained_volume(shape, members):
    measured = sum(shape.intersect(member).Volume() for member in members)
    return {
        "envelope_mm3": round(shape.Volume(), 3),
        "wood_intersection_mm3": round(measured, 3),
        "contained_within_1_mm3": abs(shape.Volume() - measured) <= 1.0,
    }


def _fastener_report(
    spec,
    *,
    bounds,
    principal,
    rail,
    protected,
    purchased_screws,
    unrelated,
):
    butt_x = bounds["rail"]["x"][0]
    principal_outer_x = bounds["principal"]["x"][0]
    receiver_x = butt_x + BARREL_X_FROM_BUTT_MM
    t_min, t_max = bounds["rail"]["t"]
    insertion = spec.barrel_insertion_depth_mm
    thread_offset = spec.thread_axis_from_barrel_end_mm
    if (
        insertion < 0
        or thread_offset <= MACHINE_BOLT_NOMINAL_DIAMETER_MM / 2
        or thread_offset
        >= TRIAL_BARREL_LENGTH_MM - MACHINE_BOLT_NOMINAL_DIAMETER_MM / 2
    ):
        raise ValueError("trial insertion or thread offset leaves invalid barrel metal")
    if spec.entry_face == "minus_t":
        entry_t = t_min
        barrel_axis = (0.0, T[0], T[1])
        access_axis = (0.0, -T[0], -T[1])
        barrel_body_t = entry_t + insertion
        thread_t = barrel_body_t + thread_offset
        opposite_wood = t_max - (barrel_body_t + TRIAL_BARREL_LENGTH_MM)
    elif spec.entry_face == "plus_t":
        entry_t = t_max
        barrel_axis = (0.0, -T[0], -T[1])
        access_axis = (0.0, T[0], T[1])
        barrel_body_t = entry_t - insertion
        thread_t = barrel_body_t - thread_offset
        opposite_wood = (barrel_body_t - TRIAL_BARREL_LENGTH_MM) - t_min
    else:
        raise ValueError("entry face must be minus_t or plus_t")

    machine_start = _xyz(principal_outer_x, thread_t, spec.n_mm)
    machine_length_to_thread_axis = receiver_x - principal_outer_x
    machine_envelope_length = TRIAL_MACHINE_BOLT_LENGTH_MM
    machine_bore = _cylinder(
        machine_start,
        (1, 0, 0),
        machine_envelope_length,
        MACHINE_BOLT_TRIAL_BORE_DIAMETER_MM,
    )
    barrel_entry = _xyz(receiver_x, entry_t, spec.n_mm)
    barrel_start = _xyz(receiver_x, barrel_body_t, spec.n_mm)
    barrel = _cylinder(
        barrel_start,
        barrel_axis,
        TRIAL_BARREL_LENGTH_MM,
        TRIAL_BARREL_OUTSIDE_DIAMETER_MM,
    )
    barrel_cross_bore = _cylinder(
        barrel_entry,
        barrel_axis,
        insertion + TRIAL_BARREL_LENGTH_MM,
        TRIAL_BARREL_OUTSIDE_DIAMETER_MM,
    )
    bolt_access = _cylinder(
        machine_start,
        (-1, 0, 0),
        ACCESS_LENGTH_MM,
        ACCESS_DIAMETER_MM,
    )
    barrel_access = _cylinder(
        barrel_entry,
        access_axis,
        ACCESS_LENGTH_MM,
        ACCESS_DIAMETER_MM,
    )
    bolt_radius = MACHINE_BOLT_TRIAL_BORE_DIAMETER_MM / 2
    barrel_radius = TRIAL_BARREL_OUTSIDE_DIAMETER_MM / 2
    t_edges = (thread_t - t_min - bolt_radius, t_max - thread_t - bolt_radius)
    n_edges_bolt = (
        spec.n_mm - bounds["rail"]["n"][0] - bolt_radius,
        bounds["rail"]["n"][1] - spec.n_mm - bolt_radius,
    )
    n_edges_barrel = (
        spec.n_mm - bounds["rail"]["n"][0] - barrel_radius,
        bounds["rail"]["n"][1] - spec.n_mm - barrel_radius,
    )
    physical_envelopes = {
        "machine_bolt_bore_and_tip": machine_bore,
        "barrel_cross_bore": barrel_cross_bore,
        "barrel_body": barrel,
        "bolt_head_approach": bolt_access,
        "barrel_insertion_removal_approach": barrel_access,
    }
    purchased_screen = _screw_envelope_hits(physical_envelopes, purchased_screws)
    thread_radius = MACHINE_BOLT_NOMINAL_DIAMETER_MM / 2
    return {
        "name": spec.name,
        "machine_bolt": {
            "axis": "+X; principal outside face into rail end",
            "start_xyz_mm": [round(value, 3) for value in machine_start],
            "thread_axis_xyz_mm": [
                round(value, 3) for value in _xyz(receiver_x, thread_t, spec.n_mm)
            ],
            "wood_path_to_thread_axis_mm": round(machine_length_to_thread_axis, 3),
            "trial_tip_beyond_thread_axis_mm": (
                round(
                    TRIAL_MACHINE_BOLT_LENGTH_MM - machine_length_to_thread_axis,
                    3,
                )
            ),
            "trial_under_head_axis_to_tip_mm_excluding_head_washer": round(
                machine_envelope_length, 3
            ),
            "trial_tip_beyond_barrel_far_surface_mm": round(
                TRIAL_MACHINE_BOLT_LENGTH_MM
                - machine_length_to_thread_axis
                - TRIAL_BARREL_OUTSIDE_DIAMETER_MM / 2,
                3,
            ),
            "nominal_diameter_mm_from_1_4_20_listing": (
                MACHINE_BOLT_NOMINAL_DIAMETER_MM
            ),
            "trial_wood_bore_diameter_mm_not_drill_size": (
                MACHINE_BOLT_TRIAL_BORE_DIAMETER_MM
            ),
            "wood_path": _contained_volume(machine_bore, (principal, rail)),
            "trial_radial_wood_to_rail_t_faces_mm": [round(v, 3) for v in t_edges],
            "trial_radial_wood_to_rail_n_faces_mm": [round(v, 3) for v in n_edges_bolt],
            "protected_axis_clashes_mm3": _hits(machine_bore, protected),
            "unrelated_part_clashes_mm3": _hits(machine_bore, unrelated),
            "entry_access_clashes_mm3": _hits(bolt_access, unrelated),
        },
        "receiver": {
            "type": "transverse steel cross-dowel/barrel nut",
            "entry_face": spec.entry_face,
            "timber_entry_xyz_mm": [round(value, 3) for value in barrel_entry],
            "barrel_body_start_xyz_mm": [round(value, 3) for value in barrel_start],
            "axis_xyz": [round(value, 6) for value in barrel_axis],
            "barrel_insertion_depth_mm": round(insertion, 3),
            "thread_axis_from_barrel_end_mm": thread_offset,
            "bolt_depth_from_timber_face_mm": round(insertion + thread_offset, 3),
            "trial_outside_diameter_mm_unverified_for_801914": (
                TRIAL_BARREL_OUTSIDE_DIAMETER_MM
            ),
            "trial_length_mm_unverified_for_801914": TRIAL_BARREL_LENGTH_MM,
            "body_path": _contained_volume(barrel, (rail,)),
            "cross_bore_path": _contained_volume(barrel_cross_bore, (rail,)),
            "trial_radial_wood_to_rail_n_faces_mm": [
                round(v, 3) for v in n_edges_barrel
            ],
            "trial_wood_beyond_body_at_opposite_t_face_mm": round(opposite_wood, 3),
            "protected_axis_clashes_mm3": _hits(barrel, protected),
            "unrelated_part_clashes_mm3": _hits(barrel, unrelated),
            "cross_bore_protected_axis_clashes_mm3": _hits(
                barrel_cross_bore, protected
            ),
            "cross_bore_unrelated_part_clashes_mm3": _hits(
                barrel_cross_bore, unrelated
            ),
            "entry_access_clashes_mm3": _hits(barrel_access, unrelated),
            "machine_bore_intersection_mm3": round(
                barrel.intersect(machine_bore).Volume(), 3
            ),
            "nominal_metal_beyond_thread_major_radius_mm": [
                round(thread_offset - thread_radius, 3),
                round(TRIAL_BARREL_LENGTH_MM - thread_offset - thread_radius, 3),
            ],
            "loaded_barrel_length_mm": None,
            "thread_minor_diameter_mm": None,
            "thread_engagement_length_mm": None,
            "effective_thread_engagement_mm": None,
            "first_complete_thread_datum_mm": None,
            "barrel_thread_chamfer_mm": None,
            "bottoming_clearance_verified": False,
            "barrel_bore_clearance_mm": None,
            "barrel_alignment_method_verified": False,
            "barrel_depth_stop_or_support_verified": False,
            "barrel_removal_method_verified": False,
        },
        "purchased_hillman_screen": purchased_screen,
        "solids": {
            "machine_bore": machine_bore,
            "barrel": barrel,
            "barrel_cross_bore": barrel_cross_bore,
        },
    }


def _pose(
    name,
    specs,
    *,
    bounds,
    principal,
    rail,
    protected,
    purchased_screws,
    unrelated,
):
    reports = [
        _fastener_report(
            spec,
            bounds=bounds,
            principal=principal,
            rail=rail,
            protected=protected,
            purchased_screws=purchased_screws,
            unrelated=unrelated,
        )
        for spec in specs
    ]
    first, second = reports
    bolt_gap = first["solids"]["machine_bore"].distance(
        second["solids"]["machine_bore"]
    )
    barrel_gap = first["solids"]["barrel"].distance(second["solids"]["barrel"])
    cross_bore_gap = first["solids"]["barrel_cross_bore"].distance(
        second["solids"]["barrel_cross_bore"]
    )
    geometry_clear_under_trial_dimensions = (
        all(
            report[family][key]["contained_within_1_mm3"]
            for report in reports
            for family, key in (
                ("machine_bolt", "wood_path"),
                ("receiver", "body_path"),
                ("receiver", "cross_bore_path"),
            )
        )
        and all(
            not report[family][key]
            for report in reports
            for family, key in (
                ("machine_bolt", "protected_axis_clashes_mm3"),
                ("machine_bolt", "unrelated_part_clashes_mm3"),
                ("machine_bolt", "entry_access_clashes_mm3"),
                ("receiver", "protected_axis_clashes_mm3"),
                ("receiver", "unrelated_part_clashes_mm3"),
                ("receiver", "cross_bore_protected_axis_clashes_mm3"),
                ("receiver", "cross_bore_unrelated_part_clashes_mm3"),
                ("receiver", "entry_access_clashes_mm3"),
            )
        )
        and all(
            not _has_hits(report["purchased_hillman_screen"]["clashes_mm3"])
            for report in reports
        )
    )
    public_product_geometry_matches_trial = False
    cleaned = []
    for report in reports:
        cleaned.append({key: value for key, value in report.items() if key != "solids"})
    return {
        "name": name,
        "fasteners": cleaned,
        "machine_bore_surface_gap_mm": round(bolt_gap, 3),
        "barrel_body_surface_gap_mm": round(barrel_gap, 3),
        "barrel_cross_bore_surface_gap_mm": round(cross_bore_gap, 3),
        "geometry_clear_under_unverified_trial_dimensions": (
            geometry_clear_under_trial_dimensions
        ),
        "public_product_geometry_matches_trial": public_product_geometry_matches_trial,
        "actual_801914_geometry_clear": None,
        "structural_capacity_checked": False,
        "drilling_released": False,
    }


def screen():
    """Build one recessed, centered direct-joint pose."""
    raw = {part.name: part.shape for part in variant(KERF_RIGHT).uncut_wood_parts()}
    principal = raw[UPRIGHT]
    rail = raw[RAIL]
    protected, hillman_metadata, purchased_screws = _panel_axes()
    unrelated = {
        name: shape for name, shape in raw.items() if name not in {UPRIGHT, RAIL}
    }
    bounds = {
        "principal": _local_bounds(principal),
        "rail": _local_bounds(rail),
    }
    rail_t = bounds["rail"]["t"][1] - bounds["rail"]["t"][0]
    insertion = round((rail_t - TRIAL_BARREL_LENGTH_MM) / 2, 3)
    recessed = _pose(
        "recessed_centered_receiver_pair",
        (
            FastenerPose(
                "cd1",
                ROW_N_MM[0],
                "minus_t",
                insertion,
                TRIAL_THREAD_AXIS_FROM_BARREL_END_MM,
            ),
            FastenerPose(
                "cd2",
                ROW_N_MM[1],
                "plus_t",
                insertion,
                TRIAL_THREAD_AXIS_FROM_BARREL_END_MM,
            ),
        ),
        bounds=bounds,
        principal=principal,
        rail=rail,
        protected=protected,
        purchased_screws=purchased_screws,
        unrelated=unrelated,
    )
    return {
        "study": "CD-01 direct steel cross-dowel at PB-01 only",
        "participants": [UPRIGHT, RAIL],
        "fixed_panel_and_kicker_axes_checked": len(protected),
        "purchased_hillman_envelope_basis": hillman_metadata,
        "meeting_surface": {
            "type": "existing end-to-side butt",
            "butt_plane_x_mm": round(bounds["rail"]["x"][0], 3),
            "rail_section_t_by_n_mm": [
                round(bounds["rail"]["t"][1] - bounds["rail"]["t"][0], 3),
                round(bounds["rail"]["n"][1] - bounds["rail"]["n"][0], 3),
            ],
            "rail_grain": "+X",
            "principal_grain": "inclined frame direction; not inferred from box axes",
        },
        "retailer_lead": {
            "retailer": "Home Depot",
            "brand": "Everbilt",
            "model": "801914",
            "internet_number": "204276112",
            "url": "https://www.homedepot.com/p/204276112",
            "verified_on": "2026-09-20",
            "title": "1/4 in.-20 Zinc Plated Cross Dowel Nut (4-Pack)",
            "controlled_public_fields": {
                "internal_thread": "1/4-20",
                "material_description": "zinc plated steel",
                "package_quantity": 4,
                "displayed_package_price_usd": 5.98,
                "fastener_type": "Dowel Nut",
                "connector_bolt_included": False,
            },
            "not_publicly_controlled": [
                "barrel outside diameter and tolerance",
                "barrel length and tolerance",
                "thread-axis position from either insertion end",
                "thread minor diameter, engagement length, and tolerance class",
                "steel grade, yield strength, and heat treatment",
                "barrel transverse-section, bending, or stripping resistance",
                "wood-joint or complete-assembly rating",
            ],
            "manufacturer_contacted": False,
        },
        "dimensioned_retail_lead": {
            "retailer": "Home Depot",
            "brand": "Everbilt",
            "model": "817828",
            "internet_number": "204281673",
            "url": "https://www.homedepot.com/p/204281673",
            "verified_on": "2026-09-20",
            "title": "1/4 in. x 16 mm Type F Zinc Cross Dowel Nut",
            "public_length_mm": 16,
            "trial_length_matches_public_title": True,
            "outside_diameter_thread_axis_and_metal_basis_verified": False,
            "manufacturer_contacted": False,
        },
        "diagnostic_hardware_sensitivity_not_801914_dimensions": {
            "machine_bolt_nominal_diameter_mm": MACHINE_BOLT_NOMINAL_DIAMETER_MM,
            "machine_bolt_trial_wood_bore_diameter_mm": (
                MACHINE_BOLT_TRIAL_BORE_DIAMETER_MM
            ),
            "machine_bolt_trial_under_head_length_mm": (TRIAL_MACHINE_BOLT_LENGTH_MM),
            "barrel_outside_diameter_mm": TRIAL_BARREL_OUTSIDE_DIAMETER_MM,
            "barrel_length_mm": TRIAL_BARREL_LENGTH_MM,
            "barrel_insertion_depth_mm": insertion,
            "thread_axis_from_barrel_end_mm": (TRIAL_THREAD_AXIS_FROM_BARREL_END_MM),
            "bolt_depth_from_timber_face_mm": (
                insertion + TRIAL_THREAD_AXIS_FROM_BARREL_END_MM
            ),
        },
        "poses": [recessed],
        "pose_count": 1,
        "reference_six_inch_corner_block": {
            "size_x_t_n_mm": [139.7, 57.15, 152.4],
            "gross_volume_mm3": round(139.7 * 57.15 * 152.4, 3),
            "bolt_count": 4,
            "interfaces": 2,
            "status": "retained PB-01 comparison reference",
        },
        "inventory_comparison": {
            "recessed_cross_dowel": {
                "added_wood_volume_mm3": 0.0,
                "main_bolts": 2,
                "cross_dowels": 2,
                "interfaces": 1,
                "t_n_drilling": "two 27.05 mm blind cross-bores",
                "strength_established": False,
            },
            "six_inch_corner_block": {
                "added_wood_volume_mm3": round(139.7 * 57.15 * 152.4, 3),
                "main_bolts": 4,
                "cross_dowels": 0,
                "interfaces": 2,
                "t_n_drilling": "four through-bolt stacks",
                "strength_established": False,
            },
            "mechanically_preferable_option": None,
            "observation": (
                "the cross-dowel uses less wood and hardware, but current evidence "
                "does not establish it as mechanically preferable"
            ),
        },
        "comparison_duties": {
            "retained_scenario_names": ["a12-left", "k12-right"],
            "changed_topology_demands": None,
            "corner_block_local_actions_reused": False,
            "status": "names retained for a later CD-02 analysis only",
        },
        "direct_joint_inventory": {
            "added_wood_volume_mm3": 0.0,
            "cross_dowels": 2,
            "machine_bolts": 2,
            "head_washers": 2,
            "optional_pins": 0,
            "drilling_directions": ["+X machine-bolt/end bores", "+/-T barrel bores"],
            "longest_aligned_wood_path_mm": round(
                recessed["fasteners"][0]["machine_bolt"]["wood_path_to_thread_axis_mm"],
                3,
            ),
            "precision_dependency": (
                "each +X bore must intersect a transverse barrel thread axis; "
                "the public SKU does not control that axis location"
            ),
        },
        "connection_mechanism": {
            "separation_x": (
                "machine-bolt head/washer -> bolt tension -> barrel threads -> "
                "barrel bearing in rail; all capacities unresolved"
            ),
            "compression_x": "existing principal-to-rail butt-face contact",
            "shear_t_and_n": (
                "machine-bolt shank bearing along the principal and end-entering "
                "rail bores; wood bearing, splitting, and bolt yield unresolved"
            ),
            "rotation": (
                "two N-separated bolt axes at the rail T center provide a candidate "
                "force-couple "
                "route with face contact; stiffness, contact state, and capacity unresolved"
            ),
            "friction_credited": False,
            "locating_or_shear_pin_credited": False,
        },
        "cost_and_assembly": {
            "barrel_consumed_cost_usd": 2.99,
            "barrel_checkout_cost_usd": 5.98,
            "machine_bolts_washers_bits_jig_cost_usd": None,
            "corner_block_wood_checkout_and_consumed_cost_usd": None,
            "direct_complete_cost_usd": None,
            "known_assembly_sequence": [
                "cross-drill two barrel entry holes from opposite rail T faces",
                "drill two end-entry bolt paths through principal into the rail",
                "insert and align both barrels at their accessible T faces",
                "seat two bolt heads/washers at the principal outside face and tighten",
            ],
            "alignment_jig_and_delivered_hardware_fit_verified": False,
            "repeat_disassembly_uses_accessible_metal_threads": True,
        },
        "method_limits": {
            "pb01_archived_corner_block_reactions_transferred": False,
            "pb01_named_scenarios_reanalyzed_for_changed_topology": False,
            "awc_tr12_barrel_anchorage_rating_claimed": False,
            "usda_fpl_rp_586_load_values_scaled_to_furniture_barrel": False,
            "wood_bearing_splitting_tearout_net_section_checked": False,
            "barrel_thread_stripping_bending_section_checked": False,
            "bolt_head_washer_and_steel_checked": False,
            "purchased_hillman_physical_clearance_accepted": False,
            "complete_joint_utilization": None,
        },
        "decision": {
            "cd01": "hold_before_CD-02",
            "geometry_observation": (
                "one recessed centered pose clears the retained model and both "
                "conditional purchased-screw envelopes under unverified barrel "
                "dimensions"
            ),
            "blocking_reason": (
                "801914 does not publish barrel geometry; the separate 817828 title "
                "publishes 16 mm length but not the outside diameter, thread-axis "
                "position, tolerances, or metal basis needed to establish alignment, "
                "remaining wood, or a supportable mechanics route"
            ),
            "structural_verdict": None,
            "hardware_selected": False,
            "fabrication_or_drilling_released": False,
        },
    }


if __name__ == "__main__":
    print(json.dumps(screen(), indent=2, sort_keys=True))
