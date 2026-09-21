"""Analytical grain-normal sections of the maintained PB01 quarter_short pose."""

import json
import math

from scripts.simple_rail_joint_comparison import PB01_GROUP_TRIAL_SIZE_MM, N, T, compare

POSE = "cleat_grain_n_4x6_group_quarter"


def _section(rectangles, width, depth, bore_names, station):
    """Centroidal second moments of disjoint retained X/T rectangles."""
    parts = [(b - a, d - c, (a + b) / 2, (c + d) / 2) for a, b, c, d in rectangles]
    area = sum(w * h for w, h, _, _ in parts)
    cx = sum(w * h * x for w, h, x, _ in parts) / area
    ct = sum(w * h * t for w, h, _, t in parts) / area
    ix = sum(w * h**3 / 12 + w * h * (t - ct) ** 2 for w, h, _, t in parts)
    it = sum(h * w**3 / 12 + w * h * (x - cx) ** 2 for w, h, x, _ in parts)
    # Every retained rectangle spans the complete X or T dimension, so Ixt=0.
    return {
        "n_mm": station,
        "bore_names": bore_names,
        "removed_area_mm2": width * depth - area,
        "net_area_mm2": area,
        "retained_fraction": area / (width * depth),
        "centroid_x_t_mm": [cx, ct],
        "second_moments_about_x_t_mm4": [ix, it],
        "product_second_moment_mm4": 0.0,
        "principal_second_moments_mm4": sorted((ix, it)),
    }


def screen():
    """Use one maintained CAD pose; evaluate only its three bore-center cuts."""
    source = compare(quarter_n_length=PB01_GROUP_TRIAL_SIZE_MM[2])
    pose = source[POSE]
    width, depth, length = pose["size_local_x_t_n_mm"]
    diameter = pose["diagnostic_wood_bore_diameter_mm_not_drill_instruction"]
    front = pose["adjusted_front_n_mm"]
    if (
        source["station"] != "clip_horizontal_lower_right_1"
        or source["physical_width"] != "kerf-right"
        or source["fixed_panel_axes"] != 66
        or pose["fixed_panel_axes_checked"] != 66
        or pose["status"] != "diagnostic_pose_only"
        or pose["grain_axis"] != "N"
        or [width, depth, length] != list(PB01_GROUP_TRIAL_SIZE_MM)
        or diameter != 7.5
    ):
        raise ValueError("PB01 quarter_short source pose changed")
    bores = {
        bore["name"]: (family, bore)
        for family in ("upright", "rail")
        for bore in pose["bolt_groups"][family]
    }
    if (
        set(bores) != {"u1", "u2", "r1", "r2"}
        or sum(len(pose["bolt_groups"][family]) for family in ("upright", "rail")) != 4
    ):
        raise ValueError("PB01 four-bore inventory changed")
    centers = dict(zip(("u1", "u2"), pose["upright_bolt_n_centers_mm"], strict=True))
    centers.update(zip(("r1", "r2"), pose["rail_bolt_n_centers_mm"], strict=True))
    for name, (family, bore) in bores.items():
        axis = bore["axis_xyz"]
        expected_axis = (1, 0, 0) if family == "upright" else (0, *T)
        station = sum(a * b for a, b in zip(bore["start_xyz_mm"], (0, *N)))
        if (
            not all(
                math.isclose(a, b, abs_tol=1e-6) for a, b in zip(axis, expected_axis)
            )
            or not math.isclose(station, centers[name], abs_tol=0.002)
            or bore["clearance_diameter_mm_trial_not_shop_instruction"] != diameter
            or bore["full_bore_containment"].get("cleat") is not True
        ):
            raise ValueError(f"PB01 source bore changed: {name}")
    if (
        centers != {"u1": 265.0, "u2": 310.0, "r1": 290.0, "r2": 290.0}
        or pose["rail_bolt_x_from_butt_mm"] != [70.0, 110.0]
        or not math.isclose(
            bores["r2"][1]["start_xyz_mm"][0] - bores["r1"][1]["start_xyz_mm"][0],
            40.0,
            abs_tol=0.002,
        )
        or pose["center_to_edges_and_spacing_mm"]["upright_in_cleat_t"]
        != [depth / 2, depth / 2]
        or not front < min(centers.values()) <= max(centers.values()) < front + length
    ):
        raise ValueError("PB01 bore placement changed")
    radius = diameter / 2
    rail_x = pose["rail_bolt_x_from_butt_mm"]
    if (
        not (
            0
            < rail_x[0] - radius
            < rail_x[0] + radius
            < rail_x[1] - radius
            < rail_x[1] + radius
            < width
        )
        or diameter >= depth
    ):
        raise ValueError("PB01 retained rectangles invalid")
    upright_rectangles = [
        (0, width, 0, depth / 2 - radius),
        (0, width, depth / 2 + radius, depth),
    ]
    rail_rectangles = [
        (0, rail_x[0] - radius, 0, depth),
        (rail_x[0] + radius, rail_x[1] - radius, 0, depth),
        (rail_x[1] + radius, width, 0, depth),
    ]
    sections = [
        _section(upright_rectangles, width, depth, ["u1"], centers["u1"]),
        _section(rail_rectangles, width, depth, ["r1", "r2"], centers["r1"]),
        _section(upright_rectangles, width, depth, ["u2"], centers["u2"]),
    ]
    return {
        "variant": "quarter_short",
        "source": "maintained simple_rail_joint_comparison.compare pose",
        "fixed_panel_axes": source["fixed_panel_axes"],
        "bore_names": ["u1", "u2", "r1", "r2"],
        "size_x_t_n_mm": [width, depth, length],
        "front_n_mm": front,
        "diameter_mm_diagnostic_only": diameter,
        "grain_normal_planes_n_mm": [row["n_mm"] for row in sections],
        "gross_area_mm2": width * depth,
        "sections": sections,
        "minimum_net_area_mm2": min(row["net_area_mm2"] for row in sections),
        "material_strength_assessed": False,
        "wall_tearout_splitting_assessed": False,
        "capacity_n": None,
        "drilling_released": False,
    }


if __name__ == "__main__":
    print(json.dumps(screen(), indent=2, sort_keys=True))
