"""The right-center search keeps the owner wood and every nominal stop gate."""

from mini_moonboard.floor_flush_width import KERF_RIGHT, variant
from scripts import owner_barrel_rail_clearance_probe as probe
from scripts import owner_barrel_rail_layout as rail


def test_owner_wood_has_moved_posts_and_both_kicker_screw_backers():
    source = variant(KERF_RIGHT)
    wood = probe.owner_wood(source)
    assert len(wood) == len(tuple(source.uncut_wood_parts())) + 2
    for side, center in (("left", -180.0), ("right", 180.0)):
        bounds = wood[f"base_post_center_{side}"].BoundingBox()
        assert abs((bounds.xmin + bounds.xmax) / 2 - center) < 1e-6
        assert wood[f"inner_kicker_backer_{side}"].Volume() > 0


def test_search_reports_both_rows_and_keeps_blocking_gates(monkeypatch):
    monkeypatch.setattr(probe, "ROW_PAIRS_MM", ((60.0, 92.25), (50.0, 92.25)))
    monkeypatch.setattr(probe, "SETBACKS_MM", (70.0,))
    report = probe.search()
    assert report["candidate_count"] == 2
    assert report["panel_screw_axes_preserved"] == 66
    assert report["retained_frame_bolt_axes_preserved"] == 12
    assert report["protected_inventory_counts"]["panel_screws"] == 66
    assert report["protected_inventory_counts"]["frame_bolts"] == 12
    assert report["fit_qualified"] is False
    assert report["drilling_released"] is False
    candidate = report["candidates"][0]
    assert set(candidate["stations"]) == set(probe.STATIONS)
    for station in candidate["stations"].values():
        assert len(station["bore_intersections_mm3"]) == 2
        assert len(station["body_contained"]) == 2
        assert len(station["nominal_bolt_tip"]) == 2
        assert station["gates"]["nominal_reserves"]
        assert station["gates"]["bores_meet"]
        assert station["gates"]["bolt_tip_inside_rail_exterior"]
        assert all(
            row["past_modeled_bore_mm"] > 0 for row in station["nominal_bolt_tip"]
        )
        assert not station["gates"]["no_protected_hits"]
    assert candidate["geometry_gates_clear"] is False
    continued = report["candidates"][1]
    assert continued["geometry_gates_clear"] is True
    for station in continued["stations"].values():
        assert station["failed_gates"] == []
        assert station["nominal_bolt_tip"][0]["past_modeled_bore_mm"] == 10.2452
        assert station["nominal_bolt_tip"][0]["to_rail_exterior_mm"] == 950.826
    assert report["fit_qualified"] is False


def test_layout_parameter_search_does_not_change_default_pose():
    assert rail.ROW_N_FROM_FRONT_MM == (60.0, 92.25)
    assert rail.BARREL_X_FROM_BUTT_MM == 70.0
