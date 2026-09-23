"""Nominal combined-cut geometry for the eight governing barrel stations.

This is a source-bound geometry diagnostic.  It does not establish toleranced
fit, wood resistance, joint stiffness, contact capacity, or fabrication release.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path

import cadquery as cq

from scripts import owner_barrel_installed_stack_audit as stack_audit
from scripts import owner_barrel_integrated_kinematics as kinematics
from scripts import owner_barrel_rail_layout as rail
from scripts.export_owner_barrel_scene import build_integrated_viewer_assembly
from scripts.owner_barrel_visual_wood import build_visual_wood

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "docs/barrel-nut-combined-cut-sections.json"
SCHEMA = "owner_barrel_combined_cut_sections/v1"

PRINCIPAL_STATIONS = (
    "clip_split_base_center_left",
    "clip_split_base_center_right",
)
OUTER_RAIL_STATIONS = (
    "clip_horizontal_bottom_left_1",
    "clip_horizontal_bottom_right_2",
    "clip_horizontal_lower_left_1",
    "clip_horizontal_lower_right_2",
    "clip_horizontal_upper_left_1",
    "clip_horizontal_upper_right_2",
)
GOVERNING_STATIONS = PRINCIPAL_STATIONS + OUTER_RAIL_STATIONS
SCOPED_MEMBERS = frozenset(
    {
        "base_header",
        "base_principal_center_left",
        "base_principal_center_right",
        "base_rail_bottom_left",
        "base_rail_bottom_right",
        "base_rail_service_lower_left",
        "base_rail_service_lower_right",
        "base_rail_service_upper_left",
        "base_rail_service_upper_right",
        "base_side_left",
        "base_side_right",
    }
)
SOURCE_PATHS = (
    "scripts/export_owner_barrel_scene.py",
    "scripts/owner_barrel_center_single_layout.py",
    "scripts/owner_barrel_combined_cut_sections.py",
    "scripts/owner_barrel_installed_stack_audit.py",
    "scripts/owner_barrel_integrated_kinematics.py",
    "scripts/owner_barrel_rail_layout.py",
    "scripts/owner_barrel_visual_wood.py",
)
TOL_MM = 1.0e-4
TOL_MM3 = 1.0
SECTION_PITCHES_MM = (1.0, 0.5, 0.25)
SECTION_SAMPLE_SET_STABILITY_THRESHOLD_MM2 = 0.1
SECTION_AREA_COMPARISON_TOLERANCE_MM2 = 0.001
PRINCIPAL_FULL_SECTION_PITCH_MM = 0.25
PRINCIPAL_LOCAL_WINDOW_MM = 250.0
PRINCIPAL_WINDOW_MARGIN_MM = 30.0
GROSS_FULL_SECTION_TOLERANCE_MM2 = 0.01
SLOPED_GRAIN_ANGLE_DEG = 50.0
T = (
    math.cos(math.radians(SLOPED_GRAIN_ANGLE_DEG)),
    math.sin(math.radians(SLOPED_GRAIN_ANGLE_DEG)),
)


def _rounded(value, digits=6):
    return round(float(value), digits)


def _sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _grain(member):
    if member == "base_header" or member.startswith("base_rail_"):
        return cq.Vector(1, 0, 0)
    return cq.Vector(0, *T)


def _section_area(shape, station, grain):
    x_direction = cq.Vector(0, 1, 0) if abs(grain.x) > 0.9 else cq.Vector(1, 0, 0)
    plane = cq.Plane(
        origin=(grain * station).toTuple(),
        xDir=x_direction.toTuple(),
        normal=grain.toTuple(),
    )
    section = cq.Workplane(plane).newObject([shape]).section()
    return sum(item.Area() for item in section.vals())


def _projected_interval(shape, grain):
    """Return CAD bounding extrema along either supported member grain axis."""
    direction = grain.normalized()
    if abs(direction.x - 1.0) <= TOL_MM:
        bounds = shape.BoundingBox()
        return bounds.xmin, bounds.xmax
    if (
        abs(direction.x) <= TOL_MM
        and abs(direction.y - T[0]) <= TOL_MM
        and abs(direction.z - T[1]) <= TOL_MM
    ):
        aligned = shape.rotate(
            (0, 0, 0),
            (1, 0, 0),
            -SLOPED_GRAIN_ANGLE_DEG,
        )
        bounds = aligned.BoundingBox()
        return bounds.ymin, bounds.ymax
    raise ValueError("Unsupported combined-cut member grain direction")


def _section_samples(raw, cut, cutters, member):
    """Event-directed nominal sections; explicitly not a continuous minimum."""
    grain = _grain(member).normalized()
    member_low, member_high = _projected_interval(raw, grain)
    events = []
    affected = []
    for _, _, cutter in cutters:
        clipped = cutter.intersect(raw)
        if clipped.Volume() <= TOL_MM3:
            raise ValueError(f"{member}: retained cutter misses its host")
        low, high = _projected_interval(clipped, grain)
        affected.append((low, high))
        events.extend((low, (low + high) / 2, high))
    if not events:
        raise ValueError(f"{member}: no combined-cut section events")

    refinements = []
    previous = None
    positions = set()
    for pitch in SECTION_PITCHES_MM:
        positions.update(
            max(member_low + TOL_MM, min(member_high - TOL_MM, event + offset))
            for event in events
            for offset in (-pitch, -pitch / 2, 0.0, pitch / 2, pitch)
        )
        rows = [
            (position, _section_area(cut, position, grain))
            for position in sorted(positions)
        ]
        station, area = min(rows, key=lambda row: row[1])
        refinements.append(
            {
                "local_pitch_mm": pitch,
                "sample_count": len(rows),
                "minimum_sampled_net_area_mm2": _rounded(area),
                "critical_grain_station_mm": _rounded(station),
                "change_from_previous_mm2": (
                    None if previous is None else _rounded(area - previous)
                ),
            }
        )
        previous = area
    final = refinements[-1]
    gross_at_critical = _section_area(raw, final["critical_grain_station_mm"], grain)
    sample_set_delta = abs(final["change_from_previous_mm2"])
    return {
        "grain_direction_xyz": [_rounded(value) for value in grain.toTuple()],
        "member_grain_span_mm": [_rounded(member_low), _rounded(member_high)],
        "affected_cutter_projection_span_mm": [
            _rounded(min(low for low, _ in affected)),
            _rounded(max(high for _, high in affected)),
        ],
        "refinement": refinements,
        "minimum_sampled_net_area_mm2": final["minimum_sampled_net_area_mm2"],
        "gross_area_at_critical_station_mm2": _rounded(gross_at_critical),
        "area_comparison_tolerance_mm2": SECTION_AREA_COMPARISON_TOLERANCE_MM2,
        "critical_grain_station_mm": final["critical_grain_station_mm"],
        "sample_set_minimum_delta_last_two_mm2": sample_set_delta,
        "sample_set_stability_threshold_mm2": (
            SECTION_SAMPLE_SET_STABILITY_THRESHOLD_MM2
        ),
        "sample_set_minimum_stable": (
            sample_set_delta <= SECTION_SAMPLE_SET_STABILITY_THRESHOLD_MM2
        ),
        "coverage_boundary": (
            "Samples cutter projection endpoints and midpoints plus local offsets "
            "at 1.0, 0.5 and 0.25 mm. This event-directed nominal screen does "
            "not prove a continuous global minimum between samples, tolerance-case "
            "minimum, fracture path, stress concentration, or strength."
        ),
        "strength_or_capacity_claimed": False,
    }


def _principal_full_section_screen(raw, cut, cutters, member):
    """Sample full-gross principal sections through the local base-joint zone."""
    grain = _grain(member).normalized()
    member_low, _ = _projected_interval(raw, grain)
    nearby_centers = [
        cutter.Center().dot(grain)
        for _, _, cutter in cutters
        if member_low - TOL_MM
        <= cutter.Center().dot(grain)
        <= member_low + PRINCIPAL_LOCAL_WINDOW_MM
    ]
    if not nearby_centers:
        raise ValueError(f"{member}: no local principal cutter centers")
    high = max(nearby_centers) + PRINCIPAL_WINDOW_MARGIN_MM
    count = math.floor((high - member_low) / PRINCIPAL_FULL_SECTION_PITCH_MM) + 1
    samples = []
    for index in range(count):
        station = member_low + index * PRINCIPAL_FULL_SECTION_PITCH_MM
        samples.append(
            (
                station,
                _section_area(raw, station, grain),
                _section_area(cut, station, grain),
            )
        )
    gross = max(row[1] for row in samples)
    full = [
        row for row in samples if row[1] >= gross - GROSS_FULL_SECTION_TOLERANCE_MM2
    ]
    if not full:
        raise ValueError(f"{member}: no full-gross local principal samples")
    station, critical_gross, net = min(full, key=lambda row: row[2])
    barrel_paths = [
        cutter
        for _, name, cutter in cutters
        if name.startswith("barrel_center_clip_split_base_center_")
        and name.endswith("/barrel_cross_bore")
    ]
    if len(barrel_paths) != 1:
        raise ValueError(f"{member}: principal barrel cutter identity changed")
    barrel_station = barrel_paths[0].Center().dot(grain)
    return {
        "sample_pitch_mm": PRINCIPAL_FULL_SECTION_PITCH_MM,
        "sample_anchor_member_grain_start_mm": _rounded(member_low),
        "sample_window_mm": [_rounded(member_low), _rounded(high)],
        "sample_count": len(samples),
        "full_gross_sample_count": len(full),
        "gross_full_section_tolerance_mm2": GROSS_FULL_SECTION_TOLERANCE_MM2,
        "critical_grain_station_mm": _rounded(station),
        "gross_area_at_critical_station_mm2": _rounded(critical_gross),
        "minimum_sampled_full_gross_net_area_mm2": _rounded(net),
        "net_area_at_principal_barrel_axis_mm2": _rounded(
            _section_area(cut, barrel_station, grain)
        ),
        "principal_barrel_axis_grain_station_mm": _rounded(barrel_station),
        "coverage_boundary": (
            "Nominal 0.25 mm grid covers only the local base-joint window and "
            "reports sections whose gross area is within 0.01 mm2 of the maximum "
            "sampled gross area. It is not a continuous or tolerance-case minimum."
        ),
        "strength_or_capacity_claimed": False,
    }


def _scope(assembly):
    stations = {}
    members = set()
    pair_count = 0
    for station in GOVERNING_STATIONS:
        bolts = sorted(
            name for name, owner in assembly["bolt_station"].items() if owner == station
        )
        barrels = sorted(
            name
            for name, owner in assembly["barrel_station"].items()
            if owner == station
        )
        station_members = sorted(
            {member for bolt in bolts for member in assembly["bolts"][bolt].members}
        )
        stations[station] = {
            "bolt_names": bolts,
            "barrel_names": barrels,
            "members": station_members,
        }
        members.update(station_members)
        pair_count += len(bolts)
    if (
        tuple(rail.VIEWER_OUTER_STATIONS) != OUTER_RAIL_STATIONS
        or set(stations) != set(GOVERNING_STATIONS)
        or pair_count != 14
        or any(
            len(row["bolt_names"]) != (1 if name in PRINCIPAL_STATIONS else 2)
            or len(row["barrel_names"]) != len(row["bolt_names"])
            for name, row in stations.items()
        )
        or members != SCOPED_MEMBERS
    ):
        raise ValueError("Governing combined-cut station scope changed")
    return stations


def _validate_sources(assembly, visual, axial, motion):
    scope = _scope(assembly)
    report = visual["report"]
    outer_rows = [
        row for row in axial["rows"] if row["station"] in OUTER_RAIL_STATIONS
    ]
    if (
        assembly.get("post_placement") != "integrated"
        or len(assembly.get("bolts", {})) != 46
        or any(assembly.get("release_flags", {}).values())
        or report.get("candidate_barrel_pairs_with_cut_wood") != 46
        or report.get("replacement_timber_members") != 20
        or report.get("retained_frame_bolt_cuts_in_replacements") != 24
        or report.get("inherited_additional_cuts_in_replacements") != 2
        or report.get("total_host_cutter_records") != 268
        or report.get("all_host_cutters_intersect_raw_wood") is not True
        or report.get("all_host_cutters_removed_from_cut_solids") is not True
        or report.get("all_twenty_frame_timber_hosts_represented") is not True
        or report.get("barrel_drilling_paths_without_cut_wood")
        or report.get("barrel_path_host_anomalies")
        or set(visual.get("cutters", {})) != set(visual["wood"])
        or len(outer_rows) != 12
        or any(row["shaft_length_mm"] != 152.4 for row in outer_rows)
        or motion.get("native_solve") is not False
        or motion.get("station_count") != 24
    ):
        raise ValueError("Current integrated combined-cut source changed")
    return scope, outer_rows


def build_report(assembly=None):
    assembly = build_integrated_viewer_assembly() if assembly is None else assembly
    visual = build_visual_wood(
        assembly=assembly,
        candidate_service=True,
        candidate_center_cuts=True,
        candidate_all_cuts=True,
        complete_frame_hosts=True,
    )
    axial = stack_audit.build_report(assembly)
    motion = kinematics.build_report(assembly)
    scope, outer_rows = _validate_sources(assembly, visual, axial, motion)
    visual_report = visual["report"]

    members = {}
    cutter_inventory = []
    for member in sorted(SCOPED_MEMBERS):
        raw = assembly["wood"][member]
        cut = visual["wood"][member]
        cutters = visual["cutters"][member]
        per_member = visual["report"]["per_member"][member]
        if (
            not cut.isValid()
            or len(cut.Solids()) != 1
            or len(cutters) != per_member["counts"]["total"]
            or cut.Volume() > raw.Volume() + TOL_MM3
        ):
            raise ValueError(f"{member}: invalid or incomplete combined-cut solid")
        members[member] = {
            "uncut_volume_mm3": _rounded(raw.Volume()),
            "combined_cut_volume_mm3": _rounded(cut.Volume()),
            "removed_volume_mm3": _rounded(raw.Volume() - cut.Volume()),
            "combined_cut_is_valid": True,
            "combined_cut_solid_count": 1,
            "cutter_count": len(cutters),
            "cutter_counts_by_category": per_member["counts"],
            "nominal_grain_normal_sections": _section_samples(
                raw, cut, cutters, member
            ),
        }
        for category, name, cutter in cutters:
            intersection = cutter.intersect(raw).Volume()
            if intersection <= TOL_MM3:
                raise ValueError(f"{member}/{name}: cutter lost host coverage")
            cutter_inventory.append(
                {
                    "host_member": member,
                    "category": category,
                    "name": name,
                    "cutter_volume_mm3": _rounded(cutter.Volume()),
                    "host_intersection_mm3": _rounded(intersection),
                    "host_covered": True,
                }
            )

    center_source = assembly["diagnostics"]["producer_diagnostics"]["center6"][
        "revised_center"
    ]
    principals = {}
    for station in PRINCIPAL_STATIONS:
        principal_member = f"base_principal_center_{station.rsplit('_', 1)[1]}"
        rows = center_source["stations"][station]["bolts"]
        if len(rows) != 1:
            raise ValueError(f"{station}: current one-bolt principal layout changed")
        name, row = next(iter(rows.items()))
        motion_row = motion["stations"][station]
        pocket_stock = min(
            row["head_pocket_header_bottom_margin_mm"],
            row["head_pocket_header_top_margin_mm"],
        )
        if (
            abs(pocket_stock - 2.092152) > TOL_MM
            or motion_row["bolt_count"] != 1
            or motion_row["ranks"]["bolts_full_face_closed"] != 5
            or abs(
                motion_row[
                    "closed_full_free_rotation_axis_alignment_with_face_normal_abs"
                ]
                - 1.0
            )
            > 1.0e-6
        ):
            raise ValueError(f"{station}: governing pocket or twist diagnostic changed")
        principals[station] = {
            "bolt_name": f"{name}_bolt",
            "members": scope[station]["members"],
            "head_pocket_minimum_nominal_header_edge_stock_mm": _rounded(
                pocket_stock
            ),
            "barrel_nominal_radial_x_edge_ligament_mm": row[
                "barrel_radial_x_edge_ligament_mm"
            ],
            "isolated_closed_face_rank": 5,
            "isolated_relative_dof": 6,
            "free_mode_alignment_with_face_normal_abs": motion_row[
                "closed_full_free_rotation_axis_alignment_with_face_normal_abs"
            ],
            "face_normal_twist_mode_unresolved": True,
            "geometry_survival_or_strength_claimed": False,
            "local_full_section_screen": _principal_full_section_screen(
                assembly["wood"][principal_member],
                visual["wood"][principal_member],
                visual["cutters"][principal_member],
                principal_member,
            ),
        }

    six_inch = []
    for row in sorted(outer_rows, key=lambda item: item["bolt_name"]):
        if (
            abs(row["tip_past_assumed_axis_mm"] - 1.849) > TOL_MM
            or abs(
                row["maximum_body_overlap_with_fully_threaded_shaft_mm"] - 6.8528
            )
            > TOL_MM
            or abs(row["modeled_barrel_diametral_clearance_mm"]) > TOL_MM
        ):
            raise ValueError(f"{row['bolt_name']}: governing stack diagnostic changed")
        six_inch.append(
            {
                key: row[key]
                for key in (
                    "station",
                    "bolt_name",
                    "barrel_name",
                    "shaft_length_mm",
                    "tip_past_assumed_axis_mm",
                    "maximum_body_overlap_with_fully_threaded_shaft_mm",
                    "partial_thread_comparator_body_overlap_mm",
                    "modeled_barrel_diametral_clearance_mm",
                    "machine_bore_od_mm",
                    "barrel_body_od_mm",
                    "tip_to_bore_far_cap_clearance_mm",
                    "thread_engagement",
                )
            }
            | {
                "fit_qualified": False,
                "thread_engagement_qualified": False,
            }
        )

    unstable_sample_set_members = sorted(
        member
        for member, row in members.items()
        if not row["nominal_grain_normal_sections"]["sample_set_minimum_stable"]
    )

    return {
        "schema": SCHEMA,
        "candidate": "compact-floor-flush-bolted-development",
        "source": {
            "assembly": "scripts.export_owner_barrel_scene.build_integrated_viewer_assembly()",
            "combined_wood": (
                "scripts.owner_barrel_visual_wood.build_visual_wood("
                "assembly=assembly,candidate_service=True,candidate_center_cuts=True,"
                "candidate_all_cuts=True,complete_frame_hosts=True)"
            ),
            "source_sha256": {
                name: _sha256(ROOT / name) for name in SOURCE_PATHS
            },
            "historical_two_row_preliminary_used": False,
        },
        "scope": {
            "station_count": len(scope),
            "barrel_pair_count": sum(
                len(row["bolt_names"]) for row in scope.values()
            ),
            "member_count": len(SCOPED_MEMBERS),
            "stations": scope,
            "members": sorted(SCOPED_MEMBERS),
        },
        "nominal_full_frame_machining_inventory": {
            "member_count": visual_report["replacement_timber_members"],
            "all_members_one_valid_connected_solid": True,
            "host_cutter_count": visual_report["total_host_cutter_records"],
            "all_host_cutters_intersect_raw_wood": visual_report[
                "all_host_cutters_intersect_raw_wood"
            ],
            "all_host_cutters_removed_from_cut_solids": visual_report[
                "all_host_cutters_removed_from_cut_solids"
            ],
            "service_cut_count": visual_report[
                "inherited_service_cuts_in_replacements"
            ],
            "additional_cut_count": visual_report[
                "inherited_additional_cuts_in_replacements"
            ],
            "fixed_panel_kicker_cut_count": visual_report[
                "fixed_panel_receiver_cuts_in_replacements"
            ],
            "retained_frame_cut_count": visual_report[
                "retained_frame_bolt_cuts_in_replacements"
            ],
            "outer_header_trial_cut_count": visual_report[
                "outer_header_trial_cuts"
            ],
            "center_trial_cut_count": visual_report["center_trial_cuts"],
            "remaining_barrel_trial_cut_count": visual_report[
                "remaining_trial_cuts"
            ],
            "excluded_legacy_sds_axis_count": visual_report[
                "excluded_legacy_sds_axes"
            ],
            "tolerance_or_resistance_credit": False,
        },
        "combined_cut_solids": members,
        "section_coverage": {
            "method": "event-directed nominal grain-normal sections",
            "refinement_pitches_mm": list(SECTION_PITCHES_MM),
            "sample_set_stability_threshold_mm2": (
                SECTION_SAMPLE_SET_STABILITY_THRESHOLD_MM2
            ),
            "unstable_sample_set_members": unstable_sample_set_members,
            "all_member_sample_set_minima_stable": not unstable_sample_set_members,
            "continuous_global_coverage_complete": False,
            "tolerance_case_coverage_complete": False,
            "geometry_survival_established": False,
        },
        "cutter_inventory": {
            "host_cutter_count": len(cutter_inventory),
            "all_scoped_member_cutters_retained": True,
            "all_cutters_have_host_coverage": True,
            "rows": sorted(
                cutter_inventory,
                key=lambda row: (row["host_member"], row["category"], row["name"]),
            ),
        },
        "critical_principal_header": principals,
        "six_inch_outer_rail_stacks": {
            "row_count": len(six_inch),
            "rows": six_inch,
            "nominal_tip_past_assumed_axis_mm": 1.849,
            "nominal_maximum_body_overlap_if_fully_threaded_mm": 6.8528,
            "nominal_barrel_bore_diametral_fit_allowance_mm": 0.0,
        },
        "controlled_tolerance_cases": [],
        "net_section_resistance_evaluated": False,
        "net_section_resistance_not_evaluated_reason": (
            "No tolerance-minimum section, signed section demand, or applicable "
            "local net-section interaction method and wood adjustments are available."
        ),
        "missing_controlled_inputs": [
            "delivered lumber section, moisture, warp, grain and defect bounds",
            "realizable drill and pocket diameter, depth, position and angular tolerances",
            "delivered barrel OD, length, axis, opening and usable female-thread interval",
            "delivered bolt body, tip, runout and complete male-thread interval",
            "washer and head dimensions plus installed seating and recess bounds",
            "assembly gap, alignment, barrel rotation, retention and bore damage bounds",
        ],
        "disposition": "EVIDENCE_BLOCKED",
        "disposition_basis": (
            "Nominal combined solids do not bound realizable adverse sections or fit. "
            "All twelve six-inch stacks have only 1.849 mm nominal reach past the "
            "assumed barrel axis, 6.8528 mm maximum body overlap if fully threaded, "
            "and zero modeled barrel-bore fit allowance. Each one-bolt principal/header "
            "joint retains an isolated closed-face face-normal twist mode, and each "
            "header pocket leaves 2.092152 mm nominal edge stock. No GO or NO_GO may "
            "be issued until controlled realizable tolerance cases and applicable "
            "resistance/stiffness evidence exist."
        ),
        "flags": {
            "go": False,
            "no_go": False,
            "native_solve_run": False,
            "strength_or_capacity_qualified": False,
            "contact_strength_qualified": False,
            "fit_qualified": False,
            "qualification_pass": False,
            "drilling_released": False,
            "fabrication_released": False,
            "structural_released": False,
        },
    }


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=OUTPUT)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)
    report = build_report()
    encoded = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.check:
        if not args.output.is_file() or args.output.read_text() != encoded:
            raise SystemExit(f"Stale combined-cut artifact: {args.output}")
    else:
        args.output.write_text(encoded)
    print(
        f"{report['disposition']}: {report['scope']['station_count']} stations, "
        f"{report['scope']['barrel_pair_count']} pairs, "
        f"{report['scope']['member_count']} members"
    )


if __name__ == "__main__":
    main()
