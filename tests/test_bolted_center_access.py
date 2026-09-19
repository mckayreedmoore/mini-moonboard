"""Collision regressions for the unselected center-header access trial."""

import json
from pathlib import Path

import cadquery as cq
import pytest

from scripts.bolted_candidate_center_access import screen_center_access


@pytest.fixture(scope="module")
def nominal():
    return screen_center_access()


def test_shared_row_has_four_nominal_clear_shaft_and_radial_probes(nominal):
    assert nominal["status"] == "nominal_access_diagnostic_only"
    assert nominal["width_option"] == "kerf-right"
    assert nominal["retained_axis_counts"] == {
        "hillman_panel": 66,
        "bolt_clearance": 12,
    }
    assert nominal["kerf_right_panel_kicker_solid_obstacles"] == [
        "kicker_left",
        "kicker_right",
        "main_lower_left",
        "main_lower_right",
        "main_upper_left",
        "main_upper_right",
    ]
    assert "installed-panel access" in nominal["limits"]
    assert nominal["joint_selected"] is False
    assert nominal["access_verified"] is False
    assert nominal["drilling_released"] is False
    assert nominal["illustrative_washer_radius_mm"] == pytest.approx(17.5)
    assert nominal["radial_probe_radius_mm"] == pytest.approx(25)
    shared, distinct = nominal["cases"]
    assert shared["shared_through_header_axes"] is True
    assert shared["top_y_mm"] == pytest.approx(-95.382052)
    assert shared["underside_y_mm"] == shared["top_y_mm"]
    assert len(shared["axes"]) == 4
    for axis in shared["axes"]:
        assert axis["stack_mm"] == pytest.approx(50.8)
        assert axis["top_insertion_or_withdrawal_shaft_hits"] == []
        assert axis["bottom_insertion_or_withdrawal_shaft_hits"] == []
        assert axis["top_radial_envelope_hits"] == []
        assert axis["bottom_radial_envelope_hits"] == []
        assert axis["top_washer_envelope_hits"] == []
        assert axis["bottom_washer_envelope_hits"] == []
    assert distinct["shared_through_header_axes"] is False


def test_distinct_midpoint_has_one_open_axial_side_per_row(nominal):
    distinct = nominal["cases"][1]
    assert distinct["underside_y_mm"] == pytest.approx(-119.666026)
    assert len(distinct["axes"]) == 8
    for axis in distinct["axes"]:
        side = axis["axis"].split("_")[0]
        assert axis["stack_mm"] == pytest.approx(44.45)
        if "_top_" in axis["axis"]:
            assert axis["top_insertion_or_withdrawal_shaft_hits"] == []
            assert axis["bottom_insertion_or_withdrawal_shaft_hits"] == [
                f"angle:{side}:underside:0"
            ]
            assert axis["top_radial_envelope_hits"] == []
            assert axis["bottom_radial_envelope_hits"] == [f"angle:{side}:underside:0"]
            assert axis["top_washer_envelope_hits"] == []
            assert axis["bottom_washer_envelope_hits"] == [f"angle:{side}:underside:0"]
        else:
            assert axis["bottom_insertion_or_withdrawal_shaft_hits"] == []
            assert axis["top_insertion_or_withdrawal_shaft_hits"] == [
                f"angle:{side}:top:0"
            ]
            assert axis["bottom_radial_envelope_hits"] == []
            assert axis["top_radial_envelope_hits"] == [f"angle:{side}:top:0"]
            assert axis["bottom_washer_envelope_hits"] == []
            assert axis["top_washer_envelope_hits"] == [f"angle:{side}:top:0"]


def test_injected_obstruction_changes_shaft_and_radial_result():
    obstacle = cq.Solid.makeBox(10, 10, 10, cq.Vector(-130, -100, 300))
    result = screen_center_access(extra_obstacles=(("test:obstruction", obstacle),))
    left = result["cases"][0]["axes"][0]
    right = result["cases"][0]["axes"][2]
    assert "test:obstruction" in left["top_insertion_or_withdrawal_shaft_hits"]
    assert "test:obstruction" in left["top_radial_envelope_hits"]
    assert "test:obstruction" not in right["top_insertion_or_withdrawal_shaft_hits"]
    assert "test:obstruction" not in left["bottom_radial_envelope_hits"]


@pytest.mark.parametrize(
    "dimensions",
    [
        {"bolt_length_mm": 50},
        {"bolt_length_mm": float("nan")},
        {"radial_probe_mm": 6},
        {"washer_probe_radius_mm": 6},
        {"radial_depth_mm": 0},
    ],
)
def test_rejects_invalid_probe_dimensions(dimensions):
    with pytest.raises(ValueError):
        screen_center_access(**dimensions)


def test_record_tracks_screen_and_keeps_access_unverified(nominal):
    record = json.loads(
        (
            Path(__file__).resolve().parents[1]
            / "docs/bolted-candidate-prototypes/center-access.json"
        ).read_text()
    )
    shared, distinct = nominal["cases"]
    assert record["physical_width"] == nominal["width_option"]
    assert (
        record["illustrative_probes"]["bolt_length_mm"]
        == nominal["illustrative_bolt_length_mm"]
    )
    assert (
        record["illustrative_probes"]["washer_radius_mm"]
        == nominal["illustrative_washer_radius_mm"]
    )
    assert record["coincident_shared_row"]["unique_header_axes"] == len(shared["axes"])
    assert record["conditional_distinct_row_midpoint"]["unique_header_axes"] == len(
        distinct["axes"]
    )
    assert (
        record["conditional_distinct_row_midpoint"]["underside_y_mm"]
        == distinct["underside_y_mm"]
    )
    assert record["joint_selected"] is nominal["joint_selected"] is False
    assert record["access_verified"] is nominal["access_verified"] is False
    assert record["drilling_released"] is nominal["drilling_released"] is False
