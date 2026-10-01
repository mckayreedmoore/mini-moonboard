"""Independent selected-floor input and source-wrench audit; never executes."""
from pathlib import Path
import argparse,hashlib,importlib.util,json
import numpy as np
HERE=Path(__file__).resolve().parent
BASE=HERE.parent
OLD=BASE/'current-springa-frame-a12-rear-controls-attempt01'
HELPER=BASE/'current-springa-parent-input-audit-attempt01/check.py'
spec=importlib.util.spec_from_file_location('parent_deck_parser',HELPER);parser=importlib.util.module_from_spec(spec);spec.loader.exec_module(parser)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def run(directory,output_path=None):
 directory=Path(directory).resolve();old=json.loads((OLD/'model.json').read_text());new=json.loads((directory/'model.json').read_text())
 assert sha(OLD/'model.json')=='b89e69abd004bd788d3619f73270375bbd8d8a195edf29313a77baee3c1a8f1e'
 assert sha(OLD/'model.inp')=='bab4e4728e6a690dbff66d44cced93977a6125d5fd9fc21fe26d927d83785ca2'
 assert new['schema']=='current_springa_selected_floor_input_model/v1'
 for key in ['candidate','geometry_revision_id','physical_body_nodes','physical_body_elements','body_geometry','connection_ownership','physical_body_loads','physical_external_loads','springs','elements','loads','material_binding','nonlinear_native_carrier_bindings','unilateral_springa_bindings','numerical_spring_ground_nodes']:
  assert old[key]==new[key],('source field changed',key)
 oldcards=parser.cards((OLD/'model.inp').read_text());cards=parser.cards((directory/'model.inp').read_text())
 mutable={'NODE','BOUNDARY','EQUATION','CLOAD'}
 assert [(h,r) for h,r in oldcards if h[1:].split(',')[0].upper() not in mutable]==[(h,r) for h,r in cards if h[1:].split(',')[0].upper() not in mutable]
 nodes={};loads={};fixed=set()
 for h,rows in cards:
  if h.upper()=='*NODE':
   for row in rows:
    fields=row.split(',');n=int(fields[0]);assert n not in nodes;nodes[n]=np.array(list(map(float,fields[1:])))
  elif h.upper()=='*CLOAD':
   for row in rows:
    n,d,v=row.split(',');key=(int(n),int(d));loads[key]=loads.get(key,0)+float(v)
  elif h.upper()=='*BOUNDARY':
   for row in rows:
    n,a,b,*v=row.split(',');assert not v or float(v[0])==0
    fixed.update((int(n),d) for d in range(int(a),int(b)+1))
 declared={(int(n),d+1):v for n,f in old['physical_external_loads'].items() for d,v in enumerate(f)}
 assert not set(loads)-set(declared)
 load_error=max(abs(loads.get(k,0)-v) for k,v in declared.items());assert load_error<1e-8
 oldrefs={int(r['node']) for r in old['floor_reference_nodes_and_load_map']}
 preserved=set(map(int,old['nodes']))-oldrefs
 assert preserved<=set(nodes)
 node_error=max(abs(nodes[n][d]-old['nodes'][str(n)][d]) for n in preserved for d in range(3));assert node_error<1e-8
 eq=parser.equations((directory/'model.inp').read_text());assert not set(eq)&fixed
 assert len(eq)==len(new['equations'])
 fa=json.loads((BASE/'current-floor-stick-constraint-audit-attempt01/audit.json').read_text());mat=np.load(BASE/'current-floor-stick-constraint-audit-attempt01/constraint-matrices.npz');A=mat['original'];masters=[tuple(k) for k in fa['physical_master_dofs']];column={k:i for i,k in enumerate(masters)}
 screen=json.loads((BASE/'current-springa-selected-floor-branch-screen-attempt01/screen.json').read_text());proposed=set(screen['diagnostic_positive_cells_at_final_time'])
 refs=sorted(new['floor_reference_nodes_and_load_map'],key=lambda r:r['source_row_original_index']);indices=[int(r['source_row_original_index']) for r in refs]
 N=2*len(proposed);assert len(refs)==N and 0<len(proposed)<100
 assert {r['normal_cell'] for r in refs}==proposed
 expected=[int(r['source_row_original_index']) for r in old['floor_reference_nodes_and_load_map'] if r['normal_cell'] in proposed];assert indices==sorted(expected)
 baseline_refs={int(r['source_row_original_index']):r for r in old['floor_reference_nodes_and_load_map']}
 for r in refs:
  for key in ['normal_cell','physical_owner','owner_tangent_basis_global_xyz','owner_floorpoint_xyz_mm','source_row_id']:
   assert r[key]==baseline_refs[int(r['source_row_original_index'])][key]
 refcolumn={int(r['node']):i for i,r in enumerate(refs)};assert len(refcolumn)==N
 pivots=[k for k in eq if k in column];assert len(pivots)==N
 H=np.zeros((N,len(masters)));D=np.zeros((N,N))
 for i,k in enumerate(pivots):
  terms=eq[k];assert terms[0][2]==1
  for n,d,c in terms:
   if (n,d) in column:H[i,column[n,d]]+=c
   else:assert n in refcolumn and d==1;D[i,refcolumn[n]]-=c
 assert np.max(np.abs(H[:,[column[k] for k in pivots]]-np.eye(N)))<1e-12
 S=A[np.ix_(indices,[column[k] for k in pivots])]
 constraint_error=float(np.max(np.abs(S@H-A[indices])));reference_error=float(np.max(np.abs(S@D-np.eye(N))))
 assert constraint_error<1e-10 and reference_error<1e-10
 physical_map=H.T@np.linalg.inv(D.T);W=np.zeros((6,len(masters)))
 for j,(n,d) in enumerate(masters):
  unit=np.eye(3)[d-1];W[:3,j]=unit;W[3:,j]=np.cross(nodes[n],unit)
 expected_w=np.array([np.r_[r['owner_tangent_basis_global_xyz'],np.cross(r['owner_floorpoint_xyz_mm'],r['owner_tangent_basis_global_xyz'])] for r in refs]).T
 error=W@physical_map-expected_w;force_error=float(np.max(np.abs(error[:3])));moment_error=float(np.max(np.abs(error[3:])));assert force_error<1e-9 and moment_error<1e-6
 correction=D.T@np.array([loads.get(k,0) for k in pivots]);declared_correction=np.array([r['source_load_correction_N'] for r in refs]);correction_error=float(np.max(np.abs(correction-declared_correction)));assert correction_error<1e-8
 oldeq=parser.equations((OLD/'model.inp').read_text());oldfloor=set(masters)&set(oldeq)
 for k,terms in oldeq.items():
  if k not in oldfloor:assert eq.get(k)==terms,('changed non-floor equation',k)
 result={'status':'PASS_PARENT_SELECTED_FLOOR_SERIALIZED_INPUT_AUDIT','model_sha256':sha(directory/'model.json'),'deck_sha256':sha(directory/'model.inp'),'physical_body_count':50,'candidate_bolt_axes':92,'retained_leg_runner_axes':12,'hillman_axes':66,'selected_bearing_cells':len(proposed),'released_cells':100-len(proposed),'active_tangent_rows':N,'no_geometry_law_load_or_material_change':True,'source_load_serialization_error_N':load_error,'preserved_node_serialization_error_mm':node_error,'constraint_reconstruction_error':constraint_error,'reference_transfer_error':reference_error,'reference_unit_wrench_force_error':force_error,'reference_unit_wrench_moment_error_mm':moment_error,'source_load_correction_error_N':correction_error,'no_dependent_fixed_collision':True,'proposed_branch_accepted':False,'native_run_authorized':False,'corner_demands_usable':False}
 (Path(output_path) if output_path else HERE/'audit.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('input_directory');ap.add_argument('--output');args=ap.parse_args();run(args.input_directory,args.output)
