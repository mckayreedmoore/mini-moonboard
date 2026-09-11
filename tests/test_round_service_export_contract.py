"""Check candidate selection and source closure without generating CAD."""
import json
from pathlib import Path

import pytest

from fea import round_service_audit as audit
from mini_moonboard import round_service_exports as exports


def test_saved_current_audit_matches_sources_and_requested_layout():
    report = json.loads(exports.AUDIT.read_text())
    assert report['candidate'] == exports.model.KEY
    assert report['source_sha256'] == audit.sources()
    assert report['panel_layout_gate']['passed']
    assert report['inventory']['panel_kicker_screws'] == 56
    assert report['inventory']['round_bores'] == 32
    assert report['all_tested_geometry_gates_passed']
    assert report['all_tested_product_geometry_gates_passed']
    assert not report['qualified_for_design']


def test_export_rejects_preceding_candidate_before_creating_outputs(tmp_path, monkeypatch):
    assert exports.AUDIT == Path('fea/results/round-service-audit-v1.json')
    assert exports.model.KEY == 'round-bore-service-development'
    wrong = tmp_path/'wrong.json'
    wrong.write_text(json.dumps({'candidate': 'horizontal-service-development', 'source_sha256': {}}))
    monkeypatch.setattr(exports, 'AUDIT', wrong)
    with pytest.raises(ValueError, match='Recompute the candidate geometry audit'):
        exports.export(tmp_path/'export', tmp_path/'viewer')
    assert not (tmp_path/'export').exists() and not (tmp_path/'viewer').exists()


def test_audit_excludes_output_consumers_but_authenticates_round_geometry(monkeypatch):
    excluded = {'mini_moonboard/round_service_exports.py', 'mini_moonboard/round_service_drilling.py'}
    expected = (set(audit.previous_audit.sources()) | {
        'fea/round_service_audit.py', 'docs/round-service-wiring-reference.json',
        'docs/round-panel-countersink-reference.json'})-excluded
    original = audit.sources()
    assert set(original) == expected
    assert {'mini_moonboard/round_service_frame.py', 'mini_moonboard/round_service_wiring.py',
            'mini_moonboard/split_center_hardware.py', 'mini_moonboard/round_panel_hardware.py',
            'docs/round-service-wiring-reference.json', 'docs/round-panel-countersink-reference.json',
            'docs/led-wiring-reference.json'} <= expected
    read = Path.read_bytes
    changed = {Path(name).resolve() for name in excluded}
    monkeypatch.setattr(Path, 'read_bytes', lambda path: read(path)+b'changed'
                        if path.resolve() in changed else read(path))
    assert audit.sources() == original
    producer = 'mini_moonboard/round_service_wiring.py'
    changed.add(Path(producer).resolve())
    refreshed = audit.sources()
    assert {name for name in original if refreshed[name] != original[name]} == {producer}
