"""Finite current ten-bore side-cleat/Y trials; nominal CAD only."""

import json
from unittest.mock import patch

import cadquery as cq

from scripts import simple_center_combined_cleats_probe as combined
from scripts import simple_center_current_placement_table as placement
from scripts import simple_center_header_principal_probe as frame
from scripts import simple_center_post_header_two_bolt_probe as post
from scripts import simple_center_second_bolt_tolerance_probe as prior
from scripts import simple_center_tolerance_pose_probe as tolerance
from scripts import simple_center_wide_post_probe as wide

# Rear face stays against the existing rear cleat; side cleat is one solid blank.
# Each tuple is (front Y, upright Y, upright Z), millimeters.
VARIANTS = {
    "minimum_depth_centered": (-114.9, -145.3, 360),
    "moderate_depth_shift": (-104.6, -135, 360),
    "deeper_same_upright": (-95.7, -135, 360),
}
SIDE_REAR_Y = -175.7
LINK_REAR_Y = -213.8


def _change(parts, bores, ends, front_y, upright_y, upright_z):
    parts["upright_side_cleat"] = cq.Solid.makeBox(
        88.9, front_y - SIDE_REAR_Y, 183, cq.Vector(89.05, SIDE_REAR_Y, 277)
    )
    bores["upright"] = combined.cylinder(
        wide.BORE_RADIUS, 127, (50.95, upright_y, upright_z), (1, 0, 0)
    )
    bores["cleat_link"] = combined.cylinder(
        wide.BORE_RADIUS, front_y - LINK_REAR_Y, (133.5, LINK_REAR_Y, 370), (0, 1, 0)
    )
    if ends is not None:
        ends["upright_left"] = (
            (50.95, upright_y, upright_z),
            (-1, 0, 0),
            "base_principal_center_right",
        )
        ends["upright_right"] = (
            (177.95, upright_y, upright_z),
            (1, 0, 0),
            "upright_side_cleat",
        )
        ends["link_front"] = ((133.5, front_y, 370), (0, 1, 0), "upright_side_cleat")
    return parts, bores, ends


def probe_one(front_y, upright_y, upright_z):
    """Use the maintained full-center checker, then correct its fixed link insertion length."""
    original_geometry = prior._geometry

    def changed_prior_geometry():
        return _change(*original_geometry(), front_y, upright_y, upright_z)

    with patch.object(prior, "_geometry", changed_prior_geometry):
        checked = post._candidate(post.VARIANTS["shorter_8in_trial"])

    original_current = placement._geometry

    def changed_current_geometry():
        parts, bores, owners = original_current()
        _change(parts, bores, None, front_y, upright_y, upright_z)
        return parts, bores, owners

    with patch.object(placement, "_geometry", changed_current_geometry):
        inventory = placement.table()

    parts, bores, _ = changed_current_geometry()
    counts, screws = frame._fixed_screws()
    side = {"upright_side_cleat": parts["upright_side_cleat"]}
    # The parent checker only identifies its post/header block as new wood.
    side_checks = {
        "side_other_wood_hits_mm3": combined.hits(
            side,
            {
                name: wood
                for name, wood in parts.items()
                if name != "upright_side_cleat"
            },
        ),
        "side_screw_hits_mm3": combined.hits(side, screws),
    }
    ends = {
        "link_rear": ((133.5, LINK_REAR_Y, 370), (0, -1, 0), "rear_cleat"),
        "link_front": ((133.5, front_y, 370), (0, 1, 0), "upright_side_cleat"),
    }
    # Rebuild all 20 end envelopes for the changed link approach; the maintained
    # checker otherwise uses its original 94.9-mm link insertion length.
    _, _, all_ends = changed_prior_geometry()
    for name in (
        "post_left",
        "post_cleat_right",
        "post_cleat_bottom",
        "post_header_top",
    ):
        all_ends.pop(name)
    bottom, post_y, post_z, vertical_x = post.VARIANTS["shorter_8in_trial"]
    for index, z in enumerate(post_z, 1):
        all_ends[f"post_cleat_{index}_left"] = (
            (88.75, post_y, z),
            (-1, 0, 0),
            "shifted_right_post",
        )
        all_ends[f"post_cleat_{index}_right"] = (
            (266.55, post_y, z),
            (1, 0, 0),
            "header_post_side_cleat",
        )
    for index, x in enumerate(vertical_x, 1):
        all_ends[f"cleat_header_{index}_bottom"] = (
            (x, -130, bottom),
            (0, 0, -1),
            "header_post_side_cleat",
        )
        all_ends[f"cleat_header_{index}_top"] = (
            (x, -130, 277),
            (0, 0, 1),
            "base_header",
        )
    _, _, all_hardware, _ = combined.end_envelopes(all_ends, parts)
    link_length = front_y - LINK_REAR_Y
    insertion = {
        name: combined.cylinder(
            wide.BORE_RADIUS, link_length + post.INSERTION_ALLOWANCE, point, outward
        )
        for name, (point, outward, _) in ends.items()
    }
    insertion_hits = combined.hits(insertion, parts) | combined.hits(insertion, screws)
    insertion_hits |= {
        key: volume
        for key, volume in combined.hits(insertion, all_hardware).items()
        if key.split("/")[1] not in ends
    }
    insertion_clear = [
        name
        for name in ends
        if not any(key.startswith(f"{name}/") for key in insertion_hits)
    ]
    side_y = [upright_y - SIDE_REAR_Y, front_y - upright_y]
    side_reserve = round(
        min(side_y) - 4 * placement.DIAMETER_MM - placement.FABRICATION_ALLOWANCE_MM, 5
    )
    failed_rows = [
        {k: row[k] for k in ("bolt", "member", "feature", "reserve_mm")}
        for row in inventory["rows"]
        if row["reserve_mm"] is not None and row["reserve_mm"] < 0
    ]
    geometry_clear = (
        checked["nominal_geometry"] == "feasible"
        and counts == {"panel": 48, "kicker": 18}
        and len(screws) == 66
        and not any(side_checks.values())
        and bool(insertion_clear)
    )
    return {
        "side_bounds_mm": list(wide.bounds(parts["upright_side_cleat"])),
        "upright_axis_yz_mm": [upright_y, upright_z],
        "side_y_edge_distances_mm": side_y,
        "side_y_conditional_4d_plus_project_5_reserve_mm": side_reserve,
        "conditional_subset_minimum_reserve_mm": inventory[
            "conditional_subset_minimum_reserve_mm"
        ],
        "conditional_negative_rows": failed_rows,
        "whole_center_classification_complete": False,
        "bore_count": len(bores),
        "fixed_screw_count": len(screws),
        "inner_kicker_edges_supported": tolerance._fixed()[2][
            "inner_kicker_edges_supported"
        ],
        "bore_received_fraction": checked["bore_received_fraction"],
        "washer_bearing_fraction": checked["washer_bearing_fraction"],
        "clear_insertion_ends_by_bolt": checked["clear_insertion_ends_by_bolt"]
        | {"cleat_link": insertion_clear},
        "link_insertion_hits_mm3": insertion_hits,
        "side_checks": side_checks,
        "full_center_collision_checks": checked["collision_checks"],
        "nominal_cad_clear": geometry_clear,
        "conditional_subset_clear": not failed_rows,
        "rating_or_drilling_release": False,
    }


def probe():
    return {name: probe_one(*parameters) for name, parameters in VARIANTS.items()}


if __name__ == "__main__":
    result = probe()
    assert all(
        row["bore_count"] == 10 and row["fixed_screw_count"] == 66
        for row in result.values()
    )
    print(json.dumps(result, indent=2, sort_keys=True))
