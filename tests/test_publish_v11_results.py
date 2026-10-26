import copy
import json
from pathlib import Path

import pytest

from scripts import publish_v11_results as publisher

ROOT = Path(__file__).resolve().parents[1]


def test_check_reads_only_public_assets_and_records(monkeypatch):
    original = Path.read_bytes

    def public_only(path):
        resolved = path.resolve()
        assert resolved.is_relative_to(ROOT / 'site') or resolved.is_relative_to(ROOT / 'docs'), path
        return original(path)

    monkeypatch.setattr(Path, 'read_bytes', public_only)
    result = publisher.check(ROOT)
    assert result['cases'] == 6 and result['independent_replays'] == 12
    assert result['mapped_axes'] == 88 and result['unsupported_mixed_axes'] == 24
    assert result['inconclusive_row_bounds'] == 21 and result['ignored_inputs_read'] is False


@pytest.mark.parametrize('change', ['old_bank', 'changed_load', 'duplicate_fields', 'foreign_review_field',
                                   'actual_property_adoption', 'lost_mixed_axis', 'lost_row_flag', 'adopted_group_capacity'])
def test_public_projection_rejects_foreign_joins_and_qualification_changes(monkeypatch, change):
    records = {name: json.loads((ROOT / ref['path']).read_bytes()) for name, ref in publisher.SOURCES.items()}
    records = copy.deepcopy(records)
    if change == 'old_bank':
        records['property_comparison']['source_bindings']['response_bank']['sha256'] = '0' * 64
    elif change == 'changed_load':
        records['response_bank']['load_contract']['weight_lb'] = 300
    elif change == 'duplicate_fields':
        records['response_bank']['cases'][1]['field']['sha256'] = records['response_bank']['cases'][0]['field']['sha256']
    elif change == 'foreign_review_field':
        records['reference_review']['fields']['a12-forward']['sha256'] = '0' * 64
    elif change == 'actual_property_adoption':
        records['property_comparison']['property_specification']['automatic_actual_property_adoption'] = True
    elif change == 'lost_mixed_axis':
        records['property_comparison']['unsupported_mixed_axes'].pop()
    elif change == 'lost_row_flag':
        records['row_comparison']['explicit92_inconclusive_flags'].pop()
    else:
        records['row_comparison']['qualifications']['complete_group_pass'] = True
    original = publisher.bound

    def changed_source(root, ref):
        for name, expected in publisher.SOURCES.items():
            if ref == expected:
                return publisher.encode(records[name])
        return original(root, ref)

    monkeypatch.setattr(publisher, 'bound', changed_source)
    with pytest.raises(ValueError):
        publisher.prepare(ROOT)


def test_publication_is_idempotent_and_preserves_an_existing_different_file(tmp_path, monkeypatch):
    current = json.loads((ROOT / publisher.ASSET).read_bytes())
    monkeypatch.setattr(publisher, 'prepare', lambda _: current)
    target = tmp_path / publisher.ASSET
    target.parent.mkdir(parents=True)
    publisher.publish(tmp_path)
    stamp = target.stat().st_mtime_ns
    publisher.publish(tmp_path)
    assert target.stat().st_mtime_ns == stamp
    target.write_bytes(b'preserved owner bytes\n')
    with pytest.raises(ValueError, match='Preserve existing differing file'):
        publisher.publish(tmp_path)
    assert target.read_bytes() == b'preserved owner bytes\n'
