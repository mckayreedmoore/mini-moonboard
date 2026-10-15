"""Known-answer and refusal controls for the current finite-body adapter."""
import copy
import hashlib
import json
from types import SimpleNamespace

import numpy as np
import pytest
from scipy import sparse

from scripts import eoere_cleat_finite_body as finite


@pytest.fixture(scope='module')
def kernel():
    inputs = json.loads(finite.INPUT.read_bytes())
    return finite.component.load(inputs['kernel'], 'test_existing_current_finite_kernel')


@pytest.mark.parametrize('swap', [False, True])
def test_boolean_seam_closure_matches_independent_element_assembly_and_affine_energy(kernel, swap):
    _, _, _, _, _, scenario, brick = kernel.libraries()
    geom = {'length_mm': 40., 'width_mm': 20., 'depth_mm': 20., 'actual_volume_mm3': 16000.,
            'frame': np.eye(3).tolist(), 'start': [0., 0., 0.], 'bores': [], 'recess_source': None}
    constants = scenario()['calculix_engineering_constants']
    full_nodes, full_elements, _ = kernel.mesh(geom, 20., 2, 0., crack_interval=[0., 40.])
    full_k = kernel.stiffness(full_nodes, full_elements, constants, swap)
    for interval in (None, [0., 5.], [0., 10.]):
        nodes, elements, _ = kernel.mesh(geom, 20., 2, 0., crack_interval=interval)
        p = finite.assembly_map(full_nodes, full_elements, nodes, elements)
        actual = p.T @ full_k @ p
        direct = kernel.stiffness(nodes, elements, constants, swap)
        assert np.max(abs((actual-direct).data), initial=0.) < 1e-8
    nodes, elements, _ = kernel.mesh(geom, 20., 2, 0.)
    p = finite.assembly_map(full_nodes, full_elements, nodes, elements)
    k = (p.T @ full_k @ p).tocsr()
    strain = np.array([1., -2., 3., -4., 5., -6.])*1e-5
    tensor = np.diag(strain[:3])
    for value, (i, j) in zip(strain[3:], ((0, 1), (0, 2), (1, 2)), strict=True):
        tensor[i, j] = tensor[j, i] = value/2
    affine = (nodes@tensor).reshape(-1, 1)
    force = k@affine
    u, census = kernel.elastic_response(k, nodes, force)
    q = kernel.rigid_columns(nodes)
    delta = u-affine
    assert np.max(abs(delta-q@(q.T@delta))) < 1e-9
    axes = {'L': [1., 0., 0.], 'R': [0., 0., 1.] if swap else [0., 1., 0.],
            'T': [0., -1., 0.] if swap else [0., 0., 1.]}
    c = brick.engineering_stiffness(constants, axes)
    analytical = .5*geom['actual_volume_mm3']*strain@c@strain
    assert census['strain_energy_nmm'][0] == pytest.approx(analytical, rel=1e-9)
    assert census['maximum_gauge_reaction_n'] < 1e-7
    recovered = finite.saved_response(kernel, k, nodes, force, u)
    assert recovered['strain_energy_nmm'] == pytest.approx(census['strain_energy_nmm'], rel=1e-13)
    assert recovered['saved_field_recovered_without_interior_factorization'] is True
    broken = u.copy()
    broken[10] += .001
    with pytest.raises(ValueError, match='saved gauge/rigid/equilibrium'):
        finite.saved_response(kernel, k, nodes, force, broken)


def test_seam_mapping_rejects_changed_physical_cells_or_inconsistent_identifications():
    full_nodes = np.array([[0., 0., 0.], [0., 0., 0.], [1., 0., 0.], [-1., 0., 0.]])
    full_elements = np.array([[0, 2], [1, 3]])
    nodes = full_nodes[[0, 2, 3]]
    elements = np.array([[0, 1], [0, 2]])
    mapping = finite.assembly_map(full_nodes, full_elements, nodes, elements)
    assert mapping.shape == (12, 9)
    with pytest.raises(ValueError, match='physical elements'):
        finite.assembly_map(full_nodes, full_elements, nodes+1., elements)
    # A fully split node cannot become two different target DOFs.
    repeated = np.array([[0, 2], [0, 3]])
    with pytest.raises(ValueError, match='exactly one'):
        finite.assembly_map(full_nodes, repeated, full_nodes, full_elements)


@pytest.mark.parametrize('radius,side', [(15., -1), (15., 1), (30., -1), (30., 1)])
def test_scaled_original_side_load_map_preserves_force_couple_and_excludes_the_seam(kernel, radius, side):
    nodes = np.array([(x, y, z) for x in (0., 10., 20., 30., 40.)
                      for y in (-10., 0., 10.) for z in (-20., -10., 0., 10., 20.)])
    geom = {'frame': np.eye(3).tolist(), 'start': [0., 0., 0.]}
    p1, p2, force = np.array([15., 0., 0.]), np.array([25., 0., 0.]), np.array([1., -2., 3.])
    records = [{'actions': [{'point_mm': p1.tolist(), 'force_n': force.tolist(), 'free_moment_nmm': [0., 0., 0.]},
                           {'point_mm': p2.tolist(), 'force_n': (-force).tolist(),
                            'free_moment_nmm': (-np.cross(p1-p2, force)).tolist()}]}]
    untouched = copy.deepcopy(records)
    f, info = finite.nodal_loads(kernel, nodes, geom, records, 0., radius, side)
    assert records == untouched
    values = f.reshape(len(nodes), 3)
    assert values.sum(axis=0) == pytest.approx([0.]*3, abs=1e-12)
    assert np.cross(nodes, values).sum(axis=0) == pytest.approx([0.]*3, abs=1e-11)
    assert np.max(abs(values[nodes[:, 2]*side <= 0.]), initial=0.) == 0.
    assert info['coincident_selection_offsets'] == 2
    assert info['radius_increment_mm'] == radius


def test_energy_increment_and_contact_upper_reference_have_independent_known_values():
    # Nested spring spaces give strain energies 1, 2, 5 Nmm.
    f = np.array([2., 4.])
    energies = [.5*f@np.linalg.solve(sparse.diags(d).toarray(), f)
                for d in ([4., 16.], [2., 8.], [.8, 3.2])]
    result = finite.energy_comparison(energies, [10., 15.])
    assert result['signed_free_face_energy_release_n_per_mm'] == pytest.approx(.6)
    assert result['signed_contact_upper_reference_n_per_mm'] == pytest.approx(.8)
    assert result['added_sound_area_mm2'] == 5.


@pytest.mark.parametrize('energies,areas', [([1., .5, 3.], [1., 2.]), ([1., 3., 2.], [1., 2.]),
                                         ([-1., 1., 2.], [1., 2.]), ([1., 2., np.nan], [1., 2.]),
                                         ([1., 2., 3.], [2., 2.]), ([1., 2., 3.], [0., 2.])])
def test_nonfinite_or_non_nested_energy_or_fake_sound_area_is_refused(energies, areas):
    with pytest.raises(ValueError):
        finite.energy_comparison(energies, areas)


def synthetic_geometry():
    profile = {'name': 'test', 'axis': [0., 0., 1.], 'width_mm': 4., 'depth_mm': 20.,
               'start': [10., 0., 0.], 'raw_profile_source': {
                   'basis_grain_u_v_xyz': [[0., 0., 1.], [1., 0., 0.], [0., 1., 0.]],
                   'finished_YZ_polygon_mm': [[-10., 0.], [10., 0.], [10., 50.], [-10., 30.]]}}
    actions = [{'id': f'b{i}/complete-wood-wrench', 'point_xyz_mm': [10., y, z]}
               for i, (y, z) in enumerate(((-4., 10.), (4., 10.), (-4., 20.), (4., 20.)))]
    shafts = {f'b{i}': {'basis': [[1., 0., 0.]], 'bore_diameter_mm': 2.} for i in range(4)}
    saved = {'whole_volume_mm3': 3200.-16*np.pi, 'observation': {'source': {'path': 'test.brep', 'sha256': 'test'}}}
    return profile, saved, actions, shafts


def test_current_profile_adapter_recovers_exact_trapezoid_minus_four_cylinders():
    profile, saved, actions, shafts = synthetic_geometry()
    geom = finite.geometry(profile, saved, actions, shafts)
    assert geom['analytic_finished_volume_mm3'] == pytest.approx(3200.-16*np.pi)
    assert geom['start'] == [10., 0., 0.]
    assert geom['bores'][0]['origin'] == [10., 0., -4.]
    assert geom['planes'][1] == {'normal': [1., 0., -1.], 'offset': 40.}


@pytest.mark.parametrize('change', ['volume', 'axis', 'bore', 'polygon'])
def test_unbound_or_unsupported_current_geometry_is_refused(change):
    profile, saved, actions, shafts = synthetic_geometry()
    if change == 'volume':
        saved['whole_volume_mm3'] += 1.
    elif change == 'axis':
        profile['axis'] = [1., 0., 0.]
    elif change == 'bore':
        actions[0]['point_xyz_mm'][1] = -10.
    else:
        profile['raw_profile_source']['finished_YZ_polygon_mm'][0][1] = 1.
    with pytest.raises(ValueError):
        finite.geometry(profile, saved, actions, shafts)


@pytest.mark.parametrize('key,value', [('extra_grid', True), ('actual_observations', {}),
                                     ('mesh_sizes_mm', [15.]), ('radius_increments_mm', [30.]),
                                     ('Gc_all_modes_n_per_mm', [.2]), ('Ft90_reference_mpa', .5)])
def test_changed_declared_scope_requires_a_separate_input(key, value):
    inputs = json.loads(finite.INPUT.read_bytes())
    inputs[key] = value
    with pytest.raises(ValueError):
        finite.validate(inputs)


def test_independent_sound_area_subtracts_the_actual_bore_and_sloping_finished_end():
    geom = finite.geometry(*synthetic_geometry())
    assert finite.exact_crack_area(geom, -4., None) == 0.
    assert finite.exact_crack_area(geom, -4., [5., 15.]) == pytest.approx(4.*(10.-2.))
    assert finite.exact_crack_area(geom, -4., [10., 13.]) == pytest.approx(4.*(3.-1.))
    assert finite.exact_crack_area(geom, 0., [30., 50.]) == pytest.approx(4.*(40.-30.))
    with pytest.raises(ValueError):
        finite.exact_crack_area(geom, 0., [40., 50.])


def test_source_registry_excludes_only_declared_dependency_roots_and_keeps_ignored_helpers(tmp_path, monkeypatch):
    monkeypatch.setattr(finite.current, 'ROOT', tmp_path)
    dependency = tmp_path/'.venv/site-packages'
    monkeypatch.setattr(finite.sysconfig, 'get_path', lambda _: str(dependency))
    assert finite.repository_source(dependency/'scipy/__config__.py') is None
    assert finite.repository_source(tmp_path/'fea/generated/helper.py') == 'fea/generated/helper.py'
    assert finite.repository_source(tmp_path/'scripts/helper.py') == 'scripts/helper.py'
    assert finite.repository_source(tmp_path/'unrelated/site-packages/helper.py') == 'unrelated/site-packages/helper.py'


def test_unbound_generated_repository_helper_is_still_rejected(tmp_path, monkeypatch):
    monkeypatch.setattr(finite.current, 'ROOT', tmp_path)
    monkeypatch.setattr(finite.sysconfig, 'get_path', lambda _: str(tmp_path/'.venv/site-packages'))
    path = tmp_path/'fea/generated/unbound.py'
    path.parent.mkdir(parents=True)
    path.write_text('unbound = True\n')
    monkeypatch.setitem(finite.sys.modules, 'current_unbound_component_control', SimpleNamespace(__file__=str(path)))
    with pytest.raises(ValueError, match='unbound repository execution source: fea/generated/unbound.py'):
        finite.verify_execution_sources({})


def test_input_digest_binds_exact_parsed_bytes_before_intake_and_rejects_drift(tmp_path, monkeypatch):
    raw = finite.INPUT.read_bytes()
    path = tmp_path/'inputs.json'
    path.write_bytes(raw)
    monkeypatch.setattr(finite, 'INPUT', path)
    monkeypatch.setattr(finite.current, 'ROOT', tmp_path)

    def intake():
        path.write_bytes(raw+b'\n')
        return [], {}

    monkeypatch.setattr(finite.prior.intake_source, 'intake', intake)
    monkeypatch.setattr(finite.current, 'read', lambda _: {'source_sha256': {'uv.lock': 'unused'}})
    monkeypatch.setattr(finite.current, 'ref', lambda p: {'path': str(p), 'sha256': 'unused'})

    def verify(pins):
        assert pins['inputs.json'] == hashlib.sha256(raw).hexdigest()
        assert pins['inputs.json'] != hashlib.sha256(path.read_bytes()).hexdigest()
        raise ValueError('changed parsed input refused before local work')

    monkeypatch.setattr(finite.current, 'verify', verify)
    with pytest.raises(ValueError, match='changed parsed input refused'):
        finite.run(tmp_path/'unused-output', 0, prepare_only=True)


def test_saved_array_digest_binds_the_bytes_parsed_and_refuses_source_drift(tmp_path, monkeypatch):
    monkeypatch.setattr(finite.current, 'ROOT', tmp_path)
    p = tmp_path/'array.npz'
    np.savez_compressed(p, U=np.arange(6).reshape(3, 2))
    ref = {'path': 'array.npz', 'sha256': hashlib.sha256(p.read_bytes()).hexdigest()}
    read = finite.read_array_file(ref)
    assert np.array_equal(read['U'], np.arange(6).reshape(3, 2))
    read.close()
    p.write_bytes(p.read_bytes()+b'changed')
    with pytest.raises(ValueError, match='saved array source changed'):
        finite.read_array_file(ref)
