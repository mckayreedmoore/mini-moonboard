"""Floor rail contacts act locally along the member and retain penalty totals."""
import cadquery as cq
import numpy as np
import pytest

from fea.current_response_model import add_floor_rail, floor_rail_samples
from fea.horizontal_panel_frame import Structure


def test_long_rail_uses_local_sections_not_a_rigid_endpoint_arm():
    shape = cq.Solid.makeBox(38.1, 1700., 139.7)
    samples = floor_rail_samples(shape, (7, 2))
    centre = sum(p*w for p, w in samples)
    np.testing.assert_allclose(centre, [19.05, 850., 0.])
    assert sum(w for _, w in samples) == pytest.approx(1.)
    record = {'name':'base_floor_left', 'start':[19.05, 0., 69.85],
              'end':[19.05, 1700., 69.85], 'section_u':[1., 0., 0.],
              'width_mm':38.1, 'depth_mm':139.7}
    structure = Structure()
    structure.member(record, [p for p, _ in samples]+[centre], 150.)
    first_section = set(structure.members[record['name']]['sections'][0.])
    equation_start = len(structure.equations)
    owners = {}
    add_floor_rail(structure, record['name'], owners, samples, {'floor':100000.})
    # All samples are interior: no artificial transfer to the front endpoint.
    assert not any(n in first_section for terms in structure.equations[equation_start:]
                   for n, _, _ in terms)
    normal = [s for s in structure.springs if not s['name'].endswith('_friction')]
    assert len(normal) == 14
    assert sum(s['stiffness_n_per_mm'] for s in normal) == pytest.approx(400000.)
    assert len([s for s in structure.springs if s['name'].endswith('_friction')]) == 2
    assert len(owners) == 15
    refined = floor_rail_samples(shape, (14, 2))
    assert sum(w*400000. for _, w in refined) == pytest.approx(400000.)


@pytest.mark.parametrize('grid', [(1, 2), (7, True), (7, 2.5), (7,), 7])
def test_invalid_grid_rejected(grid):
    with pytest.raises(ValueError, match='two integers'):
        floor_rail_samples(cq.Solid.makeBox(38.1, 1700., 139.7), grid)


def test_raised_rail_does_not_receive_fictional_floor_support():
    shape = cq.Solid.makeBox(38.1, 1700., 139.7, cq.Vector(0., 0., 1.))
    with pytest.raises(ValueError, match='at Z=0'):
        floor_rail_samples(shape, (7, 2))


def test_kicker_edge_cutout_removes_stiffness_mass_and_corner_contact_nodes():
    from fea.current_response_model import (
        add_panel_floor,
        cut_panel_mesh,
        retained_panel_weights,
    )
    from fea.horizontal_panel_frame import panel_kernel

    bounds = (-1219.2, 0., 0., 277.)
    cutout = (-1219.2, -1179.1, 0., 141.7)
    xs = panel_kernel.mesh_axes(bounds[0], bounds[1], 120., [-1179.1, -1162.05])
    ys = panel_kernel.mesh_axes(bounds[2], bounds[3], 120., [60., 141.7, 192.])
    local, elements, lookup = cut_panel_mesh(xs, ys, [cutout], [(-1162.05, 60.)])
    assert set(local) == {n for ids in elements.values() for n in ids}
    assert set(lookup.values()) == set(local)
    assert (-1219.2, 0.) not in lookup
    weights, area = retained_panel_weights(local, elements)
    expected = 1219.2*277.-40.1*141.7
    assert area == pytest.approx(expected)
    assert sum(weights.values()) == pytest.approx(1.)
    np.testing.assert_allclose(sum(np.array(local[n])*w for n, w in weights.items())[:2],
        [(1219.2*277.*(-609.6)-40.1*141.7*(-1199.15))/expected,
         (1219.2*277.*138.5-40.1*141.7*70.85)/expected])
    structure = Structure()
    tags = [structure.node((x, 0., z)) for x, z, _ in local.values()]
    structure.panels['kicker_left'] = {'nodes':tags}
    ownership = {}
    add_panel_floor(structure, 'kicker_left', ownership, 100000.)
    assert ownership
    assert all(row['point'][0] >= -1179.1-1.e-7 for row in ownership.values())
    with pytest.raises(ValueError, match='attachment lies'):
        cut_panel_mesh(xs, ys, [cutout], [(-1219.2, 60.)])


def test_panel_cutout_requires_exact_edge_imprint():
    from fea.current_response_model import cut_panel_mesh

    with pytest.raises(ValueError, match='imprinted'):
        cut_panel_mesh([0., 100.], [0., 100.], [(0., 40., 0., 50.)])
    with pytest.raises(ValueError, match='reach a panel edge'):
        cut_panel_mesh([0., 50., 100.], [0., 50., 100.], [(20., 50., 20., 50.)])
