"""Reconcile the WJ24 fixed Hillman axes with their finished receivers.

This is a bounded JSON/CSV audit. It does not import CAD, rebuild geometry,
run a solver, or calculate a fastener capacity. Its receiver claims are limited
to the recorded WJ24 static composition and diagnostic.

Run from the repository root with::

    python3 scripts/wood_joint_wj24_fixed_receiver_contract.py
"""

from __future__ import annotations

import csv
import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
INVENTORY_PATH = "docs/wood-joints-mvp/source-inventory.json"
KERF_ATTACHMENTS_PATH = "docs/floor-flush-construction-kerf-right/panel-attachment-axes.csv"
KERF_CONNECTIONS_PATH = "docs/floor-flush-construction-kerf-right/connection-axes.csv"
BASE_ATTACHMENTS_PATH = "docs/floor-flush-construction/panel-attachment-axes.csv"
COMPOSITION_PATH = "docs/wood-joints-mvp/hypotheses/wj24-integrated-static/composition.json"
DIAGNOSTIC_PATH = "docs/wood-joints-mvp/hypotheses/wj24-integrated-static/diagnostic.json"
EDGE_AUDIT_PATH = "docs/wood-joints-mvp/wj05-receiver-audit.json"

EXPECTED_REDIRECTS = {
    "round_kicker_left_center_1": "inner_kicker_backer_left",
    "round_kicker_left_center_2": "inner_kicker_backer_left",
    "round_kicker_right_center_1": "inner_kicker_backer_right",
    "round_kicker_right_center_2": "inner_kicker_backer_right",
}
TOLERANCE_MM = 1e-6


def _read_json(relative_path: str) -> dict[str, Any]:
    return json.loads((ROOT / relative_path).read_text())


def _read_csv(relative_path: str, key: str) -> dict[str, dict[str, str]]:
    with (ROOT / relative_path).open(newline="") as stream:
        rows = list(csv.DictReader(stream))
    result = {row[key]: row for row in rows}
    if len(result) != len(rows):
        raise ValueError(f"duplicate {key} values in {relative_path}")
    return result


def _close(a: float, b: float) -> bool:
    return abs(a - b) <= TOLERANCE_MM


def build_report() -> dict[str, Any]:
    inventory = _read_json(INVENTORY_PATH)
    composition = _read_json(COMPOSITION_PATH)
    diagnostic = _read_json(DIAGNOSTIC_PATH)
    edge_audit = _read_json(EDGE_AUDIT_PATH)
    kerf_attachments = _read_csv(KERF_ATTACHMENTS_PATH, "name")
    kerf_connections = _read_csv(KERF_CONNECTIONS_PATH, "name")
    base_attachments = _read_csv(BASE_ATTACHMENTS_PATH, "name")

    axes = inventory.get("fixed_panel_kicker_screws", [])
    by_id = {row["axis_id"]: row for row in axes}
    if len(by_id) != len(axes):
        raise ValueError("source inventory contains duplicate fixed screw axis IDs")
    axis_ids = set(by_id)
    redirects = {
        axis_id: row["candidate_finished_receiver_member"]
        for axis_id, row in by_id.items()
        if row["source_finished_receiver_member"]
        != row["candidate_finished_receiver_member"]
    }
    if len(axes) != 66:
        raise ValueError(f"expected 66 inventoried panel/kicker axes, found {len(axes)}")
    if redirects != EXPECTED_REDIRECTS:
        raise ValueError(f"four-backer redirect map changed: {redirects!r}")

    diag_receivers = diagnostic["fixed_66_receiver_checks"]
    per_axis = diag_receivers["per_axis"]
    if set(per_axis) != axis_ids:
        raise ValueError("WJ24 diagnostic axis IDs differ from source inventory")
    if set(composition["fixed_panel_axes"]) != axis_ids:
        raise ValueError("WJ24 composition axis IDs differ from source inventory")

    rows: list[dict[str, Any]] = []
    receiver_counts: Counter[str] = Counter()
    cut_owners: Counter[str] = Counter()
    for axis_id in sorted(axis_ids):
        axis = by_id[axis_id]
        shop = kerf_attachments.get(axis_id)
        connection = kerf_connections.get(axis_id)
        baseline = base_attachments.get(axis_id)
        finding = per_axis[axis_id]
        if shop is None or connection is None or baseline is None:
            raise ValueError(f"axis missing from a shop/coordinate table: {axis_id}")
        receiver = axis["candidate_finished_receiver_member"]
        if shop["panel"] != axis["panel_member"]:
            raise ValueError(f"panel mismatch for {axis_id}")
        if shop["receiver"] != axis["source_finished_receiver_member"]:
            raise ValueError(f"selected-baseline/shop receiver mismatch for {axis_id}")
        if connection["kind"] != "screw":
            raise ValueError(f"non-screw connection row for {axis_id}")
        if connection["first_member"] != axis["panel_member"]:
            raise ValueError(f"panel axis member mismatch for {axis_id}")
        if connection["second_member"] != axis["source_finished_receiver_member"]:
            raise ValueError(f"source receiver mismatch for {axis_id}")
        if axis["shop_opening_kind"] != "hillman_panel":
            raise ValueError(f"unexpected shop hardware policy for {axis_id}")
        if float(axis["shop_purchased_length_mm"]) != 63.5:
            raise ValueError(f"purchased Hillman length changed for {axis_id}")
        if float(shop["shop_purchased_length_mm"]) != 63.5:
            raise ValueError(f"shop packet length changed for {axis_id}")

        for coordinate in ("x", "y", "z"):
            inventory_value = float(
                axis["origin_global_xyz_mm"]["xyz".index(coordinate)]
            )
            connection_value = float(connection[f"start_{coordinate}_mm"])
            if not _close(inventory_value, connection_value):
                raise ValueError(f"global {coordinate} coordinate mismatch for {axis_id}")
            axis_value = float(axis["axis_global_xyz"]["xyz".index(coordinate)])
            connection_axis_value = float(connection[f"direction_{coordinate}"])
            if not _close(axis_value, connection_axis_value):
                raise ValueError(f"global {coordinate} direction mismatch for {axis_id}")

        if finding["candidate_receiver_member"] != receiver:
            raise ValueError(f"diagnostic receiver mismatch for {axis_id}")
        if not finding["raw_receiver_material_present"]:
            raise ValueError(f"diagnostic lacks receiver material for {axis_id}")
        if not finding["receiver_present_in_finished_scene"]:
            raise ValueError(f"receiver missing from finished scene for {axis_id}")
        if not finding["purchase_cut_present_on_composed_receiver"]:
            raise ValueError(f"purchase cut missing from finished receiver for {axis_id}")
        if not finding["finished_receiver_clear_of_axis"]:
            raise ValueError(f"occupied analysis axis is not clear after its cut: {axis_id}")
        if float(finding["finished_receiver_axis_overlap_mm3"]) != 0.0:
            raise ValueError(f"finished receiver still overlaps axis envelope: {axis_id}")
        if finding["required_support_or_embedment_evaluated"]:
            raise ValueError(f"unexpected support/embedment acceptance for {axis_id}")
        if finding["thread_embedment_or_capacity_established"]:
            raise ValueError(f"unexpected thread/capacity acceptance for {axis_id}")

        owner = finding["purchase_cut_owner"]
        if owner != ("candidate_part" if axis_id in EXPECTED_REDIRECTS else "source_host"):
            raise ValueError(f"purchase cut owner mismatch for {axis_id}: {owner}")
        receiver_counts[receiver] += 1
        cut_owners[owner] += 1
        rows.append(
            {
                "axis_id": axis_id,
                "panel_member": axis["panel_member"],
                "source_finished_receiver_member": axis[
                    "source_finished_receiver_member"
                ],
                "candidate_finished_receiver_member": receiver,
                "origin_global_xyz_mm": axis["origin_global_xyz_mm"],
                "axis_global_xyz": axis["axis_global_xyz"],
                "purchased_hillman_length_mm": float(
                    axis["shop_purchased_length_mm"]
                ),
                "static_purchase_cut_owner": owner,
                "static_purchase_cut_present": True,
                "static_raw_receiver_present": True,
                "static_finished_axis_envelope_clear": True,
                "required_support_or_embedment_evaluated": False,
                "receiver_to_frame_path_complete_in_inventory": axis[
                    "receiver_to_frame_path_complete"
                ],
                "receiver_to_frame_path": axis["receiver_to_frame_path"],
            }
        )

    if receiver_counts.total() != 66:
        raise ValueError("finished receiver counts do not reconcile to 66")
    if cut_owners != Counter({"source_host": 62, "candidate_part": 4}):
        raise ValueError(f"receiver purchase-cut owner counts changed: {cut_owners}")
    if diag_receivers["required_support_or_embedment_evaluated"] is not False:
        raise ValueError("WJ24 diagnostic unexpectedly accepts support/embedment")
    if not diag_receivers["all_purchase_cuts_present_on_composed_receivers"]:
        raise ValueError("global WJ24 receiver-cut presence gate failed")

    # Recheck the WJ05 three-point inner-edge screen against the current WJ24
    # candidate-part bounds, without expanding the sampled result into a
    # continuous-contact or tolerance claim.
    edge_support = edge_audit["center_receiver_trial"]["inner_kicker_edge_support"]
    backers = composition["candidate_parts"]
    edge_checks: dict[str, Any] = {}
    for side in ("left", "right"):
        backer_id = f"inner_kicker_backer_{side}"
        bounds = backers[backer_id]["finished_shape"]["bounds_xyz_mm"]
        samples = edge_support[side]["sample_points_global_xyz_mm"]
        inside = [
            bounds[0] <= p[0] <= bounds[1]
            and bounds[2] <= p[1] <= bounds[3]
            and bounds[4] <= p[2] <= bounds[5]
            for p in samples
        ]
        if len(samples) != 3 or not all(inside):
            raise ValueError(f"{side} WJ05 edge samples leave WJ24 finished backer")
        if not edge_support[side]["all_inside_receiver"]:
            raise ValueError(f"{side} WJ05 edge-support flag is not true")
        edge_checks[side] = {
            "finished_backer_bounds_xyz_mm": bounds,
            "sample_points_global_xyz_mm": samples,
            "sample_count_inside_finished_backer": sum(inside),
            "source_audit_status": "three_nominal_samples_only",
        }

    # The right K-edge moved with the kerf-right panel datum. The local
    # distance from the installed edge screw axis to that modeled panel edge
    # remains the source packet's 19.05 mm.
    right_kicker_bounds = composition["panel_replacements"]["kicker_right"][
        "bounds_xyz_mm"
    ]
    right_rim = by_id["round_kicker_right_rim_1"]
    right_edge_distance = right_kicker_bounds[1] - right_rim[
        "origin_global_xyz_mm"
    ][0]
    kerf_axis = float(kerf_attachments["round_kicker_right_rim_1"]["from_left_mm"])
    base_axis = float(base_attachments["round_kicker_right_rim_1"]["from_left_mm"])
    if not _close(right_edge_distance, 19.05):
        raise ValueError(f"right kicker K-edge screw distance changed: {right_edge_distance}")
    if not _close(base_axis - kerf_axis, 3.175):
        raise ValueError("kerf-right right-rim screw datum no longer shifts by 3.175 mm")

    false_path_count = sum(
        not row["receiver_to_frame_path_complete"] for row in axes
    )
    if false_path_count != 66:
        raise ValueError(f"receiver-to-frame completion flags changed: {false_path_count}")

    source_provenance = diagnostic["source_provenance"]
    hash_checks: dict[str, bool] = {}
    for relative_path in (
        INVENTORY_PATH,
        KERF_CONNECTIONS_PATH,
        "docs/floor-flush-construction-kerf-right/stock-profiles.json",
        "scripts/wood_joint_wj24_compositor.py",
        "scripts/wood_joint_wj24_diagnostic.py",
    ):
        expected = source_provenance["family_input_sha256"].get(relative_path)
        if expected is None and relative_path == INVENTORY_PATH:
            expected = composition["source_input_hashes_sha256"].get(relative_path)
        if expected is None and relative_path.startswith("scripts/"):
            basename = Path(relative_path).stem.replace("wood_joint_", "")
            producer_key = "wj24_compositor" if basename == "wj24_compositor" else "wj24_diagnostic"
            expected = composition["producer_hashes_sha256"].get(producer_key)
        if expected is None:
            raise ValueError(f"WJ24 recorded provenance omits {relative_path}")
        actual = hashlib.sha256((ROOT / relative_path).read_bytes()).hexdigest()
        hash_checks[relative_path] = actual == expected
        if actual != expected:
            raise ValueError(f"WJ24 source provenance is stale for {relative_path}")

    return {
        "schema": "wood_joint_wj24_fixed_receiver_contract/v1",
        "status": "source_bound_fixed_receiver_reconciliation",
        "candidate": inventory["candidate"],
        "source_commit": inventory["source_commit"],
        "width_variant": inventory["width_variant"],
        "source_inventory_sha256": diagnostic["source_binding"][
            "inventory_sha256"
        ],
        "composition_status": composition["status"],
        "diagnostic_status": diagnostic["status"],
        "counts": {
            "fixed_hillman_axes": len(rows),
            "main_panel_axes": sum(row["panel_member"].startswith("main_") for row in rows),
            "kicker_axes": sum(row["panel_member"].startswith("kicker_") for row in rows),
            "unchanged_candidate_receivers": 62,
            "redirected_candidate_receivers": len(redirects),
            "purchase_cuts_on_source_hosts": cut_owners["source_host"],
            "purchase_cuts_on_candidate_backers": cut_owners["candidate_part"],
            "receiver_to_frame_incomplete": false_path_count,
        },
        "redirects": redirects,
        "receiver_counts": dict(sorted(receiver_counts.items())),
        "static_gates": {
            "all_66_axes_match_inventory_composition_and_diagnostic": True,
            "all_66_shop_rows_match_panel_and_original_receiver": True,
            "all_66_candidate_receivers_have_raw_material": True,
            "all_66_recorded_purchase_cuts_are_present": True,
            "all_66_frozen_axis_envelopes_clear_finished_receiver": True,
            "required_hillman_support_or_embedment_evaluated": False,
            "hillman_thread_embedment_or_capacity_established": False,
            "all_66_receiver_to_frame_paths_complete": False,
        },
        "kerf_right_kicker_edge": {
            "right_panel_k_bounds_xyz_mm": right_kicker_bounds,
            "right_rim_axis_global_x_mm": right_rim["origin_global_xyz_mm"][0],
            "right_k_edge_distance_mm": right_edge_distance,
            "baseline_to_kerf_right_axis_shift_mm": base_axis - kerf_axis,
            "inner_edge_samples": edge_checks,
            "scope": "modeled edge/datum geometry and three WJ05 samples only",
        },
        "provenance_hash_checks": hash_checks,
        "per_axis": rows,
        "claim_boundary": [
            "The 63.5 mm purchased length is not a modeled engagement length.",
            "The static axis envelope is not a Hillman 42605 geometry or resistance model.",
            "Static material presence and cut reconciliation do not establish screw capacity, stiffness, installation, or load transfer.",
            "No continuous contact, build tolerance, physical edge support, inspection, fabrication, or climbing release is established.",
        ],
    }


if __name__ == "__main__":
    print(json.dumps(build_report(), indent=2, sort_keys=True))
