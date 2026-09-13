"""Independent invariants of the recorded assembled-frame results."""
import json
from pathlib import Path

import numpy as np


def test_published_cases_balance_actual_six_feet_and_pinned_geometry():
    report = json.loads(Path('fea/results/current-frame-response.json').read_text())
    assert len(report['cases']) == 9
    assert report['all_cases_numerically_accepted']
    assert not report['qualified_for_design']
    identity = report['analyzed_geometry_source_sha256']
    for case in report['cases']:
        assert case['numerically_accepted']
        assert case['numerical_audits']['closed_bearing_assumption_passed']
        assert case['inventory']['leg_bolts'] == 8
        assert case['inventory']['panel_screws'] == 66
        assert case['inventory']['ML24Z'] == 24
        assert len(case['floor_resultants']) == 6
        assert {k:v for k,v in case['native_producer_source_sha256'].items()
                if k.startswith('mini_moonboard/')} == identity
        force = np.array(case['load']['force_xyz_n'])
        force[2] -= (case['model']['modeled_mass_kg']+case['load']['equipment_kg'])*9.80665
        force += sum((np.array(row['force_xyz_n']) for row in case['floor_resultants'].values()),np.zeros(3))
        assert max(abs(force)) <= .1
        assert all(row['force_xyz_n'][2] >= -.1 for row in case['floor_resultants'].values())


def test_nominal_bolt_comparison_does_not_hide_a_static_or_doubled_case():
    report = json.loads(Path('fea/results/current-frame-response.json').read_text())
    cases = {row['name']:row for row in report['cases']}
    static = cases['current-response-static']
    doubled = cases['current-response-A12-150-refined']
    assert np.isclose(doubled['load']['force_xyz_n'][2],2*static['load']['force_xyz_n'][2])
    assert static['load']['force_xyz_n'][:2] == [0.,0.]
    assert doubled['load']['force_xyz_n'][:2] == [0.,300.]
    for case in (static,doubled):
        for bolt in case['leg_bolts'].values():
            assert np.isclose(bolt['conditional_nominal_diameter_ratio'],
                bolt['lateral_demand_n']/bolt['conditional_nominal_diameter_reference_n'])


def test_native_archive_and_refactor_witness_match_recorded_input():
    import hashlib
    import tarfile

    report = json.loads(Path('fea/results/current-frame-response.json').read_text())
    evidence = report['native_evidence']
    archive = Path(evidence['path'])
    assert hashlib.sha256(archive.read_bytes()).hexdigest() == evidence['sha256']
    witness = report['dependency_refactor_equivalence']
    assert witness['identical_native_input']
    assert witness['analyzed_native_deck_sha256'] == witness['refactored_native_deck_sha256']
    with tarfile.open(archive) as bundle:
        raw = bundle.extractfile('governing/cycle-00/frame.inp').read()
    assert hashlib.sha256(raw).hexdigest() == witness['analyzed_native_deck_sha256']
    assert {'fea/dowel_yield.py','fea/reinforced_timber_resistance.py',
            'fea/reinforced_fastener_checks.py','docs/reinforced-fastener-applicability.json'} <= report['sources_sha256'].keys()
