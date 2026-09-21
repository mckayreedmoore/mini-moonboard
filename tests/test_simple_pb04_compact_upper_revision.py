"""The detached compact block moves only its loaded front grain end."""

import pytest

from scripts import simple_pb04_compact_upper_revision as compact


@pytest.fixture(scope="module")
def result():
    return compact.screen()


def test_front_moves_and_six_inch_rear_stays(result):
    ends = result["projected_n_ends_mm"]
    assert result["block_length_mm"] == pytest.approx(164.141)
    assert ends["front"] == pytest.approx(ends["pb04_front"] - 11.741)
    assert ends["rear"] == pytest.approx(ends["unshifted_six_inch_rear"])
    assert result["gates"]["bolts_unchanged"]
    assert result["gates"]["compact_solid"]
    assert result["fixed_panel_kicker_axes"] == 66


def test_signed_case_and_physical_barrier(result):
    assert result["signed_case"] == "a12-forward"
    assert len(result["signed_end_edge"]) == 4
    assert all(len(members) == 2 for members in result["signed_end_edge"].values())
    assert result["gates"]["both_member_signed_7d_4d"]
    assert result["gates"]["opening_4d_clearance"]
    assert result["gates"]["pockets_clear"]
    assert result["gates"]["pocket_tools_clear"]
    assert result["collision_hits_mm3"]["timber_and_panels"]["main_upper_left"] > 0
    assert not result["collision_hits_mm3"]["pb04_timber_and_panels"]
    assert result["geometry_decision"] == "REVISE_GEOMETRY"
    assert result["solve_run"] is False
    assert result["fabrication_released"] is False
