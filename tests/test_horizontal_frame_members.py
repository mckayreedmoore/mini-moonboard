"""Small synthetic CAD checks; no full-frame generation or solver needed."""
from types import SimpleNamespace

import cadquery as cq
import pytest

from fea.horizontal_frame_members import member_record


def test_service_pocket_reduces_section_and_moves_centroid():
    blank = cq.Solid.makeBox(38.1, 139.7, 1000.)
    pocket = cq.Solid.makeBox(40., 50., 40., cq.Vector(-1., 0., 450.))
    part = SimpleNamespace(name='test_rail', shape=blank.cut(pocket))
    row = member_record(part, cq.Vector(0, 0, 1), cq.Vector(1, 0, 0))
    assert row['width_mm'] == pytest.approx(38.1, abs=1.e-4)
    assert row['depth_mm'] == pytest.approx(89.7, abs=1.e-4)
    assert row['section_centroid_shift_v_mm'] == pytest.approx(25., abs=1.e-4)
    assert row['retained_prism_outside_wood_mm3'] < 1.e-3
    assert not row['qualified_for_design']


def test_cut_through_rear_face_cannot_silently_use_gross_section():
    blank = cq.Solid.makeBox(38.1, 139.7, 1000.)
    cut = cq.Solid.makeBox(40., 140., 40., cq.Vector(-1., 0., 450.))
    part = SimpleNamespace(name='severed_rail', shape=blank.cut(cut))
    with pytest.raises(ValueError, match='no constant rear rectangle'):
        member_record(part, cq.Vector(0, 0, 1), cq.Vector(1, 0, 0))
