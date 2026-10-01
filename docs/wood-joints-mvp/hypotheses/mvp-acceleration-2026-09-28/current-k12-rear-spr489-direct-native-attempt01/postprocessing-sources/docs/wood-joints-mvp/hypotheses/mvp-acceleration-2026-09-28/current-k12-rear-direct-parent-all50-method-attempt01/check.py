"""Independent force/moment sums at every physical body; no solver launch."""
import argparse,hashlib,json,math
from pathlib import Path
HERE=Path(__file__).resolve().parent

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def cross(a,b):return [a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0]]
def balance(entries,reference):
 forces=[[] for _ in range(3)];moments=[[] for _ in range(3)];fr=[[] for _ in range(3)];mr=[[] for _ in range(3)]
 for point,force,radius in entries:
  arm=[point[j]-reference[j] for j in range(3)];moment=cross(arm,force);x,y,z=map(abs,arm);mrad=[z*radius[1]+y*radius[2],z*radius[0]+x*radius[2],y*radius[0]+x*radius[1]]
  for j in range(3):forces[j].append(force[j]);moments[j].append(moment[j]);fr[j].append(radius[j]);mr[j].append(mrad[j])
 f=list(map(math.fsum,forces));m=list(map(math.fsum,moments));rf=list(map(math.fsum,fr));rm=list(map(math.fsum,mr));fd=[max(0,abs(f[j])-rf[j]) for j in range(3)];md=[max(0,abs(m[j])-rm[j]) for j in range(3)]
 return {'reference_xyz_mm':reference,'force_residual_xyz_n':f,'moment_residual_xyz_nmm':m,'force_rounding_radius_xyz_n':rf,'moment_rounding_radius_xyz_nmm':rm,'force_interval_distance_from_zero_n':fd,'moment_interval_distance_from_zero_nmm':md,'printed_resultants_passed':max(map(abs,f))<=.1 and max(map(abs,m))<=2.,'interval_resultants_passed':max(fd)<=.1 and max(md)<=2.}
def _safe_output_path(output_path,model_path,response_path):
 output_path=Path(output_path).expanduser().resolve();model_path=Path(model_path).resolve();response_path=Path(response_path).resolve()
 pinned_parent_dir=(HERE.parent/'current-springa-selected-floor-parent-response-audit-attempt01').resolve()
 if output_path in (model_path,response_path) or any(parent in output_path.parents for parent in (model_path.parent,response_path.parent,pinned_parent_dir)):
  raise ValueError(f'refusing to write parent all-body audit into a pinned input/source directory: {output_path}')
 return output_path
def run(model_path,response_path,output_path=HERE/'audit.json'):
 model_path=Path(model_path).resolve();response_path=Path(response_path).resolve();model=json.loads(model_path.read_text());response=json.loads(response_path.read_text());directory=model_path.parent
 output_path=_safe_output_path(output_path,model_path,response_path)
 assert model['schema']=='current_springa_selected_floor_input_model/v1'
 assert response['schema']=='current_k12_rear_spr489_direct_master_physical_response_audit/v1'
 assert response['status']=='PASS_K12_REAR_SPR489_DIRECT_MASTER_RESPONSE_AUDIT_ONLY'
 assert response['source_input_model_json_sha256']==sha(model_path)
 assert response['source_input_deck_sha256']==sha(directory/'model.inp') and response['native_data_sha256']==sha(directory/'model.dat')
 execution=json.loads((directory/'execution.json').read_text());assert execution['returncode']==0 and execution['container_confirmed_terminal']
 assert abs(response['increments'][-1]['load_factor']-1)<1e-12
 bodies=model['physical_body_nodes'];assert len(bodies)==50
 datums={body:[math.fsum(model['nodes'][str(n)][j] for n in tags)/len(tags) for j in range(3)] for body,tags in bodies.items()}
 reports=[]
 for increment in response['increments']:
  scale=increment['load_factor'];entries={b:[] for b in bodies};global_entries=[];loaded=set()
  for body,loads in model['physical_body_loads'].items():
   for node,value in loads.items():
    n=int(node);assert n not in loaded and n in bodies[body];loaded.add(n)
    row=(model['nodes'][str(n)],[scale*v for v in value],[0.,0.,0.]);entries[body].append(row);global_entries.append(row)
  for row in list(increment['physical_connection_forces'].values())+increment['exact_floor_tangent_reactions']:
   first,second=row['first'],row['second'];assert first in bodies or first=='floor';assert second in bodies or second=='floor'
   a=row['force_on_first_xyz_n'];b=row['force_on_second_xyz_n'];radius=row['force_rounding_radius_xyz_n'];assert max(abs(a[j]+b[j]) for j in range(3))<1e-10
   assert all(v>=0 and math.isfinite(v) for v in radius)
   for owner,point,force in [(first,row.get('first_point',row['point']),a),(second,row.get('second_point',row['point']),b)]:
    if owner=='floor':continue
    entry=(point,force,radius);entries[owner].append(entry);global_entries.append(entry)
  result={b:balance(values,datums[b]) for b,values in entries.items()};global_result=balance(global_entries,[0.,0.,0.])
  passed=all(v['printed_resultants_passed'] and v['interval_resultants_passed'] for v in list(result.values())+[global_result])
  reports.append({'time':increment['time'],'load_factor':scale,'body_count':50,'body_equilibrium':result,'global_equilibrium':global_result,'passed':passed,'numerical_grounds_counted':0})
 passed=all(r['passed'] for r in reports)
 result={'status':'PASS_PARENT_ALL_BODY_RESPONSE_SUMS' if passed else 'FAIL_PARENT_ALL_BODY_RESPONSE_SUMS','source_model_sha256':sha(model_path),'source_response_sha256':sha(response_path),'increments':reports,'physical_tolerances_N_Nmm':[.1,2.],'joint_accepted':False,'qualification_limit':'Independent physical resultant sums only; source-law and floor compatibility must also pass their audited gates. No material or connection resistance is qualified here.'}
 output_path.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'status':result['status'],'increment_count':len(reports),'body_count':50,'output_path':str(output_path)}))
if __name__=='__main__':
 parser=argparse.ArgumentParser();parser.add_argument('model');parser.add_argument('response');parser.add_argument('--output',type=Path,default=HERE/'audit.json');args=parser.parse_args();run(args.model,args.response,args.output)
