"""Bind the complete corner demand inventory to reviewed INPUT ownership only."""
import hashlib
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent
SOURCE=HERE.parent/'reduced-static-a12-rear-ratio1-gap0-attempt02/cycle-11-sign-closure-r1/model.json'
PIN='d3417111926c982a07ced393aa1c12f815aa87b5b8eb851b45bc63a1ea10fac0'
BODIES={'base_post_outer_left','knee_outer_left_spine','base_side_left',
        'knee_outer_left_inner_frame_block','base_header'}
GROUPS={'BG001':['knee_outer_left_post_1','knee_outer_left_post_2'],
        'BG003':['knee_outer_left_side_1','knee_outer_left_side_2'],
        'BG045':['knee_outer_left_inner_header_1','knee_outer_left_inner_header_2']}
raw=SOURCE.read_bytes()
assert hashlib.sha256(raw).hexdigest()==PIN
model=json.loads(raw)
owners=model['connection_ownership']
assert BODIES <= set(model['physical_body_nodes'])
retained={r['axis_id'] for r in owners.values() if r['role']=='retained_bolt_lateral_plane'}
new={r['axis_id'] for r in owners.values() if r['role']=='candidate_bolt_lateral_plane'}
assert len(retained)==12 and len(new)==92 and not retained & new
corner_axes=set(sum(GROUPS.values(),[]))
assert corner_axes <= new and not corner_axes & retained
inventory=[]
for name,owner in sorted(owners.items()):
    endpoints={owner['first'],owner['second']}
    if not endpoints & BODIES:
        continue
    relation='internal_corner_transfer' if endpoints <= BODIES else 'onward_or_incoming_boundary_transfer'
    inventory.append({'source_connection_name':name,'relation':relation,
                      'owner':owner,'physical_action_required_on':sorted(endpoints & BODIES)})
counts={}
for row in inventory:
    role=row['owner']['role']
    counts[role]=counts.get(role,0)+1
primary={}
for group,axes in GROUPS.items():
    rows=[r for r in inventory if r['owner'].get('axis_id') in axes]
    lateral=[r for r in rows if r['owner']['role']=='candidate_bolt_lateral_plane']
    ties=[r for r in rows if r['owner']['role']=='physical_bolt_outer_seat_tension']
    assert len(lateral)==(4 if group=='BG003' else 2) and len(ties)==2
    primary[group]={'axis_ids':axes,'lateral_plane_count':len(lateral),'outer_seat_tie_count':len(ties),
                    'source_connection_names':[r['source_connection_name'] for r in rows]}
output={'schema':'current_complete_corner_demand_contract/v1',
        'candidate':model['candidate'],'geometry_revision_id':model['geometry_revision_id'],
        'source_input_sha256':PIN,'source_response_used':False,
        'corner_body_names':sorted(BODIES),'primary_new_corner_groups':primary,
        'new_block_axis_count':92,'retained_original_leg_runner_axis_count':12,
        'retained_original_axis_ids':sorted(retained),'interface_counts_by_role':counts,
        'interface_inventory':inventory,
        'required_demand_results':['Signed vector action on both physical sides of every interface at recorded source points',
          'Signed six-component cut/member and group wrenches at explicitly recorded datums',
          'Concurrent eight lateral-plane and six outer-seat actions for BG001/BG003/BG045',
          'Contact normal forces, pressures/areas and compatible unilateral states; all relevant parallel paths',
          'Every five-member external load plus all incoming/onward transfers, closing each member force/moment balance',
          'Six authenticated source cases, declared stiffness/engagement/material/accessory assumptions and sensitivity limits'],
        'datum_rule':'Moment at datum O equals sum((source_point-O) cross physical_force); preserve separate outer-seat points',
        'acceptance_rules':['Do not sum the two BG003 plane capacities as independent physical bolts',
           'Do not assign an entire corner wrench to one group when parallel contact/runner transfer exists',
           'Never include numerical spring grounds as real supports',
           'Original leg/runner demand changes do not restart unchanged resistance calculations',
           'No accepted historical response or case pass is transferred'],
        'actual_case_demands_available':False,'complete_joint_validated':False}
(HERE/'contract.json').write_text(json.dumps(output,indent=2)+'\n')
print(json.dumps({'primary_groups':primary,'counts':counts,'inventory_size':len(inventory)}))
