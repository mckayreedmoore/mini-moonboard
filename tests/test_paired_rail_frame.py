"""Independent seam-rail ownership and center-base retention geometry."""
from itertools import combinations

import pytest

from mini_moonboard import paired_rail_frame as model
from mini_moonboard.connection_geometry import material_intervals


@pytest.fixture(scope='module')
def candidate():
    return {p.name: p for p in model.wood_parts()}, model.connections()


def test_only_horizontal_seam_members_are_paired(candidate):
    raw, _ = candidate
    seams = [p for name, p in raw.items() if name.startswith('base_rail_mid_')]
    assert {p.name for p in seams} == {
        f'base_rail_mid_{level}_{side}' for level in ('lower', 'upper') for side in ('left', 'right')}
    assert all(p.blank[1:] == (139.7, 38.1) and p.laminations == 1 for p in seams)
    old = {p.name: p for p in model.previous.wood_parts()}
    for name in ('base_principal_center', 'base_post_center', 'base_header'):
        assert raw[name].shape is old[name].shape
    assert len(raw) == len(old)+2
    assert not any(name.startswith('insert_') for name in raw)


def test_each_seam_rail_and_center_base_have_complete_clip_receivers(candidate):
    raw, connections = candidate
    selected = [c for c in connections if c.name.startswith('clip_paired_')]
    assert len(selected) == 54  # Eight seam clips plus one center-base clip, six screws each.
    for c in selected:
        shape = raw[c.members[1]].shape
        material = sum(end-start for start, end in material_intervals(
            shape, c.start, c.direction, 0., c.length))
        assert material == pytest.approx(model.hardware.SDS['gross_penetration_through_nominal_ml24z']), c.name
    for side in ('left', 'right'):
        for level in ('lower', 'upper'):
            name = f'base_rail_mid_{level}_{side}'
            assert sum(c.members[1] == name for c in selected) == 6
    center = [c for c in selected if c.name.startswith('clip_paired_base_center')]
    assert {c.members[1] for c in center} == {'base_header', 'base_principal_center'}
    opposing = [c for c in selected if c.name.startswith('clip_paired_mid_')
                and c.members[1] == 'base_principal_center']
    for first, second in combinations(opposing, 2):
        assert first.components()[0].intersect(second.components()[0]).Volume() < 1e-5


def test_panel_screws_remain_separate_and_centered_on_their_seam_rail(candidate):
    _, connections = candidate
    screws = [c for c in connections if isinstance(c, model.timber.PanelScrew)]
    assert len(screws) == 56
    tangent = (model.b.point(0., 1., 0.)-model.b.point(0., 0., 0.)).normalized()
    seam = [c for c in screws if c.members[1].startswith('base_rail_mid_')]
    assert len(seam) == 8
    for c in seam:
        panel, receiver = c.members
        level = 'lower' if 'lower' in panel else 'upper'
        assert f'_{level}_' in receiver
        s = (c.start-model.b.point(0., 0., 0.)).dot(tangent)
        assert s == pytest.approx(sum(model.SEAM_SPANS[level])/2)
    center_kicker = [c for c in screws if c.members[1] == 'base_post_center']
    assert max(c.start.z for c in center_kicker) == 140.
    top = next(c for c in screws if c.name == 'timber_panel_upper_right_2')
    s = (top.start-model.b.point(0., 0., 0.)).dot(tangent)
    assert model.b.LENGTH-38.1-s == pytest.approx(46.9)
