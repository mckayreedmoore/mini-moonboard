"""Read-only independent review probes; run against a separate attempt10 replay."""
from __future__ import annotations

import copy
import importlib.util
import itertools
import json
from pathlib import Path
import sys

replay = Path(sys.argv[1]).resolve()
sys.path.insert(0, str(replay))
from mini_moonboard import nds_2024_group_action as method

assert Path(method.__file__).resolve() == replay / 'mini_moonboard/nds_2024_group_action.py'
spec = importlib.util.spec_from_file_location('review_fixtures', replay / 'tests/test_nds_2024_group_action.py')
fixtures = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fixtures)
checks = []

def compare(left, right, paths, *, root_keys=False):
    baseline = fixtures.payload(count=3)
    variant = fixtures.payload(count=3)
    variant['scenario_id'] = 'sensitivity'
    variant['source_bindings'] = fixtures.bindings('sensitivity')
    if root_keys:
        baseline.update(left)
        variant.update(right)
    else:
        baseline['producer_extension'] = left
        variant['producer_extension'] = right
    contract = {
        'contract_id': 'independent-attempt10-review',
        'source_id': 'synthetic-only/independent-attempt10-review',
        'sha256': 'pending-digest',
        'review_status': 'coordinator_reviewed',
        'classification': 'composite_scenario',
        'candidate_id': 'synthetic-only',
        'revision_id': 'fixture-v1',
        'group_id': 'group-01',
        'baseline_scenario_id': 'baseline',
        'sensitivity_scenario_id': 'sensitivity',
        'changed_input_paths': paths,
    }
    binding = fixtures.bind_sensitivity_contract(contract)
    return method.evaluate_group_factor_sensitivity(
        baseline, variant,
        baseline_expected_bindings=fixtures.bindings(),
        baseline_expected_payload_sha256=method.canonical_group_record_sha256(baseline),
        sensitivity_expected_bindings=fixtures.bindings('sensitivity'),
        sensitivity_expected_payload_sha256=method.canonical_group_record_sha256(variant),
        expected_sensitivity_contract=contract,
        expected_sensitivity_binding=binding,
    )

def exercise(label, left, right, expected, *, root_keys=False):
    result = compare(left, right, list(reversed(expected)), root_keys=root_keys)
    assert result['status'] == 'calculated_method_sensitivity_only', (label, result)
    assert result['changed_input_paths'] == sorted(expected), (label, result)
    assert result['capacity'] is None and result['criterion_disposition'] == 'pending'
    # Reject each omitted location independently, even when paths share punctuation.
    for path in expected:
        omitted = [item for item in expected if item != path]
        if not omitted:
            omitted = ['deliberately.wrong.path']
        pending = compare(left, right, omitted, root_keys=root_keys)
        assert pending['status'] == 'pending', (label, path, pending)
        assert pending['capacity'] is None and pending['criterion_disposition'] == 'pending'
    checks.append({'label': label, 'expected_paths': sorted(expected), 'omission_rejections': len(expected)})

exercise('multi-digit list growth', list(range(10)), list(range(13)), ['producer_extension.length', *[f'producer_extension[{i}]' for i in range(10, 13)]])
exercise('multi-digit list shrink', list(range(13)), list(range(10)), ['producer_extension.length', *[f'producer_extension[{i}]' for i in range(10, 13)]])
exercise('empty list growth uses whole items', [], [{'a.b': [1, 2]}, []], ['producer_extension.length', 'producer_extension[0]', 'producer_extension[1]'])
exercise('empty list shrink uses whole items', [{'a.b': [1, 2]}, []], [], ['producer_extension.length', 'producer_extension[0]', 'producer_extension[1]'])
exercise('middle removal uses positional differences', ['a', 'b', 'c'], ['a', 'c'], ['producer_extension.length', 'producer_extension[1]', 'producer_extension[2]'])
exercise('middle insertion uses positional differences', ['a', 'c'], ['a', 'b', 'c'], ['producer_extension.length', 'producer_extension[1]', 'producer_extension[2]'])

cases = [
    ('a.b', r'a\.b'), ('a[0]', r'a\[0\]'), ('a\\b', r'a\\b'),
    ('', r'\e'), (r'\e', r'\\e'), (' ', r'\u0020'),
    (r'\u0020', r'\\u0020'), ('\t\n\u3000', r'\u0009\u000a\u3000'),
    (r'\u0009\u000a\u3000', r'\\u0009\\u000a\\u3000'),
    ('scenario_id', 'scenario_id'), ('source_bindings', 'source_bindings'),
    ('a\\.[]', r'a\\\.\[\]'),
]
left = {key: 0 for key, _ in cases}
right = {key: 1 for key, _ in cases}
left['a'] = {'b': 0}
right['a'] = {'b': 1}
left['x'] = [0]
right['x'] = [1]
left['x[0]'] = 0
right['x[0]'] = 1
exercise('simultaneous escaped and structural paths stay distinct', left, right, [*[f'producer_extension.{encoded}' for _, encoded in cases], 'producer_extension.a.b', 'producer_extension.x[0]', r'producer_extension.x\[0\]'])
exercise('empty root key does not suppress nested identity paths', {'': {'scenario_id': 1, 'source_bindings': 1}}, {'': {'scenario_id': 2, 'source_bindings': 2}}, [r'\e.scenario_id', r'\e.source_bindings'], root_keys=True)
exercise('root empty and whitespace keys differ from literal escapes', {key: 0 for key, _ in cases[:9]}, {key: 1 for key, _ in cases[:9]}, [encoded for _, encoded in cases[:9]], root_keys=True)
exercise('boolean and numeric and signed zero differences', {'a': True, 'b': 1, 'c': -0.0}, {'a': 1, 'b': 1.0, 'c': 0.0}, ['producer_extension.a', 'producer_extension.b', 'producer_extension.c'])

for label, invalid in [('tuple', (1, 2)), ('non-string key', {1: 'one'}), ('nan', float('nan')), ('infinity', float('inf'))]:
    result = compare(1, invalid, ['producer_extension'])
    assert result['status'] == 'pending', (label, result)
    assert result['capacity'] is None and result['criterion_disposition'] == 'pending'
    checks.append({'label': f'strict JSON rejects {label}', 'reason_codes': result['reason_codes'], 'missing_inputs': result['missing_inputs']})

alphabet = ('a', '.', '[', ']', '\\', 'e', 'u', '0', ' ', '\t', '\u3000')
encoded_to_key = {}
for length in range(4):
    for chars in itertools.product(alphabet, repeat=length):
        key = ''.join(chars)
        encoded = method._changed_payload_paths({key: 0}, {key: 1})[0]
        assert encoded.strip(), repr(key)
        assert encoded not in encoded_to_key or encoded_to_key[encoded] == key, (repr(key), repr(encoded_to_key[encoded]), repr(encoded))
        encoded_to_key[encoded] = key
checks.append({'label': 'generated key encoding injectivity and nonblank output', 'distinct_keys': len(encoded_to_key), 'max_key_length': 3, 'alphabet': alphabet})
print(json.dumps({'all_passed': True, 'loaded_method_path': str(Path(method.__file__).resolve()), 'checks': checks}, indent=2))
