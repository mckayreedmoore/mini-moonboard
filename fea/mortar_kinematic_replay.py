"""Replay observed coupling kinematics and forces, not geometric segmentation."""
import json
import math

from fea.mortar_observer_replay import PREFIX, _object, require, same
from fea.mortar_observer_replay import SCHEMA as V1_SCHEMA
from fea.mortar_observer_replay import replay as replay_v1

SCHEMA = {
    'KIN_INVENTORY': 'all_node_count physical_count dd_count bd_count slave_count',
    'KIN_NODE': 'node dd_count bd_count b2 vold vini',
    'KIN_DD': 'node entry row_node slave_slot value',
    'KIN_BD': 'node entry row_node slave_slot value',
    'KIN_GAP': 'pair slot node gap',
    'CFS_INVENTORY': 'all_node_count physical_count',
    'CFS_NODE': 'node force',
    'CFS_OUTSIDE': 'node force',
    'CFS_END': 'scanned_nodes physical_count outside_nonzero_count',
}
ARRAYS = {'b2', 'vold', 'vini', 'force'}
SCALARS = {'value', 'gap'}


def parse_extra(row):
    require(set(row) == {'kind', 'call_id', *SCHEMA[row['kind']].split()}, 'Kinematic schema differs')
    for key, value in row.items():
        if key == 'kind':
            continue
        if key in ARRAYS:
            require(type(value) is list and len(value) == 3, 'Three physical components required')
            require(all(type(v) in (int, float) and math.isfinite(v) for v in value), 'Finite physical components required')
        elif key in SCALARS:
            require(type(value) in (int, float) and math.isfinite(value), 'Finite coupling scalar required')
        else:
            require(type(value) is int, 'Integer coupling identity/count required')
    return row


def check_call(rows):
    """Bound one complete packet to the same call's original pre/post records."""
    extra = [r for r in rows if r['kind'] in SCHEMA]
    cursor = 0

    def take(kind):
        nonlocal cursor
        require(cursor < len(extra) and extra[cursor]['kind'] == kind, 'Missing/reordered coupling record: '+kind)
        row = extra[cursor]
        cursor += 1
        return row

    kinds = [r['kind'] for r in rows]
    require(kinds[0] == 'BEGIN' and kinds[1] == 'KIN_INVENTORY', 'Kinematics must precede law snapshot')
    require(max(i for i, kind in enumerate(kinds) if kind.startswith('KIN_')) <
            kinds.index('INVENTORY'), 'Gap snapshot phase differs')
    require(max(i for i, kind in enumerate(kinds) if kind == 'POST_RAW_AFTER_ACTIVE_LOOP') <
            kinds.index('CFS_INVENTORY') and
            max(i for i, kind in enumerate(kinds) if kind.startswith('CFS_')) <
            kinds.index('SUMMARY_PRE_OVERRIDE'), 'Contact force phase differs')
    raw = {r['slot']: r for r in rows if r['kind'] == 'PRE_RAW'}
    laws = {r['slot']: r for r in rows if r['kind'] == 'LAW'}
    post = {r['slot']: r for r in rows if r['kind'] == 'POST_RAW_AFTER_ACTIVE_LOOP'}
    inventory = take('KIN_INVENTORY')
    require(inventory['all_node_count'] > 0 and 0 < inventory['physical_count'] <= inventory['all_node_count'] and
            inventory['slave_count'] == len(raw) > 0, 'Invalid kinematic inventory')
    physical, matrices = {}, {'KIN_DD': [], 'KIN_BD': []}
    for _ in range(inventory['physical_count']):
        node = take('KIN_NODE')
        require(0 < node['node'] <= inventory['all_node_count'] and
                (not physical or node['node'] > max(physical)) and
                min(node['dd_count'], node['bd_count']) >= 0 and node['dd_count']+node['bd_count'] > 0,
                'Invalid coupled physical node')
        physical[node['node']] = node
        for kind, count in (('KIN_DD', node['dd_count']), ('KIN_BD', node['bd_count'])):
            previous_entry = None
            for _ in range(count):
                entry = take(kind)
                require(entry['node'] == node['node'] and entry['slave_slot'] in raw and
                        entry['row_node'] == raw[entry['slave_slot']]['node'] and entry['entry'] >= 0 and
                        (previous_entry is None or entry['entry'] == previous_entry+1), 'Invalid coupling matrix entry')
                previous_entry = entry['entry']
                matrices[kind].append(entry)
    for kind, count in (('KIN_DD', 'dd_count'), ('KIN_BD', 'bd_count')):
        require(len(matrices[kind]) == inventory[count] and
                len({r['entry'] for r in matrices[kind]}) == len(matrices[kind]), 'Coupling entry inventory differs')
    gaps = {}
    for slot, node in raw.items():
        gap = take('KIN_GAP')
        require(all(gap[k] == node[k] for k in ('pair', 'slot', 'node')), 'Weighted gap identity differs')
        gaps[slot] = gap['gap']
    du, history = ({slot: [0., 0., 0.] for slot in raw} for _ in range(2))
    forces = {node: [0., 0., 0.] for node in physical}
    # Preserve each source loop's Dd-then-Bd accumulation order.
    for entries in matrices.values():
        for entry in entries:
            slot, node, weight = entry['slave_slot'], entry['node'], entry['value']
            for axis in range(3):
                p = physical[node]
                du[slot][axis] += weight*p['b2'][axis]
                history[slot][axis] += weight*(p['vold'][axis]-p['vini'][axis])
                forces[node][axis] += weight*post[slot]['lambda_raw'][axis]
    for slot, law in laws.items():
        normal_increment = sum(a*b for a, b in zip(du[slot], law['normal'], strict=True))
        same(law['q'], normal_increment-gaps[slot], 'independent weighted q')
        same(post[slot]['gap'], gaps[slot]-normal_increment, 'updated weighted gap')
        for axis in range(2):
            tangent = law['tangents'][3*axis:3*axis+3]
            expected = sum((du[slot][i]+history[slot][i])*tangent[i] for i in range(3))
            same(law['ut'][axis], expected, 'independent tangent history')
    cfs_inventory = take('CFS_INVENTORY')
    require(all(cfs_inventory[k] == inventory[k] for k in ('all_node_count', 'physical_count')), 'CFS inventory differs')
    for node in physical:
        row = take('CFS_NODE')
        require(row['node'] == node, 'Missing/reordered CFS node')
        for actual, expected in zip(row['force'], forces[node], strict=True):
            same(actual, expected, 'independent contact force')
    # Any CFS_OUTSIDE record is a hard coverage failure, not an ignored force.
    end = take('CFS_END')
    require(end == {'kind': 'CFS_END', 'call_id': rows[0]['call_id'],
                    'scanned_nodes': inventory['all_node_count'], 'physical_count': len(physical),
                    'outside_nonzero_count': 0} and cursor == len(extra), 'Incomplete/outside contact forces')
    primal = [physical[n]['b2'][i]*forces[n][i] for n in physical for i in range(3)]
    dual = [du[s][i]*post[s]['lambda_raw'][i] for s in raw for i in range(3)]
    left, right = math.fsum(primal), math.fsum(dual)
    scale = math.fsum(abs(x) for x in primal+dual)
    # Floating-point accumulation bound, not an engineering acceptance limit.
    bound = 32*math.ulp(1.)*(sum(map(len, matrices.values()))+len(primal)+len(dual))*scale
    require(all(math.isfinite(x) for x in (left, right, scale, bound)) and abs(left-right) <= bound,
            'Coupling virtual-work identity differs')
    return {'call_id': rows[0]['call_id'], 'physical_count': len(physical),
            'dd_count': len(matrices['KIN_DD']), 'bd_count': len(matrices['KIN_BD']),
            'virtual_work': {'physical': left, 'dual': right, 'difference': left-right, 'roundoff_bound': bound},
            'physical_nodes': [{'node': n, 'internal_contact_force': forces[n],
                                'applied_contact_force': [-x for x in forces[n]],
                                'endpoint_displacement': [p['vold'][i]+p['b2'][i] for i in range(3)]}
                               for n, p in physical.items()]}


def replay(text, sta_text):
    """Process additional packets per call; reuse the unchanged v1 acceptance audit."""
    v1_lines, current, coupled = [], [], []
    for line in text.splitlines():
        if PREFIX.strip() not in line:
            continue
        require(line.startswith(PREFIX), 'Malformed observer prefix')
        row = json.loads(line[len(PREFIX):], object_pairs_hook=_object)
        require(type(row) is dict and row.get('kind') in SCHEMA.keys() | V1_SCHEMA.keys(), 'Unknown observer kind')
        if row['kind'] in SCHEMA:
            parse_extra(row)
        else:
            v1_lines.append(line)
        require(row.get('call_id') == len(coupled)+1, 'Kinematic call identity differs')
        current.append(row)
        if row['kind'] == 'POST_CHECK':
            coupled.append(check_call(current))
            current = []
    require(not current and coupled, 'Incomplete/missing kinematic calls')
    original = replay_v1('\n'.join(v1_lines), sta_text)
    require(len(original['calls']) == len(coupled), 'Original/kinematic call coverage differs')
    accepted = set(original['accepted_call_ids'])
    return {'status': 'OBSERVED MATRIX KINEMATIC/FORCE REPLAY; GEOMETRIC SEGMENTATION AND PHYSICAL CAPACITY NOT VALIDATED',
            'limitations': 'Coupling matrices, initial weighted gap and frozen bases remain observed inputs. Applied forces are negative internal cfs. No cfm-side interpretation, guessed nodal area or joint-strength credit.',
            'original_replay': original, 'accepted_coupling': [c for c in coupled if c['call_id'] in accepted],
            'calls_checked': len(coupled)}
