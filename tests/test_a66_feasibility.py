"""Conditional A66 wood envelope; no factory layout or drilling authority."""

import json
from pathlib import Path

import pytest

from scripts.bolted_candidate_a66_feasibility import envelope, trial


@pytest.mark.parametrize(
    "family,side", [("center", "left"), ("outer", "left"), ("outer", "right")]
)
def test_envelope_uses_current_raw_cad_and_has_no_release(family, side):
    result = envelope(family, side)
    assert result["station"].startswith("clip_")
    assert result["raw_cad_source"].endswith("uncut_wood_parts() and stations()")
    assert result["bolt_diameter_mm"] == 9.525
    assert result["factory_hole_coordinates_known"] is False
    assert result["oblique_end_distance_classified"] is False
    assert result["connector_strength_classified"] is False
    assert result["drilling_released"] is False
    assert result["vertical_offset_band_mm"][1] > result["vertical_offset_band_mm"][0]


def test_trial_rejects_oblique_end_and_broad_face_edge_losses():
    bounds = envelope("center", "left")
    row_y = bounds["example_row_y_mm"]
    low, high = bounds["vertical_offset_band_mm"]
    good = trial("center", "left", row_y, (low + 1, high - 1), (20, 60))
    assert good["conditional_wood_geometry"] is True
    assert all(v >= 0.99999 for v in good["raw_wood_bore_fractions"])
    near_end = trial("center", "left", row_y, (2, high - 1), (20, 60))
    assert near_end["conditional_wood_geometry"] is False
    assert near_end["raw_wood_bore_fractions"][0] < 0.99999
    outside = trial("center", "left", row_y + 100, (low + 1, high - 1), (20, 60))
    assert outside["conditional_wood_geometry"] is False


def test_offsets_are_inputs_not_claimed_factory_coordinates():
    with pytest.raises(ValueError):
        trial("outer", "left", -90, (20, 10), (20, 60))
    with pytest.raises(ValueError):
        trial("outer", "left", -90, (20, 40), (20, float("nan")))


def test_center_horizontal_axes_mirror_away_from_principal_faces():
    left = envelope("center", "left")
    right = envelope("center", "right")
    left_trial = trial("center", "left", left["example_row_y_mm"], (20, 80), (20, 60))
    right_trial = trial(
        "center", "right", right["example_row_y_mm"], (20, 80), (20, 60)
    )
    assert left["bend_xyz_mm"][0] == -89.05
    assert right["bend_xyz_mm"][0] == 89.05
    assert left_trial["hypothetical_horizontal_axis_x_mm"] == [-109.05, -149.05]
    assert right_trial["hypothetical_horizontal_axis_x_mm"] == [109.05, 149.05]
    assert left_trial["conditional_wood_geometry"] is True
    assert right_trial["conditional_wood_geometry"] is True


def test_report_preserves_assumption_and_release_boundaries():
    path = (
        Path(__file__).resolve().parents[1]
        / "docs/bolted-candidate-prototypes/a66-feasibility-envelope.json"
    )
    report = json.loads(path.read_text())
    assert "retailer-listed" in report["assumption_sources"]["offset_search_cap"]
    assert "No A66 wood-bore diameter" in report["assumption_sources"]["bore_diameter"]
    assert report["factory_pattern"].startswith("Unknown")
    assert report["drilling_released"] is False
    for record in report["geometry_records"]:
        family = "center" if "center" in record["station"] else "outer"
        side = "left" if record["station"].endswith("left") else "right"
        assert record == envelope(family, side)
