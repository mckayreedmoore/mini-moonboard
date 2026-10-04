"""Augment REVIEWED104 wood operators with physical C3D20 point ports.

Import is inert: only standard-library imports and path constants are created.
The parent owns serialization and must grant a reduction slot before calling
build(output, request: Path, expected_sha256: str). This module never launches
a native solver or CAD operation and never changes geometry or hardware.

The request has schema ``joint_frame_port_request/v1`` and these fields:
``source_operator_directory`` (repository-relative operators-attempt02),
``source_sha256`` (repository-relative file path -> SHA-256),
``old_kept_lumped_rows`` (unique, ordered indices after simple_frame.lump_floor),
``new_port_count``, and ``new_wood_port_terms``. The last field contains one
list per new port, each containing zero or more {member_id, point_mm,
direction_global_xyz} records. Directions include their signed coefficients;
an empty list has an identically zero wood map for a metal-only spring.
Call source_pin_paths() to obtain the required input paths before freezing.

Rows are ordered as requested old rows followed by new ports. Bwood maps
native displacement to port displacement; Bwood.T maps port basis loads to
native DOFs. In the existing frame convention q = Dwood a + ewood - Hwood f,
the connector force on wood is -Bwood.T f. Rotations in a are scaled by
1000 mm, so rotational columns of Dwood and Wwood retain their source units.

Parent command, from the repository root after obtaining the serialized slot:
uv run python docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/upper-corner-screw-layout/joint-frame-port-reduction.py \\
  --output docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/upper-corner-screw-layout/rawlocal/joint-frame-port-reduction/attempt01 \\
  --request REQUEST_PATH --expected-sha256 REQUEST_SHA256

Return value contains Hwood, Dwood, ewood, Wwood, Bwood, certificate and receipt.
The same arrays/maps and JSON records are saved in the fresh output directory.
Failed builds retain a STOP receipt and raise; they do not return usable arrays.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib
import json
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
RAW = HERE / "rawlocal/joint-frame-port-reduction"
FRAME = HERE / "operators-attempt02"
RESUME = HERE.parent
BASE = ROOT / "docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28"
ROTATION_SCALE_MM = 1000.0
KNEE_BODIES = (
    "base_side_left", "base_side_right",
    "knee_outer_left_inner_frame_block", "knee_outer_left_spine",
    "knee_outer_right_inner_frame_block", "knee_outer_right_spine",
)


def source_pin_paths() -> dict[str, Path]:
    """Return required source paths without reading or importing source files."""
    return {
        "operators": FRAME / "operators.npz",
        "projection": FRAME / "B.npz",
        "rows": FRAME / "row-identities.json",
        "coordinates": FRAME / "model.json",
        "operator_assessment": FRAME / "operator-assessment.json",
        "source_model": BASE / "current-springa-frame-input-adapter-attempt01/a12-rear/model.json",
        "native_stiffness": BASE / "current-frame-pure-solid-matrix-export-native-attempt01/model.sti",
        "native_dofs": BASE / "current-frame-pure-solid-matrix-export-native-attempt01/model.dof",
        "parser": BASE / "current-frame-pure-solid-export-assessment-method-attempt01/assess_matrixstorage.py",
        "helper": BASE / "current-frame-free-body-condensation-preflight-attempt01/condensation.py",
        "quotient": BASE / "current-elastic-quotient-method-preflight-attempt02/quotient_method.py",
        "refinement": BASE / "current-bordered-refinement-diagnostic-attempt01/bounded_refinement.py",
        "known_answer": BASE / "current-elastic-quotient-method-preflight-attempt02/assessment.json",
        "point_method": RESUME / "corner_frame.py",
        "accounting": RESUME / "top_corner_actions.py",
        "floor_method": RESUME / "simple_frame.py",
        "point_inverse": ROOT / "fea/wood_joint_reduced_members.py",
        "shape20": ROOT / "fea/floor_recess_mesh.py",
        "environment": ROOT / "uv.lock",
    }


def _require(condition, message):
    if not condition:
        raise ValueError("STOP: " + message)


def _sha(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _write(path, record):
    path.write_text(json.dumps(record, indent=2, allow_nan=False) + "\n")


def _repository_path(relative):
    _require(isinstance(relative, str) and relative and not Path(relative).is_absolute(),
             "source paths must be relative to ROOT")
    path = (ROOT / relative).resolve()
    _require(path.is_relative_to(ROOT), "source path escapes ROOT: " + relative)
    return path


def _authenticate_request(request, expected_sha256):
    raw = request.read_bytes()
    _require(hashlib.sha256(raw).hexdigest() == expected_sha256,
             "request SHA-256 mismatch: " + str(request))
    record = json.loads(raw)
    _require(isinstance(record, dict) and record.get("schema") == "joint_frame_port_request/v1",
             "request schema must be joint_frame_port_request/v1")
    _require(_repository_path(record.get("source_operator_directory")) == FRAME.resolve(),
             "source_operator_directory must be REVIEWED104 operators-attempt02")
    raw_pins = record.get("source_sha256")
    _require(isinstance(raw_pins, dict) and raw_pins, "source_sha256 is missing or empty")
    pins = {}
    for relative, digest in raw_pins.items():
        path = _repository_path(relative)
        _require(isinstance(digest, str) and len(digest) == 64
                 and all(c in "0123456789abcdef" for c in digest),
                 "invalid SHA-256 for " + relative)
        _require(path not in pins, "duplicate normalized source pin: " + relative)
        pins[path] = digest
    missing = [str(p.relative_to(ROOT)) for p in source_pin_paths().values() if p not in pins]
    _require(not missing, "missing source pins: " + ", ".join(missing))
    _check_pins(pins)
    kept = record.get("old_kept_lumped_rows")
    _require(isinstance(kept, list) and all(type(i) is int and i >= 0 for i in kept)
             and len(set(kept)) == len(kept), "old_kept_lumped_rows must be unique nonnegative integers")
    terms = record.get("new_wood_port_terms")
    count = record.get("new_port_count")
    _require(type(count) is int and count >= 0 and isinstance(terms, list) and len(terms) == count,
             "new_port_count must equal len(new_wood_port_terms)")
    _require(all(isinstance(port, list) for port in terms), "each new wood port must be a list of terms")
    return record, raw, pins


def _check_pins(pins):
    for path, digest in pins.items():
        _require(_sha(path) == digest, "source SHA-256 mismatch: " + str(path.relative_to(ROOT)))


def _calculate(record, pins, certificate):
    import numpy as np
    import scipy
    from scipy import sparse

    paths = source_pin_paths()
    # Existing modules have normal imports; defer them until the explicit build.
    search_path = sys.path[:]
    try:
        sys.path[:0] = [str(RESUME), str(ROOT)]
        method = importlib.import_module("corner_frame")
        accounting = importlib.import_module("top_corner_actions")
        simple = importlib.import_module("simple_frame")
        for module, role in ((method, "point_method"), (accounting, "accounting"), (simple, "floor_method")):
            _require(Path(module.__file__).resolve() == paths[role], "imported wrong " + role)
        _require(accounting.MODEL == paths["source_model"]
                 and method.NATIVE / "model.sti" == paths["native_stiffness"],
                 "shared native/source model bindings changed")
        parser = method.module(paths["parser"], "joint_frame_port_parser")
        helper = method.module(paths["helper"], "joint_frame_port_condensation")
        quotient = method.module(paths["quotient"], "joint_frame_port_quotient")
        return _reduce(record, pins, certificate, paths, method, accounting, simple,
                       parser, helper, quotient, np, sparse, scipy)
    finally:
        sys.path[:] = search_path


def _reduce(record, pins, certificate, paths, method, accounting, simple,
            parser, helper, quotient, np, sparse, scipy):
    def peak(value):
        return float(np.max(np.abs(value), initial=0.0))

    def norm_inf(value):
        return float(np.max(np.sum(np.abs(value), axis=1), initial=0.0))

    assessment = accounting.read(paths["operator_assessment"])
    _require(assessment["status"] == "PASS_UPDATED_ELASTIC_FRAME_OPERATORS", "source operators did not pass")
    for name in ("operators.npz", "B.npz", "row-identities.json", "model.json"):
        _require(pins[FRAME / name] == assessment["output_sha256"][name], "source receipt mismatch: " + name)
    for role in ("source_model", "native_stiffness", "native_dofs", "parser", "helper", "quotient", "point_inverse", "shape20"):
        path = paths[role]
        _require(pins[path] == assessment["source_sha256"][str(path.relative_to(ROOT))],
                 "source operator dependency mismatch: " + role)
    known = accounting.read(paths["known_answer"])
    _require(known["schema"] == "elastic_quotient_method_known_answer/v1"
             and known["status"] == "PASS_ELASTIC_QUOTIENT_METHOD_KNOWN_ANSWER",
             "saved quotient known answer did not pass")
    for role in ("helper", "quotient", "refinement"):
        _require(known["source_sha256"][paths[role].name] == pins[paths[role]],
                 "known-answer method pin mismatch: " + role)
    certificate["known_answer"] = {
        "source_path": str(paths["known_answer"].relative_to(ROOT)),
        "source_sha256": pins[paths["known_answer"]], "status": known["status"],
        "replayed": False,
        "max_reference_displacement_relative": known["known_cube"]["max_reference_displacement_relative"],
        "scope": "Previously authenticated native isotropic C3D20 cube quotient; no new cube run or capacity claim.",
    }
    source = parser.load_frame_source_model(accounting.MODEL)
    model = source["model"]
    frame = accounting.read(paths["coordinates"])
    names = frame["body_names"]
    _require(len(names) == 50 and names == list(source["bodies"]), "native/source rigid body order changed")
    coordinates = {int(node): np.asarray(xyz, dtype=float)
                   for node, xyz in frame["physical_node_coordinates_mm"].items()}
    labels = parser.parse_dof_file(paths["native_dofs"])
    parser.require_dof_bijection(labels, source["physical_nodes"], parser.FRAME_DOF_COUNT)
    row_for = {label: i for i, label in enumerate(labels)}
    owners = np.asarray([source["owner_by_node"][node] for node, _ in labels])
    rows = accounting.read(paths["rows"])
    _require([r["row"] for r in rows] == list(range(len(rows))), "source row order changed")
    with np.load(paths["operators"], allow_pickle=False) as data:
        raw_H, raw_D, raw_e, W, F = [data[key].copy() for key in ("H", "D", "e", "W", "F")]
    _require(raw_H.shape == (len(rows), len(rows)) and raw_D.shape == (len(rows), 300)
             and raw_e.shape == (len(rows), 12) and W.shape == (300, 12)
             and F.shape == (len(labels), 12), "source operator dimensions changed")
    _require(all(np.isfinite(v).all() for v in (raw_H, raw_D, raw_e, W, F)), "nonfinite source operator")
    old_B = sparse.load_npz(paths["projection"]).tocsr()
    _require(old_B.shape == (len(rows), len(labels)) and np.isfinite(old_B.data).all(), "source B dimensions/values changed")
    lumped_H, lumped_D, lumped_e, lumped_W, _, _, _, _, T, _ = simple.lump_floor(raw_H, raw_D, raw_e, W, rows)
    kept = np.asarray(record["old_kept_lumped_rows"], dtype=int)
    _require(not len(kept) or int(kept.max()) < len(lumped_H), "old kept index outside lumped operator")
    old_H = lumped_H[np.ix_(kept, kept)]
    old_D, old_e = lumped_D[kept], lumped_e[kept]
    n_old, n_new = len(kept), record["new_port_count"]
    B_old = (sparse.csr_matrix(T[kept]) @ old_B).tocsr()
    B_new = sparse.lil_matrix((n_new, len(labels)), dtype=float)
    expected = {body: np.zeros((n_new, 6)) for body in KNEE_BODIES}
    mapped_bodies = set()
    affine = np.array([[0.001, 0.002, -0.003], [0.004, -0.005, 0.006], [0.007, 0.008, 0.009]])
    offset = np.array([0.3, -0.2, 0.1])
    point_reports = []
    for port, terms in enumerate(record["new_wood_port_terms"]):
        for term_number, term in enumerate(terms):
            _require(isinstance(term, dict), "point term must be an object")
            body = term.get("member_id")
            _require(body in KNEE_BODIES, "point term outside six knee/body members: " + str(body))
            point = np.asarray(term.get("point_mm"), dtype=float)
            direction = np.asarray(term.get("direction_global_xyz"), dtype=float)
            _require(point.shape == direction.shape == (3,) and np.isfinite(point).all()
                     and np.isfinite(direction).all() and peak(direction) > 0, "invalid point/direction vector")
            values = method.point_terms(body, point, direction, model, coordinates, row_for)
            force, moment, virtual = np.zeros(3), np.zeros(3), 0.0
            for dof, value in values.items():
                node, axis = labels[dof]
                _require(names[int(owners[dof])] == body, "point projection crossed body ownership")
                nodal = np.zeros(3)
                nodal[axis - 1] = value
                force += nodal
                moment += np.cross(coordinates[node], nodal)
                virtual += value * (affine @ coordinates[node] + offset)[axis - 1]
                B_new[port, dof] += value
            force_error = peak(force - direction)
            moment_error = peak(moment - np.cross(point, direction))
            affine_answer = float(direction @ (affine @ point + offset))
            work_error = abs(virtual - affine_answer)
            _require(force_error <= 1e-9 * max(1.0, peak(direction))
                     and moment_error <= 1e-6 * max(1.0, peak(direction))
                     and work_error <= 1e-9 * max(1.0, abs(affine_answer)),
                     f"point force/moment/affine virtual work failed at port {port}, term {term_number}")
            center = np.mean([coordinates[node] for node in sorted(source["bodies"][body])], axis=0)
            expected[body][port] += np.r_[direction, np.cross(point - center, direction) / ROTATION_SCALE_MM]
            mapped_bodies.add(body)
            point_reports.append({"port": port, "term": term_number, "body": body,
                                  "native_nonzero_dofs": len(values), "force_error_n": force_error,
                                  "moment_about_global_origin_error_nmm": moment_error,
                                  "affine_virtual_work_error_nmm": work_error})
    B_new = B_new.tocsr()
    B_new.eliminate_zeros()
    Bwood = sparse.vstack([B_old, B_new], format="csr")
    Hwood = np.zeros((n_old + n_new, n_old + n_new))
    Dwood = np.zeros((n_old + n_new, 300))
    ewood = np.zeros((n_old + n_new, 12))
    Hwood[:n_old, :n_old], Dwood[:n_old], ewood[:n_old] = old_H, old_D, old_e
    Wwood = lumped_W.copy()
    certificate.update(native_dof_count=len(labels), body_names=names,
                       old_kept_lumped_rows=kept.tolist(), old_floor_lumped_row_count=len(T),
                       new_port_count=n_new, point_maps=point_reports,
                       metal_only_new_ports=[i for i, terms in enumerate(record["new_wood_port_terms"]) if not terms],
                       bodies=[], runtime={"python": sys.version.split()[0], "numpy": np.__version__, "scipy": scipy.__version__})
    parsed = parser.parse_upper_triangle_file(paths["native_stiffness"], len(labels),
                                             owner_by_row=owners, owner_names=names)
    parser.require_no_cross_body_coupling(parsed)
    K = parsed["matrix"]
    for body in sorted(mapped_bodies):
        body_id = names.index(body)
        dofs = np.flatnonzero(owners == body_id)
        body_labels = [labels[int(i)] for i in dofs]
        _require(all(np.array_equal(coordinates[node], source["coordinates"][node])
                     for node in source["bodies"][body]), "native K coordinates changed for " + body)
        center, R, Q = helper.rigid_basis(body_labels, coordinates, ROTATION_SCALE_MM)
        columns = slice(6 * body_id, 6 * body_id + 6)
        old_map_error = peak(B_old[:, dofs] @ R - old_D[:, columns])
        load_map_error = peak(R.T @ F[dofs] - W[columns])
        new_projection = B_new[:, dofs].tocsr()
        new_map = np.asarray(new_projection @ R)
        new_map_error = peak(new_map - expected[body])
        _require(old_map_error < 1e-8 and load_map_error < 1e-8 and new_map_error < 1e-8,
                 "rigid/physical load map authentication failed for " + body)
        Dwood[n_old:, columns] = new_map
        active = np.flatnonzero(np.diff(new_projection.indptr))
        body_report = {"body": body, "physical_dofs": len(dofs), "datum_mm": center.tolist(),
                       "active_new_ports": active.tolist(), "old_rigid_map_error": old_map_error,
                       "source_W_rigid_load_map_error_n": load_map_error, "new_point_rigid_map_error": new_map_error}
        certificate["bodies"].append(body_report)
        if not len(active):
            body_report["factorization_performed"] = False
            continue
        projection = new_projection[active]
        raw = projection.T.toarray()
        elastic = raw - Q @ (Q.T @ raw)
        body_K = K[dofs][:, dofs].tocsr()
        operator = quotient.audit_quotient_operator(body_K, R)
        body_report["operator"] = operator
        _require(operator["status"] == quotient.PASS_ELASTIC_QUOTIENT_SCREEN, body + ": rigid leakage failed")
        factor, system = helper.factor_bordered(body_K, R)
        body_report["factorization_performed"] = True
        solved = quotient.solve_quotient_chunk(factor, system, body_K, R, elastic, operator_report=operator)
        for key in ("status", "corrections", "refinement_history", "failed_gates",
                    "KKT_upper_force_residual_relative", "projected_elastic_force_residual_relative",
                    "max_gauge_R_transpose_u_mm", "rigid_identity_closure", "legacy_zero_lambda_gate"):
            if key in solved:
                body_report[key] = solved[key]
        _require(solved["status"] == quotient.PASS_ELASTIC_QUOTIENT_SCREEN, body + ": " + solved["status"])
        displacement = solved["displacement_mm"]
        cross = B_old[:, dofs] @ displacement
        contribution = np.asarray(projection @ displacement)
        new_indices = n_old + active
        Hwood[:n_old, new_indices] += cross
        Hwood[new_indices, :n_old] += cross.T
        Hwood[np.ix_(new_indices, new_indices)] += contribution
        ewood[new_indices] += displacement.T @ F[dofs]
        reciprocal = norm_inf(contribution - contribution.T) / max(norm_inf(contribution), np.finfo(float).tiny)
        _require(reciprocal <= 1e-8, body + ": new port compliance reciprocity failed")
        body_report["new_compliance_relative_reciprocity"] = reciprocal
        # Audit work against the original K with a deterministic combined load.
        weights = 1.0 + (np.arange(len(active)) % 7) / 7.0
        motion = displacement @ weights
        applied_work = float(weights @ contribution @ weights)
        strain_work = float(motion @ (body_K @ motion))
        work_error = abs(applied_work - strain_work) / max(1.0, abs(applied_work), abs(strain_work))
        _require(work_error <= 1e-8 and strain_work >= -1e-10,
                 body + ": native elastic virtual work/energy failed")
        body_report["native_work"] = {"port_work_nmm": applied_work, "strain_work_nmm": strain_work,
                                       "relative_error": work_error, "positive_energy_witness": True}
        print(body + ": reduced new point ports", flush=True)
        del factor, system, solved, displacement, raw, elastic
    scale = norm_inf(Hwood)
    reciprocal = norm_inf(Hwood - Hwood.T) / max(scale, np.finfo(float).tiny)
    _require(reciprocal <= 1e-8, "augmented wood compliance reciprocity failed")
    preservation = {
        "Hwood_old_block_exact": np.array_equal(Hwood[:n_old, :n_old], old_H),
        "Dwood_old_rows_exact": np.array_equal(Dwood[:n_old], old_D),
        "ewood_old_rows_exact": np.array_equal(ewood[:n_old], old_e),
        "Wwood_exact": np.array_equal(Wwood, W),
    }
    _require(all(preservation.values()), "old kept H/D/e/W changed")
    _require(all(np.isfinite(v).all() for v in (Hwood, Dwood, ewood, Wwood, Bwood.data)), "nonfinite output operator")
    certificate.update(old_operator_preservation=preservation,
                       compliance={"relative_reciprocity": reciprocal, "infinity_norm_mm_per_n": scale,
                                   "old_block_symmetrized": False, "full_psd_eigenvalue_check_performed": False},
                       formula={"old": "Keep specified rows from simple_frame.lump_floor; B_old = T_keep B_source.",
                                "new": "For each incident body, U_new = quotient(K,R) P_elastic B_new.T; H_old,new = B_old U_new; H_new,new = B_new U_new; e_new = U_new.T F; D_new = B_new R.",
                                "physical_force_convention": "Frame connector force on wood = -Bwood.T f; no projection repairs a physical load."})
    return {"Hwood": Hwood, "Dwood": Dwood, "ewood": ewood, "Wwood": Wwood, "Bwood": Bwood}


def build(output, request: Path, expected_sha256: str):
    """Run only when the parent has assigned the serialized reduction slot."""
    started = time.monotonic()
    request = Path(request).resolve()
    output = Path(output).resolve()
    _require(output.is_relative_to(RAW.resolve()) and output != RAW.resolve(),
             "output must be a fresh child below rawlocal/joint-frame-port-reduction")
    _require(not output.exists(), "preserve existing output: " + str(output))
    record, raw_request, pins = _authenticate_request(request, expected_sha256)
    producer = Path(__file__).resolve()
    producer_sha256 = _sha(producer)
    output.mkdir(parents=True, exist_ok=False)
    (output / "request.json").write_bytes(raw_request)
    certificate = {"schema": "joint_frame_port_certificate/v1", "status": "STOP_INCOMPLETE_REDUCTION",
                   "candidate": "compact-floor-flush-wood-joints-development", "basis": "REVIEWED104",
                   "source_sha256": {str(p.relative_to(ROOT)): h for p, h in pins.items()},
                   "request_sha256": expected_sha256, "producer_sha256": producer_sha256,
                   "native_solver_launched": False, "CAD_executed": False,
                   "geometry_changed": False, "hardware_delta": False, "six_bore_proposal_used": False,
                   "software_tests_or_reviews_run": False, "complete_joint_acceptance": False,
                   "physical_release": False,
                   "limits": ["Source gross, filled-bore elastic timber and F/W load idealizations remain conditional.",
                              "Only the six incident knee/body members are factored; every old kept contribution is reused exactly.",
                              "Metal compliance, spring laws and global physical balance belong to the parent coupled frame.",
                              "This certificate authenticates numerical reduction, not timber, hardware or complete joint resistance."]}
    receipt = {"schema": "joint_frame_port_receipt/v1", "status": "STOP_INCOMPLETE_REDUCTION",
               "request_path": str(request), "request_sha256": expected_sha256,
               "producer_sha256": producer_sha256, "source_sha256": certificate["source_sha256"]}
    try:
        result = _calculate(record, pins, certificate)
        _check_pins(pins)
        _require(_sha(request) == expected_sha256 and _sha(producer) == producer_sha256,
                 "request or producer changed during reduction")
        import numpy as np
        from scipy import sparse

        np.savez_compressed(output / "wood-operators.npz", **{k: result[k] for k in ("Hwood", "Dwood", "ewood", "Wwood")})
        sparse.save_npz(output / "Bwood.npz", result["Bwood"])
        certificate["status"] = "PASS_JOINT_FRAME_PORT_REDUCTION"
        certificate["source_unchanged"] = True
        _write(output / "certificate.json", certificate)
        receipt.update(status=certificate["status"], source_unchanged=True,
                       output_sha256={name: _sha(output / name) for name in
                                      ("request.json", "wood-operators.npz", "Bwood.npz", "certificate.json")})
        result.update(certificate=certificate, receipt=receipt)
        return result
    except Exception as error:
        certificate.update(status="STOP_JOINT_FRAME_PORT_REDUCTION", reason=str(error))
        _write(output / "certificate.json", certificate)
        receipt.update(status=certificate["status"], reason=str(error),
                       certificate_sha256=_sha(output / "certificate.json"))
        raise
    finally:
        receipt["elapsed_seconds"] = time.monotonic() - started
        _write(output / "receipt.json", receipt)


if __name__ == "__main__":
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("--output", type=Path, required=True)
    cli.add_argument("--request", type=Path, required=True)
    cli.add_argument("--expected-sha256", required=True)
    args = cli.parse_args()
    packet = build(args.output, args.request, args.expected_sha256)
    print(packet["receipt"]["status"], flush=True)
