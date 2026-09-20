"""The PB01 comparison stays a signed, conditional component screen."""

import copy

import pytest

from scripts import simple_pb01_hybrid_component_comparison as component
from scripts.simple_pb01_hybrid_component_comparison import compare
from scripts.simple_pb01_hybrid_local_actions import extract


def test_frozen_comparison_keeps_signs_and_unresolved_joint():
    result = compare()
    assert result["case"] == "a12-left"
    assert result["proxy_station_count"] == 23
    assert result["joint_utilization"] is None
    assert result["design_pass"] is None
    assert set(result["interfaces"]) == {"upright", "rail"}
    rows = {
        bolt["name"]: bolt
        for face in result["interfaces"].values()
        for bolt in face["bolts"]
    }
    assert set(rows) == {
        "pb01_upright_u1",
        "pb01_upright_u2",
        "pb01_rail_r1",
        "pb01_rail_r2",
    }
    assert rows["pb01_upright_u1"]["axial_on_host_n"] == pytest.approx(-0.635)
    assert rows["pb01_rail_r1"]["axial_on_host_n"] == pytest.approx(31.36663)
    assert rows["pb01_rail_r1"]["washer_positive_axial_ratio"] > 0
    assert rows["pb01_rail_r2"]["washer_positive_axial_ratio"] is None
    for row in rows.values():
        assert row["lateral_on_host_magnitude_n"] >= 0
        assert row["conditional_lateral_yield"]["0.189"]["90deg_ratio"] >= 0
        assert row["conditional_lateral_yield"]["0.180"]["90deg_ratio"] >= 0
        assert all(value is None for value in row["unknowns"].values())


def test_wrong_source_identity_fails_closed(monkeypatch):
    source = copy.deepcopy(extract())
    source["case"] = "a12-forward"
    monkeypatch.setattr(component, "extract", lambda: source)
    with pytest.raises(ValueError, match="source identity"):
        compare()
    source = copy.deepcopy(extract())
    source["interfaces"]["rail"]["bolts"][0]["axis_xyz"] = [0, 0, 1]
    with pytest.raises(ValueError, match="axis"):
        compare()
