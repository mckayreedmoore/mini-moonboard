"""PB03 representative-stack conditional resistance screen."""

import pytest

from scripts.simple_pb03_conditional_resistance import screen


@pytest.fixture(scope="module")
def result():
    return screen()


def test_screen_is_bound_to_four_representative_pb03_stations(result):
    assert result["schema"] == "simple_pb03_conditional_resistance/v1"
    assert result["source"] == {
        "adapter": "scripts/simple_pb03_native.py",
        "pb03_source_id": "pb03-lower-service-plus-upper-and-bottom-outer-v1",
        "modeled_bolt_diameter_mm": 6.35,
        "modeled_bore_diameter_mm": 7.5,
        "candidate_bolt_diameter_mm": 9.525,
        "candidate_fits_modeled_bore": False,
    }
    assert result["representative_stations"] == {
        "lower_inner": "clip_horizontal_lower_left_2",
        "lower_outer": "clip_horizontal_lower_left_1",
        "upper_outer": "clip_horizontal_upper_left_1",
        "bottom_outer": "clip_horizontal_bottom_left_1",
    }
    assert len(result["stacks"]) == 16
    assert {row["family"] for row in result["stacks"]} == {
        "lower_inner",
        "lower_outer",
        "upper_outer",
        "bottom_outer",
    }
    assert all(row["source_geometry_authenticated"] for row in result["stacks"])


def test_thread_root_is_used_conservatively_and_modes_remain_separate(result):
    rows = {row["name"]: row for row in result["stacks"]}
    rail = rows["pb03_left_rail_1"]
    outer = rows["pb03_lower_outer_left_upright_1"]
    inner = rows["pb03_left_upright_1"]

    assert rail["hardware_lead"]["model"] == "805606"
    assert rail["hardware_lead"]["thread_basis"] == "fully_threaded"
    assert outer["hardware_lead"]["model"] == "190231"
    assert outer["hardware_lead"]["thread_basis"] == (
        "unknown_transition_root_diameter_through_both_members"
    )
    assert inner["hardware_lead"]["model"] is None
    assert inner["hardware_lead"]["exact_product_selected"] is False

    for row in result["stacks"]:
        wood = row["wood_yield_bearing"]
        assert wood["effective_bearing_diameter_in"] == pytest.approx(0.298)
        assert wood["parallel_sensitivity"]["governing_mode"] == "IV"
        assert wood["parallel_sensitivity"]["reference_lateral_n"] == pytest.approx(
            1131.3802912
        )
        assert wood["perpendicular_sensitivity"]["governing_mode"] == "IV"
        assert wood["perpendicular_sensitivity"][
            "reference_lateral_n"
        ] == pytest.approx(774.4555758)
        assert row["bolt_steel"]["threaded_tension_asd_reference_n"] == pytest.approx(
            7756.5864416
        )
        assert row["bolt_steel"]["threaded_single_shear_asd_reference_n"] == (
            pytest.approx(4653.9518650)
        )
        assert row["washer_bearing"]["one_inch_od_sensitivity_n"] == pytest.approx(
            1823.1502987
        )
        assert row["bolt_steel"]["long_grip_adjustment_qualified"] is False
        assert row["washer_bearing"]["actual_washer_qualified"] is False


def test_no_serial_capacity_or_joint_verdict_is_invented(result):
    assert result["governing_conditional_component"] == {
        "mechanism": "2024 NDS single-bolt lateral yield Mode IV",
        "case": "both_members_90_degrees_to_grain",
        "reference_n": pytest.approx(774.4555758),
    }
    assert "complete_joint_capacity_n" not in result
    assert "demand_ratio" not in result
    assert result["unsupported_mechanisms"]
    assert result["exact_unresolved_gates"]
    assert any(
        "7.5 mm" in gate and "9.525 mm" in gate
        for gate in result["exact_unresolved_gates"]
    )
    assert any("same-case" in gate for gate in result["exact_unresolved_gates"])
    assert all(
        row["group_row_effects"]["qualified"] is False for row in result["stacks"]
    )
    assert result["qualified_for_design"] is False
    assert result["drilling_released"] is False
    assert result["fabrication_released"] is False
    assert result["structural_released"] is False
