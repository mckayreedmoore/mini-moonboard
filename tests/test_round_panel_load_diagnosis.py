"""Per-panel force recovery uses its own rounding budget and signed reactions."""
import copy

from fea.round_panel_load_diagnosis import panel_balance


def test_panel_balance_rejects_real_residual_and_distinguishes_withdrawal():
    nodes = {i+1: p for i, p in enumerate([(0, 0, 0), (2, 0, 0), (2, 2, 0), (0, 2, 0),
                                         (1, 0, 0), (2, 1, 0), (1, 2, 0), (0, 1, 0), (0, 0, 0)])}
    record = {'nodes': nodes, 'loads': {1: [0., 0., -10.]}, 'panel_nodes': {'panel': list(range(1, 9))},
              'elements': {1: ['S8', list(range(1, 9)), 'panel']},
              'springs': [{'name': 'fastener', 'nodes': [9, 1], 'dof': d, 'stiffness_n_per_mm': 1000.}
                          for d in (1, 2, 3)]}
    report = {'connector_forces': {'fastener': {
        'force_on_first_xyz_n': [0., 0., -10.], 'first_point_xyz_mm': [0., 0., 0.]}}}
    precision = {n: [1.e-8]*3 for n in nodes}
    result = panel_balance(record, report, precision)[0]
    assert result['wrench_balance_passed']
    assert result['total_withdrawal_n'] == 10.
    assert result['total_compression_n'] == 0.
    altered = copy.deepcopy(report)
    altered['connector_forces']['fastener']['force_on_first_xyz_n'][2] = -9.
    assert not panel_balance(record, altered, precision)[0]['wrench_balance_passed']
