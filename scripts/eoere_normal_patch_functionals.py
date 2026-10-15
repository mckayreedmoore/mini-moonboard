"""Use exact owner equilibrium to sharpen continuous-model leg reactions.

Change only the reported scalar functional. Reuse the frozen primal/dual gap,
model and load certificates; compute no response or matrix inverse.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import io
import json
import platform
from fractions import Fraction as F
from pathlib import Path
from types import ModuleType

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
OWN = Path(__file__).resolve()
LOADED_SHA = hashlib.sha256(OWN.read_bytes()).hexdigest()
BASE = {'path': 'scripts/eoere_normal_patch_reactions.py',
        'sha256': '2453ea37c5b6f36db193518ebf0e42cc09dc33d9ffc9f2e1d2f69854ed9fc3cd'}


def require(ok, message):
    if not ok:
        raise ValueError(message)


def producer(pins):
    """Bind executed bootstrap helpers to verified bytes, ignoring caches."""
    path = ROOT/BASE['path']; data = path.read_bytes()
    digest = hashlib.sha256(data).hexdigest()
    require(digest == BASE['sha256'] and pins.get(BASE['path'], digest) == digest,
            'preserved functional base source changed')
    pins[BASE['path']] = digest
    module = ModuleType('_eoere_verified_functional_base')
    module.__file__ = str(path)
    exec(compile(data, str(path), 'exec'), module.__dict__)  # noqa: S102 - verified frozen buffer
    return module


def check_runtime(expected):
    actual = {'python': platform.python_version(), 'numpy': np.__version__,
              'scipy': importlib.metadata.version('scipy')}
    require(expected == actual, 'inherited exact functional runtime required')
    return actual


def equivalent(target, action, multiplier):
    """l*r = a*p + (l-a*D)*r when D*r=p in a kernel direction."""
    target, action = [list(map(F, row)) for row in (target, action)]
    multiplier = F(multiplier)
    require(len(target) == len(action) > 0, 'same nonempty scalar order required')
    return [l-multiplier*d for l, d in zip(target, action, strict=True)]


def shifted_scalar(offset, coefficients, candidate, radius, stiffness, gap, audit):
    """Reuse the exact signed scalar enclosure; preserve a signed offset."""
    offset, gap = F(offset), F(gap)
    candidate, radius, stiffness = [list(map(F, values)) for values in (candidate, radius, stiffness)]
    n = len(candidate)
    require(n > 0 and len(radius) == len(stiffness) == n and min(radius) >= 0 and min(stiffness) > 0,
            'complete positive scalar metric and nonnegative correction box required')
    require(gap >= 0, 'nonnegative gap required')
    require(all(type(j) is int and 0 <= j < n for j in coefficients), 'bounded nonnegative integer scalar indices required')
    coefficients = {j: F(v) for j, v in coefficients.items() if F(v)}
    enclosure = audit.functional([coefficients], candidate, radius, stiffness, gap)
    center = offset+F(enclosure['exact_candidate_center'][0])
    correction = F(enclosure['exact_dual_correction_norm_upper'])
    movement = F(enclosure['exact_equilibrium_change_norm_upper'])
    lower, upper = center-correction-movement, center+correction+movement
    require(lower == offset+F(enclosure['exact_scalar_lower']), 'same signed scalar interval required')
    return {'exact_offset_n': str(offset), 'exact_center_n': str(center),
            'exact_signed_lower_n': str(lower), 'exact_upper_n': str(upper),
            'signed_lower_n': float(lower), 'upper_n': float(upper),
            'strict_positive_normal_resultant_certified': lower > 0,
            'unchanged_metric_enclosure': enclosure}


def run(reference):
    pins = {}; base = producer(pins)
    inputs = json.loads(base.captured(reference, pins))
    require(inputs['schema'] == 'eoere_continuous_normal_equilibrium_functional_inputs/v1'
            and inputs['geometry_revision'] == 'eoere-raised-kicker-screws-v1'
            and inputs['hardware_revision'] == 'eoere-selected-purchase-hardware-v1'
            and inputs['current_bolt_count'] == 100 and inputs['current_screw_count'] == 66
            and inputs['extra_grid'] is False and inputs['actual_observations'] is None
            and inputs['structural_acceptance'] is False, 'retained functional-only scope required')
    for source in inputs['execution_sources']:
        base.captured(source, pins)
    require(pins.get(str(OWN.relative_to(ROOT))) == LOADED_SHA
            and pins.get(str(base.OWN.relative_to(ROOT))) == base.LOADED_SHA,
            'exact executing functional consumer and base helper required')
    source = json.loads(base.captured(inputs['reaction_result'], pins))
    require(source['schema'] == 'eoere_continuous_normal_support_refinement/v1'
            and source['all_six_exact_original_load_dual_bounds_proven'] is True
            and source['continuous_normal_law_or_original_load_changed'] is False,
            'completed unchanged-law continuous-model gap certificate required')
    for path, digest in source['source_sha256'].items():
        base.captured({'path': path, 'sha256': digest}, pins)
    source_inputs = json.loads(base.captured(source['inputs'], pins))
    runtime = check_runtime(source_inputs['runtime'])
    h = base.prepare(source_inputs, pins)
    response = json.loads(base.captured(h.trace_inputs['current_response'], pins))
    previous = json.loads(base.captured(source_inputs['original_bounds'], pins))
    old = json.loads(base.captured(h.prior_inputs['recession_result'], pins))
    core = json.loads(base.captured(h.prior_inputs['core_result'], pins))
    require(core['constructed_comparator_core_PSD_and_exact_registered_kernel_proven'] is True
            and len(response['cases']) == len(source['cases']) == len(previous['cases']) == 6,
            'same certified core and six current cases required')
    selected = set(old['shared_minor_columns'])
    result, common_maps, common_rows = [], None, None
    for binding, bound, prior in zip(response['cases'], source['cases'], previous['cases'], strict=True):
        require(bound['binding'] == prior['binding'] == {k: binding[k] for k in ('case_id', 'state_id', 'field')},
                'own retained load and response binding required')
        field = json.loads(base.captured(binding['field'], pins))
        pointer = field['operator_bundle']
        require(pointer == bound['operator_bundle'] == prior['operator_bundle'], 'own original operators required')
        manifest = json.loads(base.captured(pointer['manifest'], pins)); data = base.captured(pointer['arrays'], pins)
        with np.load(io.BytesIO(data), allow_pickle=False) as arrays:
            maps, owners, bodies, dimension = h.reader.rigid_basis(manifest['coordinate_map'], arrays[manifest['rigid_modes_key']])
            parts = h.transfer.partitions(manifest, arrays)
            enabled = {r['id'] for r in parts['tangents']} & set(old['shared_constraint_identities'])
            components, ports, bilateral = h.audit.register(parts, field, enabled)
            require(dimension == 800 and len(maps) == len(owners) == 9350 and bilateral == 968
                    and len(ports) == 2324 and [r['id'] for r in components] == previous['scalar_component_identities'],
                    'complete unchanged source registration required')
            rows = [r['row'] for r in components]
            if common_maps is None:
                common_maps, common_rows = maps, rows
            else:
                require(maps == common_maps and rows == common_rows, 'same source maps and scalar order across cases required')
            load = h.core.action(h.core.transpose(maps, dimension), list(map(F, arrays[manifest['applied_key']])))
            digest = hashlib.sha256(json.dumps(list(map(str, load)), separators=(',', ':')).encode()).hexdigest()
            require(digest == bound['exact_original_rigid_load_sha256'] == prior['exact_original_rigid_load_sha256'],
                    'same exact original registered load required')
            candidate = list(map(F, prior['candidate_auxiliary_weights']))
            error = F(bound['exact_new_correction_inf_n'])
            radius = [error if j in selected else F(0) for j in range(len(components))]
            stiffness = [r['stiffness'] for r in components]
            gap = F(bound['exact_total_Fenchel_gap_upper_nmm'])
            legs = []
            for name in ('lumber_leg_left', 'lumber_leg_right'):
                body, = [r for r in bodies if r['body'] == name]
                require(body['source_mode_columns'] == [0, 1, 2, 3, 4, 5], 'own registered XYZ/rotation order required')
                column = body['first_rigid_column']+2
                # No continuous bed uses this owner: its point-map derivative
                # vanishes everywhere, not merely at auxiliary support means.
                require(all(name not in (p['first'], p['second']) for p in field['source_inputs']['flange_shared_face_patches'])
                        and all(not F(r['exact_rigid_compression_row'].get(str(column), '0'))
                                for r in source['shared_material_support_records']),
                        'complete continuous normal derivative must vanish for this owner direction')
                direction = [row.get(column, F(0)) for row in maps]
                require(all(not v or owners[i] == name for i, v in enumerate(direction)), 'owner-isolated kernel direction required')
                action = h.core.action(rows, direction)
                own = [p for p in ports if p['descriptor']['kind'] == 'floor_normal' and p['descriptor']['first'] == name]
                require(len(own) == 4 and all(p['descriptor']['direction_xyz'] == [0., 0., 1.] for p in own),
                        'four own upward floor normals required')
                js = {p['columns'][0] for p in own}
                require(len(js) == 4 and all(action[j] == -1 for j in js), 'exact downward-compression translation sign required')
                target = [F(int(j in js)) for j in range(len(components))]
                coefficients = equivalent(target, action, -1)
                sparse = {j: v for j, v in enumerate(coefficients) if v}
                require(sparse and all(components[j]['kind'] == 'common_shaft_bearing' for j in sparse),
                        'this equivalent leg functional must use unchanged bearing laws only')
                enclosure = shifted_scalar(-load[column], sparse, candidate, radius, stiffness, gap, h.audit)
                legs.append({'body': name, 'registered_translation_column': column,
                             'exact_multiplier': '-1', 'exact_registered_load_component_n': str(load[column]),
                             'equivalent_scalar_coefficients': {components[j]['id']: str(v) for j, v in sparse.items()},
                             'nonnegative_normal_lower_n': str(max(F(0), F(enclosure['exact_signed_lower_n']))),
                             'normal_resultant': enclosure})
            result.append({'binding': bound['binding'], 'operator_bundle': pointer,
                           'exact_original_rigid_load_sha256': digest,
                           'exact_reused_total_Fenchel_gap_upper_nmm': str(gap), 'legs': legs})
    for path, digest in tuple(pins.items()):
        base.captured({'path': path, 'sha256': digest}, pins)
    return {'schema': 'eoere_continuous_normal_equilibrium_functionals/v1', 'inputs': reference,
            'runtime': runtime,
            'source_sha256': pins, 'reaction_result': inputs['reaction_result'], 'cases': result,
            'geometry_revision': inputs['geometry_revision'], 'hardware_revision': inputs['hardware_revision'],
            'current_bolt_count': 100, 'current_screw_count': 66, 'extra_grid': False,
            'positive_leg_resultants_certified': sum(r['normal_resultant']['strict_positive_normal_resultant_certified'] for c in result for r in c['legs']),
            'continuous_law_core_loads_gap_or_geometry_changed': False,
            'new_solve_optimization_inverse_factorization_or_response': False,
            'physical_stiffness_demand_restraint_or_complete_resistance_qualified': False,
            'panel_screw_exceedances_deferred': True, 'actual_observations': None, 'structural_acceptance': False,
            'limits': inputs['limits']}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--inputs', type=Path, required=True); parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    require(not args.out.exists(), 'preserve issued equilibrium-functional evidence')
    reference = {'path': str(args.inputs.resolve().relative_to(ROOT)), 'sha256': hashlib.sha256(args.inputs.read_bytes()).hexdigest()}
    result = run(reference)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open('x') as stream:
        stream.write(json.dumps(result, indent=2, sort_keys=True, allow_nan=False)+'\n')
    print(json.dumps({'path': str(args.out), 'bytes': args.out.stat().st_size,
                      'sha256': hashlib.sha256(args.out.read_bytes()).hexdigest(),
                      'positive_leg_resultants_certified': result['positive_leg_resultants_certified']}))


if __name__ == '__main__':
    main()
