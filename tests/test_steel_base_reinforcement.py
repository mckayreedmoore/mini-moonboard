import pytest

from mini_moonboard import round_structural_frame as original
from mini_moonboard import steel_base_reinforcement as candidate


def test_candidate_only_replaces_outer_base_connections_and_preserves_legs():
    before = {c.name: c for c in original.connections()}
    after = {c.name: c for c in candidate.connections()}
    removed = set(before)-set(after)
    assert len(removed) == 12
    assert all(name.startswith('clip_angle_base_') for name in removed)
    assert len(set(after)-set(before)) == 16
    assert all(after[name] == before[name] for name in set(after)&set(before))
    assert sum(c.name.startswith('lumber_leg_bolt_') for c in after.values()) == 8
    assert candidate.KEY != original.KEY


def test_new_header_axes_keep_conservative_four_diameter_edge_margin():
    bolts = [c for c in candidate.added_connections() if 'header_' in c.name]
    rear = original.base.HEADER_FRONT_Y-original.HEADER_DEPTH
    for c in bolts:
        assert min(c.start.y-rear, original.base.HEADER_FRONT_Y-c.start.y) >= 4*c.diameter
        assert original.b.HALF-abs(c.start.x) >= 7*c.diameter


def test_trimmed_rims_keep_upper_vertices_and_baseline_end_geometry():
    before = {p.name: p.shape for p in original.wood_parts()}
    after = {p.name: p.shape for p in candidate.wood_parts()}
    for side in ('left', 'right'):
        name = 'base_side_'+side
        assert before[name].BoundingBox().zmin == pytest.approx(225.)
        assert after[name].BoundingBox().zmin == pytest.approx(234.525)
        assert after[name].BoundingBox().zmax == pytest.approx(before[name].BoundingBox().zmax)
        assert after[name].Volume() < before[name].Volume()
    assert after['base_header'].Volume() == pytest.approx(before['base_header'].Volume())


def test_new_bolt_stack_uses_inspectable_hex_head_and_nut():
    components = candidate.added_connections()[0].components()
    assert len(components) == 5
    assert sum(f.geomType() == 'PLANE' for f in components[3].Faces()) == 8
    assert sum(f.geomType() == 'PLANE' for f in components[4].Faces()) == 8
