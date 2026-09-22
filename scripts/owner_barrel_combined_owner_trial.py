"""Read-only full-assembly screen of two unapproved owner decisions.

This composes the maintained 46-pair scene, then moves only two first
left-center rail rows to N=42 mm and extends only four top-outer machine
bores by 2 mm. It does not change the maintained producer or viewer.
"""

import json
from dataclasses import replace

import cadquery as cq

from scripts import owner_barrel_coordinates as coordinates
from scripts import owner_layout_protected as protected
from scripts.export_owner_barrel_scene import build_integrated_viewer_assembly
from scripts.owner_barrel_installed_stack_audit import (
    _axial_caps,
    _cylinder,
)
from scripts.owner_barrel_installed_stack_audit import (
    build_report as stack_report,
)
from scripts.owner_barrel_visual_wood import build_visual_wood

LEFT_STATIONS = frozenset(
    {
        "clip_horizontal_lower_left_2",
        "clip_horizontal_upper_left_2",
    }
)
TOP_STATIONS = frozenset({"clip_single_top_left_1", "clip_single_top_right_2"})
FRONT_ROW_SHIFT_MM = -18.0
TOP_BORE_EXTENSION_MM = 2.0


def _copy_assembly(source):
    result = dict(source)
    for key in ("bolts", "barrels", "stacks", "drilling_paths", "access_paths"):
        result[key] = dict(source[key])
    result["stacks"] = {name: dict(roles) for name, roles in source["stacks"].items()}
    result["replacement_solids"] = dict(source["replacement_solids"])
    result["diagnostic_bolt_axes"] = result["bolts"]
    result["barrel_solids"] = result["barrels"]
    # The maintained producer's collision diagnostics do not cover this trial.
    result["diagnostics"] = {"status": "UNAPPROVED_COMBINED_TRIAL_RESCREEN_REQUIRED"}
    return result


def _move_first_rows(source, trial):
    delta = cq.Vector(
        0,
        coordinates.N[0] * FRONT_ROW_SHIFT_MM,
        coordinates.N[1] * FRONT_ROW_SHIFT_MM,
    )
    changed = []
    for station in sorted(LEFT_STATIONS):
        bolts = sorted(
            name for name, owner in source["bolt_station"].items() if owner == station
        )
        if len(bolts) != 2 or not bolts[0].endswith("_1_bolt"):
            raise ValueError(f"{station}: first-row identity changed")
        name = bolts[0]
        barrel = name.removesuffix("_bolt")
        trial["bolts"][name] = replace(
            source["bolts"][name], start=source["bolts"][name].start + delta
        )
        trial["barrels"][barrel] = source["barrels"][barrel].translate(delta)
        trial["stacks"][name] = {
            role: shape.translate(delta)
            for role, shape in source["stacks"][name].items()
        }
        for key in ("drilling_paths", "access_paths"):
            for path, shape in source[key].items():
                if path.startswith(barrel + "/"):
                    trial[key][path] = shape.translate(delta)
        changed.append(name)
    return changed


def _extend_top_bores(source, trial):
    changed = []
    extensions = {}
    for station in sorted(TOP_STATIONS):
        bolts = sorted(
            name for name, owner in source["bolt_station"].items() if owner == station
        )
        if len(bolts) != 2:
            raise ValueError(f"{station}: top-outer rows changed")
        for name in bolts:
            barrel = name.removesuffix("_bolt")
            path = f"{barrel}/machine_bore"
            bore = source["drilling_paths"][path]
            bolt = source["bolts"][name]
            axis = bolt.direction.normalized()
            _, length, diameter, vertices = _cylinder(bore, path)
            near, far = _axial_caps(vertices, bolt.start, axis)
            start = bolt.start + axis * near
            enlarged = cq.Solid.makeCylinder(
                diameter / 2, length + TOP_BORE_EXTENSION_MM, start, axis
            )
            if abs(far - near - length) > 1e-4:
                raise ValueError(f"{path}: machine bore cap changed")
            trial["drilling_paths"][path] = enlarged
            extensions[path] = enlarged.cut(bore)
            changed.append(path)
    return changed, extensions


def _refresh_replacements(trial, stations):
    for station in stations:
        barrels = (
            shape
            for name, shape in trial["barrels"].items()
            if trial["barrel_station"][name] == station
        )
        stacks = (
            shape
            for name, roles in trial["stacks"].items()
            if trial["bolt_station"][name] == station
            for shape in roles.values()
        )
        trial["replacement_solids"][station] = (*barrels, *stacks)


def build_trial(source=None):
    """Return a detached trial assembly and the four incremental bore tips."""
    source = build_integrated_viewer_assembly() if source is None else source
    if (
        source["post_placement"] != "integrated"
        or len(source["bolts"]) != 46
        or len(source["panel_connections"]) != 66
        or len(source["frame_connections"]) != 12
        or any(source["release_flags"].values())
    ):
        raise ValueError("Maintained integrated assembly identity changed")
    trial = _copy_assembly(source)
    moved = _move_first_rows(source, trial)
    extended, tips = _extend_top_bores(source, trial)
    _refresh_replacements(trial, LEFT_STATIONS)
    return source, trial, moved, extended, tips


def report(source=None):
    """Check whole trial-cut inventory, source invariants and changed margins."""
    source, trial, moved, extended, tips = build_trial(source)
    visual = build_visual_wood(
        assembly=trial,
        candidate_service=True,
        candidate_center_cuts=True,
        candidate_all_cuts=True,
    )["report"]
    axial = stack_report(trial)
    fixed = protected.inventory()
    tip_hits = {
        path: {
            key: value
            for key, value in protected.hits({path: tip}, fixed)[path].items()
        }
        for path, tip in tips.items()
    }
    moved_barrels = [name.removesuffix("_bolt") for name in moved]
    moved_paths = {
        path
        for path in trial["drilling_paths"]
        if path.rsplit("/", 1)[0] in moved_barrels
    }
    if len(moved_paths) != 4 or len(extended) != 4:
        raise ValueError("Expected four moved and four extended drill paths")
    changed_paths = moved_paths | set(extended)
    changed_cut_intersections = {
        key: [
            row
            for row in visual[key]
            if row["trial_path"] in changed_paths or row["other_path"] in changed_paths
        ]
        for key in (
            "remaining_to_protected_cut_intersections",
            "remaining_to_center_cut_intersections",
            "remaining_to_outer_header_cut_intersections",
            "unrelated_remaining_pair_cut_intersections",
        )
    }
    tip_receiver_coverage = {
        path: round(
            tip.intersect(trial["wood"]["base_rail_top"]).Volume() / tip.Volume(),
            6,
        )
        for path, tip in tips.items()
    }
    tip_other_wood_hits = {
        path: {
            name: round(volume, 6)
            for name, wood in trial["wood"].items()
            if name != "base_rail_top"
            and (volume := protected._volume(tip, wood)) > 1.0
        }
        for path, tip in tips.items()
    }
    unchanged = (
        source["wood"] == trial["wood"]
        and source["panel_connections"] == trial["panel_connections"]
        and source["frame_connections"] == trial["frame_connections"]
        and source["release_flags"] == trial["release_flags"]
    )
    return {
        "schema": "owner_barrel_combined_owner_trial/v1",
        "maintained_scene_changed": False,
        "source_wood_panel_frame_release_unchanged": unchanged,
        "moved_first_row_bolts": moved,
        "moved_first_row_drilling_paths": sorted(moved_paths),
        "changed_drilling_paths_checked": sorted(changed_paths),
        "first_row_trial_n_mm": 42.0,
        "extended_top_machine_bores": extended,
        "extension_mm": TOP_BORE_EXTENSION_MM,
        "whole_cut_path_host_anomalies": visual["barrel_path_host_anomalies"],
        "whole_cut_missing_paths": visual["barrel_drilling_paths_without_cut_wood"],
        "whole_cut_barrel_pairs": visual["candidate_barrel_pairs_with_cut_wood"],
        "changed_cut_intersections": changed_cut_intersections,
        "incremental_top_tip_protected_hits": tip_hits,
        "incremental_top_tip_receiver_coverage": tip_receiver_coverage,
        "incremental_top_tip_other_wood_hits": tip_other_wood_hits,
        "top_tip_clearance_mm": {
            row["bolt_name"]: row["tip_to_bore_far_cap_clearance_mm"]
            for row in axial["rows"]
            if row["station"] in TOP_STATIONS
        },
        "structural_released": False,
        "drilling_released": False,
        "fabrication_released": False,
        "owner_approval_pending": True,
        "limits": (
            "Read-only nominal assembly trial. Protected hits use >1 mm3 overlap; "
            "no measured hardware, local net-section, actual thread, signed loads, "
            "tolerances or fabrication acceptance is established."
        ),
    }


if __name__ == "__main__":
    print(json.dumps(report(), indent=2))
