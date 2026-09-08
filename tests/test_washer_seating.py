"""Actual machined wood support under all current through-bolt washers.

This verifies the geometric full-annulus assumption, not washer stiffness,
installation preload, material quality or a connection resistance.
"""
import math

import cadquery as cq
import pytest

from mini_moonboard import wide_frame as frame
from mini_moonboard.bolted_frame import WASHER
from mini_moonboard.product_frame import BOLT_HOLE_DIAMETER_MM
from mini_moonboard.selected_hardware import BoltSpec

# Minimum OD from the selected SAE washer dimensional sheet; the wood bore
# exceeds the selected maximum washer ID (10.6426 mm) and sets the unsupported
# diameter. Actual drill tolerance and delivered washer size remain audit items.
MIN_OD = 20.447
PROBE_DEPTH = .1


def annulus(start, direction):
    return cq.Solid.makeCylinder(MIN_OD/2, PROBE_DEPTH, start, direction).cut(
        cq.Solid.makeCylinder(BOLT_HOLE_DIAMETER_MM/2, PROBE_DEPTH, start, direction))


def test_all_forty_eight_washer_planes_have_full_modeled_wood_support():
    parts = {p.name: p.shape for p in frame.parts(True)}
    bolts = [c for c in frame.connections() if c.kind == "bolt"]
    assert len(bolts) == 24
    expected = math.pi/4*(MIN_OD**2-BOLT_HOLE_DIAMETER_MM**2)*PROBE_DEPTH
    for c in bolts:
        direction = c.direction.normalized()
        for side, member, start, inward in (
            ("head", c.members[0], c.start+direction*WASHER, direction),
            ("nut", c.members[-1], c.start+direction*(WASHER+c.grip), -direction),
        ):
            probe = annulus(start, inward)
            assert probe.Volume() == pytest.approx(expected, abs=1e-6)
            assert probe.intersect(parts[member]).Volume() == pytest.approx(
                expected, abs=1e-4), (c.name, side, member)


def test_probe_detects_an_air_gap_and_partial_edge_support():
    probe = annulus(cq.Vector(0, 0, 0), cq.Vector(0, 0, 1))
    full = cq.Workplane("XY").box(30, 30, 1, centered=(True, True, False)).val()
    assert probe.intersect(full).Volume() == pytest.approx(probe.Volume())
    assert probe.intersect(full.translate((0, 0, .2))).Volume() == pytest.approx(0.)
    assert 0 < probe.intersect(full.translate((15, 0, 0))).Volume() < probe.Volume()


def test_current_bolt_stacks_leave_two_pitches_at_nominal_wood_grip():
    bolts = [c for c in frame.connections() if c.kind == "bolt"]
    assert len(bolts) == 24
    for c in bolts:
        # Selected ASME-pattern underlength bands; these are not wood-grip
        # tolerances. Tip chamfer/runout still needs actual hardware inspection.
        under = 1.016 if c.length <= 63.5 else 1.524 if c.length <= 101.6 else 2.54
        assert c.length <= 152.4, "Longer lengths need a different tolerance band"
        spec = BoltSpec("selected dimensional family", c.length, c.grip, under)
        projection = c.length-under-c.grip-2*spec.washer_thickness_max_mm-spec.nut_height_max_mm
        assert projection >= 2*spec.pitch_mm, (c.name, projection)
        # With the reference thread length, even the minimum washer stack
        # must place the nut beyond the unthreaded shank. Thread runout is not
        # specified by this reference length and remains an inspection item.
        nut_start = c.grip+2*spec.washer_thickness_min_mm
        assert nut_start > c.length-spec.thread_length_reference_mm, c.name
