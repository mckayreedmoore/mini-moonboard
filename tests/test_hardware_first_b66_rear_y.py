"""One bounded rear-Y B66 center pose, with no fabrication implication."""

import json
from pathlib import Path

from scripts.hardware_first_b66_rear_y import screen_b66_rear_y

REPORT = (
    Path(__file__).resolve().parents[1]
    / "docs/bolted-candidate-prototypes/hardware_first_b66_rear_y.json"
)


def test_rear_y_b66_installed_pose_and_evidence_are_reproducible():
    result = screen_b66_rear_y()
    assert result["status"] == "rejected_nominal_installed_geometry"
    assert result["protected_screw_axes"] == 66
    assert result["retained_frame_axes"] == 12
    assert result["protected_screw_receiver_intersections"] == 66
    assert result["brackets"] == 3
    assert result["factory_hole_paths"] == 12
    assert result["nominal_dxf_free_end_offsets_mm"] == [25.4, 126.744]
    assert result["minimum_receiver_thickness_mm"] >= 76.2
    assert result["rear_y_upper_bore_missing_wood_mm3"]
    assert result["new_wood_neighbor_conflicts"]
    assert json.loads(REPORT.read_text()) == result
