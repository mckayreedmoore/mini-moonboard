"""Saved component joins and independent scalar arithmetic; no model reduction call."""
from __future__ import annotations

import argparse
import collections
import hashlib
import importlib.util
import json
import math
import os
import platform
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[5]
OWN = Path(__file__).resolve()
LOADED_SHA = hashlib.sha256(OWN.read_bytes()).hexdigest()
LEAF = "fea/generated/thin-bolted-current-contact-v1/eoere-successor-v1"
REVIEW = LEAF + "/raw-angle-review-v1/"
RUN = LEAF + "/a12-first-order-v2/"
FIELD = RUN + "field.json"
ADMISSION = RUN + "admission-v3.json"
OUTPUT = RUN + "components-v3.json"
GATE = LEAF + "/four-port-method-v1/first_order_admission_v3.py"
FROZEN = {
    OUTPUT: "03e04dc47bb7b7705463d1883be9b18e76d8401d2e91cea2733517c5ef423d21",
    FIELD: "dad00e84ae98333beeb89a0c2403d48d9f40e9189c4525fc3746b8b3118de598",
    ADMISSION: "383772d00e6f6c9207a833f5a9a067b6eaa1ca01279eb367c6ef518e41f77ee0",
    GATE: "a32992a3a5f4fb8c16a0402ad522b938650d8744200ca4d8a28dfd38e07a0008",
    REVIEW + "independent-ordered-component-gate-review.json": "1a8060734eea71e53eaed1089c5f18ae4f8a1da034b3ed8d02a796ef05c47c8f",
    LEAF + "/component-method-v1/gross_members.py": "01aaf22c8b2cf93430e7bbce4768260efea39bed3d527b8f5486ba4e38e32258",
    RUN + "audit_steel_shafts.py": "052b7a59d172a7fc0603bcf6aa68e3a9ac10579dbd07b8ed4bae79ad8af75016",
}
ERRORS = collections.defaultdict(float)


def require(ok, label):
    if not ok:
        raise ValueError(label)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def canonical(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()).hexdigest()


def join(pins, extra):
    for path, digest in extra.items():
        require(path not in pins or pins[path] == digest, "contradictory actual component pin")
        pins[path] = digest


def verify(pins):
    for path, digest in pins.items():
        require(sha(ROOT/path) == digest, "actual component source changed: " + path)


def close(actual, expected, label, tolerance=1e-8):
    a, b = np.asarray(actual, dtype=float), np.asarray(expected, dtype=float)
    require(a.shape == b.shape and np.isfinite(a).all() and np.isfinite(b).all(), label + " finite shape")
    error = float(np.max(abs(a-b), initial=0.))
    ERRORS[label] = max(ERRORS[label], error)
    require(error <= tolerance, label + " exceeds tolerance: " + str(error))


def indexed(rows, key):
    result = {r[key]: r for r in rows}
    require(len(result) == len(rows), "duplicate actual own row: " + key)
    return result


def load(relative, name):
    spec = importlib.util.spec_from_file_location(name, ROOT/relative)
    result = importlib.util.module_from_spec(spec)
    sys.modules[name] = result
    spec.loader.exec_module(result)
    return result


def provenance(component, field, receipt):
    require(component["schema"] == "eoere_same_state_conditional_component_receipt/v1" and
            component["disposition"] == "SAME_NEW_STATE_CONDITIONAL_COMPONENT_FINDINGS", "current component scope")
    for key in ("state_id", "case_id", "accessory_placement"):
        require(component[key] == field[key] == receipt[key], "mixed actual component identity")
    require(component["state_id"] == "eoere-a12-2cc47f73f1c898d9663dd319" and
            component["raw_field_sha256"] == FROZEN[FIELD] and
            component["field_admission_receipt_sha256"] == FROZEN[ADMISSION] and
            component["fresh_gate_sha256"] == FROZEN[GATE] and component["release"] == field["release"] == receipt["release"] and
            not any(component["release"].values()), "raw/admission/source/release binding")
    require(component["enclosed_unlabeled_recovery_table_canonical_sha256"] == {key: canonical(field[key]) for key in
            ("four_port_fitting_actions", "common_shaft_section_cut_actions")}, "same unlabeled recovery bytes")
    expected = {"consumer_gate_path_adapter": ("corrected_gate.py", "42c2ae96e2f25e7fb16cbdd3cfe390a620c312bfe9db072d2363bd559e9b35cc"),
                "consumer_order_gate_path_adapter": ("ordered_gate.py", "b0e1f9f5f894faf0630cf7f6100b0dda75a00e00f840384241d4591788ab88ba")}
    for key, (name, digest) in expected.items():
        row = component[key]
        require(row["actual_gate_path"] == GATE and row["actual_gate_sha256"] == FROZEN[GATE]
                and row["frozen_consumer_sha256"] == "f5ae45cb3b630a57895b2119958c24f1cc559d9cbf34d5b2373b5a1975c300b0"
                and row["field_or_admission_payload_modified"] is False and row["component_algorithms_changed"] is False,
                "actual adapter identity")
        digest_key = "loaded_wrapper_sha256" if key == "consumer_gate_path_adapter" else "loaded_outer_sha256"
        require(row[digest_key] == digest and component["source_sha256"][LEAF + "/component-method-v1/" + name] == digest,
                "actual executed wrapper source")
    command = component["execution"]["sys_orig_argv"]
    require(LEAF + "/component-method-v1/ordered_gate.py" in command and FROZEN[FIELD] in command and FROZEN[GATE] in command
            and component["execution"]["no_CAD_K_or_solve"] is True, "actual command provenance")


def duty_and_port_joins(d, field):
    source = field["source_inputs"]
    shafts = indexed(source["shafts"], "axis_id")
    poses = indexed(source["fitting_poses"], "id")
    recoveries = indexed(field["four_port_fitting_actions"], "body")
    angles = indexed(d["angle_duties"], "body")
    require(len(angles) == 22 and set(angles) == set(poses) == set(recoveries), "22 actual angle owners")
    require(len({r["duty_id"] for r in angles.values()}) == 22, "22 unique angle duties")
    expected_ports = {}
    for binding in source["fitting_port_bindings"]:
        key = (binding["axis_id"], binding["angle_id"], binding["model_port_id"])
        require(key not in expected_ports, "duplicate own port binding")
        expected_ports[key] = binding
    saved_ports = {(r["axis_id"], r["angle_id"], r["flange"]): r for r in d["own_steel_surface_wrenches"]}
    require(len(expected_ports) == len(saved_ports) == 88 and set(expected_ports) == set(saved_ports), "88 unique owned ports")
    for key, binding in expected_ports.items():
        raw = [r for r in field["common_shaft_bearing_actions"] if (r["axis_id"], r["second"], r["flange"]) == key]
        capture = [r for r in field["shaft_end_capture_actions"] if
                   (r["axis_id"], r["second"], r["end"].get("flange")) == key]
        require(len(raw) == 2 and len(capture) == 1, "own steel two bearings/one capture")
        origin = np.asarray(binding["entry_xyz_mm"])
        force, moment = np.zeros(3), np.zeros(3)
        for row in [*raw, *capture]:
            point = row["host_support_point_xyz_mm"] if row in capture else row["point_xyz_mm"]
            f = np.asarray(row["force_on_second_xyz_n"])
            force += f
            moment += row["moment_on_second_at_point_xyz_nmm"] + np.cross(np.asarray(point)-origin, f)
        saved = saved_ports[key]
        close(saved["force_on_steel_xyz_n"], force, "steel port force", 1e-7)
        close(saved["moment_on_steel_at_point_xyz_nmm"], moment, "steel port moment", 1e-4)
        require(set(saved["physical_action_ids"]) == {r["id"] for r in [*raw, *capture]}, "own raw port action lineage")
    for body, row in angles.items():
        bindings = [r for r in source["fitting_port_bindings"] if r["angle_id"] == body]
        require(row["duty_id"] == poses[body]["duty_id"] and row["physical_axis_ids"] == sorted(r["axis_id"] for r in bindings)
                and len(bindings) == 4 and row["complete_group_heel_hole_prying_or_corner_resistance"] is None,
                "own angle duty/axes/scope")
        ports = indexed(recoveries[body]["port_actions"], "port_id")
        joins = indexed(row["own_external_port_joins"], "port_id")
        require(len(joins) == 4 and set(joins) == set(ports), "four own external fitting ports")
        for port_id, saved in joins.items():
            port = ports[port_id]
            force, moment, ids = np.zeros(3), np.zeros(3), []
            point = np.asarray(port["point_xyz_mm"])
            for action in field["common_shaft_steel_port_actions"]:
                if action["host"] == body and action["flange"] == port_id:
                    f = np.asarray(action["force_on_steel_xyz_n"])
                    force += f
                    moment += action["moment_on_steel_at_point_xyz_nmm"] + np.cross(np.asarray(action["point_xyz_mm"])-point, f)
                    ids.append("shaft-surface/" + action["axis_id"] + "/" + str(action["surface_index"]))
            for action in field["contact_actions"]:
                if action["kind"] == "flange_contact" and action["first"] == body and action["flange"] == port_id:
                    f = np.asarray(action["force_on_first_xyz_n"])
                    force += f
                    moment += np.cross(np.asarray(action["point_xyz_mm"])-point, f)
                    ids.append(action["id"])
            close(saved["own_external_force_xyz_n"], force, "fitting external force", 1e-7)
            close(saved["own_external_couple_about_port_xyz_nmm"], moment, "fitting external moment", 1e-4)
            close(saved["external_minus_elastic_required_force_xyz_n"], force-port["external_force_required_at_port_xyz_n"], "fitting force residual", 1e-7)
            close(saved["external_minus_elastic_required_couple_xyz_nmm"], moment-port["external_couple_required_at_port_xyz_nmm"], "fitting moment residual", 1e-4)
            require(saved["own_external_action_ids"] == ids, "own flange/bore/capture lineage")
    require(len(d["exterior_cleat_corners"]) == 2, "two replacement corner duties")
    for row in d["exterior_cleat_corners"]:
        side = row["duty_id"].removeprefix("exterior-cleat-corner-")
        members = ["eoere_cleat_" + side, "base_side_" + side, "base_post_outer_" + side, "base_header"]
        axes = sorted(k for k, s in shafts.items() if members[0] in s["source_axis"]["receivers"])
        contacts = [r["id"] for r in field["contact_actions"] if r["first"] in members and r["second"] in members]
        require(row["members"] == members and row["physical_axis_ids"] == axes and len(axes) == 4 and
                row["own_direct_contact_ids"] == contacts and row["complete_corner_splitting_group_or_bearing_resistance"] is None,
                "four-axis replacement corner path")
    require(d["own_wood_bearing_resultants_from_admitted_field"] == field["common_shaft_wood_bearing_actions"] and
            len(d["own_wood_bearing_resultants_from_admitted_field"]) == 120 and
            d["complete_wood_bolt_yield_end_edge_Cdelta_group_splitting_resistance"] is None, "120 own wood paths/scope")
    cuts = indexed(field["common_shaft_section_cut_actions"], "axis_id")
    circles = indexed(d["own_shaft_circle_comparisons"], "axis_id")
    require(len(circles) == 100 and set(circles) == set(shafts) == set(cuts), "100 own cut/circle joins")
    return {"angle_duties": 22, "replacement_corner_duties": 2, "own_ports": 88, "wood_paths": 120,
            "shaft_owners": 100, "admitted_signed_shaft_cuts": sum(len(r["cuts"]) for r in cuts.values())}


def captures(d, field):
    source = indexed(field["source_inputs"]["shafts"], "axis_id")
    actions = indexed(field["shaft_end_capture_actions"], "id")
    saved = indexed(d["own_washer_capture_diagnostics"], "id")
    require(len(saved) == 200 and set(saved) == set(actions), "200 own end capture joins")
    for key, row in saved.items():
        action = actions[key]
        shaft = source[row["axis_id"]]
        end = next(r for r in shaft["ends"] if r["end"] == row["end"])
        require(action["end"] == end and row["host"] == end["host"] == action["second"], "own end capture host")
        p, g = np.asarray(shaft["point"]), np.asarray(shaft["basis"])[0]
        close(action["point_xyz_mm"], p+g*end["pressure_face_s_mm"], "capture pressure plane", 1e-7)
        close(action["host_support_point_xyz_mm"], p+g*end["support_s_mm"], "capture support plane", 1e-7)
        hardware = shaft["source_axis"]["hardware_scenario"]
        area = math.pi*(hardware["washer_od_mm"]**2-hardware["washer_id_mm"]**2)/4
        close(row["compression_n"], action["compression_n"], "own capture scalar")
        close(row["nominal_full_annulus_area_mm2"], area, "own annulus area")
        close(row["nominal_full_annulus_average_pressure_mpa"], action["compression_n"]/area, "own annulus average")
        require(row["actual_pressure_couple_nmm"] is row["actual_contact_area_or_peak_pressure"] is
                row["washer_bending_nut_head_or_wood_seat_resistance"] is None, "nominal average acquired resistance")
    peak = max(saved.values(), key=lambda r: r["nominal_full_annulus_average_pressure_mpa"])
    return {key: peak[key] for key in ("id", "axis_id", "end", "host", "compression_n", "nominal_full_annulus_average_pressure_mpa")}


def screws(d, field, panel):
    sources = indexed(field["source_inputs"]["hillman_rows"], "id")
    actions = indexed(field["panel_screw_actions"], "axis_id")
    saved = indexed(d["simultaneous_Hillman_actions_and_generic_references"], "axis_id")
    require(len(saved) == 66 and set(saved) == set(actions) == set(sources), "66 own simultaneous screws")
    head = panel.scalar_head_reference(panel.CAT)
    capacity_per_mm = 2850*.5**2*.190*panel.N_PER_LBF/25.4
    for key, row in saved.items():
        action, source = actions[key], sources[key]
        require(all(row[k] == v for k, v in action.items()) and action["first"] == source["first"] and
                action["second"] == source["second"], "same own screw action copied")
        close(action["point_xyz_mm"], source["point_xyz_mm"], "own screw point", 1e-7)
        local = np.asarray(action["local_force_n"])
        close(np.asarray(source["basis"]).T@local, action["force_on_receiver_xyz_n"], "signed simultaneous screw", 1e-7)
        close(row["withdrawal_n"], local[0], "same screw withdrawal")
        close(row["lateral_n"], np.linalg.norm(local[1:]), "same screw lateral")
        close(row["generic_head_reference_n_CD1"], head, "generic head reference")
        close(row["generic_head_ratio_CD1"], local[0]/head, "generic head index")
        close(row["generic_withdrawal_required_effective_thread_mm_CD1"], local[0]/capacity_per_mm, "generic required thread")
        require(row["Hillman_product_capacity_or_stiffness_established"] is False and
                row["local_conical_indentation_punching_edge_capacity_established"] is False, "generic screw reference acquired product strength")
    peak = max(saved.values(), key=lambda r: r["generic_head_ratio_CD1"])
    return {**{k: peak[k] for k in ("axis_id", "panel", "receiver", "withdrawal_n", "lateral_n", "generic_head_ratio_CD1",
        "generic_withdrawal_required_effective_thread_mm_CD1", "gross_nominal_length_after_panel_mm")},
        "generic_head_exceeding_axes": [r["axis_id"] for r in saved.values() if r["generic_head_ratio_CD1"] > 1.]}


def point_actions(field):
    actions, gravity = collections.defaultdict(list), {}
    for table in ("common_shaft_bearing_actions", "shaft_end_capture_actions", "panel_screw_actions", "contact_actions"):
        for row in field[table]:
            p, f = np.asarray(row["point_xyz_mm"]), np.asarray(row["force_on_first_xyz_n"])
            m = np.asarray(row.get("moment_on_first_at_point_xyz_nmm", row.get("moment_at_point_model_xyz_nmm", [0.]*3)))
            actions[row["first"]].append((p, f, m))
            actions[row["second"]].append((np.asarray(row.get("host_support_point_xyz_mm", p)), -f,
                np.asarray(row.get("moment_on_second_at_point_xyz_nmm", -m))))
    for row in field["floor_actions"]:
        actions[row["first"]].append((np.asarray(row["point_xyz_mm"]), np.asarray(row["force_on_first_xyz_n"]),
            np.asarray(row.get("moment_at_point_model_xyz_nmm", [0.]*3))))
    for row in field["body_applied_loads"]:
        if row["id"].startswith("self-weight/"):
            require(row["body"] not in gravity, "duplicate own body gravity")
            gravity[row["body"]] = (np.asarray(row["point_xyz_mm"]), np.asarray(row["force_xyz_n"]))
        else:
            actions[row["body"]].append((np.asarray(row["point_xyz_mm"]), np.asarray(row["force_xyz_n"]),
                                        np.asarray(row.get("moment_xyz_nmm", [0.]*3))))
    return actions, gravity


def gross_members(d, field, gross):
    source = indexed(field["source_inputs"]["timber_rows"], "name")
    saved = indexed(d["fresh_gross_member_diagnostics"], "member")
    require(len(saved) == 22 and set(saved) == set(source), "22 fresh gross witnesses")
    actions, gravity = point_actions(field)
    refs = gross.rectangle.nds.adjusted_reference(139.7)
    summary, total_samples = [], 0
    for name, row in source.items():
        record = saved[name]
        basis = np.asarray([row[k] for k in ("axis", "section_u", "section_v")])
        g, start, end = basis[0], np.asarray(row["start"]), np.asarray(row["end"])
        low, high = float(g@start), float(g@end)
        length, width, depth = high-low, row["width_mm"], row["depth_mm"]
        close(record["source_basis_grain_u_v_xyz"], basis, "fresh member basis")
        close(record["source_span_mm"], length, "fresh member span")
        close([record["source_width_mm"], record["source_depth_mm"]], [width, depth], "fresh member dimensions")
        require(record["finished_net_resistance_established"] is False and record["continuous_maximum_or_actual_bracing_established"] is False
                and record["old_cut_or_force_used"] is False, "gross result acquired net/continuous qualification")
        center, weight = gravity[name]
        beta = 12*(float(g@center)-.5*(low+high))/length**2
        require(min(1.-beta*length/2, 1.+beta*length/2) >= -1e-10, "negative affine gravity")
        stations = set(np.linspace(low, high, 51).tolist())
        for point, _, _ in actions[name]:
            station = float(g@point)
            stations.update((float(np.clip(station-1e-5, low, high)), float(np.clip(station+1e-5, low, high))))
        require(len(stations) == record["sample_count"], "fresh gross station census")
        total_samples += len(stations)
        cu, cv = gross.rectangle.torsion_faces(round(width, 9), round(depth, 9), 1.)
        area = width*depth
        projected = [(float(g@p), p, f, m) for p, f, m in actions[name]]

        def evaluate(station, *, start=start, g=g, low=low, beta=beta, length=length, center=center,
                     weight=weight, projected=projected, basis=basis, width=width, depth=depth, area=area, cu=cu, cv=cv):
            cut = start+g*(station-low)
            actual_station = float(g@cut)
            t = actual_station-low
            fraction = (t+beta*(t*t/2-length*t/2))/length
            local_first = (t*t/2+beta*(t*t*t/3-length*t*t/4))/length
            arm = (center-g*float(g@center)-cut)*fraction + g*(low*fraction+local_first)
            force, moment = weight*fraction, np.cross(arm, weight)
            for s, p, f, m in projected:
                if s < actual_station:
                    force += f
                    moment += np.cross(p-cut, f)+m
            value = np.r_[-basis@force, -basis@moment]
            n, vu, vv, torque, mu, mv = value
            bend = 6*abs(mu)/(width*depth**2)+6*abs(mv)/(depth*width**2)
            normal = ((max(-n, 0)/area/refs["Fc_star_mpa"])**2+bend/refs["Fb_star_mpa"] if n < 0 else
                      max(n, 0)/area/refs["Ft_mpa"]+bend/refs["Fb_star_mpa"])
            transverse = np.array([1.5*abs(vu)/area, 1.5*abs(vv)/area])
            torsion = abs(torque)*np.array([cu, cv])
            shear = float(np.linalg.norm((transverse+torsion)/refs["Fv_mpa"]))
            return value, float(normal), shear

        all_values = [evaluate(s) for s in sorted(stations)]
        normal_max = max(v[1] for v in all_values)
        shear_max = max(v[2] for v in all_values)
        for kind, position, key in (("fully_braced_normal", 1, "fully_braced_component_normal_interaction"),
                                    ("sufficient_shear_torsion", 2, "equal_longitudinal_shear_moduli_rectangle_component_upper_bound_ratio")):
            witness = record["witnesses"][kind]
            value = evaluate(witness["station_global_grain_projection_mm"])
            close(witness["local_N_Vu_Vv_T_Mu_Mv_n_nmm"], value[0], "independent gross cut sixvector", 2e-5)
            close(witness["gross_CD1_comparison"][key], value[position], "independent gross witness ratio", 2e-9)
            close(witness["gross_CD1_comparison"][key], max(v[position] for v in all_values), "independent sampled gross maximum", 2e-9)
        summary.append({"member": name, "sample_count": len(stations), "gross_fully_braced_normal_CD1": normal_max,
                        "gross_equal_moduli_shear_torsion_CD1": shear_max,
                        "full_length_over_weak_column_domain_limit": length/(50*min(width, depth))})
    return {"independent_fresh_sample_count": total_samples,
        "normal_governing": max(summary, key=lambda r: r["gross_fully_braced_normal_CD1"]),
        "shear_torsion_governing": max(summary, key=lambda r: r["gross_equal_moduli_shear_torsion_CD1"]),
        "full_length_weak_column_domain_exceeding_members": [r["member"] for r in summary if r["full_length_over_weak_column_domain_limit"] > 1.],
        "finished_net_and_continuous_resistance_established": False,
        "K1_sensitivity_is_not_a_governing_bracing_or_stability_pass": True}


def panels(d, field, panel):
    saved = indexed(d["six_panel_reductions"]["panel_diagnostics"], "panel")
    coefficients = field["panel_generalized_coefficients"]
    require(len(saved) == 6 and set(saved) == set(coefficients) == set(field["source_inputs"]["panel_ids"]), "six exact current panel blocks")
    integrated = json.loads(panel.INTEGRATED.read_bytes())
    whole = np.asarray(field["response"]["q"])
    summary = []
    convert = panel.N_PER_LBF/304.8
    reference = {"bending_x": 775*25.4*convert, "bending_y": 455*25.4*convert, "rolling_x": 350*convert, "rolling_y": 350*convert}
    for name, row in coefficients.items():
        q = np.asarray(row["coefficients"])
        close(q, whole[row["indices"]], "same current panel q slice", 0.)
        basis = panel.SheetBasis(row["width_mm"], row["height_mm"], row["intervals"])
        require(basis.order == row["basis_order_per_direction"] and basis.knots.tolist() == row["knots_normalized"] and
                row["coefficient_order"] == "u,v,outward_w; x-major tensor cubic B-spline coefficients in mm", "current panel chart")
        geometry = {k: np.asarray(v) if k in ("axes", "origin", "inward") else v for k, v in row["geometry"].items()}
        x, y = np.meshgrid(np.linspace(0, basis.width, 41), np.linspace(0, basis.height, 41), indexing="ij")
        points = np.c_[x.ravel(), y.ravel()]
        keep = points[:, 1] <= geometry["front_height"]+1e-8
        for hole in integrated["panel_machining"]["features"]:
            if hole["panel"] == name:
                xy = ((np.asarray(hole["start_xyz_mm"])-geometry["origin"])@geometry["axes"])[:2]
                keep &= np.linalg.norm(points-xy, axis=1) > hole["diameter_mm"]/2
        spatial = points[keep]
        w = q[2*basis.size:]
        bx, by = panel.material.APA_EI[::-1]
        twist = panel.material.APA_GA*row["thickness_mm"]**2/12
        resultants = {"bending_x": -bx*(basis.values(spatial, 2)@w), "bending_y": -by*(basis.values(spatial, 0, 2)@w),
            "rolling_x": -bx*(basis.values(spatial, 3)@w)-2*twist*(basis.values(spatial, 1, 2)@w),
            "rolling_y": -by*(basis.values(spatial, 0, 3)@w)-2*twist*(basis.values(spatial, 2, 1)@w)}
        peak_ratios = {}
        for key, values in resultants.items():
            peak = int(abs(values).argmax())
            source = saved[name]["resolved_section_diagnostics"]["components"][key]
            close(source["peak_abs_resultant"], abs(values[peak]), "independent spatial panel resultant", 1e-7)
            close(source["xy_mm"], spatial[peak], "independent spatial panel witness", 1e-7)
            close(source["reference_per_mm_width_CD1"], reference[key], "panel reference")
            peak_ratios[key] = float(abs(values[peak])/reference[key])
            close(source["sampled_ratio_CD1"], peak_ratios[key], "independent spatial panel ratio", 1e-8)
        sampled_w = basis.values(points)@w
        sx, sy = basis.values(points, 1)@w, basis.values(points, 0, 1)@w
        slope = np.hypot(sx, sy)
        design = np.c_[np.ones(len(points)), points]
        affine = np.linalg.lstsq(design, sampled_w, rcond=None)[0]
        warp = sampled_w-design@affine
        def_saved = saved[name]["deformation_diagnostics"]
        for key, value in (("maximum_sampled_abs_outward_w_mm", float(abs(sampled_w).max())),
                           ("maximum_sampled_slope_norm", float(slope.max())),
                           ("maximum_sampled_affine_removed_warp_mm", float(abs(warp).max())),
                           ("absolute_outward_w_coefficient_convex_hull_bound_mm", float(abs(w).max()))):
            close(def_saved[key], value, "independent panel deformation", 1e-8)
        require(saved[name]["resolved_section_diagnostics"]["status"] == "SPATIAL_RESOLUTION_DIAGNOSTIC_NOT_LOCAL_CAPACITY_ACCEPTANCE"
                and def_saved["linear_plate_applicability_established"] is False, "panel sampled reference acquired acceptance")
        summary.append({"panel": name, "spatial_CD1_ratios": peak_ratios,
                        "maximum_sampled_abs_outward_w_mm": float(abs(sampled_w).max())})
    return {"six_current_spatial_panels": summary,
        "bending_governing": max(({"panel": r["panel"], "component": k, "ratio_CD1": v} for r in summary for k, v in
                                 r["spatial_CD1_ratios"].items() if k.startswith("bending")), key=lambda r: r["ratio_CD1"]),
        "rolling_governing": max(({"panel": r["panel"], "component": k, "ratio_CD1": v} for r in summary for k, v in
                                 r["spatial_CD1_ratios"].items() if k.startswith("rolling")), key=lambda r: r["ratio_CD1"]),
        "mean_net_cut_comparison_issued_in_this_component_output": False,
        "spatial_diagnostics_are_not_mean_pressure_or_local_hole_head_seat_capacity": True}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--steel-review", type=Path, required=True)
    parser.add_argument("--steel-review-sha256", required=True)
    options = parser.parse_args()
    require(not options.output.exists(), "preserve issued actual component review")
    verify(FROZEN)
    component = json.loads((ROOT/OUTPUT).read_bytes())
    pins = dict(FROZEN)
    join(pins, component["source_sha256"])
    verify(pins)
    gate = load(GATE, "independent_saved_components_actual_cheap_gate")
    receipt = json.loads((ROOT/ADMISSION).read_bytes())
    field, gate_pins = gate.require_admitted_payload((ROOT/FIELD).read_bytes(), receipt, admission_sha256=FROZEN[GATE])
    join(pins, gate_pins)
    provenance(component, field, receipt)
    # Import only pinned basis/reference functions; neither consume/reduce_field
    # nor member_witnesses nor any assembly/operator reader is called.
    panel = load("scripts/thin_bolted_panel_mechanics.py", "independent_saved_component_panel_basis")
    gross = load(LEAF + "/component-method-v1/gross_members.py", "independent_saved_component_reference_coefficients")
    d = component["component_reductions"]
    census = duty_and_port_joins(d, field)
    washer_peak, screw_peak = captures(d, field), screws(d, field, panel)
    panel_result, member_result = panels(d, field, panel), gross_members(d, field, gross)
    require(sha(options.steel_review) == options.steel_review_sha256, "independent actual steel review changed")
    steel_review = json.loads(options.steel_review.read_bytes())
    require(steel_review["schema"] == "eoere_actual_same_state_steel_shaft_independent_review/v1" and
            steel_review["independent_steel_shaft_saved_action_checks_pass"] is True and
            steel_review["state_id"] == field["state_id"] and steel_review["admitted_field_raw_sha256"] == FROZEN[FIELD] and
            steel_review["verified_referenced_source_maps"][OUTPUT]["raw_sha256"] == FROZEN[OUTPUT] and
            steel_review["verified_referenced_source_maps"][ADMISSION]["raw_sha256"] == FROZEN[ADMISSION],
            "steel review is not this current output/field")
    join(pins, steel_review["source_sha256"])
    join(pins, {str(options.steel_review.resolve().relative_to(ROOT)): options.steel_review_sha256,
                str(OWN.relative_to(ROOT)): LOADED_SHA})
    verify(pins)
    require(sha(OWN) == LOADED_SHA, "actual component reviewer changed")
    result = {"schema": "eoere_same_state_actual_components_independent_saved_review/v1",
        "independent_actual_component_source_joins_and_scalar_checks_pass": True,
        "status": "PASS_SAVED_CONDITIONAL_COMPONENT_FINDINGS", "state_id": field["state_id"],
        "source_sha256": {**FROZEN, str(OWN.relative_to(ROOT)): LOADED_SHA,
                          str(options.steel_review.resolve().relative_to(ROOT)): options.steel_review_sha256},
        "verified_source_pin_count": len(pins), "verified_source_pin_union_canonical_sha256": canonical(pins),
        "all_source_pins_before_after_unchanged": True, "actual_component_pin_count": len(component["source_sha256"]),
        "complete_same_state_census": {**census, "own_washer_captures": 200, "simultaneous_Hillman_screws": 66,
                                      "current_panels": 6, "fresh_gross_members": 22},
        "maximum_arithmetic_differences": dict(ERRORS), "own_nominal_washer_average_peak": washer_peak,
        "same_axis_generic_Hillman_governing": screw_peak, "independent_panel_findings": panel_result,
        "independent_gross_member_findings": member_result,
        "steel_arithmetic_independent_peer_review": {"path": str(options.steel_review), "sha256": options.steel_review_sha256},
        "steel_peer_governing_nominal_demands": {"half_strip": steel_review["governing_half_strip"],
                                                "circle": steel_review["governing_nominal_circle"],
                                                "Fy_and_yield_indices": None},
        "limits": ["The actual numerical field is source-bound and admitted; spring-model actions are not physical demand bounds.",
            "The generic Hillman head/withdrawal references are not actual product steel/lateral/edge/punching resistance.",
            "Six panel findings are sampled spatial spline diagnostics; no mean pressure or local hole/head-seat capacity pass follows.",
            "All22 member results concern sampled gross rectangles with source affine gravity. Changed bores/net cuts, continuous extrema, fracture, actual bracing and complete stability remain unqualified.",
            "N/A on the nominal full washer annulus is an average only; actual seat area, pressure couples/peaks, washer/nut/head resistance remain null.",
            "Steel product Fy/Fu, delivered bolt root/shank and complete heel/hole/prying/group/corner/joint resistance remain unavailable."],
        "new_consumer_force_reduction_CAD_query_profile_K_or_solve_executed": False,
        "saved_current_field_read_for_independent_arithmetic_only": True,
        "execution": {"sys_orig_argv": sys.orig_argv, "cwd": str(Path.cwd()), "PYTHONPATH": os.environ.get("PYTHONPATH"),
                      "python": platform.python_version(), "numpy": np.__version__}, "release": component["release"]}
    with options.output.open("x") as stream:
        json.dump(result, stream, sort_keys=True, indent=2, allow_nan=False)
        stream.write("\n")
    print(json.dumps({"path": str(options.output), "sha256": sha(options.output), "bytes": options.output.stat().st_size,
                      "pins": len(pins), "status": result["status"]}))


if __name__ == "__main__":
    main()
