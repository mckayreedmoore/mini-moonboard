"""Actual solid-stock inventory, not permission to claim the NDS exception."""
import json
from pathlib import Path

import pytest

from fea import solid_leg_thread_screen as screen


@pytest.fixture(scope="module")
def result():
    return screen.build()


def test_published_report_replays_exactly(result):
    assert json.loads(Path("fea/results/solid-leg-thread-screen.json").read_text()) == result


def test_all_actual_solid_members_and_tolerance_margin(result):
    assert len(result["stacks"]) == 8
    assert not result["qualified_for_design"] and not result["full_body_exception_verified"]
    for stack in result["stacks"]:
        assert len(stack["members"]) == 2
        members = sorted(stack["members"], key=lambda r: r["raw_interval_mm"][0])
        assert members[0]["raw_interval_mm"] == pytest.approx([2.032, 40.132])
        assert members[1]["raw_interval_mm"] == pytest.approx([40.132, 78.232])
        side = members[1]
        assert side["minimum_full_body_length_for_quarter_condition_mm"] == pytest.approx(68.707)
        cases = side["scenarios"]
        assert [c["quarter_margin_mm"] for c in cases] == pytest.approx([1.143, -.381, 7.493, 5.969])
        assert [c["nominal_quarter_length_condition"] for c in cases] == [True, False, True, True]
        runout = side["generic_runout_screen_not_product_certification"]
        assert [r["generic_minimum_body_length_mm"] for r in runout] == pytest.approx([61.9125, 68.2625])
        assert all(r["quarter_condition_margin_mm"] < 0 for r in runout)


def test_same_case_reference_comparison_and_no_force_changes(result):
    evidence = screen.resistance.screen(screen.ARCHIVE)
    assert len(result["rows"]) == 12
    for row in result["rows"]:
        for label in ("governing_root", "governing_conditional_full_body"):
            peak = row[label]
            original = next(r for r in evidence["rows"] if r["stiffness"] == row["stiffness"] and r["case"] == peak["case"])
            bolt = original["bolts"][peak["bolt"]]
            assert peak["force_xyz_n"] == bolt["force_xyz_n"]
            assert peak["conditional_full_body_ratio"] == pytest.approx(
                bolt["lateral_n"]/peak["conditional_full_body_reference"]["reference_lateral_n"])
            assert peak["conditional_full_body_ratio"] < bolt["directional_reference"]["lateral_demand_reference_ratio"]


def test_full_diameter_reference_reuses_explicit_kernel():
    result = screen.full_body_reference([3650., 3650.])
    inputs = dict(screen.resistance.bolt_reference()["inputs"])
    inputs.update(main_bearing_lb_in=3650*.375, side_bearing_lb_in=3650*.375,
                  main_yield_moment_lb_in=45000*.375**3/6,
                  side_yield_moment_lb_in=45000*.375**3/6)
    expected = screen.resistance.single_shear(**inputs)
    assert result["reference_lateral_n"] == pytest.approx(expected["reference_lateral_lbf"]*4.4482216152605)
