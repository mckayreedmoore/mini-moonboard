"""Authenticated native response wrapper for selected spliced flush-top frame."""
import hashlib
from pathlib import Path

from fea import current_response_run as native
from fea.floor_uncut_mesh import prepare_uncut
from mini_moonboard import compact_spliced_flush_top as candidate

ORIGINAL_SOURCES = native.source_hashes


def sources():
    """Hash every source consumed by this candidate-specific native producer."""
    result = ORIGINAL_SOURCES()
    paths = native.repository_source_closure([Path(__file__), Path(candidate.__file__)])
    # Repository closure follows project-library imports. CLI and bolt-property
    # producer live under scripts/, so name those executable inputs explicitly.
    paths += [
        Path('scripts/compact_spliced_flush_top_study.py'),
        Path('scripts/compact_rail_study.py'),
    ]
    for source in paths:
        relative = str(source.resolve().relative_to(Path.cwd()))
        result[relative] = hashlib.sha256(source.read_bytes()).hexdigest()
    return result


LOADED_SOURCES = sources()


def run(output, **kwargs):
    """Run only selected candidate with exact-prism preparation."""
    protected = {'module', 'expected_candidate', 'prepare_factory'}
    if protected & kwargs.keys():
        raise ValueError('Selected candidate and exact prepare factory cannot be overridden')
    if ORIGINAL_SOURCES() != native.LOADED_SOURCE_SHA256 or sources() != LOADED_SOURCES:
        raise ValueError('Restart selected flush-top runner after source changes')
    old = native.source_hashes, native.LOADED_SOURCE_SHA256
    try:
        native.source_hashes = sources
        native.LOADED_SOURCE_SHA256 = LOADED_SOURCES
        return native.run(
            output,
            module=candidate,
            expected_candidate=candidate.KEY,
            prepare_factory=prepare_uncut,
            **kwargs,
        )
    finally:
        native.source_hashes, native.LOADED_SOURCE_SHA256 = old
