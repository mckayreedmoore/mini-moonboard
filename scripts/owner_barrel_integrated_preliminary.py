"""Conditional components for two joints in the maintained barrel assembly.

No constituent number is a complete barrel-joint resistance or a load rating.
"""

import json
import math
from pathlib import Path

from mini_moonboard.bolted_timber_checks import (
    dfl_axial_wood_bearing_reference_lbf,
    dfl_dowel_bearing_psi,
    dfl_net_parallel_tension_reference_lbf,
)
from scripts.export_owner_barrel_scene import build_integrated_viewer_assembly
from scripts.owner_barrel_coordinates import local_bounds
from scripts.owner_barrel_installed_stack_audit import _cylinder, _row
from scripts.owner_barrel_mvp_preliminary import _joint as historical_two_row_components
from scripts.simple_owner_duty_ledger import selected_duties

ROOT = Path(__file__).resolve().parents[1]
MATERIAL = ROOT / "docs/bolted-candidate-material-basis.json"
RAIL = "clip_horizontal_lower_right_2"
CENTER = "clip_split_base_center_right"
MM_PER_IN = 25.4
N_PER_LBF = 4.4482216152605
STEEL_E_MPA_SENSITIVITY = 205_000.0
ROOT_DIAMETER_MM_SENSITIVITY = 0.189 * MM_PER_IN


def _center(assembly):
    names = [
        name for name, station in assembly["bolt_station"].items() if station == CENTER
    ]
    if len(names) != 1:
        raise ValueError("Current principal/header center must have one bolt")
    name = names[0]
    row = _row(assembly, name)
    _, _, washer_od, _ = _cylinder(assembly["stacks"][name]["washer"], name + "/washer")
    principal = assembly["wood"]["base_principal_center_right"]
    bounds = local_bounds(principal)
    report = assembly["diagnostics"]["producer_diagnostics"]["center6"][
        "revised_center"
    ]
    station_rows = report["stations"][CENTER]["bolts"]
    datum = station_rows[name.removesuffix("_bolt")]
    if (
        report["nominal_geometry_disposition"] != "CANDIDATE_ONLY_UNVERIFIED"
        or report["candidate_service_diameter_mm"] != 25.4
        or row["nominal_axial_flags"] != ["AXIS_REACHED_WITHIN_MODELED_BORE"]
        or any(assembly["release_flags"].values())
    ):
        raise ValueError("Integrated center geometry/release boundary changed")
    thickness = bounds["x"][1] - bounds["x"][0]
    width = bounds["n"][1] - bounds["n"][0]
    shaft_d = row["shaft_od_mm"]
    bore_d = row["machine_bore_od_mm"]
    barrel_d = row["barrel_body_od_mm"]
    reach = row["assumed_thread_axis_reach_mm"]
    washer_n = (
        dfl_axial_wood_bearing_reference_lbf(
            washer_od / MM_PER_IN, bore_d / MM_PER_IN, shaft_d / MM_PER_IN
        )
        * N_PER_LBF
    )
    # A full through-width slot is a component sensitivity, not the actual
    # blind-barrel section with neighboring service holes and local fracture.
    slot_n = (
        dfl_net_parallel_tension_reference_lbf(
            thickness / MM_PER_IN, width / MM_PER_IN, (barrel_d / MM_PER_IN,)
        )
        * N_PER_LBF
    )
    steel_k = (
        STEEL_E_MPA_SENSITIVITY * math.pi * ROOT_DIAMETER_MM_SENSITIVITY**2 / 4 / reach
    )
    return {
        "station": CENTER,
        "members": ["base_header", "base_principal_center_right"],
        "rows": [
            {
                "bolt": name,
                "nominal_length_mm": row["shaft_length_mm"],
                "seat_to_assumed_barrel_axis_mm": reach,
                "tip_past_barrel_far_wall_mm": row["tip_past_barrel_far_wall_mm"],
                "tip_to_modeled_bore_cap_mm": row["tip_to_bore_far_cap_clearance_mm"],
                "maximum_body_overlap_if_fully_threaded_mm": row[
                    "maximum_body_overlap_with_fully_threaded_shaft_mm"
                ],
                "thread_engagement": row["thread_engagement"],
            }
        ],
        "principal_section_x_n_mm": [round(thickness, 3), round(width, 3)],
        "barrel_body_ligament_to_nearest_x_edge_mm": datum[
            "barrel_radial_x_edge_ligament_mm"
        ],
        "head_pocket_edge_stock_mm": min(
            datum["head_pocket_header_bottom_margin_mm"],
            datum["head_pocket_header_top_margin_mm"],
        ),
        "barrel_recess_mm": datum["barrel_recess_mm"],
        "candidate_F1_G1_passage_diameter_mm": report["candidate_service_diameter_mm"],
        "conditional_wood": {
            "ideal_full_contact_washer_fc_perp_n": round(washer_n, 3),
            "one_full_slot_parallel_tension_sensitivity_n": round(slot_n, 3),
            "dfl_fe_parallel_psi_input_only": dfl_dowel_bearing_psi(
                shaft_d / MM_PER_IN, 0
            ),
            "dfl_fe_perpendicular_psi_input_only": dfl_dowel_bearing_psi(
                shaft_d / MM_PER_IN, 90
            ),
            "actual_cut_net_section_capacity_n": None,
            "barrel_bearing_breakout_splitting_n": None,
        },
        "stiffness": {
            "steel_only_ea_over_length_n_per_mm": round(steel_k, 3),
            "assumed_root_diameter_mm": round(ROOT_DIAMETER_MM_SENSITIVITY, 4),
            "complete_axial_or_lateral_joint_stiffness_n_per_mm": None,
        },
        "single_fastener_free_moment_resistance_nmm": None,
        "moment_transfer_note": "One axial fastener cannot by itself transmit a free couple; butt-face compression and connected-frame restraint must be established for opening/twist cases.",
        "actual_new_topology_demand_n": None,
        "complete_joint_capacity_n": None,
        "complete_joint_stiffness_n_per_mm": None,
    }


def report(assembly=None):
    """Read integrated viewer geometry and keep conditional quantities separate."""
    assembly = build_integrated_viewer_assembly() if assembly is None else assembly
    material = json.loads(MATERIAL.read_text())
    values = material["reference_values"]
    if (
        material["source"]["edition"] != "2024 NDS and 2024 NDS Supplement"
        or values["Ft_parallel"]["value"] != 575
        or values["Fc_perpendicular"]["value"] != 625
        or values["G"]["value"] != 0.5
        or assembly["post_placement"] != "integrated"
        or len(assembly["bolts"]) != 46
        or len(assembly["panel_connections"]) != 66
        or len(assembly["frame_connections"]) != 12
        or len(set(assembly["bolt_station"].values())) != 24
    ):
        raise ValueError("Current barrel assembly or material edition changed")
    rail = historical_two_row_components(assembly, selected_duties(), None, RAIL)
    rail.pop("historical_bracket_two_point_scale_only")
    rail["actual_new_topology_demand_n"] = None
    rail["complete_joint_stiffness_n_per_mm"] = None
    return {
        "schema": "owner_barrel_integrated_preliminary/v1",
        "geometry_source": "integrated_viewer_assembly",
        "material_source": "docs/bolted-candidate-material-basis.json",
        "edition": material["source"]["edition"],
        "modeled_barrel_pairs": len(assembly["bolts"]),
        "former_angle_duties": len(set(assembly["bolt_station"].values())),
        "fixed_panel_kicker_screws": len(assembly["panel_connections"]),
        "retained_frame_bolts": len(assembly["frame_connections"]),
        "joints": {
            "lower_outer_rail": rail,
            "center_principal_header": _center(assembly),
        },
        "missing": [
            "new-topology signed six-case forces and moments with contact/load sharing",
            "delivered bolt/barrel/washer geometry, grade, thread span and resistance",
            "center one-fastener moment path; header-pocket and principal breakout",
            "actual cut wood sections, grading, moisture, splitting and net section",
            "complete-joint slip/stiffness and repeated-demounting evidence",
        ],
        "native_solve": False,
        "drilling_released": False,
        "fabrication_released": False,
        "structural_released": False,
    }


if __name__ == "__main__":
    print(json.dumps(report(), indent=2))
