"""Current-force flush comparisons with unresolved completion gates kept explicit."""
import argparse
import gzip
import hashlib
import json
import math
from pathlib import Path

from scripts.clear_space_results import checks as existing_checks

CANDIDATE = 'compact-floor-flush-development'
FROZEN_ADOPTED_CRITERIA = frozenset({
    'actual_angle_lateral_CD_1', 'additional_group_reduction_sensitivity',
    'local_parallel', 'supplemental_EC5_splitting', 'sampled_net_member',
    'header_gross_full_length_stability', 'base_bearing_average',
    'base_bearing_quarter_area_sensitivity', 'base_end_notch_shear',
    'group_spacing', 'catalog_washer_bounds', 'directional_edges',
    'steel_direct', 'washer_bearing', 'washer_bending', 'receiver_fit',
    'overlap_contact', 'all_machining_represented', 'sampled_member_stability',
    'all_bolt_centres_sampled', 'angle_rated_force_components',
    'floor_rail_wood_bearing', 'actual_kicker_cutouts',
    'taper_native_actual_taper', 'taper_native_matches_cad_taper',
    'taper_actual_mesh_volume', 'taper_taper_at_least_one_in_ten',
    'taper_intended_stock_and_runout', 'taper_taper_bounds_sampled',
    'taper_actual_net_section_normal_resistance',
    'taper_sampled_rectangular_shear_torsion',
    'taper_taper_region_unbored_torsion_applicable', 'component_layouts',
    'flush_face_normal_contact', 'flush_face_wood_bearing',
    'flush_sampled_taper_top_clearance',
})
CONDITIONAL_CRITERIA = frozenset({'finite_floor_friction_law'})


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
        'finite_adopted_check': True,
        'load_path_interfaces': sorted(pairs),
        'sampling_limitation': ('The six saved interface quadratures are a finite '
            'represented-contact check; they are not a convergence proof or a '
            'claim about unsampled clearance.'),
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
    projected_seat = result['criteria'].pop('base_end_cut_geometry')
    result['non_adopted_sensitivities'] = {
        'base_end_cut_geometry': {
            'recorded_result': projected_seat,
            'minimum_quarter_depth_margin_after_3mm_allowance_mm': min(
                row['quarter_depth_margin_after_3mm_allowance_mm']
                for row in result['base'].values()),
            'adopted_as_acceptance_criterion': False,
            'reason': ('Historical projected-seat scalar has no established mapping to '
                       'this supported terminal bevel. Retained-section, bearing, '
                       'contact and gross/net checks remain adopted.'),
        },
    }
    names = set(result['criteria'])
    missing = FROZEN_ADOPTED_CRITERIA - names
    unexpected = names - FROZEN_ADOPTED_CRITERIA - CONDITIONAL_CRITERIA
    if missing or unexpected:
        raise ValueError(f'Floor-runner criteria ledger drift: missing={sorted(missing)}, '
                         f'unexpected={sorted(unexpected)}')
    result['criteria_ledger'] = {
        'revision': 'floor-runner-mvp-2026-09-16',
        'document': 'docs/floor-runner-mvp-criteria.md',
        'required_adopted': sorted(FROZEN_ADOPTED_CRITERIA),
        'conditional_adopted': sorted(names & CONDITIONAL_CRITERIA),
    }
    result['metrics']['flush_face_wood_bearing'] = contacts['peak_wood_bearing_ratio']
    result['flush_face_contact'] = contacts
    result['rim_cut_side_stress_diagnostic'] = rim_cut_side_stress_diagnostic(report)
    result['analytical_limits'] = {
        'taper_local_fracture': {
            'classification': 'ANALYTICAL_LIMITATION',
            'description': ('The nominal cut-face stress inference is not an '
                'applicable local-fracture resistance check and is not converted '
                'into a numerical pass or failure.'),
            'inspection_controls': [
                'Use sound, check-free stock at the 1:12 recess.',
                'Make a smooth transition with no overcut.',
                'Reject splits, checks, or other recess damage.',
            ],
            'release_effect': ('Controls are required at fabrication; this '
                'limitation is not a separate open analytical gate.'),
        },
        'contact_sampling': {
            'classification': 'FINITE_SAMPLING_LIMITATION',
            'description': contacts.get('sampling_limitation',
                'The six saved interface quadratures are a finite represented-contact check; '
                'they are not a convergence proof or a claim about unsampled clearance.'),
            'finite_adopted_check': True,
            'release_effect': ('The exact six runner/post/leg interfaces and '
                'their saved normal reactions remain adopted finite checks; '
                'no open-ended refinement gate is created.'),
        },
    }
    result['completion_gates'] = {
        'fabrication_allowances': 'OPEN: nominal placement includes existing 3 mm boundary inset; complete cut/drill/stock tolerances are not released.',
        'full_current_case_set': 'OPEN: this assessment covers only this report and cannot establish completion of other cases.'}
    result['status'] = ('IMPLEMENTED_FLUSH_CRITERIA_MET_COMPLETION_GATES_OPEN'
        if all(result['criteria'].values()) else 'IMPLEMENTED_FLUSH_CRITERIA_NOT_MET')
    result['qualified_for_design'] = False
    result['limits'].append('Earlier taper-method comparison is retained as diagnostic arithmetic; the taper local-fracture behavior remains an analytical limitation paired with stock and cut inspection controls.')
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
