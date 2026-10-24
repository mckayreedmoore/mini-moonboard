import copy
import json
from pathlib import Path

import pytest

from scripts import publish_packer_free_results as publisher

ROOT = Path(__file__).resolve().parents[1]


def test_publication_check_never_opens_ignored_fields_or_replays(monkeypatch):
    real = publisher.bound

    def tracked_only(root, ref):
        assert ref['path'].startswith(('docs/', 'site/'))
        return real(root, ref)

    monkeypatch.setattr(publisher, 'bound', tracked_only)
    result = publisher.check(ROOT)
    assert result['cases'] == 6
    assert result['independent_replays'] == 12
    assert result['asset_bytes'] == 7551
    assert result['ignored_inputs_read'] is False


@pytest.mark.parametrize('change', ['old_receipt', 'changed_load', 'replay_failure', 'missing_diagnostic', 'adopted_Cg'])
def test_source_counterexamples_cannot_produce_an_own_results_label(monkeypatch, change):
    records = {name: json.loads(publisher.bound(ROOT, ref)) for name, ref in publisher.SOURCES.items()}
    bank, evaluation = records['response_bank'], records['evaluation']
    if change == 'old_receipt':
        bank['physical_geometry']['sha256'] = 'd9df40fe76e08f008391cb276b8c2136abae09820273b541d10d49b5648d9ef2'
    elif change == 'changed_load':
        bank['load_contract']['horizontal_force_N'] = 250
        evaluation['load_contract']['horizontal_force_N'] = 250
    elif change == 'replay_failure':
        bank['cases'][0]['both_independent_replays_admitted'] = False
    elif change == 'missing_diagnostic':
        evaluation['bearing_diagnostic_rows'].pop()
    else:
        evaluation['actual_Cg_adopted'] = .5
    real = publisher.bound

    def in_memory(root, ref):
        for name, source in publisher.SOURCES.items():
            if ref == source:
                return publisher.encode(records[name])
        return real(root, ref)

    monkeypatch.setattr(publisher, 'bound', in_memory)
    with pytest.raises(ValueError):
        publisher.prepare(ROOT)


def test_result_publication_preserves_conflicts_and_repeated_identical_bytes(tmp_path, monkeypatch):
    record = copy.deepcopy(publisher.prepare(ROOT))
    monkeypatch.setattr(publisher, 'prepare', lambda _: record)
    target = tmp_path / publisher.ASSET
    target.parent.mkdir(parents=True)
    target.write_bytes(b'preserved owner record\n')
    with pytest.raises(ValueError, match='Preserve existing differing file'):
        publisher.publish(tmp_path)
    assert target.read_bytes() == b'preserved owner record\n'
    target.unlink()
    publisher.publish(tmp_path)
    stamp = target.stat().st_mtime_ns
    publisher.publish(tmp_path)
    assert target.stat().st_mtime_ns == stamp
    assert target.read_bytes() == (ROOT / publisher.ASSET).read_bytes()
