"""Prepare a bounded numerical seed from four unchanged-contact native iterates.

No result is accepted or rewritten. Run a fresh native solve with the seed;
normal complementarity, friction law and equilibrium gates still apply.
"""
import argparse
import hashlib
import json
import math
from itertools import pairwise
from pathlib import Path


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def build(directory):
    cycles = sorted((p for p in directory.glob('cycle-*')
                     if (p/'report.json').is_file() and (p/'input.json').is_file()),
                    key=lambda p:int(p.name.split('-')[1]))[-4:]
    if len(cycles) != 4:
        raise ValueError('Need four completed native cycles')
    reports = [json.loads((p/'report.json').read_text()) for p in cycles]
    inputs = [json.loads((p/'input.json').read_text()) for p in cycles]
    if not all(r.get('closed_bearing_assumption_passed') is True
               and r.get('global_equilibrium_passed') is True
               and r.get('member_equilibrium_passed') is True
               and r.get('mpc_check_passed') is True for r in reports):
        raise ValueError('All four iterates require strict normal/equilibrium/interpolation gates')
    active = [{row['name'] for row in r['bearings'] if row['active']} for r in reports]
    if any(a != active[0] for a in active[1:]):
        raise ValueError('Normal contact classification changed in last four cycles')
    cells = inputs[-1]['floor_tangent_cells']
    elastic = {n:c['elastic_tangent_n_per_mm'] for n,c in cells.items()}
    feet = [r['floor_friction_law']['feet'] for r in reports]
    mu = reports[-1]['floor_friction_law']['mu_assumed']
    if any(set(f) != set(elastic) for f in feet):
        raise ValueError('Friction cell inventory differs')
    if any(r['floor_friction_law']['mu_assumed'] != mu for r in reports):
        raise ValueError('Physical friction coefficient changed')
    candidate = inputs[-1]['candidate']
    for record in inputs:
        if (record['candidate'] != candidate or record['floor_tangent_cells'] != cells
                or record['force_xyz_n'] != inputs[-1]['force_xyz_n']
                or record['loads'] != inputs[-1]['loads']):
            raise ValueError('Native physical geometry/cell/load metadata changed')
    states = [{n:r[n]['state'] for n in elastic} for r in feet]
    if any(s != states[0] for s in states[1:]):
        raise ValueError('Friction stick/slip/open classification changed')
    seed, details = {}, {}
    for name, upper in elastic.items():
        values = [r[name]['next_secant_n_per_mm'] for r in feet]
        if not math.isfinite(upper) or upper <= 0 or not all(math.isfinite(v) and 0 <= v <= upper for v in values):
            raise ValueError('Nonfinite or out-of-range elastic/target secants')
        seed[name] = values[-1]
        increments = [b-a for a,b in pairwise(values)]
        detail = {'target_secants_n_per_mm':values, 'increments_n_per_mm':increments,
                  'elastic_bound_n_per_mm':upper, 'extrapolated':False}
        details[name] = detail
        if states[-1][name] != 'slip':
            detail['reason'] = 'Retain open/stick target'
            continue
        if (min(abs(v) for v in increments) < 1.e-5*max(1.,abs(values[-1]))
                or not all(v*increments[0] > 0 for v in increments)):
            detail['reason'] = 'Small or nonmonotone increments'
            continue
        rates = [increments[1]/increments[0],increments[2]/increments[1]]
        detail['contraction_rates'] = rates
        if not all(0 < v < .98 for v in rates) or abs(rates[0]-rates[1]) > .03:
            detail['reason'] = 'Contraction not sufficiently consistent'
            continue
        trial = values[-1]+increments[-1]*rates[-1]/(1.-rates[-1])
        detail['unclipped_aitken_secant_n_per_mm'] = trial
        if not 0 <= trial <= upper or abs(trial-values[-1]) > .5*max(1.,values[-1]):
            detail['reason'] = 'Extrapolation outside physical or bounded search step'
            continue
        seed[name] = trial
        detail.update(extrapolated=True,reason='Consistent bounded monotone contraction')
    hashes = {str(p/name):digest(p/name) for p in cycles for name in ('report.json','input.json')}
    hashes[str(Path(__file__).resolve())] = digest(__file__)
    return {'candidate':candidate,'mu_assumed':mu,'source_cycles':[str(p) for p in cycles],
        'source_sha256':hashes,'initial_contact_names':sorted(active[-1]),
        'initial_tangent_secants':seed,'cell_details':details,'cell_count':len(seed),
        'extrapolated_count':sum(d['extrapolated'] for d in details.values()),
        'guards':{'cycle_count':4,'normal_and_friction_classifications_identical':True,
            'maximum_contraction_rate':.98,'maximum_rate_change':.03,
            'minimum_increment_relative_to_max_one_current':1.e-5,
            'maximum_step_relative_to_max_one_current':.5},
        'scope':'Numerical search initialization only. No native or resistance acceptance; fresh strict native verification mandatory.'}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('native_folder',type=Path)
    parser.add_argument('output_json',type=Path)
    args = parser.parse_args()
    if args.output_json.exists():
        raise FileExistsError('Refusing to overwrite prior seed provenance')
    result = build(args.native_folder.resolve())
    args.output_json.write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
    print(json.dumps({k:result[k] for k in ('candidate','source_cycles','cell_count','extrapolated_count')}))
