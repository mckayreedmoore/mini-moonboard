import copy
import json
from pathlib import Path

import pytest

from scripts import publish_v11_results_v2 as publisher

ROOT = Path(__file__).resolve().parents[1]


def test_method_update_check_reads_only_public_files(monkeypatch):
    real = Path.read_bytes

    def public(path):
        assert path.resolve().is_relative_to(ROOT / 'site') or path.resolve().is_relative_to(ROOT / 'docs'), path
        return real(path)

    monkeypatch.setattr(Path, 'read_bytes', public)
    assert publisher.check(ROOT)['ignored_inputs_read'] is False


@pytest.mark.parametrize('change', ['old_bank', 'duplicated_cases', 'adoptedCg', 'mixed_capacity'])
def test_method_update_rejects_wrong_joins_and_acceptance(monkeypatch, change):
    standard = json.loads((ROOT / publisher.STANDARD['path']).read_bytes())
    criterion = json.loads((ROOT / publisher.CRITERION['path']).read_bytes())
    standard, criterion = copy.deepcopy(standard), copy.deepcopy(criterion)
    if change == 'old_bank':
        standard['source_bindings']['response_bank']['sha256'] = '0' * 64
    elif change == 'duplicated_cases':
        standard['source_bindings']['six_cases'][1] = standard['source_bindings']['six_cases'][0]
    elif change == 'adoptedCg':
        standard['qualifications']['actual_Cg'] = 1
    else:
        criterion['mixed_planes']['qualification']['complete_group_capacity'] = 1000
    real = publisher.bound

    def changed(root, ref):
        if ref == publisher.STANDARD:
            return publisher.encode(standard)
        if ref == publisher.CRITERION:
            return publisher.encode(criterion)
        return real(root, ref)

    monkeypatch.setattr(publisher, 'bound', changed)
    with pytest.raises(ValueError):
        publisher.prepare(ROOT)
