import pytest

from mini_moonboard import compact_spliced_installation as installed


def test_outward_stacks_preserve_structural_interfaces_and_washer_planes():
    original = {c.name:c for c in installed.structural.connections()}
    flipped = []
    for c in installed.connections():
        old = original[c.name]
        if c.kind != 'bolt':
            assert c is old
            continue
        assert c.start.x*c.direction.x > 0
        assert c.grip == old.grip and c.length == old.length
        assert set(c.members) == set(old.members)
        assert (installed.bolt_interface_point(c)-installed.structural.bolt_interface_point(old)).Length < 1e-8
        old_seats = sorted(p.Center().x for p in old.components()[1:3])
        new_seats = sorted(p.Center().x for p in c.components()[1:3])
        assert new_seats == pytest.approx(old_seats)
        assert c.components()[4].Center().x*c.direction.x > c.components()[3].Center().x*c.direction.x
        if c.direction != old.direction:
            flipped.append(c.name)
            assert c.members == tuple(reversed(old.members))
    assert len(flipped) == 16
    assert installed.parts is installed.structural.parts
    assert installed.uncut_wood_parts is installed.structural.uncut_wood_parts
