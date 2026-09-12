"""Check additive product/receiver geometry without a full assembly export."""
import pytest

from mini_moonboard import kicker_header_reinforcement as revision


def test_adds_ten_product_identical_screws_without_replacing_predecessor():
    previous = revision.previous.panel_connections()
    assert len(previous) == 56
    assert revision.panel_connections()[:56] == previous
    assert len(revision.panel_connections()) == 66
    assert len({c.name for c in revision.connections()}) == len(revision.connections())
    for side in ('left', 'right'):
        assert sum(c.members[0] == 'kicker_'+side for c in revision.panel_connections()) == 9
    for c in revision.added_connections():
        assert c.length == 50.8
        assert c.diameter == 4.1402
        assert c.direction.toTuple() == (0., -1., 0.)
        assert c.members[1] == 'base_header'


def test_nominal_new_axes_and_full_embedded_cylinders_fit_header():
    base = revision.previous.base
    for c in revision.added_connections():
        radius = c.diameter/2
        assert c.start.z-radius > base.HEADER_BOTTOM
        assert c.start.z+radius < base.HEADER_TOP
        assert min(c.start.z-base.HEADER_BOTTOM, base.HEADER_TOP-c.start.z) == pytest.approx(19.05)
        assert abs(c.start.x)+radius < revision.previous.b.HALF
        tip = c.start+c.direction*c.length
        assert base.HEADER_FRONT_Y-revision.previous.HEADER_DEPTH < tip.y < base.HEADER_FRONT_Y
        assert base.HEADER_FRONT_Y-tip.y == pytest.approx(32.54375)


def test_header_patch_rejects_incomplete_assembly():
    with pytest.raises(ValueError, match='header and both'):
        revision.cut_added_connections([])
