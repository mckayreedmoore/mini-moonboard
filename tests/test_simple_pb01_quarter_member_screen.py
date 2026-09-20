"""Conditional PB-01 member components cannot become a joint verdict."""

import json

import pytest

from scripts import simple_pb01_quarter_member_screen as member_screen
from scripts.simple_pb01_quarter_member_screen import screen


def test_quarter_member_screen_uses_actual_four_bolt_pose_and_no_demand():
    result = screen()
    assert result["pose"] == "cleat_grain_n_4x6_group_quarter"
    assert result["physical_width"] == "kerf-right"
    assert result["bore_diameter_mm"] == 7.5
    assert result["bolt_count_by_interface"] == {"upright": 2, "rail": 2}
    assert result["conditional_only"] is True
    assert result["joint_capacity_lbf"] is None
    assert result["utilization"] is None
    assert result["drilling_released"] is False


def test_parallel_member_components_match_documented_pose_geometry():
    members = screen()["components_lbf"]
    assert members["rail_host_row_toward_butt"] == pytest.approx(850.3937)
    assert members["cleat_upright_row_toward_front"] == pytest.approx(3507.8740)
    assert members["upright_host_net_tension"] == pytest.approx(4234.3996)
    assert members["rail_host_net_tension"] == pytest.approx(4489.0748)
    assert members["cleat_rail_holes_net_tension"] == pytest.approx(6351.5994)
    assert members["cleat_upright_hole_net_tension"] == pytest.approx(6181.8159)


def test_changed_pose_inventory_fails_closed(tmp_path, monkeypatch):
    source = json.loads(member_screen.SOURCE.read_text())
    source[member_screen.POSE]["bolt_groups"]["rail"].pop()
    trial = tmp_path / "pose.json"
    trial.write_text(json.dumps(source))
    monkeypatch.setattr(member_screen, "SOURCE", trial)
    with pytest.raises(ValueError, match="four-bolt count"):
        screen()
