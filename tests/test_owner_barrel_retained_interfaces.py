"""Kerf-right retained bolt interfaces must lie on current timber faces."""

import pytest

from mini_moonboard.floor_flush_width import KERF_RIGHT, variant
from scripts.export_owner_barrel_scene import build_integrated_viewer_assembly
from scripts.owner_barrel_retained_interfaces import retained_interface_point


def test_right_rim_leg_interfaces_follow_current_kerf_right_face():
    assembly = build_integrated_viewer_assembly()
    baseline = variant(KERF_RIGHT)
    rim = assembly["wood"]["base_side_right"].BoundingBox()
    leg = assembly["wood"]["lumber_leg_right"].BoundingBox()
    assert rim.xmax == pytest.approx(leg.xmin, abs=1e-6)
    for bolt in assembly["frame_connections"]:
        if bolt.name.startswith("lumber_leg_bolt_right_"):
            old = baseline.bolt_interface_point(bolt)
            current = retained_interface_point(assembly, baseline, bolt)
            assert old.x - current.x == pytest.approx(3.175, abs=1e-6)
            assert current.x == pytest.approx(rim.xmax, abs=1e-6)
        else:
            assert retained_interface_point(assembly, baseline, bolt).toTuple() == (
                pytest.approx(baseline.bolt_interface_point(bolt).toTuple())
            )
