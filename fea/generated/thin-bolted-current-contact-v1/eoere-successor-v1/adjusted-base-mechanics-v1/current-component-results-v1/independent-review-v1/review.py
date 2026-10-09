"""Independently check frozen current component outputs using saved data only.

This stdlib-only reviewer does not import or execute a producer, reducer,
admission gate, CAD library, panel spatial evaluator or solver. Numerical field
admission is authenticated and relied upon, not repeated. Scalar expressions
are checked separately against the pinned equations. Gross member checks cover
the two reported witnesses, not a second search for their sampled extrema.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import math
import re
import sys
from collections import defaultdict
from decimal import Decimal, localcontext
from functools import cache
from pathlib import Path

OWN = Path(__file__).resolve()
ROOT = OWN.parents[7]
MECH = OWN.parents[2]
BASE = MECH.parent
DOC = ROOT / "docs/wood-joints-mvp/hypotheses/hl35-candidate/thin-frame-comparison/eoere-successor-v1"
GEOMETRY = DOC / "occupied-extended-cleats-v1.json"
DESCRIPTORS = MECH / "current-source-observations-v1/attempt01.json"
INPUTS = MECH / "current-inputs-v1/attempt01/inputs.json"
CONSUMER = MECH / "current-component-bridge-v1/consumer-v1/consume.py"
GATE = MECH / "current-force-bridge-v1/review-fix-v2/bridge.py"
CONSUMER_SHA = "f11175782c7b29abbdfbcbf5fbad63f919596bc6a613b4c7a5b65acc1027bad9"
GATE_SHA = "4916532168ba05268e164b28bb634743013b4aa7e062b7f9d345ecfafb954643"
FIXED = {
    GEOMETRY: "01ba30abe20c2efec136374b8d9a74a098a19929be3cc784b5ebcf7608e62a2d",
    DESCRIPTORS: "0f7e95f0dabfb5f0b5d63f8ef7d78e3c52c07672b4f482a89a89496eec703de7",
    INPUTS: "f0c55ac1d67650eec2de0cedfe4ec383d5b2a04253fbf10c9db9df9251711baa",
    CONSUMER: CONSUMER_SHA,
    GATE: GATE_SHA,
}
FIRST_THREE = {
    "a12-forward": (
        "5b4e4e2a467a9593bcc8b25687d4d2547aad2b7cb99b2b80624df531d40a81a6",
        "a6061668878537da052571075c3ede10ab4236f9734eea5be0176c647688f4bb",
        "f15357cfc083a50446eec61550900fd44fdab0198a13e2c06a252bd25bfbd2b7"),
    "a12-rear": (
        "e20c1fbfe688183bc748a991781bad5b0022435368061c8eb183906b5acd40b2",
        "9d0e12d3a3b953f037ce3570b9412e0cef786a699779cf596b791c6bc3ee7685",
        "93db5b0bfbd3587e48d77caeba62f50a3df5b98431a586fe2f346c387daa527b"),
    "a12-left": (
        "b6d40cb2b2253ae9c461c7f01070a7dd8b35011c0dd1d9972b8e800630e93728",
        "44e762a58d0077e6e6a812cf40a265bf1f52714bd6c8f8ebd773fde8d3a141d0",
        "010719584f83ea389e6a41d82aafce168ce8f74cafeb0498c20de8e721eed77a"),
}
CASES = (*FIRST_THREE, "k12-right", "k12-rear", "a1-rear")
RELEASE = {key: False for key in (
    "candidate_accepted", "capacity_established", "climbing_released",
    "complete_joint_acceptance", "fabrication_released", "structural_released")}
METHODS = (
    BASE / "component-method-v1/assessment.py",
    BASE / "component-method-v1/gross_members.py",
    BASE / "raised-rail-components-v1/comparisons.py",
    BASE / "steel-shaft-comparison-v1/comparison.py",
    ROOT / "scripts/thin_bolted_steel_resistance.py",
    ROOT / "scripts/thin_bolted_flange_torsion.py",
    ROOT / "scripts/thin_bolted_panel_coupled.py",
    ROOT / "scripts/thin_bolted_panel_mechanics.py",
    ROOT / "scripts/thin_bolted_timber_common_shaft_checks.py",
    ROOT / "scripts/thin_bolted_timber_demand_checks.py",
    ROOT / "fea/reinforced_timber_resistance.py",
    ROOT / "docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/upper-corner-screw-layout/panel-method-correction.py",
    ROOT / "docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/member-stability-attempt01/all-two-receiver/producer.py.snapshot",
)
N_PER_LBF = 4.4482216152605


def require(ok, label):
    if not ok:
        raise ValueError(label)


def relative(path):
    path = Path(path).resolve()
    return str(path.relative_to(ROOT)) if path.is_relative_to(ROOT) else str(path)


def sha(path):
    value = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            value.update(block)
    return value.hexdigest()


def canonical(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()).hexdigest()


def merge(pins, extra):
    for path, digest in extra.items():
        require(path not in pins or pins[path] == digest, "conflicting source binding: " + path)
        require(re.fullmatch(r"[0-9a-f]{64}", digest) is not None, "invalid SHA: " + path)
        pins[path] = digest


def verify(pins):
    for path, digest in pins.items():
        require(sha(ROOT / path) == digest, "source bytes differ: " + path)


def finite(value):
    if isinstance(value, float):
        require(math.isfinite(value), "nonfinite saved number")
    elif isinstance(value, list):
        for item in value:
            finite(item)
    elif isinstance(value, dict):
        for item in value.values():
            finite(item)


def read(path, digest):
    raw = path.read_bytes()
    require(hashlib.sha256(raw).hexdigest() == digest, "frozen target differs: " + relative(path))
    value = json.loads(raw, parse_constant=lambda _: (_ for _ in ()).throw(ValueError("nonfinite JSON constant")))
    finite(value)
    return value


def indexed(rows, key):
    result = {row[key]: row for row in rows}
    require(len(result) == len(rows), "duplicate saved identity: " + key)
    return result


def dot(a, b):
    return math.fsum(x * y for x, y in zip(a, b, strict=True))


def add(a, b):
    return [x + y for x, y in zip(a, b, strict=True)]


def sub(a, b):
    return [x - y for x, y in zip(a, b, strict=True)]


def scale(a, factor):
    return [x * factor for x in a]


def cross(a, b):
    return [a[1]*b[2]-a[2]*b[1], a[2]*b[0]-a[0]*b[2], a[0]*b[1]-a[1]*b[0]]


def matvec(rows, value):
    return [dot(row, value) for row in rows]


def columns(rows):
    return list(zip(*rows, strict=True))


class Comparison:
    def __init__(self):
        self.count = 0
        self.errors = defaultdict(float)

    def number(self, actual, expected, label, *, atol=2e-9, rtol=2e-11):
        require(not isinstance(actual, bool) and isinstance(actual, (float, int)) and math.isfinite(actual), label + ": finite scalar required")
        expected = float(expected)
        require(math.isfinite(expected), label + ": finite independent scalar required")
        error = abs(actual - expected)
        require(error <= atol + rtol * max(abs(actual), abs(expected)), label + ": independent scalar differs")
        self.errors[label.split("/")[0]] = max(self.errors[label.split("/")[0]], error)
        self.count += 1

    def vector(self, actual, expected, label, **kwargs):
        require(len(actual) == len(expected), label + ": vector size differs")
        for a, b in zip(actual, expected, strict=True):
            self.number(a, b, label, **kwargs)


def same_state(field, row):
    require(all(row[key] == field[key] for key in ("state_id", "case_id", "accessory_placement")), "mixed state/case/accessory identity")


def boundaries(report):
    require(report["release"] == RELEASE and report["complete_joint_resistance"] is None, "conditional null/release boundary changed")
    reductions = report["component_reductions"]
    require(reductions["complete_wood_bolt_yield_end_edge_Cdelta_group_splitting_resistance"] is None, "complete wood/group resistance invented")
    require(all(row["complete_group_heel_hole_prying_or_corner_resistance"] is None for row in reductions["angle_duties"]), "complete angle resistance invented")
    require(all(row["complete_corner_splitting_group_or_bearing_resistance"] is None for row in reductions["exterior_cleat_corners"]), "complete cleat resistance invented")


def check_identity(report, field, admission, case, geometry, descriptors, inputs):
    boundaries(report)
    require(report["schema"] == "eoere_extended_cleat_same_state_conditional_component_receipt/v1", "current component schema required")
    require(field["schema"] == "eoere_extended_cleat_fixed_floor_candidate/v1" and field["release"] == RELEASE and field["response"]["converged"] is True, "current unreleased converged field required")
    require(admission["schema"] == "eoere_extended_cleat_fixed_floor_independent_field_admission/v1" and admission["current_extended_cleat_equilibrium_and_recovery_pass"] is True, "completed own numerical admission required")
    same_state(field, report)
    same_state(field, admission)
    require(field["case_id"] == case and field["accessory_placement"] == "retained-original-top-hold", "current case/accessory required")
    require(admission["release"] == RELEASE and admission["admission_source_sha256"] == report["fresh_gate_sha256"] == GATE_SHA, "own corrected admission gate required")
    require(admission["first_order_physical_applicability_established"] is False and admission["physical_demand_bounds_established"] is False, "numerical admission must not imply physical demand bounds")
    require(admission["input_canonical_sha256"] == canonical(field), "admission canonical field differs")
    for table, digest in admission["table_canonical_sha256"].items():
        require(canonical(field[table]) == digest, "admitted action table differs: " + table)
    source = field["source_inputs"]
    selection = field["source_case_selection"]
    chosen = next(row for row in inputs["cases"] if row["case_id"] == case)
    expected = {**inputs, "case": chosen}
    require(source == expected and source["optional_2026_extra"] is False, "only own current case selection may differ from frozen OFF inputs")
    require(selection["raw_input_canonical_sha256"] == canonical(inputs) and selection["selected_input_canonical_sha256"] == canonical(source), "raw/selected current input binding differs")
    require(report["source_inputs_canonical_sha256"] == canonical(source), "component source input binding differs")
    require(report["current_geometry"] == source["geometry"]["report"] == {"path": relative(GEOMETRY), "sha256": FIXED[GEOMETRY]}, "exact current geometry required")
    require(report["current_saved_descriptors"] == source["geometry"]["cached_source_export"] == {"path": relative(DESCRIPTORS), "sha256": FIXED[DESCRIPTORS]}, "exact current descriptor source required")
    axes = indexed(geometry["axes"], "id")
    shafts = indexed(source["shafts"], "axis_id")
    require(len(axes) == len(shafts) == 100 and set(axes) == set(shafts), "all current 100 axes required")
    require(all(row["source_axis"] == axes[key] for key, row in shafts.items()) and source["shafts"] == descriptors["shafts"], "current axis/descriptor identity differs")
    require(len(source["hillman_rows"]) == 66 and [r["source_screw_descriptor"] for r in source["hillman_rows"]] == geometry["screw_axes"] and source["hillman_rows"] == descriptors["hillman_rows"], "current 66 Hillman axes required")
    require(source["timber_rows"] == descriptors["raw_gross_timber_rows"] and len(source["timber_rows"]) == 22, "current 22 gross timber rows required")
    panels = set(source["panel_ids"])
    require(panels == set(field["panel_generalized_coefficients"]) and len(panels) == 6, "all six current panel slices required")
    require(source["current_panel_machining_descriptors"] == descriptors["current_panel_machining_descriptors"] and len(source["current_panel_machining_descriptors"]["features"]) == 340, "current 340 panel apertures required")
    for table in ("panel_screw_actions", "contact_actions", "floor_actions", "common_shaft_bearing_actions", "shaft_end_capture_actions", "common_shaft_wood_bearing_actions", "common_shaft_steel_port_actions"):
        for row in field[table]:
            same_state(field, row)
    require(report["current_callbacks"] == {"axes": 100, "panel_apertures": 340, "panel_screws": 66, "old_geometry_source_contract_called": False, "old_support_footprints_used": False, "scoped_boundaries_restored": True, "equations_or_tolerances_changed": False, "field_or_admission_payload_modified": False}, "current callback boundary differs")
    require(report["component_reductions"]["own_wood_bearing_resultants_from_admitted_field"] == field["common_shaft_wood_bearing_actions"] and len(field["common_shaft_wood_bearing_actions"]) == 120, "all own wood action aliases must retain exact current bytes")
    mixed = [key for key, row in shafts.items() if len(row["surfaces"]) > 2 and {s["kind"] for s in row["surfaces"]} == {"wood", "steel"}]
    require(set(mixed) == {"eoere_bolt_"+number for number in ("065", "066", "067", "070", "071", "074", "079", "080")}, "eight mixed/shared stacks must remain represented")
    return axes, shafts, sorted(mixed)


def washer(check, row, action, shaft):
    require(row["id"] == action["id"] and row["axis_id"] == shaft["axis_id"] and row["end"] == action["end"]["end"] and row["host"] == action["end"]["host"], "washer own action/host differs")
    hardware = shaft["source_axis"]["hardware_scenario"]
    with localcontext() as context:
        context.prec = 45
        area = Decimal(str(math.pi)) * (Decimal(str(hardware["washer_od_mm"]))**2 - Decimal(str(hardware["washer_id_mm"]))**2) / 4
        check.number(row["nominal_full_annulus_area_mm2"], area, "annulus/area")
        check.number(row["nominal_full_annulus_average_pressure_mpa"], Decimal(str(action["compression_n"])) / area, "annulus/pressure")
    require(row["compression_n"] == action["compression_n"] >= 0 and row["actual_pressure_couple_nmm"] is None and row["actual_contact_area_or_peak_pressure"] is None and row["washer_bending_nut_head_or_wood_seat_resistance"] is None and row["point_capture_free_couple_is_annular_pressure_couple"] is False, "nominal washer average is not physical seat acceptance")


def screw(check, row, action, source, thickness):
    require(all(row[key] == value for key, value in action.items()), "screw action changed during scalar reference projection")
    require(action["first"] == source["first"] and action["second"] == source["second"] and action["point_xyz_mm"] == source["point_xyz_mm"], "own current screw source differs")
    force = matvec(columns(source["basis"]), action["local_force_n"])
    check.vector(action["force_on_receiver_xyz_n"], force, "screw/world-force")
    tension = action["local_force_n"][0]
    lateral = math.hypot(*action["local_force_n"][1:])
    check.number(action["withdrawal_n"], tension, "screw/signed-withdrawal")
    check.number(row["same_axis_simultaneous_lateral_n"], lateral, "screw/lateral")
    require(tension >= -1e-9, "tension-only screw cannot take compression")
    d, t = 9 / 25.4, (thickness - 1) / 25.4
    head = min(690 * math.pi * d * t, 1725 * math.pi * d*d) * 0.25 * N_PER_LBF
    thread = 2850 * 0.25 * 0.190 * N_PER_LBF / 25.4
    for key, value in {
        "generic_head_reference_n_CD1": head,
        "generic_head_ratio_CD1": tension / head,
        "generic_head_ratio_conditional_CD1p6": tension / (1.6 * head),
        "generic_withdrawal_required_effective_thread_mm_CD1": tension / thread,
        "generic_withdrawal_required_effective_thread_mm_conditional_CD1p6": tension / (1.6 * thread),
        "gross_nominal_length_after_panel_mm": 63.5 - thickness,
        "projected_annulus_mean_pressure_mpa": tension / (14 * math.pi),
    }.items():
        check.number(row[key], value, "screw/" + key)
    require(row["Hillman_product_capacity_or_stiffness_established"] is False and row["local_conical_indentation_punching_edge_capacity_established"] is False, "generic screw references must not qualify Hillman")


def circle_stress(value, diameter):
    with localcontext() as context:
        context.prec = 45
        n, v1, v2, t, m1, m2 = (Decimal(str(v)) for v in value)
        d, pi = Decimal(str(diameter)), Decimal(str(math.pi))
        area = pi * d*d / 4
        sigma = abs(n) / area + 32 * (m1*m1 + m2*m2).sqrt() / (pi * d**3)
        tau = 4 * (v1*v1 + v2*v2).sqrt() / (3 * area) + 16 * abs(t) / (pi * d**3)
        return float((sigma*sigma + 3 * tau*tau).sqrt())


def shaft_circle(check, row, cut_table, axis):
    require(row["axis_id"] == cut_table["axis_id"] == axis["id"] and row["body"] == "shaft/" + axis["id"], "shaft own identity differs")
    require(len(row["section_scenarios"]) == 1, "only declared nominal circle expected")
    section = row["section_scenarios"][0]
    diameter = axis["diameter_mm"]
    require(section["section_scenario"]["diameter_mm"] == diameter and section["section_scenario"]["id"] == "nominal_model_circle", "own nominal circle differs")
    require(section["sample_count"] == len(cut_table["cuts"]), "shaft sample census differs")
    peak = section["sampled_governing_same_cut"]
    matches = [r for r in cut_table["cuts"] if r["station_from_axis_point_mm"] == peak["station_from_axis_point_mm"]]
    require(len(matches) == 1 and matches[0]["local_N_V1_V2_T_M1_M2_n_nmm"] == peak["same_cut_N_V1_V2_T_M1_M2_n_nmm"] and matches[0]["point_xyz_mm"] == peak["point_xyz_mm"], "shaft peak must be one complete actual cut")
    value = peak["same_cut_N_V1_V2_T_M1_M2_n_nmm"]
    expected = circle_stress(value, diameter)
    check.number(peak["same_section_nominal_stress_envelope_mpa"], expected, "shaft/stress")
    check.number(expected, max(circle_stress(r["local_N_V1_V2_T_M1_M2_n_nmm"], diameter) for r in cut_table["cuts"]), "shaft/maximum-selection")
    direct = peak["direct_reference"]
    check.number(direct["axial_tension_demand_n"], max(value[0], 0), "shaft/direct-tension")
    check.number(direct["lateral_shear_demand_n"], math.hypot(*value[1:3]), "shaft/direct-shear")
    require(peak["same_section_nominal_first_yield_index"] is None and row["conditional_fy_mpa"] is None and row["material_basis"] is None and row["actual_thread_root_or_occupancy_adopted"] is False and row["complete_joint_acceptance"] is False, "nominal circle must not imply delivered bolt capacity")


@cache
def strip_j(width, thickness):
    b, t = max(width, thickness), min(width, thickness)
    series = math.fsum(math.tanh(n * math.pi * b / (2*t)) / n**5 for n in range(1, 128, 2))
    tail = 129**-5 + 1 / (8 * 129**4)
    factor, coefficient = b*t**3 / 3, 192*t / (math.pi**5 * b)
    allowance = 32 * sys.float_info.epsilon
    return factor*(1-coefficient*(series+tail))*(1-allowance), factor*(1-coefficient*series)*(1+allowance)


def strip_endpoint(check, row, root, force, couple, basis, width, thickness):
    local_f = matvec(columns(basis), force)
    local_m = matvec(columns(basis), add(couple, cross(sub(root, row["point_xyz_mm"]), force)))
    check.vector(row["same_section_force_N_V1_V2_n"], local_f, "strip/local-force")
    check.vector(row["same_section_moment_T_M1_M2_nmm"], local_m, "strip/local-couple", atol=2e-7)
    sigma = abs(local_f[0]) / (width*thickness) + 6*abs(local_m[1]) / (width*thickness**2) + 6*abs(local_m[2]) / (thickness*width**2)
    tau_v = 1.5*math.hypot(*local_f[1:]) / (width*thickness)
    jlow, jhigh = strip_j(width, thickness)
    tau_t = abs(local_m[0]) * min(width, thickness) / jlow
    for key, value in {
        "nominal_normal_stress_bound_mpa": sigma,
        "nominal_transverse_shear_norm_bound_mpa": tau_v,
        "nominal_torsion_shear_norm_bound_mpa": tau_t,
        "simultaneous_nominal_vm_bound_mpa": math.sqrt(sigma*sigma + 3*(tau_v+tau_t)**2),
    }.items():
        check.number(row[key], value, "strip/" + key)
    check.number(row["torsion_rectangle"]["J_lower_mm4"], jlow, "strip/J-lower")
    check.number(row["torsion_rectangle"]["J_upper_mm4"], jhigh, "strip/J-upper")
    require(row["section_scenario"] == "gross_rectangle" and row["removed_chord_mm"] == 0 and row["specified_fy_mpa"] is None and row["simultaneous_nominal_first_yield_bound_index"] is None and row["physical_fitting_strength_or_complete_joint_acceptance"] is False, "gross strip is not an actual holed fitting capacity")


def angle(check, row, recovery, descriptor, field):
    require(row["body"] == recovery["body"] == descriptor["body"], "angle own recovery differs")
    data = row["loaded_strip_comparison"]
    roots = indexed(recovery["strip_root_actions"], "port_id")
    ports = indexed(recovery["port_actions"], "port_id")
    source_ports = indexed(descriptor["ports"], "id")
    require(len(data["strips"]) == len(roots) == len(ports) == 4, "four own strips/ports required")
    q = descriptor["own_fitting_scenario"]["fitting_basis_columns_xyz"]
    heel = descriptor["own_fitting_scenario"]["heel_reference_xyz_mm"]
    flange_sums = defaultdict(list)
    for strip in data["strips"]:
        key = strip["port_id"]
        source, original = source_ports[key], roots[key]
        require(strip["flange"] == source["flange"] == original["flange"], "own flange differs")
        require(strip["strip_width_mm"] == 44.45 and strip["thickness_mm"] == 6.35 and strip["interval_length_mm"] == 65.0875, "declared gross strip dimensions differ")
        sign = -1 if key.endswith("minus") else 1
        local_root = [0, sign*22.225, 3.175] if strip["flange"] == "arm-x" else [3.175, sign*22.225, 0]
        root = add(heel, matvec(q, local_root))
        basis = q if strip["flange"] == "arm-x" else [[r[2], r[1], -r[0]] for r in q]
        check.vector(original["point_xyz_mm"], root, "strip/source-root", atol=2e-8)
        for a, b in zip(strip["basis_columns_xyz"], basis, strict=True):
            check.vector(a, b, "strip/source-basis")
        force, couple = original["applied_to_strip_force_xyz_n"], original["applied_to_strip_couple_at_root_xyz_nmm"]
        ends = indexed(strip["same_strip_endpoint_witnesses"], "cut_id")
        require(set(ends) == {"root", "neutral-tip"}, "both same-strip endpoints required")
        check.vector(ends["root"]["point_xyz_mm"], root, "strip/root-datum", atol=2e-8)
        check.vector(ends["neutral-tip"]["point_xyz_mm"], add(root, scale(columns(basis)[0], 65.0875)), "strip/tip-datum", atol=2e-8)
        for endpoint in ends.values():
            strip_endpoint(check, endpoint, root, force, couple, basis, 44.45, 6.35)
        require(strip["nominal_gross_prismatic_field_governing_endpoint"] == max(ends.values(), key=lambda r: r["simultaneous_nominal_vm_bound_mpa"]), "strip governing endpoint selection differs")
        flange_sums[strip["flange"]].append(force + add(couple, cross(sub(root, heel), force)))
    for arm, values in flange_sums.items():
        check.vector(data["flange_root_resultants_diagnostic_only_n_nmm"][arm], [math.fsum(r[i] for r in values) for i in range(6)], "strip/flange-resultant", atol=2e-7)
    require(data["complete_joint_acceptance"] is False and data["physical_product_fy_mpa"] is None and data["full_flange_aggregate_stress_comparison"] is None, "strip model must retain unknown whole fitting resistance")
    joins = indexed(row["own_external_port_joins"], "port_id")
    for key, port in ports.items():
        point = port["point_xyz_mm"]
        actions = []
        for action in field["common_shaft_steel_port_actions"]:
            if action["host"] == row["body"] and action["flange"] == key:
                actions.append(("shaft-surface/"+action["axis_id"]+"/"+str(action["surface_index"]), action["point_xyz_mm"], action["force_on_steel_xyz_n"], action["moment_on_steel_at_point_xyz_nmm"]))
        for action in field["contact_actions"]:
            if action["kind"] == "flange_contact" and action["first"] == row["body"] and action["flange"] == key:
                actions.append((action["id"], action["point_xyz_mm"], action["force_on_first_xyz_n"], [0, 0, 0]))
        join = joins[key]
        require(join["own_external_action_ids"] == [a[0] for a in actions], "external port action selection differs")
        force = [math.fsum(a[2][i] for a in actions) for i in range(3)]
        moments = [add(a[3], cross(sub(a[1], point), a[2])) for a in actions]
        couple = [math.fsum(a[i] for a in moments) for i in range(3)]
        check.vector(join["own_external_force_xyz_n"], force, "port/force")
        check.vector(join["own_external_couple_about_port_xyz_nmm"], couple, "port/couple", atol=2e-7)
        check.vector(join["external_minus_elastic_required_force_xyz_n"], sub(force, port["external_force_required_at_port_xyz_n"]), "port/force-residual")
        check.vector(join["external_minus_elastic_required_couple_xyz_nmm"], sub(couple, port["external_couple_required_at_port_xyz_nmm"]), "port/couple-residual", atol=2e-7)


def point_actions(field):
    actions, gravity = defaultdict(list), {}
    for table in ("common_shaft_bearing_actions", "shaft_end_capture_actions", "panel_screw_actions", "contact_actions"):
        for row in field[table]:
            force, point = row["force_on_first_xyz_n"], row["point_xyz_mm"]
            first_couple = row.get("moment_on_first_at_point_xyz_nmm", row.get("moment_at_point_model_xyz_nmm", [0, 0, 0]))
            second_couple = row.get("moment_on_second_at_point_xyz_nmm", scale(first_couple, -1))
            actions[row["first"]].append((point, force, first_couple))
            actions[row["second"]].append((row.get("host_support_point_xyz_mm", point), scale(force, -1), second_couple))
    for row in field["floor_actions"]:
        actions[row["first"]].append((row["point_xyz_mm"], row["force_on_first_xyz_n"], row.get("moment_at_point_model_xyz_nmm", [0, 0, 0])))
    for row in field["body_applied_loads"]:
        if row["id"].startswith("self-weight/"):
            require(row["body"] not in gravity, "duplicate own member selfweight")
            gravity[row["body"]] = row
        else:
            actions[row["body"]].append((row["point_xyz_mm"], row["force_xyz_n"], row.get("moment_xyz_nmm", [0, 0, 0])))
    return actions, gravity


def gross_wrench(source, cut, actions, gravity):
    grain = source["axis"]
    low, high = dot(grain, source["start"]), dot(grain, source["end"])
    station, length = dot(grain, cut), high-low
    center, weight = gravity["point_xyz_mm"], gravity["force_xyz_n"]
    t = (station-low)/length
    delta = (dot(grain, center)-(low+high)/2)/length
    # Integrate in normalized t rather than subtracting global s**3 terms.
    fraction = t + 6*delta*(t*t-t)
    first_t = t*t/2 + 12*delta*(t**3/3-t*t/4)
    base = add(sub(center, scale(grain, dot(grain, center))), scale(grain, low))
    arm = add(scale(sub(base, cut), fraction), scale(grain, length*first_t))
    forces, moments = [scale(weight, fraction)], [cross(arm, weight)]
    for point, force, couple in actions:
        if dot(grain, point) < station:
            forces.append(force)
            moments.append(add(cross(sub(point, cut), force), couple))
    return [-math.fsum(row[i] for row in forces) for i in range(3)], [-math.fsum(row[i] for row in moments) for i in range(3)]


@cache
def timber_torsion(width, depth):
    # The pinned 200-odd-term equal-modulus face coefficients; scalar only.
    w, h = round(width, 9), round(depth, 9)
    b, d = min(w, h), max(w, h)
    odd = range(1, 400, 2)
    j = d*b**3/3*(1-192*b/(math.pi**5*d)*math.fsum(math.tanh(n*math.pi*d/(2*b))/n**5 for n in odd))

    def factor(ratio):
        return 1-8/math.pi**2*math.fsum(2*math.exp(-n*math.pi*ratio/2)/(1+math.exp(-n*math.pi*ratio))/n**2 for n in odd)

    return h*factor(w/h)/j, w*factor(h/w)/j


def gross_member(check, row, source, actions, gravity):
    basis = [source[key] for key in ("axis", "section_u", "section_v")]
    width, depth = source["width_mm"], source["depth_mm"]
    span = dot(source["axis"], sub(source["end"], source["start"]))
    require(row["member"] == source["name"] and row["source_basis_grain_u_v_xyz"] == basis and row["sample_count"] >= 51, "own sampled gross member source differs")
    check.vector([row["source_width_mm"], row["source_depth_mm"], row["source_span_mm"]], [width, depth, span], "gross/source-dimensions")
    require(row["finished_net_resistance_established"] is False and row["continuous_maximum_or_actual_bracing_established"] is False and row["old_cut_or_force_used"] is False and row["own_host_capture_points_and_free_couples_preserved"] is True, "gross sample must not imply net or restraint acceptance")
    area = width*depth
    psi = 0.006894757293168361
    refs = {"Fb_star_mpa": 900*1.3*psi, "Ft_mpa": 575*1.3*psi, "Fc_star_mpa": 1350*1.1*psi, "Fv_mpa": 180*psi, "Fc_perp_mpa": 625*psi, "Emin_mpa": 580000*psi}
    require(set(row["witnesses"]) == {"fully_braced_normal", "sufficient_shear_torsion"}, "two separate complete gross witnesses required")
    for witness in row["witnesses"].values():
        wrench = witness["signed_same_cut_wrench"]
        force, couple = gross_wrench(source, wrench["cut_point_xyz_mm"], actions, gravity)
        check.vector(wrench["force_on_lower_portion_xyz_n"], force, "gross/cut-force", atol=2e-7)
        check.vector(wrench["moment_on_lower_portion_about_cut_xyz_nmm"], couple, "gross/cut-couple", atol=2e-6)
        local = matvec(basis, force) + matvec(basis, couple)
        check.vector(witness["local_N_Vu_Vv_T_Mu_Mv_n_nmm"], local, "gross/local-wrench", atol=2e-6)
        n, vu, vv, torque, mu, mv = local
        comparison = witness["gross_CD1_comparison"]
        stored_refs = comparison["conditional_full_length_stability_kernel"]["references"]
        for key, value in refs.items():
            check.number(stored_refs[key], value, "gross/reference")
        bending = 6*abs(mu)/(width*depth**2) + 6*abs(mv)/(depth*width**2)
        normal = (max(-n, 0)/area/refs["Fc_star_mpa"])**2+bending/refs["Fb_star_mpa"] if n < 0 else max(n, 0)/area/refs["Ft_mpa"]+bending/refs["Fb_star_mpa"]
        check.number(comparison["fully_braced_component_normal_interaction"], normal, "gross/normal")
        transverse = [1.5*abs(vu)/area, 1.5*abs(vv)/area]
        torsion = scale(timber_torsion(width, depth), abs(torque))
        face = [(a+b)/refs["Fv_mpa"] for a, b in zip(transverse, torsion, strict=True)]
        check.vector(comparison["transverse_shear_component_maxima_mpa"], transverse, "gross/transverse")
        check.vector(comparison["torsional_shear_component_maxima_mpa"], torsion, "gross/torsion")
        check.number(comparison["equal_longitudinal_shear_moduli_rectangle_face_ratio"], max(face), "gross/face-ratio")
        check.number(comparison["equal_longitudinal_shear_moduli_rectangle_component_upper_bound_ratio"], math.hypot(*face), "gross/sufficient-ratio")
        check.number(comparison["weak_column_effective_length_domain_limit_mm"], 50*min(width, depth), "gross/domain-limit")
        check.number(comparison["full_length_over_weak_column_domain_limit"], span/(50*min(width, depth)), "gross/span-domain")


def panel_scalars(check, row, coefficients):
    section, deformation = row["resolved_section_diagnostics"], row["deformation_diagnostics"]
    require(section["sample_count_per_axis"] == deformation["sample_count_per_axis"] == 41 and deformation["linear_plate_applicability_established"] is False, "declared panel sample/applicability boundary differs")
    references = {"bending_x": 775*N_PER_LBF/12, "bending_y": 455*N_PER_LBF/12, "rolling_x": 350*N_PER_LBF/(12*25.4), "rolling_y": 350*N_PER_LBF/(12*25.4)}
    require(set(section["components"]) == set(references), "all four separate panel references required")
    for key, result in section["components"].items():
        check.number(result["reference_per_mm_width_CD1"], references[key], "panel/reference")
        check.number(result["sampled_ratio_CD1"], result["peak_abs_resultant"]/references[key], "panel/CD1-ratio")
        check.number(result["sampled_ratio_conditional_CD1p6"], result["peak_abs_resultant"]/(1.6*references[key]), "panel/CD1p6-ratio")
    order = coefficients["basis_order_per_direction"]
    w = coefficients["coefficients"][2*order*order:]
    require(len(w) == order*order, "own outward panel coefficient block required")
    knots = coefficients["knots_normalized"]
    cx = [3*(w[(i+1)*order+j]-w[i*order+j])/(knots[i+4]-knots[i+1])/coefficients["width_mm"] for i in range(order-1) for j in range(order)]
    cy = [3*(w[i*order+j+1]-w[i*order+j])/(knots[j+4]-knots[j+1])/coefficients["height_mm"] for i in range(order) for j in range(order-1)]
    check.number(deformation["absolute_outward_w_coefficient_convex_hull_bound_mm"], max(map(abs, w)), "panel/coefficient-bound")
    check.number(deformation["absolute_slope_x_derivative_coefficient_bound"], max(map(abs, cx)), "panel/x-derivative-bound")
    check.number(deformation["absolute_slope_upslope_derivative_coefficient_bound"], max(map(abs, cy)), "panel/y-derivative-bound")
    peak = deformation["maximum_sampled_abs_outward_w_mm"]
    check.number(peak, max(abs(deformation["minimum_sampled_outward_w_mm"]), abs(deformation["maximum_sampled_outward_w_mm"])), "panel/sample-absolute")
    check.number(deformation["maximum_sampled_abs_w_over_panel_height"], peak/coefficients["height_mm"], "panel/height-ratio")
    check.number(deformation["slope_angle_marker_rad"], math.atan(deformation["maximum_sampled_slope_norm"]), "panel/slope-angle")
    require(peak <= max(map(abs, w))+1e-9 and deformation["maximum_sampled_slope_norm"] <= math.hypot(max(map(abs, cx)), max(map(abs, cy)))+1e-9, "panel samples leave independent coefficient bounds")


def check_case(report, field, admission, case, geometry, descriptors, inputs):
    check = Comparison()
    axes, shafts, mixed = check_identity(report, field, admission, case, geometry, descriptors, inputs)
    reductions = report["component_reductions"]
    captures = indexed(field["shaft_end_capture_actions"], "id")
    require(len(captures) == len(reductions["own_washer_capture_diagnostics"]) == 200, "all 200 own capture diagnostics required")
    require(len(indexed(reductions["own_washer_capture_diagnostics"], "id")) == 200, "unique capture diagnostics required")
    for row in reductions["own_washer_capture_diagnostics"]:
        washer(check, row, captures[row["id"]], shafts[row["axis_id"]])
    screws, screw_source = indexed(field["panel_screw_actions"], "axis_id"), indexed(field["source_inputs"]["hillman_rows"], "id")
    require(len(indexed(reductions["simultaneous_Hillman_actions_and_generic_references"], "axis_id")) == len(screws) == 66, "all 66 own screw references required")
    for row in reductions["simultaneous_Hillman_actions_and_generic_references"]:
        screw(check, row, screws[row["axis_id"]], screw_source[row["axis_id"]], field["panel_generalized_coefficients"][row["panel"]]["thickness_mm"])
    cuts = indexed(field["common_shaft_section_cut_actions"], "axis_id")
    require(set(indexed(reductions["own_shaft_circle_comparisons"], "axis_id")) == set(axes) == set(cuts), "all 100 own shaft comparisons required")
    for row in reductions["own_shaft_circle_comparisons"]:
        shaft_circle(check, row, cuts[row["axis_id"]], axes[row["axis_id"]])
    recovery = indexed(field["four_port_fitting_actions"], "body")
    fitting_descriptors = indexed(field["fitting_operator_descriptors"], "body")
    require(set(indexed(reductions["angle_duties"], "body")) == set(recovery) == set(fitting_descriptors) and len(recovery) == 22, "all 22 current fittings required")
    for row in reductions["angle_duties"]:
        bindings = [r["axis_id"] for r in field["source_inputs"]["fitting_port_bindings"] if r["angle_id"] == row["body"]]
        require(row["physical_axis_ids"] == sorted(bindings) and len(bindings) == 4, "own fitting/shaft duty selection differs")
        angle(check, row, recovery[row["body"]], fitting_descriptors[row["body"]], field)
    steel = {(r["axis_id"], r["angle_id"], r["flange"]): r for r in field["common_shaft_steel_port_actions"]}
    surfaces = reductions["own_steel_surface_wrenches"]
    require(len(surfaces) == len(steel) == 88 and len({(r["axis_id"], r["angle_id"], r["flange"]) for r in surfaces}) == 88, "all 88 own steel surface wrenches required")
    for row in surfaces:
        original = steel[row["axis_id"], row["angle_id"], row["flange"]]
        for key in ("point_xyz_mm", "force_on_steel_xyz_n", "moment_on_steel_at_point_xyz_nmm"):
            check.vector(row[key], original[key], "steel-surface/" + key, atol=2e-7)
        require(set(row["physical_action_ids"]) == set(original["own_bearing_points"]+original["own_end_captures"]) and row["opposed_wood_or_angle_action_inferred"] is False, "own steel source action selection differs")
    timbers = indexed(field["source_inputs"]["timber_rows"], "name")
    require(set(indexed(reductions["fresh_gross_member_diagnostics"], "member")) == set(timbers), "all 22 own gross member diagnostics required")
    actions, gravity = point_actions(field)
    for row in reductions["fresh_gross_member_diagnostics"]:
        gross_member(check, row, timbers[row["member"]], actions[row["member"]], gravity[row["member"]])
    panels = reductions["six_panel_reductions"]
    require(set(indexed(panels["panel_diagnostics"], "panel")) == set(field["source_inputs"]["panel_ids"]) and panels["old_state_validator_or_old_demand_called"] is False, "all six current panel diagnostics required")
    for row in panels["panel_diagnostics"]:
        panel_scalars(check, row, field["panel_generalized_coefficients"][row["panel"]])
    corners = indexed(reductions["exterior_cleat_corners"], "duty_id")
    require(set(corners) == {"exterior-cleat-corner-left", "exterior-cleat-corner-right"}, "both cleat corners required")
    for side in ("left", "right"):
        row = corners["exterior-cleat-corner-"+side]
        members = ["eoere_cleat_"+side, "base_side_"+side, "base_post_outer_"+side, "base_header"]
        require(row["members"] == members and row["physical_axis_ids"] == sorted(k for k, v in axes.items() if "eoere_cleat_"+side in v["receivers"]), "own current cleat corner path differs")
        require(row["own_direct_contact_ids"] == [r["id"] for r in field["contact_actions"] if r["first"] in members and r["second"] in members], "own cleat contact selection differs")
    shaft_peak = max(reductions["own_shaft_circle_comparisons"], key=lambda r: r["section_scenarios"][0]["sampled_governing_same_cut"]["same_section_nominal_stress_envelope_mpa"])
    strip_peaks = [(a["body"], s["port_id"], s["nominal_gross_prismatic_field_governing_endpoint"]["simultaneous_nominal_vm_bound_mpa"]) for a in reductions["angle_duties"] for s in a["loaded_strip_comparison"]["strips"]]
    screw_peak = max(reductions["simultaneous_Hillman_actions_and_generic_references"], key=lambda r: r["generic_head_ratio_CD1"])
    panel_peaks = [(p["panel"], k, v["sampled_ratio_CD1"]) for p in panels["panel_diagnostics"] for k, v in p["resolved_section_diagnostics"]["components"].items()]
    return {"case_id": case, "state_id": field["state_id"], "scalar_comparisons": check.count,
            "maximum_absolute_arithmetic_errors_by_quantity_family": dict(sorted(check.errors.items())),
            "current_axes_screws_panels_timbers": [100, 66, 6, 22], "mixed_shared_stack_axis_ids_resistance_still_null": mixed,
            "nominal_shaft_peak": {"axis_id": shaft_peak["axis_id"], "stress_envelope_mpa": shaft_peak["section_scenarios"][0]["sampled_governing_same_cut"]["same_section_nominal_stress_envelope_mpa"]},
            "nominal_gross_strip_peak_body_port_mpa": max(strip_peaks, key=lambda r: r[2]),
            "generic_screw_head_peak": {"axis_id": screw_peak["axis_id"], "CD1_reference_ratio": screw_peak["generic_head_ratio_CD1"], "Hillman_capacity_established": False},
            "panel_sample_peak_panel_component_CD1_reference_ratio": max(panel_peaks, key=lambda r: r[2]),
            "checks": {"raw_field_admission_and_current_input_case_identity": True, "all_11_admitted_table_digests": True,
                       "own_120_wood_aliases": True, "own_200_nominal_annuli": True, "own_66_screw_generic_scalar_references": True,
                       "own_100_shaft_raw_sample_maximum_selections": True, "own_176_strip_endpoints_and_88_endpoint_selections": True,
                       "own_88_external_port_wrench_transports": True, "own_88_steel_surface_aliases": True,
                       "own_44_gross_cut_wrenches_and_scalar_references": True, "own_six_panel_scalar_ratios_and_coefficient_bounds": True,
                       "both_cleat_corner_members_axes_contacts": True, "unknown_joint_resistance_and_all_false_release_preserved": True}}


def controls(report, field):
    """Alter isolated in-memory rows only; no live source/file mutation."""
    reductions = report["component_reductions"]
    actions, gravity = point_actions(field)
    shafts = indexed(field["source_inputs"]["shafts"], "axis_id")
    captures = indexed(field["shaft_end_capture_actions"], "id")
    screw_actions = indexed(field["panel_screw_actions"], "axis_id")
    screw_sources = indexed(field["source_inputs"]["hillman_rows"], "id")
    cuts = indexed(field["common_shaft_section_cut_actions"], "axis_id")
    timbers = indexed(field["source_inputs"]["timber_rows"], "name")
    result = []

    def reject(label, value, mutate, evaluate):
        altered = copy.deepcopy(value)
        mutate(altered)
        try:
            evaluate(altered)
        except (ValueError, KeyError):
            result.append(label)
        else:
            raise ValueError("reviewer accepted altered row: " + label)

    row = reductions["own_washer_capture_diagnostics"][0]
    reject("nominal_annulus_pressure", row, lambda r: r.update(nominal_full_annulus_average_pressure_mpa=r["nominal_full_annulus_average_pressure_mpa"]+1), lambda r: washer(Comparison(), r, captures[r["id"]], shafts[r["axis_id"]]))
    row = reductions["simultaneous_Hillman_actions_and_generic_references"][0]
    reject("generic_screw_ratio", row, lambda r: r.update(generic_head_ratio_CD1=r["generic_head_ratio_CD1"]+1), lambda r: screw(Comparison(), r, screw_actions[r["axis_id"]], screw_sources[r["axis_id"]], field["panel_generalized_coefficients"][r["panel"]]["thickness_mm"]))
    row = reductions["own_shaft_circle_comparisons"][0]
    reject("shaft_governing_stress", row, lambda r: r["section_scenarios"][0]["sampled_governing_same_cut"].update(same_section_nominal_stress_envelope_mpa=0), lambda r: shaft_circle(Comparison(), r, cuts[r["axis_id"]], shafts[r["axis_id"]]["source_axis"]))
    row = reductions["angle_duties"][0]["loaded_strip_comparison"]["strips"][0]
    endpoint = row["same_strip_endpoint_witnesses"][0]
    root = next(r for r in field["four_port_fitting_actions"][0]["strip_root_actions"] if r["port_id"] == row["port_id"])
    reject("strip_same_cut_vm", endpoint, lambda r: r.update(simultaneous_nominal_vm_bound_mpa=0), lambda r: strip_endpoint(Comparison(), r, root["point_xyz_mm"], root["applied_to_strip_force_xyz_n"], root["applied_to_strip_couple_at_root_xyz_nmm"], row["basis_columns_xyz"], 44.45, 6.35))
    row = reductions["fresh_gross_member_diagnostics"][0]
    reject("gross_member_cut_couple", row, lambda r: r["witnesses"]["fully_braced_normal"]["signed_same_cut_wrench"]["moment_on_lower_portion_about_cut_xyz_nmm"].__setitem__(0, 1e9), lambda r: gross_member(Comparison(), r, timbers[r["member"]], actions[r["member"]], gravity[r["member"]]))
    row = reductions["six_panel_reductions"]["panel_diagnostics"][0]
    reject("panel_scalar_ratio", row, lambda r: r["resolved_section_diagnostics"]["components"]["bending_x"].update(sampled_ratio_CD1=1e9), lambda r: panel_scalars(Comparison(), r, field["panel_generalized_coefficients"][r["panel"]]))
    reject("invented_complete_resistance", {"release": report["release"], "complete_joint_resistance": None, "component_reductions": {"complete_wood_bolt_yield_end_edge_Cdelta_group_splitting_resistance": None, "angle_duties": [], "exterior_cleat_corners": []}}, lambda r: r.update(complete_joint_resistance=1), boundaries)
    reject("cross_case_identity", {k: report[k] for k in ("state_id", "case_id", "accessory_placement")}, lambda r: r.update(case_id="wrong-case"), lambda r: same_state(field, r))
    reject("nonfinite_number", {"value": 1.}, lambda r: r.update(value=float("nan")), finite)
    return result


def parse_cases(values):
    if not values:
        return dict(FIRST_THREE)
    result = {}
    for value in values:
        parts = value.split(":")
        require(len(parts) == 4 and parts[0] in CASES and parts[0] not in result and all(re.fullmatch(r"[0-9a-f]{64}", v) for v in parts[1:]), "case requires unique CASE:RESULT_SHA:FIELD_SHA:ADMISSION_SHA")
        result[parts[0]] = tuple(parts[1:])
        require(parts[0] not in FIRST_THREE or result[parts[0]] == FIRST_THREE[parts[0]], "first three frozen target bindings must be retained")
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--case", action="append", help="CASE:RESULT_SHA:FIELD_SHA:ADMISSION_SHA; default is the frozen first three")
    parser.add_argument("--component-attempt", action="append", default=[], help="CASE:attemptNN; default attempt01. Field/admission always use attempt01.")
    parser.add_argument("--prior-review", type=Path, help="reuse exactly pinned checks for already reviewed cases")
    parser.add_argument("--prior-sha256", help="expected SHA256 of --prior-review")
    parser.add_argument("--out", type=Path, help="exclusive new receipt path, inside this review directory")
    args = parser.parse_args()
    cases = parse_cases(args.case)
    attempts = {}
    for value in args.component_attempt:
        case, attempt = value.split(":")
        require(case in cases and case not in attempts and re.fullmatch(r"attempt[0-9]{2,}", attempt), "unique current case/attempt required")
        attempts[case] = attempt
    require(bool(args.prior_review) == bool(args.prior_sha256), "prior review path and exact SHA must be provided together")
    require(args.out is None or args.out.resolve().parent == OWN.parent, "receipt must stay in the owned review directory")
    require(args.out is None or not args.out.exists(), "receipt path already exists")
    own_digest = sha(OWN)
    direct = {relative(path): digest for path, digest in FIXED.items()}
    direct[relative(OWN)] = own_digest
    prior = read(args.prior_review, args.prior_sha256) if args.prior_review else None
    if prior is not None:
        require(prior["schema"] == "eoere_current_component_actual_output_independent_review/v1" and prior["status"] == "CLEAN_SAVED_CURRENT_OUTPUTS_AND_BOUNDED_SCALAR_ARITHMETIC" and prior["findings"] == [] and prior["targets_and_direct_sources_sha256"][relative(OWN)] == own_digest, "clean prior receipt from identical reviewer required")
        require(set(prior["reviewed_case_ids"]) < set(cases) and prior["release"] == RELEASE, "prior cases must be a strict subset of extended review")
    geometry, descriptors, inputs = [read(path, FIXED[path]) for path in (GEOMETRY, DESCRIPTORS, INPUTS)]
    loaded, union = {}, dict(direct)
    for case, digests in cases.items():
        paths = [MECH / "current-component-results-v1" / case / attempts.get(case, "attempt01") / "result.json",
                 MECH / "current-cases-v1" / case / "attempt01/field.json",
                 MECH / "current-cases-v1" / case / "attempt01/admission.json"]
        values = [read(path, digest) for path, digest in zip(paths, digests, strict=True)]
        for path, digest in zip(paths, digests, strict=True):
            merge(direct, {relative(path): digest})
        report, _field, admission = values
        require(report["raw_field_sha256"] == admission["input_raw_sha256"] == digests[1] and report["field_admission_receipt_sha256"] == digests[2], "result must bind exact raw field/admission pair")
        require(Path(ROOT / admission["source_path"]).resolve() == GATE, "admission validator source path differs")
        for value in values:
            merge(union, value["source_sha256"])
        require(report["source_sha256"][relative(CONSUMER)] == CONSUMER_SHA, "actual result must bind reviewed consumer")
        loaded[case] = values
    if prior is not None:
        require(all(direct.get(path) == digest for path, digest in prior["targets_and_direct_sources_sha256"].items()), "prior target/direct source bindings differ")
        prior_union = dict(prior["targets_and_direct_sources_sha256"])
        for case in prior["reviewed_case_ids"]:
            for value in loaded[case]:
                merge(prior_union, value["source_sha256"])
        require(canonical(prior_union) == prior["authenticated_source_union"]["canonical_sha256"], "prior authenticated union differs")
        merge(direct, {relative(args.prior_review): args.prior_sha256})
    merge(union, direct)
    for path in METHODS:
        require(relative(path) in union, "inspected equation source lacks a result closure binding: " + relative(path))
    verify(union)
    prior_checks = indexed(prior["cases"], "case_id") if prior else {}
    results = [prior_checks[case] if case in prior_checks else check_case(*values, case, geometry, descriptors, inputs) for case, values in loaded.items()]
    first = next(values for case, values in loaded.items() if case not in prior_checks)
    negative = controls(first[0], first[1])
    # Simple signed/circular hand fixtures exercise independent math paths.
    check = Comparison()
    check.number(circle_stress([math.pi, 0, 0, 0, 0, 0], 2), 1, "fixture/axial-circle")
    check.number(circle_stress([0, 0, 0, math.pi/2, 0, 0], 2), math.sqrt(3), "fixture/torsion-circle")
    check.vector(cross([1, 0, 0], [0, 2, 0]), [0, 0, 2], "fixture/transport-sign")
    verify(union)
    receipt = {
        "schema": "eoere_current_component_actual_output_independent_review/v1",
        "status": "CLEAN_SAVED_CURRENT_OUTPUTS_AND_BOUNDED_SCALAR_ARITHMETIC",
        "findings": [], "reviewed_case_ids": list(cases), "all_six_case_coverage": set(cases) == set(CASES),
        "prior_review": {"path": relative(args.prior_review), "sha256": args.prior_sha256, "case_checks_reused_without_reduction": list(prior_checks)} if prior else None,
        "targets_and_direct_sources_sha256": dict(sorted(direct.items())),
        "equation_sources_sha256": {relative(p): union[relative(p)] for p in METHODS},
        "authenticated_source_union": {"paths": len(union), "canonical_sha256": canonical(union),
                                       "derivation": "union of each exact target result, field and admission source_sha256 map plus targets_and_direct_sources_sha256",
                                       "every_source_file_hashed_before_and_after": True},
        "cases": results, "isolated_in_memory_negative_controls_rejected": negative,
        "known_answer_scalar_fixtures": ["axial_circle", "torsion_circle", "signed_cross_product_transport"],
        "execution": {"stdlib_only": True, "saved_JSON_and_source_hash_reads_only": True,
                      "genuine_producer_reducer_or_gate_import_or_call": False, "numerical_field_admission_rerun": False,
                      "CAD_import_query_or_rebuild": False, "panel_spatial_resampling_or_operator_preparation": False,
                      "frame_K_q_native_solve_or_browser": False, "source_mutation_staging_or_shared_document_writes": False},
        "limits": [
            "Authenticates and relies upon the exact completed independent numerical field admissions; does not independently repeat their laws, stiffness, equilibrium or recovery calculations.",
            "Checks stored component arithmetic, identities, scalar source references, shaft raw-sample maxima, and strip endpoint selection. Does not establish a physical demand bound or validate the first-order approximation.",
            "Gross member review independently integrates own saved point loads and affine selfweight at the 44 reported witness cuts per case. It does not rerun their station search, complete stability kernel, continuous extrema or finished-net-section calculations.",
            "Panel checks cover scalar ratios and coefficient/derivative bounds from current slices. Spatial sampled peaks, affine fit, opening boundaries, local supports, punching and panel product resistance are not independently resampled or qualified.",
            "Gross strip and nominal circular stresses, generic screw references and annulus average pressure retain their recorded scopes. Delivered thickness/radius/material/shank/threads/seats/tools, eight mixed stacks, group/splitting behavior, restraint and complete joint resistances remain unresolved.",
            "Reference exceedances remain reported; panel and screw remedies remain stopped. No historical forces, cross-case combined interaction, capacity or release is transferred.",
        ],
        "command": list(sys.orig_argv), "python": sys.version,
        "complete_joint_resistance": None, "release": dict(RELEASE),
    }
    payload = (json.dumps(receipt, indent=2, sort_keys=True, allow_nan=False)+"\n").encode()
    verify(union)
    if args.out is not None:
        with args.out.open("xb") as stream:
            stream.write(payload)
        verify(union)
    print(json.dumps({"status": receipt["status"], "cases": list(cases), "source_union_paths": len(union),
                      "scalar_comparisons": sum(r["scalar_comparisons"] for r in results), "negative_controls": len(negative),
                      "review_helper_sha256": own_digest,
                      "receipt": relative(args.out) if args.out else None,
                      "receipt_sha256": hashlib.sha256(payload).hexdigest() if args.out else None}, sort_keys=True))


if __name__ == "__main__":
    main()
