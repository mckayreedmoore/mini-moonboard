"""Finite NDS component references, with issued actions and current seat geometry.

Reuse the frozen bounded-study admission and section evidence. No mechanics
solve, response assembly, frame modification, CAD rebuild or mesh export.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import math
import platform
import sys
from pathlib import Path

import cadquery as cq
import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = next(p for p in HERE.parents if (p / "current-candidate.json").is_file())
sys.path.insert(0, str(ROOT))

spec = importlib.util.spec_from_file_location(
    "issued_bounded_methods", HERE.parent / "analyze.py"
)
parent = importlib.util.module_from_spec(spec)
spec.loader.exec_module(parent)

from fea.reinforced_timber_resistance import adjusted_reference
from mini_moonboard import bolted_timber_checks as nds
from scripts import thin_bolted_timber_common_shaft_checks as own
from scripts.thin_bolted_steel_resistance import annulus_pressure

N_PER_LBF = own.unit.N_PER_LBF
INCH_MM = 25.4


def reduced_depth_shear(fv_mpa, width_mm, depth_mm, engaged_depth_mm, end_mm):
    """NDS 2024 3.4.4.1, Eqs. 3.4-6/7; rectangular beam component only."""
    values = (fv_mpa, width_mm, depth_mm, engaged_depth_mm, end_mm)
    parent.require(all(math.isfinite(x) for x in values), "nonfinite shear input")
    parent.require(
        all(x > 0 for x in values[:4]) and end_mm >= 0, "invalid shear dimensions"
    )
    parent.require(engaged_depth_mm <= depth_mm, "engagement exceeds member depth")
    near = end_mm < 5 * depth_mm
    gross_engaged = 2 / 3 * fv_mpa * width_mm * engaged_depth_mm
    return {
        "reference_n": gross_engaged * (engaged_depth_mm / depth_mm) ** 2
        if near
        else gross_engaged,
        "equation": "3.4-6" if near else "3.4-7",
        "connection_within_5d_of_end": near,
        "Fv_prime_mpa": fv_mpa,
        "b_mm": width_mm,
        "d_mm": depth_mm,
        "de_mm": engaged_depth_mm,
        "nearest_grain_end_mm": end_mm,
    }


def annular_probe(shape, point, inward, outer_mm, inner_mm):
    """The existing washer-seating test's thin-volume method, parameterized."""
    depth_mm = 0.1
    point, inward = cq.Vector(*point), cq.Vector(*inward)
    probe = cq.Solid.makeCylinder(outer_mm / 2, depth_mm, point, inward).cut(
        cq.Solid.makeCylinder(inner_mm / 2, depth_mm, point, inward)
    )
    expected = math.pi / 4 * (outer_mm**2 - inner_mm**2) * depth_mm
    parent.require(
        abs(probe.Volume() - expected) < 1e-6, "probe-volume arithmetic differs"
    )
    actual = probe.intersect(shape).Volume()
    return {
        "probe_depth_mm": depth_mm,
        "OD_mm": outer_mm,
        "support_inner_diameter_mm": inner_mm,
        "expected_probe_volume_mm3": expected,
        "intersected_current_wood_volume_mm3": actual,
        "support_fraction": actual / expected,
        "full_modeled_support": abs(actual - expected) <= 1e-4,
    }


def known_answers():
    near = reduced_depth_shear(2, 3, 10, 5, 49.999)
    far = reduced_depth_shear(2, 3, 10, 5, 50)
    parent.require(
        near["reference_n"] == 5 and far["reference_n"] == 20, "5d branch fixture"
    )
    rejected = 0
    for values in ((2, 3, 10, 11, 0), (2, 3, 10, 0, 1), (2, 3, 10, 5, -1)):
        try:
            reduced_depth_shear(*values)
        except ValueError:
            rejected += 1
    parent.require(rejected == 3, "invalid reduced-depth inputs must stop")
    box = cq.Workplane("XY").box(30, 30, 1, centered=(True, True, False)).val()
    full = annular_probe(box, [0, 0, 0], [0, 0, 1], 20, 10)
    gap = annular_probe(box.translate((0, 0, 0.2)), [0, 0, 0], [0, 0, 1], 20, 10)
    edge = annular_probe(box.translate((15, 0, 0)), [0, 0, 0], [0, 0, 1], 20, 10)
    parent.require(
        full["full_modeled_support"] and gap["support_fraction"] == 0,
        "full/gap fixture",
    )
    parent.require(
        0 < edge["support_fraction"] < 1 and not edge["full_modeled_support"],
        "clipped-ring fixture",
    )
    # Independent circular-area expression checks the reused dimensional helper.
    bearing = nds.dfl_axial_wood_bearing_reference_lbf(1, 0.5, 0.4)
    parent.require(
        abs(bearing - 625 * math.pi / 4 * 0.75) < 1e-10, "washer reference fixture"
    )
    return {
        "near_and_exact_5d_references_n": [near["reference_n"], far["reference_n"]],
        "invalid_input_rejections": rejected,
        "full_gap_clipped_probe_fractions": [
            r["support_fraction"] for r in (full, gap, edge)
        ],
        "independent_washer_area_reference_lbf": bearing,
    }


def washer_references(cases, geometry, old_geometry, trim, pins):
    solids = {
        r["id"]: r
        for k in ("changed_finished_solids", "unchanged_finished_solids")
        for r in geometry[k]
    }
    old_solids = {r["id"]: r for r in old_geometry["finished_solids"]}
    trimmed_seats = {
        (r["axis_id"], r["receiver"]): r for r in trim["bolt_bore_washer_geometry"]
    }
    first_field, first_report = cases[0][1], cases[0][2]["washers"]
    ends = {r["id"]: r for r in first_field["shaft_end_capture_actions"]}
    shapes, seats, rows = {}, {}, []
    for row in first_report["all200_own_end_diagnostics"]:
        if row["receiver_kind"] != "wood":
            continue
        parent.require(
            row["grain_axis_abs_cos_to_pressure_normal"] < 1e-8,
            "Fc-perp seating orientation",
        )
        profiles = [
            row["nominal_own_hardware_geometry"],
            *row["USS_catalog_corners_min_thickness"],
        ]
        outer = max(p["OD_mm"] for p in profiles)
        inner = min(
            max(p["ID_mm"], p["source_support_opening_diameter_mm"]) for p in profiles
        )
        host, capture = row["host"], row["capture_id"]
        support = {
            "capture_id": capture,
            "axis_id": row["axis_id"],
            "host": host,
            "bounding_OD_mm": outer,
            "bounding_inner_diameter_mm": inner,
        }
        if (
            row["outer_landing_for_max_nominal_or_catalog_OD"][
                "finished_local_service_cuts_proven_clear"
            ]
            is False
        ):
            solid = solids[host]
            parent.merge(pins, {solid["path"]: solid["sha256"]})
            if host not in shapes:
                shapes[host] = cq.importers.importBrep(str(ROOT / solid["path"])).val()
            end = ends[capture]
            point = end["host_support_point_xyz_mm"]
            inward = -np.asarray(end["end"]["direction_on_shaft_xyz"])
            delta = np.asarray(point) - end["point_xyz_mm"]
            parent.require(
                abs(np.linalg.norm(inward) - 1) < 1e-9 and np.dot(delta, inward) > 0,
                "washer exterior/inward orientation",
            )
            parent.require(
                np.linalg.norm(np.cross(delta, inward)) < 1e-6,
                "washer face datums not concentric",
            )
            support.update(
                annular_probe(shapes[host], point, inward.tolist(), outer, inner)
            )
            support["proof"] = (
                "current cached finished BREP thin annulus; includes actual current service cuts"
            )
            support["solid_source"] = {"path": solid["path"], "sha256": solid["sha256"]}
        elif host.startswith("eoere_cleat"):
            evidence = trimmed_seats[(row["axis_id"], host)]
            parent.require(
                evidence["modeled_washer_footprint_fraction"] == 1
                and evidence["full_bore_body_fraction"] == 1,
                "trimmed seat receipt",
            )
            parent.require(
                outer <= row["nominal_own_hardware_geometry"]["OD_mm"],
                "catalog OD exceeds proven trimmed footprint",
            )
            support.update(
                {
                    "full_modeled_support": True,
                    "proof": "issued current trimmed-cleat footprint receipt; catalog outer diameters no larger",
                }
            )
        else:
            parent.require(
                solids[host]["sha256"] == old_solids[host]["sha256"],
                "inherited seat solid changed",
            )
            parent.require(
                all(p["source_nominal_supported_ring_landing_full"] for p in profiles),
                "inherited landing not full",
            )
            parent.require(
                row["outer_landing_for_max_nominal_or_catalog_OD"][
                    "source_nominal_outer_landing_full"
                ],
                "catalog outer landing not proven",
            )
            support.update(
                {
                    "full_modeled_support": True,
                    "proof": "issued full outer-landing proof on byte-identical finished timber",
                }
            )
        seats[capture] = support
    for case, field, reports in cases:
        end_lookup = {r["id"]: r for r in field["shaft_end_capture_actions"]}
        for row in reports["washers"]["all200_own_end_diagnostics"]:
            if row["receiver_kind"] != "wood":
                continue
            capture = row["capture_id"]
            parent.require(
                math.dist(
                    row["own_support_point_xyz_mm"],
                    ends[capture]["host_support_point_xyz_mm"],
                )
                < 1e-7,
                "cross-case seat moved",
            )
            parent.require(
                row["N_n"] == end_lookup[capture]["compression_n"],
                "cross-case own axial demand",
            )
            for i, p in enumerate(
                [
                    row["nominal_own_hardware_geometry"],
                    *row["USS_catalog_corners_min_thickness"],
                ]
            ):
                outer, inner = (
                    p["OD_mm"],
                    max(p["ID_mm"], p["source_support_opening_diameter_mm"]),
                )
                parent.require(
                    outer <= seats[capture]["bounding_OD_mm"]
                    and inner >= seats[capture]["bounding_inner_diameter_mm"],
                    "profile outside proven ring",
                )
                reference = (
                    nds.dfl_axial_wood_bearing_reference_lbf(
                        outer / INCH_MM,
                        p["source_support_opening_diameter_mm"] / INCH_MM,
                        p["ID_mm"] / INCH_MM,
                    )
                    * N_PER_LBF
                )
                load_kern = (
                    p["ID_mm"] ** 2 / 4 + p["uniform_load_ring_outer_radius_mm"] ** 2
                ) / (4 * p["uniform_load_ring_outer_radius_mm"])
                support_kern = (inner**2 / 4 + outer**2 / 4) / (2 * outer)
                eccentricity = min(load_kern, support_kern)
                pressure = annulus_pressure(
                    axial_n=row["N_n"],
                    moment_xy_nmm=[row["N_n"] * eccentricity, 0],
                    inner_radius_mm=inner / 2,
                    outer_radius_mm=outer / 2,
                )
                rows.append(
                    {
                        "case_id": case,
                        "capture_id": capture,
                        "host": row["host"],
                        "profile": "nominal" if i == 0 else "catalog-corner-" + str(i),
                        "OD_mm": outer,
                        "support_inner_diameter_mm": inner,
                        "axial_N_n": row["N_n"],
                        "Fc_perp625psi_full_ring_reference_n": reference,
                        "mean_reference_ratio": row["N_n"] / reference,
                        "peak_reference_ratio_at_two_face_affine_contact_limit": pressure[
                            "pressure_max_mpa"
                        ]
                        / adjusted_reference(139.7)["Fc_perp_mpa"],
                        "two_face_affine_eccentricity_mm": eccentricity,
                        "full_modeled_support": seats[capture]["full_modeled_support"],
                        "physical_couple_and_washer_combined_resistance_qualified": False,
                    }
                )
    eligible = [r for r in rows if r["full_modeled_support"]]
    nominal = [r for r in eligible if r["profile"] == "nominal"]
    return {
        "current_wood_seats": len(seats),
        "previously_service_cut_conditional_seats_checked": len(
            [s for s in seats.values() if "solid_source" in s]
        ),
        "current_annular_probes_full": sum(
            s.get("full_modeled_support", False)
            for s in seats.values()
            if "solid_source" in s
        ),
        "reused_trimmed_cleat_footprints": sum(
            s["host"].startswith("eoere_cleat") for s in seats.values()
        ),
        "reused_unchanged_finished_seats": sum(
            "byte-identical" in s["proof"] for s in seats.values()
        ),
        "minimum_support_fraction_in_queried_seats": min(
            s["support_fraction"] for s in seats.values() if "solid_source" in s
        ),
        "nominal_recipe_references_n": sorted(
            {r["Fc_perp625psi_full_ring_reference_n"] for r in nominal}
        ),
        "catalog_and_nominal_reference_range_n": [
            min(r["Fc_perp625psi_full_ring_reference_n"] for r in eligible),
            max(r["Fc_perp625psi_full_ring_reference_n"] for r in eligible),
        ],
        "worst_nominal_mean": max(nominal, key=lambda r: r["mean_reference_ratio"]),
        "worst_catalog_or_nominal_mean": max(
            eligible, key=lambda r: r["mean_reference_ratio"]
        ),
        "worst_at_two_face_affine_contact_limit": max(
            eligible,
            key=lambda r: r["peak_reference_ratio_at_two_face_affine_contact_limit"],
        ),
        "scope": "Current CAD containment with fixed old axial forces; Fc-perp ring references require sound dry DF-L No.2 and a sufficiently stiff seated washer. No physical couple, preload or combined washer resistance is established.",
    }, {"seat_geometry": list(seats.values()), "own_case_component_rows": rows}


def cleat_references(cases, trim, original_details):
    fv = adjusted_reference(139.7)["Fv_mpa"]
    polygon = trim["retained_YZ_polygon_mm"]
    sections, shears, tearout = [], [], []
    for section in original_details["sections"]:
        if not section["member"].startswith("eoere_cleat"):
            continue
        area = section["current"]["area_mm2"]
        row = {
            "member": section["member"],
            "station_mm": section["station_mm"],
            "area_mm2": area,
            "base_Ft575psi_area_reference_n": area * 575 * N_PER_LBF / INCH_MM**2,
            "Ft747p5psi_CF1p3_scenario_reference_n": area
            * adjusted_reference(139.7)["Ft_mpa"],
            "maximum_fixed_old_average_tension_n": max(
                max(0, r["parallel_axial_n"])
                for r in section["fixed_old_action_average_bounds"]
            ),
        }
        row["maximum_average_tension_over_adjusted_reference"] = (
            row["maximum_fixed_old_average_tension_n"]
            / row["Ft747p5psi_CF1p3_scenario_reference_n"]
        )
        sections.append(row)
    for case, field, reports in cases:
        actions, gravity = own.member_point_inputs(field)
        wood = reports["timber"]["wood_surfaces"]
        for member in field["source_inputs"]["timber_rows"]:
            name = member["name"]
            if not name.startswith("eoere_cleat"):
                continue
            own_wood = [r for r in wood if r["receiver"] == name]
            stations = sorted({r["own_aggregate_point_xyz_mm"][2] for r in own_wood})
            parent.require(len(stations) == 2, "two cleat grain stations required")
            low, high = (member[k][2] for k in ("start", "end"))
            for z in stations:
                group = [
                    r
                    for r in own_wood
                    if abs(r["own_aggregate_point_xyz_mm"][2] - z) < 1e-8
                ]
                ys = [r["own_aggregate_point_xyz_mm"][1] for r in group]
                sign = math.copysign(1, sum(r["own_force_xyz_n"][1] for r in group))
                # de extends from the loaded edge to the bolt furthest from it.
                current_rear = (
                    -105.85
                    - parent.trimmed_ray(polygon, [0, -105.85, z], [0, -1, 0])[
                        "distance_mm"
                    ]
                )
                old_depth, current_depth = 139.7, -36 - current_rear
                old_de = max(ys) + 175.7 if sign < 0 else -36 - min(ys)
                current_de = max(ys) - current_rear if sign < 0 else -36 - min(ys)
                old_ref = reduced_depth_shear(
                    fv, member["width_mm"], old_depth, old_de, min(z - low, high - z)
                )
                current_ref = reduced_depth_shear(
                    fv,
                    member["width_mm"],
                    current_depth,
                    current_de,
                    min(z - low, high - z),
                )
                stock_depth_ref = reduced_depth_shear(
                    fv,
                    member["width_mm"],
                    old_depth,
                    current_de,
                    min(z - low, high - z),
                )
                cuts = []
                radius = (
                    max(
                        r["bore_diameter_mm"]
                        for r in field["source_inputs"]["shafts"]
                        if r["axis_id"] in {a["axis_id"] for a in group}
                    )
                    / 2
                )
                # Use the source opening to stay outside bore-support bands.
                for side in (-1, 1):
                    station = z + side * (radius + 1e-4)
                    point = [member["start"][0], member["start"][1], station]
                    wrench = own.previous.member_cut_wrench(
                        member["axis"], low, high, point, *gravity[name], actions[name]
                    )
                    cuts.append({"side": side, "station_mm": station, **wrench})
                demand = max(abs(r["force_on_lower_portion_xyz_n"][1]) for r in cuts)
                shears.append(
                    {
                        "case_id": case,
                        "member": name,
                        "group_grain_station_mm": z,
                        "group_crossgrain_Y_resultant_n": sum(
                            r["own_force_xyz_n"][1] for r in group
                        ),
                        "maximum_adjacent_grain_normal_section_Y_shear_n": demand,
                        "untrimmed_rectangular_NDS_reference": old_ref,
                        "current_local_depth_parameter_sensitivity": current_ref,
                        "stock_depth_with_trimmed_engagement_parameter_sensitivity": stock_depth_ref,
                        "untrimmed_component_ratio": demand / old_ref["reference_n"],
                        "current_local_parameter_sensitivity_ratio": demand
                        / current_ref["reference_n"],
                        "stock_depth_trimmed_engagement_parameter_sensitivity_ratio": demand
                        / stock_depth_ref["reference_n"],
                        "adjacent_complete_own_cut_wrenches": cuts,
                        "current_trimmed_cleat_complete_splitting_resistance_n": None,
                    }
                )
            for row in own_wood:
                point = row["own_aggregate_point_xyz_mm"]
                force = row["own_signed_components"]["parallel_grain_signed_n"]
                direction = [0, 0, 1 if force >= 0 else -1]
                ray = parent.trimmed_ray(polygon, point, direction)
                old_end = high - point[2] if force >= 0 else point[2] - low
                args = (member["width_mm"] / INCH_MM, 1)
                old_value = (
                    nds.dfl_parallel_row_tear_out_reference_lbf(
                        *args, old_end / INCH_MM
                    )
                    * N_PER_LBF
                )
                current_value = (
                    nds.dfl_parallel_row_tear_out_reference_lbf(
                        *args, ray["distance_mm"] / INCH_MM
                    )
                    * N_PER_LBF
                )
                tearout.append(
                    {
                        "case_id": case,
                        "member": name,
                        "axis_id": row["axis_id"],
                        "own_parallel_grain_signed_force_n": force,
                        "old_square_loaded_end_distance_mm": old_end,
                        "current_loaded_grain_ray": ray,
                        "old_single_bolt_parallel_row_reference_n": old_value,
                        "current_end_distance_parameter_sensitivity_n": current_value,
                        "current_parameter_sensitivity_ratio": abs(force)
                        / current_value,
                        "current_oblique_end_full_tearout_qualification": False,
                    }
                )
    loaded_sections = [
        r
        for r in sections
        if any(abs(r["station_mm"] - z) < 0.01 for z in (200, 342.0875))
    ]
    force_replay_error = max(
        abs(
            r["maximum_adjacent_grain_normal_section_Y_shear_n"]
            - abs(r["group_crossgrain_Y_resultant_n"])
        )
        for r in shears
    )
    parent.require(force_replay_error < 1e-7, "cleat complete cut/group force mismatch")
    return {
        "near_end_rectangular_reference_range_n": [
            min(
                r["untrimmed_rectangular_NDS_reference"]["reference_n"] for r in shears
            ),
            max(
                r["untrimmed_rectangular_NDS_reference"]["reference_n"] for r in shears
            ),
        ],
        "current_local_parameter_sensitivity_reference_range_n": [
            min(
                r["current_local_depth_parameter_sensitivity"]["reference_n"]
                for r in shears
            ),
            max(
                r["current_local_depth_parameter_sensitivity"]["reference_n"]
                for r in shears
            ),
        ],
        "stock_depth_trimmed_engagement_parameter_sensitivity_range_n": [
            min(
                r["stock_depth_with_trimmed_engagement_parameter_sensitivity"][
                    "reference_n"
                ]
                for r in shears
            ),
            max(
                r["stock_depth_with_trimmed_engagement_parameter_sensitivity"][
                    "reference_n"
                ]
                for r in shears
            ),
        ],
        "complete_section_versus_independent_group_force_max_error_n": force_replay_error,
        "worst_matching_section_shear": max(
            shears,
            key=lambda r: r[
                "stock_depth_trimmed_engagement_parameter_sensitivity_ratio"
            ],
        ),
        "worst_parallel_row_parameter_sensitivity": max(
            tearout, key=lambda r: r["current_parameter_sensitivity_ratio"]
        ),
        "loaded_bolt_plane_adjusted_net_tension_reference_range_n": [
            min(r["Ft747p5psi_CF1p3_scenario_reference_n"] for r in loaded_sections),
            max(r["Ft747p5psi_CF1p3_scenario_reference_n"] for r in loaded_sections),
        ],
        "worst_average_parallel_net_tension": max(
            sections, key=lambda r: r["maximum_average_tension_over_adjusted_reference"]
        ),
        "actual_all_mode_current_cleat_resistance_n": None,
        "scope": "NDS reduced-depth connection shear checks a rectangular bending-member component and uses shear on grain-normal sections. Current trimmed-depth and sloping-end tearout values are parameter sensitivities. The separate Y-normal tensile-opening cut, torsion, bending, clamp pressure and interacting modes remain undisposed.",
    }, {
        "reduced_depth_shear": shears,
        "parallel_single_bolt_row_tearout": tearout,
        "net_parallel_tension": sections,
    }


def run():
    inputs = json.loads((HERE / "inputs.json").read_bytes())
    original_inputs = parent.read(inputs["original_inputs"])
    original_result = parent.read(inputs["original_result"])
    original_details = parent.read(inputs["original_details"])
    pins = dict(original_details["complete_source_sha256"])
    parent.merge(
        pins,
        {
            r["path"]: r["sha256"]
            for r in (
                inputs["original_inputs"],
                inputs["original_result"],
                inputs["original_details"],
                *inputs["pinned_method_sources"],
            )
        },
    )
    parent.merge(
        pins,
        {
            str(p.relative_to(ROOT)): parent.sha(p)
            for p in (HERE / "analyze.py", HERE / "inputs.json")
        },
    )
    parent.verify(pins)
    geometry, old_geometry, trim = (
        parent.read(original_inputs[k])
        for k in ("current_geometry", "old_geometry", "trim_geometry")
    )
    parent.require(
        geometry["revision"] == "eoere-grid-aligned-wire-cutouts-v1"
        and geometry["mechanics_ready"] is False,
        "current geometry with no current response field",
    )
    parent.require(
        geometry["axes"] == old_geometry["axes"]
        and geometry["screw_axes"] == old_geometry["screw_axes"],
        "unchanged axis records",
    )
    intake = parent.module(
        "resistance_issued_intake", original_inputs["helpers"]["admission"]
    )
    cases = []
    for row in original_inputs["cases"]:
        field, admitted = intake.load_admitted(ROOT / row["manifest"]["path"])
        parent.merge(pins, admitted)
        parent.require(
            field["case_id"] == row["case_id"]
            and field["source_inputs"]["geometry"]["report"]
            == original_inputs["old_geometry"],
            "issued old-case identity",
        )
        reports = {k: parent.read(row["reports"][k]) for k in ("timber", "washers")}
        parent.require(
            all(r["case_id"] == row["case_id"] for r in reports.values()),
            "cross-case report",
        )
        cases.append((row["case_id"], field, reports))
    checks = known_answers()
    washer, washer_rows = washer_references(cases, geometry, old_geometry, trim, pins)
    cleat, cleat_rows = cleat_references(cases, trim, original_details)
    bolt_rows = original_details["timber"]["components"]
    bolt = {
        "reused_issued_component_rows": len(bolt_rows),
        "unadjusted_single_shear_component_reference_range_n": [
            min(r["unadjusted_component_Z_n"] for r in bolt_rows),
            max(r["unadjusted_component_Z_n"] for r in bolt_rows),
        ],
        "worst_unadjusted_component_comparison": max(
            bolt_rows, key=lambda r: r["V_over_unadjusted_component_Z"]
        ),
        "adjusted_oblique_group_or_shared_stack_reference_n": None,
        "scope": "Six-mode single-shear references remain finite; none supplies the missing group, geometry, mixed shared-stack or complete-member resistance.",
    }
    parent.verify(pins)
    result = {
        "schema": "eoere_nds_component_resistance_followup/v1",
        "status": "FINITE_COMPONENT_REFERENCES_AND_CURRENT_SEAT_GEOMETRY; COMPLETE_JOINT_RESISTANCE_OPEN",
        "current_geometry": geometry["revision"],
        "response_geometry": original_result["response_geometry"],
        "case_ids": [c[0] for c in cases],
        "load_contract": original_result["load_contract"],
        "method_sources": inputs["method_sources"],
        "material_reference": adjusted_reference(139.7),
        "known_answers": checks,
        "washer_wood_bearing": washer,
        "cleat_member_components": cleat,
        "bolt_yield_components": bolt,
        "runtime": {
            "python": platform.python_version(),
            "numpy": np.__version__,
            "cadquery": cq.__version__,
        },
        "source_binding": {
            "pin_count": len(pins),
            "canonical_sha256": parent.canonical(pins),
            "verified_before_after": True,
        },
        "limits": inputs["limits"],
        "release": {
            "new_response_solve": False,
            "geometry_changed": False,
            "candidate_selected": False,
            "fabrication": False,
            "complete_joint_strength_qualified": False,
        },
    }
    details = {
        "complete_source_sha256": pins,
        "washers": washer_rows,
        "cleats": cleat_rows,
    }
    return result, details


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument(
        "--compare",
        type=Path,
        help="Compare recomputed serialized hashes without duplicating detailed output",
    )
    args = parser.parse_args()
    result, details = run()
    payloads = {
        name: json.dumps(value, indent=2, sort_keys=True, allow_nan=False).encode()
        + b"\n"
        for name, value in (("result.json", result), ("details.json", details))
    }
    if args.compare:
        for name, payload in payloads.items():
            parent.require(
                (args.compare / name).read_bytes() == payload,
                "reproduction differs: " + name,
            )
        print(
            json.dumps(
                {"reproduced": True, "files": {k: len(v) for k, v in payloads.items()}}
            )
        )
    else:
        args.output_dir.mkdir(parents=True, exist_ok=False)
        for name, payload in payloads.items():
            (args.output_dir / name).write_bytes(payload)
        print(
            json.dumps(
                {
                    "output": str(args.output_dir),
                    "source_binding": result["source_binding"],
                    "wood_seats": result["washer_wood_bearing"]["current_wood_seats"],
                }
            )
        )
