from collections import Counter

import pytest

from scripts.wood_joint_midpoint_clearance import midpoint_sites


def test_nearest_neighbor_sites_are_unique_and_include_kicker():
    rows = midpoint_sites()
    assert len({r["id"] for r in rows}) == 491
    assert Counter((r["family"], r["direction"]) for r in rows) == {
        ("LED", "horizontal"): 120,
        ("LED", "vertical"): 121,
        ("T-nut", "horizontal"): 120,
        ("T-nut", "vertical"): 121,
        ("kicker T-nut", "horizontal"): 9,
    }


def test_stock_grid_boundary_exceptions_are_not_regularized():
    rows = {r["id"]: r for r in midpoint_sites()}
    assert rows["T-nut:A6-A7"]["s_mm"] == pytest.approx(1209.2)
    assert rows["LED:A1-A2"]["s_mm"] == pytest.approx(109.2)
    assert rows["LED:A7-A8"]["s_mm"] == pytest.approx(1309.2)
    assert rows["T-nut:A1-B1"]["x_mm"] == 300
    assert rows["T-nut:A1-B1"]["s_mm"] == pytest.approx(99.2)
