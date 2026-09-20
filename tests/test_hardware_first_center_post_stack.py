"""Nominal stack arithmetic for the shared HL33 post bolt."""

import json
from pathlib import Path

from scripts.hardware_first_center_post_stack import calculate


def test_stack_bounds_and_unresolved_thread_fit():
    result = calculate()
    assert result["wood_and_plates_mm"] == 199.6
    assert result["under_nut_grip_mm"] == 205.1372
    rows = {row["length_in"]: row for row in result["candidates"]}
    assert rows[8]["end_beyond_nut_mm"] == [-13.3164, -12.783]
    assert rows[8]["length_status"] == "too_short_with_two_washers_and_full_nut"
    assert rows[10]["end_beyond_nut_mm"] == [37.4836, 38.017]
    assert rows[10]["thread_engagement_status"] == "unresolved_thread_start_and_runout"
    assert rows[12]["end_beyond_nut_mm"] == [88.2836, 88.817]
    assert (
        rows[12]["thread_engagement_status"]
        == "nominal_thread_span_only_runout_unresolved"
    )
    assert result["status"] == "screen_only_no_selection"
    report = (
        Path(__file__).resolve().parents[1]
        / "docs/bolted-candidate-prototypes/hardware_first_center_post_stack.json"
    )
    assert json.loads(report.read_text()) == result
