"""Independent saved-action scalar audit; never call gate, reader or response.

Only the admitted source-owned half-strip and circle comparisons are reviewed.
No q, CAD, K, native, candidate solve or other component reduction is evaluated.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import platform
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]
OWN = Path(__file__).resolve()
LEAF = "fea/generated/thin-bolted-current-contact-v1/eoere-successor-v1"
FIELD = LEAF + "/a12-first-order-v2/field.json"
COMPONENT = LEAF + "/a12-first-order-v2/components-v3.json"
ADMISSION = LEAF + "/a12-first-order-v2/admission-v3.json"
GATE = LEAF + "/four-port-method-v1/first_order_admission_v3.py"
METHOD_REVIEW = LEAF + "/raw-angle-review-v1/independent-component-method-review.json"
GEOMETRY = LEAF + "/occupied-geometry-v2-complete/geometry.json"
SCENE = LEAF + "/occupied-geometry-v2-complete/scene.json"
INPUT = LEAF + "/four-port-method-v1/inputs.json"
DIRECT = {
    FIELD: "dad00e84ae98333beeb89a0c2403d48d9f40e9189c4525fc3746b8b3118de598",
    COMPONENT: "03e04dc47bb7b7705463d1883be9b18e76d8401d2e91cea2733517c5ef423d21",
    ADMISSION: "383772d00e6f6c9207a833f5a9a067b6eaa1ca01279eb367c6ef518e41f77ee0",
    GATE: "a32992a3a5f4fb8c16a0402ad522b938650d8744200ca4d8a28dfd38e07a0008",
    METHOD_REVIEW: "b359b424b1aa1871cb3c65c09d402b4f9074d698b1da8200f9f323cc5014fd85",
    GEOMETRY: "05baab7ffdd329c3240a1770cf3539e321ab47d5cd2bc6354f8fceb6db8a0efd",
    SCENE: "8599fca392ccf2ec366ab4c39e4c1d74be89da50167edc7c760e5cb73c524c4a",
    INPUT: "a938b41e53f5708c74e30ec1f021e894513ab6be4b1c6df390bababcfeebbd8e",
    LEAF + "/steel-shaft-comparison-v1/comparison.py": "9d670f264d5b074abf4cbd48baaebde486b1c15e3ddb612302bd1f41a577a360",
    LEAF + "/steel-shaft-comparison-v1/test_comparison.py": "7e14df56a8265f8f9b705f09a74249d4f19fa8f878555b3ead0c127e28240afb",
    LEAF + "/steel-shaft-comparison-v1/plan.json": "ffa8b5022faffae40ee44140a8cfade7c257dd7a4f84dd98f89251c7ccf0467c",
}
STATE = "eoere-a12-2cc47f73f1c898d9663dd319"
PORTS = ("arm-x/far-minus", "arm-x/far-plus", "arm-z/far-minus", "arm-z/far-plus")


def require(ok, label):
    if not ok:
        raise ValueError(label)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def canonical(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()).hexdigest()


def verify(pins):
    for path, digest in pins.items():
        require(sha(ROOT/path) == digest, "source changed: " + path)


def join(pins, additions):
    for path, digest in additions.items():
        require(path not in pins or pins[path] == digest, "contradictory pin: " + path)
        pins[path] = digest


def v(value, n=3):
    require(len(value) == n and all(isinstance(x, (int, float)) and math.isfinite(x) for x in value), "finite complete saved vector required")
    return [float(x) for x in value]


def add(a, b):
    return [x+y for x, y in zip(a, b, strict=True)]


def sub(a, b):
    return [x-y for x, y in zip(a, b, strict=True)]


def scale(a, k):
    return [k*x for x in a]


def dot(a, b):
    return math.fsum(x*y for x, y in zip(a, b, strict=True))


def cross(a, b):
    return [a[1]*b[2]-a[2]*b[1], a[2]*b[0]-a[0]*b[2], a[0]*b[1]-a[1]*b[0]]


def unit(a):
    length = math.sqrt(dot(a, a))
    require(length > 0., "nonzero axis required")
    return scale(a, 1/length)


def unique(rows, key):
    out = {r[key]: r for r in rows}
    require(len(out) == len(rows), "duplicate own identity: " + key)
    return out


def proper(columns):
    require(len(columns) == 3, "three supplied basis columns required")
    for i, a in enumerate(columns):
        v(a)
        for j, b in enumerate(columns):
            require(abs(dot(a, b)-(i == j)) < 1e-10, "supplied chart is not orthogonal")
    require(abs(dot(columns[0], cross(columns[1], columns[2]))-1) < 1e-10, "supplied chart is not proper")


def local(columns, world):
    return [dot(a, world) for a in columns]


def metrics():
    return {k: 0. for k in ("datum_mm", "force_n", "moment_nmm", "strip_vm_mpa", "circle_vm_mpa", "J_lower_mm4", "root_port_force_balance_n", "root_port_moment_balance_nmm", "flange_transport_n_nmm", "collector_balance_n_nmm")}


def near(observed, expected, key, errors, tolerance):
    delta = max(abs(a-b) for a, b in zip(v(observed, len(expected)), v(expected, len(expected)), strict=True))
    errors[key] = max(errors[key], delta)
    require(delta <= tolerance, "saved scalar/vector mismatch: " + key)


def rectangle_J_lower(b=44.45, t=6.35):
    partial = math.fsum(math.tanh(n*math.pi*b/(2*t))/n**5 for n in range(1, 128, 2))
    tail = 1/129**5+1/(8*129**4)
    low = b*t**3/3*(1-192*t/(math.pi**5*b)*(partial+tail))
    return low*(1-32*2**-52)


def strip_value(force, moment, J):
    A = 44.45*6.35
    normal = abs(force[0])/A+abs(moment[1])/(44.45*6.35**2/6)+abs(moment[2])/(6.35*44.45**2/6)
    shear = 1.5*math.hypot(force[1], force[2])/A
    torsion = abs(moment[0])*6.35/J
    return normal, shear, torsion, math.hypot(normal, math.sqrt(3)*(shear+torsion))


def circle_value(action, d):
    N, Vy, Vz, T, My, Mz = v(action, 6)
    A = math.pi*d*d/4
    normal = abs(N)/A+32*math.hypot(My, Mz)/(math.pi*d**3)
    shear = 4*math.hypot(Vy, Vz)/(3*A)+16*abs(T)/(math.pi*d**3)
    return math.hypot(normal, math.sqrt(3)*shear)


def review():
    direct = {**DIRECT, str(OWN.relative_to(ROOT)): sha(OWN)}
    verify(direct)
    field, receipt, component, method, geometry, scene, inputs = [json.loads((ROOT/p).read_bytes()) for p in (FIELD, ADMISSION, COMPONENT, METHOD_REVIEW, GEOMETRY, SCENE, INPUT)]
    require(receipt["schema"] == "eoere_first_order_independent_field_admission/v1"
        and receipt["independent_eoere_original_law_gradient_work_and_equilibrium_checks_pass"] is True
        and receipt["source_path"] == GATE and receipt["admission_source_sha256"] == DIRECT[GATE]
        and receipt["input_raw_sha256"] == DIRECT[FIELD] and receipt["input_canonical_sha256"] == canonical(field), "actual issued admission binding failed")
    require(component["schema"] == "eoere_same_state_conditional_component_receipt/v1"
        and component["raw_field_sha256"] == DIRECT[FIELD] and component["field_admission_receipt_sha256"] == DIRECT[ADMISSION]
        and component["fresh_gate_sha256"] == DIRECT[GATE], "actual component input binding failed")
    require(method["independent_component_method_checks_pass"] is True and len(method["source_sha256"]) == 165, "prior165-pin method review differs")
    for obj in (field, receipt, component):
        require((obj["state_id"], obj["case_id"], obj["accessory_placement"]) == (STATE, "a12-rear", "retained-original-top-hold"), "actual current-state label differs")
        require(all(x is False for x in obj["release"].values()), "release flag changed")
    pins = dict(direct)
    maps = {FIELD: field, ADMISSION: receipt, COMPONENT: component, METHOD_REVIEW: method, GEOMETRY: geometry}
    for obj in maps.values():
        join(pins, obj["source_sha256"])
    verify(pins)
    source = field["source_inputs"]
    require(component["source_sha256"][LEAF+"/steel-shaft-comparison-v1/comparison.py"] == DIRECT[LEAF+"/steel-shaft-comparison-v1/comparison.py"], "actual frozen comparison helper not bound")
    for table in ("four_port_fitting_actions", "common_shaft_section_cut_actions"):
        digest = canonical(field[table])
        require(receipt["table_canonical_sha256"][table] == component["enclosed_unlabeled_recovery_table_canonical_sha256"][table] == digest,
                "actual enclosed action table differs")
    recovery = unique(field["four_port_fitting_actions"], "body")
    descriptors = unique(field["fitting_operator_descriptors"], "body")
    poses = unique(source["fitting_poses"], "id")
    occupied = unique([r for r in scene["solids"] if r["fabrication"]["kind"] == "bracket"], "id")
    saved = unique(component["component_reductions"]["angle_duties"], "body")
    require(len(recovery) == 22 and set(recovery) == set(descriptors) == set(poses) == set(occupied) == set(saved), "all22 own fittings differ")
    bindings = source["fitting_port_bindings"]
    require(len(bindings) == len({(r["angle_id"], r["model_port_id"]) for r in bindings}) == 88,
            "all88 source fitting/shaft bindings required")
    error = metrics()
    J = rectangle_J_lower()
    all_ends, per_fitting = [], []
    for body, rec in recovery.items():
        desc, out, pose = descriptors[body], saved[body]["loaded_strip_comparison"], poses[body]
        require(out["body"] == body and out["physical_product_fy_mpa"] is out["conditional_fy_mpa"] is out["material_basis"] is out["fy_scenario_id"] is None
                and out["full_flange_aggregate_stress_comparison"] is None and out["complete_joint_acceptance"] is False, "fitting material/aggregate claim changed")
        bound = unique([r for r in bindings if r["angle_id"] == body], "model_port_id")
        require(set(bound) == set(PORTS) and saved[body]["physical_axis_ids"] == sorted(r["axis_id"] for r in bound.values()),
                "own four-port physical shaft ownership differs")
        data = desc["own_fitting_scenario"]
        require({k: val for k, val in data.items() if k not in ("heel_reference_xyz_mm", "fitting_basis_columns_xyz")} ==
                {k: val for k, val in inputs.items() if k not in ("heel_reference_xyz_mm", "fitting_basis_columns_xyz")}, "own inch scenario differs")
        require(desc["scenario_canonical_sha256"] == canonical(data) and desc["immutable_operator_snapshot_sha256"] == rec["immutable_operator_snapshot_sha256"]
                and desc["source_sha256"] == rec["source_sha256"] and rec["root_recovery_uses_loaded_heel"] is True
                and rec["frozen_unloaded_model_response_used_for_gravity"] is False, "own loaded operator/scenario join failed")
        Q = [list(column) for column in zip(*data["fitting_basis_columns_xyz"], strict=True)]
        proper(Q)
        t = occupied[body]["transform"]
        u = unit(t[:3]); vv = t[4:7]; vv = unit(sub(vv, scale(u, dot(vv, u)))); w = cross(u, vv)
        for a, b in zip(Q, (u, scale(w, -1), vv), strict=True):
            near(a, b, "datum_mm", error, 1e-12)
        origin = v(data["heel_reference_xyz_mm"])
        near(origin, t[12:15], "datum_mm", error, 1e-8)
        near(origin, pose["origin_xyz_mm"], "datum_mm", error, 1e-8)
        require(saved[body]["duty_id"] == pose["duty_id"], "own duty identity differs")
        roots, ports = unique(rec["strip_root_actions"], "port_id"), unique(rec["port_actions"], "port_id")
        strips = unique(out["strips"], "port_id")
        require(set(roots) == set(ports) == set(strips) == set(PORTS), "four unique own strips required")
        flanges = {arm: [0.]*6 for arm in ("arm-x", "arm-z")}
        own_ends = []
        for port_id in PORTS:
            arm, side = port_id.split("/"); sign = -1 if side == "far-minus" else 1
            along = Q[0] if arm == "arm-x" else Q[2]
            basis = [along, Q[1], cross(along, Q[1])]
            root = add(origin, scale(Q[1], sign*22.225))
            tip = add(root, scale(along, 65.0875))
            hole = add(add(origin, scale(along, 65.0875)), scale(Q[1], sign*25.4))
            r, p, s = roots[port_id], ports[port_id], strips[port_id]
            require(r["body"] == p["body"] == body and r["flange"] == s["flange"] == arm
                    and (s["strip_width_mm"], s["thickness_mm"], s["interval_length_mm"]) == (44.45, 6.35, 65.0875)
                    and s["all_factory_holes_filled_in_nominal_field"] is True and s["actual_holed_strip_field_bound"] is False, "own half-strip scope changed")
            near(r["point_xyz_mm"], root, "datum_mm", error, 1e-8); near(p["point_xyz_mm"], hole, "datum_mm", error, 1e-8)
            near(bound[port_id]["entry_xyz_mm"], hole, "datum_mm", error, 1e-7)
            for a, b in zip(zip(*s["basis_columns_xyz"], strict=True), basis, strict=True):
                near(a, b, "datum_mm", error, 1e-12)
            F, M = v(r["applied_to_strip_force_xyz_n"]), v(r["applied_to_strip_couple_at_root_xyz_nmm"])
            fp, mp = v(p["external_force_required_at_port_xyz_n"]), v(p["external_couple_required_at_port_xyz_nmm"])
            near(add(F, fp), [0.]*3, "root_port_force_balance_n", error, 1e-7)
            near(add(add(M, mp), cross(sub(hole, root), fp)), [0.]*3, "root_port_moment_balance_nmm", error, 1e-4)
            flanges[arm] = add(flanges[arm], F+add(M, cross(sub(root, origin), F)))
            endpoints = unique(s["same_strip_endpoint_witnesses"], "cut_id")
            require(set(endpoints) == {"root", "neutral-tip"}, "own two endpoints required")
            values = []
            for label, point in (("root", root), ("neutral-tip", tip)):
                cut = endpoints[label]
                f, m = local(basis, F), local(basis, add(M, cross(sub(root, point), F)))
                near(cut["point_xyz_mm"], point, "datum_mm", error, 1e-8)
                near(cut["same_section_force_N_V1_V2_n"], f, "force_n", error, 1e-8)
                near(cut["same_section_moment_T_M1_M2_nmm"], m, "moment_nmm", error, 1e-5)
                numbers = strip_value(f, m, J)
                for key, expected in zip(("nominal_normal_stress_bound_mpa", "nominal_transverse_shear_norm_bound_mpa", "nominal_torsion_shear_norm_bound_mpa", "simultaneous_nominal_vm_bound_mpa"), numbers, strict=True):
                    near([cut[key]], [expected], "strip_vm_mpa", error, 1e-9)
                near([cut["torsion_rectangle"]["J_lower_mm4"]], [J], "J_lower_mm4", error, 1e-9)
                require(cut["specified_fy_mpa"] is cut["simultaneous_nominal_first_yield_bound_index"] is None
                        and cut["physical_fitting_strength_or_complete_joint_acceptance"] is False
                        and cut["removed_chord_mm"] == 0. and cut["section_scenario"] == "gross_rectangle"
                        and (cut["torsion_rectangle"]["long_side_mm"], cut["torsion_rectangle"]["short_side_mm"], cut["torsion_rectangle"]["series_terms"]) == (44.45, 6.35, 64)
                        and cut["torsion_rectangle"]["polar_second_moment_substituted_for_J"] is False, "fitting yield or section scope acquired")
                values.append(cut)
                own_ends.append({"body": body, "port_id": port_id, "cut_id": label, "width_mm": 44.45, "thickness_mm": 6.35, "point_xyz_mm": point,
                    "same_cut_force_N_V1_V2_n": f, "same_cut_moment_T_M1_M2_nmm": m,
                    "normal_stress_envelope_mpa": numbers[0], "transverse_shear_envelope_mpa": numbers[1], "torsion_shear_envelope_mpa": numbers[2], "vm_envelope_mpa": numbers[3]})
            gov = max(values, key=lambda a: a["simultaneous_nominal_vm_bound_mpa"])
            require(canonical(gov) == canonical(s["nominal_gross_prismatic_field_governing_endpoint"]), "strip governing endpoint differs")
        for arm, resultant in flanges.items():
            near(rec["per_flange_applied_strip_root_wrench_about_heel_n_nmm"][arm], resultant, "flange_transport_n_nmm", error, 1e-4)
            near(out["flange_root_resultants_diagnostic_only_n_nmm"][arm], resultant, "flange_transport_n_nmm", error, 1e-4)
        near(add(flanges["arm-x"], flanges["arm-z"]), rec["load_projection"]["heel_wrench_n_nmm"], "collector_balance_n_nmm", error, 1e-4)
        all_ends.extend(own_ends)
        top = max(own_ends, key=lambda a: a["vm_envelope_mpa"])
        per_fitting.append([body, top["port_id"], top["cut_id"], top["vm_envelope_mpa"]])
    axes = unique(geometry["axes"], "id")
    raw_shafts = unique(field["common_shaft_section_cut_actions"], "axis_id")
    source_shafts = unique(source["shafts"], "axis_id")
    circles = unique(component["component_reductions"]["own_shaft_circle_comparisons"], "axis_id")
    require(len(axes) == 100 and set(axes) == set(raw_shafts) == set(source_shafts) == set(circles), "all100 own shafts differ")
    diameters, cut_count, witnesses = Counter(), 0, []
    for axis_id, axis in axes.items():
        row, result = raw_shafts[axis_id], circles[axis_id]
        d = axis["diameter_mm"]; diameters[d] += 1
        require(d in (9.525, 12.7) and row["body"] == result["body"] == "shaft/"+axis_id
            and row["elastic_section_diameter_mm"] == row["bearing_contact_major_diameter_mm"] == d
            and canonical(source_shafts[axis_id]["source_axis"]) == canonical(axis)
            and row["body_root_and_delivered_shank_exposure_adopted"] is False
            and row["point_gravity_role_centroids_preserved"] is True, "own shaft source/diameter differs")
        for key in ("conditional_fy_mpa", "material_basis", "fy_scenario_id"):
            require(result[key] is None, "bolt grade/Fy acquired")
        require(result["complete_joint_acceptance"] is result["actual_thread_root_or_occupancy_adopted"] is result["NDS_fyb_inferred_from_tensile_yield"] is False
                and len(result["section_scenarios"]) == 1, "shaft comparison scope differs")
        section = result["section_scenarios"][0]
        require(section["section_scenario"]["id"] == "nominal_model_circle" and section["section_scenario"]["diameter_mm"] == d, "nominal circle differs")
        proper(row["basis_axis_tangent1_tangent2_xyz"])
        direction = unit(v(axis["direction_xyz"]))
        near(row["axis_point_xyz_mm"], axis["point_xyz_mm"], "datum_mm", error, 1e-8)
        near(row["axis_direction_xyz"], direction, "datum_mm", error, 1e-10)
        near(row["basis_axis_tangent1_tangent2_xyz"][0], direction, "datum_mm", error, 1e-10)
        cuts = unique(row["cuts"], "station_from_axis_point_mm")
        require(len(cuts) == section["sample_count"] and cuts, "own shaft cut census differs")
        cut_count += len(cuts)
        low, high = v(row["shaft_interval_from_axis_point_mm"], 2)
        all_values = []
        for station, cut in cuts.items():
            require(low <= station <= high, "cut outside own source interval")
            near(cut["point_xyz_mm"], add(v(axis["point_xyz_mm"]), scale(direction, station)), "datum_mm", error, 1e-7)
            all_values.append(circle_value(cut["local_N_V1_V2_T_M1_M2_n_nmm"], d))
        gov = section["sampled_governing_same_cut"]
        raw = cuts[gov["station_from_axis_point_mm"]]
        require(canonical(raw["point_xyz_mm"]) == canonical(gov["point_xyz_mm"])
            and canonical(raw["local_N_V1_V2_T_M1_M2_n_nmm"]) == canonical(gov["same_cut_N_V1_V2_T_M1_M2_n_nmm"]), "governing cut is not own fresh signed cut")
        own_value = circle_value(raw["local_N_V1_V2_T_M1_M2_n_nmm"], d)
        near([gov["same_section_nominal_stress_envelope_mpa"]], [own_value], "circle_vm_mpa", error, 1e-9)
        near([gov["same_section_nominal_stress_envelope_mpa"]], [max(all_values)], "circle_vm_mpa", error, 1e-9)
        require(gov["same_section_nominal_first_yield_index"] is None and gov["direct_reference"]["status"] == "unresolved", "shaft yield comparison acquired")
        witnesses.append({"axis_id": axis_id, "body": row["body"], "diameter_mm": d, "sample_count": len(cuts),
            "station_from_axis_point_mm": gov["station_from_axis_point_mm"], "point_xyz_mm": gov["point_xyz_mm"],
            "same_cut_N_V1_V2_T_M1_M2_n_nmm": gov["same_cut_N_V1_V2_T_M1_M2_n_nmm"], "vm_envelope_mpa": own_value})
    require(diameters == {9.525: 96, 12.7: 4} and len(all_ends) == 176 and cut_count == 5908, "exact production comparison census differs")
    verify(pins)
    return {"schema": "eoere_actual_same_state_steel_shaft_independent_review/v1", "status": "PASS_SAVED_ACTION_SCALAR_AUDIT",
        "independent_steel_shaft_saved_action_checks_pass": True, "state_id": STATE, "case_id": field["case_id"], "accessory_placement": field["accessory_placement"],
        "source_sha256": direct, "verified_referenced_source_maps": {p: {"raw_sha256": direct[p], "pin_count": len(o["source_sha256"])} for p, o in maps.items()},
        "source_pin_union_count": len(pins), "source_pin_union_canonical_sha256": canonical(pins), "source_pins_before_after_unchanged": True,
        "admitted_field_raw_sha256": DIRECT[FIELD], "admitted_field_canonical_sha256": receipt["input_canonical_sha256"],
        "saved_issued_admission_authenticated_not_rerun": True, "enclosed_action_table_canonical_sha256": component["enclosed_unlabeled_recovery_table_canonical_sha256"],
        "census": {"fittings": 22, "independent_half_strips": 88, "own_endpoint_witnesses": 176, "physical_shafts": 100, "nominal_9p525_mm": 96, "nominal_12p7_mm": 4, "own_signed_shaft_cuts": cut_count},
        "maximum_independent_arithmetic_errors": error, "rectangle_J_lower_mm4": J,
        "governing_half_strip": max(all_ends, key=lambda a: a["vm_envelope_mpa"]), "per_fitting_maximum_rows_body_port_cut_vm_mpa": sorted(per_fitting),
        "governing_nominal_circle": max(witnesses, key=lambda a: a["vm_envelope_mpa"]),
        "governing_by_nominal_diameter": {str(d): max((w for w in witnesses if w["diameter_mm"] == d), key=lambda a: a["vm_envelope_mpa"]) for d in (9.525, 12.7)},
        "fitting_Fy_Fu_bolt_grade_and_first_yield_ratios": None,
        "limits": ["These are same admitted first-order spring-model action comparisons, not physical demand bounds.",
            "Half-strip gross fields fill all holes and omit actual formed heel/radius/thinning/warping/interstrip plate continuity/local introduction/contact/prying; aggregate flange cancellation is not a strip strength check.",
            "Constant unloaded prismatic strip nominal envelope is convex along the root-to-tip interval; endpoint maxima bound only this declared field.",
            "Circular comparisons are sampled same-cut nominal circles; delivered shank/threadroot/occupancy, notches, head/nut/stripping/washer seats and continuous extrema are unqualified.",
            "E200000MPa is an elastic scenario, product Fy/Fu and bolt grade remain unknown. No blanket factor, ASD allowable, product strength, complete-joint or construction release."],
        "other_components_reviewed_here": False, "q_CAD_K_native_gate_consumer_or_solve_executed": False, "release": component["release"],
        "execution": {"sys_orig_argv": sys.orig_argv, "python": platform.python_version(), "independent_math": "Python stdlib scalar math; no model imports"},
        "reproduction_command": "uv run python "+str(OWN.relative_to(ROOT))+" --out /tmp/eoere-actual-steel-shaft-review-replay.json"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    report = review()
    with args.out.open("x") as stream:
        json.dump(report, stream, indent=2, allow_nan=False)
        stream.write("\n")
    print(json.dumps({"path": str(args.out), "sha256": sha(args.out), "bytes": args.out.stat().st_size,
                      "status": report["status"], "source_pin_union_count": report["source_pin_union_count"],
                      "half_strip_vm_mpa": report["governing_half_strip"]["vm_envelope_mpa"], "circle_vm_mpa": report["governing_nominal_circle"]["vm_envelope_mpa"]}))


if __name__ == "__main__":
    main()
