"""Add the owner's second vertical through-bolt to each interior sandwich block."""

from __future__ import annotations

import copy
from dataclasses import replace
from typing import Any

from scripts.wood_joint_wj24_common_blocks import REVISION_ID as INPUT_REVISION_ID
from scripts.wood_joint_wj24_remove_outer_links import (
    _merge_display_ids,
    _nested_proxy,
    _proxy,
    _rebuild_candidate_part,
    _rebuild_host,
)

REVISION_ID = "common-blocks-two-inner-header-bolts-v1"
SECOND_AXIS_EDGE_OFFSET_MM = 20.0


def build_wj24_second_inner_bolts(geometry: Any, prior_report: dict) -> tuple[Any, dict]:
    if geometry.layout_id != INPUT_REVISION_ID or prior_report.get("revision_id") != INPUT_REVISION_ID:
        raise ValueError("second inner bolts require the common-block consolidation")
    bores = dict(geometry.candidate_bores)
    hardware = {axis: dict(roles) for axis, roles in geometry.candidate_installed_hardware.items()}
    parts = dict(geometry.finished_candidate_parts)
    hosts = dict(geometry.finished_hosts)
    new_axes = {}
    part_replay = {}
    for side in ("left", "right"):
        template = f"knee_outer_{side}_inner_header_1"
        axis = f"knee_outer_{side}_inner_header_2"
        part = f"knee_outer_{side}_inner_frame_block"
        if axis in bores or tuple(bores[template].receiver_ids) != (part, "base_header"):
            raise ValueError(f"unexpected second-bolt receiver or axis: {axis}")
        box = geometry.raw_candidate_parts[part].BoundingBox()
        y = box.ymin + SECOND_AXIS_EDGE_OFFSET_MM
        delta = (0.0, y - hardware[template]["shaft"].Center().y, 0.0)
        bores[axis] = replace(bores[template], axis_id=axis, shape=bores[template].shape.translate(delta))
        hardware[axis] = {role: shape.translate(delta) for role, shape in hardware[template].items()}
        parts[part], part_replay[part] = _rebuild_candidate_part(geometry, part, bores)
        new_axes[axis] = {
            "template_axis": template, "translation_xyz_mm": list(delta),
            "center_y_mm": y, "vertical_axis_spacing_mm": abs(delta[1]),
            "end_axis_distance_mm": SECOND_AXIS_EDGE_OFFSET_MM,
            "receiver_ids": [part, "base_header"],
            "purchased_length_selected": False,
        }
    hosts["base_header"], host_replay = _rebuild_host(geometry, "base_header", bores)
    if len(bores) != 92 or sum(map(len, hardware.values())) != 460:
        raise ValueError("second-bolt revision must have 92 axes and 460 hardware roles")
    checks = dict(prior_report["checks"])
    checks["two_vertical_inner_block_header_bolts_per_side"] = True
    revised = replace(
        geometry, layout_id=REVISION_ID, trial_id=REVISION_ID,
        finished_hosts=_proxy(hosts), finished_candidate_parts=_proxy(parts),
        candidate_bores=_proxy(bores), candidate_installed_hardware=_nested_proxy(hardware),
        composition_checks=_proxy(checks),
    )
    report = copy.deepcopy(prior_report)
    report.update({
        "schema": "wood_joint_wj24_second_inner_bolts/v1",
        "revision_id": REVISION_ID, "input_revision_id": INPUT_REVISION_ID,
        "prior_revision_report": copy.deepcopy(prior_report),
        "summary": "Twenty-four corner blocks use seven designs; fifteen share one blank and drilling pattern. Each interior sandwich block now has two vertical bolts through the kicker header. The two existing bottom-center bolt-tail clashes remain open.",
        "added_candidate_axes": new_axes,
        "changed_display_solid_ids": _merge_display_ids(
            prior_report["changed_display_solid_ids"], {
                "finished_hosts": ["base_header"],
                "finished_candidate_parts": sorted(part_replay),
                "candidate_installed_hardware": sorted(f"{axis}/{role}" for axis in new_axes for role in hardware[axis]),
            }, set(prior_report.get("removed_display_solid_ids", ())),
        ),
        "affected_receiver_ids": {"raw_hosts": ["base_header"], "retained_candidate_parts": sorted(part_replay)},
        "host_replay": {"base_header": host_replay}, "candidate_part_replay": part_replay,
        "preserved_counts": {
            "candidate_parts_before_after": [24, 24], "candidate_axes_before_after": [90, 92],
            "candidate_hardware_roles_before_after": [450, 460],
            "fixed_panel_axes": 66, "starting_frame_bolts": 12,
        },
        "checks": checks,
    })
    return revised, report
