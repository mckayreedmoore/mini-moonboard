"""Restore saved finite panel load work without correction or frame solves.

Use the current v5 mass rows and its two explicitly generalized correction
vectors. Reuse the frozen external-potential method with one data-access seam;
all evaluations below are known synthetic kinematics, never saved responses.
"""
from __future__ import annotations

import argparse
import ast
import copy
import hashlib
import json
from fractions import Fraction as F
from pathlib import Path
from types import MethodType, ModuleType, SimpleNamespace

import numpy as np
from scipy.sparse import csr_matrix

ROOT = Path(__file__).resolve().parents[1]
OWN = Path(__file__).resolve()
LOADED_SHA = hashlib.sha256(OWN.read_bytes()).hexdigest()
BOOT = {'path': 'scripts/eoere_panel_bulk_consumer.py',
        'sha256': '6f6275882feea7dcaba06446af67c3b12fc7e4e82479ac727a70a4dcabc21716'}


def require(ok, message):
    if not ok:
        raise ValueError(message)


def bootstrap(pins):
    data = (ROOT/BOOT['path']).read_bytes()
    require(hashlib.sha256(data).hexdigest() == BOOT['sha256']
            and pins.get(BOOT['path'], BOOT['sha256']) == BOOT['sha256'], 'frozen finite interface consumer changed')
    pins[BOOT['path']] = BOOT['sha256']
    module = ModuleType('_eoere_verified_finite_panel_load_bootstrap'); module.__file__ = str(ROOT/BOOT['path'])
    exec(compile(data, module.__file__, 'exec'), module.__dict__)  # noqa: S102 - authenticated source buffer
    return module


def load_api(inputs, producer, consumer, base, pins):
    """Capture port embeddings and the external method, never a constructor."""
    api = producer.methods(inputs, base, pins)
    consumer.install_point_port(api, producer, inputs, base, pins)
    ns = dict(api.adapter.point_port.__globals__)
    ns['diagnostics'] = SimpleNamespace(REFERENCE=np.array([0., 750., 1100.]))
    methods = producer.class_subset(inputs['panel_adapter'], 'FinitePanelAdapter',
        ('_embed_gradient', '_embed_matrix', 'current_rigid_modes'), ns, base, pins)
    for name in ('_embed_gradient', '_embed_matrix', 'current_rigid_modes'):
        setattr(api.adapter, name, getattr(methods, name))
    tree = ast.parse(base.captured(inputs['panel_adapter'], pins))
    classes = [n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == 'FinitePanelLoads']
    require(len(classes) == 1, 'one frozen finite panel load class required')
    functions = [n for n in classes[0].body if isinstance(n, ast.FunctionDef) and n.name == 'external']
    require(len(functions) == 1, 'one complete frozen external load method required')
    function = copy.deepcopy(functions[0])
    old = ast.parse('a.measure["mass_weights"] @ a.measure["xy_mm"]', mode='eval').body
    replacement = ast.parse('a.saved_mass_reference_xy_mm', mode='eval').body
    class SavedMean(ast.NodeTransformer):
        count = 0
        def visit_BinOp(self, node):
            if ast.dump(node, include_attributes=False) == ast.dump(old, include_attributes=False):
                self.count += 1
                return copy.deepcopy(replacement)
            return self.generic_visit(node)
    transform = SavedMean(); function = transform.visit(function)
    require(transform.count == 1, 'exact single reference-mass-mean data access seam required')
    external_ns = {'np': np, 'csr_matrix': csr_matrix, 'diagnostics': ns['diagnostics']}
    exec(compile(ast.fix_missing_locations(ast.Module(body=[function], type_ignores=[])),  # noqa: S102 - pinned local method
        inputs['panel_adapter']['path'], 'exec', dont_inherit=True), external_ns)
    api.external = external_ns['external']
    return api


def finite_vector(values, size):
    value = np.asarray(values, dtype=float)
    require(value.shape == (size,) and np.isfinite(value).all(), 'complete finite numeric load/measure vector required')
    return value.copy()


def restore_load(panel, saved_panel, source_loads, corrections, case_id, state_id, api, gates):
    """Use the saved finite source data, with no inverse or load regeneration."""
    name = panel.geometry['name']
    require(saved_panel['global_dof_indices'] and len(saved_panel['global_dof_indices']) == 363
        and np.array_equal(saved_panel['axes_columns_xyz'], panel.axes)
        and np.array_equal(saved_panel['origin_xyz_mm'], panel.origin)
        and saved_panel['basis_width_mm'] == panel.basis.width and saved_panel['basis_height_mm'] == panel.basis.height
        and saved_panel['basis_order'] == 11 and np.array_equal(saved_panel['basis_knots_normalized'], panel.basis.knots),
        'same source finite panel embedding and coefficient space required')
    mass = finite_vector(saved_panel['mass_coefficient_row'], 121)
    mean = finite_vector(saved_panel['mass_reference_xy_mm'], 2)
    local_nodes = (panel.reference_nodes-panel.origin)@panel.axes[:, :2]
    normalization_error = float(abs(mass.sum()-1.))
    mean_error = float(np.max(abs(mass@local_nodes-mean)))
    require(normalization_error < gates['mass_sum'] and mean_error < gates['mass_mean_mm'], 'retained finite mass row and reference mean disagree')
    panel.measure = {'mass_row': mass}; panel.saved_mass_reference_xy_mm = mean
    loads = [copy.deepcopy(row) for row in source_loads if row['body'] == name]
    require(loads and len({row['id'] for row in loads}) == len(loads)
        and all(not any(row.get('moment_xyz_nmm', [0., 0., 0.])) for row in loads), 'unique own loads without point couples required')
    uniform = [row for row in loads if row['id'] == 'self-weight/'+name]
    require(len(uniform) == 1 and not any(row['id'].startswith('self-weight/') for row in loads if row not in uniform), 'one own uniform selfweight required')
    force = finite_vector(uniform[0]['force_xyz_n'], 3)
    own = [row for row in corrections if row['panel'] == name]
    require(len(own) == 2 and {row['kind'] for row in own} == {'retained_rigid_RHS', 'reference_port_alignment'}
        and all(row['case_id'] == case_id and row['state_id'] == state_id
            and row['global_coefficient_indices'] == saved_panel['global_dof_indices']
            and row['physical_point_forces_or_pressure_representation'] is False for row in own), 'two distinct own explicitly generalized correction terms required')
    vectors = {row['kind']: finite_vector(row['local_generalized_force_n'], 363) for row in own}
    load = SimpleNamespace(adapter=panel, loads=loads, point_loads=[row for row in loads if row not in uniform],
        uniform_force=force, uniform_generalized=np.concatenate([f*mass for f in panel.axes.T@force]),
        retained_rigid_correction_n=vectors['retained_rigid_RHS'], reference_port_alignment_correction_n=vectors['reference_port_alignment'],
        correction_n=vectors['retained_rigid_RHS']+vectors['reference_port_alignment'], case_id=case_id, accessory='original_top')
    load.external = MethodType(api.external, load)
    return load, {'mass_sum_minus_one': float(mass.sum()-1.), 'mass_first_moment_difference_mm': (mass@local_nodes-mean).tolist(),
        'normalization_exact_in_stored_binary_coefficients_asserted': False, 'source_ids': [row['id'] for row in loads]}


def controls(load, producer, gates):
    panel = load.adapter; zero = np.zeros(363); reference = np.array([0., 750., 1100.])
    rest = load.external(zero, tangent=False, reference=reference)
    total_force = sum((np.asarray(row['force_xyz_n']) for row in load.loads), np.zeros(3))
    translation = np.array([.3, -.2, .1])
    translated = producer.panel_state(panel, np.eye(3), translation)
    shifted = load.external(translated, tangent=False, reference=reference)
    translation_error = abs(shifted['physical_load_potential_nmm']-rest['physical_load_potential_nmm']+total_force@translation)
    rotation = np.array([[0., -1., 0.], [0., 0., -1.], [1., 0., 0.]])
    offset = np.array([23., -31., 17.]); rotated = producer.panel_state(panel, rotation, offset)
    moved = load.external(rotated, tangent=False, reference=reference)
    mass_reference = panel.origin+panel.axes@np.r_[panel.saved_mass_reference_xy_mm, 0.]
    rigid_physical = -load.uniform_force@(rotation@mass_reference+offset-mass_reference)
    for row in load.point_loads:
        # Use the actual reference port, including the declared accessory edge
        # extension; source-coordinate rounding is kept separate below.
        port = panel.point_port(zero, row['point_xyz_mm'], tangent=False, allow_edge_extension=row['id'].startswith('accessory/'))
        position = port['position_xyz_mm']
        rigid_physical -= np.asarray(row['force_xyz_n'])@(rotation@position+offset-position)
    rotation_error = abs(moved['physical_load_potential_nmm']-rest['physical_load_potential_nmm']-rigid_physical)
    require(translation_error < gates['energy_nmm'] and rotation_error < gates['energy_nmm'], 'known finite dead-load potential identity failed')
    residual_force = max(float(max(abs(r['wrench_residual_n_nmm'][:3]))) for r in (rest, shifted, moved))
    residual_moment = max(float(max(abs(r['wrench_residual_n_nmm'][3:]))) for r in (rest, shifted, moved))
    require(residual_force < gates['force_n'] and residual_moment < gates['moment_nmm'], 'physical plus explicit generalized work must equal total load work')
    for q, result in ((zero, rest), (translated, shifted), (rotated, moved)):
        require(abs(result['correction_potential_nmm']+load.correction_n@q) < gates['energy_nmm']
                and abs(result['correction_potential_nmm']-result['retained_rigid_correction_potential_nmm']
                        -result['reference_port_alignment_potential_nmm']) < gates['energy_nmm'], 'both original correction potentials must stay explicit')
    return rest, {'translation_potential_error_nmm': float(translation_error), 'common_rotation_physical_potential_error_nmm': float(rotation_error),
        'maximum_owner_force_work_residual_n': residual_force, 'maximum_owner_moment_work_residual_nmm': residual_moment,
        'all_evaluated_poses_are_synthetic_method_controls': True}


def vector_key(value):
    return hashlib.sha256(np.asarray(value, dtype='<f8').tobytes()).hexdigest()


def run(reference):
    pins = {}; consumer = bootstrap(pins); producer, base = consumer.context(pins)
    inputs = json.loads(base.captured(reference, pins))
    require(inputs['schema'] == 'eoere_finite_panel_load_inputs/v1' and inputs['actual_observations'] is None
        and inputs['structural_acceptance'] is False and inputs['extra_grid'] is False, 'current load-method-only scope required')
    for row in inputs['execution_sources']: base.captured(row, pins)
    require(pins.get(str(OWN.relative_to(ROOT))) == LOADED_SHA, 'exact executing finite load consumer required')
    parent = json.loads(base.captured(inputs['panel_bulk_result'], pins))
    for path, digest in parent['source_sha256'].items(): base.captured({'path': path, 'sha256': digest}, pins)
    require(parent['geometry_revision'] == inputs['geometry_revision'] == 'eoere-raised-kicker-screws-v1'
        and parent['hardware_revision'] == inputs['hardware_revision'] == 'eoere-selected-purchase-hardware-v1'
        and parent['complete_coupled_contact_fracture_law_or_evaluation_ready'] is False, 'same incomplete retained bulk/interface stage required')
    interface_inputs = json.loads(base.captured(parent['inputs'], pins))
    remaining = producer.bootstrap(pins); gravity = remaining.bootstrap(pins); contact = gravity.bootstrap(pins)
    material = contact.bootstrap(pins); prior = material.bootstrap(pins); boot = prior.bootstrap(pins)
    runtime = boot.check_runtime(parent['runtime'])
    old_load_work = json.loads(base.captured(interface_inputs['remaining_load_work'], pins))
    finite = json.loads(base.captured(inputs['current_finite_frame_v5'], pins))
    require(finite['geometry_revision'] == parent['geometry_revision'] and finite['hardware_revision'] == parent['hardware_revision']
        and finite['extra_grid'] is False and all(row['finite_equilibrium_established'] is False for row in finite['cases']),
        'same current unbalanced v5 source model required; no equilibrium acceptance transfer')
    gates = inputs['control_gates']
    require(gates == {'mass_sum': 1e-12, 'mass_mean_mm': 1e-7, 'reference_rhs_n': 1e-5,
                     'energy_nmm': 1e-5, 'force_n': 1e-7, 'moment_nmm': 1e-5}, 'fixed numerical source/work gates required')
    api = load_api(interface_inputs, producer, consumer, base, pins)
    cases, vectors, panel_data = [], {}, {}
    for binding, old_case in zip(parent['case_source_bindings_only'], old_load_work['cases'], strict=True):
        field = json.loads(base.captured(binding['field'], pins))
        v5, = [row for row in finite['cases'] if row['case_id'] == binding['case_id'] and row['state_id'] == binding['state_id']]
        require(v5['field'] == binding['field'] and old_case['binding'] == binding, 'same own source case/field required')
        manifest = json.loads(base.captured(field['operator_bundle']['manifest'], pins))
        panels = {name: producer.panel_adapter(descriptor, api)[0] for name, descriptor in manifest['coordinate_map']['panels'].items()}
        require(len(v5['panel_generalized_load_corrections']) == 12 and len(panels) == 6, 'complete six-panel correction census required')
        registrations, all_ids = [], []
        for name, panel in panels.items():
            saved_panel = v5['full_finite_kinematic_map']['panels'][name]
            require(saved_panel['global_dof_indices'] == manifest['coordinate_map']['panels'][name]['indices'], 'same own panel coefficient indices required')
            load, measure = restore_load(panel, saved_panel, field['body_applied_loads'], v5['panel_generalized_load_corrections'],
                                         binding['case_id'], binding['state_id'], api, gates)
            rest, observed = controls(load, producer, gates)
            previous, = [row for row in old_case['panel_work'] if row['panel'] == name]
            target = np.array([float(F(value))
                               for value in old_load_work['saved_panel_force_vectors_by_sha256'][previous['force_vector_sha256']]])
            error = float(np.max(abs(-rest['local_gradient_n']-target)))
            require(error < gates['reference_rhs_n'] and previous['source_load_ids'] == measure['source_ids'], 'restore the complete saved linear panel RHS and original source inventory')
            hashes = {}
            for kind, value in [('retained_rigid_RHS', load.retained_rigid_correction_n), ('reference_port_alignment', load.reference_port_alignment_correction_n)]:
                digest = vector_key(value); values = value.tolist()
                require(digest not in vectors or vectors[digest] == values, 'same correction digest must bind identical coefficients')
                vectors[digest] = values; hashes[kind] = digest
            data = {'saved_panel': saved_panel, 'measure_control': {key: value for key, value in measure.items() if key != 'source_ids'}}
            require(name not in panel_data or panel_data[name] == data, 'same retained reference-mass data across cases required')
            panel_data[name] = data; all_ids.extend(measure['source_ids'])
            registrations.append({'panel': name, 'source_ids': measure['source_ids'], 'point_load_count': len(load.point_loads),
                'uniform_selfweight_ids': ['self-weight/'+name], 'correction_vector_sha256': hashes,
                'reference_rhs_difference_linf_n': error, 'saved_linear_load_vector_sha256': previous['force_vector_sha256'], 'controls': observed})
        require(len(all_ids) == len(set(all_ids)) == 217, 'all 217 own physical panel actions exactly once required')
        mapped = contact.split_loads(field)
        panel_ids = set(all_ids); other_ids = [row['id'] for row in mapped if row['id'] not in panel_ids]
        require(len(mapped) == 835 and len(other_ids) == 618, 'same 835-source inventory with 618 separately defined bulk actions required')
        cases.append({'binding': binding, 'panels': registrations, 'source_physical_action_counts': {'panel': 217, 'other_bulk': 618, 'total': 835},
                      'explicit_generalized_correction_terms': 12, 'candidate_response_or_equilibrium_evaluated': False})
    require(len(cases) == 6 and len(panel_data) == 6, 'all 36 panel/case registrations required')
    for path, digest in tuple(pins.items()): base.captured({'path': path, 'sha256': digest}, pins)
    return {'schema': 'eoere_finite_panel_load_work/v1', 'inputs': reference, 'source_sha256': pins, 'runtime': runtime,
        'geometry_revision': inputs['geometry_revision'], 'hardware_revision': inputs['hardware_revision'], 'extra_grid': False,
        'panels': panel_data, 'cases': cases, 'correction_vectors_by_sha256': vectors, 'law_and_limits': inputs['law_and_limits'],
        'primary_method': inputs['primary_method'], 'finite_panel_load_work_defined_without_correction_regeneration': True,
        'complete_coupled_contact_fracture_law_or_evaluation_ready': False,
        'new_candidate_response_native_frame_contact_equilibrium_inverse_factorization_or_CAD': False,
        'physical_stiffness_restraint_demand_or_complete_resistance_qualified': False,
        'panel_screw_exceedances_deferred': True, 'actual_observations': None, 'structural_acceptance': False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--inputs', type=Path, required=True); parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args(); require(not args.out.exists(), 'preserve issued finite panel load evidence')
    reference = {'path': str(args.inputs.resolve().relative_to(ROOT)), 'sha256': hashlib.sha256(args.inputs.read_bytes()).hexdigest()}
    result = run(reference); args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open('x') as stream:
        json.dump(result, stream, indent=2, sort_keys=True); stream.write('\n')
    print(json.dumps({'output': str(args.out), 'registrations': 36, 'correction_vectors': len(result['correction_vectors_by_sha256'])}))


if __name__ == '__main__':
    main()
