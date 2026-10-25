from pathlib import Path

import pytest

from scripts import publish_center_far_row_viewer as publisher

ROOT = Path(__file__).resolve().parents[1]


def test_public_check_does_not_open_ignored_sources(monkeypatch):
    real = publisher.local_path

    def site_only(root, name):
        assert name.startswith('site/')
        return real(root, name)

    monkeypatch.setattr(publisher, 'local_path', site_only)
    result = publisher.check(ROOT)
    assert result['parts'] == 1105
    assert result['bolt_stacks'] == 108
    assert result['new_mesh_payloads'] == 1
    assert result['ignored_inputs_read'] is False
    assert result['geometry_adopted'] is False


@pytest.fixture
def target(tmp_path, monkeypatch):
    payloads = {name: (ROOT / name).read_bytes() for name in (publisher.SCENE, publisher.PROVENANCE)}
    monkeypatch.setattr(publisher, 'prepare', lambda *_: payloads)
    parent = tmp_path / publisher.PARENT['path']
    parent.parent.mkdir(parents=True)
    parent.write_bytes((ROOT / publisher.PARENT['path']).read_bytes())
    return tmp_path


def test_late_provenance_conflict_preserves_existing_bytes_and_prevents_partial_copy(target):
    conflict = target / publisher.PROVENANCE
    conflict.write_bytes(b'preserved owner bytes\n')
    with pytest.raises(ValueError, match='Preserve existing differing file'):
        publisher.publish(ROOT, target)
    assert conflict.read_bytes() == b'preserved owner bytes\n'
    assert not (target / publisher.SCENE).exists()


def test_frozen_asset_publication_is_idempotent(target):
    publisher.publish(ROOT, target)
    stamps = {name: (target / name).stat().st_mtime_ns for name in (publisher.SCENE, publisher.PROVENANCE)}
    publisher.publish(ROOT, target)
    for name, stamp in stamps.items():
        assert (target / name).stat().st_mtime_ns == stamp
        assert (target / name).read_bytes() == (ROOT / name).read_bytes()
