"""One bounded immutable-observer replay of the archived finest original frame."""
import argparse
import hashlib
import json
import math
import os
import re
import resource
import signal
import subprocess
import sys
import tempfile
import time
from decimal import Decimal
from pathlib import Path

from fea.floor_contact import FACES, mesh
from fea.floor_contact_results import blocks, cross
from fea.full_frame_mortar import verify_deck
from fea.full_frame_refinement import read_archive
from fea.full_frame_refinement import replay as global_replay
from fea.mortar_kinematic_replay import replay
from fea.mortar_observer_replay import PREFIX

ARCHIVE = Path('fea/results/full_frame_refinement/0.0625.tar.gz')
ARCHIVE_SHA = 'b7191366c224835aa6f790996671cc491ad3ae878cb9b797698a04d45e0b373b'
IMAGE = 'sha256:8e84d8ad546cd98a861ceba3ccbf4c486b88f38a8b7e4c45f7784ace4cea21e1'
PUBLICATION = Path('fea/mortar_kinematic_build/report.json')
BINARY = '/usr/local/bin/ccx-kinematic-observer-2.21'
LOG_LIMIT = 512 * 1024**2
MEMORY_LIMIT = 6 * 1024**3
SECONDS = 1500
PROJECT_ROOT = Path(__file__).resolve().parents[1]
# Complete import-time project dependency closure for this audit. Dormant CAD
# construction/integration functions are not called by the archive-only audit.
SOURCE_FILES = ('mortar_frame_observer.py', 'floor_contact.py', 'floor_contact_results.py',
                'full_frame_mortar.py', 'floor_contact_recovery.py', 'full_frame_refinement.py',
                'mortar_observer_replay.py', 'mortar_kinematic_replay.py', 'mortar_linear_law.py')
IMPORTED_PATHS = {name: Path(__file__).resolve() if name == 'mortar_frame_observer.py' else
                  Path(sys.modules['fea.'+Path(name).stem].__file__).resolve() for name in SOURCE_FILES}
LOADED_SOURCE_SHA256 = {name: hashlib.sha256(IMPORTED_PATHS[name].read_bytes()).hexdigest()
                        for name in SOURCE_FILES}


def sha(path):
    with path.open('rb') as handle:
        return hashlib.file_digest(handle, 'sha256').hexdigest()


def save(path, data):
    path.write_text(json.dumps(data, indent=2, allow_nan=False) + '\n')


def verify_audit_sources(directory, report):
    """Bind live, imported and archived project source to the launch digests."""
    if set(report.get('audit_source_sha256', {})) != set(SOURCE_FILES):
        raise ValueError('Audit source inventory differs')
    if (PROJECT_ROOT/'fea/__init__.py').exists():
        raise ValueError('Unexpected executable fea package initializer')
    for name, expected in report['audit_source_sha256'].items():
        archived = 'launch.py' if name == 'mortar_frame_observer.py' else 'launch_sources/'+name
        if (report['prelaunch_sha256'].get(archived) != expected or
                IMPORTED_PATHS[name] != (PROJECT_ROOT/'fea'/name).resolve() or
                sha(directory/archived) != expected or sha(PROJECT_ROOT/'fea'/name) != expected or
                LOADED_SOURCE_SHA256.get(name) != expected):
            raise ValueError('Executing or snapshotted audit source drift: '+name)


def monitor(command, directory, launch_report=None):
    """Bound one named container; preserve interruption/cleanup uncertainty."""
    name = command[command.index('--name')+1]
    log_path = directory/'frame.log'
    report = dict(launch_report or {}) | {'exit_code': -998, 'terminal_state_confirmed': False}
    started, process = time.monotonic(), None
    previous = {s: signal.getsignal(s) for s in (signal.SIGINT, signal.SIGTERM)}
    def interrupted(signum, frame):
        raise KeyboardInterrupt('Received signal '+str(signum))
    try:
        for signum in previous:
            signal.signal(signum, interrupted)
        with log_path.open('w') as log:
            try:
                old_mask = signal.pthread_sigmask(signal.SIG_BLOCK, previous)
                try:
                    process = subprocess.Popen(command, stdout=log, stderr=subprocess.STDOUT)
                    report['docker_client_pid'] = process.pid
                finally:
                    signal.pthread_sigmask(signal.SIG_SETMASK, old_mask)
                while process.poll() is None:
                    if time.monotonic()-started > SECONDS or log_path.stat().st_size > LOG_LIMIT:
                        report['stop_reason'] = 'Runtime or stdout budget exceeded; retained partial evidence'
                        break
                    time.sleep(2)
                if 'stop_reason' not in report:
                    report['exit_code'] = process.wait(timeout=30)
            except BaseException as error:  # noqa: BLE001 -- cleanup and retain interruptions too
                report['stop_reason'] = 'Monitor interrupted/failed; retained partial evidence'
                report['monitor_error'] = type(error).__name__+': '+str(error)
            finally:
                try:
                    # Stop/reap a pending client before deciding an absent
                    # container is terminal: it must not start one afterwards.
                    if process is not None:
                        if process.poll() is None:
                            process.kill()
                        report['exit_code'] = process.wait(timeout=30)
                    def container_running():
                        probe = subprocess.run(['docker', 'inspect', '--format', '{{.State.Running}}', name],
                                               capture_output=True, text=True, check=False, timeout=15)
                        if probe.returncode and re.fullmatch(
                                r'(?i:(?:error:\s*)?no such object:)\s*'+re.escape(name), probe.stderr.strip()):
                            return False
                        if probe.returncode or probe.stdout.strip() not in ('true', 'false'):
                            raise RuntimeError('Cannot resolve named container: '+probe.stderr)
                        return probe.stdout.strip() == 'true'
                    # A disconnected/exited Docker client is not evidence that
                    # its container stopped. Inspect after every client outcome.
                    if container_running():
                        report.setdefault('stop_reason', 'Container survived client exit; explicitly stopped; partial evidence')
                        killed = subprocess.run(['docker', 'kill', name], capture_output=True,
                                                text=True, check=False, timeout=15)
                        if killed.returncode or container_running():
                            raise RuntimeError('Named container termination not confirmed: '+killed.stderr)
                    if process is None:
                        report['exit_code'] = 1
                    report['terminal_state_confirmed'] = True
                except BaseException as error:  # noqa: BLE001 -- never falsely assert successful cleanup
                    report['stop_reason'] = 'Named container termination unconfirmed'
                    report['cleanup_error'] = type(error).__name__+': '+str(error)
                    report['terminal_state_confirmed'] = False
    finally:
        old_mask = signal.pthread_sigmask(signal.SIG_BLOCK, previous)
        try:
            report['elapsed_seconds'] = time.monotonic()-started
            # Check completed jobs too; do not confuse client exit with success.
            if report['elapsed_seconds'] > SECONDS or (log_path.exists() and log_path.stat().st_size > LOG_LIMIT):
                report.setdefault('stop_reason', 'Final runtime or stdout budget exceeded; retained partial evidence')
            report['status'] = ('TERMINAL; AUDIT PENDING; NO PHYSICAL ACCEPTANCE' if report['exit_code'] == 0 and 'stop_reason' not in report
                                else 'TERMINAL SOLVER FAILURE/STOP; PARTIAL EVIDENCE; NO PHYSICAL ACCEPTANCE')
            if not report['terminal_state_confirmed']:
                report['status'] = 'CONTAINER TERMINATION UNCONFIRMED; CLEANUP ERROR; NO PHYSICAL ACCEPTANCE'
            report['output_sha256'] = {p.name: sha(p) for p in directory.iterdir() if p.name.startswith('frame.')}
            save(directory/'report.json', report)
        finally:
            for signum, handler in previous.items():
                signal.signal(signum, handler)
            signal.pthread_sigmask(signal.SIG_SETMASK, old_mask)
    return report


def run_audit(directory, report):
    """Bound one isolated audit child and hash partial outputs even on signals."""
    process = None
    previous = {s: signal.getsignal(s) for s in (signal.SIGINT, signal.SIGTERM)}
    report['audit_exit_code'] = -999
    def interrupted(signum, frame):
        raise KeyboardInterrupt('Received audit signal '+str(signum))
    try:
        for signum in previous:
            signal.signal(signum, interrupted)
        with (directory/'audit.log').open('w') as log:
            try:
                verify_audit_sources(directory, report)
                command = [sys.executable, '-m', 'fea.mortar_frame_observer', '--audit', str(directory)]
                # Do not deliver an interruption after spawn but before its
                # child handle is assigned: cleanup must know the exact PID.
                old_mask = signal.pthread_sigmask(signal.SIG_BLOCK, previous)
                try:
                    process = subprocess.Popen(command, stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
                finally:
                    signal.pthread_sigmask(signal.SIG_SETMASK, old_mask)
                report['audit_pid'] = process.pid
                report['audit_exit_code'] = process.wait(timeout=300)
            except BaseException as error:  # noqa: BLE001 -- persist interrupted or failed audits too
                report['audit_error'] = type(error).__name__+': '+str(error)
            finally:
                if process is not None:
                    try:
                        if process.poll() is None:
                            process.kill()
                        report['audit_child_exit_code'] = process.wait(timeout=30)
                        report['audit_termination_confirmed'] = True
                    except BaseException as error:  # noqa: BLE001 -- retain scoped cleanup uncertainty
                        report['audit_cleanup_error'] = type(error).__name__+': '+str(error)
                        report['audit_termination_confirmed'] = False
                        report['audit_exit_code'] = 1
    finally:
        old_mask = signal.pthread_sigmask(signal.SIG_BLOCK, previous)
        try:
            report['status'] = 'TERMINAL DIAGNOSTIC ONLY; '+('AUDIT COMPLETE' if not report['audit_exit_code'] else 'AUDIT REJECTED')
            report['audit_output_sha256'] = {name: sha(directory/name) for name in
                                            ('audit.json', 'local_replay.json', 'coupling_resultants.json', 'audit.log')
                                            if (directory/name).is_file()}
            save(directory/'report.json', report)
        finally:
            for signum, handler in previous.items():
                signal.signal(signum, handler)
            signal.pthread_sigmask(signal.SIG_SETMASK, old_mask)


def reference():
    if sha(ARCHIVE) != ARCHIVE_SHA:
        raise ValueError('Finest original archive changed')
    publication = json.loads(ARCHIVE.with_name('report.json').read_text())['runs']['0.0625']
    files = read_archive(ARCHIVE)
    if {n: hashlib.sha256(v).hexdigest() for n, v in files.items()} != publication['archive_contents_sha256']:
        raise ValueError('Archive contents differ from publication')
    verify_deck(files['frame.inp'].decode(), json.loads(files['frame.json']))
    return files


def deck_inventory(text, with_surfaces=False):
    """Expand literal C3D10 slave faces in deck contact-pair order, not geometry."""
    _, elements = mesh(text)
    surfaces, pairs, bricks, mode = {}, [], {}, None
    for raw in text.splitlines():
        line = raw.strip().upper()
        if not line or line.startswith('**'):
            continue
        if line.startswith('*'):
            cells = line.split(',')
            mode = None
            if cells[0] == '*ELEMENT' and 'TYPE=C3D8' in cells:
                mode = 'BRICK'
            if cells[0] == '*TIE':
                raise ValueError('Unexpected tie changes contact pair numbering')
            if cells[0] == '*SURFACE':
                names = [c.split('=', 1)[1] for c in cells[1:] if c.startswith('NAME=')]
                if len(names) != 1 or names[0] in surfaces:
                    raise ValueError('Missing/duplicate named surface')
                mode = names[0]
                surfaces[mode] = []
            elif cells[0] == '*CONTACT PAIR':
                if 'TYPE=MORTAR' not in cells:
                    raise ValueError('Unexpected contact formulation')
                mode = 'CONTACT_PAIR'
            continue
        if mode == 'BRICK':
            values = list(map(int, line.split(',')))
            if len(values) != 9 or values[0] in bricks:
                raise ValueError('Expected unique single-line C3D8 master element')
            bricks[values[0]] = values[1:]
        elif mode == 'CONTACT_PAIR':
            cells = line.split(',')
            if len(cells) != 2 or cells[0] not in surfaces or cells[1] not in surfaces:
                raise ValueError('Undefined slave/master pair')
            pairs.append(tuple(cells))
            mode = None
        elif mode is not None:
            surfaces[mode].append(line.split(','))
    if pairs != [('SLAVE_'+n, 'MASTER_'+n) for n in ('LEFT', 'RIGHT', 'KICKER')]:
        raise ValueError('Expected exact three ordered contact pairs')
    inventory, seen, memberships = [], set(), {}
    for pair, (slave, master) in enumerate(pairs):
        nodes = set()
        if not surfaces[slave] or not surfaces[master]:
            raise ValueError('Empty contact surface')
        for cells in surfaces[slave]:
            if len(cells) != 2 or cells[1] not in ('S1', 'S2', 'S3', 'S4') or int(cells[0]) not in elements:
                raise ValueError('Unsupported slave face')
            nodes.update(elements[int(cells[0])][i] for i in FACES[int(cells[1][1:])-1])
        if seen & nodes:
            raise ValueError('Overlapping slave pair nodes')
        seen.update(nodes)
        master_nodes = set()
        for cells in surfaces[master]:
            if len(cells) != 2 or cells[1] != 'S2' or int(cells[0]) not in bricks:
                raise ValueError('Expected literal C3D8 S2 master face')
            master_nodes.update(bricks[int(cells[0])][4:8])
        if len(master_nodes) != 4 or nodes & master_nodes:
            raise ValueError('Invalid master surface membership')
        memberships[pair] = {'slave': nodes, 'master': master_nodes}
        # CalculiX stores each tie's slave node numbers in ascending order.
        start = len(inventory)
        inventory.extend((pair, start+i, node) for i, node in enumerate(sorted(nodes)))
    if len(inventory) != 610:
        raise ValueError('Expected 610 original-frame contact nodes')
    if len(set.union(*(v['master'] for v in memberships.values()))) != 12:
        raise ValueError('Overlapping master patches')
    return (inventory, memberships) if with_surfaces else inventory


def check_inventory(log, expected):
    current, count = [], 0
    with log.open() as handle:
        for line in handle:
            if not line.startswith(PREFIX):
                continue
            row = json.loads(line[len(PREFIX):])
            if row['kind'] == 'BEGIN':
                if count and current != expected:
                    raise ValueError('Observer/deck ordered slave inventory differs')
                current, count = [], count+1
            elif row['kind'] == 'PRE_RAW':
                current.append((row['pair'], row['slot'], row['node']))
    if not count or current != expected:
        raise ValueError('Observer/deck ordered slave inventory differs')
    return count


def verified_observer():
    publication = json.loads(PUBLICATION.read_text())
    if publication['observer_image_id'] != IMAGE:
        raise ValueError('Unexpected observer image')
    for name, expected in publication['evidence_sha256'].items():
        if sha(Path(name)) != expected:
            raise ValueError('Observer published evidence changed')
    for name, expected in publication['sources_sha256'].items():
        if sha(Path(name)) != expected:
            raise ValueError('Observer published source changed')
    directory = Path(publication['build_directory'])
    built = json.loads((directory/'build_result.json').read_text())
    if built['exit_code'] or built['image_id'] != IMAGE:
        raise ValueError('Successful immutable observer build required')
    for name, expected in built['evidence_sha256'].items():
        if sha(directory/name) != expected:
            raise ValueError('Nested observer build evidence changed')
    manifest = (directory/'build_manifest.json').read_bytes()
    if subprocess.check_output(['docker', 'run', '--rm', IMAGE, 'cat', '/opt/ccx-kinematic-observer-2.21/build_manifest.json'], timeout=30) != manifest:
        raise ValueError('Actual image manifest differs')
    binaries = json.loads(manifest)['binary_sha256']
    actual = subprocess.check_output(['docker', 'run', '--rm', IMAGE, 'sha256sum', *sorted(binaries)], text=True, timeout=30)
    if {p: h for h, p in (line.split() for line in actual.splitlines())} != binaries:
        raise ValueError('Actual observer binary differs')
    return {'image_id': IMAGE, 'build_manifest_sha256': hashlib.sha256(manifest).hexdigest(),
            'binary_sha256': binaries, 'observer_publication_sha256': sha(PUBLICATION)}


def displacement_bounds(text):
    """Half last printed decimal unit at every DAT displacement endpoint."""
    result = {}
    pattern = r'displacements[^\n]*for set (\w+) and time\s+([\d.Ee+\-]+)\n(.*?)(?=\n\s*[A-Za-z]|\Z)'
    for name, endpoint, body in re.findall(pattern, text, re.DOTALL | re.IGNORECASE):
        result[name.upper(), float(endpoint)] = {
            int(c[0]): [float(Decimal(5).scaleb(Decimal(t).as_tuple().exponent-1)) for t in c[1:]]
            for line in body.splitlines() if len(c := line.split()) == 4 and c[0].isdigit()}
    return result


def coupling_resultants(coupling, endpoint, memberships, positions, parsed, bounds, supports=None):
    """Classify actual deck surface nodes and bind U before any force moment."""
    owners = {n: (pair, side) for pair, sides in memberships.items() for side, ids in sides.items() for n in ids}
    if len(owners) != sum(len(ids) for sides in memberships.values() for ids in sides.values()):
        raise ValueError('Ambiguous slave/master ownership')
    physical = coupling['physical_nodes']
    if len({r['node'] for r in physical}) != len(physical):
        raise ValueError('Duplicate coupled physical node')
    rows, max_difference = [], 0.
    for row in physical:
        node = row['node']
        if node not in owners:
            raise ValueError('Coupled node outside launched slave/master surfaces')
        pair, side = owners[node]
        name = 'WOODN' if side == 'slave' else 'GROUND_'+('LEFT', 'RIGHT', 'KICKER')[pair]
        printed = parsed.get(('displacements', name, endpoint), {}).get(node)
        tolerance = bounds.get((name, endpoint), {}).get(node)
        u, force = row['endpoint_displacement'], row['applied_contact_force']
        if (printed is None or tolerance is None or len(u) != 3 or len(force) != 3 or
                not all(math.isfinite(v) for v in (*u, *force, *printed, *tolerance, *positions[node]))):
            raise ValueError('Missing/nonfinite DAT/observer endpoint displacement')
        differences = [abs(a-b) for a, b in zip(u, printed, strict=True)]
        if any(d > t+1e-12 for d, t in zip(differences, tolerance, strict=True)):
            raise ValueError('Observer endpoint displacement differs from DAT print precision')
        max_difference = max(max_difference, *differences)
        rows.append((pair, side, node, [a+b for a, b in zip(positions[node], u, strict=True)], force))
    result = []
    for pair, sides in memberships.items():
        entry = {'patch': ('LEFT', 'RIGHT', 'KICKER')[pair]}
        for side, ids in sides.items():
            selected = [(p, f) for owner, which, _, p, f in rows if (owner, which) == (pair, side)]
            entry[side] = {'applied_force_n': [math.fsum(f[i] for _, f in selected) for i in range(3)],
                           'moment_about_origin_nmm': [math.fsum(cross(p, f)[i] for p, f in selected) for i in range(3)],
                           'uncoupled_surface_nodes': sorted(ids-{n for owner, which, n, _, _ in rows if (owner, which) == (pair, side)})}
        entry['slave_plus_master_force_n'] = [entry['slave']['applied_force_n'][i]+entry['master']['applied_force_n'][i] for i in range(3)]
        entry['slave_plus_master_moment_nmm'] = [entry['slave']['moment_about_origin_nmm'][i]+entry['master']['moment_about_origin_nmm'][i] for i in range(3)]
        if supports is not None:
            name = entry['patch']
            ids = supports[name]
            gu = parsed.get(('displacements', 'GROUND_'+name, endpoint), {})
            rf = parsed.get(('forces', 'GROUND_'+name, endpoint), {})
            if len(ids) != 4 or len(set(ids)) != 4 or not set(ids) <= gu.keys() & rf.keys():
                raise ValueError('Incomplete ground-bottom body-balance output')
            if any(not math.isfinite(v) for n in ids for v in (*gu[n], *rf[n], *positions[n])):
                raise ValueError('Nonfinite ground-bottom body-balance output')
            if any(abs(v) > 1e-9 for n in ids for v in gu[n]):
                raise ValueError('Fixed ground-bottom node moved')
            bottom = [([positions[n][i]+gu[n][i] for i in range(3)], rf[n]) for n in ids]
            force = [math.fsum(f[i] for _, f in bottom)+entry['master']['applied_force_n'][i] for i in range(3)]
            moment = [math.fsum(cross(p, f)[i] for p, f in bottom)+entry['master']['moment_about_origin_nmm'][i] for i in range(3)]
            entry['ground_body_balance'] = {'force_residual_n': force, 'moment_residual_nmm': moment,
                                            'force_pass': max(map(abs, force)) <= .1,
                                            'moment_pass': max(map(abs, moment)) <= 1.,
                                            'qualification': 'Massless numerical ground brick: applied master contact plus four bottom RF; nominal unchanged diagnostic thresholds, not capacity'}
        result.append(entry)
    return {'call_id': coupling['call_id'], 'time': endpoint, 'patches': result,
            'maximum_dat_displacement_difference_mm': max_difference,
            'qualification': 'Observed coupling only; absent matrix columns listed, no independent segmentation or weak-law acceptance'}


def audit(directory):
    terminal = json.loads((directory/'report.json').read_text())
    verify_audit_sources(directory, terminal)
    resource.setrlimit(resource.RLIMIT_AS, (MEMORY_LIMIT, MEMORY_LIMIT))
    files = reference()
    if (directory/'frame.inp').read_bytes() != files['frame.inp']:
        raise ValueError('Actual launched deck differs from archived baseline')
    if (terminal['exit_code'] != 0 or terminal['image_id'] != IMAGE or
            terminal.get('terminal_state_confirmed') is not True or 'stop_reason' in terminal):
        raise ValueError('Successful bound observer run required')
    for name, expected in terminal['output_sha256'].items():
        if sha(directory/name) != expected:
            raise ValueError('Terminal observer output changed')
    context = json.loads(files['frame.json'])
    calls = check_inventory(directory/'frame.log', deck_inventory(files['frame.inp'].decode()))
    local = replay((directory/'frame.log').read_text(), (directory/'frame.sta').read_text())
    accepted = [c for c in local['original_replay']['calls'] if c['accepted']]
    local_summary = {'calls': calls, 'accepted_calls': len(accepted),
                     'accepted_override_call_ids': local['original_replay']['accepted_override_call_ids'],
                     'status': local['status'], 'limitations': local['limitations'],
                     'accepted_nodes': [{'call_id': c['call_id'], 'step': c['step'], 'inc': c['inc'],
                                         'nodes': c['nodes']} for c in accepted],
                     'accepted_coupling': local['accepted_coupling']}
    save(directory/'local_replay.json', local_summary)
    dat = (directory/'frame.dat').read_text()
    current, bounds = blocks(dat), displacement_bounds(dat)
    _, memberships = deck_inventory(files['frame.inp'].decode(), with_surfaces=True)
    positions, _ = mesh(files['frame.inp'].decode())
    sta_rows = [line.split() for line in (directory/'frame.sta').read_text().splitlines()
                if len(line.split()) == 7 and all(c.isdigit() for c in line.split()[:4])]
    endpoints = {(int(r[0]), int(r[1])): float(r[4]) for r in sta_rows}
    identity = {c['call_id']: endpoints[c['step'], c['inc']] for c in accepted}
    if set(identity) != {c['call_id'] for c in local['accepted_coupling']}:
        raise ValueError('Accepted physical coupling coverage differs')
    force_reports = [coupling_resultants(c, identity[c['call_id']], memberships, positions, current, bounds, context['bottom_nodes'])
                     for c in local['accepted_coupling']]
    save(directory/'coupling_resultants.json', force_reports)
    del local, local_summary, accepted, bounds, dat
    baseline = blocks(files['frame.dat'].decode())
    if baseline.keys() != current.keys() or any(baseline[k].keys() != current[k].keys() for k in current):
        raise ValueError('DAT output coverage differs')
    differences = {kind: max(abs(a-b) for key in current if key[0] == kind
                             for node, vector in current[key].items()
                             for a, b in zip(vector, baseline[key][node], strict=True))
                   for kind in ('forces', 'displacements')}
    del baseline, current
    sta = lambda value: [line.split() for line in value.splitlines() if line.split() and line.split()[0].isdigit()]
    equal = sta(files['frame.sta'].decode()) == sta((directory/'frame.sta').read_text())
    context.update(output_sha256={}, elapsed_seconds=0, status='OBSERVER REPLAY DIAGNOSTIC ONLY')
    result_files = dict(files) | {'frame.json': json.dumps(context).encode(),
                                 'frame.dat': (directory/'frame.dat').read_bytes(),
                                 'frame.sta': (directory/'frame.sta').read_bytes()}
    result = global_replay(result_files)
    save(directory/'audit.json', {'maximum_printed_difference': differences, 'accepted_history_equal': equal,
                                 'output_and_history_equal': equal and not any(differences.values()),
                                 'global_gates_pass': all(e['global_gate_pass'] for e in result['diagnostic_endpoints']),
                                 'ground_body_gates_pass': all(p['ground_body_balance']['force_pass'] and p['ground_body_balance']['moment_pass']
                                                               for r in force_reports for p in r['patches']),
                                 'diagnostic_endpoints': result['diagnostic_endpoints'],
                                 'arithmetic_replay_pass': True, 'independent_deck_inventory_pass': True,
                                 'qualification': 'Observed-matrix kinematics/coupling checked; segmentation, local weak-law acceptance and physical capacity remain unvalidated'})
    body_pass = all(p['ground_body_balance']['force_pass'] and p['ground_body_balance']['moment_pass']
                    for r in force_reports for p in r['patches'])
    if not equal or any(differences.values()) or not all(e['global_gate_pass'] for e in result['diagnostic_endpoints']) or not body_pass:
        raise ValueError('Observer output/history equivalence, global or ground-body diagnostic gate failed')
    verify_audit_sources(directory, terminal)


def run():
    files, image = reference(), verified_observer()
    inventory = deck_inventory(files['frame.inp'].decode())
    if os.statvfs('.').f_bavail * os.statvfs('.').f_frsize < 2*1024**3:
        raise ValueError('At least 2 GiB disk reserve required')
    directory = Path(tempfile.mkdtemp(prefix='mortar-frame-observer-', dir='fea/generated')).resolve()
    for name in ('frame.inp', 'frame.json'):
        (directory/('reference.context.json' if name.endswith('json') else name)).write_bytes(files[name])
    (directory/'launch.py').write_bytes(Path(__file__).read_bytes())
    snapshots = directory/'launch_sources'
    snapshots.mkdir()
    for source in SOURCE_FILES[1:]:
        (snapshots/source).write_bytes((Path('fea')/source).read_bytes())
    name = directory.name
    command = ['docker', 'run', '--rm', '--name', name, '--memory=6g', '--memory-swap=6g',
               '-e', 'OMP_NUM_THREADS=2', '-v', str(directory)+':/work', '-w', '/work',
               IMAGE, BINARY, '-i', 'frame']
    report = {'status': 'RUNNING; NO PHYSICAL ACCEPTANCE', **image, 'command': command,
              'reference_archive_sha256': ARCHIVE_SHA, 'historical_image_binding': 'Not present in archived launch context',
              'prelaunch_sha256': {str(p.relative_to(directory)): sha(p) for p in directory.rglob('*') if p.is_file()},
              'audit_source_sha256': dict(LOADED_SOURCE_SHA256),
              'deck_inventory': inventory, 'max_seconds': SECONDS, 'stdout_limit_bytes': LOG_LIMIT}
    save(directory/'report.json', report)
    verify_audit_sources(directory, report)
    print('Evidence: '+str(directory), flush=True)
    report = monitor(command, directory, report)
    if report['exit_code'] == 0 and 'stop_reason' not in report:
        run_audit(directory, report)
    report['audit_output_sha256'] = {name: sha(directory/name) for name in
                                      ('audit.json', 'local_replay.json', 'coupling_resultants.json', 'audit.log')
                                      if (directory/name).is_file()}
    save(directory/'report.json', report)
    print(json.dumps({'directory': str(directory), 'status': report['status']}), flush=True)
    failure = report['exit_code'] or report.get('audit_exit_code', 0) or (124 if 'stop_reason' in report else 0)
    if failure:
        raise SystemExit(failure if failure > 0 else 1)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--audit', type=Path)
    args = parser.parse_args()
    audit(args.audit) if args.audit else run()
