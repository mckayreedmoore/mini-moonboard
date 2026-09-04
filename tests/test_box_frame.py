"""Physical invariants for the box revision, independent of display offsets."""
import math
from itertools import combinations, pairwise

import cadquery as cq
import pytest

from mini_moonboard.box_exports import collisions, overlap
from mini_moonboard.box_frame import (
    DEPTH,
    HALF,
    LENGTH,
    THICKNESS,
    connections,
    frame_parts,
    normal,
    panel_screws,
    point,
)


def test_laminated_stock_and_depth():
    assert THICKNESS == pytest.approx(2*0.75*25.4)
    assert DEPTH == pytest.approx(12*25.4)
    for p in frame_parts():
        assert p.shape.isValid(),p.name
        assert len(p.shape.Solids())==1,p.name
        if p.laminations==2:
            assert p.blank[2] == pytest.approx(38.1),p.name
        if p.name.startswith("leg_"):
            assert p.shape.BoundingBox().xlen == pytest.approx(38.1)
        if p.name.startswith("box_side_"):
            ns=[(v.Center()-point(0,0,0)).dot(normal()) for v in p.shape.Vertices()]
            assert max(ns)==pytest.approx(DEPTH)
            assert min(ns)==pytest.approx(-18)
    tangent=(point(0,LENGTH,0)-point(0,0,0)).normalized()
    assert math.degrees(math.acos(tangent.z))==pytest.approx(40)


def test_no_unintended_timber_or_fastener_head_collisions():
    for a,b in combinations(frame_parts(),2):
        assert overlap(a.shape,b.shape)<.01,(a.name,b.name)
    assert not collisions(),collisions()


def test_floor_bearing_is_full_width_and_level():
    for p in frame_parts():
        if not p.name.startswith("leg_"):
            continue
        assert p.shape.BoundingBox().zmin==pytest.approx(0,abs=1e-5)
        faces=[f for f in p.shape.Faces() if abs(f.BoundingBox().zmin)<1e-5 and abs(f.BoundingBox().zmax)<1e-5]
        assert sum(f.Area() for f in faces)==pytest.approx(THICKNESS*180/math.cos(math.radians(20)),rel=1e-5)


def test_each_panel_has_regular_supported_perimeter_including_top():
    screws=panel_screws()
    assert len(screws)==96
    for panel in {p for p,_,_ in screws}:
        row=0 if "lower" in panel else 1
        col=0 if "left" in panel else 1
        pts=[(x+HALF-col*HALF,s-row*HALF) for p,x,s in screws if p==panel]
        assert len(set(pts))==24
        for axis in (0,1):
            for edge in (25,HALF-25):
                along=sorted(p[1-axis] for p in pts if abs(p[axis]-edge)<1e-5)
                assert len(along)==(5 if axis==0 else 7),(panel,axis,edge)
                assert max(b-a for a,b in pairwise(along))<=250


def test_each_connection_enters_named_members_with_contained_tip():
    parts={p.name:p.shape for p in frame_parts()}
    for c in connections():
        direction=c.direction.normalized()
        # The drilled bore is empty: test a small annular envelope outside
        # the hole to verify real receiving timber, not just coincident axes.
        radius=5.5 if c.kind=="bolt" else 3.0
        probe=cq.Solid.makeCylinder(radius,c.length,c.start,direction)
        for name in c.members:
            assert probe.intersect(parts[name]).Volume()>1,(c.name,name)
        assert parts[c.members[0]].distance(parts[c.members[1]])<1e-5,(c.name,"joint gap")
        if c.kind=="screw":
            tip=c.start+direction*(c.length-.5)+cq.Vector(0,0,0)
            # Tip plus radial offset lies in receiving material around pilot.
            perpendicular=direction.cross(cq.Vector(1,0,0))
            if perpendicular.Length<.5:
                perpendicular=direction.cross(cq.Vector(0,1,0))
            assert parts[c.members[-1]].isInside(tip+perpendicular.normalized()*2.5,1e-5),(c.name,"tip exits receiver")
        else:
            assert 3 <= c.length-(c.grip+4+9) <= 7,c.name
