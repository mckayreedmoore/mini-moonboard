"""Current-force flush comparisons with unresolved completion gates kept explicit."""
import argparse
import gzip
import hashlib
import json
import math
from pathlib import Path

from scripts.clear_space_results import checks as existing_checks

CANDIDATE = 'compact-floor-flush-development'


def face_contact_check(report):
    """Check actual six-interface inventory and saved normal-contact reactions.

    This checks the represented quadrature, not convergence under refinement or
    clearance everywhere between its points. The 625 psi reference is the
    project's existing DF-L perpendicular-grain bearing assumption.
    """
    expected = set()
    for side in ('left', 'right'):
        expected.update({tuple(sorted(pair)) for pair in (
            (f'base_side_{side}', f'lumber_leg_{side}'),
            (f'base_post_outer_{side}', f'base_floor_{side}'),
            (f'lumber_leg_{side}', f'base_floor_{side}'))})
    contacts = report.get('member_contacts', [])
    bearings = {row['name']: row for row in report['bearings']}
    physical = report['physical_connection_forces']
    names = [row['name'] for row in contacts]
    pairs = {tuple(sorted((row['first'], row['second']))) for row in contacts}
    if not contacts or len(names) != len(set(names)) or pairs != expected:
        raise ValueError('Require unique contacts covering all six actual flush interfaces')
    records = {}
    for row in contacts:
        name = row['name']
        bearing, force = bearings[name], physical[name]
        area = row['tributary_area_mm2']
        if (not math.isfinite(area) or area <= 0 or force['first'] != row['first']
                or force['second'] != row['second'] or force['point'] != row['point_xyz_mm']
                or force['scalar_normal'] != row['normal_xyz']):
            raise ValueError('Contact geometry/reaction inventory mismatch: '+name)
        compression = bearing['compression_force_n']
        if not math.isfinite(compression) or not math.isfinite(bearing['opening_mm']):
            raise ValueError('Require finite contact response')
        records[name] = {'first': row['first'], 'second': row['second'],
            'area_mm2': area, 'compression_n': compression,
            'opening_mm': bearing['opening_mm'], 'active': bearing['active'],
            'wood_bearing_ratio': max(0., compression)/(area*625*.006894757293168361),
            'normal_contact_passed': bearing['compression_only_assumption_satisfied'] is True}
    return {'points': records, 'interface_count': len(pairs),
        'peak_wood_bearing_ratio': max(v['wood_bearing_ratio'] for v in records.values()),
        'normal_contact_passed': all(v['normal_contact_passed'] for v in records.values()),
        'scope': face_contact_check.__doc__}



def rim_cut_side_stress_diagnostic(report):
    """Signed gross stresses at first recovered full section, not the heel cut.

    Native section_u cross section_v equals grain. The reported moment is the
    moment of loads above the section, hence sigma=N/A+Mu*v/Iu-Mv*u/Iv.
    The cut heel lies on positive native v (negative CAD profile q).
    """
    result = {}
    for name in ('base_side_left', 'base_side_right'):
        data = report['member_section_demands'][name]
        member = data['member']
        b, d = member['width_mm'], member['depth_mm']
        first = min(row['station_along_grain_mm'] for row in data['sections'])
        rows = []
        for row in data['sections']:
            if not math.isclose(row['station_along_grain_mm'], first, abs_tol=1.e-6):
                continue
            stresses = [row['axial_n_tension_positive']/(b*d)
                +row['moment_u_nmm']*(d/2)/(b*d**3/12)
                -row['moment_v_nmm']*u/(d*b**3/12) for u in (-b/2, b/2)]
            rows.append({'origin_xyz_mm': row['origin_xyz_mm'],
                'include_station_loads': row['include_station_loads'],
                'cut_side_corner_stress_tension_positive_mpa': stresses})
        result[name] = {'first_recovered_station_mm': first, 'sections': rows,
            'scope': 'Adjacent full-section diagnostic only. Native recovery omits the partial heel-cut interval; these values do not establish local cut-face stresses or a compression-only taper classification.'}
    return result


def checks(report, geometry):
    if report.get('candidate') != CANDIDATE or geometry.get('candidate') != CANDIDATE:
        raise ValueError('Require matching actual flush identities; historical passes cannot transfer')
    result = existing_checks(report, geometry)
    if 'criteria' not in result:
        return result
    contacts = face_contact_check(report)
    monitors = report.get('clearance_monitors', [])
    expected_monitors = {f'flush_taper_top_{side}_{depth}_{station}'
        for side in ('left', 'right') for depth in range(3) for station in range(3)}
    monitored = ({row['name'] for row in monitors} == expected_monitors
        and len(monitors) == len(expected_monitors)
        and all(math.isfinite(row['deformed_gap_mm']) and row['deformed_gap_mm'] > 0 for row in monitors))
    result['criteria'].update({'flush_face_normal_contact': contacts['normal_contact_passed'],
        'flush_face_wood_bearing': contacts['peak_wood_bearing_ratio'] <= 1.,
        'flush_sampled_taper_top_clearance': monitored})
    result['metrics']['flush_face_wood_bearing'] = contacts['peak_wood_bearing_ratio']
    result['flush_face_contact'] = contacts
    result['rim_cut_side_stress_diagnostic'] = rim_cut_side_stress_diagnostic(report)
    result['completion_gates'] = {
        'taper_stress_method_applicability': 'OPEN: uniform-section shear and hybrid notch comparison do not establish taper-induced stress resistance.',
        'contact_discretization_adequacy': 'OPEN: actual unilateral interfaces are represented; point/mesh/stiffness refinement and unsampled clearance remain to be established.',
        'fabrication_allowances': 'OPEN: nominal placement includes existing 3 mm boundary inset; complete cut/drill/stock tolerances are not released.',
        'full_current_case_set': 'OPEN: this assessment covers only this report and cannot establish completion of other cases.'}
    result['status'] = ('IMPLEMENTED_FLUSH_CRITERIA_MET_COMPLETION_GATES_OPEN'
        if all(result['criteria'].values()) else 'IMPLEMENTED_FLUSH_CRITERIA_NOT_MET')
    result['qualified_for_design'] = False
    result['limits'].append('Earlier taper-method comparison is retained as diagnostic arithmetic; its passing flags do not close the separately listed method applicability gate.')
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--report', type=Path, required=True)
    parser.add_argument('--geometry', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    data = args.report.read_bytes()
    report = json.loads(gzip.decompress(data) if args.report.suffix == '.gz' else data)
    result = checks(report, json.loads(args.geometry.read_text()))
    result['assessment_input_sha256'] = {str(path): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in (args.report, args.geometry, Path(__file__),
            Path('scripts/clear_space_results.py'), Path('scripts/floor_taper_checks.py'))}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, allow_nan=False)+'\n')
    print(result['status'])
    print('Failed:', [key for key, value in result.get('criteria', {}).items() if not value])
    print(result.get('metrics', {}))


if __name__ == '__main__':
    main()
