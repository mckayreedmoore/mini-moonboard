"""Run a climber-weight comparison on the current retained-frame geometry.

Requires the recovered, source-bound owner-bolt-moves-v4 analysis packet.
Reuses its methods and net geometry; never rebuilds CAD or scales old ratios.
"""

from __future__ import annotations

import argparse
import ast
import fcntl
import importlib
import json
import os
import platform
import subprocess
import sys
from pathlib import Path
from unittest.mock import patch

import numpy as np
import scipy

from scripts import eoere_load_parameters as loads
from scripts.eoere_paired_frame_basis import CASES, RAW, ROOT, ref, sha

OWN = Path(__file__).resolve()
WORK = ROOT / RAW / 'frame-completion-v1'
BASE = WORK / 'owner-bolt-moves-v4/analysis'
REFERENCE = ROOT / 'docs/bolted-frame-development/owner-frame-v4/engineering-review.json'
REFERENCE_SHA = 'e0a6a185c417523a6769bc0263d62579ef8b29607c386e475e26d6b7ca14dc8b'
INPUTS = BASE / 'fixed-floor-shared-v1/preparation/inputs.json'
REVIEW_STEPS = ('preflight', 'local', 'group', 'bearing', 'boltgeometry', 'sections', 'rows', 'summary')


def write(path, data):
    with path.open('x') as stream:
        json.dump(data, stream, indent=2, sort_keys=True, allow_nan=False)
        stream.write('\n')


def authenticated(path, expected):
    if sha(path) != expected:
        raise ValueError(f'source changed: {path}')
    return json.loads((ROOT / path).read_bytes())


def baseline():
    """Bind this adapter to the reviewed geometry and exact captured inputs."""
    report = authenticated(REFERENCE, REFERENCE_SHA)
    first = report['scenarios']['four_hosts']['cases'][0]['field']
    field = authenticated(first['path'], first['sha256'])
    binding = field['source_input_review']['input']
    if ROOT / binding['path'] != INPUTS:
        raise ValueError('unexpected reference input bank')
    data = authenticated(INPUTS, binding['sha256'])
    for path, digest in {**report['input_receipts'], **field['source_sha256']}.items():
        if sha(path) != digest:
            raise ValueError(f'recovered source changed: {path}')
    if data != field['source_inputs']:
        # The trial selects its own case from the bank before serializing.
        captured = dict(field['source_inputs'], case=data['case'])
        if data != captured:
            raise ValueError('prepared bank differs from the admitted reference field')
    return data


def prepare(out, parameters):
    if out.exists():
        raise FileExistsError(f'use a fresh output directory: {out}')
    out.relative_to(ROOT / 'fea/generated')
    source = baseline()
    data = loads.parameterize_inputs(source, parameters)
    folder = out / 'preparation'
    folder.mkdir(parents=True)
    # Keep the orchestration source as an immutable run input as well.
    snapshot = folder / 'weight-study-producer.py'
    snapshot.write_bytes(OWN.read_bytes())
    mechanics_source = ROOT / 'scripts/eoere_leg_header_mechanics.py'
    mechanics_snapshot = folder / 'producer-snapshot.py'
    mechanics_snapshot.write_bytes(mechanics_source.read_bytes())
    for path in (snapshot, mechanics_snapshot, Path(loads.__file__), INPUTS):
        data['source_sha256'][ref(path)['path']] = sha(path)
    write(folder / 'inputs.json', data)
    write(out / 'study.json', {
        'schema': 'eoere_climber_weight_study_inputs/v1',
        'parameters': parameters.record(), 'baseline_review': ref(REFERENCE),
        'baseline_inputs': ref(INPUTS), 'inputs': ref(folder / 'inputs.json'),
        'producer_snapshot': ref(snapshot), 'case_ids': list(CASES),
        'geometry': data['geometry'], 'material': data['plywood_material'],
        'geometry_changed': False, 'capacity_criteria_changed': False,
        'structural_acceptance': False, 'climber_rating': False,
    })
    print('Prepared', parameters.record(), flush=True)


def modules(out):
    """Configure existing frozen adapters without changing their source bytes."""
    sys.path.insert(0, str(WORK))
    basis = importlib.import_module('owner_bolt_moves_basis')
    basis.RUN = out
    basis.REVIEW = out / 'review'
    reviews = importlib.import_module('owner_bolt_moves_reviews')
    reviews.OUT = basis.REVIEW / 'complete-v1'
    return basis, reviews


def review(out, kind):
    basis, reviews = modules(out)
    if kind == 'rows':
        folders = [(ROOT / binding['path']).parent for _, _, binding, _ in basis.load()[1]]
        original = Path.glob

        def routed(path, pattern):
            if path == basis.RUN / 'nominal' and pattern == 'three-pin-shift-corner-floor-*-v1':
                return iter(folders)
            return original(path, pattern)

        with patch.object(Path, 'glob', routed):
            for thickness in (38.1, 36.5):
                reviews.plywood(thickness)
        return
    if kind == 'sections':
        # These hole-deducted cores depend on geometry, not climber weight.
        original = BASE / 'review/complete-v1/timber-net-geometry-v1.json'
        core = json.loads(original.read_bytes())
        if core['geometry'] != ref(basis.GEOMETRY) or not core['all_nominal_core_prisms_contained']:
            raise ValueError('net geometry is not applicable to this study')
        for path, digest in core['source_sha256'].items():
            if sha(path) != digest:
                raise ValueError(f'net geometry source changed: {path}')
        reviews.OUT.mkdir(parents=True, exist_ok=True)
        (reviews.OUT / original.name).write_bytes(original.read_bytes())
    reviews.worksheet(kind)


def reducer():
    """Reuse the issued summary arithmetic, without executing its publisher."""
    source = WORK / 'owner_current_engineering_summary.py'
    tree = ast.parse(source.read_bytes())
    names = ('read', 'maximum', 'rows_report', 'scenario')
    nodes = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name in names]
    if len(nodes) != len(names):
        raise ValueError('issued summary interface changed')
    import math

    scope = {'Path': Path, 'ROOT': ROOT, 'json': json, 'math': math, 'numpy': np,
             'ref': ref, 'sha': sha, 'pins': {}, 'authenticated': set()}
    exec(compile(ast.Module(body=nodes, type_ignores=[]), str(source), 'exec'), scope)  # noqa: S102 -- fixed functions from the authenticated issued reducer
    return scope


def compact_comparison(scenario):
    """Human-readable governing comparisons, with the same declared limits."""
    bolts = json.loads((ROOT / scenario['shaft82_geometry_source']['path']).read_bytes())
    timber = json.loads((ROOT / scenario['timber_source']['path']).read_bytes())
    result = []
    for side in ('left', 'right'):
        for component, prefix in (('front post/runner', f'rail_front_bolt_{side}_'),
                                  ('upper long support/side rim', f'lumber_leg_bolt_{side}')):
            rows = [(c, r) for c in bolts['cases'] for r in c['shafts'] if r['axis_id'].startswith(prefix)]
            if not rows:
                raise ValueError(f'missing bolt comparison: {prefix}')
            for label, key in (('wood bearing', 'maximum_bearing_index_before_Cdelta'),
                               ('bolt axial/bending', 'maximum_N_M_index_before_Cdelta')):
                c, r = max(rows, key=lambda pair, k=key: pair[1][k])
                result.append({'component': f'{side} {component}', 'reference': label,
                               'value': r[key], 'case_id': c['case_id'], 'id': r['axis_id']})
    for name in ('base_header', 'base_rail_top', 'base_side_left', 'base_side_right'):
        rows = [(c, r) for c in timber['cases'] for r in c['members'] if r['member'] == name]
        key = 'maximum_shear_torsion_reference_upper'
        c, r = max(rows, key=lambda pair: pair[1][key])
        result.append({'component': name, 'reference': 'net shear/torsion',
                       'value': r[key], 'case_id': c['case_id'], 'id': name})
    for name in ('nominal38p1_rows', 'minimum36p5_rows'):
        rows = scenario[name]
        c = max(rows['cases'], key=lambda r: r['row_reference_index'])
        result.append({'component': 'bonded cleat', 'reference': f"{rows['credited_combined_wall_mm']} mm wall",
                       'value': c['row_reference_index'], 'case_id': c['case_id'], 'id': c['laminate']})
    return result


def summarize(out):
    basis, _ = modules(out)
    scope = reducer()
    scenario = scope['scenario'](basis)
    study = json.loads((out / 'study.json').read_bytes())
    reference = authenticated(REFERENCE, REFERENCE_SHA)['scenarios']['four_hosts']
    result = {
        'schema': 'eoere_climber_weight_study_result/v1', 'study': ref(out / 'study.json'),
        'parameters': study['parameters'], 'baseline_review': ref(REFERENCE),
        'comparison': compact_comparison(scenario), 'baseline_comparison': compact_comparison(reference),
        'scenarios': {'four_hosts': scenario}, 'input_receipts': scope['pins'],
        'versions': {'Python': platform.python_version(), 'NumPy': np.__version__, 'SciPy': scipy.__version__},
        'all_six_independent_replays_admitted': True, 'ratios_scaled_from_reference': False,
        'geometry_changed': False, 'native_executable_solve_performed': False,
        'structural_acceptance': False, 'fabrication_released': False,
        'climbing_released': False, 'climber_rating': False, 'panel_Hillman_resolution_deferred': True,
        'limits': [
            'Only the recorded six single-climber load locations and directions are covered.',
            'Mass, downward multiplier and horizontal force are independent study inputs; no standard load combination is claimed.',
            'Dead loads and the 25 kg accessory allowance stay fixed. NDS duration factor stays CD1.',
            'Four-host centroid XY and compression-only normals remain unverified floor assumptions.',
            'Perfect bonding and the full-width plywood beam approximation remain unqualified physical assumptions.',
            'Only the existing 82 ordinary-bolt and 20 timber references plus cleat rows are recomputed. Ten dedicated joints, complete steel/end/group/seat/washer duties and panel screws retain their open qualifications.',
            'A ratio below 1.0 does not complete or rate the frame.',
        ],
    }
    write(out / 'result.json', result)
    before = {(r['component'], r['reference']): r['value'] for r in result['baseline_comparison']}
    lines = ['component\treference\t250_lb_baseline\tstudy\tcase\texceeds_1']
    for r in result['comparison']:
        lines.append('\t'.join((r['component'], r['reference'],
                                f"{before[r['component'], r['reference']]:.6f}",
                                f"{r['value']:.6f}", r['case_id'], str(r['value'] > 1.))))
    (out / 'comparison.tsv').write_text('\n'.join(lines) + '\n')
    print('\n'.join(lines), flush=True)


def step(out, name):
    study = json.loads((out / 'study.json').read_bytes())
    authenticated(study['inputs']['path'], study['inputs']['sha256'])
    snapshot = study['producer_snapshot']
    if sha(OWN) != snapshot['sha256']:
        raise ValueError('running adapter differs from the prepared producer snapshot')
    if name in CASES:
        basis, _ = modules(out)
        floor = basis.analysis.floor_method()
        floor.OUT = out
        floor.run(name)
    elif name == 'summary':
        summarize(out)
    else:
        review(out, name)


def run(out):
    # Share the existing parent-owned execution lock. Cases run sequentially;
    # each subprocess releases solver state before the next case starts.
    lock_path = ROOT / 'docs/wood-joints-mvp/luna-max-native-run-ledger.lock'
    ledger = lock_path.with_suffix('.json')
    with lock_path.open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        if json.loads(ledger.read_bytes())['slot']['state'] != 'idle':
            raise ValueError('the shared execution slot must be idle')
        env = {**os.environ, 'OPENBLAS_NUM_THREADS': '1', 'OMP_NUM_THREADS': '1'}
        for name in (*CASES, *REVIEW_STEPS):
            print('Running', name, flush=True)
            with (out / (name + '.log')).open('x') as log:
                subprocess.run([sys.executable, '-B', '-m', 'scripts.eoere_weight_study',
                                '--out', str(out), '--_step', name],
                               cwd=ROOT, env=env, stdout=log, stderr=subprocess.STDOUT,
                               check=True, timeout=900)
    print('Result:', out / 'result.json', flush=True)
    print((out / 'comparison.tsv').read_text(), flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    weight = parser.add_mutually_exclusive_group()
    weight.add_argument('--weight-kg', type=float)
    weight.add_argument('--weight-lb', type=float)
    parser.add_argument('--downward-multiplier', type=float, default=2.)
    parser.add_argument('--horizontal-force-n', type=float, default=300.)
    parser.add_argument('--out', type=Path, required=True, help='fresh directory under fea/generated')
    parser.add_argument('--prepare-only', action='store_true', help='validate and capture loads without solving')
    parser.add_argument('--_step', choices=(*CASES, *REVIEW_STEPS), help=argparse.SUPPRESS)
    args = parser.parse_args()
    out = args.out.resolve()
    if args._step:
        step(out, args._step)
        return
    if args.weight_kg is None and args.weight_lb is None:
        parser.error('provide --weight-kg or --weight-lb')
    try:
        parameters = loads.LoadParameters(
            args.weight_kg if args.weight_kg is not None else args.weight_lb,
            'kg' if args.weight_kg is not None else 'lb', args.downward_multiplier,
            args.horizontal_force_n)
        prepare(out, parameters)
        if not args.prepare_only:
            run(out)
    except (ValueError, FileExistsError, FileNotFoundError, BlockingIOError) as error:
        parser.exit(2, f'{error}\n')


if __name__ == '__main__':
    main()
