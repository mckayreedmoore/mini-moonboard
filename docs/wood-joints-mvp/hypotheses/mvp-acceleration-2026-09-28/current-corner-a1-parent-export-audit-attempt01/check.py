"""Independent exact-vector and complete-inventory check of the corner export."""
from pathlib import Path
import hashlib,json,math
HERE=Path(__file__).resolve().parent;B=HERE.parent
REPORT=B/'current-corner-a1-rear-case-bound-export-attempt01/corner-demand-report.json'
RESPONSE=B/'current-springa-selected-floor-a1-rear-attempt02/response-zero-u-token.json'
CONTRACT=B/'current-corner-demand-contract-attempt01/contract.json'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
c=json.loads(REPORT.read_text());r=json.loads(RESPONSE.read_text());ct=json.loads(CONTRACT.read_text())
assert c['status']=='PASS_NUMERICAL_CORNER_DEMAND_REPORT_ONLY'
expected={x['source_connection_name']:x for x in ct['interface_inventory']};counts=[]
for out,raw in zip(c['increments'],r['increments'],strict=True):
 assert out['load_factor']==raw['load_factor'] and out['all_five_corner_bodies_raw_and_interval_balance_passed']
 rows={x['source_connection_name']:x for x in out['all_corner_interfaces']};assert set(rows)==set(expected) and len(rows)==338
 zeros={x['source_row_id']:x for x in raw['inactive_floor_tangent_zero_actions']}
 tangents={x['source_row_id']:x for x in raw['exact_floor_tangent_reactions']};matched=zero=active=0
 for name,x in rows.items():
  if name in raw['physical_connection_forces']:
   q=raw['physical_connection_forces'][name]
   for key in ['first','second','force_on_first_xyz_n','force_on_second_xyz_n','force_rounding_radius_xyz_n']:assert x[key]==q[key],(name,key)
   matched+=1
  else:
   assert x['role']==expected[name]['owner']['role']=='assumed_no_slip_floor'
   assert len(x['source_row_ids'])==2
   if x['floor_tangent_state']=='released_inactive_floor_tangent_zero_action':
    assert x['force_on_first_xyz_n']==x['force_on_second_xyz_n']==[0.,0.,0.]
    assert all(k in zeros for k in x['source_row_ids'])
    zero+=1
   else:
    assert x['floor_tangent_state']=='active_selected_floor_tangent_reaction'
    channels=[tangents[k] for k in x['source_row_ids']]
    assert all(q['first']==x['first'] and q['second']==x['second'] for q in channels)
    for key in ['force_on_first_xyz_n','force_on_second_xyz_n','force_rounding_radius_xyz_n']:
     vector=[math.fsum(q[key][j] for q in channels) for j in range(3)]
     assert all(math.isclose(v,w,rel_tol=1e-14,abs_tol=1e-14) for v,w in zip(vector,x[key])),(name,key)
    active+=1
 assert matched+zero+active==338
 groups=out['primary_physical_bolt_groups'];assert set(groups)=={'BG001','BG003','BG045'}
 assert sum(g['physical_bolt_count'] for g in groups.values())==6
 assert sum(g['lateral_plane_count'] for g in groups.values())==8
 assert sum(g['outer_seat_tie_count'] for g in groups.values())==6
 for g,v in groups.items():
  assert v['axis_ids']==ct['primary_new_corner_groups'][g]['axis_ids']
  for bolt in v['bolts']:
   for action in bolt['actions']:
    q=raw['physical_connection_forces'][action['source_connection_name']]
    for key in ['first','second','force_on_first_xyz_n','force_on_second_xyz_n']:assert action[key]==q[key]
 assert out['retained_original_arrangement_count']==12 and out['retained_resistance_reopened'] is False
 counts.append({'load_factor':out['load_factor'],'exact_native_group_vectors':matched,'released_zero_groups':zero,'active_corrected_floor_groups':active,'complete_owned_interfaces':338})
result={'status':'PASS_PARENT_CORNER_INVENTORY_AND_EXACT_SIGNED_FORCE_AUDIT','report_sha256':sha(REPORT),'response_sha256':sha(RESPONSE),'contract_sha256':sha(CONTRACT),'increments':counts,'joint_accepted':False}
(HERE/'audit.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'status':result['status'],'increment_count':len(counts)}))
