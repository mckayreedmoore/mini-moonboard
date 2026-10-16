"""Parent-owned vertical climber-load comparison with fixed horizontal load.

Reuse the authenticated nodal live-load decomposition and current panel
kernel. This adapter prepares load vectors only; frame response is separate.
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
COMPONENTS = HERE / "load-components-attempt01"
COMPONENT_RECEIPT_SHA = "178a745fe832f9521591b82a26cd6952e108aa374f1e27b7e010a876edf19a0e"


def build(output, weight_lb, *, methods, frame, native):
    """Parent passes authenticated original-geometry frame and native arrays."""
    move = methods.module(HERE / "panel-load-sharing-remedy.py", "weight_panel_kernel")
    require = move.require
    require(math.isfinite(weight_lb) and 0 < weight_lb <= 250, "invalid comparison weight")
    require(frame["H"].shape == (3192, 3192) and frame["e"].shape == (3192, 12),
            "weight basis requires the original 66-axis horizontal profile")
    require(native["F"].shape == (37647, 12), "native case basis differs")
    require(methods.sha(COMPONENTS / "receipt.json") == COMPONENT_RECEIPT_SHA,
            "live-load decomposition receipt changed")
    receipt = json.loads((COMPONENTS / "receipt.json").read_text())
    pins = {**frame["source_sha256"], **native["source_sha256"]}
    for key, digest in receipt["source_sha256"].items():
        path = ROOT / key
        require(methods.sha(path) == digest, "decomposition source changed: " + key)
        pins[path] = digest
    component_path = COMPONENTS / "components.npz"
    require(methods.sha(component_path) == receipt["components_sha256"],
            "nodal vertical load decomposition changed")
    for path in (component_path, COMPONENTS / "receipt.json", Path(__file__)):
        pins[path] = methods.sha(path)
    with np.load(component_path, allow_pickle=False) as data:
        vertical_F = data["F_vertical"].copy()
    require(vertical_F.shape == (37647, 6), "decomposition case inventory differs")
    static = move._load_static()
    pins.update(static.pins)
    kernel = move.module(move.WIDTH / "producer.py.snapshot", "weight_width_materials")
    materials = kernel.deck_materials(move.NATIVE / "model.inp")
    model = json.loads((move.OLD / "model.json").read_text())
    for path in (move.WIDTH / "producer.py.snapshot", move.NATIVE / "model.inp",
                 move.OLD / "model.json", HERE / "panel-load-sharing-remedy.py"):
        pins[path] = methods.sha(path)
    helper = methods.module(move.CONDENSATION, "weight_panel_condensation")
    quotient = methods.module(move.QUOTIENT, "weight_panel_quotient")
    output = methods.output_directory(output)
    (output / "producer.py.snapshot").write_bytes(Path(__file__).read_bytes())
    reproduced_e = np.zeros((3192, 6))
    reproduced_W = np.zeros((344, 6))
    vertical_e = np.zeros_like(reproduced_e)
    vertical_W = np.zeros_like(reproduced_W)
    reports = []
    loaded = np.flatnonzero(np.max(abs(vertical_F), axis=1) > 0)
    body_ids = set(np.asarray(native["owners"])[loaded].tolist())
    expected_bodies = {"main_upper_left", "main_upper_right", "main_lower_left"}
    require({native["names"][i] for i in body_ids} == expected_bodies,
            "vertical decomposition has an unexpected loaded body")
    cache = {}
    for body in kernel.PANELS:
        body_id = native["names"].index(body)
        dofs, K, kernel_audit = move._panel_width_matrix(native, body, static.corner, model, materials,
                                                       translation_cache=cache)
        if body not in expected_bodies:
            continue
        labels = [native["labels"][int(i)] for i in dofs]
        xyz = {node: native["coordinates"][node] for node, _ in labels}
        _center, R, Q = helper.rigid_basis(labels, xyz, 1000.)
        rhs = np.column_stack((native["F"][dofs, 1::2], vertical_F[dofs]))
        rhs -= Q @ (Q.T @ rhs)
        audit = quotient.audit_quotient_operator(K, R)
        require(audit["status"] == quotient.PASS_ELASTIC_QUOTIENT_SCREEN,
                body + ": quotient screen failed")
        factor, system = helper.factor_bordered(K, R)
        solved = quotient.solve_quotient_chunk(factor, system, K, R, rhs, operator_report=audit)
        require(solved["status"] == quotient.PASS_ELASTIC_QUOTIENT_SCREEN,
                body + ": live decomposition solve failed")
        response = np.asarray(frame["Bwood"][:, dofs] @ solved["displacement_mm"])
        reproduced_e += response[:, :6]
        vertical_e += response[:, 6:]
        rows = slice(6 * body_id, 6 * body_id + 6)
        reproduced_W[rows] = R.T @ native["F"][dofs, 1::2]
        vertical_W[rows] = R.T @ vertical_F[dofs]
        reports.append({"body": body, "kernel": kernel_audit,
            "quotient_status": solved["status"],
            "KKT_upper_force_residual_relative": solved["KKT_upper_force_residual_relative"]})
        print(body + ": fixed-horizontal live-load decomposition passed", flush=True)
    e_error = float(np.max(abs(reproduced_e - frame["e"][:, 1::2])))
    W_error = float(np.max(abs(reproduced_W - frame["W"][:, 1::2])))
    diagnostics = {"body_reports": reports,
        "original_live_e_reproduction_error_mm": e_error,
        "original_live_W_reproduction_error_N": W_error,
        "worst_e_port_case": list(map(int, np.unravel_index(
            np.argmax(abs(reproduced_e - frame["e"][:, 1::2])), reproduced_e.shape))),
        "worst_W_rigid_case": list(map(int, np.unravel_index(
            np.argmax(abs(reproduced_W - frame["W"][:, 1::2])), reproduced_W.shape))),
        "no_native_launch": True, "frame_response_executed": False}
    np.savez_compressed(output / "reproduction-diagnostics.npz", reproduced_e=reproduced_e,
        reproduced_W=reproduced_W, vertical_e=vertical_e, vertical_W=vertical_W,
        expected_e=frame["e"][:, 1::2], expected_W=frame["W"][:, 1::2])
    methods.write(output / "operator-audit.json", diagnostics)
    print(json.dumps(diagnostics), flush=True)
    if e_error >= 1e-8 or W_error >= 1e-7:
        methods.write(output / "stop.json", {"status": "STOP_ORIGINAL_LIVE_REPRODUCTION_FAILED",
            "source_sha256": {str(Path(p).resolve().relative_to(ROOT)): h for p, h in pins.items()},
            "output_sha256": {p.name: methods.sha(p) for p in output.iterdir()
                              if p.is_file() and p.name != ".gitignore"},
            "diagnostics": diagnostics, "physical_release": False})
    require(e_error < 1e-8 and W_error < 1e-7,
            "full source live response was not reproduced")
    # Independent analytic combination: A12 rear/forward cancel the 300N
    # horizontal force and its full lever couple, leaving the vertical patch.
    require(np.max(abs(vertical_F[:, 0] - (native["F"][:, 1] + native["F"][:, 3]) / 2)) < 1e-8,
            "A12 vertical patch does not equal opposite-horizontal average")
    require(np.max(abs(vertical_e[:, 0] - (frame["e"][:, 1] + frame["e"][:, 3]) / 2)) < 1e-8,
            "A12 vertical elastic response does not equal known load combination")
    scale = float(weight_lb / 250)
    de, dW = np.zeros_like(frame["e"]), np.zeros_like(frame["W"])
    de[:, 1::2], dW[:, 1::2] = (scale - 1) * vertical_e, (scale - 1) * vertical_W
    Fnew = native["F"].copy()
    Fnew[:, 1::2] += (scale - 1) * vertical_F
    require(np.array_equal(Fnew[:, ::2], native["F"][:, ::2]), "gravity columns changed")
    np.savez_compressed(output / "load-delta.npz", de=de, dW=dW, F_native=Fnew,
                        F_original=native["F"], F_vertical=vertical_F)
    comparison = {"schema": "fixed_horizontal_climber_weight_loads/v1",
        "source_climber_weight_lb": 250., "comparison_climber_weight_lb": float(weight_lb),
        "vertical_live_scale": scale, "downward_dynamic_factor": 2.,
        "downward_climber_force_N": weight_lb * 2 * 4.4482216152605,
        "horizontal_force_magnitude_N": 300., "horizontal_live_scale": 1.,
        "hold_lever_mm": 100., "gravity_and_accessory_unchanged": True,
        "geometry_operator_basis": "original_66_horizontal_profile_before_any_axis_operator_delta",
        "source_requirement_replaced": False, "physical_release": False}
    methods.write(output / "load-comparison.json", comparison)
    diagnostics["A12_opposite_horizontal_combination_passed"] = True
    methods.write(output / "operator-audit.json", diagnostics)
    for path, digest in pins.items():
        require(methods.sha(path) == digest, "weight input changed during preparation")
    methods.write(output / "receipt.json", {"schema": "climber_weight_load_delta_receipt/v1",
        "source_sha256": {str(Path(p).resolve().relative_to(ROOT)): h for p, h in pins.items()},
        "output_sha256": {p.name: methods.sha(p) for p in output.iterdir()
                          if p.is_file() and p.name != ".gitignore"},
        "status": "PREPARED_LOAD_COMPARISON_FRAME_RESPONSE_REQUIRED", "physical_release": False})
    return output


def reweight_axis_packet(source, loads, output, *, methods, reader, mechanics, frame, native):
    """Reuse frozen geometry H/D while recomputing its changed-point live e.

    The original weight delta and the geometry delta have a mixed term. This
    function calculates that term with the full changed B, retaining the
    original panel kernel and all additional-screw dead loads.
    """
    import shutil

    from scipy import sparse

    move = methods.module(HERE / "panel-load-sharing-remedy.py", "reweight_axis_panel_kernel")
    source, loads = Path(source).resolve(), Path(loads).resolve()
    old_Bwood = frame["Bwood"].copy()
    _recovery, _context, load_binding = reader.apply_case_loads(methods, mechanics, frame, loads, frame["source_sha256"])
    pins = dict(frame["source_sha256"])
    recovery, context, geometry_binding = reader.apply_axis_operators(methods, mechanics, frame, source, pins)
    require = move.require
    require(context["screw_axis_count"] == 98 and frame["H"].shape == (3288, 3288),
            "bounded reweighting expects the existing authorized 98-screw packet")
    with np.load(loads / "load-delta.npz", allow_pickle=False) as data:
        vertical_F, original_F, original_de = [data[k].copy() for k in ("F_vertical", "F_original", "de")]
    require(np.array_equal(recovery["F"][:, 1::2], original_F[:, 1::2]),
            "geometry packet has another live-load basis")
    scale_delta = load_binding["comparison"]["vertical_live_scale"] - 1
    require(scale_delta < 0, "reweighting requires a lower comparison weight")
    static = move._load_static()
    pins.update(static.pins)
    original_raw = sparse.vstack((static.B0, sparse.csr_matrix((96, 37647))), format="csr")
    require(recovery["B"].shape == original_raw.shape == (1984, 37647), "98 raw action census differs")
    mr, mc, mv = [], [], []
    for item in recovery["mapping"]["kept_map"]:
        mr.extend([item["kept_position"]] * len(item["raw_rows"]))
        mc.extend(item["raw_rows"])
        mv.extend(item["weights"])
    P = sparse.coo_matrix((mv, (mr, mc)), shape=(3288, 1984)).tocsr()
    require(len(set(mr)) == 1688 and max(mr) == 3287, "full 98 current mapping differs")
    delta_B = (P @ (recovery["B"] - original_raw)).tocsr()
    kernel = move.module(move.WIDTH / "producer.py.snapshot", "reweight_exact_width_kernel")
    materials = kernel.deck_materials(move.NATIVE / "model.inp")
    model = json.loads((move.OLD / "model.json").read_text())
    helper = methods.module(move.CONDENSATION, "reweight_condensation")
    quotient = methods.module(move.QUOTIENT, "reweight_quotient")
    mixed_vertical = np.zeros((3288, 6))
    original_vertical = np.zeros((3192, 6))
    reports, cache = [], {}
    for body in kernel.PANELS:
        dofs, K, kernel_audit = move._panel_width_matrix(native, body, static.corner, model, materials,
                                                       translation_cache=cache)
        if np.max(abs(vertical_F[dofs])) == 0:
            continue
        labels = [native["labels"][int(i)] for i in dofs]
        xyz = {node: native["coordinates"][node] for node, _ in labels}
        _center, R, Q = helper.rigid_basis(labels, xyz, 1000.)
        rhs = vertical_F[dofs].copy()
        rhs -= Q @ (Q.T @ rhs)
        audit = quotient.audit_quotient_operator(K, R)
        require(audit["status"] == quotient.PASS_ELASTIC_QUOTIENT_SCREEN, body + ": quotient screen failed")
        factor, system = helper.factor_bordered(K, R)
        solved = quotient.solve_quotient_chunk(factor, system, K, R, rhs, operator_report=audit)
        require(solved["status"] == quotient.PASS_ELASTIC_QUOTIENT_SCREEN, body + ": mixed load solve failed")
        U = solved["displacement_mm"]
        mixed_vertical += delta_B[:, dofs] @ U
        original_vertical += old_Bwood[:, dofs] @ U
        reports.append({"body": body, "kernel": kernel_audit, "quotient_status": solved["status"],
                        "KKT_upper_force_residual_relative": solved["KKT_upper_force_residual_relative"]})
    error = float(np.max(abs(original_vertical - original_de[:, 1::2] / scale_delta)))
    require(error < 1e-8, "Original-weight vertical response reproduction failed")
    source_receipt = json.loads((source / "receipt.json").read_text())
    with np.load(source / "operator-delta.npz", allow_pickle=False) as data:
        operators = {k: data[k].copy() for k in data.files}
    require(operators["de"].shape == (3288, 12), "geometry elastic-load delta shape differs")
    operators["de"][:, 1::2] += scale_delta * mixed_vertical
    operators["F_native"][:, 1::2] += scale_delta * vertical_F
    require(np.array_equal(operators["F_native"][:, ::2], recovery["F"][:, ::2]),
            "Additional-screw gravity columns changed")
    pins[Path(__file__)] = methods.sha(__file__)
    for path in (move.WIDTH / "producer.py.snapshot", move.NATIVE / "model.inp", move.OLD / "model.json"):
        pins[path] = methods.sha(path)
    output = methods.output_directory(output)
    for name in source_receipt["output_sha256"]:
        if name not in ("operator-delta.npz", "receipt.json", "producer.py.snapshot", "runner.py.snapshot", ".gitignore"):
            shutil.copyfile(source / name, output / name)
    (output / "producer.py.snapshot").write_bytes(Path(__file__).read_bytes())
    np.savez_compressed(output / "operator-delta.npz", **operators)
    context["load_comparison"] = load_binding["comparison"]
    context["head_pull_through_esg"] = .50
    context["panel_grade_owner_report"] = "Group 1, sanded A-C"
    methods.write(output / "panel-reference-context.json", context)
    proposal = json.loads((output / "proposal.json").read_text())
    proposal["case_load_comparison"] = load_binding
    proposal["reused_geometry_operator_packet"] = geometry_binding
    methods.write(output / "proposal.json", proposal)
    methods.write(output / "mixed-load-update-audit.json", {"schema": "axis_geometry_weight_mixed_term/v1",
        "source_geometry": geometry_binding, "load_comparison": load_binding,
        "original_vertical_e_reproduction_error_mm": error, "bodies": reports,
        "dH_dD_dW_and_gravity_columns_preserved": True,
        "mixed_term_rule": "de145=de250+(145/250-1)*(Bnew-Boriginal)Kquotient_inverse Fvertical",
        "complete_joint_acceptance": False, "physical_release": False})
    require(all(methods.sha(p) == h for p, h in pins.items()), "Mixed-term input changed")
    methods.write(output / "receipt.json", {"schema": "axis_weight_reweighted_operator_delta_receipt/v1",
        "source_sha256": {mechanics.source_key(p): h for p, h in pins.items()},
        "output_sha256": {p.name: methods.sha(p) for p in output.iterdir() if p.is_file() and p.name != ".gitignore"},
        "status": "PREPARED_REWEIGHTED_98_OPERATORS_FRAME_RESPONSE_REQUIRED", "physical_release": False})
    print(json.dumps({"output": str(output), "reproduction_error_mm": error}))
    return output


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--weight-lb", type=float, required=True)
    parser.add_argument("--axis-operators", type=Path)
    parser.add_argument("--case-loads", type=Path)
    args = parser.parse_args()
    sys.path[:0] = [str(ROOT), str(HERE.parent)]
    import importlib.util

    spec = importlib.util.spec_from_file_location("weight_parent_reader", HERE / "hardware-clearance-remedy.py")
    reader = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(reader)
    methods = reader.load_methods()
    _follow, mechanics, frame, _pins, _orientation = reader.load_frame(methods)
    native = mechanics.source_context()
    if args.axis_operators is None:
        build(args.output, args.weight_lb, methods=methods, frame=frame, native=native)
    else:
        if args.case_loads is None:
            parser.error("--case-loads is required with --axis-operators")
        if json.loads((args.case_loads / "load-comparison.json").read_text())["comparison_climber_weight_lb"] != args.weight_lb:
            parser.error("--weight-lb differs from the authenticated load packet")
        reweight_axis_packet(args.axis_operators, args.case_loads, args.output, methods=methods,
                             reader=reader, mechanics=mechanics, frame=frame, native=native)
