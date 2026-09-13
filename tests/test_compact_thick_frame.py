"""Current compact-candidate geometry contracts; historical frames remain intact."""
import pytest

from mini_moonboard import compact_thick_frame as model


def test_compact_datums_and_three_complete_stacks_per_leg():
    assert model.KEY == 'compact-thick-development'
    assert model.BOLT_LENGTH_MM == 203.2
    assert model.HEADER_DEPTH == 139.7
    assert model.REAR_OVERHANG_MM == 7.
    assert model.b.V1_KICKER_HEIGHT_MM == 277.
    assert len(model.bolt_points()) == model.BOLT_COUNT_PER_LEG == 3
    bolts = [c for c in model.connections() if isinstance(c, model.CompactLegBolt)]
    assert len(bolts) == 6
    for bolt in bolts:
        assert abs(model.bolt_interface_point(bolt).x) == pytest.approx(model.b.HALF)
    assert len(bolts[0].components()) == 5


def test_actual_flush_rims_shortened_rails_and_base_envelope():
    raw = {p.name:p for p in model.raw_changed_parts()}
    for side, sign in (('left', -1), ('right', 1)):
        bounds = raw['base_side_'+side].shape.BoundingBox()
        assert bounds.xlen == pytest.approx(88.9)
        assert (bounds.xmin if sign < 0 else bounds.xmax) == pytest.approx(sign*model.b.HALF)
        assert bounds.ymin == pytest.approx(model.INCLINED_TRIM_Y)
        assert bounds.zmin == pytest.approx(277.)
    for name,part in raw.items():
        assert part.shape.isValid(), name
        if name.startswith('base_rail_'):
            bounds = part.shape.BoundingBox()
            assert bounds.xmin >= -model.base.INNER_EDGE-1e-6
            assert bounds.xmax <= model.base.INNER_EDGE+1e-6
        if name.startswith('base_post_') or name == 'base_header':
            assert part.shape.BoundingBox().ylen == pytest.approx(139.7)
    assert raw['base_header'].blank[0] == pytest.approx(2438.4)


def test_every_revised_screw_tip_reaches_its_actual_raw_wood_receiver():
    raw = {p.name:p for p in model.raw_changed_parts()}
    checked = set()
    for c in model.connections():
        if c.kind != 'screw':
            continue
        for name in c.members:
            if name not in raw:
                continue
            tip = c.start+c.direction*(c.length-1.)
            assert raw[name].shape.isInside(tip, 1e-5), (c.name, name, tip.toTuple())
            checked.add(name)
    assert set(raw)-{'lumber_leg_left', 'lumber_leg_right'} <= checked


def test_triangle_shift_uses_preserved_centered_pivot_reference():
    points = model.bolt_points()
    offset = sum(points, model.cq.Vector())/3-model.pivot_reference.bolt_points()[0]
    for grain, expected in ((model.axes()[2], -5.), (model.axes()[4], 5.)):
        normal = model.cq.Vector(0., grain.z, -grain.y)
        assert offset.dot(normal) == pytest.approx(expected)
