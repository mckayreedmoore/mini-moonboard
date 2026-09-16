"""The flush adapter must retain its contact model and restore shared factories."""
import pytest

from fea import floor_flush_run as adapter


def test_flush_wrapper_restores_factories_after_native_failure(monkeypatch):
    native = adapter.native
    original = (native.source_hashes, native.LOADED_SOURCE_SHA256)
    contacts = [{'name': 'required-face-contact'}]
    monitors = [{'name': 'required-top-gap'}]
    def contact_factory(module, *, stiffness_per_area):
        assert stiffness_per_area == 250.
        return contacts

    monkeypatch.setattr(adapter, 'face_contacts', contact_factory)
    monkeypatch.setattr(adapter, 'taper_top_monitors', lambda module: monitors)

    def fail(*args, **kwargs):
        assert kwargs['prepare_factory'] is adapter.prepare_flush
        assert kwargs['expected_candidate'] == adapter.candidate.KEY
        assert kwargs['member_contacts'] is contacts
        assert kwargs['clearance_monitors'] is monitors
        assert native.source_hashes() == native.LOADED_SOURCE_SHA256
        assert 'fea/floor_flush_mesh.py' in native.LOADED_SOURCE_SHA256
        raise RuntimeError('deliberate native failure')

    monkeypatch.setattr(native, 'run', fail)
    with pytest.raises(RuntimeError, match='deliberate native failure'):
        adapter.run('unused', contact_stiffness_per_area=250.)
    assert (native.source_hashes, native.LOADED_SOURCE_SHA256) == original


@pytest.mark.parametrize('override', ['member_contacts', 'clearance_monitors'])
def test_flush_contact_model_cannot_be_overridden(override):
    with pytest.raises(ValueError, match='cannot be silently overridden'):
        adapter.run('unused', **{override: []})


@pytest.mark.parametrize('stiffness', [0., -1., float('nan'), float('inf')])
def test_contact_penalty_rejects_nonphysical_values_before_geometry(stiffness):
    with pytest.raises(ValueError, match='positive and finite'):
        adapter.face_contacts(stiffness_per_area=stiffness)
