"""Axial overlap is deliberately distinct from effective threaded embedment."""
from collections import Counter

import pytest

from mini_moonboard.connection_engagement import covered_length, report


def test_thread_tail_overlap_respects_gaps_and_truncated_ends():
    intervals = [(10., 20.), (25., 40.)]
    assert covered_length(intervals, 15., 30.) == 10.
    assert covered_length(intervals, 21., 24.) == 0.
    assert covered_length(intervals, 0., 100.) == 25.


def test_current_candidate_axial_audit_preserves_unknown_effective_embedment():
    result = report()
    assert result["qualified_for_design"] is False
    rows = result["connections"]
    assert len(rows) == len({r["connection"] for r in rows}) == 278
    assert Counter(r["kind"] for r in rows) == {"bolt": 114, "screw": 164}
    for row in rows:
        if row["kind"] == "bolt":
            assert row["tip_projection_catalog_stack_mm"] >= row["two_pitch_reference_mm"]
            assert row["stock_tolerance_included"] is False
            assert row["complete_exposed_threads_verified"] is False
        else:
            assert row["axis_material_intervals_mm"]
            assert row["nominal_axis_material_in_thread_tail_including_point_mm"] > 0
            assert row["effective_threaded_embedment_mm"] is None
            assert row["point_exclusion_mm"] is None
            for scenario in row["product_generation_endpoint_scenarios"]:
                assert 0 <= scenario["axial_material_in_thread_tail_including_point_mm"] <= scenario["thread_tail_mm"]+1e-7
    panel = next(r for r in rows if r["connection"] == "panel_1")
    assert panel["axis_material_intervals_mm"][0][0] == pytest.approx(18.25625)
    assert panel["nominal_axis_material_in_thread_tail_including_point_mm"] == pytest.approx(32.54375)
    assert panel["nominal_axial_cover_beyond_tip_mm"] == pytest.approx(5.55625)
