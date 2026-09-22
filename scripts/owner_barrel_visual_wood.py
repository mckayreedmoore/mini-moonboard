"""Rebuild the 16 former-angle timbers for a visual-only barrel scene.

The active assembly supplies uncut kerf-right solids. Only source-recorded
non-angle machining is replayed. No candidate barrel bore or structural
resistance is established here; callers may replace the old timber visuals.
"""

from collections import defaultdict
from itertools import combinations

import cadquery as cq

from mini_moonboard.floor_flush_width import (
    KERF_RIGHT,
    KERF_RIGHT_MM,
    TRANSLATE_NAMES,
    variant,
)
from scripts import owner_barrel_outer_header_cut_integrity as outer_header
from scripts.center_posts_outward_owner_layout import build_layout as post_layout
from scripts.export_owner_barrel_scene import build_viewer_assembly
from scripts.simple_owner_duty_ledger import selected_duties

EXPECTED_TIMBERS = frozenset(
    {
        "base_header",
        "base_post_center_left",
        "base_post_center_right",
        "base_post_outer_left",
        "base_post_outer_right",
        "base_principal_center_left",
        "base_principal_center_right",
        "base_rail_bottom_left",
        "base_rail_bottom_right",
        "base_rail_service_lower_left",
        "base_rail_service_lower_right",
        "base_rail_service_upper_left",
        "base_rail_service_upper_right",
        "base_rail_top",
        "base_side_left",
        "base_side_right",
    }
)


def _source_cutter_pose(cutter, member, placement):
    """Follow the width adapter and the two moved center posts."""
    shift = -KERF_RIGHT_MM if member in TRANSLATE_NAMES else 0.0
    if member.startswith("base_post_center_"):
        shift += placement["post_shift_x_mm"][member.removeprefix("base_post_center_")]
    return cutter.translate(cq.Vector(shift, 0, 0)) if shift else cutter


def _same_envelope(first, second):
    a, b = first.BoundingBox(), second.BoundingBox()
    return abs(first.Volume() - second.Volume()) < 1e-4 and all(
        abs(getattr(a, field) - getattr(b, field)) < 1e-5
        for field in ("xmin", "xmax", "ymin", "ymax", "zmin", "zmax")
    )


def _boxes_overlap(first, second):
    a, b = first.BoundingBox(), second.BoundingBox()
    return all(
        min(getattr(a, f"{axis}max"), getattr(b, f"{axis}max"))
        > max(getattr(a, f"{axis}min"), getattr(b, f"{axis}min"))
        for axis in "xyz"
    )


def _cut_intersections(raw, trial, others, *, same_category=False):
    hits = []
    for member, rows in trial.items():
        pairs = (
            combinations(rows, 2)
            if same_category
            else (
                (trial_row, protected_row)
                for trial_row in rows
                for protected_row in others[member]
            )
        )
        for (_, trial_name, first), (_, other_name, second) in pairs:
            if not _boxes_overlap(first, second):
                continue
            volume = first.intersect(second).intersect(raw[member]).Volume()
            if volume > 1e-4:
                hits.append(
                    {
                        "member": member,
                        "trial_path": trial_name,
                        "other_path": other_name,
                        "intersection_mm3": round(volume, 6),
                    }
                )
    return sorted(
        hits, key=lambda row: (row["member"], row["trial_path"], row["other_path"])
    )


def build_visual_wood(*, assembly=None, placement=None):
    """Return detached replacement solids and a closed visual-only inventory."""
    assembly = build_viewer_assembly() if assembly is None else assembly
    placement = post_layout() if placement is None else placement
    source = variant(KERF_RIGHT)
    duties = selected_duties()
    targets = {member for row in duties.values() for member in row["timber"]}
    legacy = {name for row in duties.values() for name in row["sds_axes"]}
    source_raw = {part.name: part.shape for part in source.uncut_wood_parts()}
    fixed_panels = {row.name: row for row in assembly["panel_connections"]}
    fixed_frame = {row.name: row for row in assembly["frame_connections"]}
    pose = assembly["post_placement"]
    receiver_map = dict(placement["panel_receiver_map"])
    if pose == "integrated":
        for row in fixed_panels.values():
            if row.name.startswith("round_kicker_") and "_center_" in row.name:
                receiver_map[row.name] = row.members[1]
    if (
        targets != EXPECTED_TIMBERS
        or len(duties) != 24
        or len(legacy) != 144
        or {row.name for row in assembly["removed_legacy_sds"]} != legacy
        or set(assembly["removed_legacy_stations"]) != set(duties)
        or len(fixed_panels) != 66
        or len(fixed_frame) != 12
        or set(receiver_map) != set(fixed_panels)
        or pose not in ("outward", "integrated")
        or any(assembly["release_flags"].values())
        or not targets <= set(assembly["wood"]) & set(source_raw)
    ):
        raise ValueError("Active barrel visual-wood source changed")
    for name in targets:
        shifted = source_raw[name]
        if name.startswith("base_post_center_") and pose == "outward":
            side = name.removeprefix("base_post_center_")
            shifted = shifted.translate(
                cq.Vector(placement["post_shift_x_mm"][side], 0, 0)
            )
        if name.startswith("base_post_center_") and pose == "integrated":
            post = assembly["wood"][name].BoundingBox()
            seam = source_raw["kicker_left"].BoundingBox().xmax
            side = name.removeprefix("base_post_center_")
            x0 = seam - 88.9 if side == "left" else seam
            shifted = cq.Solid.makeBox(
                88.9,
                139.7,
                source_raw[name].BoundingBox().zlen,
                cq.Vector(x0, source_raw[name].BoundingBox().ymax - 139.7, post.zmin),
            )
        if not _same_envelope(shifted, assembly["wood"][name]):
            raise ValueError(
                f"{name}: active uncut wood differs from kerf-right source"
            )

    cutters = defaultdict(list)

    def add(member, category, name, cutter):
        if name in legacy:
            raise ValueError("Historical SDS cutter entered visual replacement")
        if member in targets:
            cutters[member].append((category, name, cutter))

    service_count = 0
    for member, name, cutter in source.service_cutters():
        if member in targets:
            service_count += 1
            add(
                member,
                "inherited_service",
                name,
                _source_cutter_pose(cutter, member, placement),
            )
    additional_count = 0
    for member, name, _, cutter in source.additional_machining_cutters():
        if member in targets:
            additional_count += 1
            add(
                member,
                "inherited_additional",
                name,
                _source_cutter_pose(cutter, member, placement),
            )

    panel_cuts = 0
    backer_landings = 0
    for row in fixed_panels.values():
        receiver = receiver_map[row.name]
        if receiver in targets:
            # In the selected source the timber is the second member; no
            # screw-head cutter belongs in the timber receiver.
            if receiver != row.members[1]:
                raise ValueError(f"{row.name}: changed timber receiver")
            add(
                receiver,
                "fixed_panel",
                row.name,
                cq.Solid.makeCylinder(
                    row.diameter / 2,
                    row.length + 2,
                    row.start - row.direction,
                    row.direction,
                ),
            )
            panel_cuts += 1
        elif receiver in {"inner_kicker_backer_left", "inner_kicker_backer_right"}:
            if receiver not in assembly["wood"]:
                raise ValueError(f"{row.name}: missing current backer")
            backer_landings += 1
        else:
            raise ValueError(f"{row.name}: unrepresented fixed screw receiver")

    frame_cuts = 0
    for row in fixed_frame.values():
        if row.kind != "bolt" or len(row.members) != 2:
            raise ValueError(f"{row.name}: retained frame bolt changed")
        diameter = source.bolt_dimensions(row)["hole_diameter_mm"]
        cutter = cq.Solid.makeCylinder(
            diameter / 2,
            row.length + 2,
            row.start - row.direction,
            row.direction,
        )
        for member in row.members:
            if member in targets:
                add(member, "retained_frame", row.name, cutter)
                frame_cuts += 1

    expected_panel_cuts = 66 if pose == "integrated" else 62
    expected_backer_landings = 0 if pose == "integrated" else 4
    if (service_count, additional_count, panel_cuts, backer_landings, frame_cuts) != (
        32,
        0,
        expected_panel_cuts,
        expected_backer_landings,
        8,
    ):
        raise ValueError("Current inherited cut inventory changed")
    protected = {name: tuple(cutters[name]) for name in targets}
    trial = defaultdict(list)
    for prefix, row in outer_header._rows(assembly).items():
        side = row["side"]
        for member, roles in (
            ("base_header", ("counterbore", "machine_bore")),
            (f"base_post_outer_{side}", ("barrel_bore", "machine_bore")),
        ):
            for role in roles:
                name = f"{prefix}/{role}"
                cutter = row["paths"][role]
                if cutter.intersect(assembly["wood"][member]).Volume() <= 1.0:
                    raise ValueError(f"{name}: outer-header trial misses {member}")
                add(member, "outer_header_trial", name, cutter)
                trial[member].append(("outer_header_trial", name, cutter))
    if sum(map(len, trial.values())) != 16 or len(trial["base_header"]) != 8:
        raise ValueError("Outer-header trial bore inventory changed")
    protected_intersections = _cut_intersections(assembly["wood"], trial, protected)
    trial_intersections = _cut_intersections(
        assembly["wood"], trial, trial, same_category=True
    )
    visual = {}
    for name in sorted(targets):
        raw = assembly["wood"][name]
        tools = [cutter for _, _, cutter in cutters[name]]
        shape = raw.cut(*tools).clean() if tools else raw
        if (
            not shape.isValid()
            or len(shape.Solids()) != 1
            or shape.Volume() > raw.Volume() + 1e-4
        ):
            raise ValueError(f"{name}: invalid visual-only replacement solid")
        visual[name] = shape
    per_member = {}
    for name in sorted(targets):
        names = {
            category: sorted(
                row_name for kind, row_name, _ in cutters[name] if kind == category
            )
            for category in (
                "inherited_service",
                "inherited_additional",
                "fixed_panel",
                "retained_frame",
                "outer_header_trial",
            )
        }
        per_member[name] = {
            "counts": {category: len(rows) for category, rows in names.items()}
            | {"total": sum(map(len, names.values()))},
            "cutter_names": names,
        }
    landing_note = (
        "integrated center posts. "
        if pose == "integrated"
        else "separate backers, outside these 16 replacements. "
    )
    return {
        "wood": visual,
        "report": {
            "status": "VISUAL_ONLY_UNRELEASED",
            "former_angle_stations": len(duties),
            "replacement_timber_members": len(visual),
            "excluded_legacy_sds_axes": len(legacy),
            "fixed_panel_kicker_axes": len(fixed_panels),
            "fixed_panel_receiver_cuts_in_replacements": panel_cuts,
            "fixed_panel_axes_landing_on_separate_backers": backer_landings,
            "retained_frame_bolt_axes": len(fixed_frame),
            "retained_frame_bolt_cuts_in_replacements": frame_cuts,
            "inherited_service_cuts_in_replacements": service_count,
            "inherited_additional_cuts_in_replacements": additional_count,
            "outer_header_trial_cuts": 16,
            "candidate_barrel_body_cuts": 4,
            "per_member": per_member,
            "trial_to_protected_cut_intersections": protected_intersections,
            "trial_to_trial_intersections": trial_intersections,
            "release": False,
            "limits": (
                "Detached visual wood only. The four center kicker screw landings are on "
                + landing_note
                + "Only the 16 source-defined "
                "outer-header trial paths are shown; other candidate barrel, machine-bolt, "
                "washer-seat and counterbore cuts are omitted. Delivered hardware, "
                "clearance, wood strength, load path, drilling and fabrication remain open."
            ),
        },
    }
