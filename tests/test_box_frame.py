"""Physical invariants for the box revision, independent of display offsets."""
import math
from itertools import combinations, pairwise

import cadquery as cq
import pytest

from mini_moonboard.box_exports import collisions, overlap, sheet_layout
from mini_moonboard.box_frame import (
    DEPTH,
    HALF,
    LENGTH,
    SCREW_EDGE,
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
    assert len(screws)==48
    for panel in {p for p,_,_ in screws}:
        row=0 if "lower" in panel else 1
        col=0 if "left" in panel else 1
        pts=[(x+HALF-col*HALF,s-row*HALF) for p,x,s in screws if p==panel]
        assert len(set(pts))==12
        assert all((u,v) in pts for u in (SCREW_EDGE,HALF-SCREW_EDGE) for v in (SCREW_EDGE,HALF-SCREW_EDGE))
        for axis in (0,1):
            for edge in (SCREW_EDGE,HALF-SCREW_EDGE):
                along=sorted(p[1-axis] for p in pts if abs(p[axis]-edge)<1e-5)
                assert len(along)==4
                assert max(b-a for a,b in pairwise(along))<=450


def test_kicker_has_four_per_long_edge_and_shared_end_corners():
    for side,col in (("left",0),("right",1)):
        screws=[c for c in connections() if c.name.startswith(f"analysis_kicker_screw_{side}_")]
        pts={(round(c.start.x+HALF-col*HALF,6),c.start.z) for c in screws}
        assert len(screws)==len(pts)==8
        assert all((round(x,6),z) in pts for x in (25,HALF-25) for z in (25,200))
        assert all(sum(z==edge for x,z in pts)==4 for edge in (25,200))
        assert all(sum(abs(x-edge)<1e-5 for x,z in pts)==2 for edge in (25,HALF-25))


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


def test_sheet_layout_accounts_for_all_layers_without_overlap():
    rows=sheet_layout()
    assert len(rows)==sum(p.laminations for p in frame_parts())
    assert len({(r[2],r[3]) for r in rows})==len(rows)
    for sheet,thickness,name,layer,x,y,w,h,kerf in rows:
        assert x>=0 and y>=0 and x+w<=1219.2+1e-5 and y+h<=2438.4+1e-5,name
        assert thickness in (18,19.05)
    for a,b in combinations(rows,2):
        if a[0]!=b[0]:
            continue
        assert a[1]==b[1]
        _,_,_,_,ax,ay,aw,ah,k=a
        _,_,_,_,bx,by,bw,bh,_=b
        assert ax+aw+k<=bx+1e-5 or bx+bw+k<=ax+1e-5 or ay+ah+k<=by+1e-5 or by+bh+k<=ay+1e-5,(a[2],b[2])


def test_all_parts_have_a_declared_fastened_path_to_the_frame():
    graph={p.name:set() for p in frame_parts()}
    for c in connections():
        a,b=c.members
        graph[a].add(b)
        graph[b].add(a)
    seen=set()
    pending=["box_side_left"]
    while pending:
        name=pending.pop()
        if name not in seen:
            seen.add(name)
            pending.extend(graph[name]-seen)
    assert seen==set(graph),set(graph)-seen


def test_both_fasteners_in_a_reported_collision_are_flagged(monkeypatch):
    from mini_moonboard import box_exports
    a,b=connections()[:2]
    monkeypatch.setattr(box_exports,"collisions",lambda:((a.name,"other fastener",b.name,1.),))
    assert box_exports.metadata(a.name)["clearance_status"].startswith("FAIL")
    assert box_exports.metadata(b.name)["clearance_status"].startswith("FAIL")
