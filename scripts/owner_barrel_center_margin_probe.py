"""Bounded center-principal/header barrel and washer-seat CAD sensitivity.

This is a nominal geometry screen, not a hardware, drilling, or strength release.
The six-duty viewer layout is read as a source; only its two principal/header
station poses are rebuilt here. No scene or shared assembly is changed.
"""

import json

import cadquery as cq

from scripts import owner_barrel_center_layout as center
from scripts import owner_layout_protected as protected

SOURCE_ID = "owner-barrel-center-principal-margin-probe-v1"
SIDES = ("left", "right")
TRIAL_WASHER_OD_MM = (22.0, 23.0, 24.0, 25.4)
RETAIL_WASHER_LEAD_OD_MM = 19.05
RETAIL_WASHER_LEAD_THICKNESS_MM = 25.4 / 16
TRIAL_BOLT_LENGTHS_IN = (4.0, 4.5, 5.0)
PROVISIONAL_TIP_PAST_THREAD_AXIS_MM = 10.0
HIT_TOL_MM3 = 1.0
CORE_FRACTION_MIN = 0.999


def _bounds(wood):
    header = wood["base_header"].BoundingBox()
    if abs(header.ymin + 175.7) > 1e-5 or abs(header.ymax + 36.0) > 1e-5:
        raise ValueError("Original kerf-right header Y edges changed")
    for side in SIDES:
        backer = wood[f"inner_kicker_backer_{side}"].BoundingBox()
        if abs(backer.ymin + 124.9) > 1e-5:
            raise ValueError("Fixed kicker-backer rear edge changed")
    return header.ymin, -124.9


def row_window(od_mm, reserve_mm=0.0):
    """Exact Y inequalities for two non-overlapping, flat underside seats."""
    if od_mm <= 0 or reserve_mm < 0:
        raise ValueError("Washer OD must be positive and reserve nonnegative")
    rear, backer = -175.7, -124.9
    rear_min = rear + od_mm / 2 + reserve_mm
    forward_max = backer - od_mm / 2 - reserve_mm
    rear_max = forward_max - od_mm - reserve_mm
    return {
        "rear_row_y_mm": [rear_min, rear_max],
        "forward_row_y_max_mm": forward_max,
        "minimum_row_spacing_mm": od_mm + reserve_mm,
        "nonempty": rear_min <= rear_max + 1e-8,
    }


def balanced_rows(od_mm):
    """Divide available Y slack equally across rear, between, and backer gaps."""
    slack = -124.9 - (-175.7) - 2 * od_mm
    if slack < -1e-7:
        raise ValueError("Two washer seats cannot fit between fixed edges")
    reserve = max(0.0, slack / 3)
    rear = -175.7 + od_mm / 2 + reserve
    forward = rear + od_mm + reserve
    return (rear, forward), reserve


def _full_bolt_tip_bound(wood):
    """Prove the rear nominal tip misses wood throughout this OD/Y window."""
    best_rear_y = row_window(min(TRIAL_WASHER_OD_MM))["rear_row_y_mm"][1]
    minimum_tip_y = []
    for side in SIDES:
        station = f"clip_split_base_center_{side}"
        spec = center._station_spec(station, wood)[1][0]
        tip_z = (
            spec["bolt_seat"][2] + center.BOLT_LENGTH_MM - center.WASHER_THICKNESS_MM
        )
        nmax = center._local_bounds(wood[spec["bolt_hosts"][1]])["n"][1]
        minimum_tip_y.append((center.N[1] * tip_z - nmax) / -center.N[0])
    return {
        "washer_od_range_mm": [min(TRIAL_WASHER_OD_MM), max(TRIAL_WASHER_OD_MM)],
        "most_forward_rear_row_y_mm": round(best_rear_y, 6),
        "nominal_tip_z_mm": round(tip_z, 6),
        "minimum_principal_y_at_tip_z_mm": round(min(minimum_tip_y), 6),
        "tip_y_shortfall_at_most_favorable_row_mm": round(
            min(minimum_tip_y) - best_rear_y, 6
        ),
        "full_nominal_rear_bolt_tip_misses_principal_for_all_seat_rows": (
            best_rear_y < min(minimum_tip_y)
        ),
    }


def _moved_spec(spec, y):
    moved = dict(spec)
    moved["bolt_seat"] = (spec["bolt_seat"][0], y, spec["bolt_seat"][2])
    moved["barrel_entry"] = (spec["barrel_entry"][0], y, spec["barrel_entry"][2])
    return moved


def _nominal_length_window_22mm(wood, rows):
    """Necessary length bounds from provisional axis reach and rear bore edge."""
    lower, upper = [], []
    for side in SIDES:
        station = f"clip_split_base_center_{side}"
        source = center._station_spec(station, wood)[1][0]
        spec = _moved_spec(source, rows[0])
        seat_z = spec["bolt_seat"][2]
        path_to_axis = spec["header_length"] + spec["receiver_length"]
        lower.append(
            path_to_axis
            + center.WASHER_THICKNESS_MM
            + PROVISIONAL_TIP_PAST_THREAD_AXIS_MM
        )
        nmax = center._local_bounds(wood[spec["bolt_hosts"][1]])["n"][1]
        bore_radius = center.BORE_DIAMETER_MM / 2
        tip_z_max = (
            nmax - abs(center.N[0]) * bore_radius - center.N[0] * rows[0]
        ) / center.N[1]
        upper.append(tip_z_max - seat_z + center.WASHER_THICKNESS_MM)
    return {
        "minimum_nominal_length_for_provisional_overrun_mm": round(max(lower), 6),
        "maximum_nominal_length_from_rear_bore_edge_mm": round(min(upper), 6),
        "maximum_nominal_length_from_rear_bore_edge_in": round(min(upper) / 25.4, 6),
        "status": "necessary nominal geometric bounds, not SKU or engagement limits",
    }


def _core_fractions(spec, solids, wood):
    seat, axis = spec["bolt_seat"], spec["bolt_axis"]
    header_segment = center._cylinder(
        seat, axis, spec["header_length"], center.BORE_DIAMETER_MM
    )
    receiver_segment = center._cylinder(
        center._add(seat, axis, spec["header_length"]),
        axis,
        spec["receiver_length"],
        center.BORE_DIAMETER_MM,
    )
    name = next(iter(solids)).split("/")[0]
    barrel_bore = solids[f"{name}/barrel_cross_bore"]
    barrel_body = solids[f"{name}/barrel_body"]
    host, receiver = spec["bolt_hosts"]
    return {
        "header_bolt_bore": protected._volume(header_segment, wood[host])
        / header_segment.Volume(),
        "principal_bolt_bore": protected._volume(receiver_segment, wood[receiver])
        / receiver_segment.Volume(),
        "principal_barrel_bore": protected._volume(barrel_bore, wood[receiver])
        / barrel_bore.Volume(),
        "principal_barrel_body": protected._volume(barrel_body, wood[receiver])
        / barrel_body.Volume(),
    }


def _pair_hits(first, second):
    return {
        f"{a} x {b}": round(volume, 6)
        for a, shape_a in first.items()
        for b, shape_b in second.items()
        if (volume := protected._volume(shape_a, shape_b)) > HIT_TOL_MM3
    }


def screen_pose(
    wood, inventory, od_mm, rows, bolt_length_mm=None, washer_thickness_mm=None
):
    """Screen every hardware, bore, and access solid on both mirrored duties."""
    bolt_length_mm = center.BOLT_LENGTH_MM if bolt_length_mm is None else bolt_length_mm
    washer_thickness_mm = (
        center.WASHER_THICKNESS_MM
        if washer_thickness_mm is None
        else washer_thickness_mm
    )
    if washer_thickness_mm <= 0 or bolt_length_mm <= washer_thickness_mm:
        raise ValueError("Nominal bolt length must exceed washer thickness")
    rear_edge, backer_edge = _bounds(wood)
    rear_y, forward_y = rows
    if rear_y >= forward_y:
        raise ValueError("Rows must be ordered rear to front")
    radius = od_mm / 2
    reserves = {
        "rear_header_edge_mm": rear_y - radius - rear_edge,
        "washer_to_washer_mm": forward_y - rear_y - od_mm,
        "forward_backer_rear_mm": backer_edge - forward_y - radius,
    }
    all_solids, bolts, pair_hits = {}, {}, {}
    header = wood["base_header"].BoundingBox()
    for side in SIDES:
        station = f"clip_split_base_center_{side}"
        family, source_specs, _ = center._station_spec(station, wood)
        if family != "principal_header" or len(source_specs) != 2:
            raise ValueError("Two-bolt principal/header duty changed")
        row_solids = []
        for index, (source, y) in enumerate(zip(source_specs, rows, strict=True), 1):
            spec = _moved_spec(source, y)
            name, solids, datum = center._hardware(station, index, spec)
            seat = spec["bolt_seat"]
            washer_start = center._add(seat, spec["bolt_axis"], -washer_thickness_mm)
            solids[f"{name}/bolt_shaft_full_nominal"] = center._cylinder(
                washer_start,
                spec["bolt_axis"],
                bolt_length_mm,
                center.hardware.THREAD_MAJOR_MM,
            )
            full_bore = center._cylinder(
                seat,
                spec["bolt_axis"],
                bolt_length_mm - washer_thickness_mm,
                center.BORE_DIAMETER_MM,
            )
            solids[f"{name}/bolt_bore_full_nominal"] = full_bore
            solids[f"{name}/washer"] = center._cylinder(
                washer_start, spec["bolt_axis"], washer_thickness_mm, od_mm
            )
            solids[f"{name}/head"] = center._cylinder(
                center._add(washer_start, spec["bolt_axis"], -4.0),
                spec["bolt_axis"],
                4.0,
                center.HEAD_DIAMETER_MM,
            )
            all_solids.update(solids)
            row_solids.append(solids)
            core = _core_fractions(spec, solids, wood)
            host, receiver = spec["bolt_hosts"]
            uncontained_bore = max(
                0.0,
                full_bore.Volume()
                - protected._volume(full_bore, wood[host])
                - protected._volume(full_bore, wood[receiver]),
            )
            tip = center._add(
                seat,
                spec["bolt_axis"],
                bolt_length_mm - washer_thickness_mm,
            )
            embedded_shaft = center._cylinder(
                seat,
                spec["bolt_axis"],
                bolt_length_mm - washer_thickness_mm,
                center.hardware.THREAD_MAJOR_MM,
            )
            uncontained_shaft = max(
                0.0,
                embedded_shaft.Volume()
                - protected._volume(embedded_shaft, wood[host])
                - protected._volume(embedded_shaft, wood[receiver]),
            )
            tip_past_axis = (
                bolt_length_mm
                - washer_thickness_mm
                - datum["bolt_seat_to_thread_axis_mm"]
            )
            unrelated = {
                member: shape
                for member, shape in wood.items()
                if member not in spec["bolt_hosts"]
            }
            wood_hits = {
                feature.removeprefix(name + "/"): hits
                for feature, shape in solids.items()
                if (
                    hits := {
                        member: round(volume, 6)
                        for member, other in unrelated.items()
                        if (volume := protected._volume(shape, other)) > HIT_TOL_MM3
                    }
                )
            }
            bolts[name] = {
                "y_mm": y,
                "bolt_barrel_intersection_mm3": round(
                    protected._volume(full_bore, solids[f"{name}/barrel_cross_bore"]),
                    6,
                ),
                "nominal_tip_beyond_thread_axis_mm": round(tip_past_axis, 6),
                "provisional_tip_past_axis_allowance_met": (
                    tip_past_axis >= PROVISIONAL_TIP_PAST_THREAD_AXIS_MM
                ),
                "minimum_intended_core_fraction": round(min(core.values()), 7),
                "full_nominal_bore_uncontained_mm3": round(uncontained_bore, 6),
                "embedded_nominal_shaft_uncontained_mm3": round(uncontained_shaft, 6),
                "nominal_bolt_tip_xyz_mm": list(tip),
                "nominal_bolt_tip_center_in_principal": wood[receiver].isInside(
                    cq.Vector(*tip), 1e-6
                ),
                "washer_to_header_x_edge_mm": round(
                    min(seat[0] - header.xmin, header.xmax - seat[0]) - radius, 6
                ),
                "washer_to_header_front_edge_mm": round(header.ymax - y - radius, 6),
                "unrelated_wood_hits_mm3": wood_hits,
            }
        pair_hits[station] = _pair_hits(*row_solids)
    protected_hits = protected.hits(all_solids, inventory)
    for name, row in bolts.items():
        row["protected_hits_mm3"] = {
            feature.removeprefix(name + "/"): hits
            for feature, hits in protected_hits.items()
            if feature.startswith(name + "/") and hits
        }
    seat_clear = (
        min(reserves.values()) > 0
        and all(not hits for hits in pair_hits.values())
        and all(
            row["minimum_intended_core_fraction"] >= CORE_FRACTION_MIN
            and row["bolt_barrel_intersection_mm3"] > 0
            and row["washer_to_header_x_edge_mm"] > 0
            and row["washer_to_header_front_edge_mm"] > 0
            and not row["unrelated_wood_hits_mm3"]
            and not row["protected_hits_mm3"]
            for row in bolts.values()
        )
    )
    return {
        "bolt_nominal_length_mm": bolt_length_mm,
        "washer_thickness_mm": washer_thickness_mm,
        "washer_od_mm": od_mm,
        "rows_y_mm": list(rows),
        "seat": "flat header underside; washer centered on each bolt axis",
        "reserves_mm": {key: round(value, 6) for key, value in reserves.items()},
        "pair_hits_mm3": pair_hits,
        "bolts": bolts,
        "washer_seat_cad_opportunity": seat_clear,
        "full_nominal_bolt_bore_contained": all(
            row["full_nominal_bore_uncontained_mm3"] <= HIT_TOL_MM3
            and row["embedded_nominal_shaft_uncontained_mm3"] <= HIT_TOL_MM3
            and row["nominal_bolt_tip_center_in_principal"]
            for row in bolts.values()
        ),
        "provisional_axis_overrun_met": all(
            row["provisional_tip_past_axis_allowance_met"] for row in bolts.values()
        ),
    }


def build():
    """Return bounded nominal CAD evidence without modifying source geometry."""
    source, wood, layout = center._wood()
    _bounds(wood)
    if layout["post_bounds_x_mm"] != {
        "left": [-199.05, -160.95],
        "right": [160.95, 199.05],
    }:
        raise ValueError("Exact X±180 post pose changed")
    inventory = protected.inventory()
    panel = tuple(source.panel_connections())
    frame = tuple(row for row in source.connections() if row.kind == "bolt")
    if len(panel) != 66 or len(frame) != 12:
        raise ValueError("Fixed panel or old frame-bolt inventory changed")
    trials = []
    for od in TRIAL_WASHER_OD_MM:
        rows, reserve = balanced_rows(od)
        trial = screen_pose(wood, inventory, od, rows)
        trial["balanced_reserve_mm"] = round(reserve, 6)
        trials.append(trial)
    bolt_trials = []
    rows_22mm = trials[0]["rows_y_mm"]
    for nominal_in in TRIAL_BOLT_LENGTHS_IN:
        trial = (
            dict(trials[0])
            if nominal_in == 5.0
            else screen_pose(wood, inventory, 22.0, rows_22mm, nominal_in * 25.4)
        )
        trial["bolt_nominal_length_in"] = nominal_in
        trial["nominal_geometry_plausible"] = (
            trial["washer_seat_cad_opportunity"]
            and trial["full_nominal_bolt_bore_contained"]
            and trial["provisional_axis_overrun_met"]
        )
        bolt_trials.append(trial)
    retail_rows, retail_reserve = balanced_rows(RETAIL_WASHER_LEAD_OD_MM)
    retail_washer_trial = screen_pose(
        wood,
        inventory,
        RETAIL_WASHER_LEAD_OD_MM,
        retail_rows,
        4.0 * 25.4,
        RETAIL_WASHER_LEAD_THICKNESS_MM,
    )
    retail_washer_trial["balanced_reserve_mm"] = round(retail_reserve, 6)
    retail_washer_trial["nominal_geometry_plausible"] = (
        retail_washer_trial["washer_seat_cad_opportunity"]
        and retail_washer_trial["full_nominal_bolt_bore_contained"]
        and retail_washer_trial["provisional_axis_overrun_met"]
    )
    return {
        "source_id": SOURCE_ID,
        "scope": "two center-principal/header duties, two bolts per side",
        "post_centers_x_mm": [-180.0, 180.0],
        "header_rear_y_mm": -175.7,
        "backer_rear_y_mm": -124.9,
        "fixed_panel_screw_axes": len(panel),
        "retained_old_frame_bolt_axes": len(frame),
        "protected_counts": inventory["counts"],
        "panel_edges_source": "unchanged kerf-right variant geometry",
        "washer_22mm_one_mm_reserve_window": row_window(22.0, 1.0),
        "provisional_hardware": {
            "barrel_length_mm": center.BARREL_LENGTH_MM,
            "barrel_od_mm": center.BARREL_OD_MM,
            "bolt_nominal_length_mm": center.BOLT_LENGTH_MM,
            "bolt_bore_diameter_mm": center.BORE_DIAMETER_MM,
            "washer_thickness_mm": center.WASHER_THICKNESS_MM,
            "head_diameter_mm": center.HEAD_DIAMETER_MM,
            "tool_diameter_mm": center.TOOL_DIAMETER_MM,
            "thread_axis_offset_assumed_mm": center.THREAD_AXIS_OFFSET_MM,
        },
        "bounded_full_bolt_tip_proof": _full_bolt_tip_bound(wood),
        "trials": trials,
        "retail_washer_od_lead_19_05mm": {
            "listing": "Hillman 811070, Lowe's item 67343; table lists 3/4-in OD and 1/16-in thickness",
            "same_page_hillman_answer": (
                "Hillman response reports 0.868-0.905-in OD, 0.370-0.390-in ID, "
                "and 0.064-0.104-in thickness; conflicts with product table"
            ),
            "retail_dimensions_conflicted": True,
            "trial": retail_washer_trial,
            "bearing_qualified": False,
            "delivered_dimensions_verified": False,
        },
        "bolt_length_sensitivity_22mm": {
            "provisional_required_tip_past_thread_axis_mm": (
                PROVISIONAL_TIP_PAST_THREAD_AXIS_MM
            ),
            "allowance_status": "geometry-only; not verified thread engagement",
            "necessary_length_window": _nominal_length_window_22mm(wood, rows_22mm),
            "trials": bolt_trials,
            "selected_length": None,
            "retail_qualified": False,
        },
        "structural_fit_verified": False,
        "delivered_hardware_fit_verified": False,
        "drilling_released": False,
    }


if __name__ == "__main__":
    print(json.dumps(build(), indent=2, sort_keys=True))
