"""Apply a one-sided volume-strength bound to authenticated saved cleat trials.

This performs no response solve. Floating arithmetic selects one trial; exact
rational work and Bernstein support bounds certify only that selected trial.
The saved nodal force cloud is an additional load-functional hypothesis.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
from collections import Counter
from fractions import Fraction as F
from functools import lru_cache
from itertools import product
from pathlib import Path

import numpy as np

from fea.wood_joint_reduced_members import shape20_derivatives
from scripts import eoere_cleat_finite_body as model
from scripts import eoere_cleat_virtual_work as vw
from scripts.eoere_mixed_continuous_bound import read_exact

current = model.current
OWN = Path(__file__).resolve()
LOADED_SHA = current.sha(OWN)
INPUT = current.DOC/'selected-hardware-v1/current-response-v1/joint-closure-v1/cleat-volume-work-inputs-v1.json'
MEMBERS = ('eoere_cleat_left', 'eoere_cleat_right')


def validate(inputs):
    vw.require(inputs['schema'] == 'eoere_current_cleat_volume_work_inputs/v1'
               and inputs['geometry_revision'] == 'eoere-raised-kicker-screws-v1'
               and inputs['hardware_revision'] == 'eoere-selected-purchase-hardware-v1'
               and inputs['current_bolt_count'] == 100 and inputs['current_screw_count'] == 66
               and inputs['extra_grid'] is False and inputs['actual_observations'] is None
               and inputs['structural_acceptance'] is False and inputs['physical_failure_established'] is False
               and inputs['complete_cleat_resistance'] is None, 'unchanged conditional retained scope required')
    vw.require({k: F(v) for k, v in inputs['base_strengths_mpa'].items()} == vw.BASE_STRENGTHS
               and inputs['uniform_strength_divisors'] == ['1.5', '2', '3']
               and inputs['working_strength_divisor'] == '2' and inputs['load_factors'] == ['1', '1.5']
               and inputs['load_functional'] == 'L(v)=saved_F_dot_v_on_the_compatible_virtual_space'
               and inputs['trial_rule'] == 'all_48_intact_saved_U_columns_zeroed_outside_sound_free_nodes'
               and inputs['selected_certificate_rule'] == 'largest_positive_work_over_float_Bernstein_upper_at_divisor_2'
               and inputs['source_configuration_index'] == 0, 'predeclared strength, work and selection hypotheses required')
    vw.require(inputs['runtime_versions'] == {'numpy': '2.5.2', 'scipy': '1.18.1'}, 'pinned numerical runtime required')
    vw.require(inputs['volume_helper'] == current.ref(vw.OWN) and vw.LOADED_SHA == inputs['volume_helper']['sha256'],
               'loaded exact helper changed')


def check_saved(job, fields):
    vw.require(job['schema'] == 'eoere_current_refined_fixed_action_finite_crack_comparisons/v1'
               and job['status'] == 'CURRENT_DECLARED_FINER_GRID_BORE_FLAW_COMPARISONS_COMPLETE_LOCAL_MODEL_ONLY'
               and job['job'] == {'mesh_size_mm': 7.5, 'plane_mm': -25.4, 'swap_RT': False}
               and job['geometry_revision'] == 'eoere-raised-kicker-screws-v1'
               and job['hardware_revision'] == 'eoere-selected-purchase-hardware-v1'
               and job['current_bolt_count'] == 100 and job['current_screw_count'] == 66
               and job['extra_grid'] is False and job['structural_acceptance'] is False
               and job['actual_observations'] is None and set(job['geometry']) == set(MEMBERS),
               'own complete unchanged fine-grid source required')
    config = job['configurations'][0]
    vw.require(config['index'] == 0 and config['interval'] is None and len(config['labels']) == 48,
               'complete intact 48-column source required')
    labels = config['labels']
    vw.require(len({(r['case_id'], r['member'], r['radius_increment_mm'], r['coincident_point_side']) for r in labels}) == 48
               and len(job['records']) == 12, 'own six-case two-member cloud census required')
    for label in labels:
        matches = [r for r in job['records'] if all(r[k] == label[k] for k in ('case_id', 'member', 'field', 'state_id'))]
        vw.require(len(matches) == 1 and label['radius_increment_mm'] in (15., 30.)
                   and label['coincident_point_side'] in (-1, 1), 'label must match its own authenticated record')
    nodes, elements, force, displacement = (fields[k] for k in ('nodes', 'elements', 'F', 'U'))
    vw.require(nodes.dtype == np.float64 and nodes.ndim == 2 and nodes.shape[1] == 3
               and elements.ndim == 2 and elements.shape[1] == 20 and elements.dtype.kind in 'iu'
               and force.dtype == displacement.dtype == np.float64
               and force.shape == displacement.shape == (3*len(nodes), 48)
               and min(elements.flat) >= 0 and max(elements.flat) < len(nodes)
               and all(np.isfinite(a).all() for a in (nodes, force, displacement)),
               'finite complete own stored binary arrays required')
    return nodes, elements, force, displacement, labels


def sound_submesh(nodes, elements, geometry):
    selected, boxes, reasons = [], [], Counter()
    for element in elements:
        try:
            mapped = vw.separable_geometry(nodes[element])
        except ValueError as error:
            vw.require(str(error) == 'nonseparable stored geometry requires another map', str(error))
            selected.append(False)
            reasons['nonseparable_stored_map'] += 1
            continue
        safe = vw.sound_box(mapped['boxes'], geometry)
        selected.append(safe)
        if safe:
            boxes.append(mapped['boxes'])
        else:
            reasons['profile_or_bore_intersection'] += 1
    # For this tensor-grid source, consecutive exact coordinate intervals and
    # distinct occupied boxes certify no positive-volume overlap of trial cells.
    cuts = [sorted({v for box in boxes for v in box[axis]}) for axis in range(3)]
    positions = [{v: i for i, v in enumerate(axis)} for axis in cuts]
    occupied = set()
    for box in boxes:
        key = tuple(positions[i][bounds[0]] for i, bounds in enumerate(box))
        vw.require(all(positions[i][bounds[1]] == key[i]+1 for i, bounds in enumerate(box))
                   and key not in occupied, 'nonoverlapping conforming tensor boxes required')
        occupied.add(key)
    free, boundary = vw.support_nodes(elements, selected)
    vw.require(free and boxes, 'nonempty sound compatible virtual space required')
    return np.asarray(selected, dtype=bool), free, {'selected_elements': int(sum(selected)),
        'excluded_element_reasons': dict(reasons), 'free_nodes': len(free), 'boundary_nodes': len(boundary),
        'exact_nonoverlapping_box_count': len(occupied)}


@lru_cache(maxsize=1)
def float_selection_basis():
    points = np.asarray(list(product(np.linspace(-1., 1., 4), repeat=3)))
    derivatives = np.asarray([shape20_derivatives(p) for p in points])
    t = np.linspace(0., 1., 4)
    basis = np.asarray([[vw.math.comb(3, j)*x**j*(1-x)**(3-j) for j in range(4)] for x in t])
    inverse = np.linalg.inv(basis)
    for array in (points, derivatives, inverse):
        array.setflags(write=False)
    return points, derivatives, inverse


def float_element_upper(positions, virtual):
    """Candidate selection only; exact certificate never uses these numbers."""
    points, derivatives, inverse = float_selection_basis()
    geometry = vw.separable_geometry(positions)
    jacobians = np.asarray([float(p[vw.ZERO]) + float(p.get(tuple(int(j == i) for j in range(3)), 0))*points[:, i]
                           for i, p in enumerate(geometry['jacobians'])]).T
    cofactors = np.prod(jacobians, axis=1)[:, None]/jacobians
    gradient = np.einsum('ick,gid,gd->gcdk', virtual, derivatives, cofactors, optimize=True)
    strain = np.stack([gradient[:, 0, 0], gradient[:, 1, 1], gradient[:, 2, 2],
                       gradient[:, 0, 1]+gradient[:, 1, 0], gradient[:, 0, 2]+gradient[:, 2, 0],
                       gradient[:, 1, 2]+gradient[:, 2, 1]], axis=1)
    coefficients = np.einsum('ai,bj,ck,ijkdp->abcdp', inverse, inverse, inverse,
                             strain.reshape(4, 4, 4, 6, -1), optimize=True).reshape(64, 6, -1)
    s = vw.BASE_STRENGTHS
    values = [coefficients[:, 0]*float(s['tension_parallel']), -coefficients[:, 0]*float(s['compression_parallel'])]
    for component in (1, 2):
        values.extend([coefficients[:, component]*float(s['tension_perpendicular']),
                       -coefficients[:, component]*float(s['compression_perpendicular'])])
    values.extend([abs(coefficients[:, 3])*float(s['parallel_shear']), abs(coefficients[:, 4])*float(s['parallel_shear']),
                   abs(coefficients[:, 5])*float(s['rolling_shear'])])
    return np.max(values, axis=0).sum(axis=0)/8


def select_trial(nodes, elements, force, displacement, labels, masks):
    trials = np.zeros_like(displacement).reshape(len(nodes), 3, 48)
    views = displacement.reshape(len(nodes), 3, 48)
    for col, label in enumerate(labels):
        _, free, _ = masks[label['member']]
        trials[free, :, col] = views[free, :, col]
    work = np.sum(force*trials.reshape(force.shape), axis=0)
    signs = np.where(work < 0, -1., 1.)
    trials *= signs[None, None, :]
    upper = np.zeros(48)
    for index, element in enumerate(elements):
        active = [col for col, label in enumerate(labels) if masks[label['member']][0][index]]
        if active:
            upper[active] += float_element_upper(nodes[element], trials[element][:, :, active])
    vw.require(np.isfinite(upper).all() and np.isfinite(work).all() and (upper > 0).all(),
               'finite nonzero floating candidate support required')
    indices = 2*abs(work)/upper
    chosen = int(np.argmax(indices))
    vw.require(abs(work[chosen]) > 0, 'positive useful virtual work required before exact integration')
    rows = [{**label, 'column': i, 'orientation': int(signs[i]), 'float_work_nmm': float(abs(work[i])),
             'float_base_support_upper_nmm': float(upper[i]), 'float_working_necessary_index': float(indices[i]),
             'certified_result': False} for i, label in enumerate(labels)]
    return chosen, trials[:, :, chosen].copy(), rows


def exact_certificate(nodes, elements, force, virtual, selected):
    exact_work = sum((vw.number(float(f))*vw.number(float(v)) for f, v in
                      zip(force, virtual.reshape(-1), strict=True) if f and v), F(0))
    vw.require(exact_work > 0, 'exact selected work must remain positive')
    lower, upper, active = F(0), F(0), 0
    for index, (element, chosen) in enumerate(zip(elements, selected, strict=True)):
        if chosen and np.any(virtual[element]):
            bounds = vw.element_bound(nodes[element], virtual[element], vw.BASE_STRENGTHS)
            lower += bounds['lower']
            upper += bounds['upper']
            active += 1
        elif not chosen:
            vw.require(not np.any(virtual[element]), 'virtual field must vanish on every excluded cell')
        if (index+1) % 250 == 0:
            print(json.dumps({'exact_elements_checked': index+1, 'total_elements': len(elements)}), flush=True)
    vw.require(upper >= lower > 0, 'positive exact support enclosure required')
    return {'exact_work_nmm': str(exact_work), 'exact_base_support_lower_nmm': str(lower),
            'exact_base_support_upper_nmm': str(upper), 'nonzero_selected_elements': active,
            'virtual_binary64_sha256': hashlib.sha256(np.ascontiguousarray(virtual).tobytes()).hexdigest()}


def verify_sources(pins, inputs):
    vw.require(current.sha(OWN) == LOADED_SHA and current.sha(vw.OWN) == vw.LOADED_SHA,
               'loaded volume-work producer/helper changed')
    vw.require({k: importlib.metadata.version(k) for k in inputs['runtime_versions']} == inputs['runtime_versions'],
               'numerical runtime changed')
    model.verify_execution_sources(pins)


def run():
    input_ref = current.ref(INPUT)
    inputs = read_exact(input_ref)
    validate(inputs)
    job = read_exact(inputs['source_job'])
    field_ref = job['configurations'][0]['field']
    refs = [input_ref, inputs['source_job'], field_ref, inputs['material_source'], inputs['volume_helper'],
            *inputs['execution_sources'],
            current.ref(OWN), current.ref(current.ROOT/'tests/test_eoere_cleat_virtual_work.py'),
            current.ref(current.ROOT/'tests/test_eoere_cleat_virtual_work_audit.py'),
            current.ref(current.ROOT/'scripts/eoere_mixed_continuous_bound.py')]
    pins = current.join(job['source_sha256'], {r['path']: r['sha256'] for r in refs})
    verify_sources(pins, inputs)
    with model.read_array_file(field_ref) as fields:
        nodes, elements, force, displacement, labels = check_saved(job, fields)
    masks = {member: sound_submesh(nodes, elements, job['geometry'][member]) for member in MEMBERS}
    chosen, virtual, screening = select_trial(nodes, elements, force, displacement, labels, masks)
    print(json.dumps({'chosen_column': chosen, 'float_working_index': screening[chosen]['float_working_necessary_index']}), flush=True)
    selected = masks[labels[chosen]['member']][0]
    exact = exact_certificate(nodes, elements, force[:, chosen], virtual, selected)
    rows = []
    for divisor, factor in product(inputs['uniform_strength_divisors'], inputs['load_factors']):
        index = F(divisor)*F(factor)*vw.necessary_index(F(exact['exact_work_nmm']), F(exact['exact_base_support_upper_nmm']))
        rows.append({'strength_divisor': divisor, 'load_factor': factor, 'exact_necessary_index_lower': str(index),
                     'necessary_index_lower': float(index), 'declared_nodal_work_strength_model_impossible': index > 1,
                     'value_at_or_below_one_establishes_feasibility': False})
    verify_sources(pins, inputs)
    return {'schema': 'eoere_current_cleat_volume_work_bound/v1', 'status': 'SELECTED_COMPATIBLE_TRIAL_NECESSARY_BOUND_COMPLETE',
            'inputs': input_ref, 'source_sha256': pins, 'source_job': inputs['source_job'], 'source_field': field_ref,
            'all_sources_unchanged': True, 'geometry_revision': inputs['geometry_revision'],
            'hardware_revision': inputs['hardware_revision'], 'current_bolt_count': 100, 'current_screw_count': 66,
            'extra_grid': False, 'actual_observations': None, 'structural_acceptance': False,
            'physical_demand_bounds_established': False, 'physical_failure_established': False,
            'complete_cleat_resistance': None, 'new_response_or_frame_or_native_solve_performed': False,
            'runtime_versions': inputs['runtime_versions'], 'submeshes': {k: value[2] for k, value in masks.items()},
            'floating_trial_selection': screening, 'chosen_trial': screening[chosen], 'exact_certificate': exact,
            'necessary_comparisons': rows, 'load_functional': inputs['load_functional'], 'limits': inputs['assumptions']}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    with current.load('bridge').reserve(args.out) as output:
        output.write(run())
    print(json.dumps(current.ref(args.out)))


if __name__ == '__main__':
    main()
