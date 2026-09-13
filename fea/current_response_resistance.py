"""Conditional resistance comparisons for the shoe-free 277 mm response model.

This module consumes recovered current forces without building CAD or running a
solver. Full-length unbraced member checks are sensitivities, not assertions that
panel-connected members lack restraint. Numerical validity remains a prerequisite
for interpreting any demand. No comparison establishes a climber weight rating.
"""
import argparse
import json
import math
from pathlib import Path

from fea.dowel_yield import single_shear
from fea.reinforced_fastener_checks import (
    LBF_N,
    dot,
    norm,
    panel_check,
    subtract,
    wrench,
)
from fea.reinforced_fastener_checks import (
    VALIDITY as FASTENER_VALIDITY,
)
from fea.reinforced_timber_resistance import (
    conditional_dowel_reference,
    effective_beam_length,
    member_check,
)

ROOT = Path(__file__).resolve().parents[1]
VALIDITY = (*FASTENER_VALIDITY, 'member_equilibrium_passed', 'numerically_accepted')


def member_comparisons(report):
    results = {}
    for name, data in report['member_section_demands'].items():
        member = data['member']
        original_width, original_depth = member['width_mm'], member['depth_mm']
        width, depth = sorted((original_width, original_depth))
        swapped = original_width > original_depth
        length = data['length_mm']
        rows = []
        for section in data['sections']:
            check = member_check(
                width_mm=width, depth_mm=depth,
                axial_n=section['axial_n_tension_positive'],
                moment_strong_nmm=section['moment_v_nmm' if swapped else 'moment_u_nmm'],
                moment_weak_nmm=section['moment_u_nmm' if swapped else 'moment_v_nmm'],
                shear_strong_n=section['shear_u_n' if swapped else 'shear_v_n'],
                shear_weak_n=section['shear_v_n' if swapped else 'shear_u_n'],
                torsion_nmm=section['torsion_nmm'],
                column_effective_strong_mm=length,
                column_effective_weak_mm=length,
                beam_effective_mm=effective_beam_length(length, depth))
            necessary = max(check['necessary_compression_interaction_even_if_fully_braced'],
                            check['tension_conservative_interaction'], check['shear_ratio'])
            ratios = [necessary, check['stability_interaction_NDS_3_9_4']]
            compression = check['compression_biaxial_interaction_NDS_3_9_3']
            if compression is not None:
                ratios.append(compression)
            rows.append({'station_along_grain_mm': section['station_along_grain_mm'],
                         'include_station_loads': section['include_station_loads'],
                         'actions': section, 'necessary_gross_section_ratio': necessary,
                         'full_length_unbraced_ratio': max(ratios), **check})
        peak = max(rows, key=lambda row: row['necessary_gross_section_ratio']) if rows else None
        results[name] = {
            'width_mm': width, 'depth_mm': depth, 'gross_length_mm': length,
            'section_valid_from_mm': data['section_valid_from_mm'],
            'gross_section_peak': peak,
            'full_length_unbraced_peak': max(rows, key=lambda r: r['full_length_unbraced_ratio']) if rows else None,
            'full_length_unbraced_sensitivity_failed': any(r['conditional_checked_failure'] for r in rows),
            'checks': rows, 'force_residual_n': data['force_residual_n'],
            'moment_residual_nmm': data['moment_residual_nmm'],
            'limits': ['Dry, unincised Douglas Fir-Larch No. 2 with CD=CM=Ct=1 is assumed.',
                       'The gross section omits service bores, bolt holes and local load introduction.',
                       'The full current member length is an unbraced pin-end sensitivity. Actual restraint is not established by this calculation.',
                       'A necessary gross-section screen below unity does not establish stability, torsion or opening resistance.'],
            'qualified_for_design': False}
    return results


def bolt_comparison(row, members):
    """Use individual solved forces and actual current grain directions."""
    axis = row['axis']
    if not math.isclose(norm(axis), 1., abs_tol=1.e-8):
        raise ValueError('Bolt installation axis must be unit length')
    force = row['force_on_first_xyz_n']
    axial = dot(force, axis)
    lateral_vector = subtract(force, [axial*x for x in axis])
    lateral = norm(lateral_vector)
    bearing = []
    for key in ('first', 'second'):
        grain = members[row[key]]['axis']
        cosine2 = min(1., (dot(lateral_vector, grain)/lateral)**2) if lateral else 0.
        # Published DF-L dowel-bearing references for the retained 3/8-inch bolt.
        bearing.append(5600*3650/(5600*(1-cosine2)+3650*cosine2))
    reference = conditional_dowel_reference(False, *bearing)
    # Diameter alternatives retain identical bearing strengths, loads and Rd.
    # No second distribution factor is needed for this individual-force screen.
    diameter = .375
    smooth = single_shear(main_length_in=1.5, side_length_in=1.5,
        main_bearing_lb_in=bearing[0]*diameter, side_bearing_lb_in=bearing[1]*diameter,
        main_yield_moment_lb_in=45000*diameter**3/6,
        side_yield_moment_lb_in=45000*diameter**3/6, gap_in=0.,
        reduction_terms={'Im': 5., 'Is': 5., 'II': 4.5, 'IIIm': 4., 'IIIs': 4., 'IV': 4.})
    nominal_capacity = smooth['reference_lateral_lbf']*LBF_N
    return {'force_on_first_xyz_n': force, 'lateral_demand_n': lateral,
            'axial_increment_n': axial, 'reference': reference,
            'lateral_ratio': lateral/reference['adjusted_lateral_n'],
            'individual_root_reference_n': reference['reference_lateral_n'],
            'individual_root_ratio_without_second_group_factor': lateral/reference['reference_lateral_n'],
            'conditional_nominal_diameter_reference_n': nominal_capacity,
            'conditional_nominal_diameter_ratio': lateral/nominal_capacity,
            'conditional_nominal_diameter_yield_mode': smooth['governing_mode'],
            'nominal_diameter_condition': 'Full-body 3/8-inch bolt with threaded bearing no more than one quarter of each solid member bearing length; delivered thread/runout/tolerances must satisfy NDS 12.3.7.2.',
            'group_factor_scope': 'The inherited four-fastener/70 mm Cg is retained only as a historical conservative comparison. Actual rows contain two bolts, and the FE forces already resolve unequal distribution; use the separate individual-force ratio for that interpretation.',
            'limits': ['The existing 3/8-inch single-shear wood/wood joint is assumed, with a 0.298-inch thread root throughout.',
                       'Fyb at least 45 ksi is conditional; the modeled A307 designation alone does not establish it.',
                       'The inherited conservative four-fastener group factor does not establish equal sharing.',
                       'Axial bolt, washer, prying, edge distances and splitting resistance are not qualified by this lateral comparison.'],
            'qualified_for_design': False}


def angle_comparisons(forces, stations):
    """Retain each flange wrench; do not cancel both flanges to hide transfer."""
    lookup = {s['name']: s for s in json.loads((ROOT/'docs/reinforced-fastener-applicability.json').read_text())['ML24Z']['stations']}
    output = {}
    for station in stations:
        name = station['name']
        origin = station.get('origin_mm', station.get('origin'))
        if name in lookup:
            mapping = lookup[name]
            for axis in ('u', 'v'):
                if norm(subtract(station[axis], mapping[axis])) > 1.e-7:
                    raise ValueError('Current ML24Z orientation differs: '+name)
        elif name in ('clip_angle_base_left', 'clip_angle_base_right'):
            mapping = {'F1_axis': [0., 1., 0.], 'F2_separation_axis': [0., 0., 1.],
                       'F3_F4_axis_unsigned': [1., 0., 0.], 'F2_catalog_allowable_lbf': None}
            if abs(station['v'][2]-1.) > 1.e-7 or abs(abs(station['u'][0])-1.) > 1.e-7:
                raise ValueError('Unexpected outer base-angle orientation')
        else:
            raise ValueError('Unknown current angle station: '+name)
        groups = {flange: [forces[f'{name}_{flange}_{i}'] for i in (1, 2, 3)]
                  for flange in ('beam', 'upright')}
        for group in groups.values():
            for row in group:
                if row['second'] != name:
                    raise ValueError('Expected wood-first/angle-second force ownership')
        flanges = {key: wrench(rows, origin) for key, rows in groups.items()}
        bearing = mapping['F2_catalog_allowable_lbf'] is None
        loaded = flanges['upright' if bearing else 'beam']
        projected = {key: dot(loaded['force_xyz_n'], mapping[axis]) for key, axis in (
            ('F1', 'F1_axis'), ('F2', 'F2_separation_axis'), ('F34', 'F3_F4_axis_unsigned'))}
        rated_ratio = abs(projected['F1'])/(595*LBF_N)+abs(projected['F34'])/(450*LBF_N)
        if not bearing:
            rated_ratio += abs(projected['F2'])/(450*LBF_N)
        output[name] = {'origin_mm': origin, 'flange_member_on_bracket_wrenches': flanges,
            'all_six_screw_residual': wrench(groups['beam']+groups['upright'], origin),
            'projected_loaded_flange_force_n': projected,
            'rated_force_component_unity': rated_ratio,
            'bearing_like': bearing,
            'unlisted_separation_demand_n': max(0., projected['F2']) if bearing else None,
            'independent_couple_resolved': False,
            'limits': ['A conservative absolute directional interaction uses the weaker F3/F4 reference for both signs.',
                       'Bearing-like separation is unlisted, not zero capacity. Timber compression requires its own contact check.',
                       'Catalog grain and mounting applicability and the force application points remain conditional; flange moments are retained.'],
            'qualified_for_design': False}
    return output


def assess(report, stations=None):
    if report.get('candidate') != 'no-shoes-development':
        raise ValueError('Require the current shoe-free candidate response')
    forces = {}
    for name, source in report['physical_connection_forces'].items():
        row = dict(source)
        row.setdefault('force_on_second_xyz_n', [-x for x in row['force_on_first_xyz_n']])
        if norm([a+b for a, b in zip(row['force_on_first_xyz_n'], row['force_on_second_xyz_n'], strict=True)]) > 1.e-6:
            raise ValueError('Action/reaction mismatch: '+name)
        forces[name] = row
    members = {name: data['member'] for name, data in report['member_section_demands'].items()}
    panels = {name: panel_check(row) for name, row in forces.items()
              if name.startswith(('round_panel_', 'round_kicker_', 'kicker_header_')) and 'axis' in row}
    bolts = {name: bolt_comparison(row, members) for name, row in forces.items()
             if name.startswith('lumber_leg_bolt_')}
    stations = stations if stations is not None else report.get('angle_stations', report.get('ML24Z_stations', []))
    validity = {key: report.get(key) for key in VALIDITY}
    return {'candidate': report['candidate'], 'producer_validity': validity,
            'response_status': 'converged_conditional_model' if all(v is True for v in validity.values()) else 'INVALID_RESPONSE_DIAGNOSTIC_ONLY',
            'members': member_comparisons(report), 'leg_bolts': bolts,
            'panel_screws': panels, 'ML24Z': angle_comparisons(forces, stations),
            'missing_angle_inventory': not bool(stations),
            'connection_inventory_complete': len(panels) == 66 and len(bolts) == 8 and len(stations) == 24,
            'connection_counts': {'panel_screws': len(panels), 'leg_bolts': len(bolts), 'ML24Z': len(stations)},
            'reference_basis': 'Existing published NDS/TR12/SPAX/Simpson references; no load-duration increase is applied.',
            'floor_basis': 'No-slip supports are an owner-authorized analytical assumption. No friction qualification is added.',
            'qualified_for_design': False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('report', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    result = assess(json.loads(args.report.read_text()))
    with args.output.open('x') as stream:
        json.dump(result, stream, indent=2, allow_nan=False)
        stream.write('\n')


if __name__ == '__main__':
    main()
