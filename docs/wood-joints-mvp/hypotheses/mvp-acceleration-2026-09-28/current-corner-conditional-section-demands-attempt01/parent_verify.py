"""Independent point-force cut sums from native response, not the corner exporter."""
import hashlib,json,math
from pathlib import Path
HERE=Path(__file__).resolve().parent;BASE=HERE.parent;ROOT=HERE.parents[4]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def cross(a,b):return [a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0]]
sources={'a12-rear':('current-springa-selected-floor-a12-rear-attempt03','response.json'),'a1-rear':('current-springa-selected-floor-a1-rear-attempt02','response-zero-u-token.json'),'k12-rear':('current-k12-rear-spr489-direct-native-attempt01','response.json')}
pins={};models={};responses={}
for case,(directory,name) in sources.items():
 p=BASE/directory;models[case]=json.loads((p/'model.json').read_text());responses[case]=json.loads((p/name).read_text())
 for f in [p/'model.json',p/name]:pins[str(f.relative_to(ROOT))]=sha(f)
report=json.loads((HERE/'section-demands.json').read_text());checks=0;maximum_force_difference=0.;maximum_moment_difference=0.
for row in report['per_increment_body_sections']:
 case=row['case_id'];body=row['body'];model=models[case];state=next(s for s in responses[case]['increments'] if s['time']==row['time']);assert state['load_factor']==row['load_factor']
 actions=[]
 for connection in state['physical_connection_forces'].values():
  for side in ['first','second']:
   if connection[side]==body:actions.append((connection.get(side+'_point',connection['point']),connection['force_on_'+side+'_xyz_n']))
 for node,f in model['physical_body_loads'][body].items():actions.append((model['nodes'][node],[row['load_factor']*x for x in f]))
 for station in row['section_stations']:
  z=station['station_z_global_mm'];datum=station['cut_datum_global_xyz_mm']
  for side in ['just_below','just_above']:
   selected=[(p,f) for p,f in actions if (p[2]-z < -1e-6 if side=='just_below' else p[2]-z<=1e-6)]
   force=[-math.fsum(f[j] for p,f in selected) for j in range(3)]
   moments=[cross([p[j]-datum[j] for j in range(3)],f) for p,f in selected]
   moment=[-math.fsum(m[j] for m in moments) for j in range(3)]
   actual=station['one_sided_cut_results'][side]['lower_segment_material_action']
   fd=max(abs(force[j]-actual['force_xyz_n'][j]) for j in range(3));md=max(abs(moment[j]-actual['moment_xyz_nmm'][j]) for j in range(3))
   assert fd<=1e-9 and md<=1e-7,(case,body,z,side,fd,md)
   maximum_force_difference=max(maximum_force_difference,fd);maximum_moment_difference=max(maximum_moment_difference,md);checks+=1
assert checks==252 and len(report['per_increment_body_sections'])==42
for p in [HERE/'section-demands.json',HERE/'produce.py',Path(__file__)]:pins[str(p.relative_to(ROOT))]=sha(p)
result={'status':'PASS_PARENT_NATIVE_POINT_FORCE_SECTION_RECONSTRUCTION','body_state_count':42,'independent_one_sided_cut_count':checks,'maximum_force_difference_N':maximum_force_difference,'maximum_moment_difference_Nmm':maximum_moment_difference,'source_sha256':pins,'physics_scope':'Native physical point forces plus load-factor-scaled source discrete nodal loads; no exporter force arithmetic or serialized couples counted.','physical_mass_distribution_qualified':False,'joint_accepted':False}
(HERE/'parent-verification.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k not in ['source_sha256','physics_scope']}))
