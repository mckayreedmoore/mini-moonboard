import copy
from pathlib import Path

import pytest

from fea import panel_screw_comparison as comparison


@pytest.fixture
def pair():
    full = Path('fea/generated/horizontal-frame-batch-v2/f10-k1000')
    reduced = Path('fea/generated/panel-screw-sensitivity-v1/f10-reduced')
    if not reduced.exists():
        pytest.skip('Local expanded sensitivity evidence unavailable')
    return full, reduced, Path('exports/horizontal-service-development/connections.csv')


def test_signed_demand_increase_survives_small_displacement_change(pair):
    result = comparison.compare(*pair)
    assert result['reduced_count'] == 75 and result['removed_count'] == 12
    assert not result['qualified_for_design'] and not result['removal_approved']
    full = result['worst']['full']['withdrawal_n']['full']['withdrawal_n']
    reduced = result['worst']['reduced']['withdrawal_n']['reduced']['withdrawal_n']
    assert reduced/full > 1.19
    assert result['displacement']['maximum_panel_displacement_mm']['percent_change'] < 2.
    assert len(result['rows']) == 87


def test_changed_load_rejected_even_if_both_diagnostics_pass(pair, monkeypatch):
    read = comparison.read_case
    def changed(path):
        report, record = read(path)
        if path == pair[1]:
            record = copy.deepcopy(record)
            next(iter(record['loads'].values()))[0] += 1.
        return report, record
    monkeypatch.setattr(comparison, 'read_case', changed)
    with pytest.raises(ValueError, match='comparison mismatch: loads'):
        comparison.compare(*pair)


def test_retained_screw_stiffness_change_rejected(pair, monkeypatch):
    read = comparison.read_case
    def changed(path):
        report, record = read(path)
        if path == pair[1]:
            record = copy.deepcopy(record)
            record['springs'][0]['stiffness_n_per_mm'] *= 2.
        return report, record
    monkeypatch.setattr(comparison, 'read_case', changed)
    with pytest.raises(ValueError, match='Retained spring mechanics'):
        comparison.compare(*pair)
