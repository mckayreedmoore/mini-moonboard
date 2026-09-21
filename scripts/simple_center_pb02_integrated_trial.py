"""One PB02 ten-bore nominal CAD trial; no strength or drilling release."""

import json
from dataclasses import replace
from itertools import combinations
from unittest.mock import patch

from scripts import simple_center_combined_cleats_probe as combined
from scripts import simple_center_current_placement_table as placement
from scripts import simple_center_header_principal_probe as frame
from scripts import simple_center_post_header_two_bolt_probe as post
from scripts import simple_center_second_bolt_tolerance_probe as prior
from scripts import simple_center_side_depth_y_probe as side
from scripts import simple_center_tolerance_pose_probe as tolerance
from scripts import simple_center_wide_post_probe as wide
from scripts.simple_center_pb02_geometry import (
    ACTIVE_FINGERPRINT,
    ACTIVE_TRIAL,
    BLOCK_BOTTOM_Z,
    FRONT_Y,
    HEADER_SIDE_TOP_Z,
    POST_AXIS_Y,
    POST_CLEAT_Z,
    UPRIGHT_Y,
    UPRIGHT_Z,
    active_geometry,
    build_center_geometry,
)

WORKING_LINK_Z = 370
COMPARISON_LINK_Z = 390
POST_CLEAT_2_Z = 176


def working_geometry():
    """Compatibility alias for the active front-stagger geometry."""
    return active_geometry()


def _integrated_nominal_clear(result):
    """Require every reported collision category in the nominal summary."""
    side_checks = result.get("side_checks", {})
    required_side_checks = {
        "side_other_wood_hits_mm3",
        "side_screw_hits_mm3",
    }
    return (
        result["bore_count"] == 10
        and result["all_66_fixed_axes_preserved"]
        and all(result["inner_kicker_edges_supported"].values())
        and result["parent_nominal_geometry"] == "feasible"
        and result["all_20_washer_seats_full"]
        and result["one_insertion_end_per_bolt_clear"]
        and all(value == 1 for value in result["bore_received_fraction"].values())
        and min(result["finite_shared_member_bore_ligaments_mm"].values()) > 0
        and result["header_side_cleat_header_contact_area_mm2"] > 0
        and all(
            value > 0
            for value in result["header_cleat_bore_reception_fraction"].values()
        )
        and round(sum(result["header_cleat_bore_reception_fraction"].values()), 8) == 1
        and set(side_checks) == required_side_checks
        and not any(side_checks["side_other_wood_hits_mm3"].values())
        and not any(side_checks["side_screw_hits_mm3"].values())
    )


def probe(link_z=WORKING_LINK_Z):
    source_counts, source_screws = frame._fixed_screws()
    source_axes = {
        name: (tuple(wide.bounds(solid)), round(solid.Volume(), 8))
        for name, solid in source_screws.items()
    }
    spec = replace(ACTIVE_TRIAL, link_z=link_z)
    parts, bores, ends = build_center_geometry(spec)
    config = (
        BLOCK_BOTTOM_Z,
        POST_AXIS_Y,
        POST_CLEAT_Z,
        spec.vertical_x,
        spec.vertical_y,
    )
    with patch.object(prior, "POSE", replace(prior.POSE, top_z=HEADER_SIDE_TOP_Z)):
        fit = post._candidate(config, geometry=(parts, bores, ends))
    owners = placement._owners()
    inventory = placement.table((parts, bores, owners), spec.variant_id)
    _, screws = frame._fixed_screws()
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
    header = parts["base_header"]
    cleat = parts["header_side_cleat"]
    contact_area = wide.hit_volume(cleat.translate((0, 0, -0.01)), header) / 0.01
    header_bore = bores["header_cleat"]
    reception = {
        name: round(wide.hit_volume(header_bore, parts[name]) / header_bore.Volume(), 8)
        for name in ("base_header", "header_side_cleat")
    }
    result = {
        "variant_id": spec.variant_id,
        "source_fingerprint": (ACTIVE_FINGERPRINT if spec == ACTIVE_TRIAL else None),
        "side_bounds_mm": list(wide.bounds(parts["upright_side_cleat"])),
        "side_y_conditional_4d_plus_project_5_reserve_mm": round(
            min(UPRIGHT_Y - side.SIDE_REAR_Y, FRONT_Y - UPRIGHT_Y)
            - 4 * placement.DIAMETER_MM
            - placement.FABRICATION_ALLOWANCE_MM,
            5,
        ),
        "bore_count": len(bores),
        "inner_kicker_edges_supported": tolerance._fixed()[2][
            "inner_kicker_edges_supported"
        ],
        "bore_received_fraction": fit["bore_received_fraction"],
        "washer_bearing_fraction": fit["washer_bearing_fraction"],
        "clear_insertion_ends_by_bolt": fit["clear_insertion_ends_by_bolt"],
        "parent_nominal_geometry": fit["nominal_geometry"],
        "side_checks": side_checks,
        "full_center_collision_checks": fit["collision_checks"],
        "whole_center_classification_complete": False,
        "rating_or_drilling_release": False,
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
            "header_side_top_z": HEADER_SIDE_TOP_Z,
            "post_cleat_2_z": POST_CLEAT_2_Z,
            "post_high_z": spec.post_high_z,
            "vertical_x": spec.vertical_x,
            "vertical_y": spec.vertical_y,
            "cleat_link_z": link_z,
        },
        post_high_loaded_end_distance_mm=round(238.9 - spec.post_high_z, 5),
        post_high_conditional_3_5d_reserve_mm=round(
            238.9 - spec.post_high_z - 3.5 * placement.DIAMETER_MM, 5
        ),
        post_high_conditional_c_delta=round(
            min(1.0, (238.9 - spec.post_high_z) / (7 * placement.DIAMETER_MM)), 5
        ),
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
            POST_CLEAT_2_Z - POST_CLEAT_Z[0] - (4 * 6.35 + 5), 5
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
    result["integrated_nominal_cad_clear"] = _integrated_nominal_clear(result)
    return result


if __name__ == "__main__":
    print(
        json.dumps(
            {"working_z370": probe(), "rejected_z390": probe(COMPARISON_LINK_Z)},
            indent=2,
            sort_keys=True,
        )
    )
