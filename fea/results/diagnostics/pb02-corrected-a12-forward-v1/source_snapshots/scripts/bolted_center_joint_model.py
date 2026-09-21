"""Nominal left-center AB205 topology for diagnostic preparation only."""

import math

from scripts.bolted_candidate_ab205_center_fit import (
    screen_center_fit,
    screen_opposed_center_fit,
)


def shared_center_joint(
    module, *, vertical_spring, steel_bolt_spring,
    wood_bearing_lateral_n_per_mm, flange_contact_n_per_mm
):
    """Replace two old clip paths with two rigid angles and two shared bolt bodies.

    Springs are caller-supplied provisional slip parameters, not product ratings.
    The header bolt is one body with two distributed lateral-only wood branches.
    """
    fit = screen_center_fit("short")
    row_y = (fit["reversible_4d_y_lower_mm"] + fit["reversible_4d_y_upper_mm"]) / 2
    opposed = screen_opposed_center_fit(row_y)
    if (opposed["unique_wood_bore_axes"] != 6
            or opposed["retained_axis_conflicts_for_six_unique_bores"]
            or opposed["nominal_angle_outer_envelope_intersecting_raw_wood_parts"]
            or any(abs(fraction-1) > 1e-5 for fraction in opposed["post_bore_full_section_fractions"])):
        raise ValueError("Nominal shared-header trial no longer fits the protected raw geometry")
    raw = {part.name: part.shape for part in module.uncut_wood_parts()}
    header = raw["base_header"].BoundingBox()
    principal = raw["base_principal_center_left"].BoundingBox()
    post = raw["base_post_center_left"].BoundingBox()
    x = principal.xmin
    top_z, bottom_z = header.zmax, header.zmin
    vertical = [offset * 25.4 for offset in fit["vertical_hole_offsets_from_bend_in"]]
    header_x = [
        x - offset * 25.4 for offset in fit["horizontal_hole_offsets_from_bend_in"]
    ]
    angles = [
        {
            "name": "diagnostic_ab205_upper_left",
            "wood_member": "base_principal_center_left",
            "vertical_points": [[x, row_y, top_z + dz] for dz in vertical],
            "header_points": [[hx, row_y, top_z] for hx in header_x],
            "contact_points": [[hx, row_y + side * 12., top_z]
                               for hx in header_x for side in (-1, 1)],
            "contact_inward_xyz": [0., 0., -1.],
        },
        {
            "name": "diagnostic_ab205_lower_left",
            "wood_member": "base_post_center_left",
            "vertical_points": [[x, row_y, post.zmax - dz] for dz in vertical],
            "header_points": [[hx, row_y, bottom_z] for hx in header_x],
            "contact_points": [[hx, row_y + side * 12., bottom_z]
                               for hx in header_x for side in (-1, 1)],
            "contact_inward_xyz": [0., 0., 1.],
        },
    ]
    bolts = [
        {
            "name": f"diagnostic_shared_header_left_{i}",
            "top_point": [hx, row_y, top_z],
            "wood_upper_point": [hx, row_y, top_z - (top_z - bottom_z) / 4],
            "wood_lower_point": [hx, row_y, bottom_z + (top_z - bottom_z) / 4],
            "bottom_point": [hx, row_y, bottom_z],
        }
        for i, hx in enumerate(header_x)
    ]
    for name, spring in (
        ("vertical", vertical_spring),
        ("steel_bolt", steel_bolt_spring),
    ):
        if not isinstance(spring, dict) or set(spring) != {
            "axial_n_per_mm",
            "lateral_n_per_mm",
        }:
            raise ValueError(f"{name} requires explicit axial/lateral spring values")
        if any(
            not isinstance(value, (float, int))
            or not math.isfinite(value)
            or value <= 0
            or value > 1e12
            for value in spring.values()
        ):
            raise ValueError(
                f"{name} spring values must be finite positive diagnostic inputs"
            )
    for name, value in (("wood bearing", wood_bearing_lateral_n_per_mm),
                        ("flange contact", flange_contact_n_per_mm)):
        if not isinstance(value, (float, int)) or not math.isfinite(value) or not 0 < value <= 1e12:
            raise ValueError(f"{name} requires finite positive diagnostic stiffness")
    return {
        "replaced_clips": [
            "clip_split_base_center_left",
            "clip_split_header_center_left",
        ],
        "angles": angles,
        "shared_header_bolts": bolts,
        "vertical_spring": vertical_spring,
        "steel_bolt_spring": steel_bolt_spring,
        "wood_bearing_lateral_n_per_mm": wood_bearing_lateral_n_per_mm,
        "flange_contact_n_per_mm": flange_contact_n_per_mm,
        "row_y_mm": row_y,
        "nominal_bolt_diameter_mm": 12.7,
        "model_limit": "Rigid nominal angles/bolt bodies; two bilateral lateral bore springs "
        "per axis and sampled unilateral flange compression. No resolved bore pressure, "
        "flange flexure, prying, bolt/wood yielding, clearance, preload, "
        "washers, resistance or installation qualification.",
    }
