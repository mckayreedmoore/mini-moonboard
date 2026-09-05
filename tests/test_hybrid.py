"""Layout gates, deliberately not structural acceptance tests."""
import math
from itertools import combinations
from pathlib import Path

import cadquery as cq
import pytest

from mini_moonboard import box_frame as base
from mini_moonboard import hybrid
from mini_moonboard.box_exports import overlap


@pytest.mark.parametrize("size,width",[("2x8",184.15),("2x10",234.95),("2x12",285.75)])
def test_layout_geometry_and_leg_hardware(size,width):
    parts={p.name:p for p in hybrid.parts(size)}
    assert len(parts)==11
    assert len(hybrid.leg_bolts(size))==8
    for p in parts.values():
        assert p.shape.isValid() and len(p.shape.Solids())==1,p.name
    for a,b in combinations(parts.values(),2):
        assert overlap(a.shape,b.shape)<.01,(a.name,b.name)
    for side in ("left","right"):
        rim=parts[f"box_side_{side}"]
        assert rim.laminations==1
        ns=[(v.Center()-base.point(0,0,0)).dot(base.normal()) for v in rim.shape.Vertices()]
        assert min(ns)==pytest.approx(-18)
        assert max(ns)==pytest.approx(width-18)
        leg=parts[f"leg_{side}"]
        assert leg.laminations==2 and leg.blank[2]==pytest.approx(38.1)
        floor=[f for f in leg.shape.Faces() if abs(f.BoundingBox().zmin)<1e-5
               and abs(f.BoundingBox().zmax)<1e-5]
        assert len(floor)==1
        assert floor[0].Area()==pytest.approx(38.1*180/math.sin(
            math.radians(hybrid.lower_angle(size))),rel=1e-5)
        ref=base.point(0,1480,base.LEG_NORMAL)
        assert floor[0].Center().y==pytest.approx(ref.y+ref.z/math.tan(math.radians(70)))
        assert leg.shape.distance(rim.shape)<1e-5
        # Top cap has real bearing on the full rim end, not just edge contact.
        top=parts["box_top"].shape
        assert top.intersect(rim.shape.translate((0,0,.001))).Volume()>0
    for c in hybrid.leg_bolts(size):
        for name in c.members:
            probe=cq.Solid.makeCylinder(6,c.length,c.start,c.direction)
            assert overlap(probe,parts[name].shape)>100
        for head in c.components()[1:]:
            assert all(overlap(head,p.shape)<.01 for p in parts.values()),c.name
        assert 3<=c.length-c.grip-4-9<=7
    assert all(overlap(cq.Compound.makeCompound(a.components()),
                       cq.Compound.makeCompound(b.components()))<.01
               for a,b in combinations(hybrid.leg_bolts(size),2))


def test_invalid_size_rejected_and_default_unchanged():
    with pytest.raises(KeyError):
        hybrid.parts("2x6")
    hybrid.leg_bolts("2x12")
    assert base.DEPTH==304.8
    assert base.LEG_NORMAL==214.8
    assert all(c.start==base.point(c.start.x,s,base.LEG_NORMAL)
               for c,s in zip([c for c in base.connections()
                              if c.name.startswith("analysis_leg_wall_bolt_left_")],
                             base.LEG_STATIONS,strict=True))


def test_hybrid_exports_are_fresh(tmp_path):
    hybrid.export(tmp_path)
    committed=Path(__file__).parents[1]/"exports"/"hybrid"
    assert {p.name for p in tmp_path.iterdir()}=={p.name for p in committed.iterdir()}
    for path in tmp_path.iterdir():
        if path.suffix==".step":
            # STEP headers carry timestamps; compare imported physical solids.
            a=cq.importers.importStep(str(path)).val()
            b=cq.importers.importStep(str(committed/path.name)).val()
            assert len(a.Solids())==len(b.Solids())
            assert a.cut(b).Volume()+b.cut(a).Volume()<.01
        else:
            assert path.read_bytes()==(committed/path.name).read_bytes(),path.name
