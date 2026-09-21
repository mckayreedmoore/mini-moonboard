"""One PB02 ten-bore nominal CAD trial; no strength or drilling release."""

import json
from dataclasses import replace
from itertools import combinations
from unittest.mock import patch

from scripts import simple_center_current_placement_table as placement
from scripts import simple_center_current_stack_tip_screen as stack
from scripts import simple_center_header_principal_probe as frame
from scripts import simple_center_post_header_two_bolt_probe as post
from scripts import simple_center_second_bolt_tolerance_probe as prior
from scripts import simple_center_side_depth_y_probe as side
from scripts import simple_center_wide_post_probe as wide

FRONT_Y = -114.1
UPRIGHT_Y = -144.5
UPRIGHT_Z = 356
WORKING_LINK_Z = 370
COMPARISON_LINK_Z = 390
POST_CLEAT_2_Z = 176


def working_geometry():
    """Return the maintained ten-bore source geometry at the checked Z370 pose."""
    source_geometry = prior._geometry
    config = list(post.VARIANTS["shorter_8in_trial"])
    config[2] = (config[2][0], POST_CLEAT_2_Z)

    def integrated_geometry():
        return side._change(*source_geometry(), FRONT_Y, UPRIGHT_Y, UPRIGHT_Z)

    with (
        patch.object(prior, "POSE", replace(prior.POSE, top_z=344)),
        patch.dict(post.VARIANTS, {"shorter_8in_trial": tuple(config)}),
        patch.object(prior, "_geometry", integrated_geometry),
    ):
        return stack._geometry()


def probe(link_z=WORKING_LINK_Z):
    source_geometry = prior._geometry
    source_counts, source_screws = frame._fixed_screws()
    source_axes = {
        name: (tuple(wide.bounds(solid)), round(solid.Volume(), 8))
        for name, solid in source_screws.items()
    }
    config = list(post.VARIANTS["shorter_8in_trial"])
    config[2] = (config[2][0], POST_CLEAT_2_Z)
    pose = replace(prior.POSE, top_z=344)

    def integrated_geometry():
        return side._change(*source_geometry(), FRONT_Y, UPRIGHT_Y, UPRIGHT_Z, link_z)

    with (
        patch.object(prior, "POSE", pose),
        patch.dict(post.VARIANTS, {"shorter_8in_trial": tuple(config)}),
    ):
        result = side.probe_one(FRONT_Y, UPRIGHT_Y, UPRIGHT_Z, link_z)
        with patch.object(prior, "_geometry", integrated_geometry):
            parts, bores, owners = placement._geometry()
            inventory = placement.table()

        _, screws = frame._fixed_screws()
        axes = {
            name: (tuple(wide.bounds(solid)), round(solid.Volume(), 8))
            for name, solid in screws.items()
        }
        header = parts["base_header"]
        cleat = parts["header_side_cleat"]
        contact_area = wide.hit_volume(cleat.translate((0, 0, -0.01)), header) / 0.01
        header_bore = bores["header_cleat"]
        reception = {
            name: round(
                wide.hit_volume(header_bore, parts[name]) / header_bore.Volume(), 8
            )
            for name in ("base_header", "header_side_cleat")
        }

    finite_ligaments = {
        f"{first}/{second}": round(
            placement._centerline_gap(
                bores[first],
                placement.AXES[first],
                bores[second],
                placement.AXES[second],
            )
            - 2 * wide.BORE_RADIUS,
            5,
        )
        for first, second in combinations(bores, 2)
        if set(owners[first]) & set(owners[second])
    }
    negatives = [
        {key: row[key] for key in ("bolt", "member", "feature", "reserve_mm")}
        for row in inventory["rows"]
        if row["reserve_mm"] is not None and row["reserve_mm"] < 0
    ]
    result.update(
        coordinates_mm={
            "side_rear_y": side.SIDE_REAR_Y,
            "side_front_y": FRONT_Y,
            "side_bottom_z": 277,
            "side_top_z": 460,
            "upright_y": UPRIGHT_Y,
            "upright_z": UPRIGHT_Z,
            "header_side_top_z": 344,
            "post_cleat_2_z": POST_CLEAT_2_Z,
            "cleat_link_z": link_z,
        },
        header_side_cleat_header_contact_area_mm2=round(contact_area, 5),
        header_cleat_bore_reception_fraction=reception,
        all_66_fixed_axes_preserved=(
            source_counts == {"panel": 48, "kicker": 18}
            and source_axes == axes
            and len(axes) == 66
        ),
        finite_shared_member_bore_ligaments_mm=finite_ligaments,
        minimum_finite_shared_member_bore_ligament_mm=min(finite_ligaments.values()),
        conditional_negative_rows=negatives,
        conditional_subset_minimum_reserve_mm=inventory[
            "conditional_subset_minimum_reserve_mm"
        ],
        side_z_conditional_7d_plus_5_reserve_mm=round(
            min(UPRIGHT_Z - 277, 460 - UPRIGHT_Z, link_z - 277, 460 - link_z)
            - (7 * 6.35 + 5),
            5,
        ),
        post_pair_conditional_4d_plus_5_reserve_mm=round(
            POST_CLEAT_2_Z - config[2][0] - (4 * 6.35 + 5), 5
        ),
        all_20_washer_seats_full=all(
            value == 1 for value in result["washer_bearing_fraction"].values()
        ),
        one_insertion_end_per_bolt_clear=all(
            result["clear_insertion_ends_by_bolt"].values()
        ),
        conditional_geometry_only=True,
        rating_or_drilling_release=False,
    )
    result["integrated_nominal_cad_clear"] = (
        result["bore_count"] == 10
        and result["all_66_fixed_axes_preserved"]
        and all(result["inner_kicker_edges_supported"].values())
        and result["nominal_cad_clear"]
        and result["all_20_washer_seats_full"]
        and result["one_insertion_end_per_bolt_clear"]
        and all(value == 1 for value in result["bore_received_fraction"].values())
        and min(finite_ligaments.values()) > 0
        and contact_area > 0
        and all(value > 0 for value in reception.values())
        and round(sum(reception.values()), 8) == 1
    )
    return result


if __name__ == "__main__":
    print(
        json.dumps(
            {"working_z370": probe(), "rejected_z390": probe(COMPARISON_LINK_Z)},
            indent=2,
            sort_keys=True,
        )
    )
