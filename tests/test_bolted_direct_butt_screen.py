"""The preserved hard joints have contact, not a ready-made lap-bolt stack."""

import json
from pathlib import Path

import pytest

from mini_moonboard import compact_floor_flush_frame as frame


def test_representative_direct_bolt_screen_matches_current_uncut_solids():
    record = json.loads(Path("docs/bolted-candidate-direct-butt-screen.json").read_text())
    solids = {part.name: part.shape for part in frame.uncut_wood_parts()}
    assert record["status"] == "geometry_screen_only"
    assert record["direct_bolt_detail_selected"] is False
    for joint in record["pairs"]:
        first, second = (solids[name] for name in joint["members"])
        assert first.distance(second) == pytest.approx(0, abs=1e-5)
        assert first.intersect(second).Volume() == pytest.approx(0, abs=1e-3)
        axis = joint["nominal_contact_axis"]
        assert getattr(first.BoundingBox(), f"{axis}{joint['first_boundary']}") == pytest.approx(
            joint["nominal_contact_datum_mm"], abs=1e-3
        )
        assert getattr(second.BoundingBox(), f"{axis}{joint['second_boundary']}") == pytest.approx(
            joint["nominal_contact_datum_mm"], abs=1e-3
        )
        assert joint["nominal_contact_description"] == "end-to-side butt"
        assert joint["bolt_axis_and_stack_verified"] is False
    assert record["retained_panel_axes_unchanged"] is True
    assert record["drilling_released"] is False
