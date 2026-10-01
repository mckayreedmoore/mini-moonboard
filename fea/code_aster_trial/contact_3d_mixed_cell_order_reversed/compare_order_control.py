#!/usr/bin/env python3
"""Compare the paired active/open contact-order diagnostic outputs offline."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re


def read_verified_attempt(path: Path) -> tuple[dict, dict]:
    freeze_path = path / "input-freeze.json"
    freeze = json.loads(freeze_path.read_text())
    changed = []
    for name, expected in freeze["input_sha256"].items():
        candidate = path / name
        actual = hashlib.sha256(candidate.read_bytes()).hexdigest() if candidate.is_file() else None
        if actual != expected:
            changed.append(name)
    if changed:
        raise ValueError(f"{path}: frozen-input hash mismatch: {changed}")
    execution = json.loads((path / "execution.json").read_text())
    if execution["returncode"] != 0 or execution["timed_out"] or execution["changed_frozen_inputs"]:
        raise ValueError(f"{path}: native process did not complete cleanly: {execution}")
    audit = json.loads((path / "parent-audit.json").read_text())
    return freeze, audit


def slave_group_members(path: Path) -> list[str]:
    lines = (path / "contact_coupon.mail").read_text().splitlines()
    for index, line in enumerate(lines[:-1]):
        if line.strip() == "GROUP_MA" and lines[index + 1].startswith("SLAVE "):
            return lines[index + 1].split()[1:]
    raise ValueError(f"no SLAVE GROUP_MA record in {path}")


def slave_cell_order(path: Path) -> list[str]:
    lines = (path / "contact_coupon.mail").read_text().splitlines()
    try:
        start = lines.index("TRIA6") + 1
    except ValueError as error:
        raise ValueError(f"no TRIA6 section in {path}") from error
    end = lines.index("FINSF", start)
    return [line.split()[0] for line in lines[start:end] if line.startswith("ST")]


def native_slave_mesh_index_order(path: Path) -> list[int]:
    text = (path / "native.stdout").read_text()
    marker = "Informations sur les mailles esclaves:"
    if marker not in text:
        return []
    tail = text.split(marker, 1)[1].split("# Résultat commande", 1)[0]
    return [int(value) for value in re.findall(r"Maille\s+(\d+)\s+- Zone:", tail)]


def meshes_differ_only_by_slave_face_order(first: Path, second: Path) -> bool:
    a = (first / "contact_coupon.mail").read_text().splitlines()
    b = (second / "contact_coupon.mail").read_text().splitlines()
    if len(a) != len(b):
        return False
    def normalized(lines):
        result = list(lines)
        try:
            start = result.index("TRIA6") + 1
            end = result.index("FINSF", start)
        except ValueError:
            return None
        slave_rows = sorted(
            (line for line in result[start:end] if line.startswith("ST")),
            key=lambda line: line.split()[0],
        )
        slave_positions = [index for index in range(start, end) if result[index].startswith("ST")]
        for index, row in zip(slave_positions, slave_rows):
            result[index] = row
        for index, line in enumerate(result[:-1]):
            if line.strip() == "GROUP_MA" and result[index + 1].startswith("SLAVE "):
                result[index + 1] = "SLAVE " + " ".join(sorted(result[index + 1].split()[1:]))
        return result
    return normalized(a) == normalized(b)


def max_abs_delta(a, b) -> float:
    return max(abs(float(x) - float(y)) for x, y in zip(a, b))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("active_open", type=Path)
    parser.add_argument("open_active", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    base_path = args.active_open.resolve()
    reverse_path = args.open_active.resolve()
    base_freeze, base = read_verified_attempt(base_path)
    reverse_freeze, reverse = read_verified_attempt(reverse_path)

    base_order = slave_group_members(base_path)
    reverse_order = slave_group_members(reverse_path)
    base_cell_order = slave_cell_order(base_path)
    reverse_cell_order = slave_cell_order(reverse_path)
    base_native_indices = native_slave_mesh_index_order(base_path)
    reverse_native_indices = native_slave_mesh_index_order(reverse_path)
    base_diagnostics = base["diagnostics"]
    reverse_diagnostics = reverse["diagnostics"]
    base_shared_status = base_diagnostics["shared_node_statuses_after_all_face_writes"]
    reverse_shared_status = reverse_diagnostics["shared_node_statuses_after_all_face_writes"]
    base_shared_rn = base_diagnostics["shared_node_RN_after_all_face_writes_N"]
    reverse_shared_rn = reverse_diagnostics["shared_node_RN_after_all_face_writes_N"]

    tolerance_n = min(base["frozen_limits"]["force_n"], reverse["frozen_limits"]["force_n"])
    slave_delta = max_abs_delta(base["slave_cut_reaction_noda_n"], reverse["slave_cut_reaction_noda_n"])
    master_delta = max_abs_delta(base["master_cut_reaction_noda_n"], reverse["master_cut_reaction_noda_n"])
    reactions_unchanged = slave_delta <= tolerance_n and master_delta <= tolerance_n
    shared_ids_match = set(base_shared_status) == set(reverse_shared_status)
    shared_status_flip = (shared_ids_match
                          and all(value == 0.0 for value in base_shared_status.values())
                          and all(value == 2.0 for value in reverse_shared_status.values()))
    shared_rn_flip = (shared_ids_match
                      and all(abs(value) <= 1.0e-10 for value in base_shared_rn.values())
                      and all(abs(value) > 1.0e-8 for value in reverse_shared_rn.values()))
    geometry_order_only = meshes_differ_only_by_slave_face_order(base_path, reverse_path)
    solver_deck_identical = (
        base_freeze["input_sha256"]["contact_3d.comm"] == reverse_freeze["input_sha256"]["contact_3d.comm"]
        and base_freeze["input_sha256"]["contact_3d.export"] == reverse_freeze["input_sha256"]["contact_3d.export"]
        and base_freeze["image"] == reverse_freeze["image"]
    )
    group_order_reversed = (
        base_order == ["ST00001", "ST00002"]
        and reverse_order == ["ST00002", "ST00001"]
    )
    cell_order_reversed = (
        base_cell_order == ["ST00001", "ST00002"]
        and reverse_cell_order == ["ST00002", "ST00001"]
    )
    solver_setup_identical = group_order_reversed and geometry_order_only and solver_deck_identical
    checks = {
        "contact_group_membership_order_reversed": group_order_reversed,
        "TRIA6_cell_record_order_reversed": cell_order_reversed,
        "mesh_data_differs_only_by_slave_group_and_cell_order": geometry_order_only,
        "solver_deck_and_pinned_image_identical": solver_deck_identical,
        "native_contact_log_lists_two_slave_mesh_cells": base_native_indices == [7, 8] and reverse_native_indices == [7, 8],
        "shared_contact_status_flips_with_order": shared_status_flip,
        "shared_RN_flips_with_order": shared_rn_flip,
        "cut_reactions_unchanged_with_order_within_frozen_tolerance": reactions_unchanged,
    }
    if (solver_setup_identical and cell_order_reversed and checks["native_contact_log_lists_two_slave_mesh_cells"]
            and base["status"] == "CONSISTENT_WITH_SOURCE_ORDERED_OVERWRITE"
            and reverse["status"] == "CONSISTENT_WITH_SOURCE_ORDERED_OVERWRITE"
            and shared_status_flip and shared_rn_flip and reactions_unchanged):
        status = "ORDER_SENSITIVE_SHARED_NODE_OUTPUT_OBSERVED"
        interpretation = (
            "Reversing both the slave TRIA6 cell-record order and the SLAVE group order changes the shared-node CONT_NOEU status and RN values while leaving the paired remote cut reactions unchanged. The native log visits mesh cells 7 then 8, which map to open ST00002 then active ST00001 in this control. This supports an order-sensitive node-output overwrite explanation for this fixture. The RN-to-cut residual is evidence only; exact recovery of a particular increment is not an acceptance criterion."
        )
    elif (solver_setup_identical and group_order_reversed and not cell_order_reversed
          and shared_ids_match and base_shared_status == reverse_shared_status
          and base_shared_rn == reverse_shared_rn and reactions_unchanged):
        status = "GROUP_MEMBERSHIP_ORDER_DID_NOT_CHANGE_OUTPUT"
        interpretation = (
            "Reversing only the SLAVE group member list left the contact cell-record order and all shared-node outputs unchanged. The native log still lists mesh cells 7 then 8. This control did not reverse the contact-sample visit order and does not refute order-sensitive writes; the cell-order control is needed."
        )
    else:
        status = "INCONCLUSIVE"
        interpretation = (
            "The paired runs do not isolate a consistent traversal-order effect. Check the mesh-order mapping, native contact-cell listing, cut-reaction change, and shared-node fields before interpreting the difference."
        )
    report = {
        "scope": "offline paired-output ordering diagnostic; no capacity or candidate acceptance claim",
        "active_open_attempt": str(base_path),
        "open_active_attempt": str(reverse_path),
        "active_open_input_freeze_created_utc": base_freeze["created_utc"],
        "open_active_input_freeze_created_utc": reverse_freeze["created_utc"],
        "active_open_slave_group_order": base_order,
        "open_active_slave_group_order": reverse_order,
        "active_open_slave_cell_order": base_cell_order,
        "open_active_slave_cell_order": reverse_cell_order,
        "active_open_native_slave_mesh_indices": base_native_indices,
        "open_active_native_slave_mesh_indices": reverse_native_indices,
        "open_active_native_visited_slave_labels_from_mesh_order": [
            reverse_cell_order[index] for index in range(min(len(reverse_native_indices), len(reverse_cell_order)))
        ],
        "checks": checks,
        "slave_cut_reaction_max_component_delta_n": slave_delta,
        "master_cut_reaction_max_component_delta_n": master_delta,
        "frozen_cut_reaction_comparison_tolerance_n": tolerance_n,
        "active_open_RN_z_vs_slave_cut_reaction_residual_n": base_diagnostics["RN_z_vs_SCUT_REAC_NODA_residual_n"],
        "open_active_RN_z_vs_slave_cut_reaction_residual_n": reverse_diagnostics["RN_z_vs_SCUT_REAC_NODA_residual_n"],
        "shared_RN_by_node_active_open_N": base_shared_rn,
        "shared_RN_by_node_open_active_N": reverse_shared_rn,
        "status": status,
        "interpretation": interpretation,
    }
    args.output.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))
    if report["status"] == "INCONCLUSIVE":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
