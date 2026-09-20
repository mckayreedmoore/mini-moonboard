"""Regression for the hybrid upper toe/seat search bound."""

import json
from pathlib import Path

from scripts.hardware_first_center_hybrid_toe import screen_toe_shift

REPORT = (
    Path(__file__).resolve().parents[1]
    / "docs/bolted-candidate-prototypes/hardware_first_center_hybrid_toe.json"
)


def test_full_upper_seat_band_cannot_contain_first_toe_bores():
    result = screen_toe_shift()
    assert result["status"] == "nominal_shift_band_rejected"
    assert result["width_option"] == "kerf-right"
    assert result["maximum_shift_with_full_127_mm_seat_on_existing_header_mm"] == 12.7
    assert result["seat_overhang_at_15_mm_shift_mm"] == 2.3
    assert all(
        row["at_max_supported_shift_missing_wood_mm3"] > 800
        and row["at_15_mm_shift_missing_wood_mm3"] == 0
        for row in result["first_bore_samples"].values()
    )
    assert json.loads(REPORT.read_text()) == result
