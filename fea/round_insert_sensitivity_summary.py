"""Authenticate the finite insert probes and verify their controlled differences."""
import argparse
import hashlib
import json
from pathlib import Path

from fea import run_round_insert_batch
from fea.round_insert_load_assessment import build as assess
from fea.run_round_insert_batch import CASES
from fea.shell_surface_recovery import recover


def physical(record):
    elements = {e: value for e, value in record['elements'].items() if value[0] in ('C3D20', 'S8')}
    nodes = {str(n) for _, ids, _ in elements.values() for n in ids}
    return {'elements': elements, 'nodes': {n: record['nodes'][n] for n in nodes}, 'loads': record['loads'],
            'members': record['members'], 'panel_nodes': record['panel_nodes'], 'fixed_nodes': record['fixed_nodes']}


def build(directory):
    directory = Path(directory)
    summary = json.loads((directory/'summary.json').read_text())
    completed = [row['case'] for row in summary['cases']]
    if (completed != [name for name, _ in CASES][:len(completed)] or not completed
            or summary['batch_complete'] != (len(completed) == len(CASES))
            or hashlib.sha256((directory/'launch.py').read_bytes()).hexdigest() != summary['launch_sha256']):
        raise ValueError('Require authenticated completed prefix of the eight-case launch')
    records, rows = {}, []
    for saved in summary['cases']:
        root = directory/saved['case']
        payload = (root/'report.json').read_bytes()
        if hashlib.sha256(payload).hexdigest() != saved['report_sha256']:
            raise ValueError('Batch case report mismatch')
        report = json.loads(payload)
        result = assess(root)
        records[saved['case']] = json.loads((root/report['final_cycle_directory']/'input.json').read_text())
        if saved['parameters'] != report['parameters']:
            raise ValueError('Declared and native case parameters differ')
        rows.append({'case': saved['case'], 'maximum_panel_displacement_mm': report['maximum_panel_displacement_mm'],
            'maximum_withdrawal': result['maximum_withdrawal'], 'all_panel_wrench_intervals_passed': result['all_panel_wrench_intervals_passed'],
            'contact_diagnostic_checks_passed': report['contact_diagnostic_checks_passed'],
            'rejected_sample_points': records[saved['case']]['seating_rejected_point_count'],
            'discarded_tributary_area_mm2': records[saved['case']]['seating_rejected_tributary_area_mm2'],
            'assessment': result})
    base = records['f10-contact']
    core = records['f10-no-contact']
    for name, overrides in CASES:
        if name not in records:
            continue
        record = records[name]
        expected = {'hold': 'F10', 'contact': True, 'panel_stiffness': 1000., 'samples': 3, 'penalty': 100., **overrides}
        actual = {'hold': record['hold'], 'contact': record['seating_contact_enabled'],
                  'panel_stiffness': record['panel_attachment_stiffness_n_per_mm'],
                  'samples': record['seating_contact_samples_across_width'], 'penalty': record['seating_penalty_n_per_mm3']}
        if actual != expected or record['pounds'] != 250. or record['load_kind'] != 'full':
            raise ValueError('Actual probe metadata differs from finite matrix: '+name)
        if record['hold'] != 'F10':
            continue
        if physical(record) != physical(base):
            raise ValueError('Same-hold probe changed physical mesh, supports or loads: '+name)
        if ({n: record['nodes'][n] for n in core['nodes']} != core['nodes']
                or record['equations'][:len(core['equations'])] != core['equations']):
            raise ValueError('Probe changed baseline connector kinematics: '+name)
        contacts = record['seating_contacts']
        if not expected['contact'] and contacts:
            raise ValueError('No-contact control still contains seating contacts')
        if expected['contact'] and expected['samples'] == 3:
            strip = lambda row: {k: v for k, v in row.items() if k != 'normal_stiffness_n_per_mm'}
            if list(map(strip, contacts)) != list(map(strip, base['seating_contacts'])):
                raise ValueError('Stiffness/penalty probe changed seating geometry')
        for contact in contacts:
            if contact['normal_stiffness_n_per_mm'] != contact['tributary_area_mm2']*expected['penalty']:
                raise ValueError('Contact spring differs from requested penalty')
        expected_k = overrides.get('panel_stiffness', 1000.)
        for spring in record['springs']:
            if spring['name'] in record['panel_attachment_names']:
                if spring['stiffness_n_per_mm'] != expected_k:
                    raise ValueError('Panel stiffness probe differs from requested value')
            elif not spring['name'].startswith('seating_'):
                original = next(r for r in base['springs'] if (r['name'], r['dof']) == (spring['name'], spring['dof']))
                if {k: v for k, v in spring.items() if k != 'active'} != {k: v for k, v in original.items() if k != 'active'}:
                    raise ValueError('Structural connection changed in panel/contact probe')
    incomplete = []
    for name, _ in CASES:
        if name in completed:
            continue
        job = directory/name/'cycle-00'
        failure = {'case': name, 'status': 'not_started'}
        if job.exists():
            record = json.loads((job/'input.json').read_text())
            try:
                recover(record, (job/'frame.dat').read_text(), (job/'frame.frd').read_text(), (job/'frame.12d').read_text())
            except ValueError as exc:
                failure.update(status='rejected', cycle='cycle-00', reason=str(exc),
                    artifact_sha256={p.name: hashlib.sha256(p.read_bytes()).hexdigest()
                                     for p in sorted(job.iterdir()) if p.is_file()})
            else:
                failure.update(status='incomplete', reason='No completed authenticated case report')
        incomplete.append(failure)
    completed_pass = all(r['all_panel_wrench_intervals_passed'] and r['contact_diagnostic_checks_passed'] for r in rows)
    return {'candidate': 'round-insert-development', 'cases': rows, 'controlled_difference_checks_passed': True,
        'planned_case_count': len(CASES), 'completed_case_count': len(rows), 'incomplete_cases': incomplete,
        'batch_complete': summary['batch_complete'], 'completed_case_numerical_gates_passed': completed_pass,
        'all_finite_numerical_gates_passed': summary['batch_complete'] and completed_pass,
        'qualified_for_design': False, 'insert_resistance_qualified': False, 'contact_convergence_established': False,
        'source_sha256': {str(path.resolve().relative_to(Path.cwd())): hashlib.sha256(path.read_bytes()).hexdigest()
                          for path in (Path(__file__), Path(run_round_insert_batch.__file__))},
        'batch_summary_sha256': hashlib.sha256((directory/'summary.json').read_bytes()).hexdigest(),
        'limits': 'Finite arbitrary-stiffness/contact comparisons only. Whole tributaries at void samples are discarded; '
                  'sampling and penalty sensitivity do not alone establish contact convergence. Insert resistance and floor qualification remain open.'}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--directory', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    report = build(args.directory)
    with args.output.open('x') as stream:
        json.dump(report, stream, indent=2, allow_nan=False)
        stream.write('\n')
    print({row['case']: row['maximum_withdrawal'] for row in report['cases']})
