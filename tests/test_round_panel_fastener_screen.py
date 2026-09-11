"""Fresh probe identities and evidence-source coverage cannot inherit old counts."""
import json
from pathlib import Path

import pytest

from fea import round_panel_fastener_screen as screen
from fea import round_panel_frame, round_service_floor


def test_fresh_round_source_closures_include_layout_and_head_reference():
    for sources in (round_panel_frame.source_hashes(), round_service_floor.sources()):
        assert 'mini_moonboard/round_panel_layout.py' in sources
        assert 'docs/round-panel-countersink-reference.json' in sources


def test_round_fastener_screen_requires_three_distinct_hold_probes(tmp_path, monkeypatch):
    def authenticated(root, **kwargs):
        assert (kwargs['screw_count'], kwargs['case_count'], kwargs['coupled_count']) == (56, 3, 3)
        return {'limits': '', 'input_sha256': {}, 'qualified_for_design': False}

    monkeypatch.setattr(screen.shared, 'build', authenticated)
    cases = []
    for hold in ('F10', 'C6', 'C10'):
        directory = tmp_path/hold
        (directory/'cycle-00').mkdir(parents=True)
        (directory/'report.json').write_text(json.dumps({'final_cycle_directory': 'cycle-00'}))
        (directory/'cycle-00/input.json').write_text(json.dumps({
            'hold': hold, 'pounds': 250., 'load_kind': 'full', 'panel_screw_count': 56,
            'stiffness_n_per_mm': 1000.}))
        cases.append({'case': hold})
    (tmp_path/'summary.json').write_text(json.dumps({'cases': cases}))
    result = screen.build(tmp_path)
    assert result['qualified_for_design'] is False
    assert 'does not isolate screw count' in result['limits']
    assert str(Path(screen.__file__).resolve().relative_to(Path.cwd())) in result['input_sha256']
    record_path = tmp_path/'C10/cycle-00/input.json'
    record = json.loads(record_path.read_text())
    record['hold'] = 'F10'
    record_path.write_text(json.dumps(record))
    with pytest.raises(ValueError, match='independent C10'):
        screen.build(tmp_path)


def test_layout_gate_rejects_missing_face_screw():
    from fea.round_service_audit import panel_layout_gate
    from mini_moonboard import round_service_frame as model

    screws = [c for c in model.connections() if isinstance(c, model.timber.PanelScrew)]
    assert panel_layout_gate(screws)['passed']
    result = panel_layout_gate(screws[1:])
    assert not result['passed']
    assert result['missing'] == [screws[0].name]
