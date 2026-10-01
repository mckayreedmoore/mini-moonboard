"""Meaningful checks for the pinned upper-block lateral replay."""

from __future__ import annotations

import importlib.util
import json
import math
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location("upper_block_lateral", HERE / "lateral.py")
assert SPEC is not None and SPEC.loader is not None
lateral = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(lateral)


@pytest.fixture(scope="module")
def report():
    return lateral.produce()


def test_replays_all_same_state_force_rows_and_six_modes(report):
    assert report["counts"]["component_records"] == 672
    assert report["counts"]["physical_bolt_axes"] == 32
    assert report["counts"]["upper_blocks"] == 8
    assert report["counts"]["six_mode_records"] == 4032
    assert len(report["rows"]) == 672
    source_actions = {}
    for relative in lateral.ACTION_PATHS:
        action_report = json.loads((lateral.ROOT / relative).read_text())
        for action in action_report["bolt_actions"]:
            key = (relative, action["axis_id"], action["case"], action["load_factor"])
            source_actions[key] = action
    for row in report["rows"]:
        key = (row["source_report"], row["axis_id"], row["case"], row["load_factor"])
        source = source_actions[key]
        assert row["source_lateral_force_on_block_n"] == source["lateral_force_on_block_n"]
        assert row["source_lateral_force_rounding_radius_n"] == source[
            "lateral_force_rounding_radius_n"
        ]
        assert row["source_axial_force_on_block_n_same_state"] == source[
            "axial_force_on_block_n"
        ]
        assert row["source_axial_tension_n_same_state"] == source["axial_tension_n"]
        assert row["source_axial_tension_n_same_state"] >= 0
        assert len(row["full_D_Fyb106ksi_commentary_estimate"]["six_unadjusted_mode_references_n"]) == 6
        assert row["full_D_Fyb106ksi_commentary_estimate"]["effective_bearing_diameter_in"] == 0.25
        assert row["complete_joint_accepted"] is False


@pytest.mark.parametrize(
    ("block", "demand", "capacity", "ratio", "table_ratio", "dr_ratio"),
    [
        (
            "top_outer_left_cleat",
            1074.7867837618585,
            924.0836351885484,
            1.1630838842228397,
            1.7850801221004813,
            1.5696212846824789,
        ),
        (
            "top_outer_right_cleat",
            1264.6913958751518,
            925.3569649376914,
            1.366706518451838,
            2.0975964605198705,
            1.8444169594093378,
        ),
    ],
)
def test_outer_block_known_answers_and_required_total_multiplier(
    report, block, demand, capacity, ratio, table_ratio, dr_ratio
):
    result = report["top_outer_conditional_sensitivities"][block]
    assert math.isclose(result["lateral_demand_n"], demand, rel_tol=1e-13)
    assert math.isclose(result["Fyb106000_conditional_unadjusted_reference_n"], capacity, rel_tol=1e-13)
    assert math.isclose(result["minimum_total_uniform_multiplier_for_unity_before_any_end_use_adjustments"], ratio, rel_tol=1e-13)
    assert ratio > 1
    assert math.isclose(result["Fyb45000_demand_to_unadjusted_reference"], table_ratio, rel_tol=1e-13)
    assert math.isclose(result["Dr0189_all_thread_Fyb106000_demand_to_reference"], dr_ratio, rel_tol=1e-13)
    critical_row = next(
        row
        for row in report["rows"]
        if row["block"] == block
        and row["case"] == result["governing_state"]["case"]
        and row["axis_id"] == result["governing_state"]["axis_id"]
        and row["load_factor"] == result["governing_state"]["load_factor"]
    )
    table_basis = critical_row[
        "full_D_Fyb45000_source_table_scope_limited_sensitivity"
    ]["Fyb_basis"]
    assert "limited to D >= 3/8 in" in table_basis
    assert "does not qualify a 1/4-in Fyb" in table_basis
    assert result["same_state_direct_component_context"]["direct_steel_reference"]["interaction_rule"] == "unresolved"
    assert "not_performed" in result["same_state_direct_component_context"]["nut_capacity_comparison"]


def test_conditional_cd_thresholds_are_not_silently_applied(report):
    left = report["top_outer_conditional_sensitivities"]["top_outer_left_cleat"][
        "minimum_Fyb_by_conditional_CD_sensitivity"
    ]
    right = report["top_outer_conditional_sensitivities"]["top_outer_right_cleat"][
        "minimum_Fyb_by_conditional_CD_sensitivity"
    ]
    assert [row["declared_CD_sensitivity"] for row in left] == [1.0, 1.25, 1.6]
    assert [row["declared_CD_sensitivity"] for row in right] == [1.0, 1.25, 1.6]
    assert [round(row["minimum_Fyb_psi"]) for row in left] == [143393, 91772, 56013]
    assert [round(row["minimum_Fyb_psi"]) for row in right] == [197996, 126717, 77342]
    assert all(row["CD_is_adopted"] is False for row in left + right)
    assert all(row["governing_mode_at_threshold"] == "IV" for row in left + right)
    # At the NDS Table 12A Fyb assumption, even this illustrative CD=1.6
    # does not reach unity for either critical sampled state.
    assert left[-1]["Fyb45000_demand_to_that_conditional_value"] > 1
    assert right[-1]["Fyb45000_demand_to_that_conditional_value"] > 1


def test_hash_mismatch_fails_closed():
    source = lateral.ROOT / "mini_moonboard/bolted_wood_wood_yield.py"
    with pytest.raises(RuntimeError, match="Pinned source changed"):
        lateral.require_hash(source, "0" * 64)
