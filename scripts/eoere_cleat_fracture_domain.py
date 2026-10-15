"""Check the length domain of a published mean-stress fracture method.

This source-qualified arithmetic screen reuses current saved geometry. It does
not compute an elastic stress field, a fracture capacity or a frame response.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path

from scripts import eoere_cleat_reference_audit as prior

current = prior.current
OWN = Path(__file__).resolve()
LOADED_SHA = current.sha(OWN)
INPUT = current.DOC / "selected-hardware-v1/current-response-v1/joint-closure-v1/cleat-fracture-domain-inputs-v1.json"


def positive(*values):
    current.require(all(isinstance(v, (float, int)) and not isinstance(v, bool)
                        and math.isfinite(v) and v > 0. for v in values),
                    "finite positive real parameters required")


def generalized_moduli(ex, ey, gxy, nu_xy):
    """Aquino et al. (2026), Eq.24, with x parallel to the grain."""
    positive(ex, ey, gxy)
    current.require(isinstance(nu_xy, (int, float)) and not isinstance(nu_xy, bool)
                    and math.isfinite(nu_xy) and abs(nu_xy) < math.sqrt(ex/ey),
                    "reciprocal positive plane compliance required")
    denominator = math.sqrt(ex/ey)-nu_xy+ex/(2*gxy)
    return math.sqrt(2*ex*ey/denominator), math.sqrt(2*ex*ex/denominator)


def length_bound(ei, eii, gi, gii, ft, fv):
    """Exact algebraic minimum over nonnegative mixed-mode magnitudes.

    Eqs.22-23 give x(k)=c*(1+k²/r²)/(1+q*k)², where c=x_I,
    r=fv/ft and q=sqrt(EI*GI/(EII*GII)). Cauchy-Schwarz gives
    min x = 1/(1/x_I+1/x_II), attained at k=q*r². This bound
    does not need a sampled stress ratio or the current stress field.
    """
    positive(ei, eii, gi, gii, ft, fv)
    xi, xii = 2/math.pi*ei*gi/ft**2, 2/math.pi*eii*gii/fv**2
    minimum = 1/(1/xi+1/xii)
    ratio = math.sqrt(ei*gi/(eii*gii))*(fv/ft)**2
    positive(xi, xii, minimum, ratio)
    return {"pure_mode_I_length_mm": xi, "pure_mode_II_length_mm": xii,
            "minimum_over_all_nonnegative_mode_ratios_mm": minimum,
            "minimizing_absolute_shear_to_tension_ratio": ratio}


def tangent_paths(member, polygon, bores):
    """Optimistic grain-parallel bore-tangent rays to the finished ends.

    Only the authenticated four-vertex, flat-bottom/sloped-top profile is
    accepted. Other voids, a finite averaging-band height and stress-field
    requirements are omitted, so length sufficiency is never a fracture pass.
    """
    current.require(len(polygon) == 4 and all(len(p) == 2 for p in polygon),
                    "four-vertex YZ profile required")
    current.require(all(isinstance(v, (int, float)) and not isinstance(v, bool)
                        and math.isfinite(v) for p in polygon for v in p),
                    "finite profile coordinates required")
    (yl, bottom), (yr, bottom_r), (yr_top, top_r), (yl_top, top_l) = polygon
    current.require(yl == yl_top and yr == yr_top and bottom == bottom_r
                    and yl < yr and bottom < top_l <= top_r,
                    "flat-bottom rising-top current profile required")
    current.require(len(bores) == len({b['axis_id'] for b in bores}) == 4,
                    "four distinct current cleat bores required")

    def top(y):
        return top_l+(top_r-top_l)*(y-yl)/(yr-yl)

    result = []
    for bore in bores:
        y, z, radius = bore['y_mm'], bore['z_mm'], bore['radius_mm']
        positive(radius)
        current.require(all(isinstance(v, (int, float)) and not isinstance(v, bool)
                            and math.isfinite(v) for v in (y, z)), "finite bore center required")
        current.require(yl < y-radius < y+radius < yr
                        and bottom < z-radius and z+radius < top(y-radius),
                        "whole bore envelope must lie inside the finished profile")
        for side in (-1, 1):
            path_y = y+side*radius
            for direction, end in ((-1, bottom), (1, top(path_y))):
                length = direction*(end-z)
                positive(length)
                result.append({"member": member, "axis_id": bore['axis_id'],
                               "tangent_side": side, "grain_direction": direction,
                               "path_y_mm": path_y, "start_z_mm": z, "end_z_mm": end,
                               "available_length_upper_bound_mm": length})
    return result


def validate(inputs):
    current.require(inputs['schema'] == 'eoere_cleat_fracture_domain_inputs/v1'
                    and inputs['geometry_revision'] == 'eoere-raised-kicker-screws-v1'
                    and inputs['hardware_revision'] == 'eoere-selected-purchase-hardware-v1'
                    and inputs['actual_observations'] is None and inputs['extra_grid'] is False,
                    "current unobserved, extra-grid-off domain hypothesis required")
    current.require(inputs['fracture_energies_mode_I_n_per_mm'] == [.05, .1]
                    and inputs['mode_II_to_I_energy_ratios'] == [1., 3.5]
                    and inputs['strength_divisors'] == [1.5, 2., 3.],
                    "declared historical-energy and published-ratio sensitivity scope required")
    current.require(inputs['base_strengths_mpa'] == {'tension': .4, 'parallel_shear': 2.144},
                    "unchanged intact-section base strength hypothesis required")
    expected = [{'id': 'grain_L_normal_R', 'E_x_mpa': 11032., 'E_y_mpa': 750.176,
                 'G_xy_mpa': 706.048, 'nu_xy': .292},
                {'id': 'grain_L_normal_T', 'E_x_mpa': 11032., 'E_y_mpa': 551.6,
                 'G_xy_mpa': 860.496, 'nu_xy': .449}]
    current.require(inputs['elastic_orientations'] == expected,
                    "both complete plane bindings of the existing elastic hypothesis required")


def run():
    input_path = INPUT.resolve()
    current.require(input_path.is_relative_to(current.ROOT), "repository input required")
    raw = input_path.read_bytes()
    input_ref = {'path': str(input_path.relative_to(current.ROOT)), 'sha256': hashlib.sha256(raw).hexdigest()}
    inputs = json.loads(raw)
    validate(inputs)
    cases, pins = prior.intake_source.intake()
    source = current.read(prior.DEMAND)
    refs = [input_ref, prior.DEMAND, current.ref(OWN), current.ref(Path(prior.__file__)),
            current.ref(current.ROOT/'tests/test_eoere_cleat_fracture_domain.py'), *inputs['references']]
    current.require(inputs['section_material_input'] in inputs['references'],
                    "the frozen section material input must be an explicit source pin")
    pins = current.join(pins, source['source_sha256'], {r['path']: r['sha256'] for r in refs})
    current.verify(pins)
    material = current.read(inputs['section_material_input'])
    current.require(material['intact_section_base_reference_mpa']['tension'] == inputs['base_strengths_mpa']['tension']
                    and material['intact_section_base_reference_mpa']['parallel_shear'] == inputs['base_strengths_mpa']['parallel_shear'],
                    "strengths must retain the frozen declared section hypothesis")
    profiles, paths, audit = {}, {}, []
    by_case = {b['case_id']: (b, f) for b, f, _ in cases}
    current.require(len(by_case) == 6 and len(source['cases']) == 12,
                    "all six own cases and both cleats required")
    for saved in source['cases']:
        binding, field = by_case[saved['case_id']]
        member = saved['member']
        current.require(member in ('eoere_cleat_left', 'eoere_cleat_right')
                        and saved['state_id'] == binding['state_id'] and saved['field'] == binding['field'],
                        "own authenticated case/state/field required")
        profile = next(r for r in field['source_inputs']['timber_rows'] if r['name'] == member)
        current.require(profile['axis'] == [0., 0., 1.]
                        and profile['raw_profile_source']['basis_grain_u_v_xyz'] == [[0., 0., 1.], [1., 0., 0.], [0., 1., 0.]],
                        "current grain-Z and transverse-X/Y geometry required")
        shafts = {s['axis_id']: s for s in field['source_inputs']['shafts']}
        bores = []
        for action in saved['complete_saved_exterior_point_actions']:
            suffix = '/complete-wood-wrench'
            if action['id'].endswith(suffix):
                axis_id = action['id'][:-len(suffix)]
                shaft = shafts[axis_id]
                current.require(abs(abs(shaft['basis'][0][0])-1.) < 1e-10,
                                "X-oriented current cleat bore required")
                bores.append({'axis_id': axis_id, 'y_mm': action['point_xyz_mm'][1],
                              'z_mm': action['point_xyz_mm'][2], 'radius_mm': shaft['bore_diameter_mm']/2})
        geometry = {'polygon_yz_mm': profile['raw_profile_source']['finished_YZ_polygon_mm'], 'bores': bores}
        if member in profiles:
            current.require(geometry == profiles[member], "current cleat geometry changed between own cases")
        else:
            profiles[member] = geometry
            paths[member] = tangent_paths(member, geometry['polygon_yz_mm'], bores)
        audit.append({'case_id': saved['case_id'], 'state_id': saved['state_id'],
                      'field': saved['field'], 'member': member, 'unchanged_current_geometry': True})
    scenarios = []
    for orientation in inputs['elastic_orientations']:
        ei, eii = generalized_moduli(*(orientation[k] for k in ('E_x_mpa', 'E_y_mpa', 'G_xy_mpa', 'nu_xy')))
        for divisor in inputs['strength_divisors']:
            ft, fv = (inputs['base_strengths_mpa'][k]/divisor for k in ('tension', 'parallel_shear'))
            for gi in inputs['fracture_energies_mode_I_n_per_mm']:
                for energy_ratio in inputs['mode_II_to_I_energy_ratios']:
                    bound = length_bound(ei, eii, gi, gi*energy_ratio, ft, fv)
                    minimum = bound['minimum_over_all_nonnegative_mode_ratios_mm']
                    comparisons = []
                    for member_paths in paths.values():
                        for path in member_paths:
                            length = path['available_length_upper_bound_mm']
                            comparisons.append({**path, 'minimum_required_to_available_ratio': minimum/length,
                                                'mode_I_energy_ceiling_for_any_fitting_ratio_n_per_mm': gi*length/minimum,
                                                'length_status': 'NO_NONNEGATIVE_MODE_RATIO_FITS' if minimum > length else
                                                                 'LENGTH_ALONE_DOES_NOT_RULE_OUT_SOME_MODE_RATIO'})
                    scenarios.append({'orientation': orientation['id'], 'strength_divisor': divisor,
                                      'G_Ic_n_per_mm': gi, 'G_IIc_n_per_mm': gi*energy_ratio,
                                      'mode_II_to_I_energy_ratio': energy_ratio, 'Ft90_mpa': ft, 'Fv_mpa': fv,
                                      'E_I_star_mpa': ei, 'E_II_star_mpa': eii, **bound,
                                      'paths': comparisons, 'fracture_capacity_or_current_stress_comparison': None})
    current.require(len(scenarios) == 24 and sum(len(s['paths']) for s in scenarios) == 768
                    and current.sha(OWN) == LOADED_SHA, "complete unchanged domain producer required")
    current.verify(pins)
    return {'schema': 'eoere_cleat_fracture_mean_stress_domain/v1', 'producer': current.ref(OWN),
            'inputs': input_ref, 'source_sha256': pins, 'all_sources_unchanged': True,
            'geometry_revision': inputs['geometry_revision'], 'hardware_revision': inputs['hardware_revision'],
            'extra_grid': False, 'bolt_count': 100, 'Hillman_screw_count': 66,
            'authenticated_member_case_geometry_checks': audit, 'geometry': profiles,
            'scenarios': scenarios, 'status': 'COMPLETE_PUBLISHED_MEAN_STRESS_LENGTH_DOMAIN_SCREEN',
            'current_stress_field_computed': False, 'fracture_capacity': None,
            'complete_cleat_joint_or_member_resistance': None, 'physical_demand_bounds_established': False,
            'structural_acceptance': False, 'native_or_frame_solve_CAD_rebuild_geometry_change_or_actual_fit': False,
            'limits': ['The strengths, energies and elastic planes are declared hypotheses, not observed DF-L No.2 properties. The published 3.5 energy ratio is a spruce-model sensitivity, not a measured Douglas-fir value.',
                       'The analytic lower length bound covers all nonnegative mode-I/II ratios in the published infinite-crack mixed-mode formula. A path too short cannot use that unmodified averaging construction; it is not a physical-failure or no-other-method proof.',
                       'The 32 representative tangent rays are optimistic length bounds. Fitting a length establishes neither the current mixed-mode ratio, elastic stress averages, crack growth resistance, finite-width effects nor complete connection qualification.',
                       'The cited planar mean-stress criterion covers transverse opening and grain-parallel sliding. Current width-varying actions and rolling-shear/mode-III torque require an applicable extension or another method; no stress or capacity is invented.',
                       'No native executable, frame solve, CAD query, altered geometry, panel/screw remedy, physical observation or release is introduced.']}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    with current.load('bridge').reserve(args.out) as output:
        output.write(run())
    print(json.dumps(current.ref(args.out)))


if __name__ == '__main__':
    main()
