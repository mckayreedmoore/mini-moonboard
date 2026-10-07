"""Consume one authenticated thin-frame elastic state using frozen timber inputs.

No CAD queries, geometry changes, native solves or historical demand transfer
occur here. References remain conditional components of the stated surrogate.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from collections import defaultdict
from pathlib import Path

from mini_moonboard.nds_2024_group_action import (
    SCHEMA_VERSION as GROUP_SCHEMA,
    canonical_group_record_sha256,
    evaluate_group_action_factor,
)
from scripts import thin_bolted_timber_resistance as unit
from scripts import thin_bolted_finished_support_audit as support_audit

ROOT = unit.ROOT
UNIT = unit.PACKET / "timber-bolt-resistance-v4.json"
UNIT_SHA = "5e78ac49a2db2050caf7ee7d2002d0ebf4f9a92496e857a0e2d652629bd0d848"
FRAME_PRODUCER = "scripts/thin_bolted_frame_mechanics.py"
FRAME_PRODUCER_SHA = "05cdf6897645fe7ee1b72b5b5125c04c68d758108f4860f995cef6aa1b676448"
NATIVE = unit.PACKET / "native-geometry-v4.json"
NATIVE_SHA = "cafdd983a41f2eee15647b28e60e5b2704354a4c5518d120e4c4342001994bb9"
CONTACT = unit.PACKET / "frame-contact-geometry-v4.json"
CONTACT_SHA = "e6c7ac4548b943bef4580b7c58efd67c11e29ed3335ae4036998a70c346986fc"
FLOOR_BASIS = "authenticated-finished-timber-horizontal-faces"
SUPPORT_AUDIT = "scripts/thin_bolted_finished_support_audit.py"
SUPPORT_AUDIT_SHA = "0a37e67ed20e3fd1eed8b8b4d0d12889df6fd9a6fb33d6f8f68a0c6768f5ada0"
ARITHMETIC_AUDIT = "scripts/thin_bolted_equilibrium_audit.py"
ARITHMETIC_AUDIT_SHA = "748f637b918bf9b7faca673cb2e723c8dbb8f98bc4a2d3fd5b12987c20980b84"
ASME_BODY_WINDOWS_IN = {(12.7, 76.2): (1.75, 1.36), (12.7, 127.): (3.75, 3.36),
                       (12.7, 203.2): (6.50, 6.12), (12.7, 215.9): (7.00, 6.62),
                       (9.525, 101.6): (3.00, 2.69), (9.525, 114.3): (3.50, 3.19)}
ASME_BODY_SOURCE = {"url": "https://www.wanhong-fastener.com/wp-content/uploads/2025/04/ASME-B18.2.1-2012.pdf",
                    "standard": "ASME B18.2.1-2012", "locators": "4.7 printed19; Table12 printed20-22/PDF29-31",
                    "provenance": "supplier-hosted primary standard text, independently browser-transcribed; original PDF byte SHA unavailable",
                    "product_conformance_and_delivered_transition_verified": False}
DURATION_CACHE = ROOT / "docs/wood-joints-mvp/hypotheses/upper-block-strength-2026-10-01/source-cache"
DURATION_PINS = {"chapter2-2024-awc.pdf": "6bb62f3560ab5bcdbed297cd03bba560f20882a638ee591c0c97013f7c075100",
                 "chapter11-2024-awc-20260911.pdf": "45a3d78de1a4fba573589be0fc776e37bd581e4cedec24e38d63856161092d33",
                 "appendix-2024-awc-20260911.pdf": "1fa2bcf52803b1bbed8ea30cf13551dd5f76c90bf110ac475b401f81d116ec31"}


def canonical_sha(value: object) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"),
                                     allow_nan=False).encode()).hexdigest()


def add(first, second):
    return [a + b for a, b in zip(first, second, strict=True)]


def scale(value, factor):
    return [factor * a for a in value]


def state_identity(field: dict) -> str:
    identity = {key: field[key] for key in
                ("case_id", "accessory_placement", "parameters", "geometry_cache_sha256")}
    return "thin-v4-" + canonical_sha(identity)[:24]


def read_unit() -> tuple[dict, dict, dict]:
    unit.require(unit.sha(UNIT) == UNIT_SHA, "frozen unit packet differs")
    packet = json.loads(UNIT.read_text())
    for relative, expected in packet["source_sha256"].items():
        unit.require(unit.sha(ROOT / relative) == expected, f"unit source differs: {relative}")
    unit.require(unit.sha(NATIVE) == NATIVE_SHA, "native geometry metadata differs")
    native = json.loads(NATIVE.read_text())
    layout, _, _, _ = unit.source_inputs()
    return packet, native, layout


def read_duration_sources() -> dict:
    """Authenticate reusable 2024 primary clauses without copying manuals."""
    bounds_path = DURATION_CACHE / "source-bounds.json"
    bounds = json.loads(bounds_path.read_text())
    entries = {row["cache_path"]: row for row in bounds["sources"]}
    sources = []
    for name, expected in DURATION_PINS.items():
        path, entry = DURATION_CACHE / name, entries[name]
        unit.require(unit.sha(path) == expected == entry["sha256"], "2024 duration source identity differs")
        unit.require(entry["official_url"].startswith(("https://awc.org/", "https://web-media.awc.org/")),
                     "duration source must be the recorded primary publisher")
        sources.append({"path": str(path.relative_to(ROOT)), "sha256": expected,
                        "official_url": entry["official_url"]})
    return {"source_metadata_path": str(bounds_path.relative_to(ROOT)),
            "source_metadata_sha256": unit.sha(bounds_path), "authenticated_primary_sources": sources,
            "locators": "NDS2024 §§2.3.2.1-.3/Table2.3.2 printed12-13; §§11.2.3/11.3.1-.2/Table11.3.1 printed71-72; AppendixB.1-.3 printed170-171",
            "scope": "Wood-controlled reference connection and axial timber component duration hypotheses; shortest cumulative duration and other adjustment factors remain unadopted.",
            "current2024_adjustment_clauses_verified": True, "actual_case_duration_adopted": False,
            "direct_metal_parts_Fc_perp_E_Emin_duration_increase": False,
            "connection_impact_CD2p0_permitted": False}


def internal_actions(field: dict) -> list[dict]:
    return [row for table in ("attachment_actions", "retained_bolt_actions", "panel_screw_actions", "contact_actions")
            for row in field[table]]


def free_moment(row: dict) -> list[float]:
    # These model couples are explicit free moments at the same action datum.
    # They are never reinterpreted as delivered bolt bending demands.
    value = row.get("moment_at_point_model_xyz_nmm", [0., 0., 0.])
    return unit.vector(value, "model free moment")


def authenticated_field_audit(field: dict) -> dict:
    """Reuse the released support/load/contact/wrench audit before consumption."""
    for relative, expected in ((SUPPORT_AUDIT, SUPPORT_AUDIT_SHA),
                               (ARITHMETIC_AUDIT, ARITHMETIC_AUDIT_SHA)):
        unit.require(unit.sha(ROOT / relative) == expected, f"frozen demand audit differs: {relative}")
    receipt = support_audit.audit_finished_state(field)
    unit.require(receipt["independent_finished_support_and_equilibrium_checks_pass"] is True,
                 "independent finished-support/equilibrium gate fails")
    # Bind the invoked shared gate as well as its independently authenticated
    # geometry, retained load basis, contact aliases and arithmetic dependencies.
    return {**receipt, "invoked_support_audit_sha256": SUPPORT_AUDIT_SHA,
            "invoked_arithmetic_audit_sha256": ARITHMETIC_AUDIT_SHA,
            "physical_demand_upper_bound_established": False}


def validate_field(field: dict, layout: dict, native: dict, packet: dict) -> dict:
    unit.require(field["candidate"] == unit.CANDIDATE, "foreign force-field candidate")
    unit.require(field.get("layout_report_sha256") == unit.LAYOUT_SHA, "force-field layout differs")
    unit.require(field["geometry_cache_sha256"] == NATIVE_SHA, "force-field geometry cache differs")
    unit.require(field["state_id"] == state_identity(field), "state identity does not bind case/accessory/all parameters")
    unit.require(field["source_sha256"].get(FRAME_PRODUCER) == FRAME_PRODUCER_SHA,
                 "force field does not bind released mechanics producer")
    for relative, expected in field["source_sha256"].items():
        unit.require(unit.sha(ROOT / relative) == expected, f"fresh field source differs: {relative}")
    unit.require(field["usable_conditional_actions"] is True, "conditional force field was not released for consumption")
    response = field["response"]
    unit.require(response["converged"] is True and response["physical_residual_uses_unmodified_laws"] is True,
                 "constitutive convergence/residual basis is unavailable")
    tol = response["generalized_residual_tolerance_n"]
    unit.require(0 < tol <= 1e-5 and response["gradient_inf_n"] < tol, "generalized residual criterion fails")
    unit.require(field["equilibrium_verification"]["all_body_and_global_checks_pass"] is True,
                 "mechanics all-body/global gate is open")
    unit.require(not any(field["release"].values()), "unexpected mechanics release flag")
    body_ids = {p["id"] for p in native["parts"] if p["kind"] in ("timber", "panel", "bracket")}
    unit.require(len(body_ids) == 62, "native62body census differs")
    axes = {a["id"]: a for a in layout["installed_axes"]}
    expected = {(a["id"], f["angle_id"], f["flange"], f["receiver"])
                for a in axes.values() for f in a["attachments"]}
    actual = set()
    for row in field["attachment_actions"]:
        identity = (row["axis_id"], row["angle_id"], row["flange"], row["receiver"])
        unit.require(identity not in actual and identity in expected, "duplicate/foreign flange witness")
        actual.add(identity)
        unit.require(row["first"] == row["receiver"] and row["second"] == row["angle_id"], "flange first/second body mismatch")
        unit.require(math.dist(row["force_on_first_xyz_n"], row["force_on_receiver_xyz_n"]) < 1e-8,
                     "flange receiver force differs from equilibrium force")
    unit.require(len(field["attachment_actions"]) == 72 and actual == expected, "exact72flange census differs")
    support = {r["axis_id"]: r for r in packet["finished_geometry_queries"]["physical_shaft_wood_support"]}
    expected_retained = {a["id"] for a in axes.values() if not a["attachments"]}
    seen = set()
    for row in field["retained_bolt_actions"]:
        unit.require(row["axis_id"] in expected_retained and row["axis_id"] not in seen, "duplicate/foreign retained witness")
        seen.add(row["axis_id"])
        axis = axes[row["axis_id"]]
        unit.require([row["first"], row["second"]] == axis["receivers"], "retained member order differs")
        point = unit.vector(row["point_xyz_mm"], "retained wood interface")
        delta = [p - a for p, a in zip(point, axis["point"], strict=True)]
        shaft = unit.unit(axis["direction"])
        t = unit.dot(delta, shaft)
        unit.require(math.hypot(*unit.cross(delta, shaft)) < 1e-5, "retained interface is off its physical shaft")
        intervals = support[axis["id"]]["member_intervals"]
        first = [r["interval_mm"] for r in intervals if r["member"] == row["first"]]
        second = [r["interval_mm"] for r in intervals if r["member"] == row["second"]]
        contacts = [a for interval in first for a in interval
                    if any(abs(a - b) < 1e-5 for other in second for b in other)]
        unit.require(any(abs(t - a) < 1e-5 for a in contacts), "retained force datum differs from actual member interface")
    unit.require(len(field["retained_bolt_actions"]) == 12 and seen == expected_retained, "exact12retained census differs")
    for table in ("attachment_actions", "retained_bolt_actions", "panel_screw_actions", "contact_actions", "floor_actions", "member_element_actions"):
        for row in field[table]:
            unit.require(row["state_id"] == field["state_id"], "action mixes an accessory/parameter state")
            if "case_id" in row:
                unit.require(row["case_id"] == field["case_id"]
                             and row["accessory_placement"] == field["accessory_placement"], "action case/accessory differs")
    return authenticated_field_audit(field)


def material_scenario(axis: dict, bearing_mm: float, root_fraction: float) -> dict:
    return {"scenario_id": f"generic45ksi_conditionalFe49p5ksi_rootfraction{root_fraction:g}",
            "source": "frozen timber unit packet conditional TR12/Eaton component inputs",
            "steel_Fe_psi": 49500., "bolt_Fyb_psi": 45000.,
            "full_body_diameter_in": axis["diameter_mm"] / 25.4,
            "thread_root_diameter_in": root_fraction * axis["diameter_mm"] / 25.4,
            "wood_thread_bearing_length_in": 0. if root_fraction == 1. else bearing_mm / 25.4,
            "steel_thread_bearing_length_in": 0., "steel_side_a_thread_bearing_length_in": 0.,
            "steel_side_b_thread_bearing_length_in": 0.}


def duration_component_sensitivity(reference_n: float, target_n: float, *,
                                   case_id: str | None, live_load_present: bool | None) -> dict:
    """Keep an arithmetic wood-connection duration hypothesis separate from Z'."""
    return {"case_id": case_id, "live_load_in_authenticated_case": live_load_present,
            "CD1_reference_n": reference_n, "CD1_same_state_component_ratio": target_n / reference_n,
            "conditional_CD1p6_reference_n": 1.6 * reference_n if live_load_present is True else None,
            "conditional_CD1p6_same_state_component_ratio": target_n / (1.6 * reference_n) if live_load_present is True else None,
            "current_case_shortest_cumulative_duration_adopted": False,
            "complete_adjusted_NDS_resistance_n": None,
            "permanent_only_case_and_CD0p9_comparison": None if live_load_present is not False else {
                "conditional_reference_n": .9 * reference_n, "same_state_component_ratio": target_n / (.9 * reference_n)},
            "duration_factor_is_not_a_direct_metal_part_or_washer_bearing_increase": True}


def signed_boundary_diagnostics(action: dict, receiver: dict, diameter_mm: float) -> dict:
    distances = receiver["sampled_minimum_distances_to_first_finished_boundary_mm"]
    end = action["grain_loaded_end"]
    edge = action["cross_grain_loaded_edge"]
    signed_end = None if end is None else distances["grain"][end]
    loaded_edge = None if edge is None else distances["cross_grain"][edge]
    def selected_face(kind, side):
        probes = receiver.get("boundary_probes", [])
        if side is None or not probes:
            return None
        probe = min(probes, key=lambda row: row[kind][side]["distance_mm"])
        return {"bearing_probe_point_xyz_mm": probe["point_xyz_mm"], **probe[kind][side]}
    return {"grain_loaded_end": end, "cross_grain_loaded_edge": edge,
            "signed_lateral_load_to_grain_degrees": action["load_to_grain_degrees"],
            "sampled_loaded_grain_boundary_face_witness": selected_face("grain", end),
            "sampled_loaded_cross_grain_boundary_face_witness": selected_face("cross_grain", edge),
            "sampled_signed_first_grain_boundary_mm": signed_end,
            "softwood_tension_end_component_diagnostic": None if signed_end is None else
                unit.end_geometry_factor(signed_end, diameter_mm, "softwood_parallel_tension"),
            "compression_end_component_diagnostic": None if signed_end is None else
                unit.end_geometry_factor(signed_end, diameter_mm, "parallel_compression"),
            "sampled_signed_first_cross_grain_boundary_mm": loaded_edge,
            "loaded_perpendicular_edge_4D_diagnostic_margin_mm": None if loaded_edge is None else loaded_edge - 4. * diameter_mm,
            "first_cross_grain_boundary_1p5D_margins_mm": {side: distances["cross_grain"][side] - 1.5 * diameter_mm
                                                          for side in ("negative", "positive")},
            "NDS_member_end_tension_compression_classification": None,
            "complete_Cdelta": None, "formal_end_edge_acceptance": False,
            "limits": "A first boundary may be an intersecting hole or service cut. Sampled square/oblique metadata is available in the unit packet; actual end category, oblique shear area, loaded group and continuous edge minimum are not inferred from a ray or force sign."}


def retained_reference(axis: dict, source: dict, receivers: dict, root_fraction: float,
                       live_load_present: bool | None = None) -> dict:
    first, second = [receivers[(axis["id"], member)] for member in axis["receivers"]]
    force = unit.vector(source["force_on_first_xyz_n"], "retained first-member force")
    actions = [unit.resolved_action(force, first["grain_axis_xyz"], axis["direction"]),
               unit.resolved_action(scale(force, -1.), second["grain_axis_xyz"], axis["direction"])]
    diameter = root_fraction * axis["diameter_mm"] / 25.4
    members = []
    for receiver, action in zip((first, second), actions, strict=True):
        members.append({"member": receiver["member"], **action,
                        "bearing_length_in": receiver["finished_full_wall_length_mm"] / 25.4,
                        "signed_boundary_diagnostics": signed_boundary_diagnostics(action, receiver, axis["diameter_mm"])})
    base = {"state_id": source["state_id"], "axis_id": axis["id"],
            "root_fraction_scenario": root_fraction, "effective_diameter_in": diameter,
            "generic_Fyb_scenario_psi": 45000., "members": members,
            "actual_material_contact_thread_window_adopted": False,
            "complete_connection_utilization": None}
    if actions[0]["lateral_n"] < 1e-10:
        return {**base, "status": "zero_lateral_action", "reference_n": None}
    for member in members:
        member["fe_theta_psi"] = unit.dfl_dowel_bearing_psi(diameter, member["load_to_grain_degrees"])
    reductions = unit._reduction_terms(diameter_in=diameter,
        nominal_diameter_in=axis["diameter_mm"] / 25.4,
        angle_max_degrees=max(action["load_to_grain_degrees"] for action in actions))
    modes = unit._single_shear_modes(members[0], members[1], diameter, 45000., reductions)
    mode_n = {mode: value * unit.N_PER_LBF for mode, value in modes.items()}
    reference = min(mode_n.values())
    target = actions[0]["lateral_n"]
    fixed_modes = {mode: mode_n[mode] for mode in ("Im", "Is", "II")}
    fixed_ceiling = min(fixed_modes.values())
    inversion = {"fixed_effective_diameter_in": diameter,
                 "fixed_member_Fe_theta_psi": [member["fe_theta_psi"] for member in members],
                 "fixed_mode_ceilings_n": fixed_modes,
                 "Fyb_independent_component_ceiling_n": fixed_ceiling,
                 "Fyb_independent_ceiling_governing_mode": min(fixed_modes, key=fixed_modes.get),
                 "target_same_state_lateral_n": target,
                 "actual_Fyb_or_complete_connection_utilization_adopted": False}
    if target > fixed_ceiling:
        inversion.update(status="unattainable_by_Fyb_alone", required_Fyb_psi=None)
    else:
        def reference_at_fyb(fyb):
            values = unit._single_shear_modes(members[0], members[1], diameter, fyb, reductions)
            return min(values.values()) * unit.N_PER_LBF

        low, high = 0., 45000.
        while reference_at_fyb(high) < target:
            high *= 2.
            unit.require(high < 1e12, "retained Fyb inversion exceeds numerical bracket")
        for _ in range(80):
            mid = .5 * (low + high)
            if reference_at_fyb(mid) < target:
                low = mid
            else:
                high = mid
        inversion.update(status="conditional_required_Fyb_for_fixed_other_inputs", required_Fyb_psi=high)
    return {**base, "status": "fresh_conditional_six_mode_component_reference",
            "mode_values_n": mode_n, "governing_mode": min(mode_n, key=mode_n.get),
            "reference_n": reference,
            "same_state_lateral_over_unadjusted_reference": target / reference,
            "duration_component_sensitivity": duration_component_sensitivity(reference, target,
                case_id=source.get("case_id"), live_load_present=live_load_present),
            "required_Fyb_for_this_unadjusted_component": inversion,
            "axial_capture_and_bending_response_established": False}


def standard_thread_window(axis: dict, receivers: dict, length_mm: float | None = None) -> dict:
    """Apply NDS quarter-thread exposure to every actual bearing member.

    The body and grip-gaging lengths are conditional product-standard bounds,
    including transition semantics; they are not measurements. Nominal washer
    thickness is explicit, so tolerance-extreme assembly fit remains separate.
    """
    length = axis["nominal_under_head_length_mm"] if length_mm is None else length_mm
    key = (axis["diameter_mm"], length)
    unit.require(key in ASME_BODY_WINDOWS_IN, "untranscribed standard body-window family")
    grip_gaging_max, body_min = [v * 25.4 for v in ASME_BODY_WINDOWS_IN[key]]
    washer = axis["hardware_scenario"]["washer_thickness_mm"]
    wood_offset = washer + axis["before_plate_mm"]
    members = []
    for member in axis["receivers"]:
        receiver = receivers[(axis["id"], member)]
        intervals = [[low + wood_offset, high + wood_offset]
                     for low, high in receiver["finished_full_wall_intervals_from_axis_point_mm"]]
        members.append({"member": member, "material": "wood", "underhead_bearing_intervals_mm": intervals})
    if axis["before_plate_mm"] > 0:
        members.append({"member": "near_steel_side", "material": "steel",
                        "underhead_bearing_intervals_mm": [[washer, wood_offset]]})
    if axis["after_plate_mm"] > 0:
        low = wood_offset + axis["grip_mm"]
        members.append({"member": "far_steel_side", "material": "steel",
                        "underhead_bearing_intervals_mm": [[low, low + axis["after_plate_mm"]]]})
    for member in members:
        intervals = member["underhead_bearing_intervals_mm"]
        bearing = sum(high - low for low, high in intervals)
        minimum_threads = sum(max(0., high - max(low, grip_gaging_max)) for low, high in intervals)
        maximum_threads = sum(max(0., high - max(low, body_min)) for low, high in intervals)
        member.update(bearing_length_mm=bearing, quarter_bearing_length_mm=bearing / 4.,
                      minimum_thread_bearing_from_Lgmax_mm=minimum_threads,
                      maximum_possible_thread_bearing_from_Lbmin_mm=maximum_threads,
                      fullD_exception_guaranteed_by_standard_window=maximum_threads <= bearing / 4. + 1e-6,
                      Dr_required_by_standard_window=minimum_threads > bearing / 4. + 1e-6)
    forced_root = any(member["Dr_required_by_standard_window"] for member in members)
    guaranteed_body = all(member["fullD_exception_guaranteed_by_standard_window"] for member in members)
    return {"axis_id": axis["id"], "nominal_CAD_length_mm": axis["nominal_under_head_length_mm"],
            "length_scenario_mm": length, "geometry_or_hardware_changed": False,
            "washer_thickness_scenario_mm": washer,
            "standard_Lgmax_mm": grip_gaging_max, "standard_Lbmin_mm": body_min,
            "all_bearing_members": members,
            "NDS_diameter_window_scenario": "Dr_required" if forced_root else "fullD_exception_within_standard_window" if guaranteed_body else "delivered_transition_dependent_D_or_Dr",
            "actual_NDS_diameter_or_material_adopted": False,
            "limits": "NDS12.3.7 quarter-thread limit applies independently to every wood and steel member. Nominal washers and a conforming ASME2012 product hypothesis are explicit; actual root/body diameters, runout, tolerance-extreme stacks, nut engagement and delivered conformance remain separate."}


def member_cut_wrench(grain, low: float, high: float, cut_point, center, gravity_force,
                      point_actions: list[tuple[list, list, list]]) -> dict:
    """Recover one same-state cut, including affine member selfweight.

    This is an equilibrium calculation on the lower-grain portion. It does not
    repeat a CAD section or combine independently located wrench extrema.
    """
    s = unit.dot(grain, cut_point)
    length, mid = high - low, .5 * (high + low)
    unit.require(length > 0 and low - 1e-5 <= s <= high + 1e-5, "cut lies outside recovered beam span")
    center_s = unit.dot(grain, center)
    beta = 12. * (center_s - mid) / length**2
    unit.require(min(1. + beta * (low - mid), 1. + beta * (high - mid)) >= -1e-10,
                 "affine selfweight becomes negative")
    fraction = ((s - low) + .5 * beta * ((s - mid)**2 - (low - mid)**2)) / length
    first_moment = (.5 * (s**2 - low**2) + beta * ((s**3 - low**3) / 3. - .5 * mid * (s**2 - low**2))) / length
    off_axis = [c - g * center_s for c, g in zip(center, grain, strict=True)]
    arm_integral = add(scale([a - c for a, c in zip(off_axis, cut_point, strict=True)], fraction), scale(grain, first_moment))
    force = scale(gravity_force, fraction)
    moment = unit.cross(arm_integral, gravity_force)
    for point, action, free in point_actions:
        if unit.dot(point, grain) < s:
            force = add(force, action)
            moment = add(moment, add(unit.cross([p - c for p, c in zip(point, cut_point, strict=True)], action), free))
    return {"cut_point_xyz_mm": cut_point, "cut_grain_station_mm": s,
            "force_on_lower_portion_xyz_n": scale(force, -1.),
            "moment_on_lower_portion_about_cut_xyz_nmm": scale(moment, -1.),
            "axial_tension_positive_n": -unit.dot(force, grain),
            "affine_selfweight_mass_and_centroid_retained": True}


def net_section_checks(field: dict, full_geometry: dict) -> list[dict]:
    by_body = defaultdict(list)
    for row in internal_actions(field):
        for body, sign in ((row["first"], 1.), (row["second"], -1.)):
            by_body[body].append((row["point_xyz_mm"], scale(row["force_on_first_xyz_n"], sign), scale(free_moment(row), sign)))
    for row in field["floor_actions"]:
        by_body[row["first"]].append((row["point_xyz_mm"], row["force_on_first_xyz_n"], free_moment(row)))
    gravity = {}
    for load in field["body_applied_loads"]:
        if load["id"].startswith("self-weight/"):
            unit.require(load["body"] not in gravity, "duplicate selfweight body")
            gravity[load["body"]] = (load["point_xyz_mm"], load["force_xyz_n"])
        else:
            by_body[load["body"]].append((load["point_xyz_mm"], load["force_xyz_n"], load.get("moment_xyz_nmm", [0., 0., 0.])))
    elements = defaultdict(list)
    for row in field["member_element_actions"]:
        elements[row["member"]].append(row)
    results = []
    for geometry in full_geometry["finished_member_sections"]:
        name, grain = geometry["member"], geometry["grain_axis_xyz"]
        unit.require(name in elements and name in gravity, "member load/span source missing")
        rows = elements[name]
        for row in rows:
            unit.require(math.dist(unit.unit(row["basis_grain_u_v_xyz"][0]), grain) < 1e-8,
                         "member action grain differs from unit geometry")
        points = [row[key] for row in rows for key in ("start_xyz_mm", "end_xyz_mm")]
        start = min(points, key=lambda point: unit.dot(grain, point))
        low, high = min(unit.dot(grain, p) for p in points), max(unit.dot(grain, p) for p in points)
        center, gravity_force = gravity[name]
        samples = []
        for section in geometry["sampled_sections"]:
            s = section["station_global_grain_projection_mm"]
            if not low - 1e-5 <= s <= high + 1e-5:
                continue
            cut = add(start, scale(grain, s - low))
            wrench = member_cut_wrench(grain, low, high, cut, center, gravity_force, by_body[name])
            area = section["finished_area_mm2"]
            axial = wrench["axial_tension_positive_n"]
            ft = 575. * unit.N_PER_LBF / 25.4**2
            fc = 1350. * unit.N_PER_LBF / 25.4**2
            samples.append({**wrench, "finished_area_mm2": area,
                            "Ft_base_average_axial_reference_n": area * ft,
                            "Fc_base_average_axial_reference_n": area * fc,
                            "positive_tension_over_base_area_reference": max(axial, 0.) / (area * ft) if area else None,
                            "compression_over_base_area_reference": max(-axial, 0.) / (area * fc) if area else None,
                            "bending_torsion_shear_interaction_or_column_stability": None})
        unit.require(samples, "no existing finished sections intersect beam action span")
        tension = max(samples, key=lambda row: row["positive_tension_over_base_area_reference"] or 0.)
        compression = max(samples, key=lambda row: row["compression_over_base_area_reference"] or 0.)
        results.append({"member": name, "existing_finished_section_samples_compared": len(samples),
                        "maximum_tension_area_component_witness": tension,
                        "maximum_compression_area_component_witness": compression,
                        "continuous_minimum_section_or_maximum_stress_proved": False,
                        "complete_net_section_utilization": None,
                        "limits": "CD=CM=Ct=1 and no size increase. Same-state cut actions and actual sampled area support average axial component diagnostics only; bending and local stress/fracture are not qualified."})
    return results


def connected_duty_group_diagnostics(field: dict, layout: dict, receivers: dict,
                                     full_geometry: dict, field_sha: str) -> list[dict]:
    """Keep actual duties/physical shafts and signed row references distinct.

    Duty ownership is explicit in the frozen layout. It is not evidence that
    separate formed fittings form the uniform continuous metal side member
    required by a group-action model, nor proof of a fracture surface.
    """
    axes = {a["id"]: a for a in layout["installed_axes"]}
    rays = {r["axis_id"]: r for r in layout["grain_ray_end_diagnostic"]}
    grouped = defaultdict(list)
    for row in field["attachment_actions"]:
        axis = axes[row["axis_id"]]
        fitting = next(a for a in axis["attachments"] if a["angle_id"] == row["angle_id"]
                       and a["flange"] == row["flange"])
        grouped[(fitting["duty_id"], row["flange"], row["receiver"])].append(row)
    sections = {r["member"]: r for r in full_geometry["finished_member_sections"]}
    output = []
    for (duty, flange, member), sources in sorted(grouped.items()):
        physical = defaultdict(list)
        for row in sources:
            physical[row["axis_id"]].append(row)
        ids = sorted(physical)
        first_receiver = receivers[(ids[0], member)]
        grain, shaft = first_receiver["grain_axis_xyz"], axes[ids[0]]["direction"]
        resultant = [sum(row["force_on_receiver_xyz_n"][i] for row in sources) for i in range(3)]
        resolved = unit.resolved_action(resultant, grain, shaft)
        positions, row_inputs = [], []
        for axis_id in ids:
            axis, receiver = axes[axis_id], receivers[(axis_id, member)]
            intervals = receiver["finished_full_wall_intervals_from_axis_point_mm"]
            mid = sum((high**2 - low**2) / 2. for low, high in intervals) / receiver["finished_full_wall_length_mm"]
            positions.append(add(axis["point"], scale(unit.unit(axis["direction"]), mid)))
            force = [sum(row["force_on_receiver_xyz_n"][i] for row in physical[axis_id]) for i in range(3)]
            action = unit.resolved_action(force, grain, axis["direction"])
            side = action["grain_loaded_end"]
            raw_end = None if side is None else rays[axis_id]["grain_ray_end_distances_mm"][0 if side == "negative" else 1]
            row_inputs.append({"axis_id": axis_id, **action,
                               "raw_signed_outer_grain_end_ray_mm": raw_end,
                               "bearing_length_mm": receiver["finished_full_wall_length_mm"],
                               "raw_one_bolt_parallel_row_reference_n": None if raw_end is None else
                                   unit.dfl_parallel_row_tear_out_reference_lbf(
                                       receiver["finished_full_wall_length_mm"] / 25.4, 1, raw_end / 25.4) * unit.N_PER_LBF,
                               "finished_connected_fracture_reference_n": None})
        row_record = {"state_id": field["state_id"], "duty_id": duty, "flange": flange,
                      "member": member, "physical_axis_ids": ids,
                      "physical_fastener_count": len(ids), "attachment_count": len(sources),
                      "same_state_force_on_member_xyz_n": resultant, "resolved_resultant": resolved,
                      "signed_physical_axis_components": row_inputs,
                      "actual_Cg": None, "complete_group_reference_n": None,
                      "capacity_or_pass_claim": False}
        if len(ids) == 2:
            delta = [b - a for a, b in zip(*positions, strict=True)]
            pitch = abs(unit.dot(delta, grain))
            q = unit.unit(unit.cross(grain, unit.unit(shaft)))
            cross_pitch = abs(unit.dot(delta, q))
            same_grain_row = cross_pitch < 1e-5
            d = max(axes[axis_id]["diameter_mm"] for axis_id in ids)
            same_end = row_inputs[0]["grain_loaded_end"] is not None and row_inputs[0]["grain_loaded_end"] == row_inputs[1]["grain_loaded_end"]
            row_record["actual_projected_spacing"] = {"grain_mm": pitch, "cross_grain_mm": cross_pitch,
                "same_grain_row": same_grain_row, "same_signed_loaded_end": same_end,
                "3D_minimum_same_row_margin_mm": pitch - 3. * d if same_grain_row else None,
                "4D_full_parallel_same_row_margin_mm": pitch - 4. * d if same_grain_row else None}
            row_record["conditional_raw_two_bolt_row_reference_n"] = (
                unit.dfl_parallel_row_tear_out_reference_lbf(
                    min(row["bearing_length_mm"] for row in row_inputs) / 25.4, 2,
                    min(row["raw_signed_outer_grain_end_ray_mm"] for row in row_inputs) / 25.4,
                    pitch / 25.4) * unit.N_PER_LBF
                if same_grain_row and same_end and pitch > 1e-6 else None)
            side_id = "+".join(sorted({row["angle_id"] for row in sources}))
            bindings = {"geometry": {"source_id": "reviewed-v4-layout", "sha256": unit.LAYOUT_SHA},
                        "member_sections": {"source_id": "frozen-unit-finished-sections", "sha256": UNIT_SHA,
                                            "main_member_id": member, "side_member_ids": [side_id], "shear_planes": 1},
                        "fastener_product": {"source_id": "explicit-generic45ksi-unit-scenario", "sha256": UNIT_SHA},
                        "load_cases": {"source_id": field["state_id"], "sha256": field_sha}}
            gross_area = max(r["raw_area_mm2"] for r in sections[member]["sampled_sections"]) / 25.4**2
            payload = {"schema": GROUP_SCHEMA, "candidate_id": unit.CANDIDATE,
                       "revision_id": "reviewed-v4", "group_id": f"{duty}/{flange}", "scenario_id": field["state_id"],
                       "source_bindings": bindings,
                       "group_geometry": {"row_axis_xyz": grain, "fasteners": [
                           {"fastener_id": axis_id, "type": "dowel", "center_in": scale(point, 1. / 25.4),
                            "nominal_diameter_in": axes[axis_id]["diameter_mm"] / 25.4}
                           for axis_id, point in zip(ids, positions, strict=True)]},
                       "load_case": {"case_id": field["case_id"], "lateral_resultant_xyz_lbf": scale(resolved["lateral_xyz_n"], 1. / unit.N_PER_LBF)},
                       "members": {"main": {"member_id": member, "material": "wood", "elastic_modulus_psi": 1600000.,
                                             "grain_axis_xyz": grain, "gross_section_area_in2": gross_area},
                                   "side_members": [{"member_id": side_id, "material": "steel", "elastic_modulus_psi": 29000000.}],
                                   "shear_planes": 1}}
            row_record["maintained_group_method_applicability"] = evaluate_group_action_factor(
                payload, expected_bindings=bindings, expected_payload_sha256=canonical_group_record_sha256(payload))
            row_record["group_source_binding_scope"] = "consumer-verified frozen geometry/unit/action inputs; not an independently adopted fastener product or continuous metal side member"
        else:
            row_record["maintained_group_method_applicability"] = {"status": "one_physical_fastener_group_factor_not_invoked", "cg": None}
        row_record["limits"] = "Raw outer-end row references omit actual finished shear/tension fracture surfaces, local bore/cut interaction, oblique load applicability and adjustments. Coincident opposed flange attachments count as one shaft. Separate fittings are not silently merged into one continuous steel group side member."
        output.append(row_record)
    return output


def axial_interface_diagnostics(field: dict, layout: dict, packet: dict) -> list[dict]:
    """Report model axis components beside separate ideal annulus references.

    The actual shaft/head/nut/washer load path is unresolved, especially where
    two ports share one physical shaft or a retained bilateral spring carries
    compression. No model component is asserted to be a physical washer load.
    """
    axes = {a["id"]: a for a in layout["installed_axes"]}
    actions = defaultdict(list)
    for row in field["attachment_actions"]:
        shaft = unit.unit(axes[row["axis_id"]]["direction"])
        actions[row["axis_id"]].append({"kind": "flange_port", "angle_id": row["angle_id"],
            "flange": row["flange"], "model_signed_receiver_axis_component_n": unit.dot(row["force_on_receiver_xyz_n"], shaft)})
    for row in field["retained_bolt_actions"]:
        shaft = unit.unit(axes[row["axis_id"]]["direction"])
        actions[row["axis_id"]].append({"kind": "retained_bilateral_port", "first": row["first"],
            "second": row["second"], "model_signed_first_member_axis_component_n": unit.dot(row["force_on_first_xyz_n"], shaft)})
    rows = []
    for washer in packet["washer_wood_interface_references"]:
        model = actions[washer["axis_id"]]
        unique_component = (next(value for key, value in model[0].items() if key.startswith("model_signed"))
                            if len(model) == 1 else None)
        reference = washer["ideal_full_contact_wood_annulus_reference_n"]
        rows.append({"state_id": field["state_id"], "axis_id": washer["axis_id"], "role": washer["role"],
            "support_material": washer["support_material"], "same_state_model_axis_components": model,
            "ideal_full_contact_wood_annulus_reference_n": reference,
            "absolute_single_port_component_over_ideal_annulus_diagnostic":
                abs(unique_component) / reference if unique_component is not None and reference is not None else None,
            "actual_washer_force_or_bolt_tension_n": None,
            "complete_axial_interface_reference_n": None,
            "duration_increase_applied_to_Fc_perp": False,
            "limits": "One model axis component is only a diagnostic beside ideal Fc-perp annulus bearing. Head/nut/thread/tension, washer spreading, formed plate contact, simultaneous lateral action and local wood fracture remain separate. Shared ports are not summed into one physical tension."})
    return rows


def build_report(field_path: Path, expected_sha256: str) -> dict:
    unit.require(unit.sha(field_path) == expected_sha256, "force field differs from parent-released immutable file")
    packet, native, layout = read_unit()
    duration_sources = read_duration_sources()
    field = json.loads(field_path.read_text())
    closure = validate_field(field, layout, native, packet)
    live_load_present = any(row["id"].startswith("climber/") for row in field["body_applied_loads"])
    detail = packet["reproducible_detail_artifact"]
    detail_path = ROOT / detail["path"]
    unit.require(unit.sha(detail_path) == detail["sha256"], "full existing geometry detail differs")
    full = json.loads(detail_path.read_text())["finished_geometry_queries"]
    receivers = {(r["axis_id"], r["member"]): r for r in full["receiver_boundary_geometry"]}
    axes = {a["id"]: a for a in layout["installed_axes"]}
    scenarios, attachments, shared = [], [], []
    for fraction in (1., .8):
        materials = {axis["id"]: material_scenario(axis,
            receivers[(axis["id"], axis["receivers"][0])]["finished_full_wall_length_mm"], fraction)
            for axis in axes.values() if axis["attachments"]}
        witnesses = unit.compare_actions(layout, field, materials)
        for witness in witnesses:
            axis = axes[witness["axis_id"]]
            receiver = receivers[(axis["id"], witness["receiver"])]
            witness["root_fraction_scenario"] = fraction
            witness["force_field_classification"] = "source_verified_same_state_conditional_elastic_surrogate"
            witness["conditional_model_closure_and_finished_support_validated"] = True
            witness["physical_strength_demand_bounds_established"] = False
            window = standard_thread_window(axis, receivers)["NDS_diameter_window_scenario"]
            witness["conditional_product_standard_thread_window"] = window
            witness["reference_diameter_applicability"] = (
                "explicit_0p8D_root_sensitivity_actual_Dr_unavailable" if fraction == .8 else
                "fullD_counterfactual_under_this_product_standard_window" if window == "Dr_required" else
                "fullD_delivered_transition_input_required" if window == "delivered_transition_dependent_D_or_Dr" else
                "fullD_conditional_product_standard_window_exception")
            witness["signed_finished_boundary_diagnostics"] = signed_boundary_diagnostics(witness, receiver, axis["diameter_mm"])
            if len(axis["attachments"]) == 1 and witness["lateral_n"] > 1e-10:
                plane = dict(axis, grip_mm=receiver["finished_full_wall_length_mm"])
                witness["required_Fyb_for_this_unadjusted_component"] = unit.required_fyb_for_single_shear(
                    plane, witness, materials[axis["id"]], witness["lateral_n"])
                witness["duration_component_sensitivity"] = duration_component_sensitivity(
                    witness["reference"]["single_fastener_reference_n"], witness["lateral_n"],
                    case_id=field["case_id"], live_load_present=live_load_present)
            attachments.append(witness)
        for row in unit.compare_shared_axes(layout, witnesses, materials):
            row["root_fraction_scenario"] = fraction
            row["conditional_product_standard_thread_window"] = standard_thread_window(
                axes[row["axis_id"]], receivers)["NDS_diameter_window_scenario"]
            shared.append(row)
        scenarios.append({"root_fraction": fraction, "Fyb_psi": 45000., "conditional_Fe_psi": 49500.,
                          "actual_material_or_thread_window_adopted": False})
    retained = [retained_reference(axes[source["axis_id"]], source, receivers, fraction, live_load_present)
                for source in field["retained_bolt_actions"] for fraction in (1., .8)]
    for row in retained:
        row["conditional_product_standard_thread_window"] = standard_thread_window(
            axes[row["axis_id"]], receivers)["NDS_diameter_window_scenario"]
    sources = {str(p.resolve().relative_to(ROOT)): unit.sha(p) for p in
               (field_path, UNIT, NATIVE, CONTACT, detail_path, Path(__file__),
                ROOT / FRAME_PRODUCER, ROOT / SUPPORT_AUDIT, ROOT / ARITHMETIC_AUDIT,
                ROOT / "mini_moonboard/nds_2024_group_action.py")}
    sources.update({row["path"]: row["sha256"] for row in duration_sources["authenticated_primary_sources"]})
    sources[duration_sources["source_metadata_path"]] = duration_sources["source_metadata_sha256"]
    return {"schema": "thin_bolted_timber_fresh_state_components/v1", "candidate": unit.CANDIDATE,
            "layout_report_sha256": unit.LAYOUT_SHA, "state_id": field["state_id"],
            "case_id": field["case_id"], "accessory_placement": field["accessory_placement"],
            "parameters": field["parameters"], "source_sha256": sources,
            "conditional_duration_sensitivity_source": duration_sources,
            "conditional_field_validation": closure, "material_scenarios": scenarios,
            "signed_flange_component_checks": attachments, "shared_physical_shaft_checks": shared,
            "retained_two_member_checks": retained,
            "product_standard_thread_windows": {"source": ASME_BODY_SOURCE,
                "current70nominal_length_scenarios": [standard_thread_window(axis, receivers) for axis in axes.values()],
                "original_four_8p5inch_length_proposal_scenarios": [standard_thread_window(axis, receivers, 215.9)
                    for axis in axes.values() if not axis["attachments"] and axis["diameter_mm"] == 12.7]},
            "connected_duty_group_diagnostics": connected_duty_group_diagnostics(field, layout, receivers, full, expected_sha256),
            "same_state_axial_interface_diagnostics": axial_interface_diagnostics(field, layout, packet),
            "finished_net_section_average_axial_checks": net_section_checks(field, full),
            "counts": {"same_state_flange_actions": 72, "same_state_retained_actions": 12,
                       "flange_body_root_checks": len(attachments), "shared_body_root_checks": len(shared),
                       "retained_body_root_checks": len(retained)},
            "group_action": {"Cg": None, "reason": "Actual steel/oblique connected patterns require scope classification; no blanket group factor is credited."},
            "complete_joint_acceptance": False, "all18_completion_gates_open": True,
            "physical_demand_upper_bound_established": False, "CAD_queries_repeated": False,
            "native_solve_executed": False, "release": unit.RELEASE,
            "limits": field["limits"] + [
                "Body/root references are unadjusted components under explicit generic45ksi and conditionalFe49.5ksi assumptions.",
                "Free flange moments are not assigned as physical bolt bending; unequal common shafts remain outside the symmetric method.",
                "Signed first-boundary diagnostics do not classify NDS end/edge applicability or oblique failure areas.",
                "Group action, connected row/group fracture, splitting and complete axial/contact interfaces remain separate."]}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--field", type=Path, required=True)
    parser.add_argument("--field-sha256", required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    unit.require(not args.out.exists(), "preserve distinct frozen fresh-state evidence")
    report = build_report(args.field, args.field_sha256)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n")
    print(json.dumps({"path": str(args.out), "state_id": report["state_id"], "counts": report["counts"],
                      "release": report["release"]}, indent=2))


if __name__ == "__main__":
    main()
