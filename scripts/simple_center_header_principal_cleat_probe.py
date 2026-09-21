"""One PB-02 rectangular side-cleat through-bolt geometry trial; no release."""

import json
import sys
from pathlib import Path

import cadquery as cq

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts import simple_center_header_principal_probe as inherited
from scripts import simple_center_wide_post_probe as wide

CLEAT = cq.Solid.makeBox(50.95, 115.7, 103, cq.Vector(0, -175.7, 277))
VERTICAL_CENTER = (25.475, -150.0)
CROSS_CENTER = (-95.0, 330.0)
BORE_RADIUS = wide.BORE_RADIUS
WASHER_RADIUS = 10.0  # Illustration only; no hardware selected.
TOOL_RADIUS = 20.0


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
    """Screen two orthogonal bolts and their exposed washer/tool seats."""
    pose = inherited.link.probe()
    parts = inherited._parts()
    parts["header_side_cleat"] = CLEAT
    counts, screws = inherited._fixed_screws()
    x, y = VERTICAL_CENTER
    cross_y, cross_z = CROSS_CENTER
    bores = {
        "header_cleat": _cylinder(BORE_RADIUS, 141.1, (x, y, 238.9), (0, 0, 1)),
        "cleat_principal": _cylinder(
            BORE_RADIUS, 89.05, (0, cross_y, cross_z), (1, 0, 0)
        ),
    }
    intended = {
        "header_cleat": ("base_header", "header_side_cleat"),
        "cleat_principal": ("header_side_cleat", "base_principal_center_right"),
    }
    received = {
        name: round(
            sum(wide.hit_volume(bore, parts[owner]) for owner in intended[name])
            / bore.Volume(),
            8,
        )
        for name, bore in bores.items()
    }
    other_bores = {
        "post_low": _cylinder(BORE_RADIUS, 127, (140, -213.8, 110), (0, 1, 0)),
        "post_high": _cylinder(BORE_RADIUS, 127, (140, -213.8, 190), (0, 1, 0)),
        "upright": _cylinder(BORE_RADIUS, 127, (50.95, -147.3, 350), (1, 0, 0)),
        "cleat_link": _cylinder(BORE_RADIUS, 94.9, (133.5, -213.8, 370), (0, 1, 0)),
    }
    washer_specs = {
        "header_bottom": ((x, y, 238.9), (0, 0, 1), "base_header"),
        "cleat_top": ((x, y, 380), (0, 0, -1), "header_side_cleat"),
        "cleat_left": ((0, cross_y, cross_z), (1, 0, 0), "header_side_cleat"),
        "principal_right": (
            (89.05, cross_y, cross_z),
            (-1, 0, 0),
            "base_principal_center_right",
        ),
    }
    washers = {
        name: round(
            wide.hit_volume(_cylinder(WASHER_RADIUS, 0.01, point, inward), parts[owner])
            / _cylinder(WASHER_RADIUS, 0.01, point, inward).Volume(),
            8,
        )
        for name, (point, inward, owner) in washer_specs.items()
    }
    tools = {
        name: _cylinder(TOOL_RADIUS, 20, point, tuple(-v for v in inward))
        for name, (point, inward, _) in washer_specs.items()
    }
    tool_hits = _hits(tools, parts)
    panel_kicker = {
        name: shape
        for name, shape in parts.items()
        if name.startswith(("panel_", "kicker_"))
    }
    overlap = _hits(
        {"header_side_cleat": CLEAT},
        {k: v for k, v in parts.items() if k != "header_side_cleat"},
    )
    fixed_hits = _hits({"header_side_cleat": CLEAT, **bores}, screws)
    unintended = {
        f"{name}/{wood}": round(volume, 5)
        for name, bore in bores.items()
        for wood, solid in parts.items()
        if wood not in intended[name]
        if (volume := wide.hit_volume(bore, solid)) > wide.TOL
    }
    bore_pairs = _hits(bores, other_bores)
    crossing = wide.hit_volume(*bores.values())
    if crossing > wide.TOL:
        bore_pairs["header_cleat/cleat_principal"] = round(crossing, 5)
    clear = (
        pose["fixed_axes"] == counts == {"panel": 48, "kicker": 18}
        and all(pose["inner_kicker_edges_supported"].values())
        and set(pose["center_kicker_screw_receiver_fraction"].values()) == {1.0}
        and all(
            not pose[key]
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
        clear
        and all(value == 1.0 for value in received.values())
        and all(value == 1.0 for value in washers.values())
        and not any((overlap, fixed_hits, unintended, bore_pairs, tool_hits))
    )
    # ponytail: report only the stock faces that can govern these two axes.
    distances = {
        "vertical_cleat_x_edges": [x, 50.95 - x],
        "vertical_cleat_y_edges": [y + 175.7, -60 - y],
        "vertical_header_y_edges": [y + 175.7, -36 - y],
        "cross_cleat_y_edges": [cross_y + 175.7, -60 - cross_y],
        "cross_cleat_z_ends": [cross_z - 277, 380 - cross_z],
        "cross_principal_rear_y_offset": cross_y + 182.7,
    }
    distances = {
        name: [round(value, 5) for value in values]
        if isinstance(values, list)
        else round(values, 5)
        for name, values in distances.items()
    }
    return {
        "station": "clip_split_base_center_right",
        "pose": "simple_center_link_edge_probe",
        "cleat_bounds_mm": [0, 50.95, -175.7, -60, 277, 380],
        "bolt_axes": {
            "header_cleat": [x, y, 238.9, 380],
            "cleat_principal": [0, 89.05, cross_y, cross_z],
        },
        "nominal_bolt_diameter_mm": 6.35,
        "occupied_bore_diameter_mm": 2 * BORE_RADIUS,
        "fixed_axes": counts,
        "inherited_pose_clear": clear,
        "inner_kicker_edges_supported": pose["inner_kicker_edges_supported"],
        "center_kicker_screw_receiver_fraction": pose[
            "center_kicker_screw_receiver_fraction"
        ],
        "new_wood_overlaps_mm3": overlap,
        "bore_received_fraction": received,
        "fixed_screw_hits_mm3": fixed_hits,
        "unintended_bore_wood_hits_mm3": unintended,
        "bore_pair_hits_mm3": bore_pairs,
        "washer_bearing_fraction": washers,
        "tool_wood_hits_mm3": tool_hits,
        "tool_panel_kicker_hits_mm3": _hits(tools, panel_kicker),
        "face_center_distances_mm": distances,
        "conditional_nds_2024_4d_mm": 25.4,
        "conditional_nds_2024_1_5d_mm": 9.525,
        "conditional_nds_2024_softwood_tension_end_7d_mm": 44.45,
        "nominal_geometry": "accepted" if accepted else "rejected",
        "fabrication_ready": False,
        "strength_mechanism_gate": (
            "One bolt per interface and the vertical bolt into cleat end grain "
            "require a complete signed-load and connection-mechanism check."
        ),
        "rating_or_drilling_release": False,
        "old_proxy_forces_are_new_demand": False,
    }


if __name__ == "__main__":
    print(json.dumps(probe(), indent=2, sort_keys=True))
