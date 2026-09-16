import json
from pathlib import Path

import pytest

from scripts.compact_spliced_flush_top_angle_ledger import build, markdown

ROOT = Path(__file__).resolve().parents[1]


def test_saved_angle_ledger_is_deterministic_and_complete():
    rebuilt = build()
    saved = json.loads((ROOT / 'docs/compact-spliced-flush-top-angle-ledger.json').read_text())
    assert rebuilt == saved
    assert markdown(rebuilt) == (ROOT / 'docs/compact-spliced-flush-top-angle-ledger.md').read_text()
    assert rebuilt['case_count'] == 6
    assert rebuilt['inventory_across_six_case_records'] == {
        'ML24Z_connection_records': 144,
        'SDS25112_screw_records': 864,
    }
    for case in rebuilt['cases'].values():
        assert case['ML24Z_connection_count'] == 24
        assert case['SDS25112_screw_count'] == 144
        assert len(case['connections']) == 24
        assert {row['screw_count'] for row in case['connections'].values()} == {6}
        assert all(row['independent_couple_resolved'] is False
                   for row in case['connections'].values())
    assert rebuilt['completion_gate']['status'] == 'OPEN'
    assert rebuilt['qualified_for_design'] is False


def test_angle_ledger_retains_positive_separation_and_loaded_flange_couple():
    result = build()
    separation = result['envelope_maxima']['unlisted_positive_F2_separation']
    couple = result['envelope_maxima']['absolute_force_parallel_loaded_flange_couple']
    assert separation['unlisted_positive_F2_separation_n'] > 0
    assert couple['absolute_force_parallel_couple_nmm'] > 0
    row = result['cases'][couple['case']]['connections'][couple['station']]
    assert abs(row['force_parallel_couple_nmm']) == pytest.approx(
        couple['absolute_force_parallel_couple_nmm'])
    assert len(row['loaded_flange_force_xyz_n']) == 3
    assert len(row['loaded_flange_moment_xyz_nmm']) == 3
