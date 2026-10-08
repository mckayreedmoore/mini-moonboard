"""Exact pre-solve sparse snapshots; no assembly, response or old-field reader."""
from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace

import numpy as np
from scipy.sparse import csr_matrix

OWN = Path(__file__).resolve()
CORE = OWN.with_name("run_first_order.py")
CORE_SHA = "28ceafcb9eac9764358071b728da96fbb2e5cd46011ead031ade8a9d7a811a39"
LOADED_SHA = hashlib.sha256(OWN.read_bytes()).hexdigest()
if hashlib.sha256(CORE.read_bytes()).hexdigest() != CORE_SHA:
    raise ValueError("preserve frozen first-order core")
SPEC = importlib.util.spec_from_file_location("eoere_frozen_operator_export_core", CORE)
core = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(core)
FROZEN_RUNTIME_PINS = core.runtime_pins
require, frame = core.factory.require, core.frame
SCHEMA = "eoere_first_order_original_operator_bundle/v1"


def source_pins(extra=None):
    pins = FROZEN_RUNTIME_PINS(extra)
    require(frame.sha(CORE) == CORE_SHA and frame.sha(OWN) == LOADED_SHA, "operator snapshot source changed")
    pins[str(OWN.relative_to(frame.ROOT))] = LOADED_SHA
    return pins


def artifact_path(path):
    path = Path(path).resolve()
    return str(path.relative_to(frame.ROOT)) if path.is_relative_to(frame.ROOT) else str(path)


def coordinate_map(prepared):
    """Owned point/rigid maps only; no element K or response is reconstructed."""
    assembly = prepared.assembly
    timber = {name: {key: core.serial(row[key]) for key in ("index", "stations", "start", "axis", "source")}
              for name, row in assembly.members.items()}
    panels = {}
    for name, panel in assembly.panels.items():
        basis = panel["basis"]
        panels[name] = {"indices": assembly.panel_offsets[name].tolist(), "geometry": core.serial(panel["geometry"]),
                       "thickness_mm": panel["thickness"], "width_mm": basis.width, "height_mm": basis.height,
                       "intervals": basis.intervals, "basis_order_per_direction": basis.order,
                       "knots_normalized": basis.knots.tolist(),
                       "coefficient_order": "u,v,outward_w; x-major tensor cubic B-spline coefficients in mm"}
    shafts = {name: {key: core.serial(row[key]) for key in
              ("axis_id", "point", "basis", "diameter_mm", "stations", "index", "offset", "ndof", "surfaces", "ends")}
              for name, row in prepared.system.shafts.items()}
    return {"schema": "eoere_first_order_owned_coordinate_map/v1", "final_ndof": assembly.ndof,
            "rotation_scale": frame.ROTATION_SCALE, "timber": timber, "panels": panels, "shafts": shafts,
            "four_port_fittings": {name: element.descriptor() for name, element in prepared.fittings.items()},
            "fitting_embedding_ndof_by_owner": {name: element.ndof for name, element in prepared.fittings.items()},
            "unused_legacy_two_port_fitting_indices": {name: core.serial(row["index"]) for name, row in assembly.fittings.items()},
            "shaft_axial_spin_is_free_numerical_gauge_without_torque_reaction": True}


def _array_record(value):
    require(isinstance(value, np.ndarray) and value.dtype.kind in "fiu" and np.isfinite(value).all(),
            "finite numeric raw operator array required")
    return {"dtype": value.dtype.str, "shape": list(value.shape), "nbytes": value.nbytes,
            "content_sha256": hashlib.sha256(value.tobytes(order="C")).hexdigest()}


def _put_csr(arrays, prefix, matrix):
    require(isinstance(matrix, csr_matrix), "actual CSR operator required; no format conversion")
    keys = {name: prefix+"/"+name for name in ("data", "indices", "indptr")}
    for name, key in keys.items():
        arrays[key] = getattr(matrix, name).copy()
    return {"storage": "csr", "shape": list(matrix.shape), **keys}


def _get_csr(arrays, record):
    require(record["storage"] == "csr" and len(record["shape"]) == 2, "CSR shape contract differs")
    rows, columns = record["shape"]
    require(type(rows) is int and type(columns) is int and rows > 0 and columns > 0, "positive CSR shape required")
    data, indices, indptr = (arrays[record[key]] for key in ("data", "indices", "indptr"))
    require(data.ndim == indices.ndim == indptr.ndim == 1 and data.dtype.kind == "f"
            and indices.dtype.kind in "iu" and indptr.dtype.kind in "iu"
            and len(data) == len(indices) and len(indptr) == rows+1
            and indptr[0] == 0 and indptr[-1] == len(data) and np.all(indptr[1:] >= indptr[:-1])
            and np.all((indices >= 0) & (indices < columns)), "raw CSR array contract differs")
    matrix = csr_matrix((data, indices, indptr), shape=(rows, columns), copy=True)
    # SciPy may downcast int64 indices. Preserve exact original storage bytes.
    matrix.data, matrix.indices, matrix.indptr = data.copy(), indices.copy(), indptr.copy()
    return matrix


def snapshot(prepared, *, arrays_path, manifest_path, pins, command):
    """Write exclusive immutable operators before solve; include every source row."""
    arrays_path, manifest_path = Path(arrays_path), Path(manifest_path)
    require(not arrays_path.exists() and not manifest_path.exists(), "preserve existing operator bundle bytes")
    before = source_pins(pins)
    fingerprint = core.operator_fingerprint(prepared)
    arrays = {"applied": np.asarray(prepared.applied).copy(), "rigid_modes": prepared.assembly.rigid_modes().copy()}
    n = prepared.assembly.ndof
    require(arrays["applied"].shape == (n,) and arrays["rigid_modes"].shape == (n, 6), "full-coordinate load/rigid shape differs")
    k = _put_csr(arrays, "K", prepared.assembly.K)
    partitions = {}
    for partition in ("groups", "contacts", "tangents"):
        partitions[partition] = [{"descriptor": core.descriptor(row),
            "B": _put_csr(arrays, f"{partition}/{i}", row["B"])}
            for i, row in enumerate(getattr(prepared, partition))]
    records = {key: _array_record(value) for key, value in arrays.items()}
    arrays_path.parent.mkdir(parents=True, exist_ok=True)
    with arrays_path.open("xb") as handle:
        np.savez_compressed(handle, **arrays)
    pointer = {"path": artifact_path(arrays_path), "sha256": frame.sha(arrays_path)}
    manifest = {"schema": SCHEMA, "source_sha256": before, "arrays": pointer, "array_metadata": records,
        "K": k, "applied_key": "applied", "rigid_modes_key": "rigid_modes", "partitions": partitions,
        "final_ndof": n, "case": core.serial(prepared.case), "body_descriptors": core.serial(prepared.assembly.geo["bodies"]),
        "fitting_descriptors": [el.descriptor() for el in prepared.fittings.values()], "coordinate_map": coordinate_map(prepared),
        "original_operator_fingerprint_sha256": fingerprint, "execution_command": command,
        "captured_before_one_fresh_solve": True, "historical_q_or_forces_used": False,
        "original_support_rows_preserved_in_source_order": True, "rigid_modes_reference_xyz_mm": frame.REFERENCE.tolist()}
    require(source_pins(pins) == before and core.operator_fingerprint(prepared) == fingerprint,
            "source/operator changed during snapshot")
    core.write_exclusive(manifest_path, manifest)
    return {"manifest": {"path": artifact_path(manifest_path), "sha256": frame.sha(manifest_path)}, "arrays": pointer}


def read_snapshot(pointer):
    """Deserialize original numeric operators; no candidate preparation or K build."""
    paths = {}
    for key in ("manifest", "arrays"):
        record = pointer[key]
        paths[key] = frame.ROOT/record["path"]
        require(frame.sha(paths[key]) == record["sha256"], "raw operator bundle SHA differs")
    manifest = json.loads(paths["manifest"].read_bytes())
    require(manifest["schema"] == SCHEMA and manifest["arrays"] == pointer["arrays"]
            and manifest["captured_before_one_fresh_solve"] is True
            and manifest["historical_q_or_forces_used"] is False
            and manifest["original_support_rows_preserved_in_source_order"] is True, "operator manifest contract differs")
    before = source_pins(manifest["source_sha256"])
    with np.load(paths["arrays"], allow_pickle=False) as bank:
        require(set(bank.files) == set(manifest["array_metadata"]), "raw operator array inventory differs")
        arrays = {key: bank[key].copy() for key in bank.files}
    require(all(_array_record(arrays[key]) == record for key, record in manifest["array_metadata"].items()),
            "raw array dtype/shape/content differs")
    n = manifest["final_ndof"]
    k = _get_csr(arrays, manifest["K"])
    applied, rigid = arrays[manifest["applied_key"]], arrays[manifest["rigid_modes_key"]]
    require(k.shape == (n, n) and applied.shape == (n,) and rigid.shape == (n, 6), "full-coordinate bundle shape differs")
    partitions = {}
    for partition in ("groups", "contacts", "tangents"):
        partitions[partition] = [{**copy.deepcopy(row["descriptor"]), "B": _get_csr(arrays, row["B"])}
                                 for row in manifest["partitions"][partition]]
        require(all(row["B"].shape == (3 if partition == "groups" else 1, n) for row in partitions[partition]),
                "interaction B row/full-coordinate shape differs")
    ids = [row["id"] for partition in partitions.values() for row in partition]
    require(len(ids) == len(set(ids)), "original interaction ID duplicated")
    descriptors = manifest["fitting_descriptors"]
    audit_view = SimpleNamespace(assembly=SimpleNamespace(K=k, ndof=n, geo={"bodies": manifest["body_descriptors"]}),
        applied=applied, case=manifest["case"], fittings={row["body"]: SimpleNamespace(descriptor=lambda row=row: row)
        for row in descriptors}, **partitions)
    require(core.operator_fingerprint(audit_view) == manifest["original_operator_fingerprint_sha256"],
            "original operator fingerprint cannot be reproduced")
    require(source_pins(manifest["source_sha256"]) == before
            and all(frame.sha(paths[key]) == pointer[key]["sha256"] for key in paths), "bundle/source bytes changed during read")
    return SimpleNamespace(**vars(audit_view), rigid_modes=rigid, manifest=manifest, coordinate_map=manifest["coordinate_map"])
