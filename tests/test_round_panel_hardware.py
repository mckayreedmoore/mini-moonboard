"""Nominal SPAX head angle, flush seating and matching panel recess."""
from math import atan, degrees, pi

import cadquery as cq
import pytest

from mini_moonboard import round_panel_hardware as hardware
from mini_moonboard import timber_frame as timber


def test_corrected_head_is_90_degrees_and_stays_flush():
    screw = hardware.CountersunkPanelScrew('coupon', cq.Vector(0, 0, 0), cq.Vector(0, 0, 1),
                                           50.8, 4.1402, ('panel', 'receiver'))
    shaft, head = screw.components()
    assert isinstance(screw, timber.PanelScrew)
    assert 2*degrees(atan((hardware.HEAD_DIAMETER_MM-hardware.SHANK_DIAMETER_MM)/(2*hardware.HEAD_HEIGHT_MM))) == pytest.approx(90.)
    bounds = head.BoundingBox()
    assert bounds.zmin == pytest.approx(0.)
    assert bounds.zmax == pytest.approx(2.6035)
    assert bounds.xlen == pytest.approx(8.128)
    assert shaft.BoundingBox().zmax == pytest.approx(50.8)
    assert screw.length-hardware.NOMINAL_THREAD_LENGTH_MM == pytest.approx(19.304)


def test_panel_recess_matches_the_head_and_shank_without_major_diameter_overcut():
    screw = hardware.CountersunkPanelScrew('coupon', cq.Vector(0, 0, 0), cq.Vector(0, 0, 1),
                                           50.8, 4.1402, ('panel', 'receiver'))
    thickness = timber.product.FACE_THICKNESS_MM
    coupon = cq.Solid.makeBox(20., 20., thickness, cq.Vector(-10., -10., 0.))
    shaft, head = screw.components()
    cut = coupon.cut(shaft).cut(head).clean()
    expected = head.Volume()+pi*(hardware.SHANK_DIAMETER_MM/2)**2*(thickness-hardware.HEAD_HEIGHT_MM)
    assert coupon.Volume()-cut.Volume() == pytest.approx(expected)
    assert thickness-hardware.HEAD_HEIGHT_MM == pytest.approx(15.65275)
    assert cut.intersect(head).Volume() < 1e-6
    assert cut.isValid() and len(cut.Solids()) == 1
