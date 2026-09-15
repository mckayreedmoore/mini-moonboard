import pytest

from fea import floor_taper_run as adapter
from fea.floor_taper_mesh import prepare_taper


def test_taper_wrapper_records_new_sources_and_restores_factories_on_failure(monkeypatch):
    native=adapter.native
    original=(native.prepare,native.prepare_recess,native.sources,native.LOADED_SOURCES)
    def fail(*args,**kwargs):
        assert native.prepare is prepare_taper
        assert native.sources()==native.LOADED_SOURCES
        assert 'fea/floor_taper_run.py' in native.LOADED_SOURCES
        assert 'fea/floor_taper_mesh.py' in native.LOADED_SOURCES
        assert 'mini_moonboard/compact_floor_taper_frame.py' in native.LOADED_SOURCES
        raise RuntimeError('deliberate preparation failure')
    monkeypatch.setattr(native,'run',fail)
    with pytest.raises(RuntimeError,match='deliberate preparation'):
        adapter.run('unused',mu=.5)
    assert (native.prepare,native.prepare_recess,native.sources,native.LOADED_SOURCES)==original
