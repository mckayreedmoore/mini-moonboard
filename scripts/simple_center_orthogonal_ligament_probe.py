"""Bounded PB02 orthogonal-bore screen; nominal geometry, no strength rating."""

import json
from itertools import combinations

from scripts import simple_center_combined_cleats_probe as combined
from scripts import simple_center_current_placement_table as placement
from scripts import simple_center_header_principal_probe as frame
from scripts import simple_center_wide_post_probe as wide

DIAMETER = 2 * wide.BORE_RADIUS
PAIRS = (("post_high", "post_cleat_2"), ("upright", "cleat_link"))


def _sample(post_upper_z, link_z, geometry):
    parts, bores, owners = geometry()
    bores["post_cleat_2"] = combined.cylinder(
        wide.BORE_RADIUS, 177.8, (88.75, -145, post_upper_z), (1, 0, 0)
    )
    bores["cleat_link"] = combined.cylinder(
        wide.BORE_RADIUS, 94.9, (133.5, -213.8, link_z), (0, 1, 0)
    )
    counts, screws = frame._fixed_screws()
    gaps = {
        f"{a}/{b}": round(
            placement._centerline_gap(
                bores[a], placement.AXES[a], bores[b], placement.AXES[b]
            ),
            5,
        )
        for a, b in PAIRS
    }
    receiver = {
        name: round(
            sum(wide.hit_volume(bore, parts[member]) for member in owners[name])
            / bore.Volume(),
            8,
        )
        for name, bore in bores.items()
    }
    unintended = {
        key: value
        for name, bore in bores.items()
        for key, value in combined.hits(
            {name: bore},
            {
                member: wood
                for member, wood in parts.items()
                if member not in owners[name]
            },
        ).items()
    }
    pair_hits = {
        f"{a}/{b}": round(volume, 5)
        for (a, left), (b, right) in combinations(bores.items(), 2)
        if (volume := wide.hit_volume(left, right)) > wide.TOL
    }
    screw_hits = combined.hits(bores, screws)
    # Moved exposed ends retain the same member faces and hardware envelope.
    ends = {
        "post_left": ((88.75, -145, post_upper_z), (-1, 0, 0), "shifted_right_post"),
        "post_right": (
            (266.55, -145, post_upper_z),
            (1, 0, 0),
            "header_post_side_cleat",
        ),
        "link_rear": ((133.5, -213.8, link_z), (0, -1, 0), "rear_cleat"),
        "link_front": ((133.5, -118.9, link_z), (0, 1, 0), "upright_side_cleat"),
    }
    washers, _, hardware, _ = combined.end_envelopes(ends, parts)
    # Hardware collision against wood and fixed screws is local to changed ends.
    hardware_wood = combined.hits(hardware, parts)
    hardware_screws = combined.hits(hardware, screws)
    return {
        "post_upper_z_mm": post_upper_z,
        "link_z_mm": link_z,
        "bore_count": len(bores),
        "fixed_axes": counts,
        "fixed_screw_axes_checked": len(screws),
        "centerline_gap_mm": gaps,
        "nominal_wood_ligament_mm": {
            key: round(value - DIAMETER, 5) for key, value in gaps.items()
        },
        "post_pair_pitch_mm": round(post_upper_z - 145, 5),
        "post_pair_pitch_reserve_with_5mm_mm": round(post_upper_z - 145 - 25.4 - 5, 5),
        "link_top_grain_end_mm": round(460 - link_z, 5),
        "receiver_fraction": receiver,
        "moved_washer_bearing_fraction": washers,
        "unintended_wood_hits_mm3": unintended,
        "bore_pair_hits_mm3": pair_hits,
        "fixed_screw_hits_mm3": screw_hits,
        "moved_hardware_wood_hits_mm3": hardware_wood,
        "moved_hardware_screw_hits_mm3": hardware_screws,
    }


def probe():
    samples = {
        "current": _sample(180, 370, placement.historical_geometry),
        "bounded_adjustment": _sample(176, 390, placement.historical_geometry),
    }
    return {
        "source_pose": "explicit pre-consolidation placement geometry",
        "wood_and_fixed_axis_geometry_unchanged": True,
        "samples": samples,
        "post_fixed_block_gap_cap_with_5mm_mm": round(
            190 - (95 + 44.45 + 5 + 25.4 + 5), 5
        ),
        "nominal_bore_diameter_mm": DIAMETER,
        "strength_or_nds_pass": False,
    }


if __name__ == "__main__":
    print(json.dumps(probe(), indent=2, sort_keys=True))
