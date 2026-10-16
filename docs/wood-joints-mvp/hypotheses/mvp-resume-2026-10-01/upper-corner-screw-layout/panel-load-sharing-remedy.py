"""Inert preparation and parent-invoked operator update for one panel screw move.

The default proposal translates the existing upper-left edge screw 214.925 mm
in global X while retaining its panel, rail receiver, laws, and 66-screw count.
``prepare_one_axis`` performs only source-bound point/geometry projection.
``build_operator_delta`` is callable by the parent with already-loaded source
matrices; it does not parse native files or run frame equilibrium itself.
"""
from __future__ import annotations

import copy
import hashlib
import importlib.machinery
import importlib.util
import json
import sys
from pathlib import Path
from types import SimpleNamespace

import numpy as np
from scipy import sparse

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
BASE = ROOT / "docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28"
WIDTH = HERE / "panel-width-operators-attempt01"
OLD = HERE / "operators-attempt02"
ROW_MAP = HERE / "rawlocal/joint-frame-action-reconciliation/profile-attempt01/source-row-map.json"
PORT_PREP = HERE / "rawlocal/joint-frame-compatibility-completion/prepare-attempt03"
PORT_REQUEST = PORT_PREP / "wood-port-request.json"
PORT_RECEIPT = PORT_PREP / "receipt.json"
NATIVE = BASE / "current-frame-pure-solid-matrix-export-native-attempt01"
DOF = NATIVE / "model.dof"
PARSER = BASE / "current-frame-pure-solid-export-assessment-method-attempt01/assess_matrixstorage.py"
CONDENSATION = BASE / "current-frame-free-body-condensation-preflight-attempt01/condensation.py"
QUOTIENT = BASE / "current-elastic-quotient-method-preflight-attempt02/quotient_method.py"
AXIS_ID = "round_panel_upper_left_edge_1"
MOVE_X_MM = -214.925
EXPECTED_POINT_MM = [-650.0, 1523.3394035191589, 2141.899800434121]
OUTPUT_ROOT = HERE / "rawlocal/current-method-corrections/panel-remedy"


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def require(condition, message):
    if not condition:
        raise ValueError("STOP: " + message)


def module(path, name):
    for folder in (ROOT, HERE.parent, HERE):
        if str(folder) not in sys.path:
            sys.path.insert(0, str(folder))
    spec = importlib.util.spec_from_file_location(name, path,
        loader=importlib.machinery.SourceFileLoader(name, str(path)))
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


def _load_static():
    """Load only cached geometry/operator identities and point interpolation."""
    panel = module(HERE / "panel-compatible-response.py", "panel_remedy_panel_sources")
    data = panel.static_sources()
    require(sha(WIDTH / "operator-assessment.json") == "47e3405e15e3d97f8666ffdead694f1a83fe6f3f76608fc81882112075e98fe0",
            "width-grain operator receipt changed")
    assessment = json.loads((WIDTH / "operator-assessment.json").read_text())
    require(assessment["status"] == "PASS_UPDATED_ELASTIC_FRAME_OPERATORS"
            and assessment["native_launch"] is False, "authenticated width-grain operators required")
    pins = dict(data.pins)
    for rel, digest in assessment["source_sha256"].items():
        path = (ROOT / rel).resolve()
        require(sha(path) == digest, "width-grain source changed: " + rel)
        pins[path] = digest
    for name, digest in assessment["output_sha256"].items():
        path = (WIDTH / name).resolve()
        require(sha(path) == digest, "width-grain operator output changed: " + name)
        pins[path] = digest
    require(sha(ROW_MAP) == "f9ae9865e80ea95db9dccd6e6cd484ce60c6bb3aa6f617ec4387e346c55a5b8d",
            "canonical-to-current row map changed")
    mapping = json.loads(ROW_MAP.read_text())
    require(sha(PORT_RECEIPT) == "0aa9a156766c7965ae722bedd2ea56ec361c187a63ae316c5ddc6e0b75e9a31d",
            "continuous-port preparation receipt changed")
    port_receipt = json.loads(PORT_RECEIPT.read_text())
    for name, digest in port_receipt["output_sha256"].items():
        path = (PORT_PREP / name).resolve()
        require(sha(path) == digest, "continuous-port preparation output changed: " + name)
        pins[path] = digest
    require(len(mapping["old_kept_lumped_rows"]) == 1592
            and len({int(x) for x in mapping["old_kept_lumped_rows"]}) == 1592,
            "1592 kept-row mapping differs")
    for path in (ROW_MAP, PORT_RECEIPT, DOF, PARSER, CONDENSATION, QUOTIENT,
                 ROOT / "docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/corner_frame.py"):
        pins[path.resolve()] = sha(path)
    parser = module(PARSER, "panel_remedy_geometry_parser")
    corner = module(ROOT / "docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/corner_frame.py",
                    "panel_remedy_corner_projection")
    source = parser.load_frame_source_model(corner.accounting.MODEL)
    model = source["model"]
    coordinates = {int(node): np.asarray(value, dtype=float)
                   for node, value in source["coordinates"].items()}
    labels = parser.parse_dof_file(DOF)
    row_for = {label: i for i, label in enumerate(labels)}
    require(len(row_for) == len(labels) == 37647, "native DOF label census differs")
    B0 = sparse.load_npz(WIDTH / "B.npz").tocsr()
    require(B0.shape == (1888, len(labels)), "cached raw panel operator shape differs")
    return SimpleNamespace(panel=panel, data=data, pins=pins, mapping=mapping, parser=parser,
                           corner=corner, model=model, coordinates=coordinates,
                           labels=labels, row_for=row_for, B0=B0)


def _row_mapping(mapping):
    raw_to_current = {}
    for item in mapping["kept_map"]:
        for raw, weight in zip(item["raw_rows"], item["weights"], strict=True):
            raw = int(raw)
            require(raw not in raw_to_current, "raw row maps more than once")
            raw_to_current[raw] = (int(item["kept_position"]), float(weight))
    return raw_to_current


def _axis_geometry(data, axis, point):
    panel = data.geometry["panels"][axis["panel"]]
    basis = np.asarray(panel["basis"], dtype=float)
    point = np.asarray(point, dtype=float)
    xy = (basis[:2] @ point).tolist()
    bounds = panel["bounds_mm"]
    radius = max(float(c["radius_mm"]) for c in next(o for o in panel["openings"]
        if o.get("axis_id") == axis["axis_id"])["cones"])
    edge_clearances = [xy[0] - bounds[0][0] - radius, bounds[0][1] - xy[0] - radius,
                       xy[1] - bounds[1][0] - radius, bounds[1][1] - xy[1] - radius]
    require(min(edge_clearances) > 0, "proposed countersink reaches the panel outline")
    target = next(o for o in panel["openings"] if o.get("axis_id") == axis["axis_id"])
    clearances = []
    for opening in panel["openings"]:
        if opening is target:
            continue
        other_xy = np.asarray(opening["xy_mm"], dtype=float)
        other_radius = max([float(opening.get("bore_radius_mm", 0.0)),
                            *(float(c["radius_mm"]) for c in opening.get("cones", []))])
        clearance = float(np.linalg.norm(np.asarray(xy) - other_xy) - radius - other_radius)
        clearances.append({"kind": opening["kind"], "axis_id": opening.get("axis_id"),
                           "center_distance_mm": float(np.linalg.norm(np.asarray(xy) - other_xy)),
                           "combined_radius_mm": radius + other_radius,
                           "surface_clearance_mm": clearance})
        require(clearance > 0, "proposed countersink overlaps a hold, LED, or screw opening")
    require(abs(float(np.dot(point, basis[2])) - float(np.dot(axis["point_mm"], basis[2]))) < 1e-7,
            "panel-normal coordinate changed")
    return {"panel_basis_global_xyz": basis.tolist(), "point_xy_original_panel_basis_mm": xy,
            "bounds_original_panel_basis_mm": bounds, "countersink_radius_mm": radius,
            "edge_clearances_after_countersink_mm": edge_clearances,
            "nearest_opening_clearance_mm": min(r["surface_clearance_mm"] for r in clearances),
            "opening_clearances": clearances}


def prepare_one_axis():
    """Return an in-memory proposal and updated raw B; no K/factor/response run."""
    src = _load_static()
    axes = copy.deepcopy(src.data.axes)
    rows = copy.deepcopy(src.data.rows)
    axis = next(a for a in axes if a["axis_id"] == AXIS_ID)
    old_point = np.asarray(axis["point_mm"], dtype=float)
    delta = np.array([MOVE_X_MM, 0., 0.])
    new_point = old_point + delta
    require(np.max(abs(new_point - EXPECTED_POINT_MM)) < 1e-9, "frozen owner-directed point differs")
    row_ids = list(axis["rows"])
    require(row_ids == [292, 293, 1484], "edge-1 screw row identities differ")
    raw_to_current = _row_mapping(src.mapping)
    require({row: raw_to_current[row][0] for row in row_ids} == {292: 276, 293: 277, 1484: 1368},
            "edge-1 retained response ports differ")
    old_record = copy.deepcopy(axis["source_axis_record"])
    new_record = copy.deepcopy(old_record)
    new_record["origin_global_xyz_mm"] = (np.asarray(old_record["origin_global_xyz_mm"]) + delta).tolist()
    new_record["translation_from_source_xyz_mm"] = delta.tolist()
    new_record["current_location_status"] = "owner_authorized_development_proposal_undrilled"
    new_record["owner_moved_axis_record"] = {"authorization_scope": "conditional panel-load-sharing remedy",
        "source_origin_global_xyz_mm": old_record["origin_global_xyz_mm"],
        "translation_global_xyz_mm": delta.tolist(), "proposed_origin_global_xyz_mm": new_record["origin_global_xyz_mm"],
        "66_axis_count_retained": True, "receiver_unchanged": True, "physical_hole_drilled": False}
    require(new_record["receiver_member"] == "base_rail_top"
            and new_record["panel_member"] == "main_upper_left", "approved panel/receiver identity differs")
    for item in axes:
        if item["axis_id"] == AXIS_ID:
            item["point_mm"] = new_point.tolist()
            item["source_axis_record"] = new_record
    changed_rows = []
    B_new = src.B0.tolil(copy=True)
    for row_id in row_ids:
        row = rows[row_id]
        own = row["ownership"]
        point_terms = {}
        for body, sign in ((own["first_body"], -1.), (own["second_body"], 1.)):
            terms = src.corner.point_terms(body, new_point, sign * np.asarray(own["direction_global_xyz"], dtype=float),
                                           src.model, src.coordinates, src.row_for)
            for dof, value in terms.items():
                point_terms[dof] = point_terms.get(dof, 0.) + value
        old_row = src.B0.getrow(row_id)
        new_row = sparse.csr_matrix((list(point_terms.values()),
                                     ([0] * len(point_terms), list(point_terms))), shape=(1, src.B0.shape[1]))
        old_generated = {}
        for body, sign in ((own["first_body"], -1.), (own["second_body"], 1.)):
            for dof, value in src.corner.point_terms(body, old_point, sign * np.asarray(own["direction_global_xyz"], dtype=float),
                                                      src.model, src.coordinates, src.row_for).items():
                old_generated[dof] = old_generated.get(dof, 0.) + value
        old_expected = sparse.csr_matrix((list(old_generated.values()),
                                          ([0] * len(old_generated), list(old_generated))), shape=old_row.shape)
        require((old_row - old_expected).nnz == 0 or np.max(abs((old_row - old_expected).data), initial=0) < 1e-10,
                "cached old B row differs from existing point_terms")
        B_new[row_id, :] = new_row
        own["point_mm"] = new_point.tolist()
        changed_rows.append({"row": row_id, "row_id": row["row_id"],
            "old_current_kept_position": raw_to_current[row_id][0], "direction_global_xyz": own["direction_global_xyz"],
            "first_body": own["first_body"], "second_body": own["second_body"],
            "point_terms_rebuilt_for_both_receivers": True})
    panel_clearance = _axis_geometry(src.data, axis, new_point)
    geometry = copy.deepcopy(src.data.geometry)
    panel_geometry = geometry["panels"][axis["panel"]]
    opening = next(o for o in panel_geometry["openings"] if o.get("axis_id") == AXIS_ID)
    opening["xy_mm"] = panel_clearance["point_xy_original_panel_basis_mm"]
    # Do not rewrite frozen_xy_mm: it remains the immutable source station.
    src.pins[Path(__file__).resolve()] = sha(__file__)
    src.pins[WIDTH / "operator-assessment.json"] = sha(WIDTH / "operator-assessment.json")
    src.pins[ROW_MAP] = sha(ROW_MAP)
    src.pins[PORT_REQUEST] = sha(PORT_REQUEST)
    src.pins[WIDTH / "model.json"] = sha(WIDTH / "model.json")
    proposal = {"schema": "panel_screw_load_sharing_move/v1", "status": "UNTESTED_PARENT_RESPONSE_REQUIRED",
        "axis_id": AXIS_ID, "panel": axis["panel"], "receiver": axis["receiver"],
        "old_interface_point_global_xyz_mm": old_point.tolist(), "new_interface_point_global_xyz_mm": new_point.tolist(),
        "front_datum_old_global_xyz_mm": old_record["origin_global_xyz_mm"],
        "front_datum_new_global_xyz_mm": new_record["origin_global_xyz_mm"],
        "translation_global_xyz_mm": delta.tolist(), "raw_rows": row_ids,
        "current_kept_positions": [raw_to_current[r][0] for r in row_ids],
        "screw_count_before_after": [66, 66], "receiver_changed": False,
        "panel_outline_changed": False, "mounting_holes_drilled": False,
        "static_geometry": panel_clearance, "receiver_point_projection": changed_rows,
        "conditional_limits": ["Global force response and all six cases remain unrun by this adapter.",
            "Hillman 42605 screw resistance, head pull-through, local fracture, and rolling-shear capacity remain unqualified.",
            "Moved panel hole remains a separately frozen development proposal; no selected-baseline geometry is changed."],
        "physical_release": False}
    return {"proposal": proposal, "B_raw": B_new.tocsr(), "rows": rows, "axes": axes,
            "mapping": src.mapping, "geometry": geometry, "source_sha256": src.pins,
            "_source": src, "_B_original": src.B0.tocsr()}


def _current_delta(raw_delta, mapping, current_rows):
    raw_to_current = _row_mapping(mapping)
    result = sparse.lil_matrix((current_rows, raw_delta.shape[1]), dtype=float)
    touched = set()
    for raw in np.flatnonzero(np.diff(raw_delta.indptr)):
        require(int(raw) in raw_to_current, "changed canonical row has no current kept port")
        pos, weight = raw_to_current[int(raw)]
        result[pos, :] += weight * raw_delta.getrow(int(raw))
        touched.add(pos)
    return result.tocsr(), sorted(touched)


def _panel_width_matrix(native, body, corner, old_model, deck_materials, *, translation_cache=None):
    """Rebuild one width-oriented panel K with the cached C3D20 method."""
    body_id = native["names"].index(body)
    dofs = np.flatnonzero(np.asarray(native["owners"]) == body_id)
    labels = [native["labels"][int(i)] for i in dofs]
    local_row = {label: i for i, label in enumerate(labels)}
    physical = native["source"]["model"]
    coordinates = native["coordinates"]
    axes_record = old_model["material_binding"]["panel_axes"][body]
    axes = {"L": axes_record["assumed_apa_direction_1_global_xyz"],
            "R": axes_record["assumed_apa_direction_2_global_xyz"],
            "T": axes_record["panel_normal_global_xyz"]}
    ii, jj, old_values, new_values = [], [], [], []
    for element in physical["physical_body_elements"][body]:
        kind, nodes, group = physical["elements"][str(element)]
        require(kind == "C3D20" and group.startswith(body + "_layer_"),
                "unexpected source panel element/layer")
        constants = deck_materials["PANEL_LAYER_" + group.rsplit("_", 1)[1]]
        positions = np.asarray([coordinates[n] for n in nodes], dtype=float)
        if translation_cache is None:
            old_element, _ = corner.brick_stiffness(positions, constants, axes)
            new_element, _ = corner.brick_stiffness(positions, [constants[1], constants[0], *constants[2:]], axes)
        else:
            # Match the frozen width producer's translated congruent element
            # reuse exactly. The caller also supplies its recorded body order.
            relative = positions - positions[0]
            key = (tuple(np.round(relative, 6).ravel()), tuple(constants))
            if key not in translation_cache:
                old_element, _ = corner.brick_stiffness(positions, constants, axes)
                new_element, _ = corner.brick_stiffness(positions, [constants[1], constants[0], *constants[2:]], axes)
                translation_cache[key] = (relative, old_element, new_element, axes)
            reference, old_element, new_element, saved_axes = translation_cache[key]
            require(np.max(abs(relative - reference)) < 1e-8 and saved_axes == axes,
                    "cached elements are not translated congruent bricks with the same material axes")
        rows = np.asarray([local_row[(node, d)] for node in nodes for d in (1, 2, 3)], dtype=int)
        ii.extend(np.repeat(rows, 60)); jj.extend(np.tile(rows, 60))
        old_values.extend(old_element.ravel()); new_values.extend(new_element.ravel())
    shape = (len(dofs), len(dofs))
    assembled_old = sparse.coo_matrix((old_values, (ii, jj)), shape=shape).tocsr()
    assembled_new = sparse.coo_matrix((new_values, (ii, jj)), shape=shape).tocsr()
    native_old = native["K"][dofs][:, dofs].tocsr()
    scale = float(np.max(abs(native_old.data), initial=0))
    mismatch = float(np.max(abs((assembled_old - native_old).data), initial=0) / max(scale, np.finfo(float).tiny))
    require(mismatch <= 1e-6, body + ": C3D20 baseline does not reproduce original native panel K")
    return dofs, assembled_new, {"body": body, "physical_dofs": len(dofs),
        "elements": len(physical["physical_body_elements"][body]),
        "original_native_K_relative_max_difference": mismatch,
        "width_constants_swapped_only": True}


def build_operator_delta(output, request):
    """Parent-only changed-point compliance update from already-loaded arrays.

    ``request`` must contain ``prepared`` from :func:`prepare_one_axis`,
    ``frame`` from the current profile adapter, and ``native_context`` from the
    parent's authenticated ``source_context``. This method uses the pinned
    quotient functions but does not parse native files or run frame response.
    """
    prepared = request["prepared"]
    frame, native = request["frame"], request["native_context"]
    require(frame["H"].shape == (3192, 3192) and frame["e"].shape == (3192, 12)
            and frame["D"].shape == (3192, 344) and frame["Bwood"].shape[0] == 3192,
            "current 3192-port frame interface differs")
    require(native["K"].shape == (37647, 37647) and native["F"].shape == (37647, 12),
            "parent native context shape differs")
    pins = dict(prepared["source_sha256"])
    for path, digest in native["source_sha256"].items():
        path = Path(path).resolve()
        require(sha(path) == digest, "parent native source context changed: " + str(path))
        pins[path] = digest
    pins[Path(__file__).resolve()] = sha(__file__)
    load_binding = request.get("case_load_comparison")
    with np.load(WIDTH / "operators.npz", allow_pickle=False) as saved:
        F_native, D_raw = saved["F"].copy(), saved["D"].copy()
    if load_binding is not None:
        load_path = ROOT / load_binding["path"]
        require(sha(load_path / "receipt.json") == load_binding["receipt_sha256"],
                "changed-axis load packet binding differs")
        load_receipt = json.loads((load_path / "receipt.json").read_text())
        require(load_receipt["schema"] == "climber_weight_load_delta_receipt/v1",
                "unsupported changed-axis load comparison")
        pins[load_path / "receipt.json"] = sha(load_path / "receipt.json")
        for name, digest in load_receipt["output_sha256"].items():
            path = (load_path / name).resolve()
            require(path.is_relative_to(load_path.resolve()) and sha(path) == digest,
                    "changed-axis load output changed: " + name)
            pins[path] = digest
        with np.load(load_path / "load-delta.npz", allow_pickle=False) as saved:
            require(np.array_equal(saved["F_original"], F_native), "comparison original load basis differs")
            F_native = saved["F_native"].copy()
        require(load_binding["comparison"] == json.loads((load_path / "load-comparison.json").read_text()),
                "changed-axis load semantics differ")
    require(np.array_equal(F_native, native["F"]), "F source differs from bound operator loads")
    corner = prepared["_source"].corner
    panel_producer = module(WIDTH / "producer.py.snapshot", "panel_remedy_existing_width_producer")
    deck_materials = panel_producer.deck_materials(NATIVE / "model.inp")
    old_model = json.loads((OLD / "model.json").read_text())
    pins[WIDTH / "producer.py.snapshot"] = sha(WIDTH / "producer.py.snapshot")
    pins[NATIVE / "model.inp"] = sha(NATIVE / "model.inp")
    pins[OLD / "model.json"] = sha(OLD / "model.json")

    Braw_old, Braw_new = prepared["_B_original"], prepared["B_raw"]
    delta_raw = (Braw_new - Braw_old).tocsr()
    delta_current, touched = _current_delta(delta_raw, prepared["mapping"], frame["Bwood"].shape[0])
    changed_raw = np.flatnonzero(np.diff(delta_raw.indptr)).tolist()
    if len(changed_raw) == 3:
        require(touched == [276, 277, 1368], "current moved panel-screw row positions differ")
    else:
        require(len(changed_raw) == 6 and touched == [278, 279, 290, 291, 1369, 1375]
                and load_binding is not None, "unsupported changed screw row inventory")
    # Confirm current Bwood retains the exact original point operators before
    # adding the moved-point delta; this catches stale or mismatched row maps.
    row_map = {raw: (item["kept_position"], weight) for item in prepared["mapping"]["kept_map"]
               for raw, weight in zip(item["raw_rows"], item["weights"], strict=True)}
    for raw in changed_raw:
        pos, weight = row_map[raw]
        require(np.max(abs((frame["Bwood"].getrow(pos) - weight * Braw_old.getrow(raw)).data), initial=0) < 1e-8,
                "current Bwood old panel row differs from cached raw source")

    delta_H = np.zeros((3192, 3192), dtype=float)
    delta_D = np.zeros((3192, 344), dtype=float)
    delta_e = np.zeros((3192, 12), dtype=float)
    report_bodies = []
    condensation = module(CONDENSATION, "panel_remedy_condensation")
    quotient = module(QUOTIENT, "panel_remedy_quotient")
    changed_bodies = {prepared["rows"][raw]["ownership"][key] for raw in changed_raw
                      for key in ("first_body", "second_body")}
    require(changed_bodies == ({"main_upper_left", "base_rail_top"} if len(changed_raw) == 3 else
            {"main_upper_left", "base_rail_top", "base_rail_service_upper_left"}),
            "bounded changed receiver inventory differs")
    panel_cache, changed_K, panel_report = {}, {}, {}
    for body in panel_producer.PANELS:
        _dofs, K_panel, audit_panel = _panel_width_matrix(native, body, corner, old_model, deck_materials,
                                                        translation_cache=panel_cache)
        if body in changed_bodies:
            changed_K[body], panel_report[body] = K_panel, audit_panel
    for body in sorted(changed_bodies):
        body_id = native["names"].index(body)
        dofs = np.flatnonzero(np.asarray(native["owners"]) == body_id)
        labels = [native["labels"][int(i)] for i in dofs]
        coordinates = {node: native["coordinates"][node] for node, _ in labels}
        _center, R, Q = condensation.rigid_basis(labels, coordinates, 1000.)
        K = changed_K.get(body, native["K"][dofs][:, dofs].tocsr())
        old_B = frame["Bwood"][:, dofs].tocsr()
        delta_B = delta_current[:, dofs].tocsr()
        active = np.flatnonzero(np.diff(delta_B.indptr))
        require(len(active) == (len(changed_raw) if body == "main_upper_left" else 3),
                body + ": changed scalar screw row count differs")
        raw_rhs = delta_B[active].T.toarray()
        elastic_rhs = raw_rhs - Q @ (Q.T @ raw_rhs)
        operator = quotient.audit_quotient_operator(K, R)
        require(operator.get("status") == quotient.PASS_ELASTIC_QUOTIENT_SCREEN,
                body + ": elastic quotient screen failed")
        factor, system = condensation.factor_bordered(K, R)
        solved = quotient.solve_quotient_chunk(factor, system, K, R, elastic_rhs,
                                               operator_report=operator)
        require(solved.get("status") == quotient.PASS_ELASTIC_QUOTIENT_SCREEN,
                body + ": changed-axis quotient solve failed: " + str(solved.get("status")))
        U = np.asarray(solved["displacement_mm"])
        cross = np.asarray(old_B @ U)
        delta_H[:, active] += cross
        delta_H[active, :] += cross.T
        delta_H[np.ix_(active, active)] += np.asarray(delta_B[active] @ U)
        delta_e[np.ix_(active, np.arange(12))] += U.T @ native["F"][dofs]
        delta_D[:, 6 * body_id:6 * body_id + 6] += np.asarray(delta_B @ R)
        raw_body_delta = delta_raw[:, dofs]
        D_raw[:, 6 * body_id:6 * body_id + 6] += np.asarray(raw_body_delta @ R)
        report_bodies.append({"body": body, "changed_current_rows": active.tolist(),
            "quotient_status": solved["status"],
            "KKT_upper_force_residual_relative": solved["KKT_upper_force_residual_relative"],
            "rigid_projected_deltaB_rhs": True,
            "full_3192_row_cross_terms_included": True})
    asym = float(np.max(abs(delta_H - delta_H.T), initial=0))
    require(asym <= 1e-8 * max(1., float(np.max(abs(delta_H), initial=0))),
            "changed-axis compliance delta is not reciprocal")

    output = Path(output).resolve()
    require(output.is_relative_to(OUTPUT_ROOT.resolve()) and output != OUTPUT_ROOT.resolve() and not output.exists(),
            "fresh panel-remedy rawlocal output directory required")
    output.mkdir(parents=True)
    (output / ".gitignore").write_text("*\n")
    (output / "producer.py.snapshot").write_bytes(Path(__file__).read_bytes())
    np.savez_compressed(output / "operator-delta.npz", dH=delta_H, dD=delta_D, de=delta_e,
                        D_raw=D_raw, F_native=F_native)
    sparse.save_npz(output / "B.npz", Braw_new)
    shared = module(HERE / "current-method-corrections.py", "panel_remedy_shared_writer")
    shared.write(output / "proposal.json", prepared["proposal"])
    shared.write(output / "row-identities.json", prepared["rows"])
    shared.write(output / "axes.json", prepared["axes"])
    shared.write(output / "source-row-map.json", prepared["mapping"])
    shared.write(output / "panel-reference-context.json", {"schema": "panel_remedy_reference_context/v1",
        "screw_axis_count": 66, "geometry": prepared["geometry"],
        **({"head_pull_through_esg": 0.50, "panel_grade_owner_report": "Group 1, sanded A-C",
            "load_comparison": load_binding["comparison"]} if load_binding is not None else {}),
        "physical_release": False})
    shared.write(output / "operator-update-audit.json", {"schema": "panel_load_sharing_operator_update/v1",
        "status": "OPERATORS_PREPARED_PARENT_RESPONSE_REQUIRED", "changed_bodies": report_bodies,
        "panel_width_reassembly": panel_report, "changed_current_rows": touched,
        "delta_H_max_abs_asymmetry": asym, "native_matrix_parsing_by_adapter": False,
        "case_load_comparison": load_binding, "changed_raw_rows": changed_raw,
        "frame_equilibrium_or_response_by_adapter": False, "complete_joint_acceptance": False,
        "physical_release": False})
    for path, digest in pins.items():
        require(sha(path) == digest, "source changed while constructing panel remedy: " + str(path))
    source_sha = {str(Path(path).resolve().relative_to(ROOT)): digest for path, digest in pins.items()}
    outputs = {path.name: sha(path) for path in output.iterdir() if path.is_file() and path.name != "receipt.json"}
    shared.write(output / "receipt.json", {"schema": "panel_load_sharing_operator_delta_receipt/v1",
        "status": "OPERATORS_PREPARED_PARENT_RESPONSE_REQUIRED", "source_sha256": source_sha,
        "output_sha256": outputs, "physical_release": False})
    return {"path": output, "source_sha256": source_sha, "output_sha256": outputs,
            "bodies": report_bodies, "physical_release": False}
