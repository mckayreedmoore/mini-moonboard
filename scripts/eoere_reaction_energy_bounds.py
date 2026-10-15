"""Reaction enclosures in a declared first-order stiffness family, without a solve.

For the saved q, recover a dual-feasible load f_hat=f+grad(Pi(q)). In exact
arithmetic the old quadratic complementary energy is Q and the unchanged
radial-clearance term is L. Hence C0=Q+L=-Pi(q)+q.grad(Pi(q)).

Keep panel/attachment and floor laws fixed. Vary the other positive spring
coefficients in [alpha,beta] times their old values and the elastic core in
the corresponding Loewner interval, with its kernel unchanged. Fenchel's
inequality bounds the dual gap at the old primal/dual pair by eta*Q_variable,
where eta=max(alpha+1/alpha-2,beta+1/beta-2). Strong convexity of each spring's
quadratic conjugate then gives sum ||delta r_j||^2/(2*k'_j) <= that gap.
Contact switches are permitted. A Cauchy bound encloses resultant/couple
changes without prescribing their directions. These are conditional model
bounds for f_hat, not physical bounds for the original loads or measured parts.
"""
from __future__ import annotations

import argparse
import importlib.metadata
import math
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np

from scripts import eoere_current_washer_lands as intake_source
from scripts.summarize_eoere_current_response import canonical_sha

current = intake_source.current
OWN = Path(__file__).resolve()
LOADED_SHA = current.sha(OWN)
INPUT = current.DOC/'selected-hardware-v1/current-response-v1/joint-closure-v1/reaction-energy-bound-inputs-v1.json'
FIXED_KINDS = {'panel_screw', 'panel_contact', 'floor_normal', 'floor_tangent'}
GROUP_COUNTS = {'panel_screw': 66, 'common_shaft_bearing': 416}
CONTACT_COUNTS = {'timber_face_contact': 332, 'panel_contact': 922, 'flange_contact': 352,
                  'floor_normal': 32, 'shaft_end_capture': 200}


def validate(inputs):
    current.require(inputs['schema'] == 'eoere_current_reaction_energy_bound_inputs/v1'
                    and inputs['geometry_revision'] == 'eoere-raised-kicker-screws-v1'
                    and inputs['hardware_revision'] == 'eoere-selected-purchase-hardware-v1'
                    and inputs['current_bolt_count'] == 100 and inputs['current_screw_count'] == 66
                    and inputs['extra_grid'] is False and inputs['actual_observations'] is None
                    and inputs['physical_demand_bounds_established'] is False
                    and inputs['structural_acceptance'] is False, 'unchanged conditional current scope required')
    current.require(inputs['stiffness_families'] == [
        {'id': 'unchanged-law-control', 'alpha': 1., 'beta': 1.},
        {'id': 'half-to-double-trial', 'alpha': .5, 'beta': 2.},
        {'id': 'tenth-to-tenfold-trial', 'alpha': .1, 'beta': 10.}],
        'declared engineering trial families required')
    current.require(inputs['fixed_spring_kinds'] == sorted(FIXED_KINDS)
                    and inputs['energy_padding_nmm'] == .001
                    and inputs['identity_tolerance_nmm'] == 1e-5
                    and inputs['saved_force_tolerance_n'] == 1e-6
                    and inputs['wood_land_reference_mpa'] == 625*0.006894757293168361
                    and inputs['runtime_versions'] == {'numpy': '2.5.2', 'scipy': '1.18.1'},
                    'fixed laws, scalar reference and arithmetic gates required')


def gap_factor(alpha, beta):
    current.require(math.isfinite(alpha) and math.isfinite(beta) and 0. < alpha <= 1. <= beta,
                    'finite positive stiffness interval containing the old law required')
    return max((alpha-1.)**2/alpha, (beta-1.)**2/beta)


def perturbation_bound(gap, stiffness_sum):
    current.require(math.isfinite(gap) and math.isfinite(stiffness_sum) and gap >= 0. and stiffness_sum >= 0.,
                    'finite nonnegative gap and stiffness required')
    return math.sqrt(2.*gap*stiffness_sum)


def group_energy(row, force):
    force = np.asarray(force, dtype=float)
    current.require(force.shape == (3,) and np.isfinite(force).all()
                    and all(math.isfinite(row[k]) and row[k] >= 0. for k in ('ka', 'kl', 'clearance')),
                    'finite nonnegative spring law and three local force components required')
    a, lateral = float(force[0]), float(np.linalg.norm(force[1:]))
    current.require(not row['tension_only'] or a >= 0., 'tension-only conjugate domain required')
    current.require((row['ka'] > 0. or a == 0.) and (row['kl'] > 0. or lateral == 0.),
                    'zero-stiffness component cannot carry force')
    quadratic = .5*((a*a/row['ka'] if row['ka'] else 0.)+(lateral*lateral/row['kl'] if row['kl'] else 0.))
    return quadratic, row['clearance']*lateral


def contact_energy(row, force):
    current.require(math.isfinite(force) and force >= 0. and math.isfinite(row['stiffness'])
                    and row['stiffness'] > 0., 'compression-only positive-stiffness conjugate domain required')
    return .5*force**2/row['stiffness']


def wood_surface(row, shaft, ports, gap, beta):
    """Two exact own Gauss ports; resultant and moment about their own midpoint."""
    surface = row['surface']
    current.require(surface['kind'] == 'wood' and surface in shaft['surfaces'] and len(ports) == 2
                    and {p['row']['quad_index'] for p in ports} == {0, 1}
                    and all(p['row']['surface'] == surface and p['row']['axis_id'] == shaft['axis_id']
                            and p['row']['kind'] == 'common_shaft_bearing' and p['row']['ka'] == 0.
                            and p['row']['first'] == shaft['body'] and p['row']['second'] == surface['host']
                            for p in ports), 'two own wood-bearing ports required')
    lo, hi = surface['interval_mm']
    current.require(math.isfinite(lo) and math.isfinite(hi) and hi > lo, 'positive own wood-bearing interval required')
    direction = np.asarray(shaft['basis'][0])
    center = np.asarray(shaft['point'])+.5*(lo+hi)*direction
    force, moment = np.zeros(3), np.zeros(3)
    k_sum, k_arm_sum = 0., 0.
    for port in ports:
        descriptor = port['row']
        basis = np.asarray(descriptor['basis'])
        arm = np.asarray(descriptor['point_xyz_mm'])-center
        k = descriptor['kl']
        current.require(np.allclose(basis@basis.T, np.eye(3), rtol=0., atol=1e-8)
                        and np.linalg.norm(np.cross(arm, direction)) < 1e-6
                        and abs(np.linalg.norm(arm)-(hi-lo)/(2*math.sqrt(3))) < 1e-6
                        and abs(descriptor['weight_length_mm']-.5*(hi-lo)) < 1e-6
                        and abs(k/descriptor['weight_length_mm']-26.246719160104988) < 1e-7,
                        'own source basis, Gauss stations and current wood foundation required')
        # The constitutive force multiplies B=(second-first); its force on
        # the first body (the shaft) is negative in the frozen exporter.
        f = -basis.T@port['force']
        action = port['source_action']
        current.require(all(action[key] == descriptor[key] for key in
                            ('id', 'axis_id', 'first', 'second', 'surface_index', 'quad_index', 'point_xyz_mm'))
                        and action['surface_interval_mm'] == surface['interval_mm']
                        and np.linalg.norm(np.asarray(action['force_on_first_xyz_n'])-f) <= 1e-6
                        and np.linalg.norm(np.asarray(action['force_on_second_xyz_n'])+f) <= 1e-6
                        and np.linalg.norm(action['moment_on_first_at_point_xyz_nmm']) <= 1e-6
                        and np.linalg.norm(action['moment_on_second_at_point_xyz_nmm']) <= 1e-6,
                        'signed own saved bearing actions and zero point couples required')
        force += f
        moment += np.cross(arm, f)
        k_sum += k
        k_arm_sum += k*float(arm@arm)
    current.require(abs(k_arm_sum-k_sum*(hi-lo)**2/12.) < 1e-4,
                    'own Gauss second moment must match the interval')
    df, dm = perturbation_bound(gap, beta*k_sum), perturbation_bound(gap, beta*k_arm_sum)
    return {'axis_id': shaft['axis_id'], 'host': surface['host'], 'surface_index': row['surface_index'],
            'bearing_interval_mm': surface['interval_mm'], 'moment_reference_xyz_mm': center.tolist(),
            'old_force_on_shaft_xyz_n': force.tolist(), 'old_couple_on_shaft_xyz_nmm': moment.tolist(),
            'force_change_norm_upper_n': df, 'couple_change_norm_upper_nmm': dm,
            'force_norm_upper_n': float(np.linalg.norm(force))+df,
            'couple_norm_upper_nmm': float(np.linalg.norm(moment))+dm,
            'complete_joint_or_brittle_resistance': None}


def seed(binding, field, snapshot, frozen, inputs):
    current.require(dict(Counter(r['kind'] for r in snapshot.groups)) == GROUP_COUNTS
                    and dict(Counter(r['kind'] for r in snapshot.contacts)) == CONTACT_COUNTS,
                    'exact current group/contact inventory required')
    q = np.asarray(field['response']['q'])
    k = snapshot.assembly.K
    asymmetry = k-k.T
    symmetry_error = float(abs(asymmetry.data).max()) if asymmetry.nnz else 0.
    current.require(np.isfinite(k.data).all() and np.isfinite(q).all()
                    and symmetry_error <= 1e-12*float(abs(k.data).max()), 'finite symmetric saved elastic operator required')
    gradient, potential, _, group_forces, normal, _ = frozen.law.replay(
        k, snapshot.applied, snapshot.groups, snapshot.contacts, snapshot.tangents, q)
    current.require(float(abs(gradient).max()) <= 1e-5
                    and float(abs(group_forces-np.asarray(field['response']['connector_local_force_n'])).max())
                    <= inputs['saved_force_tolerance_n']
                    and float(abs(normal-np.asarray(field['response']['normal_contact_force_n'])).max())
                    <= inputs['saved_force_tolerance_n']
                    and abs(potential-field['response']['potential_energy_nmm']) <= inputs['identity_tolerance_nmm'],
                    'own admitted residual, saved forces and potential required')
    energy, ports, clearance = defaultdict(float), [], 0.
    energy['core'] = .5*float(q@(k@q))
    current.require(energy['core'] >= 0., 'nonnegative seed elastic energy required; this is not a PSD spectrum proof')
    for row, force in zip(snapshot.groups, group_forces, strict=True):
        quadratic, travel = group_energy(row, force)
        energy[row['kind']] += quadratic
        clearance += travel
        ports.append({'row': row, 'force': np.asarray(force), 'max_stiffness': max(row['ka'], row['kl'])})
    for row, force in zip(snapshot.contacts, normal, strict=True):
        energy[row['kind']] += contact_energy(row, float(force))
        ports.append({'row': row, 'force': np.asarray([float(force)]), 'max_stiffness': row['stiffness']})
    enabled = [r for r in snapshot.tangents if r['first'] in {'lumber_leg_left', 'lumber_leg_right'}]
    current.require(len(enabled) == 4 and len(snapshot.tangents) == 16
                    and all(r['kind'] == 'floor_tangent' for r in enabled), 'two original rear-leg XY restraints required')
    for row in enabled:
        f = row['stiffness']*float((row['B']@q)[0])
        energy[row['kind']] += .5*f*f/row['stiffness']
        ports.append({'row': row, 'force': np.asarray([f]), 'max_stiffness': row['stiffness']})
    quadratic = math.fsum(energy.values())
    complement = quadratic+clearance
    corrected_load = snapshot.applied+gradient
    work_error = float(q@corrected_load)-(2.*quadratic+clearance)
    conjugacy_error = complement-(-potential+float(q@gradient))
    current.require(abs(work_error) <= inputs['identity_tolerance_nmm']
                    and abs(conjugacy_error) <= inputs['identity_tolerance_nmm'], 'independent work/conjugacy identities required')
    variable = math.fsum(value for kind, value in energy.items() if kind not in FIXED_KINDS)
    return {'binding': {key: binding[key] for key in ('case_id', 'state_id', 'field')},
            'quadratic_energy_by_kind_nmm': dict(energy), 'quadratic_complementary_energy_nmm': quadratic,
            'radial_clearance_complementary_energy_nmm': clearance, 'complementary_energy_nmm': complement,
            'variable_quadratic_energy_nmm': variable, 'fresh_potential_nmm': potential,
            'work_identity_error_nmm': work_error, 'conjugacy_identity_error_nmm': conjugacy_error,
            'original_load_canonical_sha256': canonical_sha(snapshot.applied.tolist()),
            'dual_feasible_load_canonical_sha256': canonical_sha(corrected_load.tolist()),
            'dual_load_correction_canonical_sha256': canonical_sha(gradient.tolist()),
            'dual_load_correction_inf_n': float(abs(gradient).max()),
            'dual_load_correction_l2_n': float(np.linalg.norm(gradient)),
            'elastic_K_relative_symmetry_error': symmetry_error/float(abs(k.data).max()),
            'spring_port_count': len(ports), 'original_load_is_exactly_dual_feasible': bool(np.all(gradient == 0.))}, ports


def scenario(family, seed_data, ports, field, components, inputs):
    alpha, beta = family['alpha'], family['beta']
    gap = gap_factor(alpha, beta)*(seed_data['variable_quadratic_energy_nmm']+inputs['energy_padding_nmm'])
    worsts = {}
    bearings, captures = defaultdict(list), {}
    source_actions = {r['id']: r for r in field['common_shaft_bearing_actions']}
    current.require(len(source_actions) == 416 and all(r['case_id'] == field['case_id']
                    and r['state_id'] == field['state_id'] for r in source_actions.values()),
                    'all own current saved bearing actions required')
    for port in ports:
        row = port['row']
        own_beta = 1. if row['kind'] in FIXED_KINDS else beta
        delta = perturbation_bound(gap, own_beta*port['max_stiffness'])
        old = float(np.linalg.norm(port['force']))
        item = {'id': row['id'], 'old_force_norm_n': old, 'force_change_norm_upper_n': delta,
                'force_norm_upper_n': old+delta, 'own_stiffness_upper_n_mm': own_beta*port['max_stiffness']}
        if row['kind'] not in worsts or item['force_norm_upper_n'] > worsts[row['kind']]['force_norm_upper_n']:
            worsts[row['kind']] = item
        if row['kind'] == 'common_shaft_bearing' and row['surface']['kind'] == 'wood':
            bearings[(row['axis_id'], row['surface_index'])].append({**port, 'source_action': source_actions[row['id']]})
        elif row['kind'] == 'shaft_end_capture':
            captures[row['id']] = item
    shafts = {r['axis_id']: r for r in field['source_inputs']['shafts']}
    current.require(len(shafts) == 100 and len(bearings) == 120 and len(captures) == 200,
                    'all 100 axes, 120 wood-bearing surfaces and 200 captures required')
    wood = [wood_surface(rows[0]['row'], shafts[axis], rows, gap, beta)
            for (axis, _), rows in sorted(bearings.items())]
    ends = {r['id']: r for r in field['shaft_end_capture_actions']}
    washer_rows = [r for r in components['findings']['washers']['all200_own_end_diagnostics'] if r['receiver_kind'] == 'wood']
    current.require(len(washer_rows) == 112, '112 own wood-land references required')
    land_bounds = []
    for row in washer_rows:
        key = row['capture_id']
        geometry = intake_source.seat_geometry(row, ends[key])
        current.require(abs(captures[key]['old_force_norm_n']-row['N_n']) <= inputs['saved_force_tolerance_n'],
                        'own saved capture/washer force join required')
        force = captures[key]['force_norm_upper_n']
        area = geometry['least_profile_ring_area_mm2']
        index = force/(area*inputs['wood_land_reference_mpa'])
        land_bounds.append({'capture_id': key, 'axis_id': row['axis_id'], 'host': row['host'],
                            'force_upper_n': force, 'least_catalog_profile_area_mm2': area,
                            'conditional_mean_pressure_reference_upper_index': index,
                            'upper_index_exceedance_is_actual_force_or_failure': False})
    return {**family, 'fenchel_gap_upper_nmm': gap, 'spring_port_bounds_count': len(ports),
            'worst_force_enclosure_by_kind': worsts, 'wood_bearing_enclosures': wood,
            'wood_land_mean_reference_enclosures': land_bounds,
            'wood_land_upper_index_above_one_count': sum(r['conditional_mean_pressure_reference_upper_index'] > 1. for r in land_bounds),
            'worst_wood_land_upper_index': max(r['conditional_mean_pressure_reference_upper_index'] for r in land_bounds),
            'complete_resistance_certificate_established': False}


def run():
    input_ref = current.ref(INPUT)
    inputs = current.read(input_ref)
    validate(inputs)
    runtime = {name: importlib.metadata.version(name) for name in inputs['runtime_versions']}
    current.require(runtime == inputs['runtime_versions'], 'declared reaction-bound runtime required')
    cases, pins = intake_source.intake()
    frozen = current.load('bridge').frozen()
    refs = [input_ref, current.ref(OWN), current.ref(current.ROOT/'tests/test_eoere_reaction_energy_bounds.py'),
            current.ref(Path(frozen.bundle.__file__)), current.ref(Path(frozen.law.__file__)), *inputs['references']]
    pins = current.join(pins, {r['path']: r['sha256'] for r in refs})
    current.verify(pins)
    outputs = []
    for binding, field, components in cases:
        snapshot = frozen.bundle.read_snapshot(field['operator_bundle'])
        data, ports = seed(binding, field, snapshot, frozen, inputs)
        outputs.append({**data, 'families': [scenario(f, data, ports, field, components, inputs)
                                            for f in inputs['stiffness_families']]})
    current.verify(pins)
    current.require(current.sha(OWN) == LOADED_SHA, 'loaded reaction-bound producer changed')
    return {'schema': 'eoere_current_reaction_energy_bounds/v1',
            'status': 'COMPLETE_DECLARED_FAMILY_REACTION_ENCLOSURES_NO_PHYSICAL_QUALIFICATION',
            'producer': current.ref(OWN), 'inputs': input_ref, 'source_sha256': pins,
            'all_sources_unchanged': True, 'runtime_versions': runtime,
            'geometry_revision': inputs['geometry_revision'], 'hardware_revision': inputs['hardware_revision'],
            'current_bolt_count': 100, 'current_screw_count': 66, 'extra_grid': False, 'cases': outputs,
            'case_count': len(outputs), 'stiffness_family_case_comparisons': 3*len(outputs),
            'spring_port_enclosures': sum(f['spring_port_bounds_count'] for r in outputs for f in r['families']),
            'wood_bearing_enclosures': sum(len(f['wood_bearing_enclosures']) for r in outputs for f in r['families']),
            'wood_land_reference_enclosures': sum(len(f['wood_land_mean_reference_enclosures']) for r in outputs for f in r['families']),
            'bounds_allow_radial_and_normal_contact_switches': True,
            'bounds_apply_to_original_exact_loads': False, 'physical_demand_bounds_established': False,
            'finite_geometry_or_directional_restraint_qualified': False, 'core_PSD_independently_certified': False,
            'complete_joint_resistance': None, 'finished_member_capacity': None, 'actual_observations': None,
            'frame_native_elastic_solve_CAD_or_geometry_change': False, 'structural_acceptance': False,
            'primary_source_urls': inputs['primary_source_urls'], 'limits': inputs['assumptions']}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    with current.load('bridge').reserve(args.out) as output:
        output.write(run())
    print(current.ref(args.out))


if __name__ == '__main__':
    main()
