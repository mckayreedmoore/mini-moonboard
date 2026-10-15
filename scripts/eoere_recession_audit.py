"""Static recession certificates at the unchanged six original load vectors.

Uses saved reference-coordinate port maps, not a new frame response. The
registered body-rigid core kernel is an explicit idealized-model hypothesis.
Auxiliary positive dual weights are not constitutive forces or floor pressure.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
from collections import Counter
from fractions import Fraction as F
from pathlib import Path
from unittest.mock import patch

import numpy as np

from scripts import eoere_cleat_finite_body as model
from scripts import eoere_current_finite_preflight as preflight
from scripts import eoere_current_washer_lands as intake_source
from scripts import eoere_recession_certificate as method
from scripts.eoere_mixed_continuous_bound import read_exact

current = model.current
OWN = Path(__file__).resolve()
LOADED_SHA = current.sha(OWN)
INPUT = current.DOC/'selected-hardware-v1/current-response-v1/joint-closure-v1/recession-certificate-inputs-v1.json'
FAMILIES = {'timber': ('timber', 'index', 22), 'fitting': ('four_port_fittings', 'dof_indices', 22),
            'shaft': ('shafts', 'index', 100), 'panel': ('panels', 'indices', 6)}


def validate(inputs):
    method.require(inputs['schema'] == 'eoere_current_recession_certificate_inputs/v1'
        and inputs['geometry_revision'] == 'eoere-raised-kicker-screws-v1'
        and inputs['hardware_revision'] == 'eoere-selected-purchase-hardware-v1'
        and inputs['current_bolt_count'] == 100 and inputs['current_screw_count'] == 66
        and inputs['extra_grid'] is False and inputs['actual_observations'] is None
        and inputs['structural_acceptance'] is False and inputs['physical_demand_bounds_established'] is False,
        'unchanged conditional retained scope required')
    method.require(inputs['core_hypothesis'] == 'PSD_exact_kernel_equals_registered_body_rigid_space'
        and inputs['rigid_basis_rule'] == 'saved_global_modes_rotation_columns_divided_by_1000_drop_largest_axis_shaft_rotation'
        and inputs['minimum_auxiliary_weight_n'] == '1/1000'
        and inputs['bilateral_rows'] == 968 and inputs['one_sided_rows'] == 1904
        and inputs['rigid_coordinate_count'] == 800 and inputs['original_coordinate_count'] == 9350
        and inputs['fixed_rear_XY_hosts'] == ['lumber_leg_left', 'lumber_leg_right']
        and inputs['runtime_versions'] == {'numpy': '2.5.2', 'scipy': '1.18.1'} and inputs['highs_version'] == '1.12.0',
        'predeclared cone/core and runtime required')
    method.require(inputs['method_helper'] == current.ref(method.OWN)
        and method.LOADED_SHA == inputs['method_helper']['sha256'], 'loaded exact certificate helper changed')


def rigid_basis(chart, stored_modes):
    """Register source rigid coordinates; do not assert they are exact K nulls."""
    n = chart['final_ndof']
    method.require(stored_modes.shape == (n, 6) and stored_modes.dtype == np.float64
                   and np.isfinite(stored_modes).all() and chart['rotation_scale'] == 1000., 'complete finite source rigid map required')
    maps, owners, manifest, cursor = [None]*n, [None]*n, [], 0
    for family, (bank, key, _) in FAMILIES.items():
        for body, row in chart[bank].items():
            indices = np.asarray(row[key])
            method.require(indices.dtype.kind in 'iu', 'integer owned coordinate indices required')
            indices = indices[indices >= 0].ravel()
            axes = list(range(6))
            if family == 'shaft':
                # The source already removes one free circular-shaft spin.
                axes.remove(3+int(np.argmax(abs(np.asarray(row['basis'][0])))))
            manifest.append({'body': body, 'family': family, 'first_rigid_column': cursor,
                             'source_mode_columns': axes, 'owned_coordinates': len(indices)})
            for i in indices:
                i = int(i)
                method.require(i < n and owners[i] is None, 'duplicate or out-of-range coordinate owner')
                owners[i] = body
                maps[i] = {cursor+j: method.rational(stored_modes[i, k])/(1000 if k >= 3 else 1)
                           for j, k in enumerate(axes) if stored_modes[i, k]}
            cursor += len(axes)
    method.require(all(owner is not None for owner in owners), 'every source coordinate needs an owner')
    return maps, owners, manifest, cursor


def compose_row(matrix, index, maps, owners, descriptor):
    result = {}
    permitted = {descriptor['first'], descriptor.get('second')}
    for at in range(matrix.indptr[index], matrix.indptr[index+1]):
        coordinate = int(matrix.indices[at])
        method.require(owners[coordinate] in permitted, 'port map references a foreign mechanical owner')
        value = method.rational(matrix.data[at])
        for j, coefficient in maps[coordinate].items():
            result[j] = result.get(j, F(0))+value*coefficient
    return {j: v for j, v in result.items() if v}


def constraints(partitions, maps, owners, enabled_ids):
    bilateral, unilateral, descriptions = [], [], []
    for row in partitions['groups']:
        method.require(np.isfinite([row['ka'], row['kl'], row['clearance']]).all()
                       and row['ka'] >= 0 and row['kl'] > 0 and row['clearance'] >= 0, 'source positive lateral law required')
        if row['ka'] > 0:
            target = unilateral if row['tension_only'] else bilateral
            target.append((compose_row(row['B'], 0, maps, owners, row), row['id']+'/axial'))
        for component in (1, 2):
            bilateral.append((compose_row(row['B'], component, maps, owners, row), row['id']+f'/lateral-{component}'))
    for row in partitions['contacts']:
        method.require(np.isfinite(row['stiffness']) and row['stiffness'] > 0, 'positive source one-sided law required')
        unilateral.append((compose_row(row['B'], 0, maps, owners, row), row['id']))
    for row in partitions['tangents']:
        if row['id'] in enabled_ids:
            method.require(np.isfinite(row['stiffness']) and row['stiffness'] > 0, 'positive enabled XY source law required')
            bilateral.append((compose_row(row['B'], 0, maps, owners, row), row['id']))
    rows = [{} for _ in range(max(j for row in maps for j in row)+1)]
    for column, (row, identity) in enumerate(bilateral+unilateral):
        descriptions.append(identity)
        for j, value in row.items():
            rows[j][column] = value
    return rows, len(bilateral), descriptions


def original_load(applied, maps):
    method.require(applied.shape == (len(maps),) and applied.dtype == np.float64
                   and np.isfinite(applied).all(), 'finite complete original stored load required')
    result = [F(0)]*(max(j for row in maps for j in row)+1)
    for value, row in zip(applied, maps, strict=True):
        force = method.rational(value)
        for j, coefficient in row.items():
            result[j] += force*coefficient
    return result


def import_case(binding, field, frozen, partition_helper):
    pointer = field['operator_bundle']
    record = read_exact(pointer['manifest'])
    method.require(record['arrays'] == pointer['arrays'] and record['captured_before_one_fresh_solve'] is True
        and record['historical_q_or_forces_used'] is False and record['final_ndof'] == 9350
        and record['original_operator_fingerprint_sha256'] == field['original_operator_fingerprint_sha256']
        and record['case']['case_id'] == binding['case_id'] and record['case']['loads'] == field['body_applied_loads'],
        'own unchanged pre-response operator/load identity required')
    chart = record['coordinate_map']
    ownership = preflight.current_partition(partition_helper, chart, record['case']['loads'], field['source_inputs']['shafts'])
    contact = preflight.current_contacts(record, field)
    with model.read_array_file(pointer['arrays']) as archive:
        method.require(set(archive.files) == set(record['array_metadata']), 'complete stored numeric inventory required')
        bank = {key: archive[key] for key in archive.files}
    method.require(all(frozen.bundle._array_record(bank[key]) == meta for key, meta in record['array_metadata'].items()),
                   'stored numeric metadata/content drift')
    partitions = {name: [{**row['descriptor'], 'B': frozen.bundle._get_csr(bank, row['B'])} for row in record['partitions'][name]]
                  for name in ('groups', 'contacts', 'tangents')}
    method.require(all(row['B'].shape == (3 if name == 'groups' else 1, record['final_ndof'])
                       for name, rows in partitions.items() for row in rows), 'complete source port row shapes required')
    maps, owners, bodies, size = rigid_basis(chart, bank[record['rigid_modes_key']])
    method.require(size == 800 and dict(Counter(row['family'] for row in bodies)) == preflight.FAMILIES
        and {body: family for body, family in ownership['body_manifest'].items()} ==
            {row['body']: row['family'] for row in bodies}, 'complete own 150-body /800-coordinate rigid space required')
    rows, bilateral, descriptions = constraints(partitions, maps, owners, set(contact['enabled_floor_tangent_ids']))
    method.require(bilateral == 968 and len(descriptions)-bilateral == 1904 and len(rows) == 800,
                   'all positive-law recession directions required')
    applied = bank[record['applied_key']]
    load = original_load(applied, maps)
    return {'rows': rows, 'bilateral': bilateral, 'columns': len(descriptions), 'load': load, 'bodies': bodies,
            'constraint_identities': descriptions, 'binding': {k: binding[k] for k in ('case_id', 'state_id', 'field')},
            'operator_bundle': pointer, 'exact_constraint_matrix_sha256': method.matrix_digest(rows),
            'exact_registered_rigid_basis_sha256': method.matrix_digest(maps),
            'exact_rigid_load_sha256': hashlib.sha256(json.dumps(list(map(str, load)), separators=(',', ':')).encode()).hexdigest(),
            'original_applied_binary64_sha256': hashlib.sha256(applied.tobytes()).hexdigest()}


def sources(pins, inputs):
    from scipy.optimize._highspy import _core

    method.require(current.sha(OWN) == LOADED_SHA and current.sha(method.OWN) == method.LOADED_SHA,
                   'loaded static-certificate sources changed')
    method.require({k: importlib.metadata.version(k) for k in inputs['runtime_versions']} == inputs['runtime_versions'],
                   'declared numerical runtime required')
    highs = '.'.join(str(getattr(_core, 'HIGHS_VERSION_'+part)) for part in ('MAJOR', 'MINOR', 'PATCH'))
    method.require(highs == inputs['highs_version'], 'declared static LP library version required')
    model.verify_execution_sources(pins)


def run():
    input_ref = current.ref(INPUT)
    inputs = read_exact(input_ref)
    validate(inputs)
    parent = read_exact(inputs['parent_energy_bounds'])
    method.require(parent['schema'] == 'eoere_current_reaction_energy_bounds/v1'
        and parent['all_sources_unchanged'] is True and parent['case_count'] == 6
        and parent['bounds_apply_to_original_exact_loads'] is False
        and parent['finite_geometry_or_directional_restraint_qualified'] is False,
        'unchanged completed corrected-load energy bounds required')
    # Reuse the exact current six-case intake, binding every JSON buffer it
    # consumes; this temporary callback is restored even when intake refuses.
    with patch.object(current, 'read', read_exact):
        cases, pins = intake_source.intake()
    frozen = current.load('bridge').frozen()
    helper = model.component.load(preflight.PARTITION, 'current_recession_source_partition')
    refs = [input_ref, inputs['parent_energy_bounds'], inputs['method_helper'], preflight.PARTITION, *inputs['execution_sources'],
            current.ref(OWN), current.ref(current.ROOT/'tests/test_eoere_recession_certificate.py'),
            current.ref(current.ROOT/'tests/test_eoere_recession_audit.py')]
    pins = current.join(pins, parent['source_sha256'], helper.source_pins(), {r['path']: r['sha256'] for r in refs})
    sources(pins, inputs)
    results, rank, selected, common_sha, common_bodies, common_ids, common_basis = [], None, None, None, None, None, None
    for binding, field, _ in cases:
        imported = import_case(binding, field, frozen, helper)
        rows, n, bilateral, load = (imported[k] for k in ('rows', 'columns', 'bilateral', 'load'))
        if common_sha is None:
            common_sha = imported['exact_constraint_matrix_sha256']
            common_bodies, common_ids = imported['bodies'], imported['constraint_identities']
            common_basis = imported['exact_registered_rigid_basis_sha256']
        method.require(imported['exact_constraint_matrix_sha256'] == common_sha
            and imported['exact_registered_rigid_basis_sha256'] == common_basis
            and imported['bodies'] == common_bodies and imported['constraint_identities'] == common_ids,
            'rank-witness sharing requires identical own basis, identities and constraint matrices')
        trial = method.select_witness(rows, n, bilateral, load, F(inputs['minimum_auxiliary_weight_n']),
                                      rank_proof=rank, selected=selected)
        rank, selected = trial['rank_certificate'], trial['selected_minor_columns']
        results.append({k: v for k, v in imported.items() if k not in ('rows', 'load', 'bodies', 'constraint_identities')} |
                       {k: v for k, v in trial.items() if k not in ('rank_certificate', 'selected_minor_columns')})
        print(json.dumps({'case_id': binding['case_id'], 'strict_weight_margin_lower': trial['load_certificate']['strict_weight_margin_lower']}), flush=True)
    sources(pins, inputs)
    return {'schema': 'eoere_current_recession_certificate/v1', 'status': 'STRICT_RIGID_RECESSION_LOAD_CERTIFICATES_COMPLETE_UNDER_CORE_HYPOTHESIS',
        'inputs': input_ref, 'source_sha256': pins, 'all_sources_unchanged': True, 'geometry_revision': inputs['geometry_revision'],
        'hardware_revision': inputs['hardware_revision'], 'current_bolt_count': 100, 'current_screw_count': 66, 'extra_grid': False,
        'case_count': len(results), 'cases': results, 'shared_rank_certificate': rank, 'shared_minor_columns': selected,
        'shared_body_rigid_basis': common_bodies, 'shared_constraint_identities': common_ids,
        'conditional_fixed_reference_convex_family_coercivity_and_existence_at_original_loads': True,
        'core_PSD_or_exact_kernel_independently_verified': False, 'uniform_response_or_reaction_bound_established': False,
        'old_f_hat_energy_bounds_transferred_to_original_f': False, 'physical_or_finite_geometry_restraint_qualified': False,
        'credited_rear_leg_bearing_at_an_unknown_equilibrium_proven': False, 'auxiliary_weights_are_constitutive_forces': False,
        'new_frame_response_or_native_FEA_or_CAD_run': False, 'actual_observations': None, 'structural_acceptance': False,
        'complete_joint_or_cleat_or_finished_member_resistance': None, 'runtime_versions': inputs['runtime_versions'], 'limits': inputs['assumptions']}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    with current.load('bridge').reserve(args.out) as output:
        output.write(run())
    print(json.dumps(current.ref(args.out)))


if __name__ == '__main__':
    main()
