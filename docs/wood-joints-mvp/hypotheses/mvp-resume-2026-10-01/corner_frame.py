"""Integrate the isolated top-corner correction into the simple elastic frame.

Reuse all unchanged source body contributions. Replace the five affected
body projections and the two cleat stiffnesses; retain panel-screw assumptions
explicitly. Output directories preserve each completed or failed calculation.
"""

import argparse
import copy
import fcntl
import importlib.util
import json
import sys
import time
from itertools import product
from pathlib import Path

import numpy as np
import top_corner_actions as accounting
from scipy import sparse

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
BASE = accounting.BASE
COMP = accounting.COMP
NATIVE = BASE / "current-frame-pure-solid-matrix-export-native-attempt01"
sys.path.insert(0, str(ROOT))
T = np.array([0.0, 0.642787610, 0.766044443])
T /= np.linalg.norm(T)
PAIR = [(0, 0), (1, 1), (2, 2), (0, 1), (0, 2), (1, 2)]
BLOCKS = set(accounting.BLOCK_HOSTS)
CHANGED = sorted(BLOCKS | {"base_side_left", "base_side_right", "base_rail_top"})
sha, read, require = accounting.sha, accounting.read, accounting.require


def write(path, value):
    path.write_text(json.dumps(value, indent=2, allow_nan=False) + "\n")


def module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


def engineering_stiffness(constants, axes):
    from fea.wood_joint_patch_materials import validate_engineering_constants

    local = np.linalg.inv(
        validate_engineering_constants(constants)["compliance_matrix_mpa_inv"]
    )
    rotation = np.array([axes[k] for k in ("L", "R", "T")]).T
    require(
        np.max(abs(rotation.T @ rotation - np.eye(3))) < 1e-8, "invalid material axes"
    )
    columns = []
    for a, b in PAIR:
        strain = np.zeros((3, 3))
        strain[a, b] = strain[b, a] = 1 if a == b else 0.5
        rotated_strain = rotation.T @ strain @ rotation
        vector = np.array(
            [rotated_strain[i, j] * (1 if i == j else 2) for i, j in PAIR]
        )
        stress_vector = local @ vector
        stress = np.zeros((3, 3))
        for (i, j), value in zip(PAIR, stress_vector, strict=True):
            stress[i, j] = stress[j, i] = value
        global_stress = rotation @ stress @ rotation.T
        columns.append([global_stress[i, j] for i, j in PAIR])
    result = np.array(columns).T
    require(np.max(abs(result - result.T)) < 1e-7, "asymmetric constitutive matrix")
    return (result + result.T) / 2


def brick_stiffness(positions, constants, axes):
    from fea.floor_recess_mesh import shape20
    from fea.wood_joint_reduced_members import shape20_derivatives

    constitutive = engineering_stiffness(constants, axes)
    points, weights = np.polynomial.legendre.leggauss(3)
    stiffness, volumes = np.zeros((60, 60)), np.zeros(20)
    for indices in product(range(3), repeat=3):
        natural = points[list(indices)]
        derivatives = shape20_derivatives(natural)
        jacobian = positions.T @ derivatives
        determinant = float(np.linalg.det(jacobian))
        require(determinant > 0, "nonpositive cleat Jacobian")
        gradients = derivatives @ np.linalg.inv(jacobian)
        strain = np.zeros((6, 60))
        for i in range(3):
            strain[i, i::3] = gradients[:, i]
        for k, (i, j) in enumerate(PAIR[3:], start=3):
            strain[k, i::3] = gradients[:, j]
            strain[k, j::3] = gradients[:, i]
        dv = determinant * float(np.prod(weights[list(indices)]))
        stiffness += strain.T @ constitutive @ strain * dv
        volumes += shape20(natural) * dv
    return (stiffness + stiffness.T) / 2, volumes


def point_terms(body, point, direction, model, coordinates, row_for):
    from fea.wood_joint_reduced_members import _inverse_shape20

    point = np.array(point)
    for element in model["physical_body_elements"][body]:
        kind, ids, _ = model["elements"][str(element)]
        require(kind == "C3D20", "unsupported projection element")
        positions = np.array([coordinates[n] for n in ids])
        if np.any(point < positions.min(axis=0) - 1e-6) or np.any(
            point > positions.max(axis=0) + 1e-6
        ):
            continue
        inverse = _inverse_shape20(point, positions)
        if inverse is None:
            continue
        require(
            np.linalg.norm(inverse[1] @ positions - point) < 1e-6,
            "point map lost position",
        )
        return {
            row_for[(node, d + 1)]: float(weight * direction[d])
            for node, weight in zip(ids, inverse[1], strict=True)
            for d in range(3)
            if weight * direction[d] != 0
        }
    raise ValueError(f"new connector point outside {body}: {point.tolist()}")


def build(output):
    import cadquery as cq

    from fea.horizontal_panel_frame import distribute_wrench, traction_wrench
    from fea.wood_joint_patch_materials import material_scenario

    started = time.monotonic()
    baseline = read(HERE / "simple-frame-results.json")
    assessment = read(COMP / "assessment.json")
    old_inputs_path = COMP / "inputs.json"
    require(
        sha(old_inputs_path) == assessment["input_record_sha256"],
        "changed original reduction input record",
    )
    original_pins = read(old_inputs_path)["source_sha256"]
    paths = [
        accounting.MODEL,
        accounting.LOADS,
        NATIVE / "model.sti",
        NATIVE / "model.dof",
        BASE
        / "current-frame-pure-solid-export-assessment-method-attempt01/assess_matrixstorage.py",
        BASE
        / "current-frame-free-body-condensation-preflight-attempt01/condensation.py",
        BASE / "current-elastic-quotient-method-preflight-attempt02/quotient_method.py",
    ]
    pins = {p: original_pins[str(p.relative_to(ROOT))] for p in paths}
    pins.update({COMP / p: h for p, h in assessment["outputs_sha256"].items()})
    pins[COMP / "assessment.json"] = baseline["source_sha256"]["assessment.json"]
    contact_path = HERE / "top-corner-contact-geometry.json"
    contact = read(contact_path)
    require(
        contact["producer_sha256"] == sha(HERE / "top_corner_contact.py"),
        "changed prepared contact producer",
    )
    pins.update({ROOT / p: h for p, h in contact["source_sha256"].items()})
    pins.update(
        {
            contact_path: sha(contact_path),
            HERE / "simple-frame-results.json": sha(HERE / "simple-frame-results.json"),
        }
    )
    for relative in [
        "fea/floor_recess_mesh.py",
        "fea/wood_joint_reduced_members.py",
        "fea/horizontal_panel_frame.py",
        "fea/wood_joint_patch_materials.py",
        "fea/generated/ccx_2.23.pdf",
    ]:
        pins[ROOT / relative] = sha(ROOT / relative)
    require(
        pins[ROOT / "fea/generated/ccx_2.23.pdf"]
        == "a0bf3fc03f374912ff2bf28da3f7dfb6a61428dd7f41b281a2e7e1fdb318f330",
        "changed pinned solver manual",
    )
    for p, h in pins.items():
        require(sha(p) == h, "changed frame-update input: " + str(p))
    output.mkdir(exist_ok=False)
    write(
        output / "inputs.json",
        {
            "producer_sha256": sha(Path(__file__)),
            "source_sha256": {str(p.relative_to(ROOT)): h for p, h in pins.items()},
            "native_launch": False,
        },
    )
    (output / "corner_frame.py.snapshot").write_bytes(Path(__file__).read_bytes())
    parser = module(paths[4], "corner_frame_parser")
    helper = module(paths[5], "corner_frame_condensation")
    quotient = module(paths[6], "corner_frame_quotient")
    source = parser.load_frame_source_model(accounting.MODEL)
    model = source["model"]
    body_names = assessment["body_names_in_rigid_column_order"]
    require(list(source["bodies"]) == body_names, "changed body column order")
    labels = parser.parse_dof_file(NATIVE / "model.dof")
    row_for = {label: i for i, label in enumerate(labels)}
    owners = np.array([source["owner_by_node"][node] for node, _ in labels])
    parsed = parser.parse_upper_triangle_file(
        NATIVE / "model.sti", len(labels), owner_by_row=owners, owner_names=body_names
    )
    parser.require_no_cross_body_coupling(parsed)
    K = parsed["matrix"]
    old_coordinates = source["coordinates"]
    coordinates = {n: np.array(p).copy() for n, p in old_coordinates.items()}
    for block in BLOCKS:
        center = source["centroids"][block]
        for node in source["bodies"][block]:
            old = coordinates[node]
            coordinates[node] = old + T * (
                (139.7 / 88.9 - 1) * (T @ (old - center)) - 25.4
            )
    old_rows = read(COMP / "row-identities.json")
    removed = [
        r["row"]
        for r in old_rows
        if BLOCKS & {r["ownership"]["first_body"], r["ownership"]["second_body"]}
    ]
    require(len(removed) == 40, "expected forty original corner rows")
    retained = np.array([r["row"] for r in old_rows if r["row"] not in removed])
    rows = [copy.deepcopy(old_rows[i]) for i in retained]
    old_B = sparse.load_npz(COMP / "B.npz").tocsr()
    B = sparse.lil_matrix((len(retained) + 88, len(labels)))
    B[: len(retained)] = old_B[retained]
    proposal = read(HERE / "top-corner-correction/proposal.json")
    axes = {a["axis_id"]: a for p in proposal["proposals"] for a in p["axes"]}

    def add_row(record, first_point, second_point):
        i = len(rows)
        own = record["ownership"]
        direction = np.array(own["direction_global_xyz"])
        for body, point, sign in [
            (own["first_body"], first_point, -1),
            (own["second_body"], second_point, 1),
        ]:
            for dof, value in point_terms(
                body, point, sign * direction, model, coordinates, row_for
            ).items():
                B[i, dof] += value
        record["row"] = i
        rows.append(record)

    for row in old_rows:
        if row["row"] not in removed or row["ownership"]["role"] != accounting.LATERAL:
            continue
        record = copy.deepcopy(row)
        axis = row["row_id"].rsplit("/", 1)[0]
        revision = axes[axis]
        point = (
            np.array(row["ownership"]["point_mm"])
            + revision["axis_translation_T_mm"] * T
        )
        record["ownership"]["point_mm"] = point.tolist()
        record["law"]["stiffness_N_per_mm"] *= (
            revision["nominal_bolt_diameter_mm"] / 6.35
        )
        record["source_row"] = row["row"]
        add_row(record, point, point)
    for cleat in contact["cleats"]:
        for i, row in enumerate(cleat["rows"]):
            contact_row = row["kind"] == "contact"
            direction = -np.array(row["direction_xyz"])
            record = {
                "family": "unilateral_springa",
                "row_id": cleat["block"] + "/contact-cell-" + str(i)
                if contact_row
                else row["axis_id"] + "/outer-seat-axial-tie",
                "law": {
                    "stiffness_N_per_mm": row["stiffness_n_per_mm"],
                    "force_law": "k * max(q_mm, 0)",
                    "intended_law": "compression_only"
                    if contact_row
                    else "tension_only",
                },
                "ownership": {
                    "first_body": row["host"],
                    "second_body": cleat["block"],
                    "role": accounting.CONTACT
                    if contact_row
                    else "physical_bolt_outer_seat_tension",
                    "point_mm": row["point_mm"],
                    "direction_global_xyz": direction.tolist(),
                },
            }
            if contact_row:
                record["contact_area_mm2"] = row["area_mm2"]
                points = [row["point_mm"], row["point_mm"]]
            else:
                points = row["axial_law"]["outer_seat_points_xyz_mm"]
                record["outer_seat_points_mm"] = points
                record["nominal_washer_area_mm2"] = row["nominal_washer_area_mm2"]
            add_row(record, *points)
    require(len(rows) == 1888, "incomplete revised connector inventory")
    for i, row in enumerate(rows):
        row["row"] = i
    B = B.tocsr()
    with np.load(COMP / "operators.npz", allow_pickle=False) as data:
        old_H, old_D, old_e, W = [data[k].copy() for k in ("H", "D", "e", "W")]
    H, e, D = np.zeros((1888, 1888)), np.zeros((1888, 12)), np.zeros((1888, 300))
    H[: len(retained), : len(retained)] = old_H[np.ix_(retained, retained)]
    e[: len(retained)] = old_e[retained]
    D[: len(retained)] = old_D[retained]
    F = np.zeros((len(labels), 12))
    for case_index, case in enumerate(read(accounting.LOADS)["cases"]):
        for offset, kind in enumerate(["gravity_nodal_map", "climber_nodal_map"]):
            for node, force in case[kind].items():
                for direction, value in enumerate(force, start=1):
                    F[row_for[(int(node), direction)], 2 * case_index + offset] = value
    mass_changes, body_reports = [], []
    members = {
        m["member_id"]: m
        for m in read(BASE / "reduced-static-attempt01/model-inputs.json")["members"]
    }
    for body in CHANGED:
        body_id = body_names.index(body)
        dofs = np.flatnonzero(owners == body_id)
        body_labels = [labels[int(i)] for i in dofs]
        old_center, old_R, old_Q = helper.rigid_basis(body_labels, old_coordinates)
        center, R, Q = helper.rigid_basis(body_labels, coordinates)
        old_body_K = K[dofs][:, dofs].tocsr()
        new_body_K = old_body_K
        old_F = F[dofs].copy()
        new_F = old_F.copy()
        info = {"body": body, "physical_dofs": len(dofs)}
        if body in BLOCKS:
            element_ids = model["physical_body_elements"][body]
            require(len(element_ids) == 1, "cleat must contain one source brick")
            _, nodes, _ = model["elements"][str(element_ids[0])]
            axes_body = model["material_binding"]["orientation_overrides"][body][
                "material_axes_global_xyz"
            ]
            constants = material_scenario()["calculix_engineering_constants"]
            expected_old, _ = brick_stiffness(
                np.array([old_coordinates[n] for n in nodes]), constants, axes_body
            )
            revised, volume_weights = brick_stiffness(
                np.array([coordinates[n] for n in nodes]), constants, axes_body
            )
            element_labels = [(node, d) for node in nodes for d in (1, 2, 3)]
            permutation = [element_labels.index(label) for label in body_labels]
            expected_old = expected_old[np.ix_(permutation, permutation)]
            reference = old_body_K.toarray()
            mismatch = float(
                np.max(abs(reference - expected_old)) / np.max(abs(reference))
            )
            require(
                mismatch <= 1e-6,
                "cleat assembly does not reproduce authenticated original K",
            )
            new_body_K = sparse.csr_matrix(revised[np.ix_(permutation, permutation)])
            info["original_native_brick_matrix_relative_max_difference"] = mismatch
        delta = np.zeros(6)
        if body != "base_rail_top":
            old_shape = cq.importers.importStep(
                str(ROOT / members[body]["current_finished_step_binding"]["path"])
            ).val()
            new_shape = cq.importers.importStep(
                str(HERE / "top-corner-correction" / (body + ".step"))
            ).val()
            old_mass, new_mass = (
                old_shape.Volume() * 500e-9,
                new_shape.Volume() * 500e-9,
            )
            old_force, new_force = (
                np.array([0.0, 0.0, -9.80665 * old_mass]),
                np.array([0.0, 0.0, -9.80665 * new_mass]),
            )
            delta[:3] = new_force - old_force
            delta[3:] = np.cross(new_shape.Center().toTuple(), new_force) - np.cross(
                old_shape.Center().toTuple(), old_force
            )
            mass_changes.append(
                {
                    "body": body,
                    "wood_mass_change_kg": new_mass - old_mass,
                    "gravity_wrench_change_about_global_origin_n_nmm": delta.tolist(),
                }
            )
        unique_nodes = sorted(source["bodies"][body])
        local_row_for = {label: i for i, label in enumerate(body_labels)}
        positions = np.array([coordinates[n] for n in unique_nodes])
        old_positions = np.array([old_coordinates[n] for n in unique_nodes])
        for column in range(0, 12, 2):
            nodal = np.array(
                [
                    [old_F[local_row_for[(n, d)], column] for d in (1, 2, 3)]
                    for n in unique_nodes
                ]
            )
            total_force = nodal.sum(axis=0) + delta[:3]
            total_moment_global = (
                np.sum(np.cross(old_positions, nodal), axis=0) + delta[3:]
            )
            if body in BLOCKS:
                weights_for_node = dict(
                    zip(nodes, volume_weights / volume_weights.sum(), strict=True)
                )
                values = traction_wrench(
                    positions,
                    np.array([weights_for_node[n] for n in unique_nodes]),
                    total_force,
                    total_moment_global - np.cross(center, total_force),
                    center,
                )
            else:
                values = nodal + distribute_wrench(
                    positions,
                    delta[:3],
                    delta[3:] - np.cross(center, delta[:3]),
                    center,
                )
            for n, value in zip(unique_nodes, values, strict=True):
                for d in (1, 2, 3):
                    new_F[local_row_for[(n, d)], column] = value[d - 1]

        def contributions(
            body_K, basis, orthogonal, projection, loads, description, info=info
        ):
            factor, system = helper.factor_bordered(body_K, basis)
            active = np.flatnonzero(np.diff(projection.indptr))
            Bb = projection[active]
            raw = np.column_stack([Bb.T.toarray(), loads])
            elastic = raw - orthogonal @ (orthogonal.T @ raw)
            solved = quotient.solve_quotient_chunk(
                factor, system, body_K, basis, elastic
            )
            require(
                solved["status"] == quotient.PASS_ELASTIC_QUOTIENT_SCREEN,
                description + ": " + solved["status"],
            )
            displacement = solved["displacement_mm"]
            info[description + "_max_relative_kkt_residual"] = solved[
                "KKT_upper_force_residual_relative"
            ]
            info[description + "_corrections"] = solved["corrections"]
            return (
                active,
                Bb @ displacement[:, : len(active)],
                Bb @ displacement[:, len(active) :],
                np.asarray(projection @ basis),
                basis.T @ loads,
            )

        old_active, old_contribution, old_load_motion, old_map, _old_load = (
            contributions(
                old_body_K, old_R, old_Q, old_B[:, dofs].tocsr(), old_F, "original"
            )
        )
        require(
            np.max(abs(old_map - old_D[:, 6 * body_id : 6 * body_id + 6])) < 1e-8,
            "original projection/wrench map mismatch",
        )
        locations = {int(original): new for new, original in enumerate(retained)}
        selected = [
            i for i, original in enumerate(old_active) if int(original) in locations
        ]
        new_locations = [locations[int(old_active[i])] for i in selected]
        H[np.ix_(new_locations, new_locations)] -= old_contribution[
            np.ix_(selected, selected)
        ]
        e[new_locations] -= old_load_motion[selected]
        active, contribution, load_motion, body_D, body_W = contributions(
            new_body_K, R, Q, B[:, dofs].tocsr(), new_F, "revised"
        )
        H[np.ix_(active, active)] += contribution
        e[active] += load_motion
        D[:, 6 * body_id : 6 * body_id + 6] = body_D
        W[6 * body_id : 6 * body_id + 6] = body_W
        info["old_datum_mm"], info["new_datum_mm"] = (
            old_center.tolist(),
            center.tolist(),
        )
        body_reports.append(info)
        F[dofs] = new_F
        print(body, "updated elastic body and connectors", flush=True)
    H_scale = float(np.linalg.norm(H, ord=np.inf))
    reciprocity = float(np.linalg.norm(H - H.T, ord=np.inf) / H_scale)
    H_symmetric = (H + H.T) / 2
    eigenvalue = float(np.linalg.eigvalsh(H_symmetric)[0])
    require(
        reciprocity <= 1e-8 and eigenvalue >= -1e-9 * H_scale,
        "revised frame compliance consistency",
    )
    mass = baseline["modeled_mass_kg"] + sum(
        r["wood_mass_change_kg"] for r in mass_changes
    )
    np.savez_compressed(output / "operators.npz", H=H, D=D, e=e, W=W, F=F)
    sparse.save_npz(output / "B.npz", B)
    write(output / "row-identities.json", rows)
    write(
        output / "model.json",
        {
            "schema": "simple_corrected_frame_model/v1",
            "candidate": baseline["candidate"],
            "source_revision": baseline["revision_id"],
            "development_revision": "top-outer-4x6-cleats-5_16-side-bolts-v1",
            "body_names": body_names,
            "body_nodes": model["physical_body_nodes"],
            "physical_node_coordinates_mm": {
                str(n): p.tolist() for n, p in coordinates.items()
            },
            "physical_elements": {
                str(i): model["elements"][str(i)]
                for ids in model["physical_body_elements"].values()
                for i in ids
            },
            "connector_rows_file": "row-identities.json",
            "proposed_corner_axes": proposal["proposals"],
            "material_binding": model["material_binding"],
            "modeled_mass_kg": mass,
            "planning_accessory_mass_kg": 25.0,
            "dead_load_factor": (mass + 25) / mass,
            "wood_mass_changes": mass_changes,
            "reviewed_geometry_changed": False,
            "physical_release": False,
        },
    )
    report = {
        "schema": "simple_corrected_frame_operators/v1",
        "status": "PASS_UPDATED_ELASTIC_FRAME_OPERATORS",
        "producer_sha256": sha(Path(__file__)),
        "source_sha256": {str(p.relative_to(ROOT)): h for p, h in pins.items()},
        "bodies_recomputed": body_reports,
        "removed_original_rows": removed,
        "dimensions": {
            "physical_dofs": len(labels),
            "connector_rows": len(rows),
            "rigid_coordinates": 300,
        },
        "compliance_checks": {
            "relative_reciprocity": reciprocity,
            "minimum_symmetric_eigenvalue_mm_per_n": eigenvalue,
            "infinity_norm_mm_per_n": H_scale,
        },
        "modeled_mass_kg": mass,
        "dead_load_factor": (mass + 25) / mass,
        "elapsed_seconds": time.monotonic() - started,
        "limits": [
            "Unchanged bodies reuse original conditional elastic compliance; filled-bore gross member stiffness remains the source idealization.",
            "66 Hillman axial/lateral spring properties remain unsupported parametric assumptions; zero-withdrawal failure remains preserved.",
            "Existing hardware gravity is carried forward; the unchanged 25 kg proportional accessory allowance remains a placement assumption, not a delivered hardware census.",
            "Contact uses sixteen exact-area centroid cells on each corrected corner face, the existing penalty and zero initial gaps. Lateral gaps and preload remain omitted.",
            "Native export authentication and formal qualification are not transferred to this calculated development model.",
        ],
        "native_launch": False,
        "complete_joint_acceptance": False,
        "reviewed_geometry_changed": False,
        "physical_release": False,
    }
    for p, h in pins.items():
        require(sha(p) == h, "input changed during frame update")
    report["output_sha256"] = {
        name: sha(output / name)
        for name in ["operators.npz", "B.npz", "row-identities.json", "model.json"]
    }
    write(output / "operator-assessment.json", report)
    print(report["status"], flush=True)


def solve(output):
    import simple_frame as frame

    assessment = read(output / "operator-assessment.json")
    for name, digest in assessment["output_sha256"].items():
        require(sha(output / name) == digest, "changed updated frame input")
    rows = read(output / "row-identities.json")
    with np.load(output / "operators.npz", allow_pickle=False) as data:
        H, D, e, W = [data[k].copy() for k in ("H", "D", "e", "W")]
    H, D, e, W, k, uni, normals, tangents, transform, floors = frame.lump_floor(
        H, D, e, W, rows
    )
    H = (H + H.T) / 2
    baseline = read(HERE / "simple-frame-results.json")
    response, cases = {}, []
    started = time.monotonic()
    for index, column in enumerate(range(0, 12, 2)):
        case = baseline["cases"][index]["case_id"]
        try:
            force, rigid, motion, bearing, result = frame.solve_case(
                H,
                D,
                assessment["dead_load_factor"] * e[:, column] + e[:, column + 1],
                assessment["dead_load_factor"] * W[:, column] + W[:, column + 1],
                k,
                uni,
                normals,
                tangents,
            )
            result["peak_body_translation_mm"] = float(
                np.linalg.norm(rigid.reshape(-1, 6)[:, :3], axis=1).max()
            )
            response.update(
                {
                    case + "_force_n": transform.T @ force,
                    case + "_rigid_coordinates": rigid,
                    case + "_lumped_motion_mm": motion,
                    case + "_bearing_mask": bearing,
                }
            )
        except RuntimeError as error:
            result = {"status": "STOP_STATIC_SCENARIO", "reason": str(error)}
        cases.append({"case_id": case, **result})
        print(case, result["status"], flush=True)
    np.savez_compressed(output / "frame-response.npz", **response)
    write(
        output / "frame-results.json",
        {
            "schema": "simple_corrected_frame_six_case_response/v1",
            "operator_assessment_sha256": sha(output / "operator-assessment.json"),
            "solver_helper_sha256": sha(Path(frame.__file__)),
            "producer_sha256": sha(Path(__file__)),
            "response_sha256": sha(output / "frame-response.npz"),
            "cases": cases,
            "floor_footprints": floors,
            "modeled_mass_kg": assessment["modeled_mass_kg"],
            "planning_accessory_mass_kg": 25.0,
            "dead_load_factor": assessment["dead_load_factor"],
            "elapsed_seconds": time.monotonic() - started,
            "assumptions": assessment["limits"],
            "complete_joint_acceptance": False,
            "physical_release": False,
        },
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("stage", choices=("build", "solve"))
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    lock = ROOT / "docs/wood-joints-mvp/luna-max-native-run-ledger.lock"
    with lock.open("a") as stream:
        fcntl.flock(stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
        require(
            read(lock.with_suffix(".json"))["slot"]["state"] == "idle",
            "shared analysis slot occupied",
        )
        require(
            not args.output.exists()
            if args.stage == "build"
            else not any(
                (args.output / name).exists()
                for name in ("frame-results.json", "frame-response.npz")
            ),
            "output already exists; preserve the recorded calculation",
        )
        try:
            (build if args.stage == "build" else solve)(args.output)
        except Exception as error:
            if args.output.is_dir():
                write(
                    args.output / (args.stage + "-failure.json"),
                    {
                        "exception": str(error),
                        "producer_sha256": sha(Path(__file__)),
                        "physical_release": False,
                    },
                )
            raise
