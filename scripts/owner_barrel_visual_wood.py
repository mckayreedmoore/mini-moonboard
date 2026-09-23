"""Rebuild former-angle timbers with source and optional candidate trial cuts.

This is visual geometry, not a drilling plan or wood-resistance assessment.
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
from scripts.owner_barrel_candidate_service import (
    F1_G1_DIAMETER_MM,
    candidate_service_cutters,
)
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
RETAINED_ONLY_TIMBERS = frozenset(
    {
        "base_floor_left",
        "base_floor_right",
        "lumber_leg_left",
        "lumber_leg_right",
    }
)
ALL_FRAME_TIMBERS = EXPECTED_TIMBERS | RETAINED_ONLY_TIMBERS


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
            common = first.intersect(second)
            if common.Volume() <= 1e-4:
                continue
            volume = common.intersect(raw[member]).Volume()
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


def build_visual_wood(
    *,
    assembly=None,
    placement=None,
    candidate_service=False,
    candidate_center_cuts=False,
    candidate_all_cuts=False,
    complete_frame_hosts=False,
):
    """Return cut-derived visual solids and an unreleased cutter inventory."""
    assembly = build_viewer_assembly() if assembly is None else assembly
    placement = post_layout() if placement is None else placement
    source = variant(KERF_RIGHT)
    duties = selected_duties()
    replacement_targets = {
        member for row in duties.values() for member in row["timber"]
    }
    targets = (
        set(ALL_FRAME_TIMBERS)
        if complete_frame_hosts
        else replacement_targets
    )
    legacy = {name for row in duties.values() for name in row["sds_axes"]}
    source_raw = {part.name: part.shape for part in source.uncut_wood_parts()}
    fixed_panels = {row.name: row for row in assembly["panel_connections"]}
    fixed_frame = {row.name: row for row in assembly["frame_connections"]}
    pose = assembly["post_placement"]
    if candidate_center_cuts and (pose != "integrated" or not candidate_service):
        raise ValueError("Center candidate cuts require integrated posts and service")
    if candidate_all_cuts and not candidate_center_cuts:
        raise ValueError("Whole-barrel cuts require the integrated center cuts")
    receiver_map = dict(placement["panel_receiver_map"])
    if pose == "integrated":
        for row in fixed_panels.values():
            if row.name.startswith("round_kicker_") and "_center_" in row.name:
                receiver_map[row.name] = row.members[1]
    if (
        replacement_targets != EXPECTED_TIMBERS
        or targets
        != (set(ALL_FRAME_TIMBERS) if complete_frame_hosts else set(EXPECTED_TIMBERS))
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
    service_rows = (
        candidate_service_cutters(source, assembly["wood"])
        if candidate_service
        else source.service_cutters()
    )
    for member, name, cutter in service_rows:
        if member in targets:
            service_count += 1
            add(
                member,
                "inherited_service",
                name,
                cutter
                if candidate_service
                else _source_cutter_pose(cutter, member, placement),
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
        2 if complete_frame_hosts else 0,
        expected_panel_cuts,
        expected_backer_landings,
        24 if complete_frame_hosts else 8,
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
    center_trial = defaultdict(list)
    if candidate_center_cuts:
        for path_name, cutter in assembly["drilling_paths"].items():
            if not path_name.startswith("barrel_center_clip_split_"):
                continue
            barrel_name, role = path_name.rsplit("/", 1)
            station = assembly["barrel_station"].get(barrel_name)
            if station is None:
                raise ValueError(f"{path_name}: center barrel has no station")
            side = station.rsplit("_", 1)[1]
            receiver = (
                f"base_post_center_{side}"
                if "header_center" in station
                else f"base_principal_center_{side}"
            )
            if role == "bolt_bore":
                hosts = ("base_header", receiver)
            elif role == "barrel_cross_bore":
                hosts = (receiver,)
            elif role == "head_pocket" and "base_center" in station:
                hosts = ("base_header",)
            else:
                raise ValueError(f"{path_name}: unexpected center drilling role")
            for member in hosts:
                if cutter.intersect(assembly["wood"][member]).Volume() <= 1.0:
                    raise ValueError(f"{path_name}: center path misses {member}")
                add(member, "center_barrel_trial", path_name, cutter)
                center_trial[member].append(("center_barrel_trial", path_name, cutter))
        if sum(map(len, center_trial.values())) != 20:
            raise ValueError("Integrated center drilling-cut inventory changed")
    represented_paths = defaultdict(set)
    for member, rows in (*trial.items(), *center_trial.items()):
        for _, path_name, _ in rows:
            represented_paths[path_name].add(member)
    remaining_trial = defaultdict(list)
    path_host_anomalies = []
    if candidate_all_cuts:
        if len(assembly["barrels"]) != 46 or len(assembly["drilling_paths"]) != 98:
            raise ValueError("Integrated barrel drilling inventory changed")
        for path_name, cutter in assembly["drilling_paths"].items():
            if path_name in represented_paths:
                continue
            barrel_name, role = path_name.rsplit("/", 1)
            if barrel_name not in assembly["barrels"] or role not in (
                "machine_bore",
                "barrel_bore",
                "bolt_bore",
                "barrel_cross_bore",
            ):
                raise ValueError(f"{path_name}: unexpected remaining drill path")
            hit_members = [
                member
                for member in sorted(targets)
                if _boxes_overlap(cutter, assembly["wood"][member])
                and cutter.intersect(assembly["wood"][member]).Volume() > 1.0
            ]
            if not hit_members:
                raise ValueError(f"{path_name}: drill path misses replacement wood")
            for member in hit_members:
                add(member, "remaining_barrel_trial", path_name, cutter)
                remaining_trial[member].append(
                    ("remaining_barrel_trial", path_name, cutter)
                )
                represented_paths[path_name].add(member)
        missing_paths = sorted(set(assembly["drilling_paths"]) - set(represented_paths))
        if missing_paths:
            raise ValueError(
                f"Barrel drill paths omitted from visual wood: {missing_paths}"
            )
        for path_name in sorted(assembly["drilling_paths"]):
            barrel_name, role = path_name.rsplit("/", 1)
            bolt_name = f"{barrel_name}_bolt"
            hosts = set(assembly["bolts"][bolt_name].members)
            body = assembly["barrels"][barrel_name]
            receivers = {
                member
                for member in hosts
                if abs(
                    body.intersect(assembly["wood"][member]).Volume() - body.Volume()
                )
                < 1e-3
            }
            if len(hosts) != 2 or len(receivers) != 1:
                raise ValueError(f"{barrel_name}: receiving wood is ambiguous")
            expected = (
                hosts
                if role in ("machine_bore", "bolt_bore")
                else receivers
                if role in ("barrel_bore", "barrel_cross_bore")
                else hosts - receivers
                if role in ("counterbore", "head_pocket")
                else set()
            )
            actual = represented_paths[path_name]
            if expected != actual:
                path_host_anomalies.append(
                    {
                        "path": path_name,
                        "role": role,
                        "expected_members": sorted(expected),
                        "cut_members": sorted(actual),
                    }
                )
    protected_intersections = _cut_intersections(assembly["wood"], trial, protected)
    trial_intersections = _cut_intersections(
        assembly["wood"], trial, trial, same_category=True
    )
    center_protected_intersections = _cut_intersections(
        assembly["wood"], center_trial, protected
    )
    center_outer_intersections = _cut_intersections(
        assembly["wood"], center_trial, trial
    )
    remaining_protected_intersections = _cut_intersections(
        assembly["wood"], remaining_trial, protected
    )
    remaining_center_intersections = _cut_intersections(
        assembly["wood"], remaining_trial, center_trial
    )
    remaining_outer_intersections = _cut_intersections(
        assembly["wood"], remaining_trial, trial
    )
    remaining_pair_intersections = _cut_intersections(
        assembly["wood"], remaining_trial, remaining_trial, same_category=True
    )
    unrelated_remaining_pair_intersections = [
        row
        for row in remaining_pair_intersections
        if row["trial_path"].rsplit("/", 1)[0] != row["other_path"].rsplit("/", 1)[0]
    ]
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
        for category, cutter_name, cutter in cutters[name]:
            if cutter.intersect(raw).Volume() <= 1e-4:
                raise ValueError(
                    f"{name}/{category}/{cutter_name}: cutter misses raw host"
                )
            if cutter.intersect(shape).Volume() > 1e-3:
                raise ValueError(
                    f"{name}/{category}/{cutter_name}: cutter remains in cut solid"
                )
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
                "center_barrel_trial",
                "remaining_barrel_trial",
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
        # Keep the exact cutter solids available to source-bound diagnostic
        # consumers.  These are nominal CAD envelopes, not shop instructions.
        "cutters": {
            name: tuple(cutters[name]) for name in sorted(targets)
        },
        "report": {
            "status": "VISUAL_ONLY_UNRELEASED",
            "candidate_service_diameter_mm": (
                F1_G1_DIAMETER_MM if candidate_service else None
            ),
            "former_angle_stations": len(duties),
            "replacement_timber_members": len(visual),
            "complete_frame_hosts_requested": complete_frame_hosts,
            "all_twenty_frame_timber_hosts_represented": (
                complete_frame_hosts and set(visual) == set(ALL_FRAME_TIMBERS)
            ),
            "excluded_legacy_sds_axes": len(legacy),
            "fixed_panel_kicker_axes": len(fixed_panels),
            "fixed_panel_receiver_cuts_in_replacements": panel_cuts,
            "fixed_panel_axes_landing_on_separate_backers": backer_landings,
            "retained_frame_bolt_axes": len(fixed_frame),
            "retained_frame_bolt_cuts_in_replacements": frame_cuts,
            "inherited_service_cuts_in_replacements": service_count,
            "inherited_additional_cuts_in_replacements": additional_count,
            "total_host_cutter_records": sum(map(len, cutters.values())),
            "all_host_cutters_intersect_raw_wood": True,
            "all_host_cutters_removed_from_cut_solids": True,
            "outer_header_trial_cuts": 16,
            "center_trial_cuts": sum(map(len, center_trial.values())),
            "remaining_trial_cuts": sum(map(len, remaining_trial.values())),
            "candidate_barrel_pairs_with_cut_wood": sum(
                all(
                    path in represented_paths
                    for path in assembly["drilling_paths"]
                    if path.startswith(name + "/")
                )
                for name in assembly["barrels"]
                if any(
                    path.startswith(name + "/") for path in assembly["drilling_paths"]
                )
            ),
            "barrel_drilling_paths_without_cut_wood": sorted(
                set(assembly["drilling_paths"]) - set(represented_paths)
            ),
            "barrel_path_hosts": {
                name: sorted(hosts) for name, hosts in sorted(represented_paths.items())
            },
            "barrel_path_host_anomalies": path_host_anomalies,
            "outer_header_barrel_body_cuts": sum(
                row_name.endswith("/barrel_bore")
                for rows in trial.values()
                for _, row_name, _ in rows
            ),
            "center_barrel_body_cuts": sum(
                row_name.endswith("/barrel_cross_bore")
                for rows in center_trial.values()
                for _, row_name, _ in rows
            ),
            "per_member": per_member,
            "trial_to_protected_cut_intersections": protected_intersections,
            "trial_to_trial_intersections": trial_intersections,
            "center_to_protected_cut_intersections": center_protected_intersections,
            "center_to_outer_header_cut_intersections": center_outer_intersections,
            "remaining_to_protected_cut_intersections": remaining_protected_intersections,
            "remaining_to_center_cut_intersections": remaining_center_intersections,
            "remaining_to_outer_header_cut_intersections": remaining_outer_intersections,
            "remaining_pair_cut_intersections": remaining_pair_intersections,
            "unrelated_remaining_pair_cut_intersections": unrelated_remaining_pair_intersections,
            "release": False,
            "limits": (
                "Visual timber only. The four center kicker screw landings are on "
                + landing_note
                + ("Center trial paths are also cut. " if candidate_center_cuts else "")
                + (
                    "All 46 candidate barrel pairs have visual trial cuts. "
                    if candidate_all_cuts
                    else "Only the outer-header and selected center trial paths are shown; remaining candidate cuts are omitted. "
                )
                + "Delivered hardware, "
                "clearance, wood strength, load path, drilling and fabrication remain open."
            ),
        },
    }
