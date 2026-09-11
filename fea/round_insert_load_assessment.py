"""Authenticated insert demands and independent panel/contact wrench checks."""
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np

from fea import round_insert_frame as frame
from fea.round_panel_load_diagnosis import panel_balance
from fea.shell_surface_recovery import recover


def build(directory):
    directory = Path(directory)
    record, provenance = frame.authenticated_input(directory)
    report = json.loads((directory/'report.json').read_text())
    job = directory/report['final_cycle_directory']
    _, _, precision = recover(record, (job/'frame.dat').read_text(),
        (job/'frame.frd').read_text(), (job/'frame.12d').read_text())
    panels = panel_balance(record, report, precision)
    for panel in panels:
        residual = np.array(panel['force_residual_n'])
        moment = np.array(panel['moment_residual_nmm'])
        force_radius = np.array(panel['force_rounding_interval_radius_n'])
        moment_radius = np.array(panel['moment_rounding_interval_radius_nmm'])
        contacts = [r for r in record['seating_contacts'] if r['panel'] == panel['panel']]
        for contact in contacts:
            value = report['connector_forces'][contact['name']]
            force = np.array(value['force_on_first_xyz_n'])
            first, second = contact['scalar_nodes']
            radius = (contact['normal_stiffness_n_per_mm']*(precision[first][0]+precision[second][0])
                      *abs(np.array(contact['inward_xyz'])))
            residual -= force
            point = contact['point_xyz_mm']
            moment -= np.cross(point, force)
            force_radius += radius
            x, y, z = point
            moment_radius += np.abs([[0., -z, y], [z, 0., -x], [-y, x, 0.]])@radius
        panel.update(seating_contact_count=len(contacts), force_residual_n=residual.tolist(),
            moment_residual_nmm=moment.tolist(), force_rounding_interval_radius_n=force_radius.tolist(),
            moment_rounding_interval_radius_nmm=moment_radius.tolist(),
            wrench_balance_passed=bool(np.all(abs(residual) <= force_radius+1.e-5)
                                      and np.all(abs(moment) <= moment_radius+.001)))
    worst = max((row for panel in panels for row in panel['attachments']), key=lambda r: r['withdrawal_n'])
    paths = [Path(__file__), Path('fea/round_panel_load_diagnosis.py'),
             Path('fea/round_insert_frame.py'), Path('fea/shell_surface_recovery.py'),
             Path('fea/frd_displacements.py'), Path('fea/horizontal_panel_frame.py'),
             Path('fea/horizontal_frame_stress.py'), Path('fea/panel_screw_sensitivity.py'),
             Path('pyproject.toml'), Path('uv.lock')]
    return {'candidate': record['candidate'], 'hold': record['hold'], 'parameters': report['parameters'],
        'provenance': provenance, 'source_sha256': {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths},
        'panels': panels, 'maximum_withdrawal': worst,
        'all_panel_wrench_intervals_passed': all(p['wrench_balance_passed'] for p in panels),
        'insert_product': 'E-Z LOK 801420-13', 'machine_screw_product': 'Dottie FMDD14114',
        'qualified_withdrawal_resistance_n': None, 'qualified_head_pull_through_resistance_n': None,
        'effective_thread_engagement_mm': None,
        'insert_demands_qualified': False, 'insert_resistance_qualified': False, 'qualified_for_design': False,
        'limits': 'Finite native diagnostic with corrected shell displacement recovery. Measured insert '
                  'stiffness, effective thread overlap, exact receiver/pilot resistance, head pull-through '
                  'in owned plywood, combined/cyclic actions and actual floor remain unqualified. '
                  'Manufacturer does not publish Hex Drive performance tests; SPAX references are not transferred.',
        'resistance_source': 'https://www.ezlok.com/testing'}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--directory', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    report = build(args.directory)
    with args.output.open('x') as stream:
        json.dump(report, stream, indent=2, allow_nan=False)
        stream.write('\n')
    print({key: report[key] for key in ('all_panel_wrench_intervals_passed', 'maximum_withdrawal')})
