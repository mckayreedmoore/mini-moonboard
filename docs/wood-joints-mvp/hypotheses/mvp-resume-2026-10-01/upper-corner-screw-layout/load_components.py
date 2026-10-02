"""Separate vertical and horizontal hold-load effects without changing loads.

Reproduce the saved eight-node uniform square patch and its nodal couple.
This supplies explicit live-load components for the 140/250 lb comparison.
"""

import argparse
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
sys.path.insert(0, str(ROOT))
from fea.horizontal_panel_frame import traction_wrench

sha, read, require = accounting.sha, accounting.read, accounting.require


def build(frame_directory, output):
    frame_directory, output = frame_directory.resolve(), output.resolve()
    require(not output.exists(), "preserve the existing load decomposition")
    metadata = read(frame_directory / "model.json")
    inputs_path = accounting.BASE / "reduced-static-attempt01/model-inputs.json"
    inputs = read(inputs_path)
    assessment = read(frame_directory / "operator-assessment.json")
    pins = {ROOT / p: h for p, h in assessment["source_sha256"].items()}
    pins.update({frame_directory / p: h for p, h in assessment["output_sha256"].items()})
    pins.update({p: sha(p) for p in (Path(__file__), Path(method.__file__),
                                   accounting.LOADS, ROOT / "fea/horizontal_panel_frame.py")})
    for p, h in pins.items():
        require(sha(p) == h, "changed component input: " + str(p))
    base = accounting.BASE
    parser = method.module(base / "current-frame-pure-solid-export-assessment-method-attempt01/assess_matrixstorage.py", "hold_component_parser")
    helper = method.module(base / "current-frame-free-body-condensation-preflight-attempt01/condensation.py", "hold_component_helper")
    quotient = method.module(base / "current-elastic-quotient-method-preflight-attempt02/quotient_method.py", "hold_component_quotient")
    source = parser.load_frame_source_model(accounting.MODEL)
    labels = parser.parse_dof_file(method.NATIVE / "model.dof")
    row_for = {label: i for i, label in enumerate(labels)}
    owners = np.array([source["owner_by_node"][n] for n, _ in labels])
    parsed = parser.parse_upper_triangle_file(method.NATIVE / "model.sti", len(labels),
                                            owner_by_row=owners, owner_names=metadata["body_names"])
    parser.require_no_cross_body_coupling(parsed)
    K = parsed["matrix"]
    B = sparse.load_npz(frame_directory / "B.npz").tocsr()
    xyz = {int(n): np.array(p) for n, p in metadata["physical_node_coordinates_mm"].items()}
    with np.load(frame_directory / "operators.npz", allow_pickle=False) as operators:
        source_e, source_W, source_F = [operators[k].copy() for k in ("e", "W", "F")]
    vertical_F = np.zeros((len(labels), 6))
    nodal_reports = []
    tangent = np.array([0, np.cos(np.deg2rad(50)), np.sin(np.deg2rad(50))])
    for i, (case, saved) in enumerate(zip(inputs["cases"], read(accounting.LOADS)["cases"], strict=True)):
        require(case["case_id"] == saved["case_id"], "case order changed")
        load = case["source_applied_load"]
        nodes = [int(n) for n in saved["climber_nodal_map"]]
        require(len(nodes) == 8, "expected one eight-node imprinted patch")
        positions = np.array([xyz[n] for n in nodes])
        center = np.array(load["patch_center_global_xyz_mm"])
        relative = positions - center
        x, t = abs(relative[:, 0]), abs(relative @ tangent)
        corner = (abs(x - 10) < 1e-5) & (abs(t - 10) < 1e-5)
        middle = ((x < 1e-5) & (abs(t - 10) < 1e-5)) | ((t < 1e-5) & (abs(x - 10) < 1e-5))
        require(np.count_nonzero(corner) == 4 and np.count_nonzero(middle) == 4,
                "patch is not the saved complete S8 square")
        weights = np.where(corner, -1 / 12, 1 / 3)
        force = np.array(load["applied_force_global_xyz_n"])
        lever = np.array(load["force_application_point_global_xyz_mm"]) - center
        original = traction_wrench(positions, weights, force, np.cross(lever, force), center)
        saved_values = np.array([saved["climber_nodal_map"][str(n)] for n in nodes])
        error = float(np.max(abs(original - saved_values)))
        require(error < 1e-5, "saved complete patch nodal loads not reproduced")
        force[:2] = 0
        values = traction_wrench(positions, weights, force, np.cross(lever, force), center)
        for node, value in zip(nodes, values, strict=True):
            for direction in (1, 2, 3):
                vertical_F[row_for[(node, direction)], i] = value[direction - 1]
        nodal_reports.append({"case_id": case["case_id"], "original_nodal_error_n": error})
    e_vertical = np.zeros((len(source_e), 6))
    W_vertical = np.zeros((300, 6))
    e_original = np.zeros_like(e_vertical)
    W_original = np.zeros_like(W_vertical)
    body_reports = []
    for body in sorted({case["loaded_panel"] for case in inputs["cases"]}):
        body_id = metadata["body_names"].index(body)
        dofs = np.flatnonzero(owners == body_id)
        _, R, Q = helper.rigid_basis([labels[int(i)] for i in dofs], xyz)
        full = source_F[dofs, 1::2]
        vertical = vertical_F[dofs]
        raw = np.column_stack((full, vertical))
        elastic = raw - Q @ (Q.T @ raw)
        body_K = K[dofs][:, dofs].tocsr()
        factor, system = helper.factor_bordered(body_K, R)
        solved = quotient.solve_quotient_chunk(factor, system, body_K, R, elastic)
        require(solved["status"] == quotient.PASS_ELASTIC_QUOTIENT_SCREEN,
                body + ": " + solved["status"])
        response = B[:, dofs] @ solved["displacement_mm"]
        e_original += response[:, :6]
        e_vertical += response[:, 6:]
        W_original[6 * body_id:6 * body_id + 6] = R.T @ full
        W_vertical[6 * body_id:6 * body_id + 6] = R.T @ vertical
        body_reports.append({"body": body, "KKT_upper_force_residual_relative": solved["KKT_upper_force_residual_relative"]})
        print(body, "separated live load components", flush=True)
    e_error = float(np.max(abs(e_original - source_e[:, 1::2])))
    W_error = float(np.max(abs(W_original - source_W[:, 1::2])))
    require(e_error < 1e-8 and W_error < 1e-7, "original live operator not reproduced")
    for p, h in pins.items():
        require(sha(p) == h, "component input changed during calculation")
    output.mkdir(parents=True)
    np.savez_compressed(output / "components.npz", e_vertical=e_vertical,
                        W_vertical=W_vertical, F_vertical=vertical_F)
    report = {
        "schema": "explicit_hold_load_components/v1",
        "source_sha256": {str(p.relative_to(ROOT)): h for p, h in pins.items()},
        "frame_operator_sha256": sha(frame_directory / "operators.npz"),
        "producer_sha256": sha(Path(__file__)),
        "components_sha256": sha(output / "components.npz"),
        "nodal_reports": nodal_reports, "body_reports": body_reports,
        "original_e_error_mm": e_error, "original_W_error_n": W_error,
        "gravity_unchanged": True, "native_launch": False,
        "complete_joint_acceptance": False, "physical_release": False,
    }
    (output / "receipt.json").write_text(json.dumps(report, indent=2, allow_nan=False) + "\n")
    (output / "producer.py.snapshot").write_bytes(Path(__file__).read_bytes())


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--frame-directory", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    lock = ROOT / "docs/wood-joints-mvp/luna-max-native-run-ledger.lock"
    with lock.open("a") as stream:
        fcntl.flock(stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
        require(read(lock.with_suffix(".json"))["slot"]["state"] == "idle", "shared analysis slot occupied")
        build(args.frame_directory, args.output)
