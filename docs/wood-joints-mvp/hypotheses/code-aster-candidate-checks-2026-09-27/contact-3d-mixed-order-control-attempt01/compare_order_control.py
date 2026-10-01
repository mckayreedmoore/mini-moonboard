#!/usr/bin/env python3
"""Compare the paired active/open contact-order diagnostic outputs offline."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


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


def meshes_differ_only_by_slave_order(first: Path, second: Path) -> bool:
    a = (first / "contact_coupon.mail").read_text().splitlines()
    b = (second / "contact_coupon.mail").read_text().splitlines()
    if len(a) != len(b):
        return False
    def normalized(lines):
        result = list(lines)
        for index, line in enumerate(result[:-1]):
            if line.strip() == "GROUP_MA" and result[index + 1].startswith("SLAVE "):
                result[index + 1] = "SLAVE <ORDERED_FACE_NAMES>"
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
    geometry_order_only = meshes_differ_only_by_slave_order(base_path, reverse_path)
    solver_deck_identical = (
        base_freeze["input_sha256"]["contact_3d.comm"] == reverse_freeze["input_sha256"]["contact_3d.comm"]
        and base_freeze["input_sha256"]["contact_3d.export"] == reverse_freeze["input_sha256"]["contact_3d.export"]
        and base_freeze["image"] == reverse_freeze["image"]
    )
    checks = {
        "contact_group_order_reversed": base_order == ["ST00001", "ST00002"] and reverse_order == ["ST00002", "ST00001"],
        "mesh_data_differs_only_by_slave_group_order": geometry_order_only,
        "solver_deck_and_pinned_image_identical": solver_deck_identical,
        "both_attempt_audits_classify_shared_node_order_effect": (
            base["status"] == "CONSISTENT_WITH_SOURCE_ORDERED_OVERWRITE"
            and reverse["status"] == "CONSISTENT_WITH_SOURCE_ORDERED_OVERWRITE"
        ),
        "shared_contact_status_flips_with_order": shared_status_flip,
        "shared_RN_flips_with_order": shared_rn_flip,
        "cut_reactions_unchanged_with_order_within_frozen_tolerance": reactions_unchanged,
    }
    report = {
        "scope": "offline paired-output ordering diagnostic; no capacity or candidate acceptance claim",
        "active_open_attempt": str(base_path),
        "open_active_attempt": str(reverse_path),
        "active_open_input_freeze_created_utc": base_freeze["created_utc"],
        "open_active_input_freeze_created_utc": reverse_freeze["created_utc"],
        "active_open_slave_group_order": base_order,
        "open_active_slave_group_order": reverse_order,
        "checks": checks,
        "slave_cut_reaction_max_component_delta_n": slave_delta,
        "master_cut_reaction_max_component_delta_n": master_delta,
        "frozen_cut_reaction_comparison_tolerance_n": tolerance_n,
        "active_open_RN_z_vs_slave_cut_reaction_residual_n": base_diagnostics["RN_z_vs_SCUT_REAC_NODA_residual_n"],
        "open_active_RN_z_vs_slave_cut_reaction_residual_n": reverse_diagnostics["RN_z_vs_SCUT_REAC_NODA_residual_n"],
        "shared_RN_by_node_active_open_N": base_shared_rn,
        "shared_RN_by_node_open_active_N": reverse_shared_rn,
        "status": "ORDER_SENSITIVE_SHARED_NODE_OUTPUT_OBSERVED" if all(checks.values()) else "INCONCLUSIVE",
        "interpretation": (
            "The shared-node CONT_NOEU status and RN values follow the last face in the SLAVE group while both remote cut reactions remain unchanged. This supports an order-sensitive node-output overwrite explanation for this fixture. The RN-to-cut residual is reported as evidence only; its exact recovery is not an acceptance criterion."
            if all(checks.values()) else
            "The paired outputs do not satisfy every frozen order-control check; inspect the values before attributing the difference to source-ordered output writes."
        ),
    }
    args.output.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))
    if report["status"] != "ORDER_SENSITIVE_SHARED_NODE_OUTPUT_OBSERVED":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
