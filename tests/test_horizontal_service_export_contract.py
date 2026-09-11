"""Catch wrong-candidate audit selection without rebuilding the CAD assembly."""
import json
from pathlib import Path

from fea import horizontal_service_audit as audit
from mini_moonboard import horizontal_service_exports as exports


def test_export_reads_saved_horizontal_candidate_audit():
    assert exports.AUDIT == Path('fea/results/horizontal-service-audit-v1.json')
    saved = json.loads(exports.AUDIT.read_text())
    assert saved['candidate'] == exports.model.KEY == 'horizontal-service-development'


def test_audit_excludes_only_output_consumers_and_keeps_geometry_sources(monkeypatch):
    excluded = {'mini_moonboard/horizontal_service_exports.py',
                'mini_moonboard/horizontal_service_drilling.py'}
    expected = (set(audit.previous_audit.sources()) | {
        'fea/horizontal_service_audit.py', 'docs/led-wiring-reference.json'})-excluded
    original = audit.sources()
    assert set(original) == expected
    assert {'mini_moonboard/horizontal_service_frame.py', 'mini_moonboard/horizontal_service_wiring.py',
            'mini_moonboard/connection_geometry.py', 'docs/led-wiring-reference.json'} <= expected
    read = Path.read_bytes
    changed = {Path(name).resolve() for name in excluded}
    monkeypatch.setattr(Path, 'read_bytes', lambda path: read(path)+b'changed'
                        if path.resolve() in changed else read(path))
    assert audit.sources() == original
    producer = 'mini_moonboard/horizontal_service_wiring.py'
    changed.add(Path(producer).resolve())
    refreshed = audit.sources()
    assert refreshed[producer] != original[producer]
    assert {name for name in original if refreshed[name] != original[name]} == {producer}
