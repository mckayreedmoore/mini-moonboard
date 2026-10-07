"""Independent panel-outline fixtures for the separate CAD review export."""

import math

import cadquery as cq
import pytest

from scripts.thin_bolted_model import unperforated_main


def test_internal_hole_is_filled_without_changing_rotated_panel_outline():
    original = cq.Solid.makeBox(100, 70, 18)
    hole = cq.Solid.makeCylinder(6, 20, cq.Vector(35, 25, -1))
    perforated = original.cut(hole).rotate((0, 0, 0), (1, 0, 0), 27).translate((3, 8, 15))
    direction = cq.Vector(0, -math.sin(math.radians(27)), math.cos(math.radians(27)))
    filled = unperforated_main(perforated, direction)
    expected = original.rotate((0, 0, 0), (1, 0, 0), 27).translate((3, 8, 15))
    assert filled.Volume() == pytest.approx(100 * 70 * 18)
    assert filled.cut(expected).Volume() < 1e-6
    assert expected.cut(filled).Volume() < 1e-6


def test_curved_body_cannot_supply_a_planar_panel_outline():
    sphere = cq.Solid.makeSphere(20, angleDegrees1=-90, angleDegrees2=90)
    with pytest.raises(ValueError, match="no front planar panel face"):
        unperforated_main(sphere, cq.Vector(0, 0, 1))
