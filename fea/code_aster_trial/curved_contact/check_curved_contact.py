#!/usr/bin/env python3
"""Audit frozen native curved-contact tables against the source-geometry oracle.

This reads parent-produced tables only; it never invokes Code_Aster.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from pathlib import Path
import re
import sys


ROOT = Path(__file__).resolve().parents[3]
DEFAULT_ORACLE = Path(__file__).resolve().with_name("geometry-oracle.json")
DEFAULT_MAIL = Path(__file__).resolve().with_name("curved_contact.mail")
HISTORY = (
    (0.0, 0.0),
    (1.0, -0.10),
    (2.0, -0.20),
    (3.0, 0.0),
    (4.0, 0.50),
    (5.0, 0.60),
    (6.0, 0.65),
    (7.0, 0.60),
    (8.0, 0.50),
    (9.0, 0.0),
    (10.0, -0.10),
    (11.0, 0.60),
)
TIME_TOL = 1.0e-8


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def normalized(value: str) -> str:
    return re.sub(r"[^A-Z0-9_]", "", value.upper())


def parse_table(path: Path, required: tuple[str, ...]) -> list[dict[str, str]]:
    """Read semicolon IMPR_TABLE output, tolerating its text preamble."""
    header = None
    rows: list[dict[str, str]] = []
    for line in path.read_text(errors="replace").splitlines():
        cells = [cell.strip() for cell in next(csv.reader([line], delimiter=";", skipinitialspace=True))]
        keys = [normalized(cell) for cell in cells]
        if all(name in keys for name in required):
            header = keys
            continue
        if header is None or not line.strip() or line.lstrip().startswith(("#", "*")):
            continue
        if len(cells) != len(header):
            continue
        rows.append(dict(zip(header, cells)))
    if not rows:
        raise ValueError(f"No data rows with columns {required} found in {path}")
    return rows


def number(row: dict[str, str], name: str) -> float:
    raw = row.get(name)
    if raw is None or not raw.strip():
        raise ValueError(f"Missing {name} in parsed row: {row}")
    value = float(raw.replace("D", "E").replace("d", "e"))
    if not math.isfinite(value):
        raise ValueError(f"Non-finite {name} in parsed row: {row}")
    return value


def node_key(row: dict[str, str]) -> str:
    value = row.get("NOEUD", row.get("NOEUD_CMP", "")).strip()
    if not value:
        raise ValueError(f"No NOEUD/NOEUD_CMP in parsed row: {row}")
    return value


def grouped(rows: list[dict[str, str]]) -> dict[float, list[dict[str, str]]]:
    by_time: dict[float, list[dict[str, str]]] = {}
    for row in rows:
        by_time.setdefault(number(row, "INST"), []).append(row)
    return by_time


def canonicalize_nodes(rows: list[dict[str, str]], oracle, table_name: str):
    """Map internal numeric NOEUD identifiers back to the .mail node labels."""
    by_number = {}
    by_label = {}
    for group_rows in oracle["node_groups"].values():
        for item in group_rows:
            number_id = int(item["aster_node_number"])
            label = item["output_node"]
            if number_id in by_number and by_number[number_id] != label:
                raise ValueError(f"oracle repeats ASTER node number {number_id}")
            if label in by_label and by_label[label] != number_id:
                raise ValueError(f"oracle repeats output node label {label}")
            by_number[number_id] = label
            by_label[label] = number_id

    result = []
    for row in rows:
        canonical = dict(row)
        raw = node_key(row).strip().strip("'\"")
        if raw in by_label:
            label = raw
        else:
            try:
                numeric = float(raw.replace("D", "E").replace("d", "e"))
            except ValueError as exc:
                raise ValueError(f"{table_name} has unrecognized node identifier {raw!r}") from exc
            if not numeric.is_integer() or int(numeric) not in by_number:
                raise ValueError(f"{table_name} has ASTER node number outside frozen crop: {raw!r}")
            label = by_number[int(numeric)]
        canonical["NOEUD"] = label
        canonical.pop("NOEUD_CMP", None)
        result.append(canonical)
    return result


def assert_exact_times(data: dict[float, list[dict[str, str]]],
                       expected: tuple[float, ...], table_name: str):
    """Require exactly the requested INST set, matching each once within tolerance."""
    unmatched = list(data)
    for target in expected:
        matches = [(abs(inst - target), inst) for inst in unmatched]
        if not matches:
            raise ValueError(f"Missing {table_name} at INST={target:g}")
        delta, actual = min(matches)
        if delta > TIME_TOL:
            raise ValueError(f"Missing {table_name} at INST={target:g}; nearest differs by {delta:g}")
        unmatched.remove(actual)
    if unmatched:
        raise ValueError(f"Unexpected extra {table_name} instants: {sorted(unmatched)}")


def assert_times_with_initial(data: dict[float, list[dict[str, str]]], table_name: str):
    """Require exactly one initial INST=-1 plus the 12 evaluated history points."""
    initial = [inst for inst in data if abs(inst + 1.0) <= TIME_TOL]
    if len(initial) != 1:
        raise ValueError(f"{table_name} must contain exactly one initial INST=-1 record, got {initial}")
    evaluated = {inst: rows for inst, rows in data.items() if inst != initial[0]}
    assert_exact_times(evaluated, tuple(inst for inst, _ in HISTORY), table_name)
    return initial[0]


def rows_at(data, target: float, table_name: str) -> list[dict[str, str]]:
    matches = [(abs(inst - target), rows) for inst, rows in data.items()]
    delta, rows = min(matches, key=lambda item: item[0])
    if delta > TIME_TOL:
        raise ValueError(f"Missing {table_name} at INST={target:g}; nearest differs by {delta:g}")
    return rows


def keyed_rows(rows, expected_nodes: set[str], table_name: str, inst: float):
    mapping = {}
    for row in rows:
        key = node_key(row)
        if key in mapping:
            raise ValueError(f"Duplicate {table_name} row for node {key} at INST={inst:g}")
        mapping[key] = row
    actual = set(mapping)
    if actual != expected_nodes:
        missing = sorted(expected_nodes - actual)
        extra = sorted(actual - expected_nodes)
        raise ValueError(f"{table_name} node coverage differs at INST={inst:g}; missing={missing[:8]}, extra={extra[:8]}")
    return mapping


def vector_sum(rows_by_node, components):
    return tuple(math.fsum(number(row, cmp) for row in rows_by_node.values())
                 for cmp in components)


def vector_norm(vector):
    return math.sqrt(math.fsum(value * value for value in vector))


def vector_add(a, b):
    return tuple(x + y for x, y in zip(a, b))


def vector_sub(a, b):
    return tuple(x - y for x, y in zip(a, b))


def vector_dot(a, b):
    return math.fsum(x * y for x, y in zip(a, b))


def close(a, b, tol=1.0e-12):
    return abs(a - b) <= tol


def prove_slave_cell_order_control(baseline_path: Path, control_path: Path,
                                   baseline_sha256: str, slave_record_count: int):
    """Prove the control mesh differs only by reversing its slave TRIA6 rows."""
    if sha256(baseline_path) != baseline_sha256:
        raise ValueError("cell-order control baseline mail hash differs from its provenance")
    baseline_lines = baseline_path.read_text().splitlines(keepends=True)
    control_lines = control_path.read_text().splitlines(keepends=True)
    if len(baseline_lines) != len(control_lines):
        raise ValueError("cell-order control changed mail line count")
    def tria_bounds(lines):
        indices = [i for i, line in enumerate(lines) if line.strip() == "TRIA6"]
        if len(indices) != 1:
            raise ValueError("cell-order control mail must contain one TRIA6 section")
        start = indices[0] + 1
        ends = [i for i in range(start, len(lines)) if lines[i].strip() == "FINSF"]
        if not ends:
            raise ValueError("TRIA6 section has no FINSF terminator")
        return start, ends[0]
    base_start, base_end = tria_bounds(baseline_lines)
    ctrl_start, ctrl_end = tria_bounds(control_lines)
    if (base_start, base_end) != (ctrl_start, ctrl_end):
        raise ValueError("cell-order control changed TRIA6 section bounds")
    if base_end - base_start <= slave_record_count:
        raise ValueError("cell-order control TRIA6 section is shorter than slave block")
    if baseline_lines[:base_start] != control_lines[:ctrl_start]:
        raise ValueError("cell-order control changed coordinates or solid element records")
    if control_lines[ctrl_start:ctrl_start + slave_record_count] != list(
            reversed(baseline_lines[base_start:base_start + slave_record_count])):
        raise ValueError("cell-order control slave records are not the exact reversed lines")
    if control_lines[ctrl_start + slave_record_count:] != baseline_lines[base_start + slave_record_count:]:
        raise ValueError("cell-order control changed master records or post-TRIA6 mesh groups")
    base_records = [line.split() for line in baseline_lines[base_start:base_end]]
    ctrl_records = [line.split() for line in control_lines[ctrl_start:ctrl_end]]
    if any(len(row) != 7 for row in base_records + ctrl_records):
        raise ValueError("cell-order control found malformed TRIA6 record")
    if {row[0]: row[1:] for row in base_records[:slave_record_count]} != {
            row[0]: row[1:] for row in ctrl_records[:slave_record_count]}:
        raise ValueError("cell-order control altered slave connectivity or orientation")


def load_oracle(path: Path, mail_path: Path):
    oracle = json.loads(path.read_text())
    recorded = oracle["source"]
    if sha256(mail_path) != recorded["crop_mail_sha256"]:
        raise ValueError("cropped ASTER mesh hash differs from the selected frozen geometry oracle")
    format_revision = recorded.get("format_only_revision")
    if format_revision is not None:
        original_mail = DEFAULT_MAIL
        if sha256(original_mail) != format_revision["original_crop_mail_sha256"]:
            raise ValueError("original crop mesh hash differs from the format-only revision provenance")
        if format_revision.get("all_whitespace_separated_tokens_identical") is not True:
            raise ValueError("format-only revision does not assert identical whitespace-separated tokens")
        order_control = recorded.get("cell_order_control")
        if order_control is None:
            if original_mail.read_text().split() != mail_path.read_text().split():
                raise ValueError("native mesh tokens differ from the original crop despite format-only provenance")
        else:
            baseline_mail = ROOT / order_control["baseline_mail_repo_path"]
            if original_mail.read_text().split() != baseline_mail.read_text().split():
                raise ValueError("v3 format-only baseline differs from the original crop token stream")
            prove_slave_cell_order_control(
                baseline_mail, mail_path,
                order_control["baseline_mail_sha256"],
                int(order_control["record_count"]))
    generator_path = Path(__file__).with_name("generate.py")
    if sha256(generator_path) != recorded["generator_sha256"]:
        raise ValueError("geometry generator changed after the geometry oracle was frozen")
    for key, relative in (("mesh.inp", recorded["mesh"]),
                          ("contact-fragment.inc", recorded["contact_fragment"])):
        source_path = ROOT / relative
        if sha256(source_path) != recorded["sha256"][key]:
            raise ValueError(f"source geometry input changed after freezing: {relative}")
    labels_in_mail_order = []
    in_coordinates = False
    for line in mail_path.read_text().splitlines():
        if line.strip() == "COOR_3D":
            in_coordinates = True
            continue
        if in_coordinates:
            if line.strip() == "FINSF":
                break
            fields = line.split()
            if len(fields) != 4:
                raise ValueError(f"Malformed COOR_3D line in frozen mesh: {line!r}")
            labels_in_mail_order.append(fields[0])
    expected_number_map = {int(item["aster_node_number"]): item["output_node"]
                           for group_rows in oracle["node_groups"].values()
                           for item in group_rows}
    expected_labels = [expected_number_map.get(index)
                       for index in range(1, len(labels_in_mail_order) + 1)]
    if labels_in_mail_order != expected_labels:
        raise ValueError("oracle ASTER node-number mapping differs from .mail COOR_3D order")
    return oracle


def check(contact_path: Path, slave_cut_path: Path, master_cut_path: Path,
          oracle_path=DEFAULT_ORACLE, mail_path=DEFAULT_MAIL,
          displacement_path: Path | None = None):
    oracle = load_oracle(oracle_path, mail_path)
    contact = grouped(canonicalize_nodes(parse_table(contact_path,
                                  ("INST", "NOEUD", "CONT", "JEU", "RNX", "RNY", "RNZ")),
                                  oracle, "contact table"))
    slave_cut = grouped(canonicalize_nodes(parse_table(slave_cut_path,
                                    ("INST", "NOEUD", "DX", "DY", "DZ")),
                                    oracle, "SCUT reaction table"))
    master_cut = grouped(canonicalize_nodes(parse_table(master_cut_path,
                                     ("INST", "NOEUD", "DX", "DY", "DZ")),
                                     oracle, "MCUT reaction table"))
    displacement = None
    if displacement_path:
        displacement = grouped(canonicalize_nodes(parse_table(displacement_path,
                                           ("INST", "NOEUD", "DX", "DY", "DZ")),
                                           oracle, "SNODE displacement table"))

    initial_times = {
        "contact": assert_times_with_initial(contact, "contact table"),
        "SCUT": assert_times_with_initial(slave_cut, "SCUT reaction table"),
        "MCUT": assert_times_with_initial(master_cut, "MCUT reaction table"),
    }
    if displacement is not None:
        initial_times["SDISP"] = assert_times_with_initial(displacement,
                                                            "SNODE displacement table")

    close_dir = tuple(oracle["initial_gap"]["closing_direction_unit_vector"])
    thresholds = oracle["frozen_screen_thresholds"]
    open_error_tol = thresholds["open_state_maximum_absolute_gap_error_mm"]
    active_gap_tol = thresholds["active_node_maximum_absolute_gap_mm"]
    penetration_tol = thresholds["all_slave_nodes_maximum_penetration_mm"]
    force_tol = 0.05
    force_rel_tol = 0.001

    node_groups = oracle["node_groups"]
    expected_slave = {item["output_node"] for item in node_groups["SNODE"]}
    expected_slave_cut = {item["output_node"] for item in node_groups["SCUT"]}
    expected_master_cut = {item["output_node"] for item in node_groups["MCUT"]}
    motion_states = oracle["open_motion_geometry_oracle"]["states"]

    # The pre-step record exists only because the model explicitly evaluates
    # its zero-motion geometry. Contact fields may be uninitialized there, so
    # validate row coverage and ignore all force/status/gap values at INST=-1.
    keyed_rows(contact[initial_times["contact"]], expected_slave,
               "initial contact table", initial_times["contact"])
    keyed_rows(slave_cut[initial_times["SCUT"]], expected_slave_cut,
               "initial SCUT reaction table", initial_times["SCUT"])
    keyed_rows(master_cut[initial_times["MCUT"]], expected_master_cut,
               "initial MCUT reaction table", initial_times["MCUT"])
    if displacement is not None:
        keyed_rows(displacement[initial_times["SDISP"]], expected_slave,
                   "initial SNODE displacement table", initial_times["SDISP"])

    reports = []
    all_failures = []
    for inst, imposed in HISTORY:
        contacts = keyed_rows(rows_at(contact, inst, "contact table"), expected_slave,
                              "contact table", inst)
        slave_reactions = keyed_rows(rows_at(slave_cut, inst, "SCUT reaction table"),
                                     expected_slave_cut, "SCUT reaction table", inst)
        master_reactions = keyed_rows(rows_at(master_cut, inst, "MCUT reaction table"),
                                      expected_master_cut, "MCUT reaction table", inst)

        all_gaps = {node: number(row, "JEU") for node, row in contacts.items()}
        all_status = {node: number(row, "CONT") for node, row in contacts.items()}
        state_failures = []
        def fail(message):
            state_failures.append(message)
            all_failures.append({"inst": inst, "message": message})
        if any(status < -1.0 - 1.0e-8 or status > 2.0 + 1.0e-8 for status in all_status.values()):
            fail(f"Unexpected CONT status outside [-1,2] at INST={inst:g}")
        if any(close(status, -1.0) for status in all_status.values()):
            fail(f"CONT=-1 indicates an unpaired slave node at INST={inst:g}")

        local_rn = {}
        for node, row in contacts.items():
            local_rn[node] = (number(row, "RNX"), number(row, "RNY"), number(row, "RNZ"))
        rn_sum = tuple(math.fsum(vector[i] for vector in local_rn.values()) for i in range(3))
        local_force_norm_sum = math.fsum(vector_norm(vector) for vector in local_rn.values())
        slave_cut_sum = vector_sum(slave_reactions, ("DX", "DY", "DZ"))
        master_cut_sum = vector_sum(master_reactions, ("DX", "DY", "DZ"))
        scale = max(vector_norm(rn_sum), vector_norm(slave_cut_sum), vector_norm(master_cut_sum))
        balance_tol = max(force_tol, force_rel_tol * scale)
        slave_balance = vector_sub(rn_sum, slave_cut_sum)
        master_balance = vector_add(rn_sum, master_cut_sum)
        slave_balance_error = vector_norm(slave_balance)
        master_balance_error = vector_norm(master_balance)

        open_key = f"{imposed:+.2f}"
        if open_key in motion_states:
            expected_rows = motion_states[open_key]["nodes"]
            # Output label lookup uses the frozen source-to-label contact map.
            label_by_source = {item["source_node"]: item["output_node"]
                               for item in node_groups["SNODE"]}
            expected_gap = {label_by_source[row["source_slave_node"]]: row["gap_mm"]
                            for row in expected_rows}
            if set(expected_gap) != expected_slave:
                raise ValueError(f"geometry oracle node coverage mismatch at INST={inst:g}")
            errors = {node: all_gaps[node] - expected_gap[node] for node in expected_slave}
            max_gap_error = max(abs(value) for value in errors.values())
            worst_gap_error_node = max(errors, key=lambda node: abs(errors[node]))
            min_gap = min(all_gaps.values())
            if max_gap_error > open_error_tol:
                fail(f"open geometry gap error {errors[worst_gap_error_node]:+.6g} mm at {worst_gap_error_node}, INST={inst:g}")
            if min_gap < 0.0:
                fail(f"open state has a negative local JEU at INST={inst:g}: {min_gap:g} mm")
            if any(abs(status) > 1.0e-8 for status in all_status.values()):
                fail(f"open state has a nonzero contact status at INST={inst:g}")
            if local_force_norm_sum > force_tol:
                fail(f"open state has sum of local RN norms {local_force_norm_sum:g} N at INST={inst:g}")
            displacement_error = None
            if displacement is not None:
                disp_rows = keyed_rows(rows_at(displacement, inst, "SNODE displacement table"),
                                       expected_slave, "SNODE displacement table", inst)
                expected_disp = tuple(imposed * x for x in close_dir)
                errors_by_node = {}
                for node, row in disp_rows.items():
                    actual = tuple(number(row, cmp) for cmp in ("DX", "DY", "DZ"))
                    errors_by_node[node] = vector_norm(vector_sub(actual, expected_disp))
                displacement_error = max(errors_by_node.values())
                if displacement_error > open_error_tol:
                    node = max(errors_by_node, key=errors_by_node.get)
                    fail(f"open rigid-motion displacement error {displacement_error:g} mm at {node}, INST={inst:g}")
            state = "open"
            active_nodes = []
            penetration = max(0.0, -min_gap)
        else:
            max_gap_error = None
            displacement_error = None
            min_gap = min(all_gaps.values())
            penetration = max(0.0, -min_gap)
            if penetration > penetration_tol:
                worst_penetration_node = min(all_gaps, key=all_gaps.get)
                fail(f"local penetration {penetration:g} mm at {worst_penetration_node} exceeds {penetration_tol:g} at INST={inst:g}")
            active_nodes = [node for node, status in all_status.items() if status > 0.0]
            for node in active_nodes:
                if abs(all_gaps[node]) > active_gap_tol:
                    fail(f"active node {node} has |JEU|={abs(all_gaps[node]):g} mm at INST={inst:g}")
            if not active_nodes:
                fail(f"compression/reclosure state has no active contact nodes at INST={inst:g}")
            rn_magnitude = vector_norm(rn_sum)
            signed_projection = vector_dot(rn_sum, close_dir)
            if rn_magnitude <= force_tol:
                fail(f"compression contact resultant {rn_magnitude:g} N is not above {force_tol:g} N at INST={inst:g}")
            if signed_projection <= force_tol:
                fail(f"signed RN projection along closing direction is {signed_projection:g} N at INST={inst:g}")
            if slave_balance_error > balance_tol:
                fail(f"RN versus SCUT signed reaction imbalance {slave_balance_error:g} N exceeds {balance_tol:g} N at INST={inst:g}")
            if master_balance_error > balance_tol:
                fail(f"RN versus MCUT action/reaction imbalance {master_balance_error:g} N exceeds {balance_tol:g} N at INST={inst:g}")
            state = "contact"

        reports.append({
            "inst": inst,
            "control_displacement_mm": imposed,
            "state": state,
            "minimum_local_jeu_mm": min_gap,
            "maximum_local_jeu_mm": max(all_gaps.values()),
            "maximum_penetration_mm": penetration,
            "maximum_open_geometry_error_mm": max_gap_error,
            "worst_open_geometry_error_node": (worst_gap_error_node if open_key in motion_states else None),
            "maximum_open_rigid_motion_error_mm": displacement_error,
            "contact_status_counts": {
                str(code): sum(1 for value in all_status.values() if close(value, code, 1.0e-8))
                for code in (0.0, 1.0, 2.0)
            },
            "interpolated_or_partial_status_nodes": [node for node, value in all_status.items()
                                                     if 0.0 < value < 2.0],
            "active_contact_nodes_cont_gt_zero": active_nodes,
            "sum_local_contact_force_norms_n": local_force_norm_sum,
            "contact_resultant_rn_n": list(rn_sum),
            "contact_resultant_magnitude_n": vector_norm(rn_sum),
            "contact_resultant_projection_closing_direction_n": vector_dot(rn_sum, close_dir),
            "scut_forc_noda_resultant_n": list(slave_cut_sum),
            "mcut_forc_noda_resultant_n": list(master_cut_sum),
            "rn_minus_scut_balance_vector_n": list(slave_balance),
            "rn_minus_scut_balance_error_n": slave_balance_error,
            "rn_plus_mcut_balance_vector_n": list(master_balance),
            "rn_plus_mcut_balance_error_n": master_balance_error,
            "frozen_force_balance_tolerance_n": balance_tol,
            "state_failures": state_failures,
            "all_local_values": [
                {"node": node,
                 "jeu_mm": all_gaps[node],
                 "cont": all_status[node],
                 "rnx_n": local_rn[node][0],
                 "rny_n": local_rn[node][1],
                 "rnz_n": local_rn[node][2],
                 "rn_norm_n": vector_norm(local_rn[node])}
                for node in sorted(expected_slave)
            ],
        })

    result = {
        "scope": "A09 pair021 cropped quadratic curved contact method screen; not candidate joint acceptance.",
        "analysis_kind": "Post-run table audit; no native solver invocation.",
        "runtime_image_expected": "simvia/code_aster@sha256:d8d19ea91989eac0d38195bc5795c54c69f530f7196f53d67697ffa57c9106d5",
        "independent_geometry_oracle": str(oracle_path),
        "crop_mail_sha256": sha256(mail_path),
        "mesh_format_provenance": {
            "original_generated_mail_sha256": oracle["source"].get("format_only_revision", {}).get(
                "original_crop_mail_sha256", oracle["source"]["crop_mail_sha256"]),
            "v3_wrapped_baseline_mail_sha256": oracle["source"].get("cell_order_control", {}).get(
                "baseline_mail_sha256", oracle["source"]["crop_mail_sha256"]),
            "native_mail_sha256": sha256(mail_path),
            "v3_reflow_preserves_original_mesh_tokens": oracle["source"].get(
                "format_only_revision", {}).get("all_whitespace_separated_tokens_identical", True),
            "slave_cell_order_reversal_verified": "cell_order_control" in oracle["source"],
            "cell_order_control": oracle["source"].get("cell_order_control"),
            "interpretation": "A cell-order control is accepted only after exact line-level reversal proof against the pinned v3 baseline; v3 parser reflow itself is separately verified as token-identical to the generated crop.",
        },
        "input_tables": {str(path): sha256(path) for path in
                         (contact_path, slave_cut_path, master_cut_path) +
                         ((displacement_path,) if displacement_path else ())},
        "frozen_screen_thresholds": thresholds,
        "states_checked": len(reports),
        "accepted": not all_failures,
        "failures": all_failures,
        "force_interpretation": "Displacement-controlled response has no analytical pressure oracle. RN-to-SCUT/MCUT comparisons test signed equilibrium consistency only, not pressure accuracy or joint strength.",
        "states": reports,
    }
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("contact_table", type=Path)
    parser.add_argument("slave_cut_reaction_table", type=Path)
    parser.add_argument("master_cut_reaction_table", type=Path)
    parser.add_argument("--oracle", type=Path, default=DEFAULT_ORACLE)
    parser.add_argument("--mail", type=Path, default=DEFAULT_MAIL)
    parser.add_argument("--displacement-table", type=Path,
                        help="optional SNODE DEPL table for rigid-motion checks in open states")
    parser.add_argument("--json", type=Path, help="write all local gaps, forces and state checks")
    args = parser.parse_args()
    try:
        result = check(args.contact_table, args.slave_cut_reaction_table,
                       args.master_cut_reaction_table, args.oracle, args.mail,
                       args.displacement_table)
        for state in result["states"]:
            print(f"INST={state['inst']:g} d={state['control_displacement_mm']:+.3f} mm "
                  f"{state['state']}: JEU=[{state['minimum_local_jeu_mm']:+.6g},"
                  f" {state['maximum_local_jeu_mm']:+.6g}] mm, "
                  f"RN={state['contact_resultant_rn_n']} N, "
                  f"active={len(state['active_contact_nodes_cont_gt_zero'])}, "
                  f"RN/MCUT balance={state['rn_plus_mcut_balance_error_n']:.4g} N")
        if args.json:
            args.json.write_text(json.dumps(result, indent=2, allow_nan=False) + "\n")
    except (OSError, ValueError, KeyError, csv.Error) as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1
    if result["accepted"]:
        print("PASS: frozen curved-contact geometry, local-gap, signed-force and reaction-consistency screens.")
        return 0
    for failure in result["failures"]:
        print(f"FAIL: INST={failure['inst']:g}: {failure['message']}", file=sys.stderr)
    print(f"FAIL: {len(result['failures'])} frozen screening checks failed; complete metrics were written when --json was supplied.", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
