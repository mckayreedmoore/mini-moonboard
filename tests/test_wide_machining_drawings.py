"""Small geometric reference controls; SVGs are never cutting templates."""
import xml.etree.ElementTree as ET

import cadquery as cq

from mini_moonboard.box_frame import Part
from mini_moonboard.wide_machining import datum, to_world
from scripts.wide_machining_drawings import drawing, vertices


def test_labeled_three_views_have_dual_units_and_reversible_vertices():
    shape = cq.Solid.makeBox(10., 20., 30., cq.Vector(4., 5., 6.))
    part = Part("base_header", shape, (10., 20., 30.), "test", 1)
    axes = datum(part)
    points = vertices(part, axes)
    assert len(points) == 8
    assert set(points) == {(x, y, z) for x in (0., 10.) for y in (0., 20.) for z in (0., 30.)}
    for point in points:
        world = to_world(point, axes)
        assert world in {(x, y, z) for x in (4., 14.) for y in (5., 25.) for z in (6., 36.)}
    text = drawing(part, axes)
    root = ET.fromstring(text)
    assert root.tag == "{http://www.w3.org/2000/svg}svg"
    assert text.count("datum 0") == 3 and text.count("stroke-dasharray") == 3
    assert "10.000 mm / 0.3937 in" in text and "30.000 mm / 1.1811 in" in text
    assert "not a cutting template" in text and "raw-form envelope" in text
