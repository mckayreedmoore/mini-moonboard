"""Parent-invoked 32-screw extension of an authenticated 66-screw study.

The owner permits eight additions per main panel only after redistribution
fails. No native file parse or frame equilibrium is launched by this module.
Existing C3D20, rigid projection and quotient helpers provide the operators.
"""
from __future__ import annotations

import copy
import json
from pathlib import Path

import numpy as np
from scipy import sparse

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
SCREW_MASS_KG = 0.015


def build(output, *, methods, frame, native, layout_source, base_operator):
    """Build cumulative operators; caller owns source parse, lock and response."""
    move = methods.module(HERE / "panel-load-sharing-remedy.py", "extra_existing_move")
    clearance = methods.module(HERE / "hardware-clearance-remedy.py", "extra_operator_reader")
    initial_H, initial_D, initial_e = (frame[k].copy() for k in ("H", "D", "e"))
    pins = dict(native["source_sha256"])
    recovery, context, _binding = clearance.apply_axis_operators(methods,
        methods.module(HERE / "joint-frame-member-replacement.py", "extra_mechanics"),
        frame, base_operator, pins)
    move.require(context["screw_axis_count"] == 66 and frame["H"].shape == (3192, 3192),
                 "the fallback must extend an authenticated 66-screw study")
    static = move._load_static()
    current_delta, _ = move._current_delta(recovery["B"] - static.B0,
        recovery["mapping"], 3192)
    Bcurrent = frame["Bwood"] + current_delta
    rawB = recovery["B"].tocsr()
    rows, axes = copy.deepcopy(recovery["rows"]), copy.deepcopy(recovery["axes"])
    geometry = copy.deepcopy(context["geometry"])
    mapping = copy.deepcopy(recovery["mapping"])
    layout_source = Path(layout_source).resolve()
    receipt_path = layout_source / "parent-freeze.json"
    if not receipt_path.exists():
        receipt_path = layout_source / "receipt.json"
    receipt = json.loads(receipt_path.read_text())
    for name, digest in receipt["output_sha256"].items():
        path = (layout_source / name).resolve()
        move.require(path.is_relative_to(layout_source) and methods.sha(path) == digest,
                     "extra-layout output changed: " + name)
        pins[path] = digest
    pins[receipt_path] = methods.sha(receipt_path)
    layout = json.loads((layout_source / "layout.json").read_text())
    additions = layout["axes"]
    move.require(len(additions) == 32 and len({a["axis_id"] for a in additions}) == 32,
                 "exactly 32 unique added axes required")
    for panel in ("main_upper_left", "main_upper_right", "main_lower_left", "main_lower_right"):
        owned = [a for a in additions if a["panel"] == panel]
        move.require(len(owned) == 8 and all(sum(a["edge"] == edge for a in owned) == 2
            for edge in ("top", "bottom", "inner", "outer")),
            "owner's two-additions-per-edge count differs")
    pins[Path(__file__).resolve()] = methods.sha(__file__)
    for path in (HERE / "current-method-corrections.py", HERE / "hardware-clearance-remedy.py",
                 HERE / "panel-load-sharing-remedy.py", move.WIDTH / "producer.py.snapshot",
                 move.NATIVE / "model.inp", move.OLD / "model.json"):
        pins[path] = methods.sha(path)
    pins.update(frame["source_sha256"])
    pins.update(static.pins)
    for rel, digest in layout.get("source_sha256", {}).items():
        path = ROOT / rel
        move.require(methods.sha(path) == digest, "extra-layout source changed: " + rel)
        pins[path] = digest
    by_axis = {a["axis_id"]: a for a in axes}
    newB = sparse.lil_matrix((96, rawB.shape[1]))
    new_k, new_uni = [], []
    Fextra = np.zeros_like(native["F"])
    for number, addition in enumerate(additions):
        template = by_axis[addition["template_axis_id"]]
        move.require(template["panel"] == addition["panel"]
            and template["receiver"] == addition["receiver"], "added-axis law template receiver differs")
        axis = copy.deepcopy(template)
        axis["axis_id"] = addition["axis_id"]
        axis["point_mm"] = addition["point_mm"]
        axis["rows"] = list(range(1888 + 3 * number, 1891 + 3 * number))
        axis["source_axis_record"]["axis_id"] = addition["axis_id"]
        axis["source_axis_record"]["origin_global_xyz_mm"] = addition["front_datum_mm"]
        axis["source_axis_record"]["current_location_status"] = "owner_authorized_extra_screw_development_proposal"
        axis["source_axis_record"]["owner_moved_axis_record"] = None
        axis["source_axis_record"]["physical_hole_drilled"] = False
        for component, old_row in enumerate(template["rows"]):
            row = copy.deepcopy(rows[old_row])
            raw = axis["rows"][component]
            row["row"] = raw
            row["row_id"] = row["row_id"].replace(template["axis_id"], axis["axis_id"])
            row["ownership"]["point_mm"] = addition["point_mm"]
            row["source_element"] = None
            row["source_group"] = "DEVELOPMENT_EXTRA_SCREW"
            row["source_inventory_row_index"] = None
            terms = {}
            own = row["ownership"]
            for body, sign in ((own["first_body"], -1.), (own["second_body"], 1.)):
                for dof, value in static.corner.point_terms(body, addition["point_mm"],
                    sign * np.asarray(own["direction_global_xyz"]), static.model,
                    static.coordinates, static.row_for).items():
                    terms[dof] = terms.get(dof, 0.) + value
            local = 3 * number + component
            newB[local, list(terms)] = list(terms.values())
            rows.append(row)
            new_k.append(row["law"]["stiffness_N_per_mm"])
            new_uni.append(component == 2)
            mapping["kept_map"].append({"raw_rows": [raw], "weights": [1.],
                                        "kept_position": 3192 + local})
        panel_geometry = geometry["panels"][addition["panel"]]
        opening = copy.deepcopy(next(o for o in panel_geometry["openings"]
            if o.get("axis_id") == template["axis_id"]))
        opening["axis_id"] = addition["axis_id"]
        opening["xy_mm"] = (np.asarray(panel_geometry["basis"][:2])
                                @ np.asarray(addition["point_mm"])).tolist()
        opening["frozen_xy_mm"] = list(opening["xy_mm"])
        panel_geometry["openings"].append(opening)
        axes.append(axis)
        # Conservative 15 g per extra screw is added explicitly. The existing
        # proportional 25 kg accessory allowance is not reduced or spent.
        mass_terms = static.corner.point_terms(addition["panel"], addition["point_mm"],
            [0., 0., -SCREW_MASS_KG * 9.81], static.model, static.coordinates, static.row_for)
        for dof, value in mass_terms.items():
            Fextra[dof, ::2] += value
    newB = newB.tocsr()
    Ftotal = native["F"] + Fextra
    H = np.pad(frame["H"], ((0, 96), (0, 96)))
    D = np.pad(frame["D"], ((0, 96), (0, 0)))
    e = np.pad(frame["e"], ((0, 96), (0, 0)))
    dW = np.zeros_like(frame["W"])
    Dnew_raw = np.zeros((96, 300))
    condensation = move.module(move.CONDENSATION, "extra_condensation")
    quotient = move.module(move.QUOTIENT, "extra_quotient")
    width = move.module(move.WIDTH / "producer.py.snapshot", "extra_width_producer")
    materials = width.deck_materials(move.NATIVE / "model.inp")
    old_model = json.loads((move.OLD / "model.json").read_text())
    audits = []
    for body_id, body in enumerate(native["names"]):
        dofs = np.flatnonzero(native["owners"] == body_id)
        Bnew_body = newB[:, dofs].tocsr()
        active = np.flatnonzero(np.diff(Bnew_body.indptr))
        if len(active) == 0:
            continue
        labels = [native["labels"][int(i)] for i in dofs]
        coordinates = {node: native["coordinates"][node] for node, _ in labels}
        _center, R, Q = condensation.rigid_basis(labels, coordinates, 1000.)
        if body.startswith("main_"):
            _dofs, K, material_audit = move._panel_width_matrix(native, body,
                static.corner, old_model, materials)
        else:
            K, material_audit = native["K"][dofs][:, dofs].tocsr(), None
        rhs = Bnew_body[active].T.toarray()
        extra_force = Fextra[dofs, 0]
        has_mass = np.max(abs(extra_force), initial=0) > 0
        if has_mass:
            rhs = np.column_stack((rhs, extra_force))
        rhs -= Q @ (Q.T @ rhs)
        audit = quotient.audit_quotient_operator(K, R)
        move.require(audit["status"] == quotient.PASS_ELASTIC_QUOTIENT_SCREEN,
                     body + ": source quotient audit failed")
        factor, system = condensation.factor_bordered(K, R)
        solved = quotient.solve_quotient_chunk(factor, system, K, R, rhs,
                                               operator_report=audit)
        move.require(solved["status"] == quotient.PASS_ELASTIC_QUOTIENT_SCREEN,
                     body + ": added-port quotient solve failed")
        U = solved["displacement_mm"][:, :len(active)]
        positions = 3192 + active
        cross = np.asarray(Bcurrent[:, dofs] @ U)
        H[:3192, positions] += cross
        H[positions, :3192] += cross.T
        H[np.ix_(positions, positions)] += np.asarray(Bnew_body[active] @ U)
        e[positions] += U.T @ Ftotal[dofs]
        D[np.ix_(positions, np.arange(6 * body_id, 6 * body_id + 6))] += np.asarray(Bnew_body[active] @ R)
        Dnew_raw[np.ix_(active, np.arange(6 * body_id, 6 * body_id + 6))] += np.asarray(Bnew_body[active] @ R)
        if has_mass:
            e[:3192, ::2] += np.asarray(Bcurrent[:, dofs] @ solved["displacement_mm"][:, -1])[:, None]
            dW[6 * body_id:6 * body_id + 6] += R.T @ Fextra[dofs]
        audits.append({"body": body, "added_scalar_rows": active.tolist(),
            "KKT_force_residual_relative": solved["KKT_upper_force_residual_relative"],
            "material_reassembly": material_audit, "status": solved["status"]})
        print(body + ": added screw operators pass", flush=True)
    move.require(np.max(abs(H - H.T)) <= 1e-8 * max(1., np.max(abs(H))),
                 "extended compliance is not reciprocal")
    output = methods.output_directory(output)
    (output / "producer.py.snapshot").write_bytes(Path(__file__).read_bytes())
    np.savez_compressed(output / "operator-delta.npz",
        dH=H - np.pad(initial_H, ((0, 96), (0, 96))),
        dD=D - np.pad(initial_D, ((0, 96), (0, 0))),
        de=e - np.pad(initial_e, ((0, 96), (0, 0))), dW=dW,
        D_raw=np.vstack((recovery["D"], Dnew_raw)), F_native=Ftotal)
    sparse.save_npz(output / "B.npz", sparse.vstack((rawB, newB), format="csr"))
    for name, value in (("axes.json", axes), ("row-identities.json", rows),
        ("source-row-map.json", mapping), ("added-screw-laws.json", {"k": new_k, "unilateral": new_uni}),
        ("panel-reference-context.json", {"schema": "panel_remedy_reference_context/v1",
            "screw_axis_count": 98, "geometry": geometry,
            "panel_grade_owner_report": "Group 1, sanded A-C",
            "head_pull_through_esg": 0.50,
            "head_esg_source": "APA D510F Table 4; publisher May 2025 webinar slide 52.",
            "primary_source": "https://www.apawood.org/data/Sites/1/documents/webinars/webinar-mastering-wsp-design-and-specification-handout.pdf",
            "physical_release": False}),
        ("operator-update-audit.json", {"schema": "extra_screw_operators/v1", "bodies": audits,
            "added_screws": 32, "modeled_added_mass_kg": 32 * SCREW_MASS_KG,
            "dead_load_convention": "Explicit added mass in all gravity RHS; original accessory factor retained.",
            "gross_filled_bore_member_stiffness_retained": True, "physical_release": False})):
        methods.write(output / name, value)
    for path, digest in pins.items():
        move.require(methods.sha(path) == digest, "source changed during added-port build: " + str(path))
    methods.write(output / "receipt.json", {"schema": "extra_screw_operator_receipt/v1",
        "source_sha256": {str(p.relative_to(ROOT)): h for p, h in pins.items()},
        "output_sha256": {p.name: methods.sha(p) for p in output.iterdir()
                          if p.is_file() and p.name != ".gitignore"},
        "status": "OPERATORS_PREPARED_PARENT_RESPONSE_REQUIRED", "physical_release": False})
    return output
