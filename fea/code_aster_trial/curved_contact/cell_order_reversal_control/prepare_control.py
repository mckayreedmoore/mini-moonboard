#!/usr/bin/env python3
"""Prepare and preflight a source-only slave-cell-order control fixture.

This script copies the pinned native_input_v3 deck and reverses only the
sequence of its 95 named slave TRIA6 records. It never launches Code_Aster.
"""

from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
import shutil


ROOT = Path(__file__).resolve().parents[4]
CONTROL = Path(__file__).resolve().parent
BASELINE = ROOT / "fea/code_aster_trial/curved_contact/native_input_v3"
BASELINE_REPO_PATH = "fea/code_aster_trial/curved_contact/native_input_v3/curved_contact.mail"
FILES = ("curved_contact.comm", "curved_contact.export", "curved_contact.mail",
         "generate.py", "geometry-oracle.json")
EXPECTED_BASELINE_SHA256 = {
    "curved_contact.comm": "ab99d41d038d8c81ae60411b676ab8aee5c037b2db4840d1540cb34216d899e5",
    "curved_contact.export": "c0e3c9939c4b61137891656af2d7ec465c6b1e9d8eaab4fb28f22581489a4e2c",
    "curved_contact.mail": "a9b4ba52c842c72481324720c5bb745dd44fed15ff697cba4188d1ac03cabcfa",
    "generate.py": "526c51ab6a0ad184ea14cf23dd4571fdd4f4fce37d27bceef3ea6b174d1efd96",
    "geometry-oracle.json": "cc56a4271146a5cc9daf0b8359b58c953ea74c9b5e83b4a308367ae09f833201",
}


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def line_body(line: str) -> str:
    return line.rstrip("\r\n")


def section_bounds(lines: list[str], section_name: str) -> tuple[int, int]:
    starts = [index for index, line in enumerate(lines) if line_body(line) == section_name]
    if len(starts) != 1:
        raise ValueError(f"expected one {section_name} section, found {len(starts)}")
    start = starts[0]
    ends = [index for index in range(start + 1, len(lines)) if line_body(lines[index]) == "FINSF"]
    if not ends:
        raise ValueError(f"{section_name} section has no FINSF terminator")
    return start + 1, ends[0]


def parse_element_records(lines: list[str], section_name: str) -> list[dict[str, object]]:
    start, end = section_bounds(lines, section_name)
    records = []
    for line in lines[start:end]:
        fields = line_body(line).split()
        if len(fields) != 7:
            raise ValueError(f"{section_name} record must have a label and six nodes: {line_body(line)!r}")
        records.append({"label": fields[0], "connectivity": fields[1:], "line": line})
    return records


def parse_groups(lines: list[str], keyword: str) -> dict[str, set[str]]:
    groups = {}
    for index, line in enumerate(lines):
        if line_body(line) != keyword:
            continue
        end = next((j for j in range(index + 1, len(lines))
                    if line_body(lines[j]) == "FINSF"), None)
        if end is None:
            raise ValueError(f"unterminated {keyword} block at line {index + 1}")
        tokens = " ".join(line_body(item) for item in lines[index + 1:end]).split()
        if not tokens:
            raise ValueError(f"empty {keyword} block at line {index + 1}")
        name, *members = tokens
        if name in groups:
            raise ValueError(f"duplicate {keyword} group {name}")
        groups[name] = set(members)
    return groups


def tria_record_index_bounds(lines: list[str]) -> tuple[int, int]:
    start, end = section_bounds(lines, "TRIA6")
    return start, end


def build_control_mail(baseline_bytes: bytes, slave_count: int) -> tuple[bytes, dict[str, object]]:
    text = baseline_bytes.decode("utf-8")
    lines = text.splitlines(keepends=True)
    start, end = tria_record_index_bounds(lines)
    records = parse_element_records(lines, "TRIA6")
    if len(records) <= slave_count:
        raise ValueError(f"TRIA6 section has {len(records)} records; cannot split {slave_count} slave records")
    slave = records[:slave_count]
    master = records[slave_count:]
    slave_group = parse_groups(lines, "GROUP_MA").get("SLAVE")
    master_group = parse_groups(lines, "GROUP_MA").get("MASTER")
    if slave_group is None or master_group is None:
        raise ValueError("baseline mail lacks SLAVE or MASTER GROUP_MA")
    if {row["label"] for row in slave} != slave_group or len(slave) != len(slave_group):
        raise ValueError("first TRIA6 records do not match the SLAVE group membership")
    if {row["label"] for row in master} != master_group or len(master) != len(master_group):
        raise ValueError("remaining TRIA6 records do not match the MASTER group membership")
    new_lines = lines[:start] + list(reversed(lines[start:start + slave_count])) + lines[start + slave_count:]
    output = "".join(new_lines).encode("utf-8")
    metadata = {
        "section": "TRIA6",
        "group_ma": "SLAVE",
        "record_count": slave_count,
        "baseline_first_line_1based": start + 1,
        "baseline_last_line_1based": start + slave_count,
        "baseline_record_labels": [str(row["label"]) for row in slave],
        "control_record_labels": [str(row["label"]) for row in reversed(slave)],
        "records_reversed_as_whole_lines": True,
        "all_label_connectivity_pairs_preserved": True,
        "master_record_sequence_preserved": True,
        "all_other_mail_lines_preserved_byte_for_byte": True,
    }
    return output, metadata


def prove_reversal(baseline_bytes: bytes, control_bytes: bytes, slave_count: int) -> dict[str, object]:
    baseline_lines = baseline_bytes.decode("utf-8").splitlines(keepends=True)
    control_lines = control_bytes.decode("utf-8").splitlines(keepends=True)
    if len(baseline_lines) != len(control_lines):
        raise ValueError("line count changed; control must be a pure record permutation")
    base_start, base_end = tria_record_index_bounds(baseline_lines)
    ctrl_start, ctrl_end = tria_record_index_bounds(control_lines)
    if (base_start, base_end) != (ctrl_start, ctrl_end):
        raise ValueError("TRIA6 section boundaries changed")
    if base_end - base_start != 183:
        raise ValueError(f"expected 183 total TRIA6 records, found {base_end - base_start}")
    if control_lines[:base_start] != baseline_lines[:base_start]:
        raise ValueError("mail lines before TRIA6 changed")
    if control_lines[base_start:base_start + slave_count] != list(
            reversed(baseline_lines[base_start:base_start + slave_count])):
        raise ValueError("slave TRIA6 records are not an exact reverse of baseline sequence")
    if control_lines[base_start + slave_count:] != baseline_lines[base_start + slave_count:]:
        raise ValueError("mail lines after slave TRIA6 block changed")

    baseline_records = parse_element_records(baseline_lines, "TRIA6")
    control_records = parse_element_records(control_lines, "TRIA6")
    base_slaves, ctrl_slaves = baseline_records[:slave_count], control_records[:slave_count]
    base_masters, ctrl_masters = baseline_records[slave_count:], control_records[slave_count:]
    def connectivity_map(records):
        return {row["label"]: row["connectivity"] for row in records}
    if connectivity_map(base_slaves) != connectivity_map(ctrl_slaves):
        raise ValueError("slave label-to-connectivity mapping changed")
    if base_masters != ctrl_masters:
        raise ValueError("master TRIA6 records changed")
    for keyword in ("GROUP_MA", "GROUP_NO"):
        if parse_groups(baseline_lines, keyword) != parse_groups(control_lines, keyword):
            raise ValueError(f"{keyword} memberships changed")
    expected_labels = set(parse_groups(baseline_lines, "GROUP_MA")["SLAVE"])
    if {row["label"] for row in base_slaves} != expected_labels:
        raise ValueError("baseline slave mesh records do not equal SLAVE group membership")
    return {
        "exact_reversal_proven": True,
        "source_slave_record_count": len(base_slaves),
        "source_master_record_count": len(base_masters),
        "slave_record_labels_unchanged": True,
        "slave_connectivity_and_orientation_unchanged": True,
        "master_records_and_order_unchanged": True,
        "tetra10_solids_and_all_pre_tria_lines_unchanged": True,
        "all_post_tria_lines_unchanged": True,
        "group_ma_memberships_unchanged": True,
        "group_no_memberships_unchanged": True,
        "coordinates_unchanged": True,
    }


def prepare() -> dict[str, object]:
    for name, expected_hash in EXPECTED_BASELINE_SHA256.items():
        actual_hash = sha256(BASELINE / name)
        if actual_hash != expected_hash:
            raise ValueError(f"pinned v3 source hash mismatch for {name}: {actual_hash}")

    baseline_oracle = json.loads((BASELINE / "geometry-oracle.json").read_text())
    slave_count = int(baseline_oracle["crop_rule"]["slave_source_faces"])
    if slave_count != 95 or int(baseline_oracle["crop_rule"]["master_source_faces"]) != 88:
        raise ValueError("pinned v3 crop no longer has 95 slave and 88 master TRIA6 records")

    CONTROL.mkdir(parents=True, exist_ok=True)
    for name in FILES:
        if name not in ("curved_contact.mail", "geometry-oracle.json"):
            shutil.copyfile(BASELINE / name, CONTROL / name)

    baseline_mail_bytes = (BASELINE / "curved_contact.mail").read_bytes()
    control_mail_bytes, reversal = build_control_mail(baseline_mail_bytes, slave_count)
    (CONTROL / "curved_contact.mail").write_bytes(control_mail_bytes)
    diff_proof = prove_reversal(baseline_mail_bytes, control_mail_bytes, slave_count)
    if (CONTROL / "curved_contact.comm").read_bytes() != (BASELINE / "curved_contact.comm").read_bytes():
        raise ValueError(".comm changed from pinned v3 deck")
    if (CONTROL / "curved_contact.export").read_bytes() != (BASELINE / "curved_contact.export").read_bytes():
        raise ValueError(".export changed from pinned v3 deck")
    if (CONTROL / "generate.py").read_bytes() != (BASELINE / "generate.py").read_bytes():
        raise ValueError("generator copy differs from pinned v3 source")

    control_mail_hash = sha256(CONTROL / "curved_contact.mail")
    control_oracle = copy.deepcopy(baseline_oracle)
    source = control_oracle["source"]
    source["crop_mail_sha256"] = control_mail_hash
    source["cell_order_control"] = {
        "baseline_mail_repo_path": BASELINE_REPO_PATH,
        "baseline_mail_sha256": EXPECTED_BASELINE_SHA256["curved_contact.mail"],
        "operation": "Reverse only the 95 contiguous SLAVE TRIA6 mesh-record lines; preserve each line intact.",
        "group_ma": "SLAVE",
        "record_count": slave_count,
        "control_record_labels": reversal["control_record_labels"],
        "mesh_geometry_unchanged": True,
        "purpose": "Source-order sensitivity control only; it is not a corrected or accepted geometry.",
    }
    oracle_path = CONTROL / "geometry-oracle.json"
    oracle_path.write_text(json.dumps(control_oracle, indent=2, sort_keys=True) + "\n")
    if json.loads(oracle_path.read_text()) != control_oracle:
        raise ValueError("copied geometry oracle failed semantic round-trip")
    # Every baseline oracle field other than the control input hash and its
    # explicit provenance must remain identical.
    oracle_compare = copy.deepcopy(control_oracle)
    oracle_compare["source"]["crop_mail_sha256"] = baseline_oracle["source"]["crop_mail_sha256"]
    del oracle_compare["source"]["cell_order_control"]
    if oracle_compare != baseline_oracle:
        raise ValueError("control oracle changed fields beyond input hash/provenance")

    for name in ("curved_contact.comm", "curved_contact.export", "generate.py"):
        if sha256(CONTROL / name) != EXPECTED_BASELINE_SHA256[name]:
            raise ValueError(f"copied artifact hash differs from pinned v3: {name}")
    if control_mail_hash == EXPECTED_BASELINE_SHA256["curved_contact.mail"]:
        raise ValueError("reversal unexpectedly produced the same mail hash as baseline")

    manifest = {
        "purpose": "Source-only reversed SLAVE TRIA6 cell-order control for the A09 pair-021 quadratic curved-contact crop.",
        "native_solver_invoked": False,
        "baseline": {
            "input_directory": str(BASELINE.relative_to(ROOT)),
            "file_sha256": EXPECTED_BASELINE_SHA256,
        },
        "control": {
            "directory": str(CONTROL.relative_to(ROOT)),
            "file_sha256": {name: sha256(CONTROL / name) for name in FILES},
        },
        "preflight_script": {
            "repo_path": str(Path(__file__).resolve().relative_to(ROOT)),
            "sha256": sha256(Path(__file__).resolve()),
        },
        "change_scope": {
            "only_native_input_change": "reverse the ordered 95 SLAVE TRIA6 mesh-record lines",
            "sequence_change": reversal,
            "preflight_proofs": diff_proof,
            "comm_export_generator_byte_identical": True,
            "geometry_oracle_numeric_content_unchanged": True,
            "copied_oracle_metadata_change": ["source.crop_mail_sha256", "source.cell_order_control"],
            "group_ma_and_group_no_memberships_unchanged": True,
            "coordinates_and_tetra10_solid_connectivity_unchanged": True,
            "master_contact_record_sequence_unchanged": True,
        },
        "interpretation": "This isolates input cell-record ordering as one potential source of solver sensitivity. It does not change geometry, orientation, contact pairing, supports, material, motion, or acceptance limits. Any result remains a diagnostic control, not acceptance or qualification.",
    }
    manifest_path = CONTROL / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    return manifest


if __name__ == "__main__":
    result = prepare()
    print(json.dumps({
        "control_mail_sha256": result["control"]["file_sha256"]["curved_contact.mail"],
        "preflight": result["change_scope"]["preflight_proofs"],
        "native_solver_invoked": result["native_solver_invoked"],
        "manifest": str((CONTROL / "manifest.json").relative_to(ROOT)),
    }, indent=2, sort_keys=True))
