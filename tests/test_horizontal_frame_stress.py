"""Integration-point ownership and tensor axes are explicit, never a yield pass."""
import copy

import numpy as np
import pytest

from fea import horizontal_frame_stress as stress


def output(count=27):
    lines = ['stresses (elem, integ.pnt.,sxx,syy,szz,sxy,sxz,syz) for set WOOD and time 1.000000D+00']
    lines += [f'1 {i} 10 20 -30 4 5 6' for i in range(1, count+1)]
    lines += ['global coordinates (elem, integ.pnt.,x,y,z) for set WOOD and time 1.000000E+00']
    lines += [f'1 {i} 0 0 {i}' for i in range(1, count+1)]
    return '\n'.join(lines)


def record():
    return {'candidate': 'test', 'elements': {'1': ['C3D20', [], 'WOOD'], '2': ['SPRING2', [], 'SPR']},
            'members': [{'name': 'WOOD', 'axis': [0, 0, 1], 'section_u': [1, 0, 0], 'section_v': [0, 1, 0]}],
            'nodes': {}, 'stress_output': {'global': True, 'variables': ['S', 'COORD'],
                                          'integration_points': {'C3D20': 27, 'S8': 27}}}


def test_ccx_component_order_and_grain_rotation():
    tensor = stress.transform([10, 20, -30, 4, 5, 6], [[0, 0, 1], [1, 0, 0], [0, 1, 0]])
    assert tensor == pytest.approx(np.array([[-30, 5, 6], [5, 10, 4], [6, 4, 20]]))
    s = 2**-.5
    rotated = stress.transform([100, 0, 0, 0, 0, 0], [[s, s, 0], [-s, s, 0], [0, 0, 1]])
    assert rotated[0, 0] == pytest.approx(50)
    assert rotated[0, 1] == pytest.approx(-50)
    with pytest.raises(ValueError, match='orthonormal'):
        stress.transform([1]*6, [[2, 0, 0], [0, 1, 0], [0, 0, 1]])


def test_complete_ip_envelope_retains_witness_and_no_strength_pass():
    result = stress.assess(record(), output())
    assert result['integration_point_count'] == 27
    group = result['groups'][0]
    assert group['extrema']['normal_grain']['minimum']['value_mpa'] == -30
    assert group['extrema']['normal_grain']['minimum']['coordinate_xyz_mm'] == [0, 0, 1]
    assert group['extrema']['shear_on_axis_0_plane_magnitude']['maximum']['value_mpa'] == pytest.approx(61**.5)
    assert not result['qualified_for_design'] and not result['member_strength_passed'] and not result['plywood_strength_passed']


@pytest.mark.parametrize('bad', [output(26), output().replace('for set WOOD', 'for set OTHER', 1),
                                  output().replace('1 2 10 20 -30 4 5 6', '1 1 10 20 -30 4 5 6'),
                                  output().replace('10 20 -30', 'nan 20 -30', 1)])
def test_partial_duplicate_wrong_owner_and_nonfinite_output_rejected(bad):
    with pytest.raises(ValueError):
        stress.assess(record(), bad)


def test_missing_global_stress_metadata_rejected():
    data = copy.deepcopy(record())
    data['stress_output']['global'] = False
    with pytest.raises(ValueError, match='global'):
        stress.assess(data, output())


def cycle_evidence(tmp_path):
    import hashlib
    import json

    cycle = tmp_path/'cycle-02'
    cycle.mkdir()
    for name, text in [('input.json', '{}'), ('frame.dat', 'stress data'), ('frame.inp', 'deck')]:
        (cycle/name).write_text(text)
    digest = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
    report = {'artifact_sha256': {name: digest(cycle/name) for name in ('input.json', 'frame.dat', 'frame.inp')},
              'global_equilibrium_passed': True, 'mpc_check_passed': True, 'closed_bearing_assumption_passed': True}
    (cycle/'report.json').write_text(json.dumps(report))
    snapshots = tmp_path/'source_snapshots'
    snapshots.mkdir()
    (snapshots/'source.py').write_text('authenticated source')
    parent = {'final_cycle_directory': 'cycle-02', 'contact_diagnostic_checks_passed': True,
              'contact_cycles': [{'directory': 'cycle-02', 'report_sha256': digest(cycle/'report.json'),
                                  'bearing_complementarity_passed': True}],
              'artifact_sha256': {'cycle-02/'+p.name: digest(p) for p in cycle.iterdir()},
              'source_sha256': {'source.py': digest(snapshots/'source.py')}}
    (tmp_path/'report.json').write_text(json.dumps(parent))
    return cycle


@pytest.mark.parametrize('from_parent', [False, True])
def test_cli_authenticates_cycle_through_parent_manifest(tmp_path, monkeypatch, from_parent):
    cycle = cycle_evidence(tmp_path)
    monkeypatch.setattr(stress, 'assess', lambda record, data: {'qualified_for_design': False})
    result = stress.from_directory(tmp_path if from_parent else cycle)
    assert result['native_numerical_gates_passed'] and result['parent_manifest_sha256']
    assert not result['qualified_for_design']
    (cycle/'frame.dat').write_text('tampered')
    with pytest.raises(ValueError, match='evidence hash'):
        stress.from_directory(cycle)


def test_cli_rejects_cycle_report_or_snapshot_not_owned_by_parent(tmp_path, monkeypatch):
    import json

    cycle = cycle_evidence(tmp_path)
    monkeypatch.setattr(stress, 'assess', lambda record, data: {})
    source = tmp_path/'source_snapshots/source.py'
    source.write_text('different source')
    with pytest.raises(ValueError, match='source snapshot'):
        stress.from_directory(cycle)
    source.write_text('authenticated source')
    report = json.loads((cycle/'report.json').read_text())
    report['global_equilibrium_passed'] = False
    (cycle/'report.json').write_text(json.dumps(report))
    with pytest.raises(ValueError, match='parent manifest'):
        stress.from_directory(cycle)
