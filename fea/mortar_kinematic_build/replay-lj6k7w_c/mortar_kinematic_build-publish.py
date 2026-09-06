"""Bind the new build, four unchanged cube comparisons and v2 replay evidence."""
import argparse
import json
import tempfile
from pathlib import Path

from fea.mortar_kinematic_build.record_build import sha
from fea.mortar_observer_build.publish import require_comparison_coverage

ROOT = Path(__file__).parent
REPO = ROOT.resolve().parents[1]


def reference(path):
    return str(path.resolve().relative_to(REPO))


def main():
    from fea.mortar_kinematic_replay import replay
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('build', type=Path)
    parser.add_argument('cubes', type=Path)
    args = parser.parse_args()
    if (ROOT/'report.json').exists():
        raise ValueError('Do not overwrite published v2 evidence')
    build = json.loads((args.build/'build_result.json').read_text())
    comparison = json.loads((args.cubes/'report.json').read_text())
    if (build['exit_code'] or comparison['build_result_sha256'] != sha(args.build/'build_result.json') or
            comparison['build_manifest_sha256'] != sha(args.build/'build_manifest.json')):
        raise ValueError('Successful matching immutable build required')
    require_comparison_coverage(comparison['runs'])
    for name, expected in build['evidence_sha256'].items():
        if sha(args.build/name) != expected:
            raise ValueError('Build evidence changed')
    for name, expected in comparison['helper_snapshot_sha256'].items():
        if sha(args.cubes/name) != expected:
            raise ValueError('Comparison helper snapshot changed')
    if sha(args.cubes/'compare_cube.launch.py') != comparison['launch_source_sha256']:
        raise ValueError('Comparison launch source changed')
    destination = Path(tempfile.mkdtemp(prefix='replay-', dir=ROOT))
    cases = []
    for run in comparison['runs']:
        directory = args.cubes/(run['case']+'-'+run['binary'])
        for name, expected in run['output_sha256'].items():
            if sha(directory/name) != expected:
                raise ValueError('Cube evidence changed')
        if (any(run['maximum_printed_difference_from_archive'].values()) or
                not run['accepted_history_equal_to_archive'] or
                not all(ep[k] for ep in run['endpoints'] for k in
                        ('force_pass', 'moment_pass', 'aggregate_friction_pass'))):
            raise ValueError('Cube comparison did not pass')
        if run['binary'] != 'observer':
            continue
        result = replay((directory/'cube.log').read_text(), (directory/'cube.sta').read_text())
        output = destination/(run['case']+'.json')
        output.write_text(json.dumps(result, indent=2, allow_nan=False)+'\n')
        cases.append({'case': run['case'], 'replay': reference(output), 'replay_sha256': sha(output),
                      'calls_checked': result['calls_checked'],
                      'accepted_coupling_count': len(result['accepted_coupling']),
                      'status': result['status'], 'limitations': result['limitations']})
    sources = [Path('fea/mortar_observer/patch.py'), Path('fea/mortar_observer/kinematic_patch.py'),
               Path('fea/mortar_observer_replay.py'), Path('fea/mortar_kinematic_replay.py'),
               Path('fea/mortar_linear_law.py'), *[ROOT/n for n in
               ('Dockerfile', 'build.py', 'record_build.py', 'compare_cube.py', 'publish.py')]]
    for path in sources:
        (destination/(path.parent.name+'-'+path.name)).write_bytes(path.read_bytes())
    report = {'status': 'V2 CUBE KINEMATIC/COUPLING REPLAY ONLY; NO FRAME OR PHYSICAL CAPACITY APPROVAL',
              'observer_image_id': build['image_id'], 'parent_image_id': build['parent_image_id'],
              'build_directory': reference(args.build), 'cube_directory': reference(args.cubes),
              'sources_sha256': {reference(p): sha(p) for p in sources},
              'evidence_sha256': {reference(p): sha(p) for p in
                                  (args.build/'build_result.json', args.build/'build_manifest.json', args.cubes/'report.json')},
              'cases': cases}
    initial = ROOT/'initial-report.json'
    if initial.exists():
        report['publication_history'] = {
            'initial_report': reference(initial), 'initial_report_sha256': sha(initial),
            'change': 'Repository-relative references; original publication and publisher snapshot retained. Solver inputs, executions and replay quantities unchanged.',
        }
    (ROOT/'report.json').write_text(json.dumps(report, indent=2, allow_nan=False)+'\n')
    print(json.dumps({'report': str(ROOT/'report.json'), 'cases': cases}), flush=True)


if __name__ == '__main__':
    main()
