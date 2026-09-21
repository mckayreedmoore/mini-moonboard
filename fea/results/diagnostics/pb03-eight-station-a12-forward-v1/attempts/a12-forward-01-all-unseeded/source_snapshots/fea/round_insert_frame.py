"""Fresh insert-frame diagnostic with sampled unilateral panel seating contact.

Contact is frictionless and sampled over actual timber support. Arbitrary spring
and penalty stiffness, isotropic materials and clamped feet remain development
assumptions; native convergence does not qualify inserts or the structure.
"""
import argparse
import copy
import hashlib
import json
import os
import subprocess
from functools import lru_cache
from pathlib import Path
from types import SimpleNamespace

import numpy as np

from fea import horizontal_frame_stress as stress
from fea import horizontal_panel_frame as frame
from fea import shell_surface_recovery
from mini_moonboard.connection_geometry import material_intervals


def panel_interpolation(structure, panel, point, inward):
    """Independent S8 interpolation; normal motion is constant through thickness."""
    p = np.asarray(point)
    normal = np.asarray(inward)
    for kind, ids, group in structure.elements.values():
        if kind != 'S8' or group != panel:
            continue
        nodes = np.array([structure.nodes[n] for n in ids])
        x, y = nodes[1]-nodes[0], nodes[3]-nodes[0]
        lx, ly = np.linalg.norm(x), np.linalg.norm(y)
        x, y = x/lx, y/ly
        delta = p-nodes[0]
        u, v = np.dot(delta, x)/lx, np.dot(delta, y)/ly
        if -.0000001 <= u <= 1.0000001 and -.0000001 <= v <= 1.0000001:
            weights = frame.shape8(2*u-1, 2*v-1)
            projected = sum(w*n for w, n in zip(weights, nodes, strict=True))
            if np.linalg.norm(np.cross(projected-p, normal)) > 1.e-5:
                raise ValueError('Panel interpolation does not reproduce contact tangential position')
            return ids, weights
    return None


def normal_contact(structure, name, wood, ids, weights, point, inward, stiffness):
    """Project relative motion on the physical normal into a scalar SPRING2."""
    auxiliary = [structure.node(point), structure.node(point)]
    for node, terms in ((auxiliary[0], [(wood, 1.)]),
                        (auxiliary[1], list(zip(ids, weights, strict=True)))):
        structure.equations.append([(node, 1, 1.)]+[
            (source, dof+1, -float(weight*component)) for source, weight in terms
            for dof, component in enumerate(inward) if abs(weight*component) > 1.e-13])
        structure.equations.extend([[(node, 2, 1.)], [(node, 3, 1.)]])
    structure.spring(*auxiliary, stiffness, name, dofs=(1,), bearing=True)
    structure.rotation_masters.update(auxiliary)  # Scalar coordinates are not physical displacements.
    return auxiliary


def tributary_area(structure, panel, point, grain, transverse, along_bounds, width):
    """Clip each axis-aligned tributary rectangle to its independent panel."""
    nodes = np.array([structure.nodes[n] for n in structure.panels[panel]['nodes']])
    element = next(ids for kind, ids, group in structure.elements.values()
                   if kind == 'S8' and group == panel)
    corner = np.array(structure.nodes[element[0]])
    axes = [np.array(structure.nodes[element[i]])-corner for i in (1, 3)]
    axes = np.array([axis/np.linalg.norm(axis) for axis in axes])
    for direction in (grain, transverse):
        if not np.isclose(max(abs(axes@direction)), 1., atol=1.e-8):
            raise ValueError('Tributary rectangles require panel-aligned receiver axes')
    corners = np.array([point+grain*a+transverse*b for a in along_bounds for b in (-width/2, width/2)])
    projected, boundary = corners@axes.T, nodes@axes.T
    extent = np.maximum(0., np.minimum(projected.max(axis=0), boundary.max(axis=0))-
                        np.maximum(projected.min(axis=0), boundary.min(axis=0)))
    return float(np.prod(extent))


def has_seating_material(point, inward, openings):
    """No seating reaction at a sample inside an actual receiver display cut."""
    return not any(cut.isInside(point+inward*.001, 1.e-7) for cut in openings)


def seating_contacts(structure, module, samples=3, penalty=100.):
    """Tributary-area springs at existing timber stations and support-width samples.

    Uses raw CAD for backing occupancy. This samples intact backing; local pilot
    holes/countersinks, contact pressure peaks and mesh convergence are excluded.
    """
    import cadquery as cq

    if samples < 1 or penalty <= 0 or not np.isfinite(penalty):
        raise ValueError('Positive sampling count and penalty required')
    raw = {p.name: p for p in module.wood_parts()}
    result = []
    structure.seating_sample_rejections = []
    openings = {}
    for connection in module.panel_connections():
        openings.setdefault(connection.members[1], []).append(connection.receiver_cut())
    for member, entry in structure.members.items():
        if member != 'base_header' and not member.startswith(('base_side_', 'base_principal_', 'base_rail_', 'base_post_')):
            continue
        kicker = member == 'base_header' or member.startswith('base_post_')
        inward = cq.Vector(0, -1, 0) if kicker else module.b.normal()
        plane_origin = cq.Vector(0, module.base.HEADER_FRONT_Y, 0) if kicker else module.b.point(0, 0, 0)
        normal = np.array(inward.toTuple())
        transverse = cq.Vector(*np.cross(entry['axis'], normal)).normalized()
        stations = sorted(entry['sections'])
        for index, station in enumerate(stations):
            low = station if index == 0 else (stations[index-1]+station)/2
            high = station if index == len(stations)-1 else (station+stations[index+1])/2
            centre = cq.Vector(*(entry['start']+entry['axis']*station))
            face = centre-inward*(centre-plane_origin).dot(inward)
            intervals = material_intervals(raw[member].shape, face+inward*.001, transverse, -5000., 5000.)
            for start, end in intervals:
                for sample in range(samples):
                    point = face+transverse*(start+(end-start)*(sample+.5)/samples)
                    available = has_seating_material(point, inward, openings.get(member, []))
                    panel_names = [name for name in structure.panels if name.startswith('kicker_' if kicker else 'main_')]
                    for panel in panel_names:
                        match = panel_interpolation(structure, panel, point.toTuple(), normal)
                        if match is None:
                            continue
                        ids, weights = match
                        area = tributary_area(structure, panel, np.array(point.toTuple()),
                            entry['axis'], np.array(transverse.toTuple()),
                            (low-station, high-station), (end-start)/samples)
                        if area <= 1.e-10:
                            continue
                        if not available:
                            structure.seating_sample_rejections.append({'panel': panel, 'member': member,
                                'point_xyz_mm': list(point.toTuple()), 'discarded_tributary_area_mm2': area,
                                'reason': 'Sample lies in modeled insert receiver opening; whole tributary omitted, not exact void-area integration'})
                            continue
                        wood = structure.attachment(member, point.toTuple())
                        name = f'seating_{len(result)+1}'
                        aux = normal_contact(structure, name, wood, ids, weights, point.toTuple(), normal, penalty*area)
                        result.append({'name': name, 'panel': panel, 'member': member,
                            'point_xyz_mm': list(point.toTuple()), 'inward_xyz': normal.tolist(),
                            'tributary_area_mm2': area, 'normal_stiffness_n_per_mm': penalty*area,
                            'scalar_nodes': aux, 'qualified_contact_pressure': False})
    if not result:
        raise ValueError('No physical panel backing contacts sampled')
    return result


@lru_cache(maxsize=3)
def base_frame(module, hold, source_identity):
    """Cache only the unchanged base; each probe receives its own deep copy."""
    from mini_moonboard.insert_frame import PanelMachineScrew

    class Adapter:
        timber = SimpleNamespace(PanelScrew=(module.timber.PanelScrew, PanelMachineScrew))
        def __getattr__(self, name):
            return getattr(module, name)

    return frame.current_frame(Adapter(), hold=hold, stiffness=1000., mode='coupled',
        pounds=250., load_kind='full', frame_size=100., panel_size=80., patch_size=20.)


def prepare(module, hold='F10', panel_stiffness=1000., samples=3, penalty=100., contact=True):
    structure, metadata = copy.deepcopy(base_frame(module, hold, tuple(sorted(sources().items()))))
    names = {c.name for c in module.panel_connections()}
    if len(names) != 56 or panel_stiffness <= 0 or not np.isfinite(panel_stiffness):
        raise ValueError('Require 56 current inserts and positive panel attachment stiffness')
    for spring in structure.springs:
        if spring['name'] in names:
            spring['stiffness_n_per_mm'] = panel_stiffness
    contacts = seating_contacts(structure, module, samples, penalty) if contact else []
    rejected = getattr(structure, 'seating_sample_rejections', [])
    metadata.update(seating_rejected_samples=rejected,
        seating_rejected_point_count=len({(r['member'], *r['point_xyz_mm']) for r in rejected}),
        seating_rejected_tributary_area_mm2=sum(r['discarded_tributary_area_mm2'] for r in rejected),
        panel_screw_count=len(names), panel_attachment_names=sorted(names),
        panel_attachment_stiffness_n_per_mm=panel_stiffness,
        seating_contacts=contacts, seating_contact_enabled=contact,
        seating_contact_samples_across_width=samples, seating_penalty_n_per_mm3=penalty,
        insert_connections_qualified=False, round_service_bores=module.bore_records(),
        stress_output={'global': True, 'variables': ['S', 'COORD'],
                       'integration_points': {'C3D20': 27, 'S8': 27}})
    metadata['limits'] += ' '+__doc__+' Panel seating uses normal scalar MPCs at existing member stations; '
    metadata['limits'] += ('Contact samples exclude modeled insert receiver openings; tributary areas remain approximate and do not resolve local pressure, preload or friction. '
                          'Panel springs are unqualified insert-connection surrogates, not inherited SPAX resistance.')
    return structure, metadata


def assess(record, data, frd, expansion):
    result = shell_surface_recovery.assess(record, data, frd, expansion)
    contacts = []
    for row in record['seating_contacts']:
        scalar = result['connector_forces'][row['name']]['force_on_first_xyz_n'][0]
        result['connector_forces'][row['name']]['force_on_first_xyz_n'] = (scalar*np.array(row['inward_xyz'])).tolist()
        contacts.append({**row, 'compression_n': scalar,
                        'physical_force_on_wood_xyz_n': (scalar*np.array(row['inward_xyz'])).tolist()})
    result['seating_contacts'] = contacts
    result['insert_connections_qualified'] = False
    return result


def authenticated_input(directory):
    """Verify native/source receipts, exact expanded-output deck and corrected replay."""
    from fea.panel_screw_sensitivity import restore

    directory = Path(directory)
    digest = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
    report = json.loads((directory/'report.json').read_text())
    if not report['contact_diagnostic_checks_passed']:
        raise ValueError('Insert diagnostic did not pass')
    for name, sha in report['source_sha256'].items():
        if digest(directory/'source_snapshots'/name) != sha:
            raise ValueError('Insert source snapshot mismatch: '+name)
    for name, sha in report['artifact_sha256'].items():
        if digest(directory/name) != sha:
            raise ValueError('Insert native artifact mismatch: '+name)
    job = directory/report['final_cycle_directory']
    record = json.loads((job/'input.json').read_text())
    if (record['candidate'] != 'round-insert-development' or record['mode'] != 'coupled'
            or record['assumed_modulus_mpa'] != 7000. or record['assumed_poisson_ratio'] != .3):
        raise ValueError('Unsupported current insert mechanics')
    active = {r['name'] for r in record['springs'] if r['bearing_closed_assumption'] and r['active']}
    expected = restore(record).deck(active_bearings=active, stress=True).replace(
        '*END STEP', '*NODE FILE,OUTPUT=3D\nU\n*END STEP')
    if expected != (job/'frame.inp').read_text():
        raise ValueError('Expanded-output insert deck does not reproduce')
    data = (job/'frame.dat').read_text()
    replay = assess(record, data, (job/'frame.frd').read_text(), (job/'frame.12d').read_text())
    for key, value in replay.items():
        if report[key] != value:
            raise ValueError('Corrected insert diagnostic replay differs: '+key)
    if stress.assess(record, data) != report['diagnostic_stress']:
        raise ValueError('Insert stress replay differs')
    return record, {'directory': str(directory), 'report_sha256': digest(directory/'report.json'),
                    'input_sha256': digest(job/'input.json'), 'source_sha256': report['source_sha256']}


def sources():
    paths = [Path(__file__), Path('fea/horizontal_panel_frame.py'), Path('fea/horizontal_frame_stress.py'),
             Path('fea/horizontal_frame_members.py'), Path(frame.panel_kernel.__file__),
             Path('fea/shell_surface_recovery.py'), Path('fea/frd_displacements.py'),
             Path('fea/panel_screw_sensitivity.py'), Path('pyproject.toml'), Path('uv.lock'),
             *Path('mini_moonboard').glob('*.py'), *Path('docs').glob('*reference.json')]
    return {str(p.resolve().relative_to(Path.cwd())): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}


def run(output, **parameters):
    from mini_moonboard import round_insert_frame as module

    directory = Path(output)
    directory.mkdir(parents=True, exist_ok=False)
    hashes = sources()
    structure, metadata = prepare(module, **parameters)
    for name in hashes:
        target = directory/'source_snapshots'/name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(Path(name).read_bytes())
    active = {r['name'] for r in structure.springs if r['bearing_closed_assumption']}
    seen, history = set(), []
    converged = False
    for iteration in range(30):
        signature = tuple(sorted(active))
        if signature in seen:
            break
        seen.add(signature)
        job = directory/f'cycle-{iteration:02d}'
        job.mkdir()
        record = frame.record_structure(structure, metadata, active)
        (job/'input.json').write_text(json.dumps(record, indent=2)+'\n')
        (job/'frame.inp').write_text(structure.deck(active_bearings=active, stress=True).replace(
            '*END STEP', '*NODE FILE,OUTPUT=3D\nU\n*END STEP'))
        command = ['docker', 'run', '--rm', '--network=none', '--cpus=1', '--memory=4g',
            '--user', f'{os.getuid()}:{os.getgid()}', '-e', 'OMP_NUM_THREADS=1',
            '-v', f'{job.resolve()}:/output', '-w', '/output', frame.panel_kernel.IMAGE,
            'timeout', '180s', 'ccx', '-i', 'frame']
        native = subprocess.run(command, capture_output=True, text=True, timeout=200, check=False)
        log = native.stdout+native.stderr
        (job/'frame.log').write_text(log)
        if native.returncode or '*ERROR' in log.upper():
            raise ValueError('Native insert solve failed; inspect cycle log')
        data = (job/'frame.dat').read_text()
        report = assess(record, data, (job/'frame.frd').read_text(), (job/'frame.12d').read_text())
        report['diagnostic_stress'] = stress.assess(record, data)
        report['artifact_sha256'] = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in job.iterdir() if p.is_file()}
        (job/'report.json').write_text(json.dumps(report, indent=2)+'\n')
        history.append({'directory': job.name, 'report_sha256': hashlib.sha256((job/'report.json').read_bytes()).hexdigest()})
        if report['closed_bearing_assumption_passed']:
            converged = True
            break
        active = frame.next_bearing_set(report['bearings'])
    if hashes != sources():
        raise ValueError('Source changed during insert-frame diagnostic')
    report.update(contact_active_set_converged=converged, contact_cycles=history,
        final_cycle_directory=history[-1]['directory'], source_sha256=hashes,
        contact_diagnostic_checks_passed=bool(converged and report['global_equilibrium_passed'] and report['mpc_check_passed']),
        parameters=parameters, solver_image=frame.panel_kernel.IMAGE)
    report['artifact_sha256'] = {str(p.relative_to(directory)): hashlib.sha256(p.read_bytes()).hexdigest()
                                for p in directory.rglob('*') if p.is_file()}
    (directory/'report.json').write_text(json.dumps(report, indent=2)+'\n')
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--hold', choices=('F10', 'C6', 'C10'), default='F10')
    parser.add_argument('--panel-stiffness', type=float, default=1000.)
    parser.add_argument('--samples', type=int, default=3)
    parser.add_argument('--penalty', type=float, default=100.)
    parser.add_argument('--no-contact', action='store_true')
    args = parser.parse_args()
    r = run(args.output, hold=args.hold, panel_stiffness=args.panel_stiffness, samples=args.samples,
            penalty=args.penalty, contact=not args.no_contact)
    print({k: r[k] for k in ('contact_diagnostic_checks_passed', 'maximum_panel_displacement_mm', 'insert_connections_qualified')})
