"""One-run evidence publisher; run from repository root after terminal context exists.

Reads this run only. Refuses to overwrite published evidence. Uses existing mesh
and nodal-output parsers; computes contact laws and moments independently.
"""
import hashlib
import json
import math
import re
import tarfile
from collections import Counter
from pathlib import Path

from fea.floor_contact import FACES, floor_faces, mesh
from fea.floor_contact_results import blocks, cross

SOURCE = Path('fea/generated/continuation-xy-69dgf_rc')
DEST = Path(__file__).parent


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def eps(token):
    mantissa, exponent = token.upper().split('E')
    return .5 * 10 ** (int(exponent) - len(mantissa.split('.')[1]))


def main():
    names = ['continuation.' + suffix for suffix in ('inp', 'json', 'dat', 'log', 'sta', 'cvg', 'frd')]
    names.append('floor_contact_continuation.launch.py')
    raw = {name: (SOURCE / name).read_bytes() for name in names}
    record = json.loads(raw['continuation.json'])
    assert 'exit_code' in record, 'Run is not terminal'
    assert digest(raw['continuation.inp']) == record['deck_sha256']
    launch = names[-1]
    launch_hashes = [v for k, v in record['prelaunch_sha256'].items() if k.endswith('fea/floor_contact_continuation.py')]
    assert launch_hashes == [digest(raw[launch])]
    for name, sha in record['output_sha256'].items():
        assert digest(raw[name]) == sha
    assert not any((DEST / name).exists() for name in ('report.json', 'independent_audit.json', 'solver_evidence.tar.gz', launch))
    data = raw['continuation.dat'].decode()
    nodes, elements = mesh(raw['continuation.inp'].decode())
    nodes = {n: xyz for n, xyz in nodes.items() if str(n) in record['nodal_volume_mm3']}
    groups = floor_faces(nodes, elements)
    face_patch = {tuple(face): name for name, faces in groups.items() for face in faces}
    parsed = blocks(data)
    local = {}
    pattern = r'(relative contact displacement|contact stress)[^\n]*time\s+(\S+)\n(.*?)(?=\n\s*[A-Za-z]|\Z)'
    for kind, time, body in re.findall(pattern, data, re.DOTALL):
        rows = [line.split() for line in body.splitlines() if len(line.split()) == 5]
        local[kind, float(time)] = rows
    pair = {}
    pattern = r'statistics for slave set SLAVE_(\w+), master set MASTER_(\w+) and time\s+(\S+)(.*?)(?=\n\s*statistics|\n\s*(?:displacements|forces|relative contact|contact stress)|\Z)'
    for name, master, time, body in re.findall(pattern, data, re.DOTALL):
        assert name == master and name in groups
        numeric = [line.split() for line in body.splitlines() if line.strip() and re.match(r'^[+\-\d.]', line.strip())]
        if len(numeric) == 4 and list(map(len, numeric)) == [6, 6, 3, 3]:
            pair.setdefault((float(time), name), []).append(numeric)
    endpoints = []
    for time, load in ((1., 0.), (2., 0.), (3., 1200.)):
        u = parsed.get(('displacements', 'WOODN', time), {})
        if u.keys() != nodes.keys():
            continue
        guide = parsed['forces', 'PRELOAD_GUIDE', time]
        assert guide.keys() == set(record['guide_nodes'])
        pos = {n: [a+b for a, b in zip(xyz, u[n])] for n, xyz in nodes.items()}
        body = [(pos[int(n)], (0., 0., -v*6e-10*9806.65)) for n, v in record['nodal_volume_mm3'].items()]
        body += [(pos[n], (0., 0., -load/len(record['load_nodes']))) for n in record['load_nodes']]
        if time == 1:
            body += [(pos[n], (v[0], v[1], 0.)) for n, v in guide.items()]
        external = list(body)
        patches = {}
        for name, xyz in record['ground_nodes'].items():
            rf = parsed['forces', 'GROUND_'+name, time]
            assert set(rf) == set(map(int, xyz))
            external += [(xyz[str(n)], v) for n, v in rf.items()]
            force = [sum(v[i] for v in rf.values()) for i in range(3)]
            moment = [sum(cross(xyz[str(n)], v)[i] for n, v in rf.items()) for i in range(3)]
            faces = {tuple(face) for face in groups[name]}
            feet = {elements[e][i] for e, f in faces for i in FACES[f-1]}
            gap = [pos[n][2] for n in feet]
            cf = pair.get((time, name), [])
            first = list(map(float, cf[0][0])) if cf else None
            rf_tokens = []
            for tk, tn, tt, tb in re.findall(r'(forces)[^\n]*for set (GROUND_\w+) and time\s+(\S+)\n(.*?)(?=\n\s*[A-Za-z]|\Z)', data, re.DOTALL):
                if tn == 'GROUND_'+name and float(tt) == time:
                    rf_tokens = [line.split() for line in tb.splitlines() if len(line.split()) == 4]
            force_tol = [eps(cf[0][0][i])+sum(eps(row[i+1]) for row in rf_tokens) for i in range(3)] if first else None
            moment_tol = [eps(cf[0][0][i+3])+sum(abs(xyz[row[0]][(i+1)%3])*eps(row[(i+2)%3+1])+abs(xyz[row[0]][(i+2)%3])*eps(row[(i+1)%3+1]) for row in rf_tokens) for i in range(3)] if first else None
            patches[name] = {'ground_reaction_n': force, 'ground_moment_nmm': moment,
                                 'aggregate_friction_utilization': math.hypot(*force[:2])/(record['mu']*force[2]),
                                 'sampled_physical_nodal_gap_mm': [min(gap), max(gap)],
                                 'cf_triplet_count': len(cf), 'cf_force_moment': first,
                                 'cf_minus_rf_force_n': [first[i]-force[i] for i in range(3)] if first else None,
                                 'cf_minus_rf_moment_nmm': [first[i+3]-moment[i] for i in range(3)] if first else None,
                                 'cf_minus_rf_force_print_tolerance_n': force_tol,
                                 'cf_minus_rf_moment_print_tolerance_nmm': moment_tol,
                                 'cf_area_mm2': float(cf[0][3][0]) if cf else None}
        cdis = local['relative contact displacement', time]
        cstr = local['contact stress', time]
        assert len(cdis) == len(cstr) and cdis
        assert [r[:2] for r in cdis] == [r[:2] for r in cstr]
        counts = Counter(tuple(map(int, row[:2])) for row in cstr)
        assert counts.keys() <= face_patch.keys(), 'Unknown contact face'
        normal_errors, normal_tols, excesses, friction_tols, gammas, pressures = [], [], [], [], [], []
        normal_bad = compression_bad = friction_bad = 0
        for disp, stress in zip(cdis, cstr):
            gap, pressure, a, b = float(disp[2]), *map(float, stress[2:])
            pe, ae, be = map(eps, stress[2:])
            error = abs(pressure + record['normal_penalty_n_mm3']*gap)
            tolerance = pe + record['normal_penalty_n_mm3']*eps(disp[2]) + 1e-14
            excess = math.hypot(a, b) - record['mu']*pressure
            ftol = math.hypot(ae, be) + record['mu']*pe + 1e-14
            normal_errors.append(error); normal_tols.append(tolerance)
            excesses.append(excess); friction_tols.append(ftol); pressures.append(pressure)
            if pressure > 0:
                gammas.append(math.hypot(a, b)/(record['mu']*pressure))
            normal_bad += error > tolerance
            compression_bad += pressure < -pe
            friction_bad += excess > ftol
        for name, patch in patches.items():
            patch['active_point_count'] = sum(v for face, v in counts.items() if face_patch[face] == name)
            patch['active_points_per_face'] = {f'{e}:{f}': counts[e, f] for e, f in groups[name]}
        force = [sum(v[i] for p, v in external) for i in range(3)]
        moment = [sum(cross(p, v)[i] for p, v in external) for i in range(3)]
        cf_complete = all(v['cf_triplet_count'] == 3 for v in patches.values())
        slave_moment = [sum(v['cf_force_moment'][i+3] for v in patches.values())+sum(cross(p, v)[i] for p, v in body) for i in range(3)] if cf_complete else None
        endpoints.append({'time': time, 'temporary_guides_active': time == 1, 'downward_climber_n': load,
                              'force_residual_n': force, 'ground_moment_residual_nmm': moment,
                              'slave_cf_moment_residual_nmm': slave_moment,
                              'global_equilibrium_pass': max(map(abs, force)) <= .1 and max(map(abs, moment)) <= 1,
                              'maximum_guide_xy_n': max(abs(v[i]) for v in guide.values() for i in (0, 1)),
                              'maximum_nodal_displacement_mm': max(math.sqrt(sum(x*x for x in v)) for v in u.values()),
                              'active_point_count': len(cstr), 'unknown_face_count': 0, 'matched_point_face_sequence': True,
                              'pressure_range_n_mm2': [min(pressures), max(pressures)],
                              'maximum_normal_law_error_n_mm2': max(normal_errors), 'normal_law_tolerance_range_n_mm2': [min(normal_tols), max(normal_tols)],
                              'maximum_raw_coulomb_excess_n_mm2': max(excesses), 'coulomb_tolerance_range_n_mm2': [min(friction_tols), max(friction_tols)],
                              'normal_law_violation_count': normal_bad, 'compression_violation_count': compression_bad,
                              'coulomb_violation_count': friction_bad, 'maximum_point_friction_gamma': max(gammas), 'patches': patches})
    audit = {'status': 'DIAGNOSTIC ENDPOINT AUDIT; NOT PHYSICAL OR STRUCTURAL ACCEPTANCE', 'dat_sha256': digest(raw['continuation.dat']),
                 'recorded_exit_code': record['exit_code'], 'production_audit_error': record.get('audit_error'),
                 'formulas': {'position': 'initial+printedU; ground fixed', 'gravity': '-nodal_volume_mm3*6e-10*9806.65 in Z',
                               'moment': 'sum cross(deformed position, external force); guide XY only time1',
                               'local_normal': 'p=-K*CDISnormal; tolerance epsilon_p+K*epsilon_gap+1e-14',
                               'local_friction': 'hypot(tau1,tau2)<=mu*p+hypot(epsilon_tau1,epsilon_tau2)+mu*epsilon_p+1e-14',
                               'rounding': 'epsilon=0.5*10^(printed exponent-digits after decimal)',
                               'pair_order': 'CF,CFN,CFS according to deck; identical headings in2.21',
                               'global_gate': 'maxabs force<=0.1N; maxabs moment<=1Nmm'},
                 'limitations': 'Missing active-point faces are counted explicitly, not proven open. CF/RF differences are diagnostics, not independently integrated traction proof. History, mesh, penalty, friction, material and connection validation remain required.', 'endpoints': endpoints}
    accepted = []
    for line in raw['continuation.sta'].decode().splitlines():
        row = line.split()
        if len(row) == 7 and row[0].isdigit():
            accepted.append(dict(zip(('step', 'increment', 'attempt', 'iterations', 'total_time', 'step_time', 'increment_time'), [*map(int, row[:4]), *map(float, row[4:])])) )
    complete = {row['step'] for row in accepted if abs(row['step_time']-1) < 1e-8}
    archive = DEST/'solver_evidence.tar.gz'
    with tarfile.open(archive, 'w:gz') as tar:
        for name in names:
            tar.add(SOURCE/name, arcname=name)
    with tarfile.open(archive, 'r:gz') as tar:
        assert all(tar.extractfile(name).read() == content for name, content in raw.items())
    assert archive.stat().st_size < 100_000_000
    report = {'status': ('TIMEOUT; ' if record['exit_code'] == -999 else 'TERMINAL; ')+'NO ACCEPTED PHYSICAL BOARD SOLUTION',
                  'source_directory': str(SOURCE), 'exit_code': record['exit_code'], 'max_seconds': record['max_seconds'], 'elapsed_seconds': record['elapsed_seconds'],
                  'mu': record['mu'], 'free_increment': record['free_increment'], 'accepted_partial_increments': accepted,
                  'last_accepted_total_time': accepted[-1]['total_time'] if accepted else 0, 'complete_steps': len(complete),
                  'guided_preload_complete': 1 in complete, 'free_gravity_reached': any(row['step'] == 2 for row in accepted), 'free_gravity_complete': 2 in complete,
                  'climber_load_reached': any(row['step'] == 3 for row in accepted), 'climber_load_complete': 3 in complete,
                  'accepted_physical_solution': False, 'audit_error': record.get('audit_error'), 'independent_audit': 'independent_audit.json',
                  'archive': archive.name, 'archive_bytes': archive.stat().st_size, 'archive_sha256': digest(archive.read_bytes()), 'archive_contents': names,
                  'source_sha256': record['source_sha256'], 'deck_sha256': record['deck_sha256'], 'launch_source_sha256': digest(raw[launch]),
                  'interpretation': 'Full guided preload; only free release/load increments capped0.1. Mu0.5 is assumed, not measured. Global/local printed endpoint checks do not establish full complementarity, history/mesh independence or member/connection capacity.'}
    for name, value in (('report.json', report), ('independent_audit.json', audit)):
        (DEST/name).write_text(json.dumps(value, indent=2)+'\n')
    (DEST/launch).write_bytes(raw[launch])
    print(json.dumps({'archive_bytes': report['archive_bytes'], 'exit_code': record['exit_code'], 'endpoints': [{k: v for k, v in ep.items() if k != 'patches'} for ep in endpoints]}))


if __name__ == '__main__':
    main()
