"""Trim the tall center blocks and move one LED to clear current viewer details."""

from __future__ import annotations

import copy
from dataclasses import replace
from typing import Any

import cadquery as cq

from mini_moonboard import panel_grid_v2, round_structural_wiring
from scripts.wood_joint_wj24_bolt_orientation import REVISION_ID as INPUT_REVISION_ID
from scripts.wood_joint_wj24_remove_outer_links import (
    _merge_display_ids,
    _nested_proxy,
    _proxy,
)

REVISION_ID = "trimmed-center-blocks-g2-led-clearance-v1"
SIDE_TRIM_MM = 5.0
TOP_TRIM_MM = 5.0
G2_TRANSLATION_MM = (5.0, 0.0, 0.0)
LED_HOLE_DIAMETER_MM = 13.0


def _moved_wire(geometry: Any, name: str) -> tuple[cq.Shape, dict]:
    wiring = round_structural_wiring
    record = copy.deepcopy(next(row for row in wiring.segments() if row["name"] == name))
    original = next(part.shape for part in wiring.parts() if part.name == name)
    current = geometry.protected["wires"][name]
    placement = current.Center() - original.Center()
    placed = original.translate(placement)
    difference = max(0.0, current.Volume() + placed.Volume() - 2 * current.intersect(placed).Volume())
    if difference > 0.03:
        raise ValueError(f"{name}: current wire does not match the retained routing source")
    endpoint = 0 if record["datums"][0] == "G2" else -1
    record["route_local_mm"][endpoint][0] += G2_TRANSLATION_MM[0]
    path = wiring.wire_path(record)
    first, second = [wiring.b.point(*point) for point in record["route_local_mm"][:2]]
    plane = cq.Plane(origin=first, normal=(second - first).normalized())
    shape = cq.Workplane(plane).circle(wiring.CABLE_DIAMETER_MM / 2).sweep(
        cq.Workplane(obj=path), isFrenet=True
    ).val().translate(placement)
    if record["string_connector_envelope"]:
        raise ValueError("this local endpoint revision must not omit a string connector")
    return shape, {
        "datums": record["datums"], "route_local_mm": record["route_local_mm"],
        "source_placement_xyz_mm": list(placement.toTuple()),
        "routed_length_mm": path.Length(),
        "prior_routed_length_mm": next(row["routed_length_mm"] for row in wiring.segments() if row["name"] == name),
        "approximate_path_budget_mm": wiring.APPROXIMATE_PATH_BUDGET_MM,
    }


def build_wj24_led_clearance(geometry: Any, prior_report: dict) -> tuple[Any, dict]:
    if geometry.layout_id != INPUT_REVISION_ID or prior_report.get("revision_id") != INPUT_REVISION_ID:
        raise ValueError("LED clearance requires the oriented common-block revision")
    raw_parts = dict(geometry.raw_candidate_parts)
    parts = dict(geometry.finished_candidate_parts)
    hardware = {axis: dict(roles) for axis, roles in geometry.candidate_installed_hardware.items()}
    block_changes = {}
    changed_axes = []
    for side in ("left", "right"):
        name = f"center_principal_cleat_{side}"
        old = raw_parts[name]
        bounds = old.BoundingBox()
        xmin = bounds.xmin + SIDE_TRIM_MM if side == "left" else bounds.xmin
        blank = cq.Solid.makeBox(
            bounds.xlen - SIDE_TRIM_MM, bounds.ylen, bounds.zlen - TOP_TRIM_MM,
            cq.Vector(xmin, bounds.ymin, bounds.zmin),
        )
        raw_parts[name] = blank
        # Retain every existing cut, including bores, without restoring timber
        # in any previously removed region.
        parts[name] = parts[name].intersect(blank).clean()
        block_changes[name] = {
            "before_dimensions_xyz_mm": [bounds.xlen, bounds.ylen, bounds.zlen],
            "after_dimensions_xyz_mm": [bounds.xlen - SIDE_TRIM_MM, bounds.ylen, bounds.zlen - TOP_TRIM_MM],
            "removed_finished_volume_mm3": geometry.finished_candidate_parts[name].Volume() - parts[name].Volume(),
        }
        for axis, bore in geometry.candidate_bores.items():
            if name not in bore.receiver_ids:
                continue
            if next(iter(bore.receiver_ids)) != name:
                raise ValueError(f"{axis}: expected the current head on the trimmed block")
            delta = (0.0, 0.0, -TOP_TRIM_MM) if "header" in axis else (
                SIDE_TRIM_MM if side == "left" else -SIDE_TRIM_MM, 0.0, 0.0
            )
            for role in ("head", "head_washer", "shaft"):
                hardware[axis][role] = hardware[axis][role].translate(delta)
            changed_axes.append(axis)

    panels = dict(geometry.panel_replacements)
    panel_id = "main_lower_right"
    panel = panels[panel_id]
    x, station = panel_grid_v2.main_led_datums()["G2"]
    normal = geometry.source.b.normal().normalized()
    rear = geometry.source.b.point(x - geometry.source.b.HALF, station, 0.0)
    thickness = next(p.blank[2] for p in geometry.source.parts() if p.name == panel_id)
    old_hole = cq.Solid.makeCylinder(LED_HOLE_DIAMETER_MM / 2, thickness, rear - normal * thickness, normal)
    if panel.intersect(old_hole).Volume() > 1e-4:
        raise ValueError("recorded G2 hole is not clear in the current panel")
    new_hole = old_hole.translate(G2_TRANSLATION_MM)
    # Close the former nominal hole in CAD, then cut the translated one. This
    # is a new panel layout, not an instruction to patch/redrill a built panel.
    panels[panel_id] = panel.fuse(old_hole).clean().cut(new_hole).clean()
    protected = {family: dict(shapes) for family, shapes in geometry.protected.items()}
    protected["lights"]["light_G2"] = protected["lights"]["light_G2"].translate(G2_TRANSLATION_MM)
    wire_records = {}
    for name in ("wire_073_G1_G2", "wire_074_G2_G3"):
        protected["wires"][name], wire_records[name] = _moved_wire(geometry, name)
    electrical_ids = {"light_G2": "lights", **{name: "wires" for name in wire_records}}
    checks = {
        "two_tall_blocks_trimmed_without_changing_bore_axes": True,
        "heads_and_shafts_follow_trimmed_faces_nuts_remain_seated": True,
        "g2_led_hole_body_and_two_wire_endpoints_move_together": True,
        "panel_outlines_hold_tnuts_and_66_panel_screws_preserved": True,
        "occupied_bolt_lengths_preserved_delivered_shank_unresolved": True,
        "complete_joint_acceptance": False, "installation_proven": False,
        "fabrication_released": False, "structural_released": False,
    }
    revised = replace(
        geometry, layout_id=REVISION_ID, trial_id=REVISION_ID,
        raw_candidate_parts=_proxy(raw_parts), finished_candidate_parts=_proxy(parts),
        candidate_installed_hardware=_nested_proxy(hardware), panel_replacements=_proxy(panels),
        protected=_nested_proxy(protected), composition_checks=_proxy(checks),
    )
    report = copy.deepcopy(prior_report)
    report.update({
        "schema": "wood_joint_wj24_led_clearance/v1", "revision_id": REVISION_ID,
        "input_revision_id": INPUT_REVISION_ID, "prior_revision_report": copy.deepcopy(prior_report),
        "summary": "The two tall central blocks are 5 mm thinner at their outer faces and 5 mm shorter at the top. G2's 13 mm LED hole and light move 5 mm outward, with both adjacent wire endpoints updated. The shared member-block drilling pattern is preserved.",
        "block_trims": block_changes, "reseated_candidate_axis_ids": changed_axes,
        "led_datum_overrides_mm": {"G2": [x + G2_TRANSLATION_MM[0], station]},
        "led_move": {"label": "G2", "translation_xyz_mm": list(G2_TRANSLATION_MM), "hole_diameter_mm": LED_HOLE_DIAMETER_MM, "old_rear_xyz_mm": list(rear.toTuple()), "new_rear_xyz_mm": list((rear + cq.Vector(*G2_TRANSLATION_MM)).toTuple())},
        "wire_endpoint_revisions": wire_records, "electrical_replacements": electrical_ids,
        "changed_display_solid_ids": _merge_display_ids(
            prior_report["changed_display_solid_ids"], {
                "finished_candidate_parts": sorted(block_changes), "panel_replacements": [panel_id],
                "candidate_installed_hardware": sorted(f"{axis}/{role}" for axis in changed_axes for role in hardware[axis]),
                "electrical_replacements": sorted(electrical_ids),
            }, set(prior_report.get("removed_display_solid_ids", ())),
        ),
        "checks": checks,
    })
    return revised, report
