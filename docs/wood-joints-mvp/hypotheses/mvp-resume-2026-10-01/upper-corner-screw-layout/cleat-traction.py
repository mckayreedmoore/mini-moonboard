"""Recover current right-cleat applied actions without solving its mechanics.

Only frozen-state quadrature, matrix multiplication and wrench accounting run.
An unexplained moment is never added to the applied action inventory.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
BASE = HERE.parents[1] / "mvp-acceleration-2026-09-28"
RAW = HERE / "rawlocal/cleat-traction"
CLEAT = "top_outer_right_cleat"
CASES = ("a12-rear", "a12-forward", "a12-left", "k12-right", "k12-rear", "a1-rear")
BLOCK = HERE / "rawlocal/upper-right-block/attempt01/checks.json"
PAIRS = [
    HERE / f"rawlocal/upper-right-{f}-pair/attempt01/checks.json"
    for f in ("rail", "side")
]
HELPER = HERE / "upper-right-combined-transfer.py"
OPERATORS = HERE / "operators-attempt02/operators.npz"
MODEL = HERE / "operators-attempt02/model.json"
INPUTS = HERE / "operators-attempt02/model-inputs.json"
COMPARISON = HERE / "frame-250-attempt02/comparison.json"
COMPONENT = HERE / "bolted-replay-results/corner-attempt01/component-results.json"
DOF = BASE / "current-frame-pure-solid-matrix-export-native-attempt01/model.dof"
PARSER = (
    BASE
    / "current-frame-pure-solid-export-assessment-method-attempt01/assess_matrixstorage.py"
)
PINS = {
    BLOCK: "0b0b392b9e5e411173395671878c09e0be303abd4885f48d1e7e7b61d8f6a89b",
    PAIRS[0]: "e0cccb56abb94ed16c322da888cd64a9904c4e49d1e34f573a6903c8b8b98d3d",
    PAIRS[1]: "b507a5a501737c89814a471eee6a12749a3c54224f5444b2c5d583020e875ba7",
    HELPER: "fba852724b82ee3cd28b0318bfdf156ac1786f85ac26257698d8d103c26c62b0",
    OPERATORS: "c9483639c69c0696b29f3fd69522e6c9a8e673aa7ce82277788103b14c955ba3",
    MODEL: "b5f9b87b70c4a9920372a3443a55e37dfe34351fb9ac8210b299c1360fb93626",
    INPUTS: "e2109cabed9fcbc0a14346ef63b707abb1aed358ebf5fa126b2cba216aa771cc",
    COMPARISON: "bea6cbc330af3cdb20499d774a8f6bb24481d687c3150adb01ede18e4c1d50ca",
    COMPONENT: "401b8876dc3a96b553c847f1029a5a9200ba3f45af5493f64edd61fdc6bc42b6",
    DOF: "532f732e5b2ed88d96c544b73bcc33168a65942ff6c5155f30c6d4ade9173f1d",
    PARSER: "7abfeb3b02843588651b440dba4a86ae3f85106557383225a50c09b5cb080632",
    HERE
    / "block-group-resistance.py": "e5df5f81168a0e700948816a5c292c521593b328ab86fb72b1a2e2f0cd98b3b0",
    HERE
    / "block-group-resistance.md": "8bcfbef56e69fb203fcc87a95c16df4d6eb16b7c544d83359dbf0b74c66bab77",
}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def read(path):
    return json.loads(path.read_text())


def dump(path, data):
    path.write_text(json.dumps(data, indent=2, sort_keys=True, allow_nan=False) + "\n")


def authenticate(pins):
    for path, digest in pins.items():
        require(sha(path) == digest, f"frozen source differs: {path}")


def frozen_module(path, name):
    sys.dont_write_bytecode = True
    spec = importlib.util.spec_from_file_location(name, path)
    require(spec is not None and spec.loader is not None, f"module unavailable: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def skew(vector):
    x, y, z = vector
    return np.array([[0.0, -z, y], [z, 0.0, -x], [-y, x, 0.0]])


def shifted(wrench, old, new):
    value = np.array(wrench, dtype=float)
    value[3:] += np.cross(np.array(old) - new, value[:3])
    return value


def action(kind, identity, point, force, **metadata):
    return {
        "kind": kind,
        "identity": identity,
        "point_xyz_mm": np.asarray(point).tolist(),
        "force_xyz_n": np.asarray(force).tolist(),
        **metadata,
    }


def wrench(actions, datum):
    value = np.zeros(6)
    for a in actions:
        force = np.array(a["force_xyz_n"])
        value[:3] += force
        value[3:] += np.cross(np.array(a["point_xyz_mm"]) - datum, force)
    return value


def wood_seat(helper, bolt, end_index, geometry, n, B, kwood):
    """Recover pressure on its own nominal outer wood annulus, with signed tilt.

    Nut wood force is -T*n and its centroid direction is +B*slope_unit.
    Head wood force is +T*n and its centroid direction is -B*slope_unit.
    A point-force inventory includes the pressure moment once, without adding
    the saved end moment as a second independent couple.
    """
    length = geometry["host_length_mm"] + geometry["cleat_length_mm"]
    p = np.array(bolt["interface_point_xyz_mm"])
    center = p + (end_index * length - geometry["host_length_mm"]) * n
    end = bolt["end_contacts"][end_index]
    record = end["wood_contact"]
    inner, outer = geometry["washer_ID_max_mm"] / 2, geometry["washer_OD_min_mm"] / 2
    area, cosine, _ = helper.annulus(inner, outer)
    abscissa = np.polynomial.legendre.leggauss(8)[0]
    radii = inner + (abscissa + 1) * (outer - inner) / 2
    angles = (np.arange(32) + 0.5) * (2 * np.pi / 32)
    sine = np.repeat(radii, 32) * np.tile(np.sin(angles), 8)
    slope = np.array(bolt["end_slope_vectors_rad"][end_index])
    norm = float(np.linalg.norm(slope))
    unit = slope / norm if norm else np.array([1.0, 0.0])
    signed = 1 if end_index == 1 else -1
    pressure_frame = signed * B @ np.column_stack((unit, [-unit[1], unit[0]]))
    offsets = np.column_stack((cosine, sine)) @ pressure_frame.T
    pressure = kwood * np.maximum(record["closure_mm"] + record["tilt_rad"] * cosine, 0)
    normal_loads = area * pressure
    inward = -signed * n
    points = center + offsets
    actions = [
        action(
            "outer_wood_washer_quadrature",
            bolt["axis_id"],
            point,
            load * inward,
            end="cleat_nut" if end_index else "host_head",
            quadrature_index=i,
            pressure_mpa=float(pressure[i]),
            quadrature_area_mm2=float(area[i]),
        )
        for i, (point, load) in enumerate(zip(points, normal_loads, strict=True))
    ]
    total = float(np.sum(normal_loads))
    centroid = (
        center + np.sum(offsets * normal_loads[:, None], axis=0) / total
        if total
        else None
    )
    recovered = wrench(actions, center)
    expected_moment = np.cross(
        n, B @ np.array(bolt["end_moment_vectors_in_transverse_basis_nmm"][end_index])
    )
    comparison = {
        "axis_id": bolt["axis_id"],
        "end": "cleat_nut" if end_index else "host_head",
        "nominal_outer_wood_seat_xyz_mm": center.tolist(),
        "signed_pressure_frame_columns_xyz": pressure_frame.tolist(),
        "pressure_weighted_contact_centroid_xyz_mm": None
        if centroid is None
        else centroid.tolist(),
        "T_n": bolt["compatible_T_n"],
        "pressure_integral_n": total,
        "pressure_integral_minus_T_n": total - bolt["compatible_T_n"],
        "recovered_force_and_own_pressure_moment_at_seat_n_nmm": recovered.tolist(),
        "opposite_saved_beam_end_moment_xyz_nmm": (
            -np.array(end["moment_on_beam_xyz_nmm"])
        ).tolist(),
        "correct_signed_local2_moment_xyz_nmm": expected_moment.tolist(),
        "moment_minus_correct_local2_vector_nmm": (
            recovered[3:] - expected_moment
        ).tolist(),
        "saved_head_wood_moment_balance_residual_nmm": end[
            "moment_balance_residual_nmm"
        ],
        "offset_includes_beam_end_translation": False,
    }
    require(
        abs(total - bolt["compatible_T_n"]) < 1e-7,
        "saved annular pressure does not recover T",
    )
    require(
        np.max(abs(recovered[3:] - expected_moment)) < 1e-6,
        "signed washer moment recovery differs",
    )
    return actions, comparison


def beam_diagnostic(helper, bolt, spec, datum, number, saved_gradient):
    """Evaluate the frozen beam gradient and its rigid virtual work, no solve."""
    geometry, n, B = (
        spec["geometry"],
        np.array(spec["bolt_axis_head_to_nut_xyz"]),
        np.array(spec["transverse_basis_xyz"]),
    )
    length = geometry["host_length_mm"] + geometry["cleat_length_mm"]
    elastic, geometric, samples, _, _ = helper.beam_model(geometry, 1.0)
    K, G = elastic[:34, :34], geometric[:34, :34]
    nodes = np.r_[
        np.linspace(0, geometry["host_length_mm"], 9),
        np.linspace(geometry["host_length_mm"], length, 9)[1:],
    ]
    p = np.array(bolt["interface_point_xyz_mm"])
    positions = p + (nodes[:, None] - geometry["host_length_mm"]) * n
    displacement, slopes = (
        np.array(bolt["beam_node_displacements_in_basis_mm"]),
        np.array(bolt["beam_node_slopes_in_basis_rad"]),
    )
    terms, gradient = [], []
    virtual_work = {
        k: np.zeros(6)
        for k in ("elastic", "geometric_T", "bore", "end_slope", "gradient_residual")
    }
    for plane in range(2):
        q = np.empty(34)
        q[::2], q[1::2] = displacement[plane], length * slopes[plane]
        bore = np.zeros(34)
        for sample, field in zip(samples, bolt["bore_fields"], strict=True):
            row, _, location, receiver = sample
            require(
                abs(location - field["x_mm"]) < 1e-10 and receiver == field["receiver"],
                "bore sample identity differs",
            )
            bore -= row[:34] * field["force_on_beam_in_basis_n"][plane]
        end = np.zeros(34)
        end[1] = bolt["end_moment_vectors_in_transverse_basis_nmm"][0][plane] / length
        end[33] = bolt["end_moment_vectors_in_transverse_basis_nmm"][1][plane] / length
        fields = {
            "elastic": K @ q,
            "geometric_T": bolt["compatible_T_n"] * (G @ q),
            "bore": bore,
            "end_slope": end,
        }
        fields["gradient_residual"] = sum(fields.values())
        R = np.zeros((34, 6))
        R[::2, :3] = B[:, plane]
        for i, position in enumerate(positions):
            R[2 * i, 3:] = B[:, plane] @ (-skew(position - datum))
            R[2 * i + 1, 3:] = length * B[:, plane] @ (-skew(n))
        for name, values in fields.items():
            virtual_work[name] += R.T @ values
        terms.append({k: v.tolist() for k, v in fields.items()})
        gradient.extend(fields["gradient_residual"].tolist())
    gradient = np.array(gradient)
    saved = np.array(saved_gradient)[68 * number : 68 * number + 68]
    require(
        np.max(abs(gradient - saved)) < 1e-7,
        "arithmetic gradient does not reproduce saved beam residual",
    )
    endpoint_delta = B @ (displacement[:, -1] - displacement[:, 0])
    geometric_moment = bolt["compatible_T_n"] * np.cross(n, endpoint_delta)
    require(
        np.max(abs(virtual_work["geometric_T"][3:] - geometric_moment)) < 1e-6,
        "geometric-T endpoint identity differs",
    )
    return {
        "axis_id": bolt["axis_id"],
        "beam_end_displacement_difference_xyz_mm": endpoint_delta.tolist(),
        "geometric_T_rigid_rotation_work_xyz_nmm": geometric_moment.tolist(),
        "predicted_wood_action_minus_rigid_dual_geometric_term_n_nmm": np.r_[
            np.zeros(3), -geometric_moment
        ].tolist(),
        "rigid_virtual_work_by_term_n_nmm": {
            k: v.tolist() for k, v in virtual_work.items()
        },
        "gradient_by_plane_scaled_n": terms,
        "maximum_gradient_minus_saved_n": float(np.max(abs(gradient - saved))),
        "beam_end_slopes_in_basis_rad": slopes[:, [0, -1]].tolist(),
        "saved_relative_end_slopes_rad": bolt["end_slope_vectors_rad"],
        "host_head_relative_slope_frame_term_rad": (
            slopes[:, 0] - np.array(bolt["end_slope_vectors_rad"][0])
        ).tolist(),
    }


def group_recovery(helper, group, state, datum, seats):
    spec = group["model"]
    n, B = (
        np.array(spec["bolt_axis_head_to_nut_xyz"]),
        np.array(spec["transverse_basis_xyz"]),
    )
    require(
        np.max(abs(B.T @ B - np.eye(2))) < 1e-12
        and np.linalg.norm(np.cross(B[:, 0], B[:, 1]) - n) < 1e-12,
        "signed local2 basis is not right-handed about bolt n",
    )
    cleat_actions, host_actions, seat_records, diagnostics = [], [], [], []
    for number, bolt in enumerate(state["bolts"]):
        point = np.array(bolt["interface_point_xyz_mm"])
        for i, field in enumerate(bolt["bore_fields"]):
            force = -np.array(field["force_on_beam_xyz_n"])
            require(
                np.max(abs(-B @ np.array(field["force_on_beam_in_basis_n"]) - force))
                < 1e-9,
                "bore force basis differs",
            )
            where = point + (field["x_mm"] - spec["geometry"]["host_length_mm"]) * n
            record = action(
                "bore_station_resultant",
                bolt["axis_id"],
                where,
                force,
                x_mm=field["x_mm"],
                receiver=field["receiver"],
                quadrature_index=i,
            )
            (cleat_actions if field["receiver"] == "cleat" else host_actions).append(
                record
            )
        for end_index, target, body in (
            (0, host_actions, spec["host"]),
            (1, cleat_actions, CLEAT),
        ):
            actions, record = wood_seat(
                helper,
                bolt,
                end_index,
                spec["geometry"],
                n,
                B,
                spec["Kwood_mpa_per_mm_hypothesis"],
            )
            require(
                np.linalg.norm(
                    np.array(record["nominal_outer_wood_seat_xyz_mm"])
                    - seats[(bolt["axis_id"], body)]["seat_point_mm"]
                )
                < 1e-7,
                "own modeled outer wood seat differs from completed support geometry",
            )
            target.extend(actions)
            seat_records.append(record)
        diagnostic = beam_diagnostic(
            helper,
            bolt,
            spec,
            datum,
            number,
            state["mixed_scaled_gradient_components_n"],
        )
        diagnostic["host_rotation_xyz_rad"] = state["host_rotation_xyz_rad"]
        expected_frame = B.T @ np.cross(np.array(state["host_rotation_xyz_rad"]), n)
        require(
            np.max(
                abs(
                    np.array(diagnostic["host_head_relative_slope_frame_term_rad"])
                    - expected_frame
                )
            )
            < 1e-12,
            "host/end-slope frame contribution differs",
        )
        diagnostics.append(diagnostic)
    for cell in state["face_cells"]:
        cleat_actions.append(
            action(
                "face_cell",
                cell["row_id"],
                cell["point_xyz_mm"],
                cell["compression_n"] * n,
            )
        )
        host_actions.append(
            action(
                "face_cell",
                cell["row_id"],
                cell["point_xyz_mm"],
                -cell["compression_n"] * n,
            )
        )
    source_host = (
        np.sum(
            [b["wrench_on_host_at_face_datum_n_nmm"] for b in state["bolts"]], axis=0
        )
        + state["face_wrench_on_host_at_face_datum_n_nmm"]
    )
    saved_host = shifted(source_host, spec["face_datum_xyz_mm"], datum)
    host_physical, cleat_physical = (
        wrench(host_actions, datum),
        wrench(cleat_actions, datum),
    )
    host_error = host_physical - saved_host
    require(
        np.max(abs(host_error)) < 1e-6,
        "own host pressure/bore recovery differs from saved host wrench",
    )
    dual = -saved_host
    difference = cleat_physical - dual
    geometric = np.sum(
        [
            d["predicted_wood_action_minus_rigid_dual_geometric_term_n_nmm"]
            for d in diagnostics
        ],
        axis=0,
    )
    residual = np.sum(
        [
            d["rigid_virtual_work_by_term_n_nmm"]["gradient_residual"]
            for d in diagnostics
        ],
        axis=0,
    )
    elastic = np.sum(
        [d["rigid_virtual_work_by_term_n_nmm"]["elastic"] for d in diagnostics], axis=0
    )
    explained = geometric + residual - elastic - host_error
    explanation_error = difference - explained
    require(
        np.max(abs(explanation_error)) < 1e-6,
        "physical/dual discrepancy has unexplained mechanics terms",
    )
    return cleat_actions, {
        "case_id": state["case_id"],
        "host": spec["host"],
        "physical_applied_cleat_wrench_n_nmm": cleat_physical.tolist(),
        "physical_applied_host_wrench_n_nmm": host_physical.tolist(),
        "saved_host_wrench_n_nmm": saved_host.tolist(),
        "host_physical_minus_saved_n_nmm": host_error.tolist(),
        "saved_rigid_dual_cleat_wrench_n_nmm": dual.tolist(),
        "physical_cleat_minus_rigid_dual_n_nmm": difference.tolist(),
        "geometric_T_explanation_n_nmm": geometric.tolist(),
        "beam_rigid_gradient_residual_n_nmm": residual.tolist(),
        "elastic_rigid_virtual_work_roundoff_n_nmm": elastic.tolist(),
        "physical_minus_full_explanation_n_nmm": explanation_error.tolist(),
        "wood_seats": seat_records,
        "beam_diagnostics": diagnostics,
        "balancing_free_couple_added": False,
    }


def cut_inventory(actions, points, grain):
    """Finite point-action candidates only; retain disagreement and on-plane jumps."""
    output = []
    for identity, datum in points:
        datum = np.array(datum)
        distances = [(np.array(a["point_xyz_mm"]) - datum) @ grain for a in actions]
        buckets = {"before": [], "on": [], "after": []}
        for a, distance in zip(actions, distances, strict=True):
            buckets[
                "before" if distance < -1e-6 else "after" if distance > 1e-6 else "on"
            ].append(a)
        sums = {key: wrench(values, datum) for key, values in buckets.items()}
        output.append(
            {
                "station_identity": identity,
                "plane_datum_xyz_mm": datum.tolist(),
                "plane_normal_grain_xyz": grain.tolist(),
                "point_action_counts": {k: len(v) for k, v in buckets.items()},
                "external_point_sums_n_nmm": {k: v.tolist() for k, v in sums.items()},
                "before_plane_internal_on_negative_half_from_negative_actions_n_nmm": (
                    -sums["before"]
                ).tolist(),
                "before_plane_internal_on_negative_half_from_positive_actions_n_nmm": (
                    sums["on"] + sums["after"]
                ).tolist(),
                "after_plane_internal_on_negative_half_from_negative_actions_n_nmm": (
                    -sums["before"] - sums["on"]
                ).tolist(),
                "after_plane_internal_on_negative_half_from_positive_actions_n_nmm": sums[
                    "after"
                ].tolist(),
                "candidate_disagreement_negative_minus_positive_n_nmm": (
                    -sum(sums.values())
                ).tolist(),
                "equilibrated_timber_section_actions_established": False,
                "scope": "Requested axis bore resultants, sampled annular/face actions and original mapped nodal W only. No finished section, radial bore-wall traction field or real material-region sharing is inferred.",
            }
        )
    return output


def run(output):
    require(
        output.is_relative_to(RAW) and not output.exists(),
        "use a fresh owned rawlocal/cleat-traction attempt",
    )
    pins = dict(PINS)
    pins[Path(__file__).resolve()] = sha(Path(__file__).resolve())
    authenticate(pins)
    block, groups = read(BLOCK), [read(p) for p in PAIRS]
    for result in [block, *groups]:
        require(
            [s["case_id"] for s in result["states"]] == list(CASES),
            "six-case identities differ",
        )
        for relative, digest in result["source_sha256"].items():
            path = ROOT / relative
            require(
                path not in pins or pins[path] == digest, "conflicting source binding"
            )
            pins[path] = digest
    authenticate(pins)
    helper = frozen_module(HELPER, "cleat_traction_frozen_arithmetic")
    parser = frozen_module(PARSER, "cleat_traction_frozen_dof_parser")
    model, inputs, comparison, component = (
        read(p) for p in (MODEL, INPUTS, COMPARISON, COMPONENT)
    )
    datum = np.array(block["common_datum_xyz_mm"])
    nodes = sorted(set(model["body_nodes"][CLEAT]))
    coordinates = {
        n: np.array(model["physical_node_coordinates_mm"][str(n)]) for n in nodes
    }
    require(
        np.linalg.norm(np.mean(list(coordinates.values()), axis=0) - datum) < 1e-9,
        "common datum differs",
    )
    labels = parser.parse_dof_file(DOF)
    selected = [(i, n, d - 1) for i, (n, d) in enumerate(labels) if n in coordinates]
    require(len(selected) == 3 * len(nodes), "mapped body DOF census differs")
    body = model["body_names"].index(CLEAT)
    grain = np.array(
        next(
            m["reduced_geometry_descriptor"]["axis"]
            for m in inputs["members"]
            if m["member_id"] == CLEAT
        )
    )
    grain /= np.linalg.norm(grain)
    seats = {(s["axis_id"], s["body"]): s for s in component["washer_seats"]}
    all_actions, states = [], []
    with np.load(OPERATORS, allow_pickle=False) as operators:
        F, W = operators["F"], operators["W"]
        require(F.shape == (len(labels), 12), "load operator order differs")
        for index, case in enumerate(CASES):
            require(
                inputs["cases"][index]["case_id"] == case,
                "load column case identity differs",
            )
            actions, interfaces, cut_points = [], [], []
            completed = block["states"][index]
            for group in groups:
                applied, record = group_recovery(
                    helper, group, group["states"][index], datum, seats
                )
                reference = next(
                    h["compatible_reaction_on_rigid_cleat_n_nmm"]
                    for h in completed["hosts"]
                    if h["host"] == record["host"]
                )
                require(
                    np.max(
                        abs(
                            np.array(reference)
                            - record["saved_rigid_dual_cleat_wrench_n_nmm"]
                        )
                    )
                    < 1e-6,
                    "completed block dual reaction differs",
                )
                actions.extend(applied)
                interfaces.append(record)
                for bolt in group["states"][index]["bolts"]:
                    cut_points.append((bolt["axis_id"], bolt["interface_point_xyz_mm"]))
            node_forces = {n: np.zeros(3) for n in nodes}
            for row, node, direction in selected:
                node_forces[node][direction] = (
                    comparison["dead_load_factor"] * F[row, 2 * index]
                    + F[row, 2 * index + 1]
                )
            gravity = [
                action(
                    "original_current_mapped_W_node",
                    str(n),
                    coordinates[n],
                    node_forces[n],
                    node_id=n,
                )
                for n in nodes
            ]
            original_W = (
                comparison["dead_load_factor"] * W[6 * body : 6 * body + 6, 2 * index]
                + W[6 * body : 6 * body + 6, 2 * index + 1]
            )
            original_W = original_W.copy()
            original_W[3:] *= 1000
            mapped_W = wrench(gravity, datum)
            require(
                np.max(abs(mapped_W - original_W)) < 1e-7
                and np.max(abs(original_W - completed["applied_weight_wrench_n_nmm"]))
                < 1e-7,
                "original mapped nodal W does not reproduce current block W",
            )
            actions.extend(gravity)
            physical = wrench(actions, datum)
            dual = (
                sum(
                    np.array(r["saved_rigid_dual_cleat_wrench_n_nmm"])
                    for r in interfaces
                )
                + mapped_W
            )
            difference = physical - dual
            require(
                np.max(abs(dual - completed["compatible_balance_residual_n_nmm"]))
                < 1e-6,
                "saved whole-block residual differs",
            )
            states.append(
                {
                    "case_id": case,
                    "physical_action_count": len(actions),
                    "interfaces": interfaces,
                    "original_mapped_nodal_W_wrench_n_nmm": mapped_W.tolist(),
                    "nodal_W_minus_saved_W_n_nmm": (mapped_W - original_W).tolist(),
                    "physical_applied_whole_cleat_residual_n_nmm": physical.tolist(),
                    "saved_rigid_dual_whole_block_residual_n_nmm": dual.tolist(),
                    "physical_minus_saved_dual_whole_block_n_nmm": difference.tolist(),
                    "geometric_T_discrepancy_sum_n_nmm": sum(
                        np.array(r["geometric_T_explanation_n_nmm"]) for r in interfaces
                    ).tolist(),
                    "within_existing_whole_block_force_tolerance": bool(
                        np.max(abs(physical[:3])) < 0.002
                    ),
                    "within_existing_whole_block_moment_tolerance": bool(
                        np.max(abs(physical[3:])) < 0.6
                    ),
                    "cut_action_inventory": cut_inventory(actions, cut_points, grain),
                    "equilibrated_independent_timber_section_actions_established": False,
                }
            )
            all_actions.extend({"case_id": case, **a} for a in actions)
    summary = {
        "cases": len(states),
        "applied_point_actions": len(all_actions),
        "maximum_whole_physical_force_residual_n": max(
            max(abs(np.array(s["physical_applied_whole_cleat_residual_n_nmm"])[:3]))
            for s in states
        ),
        "maximum_whole_physical_moment_residual_nmm": max(
            max(abs(np.array(s["physical_applied_whole_cleat_residual_n_nmm"])[3:]))
            for s in states
        ),
        "maximum_interface_unexplained_mechanics_residual_n_nmm": max(
            max(abs(np.array(r["physical_minus_full_explanation_n_nmm"])))
            for s in states
            for r in s["interfaces"]
        ),
        "maximum_host_pressure_and_bore_recovery_error_n_nmm": max(
            max(abs(np.array(r["host_physical_minus_saved_n_nmm"])))
            for s in states
            for r in s["interfaces"]
        ),
        "balancing_free_couples_added": 0,
        "original_mapped_load_nodes_per_case": len(nodes),
    }
    result = {
        "schema": "current_right_cleat_physical_action_recovery/v1",
        "cleat": CLEAT,
        "common_datum_xyz_mm": datum.tolist(),
        "summary": summary,
        "states": states,
        "mechanics_identity": "physical_cleat - rigid_dual = -T*n_cross_B(w_L-w_0) + beam_rigid_gradient_residual - elastic_rigid_work_roundoff - (physical_host-saved_host); summed boltwise at the same datum.",
        "cut_applicability": "The frozen annular/bore/face/nodal inventory is recovered. Its significant geometric-T moment defect prevents treating it as independently equilibrated timber-section actions of the existing rigid-dual model. Raw before/on/after candidates retain the disagreement; no torque distribution is invented.",
        "unchanged_assumptions": "Frozen smooth-beam, fixed-cleat, rigid-host, nominal concentric circular annuli, local2 axes, positive T, compression-only contacts and original W mapping. No relative-end translation is added to the saved washer annulus.",
        "complete_joint_acceptance": False,
        "physical_release": False,
        "source_sha256": {
            str(p.relative_to(ROOT)): digest for p, digest in sorted(pins.items())
        },
        "runtime": {"python": sys.version.split()[0], "numpy": np.__version__},
    }
    authenticate(pins)
    output.mkdir(parents=True, exist_ok=False)
    (output / "producer.py.snapshot").write_bytes(Path(__file__).read_bytes())
    dump(output / "checks.json", result)
    with (output / "applied-actions.jsonl").open("w") as stream:
        for a in all_actions:
            stream.write(json.dumps(a, sort_keys=True, allow_nan=False) + "\n")
    authenticate(pins)
    dump(
        output / "receipt.json",
        {
            "source_sha256": result["source_sha256"],
            "output_sha256": {
                name: sha(output / name)
                for name in (
                    "checks.json",
                    "applied-actions.jsonl",
                    "producer.py.snapshot",
                )
            },
        },
    )
    print(
        json.dumps({"checks_sha256": sha(output / "checks.json"), "summary": summary})
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    run(parser.parse_args().output.resolve())
