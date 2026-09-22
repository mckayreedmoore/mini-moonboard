"""Detached sampled rim withdrawal against either barrel composition.

Nominal positive-volume intersections are evidence of interference, while an
empty sampled result cannot qualify a continuous or real service operation.
"""

import json
import math
from itertools import pairwise

import cadquery as cq

from mini_moonboard.floor_flush_width import KERF_RIGHT, variant
from scripts import export_owner_barrel_scene as viewer
from scripts import owner_barrel_coordinates as coordinates
from scripts import owner_barrel_outer_header_sequence_probe as sequence
from scripts import owner_layout_protected as protected
from scripts import simple_owner_duty_ledger as ledger

SCHEMA = "owner_barrel_rim_withdrawal_hardware_probe/v1"
SOURCE_FORWARD_Y_MM = -85.0
HIT_TOL_MM3 = 1.0
SAMPLES_MM = tuple(range(0, 161, 5))
CATEGORIES = (
    "other_uncut_wood",
    "retained_barrels",
    "retained_bolt_stacks",
    "protected_envelopes",
)


def _axis_signature(row):
    return (
        row.name,
        row.start.toTuple(),
        row.direction.toTuple(),
        row.length,
        row.diameter,
        tuple(row.members),
    )


def _validate_current_viewer(assembly):
    source = variant(KERF_RIGHT)
    expected_panel = tuple(source.panel_connections())
    expected_frame = tuple(row for row in source.connections() if row.kind == "bolt")
    for key, expected, count in (
        ("panel_connections", expected_panel, 66),
        ("frame_connections", expected_frame, 12),
    ):
        actual = tuple(assembly[key])
        if len(actual) != count or tuple(map(_axis_signature, actual)) != tuple(
            map(_axis_signature, expected)
        ):
            raise ValueError(f"Fixed source axes changed: {key}")
    if any(assembly["release_flags"].values()):
        raise ValueError("Current viewer unexpectedly carries release approval")
    forward = assembly["diagnostics"]["producer_diagnostics"]["outer_top8"][
        "viewer_trial_outer_header_forward_y_mm"
    ]
    if abs(forward - SOURCE_FORWARD_Y_MM) > 1e-6:
        raise ValueError("Viewer outer-header forward row changed")
    for side in sequence.SIDES:
        station = f"clip_timber_header_outer_{side}"
        for index, y in ((1, -135.0), (2, SOURCE_FORWARD_Y_MM)):
            prefix = f"barrel_trial_{station}_{index}"
            bolt = f"{prefix}_bolt"
            if (
                assembly["barrel_station"].get(prefix) != station
                or assembly["bolt_station"].get(bolt) != station
                or abs(assembly["bolts"][bolt].start.y - y) > 1e-6
                or set(assembly["stacks"][bolt]) != {"shaft", "washer", "head"}
            ):
                raise ValueError(f"Viewer outer-header row changed: {prefix}")


def _bounds_overlap(a, b):
    return all(
        min(getattr(a, f"{axis}max"), getattr(b, f"{axis}max"))
        > max(getattr(a, f"{axis}min"), getattr(b, f"{axis}min"))
        for axis in "xyz"
    )


def _swept_aabb_certificate(rim, direction, path_end_mm, targets):
    """Conservatively enclose every translated rim pose on one straight path."""
    if (
        tuple(targets) != CATEGORIES
        or not math.isfinite(path_end_mm)
        or path_end_mm <= 0
        or not math.isclose(direction.Length, 1.0, abs_tol=1e-9)
    ):
        raise ValueError("Require current targets and a finite unit-direction path")
    start = rim.BoundingBox()
    end = rim.translate(direction * path_end_mm).BoundingBox()
    swept = {
        axis: (
            min(getattr(start, f"{axis}min"), getattr(end, f"{axis}min")),
            max(getattr(start, f"{axis}max"), getattr(end, f"{axis}max")),
        )
        for axis in "xyz"
    }
    uncertified = {}
    minimum_gaps = {}
    for family, rows in targets.items():
        uncertified[family] = []
        certified_gaps = []
        for name, shape in rows.items():
            box = shape.BoundingBox()
            # A strictly positive gap on any one world axis proves the
            # target misses the entire swept rim, not just sampled poses.
            gap = max(
                max(
                    swept[axis][0] - getattr(box, f"{axis}max"),
                    getattr(box, f"{axis}min") - swept[axis][1],
                )
                for axis in "xyz"
            )
            if gap <= 1e-6:
                uncertified[family].append(name)
            else:
                certified_gaps.append(gap)
        minimum_gaps[family] = round(min(certified_gaps), 6) if certified_gaps else None
    hardware_families = CATEGORIES[1:]
    return {
        "path_end_mm": path_end_mm,
        "direction_xyz": list(direction.toTuple()),
        "target_counts": {family: len(rows) for family, rows in targets.items()},
        "uncertified_targets": uncertified,
        "minimum_certified_axis_gap_mm": minimum_gaps,
        "retained_hardware_and_protected_clear": all(
            not uncertified[family] for family in hardware_families
        ),
        "other_wood_clear": not uncertified["other_uncut_wood"],
        "scope": "Nominal straight-line CAD bounding-box exclusion only",
    }


def _sample_withdrawal(rim, samples_mm, targets):
    """Test isolated rim poses; no interpolation or swept volume is implied."""
    if tuple(targets) != CATEGORIES:
        raise ValueError("Withdrawal target categories changed")
    if (
        not samples_mm
        or samples_mm[0] != 0
        or any(not math.isfinite(value) for value in samples_mm)
        or any(next_value <= value for value, next_value in pairwise(samples_mm))
    ):
        raise ValueError("Withdrawal samples must start at zero and increase")
    target_boxes = {
        family: {name: shape.BoundingBox() for name, shape in rows.items()}
        for family, rows in targets.items()
    }
    direction = cq.Vector(0, *coordinates.N)
    swept = _swept_aabb_certificate(rim, direction, samples_mm[-1], targets)
    n0, n1 = coordinates.local_bounds(rim)["n"]
    rows = []
    for distance in samples_mm:
        moving = rim.translate(direction * distance)
        moving_box = moving.BoundingBox()
        hits = {}
        for family in CATEGORIES:
            hits[family] = {}
            for name, target in targets[family].items():
                if not _bounds_overlap(moving_box, target_boxes[family][name]):
                    continue
                volume = moving.intersect(target).Volume()
                if volume > HIT_TOL_MM3:
                    hits[family][name] = round(volume, 6)
        rows.append({"withdrawal_mm": distance, "positive_volume_hits_mm3": hits})
    return {
        "direction_xyz": [0.0, *coordinates.N],
        "rim_normal_depth_mm": round(n1 - n0, 6),
        "last_sample_exceeds_rim_normal_depth": samples_mm[-1] > n1 - n0,
        "positive_volume_threshold_mm3": HIT_TOL_MM3,
        "continuous_swept_aabb": swept,
        "samples": rows,
        "sampled_clear": not any(
            hits for row in rows for hits in row["positive_volume_hits_mm3"].values()
        ),
        "continuous_sweep_verified": False,
        "real_hardware_and_service_verified": False,
    }


def _side_inventory(assembly, fixed, side, release):
    removed_stations = set(release["candidate_barrel_stations"])
    if len(removed_stations) != 5 or any(
        assembly["station_modes"].get(name) != "direct" for name in removed_stations
    ):
        raise ValueError(f"Rim station inventory changed on {side}")
    if set(assembly["barrel_station"]) != set(assembly["barrels"]) or set(
        assembly["bolt_station"]
    ) != set(assembly["stacks"]):
        raise ValueError("Viewer physical inventory changed")
    removed_barrels = sorted(
        name
        for name, station in assembly["barrel_station"].items()
        if station in removed_stations
    )
    removed_stacks = sorted(
        name
        for name, station in assembly["bolt_station"].items()
        if station in removed_stations
    )
    if len(removed_barrels) != 10 or len(removed_stacks) != 10:
        raise ValueError(f"Rim-attached hardware inventory changed on {side}")
    for station in removed_stations:
        if (
            sum(owner == station for owner in assembly["barrel_station"].values()) != 2
            or sum(owner == station for owner in assembly["bolt_station"].values()) != 2
        ):
            raise ValueError(f"Rim station row count changed: {station}")
    expected_stations = {
        station for _, left, right in ledger.PAIRS for station in (left, right)
    }
    if set(assembly["station_modes"]) != expected_stations:
        raise ValueError("Viewer station inventory changed")
    for name, roles in assembly["stacks"].items():
        if set(roles) != {"shaft", "washer", "head"}:
            raise ValueError(f"Viewer bolt stack changed: {name}")
    retained_barrels = {
        f"barrel/{name}": shape
        for name, shape in assembly["barrels"].items()
        if name not in removed_barrels
    }
    retained_stacks = {
        f"bolt/{name}/{role}": shape
        for name, roles in assembly["stacks"].items()
        if name not in removed_stacks
        for role, shape in roles.items()
    }
    removed_panel = set(release["fixed_panel_screws"])
    removed_frame = set(release["fixed_frame_bolts"])
    if (
        len(removed_panel) != 8
        or len(removed_frame) != 2
        or removed_panel - set(fixed["solids"]["panel_screws"])
        or removed_frame - set(fixed["solids"]["frame_bolts"])
    ):
        raise ValueError(f"Fixed rim attachment inventory changed on {side}")
    protected_targets = {
        f"{family}/{name}": shape
        for family, rows in fixed["solids"].items()
        for name, shape in rows.items()
        if not (
            (family == "panel_screws" and name in removed_panel)
            or (family == "frame_bolts" and name in removed_frame)
        )
    }
    header = f"clip_timber_header_outer_{side}"
    header_rows = sum(owner == header for owner in assembly["barrel_station"].values())
    header_stacks = sorted(
        name for name, owner in assembly["bolt_station"].items() if owner == header
    )
    if (
        header in removed_stations
        or header_rows != 2
        or len(header_stacks) != 2
        or any(name in removed_stacks for name in header_stacks)
        or any(
            any(
                f"bolt/{name}/{role}" not in retained_stacks
                for role in ("shaft", "washer", "head")
            )
            for name in header_stacks
        )
        or any(
            f"barrel/{name}" not in retained_barrels
            for name, owner in assembly["barrel_station"].items()
            if owner == header
        )
    ):
        raise ValueError(f"Outer-header hardware was not retained on {side}")
    return (
        {
            "rim_attached_stations": sorted(removed_stations),
            "station_barrels": removed_barrels,
            "station_bolt_stacks": removed_stacks,
            "fixed_panel_screws": sorted(removed_panel),
            "fixed_frame_bolts": sorted(removed_frame),
            "classification": "temporary_fastener_removal_only",
        },
        {
            "retained_barrels": retained_barrels,
            "retained_bolt_stacks": retained_stacks,
            "protected_envelopes": protected_targets,
        },
        header_stacks,
    )


def probe(*, assembly=None):
    """Screen a supplied viewer composition after temporary rim-fastener removal."""
    assembly = viewer.build_viewer_assembly() if assembly is None else assembly
    _validate_current_viewer(assembly)
    graph = sequence.probe()
    fixed = protected.inventory()
    if set(fixed["solids"]["panel_screws"]) != {
        row.name for row in assembly["panel_connections"]
    } or set(fixed["solids"]["frame_bolts"]) != {
        row.name for row in assembly["frame_connections"]
    }:
        raise ValueError("Protected fixed axes changed")
    wood = assembly["wood"]
    sides = {}
    for side in sequence.SIDES:
        rim_name = f"base_side_{side}"
        if rim_name not in wood:
            raise ValueError(f"Missing viewer rim: {rim_name}")
        release = graph["sides"][side]["release_before_rim_withdrawal"]
        removed, retained, header_stacks = _side_inventory(
            assembly, fixed, side, release
        )
        targets = {
            "other_uncut_wood": {
                name: shape for name, shape in wood.items() if name != rim_name
            },
            **retained,
        }
        sides[side] = {
            "rim": rim_name,
            "temporary_removal": removed,
            "geometry_altered": False,
            "retained_outer_header_rows": len(header_stacks),
            "retained_outer_header_stacks": header_stacks,
            "viewer_supplemental_heads_washers_absent_for": sorted(
                name
                for name in assembly["stacks"]
                if name not in removed["station_bolt_stacks"]
                and set(assembly["stacks"][name]) == {"shaft"}
            ),
            "retained_inventory": {
                "other_uncut_wood": len(targets["other_uncut_wood"]),
                "barrels": len(targets["retained_barrels"]),
                "bolt_stack_solids": len(targets["retained_bolt_stacks"]),
                "protected_panel_screws": 66 - len(removed["fixed_panel_screws"]),
                "protected_frame_bolts": 12 - len(removed["fixed_frame_bolts"]),
                "other_protected_envelopes": len(targets["protected_envelopes"])
                - 66
                - 12
                + len(removed["fixed_panel_screws"])
                + len(removed["fixed_frame_bolts"]),
            },
            "withdrawal": _sample_withdrawal(wood[rim_name], SAMPLES_MM, targets),
        }
    return {
        "schema": SCHEMA,
        "source_assembly": (
            "export_owner_barrel_scene.build_integrated_viewer_assembly"
            if assembly.get("post_placement") == "integrated"
            else "export_owner_barrel_scene.build_viewer_assembly"
        ),
        "width_option": KERF_RIGHT,
        "source_forward_row_y_mm": SOURCE_FORWARD_Y_MM,
        "fixed_axis_inventory": graph["fixed_axis_inventory"],
        "fixed_axis_coordinates_changed": False,
        "source_release_flags": dict(assembly["release_flags"]),
        "sides": sides,
        "drilling_released": False,
        "fabrication_released": False,
        "structural_released": False,
        "limits": (
            "Wood is checked only at isolated 0..160 mm positions at 5 mm spacing. "
            "A conservative full-path swept AABB excludes retained nominal hardware "
            "and protected envelopes, but not all other timber boxes or tolerances. "
            "Represented barrel/stack solids are provisional; "
            "all modeled heads/washers are provisional envelopes, not delivered parts. "
            "protected holds, T-nuts and electrical shapes are modeled envelopes, "
            "including a trial hold-bolt projection. Actual delivered hardware, "
            "tools, support, fastener access, demounting, reassembly and strength "
            "remain unverified. No drilling, fabrication or structural approval."
        ),
    }


if __name__ == "__main__":
    print(json.dumps(probe(), indent=2, sort_keys=True))
