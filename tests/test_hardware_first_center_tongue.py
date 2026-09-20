"""Regression for the single full-center kerf-right tongue trial."""

import json
from pathlib import Path

from scripts.hardware_first_center_tongue import screen_center_tongue

REPORT = (
    Path(__file__).resolve().parents[1]
    / "docs/bolted-candidate-prototypes/hardware_first_center_tongue.json"
)


def test_full_center_tongue_trial():
    result = screen_center_tongue()
    assert result["protected_axis_count"] == 66
    assert result["retained_frame_axis_count"] == 12
    assert result["changed_rail_count"] == 6
    assert result["lower_seat_center_x_gap_mm"] == 25.4
    assert result["tongue_backing_width_each_edge_mm"] == {
        "left": 11.1125,
        "right": 14.2875,
    }
    assert result["illustrative_left_width_over_half_plywood_mm"] == 1.5875
    assert result["post_listed_4x8_thickness_margin_over_hl_minimum_mm"] == 1.5748
    assert "no bearing minimum" in result["tongue_backing_width_qualification"]
    assert result["tongue_meets_header"]
    assert result["minimum_upper_lower_header_bore_surface_gap_mm"] > 0
    assert all(result["one_piece_cad_solid"].values())
    assert all(result["ordinary_stock_example_dimension_fit"].values())
    assert result["bore_missing_receiver_wood_mm3"] == {}
    assert result["protected_screw_receiver_loss_mm3"] == {}
    assert result["protected_screw_receiver_missing"] == {}
    assert not {k: v for k, v in result.items() if "clashes_mm3" in k and v}
    assert result["failures"] == []
    assert result["status"] == "geometry_only_unqualified"
    assert json.loads(REPORT.read_text()) == result
