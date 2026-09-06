"""Reproduce the bounded observer publication from retained build/cube evidence."""
import hashlib
import json
from pathlib import Path

from fea.mortar_observer_replay import replay

ROOT = Path('fea/mortar_observer_build')
BUILD = ROOT/'build-rvk4q426'
CUBES = ROOT/'cube-qyk279w_'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require_comparison_coverage(runs):
    expected = {(case, binary) for case in ('mortar_0p25', 'mortar_0p125')
                for binary in ('upstream', 'observer')}
    if (len(runs) != len(expected) or
            {(run['case'], run['binary']) for run in runs} != expected or
            any(type(run['exit_code']) is not int or run['exit_code'] != 0 for run in runs)):
        raise ValueError('Exactly four unique successful cube comparisons required')


def main():
    build = json.loads((BUILD/'build_result.json').read_text())
    comparison = json.loads((CUBES/'report.json').read_text())
    if build['exit_code'] or comparison['build_result_sha256'] != sha(BUILD/'build_result.json'):
        raise ValueError('Successful matching build required')
    require_comparison_coverage(comparison['runs'])
    for name, expected in build['evidence_sha256'].items():
        if sha(BUILD/name) != expected:
            raise ValueError('Build evidence changed')
    replay_directory = ROOT/'replay-qyk279w_'
    replay_directory.mkdir(exist_ok=True)
    cases = []
    for run in comparison['runs']:
        directory = CUBES/(run['case']+'-'+run['binary'])
        for name, expected in run['output_sha256'].items():
            if sha(directory/name) != expected:
                raise ValueError('Cube output changed')
        if (any(run['maximum_printed_difference_from_archive'].values()) or
                not run['accepted_history_equal_to_archive'] or
                not all(ep[k] for ep in run['endpoints']
                        for k in ('force_pass', 'moment_pass', 'aggregate_friction_pass'))):
            raise ValueError('Cube output comparison failed')
        if run['binary'] != 'observer':
            continue
        result = replay((directory/'cube.log').read_text(), (directory/'cube.sta').read_text())
        output = replay_directory/(run['case']+'.json')
        output.write_text(json.dumps(result, indent=2, allow_nan=False)+'\n')
        nodes = [n for call in result['calls'] if call['accepted'] for n in call['nodes']]
        eligible = [n for n in nodes if n['eligible']]
        cases.append({
            'case': run['case'], 'replay': str(output), 'replay_sha256': sha(output),
            'calls': len(result['calls']), 'accepted_increments': len(result['accepted_call_ids']),
            'accepted_override_call_ids': result['accepted_override_call_ids'],
            'accepted_node_observations': len(nodes), 'eligible_node_observations': len(eligible),
            'max_abs_normal_residual': max(abs(n['normal_residual']) for n in eligible),
            'max_abs_tangent_residual': max(abs(t) for n in eligible for t in n['tangent_residual']),
            'min_weighted_regularized_opening': min(n['weighted_regularized_opening'] for n in eligible),
            'max_internal_coulomb_excess': max(n['internal_coulomb_excess'] for n in eligible),
        })
    sources = [Path('fea/mortar_observer/patch.py'), Path('fea/mortar_observer_replay.py'),
               Path('fea/mortar_linear_law.py'), *[ROOT/name for name in
               ('Dockerfile', 'record_build.py', 'build.py', 'compare_cube.py', 'publish.py')]]
    evidence = [BUILD/'build_result.json', BUILD/'build_manifest.json', CUBES/'report.json']
    report = {
        'status': 'BOUNDED CUBE OBSERVER REPLAY; NO REDESIGNED FRAME RESULT OR PHYSICAL APPROVAL',
        'qualification': 'Printed U/RF and accepted histories match the unmodified upstream solver and archive. Complete internal multiplier transforms and residual arithmetic replay on two cubes. Independent gap/displacement kinematics, segmentation, coupling-force balance and physical floor/joint properties remain unqualified.',
        'observer_image_id': build['image_id'], 'parent_image_id': build['parent_image_id'],
        'build_directory': str(BUILD), 'cube_directory': str(CUBES),
        'sources_sha256': {str(p): sha(p) for p in sources},
        'evidence_sha256': {str(p): sha(p) for p in evidence}, 'cases': cases,
    }
    (ROOT/'report.json').write_text(json.dumps(report, indent=2, allow_nan=False)+'\n')
    print(json.dumps({'report': str(ROOT/'report.json'), 'cases': cases}), flush=True)


if __name__ == '__main__':
    main()
