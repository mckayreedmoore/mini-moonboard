"""Independent nonsymmetric two-body coupling examples and corrupt packets."""
import copy

import pytest
from test_mortar_observer_replay import fixture, stream

from fea.mortar_kinematic_replay import replay


def coupled_fixture():
    events, sta = fixture()
    output = []
    for call_id in sorted({r['call_id'] for r in events}):
        rows = copy.deepcopy([r for r in events if r['call_id'] == call_id])
        laws = [r for r in rows if r['kind'] == 'LAW']
        post = [r for r in rows if r['kind'] == 'POST_RAW_AFTER_ACTIVE_LOOP']
        # Physical columns7/8 are slave,9 master. Nonsymmetric Dd and nonzero
        # off-diagonal terms expose row/column and sign mistakes.
        matrix = {7: [1., .2], 8: [.3, 1.], 9: [-1.3, -1.2]}
        vold = {7: [.1, .2, .3], 8: [.2, .3, .4], 9: [.05, .06, .07]}
        vini = {n: [.01, .02, .03] for n in matrix}
        history = [[sum(matrix[n][s]*(vold[n][i]-vini[n][i]) for n in matrix)
                    for i in range(3)] for s in range(2)]
        gap = [.01, .02]
        target = [[laws[s]['ut'][0]-history[s][0], laws[s]['ut'][1]-history[s][1],
                   laws[s]['q']+gap[s]] for s in range(2)]
        b2 = {9: [.003, .005, .002]}
        corrected = [[target[s][i]-matrix[9][s]*b2[9][i] for i in range(3)] for s in range(2)]
        b2[7] = [(corrected[0][i]-.3*corrected[1][i])/.94 for i in range(3)]
        b2[8] = [(corrected[1][i]-.2*corrected[0][i])/.94 for i in range(3)]
        before, after = [], []

        def emit(target, kind, call_id=call_id, **fields):
            target.append({'kind': kind, 'call_id': call_id, **fields})

        emit(before, 'KIN_INVENTORY', all_node_count=9, physical_count=3, dd_count=4, bd_count=2, slave_count=2)
        for node in matrix:
            kind = 'KIN_BD' if node == 9 else 'KIN_DD'
            emit(before, 'KIN_NODE', node=node, dd_count=0 if node == 9 else 2,
                 bd_count=2 if node == 9 else 0, b2=b2[node], vold=vold[node], vini=vini[node])
            for slot in range(2):
                emit(before, kind, node=node, entry=(0 if node == 9 else (node-7)*2)+slot,
                     row_node=7+slot, slave_slot=slot, value=matrix[node][slot])
        for slot in range(2):
            emit(before, 'KIN_GAP', pair=0, slot=slot, node=7+slot, gap=gap[slot])
            post[slot]['gap'] = -laws[slot]['q']
        emit(after, 'CFS_INVENTORY', all_node_count=9, physical_count=3)
        for node in matrix:
            force = [sum(matrix[node][s]*post[s]['lambda_raw'][i] for s in range(2)) for i in range(3)]
            emit(after, 'CFS_NODE', node=node, force=force)
        emit(after, 'CFS_END', scanned_nodes=9, physical_count=3, outside_nonzero_count=0)
        for row in rows:
            if row['kind'] == 'SUMMARY_PRE_OVERRIDE':
                output.extend(after)
            output.append(row)
            if row['kind'] == 'BEGIN':
                output.extend(before)
    return output, sta


def test_nonsymmetric_coupling_history_forces_and_work():
    events, sta = coupled_fixture()
    result = replay(stream(events), sta)
    assert result['calls_checked'] == 10
    assert [c['call_id'] for c in result['accepted_coupling']] == [3, 5, 8, 10]
    for call in result['accepted_coupling']:
        assert call['physical_count'] == 3 and (call['dd_count'], call['bd_count']) == (4, 2)
        assert abs(call['virtual_work']['difference']) <= call['virtual_work']['roundoff_bound']
        nodes = call['physical_nodes']
        assert nodes[0]['internal_contact_force'] == pytest.approx([3.2, 5.6, 14.])
        assert nodes[2]['internal_contact_force'] == pytest.approx([-9.8, -14.8, -37.])
        assert nodes[2]['applied_contact_force'] == pytest.approx([9.8, 14.8, 37.])
        assert nodes[2]['endpoint_displacement'] == pytest.approx([.053, .065, .072])
    assert 'NOT VALIDATED' in result['status']


@pytest.mark.parametrize('kind', ['KIN_INVENTORY', 'KIN_NODE', 'KIN_DD', 'KIN_BD', 'KIN_GAP',
                                  'CFS_INVENTORY', 'CFS_NODE', 'CFS_END'])
@pytest.mark.parametrize('mutation', ['drop', 'duplicate', 'reorder'])
def test_coupling_coverage_corruption_rejected(kind, mutation):
    events, sta = coupled_fixture()
    index = next(i for i, r in enumerate(events) if r['kind'] == kind)
    if mutation == 'drop':
        events.pop(index)
    elif mutation == 'duplicate':
        events.insert(index, copy.deepcopy(events[index]))
    else:
        events[index], events[index+1] = events[index+1], events[index]
    with pytest.raises(ValueError):
        replay(stream(events), sta)


@pytest.mark.parametrize('kind,field,value', [
    ('KIN_NODE', 'b2', [0., 0., 0.]), ('KIN_NODE', 'vini', [0., 0., 0.]),
    ('KIN_NODE', 'vold', [0., 0., 0.]), ('KIN_GAP', 'gap', 5.),
    ('KIN_DD', 'value', 2.), ('KIN_BD', 'value', 2.), ('KIN_DD', 'row_node', 9),
    ('KIN_DD', 'slave_slot', 7), ('KIN_NODE', 'b2', [float('nan'), 0., 0.]),
    ('KIN_INVENTORY', 'physical_count', True), ('CFS_NODE', 'force', [0., 0., 0.]),
    ('CFS_END', 'outside_nonzero_count', 1), ('CFS_END', 'scanned_nodes', 8),
])
def test_changed_kinematics_mapping_or_force_rejected(kind, field, value):
    events, sta = coupled_fixture()
    next(r for r in events if r['kind'] == kind)[field] = value
    with pytest.raises(ValueError):
        replay(stream(events), sta)


def test_force_outside_declared_inventory_rejected():
    events, sta = coupled_fixture()
    index = next(i for i, r in enumerate(events) if r['kind'] == 'CFS_END')
    events.insert(index, {'kind': 'CFS_OUTSIDE', 'call_id': 1, 'node': 1, 'force': [0., 0., 1.]})
    with pytest.raises(ValueError):
        replay(stream(events), sta)
