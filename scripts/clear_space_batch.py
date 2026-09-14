"""Run a finite case set serially, stopping at the first numerical/design failure."""
import argparse
import importlib
import json
import subprocess
import sys
from pathlib import Path

from fea.current_response_run import run
from scripts.clear_space_results import PREFIXES, checks
from scripts.clear_space_study import MODELS, geometry
from scripts.compact_rail_study import bolt_properties

CASES = {
    'a12-rear': ('A12', (0., 300.)),
    'a12-forward': ('A12', (0., -300.)),
    'a12-left': ('A12', (-300., 0.)),
    'k12-right': ('K12', (300., 0.)),
    'k12-rear': ('K12', (0., 300.)),
    'a1-rear': ('A1', (0., 300.)),
}


def archive(native, geometry_path, output, model):
    subprocess.run([sys.executable, '-m', 'scripts.compact_two_results',
        '--native', str(native), '--geometry', str(geometry_path), '--output', str(output),
        '--expected-candidate', model.KEY, '--model-source', str(Path(model.__file__).resolve().relative_to(Path.cwd())),
        '--bolt-prefix', *PREFIXES], check=True, stdout=subprocess.DEVNULL)
    report = json.loads((native/'report.json').read_text())
    result = checks(report, json.loads(geometry_path.read_text()))
    (output/'assessment.json').write_text(json.dumps(result, indent=2, allow_nan=False)+'\n')
    print(json.dumps({'case':output.name, 'status':result['status'], 'metrics':result.get('metrics'),
        'failed':[key for key, passed in result.get('criteria', {}).items() if not passed]}), flush=True)
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('candidate', choices=MODELS)
    parser.add_argument('--cases', nargs='+', choices=CASES, default=list(CASES))
    parser.add_argument('--native-prefix', required=True)
    parser.add_argument('--archive-root', type=Path, required=True)
    parser.add_argument('--geometry', type=Path, required=True)
    parser.add_argument('--existing-first', type=Path)
    parser.add_argument('--floor-grid', nargs=2, type=int)
    parser.add_argument('--contact-update-strategy', choices=('all', 'one_per_floor_body'), default='all')
    args = parser.parse_args()
    model = importlib.import_module('mini_moonboard.'+MODELS[args.candidate])
    if args.floor_grid:
        if not args.candidate.startswith('floor'):
            parser.error('--floor-grid requires floor candidate')
        model.FLOOR_RAIL_GRID = tuple(args.floor_grid)
    print('Building actual receiver geometry', flush=True)
    actual = geometry(model)
    args.geometry.write_text(json.dumps(actual, indent=2, allow_nan=False)+'\n')
    if not actual['receiver_fit_pass']:
        raise SystemExit('Actual receiver geometry fails')
    bolts = {c.name:bolt_properties(c) for c in model.connections() if c.kind == 'bolt'}
    contacts = [{**row, 'stiffness_n_per_mm':100.*row['tributary_area_mm2']}
                for row in model.overlap_contact_datums()]
    seed = None
    for index, case in enumerate(args.cases):
        native = args.existing_first if index == 0 and args.existing_first else Path(args.native_prefix+'-'+case)
        if not (index == 0 and args.existing_first):
            hold, force = CASES[case]
            options = {'initial_contact_names':seed} if seed is not None else {}
            report = run(native, module=model, expected_candidate=model.KEY,
                bolt_stiffness={**next(iter(bolts.values())), 'by_name':bolts},
                member_contacts=contacts, hold=hold, pounds=250., horizontal_force=force,
                leg_floor_grid=3, patch_size=20.,
                contact_update_strategy=args.contact_update_strategy, **options)
        else:
            report = json.loads((native/'report.json').read_text())
        if not report.get('numerically_accepted'):
            raise SystemExit('Numerical response rejected: '+case)
        result = archive(native, args.geometry, args.archive_root/case, model)
        if not result.get('criteria') or not all(result['criteria'].values()):
            raise SystemExit('Design check failed: '+case)
        seed = [row['name'] for row in report['bearings'] if row['active']]
