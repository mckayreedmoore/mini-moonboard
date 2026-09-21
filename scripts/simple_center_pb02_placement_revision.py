"""Bounded PB02 conditional placement trials; nominal geometry, not a release."""

import json
from dataclasses import replace
from functools import lru_cache
from unittest.mock import patch

from scripts import simple_center_combined_cleats_probe as combined
from scripts import simple_center_current_placement_table as placement
from scripts import simple_center_header_principal_probe as frame
from scripts import simple_center_pb02_integrated_trial as integrated
from scripts import simple_center_post_header_two_bolt_probe as post
from scripts import simple_center_second_bolt_tolerance_probe as prior
from scripts import simple_center_side_depth_y_probe as side
from scripts import simple_center_wide_post_probe as wide

# Fixed side-cleat pose; vary only the post-high axis and the two vertical axes.
TRIALS = {
    "working_reference": (190.0, (208.35, 235.85), (-130.0, -130.0)),
    "rear_stagger": (189.0, (208.35, 235.85), (-130.0, -144.0)),
    "front_stagger": (189.0, (208.35, 236.0), (-130.5, -117.5)),
}


def trial(post_high_z, vertical_x, vertical_y):
    """Rebuild the ten bores and independently check placement and full CAD fit."""
    original_geometry = prior._geometry
    source_counts, source_screws = frame._fixed_screws()
    source_axes = {
        name: (tuple(wide.bounds(solid)), round(solid.Volume(), 8))
        for name, solid in source_screws.items()
    }
    config = (95, -145, (145, 176), vertical_x)
    extended_config = (*config, vertical_y)

    def changed_geometry():
        parts, bores, ends = side._change(
            *original_geometry(),
            integrated.FRONT_Y,
            integrated.UPRIGHT_Y,
            integrated.UPRIGHT_Z,
        )
        dz = post_high_z - 190
        bores["post_high"] = bores["post_high"].translate((0, 0, dz))
        for name in ("post_rear_high", "post_front_high"):
            point, outward, owner = ends[name]
            ends[name] = ((point[0], point[1], point[2] + dz), outward, owner)
        return parts, bores, ends

    with (
        patch.object(prior, "POSE", replace(prior.POSE, top_z=344)),
        patch.object(prior, "_geometry", changed_geometry),
        patch.dict(post.VARIANTS, {"shorter_8in_trial": config}),
    ):
        fit = post._candidate(extended_config)
        parts, bores, owners = placement._geometry()
        bores["cleat_header_1"] = bores["cleat_header_1"].translate(
            (0, vertical_y[0] + 130, 0)
        )
        bores["cleat_header_2"] = bores["cleat_header_2"].translate(
            (0, vertical_y[1] + 130, 0)
        )
        with patch.object(placement, "_geometry", return_value=(parts, bores, owners)):
            inventory = placement.table()

    negatives = [
        {key: row[key] for key in ("bolt", "member", "feature", "reserve_mm")}
        for row in inventory["rows"]
        if row["reserve_mm"] is not None and row["reserve_mm"] < -1e-5
    ]
    target_rows = [
        row
        for row in inventory["rows"]
        if (
            row["bolt"] == "post_high"
            and row["member"] == "shifted_right_post"
            and row["feature"] == "z_high"
        )
        or (row["bolt"] == "cleat_header_1" and row["feature"] == "cleat_header_2")
    ]
    counts, screws = frame._fixed_screws()
    axes = {
        name: (tuple(wide.bounds(solid)), round(solid.Volume(), 8))
        for name, solid in screws.items()
    }
    side_wood = {"upright_side_cleat": parts["upright_side_cleat"]}
    side_checks = {
        "side_other_wood_hits_mm3": combined.hits(
            side_wood,
            {name: wood for name, wood in parts.items() if name not in side_wood},
        ),
        "side_screw_hits_mm3": combined.hits(side_wood, screws),
    }
    axes_fixed = (
        source_counts == counts == {"panel": 48, "kicker": 18}
        and source_axes == axes
        and len(axes) == 66
    )
    nominal_fit = (
        fit["nominal_geometry"] == "feasible"
        and not any(side_checks.values())
        and all(value == 1 for value in fit["bore_received_fraction"].values())
        and all(value == 1 for value in fit["washer_bearing_fraction"].values())
        and all(fit["clear_insertion_ends_by_bolt"].values())
        and axes_fixed
    )
    return {
        "post_high_z_mm": post_high_z,
        "vertical_x_mm": vertical_x,
        "vertical_y_mm": vertical_y,
        "conditional_minimum_reserve_mm": inventory[
            "conditional_subset_minimum_reserve_mm"
        ],
        "conditional_negative_rows": negatives,
        "target_conditional_reserves_mm": {
            f"{row['bolt']}/{row['member']}/{row['feature']}": row["reserve_mm"]
            for row in target_rows
        },
        "nominal_cad_clear": nominal_fit,
        "fixed_screw_axes_preserved": axes_fixed,
        "full_center_collision_checks": fit["collision_checks"],
        "side_checks": side_checks,
        "bore_received_fraction": fit["bore_received_fraction"],
        "washer_bearing_fraction": fit["washer_bearing_fraction"],
        "clear_insertion_ends_by_bolt": fit["clear_insertion_ends_by_bolt"],
        "conditional_geometry_only": True,
        "whole_center_classification_complete": False,
        "rating_or_drilling_release": False,
    }


@lru_cache(maxsize=1)
def probe():
    return {name: trial(*coordinates) for name, coordinates in TRIALS.items()}


if __name__ == "__main__":
    print(json.dumps(probe(), indent=2, sort_keys=True))
