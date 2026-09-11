"""Reference diagnostics retain signs and never become construction acceptance."""
import hashlib
import json
import tarfile
from pathlib import Path

import pytest

from fea import infill_connection_screen as screen


def fixture(reaction):
    candidate = 'infill-panel-development'
    cases = [{'candidate': candidate, 'case_id': label, 'panel': 'main_lower_left',
              'mesh_mm': 25., 'linear_250_over_300_scale': .8,
              'ideal_screw_normal_reactions_n': {'screw': reaction}}
             for label in ('D6', 'D7', 'H6', 'H7', 'F3', 'F10', 'G3', 'G10')]
    return {'revised': candidate, 'cases': cases, 'comparison': {'reaction_refinement_checks': [
        {'candidate': candidate, 'case_id': c['case_id'],
         'individual_reactions': [{'connection': 'screw', 'passed': False}]} for c in cases]}}


@pytest.mark.parametrize('reaction,tension', [(100., 0.), (-100., 80.), (-2000., 1600.)])
def test_tension_sign_scaling_and_false_qualification(reaction, tension):
    ref = json.loads(screen.REFERENCE.read_text())
    result = screen.assess(fixture(reaction), ref)
    peak = result['maximum_ideal_tension']
    assert peak['ideal_tension_250lb_n'] == tension
    assert peak['normal_only_250lb_over_unadjusted_withdrawal'] == pytest.approx(
        tension/(133*1.24*screen.LBF_N))
    assert result['rows_above_unadjusted_withdrawal_reference'] == (8 if tension > 733.601 else 0)
    for flag in ('qualified_for_design', 'joint_strength_passed', 'actual_demands_available',
                 'material_applicability_verified', 'individual_reaction_refinement_passed'):
        assert result[flag] is False
    assert not any(r['qualified_connection'] for r in result['rows'])


def test_published_connection_ledger_replays_archived_panel_report():
    with tarfile.open('fea/results/infill-panel-comparison-v1.tar.xz', mode='r|xz') as archive:
        report_bytes = next(archive.extractfile(member).read() for member in archive
                            if member.isfile() and member.name == 'report.json')
    report = json.loads(report_bytes)
    saved = json.loads(Path('fea/results/infill-connection-screen-v1.json').read_text())
    assert saved['panel_report_sha256'] == hashlib.sha256(report_bytes).hexdigest()
    assert {'fea/infill_connection_screen.py', str(screen.REFERENCE)} <= saved['source_sha256'].keys()
    assert saved['source_sha256'].items() >= report['source_sha256'].items()
    for name, sha in saved['source_sha256'].items():
        assert hashlib.sha256(Path(name).read_bytes()).hexdigest() == sha, name
    reference = json.loads(screen.REFERENCE.read_text())
    assert saved['reference'] == reference
    replay = screen.assess(report, reference)
    assert replay == {key: value for key, value in saved.items()
                      if key not in ('source_sha256', 'panel_report_sha256')}
    assert saved['candidate'] == report['revised'] == 'infill-panel-development'
    for flag in ('qualified_for_design', 'joint_strength_passed', 'actual_demands_available',
                 'material_applicability_verified', 'individual_reaction_refinement_passed'):
        assert saved[flag] is False
    assert not any(row['qualified_connection'] for row in saved['rows'])
