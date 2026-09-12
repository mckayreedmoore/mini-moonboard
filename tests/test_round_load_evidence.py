"""Replay load probes and prove they retain the final 56-attachment parent."""
import hashlib
import json
import tarfile
from pathlib import Path

import numpy as np
import pytest
from evidence_assertions import assert_replay_value

from fea import horizontal_frame_stress as stress
from fea import horizontal_panel_frame as frame
from fea import panel_load_sensitivity as load

SCENARIOS = {'body-x1': (1., 300., 100.), 'no-horizontal': (2., 0., 100.),
             'zero-standoff': (2., 300., 0.)}


@pytest.fixture(scope='module')
def evidence():
    def read(path):
        with tarfile.open(path) as archive:
            members = [m for m in archive if m.isfile()]
            assert len({m.name for m in members}) == len(members)
            return {m.name: archive.extractfile(m).read() for m in members}
    return (read('fea/results/round-load-sensitivity-v1.tar.gz'),
            read('fea/results/round-frame-batch-v1.tar.gz'))


@pytest.mark.parametrize('name,values', SCENARIOS.items())
def test_round_load_archive_authenticates_parent_and_replays(evidence, name, values):
    files, parent_files = evidence
    digest = lambda b: hashlib.sha256(b).hexdigest()
    summary = json.loads(files['summary.json'])
    assert {c['case'] for c in summary['cases']} == SCENARIOS.keys()
    assert len(summary['cases']) == 3 and not summary['qualified_for_design']
    root = name+'/'
    report = json.loads(files[root+'report.json'])
    case = next(c for c in summary['cases'] if c['case'] == name)
    assert digest(files[root+'report.json']) == case['report_sha256']
    for source, sha in report['source_sha256'].items():
        assert digest(files[root+'source_snapshots/'+source]) == sha
    for artifact, sha in report['artifact_sha256'].items():
        assert digest(files[root+artifact]) == sha
    for cycle in report['contact_cycles']:
        assert digest(files[root+cycle['directory']+'/report.json']) == cycle['report_sha256']
    parent_report = json.loads(parent_files['f10-k1000/report.json'])
    parent_input = 'f10-k1000/'+parent_report['final_cycle_directory']+'/input.json'
    provenance = report['screw_sensitivity']['parent']
    assert provenance['report_sha256'] == digest(parent_files['f10-k1000/report.json'])
    assert provenance['input_sha256'] == digest(parent_files[parent_input])
    assert provenance['source_sha256'] == parent_report['source_sha256']
    assert report['screw_sensitivity']['removed'] == []
    parent = json.loads(parent_files[parent_input])
    final = root+report['final_cycle_directory']+'/'
    record = json.loads(files[final+'input.json'])
    assert record['candidate'] == parent['candidate'] == 'round-bore-service-development'
    assert record['panel_screw_count'] == parent['panel_screw_count'] == 56
    assert record['hold'] == 'F10'
    for key in ('nodes', 'elements', 'members', 'equations', 'fixed_nodes', 'panel_nodes',
                'round_service_bores', 'panel_patch_mm', 'stiffness_n_per_mm'):
        assert record[key] == parent[key], key
    strip_active = lambda rows: [{k: v for k, v in r.items() if k != 'active'} for r in rows]
    assert strip_active(record['springs']) == strip_active(parent['springs'])
    expected = load.change_load(parent, *values)
    assert record['load_assumption_scenario'] == expected['load_assumption_scenario']
    actual_loads = {int(n): f for n, f in record['loads'].items()}
    assert actual_loads.keys() == expected['loads'].keys()
    assert np.array(list(actual_loads.values())) == pytest.approx(
        np.array([expected['loads'][n] for n in actual_loads]), abs=1e-7, rel=0.)
    data = files[final+'frame.dat'].decode()
    for key, value in frame.assess(record, data).items():
        assert_replay_value(report[key], value, key)
    assert report['diagnostic_stress'] == json.loads(json.dumps(stress.assess(record, data)))
    assert report['contact_diagnostic_checks_passed']
    assert report['closed_bearing_assumption_passed']
    assert not report['qualified_for_design']
    assert not report['actual_joint_demands_qualified']


def test_saved_insert_assessment_authenticates_nominal_arithmetic_only():
    from fea.round_insert_repair_assessment import dimensional_screen

    report = json.loads(Path('fea/results/round-insert-repair-v1/report.json').read_text())
    assert report['dimensional_screen'] == dimensional_screen()
    for field in ('physical_tests_performed', 'damaged_wood_assessed', 'authorized_for_climbing'):
        assert report[field] is False
    for source, sha in report['source_sha256'].items():
        assert hashlib.sha256(Path(source).read_bytes()).hexdigest() == sha
