"""Finite load integrals and saved-panel work; no candidate solve or CAD build."""
import copy
import hashlib
import io
import sys
from fractions import Fraction as F
from types import SimpleNamespace

import numpy as np
import pytest

from scripts import eoere_remaining_load_work as model


@pytest.fixture(scope='module')
def contact():
    return model.bootstrap({}).bootstrap({})


def gravity_row():
    return {'id': 'metal-share', 'body': 'wood', 'parent_body': 'wood',
        'force_xyz_n': [0, 0, -24], 'point_xyz_mm': [2, -3, 4]}


def test_cube_integrates_each_affine_work_coefficient_exactly(contact):
    source = gravity_row(); law = model.cube_law(source, 1, 10, F(1, 10**7), True, contact)
    assert F(law['volume_mm3']) == 8 and list(map(F, law['uniform_force_density_n_per_mm3'])) == [0, 0, -3]
    assert F(law['L2_load_functional_norm_square_n2_per_mm3']) == 72
    # Tensor-product endpoint integration is exact for every affine monomial.
    bounds = [list(map(F, row)) for row in law['cube_bounds_xyz_mm']]
    differential_force = [F(value)*F(law['volume_mm3'])/8 for value in law['uniform_force_density_n_per_mm3']]
    pieces = [{'force_xyz_n': differential_force, 'point_xyz_mm': [x, y, z]}
              for x in bounds[0] for y in bounds[1] for z in bounds[2]]
    assert contact.affine_load_coefficients(pieces) == list(map(F, law['exact_affine_work_coefficients']))
    assert law['exact_resultant_and_affine_first_moments_preserved'] is True
    assert law['arbitrary_old_beam_work_or_comparator_bounds_transferred'] is False


def test_cube_width_sensitivities_keep_force_and_moment_but_change_nonaffine_work(contact):
    laws = [model.cube_law(gravity_row(), r, 10, F(1, 10**7), True, contact) for r in (F(1, 2), F(1), F(2))]
    assert all(row['exact_affine_work_coefficients'] == laws[0]['exact_affine_work_coefficients'] for row in laws)
    assert [F(row['L2_load_functional_norm_square_n2_per_mm3']) for row in laws] == [576, 72, 9]
    # Integral x^2 over a uniform cube is p_x^2+r^2/3, not the point value p_x^2.
    for r in (F(1, 2), F(1), F(2)):
        mean = ((2+r)**3-(2-r)**3)/(6*r)
        assert mean == 4+r*r/3 and mean != 4


@pytest.mark.parametrize('half_width,distance,tolerance,inside', [(0, 10, F(1, 100), True),
    (-1, 10, F(1, 100), True), (1, 1, F(1, 100), True), (1, 10, 0, True),
    (1, 10, F(1, 100), False), (1, 10, F(1, 100), 1), (True, 10, F(1, 100), True)])
def test_uncontained_empty_or_unverified_cubes_are_refused(contact, half_width, distance, tolerance, inside):
    with pytest.raises(ValueError):
        model.cube_law(gravity_row(), half_width, distance, tolerance, inside, contact)


@pytest.mark.parametrize('change', ['upward', 'lateral', 'free_couple', 'boolean'])
def test_changed_gravity_actions_are_refused(contact, change):
    row = gravity_row()
    if change == 'upward': row['force_xyz_n'][2] = 24
    if change == 'lateral': row['force_xyz_n'][0] = 1
    if change == 'free_couple': row['moment_xyz_nmm'] = [1, 0, 0]
    if change == 'boolean': row['force_xyz_n'][0] = False
    with pytest.raises(ValueError):
        model.cube_law(row, 1, 10, F(1, 10**7), True, contact)


def test_panel_linear_work_has_exact_signed_directional_derivative():
    force, coefficients, direction = [F(1, 3), -2, 7], [3, F(1, 5), -4], [2, -3, F(2, 7)]
    step = F(1, 10**8)
    high = model.linear_panel_work(force, [a+step*b for a, b in zip(coefficients, direction, strict=True)])
    low = model.linear_panel_work(force, [a-step*b for a, b in zip(coefficients, direction, strict=True)])
    assert (high-low)/(2*step) == model.linear_panel_work(force, direction)
    assert -model.linear_panel_work(force, coefficients) == F(137, 5)
    with pytest.raises(ValueError): model.linear_panel_work(force, [1])
    with pytest.raises(ValueError): model.linear_panel_work([True], [1])


def test_attachment_share_joins_the_current_axis_and_receiver():
    loads = [{'id': 'bolt-weight/fastener_axis/source-metal-share-1', 'body': 'wood'}]
    axes = [{'id': 'axis', 'second': 'wood'}]
    assert model.attachment_axes(loads, axes) == {loads[0]['id']: 'axis'}
    for bad in ([{'id': loads[0]['id'], 'body': 'other'}], [{'id': 'unknown', 'body': 'wood'}]):
        with pytest.raises(ValueError): model.attachment_axes(bad, axes)
    with pytest.raises(ValueError): model.attachment_axes(loads*2, axes*2)


@pytest.mark.parametrize('groups', [(['a'], ['b'], ['c']), (['a'], ['a'], ['c']), (['a'], ['b'], ['d']),
    (['a', 'a'], ['b'], ['c'])])
def test_source_partition_requires_all_and_only_the_original_loads_once(groups):
    mapped = [{'id': value} for value in ('a', 'b', 'c')]
    if groups == (['a'], ['b'], ['c']):
        model.complete_partition(mapped, *groups)
    else:
        with pytest.raises(ValueError): model.complete_partition(mapped, *groups)


def panel_fixture():
    loads = [{'id': 'load', 'body': 'panel', 'force_xyz_n': [5, -6, -7], 'point_xyz_mm': [2, 3, 4]}]
    return {'name': 'panel', 'descriptor': {'indices': list(range(6))}, 'loads': loads,
        'applied': np.array([5, -6, -7, 4, 22, -16], dtype=float), 'rigid': np.eye(6), 'reference': [1, 1, 1],
        'force_tolerance': F(1, 10**7), 'moment_tolerance': F(1, 10**5)}


def test_panel_saved_vector_and_six_source_wrench_components_are_bound(contact):
    fixture = panel_fixture(); record = model.panel_work_record(contact=contact, **fixture)
    assert list(map(F, record['exact_saved_rigid_work_n_nmm'])) == [5, -6, -7, 4, 22, -16]
    assert list(map(F, record['exact_rigid_work_minus_source_wrench_n_nmm'])) == [0]*6
    assert record['all_saved_linear_panel_work_preserved_by_definition'] is True
    assert record['physical_finite_panel_bulk_coupling_or_objectivity_qualified'] is False


@pytest.mark.parametrize('change', ['duplicate_index', 'outside_index', 'duplicate_load', 'wrong_owner', 'wrong_force',
    'nonfinite', 'lost_precision_type', 'free_couple'])
def test_changed_or_unbound_panel_work_is_refused(contact, change):
    fixture = panel_fixture()
    if change == 'duplicate_index': fixture['descriptor']['indices'][-1] = 0
    if change == 'outside_index': fixture['descriptor']['indices'][-1] = 6
    if change == 'duplicate_load': fixture['loads'].append(copy.deepcopy(fixture['loads'][0]))
    if change == 'wrong_owner': fixture['loads'][0]['body'] = 'other'
    if change == 'wrong_force': fixture['applied'][0] = 6
    if change == 'nonfinite': fixture['rigid'][0, 0] = np.nan
    if change == 'lost_precision_type': fixture['applied'] = list(fixture['applied'])
    if change == 'free_couple': fixture['loads'][0]['moment_xyz_nmm'] = [1, 0, 0]
    with pytest.raises(ValueError): model.panel_work_record(contact=contact, **fixture)


def array_fixture():
    applied, rigid = np.arange(6, dtype=float), np.eye(6)
    manifest = {'applied_key': 'f', 'rigid_modes_key': 'r', 'final_ndof': 6,
        'array_metadata': {key: {'shape': list(a.shape), 'dtype': a.dtype.str,
            'nbytes': a.nbytes, 'content_sha256': hashlib.sha256(a.tobytes()).hexdigest()}
            for key, a in [('f', applied), ('r', rigid)]}}
    stream = io.BytesIO(); np.savez(stream, f=applied, r=rigid)
    return manifest, stream.getvalue()


def test_saved_array_shape_dtype_and_content_are_checked():
    manifest, data = array_fixture(); applied, rigid = model.saved_arrays(manifest, data)
    assert np.array_equal(applied, np.arange(6)) and np.array_equal(rigid, np.eye(6))


@pytest.mark.parametrize('change', ['hash', 'shape', 'dtype', 'bytes'])
def test_saved_array_metadata_mismatch_is_refused(change):
    manifest, data = array_fixture(); metadata = manifest['array_metadata']['f']
    key, value = {'hash': ('content_sha256', '0'*64), 'shape': ('shape', [5]),
                  'dtype': ('dtype', '<f4'), 'bytes': ('nbytes', 8)}[change]
    metadata[key] = value
    with pytest.raises(ValueError): model.saved_arrays(manifest, data)


@pytest.mark.parametrize('change', ['valid', 'other_proof', 'outside', 'boundary'])
def test_cached_geometry_keeps_every_boundary_shell_and_strict_container(change):
    proof = {'complete': True}; point = [1, 2, 3]
    shape = SimpleNamespace(Shells=lambda: [20., 7. if change != 'boundary' else 0.],
                            isInside=lambda p, tol: change != 'outside')
    observations = {'wood': {'source': {'path': 'cached.brep'}, 'strict_container': proof}}
    imports = []
    def imported(stream):
        assert stream.read() == b'cached'; imports.append(True); return shape
    reference = SimpleNamespace(cq=SimpleNamespace(Shape=SimpleNamespace(importBrep=imported),
        Vertex=SimpleNamespace(makeVertex=lambda *p: p)),
        distance_tool=lambda vertex, shell, tolerance: SimpleNamespace(Value=lambda: shell))
    strict = SimpleNamespace(strict_solid=lambda s, r: (s, proof if change != 'other_proof' else {}))
    base = SimpleNamespace(captured=lambda source, pins: b'cached')
    loads = [{'id': str(i), 'body': 'wood', 'point_xyz_mm': point} for i in range(2)]
    if change != 'valid':
        with pytest.raises(ValueError): model.cube_geometry(loads, observations, reference, strict, base, {}, F(1, 10**7))
    else:
        rows, proofs = model.cube_geometry(loads, observations, reference, strict, base, {}, F(1, 10**7))
        assert len(imports) == 1 and proofs == {'wood': proof}
        assert all(row['boundary_shell_count'] == 2 and row['minimum_boundary_distance_mm'] == 7 for row in rows)


def test_verified_bootstrap_ignores_module_cache_and_refuses_pin_conflict(monkeypatch):
    monkeypatch.setitem(sys.modules, 'scripts.eoere_distributed_gravity', SimpleNamespace(bootstrap=None))
    assert callable(model.bootstrap({}).bootstrap)
    with pytest.raises(ValueError): model.bootstrap({model.BOOT['path']: '0'*64})
