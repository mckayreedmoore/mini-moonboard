"""Parent-only reference arithmetic on the accepted common knee shaft fields.

Import is inert. prepare(output) performs only stdlib provenance/identity joins.
build(output) compares saved simultaneous T/V/M, separate nominal thread tension,
wood seats and bore demands, and exports 48 signed own-end pressure wrenches.
No equilibrium, native, CAD, washer-flexure, timber-cut or splitting API is called.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
RAW = HERE / "rawlocal/knee-common-references"
COMMON = HERE / "rawlocal/knee-common-shafts/attempt01"
PRODUCER = HERE / "knee-common-shafts.py"
MATERIALS = ROOT / "docs/wood-joints-mvp/hypotheses/hardware-material-specification-2026-09-30/material-inputs.json"
FASTENERS = MATERIALS.with_name("fastener-inputs.json")
PSI_MPA = 0.006894757293168
STEEL_REFERENCE_DIVISOR = 1.25  # Owner-directed reference convention, applied once.
CASES = ["a12-rear", "a12-forward", "a12-left", "k12-right", "k12-rear", "a1-rear"]
AXES = [f"knee_outer_{side}_side_{i}" for side in ("left", "right") for i in (1, 2)]
PINS = {
    COMMON / "receipt.json": "7abd870ca5a3923937cc44ada389704f9977e0d3bb9ed0f546abb06ba283ffda",
    COMMON / "report.json": "dd6228320aaeaef898e68b738c05ade574be9fa28e8c7473648e9f21b5c7b2b0",
    COMMON / "input-contract.json": "7a38255a5e4bfcc49e7e2fd74b12117de7673dca769c6b17611a29cd0aa0f3a6",
    COMMON / "engineering-reference.json": "24b3eb2e865b00cf02fb448bbfb533cf37a11b56a37b8cce127cb928c0c34183",
    PRODUCER: "540d2b4311de1fc46de1995305519bbfab2dc9efceedf3dda2b0e95f98784288",
    MATERIALS: "0f33ad8fd517673a4ebbed36c4a30c1cfe07e0d8163165bdc804af91d958fc5a",
    FASTENERS: "ac8c5ca36105e3eab48f58c868794fc8a42d77cd54dfa5c76fb41f0934fd2ac2",
}
FLAGS = {
    "new_equilibrium_native_CAD_or_washer_flexure_run": False,
    "historical_isolated_pass_transferred": False,
    "source_loads_or_model_changed": False,
    "finite_rotation_rechecked": False,
    "actual_hardware_or_wood_qualified": False,
    "bore_ratios_are_adjusted_joint_resistance": False,
    "wood_peak_ratios_are_joint_utilization": False,
    "N09_complete": False,
    "timber_splitting_or_cuts_completed": False,
    "other_30_joint_duties_completed": False,
    "internal_v_field_qualified": False,
    "global_frame_feedback": False,
    "complete_joint_acceptance": False,
    "proposal_adopted": False,
    "physical_release": False,
    "physical_failure_claimed": False,
    "software_tests_or_review_run": False,
}
LIMITS = [
    "The saved common-pose maximum is about 5.616 degrees. These are first-order kinematics; finite rotation, geometric shortening and geometric stiffness are not rechecked by arithmetic.",
    "Steel uses simultaneous saved smooth-section T/V/M and a cross-section normal/shear envelope proxy, not an exact fiber-level von Mises field or actual thread-root stress.",
    "The owner-directed 1.25 steel reference divisor is applied once to yield references; saved loads, pressure fields and wood references remain unscaled.",
    "Wood seat means and local peaks use conditional dry DF-L No. 2 orientation/base references. Rigid concentric annuli and source-proposed grain remain hypotheses; support masks, stock and ripped-block grade are unqualified.",
    "Bore pressure/Fe comparisons use the nominal full 6.35 mm diameter hypothesis and conditional 5600/4450 psi bearing inputs. They do not supply three-receiver joint resistance, thread-occupancy qualification or splitting resistance.",
    "Reference exceedance identifies the named arithmetic comparison only. It does not assert an observed physical failure or complete structural acceptance.",
    "Timber cuts/splitting, other 30 duties, internal v ties, washer flexure/capacity and external frame feedback remain with the parent and their existing owners.",
]


def require(condition, message):
    if not condition:
        raise ValueError("STOP: " + message)


def sha(path):
    with Path(path).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def read(path):
    return json.loads(Path(path).read_text())


def write(path, value):
    with Path(path).open("x") as stream:
        stream.write(json.dumps(value, indent=2, allow_nan=False) + "\n")


def lines(path, records):
    with Path(path).open("x") as stream:
        stream.writelines(json.dumps(record, allow_nan=False) + "\n" for record in records)


def bind(pins, path, digest):
    path = Path(path).resolve()
    require(path.is_relative_to(ROOT) and (path not in pins or pins[path] == digest), "conflicting/external source")
    pins[path] = digest


def authenticate(pins):
    for path, digest in pins.items():
        require(sha(path) == digest, "frozen source changed: " + str(path))


def source_map(pins):
    return {p.relative_to(ROOT).as_posix(): digest for p, digest in sorted(pins.items())}


def dot(a, b):
    return sum(x*y for x, y in zip(a, b, strict=True))


def norm(a):
    return math.sqrt(dot(a, a))


def cross(a, b):
    return [a[1]*b[2]-a[2]*b[1], a[2]*b[0]-a[0]*b[2], a[0]*b[1]-a[1]*b[0]]


def subtract(a, b):
    return [x-y for x, y in zip(a, b, strict=True)]


def reference_status(index):
    return "NULL_UNSUPPORTED" if index is None else "SUPPORTED_COMPARISON" if index <= 1 else "EXCEEDANCE"


def sources(pins):
    authenticate(pins)
    receipt, report, inputs, reference = (read(COMMON / name) for name in
                                         ("receipt.json", "report.json", "input-contract.json", "engineering-reference.json"))
    require(receipt["status"] == report["status"] == "COMPLETE_12_CONDITIONAL_COMMON_RECEIVER_EQUILIBRIA"
            and receipt["sources_unchanged_before_and_after"] and report["sources_unchanged_before_and_after"]
            and reference["status"] == "MATCHED" and report["coupled_equilibria_attempted"] == 12
            and report["source_sha256"] == receipt["source_sha256"] == inputs["source_sha256"], "accepted common receipt differs")
    for relative, digest in receipt["source_sha256"].items():
        bind(pins, ROOT / relative, digest)
    for name, digest in receipt["output_sha256"].items():
        path = (COMMON / name).resolve()
        require(path.parent == COMMON, "common receipt output leaves frozen attempt")
        bind(pins, path, digest)
    require(receipt["output_sha256"]["producer.py.snapshot"] == PINS[PRODUCER]
            and receipt["source_sha256"][PRODUCER.relative_to(ROOT).as_posix()] == PINS[PRODUCER], "accepted producer differs")
    authenticate(pins)
    contract, material, hardware = inputs["contract"], read(MATERIALS), read(FASTENERS)
    properties = material["conditional_DF_L_No2_base_row"]["base_properties"]
    bearing = material["dowel_bearing_scenario"]["conditional_hardware_scenario"]
    steel = hardware["material_boundaries"]["sae_j429_grade5_1_4_through_1_in"]
    require(properties["Fc_perpendicular"] == 625 and properties["Fc_parallel"] == 1350
            and bearing["D_mm"] == 6.35 and bearing["Fe_parallel_psi"] == 5600
            and bearing["Fe_perpendicular_table_rounded_psi"] == 4450
            and steel["machine_test_yield_ksi_min"] == 92
            and hardware["dimension_inputs"]["nut"]["tensile_stress_area_in2"] == 0.0318,
            "pinned material/reference convention differs")
    require(contract["model"]["bolt_E_mpa"] == 200000.0
            and contract["model"]["wood_bore_and_seat_stiffness_mpa_per_mm"] == 20.0
            and contract["model"]["head_contact_stiffness_mpa_per_mm"] == 10000.0
            and set(contract["geometry"]) == set(AXES), "accepted common model differs")
    members = {m["member_id"]: m for m in material["members"]}
    states, joins, seen = [], [], set()
    require([(r["side"], r["case_id"]) for r in report["states"]]
            == [(side, case) for side in ("left", "right") for case in CASES], "twelve state identities differ")
    for record in report["states"]:
        path = COMMON / record["path"]
        require(path.parent == COMMON and receipt["output_sha256"][path.name] == record["sha256"], "state receipt join differs")
        state = read(path)
        require(state["combined_full_wrenches_closed"] is record["combined_full_wrenches_closed"] is True
                and state["status"] == record["status"] == "CONDITIONAL_COMMON_RECEIVER_EQUILIBRIUM"
                and state["case_id"] == record["case_id"] and state["side"] == record["side"]
                and state["complete_joint_acceptance"] is False and state["physical_release"] is False
                and len(state["shafts"]) == 2, "common state identity/closure differs")
        states.append(state)
        for index, shaft in enumerate(state["shafts"]):
            axis, case = shaft["axis_id"], state["case_id"]
            key = (case, axis)
            require(key not in seen and axis in AXES and "_"+state["side"]+"_" in axis, "duplicate or foreign shaft")
            seen.add(key)
            geometry = contract["geometry"][axis]
            boundary = next(b for b in contract["boundaries"] if (b["case_id"], b["axis_id"]) == key)
            require(geometry["shaft_diameter_mm"] == 6.35 and abs(geometry["modeled_wood_grip_mm"]-215.9) <= 1e-8
                    and all(r["bore_diameter_mm"] == 7.5 for r in geometry["receivers"])
                    and [r["receiver"] for r in shaft["receivers"]] == geometry["receiver_order"]
                    and len(shaft["beam_fields"]) == 120 and len(shaft["bore_fields"]) == 72
                    and [e["end"] for e in shaft["outer_seat_fields"]] == ["head", "nut"]
                    and shaft["redistributed_tension_n"] == shaft["normal_transfer"]["single_physical_tie_n"],
                    "common shaft fields or tension join differs")
            for member, grain in zip(geometry["receiver_order"], geometry["grain_xyz"], strict=True):
                proposed = members[member]["source_proposed_longitudinal_grain_global_xyz"]
                require(norm(subtract(grain, proposed)) <= 1e-8, "accepted/material grain orientation differs")
            joins.append({"case_id": case, "side": state["side"], "axis_id": axis, "gap_scale": 1.0,
                "state_path": path.relative_to(ROOT).as_posix(), "state_sha256": record["sha256"],
                "shaft_pointer": f"#/shafts/{index}", "input_contract_sha256": PINS[COMMON / "input-contract.json"],
                "geometry_pointer": "#/contract/geometry/"+axis,
                "boundary_pointer": f"#/contract/boundaries/{contract['boundaries'].index(boundary)}",
                "source_receipt_sha256": PINS[COMMON / "receipt.json"], "source_report_sha256": PINS[COMMON / "report.json"],
                "common_producer_sha256": PINS[PRODUCER],
                "original_global_axis_tension_n": shaft["source_tension_n"],
                "demand_policy": "Use redistributed common T and saved simultaneous fields; original isolated allocations are diagnostics only."})
    require(seen == {(case, axis) for case in CASES for axis in AXES} and len(joins) == 24, "24 source joins incomplete")
    authenticate(pins)
    return {"contract": contract, "states": states, "joins": joins, "members": members,
            "references": {"yield_mpa": steel["machine_test_yield_ksi_min"]*1000*PSI_MPA,
                "steel_reference_divisor": STEEL_REFERENCE_DIVISOR,
                "thread_area_mm2": hardware["dimension_inputs"]["nut"]["tensile_stress_area_in2"]*25.4**2,
                "Fc_perpendicular_mpa": properties["Fc_perpendicular"]*PSI_MPA,
                "Fc_parallel_mpa": properties["Fc_parallel"]*PSI_MPA,
                "Fe_parallel_mpa": bearing["Fe_parallel_psi"]*PSI_MPA,
                "Fe_perpendicular_mpa": bearing["Fe_perpendicular_table_rounded_psi"]*PSI_MPA},
            "end_profile": contract["model"]["end_profile"], "catalog": hardware["dimension_inputs"]}


def orientation(normal, grain, refs):
    cosine = abs(dot(normal, grain)) / (norm(normal)*norm(grain))
    if cosine <= 1e-8:
        route, reference = "PERPENDICULAR_BASE_REFERENCE", refs["Fc_perpendicular_mpa"]
    elif abs(cosine-1) <= 1e-8:
        route, reference = "PARALLEL_BASE_REFERENCE", refs["Fc_parallel_mpa"]
    else:
        route, reference = "OBLIQUE_REFERENCE_UNAVAILABLE", None
    return {"normal_grain_abs_cosine": cosine, "grain_xyz": grain,
            "wood_reference_route": route, "wood_reference_mpa": reference,
            "material_source_sha256": PINS[MATERIALS], "reference_is_conditional": True}


def smooth_fields(shaft, geometry, boundary, join, refs):
    diameter, tension = geometry["shaft_diameter_mm"], shaft["redistributed_tension_n"]
    area, inertia = math.pi*diameter**2/4, math.pi*diameter**4/64
    n, basis = geometry["bolt_axis_xyz"], boundary["transverse_basis_xyz"]
    reference = refs["yield_mpa"] / refs["steel_reference_divisor"]
    records = []
    for index, field in enumerate(shaft["beam_fields"]):
        moment, shear = norm(field["EI_curvature_components_nmm"]), norm(field["EI_third_derivative_components_n"])
        normal_stress, shear_stress = abs(tension)/area + moment*diameter/(2*inertia), 4*shear/(3*area)
        proxy = math.hypot(normal_stress, math.sqrt(3)*shear_stress)
        v = [-sum(basis[k][c]*field["EI_third_derivative_components_n"][k] for k in range(2)) for c in range(3)]
        records.append({"case_id": join["case_id"], "axis_id": join["axis_id"], "side": join["side"],
            "element": field["element"], "x_mm": field["x_mm"], "T_n": tension, "V_n": shear, "M_nmm": moment,
            "V_on_head_side_cut_xyz_n": v, "F_on_head_side_cut_xyz_n": [tension*n[c]+v[c] for c in range(3)],
            "M_on_head_side_cut_xyz_nmm": field["physical_bending_vector_xyz_nmm"],
            "cut_point_mm": [geometry["head_seat_point_mm"][c]+field["x_mm"]*n[c] for c in range(3)],
            "sigma_axial_plus_bending_envelope_mpa": normal_stress, "tau_round_section_envelope_mpa": shear_stress,
            "smooth_vm_proxy_mpa": proxy, "conditional_yield_mpa": refs["yield_mpa"],
            "steel_reference_divisor_applied_once": refs["steel_reference_divisor"], "steel_reference_mpa": reference,
            "unfactored_yield_ratio": proxy/refs["yield_mpa"], "smooth_reference_index": proxy/reference,
            "reference_status": reference_status(proxy/reference),
            "source_field_pointer": join["shaft_pointer"]+f"/beam_fields/{index}",
            "state_sha256": join["state_sha256"], "source_join_key": [join["case_id"], join["axis_id"]]})
    return records


def pressure_wrench(field, seat, datum):
    points, forces = field["reference_points_mm"], field["point_forces_xyz_n"]
    area, pressure = field["quadrature_area_mm2"], field["pressure_mpa"]
    require(len(points) == len(forces) == len(area) == len(pressure) == 256
            and all(a > 0 and p >= 0 and math.isfinite(a) and math.isfinite(p) for a, p in zip(area, pressure, strict=True)),
            "annular field census or pressure invalid")
    force = [sum(f[c] for f in forces) for c in range(3)]
    moments = [cross(subtract(p, seat), f) for p, f in zip(points, forces, strict=True)]
    moment = [sum(m[c] for m in moments) for c in range(3)]
    saved = field["integrated_wrench_about_common_datum"]
    transported = [saved["moment_xyz_nmm"][c]+cross(subtract(datum, seat), saved["force_xyz_n"])[c] for c in range(3)]
    require(max(abs(x) for x in subtract(force, saved["force_xyz_n"])) <= 1e-7
            and max(abs(x) for x in subtract(moment, transported)) <= 1e-6, "saved annular wrench/point-force join does not close")
    full_area = sum(area)
    active_area = sum(a for a, p in zip(area, pressure, strict=True) if p > 0)
    normal_force = sum(a*p for a, p in zip(area, pressure, strict=True))
    return {"full_annulus_area_mm2": full_area, "active_area_mm2": active_area,
            "full_annulus_mean_pressure_mpa": normal_force/full_area,
            "active_area_mean_pressure_mpa": normal_force/active_area if active_area else 0.0,
            "peak_pressure_mpa": max(pressure), "force_xyz_n": force, "moment_xyz_nmm": moment,
            "datum_mm": seat, "quadrature_count": 256, "force_weights_already_included": True}


def end_reference(shaft, geometry, boundary, end_index, join, data):
    end = shaft["outer_seat_fields"][end_index]
    role, sign = ("head", 1) if end_index == 0 else ("nut", -1)
    receiver_index = 0 if end_index == 0 else 2
    member = geometry["receiver_order"][receiver_index]
    require(end["end"] == role and end["receiver"] == member, "saved end ownership differs")
    seat = geometry["head_seat_point_mm" if end_index == 0 else "nut_seat_point_mm"]
    n, basis, tension = geometry["bolt_axis_xyz"], boundary["transverse_basis_xyz"], shaft["redistributed_tension_n"]
    wood = pressure_wrench(end["point_tractions"]["wood_contact"], seat, geometry["datum_mm"])
    hardware = pressure_wrench(end["point_tractions"]["head_contact"], seat, geometry["datum_mm"])
    require(max(abs(wood["force_xyz_n"][c]-sign*tension*n[c]) for c in range(3)) <= 1e-6
            and max(abs(wood[k][c]+hardware[k][c]) for k in ("force_xyz_n", "moment_xyz_nmm") for c in range(3)) <= 1e-6
            and abs(norm(wood["moment_xyz_nmm"])-abs(end["series_contact"]["moment_nmm"])) <= 1e-6,
            "own-end wood/hardware pressure actions do not balance")
    orient = orientation(n, geometry["grain_xyz"][receiver_index], data["references"])
    reference = orient["wood_reference_mpa"]
    ratios = {name+"_over_wood_reference": wood[name+"_pressure_mpa"]/reference if reference else None
              for name in ("full_annulus_mean", "active_area_mean", "peak")}
    return {"schema": "knee_common_washer_own_end_source/v1", "obligation": "N09_SOURCE_ONLY",
        "case_id": join["case_id"], "side": join["side"], "axis_id": join["axis_id"], "gap_scale": 1.0,
        "end_role": role, "receiver_member": member, "join_key": [join["case_id"], join["axis_id"], role, member],
        "status": "COMPLETE_SAVED_COMMON_END_SOURCE", "source_join": join,
        "saved_end_pointer": join["shaft_pointer"]+f"/outer_seat_fields/{end_index}",
        "fresh_signed_T_n": tension, "normal_compression_T_n": tension, "signed_T_n": sign*tension,
        "force_on_receiver_xyz_n": wood["force_xyz_n"], "own_end_M_signed_xyz_nmm": wood["moment_xyz_nmm"],
        "own_end_M_magnitude_nmm": norm(wood["moment_xyz_nmm"]),
        "own_end_M_signed_transverse_pair_nmm": [dot(b, wood["moment_xyz_nmm"]) for b in basis],
        "physical_transverse_basis_columns_xyz": [[basis[k][c] for k in range(2)] for c in range(3)],
        "shaft_axis_head_to_nut_xyz": n, "normal_into_receiver_xyz": [sign*x for x in n],
        "end_wrench_datum_global_xyz_mm": seat, "source_axis_datum_global_xyz_mm": geometry["datum_mm"],
        "moment_on_beam_xyz_nmm": hardware["moment_xyz_nmm"],
        "pressure_recovery": {"method": "Sum saved weighted point forces; rebase moments to each own seat, no pressure/contact solve.",
                              "wood_annulus": wood, "hardware_annulus": hardware},
        "wood_orientation_reference": {**orient, "member_material_scenario": data["members"][member]["material_scenario"]},
        "wood_reference_ratios": ratios,
        "wood_mean_reference_status": reference_status(ratios["full_annulus_mean_over_wood_reference"]),
        "wood_local_peak_diagnostic_status": reference_status(ratios["peak_over_wood_reference"]),
        "saved_end_contact": end["series_contact"],
        "contact_hypotheses": {"first_order": True, "rigid_concentric_washer": True, "actual_support_mask_qualified": False,
            "preload_n": 0, "Kwood_mpa_per_mm": 20, "Khead_mpa_per_mm": 10000,
            "shaft_diameter_mm": 6.35, "bore_diameter_mm": 7.5, "wood_grip_mm": 215.9,
            "wood_contact_inner_outer_radii_mm": [data["end_profile"]["washer_ID_max_mm"]/2, data["end_profile"]["washer_OD_min_mm"]/2],
            "head_nut_contact_inner_outer_radii_mm": [data["end_profile"]["washer_ID_max_mm"]/2, data["end_profile"]["hypothetical_concentric_head_and_nut_flat_radius_mm"]],
            "catalog_washer_envelope": data["catalog"]["washer"], "catalog_source_sha256": PINS[FASTENERS]},
        **FLAGS}


def bore_references(shaft, geometry, join, refs):
    records = []
    for index, field in enumerate(shaft["bore_fields"]):
        member_index = geometry["receiver_order"].index(field["receiver"])
        grain, normal = geometry["grain_xyz"][member_index], geometry["bolt_axis_xyz"]
        force, pressure = field["force_on_wood_xyz_n"], field["pressure_mpa"]
        applicable = abs(dot(grain, normal))/(norm(grain)*norm(normal)) <= 1e-8
        theta, directional = None, None
        if applicable and norm(force) > 0:
            cosine = min(1.0, abs(dot(grain, force))/(norm(grain)*norm(force)))
            theta = math.degrees(math.acos(cosine))
            fp, fn = refs["Fe_parallel_mpa"], refs["Fe_perpendicular_mpa"]
            directional = fp*fn/(fp*(1-cosine**2)+fn*cosine**2)
        nominal = min(refs["Fe_parallel_mpa"], refs["Fe_perpendicular_mpa"]) if applicable else None
        records.append({"case_id": join["case_id"], "side": join["side"], "axis_id": join["axis_id"],
            "receiver": field["receiver"], "x_mm": field["x_mm"], "reference_point_mm": field["reference_point_mm"],
            "force_on_wood_xyz_n": force, "pressure_mpa": pressure, "radial_penetration_mm": field["radial_penetration_mm"],
            "grain_xyz": grain, "load_to_grain_angle_deg": theta, "nominal_minimum_Fe_mpa": nominal,
            "peak_pressure_over_nominal_minimum_Fe": pressure/nominal if nominal else None,
            "directional_Fe_mpa": directional, "pressure_over_directional_Fe": pressure/directional if directional else None,
            "directional_null_reason": None if directional else "UNLOADED_DIRECTION_UNDEFINED" if applicable else "END_GRAIN_REFERENCE_NOT_THIS_ROUTE",
            "nominal_full_D_comparison_applicable": applicable,
            "reference_status": reference_status(pressure/nominal if nominal else None),
            "reference_scope": "Nominal local pressure/Fe diagnostic; no three-receiver lateral-yield capacity, thread-occupancy or splitting qualification.",
            "material_source_sha256": PINS[MATERIALS], "source_join_key": [join["case_id"], join["axis_id"]],
            "source_field_pointer": join["shaft_pointer"]+f"/bore_fields/{index}", "state_sha256": join["state_sha256"]})
    return records


def peak(records, key):
    finite = [r for r in records if r[key] is not None]
    if not finite:
        return None
    return max(finite, key=lambda r: r[key])


def arithmetic(data):
    refs, contract = data["references"], data["contract"]
    smooth, bores, ends, shafts, motions = [], [], [], [], []
    joins = {(j["case_id"], j["axis_id"]): j for j in data["joins"]}
    for state in data["states"]:
        for member, pose in zip(state["receiver_order"], state["receiver_poses_t_1000theta"], strict=True):
            motions.append({"case_id": state["case_id"], "side": state["side"], "receiver": member,
                            "rotation_norm_deg": math.degrees(norm(pose[3:])/1000),
                            "translation_norm_mm": norm(pose[:3]), "datum_mm": state["reference_origin_mm"],
                            "first_order_only": True, "finite_rotation_rechecked": False})
        for shaft in state["shafts"]:
            axis, case = shaft["axis_id"], state["case_id"]
            geometry, join = contract["geometry"][axis], joins[case, axis]
            boundary = next(b for b in contract["boundaries"] if (b["case_id"], b["axis_id"]) == (case, axis))
            fields = smooth_fields(shaft, geometry, boundary, join, refs)
            smooth.extend(fields)
            bore = bore_references(shaft, geometry, join, refs)
            bores.extend(bore)
            own_ends = [end_reference(shaft, geometry, boundary, i, join, data) for i in (0, 1)]
            ends.extend(own_ends)
            thread_stress = max(shaft["redistributed_tension_n"], 0)/refs["thread_area_mm2"]
            thread_index = thread_stress/(refs["yield_mpa"]/refs["steel_reference_divisor"])
            strongest = peak(fields, "smooth_reference_index")
            shafts.append({"schema": "knee_common_shaft_reference/v1", "case_id": case, "axis_id": axis,
                "side": state["side"], "source_join": join, "redistributed_T_n": shaft["redistributed_tension_n"],
                "smooth_peak_same_state_same_position": strongest, "smooth_status": strongest["reference_status"],
                "nominal_thread_tension": {"T_n": shaft["redistributed_tension_n"], "nominal_tensile_area_mm2": refs["thread_area_mm2"],
                    "stress_mpa": thread_stress, "conditional_yield_mpa": refs["yield_mpa"],
                    "steel_reference_divisor_applied_once": refs["steel_reference_divisor"],
                    "reference_mpa": refs["yield_mpa"]/refs["steel_reference_divisor"],
                    "unfactored_yield_ratio": thread_stress/refs["yield_mpa"], "reference_index": thread_index,
                    "status": reference_status(thread_index), "combined_with_smooth_bending_or_shear": False,
                    "delivered_thread_root_qualified": False, "area_source_sha256": PINS[FASTENERS]},
                "bore_receiver_diagnostics": [peak([r for r in bore if r["receiver"] == member], "peak_pressure_over_nominal_minimum_Fe")
                                              for member in geometry["receiver_order"]],
                "own_end_join_keys": [e["join_key"] for e in own_ends], **FLAGS})
    require(len(shafts) == 24 and len(ends) == 48 and len(smooth) == 2880 and len(bores) == 1728,
            "arithmetic field coverage incomplete")
    return {"shafts": shafts, "smooth": smooth, "bores": bores, "ends": ends, "motions": motions}


def execute(output, *, calculate):
    output = Path(output).resolve()
    require(output.parent == RAW.resolve() and not output.exists(), "use a fresh immediate owned output child")
    output.mkdir(parents=True, exist_ok=False)
    (output / ".gitignore").write_text("*\n")
    (output / "producer.py.snapshot").write_bytes(Path(__file__).read_bytes())
    pins = {**PINS, Path(__file__).resolve(): sha(Path(__file__))}
    summary = {"schema": "knee_common_references/v1", "status": "STOP_SOURCE_OR_ARITHMETIC",
               "mode": "build" if calculate else "prepare", "saved_field_arithmetic_executed": False,
               "limits": LIMITS, "source_common_receipt_sha256": PINS[COMMON / "receipt.json"],
               "source_common_report_sha256": PINS[COMMON / "report.json"],
               "scope": "Only four existing side shafts in six nominal cases; own-end export supplies demands, not N09 completion.",
               **FLAGS}
    try:
        data = sources(pins)
        summary.update(references=data["references"], prepared_source_join_count=len(data["joins"]),
                       required_counts={"shaft_states": 24, "smooth_samples": 2880, "bore_samples": 1728, "own_ends": 48})
        lines(output / "source-joins.jsonl", data["joins"])
        if calculate:
            summary["saved_field_arithmetic_executed"] = True
            results = arithmetic(data)
            for name, key in (("shaft-references.jsonl", "shafts"), ("smooth-fields.jsonl", "smooth"),
                              ("bore-fields.jsonl", "bores"), ("washer-ends.jsonl", "ends")):
                lines(output / name, results[key])
            smooth = peak(results["smooth"], "smooth_reference_index")
            thread = max(results["shafts"], key=lambda r: r["nominal_thread_tension"]["reference_index"])
            summary.update(status="COMPLETE_SAVED_COMMON_REFERENCE_COMPARISONS",
                counts={"shaft_states": len(results["shafts"]), "smooth_samples": len(results["smooth"]),
                        "bore_samples": len(results["bores"]), "own_ends": len(results["ends"])},
                peak_smooth=smooth, peak_nominal_thread=thread,
                peak_wood_mean=max(results["ends"], key=lambda r: r["wood_reference_ratios"]["full_annulus_mean_over_wood_reference"] or 0),
                peak_wood_local_pressure=max(results["ends"], key=lambda r: r["wood_reference_ratios"]["peak_over_wood_reference"] or 0),
                peak_bore_nominal=peak(results["bores"], "peak_pressure_over_nominal_minimum_Fe"),
                peak_shared_pose_rotation=peak(results["motions"], "rotation_norm_deg"),
                smooth_exceedances=[{"case_id": r["case_id"], "axis_id": r["axis_id"],
                                     "index": r["smooth_peak_same_state_same_position"]["smooth_reference_index"]}
                                    for r in results["shafts"] if r["smooth_status"] == "EXCEEDANCE"],
                thread_exceedances=[{"case_id": r["case_id"], "axis_id": r["axis_id"],
                                     "index": r["nominal_thread_tension"]["reference_index"]}
                                    for r in results["shafts"] if r["nominal_thread_tension"]["status"] == "EXCEEDANCE"],
                wood_reference_nulls=[e["join_key"] for e in results["ends"] if e["wood_orientation_reference"]["wood_reference_mpa"] is None],
                wood_mean_exceedances=[e["join_key"] for e in results["ends"] if e["wood_mean_reference_status"] == "EXCEEDANCE"],
                wood_peak_diagnostic_exceedances=[e["join_key"] for e in results["ends"] if e["wood_local_peak_diagnostic_status"] == "EXCEEDANCE"],
                bore_reference_null_count=sum(r["nominal_minimum_Fe_mpa"] is None for r in results["bores"]))
            if summary["wood_reference_nulls"] or summary["bore_reference_null_count"]:
                summary["status"] = "PARTIAL_NULL_COMMON_REFERENCES"
        else:
            summary["status"] = "PREPARED_SAVED_COMMON_REFERENCE_API"
    except (ValueError, KeyError, OSError, ArithmeticError) as error:
        summary["status"] = "STOP_SOURCE_OR_ARITHMETIC"
        summary["failure"] = {"type": type(error).__name__, "detail": str(error)}
    try:
        authenticate(pins)
        summary["sources_unchanged_before_and_after"] = True
    except (ValueError, OSError) as error:
        summary["status"] = "STOP_SOURCE_OR_ARITHMETIC"
        summary["sources_unchanged_before_and_after"] = False
        summary["source_failure"] = str(error)
    write(output / "sources.json", source_map(pins))
    write(output / "summary.json", summary)
    receipt = {"schema": "knee_common_references_receipt/v1", "status": summary["status"],
               "producer_sha256": pins[Path(__file__).resolve()], "source_sha256": source_map(pins),
               "output_sha256": {p.name: sha(p) for p in sorted(output.iterdir()) if p.is_file()},
               "sources_unchanged_before_and_after": summary["sources_unchanged_before_and_after"], **FLAGS}
    write(output / "receipt.json", receipt)
    return summary


def prepare(output):
    """Authenticate saved source fields and identities without reference arithmetic."""
    return execute(output, calculate=False)


def build(output):
    """Parent-only stdlib saved-field reference arithmetic and own-end export."""
    return execute(output, calculate=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--build", action="store_true", help="Parent-only arithmetic; default authenticates/prepares only.")
    args = parser.parse_args()
    result = build(args.output) if args.build else prepare(args.output)
    print(result["status"])
    raise SystemExit(0 if result["status"].startswith(("PREPARED_", "COMPLETE_")) else 2)
