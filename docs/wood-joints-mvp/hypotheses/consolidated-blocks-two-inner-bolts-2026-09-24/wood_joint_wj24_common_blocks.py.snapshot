"""Apply the owner-selected common block pattern to the current viewer geometry.

The frozen comparison supplies translations, not new holes alongside old ones.
Rebuild receivers from raw stock and retained cuts. Bolt lengths remain as in
the comparison; the two documented bolt-tail clashes are still open.
"""

from __future__ import annotations

import copy
import hashlib
import json
from dataclasses import replace
from pathlib import Path
from typing import Any

from scripts.wood_joint_wj24_remove_outer_links import (
    _merge_display_ids,
    _merge_ids,
    _nested_proxy,
    _proxy,
    _rebuild_candidate_part,
    _rebuild_host,
)

ROOT = Path(__file__).resolve().parents[1]
STUDY = ROOT / "docs/wood-joints-mvp/hypotheses/common-corner-block-study-2026-09-24"
INPUT_REVISION_ID = "outer-rear-bridges-under-header-links-removed-v1"
REVISION_ID = "common-corner-blocks-seven-designs-v1"


def build_wj24_common_blocks(geometry: Any, prior_report: dict) -> tuple[Any, dict]:
    """Return revised CAD and a cumulative source-bound viewer report."""
    if (
        geometry.layout_id != INPUT_REVISION_ID
        or geometry.trial_id != INPUT_REVISION_ID
        or prior_report.get("revision_id") != INPUT_REVISION_ID
    ):
        raise ValueError("common blocks require the recorded outer-links-removed revision")
    plan_raw = (STUDY / "pattern-comparison.json").read_bytes()
    plan = json.loads(plan_raw)
    bores = dict(geometry.candidate_bores)
    hardware = {axis: dict(roles) for axis, roles in geometry.candidate_installed_hardware.items()}
    changed_parts = []
    translations = {}
    for fit in plan["fits"]:
        if fit["max_shift_mm"] < 1e-5:
            continue
        part = fit["part"]
        changed_parts.append(part)
        for pair in fit["pairs"]:
            if pair["center_shift_mm"] < 1e-5:
                continue
            axis = pair["target_axis"]
            if axis in translations or part not in bores[axis].receiver_ids:
                raise ValueError(f"invalid common-block axis ownership: {axis}")
            delta = tuple(pair["translation_global_xyz_mm"])
            translations[axis] = list(delta)
            bores[axis] = replace(bores[axis], shape=bores[axis].shape.translate(delta))
            hardware[axis] = {role: shape.translate(delta) for role, shape in hardware[axis].items()}
    if len(changed_parts) != 7 or len(translations) != 24:
        raise ValueError("the frozen common-block plan must change seven blocks and 24 axes")
    affected_hosts = {
        receiver for axis in translations for receiver in bores[axis].receiver_ids
        if receiver in geometry.raw_hosts
    }
    affected_parts = {
        receiver for axis in translations for receiver in bores[axis].receiver_ids
        if receiver in geometry.raw_candidate_parts
    }
    if affected_parts != set(changed_parts):
        raise ValueError("common-block plan affects an unexpected candidate receiver")
    hosts = dict(geometry.finished_hosts)
    parts = dict(geometry.finished_candidate_parts)
    host_replay = {}
    part_replay = {}
    for name in sorted(affected_hosts):
        hosts[name], host_replay[name] = _rebuild_host(geometry, name, bores)
    for name in sorted(affected_parts):
        parts[name], part_replay[name] = _rebuild_candidate_part(geometry, name, bores)
    if (len(parts), len(bores), len(geometry.fixed_axes), len(geometry.frame_bolt_records)) != (24, 90, 66, 12):
        raise ValueError("common-block consolidation changed the required inventory")
    checks = {
        "seven_blocks_and_24_axes_use_the_frozen_common_pattern": True,
        "affected_receivers_rebuilt_from_raw_stock_without_old_holes": True,
        "all_66_panel_axes_and_12_starting_frame_bolts_preserved": True,
        "block_blanks_and_positions_preserved": True,
        "bolt_length_envelopes_preserved_tail_detail_still_open": True,
        "complete_joint_acceptance": False,
        "installation_proven": False,
        "fabrication_released": False,
        "structural_released": False,
    }
    revised = replace(
        geometry, layout_id=REVISION_ID, trial_id=REVISION_ID,
        finished_hosts=_proxy(hosts), finished_candidate_parts=_proxy(parts),
        candidate_bores=_proxy(bores), candidate_installed_hardware=_nested_proxy(hardware),
        composition_checks=_proxy(checks),
    )
    report = copy.deepcopy(prior_report)
    report.update({
        "schema": "wood_joint_wj24_common_blocks/v1",
        "revision_id": REVISION_ID,
        "input_revision_id": INPUT_REVISION_ID,
        "prior_revision_report": copy.deepcopy(prior_report),
        "summary": "Twenty-four corner blocks now use seven designs. Fifteen share one blank and drilling pattern; seven blocks and 24 bolt axes were revised. The two existing bottom-center bolt-tail clashes remain open.",
        "owner_selected_geometry_consolidation": True,
        "common_block_plan_sha256": hashlib.sha256(plan_raw).hexdigest(),
        "common_block_template": plan["template"],
        "common_block_axis_translations_xyz_mm": translations,
        "moved_candidate_axis_ids": _merge_ids(prior_report.get("moved_candidate_axis_ids", ()), list(translations)),
        "changed_display_solid_ids": _merge_display_ids(
            prior_report["changed_display_solid_ids"], {
                "finished_hosts": sorted(affected_hosts),
                "finished_candidate_parts": sorted(affected_parts),
                "candidate_installed_hardware": sorted(f"{axis}/{role}" for axis in translations for role in hardware[axis]),
            }, set(prior_report.get("removed_display_solid_ids", ())),
        ),
        "affected_receiver_ids": {"raw_hosts": sorted(affected_hosts), "retained_candidate_parts": sorted(affected_parts)},
        "host_replay": host_replay,
        "candidate_part_replay": part_replay,
        "checks": checks,
        "joint_evaluations_run": False,
    })
    # Those restoration/identity checks described the previous operation only.
    report.pop("removed_hole_restoration_mm3", None)
    report.pop("retained_neighbor_findings_geometry_identity_checked", None)
    report["preserved_counts"] = {
        "candidate_parts_before_after": [24, 24], "candidate_axes_before_after": [90, 90],
        "candidate_hardware_roles_before_after": [450, 450],
        "fixed_panel_axes": 66, "starting_frame_bolts": 12,
    }
    report["findings"].extend([
        {"title": "Bottom-center bolt tails need a length detail", "detail": "Two rail-bolt tails intersect the enlarged central header blocks, as in the comparison. A 3 mm shorter occupied-tail sensitivity clears timber, but no shorter purchased bolt or delivered shank has been selected. Current shaft lengths are unchanged."},
        {"title": "G12 hold-bolt clearance", "detail": "The top-right center block retains its existing overlap with the provisional G12 hold-bolt envelope. Consolidation does not resolve it."},
        {"title": "Midpoint maps describe the preceding revision", "detail": "The 491-site midpoint screen remains bound to the outer-links-removed revision. It has not been rerun after moving these bolt axes and receiver holes."},
    ])
    return revised, report
