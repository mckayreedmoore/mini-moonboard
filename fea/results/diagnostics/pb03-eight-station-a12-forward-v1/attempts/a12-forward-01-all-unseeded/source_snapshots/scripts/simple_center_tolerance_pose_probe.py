"""Bounded PB-02 center-pose search; nominal geometry, never a drill release."""

import json
import sys
from dataclasses import asdict, dataclass
from functools import lru_cache
from pathlib import Path

import cadquery as cq

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts import simple_center_combined_cleats_probe as combined
from scripts import simple_center_combined_small_tool_probe as small
from scripts import simple_center_header_principal_probe as frame
from scripts import simple_center_link_edge_probe as link
from scripts import simple_center_wide_post_probe as wide

TARGET_MARGIN = 5.0
EXTENSION_SCREEN_LENGTH = 100.0  # Illustrative coaxial clearance, not a catalog tool.
INSERTION_ALLOWANCE = 25.0  # Illustrative protrusion beyond modeled wood span.


@dataclass(frozen=True)
class Pose:
    rear_y: float = -190.0
    top_z: float = 338.0
    vertical_y: float = -145.3
    cross_z: float = 307.5
    upright_y: float = -147.3
    upright_z: float = 350.0
    link_x: float = 133.5


def _distances(pose):
    return {
        "header_vertical_y_transverse_mm": [
            pose.vertical_y + 175.7,
            -36.0 - pose.vertical_y,
        ],
        "cleat_vertical_x_transverse_mm": [35.475, 35.475],
        "cleat_vertical_y_grain_ends_mm": [
            pose.vertical_y - pose.rear_y,
            -45.0 - pose.vertical_y,
        ],
        "cleat_cross_z_transverse_mm": [
            pose.cross_z - 277.0,
            pose.top_z - pose.cross_z,
        ],
        "cleat_cross_y_grain_ends_mm": [-95.0 - pose.rear_y, 50.0],
    }


def _margin(distances):
    values = [
        value - (small.EDGE_RESERVE if "transverse" in name else small.END_RESERVE)
        for name, pair in distances.items()
        for value in pair
    ]
    return round(min(values), 5)


@lru_cache(maxsize=1)
def _fixed():
    return frame._parts(), frame._fixed_screws(), link.probe()


def _pair_hits(solids):
    items = list(solids.items())
    return {
        f"{name}/{other}": round(volume, 5)
        for index, (name, shape) in enumerate(items)
        for other, second in items[index + 1 :]
        if (volume := wide.hit_volume(shape, second)) > wide.TOL
    }


def _fraction(shape, wood):
    return round(wide.hit_volume(shape, wood) / shape.Volume(), 8)


def evaluate(pose, *, detailed=True):
    """Evaluate one bounded pose, including complete envelopes when requested."""
    distances = _distances(pose)
    margin = _margin(distances)
    result = {
        "coordinates_mm": asdict(pose),
        "conditional_distances_mm": distances,
        "minimum_margin_mm": margin,
        "target_margin_met": margin >= TARGET_MARGIN - 1e-6,
        "nominal_geometry": "not screened",
    }
    if not detailed:
        return result

    original_parts, (counts, screws), baseline = _fixed()
    cleat = cq.Solid.makeBox(
        70.95,
        -45.0 - pose.rear_y,
        pose.top_z - 277.0,
        cq.Vector(-20, pose.rear_y, 277),
    )
    new_wood = {
        "header_post_side_cleat": combined.NEW_WOOD["header_post_side_cleat"],
        "header_side_cleat": cleat,
    }
    parts = original_parts | new_wood
    bores = combined.new_bores() | {
        "header_cleat": combined.cylinder(
            wide.BORE_RADIUS,
            pose.top_z - 238.9,
            (15.475, pose.vertical_y, 238.9),
            (0, 0, 1),
        ),
        "cleat_principal": combined.cylinder(
            wide.BORE_RADIUS,
            109.05,
            (-20, -95, pose.cross_z),
            (1, 0, 0),
        ),
    }
    old_bores = combined.inherited_bores() | {
        "upright": combined.cylinder(
            wide.BORE_RADIUS, 127, (50.95, pose.upright_y, pose.upright_z), (1, 0, 0)
        ),
        "cleat_link": combined.cylinder(
            wide.BORE_RADIUS, 94.9, (pose.link_x, -213.8, 370), (0, 1, 0)
        ),
    }
    new_ends = combined.NEW_ENDS | {
        "principal_header_bottom": (
            (15.475, pose.vertical_y, 238.9),
            (0, 0, -1),
            "base_header",
        ),
        "principal_cleat_top": (
            (15.475, pose.vertical_y, pose.top_z),
            (0, 0, 1),
            "header_side_cleat",
        ),
        "principal_cleat_left": (
            (-20, -95, pose.cross_z),
            (-1, 0, 0),
            "header_side_cleat",
        ),
        "principal_right": (
            (89.05, -95, pose.cross_z),
            (1, 0, 0),
            "base_principal_center_right",
        ),
    }
    old_ends = combined.INHERITED_ENDS | {
        "upright_left": (
            (50.95, pose.upright_y, pose.upright_z),
            (-1, 0, 0),
            "base_principal_center_right",
        ),
        "upright_right": (
            (177.95, pose.upright_y, pose.upright_z),
            (1, 0, 0),
            "upright_side_cleat",
        ),
        "link_rear": ((pose.link_x, -213.8, 370), (0, -1, 0), "rear_cleat"),
        "link_front": ((pose.link_x, -118.9, 370), (0, 1, 0), "upright_side_cleat"),
    }
    ends = new_ends | old_ends
    all_bores = bores | old_bores
    intended = combined.INTENDED | {
        "post_low": ("rear_cleat", "shifted_right_post"),
        "post_high": ("rear_cleat", "shifted_right_post"),
        "upright": ("base_principal_center_right", "upright_side_cleat"),
        "cleat_link": ("rear_cleat", "upright_side_cleat"),
    }
    washers, seats, hardware, _ = combined.end_envelopes(ends, parts)
    sockets = {
        name: combined.cylinder(
            small.SOCKET_RADIUS, small.SOCKET_LENGTH, point, outward
        )
        for name, (point, outward, _) in ends.items()
    }
    # Screen either approach with an illustrative hardware/protrusion allowance.
    insertion = {
        name: combined.cylinder(
            wide.BORE_RADIUS, 127 + INSERTION_ALLOWANCE, point, outward
        )
        for name, (point, outward, _) in ends.items()
        if name in ("upright_left", "upright_right")
    }
    # All other approach lengths are the actual modeled bore spans.
    for length, end_names in {
        177.8: ("post_left", "post_cleat_right"),
        167.0: ("post_cleat_bottom", "post_header_top"),
        pose.top_z - 238.9: ("principal_header_bottom", "principal_cleat_top"),
        109.05: ("principal_cleat_left", "principal_right"),
        94.9: ("link_rear", "link_front"),
    }.items():
        for name in end_names:
            point, outward, _ = ends[name]
            insertion[name] = combined.cylinder(
                wide.BORE_RADIUS, length + INSERTION_ALLOWANCE, point, outward
            )
    for name in (
        "post_rear_low",
        "post_front_low",
        "post_rear_high",
        "post_front_high",
    ):
        point, outward, _ = ends[name]
        insertion[name] = combined.cylinder(
            wide.BORE_RADIUS, 127 + INSERTION_ALLOWANCE, point, outward
        )
    extension = {
        name: combined.cylinder(
            small.SOCKET_RADIUS,
            EXTENSION_SCREEN_LENGTH,
            tuple(point[i] + outward[i] * small.SOCKET_LENGTH for i in range(3)),
            outward,
        )
        for name, (point, outward, _) in ends.items()
    }
    received = {
        name: round(
            sum(wide.hit_volume(bore, parts[wood]) for wood in intended[name])
            / bore.Volume(),
            8,
        )
        for name, bore in all_bores.items()
    }
    header_receivers = {
        name: _fraction(screw, parts["base_header"])
        for name, screw in screws.items()
        if name.startswith("kicker_header_")
    }
    center_receivers = {}
    for name, wood in (
        ("round_kicker_left_center_1", "base_post_center_left"),
        ("round_kicker_left_center_2", "base_post_center_left"),
        ("round_kicker_right_center_1", "backer"),
        ("round_kicker_right_center_2", "backer"),
    ):
        kicker = parts["kicker_left" if "_left_" in name else "kicker_right"]
        center_receivers[name] = _fraction(screws[name].cut(kicker), parts[wood])
    checks = {
        "wood_overlaps_mm3": combined.hits(
            new_wood, {k: v for k, v in parts.items() if k not in new_wood}
        )
        | combined.hits(
            {"header_side_cleat": cleat},
            {"header_post_side_cleat": new_wood["header_post_side_cleat"]},
        ),
        "wood_screw_hits_mm3": combined.hits(new_wood, screws),
        "bore_unintended_wood_hits_mm3": {
            key: volume
            for name, bore in all_bores.items()
            for key, volume in combined.hits(
                {name: bore},
                {
                    wood: solid
                    for wood, solid in parts.items()
                    if wood not in intended[name]
                },
            ).items()
        },
        "bore_pair_hits_mm3": _pair_hits(all_bores),
        "bore_screw_hits_mm3": combined.hits(all_bores, screws),
        "hardware_wood_hits_mm3": combined.hits(hardware, parts),
        "hardware_screw_hits_mm3": combined.hits(hardware, screws),
        "hardware_pair_hits_mm3": _pair_hits(hardware),
        "washer_face_wood_hits_mm3": combined.hits(seats, parts),
        "washer_face_screw_hits_mm3": combined.hits(seats, screws),
        "socket_body_wood_hits_mm3": combined.hits(sockets, parts),
        "socket_body_screw_hits_mm3": combined.hits(sockets, screws),
        "socket_body_cross_hardware_hits_mm3": {
            key: value
            for key, value in combined.hits(sockets, hardware).items()
            if key.split("/")[0] != key.split("/")[1]
        },
        "socket_body_pair_hits_mm3": _pair_hits(sockets),
    }
    insertion_wood = combined.hits(insertion, parts)
    insertion_screws = combined.hits(insertion, screws)
    insertion_pairs = {
        "post_cleat": ("post_left", "post_cleat_right"),
        "cleat_header": ("post_cleat_bottom", "post_header_top"),
        "header_cleat": ("principal_header_bottom", "principal_cleat_top"),
        "cleat_principal": ("principal_cleat_left", "principal_right"),
        "post_low": ("post_rear_low", "post_front_low"),
        "post_high": ("post_rear_high", "post_front_high"),
        "upright": ("upright_left", "upright_right"),
        "cleat_link": ("link_rear", "link_front"),
    }
    insertion_clear = {
        bolt: [
            end
            for end in pair
            if not any(
                key.startswith(f"{end}/") for key in insertion_wood | insertion_screws
            )
        ]
        for bolt, pair in insertion_pairs.items()
    }
    extension_wood = combined.hits(extension, parts)
    extension_screws = combined.hits(extension, screws)
    fixed_clear = (
        counts == baseline["fixed_axes"] == {"panel": 48, "kicker": 18}
        and len(screws) == 66
        and all(baseline["inner_kicker_edges_supported"].values())
        and all(
            not baseline[key]
            for key in (
                "solid_overlaps_mm3",
                "fixed_screw_hits_mm3",
                "bore_unintended_wood_hits_mm3",
                "bore_pair_hits_mm3",
                "trial_20mm_radius_tool_wood_hits_mm3",
            )
        )
        and len(header_receivers) == 10
        and set(header_receivers.values()) == {0.7125}
        and len(center_receivers) == 4
        and set(center_receivers.values()) == {1.0}
    )
    clear = (
        fixed_clear
        and all(insertion_clear.values())
        and all(value == 1 for value in received.values())
        and all(value == 1 for value in washers.values())
        and all(not value for value in checks.values())
    )
    result.update(
        {
            "fixed_axes": counts,
            "fixed_screw_axes_checked": len(screws),
            "inner_kicker_edges_supported": baseline["inner_kicker_edges_supported"],
            "fixed_geometry_clear": fixed_clear,
            "header_screw_receiver_fraction": header_receivers,
            "center_kicker_screw_receiver_fraction": center_receivers,
            "bore_received_fraction": received,
            "washer_bearing_fraction": washers,
            "socket_body_radius_mm": round(small.SOCKET_RADIUS, 4),
            "socket_body_length_mm": round(small.SOCKET_LENGTH, 3),
            "illustrative_extension_screen_length_mm": EXTENSION_SCREEN_LENGTH,
            "illustrative_insertion_allowance_mm": INSERTION_ALLOWANCE,
            "insertion_wood_hits_mm3": insertion_wood,
            "insertion_screw_hits_mm3": insertion_screws,
            "clear_insertion_ends_by_bolt": insertion_clear,
            "extension_wood_hits_mm3": extension_wood,
            "extension_screw_hits_mm3": extension_screws,
            **checks,
            "nominal_geometry": "feasible" if clear else "rejected",
        }
    )
    return result


def search():
    """Screen a finite, named set of physical changes and retain all failures."""
    poses = {
        "reference": Pose(),
        "rear_extension_only": Pose(rear_y=-196),
        "top_and_cross_only": Pose(top_z=348, cross_z=312.5),
        "upright_and_top": Pose(
            vertical_y=-139, top_z=348, cross_z=312.5, upright_y=-135, upright_z=360
        ),
        "upright_and_top_link_shift": Pose(
            vertical_y=-139,
            top_z=348,
            cross_z=312.5,
            upright_y=-135,
            upright_z=360,
            link_x=136.5,
        ),
    }
    trials = {
        name: evaluate(pose, detailed=name.startswith("upright_and_top"))
        for name, pose in poses.items()
    }
    feasible = [
        name
        for name, trial in trials.items()
        if trial["nominal_geometry"] == "feasible"
    ]
    best = (
        max(feasible, key=lambda name: trials[name]["minimum_margin_mm"])
        if feasible
        else max(trials, key=lambda name: trials[name]["minimum_margin_mm"])
    )
    return {
        "tested_poses": trials,
        "best_pose": best,
        "target_margin_feasible_in_tested_set": bool(
            feasible and trials[best]["target_margin_met"]
        ),
        "fixed_axes": trials["upright_and_top"]["fixed_axes"],
        "fixed_screw_axes_checked": trials["upright_and_top"][
            "fixed_screw_axes_checked"
        ],
        "inner_kicker_edges_supported": trials["upright_and_top"][
            "inner_kicker_edges_supported"
        ],
        "ratchet_sweep_verified": False,
        "extension_diameter_verified": False,
        "delivered_bolt_stack_verified": False,
        "joint_mechanics_verified": False,
        "geometry_only": True,
        "rating_or_drilling_release": False,
    }


if __name__ == "__main__":
    print(json.dumps(search(), indent=2, sort_keys=True))
