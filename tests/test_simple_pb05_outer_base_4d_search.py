"""Bounded geometry checks for the unchanged PB05 outer-base duties."""

import pytest

from scripts import simple_pb05_outer_base_4d_search as trial


@pytest.fixture(scope="module")
def result():
    return trial.screen()


def test_full_section_stock_and_conditional_4d_centers(result):
    assert not result["stock_screen"]["2x4-flat"]["4d_plan_possible"]
    assert not result["stock_screen"]["2x4-edge"]["4d_plan_possible"]
    assert result["stock_screen"]["4x4"]["4d_plan_possible"]
    assert set(result["stations"]) == set(trial.prior.TARGET_STATIONS)
    for row in result["stations"].values():
        assert row["conditional_4d_edges"]
        assert min(row["edge_margins_mm"].values()) >= trial.FOUR_D_MM
        assert row["bolt_grips_mm"][
            next(name for name in row["bolt_grips_mm"] if name.endswith("_side"))
        ] == pytest.approx(177.8)
        side = next(
            stack
            for name, stack in row["nominal_bolt_stacks"].items()
            if name.endswith("_side")
        )
        assert side["required_length_mm"] == pytest.approx(189.3824)
        assert side["length_margin_mm"] == pytest.approx(13.8176)
        assert side["tip_beyond_wood_mm"] == pytest.approx(23.749)
        assert side["tip_beyond_nut_mm"] == pytest.approx(16.3576)
        assert side["nut_start_after_listed_8in_thread_start"]
        assert row["side_6in_length_shortfall_mm"] == pytest.approx(36.9824)
        assert all(
            stack["tip_within_40mm_far_tool"]
            for stack in row["nominal_bolt_stacks"].values()
        )
        assert all(volume > 0 for volume in row["host_bore_volume_mm3"].values())
        assert row["header_contact_area_mm2"] > 0
        assert row["side_contact_area_mm2"] > 0


def test_exact_protected_occupancy_and_no_release(result):
    assert all(not row["protected_collisions"] for row in result["stations"].values())
    assert all(not row["cross_bolt_collisions"] for row in result["stations"].values())
    assert result["decision"] == "GEOMETRY_PASS_CONDITIONAL"
    assert not result["strength_checked"]
    assert not result["drilling_released"]
    assert not result["fabrication_released"]


def test_source_identity_guard():
    class WrongSource:
        KEY = "wrong"

    with pytest.raises(ValueError, match="source identity"):
        trial.screen(module=WrongSource())
