"""Parent-only changed-point update for an existing 98-screw proposal.

Use the saved C3D20 and quotient helpers to change placement without inventing
equal sharing or changing screw laws. Added screw mass follows its new point.
This module does not parse native matrices or solve a frame response.
"""
from __future__ import annotations

import copy
import json
from pathlib import Path

import numpy as np
from scipy import sparse

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]


def build(output, *, methods, frame, native, source_packet, placement_file):
    move = methods.module(HERE / "panel-load-sharing-remedy.py", "placement_old_tools")
    reader = methods.module(HERE / "hardware-clearance-remedy.py", "placement_reader")
    base_H, base_D, base_e = (frame[k].copy() for k in ("H", "D", "e"))
    pins = dict(native["source_sha256"])
    recovery, context, _ = reader.apply_axis_operators(methods,
        methods.module(HERE / "joint-frame-member-replacement.py", "placement_mechanics"),
        frame, source_packet, pins)
    move.require(context["screw_axis_count"] == 98, "placement study requires the authorized 98-screw count")
    static = move._load_static()
    mapping = recovery["mapping"]
    d_old, _ = move._current_delta(recovery["B"][:1888] - static.B0, mapping, 3192)
    Bcurrent = sparse.vstack((frame["Bwood"] + d_old, recovery["B"][1888:]), format="csr")
    changes_path = Path(placement_file).resolve()
    changes = json.loads(changes_path.read_text())
    move.require(changes["schema"] == "panel_98_axis_reposition/v1", "changed-placement schema differs")
    move.require(len(changes["axes"]) == 32, "expected 16 old and 16 added horizontal-axis moves")
    static_summary = changes["static_audit"]
    move.require(static_summary["status"] == "STATIC_GEOMETRY_PASS"
        and static_summary["total_including_unchanged_kickers"] == 98
        and static_summary["receiver_full_nominal_reach_passes"] == 32
        and static_summary["point_terms_checks_passed"] == 288,
        "changed-placement static geometry is incomplete")
    audit_path = (ROOT / static_summary["detailed_audit_path"]).resolve()
    move.require(audit_path.is_relative_to(ROOT)
        and json.loads(audit_path.read_text())["status"] == "STATIC_GEOMETRY_PASS",
        "changed-placement detailed audit differs")
    pins[audit_path] = methods.sha(audit_path)
    pins[changes_path] = methods.sha(changes_path)
    for rel, digest in changes["source_sha256"].items():
        path = ROOT / rel
        move.require(methods.sha(path) == digest, "changed-placement source differs: " + rel)
        pins[path] = digest
    pins.update(static.pins)
    pins.update(frame["source_sha256"])
    for path in (Path(__file__).resolve(), HERE / "panel-load-sharing-remedy.py",
        HERE / "current-method-corrections.py", HERE / "hardware-clearance-remedy.py",
        move.WIDTH / "producer.py.snapshot", move.NATIVE / "model.inp", move.OLD / "model.json"):
        pins[path] = methods.sha(path)
    rows, axes = copy.deepcopy(recovery["rows"]), copy.deepcopy(recovery["axes"])
    geometry = copy.deepcopy(context["geometry"])
    Braw = recovery["B"].tolil(copy=True)
    delta_raw = sparse.lil_matrix(Braw.shape)
    Fdelta = np.zeros_like(recovery["F"])
    by_axis = {a["axis_id"]: a for a in axes}
    seen = set()
    for change in changes["axes"]:
        axis = by_axis[change["axis_id"]]
        move.require(axis["axis_id"] not in seen, "duplicate changed axis")
        seen.add(axis["axis_id"])
        old = np.asarray(axis["point_mm"])
        new = np.asarray(change["new_point_mm"])
        move.require(change["panel"] == axis["panel"] and change["receiver"] == axis["receiver"],
                     "changed-placement receiver identity differs")
        move.require(np.max(abs(old - change["old_point_mm"])) < 1e-7,
                     "changed-axis old interface differs")
        shift = new - old
        move.require(abs(shift[1]) + abs(shift[2]) < 1e-7, "only reported horizontal placement changes permitted")
        for raw in axis["rows"]:
            row = rows[raw]
            own = row["ownership"]
            terms = {}
            for body, sign in ((own["first_body"], -1.), (own["second_body"], 1.)):
                for point, weight in ((old, -1.), (new, 1.)):
                    for dof, value in static.corner.point_terms(body, point,
                        sign * weight * np.asarray(own["direction_global_xyz"]),
                        static.model, static.coordinates, static.row_for).items():
                        terms[dof] = terms.get(dof, 0.) + value
            delta_row = sparse.csr_matrix((list(terms.values()),
                ([0] * len(terms), list(terms))), shape=(1, Braw.shape[1]))
            Braw[raw] = recovery["B"].getrow(raw) + delta_row
            delta_raw[raw] = delta_row
            own["point_mm"] = new.tolist()
        if axis["axis_id"].startswith("owner_extra32_"):
            for point, weight in ((old, -1.), (new, 1.)):
                force_terms = static.corner.point_terms(axis["panel"], point,
                    [0., 0., -weight * 0.015 * 9.81], static.model,
                    static.coordinates, static.row_for)
                for dof, value in force_terms.items():
                    Fdelta[dof, ::2] += value
        axis["point_mm"] = new.tolist()
        record = axis["source_axis_record"]
        record["origin_global_xyz_mm"] = (np.asarray(record["origin_global_xyz_mm"]) + shift).tolist()
        record["current_location_status"] = "owner_authorized_98_screw_placement_trial"
        record["physical_hole_drilled"] = False
        opening = next(o for o in geometry["panels"][axis["panel"]]["openings"]
            if o.get("axis_id") == axis["axis_id"])
        opening["xy_mm"] = (np.asarray(geometry["panels"][axis["panel"]]["basis"][:2]) @ new).tolist()
    Braw, delta_raw = Braw.tocsr(), delta_raw.tocsr()
    delta, touched = move._current_delta(delta_raw, mapping, 3288)
    Bnew = Bcurrent + delta
    move.require(len(touched) == 96, "changed-placement three-component census differs")
    Fnew = recovery["F"] + Fdelta
    D_raw = recovery["D"].copy()
    H, D, e = (frame[k].copy() for k in ("H", "D", "e"))
    source_packet = Path(source_packet).resolve()
    with np.load(source_packet / "operator-delta.npz") as saved:
        dW = saved["dW"].copy()
    condensation = move.module(move.CONDENSATION, "placement_condensation")
    quotient = move.module(move.QUOTIENT, "placement_quotient")
    width = move.module(move.WIDTH / "producer.py.snapshot", "placement_width")
    materials = width.deck_materials(move.NATIVE / "model.inp")
    model = json.loads((move.OLD / "model.json").read_text())
    audits = []
    for body_id, body in enumerate(native["names"]):
        dofs = np.flatnonzero(native["owners"] == body_id)
        local_delta = delta[:, dofs].tocsr()
        active = np.flatnonzero(np.diff(local_delta.indptr))
        if not len(active):
            continue
        labels = [native["labels"][int(i)] for i in dofs]
        coordinates = {node: native["coordinates"][node] for node, _ in labels}
        _center, R, Q = condensation.rigid_basis(labels, coordinates, 1000.)
        if body.startswith("main_"):
            _dofs, K, material_audit = move._panel_width_matrix(native, body,
                static.corner, model, materials)
        else:
            K, material_audit = native["K"][dofs][:, dofs].tocsr(), None
        rhs = local_delta[active].T.toarray()
        mass_rhs = Fdelta[dofs, 0]
        has_mass = np.max(abs(mass_rhs), initial=0) > 0
        if has_mass:
            rhs = np.column_stack((rhs, mass_rhs))
        rhs -= Q @ (Q.T @ rhs)
        check = quotient.audit_quotient_operator(K, R)
        move.require(check["status"] == quotient.PASS_ELASTIC_QUOTIENT_SCREEN,
                     body + ": changed-placement quotient screen failed")
        factor, system = condensation.factor_bordered(K, R)
        solved = quotient.solve_quotient_chunk(factor, system, K, R, rhs, operator_report=check)
        move.require(solved["status"] == quotient.PASS_ELASTIC_QUOTIENT_SCREEN,
                     body + ": changed-placement RHS solve failed")
        U = solved["displacement_mm"][:, :len(active)]
        cross = np.asarray(Bcurrent[:, dofs] @ U)
        H[:, active] += cross
        H[active] += cross.T
        H[np.ix_(active, active)] += np.asarray(local_delta[active] @ U)
        e[active] += U.T @ recovery["F"][dofs]
        D[:, 6 * body_id:6 * body_id + 6] += np.asarray(local_delta @ R)
        D_raw[:, 6 * body_id:6 * body_id + 6] += np.asarray(delta_raw[:, dofs] @ R)
        if has_mass:
            e[:, ::2] += np.asarray(Bnew[:, dofs] @ solved["displacement_mm"][:, -1])[:, None]
            dW[6 * body_id:6 * body_id + 6] += R.T @ Fdelta[dofs]
        audits.append({"body": body, "changed_rows": active.tolist(),
            "KKT_force_residual_relative": solved["KKT_upper_force_residual_relative"],
            "material_reassembly": material_audit, "status": solved["status"]})
        print(body + ": changed-placement operators pass", flush=True)
    move.require(np.max(abs(H - H.T)) < 1e-8 * max(1., np.max(abs(H))), "placement compliance is not reciprocal")
    output = methods.output_directory(output)
    (output / "producer.py.snapshot").write_bytes(Path(__file__).read_bytes())
    np.savez_compressed(output / "operator-delta.npz",
        dH=H - np.pad(base_H, ((0, 96), (0, 96))),
        dD=D - np.pad(base_D, ((0, 96), (0, 0))),
        de=e - np.pad(base_e, ((0, 96), (0, 0))), dW=dW,
        D_raw=D_raw, F_native=Fnew)
    sparse.save_npz(output / "B.npz", Braw)
    context["geometry"] = geometry
    for name, value in (("axes.json", axes), ("row-identities.json", rows),
        ("source-row-map.json", mapping), ("panel-reference-context.json", context),
        ("proposal.json", changes), ("operator-update-audit.json", {"bodies": audits,
            "unchanged_98_screw_count": True, "unchanged_spring_laws": True,
            "additional_mass_positions_updated": True, "physical_release": False})):
        methods.write(output / name, value)
    (output / "added-screw-laws.json").write_bytes((source_packet / "added-screw-laws.json").read_bytes())
    for path, digest in pins.items():
        move.require(methods.sha(path) == digest, "source changed during placement build: " + str(path))
    methods.write(output / "receipt.json", {"schema": "panel_placement_operator_receipt/v1",
        "source_sha256": {str(p.relative_to(ROOT)) if p.is_relative_to(ROOT) else str(p): h
                          for p, h in pins.items()},
        "output_sha256": {p.name: methods.sha(p) for p in output.iterdir()
                          if p.is_file() and p.name != ".gitignore"},
        "status": "OPERATORS_PREPARED_PARENT_RESPONSE_REQUIRED", "physical_release": False})
    return output
