"""The flush adapter must retain its contact model and restore shared factories."""
import pytest

from fea import floor_flush_run as adapter


def test_flush_wrapper_restores_factories_after_native_failure(monkeypatch):
    native = adapter.native
    original = (native.prepare, native.prepare_recess, native.sources, native.LOADED_SOURCES)
    contacts = [{'name': 'required-face-contact'}]
    monitors = [{'name': 'required-top-gap'}]
    monkeypatch.setattr(adapter, 'face_contacts', lambda module: contacts)
    monkeypatch.setattr(adapter, 'taper_top_monitors', lambda module: monitors)

    def fail(*args, **kwargs):
        assert native.prepare is adapter.prepare_flush
        assert native.prepare_recess is adapter.prepare_flush
        assert kwargs['member_contacts'] is contacts
        assert kwargs['clearance_monitors'] is monitors
        assert native.sources() == native.LOADED_SOURCES
        assert 'fea/floor_flush_mesh.py' in native.LOADED_SOURCES
        raise RuntimeError('deliberate native failure')

    monkeypatch.setattr(native, 'run', fail)
    with pytest.raises(RuntimeError, match='deliberate native failure'):
        adapter.run('unused', mu=.4)
    assert (native.prepare, native.prepare_recess, native.sources, native.LOADED_SOURCES) == original


@pytest.mark.parametrize('override', ['member_contacts', 'clearance_monitors'])
def test_flush_contact_model_cannot_be_overridden(override):
    with pytest.raises(ValueError, match='cannot be silently overridden'):
        adapter.run('unused', mu=.4, **{override: []})
