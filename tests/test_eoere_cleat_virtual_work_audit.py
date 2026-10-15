"""Bindings and candidate/certificate separation for the saved volume bound."""
import copy
import json
from fractions import Fraction as F

import numpy as np
import pytest

from scripts import eoere_cleat_virtual_work_audit as audit
from tests.test_eoere_cleat_virtual_work import cube


def test_floating_candidate_support_agrees_with_exact_warped_cell_bound():
    positions = cube(F(1, 100))
    virtual = np.asarray([[float(p[0]*p[1]), float(p[1]*p[2]), float(-p[0]+p[2]*p[2])]
                          for p in positions])
    actual = audit.float_element_upper(positions, virtual[:, :, None])[0]
    expected = audit.vw.element_bound(positions, virtual, audit.vw.BASE_STRENGTHS)['upper']
    assert np.isclose(actual, float(expected), rtol=1e-13, atol=1e-13)


def test_nonoverlapping_exact_cell_and_boundary_mask_for_a_single_brick():
    geometry = {'planes': [], 'bores': []}
    with pytest.raises(ValueError, match='nonempty sound'):
        audit.sound_submesh(np.asarray(cube(), dtype=float), np.arange(20)[None, :], geometry)


def test_exact_certificate_refuses_nonzero_displacement_on_excluded_cell():
    nodes = np.asarray(cube(), dtype=float)
    virtual = np.zeros((20, 3))
    virtual[0, 0] = 1
    force = virtual.reshape(-1)
    with pytest.raises(ValueError, match='excluded cell'):
        audit.exact_certificate(nodes, np.arange(20)[None, :], force, virtual, [False])


def test_exact_certificate_retains_signed_work_and_binary_values():
    nodes = np.asarray(cube(), dtype=float)
    virtual = np.asarray([[float(p[0]), 0., 0.] for p in cube()])
    force = virtual.reshape(-1).copy()
    result = audit.exact_certificate(nodes, np.arange(20)[None, :], force, virtual, [True])
    assert F(result['exact_work_nmm']) == sum(F.from_float(v)**2 for v in force)
    assert F(result['exact_base_support_lower_nmm']) == F('8.5')
    assert F(result['exact_base_support_upper_nmm']) == F('8.5')
    with pytest.raises(ValueError, match='positive'):
        audit.exact_certificate(nodes, np.arange(20)[None, :], -force, virtual, [True])


@pytest.mark.parametrize('key,value', [('current_bolt_count', 99), ('current_screw_count', 65),
    ('structural_acceptance', True), ('actual_observations', {}), ('load_functional', 'wrenches_only'),
    ('working_strength_divisor', '1.5'), ('trial_rule', 'arbitrary'), ('source_configuration_index', 1)])
def test_predeclared_scope_and_load_hypothesis_cannot_drift(key, value):
    inputs = json.loads(audit.INPUT.read_text())
    audit.validate(inputs)
    inputs[key] = value
    with pytest.raises(ValueError):
        audit.validate(inputs)


def test_candidate_selection_uses_own_masks_signed_work_and_does_not_edit_sources(monkeypatch):
    nodes, elements = np.asarray(cube(), dtype=float), np.arange(20)[None, :]
    labels = [{'member': audit.MEMBERS[i % 2], 'case_id': str(i)} for i in range(48)]
    masks = {audit.MEMBERS[0]: (np.array([True]), [0], {}), audit.MEMBERS[1]: (np.array([True]), [1], {})}
    displacement = np.ones((60, 48))
    force = np.ones((60, 48))
    force[:, 47] = -48
    old_f, old_u = force.copy(), displacement.copy()
    monkeypatch.setattr(audit, 'float_element_upper', lambda positions, virtual: np.sum(abs(virtual), axis=(0, 1)))
    chosen, virtual, rows = audit.select_trial(nodes, elements, force, displacement, labels, masks)
    assert chosen == 47 and rows[chosen]['orientation'] == -1
    assert np.array_equal(virtual[1], [-1, -1, -1])
    assert not np.any(np.delete(virtual, 1, axis=0))
    assert all(row['certified_result'] is False for row in rows)
    assert np.array_equal(force, old_f) and np.array_equal(displacement, old_u)


def test_loaded_helper_drift_is_refused():
    inputs = json.loads(audit.INPUT.read_text())
    changed = copy.deepcopy(inputs)
    changed['volume_helper']['sha256'] = '0'*64
    with pytest.raises(ValueError, match='helper changed'):
        audit.validate(changed)
