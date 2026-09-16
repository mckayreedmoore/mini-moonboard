"""Full-stock inclined ends must retain geometry and interpolate local motion."""
import copy
import pickle
from itertools import product
from types import SimpleNamespace

import numpy as np
import pytest

from fea import current_response_model as base
from fea.floor_recess_mesh import shape20
from fea.floor_taper_mesh import locate, mapped
from fea.floor_uncut_mesh import UncutStructure, panel_offset_weights, prepare_uncut


def record():
    grain = np.array([0., .6, .8])
    normal = np.array([0., .8, -.6])
    # Independent polygon area/centroid; bottom is a full horizontal bevel.
    points = np.array([[0., 0.], [25., 0.], [100., 100.], [95., 110.], [72., 96.]])
    nxt = np.roll(points, -1, axis=0)
    cross = points[:, 0]*nxt[:, 1]-nxt[:, 0]*points[:, 1]
    area = cross.sum()/2
    centroid = ((points+nxt)*cross[:, None]).sum(axis=0)/(6*area)
    return {'name': 'leg', 'start': [0., 0., 0.], 'end': (grain*150).tolist(),
        'axis': grain.tolist(), 'section_u': [1., 0., 0.],
        'section_v': (-normal).tolist(), 'width_mm': 4., 'depth_mm': 20.,
        'uncut_prism_geometry': {'side_profile_yz_mm': points.tolist(),
            'x_bounds_mm': [-2., 2.], 'expected_volume_mm3': 4*area,
            'expected_centroid_xyz_mm': [0., *centroid]}}


def offset_fixture():
    item = record(); structure = UncutStructure({})
    structure.member(item, size=35.)
    member = structure.members['leg']
    outer_q = max(cell['q_mm'][1] for cell in member['floor_taper_cells'])
    cell = next(cell for cell in member['floor_taper_cells']
                if cell['q_mm'][1] == outer_q)
    anchor = mapped(cell, [.2, 1., .1], member['axis'], member['floor_taper_normal'])
    direction = -member['floor_taper_normal']
    point = anchor-direction*base.panel_kernel.THICKNESS/2
    spec = {'name': 'panel_screw_test', 'point_xyz_mm': point.tolist(),
            'anchor_xyz_mm': anchor.tolist(), 'direction_xyz': direction.tolist()}
    item['panel_midsurface_offsets'] = [spec]
    return structure, spec


def test_beveled_prism_volume_centroid_positive_jacobian_and_affine_recovery():
    item = record(); structure = UncutStructure({})
    structure.member(item, [(1., 42., 55.)], size=35.)
    member = structure.members['leg']
    integrated = 0.; moment = np.zeros(3)
    for cell in member['floor_taper_cells']:
        xyz = np.array([structure.nodes[n] for n in structure.elements[cell['element']][1]])
        for point in product((-1/np.sqrt(3), 1/np.sqrt(3)), repeat=3):
            point = np.array(point)
            derivative = np.column_stack([(shape20(point+delta*1.e-6)-shape20(point-delta*1.e-6))/2.e-6
                                           for delta in np.eye(3)])
            determinant = np.linalg.det(xyz.T@derivative)
            assert determinant > 0
            integrated += determinant
            moment += (shape20(point)@xyz)*determinant
    expected = item['uncut_prism_geometry']
    assert integrated == pytest.approx(expected['expected_volume_mm3'], rel=1.e-8)
    assert moment/integrated == pytest.approx(expected['expected_centroid_xyz_mm'], abs=1.e-7)
    cells = member['floor_taper_cells']
    first_strip = [c for c in cells if c['q_mm'] == cells[0]['q_mm']]
    across = next(c for c in cells if c['q_mm'] != cells[0]['q_mm'])
    first_nodes = set(structure.elements[cells[0]['element']][1])
    for neighbor in (first_strip[1], across):
        assert len(first_nodes & set(structure.elements[neighbor['element']][1])) == 8
    matrix = np.array([[1., 2., 3.], [0., -.5, .2], [1., -.2, 0.]])
    offset = np.array([4., 5., 6.])
    for point in ((0., 12.5, 0.), (-2., 0., 0.), (2., 100., 100.), (1., 42., 55.)):
        ids, weights = locate(structure, 'leg', point)
        field = np.array([matrix@structure.nodes[n]+offset for n in ids])
        assert weights@field == pytest.approx(matrix@point+offset, abs=1.e-8)
    structure.attachment('leg', [.3, 11., 0.])
    assert len(structure.equations) == 3
    assert all(len(equation) > 2 for equation in structure.equations)
    assert 69.2 in member['record']['additional_recovery_stations_mm']
    restored = pickle.loads(pickle.dumps(structure))
    assert type(restored) is UncutStructure
    with pytest.raises(ValueError, match='outside'):
        restored.attachment('leg', [0., 40., 0.])


def test_prism_rejects_cad_volume_or_centroid_mismatch():
    item = record()
    for key in ('expected_volume_mm3', 'expected_centroid_xyz_mm'):
        bad = copy.deepcopy(item)
        if key == 'expected_volume_mm3':
            bad['uncut_prism_geometry'][key] += 1.
        else:
            bad['uncut_prism_geometry'][key][1] += 1.
        with pytest.raises(ValueError, match='differs from actual CAD'):
            UncutStructure({}).member(bad)


def test_named_panel_offset_recovers_rigid_translation_and_rotation():
    structure, spec = offset_fixture()
    ids, matrices = panel_offset_weights(structure, 'leg', spec)
    xyz = np.asarray([structure.nodes[node] for node in ids])
    point = np.asarray(spec['point_xyz_mm'])
    translation = np.array([2.3, -4.1, 7.2])
    omega = np.array([.013, -.021, .034])
    nodal_motion = translation+np.cross(omega, xyz)

    assert np.sum(matrices@nodal_motion[..., None], axis=0).ravel() == pytest.approx(
        translation+np.cross(omega, point), abs=1.e-11)


def test_named_panel_offset_preserves_force_and_moment_resultants():
    structure, spec = offset_fixture()
    ids, matrices = panel_offset_weights(structure, 'leg', spec)
    xyz = np.asarray([structure.nodes[node] for node in ids])
    point = np.asarray(spec['point_xyz_mm'])
    force = np.array([123.4, -56.7, 89.])
    nodal_forces = np.asarray([matrix.T@force for matrix in matrices])

    assert nodal_forces.sum(axis=0) == pytest.approx(force, abs=1.e-11)
    assert np.cross(xyz, nodal_forces).sum(axis=0) == pytest.approx(
        np.cross(point, force), abs=1.e-8)


def test_only_exact_named_panel_offset_accepts_an_outside_point():
    structure, spec = offset_fixture()
    tag = structure.attachment('leg', spec['point_xyz_mm'])
    assert structure.nodes[tag] == pytest.approx(spec['point_xyz_mm'])
    assert len(structure.equations) == 3

    structure.members['leg']['record']['panel_midsurface_offsets'] = []
    with pytest.raises(ValueError, match='outside'):
        structure.attachment('leg', spec['point_xyz_mm'])


@pytest.mark.parametrize('bad', [
    {},
    {'name': '', 'point_xyz_mm': [0., 0., 0.], 'anchor_xyz_mm': [0., 0., 0.],
     'direction_xyz': [0., 0., 1.]},
    {'name': 'bad', 'point_xyz_mm': [0.], 'anchor_xyz_mm': [0., 0., 0.],
     'direction_xyz': [0., 0., 1.]},
    {'name': 'bad', 'point_xyz_mm': [0., 0., np.nan], 'anchor_xyz_mm': [0., 0., 0.],
     'direction_xyz': [0., 0., 1.]},
])
def test_malformed_panel_offset_registrations_are_rejected(bad):
    structure, spec = offset_fixture()
    structure.members['leg']['record']['panel_midsurface_offsets'] = [bad]
    with pytest.raises(ValueError, match='Malformed panel midsurface registration'):
        structure.attachment('leg', spec['point_xyz_mm'])


def test_duplicate_panel_offset_registrations_are_rejected():
    structure, spec = offset_fixture()
    structure.members['leg']['record']['panel_midsurface_offsets'] = [spec, dict(spec)]
    with pytest.raises(ValueError, match='Ambiguous registered panel midsurface point'):
        structure.attachment('leg', spec['point_xyz_mm'])


@pytest.mark.parametrize('key,value', [
    ('anchor_xyz_mm', [0., 0., 0.]),
    ('direction_xyz', [1., 0., 0.]),
])
def test_named_panel_offset_registration_must_reach_actual_face(key, value):
    structure, spec = offset_fixture()
    spec[key] = value
    with pytest.raises(ValueError, match='must meet its actual timber face'):
        structure.attachment('leg', spec['point_xyz_mm'])


def test_prepare_restores_global_factories_after_failure(monkeypatch):
    original = base.CurrentStructure, base.gross_member_record, base.floor_attachment
    def fail(*args, **kwargs):
        assert base.CurrentStructure is UncutStructure
        raise RuntimeError('preparation failed')
    monkeypatch.setattr(base, 'prepare', fail)
    module = SimpleNamespace(uncut_wood_parts=lambda: (), runner_end_geometry=dict,
                             panel_connections=lambda: ())
    with pytest.raises(RuntimeError, match='preparation failed'):
        prepare_uncut(module)
    assert (base.CurrentStructure, base.gross_member_record, base.floor_attachment) == original


def test_prepare_registers_actual_trimmed_knee_as_constant_x_prism(monkeypatch):
    from mini_moonboard import compact_spliced_flush_top as candidate

    knee = next(part for part in candidate.uncut_wood_parts()
                if part.name == 'base_knee_left_rim')
    grain, across = candidate.MEMBER_AXES[knee.name]

    def inspect(module, **kwargs):
        record = base.gross_member_record(knee, grain, across, square_ends=False)
        prism = record['uncut_prism_geometry']
        assert prism['expected_volume_mm3'] == pytest.approx(knee.shape.Volume())
        assert prism['expected_centroid_xyz_mm'] == pytest.approx(knee.shape.Center().toTuple())
        assert len(prism['side_profile_yz_mm']) >= 4
        actual_stations = [vertex.Center().dot(grain) for vertex in knee.shape.Vertices()]
        assert np.dot(record['start'], grain.toTuple()) == pytest.approx(min(actual_stations))
        assert np.dot(record['end'], grain.toTuple()) == pytest.approx(max(actual_stations))
        structure = UncutStructure({})
        structure.member(record, size=150.)
        assert structure.members[knee.name]['record']['native_section_geometry'] == 'ACTUAL_UNCUT_PRISM_C3D20'
        return 'structure', {'candidate': module.KEY}

    monkeypatch.setattr(base, 'prepare', inspect)
    assert prepare_uncut(candidate)[1]['candidate'] == candidate.KEY
