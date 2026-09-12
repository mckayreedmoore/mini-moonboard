"""Native corner/midside coupons prove recovery; incompatible outputs fail shut."""
import hashlib
import json
import tarfile
from pathlib import Path

import numpy as np
import pytest

from fea import horizontal_panel_frame as frame
from fea import shell_surface_recovery as recovery


@pytest.fixture(scope='module')
def archive():
    with tarfile.open('fea/results/shell-spring-output-v2.tar.gz') as stream:
        data = {member.name: stream.extractfile(member).read() for member in stream.getmembers() if member.isfile()}
    root = json.loads(data['report.json'])
    for name, sha in root['artifact_sha256'].items():
        assert hashlib.sha256(data[name]).hexdigest() == sha
    assert root['source_sha256']['fea/shell_spring_output_probe.py'] == hashlib.sha256(Path('fea/shell_spring_output_probe.py').read_bytes()).hexdigest()
    return data


def inputs(archive, case):
    root = case+'/'
    return (json.loads(archive[root+'input.json']), archive[root+'frame.dat'].decode(),
            archive[root+'frame.frd'].decode(), archive[root+'frame.12d'].decode())


@pytest.mark.parametrize('case', ['direct', 'proxy', 'direct-all', 'proxy-all'])
def test_recovered_spring_forces_match_native_reactions_and_all_mpcs(archive, case):
    record, data, frd, expansion = inputs(archive, case)
    _, u, precision = recovery.recover(record, data, frd, expansion)
    rf = frame.panel_kernel.read_blocks(data)['forces']
    assert frame.mpc_intervals(record['equations'], u, precision)['passed']
    reactions = np.array([rf[row['fixed']] for row in record['supports']])
    applied = np.array(list(record['loads'].values())).sum(axis=0)
    assert np.all(abs(reactions.sum(axis=0)+applied) <= np.maximum(1.e-8, abs(reactions)*1.e-6).sum(axis=0))
    for row in record['supports']:
        fixed, attached = row['fixed'], row['attached']
        recovered = 1000.*(np.array(u[attached])-u[fixed])
        native = -np.array(rf[fixed])
        radius = 1000.*(np.array(precision[attached])+precision[fixed])+np.maximum(1.e-8, abs(native)*1.e-6)
        assert np.all(abs(recovered-native) <= radius)
    if case.startswith('direct'):
        assert not json.loads(archive[case+'/report.json'])['all_spring_recoveries_passed']


def test_changed_non_shell_output_cannot_mix_cycles(archive):
    record, data, frd, expansion = inputs(archive, 'proxy')
    target = record['supports'][0]['attached']
    lines, active = [], False
    for line in frd.splitlines():
        if line.startswith(' -4  DISP'):
            active = True
        if active and line.startswith(' -1') and int(line[3:13]) == target:
            line = line[:13]+f'{float(line[13:25])+1.:12.5E}'+line[25:]
        lines.append(line)
    with pytest.raises(ValueError, match='original-node displacement intervals disagree'):
        recovery.recover(record, data, '\n'.join(lines), expansion)


def test_changed_original_node_identity_is_rejected(archive):
    record, data, frd, expansion = inputs(archive, 'direct')
    changed = expansion.replace('          1          2', '         99          2', 1)
    with pytest.raises(ValueError, match='topology differs'):
        recovery.recover(record, data, frd, changed)


def test_binary32_then_decimal_rounding_covers_native_small_displacement():
    # v3/v4 k10000 cycle00 node3067 X. A possible solver double inside the
    # DAT interval reproduces both native tokens through the actual writers.
    actual = .000997105552
    dat, frd = '9.971056E-04', '9.97105E-04'
    assert format(actual, '.6E') == dat
    assert format(float(np.float32(actual)), '.5E') == frd
    difference = abs(float(dat)-float(frd))
    dat_radius = recovery.half_last_place(dat)
    assert difference > dat_radius+recovery.half_last_place(frd)
    radius = dat_radius+recovery.frd_roundoff(frd)
    assert difference <= radius
    assert abs(float(dat)-(float(frd)-1.e-9)) > radius


@pytest.mark.parametrize('value', [0., 1.e-42, .000997105552, -12.3456789, 1024.000061])
def test_frd_precision_bounds_both_writer_roundings(value):
    token = format(float(np.float32(value)), '.5E')
    assert abs(value-float(token)) <= recovery.frd_roundoff(token)
