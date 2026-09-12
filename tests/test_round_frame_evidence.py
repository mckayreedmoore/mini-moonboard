"""Authenticate and replay published native round-frame evidence without a solver."""
import hashlib
import json
import tarfile
from pathlib import Path

import pytest
from evidence_assertions import assert_replay_value, assert_stress_replay

from fea import horizontal_frame_stress as stress
from fea import horizontal_panel_frame as frame

ARCHIVE = Path('fea/results/round-frame-batch-v1.tar.gz')
CASES = {'f10-k1000': 'F10', 'c6-k1000': 'C6', 'c10-k1000': 'C10'}


@pytest.fixture(scope='module')
def evidence():
    with tarfile.open(ARCHIVE, 'r:gz') as archive:
        members = [member for member in archive.getmembers() if member.isfile()]
        assert len({member.name for member in members}) == len(members)
        return {member.name.removeprefix('./'): archive.extractfile(member).read()
                for member in members}


def test_round_archive_authenticates_all_sources_and_native_artifacts(evidence):
    summary = json.loads(evidence['summary.json'])
    assert {case['case'] for case in summary['cases']} == CASES.keys()
    assert len(summary['cases']) == 3
    for case in summary['cases']:
        root = case['case']+'/'
        payload = evidence[root+'report.json']
        assert hashlib.sha256(payload).hexdigest() == case['report_sha256']
        report = json.loads(payload)
        assert {'mini_moonboard/round_service_frame.py', 'mini_moonboard/round_panel_layout.py',
                'mini_moonboard/round_service_wiring.py', 'fea/round_panel_frame.py',
                'docs/round-panel-countersink-reference.json'} <= report['source_sha256'].keys()
        assert report['artifact_sha256']
        for name, digest in report['source_sha256'].items():
            assert hashlib.sha256(evidence[root+'source_snapshots/'+name]).hexdigest() == digest
        for name, digest in report['artifact_sha256'].items():
            assert hashlib.sha256(evidence[root+name]).hexdigest() == digest
        for cycle in report['contact_cycles']:
            assert hashlib.sha256(evidence[root+cycle['directory']+'/report.json']).hexdigest() == cycle['report_sha256']


@pytest.mark.parametrize('case,hold', CASES.items())
def test_round_final_cycle_replays_diagnostics_without_qualification(evidence, case, hold):
    root = case+'/'
    report = json.loads(evidence[root+'report.json'])
    final = root+report['final_cycle_directory']+'/'
    record = json.loads(evidence[final+'input.json'])
    assert record['candidate'] == 'round-bore-service-development'
    assert record['hold'] == hold
    assert record['mode'] == 'coupled' and record['load_kind'] == 'full'
    assert record['pounds'] == 250. and record['stiffness_n_per_mm'] == 1000.
    assert record['panel_screw_count'] == 56
    bores = record['round_service_bores']
    assert len({bore['name'] for bore in bores}) == len(bores) == 32
    assert all(bore['diameter_mm'] == 25.4 and not bore['qualified_for_machining'] for bore in bores)
    names = {spring['name'] for spring in record['springs'] if spring['name'].startswith(('round_panel_', 'round_kicker_'))}
    assert len(names) == 56
    assert sum(name.startswith('round_kicker_') for name in names) == 8
    assert record['qualified_for_design'] is False
    assert record['actual_joint_demands_qualified'] is False
    data = evidence[final+'frame.dat'].decode()
    replay = frame.assess(record, data)
    for key, value in replay.items():
        assert_replay_value(report[key], value, key, record, data)
    assert_stress_replay(report['diagnostic_stress'], json.loads(json.dumps(stress.assess(record, data))))
    for gate in ('qualified_for_design', 'member_strength_passed', 'plywood_strength_passed'):
        assert report['diagnostic_stress'][gate] is False
    assert report['qualified_for_design'] is False
    assert report['actual_joint_demands_qualified'] is False
    assert report['contact_active_set_converged'] is report['closed_bearing_assumption_passed']
    assert report['contact_diagnostic_checks_passed'] is bool(
        report['contact_active_set_converged'] and report['global_equilibrium_passed']
        and report['mpc_check_passed'])
