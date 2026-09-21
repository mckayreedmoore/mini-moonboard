"""One solid 4x6 side-cleat reserve trial for PB-02; nominal CAD only."""

import json
import sys
from pathlib import Path

import cadquery as cq

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts import simple_center_header_principal_probe as inherited
from scripts import simple_center_wide_post_probe as wide

# Rip an ordinary 4x6 cross section; the 145-mm length follows the grain.
BOUNDS = (-20.0, 50.95, -190.0, -45.0, 277.0, 380.0)
CLEAT = cq.Solid.makeBox(70.95, 145.0, 103.0, cq.Vector(-20, -190, 277))
VERTICAL = (15.475, -145.3)
CROSS = (-95.0, 330.0)
EDGE_4D = 25.4
RESERVE = 5.0


def _cylinder(radius, length, start, direction):
    return cq.Solid.makeCylinder(
        radius, length, cq.Vector(*start), cq.Vector(*direction)
    )


def _hits(shapes, targets):
    return {
        f"{name}/{target}": round(volume, 5)
        for name, shape in shapes.items()
        for target, solid in targets.items()
        if (volume := wide.hit_volume(shape, solid)) > wide.TOL
    }


def probe():
    """Check actual solid intersections, receivers, bores, and access envelopes."""
    inherited_pose = inherited.link.probe()
    parts = inherited._parts()
    parts["header_side_cleat"] = CLEAT
    counts, screws = inherited._fixed_screws()
    x, y = VERTICAL
    cross_y, cross_z = CROSS
    bores = {
        "header_cleat": _cylinder(wide.BORE_RADIUS, 141.1, (x, y, 238.9), (0, 0, 1)),
        "cleat_principal": _cylinder(
            wide.BORE_RADIUS, 109.05, (-20, cross_y, cross_z), (1, 0, 0)
        ),
    }
    intended = {
        "header_cleat": ("base_header", "header_side_cleat"),
        "cleat_principal": ("header_side_cleat", "base_principal_center_right"),
    }
    received = {
        name: round(
            sum(wide.hit_volume(bore, parts[wood]) for wood in intended[name])
            / bore.Volume(),
            8,
        )
        for name, bore in bores.items()
    }
    other_bores = {
        "post_low": _cylinder(wide.BORE_RADIUS, 127, (140, -213.8, 110), (0, 1, 0)),
        "post_high": _cylinder(wide.BORE_RADIUS, 127, (140, -213.8, 190), (0, 1, 0)),
        "upright": _cylinder(wide.BORE_RADIUS, 127, (50.95, -147.3, 350), (1, 0, 0)),
        "cleat_link": _cylinder(
            wide.BORE_RADIUS, 94.9, (133.5, -213.8, 370), (0, 1, 0)
        ),
    }
    washer_specs = {
        "header_bottom": ((x, y, 238.9), (0, 0, 1), "base_header"),
        "cleat_top": ((x, y, 380), (0, 0, -1), "header_side_cleat"),
        "cleat_left": ((-20, cross_y, cross_z), (1, 0, 0), "header_side_cleat"),
        "principal_right": (
            (89.05, cross_y, cross_z),
            (-1, 0, 0),
            "base_principal_center_right",
        ),
    }
    washers = {
        name: round(
            wide.hit_volume(_cylinder(10, 0.01, point, inward), parts[wood])
            / _cylinder(10, 0.01, point, inward).Volume(),
            8,
        )
        for name, (point, inward, wood) in washer_specs.items()
    }
    tools = {
        name: _cylinder(20, 20, point, tuple(-component for component in inward))
        for name, (point, inward, _) in washer_specs.items()
    }
    overlaps = _hits(
        {"cleat": CLEAT},
        {name: part for name, part in parts.items() if name != "header_side_cleat"},
    )
    fixed_hits = _hits({"cleat": CLEAT, **bores}, screws)
    unintended = {
        f"{name}/{wood}": round(volume, 5)
        for name, bore in bores.items()
        for wood, solid in parts.items()
        if wood not in intended[name]
        if (volume := wide.hit_volume(bore, solid)) > wide.TOL
    }
    bore_pairs = _hits(bores, other_bores)
    if (volume := wide.hit_volume(*bores.values())) > wide.TOL:
        bore_pairs["header_cleat/cleat_principal"] = round(volume, 5)
    principal_ray = _cylinder(0.01, 1000, (70, cross_y, 0), (0, 0, 1))
    principal_section = (
        parts["base_principal_center_right"].intersect(principal_ray).BoundingBox()
    )
    distances = {
        "vertical_cleat_x_transverse": [x - BOUNDS[0], BOUNDS[1] - x],
        "vertical_header_y_transverse": [y - (-175.7), -36 - y],
        "vertical_cleat_y_grain_ends": [y - BOUNDS[2], BOUNDS[3] - y],
        "cross_cleat_z_transverse": [cross_z - BOUNDS[4], BOUNDS[5] - cross_z],
        "cross_cleat_y_grain_ends": [cross_y - BOUNDS[2], BOUNDS[3] - cross_y],
        "cross_principal_rear_y_grain_offset": cross_y - (-182.7),
        "cross_principal_z_section_transverse": [
            cross_z - principal_section.zmin,
            principal_section.zmax - cross_z,
        ],
    }
    distances = {
        name: [round(v, 5) for v in values]
        if isinstance(values, list)
        else round(values, 5)
        for name, values in distances.items()
    }
    transverse = {
        name: values
        for name, values in distances.items()
        if name.endswith("_transverse")
    }
    minimum_reserve = round(
        min(v for values in transverse.values() for v in values) - EDGE_4D, 5
    )
    inherited_clear = (
        inherited_pose["fixed_axes"] == counts == {"panel": 48, "kicker": 18}
        and all(inherited_pose["inner_kicker_edges_supported"].values())
        and set(inherited_pose["center_kicker_screw_receiver_fraction"].values())
        == {1.0}
        and all(
            not inherited_pose[key]
            for key in (
                "solid_overlaps_mm3",
                "fixed_screw_hits_mm3",
                "bore_unintended_wood_hits_mm3",
                "bore_pair_hits_mm3",
                "trial_20mm_radius_tool_wood_hits_mm3",
            )
        )
    )
    tool_hits = _hits(tools, parts)
    accepted = (
        inherited_clear
        and minimum_reserve >= RESERVE
        and all(v == 1.0 for v in received.values())
        and all(v == 1.0 for v in washers.values())
        and not any((overlaps, fixed_hits, unintended, bore_pairs, tool_hits))
    )
    return {
        "station": "clip_split_base_center_right",
        "cleat_bounds_mm": BOUNDS,
        "cleat_grain_axis": "Y",
        "stock_blank_nominal_mm": [88.9, 139.7, 145.0],
        "stock_finished_nominal_mm": [70.95, 103.0, 145.0],
        "bolt_axes": {
            "header_cleat": [x, y, 238.9, 380],
            "cleat_principal": [-20, 89.05, cross_y, cross_z],
        },
        "nominal_bolt_diameter_mm": 6.35,
        "occupied_bore_diameter_mm": 2 * wide.BORE_RADIUS,
        "fixed_axes": counts,
        "inherited_pose_clear": inherited_clear,
        "inner_kicker_edges_supported": inherited_pose["inner_kicker_edges_supported"],
        "center_kicker_screw_receiver_fraction": inherited_pose[
            "center_kicker_screw_receiver_fraction"
        ],
        "new_wood_overlaps_mm3": overlaps,
        "bore_received_fraction": received,
        "fixed_screw_hits_mm3": fixed_hits,
        "unintended_bore_wood_hits_mm3": unintended,
        "bore_pair_hits_mm3": bore_pairs,
        "washer_bearing_fraction": washers,
        "tool_wood_hits_mm3": tool_hits,
        "tool_panel_kicker_hits_mm3": _hits(
            tools,
            {
                name: part
                for name, part in parts.items()
                if name.startswith(("panel_", "kicker_"))
            },
        ),
        "face_center_distances_mm": distances,
        "minimum_conditional_4d_transverse_reserve_mm": minimum_reserve,
        "header_bottom_tool_to_backer_y_gap_mm": round(-124.9 - (y + 20), 5),
        "nominal_geometry": "accepted" if accepted else "rejected",
        "fabrication_ready": False,
        "rating_or_drilling_release": False,
    }


if __name__ == "__main__":
    print(json.dumps(probe(), indent=2, sort_keys=True))
