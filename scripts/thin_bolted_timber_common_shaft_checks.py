"""Fresh timber components from one audited 132-body physical-shaft state.

Wood resultants and cut wrenches are independently reduced from the actual
distributed bearing points and each own end capture. The previous 72/12
paired-arrow demands are not used. No CAD query or solve occurs here.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from collections import defaultdict
from itertools import pairwise
from pathlib import Path

from scripts import thin_bolted_timber_demand_checks as previous
from scripts import thin_bolted_timber_resistance as unit
from scripts import thin_bolted_timber_section_properties as sections

ROOT, PACKET = unit.ROOT, unit.PACKET
PREVIOUS_SHA = "1be05e74563d2cc7a7ea5437aa4ff7217e62f8314f9fe011ff273d201f755e20"
SECTIONS_SHA = "398e883849dfd83a34aeb60b5ac0b5d50f57ffa9b01f3f2427e341725749a80a"
COMMON = "scripts/thin_bolted_common_shaft.py"
COMMON_SHA = "0ff8c52a36f168cba0bd3fed2d592daa9e5d9de5facbc650b151f64c2f23f4eb"
AUDIT = "scripts/thin_bolted_common_shaft_export_audit.py"
AUDIT_SHA = "26feb3bb369490729c6f8e48365d816cbda458b2fdeea89a97b8286842d1be58"
STEEL = "scripts/thin_bolted_common_shaft_steel.py"
STEEL_SHA = "4b28f7a055c50dc127569b7df387f8e8d973f74080d2937ceb5db356a89d9952"
SPAN_SOURCE = PACKET / "compatible-frame-a12-rear-finished-floor-v4.json"
SPAN_SOURCE_SHA = "8d90941f9d1cb20d938ddc65992b2db7b0fe0c38420bf6bfc10fc0684281256d"


def read_member_span_geometry() -> dict:
    """Reuse only unchanged centerlines/extents/bases from issued geometry.

    This file contains an earlier force field. No force, displacement,
    equilibrium result or acceptance from it is selected here.
    """
    payload = SPAN_SOURCE.read_bytes()
    unit.require(hashlib.sha256(payload).hexdigest() == SPAN_SOURCE_SHA, "frozen member span geometry differs")
    source = json.loads(payload)
    unit.require(source["candidate"] == unit.CANDIDATE
                 and source["geometry_cache_sha256"] == previous.NATIVE_SHA
                 and source["layout_report_sha256"] == unit.LAYOUT_SHA,
                 "span source does not bind the unchanged candidate geometry")
    grouped = defaultdict(list)
    for row in source["member_element_actions"]:
        grouped[row["member"]].append(row)
    result = {}
    for name, rows in grouped.items():
        basis = rows[0]["basis_grain_u_v_xyz"]
        g = basis[0]
        points = [row[key] for row in rows for key in ("start_xyz_mm", "end_xyz_mm")]
        start, end = min(points, key=lambda p: unit.dot(g, p)), max(points, key=lambda p: unit.dot(g, p))
        result[name] = {"start_xyz_mm": start, "end_xyz_mm": end, "basis_grain_u_v_xyz": basis}
    unit.require(len(result) == 20, "all20 unchanged timber span geometries required")
    return result


def verify_member_span_geometry(demand: dict, spans: dict) -> dict:
    """Authenticate new refined meshes against unchanged physical centerlines."""
    grouped = defaultdict(list)
    for row in demand["member_element_actions"]:
        grouped[row["member"]].append(row)
    unit.require(set(grouped) == set(spans), "new member mesh contains foreign/missing timber")
    for name, rows in grouped.items():
        saved = spans[name]
        basis = saved["basis_grain_u_v_xyz"]
        grain, origin = basis[0], saved["start_xyz_mm"]
        expected_low, expected_high = unit.dot(grain, origin), unit.dot(grain, saved["end_xyz_mm"])
        intervals = []
        for row in rows:
            unit.require(all(math.dist(actual, expected) < 1e-8
                             for actual, expected in zip(row["basis_grain_u_v_xyz"], basis, strict=True)),
                         "fresh member basis differs from authenticated geometry")
            points = [unit.vector(row[key], "fresh member endpoint") for key in ("start_xyz_mm", "end_xyz_mm")]
            unit.require(all(math.hypot(*unit.cross([a - b for a, b in zip(p, origin, strict=True)], grain)) < 1e-5
                             for p in points), "fresh member endpoint leaves authenticated centerline")
            low, high = sorted(unit.dot(grain, p) for p in points)
            unit.require(high - low > 1e-7, "fresh member element has no geometric length")
            intervals.append((low, high))
        intervals.sort()
        unit.require(abs(intervals[0][0] - expected_low) < 1e-5 and abs(intervals[-1][1] - expected_high) < 1e-5
                     and all(abs(a[1] - b[0]) < 1e-5 for a, b in pairwise(intervals)),
                     "fresh member mesh omits/overlaps or changes authenticated physical extents")
    return {"member_count": len(grouped), "centerlines_bases_complete_extents_authenticated": True,
            "interior_refinement_allowed": True, "historical_force_or_acceptance_selected": False}


def verify_alias_state_labels(demand: dict) -> None:
    """Aggregate and cut aliases must retain the admitted complete identity."""
    keys = ("state_id", "case_id", "accessory_placement")
    identity = tuple(demand[key] for key in keys)
    for table in ("common_shaft_wood_bearing_actions", "common_shaft_steel_port_actions",
                  "common_shaft_section_cut_actions", "member_element_actions"):
        for row in demand[table]:
            for labeled in (row, *row.get("cuts", [])):
                unit.require(tuple(labeled.get(key) for key in keys) == identity,
                             "common timber aggregate/cut alias mixes or omits admitted state/load identity")


def own_host_force(row: dict) -> list[float]:
    force = unit.vector(row["force_on_second_xyz_n"], "own host force")
    first = unit.vector(row["force_on_first_xyz_n"], "own shaft force")
    unit.require(math.hypot(*previous.add(force, first)) < 1e-7, "own shaft/wood force dual differs")
    return force


def aggregate_wood_bearings(layout: dict, packet: dict, demand: dict) -> list[dict]:
    """Independently reproduce all own wood F/M, including capture datums."""
    axes = {row["id"]: row for row in layout["installed_axes"]}
    raw_bearing = demand["common_shaft_bearing_actions"]
    captures = demand["shaft_end_capture_actions"]
    exported = demand["common_shaft_wood_bearing_actions"]
    indexed = {(row["axis_id"], row["member"]): row for row in exported}
    receivers = packet["finished_geometry_queries"]["receiver_boundary_geometry"]
    keys = {(row["axis_id"], row["member"]) for row in receivers}
    unit.require(len(indexed) == len(exported) == len(receivers) and set(indexed) == keys,
                 "complete unique actual wood-bearing aggregate census required")
    result = []
    for receiver in receivers:
        key = (receiver["axis_id"], receiver["member"])
        axis, saved = axes[key[0]], indexed[key]
        unit.require(all(saved.get(name) == demand[name] for name in ("state_id", "case_id", "accessory_placement")),
                     "wood aggregate alias mixes or omits admitted state/load identity")
        intervals = receiver["finished_full_wall_intervals_from_axis_point_mm"]
        unit.require(len(intervals) == 1, "this issued aggregate method requires one current full-wall span per host")
        span = intervals[0]
        shaft = unit.unit(axis["direction"])
        point = previous.add(axis["point"], previous.scale(shaft, .5 * sum(span)))
        unit.require(math.dist(saved["grain_axis_xyz"], receiver["grain_axis_xyz"]) < 1e-8
                     and math.dist(saved["surface_interval_mm"], span) < 1e-5
                     and math.dist(saved["point_xyz_mm"], point) < 1e-5,
                     "actual wood aggregate grain/span/datum differs from frozen bearing geometry")
        selected = [row for row in raw_bearing if row["axis_id"] == key[0]
                    and row["second"] == key[1] and row["surface_material"] == "wood"]
        own_captures = [row for row in captures if row["axis_id"] == key[0] and row["second"] == key[1]]
        unit.require(len(selected) == len({row["id"] for row in selected}) == 2
                     and {row["quad_index"] for row in selected} == {0, 1}
                     and all(row["surface_index"] == saved["surface_index"] for row in selected)
                     and set(saved["own_bearing_points"]) == {row["id"] for row in selected}
                     and len(saved["own_bearing_points"]) == 2
                     and len({row["id"] for row in own_captures}) == len(own_captures)
                     and set(saved["own_end_captures"]) == {row["id"] for row in own_captures}
                     and len(saved["own_end_captures"]) == len(own_captures),
                     "own wood aggregate includes a foreign/missing bearing or capture")
        force, moment, radial_force = [0.] * 3, [0.] * 3, [0.] * 3
        points = []
        for row in [*selected, *own_captures]:
            action = own_host_force(row)
            datum = unit.vector(row.get("host_support_point_xyz_mm", row["point_xyz_mm"]), "own wood support datum")
            free = unit.vector(row.get("moment_on_second_at_point_xyz_nmm", [0.] * 3), "own wood free couple")
            force = previous.add(force, action)
            moment = previous.add(moment, previous.add(unit.cross([a - b for a, b in zip(datum, point, strict=True)], action), free))
            if row in selected:
                radial_force = previous.add(radial_force, action)
                unit.require(math.dist(row["surface_interval_mm"], span) < 1e-5,
                             "wood radial path belongs to a different actual span")
                points.append({"id": row["id"], "point_xyz_mm": datum, "force_on_wood_xyz_n": action,
                               "axis_station_mm": row["axis_station_mm"], "weight_length_mm": row["weight_length_mm"],
                               **unit.resolved_action(action, receiver["grain_axis_xyz"], shaft)})
        unit.require(math.dist(saved["force_on_host_xyz_n"], force) < 1e-7
                     and math.dist(saved["moment_on_host_at_point_xyz_nmm"], moment) < 1e-4,
                     "producer wood aggregate differs from independent own-point wrench reduction")
        resolved = unit.resolved_action(force, receiver["grain_axis_xyz"], shaft)
        result.append({"state_id": demand["state_id"], "case_id": demand["case_id"],
                       "accessory_placement": demand["accessory_placement"], "axis_id": key[0], "member": key[1],
                       "point_xyz_mm": point, "actual_finished_bearing_interval_mm": span,
                       "actual_finished_bearing_length_mm": span[1] - span[0],
                       "force_on_wood_xyz_n": force, "moment_on_wood_at_point_xyz_nmm": moment,
                       "radial_bearing_resultant_xyz_n": radial_force, "resolved_resultant": resolved,
                       "own_radial_bearing_points": points, "own_capture_ids": [row["id"] for row in own_captures],
                       "signed_boundary_diagnostics": previous.signed_boundary_diagnostics(resolved, receiver, axis["diameter_mm"]),
                       "resultant_is_not_uniform_bearing_distribution": True,
                       "opposed_flange_or_other_wood_force_inferred": False})
    return result


def verify_steel_aliases(demand: dict, reduced: list[dict]) -> None:
    """Check the producer's optional flange aliases against reused reduction."""
    supplied = demand["common_shaft_steel_port_actions"]
    keys = ("axis_id", "angle_id", "flange")
    indexed = {tuple(row[key] for key in keys): row for row in supplied}
    wanted = {tuple(row[key] for key in keys) for row in reduced}
    unit.require(len(indexed) == len(supplied) == len(reduced) and set(indexed) == wanted,
                 "complete unique actual steel flange aggregate census required")
    for row in reduced:
        saved = indexed[tuple(row[key] for key in keys)]
        for name, tolerance in (("point_xyz_mm", 1e-5), ("force_on_steel_xyz_n", 1e-7),
                                ("moment_on_steel_at_point_xyz_nmm", 1e-4)):
            unit.require(math.dist(unit.vector(saved[name], name), unit.vector(row[name], name)) < tolerance,
                         "steel flange alias differs from independent own-point wrench reduction")


def own_wood_washer_references(demand: dict, packet: dict) -> list[dict]:
    """Compare each own wood capture beside its separate ideal annulus."""
    references = {(row["axis_id"], row["role"]): row for row in packet["washer_wood_interface_references"]}
    rows = []
    for capture in demand["shaft_end_capture_actions"]:
        role = capture["end"]["end"]
        reference = references[(capture["axis_id"], role + "_washer")]
        if reference["support_material"] != "wood":
            continue
        value = reference["ideal_full_contact_wood_annulus_reference_n"]
        unit.require(value is not None and value > 0. and capture["compression_n"] >= 0.,
                     "own wood annulus/capture parameter is invalid")
        rows.append({"state_id": demand["state_id"], "case_id": demand["case_id"],
                     "accessory_placement": demand["accessory_placement"],
                     "axis_id": capture["axis_id"], "role": role, "member": capture["second"],
                     "own_capture_id": capture["id"], "model_own_capture_compression_n": capture["compression_n"],
                     "shaft_pressure_face_point_xyz_mm": capture["point_xyz_mm"],
                     "actual_host_support_point_xyz_mm": capture["host_support_point_xyz_mm"],
                     "ideal_full_contact_Fc_perp_annulus_reference_n": value,
                     "own_model_capture_over_ideal_annulus_component_ratio": capture["compression_n"] / value,
                     "duration_factor_applied_to_Fc_perp": 1.,
                     "actual_wood_pressure_distribution_or_complete_axial_capacity": None,
                     "limits": "The model's own unilateral capture force is retained. Exact contact footprint, washer spreading/material, prying, head/nut/thread and local wood fracture are not adopted."})
    return rows


def bearing_parameter_diagnostics(wood: list[dict], layout: dict) -> list[dict]:
    """Actual quadrature forces beside conditional NDS material parameters.

    F/(D*weight) is the foundation patch's average bearing stress. Fe_theta
    is a material parameter in the NDS yield equations, not an adjusted
    allowable local patch stress or a complete connection resistance.
    """
    axes = {row["id"]: row for row in layout["installed_axes"]}
    output = []
    for host in wood:
        axis = axes[host["axis_id"]]
        for fraction in (1., .8):
            diameter = axis["diameter_mm"] * fraction
            values = []
            for point in host["own_radial_bearing_points"]:
                theta = point["load_to_grain_degrees"]
                pressure = point["lateral_n"] / (diameter * point["weight_length_mm"])
                fe = unit.dfl_dowel_bearing_psi(diameter / 25.4, theta) if theta is not None else None
                fe_mpa = fe * unit.N_PER_LBF / 25.4**2 if fe is not None else None
                values.append({**point, "foundation_patch_average_pressure_n_mm2": pressure,
                               "conditional_NDS_Fe_theta_psi": fe,
                               "pressure_over_NDS_material_parameter": pressure / fe_mpa if fe_mpa else None,
                               "adjusted_allowable_patch_stress_or_connection_utilization": None})
            output.append({"state_id": host["state_id"], "case_id": host["case_id"],
                           "accessory_placement": host["accessory_placement"], "axis_id": host["axis_id"], "member": host["member"],
                           "reference_diameter_fraction_scenario": fraction,
                           "reference_diameter_mm": diameter, "actual_D_or_Dr_adopted": False,
                           "same_state_radial_patch_components": values,
                           "NDS_general_common_shaft_adjusted_resistance_n": None,
                           "limits": "The explicit diameter sensitivity changes parameter references only; it does not recompute the compatible elastic field. Fe_theta and patch pressure are not a local ASD acceptance rule."})
    return output


def member_point_inputs(demand: dict) -> tuple[dict, dict]:
    """Preserve every actual own host datum; collect complete point wrenches."""
    point_actions, gravity = defaultdict(list), {}
    for table in ("common_shaft_bearing_actions", "shaft_end_capture_actions", "panel_screw_actions", "contact_actions"):
        for row in demand[table]:
            force = unit.vector(row["force_on_first_xyz_n"], "same-state point force")
            first_point = unit.vector(row["point_xyz_mm"], "first point datum")
            second_point = unit.vector(row.get("host_support_point_xyz_mm", first_point), "own host support datum")
            first_moment = row.get("moment_on_first_at_point_xyz_nmm", row.get("moment_at_point_model_xyz_nmm", [0.] * 3))
            second_moment = row.get("moment_on_second_at_point_xyz_nmm", previous.scale(first_moment, -1.))
            point_actions[row["first"]].append((first_point, force, unit.vector(first_moment, "first free moment")))
            point_actions[row["second"]].append((second_point, previous.scale(force, -1.), unit.vector(second_moment, "second free moment")))
    for row in demand["floor_actions"]:
        point_actions[row["first"]].append((row["point_xyz_mm"], row["force_on_first_xyz_n"], previous.free_moment(row)))
    for load in demand["body_applied_loads"]:
        if load["id"].startswith("self-weight/"):
            unit.require(load["body"] not in gravity, "duplicate selfweight in fresh timber replay")
            gravity[load["body"]] = (load["point_xyz_mm"], load["force_xyz_n"])
        else:
            point_actions[load["body"]].append((load["point_xyz_mm"], load["force_xyz_n"], load.get("moment_xyz_nmm", [0.] * 3)))
    return point_actions, gravity


def replay_existing_member_cuts(demand: dict, full: dict, spans: dict) -> list[dict]:
    """Complete simultaneous six-vectors at saved stations, no CAD query."""
    verify_member_span_geometry(demand, spans)
    point_actions, gravity = member_point_inputs(demand)
    elements = defaultdict(list)
    for row in demand["member_element_actions"]:
        unit.require(row["state_id"] == demand["state_id"], "member element mixes force states")
        elements[row["member"]].append(row)
    output = []
    live = any(row["id"].startswith("climber/") for row in demand["body_applied_loads"])
    for geometry in full["finished_member_sections"]:
        name, grain = geometry["member"], geometry["grain_axis_xyz"]
        unit.require(name in elements and name in gravity, "fresh complete member span/selfweight missing")
        rows = elements[name]
        unit.require(all(math.dist(row["basis_grain_u_v_xyz"][0], grain) < 1e-8 for row in rows),
                     "member section replay grain differs from finished geometry")
        points = [row[key] for row in rows for key in ("start_xyz_mm", "end_xyz_mm")]
        start = min(points, key=lambda p: unit.dot(grain, p))
        low, high = min(unit.dot(grain, p) for p in points), max(unit.dot(grain, p) for p in points)
        center, weight = gravity[name]
        u, v, _ = sections.section_basis(grain)
        witnesses = []
        for section in geometry["sampled_sections"]:
            station = section["station_global_grain_projection_mm"]
            if not low - 1e-5 <= station <= high + 1e-5:
                continue
            cut = previous.add(start, previous.scale(grain, station - low))
            wrench = previous.member_cut_wrench(grain, low, high, cut, center, weight, point_actions[name])
            force, moment = wrench["force_on_lower_portion_xyz_n"], wrench["moment_on_lower_portion_about_cut_xyz_nmm"]
            area, axial = section["finished_area_mm2"], wrench["axial_tension_positive_n"]
            ft = area * 575. * unit.N_PER_LBF / 25.4**2
            fc = area * 1350. * unit.N_PER_LBF / 25.4**2
            shear = [unit.dot(force, a) for a in (u, v)]
            bending = [unit.dot(moment, a) for a in (u, v)]
            witnesses.append({"state_id": demand["state_id"], "case_id": demand["case_id"],
                              "accessory_placement": demand["accessory_placement"], "member": name, **wrench,
                              "finished_area_mm2": area, "basis_u_v_grain_xyz": [u, v, grain],
                              "shear_force_uv_n": shear, "bending_moment_uv_nmm": bending,
                              "torsion_nmm": unit.dot(moment, grain),
                              "shear_force_magnitude_n": math.hypot(*shear),
                              "bending_moment_magnitude_about_cut_datum_nmm": math.hypot(*bending),
                              "tension_average_area_reference": previous.duration_component_sensitivity(
                                  ft, max(0., axial), case_id=demand["case_id"], live_load_present=live),
                              "compression_average_area_reference": previous.duration_component_sensitivity(
                                  fc, max(0., -axial), case_id=demand["case_id"], live_load_present=live),
                              "complete_net_section_resistance_or_utilization": None})
        unit.require(witnesses, "no saved member sections intersect fresh action span")
        selectors = {"maximum_tension_average_area_witness": lambda r: r["tension_average_area_reference"]["CD1_same_state_component_ratio"],
                     "maximum_compression_average_area_witness": lambda r: r["compression_average_area_reference"]["CD1_same_state_component_ratio"],
                     "maximum_bending_moment_witness": lambda r: r["bending_moment_magnitude_about_cut_datum_nmm"],
                     "maximum_shear_force_witness": lambda r: r["shear_force_magnitude_n"],
                     "maximum_torsion_witness": lambda r: abs(r["torsion_nmm"])}
        output.append({"member": name, "existing_saved_cut_count_compared": len(witnesses),
                       **{key: max(witnesses, key=selector) for key, selector in selectors.items()},
                       "each_selected_witness_retains_its_own_complete_simultaneous_cut_vector": True,
                       "independently_located_component_extrema_combined": False,
                       "net_centroid_and_inertia_targeted_queries_pending": True,
                       "shear_torsion_local_fracture_stability_complete": False,
                       "continuous_maximum_or_complete_member_acceptance": False})
    return output


def consume(field_path: Path, expected_sha256: str) -> dict:
    from scripts.thin_bolted_common_shaft_export_audit import audit_common_shaft_state

    for relative, expected in ((str(Path(previous.__file__).relative_to(ROOT)), PREVIOUS_SHA),
                               (str(Path(sections.__file__).relative_to(ROOT)), SECTIONS_SHA),
                               (COMMON, COMMON_SHA), (AUDIT, AUDIT_SHA)):
        unit.require(unit.sha(ROOT / relative) == expected, "frozen common timber consumer dependency differs")
    field_bytes = field_path.read_bytes()
    unit.require(hashlib.sha256(field_bytes).hexdigest() == expected_sha256, "parent-released common field differs")
    demand = json.loads(field_bytes)
    packet, _, layout = previous.read_unit()
    unit.require(demand["candidate"] == unit.CANDIDATE
                 and demand["layout_report_sha256"] == unit.LAYOUT_SHA
                 and demand["geometry_cache_sha256"] == previous.NATIVE_SHA,
                 "common timber field candidate/geometry identity differs")
    unit.require(demand["state_id"] == previous.state_identity(demand), "common state does not bind all case/accessory/parameters")
    audit = audit_common_shaft_state(demand)
    unit.require(audit["independent_common_shaft_support_load_and_equilibrium_checks_pass"] is True,
                 "independent132body common shaft gate fails")
    verify_alias_state_labels(demand)
    unit.require(not any(demand["release"].values()), "unexpected common force field release")
    detail = packet["reproducible_detail_artifact"]
    detail_path = ROOT / detail["path"]
    unit.require(unit.sha(detail_path) == detail["sha256"], "saved finished sections differ")
    full = json.loads(detail_path.read_text())["finished_geometry_queries"]
    wood = aggregate_wood_bearings(layout, {"finished_geometry_queries": full}, demand)
    unit.require(len(wood) == 82, "all82 actual wood-bearing paths required")
    # Reuse the other lane's independent72-port reduction and70-shaft cut
    # replay once its source bytes have been reviewed and issued.
    unit.require(STEEL_SHA != "UNISSUED" and unit.sha(ROOT / STEEL) == STEEL_SHA,
                 "shared common steel reduction/cut replay must be frozen before consumption")
    from scripts.thin_bolted_common_shaft import read_inputs
    from scripts.thin_bolted_common_shaft_steel import (
        aggregate_steel_ports,
        verify_shaft_cuts,
    )

    steel = aggregate_steel_ports(layout, demand["common_shaft_bearing_actions"], demand["shaft_end_capture_actions"])
    verify_steel_aliases(demand, steel)
    cut_receipt = verify_shaft_cuts(demand, read_inputs())
    unit.require(len(steel) == 72 and cut_receipt["independent_same_cut_equilibrium_replay_pass"] is True,
                 "shared physical flange/cut reduction gate fails")
    receivers = {(r["axis_id"], r["member"]): r for r in full["receiver_boundary_geometry"]}
    windows = [previous.standard_thread_window(axis, receivers) for axis in layout["installed_axes"]]
    spans = read_member_span_geometry()
    span_receipt = verify_member_span_geometry(demand, spans)
    member_cuts = replay_existing_member_cuts(demand, full, spans)
    duration = previous.read_duration_sources()
    paths = [field_path, Path(__file__), Path(previous.__file__), Path(sections.__file__),
             ROOT / COMMON, ROOT / AUDIT, ROOT / STEEL, previous.UNIT, previous.NATIVE, detail_path, SPAN_SOURCE,
             ROOT / "tests/test_thin_bolted_timber_common_shaft_checks.py",
             previous.DURATION_CACHE / "source-bounds.json"]
    pins = {str(path.resolve().relative_to(ROOT)): unit.sha(path) for path in paths}
    pins.update({row["path"]: row["sha256"] for row in duration["authenticated_primary_sources"]})
    unit.require(unit.sha(field_path) == expected_sha256, "released field changed during timber consumption")
    return {"schema": "thin_bolted_timber_common_shaft_components/v1", "candidate": unit.CANDIDATE,
            "state_id": demand["state_id"], "case_id": demand["case_id"], "accessory_placement": demand["accessory_placement"],
            "parameters": demand["parameters"], "source_sha256": pins, "producer_source_sha256": demand["source_sha256"],
            "independent132body_common_shaft_audit": audit, "independent70shaft_cut_replay": cut_receipt,
            "independent_member_span_geometry": span_receipt,
            "actual82wood_bearing_wrenches": wood,
            "actual72steel_flange_wrenches": steel,
            "actual164wood_body_root_bearing_parameter_diagnostics": bearing_parameter_diagnostics(wood, layout),
            "own_direct_wood_capture_annulus_references": own_wood_washer_references(demand, packet),
            "simultaneous_existing_member_cut_witnesses": member_cuts,
            "conditional_duration_source": duration, "current70thread_windows": windows,
            "unequal_shared_shaft_yield_scope": {"symmetric_four_mode_resistance_inferred": False,
                "two_single_shear_values_added": False, "actual_general132body_shaft_field_used": True,
                "complete_adjusted_NDS_general_shaft_yield_resistance_n": None,
                "remaining": "ActualDr/Fyb, distributed nonlinear wood-bearing/moment yielding and complete geometry/fracture adjustments are not adopted."},
            "counts": {"actual_wood_bearing_hosts": 82, "actual_steel_flange_hosts": 72,
                       "physical_shafts": 70, "raw_radial_bearing_points": 308, "own_end_captures": 140,
                       "existing_member_sections_replayed": sum(r["existing_saved_cut_count_compared"] for r in member_cuts)},
            "CAD_query_executed": False, "native_solve_executed": False, "historical_force_or_acceptance_transferred": False,
            "all18_completion_gates_open": True, "complete_joint_acceptance": False, "release": unit.RELEASE,
            "limits": demand["limits"] + [
                "All own wood force/couples are independently reduced from distributed bearing and own captures; steel cut/port reduction is reused source-bound.",
                "NDSFe and patch pressure are conditional material diagnostics, not adjusted allowable patch stress or a common shaft yield rating.",
                "Every selected timber stress witness retains one complete same-state/same-cut vector; exact net centroid/inertia queries and shear/fracture/stability remain separate."]}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--field", type=Path, required=True)
    parser.add_argument("--field-sha256", required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    unit.require(not args.out.exists(), "preserve distinct common timber evidence")
    result = consume(args.field, args.field_sha256)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n")
    print(json.dumps({"path": str(args.out), "state_id": result["state_id"], "counts": result["counts"],
                      "release": result["release"]}, indent=2))


if __name__ == "__main__":
    main()
