"""Selected flush-top native producer must authenticate and freeze its full path."""
import pytest


def test_source_guard_covers_selected_native_producer_path():
    from fea import compact_spliced_flush_top_run as adapter

    assert {
        'fea/compact_spliced_flush_top_run.py',
        'fea/floor_uncut_mesh.py',
        'mini_moonboard/compact_spliced_flush_top.py',
        'scripts/compact_spliced_flush_top_study.py',
        'scripts/compact_rail_study.py',
    } <= adapter.sources().keys()


def test_wrapper_injects_selected_candidate_and_exact_prepare_then_restores_native(monkeypatch):
    from fea import compact_spliced_flush_top_run as adapter

    native = adapter.native
    original = native.source_hashes, native.LOADED_SOURCE_SHA256
    captured = {}

    def fail(output, **kwargs):
        captured.update(output=output, **kwargs)
        assert native.source_hashes() == native.LOADED_SOURCE_SHA256
        raise RuntimeError('deliberate native failure')

    monkeypatch.setattr(native, 'run', fail)
    with pytest.raises(RuntimeError, match='deliberate native failure'):
        adapter.run('unused', hold='A12')

    assert captured['module'] is adapter.candidate
    assert captured['expected_candidate'] == adapter.candidate.KEY
    assert captured['prepare_factory'] is adapter.prepare_uncut
    assert captured['hold'] == 'A12'
    assert (native.source_hashes, native.LOADED_SOURCE_SHA256) == original


@pytest.mark.parametrize('override', ['module', 'expected_candidate', 'prepare_factory'])
def test_wrapper_rejects_native_identity_overrides(override):
    from fea import compact_spliced_flush_top_run as adapter

    with pytest.raises(ValueError, match='cannot be overridden'):
        adapter.run('unused', **{override: object()})


def test_wrapper_rejects_loaded_source_drift(monkeypatch):
    from fea import compact_spliced_flush_top_run as adapter

    monkeypatch.setattr(adapter, 'LOADED_SOURCES', {})
    with pytest.raises(ValueError, match='Restart selected flush-top runner'):
        adapter.run('unused')
