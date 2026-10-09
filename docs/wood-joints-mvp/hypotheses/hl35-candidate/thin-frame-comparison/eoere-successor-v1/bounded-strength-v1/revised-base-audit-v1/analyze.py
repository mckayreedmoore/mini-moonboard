"""Read-only audit of frozen midpoint-ready base v3 and existing NDS evidence.

Queries saved BREP solids only. Existing issued actions remain attached to their
original field geometry; no response assembly, geometry edit or native solve.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import platform
import sys
from pathlib import Path

import cadquery as cq
import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = next(p for p in HERE.parents if (p / "current-candidate.json").is_file())
sys.path.insert(0, str(ROOT))
spec = importlib.util.spec_from_file_location(
    "revised_base_component_methods", HERE.parent / "resistance-followup-v1/analyze.py"
)
component = importlib.util.module_from_spec(spec)
spec.loader.exec_module(component)
parent = component.parent

from scripts.eoere_2026_adjustments import canonical_interval_shift


def relative(path):
    resolved = (ROOT / path).resolve()
    try:
        return str(resolved.relative_to(ROOT))
    except ValueError:
        return str(resolved)  # Preserve the parent's external archive-manifest pins.


def add_pins(pins, extra):
    parent.merge(pins, {relative(p): h for p, h in extra.items()})


def delta_audit(current, previous):
    before = {r["id"]: r for r in previous["axes"]}
    after = {r["id"]: r for r in current["axes"]}
    parent.require(
        set(before) == set(after) and len(after) == 100, "100 shaft identities"
    )
    rows = []
    for axis, new in after.items():
        old = before[axis]
        for key in (
            "receivers",
            "hardware_scenario",
            "source",
        ):
            parent.require(new[key] == old[key], axis + " changed " + key)
        for key in (
            "grip_mm",
            "diameter_mm",
            "bore_diameter_mm",
            "before_plate_mm",
            "after_plate_mm",
            "nominal_under_head_length_mm",
        ):
            parent.require(abs(new[key] - old[key]) < 1e-6, axis + " changed " + key)
        parent.require(
            np.linalg.norm(np.asarray(new["direction_xyz"]) - old["direction_xyz"])
            < 1e-8,
            axis + " rotated",
        )
        delta = np.asarray(new["point_xyz_mm"]) - old["point_xyz_mm"]
        parent.require(
            len(new["attachments"]) == len(old["attachments"]), "attachment census"
        )
        for new_attachment, old_attachment in zip(
            new["attachments"], old["attachments"]
        ):
            for key in (
                "angle_id",
                "duty_id",
                "receiver",
                "receivers",
                "flange",
                "row",
                "transverse",
            ):
                parent.require(
                    new_attachment[key] == old_attachment[key],
                    "attachment identity changed",
                )
            parent.require(
                np.linalg.norm(
                    np.asarray(new_attachment["point"])
                    - old_attachment["point"]
                    - delta
                )
                < 1e-6,
                "attachment did not follow installed shaft",
            )
            # Saved intervals use a unit direction whose first nonzero is positive,
            # regardless of which way the shaft or opposed flange is installed.
            expected_interval_delta = canonical_interval_shift(
                old_attachment["direction"], delta.tolist()
            )
            parent.require(
                np.max(
                    np.abs(
                        np.asarray(new_attachment["interval_mm"])
                        - old_attachment["interval_mm"]
                        - expected_interval_delta
                    )
                )
                < 1e-6,
                "attachment interval did not follow canonical direction",
            )
        if np.linalg.norm(delta) > 1e-6:
            parent.require(
                np.linalg.norm(delta - current["principal_shift_xyz_mm"]) < 1e-6,
                "unexpected shaft translation",
            )
            rows.append({"axis_id": axis, "translation_xyz_mm": delta.tolist()})
    parent.require(
        {r["axis_id"] for r in rows} == set(current["moved_bolt_axes"]),
        "moved-shaft census",
    )
    old_screws = {r["axis_id"]: r for r in previous["screw_axes"]}
    screw_rows = []
    parent.require(len(old_screws) == len(current["screw_axes"]) == 66, "66 screws")
    for new in current["screw_axes"]:
        old = old_screws[new["axis_id"]]
        for key in ("panel", "receiver"):
            parent.require(new[key] == old[key], "changed screw receiver/panel")
        parent.require(
            np.linalg.norm(np.asarray(new["direction_xyz"]) - old["direction_xyz"])
            < 1e-8,
            "rotated screw",
        )
        delta = np.asarray(new["origin_xyz_mm"]) - old["origin_xyz_mm"]
        if np.linalg.norm(delta) > 1e-6:
            parent.require(
                np.linalg.norm(delta - current["principal_shift_xyz_mm"]) < 1e-6,
                "unexpected screw translation",
            )
            screw_rows.append(
                {"axis_id": new["axis_id"], "translation_xyz_mm": delta.tolist()}
            )
    parent.require(
        {r["axis_id"] for r in screw_rows} == set(current["moved_panel_screw_axes"]),
        "moved-screw census",
    )
    starting = [
        axis
        for axis, row in after.items()
        if row["source"] == "original_starting_frame_axis"
    ]
    parent.require(len(starting) == 12, "twelve starting bolt arrangements")
    parent.require(
        not set(starting) & set(current["moved_bolt_axes"]), "starting bolt moved"
    )
    return {
        "total_physical_shafts": len(after),
        "moved_shafts": rows,
        "unchanged_starting_frame_bolt_ids": starting,
        "unchanged_hardware_recipes_grips_and_directions": True,
        "total_panel_kicker_screws": 66,
        "moved_screws": screw_rows,
        "affected_duties": current["affected_duties"],
        "changed_timber_ids": [
            r["id"] for r in current["changed_finished_solids"] if r["kind"] == "timber"
        ],
        "current_response_exists_in_this_packet": False,
        "field_transfer": "NOT_ADMITTED: source geometry differs from all six issued fields",
    }


def washer_seats(current, previous, evidence, first_field):
    changed = {
        r["id"]: r for r in current["changed_finished_solids"] if r["kind"] == "timber"
    }
    previous_axes = {r["id"]: r for r in previous["axes"]}
    current_axes = {r["id"]: r for r in current["axes"]}
    ends = {r["id"]: r for r in first_field["shaft_end_capture_actions"]}
    shapes = {}
    rows = []
    for old in evidence["washers"]["seat_geometry"]:
        row = dict(old)
        parent.require(
            old["full_modeled_support"], "prior seat did not qualify geometrically"
        )
        axis, host = row["axis_id"], row["host"]
        delta = (
            np.asarray(current_axes[axis]["point_xyz_mm"])
            - previous_axes[axis]["point_xyz_mm"]
        )
        if host in changed:
            source = changed[host]
            if host not in shapes:
                shapes[host] = cq.importers.importBrep(str(ROOT / source["path"])).val()
            capture = ends[row["capture_id"]]
            parent.require(capture["end"]["host"] == host, "seat host differs")
            point = np.asarray(capture["host_support_point_xyz_mm"]) + delta
            inward = -np.asarray(capture["end"]["direction_on_shaft_xyz"])
            row.update(
                component.annular_probe(
                    shapes[host],
                    point.tolist(),
                    inward.tolist(),
                    row["bounding_OD_mm"],
                    row["bounding_inner_diameter_mm"],
                )
            )
            row.update(
                {
                    "proof": "fresh bounding-annulus query on saved midpoint-ready base v3 timber",
                    "solid_source": source,
                    "current_host_support_point_xyz_mm": point.tolist(),
                    "old_force_used_as_new_response": False,
                }
            )
        else:
            parent.require(np.linalg.norm(delta) < 1e-6, "moved seat on unchanged host")
            row["proof"] = (
                "reused prior full seat: unchanged shaft location and same finished host"
            )
        rows.append(row)
    parent.require(len(rows) == 112, "112 wood washer ends")
    queried = [r for r in rows if "current_host_support_point_xyz_mm" in r]
    return {
        "total_wood_seats": len(rows),
        "fresh_changed_host_probes": len(queried),
        "unchanged_seat_proofs_reused": len(rows) - len(queried),
        "minimum_fresh_support_fraction": min(r["support_fraction"] for r in queried),
        "failed_seat_ids": [
            r["capture_id"] for r in rows if not r["full_modeled_support"]
        ],
        "scope": "nominal saved geometry only; no physical contact pressure, stiffness or current load qualification",
    }, rows


def screw_edges(current):
    panels = {
        r["id"]: r for r in current["changed_finished_solids"] if r["kind"] == "panel"
    }
    shapes = {
        k: cq.importers.importBrep(str(ROOT / r["path"])).val()
        for k, r in panels.items()
    }
    rows = []
    for axis in current["screw_axes"]:
        if axis["axis_id"] not in current["moved_panel_screw_axes"]:
            continue
        box = shapes[axis["panel"]].BoundingBox()
        x = axis["origin_xyz_mm"][0]
        rows.append(
            {
                "axis_id": axis["axis_id"],
                "panel": axis["panel"],
                "receiver": axis["receiver"],
                "x_mm": x,
                "panel_min_x_mm": box.xmin,
                "distance_to_left_panel_outline_edge_mm": x - box.xmin,
                "current_receiver_body_fraction": axis[
                    "conditional_raw_wood_penetration_body_fraction"
                ],
                "strength_or_punching_capacity": None,
            }
        )
    parent.require(len(rows) == 10, "ten moved screw edge queries")
    parent.require(
        all(r["current_receiver_body_fraction"] == 1 for r in rows),
        "unsupported moved screw",
    )
    return rows


def brace_paths(current, first_field, cases, component_reports):
    timbers = {r["name"]: r for r in first_field["source_inputs"]["timber_rows"]}
    screws = current["screw_axes"]
    members = []
    raw_actions = []
    for name in (
        "base_header",
        "base_rail_top",
        "base_principal_center_left",
        "base_principal_center_right",
    ):
        member = timbers[name]
        grain = np.asarray(member["axis"])
        start, end = np.asarray(member["start"]), np.asarray(member["end"])
        if name == "base_principal_center_right":
            start = start + current["principal_shift_xyz_mm"]
            end = end + current["principal_shift_xyz_mm"]
        if member["width_mm"] <= member["depth_mm"]:
            weak, width = np.asarray(member["section_u"]), member["width_mm"]
        else:
            weak, width = np.asarray(member["section_v"]), member["depth_mm"]
        length = float(np.dot(end - start, grain))
        own_screws = [r for r in screws if r["receiver"] == name]
        stations = sorted(
            float(np.dot(np.asarray(r["origin_xyz_mm"]) - start, grain))
            for r in own_screws
        )
        parent.require(
            all(-1e-6 <= s <= length + 1e-6 for s in stations),
            "brace point outside member",
        )
        gaps = np.diff([0.0, *stations, length]).tolist()
        dots = [float(abs(np.dot(r["direction_xyz"], weak))) for r in own_screws]
        parent.require(max(dots) < 1e-8, "weak brace direction is not panel in-plane")
        ids = {r["axis_id"] for r in own_screws}
        old_loads = []
        for case_id, field, _ in cases:
            for action in field["panel_screw_actions"]:
                if action["axis_id"] in ids:
                    row = {
                        "case_id": case_id,
                        "axis_id": action["axis_id"],
                        "old_field_receiver": name,
                        "weak_direction_action_n": abs(
                            float(np.dot(action["force_on_receiver_xyz_n"], weak))
                        ),
                        "simultaneous_lateral_n": action["lateral_n"],
                        "simultaneous_withdrawal_n": action["withdrawal_n"],
                        "current_brace_force_demand": None,
                    }
                    old_loads.append(row)
                    raw_actions.append(row)
        old_heads = [
            r
            for _, report in component_reports
            for r in report["simultaneous_Hillman_actions_and_generic_references"]
            if r["axis_id"] in ids
        ]
        routes = []
        for panel in sorted({r["panel"] for r in own_screws}):
            anchors = [
                r for r in screws if r["panel"] == panel and r["receiver"] != name
            ]
            routes.append(
                {
                    "panel": panel,
                    "other_receivers": sorted({r["receiver"] for r in anchors}),
                    "other_anchor_axis_ids": [r["axis_id"] for r in anchors],
                    "route": "member -> Hillman lateral bearing -> panel in-plane -> other Hillman axes -> other frame receivers",
                    "route_strength_and_stiffness_qualified": False,
                }
            )
        members.append(
            {
                "member": name,
                "gross_length_mm": length,
                "weak_dimension_mm": width,
                "unbraced_Ke1_Le_over_weak_dimension": length / width,
                "NDS3p7p1p4_domain_limit_mm": 50 * width,
                "candidate_screw_axis_ids": sorted(ids),
                "candidate_stations_mm": stations,
                "end_and_interior_geometric_gaps_mm": gaps,
                "largest_candidate_gap_mm": max(gaps),
                "Ke1_candidate_gap_over_weak_dimension": max(gaps) / width,
                "weak_displacement_direction_xyz": weak.tolist(),
                "maximum_screw_axis_alignment_to_weak_direction": max(dots),
                "required_attachment_action": "lateral, through panel in-plane stiffness",
                "candidate_panel_return_paths": routes,
                "old_issued_field_peak_weak_direction_screw_action": max(
                    old_loads, key=lambda r: r["weak_direction_action_n"]
                ),
                "old_issued_field_peak_candidate_screw_generic_head_ratio_CD1": max(
                    r["generic_head_ratio_CD1"] for r in old_heads
                ),
                "effective_length_adopted": False,
                "Cp_adopted": False,
            }
        )
    return members, raw_actions


def group_applicability(current, cases):
    summary, details = [], []
    first = cases[0][1]
    source_shafts = {r["axis_id"]: r for r in first["source_inputs"]["shafts"]}
    unsupported = [
        r for r in cases[0][2]["timber"]["shaft_components"] if r["component"] is None
    ]
    pair_count = qualifying = 0
    for _, _, reports in cases:
        for duty in reports["timber"]["duties"]:
            for pair in duty.get("own_receiver_pair_geometry_and_actions", []):
                pair_count += 1
                qualifying += bool(pair["uniform_load_aligned_row_qualified"])
    for shaft in unsupported:
        axis = shaft["axis_id"]
        surfaces = source_shafts[axis]["surfaces"]
        axis_direction = np.asarray(source_shafts[axis]["basis"][0])
        own_cases = []
        for case_id, field, _ in cases:
            ports = [
                r
                for kind in (
                    "common_shaft_wood_bearing_actions",
                    "common_shaft_steel_port_actions",
                )
                for r in field[kind]
                if r["axis_id"] == axis
            ]
            rows = []
            for port in ports:
                force = np.asarray(port["force_on_host_xyz_n"])
                lateral = force - np.dot(force, axis_direction) * axis_direction
                rows.append(
                    {
                        "host": port["host"],
                        "surface_index": port["surface_index"],
                        "surface_interval_mm": port["surface_interval_mm"],
                        "lateral_force_xyz_n": lateral.tolist(),
                        "lateral_n": float(np.linalg.norm(lateral)),
                        "own_free_moment_xyz_nmm": port[
                            "moment_on_host_at_point_xyz_nmm"
                        ],
                    }
                )
            steel = [r for r in rows if r["host"].startswith("eoere_clip")]
            equal_outer_error = (
                float(
                    np.linalg.norm(
                        np.asarray(steel[0]["lateral_force_xyz_n"])
                        - steel[1]["lateral_force_xyz_n"]
                    )
                )
                if len(steel) == 2
                else None
            )
            own_cases.append(
                {
                    "case_id": case_id,
                    "axis_id": axis,
                    "own_ports": rows,
                    "two_steel_outer_force_difference_n": equal_outer_error,
                    "complete_joint_reference_n": None,
                }
            )
        details.extend(own_cases)
        summary.append(
            {
                "axis_id": axis,
                "existing_disposition": shaft["disposition"],
                "ordered_material_stack": [
                    {
                        "kind": r["kind"],
                        "host": r["host"],
                        "bearing_length_mm": r["interval_mm"][1] - r["interval_mm"][0],
                    }
                    for r in sorted(surfaces, key=lambda r: r["interval_mm"][0])
                ],
                "moved_in_base_v3": axis in current["moved_bolt_axes"],
                "peak_old_own_port_lateral_n": max(
                    r["lateral_n"] for c in own_cases for r in c["own_ports"]
                ),
                "peak_old_own_port_free_moment_nmm": max(
                    float(np.linalg.norm(r["own_free_moment_xyz_nmm"]))
                    for c in own_cases
                    for r in c["own_ports"]
                ),
                "maximum_old_two_steel_outer_force_difference_n": max(
                    c["two_steel_outer_force_difference_n"] for c in own_cases
                )
                if shaft["steel_surface_count"] == 2
                else None,
                "next_method": "connected three-member dowel bearing/yield model with own loading, actual thread intervals and member properties; separate axial seating and free couples",
                "complete_joint_reference_n": None,
            }
        )
    parent.require(
        len(summary) == 8 and pair_count == 276 and qualifying == 0,
        "group applicability census",
    )
    return {
        "unsupported_shaft_count": len(summary),
        "unsupported_shafts": summary,
        "issued_pair_records_examined": pair_count,
        "existing_uniform_load_aligned_row_qualified_records": qualifying,
        "NDS11p3p6_row_formula_directly_adopted": False,
        "single_shear_refs_reused_as_complete_joint_rating": False,
        "appendix_E_parallel_tearout_used_as_crossgrain_opening_resistance": False,
    }, details


def run():
    inputs = json.loads((HERE / "inputs.json").read_bytes())
    refs = inputs["references"]
    prior = parent.read(refs["prior_details"])
    pins = {}
    add_pins(pins, prior["complete_source_sha256"])
    add_pins(pins, {r["path"]: r["sha256"] for r in refs.values()})
    current = parent.read(refs["current_base"])
    add_pins(pins, current["source_sha256"])
    add_pins(
        pins,
        {
            str(p.relative_to(ROOT)): parent.sha(p)
            for p in (HERE / "analyze.py", HERE / "inputs.json")
        },
    )
    parent.verify(pins)
    parent.require(
        current["revision"] == "eoere-midpoint-ready-frame-v3"
        and not current["unofficial_2026_grid_included"]
        and not current["mechanics_ready"],
        "frozen base v3 extra OFF",
    )
    original_inputs = parent.read(refs["original_inputs"])
    parent.require(
        current["parent_geometry"]["sha256"]
        == original_inputs["current_geometry"]["sha256"],
        "base parent does not inherit the prior aligned-wire geometry",
    )
    add_pins(
        pins, {current["parent_geometry"]["path"]: current["parent_geometry"]["sha256"]}
    )
    previous = parent.read(original_inputs["current_geometry"])
    intake = parent.module(
        "revised_base_issued_intake", original_inputs["helpers"]["admission"]
    )
    cases = []
    publication = parent.read(refs["publication"])
    component_reports = []
    for case in original_inputs["cases"]:
        field, admitted = intake.load_admitted(ROOT / case["manifest"]["path"])
        add_pins(pins, admitted)
        parent.require(
            field["source_inputs"]["geometry"]["report"]
            == original_inputs["old_geometry"],
            "old field geometry identity",
        )
        cases.append(
            (case["case_id"], field, {"timber": parent.read(case["reports"]["timber"])})
        )
        pub_case = next(
            r for r in publication["cases"] if r["case_id"] == case["case_id"]
        )
        reference = pub_case["references"]["components"]
        add_pins(pins, {reference["path"]: reference["sha256"]})
        component_reports.append(
            (case["case_id"], parent.read(reference)["component_reductions"])
        )
    known = component.known_answers()
    geometry = delta_audit(current, previous)
    washer, washer_rows = washer_seats(current, previous, prior, cases[0][1])
    edge_rows = screw_edges(current)
    braces, brace_actions = brace_paths(current, cases[0][1], cases, component_reports)
    groups, group_rows = group_applicability(current, cases)
    previous_result = parent.read(refs["previous_result"])
    cleat = previous_result["cleat_member_components"]
    cleat_screens = {
        "source": refs["previous_result"],
        "current_cleat_solids_unchanged_from_trimmed_geometry": not any(
            name.startswith("eoere_cleat") for name in geometry["changed_timber_ids"]
        ),
        "old_fixed_actions_with_trimmed_geometry_sensitivities": True,
        "stock_depth_trimmed_engagement_reference_range_n": cleat[
            "stock_depth_trimmed_engagement_parameter_sensitivity_range_n"
        ],
        "worst_matching_section_shear_n": cleat["worst_matching_section_shear"][
            "maximum_adjacent_grain_normal_section_Y_shear_n"
        ],
        "worst_matching_section_shear_ratio": cleat["worst_matching_section_shear"][
            "stock_depth_trimmed_engagement_parameter_sensitivity_ratio"
        ],
        "parallel_net_tension_reference_range_n": cleat[
            "loaded_bolt_plane_adjusted_net_tension_reference_range_n"
        ],
        "mechanisms_still_separate": [
            "Y-normal tensile opening",
            "full section bending/torsion",
            "sloping-end qualification",
            "bolt group and mixed material stack",
            "washer pressure/preload",
        ],
        "actual_all_mode_current_cleat_resistance_n": None,
        "current_geometry_response": False,
    }
    nominal = parent.read(refs["nominal_heel_result"])
    supplier = {
        **inputs["supplier_observation"],
        "old_nominal_heel_scenario": {
            "thickness_mm": nominal["thickness_mm"],
            "inside_radius_mm": nominal["inside_radius_mm"],
            "worst": nominal["worst"],
            "reference_margin_percent": nominal["reference_margin_percent"],
            "current_geometry_response": False,
            "actual_formed_heel_stress_bound": False,
        },
        "supplier_question_priority": inputs["supplier_questions"],
        "seller_contact_sent": False,
        "part_inspected_or_tested": False,
    }
    retained_exceedances = [
        {
            "case_id": r["case_id"],
            **{
                k: v
                for k, v in r["component_metrics"].items()
                if k
                in (
                    "generic_Hillman_head_CD1",
                    "panel_spatial_bending_CD1",
                    "panel_spatial_rolling_shear_CD1",
                )
            },
        }
        for r in publication["cases"]
    ]
    parent.verify(pins)
    result = {
        "schema": "eoere_revised_base_bounded_audit/v1",
        "status": "COMPLETE_READ_ONLY_AUDIT_STRENGTH_UNRESOLVED",
        "current_base": refs["current_base"],
        "current_geometry_revision": current["revision"],
        "six_field_geometry_revision": "eoere-bottom-rail-tnut-clearance-v1",
        "geometry_delta": geometry,
        "washer_support": washer,
        "moved_screw_edges": edge_rows,
        "candidate_member_restraint_paths": braces,
        "group_applicability": groups,
        "reused_cleat_component_screens": cleat_screens,
        "reused_single_bolt_yield_components": previous_result["bolt_yield_components"],
        "supplier_information": supplier,
        "retained_old_panel_screw_exceedances": retained_exceedances,
        "known_answers": known,
        "source_pin_count": len(pins),
        "complete_source_canonical_sha256": parent.canonical(pins),
        "runtime": {
            "python": platform.python_version(),
            "cadquery": cq.__version__,
            "numpy": np.__version__,
        },
        "execution": {
            "native_solve": False,
            "response_assembly": False,
            "geometry_rebuild": False,
            "mesh_export": False,
        },
        "limits": inputs["limits"],
        "fabrication_or_climbing_release": False,
    }
    details = {
        "complete_source_sha256": pins,
        "washer_seat_rows": washer_rows,
        "old_brace_axis_actions": brace_actions,
        "unsupported_stack_own_case_ports": group_rows,
    }
    return result, details


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    result, details = run()
    args.out.mkdir(parents=True, exist_ok=True)
    for name, value in (("result.json", result), ("details.json", details)):
        (args.out / name).write_text(
            json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n"
        )
    print(
        json.dumps(
            {
                "status": result["status"],
                "washer_support": result["washer_support"],
                "pin_count": result["source_pin_count"],
            }
        )
    )
