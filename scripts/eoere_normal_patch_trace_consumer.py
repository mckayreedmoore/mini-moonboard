"""Opening-coordinate adapter for the preserved saved-pose contact trace."""
from __future__ import annotations

import argparse
import ast
import hashlib
import json
from functools import cache
from pathlib import Path
from types import ModuleType

ROOT = Path(__file__).resolve().parents[1]
OWN = Path(__file__).resolve()
LOADED_SHA = hashlib.sha256(OWN.read_bytes()).hexdigest()
V1_PATH = 'scripts/eoere_normal_patch_trace.py'
V1_SHA = 'e7e0deb227258a53e35e0260db2445880af642313b50b72c9c98233c3f19a813'
STORED_EXPRESSION = 'sum((F(float(v))*q[int(i)] for v, i in zip(coefficients, columns, strict=True)), F(0))'
CONVENTION = 'Source Bq is positive compression; the geometric gap is positive opening, so g = -Bq.'


def captured(reference):
    path = (ROOT/reference['path']).resolve()
    if not path.is_relative_to(ROOT):
        raise ValueError('repository source required')
    data = path.read_bytes()
    if hashlib.sha256(data).hexdigest() != reference['sha256']:
        raise ValueError('source buffer changed: '+reference['path'])
    return data


def opening_tree(data):
    """Negate only the unique, exact preserved sparse-row assignment."""
    tree = ast.parse(data, filename=V1_PATH)
    runs = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'run']
    if len(runs) != 1:
        raise ValueError('one preserved run definition required')
    assignments = [n for n in ast.walk(runs[0]) if isinstance(n, ast.Assign)
                   and any(isinstance(t, ast.Name) and t.id == 'stored' for t in n.targets)]
    expected = ast.parse(STORED_EXPRESSION, mode='eval').body
    if (len(assignments) != 1 or len(assignments[0].targets) != 1
            or ast.dump(assignments[0].value) != ast.dump(expected)):
        raise ValueError('one exact preserved sparse-row assignment required')
    assignment = assignments[0]
    assignment.value = ast.copy_location(ast.UnaryOp(op=ast.USub(), operand=assignment.value), assignment.value)
    return ast.fix_missing_locations(tree)


@cache
def _producer():
    data = captured({'path': V1_PATH, 'sha256': V1_SHA})
    module = ModuleType('_eoere_verified_opening_trace_v1')
    module.__file__ = str(ROOT/V1_PATH)
    exec(compile(opening_tree(data), module.__file__, 'exec'), module.__dict__)  # noqa: S102 - one verified AST delta
    if module.LOADED_SHA != V1_SHA:
        raise ValueError('preserved producer identity changed')
    return module


def run(reference):
    inputs = json.loads(captured(reference))
    own = {'path': str(OWN.relative_to(ROOT)), 'sha256': LOADED_SHA}
    refs = inputs['execution_sources']
    if (inputs['execution_adapter_schema'] != 'eoere_current_normal_patch_trace_adapter/v2'
            or own not in refs or {'path': V1_PATH, 'sha256': V1_SHA} not in refs
            or inputs['source_coordinate_convention'] != CONVENTION):
        raise ValueError('exact adapter, producer and source coordinates required')
    for ref in (*refs, inputs['preserved_v1_inputs'], inputs['stopped_v1_execution']):
        captured(ref)
    result = _producer().run(reference)
    for row in result['records']:
        for centroid in row['source_centroids']:
            opening = centroid.pop('exact_stored_Bq_mm')
            centroid['exact_negative_stored_compression_Bq_mm'] = opening
            centroid['exact_original_stored_compression_Bq_mm'] = str(-_producer().F(opening))
    for ref in (*refs, inputs['preserved_v1_inputs'], inputs['stopped_v1_execution']):
        captured(ref)
        result['source_sha256'][ref['path']] = ref['sha256']
    if hashlib.sha256(OWN.read_bytes()).hexdigest() != LOADED_SHA:
        raise ValueError('executing adapter changed')
    result.update(schema='eoere_current_normal_patch_trace/v2', execution_driver=own,
                  source_coordinate_convention=CONVENTION,
                  captured_AST_delta='Only stored = sum(...) becomes stored = -sum(...) in the preserved run definition.',
                  preserved_v1_inputs=inputs['preserved_v1_inputs'], stopped_v1_execution=inputs['stopped_v1_execution'])
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--inputs', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    if args.out.exists():
        raise FileExistsError('preserve issued saved-pose trace evidence')
    reference = {'path': str(args.inputs.resolve().relative_to(ROOT)),
                 'sha256': hashlib.sha256(args.inputs.read_bytes()).hexdigest()}
    result = run(reference)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open('x') as stream:
        stream.write(json.dumps(result, indent=2, sort_keys=True, allow_nan=False)+'\n')
    print(json.dumps({'path': str(args.out), 'bytes': args.out.stat().st_size,
                      'sha256': hashlib.sha256(args.out.read_bytes()).hexdigest(),
                      'patch_states': len(result['records'])}))


if __name__ == '__main__':
    main()
