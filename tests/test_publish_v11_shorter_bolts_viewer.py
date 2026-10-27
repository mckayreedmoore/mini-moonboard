import json
from pathlib import Path

import pytest

from scripts import publish_v11_shorter_bolts_viewer as publisher

ROOT = Path(__file__).resolve().parents[1]


def test_git_only_check_never_opens_ignored_sources(monkeypatch):
    real = Path.read_bytes

    def public(path):
        assert path.resolve().is_relative_to(ROOT / 'site') or path.resolve().is_relative_to(ROOT / 'docs'), path
        return real(path)

    monkeypatch.setattr(Path, 'read_bytes', public)
    result = publisher.check(ROOT)
    assert result['parts'] == 1089 and result['stacks'] == 112 and result['spacers'] == 4
    assert result['ignored_inputs_read'] is False and result['historical_capacity_transferred'] is False


@pytest.fixture
def target(tmp_path, monkeypatch):
    payloads = {name: (ROOT / name).read_bytes() for name in (publisher.SCENE, publisher.PROVENANCE, publisher.OVERLAY)}
    monkeypatch.setattr(publisher, 'prepare', lambda _: payloads)
    for ref in (publisher.PARENT, publisher.OWNER, publisher.RECEIPT):
        p = tmp_path / ref['path']
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes((ROOT / ref['path']).read_bytes())
    return tmp_path


def test_publication_is_idempotent(target):
    publisher.publish(ROOT, target)
    paths = [target / name for name in (publisher.SCENE, publisher.PROVENANCE, publisher.OVERLAY)]
    stamps = [p.stat().st_mtime_ns for p in paths]
    publisher.publish(ROOT, target)
    assert stamps == [p.stat().st_mtime_ns for p in paths]


def test_late_conflict_prevents_any_partial_publication(target):
    conflict = target / publisher.OVERLAY
    conflict.write_bytes(b'preserve owner bytes\n')
    with pytest.raises(ValueError, match='Preserve existing differing file'):
        publisher.publish(ROOT, target)
    assert not (target / publisher.SCENE).exists()
    assert conflict.read_bytes() == b'preserve owner bytes\n'


def test_runtime_module_tampering_is_detected(target):
    publisher.publish(ROOT, target)
    p = target / publisher.OVERLAY
    p.write_bytes(p.read_bytes() + b'\n')
    with pytest.raises(ValueError):
        publisher.check(target)


def test_no_old_analysis_can_be_attached_to_the_geometry_contract():
    import gzip

    data = json.loads(gzip.decompress((ROOT / publisher.SCENE).read_bytes()))
    data['force_only'] = {'maximum': .842003}
    with pytest.raises(ValueError):
        publisher.contract(data)
