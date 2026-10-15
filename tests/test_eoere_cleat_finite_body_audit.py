"""Independent matrix assembly, stress, energy and comparison-identity controls."""
import numpy as np
import pytest
from scipy import sparse

from scripts import eoere_cleat_finite_body_audit as audit


def test_auditor_enforces_its_declared_numerical_runtime_versions(monkeypatch):
    versions = {'numpy': '2.5.2', 'scipy': '1.18.1'}
    monkeypatch.setattr(audit.importlib.metadata, 'version', versions.__getitem__)
    assert audit.verify_runtime({'runtime_versions': versions}) == versions
    with pytest.raises(ValueError, match='auditor numerical runtime'):
        audit.verify_runtime({'runtime_versions': {**versions, 'scipy': '1.18.0'}})


def fixture():
    full_nodes = np.array([[0., 0., 0.], [0., 0., 0.], [1., 0., 0.], [-1., 0., 0.]])
    full_elements = np.array([[0, 2], [1, 3]])
    nodes, elements = full_nodes[[0, 2, 3]], np.array([[0, 1], [0, 2]])
    full_k, direct = np.zeros((12, 12)), np.zeros((9, 9))
    for old, new, diagonal in zip(full_elements, elements, ([2., 3., 5.], [7., 11., 13.]), strict=True):
        c = np.diag(diagonal)
        local = np.block([[c, -c], [-c, c]])
        a, b = [(3*e[:, None]+np.arange(3)).ravel() for e in (old, new)]
        full_k[np.ix_(a, a)] += local
        direct[np.ix_(b, b)] += local
    return sparse.csr_matrix(full_k), full_nodes, full_elements, nodes, elements, direct


def test_direct_matrix_entry_coalescing_equals_independently_assembled_two_springs():
    k, fn, fe, nodes, elements, expected = fixture()
    actual = audit.coalesce_operator(k, fn, fe, nodes, elements)
    assert actual.toarray() == pytest.approx(expected)
    u = np.arange(9, dtype=float)
    assert .5*u@actual@u == pytest.approx(.5*u@expected@u)


def test_changed_physical_element_geometry_is_rejected():
    k, fn, fe, nodes, elements, _ = fixture()
    with pytest.raises(ValueError, match='physical elements changed'):
        audit.coalesce_operator(k, fn, fe, nodes+1., elements)


def test_inconsistent_node_identification_is_rejected():
    k, fn, _, _, _, _ = fixture()
    with pytest.raises(ValueError, match='inconsistent'):
        audit.coalesce_operator(k, fn, np.array([[0, 2], [0, 3]]), fn, np.array([[0, 2], [1, 3]]))


@pytest.mark.parametrize('natural', [[0., 0., 0.], [.3, -.4, .2], [-.7, .1, .5]])
def test_independent_affine_displacement_gradient_recovers_all_six_engineering_strains(natural):
    inputs = audit.current.read(audit.current.ref(audit.model.INPUT))
    kernel = audit.model.component.load(inputs['kernel'], 'audit_affine_witness_fixture')
    _, _, _, reference_nodes, _, _, _ = kernel.libraries()
    nodes = reference_nodes*np.array([7., 11., 13.])+[17., 19., 23.]
    tensor = np.array([[1., 2., 3.], [2., 4., 5.], [3., 5., 6.]])*.001
    constitutive = np.diag([2., 3., 5., 7., 11., 13.])
    actual = audit.witness_stress(nodes, nodes@tensor, constitutive, natural)
    expected = constitutive@np.array([1., 4., 6., 4., 6., 10.])*.001
    assert actual == pytest.approx(expected, abs=1e-14)


def test_physical_fingerprint_is_invariant_to_node_reindexing_but_detects_changed_load():
    nodes = np.array([[1., 2., 3.], [4., 5., 6.], [7., 8., 9.]])
    force = np.arange(18, dtype=float).reshape(9, 2)
    order = [2, 0, 1]
    a = audit.physical_fingerprint(nodes, force)
    b = audit.physical_fingerprint(nodes[order], force.reshape(3, 3, 2)[order].reshape(9, 2))
    assert a == b
    changed = force.copy()
    changed[0, 0] += 1.
    assert audit.physical_fingerprint(nodes, changed) != a


def test_consistent_changed_configuration_load_is_rejected_against_fixed_family():
    nodes = np.array([[1., 2., 3.], [4., 5., 6.]])
    force = np.arange(288, dtype=float).reshape(6, 48)
    original = [audit.physical_fingerprint(nodes, force[:, i*12:(i+1)*12]) for i in range(4)]
    maps = [{'physical_nodal_load_sha256': value} for value in original]
    assert audit.verify_fixed_loads(nodes, force, maps, original) == original
    changed = force.copy()
    changed[0, 0] += 1.
    changed[3, 0] -= 1.  # Balanced resultant; metadata alone would be consistent.
    altered = [audit.physical_fingerprint(nodes, changed[:, i*12:(i+1)*12]) for i in range(4)]
    new_maps = [{'physical_nodal_load_sha256': value} for value in altered]
    with pytest.raises(ValueError, match='fixed prescribed physical loads'):
        audit.verify_fixed_loads(nodes, changed, new_maps, original, original)


def seam_fixture(interval):
    # Two adjacent rectangular elements share the z=0 face. Four seam nodes
    # at grain coordinates 1 and 3 allow equal-area low/high crack families.
    nodes, elements, known = [], [], {}
    for z0, z1 in ((-1., 0.), (0., 1.)):
        indices = []
        for z in (z0, z1):
            for y in (-1., 1.):
                for x in (1., 3.):
                    split = interval is not None and interval[0] < x < interval[1] and z == 0. and z1 > 0.
                    key = (x, y, z, bool(split))
                    if key not in known:
                        known[key] = len(nodes)
                        nodes.append([x, y, z])
                    indices.append(known[key])
        elements.append(indices)
    return np.array(nodes), np.array(elements)


@pytest.mark.parametrize('interval', [None, (0., 2.), (2., 4.), (0., 4.)])
def test_declared_seam_topology_accepts_only_the_own_interval_and_arbitrary_node_numbering(interval):
    nodes, elements = seam_fixture(interval)
    order = np.arange(len(nodes))[::-1]
    inverse = np.argsort(order)
    audit.verify_crack_topology(nodes[order], inverse[elements], 2, 0., interval, 4.)


def test_equal_area_swapped_bore_crack_family_is_rejected_by_saved_connectivity():
    nodes, elements = seam_fixture((0., 2.))
    with pytest.raises(ValueError, match='saved seam topology'):
        audit.verify_crack_topology(nodes, elements, 2, 0., (2., 4.), 4.)
    with pytest.raises(ValueError, match='saved seam topology'):
        audit.verify_crack_topology(nodes, elements, 2, 0., None, 4.)


@pytest.mark.parametrize('coarse,fine,expected', [(1., .8, .2), (0., 0., 0.),
                                               (1e-10, 2e-10, .01), (-1., -2., .5)])
def test_mesh_change_uses_the_declared_symmetric_denominator_and_precision_floor(coarse, fine, expected):
    assert audit.relative_change(coarse, fine) == pytest.approx(expected)


def test_nonfinite_mesh_value_is_rejected():
    with pytest.raises(ValueError):
        audit.relative_change(np.nan, 1.)


def test_independent_energy_arithmetic_and_non_nested_refusal():
    assert audit.independent_energies(1., 3., 7., 2.) == (2., 3.)
    with pytest.raises(ValueError):
        audit.independent_energies(1., .9, 7., 2.)
    with pytest.raises(ValueError):
        audit.independent_energies(1., 3., 7., 0.)


def test_mesh_pair_identity_keeps_member_case_field_bore_tip_and_boundary_hypothesis():
    row = {'member': 'left', 'case_id': 'a12-left', 'state_id': 'own', 'field': {'path': 'own.json', 'sha256': 'hash'},
           'bore_id': 'own-bore', 'tip': 'high', 'radius_increment_mm': 15., 'coincident_point_side': -1}
    job = {'swap_RT': False, 'plane_mm': -25.4, 'mesh_size_mm': 15.}
    key = audit.trace_key(row, job)
    assert key == audit.trace_key(row, {**job, 'mesh_size_mm': 10.})
    for name, value in [('member', 'right'), ('case_id', 'other'), ('state_id', 'other'),
                        ('bore_id', 'other'), ('tip', 'low'), ('radius_increment_mm', 30.), ('coincident_point_side', 1)]:
        assert audit.trace_key({**row, name: value}, job) != key
