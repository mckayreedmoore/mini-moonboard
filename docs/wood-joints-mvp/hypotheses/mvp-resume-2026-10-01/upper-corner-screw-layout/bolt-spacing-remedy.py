"""Inert parent-invoked operator update for the six structural bolt shifts.

``prepare_bolt_spacing`` does source-bound point projection only. The parent
may call ``build_operator_delta`` with an authenticated current frame and its
already-loaded native context; this adapter does not parse native matrices or
run a frame response. A receipt-bound 66- or 98-panel-axis operator packet can
be composed into the same cumulative delta.
"""
from __future__ import annotations

import copy
import hashlib
import importlib.machinery
import importlib.util
import json
import shutil
import sys
from pathlib import Path

import numpy as np
from scipy import sparse

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
BASE = ROOT / "docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28"
PANEL = HERE / "panel-load-sharing-remedy.py"
WIDTH = HERE / "panel-width-operators-attempt01"
POINT_MAP = HERE / "rawlocal/current-method-corrections/receiver-remedy/attempt02/frozen-point-map.json"
SPACING_SCREEN = HERE / "rawlocal/current-method-corrections/receiver-remedy/attempt02/spacing-washer-end-static.json"
DEFAULT_PANEL_PACKET = HERE / "rawlocal/current-method-corrections/panel-remedy/one-axis01"
OUTPUT_ROOT = HERE / "rawlocal/current-method-corrections/bolt-spacing-remedy"
NATIVE = BASE / "current-frame-pure-solid-matrix-export-native-attempt01"
DOF = NATIVE / "model.dof"
PARSER = BASE / "current-frame-pure-solid-export-assessment-method-attempt01/assess_matrixstorage.py"
CONDENSATION = BASE / "current-frame-free-body-condensation-preflight-attempt01/condensation.py"
QUOTIENT = BASE / "current-elastic-quotient-method-preflight-attempt02/quotient_method.py"

EXPECTED_PANEL_SCREW_COUNTS = {66, 98}
CURRENT_PORT_COUNTS = {3192, 3288}
EXPECTED_CHANGED_BODIES = {
    "base_post_outer_left", "base_floor_left", "base_post_outer_right",
    "base_floor_right", "base_side_left", "bottom_outer_left_cleat",
}
EXPECTED_ROW_IDS = {
    "rail_front_bolt_left_1/wood-interface", "rail_front_bolt_left_2/wood-interface",
    "rail_front_bolt_right_1/wood-interface", "rail_front_bolt_right_2/wood-interface",
    "rail_front_bolt_left_1/outer-seat-axial-tie", "rail_front_bolt_left_2/outer-seat-axial-tie",
    "rail_front_bolt_right_1/outer-seat-axial-tie", "rail_front_bolt_right_2/outer-seat-axial-tie",
    "bottom_outer/clip_horizontal_bottom_left_1/side_1/plane-11",
    "bottom_outer/clip_horizontal_bottom_left_1/side_2/plane-12",
    "bottom_outer/clip_horizontal_bottom_left_1/side_1/outer-seat-axial-tie",
    "bottom_outer/clip_horizontal_bottom_left_1/side_2/outer-seat-axial-tie",
}


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def require(condition, message):
    if not condition:
        raise ValueError("STOP: " + message)


def module(path, name):
    for folder in (ROOT, HERE.parent, HERE):
        if str(folder) not in sys.path:
            sys.path.insert(0, str(folder))
    spec = importlib.util.spec_from_file_location(
        name, path, loader=importlib.machinery.SourceFileLoader(name, str(path)))
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


def _pin_source_tree(pins, source_map):
    for rel, digest in source_map.items():
        path = (ROOT / rel).resolve()
        require(path.is_file() and sha(path) == digest, "frozen point-map source changed: " + rel)
        pins[path] = digest


def _load_packet(path):
    """Load and authenticate a parent/base packet without invoking its runner."""
    path = Path(path).resolve()
    receipt_path = path / "receipt.json"
    require(receipt_path.is_file(), "base operator packet must have a receipt")
    receipt = json.loads(receipt_path.read_text())
    status = str(receipt.get("status", ""))
    require((not status or any(token in status for token in ("PREPARED", "UNTESTED", "RESPONSE_REQUIRED")))
            and not any(token in status for token in ("ACCEPTED", "COMPLETE", "RELEASED")),
            "base operator packet is not a prepared, unaccepted proposal")
    require(isinstance(receipt.get("output_sha256"), dict) and receipt["output_sha256"],
            "base packet has no output hash closure")
    for name, digest in receipt.get("output_sha256", {}).items():
        target = path / name
        require(target.is_file() and sha(target) == digest, "base packet output changed: " + name)
    return path, receipt


def _base_bundle(src, panel_packet=None):
    if panel_packet is None:
        with np.load(WIDTH / "operators.npz", allow_pickle=False) as saved:
            D_raw, F_native = saved["D"].copy(), saved["F"].copy()
        return {
            "B": src.B0.tocsr(), "D_raw": D_raw, "F_native": F_native,
            "dH": None, "dD": None, "de": None, "dW": np.zeros((344, 12)),
            "axes": copy.deepcopy(src.data.axes), "rows": copy.deepcopy(src.data.rows),
            "mapping": copy.deepcopy(src.mapping), "geometry": copy.deepcopy(src.data.geometry),
            "panel_context": {"schema": "panel_remedy_reference_context/v1", "screw_axis_count": 66,
                "geometry": copy.deepcopy(src.data.geometry), "physical_release": False},
            "base_audit": None,
            "panel_count": 66, "packet_path": None, "packet_receipt": None,
            "added_screw_laws_path": None,
        }

    packet_path, receipt = _load_packet(panel_packet)
    with np.load(packet_path / "operator-delta.npz", allow_pickle=False) as saved:
        operator = {key: saved[key].copy() for key in saved.files}
    panel_context = json.loads((packet_path / "panel-reference-context.json").read_text())
    audit_path = packet_path / "operator-update-audit.json"
    require(audit_path.is_file(), "base operator packet must identify its changed receiver bodies")
    base_audit = json.loads(audit_path.read_text())
    added_screw_laws_path = packet_path / "added-screw-laws.json"
    bundle = {
        "B": sparse.load_npz(packet_path / "B.npz").tocsr(),
        "D_raw": operator["D_raw"], "F_native": operator["F_native"],
        "dH": operator["dH"], "dD": operator["dD"], "de": operator["de"],
        "dW": operator.get("dW", np.zeros((344, 12))),
        "axes": json.loads((packet_path / "axes.json").read_text()),
        "rows": json.loads((packet_path / "row-identities.json").read_text()),
        "mapping": json.loads((packet_path / "source-row-map.json").read_text()),
        "geometry": panel_context["geometry"], "panel_context": panel_context,
        "base_audit": base_audit,
        "panel_count": panel_context["screw_axis_count"],
        "packet_path": packet_path, "packet_receipt": receipt,
        "added_screw_laws_path": added_screw_laws_path if added_screw_laws_path.is_file() else None,
    }
    require(bundle["panel_count"] in EXPECTED_PANEL_SCREW_COUNTS,
            "base packet panel-screw count must be 66 or the conditional 98")
    require(bundle["B"].shape[0] in (1888, 1984), "base raw row census must be 1888 or 1984")
    require(bundle["B"].shape[1] == src.B0.shape[1], "base packet native DOF count differs")
    require(bundle["D_raw"].shape == (bundle["B"].shape[0], 300), "base raw rigid operator shape differs")
    require(bundle["F_native"].shape == (src.B0.shape[1], 12), "base native load matrix shape differs")
    require(bundle["B"].shape[0] == len(bundle["rows"]), "base raw row identities differ")
    require(len(bundle["axes"]) == bundle["panel_count"], "base panel axis metadata census differs")
    require(bundle["mapping"]["old_kept_lumped_rows"] == src.mapping["old_kept_lumped_rows"],
            "base mapping changed the frozen 1592 original kept positions")
    n = bundle["dH"].shape[0]
    require(n in CURRENT_PORT_COUNTS and bundle["dH"].shape == (n, n)
            and bundle["dD"].shape == (n, 344) and bundle["de"].shape == (n, 12),
            "base operator packet current-port delta shapes differ")
    require(bundle["dW"].shape == (344, 12), "base operator packet dW shape differs")
    audit_bodies = bundle["base_audit"].get("changed_bodies", bundle["base_audit"].get("bodies"))
    require(isinstance(audit_bodies, list), "base audit does not enumerate affected bodies")
    bundle["audit_bodies"] = {item["body"] if isinstance(item, dict) else str(item)
                              for item in audit_bodies}
    if bundle["panel_count"] == 66:
        require(bundle["audit_bodies"].isdisjoint(EXPECTED_CHANGED_BODIES),
                "66-axis base and six bolt moves change the same body; missing mixed cross terms")
    return bundle


def _row_mapping(mapping):
    raw_to_current = {}
    for item in mapping["kept_map"]:
        for raw, weight in zip(item["raw_rows"], item["weights"], strict=True):
            raw = int(raw)
            require(raw not in raw_to_current, "raw row maps more than once")
            raw_to_current[raw] = (int(item["kept_position"]), float(weight))
    return raw_to_current


def _point_row(point_terms, body_points, direction, first, second, model, coordinates, row_for):
    result = {}
    for item in body_points:
        body = item["body"]
        sign = -1.0 if body == first else 1.0 if body == second else None
        require(sign is not None, "point map names a body outside row ownership")
        point = item["old_physical_point_mm"]
        for dof, value in point_terms(body, point, sign * np.asarray(direction, dtype=float),
                                      model, coordinates, row_for).items():
            result[dof] = result.get(dof, 0.0) + value
    return result


def _sparse_row(terms, columns):
    if not terms:
        return sparse.csr_matrix((1, columns), dtype=float)
    ids = list(terms)
    return sparse.csr_matrix((list(terms.values()), ([0] * len(ids), ids)), shape=(1, columns))


def prepare_bolt_spacing(panel_operator=None):
    """Freeze the six-axis point delta using saved geometry and point maps only."""
    panel = module(PANEL, "bolt_spacing_panel_static_sources")
    src = panel._load_static()
    packet = json.loads(POINT_MAP.read_text())
    spacing = json.loads(SPACING_SCREEN.read_text())
    require(packet.get("schema") == "receiver_bolt_spacing_frozen_points/v1",
            "receiver point-map schema differs")
    require(spacing.get("schema") == "bolt_spacing_washer_edge_static_screen/v1",
            "bolt spacing/washer static screen schema differs")
    require(len(packet.get("axes", [])) == 6, "expected exactly six shifted structural axes")
    _pin_source_tree(src.pins, packet["source_pins"])
    _pin_source_tree(src.pins, spacing["source_pins"])
    src.pins[POINT_MAP.resolve()] = sha(POINT_MAP)
    src.pins[SPACING_SCREEN.resolve()] = sha(SPACING_SCREEN)
    src.pins[Path(__file__).resolve()] = sha(__file__)
    bundle = _base_bundle(src, panel_operator)
    if bundle["packet_path"] is not None:
        _pin_source_tree(src.pins, bundle["packet_receipt"].get("source_sha256", {}))
        receipt_path = bundle["packet_path"] / "receipt.json"
        src.pins[receipt_path] = sha(receipt_path)
        for name in bundle["packet_receipt"]["output_sha256"]:
            output_path = bundle["packet_path"] / name
            src.pins[output_path] = sha(output_path)
    mapping = bundle["mapping"]
    raw_to_current = _row_mapping(mapping)
    rows = copy.deepcopy(bundle["rows"])
    axes = copy.deepcopy(bundle["axes"])
    delta_raw = sparse.lil_matrix(bundle["B"].shape, dtype=float)
    row_audit = []
    seen_raw, seen_ids, bodies = set(), set(), set()

    for axis in packet["axes"]:
        axis_id = axis["axis_id"]
        old_axis = np.asarray(axis["source_axis_point_xyz_mm"], dtype=float)
        new_axis = np.asarray(axis["proposed_axis_point_xyz_mm"], dtype=float)
        require(old_axis.shape == new_axis.shape == (3,), axis_id + ": invalid axis points")
        require(np.max(np.abs(new_axis - old_axis)) <= 3.251,
                axis_id + ": movement exceeds the frozen 3.25 mm maximum transverse shift")
        require(len(axis["rows"]) == 3, axis_id + ": expected two lateral and one axial row")
        body_set = set(axis["receiver_member_ids"])
        require(len(body_set) == 2, axis_id + ": expected two supported timber receivers")
        bodies.update(body_set)
        for spec in axis["rows"]:
            raw = int(spec["operator_row"])
            row_id = spec["row_id"]
            require(raw not in seen_raw and row_id in EXPECTED_ROW_IDS,
                    "unexpected or repeated moved structural row: " + row_id)
            seen_raw.add(raw)
            seen_ids.add(row_id)
            require(raw in raw_to_current, row_id + ": moved row is absent from current mapping")
            require(raw < len(rows) and rows[raw]["row_id"] == row_id,
                    row_id + ": row identity does not match the frozen operator row")
            saved = rows[raw]
            own = saved["ownership"]
            first, second = own["first_body"], own["second_body"]
            direction = np.asarray(spec["direction_global_xyz"], dtype=float)
            require({first, second} == {item["body"] for item in spec["body_points"]},
                    row_id + ": body-specific physical-point coverage differs")
            require({first, second}.issubset(body_set), row_id + ": receiver body differs from its axis")
            old_terms = _point_row(src.corner.point_terms, spec["body_points"], direction,
                                   first, second, src.model, src.coordinates, src.row_for)
            original = src.B0.getrow(raw)
            expected_old = _sparse_row(old_terms, src.B0.shape[1])
            old_error = float(np.max(np.abs((original - expected_old).data), initial=0.0))
            require(old_error <= 1e-8, row_id + ": saved B0 row does not match the receiver packet old points")

            delta_terms = {}
            per_body = []
            for item in spec["body_points"]:
                body = item["body"]
                sign = -1.0 if body == first else 1.0
                old = np.asarray(item["old_physical_point_mm"], dtype=float)
                new = np.asarray(item["new_physical_point_mm"], dtype=float)
                require(old.shape == new.shape == (3,), row_id + ": invalid body point")
                for point, weight in ((old, -1.0), (new, 1.0)):
                    for dof, value in src.corner.point_terms(
                            body, point, sign * weight * direction,
                            src.model, src.coordinates, src.row_for).items():
                        delta_terms[dof] = delta_terms.get(dof, 0.0) + value
                bodies.add(body)
                per_body.append({"body": body, "old_physical_point_mm": old.tolist(),
                    "new_physical_point_mm": new.tolist(),
                    "old_mapping": item["old_point_map"], "new_mapping": item["new_point_map"]})
            delta_row = _sparse_row(delta_terms, src.B0.shape[1])
            delta_raw[raw, :] = delta_row
            if "physical_point_updates" in saved:
                require(saved["physical_point_updates"].get("source_sha256") == sha(POINT_MAP),
                        row_id + ": a prior physical-point update is already present")
            saved["physical_point_updates"] = {
                "source": POINT_MAP.relative_to(ROOT).as_posix(),
                "source_sha256": sha(POINT_MAP), "axis_id": axis_id,
                "operator_rule": "Bnew=Bold+Phi(new_physical_point,body,direction)-Phi(old_physical_point,body,direction); saved virtual reference is retained",
                "virtual_reference_point_mm_preserved": own["point_mm"],
                "body_points": per_body,
            }
            row_audit.append({"operator_row": raw, "row_id": row_id,
                "current_port": raw_to_current[raw][0], "axis_id": axis_id,
                "direction_global_xyz": direction.tolist(), "old_B0_point_projection_max_error": old_error,
                "body_points": per_body})

    require(seen_ids == EXPECTED_ROW_IDS and len(seen_raw) == 18,
            "the six-axis map must cover the frozen eighteen structural point rows")
    require(bodies == EXPECTED_CHANGED_BODIES, "changed receiver set differs from the six approved timber bodies")
    require(bundle["panel_count"] in EXPECTED_PANEL_SCREW_COUNTS,
            "panel screw-axis count must remain the packet's 66 or conditional 98")

    # All six changes are structural bolts. The panel-screw axes and panel
    # outlines therefore remain byte-identical to the selected base packet.
    proposal = {"schema": "bolt_spacing_remedy_proposal/v1",
        "status": "UNTESTED_PARENT_RESPONSE_REQUIRED", "source_geometry": POINT_MAP.relative_to(ROOT).as_posix(),
        "source_geometry_sha256": sha(POINT_MAP), "changed_structural_axes": packet["axes"],
        "frozen_geometry_checks": packet["checks"],
        "washer_edge_neighbor_detail_screen": {"source": SPACING_SCREEN.relative_to(ROOT).as_posix(),
            "source_sha256": sha(SPACING_SCREEN),
            "status": spacing["status"],
            "front_pair_46mm": {"pair_geometry": spacing["front_pair_46mm_proposal"]["pair_geometry"],
                "member_edges_and_ends": spacing["front_pair_46mm_proposal"]["member_edges_and_ends"],
                "washer": spacing["front_pair_46mm_proposal"]["washer"],
                "front_bolt_neighbor_axis_lines": spacing["front_pair_46mm_proposal"]["front_bolt_neighbor_axis_lines"],
                "nearest_line_gate": spacing["front_pair_46mm_proposal"]["nearest_line_gate"]},
            "bottom_pair_36mm": {"member_pair_by_axis": spacing["bottom_pair_36mm_proposal"]["member_pair_by_axis"],
                "host_edge_end_basis": spacing["bottom_pair_36mm_proposal"]["host_edge_end_basis"],
                "hardware": spacing["bottom_pair_36mm_proposal"]["hardware"],
                "pitch_mm": spacing["bottom_pair_36mm_proposal"]["pitch_mm"],
                "pair_washer_edge_gap_at_max_OD_mm": spacing["bottom_pair_36mm_proposal"]["pair_washer_edge_gap_at_max_OD_mm"],
                "neighbor_axis_lines": spacing["bottom_pair_36mm_proposal"]["neighbor_axis_lines"],
                "closest_neighbor_axis": spacing["bottom_pair_36mm_proposal"]["closest_neighbor_axis"],
                "end_edge_limit": spacing["bottom_pair_36mm_proposal"]["end_edge_limit"]},
            "limits": spacing["limits"]},
        "changed_raw_rows": sorted(seen_raw), "changed_row_count": len(seen_raw),
        "changed_receivers": sorted(bodies), "panel_screw_axis_count": bundle["panel_count"],
        "panel_screw_count_changed_by_this_adapter": False,
        "conditional_extra_panel_screw_axes_in_base_packet": max(0, bundle["panel_count"] - 66),
        "panel_fasteners_added_by_this_adapter": 0,
        "through_bolts_or_inserts_added": False, "custom_steel_added": False,
        "panel_outline_changed": False, "climbing_surface_changed": False,
        "mounting_holes_drilled": False, "abandoned_holes_created": False,
        "native_matrix_parse_by_adapter": False, "frame_response_by_adapter": False,
        "structural_acceptance": False, "physical_release": False}

    return {"proposal": proposal, "B_delta_raw": delta_raw.tocsr(), "B_base": bundle["B"],
        "D_raw_base": bundle["D_raw"], "F_native_base": bundle["F_native"],
        "dH_base": bundle["dH"], "dD_base": bundle["dD"], "de_base": bundle["de"],
        "dW_base": bundle["dW"], "panel_context": bundle["panel_context"],
        "added_screw_laws_path": bundle["added_screw_laws_path"],
        "rows": rows, "axes": axes, "mapping": mapping, "geometry": bundle["geometry"],
        "panel_count": bundle["panel_count"], "base_packet": bundle["packet_path"],
        "base_receipt": bundle["packet_receipt"], "base_audit": bundle["base_audit"],
        "base_audit_bodies": bundle.get("audit_bodies", set()),
        "row_audit": row_audit,
        "source_sha256": src.pins, "_source": src}


def _pad_vector_rows(array, rows, columns, label):
    array = np.asarray(array, dtype=float)
    require(array.ndim == 2 and array.shape[1] == columns and array.shape[0] <= rows,
            label + ": incompatible shape")
    if array.shape[0] == rows:
        return array.copy()
    result = np.zeros((rows, columns), dtype=float)
    result[:array.shape[0]] = array
    return result


def _pad_square(array, size, label):
    array = np.asarray(array, dtype=float)
    require(array.ndim == 2 and array.shape[0] == array.shape[1] and array.shape[0] <= size,
            label + ": incompatible shape")
    if array.shape[0] == size:
        return array.copy()
    result = np.zeros((size, size), dtype=float)
    result[:array.shape[0], :array.shape[1]] = array
    return result


def _mapped_delta(raw_delta, mapping, current_rows):
    raw_to_current = _row_mapping(mapping)
    result = sparse.lil_matrix((current_rows, raw_delta.shape[1]), dtype=float)
    touched = set()
    for raw in np.flatnonzero(np.diff(raw_delta.indptr)):
        require(int(raw) in raw_to_current, "changed raw row has no current port: " + str(raw))
        position, weight = raw_to_current[int(raw)]
        require(0 <= position < current_rows, "changed raw row maps outside the current frame")
        result[position, :] += weight * raw_delta.getrow(int(raw))
        touched.add(position)
    return result.tocsr(), sorted(touched)


def _verify_mapped_Bwood(raw_B, mapping, current_Bwood, label):
    """Check all receipt-mapped raw rows against a caller's current Bwood."""
    for item in mapping["kept_map"]:
        position = int(item["kept_position"])
        expected = sparse.csr_matrix((1, raw_B.shape[1]), dtype=float)
        for raw, weight in zip(item["raw_rows"], item["weights"], strict=True):
            raw = int(raw)
            require(0 <= raw < raw_B.shape[0], label + ": raw map outside B")
            expected += float(weight) * raw_B.getrow(raw)
        require(0 <= position < current_Bwood.shape[0], label + ": mapped current row outside frame")
        actual = current_Bwood.getrow(position)
        error = float(np.max(np.abs((actual - expected).data), initial=0.0))
        require(error < 1e-8, label + ": frame Bwood is not the receipt-mapped base B at row " + str(position))


def build_operator_delta(output, request):
    """Build cumulative current-frame deltas from already-loaded parent arrays.

    ``request`` contains ``prepared``, ``frame`` and ``native_context``. The
    ``frame[H,D,e]`` are the original horizontal-grain operators, zero-padded
    to 3288 when needed; the base packet deltas are added here. With a 98-axis
    base, ``frame[Bwood]`` must already carry its full updated raw-point map so
    changed bolt compliance includes every new port. No native parse,
    stiffness assembly, or frame response is performed here.
    """
    prepared = request["prepared"]
    frame, native = request["frame"], request["native_context"]
    n = int(frame["H"].shape[0])
    require(n in CURRENT_PORT_COUNTS and frame["H"].shape == (n, n)
            and frame["e"].shape == (n, 12) and frame["D"].shape == (n, 344),
            "current frame must expose a 3192- or 3288-port operator basis")
    require(frame["Bwood"].shape == (n, 37647), "current full wood action matrix must match frame ports")
    require(native["K"].shape == (37647, 37647) and native["F"].shape == (37647, 12),
            "parent native context shape differs")
    require(len(native["names"]) == 50 and len(native["owners"]) == 37647,
            "native body/DOF ownership census differs")
    for path, digest in frame.get("source_sha256", {}).items():
        path = Path(path).resolve()
        require(sha(path) == digest, "parent frame source changed: " + str(path))
        prepared["source_sha256"][path] = digest
    for path, digest in native["source_sha256"].items():
        path = Path(path).resolve()
        require(sha(path) == digest, "parent native source changed: " + str(path))
        prepared["source_sha256"][path] = digest
    require(np.asarray(prepared["F_native_base"]).shape == native["F"].shape,
            "base operator packet native force shape differs")

    point_delta = prepared["B_delta_raw"].tocsr()
    require(point_delta.shape == prepared["B_base"].shape == (len(prepared["rows"]), 37647),
            "prepared raw B and row census differ")
    current_delta, touched = _mapped_delta(point_delta, prepared["mapping"], n)
    require(len(touched) >= 18, "expected all six shifted structural axes to touch current ports")
    base_rows = _row_mapping(prepared["mapping"])
    if prepared["panel_count"] == 98:
        require(n == 3288, "98-axis composition requires the full 3288-port frame")
        _verify_mapped_Bwood(prepared["B_base"], prepared["mapping"], frame["Bwood"],
                             "98-axis base packet")
    else:
        for raw in sorted(int(x) for x in np.flatnonzero(np.diff(point_delta.indptr))):
            pos, weight = base_rows[raw]
            expected = weight * prepared["_source"].B0.getrow(raw)
            actual = frame["Bwood"].getrow(pos)
            require(np.max(np.abs((actual - expected).data), initial=0.0) < 1e-8,
                    "current frame Bwood does not contain the frozen original shifted-row action")

    dH = np.zeros((n, n), dtype=float)
    dD = np.zeros((n, 344), dtype=float)
    de = np.zeros((n, 12), dtype=float)
    dW = np.asarray(prepared["dW_base"], dtype=float).copy()
    D_raw = np.asarray(prepared["D_raw_base"], dtype=float).copy()
    F_native = np.asarray(prepared["F_native_base"], dtype=float).copy()
    if prepared["dH_base"] is not None:
        dH += _pad_square(prepared["dH_base"], n, "base dH")
        dD += _pad_vector_rows(prepared["dD_base"], n, 344, "base dD")
        de += _pad_vector_rows(prepared["de_base"], n, 12, "base de")
    require(D_raw.shape == (point_delta.shape[0], 300), "base D_raw shape differs from B row count")
    require(F_native.shape == (37647, 12) and np.all(np.isfinite(F_native)),
            "base native force matrix is invalid")

    condensation = module(CONDENSATION, "bolt_spacing_condensation")
    quotient = module(QUOTIENT, "bolt_spacing_quotient")
    body_reports = []
    changed_bodies = set()
    for body in sorted(EXPECTED_CHANGED_BODIES):
        body_id = native["names"].index(body)
        dofs = np.flatnonzero(np.asarray(native["owners"]) == body_id)
        labels = [native["labels"][int(i)] for i in dofs]
        coordinates = {node: native["coordinates"][node] for node, _ in labels}
        _center, R, Q = condensation.rigid_basis(labels, coordinates, 1000.)
        K = native["K"][dofs][:, dofs].tocsr()
        old_B = frame["Bwood"][:, dofs].tocsr()
        delta_B = current_delta[:, dofs].tocsr()
        active = np.flatnonzero(np.diff(delta_B.indptr))
        require(len(active) > 0, body + ": no changed point rows project into the receiver")
        raw_rhs = delta_B[active].T.toarray()
        elastic_rhs = raw_rhs - Q @ (Q.T @ raw_rhs)
        operator = quotient.audit_quotient_operator(K, R)
        require(operator.get("status") == quotient.PASS_ELASTIC_QUOTIENT_SCREEN,
                body + ": elastic quotient screen failed")
        factor, system = condensation.factor_bordered(K, R)
        solved = quotient.solve_quotient_chunk(factor, system, K, R, elastic_rhs,
                                               operator_report=operator)
        require(solved.get("status") == quotient.PASS_ELASTIC_QUOTIENT_SCREEN,
                body + ": changed-point quotient solve failed: " + str(solved.get("status")))
        U = np.asarray(solved["displacement_mm"])
        cross = np.asarray(old_B @ U)
        dH[:, active] += cross
        dH[active, :] += cross.T
        dH[np.ix_(active, active)] += np.asarray(delta_B[active] @ U)
        de[np.ix_(active, np.arange(12))] += U.T @ F_native[dofs]
        body_d = np.asarray(delta_B @ R)
        body_d_raw = np.asarray(point_delta[:, dofs] @ R)
        dD[:, 6 * body_id:6 * body_id + 6] += body_d
        D_raw[:, 6 * body_id:6 * body_id + 6] += body_d_raw
        changed_bodies.add(body)
        body_reports.append({"body": body, "body_id": int(body_id),
            "changed_current_rows": active.tolist(), "local_dof_count": len(dofs),
            "quotient_status": solved["status"],
            "KKT_upper_force_residual_relative": solved["KKT_upper_force_residual_relative"],
            "cross_terms_include_all_current_ports": True,
            "native_stiffness_rebuilt": False})
    require(changed_bodies == EXPECTED_CHANGED_BODIES, "not all six receivers were updated")
    asym = float(np.max(np.abs(dH - dH.T), initial=0.0))
    require(asym <= 1e-8 * max(1.0, float(np.max(np.abs(dH), initial=0.0))),
            "cumulative operator delta is not reciprocal")

    output = Path(output).resolve()
    require(output.is_relative_to(OUTPUT_ROOT.resolve()) and output != OUTPUT_ROOT.resolve()
            and not output.exists(), "fresh bolt-spacing rawlocal output directory required")
    output.mkdir(parents=True)
    (output / ".gitignore").write_text("*\n")
    (output / "producer.py.snapshot").write_bytes(Path(__file__).read_bytes())
    np.savez_compressed(output / "operator-delta.npz", dH=dH, dD=dD, de=de, dW=dW,
                        D_raw=D_raw, F_native=F_native)
    sparse.save_npz(output / "B.npz", prepared["B_base"] + point_delta)
    shared = module(HERE / "current-method-corrections.py", "bolt_spacing_shared_writer")
    shared.write(output / "proposal.json", prepared["proposal"])
    shared.write(output / "row-identities.json", prepared["rows"])
    shared.write(output / "axes.json", prepared["axes"])
    shared.write(output / "source-row-map.json", prepared["mapping"])
    shared.write(output / "panel-reference-context.json", prepared["panel_context"])
    if prepared["added_screw_laws_path"] is not None:
        shutil.copyfile(prepared["added_screw_laws_path"], output / "added-screw-laws.json")
    shared.write(output / "operator-update-audit.json", {"schema": "bolt_spacing_operator_update/v1",
        "status": "OPERATORS_PREPARED_PARENT_RESPONSE_REQUIRED", "current_port_count": n,
        "raw_operator_row_count": int(point_delta.shape[0]), "changed_current_rows": touched,
        "changed_bodies": body_reports, "source_base_packet": str(prepared["base_packet"]) if prepared["base_packet"] else None,
        "base_panel_axis_count": prepared["panel_count"], "cumulative_from_original_horizontal_frame": True,
        "panel_delta_added": prepared["dH_base"] is not None,
        "base_audit_bodies": sorted(prepared["base_audit_bodies"]),
        "added_screw_laws_preserved": prepared["added_screw_laws_path"] is not None,
        "dW_preserved_from_base_packet": True,
        "full_current_Bwood_cross_terms_included": True, "delta_H_max_abs_asymmetry": asym,
        "native_matrix_parsing_by_adapter": False, "native_stiffness_assembly_by_adapter": False,
        "frame_equilibrium_or_response_by_adapter": False, "complete_joint_acceptance": False,
        "physical_release": False})
    for path, digest in prepared["source_sha256"].items():
        path = Path(path).resolve()
        require(sha(path) == digest, "source changed while constructing bolt-spacing remedy: " + str(path))
    source_sha = {Path(path).resolve().relative_to(ROOT).as_posix(): digest
                  for path, digest in prepared["source_sha256"].items()}
    output_sha = {path.name: sha(path) for path in output.iterdir()
                  if path.is_file() and path.name != "receipt.json"}
    shared.write(output / "receipt.json", {"schema": "bolt_spacing_operator_delta_receipt/v1",
        "status": "OPERATORS_PREPARED_PARENT_RESPONSE_REQUIRED", "source_sha256": source_sha,
        "output_sha256": output_sha, "physical_release": False})
    return {"path": output, "source_sha256": source_sha, "output_sha256": output_sha,
        "changed_bodies": body_reports, "current_port_count": n, "physical_release": False}
