"""Conditional DF-L member screens for the PB-01 quarter-inch trial pose.

These 2024 NDS Appendix E reference components are not a joint capacity,
load rating, demand comparison, or drilling instruction.
"""

import json
import math
from pathlib import Path

from mini_moonboard.bolted_timber_checks import (
    dfl_net_parallel_tension_reference_lbf,
    dfl_parallel_row_tear_out_reference_lbf,
)

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "docs/bolted-candidate-prototypes/simple_rail_joint_comparison.json"
POSE = "cleat_grain_n_4x6_group_quarter"
MM_PER_IN = 25.4


def _projection(point, axis):
    return sum(a * b for a, b in zip(point, axis, strict=True))


def screen() -> dict:
    """Calculate only conditional row/net-tension reference components."""
    data = json.loads(SOURCE.read_text())
    pose = data[POSE]
    if (
        data["physical_width"] != "kerf-right"
        or pose["status"] != "diagnostic_pose_only"
    ):
        raise ValueError("PB-01 quarter-inch pose identity changed")
    if pose["nominal_trial_bolt_diameter_mm_not_selected"] != 6.35:
        raise ValueError("PB-01 bolt nominal diameter changed")
    bore_mm = pose["diagnostic_wood_bore_diameter_mm_not_drill_instruction"]
    x_mm, t_mm, n_mm = pose["size_local_x_t_n_mm"]
    host_mm = 38.1
    if (
        not math.isclose(n_mm, 300.0)
        or not math.isclose(x_mm, 139.7)
        or not math.isclose(t_mm, 57.15)
    ):
        raise ValueError("PB-01 cleat stock or geometry changed")
    if not math.isclose(
        pose["trial_envelope_grips_mm_not_purchased_lengths"]["u1"],
        x_mm + host_mm + 5.0,
    ):
        raise ValueError("PB-01 upright trial grip changed")
    if not math.isclose(
        pose["trial_envelope_grips_mm_not_purchased_lengths"]["r1"],
        t_mm + host_mm + 5.0,
    ):
        raise ValueError("PB-01 rail trial grip changed")
    groups = pose["bolt_groups"]
    if any(len(groups[family]) != 2 for family in ("upright", "rail")):
        raise ValueError("PB-01 four-bolt count changed")
    angle = math.radians(50)
    tangent = (0.0, math.cos(angle), math.sin(angle))
    normal = (0.0, -math.sin(angle), math.cos(angle))
    upright_starts = [row["start_xyz_mm"] for row in groups["upright"]]
    rail_starts = [row["start_xyz_mm"] for row in groups["rail"]]
    if not math.isclose(
        _projection(upright_starts[0], tangent),
        _projection(upright_starts[1], tangent),
        abs_tol=1e-3,
    ):
        raise ValueError("Upright bolts no longer share a grain-T section")
    if not math.isclose(
        _projection(rail_starts[0], normal),
        _projection(rail_starts[1], normal),
        abs_tol=1e-3,
    ):
        raise ValueError("Rail bolts no longer share a cleat grain-N section")
    edges = pose["center_to_edges_and_spacing_mm"]
    if not math.isclose(sum(edges["upright_in_host_n"][0]), 139.7, abs_tol=1e-3):
        raise ValueError("Upright host net-section width changed")
    if not math.isclose(sum(edges["rail_in_host_n"]), 139.7, abs_tol=1e-3):
        raise ValueError("Rail host net-section width changed")
    bore_in = bore_mm / MM_PER_IN
    host_in, x_in, t_in = (value / MM_PER_IN for value in (host_mm, x_mm, t_mm))
    components = {
        "rail_host_row_toward_butt": dfl_parallel_row_tear_out_reference_lbf(
            host_in,
            2,
            edges["rail_in_host_x"][0][0] / MM_PER_IN,
            edges["rail_group_x_pitch"] / MM_PER_IN,
        ),
        "cleat_upright_row_toward_front": dfl_parallel_row_tear_out_reference_lbf(
            x_in,
            2,
            edges["upright_in_cleat_n"][0][0] / MM_PER_IN,
            edges["upright_group_n_pitch"] / MM_PER_IN,
        ),
        "upright_host_net_tension": dfl_net_parallel_tension_reference_lbf(
            host_in, x_in, (bore_in, bore_in)
        ),
        "rail_host_net_tension": dfl_net_parallel_tension_reference_lbf(
            host_in, x_in, (bore_in,)
        ),
        "cleat_rail_holes_net_tension": dfl_net_parallel_tension_reference_lbf(
            t_in, x_in, (bore_in, bore_in)
        ),
        "cleat_upright_hole_net_tension": dfl_net_parallel_tension_reference_lbf(
            x_in, t_in, (bore_in,)
        ),
    }
    return {
        "pose": POSE,
        "physical_width": "kerf-right",
        "bore_diameter_mm": bore_mm,
        "bolt_count_by_interface": {
            family: len(groups[family]) for family in ("upright", "rail")
        },
        "components_lbf": components,
        "conditions": "Dry solid DF-L No.2 Appendix E reference inputs; hypothetical parallel-grain tension/tear-out only; other holes, cuts, group effects and adjustment factors excluded",
        "conditional_only": True,
        "joint_capacity_lbf": None,
        "utilization": None,
        "drilling_released": False,
    }


if __name__ == "__main__":
    print(json.dumps(screen(), indent=2, sort_keys=True))
