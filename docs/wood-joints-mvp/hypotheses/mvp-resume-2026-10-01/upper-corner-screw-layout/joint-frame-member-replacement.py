"""Replace a complete timber contribution in the existing REVIEWED104 frame.

No solver, evidence read, or calculation occurs on import. ``prepare`` only
authenticates a frozen request. The parent serializes native matrix reads,
``reduce_body`` and actual frame equilibrium. No native executable is launched.
The source body is gross/filled-bore; a drilled/cracked replacement must supply
its own K/B/F/R, preserving the source datum, external wrench and port ordering.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import sys
import time
from pathlib import Path

import numpy as np
from scipy import sparse

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
RAW = HERE / "rawlocal/joint-frame-member-replacement"
FRAME = HERE / "rawlocal/joint-frame-compatibility-completion/frame-attempt08"
PREPARATION = HERE / "rawlocal/joint-frame-compatibility-completion/prepare-attempt03"
WOOD = HERE / "rawlocal/joint-frame-port-reduction/attempt01"
ACTIONS = HERE / "rawlocal/joint-frame-action-reconciliation/attempt03"
WORKING_PROFILE = HERE / "rawlocal/washer-working-profile-completion/preparation01"
WORKING_PROFILE_RECEIPT_SHA256 = "8f64eabfd382d51b2cf5cf0aa67c2149bc13cb7ea825ebe076572c80418a89c1"
ROTATION_SCALE_MM = 1000.0
CASES = ("a12-rear", "a12-forward", "a12-left", "k12-right", "k12-rear", "a1-rear")
PARTIAL_CONSTANT = "selected_body_load_matrix_plus_unchanged_constant"
COMPLETE_CONSTANT = "complete_assembly_body_load_matrix"


def require(condition, message):
    if not condition:
        raise ValueError("STOP: " + message)


def sha(path):
    with Path(path).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def read(path):
    return json.loads(Path(path).read_text())


def write(path, value):
    Path(path).write_text(json.dumps(value, indent=2, allow_nan=False) + "\n")


def source_key(path):
    """Keep explicit frozen reference sources absolute when outside ROOT."""
    path = Path(path).resolve()
    return path.relative_to(ROOT).as_posix() if path.is_relative_to(ROOT) else str(path)


def module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    loaded = importlib.util.module_from_spec(spec)
    old_path, old_bytecode = sys.path[:], sys.dont_write_bytecode
    try:
        sys.path[:0] = [str(ROOT), str(HERE.parent)]
        sys.dont_write_bytecode = True
        spec.loader.exec_module(loaded)
    finally:
        sys.path[:] = old_path
        sys.dont_write_bytecode = old_bytecode
    return loaded


def compatibility():
    return module(HERE / "joint-frame-compatibility-completion.py", "member_replacement_frame")


def floor_failure_summary(exception):
    """Delegate the snapshot-only action consumer to the existing pure helper.

    Imports stay inside this wrapper because that consumer extracts this one
    function with AST, without importing the producer or executing mechanics.
    Commands run in the repository; the consumed source closure pins the helper.
    """
    import importlib.util
    from pathlib import Path

    root = next(p for p in (Path.cwd(), *Path.cwd().parents) if (p / "current-candidate.json").is_file())
    path = root / "docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/upper-corner-screw-layout/joint-frame-compatibility-completion.py"
    spec = importlib.util.spec_from_file_location("member_replacement_saved_floor_summary", path)
    method = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(method)
    return method.floor_failure_summary(exception)


def source_pin_paths():
    """Required source files; no evidence is opened by this function."""
    port = module(HERE / "joint-frame-port-reduction.py", "member_replacement_port")
    paths = port.source_pin_paths()
    paths.update({"port_adapter": HERE / "joint-frame-port-reduction.py",
                  "frame_adapter": HERE / "joint-frame-compatibility-completion.py",
                  "producer": Path(__file__).resolve(),
                  "frame_receipt": FRAME / "receipt.json", "frame_inputs": FRAME / "inputs.json",
                  "frame_comparison": FRAME / "comparison.json", "frame_response": FRAME / "response.npz",
                  "preparation_receipt": PREPARATION / "receipt.json",
                  "joint_operators": PREPARATION / "joint-operators.npz",
                  "port_labels": PREPARATION / "port-labels.json",
                  "port_request": PREPARATION / "wood-port-request.json",
                  "wood_receipt": WOOD / "receipt.json", "wood_certificate": WOOD / "certificate.json",
                  "wood_request": WOOD / "request.json", "wood_operators": WOOD / "wood-operators.npz",
                  "wood_projection": WOOD / "Bwood.npz", "action_receipt": ACTIONS / "receipt.json",
                  "action_summary": ACTIONS / "summary.json", "action_rows": ACTIONS / "source-row-map.json"})
    return paths


def authenticate(pins):
    for path, digest in pins.items():
        require(sha(path) == digest, "source SHA-256 mismatch: " + str(path))


def prepare(output, request, expected_sha256):
    """Authenticate inputs and save only small known answers; no project solve."""
    output, request = Path(output).resolve(), Path(request).resolve()
    require(output.is_relative_to(RAW.resolve()) and output != RAW.resolve() and not output.exists(),
            "fresh output below rawlocal/joint-frame-member-replacement required")
    require(sha(request) == expected_sha256, "request SHA-256 differs")
    record = read(request)
    require(record.get("schema") == "joint_frame_member_replacement_request/v1", "request schema differs")
    require(record.get("source_frame_directory") == FRAME.relative_to(ROOT).as_posix()
            and record.get("preparation_directory") == PREPARATION.relative_to(ROOT).as_posix()
            and record.get("wood_reduction_directory") == WOOD.relative_to(ROOT).as_posix()
            and record.get("action_directory") == ACTIONS.relative_to(ROOT).as_posix(), "selected source authority differs")
    pins = {}
    for relative, digest in record.get("source_sha256", {}).items():
        path = (ROOT / relative).resolve()
        require(not Path(relative).is_absolute() and path.is_relative_to(ROOT)
                and isinstance(digest, str) and len(digest) == 64
                and all(c in "0123456789abcdef" for c in digest), "invalid source pin")
        require(path not in pins, "duplicate normalized source pin")
        pins[path] = digest
    missing = [str(p.relative_to(ROOT)) for p in source_pin_paths().values() if p not in pins]
    require(not missing, "missing source pins: " + ", ".join(missing))
    authenticate(pins)
    require(record.get("reviewed_bolt_axes") == 104 and record.get("hillman_axes") == 66
            and record.get("geometry_changed") is False, "reviewed geometry/hardware contract differs")
    output.mkdir(parents=True, exist_ok=False)
    (output / "request.json").write_bytes(request.read_bytes())
    (output / "producer.py.snapshot").write_bytes(Path(__file__).read_bytes())
    write(output / "known-answer.json", known_answer())
    certificate = {"schema": "joint_frame_member_replacement_preparation/v1",
        "status": "PREPARED_MEMBER_REPLACEMENT_NOT_FRAME_RESPONSE", "request_sha256": expected_sha256,
        "source_sha256": {source_key(p): d for p, d in pins.items()},
        "rotation_scale_mm": ROTATION_SCALE_MM, "reviewed_bolt_axes": 104, "hillman_axes": 66,
        "body_load_energy_scope": PARTIAL_CONSTANT, "unchanged_body_load_chi_nmm": None,
        "project_native_factorizations": 0, "frame_solves": 0, "physical_release": False,
        "complete_joint_acceptance": False}
    write(output / "certificate.json", certificate)
    authenticate(pins)
    require(sha(request) == expected_sha256, "request changed during preparation")
    write(output / "receipt.json", {"schema": "joint_frame_member_replacement_receipt/v1",
        "status": certificate["status"], "source_sha256": certificate["source_sha256"],
        "output_sha256": {name: sha(output / name) for name in
                          ("request.json", "certificate.json", "known-answer.json", "producer.py.snapshot")},
        "physical_release": False})
    return certificate


def load_frame(preparation=PREPARATION, wood_reduction=WOOD, source_response=FRAME):
    """Reconstruct the source frame, reusing its shaft and contact laws exactly."""
    preparation, wood_reduction, source_response = [Path(p).resolve() for p in
                                                   (preparation, wood_reduction, source_response)]
    require((preparation, wood_reduction, source_response) ==
            (PREPARATION.resolve(), WOOD.resolve(), FRAME.resolve()), "frame08 source selection required")
    core, pins = compatibility(), {}
    response_receipt = core.bind_packet(source_response, pins, preserved_producer=True)
    prepared = core.bind_packet(preparation, pins, preserved_producer=True)
    wood_receipt = core.bind_packet(wood_reduction, pins)
    require(prepared["status"] == "PREPARED_COUPLED_PORTS_NOT_FRAME_RESPONSE"
            and wood_receipt["status"] == "PASS_JOINT_FRAME_PORT_REDUCTION", "source preparation/reduction did not pass")
    require(response_receipt["status"] == core.PARTIAL_STATUS, "selected frame disposition differs")
    inputs = read(source_response / "inputs.json")
    require(inputs["preparation"] == preparation.relative_to(ROOT).as_posix()
            and inputs["wood_reduction"] == wood_reduction.relative_to(ROOT).as_posix()
            and inputs["proposal_ties_included"] is False, "source frame input binding differs")
    with np.load(preparation / "joint-operators.npz", allow_pickle=False) as data:
        joint = {name: data[name].copy() for name in data.files}
    with np.load(wood_reduction / "wood-operators.npz", allow_pickle=False) as data:
        Hwood, Dwood, e, Wwood = [data[name].copy() for name in ("Hwood", "Dwood", "ewood", "Wwood")]
    nold = len(joint["old_kept_lumped_rows"])
    Bbolt = np.vstack((np.zeros((nold, joint["Bbolt"].shape[1])), joint["Bbolt"]))
    Dwasher = np.vstack((np.zeros((nold, 24)), joint["Dwasher"]))
    H = Hwood + Bbolt @ joint["Cbolt"] @ Bbolt.T
    D = np.column_stack((Dwood, Bbolt @ joint["Rbolt"], Dwasher))
    W = np.vstack((Wwood, np.zeros((44, 12))))
    require(H.shape == (3192, 3192) and D.shape == (3192, 344) and e.shape == (3192, 12)
            and W.shape == (344, 12), "current frame coordinate/port census differs")
    joint["panel_screw_ports"] = core.panel_screw_ports(read(core.OPERATORS / "row-identities.json"), joint)
    comparison = read(source_response / "comparison.json")
    require(len(comparison["case_dispositions"]) == 14 and len(comparison["states"]) == 12,
            "selected twelve-field/fourteen-disposition inventory differs")
    return {"H": H, "D": D, "e": e, "W": W, "Hwood": Hwood, "Dwood": Dwood,
            "Wwood": Wwood, "Bwood": sparse.load_npz(wood_reduction / "Bwood.npz").tocsr(),
            "Bbolt": Bbolt, "Dwasher": Dwasher, "joint": joint,
            "dead_load_factor": inputs["dead_load_factor"], "modeled_mass_kg": inputs["modeled_mass_kg"], "source_sha256": pins,
            "source_frame_sha256": sha(source_response / "receipt.json"),
            "source_dispositions": comparison["case_dispositions"],
            "energy_constant_scope": PARTIAL_CONSTANT,
            "unchanged_constant_token": sha(source_response / "receipt.json"),
            "physical_release": False}


def source_context(wood_reduction=WOOD):
    """Read one original native matrix and maps; parent owns this operation."""
    require(Path(wood_reduction).resolve() == WOOD.resolve(), "source wood port selection differs")
    port = module(HERE / "joint-frame-port-reduction.py", "member_replacement_source_ports")
    paths, pins = port.source_pin_paths(), {}
    receipt = compatibility().bind_packet(wood_reduction, pins)
    require(receipt["status"] == "PASS_JOINT_FRAME_PORT_REDUCTION", "source wood reduction did not pass")
    parser = module(paths["parser"], "member_replacement_native_parser")
    helper = module(paths["helper"], "member_replacement_native_helper")
    source = parser.load_frame_source_model(paths["source_model"])
    coordinates = {int(n): np.asarray(x, dtype=float) for n, x in
                   read(paths["coordinates"])["physical_node_coordinates_mm"].items()}
    names = read(paths["coordinates"])["body_names"]
    require(names == list(source["bodies"]) and len(names) == 50, "original native body order differs")
    labels = parser.parse_dof_file(paths["native_dofs"])
    parser.require_dof_bijection(labels, source["physical_nodes"], parser.FRAME_DOF_COUNT)
    owners = np.asarray([source["owner_by_node"][node] for node, _ in labels])
    parsed = parser.parse_upper_triangle_file(paths["native_stiffness"], len(labels),
                                            owner_by_row=owners, owner_names=names)
    parser.require_no_cross_body_coupling(parsed)
    with np.load(paths["operators"], allow_pickle=False) as data:
        F = data["F"].copy()
    with np.load(Path(wood_reduction) / "wood-operators.npz", allow_pickle=False) as data:
        D, W = data["Dwood"].copy(), data["Wwood"].copy()
    authenticate(pins)
    return {"K": parsed["matrix"], "B": sparse.load_npz(Path(wood_reduction) / "Bwood.npz").tocsr(),
            "F": F, "D": D, "W": W, "names": names, "labels": labels,
            "owners": owners, "coordinates": coordinates, "source": source,
            "helper": helper, "source_sha256": pins}


def source_body(member_id, wood_reduction=WOOD, context=None):
    """Extract complete old body maps, including every incident cross-port."""
    context = source_context(wood_reduction) if context is None else context
    require(member_id in context["names"], "unknown source body: " + member_id)
    body = context["names"].index(member_id)
    dofs = np.flatnonzero(context["owners"] == body)
    labels = [context["labels"][int(i)] for i in dofs]
    coordinates = {node: context["coordinates"][node] for node, _ in labels}
    require(all(np.array_equal(x, context["source"]["coordinates"][node])
                for node, x in coordinates.items()), "native/body coordinates differ")
    datum, R, _ = context["helper"].rigid_basis(labels, coordinates, ROTATION_SCALE_MM)
    B, F = context["B"][:, dofs].tocsr(), context["F"][dofs]
    D, W = np.asarray(B @ R), R.T @ F
    columns = slice(6 * body, 6 * body + 6)
    require(np.max(abs(D - context["D"][:, columns]), initial=0) < 1e-8
            and np.max(abs(W - context["W"][columns]), initial=0) < 1e-8,
            "source body D/W provenance differs")
    return {"member_id": member_id, "K": context["K"][dofs][:, dofs].tocsr(),
            "B": B, "F": F, "R": R, "D": D, "W": W, "labels": labels,
            "coordinates": coordinates, "datum_mm": datum, "body_id": body,
            "rotation_scale_mm": ROTATION_SCALE_MM}


def save_source_body(output, body):
    """Save the selected original native inputs without another factorization."""
    nodes = sorted(body["coordinates"])
    sparse.save_npz(output / "source-body-K.npz", body["K"])
    sparse.save_npz(output / "source-body-B.npz", body["B"])
    np.savez_compressed(output / "source-body.npz", F=body["F"], R=body["R"], D=body["D"], W=body["W"],
        labels=np.asarray(body["labels"], dtype=int), node_ids=np.asarray(nodes, dtype=int),
        node_coordinates_mm=np.asarray([body["coordinates"][n] for n in nodes]), datum_mm=body["datum_mm"])
    write(output / "source-body.json", {"schema": "joint_frame_original_native_body/v1",
        "member_id": body["member_id"], "body_id": body["body_id"], "rotation_scale_mm": ROTATION_SCALE_MM,
        "port_order": "All3192 current Bwood rows; 1592 old kept followed by1600 continuous-shaft/contact ports.",
        "geometry": "Original gross filled-bore source native solid, not a drilled/cracked solid.",
        "native_factorizations": 0, "physical_release": False})


def source_export(output, member_id, source_check_packet):
    """Export native inputs; bind the previously reduced old H/e/L unchanged."""
    output, source_check_packet = Path(output).resolve(), Path(source_check_packet).resolve()
    require(output.is_relative_to(RAW.resolve()) and output != RAW.resolve() and not output.exists(), "fresh source-export output required")
    receipt_path = source_check_packet / "receipt.json"
    receipt = read(receipt_path)
    require(receipt["status"] == "PASS_SOURCE_BODY_REMOVE_REINSERT"
            and read(source_check_packet / "check.json")["member_id"] == member_id, "completed matching old-body reduction required")
    old_path = source_check_packet / "old-body-operators.npz"
    require(sha(old_path) == receipt["output_sha256"]["old-body-operators.npz"]
            and sha(source_check_packet / "check.json") == receipt["output_sha256"]["check.json"], "old-body reduction output binding differs")
    context = source_context()
    body = source_body(member_id, context=context)
    with np.load(old_path, allow_pickle=False) as reduced:
        require(np.max(abs(body["D"] - reduced["D"]), initial=0) < 1e-8
                and np.max(abs(body["W"] - reduced["W"]), initial=0) < 1e-8,
                "exported original native D/W differ from saved old-body reduction")
    for path, digest in context["source_sha256"].items():
        relative = path.relative_to(ROOT).as_posix()
        if relative in receipt["source_sha256"]:
            require(receipt["source_sha256"][relative] == digest, "source-check/export native source differs")
    output.mkdir(parents=True, exist_ok=False)
    save_source_body(output, body)
    (output / "producer.py.snapshot").write_bytes(Path(__file__).read_bytes())
    write(output / "old-body-binding.json", {"schema": "joint_frame_old_body_operator_binding/v1",
        "source_check_receipt": {"path": receipt_path.relative_to(ROOT).as_posix(), "sha256": sha(receipt_path)},
        "old_body_operators": {"path": old_path.relative_to(ROOT).as_posix(), "sha256": sha(old_path)},
        "native_factorizations": 0, "frame_solves": 0, "physical_release": False})
    pins = {**context["source_sha256"], Path(__file__).resolve(): sha(__file__),
            receipt_path: sha(receipt_path), old_path: sha(old_path),
            source_check_packet / "check.json": sha(source_check_packet / "check.json")}
    authenticate(pins)
    write(output / "receipt.json", {"schema": "joint_frame_original_native_body_receipt/v1", "status": "EXPORTED_ORIGINAL_NATIVE_BODY_WITHOUT_FACTOR",
        "source_sha256": {source_key(p): d for p, d in pins.items()},
        "output_sha256": {p.name: sha(p) for p in output.iterdir() if p.is_file()}, "physical_release": False})
    return body


def load_source_body(packet):
    """Read saved original native body inputs for localized remeshing."""
    packet = Path(packet).resolve()
    pins = {}
    receipt = compatibility().bind_packet(packet, pins)
    require(receipt["schema"] == "joint_frame_original_native_body_receipt/v1"
            and receipt["status"] == "EXPORTED_ORIGINAL_NATIVE_BODY_WITHOUT_FACTOR", "saved native body receipt differs")
    metadata = read(packet / "source-body.json")
    with np.load(packet / "source-body.npz", allow_pickle=False) as data:
        body = {key: data[key].copy() for key in ("F", "R", "D", "W", "datum_mm")}
        body["labels"] = [tuple(map(int, row)) for row in data["labels"]]
        body["coordinates"] = {int(n): xyz.copy() for n, xyz in zip(data["node_ids"], data["node_coordinates_mm"])}
    body.update(K=sparse.load_npz(packet / "source-body-K.npz").tocsr(),
                B=sparse.load_npz(packet / "source-body-B.npz").tocsr(), member_id=metadata["member_id"],
                body_id=metadata["body_id"], rotation_scale_mm=metadata["rotation_scale_mm"])
    return body


def reduce_body(K, B, F, R):
    """Reduce unbalanced unit port/body-load columns on the elastic quotient.

    Raw B/F and their D/W are retained. Projection only defines K_plus;
    actual assembled force/moment balance is audited after equilibrium.
    """
    paths = module(HERE / "joint-frame-port-reduction.py", "member_replacement_reduce_paths").source_pin_paths()
    helper = module(paths["helper"], "member_replacement_reduce_helper")
    quotient = module(paths["quotient"], "member_replacement_quotient")
    K, B = sparse.csr_matrix(K), sparse.csr_matrix(B)
    F, R = np.asarray(F, dtype=float), np.asarray(R, dtype=float)
    require(K.shape == (len(R), len(R)) and R.shape == (len(R), 6)
            and B.shape[1] == len(R) and F.ndim == 2 and F.shape[0] == len(R)
            and np.linalg.matrix_rank(R) == 6, "K/B/F/R shapes or rigid rank differ")
    require(all(np.isfinite(x).all() for x in (K.data, B.data, F, R)), "nonfinite body inputs")
    active = np.flatnonzero(np.diff(B.indptr))
    raw = np.column_stack((B[active].T.toarray(), F))
    Q, _ = np.linalg.qr(R, mode="reduced")
    elastic = raw - Q @ (Q.T @ raw)
    operator = quotient.audit_quotient_operator(K, R)
    require(operator["status"] == quotient.PASS_ELASTIC_QUOTIENT_SCREEN, "body rigid leakage failed")
    factor, system = helper.factor_bordered(K, R)
    solved = quotient.solve_quotient_chunk(factor, system, K, R, elastic, operator_report=operator)
    require(solved["status"] == quotient.PASS_ELASTIC_QUOTIENT_SCREEN, "body elastic quotient failed: " + solved["status"])
    audit = {key: solved[key] for key in ("status", "failed_gates", "KKT_upper_force_residual_relative",
        "projected_elastic_force_residual_relative", "max_gauge_R_transpose_u_mm", "rigid_identity_closure")}
    U = solved["displacement_mm"]
    return reduce_body_from_solutions(B, F, R, U[:, :len(active)], U[:, len(active):], audit, active, K)


def reduce_body_from_solutions(B, F, R, U_B, U_F, audit, active_ports=None, K=None):
    """Assemble operators from the existing audited localized solid recovery.

    U_B and U_F are elastic quotient solutions for raw B.T and F: remove only
    the six rigid-pose fields, retaining all elastic motion. The caller owns
    its original-K equilibrium/gauge audit; an accepted audit is mandatory.
    Passing K adds the deterministic native virtual-work witness below.
    """
    B, F, R = sparse.csr_matrix(B), np.asarray(F), np.asarray(R)
    U_B, U_F = np.asarray(U_B), np.asarray(U_F)
    active = np.flatnonzero(np.diff(B.indptr)) if active_ports is None else np.asarray(active_ports, dtype=int)
    require(np.array_equal(active, np.flatnonzero(np.diff(B.indptr))), "body active port order differs")
    if U_B.shape == (B.shape[1], B.shape[0]):
        U_B = U_B[:, active]
    require(R.shape == (B.shape[1], 6) and F.ndim == 2 and F.shape[0] == B.shape[1]
            and U_B.shape == (B.shape[1], len(active)) and U_F.shape == F.shape
            and all(np.isfinite(x).all() for x in (B.data, F, R, U_B, U_F)), "recovered B/F/R/U shapes or values differ")
    require(audit.get("status") == "PASS_ELASTIC_QUOTIENT_SCREEN" or audit.get("all_passed") is True,
            "accepted original-K solution audit required")
    require(not audit.get("failed_gates"), "recovered original-K solution has failed gates")
    U = np.column_stack((U_B, U_F))
    require(np.max(abs(R.T @ U), initial=0) <= 2e-10, "recovered elastic solution retains a rigid pose")
    H, e = np.zeros((B.shape[0], B.shape[0])), np.zeros((B.shape[0], F.shape[1]))
    block = np.asarray(B[active] @ U_B)
    H[np.ix_(active, active)], e[active] = block, B[active] @ U_F
    L = F.T @ U_F
    relative = lambda a: float(np.linalg.norm(a - a.T, ord=np.inf) /
                               max(np.finfo(float).tiny, np.linalg.norm(a, ord=np.inf)))
    h_reciprocal = relative(block) if len(active) else 0.
    cross_error = float(np.max(abs(e[active] - U_B.T @ F), initial=0) /
                        max(np.finfo(float).tiny, np.max(abs(e[active]), initial=0), np.max(abs(U_B.T @ F), initial=0)))
    require(h_reciprocal <= 1e-8 and relative(L) <= 1e-8 and cross_error <= 1e-8,
            "body H/e/L reciprocal recovery failed")
    report = dict(audit)
    if K is not None:
        raw = np.column_stack((B[active].T.toarray(), F))
        weights = 1. + np.arange(raw.shape[1]) % 7 / 7.
        u = U @ weights
        native_work, applied_work = float(u @ (K @ u)), float(weights @ (raw.T @ U) @ weights)
        work_error = abs(native_work - applied_work) / max(1., abs(native_work), abs(applied_work))
        require(work_error <= 1e-8 and native_work >= -1e-9, "body native virtual work/energy failed")
        report["native_virtual_work_relative_error"] = work_error
    report.update(active_ports=active.tolist(), raw_unit_columns_projected_only_for_quotient=True,
                  raw_D_W_retained=True, H_relative_reciprocity=h_reciprocal, L_relative_reciprocity=relative(L),
                  interface_body_load_reciprocity_relative=cross_error,
                  body_load_cross_terms_preserved=True, physical_response_accepted=False)
    return {"H": H, "e": e, "L": L, "D": np.asarray(B @ R), "W": R.T @ F, "audit": report}


def attach_body_load_energy(frame, old_operators, unchanged_constant_token=None):
    """Include only replaced bodies' L; unchanged constants cancel in G."""
    require(old_operators, "at least one replaced body-load operator required")
    result = frame.copy()
    result["L"] = sum((op["L"] for op in old_operators), np.zeros((frame["e"].shape[1],) * 2))
    result["energy_constant_scope"] = PARTIAL_CONSTANT
    result["unchanged_constant_token"] = unchanged_constant_token or frame["unchanged_constant_token"]
    return result


def replacement(frame, old, new):
    """Subtract the whole old contribution before adding the whole new one."""
    for name in ("H", "e", "L", "D", "W"):
        require(old[name].shape == new[name].shape, "body replacement shape differs: " + name)
        require(np.isfinite(old[name]).all() and np.isfinite(new[name]).all(), "nonfinite replacement: " + name)
    require(np.max(abs(old["D"] - new["D"]), initial=0) < 1e-8
            and np.max(abs(old["W"] - new["W"]), initial=0) < 1e-8,
            "replacement changed rigid coordinates or prescribed external body wrench")
    result = frame.copy()
    for name in ("H", "e", "L"):
        require(frame[name].shape == old[name].shape, "full port/load ordering differs: " + name)
        result[name] = frame[name] - old[name] + new[name]
    result["D"], result["W"] = frame["D"], frame["W"]
    result["physical_release"] = False
    return result


def washer_update_contract(frame, profile_packet):
    """Bind the profile packet and convert original rows to current port rows."""
    profile_packet = Path(profile_packet).resolve()
    require(profile_packet == WORKING_PROFILE.resolve()
            and sha(profile_packet / "receipt.json") == WORKING_PROFILE_RECEIPT_SHA256,
            "selected working profile receipt differs")
    profile = module(HERE / "washer-working-profile-completion.py", "member_replacement_working_profile")
    pins = {}
    profile.bind(pins, profile_packet / "receipt.json", WORKING_PROFILE_RECEIPT_SHA256)
    receipt = profile.packet(pins, profile_packet, "receipt.json")
    profile.authenticate(pins)
    require(receipt["schema"] == "washer_working_profile_preparation_receipt/v1", "washer profile receipt differs")
    update = read(profile_packet / "joint-update.json")
    require(update.get("schema") == "washer_working_profile_joint_update/v1"
            and update.get("only_scalar_axial_stiffness_changes") is True
            and update.get("D_W_or_physical_counts_changed") is False
            and update.get("physical_seats") == 8 and update.get("preload_n") == 0,
            "washer profile update domain differs")
    source_rows_path = HERE / "operators-attempt02/row-identities.json"
    require(source_rows_path in frame["source_sha256"] and source_rows_path in pins
            and frame["source_sha256"][source_rows_path] == pins[source_rows_path], "profile/source frame row binding differs")
    original_rows = read(source_rows_path)
    retained = [row for row in original_rows if row["ownership"]["second_body"] != "floor"]
    lumped_by_original = {row["row"]: i for i, row in enumerate(retained)}
    port_by_lumped = {int(original): i for i, original in enumerate(frame["joint"]["old_kept_lumped_rows"])}
    rows = []
    require(len(update["changes"]) == 4 and {r["original_row"] for r in update["changes"]} == {1850, 1851, 1886, 1887},
            "approved four top-rail ties differ")
    for change in update["changes"]:
        original = original_rows[change["original_row"]]
        require(original["row"] == change["original_row"] and original["row_id"] == change["row_id"]
                and original["ownership"] == change["source_ownership"]
                and original["ownership"]["role"] == "physical_bolt_outer_seat_tension"
                and change["new_profile_OD_ID_thickness_mm"] == [25.4, 8.3058, 2.5], "profile original row/ownership differs")
        port_row = port_by_lumped[lumped_by_original[original["row"]]]
        require(frame["joint"]["unilateral"][port_row], "top-rail axial tension-only law differs")
        rows.append({"port_row": port_row, "original_row": original["row"], "row_id": original["row_id"],
                     "old_k_n_per_mm": change["old_stiffness_n_per_mm"],
                     "new_k_n_per_mm": change["new_stiffness_n_per_mm"]})
    return {"schema": "joint_frame_scalar_seat_update/v1", "reviewed_bolt_axes": 104, "hillman_axes": 66,
            "geometry_changed": False, "preload_n": 0, "rows": rows,
            "source_sha256": {source_key(p): d for p, d in pins.items()},
            "profile_packet_directory": source_key(profile_packet),
            "profile_receipt_sha256": sha(profile_packet / "receipt.json"), "physical_release": False}


def apply_joint_update(frame, contract):
    """Apply only explicitly frozen scalar washer-seat stiffness updates."""
    if isinstance(contract, (str, Path)):
        contract = washer_update_contract(frame, contract)
    require(contract.get("schema") == "joint_frame_scalar_seat_update/v1"
            and contract.get("reviewed_bolt_axes") == 104 and contract.get("hillman_axes") == 66
            and contract.get("geometry_changed") is False and contract.get("preload_n") == 0,
            "washer update contract differs")
    require(contract.get("profile_packet_directory") == source_key(WORKING_PROFILE)
            and contract.get("profile_receipt_sha256") == WORKING_PROFILE_RECEIPT_SHA256,
            "washer update selected profile binding differs")
    profile = module(HERE / "washer-working-profile-completion.py", "member_replacement_apply_profile")
    pins = {}
    for path, digest in contract.get("source_sha256", {}).items():
        profile.bind(pins, profile.artifact(ROOT, path, absolute=True), digest)
    require(pins.get(WORKING_PROFILE / "receipt.json") == WORKING_PROFILE_RECEIPT_SHA256,
            "washer update receipt pin required")
    profile.authenticate(pins)
    joint = {name: value.copy() if isinstance(value, np.ndarray) else value for name, value in frame["joint"].items()}
    rows = contract.get("rows", [])
    require(rows and len({row["port_row"] for row in rows}) == len(rows), "unique washer-seat rows required")
    forbidden = set(np.asarray(joint["clearance_pairs"]).ravel()) | set(joint["floor_normals"]) | set(np.asarray(joint["floor_tangents"]).ravel())
    for row in rows:
        i, old_k, new_k = row["port_row"], row["old_k_n_per_mm"], row["new_k_n_per_mm"]
        require(type(i) is int and 0 <= i < len(joint["k"]) and i not in forbidden
                and np.isfinite([old_k, new_k]).all() and old_k > 0 and new_k > 0
                and abs(joint["k"][i] - old_k) <= 1e-10 * max(1., old_k), "washer-seat row/stiffness differs")
        joint["k"][i] = new_k
    result = frame.copy()
    result["joint"], result["joint_update"] = joint, contract
    return result


def load_coefficients(case, dead_load_factor):
    c = np.zeros(12)
    require(case in (*CASES, "dead-only"), "unknown external load state")
    column = 0 if case == "dead-only" else 2 * CASES.index(case)
    c[column] = dead_load_factor
    if case != "dead-only":
        c[column + 1] = 1.
    return c


def spring_energy(motion, joint, gap_scale):
    """Primal energy of the source linear, unilateral and circular-gap laws."""
    q, k, uni = np.asarray(motion), joint["k"], joint["unilateral"]
    pairs = np.asarray(joint["clearance_pairs"], dtype=int).reshape(-1, 2)
    gaps = gap_scale * joint["clearance_gaps"]
    require(q.shape == k.shape == uni.shape and len(pairs) == len(gaps), "spring energy shapes differ")
    require(np.all(k >= 0) and np.isfinite(q).all(), "invalid spring energy inputs")
    used = np.ones(len(k), dtype=bool)
    used[pairs.ravel()] = False
    scalar = np.where(uni, np.maximum(q, 0), q)
    value = .5 * float(np.sum(k[used] * scalar[used] ** 2))
    require(np.max(abs(k[pairs[:, 0]] - k[pairs[:, 1]]), initial=0) < 1e-10
            and not np.any(uni[pairs]) and len(set(pairs.ravel())) == 2 * len(pairs), "circular spring inventory differs")
    value += .5 * float(np.sum(k[pairs[:, 0]] * np.maximum(np.linalg.norm(q[pairs], axis=1) - gaps, 0) ** 2))
    return value


def complementary_energy(force, H, e, joint, gap_scale):
    """Recover the physical complementary energy independently of solver info."""
    f, k = np.asarray(force), joint["k"]
    pairs = np.asarray(joint["clearance_pairs"], dtype=int).reshape(-1, 2)
    require(f.shape == k.shape and np.asarray(e).shape == f.shape, "complementary energy dimensions differ")
    inverse = np.divide(1., k, out=np.zeros(len(k)), where=k > 0)
    return (.5 * float(f @ H @ f) - float(f @ e) + .5 * float(np.sum(inverse * f ** 2))
            + float(gap_scale * joint["clearance_gaps"] @ np.linalg.norm(f[pairs], axis=1)))


def assembled_potential(force, motion, rigid, H, e, W, L, c, joint, gap_scale=0.,
                        energy_constant_scope=COMPLETE_CONSTANT, unchanged_constant_token=None):
    """Total assembly potential, or that potential plus one shared constant.

    For a partial L, true Pi = returned Pi - chi_unchanged. Its cancellation
    is valid only at the same frozen external load and unchanged other bodies.
    H already includes timber and continuous-shaft elastic compliance.
    """
    f, q, a, c = [np.asarray(x) for x in (force, motion, rigid, c)]
    require(H.shape == (len(f), len(f)) and e.shape == (len(f), len(c))
            and W.shape == (len(a), len(c)) and L.shape == (len(c), len(c)), "assembly energy dimensions differ")
    require(energy_constant_scope in (COMPLETE_CONSTANT, PARTIAL_CONSTANT)
            and (energy_constant_scope == COMPLETE_CONSTANT or unchanged_constant_token), "unknown energy constant provenance")
    chi = .5 * float(c @ L @ c)
    cross, port = float(f @ (e @ c)), .5 * float(f @ H @ f)
    body = port - cross + chi
    connector = spring_energy(q, joint, gap_scale)
    external = float(a @ (W @ c)) + 2 * chi - cross
    potential = body + connector - external
    require(np.isfinite([chi, cross, port, body, connector, external, potential]).all(), "nonfinite assembly energy")
    complementary = complementary_energy(f, H, e @ c, joint, gap_scale)
    energy_identity_error = abs(potential + chi + complementary)
    return {"potential_nmm": potential, "body_elastic_energy_nmm": body,
            "connector_energy_nmm": connector, "external_work_nmm": external,
            "body_load_chi_nmm": chi, "interface_body_load_cross_work_nmm": cross,
            "interface_elastic_energy_nmm": port, "rigid_external_work_nmm": float(a @ (W @ c)),
            "complementary_energy_nmm": complementary, "primal_complementary_identity_error_nmm": energy_identity_error,
            "energy_constant_scope": energy_constant_scope,
            "unchanged_body_load_chi_nmm": 0. if energy_constant_scope == COMPLETE_CONSTANT else None,
            "body_elastic_energy_unchanged_offset_nmm": 0. if energy_constant_scope == COMPLETE_CONSTANT else None,
            "external_work_unchanged_offset_nmm": 0. if energy_constant_scope == COMPLETE_CONSTANT else None,
            "unchanged_constant_token": unchanged_constant_token,
            "external_coefficients": c.tolist(), "external_wrench_sha256": hashlib.sha256(np.ascontiguousarray(W @ c).tobytes()).hexdigest(),
            "joint_law_sha256": hashlib.sha256(b"".join(np.ascontiguousarray(joint[key]).tobytes() for key in
                ("k", "unilateral", "clearance_pairs", "clearance_gaps")) + np.float64(gap_scale).tobytes()).hexdigest(),
            "physical_release": False}


def energy_release(initial, final, added_sound_area_mm2):
    require(initial["energy_constant_scope"] == final["energy_constant_scope"]
            and initial["unchanged_constant_token"] == final["unchanged_constant_token"]
            and initial["external_coefficients"] == final["external_coefficients"]
            and initial["external_wrench_sha256"] == final["external_wrench_sha256"]
            and initial["joint_law_sha256"] == final["joint_law_sha256"], "fracture external load/constant identity differs")
    require(np.isfinite(added_sound_area_mm2) and added_sound_area_mm2 > 0, "positive added sound area required")
    return (initial["potential_nmm"] - final["potential_nmm"]) / added_sound_area_mm2


def solve_state(frame, case, gap_scale, initial_bearing):
    """Parent-only re-equilibrium using the unchanged existing frame laws."""
    core = compatibility()
    c = load_coefficients(case, frame["dead_load_factor"])
    force, motion, rigid, bearing, audit, history = core.solve_coupled(frame["H"], frame["D"],
        frame["e"] @ c, frame["W"] @ c, frame["joint"], initial_bearing, gap_scale)
    require(audit["all_passed"], "replacement state original physical law audit failed")
    energy = assembled_potential(force, motion, rigid, frame["H"], frame["e"], frame["W"],
        frame["L"], c, frame["joint"], gap_scale, frame["energy_constant_scope"], frame["unchanged_constant_token"])
    return {"force": force, "motion": motion, "rigid": rigid, "bearing": bearing,
            "audit": audit, "history": history, "energy": energy, "physical_release": False}


def source_check(output, preparation, member_id):
    """Parent-owned one-body reduction and source remove/reinsert proof."""
    output, preparation = Path(output).resolve(), Path(preparation).resolve()
    require(output.is_relative_to(RAW.resolve()) and output != RAW.resolve() and not output.exists(), "fresh source-check output required")
    core, pins = compatibility(), {}
    receipt = core.bind_packet(preparation, pins)
    require(receipt["status"] == "PREPARED_MEMBER_REPLACEMENT_NOT_FRAME_RESPONSE", "frozen preparation required")
    request = read(preparation / "request.json")
    require(member_id in request.get("member_ids", []), "source-check body is outside frozen request")
    authenticate(pins)
    started = time.monotonic()
    frame = load_frame()
    body = source_body(member_id)
    old = reduce_body(body["K"], body["B"], body["F"], body["R"])
    frame = attach_body_load_energy(frame, [old])
    restored = replacement(frame, old, old)
    errors = {name: float(np.max(abs(frame[name] - restored[name]), initial=0)) for name in ("H", "e", "L", "D", "W")}
    require(errors["H"] <= 1e-12 and errors["e"] <= 1e-10 and errors["L"] <= 1e-12
            and errors["D"] == 0 and errors["W"] == 0, "source-body remove/reinsert changed frame operators")
    energies = []
    with np.load(FRAME / "response.npz", allow_pickle=False) as fields:
        for disposition in frame["source_dispositions"]:
            if not disposition["accepted_force_field_exists"]:
                continue
            case, gap = disposition["case_id"], disposition["gap_scale"]
            tag = disposition["response_tag"]
            c = load_coefficients(case, frame["dead_load_factor"])
            f, q, a = [fields[tag + suffix] for suffix in ("_force_n", "_relative_motion_mm", "_rigid_scaled_mm")]
            pair = [assembled_potential(f, q, a, state["H"], state["e"], state["W"], state["L"], c,
                                       state["joint"], gap, state["energy_constant_scope"], state["unchanged_constant_token"])
                    for state in (frame, restored)]
            require(abs(pair[0]["potential_nmm"] - pair[1]["potential_nmm"]) <= 1e-7, "remove/reinsert changed assembled potential")
            energies.append({"case_id": case, "gap_scale": gap, "energy": pair[0],
                             "remove_reinsert_potential_error_nmm": abs(pair[0]["potential_nmm"] - pair[1]["potential_nmm"])})
    require(len(energies) == 12, "source accepted-state inventory differs")
    output.mkdir(parents=True, exist_ok=False)
    np.savez_compressed(output / "old-body-operators.npz", **{key: old[key] for key in ("H", "e", "L", "D", "W")})
    write(output / "known-answer.json", known_answer())
    report = {"schema": "joint_frame_member_replacement_source_check/v1", "status": "PASS_SOURCE_BODY_REMOVE_REINSERT",
              "member_id": member_id, "datum_mm": body["datum_mm"].tolist(), "physical_dofs": len(body["R"]),
              "rotation_scale_mm": ROTATION_SCALE_MM, "operator_errors": errors, "body_reduction": old["audit"],
              "states": energies, "old_body_load_full_cross_terms": True, "unchanged_constant_token": frame["unchanged_constant_token"],
              "source_remove_reinsert_is_roundtrip_only": True,
              "old_H_e_recovery_basis": "Bound native K/B/F and audited elastic quotient/virtual work; not an independent decomposition of the full global source H/e.",
              "all50_body_factorizations_performed": False, "frame_solves": 0,
              "elapsed_seconds": time.monotonic() - started, "physical_release": False}
    write(output / "check.json", report)
    pins.update(frame["source_sha256"])
    authenticate(pins)
    write(output / "receipt.json", {"schema": "joint_frame_member_replacement_receipt/v1", "status": report["status"],
          "source_sha256": {source_key(p): d for p, d in pins.items()},
          "output_sha256": {p.name: sha(p) for p in output.iterdir() if p.is_file()}, "physical_release": False})
    return report


def sweep(frame, output, cases=(*CASES, "dead-only"), gap_scales=(0., 1.)):
    """Save a separately identified frame branch using existing equilibrium.

    A profile-only gross-source branch has L_selected=0; its reported energy
    retains the unknown unchanged body-load constant. Crack branches must use
    their own frame with attached selected L and separate output directory.
    """
    output = Path(output).resolve()
    require(output.is_relative_to(RAW.resolve()) and output != RAW.resolve() and not output.exists(), "fresh frame branch output required")
    require(cases and len(set(cases)) == len(cases) and set(cases).issubset((*CASES, "dead-only"))
            and gap_scales and len(set(gap_scales)) == len(gap_scales) and set(gap_scales).issubset((0., 1.)), "requested frame state inventory differs")
    require("joint_update" in frame and "L" in frame, "explicit working profile and body-load constant scope required")
    core, vectors, states, dispositions = compatibility(), {}, [], []
    output.mkdir(parents=True, exist_ok=False)
    (output / "producer.py.snapshot").write_bytes(Path(__file__).read_bytes())
    np.savez_compressed(output / "joint-law-update.npz", k=frame["joint"]["k"], unilateral=frame["joint"]["unilateral"])
    write(output / "joint-update.json", frame["joint_update"])
    write(output / "inputs.json", {"source_frame": FRAME.relative_to(ROOT).as_posix(),
        "preparation": PREPARATION.relative_to(ROOT).as_posix(), "wood_reduction": WOOD.relative_to(ROOT).as_posix(),
        "cases": list(cases), "gap_scales": list(gap_scales), "dead_load_factor": frame["dead_load_factor"],
        "modeled_mass_kg": frame["modeled_mass_kg"], "proposal_ties_included": False, "panel_screw_component_count": 198,
        "solver_settings": core.SOLVER_SETTINGS, "elastic_duration_factor": 1.0,
        "joint_update_sha256": sha(output / "joint-update.json"), "source_frame_sha256": frame["source_frame_sha256"],
        "washer_joint_update": frame["joint_update"],
        "energy_constant_scope": frame["energy_constant_scope"], "unchanged_constant_token": frame["unchanged_constant_token"],
        "source_force_fields_relabelled": False, "physical_release": False})
    with np.load(FRAME / "response.npz", allow_pickle=False) as source:
        for case in cases:
            for gap in gap_scales:
                tag = case + ("_zero" if gap == 0 else "_gap")
                bearing = source[tag + "_bearing"].copy() if tag + "_bearing" in source else np.ones(8, dtype=bool)
                started = time.monotonic()
                try:
                    state = solve_state(frame, case, gap, bearing)
                except ValueError as error:
                    exception = str(error)
                    floor_stop = exception.startswith(core.FLOOR_FAILURE_PREFIX)
                    write(output / (tag + "-stop.json"), {"case_id": case, "gap_scale": gap, "exception": exception,
                        "accepted_force_field_exists": False, "physical_frame_failure_claim": False, "physical_release": False})
                    dispositions.append({"case_id": case, "gap_scale": gap,
                        "status": "STOP_NO_AUDITED_POSITIVE_BEARING_FLOOR_BRANCH" if floor_stop else "STOP_NUMERICAL_QUALIFICATION_OPEN",
                        "accepted_force_field_exists": False, "trace_path": tag + "-stop.json",
                        "physical_frame_failure_claim": False,
                        "stop_evidence": {"packet": output.relative_to(ROOT).as_posix(), "receipt_sha256": None,
                            "trace_path": (output / (tag + "-stop.json")).relative_to(ROOT).as_posix(),
                            "trace_sha256": sha(output / (tag + "-stop.json")), "pointer": "exception"},
                        "floor_search_summary": core.floor_failure_summary(exception) if floor_stop else None, "physical_release": False})
                    continue
                pose = frame["joint"]["Rbolt"] @ state["rigid"][300:320] - frame["joint"]["Cbolt"] @ frame["Bbolt"].T @ state["force"]
                require(np.max(abs(frame["joint"]["Kbolt"] @ pose + frame["Bbolt"].T @ state["force"])) <= .1,
                        "recovered continuous shaft nodal balance failed")
                vectors.update({tag + suffix: value for suffix, value in (
                    ("_force_n", state["force"]), ("_relative_motion_mm", state["motion"]),
                    ("_rigid_scaled_mm", state["rigid"]), ("_shaft_pose_mm", pose), ("_bearing", state["bearing"]))})
                states.append({"case_id": case, "gap_scale": gap, "audit": state["audit"], "energy": state["energy"],
                               "floor_branch_history": state["history"], "elapsed_seconds": time.monotonic() - started,
                               "physical_acceptance": False})
                dispositions.append({"case_id": case, "gap_scale": gap, "status": "PASS_CONDITIONAL_COMPATIBLE_EQUILIBRIUM",
                                     "accepted_force_field_exists": True, "response_tag": tag, "physical_release": False})
                print(tag + ": new audited profile branch", flush=True)
    np.savez_compressed(output / "response.npz", **vectors)
    status = core.PARTIAL_STATUS if len(states) != len(dispositions) else "COMPLETE_CONDITIONAL_COUPLED_FRAME_STATES"
    report = {"schema": "joint_frame_compatibility_completion/v1", "status": status, "states": states,
              "analytical_branch": "working_washer_profile_with_explicit_member_replacements",
              "case_dispositions": dispositions, "reviewed_bolt_axes": 104, "hillman_axes": 66,
              "complete_requested_state_inventory": len(dispositions) == len(cases) * len(gap_scales),
              "complete_six_case_zero_and_nominal_scope": {(s["case_id"], s["gap_scale"]) for s in states if s["case_id"] in CASES}
                  == {(case, gap) for case in CASES for gap in (0., 1.)},
              "complete_permanent_zero_and_nominal_scope": {(s["case_id"], s["gap_scale"]) for s in states if s["case_id"] == "dead-only"}
                  == {("dead-only", gap) for gap in (0., 1.)},
              "reviewed_geometry_changed": False, "numerical_goal_complete": False, "physical_release": False}
    write(output / "comparison.json", report)
    pins = {**frame["source_sha256"], Path(__file__).resolve(): sha(__file__)}
    pins.update({(ROOT / p).resolve(): d for p, d in frame["joint_update"]["source_sha256"].items()})
    authenticate(pins)
    write(output / "receipt.json", {"schema": "joint_frame_compatibility_completion_receipt/v1", "status": status,
          "source_sha256": {source_key(p): d for p, d in pins.items()},
          "output_sha256": {p.name: sha(p) for p in output.iterdir() if p.is_file()},
          "completed_states": len(states), "physical_release": False})
    return report


def known_answer():
    """Small analytic oracles; no project body or frame calculation."""
    import platform

    import scipy

    core = compatibility()
    empty = np.empty((0, 2), dtype=int)
    joint = {"k": np.array([100., 100.]), "unilateral": np.zeros(2, dtype=bool),
             "clearance_pairs": empty, "clearance_gaps": np.array([])}
    D, W, e, L, c = np.ones((2, 1)), np.array([[12.]]), np.zeros((2, 1)), np.zeros((1, 1)), np.ones(1)
    old = {"H": np.diag([.01, 0]), "e": e.copy(), "L": L.copy(), "D": D.copy(), "W": W.copy()}
    new = {**old, "H": np.diag([.03, 0])}
    frame = {"H": np.diag([.01, .02]), "D": D, "e": e, "W": W, "L": L,
             "energy_constant_scope": COMPLETE_CONSTANT, "unchanged_constant_token": None}
    restored = replacement(frame, old, old)
    require(all(np.array_equal(frame[key], restored[key]) for key in ("H", "D", "e", "W", "L")), "remove/reinsert double counting")
    energies, forces = [], []
    for state in (frame, replacement(frame, old, new)):
        f, q, a, _ = core.conic_branch(state["H"], D, e[:, 0], W[:, 0], joint["k"], joint["unilateral"],
                                      np.array([], dtype=int), empty, np.array([]))
        compliance = np.diag(state["H"]) + 1 / joint["k"]
        equivalent_k = float(np.sum(1 / compliance))
        expected_a, expected_f = 12 / equivalent_k, (12 / equivalent_k) / compliance
        require(np.max(abs(f - expected_f)) < 1e-7 and abs(a[0] - expected_a) < 1e-7, "elastic load sharing differs")
        energy = assembled_potential(f, q, a, state["H"], e, W, L, c, joint)
        require(abs(energy["potential_nmm"] + .5 * 12 ** 2 / equivalent_k) < 1e-7, "assembled potential sign/magnitude differs")
        energies.append(energy)
        forces.append(f.tolist())
    G = energy_release(*energies, 2.)
    expected_G = .5 * 12 ** 2 * (1 / (1 / .04 + 1 / .03) - 1 / (1 / .02 + 1 / .03)) / 2
    require(abs(G - expected_G) < 1e-7 and G > 0, "assembled crack energy release differs")
    shifted = []
    for state in (frame, replacement(frame, old, new)):
        f, q, a, _ = core.conic_branch(state["H"], D, e[:, 0], W[:, 0], joint["k"], joint["unilateral"],
                                      np.array([], dtype=int), empty, np.array([]))
        shifted.append(assembled_potential(f, q, a, state["H"], e, W, np.array([[9.]]), c, joint))
    require(abs(energy_release(*shifted, 2.) - G) < 1e-12
            and all(abs(x["potential_nmm"] - y["potential_nmm"] + 4.5) < 1e-12
                    for x, y in zip(shifted, energies)), "unchanged rest-body chi did not cancel")
    circular = {"k": np.array([1000., 1000.]), "unilateral": np.zeros(2, dtype=bool),
                "clearance_pairs": np.array([[0, 1]]), "clearance_gaps": np.array([.575])}
    f, q, a, _ = core.conic_branch(np.zeros((2, 2)), np.eye(2), np.zeros(2), np.array([3., 4.]),
        circular["k"], circular["unilateral"], np.array([], dtype=int), circular["clearance_pairs"], circular["clearance_gaps"])
    gap_energy = assembled_potential(f, q, a, np.zeros((2, 2)), np.zeros((2, 1)),
        np.array([[3.], [4.]]), L, c, circular, 1.)
    require(abs(gap_energy["potential_nmm"] - (-.5 * 25 / 1000 - .575 * 5)) < 1e-7,
            "circular clearance potential lost its linear gap term")
    require(spring_energy(np.array([.2, 0]), circular, 1.) == 0,
            "open circular clearance has nonzero stored energy")
    unilateral = {"k": np.array([1000.]), "unilateral": np.ones(1, dtype=bool),
                  "clearance_pairs": empty, "clearance_gaps": np.array([])}
    require(spring_energy(np.array([-1.]), unilateral, 0.) == 0
            and spring_energy(np.array([.01]), unilateral, 0.) == .05, "unilateral opening/closing energy differs")
    # Six exact gauges plus two elastic modes: raw unit port loads are unbalanced.
    R = np.vstack((np.eye(6), np.zeros((2, 6))))
    K = sparse.diags([0.] * 6 + [2., 4.])
    B = sparse.csr_matrix([[1., 0, 0, 0, 0, 0, 1., 0], [0, 1., 0, 0, 0, 0, 1., 1.]])
    F = np.zeros((8, 2))
    F[[0, 6, 7], :] = np.array([[3., 7.], [2., 4.], [1., -2.]])
    reduced = reduce_body(K, B, F, R)
    require(np.max(abs(reduced["H"] - [[.5, .5], [.5, .75]])) < 1e-12
            and np.max(abs(reduced["e"] - [[1., 2.], [1.25, 1.5]])) < 1e-12
            and np.max(abs(reduced["L"] - [[2.25, 3.5], [3.5, 9.]])) < 1e-12,
            "projected unit loads or full gravity/live cross terms differ")
    coefficients = np.array([1., 2.])
    chi = .5 * float(coefficients @ reduced["L"] @ coefficients)
    require(chi == 26.125 and np.count_nonzero(reduced["W"]) == 2, "body-load constants/raw wrench lost")
    f, q, a, _ = core.conic_branch(reduced["H"], reduced["D"], reduced["e"] @ coefficients,
        reduced["W"] @ coefficients, joint["k"], joint["unilateral"], np.array([], dtype=int), empty, np.array([]))
    loaded_energy = assembled_potential(f, q, a, reduced["H"], reduced["e"], reduced["W"],
                                      reduced["L"], coefficients, joint)
    physical_load = F @ coefficients - B.T @ f
    u = np.r_[np.zeros(6), physical_load[6:] / np.array([2., 4.])]
    x = R @ a + u
    explicit_U, explicit_work = .5 * float(u @ (K @ u)), float((F @ coefficients) @ x)
    require(np.max(abs(K @ u - physical_load)) < 1e-8
            and abs(loaded_energy["body_elastic_energy_nmm"] - explicit_U) < 1e-8
            and abs(loaded_energy["external_work_nmm"] - explicit_work) < 1e-8
            and loaded_energy["primal_complementary_identity_error_nmm"] < 1e-8,
            "explicit body-load/connector/external-work energy recovery differs")
    return {"schema": "joint_frame_member_replacement_known_answer/v1",
            "status": "PASS_ASSEMBLED_REPLACEMENT_ENERGY_KNOWN_ANSWER",
            "load_sharing_force_n": forces, "initial_potential_nmm": energies[0]["potential_nmm"],
            "final_potential_nmm": energies[1]["potential_nmm"], "G_n_per_mm": G,
            "analytic_G_n_per_mm": expected_G, "circular_gap_potential_nmm": gap_energy["potential_nmm"],
            "cross_term_body_load_chi_nmm": chi, "body_remove_reinsert_exact": True,
            "unchanged_rest_body_chi_cancellation": True,
            "explicit_body_load_potential_nmm": loaded_energy["potential_nmm"],
            "explicit_body_elastic_energy_nmm": explicit_U, "explicit_external_work_nmm": explicit_work,
            "primal_complementary_identity_error_nmm": loaded_energy["primal_complementary_identity_error_nmm"],
            "quotient": reduced["audit"],
            "runtime": {"python": platform.python_version(), "numpy": np.__version__, "scipy": scipy.__version__, "clarabel": "0.11.1"},
            "physical_release": False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("stage", choices=("prepare", "coupon", "source-check", "source-export", "profile-sweep"))
    parser.add_argument("--output", type=Path)
    parser.add_argument("--request", type=Path)
    parser.add_argument("--expected-sha256")
    parser.add_argument("--preparation", type=Path)
    parser.add_argument("--member", default="center_post_cleat_left")
    parser.add_argument("--source-check", type=Path)
    parser.add_argument("--profile-packet", type=Path)
    parser.add_argument("--case", action="append", choices=(*CASES, "dead-only"))
    parser.add_argument("--gap-scale", action="append", type=float, choices=(0., 1.))
    args = parser.parse_args()
    if args.stage == "coupon":
        print(json.dumps(known_answer(), indent=2, allow_nan=False))
    elif args.stage == "prepare":
        require(args.output is not None and args.request is not None and args.expected_sha256,
                "preparation output, request and expected SHA-256 required")
        prepare(args.output, args.request, args.expected_sha256)
    elif args.stage == "source-check":
        require(args.output is not None and args.preparation is not None, "source-check output/preparation required")
        print(json.dumps(source_check(args.output, args.preparation, args.member), indent=2))
    elif args.stage == "source-export":
        require(args.output is not None and args.source_check is not None, "source-export output and completed source-check required")
        source_export(args.output, args.member, args.source_check)
    else:
        require(args.output is not None and args.profile_packet is not None, "profile sweep output and frozen profile packet required")
        frame = apply_joint_update(load_frame(), args.profile_packet)
        frame["L"] = np.zeros((12, 12))
        sweep(frame, args.output, args.case or (*CASES, "dead-only"), args.gap_scale or (0., 1.))


if __name__ == "__main__":
    main()
