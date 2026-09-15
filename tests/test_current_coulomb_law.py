"""Finite friction vanishes with pressure and is audited from actual slip."""
import numpy as np
import pytest

from fea.current_coulomb_run import coulomb_secant, floor_law_check


def test_elastic_stick_and_circular_slip_limit():
    force, stiffness = coulomb_secant([.001, .002], 1000., .4, 100000.)
    np.testing.assert_allclose(force, [-100., -200.])
    assert stiffness == 100000.
    force, stiffness = coulomb_secant([3., 4.], 1000., .4, 100000.)
    np.testing.assert_allclose(force, [-240., -320.])
    assert stiffness == 80.
    assert np.dot(force, [3., 4.]) < 0  # Always oppose relative motion.


def test_tangential_force_continuously_vanishes_when_normal_reaction_vanishes():
    for normal in (1., .001, .000001, 0.):
        force, _ = coulomb_secant([1., -2.], normal, .4, 100000.)
        assert np.linalg.norm(force) == pytest.approx(.4*normal, abs=1.e-15)
    force, stiffness = coulomb_secant([0., 0.], 0., .4, 100000.)
    np.testing.assert_array_equal(force, [0., 0.])
    assert stiffness == 0.


def test_force_audit_rejects_surviving_tangent_on_open_foot(monkeypatch):
    from fea import current_coulomb_run as runner

    name, body = 'floor_leg_friction', 'leg'
    record = {'springs':[{'name':name, 'nodes':[1,2], 'dof':dof} for dof in (1,2)]}
    monkeypatch.setattr(runner.base.frame.panel_kernel, 'read_blocks',
        lambda data: {'displacements':{1:[.1,0.,0.], 2:[0.,0.,0.]}})
    report = {'physical_connection_forces':{
        name:{'first':body,'second':'floor','force_on_first_xyz_n':[-10.,0.,0.],
              'force_rounding_radius_xyz_n':[0.,0.,0.], 'normal_contact':'normal', 'point':[0.,0.,0.]},
        'normal':{'first':body,'second':'floor','scalar_normal':[0.,0.,1.],
                  'force_on_first_xyz_n':[0.,0.,0.], 'point':[0.,0.,0.]}}}
    result = floor_law_check(record, '', report, .4, {name:100000.})
    assert not result['passed']
    assert result['feet'][name]['state'] == 'open'
    assert result['feet'][name]['force_residual_n'] == 10.
    report['physical_connection_forces'][name]['force_on_first_xyz_n'] = [0.,0.,0.]
    assert floor_law_check(record, '', report, .4, {name:100000.})['passed']


@pytest.mark.parametrize('normal,mu,stiffness', [(-1.,.4,100.), (1.,0.,100.),
                                               (1.,.4,0.), (float('nan'),.4,100.)])
def test_invalid_friction_basis_rejected(normal, mu, stiffness):
    with pytest.raises(ValueError):
        coulomb_secant([0.,0.], normal, mu, stiffness)


def test_tangent_seed_preserves_physical_elastic_constants_and_exact_inventory():
    from fea.current_coulomb_run import validate_secant_seed

    elastic = {'left':100000., 'right':100000.}
    assert validate_secant_seed({'left':0.,'right':150.},elastic) == {'left':0.,'right':150.}
    assert elastic == {'left':100000.,'right':100000.}
    for invalid in ({'left':1.}, {'left':-1.,'right':1.}, {'left':100001.,'right':1.},
                    {'left':float('nan'),'right':1.}):
        with pytest.raises(ValueError,match='Tangent seeds'):
            validate_secant_seed(invalid,elastic)


def test_distributed_tangents_replace_centroid_and_share_each_normal_point():
    import cadquery as cq

    from fea.current_coulomb_run import distribute_floor_tangents
    from fea.current_response_model import add_member_floor
    from fea.horizontal_panel_frame import Structure

    structure = Structure()
    name = 'base_post_fixture'
    record = {'name':name, 'start':[20.,20.,0.], 'end':[20.,20.,100.],
              'section_u':[1.,0.,0.], 'width_mm':40., 'depth_mm':40.}
    structure.member(record)
    owners = {}
    add_member_floor(structure,name,owners,cq.Solid.makeBox(40.,40.,100.),{'floor':100000.})
    original_ids = {r['element'] for r in structure.springs if r['name'].endswith('_friction')}
    original_max = max(structure.elements)
    metadata = {'connection_ownership':owners}
    cells = distribute_floor_tangents(structure,metadata)
    assert len(cells) == 4
    assert f'floor_{name}_friction' not in owners
    assert not original_ids & structure.elements.keys()
    assert sum(row['elastic_tangent_n_per_mm'] for row in cells.values()) == pytest.approx(100000.)
    tangent_springs = [row for row in structure.springs if row['name'] in cells]
    assert len(tangent_springs) == 8
    assert all(row['element'] > original_max for row in tangent_springs)
    for tangent, cell in cells.items():
        assert owners[tangent]['point'] == owners[cell['normal_contact']]['point']
        assert structure.nodes[cell['wood_node']] == owners[tangent]['point']
        assert cell['ground_node'] in structure.fixed
    assert len({row['group'] for row in structure.springs}) == len(structure.springs)
