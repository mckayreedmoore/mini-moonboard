"""Full candidate geometry gates; no strength approval follows from these."""
from itertools import combinations

import cadquery as cq
import pytest

from mini_moonboard import box_frame as b
from mini_moonboard import hybrid_frame as h
from mini_moonboard.box_exports import overlap
from mini_moonboard.panel_grid import main_led_datums, main_tnut_datums


@pytest.mark.parametrize("size",["2x10","2x12"])
def test_solids_and_collisions(size):
    parts=h.parts(size)
    assert len({p.name for p in parts})==len(parts)
    invalid=[p.name for p in parts if not p.shape.isValid() or len(p.shape.Solids())!=1]
    assert not invalid,invalid
    collisions=[(a.name,b.name,overlap(a.shape,b.shape)) for a,b in combinations(parts,2)
                if overlap(a.shape,b.shape)>.01]
    assert not collisions,collisions
    collisions=[(c.name,p.name) for c in h.connections(size) for head in c.components()[1:]
                for p in parts if overlap(head,p.shape)>.01]
    assert not collisions,collisions
    solids=[(c.name,cq.Compound.makeCompound(c.components())) for c in h.connections(size)]
    collisions=[(a,bb) for (a,sa),(bb,sb) in combinations(solids,2) if overlap(sa,sb)>.01]
    assert not collisions,collisions


@pytest.mark.parametrize("size",["2x10","2x12"])
def test_connections_have_receivers_and_connected_graph(size):
    parts={p.name:p.shape for p in h.parts(size)}
    graph={name:set() for name in parts}
    failures=[]
    for c in h.connections(size):
        a,bb=c.members
        graph[a].add(bb)
        graph[bb].add(a)
        if parts[a].distance(parts[bb])>1e-5:
            failures.append((c.name,"gap"))
        probe=cq.Solid.makeCylinder(5.5 if c.kind=="bolt" else 3,c.length,c.start,c.direction)
        for member in c.members:
            if overlap(probe,parts[member])<1:
                failures.append((c.name,"missing receiver",member))
        if c.kind=="screw":
            d=c.direction
            radial=d.cross(cq.Vector(1,0,0))
            if radial.Length<.5:
                radial=d.cross(cq.Vector(0,1,0))
            tip=c.start+d*(c.length-.5)+radial.normalized()*2.5
            if not parts[bb].isInside(tip,1e-5):
                failures.append((c.name,"tip exits"))
        else:
            assert 3<=c.length-c.grip-13<=7
    assert not failures,failures
    seen=set()
    pending=["box_side_left"]
    while pending:
        name=pending.pop()
        if name not in seen:
            seen.add(name)
            pending.extend(graph[name]-seen)
    assert seen==set(parts),set(parts)-seen


def test_new_attachments_keep_original_perimeter_and_add_four_per_panel():
    points=h.panel_attachments()
    assert points[:48]==b.panel_screws()
    assert len(points)==64
    for name in {p for p,_,_ in points}:
        assert len([p for p,_,_ in points if p==name])==16


@pytest.mark.parametrize("size",["2x10","2x12"])
def test_tool_led_and_routing_envelopes(size):
    parts=h.parts(size)
    hardware=[(c.name,cq.Compound.makeCompound(c.components())) for c in h.connections(size)]
    for c in h.connections(size):
        if c.kind!="bolt":
            continue
        # Assumed 36 mm OD socket, 25 mm approach depth, plus straight bolt
        # withdrawal corridor. Actual tools and disassembly sequence still audit.
        envelopes=[cq.Solid.makeCylinder(18,25,c.start-c.direction*6,-c.direction),
                   cq.Solid.makeCylinder(18,25,c.start+c.direction*(c.grip+13),c.direction),
                   cq.Solid.makeCylinder(12.7,c.length+6,c.start,-c.direction)]
        assert not [(p.name,c.name) for p in parts for shape in envelopes
                    if overlap(shape,p.shape)>.01]
        assert not [(name,c.name,i) for name,other in hardware if name!=c.name
                    for i,shape in enumerate(envelopes) if overlap(shape,other)>.01]
    envelopes=[]
    for x,s in main_led_datums().values():
        if s>=0:
            start,d=b.point(x-b.HALF,s,0),b.normal()
        else:
            start,d=cq.Vector(x-b.HALF,-36,b.V1_KICKER_HEIGHT_MM+s),cq.Vector(0,-1,0)
        envelopes.append(cq.Solid.makeCylinder(6.35,31,start,d))
    # Straight 11 x 2 mm routing corridors behind the main backing only.
    # Not a complete kit wiring path or a cable bend-radius verification.
    envelopes.extend(b.block(x-b.HALF-5.5,x-b.HALF+5.5,0,b.LENGTH,50,52)
                     for x in sorted({x for x,_ in main_led_datums().values()}))
    assert not [(p.name,i) for p in parts for i,e in enumerate(envelopes) if overlap(p.shape,e)>.01]
    assert not [(name,i) for name,shape in hardware for i,e in enumerate(envelopes) if overlap(shape,e)>.01]
    # Added panel screws avoid both actual hold bores and backing relief edges.
    for _,x,s in h.panel_attachments()[48:]:
        assert all((x-(bx-b.HALF))**2+(s-bs)**2>=28**2
                   for bx,bs in (*main_tnut_datums().values(),*main_led_datums().values()))


@pytest.mark.parametrize("size",["2x10","2x12"])
def test_floor_and_rib_orientation(size):
    for p in h.parts(size):
        if p.name.startswith("leg_"):
            assert p.laminations==2 and p.blank[2]==pytest.approx(38.1)
            assert p.shape.BoundingBox().zmin==pytest.approx(0,abs=1e-5)
            faces=[f for f in p.shape.Faces() if abs(f.BoundingBox().zmin)<1e-5
                   and abs(f.BoundingBox().zmax)<1e-5]
            assert len(faces)==1 and faces[0].Area()>38.1*180
        if p.name.startswith("rib_"):
            assert any(abs(abs(f.normalAt().dot(b.normal()))-1)<1e-6 for f in p.shape.Faces()
                       if f.geomType()=="PLANE")


@pytest.mark.parametrize("size",["2x10","2x12"])
def test_rib_crossed_bores_retain_recorded_ligament(size):
    tangent=(b.point(0,1,0)-b.point(0,0,0)).normalized()
    for screw in h.connections(size):
        if not (screw.name.startswith("rib_") and screw.name.endswith("_front")):
            continue
        rib=screw.members[1]
        bolts=[c for c in h.connections(size) if c.kind=="bolt" and rib in c.members]
        assert len(bolts)==2
        for bolt in bolts:
            separation=abs((bolt.start-screw.start).dot(tangent))
            assert separation==pytest.approx(54)
            # Regression geometry target, NOT a material-specific safe ligament.
            assert separation-5-screw.diameter/2>46
