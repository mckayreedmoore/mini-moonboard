"""Gross elastic section components for both retained six-inch PB01 cases."""

import json
import math

from scripts.simple_pb01_cleat_gross_section_screen import (
    DEPTH_MM,
    WIDTH_MM,
    _maximum,
    finite_number,
    stress_components,
)
from scripts.simple_pb01_short_tension_component_comparison import RUNS, read_case

LENGTH_MM = 152.4
MEMBER = "base_cleat_pb01"


def _case(case, path):
    report, _ = read_case(case, path)
    demand = report["member_section_demands"][MEMBER]
    member = demand["member"]
    if member["name"] != MEMBER or member["qualified_for_design"] is not False:
        raise ValueError("Unexpected short-block section authority")
    expected = {
        "length_mm": (demand["length_mm"], LENGTH_MM),
        "gross_width_mm": (member["gross_width_mm"], WIDTH_MM),
        "gross_depth_mm": (member["gross_depth_mm"], DEPTH_MM),
        "width_mm": (member["width_mm"], WIDTH_MM),
        "depth_mm": (member["depth_mm"], DEPTH_MM),
        "area_mm2": (member["area_mm2"], WIDTH_MM * DEPTH_MM),
        "retained_area_fraction": (member["retained_area_fraction"], 1.0),
    }
    for label, (value, target) in expected.items():
        if not math.isclose(finite_number(value, label), target, abs_tol=1e-6):
            raise ValueError(f"Short-block {label} changed")
    if report["diagnostic_scope"]["old_ml24z_sds_proxy_stations"] != 23:
        raise ValueError("Short-block diagnostic scope changed")
    rows = [stress_components(row, WIDTH_MM, DEPTH_MM) for row in demand["sections"]]
    if len(rows) != 20 or any(
        not -1e-6 <= row["station_along_grain_mm"] <= LENGTH_MM + 1e-6 for row in rows
    ):
        raise ValueError("Short-block section inventory changed")
    signed_fields = (
        "axial_mpa",
        "bending_u_mpa",
        "bending_v_mpa",
        "shear_u_peak_mpa",
        "shear_v_peak_mpa",
    )
    positive_fields = (
        "normal_tension_corner_mpa",
        "normal_compression_corner_mpa",
        "transverse_shear_center_mpa",
    )
    maxima = {
        **{f"{field}_abs": _maximum(rows, field) for field in signed_fields},
        **{field: _maximum(rows, field) for field in positive_fields},
        "torsion_abs_nmm": _maximum(rows, "torsion_nmm"),
    }
    return {
        "length_mm": LENGTH_MM,
        "gross_area_mm2": WIDTH_MM * DEPTH_MM,
        "sections": rows,
        "maxima": maxima,
        "archive_numerically_accepted": report["numerically_accepted"],
        "legacy_connector_proxy_count": 23,
    }


def screen():
    """Return component stresses, not adjusted strength or a V4 joint verdict."""
    return {
        "member": MEMBER,
        "geometry_mm": {"width_u": WIDTH_MM, "depth_v": DEPTH_MM, "length": LENGTH_MM},
        "cases": {case: _case(case, path) for case, path in RUNS.items()},
        "same_topology_full_v4_demand": False,
        "net_section_stress_mpa": None,
        "torsional_stress_mpa": None,
        "complete_joint_utilization": None,
        "rating_or_drilling_release": False,
        "limits": [
            "Two source-verified hybrid diagnostics retain 23 legacy connector proxies; neither is final V4 demand.",
            "Gross unbored rectangle only; bolt-bore net sections, local fracture and splitting are not checked.",
            "Torsion is reported as a moment but no torsional stress or interaction is calculated.",
            "Corner normal and center transverse shear are isolated elastic components without adjusted material values.",
        ],
    }


if __name__ == "__main__":
    print(json.dumps(screen(), indent=2, sort_keys=True))
