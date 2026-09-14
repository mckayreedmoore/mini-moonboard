"""Run and audit the current shoe-free whole-frame elastic contact model.

Results remain conditional on the stated elastic joint and material assumptions.
A failed equilibrium, contact or interpolation audit prevents resistance acceptance.
Native solver evidence is retained in the requested output directory.
"""
import argparse
import hashlib
import json
import os
import pickle
import subprocess
from pathlib import Path

import numpy as np

from fea import horizontal_panel_frame as frame
from fea.reinforced_frame_demand import (
    active_with_friction,
    member_sections,
    repository_source_closure,
)


def source_hashes():
    paths = repository_source_closure([Path(__file__), Path('fea/current_response_model.py'),
        Path('fea/current_response_materials.py'), *Path('mini_moonboard').glob('*.py')])
    paths += [Path('pyproject.toml'), Path('uv.lock'),
        *Path('docs').glob('*reference.json')]
    return {str(p.resolve().relative_to(Path.cwd())): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}


# Imported modules are cached by Python. A long-running batch must not label
# those old definitions with a later on-disk refactor's source identity.
LOADED_SOURCE_SHA256 = source_hashes()


def physical_forces(record, result, precision=None):
    """Rotate connector-local spring forces into the physical global frame."""
    rows = {}
    radii = {}
    if precision is not None:
        for spring in record['springs']:
            first, second = spring['nodes']
            d = spring['dof']-1
            radii.setdefault(spring['name'], np.zeros(3))[d] = (
                spring['stiffness_n_per_mm']*(precision[first][d]+precision[second][d])
                if spring.get('active', True) else 0.)
    for name, owner in record['connection_ownership'].items():
        force = np.array(result['connector_forces'][name]['force_on_first_xyz_n'])
        radius = radii.get(name, np.zeros(3))
        if 'force_basis' in owner:
            radius = np.abs(np.asarray(owner['force_basis']).T) @ radius
            force = np.asarray(owner['force_basis']).T @ force
        elif 'scalar_normal' in owner:
            radius = radius[0]*np.abs(owner['scalar_normal'])
            force = force[0]*np.asarray(owner['scalar_normal'])
        row = {**owner, 'force_on_first_xyz_n': force.tolist(),
            'force_on_second_xyz_n': (-force).tolist(),
            'force_rounding_radius_xyz_n': radius.tolist()}
        if 'axis' in owner:
            axis = np.asarray(owner['axis'])
            axial = float(force @ axis)
            row.update(axial_along_installation_direction_n=axial,
                transverse_shear_n=float(np.linalg.norm(force-axial*axis)))
        rows[name] = row
    return rows


def assess(record, data, frd, expansion, *, expected_candidate='no-shoes-development'):
    if record.get('candidate') != expected_candidate or any(e[0] == 'S8' for e in record['elements'].values()):
        raise ValueError('Require the current candidate with physical layered panel solids')
    ordinary = {**record, 'springs': [dict(s, bearing_closed_assumption=False)
        if s['name'].endswith('_friction') else s for s in record['springs']]}
    result = frame.assess(ordinary, data)
    physical = physical_forces(record, result, frame.displacement_roundoff(data))
    result['physical_connection_forces'] = physical
    result['member_contacts'] = record.get('member_contacts', [])
    if 'splice_assumptions' in record:
        result['splice_assumptions'] = record['splice_assumptions']
    result['member_section_demands'] = member_sections(record, physical)
    nodes = {int(n): np.array(p) for n,p in record['nodes'].items()}
    loads = [(nodes[int(n)], np.array(f)) for n,f in record['loads'].items()]
    supports = [(np.array(c['point']), np.array(c['force_on_first_xyz_n']))
        for c in physical.values() if c['second'] == 'floor']
    force = sum((f for _,f in loads+supports), np.zeros(3))
    moment = sum((np.cross(p,f) for p,f in loads+supports), np.zeros(3))
    result['native_fixed_node_resultants'] = {k: result[k] for k in ('force_residual_n','moment_residual_nmm')}
    result.update(force_residual_n=force.tolist(), moment_residual_nmm=moment.tolist(),
        global_equilibrium_passed=bool(max(abs(force)) <= .1 and max(abs(moment)) <= 2.),
        reaction_recovery='Physical floor spring forces, including normal MPC transfer',
        floor_scope='Conditional no sliding; normal contact may open; no friction coefficient qualification')
    # Native DAT prints finite precision. Propagate its actual half-last-place
    # intervals instead of mistaking subtraction roundoff for lost equilibrium.
    result['member_equilibrium'] = {}
    for name,row in result['member_section_demands'].items():
        force_radius, moment_radius = np.zeros(3), np.zeros(3)
        start = np.asarray(row['member']['start'])
        for connection in physical.values():
            if name not in (connection['first'],connection['second']):
                continue
            radius = np.asarray(connection['force_rounding_radius_xyz_n'])
            force_radius += radius
            x,y,z = np.asarray(connection['point'])-start
            moment_radius += np.array([[0,abs(z),abs(y)],[abs(z),0,abs(x)],
                [abs(y),abs(x),0]]) @ radius
        force_error = np.maximum(0.,abs(np.asarray(row['force_residual_n']))-force_radius)
        moment_error = np.maximum(0.,abs(np.asarray(row['moment_residual_nmm']))-moment_radius)
        result['member_equilibrium'][name] = {
            'force_rounding_radius_xyz_n': force_radius.tolist(),
            'moment_rounding_radius_xyz_nmm': moment_radius.tolist(),
            'maximum_force_residual_n': max(abs(np.asarray(row['force_residual_n']))),
            'maximum_moment_residual_nmm': max(abs(np.asarray(row['moment_residual_nmm']))),
            'force_interval_distance_n': force_error.tolist(),
            'moment_interval_distance_nmm': moment_error.tolist(),
            'passed': bool(max(force_error) <= .1 and max(moment_error) <= 20.)}
    result['member_equilibrium_passed'] = all(r['passed'] for r in result['member_equilibrium'].values())
    result['member_equilibrium_criterion'] = 'Actual DAT rounding intervals intersect equilibrium within 0.1 N / 20 N mm; raw residuals retained'
    displacements = frame.panel_kernel.read_blocks(data)['displacements']
    timber_names = {row['name'] for row in record['members']}
    timber_nodes = {n for _,ids,group in record['elements'].values() if group in timber_names for n in ids}
    result['maximum_timber_displacement_mm'] = max(float(np.linalg.norm(displacements[n])) for n in timber_nodes)
    result['clearance_monitors'] = [{**monitor, 'deformed_gap_mm':
        float(np.dot(np.asarray(monitor['second_point'])-monitor['first_point']+
                     np.asarray(displacements[monitor['second_node']])-displacements[monitor['first_node']],
                     monitor['normal']))}
        for monitor in record.get('clearance_monitor_nodes', [])]
    result['sampled_unmodeled_gaps_remain_open'] = all(
        m['deformed_gap_mm'] >= 0 for m in result['clearance_monitors'])
    result['panel_displacement_scope'] = 'Physical panel midsurface translations'
    return result


def next_contact_names(bearings, strategy='all'):
    """Optionally change one normal contact per floor body to avoid bulk cycling.

    This changes the active-set search only, not stiffnesses, unilateral gates
    or the rule that tangential support requires a contacting floor body.
    """
    proposed = frame.next_bearing_set(bearings)
    if strategy == 'all':
        return proposed
    if strategy != 'one_per_floor_body':
        raise ValueError('Unknown contact update strategy')
    current = {row['name'] for row in bearings if row['active']}
    changes = {}
    for row in bearings:
        name = row['name']
        if name.startswith('floor_') and ((name in proposed) != (name in current)):
            changes.setdefault(name.rsplit('_', 1)[0], []).append(row)
    for rows in changes.values():
        selected = max(rows, key=lambda row: (abs(row['opening_mm']), row['name']))['name']
        for row in rows:
            name = row['name']
            if name != selected:
                if name in current:
                    proposed.add(name)
                else:
                    proposed.discard(name)
    return proposed


def run(output, *, cache=None, max_cycles=30, connection_scale=1., panel_group_factor=1.,
        module=None, expected_candidate='no-shoes-development', bolt_stiffness=None,
        contact_update_strategy='all', initial_contact_names=None, **parameters):
    next_contact_names([], contact_update_strategy)
    directory = Path(output)
    directory.mkdir(parents=True, exist_ok=False)
    before = source_hashes()
    if before != LOADED_SOURCE_SHA256:
        raise ValueError('Sources changed after this process imported the solver; restart from a frozen snapshot')
    if cache and (connection_scale != 1. or panel_group_factor != 1. or bolt_stiffness is not None):
        raise ValueError('Material or stiffness changes require a fresh preparation')
    if cache:
        with Path(cache).open('rb') as source:
            cached = pickle.load(source)
        if not isinstance(cached, dict) or cached.get('source_sha256') != before:
            raise ValueError('Cached model does not authenticate current producer sources')
        structure, metadata = cached['model']
        if module is not None or metadata.get('candidate') != expected_candidate:
            raise ValueError('Cached candidate must match explicit expected candidate; module requires fresh preparation')
        if parameters:
            raise ValueError('Cached model cannot be silently given new parameters')
    else:
        from fea.current_response_materials import connection_stiffnesses, materials
        from fea.current_response_model import prepare
        from mini_moonboard import no_shoes_frame
        stiffnesses = {**connection_stiffnesses(scale=connection_scale), 'floor': 1.e5, 'bearing': 1.e6, 'seating_per_area': 100.}
        if bolt_stiffness is not None:
            if any(not np.isfinite(bolt_stiffness.get(key, float('nan'))) or bolt_stiffness[key] <= 0
                   for key in ('axial_n_per_mm', 'lateral_n_per_mm')):
                raise ValueError('Explicit bolt stiffness requires positive finite axial and lateral values')
            if not bolt_stiffness.get('basis'):
                raise ValueError('Explicit bolt stiffness requires a recorded geometry/property basis')
            stiffnesses['bolt'] = dict(bolt_stiffness)
        structure, metadata = prepare(no_shoes_frame if module is None else module, expected_candidate=expected_candidate, materials=materials(panel_group_factor=panel_group_factor), stiffnesses=stiffnesses, **parameters)
    if before != source_hashes():
        raise ValueError('Consumed sources changed during preparation')
    for name,digest in before.items():
        content = Path(name).read_bytes()
        if hashlib.sha256(content).hexdigest() != digest:
            raise ValueError('Source changed before snapshot: '+name)
        target = directory/'source_snapshots'/name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(content)
    with (directory/'model.pkl').open('wb') as target:
        pickle.dump({'model': (structure,metadata), 'source_sha256': before}, target)
    active = {s['name'] for s in structure.springs if s['bearing_closed_assumption']}
    spring_names = {s['name'] for s in structure.springs}
    if initial_contact_names is not None:
        normals = set(initial_contact_names)
        if not normals <= active or any(name.endswith('_friction') for name in normals):
            raise ValueError('Initial contact inventory must contain actual normal contacts')
        active = active_with_friction(normals, spring_names, metadata['connection_ownership'])
    seen, history = set(), []
    report = {'contact_active_set_converged': False}
    for iteration in range(max_cycles):
        signature = tuple(sorted(active))
        if signature in seen:
            report['termination'] = 'Contact active set repeated without convergence'
            break
        seen.add(signature)
        job = directory/f'cycle-{iteration:02d}'
        job.mkdir()
        record = frame.record_structure(structure,metadata,active)
        (job/'input.json').write_text(json.dumps(record, indent=2)+'\n')
        (job/'frame.inp').write_text(structure.deck(active_bearings=active,stress=False).replace(
            '*END STEP','*NODE FILE,OUTPUT=3D\nU\n*END STEP'))
        command = ['docker','run','--rm','--network=none','--cpus=1','--memory=4g',
            '--user',f'{os.getuid()}:{os.getgid()}','-e','OMP_NUM_THREADS=1',
            '-v',f'{job.resolve()}:/output','-w','/output',frame.panel_kernel.IMAGE,
            'timeout','240s','ccx','-i','frame']
        native = subprocess.run(command,capture_output=True,text=True,timeout=260,check=False)
        log = native.stdout+native.stderr
        (job/'frame.log').write_text(log)
        if native.returncode or '*ERROR' in log.upper():
            raise ValueError('Native current-frame solve failed; inspect '+str(job/'frame.log'))
        report = assess(record,(job/'frame.dat').read_text(),(job/'frame.frd').read_text(),(job/'frame.12d').read_text(), expected_candidate=expected_candidate)
        (job/'report.json').write_text(json.dumps(report,indent=2,allow_nan=False)+'\n')
        history.append({'directory':job.name,'active_count':len(active),
            'contact_passed':report['closed_bearing_assumption_passed']})
        print(json.dumps({'cycle':iteration,'equilibrium':report['global_equilibrium_passed'],
            'member_equilibrium':report['member_equilibrium_passed'],
            'contacts':report['closed_bearing_assumption_passed'],
            'panel_displacement_mm':report['maximum_panel_displacement_mm']}),flush=True)
        if report['closed_bearing_assumption_passed']:
            report['contact_active_set_converged'] = True
            break
        active = active_with_friction(next_contact_names(report['bearings'], contact_update_strategy),spring_names,metadata['connection_ownership'])
    report.setdefault('contact_active_set_converged',False)
    report['contact_update_strategy'] = contact_update_strategy
    report['initial_contact_names'] = sorted(initial_contact_names) if initial_contact_names is not None else None
    report.update(candidate=metadata['candidate'],angle_stations=metadata['angle_stations'],parameters={k:metadata.get(k) for k in ('hold','pounds','force_xyz_n','standoff_from_front_mm','stiffnesses','materials','equipment_kg','frame_size_mm','panel_size_mm','leg_bolt_scale','leg_floor_grid','leg_floor_pressure_assumption','leg_joint_assumption','header_bearing_assumption')},source_sha256=before,
        contact_cycles=history,solver_image=frame.panel_kernel.IMAGE,assumptions=__doc__,qualified_for_design=False)
    report['numerically_accepted'] = all(report.get(k,False) for k in (
        'contact_active_set_converged','global_equilibrium_passed','member_equilibrium_passed','mpc_check_passed'))
    report['artifact_sha256'] = {str(p.relative_to(directory)):hashlib.sha256(p.read_bytes()).hexdigest()
        for p in directory.rglob('*') if p.is_file()}
    (directory/'report.json').write_text(json.dumps(report,indent=2,allow_nan=False)+'\n')
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--cache',type=Path)
    parser.add_argument('--hold',default='A12')
    parser.add_argument('--pounds',type=float,default=150.)
    parser.add_argument('--leg-bolt-scale',type=float,default=1.)
    parser.add_argument('--leg-floor-grid',type=int)
    args = parser.parse_args()
    if args.cache and (args.leg_bolt_scale != 1. or args.leg_floor_grid is not None):
        parser.error('Leg sensitivity changes require fresh preparation')
    result = run(args.output,cache=args.cache,**({} if args.cache else {'hold':args.hold,'pounds':args.pounds,
        'leg_bolt_scale':args.leg_bolt_scale,'leg_floor_grid':args.leg_floor_grid}))
    print(json.dumps({k:result.get(k) for k in ('numerically_accepted','contact_active_set_converged',
        'maximum_panel_displacement_mm','maximum_timber_displacement_mm')}))
