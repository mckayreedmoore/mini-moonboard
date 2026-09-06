"""Independent-ply CAD preflight only; no strength or load-sharing evidence."""

import math

import cadquery as cq
import pytest

from mini_moonboard import box_frame as b
from mini_moonboard import footprint_frame as frame


@pytest.mark.parametrize("side, sign", [("left", -1), ("right", 1)])
def test_drilled_foot100_independent_ply_geometry(side, sign):
    parts = {part.name: part.shape for part in frame.parts(100, drilled=True)}
    leg = parts[f"leg_{side}"]
    rim = parts[f"box_side_{side}"]
    bounds = leg.BoundingBox()
    thickness = b.THICKNESS / 2
    split_x = sign * (b.HALF + 1.5 * b.THICKNESS)
    assert bounds.xlen == pytest.approx(2 * thickness)
    assert (bounds.xmin + bounds.xmax) / 2 == pytest.approx(split_x)

    plies = []
    for x0 in (bounds.xmin, split_x):
        clip = cq.Solid.makeBox(
            thickness, bounds.ylen + 2, bounds.zlen + 2,
            cq.Vector(x0, bounds.ymin - 1, bounds.zmin - 1),
        )
        ply = leg.intersect(clip)
        assert ply.isValid() and len(ply.Solids()) == 1
        assert ply.BoundingBox().xlen == pytest.approx(thickness)
        assert ply.Volume() == pytest.approx(leg.Volume() / 2, abs=.01)
        plies.append(ply)

        floors = [face for face in ply.Faces()
                  if abs(face.BoundingBox().zmin) < 1e-5
                  and abs(face.BoundingBox().zmax) < 1e-5]
        assert len(floors) == 1
        floor = floors[0]
        assert floor.geomType() == "PLANE"
        assert floor.Area() == pytest.approx(
            thickness * b.V1_SUPPORT_WIDTH_MM
            / math.sin(math.radians(frame.lower_angle(100)))
        )
        assert floor.Center().toTuple() == pytest.approx(
            (x0 + thickness / 2, frame.foot_center(100).y, 0), abs=1e-5
        )

        bolts = [c for c in frame.connections()
                 if f"leg_{side}" in c.members]
        assert len(bolts) == 4
        for bolt in bolts:
            assert bolt.kind == "bolt"
            assert bolt.direction.toTuple() == pytest.approx((sign, 0, 0))
            assert bolt.diameter == pytest.approx(9.525)
            start = cq.Vector(x0, bolt.start.y, bolt.start.z)
            bore = cq.Solid.makeCylinder(5, thickness, start, cq.Vector(1, 0, 0))
            surround = cq.Solid.makeCylinder(6, thickness, start, cq.Vector(1, 0, 0))
            assert ply.intersect(bore).Volume() < .01
            # A full annulus proves the bore crosses this ply inside wood,
            # rather than merely missing it or breaking out through an edge.
            assert ply.intersect(surround).Volume() == pytest.approx(
                math.pi * (6**2 - 5**2) * thickness, abs=.01
            )

    assert sum(ply.Volume() for ply in plies) == pytest.approx(leg.Volume(), abs=.01)
    assert plies[0].intersect(plies[1]).Volume() < .01
    reconstructed = plies[0].fuse(plies[1])
    assert reconstructed.cut(leg).Volume() < .01
    assert leg.cut(reconstructed).Volume() < .01

    inner, outer = plies if sign == 1 else reversed(plies)
    assert inner.intersect(rim).Volume() < .01
    assert inner.distance(rim) == pytest.approx(0, abs=1e-5)
    assert outer.distance(rim) == pytest.approx(thickness, abs=1e-5)
