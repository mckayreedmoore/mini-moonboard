#!/usr/bin/env python3
"""Prepared, parent-gated two-body A12 row-1586 endpoint recovery.

Only --toy-check factors a synthetic matrix. Actual source-K extraction and
body recovery require a separate parent approval record and one-shot marker.
No native solver is launched by any mode.
"""
from __future__ import annotations

import os

# Keep any BLAS work single-threaded inside the frozen CPU bound.
os.environ["OPENBLAS_NUM_THREADS"] = "1"
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"

import argparse
import hashlib
import importlib.util
import json
import math
import resource
import signal
import sys
import tarfile
import time
from collections.abc import Iterable
from pathlib import Path

import numpy as np
import scipy
import scipy.sparse as sp

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
PREP = ROOT / "docs/wood-joints-mvp/hypotheses/a12-row1586-endpoint-recovery-preflight-2026-10-01"
PIN_FILE = HERE / "source-pins.json"
READINESS_SHA256 = "edcc2fbc8adddfab44e8419db8b297df4c8f6f6a11e905523d1bcb60102d84f7"
PIN_MANIFEST_SHA256 = "187fda0ceb9c93d282d1697367aa95ee57b3e205f32fcbbe1ebc6abb644b290e"
TARGET_ROW = 1586
TARGET_GROUP = "SPR1787"
TARGET_ELEMENT = 3690
TARGET_OWNERS = ("left_service_inner_lower_cleat", "base_rail_service_lower_left")
ROTATION_SCALE_MM = 1000.0
MAX_CPU_SECONDS = 60
MAX_WALL_SECONDS = 60
MAX_ADDRESS_SPACE_BYTES = 2 * 1024**3
MAX_PARENT_RUNS = 1
MAX_BODY_FACTORIZATIONS = 2
MAX_CORRECTIONS_PER_BODY = 5
RUN_MARKER = Path("/tmp/mini-moonboard-a12-row1586-endpoint-recovery-attempt01.consumed")
CCX_SOURCE_ARCHIVE = Path("/tmp/ccx_2.23.src.tar.bz2")
CCX_SOURCE_MEMBERS = {
    "./CalculiX/ccx_2.23/src/springforc_n2f.f": "706d066ef4b951c6382b754094bc576d98865b86f6272da535b588c7e7282d60",
    "./CalculiX/ccx_2.23/src/calcspringforc.f": "67d945c054f9e0584432a0f4aef5bd6d3373688530ceaafe4c96796c72b975aa",
    "./CalculiX/ccx_2.23/src/materialdata_sp.f": "b1089a3d57be2e5477cc9351866513333453bcb050617a408a7b3ff491c083a5",
}
FACTOR_COUNT = 0


def sha_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def csr_sha256(matrix: sp.csr_matrix) -> str:
    canonical = sp.csr_matrix(matrix, dtype=np.float64)
    return sha_bytes(
        np.asarray(canonical.shape, dtype="<i8").tobytes()
        + np.asarray(canonical.indptr, dtype="<i8").tobytes()
        + np.asarray(canonical.indices, dtype="<i8").tobytes()
        + np.asarray(canonical.data, dtype="<f8").tobytes()
    )


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def import_module(path: Path, name: str):
    sys.dont_write_bytecode = True
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import pinned method module: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def verify_pins() -> dict:
    if sha_file(PIN_FILE) != PIN_MANIFEST_SHA256:
        raise RuntimeError("runner source-pins.json hash differs from the reviewed manifest")
    manifest = load_json(PIN_FILE)
    if manifest.get("schema") != "a12_row1586_endpoint_recovery_runner_inputs/v1":
        raise RuntimeError("runner source pin schema changed")
    observed = {}
    for name, record in manifest["files"].items():
        path = ROOT / record["path"]
        actual = sha_file(path)
        if actual != record["sha256"]:
            observed[name] = {"expected": record["sha256"], "actual": actual}
    if observed:
        raise RuntimeError(f"frozen recovery inputs changed: {observed}")
    return {name: record["sha256"] for name, record in manifest["files"].items()}


def verify_preflight_replay() -> dict:
    module = import_module(PREP / "prepare_recovery.py", "a12_endpoint_source_preflight")
    report = module.verify_report()
    if module.sha_file(module.PIN_FILE) != sha_file(PREP / "source-pins.json"):
        raise RuntimeError("preflight source pin identity changed")
    if sha_file(PREP / "readiness.json") != READINESS_SHA256:
        raise RuntimeError("reviewed preflight readiness hash changed")
    if report.get("status") != "READY_FOR_PARENT_REVIEW_SOURCE_ONLY":
        raise RuntimeError("parent-reviewed source-only readiness no longer passes")
    return report


def verify_calculix_spring_source(pins: dict[str, str]) -> dict:
    archive_sha = "9c88385c10fb04f5dc6c4e98027a51bebdd8aee3920e05190d6c1dd08357d6e7"
    if pins.get("calculix_2_23_source_archive") != archive_sha:
        raise RuntimeError("pinned CalculiX source archive identity changed")
    source = {}
    with tarfile.open(CCX_SOURCE_ARCHIVE, mode="r:bz2") as archive:
        for member, expected_hash in CCX_SOURCE_MEMBERS.items():
            data = archive.extractfile(member)
            if data is None:
                raise RuntimeError(f"pinned CalculiX source member is missing: {member}")
            raw = data.read()
            actual_hash = sha_bytes(raw)
            if actual_hash != expected_hash:
                raise RuntimeError(f"pinned CalculiX source member hash changed: {member}")
            source[member] = raw.decode("latin1")
    endpoint = source["./CalculiX/ccx_2.23/src/springforc_n2f.f"]
    table = source["./CalculiX/ccx_2.23/src/calcspringforc.f"]
    columns = source["./CalculiX/ccx_2.23/src/materialdata_sp.f"]
    required = (
        (endpoint, "pl(j,i)=xl(j,i)+vl(j,i)"),
        (endpoint, "dd0=dsqrt((xl(1,2)-xl(1,1))**2"),
        (endpoint, "dd=dsqrt((pl(1,2)-pl(1,1))**2"),
        (endpoint, "val=dd-dd0"),
        (table, "fk=yiso(id)+xk*(val-xiso(id))"),
        (columns, "plconloc(2*k-1), k=1...200: displacement"),
        (columns, "plconloc(2*k),k=1...200:    force"),
    )
    if any(fragment not in text for text, fragment in required):
        raise RuntimeError("pinned CalculiX endpoint or nonlinear-table operation changed")
    return {
        "archive_sha256": archive_sha,
        "source_member_sha256": CCX_SOURCE_MEMBERS,
        "endpoint_dd_minus_dd0_operation_verified": True,
        "force_displacement_table_column_order_verified": True,
        "binary64_interpolation_operation_verified": True,
    }


def parse_dof_file(path: Path) -> list[tuple[int, int]]:
    labels = []
    for line_number, line in enumerate(path.read_text(encoding="ascii").splitlines(), 1):
        pieces = line.strip().split(".")
        if len(pieces) != 2:
            raise ValueError(f"bad native DOF label at line {line_number}")
        node, direction = int(pieces[0]), int(pieces[1])
        if direction not in (1, 2, 3):
            raise ValueError(f"bad native DOF direction at line {line_number}")
        labels.append((node, direction))
    if len(labels) != 37647 or len(set(labels)) != 37647:
        raise ValueError("pinned DOF labels are not a unique 37,647-entry order")
    return labels


def source_snapshot(pins: dict[str, str], *, replay: bool = True) -> dict:
    kernel_source = verify_calculix_spring_source(pins)
    preflight = verify_preflight_replay() if replay else load_json(PREP / "readiness.json")
    if preflight["scope"]["candidate"] != "compact-floor-flush-wood-joints-development":
        raise RuntimeError("candidate identity changed")
    if preflight["scope"]["geometry_revision_id"] != "led-clearance-2x6-runner-seated-blocks-v1":
        raise RuntimeError("geometry revision changed")
    if preflight["scope"]["target_row_position"] != TARGET_ROW:
        raise RuntimeError("target source row changed")
    if preflight["prior_stop"]["raw_H_status"] != "STOP_PHYSICAL_OR_SOURCE_COMPARISON_GATE":
        raise RuntimeError("original raw-H STOP status changed")
    if preflight["prior_stop"]["unchanged_failed_force_intervals"] != 27:
        raise RuntimeError("original 27-force-interval STOP count changed")

    raw_path = ROOT / "docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/current-a12-fixed-active-raw-H-comparison-attempt01/response.npz"
    with np.load(raw_path, allow_pickle=False) as archive:
        raw = {key: archive[key].copy() for key in archive.files}
    assessment = load_json(ROOT / "docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/current-a12-fixed-active-raw-H-comparison-attempt01/assessment.json")
    matrix_assessment = load_json(ROOT / "docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/current-frame-pure-solid-matrix-export-native-attempt01/assessment.json")
    model = load_json(ROOT / "docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/current-springa-frame-input-adapter-attempt01/a12-rear/model.json")
    projection = load_json(ROOT / "docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/current-frame-physical-connector-projection-contract-attempt01/projection-contract.json")
    physical_map = load_json(ROOT / "docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/current-frame-physical-connector-projection-contract-attempt01/physical-index-map.json")
    source_loads = load_json(ROOT / "docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/current-frame-pure-solid-matrix-export-preflight-attempt01/source-load-maps.json")
    native_response = load_json(ROOT / "docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/current-springa-selected-floor-a12-rear-attempt03/response.json")

    if assessment["status"] != "STOP_PHYSICAL_OR_SOURCE_COMPARISON_GATE":
        raise RuntimeError("raw-H source STOP changed")
    if assessment["original_DAT_comparisons"]["forces"]["failed_count"] != 27:
        raise RuntimeError("raw-H source failed interval count changed")
    if assessment.get("candidate_forces_adopted") or assessment.get("mechanical_acceptance"):
        raise RuntimeError("raw-H source has an adopted or accepted disposition")
    if matrix_assessment["status"] != "PASS_PURE_SOLID_SPARSE_STRUCTURE_AND_BODY_RIGID_MODE_SCREEN":
        raise RuntimeError("source matrix assessment is not the pinned sparse export")
    if matrix_assessment["stiffness"]["dimension"] != 37647 or matrix_assessment["stiffness"]["triangle_pair_count"] != 2320506:
        raise RuntimeError("source stiffness dimensions or triangle count changed")
    if matrix_assessment["stiffness"]["reconstructed_symmetric_nonzero_count"] != 4601263:
        raise RuntimeError("source stiffness reconstructed nonzero count changed")
    if matrix_assessment["stiffness"]["input_triangle"] != "one-based upper triangle, one unique pair per row":
        raise RuntimeError("source stiffness triangle convention changed")
    if matrix_assessment["stiffness"]["cross_body_nonzero_pair_count"] != 0:
        raise RuntimeError("frozen matrix assessment has cross-body nonzero pairs")
    if raw["f_full_N"].shape != (1840,) or raw["a_mm"].shape != (300,):
        raise RuntimeError("saved raw-H f/a shapes changed")

    residual = np.asarray(raw["body_equilibrium_residuals_N_and_unscaled_moment"], dtype=np.float64)
    if residual.shape != (50, 6):
        raise RuntimeError("raw-H source body equilibrium shape changed")
    force_pass = np.max(np.abs(residual[:, :3]), axis=1) <= 0.1
    moment_pass = 1000.0 * np.max(np.abs(residual[:, 3:]), axis=1) <= 2.0
    if not np.all(force_pass & moment_pass):
        raise RuntimeError("unchanged all-body raw-H force/moment bookkeeping gate now fails")

    if model.get("candidate") != preflight["scope"]["candidate"] or model.get("geometry_revision_id") != preflight["scope"]["geometry_revision_id"]:
        raise RuntimeError("source model identity does not match reviewed preflight")
    labels = parse_dof_file(ROOT / "docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/current-frame-pure-solid-matrix-export-native-attempt01/model.dof")
    physical_by_node = {int(record["node"]): record for record in physical_map}
    if len(physical_map) != 12549 or len(physical_by_node) != 12549:
        raise RuntimeError("physical source map is not a complete unique node map")
    model_nodes_by_body = {
        body: {int(node) for node in nodes}
        for body, nodes in model["physical_body_nodes"].items()
    }
    observed_nodes_by_body = {body: set() for body in model_nodes_by_body}
    for record in physical_map:
        body = record["body"]
        if body not in observed_nodes_by_body:
            raise RuntimeError(f"physical source map contains an unknown owner: {body}")
        observed_nodes_by_body[body].add(int(record["node"]))
    if observed_nodes_by_body != model_nodes_by_body:
        raise RuntimeError("physical source owner/node membership differs from the pinned source model")
    if projection.get("candidate") != preflight["scope"]["candidate"] or projection.get("geometry_revision_id") != preflight["scope"]["geometry_revision_id"] or projection.get("case_id") != "a12-rear":
        raise RuntimeError("physical connector projection candidate/revision/case changed")
    if len(projection.get("rows", [])) != 1840 or projection.get("physical_coordinate_map", {}).get("coordinate_count") != 37647:
        raise RuntimeError("physical connector projection row/coordinate coverage changed")
    owner_by_global = []
    for node, direction in labels:
        record = physical_by_node.get(node)
        if record is None or direction not in (1, 2, 3):
            raise RuntimeError(f"DOF map contains nonphysical source label {(node, direction)}")
        owner_by_global.append(record["body"])
    if set(owner_by_global) != set(model["physical_body_nodes"]):
        raise RuntimeError("native DOF map and source physical-body inventory disagree")

    load_cases = [item for item in source_loads["cases"] if item["case_id"] == "a12-rear"]
    if len(load_cases) != 1:
        raise RuntimeError("A12 rear source nodal load case is missing or duplicated")
    case = load_cases[0]
    if not case.get("gravity_nodal_map") or not case.get("climber_nodal_map"):
        raise RuntimeError("A12 rear source force maps are missing")
    native_rows = [row for row in native_response["increments"][-1]["springa_components"] if row.get("element") == TARGET_ELEMENT]
    if len(native_rows) != 1:
        raise RuntimeError("pinned native response target row is missing or duplicated")
    native_row = native_rows[0]
    if native_row.get("source_group") != TARGET_GROUP or native_row.get("source_inventory_row_index") != 1786:
        raise RuntimeError("pinned native target row identity changed")
    if native_row.get("intended_source_law") != "tension_only":
        raise RuntimeError("target native spring law changed")

    return {
        "preflight": preflight,
        "kernel_source": kernel_source,
        "raw": raw,
        "raw_assessment": assessment,
        "matrix_assessment": matrix_assessment,
        "model": model,
        "projection": projection,
        "physical_map": physical_map,
        "physical_by_node": physical_by_node,
        "source_load_case": case,
        "native_response_row": native_row,
        "labels": labels,
        "owner_by_global": owner_by_global,
        "pins": pins,
        "raw_all_body_gate_passed": True,
    }


def build_body_layouts(snapshot: dict) -> dict[str, dict]:
    physical_map = snapshot["physical_map"]
    model = snapshot["model"]
    labels = snapshot["labels"]
    body_by_node = {int(record["node"]): record["body"] for record in physical_map}
    xyz_by_node = {int(node): np.asarray(xyz, dtype=np.float64) for node, xyz in model["nodes"].items()}
    layouts = {}
    for body in TARGET_OWNERS:
        nodes = sorted(node for node, owner in body_by_node.items() if owner == body)
        if not nodes or any(node not in xyz_by_node for node in nodes):
            raise RuntimeError(f"source physical coordinates missing for target body {body}")
        body_globals = [index for index, label in enumerate(labels) if body_by_node[label[0]] == body]
        body_labels = [labels[index] for index in body_globals]
        expected_labels = {(node, direction) for node in nodes for direction in (1, 2, 3)}
        if set(body_labels) != expected_labels or len(body_globals) != 3 * len(nodes):
            raise RuntimeError(f"target body DOF order is incomplete or duplicated for {body}")
        center = np.mean(np.stack([xyz_by_node[node] for node in nodes]), axis=0)
        R = np.zeros((len(body_globals), 6), dtype=np.float64)
        local_by_global = {global_index: local_index for local_index, global_index in enumerate(body_globals)}
        local_by_label = {label: local_index for local_index, label in enumerate(body_labels)}
        eye = np.eye(3)
        for local_index, (node, direction) in enumerate(body_labels):
            component = direction - 1
            R[local_index, component] = 1.0
            relative = xyz_by_node[node] - center
            for axis in range(3):
                R[local_index, 3 + axis] = np.cross(eye[axis], relative)[component] / ROTATION_SCALE_MM
        report_body = snapshot["preflight"]["frozen_state"]["body_maps"][body]
        if len(body_globals) != report_body["physical_dof_count"]:
            raise RuntimeError(f"target body DOF count differs from frozen preflight for {body}")
        expected_sorted_hash = report_body["native_dof_index_list_sha256_i64le"]
        observed_sorted_hash = sha_bytes(np.asarray(sorted(body_globals), dtype="<i8").tobytes())
        if observed_sorted_hash != expected_sorted_hash:
            raise RuntimeError(f"target body native DOF set/order differs from frozen preflight for {body}")
        layouts[body] = {
            "nodes": nodes,
            "xyz_by_node": xyz_by_node,
            "center_mm": center,
            "global_indices": body_globals,
            "labels": body_labels,
            "local_by_global": local_by_global,
            "local_by_label": local_by_label,
            "R": R,
            "body_id": int(report_body["rigid_coordinate_index"]),
        }
    return layouts


def verify_body_rigid_operator(snapshot: dict, layouts: dict[str, dict]) -> dict[str, float]:
    operators_path = ROOT / "docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/current-frame-connector-compliance-attempt04/operators.npz"
    with np.load(operators_path, allow_pickle=False) as archive:
        D = archive["D"]
    if D.shape != (1840, 300):
        raise RuntimeError("pinned source D operator has an unexpected shape")
    physical_map = snapshot["physical_map"]
    report = {}
    for body, layout in layouts.items():
        expected = np.zeros((1840, 6), dtype=np.float64)
        for row_index, row in enumerate(snapshot["projection"]["rows"]):
            for term in row["physical_sparse_row"]:
                coordinate = int(term["coordinate_index"])
                phys = physical_map[coordinate // 3]
                if phys["body"] != body:
                    continue
                label = (int(phys["node"]), coordinate % 3 + 1)
                local = layout["local_by_label"].get(label)
                if local is None:
                    raise RuntimeError(f"target body source projection points outside its DOF map: {body}")
                expected[row_index] += float(term["coefficient"]) * layout["R"][local]
        body_id = layout["body_id"]
        difference = float(np.max(np.abs(expected - D[:, 6 * body_id:6 * body_id + 6])))
        if difference > 1.0e-14:
            raise RuntimeError(f"source reconstruction of B*R differs from saved D for {body}: {difference}")
        report[body] = difference
    return report


def build_raw_body_loads(snapshot: dict, layouts: dict[str, dict]) -> dict[str, dict]:
    physical_map = snapshot["physical_map"]
    body_by_node = snapshot["physical_by_node"]
    source_case = snapshot["source_load_case"]
    raw = snapshot["raw"]
    loads = {}
    for body, layout in layouts.items():
        p = np.zeros(len(layout["global_indices"]), dtype=np.float64)
        gravity = np.zeros_like(p)
        climber = np.zeros_like(p)
        for field, destination in (("gravity_nodal_map", gravity), ("climber_nodal_map", climber)):
            for node_text, vector in source_case[field].items():
                node = int(node_text)
                if node not in body_by_node or body_by_node[node]["body"] != body:
                    continue
                for direction, value in enumerate(vector, 1):
                    local = layout["local_by_label"].get((node, direction))
                    if local is None:
                        raise RuntimeError(f"source load node/direction missing from target DOF order: {body}")
                    destination[local] += float(value)
        p += gravity + climber
        for row_index, row in enumerate(snapshot["projection"]["rows"]):
            force = float(raw["f_full_N"][row_index])
            for term in row["physical_sparse_row"]:
                coordinate = int(term["coordinate_index"])
                phys = physical_map[coordinate // 3]
                if phys["body"] != body:
                    continue
                label = (int(phys["node"]), coordinate % 3 + 1)
                local = layout["local_by_label"].get(label)
                if local is None:
                    raise RuntimeError(f"connector row points outside target DOF map: {body}")
                p[local] -= float(term["coefficient"]) * force
        body_id = layout["body_id"]
        source_residual = np.asarray(raw["body_equilibrium_residuals_N_and_unscaled_moment"][body_id], dtype=np.float64)
        generalized = layout["R"].T @ p
        closure_error = float(np.max(np.abs(generalized + source_residual)))
        if closure_error > 1.0e-8:
            raise RuntimeError(f"unchanged raw load does not reproduce saved body residual for {body}: {closure_error}")
        threshold = 1.0e-10 + 1.0e-10 * max(1.0, float(np.linalg.norm(p, ord=1)))
        balanced = bool(float(np.max(np.abs(generalized))) <= threshold)
        loads[body] = {
            "p": p,
            "gravity": gravity,
            "climber": climber,
            "generalized_wrench_scaled_N": generalized,
            "saved_Dtf_minus_W_scaled_N": source_residual,
            "closure_error_scaled_N": closure_error,
            "balance_threshold_N": threshold,
            "balanced_before_factorization": balanced,
        }
    return loads


def upper_triangle_index(row0: int, column0: int, dimension: int) -> int:
    return row0 * dimension - row0 * (row0 - 1) // 2 + (column0 - row0)


def filter_upper_triangle(
    stream: Iterable[str],
    dimension: int,
    owner_by_index: list[str],
    target_indices: dict[str, list[int]],
    *,
    expected_pair_count: int | None = None,
    expected_zero_pair_count: int | None = None,
    expected_symmetric_nonzero_count: int | None = None,
    expected_cross_body_nonzero_count: int | None = None,
) -> tuple[dict[str, sp.csr_matrix], dict]:
    """Stream one-based upper K entries into only requested body blocks."""
    if dimension <= 0 or len(owner_by_index) != dimension:
        raise ValueError("global stiffness dimension and DOF ownership differ")
    if any(i < 0 or i >= dimension for indices in target_indices.values() for i in indices):
        raise ValueError("target body global DOF index is out of range")
    if any(indices != sorted(set(indices)) for indices in target_indices.values()):
        raise ValueError("target body global DOF order must be sorted and unique")
    for name, indices in target_indices.items():
        expected_indices = [index for index, owner in enumerate(owner_by_index) if owner == name]
        if indices != expected_indices:
            raise ValueError(f"target body global DOF ownership/order is incomplete or wrong for {name}")
    local_maps = {name: {global_index: i for i, global_index in enumerate(indices)}
                  for name, indices in target_indices.items()}
    rows = {name: [] for name in target_indices}
    cols = {name: [] for name in target_indices}
    values = {name: [] for name in target_indices}
    block_pairs = {name: 0 for name in target_indices}
    block_nonzero_pairs = {name: 0 for name in target_indices}
    diag_seen = bytearray(dimension)
    pair_capacity = dimension * (dimension + 1) // 2
    # The bitset covers the address space of possible upper-triangle pairs but
    # absent pairs are valid structural zeros in this sparse export.
    seen = bytearray((pair_capacity + 7) // 8)
    pair_count = 0
    explicit_zero_count = 0
    upper_nonzero_count = 0
    symmetric_nonzero_count = 0
    non_target_pair_count = 0
    cross_body_zero_pair_count = 0
    cross_body_nonzero_count = 0
    cross_body_nonzero_examples = []
    for line_number, raw_line in enumerate(stream, 1):
        pieces = raw_line.split()
        if not pieces:
            continue
        if len(pieces) != 3 or not pieces[0].isascii() or not pieces[0].isdecimal() or not pieces[1].isascii() or not pieces[1].isdecimal():
            raise ValueError(f".sti line {line_number} is not an integer-indexed triplet")
        row1, col1 = int(pieces[0]), int(pieces[1])
        if row1 < 1 or col1 < 1 or row1 > dimension or col1 > dimension or row1 > col1:
            raise ValueError(f".sti line {line_number} is not in the pinned one-based upper triangle")
        try:
            value = float(pieces[2].replace("D", "E").replace("d", "e"))
        except ValueError as exc:
            raise ValueError(f".sti line {line_number} has an invalid value") from exc
        if not math.isfinite(value):
            raise ValueError(f".sti line {line_number} is nonfinite")
        row0, col0 = row1 - 1, col1 - 1
        key = upper_triangle_index(row0, col0, dimension)
        byte_index, bit_index = divmod(key, 8)
        bit = 1 << bit_index
        if seen[byte_index] & bit:
            raise ValueError(f".sti line {line_number} duplicates or mirrors pair {(row1, col1)}")
        seen[byte_index] |= bit
        pair_count += 1
        if row0 == col0:
            if diag_seen[row0]:
                raise ValueError(f".sti line {line_number} repeats diagonal {row1}")
            diag_seen[row0] = 1
        if value == 0.0:
            explicit_zero_count += 1
        else:
            upper_nonzero_count += 1
            symmetric_nonzero_count += 1 if row0 == col0 else 2
        left_owner, right_owner = owner_by_index[row0], owner_by_index[col0]
        if left_owner != right_owner:
            if value != 0.0:
                cross_body_nonzero_count += 1
                if len(cross_body_nonzero_examples) < 5:
                    cross_body_nonzero_examples.append([row1, col1, value, left_owner, right_owner])
                raise ValueError(f".sti has nonzero cross-body term at line {line_number}: {cross_body_nonzero_examples[-1]}")
            cross_body_zero_pair_count += 1
            continue
        target = left_owner
        if target not in target_indices:
            non_target_pair_count += 1
            continue
        local_row, local_col = local_maps[target][row0], local_maps[target][col0]
        rows[target].append(local_row)
        cols[target].append(local_col)
        values[target].append(value)
        block_pairs[target] += 1
        if value != 0.0:
            block_nonzero_pairs[target] += 1
        if row0 != col0:
            rows[target].append(local_col)
            cols[target].append(local_row)
            values[target].append(value)
    if expected_pair_count is not None and pair_count != expected_pair_count:
        raise ValueError(f".sti sparse upper-pair count {pair_count} differs from frozen count {expected_pair_count}")
    if not all(diag_seen):
        raise ValueError(".sti is missing one or more original stiffness diagonal entries")
    if expected_zero_pair_count is not None and explicit_zero_count != expected_zero_pair_count:
        raise ValueError(f".sti explicit-zero pair count {explicit_zero_count} differs from frozen count {expected_zero_pair_count}")
    if expected_symmetric_nonzero_count is not None and symmetric_nonzero_count != expected_symmetric_nonzero_count:
        raise ValueError(
            f".sti reconstructed symmetric nonzero count {symmetric_nonzero_count} differs from frozen count {expected_symmetric_nonzero_count}"
        )
    if expected_cross_body_nonzero_count is not None and cross_body_nonzero_count != expected_cross_body_nonzero_count:
        raise ValueError(f".sti cross-body nonzero count {cross_body_nonzero_count} differs from frozen count {expected_cross_body_nonzero_count}")
    blocks = {}
    for name, indices in target_indices.items():
        block = sp.coo_matrix((values[name], (rows[name], cols[name])), shape=(len(indices), len(indices))).tocsr()
        block.sum_duplicates()
        block.eliminate_zeros()
        delta = block - block.T
        asymmetry = float(np.max(np.abs(delta.data))) if delta.nnz else 0.0
        if asymmetry != 0.0 or block.shape != (len(indices), len(indices)):
            raise ValueError(f"target body K block failed symmetric/order reconstruction for {name}")
        if np.any(~np.isfinite(block.data)) or np.any(block.diagonal() <= 0.0):
            raise ValueError(f"target body K block has nonfinite/nonpositive diagonal for {name}")
        blocks[name] = block
    accounted_pair_count = sum(block_pairs.values()) + non_target_pair_count + cross_body_zero_pair_count
    if accounted_pair_count != pair_count:
        raise ValueError("sparse upper-pair accounting did not cover every accepted source pair")
    summary = {
        "global_dimension": dimension,
        "global_unique_upper_pair_count": pair_count,
        "expected_global_sparse_upper_pair_count": expected_pair_count,
        "possible_dense_upper_pair_capacity_not_required": pair_capacity,
        "explicit_zero_upper_pair_count": explicit_zero_count,
        "upper_nonzero_pair_count": upper_nonzero_count,
        "reconstructed_symmetric_nonzero_count": symmetric_nonzero_count,
        "expected_reconstructed_symmetric_nonzero_count": expected_symmetric_nonzero_count,
        "source_dof_order_verified": True,
        "all_original_diagonals_present": True,
        "cross_body_nonzero_pair_count": cross_body_nonzero_count,
        "cross_body_explicit_zero_pair_count": cross_body_zero_pair_count,
        "non_target_same_body_upper_pair_count": non_target_pair_count,
        "upper_pair_accounting_total": accounted_pair_count,
        "target_body_upper_pair_counts": block_pairs,
        "target_body_nonzero_upper_pair_counts": block_nonzero_pairs,
        "target_body_matrix_nnz_after_zero_elimination": {name: int(block.nnz) for name, block in blocks.items()},
        "global_stiffness_matrix_rebuilt": False,
        "maximum_stored_matrix_shape": max((block.shape for block in blocks.values()), key=lambda shape: shape[0]),
        "uniqueness_bitmap_bytes": len(seen),
    }
    return blocks, summary


def quotient_solve_core(K, R: np.ndarray, p: np.ndarray, qmethod, condensation,
                         *, max_corrections: int = MAX_CORRECTIONS_PER_BODY) -> dict:
    """Run the pinned method on one already-filtered body block."""
    global FACTOR_COUNT
    matrix = sp.csr_matrix(K, dtype=np.float64)
    basis = np.asarray(R, dtype=np.float64)
    load = np.asarray(p, dtype=np.float64)
    if matrix.shape != (basis.shape[0], basis.shape[0]) or basis.shape[1] != 6 or load.shape != (basis.shape[0],):
        raise ValueError("body-only K/R/p shapes do not agree")
    if not all(np.all(np.isfinite(value)) for value in (matrix.data, basis, load)):
        return {"status": "REJECT_NONFINITE_INPUT", "factorizations": 0}
    if max_corrections != MAX_CORRECTIONS_PER_BODY or max_corrections != qmethod.MAX_CORRECTIONS:
        raise ValueError("correction count differs from pinned five-step method limit")
    if np.finfo(np.longdouble).eps >= np.finfo(np.float64).eps:
        return {"status": "UNRESOLVED_EXTRA_PRECISION_UNAVAILABLE", "factorizations": 0}
    generalized = basis.T @ load
    balance_tolerance = 1.0e-10 + 1.0e-10 * max(1.0, float(np.linalg.norm(load, ord=1)))
    if float(np.max(np.abs(generalized))) > balance_tolerance:
        return {
            "status": qmethod.REJECT_UNBALANCED_BODY_WRENCH,
            "factorizations": 0,
            "R_transpose_p_scaled_N": generalized.tolist(),
            "balance_threshold_N": balance_tolerance,
            "projection_used_to_repair_physical_load": False,
        }
    operator = qmethod.audit_quotient_operator(matrix, basis)
    if operator.get("status") != qmethod.PASS_ELASTIC_QUOTIENT_SCREEN:
        return {"status": operator.get("status"), "factorizations": 0, "operator": operator}
    if FACTOR_COUNT >= MAX_BODY_FACTORIZATIONS:
        raise RuntimeError("two-factorization cap reached")
    FACTOR_COUNT += 1
    factor, system = condensation.factor_bordered(matrix, basis)
    result = qmethod.solve_quotient_chunk(
        factor, system, matrix, basis, load,
        max_corrections=MAX_CORRECTIONS_PER_BODY,
        operator_report=operator,
    )
    result["factorizations"] = 1
    result["cumulative_factorizations"] = FACTOR_COUNT
    result["max_corrections_allowed"] = MAX_CORRECTIONS_PER_BODY
    if int(result.get("corrections", 0)) > MAX_CORRECTIONS_PER_BODY:
        raise RuntimeError("pinned method exceeded the frozen correction limit")
    return result


def evaluate_mpc_network(equations: dict, physical_values: dict[tuple[int, int], float],
                          prescribed_values: dict[tuple[int, int], float]) -> dict[tuple[int, int], float]:
    """Evaluate dependent emitted MPC DOFs in dependency order using deck coefficients."""
    values = dict(physical_values)
    for key, value in prescribed_values.items():
        if key in values and values[key] != value:
            raise ValueError(f"prescribed DOF conflicts with physical solution at {key}")
        values[key] = float(value)
    pending = {}
    for key_text, terms_raw in equations.items():
        node_text, direction_text = key_text.split(".")
        key = (int(node_text), int(direction_text))
        if key in pending:
            raise ValueError(f"duplicate emitted MPC dependent DOF {key}")
        terms = [(int(node), int(direction), float(coefficient)) for node, direction, coefficient in terms_raw]
        if not terms or terms[0][:2] != key or terms[0][2] != 1.0:
            raise ValueError(f"unexpected emitted MPC dependent coefficient at {key}")
        if key in values:
            raise ValueError(f"MPC dependent DOF already seeded as independent: {key}")
        pending[key] = terms
    evaluated = {}
    while pending:
        progressed = False
        for key, terms in list(pending.items()):
            if all((node, direction) in values for node, direction, _ in terms[1:]):
                rhs = 0.0
                for node, direction, coefficient in terms[1:]:
                    rhs += coefficient * values[(node, direction)]
                value = -rhs / terms[0][2]
                if not math.isfinite(value):
                    raise ValueError(f"emitted MPC recovery became nonfinite at {key}")
                values[key] = value
                evaluated[key] = value
                del pending[key]
                progressed = True
        if not progressed:
            raise ValueError(f"emitted MPC network has unresolved upstream DOFs: {sorted(pending)}")
    return evaluated


def parse_deck_nodes(text: str, wanted: set[int]) -> dict[int, np.ndarray]:
    nodes = {}
    in_node_section = False
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.upper().startswith("*NODE"):
            in_node_section = True
            continue
        if stripped.startswith("*"):
            in_node_section = False
        if in_node_section and stripped:
            fields = [field.strip() for field in stripped.split(",")]
            if len(fields) >= 4 and fields[0].isdigit() and int(fields[0]) in wanted:
                nodes[int(fields[0])] = np.asarray([float(value) for value in fields[1:4]], dtype=np.float64)
    if set(nodes) != wanted:
        raise ValueError(f"emitted target deck nodes missing: {sorted(wanted - set(nodes))}")
    return nodes


def parse_target_element_and_table(text: str) -> tuple[list[int], list[tuple[float, float]]]:
    lines = text.splitlines()
    connectivity = None
    table = []
    in_element = False
    in_spring = False
    for line in lines:
        stripped = line.strip()
        upper = stripped.upper()
        if upper.startswith("*"):
            in_element = upper == "*ELEMENT,TYPE=SPRINGA,ELSET=SPR1787"
            in_spring = upper == "*SPRING,ELSET=SPR1787,NONLINEAR"
            continue
        if not stripped:
            continue
        if in_element:
            fields = [piece.strip() for piece in stripped.split(",")]
            if fields[0].isdigit() and int(fields[0]) == TARGET_ELEMENT:
                connectivity = [int(fields[1]), int(fields[2])]
        if in_spring:
            fields = [piece.strip() for piece in stripped.split(",")]
            if len(fields) == 2:
                try:
                    table.append((float(fields[0]), float(fields[1])))
                except ValueError:
                    continue
    if connectivity != [21300, 21301] or len(table) != 3:
        raise ValueError("target SPRINGA identity/table differs from frozen emitted deck")
    return connectivity, table


def spring_force_from_table(displacement_mm: float, force_displacement_rows: list[tuple[float, float]]) -> float:
    """Follow CCX's tabular interpolation: input deck stores force, displacement."""
    xiso = [float(displacement) for _force, displacement in force_displacement_rows]
    yiso = [float(force) for force, _displacement in force_displacement_rows]
    if len(xiso) < 2 or any(xiso[i] >= xiso[i + 1] for i in range(len(xiso) - 1)):
        raise ValueError("target nonlinear SPRING table is not strictly displacement ordered")
    if displacement_mm < xiso[0]:
        return yiso[0]
    if displacement_mm > xiso[-1]:
        return yiso[-1]
    for index in range(len(xiso) - 1):
        if xiso[index] <= displacement_mm <= xiso[index + 1]:
            stiffness = (yiso[index + 1] - yiso[index]) / (xiso[index + 1] - xiso[index])
            return yiso[index] + stiffness * (displacement_mm - xiso[index])
    raise ValueError("target table interpolation failed to locate a displacement interval")


def vector_length(vector: Iterable[float]) -> float:
    values = tuple(float(value) for value in vector)
    if len(values) != 3:
        raise ValueError("endpoint vector must be length three")
    # Keep the CCX source operation order: square components, sum, square root.
    return math.sqrt(values[0] * values[0] + values[1] * values[1] + values[2] * values[2])


def endpoint_metrics(x1: np.ndarray, x2: np.ndarray, u1: np.ndarray, u2: np.ndarray,
                     table: list[tuple[float, float]]) -> dict:
    initial = tuple(float(x2[i] - x1[i]) for i in range(3))
    dd0 = vector_length(initial)
    if dd0 <= 0.0:
        raise ValueError("emitted SPRINGA initial span is zero")
    p1 = tuple(float(x1[i] + u1[i]) for i in range(3))
    p2 = tuple(float(x2[i] + u2[i]) for i in range(3))
    current = tuple(float(p2[i] - p1[i]) for i in range(3))
    dd = vector_length(current)
    elongation = float(dd - dd0)
    force = spring_force_from_table(elongation, table)
    axis = tuple(value / dd0 for value in initial)
    q_axis = sum(axis[i] * float(u2[i] - u1[i]) for i in range(3))
    return {
        "initial_relative_vector_mm": list(initial),
        "initial_length_dd0_mm": dd0,
        "current_endpoint1_mm": list(p1),
        "current_endpoint2_mm": list(p2),
        "current_length_dd_mm": dd,
        "finite_span_dd_minus_dd0_mm": elongation,
        "linear_endpoint_axis_projection_mm": q_axis,
        "table_force_N": force,
        "endpoint_operation_order": "pl_i=xl_i+u_i; dd0=norm(xl2-xl1); dd=norm(pl2-pl1); val=dd-dd0",
    }


def output_report(path: Path, value: dict) -> None:
    resolved = validate_output_path(path)
    resolved.parent.mkdir(parents=True, exist_ok=True)
    resolved.write_text(json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8")


def validate_output_path(path: Path) -> Path:
    resolved = path.resolve()
    if resolved == ROOT or ROOT in resolved.parents:
        raise RuntimeError("runner reports must remain outside the repository workspace")
    return resolved


def _wall_alarm(signum, frame):
    del signum, frame
    raise TimeoutError("60-second wall-clock budget reached")


def enforce_resource_caps() -> dict:
    _cpu_soft, cpu_hard = resource.getrlimit(resource.RLIMIT_CPU)
    cpu_target = MAX_CPU_SECONDS if cpu_hard == resource.RLIM_INFINITY else min(MAX_CPU_SECONDS, int(cpu_hard))
    if cpu_target <= 0:
        raise RuntimeError("OS CPU hard limit leaves no execution budget")
    resource.setrlimit(resource.RLIMIT_CPU, (cpu_target, cpu_target))
    _as_soft, as_hard = resource.getrlimit(resource.RLIMIT_AS)
    address_target = MAX_ADDRESS_SPACE_BYTES if as_hard == resource.RLIM_INFINITY else min(MAX_ADDRESS_SPACE_BYTES, int(as_hard))
    if address_target <= 0:
        raise RuntimeError("OS address-space hard limit leaves no execution budget")
    resource.setrlimit(resource.RLIMIT_AS, (address_target, address_target))
    signal.signal(signal.SIGALRM, _wall_alarm)
    signal.setitimer(signal.ITIMER_REAL, MAX_WALL_SECONDS)
    return {
        "cpu_hard_limit_seconds": cpu_target,
        "wall_alarm_seconds": MAX_WALL_SECONDS,
        "address_space_limit_bytes": address_target,
        "threads_per_blas_pool": 1,
    }


def consume_parent_run_slot(approval_path: Path) -> str:
    resolved = approval_path.resolve()
    if resolved == ROOT or ROOT in resolved.parents:
        raise RuntimeError("parent approval record must be outside the repository")
    approval = load_json(resolved)
    runner_sha = sha_file(Path(__file__).resolve())
    expected = {
        "schema": "a12_row1586_endpoint_recovery_parent_approval/v1",
        "approved": True,
        "preparation_readiness_sha256": READINESS_SHA256,
        "runner_sha256": runner_sha,
        "source_pin_manifest_sha256": PIN_MANIFEST_SHA256,
        "scope": "two_target_bodies_row_1586_only",
    }
    if approval != expected:
        raise RuntimeError("parent approval record is missing or does not match this reviewed readiness")
    digest = sha_file(resolved)
    descriptor = os.open(RUN_MARKER, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
        json.dump({"approval_sha256": digest, "readiness_sha256": READINESS_SHA256,
                   "runner_sha256": runner_sha, "source_pin_manifest_sha256": PIN_MANIFEST_SHA256,
                   "consumed": True}, stream)
        stream.write("\n")
    return digest


def make_toy_matrix() -> tuple[np.ndarray, np.ndarray, list[tuple[int, int]], dict[int, list[float]], list[str]]:
    xyz = np.asarray([[0.0, 0.0, 0.0], [1000.0, 0.0, 0.0],
                      [0.0, 1000.0, 0.0], [0.0, 0.0, 1000.0]], dtype=np.float64)
    labels = [(node, direction) for node in range(1, 5) for direction in (1, 2, 3)]
    center = np.mean(xyz, axis=0)
    R = np.zeros((12, 6), dtype=np.float64)
    eye = np.eye(3)
    for node_index, point in enumerate(xyz):
        relative = point - center
        for direction in range(3):
            R[3 * node_index + direction, direction] = 1.0
            for axis in range(3):
                R[3 * node_index + direction, 3 + axis] = np.cross(eye[axis], relative)[direction] / ROTATION_SCALE_MM
    dense = np.zeros((12, 12), dtype=np.float64)
    for i in range(4):
        for j in range(i + 1, 4):
            delta = xyz[j] - xyz[i]
            direction = delta / np.linalg.norm(delta)
            block = np.outer(direction, direction)
            si, sj = slice(3 * i, 3 * i + 3), slice(3 * j, 3 * j + 3)
            dense[si, si] += block
            dense[sj, sj] += block
            dense[si, sj] -= block
            dense[sj, si] -= block
    triplets = []
    for row in range(12):
        for col in range(row, 12):
            if dense[row, col] != 0.0:
                triplets.append(f"{row + 1} {col + 1} {dense[row, col]:.17g}\n")
    if dense[0, 4] != 0.0:
        raise AssertionError("toy explicit-zero pair is not a structural zero")
    triplets.append("1 5 0.0\n")
    return dense, R, labels, {i + 1: xyz[i].tolist() for i in range(4)}, triplets


def synthetic_sparse_filter_check() -> dict:
    lines = [
        "1 1 4.0\n", "1 2 -1.0\n", "2 2 4.0\n",
        "2 3 0.0\n", "3 3 5.0\n", "3 4 1.0\n", "4 4 6.0\n",
    ]
    owners = ["target", "target", "other", "other"]
    blocks, report = filter_upper_triangle(
        lines, 4, owners, {"target": [0, 1]},
        expected_pair_count=7,
        expected_zero_pair_count=1,
        expected_symmetric_nonzero_count=8,
        expected_cross_body_nonzero_count=0,
    )
    expected = np.asarray([[4.0, -1.0], [-1.0, 4.0]])
    if set(blocks) != {"target"} or not np.array_equal(blocks["target"].toarray(), expected):
        raise AssertionError("sparse selected-body extraction or symmetry reconstruction failed")
    if report["target_body_upper_pair_counts"] != {"target": 3}:
        raise AssertionError("sparse target-block observed pair count is incorrect")
    if report["non_target_same_body_upper_pair_count"] != 3 or report["cross_body_explicit_zero_pair_count"] != 1:
        raise AssertionError("sparse target/non-target/cross-body-zero pair accounting failed")
    if report["upper_pair_accounting_total"] != len(lines):
        raise AssertionError("sparse global pair accounting did not close")

    def must_reject(name: str, candidate_lines: list[str], candidate_owners: list[str],
                    candidate_indices: dict[str, list[int]]) -> None:
        try:
            filter_upper_triangle(candidate_lines, len(candidate_owners), candidate_owners, candidate_indices)
        except ValueError:
            return
        raise AssertionError(f"sparse filter failed to reject {name}")

    must_reject("duplicate upper pair", ["1 1 1\n", "1 2 0.5\n", "1 2 0.5\n"],
                ["target", "target"], {"target": [0, 1]})
    must_reject("wrong body DOF ownership", lines, owners, {"target": [0, 2]})
    must_reject("nonzero cross-body pair", [line.replace("2 3 0.0", "2 3 0.25") for line in lines],
                owners, {"target": [0, 1]})
    return {
        "status": "PASS_SPARSE_SELECTED_BLOCK_FIXTURE",
        "input_upper_pair_count": len(lines),
        "input_dense_upper_pair_capacity": 10,
        "target_observed_upper_pair_count": 3,
        "target_reconstructed_matrix_nnz": int(blocks["target"].nnz),
        "absent_structural_zero_pairs_allowed": True,
        "explicit_cross_body_zero_allowed": True,
        "non_target_block_not_materialized": True,
        "duplicate_pair_rejected": True,
        "wrong_owner_map_rejected": True,
        "nonzero_cross_body_pair_rejected": True,
    }


def toy_check() -> dict:
    pins = verify_pins()
    snapshot = source_snapshot(pins, replay=True)
    qmethod_path = ROOT / "docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/current-elastic-quotient-method-preflight-attempt02/quotient_method.py"
    condensation_path = ROOT / "docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/current-frame-free-body-condensation-preflight-attempt01/condensation.py"
    qmethod = import_module(qmethod_path, "a12_toy_quotient_method")
    condensation = import_module(condensation_path, "a12_toy_condensation")
    dense, R, labels, xyz, triplets = make_toy_matrix()
    owners = ["toy_body"] * 12
    target_indices = {"toy_body": list(range(12))}
    blocks, matrix_report = filter_upper_triangle(
        triplets, 12, owners, target_indices,
        expected_pair_count=len(triplets),
        expected_zero_pair_count=1,
        expected_symmetric_nonzero_count=int(np.count_nonzero(dense)),
        expected_cross_body_nonzero_count=0,
    )
    reconstructed = blocks["toy_body"].toarray()
    if not np.array_equal(reconstructed, dense):
        raise AssertionError("toy upper-triangle body block differs from constructed answer")
    alpha = 0.01
    expected_u = (alpha * (np.asarray(list(xyz.values())) - np.mean(np.asarray(list(xyz.values())), axis=0))).reshape(-1)
    p = dense @ expected_u
    global FACTOR_COUNT
    previous_factor_count = FACTOR_COUNT
    FACTOR_COUNT = 0
    solved = quotient_solve_core(blocks["toy_body"], R, p, qmethod, condensation)
    toy_factorizations = FACTOR_COUNT
    FACTOR_COUNT = previous_factor_count
    if solved.get("status") != qmethod.PASS_ELASTIC_QUOTIENT_SCREEN or toy_factorizations != 1:
        raise AssertionError(f"toy quotient core failed known answer: {solved.get('status')}")
    observed_u = np.asarray(solved["displacement_mm"], dtype=np.float64).reshape(-1)
    error = float(np.max(np.abs(observed_u - expected_u)))
    if error > 1.0e-9:
        raise AssertionError(f"toy recovered elastic field differs from prescribed answer: {error}")

    # Recover physical fields as u=R*a+u_elastic, back-project one source B
    # row, then interpolate both endpoint vectors through a recursive MPC set.
    rigid_coordinates = np.asarray([0.12, -0.04, 0.08, 0.003, -0.002, 0.004], dtype=np.float64)
    expected_full = expected_u + R @ rigid_coordinates
    observed_full = observed_u + R @ rigid_coordinates
    rigid_recovery_error = float(np.max(np.abs(observed_full - expected_full)))
    if rigid_recovery_error > 1.0e-9:
        raise AssertionError(f"toy physical field u=R*a+u_elastic differs from answer: {rigid_recovery_error}")
    physical_values = {
        label: float(observed_full[index]) for index, label in enumerate(labels)
    }
    equations = {}
    for direction in (1, 2, 3):
        equations[f"101.{direction}"] = [
            [101, direction, 1.0], [1, direction, -0.25], [2, direction, -0.75],
        ]
        equations[f"102.{direction}"] = [
            [102, direction, 1.0], [3, direction, -0.5], [4, direction, -0.5],
        ]
        equations[f"103.{direction}"] = [
            [103, direction, 1.0], [101, direction, -0.5], [102, direction, -0.5],
        ]
    mpc_values = evaluate_mpc_network(equations, physical_values, {})
    expected_endpoint1 = 0.25 * expected_full[0:3] + 0.75 * expected_full[3:6]
    expected_endpoint2 = 0.5 * expected_full[6:9] + 0.5 * expected_full[9:12]
    observed_endpoint1 = np.asarray([mpc_values[(101, direction)] for direction in (1, 2, 3)])
    observed_endpoint2 = np.asarray([mpc_values[(102, direction)] for direction in (1, 2, 3)])
    endpoint_recovery_error = float(max(
        np.max(np.abs(observed_endpoint1 - expected_endpoint1)),
        np.max(np.abs(observed_endpoint2 - expected_endpoint2)),
    ))
    if endpoint_recovery_error > 1.0e-9:
        raise AssertionError(f"toy endpoint vectors differ from prescribed answer: {endpoint_recovery_error}")
    initial1 = 0.25 * np.asarray(xyz[1]) + 0.75 * np.asarray(xyz[2])
    initial2 = 0.5 * np.asarray(xyz[3]) + 0.5 * np.asarray(xyz[4])
    axis = initial2 - initial1
    axis /= np.linalg.norm(axis)
    B = np.zeros(12, dtype=np.float64)
    for component in range(3):
        B[component] -= 0.25 * axis[component]
        B[3 + component] -= 0.75 * axis[component]
        B[6 + component] += 0.5 * axis[component]
        B[9 + component] += 0.5 * axis[component]
    q_backprojected = float(B @ observed_full)
    expected_q = float(axis @ (expected_endpoint2 - expected_endpoint1))
    q_recovery_error = abs(q_backprojected - expected_q)
    if q_recovery_error > 1.0e-9:
        raise AssertionError(f"toy endpoint displacement does not back-project through B: {q_recovery_error}")
    table = [(0.0, -20.0), (0.0, 0.0), (200.0, 20.0)]
    metrics = endpoint_metrics(initial1, initial2, observed_endpoint1, observed_endpoint2, table)
    expected_current1 = initial1 + expected_endpoint1
    expected_current2 = initial2 + expected_endpoint2
    expected_dd0 = vector_length(initial2 - initial1)
    expected_dd = vector_length(expected_current2 - expected_current1)
    expected_extension = float(expected_dd - expected_dd0)
    expected_force = spring_force_from_table(expected_extension, table)
    endpoint_scalar_error = max(
        abs(metrics["finite_span_dd_minus_dd0_mm"] - expected_extension),
        abs(metrics["table_force_N"] - expected_force),
        abs(metrics["linear_endpoint_axis_projection_mm"] - expected_q),
    )
    if endpoint_scalar_error > 1.0e-9:
        raise AssertionError(f"toy binary64 span/table or B-u back-projection differs: {endpoint_scalar_error}")
    sparse_filter_report = synthetic_sparse_filter_check()
    return {
        "schema": "a12_row1586_endpoint_recovery_runner_toy_check/v1",
        "status": "PASS_SYNTHETIC_RUNNER_CORE_ONLY",
        "source_snapshot_verified": True,
        "verified_calculix_spring_source": snapshot["kernel_source"],
        "source_stiffness_checksum_read": True,
        "source_stiffness_triplets_parsed": False,
        "actual_source_K_filtered": False,
        "actual_source_factorizations": 0,
        "actual_source_body_states_solved": 0,
        "native_runs": 0,
        "synthetic_matrix": matrix_report,
        "synthetic_quotient_method_status": solved["status"],
        "synthetic_factorizations": toy_factorizations,
        "max_prescribed_elastic_displacement_error_mm": error,
        "max_recovered_physical_field_error_mm": rigid_recovery_error,
        "max_recovered_endpoint_vector_error_mm": endpoint_recovery_error,
        "B_u_backprojection_error_mm": q_recovery_error,
        "endpoint_scalar_reconstruction_error": endpoint_scalar_error,
        "toy_recursive_MPC_values_mm": {f"{node}.{direction}": value for (node, direction), value in mpc_values.items()},
        "toy_finite_span": metrics,
        "synthetic_sparse_filter": sparse_filter_report,
    }


def summarize_body_result(body: str, layout: dict, body_load: dict, result: dict) -> dict:
    return {
        "body": body,
        "rigid_coordinate_index": layout["body_id"],
        "physical_node_count": len(layout["nodes"]),
        "physical_dof_count": len(layout["global_indices"]),
        "node_mean_rigid_basis_reference_mm": layout["center_mm"].tolist(),
        "native_dof_order_sha256_i64le": sha_bytes(np.asarray(layout["global_indices"], dtype="<i8").tobytes()),
        "R_shape": list(layout["R"].shape),
        "unmodified_raw_load_sha256_f64le": sha_bytes(np.asarray(body_load["p"], dtype="<f8").tobytes()),
        "external_gravity_sha256_f64le": sha_bytes(np.asarray(body_load["gravity"], dtype="<f8").tobytes()),
        "external_climber_sha256_f64le": sha_bytes(np.asarray(body_load["climber"], dtype="<f8").tobytes()),
        "R_transpose_p_scaled_N": body_load["generalized_wrench_scaled_N"].tolist(),
        "raw_load_to_saved_Dtf_minus_W_max_error_scaled_N": body_load["closure_error_scaled_N"],
        "balance_threshold_N": body_load["balance_threshold_N"],
        "method_status": result.get("status"),
        "failed_method_gates": result.get("failed_gates", []),
        "operator_screen": result.get("operator"),
        "max_corrections_used": result.get("corrections", 0),
        "refinement_history": result.get("refinement_history", []),
        "method_result_summary": {key: result[key] for key in (
            "KKT_upper_force_residual_relative", "max_projected_elastic_force_residual_N",
            "projected_elastic_force_residual_relative", "max_gauge_R_transpose_u_mm",
            "max_abs_original_Ku_minus_p_N", "max_abs_R_transpose_original_Ku_minus_p_scaled_N",
            "rigid_identity_closure", "legacy_zero_lambda_gate", "physical_response_accepted",
        ) if key in result},
    }


def stop_report(status: str, snapshot: dict, *, mpc_errors: dict, matrix_report: dict | None,
                body_results: dict, factor_count: int, approval_sha256: str,
                resource_report: dict) -> dict:
    return {
        "schema": "a12_row1586_endpoint_recovery_result/v1",
        "status": status,
        "target": {"source_position": TARGET_ROW, "group": TARGET_GROUP, "element": TARGET_ELEMENT,
                   "source_inventory_row_index": 1786, "owners": list(TARGET_OWNERS)},
        "candidate": snapshot["preflight"]["scope"]["candidate"],
        "geometry_revision_id": snapshot["preflight"]["scope"]["geometry_revision_id"],
        "prepared_runner_sha256": sha_file(Path(__file__).resolve()),
        "source_pin_manifest_sha256": PIN_MANIFEST_SHA256,
        "original_raw_H_status": snapshot["preflight"]["prior_stop"]["raw_H_status"],
        "unchanged_original_force_interval_failures": snapshot["preflight"]["prior_stop"]["unchanged_failed_force_intervals"],
        "body_results_before_stop": body_results,
        "matrix_filter": matrix_report,
        "MPC_validation": mpc_errors,
        "resource_and_execution": {"parent_approval_sha256": approval_sha256,
                                    "resource_caps": resource_report,
                                    "source_K_triplet_parse_passes": 1 if matrix_report else 0,
                                    "body_factorizations_used": factor_count,
                                    "body_factorizations_max": MAX_BODY_FACTORIZATIONS,
                                    "native_runs": 0,
                                    "global_K_rebuilt": False},
        "raw_H_STOP_retained": True,
        "mechanical_acceptance": False,
    }


def run_actual(approval_path: Path, report_path: Path) -> dict:
    caps = enforce_resource_caps()
    start_cpu = time.process_time()
    start_wall = time.monotonic()
    pins = verify_pins()
    snapshot = source_snapshot(pins, replay=True)
    layouts = build_body_layouts(snapshot)
    d_errors = verify_body_rigid_operator(snapshot, layouts)
    body_loads = build_raw_body_loads(snapshot, layouts)
    for body in TARGET_OWNERS:
        if not body_loads[body]["balanced_before_factorization"]:
            raise RuntimeError(f"unchanged raw load fails the pinned quotient balance gate before K filtering: {body}")
    if np.__version__ != "2.5.2" or scipy.__version__ != "1.18.1":
        raise RuntimeError(f"pinned solver-library versions changed: NumPy {np.__version__}, SciPy {scipy.__version__}")
    runner_sha = sha_file(Path(__file__).resolve())
    approval_sha = consume_parent_run_slot(approval_path)
    matrix_path = ROOT / "docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/current-frame-pure-solid-matrix-export-native-attempt01/model.sti"
    matrix_assessment = snapshot["matrix_assessment"]
    with matrix_path.open("r", encoding="ascii") as matrix_stream:
        blocks, matrix_report = filter_upper_triangle(
            matrix_stream, 37647, snapshot["owner_by_global"],
            {body: layout["global_indices"] for body, layout in layouts.items()},
            expected_pair_count=matrix_assessment["stiffness"]["triangle_pair_count"],
            expected_zero_pair_count=matrix_assessment["stiffness"]["explicit_zero_triangle_pair_count"],
            expected_symmetric_nonzero_count=matrix_assessment["stiffness"]["reconstructed_symmetric_nonzero_count"],
            expected_cross_body_nonzero_count=matrix_assessment["stiffness"]["cross_body_nonzero_pair_count"],
        )
    matrix_report["target_body_csr_sha256"] = {body: csr_sha256(block) for body, block in blocks.items()}
    if sha_file(matrix_path) != pins["model.sti"]:
        raise RuntimeError("original K hash changed during single stream/filter pass")
    qmethod = import_module(ROOT / "docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/current-elastic-quotient-method-preflight-attempt02/quotient_method.py", "a12_parent_quotient_method")
    condensation = import_module(ROOT / "docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/current-frame-free-body-condensation-preflight-attempt01/condensation.py", "a12_parent_condensation")
    body_results = {}
    physical_values = {}
    for body in TARGET_OWNERS:
        layout, body_load = layouts[body], body_loads[body]
        result = quotient_solve_core(blocks[body], layout["R"], body_load["p"], qmethod, condensation)
        body_results[body] = summarize_body_result(body, layout, body_load, result)
        if result.get("status") != qmethod.PASS_ELASTIC_QUOTIENT_SCREEN:
            report = stop_report("STOP_FIRST_METHOD_GATE_FAILURE", snapshot, mpc_errors=d_errors,
                                 matrix_report=matrix_report, body_results=body_results,
                                 factor_count=FACTOR_COUNT, approval_sha256=approval_sha,
                                 resource_report=caps)
            report["timing"] = {"cpu_seconds": time.process_time() - start_cpu,
                                "wall_seconds": time.monotonic() - start_wall}
            output_report(report_path, report)
            return report
        u_elastic = np.asarray(result["displacement_mm"], dtype=np.float64)
        a_slice = snapshot["raw"]["a_mm"][6 * layout["body_id"]:6 * layout["body_id"] + 6].astype(np.float64)
        u_full = u_elastic + layout["R"] @ a_slice
        if not np.all(np.isfinite(u_full)):
            report = stop_report("STOP_NONFINITE_RECOVERED_BODY_FIELD", snapshot, mpc_errors=d_errors,
                                 matrix_report=matrix_report, body_results=body_results,
                                 factor_count=FACTOR_COUNT, approval_sha256=approval_sha,
                                 resource_report=caps)
            output_report(report_path, report)
            return report
        body_results[body]["raw_rigid_coordinates_sha256_f64le"] = sha_bytes(np.asarray(a_slice, dtype="<f8").tobytes())
        body_results[body]["elastic_field_sha256_f64le"] = sha_bytes(np.asarray(u_elastic, dtype="<f8").tobytes())
        body_results[body]["physical_field_sha256_f64le"] = sha_bytes(np.asarray(u_full, dtype="<f8").tobytes())
        body_results[body]["max_abs_elastic_displacement_mm"] = float(np.max(np.abs(u_elastic)))
        body_results[body]["max_abs_physical_displacement_mm"] = float(np.max(np.abs(u_full)))
        for local_index, (node, direction) in enumerate(layout["labels"]):
            physical_values[(node, direction)] = float(u_full[local_index])

    deck_path = ROOT / "docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/current-springa-selected-floor-a12-rear-attempt03/model.inp"
    deck_text = deck_path.read_text(encoding="ascii")
    coords = parse_deck_nodes(deck_text, {18266, 18267, 18268, 18269, 21300, 21301})
    connectivity, table = parse_target_element_and_table(deck_text)
    if "21301,1,3,0" not in deck_text:
        raise RuntimeError("target numerical ground is not fixed by emitted SPC")
    equations = snapshot["preflight"]["unmodified_MPC_reconstruction"]["equations_from_emitted_model_inp"]
    evaluated = evaluate_mpc_network(equations, physical_values,
                                     {(21301, direction): 0.0 for direction in (1, 2, 3)})
    required_dependents = {(node, direction) for node in (18266, 18267, 18268, 18269, 21300) for direction in (1, 2, 3)}
    if set(evaluated) != required_dependents:
        report = stop_report("STOP_INCOMPLETE_EMITTED_MPC_RECOVERY", snapshot, mpc_errors=d_errors,
                             matrix_report=matrix_report, body_results=body_results,
                             factor_count=FACTOR_COUNT, approval_sha256=approval_sha,
                             resource_report=caps)
        output_report(report_path, report)
        return report
    displacements = {node: np.asarray([evaluated[(node, direction)] for direction in (1, 2, 3)], dtype=np.float64)
                     for node in (18266, 18267, 18268, 18269, 21300)}
    displacements[21301] = np.zeros(3, dtype=np.float64)
    spring = endpoint_metrics(coords[connectivity[0]], coords[connectivity[1]],
                              displacements[connectivity[0]], displacements[connectivity[1]], table)
    expected_dd0 = float(snapshot["preflight"]["unmodified_MPC_reconstruction"]["springa"]["dd0_from_emitted_deck_mm"])
    if abs(spring["initial_length_dd0_mm"] - expected_dd0) > 1.0e-12:
        raise RuntimeError("emitted target spring initial span differs from pinned preflight")
    row = snapshot["projection"]["rows"][TARGET_ROW]
    if row["source_group"] != TARGET_GROUP or row["source_element"] != TARGET_ELEMENT:
        raise RuntimeError("target connector row identity changed")
    q_linear = 0.0
    physical_map = snapshot["physical_map"]
    owner_counts = {body: 0 for body in TARGET_OWNERS}
    for term in row["physical_sparse_row"]:
        coordinate = int(term["coordinate_index"])
        physical = physical_map[coordinate // 3]
        body = physical["body"]
        if body not in owner_counts:
            raise RuntimeError("target physical projection acquired an unbounded body owner")
        label = (int(physical["node"]), coordinate % 3 + 1)
        q_linear += float(term["coefficient"]) * physical_values[label]
        owner_counts[body] += 1
    if owner_counts != {TARGET_OWNERS[0]: 40, TARGET_OWNERS[1]: 40}:
        raise RuntimeError("target physical B row support changed")
    native_row = snapshot["native_response_row"]
    rf, rf_radius = float(native_row["native_endpoint_internal_force_N"]), float(native_row["native_endpoint_internal_radius_N"])
    rf_interval = [rf - rf_radius, rf + rf_radius]
    force_inside_rf = rf_interval[0] <= spring["table_force_N"] <= rf_interval[1]
    table_interval = [float(value) for value in native_row["native_table_force_interval_N"]]
    table_interval_match = table_interval[0] <= spring["table_force_N"] <= table_interval[1]
    source_match_status = "PASS_ROW1586_WITHIN_UNCHANGED_NATIVE_RF_INTERVAL" if force_inside_rf else "ROW1586_OUTSIDE_UNCHANGED_NATIVE_RF_INTERVAL"
    report = {
        "schema": "a12_row1586_endpoint_recovery_result/v1",
        "status": "METHOD_PASS_SOURCE_ROW_RF_MATCH" if force_inside_rf else "METHOD_PASS_SOURCE_ROW_RF_MISS",
        "candidate": snapshot["preflight"]["scope"]["candidate"],
        "geometry_revision_id": snapshot["preflight"]["scope"]["geometry_revision_id"],
        "prepared_runner_sha256": runner_sha,
        "source_pin_manifest_sha256": PIN_MANIFEST_SHA256,
        "target": {"source_position": TARGET_ROW, "group": TARGET_GROUP, "element": TARGET_ELEMENT,
                   "source_inventory_row_index": 1786, "owners": list(TARGET_OWNERS)},
        "source_method_status": "PASS_ELASTIC_QUOTIENT_SCREEN",
        "source_row_comparison_status": source_match_status,
        "source_row_comparison_is_mechanical_acceptance": False,
        "original_raw_H_status": snapshot["preflight"]["prior_stop"]["raw_H_status"],
        "unchanged_original_force_interval_failures": snapshot["preflight"]["prior_stop"]["unchanged_failed_force_intervals"],
        "raw_force_at_target_row_N": float(snapshot["raw"]["f_full_N"][TARGET_ROW]),
        "raw_body_gate_at_operator_node_mean": "PASS_UNCHANGED_0.1N_2NMM_ALL_50_BODIES",
        "body_results": body_results,
        "matrix_filter": matrix_report,
        "B_times_u_linear_projection_q_mm": float(q_linear),
        "exact_emitted_MPC_downstream_displacements_mm": {f"{node}.{direction}": float(value) for (node, direction), value in evaluated.items()},
        "emitted_spring_coordinates_mm": {str(node): coords[node].tolist() for node in connectivity},
        "spring_endpoint_connectivity": connectivity,
        "finite_span_and_table": spring,
        "native_RF_comparison": {
            "original_native_endpoint_RF_center_N": rf,
            "unchanged_native_endpoint_RF_rounding_radius_N": rf_radius,
            "unchanged_native_endpoint_RF_interval_N": rf_interval,
            "recovered_table_force_inside_unchanged_RF_interval": bool(force_inside_rf),
            "native_table_force_center_from_saved_case_N": float(native_row["native_table_force_N_from_actual_dd_minus_dd0"]),
            "native_table_force_interval_N": table_interval,
            "recovered_table_force_inside_native_table_interval": bool(table_interval_match),
        },
        "resource_and_execution": {
            "parent_approval_sha256": approval_sha,
            "resource_caps": caps,
            "source_K_triplet_parse_passes": 1,
            "body_factorizations_max": MAX_BODY_FACTORIZATIONS,
            "body_factorizations_used": FACTOR_COUNT,
            "max_existing_method_corrections_per_body": MAX_CORRECTIONS_PER_BODY,
            "native_runs": 0,
            "global_K_rebuilt": False,
            "full_frame_state_solved": False,
        },
        "disposition": {"source_force_adoption": False, "gate_or_interval_changes": False,
                        "new_case_or_state_selection": False, "physical_or_design_acceptance": False,
                        "global_rebuild": False, "raw_H_STOP_retained": True,
                        "raw_state_vectors_copied_to_report": False},
        "timing": {"cpu_seconds": time.process_time() - start_cpu,
                   "wall_seconds": time.monotonic() - start_wall},
    }
    output_report(report_path, report)
    return report


def read_only_preparation_report() -> dict:
    pins = verify_pins()
    snapshot = source_snapshot(pins, replay=True)
    layouts = build_body_layouts(snapshot)
    d_errors = verify_body_rigid_operator(snapshot, layouts)
    loads = build_raw_body_loads(snapshot, layouts)
    return {
        "schema": "a12_row1586_endpoint_recovery_runner_preparation/v1",
        "status": "READY_FOR_PARENT_INDEPENDENT_REVIEW_NO_SOURCE_RECOVERY",
        "pinned_readiness_sha256": READINESS_SHA256,
        "prepared_runner_sha256": sha_file(Path(__file__).resolve()),
        "source_pin_manifest_sha256": PIN_MANIFEST_SHA256,
        "input_file_count": len(pins),
        "verified_calculix_spring_source": snapshot["kernel_source"],
        "candidate": snapshot["preflight"]["scope"]["candidate"],
        "geometry_revision_id": snapshot["preflight"]["scope"]["geometry_revision_id"],
        "target_row": TARGET_ROW,
        "target_owners": {body: {"physical_nodes": len(layouts[body]["nodes"]),
                                  "physical_dofs": len(layouts[body]["global_indices"]),
                                  "body_index": layouts[body]["body_id"],
                                  "raw_load_Rt_p_scaled_N": loads[body]["generalized_wrench_scaled_N"].tolist(),
                                  "load_balance_gate_passes_before_factor": loads[body]["balanced_before_factorization"]}
                           for body in TARGET_OWNERS},
        "independent_B_R_to_D_max_difference": d_errors,
        "original_raw_H_status": snapshot["preflight"]["prior_stop"]["raw_H_status"],
        "unchanged_force_interval_failures": snapshot["preflight"]["prior_stop"]["unchanged_failed_force_intervals"],
        "original_all_body_0_1N_2Nmm_gate_passes": snapshot["raw_all_body_gate_passed"],
        "actual_source_K_filtered": False,
        "source_stiffness_checksum_read": True,
        "source_stiffness_triplets_parsed": False,
        "actual_K_factorizations": 0,
        "actual_body_state_solutions": 0,
        "native_runs": 0,
        "resource_budget": {"cpu_seconds_max": MAX_CPU_SECONDS,
                            "wall_seconds_max": MAX_WALL_SECONDS,
                            "address_space_bytes_max": MAX_ADDRESS_SPACE_BYTES,
                            "parent_recovery_invocations_max": MAX_PARENT_RUNS,
                            "body_factorizations_max": MAX_BODY_FACTORIZATIONS,
                            "existing_method_corrections_per_body_max": MAX_CORRECTIONS_PER_BODY},
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--verify-preparation", action="store_true",
                      help="verify pinned source preparation only; never extract K or solve")
    mode.add_argument("--toy-check", action="store_true",
                      help="factor only the small synthetic known-answer fixture")
    mode.add_argument("--execute", action="store_true",
                      help="run the one-shot two-body source recovery after parent approval")
    parser.add_argument("--parent-approval", type=Path,
                        help="external approval JSON required only with --execute")
    parser.add_argument("--report", type=Path,
                        help="external report path; defaults under /tmp, never inside repository")
    args = parser.parse_args()
    default_report = Path("/tmp/mini-moonboard-a12-row1586-endpoint-recovery-toy.json" if args.toy_check
                          else "/tmp/mini-moonboard-a12-row1586-endpoint-recovery-result.json")
    report_path = args.report or default_report
    validate_output_path(report_path)

    if args.verify_preparation:
        report = read_only_preparation_report()
        if args.report:
            output_report(report_path, report)
        print(json.dumps(report, sort_keys=True))
        return 0
    if args.toy_check:
        report = toy_check()
        output_report(report_path, report)
        print(report["status"], "source_K_triplet_parse=0", "source_K_factorizations=0",
              "synthetic_factorizations=1", "native_runs=0")
        return 0
    if not args.parent_approval:
        parser.error("--execute requires an external --parent-approval JSON after independent review")
    report = run_actual(args.parent_approval, report_path)
    print(report["status"], "factorizations=", report.get("resource_and_execution", {}).get("body_factorizations_used", 0),
          "native_runs=0")
    return 0 if report["status"] in ("METHOD_PASS_SOURCE_ROW_RF_MATCH", "METHOD_PASS_SOURCE_ROW_RF_MISS") else 2


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except TimeoutError as exc:
        raise SystemExit(f"HARD_RESOURCE_STOP: {exc}")
