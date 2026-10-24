import copy
import gzip
import hashlib
import importlib.util
import json
from pathlib import Path

import pytest

MODULE = Path(__file__).resolve().parents[1]/'scripts/publish_eoere_v10.py'
spec = importlib.util.spec_from_file_location('candidate13_publisher_under_test', MODULE)
publisher = importlib.util.module_from_spec(spec)
spec.loader.exec_module(publisher)
ROOT = MODULE.parents[1]


def test_frozen_manifest_binds_all_delivery_and_paper_roots():
    manifest = publisher.load_manifest(ROOT/'site/eoere-v10-candidate13-provenance.json')
    assert len(publisher.records(manifest)) == 57
    assert sum(row['encoding'] == 'gzip' for row in publisher.records(manifest)) == 6
    assert manifest['retained_raw_evidence']['source_package_required_for_replay'] is True
    assert manifest['retained_raw_evidence']['archive_or_prune_authorized'] is False


def test_gzip_is_reproducible_and_roundtrips_original_bytes():
    raw = b'{"retained": "original bytes"}\n'*20000
    stored = publisher.deterministic_gzip(raw)
    assert stored == publisher.deterministic_gzip(raw)
    assert stored[4:8] == b'\0\0\0\0'
    assert gzip.decompress(stored) == raw


@pytest.mark.parametrize('name', ['/absolute', '../outside', 'a/../outside', 'a//b', 'a/./b', 'C:\\outside', 'a?b', 'a#b'])
def test_relocation_stays_inside_repository(tmp_path, name):
    with pytest.raises(ValueError, match='relative'):
        publisher.local_path(tmp_path, name)


def test_compressed_copy_must_match_both_integrated_and_decoded_original_bindings():
    manifest = publisher.load_manifest(ROOT/'site/eoere-v10-candidate13-provenance.json')
    row = manifest['artifacts']['geometry_raw']
    stored = (ROOT/row['integrated']['path']).read_bytes()
    original = publisher.verify_payload(row, stored)
    assert hashlib.sha256(original).hexdigest() == row['original']['sha256']
    with pytest.raises(ValueError, match='Integrated binding'):
        publisher.verify_payload(row, stored+b'x')
    bad = copy.deepcopy(row)
    bad['original']['sha256'] = 'a'*64
    with pytest.raises(ValueError, match='Decoded original'):
        publisher.verify_payload(bad, stored)


def test_release_or_source_mapping_mutations_fail_intake():
    manifest = publisher.load_manifest(ROOT/'site/eoere-v10-candidate13-provenance.json')
    for flag in publisher.FLAGS:
        with pytest.raises(ValueError, match='claim boundary'):
            publisher.validate_manifest({**manifest, flag: True})
    bad = copy.deepcopy(manifest)
    bad['artifacts']['geometry_raw']['integrated']['path'] = 'scripts/eoere_v10_geometry.py'
    with pytest.raises(ValueError, match='relocation'):
        publisher.validate_manifest(bad)


def test_every_portable_root_retains_original_bytes_and_joins():
    manifest = publisher.load_manifest(ROOT/'site/eoere-v10-candidate13-provenance.json')
    originals = {row['source_path']: publisher.verify_payload(row, (ROOT/row['integrated']['path']).read_bytes())
                 for row in publisher.records(manifest)}
    publisher.verify_joins(manifest, originals)
    bundle = json.loads(originals['delivery-bundle-13.json'])
    assert len(bundle['artifacts']) == 29
    assert bundle['physical_operations_authorized'] is False


def test_correction_cannot_be_replaced_by_earlier_loaded_edge_inference():
    manifest = publisher.load_manifest(ROOT/'site/eoere-v10-candidate13-provenance.json')
    originals = {row['source_path']: publisher.verify_payload(row, (ROOT/row['integrated']['path']).read_bytes())
                 for row in publisher.records(manifest)}
    path = 'paper-audit/center-principal-correction-13-v1.json'
    correction = json.loads(originals[path])
    correction['established_NDS_near_edge_violation'] = True
    originals[path] = json.dumps(correction).encode()
    with pytest.raises(ValueError, match='source join'):
        publisher.verify_joins(manifest, originals)


@pytest.fixture
def publication(tmp_path, monkeypatch):
    manifest = publisher.load_manifest(ROOT/'site/eoere-v10-candidate13-provenance.json')
    source, target = tmp_path/'source', tmp_path/'target'
    for row in publisher.records(manifest):
        stored = (ROOT/row['integrated']['path']).read_bytes()
        original = publisher.verify_payload(row, stored)
        destination = source/row['source_path']
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(original)
    # These tests exercise copy preflight and idempotence independently of the
    # already authenticated V9 parent files in the shared source checkout.
    monkeypatch.setattr(publisher, 'verify_parents', lambda *_: None)
    return manifest, source, target


def test_a_late_conflicting_file_stops_before_any_new_copy(publication):
    manifest, source, target = publication
    rows = publisher.records(manifest)
    conflict = target/rows[-1]['integrated']['path']
    conflict.parent.mkdir(parents=True, exist_ok=True)
    conflict.write_bytes(b'preserve another owner\n')
    with pytest.raises(ValueError, match='Preserve existing differing file'):
        publisher.publish(manifest, source, target)
    assert conflict.read_bytes() == b'preserve another owner\n'
    assert not (target/rows[0]['integrated']['path']).exists()


def test_copy_is_idempotent_and_fast_check_does_not_claim_raw_recovery(publication):
    manifest, source, target = publication
    first = publisher.publish(manifest, source, target)
    times = {(target/row['integrated']['path']): (target/row['integrated']['path']).stat().st_mtime_ns
             for row in publisher.records(manifest)}
    second = publisher.publish(manifest, source, target)
    assert first == second
    assert first['roots'] == 57
    assert first['raw_case_operator_banks_recovered'] is False
    assert all(path.stat().st_mtime_ns == timestamp for path, timestamp in times.items())
