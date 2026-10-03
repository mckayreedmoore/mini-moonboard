"""Recover two saved bodies' displacement and sample patch59 contact closure.

Saved forces and representative rigid poses are prescribed inputs. This runs
elastic displacement recovery only, never a new contact/force allocation.
The parent owns the serialized recovery run.
"""

from __future__ import annotations

import argparse
import fcntl
import json
import sys
from itertools import pairwise
from pathlib import Path

import numpy as np
from scipy import sparse

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

import corner_frame as method
import top_corner_actions as accounting

ROOT, BASE, NATIVE = accounting.ROOT, accounting.BASE, method.NATIVE
SOURCE = accounting.MODEL
CONTACTS = accounting.CONTACTS
BODIES = ("main_lower_left", "base_rail_bottom_left")
FRAMES = {
    12: ("panel-width-frame-250-attempt05-conic",
         "5a49b2076e0e32e5fbae90b1da41be6b77973da9057aee860acebaee9cef05f0",
         "ff54c8f662bce93e03b46e47b088408c82471c5956b824e3320afb32b79919ef",
         "47e3405e15e3d97f8666ffdead694f1a83fe6f3f76608fc81882112075e98fe0"),
    20: ("count20-width-grain-frame-attempt01",
         "0a8bcf1ac6679d970d72e11e652d31e3406607699230bcf9915bb009e34e9b88",
         "8271a9e6c3ff15440703f78b704e6f601a545b538611c09009afdeb77393eb7c",
         "d94732bb20ede8da48a7799c014b2c9d66e16062b7c4f485ec008e494c5488a1"),
}
sha, read, require = accounting.sha, accounting.read, accounting.require


def write(path, value):
    path.write_text(json.dumps(value, indent=2, allow_nan=False) + "\n")


def pin(path, pins, expected=None):
    digest = sha(path)
    require(expected is None or digest == expected, "Changed source: " + str(path))
    require(path not in pins or pins[path] == digest, "Inconsistent source identity")
    pins[path] = digest


def packet(count, pins):
    name, comparison_hash, response_hash, assessment_hash = FRAMES[count]
    folder = HERE / name
    pin(folder / "comparison.json", pins, comparison_hash)
    pin(folder / "response.npz", pins, response_hash)
    comparison = read(folder / "comparison.json")
    op = ROOT / comparison["frame_operator_directory"]
    pin(op / "operator-assessment.json", pins, assessment_hash)
    assessment = read(op / "operator-assessment.json")
    for filename in ("operators.npz", "B.npz", "row-identities.json", "model.json", "model-inputs.json"):
        pin(op / filename, pins, assessment["output_sha256"][filename])
    for relative, digest in assessment["source_sha256"].items():
        pin(ROOT / relative, pins, digest)
    rows, model, inputs = [read(op / filename) for filename in
                           ("row-identities.json", "model.json", "model-inputs.json")]
    case_index = next(i for i, case in enumerate(inputs["cases"]) if case["case_id"] == "a1-rear")
    with np.load(folder / "response.npz", allow_pickle=False) as data:
        force = data["a1-rear_gap_raw_force_n"].copy()
        pose = data["a1-rear_gap_rigid_coordinates"].copy()
    with np.load(op / "operators.npz", allow_pickle=False) as data:
        H, D = data["H"], data["D"]
        elastic_load = comparison["dead_load_factor"] * data["e"][:, 2 * case_index] + data["e"][:, 2 * case_index + 1]
        nodal = comparison["dead_load_factor"] * data["F"][:, 2 * case_index] + data["F"][:, 2 * case_index + 1]
        saved_q = D @ pose + elastic_load - H @ force
    return {"count": count, "model": model, "rows": rows, "pose": pose,
            "force": force, "nodal": nodal, "saved_q": saved_q,
            "B": sparse.load_npz(op / "B.npz").tocsr()}


def width_panel_K(physical, model, labels, coordinates, dofs, original, orientation):
    """Reassemble native strong-T and changed strong-X K using the pinned kernel."""
    axes = model["material_binding"]["panel_axes"][BODIES[0]]["previous_assumed_apa_directions"]
    constants = orientation.deck_materials(NATIVE / "model.inp")
    local_row = {labels[int(dof)]: i for i, dof in enumerate(dofs)}
    ii, jj, old_values, new_values = [], [], [], []
    cache = {}
    for element in physical["physical_body_elements"][BODIES[0]]:
        kind, nodes, group = physical["elements"][str(element)]
        require(kind == "C3D20", "Unexpected panel element")
        values = constants["PANEL_LAYER_" + group.rsplit("_", 1)[1]]
        positions = np.array([coordinates[n] for n in nodes])
        relative = positions - positions[0]
        key = (tuple(np.round(relative, 6).ravel()), tuple(values))
        if key not in cache:
            old, _ = method.brick_stiffness(positions, values, axes)
            new, _ = method.brick_stiffness(positions, [values[1], values[0], *values[2:]], axes)
            cache[key] = relative, old, new
        reference, old, new = cache[key]
        require(np.max(abs(relative - reference)) < 1e-8, "Noncongruent cached panel element")
        local = np.array([local_row[(n, d)] for n in nodes for d in (1, 2, 3)])
        ii.extend(np.repeat(local, 60))
        jj.extend(np.tile(local, 60))
        old_values.extend(old.ravel())
        new_values.extend(new.ravel())
    assembled = sparse.coo_matrix((old_values, (ii, jj)), shape=original.shape).tocsr()
    changed = sparse.coo_matrix((new_values, (ii, jj)), shape=original.shape).tocsr()
    difference = assembled - original
    mismatch = float(np.max(abs(difference.data), initial=0) / np.max(abs(original.data)))
    require(mismatch <= 1e-6, "Panel reassembly differs from frozen native K")
    return changed, mismatch


def points_for_patch(cells, patch):
    """Original centroids plus longitudinal/transverse half-spacing samples."""
    normal = np.array(patch["normal_on_first_xyz"])
    tangent = np.cross(normal, [1.0, 0.0, 0.0])
    center = np.array(patch["centroid_xyz_mm"])
    bands = [sorted([r for r in cells if (np.dot(np.array(r["point_xyz_mm"]) - center, tangent) > 0) == side],
                    key=lambda r: r["point_xyz_mm"][0]) for side in (False, True)]
    require(len(bands[0]) == len(bands[1]) == 11, "Expected eleven stations in each transverse band")
    result = [{"kind": "original", "source_cell": r["name"], "point_mm": r["point_xyz_mm"]} for r in cells]
    for band in bands:
        for left, right in pairwise(band):
            result.append({"kind": "half_X", "source_cell": None,
                           "point_mm": ((np.array(left["point_xyz_mm"]) + right["point_xyz_mm"]) / 2).tolist()})
    for low, high in zip(*bands, strict=True):
        require(abs(low["point_xyz_mm"][0] - high["point_xyz_mm"][0]) < 1e-6, "Transverse stations differ")
        result.append({"kind": "half_T", "source_cell": None,
                       "point_mm": ((np.array(low["point_xyz_mm"]) + high["point_xyz_mm"]) / 2).tolist()})
    for i in range(10):
        corners = [r["point_xyz_mm"] for band in bands for r in band[i:i + 2]]
        result.append({"kind": "half_X_T", "source_cell": None, "point_mm": np.mean(corners, axis=0).tolist()})
    circles = [edge["circle"] for edge in patch["boundary_edges"] if "circle" in edge]
    kept, excluded = [], []
    for row in result:
        point = np.array(row["point_mm"])
        require(abs(normal @ (point - center)) < 1e-6, "Sample left source contact plane")
        in_hole = any(np.linalg.norm(point - circle["center_xyz_mm"]) < circle["radius_mm"] for circle in circles)
        (excluded if in_hole else kept).append(row)
    require(sum(row["kind"] == "original" for row in kept) == 22, "Original cell excluded")
    return kept, excluded


def build(output):
    require(not output.exists(), "Use a fresh output child")
    pins = {}
    helper_paths = {
        "parser": BASE / "current-frame-pure-solid-export-assessment-method-attempt01/assess_matrixstorage.py",
        "condensation": BASE / "current-frame-free-body-condensation-preflight-attempt01/condensation.py",
        "quotient": BASE / "current-elastic-quotient-method-preflight-attempt02/quotient_method.py",
        "orientation": HERE / "panel_orientation.py",
    }
    pin(SOURCE, pins, "61f95ec9e670b2bd0e95d426cc14ff381283edfc4f9c87e47c2b344dd4fe50b8")
    pin(CONTACTS, pins, "034067430fff5207cdb40819fa8118a367edeb29a8d83926928cc96a0e87d151")
    pin(helper_paths["orientation"], pins, "3268faa94ba050d82d66df1393fc4b8e4d9e4a79b87412fe0f4cfdbf72dd7e93")
    pin(NATIVE / "model.inp", pins, "71dc0b73450b597aba35c0458befff5ca3b85dd87f3cfbed9992f4755b5124d5")
    pin(NATIVE / "model.sti", pins, "7d22d2b013fcdc9fddfeab589b456615f0671db989a034e091bac855f3a93c01")
    pin(NATIVE / "model.dof", pins, "532f732e5b2ed88d96c544b73bcc33168a65942ff6c5155f30c6d4ade9173f1d")
    packets = [packet(count, pins) for count in FRAMES]
    for path in [Path(__file__), Path(method.__file__), *helper_paths.values(),
                 NATIVE / "model.inp", NATIVE / "model.dof", NATIVE / "model.sti",
                 ROOT / "fea/wood_joint_reduced_members.py", ROOT / "fea/floor_recess_mesh.py",
                 ROOT / "fea/wood_joint_patch_materials.py"]:
        pin(path, pins)
    output.mkdir(parents=True)
    write(output / "inputs.json", {"source_sha256": {str(p.relative_to(ROOT)): h for p, h in pins.items()}})
    (output / "producer.py.snapshot").write_bytes(Path(__file__).read_bytes())
    modules = {name: method.module(path, "gap_recovery_" + name) for name, path in helper_paths.items()}
    parser, helper, quotient = [modules[name] for name in ("parser", "condensation", "quotient")]
    source = parser.load_frame_source_model(SOURCE)
    physical = source["model"]
    model = packets[0]["model"]
    require(list(physical["physical_body_nodes"]) == model["body_names"], "Native and operator body ordering differs")
    require(model["physical_node_coordinates_mm"] == packets[1]["model"]["physical_node_coordinates_mm"]
            and model["body_names"] == packets[1]["model"]["body_names"], "Physical coordinate/owner mismatch")
    coordinates = {int(n): np.array(value) for n, value in model["physical_node_coordinates_mm"].items()}
    labels = parser.parse_dof_file(NATIVE / "model.dof")
    owners = np.array([source["owner_by_node"][node] for node, _ in labels])
    parsed = parser.parse_upper_triangle_file(NATIVE / "model.sti", len(labels), owner_by_row=owners,
                                            owner_names=model["body_names"])
    parser.require_no_cross_body_coupling(parsed)
    recoveries, displacement_arrays = [], {}
    for body in BODIES:
        body_id = model["body_names"].index(body)
        dofs = np.flatnonzero(owners == body_id)
        body_labels = [labels[int(i)] for i in dofs]
        row_for = {label: i for i, label in enumerate(body_labels)}
        node_ids = sorted({node for node, _ in body_labels})
        xyz_rows = np.array([[row_for[(node, direction)] for direction in (1, 2, 3)] for node in node_ids])
        center, R, Q = helper.rigid_basis(body_labels, coordinates)
        body_K = parsed["matrix"][dofs][:, dofs].tocsr()
        mismatch = None
        if body == BODIES[0]:
            body_K, mismatch = width_panel_K(physical, model, labels, coordinates, dofs, body_K, modules["orientation"])
        factor, system = helper.factor_bordered(body_K, R)
        for p in packets:
            projection = p["B"][:, dofs].tocsr()
            raw = p["nodal"][dofs] - projection.T @ p["force"]
            imbalance = R.T @ raw
            require(max(abs(imbalance[:3])) <= 0.1 and 1000 * max(abs(imbalance[3:])) <= 2,
                    "Saved body forces unbalanced before elastic projection")
            elastic_rhs = raw - Q @ (Q.T @ raw)
            solved = quotient.solve_quotient_chunk(factor, system, body_K, R, elastic_rhs[:, None])
            require(solved["status"] == quotient.PASS_ELASTIC_QUOTIENT_SCREEN, body + ": " + solved["status"])
            displacement = solved["displacement_mm"][:, 0] + R @ p["pose"][6 * body_id:6 * body_id + 6]
            p.setdefault("body_displacement", {})[body] = (displacement, row_for)
            displacement_arrays[f"count{p['count']}_{body}_displacement_xyz_mm"] = displacement[xyz_rows]
            displacement_arrays[f"count{p['count']}_{body}_node_ids"] = np.array(node_ids)
            recoveries.append({"screws_per_main_panel": p["count"], "body": body, "datum_mm": center.tolist(),
                               "changed_main_panel_K_used": body == BODIES[0], "source_native_K_relative_difference": mismatch,
                               "raw_body_wrench_residual_scaled_n": imbalance.tolist(),
                               "KKT_upper_force_residual_relative": solved["KKT_upper_force_residual_relative"]})
            print("recovered", p["count"], body, flush=True)
    patch = read(CONTACTS)["contact_patches"][59]
    cells = [r for r in physical["contact_cell_ownership"] if r.get("source_patch_index") == 59]
    points, excluded = points_for_patch(cells, patch)
    inward = -np.array(patch["normal_on_first_xyz"])
    samples = []
    for p in packets:
        by_id = {row["row_id"]: row["row"] for row in p["rows"]}
        case_samples = []
        for row in points:
            values = {}
            for body in BODIES:
                u, row_for = p["body_displacement"][body]
                terms = method.point_terms(body, row["point_mm"], inward, physical, coordinates, row_for)
                values[body] = sum(weight * u[index] for index, weight in terms.items())
            closure = float(values[BODIES[0]] - values[BODIES[1]])
            original_q = None if row["source_cell"] is None else float(p["saved_q"][by_id[row["source_cell"]]])
            case_samples.append({**row, "closure_positive_penetration_mm": closure,
                                 "separation_positive_opening_mm": -closure, "saved_original_q_mm": original_q,
                                 "original_q_difference_mm": None if original_q is None else closure - original_q})
        error = max(abs(row["original_q_difference_mm"]) for row in case_samples if row["source_cell"] is not None)
        require(error <= 1e-6, "Recovered original contact q differs from saved q")
        unsampled = [row for row in case_samples if row["kind"] != "original"]
        samples.append({"screws_per_main_panel": p["count"], "original_q_max_difference_mm": error,
                        "largest_sampled_closure_mm": max(row["closure_positive_penetration_mm"] for row in case_samples),
                        "largest_original_cell_closure_mm": max(row["closure_positive_penetration_mm"] for row in case_samples if row["kind"] == "original"),
                        "half_spacing_positive_closure_count": sum(row["closure_positive_penetration_mm"] > 1e-6 for row in unsampled),
                        "largest_half_spacing_closure": max(unsampled, key=lambda row: row["closure_positive_penetration_mm"]),
                        "samples": case_samples})
    for path, digest in pins.items():
        require(sha(path) == digest, "Input changed during recovery")
    np.savez_compressed(output / "displacement.npz", **displacement_arrays)
    write(output / "result.json", {"schema": "saved_patch59_contact_gap_recovery/v1",
          "status": "RECOVERED_ORIGINAL_Q_AND_SAMPLED_HALF_SPACING", "recoveries": recoveries,
          "states": samples, "excluded_source_hole_samples": excluded,
          "source_sha256": {str(p.relative_to(ROOT)): h for p, h in pins.items()},
          "displacement_sha256": sha(output / "displacement.npz"),
          "limits": ["Prescribed saved forces and representative rigid pose; no new contact allocation.",
                     "Positive closure includes existing numerical penalty compression; it is not physical indentation qualification.",
                     "Half-spacing samples cannot bound continuous maximum gap or penetration.",
                     "Main panel uses changed width-grain K; bottom-rail timber K is unchanged native K.",
                     "Filled-bore mesh and source contact-face holes retain their recorded abstraction.",
                     "Representative saved rigid coordinates only; bounded seating and pose nonuniqueness prevent a gap envelope.",
                     "Material/contact/screw-law assumptions remain unresolved."],
          "native_launch": False, "frame_solve_executed": False, "physical_release": False})
    print("result_sha256", sha(output / "result.json"), flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    lock = ROOT / "docs/wood-joints-mvp/luna-max-native-run-ledger.lock"
    with lock.open("a") as stream:
        fcntl.flock(stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
        require(read(lock.with_suffix(".json"))["slot"]["state"] == "idle", "Shared mechanics slot occupied")
        build(args.output.resolve())
