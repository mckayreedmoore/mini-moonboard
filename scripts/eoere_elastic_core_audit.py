"""Audit unchanged current elastic blocks and an explicit invariant comparator.

No assembly, frame response, native FEA, physical stiffness calibration or
design revision is performed. The exact stored matrices and saved responses
stay immutable; conclusions for a comparator do not admit those responses.
"""
from __future__ import annotations

import argparse
import importlib.metadata
from collections import Counter
from fractions import Fraction as F
from pathlib import Path
from unittest.mock import patch

import numpy as np

from scripts import eoere_elastic_core_certificate as method
from scripts import eoere_recession_audit as recession
from scripts.eoere_mixed_continuous_bound import read_exact
from scripts.summarize_eoere_current_response import canonical_sha

current, model = recession.current, recession.model
OWN = Path(__file__).resolve()
LOADED_SHA = current.sha(OWN)
INPUT = current.DOC/'selected-hardware-v1/current-response-v1/joint-closure-v1/elastic-core-inputs-v1.json'


def validate(inputs):
    method.require(inputs['schema'] == 'eoere_current_elastic_core_inputs/v1'
        and inputs['geometry_revision'] == 'eoere-raised-kicker-screws-v1'
        and inputs['hardware_revision'] == 'eoere-selected-purchase-hardware-v1'
        and inputs['current_bolt_count'] == 100 and inputs['current_screw_count'] == 66
        and inputs['extra_grid'] is False and inputs['actual_observations'] is None
        and inputs['structural_acceptance'] is False and inputs['physical_demand_bounds_established'] is False,
        'unchanged conditional retained scope required')
    method.require(inputs['comparator'] == 'K0=(I-R*inverse(R_d)*E_d.T).T*Ksym*(I-R*inverse(R_d)*E_d.T)'
        and inputs['datum_rule'] == 'scipy_QR_column_pivots_of_registered_R_transpose'
        and inputs['positive_shift_rule'] == 'binary64_half_smallest_approximate_free_eigenvalue'
        and inputs['proof_rule'] == 'exact_integer_Gram_residual_inf_less_than_positive_shift'
        and inputs['runtime_versions'] == {'numpy': '2.5.2', 'scipy': '1.18.1'}
        and inputs['comparator_is_physical_calibration'] is False
        and inputs['comparator_responses_computed_or_admitted'] is False,
        'explicit distinct invariant comparator and exact verification rule required')
    method.require(inputs['method_helper'] == current.ref(method.OWN)
        and method.LOADED_SHA == inputs['method_helper']['sha256'], 'loaded local core helper changed')


def owner_blocks(matrix, maps, owners, bodies):
    """Extract all owned local matrices, rejecting cross-owner elastic entries."""
    n = len(maps)
    method.require(matrix.shape == (n, n) and len(owners) == n and np.isfinite(matrix.data).all(),
                   'finite complete saved elastic matrix required')
    indices = {body['body']: [] for body in bodies}
    for i, owner in enumerate(owners):
        method.require(owner in indices, 'unregistered coordinate owner')
        indices[owner].append(i)
    result = []
    for body in bodies:
        name, first = body['body'], body['first_rigid_column']
        own = indices[name]
        method.require(len(own) == body['owned_coordinates'] and own, 'complete unique own body coordinates required')
        lookup, local = {j: i for i, j in enumerate(own)}, []
        for i in own:
            row = {}
            for at in range(matrix.indptr[i], matrix.indptr[i+1]):
                j, value = int(matrix.indices[at]), method.rational(matrix.data[at])
                if value:
                    method.require(j in lookup, 'elastic matrix couples different mechanical owners')
                    row[lookup[j]] = row.get(lookup[j], F(0))+value
            local.append({j: value for j, value in row.items() if value})
        rigid = [{j-first: value for j, value in maps[i].items()} for i in own]
        r = len(body['source_mode_columns'])
        method.require(all(0 <= j < r for row in rigid for j in row)
            and {j for row in rigid for j in row} == set(range(r)), 'own registered rigid columns required')
        result.append({'body': name, 'family': body['family'], 'global_coordinates': own,
                       'rows': local, 'rigid': rigid})
    method.require(sum(len(row['global_coordinates']) for row in result) == n, 'incomplete body partition')
    return result


def original_core(field, imported, frozen):
    pointer = field['operator_bundle']
    manifest = read_exact(pointer['manifest'])
    with model.read_array_file(pointer['arrays']) as archive:
        bank = {key: archive[key] for key in archive.files}
    method.require(all(frozen.bundle._array_record(bank[key]) == value
                       for key, value in manifest['array_metadata'].items())
                   and set(bank) == set(manifest['array_metadata']), 'own exact saved numeric arrays required')
    matrix = frozen.bundle._get_csr(bank, manifest['K'])
    modes = bank[manifest['rigid_modes_key']]
    maps, owners, bodies, size = recession.rigid_basis(manifest['coordinate_map'], modes)
    method.require(size == 800 and bodies == imported['bodies']
        and method.exact.matrix_digest(maps) == imported['exact_registered_rigid_basis_sha256'],
        'local core registration differs from the existing exact recession basis')
    keys = [manifest['K'][key] for key in ('data', 'indices', 'indptr')]+[manifest['rigid_modes_key']]
    fingerprint = canonical_sha({'matrix_shape': manifest['K']['shape'],
                                 'numeric_records': {key: manifest['array_metadata'][key] for key in keys},
                                 'owners': owners, 'bodies': bodies})
    return matrix, maps, owners, bodies, fingerprint


def saved_pose_change(q, work):
    """Exact change in the core's action at one saved pose; no equilibrium."""
    q = np.asarray(q)
    method.require(q.ndim == 1 and q.dtype == np.float64 and np.isfinite(q).all()
                   and sum(len(row['global_coordinates']) for row in work) == len(q),
                   'complete finite saved binary64 pose required')
    maximum, one_norm, energy = F(0), F(0), F(0)
    witness = None
    for row in work:
        indices = row['global_coordinates']
        local = list(map(method.rational, q[indices]))
        delta, skew = method.action(row['delta'], local), method.action(row['skew'], local)
        method.require(sum((v*w for v, w in zip(local, skew, strict=True)), F(0)) == 0,
                       'a skew part must have exactly zero quadratic energy')
        energy -= sum((v*w for v, w in zip(local, delta, strict=True)), F(0))/2
        for i, (di, si) in enumerate(zip(delta, skew, strict=True)):
            value = -di-si  # K0-K = -(Ksym-K0)-(K-Ksym).
            one_norm += abs(value)
            if abs(value) > maximum:
                maximum = abs(value)
                witness = {'body': row['body'], 'global_coordinate': indices[i], 'exact_action_change': str(value)}
    return {'exact_core_action_change_inf_n': str(maximum), 'core_action_change_inf_n': float(maximum),
            'exact_core_action_change_one_norm_n': str(one_norm),
            'exact_core_energy_change_nmm': str(energy), 'core_energy_change_nmm': float(energy),
            'maximum_action_change_witness': witness,
            'saved_pose_is_an_admitted_comparator_response': False}


def sources(pins, inputs):
    method.require(current.sha(OWN) == LOADED_SHA and current.sha(method.OWN) == method.LOADED_SHA,
                   'loaded local elastic-core sources changed')
    method.require({key: importlib.metadata.version(key) for key in inputs['runtime_versions']} == inputs['runtime_versions'],
                   'declared local factorization runtime required')
    model.verify_execution_sources(pins)


def run():
    own_input = current.ref(INPUT)
    inputs = read_exact(own_input)
    validate(inputs)
    parent = read_exact(inputs['recession_certificate'])
    parent_inputs = read_exact(parent['inputs'])
    recession.validate(parent_inputs)
    method.require(parent['schema'] == 'eoere_current_recession_certificate/v1' and parent['all_sources_unchanged'] is True
        and parent['conditional_fixed_reference_convex_family_coercivity_and_existence_at_original_loads'] is True
        and parent['core_PSD_or_exact_kernel_independently_verified'] is False,
        'unchanged original-load conditional existence certificate required')
    with patch.object(current, 'read', read_exact):
        cases, pins = recession.intake_source.intake()
    frozen = current.load('bridge').frozen()
    partition = model.component.load(recession.preflight.PARTITION, 'current_core_source_partition')
    refs = [own_input, inputs['method_helper'], inputs['recession_certificate'], parent['inputs'],
            *inputs['execution_sources'], current.ref(OWN),
            current.ref(current.ROOT/'tests/test_eoere_elastic_core_certificate.py'),
            current.ref(current.ROOT/'tests/test_eoere_elastic_core_audit.py')]
    pins = current.join(pins, parent['source_sha256'], partition.source_pins(), {r['path']: r['sha256'] for r in refs})
    sources(pins, inputs)
    common, records, work, results = None, [], [], []
    for (binding, field, _), old in zip(cases, parent['cases'], strict=True):
        imported = recession.import_case(binding, field, frozen, partition)
        method.require(all(imported[key] == old[key] for key in ('binding', 'operator_bundle',
            'exact_constraint_matrix_sha256', 'exact_registered_rigid_basis_sha256', 'exact_rigid_load_sha256',
            'original_applied_binary64_sha256')), 'own original case or projected identity drift')
        matrix, maps, owners, bodies, fingerprint = original_core(field, imported, frozen)
        if common is None:
            common = fingerprint
            for block in owner_blocks(matrix, maps, owners, bodies):
                certificate, delta, skew = method.certify_core(block['rows'], block['rigid'])
                records.append({key: block[key] for key in ('body', 'family', 'global_coordinates')} | certificate)
                work.append({key: block[key] for key in ('body', 'global_coordinates')} | {'delta': delta, 'skew': skew})
                print(f"verified local core {block['body']}", flush=True)
        method.require(fingerprint == common, 'shared local certificate needs identical own K/R/ownership banks')
        results.append({'case_id': binding['case_id'], 'state_id': binding['state_id'], 'field': binding['field'],
                        'operator_bundle': field['operator_bundle'], 'own_core_registration_sha256': fingerprint,
                        **saved_pose_change(np.asarray(field['response']['q'], dtype=np.float64), work)})
    method.require(len(records) == 150 and dict(Counter(row['family'] for row in records)) == recession.preflight.FAMILIES
        and sum(row['coordinates'] for row in records) == 9350
        and sum(row['registered_rigid_dimension'] for row in records) == 800, 'complete 150-owner local core proofs required')
    sources(pins, inputs)
    return {'schema': 'eoere_current_elastic_core_audit/v1', 'status': 'ALL_LOCAL_INVARIANT_COMPARATOR_CORES_CERTIFIED',
        'inputs': own_input, 'source_sha256': pins, 'all_sources_unchanged': True,
        'geometry_revision': inputs['geometry_revision'], 'hardware_revision': inputs['hardware_revision'],
        'current_bolt_count': 100, 'current_screw_count': 66, 'extra_grid': False,
        'body_count': len(records), 'original_coordinate_count': 9350, 'registered_rigid_dimension': 800,
        'shared_core_registration_sha256': common, 'body_certificates': records, 'case_count': len(results), 'cases': results,
        'constructed_comparator_core_PSD_and_exact_registered_kernel_proven': True,
        'literal_saved_symmetric_core_hypothesis_proven': all(row['literal_saved_energy_matrix_core_hypothesis_proven'] for row in records),
        'saved_symmetric_blocks_with_negative_rigid_work': sum(row['negative_rigid_quadratic_witness'] is not None for row in records),
        'original_load_existence_proven_for_constructed_fixed_reference_comparator_family': True,
        'saved_six_fields_admitted_as_comparator_equilibria': False,
        'old_reaction_bounds_transferred_to_comparator_or_original_f': False,
        'physical_core_stiffness_or_contact_or_restraint_qualified': False,
        'new_frame_response_or_native_FEA_or_CAD_run': False, 'actual_observations': None,
        'complete_joint_or_cleat_or_finished_member_resistance': None, 'structural_acceptance': False,
        'runtime_versions': inputs['runtime_versions'], 'limits': inputs['assumptions']}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    with current.load('bridge').reserve(args.out) as output:
        output.write(run())
    print(current.ref(args.out))


if __name__ == '__main__':
    main()
