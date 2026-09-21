"""One relocated inherited upright bolt in the committed combined cleat pose."""

import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts import simple_center_combined_cleats_probe as combined
from scripts import simple_center_header_principal_probe as frame
from scripts import simple_center_link_edge_probe as link
from scripts import simple_center_wide_post_probe as wide

# Near the side cleat's forward washer limit; Z=400 is tangent to the
# header/principal cleat's Z=380 top for a 20-mm-radius straight tool.
UPRIGHT_Y = -129.0
UPRIGHT_Z = 400.0
OLD_Y = -147.3
OLD_Z = 350.0
UPRIGHT_LEFT_X = 50.95
UPRIGHT_RIGHT_X = 177.95
DIAMETER = 6.35
FOUR_D = 4 * DIAMETER
SEVEN_D = 7 * DIAMETER


def _fraction(shape, wood):
    return round(wide.hit_volume(shape, wood) / shape.Volume(), 8)


def _pair_hits(shapes):
    items = list(shapes.items())
    return {
        f"{name}/{other}": round(volume, 5)
        for i, (name, shape) in enumerate(items)
        for other, second in items[i + 1 :]
        if (volume := wide.hit_volume(shape, second)) > wide.TOL
    }


def _receiver_fractions(parts, screws):
    """Check every fixed screw's exposed shaft in its named wood receiver."""
    result = {}
    with wide.AXES.open(newline="") as handle:
        for row in csv.DictReader(handle):
            name = row["name"]
            if name not in screws:
                continue
            first = row["first_member"]
            second = row["second_member"]
            if second == "base_post_center_right":
                second = "backer"
            exposed = screws[name].cut(parts[first])
            result[name] = _fraction(exposed, parts[second])
    return result


def probe():
    parts = frame._parts() | combined.NEW_WOOD
    counts, screws = frame._fixed_screws()
    baseline = link.probe()
    new_bores = combined.new_bores()
    inherited_bores = combined.inherited_bores()
    inherited_bores["upright"] = combined.cylinder(
        wide.BORE_RADIUS,
        UPRIGHT_RIGHT_X - UPRIGHT_LEFT_X,
        (UPRIGHT_LEFT_X, UPRIGHT_Y, UPRIGHT_Z),
        (1, 0, 0),
    )
    inherited_ends = combined.INHERITED_ENDS | {
        "upright_left": (
            (UPRIGHT_LEFT_X, UPRIGHT_Y, UPRIGHT_Z),
            (-1, 0, 0),
            "base_principal_center_right",
        ),
        "upright_right": (
            (UPRIGHT_RIGHT_X, UPRIGHT_Y, UPRIGHT_Z),
            (1, 0, 0),
            "upright_side_cleat",
        ),
    }
    new_washers, new_seats, new_hardware, new_tools = combined.end_envelopes(
        combined.NEW_ENDS, parts
    )
    old_washers, old_seats, old_hardware, old_tools = combined.end_envelopes(
        inherited_ends, parts
    )
    bores = new_bores | inherited_bores
    intended = combined.INTENDED | {
        "post_low": ("rear_cleat", "shifted_right_post"),
        "post_high": ("rear_cleat", "shifted_right_post"),
        "upright": ("base_principal_center_right", "upright_side_cleat"),
        "cleat_link": ("rear_cleat", "upright_side_cleat"),
    }
    reception = {
        name: round(
            sum(wide.hit_volume(bore, parts[wood]) for wood in intended[name])
            / bore.Volume(),
            8,
        )
        for name, bore in bores.items()
    }
    unintended = {
        name: combined.hits(
            {name: bore},
            {
                wood: solid
                for wood, solid in parts.items()
                if wood not in intended[name]
            },
        )
        for name, bore in bores.items()
    }
    receiver_fractions = _receiver_fractions(parts, screws)
    # Confirm the moved X-axis occupies both named woods, including the sloped
    # principal intersection; it is not a point-centerline reception test.
    upright_segments = {
        wood: _fraction(inherited_bores["upright"], parts[wood])
        for wood in intended["upright"]
    }
    side = wide.bounds(parts["upright_side_cleat"])
    # Side cleat grain Z: Y are transverse edges, Z are grain ends. The
    # principal's inclined grain/top is reported separately below.
    distances = {
        "side_y_transverse_mm": [
            round(UPRIGHT_Y - side[2], 5),
            round(side[3] - UPRIGHT_Y, 5),
        ],
        "side_z_grain_ends_mm": [
            round(UPRIGHT_Z - side[4], 5),
            round(side[5] - UPRIGHT_Z, 5),
        ],
        "principal_rear_y_offset_mm": round(UPRIGHT_Y - (-182.7), 5),
        "side_link_z_row_spacing_mm": round(abs(UPRIGHT_Z - 370), 5),
        "side_link_y_row_spacing_mm": round(abs(UPRIGHT_Y - (-147.3)), 5),
    }
    checks = {
        "wood_overlaps_mm3": combined.hits(
            combined.NEW_WOOD,
            {k: v for k, v in parts.items() if k not in combined.NEW_WOOD},
        )
        | combined.hits(
            {"header_side_cleat": combined.NEW_WOOD["header_side_cleat"]},
            {"header_post_side_cleat": combined.NEW_WOOD["header_post_side_cleat"]},
        ),
        "bore_unintended_wood_hits_mm3": {
            k: v for hits in unintended.values() for k, v in hits.items()
        },
        "bore_pair_hits_mm3": _pair_hits(bores),
        "wood_screw_hits_mm3": combined.hits(combined.NEW_WOOD, screws),
        "bore_screw_hits_mm3": combined.hits(bores, screws),
        "hardware_wood_hits_mm3": combined.hits(new_hardware | old_hardware, parts),
        "washer_face_wood_hits_mm3": combined.hits(new_seats | old_seats, parts),
        "tool_wood_hits_mm3": combined.hits(new_tools | old_tools, parts),
        "hardware_screw_hits_mm3": combined.hits(new_hardware | old_hardware, screws),
        "washer_face_screw_hits_mm3": combined.hits(new_seats | old_seats, screws),
        "tool_screw_hits_mm3": combined.hits(new_tools | old_tools, screws),
        "hardware_hardware_hits_mm3": _pair_hits(new_hardware | old_hardware),
        "bore_hardware_hits_mm3": combined.hits(bores, new_hardware | old_hardware),
        "bore_tool_hits_mm3": combined.hits(bores, new_tools | old_tools),
        "washer_face_hardware_hits_mm3": combined.hits(
            new_seats | old_seats, new_hardware | old_hardware
        ),
        "tool_hardware_hits_mm3": combined.hits(
            new_tools | old_tools, new_hardware | old_hardware
        ),
    }
    # A bore meets its own end disks; a tool and washer seat share their own
    # coaxial hardware. Keep only cross-end intersections in these screens.
    for key in (
        "bore_hardware_hits_mm3",
        "bore_tool_hits_mm3",
        "washer_face_hardware_hits_mm3",
        "tool_hardware_hits_mm3",
    ):
        checks[key] = {
            pair: value
            for pair, value in checks[key].items()
            if pair.split("/")[0] != pair.split("/")[1]
            and not (
                pair.startswith("upright/")
                and pair.split("/")[1].startswith("upright_")
            )
        }
    inherited_baseline_clear = (
        baseline["fixed_axes"] == counts == {"panel": 48, "kicker": 18}
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
    )
    accepted = (
        inherited_baseline_clear
        and len(screws) == len(receiver_fractions) == 66
        and all(baseline["inner_kicker_edges_supported"].values())
        and all(v == 1 for v in reception.values())
        and all(v == 1 for v in new_washers.values())
        and all(v == 1 for v in old_washers.values())
        and all(v == 1 for v in receiver_fractions.values())
        and all(not item for item in checks.values())
        and min(distances["side_y_transverse_mm"]) >= FOUR_D
    )
    return {
        "pose": "committed combined cleats; one relocated inherited upright through-bolt",
        "old_upright_axis_yz_mm": [OLD_Y, OLD_Z],
        "trial_upright_axis_yz_mm": [UPRIGHT_Y, UPRIGHT_Z],
        "upright_x_span_mm": [UPRIGHT_LEFT_X, UPRIGHT_RIGHT_X],
        "old_bore_present_in_candidate": False,
        "fixed_axes": counts,
        "fixed_screw_axes_checked": len(screws),
        "fixed_screw_receiver_fraction": receiver_fractions,
        "inner_kicker_edges_supported": baseline["inner_kicker_edges_supported"],
        "inherited_baseline_clear": inherited_baseline_clear,
        "bore_received_fraction": reception,
        "upright_member_bore_fraction": upright_segments,
        "washer_bearing_fraction": new_washers | old_washers,
        "conditional_nds_distances": distances,
        "conditional_nds_markers_mm": {
            "reversible_loaded_edge_4d": FOUR_D,
            "tension_end_7d": SEVEN_D,
        },
        **checks,
        "nominal_geometry": "accepted" if accepted else "rejected",
        "stack_strength_or_drilling_release": False,
    }


if __name__ == "__main__":
    print(json.dumps(probe(), indent=2, sort_keys=True))
