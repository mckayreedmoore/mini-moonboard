"""Signed panel-screw demand versus unadjusted references; not joint qualification."""
import argparse
import hashlib
import json
import math
from pathlib import Path

N_PER_LBF = 4.4482216152605
REFERENCE = 'https://www.drjcertification.org/report/download/1936'
NON_GEOMETRY_CONSUMERS = {'mini_moonboard/horizontal_service_drilling.py'}


def require_unchanged_geometry(name):
    """Recorded export/drilling consumer drift cannot authorize producer drift."""
    if (name.startswith(('mini_moonboard/', 'docs/'))
            and not name.endswith('_exports.py') and name not in NON_GEOMETRY_CONSUMERS):
        raise ValueError('Current geometry/reference differs: '+name)


def resolve(force, direction):
    """First spring endpoint is wood; outward wood force is screw withdrawal."""
    axial = sum(f*d for f, d in zip(force, direction, strict=True))
    return max(0., -axial), max(0., axial), math.sqrt(max(0., sum(f*f for f in force)-axial*axial))


def build(root, model=None, screw_count=87, case_count=10, coupled_count=8):
    if model is None:
        from mini_moonboard import horizontal_service_frame as model

    screws = {c.name: c for c in model.connections() if isinstance(c, model.timber.PanelScrew)}
    if len(screws) != screw_count or any(abs(c.length-50.8) > 1e-6 or abs(c.diameter-4.1402) > 1e-6 for c in screws.values()):
        raise ValueError(f'Expected current {screw_count} SPAX #8 x2in panel/kicker screws')
    digest = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
    summary_path = root/'summary.json'
    summary = json.loads(summary_path.read_text())
    if len({case['case'] for case in summary['cases']}) != len(summary['cases']):
        raise ValueError('Duplicate native sensitivity case')
    if len(summary['cases']) != case_count:
        raise ValueError(f'Require complete {case_count}-case native sensitivity batch')
    hashes = {str(summary_path): digest(summary_path)}
    rows, omitted, differences = [], [], {}
    for case in summary['cases']:
        path = root/case['case']/'report.json'
        if digest(path) != case['report_sha256']:
            raise ValueError('Batch report hash mismatch')
        report = json.loads(path.read_text())
        if not report['contact_diagnostic_checks_passed']:
            raise ValueError('Incomplete diagnostic case')
        for name, sha in report['source_sha256'].items():
            snapshot = path.parent/'source_snapshots'/name
            if digest(snapshot) != sha:
                raise ValueError('Archived solver source mismatch: '+name)
            # Solver source may have acquired a new optional patch parameter;
            # actual CAD and recorded reference inputs must still match.
            if digest(Path(name)) != sha:
                differences[name] = {'archived': sha, 'current': digest(Path(name))}
                require_unchanged_geometry(name)
        input_path = path.parent/report['final_cycle_directory']/'input.json'
        key = str(input_path.relative_to(path.parent))
        if digest(input_path) != report['artifact_sha256'][key]:
            raise ValueError('Final input changed')
        record = json.loads(input_path.read_text())
        hashes[str(path)], hashes[str(input_path)] = digest(path), digest(input_path)
        if record['mode'] != 'coupled':
            omitted.append(case['case'])
            continue
        if not screws.keys() <= report['connector_forces'].keys():
            raise ValueError('Missing panel connector forces')
        for name, c in screws.items():
            result = report['connector_forces'][name]
            expected = (c.start+c.direction*(model.wide.PANEL/2)).toTuple()
            if math.dist(result['first_point_xyz_mm'], expected) > 1e-5:
                raise ValueError('Panel spring first endpoint differs from actual wood attachment')
            tension, compression, shear = resolve(result['force_on_first_xyz_n'], c.direction.toTuple())
            # Optimistic upper embedded thread length; taper/grooves can reduce it.
            length = min(1.24, (c.length-model.wide.PANEL)/25.4)
            withdrawal, head = 133*length*N_PER_LBF, 212*N_PER_LBF
            rows.append({'case': case['case'], 'connection': name, 'receiver': c.members[1],
                         'withdrawal_tension_n': tension, 'axial_compression_n': compression,
                         'lateral_resultant_n': shear, 'optimistic_embedded_thread_in': length,
                         'unadjusted_withdrawal_reference_n': withdrawal,
                         'conditional_unadjusted_head_reference_n': head,
                         'withdrawal_reference_ratio': tension/withdrawal,
                         'head_reference_ratio': tension/head,
                         'exceeds_unadjusted_axial_reference': tension > min(withdrawal, head)})
    if len(rows) != coupled_count*screw_count:
        raise ValueError(f'Require {coupled_count} coupled cases and all {screw_count} panel/kicker connectors')
    worst = {key: max(rows, key=lambda r: r[key]) for key in
             ('withdrawal_tension_n', 'lateral_resultant_n', 'withdrawal_reference_ratio', 'head_reference_ratio')}
    hashes[str(Path(__file__).relative_to(Path.cwd()))] = digest(Path(__file__))
    return {'candidate': model.KEY, 'reference_url': REFERENCE, 'reference_revision': '2025-11-04',
            'qualified_for_design': False, 'actual_joint_demands_qualified': False,
            'adjusted_capacity_failure_established': False,
            'limits': f'Maxima over {coupled_count} finite coupled probes, not a bound on unknown slip/load cases. '
                      'DF-L SG0.50 dry face-grain withdrawal, optimistic embedded thread. '
                      'Head reference requires23/32 plywood SG>=0.50, not established by lumber species. '
                      'NDS adjustments, combined action, splitting, grooves, cyclic response and actual '
                      'connector stiffness remain unresolved. No SPF lateral table assigned to DF-L. '
                      'Reference exceedance is not proof of physical failure or adjusted-capacity failure.',
            'excluded_frame_load_controls': omitted, 'rows': rows, 'worst': worst,
            'archived_source_differences_from_current': differences,
            'input_sha256': hashes}


if __name__ == '__main__':
    assert resolve([0., 0., -10.], [0., 0., 1.]) == (10., 0., 0.)
    assert resolve([3., 0., 4.], [0., 0., 1.]) == (0., 4., 3.)
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--directory', type=Path, default=Path('fea/generated/horizontal-frame-batch-v2'))
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    report = build(args.directory)
    with args.output.open('x') as stream:
        json.dump(report, stream, indent=2, allow_nan=False)
        stream.write('\n')
    print(json.dumps(report['worst'], indent=2))
