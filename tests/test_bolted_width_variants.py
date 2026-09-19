"""LB-09 width identity and transformation checks."""

import json
from pathlib import Path

import pytest

from mini_moonboard import floor_flush_width as baseline_width
from mini_moonboard.bolted_floor_flush_width import (
    KERF_RIGHT,
    KERF_RIGHT_MM,
    geometry_screen,
    variant,
)


def test_both_width_variants_resolve_the_bolted_candidate() -> None:
    official = variant("official")
    kerf = variant(KERF_RIGHT)
    assert official.KEY.endswith("-official")
    assert kerf.KEY.endswith("-kerf-right")
    assert len(official.panel_connections()) == len(kerf.panel_connections()) == 66
    assert len(official.structural_joint_records()) == len(kerf.structural_joint_records()) == 24


def test_kerf_right_translates_right_interfaces_without_claiming_mechanics() -> None:
    result = geometry_screen()
    assert result["right_shift_mm"] == KERF_RIGHT_MM
    assert result["right_shift_consistent"] is True
    assert result["mechanical_evidence_for_kerf_right"] is False


def test_kerf_right_preserves_every_frozen_panel_axis_and_kicker_width() -> None:
    candidate = variant(KERF_RIGHT)
    baseline = baseline_width.variant(KERF_RIGHT)
    expected = {item.name: item for item in baseline.panel_connections()}
    actual = {item.name: item for item in candidate.panel_connections()}
    assert actual.keys() == expected.keys()
    for name, connection in actual.items():
        assert connection.start.toTuple() == pytest.approx(expected[name].start.toTuple()), name
        assert connection.members == expected[name].members, name

    official_parts = {part.name: part for part in variant("official").uncut_wood_parts()}
    kerf_parts = {part.name: part for part in candidate.uncut_wood_parts()}
    for side in ("left", "right"):
        name = f"kicker_{side}"
        assert official_parts[name].blank[0] - kerf_parts[name].blank[0] == pytest.approx(25.4 / 16)


def test_kerf_right_joint_datums_match_frozen_station_axes() -> None:
    from scripts.bolted_candidate_scope_contract import load_axes

    kerf_rows = {row["name"]: row for row in load_axes(KERF_RIGHT)}
    for joint in variant(KERF_RIGHT).structural_joint_records():
        first = kerf_rows[joint.legacy_station_or_axis_ids[0]]
        point = tuple(float(first[f"start_{axis}_mm"]) for axis in "xyz")
        assert joint.local_basis.reference_point_mm == pytest.approx(point), joint.joint_id


def test_width_record_matches_current_adapter_and_owner_scope() -> None:
    record = json.loads((Path(__file__).parents[1] / "docs/bolted-candidate-tasks/LB-09-width-checks.json").read_text())
    result = geometry_screen()
    assert record["physical_width_option"] == "kerf-right"
    assert record["moved_right_interface_count"] == result["right_interface_count"] == 16
    assert record["stationary_right_interface_count"] == result["stationary_right_interface_count"] == 23
    assert record["kerf_right_mechanical_evidence"] is False
