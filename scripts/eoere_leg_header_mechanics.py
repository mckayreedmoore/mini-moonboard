"""Fresh conditional response for the composed leg/header/plywood revision.

Reuse cached-solid extraction and the existing four-port/common-shaft factory.
The only constitutive addition is an explicit per-mode plywood beam operator;
it is supplied separately and never inherits the DF-L stock modulus.
"""

from __future__ import annotations

import argparse
import ast
import copy
import json
from pathlib import Path
from unittest.mock import patch

import numpy as np
from scipy.sparse import coo_matrix

from scripts import eoere_current_response as response
from scripts.eoere_current_shop_followup import ROOT, module, require, sha

OWN = Path(__file__).resolve()
SCHEMA = 'eoere_leg_header_current_first_order_inputs/v1'
TRIAL = Path('fea/generated/selected-hardware-followup-v1/panel98-current-v1')
MATERIAL = Path('docs/bolted-frame-development/plywood-cleat-operator-scenario-v1.json')


def write(path, value):
    with Path(path).open('x') as stream:
        json.dump(value, stream, sort_keys=True, indent=2, allow_nan=False)
        stream.write('\n')


def changed_function(owner, name, replacements, namespace=None):
    """Retain a pinned generic function, changing explicit inventory constants."""
    tree = ast.parse(Path(owner.__file__).read_bytes())
    node = copy.deepcopy(next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == name))
    counts = dict.fromkeys(replacements, 0)
    for part in ast.walk(node):
        if isinstance(part, ast.Constant) and type(part.value) is int and part.value in replacements:
            before = part.value
            part.value = replacements[before]
            counts[before] += 1
    require(all(counts.values()), 'explicit census hook missing: '+name)
    ns = {**vars(owner), **(namespace or {})}
    exec(compile(ast.fix_missing_locations(ast.Module(body=[node], type_ignores=[])), str(OWN), 'exec'), ns)  # noqa: S102 -- authenticated fixed-function AST; inventory-only edits
    return ns[name], counts


def prepare(geometry_path, out):
    require(not out.exists(), 'fresh preparation required')
    geometry = json.loads(geometry_path.read_bytes())
    require(geometry['revision'] == 'eoere-single-leg-bolts-header-angles-v3', 'own geometry required')
    old, _, _, _, pins = response.current_metadata()
    pins.update({str(geometry_path.relative_to(ROOT)): sha(geometry_path),
                 str(OWN.relative_to(ROOT)): sha(OWN), str(MATERIAL): sha(ROOT/MATERIAL)})
    material = json.loads((ROOT/MATERIAL).read_bytes())
    pins.update(material['source_sha256'])
    p = copy.deepcopy(old)
    exporter = response.load('cached_exporter')
    ex, m = exporter.a.generic()
    axes = geometry['axes']
    from scripts.eoere_leg_header_revision import verify_attachment_axes
    verify_attachment_axes(axes)
    profiles = copy.deepcopy(geometry['profiles'])
    sources = {name: copy.deepcopy(r['finished']) for name, r in profiles.items()}
    for row in sources.values():
        box = row.get('bounds_xyz_mm')
        if box and len(box) == 6:
            row['bounds_xyz_mm'] = [box[i:i+2] for i in (0, 2, 4)]
        pins[row['path']] = row['sha256']
    for row in p['raw_gross_timber_rows']:
        name = row['name']
        if name.startswith(('base_post_outer_', 'eoere_cleat_')):
            g = profiles[name]
            raw = {'member': name, 'datum_xyz_mm': g['datum_xyz_mm'],
                   'basis_grain_u_v_xyz': g['basis_grain_u_v_xyz'],
                   'raw_profile_vertices_luv_mm': g['vertices_luv_mm'],
                   'actual_material_observed': False}
            row.update(ex.gross_row(raw, m))
            if name.startswith('eoere_cleat_'):
                row['stiffness_scenario'] = 'explicit_APA_plywood_per_mode_operator_required'
    gross = {r['name']: r for r in p['raw_gross_timber_rows']}
    poses = geometry['fitting_poses']
    report = {'axes': axes, 'scenario': response.read({'path': ex.REPORT, 'sha256': ex.REPORT_SHA})['scenario'],
              'finished_solids': [sources[name] for name in gross]}
    panels = [sources[r['id']] for r in old['physical_owner_gravity_rows'] if r['kind'] == 'panel']
    require(len(panels) == 6, 'six current panels required')
    out.mkdir(parents=True)
    (out/'producer-snapshot.py').write_bytes(OWN.read_bytes())
    q = ex.load_query_methods(pins)
    bodies, observations, import_proof = exporter.import_current(ex, report, panels, pins, q)
    role_original, ends_original = ex.role_rows, ex.end_seats
    shaft_function, edits = changed_function(ex, 'shafts', {100: 96, 120: 112, 88: 96}, {
        'role_rows': lambda a, method, volumes: response.spacer_roles(a, method, volumes, role_original),
        'end_seats': lambda a, surfaces, method: response.spacer_ends(a, surfaces, method, ends_original)})
    require(edits == {100: 1, 120: 1, 88: 1}, 'one shaft census edit required')
    with patch.object(ex, 'role_rows', lambda a, method, volumes: response.spacer_roles(a, method, volumes, role_original)), \
            patch.object(ex, 'end_seats', lambda a, surfaces, method: response.spacer_ends(a, surfaces, method, ends_original)):
        shafts, walls = shaft_function(report, gross, bodies, q, m)
    print('Fresh96 shafts/112 receiver walls extracted', flush=True)
    panel_ids = [r['id'] for r in panels]
    patches, direct, pair_census, faces = ex.contact_bank(bodies, sorted(gross), panel_ids, q, p['parameters'])
    domains, flange_patches, flange_contacts = ex.flange_bank(poses, report, bodies, faces, q, m, p['parameters'])
    ports = [{'angle_id': a['angle_id'], 'axis_id': axis['id'], 'entry_xyz_mm': a['point'],
              'model_port_id': ex.port_id(a['flange'], a['transverse']),
              'source_flange': a['flange'], 'source_transverse': a['transverse']}
             for axis in axes for a in axis['attachments']]
    holes = copy.deepcopy(old['all_factory_holes'])
    from scripts.eoere_bolted_candidate import Scenario
    for pose in geometry['new_header_angles']:
        rows = []
        for hole in Scenario().holes(active_only=False):
            beam = hole['flange'] == 'beam'
            along, normal = (pose['u_xyz'], pose['v_xyz']) if beam else (pose['v_xyz'], pose['u_xyz'])
            point = [pose['origin_xyz_mm'][j]+along[j]*hole['along_mm']
                     +pose['w_xyz'][j]*hole['transverse_mm']+normal[j]*3.175 for j in range(3)]
            binding = [r for r in ports if r['angle_id'] == pose['id'] and
                       r['source_flange'] == hole['flange'] and r['source_transverse'] == hole['transverse']]
            rows.append({'id': pose['id']+'.'+hole['flange']+'.'+hole['row']+'.'+str(hole['transverse']),
                         'flange': hole['flange'], 'row': hole['row'], 'transverse': hole['transverse'],
                         'point_xyz_mm': point, 'direction_xyz': [-v for v in normal],
                         'installed_bolt_axis_id': binding[0]['axis_id'] if hole['row'] == 'far' else None})
        holes.append({'angle_id': pose['id'], 'holes': rows})
    footprints = copy.deepcopy(old['floor_observations'])
    footprints = {r['host']: r['normal_reference_points_xyz_mm'] for r in footprints}
    require(len(footprints) == 8 and all(bodies[name].isInside(q.cq.Vector(*point), 1e-5)
            for name, points in footprints.items() for point in points), 'retained floor point outside current solid')
    owners = [{'id': r['id'], 'kind': 'panel' if r['id'] in panel_ids else 'timber',
               'mass_kg': r['volume_mm3']*500e-9, 'center_xyz_mm': r['center_xyz_mm'],
               'mass_basis': 'own finished volume; declared500kg/m3 nominal wood/plywood scenario, not a material bound'}
              for r in observations]
    fitting_mass = next(r['mass_kg'] for r in old['physical_owner_gravity_rows'] if r['kind'] == 'fitting')
    owners.extend({'id': pose['id'], 'kind': 'fitting', 'mass_kg': fitting_mass,
                   'center_xyz_mm': ex.fitting_centroid(report['scenario'], pose, m)} for pose in poses)
    for shaft in shafts:
        mass = sum(r['mass_kg'] for r in shaft['metal_roles'])
        owners.append({'id': shaft['body'], 'kind': 'shaft', 'mass_kg': mass,
                       'center_xyz_mm': [sum(r['mass_kg']*r['center_of_mass_xyz_mm'][j] for r in shaft['metal_roles'])/mass for j in range(3)]})
    roles = [{'id': r['id'], 'owner': shaft['body'], 'mass_kg': r['mass_kg'],
              'center_xyz_mm': r['center_of_mass_xyz_mm'], 'basis': r['basis']}
             for shaft in shafts for r in shaft['metal_roles']]
    require(len(owners) == 148 and len(ports) == len(domains) == 96 and len(roles) == 496,
            'exact combined owner/port/role census required')
    b = response.load('bridge').frozen()
    cases_module = b.load(b.PACKET/'raised-rail-cases-v1/cases.py', b.REUSED['raised-rail-cases-v1/cases.py'], 'leg_header_cases')
    cases, gravity = cases_module.frame.load_cases({'panel_machining': p['current_panel_machining_descriptors']},
        {'bodies': [r for r in owners if r['kind'] != 'shaft'],
         'bolt_gravity_components': roles+p['auxiliary_metal_gravity_descriptors']})
    cases = [r for r in cases if r['primary_load_basis'] and r['case_id'] != 'gravity-only']
    for case in cases:
        for row in case['loads']:
            if row['id'].startswith('bolt-weight/') and row['body'].startswith('shaft/'):
                row['id'] = 'physical-bolt-metal/'+row['id'].removeprefix('bolt-weight/')
    centroidal = b.driver.load(b.driver.CENTROIDAL, b.driver.CENTROIDAL_SHA, 'leg_header_centroidal')
    scenario = copy.deepcopy(p['material_scenario'])
    scenario.update(fitting_stiffness_basis=centroidal.SCENARIO, fitting_operator_correction=centroidal.correction_contract(),
                    plywood_stiffness_basis='separate explicit per-mode plywood operator required at execution')
    data = {'schema': SCHEMA, 'trial_screws': 66, 'source_sha256': pins,
            'geometry': {'path': str(geometry_path.relative_to(ROOT)), 'sha256': sha(geometry_path)},
            'plywood_material': {'path': str(MATERIAL), 'sha256': sha(ROOT/MATERIAL)},
            'optional_2026_extra': False, 'parameters': p['parameters'], 'scenario': scenario,
            'timber_rows': list(gross.values()), 'base_bodies': [r for r in owners if r['kind'] != 'shaft'],
            'physical_owner_gravity_rows': owners, 'fitting_poses': poses, 'all_factory_holes': holes,
            'factory_holes': [{**h, 'angle_id': r['angle_id'], 'used': h['installed_bolt_axis_id'] is not None} for r in holes for h in r['holes']],
            'fitting_port_bindings': ports, 'shafts': shafts, 'panel_ids': panel_ids, 'floor_footprints': footprints,
            'cases': cases, 'case': cases[0], 'gravity': gravity, 'finished_receiver_wall_queries': walls,
            'finished_body_observations': observations, 'direct_contacts': direct+flange_contacts,
            'hillman_rows': p['hillman_rows'], 'current_panel_machining_descriptors': p['current_panel_machining_descriptors'],
            'flange_domains': domains, 'flange_shared_face_patches': flange_patches,
            'timber_and_panel_shared_face_patches': patches, 'shared_pair_query_census': pair_census,
            'historical_q': None, 'old_field': None, 'release': copy.deepcopy(p['release'])}
    for path, digest in pins.items():
        require(sha(ROOT/path) == digest, 'source changed during preparation: '+path)
    write(out/'inputs.json', data)
    write(out/'preparation.json', {'schema': 'eoere_leg_header_current_preparation/v1',
          'input': {'path': str((out/'inputs.json').relative_to(ROOT)), 'sha256': sha(out/'inputs.json')},
          'import_proof': import_proof, 'fresh_bore_wall_queries': len(walls), 'contacts': len(direct+flange_contacts),
          'owners': len(owners), 'fitting_ports': len(ports), 'cases': len(cases),
          'native_FEA_performed': False, 'strength_accepted': False})
    print(json.dumps({'input': str(out/'inputs.json'), 'cases': len(cases), 'contacts': len(direct+flange_contacts)}), flush=True)


def plywood_local(frame, length, properties):
    """Assemble six independent modes using the established beam blocks."""
    ea, eiy, eiz, gau, gav, gj = (properties[k] for k in ('EA_N', 'EI_y_Nmm2', 'EI_z_Nmm2', 'GA_u_N', 'GA_v_N', 'GJ_Nmm2'))
    require(min(ea, eiy, eiz, gau, gav, gj) > 0, 'positive explicit plywood properties required')
    kappa = properties['shear_factor']
    result = np.zeros((12, 12))
    for indexes, ga in (((0, 6, 3, 9, 1, 5, 7, 11), gau), ((2, 4, 8, 10), gav)):
        block = frame.beam_stiffness(length, ea, eiy, eiz, gj*ea/ga, 1., ga/ea, shear_factor=kappa)
        result[np.ix_(indexes, indexes)] = block[np.ix_(indexes, indexes)]
    return result


def replace_plywood(assembly, frame, properties):
    rows, cols, values = [], [], []
    for name in ('eoere_cleat_left', 'eoere_cleat_right'):
        for element in assembly.members[name]['elements']:
            local = plywood_local(frame, float(np.linalg.norm(element['end']-element['start'])), properties)
            current = element['T'].T@local@element['T']
            delta = current-element['K']
            i, j = np.nonzero(delta)
            rows.extend(element['dofs'][i]); cols.extend(element['dofs'][j]); values.extend(delta[i, j])
            element.update(K=current, local_K=local)
        assembly.members[name]['source']['explicit_plywood_operator'] = copy.deepcopy(properties)
    assembly.K += coo_matrix((values, (rows, cols)), shape=assembly.K.shape).tocsr()


def validator(factory, count):
    _validate, edits = changed_function(factory, 'validate_rows', {150: 148, 100: 96, 176: 192, 88: 96, 500: 496}, {'SCHEMA': SCHEMA})
    require(edits == {150: 1, 100: 1, 176: 1, 88: 3, 500: 1}, 'known combined census hooks required')
    tree = ast.parse(Path(factory.__file__).read_bytes())
    node = copy.deepcopy(next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'validate_rows'))
    changes = {'bodies': 0, 'roles': 0, 'screws': 0}
    for part in ast.walk(node):
        if isinstance(part, ast.Constant) and type(part.value) is int and part.value in {150, 100, 176, 88, 500}:
            part.value = {150: 148, 100: 96, 176: 192, 88: 96, 500: 496}[part.value]
        if isinstance(part, ast.Tuple) and ast.unparse(part) == '(22, 22, 96, 6, 148)':
            part.elts[1].value = 24
            changes['bodies'] += 1
        if isinstance(part, ast.Compare) and ast.unparse(part.left) == "len(row['metal_roles'])":
            part.ops = [ast.In()]
            part.comparators = [ast.Tuple(elts=[ast.Constant(5), ast.Constant(6)], ctx=ast.Load())]
            changes['roles'] += 1
        if isinstance(part, ast.Compare) and ast.unparse(part.left) == "len(data['hillman_rows'])":
            part.comparators[0].value = count
            changes['screws'] += 1
    # ast.walk visits the tuple before its children, so match its original
    # body census if the numerical replacement above has not reached it yet.
    if not changes['bodies']:
        for part in ast.walk(node):
            if isinstance(part, ast.Tuple) and ast.unparse(part) == '(22, 22, 96, 6, 148)':
                part.elts[1].value = 24
                changes['bodies'] += 1
    require(changes == {'bodies': 1, 'roles': 1, 'screws': 1}, 'three explicit combined inventory hooks required')
    ns = {**vars(factory), 'SCHEMA': SCHEMA}
    exec(compile(ast.fix_missing_locations(ast.Module(body=[node], type_ignores=[])), str(OWN), 'exec'), ns)  # noqa: S102 -- authenticated fixed-function AST; inventory-only edits
    return ns['validate_rows']


def run(input_path, material_path, case, out):
    material = json.loads(material_path.read_bytes())
    data = json.loads(input_path.read_bytes())
    require(data['plywood_material'] == {'path': str(material_path.relative_to(ROOT)), 'sha256': sha(material_path)},
            'input must bind the exact plywood material scenario')
    require(material['physical_qualification'] is False, 'declared conditional plywood scenario required')
    for path, digest in material['source_sha256'].items():
        require(sha(ROOT/path) == digest, 'plywood material source changed')
    trial_path = TRIAL/'run_mechanics.py'
    trial = module(trial_path, 'leg_header_existing_trial_runner')
    b = response.load('bridge').frozen()
    init = b.factory.frame.ElasticAssembly.__init__

    def initialize(assembly, *args, **kwargs):
        init(assembly, *args, **kwargs)
        replace_plywood(assembly, b.factory.frame, material['properties'])

    with patch.object(trial, 'SCHEMA', SCHEMA), patch.object(trial, 'validator', validator), \
            patch.object(b.factory.frame.ElasticAssembly, '__init__', initialize):
        result = trial.run(input_path, case, out)
    write(out/'plywood-operator.json', {'material': {'path': str(material_path.relative_to(ROOT)), 'sha256': sha(material_path)},
          'adapter': {'path': str(OWN.relative_to(ROOT)), 'sha256': sha(OWN)},
          'properties': material['properties'], 'physical_qualification': False,
          'scope': 'Current conditional first-order field; shear/torsion and joint/floor priors remain hypotheses'})
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='action', required=True)
    pre = sub.add_parser('prepare')
    pre.add_argument('geometry', type=Path)
    pre.add_argument('out', type=Path)
    solve = sub.add_parser('run')
    solve.add_argument('input', type=Path)
    solve.add_argument('material', type=Path)
    solve.add_argument('case')
    solve.add_argument('out', type=Path)
    args = parser.parse_args()
    if args.action == 'prepare':
        prepare(args.geometry.resolve(), args.out.resolve())
    else:
        import fcntl
        import signal
        with (ROOT/'docs/wood-joints-mvp/luna-max-native-run-ledger.lock').open('a') as lock:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            require(json.loads((ROOT/'docs/wood-joints-mvp/luna-max-native-run-ledger.json').read_bytes())['slot']['state'] == 'idle',
                    'parent serialized execution slot must be idle')
            signal.signal(signal.SIGALRM, lambda *_: (_ for _ in ()).throw(TimeoutError('900-second case limit')))
            signal.alarm(900)
            try:
                run(args.input.resolve(), args.material.resolve(), args.case, args.out.resolve())
            finally:
                signal.alarm(0)
