import copy
import gzip
import json
from pathlib import Path

import pytest

from scripts import publish_v11_v9_eight_bolt_viewer as publisher

ROOT = Path(__file__).resolve().parents[1]
SCENE = json.loads(gzip.decompress((ROOT / publisher.SCENE).read_bytes()))


def test_public_check_reads_only_portable_site_and_owner_v9_records(monkeypatch):
    real = Path.read_bytes
    records = {(ROOT / ref['path']).resolve() for ref in
               (publisher.OWNER, publisher.V9_LAYOUT, publisher.PUBLIC_RECEIPT)}

    def tracked_only(path):
        resolved = path.resolve()
        assert resolved.is_relative_to(ROOT / 'site') or resolved in records, path
        return real(path)

    monkeypatch.setattr(Path, 'read_bytes', tracked_only)
    result = publisher.check(ROOT)
    assert result['parts'] == 1109
    assert result['bolt_stacks'] == 112
    assert result['ignored_inputs_read'] is False
    assert result['analysis_pending'] is True
    assert result['historical_capacity_transferred'] is False


@pytest.mark.parametrize('change', ['old_owner', 'old_parent', 'old_census', 'one_leaf', 'bond_claim', 'prior_bank', 'weight', 'release'])
def test_geometry_contract_rejects_scope_and_claim_transfer(change):
    data = copy.deepcopy(SCENE)
    if change == 'old_owner':
        data['owner_request']['sha256'] = '0' * 64
    elif change == 'old_parent':
        data['parent_scene']['sha256'] = '0' * 64
    elif change == 'old_census':
        data['part_count'] = 1125
    elif change == 'one_leaf':
        data['joint_contract']['cleat_joints'][0]['leaf_count'] = 1
    elif change == 'bond_claim':
        data['actual_bond_qualified'] = True
    elif change == 'prior_bank':
        data['current_response_computed'] = True
    elif change == 'weight':
        data['weight_response'] = {'mass_kg': 100}
    else:
        data['fabrication_released'] = True
    with pytest.raises(ValueError):
        publisher.geometry_contract(data)


@pytest.fixture
def target(tmp_path, monkeypatch):
    payloads = {name: (ROOT / name).read_bytes() for name in (publisher.SCENE, publisher.PROVENANCE, publisher.OVERLAY)}
    monkeypatch.setattr(publisher, 'prepare', lambda *_: payloads)
    for ref in (publisher.OWNER, publisher.V9_SCENE, publisher.V9_LAYOUT, publisher.PUBLIC_RECEIPT):
        destination = tmp_path / ref['path']
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes((ROOT / ref['path']).read_bytes())
    return tmp_path


def test_late_conflict_preserves_existing_file_and_prevents_partial_copy(target):
    conflict = target / publisher.OVERLAY
    conflict.write_bytes(b'preserve owner bytes\n')
    with pytest.raises(ValueError, match='Preserve existing differing file'):
        publisher.publish(ROOT, target)
    assert conflict.read_bytes() == b'preserve owner bytes\n'
    assert not (target / publisher.SCENE).exists()
    assert not (target / publisher.PROVENANCE).exists()


def test_frozen_publication_is_idempotent(target):
    publisher.publish(ROOT, target)
    names = (publisher.SCENE, publisher.PROVENANCE, publisher.OVERLAY)
    stamps = {name: (target / name).stat().st_mtime_ns for name in names}
    publisher.publish(ROOT, target)
    for name, stamp in stamps.items():
        assert (target / name).stat().st_mtime_ns == stamp
        assert (target / name).read_bytes() == (ROOT / name).read_bytes()


def test_public_check_rejects_a_changed_runtime_module(target):
    publisher.publish(ROOT, target)
    module = target / publisher.OVERLAY
    module.write_bytes(module.read_bytes() + b'\n')
    with pytest.raises(ValueError, match='Source bytes differ'):
        publisher.check(target)
