"""Correct four hypothetical right-side added screw stations.

Keep the asymmetric comparison recoverable. Reuse all unchanged member
operators and the existing delta-projection equations; no native launch.
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
from count_mirrored_layout import build_layout

ROOT = accounting.ROOT
SOURCE = HERE / "results/count20-operators-attempt01"
SOURCE12 = HERE.parent / "upper-corner-screw-layout/operators-attempt02"
sha, read, require = accounting.sha, accounting.read, accounting.require


def write(path, value):
    path.write_text(json.dumps(value, indent=2, allow_nan=False) + "\n")


def build(output):
    require(not output.exists(), "preserve the prior corrected projection")
    assessment = read(SOURCE / "operator-assessment.json")
    pins = {ROOT / p: h for p, h in assessment["source_sha256"].items()}
    pins.update({SOURCE / p: h for p, h in assessment["output_sha256"].items()})
    pins.update({p: sha(p) for p in (SOURCE / "operator-assessment.json", Path(__file__), HERE / "count_mirrored_layout.py")})
    for p, h in pins.items():
        require(sha(p) == h, "changed source: " + str(p))
    layout = build_layout(read(SOURCE12 / "model-inputs.json"))
    old_connections = {c["axis_id"]: c for c in read(SOURCE / "model-inputs.json")["connections"]}
    added = layout["added_connections"]
    changes = []
    for connection in added:
        new_id = connection["axis_id"]
        old_id = new_id.replace("_gap_3", "_gap_1") if "_right_" in new_id and connection["hypothetical_edge_role"] in ("edge", "service") and new_id.endswith("_gap_3") else new_id
        original = old_connections[old_id]
        delta = np.array(connection["source_point_xyz_mm"]) - original["source_point_xyz_mm"]
        if np.linalg.norm(delta) > 1e-8:
            require(connection["receiver_member_ids"] == original["receiver_member_ids"], "receiver identity changed")
            changes.append({"previous_axis_id": old_id, "axis_id": new_id, "translation_xyz_mm": delta.tolist(), "template_axis_id": connection["template_axis_id"], "source_point_xyz_mm": connection["source_point_xyz_mm"]})
    require(len(changes) == 4, "expected four right horizontal corrections")
    output.mkdir(parents=True)
    write(output / "inputs.json", {"source_sha256": {str(p.relative_to(ROOT)): h for p, h in pins.items()}, "changes": changes, "native_launch": False})
    (output / "producer.py.snapshot").write_bytes(Path(__file__).read_bytes())
    paths = {
        "parser": accounting.BASE / "current-frame-pure-solid-export-assessment-method-attempt01/assess_matrixstorage.py",
        "helper": accounting.BASE / "current-frame-free-body-condensation-preflight-attempt01/condensation.py",
        "quotient": accounting.BASE / "current-elastic-quotient-method-preflight-attempt02/quotient_method.py",
    }
    parser = method.module(paths["parser"], "mirror_parser")
    helper = method.module(paths["helper"], "mirror_condensation")
    quotient = method.module(paths["quotient"], "mirror_quotient")
    source = parser.load_frame_source_model(accounting.MODEL)
    model = source["model"]
    frame_model = read(SOURCE / "model.json")
    coordinates = {int(n): np.array(v) for n, v in frame_model["physical_node_coordinates_mm"].items()}
    names = frame_model["body_names"]
    labels = parser.parse_dof_file(method.NATIVE / "model.dof")
    row_for = {label: i for i, label in enumerate(labels)}
    owners = np.array([source["owner_by_node"][n] for n, _ in labels])
    parsed = parser.parse_upper_triangle_file(method.NATIVE / "model.sti", len(labels), owner_by_row=owners, owner_names=names)
    parser.require_no_cross_body_coupling(parsed)
    K = parsed["matrix"]
    rows = copy.deepcopy(read(SOURCE / "row-identities.json"))
    old_B = sparse.load_npz(SOURCE / "B.npz").tocsr()
    B = old_B.tolil(copy=True)
    by_axis = {c["previous_axis_id"]: c for c in changes}
    moved, bodies = [], set()
    for row in rows:
        axis = row["row_id"].split("/")[0]
        if axis not in by_axis:
            continue
        change = by_axis[axis]
        row["previous_ownership"] = copy.deepcopy(row["ownership"])
        own = row["ownership"]
        own["point_mm"] = (np.array(own["point_mm"]) + change["translation_xyz_mm"]).tolist()
        row["previous_row_id"] = row["row_id"]
        row["row_id"] = row["row_id"].replace(axis, change["axis_id"], 1)
        row["hypothetical_horizontal_placement_corrected"] = True
        row["corrected_template_axis_id"] = change["template_axis_id"]
        index = row["row"]
        B[index] = 0
        for key, sign in (("first_body", -1), ("second_body", 1)):
            body = own[key]
            bodies.add(body)
            for dof, value in method.point_terms(body, own["point_mm"], sign * np.array(own["direction_global_xyz"]), model, coordinates, row_for).items():
                B[index, dof] += value
        moved.append(index)
    require(len(moved) == 12 and len(bodies) == 6, "expected 12 changed scalars on six bodies")
    B = B.tocsr()
    delta_B = B - old_B
    require(set(np.flatnonzero(np.diff(delta_B.indptr))) == set(moved), "unrelated station map changed")
    with np.load(SOURCE / "operators.npz", allow_pickle=False) as data:
        H, D, e, W, F = [data[k].copy() for k in ("H", "D", "e", "W", "F")]
    reports = []
    for body in sorted(bodies):
        body_id = names.index(body)
        dofs = np.flatnonzero(owners == body_id)
        center, R, Q = helper.rigid_basis([labels[int(i)] for i in dofs], coordinates)
        old_projection = old_B[:, dofs].tocsr()
        require(np.max(abs(old_projection @ R - D[:, 6 * body_id:6 * body_id + 6])) < 1e-8, "source rigid map mismatch")
        delta = delta_B[moved][:, dofs].tocsr()
        raw = delta.T.toarray()
        body_K = K[dofs][:, dofs].tocsr()
        factor, system = helper.factor_bordered(body_K, R)
        solved = quotient.solve_quotient_chunk(factor, system, body_K, R, raw - Q @ (Q.T @ raw))
        require(solved["status"] == quotient.PASS_ELASTIC_QUOTIENT_SCREEN, body + ": " + solved["status"])
        displacement = solved["displacement_mm"]
        cross = old_projection @ displacement
        H[:, moved] += cross
        H[moved, :] += cross.T
        H[np.ix_(moved, moved)] += delta @ displacement
        e[moved] += displacement.T @ F[dofs]
        D[moved, 6 * body_id:6 * body_id + 6] += delta @ R
        reports.append({"body": body, "datum_mm": center.tolist(), "KKT_upper_force_residual_relative": solved["KKT_upper_force_residual_relative"]})
        print(body, "corrected right-side added screw maps", flush=True)
    scale = float(np.linalg.norm(H, ord=np.inf))
    reciprocity = float(np.linalg.norm(H - H.T, ord=np.inf) / scale)
    minimum = float(np.linalg.eigvalsh((H + H.T) / 2)[0])
    require(reciprocity <= 1e-8 and minimum >= -1e-9 * scale, "invalid updated compliance")
    with np.load(SOURCE12 / "operators.npz", allow_pickle=False) as source12:
        require(np.array_equal(H[:1888, :1888], source12["H"]) and np.array_equal(D[:1888], source12["D"]) and np.array_equal(e[:1888], source12["e"]), "original twelve-screw operator block changed")
    frame_model.update(hypothetical_placement_rule="outer_and_middle_horizontal_gaps_on_both_sides", hypothetical_station_corrections=changes)
    np.savez_compressed(output / "operators.npz", H=H, D=D, e=e, W=W, F=F)
    sparse.save_npz(output / "B.npz", B)
    write(output / "row-identities.json", rows)
    write(output / "model-inputs.json", layout["model_inputs"])
    write(output / "model.json", frame_model)
    write(output / "layout.json", {k: v for k, v in layout.items() if k != "model_inputs"})
    (output / "panel-benchmark.npz").symlink_to(SOURCE / "panel-benchmark.npz")
    for p, h in pins.items():
        require(sha(p) == h, "source changed during correction: " + str(p))
    assessment.update(schema="corrected_hypothetical_panel_placement/v1", status="PASS_CORRECTED_ELASTIC_FRAME_OPERATORS", source_sha256={str(p.relative_to(ROOT)): h for p, h in pins.items()},
        output_sha256={name: sha(output / name) for name in ("operators.npz", "B.npz", "row-identities.json", "model.json", "model-inputs.json", "panel-benchmark.npz", "layout.json")},
        bodies_recomputed=reports, station_corrections=changes,
        compliance_checks={"relative_reciprocity": reciprocity, "minimum_symmetric_eigenvalue_mm_per_n": minimum, "infinity_norm_mm_per_n": scale, "original_twelve_screw_operator_block_unchanged": True})
    write(output / "operator-assessment.json", assessment)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    with (ROOT / "docs/wood-joints-mvp/luna-max-native-run-ledger.lock").open("a") as stream:
        fcntl.flock(stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
        require(read(ROOT / "docs/wood-joints-mvp/luna-max-native-run-ledger.json")["slot"]["state"] == "idle", "shared mechanics slot occupied")
        build(args.output.resolve())
