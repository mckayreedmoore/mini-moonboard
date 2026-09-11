"""Panel equilibrium includes unilateral seating reactions, without resistance credit."""
import copy
import json

from fea import round_insert_load_assessment as assessment


def test_panel_wrench_includes_seating_and_retains_unknown_resistance(tmp_path, monkeypatch):
    job = tmp_path/'cycle-00'
    job.mkdir()
    for name in ('frame.dat', 'frame.frd', 'frame.12d'):
        (job/name).write_text('authenticated by test replacement')
    contact = {'name': 'seat', 'panel': 'main', 'scalar_nodes': [10, 11],
               'normal_stiffness_n_per_mm': 1000., 'inward_xyz': [0., 0., 1.],
               'point_xyz_mm': [0., 0., 0.]}
    record = {'candidate': 'round-insert-development', 'hold': 'F10', 'seating_contacts': [contact]}
    report = {'final_cycle_directory': 'cycle-00', 'parameters': {},
              'connector_forces': {'seat': {'force_on_first_xyz_n': [0., 0., 5.]}}}
    panel = {'panel': 'main', 'force_residual_n': [0., 0., 5.], 'moment_residual_nmm': [0.]*3,
             'force_rounding_interval_radius_n': [0.]*3, 'moment_rounding_interval_radius_nmm': [0.]*3,
             'attachments': [{'connection': 'insert', 'withdrawal_n': 100.}]}
    monkeypatch.setattr(assessment.frame, 'authenticated_input', lambda _: (record, {'verified': True}))
    monkeypatch.setattr(assessment, 'recover', lambda *args: ('', {}, {10: [1.e-8]*3, 11: [1.e-8]*3}))
    monkeypatch.setattr(assessment, 'panel_balance', lambda *args: [copy.deepcopy(panel)])
    (tmp_path/'report.json').write_text(json.dumps(report))
    result = assessment.build(tmp_path)
    assert result['all_panel_wrench_intervals_passed']
    assert result['panels'][0]['seating_contact_count'] == 1
    assert result['qualified_withdrawal_resistance_n'] is None
    assert result['qualified_head_pull_through_resistance_n'] is None
    assert result['effective_thread_engagement_mm'] is None
    assert not result['insert_demands_qualified'] and not result['insert_resistance_qualified']
    report['connector_forces']['seat']['force_on_first_xyz_n'][2] = 4.
    (tmp_path/'report.json').write_text(json.dumps(report))
    assert not assessment.build(tmp_path)['all_panel_wrench_intervals_passed']
