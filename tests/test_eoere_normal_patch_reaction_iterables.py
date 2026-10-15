"""One-pass column controls for the preserved scalar-gap implementation."""
from fractions import Fraction as F

import pytest

from scripts import eoere_normal_patch_reaction_consumer as scalar
from scripts import eoere_normal_patch_reaction_iterables as model
from scripts import eoere_normal_patch_reactions as original


def check(columns, components=None, candidate=None):
    return model.replayable_gap(scalar.exact_gap, original.distributed_gap, 0, columns,
        [{'stiffness': 3}] if components is None else components,
        [1] if candidate is None else candidate, [0], [0])


def test_preserved_iterator_counterexample_and_replayable_adapter():
    assert scalar.exact_gap(original.distributed_gap, 0, iter([0]), [{'stiffness': 3}], [1], [0], [0]) == 0
    assert check(iter([0])) == F(1, 6)


@pytest.mark.parametrize('factory', [list, tuple, iter, lambda x: (j for j in x)])
def test_all_column_containers_preserve_the_same_known_integral(factory):
    assert check(factory([0])) == F(1, 6)


def test_generator_traverses_once_and_retains_duplicate_columns():
    visited = []
    def columns():
        for j in [0, 0]:
            visited.append(j)
            yield j
    assert check(columns()) == F(1, 3) and visited == [0, 0]


def test_column_order_is_not_sorted_or_reinterpreted():
    observed = []
    def normalization(original, primal, columns, components, candidate, radius, movement):
        observed.extend(columns)
        assert list(columns) == [2, 0, 2]
        return F(1)
    assert model.replayable_gap(normalization, None, 0, iter([2, 0, 2]), [], [], [], []) == 1
    assert observed == [2, 0, 2]


def test_remaining_one_pass_arguments_are_consumed_by_existing_scalar_adapter():
    assert check(iter([0]), ({'stiffness': 3} for _ in range(1)), (j for j in [1])) == F(1, 6)


def test_private_active_adapter_uses_replayable_columns_and_exact_arithmetic():
    active = model.adapter().producer().distributed_gap
    assert active(0, iter([0]), [{'stiffness': 3}], [1], [0], [0]) == F(1, 6)
    assert active(F(1, 6), (j for j in [0]), [{'stiffness': 3}], [1], [0], [F(1, 3)]) == 0


def test_invalid_conjugate_domain_is_not_hidden_by_materialization():
    with pytest.raises(ValueError, match='nonnegative dual'):
        model.replayable_gap(scalar.exact_gap, original.distributed_gap, 0, iter([0]), [{'stiffness': 3}], [0], [1], [0])


def test_caller_rows_and_preserved_modules_remain_unchanged():
    row = {'stiffness': 3}; assert check(iter([0]), [row]) == F(1, 6)
    assert row == {'stiffness': 3} and type(row['stiffness']) is int
    assert scalar.exact_gap(original.distributed_gap, 0, iter([0]), [row], [1], [0], [0]) == 0
