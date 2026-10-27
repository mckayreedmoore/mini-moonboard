import copy
import json
from pathlib import Path

import pytest

from scripts import publish_v11_shorter_bolts_results as publisher

ROOT = Path(__file__).resolve().parents[1]
BANK = json.loads((ROOT / publisher.SOURCES['response_bank']['path']).read_bytes())


def test_check_uses_only_public_inputs_and_exact_source_projection(monkeypatch):
    real = Path.read_bytes

    def public(path):
        assert path.resolve().is_relative_to(ROOT / 'site') or path.resolve().is_relative_to(ROOT / 'docs'), path
        return real(path)

    monkeypatch.setattr(Path, 'read_bytes', public)
    result = publisher.check(ROOT)
    assert result['cases'] == 6 and result['independent_replays'] == 12
    assert result['reference_flag_families'] == 7 and result['separate_diagnostic_scenario_rows'] == 110
    assert result['ignored_inputs_read'] is False and result['structural_acceptance'] is False
    data = json.loads((ROOT / publisher.ASSET).read_bytes())
    review = json.loads((ROOT / publisher.SOURCES['reference_review']['path']).read_bytes())
    assert data['viewer_presentation'] == review['viewer_presentation']
    assert data['member_vector_maxima'] == review['member_vector_maxima']
    assert data['family_maxima'] == review['family_maxima']


@pytest.mark.parametrize('mutation', [
    lambda b: b['physical_geometry'].update(sha256='b' * 64),
    lambda b: b['load_contract'].update(downward_multiplier=1),
    lambda b: b['cases'].pop(),
    lambda b: b['cases'].__setitem__(1, copy.deepcopy(b['cases'][0])),
    lambda b: b['cases'][0].update(both_independent_replays_admitted=False),
    lambda b: b['cases'][0]['independent_plywood_replay'].update(path='historical/replay.json'),
    lambda b: b['cases'][0]['independent_replay'].update(sha256=b['cases'][0]['field']['sha256']),
    lambda b: b['cases'][0].update(gradient_inf_N=float('nan')),
    lambda b: b.update(maximum_gradient_inf_N=0),
    lambda b: b.update(historical_force_or_field_transfer=True),
    lambda b: b.update(structural_acceptance=True),
])
def test_partial_stale_or_unqualified_banks_are_rejected(mutation):
    data = copy.deepcopy(BANK)
    mutation(data)
    with pytest.raises(ValueError):
        publisher.validate_bank(data)


def test_changed_public_source_bytes_are_rejected(monkeypatch):
    real = Path.read_bytes

    def tampered(path):
        raw = real(path)
        return raw + b' ' if path == ROOT / publisher.SOURCES['reference_review']['path'] else raw

    monkeypatch.setattr(Path, 'read_bytes', tampered)
    with pytest.raises(ValueError, match='Source bytes differ'):
        publisher.prepare(ROOT)


def test_publishing_preserves_existing_bytes_and_is_idempotent(tmp_path, monkeypatch):
    data = publisher.prepare(ROOT)
    monkeypatch.setattr(publisher, 'prepare', lambda _: data)
    monkeypatch.setattr(publisher, 'check', lambda _: {'status': 'checked_fixture'})
    destination = tmp_path / publisher.ASSET
    destination.parent.mkdir(parents=True)
    publisher.publish(tmp_path)
    stamp = destination.stat().st_mtime_ns
    publisher.publish(tmp_path)
    assert destination.stat().st_mtime_ns == stamp
    destination.write_bytes(b'preserve owner bytes\n')
    with pytest.raises(ValueError, match='Preserve existing differing file'):
        publisher.publish(tmp_path)
    assert destination.read_bytes() == b'preserve owner bytes\n'
