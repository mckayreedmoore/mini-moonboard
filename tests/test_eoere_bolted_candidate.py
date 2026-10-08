"""Known-answer fixtures for paired holes, mirrored axes and raw ray crossings."""

import math

import cadquery as cq
import pytest

from scripts.eoere_bolted_candidate import (
    Scenario,
    geometry_tools,
    line_key,
    pose,
    template,
)


def test_factory_template_preserves_eight_holes_and_only_four_are_installed():
    scenario = Scenario()
    body = template(scenario)
    gross = (2 * scenario.leg_mm * scenario.thickness_mm - scenario.thickness_mm**2) * scenario.width_mm
    removed = 8 * math.pi * (scenario.factory_hole_mm / 2)**2 * scenario.thickness_mm
    assert body.isValid() and len(body.Solids()) == 1
    assert body.Volume() == pytest.approx(gross - removed, abs=1e-6)
    assert len(scenario.holes()) == 8
    assert len(scenario.holes(active_only=True)) == 4
    for flange in ("beam", "post"):
        installed = [h for h in scenario.holes(active_only=True) if h["flange"] == flange]
        assert installed[1]["transverse_mm"] - installed[0]["transverse_mm"] == pytest.approx(50.8)
        assert all(h["row"] == "far" for h in installed)


def test_mirrored_pose_retains_proper_basis_and_transverse_pair():
    shape = template(Scenario())
    row = {"duty_id": "mirrored", "beam": "a", "post": "b", "origin_xyz_mm": [8, 10, 20],
           "u_xyz": [-1, 0, 0], "v_xyz": [0, 0, 1], "w_xyz": [0, 1, 0]}
    angle = pose(row, shape)
    assert angle.u.cross(angle.v).dot(angle.w) == pytest.approx(1)
    assert angle.point(65.0875, 0, 25.4).toTuple() == pytest.approx((-57.0875, 35.4, 20))
    assert angle.shape.Volume() == pytest.approx(shape.Volume())


def test_line_grouping_counts_opposite_ports_once_and_parallel_pair_twice():
    point = cq.Vector(8, 10, 20)
    direction = cq.Vector(0, 0, 1)
    assert line_key(point, direction) == line_key(point + direction * 90, -direction)
    assert line_key(point, direction) != line_key(point + cq.Vector(50.8, 0, 0), direction)


def test_raw_oblique_receiver_crossing_uses_true_grip():
    block = cq.Solid.makeBox(100, 140, 38.1).rotate((0, 0, 0), (1, 0, 0), 40)
    direction = cq.Vector(0, -math.sin(math.radians(40)), math.cos(math.radians(40)))
    point = cq.Vector(60, 70 * math.cos(math.radians(40)), 70 * math.sin(math.radians(40)))
    near, far = geometry_tools.line_span(block, point, direction)
    assert near == pytest.approx(0, abs=1e-7)
    assert far - near == pytest.approx(38.1)
    with pytest.raises(ValueError, match="misses"):
        geometry_tools.line_span(block, point + cq.Vector(150, 0, 0), direction)


@pytest.mark.parametrize("scenario", [Scenario(far_offset_mm=40), Scenario(width_mm=50),
                                      Scenario(factory_hole_mm=9), Scenario(wood_bore_mm=9)])
def test_invalid_datum_or_hole_scenario_is_rejected(scenario):
    with pytest.raises(ValueError):
        scenario.validate()
