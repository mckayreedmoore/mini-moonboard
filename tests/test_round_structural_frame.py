"""Current screw runner cannot silently consume insert geometry or provenance."""
import json
from types import SimpleNamespace

import pytest

from fea import horizontal_panel_frame as frame
from fea import round_structural_frame as diagnostic
from mini_moonboard import round_structural_frame as cad


def test_seating_cut_matches_current_screw_and_preserves_future_reserve_material():
    import cadquery as cq

    connection = cad.panel_connections()[0]
    wrapped = diagnostic.SeatingModule(cad).panel_connections()[0]
    assert wrapped.members == connection.members
    cut = wrapped.receiver_cut()
    face = connection.start + connection.direction*cad.wide.PANEL
    transverse = connection.direction.cross(cq.Vector(1, 0, 0)).normalized()
    assert not diagnostic.shared.has_seating_material(face, connection.direction, [cut])
    # A point inside the hypothetical 12 mm insert opening but outside the
    # occupied 4.1402 mm screw must remain available for seating contact.
    assert diagnostic.shared.has_seating_material(face+transverse*4., connection.direction, [cut])


def test_prepare_uses_current_axes_and_source_bound_cache_without_native_solver(monkeypatch):
    calls = []
    fingerprint = {'current': 'first'}
    monkeypatch.setattr(diagnostic, 'sources', lambda: fingerprint.copy())

    def fresh(module, **parameters):
        calls.append((module, parameters))
        structure = frame.Structure()
        structure.springs = [{'name': c.name, 'stiffness_n_per_mm': 1000.}
                             for c in module.panel_connections()]
        return structure, {'candidate': module.KEY, 'limits': '', 'nested': [1]}

    monkeypatch.setattr(frame, 'current_frame', fresh)
    diagnostic.base_frame.cache_clear()
    try:
        first, metadata = diagnostic.prepare(cad, contact=False, panel_stiffness=100.)
        assert calls[0][0] is cad
        assert metadata['candidate'] == cad.KEY
        assert metadata['panel_screw_count'] == 56
        assert metadata['panel_attachment_names'] == sorted(c.name for c in cad.panel_connections())
        rows = cad.attachment_datums()
        assert {r['s'] for r in rows if r['role'] == 'service'} == {1134.2, 1278.25}
        assert metadata['panel_screw_connections_qualified'] is False
        assert 'insert_connections_qualified' not in metadata
        first.loads[999] = [1, 2, 3]
        metadata['nested'].append(2)
        second, clean = diagnostic.prepare(cad, contact=False, panel_stiffness=10000.)
        assert len(calls) == 1 and not second.loads and clean['nested'] == [1]
        assert {r['stiffness_n_per_mm'] for r in second.springs} == {10000.}
        fingerprint['current'] = 'second'
        diagnostic.prepare(cad, contact=False)
        assert len(calls) == 2
    finally:
        diagnostic.base_frame.cache_clear()


def test_prepare_rejects_insert_candidate_before_mesh_generation():
    with pytest.raises(ValueError, match='current structural-screw candidate'):
        diagnostic.prepare(SimpleNamespace(KEY='round-insert-development'))


def test_authenticated_replay_rejects_insert_archive(tmp_path):
    (tmp_path/'report.json').write_text(json.dumps({
        'contact_diagnostic_checks_passed': True, 'source_sha256': {},
        'artifact_sha256': {}, 'final_cycle_directory': 'cycle-00'}))
    job = tmp_path/'cycle-00'
    job.mkdir()
    (job/'input.json').write_text(json.dumps({'candidate': 'round-insert-development'}))
    with pytest.raises(ValueError, match='Unsupported current structural-screw mechanics'):
        diagnostic.authenticated_input(tmp_path)


def test_provenance_includes_current_runner_and_shared_contact_implementation():
    sources = diagnostic.sources()
    assert {'fea/round_structural_frame.py', 'fea/round_insert_frame.py',
            'mini_moonboard/round_structural_frame.py',
            'mini_moonboard/round_structural_wiring.py'} <= sources.keys()
