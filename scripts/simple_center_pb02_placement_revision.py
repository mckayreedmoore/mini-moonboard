"""Bounded PB02 conditional placement trials; nominal geometry, not a release."""

import json
from functools import lru_cache

from scripts import simple_center_combined_cleats_probe as combined
from scripts import simple_center_current_placement_table as placement
from scripts import simple_center_header_principal_probe as frame
from scripts import simple_center_post_header_two_bolt_probe as post
from scripts import simple_center_wide_post_probe as wide
from scripts.simple_center_pb02_geometry import TRIAL_SPECS, build_center_geometry

# Fixed side-cleat pose; vary only the post-high axis and the two vertical axes.
TRIALS = TRIAL_SPECS


def trial(spec):
    """Rebuild the ten bores and independently check placement and full CAD fit."""
    source_counts, source_screws = frame._fixed_screws()
    source_axes = {
        name: (tuple(wide.bounds(solid)), round(solid.Volume(), 8))
        for name, solid in source_screws.items()
    }
    geometry = build_center_geometry(spec)
    parts, bores, _ = geometry
    config = (95, -145, (145, 176), spec.vertical_x, spec.vertical_y)
    fit = post._candidate(config, geometry=geometry)
    inventory = placement.table((parts, bores, placement._owners()), spec.variant_id)

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
        "variant_id": spec.variant_id,
        "post_high_z_mm": spec.post_high_z,
        "post_high_loaded_end_distance_mm": round(238.9 - spec.post_high_z, 5),
        "post_high_conditional_3_5d_reserve_mm": round(
            238.9 - spec.post_high_z - 3.5 * placement.DIAMETER_MM, 5
        ),
        "post_high_conditional_c_delta": round(
            min(1.0, (238.9 - spec.post_high_z) / (7 * placement.DIAMETER_MM)), 5
        ),
        "vertical_x_mm": spec.vertical_x,
        "vertical_y_mm": spec.vertical_y,
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
    return {name: trial(spec) for name, spec in TRIALS.items()}


if __name__ == "__main__":
    print(json.dumps(probe(), indent=2, sort_keys=True))
