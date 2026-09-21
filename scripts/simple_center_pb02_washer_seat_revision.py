"""Bounded PB-02 center revision using the maintained ten-bore CAD checker.

All coordinates are nominal millimeters. This is geometry evidence only.
"""

import json
from dataclasses import dataclass, replace
from unittest.mock import patch

import cadquery as cq

from scripts import simple_center_header_principal_probe as frame
from scripts import simple_center_second_bolt_tolerance_probe as prior
from scripts import simple_center_side_depth_y_probe as side
from scripts import simple_center_wide_post_probe as wide


@dataclass(frozen=True)
class Trial:
    front_y: float
    upright_y: float
    upright_z: float
    header_side_top_z: float
    side_bottom_z: float = 277.0


TRIALS = {
    "minimum_depth_lowered_header": Trial(-114.9, -145.3, 355, 343),
    "working_61p6_depth": Trial(-114.1, -144.5, 356, 344),
    "deeper_raised_bottom": Trial(-110.7, -141.1, 358, 344, 305),
}
SIDE_TOP_Z = 460.0
LINK_Z = 370.0
CONDITIONAL_GRAIN_END_TARGET_MM = 7 * 6.35 + 5


def evaluate(trial: Trial):
    """Change only three local solids/axes in the existing full-center model."""
    original_change = side._change
    fixed_counts, fixed_screws = frame._fixed_screws()
    fixed_axes = {
        name: (tuple(wide.bounds(solid)), round(solid.Volume(), 8))
        for name, solid in fixed_screws.items()
    }

    def changed(parts, bores, ends, front_y, upright_y, upright_z, link_z=LINK_Z):
        parts, bores, ends = original_change(
            parts, bores, ends, front_y, upright_y, upright_z, link_z
        )
        if trial.side_bottom_z != 277:
            parts["upright_side_cleat"] = cq.Solid.makeBox(
                88.9,
                front_y - side.SIDE_REAR_Y,
                SIDE_TOP_Z - trial.side_bottom_z,
                cq.Vector(89.05, side.SIDE_REAR_Y, trial.side_bottom_z),
            )
        return parts, bores, ends

    pose = replace(prior.POSE, top_z=trial.header_side_top_z)
    with patch.object(prior, "POSE", pose), patch.object(side, "_change", changed):
        result = side.probe_one(trial.front_y, trial.upright_y, trial.upright_z)
        parts, bores, _ = prior._geometry()
        header = parts["base_header"]
        cleat = parts["header_side_cleat"]
        bore = bores["header_cleat"]
        # A 0.01-mm downward contact probe measures the common nominal face.
        contact_area = wide.hit_volume(cleat.translate((0, 0, -0.01)), header) / 0.01
        bore_reception = {
            name: round(wide.hit_volume(bore, parts[name]) / bore.Volume(), 8)
            for name in ("base_header", "header_side_cleat")
        }
        trial_counts, trial_screws = frame._fixed_screws()
        trial_axes = {
            name: (tuple(wide.bounds(solid)), round(solid.Volume(), 8))
            for name, solid in trial_screws.items()
        }

    assert result["bore_count"] == 10
    assert result["fixed_screw_count"] == 66
    assert fixed_counts == trial_counts == {"panel": 48, "kicker": 18}
    assert fixed_axes == trial_axes
    assert len(result["washer_bearing_fraction"]) == 20
    assert len(result["clear_insertion_ends_by_bolt"]) == 10
    assert all(result["inner_kicker_edges_supported"].values())
    assert contact_area > 0
    assert all(fraction > 0 for fraction in bore_reception.values())
    assert round(sum(bore_reception.values()), 8) == 1

    z_distances = {
        "upright_bottom": trial.upright_z - trial.side_bottom_z,
        "upright_top": SIDE_TOP_Z - trial.upright_z,
        "link_bottom": LINK_Z - trial.side_bottom_z,
        "link_top": SIDE_TOP_Z - LINK_Z,
    }
    result["coordinates_mm"] = {
        "side_rear_y": side.SIDE_REAR_Y,
        "side_front_y": trial.front_y,
        "side_bottom_z": trial.side_bottom_z,
        "side_top_z": SIDE_TOP_Z,
        "upright_y": trial.upright_y,
        "upright_z": trial.upright_z,
        "header_side_top_z": trial.header_side_top_z,
    }
    result["side_z_end_distances_mm"] = z_distances
    result["header_side_cleat_header_contact_area_mm2"] = round(contact_area, 5)
    result["header_cleat_bore_reception_fraction"] = bore_reception
    result["all_66_fixed_axes_preserved"] = True
    result["side_z_conditional_7d_plus_5_reserve_mm"] = round(
        min(z_distances.values()) - CONDITIONAL_GRAIN_END_TARGET_MM, 5
    )
    result["all_20_washer_seats_full"] = all(
        fraction == 1 for fraction in result["washer_bearing_fraction"].values()
    )
    result["one_insertion_end_per_bolt_clear"] = all(
        result["clear_insertion_ends_by_bolt"].values()
    )
    result["conditional_geometry_only"] = True
    result["rating_or_drilling_release"] = False
    return result


def probe():
    return {name: evaluate(trial) for name, trial in TRIALS.items()}


if __name__ == "__main__":
    print(json.dumps(probe(), indent=2, sort_keys=True))
