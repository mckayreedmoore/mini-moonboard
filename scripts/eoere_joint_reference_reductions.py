"""Evaluate saved current mixed-stack fields under explicit reduced references.

The uniform reduction is an engineering hypothesis motivated by the NDS mode
range, not an established ASD conversion for general member forces/couples.
No LP, frame, elastic or native solve, CAD query or design change occurs.
"""
from __future__ import annotations

import argparse
import importlib.metadata
import math
import sys
import sysconfig
from pathlib import Path

import numpy as np

from scripts import eoere_current_washer_lands as intake_source
from scripts import eoere_joint_vector_tests as vector

current = vector.current
OWN = Path(__file__).resolve()
LOADED_SHA = current.sha(OWN)
INPUT = current.DOC/'selected-hardware-v1/current-response-v1/joint-closure-v1/mixed-uniform-material-reduction-inputs-v1.json'
VERIFICATION = {
    'path': 'fea/generated/selected-hardware-followup-v1/engineering-closure-v1/current-joint-vector-tests-attempt05-verification.json',
    'sha256': 'f301d89a0f0d5396e53f7679b13ef3fbaee2a454ed444d838bbe0c712f45fe16',
}


def validate(inputs):
    current.require(inputs['schema'] == 'eoere_current_mixed_uniform_material_reduction_inputs/v1'
                    and inputs['geometry_revision'] == 'eoere-raised-kicker-screws-v1'
                    and inputs['hardware_revision'] == 'eoere-selected-purchase-hardware-v1'
                    and inputs['extra_grid'] is False and inputs['current_bolt_count'] == 100
                    and inputs['current_screw_count'] == 66 and inputs['actual_observations'] is None
                    and inputs['structural_acceptance'] is False and inputs['physical_or_structural_release'] is False,
                    'unchanged current unobserved design and false acceptance required')
    current.require(inputs['uniform_reference_divisors'] == [3.2, 4., 5.]
                    and inputs['working_uniform_reference_divisor'] == 5., 'declared three-scenario reduction scope required')


def reduction_range(helper, diameters_in, nominal_in):
    """Endpoint evaluation is exact for the table's positive affine Ktheta."""
    current.require(diameters_in and all(math.isfinite(d) and .25 <= d <= 1. for d in diameters_in)
                    and math.isfinite(nominal_in) and max(diameters_in) <= nominal_in <= 1.,
                    'complete body/root diameter range must lie in the declared NDS table branch')
    values = [helper._reduction_terms(diameter_in=d, nominal_diameter_in=nominal_in,
                                     angle_max_degrees=theta) for d in diameters_in for theta in (0., 90.)]
    current.require(all(set(v) == {'Im', 'Is', 'II', 'IIIm', 'IIIs', 'IV'} for v in values),
                    'all six source mode terms required')
    low, high = min(min(v.values()) for v in values), max(max(v.values()) for v in values)
    current.require(low == 3.2 and high == 5., 'source table endpoint range differs from declared hypothesis motivation')
    return {'diameters_in': diameters_in, 'nominal_diameter_in': nominal_in,
            'Ktheta_formula': '1+theta/360 for 0<=theta<=90; positive affine, so endpoints bound the range',
            'source_mode_terms_at_endpoints': values, 'source_mode_reduction_range': [low, high],
            'generalized_mixed_stack_ASD_conversion_established': False}


def compare_saved_field(grid, divisor):
    """Recompute norms, then change reference caps without changing actions."""
    current.require(isinstance(divisor, (int, float)) and not isinstance(divisor, bool)
                    and math.isfinite(divisor) and divisor >= 1., 'finite reference reduction at least one required')
    current.require(grid['physical_compatibility'] is False and grid['complete_joint_resistance'] is None
                    and grid['adjusted_capacity'] is None and grid['cells'] and grid['continuous_segments'],
                    'complete saved raw witness with unchanged claim boundary required')
    bearing = []
    for cell in grid['cells']:
        q = np.asarray(cell['density_yz'], dtype=float)
        cap = cell['cap']
        current.require(q.shape == (2,) and np.isfinite(q).all() and math.isfinite(cap) and cap > 0.
                        and math.isfinite(cell['low']) and math.isfinite(cell['high']) and cell['high'] > cell['low'],
                        'finite vector density, positive reference and cell interval required')
        bearing.append(float(np.linalg.norm(q))/cap)
    bending = []
    for segment in grid['continuous_segments']:
        coefficient = np.asarray(segment['moment_coefficients_unit_interval_nmm'], dtype=float)
        cap = segment['raw_moment_cap']
        current.require(coefficient.shape in ((3, 3), (4, 3)) and np.isfinite(coefficient).all()
                        and (len(coefficient) == 3 or np.count_nonzero(coefficient[3]) == 0)
                        and math.isfinite(cap) and cap > 0., 'finite full moment quadratic and positive cap required')
        peak = vector.spatial.peak_norm(coefficient)
        bending.append(peak['magnitude']/cap)
    raw, b, m = grid['certified_raw_reference_index'], max(bearing), max(bending)
    current.require(np.isfinite([raw, b, m]).all() and raw >= 0.
                    and np.allclose([b, m], [grid['raw_bearing_index'], grid['continuous_raw_bending_index']],
                                    rtol=1e-10, atol=1e-10)
                    and max(b, m) <= raw*(1.+1e-8)+1e-10, 'saved continuous norms or certified reference differ')
    value = raw*divisor
    current.require(math.isfinite(value), 'finite scaled witness reference required')
    return {'uniform_reference_divisor': divisor, 'source_certified_raw_reference_index': raw,
            'uniform_reduced_certified_witness_index': value,
            'uniform_reduced_bearing_index': b*divisor, 'uniform_reduced_continuous_bending_index': m*divisor,
            'saved_witness_exceeds_assumed_reference': value > 1.,
            'complete_joint_resistance': None, 'physical_failure_established': False}


def verify_execution_sources(pins):
    dependencies = {Path(sysconfig.get_path(k)).resolve() for k in ('purelib', 'platlib')}
    for module in tuple(sys.modules.values()):
        path = getattr(module, '__file__', None)
        if not path or not Path(path).is_file():
            continue
        path = Path(path).resolve()
        if path.is_relative_to(current.ROOT) and not any(path.is_relative_to(d) for d in dependencies):
            name = str(path.relative_to(current.ROOT))
            current.require(pins.get(name) == current.sha(path), 'unbound or changed repository execution source: '+name)
    current.verify(pins)


def run():
    input_ref = current.ref(INPUT)
    inputs = current.read(input_ref)
    validate(inputs)
    runtime = {p: importlib.metadata.version(p) for p in ('numpy', 'scipy')}
    current.require(runtime == inputs['runtime_versions'], 'declared numerical dependency versions required')
    cases, pins = intake_source.intake()
    refs = [input_ref, VERIFICATION, current.ref(OWN),
            current.ref(current.ROOT/'tests/test_eoere_joint_reference_reductions.py'), *inputs['references'].values()]
    source = current.read(inputs['references']['vector_fields'])
    verified = current.read(VERIFICATION)
    current.require(source['schema'] == 'eoere_current_representative_vector_joint_tests/v1'
                    and source['geometry_revision'] == inputs['geometry_revision']
                    and source['hardware_revision'] == inputs['hardware_revision'] and source['extra_grid'] is False
                    and source['current_stack_case_count'] == 48 and source['current_statics_trial_count'] == 144
                    and source['case_sequence'] == vector.spatial.SEQUENCE and source['complete_joint_resistance'] is None
                    and source['structural_acceptance'] is False and source['physical_compatibility'] is False
                    and source['producer'] == current.ref(Path(vector.__file__)), 'exact completed current raw vector record required')
    current.require(verified['record'] == inputs['references']['vector_fields'] and verified['producer'] == source['producer']
                    and verified['trial_count'] == 144 and verified['source_pin_count'] == len(source['source_sha256'])
                    and verified['all_original_current_inputs_joined'] is True
                    and verified['all_saved_vector_fields_independently_integrated'] is True
                    and verified['structural_acceptance'] is False, 'complete independent saved-field verification required')
    pins = current.join(pins, source['source_sha256'], {r['path']: r['sha256'] for r in refs})
    verify_execution_sources(pins)
    helper = intake_source.component.load(inputs['references']['NDS_reduction_helper'], 'current_mixed_reference_mode_terms')
    output = []
    for (binding, field, data), saved in zip(cases, source['cases'], strict=True):
        current.require(all(saved[k] == binding[k] for k in ('case_id', 'state_id', 'field', 'admission'))
                        and [s['axis_id'] for s in saved['mixed_stacks']] == vector.spatial.MIXED_IDS,
                        'own current six-case/eight-stack bindings required')
        shafts = {s['axis_id']: s for s in field['source_inputs']['shafts']}
        components = {r['axis_id']: r for r in data['findings']['timber']['shaft_components']}
        for stack in saved['mixed_stacks']:
            aid = stack['axis_id']
            window = components[aid]['thread_window']
            source_range = reduction_range(helper, [window['catalog_min_body_in'], window['purchase_design_root_floor_in']],
                                           shafts[aid]['diameter_mm']/25.4)
            current.require([g['cells_per_member'] for g in stack['grids']] == [8, 16, 32]
                            and all(g['facets'] == 32 for g in stack['grids']), 'complete unchanged three-grid witness inventory required')
            for grid in stack['grids']:
                for divisor in inputs['uniform_reference_divisors']:
                    output.append({**{k: binding[k] for k in ('case_id', 'state_id', 'field')}, 'axis_id': aid,
                                   'source_grid_cells_per_member': grid['cells_per_member'],
                                   'source_mode_range': source_range, 'working_reference': divisor == 5.,
                                   **compare_saved_field(grid, divisor)})
    current.require(len(output) == 432 and current.sha(OWN) == LOADED_SHA, 'complete unchanged 48-stack/three-grid/three-scenario scope required')
    verify_execution_sources(pins)
    refined = [r for r in output if r['source_grid_cells_per_member'] == 32]
    return {'schema': 'eoere_current_mixed_uniform_material_reference_comparisons/v1',
            'inputs': input_ref, 'producer': current.ref(OWN), 'source_sha256': pins, 'all_sources_unchanged': True,
            'source_vector_fields': inputs['references']['vector_fields'], 'source_saved_verification': VERIFICATION,
            'runtime_versions': runtime, 'geometry_revision': inputs['geometry_revision'],
            'hardware_revision': inputs['hardware_revision'], 'current_bolt_count': 100, 'current_screw_count': 66,
            'extra_grid': False, 'comparison_count': 432, 'refined_comparison_count': 144, 'comparisons': output,
            'refined_summaries': [{'uniform_reference_divisor': d,
                                  'maximum_witness': max((r for r in refined if r['uniform_reference_divisor'] == d),
                                                        key=lambda r: r['uniform_reduced_certified_witness_index']),
                                  'exceedance_count': sum(r['saved_witness_exceeds_assumed_reference'] for r in refined
                                                          if r['uniform_reference_divisor'] == d)}
                                 for d in inputs['uniform_reference_divisors']],
            'status': 'COMPLETE_SAVED_MIXED_WITNESS_COMPARISONS_UNDER_UNIFORM_REFERENCE_REDUCTION_HYPOTHESES',
            'complete_joint_resistance': None, 'physical_demand_bounds_established': False, 'structural_acceptance': False,
            'native_frame_elastic_LP_CAD_or_actual_fit_work': False, 'panel_screw_exceedances_deferred': True,
            'limits': inputs['assumptions']}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    with current.load('bridge').reserve(args.out) as output:
        output.write(run())
    print(current.ref(args.out))


if __name__ == '__main__':
    main()
