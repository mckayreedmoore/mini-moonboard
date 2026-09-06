"""No solver: bind original deck faces to ordered observer slave identities."""
import ast
import json
import signal
import subprocess
from pathlib import Path

import pytest

from fea.mortar_frame_observer import (
    check_inventory,
    coupling_resultants,
    deck_inventory,
    displacement_bounds,
    reference,
)


@pytest.fixture(scope='module')
def deck():
    return reference()['frame.inp'].decode()


def test_exact_archive_inventory(deck):
    inventory = deck_inventory(deck)
    assert len(inventory) == 610
    assert [slot for _, slot, _ in inventory] == list(range(610))
    assert len({node for _, _, node in inventory}) == 610
    for pair in range(3):
        nodes = [node for p, _, node in inventory if p == pair]
        assert nodes and nodes == sorted(nodes)
    _, surfaces = deck_inventory(deck, with_surfaces=True)
    assert [len(surfaces[p]['slave']) for p in range(3)] == [43, 43, 524]
    assert [len(surfaces[p]['master']) for p in range(3)] == [4, 4, 4]


@pytest.mark.parametrize('old,new', [
    ('SLAVE_LEFT,MASTER_LEFT', 'SLAVE_RIGHT,MASTER_RIGHT'),
    ('SLAVE_RIGHT,MASTER_RIGHT', 'SLAVE_UNKNOWN,MASTER_RIGHT'),
    ('*CONTACT PAIR,INTERACTION=FLOOR,TYPE=MORTAR\nSLAVE_LEFT,MASTER_LEFT\n', ''),
    ('TYPE=MORTAR', 'TYPE=SURFACE TO SURFACE'),
])
def test_wrong_missing_or_reordered_pairs_fail(deck, old, new):
    with pytest.raises(ValueError):
        deck_inventory(deck.replace(old, new, 1))


def test_observer_inventory_checked_every_call(deck, tmp_path):
    inventory = deck_inventory(deck)
    log = tmp_path/'stream.log'
    rows = []
    for call in (1, 2):
        rows.append({'kind': 'BEGIN', 'call_id': call})
        rows.extend({'kind': 'PRE_RAW', 'call_id': call, 'pair': p, 'slot': s, 'node': n}
                    for p, s, n in inventory)
    def write():
        log.write_text(''.join('MORTAR_OBSERVER '+json.dumps(row)+'\n' for row in rows))
    write()
    assert check_inventory(log, inventory) == 2
    rows[-1]['node'] += 1
    write()
    with pytest.raises(ValueError, match='ordered slave inventory'):
        check_inventory(log, inventory)
    rows.pop()
    write()
    with pytest.raises(ValueError, match='ordered slave inventory'):
        check_inventory(log, inventory)


def test_wrong_master_face_rejected(deck):
    changed = deck.replace('*SURFACE,NAME=MASTER_LEFT\n32512,S2', '*SURFACE,NAME=MASTER_LEFT\n32512,S1')
    assert changed != deck
    with pytest.raises(ValueError, match='master face'):
        deck_inventory(changed)


def result_fixture():
    coupling = {'call_id': 1, 'physical_nodes': [
        {'node': 1, 'endpoint_displacement': [0., 0., 0.], 'applied_contact_force': [0., 0., 10.]},
        {'node': 2, 'endpoint_displacement': [0., 0., 0.], 'applied_contact_force': [0., 0., -10.]},
    ]}
    members = {0: {'slave': {1, 3}, 'master': {2}}}
    positions = {1: [2., 0., 0.], 2: [2., 0., 0.]}
    parsed = {('displacements', 'WOODN', 1.): {1: [0., 0., 0.]},
              ('displacements', 'GROUND_LEFT', 1.): {2: [0., 0., 0.]}}
    bounds = {('WOODN', 1.): {1: [5e-8]*3}, ('GROUND_LEFT', 1.): {2: [5e-8]*3}}
    return coupling, 1., members, positions, parsed, bounds


def test_bound_physical_forces_use_deformed_positions_and_list_absent_columns():
    args = result_fixture()
    args[0]['physical_nodes'][0]['endpoint_displacement'][0] = .1
    args[4]['displacements', 'WOODN', 1.][1][0] = .1
    result = coupling_resultants(*args)
    patch = result['patches'][0]
    assert patch['slave']['moment_about_origin_nmm'] == pytest.approx([0., -21., 0.])
    assert patch['slave_plus_master_force_n'] == [0., 0., 0.]
    assert patch['slave_plus_master_moment_nmm'] == pytest.approx([0., -1., 0.])
    assert patch['slave']['uncoupled_surface_nodes'] == [3]


@pytest.mark.parametrize('bad', ['outside', 'displacement', 'nonfinite', 'missing_dat', 'duplicate'])
def test_reject_unbound_or_invalid_physical_moments(bad):
    args = result_fixture()
    row = args[0]['physical_nodes'][0]
    if bad == 'outside':
        row['node'] = 99
    elif bad == 'displacement':
        row['endpoint_displacement'][0] = 1e-6
    elif bad == 'nonfinite':
        row['applied_contact_force'][0] = float('nan')
    elif bad == 'missing_dat':
        args[4].clear()
    else:
        args[0]['physical_nodes'].append(dict(row))
    with pytest.raises(ValueError):
        coupling_resultants(*args)


def test_displacement_precision_at_intermediate_endpoints():
    text = ' displacements for set WOODN and time 0.0625\n\n 1 1.234567E-03 0.000000E+00 -2.000000E+01\n'
    assert displacement_bounds(text)['WOODN', .0625][1] == pytest.approx([5e-10, 5e-7, 5e-6])


def test_ground_body_balance_is_not_pair_cancellation():
    args = result_fixture()
    bottom = [10, 11, 12, 13]
    coordinates = ([1., -1., -100.], [3., -1., -100.], [3., 1., -100.], [1., 1., -100.])
    for n, xyz in zip(bottom, coordinates, strict=True):
        args[3][n] = xyz
        args[4]['displacements', 'GROUND_LEFT', 1.][n] = [0., 0., 0.]
    args[4]['forces', 'GROUND_LEFT', 1.] = {n: [0., 0., 2.5] for n in bottom}
    checked = coupling_resultants(*args, supports={'LEFT': bottom})['patches'][0]
    assert checked['ground_body_balance']['force_pass']
    assert checked['ground_body_balance']['moment_pass']
    args[4]['forces', 'GROUND_LEFT', 1.][10][2] += 1.
    args[4]['forces', 'GROUND_LEFT', 1.][11][2] -= 1.
    checked = coupling_resultants(*args, supports={'LEFT': bottom})['patches'][0]
    assert checked['ground_body_balance']['force_pass']
    assert not checked['ground_body_balance']['moment_pass']
    args[4]['forces', 'GROUND_LEFT', 1.][10][2] -= 1.
    args[4]['forces', 'GROUND_LEFT', 1.][11][2] += 1.
    args[4]['forces', 'GROUND_LEFT', 1.][10][2] += 2.
    checked = coupling_resultants(*args, supports={'LEFT': bottom})['patches'][0]
    assert checked['slave_plus_master_force_n'] == [0., 0., 0.]
    assert not checked['ground_body_balance']['force_pass']
    assert not checked['ground_body_balance']['moment_pass']
    args[4]['displacements', 'GROUND_LEFT', 1.][10][0] = .1
    with pytest.raises(ValueError, match='bottom node moved'):
        coupling_resultants(*args, supports={'LEFT': bottom})


@pytest.mark.parametrize('solver_exit,audit_exit', [(7, 0), (0, 9), (0, 0)])
def test_runner_propagates_failed_solver_or_audit(monkeypatch, tmp_path, solver_exit, audit_exit):
    from fea import mortar_frame_observer as module
    monkeypatch.setattr(module, 'reference', lambda: {'frame.inp': b'fixture', 'frame.json': b'{}'})
    monkeypatch.setattr(module, 'verified_observer', lambda: {'image_id': module.IMAGE})
    monkeypatch.setattr(module, 'deck_inventory', lambda text: [])
    work = tmp_path/'run'
    work.mkdir()
    monkeypatch.setattr(module.tempfile, 'mkdtemp', lambda **kw: str(work))
    class Process:
        pid = 123
        def __init__(self, command, **kwargs):
            self.is_audit = '--audit' in command
            if self.is_audit:
                assert kwargs['start_new_session'] is True
                for name in ('audit.json', 'local_replay.json', 'coupling_resultants.json'):
                    (work/name).write_text('fixture artifact')
            else:
                assert module.IMAGE in command and module.BINARY in command
                assert '--memory=6g' in command and '--memory-swap=6g' in command
                assert 'OMP_NUM_THREADS=2' in command
        def poll(self):
            return audit_exit if self.is_audit else solver_exit
        def wait(self, **kwargs):
            assert kwargs['timeout'] in ((300, 30) if self.is_audit else (30,))
            return self.poll()
    monkeypatch.setattr(module.subprocess, 'Popen', Process)
    monkeypatch.setattr(module.subprocess, 'run', lambda command, **kw: subprocess.CompletedProcess(command, 0, 'false\n', ''))
    if solver_exit or audit_exit:
        with pytest.raises(SystemExit) as error:
            module.run()
        assert error.value.code == solver_exit+audit_exit
    else:
        module.run()
    report = json.loads((work/'report.json').read_text())
    assert report['exit_code'] == solver_exit
    if solver_exit == 0:
        assert report['audit_exit_code'] == audit_exit
        assert set(report['audit_output_sha256']) == {'audit.json', 'local_replay.json', 'coupling_resultants.json', 'audit.log'}
        for name, expected in report['audit_output_sha256'].items():
            assert module.sha(work/name) == expected
    else:
        assert report['audit_output_sha256'] == {}


def test_import_time_project_dependency_inventory_is_complete():
    from fea import mortar_frame_observer as module
    needed, pending = set(), ['mortar_frame_observer.py']
    while pending:
        name = pending.pop()
        if name in needed:
            continue
        needed.add(name)
        for node in ast.parse((module.PROJECT_ROOT/'fea'/name).read_text()).body:
            if isinstance(node, ast.ImportFrom) and node.module and node.module.startswith('fea.'):
                pending.append(node.module.removeprefix('fea.')+'.py')
    assert needed == set(module.SOURCE_FILES)


@pytest.mark.parametrize('corruption', ['runner', 'dependency', 'snapshot', 'digest', 'loaded', 'origin'])
def test_source_drift_rejected(monkeypatch, tmp_path, corruption):
    from fea import mortar_frame_observer as module
    root, directory = tmp_path/'project', tmp_path/'evidence'
    (root/'fea').mkdir(parents=True)
    (directory/'launch_sources').mkdir(parents=True)
    report = {'audit_source_sha256': {}, 'prelaunch_sha256': {}}
    paths = {}
    for name in module.SOURCE_FILES:
        path = root/'fea'/name
        path.write_text('# '+name+'\n')
        paths[name] = path.resolve()
        archive = 'launch.py' if name == 'mortar_frame_observer.py' else 'launch_sources/'+name
        (directory/archive).write_bytes(path.read_bytes())
        report['audit_source_sha256'][name] = report['prelaunch_sha256'][archive] = module.sha(path)
    monkeypatch.setattr(module, 'PROJECT_ROOT', root)
    monkeypatch.setattr(module, 'IMPORTED_PATHS', paths)
    monkeypatch.setattr(module, 'LOADED_SOURCE_SHA256', dict(report['audit_source_sha256']))
    module.verify_audit_sources(directory, report)
    if corruption == 'runner':
        (root/'fea/mortar_frame_observer.py').write_text('drift')
    elif corruption == 'dependency':
        (root/'fea/mortar_linear_law.py').write_text('drift')
    elif corruption == 'snapshot':
        (directory/'launch_sources/mortar_linear_law.py').write_text('drift')
    elif corruption == 'digest':
        report['prelaunch_sha256']['launch.py'] = 'wrong'
    elif corruption == 'loaded':
        module.LOADED_SOURCE_SHA256['mortar_linear_law.py'] = 'wrong'
    else:
        paths['mortar_linear_law.py'] = Path('/unexpected/module.py')
    with pytest.raises(ValueError, match='source drift'):
        module.verify_audit_sources(directory, report)


@pytest.mark.parametrize('mode', ['finished_log', 'finished_time', 'running_log', 'running_time', 'interrupt', 'cleanup_failure', 'inspection_failure', 'exited_client_live_container'])
def test_monitor_budget_interruption_and_scoped_cleanup(monkeypatch, tmp_path, mode):
    from fea import mortar_frame_observer as module
    ticks, commands = [0.], []
    running = mode.startswith('running') or mode in ('interrupt', 'cleanup_failure')
    alive = [running or mode == 'exited_client_live_container']
    command = ['docker', 'run', '--name', 'only-this-unique-test-container']
    monkeypatch.setattr(module, 'LOG_LIMIT', 10)
    monkeypatch.setattr(module, 'SECONDS', 10)
    monkeypatch.setattr(module.time, 'monotonic', lambda: ticks[0])
    class Process:
        pid = 123
        def __init__(self, command, **kwargs):
            self.interrupted = False
            if 'log' in mode:
                kwargs['stdout'].write('x'*11)
                kwargs['stdout'].flush()
            if 'time' in mode:
                ticks[0] = 11.
        def poll(self):
            if mode in ('interrupt', 'cleanup_failure') and not self.interrupted:
                self.interrupted = True
                raise KeyboardInterrupt('test stop')
            return None if running else 0
        def kill(self):
            pass
        def wait(self, **kwargs):
            return 137 if running else 0
    def docker(command, **kwargs):
        commands.append(command)
        assert command[-1] == 'only-this-unique-test-container'
        if command[1] == 'inspect':
            if mode == 'inspection_failure':
                return subprocess.CompletedProcess(command, 1, '', 'daemon unavailable')
            return subprocess.CompletedProcess(command, 0, 'true\n' if alive[0] else 'false\n', '')
        if mode != 'cleanup_failure':
            alive[0] = False
        return subprocess.CompletedProcess(command, 1 if mode == 'cleanup_failure' else 0, '', 'fixture')
    monkeypatch.setattr(module.subprocess, 'Popen', Process)
    monkeypatch.setattr(module.subprocess, 'run', docker)
    report = module.monitor(command, tmp_path)
    assert 'stop_reason' in report
    assert any(c[1] == 'kill' for c in commands) == (running or mode == 'exited_client_live_container')
    assert report['terminal_state_confirmed'] == (mode not in ('cleanup_failure', 'inspection_failure'))
    if mode == 'cleanup_failure':
        assert 'cleanup_error' in report and report['exit_code'] != 0


def test_solver_spawn_interrupt_is_deferred_until_handle_assignment_and_reaped_before_inspection(monkeypatch, tmp_path):
    from fea import mortar_frame_observer as module
    events, blocked, delivered = [], [False], [False]
    def mask(how, values):
        if how == signal.SIG_BLOCK:
            blocked[0] = True
            return set()
        blocked[0] = False
        if not delivered[0]:
            delivered[0] = True
            events.append('deliver_pending_interrupt')
            signal.getsignal(signal.SIGINT)(signal.SIGINT, None)
    class Process:
        pid = 987
        def __init__(self, command, **kwargs):
            assert blocked[0]
            events.append('created')
        def poll(self):
            return None
        def kill(self):
            events.append('client_killed')
        def wait(self, timeout):
            assert timeout == 30
            events.append('client_reaped')
            return -9
    def inspect(command, **kwargs):
        assert events[-1] == 'client_reaped'
        assert command[1] == 'inspect' and command[-1] == 'only-spawn-test'
        events.append('absent_container_confirmed')
        return subprocess.CompletedProcess(command, 1, '', 'No such object: only-spawn-test')
    monkeypatch.setattr(module.signal, 'pthread_sigmask', mask)
    monkeypatch.setattr(module.subprocess, 'Popen', Process)
    monkeypatch.setattr(module.subprocess, 'run', inspect)
    report = module.monitor(['docker', 'run', '--name', 'only-spawn-test'], tmp_path)
    assert report['docker_client_pid'] == 987
    assert report['terminal_state_confirmed'] and report['exit_code'] == -9
    assert events == ['created', 'deliver_pending_interrupt', 'client_killed', 'client_reaped', 'absent_container_confirmed']


def test_solver_terminal_report_is_persisted_before_interrupt_during_raw_hash(monkeypatch, tmp_path):
    from fea import mortar_frame_observer as module
    blocked, pending = [False], [False]
    original_sha = module.sha
    def mask(how, values):
        if how == signal.SIG_BLOCK:
            old = {signal.SIGINT, signal.SIGTERM} if blocked[0] else set()
            blocked[0] = True
            return old
        blocked[0] = bool(values)
        if not blocked[0] and pending[0]:
            raise KeyboardInterrupt('deferred during raw hashing')
    def sha(path):
        value = original_sha(path)
        if path.name == 'frame.log':
            assert blocked[0]
            pending[0] = True
        return value
    class Process:
        pid = 456
        def __init__(self, command, **kwargs):
            assert blocked[0]
            kwargs['stdout'].write('retained raw solver evidence')
        def poll(self):
            return 0
        def wait(self, timeout):
            return 0
    monkeypatch.setattr(module.signal, 'pthread_sigmask', mask)
    monkeypatch.setattr(module, 'sha', sha)
    monkeypatch.setattr(module.subprocess, 'Popen', Process)
    monkeypatch.setattr(module.subprocess, 'run', lambda *args, **kwargs: subprocess.CompletedProcess(args, 0, 'false\n', ''))
    with pytest.raises(KeyboardInterrupt, match='raw hashing'):
        module.monitor(['docker', 'run', '--name', 'hash-window-only'], tmp_path, {'status': 'RUNNING', 'sentinel': 'retained'})
    report = json.loads((tmp_path/'report.json').read_text())
    assert report['status'].startswith('TERMINAL') and report['terminal_state_confirmed']
    assert report['sentinel'] == 'retained'
    assert report['output_sha256']['frame.log'] == original_sha(tmp_path/'frame.log')


@pytest.mark.parametrize('stderr,absent', [
    ('error: no such object: mortar-frame-observer-2jr09aeb\n', True),
    ('Error: No such object: mortar-frame-observer-2jr09aeb\n', True),
    ('error: no such object: mortar-frame-observer-2jr09aeb-other\n', False),
    ('error: no such object: different-container\n', False),
    ('Error: No such object: different-container\n', False),
    ('Error: No such network: mortar-frame-observer-2jr09aeb\n', False),
    ('Cannot connect to the Docker daemon\n', False),
    ('permission denied\n', False),
])
def test_monitor_exact_named_container_absence_error(monkeypatch, tmp_path, stderr, absent):
    from fea import mortar_frame_observer as module
    class Process:
        pid = 321
        def __init__(self, command, **kwargs):
            pass
        def poll(self):
            return 0
        def wait(self, timeout):
            return 0
    def inspect(command, **kwargs):
        assert command == ['docker', 'inspect', '--format', '{{.State.Running}}', 'mortar-frame-observer-2jr09aeb']
        return subprocess.CompletedProcess(command, 1, '', stderr)
    monkeypatch.setattr(module.subprocess, 'Popen', Process)
    monkeypatch.setattr(module.subprocess, 'run', inspect)
    result = module.monitor(['docker', 'run', '--name', 'mortar-frame-observer-2jr09aeb'], tmp_path)
    assert result['terminal_state_confirmed'] is absent
    assert ('stop_reason' in result) is not absent


@pytest.mark.parametrize('failure', ['timeout', 'sigint', 'sigterm'])
def test_audit_child_cleanup_and_partial_hashes_on_timeout_or_signal(monkeypatch, tmp_path, failure):
    from fea import mortar_frame_observer as module
    monkeypatch.setattr(module, 'verify_audit_sources', lambda *args: None)
    killed = []
    before = {s: signal.getsignal(s) for s in (signal.SIGINT, signal.SIGTERM)}
    class Process:
        pid = 12345
        def __init__(self, command, **kwargs):
            assert kwargs['start_new_session'] is True and '--audit' in command
            (tmp_path/'local_replay.json').write_text('partial evidence')
        def wait(self, timeout):
            if timeout == 300:
                if failure == 'timeout':
                    raise subprocess.TimeoutExpired('audit', timeout)
                sig = signal.SIGINT if failure == 'sigint' else signal.SIGTERM
                signal.getsignal(sig)(sig, None)
            assert timeout == 30 and killed == [12345]
            return -9
        def poll(self):
            return -9 if killed else None
        def kill(self):
            killed.append(self.pid)
    monkeypatch.setattr(module.subprocess, 'Popen', Process)
    report = {'exit_code': 0}
    module.run_audit(tmp_path, report)
    assert killed == [12345] and report['audit_exit_code'] != 0
    assert report['audit_termination_confirmed']
    assert json.loads((tmp_path/'report.json').read_text()) == report
    assert report['audit_output_sha256']['local_replay.json'] == module.sha(tmp_path/'local_replay.json')
    assert {s: signal.getsignal(s) for s in before} == before


@pytest.mark.parametrize('corruption', [None, 'printed_output', 'history', 'global_gate', 'body_gate'])
def test_actual_audit_wiring_and_independent_failure_gates(monkeypatch, tmp_path, corruption):
    """Patch heavyweight provenance/solver replay, not audit's STA/DAT/moment wiring."""
    from fea import mortar_frame_observer as module
    coupling, _, members, positions, _, _ = result_fixture()
    bottom = [10, 11, 12, 13]
    for n, p in zip(bottom, ([1., -1., -100.], [3., -1., -100.], [3., 1., -100.], [1., 1., -100.]), strict=True):
        positions[n] = p
    def dat(wood_force=0., couple=0.):
        sections = [
            ('displacements', 'WOODN', {1: [0., 0., 0.]}),
            ('forces', 'WOODN', {1: [wood_force, 0., 0.]}),
            ('displacements', 'GROUND_LEFT', {n: [0., 0., 0.] for n in [2, *bottom]}),
            ('forces', 'GROUND_LEFT', {10: [0., 0., 2.5+couple], 11: [0., 0., 2.5-couple],
                                       12: [0., 0., 2.5], 13: [0., 0., 2.5]}),
        ]
        return ''.join(f' {kind} for set {name} and time 1.000000E+00\n\n'+
                       ''.join(str(n)+' '+ ' '.join(f'{v:.6E}' for v in vec)+'\n' for n, vec in nodes.items())+'\n'
                       for kind, name, nodes in sections)
    baseline = dat(couple=1. if corruption == 'body_gate' else 0.)
    actual = dat(wood_force=1.) if corruption == 'printed_output' else baseline
    sta = '1 1 1 2 1.000000E+00 1.000000E+00 1.000000E+00\n'
    files = {'frame.inp': b'compact fixture', 'frame.dat': baseline.encode(), 'frame.sta': sta.encode(),
             'frame.json': json.dumps({'bottom_nodes': {'LEFT': bottom}}).encode()}
    (tmp_path/'frame.inp').write_bytes(files['frame.inp'])
    (tmp_path/'frame.dat').write_text(actual)
    (tmp_path/'frame.sta').write_text(sta.replace('1 1 1 2', '1 1 1 3') if corruption == 'history' else sta)
    (tmp_path/'frame.log').write_text('bound compact observer fixture')
    terminal = {'exit_code': 0, 'image_id': module.IMAGE, 'terminal_state_confirmed': True,
                'output_sha256': {p.name: module.sha(p) for p in tmp_path.iterdir()}}
    (tmp_path/'report.json').write_text(json.dumps(terminal))
    monkeypatch.setattr(module, 'verify_audit_sources', lambda *args: None)
    resource_limits = []
    monkeypatch.setattr(module.resource, 'setrlimit', lambda *args: resource_limits.append(args))
    monkeypatch.setattr(module, 'reference', lambda: files)
    monkeypatch.setattr(module, 'deck_inventory', lambda text, with_surfaces=False: ([], members) if with_surfaces else [])
    monkeypatch.setattr(module, 'check_inventory', lambda *args: 1)
    monkeypatch.setattr(module, 'mesh', lambda text: (positions, {}))
    local = {'calls_checked': 1, 'status': 'fixture', 'limitations': 'fixture', 'accepted_coupling': [coupling],
             'original_replay': {'accepted_override_call_ids': [], 'calls': [
                 {'call_id': 1, 'step': 1, 'inc': 1, 'accepted': True, 'nodes': []}]}}
    monkeypatch.setattr(module, 'replay', lambda text, sta: local)
    monkeypatch.setattr(module, 'global_replay', lambda files: {
        'diagnostic_endpoints': [{'time': 1., 'global_gate_pass': corruption != 'global_gate'}]})
    if corruption is None:
        module.audit(tmp_path)
    else:
        with pytest.raises(ValueError, match='diagnostic gate failed'):
            module.audit(tmp_path)
    result = json.loads((tmp_path/'audit.json').read_text())
    assert resource_limits == [(module.resource.RLIMIT_AS, (6*1024**3, 6*1024**3))]
    assert result['output_and_history_equal'] == (corruption not in ('printed_output', 'history'))
    assert result['global_gates_pass'] == (corruption != 'global_gate')
    assert result['ground_body_gates_pass'] == (corruption != 'body_gate')
    force = json.loads((tmp_path/'coupling_resultants.json').read_text())[0]
    assert force['call_id'] == 1 and force['time'] == 1.
    assert json.loads((tmp_path/'local_replay.json').read_text())['accepted_coupling'] == [coupling]
