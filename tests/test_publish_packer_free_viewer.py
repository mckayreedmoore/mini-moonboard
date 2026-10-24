import copy
import gzip
import json
from pathlib import Path

import pytest

from scripts import publish_packer_free_viewer as publisher

ROOT = Path(__file__).resolve().parents[1]
SCENE = json.loads(gzip.decompress((ROOT / publisher.SCENE).read_bytes()))
EXPORT = json.loads((ROOT / publisher.EXPORT).read_bytes())
RECEIPT = json.loads((ROOT / publisher.RECEIPT['path']).read_bytes())


def test_portable_check_reads_only_public_site_assets_and_tracked_receipt(monkeypatch):
    real_path = publisher.local_path

    def tracked_only(root, relative):
        assert not relative.startswith('fea/'), relative
        return real_path(root, relative)

    monkeypatch.setattr(publisher, 'local_path', tracked_only)
    result = publisher.check(ROOT)
    assert result['parts'] == 1125
    assert result['bolt_stacks'] == 112
    assert result['new_stl_files'] == 0
    assert result['ignored_inputs_read'] is False
    assert result['matched_results_pending'] is True


@pytest.mark.parametrize('change', ['old_geometry', 'old_receipt', 'prior_bank', 'packer_census', 'unchecked_clearance'])
def test_publisher_rejects_geometry_or_status_transfer(change):
    scene, export, receipt = copy.deepcopy(SCENE), copy.deepcopy(EXPORT), copy.deepcopy(RECEIPT)
    if change == 'old_geometry':
        scene['geometry_source']['sha256'] = 'c06d790aaed7d915cc729afaf3f5e58c456429c18a79555f1faf182775129a37'
    elif change == 'old_receipt':
        receipt['checked_geometry']['sha256'] = 'c06d790aaed7d915cc729afaf3f5e58c456429c18a79555f1faf182775129a37'
    elif change == 'prior_bank':
        scene['current_own_response_bank_recorded'] = True
    elif change == 'packer_census':
        scene['counts']['occupied_parts'] = 1151
    else:
        receipt['nominal_geometry_clear'] = False
    with pytest.raises(ValueError):
        publisher.geometry_contract(export, scene, receipt)


@pytest.fixture
def portable_roots(tmp_path):
    source, target = tmp_path / 'source', tmp_path / 'target'
    # Exact public copies recover the two frozen inputs; no ignored real data is read by these tests.
    for ref, public_name in [(publisher.FROZEN_EXPORT, publisher.EXPORT), (publisher.FROZEN_SCENE, publisher.SCENE)]:
        destination = source / ref['path']
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes((ROOT / public_name).read_bytes())
    for root in (source, target):
        for ref in (publisher.RECEIPT, publisher.PARENT):
            destination = root / ref['path']
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes((ROOT / ref['path']).read_bytes())
    return source, target


def test_exact_frozen_byte_publication_is_idempotent(portable_roots):
    source, target = portable_roots
    first = publisher.publish(source, target)
    names = (publisher.SCENE, publisher.EXPORT, publisher.PROVENANCE)
    stamps = {name: (target / name).stat().st_mtime_ns for name in names}
    assert first['new_asset_bytes'] == 60712
    publisher.publish(source, target)
    for name in names:
        assert (target / name).read_bytes() == (ROOT / name).read_bytes()
        assert (target / name).stat().st_mtime_ns == stamps[name]


def test_late_conflict_preserves_existing_bytes_without_partial_asset_copy(portable_roots):
    source, target = portable_roots
    conflict = target / publisher.PROVENANCE
    conflict.write_bytes(b'preserve another owner\n')
    with pytest.raises(ValueError, match='Preserve existing differing file'):
        publisher.publish(source, target)
    assert conflict.read_bytes() == b'preserve another owner\n'
    assert not (target / publisher.SCENE).exists()
    assert not (target / publisher.EXPORT).exists()
