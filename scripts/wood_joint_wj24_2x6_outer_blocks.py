"""Viewer revision using single 2x6 exterior sandwich blocks at the same inner faces."""

from __future__ import annotations

import copy
from dataclasses import replace
from typing import Any

import cadquery as cq

from scripts.wood_joint_wj24_inner_frame_blocks import _axis_diameter, _axis_from_roles
from scripts.wood_joint_wj24_led_clearance import REVISION_ID as INPUT_REVISION_ID
from scripts.wood_joint_wj24_remove_outer_links import (
    _merge_display_ids,
    _nested_proxy,
    _proxy,
)

REVISION_ID = "led-clearance-2x6-runner-seated-blocks-v1"
THICKNESS_MM = 38.1


def build_wj24_2x6_outer_blocks(geometry: Any, prior_report: dict) -> tuple[Any, dict]:
    if geometry.layout_id != INPUT_REVISION_ID or prior_report.get("revision_id") != INPUT_REVISION_ID:
        raise ValueError("2x6 exterior blocks require the current LED-clearance revision")
    raw = dict(geometry.raw_candidate_parts)
    parts = dict(geometry.finished_candidate_parts)
    hardware = {axis: dict(roles) for axis, roles in geometry.candidate_installed_hardware.items()}
    blocks = {}
    axes = {}
    source_parts = {part.name: part.shape for part in geometry.source.parts()}
    for side in ("left", "right"):
        name = f"knee_outer_{side}_spine"
        bounds = raw[name].BoundingBox()
        reduction = bounds.xlen - THICKNESS_MM
        if abs(reduction - 50.8) > 1e-5:
            raise ValueError("expected an 88.9 mm exterior block before the 2x6 change")
        xmin = bounds.xmax - THICKNESS_MM if side == "left" else bounds.xmin
        runner_id = f"base_floor_{side}"
        runner = geometry.finished_hosts.get(runner_id, source_parts[runner_id])
        seat_z = runner.BoundingBox().zmax
        extension = bounds.zmin - seat_z
        if abs(extension - 6.35) > 1e-5:
            raise ValueError("expected the current 6.35 mm block-to-runner gap")
        blank = cq.Solid.makeBox(THICKNESS_MM, bounds.ylen, bounds.zmax - seat_z, cq.Vector(xmin, bounds.ymin, seat_z))
        retained_cuts = raw[name].cut(parts[name])
        raw[name] = blank
        parts[name] = blank.cut(retained_cuts).clean()
        blocks[name] = {
            "before_dimensions_xyz_mm": [bounds.xlen, bounds.ylen, bounds.zlen],
            "after_dimensions_xyz_mm": [THICKNESS_MM, bounds.ylen, bounds.zmax - seat_z],
            "runner_id": runner_id, "runner_seat_z_mm": seat_z,
            "downward_extension_mm": extension,
            "removed_finished_volume_mm3": geometry.finished_candidate_parts[name].Volume() - parts[name].Volume(),
        }
        for axis, bore in geometry.candidate_bores.items():
            if name not in bore.receiver_ids:
                continue
            if next(iter(bore.receiver_ids)) != name:
                raise ValueError(f"{axis}: the current exterior head must start on the block")
            roles = hardware[axis]
            direction = _axis_from_roles(roles, axis)
            if abs(abs(direction.x) - 1.0) > 1e-6:
                raise ValueError(f"{axis}: exterior bolt must be on global X")
            delta = direction * reduction
            shaft = roles["shaft"]
            box = shaft.BoundingBox()
            diameter = _axis_diameter(shaft, direction, axis)
            start = cq.Vector(box.xmin if direction.x > 0 else box.xmax, (box.ymin + box.ymax) / 2, (box.zmin + box.zmax) / 2)
            length = box.xlen - reduction
            roles["shaft"] = cq.Solid.makeCylinder(diameter / 2, length, start + delta, direction)
            for role in ("head", "head_washer"):
                roles[role] = roles[role].translate(delta)
            axes[axis] = {
                "head_translation_xyz_mm": list(delta.toTuple()),
                "before_occupied_length_mm": box.xlen, "after_occupied_length_mm": length,
                "nut_station_and_tail_end_preserved": True,
                "purchased_length_or_delivered_shank_selected": False,
            }
    if len(axes) != 8:
        raise ValueError("the two exterior blocks must retain exactly eight through-bolt axes")
    checks = {
        "single_2x6_exterior_blocks_retain_inner_contact_faces": True,
        "all_eight_bore_axes_and_nut_stations_preserved": True,
        "shorter_occupied_shafts_preserve_the_prior_tail_ends": True,
        "frame_4x6_members_and_66_panel_screw_axes_preserved": True,
        "blocks_extend_to_runner_tops_without_moving_bore_axes": True,
        "complete_joint_acceptance": False, "installation_proven": False,
        "fabrication_released": False, "structural_released": False,
    }
    revised = replace(
        geometry, layout_id=REVISION_ID, trial_id=REVISION_ID,
        raw_candidate_parts=_proxy(raw), finished_candidate_parts=_proxy(parts),
        candidate_installed_hardware=_nested_proxy(hardware), composition_checks=_proxy(checks),
    )
    report = copy.deepcopy(prior_report)
    report.update({
        "schema": "wood_joint_wj24_2x6_outer_blocks/v1", "revision_id": REVISION_ID,
        "input_revision_id": INPUT_REVISION_ID, "prior_revision_report": copy.deepcopy(prior_report),
        "summary": "The exterior sandwich blocks use single 2x6 blanks and extend down to the floor runners, with shorter bolt envelopes. Tall central blocks are trimmed 5 mm at the outer faces and tops; G2's LED hole, body and wire endpoints move 5 mm outward. Twenty-four blocks retain seven designs and 92 candidate bolt axes.",
        "exterior_block_changes": blocks, "shortened_exterior_bolt_envelopes": axes,
        "changed_display_solid_ids": _merge_display_ids(
            prior_report["changed_display_solid_ids"], {
                "finished_candidate_parts": sorted(blocks),
                "candidate_installed_hardware": sorted(f"{axis}/{role}" for axis in axes for role in hardware[axis]),
            }, set(prior_report.get("removed_display_solid_ids", ())),
        ),
        "checks": checks,
    })
    return revised, report
