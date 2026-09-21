import ast
from pathlib import Path

from scripts.simple_cross_dowel_continuation import screen


def test_nominal_geometry_passes_without_turning_missing_evidence_into_capacity():
    result = screen()
    geometry = result["whole_section_geometry"]
    assert geometry["all_sensitivity_poses_fit_nominal_body"]
    assert geometry["row_spacing_mm"] == 45.0
    assert geometry["minimum_row_center_to_section_edge_mm"] == 39.541
    assert geometry["row_centers_from_rail_n_min_mm"] == [55.159, 100.159]
    assert result["protected_panel_kicker_axis_count"] == 66
    assert not any(result["strength_mechanisms_supported"].values())
    assert not result["shaft_rating_used_as_joint_capacity"]
    assert result["decision"] == "PARK"
    assert result["reopening_trigger"]
    assert result["manufacturer_contacted"] is False
    assert result["blocks_corner_block_work"] is False
    assert result["fabrication_or_drilling_released"] is False


def test_continuation_matches_cd01_inputs_and_separates_hillman_sensitivity():
    result = screen()
    source = result["source_trial"]
    # Read source constants without importing CAD or rerunning its collision study.
    tree = ast.parse(
        (Path(__file__).resolve().parents[1] / source["script"]).read_text()
    )
    values = {}
    for node in tree.body:
        if isinstance(node, ast.Assign) and isinstance(
            node.value, (ast.Constant, ast.Tuple)
        ):
            values[node.targets[0].id] = ast.literal_eval(node.value)
    for field, constant in {
        "barrel_od_mm": "TRIAL_BARREL_OUTSIDE_DIAMETER_MM",
        "barrel_length_mm": "TRIAL_BARREL_LENGTH_MM",
        "thread_axis_from_barrel_end_mm": "TRIAL_THREAD_AXIS_FROM_BARREL_END_MM",
        "machine_bore_diameter_mm": "MACHINE_BOLT_TRIAL_BORE_DIAMETER_MM",
        "bolt_length_mm": "TRIAL_MACHINE_BOLT_LENGTH_MM",
    }.items():
        assert source[field] == values[constant]
    assert source["row_n_mm"] == list(values["ROW_N_MM"])
    assert source["pose"] == "recessed_centered_receiver_pair"
    assert source["barrel_recess_mm"] + source["barrel_length_mm"] == 27.05
    assert (
        source["barrel_recess_mm"] + source["thread_axis_from_barrel_end_mm"] == 19.05
    )
    centered = result["whole_section_geometry"]["poses"][1]
    assert centered["recess_mm"] == 11.049
    assert centered["cross_bore_depth_mm"] == 27.051
    assert centered["axis_offset_mm_not_hillman_specification"] == 8.001
    assert result["retail"]["complete_installed_cost_usd"] is None
