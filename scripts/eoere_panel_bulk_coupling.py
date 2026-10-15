"""Define objective panel/finished-timber screw work without a response solve.

The receiver is a bounded mean-placement/mean-gradient functional on the
previously contained cubes. This is an explicit numerical coupling assumption,
not a physical Hillman embedment, stiffness, pressure or resistance model.
"""
from __future__ import annotations

import argparse
import ast
import copy
import hashlib
import json
import math
from dataclasses import dataclass
from fractions import Fraction as F
from pathlib import Path
from types import ModuleType, SimpleNamespace

import numpy as np
from scipy.interpolate import BSpline
from scipy.sparse import coo_matrix, csr_matrix

ROOT = Path(__file__).resolve().parents[1]
OWN = Path(__file__).resolve()
LOADED_SHA = hashlib.sha256(OWN.read_bytes()).hexdigest()
BOOT = {'path': 'scripts/eoere_remaining_load_work.py',
        'sha256': 'eb078177a9e10a6ae3728058953436065704fc7ad8b2cd137b2e7cef26b12082'}


def require(ok, message):
    if not ok:
        raise ValueError(message)


def bootstrap(pins):
    data = (ROOT/BOOT['path']).read_bytes()
    require(hashlib.sha256(data).hexdigest() == BOOT['sha256']
            and pins.get(BOOT['path'], BOOT['sha256']) == BOOT['sha256'], 'frozen load-work bootstrap changed')
    pins[BOOT['path']] = BOOT['sha256']
    module = ModuleType('_eoere_verified_panel_bulk_bootstrap'); module.__file__ = str(ROOT/BOOT['path'])
    exec(compile(data, module.__file__, 'exec'), module.__dict__)  # noqa: S102 - authenticated source buffer
    return module


def closed_gauss4(order):
    """Four-point Legendre rule by scalar radicals; no eigensystem/solve."""
    require(type(order) is int and order == 4, 'only the declared four-point ring rule is admitted')
    large = math.sqrt((3+2*math.sqrt(6/5))/7)
    small = math.sqrt((3-2*math.sqrt(6/5))/7)
    outer, inner = (18-math.sqrt(30))/36, (18+math.sqrt(30))/36
    return np.array([-large, -small, small, large]), np.array([outer, inner, inner, outer])


def class_subset(reference, name, methods, namespace, base, pins):
    """Capture named methods/declared data from one authenticated local class."""
    tree = ast.parse(base.captured(reference, pins))
    found = [n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == name]
    require(len(found) == 1, 'one authenticated class definition required')
    node = copy.deepcopy(found[0])
    selected = [n for n in node.body if isinstance(n, ast.FunctionDef) and n.name in methods]
    require(len(selected) == len(methods) and {n.name for n in selected} == set(methods), 'unique complete pure class methods required')
    node.body = [n for n in node.body if isinstance(n, ast.AnnAssign)]+selected
    exec(compile(ast.fix_missing_locations(ast.Module(body=[node], type_ignores=[])),  # noqa: S102 - pinned local AST
                 reference['path'], 'exec', dont_inherit=True), namespace)
    return namespace[name]


def methods(inputs, base, pins):
    """Reuse frozen finite ports and connector jets, without their assemblers."""
    loader = base.private(inputs['definition_loader'], pins)
    ns = {'np': np, 'math': math, 'BSpline': BSpline, 'dataclass': dataclass,
          'require': require, 'leggauss': closed_gauss4, 'coo_matrix': coo_matrix, 'csr_matrix': csr_matrix}
    loader.definitions(inputs['panel_basis'], ('local_xy', 'disk_quadrature'), (), ns, pins)
    basis = class_subset(inputs['panel_basis'], 'SheetBasis', ('__post_init__', 'values'), ns, base, pins)
    method = SimpleNamespace(require=require, local_xy=ns['local_xy'], disk_quadrature=ns['disk_quadrature'])
    finite = loader.definitions(inputs['finite_plate'], ('normal_derivatives',), (), {'np': np, 'require': require}, pins)
    ns.update(method=method, finite=finite)
    loader.definitions(inputs['panel_adapter'], ('_coefficient_indices', '_operator'), ('DERIVATIVES',), ns, pins)
    adapter = class_subset(inputs['panel_adapter'], 'FinitePanelAdapter', ('local_q', '_jet_result', 'screw_port'), ns, base, pins)

    # Preserve the frozen embedding algorithm; evaluate its scalar 3x3
    # determinant by the triple product instead of a library factorization.
    tree = ast.parse(base.captured(inputs['current_finite_frame'], pins))
    functions = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'prepare_panel_embedding']
    require(len(functions) == 1, 'one frozen runtime embedding definition required')
    function = copy.deepcopy(functions[0]); old = ast.parse('np.linalg.det(runtime)', mode='eval').body
    new = ast.parse('np.dot(np.cross(runtime[:, 0], runtime[:, 1]), runtime[:, 2])', mode='eval').body
    class TripleProduct(ast.NodeTransformer):
        count = 0
        def visit_Call(self, node):
            if ast.dump(node, include_attributes=False) == ast.dump(old, include_attributes=False):
                self.count += 1
                return copy.deepcopy(new)
            return self.generic_visit(node)
    transform = TripleProduct(); function = transform.visit(function)
    require(transform.count == 1, 'exact single determinant evaluation seam required')
    embedding_ns = {'np': np, 'copy': copy, 'current': SimpleNamespace(require=require),
                    'panel_method': SimpleNamespace(FinitePanelAdapter=adapter)}
    exec(compile(ast.fix_missing_locations(ast.Module(body=[function], type_ignores=[])),  # noqa: S102 - pinned local AST
                 inputs['current_finite_frame']['path'], 'exec', dont_inherit=True), embedding_ns)

    cn = {'np': np, 'dataclass': dataclass, 'coo_matrix': coo_matrix, 'csr_matrix': csr_matrix}
    class_subset(inputs['connectors'], 'ScalarJet', ('scaled',), cn, base, pins)
    class_subset(inputs['connectors'], 'VectorJet', ('minus', 'times', 'dot'), cn, base, pins)
    connectors = loader.definitions(inputs['connectors'], ('aligned_jets', 'position_field', 'normal_field',
        '_square_energy', '_radius', 'connector_response'), (), cn, pins)
    return SimpleNamespace(basis=basis, adapter=adapter, embed=embedding_ns['prepare_panel_embedding'], connectors=connectors)


def panel_adapter(descriptor, api):
    """Initialize only the authenticated port dependencies; no energy/mass K."""
    require(descriptor['intervals'] == 8 and descriptor['basis_order_per_direction'] == 11
            and len(descriptor['indices']) == 363, 'current cubic interval-eight panel required')
    panel = api.adapter(); panel.geometry = copy.deepcopy(descriptor['geometry'])
    panel.basis = api.basis(descriptor['width_mm'], descriptor['height_mm'], 8)
    require(np.array_equal(panel.basis.knots, descriptor['knots_normalized']), 'same saved spline knots required')
    panel.local_size = 363; panel.indices = np.arange(363); panel.ndof = 375
    panel.origin = np.asarray(panel.geometry['origin'], dtype=float)
    panel.axes = np.asarray(panel.geometry['axes'], dtype=float)
    panel.geometry['axes'] = panel.axes.copy()
    panel.panel = {'thickness': descriptor['thickness_mm']}
    embedding = api.embed(panel)
    knots = panel.basis.knots
    greville = np.array([sum(knots[i+1:i+4])/3 for i in range(panel.basis.order)])
    xy = np.array([[a*panel.basis.width, b*panel.basis.height] for a in greville for b in greville])
    panel.reference_nodes = panel.origin+xy@panel.axes[:, :2].T
    return panel, embedding


def bulk_port(mean_placement, mean_gradient, center, target):
    """T(chi)=mean_D chi + mean_D Grad(chi) (target-center), a linear H1 map."""
    mean, gradient, center, target = (np.asarray(a, dtype=float) for a in (mean_placement, mean_gradient, center, target))
    require(mean.shape == center.shape == target.shape == (3,) and gradient.shape == (3, 3)
            and np.isfinite([*mean, *gradient.ravel(), *center, *target]).all(), 'finite placement/gradient and reference datums required')
    offset = target-center; jacobian = np.zeros((3, 375)); jacobian[:, 363:366] = np.eye(3)
    for i in range(3): jacobian[i, 366+3*i:369+3*i] = offset
    return {'position_xyz_mm': mean+gradient@offset, 'J_csr': csr_matrix(jacobian),
            'H_xyz_csr': [csr_matrix((375, 375)) for _ in range(3)]}


def bulk_definition(center, target, cube):
    center, target = [list(map(F, a)) for a in (center, target)]
    radius, volume = F(cube['half_width_mm']), F(cube['volume_mm3'])
    require(volume == 8*radius**3 and radius > 0
            and list(map(F, cube['cube_center_xyz_mm'])) == center, 'same nonempty contained reference cube required')
    offset = [a-b for a, b in zip(target, center, strict=True)]
    return {'half_width_mm': str(radius), 'volume_mm3': str(volume), 'center_xyz_mm': list(map(str, center)),
        'target_xyz_mm': list(map(str, target)), 'target_minus_center_xyz_mm': list(map(str, offset)),
        'offset_square_mm2': str(sum(a*a for a in offset)),
        'H1_bound_L2_coefficient_per_mm3': str(1/volume),
        'H1_bound_gradient_coefficient_per_mm': str(sum(a*a for a in offset)/volume),
        'operator': 'mean_D(chi)+mean_D(Grad(chi))*(target-center)',
        'bound': '|T(v)| <= V^(-1/2)*(||v||_L2(D)+|target-center|*||Grad(v)||_L2(D))',
        'receiver_work': 'F_receiver dot mean_D(v+Grad(v)*(target-center))',
        'equivalent_reference_body_force': 'F_receiver/V on D',
        'equivalent_reference_cube_boundary_traction': '(F_receiver/V)*((target-center) dot N_D)',
        'face_traction_scalar_per_mm3': [[str(sign*offset[i]/volume) for sign in (-1, 1)] for i in range(3)],
        'physical_embedment_stiffness_pressure_or_resistance_qualified': False}


def panel_state(panel, rotation, translation):
    """Exact spline affine placement control, not a retained response state."""
    nodes = panel.reference_nodes
    return ((nodes@rotation.T+translation-nodes)@panel.axes).T.ravel()


def interaction(panel, screw, center, mean, gradient, q, api):
    require(screw['ka'] == screw['kl'] == 1000. and screw['clearance'] == 0.
            and screw['tension_only'] is True and screw['physical_Hillman_stiffness_or_capacity_qualified'] is False,
            'retain the unqualified generic Hillman law, without product-property transfer')
    first = panel.screw_port(q, screw['source_screw_descriptor'], tangent=True)
    target = first['reference_position_xyz_mm']
    require(np.linalg.norm(target-np.asarray(screw['point_xyz_mm'])) < 1e-7, 'own recorded reference port within datum precision required')
    second = bulk_port(mean, gradient, center, target)
    result = api.connectors.connector_response(api.connectors.position_field(first), api.connectors.position_field(second),
        api.connectors.normal_field(first), axial_stiffness_n_mm=screw['ka'], lateral_stiffness_n_mm=screw['kl'])
    return first, second, result


def rigid_work(panel, q, mean, gradient, result):
    nodes = panel.reference_nodes+q.reshape(3, -1).T@panel.axes.T
    columns = []
    for i in range(6):
        translation, spin = np.zeros(3), np.zeros(3)
        if i < 3: translation[i] = 1.
        else: spin[i-3] = 1.
        panel_v = (translation+np.cross(spin, nodes))@panel.axes
        mean_v = translation+np.cross(spin, mean)
        gradient_v = np.cross(spin, gradient.T).T
        columns.append(np.r_[panel_v.T.ravel(), mean_v, gradient_v.ravel()])
    return np.asarray(columns)@result['gradient_n']


def controls(panel, screw, center, api, gates):
    """Known affine/slip/rigid-motion answers; no saved q or equilibrium."""
    identity = np.eye(3); q0 = np.zeros(363)
    first, _, rest = interaction(panel, screw, center, center, identity, q0, api)
    normal = first['normal_xyz']; tangent = panel.axes[:, 0]
    require(np.dot(normal, screw['basis'][0]) > 1-1e-8, 'current positive axial director must match its own screw')
    rotation = np.array([[0., -1., 0.], [0., 0., -1.], [1., 0., 0.]])
    translation = np.array([23., -31., 17.])
    rigid_q = panel_state(panel, rotation, translation)
    rigid_first, rigid_second, rigid = interaction(panel, screw, center, rotation@center+translation, rotation, rigid_q, api)
    rigid_error = max(np.linalg.norm(rigid_first['position_xyz_mm']-(rotation@first['reference_position_xyz_mm']+translation)),
                      np.linalg.norm(rigid_second['position_xyz_mm']-(rotation@first['reference_position_xyz_mm']+translation)))
    require(rigid_error < gates['position_mm'] and max(abs(rest['energy_nmm']), abs(rigid['energy_nmm'])) < gates['energy_nmm'],
            'reference and common finite rigid motions must have zero numerical energy')
    records = []
    for axial in (.3, -.3):
        slip = axial*normal+.2*tangent
        q = panel_state(panel, identity, slip)
        p, _, result = interaction(panel, screw, center, center, identity, q, api)
        expected = .5*1000*(max(axial, 0.)**2+.2**2)
        work = rigid_work(panel, q, center, identity, result)
        rotated_q = panel_state(panel, rotation, translation+rotation@slip)
        rp, _, rotated = interaction(panel, screw, center, rotation@center+translation, rotation, rotated_q, api)
        errors = {'known_energy_nmm': abs(result['energy_nmm']-expected),
            'rotated_energy_nmm': abs(rotated['energy_nmm']-result['energy_nmm']),
            'rotated_force_n': float(np.linalg.norm(rotated['force_on_first_xyz_n']-rotation@result['force_on_first_xyz_n'])),
            'rotated_couple_nmm': float(np.linalg.norm(rotated['moment_on_director_owner_xyz_nmm']-rotation@result['moment_on_director_owner_xyz_nmm'])),
            'owner_translation_work_n': float(max(abs(work[:3]))), 'owner_rotation_work_nmm': float(max(abs(work[3:]))),
            'pair_moment_nmm': float(np.linalg.norm(result['pair_spatial_moment_residual_nmm'])),
            'rotated_port_mm': float(np.linalg.norm(rp['position_xyz_mm']-(rotation@p['position_xyz_mm']+translation)))}
        require(errors['known_energy_nmm'] < gates['energy_nmm'] and errors['rotated_energy_nmm'] < gates['energy_nmm']
                and errors['rotated_force_n'] < gates['force_n'] and errors['owner_translation_work_n'] < gates['force_n']
                and max(errors['rotated_couple_nmm'], errors['owner_rotation_work_nmm'], errors['pair_moment_nmm']) < gates['moment_nmm']
                and errors['rotated_port_mm'] < gates['position_mm'], 'known-answer work/objectivity gate failed')
        records.append({'axial_slip_mm': axial, 'lateral_slip_mm': .2, 'known_energy_nmm': expected, 'errors': errors})
    return first, {'common_rigid_position_error_mm': float(rigid_error), 'zero_reference_energy_nmm': rest['energy_nmm'],
                   'zero_common_rigid_energy_nmm': rigid['energy_nmm'], 'slip_controls': records}


def run(reference):
    pins = {}; remaining = bootstrap(pins); gravity = remaining.bootstrap(pins); contact = gravity.bootstrap(pins)
    material = contact.bootstrap(pins); prior = material.bootstrap(pins); boot = prior.bootstrap(pins); base = boot.producer(pins)
    inputs = json.loads(base.captured(reference, pins))
    require(inputs['schema'] == 'eoere_panel_bulk_coupling_inputs/v1' and inputs['actual_observations'] is None
            and inputs['structural_acceptance'] is False and inputs['extra_grid'] is False
            and inputs['geometry_revision'] == 'eoere-raised-kicker-screws-v1'
            and inputs['hardware_revision'] == 'eoere-selected-purchase-hardware-v1', 'current numerical interface-only scope required')
    for source in inputs['execution_sources']: base.captured(source, pins)
    require(pins.get(str(OWN.relative_to(ROOT))) == LOADED_SHA, 'exact executing interface checker required')
    parent = json.loads(base.captured(inputs['remaining_load_work'], pins))
    for path, digest in parent['source_sha256'].items(): base.captured({'path': path, 'sha256': digest}, pins)
    require(parent['inventory']['timber_metal_share_loads'] == 66
            and parent['complete_coupled_contact_fracture_law_or_evaluation_ready'] is False, 'same incomplete load-work stage required')
    runtime = boot.check_runtime(parent['runtime']); api = methods(inputs, base, pins)
    gates = inputs['control_gates']
    require(gates == {'position_mm': 1e-8, 'energy_nmm': 1e-6, 'force_n': 1e-6, 'moment_nmm': 1e-5}, 'fixed numerical method gates required')
    first_field = None; manifest = None; bindings = []
    for case in parent['cases']:
        field = json.loads(base.captured(case['binding']['field'], pins))
        require(field['case_id'] == case['binding']['case_id'] and field['state_id'] == case['binding']['state_id'], 'same own six source identities required')
        own = field['source_inputs']
        bundle = field['operator_bundle']; saved = json.loads(base.captured(bundle['manifest'], pins))
        if first_field is None: first_field, manifest = field, saved
        require(own['hillman_rows'] == first_field['source_inputs']['hillman_rows']
                and saved['coordinate_map']['panels'] == manifest['coordinate_map']['panels'], 'same current axes and panel spaces in all cases required')
        bindings.append(case['binding'])
    panels, embeddings = {}, {}
    for name, descriptor in manifest['coordinate_map']['panels'].items(): panels[name], embeddings[name] = panel_adapter(descriptor, api)
    axes = {row['id']: row for row in first_field['source_inputs']['hillman_rows']}
    require(len(axes) == 66 and len(panels) == 6 and len(bindings) == 6, 'complete retained panel/axis/case census required')
    rows = []
    for cube in parent['common_timber_gravity_cubes']:
        screw = axes[cube['axis_id']]; center = cube['source_load']['point_xyz_mm']
        require(screw['second'] == cube['source_load']['body'] and screw['first'] in panels
                and cube['geometry_support']['inside'] is True, 'own contained finished-timber receiver required')
        first, coupons = controls(panels[screw['first']], screw, np.asarray(center), api, gates)
        target = first['reference_position_xyz_mm'].tolist()
        definitions = [bulk_definition(center, target, spread) for spread in cube['spread_scenarios']]
        rows.append({'axis_id': screw['id'], 'panel': screw['first'], 'receiver': screw['second'],
            'source_screw': screw, 'source_cube_load_id': cube['source_load']['id'], 'source_geometry_support': cube['geometry_support'],
            'runtime_reference_target_xyz_mm': target,
            'reference_target_minus_source_point_xyz_mm': (np.asarray(target)-screw['point_xyz_mm']).tolist(),
            'bulk_port_spread_scenarios': definitions, 'method_controls': coupons})
    require({row['axis_id'] for row in rows} == set(axes), 'all retained axes exactly once required')
    for path, digest in tuple(pins.items()): base.captured({'path': path, 'sha256': digest}, pins)
    return {'schema': 'eoere_panel_bulk_coupling/v1', 'inputs': reference, 'source_sha256': pins, 'runtime': runtime,
        'geometry_revision': inputs['geometry_revision'], 'hardware_revision': inputs['hardware_revision'], 'extra_grid': False,
        'inventory': {'panels': 6, 'timber_receivers': len({row['receiver'] for row in rows}), 'screw_axes': 66, 'bolt_axes_unchanged': 100,
                      'receiver_port_spread_scenarios': sum(len(row['bulk_port_spread_scenarios']) for row in rows)},
        'case_source_bindings_only': bindings, 'runtime_panel_embeddings': embeddings, 'interfaces': rows,
        'ring_quadrature': {'radial_order': 4, 'angular_order': 24, 'nodes_weights_from_scalar_closed_radicals': [a.tolist() for a in closed_gauss4(4)],
                            'old_eigensolver_bits_not_asserted_identical': True},
        'law_and_limits': inputs['law_and_limits'], 'primary_method': inputs['primary_method'],
        'bounded_objective_numerical_panel_bulk_screw_work_defined': True,
        'saved_linear_panel_load_or_generalized_correction_replaced': False,
        'new_candidate_response_equilibrium_native_frame_solve_inverse_factorization_or_CAD': False,
        'complete_coupled_contact_fracture_law_or_evaluation_ready': False,
        'physical_stiffness_restraint_demand_or_complete_resistance_qualified': False,
        'panel_screw_exceedances_deferred': True, 'actual_observations': None, 'structural_acceptance': False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--inputs', type=Path, required=True); parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args(); require(not args.out.exists(), 'preserve issued interface evidence')
    reference = {'path': str(args.inputs.resolve().relative_to(ROOT)), 'sha256': hashlib.sha256(args.inputs.read_bytes()).hexdigest()}
    result = run(reference); args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open('x') as stream:
        json.dump(result, stream, indent=2, sort_keys=True); stream.write('\n')
    print(json.dumps({'output': str(args.out), 'screw_interfaces': len(result['interfaces']), 'spread_scenarios': 198}))


if __name__ == '__main__':
    main()
