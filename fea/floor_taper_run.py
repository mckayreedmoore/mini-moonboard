"""Isolated Coulomb producer for the actual tapered-leg candidate.

This wrapper preserves older runner files and their evidence identities. Source
snapshots include this adapter, its native mesher and the selected taper model.
Factory substitutions are serial, scoped and restored after success or failure.
"""
import hashlib
from pathlib import Path

from fea import current_coulomb_run as native
from fea.floor_taper_mesh import prepare_taper
from mini_moonboard import compact_floor_taper_frame as candidate

ORIGINAL_SOURCES = native.sources


def sources():
    result = ORIGINAL_SOURCES()
    for source in native.base.repository_source_closure([Path(__file__),Path(candidate.__file__)]):
        result[str(source.resolve().relative_to(Path.cwd()))] = hashlib.sha256(source.read_bytes()).hexdigest()
    return result


LOADED_SOURCES = sources()


def run(output, *, module=candidate, **kwargs):
    if module.KEY != candidate.KEY or not getattr(module,'TAPER_NATIVE_GEOMETRY_REQUIRED',False):
        raise ValueError('Taper producer requires explicit tapered-leg candidate')
    if ORIGINAL_SOURCES()!=native.LOADED_SOURCES or sources()!=LOADED_SOURCES:
        raise ValueError('Restart taper runner after source changes')
    old_prepare,old_recess,old_sources,old_loaded=native.prepare,native.prepare_recess,native.sources,native.LOADED_SOURCES
    try:
        native.prepare=prepare_taper
        native.prepare_recess=prepare_taper
        native.sources=sources
        native.LOADED_SOURCES=LOADED_SOURCES
        return native.run(output,module=module,**kwargs)
    finally:
        native.prepare=old_prepare
        native.prepare_recess=old_recess
        native.sources=old_sources
        native.LOADED_SOURCES=old_loaded
