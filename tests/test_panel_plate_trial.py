"""The plate concept cannot promote conditional arithmetic into a release."""
import hashlib
import json
from pathlib import Path

import cadquery as cq
import pytest

from fea import panel_plate_trial as trial


def test_full_thread_embedding_and_sensitivity_failure():
    service = trial.calculation(1725.5855201072811)
    sensitivity = trial.calculation(2022.908)
    assert service['gross_wood_penetration_mm'] == pytest.approx(62.70625)
    assert service['embedded_thread_including_tip_mm'] == pytest.approx(60.325)
    assert service['conditional_withdrawal_reference_n'] == pytest.approx(418*trial.LBF_N)
    assert not service['withdrawal_reference_exceeded']
    assert sensitivity['withdrawal_reference_exceeded']
    assert not service['qualification_passed'] and not sensitivity['qualification_passed']
    assert sensitivity['strip_bending_stress_mpa'] > service['strip_bending_stress_mpa']
    for invalid in (-1, float('nan'), float('inf')):
        with pytest.raises(ValueError):
            trial.calculation(invalid)


def test_saved_trial_replays_locations_references_and_artifacts():
    root = Path('exports/panel-plate-trial')
    saved = json.loads((root/'report.json').read_text())
    assert saved['placements'] == trial.placements()
    assert saved['reference'] == trial.REFERENCE
    for name, sha in saved['source_sha256'].items():
        assert hashlib.sha256(Path(name).read_bytes()).hexdigest() == sha, name
    for name, sha in saved['artifact_sha256'].items():
        assert hashlib.sha256((root/name).read_bytes()).hexdigest() == sha
    for row in saved['diagnostic_force_cases'].values():
        assert row == trial.calculation(row['force_n'])
    assert len(saved['placements']) == 119
    assert saved['upper_end_reference_failures']
    assert not saved['front_service_envelope_failures']
    assert not saved['plate_crosses_panel_edge']
    assert saved['plate_screw_collision_volume_mm3'] < .01
    assert saved['extended_shaft_fit']['checked_extended_shaft_count'] == 119
    assert not saved['extended_shaft_fit']['failures']
    assert not saved['extended_shaft_fit']['complete_replacement_fit_qualified']
    for flag in ('qualified_for_design', 'installed_in_current_frame',
                 'complete_frame_reanalysis_run', 'actual_connection_demands_available'):
        assert saved[flag] is False


def test_extended_shaft_detects_retained_hardware_obstruction(monkeypatch):
    row = trial.placements()[0]
    connection = next(c for c in trial.model.connections() if c.name == row['connection'])
    obstruction = cq.Solid.makeCylinder(3., 5., connection.start+connection.direction*60.,
                                       connection.direction)
    original = trial.model.hardware.clip_parts
    monkeypatch.setattr(trial.model.hardware, 'clip_parts', lambda stations:
        (*original(stations), trial.model.b.Part('injected_obstruction', obstruction,
                                                (6., 6., 5.), 'Negative test only', 1)))
    result = trial.deeper_fit([row])
    assert any('injected_obstruction' in r['retained_hardware_collisions'] for r in result['failures'])
