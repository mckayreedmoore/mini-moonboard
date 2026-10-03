"""Append hypothetical panel screws to saved elastic frame operators.

Reuse the frozen native stiffness export and quotient method. This changes
connector stations/count only; no CAD rebuild or native solver is launched.
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
from count_layout import build_layout

ROOT = accounting.ROOT
SOURCE = HERE.parent / "upper-corner-screw-layout/operators-attempt02"
sha, read, require = accounting.sha, accounting.read, accounting.require


def write(path, value):
    path.write_text(json.dumps(value, indent=2, allow_nan=False) + "\n")


def build(output):
    require(not output.exists(), "preserve the previous projection")
    assessment = read(SOURCE / "operator-assessment.json")
    paths = {
        "parser": accounting.BASE / "current-frame-pure-solid-export-assessment-method-attempt01/assess_matrixstorage.py",
        "helper": accounting.BASE / "current-frame-free-body-condensation-preflight-attempt01/condensation.py",
        "quotient": accounting.BASE / "current-elastic-quotient-method-preflight-attempt02/quotient_method.py",
    }
    pins = {ROOT / p: h for p, h in assessment["source_sha256"].items()}
    pins.update({SOURCE / p: h for p, h in assessment["output_sha256"].items()})
    pins.update({p: sha(p) for p in (
        SOURCE / "operator-assessment.json", Path(__file__),
        HERE / "count_layout.py", HERE / "count_frame.py", Path(method.__file__),
    )})
    for p, h in pins.items():
        require(sha(p) == h, "changed source: " + str(p))
    layout = build_layout(read(SOURCE / "model-inputs.json"))
    old_rows = read(SOURCE / "row-identities.json")
    rows = copy.deepcopy(old_rows)
    connections = {c["axis_id"]: c for c in read(SOURCE / "model-inputs.json")["connections"]}
    new_rows, bodies = [], set()
    for connection in layout["added_connections"]:
        template = connections[connection["template_axis_id"]]
        delta = np.array(connection["source_point_xyz_mm"]) - template["source_point_xyz_mm"]
        template_rows = [r for r in old_rows if r["row_id"].split("/")[0] == template["axis_id"]]
        require(len(template_rows) == 3, "expected three screw scalar rows")
        for original in template_rows:
            row = copy.deepcopy(original)
            row["row"] = len(rows)
            row["row_id"] = row["row_id"].replace(template["axis_id"], connection["axis_id"], 1)
            row["ownership"]["point_mm"] = (np.array(row["ownership"]["point_mm"]) + delta).tolist()
            for key in ("source_element", "source_group", "source_inventory_row_index", "previous_source_element", "previous_ownership", "station_reprojected_after_owner_authorization"):
                row.pop(key, None)
            row["hypothetical_added_panel_screw"] = True
            row["template_row"] = original["row"]
            bodies.update(row["ownership"][k] for k in ("first_body", "second_body"))
            rows.append(row)
            new_rows.append(row)
    require(len(new_rows) == 96, "expected 32 additional screws")
    output.mkdir(parents=True)
    write(output / "layout.json", {k: v for k, v in layout.items() if k != "model_inputs"})
    write(output / "inputs.json", {"source_sha256": {str(p.relative_to(ROOT)): h for p, h in pins.items()}, "native_launch": False})
    (output / "producer.py.snapshot").write_bytes(Path(__file__).read_bytes())
    parser = method.module(paths["parser"], "count_parser")
    helper = method.module(paths["helper"], "count_condensation")
    quotient = method.module(paths["quotient"], "count_quotient")
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
    old_B = sparse.load_npz(SOURCE / "B.npz").tocsr()
    added_B = sparse.lil_matrix((96, len(labels)))
    for i, row in enumerate(new_rows):
        own = row["ownership"]
        for key, sign in (("first_body", -1), ("second_body", 1)):
            for dof, value in method.point_terms(own[key], own["point_mm"], sign * np.array(own["direction_global_xyz"]), model, coordinates, row_for).items():
                added_B[i, dof] += value
    added_B = added_B.tocsr()
    B = sparse.vstack((old_B, added_B), format="csr")
    with np.load(SOURCE / "operators.npz", allow_pickle=False) as data:
        H0, D0, e0, W, F = [data[k].copy() for k in ("H", "D", "e", "W", "F")]
    old_count, count = len(old_rows), len(rows)
    H, D, e = np.zeros((count, count)), np.zeros((count, 300)), np.zeros((count, 12))
    H[:old_count, :old_count], D[:old_count], e[:old_count] = H0, D0, e0
    reports = []
    benchmark_panel = "main_upper_left"
    n = np.array([0.0, np.sin(np.deg2rad(50)), -np.cos(np.deg2rad(50))])
    benchmark_indices = np.array([
        r["row"] for r in rows
        if benchmark_panel in (r["ownership"]["first_body"], r["ownership"]["second_body"])
        and r["ownership"]["role"] in ("non_qualifying_parametric_screw_withdrawal", "timber_or_panel_contact")
        and abs(np.dot(r["ownership"]["direction_global_xyz"], n)) > 1 - 1e-8
        and not any(b.startswith(("main_", "kicker_")) and b != benchmark_panel for b in (r["ownership"]["first_body"], r["ownership"]["second_body"]))
    ], dtype=int)
    for body in sorted(bodies):
        body_id = names.index(body)
        dofs = np.flatnonzero(owners == body_id)
        center, R, Q = helper.rigid_basis([labels[int(i)] for i in dofs], coordinates)
        old_projection = old_B[:, dofs].tocsr()
        require(np.max(abs(old_projection @ R - D0[:, 6 * body_id:6 * body_id + 6])) < 1e-8, "source rigid map changed")
        new_projection = added_B[:, dofs].tocsr()
        active = np.flatnonzero(np.diff(new_projection.indptr))
        # Solve only appended rows incident on this member, retaining old H.
        projection = new_projection[active]
        raw = projection.T.toarray()
        elastic = raw - Q @ (Q.T @ raw)
        body_K = K[dofs][:, dofs].tocsr()
        factor, system = helper.factor_bordered(body_K, R)
        solved = quotient.solve_quotient_chunk(factor, system, body_K, R, elastic)
        require(solved["status"] == quotient.PASS_ELASTIC_QUOTIENT_SCREEN, body + ": " + solved["status"])
        displacement = solved["displacement_mm"]
        appended = old_count + active
        cross = old_projection @ displacement
        H[:old_count, appended] += cross
        H[appended, :old_count] += cross.T
        H[np.ix_(appended, appended)] += projection @ displacement
        e[appended] += displacement.T @ F[dofs]
        D[appended, 6 * body_id:6 * body_id + 6] += projection @ R
        if body == benchmark_panel:
            bp = B[benchmark_indices][:, dofs].tocsr()
            rhs = bp.T.toarray()
            bs = quotient.solve_quotient_chunk(factor, system, body_K, R, rhs - Q @ (Q.T @ rhs))
            require(bs["status"] == quotient.PASS_ELASTIC_QUOTIENT_SCREEN, "panel benchmark projection failed")
            u = bs["displacement_mm"]
            np.savez_compressed(output / "panel-benchmark.npz", indices=benchmark_indices, H=bp @ u, D=bp @ R, e=u.T @ F[dofs], W=W[6 * body_id:6 * body_id + 6])
        reports.append({"body": body, "new_scalar_rhs_count": len(active), "physical_dofs": len(dofs), "datum_mm": center.tolist(), "KKT_upper_force_residual_relative": solved["KKT_upper_force_residual_relative"]})
        print(body, "projected", len(active), "additional scalar rows", flush=True)
    scale = float(np.linalg.norm(H, ord=np.inf))
    reciprocity = float(np.linalg.norm(H - H.T, ord=np.inf) / scale)
    minimum = float(np.linalg.eigvalsh((H + H.T) / 2)[0])
    require(reciprocity <= 1e-8 and minimum >= -1e-9 * scale, "invalid appended compliance")
    require(np.array_equal(H[:old_count, :old_count], H0) and np.array_equal(D[:old_count], D0) and np.array_equal(e[:old_count], e0), "source operator block changed")
    frame_model.update(hypothetical_panel_screw_count=98, proposed_main_panel_screw_count=20, reviewed_geometry_changed=True, added_hardware_mass_included=False)
    np.savez_compressed(output / "operators.npz", H=H, D=D, e=e, W=W, F=F)
    sparse.save_npz(output / "B.npz", B)
    write(output / "row-identities.json", rows)
    write(output / "model.json", frame_model)
    write(output / "model-inputs.json", layout["model_inputs"])
    for p, h in pins.items():
        require(sha(p) == h, "input changed during projection: " + str(p))
    write(output / "operator-assessment.json", {
        "schema": "hypothetical_panel_count_projection/v1", "status": "PASS_APPENDED_ELASTIC_FRAME_OPERATORS",
        "source_sha256": {str(p.relative_to(ROOT)): h for p, h in pins.items()},
        "output_sha256": {name: sha(output / name) for name in ("operators.npz", "B.npz", "row-identities.json", "model.json", "model-inputs.json", "panel-benchmark.npz", "layout.json")},
        "bodies_recomputed": reports, "old_scalar_row_count": old_count, "appended_scalar_row_count": 96,
        "compliance_checks": {"relative_reciprocity": reciprocity, "minimum_symmetric_eigenvalue_mm_per_n": minimum, "infinity_norm_mm_per_n": scale, "old_operator_block_unchanged": True},
        "modeled_mass_kg": assessment["modeled_mass_kg"], "dead_load_factor": assessment["dead_load_factor"],
        "limits": ["Hypothetical 32 additional screws, outside purchased 66-axis inventory; no live CAD revision.", "Point projections fit gross filled-bore member meshes; finished holes, conflicts and installation are unverified.", "Added screw mass omitted; member stiffness, all contact patches, loads, bolt geometry and unmeasured screw laws retained.", "Panel benchmark fixes receiving members and retains only panel-normal interactions, so it is not a complete frame acceptance model."],
        "native_launch": False, "reviewed_geometry_changed": True, "complete_joint_acceptance": False, "physical_release": False,
    })


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    with (ROOT / "docs/wood-joints-mvp/luna-max-native-run-ledger.lock").open("a") as stream:
        fcntl.flock(stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
        require(read(ROOT / "docs/wood-joints-mvp/luna-max-native-run-ledger.json")["slot"]["state"] == "idle", "shared mechanics slot occupied")
        build(args.output.resolve())
