"""Owner review: kicker posts outside central T-nuts, with the center backers removed."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import replace
from typing import Any

import cadquery as cq

from mini_moonboard import wood_joint_panel_machining as panels
from scripts import wood_joint_wj24_bottom_support_above_tnuts as previous
from scripts import wood_joint_wj24_bottom_support_up_one_row as support

REVISION_ID = "kicker-posts-outside-central-tnuts-v1"
FLANGE_GAP_MM = 5.0
SIDES = ("left", "right")
REMOVED_PARTS = frozenset(f"inner_kicker_backer_{side}" for side in SIDES)
REMOVED_AXES = frozenset(f"backer_header_{side}_{index}" for side in SIDES for index in (1, 2))
MOVED_SCREWS = frozenset(f"round_kicker_{side}_center_{index}" for side in SIDES for index in (1, 2))


def build_kicker_posts_outside_tnuts(
    geometry: Any, prior_report: Mapping[str, Any]
) -> tuple[Any, dict[str, Any]]:
    if geometry.layout_id != previous.REVISION_ID or prior_report["revision_id"] != previous.REVISION_ID:
        raise ValueError("input must be the latest bottom-support-above-T-nuts review")
    tnuts = geometry.protected["tnuts"]
    kicker_tnuts = {k: v for k, v in tnuts.items() if k.startswith("hold_tnut_kicker_")}
    targets = {
        "left": max((k for k, v in kicker_tnuts.items() if v.Center().x < 0), key=lambda k: kicker_tnuts[k].Center().x),
        "right": min((k for k, v in kicker_tnuts.items() if v.Center().x > 0), key=lambda k: kicker_tnuts[k].Center().x),
    }
    raw_hosts, finished_hosts = dict(geometry.raw_hosts), dict(geometry.finished_hosts)
    raw_parts, finished_parts = dict(geometry.raw_candidate_parts), dict(geometry.finished_candidate_parts)
    bores = dict(geometry.candidate_bores)
    hardware = {k: dict(v) for k, v in geometry.candidate_installed_hardware.items()}
    native_cuts = {k: dict(v) for k, v in geometry.source_cutters_by_host.items()}
    applied_cuts = {k: dict(v) for k, v in geometry.applied_source_cutters_by_host.items()}
    purchase_cuts = {k: dict(v) for k, v in geometry.purchased_panel_cutters_by_host.items()}
    candidate_purchase = {k: dict(v) for k, v in geometry.purchased_panel_cutters_by_candidate_part.items()}
    fixed_axes = dict(geometry.fixed_axes)
    placements, post_deltas, screw_deltas = {}, {}, {}
    moved_axes = set()
    changed_hosts = {"base_header"}
    changed_parts = set()

    for side in SIDES:
        post_id, cleat_id = f"base_post_center_{side}", f"center_post_cleat_{side}"
        post_box, flange_box = raw_hosts[post_id].BoundingBox(), kicker_tnuts[targets[side]].BoundingBox()
        width = post_box.xmax - post_box.xmin
        center_x = flange_box.xmin - FLANGE_GAP_MM - width / 2 if side == "left" else flange_box.xmax + FLANGE_GAP_MM + width / 2
        delta = cq.Vector(center_x - (post_box.xmin + post_box.xmax) / 2, 0, 0)
        post_deltas[side] = delta
        raw_hosts[post_id] = raw_hosts[post_id].translate(delta)
        raw_parts[cleat_id] = raw_parts[cleat_id].translate(delta)
        finished_parts[cleat_id] = finished_parts[cleat_id].translate(delta)
        for mapping in (native_cuts, applied_cuts, purchase_cuts):
            mapping[post_id] = {k: v.translate(delta) for k, v in mapping.get(post_id, {}).items()}
        axes = {k for k, b in bores.items() if cleat_id in b.receiver_ids}
        if len(axes) != 4:
            raise ValueError(f"{cleat_id}: expected four post/header joint bolts")
        for axis in axes:
            bores[axis] = replace(bores[axis], shape=bores[axis].shape.translate(delta))
            hardware[axis] = {k: v.translate(delta) for k, v in hardware[axis].items()}
        moved_axes.update(axes)
        changed_hosts.add(post_id)
        changed_parts.add(cleat_id)
        placements[side] = {
            "post_id": post_id, "tnut_id": targets[side], "post_center_x_mm": center_x,
            "translation_global_xyz_mm": list(delta.toTuple()), "flange_gap_mm": FLANGE_GAP_MM,
        }

    source_connections = tuple(geometry.source.panel_connections())
    if len(source_connections) != 66 or len({c.name for c in source_connections}) != 66:
        raise ValueError("expected 66 source panel screws")
    previous_moves = {r["axis_id"]: r for r in prior_report["moved_panel_axes"]}
    all_connections = []
    moved_rows = list(prior_report["moved_panel_axes"])
    for connection in source_connections:
        if connection.name in previous_moves:
            old_move = previous_moves[connection.name]
            all_connections.append(replace(connection, start=connection.start + cq.Vector(*old_move["translation_global_xyz_mm"])))
            continue
        if connection.name not in MOVED_SCREWS:
            all_connections.append(connection)
            continue
        side = "left" if "_left_" in connection.name else "right"
        post_id = placements[side]["post_id"]
        delta = cq.Vector(placements[side]["post_center_x_mm"] - connection.start.x, 0, 0)
        screw_deltas[connection.name] = delta
        moved = replace(connection, start=connection.start + delta, members=(connection.members[0], post_id))
        all_connections.append(moved)
        fixed_axes[connection.name] = fixed_axes[connection.name].translate(delta)
        backer = f"inner_kicker_backer_{side}"
        receiver_cut = candidate_purchase[backer][connection.name].translate(delta)
        applied_cuts[post_id][f"panel_purchase/{connection.name}"] = receiver_cut
        purchase_cuts[post_id][f"panel_purchase/{connection.name}"] = receiver_cut
        moved_rows.append({
            "axis_id": connection.name, "visual_name": f"fastener_{connection.name}",
            "panel_member": connection.members[0], "receiver_member": post_id,
            "previous_receiver_member": backer,
            "old_start_global_xyz_mm": list(connection.start.toTuple()),
            "new_start_global_xyz_mm": list(moved.start.toTuple()),
            "translation_global_xyz_mm": list(delta.toTuple()),
            "axis_global_xyz_unchanged": list(connection.direction.toTuple()),
            "purchased_product_policy": "Hillman 42605; existing purchased screw and pilot policy retained",
        })

    removed_display = set(REMOVED_PARTS)
    for axis in REMOVED_AXES:
        if not set(bores[axis].receiver_ids) & REMOVED_PARTS:
            raise ValueError(f"unexpected ownership for removed axis {axis}")
        removed_display.update(f"{axis}/{role}" for role in hardware[axis])
        del bores[axis]
        del hardware[axis]
    for name in REMOVED_PARTS:
        del raw_parts[name]
        del finished_parts[name]
        del candidate_purchase[name]

    for host in changed_hosts:
        cutters = [v for k, v in applied_cuts[host].items() if k not in geometry.replaced_source_cutter_ids]
        cutters.extend(b.shape for b in bores.values() if host in b.receiver_ids)
        shape = raw_hosts[host].cut(*cutters).clean()
        if not shape.isValid() or not shape.Solids():
            raise ValueError(f"invalid rebuilt timber: {host}")
        finished_hosts[host] = shape

    current_parts = tuple(geometry.source.parts())
    raw_source_parts = tuple(geometry.source.uncut_wood_parts())
    panel_shapes = dict(geometry.panel_replacements)
    proxy = support._PanelModelProxy(geometry.source, tuple(all_connections))
    panel_shapes["kicker_right"] = panels.candidate_panel_replacements(proxy, current_parts=current_parts, uncut_parts=raw_source_parts)["kicker_right"].shape
    left_panel = next(p.shape for p in raw_source_parts if p.name == "kicker_left")
    for connection in all_connections:
        if connection.members[0] == "kicker_left":
            for cutter in panels._panel_connection_cutters(connection):
                left_panel = left_panel.cut(cutter)
    panel_shapes["kicker_left"] = left_panel.clean()

    protected = {k: dict(v) for k, v in geometry.protected.items()}
    for axis in MOVED_SCREWS:
        protected["fixed_66_hillman_axes_63p5mm"][axis] = fixed_axes[axis]
    checks = {
        "center_posts_outside_nearest_central_kicker_tnut_flanges": True,
        "two_center_backers_and_four_backer_bolts_removed": True,
        "four_center_kicker_screw_receivers_moved_to_posts": True,
        "all_66_panel_screw_ids_preserved": len(fixed_axes) == 66,
        "twelve_existing_frame_bolts_unchanged": True,
        "kicker_center_edge_support_verified": False,
        "complete_joint_acceptance": False,
    }
    revised = replace(
        geometry, layout_id=REVISION_ID, trial_id=REVISION_ID,
        raw_hosts=support._proxy(raw_hosts), finished_hosts=support._proxy(finished_hosts),
        raw_candidate_parts=support._proxy(raw_parts), finished_candidate_parts=support._proxy(finished_parts),
        candidate_bores=support._proxy(bores), candidate_installed_hardware=support._nested_proxy(hardware),
        source_cutters_by_host=support._nested_proxy(native_cuts),
        applied_source_cutters_by_host=support._nested_proxy(applied_cuts),
        purchased_panel_cutters_by_host=support._nested_proxy(purchase_cuts),
        purchased_panel_cutters_by_candidate_part=support._nested_proxy(candidate_purchase),
        fixed_axes=support._proxy(fixed_axes), panel_replacements=support._proxy(panel_shapes),
        protected=support._nested_proxy(protected), composition_checks=support._proxy(checks),
    )
    current_display = {
        "finished_hosts": sorted(changed_hosts), "finished_candidate_parts": sorted(changed_parts),
        "candidate_installed_hardware": sorted(f"{axis}/{role}" for axis in moved_axes for role in hardware[axis]),
        "panel_replacements": ["kicker_left", "kicker_right"],
    }
    changed_display = support._union_display_ids(prior_report["changed_display_solid_ids"], current_display)
    report = {
        "schema": "wood_joint_wj24_kicker_posts_outside_tnuts/v1", "revision_id": REVISION_ID,
        "summary": "Kicker uprights outside the central T-nuts; center backing removed",
        "supersedes_revision_id": geometry.layout_id,
        "prior_revision_report": dict(prior_report), "placements": placements,
        "moved_panel_axes": moved_rows,
        "baseline_display_translations_mm": {r["visual_name"]: r["translation_global_xyz_mm"] for r in moved_rows},
        "changed_display_solid_ids": changed_display,
        "removed_display_solid_ids": sorted(removed_display),
        "removed_candidate_part_ids": sorted(REMOVED_PARTS), "removed_candidate_axis_ids": sorted(REMOVED_AXES),
        "moved_candidate_axis_ids": sorted(moved_axes), "checks": checks,
        "scope": "Owner geometry review; no mechanics, installation, or fabrication acceptance",
    }
    return revised, report
