"""Reserved service space and full nominal washer bearing; no installation/capacity approval.

The measured light has a 24 mm body plus 7 mm dome. Reserving all 31 mm
behind the panel is conservative project geometry, not measured installed rear
projection. Connector bends, full harness routing and tool engagement remain open.
"""
import math

import cadquery as cq
import pytest

from mini_moonboard import box_frame as b
from mini_moonboard import product_frame as frame
from mini_moonboard.box_exports import overlap
from mini_moonboard.panel_grid import main_led_datums
from mini_moonboard.selected_hardware import BoltSpec, spec_for


def light_datums():
    for label, (u, s) in main_led_datums().items():
        if s >= 0:
            direction = b.normal()
            front = b.point(u-b.HALF, s, -frame.FACE_THICKNESS_MM)
        else:
            direction = cq.Vector(0, -1, 0)
            front = cq.Vector(u-b.HALF, -36+frame.FACE_THICKNESS_MM, b.V1_KICKER_HEIGHT_MM+s)
        yield label, front+direction*frame.FACE_THICKNESS_MM, direction


def test_reserved_lights_begin_at_fixed_rear_faces_not_climbing_faces():
    assert frame.FACE_THICKNESS_MM == pytest.approx(18.25625)
    records = list(light_datums())
    assert len(records) == 132
    for label, start, direction in records:
        u, s = main_led_datums()[label]
        if s >= 0:
            assert (start-b.point(u-b.HALF, s, 0)).Length < 1e-8
            assert direction.dot(b.normal()) == pytest.approx(1)
        else:
            assert start.toTuple() == pytest.approx((u-b.HALF, -36, b.V1_KICKER_HEIGHT_MM+s))
            assert direction.toTuple() == (0, -1, 0)


@pytest.fixture(scope="module")
def service_envelopes():
    envelopes = [("LED "+label, cq.Solid.makeCylinder(12.7/2, 31, start, direction))
                 for label, start, direction in light_datums()]
    xs = sorted({u-b.HALF for u, _ in main_led_datums().values()})
    assert len(xs) == 11
    envelopes.extend((f"routing X={x}", b.block(x-5.5, x+5.5, 0, b.LENGTH, 50, 52)) for x in xs)
    return envelopes


@pytest.mark.parametrize("category", ["parts", "hardware"])
def test_all_selected_parts_and_hardware_clear_reserved_service_space(category, service_envelopes):
    if category == "parts":
        objects = [(p.name, p.shape) for p in frame.parts()]
        assert len(objects) == 87
    else:
        objects = [(c.name, cq.Compound.makeCompound(c.components())) for c in frame.connections()]
        assert len(objects) == 278
    failures = [(name, label, volume) for name, shape in objects for label, envelope in service_envelopes
                if (volume := overlap(shape, envelope)) > .01]
    assert not failures, failures


def bearing_ring(start, direction):
    # Minimum supplied SAE washer OD; unsupported center excludes the larger
    # project wood/steel bore, not merely the smaller washer ID or bolt shank.
    return cq.Solid.makeCylinder(20.447/2, .5, start, direction).cut(
        cq.Solid.makeCylinder(11.1125/2, .5, start, direction))


def assert_full_bearing(ring, member):
    # A positive overlap alone allows almost the entire washer to overhang.
    assert overlap(ring, member) == pytest.approx(ring.Volume(), abs=1e-5)


def test_all_bolt_washers_have_full_minimum_bearing_annuli_in_receiving_bodies():
    assert frame.BOLT_HOLE_DIAMETER_MM == pytest.approx(11.1125)
    parts = {p.name: p.shape for p in frame.parts()}
    bolts = [c for c in frame.connections() if c.kind == "bolt"]
    assert len(bolts) == 114
    checked = 0
    for c in bolts:
        spec = spec_for(c)
        assert isinstance(spec, BoltSpec)
        assert spec.washer_id_max_mm < frame.BOLT_HOLE_DIAMETER_MM < 20.447
        first_plane = c.start+c.direction*spec.washer_thickness_nominal_mm
        last_plane = first_plane+c.direction*c.grip
        for member, plane, inward in ((c.members[0], first_plane, c.direction),
                                       (c.members[-1], last_plane, -c.direction)):
            ring = bearing_ring(plane, inward)
            assert ring.Volume() == pytest.approx(math.pi/4*(20.447**2-11.1125**2)*.5)
            try:
                assert_full_bearing(ring, parts[member])
            except AssertionError as error:
                raise AssertionError(f"Incomplete minimum washer annulus: {c.name}, {member}") from error
            checked += 1
    assert checked == 228  # Actual first/last bodies, never washer/nut solids.


def test_partial_bearing_does_not_pass_from_positive_contact_alone():
    ring = bearing_ring(cq.Vector(0, 0, 0), cq.Vector(0, 0, 1))
    partial = cq.Solid.makeBox(8, 30, 1, cq.Vector(0, -15, 0))
    assert 0 < overlap(ring, partial) < ring.Volume()
    with pytest.raises(AssertionError):
        assert_full_bearing(ring, partial)
