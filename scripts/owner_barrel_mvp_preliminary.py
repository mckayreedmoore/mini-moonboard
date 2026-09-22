"""Two current-viewer barrel joints: conditional wood and stiffness arithmetic.

Historical bracket actions are scale examples, never barrel-joint demands.
No output is a complete connection resistance or release.
"""

import json
import math
from pathlib import Path

from mini_moonboard.bolted_timber_checks import (
    dfl_axial_wood_bearing_reference_lbf,
    dfl_dowel_bearing_psi,
    dfl_net_parallel_tension_reference_lbf,
)
from scripts.export_owner_barrel_scene import build_viewer_assembly
from scripts.owner_barrel_coordinates import N, local_bounds
from scripts.owner_barrel_installed_stack_audit import _cylinder, _row
from scripts.simple_owner_duty_ledger import selected_duties

ROOT = Path(__file__).resolve().parents[1]
STATIONS = {
    "outer_rail": "clip_horizontal_lower_right_2",
    "outer_header_post": "clip_timber_header_outer_right",
}
MM_PER_IN = 25.4
N_PER_LBF = 4.4482216152605
STEEL_E_MPA_SENSITIVITY = 205_000.0
ROOT_DIAMETER_MM_SENSITIVITY = 4.8006


def _historical_scale(station, spacing_mm, payload):
    """Same-case norm envelope for an ideal two-point pair, not a new force solve."""
    if payload["candidate"] != "compact-floor-flush-development":
        raise ValueError("Historical demand source changed")
    cases = []
    for case in payload["case_order"]:
        flange = payload["cases"][case]["angles"][station]["flanges"]["beam"]
        force = flange["force_norm_n"]
        moment = flange["moment_norm_nmm"]
        cases.append(
            {
                "case": case,
                "force_norm_n": force,
                "moment_norm_nmm": moment,
                "ideal_pair_one_row_n": force / 2 + moment / spacing_mm,
            }
        )
    return max(cases, key=lambda row: row["ideal_pair_one_row_n"])


def _joint(assembly, duties, historical, station):
    names = sorted(
        n for n, owner in assembly["bolt_station"].items() if owner == station
    )
    if len(names) != 2 or len(assembly["panel_connections"]) != 66:
        raise ValueError(f"{station}: expected active two-row assembly")
    rows = [_row(assembly, name) for name in names]
    centers = [assembly["barrels"][row["barrel_name"]].Center() for row in rows]
    spacing = (centers[1] - centers[0]).Length
    shaft_d = rows[0]["shaft_od_mm"]
    barrel_d = rows[0]["barrel_body_od_mm"]
    bore_d = rows[0]["machine_bore_od_mm"]
    washers = [
        _cylinder(assembly["stacks"][name]["washer"], name + "/washer")[2]
        for name in names
    ]
    if (
        any(abs(row["shaft_od_mm"] - shaft_d) > 1e-4 for row in rows)
        or any(abs(row["barrel_body_od_mm"] - barrel_d) > 1e-4 for row in rows)
        or any(abs(washer - washers[0]) > 1e-4 for washer in washers)
        or any(not row["head_present_in_assembly"] for row in rows)
        or any(not row["washer_present_in_assembly"] for row in rows)
    ):
        raise ValueError(f"{station}: diagnostic stack changed")

    member = duties[station]["timber"][0 if station == STATIONS["outer_rail"] else 1]
    if station == STATIONS["outer_rail"]:
        bounds = local_bounds(assembly["wood"][member])
        thickness = bounds["t"][1] - bounds["t"][0]
        width = bounds["n"][1] - bounds["n"][0]
        end_distance = bounds["x"][1] - centers[0].x
        edge_distance = min(
            min(
                point.y * N[0] + point.z * N[1] - bounds["n"][0],
                bounds["n"][1] - (point.y * N[0] + point.z * N[1]),
            )
            for point in centers
        )
        grain = "X along rail; bolt X is parallel to receiving-rail grain"
    else:
        bounds = assembly["wood"][member].BoundingBox()
        thickness = bounds.xlen
        width = bounds.ylen
        end_distance = bounds.zmax - centers[0].z
        edge_distance = min(
            min(point.y - bounds.ymin, bounds.ymax - point.y) for point in centers
        )
        grain = "Z along post; bolt Z is parallel to receiving-post grain"
    # ponytail: two full-through barrel-width slots are an isolated section
    # sensitivity; actual blind cuts and all neighboring openings remain open.
    net_lbf = dfl_net_parallel_tension_reference_lbf(
        thickness / MM_PER_IN, width / MM_PER_IN, (barrel_d / MM_PER_IN,) * 2
    )
    washer_lbf = dfl_axial_wood_bearing_reference_lbf(
        washers[0] / MM_PER_IN, bore_d / MM_PER_IN, shaft_d / MM_PER_IN
    )
    steel_only = {
        label: [
            STEEL_E_MPA_SENSITIVITY
            * math.pi
            * diameter**2
            / 4
            / row["assumed_thread_axis_reach_mm"]
            for row in rows
        ]
        for label, diameter in (
            ("nominal_body", shaft_d),
            ("typical_root_sensitivity", ROOT_DIAMETER_MM_SENSITIVITY),
        )
    }
    gamma = 180_000 * (shaft_d / MM_PER_IN) ** 1.5 * N_PER_LBF / MM_PER_IN
    return {
        "station": station,
        "members": duties[station]["timber"],
        "receiving_member": member,
        "receiving_grain_and_bolt_axis": grain,
        "row_spacing_mm": spacing,
        "barrel_center_to_grain_end_mm": end_distance,
        "barrel_body_ligament_to_grain_end_mm": end_distance - barrel_d / 2,
        "barrel_body_ligament_to_nearest_section_edge_mm": edge_distance - barrel_d / 2,
        "isolated_section_thickness_width_mm": [thickness, width],
        "shaft_diameter_mm": shaft_d,
        "machine_bore_diameter_mm": bore_d,
        "barrel_body_diameter_mm": barrel_d,
        "washer_outer_diameter_mm": washers[0],
        "rows": [
            {
                "bolt": row["bolt_name"],
                "axis_xyz_mm": row["barrel_body_center_xyz_mm"],
                "nominal_length_mm": row["shaft_length_mm"],
                "seat_to_assumed_axis_mm": row["assumed_thread_axis_reach_mm"],
                "tip_past_assumed_axis_mm": row["tip_past_assumed_axis_mm"],
                "tip_past_barrel_far_wall_mm": row["tip_past_barrel_far_wall_mm"],
                "tip_to_bore_cap_mm": row["tip_to_bore_far_cap_clearance_mm"],
            }
            for row in rows
        ],
        "conditional_wood": {
            "ideal_full_contact_washer_fc_perp_n_per_bolt": washer_lbf * N_PER_LBF,
            "two_slot_net_parallel_tension_reference_n": net_lbf * N_PER_LBF,
            "dfl_fe_parallel_psi_input_only": dfl_dowel_bearing_psi(
                shaft_d / MM_PER_IN, 0
            ),
            "dfl_fe_perpendicular_psi_input_only": dfl_dowel_bearing_psi(
                shaft_d / MM_PER_IN, 90
            ),
        },
        "stiffness": {
            "steel_only_ea_over_length_n_per_mm_each": steel_only,
            "ordinary_wood_wood_group_gamma_n_per_mm_each_comparator_only": gamma,
            "centered_7p5_vs_6p35_radial_clearance_mm": (bore_d - shaft_d) / 2,
            "complete_axial_or_lateral_joint_stiffness_n_per_mm": None,
        },
        "historical_bracket_two_point_scale_only": (
            _historical_scale(station, spacing, historical)
            if historical is not None
            else None
        ),
        "actual_barrel_joint_demand_n": None,
        "complete_joint_capacity_n": None,
        "pass": None,
    }


def report(assembly=None):
    """Read current outward-post viewer solids and preserve all open decisions."""
    assembly = build_viewer_assembly() if assembly is None else assembly
    if assembly["post_placement"] != "outward" or any(
        assembly["release_flags"].values()
    ):
        raise ValueError("Expected unreleased current outward-post assembly")
    material = json.loads(
        (ROOT / "docs/bolted-candidate-material-basis.json").read_text()
    )
    values = material["reference_values"]
    if (
        values["Ft_parallel"]["value"] != 575
        or values["Fc_perpendicular"]["value"] != 625
        or values["G"]["value"] != 0.5
    ):
        raise ValueError("2024 DF-L helper inputs differ from material record")
    historical = json.loads(
        (ROOT / "docs/floor-runner-mvp-angle-demands.json").read_text()
    )
    duties = selected_duties()
    joints = {
        key: _joint(assembly, duties, historical, station)
        for key, station in STATIONS.items()
    }
    return {
        "schema": "owner_barrel_mvp_preliminary/v1",
        "geometry_source": "scripts.export_owner_barrel_scene.build_viewer_assembly()",
        "material_source": "docs/bolted-candidate-material-basis.json",
        "conditional_dfl_no2_dry_unincised": material["reference_values"],
        "historical_source": "docs/floor-runner-mvp-angle-demands.json",
        "joints": joints,
        "interpretation": "Constituent references and steel-only/comparator stiffness only; no barrel/thread capacity, current demand, or joint pass.",
        "missing": [
            "new-topology signed same-case joint forces and moments, contact and group sharing",
            "delivered barrel axis, material, wall, thread proof, engagement and tests",
            "delivered bolt root, grade, thread span, bending and combined-action properties",
            "washer stiffness/contact, bore tolerances, wood condition, all cuts and splitting",
            "barrel wood bearing/breakout and assembly-cycle slip or test stiffness",
        ],
        "drilling_released": False,
        "fabrication_released": False,
        "structural_released": False,
    }


if __name__ == "__main__":
    print(json.dumps(report(), indent=2))
