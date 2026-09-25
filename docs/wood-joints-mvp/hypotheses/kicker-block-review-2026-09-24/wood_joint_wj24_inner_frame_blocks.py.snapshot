"""Viewer-only WJ24 interior blocks for the outer-rim/kicker joint.

The two new blocks sit against the inner faces of the outer 4x6 rims and on
the top of the kicker header. Existing outer-spine/rim bolts pass through all
three solids; one additional vertical bolt per block ties it to the header.
This module consumes the already revised WJ24 geometry. It does not compose a
baseline, run mechanics, or select purchasable bolt lengths.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, replace
from math import isclose
from types import MappingProxyType
from typing import Any

import cadquery as cq

SCHEMA = "wood_joint_wj24_inner_frame_blocks/v1"
REVISION_ID = "outer-rim-inner-frame-blocks-v1"
SIDES = ("left", "right")
SIDE_AXIS_IDS = tuple(
    f"knee_outer_{side}_side_{index}" for side in SIDES for index in (1, 2)
)
VERTICAL_AXIS_IDS = {side: f"knee_outer_{side}_inner_header_1" for side in SIDES}
HARDWARE_ROLES = frozenset({"shaft", "head", "head_washer", "nut_washer", "nut"})
FIT_TOLERANCE_MM = 1e-5
FIT_TOLERANCE_MM3 = 1e-5
BORE_EXTENSION_MM = 0.5


@dataclass(frozen=True)
class InnerFrameCandidateBore:
    """A candidate through-bore; receiver_ids follows head-to-nut order."""

    axis_id: str
    family: str
    trial_id: str
    receiver_ids: tuple[str, ...]
    shape: cq.Shape
    station_id: str | None = None


def _proxy(values: Mapping[str, Any]) -> Mapping[str, Any]:
    return MappingProxyType(dict(values))


def _nested_proxy(values: Mapping[str, Mapping[str, Any]]) -> Mapping[str, Mapping[str, Any]]:
    return MappingProxyType({key: MappingProxyType(dict(rows)) for key, rows in values.items()})


def _shape(value: Any, label: str) -> cq.Shape:
    if not isinstance(value, cq.Shape) or not value.isValid() or not value.Solids():
        raise ValueError(f"{label}: expected a valid solid shape")
    return value


def _box(shape: cq.Shape) -> cq.BoundBox:
    return shape.BoundingBox()


def _axis_from_roles(roles: Mapping[str, cq.Shape], axis_id: str) -> cq.Vector:
    if set(roles) != HARDWARE_ROLES:
        raise ValueError(f"{axis_id}: ordinary bolt roles are incomplete")
    head = _shape(roles["head_washer"], f"{axis_id}/head_washer").Center()
    nut = _shape(roles["nut_washer"], f"{axis_id}/nut_washer").Center()
    axis = nut - head
    if axis.Length <= 1e-9:
        raise ValueError(f"{axis_id}: cannot infer a bolt direction")
    return axis.normalized()


def _axis_diameter(shape: cq.Shape, direction: cq.Vector, label: str) -> float:
    box = _box(_shape(shape, label))
    spans = (box.xlen, box.ylen, box.zlen)
    axis_index = max(range(3), key=lambda index: abs(direction.toTuple()[index]))
    transverse = [spans[index] for index in range(3) if index != axis_index]
    if min(transverse) <= 0 or not isclose(transverse[0], transverse[1], abs_tol=1e-4):
        raise ValueError(f"{label}: expected a round, axis-aligned envelope")
    return min(transverse)


def _make_cylinder(diameter: float, start: cq.Vector, direction: cq.Vector, length: float) -> cq.Shape:
    if diameter <= 0 or length <= 0:
        raise ValueError("bolt envelope requires positive diameter and length")
    return cq.Solid.makeCylinder(diameter / 2, length, start, direction)


def _hardware_map(geometry: Any) -> dict[str, dict[str, cq.Shape]]:
    return {axis: dict(roles) for axis, roles in geometry.candidate_installed_hardware.items()}


def _receiver_shape(geometry: Any, member_id: str) -> cq.Shape:
    for name in ("raw_candidate_parts", "raw_hosts"):
        mapping = getattr(geometry, name)
        if member_id in mapping:
            return _shape(mapping[member_id], f"{name}/{member_id}")
    raise ValueError(f"receiver {member_id} is absent from raw WJ24 geometry")


def _rebuild_host(geometry: Any, host_id: str, bores: Mapping[str, Any]) -> cq.Shape:
    raw = _shape(geometry.raw_hosts[host_id], f"raw host {host_id}")
    replaced = set(geometry.replaced_source_cutter_ids)
    retained = [
        cutter
        for cutter_id, cutter in geometry.applied_source_cutters_by_host[host_id].items()
        if cutter_id not in replaced
    ]
    retained.extend(
        bore.shape for bore in bores.values() if host_id in tuple(bore.receiver_ids)
    )
    result = raw.cut(*retained).clean() if retained else raw
    return _shape(result, f"rebuilt host {host_id}")


def _merge_display_ids(prior: Mapping[str, Any], current: Mapping[str, list[str]]) -> dict[str, list[str]]:
    result: dict[str, set[str]] = {}
    for source in (prior, current):
        for key, values in source.items():
            if not isinstance(values, (tuple, list, set, frozenset)):
                raise TypeError(f"changed_display_solid_ids/{key} must be a sequence")
            result.setdefault(str(key), set()).update(map(str, values))
    return {key: sorted(values) for key, values in sorted(result.items())}


def _face_contact(block: cq.Shape, receiver: cq.Shape, label: str) -> dict[str, Any]:
    overlap = float(block.intersect(receiver).Volume())
    distance = float(block.distance(receiver))
    if overlap > FIT_TOLERANCE_MM3:
        raise ValueError(f"{label}: proposed block interpenetrates its receiver")
    if distance > FIT_TOLERANCE_MM:
        raise ValueError(f"{label}: proposed block does not touch its receiver")
    return {
        "intersection_volume_mm3": round(overlap, 9),
        "distance_mm": round(distance, 9),
        "touches_without_solid_overlap": True,
    }


def build_wj24_inner_frame_blocks(
    geometry: Any, prior_report: Mapping[str, Any]
) -> tuple[Any, dict[str, Any]]:
    """Add the requested outer-rim sandwich blocks to current WJ24 geometry.

    This deliberately accepts the current owner-review revision instead of
    requiring the frozen baseline layout ID. The prior report supplies the
    cumulative viewer delta and keeps prior removed solids and panel-axis
    translations intact.
    """
    if not isinstance(prior_report, Mapping):
        raise TypeError("prior_report must be a mapping")
    input_revision = getattr(geometry, "layout_id", None)
    if not input_revision or prior_report.get("revision_id") != input_revision:
        raise ValueError("prior report must describe the supplied current geometry")
    required_maps = (
        "raw_hosts",
        "finished_hosts",
        "raw_candidate_parts",
        "finished_candidate_parts",
        "candidate_bores",
        "candidate_installed_hardware",
        "applied_source_cutters_by_host",
        "replaced_source_cutter_ids",
        "source_inventory",
        "source_binding",
        "source",
        "fixed_axes",
        "frame_bolt_records",
        "frame_bolt_shapes",
    )
    for name in required_maps:
        if not hasattr(geometry, name):
            raise ValueError(f"current WJ24 geometry lacks {name}")
    if not isinstance(geometry.source_inventory, Mapping) or not geometry.source_inventory:
        raise ValueError("current WJ24 source inventory is missing")
    if not geometry.source_binding or len(geometry.frame_bolt_records) != 12:
        raise ValueError("current WJ24 source/frame-bolt binding is incomplete")
    if len(geometry.fixed_axes) != 66:
        raise ValueError("current WJ24 geometry must retain all 66 panel/kicker axes")
    if len(set(prior_report.get("removed_display_solid_ids", ()))) != len(
        prior_report.get("removed_display_solid_ids", ())
    ):
        raise ValueError("prior report contains duplicate removed display IDs")

    raw_hosts = dict(geometry.raw_hosts)
    finished_hosts = dict(geometry.finished_hosts)
    raw_parts = dict(geometry.raw_candidate_parts)
    finished_parts = dict(geometry.finished_candidate_parts)
    bores = dict(geometry.candidate_bores)
    hardware = _hardware_map(geometry)
    for side in SIDES:
        side_id = f"base_side_{side}"
        spine_id = f"knee_outer_{side}_spine"
        for part_id in (side_id, spine_id):
            if part_id not in raw_hosts and part_id not in raw_parts:
                raise ValueError(f"current WJ24 geometry lacks required member {part_id}")
        for axis_id in (f"knee_outer_{side}_side_1", f"knee_outer_{side}_side_2"):
            if axis_id not in bores or axis_id not in hardware:
                raise ValueError(f"current WJ24 geometry lacks outer side bolt {axis_id}")

    header = _shape(raw_hosts.get("base_header"), "raw host base_header")
    header_box = _box(header)
    block_raw: dict[str, cq.Shape] = {}
    block_ids: dict[str, str] = {}
    contact_rows: dict[str, Any] = {}
    block_dims: dict[str, list[float]] = {}
    block_origins: dict[str, list[float]] = {}
    centers: dict[str, cq.Vector] = {}

    for side in SIDES:
        side_id, spine_id = f"base_side_{side}", f"knee_outer_{side}_spine"
        block_id = f"knee_outer_{side}_inner_frame_block"
        block_ids[side] = block_id
        side_box = _box(_shape(raw_hosts[side_id], f"raw host {side_id}"))
        spine_box = _box(_shape(raw_parts[spine_id], f"raw candidate part {spine_id}"))
        width = side_box.xlen
        if not 50.0 <= width <= 140.0:
            raise ValueError(f"{side_id}: implausible X section for a full-section block")
        if side == "left":
            x0 = side_box.xmax
        else:
            x0 = side_box.xmin - width
        y0, y1 = header_box.ymin, min(header_box.ymax, spine_box.ymax)
        z0, z1 = header_box.zmax, spine_box.zmax
        if y1 <= y0 or z1 <= z0:
            raise ValueError(f"{block_id}: header/spine datums do not bound a positive block")
        block = cq.Solid.makeBox(width, y1 - y0, z1 - z0, cq.Vector(x0, y0, z0))
        block_raw[side] = _shape(block, block_id)
        centers[side] = cq.Vector(x0 + width / 2, (y0 + y1) / 2, (z0 + z1) / 2)
        block_dims[side] = [round(width, 6), round(y1 - y0, 6), round(z1 - z0, 6)]
        block_origins[side] = [round(x0, 6), round(y0, 6), round(z0, 6)]
        contact_rows[f"{block_id}/{side_id}"] = _face_contact(block, raw_hosts[side_id], f"{block_id}/{side_id}")
        contact_rows[f"{block_id}/base_header"] = _face_contact(block, header, f"{block_id}/base_header")
        if x0 < header_box.xmin - FIT_TOLERANCE_MM or x0 + width > header_box.xmax + FIT_TOLERANCE_MM:
            raise ValueError(f"{block_id}: proposed seat extends beyond base_header in X")
        if y0 < header_box.ymin - FIT_TOLERANCE_MM or y1 > header_box.ymax + FIT_TOLERANCE_MM:
            raise ValueError(f"{block_id}: proposed seat extends beyond base_header in Y")

    # Preserve both current side-axis lines. Extend their through-bores and
    # stack hardware inboard by exactly one rim section so all three bodies
    # share one bolt stack.
    side_bore_report: dict[str, Any] = {}
    for side in SIDES:
        direction_sign = 1.0 if side == "left" else -1.0
        side_id, spine_id, block_id = f"base_side_{side}", f"knee_outer_{side}_spine", block_ids[side]
        side_box = _box(raw_hosts[side_id])
        spine_box = _box(raw_parts[spine_id])
        added_grip = block_raw[side].BoundingBox().xlen
        three_member_grip = spine_box.xlen + side_box.xlen + added_grip
        for index in (1, 2):
            axis_id = f"knee_outer_{side}_side_{index}"
            bore = bores[axis_id]
            receivers = tuple(getattr(bore, "receiver_ids", ()))
            expected = (spine_id, side_id)
            if receivers != expected:
                raise ValueError(f"{axis_id}: expected the existing exterior-spine/rim receiver order")
            roles = hardware[axis_id]
            direction = _axis_from_roles(roles, axis_id)
            if abs(abs(direction.x) - 1.0) > 1e-6 or abs(direction.y) > 1e-6 or abs(direction.z) > 1e-6:
                raise ValueError(f"{axis_id}: existing side bolt is no longer on global X")
            if direction.x * direction_sign < 0:
                raise ValueError(f"{axis_id}: existing bolt points away from the proposed inner block")
            bore_box = _box(_shape(bore.shape, f"{axis_id} bore"))
            y = (bore_box.ymin + bore_box.ymax) / 2
            z = (bore_box.zmin + bore_box.zmax) / 2
            diameter = _axis_diameter(bore.shape, direction, f"{axis_id} bore")
            outer_face = spine_box.xmin if side == "left" else spine_box.xmax
            start = cq.Vector(outer_face, y, z) - direction * BORE_EXTENSION_MM
            long_bore = _make_cylinder(
                diameter,
                start,
                direction,
                three_member_grip + 2 * BORE_EXTENSION_MM,
            )
            bores[axis_id] = replace(
                bore,
                receiver_ids=(spine_id, side_id, block_id),
                shape=long_bore,
            )

            shaft = _shape(roles["shaft"], f"{axis_id}/shaft")
            shaft_box = _box(shaft)
            shaft_diameter = _axis_diameter(shaft, direction, f"{axis_id}/shaft")
            shaft_start = cq.Vector(
                shaft_box.xmin if direction.x > 0 else shaft_box.xmax,
                (shaft_box.ymin + shaft_box.ymax) / 2,
                (shaft_box.zmin + shaft_box.zmax) / 2,
            )
            old_envelope = shaft_box.xlen
            new_envelope = old_envelope + added_grip
            roles["shaft"] = _make_cylinder(shaft_diameter, shaft_start, direction, new_envelope)
            shift = direction * added_grip
            roles["nut_washer"] = _shape(roles["nut_washer"], f"{axis_id}/nut_washer").translate(shift)
            roles["nut"] = _shape(roles["nut"], f"{axis_id}/nut").translate(shift)
            hardware[axis_id] = roles
            side_bore_report[axis_id] = {
                "receiver_ids_head_to_nut": [spine_id, side_id, block_id],
                "preserved_global_yz_station_mm": [round(y, 6), round(z, 6)],
                "axis_global_xyz": [round(value, 9) for value in direction.toTuple()],
                "wood_grip_mm": round(three_member_grip, 6),
                "previous_nominal_under_head_envelope_mm": round(old_envelope, 6),
                "new_nominal_under_head_envelope_mm": round(new_envelope, 6),
                "envelope_is_not_a_purchased_length_selection": True,
            }

    # One top-down-through-block/header stack per side, in the unobstructed
    # front strip. The location is data-bound to current member bounds.
    vertical_report: dict[str, Any] = {}
    vertical_bores: dict[str, cq.Shape] = {}
    for side in SIDES:
        axis_id = VERTICAL_AXIS_IDS[side]
        if axis_id in bores:
            raise ValueError(f"new axis ID already exists: {axis_id}")
        block_id = block_ids[side]
        block = block_raw[side]
        block_box = _box(block)
        under_link_id = f"knee_outer_{side}_under_header_link"
        under_link = _shape(raw_parts[under_link_id], f"raw candidate part {under_link_id}")
        link_box = _box(under_link)
        y = min(block_box.ymax - 20.0, header_box.ymax - 20.0)
        if y <= link_box.ymax + 20.0:
            raise ValueError(f"{axis_id}: no front-strip separation from the retained under-header link")
        x = centers[side].x
        template_id = f"knee_outer_{side}_header_1"
        template_bore = bores.get(template_id)
        template_roles = hardware.get(template_id)
        if template_bore is None or template_roles is None:
            raise ValueError(f"{axis_id}: missing same-side vertical bolt envelope template")
        template_direction = _axis_from_roles(template_roles, template_id)
        if abs(abs(template_direction.z) - 1.0) > 1e-6:
            raise ValueError(f"{template_id}: expected an existing vertical bolt stack")
        direction = cq.Vector(0, 0, -1)
        if (template_direction - direction).Length > 1e-6:
            raise ValueError(f"{template_id}: head-to-nut direction must point down through the header")
        template_receivers = tuple(template_bore.receiver_ids)
        if "base_header" not in template_receivers:
            raise ValueError(f"{template_id}: vertical template omits base_header")
        old_end_id = template_receivers[-1]
        old_end = _box(_receiver_shape(geometry, old_end_id))
        old_grip = sum(
            _box(_receiver_shape(geometry, member)).zlen for member in template_receivers
        )
        new_grip = block_box.zlen + header_box.zlen
        delta_grip = new_grip - old_grip
        template_shaft = _shape(template_roles["shaft"], f"{template_id}/shaft")
        template_shaft_box = _box(template_shaft)
        shaft_diameter = _axis_diameter(template_shaft, template_direction, f"{template_id}/shaft")
        under_head_length = template_shaft_box.zlen + delta_grip
        if under_head_length <= 0:
            raise ValueError(f"{axis_id}: invalid model bolt envelope length")
        bore_diameter = _axis_diameter(template_bore.shape, template_direction, f"{template_id} bore")
        start = cq.Vector(x, y, block_box.zmax + BORE_EXTENSION_MM)
        bore_shape = _make_cylinder(
            bore_diameter,
            start,
            direction,
            new_grip + 2 * BORE_EXTENSION_MM,
        )
        bore_record = InnerFrameCandidateBore(
            axis_id=axis_id,
            family=str(template_bore.family),
            trial_id=str(template_bore.trial_id),
            receiver_ids=(block_id, "base_header"),
            shape=bore_shape,
            station_id=f"knee_outer_{side}_inner_frame_block",
        )
        bores[axis_id] = bore_record
        vertical_bores[side] = bore_shape

        template_head_washer = _shape(template_roles["head_washer"], f"{template_id}/head_washer")
        head_box = _box(template_head_washer)
        head_delta = cq.Vector(
            x - template_head_washer.Center().x,
            y - template_head_washer.Center().y,
            block_box.zmax - head_box.zmin,
        )
        template_nut_washer = _shape(template_roles["nut_washer"], f"{template_id}/nut_washer")
        end_delta = cq.Vector(
            x - template_nut_washer.Center().x,
            y - template_nut_washer.Center().y,
            header_box.zmin - old_end.zmin,
        )
        new_roles = {
            "head": _shape(template_roles["head"], f"{template_id}/head").translate(head_delta),
            "head_washer": template_head_washer.translate(head_delta),
            "nut_washer": template_nut_washer.translate(end_delta),
            "nut": _shape(template_roles["nut"], f"{template_id}/nut").translate(end_delta),
            "shaft": _make_cylinder(
                shaft_diameter,
                cq.Vector(x, y, block_box.zmax + head_box.zlen),
                direction,
                under_head_length,
            ),
        }
        hardware[axis_id] = new_roles
        vertical_report[axis_id] = {
            "receiver_ids_head_to_nut": [block_id, "base_header"],
            "origin_global_xyz_mm": [round(x, 6), round(y, 6), round(block_box.zmax, 6)],
            "axis_global_xyz": [0.0, 0.0, -1.0],
            "wood_grip_mm": round(new_grip, 6),
            "nominal_under_head_envelope_mm": round(under_head_length, 6),
            "envelope_is_not_a_purchased_length_selection": True,
            "nut_access_side": "below base_header in the clear front strip",
        }

    # Recut the new receiver blocks, and extend the affected exterior spine
    # bores. Host rebuilds replay all retained source cuts and every live
    # candidate bore, including the already revised header obligations.
    for side in SIDES:
        block_id = block_ids[side]
        side_axes = [f"knee_outer_{side}_side_{index}" for index in (1, 2)]
        cutter_shapes = [bores[axis].shape for axis in side_axes]
        cutter_shapes.append(vertical_bores[side])
        raw_parts[block_id] = block_raw[side]
        finished_parts[block_id] = _shape(block_raw[side].cut(*cutter_shapes).clean(), f"finished {block_id}")
        spine_id = f"knee_outer_{side}_spine"
        old_finished = _shape(finished_parts[spine_id], f"finished candidate part {spine_id}")
        finished_parts[spine_id] = _shape(
            old_finished.cut(*(bores[axis].shape for axis in side_axes)).clean(),
            f"remachined {spine_id}",
        )

    changed_hosts = {"base_header", "base_side_left", "base_side_right"}
    for host_id in sorted(changed_hosts):
        if host_id not in raw_hosts or host_id not in geometry.applied_source_cutters_by_host:
            raise ValueError(f"current WJ24 maps omit affected host {host_id}")
        finished_hosts[host_id] = _rebuild_host(geometry, host_id, bores)

    # Confirm the new block lies in full contact at both requested interfaces.
    for side in SIDES:
        block_id = block_ids[side]
        contact_rows[f"{block_id}/remachined_{side}_rim"] = _face_contact(
            finished_parts[block_id], finished_hosts[f"base_side_{side}"], f"{block_id}/rim"
        )
        contact_rows[f"{block_id}/remachined_header"] = _face_contact(
            finished_parts[block_id], finished_hosts["base_header"], f"{block_id}/header"
        )

    prior_changed = prior_report.get("changed_display_solid_ids")
    if not isinstance(prior_changed, Mapping):
        raise TypeError("prior report changed_display_solid_ids must be a mapping")
    changed_now = {
        "finished_hosts": sorted(changed_hosts),
        "finished_candidate_parts": sorted(
            {block_ids[side] for side in SIDES}
            | {f"knee_outer_{side}_spine" for side in SIDES}
        ),
        "candidate_installed_hardware": sorted(
            f"{axis}/{role}"
            for axis in (*SIDE_AXIS_IDS, *VERTICAL_AXIS_IDS.values())
            for role in hardware[axis]
        ),
        "panel_replacements": [],
        "fixed_panel_axes": [],
    }
    changed_display = _merge_display_ids(prior_changed, changed_now)
    removed = list(prior_report.get("removed_display_solid_ids", ()))
    moved_panel_axes = list(prior_report.get("moved_panel_axes", ()))
    moved_ids = [row["axis_id"] for row in moved_panel_axes if isinstance(row, Mapping) and row.get("axis_id")]
    if len(moved_ids) != len(set(moved_ids)):
        raise ValueError("prior report has duplicate moved panel axes")
    if len(geometry.frame_bolt_records) != 12 or len(geometry.fixed_axes) != 66:
        raise ValueError("outer block revision changed protected bolt or panel-axis counts")

    checks = {
        "two_inner_full_section_blocks_created": len(block_ids) == 2,
        "four_outer_side_axes_extend_through_spine_rim_and_inner_block": len(SIDE_AXIS_IDS) == 4,
        "one_vertical_inner_block_to_header_axis_per_side": len(VERTICAL_AXIS_IDS) == 2,
        "all_66_fixed_panel_axes_preserved": len(geometry.fixed_axes) == 66,
        "all_12_starting_frame_bolts_preserved": len(geometry.frame_bolt_records) == 12,
        "no_forces_or_joint_capacity_claimed": True,
        "hardware_envelopes_are_not_purchase_selections": True,
        "complete_joint_acceptance": False,
        "installation_proven": False,
        "fabrication_released": False,
        "structural_released": False,
    }
    revised = replace(
        geometry,
        layout_id=REVISION_ID,
        trial_id=REVISION_ID,
        raw_hosts=_proxy(raw_hosts),
        finished_hosts=_proxy(finished_hosts),
        raw_candidate_parts=_proxy(raw_parts),
        finished_candidate_parts=_proxy(finished_parts),
        candidate_bores=_proxy(bores),
        candidate_installed_hardware=_nested_proxy(hardware),
        composition_checks=_proxy(checks),
    )
    report = {
        "schema": SCHEMA,
        "status": "unaccepted_viewer_geometry_revision",
        "revision_id": REVISION_ID,
        "base_revision_id": input_revision,
        "prior_revision_report": dict(prior_report),
        "summary": "Solid interior blocks sandwich each outer 4x6 rim with its existing exterior spine; the retained X-axis bolts pass through all three members and each block is vertically through-bolted to the kicker header.",
        "block_ids_by_side": block_ids,
        "block_min_corner_xyz_mm_by_side": block_origins,
        "block_dimensions_xyz_mm_by_side": block_dims,
        "blocks_seated_on_header_top_global_z_mm": round(header_box.zmax, 6),
        "outer_rim_side_bolts": side_bore_report,
        "vertical_block_header_bolts": vertical_report,
        "basic_contacts": contact_rows,
        "rebuilt_host_ids": sorted(changed_hosts),
        "host_rebuild_method": "raw current hosts minus all retained source/panel cuts and all current candidate bores",
        "moved_panel_axes": moved_panel_axes,
        "baseline_display_translations_mm": dict(
            prior_report.get("baseline_display_translations_mm", {})
        ),
        "removed_candidate_part_ids": list(prior_report.get("removed_candidate_part_ids", ())),
        "removed_candidate_axis_ids": list(prior_report.get("removed_candidate_axis_ids", ())),
        "moved_candidate_axis_ids": list(prior_report.get("moved_candidate_axis_ids", ())),
        "removed_display_solid_ids": sorted(set(removed)),
        "changed_display_solid_ids": changed_display,
        "checks": checks,
        "claim_boundary": "geometry and member-envelope model only; no force, capacity, delivered-hardware, assembly, installation, or fabrication conclusion",
    }
    return revised, report
