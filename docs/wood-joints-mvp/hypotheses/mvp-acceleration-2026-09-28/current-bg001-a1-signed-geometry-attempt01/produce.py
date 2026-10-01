"""Apply recorded signed-distance method to A1 vectors; no new resistance basis."""
from pathlib import Path
import hashlib, json, math
HERE = Path(__file__).resolve().parent
BASE = HERE.parent
DISTANCE = BASE/'current-corner-bg001-signed-end-distance-attempt01/signed-end-distance-screen.json'
REFERENCE = BASE/'current-bg001-a1-resultant-reference-attempt01/screen.json'
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    assert sha(DISTANCE) == '04df4147f276e1b866b076ea428d5d16e31007219653e395990aa2083a2d239e'
    assert sha(REFERENCE) == 'bd5fc8d2fcc7167b4764ea7d2c60e0ef0a04c7a5343b4f573766bdfb161126fe'
    old=json.loads(DISTANCE.read_text()); current=json.loads(REFERENCE.read_text())
    for doc,mapping in [(old,old['input_provenance']['source_sha256']),(current,current['source_sha256'])]:
        for f,h in mapping.items(): assert sha(Path(f)) == h, f
    prior={r['axis_id']:r for r in old['signed_direction_results']}; rows=[]
    for r in current['rows']:
        members={}
        for member,v in r['force_on_members_xyz_N'].items():
            g=prior[r['axis_id']]['member_geometry'][member]
            assert v[2]*g['signed_grain_parallel_action_N'] > 0  # Same end, explicitly verified.
            theta=r['grain_angles_deg'][member]; full=7-3*theta/90; distance=g['loaded_end_distance_D']
            assert distance >= full/2, 'Below recorded minimum geometry branch'
            factor=min(1.,distance/full)
            same_edge=v[1]*g['signed_cross_grain_action_N'] > 0
            loaded=g['loaded_edge_distance_D'] if same_edge else g['unloaded_edge_distance_D']
            unloaded=g['unloaded_edge_distance_D'] if same_edge else g['loaded_edge_distance_D']
            members[member]={'force_xyz_N':v,'grain_angle_deg':theta,'loaded_end':g['loaded_grain_end'],
                'loaded_end_distance_D':distance,'full_factor_end_requirement_D':full,
                'conditional_Cdelta':factor,'same_loaded_edge_as_A12':same_edge,
                'loaded_edge_distance_D':loaded,'unloaded_edge_distance_D':unloaded,
                'listed_edge_minima_met':loaded>=4 and unloaded>=1.5}
        rows.append({'axis_id':r['axis_id'],'members':members,'lateral_demand_N':r['lateral_resultant_N'],
                     'raw_reference_N':r['unadjusted_reference_N']})
    group=min(g['conditional_Cdelta'] for r in rows for g in r['members'].values())
    for r in rows:
        r['geometry_scaled_reference_N']=group*r['raw_reference_N']
        r['demand_over_geometry_scaled_reference']=r['lateral_demand_N']/r['geometry_scaled_reference_N']
    force=[math.fsum(r['members']['base_post_outer_left']['force_xyz_N'][i] for r in rows) for i in range(3)]
    sine=math.hypot(force[0],force[1])/math.sqrt(sum(v*v for v in force))
    out={'schema':'current_bg001_a1_signed_geometry/v1','case_id':'a1-rear','rows':rows,
         'group_conditional_Cdelta':group,'summed_post_lateral_force_xyz_N':force,'group_row_alignment_sine':sine,
         'Cg_for_actual_mixed_direction':None,'method_authority':old['method']['NDS_source'],
         'source_sha256':{str(p):sha(p) for p in [DISTANCE,REFERENCE,Path(__file__)]},
         'status':'CONDITIONAL_SIGNED_GEOMETRY_COMPONENT_ONLY','joint_accepted':False,
         'limits':['Recorded Commentary interpolation interpretation reused; no new primary Commentary qualification.',
                   'Sampled CAD distances and proposed grain are not inspected stock or continuous-profile minima.',
                   'Cg and mixed-action splitting remain unresolved; geometry-scaled references omit remaining adjustments and interactions.']}
    (HERE/'screen.json').write_text(json.dumps(out,indent=2)+'\n')
    print(json.dumps({'Cdelta':group,'component_comparisons':[r['demand_over_geometry_scaled_reference'] for r in rows],'group_alignment_sine':sine}))
if __name__=='__main__': main()
