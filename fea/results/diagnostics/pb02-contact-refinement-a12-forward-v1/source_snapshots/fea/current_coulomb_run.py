"""Native frame iteration with an explicit finite-Coulomb floor scenario.

This changes the former switched no-slip support law. Each floor cell has elastic
initial tangential resistance capped by mu times its own positive normal
reaction at the same physical point. It is a monotonic, zero-initial-slip scenario, not a cyclic friction
history or measured floor qualification. Normal contact and numerical gates
remain unchanged. Convergence alone does not qualify member resistance.
"""
import hashlib
import json
import math
import os
import pickle
import subprocess
from pathlib import Path

import numpy as np

from fea import current_response_run as base
from fea.contact_energy_search import normal_energy_step
from fea.current_response_materials import connection_stiffnesses, materials
from fea.current_response_model import prepare
from fea.floor_recess_mesh import prepare_recess


def sources():
    result = base.source_hashes()
    for source in base.repository_source_closure([Path(__file__)]):
        path = source.relative_to(Path.cwd())
        result[str(path)] = hashlib.sha256(source.read_bytes()).hexdigest()
    return result


LOADED_SOURCES = sources()


def coulomb_secant(slip_xy_mm, normal_n, mu, elastic_n_per_mm):
    """Return restoring force and secant for a circular elastic-slip force cap."""
    slip = np.asarray(slip_xy_mm, dtype=float)
    if (slip.shape != (2,) or not np.all(np.isfinite(slip))
            or not all(math.isfinite(x) for x in (normal_n, mu, elastic_n_per_mm))
            or normal_n < 0 or mu <= 0 or elastic_n_per_mm <= 0):
        raise ValueError('Require finite slip, nonnegative normal and positive mu/stiffness')
    bound = mu*normal_n
    magnitude = float(np.linalg.norm(slip))
    stiffness = min(elastic_n_per_mm, bound/magnitude) if magnitude else elastic_n_per_mm
    if normal_n == 0:
        stiffness = 0.
    return -stiffness*slip, stiffness



def distribute_floor_tangents(structure, metadata):
    """Replace centroid shear springs with collocated per-normal-cell springs.

    Reuse each normal's physical wood/ground attachment; scalar normal
    auxiliary nodes themselves must never receive physical X/Y shear loads.
    Per-cell tangent stiffness follows the normal tributary fraction, preserving
    the former total elastic tangent stiffness per body when all cells stick.
    """
    owners = metadata['connection_ownership']
    old = {row['name']:row for row in structure.springs if row['name'].endswith('_friction')}
    if not old:
        raise ValueError('Require original centroid floor tangent springs')
    elastic_by_body = {owners[name]['first']:row['stiffness_n_per_mm'] for name, row in old.items()}
    normal_springs = {row['name']:row for row in structure.springs
        if row['bearing_closed_assumption'] and row['name'] not in old
        and owners[row['name']]['second'] == 'floor'}
    projection = {terms[0][0]:terms for terms in structure.equations
                  if terms and terms[0][1:] == (1, 1.)}
    cells, totals = {}, {}
    for name, spring in normal_springs.items():
        owner = owners[name]
        if owner.get('scalar_normal') != [0.,0.,1.]:
            raise ValueError('Distributed floor tangents require global-Z normal cells')
        terms = projection.get(spring['nodes'][0], ())
        if len(terms) != 2 or terms[1][1:] != (3, -1.):
            raise ValueError('Cannot identify actual physical wood node of floor normal')
        wood = terms[1][0]
        ground = owner['ground_node']
        fraction = owner['normal_stiffness_fraction']
        body = owner['first']
        if body not in elastic_by_body or not math.isfinite(fraction) or fraction <= 0:
            raise ValueError('Require positive tributary cell fraction and original body stiffness')
        totals[body] = totals.get(body, 0.)+fraction
        cells[name+'_friction'] = {'normal_contact':name, 'body':body, 'wood_node':wood,
            'ground_node':ground, 'point_xyz_mm':list(owner['point']),
            'tributary_fraction':fraction, 'elastic_tangent_n_per_mm':elastic_by_body[body]*fraction}
    if set(totals) != set(elastic_by_body) or any(not math.isclose(value,1.,abs_tol=1.e-10) for value in totals.values()):
        raise ValueError('Every original floor body requires complete unit-sum normal cells')
    next_element = max(structure.elements, default=0)+1
    next_group = max((int(row['group'][3:]) for row in structure.springs), default=0)+1
    for spring in list(structure.springs):
        if spring['name'] in old:
            del structure.elements[spring['element']]
            del structure.groups[spring['group']]
    structure.springs = [row for row in structure.springs if row['name'] not in old]
    for name in old:
        del owners[name]
    # Structure allocates spring groups/elements from collection lengths. Old
    # centroid deletions leave holes, so allocate new native identifiers above
    # the retained maxima rather than colliding with later existing elements.
    for name, cell in cells.items():
        for dof in (1,2):
            group = f'SPR{next_group}'
            structure.elements[next_element] = ('SPRING2',[cell['wood_node'],cell['ground_node']],group)
            structure.groups[group] = [next_element]
            structure.springs.append({'name':name,'element':next_element,'group':group,
                'nodes':[cell['wood_node'],cell['ground_node']], 'dof':dof,
                'stiffness_n_per_mm':cell['elastic_tangent_n_per_mm'], 'bearing_closed_assumption':True})
            next_element += 1
            next_group += 1
        owners[name] = {'first':cell['body'],'second':'floor','point':cell['point_xyz_mm'],
                        'normal_contact':cell['normal_contact'],'tributary_fraction':cell['tributary_fraction']}
    metadata['floor_tangent_cells'] = cells
    metadata['floor_tangent_distribution'] = 'Collocated with each actual normal cell; no centroid tangent springs'
    return cells


def floor_law_check(record, data, report, mu, elastic, tolerance_n=.01):
    """Recover cell slip and enforce its own normal-reaction friction cap."""
    displacement = base.frame.panel_kernel.read_blocks(data)['displacements']
    rows = {}
    physical = report['physical_connection_forces']
    for name, original in elastic.items():
        springs = [row for row in record['springs'] if row['name'] == name]
        if len(springs) != 2 or {row['dof'] for row in springs} != {1, 2}:
            raise ValueError('Require exactly two physical tangent springs per foot')
        body = physical[name]['first']
        normal_name = physical[name].get('normal_contact')
        if normal_name not in physical:
            raise ValueError('Each floor tangent requires its own normal cell')
        normal_row = physical[normal_name]
        if (normal_row['first'] != body or normal_row['second'] != 'floor'
                or normal_row.get('scalar_normal') != [0.,0.,1.]
                or not np.allclose(normal_row['point'],physical[name]['point'],atol=1.e-8,rtol=0.)):
            raise ValueError('Floor tangent and normal must share body and physical point')
        normal = max(0., normal_row['force_on_first_xyz_n'][2])
        slip = np.zeros(2)
        for spring in springs:
            a, b = spring['nodes']
            index = spring['dof']-1
            slip[index] = displacement[a][index]-displacement[b][index]
        target, secant = coulomb_secant(slip, normal, mu, original)
        actual = np.asarray(physical[name]['force_on_first_xyz_n'][:2])
        radius = float(np.linalg.norm(physical[name]['force_rounding_radius_xyz_n'][:2]))
        residual = float(np.linalg.norm(actual-target))
        excess = max(0., float(np.linalg.norm(actual))-mu*normal)
        rows[name] = {'body':body, 'normal_contact':normal_name,
            'point_xyz_mm':physical[name]['point'], 'normal_n':normal, 'slip_xy_mm':slip.tolist(),
            'force_xy_n':actual.tolist(), 'expected_force_xy_n':target.tolist(),
            'force_residual_n':residual, 'coulomb_excess_n':excess,
            'force_rounding_radius_n':radius, 'next_secant_n_per_mm':secant,
            'state':'open' if normal == 0 else 'stick' if secant == original else 'slip',
            'passed':residual <= tolerance_n+radius and excess <= tolerance_n+radius}
    if not rows:
        raise ValueError('Require current explicit cell tangent connections')
    return {'mu_assumed':mu, 'force_tolerance_n':tolerance_n, 'feet':rows,
            'passed':all(row['passed'] for row in rows.values()),
            'scope':__doc__}



def validate_secant_seed(seed, elastic):
    """Seeds alter initial search stiffness only; retain original elastic law."""
    if seed is None:
        return dict(elastic)
    if set(seed) != set(elastic) or any(not math.isfinite(value) or not 0 <= value <= elastic[name]
                                      for name, value in seed.items()):
        raise ValueError('Tangent seeds must match every foot and lie between zero and elastic stiffness')
    return dict(seed)


def normal_vectors(report, names, stiffness, record, data):
    rows = {row['name']:row for row in report['bearings']}
    springs = {row['name']:row for row in record['springs'] if row['name'] in names}
    printed = base.frame.displacement_roundoff(data)
    gap = np.array([rows[name]['opening_mm'] for name in names])
    linear = np.array([stiffness[i]*gap[i] if rows[name]['active'] else 0.
                       for i, name in enumerate(names)])
    gap_radius = np.array([sum(printed[node][springs[name]['dof']-1]
                              for node in springs[name]['nodes']) for name in names])
    linear_radius = np.array([stiffness[i]*gap_radius[i] if rows[name]['active'] else 0.
                             for i, name in enumerate(names)])
    return gap, linear, gap_radius, linear_radius


def run(output, *, module, mu, expected_candidate=None, bolt_stiffness=None,
        max_cycles=160, damping=.5, initial_contact_names=None, initial_tangent_secants=None, **parameters):
    """Serial native solves; damp only the search, independently audit final law."""
    if not math.isfinite(mu) or mu <= 0 or not 0 < damping <= 1 or max_cycles < 1:
        raise ValueError('Require positive finite mu, iteration budget and damping in (0,1]')
    before = sources()
    if before != LOADED_SOURCES:
        raise ValueError('Restart Coulomb runner after source changes')
    expected_candidate = expected_candidate or module.KEY
    stiffnesses = {**connection_stiffnesses(), 'floor':1.e5, 'bearing':1.e6, 'seating_per_area':100.}
    if bolt_stiffness is not None:
        stiffnesses['bolt'] = dict(bolt_stiffness)
    factory = prepare_recess if getattr(module, 'RECESS_NATIVE_GEOMETRY_REQUIRED', False) else prepare
    structure, metadata = factory(module, expected_candidate=expected_candidate,
        materials=materials(), stiffnesses=stiffnesses, **parameters)
    distribute_floor_tangents(structure, metadata)
    if before != sources():
        raise ValueError('Source changed during native preparation')
    directory = Path(output)
    directory.mkdir(parents=True, exist_ok=False)
    for name, sha in before.items():
        content = Path(name).read_bytes()
        if hashlib.sha256(content).hexdigest() != sha:
            raise ValueError('Source changed before snapshot: '+name)
        target = directory/'source_snapshots'/name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(content)
    with (directory/'model.pkl').open('wb') as stream:
        pickle.dump({'model':(structure, metadata), 'source_sha256':before}, stream)
    elastic = {row['name']:row['stiffness_n_per_mm'] for row in structure.springs
               if row['name'].endswith('_friction')}
    normal_names = {row['name'] for row in structure.springs
                    if row['bearing_closed_assumption'] and row['name'] not in elastic}
    active = set(normal_names) if initial_contact_names is None else set(initial_contact_names)
    if not active <= normal_names:
        raise ValueError('Initial normal contacts must belong to this candidate')
    initial_secants = validate_secant_seed(initial_tangent_secants, elastic)
    for spring in structure.springs:
        if spring['name'] in initial_secants:
            spring['stiffness_n_per_mm'] = initial_secants[spring['name']]
    active.update(name for name, value in initial_secants.items() if value > 0)
    ordered_normals = sorted(normal_names)
    normal_stiffness = {row['name']:row['stiffness_n_per_mm'] for row in structure.springs
                        if row['name'] in normal_names}
    normal_k = np.array([normal_stiffness[name] for name in ordered_normals])
    normal_anchor = None
    history = []
    report = {}
    for iteration in range(max_cycles):
        job = directory/f'cycle-{iteration:02d}'
        job.mkdir()
        record = base.frame.record_structure(structure, metadata, active)
        (job/'input.json').write_text(json.dumps(record, indent=2)+'\n')
        (job/'frame.inp').write_text(structure.deck(active_bearings=active, stress=False).replace(
            '*END STEP', '*NODE FILE,OUTPUT=3D\nU\n*END STEP'))
        command = ['docker','run','--rm','--network=none','--cpus=1','--memory=4g',
            '--user',f'{os.getuid()}:{os.getgid()}','-e','OMP_NUM_THREADS=1',
            '-v',f'{job.resolve()}:/output','-w','/output',base.frame.panel_kernel.IMAGE,
            'timeout','240s','ccx','-i','frame']
        native = subprocess.run(command, capture_output=True, text=True, timeout=260, check=False)
        log = native.stdout+native.stderr
        (job/'frame.log').write_text(log)
        if native.returncode or '*ERROR' in log.upper():
            raise ValueError('Native Coulomb iteration failed; inspect '+str(job/'frame.log'))
        data = (job/'frame.dat').read_text()
        report = base.assess(record, data, (job/'frame.frd').read_text(), (job/'frame.12d').read_text(),
                             expected_candidate=expected_candidate)
        friction = floor_law_check(record, data, report, mu, elastic)
        report['floor_friction_law'] = friction
        report['floor_scope'] = __doc__
        (job/'report.json').write_text(json.dumps(report, indent=2, allow_nan=False)+'\n')
        history.append({'directory':job.name, 'normal_contact_passed':report['closed_bearing_assumption_passed'],
            'friction_law_passed':friction['passed'],
            'peak_friction_residual_n':max(row['force_residual_n'] for row in friction['feet'].values())})
        print(json.dumps(history[-1]), flush=True)
        if report['closed_bearing_assumption_passed'] and friction['passed']:
            report['contact_active_set_converged'] = True
            report['termination'] = 'Normal contact and explicit Coulomb force law converged'
            break
        if not report['closed_bearing_assumption_passed']:
            # Convex normal solve at FIXED tangential stiffness. Interpolated
            # states guide the active set but are never accepted as FE results.
            gap, linear, gap_radius, linear_radius = normal_vectors(
                report, ordered_normals, normal_k, record, data)
            if normal_anchor is None:
                normal_anchor = gap, linear, gap_radius, linear_radius
                active = base.next_contact_names(report['bearings'], 'all')
            else:
                step = normal_energy_step(normal_anchor[0], normal_anchor[1], gap, linear, normal_k,
                    gap_radius=normal_anchor[2], linear_force_radius=normal_anchor[3],
                    trial_gap_radius=gap_radius, trial_force_radius=linear_radius)
                normal_anchor = (np.array(step['gap_mm']), np.array(step['linear_contact_force_n']),
                    np.array(step['gap_radius_mm']), np.array(step['linear_contact_force_radius_n']))
                active = {name for name, included in zip(ordered_normals,
                    step['active_from_interpolated_gap'], strict=True) if included}
                if step['alpha'] == 0. and step['start_derivative_interval_contains_zero']:
                    # Printed precision cannot establish this zero-step energy
                    # decision. Try the deterministic native active-set update;
                    # retain all final contact/force tolerances unchanged.
                    normal_anchor = gap, linear, gap_radius, linear_radius
                    active = base.next_contact_names(report['bearings'], 'all')
                    step['search_fallback'] = 'Native active-set trial after interval-uncertain zero energy step'
                history[-1]['normal_energy_search'] = step
                (job/'normal-energy-search.json').write_text(json.dumps(step, indent=2)+'\n')
            active.update(row['name'] for row in structure.springs
                          if row['name'] in elastic and row['stiffness_n_per_mm'] > 0)
            continue
        # Update friction only after normal complementarity is solved. K0
        # changes here, invalidating the preceding normal energy identity.
        normal_anchor = None
        active = base.next_contact_names(report['bearings'], 'all')
        for name, row in friction['feet'].items():
            target = row['next_secant_n_per_mm']
            selected = [spring for spring in structure.springs if spring['name'] == name]
            previous = selected[0]['stiffness_n_per_mm']
            updated = 0. if target == 0. else (1.-damping)*previous+damping*target
            for spring in selected:
                spring['stiffness_n_per_mm'] = updated
            if updated > 0:
                active.add(name)
    report.setdefault('contact_active_set_converged', False)
    report.setdefault('termination', 'Coulomb/contact iteration budget exhausted')
    report.update(candidate=metadata['candidate'], angle_stations=metadata['angle_stations'],
        parameters={key:metadata.get(key) for key in ('hold','pounds','force_xyz_n','standoff_from_front_mm',
            'stiffnesses','materials','equipment_kg','frame_size_mm','panel_size_mm','leg_bolt_scale',
            'leg_floor_grid','floor_rail_support','native_panel_cutouts','leg_floor_pressure_assumption',
            'leg_joint_assumption','header_bearing_assumption','floor_tangent_distribution','floor_tangent_cells')}, source_sha256=before,
        contact_cycles=history, solver_image=base.frame.panel_kernel.IMAGE,
        contact_update_strategy='nested_normal_energy_coulomb_secant',
        initial_contact_names=sorted(initial_contact_names) if initial_contact_names is not None else None,
        assumptions=__doc__, qualified_for_design=False)
    report['parameters']['floor_friction_assumption'] = {'mu':mu, 'elastic_tangent_n_per_mm':elastic,
        'monotonic_zero_initial_slip':True, 'measured_floor':False, 'original_no_slip_basis':False,
        'initial_tangent_secants_n_per_mm':initial_secants, 'secant_damping':damping,
        'per_cell_coulomb':True, 'centroid_tangent_springs_removed':True}
    report['numerically_accepted'] = all(report.get(key,False) for key in (
        'contact_active_set_converged','global_equilibrium_passed','member_equilibrium_passed','mpc_check_passed'))
    if before != sources():
        raise ValueError('Producer source changed during solve')
    report['artifact_sha256'] = {str(path.relative_to(directory)):hashlib.sha256(path.read_bytes()).hexdigest()
        for path in directory.rglob('*') if path.is_file()}
    (directory/'report.json').write_text(json.dumps(report, indent=2, allow_nan=False)+'\n')
    return report
