import copy
import json
from pathlib import Path

import pytest

from scripts import publish_v11_matching_rear_viewer as publisher

ROOT = Path(__file__).resolve().parents[1]
BANK = json.loads((ROOT / publisher.SOURCES['response_bank']['path']).read_bytes())


def test_public_check_never_opens_ignored_sources(monkeypatch):
    real = Path.read_bytes

    def public(path):
        assert path.resolve().is_relative_to(ROOT / 'site') or path.resolve().is_relative_to(ROOT / 'docs'), path
        return real(path)

    monkeypatch.setattr(Path, 'read_bytes', public)
    checked = publisher.check(ROOT)
    assert checked['parts'] == 1099 and checked['stacks'] == 114 and checked['washers'] == 228
    assert checked['new_wood_meshes'] == 4 and checked['translated_hardware_parts'] == 10
    assert checked['ignored_inputs_read'] is False and checked['trial_selected'] is False


@pytest.mark.parametrize('mutation', [
    lambda b: b['physical_geometry'].update(sha256='a' * 64),
    lambda b: b['load_contract'].update(weight_lb=249),
    lambda b: b['cases'].pop(),
    lambda b: b['cases'][0].update(both_independent_replays_admitted=False),
    lambda b: b['cases'][0]['independent_replay'].update(path='historical/replay.json'),
    lambda b: b['cases'][0]['independent_replay'].update(sha256=b['cases'][0]['field']['sha256']),
    lambda b: b.update(historical_field_or_force_transfer=True),
    lambda b: b.update(structural_acceptance=True),
])
def test_stale_or_unadmitted_banks_are_rejected(mutation):
    data = copy.deepcopy(BANK)
    mutation(data)
    with pytest.raises(ValueError):
        publisher.validate_bank(data)


def test_results_are_a_projection_of_the_own_completion_only():
    result = publisher.result_projection(ROOT)
    own = json.loads((ROOT / publisher.SOURCES['reference_completion']['path']).read_bytes())
    for key, row in own['families']['outputs'].items():
        assert result['family_references'][key] == {name: row[name] for name in ('maximum', 'above_one_count')}
    assert result['rear']['maximum_case_reference_bracket'] == own['rear']['maximum_case_reference_bracket']
    assert result['actual_Cg_adopted'] is None and result['actual_Cdelta_adopted'] is None
    assert result['trial_selected'] is False and result['complete_connection_capacity'] is None


def test_late_conflict_prevents_partial_asset_publication(tmp_path, monkeypatch):
    payloads = {name: (ROOT / name).read_bytes() for name in (publisher.SCENE, publisher.RESULTS, publisher.PROVENANCE, publisher.OVERLAY)}
    monkeypatch.setattr(publisher, 'prepare', lambda *_: payloads)
    conflict = tmp_path / publisher.OVERLAY
    conflict.parent.mkdir(parents=True)
    conflict.write_bytes(b'preserve owner bytes\n')
    with pytest.raises(ValueError, match='Preserve existing differing file'):
        publisher.publish(ROOT, tmp_path)
    assert not (tmp_path / publisher.SCENE).exists()
    assert conflict.read_bytes() == b'preserve owner bytes\n'


def test_publication_is_idempotent(tmp_path, monkeypatch):
    payloads = {name: (ROOT / name).read_bytes() for name in (publisher.SCENE, publisher.RESULTS, publisher.PROVENANCE, publisher.OVERLAY)}
    monkeypatch.setattr(publisher, 'prepare', lambda *_: payloads)
    monkeypatch.setattr(publisher, 'check', lambda _: {'status': 'fixture_checked'})
    (tmp_path / 'site').mkdir()
    publisher.publish(ROOT, tmp_path)
    stamps = [(tmp_path / name).stat().st_mtime_ns for name in payloads]
    publisher.publish(ROOT, tmp_path)
    assert stamps == [(tmp_path / name).stat().st_mtime_ns for name in payloads]


def test_missing_target_parent_stops_publication_before_any_asset_write(tmp_path):
    for ref in publisher.SOURCES.values():
        destination = tmp_path / ref['path']
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes((ROOT / ref['path']).read_bytes())
    (tmp_path / 'site').mkdir()
    with pytest.raises(FileNotFoundError):
        publisher.publish(ROOT, tmp_path)
    assert not list((tmp_path / 'site').iterdir())
