"""Regression for rear-staggered inward upper HL33s."""

import json
from pathlib import Path

from scripts.hardware_first_center_upper_stagger import screen_upper_stagger

REPORT = (
    Path(__file__).resolve().parents[1]
    / "docs/bolted-candidate-prototypes/hardware_first_center_upper_stagger.json"
)


def test_rear_staggered_upper_pair():
    result = screen_upper_stagger()
    assert result["status"] == "rejected_installed_geometry_trial"
    assert result["outer_upper_y0_mm"] == -100.0
    assert result["shift_samples_mm"][0] == 63.5
    assert result["protected_axis_count"] == 66
    assert result["retained_frame_axis_count"] == 12
    assert result["protected_screw_receiver_loss_mm3"] == {}
    assert result["protected_screw_receiver_missing"] == {}
    assert result["baseline_failures"] == []
    losses = []
    for sample in result["samples"]:
        assert sample["new_plate_pair_clashes_mm3"]
        assert sample["new_plate_changed_wood_clashes_mm3"]
        assert "new bore receiver loss" in sample["failures"]
        assert sample["new_to_existing_plate_clashes_mm3"] == {}
        assert sample["new_independent_bore_crossings_mm3"] == {}
        assert sample["protected_screw_new_hardware_clashes_mm3"] == {}
        assert sample["existing_frame_axis_new_hardware_clashes_mm3"] == {}
        losses.append(
            sample["new_bore_missing_receiver_wood_mm3"]["upper_left_inner_principal"]
        )
    assert losses == sorted(losses)
    assert losses[0] > 0
    assert (
        result["samples"][0]["axis_boundary_rays"]["upper_left_inner_principal"][
            "transverse_negative_boundary_mm"
        ]
        < result["ideal_bore_diameter_mm"] / 2
    )
    assert json.loads(REPORT.read_text()) == result
