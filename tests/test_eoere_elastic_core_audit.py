"""Ownership and immutable-source controls; no recovered frame data needed."""
from contextlib import contextmanager
from fractions import Fraction as F
from types import SimpleNamespace

import numpy as np
import pytest
from scipy.sparse import csr_matrix

from scripts import eoere_elastic_core_audit as audit
from scripts import eoere_elastic_core_certificate as method


def owner_fixture():
    matrix = csr_matrix([[2., -1., 0., 0.], [-1., 2., 0., 0.], [0., 0., 3., -2.], [0., 0., -2., 3.]])
    maps = [{0: F(1)}, {0: F(1)}, {1: F(1)}, {1: F(1)}]
    owners = ['first', 'first', 'second', 'second']
    bodies = [{'body': name, 'family': 'synthetic', 'first_rigid_column': i, 'owned_coordinates': 2,
               'source_mode_columns': [0]} for i, name in enumerate(['first', 'second'])]
    return matrix, maps, owners, bodies


def test_every_local_matrix_and_basis_is_extracted_from_its_own_coordinates():
    blocks = audit.owner_blocks(*owner_fixture())
    assert [block['global_coordinates'] for block in blocks] == [[0, 1], [2, 3]]
    assert blocks[0]['rows'] == [{0: F(2), 1: F(-1)}, {0: F(-1), 1: F(2)}]
    assert blocks[1]['rows'] == [{0: F(3), 1: F(-2)}, {0: F(-2), 1: F(3)}]
    assert [block['rigid'] for block in blocks] == [[{0: F(1)}, {0: F(1)}]]*2


@pytest.mark.parametrize('change,match', [
    ('cross-owner', 'different mechanical owners'),
    ('foreign-rigid-column', 'own registered rigid columns'),
    ('unknown-owner', 'unregistered coordinate owner'),
    ('missing-coordinate', 'complete unique own body coordinates'),
    ('nonfinite', 'finite complete saved elastic matrix'),
])
def test_owner_or_map_drift_cannot_share_a_certificate(change, match):
    matrix, maps, owners, bodies = owner_fixture()
    if change == 'cross-owner':
        matrix = matrix.tolil()
        matrix[0, 3] = 1e-100
        matrix = matrix.tocsr()
    elif change == 'foreign-rigid-column':
        maps[0][1] = F(1, 2**100)
    elif change == 'unknown-owner':
        owners[0] = 'foreign'
    elif change == 'missing-coordinate':
        bodies[0]['owned_coordinates'] = 3
    elif change == 'nonfinite':
        matrix.data[0] = np.nan
    with pytest.raises(ValueError, match=match):
        audit.owner_blocks(matrix, maps, owners, bodies)


def test_duplicate_sparse_entries_are_summed_exactly():
    matrix, maps, owners, bodies = owner_fixture()
    # The exact stored sum is 2 + 2^-60, which a floating CSR sum would lose.
    matrix = csr_matrix((np.array([2., 2**-60, -1., -1., 2., 3., -2., -2., 3.]),
                         np.array([0, 0, 1, 0, 1, 2, 3, 2, 3]), np.array([0, 3, 5, 7, 9])), shape=(4, 4))
    blocks = audit.owner_blocks(matrix, maps, owners, bodies)
    assert blocks[0]['rows'][0][0] == 2+F(1, 2**60)


def test_saved_pose_action_and_energy_changes_match_direct_exact_arithmetic():
    delta = [{0: F(1), 1: F(2)}, {0: F(2), 1: F(3)}]
    skew = [{1: F(5)}, {0: F(-5)}]
    result = audit.saved_pose_change(np.array([2., 3.]), [
        {'body': 'known', 'global_coordinates': [0, 1], 'delta': delta, 'skew': skew}])
    assert F(result['exact_core_action_change_inf_n']) == 23
    assert F(result['exact_core_action_change_one_norm_n']) == 26
    assert F(result['exact_core_energy_change_nmm']) == F(-55, 2)
    assert result['maximum_action_change_witness'] == {
        'body': 'known', 'global_coordinate': 0, 'exact_action_change': '-23'}
    assert result['saved_pose_is_an_admitted_comparator_response'] is False


@pytest.mark.parametrize('pose', [np.array([1., np.inf]), np.array([1, 2]), np.array([[1., 2.]]), np.array([1.])])
def test_nonfinite_or_incomplete_saved_pose_is_refused(pose):
    with pytest.raises(ValueError, match='complete finite saved'):
        audit.saved_pose_change(pose, [{'body': 'known', 'global_coordinates': [0, 1], 'delta': [{}, {}], 'skew': [{}, {}]}])


def test_an_incorrect_skew_energy_is_not_accepted_as_roundoff():
    with pytest.raises(ValueError, match='exactly zero quadratic'):
        audit.saved_pose_change(np.array([1., 1.]), [{'body': 'known', 'global_coordinates': [0, 1],
                                                   'delta': [{}, {}], 'skew': [{0: F(1, 2**100)}, {}]}])


def original_fixture(monkeypatch):
    matrix, maps, owners, bodies = owner_fixture()
    modes = np.ones((4, 6))
    bank = {'data': matrix.data, 'indices': matrix.indices, 'indptr': matrix.indptr, 'modes': modes}
    metadata = {key: method.exact.matrix_digest([{i: method.rational(v) for i, v in enumerate(value.ravel())}])
                for key, value in bank.items()}
    manifest = {'K': {'data': 'data', 'indices': 'indices', 'indptr': 'indptr', 'shape': [4, 4]},
                'rigid_modes_key': 'modes', 'array_metadata': metadata, 'coordinate_map': {}}
    field = {'operator_bundle': {'manifest': {'path': 'own'}, 'arrays': {'path': 'own-arrays'}}}
    imported = {'bodies': bodies, 'exact_registered_rigid_basis_sha256': method.exact.matrix_digest(maps)}
    class Archive:
        def __init__(self):
            self.files = list(bank)
        def __getitem__(self, key):
            return bank[key]
    @contextmanager
    def real_archive(_pointer):
        yield Archive()
    monkeypatch.setattr(audit, 'read_exact', lambda _ref: manifest)
    monkeypatch.setattr(audit.model, 'read_array_file', real_archive)
    monkeypatch.setattr(audit.recession, 'rigid_basis', lambda _chart, _modes: (maps, owners, bodies, 800))
    frozen = SimpleNamespace(bundle=SimpleNamespace(_get_csr=lambda _bank, _record: matrix,
        _array_record=lambda value: method.exact.matrix_digest([{i: method.rational(v) for i, v in enumerate(value.ravel())}])))
    return field, imported, frozen, metadata, maps


def test_core_read_uses_bound_numeric_records_and_the_existing_registered_basis(monkeypatch):
    field, imported, frozen, _, maps = original_fixture(monkeypatch)
    matrix, actual, owners, bodies, fingerprint = audit.original_core(field, imported, frozen)
    assert matrix.shape == (4, 4) and actual == maps
    assert len(owners) == 4 and bodies == imported['bodies'] and len(fingerprint) == 64


@pytest.mark.parametrize('change,match', [('numeric', 'numeric arrays'), ('basis', 'recession basis')])
def test_core_sharing_refuses_numeric_or_exact_basis_drift(monkeypatch, change, match):
    field, imported, frozen, metadata, maps = original_fixture(monkeypatch)
    if change == 'numeric':
        metadata['modes'] = 'changed'
    else:
        maps[0][0] += F(1, 2**100)
    with pytest.raises(ValueError, match=match):
        audit.original_core(field, imported, frozen)
