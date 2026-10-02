"""Move four upper panel screws using the saved elastic member operators.

The owner authorized these station changes on October 2, 2026. Timber gross
stiffness, loads and contact patches stay explicit source idealizations.
No native solver or CAD scene is launched by this calculation.
"""

import argparse
import copy
import fcntl
import json
import sys
from pathlib import Path

import numpy as np
from scipy import sparse

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import corner_frame as method
import top_corner_actions as accounting

ROOT = accounting.ROOT
FRAME = HERE.parent / "corner-frame-attempt01"
INPUTS = accounting.BASE / "reduced-static-attempt01/model-inputs.json"
AXES = {
    f"round_panel_upper_{side}_{row}_4"
    for side in ("left", "right") for row in ("center", "rim")
}
T = np.array([0.0, np.cos(np.deg2rad(50)), np.sin(np.deg2rad(50))])
sha, read, require = accounting.sha, accounting.read, accounting.require


def write(path, value):
    path.write_text(json.dumps(value, indent=2, allow_nan=False) + "\n")


def build(output):
    require(not output.exists(), "preserve the previous projection packet")
    assessment = read(FRAME / "operator-assessment.json")
    paths = {
        "parser": accounting.BASE
        / "current-frame-pure-solid-export-assessment-method-attempt01/assess_matrixstorage.py",
        "helper": accounting.BASE
        / "current-frame-free-body-condensation-preflight-attempt01/condensation.py",
        "quotient": accounting.BASE
        / "current-elastic-quotient-method-preflight-attempt02/quotient_method.py",
    }
    pins = {ROOT / p: h for p, h in assessment["source_sha256"].items()}
    pins.update({FRAME / p: h for p, h in assessment["output_sha256"].items()})
    pins.update({p: sha(p) for p in (INPUTS, FRAME / "operator-assessment.json",
                                   Path(__file__), Path(method.__file__))})
    require(sha(INPUTS) == "178ab4f9352c8b1f11525ffc6680efa5733ba74cedd609874e9a1966624740f9",
            "changed source screw inventory")
    for p, h in pins.items():
        require(sha(p) == h, "changed projection input: " + str(p))
    output.mkdir(parents=True)
    write(output / "inputs.json", {
        "producer_sha256": sha(Path(__file__)),
        "source_sha256": {str(p.relative_to(ROOT)): h for p, h in pins.items()},
        "native_launch": False,
    })
    (output / "producer.py.snapshot").write_bytes(Path(__file__).read_bytes())
    parser = method.module(paths["parser"], "upper_screw_parser")
    helper = method.module(paths["helper"], "upper_screw_condensation")
    quotient = method.module(paths["quotient"], "upper_screw_quotient")
    source = parser.load_frame_source_model(accounting.MODEL)
    model = source["model"]
    frame_model = read(FRAME / "model.json")
    coordinates = {int(n): np.array(v) for n, v in
                   frame_model["physical_node_coordinates_mm"].items()}
    names = frame_model["body_names"]
    labels = parser.parse_dof_file(method.NATIVE / "model.dof")
    row_for = {label: i for i, label in enumerate(labels)}
    owners = np.array([source["owner_by_node"][n] for n, _ in labels])
    parsed = parser.parse_upper_triangle_file(
        method.NATIVE / "model.sti", len(labels),
        owner_by_row=owners, owner_names=names,
    )
    parser.require_no_cross_body_coupling(parsed)
    K = parsed["matrix"]
    old_rows = read(FRAME / "row-identities.json")
    rows = copy.deepcopy(old_rows)
    old_B = sparse.load_npz(FRAME / "B.npz").tocsr()
    B = old_B.tolil(copy=True)
    moved_rows, bodies = [], set()
    for row in rows:
        axis = row["row_id"].split("/")[0]
        if axis not in AXES:
            continue
        own = row["ownership"]
        row["previous_ownership"] = copy.deepcopy(own)
        own["point_mm"] = (np.array(own["point_mm"]) + 65.95 * T).tolist()
        for key in ("first_body", "second_body"):
            if own[key].startswith("base_principal_center_"):
                own[key] = "base_rail_top"
        i = row["row"]
        B[i] = 0
        direction = np.array(own["direction_global_xyz"])
        for key, sign in (("first_body", -1), ("second_body", 1)):
            body = own[key]
            bodies.add(body)
            for dof, value in method.point_terms(
                body, own["point_mm"], sign * direction,
                model, coordinates, row_for,
            ).items():
                B[i, dof] += value
        bodies.update(row["previous_ownership"][k] for k in
                      ("first_body", "second_body"))
        row["previous_source_element"] = row.pop("source_element", None)
        row["station_reprojected_after_owner_authorization"] = True
        moved_rows.append(i)
    require(len(moved_rows) == 12 and len(bodies) == 7,
            "expected four screws / twelve rows / seven incident bodies")
    B = B.tocsr()
    delta_B = B - old_B
    require(set(np.flatnonzero(np.diff(delta_B.indptr))) == set(moved_rows),
            "a projection outside the four screws changed")
    with np.load(FRAME / "operators.npz", allow_pickle=False) as data:
        H, D, e, W, F = [data[k].copy() for k in ("H", "D", "e", "W", "F")]
    reports = []
    for body in sorted(bodies):
        body_id = names.index(body)
        dofs = np.flatnonzero(owners == body_id)
        body_labels = [labels[int(i)] for i in dofs]
        center, R, Q = helper.rigid_basis(body_labels, coordinates)
        old_projection = old_B[:, dofs].tocsr()
        old_map_error = float(np.max(abs(old_projection @ R
                                        - D[:, 6 * body_id:6 * body_id + 6])))
        require(old_map_error < 1e-8, "original rigid projection changed")
        delta = delta_B[moved_rows][:, dofs].tocsr()
        raw = delta.T.toarray()
        elastic = raw - Q @ (Q.T @ raw)
        body_K = K[dofs][:, dofs].tocsr()
        factor, system = helper.factor_bordered(body_K, R)
        solved = quotient.solve_quotient_chunk(factor, system, body_K, R, elastic)
        require(solved["status"] == quotient.PASS_ELASTIC_QUOTIENT_SCREEN,
                body + ": " + solved["status"])
        displacement = solved["displacement_mm"]
        # ponytail: solve only twelve changed RHS columns; reuse every other
        # member contribution. This exact bilinear update is not a rigid shortcut.
        cross = old_projection @ displacement
        H[:, moved_rows] += cross
        H[moved_rows, :] += cross.T
        H[np.ix_(moved_rows, moved_rows)] += delta @ displacement
        e[moved_rows] += displacement.T @ F[dofs]
        D[moved_rows, 6 * body_id:6 * body_id + 6] += delta @ R
        reports.append({
            "body": body, "physical_dofs": len(dofs), "datum_mm": center.tolist(),
            "original_rigid_map_error": old_map_error,
            "KKT_upper_force_residual_relative": solved["KKT_upper_force_residual_relative"],
            "corrections": solved["corrections"],
        })
        print(body, "updated changed screw projections", flush=True)
    scale = float(np.linalg.norm(H, ord=np.inf))
    reciprocity = float(np.linalg.norm(H - H.T, ord=np.inf) / scale)
    minimum = float(np.linalg.eigvalsh((H + H.T) / 2)[0])
    require(reciprocity <= 1e-8 and minimum >= -1e-9 * scale,
            "reprojected compliance consistency failed")
    inputs = read(INPUTS)
    movements = []
    for connection in inputs["connections"]:
        if connection["axis_id"] not in AXES:
            continue
        record = connection["source_record"]
        before = copy.deepcopy(record)
        point = (np.array(connection["source_point_xyz_mm"]) + 65.95 * T).tolist()
        old_receiver = record["receiver_member"]
        receiver = "base_rail_top" if "center_4" in connection["axis_id"] else old_receiver
        connection["source_point_xyz_mm"] = point
        connection["receiver_member_ids"] = [record["panel_member"], receiver]
        record.update(origin_global_xyz_mm=point, receiver_member=receiver,
                      previous_receiver_member=old_receiver,
                      current_location_status="owner_authorized_upper_corner_row_move")
        record["owner_moved_axis_record"] = {
            "date": "2026-10-02", "translation_xyz_mm": (65.95 * T).tolist(),
            "previous_origin_xyz_mm": before["origin_global_xyz_mm"],
            "previous_receiver_member": old_receiver,
        }
        # Existing receiver-screen fields describe only the old station.
        record["previous_receiver_screen"] = record.pop("receiver_screen")
        record["receiver_screen"] = {"new_station_requires_saved_geometry_screen": True}
        movements.append({"axis_id": connection["axis_id"], "before": before,
                          "after": copy.deepcopy(record)})
    require(len(movements) == 4, "screw move census changed")
    frame_model.update(
        development_revision="upper-corner-screw-row-2026-10-02-v1",
        owner_authorized_screw_movements=movements, reviewed_geometry_changed=True,
    )
    inputs["derived_from_model_inputs_sha256"] = sha(INPUTS)
    inputs["owner_authorized_upper_screw_movements"] = movements
    np.savez_compressed(output / "operators.npz", H=H, D=D, e=e, W=W, F=F)
    sparse.save_npz(output / "B.npz", B)
    write(output / "row-identities.json", rows)
    write(output / "model.json", frame_model)
    write(output / "model-inputs.json", inputs)
    for p, h in pins.items():
        require(sha(p) == h, "input changed during projection")
    report = {
        "schema": "owner_authorized_screw_projection/v1",
        "status": "PASS_UPDATED_ELASTIC_FRAME_OPERATORS",
        "producer_sha256": sha(Path(__file__)),
        "source_sha256": {str(p.relative_to(ROOT)): h for p, h in pins.items()},
        "output_sha256": {name: sha(output / name) for name in
                          ("operators.npz", "B.npz", "row-identities.json", "model.json", "model-inputs.json")},
        "bodies_recomputed": reports, "changed_rows": moved_rows,
        "movements": movements, "compliance_checks": {
            "relative_reciprocity": reciprocity,
            "minimum_symmetric_eigenvalue_mm_per_n": minimum,
            "infinity_norm_mm_per_n": scale,
        },
        "modeled_mass_kg": assessment["modeled_mass_kg"],
        "dead_load_factor": assessment["dead_load_factor"],
        "limits": [
            "Saved filled-bore gross stiffness and dead-load bookkeeping are retained; finished new-hole support/conflicts are checked separately.",
            "Only four screw stations and two receiving-member identities change; timber contact patches and all bolt layouts are retained.",
            "All Hillman constitutive laws remain unmeasured source hypotheses.",
        ],
        "native_launch": False, "reviewed_geometry_changed": True,
        "complete_joint_acceptance": False, "physical_release": False,
    }
    write(output / "operator-assessment.json", report)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    lock = ROOT / "docs/wood-joints-mvp/luna-max-native-run-ledger.lock"
    with lock.open("a") as stream:
        fcntl.flock(stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
        require(read(lock.with_suffix(".json"))["slot"]["state"] == "idle",
                "shared analysis slot occupied")
        build(args.output)
