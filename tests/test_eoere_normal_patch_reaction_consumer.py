"""Integer, binary-float and near-equality controls for the exact adapter."""
import hashlib
import json
import math
from fractions import Fraction as F

import pytest

from scripts import eoere_normal_patch_reaction_consumer as model
from scripts import eoere_normal_patch_reactions as previous


def gap(primal, stiffness, candidate, radius, movement):
    return model.producer().distributed_gap(primal, [0], [{'stiffness': stiffness}], [candidate], [radius], [movement])


def test_preserved_integer_counterexample_and_exact_adapter():
    old = previous.distributed_gap(0, [0], [{'stiffness': 3}], [1], [0], [0])
    assert isinstance(old, float) and F(old) < F(1, 6)
    assert F(1, 6)-F(old) == F(1, 108086391056891904)
    assert gap(0, 3, 1, 0, 0) == F(1, 6)
    assert isinstance(gap(0, 3, 1, 0, 0), F)


@pytest.mark.parametrize('displacement', [0, F(1, 3), math.nextafter(1/3, -math.inf), 1/3, math.nextafter(1/3, math.inf)])
def test_near_equality_controls_keep_exact_nonnegative_gap(displacement):
    d = F(displacement)
    # k=3, lambda=1. The exact gap is 3/2*(d-1/3)^2.
    result = gap(3*d*d/2, 3, 1, 0, displacement)
    assert result == F(3, 2)*(d-F(1, 3))**2 and result >= 0


def test_binary_float_operands_are_exact_stored_values_not_decimal_guesses():
    values = [.1, .2, .3, .01, -.4]
    p, k, x, r, d = map(F, values)
    assert gap(*values) == p+(x+r)**2/(2*k)-x*d+r*abs(d)
    assert F(.1) != F('0.1')


def test_all_integer_force_correction_and_opening_work_are_retained():
    assert gap(2, 3, 2, 1, -1) == F(13, 2)


def test_normalization_preserves_input_ownership_and_existing_fraction_result():
    components = [{'stiffness': 3, 'row': {0: F(1)}}]
    candidate, radius, movement = [1], [0], [0]
    expected = previous.distributed_gap(F(0), [0], [{'stiffness': F(3)}], [F(1)], [F(0)], [F(0)])
    actual = model.exact_gap(previous.distributed_gap, 0, [0], components, candidate, radius, movement)
    assert actual == expected
    assert components == [{'stiffness': 3, 'row': {0: F(1)}}] and type(components[0]['stiffness']) is int
    assert candidate == [1] and type(candidate[0]) is int and radius == [0] and movement == [0]


def test_invalid_positive_conjugate_domain_is_still_refused():
    with pytest.raises(ValueError, match='nonnegative dual'):
        gap(0, 3, 0, 1, 0)


def test_source_buffer_drift_and_outside_path_are_refused(tmp_path, monkeypatch):
    path = tmp_path/'source.py'; path.write_text('raise RuntimeError("must not execute")\n')
    monkeypatch.setattr(model, 'ROOT', tmp_path)
    with pytest.raises(ValueError, match='source changed'):
        model.captured({'path': 'source.py', 'sha256': '0'*64})
    outside = tmp_path.parent/'outside-exact-adapter.py'
    with pytest.raises(ValueError, match='repository source'):
        model.captured({'path': str(outside), 'sha256': '0'*64})


def test_wrong_adapter_identity_is_rejected_before_the_producer(tmp_path, monkeypatch):
    data = {'execution_adapter_schema': 'other'}
    path = tmp_path/'input.json'; path.write_text(json.dumps(data))
    monkeypatch.setattr(model, 'ROOT', tmp_path)
    monkeypatch.setattr(model, 'OWN', tmp_path/'adapter.py')
    with pytest.raises(ValueError, match='exact scalar adapter'):
        model.run({'path': 'input.json', 'sha256': hashlib.sha256(path.read_bytes()).hexdigest()})
