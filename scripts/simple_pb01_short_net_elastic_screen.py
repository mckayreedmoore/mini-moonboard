"""Far-field elastic normal stress at six-inch PB01 diagnostic bore cuts."""

import json
import math

from scripts.simple_pb01_short_bored_section_probe import screen as bored_sections
from scripts.simple_pb01_short_tension_component_comparison import RUNS, read_case

MEMBER = "base_cleat_pb01"


def elastic_corners(section, net, *, width, depth):
    """Recenter one axial/biaxial wrench and evaluate a linear normal field.

    Local (u,v,w) is right-handed, with w along the member grain. This is a
    far-field beam idealization, not near-bore stress concentration or strength.
    """
    area = float(net["net_area_mm2"])
    center_u, center_v = map(float, net["centroid_x_t_mm"])
    iu, iv = map(float, net["second_moments_about_x_t_mm4"])
    n = float(section["axial_n_tension_positive"])
    mu = float(section["moment_u_nmm"])
    mv = float(section["moment_v_nmm"])
    if (
        min(area, iu, iv, width, depth) <= 0
        or net["product_second_moment_mm4"] != 0
        or not all(
            math.isfinite(v) for v in (area, center_u, center_v, iu, iv, n, mu, mv)
        )
    ):
        raise ValueError("Invalid net elastic section")
    # M about the net centroid = M about gross center - delta_r x (N w).
    mu_net = mu - (center_v - depth / 2) * n
    mv_net = mv + (center_u - width / 2) * n
    corners = {
        f"x{x:g}_t{t:g}": n / area
        + mu_net * (t - center_v) / iu
        - mv_net * (x - center_u) / iv
        for x in (0.0, width)
        for t in (0.0, depth)
    }
    return {
        "net_centroid_moment_u_nmm": mu_net,
        "net_centroid_moment_v_nmm": mv_net,
        "corner_normal_mpa": corners,
        "max_normal_tension_mpa": max(0.0, *corners.values()),
        "max_normal_compression_mpa": max(0.0, *(-v for v in corners.values())),
    }


def _case(case, path, net):
    report, _ = read_case(case, path)
    demand = report["member_section_demands"][MEMBER]
    member = demand["member"]
    width, depth, length = net["size_x_t_n_mm"]
    start = net["pose_member_centerline_start_xyz_mm"]
    axis = net["pose_member_grain_axis_xyz"]
    end = [a + length * b for a, b in zip(start, axis, strict=True)]
    vectors = (
        (member["start"], start),
        (member["end"], end),
        (member["axis"], axis),
        (member["section_u"], net["pose_member_section_u_xyz"]),
        (member["section_v"], net["pose_member_section_v_xyz"]),
    )
    if (
        member["name"] != MEMBER
        or member["qualified_for_design"] is not False
        or not math.isclose(demand["length_mm"], length, abs_tol=1e-6)
        or not math.isclose(member["width_mm"], width, abs_tol=1e-6)
        or not math.isclose(member["depth_mm"], depth, abs_tol=1e-6)
        or member["retained_area_fraction"] != 1.0
        or any(
            len(actual) != 3
            or any(
                not math.isclose(a, b, abs_tol=0.003)
                for a, b in zip(actual, expected, strict=True)
            )
            for actual, expected in vectors
        )
    ):
        raise ValueError("Retained section is not the modeled short block")
    selected = []
    for cut in net["sections"]:
        station = cut["n_mm"] - net["front_n_mm"]
        rows = [
            row
            for row in demand["sections"]
            if abs(row["station_along_grain_mm"] - station) <= 0.003
        ]
        if len(rows) != 2 or {row["include_station_loads"] for row in rows} != {
            False,
            True,
        }:
            raise ValueError("Bore-center cut-side inventory changed")
        for row in rows:
            selected.append(
                {
                    "n_mm": cut["n_mm"],
                    "bores": cut["bore_names"],
                    "include_station_loads": row["include_station_loads"],
                    "axial_n": row["axial_n_tension_positive"],
                    "gross_centroid_moment_u_nmm": row["moment_u_nmm"],
                    "gross_centroid_moment_v_nmm": row["moment_v_nmm"],
                    "net_area_mm2": cut["net_area_mm2"],
                    **elastic_corners(row, cut, width=width, depth=depth),
                }
            )
    return {
        "bore_center_cut_sides": selected,
        "max_normal_tension_mpa": max(
            row["max_normal_tension_mpa"] for row in selected
        ),
        "max_normal_compression_mpa": max(
            row["max_normal_compression_mpa"] for row in selected
        ),
        "legacy_connector_proxy_count": 23,
    }


def screen():
    """Pair source-verified hybrid actions with diagnostic net geometry only."""
    net = bored_sections()
    return {
        "variant": net["variant"],
        "diagnostic_bore_diameter_mm_not_drill_size": net[
            "diameter_mm_diagnostic_only"
        ],
        "fixed_panel_axes": net["fixed_panel_axes"],
        "cases": {case: _case(case, path, net) for case, path in RUNS.items()},
        "method": "linear axial plus biaxial bending normal field after net-centroid wrench shift; separate before/after load cut sides",
        "local_hole_stress_or_splitting_checked": False,
        "torsion_or_shear_stress_checked": False,
        "adjusted_wood_resistance_checked": False,
        "full_v4_joint_demands": False,
        "complete_joint_utilization": None,
        "rating_or_drilling_release": False,
    }


if __name__ == "__main__":
    print(json.dumps(screen(), indent=2, sort_keys=True))
