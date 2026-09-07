"""Current plywood boundary report: exact profiles, not load-rule acceptance."""
from collections import Counter

import pytest

from mini_moonboard.ply_profile_audit import report


def test_all_eight_independent_profiles_and_sixty_incident_bores_are_reported():
    result = report()
    assert result["qualified_for_design"] is False
    rows = result["positions"]
    assert len(result["members"]) == 8
    assert len(rows) == len({(r["member"], r["connection"]) for r in rows}) == 60
    assert Counter(r["member"] for r in rows) == {
        **{f"leg_{side}_{ply}": 7 for side in ("left", "right") for ply in ("inner", "outer")},
        **{f"cheek_splice_{side}_{ply}": 8 for side in ("left", "right") for ply in ("inner", "outer")}}
    for row in rows:
        assert row["loaded_end_or_edge_classification"] is None
        assert row["profile_clear_ligament_mm"] > 0
        assert row["bore_to_bore_clear_ligament_mm"] > 0
        assert row["nearest_profile_boundary_center_distance_mm"] == pytest.approx(
            row["profile_clear_ligament_mm"]+row["bore_diameter_mm"]/2)
        other_ply = row["member"].replace("inner", "outer") if row["member"].endswith("inner") else row["member"].replace("outer", "inner")
        mate = next(r for r in rows if r["member"] == other_ply and r["connection"] == row["connection"])
        assert mate["profile_clear_ligament_mm"] == pytest.approx(row["profile_clear_ligament_mm"])
    # Fixed layout witness: the kicker bolt pair is 30 mm apart, not the
    # overall splice blank dimension. Both project bores are 11.1125 mm.
    kicker = next(r for r in rows if r["connection"] == "transition_kicker_right_bolt_2")
    assert kicker["bore_to_bore_clear_ligament_mm"] == pytest.approx(30.-11.1125)
    assert kicker["nearest_profile_boundary_center_distance_mm"] == pytest.approx(14.0670842)
