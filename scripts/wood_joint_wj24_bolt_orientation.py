"""Apply a recorded, collision-screened bolt-orientation audit to viewer CAD."""

from __future__ import annotations

import copy
from dataclasses import replace
from typing import Any

import cadquery as cq

from scripts.wood_joint_wj24_inner_frame_blocks import _axis_from_roles
from scripts.wood_joint_wj24_remove_outer_links import (
    _merge_display_ids,
    _nested_proxy,
    _proxy,
)
from scripts.wood_joint_wj24_second_inner_bolts import REVISION_ID as INPUT_REVISION_ID

REVISION_ID = "common-blocks-two-inner-bolts-oriented-v1"


def reverse_stack(roles: dict) -> dict:
    """Reverse the complete stack around the midpoint of its wood-bearing faces."""
    direction = _axis_from_roles(roles, "orientation")
    local = cq.Location(cq.Plane(origin=(0, 0, 0), normal=direction)).inverse
    head_washer = roles["head_washer"]
    nut_washer = roles["nut_washer"]
    near = head_washer.Center() + direction * (head_washer.moved(local).BoundingBox().zlen / 2)
    far = nut_washer.Center() - direction * (nut_washer.moved(local).BoundingBox().zlen / 2)
    pivot = (near + far) * 0.5
    reference = cq.Vector(0, 0, 1) if abs(direction.z) < 0.9 else cq.Vector(1, 0, 0)
    rotation_axis = direction.cross(reference).normalized()
    return {role: shape.rotate(pivot, pivot + rotation_axis, 180) for role, shape in roles.items()}


def build_wj24_bolt_orientation(geometry: Any, prior_report: dict, audit: dict) -> tuple[Any, dict]:
    if (
        geometry.layout_id != INPUT_REVISION_ID
        or prior_report.get("revision_id") != INPUT_REVISION_ID
        or audit.get("revision_input") != INPUT_REVISION_ID
    ):
        raise ValueError("bolt orientation requires the audited two-inner-bolt revision")
    rows = audit["rows"]
    if len(rows) != 92 or {row["axis"] for row in rows} != set(geometry.candidate_bores):
        raise ValueError("orientation audit must cover all 92 current candidate axes")
    changed = [row["axis"] for row in rows if row["flipped"]]
    if any(row.get("new_or_increased_hits") for row in rows if row["flipped"]):
        raise ValueError("a proposed reversal still has a new or increased collision")
    bores = dict(geometry.candidate_bores)
    hardware = {axis: dict(roles) for axis, roles in geometry.candidate_installed_hardware.items()}
    for axis in changed:
        hardware[axis] = reverse_stack(hardware[axis])
        # The bore solid and receiver positions are unchanged; only their
        # head-to-nut order changes. No new drilling variant is introduced.
        bores[axis] = replace(bores[axis], receiver_ids=tuple(reversed(bores[axis].receiver_ids)))
    checks = dict(prior_report["checks"])
    checks.update({
        "orientation_reversals_screened_for_new_installed_collisions": True,
        "orientation_changes_preserve_bore_solids_block_patterns_and_bolt_lengths": True,
        "full_insertion_and_wrench_access_proven": False,
    })
    revised = replace(
        geometry, layout_id=REVISION_ID, trial_id=REVISION_ID,
        candidate_bores=_proxy(bores), candidate_installed_hardware=_nested_proxy(hardware),
        composition_checks=_proxy(checks),
    )
    report = copy.deepcopy(prior_report)
    report.update({
        "schema": "wood_joint_wj24_bolt_orientation/v1",
        "revision_id": REVISION_ID, "input_revision_id": INPUT_REVISION_ID,
        "prior_revision_report": copy.deepcopy(prior_report),
        "summary": f"Twenty-four corner blocks use seven designs; fifteen share one blank and drilling pattern. Each interior sandwich block has two vertical header bolts. {len(changed)} bolt stacks are reversed to face outward or use greater interior head-side room where the geometry screen permits.",
        "bolt_orientation_audit": audit,
        "reversed_candidate_axis_ids": changed,
        "changed_display_solid_ids": _merge_display_ids(
            prior_report["changed_display_solid_ids"], {
                "candidate_installed_hardware": sorted(f"{axis}/{role}" for axis in changed for role in hardware[axis]),
            }, set(prior_report.get("removed_display_solid_ids", ())),
        ),
        "checks": checks,
    })
    return revised, report
