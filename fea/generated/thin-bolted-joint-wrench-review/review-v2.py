"""Read-only old-field local statics/virtual-work diagnostic; no solve or CAD."""

from __future__ import annotations

import hashlib
import json
from collections import Counter
from pathlib import Path

import numpy as np

from scripts import thin_bolted_equilibrium_audit as arithmetic
from scripts.thin_bolted_finished_support_audit import audit_finished_state
from scripts.thin_bolted_joint_kinematics import hinge_matrix, rank_diagnostic
from scripts.thin_bolted_steel_demands import validate_demand_state

ROOT = Path(__file__).resolve().parents[3]
OUTPUT = Path(__file__).parent
INPUT = OUTPUT / "input-v2.json"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify(pins):
    for relative, expected in pins.items():
        if sha(ROOT / relative) != expected:
            raise ValueError(f"frozen source changed: {relative}")


def vector(row, body, reference):
    value = arithmetic.wrench(row["force_on_first_xyz_n"], row["point_xyz_mm"], reference,
                              row.get("moment_at_point_model_xyz_nmm", [0., 0., 0.]))
    if row["first"] == body:
        return value
    if row["second"] == body:
        return -value
    raise ValueError("action does not belong to requested body")


def summed(rows, body, reference):
    return sum((vector(row, body, reference) for row in rows
                if body in (row["first"], row["second"])), np.zeros(6))


def load_sum(rows, body, reference):
    return sum((arithmetic.wrench(row["force_xyz_n"], row["point_xyz_mm"], reference)
                for row in rows if row["body"] == body), np.zeros(6))


def rotate_about(axis, point, reference, bodies, rotating, scale):
    axis = np.asarray(axis, dtype=float)
    axis /= np.linalg.norm(axis)
    velocity = np.cross(axis, np.asarray(reference) - np.asarray(point))
    return np.concatenate([np.r_[velocity, scale * axis] if body in rotating
                           else np.zeros(6) for body in bodies])


def physical_twists(q, bodies, scale):
    return {body: {"translation_at_reference_mm_per_unit_angle_rad": q[6*i:6*i+3].tolist(),
                   "rotation_xyz_rad_per_unit_angle_rad": (q[6*i+3:6*i+6] / scale).tolist()}
            for i, body in enumerate(bodies)}


def point_velocity(q, body, point, reference, bodies, scale):
    if body not in bodies:
        return np.zeros(3)
    offset = 6 * bodies.index(body)
    return q[offset:offset+3] + np.cross(q[offset+3:offset+6] / scale,
                                        np.asarray(point) - np.asarray(reference))


def generalized(wrenches, bodies, scale):
    return np.concatenate([np.r_[wrenches[b][:3], wrenches[b][3:] / scale] for b in bodies])


def row_identity(table, row):
    return f"{table}/" + (row["id"] if "id" in row else
                         "/".join(str(row.get(key, "")) for key in ("axis_id", "angle_id", "flange")))


def fixture_checks():
    # A known z-axis hinge at (20,0,0): torque about its point is the only free work.
    body, ref, point = "coupon", [0., 0., 0.], [20., 0., 0.]
    hinge = [{"first": body, "second": "ground", "point_mm": point, "axis": [0., 0., 1.]}]
    A = hinge_matrix([body], hinge, "ground", ref, 100.)
    q = rotate_about([0, 0, 1], point, ref, [body], {body}, 100.)
    force_at_hinge = arithmetic.wrench([0., 3., 0.], point, ref)
    force_at_offset = arithmetic.wrench([0., 3., 0.], [22., 0., 0.], ref)
    assert np.max(abs(A @ q)) < 1e-12
    assert abs(generalized({body: force_at_hinge}, [body], 100.) @ q) < 1e-12
    assert abs(generalized({body: force_at_offset}, [body], 100.) @ q - 6.) < 1e-12
    pair = {"first": "coupon", "second": "partner", "point_xyz_mm": [22., 3., 4.],
            "force_on_first_xyz_n": [5., 7., 11.], "moment_at_point_model_xyz_nmm": [2., 3., 4.]}
    first, second = vector(pair, "coupon", ref), vector(pair, "partner", ref)
    assert np.max(abs(first + second)) == 0.
    ref2 = [13., -4., 8.]
    value = arithmetic.wrench([0., 3., 0.], [22., 0., 0.], ref2)
    q2 = rotate_about([0, 0, 1], point, ref2, [body], {body}, 100.)
    assert abs(generalized({body: value}, [body], 100.) @ q2 - 6.) < 1e-12
    return {"known_pin_axis_release_and_zero_work": True,
            "known_offset_force_has_6_nmm_work_per_rad": True,
            "internal_force_and_free_couple_cancel": True,
            "reference_transport_invariant": True}


def evaluate_duty(duty, field, layout):
    reference = duty["reference_xyz_mm"]
    beam = duty["beam"]
    fittings = set(duty["rigid_fittings"])
    post = duty["grounded_post_for_local_screen"]
    bodies = [beam, *duty["rigid_fittings"]]
    contacts = [r for r in field["flange_contact_actions"] if r["angle_id"] in fittings]
    pins = [r for r in field["attachment_actions"] if r["angle_id"] in fittings]
    expected_contact_count = 8 * len(fittings)
    if len(contacts) != expected_contact_count or len(pins) != 2 * len(fittings):
        raise ValueError("complete local flange/pin census required")
    if any({r["first"], r["second"]} - {*bodies, post} for r in [*contacts, *pins]):
        raise ValueError("local action connects to an unmodeled body")
    action_tables = {name: field[name] for name in
                     ("attachment_actions", "retained_bolt_actions", "panel_screw_actions", "contact_actions", "floor_actions")}
    external_rows = []
    for table, rows in action_tables.items():
        for row in rows:
            if beam not in (row["first"], row["second"]):
                continue
            is_local = row.get("angle_id") in fittings
            if is_local:
                if table not in ("attachment_actions", "contact_actions"):
                    raise ValueError("unexpected internal-duty action table")
                continue
            external_rows.append((table, row))
    # Every fitting action is local; its only prescribed external load is gravity.
    for table, rows in action_tables.items():
        for row in rows:
            if fittings.intersection((row["first"], row["second"])) and row.get("angle_id") not in fittings:
                raise ValueError("fitting has an unaccounted external interaction")
    loads = [r for r in field["body_applied_loads"] if r["body"] in bodies]
    external = {body: load_sum(loads, body, reference) for body in bodies}
    external[beam] += sum((vector(row, beam, reference) for _, row in external_rows), np.zeros(6))
    contact_wrenches = {body: summed(contacts, body, reference) for body in bodies}
    pin_wrenches = {body: summed(pins, body, reference) for body in bodies}
    closure = {body: external[body] + contact_wrenches[body] + pin_wrenches[body] for body in bodies}
    original_ref = np.asarray(field["common_wrench_reference_xyz_mm"])
    stored = {r["body"]: r for r in field["body_equilibrium_residuals"]}
    closure_discrepancy = 0.
    for body, value in closure.items():
        expected = np.r_[stored[body]["force_xyz_n"], stored[body]["moment_about_reference_xyz_nmm"]]
        expected[3:] += np.cross(original_ref - np.asarray(reference), expected[:3])
        closure_discrepancy = max(closure_discrepancy, float(np.linalg.norm(value - expected)))
    if closure_discrepancy > .001:
        raise ValueError("cut-body closure does not reproduce full source body closure")
    beam_hinges = [h for h in duty["hinges"] if beam in (h["first"], h["second"])]
    beam_axis, beam_point = beam_hinges[0]["axis"], beam_hinges[0]["point_mm"]
    axis = np.asarray(beam_axis) / np.linalg.norm(beam_axis)
    if any(np.linalg.norm(np.cross(np.asarray(h["point_mm"]) - beam_point, axis)) > 1e-5
           or np.linalg.norm(np.cross(np.asarray(h["axis"]) / np.linalg.norm(h["axis"]), axis)) > 1e-7
           for h in beam_hinges):
        raise ValueError("paired beam hinges are not one shaft")
    motion_definitions = [("beam_rotation_about_beam_shaft", beam_axis, beam_point, {beam})]
    if len(fittings) == 1:
        post_hinge = next(h for h in duty["hinges"] if post in (h["first"], h["second"]))
        motion_definitions.append(("beam_and_fitting_rotation_about_post_shaft", post_hinge["axis"],
                                   post_hinge["point_mm"], set(bodies)))
    datum_error = 0.
    axis_rows = {a["id"]: a for a in layout["installed_axes"]}
    for row in pins:
        axis_row = axis_rows[row["axis_id"]]
        shaft_axis = np.asarray(axis_row["direction"]) / np.linalg.norm(axis_row["direction"])
        datum_error = max(datum_error, float(np.linalg.norm(np.cross(
            np.asarray(row["point_xyz_mm"]) - axis_row["point"], shaft_axis))))
    if datum_error > 1e-5:
        raise ValueError("port datum is not collinear with isolated hinge shaft")
    fitting_rows = {r["angle_id"]: r for r in layout["raw_fittings"]}
    scale_checks, motions = [], []
    for scale in (10., 100., 1000.):
        A = hinge_matrix(bodies, duty["hinges"], post, reference, scale)
        diag = rank_diagnostic(A)
        normal_contact_rows = []
        for row in contacts:
            fitting_row = fitting_rows[row["angle_id"]]
            normal = np.asarray(fitting_row["v_xyz" if row["flange"] == "beam" else "u_xyz"])
            normal /= np.linalg.norm(normal)
            normal_contact_rows.append([float(normal @ (
                point_velocity(unit, row["first"], row["point_xyz_mm"], reference, bodies, scale)
                - point_velocity(unit, row["second"], row["point_xyz_mm"], reference, bodies, scale)))
                for unit in np.eye(6 * len(bodies))])
        C = np.asarray(normal_contact_rows)
        active_C = C[[r["compression_n"] > 1e-7 for r in contacts]]
        all_contact_rank = rank_diagnostic(np.vstack((A, C)))["rank"]
        active_contact_rank = rank_diagnostic(np.vstack((A, active_C)))["rank"]
        if all_contact_rank != diag["rank"] or active_contact_rank != diag["rank"]:
            raise ValueError("normal contacts unexpectedly change the isolated free-motion rank")
        Q = np.column_stack([rotate_about(a, p, reference, bodies, moving, scale)
                             for _, a, p, moving in motion_definitions])
        if (np.linalg.matrix_rank(Q) != diag["isolated_joint_free_motions"]
                or np.max(abs(A @ Q)) > 1e-5):
            raise ValueError("physical free-motion basis does not span isolated nullspace")
        _u, _s, vh = np.linalg.svd(A, full_matrices=True)
        null = vh[diag["rank"]:].T
        span_error = float(np.max(abs(Q - null @ (null.T @ Q))))
        if span_error > 1e-5:
            raise ValueError("physical motion does not lie in SVD nullspace")
        ext = generalized(external, bodies, scale)
        con = generalized(contact_wrenches, bodies, scale)
        pin = generalized(pin_wrenches, bodies, scale)
        work = {"without_contacts": (Q.T @ ext).tolist(),
                "flange_contacts": (Q.T @ con).tolist(),
                "pin_actions": (Q.T @ pin).tolist(),
                "with_contacts": (Q.T @ (ext + con)).tolist(),
                "complete_closure": (Q.T @ (ext + con + pin)).tolist()}
        scale_checks.append({"rotation_scale_mm": scale, "rank": diag["rank"],
                             "free_motions": diag["isolated_joint_free_motions"],
                             "rank_with_all_normal_contacts_treated_bilateral": all_contact_rank,
                             "rank_with_old_active_normal_contacts_treated_bilateral": active_contact_rank,
                             "contact_normal_velocity_residual_max_mm_per_rad": float(np.max(abs(C @ Q))),
                             "hinge_velocity_residual_max_mm_per_rad": float(np.max(abs(A @ Q))),
                             "SVD_nullspace_motion_span_error_mm_per_rad": span_error,
                             "unit_angular_motion_work_nmm_per_rad": work,
                             "orthonormal_scaled_null_basis_external_dual_projection_norm_n": float(np.linalg.norm(null.T @ ext)),
                             "orthonormal_scaled_null_basis_external_plus_contact_projection_norm_n": float(np.linalg.norm(null.T @ (ext + con)))})
        if scale == 100.:
            for i, (name, axis, point, rotating) in enumerate(motion_definitions):
                contributions = {}
                for body in bodies:
                    q = Q[6*bodies.index(body):6*bodies.index(body)+6, i]
                    contributions[body] = {"external": float(generalized({body: external[body]}, [body], scale) @ q),
                                           "contacts": float(generalized({body: contact_wrenches[body]}, [body], scale) @ q),
                                           "pins": float(generalized({body: pin_wrenches[body]}, [body], scale) @ q)}
                contact_velocities = []
                for row in contacts:
                    fitting_row = fitting_rows[row["angle_id"]]
                    normal = np.asarray(fitting_row["v_xyz" if row["flange"] == "beam" else "u_xyz"])
                    normal /= np.linalg.norm(normal)
                    relative = (point_velocity(Q[:, i], row["first"], row["point_xyz_mm"], reference, bodies, scale)
                                - point_velocity(Q[:, i], row["second"], row["point_xyz_mm"], reference, bodies, scale))
                    normal_velocity = float(normal @ relative)
                    tangential = relative - normal_velocity * normal
                    contact_velocities.append({"id": row["id"], "compression_n": row["compression_n"],
                        "relative_normal_velocity_mm_per_rad": normal_velocity,
                        "relative_tangential_velocity_norm_mm_per_rad": float(np.linalg.norm(tangential)),
                        "signed_virtual_work_nmm_per_rad": float(np.asarray(row["force_on_first_xyz_n"]) @ relative)})
                motions.append({"name": name, "unit_angle_rad": 1., "axis_xyz": (np.asarray(axis)/np.linalg.norm(axis)).tolist(),
                                "shaft_point_xyz_mm": point, "rotating_bodies": sorted(rotating),
                                "physical_twists": physical_twists(Q[:, i], bodies, scale),
                                "external_virtual_work_without_contacts_nmm_per_rad": work["without_contacts"][i],
                                "flange_contact_virtual_work_nmm_per_rad": work["flange_contacts"][i],
                                "external_plus_contact_virtual_work_nmm_per_rad": work["with_contacts"][i],
                                "pin_virtual_work_nmm_per_rad": work["pin_actions"][i],
                                "complete_closure_virtual_work_nmm_per_rad": work["complete_closure"][i],
                                "per_body_work_nmm_per_rad": contributions,
                                "flange_contact_motion_census": contact_velocities,
                                "flange_contact_relative_normal_velocity_max_abs_mm_per_rad": max(abs(c["relative_normal_velocity_mm_per_rad"]) for c in contact_velocities),
                                "flange_contact_relative_tangential_velocity_max_mm_per_rad": max(c["relative_tangential_velocity_norm_mm_per_rad"] for c in contact_velocities),
                                "normal_contact_removes_this_first_order_free_motion": False})
    max_no_contact = max(abs(m["external_virtual_work_without_contacts_nmm_per_rad"]) for m in motions)
    max_with_contact = max(abs(m["external_plus_contact_virtual_work_nmm_per_rad"]) for m in motions)
    # 0.1 Nmm follows the old independent body moment tolerance. It is an arithmetic
    # threshold for unit angular motions, not a physical joint acceptance threshold.
    pin_only = max_no_contact <= .1
    contact_closed = max_with_contact <= .1
    if not contact_closed:
        raise ValueError("representative old contact witness does not close released motion work")
    detail = []
    for table, rows in (("attachment_actions", pins), ("flange_contact_actions", contacts)):
        for row in rows:
            detail.append({"source_action_id": row_identity(table, row),
                           "first": row["first"], "second": row["second"],
                           "point_xyz_mm": row["point_xyz_mm"],
                           "force_on_first_xyz_n": row["force_on_first_xyz_n"],
                           "moment_at_point_model_xyz_nmm": row.get("moment_at_point_model_xyz_nmm", [0., 0., 0.]),
                           "compression_n": row.get("compression_n")})
    shared_port_rows = []
    for axis_id in duty["unique_physical_axes"]:
        axis_row = axis_rows[axis_id]
        if len(axis_row["attachments"]) <= 1:
            continue
        direction = np.asarray(axis_row["direction"]) / np.linalg.norm(axis_row["direction"])
        ports = []
        for row in field["attachment_actions"]:
            if row["axis_id"] != axis_id:
                continue
            force = np.asarray(row["force_on_receiver_xyz_n"])
            axial = float(force @ direction)
            ports.append({"angle_id": row["angle_id"], "flange": row["flange"], "receiver": row["receiver"],
                          "point_xyz_mm": row["point_xyz_mm"], "force_on_receiver_xyz_n": force.tolist(),
                          "force_norm_n": float(np.linalg.norm(force)),
                          "signed_force_along_common_axis_n": axial,
                          "lateral_force_norm_n": float(np.linalg.norm(force - axial * direction)),
                          "moment_on_receiver_at_point_model_xyz_nmm": row["moment_on_receiver_at_point_xyz_nmm"]})
        shared_port_rows.append({"axis_id": axis_id, "one_physical_shaft": True,
            "old_independent_spring_port_actions": ports,
            "physical_common_shaft_distribution_or_own_end_actions_recovered": False,
            "equal_sharing_or_two_single_shear_capacities_assigned": False})
    return {"duty": duty["duty"], "moving_bodies": bodies, "grounded_post": post,
            "wrench_reference_xyz_mm": reference, "unique_physical_shaft_ids": duty["unique_physical_axes"],
            "excluded_shared_axis_other_duty_angles": duty["excluded_shared_axis_other_duty_angles"],
            "beam_external_action_census": dict(Counter(table for table, _ in external_rows)),
            "beam_external_action_ids": [row_identity(table, row) for table, row in external_rows],
            "moving_body_applied_loads": loads,
            "duty_attachment_count": len(pins), "duty_flange_contact_count": len(contacts),
            "duty_positive_flange_contact_count": sum(r["compression_n"] > 1e-7 for r in contacts),
            "shared_physical_shafts_old_interface_port_census": shared_port_rows,
            "complete_signed_duty_pin_and_contact_census": detail,
            "body_wrenches_force_xyz_n_then_moment_xyz_nmm": {
                body: {"external": external[body].tolist(), "local_pin": pin_wrenches[body].tolist(),
                       "local_compression_contact": contact_wrenches[body].tolist(), "closure": closure[body].tolist()}
                for body in bodies},
            "datum_cross_axis_distance_max_mm": datum_error,
            "body_closure_source_comparison_max_combined_vector_norm": closure_discrepancy,
            "unit_angular_motions": motions, "scale_checks": scale_checks,
            "pin_only_prescribed_old_external_wrench_admissible": pin_only,
            "old_flange_contact_static_witness_closes_released_motion_work": contact_closed,
            "normal_contacts_add_first_order_restraint_to_isolated_free_motions": False,
            "current_field_or_complete_joint_admissibility_established": False,
            "contact_motion_compatibility_or_resistance_established": False}


def main():
    if (OUTPUT / "result-v2.json").exists():
        raise FileExistsError("preserve prior diagnostic result")
    config = json.loads(INPUT.read_text())
    inputs = config["source_sha256"]
    verify(inputs)
    field = json.loads((ROOT / config["field"]).read_text())
    layout = json.loads((ROOT / config["layout"]).read_text())
    kinematics = json.loads((ROOT / config["kinematics"]).read_text())
    verify(field["source_sha256"])
    verify(kinematics["source_sha256"])
    state = validate_demand_state(field)
    if state["state_id"] != config["state_id"]:
        raise ValueError("old state identity mismatch")
    admission = audit_finished_state(field)
    if not admission["independent_finished_support_and_equilibrium_checks_pass"]:
        raise ValueError("old finished-support gate failed")
    fixtures = fixture_checks()
    by_duty = {r["duty"]: r for r in kinematics["duties"]}
    duties = [evaluate_duty(by_duty[name], field, layout) for name in config["representative_duties"]]
    verify(inputs)
    verify(field["source_sha256"])
    verify(kinematics["source_sha256"])
    output = {"schema": "thin_bolted_saved_old_field_local_wrench_review/v1",
              "status": "CONDITIONAL_OLD_FIELD_STATIC_WITNESS_ONLY", "state": state,
              "source_sha256": inputs | {str(INPUT.relative_to(ROOT)): sha(INPUT),
                                          str(Path(__file__).relative_to(ROOT)): sha(Path(__file__))},
              "field_producer_source_sha256": field["source_sha256"],
              "kinematic_source_sha256": kinematics["source_sha256"],
              "same_source_bytes_verified_before_and_after": True,
              "old_finished_support_and_equilibrium_admission": admission,
              "fixtures": fixtures, "numpy_version": np.__version__,
              "complete_old_field_census": {"bodies": len(field["body_equilibrium_residuals"]),
                  "physical_bolt_axes": len(layout["installed_axes"]),
                  "shared_new_physical_shafts": sum(len(a["attachments"]) > 1 for a in layout["installed_axes"]),
                  "new_fitting_attachment_ports": len(field["attachment_actions"]),
                  "retained_frame_bolt_actions": len(field["retained_bolt_actions"]),
                  "Hillman_panel_screw_actions": len(field["panel_screw_actions"]),
                  "flange_compression_contact_rows": len(field["flange_contact_actions"]),
                  "all_contact_kinds": dict(Counter(r["kind"] for r in field["contact_actions"])),
                  "body_applied_load_rows": len(field["body_applied_loads"]),
                  "body_applied_load_kinds": dict(Counter(r["id"].split('/')[0] for r in field["body_applied_loads"]))},
              "method": {"pure_saved_JSON_wrench_and_small_dense_nullspace_arithmetic": True,
                  "shaft_axis_torque_or_friction_credited": False, "clamp_or_preload_credited": False,
                  "native_CAD_or_global_stiffness_assembly": False,
                  "physical_motion_normalization": "one radian about the named shaft; velocities are infinitesimal derivatives, not actual motion",
                  "scaled_SVD_basis_limit": "orthonormal scaled null projection norms depend on rotation scale; only zero/nonzero and physical unit-angular work are invariant",
                  "external_beam_wrench": "all prescribed old per-body beam loads and other beam interactions, excluding this duty's attachments and flange contacts",
                  "external_fitting_wrench": "actual frozen fitting self-weight; all fitting attachments and flange contacts are internal or ground interactions",
                  "excluded_bodies": "grounded post external loads and loads on every other body do no local virtual work and are omitted",
                  "contact_doublecount_prevented": "flange_contact_actions is used once for local contacts, and matching contact_actions rows are excluded from the exterior cut",
                  "contact_work": "beam/fitting internal pairs are included on both moving bodies; post-face contacts act on fittings against the local ground",
                  "contact_motion_interpretation": "all released directions are tangent to the corresponding flat flange; normal contacts have zero first-order normal relative velocity and provide no released-axis restoring stiffness",
                  "work_check_independence_limit": "the old field's moment-free point connectors and flange-normal forces already imply released-axis work neutrality when body closure holds; this is a transparent load-space consistency diagnostic, not an independent mechanics validation",
                  "arithmetic_motion_work_tolerance_nmm_per_rad": .1,
                  "small_motion_contact_or_capacity_acceptance_threshold": None},
              "duties": duties, "limits": config["limits"],
              "release": field["release"], "complete_joint_acceptance": False,
              "current_demands_or_joint_capacity_established": False}
    target = OUTPUT / "result-v2.json"
    target.write_text(json.dumps(output, indent=2, allow_nan=False) + "\n")
    print(json.dumps({"result": str(target.relative_to(ROOT)), "input_sha256": sha(INPUT),
                      "script_sha256": sha(Path(__file__)), "result_sha256": sha(target),
                      "duties": [{"duty": d["duty"], "pin_only_admissible": d["pin_only_prescribed_old_external_wrench_admissible"],
                                  "with_old_contacts_closes": d["old_flange_contact_static_witness_closes_released_motion_work"],
                                  "motions": d["unit_angular_motions"]} for d in duties]}, indent=2))


if __name__ == "__main__":
    main()
