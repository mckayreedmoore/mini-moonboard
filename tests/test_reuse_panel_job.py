"""A changed input or raw output cannot masquerade as an identical solver job."""
import hashlib
import json

import pytest

from fea import reuse_panel_job as reuse


def source_job(tmp_path):
    source = tmp_path/'source'
    source.mkdir()
    record = reuse.shell.benchmark(size=100)
    (source/'input.json').write_bytes(reuse.canonical_input(record))
    (source/'panel.inp').write_text(reuse.shell.deck(record))
    (source/'panel.dat').write_text('synthetic raw output for replay orchestration test\n')
    (source/'panel.log').write_text('synthetic successful log\n')
    hashes = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in source.iterdir()}
    (source/'result.json').write_text(json.dumps({'evidence_sha256': hashes}))
    return record, source


def test_identical_job_copies_verified_raw_and_runs_current_assessor(tmp_path):
    record, source = source_job(tmp_path)
    calls = []
    def assess(current, data):
        calls.append((current, data))
        return {'current_assessor_result': True, 'qualified_for_design': False}
    result, provenance = reuse.reuse(record, source, tmp_path/'replay', assess)
    assert len(calls) == 1 and calls[0][0] is record
    assert result['current_assessor_result']
    assert not provenance['fresh_solver_run']
    for name, sha in result['evidence_sha256'].items():
        assert reuse.digest(tmp_path/'replay'/name) == sha
    assert provenance['source_dat_sha256'] == reuse.digest(source/'panel.dat')


def test_changed_current_input_is_rejected_even_when_deck_is_unchanged(tmp_path):
    record, source = source_job(tmp_path)
    record['extra_metadata'] = 'changed'
    with pytest.raises(ValueError, match='canonical input differs'):
        reuse.reuse(record, source, tmp_path/'replay', lambda *_: {})
    assert not (tmp_path/'replay').exists()


@pytest.mark.parametrize('name', ['panel.dat', 'panel.log', 'panel.inp', 'input.json'])
def test_modified_raw_artifact_is_rejected_before_assessment(tmp_path, name):
    record, source = source_job(tmp_path)
    (source/name).write_text('modified')
    with pytest.raises(ValueError, match='hash differs'):
        reuse.reuse(record, source, tmp_path/'replay', lambda *_: pytest.fail('must not assess'))
    assert not (tmp_path/'replay').exists()
