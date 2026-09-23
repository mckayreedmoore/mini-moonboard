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


def extra_source_hashes(paths):
    """Fingerprint caller-owned producer inputs omitted by the base closure."""
    root = Path.cwd().resolve()
    result = {}
    for path in paths:
        resolved = Path(path).resolve()
        try:
            relative = resolved.relative_to(root)
        except ValueError as error:
            raise ValueError('Extra producer source must be inside the repository') from error
        if not resolved.is_file():
            raise ValueError('Extra producer source is missing: '+str(relative))
        result[str(relative)] = hashlib.sha256(resolved.read_bytes()).hexdigest()
    return result


def physical_forces(record, result, precision=None):
    """Rotate connector-local spring forces into the physical global frame."""
    rows = {}
    radii = {}
    clearance_offsets = {}
    if precision is not None:
        for spring in record['springs']:
            first, second = spring['nodes']
            d = spring['dof']-1
            radii.setdefault(spring['name'], np.zeros(3))[d] += (
                spring['stiffness_n_per_mm']*(precision[first][d]+precision[second][d])
                if spring.get('active', True) else 0.)
    for spring in record.get('springs', []):
        if not spring.get('radial_clearance_assumption') or not spring.get('active', True):
            continue
        normal = spring.get('clearance_contact_normal')
        if normal is None or spring['dof'] not in (2, 3):
            raise ValueError('Active radial-clearance spring requires a two-dimensional contact normal')
        clearance_offsets.setdefault(spring['name'], np.zeros(3))[spring['dof']-1] += (
            spring['stiffness_n_per_mm'] * spring['radial_clearance_mm']
            * normal[spring['dof']-2]
        )
    owners = {**record['connection_ownership'], **record.get('radial_clearance_ownership', {})}
    for name, owner in owners.items():
        force = (np.array(result['connector_forces'][name]['force_on_first_xyz_n'])
                 - clearance_offsets.get(name, np.zeros(3)))
        radius = radii.get(name, np.zeros(3))
        if 'force_basis' in owner:
            radius = np.abs(np.asarray(owner['force_basis']).T) @ radius
            force = np.asarray(owner['force_basis']).T @ force
        elif 'scalar_normal' in owner:
            radius = radius[0]*np.abs(owner['scalar_normal'])
            force = force[0]*np.asarray(owner['scalar_normal'])
        public_name = owner.get('connector_name', name)
        clean_owner = {key: value for key, value in owner.items()
                       if key not in ('connector_name', 'radial_clearance_assumption')}
        if public_name not in rows:
            rows[public_name] = {**clean_owner,
                'force_on_first_xyz_n': np.zeros(3),
                'force_rounding_radius_xyz_n': np.zeros(3)}
        row = rows[public_name]
        if any(row.get(key) != clean_owner.get(key)
               for key in ('first', 'second', 'point', 'axis')):
            raise ValueError('Connector force components do not share physical ownership')
        row['force_on_first_xyz_n'] += force
        row['force_rounding_radius_xyz_n'] += radius
    for row in rows.values():
        force = row['force_on_first_xyz_n']
        row['force_on_first_xyz_n'] = force.tolist()
        row['force_on_second_xyz_n'] = (-force).tolist()
        row['force_rounding_radius_xyz_n'] = row['force_rounding_radius_xyz_n'].tolist()
        if 'axis' in row:
            axis = np.asarray(row['axis'])
            axial = float(force @ axis)
            row.update(axial_along_installation_direction_n=axial,
                transverse_shear_n=float(np.linalg.norm(force-axial*axis)))
    return rows


def assess(record, data, frd, expansion, *, expected_candidate='no-shoes-development'):
    if record.get('candidate') != expected_candidate or any(e[0] == 'S8' for e in record['elements'].values()):
        raise ValueError('Require the current candidate with physical layered panel solids')
    ordinary = {**record, 'springs': [dict(s, bearing_closed_assumption=False)
        if (s['name'].endswith('_friction') or s.get('tension_only_assumption')
            or s.get('radial_clearance_assumption'))
        else s for s in record['springs']]}
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
    """Optionally limit normal-contact pivots to avoid bulk cycling.

    This changes the active-set search only, not stiffnesses, unilateral gates
    or the rule that tangential support requires a contacting floor body.
    """
    proposed = frame.next_bearing_set(bearings)
    if strategy == 'all':
        return proposed
    if strategy == 'one_at_a_time':
        current = {row['name'] for row in bearings if row['active']}
        changing = [row for row in bearings if (row['name'] in proposed) != (row['name'] in current)]
        if not changing:
            return current
        selected = max(changing, key=lambda row: (abs(row['opening_mm']), row['name']))['name']
        current.symmetric_difference_update({selected})
        return current
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


def axial_tension_state(record, displacements, tolerance=1.e-7):
    """Evaluate no-preload axial gaps on the solved displacement field."""
    rows = []
    for spring in record['springs']:
        if not spring.get('tension_only_assumption'):
            continue
        first, second = spring['nodes']
        dof = spring['dof'] - 1
        extension = float(displacements[second][dof] - displacements[first][dof])
        active = spring['active']
        rows.append({'name': spring['name'], 'active': active,
                     'extension_mm': extension,
                     'tension_force_n': spring['stiffness_n_per_mm'] * extension if active else 0.,
                     'tension_only_assumption_satisfied':
                         extension >= -tolerance if active else extension <= tolerance})
    return rows


def next_axial_tension_names(rows, tolerance=1.e-7):
    return {row['name'] for row in rows if
            (row['active'] and row['extension_mm'] >= -tolerance) or
            (not row['active'] and row['extension_mm'] > tolerance)}


def radial_clearance_inventory(springs):
    """Validate coupled two-direction clearance groups and return their rows."""
    groups = {}
    for spring in springs:
        if spring.get('radial_clearance_assumption'):
            groups.setdefault(spring['name'], []).append(spring)
    for name, rows in groups.items():
        if (len(rows) != 2 or {row['dof'] for row in rows} != {2, 3}
                or len({tuple(row['nodes']) for row in rows}) != 1
                or len({row['stiffness_n_per_mm'] for row in rows}) != 1
                or len({row.get('radial_clearance_mm') for row in rows}) != 1):
            raise ValueError(name+': radial clearance requires two equal lateral springs')
        clearance = rows[0].get('radial_clearance_mm')
        if not np.isfinite(clearance) or clearance <= 0:
            raise ValueError(name+': radial clearance must be positive and finite')
    return groups


def configure_radial_clearance(structure, states, base_loads):
    """Apply balanced reference loads for one linearized radial-contact trial."""
    groups = radial_clearance_inventory(structure.springs)
    if set(states) != set(groups):
        raise ValueError('Radial-clearance state inventory changed')
    structure.loads = {node: np.asarray(force, dtype=float).copy()
                       for node, force in base_loads.items()}
    corrections = []
    for name, rows in groups.items():
        normal = states[name]
        for row in rows:
            row.pop('clearance_contact_normal', None)
        if normal is None:
            continue
        normal = np.asarray(normal, dtype=float)
        if normal.shape != (2,) or not np.isfinite(normal).all() or not np.isclose(
                np.linalg.norm(normal), 1., atol=1.e-9):
            raise ValueError(name+': engaged radial state requires a unit contact normal')
        first, second = rows[0]['nodes']
        correction = np.zeros(3)
        for row in rows:
            row['clearance_contact_normal'] = normal.tolist()
            correction[row['dof']-1] = (row['stiffness_n_per_mm']
                * row['radial_clearance_mm'] * normal[row['dof']-2])
        for node, force in ((first, -correction), (second, correction)):
            structure.loads[node] = structure.loads.get(node, np.zeros(3)) + force
        corrections.append({'name': name, 'nodes': [first, second],
            'contact_normal': normal.tolist(),
            'force_on_first_local_n': (-correction).tolist(),
            'force_on_second_local_n': correction.tolist()})
    return corrections


def radial_clearance_state(record, displacements, tolerance=1.e-7,
                           direction_force_tolerance=0.1):
    """Evaluate circular lateral gaps after one linearized native solve."""
    groups = radial_clearance_inventory(record['springs'])
    rows = []
    for name, springs in groups.items():
        active_values = {spring['active'] for spring in springs}
        normals = {tuple(spring.get('clearance_contact_normal', ())) for spring in springs}
        if len(active_values) != 1:
            raise ValueError(name+': lateral clearance directions must switch together')
        active = active_values.pop()
        if (active and (len(normals) != 1 or not next(iter(normals)))
                or not active and normals != {()}):
            raise ValueError(name+': clearance normal does not match active state')
        spring = springs[0]
        first, second = spring['nodes']
        relative = np.array([
            float(displacements[second][dof-1] - displacements[first][dof-1])
            for dof in (2, 3)
        ])
        radius = float(np.linalg.norm(relative))
        clearance = spring['radial_clearance_mm']
        current = list(next(iter(normals))) if active else None
        normal_displacement = (float(relative @ np.asarray(current))
                               if active else None)
        # An engaged bore side cannot jump directly to another side.  Loss of
        # compression releases it; only a following open trial may engage the
        # new radial direction.
        if active and normal_displacement <= clearance+tolerance:
            proposed = None
        else:
            proposed = (relative/radius).tolist() if radius > clearance+tolerance else None
        direction_error_force = (spring['stiffness_n_per_mm']*clearance
            * float(np.linalg.norm(np.asarray(current)-np.asarray(proposed)))
            if active and proposed is not None else None)
        satisfied = bool((not active and proposed is None) or
            (active and proposed is not None
             and direction_error_force <= direction_force_tolerance))
        raw_force = (spring['stiffness_n_per_mm']*relative
                     if active else np.zeros(2))
        correction = (spring['stiffness_n_per_mm']*clearance*np.asarray(current)
                      if active else np.zeros(2))
        physical = raw_force-correction
        rows.append({'name': name, 'connector_name': spring.get('connector_name'),
            'active': active, 'relative_lateral_displacement_mm': relative.tolist(),
            'radius_mm': radius, 'clearance_mm': clearance,
            'radial_overtravel_mm': radius-clearance,
            'displacement_along_stored_normal_mm': normal_displacement,
            'contact_normal': current, 'proposed_contact_normal': proposed,
            'raw_spring_force_local_n': raw_force.tolist(),
            'clearance_correction_local_n': correction.tolist(),
            'physical_force_local_n': physical.tolist(),
            'direction_error_force_n': direction_error_force,
            'radial_clearance_assumption_satisfied': satisfied})
    return rows


def next_radial_clearance_states(rows):
    return {row['name']: row['proposed_contact_normal'] for row in rows}


def initial_radial_clearance_state(radial_groups, supplied=None):
    """Validate a complete same-model checkpoint or start every gap open."""
    if supplied is None:
        return {name: None for name in radial_groups}
    if not isinstance(supplied, dict) or set(supplied) != set(radial_groups):
        raise ValueError('Initial radial-clearance checkpoint must match exact inventory')
    result = {}
    for name, normal in supplied.items():
        if normal is None:
            result[name] = None
            continue
        vector = np.asarray(normal, dtype=float)
        if vector.shape != (2,) or not np.isfinite(vector).all() or not np.isclose(
                np.linalg.norm(vector), 1., atol=1.e-9):
            raise ValueError(name+': initial radial-clearance normal must be a finite unit vector')
        result[name] = vector.tolist()
    return result


def initial_active_set(structure, metadata, initial_contact_names=None,
        initial_axial_tension_names=None):
    """Build a checkpoint active set without importing friction rows directly."""
    spring_names = {spring['name'] for spring in structure.springs}
    axial_names = {spring['name'] for spring in structure.springs
                   if spring.get('tension_only_assumption')}
    if any(spring['dof'] != 1 or not spring['bearing_closed_assumption']
           for spring in structure.springs if spring.get('tension_only_assumption')):
        raise ValueError('Tension-only axial springs must be switchable local-axis springs')
    normal_names = {spring['name'] for spring in structure.springs
                    if spring['bearing_closed_assumption']
                    and not spring.get('tension_only_assumption')
                    and not spring.get('radial_clearance_assumption')
                    and not spring['name'].endswith('_friction')}
    if initial_contact_names is not None:
        selected_normals = set(initial_contact_names)
        if not selected_normals <= normal_names:
            raise ValueError('Initial contact inventory must contain actual normal contacts')
    else:
        selected_normals = normal_names
    if initial_axial_tension_names is not None:
        selected_axials = set(initial_axial_tension_names)
        if not selected_axials <= axial_names:
            raise ValueError('Initial axial inventory must contain tension-only axial springs')
    else:
        selected_axials = axial_names
    if initial_contact_names is None and initial_axial_tension_names is None:
        active = {spring['name'] for spring in structure.springs
                  if (spring['bearing_closed_assumption']
                      and not spring.get('radial_clearance_assumption'))}
    else:
        active = active_with_friction(selected_normals, spring_names,
                                      metadata['connection_ownership']) | selected_axials
    return active, axial_names


def run(output, *, cache=None, max_cycles=30, connection_scale=1., panel_group_factor=1.,
        module=None, expected_candidate='no-shoes-development', bolt_stiffness=None,
        contact_update_strategy='all', initial_contact_names=None,
        initial_axial_tension_names=None, initial_radial_clearance_states=None,
        prepare_factory=None,
        extra_source_paths=(),
        **parameters):
    next_contact_names([], contact_update_strategy)
    directory = Path(output)
    directory.mkdir(parents=True, exist_ok=False)
    core_before = source_hashes()
    if core_before != LOADED_SOURCE_SHA256:
        raise ValueError('Sources changed after this process imported the solver; restart from a frozen snapshot')
    before = {**core_before, **extra_source_hashes(extra_source_paths)}
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
        factory = prepare if prepare_factory is None else prepare_factory
        structure, metadata = factory(no_shoes_frame if module is None else module,
            expected_candidate=expected_candidate,
            materials=materials(panel_group_factor=panel_group_factor),
            stiffnesses=stiffnesses, **parameters)
    if before != {**source_hashes(), **extra_source_hashes(extra_source_paths)}:
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
    active, axial_names = initial_active_set(structure, metadata, initial_contact_names,
        initial_axial_tension_names)
    radial_groups = radial_clearance_inventory(structure.springs)
    radial_states = initial_radial_clearance_state(
        radial_groups, initial_radial_clearance_states)
    initial_radial_states = {name: None if normal is None else list(normal)
                             for name, normal in radial_states.items()}
    active |= {name for name, normal in radial_states.items() if normal is not None}
    base_loads = {node: np.asarray(force, dtype=float).copy()
                  for node, force in getattr(structure, 'loads', {}).items()}
    spring_names = {s['name'] for s in structure.springs}
    seen, history = set(), []
    report = {'contact_active_set_converged': False}
    for iteration in range(max_cycles):
        corrections = configure_radial_clearance(structure, radial_states, base_loads)
        signature = (tuple(sorted(active)), tuple(
            (name, None if normal is None else tuple(round(value, 12) for value in normal))
            for name, normal in sorted(radial_states.items())))
        if signature in seen:
            report['termination'] = 'Contact active set repeated without convergence'
            break
        seen.add(signature)
        job = directory/f'cycle-{iteration:02d}'
        job.mkdir()
        record = frame.record_structure(structure,metadata,active)
        record['radial_clearance_reference_loads'] = corrections
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
        displacements = frame.panel_kernel.read_blocks(
            (job/'frame.dat').read_text())['displacements']
        if axial_names:
            report['axial_tension'] = axial_tension_state(
                record, displacements)
            report['axial_tension_assumption_passed'] = all(
                row['tension_only_assumption_satisfied'] for row in report['axial_tension'])
        if radial_groups:
            report['radial_clearance'] = radial_clearance_state(record, displacements)
            report['radial_clearance_assumption_passed'] = all(
                row['radial_clearance_assumption_satisfied']
                for row in report['radial_clearance'])
        (job/'report.json').write_text(json.dumps(report,indent=2,allow_nan=False)+'\n')
        history.append({'directory':job.name,'active_count':len(active),
            'contact_passed':report['closed_bearing_assumption_passed'],
            'axial_tension_active_names': sorted(active & axial_names),
            'axial_tension_passed': report.get('axial_tension_assumption_passed'),
            'radial_clearance_active_names': sorted(
                name for name, normal in radial_states.items() if normal is not None),
            'radial_clearance_states': {name: normal for name, normal
                                        in sorted(radial_states.items())},
            'radial_clearance_passed': report.get('radial_clearance_assumption_passed')})
        print(json.dumps({'cycle':iteration,'equilibrium':report['global_equilibrium_passed'],
            'member_equilibrium':report['member_equilibrium_passed'],
            'contacts':report['closed_bearing_assumption_passed'],
            'panel_displacement_mm':report['maximum_panel_displacement_mm']}),flush=True)
        if (report['closed_bearing_assumption_passed']
                and report.get('axial_tension_assumption_passed', True)
                and report.get('radial_clearance_assumption_passed', True)):
            report['contact_active_set_converged'] = True
            report['termination'] = 'Normal, axial, and radial active sets converged'
            break
        active = active_with_friction(next_contact_names(report['bearings'], contact_update_strategy),spring_names,metadata['connection_ownership'])
        if axial_names:
            active |= next_axial_tension_names(report['axial_tension'])
        if radial_groups:
            radial_states = next_radial_clearance_states(report['radial_clearance'])
            active |= {name for name, normal in radial_states.items() if normal is not None}
    report.setdefault('contact_active_set_converged',False)
    report['contact_update_strategy'] = contact_update_strategy
    report['axial_tension_active_set_converged'] = bool(
        axial_names and report['contact_active_set_converged'] and
        report.get('axial_tension_assumption_passed', False))
    report['axial_tension_names'] = sorted(axial_names)
    report['pb01_axial_law'] = metadata.get('pb01_axial_law')
    report['radial_clearance_active_set_converged'] = bool(
        radial_groups and report['contact_active_set_converged']
        and report.get('radial_clearance_assumption_passed', False))
    report['radial_clearance_names'] = sorted(radial_groups)
    report['barrel_radial_clearance_law'] = metadata.get('barrel_radial_clearance_law')
    report['initial_radial_clearance_states'] = initial_radial_states
    report['radial_clearance_states'] = {name: normal for name, normal
                                         in sorted(radial_states.items())}
    report['initial_contact_names'] = sorted(initial_contact_names) if initial_contact_names is not None else None
    report['initial_axial_tension_names'] = (sorted(initial_axial_tension_names)
        if initial_axial_tension_names is not None else None)
    report.update(candidate=metadata['candidate'],angle_stations=metadata['angle_stations'],parameters={k:metadata.get(k) for k in ('hold','pounds','force_xyz_n','standoff_from_front_mm','stiffnesses','materials','equipment_kg','frame_size_mm','panel_size_mm','leg_bolt_scale','leg_floor_grid','floor_rail_support','native_panel_cutouts','leg_floor_pressure_assumption','leg_joint_assumption','header_bearing_assumption')},source_sha256=before,
        contact_cycles=history,solver_image=frame.panel_kernel.IMAGE,assumptions=__doc__,qualified_for_design=False)
    report['numerically_accepted'] = all(report.get(k,False) for k in (
        'contact_active_set_converged','global_equilibrium_passed','member_equilibrium_passed','mpc_check_passed'))
    if axial_names:
        report['numerically_accepted'] &= report['axial_tension_active_set_converged']
    if radial_groups:
        report['numerically_accepted'] &= report['radial_clearance_active_set_converged']
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
