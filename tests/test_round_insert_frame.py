"""Normal contact preserves rigid motions and cannot tie independent panels."""
import numpy as np
import pytest

from fea import horizontal_panel_frame as frame
from fea import round_insert_frame as insert


def shell():
    model = frame.Structure()
    positions = [(0, 0, 0), (2, 0, 0), (2, 2, 0), (0, 2, 0),
                 (1, 0, 0), (2, 1, 0), (1, 2, 0), (0, 1, 0)]
    ids = [model.node(point) for point in positions]
    model.element('S8', ids, 'left')
    model.panels['left'] = {'nodes': ids}
    return model, ids


def test_contact_interpolation_reproduces_point_and_keeps_panel_ownership():
    model, ids = shell()
    found, weights = insert.panel_interpolation(model, 'left', [0.7, 1.2, 9.125], [0, 0, 1])
    assert found == ids
    assert sum(weights) == pytest.approx(1.)
    assert weights @ np.array([model.nodes[n] for n in ids]) == pytest.approx([0.7, 1.2, 0])
    assert insert.panel_interpolation(model, 'right', [0.7, 1.2, 9.125], [0, 0, 1]) is None
    assert insert.panel_interpolation(model, 'left', [2.1, 1.2, 9.125], [0, 0, 1]) is None


def test_projected_contact_has_no_tangent_stiffness_and_preserves_rigid_motion():
    model, ids = shell()
    point = np.array([0.7, 1.2, 9.125])
    normal = np.array([0., 0., 1.])
    wood = model.node(point)
    _, weights = insert.panel_interpolation(model, 'left', point, normal)
    aux = insert.normal_contact(model, 'seat', wood, ids, weights, point, normal, 1000.)
    assert len(model.springs) == 1
    spring = model.springs[0]
    assert spring['dof'] == 1 and spring['bearing_closed_assumption']
    assert set(aux) <= model.rotation_masters
    assert 'seat' not in frame.next_bearing_set([{
        'name': 'seat', 'active': True, 'opening_mm': .1}])
    # Arbitrary rigid translation/rotation produces equal projected displacement,
    # even though wood contact is behind the shell midsurface.
    translation, rotation = np.array([1., -2., 3.]), np.array([.03, -.07, .05])
    displacements = {n: translation+np.cross(rotation, xyz) for n, xyz in model.nodes.items()}
    for n in aux:
        displacements[n] = np.array([np.dot(displacements[n], normal), 0., 0.])
    for terms in model.equations:
        assert sum(displacements[n][d-1]*v for n, d, v in terms) == pytest.approx(0., abs=1.e-12)
    assert displacements[aux[1]][0]-displacements[aux[0]][0] == pytest.approx(0., abs=1.e-12)
    # Free tangential panel sliding leaves all normal projection equations exact.
    for n in ids:
        displacements[n] += [9., -4., 0.]
    for terms in model.equations:
        assert sum(displacements[n][d-1]*v for n, d, v in terms) == pytest.approx(0., abs=1.e-12)


def test_seam_and_outer_edges_clip_tributary_area_without_double_counting():
    model, _ = shell()
    right = [model.node(np.array(model.nodes[n])+[2., 0., 0.]) for n in model.panels['left']['nodes']]
    model.element('S8', right, 'right')
    model.panels['right'] = {'nodes': right}
    args = (np.array([2., 1., 9.125]), np.array([1., 0., 0.]), np.array([0., 1., 0.]), (-.5, .5), 1.)
    assert insert.tributary_area(model, 'left', *args) == pytest.approx(.5)
    assert insert.tributary_area(model, 'right', *args) == pytest.approx(.5)
    # Half the longitudinal cell lies beyond the outside panel edge.
    assert insert.tributary_area(model, 'left', np.array([0., 1., 9.125]), *args[1:]) == pytest.approx(.5)


def test_receiver_opening_cannot_receive_sampled_seating_force():
    import cadquery as cq

    inward = cq.Vector(0, 0, 1)
    cut = cq.Solid.makeCylinder(6., 17.)
    assert not insert.has_seating_material(cq.Vector(0, 0, 0), inward, [cut])
    assert insert.has_seating_material(cq.Vector(7, 0, 0), inward, [cut])


def test_cached_base_is_source_bound_and_probes_do_not_mutate_it(monkeypatch):
    from types import SimpleNamespace

    class Module:
        timber = SimpleNamespace(PanelScrew=object)
        @staticmethod
        def panel_connections():
            return [SimpleNamespace(name=f'panel_{n}') for n in range(56)]
        @staticmethod
        def bore_records():
            return []

    module = Module()
    calls = []
    fingerprint = {'producer': 'first'}
    monkeypatch.setattr(insert, 'sources', lambda: fingerprint.copy())
    def fresh(*args, **kwargs):
        calls.append(kwargs['hold'])
        model = frame.Structure()
        model.springs = [{'name': 'panel_0', 'stiffness_n_per_mm': 1000.},
                         {'name': 'structural', 'stiffness_n_per_mm': 1000.}]
        return model, {'limits': '', 'nested': [1]}
    monkeypatch.setattr(frame, 'current_frame', fresh)
    insert.base_frame.cache_clear()
    first, metadata = insert.prepare(module, panel_stiffness=100., contact=False)
    metadata['nested'].append(2)
    first.loads[999] = [1, 2, 3]
    second, untouched = insert.prepare(module, panel_stiffness=10000., contact=False)
    assert calls == ['F10']
    assert untouched['nested'] == [1] and not second.loads
    assert second.springs[0]['stiffness_n_per_mm'] == 10000.
    assert second.springs[1]['stiffness_n_per_mm'] == 1000.
    fingerprint['producer'] = 'second'
    insert.prepare(module, contact=False)
    assert calls == ['F10', 'F10']
    insert.base_frame.cache_clear()
