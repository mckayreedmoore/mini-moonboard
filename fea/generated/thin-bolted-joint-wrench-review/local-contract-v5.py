"""K-free rigid-patch geometry, unilateral cone and generalized-work contract."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
from scipy.optimize import linprog

from scripts import thin_bolted_equilibrium_audit as arithmetic
from scripts.thin_bolted_common_shaft import shaft_inputs
from scripts.thin_bolted_joint_kinematics import hinge_matrix, rank_diagnostic

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).parent


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify(pins):
    for path, expected in pins.items():
        if sha(ROOT / path) != expected:
            raise ValueError("source changed: " + path)


def kernel(A):
    rank = rank_diagnostic(A)["rank"]
    return np.linalg.svd(A, full_matrices=True)[2][rank:].T


def point_port(bodies, body, point, reference, scale):
    # The excluded token is absent from the body list: no modeled body is fixed.
    return hinge_matrix(bodies, [{"first": body, "second": "__excluded__", "point_mm": point,
                                  "axis": [0., 0., 1.]}], "__excluded__", reference, scale)[:3]


def rigid_rotation_port(bodies, body, scale):
    row = np.zeros((3, 6 * len(bodies)))
    i = 6 * bodies.index(body)
    row[:, i+3:i+6] = np.eye(3) / scale
    return row


def operators(patch, layout, shafts, scale, direct):
    fitting_ids = sorted(patch["fittings"])
    rods = [s for s in shafts if s["axis_id"] in patch["axes"]]
    bodies = [*patch["timbers"], *fitting_ids, *[s["body"] for s in rods]]
    reference = np.mean([s["point"] for s in rods], axis=0)
    radials, normals, annular, direct_rows = [], [], [], []
    inventory = {"radials": [], "normals": [], "annular_tilt_potentials": [], "conditional_direct_timber_normals": []}
    for shaft in rods:
        for surface_i, surface in enumerate(shaft["surfaces"]):
            if surface["host"] not in bodies:
                raise ValueError("omitted host on selected continuous rod")
            a, b = surface["interval_mm"]
            for quad, xi in enumerate((-1/np.sqrt(3.), 1/np.sqrt(3.))):
                point = shaft["point"] + shaft["basis"][0] * (.5*(a+b) + .5*(b-a)*xi)
                ports = point_port(bodies, shaft["body"], point, reference, scale) - point_port(bodies, surface["host"], point, reference, scale)
                radials.extend(shaft["basis"][1:] @ ports)
                inventory["radials"].append({"id": shaft["axis_id"] + f"/bearing-{surface_i}-{quad}",
                    "first": shaft["body"], "second": surface["host"], "point_xyz_mm": point.tolist(),
                    "source_surface": surface, "nominal_radial_gap_mm": .5*(shaft["bore_diameter_mm"]-shaft["diameter_mm"]),
                    "two_bilateral_radial_rows_are_actual_active_contact": False})
        for end in shaft["ends"]:
            first = shaft["point"] + shaft["basis"][0]*end["pressure_face_s_mm"]
            second = shaft["point"] + shaft["basis"][0]*end["support_s_mm"]
            normal = np.asarray(end["direction_on_shaft_xyz"])
            ports = point_port(bodies, shaft["body"], first, reference, scale) - point_port(bodies, end["host"], second, reference, scale)
            normals.append(normal @ ports)
            record = {"id": shaft["axis_id"] + "/" + end["end"] + "-capture", "first": shaft["body"], "second": end["host"],
                "first_reference_point_xyz_mm": first.tolist(), "second_reference_point_xyz_mm": second.tolist(),
                "opening_positive_normal_xyz": normal.tolist(), "end": end}
            inventory["normals"].append(record)
            # A full annular normal-contact span can compare two transverse
            # tilts. This is a potential upper envelope, not adopted pressure.
            rotation = rigid_rotation_port(bodies, shaft["body"], scale) - rigid_rotation_port(bodies, end["host"], scale)
            annular.extend(scale * shaft["basis"][1:] @ rotation)
            inventory["annular_tilt_potentials"].append({**record, "transverse_normal_moment_rows": 2,
                "shaft_axis_friction_or_torque_row": False, "washer_pose_and_active_pressure_patch_collapsed_optimistically": True})
    for fit in layout["raw_fittings"]:
        if fit["angle_id"] not in fitting_ids:
            continue
        o, u, v, w = (np.asarray(fit[k]) for k in ("origin_xyz_mm", "u_xyz", "v_xyz", "w_xyz"))
        for flange, host, normal, along, length in (("beam", fit["beam"], v, u, 104.775), ("post", fit["post"], u, v, 88.9)):
            if host not in bodies:
                raise ValueError("omitted flange receiver")
            for corner, (s, t) in enumerate((s, t) for s in (5.55625, length) for t in (-20.6375, 20.6375)):
                point = o + along*s + w*t
                normals.append(normal @ (point_port(bodies, fit["angle_id"], point, reference, scale) - point_port(bodies, host, point, reference, scale)))
                inventory["normals"].append({"id": fit["angle_id"]+"/"+flange+f"/contact-{corner}", "first": fit["angle_id"],
                    "second": host, "first_reference_point_xyz_mm": point.tolist(), "second_reference_point_xyz_mm": point.tolist(),
                    "opening_positive_normal_xyz": normal.tolist(), "reference_gap_mm": 0.})
    for face in direct["patches"]:
        if face["first"] not in patch["timbers"] or face["second"] not in patch["timbers"]:
            continue
        normal = np.asarray(face["normal_from_second_to_first_xyz"])
        for cell in face["cells"]:
            point = cell["point_xyz_mm"]
            direct_rows.append(normal @ (point_port(bodies, face["first"], point, reference, scale) - point_port(bodies, face["second"], point, reference, scale)))
            inventory["conditional_direct_timber_normals"].append({"id": cell["id"], "first": face["first"], "second": face["second"],
                "point_xyz_mm": point, "opening_positive_normal_xyz": normal.tolist(), "area_mm2": cell["area_mm2"],
                "nominal_opposed_finished_face_geometry": True, "contact_law_or_production_adoption": False})
    E, N, T, D = (np.asarray(rows).reshape(-1, 6*len(bodies)) for rows in (radials, normals, annular, direct_rows))
    return bodies, reference, E, N, T, D, inventory


def global_modes(bodies):
    return np.tile(np.eye(6), (len(bodies), 1))


def rod_rolls(bodies, rods, reference, scale):
    columns = []
    for rod in rods:
        q = np.zeros(6*len(bodies))
        i = 6*bodies.index(rod["body"])
        q[i:i+3] = np.cross(rod["basis"][0], reference-rod["point"])
        q[i+3:i+6] = scale*rod["basis"][0]
        columns.append(q)
    return np.asarray(columns).T


def relative_map(bodies, timbers):
    C = np.zeros((6*(len(timbers)-1), 6*len(bodies)))
    for i, body in enumerate(timbers[1:]):
        C[6*i:6*i+6, 6*bodies.index(body):6*bodies.index(body)+6] = np.eye(6)
        C[6*i:6*i+6, :6] = -np.eye(6)
    return C


def diagnostic(A, bodies, timbers, reference, scale, rolls):
    Z, C, G = kernel(A), relative_map(bodies, timbers), global_modes(bodies)
    image = C @ Z
    image_rank = rank_diagnostic(image)["rank"]
    admissible = kernel(image.T)
    assert np.max(abs(A @ G)) < 1e-9 and np.max(abs(A @ rolls)) < 1e-9
    assert np.max(abs(image.T @ admissible), initial=0.) < 1e-9
    return {**rank_diagnostic(A), "whole_patch_rigid_modes": 6, "shaft_axis_roll_modes": rolls.shape[1],
        "remaining_internal_modes_after_global_and_shaft_roll": Z.shape[1]-6-rolls.shape[1],
        "timber_relative_coordinate_count": C.shape[0], "free_mode_image_rank_on_relative_timbers": image_rank,
        "timber_only_balanced_wrench_subspace_dimension": admissible.shape[1],
        "full_null_basis_q_columns": Z.tolist(), "relative_timber_null_image_columns": image.tolist(),
        "admissible_generalized_wrench_basis_columns": admissible.tolist(),
        "basis_coordinates": "u_xyz,L*theta_xyz at common reference; dual isF_xyz,M_xyz/L",
        "rotation_scale_mm": scale, "reference_xyz_mm": reference.tolist(),
        "actual_tangent_stiffness_or_complete_joint_compliance_established": False}


def touch_cone_certificate(N):
    # A strictly positive self-stress is a geometric Farkas certificate:
    # Nq>=0 then lambda.Nq=0 forces every touching-row opening to zero.
    # It is not an actual preload or reaction allocation.
    result = linprog(np.ones(len(N)), A_eq=N.T, b_eq=np.zeros(N.shape[1]), bounds=(1., None), method="highs")
    if not result.success:
        # Provide a directly verifiable opening direction when full positive
        # self-stress cannot force all rows to equality.
        opening = linprog(-N.sum(axis=0), A_ub=-N, b_ub=np.zeros(len(N)), bounds=(-1., 1.), method="highs")
        if not opening.success:
            raise ValueError("bounded contact-cone witness failed")
        values = N @ opening.x
        assert min(values) > -1e-8
        return {"strict_positive_geometric_self_stress_found": False, "solver_message": result.message,
                "touch_cone_lineality_equals_all_normal_nullspace": bool(max(values) < 1e-8),
                "feasible_opening_direction_q": opening.x.tolist(), "normal_row_opening_derivatives": values.tolist(),
                "maximum_opening_derivative": float(max(values)), "opening_is_physical_deflection_or_state": False}
    residual = float(np.max(abs(N.T @ result.x)))
    assert residual < 1e-8
    return {"strict_positive_geometric_self_stress_found": True, "positive_coefficients": result.x.tolist(),
        "null_equilibrium_residual": residual, "minimum_coefficient": float(min(result.x)),
        "touch_cone_lineality_equals_all_normal_nullspace": True,
        "certificate_is_actual_preload_pressure_or_current_active_branch": False,
        "conditions": "exact nominal flange/capture touching, rigid captured stack, all listed normal inequalities retained; no bore contact at centered clearance"}


def physical_loads(patch, layout, bodies, reference, scale, A, normal_only, with_direct, E, N):
    Z = kernel(A)
    outputs = []
    for timber in patch["timbers"][1:]:
        fit = next(f for f in layout["raw_fittings"] if f["angle_id"] in patch["fittings"] and f["post"] == timber)
        axes = [a for a in layout["installed_axes"] if a["id"] in patch["axes"] and any(r["angle_id"] == fit["angle_id"] for r in a["attachments"])]
        if len(axes) != 2:
            raise ValueError("two source hinge axes expected per selected angle")
        angular = np.asarray([a["direction"] for a in axes])
        translational = np.asarray([np.cross(a["direction"], reference-a["point"]) for a in axes])
        free_couple = np.cross(*angular); free_couple /= np.linalg.norm(free_couple)
        units = [] if normal_only else [("unit_F"+"xyz"[i], e, -np.linalg.pinv(angular) @ (translational @ e)) for i, e in enumerate(np.eye(3))]
        if with_direct:
            if normal_only:
                units.append(("unit_Fz", np.array([0., 0., 1.]), np.zeros(3)))
            units.append(("unit_post_axis_couple", np.zeros(3), angular[1]))
        units.append(("unit_free_transverse_couple", np.zeros(3), free_couple))
        for name, force, moment in units:
            wrench = np.r_[force, moment]
            generalized = np.zeros(6*len(bodies))
            for body, sign in ((timber, 1.), (patch["timbers"][0], -1.)):
                i = 6*bodies.index(body)
                generalized[i:i+6] = sign*np.r_[force, moment/scale]
            work = float(np.max(abs(Z.T @ generalized)))
            assert work < 1e-9
            ports = []
            # Header left is a declared particular split; its right cut is
            # zero here. The six self-equilibrated header-cut modes are absent.
            for body, sign in ((timber, 1.), (patch["timbers"][0], -1.)):
                point = np.asarray(patch["remote_ports"][body][0]["point_xyz_mm"])
                ports.append({"body": body, "point_xyz_mm": point.tolist(), "force_xyz_n": (sign*force).tolist(),
                    "moment_at_point_xyz_nmm": (sign*moment - np.cross(point-reference, sign*force)).tolist()})
            closure = sum((arithmetic.wrench(r["force_xyz_n"], r["point_xyz_mm"], reference, r["moment_at_point_xyz_nmm"]) for r in ports), np.zeros(6))
            assert np.max(abs(closure)) < 1e-9
            cones = {}
            for sign in (1., -1.):
                # Radial envelope reactions are signed bilateral multipliers;
                # normal reactions remain compression-only. Feasibility is
                # necessary rigid statics, never actual pressure or stiffness.
                constraints = np.column_stack((E.T, N.T))
                lp = linprog(np.zeros(constraints.shape[1]), A_eq=constraints, b_eq=-sign*generalized,
                             bounds=[(None, None)]*len(E) + [(0., None)]*len(N), method="highs")
                cones["positive" if sign > 0 else "negative"] = {"compression_reaction_cone_feasible": bool(lp.success)}
                if lp.success:
                    residual = float(np.max(abs(constraints @ lp.x + sign*generalized)))
                    assert residual < 1e-8
                    cones["positive" if sign > 0 else "negative"].update({"radial_bilateral_multipliers": lp.x[:len(E)].tolist(),
                        "normal_nonnegative_multipliers": lp.x[len(E):].tolist(), "equilibrium_residual": residual})
            outputs.append({"id": timber+"/"+name, "timber_vs_header_wrench_at_reference": wrench.tolist(),
                "generalized_body_load_vector": generalized.tolist(), "remote_port_actions": ports,
                "max_free_mode_work_nmm_per_scaled_coordinate": work,
                "global_force_and_moment_closure_at_reference": closure.tolist(), "conditional_rigid_reaction_cone_checks": cones,
                "is_current_demand_or_capacity": False})
    return outputs


def header_self_balanced_port_units(patch, reference):
    ports = patch["remote_ports"][patch["timbers"][0]]
    if len(ports) != 2:
        return []
    p1, p2 = (np.asarray(p["point_xyz_mm"]) for p in ports)
    outputs = []
    for i, w in enumerate(np.eye(6)):
        f, m = w[:3], w[3:]
        rows = [{"body": patch["timbers"][0], "point_xyz_mm": p1.tolist(), "force_xyz_n": f.tolist(), "moment_at_point_xyz_nmm": m.tolist()},
                {"body": patch["timbers"][0], "point_xyz_mm": p2.tolist(), "force_xyz_n": (-f).tolist(),
                 "moment_at_point_xyz_nmm": (-m-np.cross(p1-p2, f)).tolist()}]
        net = sum((arithmetic.wrench(r["force_xyz_n"], r["point_xyz_mm"], reference, r["moment_at_point_xyz_nmm"]) for r in rows), np.zeros(6))
        assert max(abs(net)) < 1e-10
        outputs.append({"id": "header-cut-null-work-"+str(i), "remote_port_actions": rows, "net_rigid_header_wrench": net.tolist(),
                        "finite_header_compliance_or_neighbor_load_split_determined": False})
    return outputs


def evaluate(config, layout, shafts, direct):
    outputs = []
    for patch in config["patches"]:
        runs = []
        for scale in (10., 100., 1000.):
            bodies, reference, E, N, T, D, inventory = operators(patch, layout, shafts, scale, direct)
            rods = [s for s in shafts if s["axis_id"] in patch["axes"]]
            rolls = rod_rolls(bodies, rods, reference, scale)
            matrices = {"nominal_touch_normals_only": N, "touch_normals_plus_annular_tilt_potential": np.vstack((N, T)),
                        "all_radial_bilateral_plus_touch_normal_envelope": np.vstack((E, N)),
                        "all_radial_normal_plus_annular_envelope": np.vstack((E, N, T)),
                        "conditional_direct_timber_plus_touch_normals": np.vstack((N, D)),
                        "conditional_direct_timber_plus_radial_normal_envelope": np.vstack((E, N, D))}
            diagnostics = {name: diagnostic(A, bodies, patch["timbers"], reference, scale, rolls) for name, A in matrices.items()}
            if scale != 100.:
                for item in diagnostics.values():
                    for key in ("full_null_basis_q_columns", "relative_timber_null_image_columns", "admissible_generalized_wrench_basis_columns"):
                        del item[key]
            runs.append({"scale_mm": scale, "diagnostics": diagnostics})
            if scale == 100.:
                certificate = {"reviewed_bracket_contact_only": touch_cone_certificate(N), "conditional_added_direct_timber": touch_cone_certificate(np.vstack((N, D)))}
                empty = np.zeros((0, len(bodies)*6))
                loads = {"nominal_touch_normal_work_subspace": physical_loads(patch, layout, bodies, reference, scale, N, True, False, empty, N),
                         "radial_bilateral_envelope_work_subspace": physical_loads(patch, layout, bodies, reference, scale, np.vstack((E, N)), False, False, E, N),
                         "conditional_direct_touch_lineality_work_subspace": physical_loads(patch, layout, bodies, reference, scale, np.vstack((N, D)), True, True, empty, np.vstack((N, D))),
                         "conditional_direct_radial_envelope_work_subspace": physical_loads(patch, layout, bodies, reference, scale, np.vstack((E, N, D)), False, True, E, np.vstack((N, D)))}
                header_units = header_self_balanced_port_units(patch, reference)
        for name in matrices:
            if len({run["diagnostics"][name]["rank"] for run in runs}) != 1:
                raise ValueError("rank changed with coordinate scale")
        outputs.append({"id": patch["id"], "body_order": bodies, "reference_xyz_mm": reference.tolist(), "rigid_body_count": len(bodies),
            "coordinate_count": 6*len(bodies), "source_rod_topology": [{"axis_id": s["axis_id"], "wood_spans": sum(r["kind"] == "wood" for r in s["surfaces"]),
                "steel_spans": sum(r["kind"] == "steel" for r in s["surfaces"]), "captures": len(s["ends"])} for s in rods],
            "source_interface_inventory": inventory, "scale_checks": runs, "nominal_touch_cone_certificate": certificate,
            "signed_balanced_unit_loads": loads, "shared_header_self_balanced_remote_port_units": header_units,
            "neighbor_and_remote_port_contract": patch})
    return outputs


def main():
    target = OUT / "result-v5.json"
    if target.exists():
        raise FileExistsError("preserve existing evidence")
    config = json.loads((OUT / "input-v5.json").read_text())
    verify(config["source_sha256"])
    read = lambda key: json.loads((ROOT / config[key]).read_text())
    layout, unit, cache = (read(k) for k in ("layout", "timber_unit_geometry", "geometry_cache"))
    direct = read("direct_timber_geometry")
    results = evaluate(config, layout, shaft_inputs(layout, unit, cache), direct)
    verify(config["source_sha256"])
    pins = config["source_sha256"] | {str((OUT/"input-v5.json").relative_to(ROOT)): sha(OUT/"input-v5.json"), str(Path(__file__).relative_to(ROOT)): sha(Path(__file__))}
    target.write_text(json.dumps({"status": "CONDITIONAL_RIGID_GEOMETRY_AND_WORK_CONTRACT_ONLY", "source_sha256": pins,
        "results": results, "limits": config["limits"], "release": {"current_actions": False, "joint_stiffness": False,
        "complete_joint_acceptance": False, "capacity": False, "fabrication": False}, "K_native_CAD_global_solve_used": False}, indent=2, allow_nan=False)+"\n")
    print(json.dumps({"input_sha256": sha(OUT/"input-v5.json"), "helper_sha256": sha(Path(__file__)), "result_sha256": sha(target), "bytes": target.stat().st_size}))


if __name__ == "__main__":
    main()
