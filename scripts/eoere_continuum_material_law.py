"""Define and check a finite-kinematics bulk law for the retained assembly.

This supplies constitutive inputs and exact material controls, not a component
or frame response, an assembled contact model, or a resistance qualification.
"""
from __future__ import annotations

import argparse
import ast
import hashlib
import json
from fractions import Fraction as F
from pathlib import Path
from types import ModuleType

ROOT = Path(__file__).resolve().parents[1]
OWN = Path(__file__).resolve()
LOADED_SHA = hashlib.sha256(OWN.read_bytes()).hexdigest()
BOOT = {'path': 'scripts/eoere_mixed_shaft_projection_limit.py',
        'sha256': '9a8ced955420f2c092ffc0724847440a9d0413e493ebefa679fa8a2f3610a64e'}


def require(ok, message):
    if not ok:
        raise ValueError(message)


def bootstrap(pins):
    data = (ROOT/BOOT['path']).read_bytes()
    require(hashlib.sha256(data).hexdigest() == BOOT['sha256']
            and pins.get(BOOT['path'], BOOT['sha256']) == BOOT['sha256'], 'frozen material bootstrap changed')
    pins[BOOT['path']] = BOOT['sha256']
    module = ModuleType('_eoere_verified_continuum_bootstrap'); module.__file__ = str(ROOT/BOOT['path'])
    exec(compile(data, module.__file__, 'exec'), module.__dict__)  # noqa: S102 - verified source buffer
    return module


def matrix3(values):
    require(len(values) == 3 and all(len(row) == 3 for row in values), 'three-by-three tensor required')
    return [[F(v) for v in row] for row in values]


def transpose(values):
    return list(map(list, zip(*values, strict=True)))


def multiply(first, second):
    first, second = matrix3(first), matrix3(second)
    return [[sum((first[i][k]*second[k][j] for k in range(3)), F(0)) for j in range(3)] for i in range(3)]


def determinant(values):
    (a, b, c), (d, e, f), (g, h, i) = matrix3(values)
    return a*(e*i-f*h)-b*(d*i-f*g)+c*(d*h-e*g)


def compliance(constants):
    """Engineering strains (11,22,33,12,13,23); reciprocal orthotropic law."""
    require(len(constants) == 9 and all(type(v) is not bool for v in constants), 'nine nonboolean constants required')
    e1, e2, e3, n12, n13, n23, g12, g13, g23 = map(F, constants)
    require(min(e1, e2, e3, g12, g13, g23) > 0, 'positive elastic moduli required')
    result = [[F(0) for _ in range(6)] for _ in range(6)]
    for i, value in enumerate((e1, e2, e3, g12, g13, g23)):
        result[i][i] = 1/value
    for i, j, value in ((0, 1, -n12/e1), (0, 2, -n13/e1), (1, 2, -n23/e2)):
        result[i][j] = result[j][i] = value
    normal = [row[:3] for row in result[:3]]
    minors = [normal[0][0], normal[0][0]*normal[1][1]-normal[0][1]**2, determinant(normal)]
    require(min(minors) > 0, 'positive normal compliance principal minors required')
    return result, minors


def green_strain(deformation):
    deformation = matrix3(deformation)
    require(determinant(deformation) > 0, 'positive deformation Jacobian required')
    metric = multiply(transpose(deformation), deformation)
    return [(metric[i][i]-1)/2 for i in range(3)]+[metric[0][1], metric[0][2], metric[1][2]]


def stress_tensor(stress):
    require(len(stress) == 6, 'six symmetric stress components required')
    a, b, c, d, e, f = map(F, stress)
    return [[a, d, e], [d, b, f], [e, f, c]]


def complementary_density(stress, constants):
    require(len(stress) == 6, 'six material stresses required')
    stress = list(map(F, stress)); tensor, _ = compliance(constants)
    strain = [sum((a*b for a, b in zip(row, stress, strict=True)), F(0)) for row in tensor]
    return strain, sum((a*b for a, b in zip(stress, strain, strict=True)), F(0))/2


def mixed_density(deformation, stress, constants):
    """E(F):S - W*(S); stationary S requires E(F)=compliance*S.

    A nonstationary mixed value is not the physical strain energy.
    """
    strain, complementary = complementary_density(stress, constants)
    green = green_strain(deformation)
    value = sum((a*F(b) for a, b in zip(green, stress, strict=True)), F(0))-complementary
    return value, [a-b for a, b in zip(green, strain, strict=True)]


def first_piola(deformation, stress):
    require(determinant(deformation) > 0, 'positive deformation Jacobian required')
    return multiply(deformation, stress_tensor(stress))


def cauchy_stress(deformation, stress):
    jacobian = determinant(deformation)
    require(jacobian > 0, 'positive deformation Jacobian required')
    pushed = multiply(first_piola(deformation, stress), transpose(deformation))
    return [[v/jacobian for v in row] for row in pushed]


def literal_constants(data):
    tree = ast.parse(data)
    node, = [n.value for n in tree.body if isinstance(n, ast.Assign)
             and any(isinstance(t, ast.Name) and t.id == 'SCENARIO_CONSTANTS_MPA' for t in n.targets)]
    values = ast.literal_eval(node)
    require(type(values) is tuple and len(values) == 9, 'existing nine-constant material declaration required')
    return [F(str(v)) for v in values]


def material_frames(row):
    frame = [list(map(F, row[key])) for key in ('axis', 'section_u', 'section_v')]
    require(all(len(v) == 3 for v in frame), 'three complete material-frame axes required')
    gram = multiply(frame, transpose(frame)); tolerance = F(1, 10**10)
    require(max(abs(gram[i][j]-(i == j)) for i in range(3) for j in range(3)) <= tolerance
            and determinant(frame) > 0, 'recorded right-handed unit grain/section frame required')
    alternate = [frame[0], frame[2], [-v for v in frame[1]]]
    return {'body': row['name'], 'source_frame_lrt': [[str(v) for v in a] for a in frame],
            'swapped_frame_lrt': [[str(v) for v in a] for a in alternate],
            'growth_ring_orientation_observed': False}


def run(reference):
    pins = {}; prior = bootstrap(pins); boot = prior.bootstrap(pins); base = boot.producer(pins)
    inputs = json.loads(base.captured(reference, pins))
    require(inputs['schema'] == 'eoere_continuum_material_law_inputs/v1'
            and inputs['geometry_revision'] == 'eoere-raised-kicker-screws-v1'
            and inputs['hardware_revision'] == 'eoere-selected-purchase-hardware-v1'
            and inputs['current_bolt_count'] == 100 and inputs['current_screw_count'] == 66
            and inputs['extra_grid'] is False and inputs['actual_observations'] is None
            and inputs['structural_acceptance'] is False, 'retained geometry and input-only qualification scope required')
    for row in inputs['execution_sources']:
        base.captured(row, pins)
    require(pins.get(str(OWN.relative_to(ROOT))) == LOADED_SHA, 'exact executing material input checker required')
    source = json.loads(base.captured(inputs['retained_reaction_result'], pins))
    source_inputs = json.loads(base.captured(source['inputs'], pins)); runtime = boot.check_runtime(source_inputs['runtime'])
    require(len(source['cases']) == 6 and source['current_bolt_count'] == 100 and source['current_screw_count'] == 66
            and source['all_six_exact_original_load_dual_bounds_proven'] is True, 'six retained current case bindings required')
    legacy = literal_constants(base.captured(inputs['elastic_material_helper'], pins))
    base.captured(inputs['wood_source_note'], pins)
    base.captured(inputs['wood_source_cache'], pins)
    strength = json.loads(base.captured(inputs['retained_strength_input'], pins))
    fracture = json.loads(base.captured(inputs['retained_fracture_input'], pins))
    definitions, cases = None, []
    for binding in source['cases']:
        field = json.loads(base.captured(binding['binding']['field'], pins)); own = field['source_inputs']
        require(field['state_id'] == binding['binding']['state_id'] and field['case_id'] == binding['binding']['case_id'],
                'own unchanged six-case field binding required')
        records = {key: own[key] for key in ('geometry', 'timber_rows', 'panel_ids', 'fitting_poses', 'shafts',
            'hillman_rows', 'finished_body_observations', 'flange_shared_face_patches', 'timber_and_panel_shared_face_patches')}
        if definitions is None:
            definitions = records
        else:
            require(records == definitions, 'same retained geometry, hardware and attachment definitions in all cases required')
        cases.append(binding['binding'])
    own = definitions
    export = json.loads(base.captured(own['geometry']['cached_source_export'], pins))
    require(export['raw_gross_timber_rows'] == own['timber_rows'] and export['shafts'] == own['shafts'],
            'same recorded material/geometry source required')
    material = export['material_scenario']; scale = F(str(material['timber_e_mpa']))/legacy[0]
    wood = [v*scale if i in (0, 1, 2, 6, 7, 8) else v for i, v in enumerate(legacy)]
    steel_e = F(str(material['common_shaft_parameters']['steel_E_mpa']))
    steel_nu = F(str(material['common_shaft_parameters']['steel_nu']))
    steel_g = steel_e/(2*(1+steel_nu)); steel = [steel_e]*3+[steel_nu]*3+[steel_g]*3
    wood_compliance, wood_minors = compliance(wood); steel_compliance, steel_minors = compliance(steel)
    timber_ids = {r['name'] for r in own['timber_rows']}; panels = set(own['panel_ids'])
    fittings = {r['id'] for r in own['fitting_poses']}; bolts = {r['axis_id'] for r in own['shafts']}
    screws = {r['id'] for r in own['hillman_rows']}
    metal_roles = {r['id'] for shaft in own['shafts'] for r in shaft['metal_roles']}
    require((len(timber_ids), len(panels), len(fittings), len(bolts), len(screws), len(metal_roles)) == (22, 6, 22, 100, 66, 508),
            'complete retained owner and hardware-role census required')
    finished = {r['id']: r for r in own['finished_body_observations']}
    require(set(finished) == timber_ids | panels and len(own['flange_shared_face_patches']) == 88,
            'all own finished wood/panel sources and normal interface seeds required')
    for row in finished.values():
        base.captured(row['source'], pins)
    require(set(strength['base_strengths_mpa']) == {'tension_parallel', 'compression_parallel', 'tension_perpendicular',
            'compression_perpendicular', 'parallel_shear', 'rolling_shear'} and strength['working_strength_divisor'] == 2,
            'retained signed full-tensor reference hypothesis required')
    require(fracture['Gc_all_modes_n_per_mm'] == [0.1, 0.05], 'retained unmeasured fracture references required')
    frames = [material_frames(row) for row in own['timber_rows']]
    for path, digest in tuple(pins.items()):
        base.captured({'path': path, 'sha256': digest}, pins)
    return {'schema': 'eoere_continuum_material_law/v1', 'inputs': reference, 'runtime': runtime, 'source_sha256': pins,
        'geometry_revision': inputs['geometry_revision'], 'hardware_revision': inputs['hardware_revision'],
        'current_bolt_count': 100, 'current_screw_count': 66, 'extra_grid': False, 'case_bindings': cases,
        'wood_constants_lrt': list(map(str, wood)), 'steel_constants': list(map(str, steel)),
        'wood_engineering_compliance': [[str(v) for v in row] for row in wood_compliance],
        'steel_engineering_compliance': [[str(v) for v in row] for row in steel_compliance],
        'wood_exact_normal_principal_minors': list(map(str, wood_minors)),
        'steel_exact_normal_principal_minors': list(map(str, steel_minors)),
        'material_frames': frames, 'finished_solid_sources': [r['source'] for r in finished.values()],
        'inventory': {'timbers': 22, 'panels': 6, 'fittings': 22, 'bolt_axes': 100, 'screw_axes': 66,
            'metal_roles': 508, 'normal_interface_seeds': 88, 'material_orientation_cases': len(frames)*2},
        'retained_strengths_mpa': strength['base_strengths_mpa'], 'working_strength_divisor': 2,
        'retained_fracture_reference_n_mm': fracture['Gc_all_modes_n_per_mm'],
        'constitutive_definition': inputs['constitutive_definition'], 'interface_definition': inputs['interface_definition'],
        'remaining_assembly_and_evaluation': inputs['remaining_assembly_and_evaluation'],
        'exact_positive_bulk_compliance_verified': True, 'finite_rigid_rotation_objectivity_is_a_material_identity': True,
        'complete_assembled_joint_contact_law_evaluated': False, 'native_or_component_or_frame_response_computed': False,
        'physical_stiffness_demand_restraint_or_complete_resistance_qualified': False,
        'geometry_hardware_or_saved_force_fields_changed': False, 'panel_screw_exceedances_deferred': True,
        'actual_observations': None, 'structural_acceptance': False, 'limits': inputs['limits']}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--inputs', type=Path, required=True); parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args(); require(not args.out.exists(), 'preserve issued material-law evidence')
    reference = {'path': str(args.inputs.resolve().relative_to(ROOT)), 'sha256': hashlib.sha256(args.inputs.read_bytes()).hexdigest()}
    result = run(reference); args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open('x') as stream:
        stream.write(json.dumps(result, indent=2, sort_keys=True, allow_nan=False)+'\n')
    print(json.dumps({'path': str(args.out), 'bytes': args.out.stat().st_size,
                      'sha256': hashlib.sha256(args.out.read_bytes()).hexdigest(), 'inventory': result['inventory']}))


if __name__ == '__main__':
    main()
