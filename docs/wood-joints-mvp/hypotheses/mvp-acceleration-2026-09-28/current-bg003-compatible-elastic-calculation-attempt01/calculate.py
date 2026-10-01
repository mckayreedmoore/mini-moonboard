"""Bounded linear Euler beam/Winkler compatibility calculation, not a capacity."""
import argparse,hashlib,json,math,sys
from pathlib import Path
import numpy as np
HERE=Path(__file__).resolve().parent;BASE=HERE.parent;ROOT=HERE.parents[4]
MEMBERS=['knee_outer_left_spine','base_side_left','knee_outer_left_inner_frame_block']
LENGTHS=[38.1,88.9,88.9];XSTART=-1257.3;DIAMETER=6.35;STEEL_E=190000.;I=math.pi*DIAMETER**4/64
CASES={'a12-rear':'current-corner-native-demand-export-attempt03','a1-rear':'current-corner-a1-rear-case-bound-export-attempt01','k12-rear':'current-corner-k12-rear-case-bound-export-attempt01'}
PINS={'a12-rear':'812a62fa3cd96a8983649c84a8c78a8d176d639465c887b11d1827a3f8f1ee17','a1-rear':'2b498383b319aeb31e74c3b329e0758330b8b39d0a8e1b4788437db06453bfce','k12-rear':'a78ca15d9d888dbddf6963be34a2f5e57159b0df77ef6b754cf631dbba8c10d0'}
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def shape(t,h):return np.array([1-3*t*t+2*t**3,h*(t-2*t*t+t**3),3*t*t-2*t**3,h*(-t*t+t**3)])
def beam_stiffness(h,ei):
 return ei/h**3*np.array([[12,6*h,-12,6*h],[6*h,4*h*h,-6*h,2*h*h],[-12,-6*h,12,-6*h],[6*h,2*h*h,-6*h,4*h*h]])
def assemble(n,k,ei=STEEL_E*I):
 ends=np.cumsum([0.]+LENGTHS);x=np.concatenate([np.linspace(ends[i],ends[i+1],n+1)[:-1] for i in range(3)]+[ends[-1:]])
 wood_offset=2*len(x);K=np.zeros((wood_offset+6,wood_offset+6));elements=[];g,w=np.polynomial.legendre.leggauss(4)
 for e in range(len(x)-1):
  member=e//n;h=x[e+1]-x[e];mid=(ends[member]+ends[member+1])/2;idx=[2*e,2*e+1,2*e+2,2*e+3,wood_offset+2*member,wood_offset+2*member+1]
  local=np.zeros((6,6));local[:4,:4]=beam_stiffness(h,ei)
  for a,b in zip(g,w):
   t=(a+1)/2;xx=x[e]+t*h;B=np.concatenate((shape(t,h),[-1.,-(xx-mid)]));local+=k[member]*h*b/2*np.outer(B,B)
  K[np.ix_(idx,idx)]+=local;elements.append((e,member,h,mid,idx))
 return x,K,elements,wood_offset

def solve(K,rhs,fixed):
 free=[j for j in range(len(rhs)) if j not in fixed];u=np.zeros(len(rhs));u[free]=np.linalg.solve(K[np.ix_(free,free)],rhs[free]);res=K@u-rhs
 assert np.max(np.abs(res[free]))<1e-5,np.max(np.abs(res[free]))
 return u,res

def fixtures():
 h=100.;ei=STEEL_E*I;K=beam_stiffness(h,ei);rhs=np.array([0.,0.,100.,0.]);u,r=solve(K,rhs,{0,1});expected=[100*h**3/(3*ei),100*h*h/(2*ei)]
 assert np.allclose(u[2:],expected,rtol=1e-12,atol=1e-12)
 cantilever_computed=u[2:].tolist()
 x,K,els,offset=assemble(4,[1000.]*3);g,w=np.polynomial.legendre.leggauss(4);records=[]
 for P in [100.,-100.]:
  rhs=np.zeros(len(K));p=P/x[-1]
  for e,member,h,mid,idx in els:
   for a,b in zip(g,w):rhs[idx[:4]]+=h*b/2*p*shape((a+1)/2,h)
  u,res=solve(K,rhs,set(range(offset,len(K))));target=P/(1000*x[-1]);error=max(abs(u[j]-target) for j in range(0,offset,2));rot=max(abs(u[j]) for j in range(1,offset,2))
  assert error<1e-10 and rot<1e-10
  records.append({'P_N':P,'expected_uniform_displacement_mm':target,'maximum_displacement_error_mm':error,'maximum_rotation_rad':rot})
 return {'cantilever_tip_displacement_rotation_computed':cantilever_computed,'cantilever_formula':'PL^3/(3EI), PL^2/(2EI)','uniform_fixed_foundation_free_beam':records,'status':'PASS_ANALYTICAL_KNOWN_ANSWERS'}

def external_loads(bolt,component):
 result={m:[0.,0.] for m in MEMBERS};ends=np.cumsum([0.]+LENGTHS)
 for action in bolt['actions']:
  if action['role']!='candidate_bolt_lateral_plane':continue
  for side in ['first','second']:
   m=action[side];i=MEMBERS.index(m);mid=(ends[i]+ends[i+1])/2;x=action[side+'_point_global_xyz_mm'][0]-XSTART;f=action['force_on_'+side+'_xyz_n'][component];result[m][0]-=f;result[m][1]-=(x-mid)*f
 total=sum(result[m][0] for m in MEMBERS);moment=sum(result[m][1]+result[m][0]*(sum(LENGTHS[:i])+LENGTHS[i]/2) for i,m in enumerate(MEMBERS))
 assert abs(total)<1e-9 and abs(moment)<1e-7,(total,moment)
 return result

def run_plane(bolt,component,n,k):
 x,K,els,offset=assemble(n,k);rhs=np.zeros(len(K));external=external_loads(bolt,component)
 for i,m in enumerate(MEMBERS):rhs[offset+2*i:offset+2*i+2]=external[m]
 u,res=solve(K,rhs,{0,1});assert max(abs(res[:2]))<1e-5,('nonzero gauge reaction',res[:2])
 g,w=np.polynomial.legendre.leggauss(4);bearing=np.zeros((3,2));samples=[];cumF=0.;cumX=0.;maxq=0.
 for e,member,h,mid,idx in els:
  def integrate(tmax):
   F=0.;X=0.;qs=[]
   for a,b in zip(g,w):
    t=tmax*(a+1)/2;xx=x[e]+t*h;beam=shape(t,h)@u[idx[:4]];wood=u[offset+2*member]+(xx-mid)*u[offset+2*member+1];q=k[member]*(beam-wood);ds=h*tmax*b/2;F+=q*ds;X+=xx*q*ds;qs.append(q)
   return F,X,qs
  for t in np.linspace(0.,1.,9):
   F,X,qs=integrate(t);xx=x[e]+t*h;samples.append({'x_mm':float(xx),'V_on_bolt_N':float(-(cumF+F)),'M_on_bolt_Nmm':float(-(xx*(cumF+F)-(cumX+X)))});maxq=max(maxq,*map(abs,qs))
  F,X,qs=integrate(1.);bearing[member]+=[F,X-mid*F];cumF+=F;cumX+=X
 mismatch=max(np.max(np.abs(bearing[i]+np.array(external[m]))) for i,m in enumerate(MEMBERS));assert mismatch<1e-5,mismatch
 assert abs(cumF)<1e-6 and abs(x[-1]*cumF-cumX)<1e-5
 return {'component_global_xyz':component,'elements_per_receiver':n,'foundation_k_N_per_mm2':k,'external_member_force_moment_about_interval_midpoint':external,'compatible_receiver_translation_mm_rotation_rad':{m:u[offset+2*i:offset+2*i+2].tolist() for i,m in enumerate(MEMBERS)},'foundation_wrench_on_wood_N_Nmm':{m:bearing[i].tolist() for i,m in enumerate(MEMBERS)},'maximum_wrench_residual_N_or_Nmm':float(mismatch),'gauge_reaction_N_Nmm':res[:2].tolist(),'maximum_sampled_line_bearing_N_per_mm':float(maxq),'sampled_internal_bolt_diagram':samples,'terminal_internal_V_N':float(-cumF),'terminal_internal_M_Nmm':float(-(x[-1]*cumF-cumX))}

def produce():
 answer={'schema':'current_bg003_compatible_elastic_calculation/v1','status':'PASS_BOUNDED_COMPATIBLE_ELASTIC_PROXY_ONLY','fixture':fixtures(),'diameter_mm':DIAMETER,'steel_E_MPa':STEEL_E,'I_mm4':I,'claim_boundary':'Per-bolt linear zero-clearance rigid-receiver Winkler proxy only. Diagnostic uniform foundation k values are NOT sourced timber properties or physical bounds. Biaxial independent directions omit contact coupling, bolt axial geometric stiffness, shared timber/group compatibility, timber elasticity, clearance, yield and brittle failure. No capacity or acceptance.','runtime':{'python':sys.version,'numpy':np.__version__,'openblas_thread_limit':'1'},'source_sha256':{},'results':[],'joint_accepted':False,'physical_stiffness_bounds_justified':False,'native_solver_launched':False}
 for case,directory in CASES.items():
  p=BASE/directory/'corner-demand-report.json';assert sha(p)==PINS[case];report=json.loads(p.read_text());assert report['actual_case_demand_usable_for_conditional_joint_checks'];answer['source_sha256'][str(p.relative_to(ROOT))]=sha(p)
  state=report['increments'][-1];assert state['load_factor']==1. and state['all_five_corner_bodies_raw_and_interval_balance_passed']
  for bolt in state['primary_physical_bolt_groups']['BG003']['bolts']:
   for kvalue in [100.,1000.,10000.]:
    meshes=[]
    for n in [4,8,16]:
     planes=[run_plane(bolt,c,n,[kvalue]*3) for c in [1,2]];assert len(planes[0]['sampled_internal_bolt_diagram'])==len(planes[1]['sampled_internal_bolt_diagram']);rows=list(zip(*(v['sampled_internal_bolt_diagram'] for v in planes)))
     M=max(math.hypot(a['M_on_bolt_Nmm'],b['M_on_bolt_Nmm']) for a,b in rows);V=max(math.hypot(a['V_on_bolt_N'],b['V_on_bolt_N']) for a,b in rows)
     meshes.append({'elements_per_receiver':n,'maximum_sampled_resultant_bending_Nmm':M,'maximum_sampled_resultant_shear_N':V,'planes':planes})
    change=abs(meshes[-1]['maximum_sampled_resultant_bending_Nmm']-meshes[-2]['maximum_sampled_resultant_bending_Nmm'])/max(meshes[-1]['maximum_sampled_resultant_bending_Nmm'],1e-10)
    assert change<.01,('mesh not converged',case,bolt['axis_id'],kvalue,change)
    answer['results'].append({'case_id':case,'axis_id':bolt['axis_id'],'load_factor':1.,'diagnostic_foundation_k_N_per_mm2':kvalue,'meshes':meshes,'last_mesh_relative_bending_change':change})
 answer['source_sha256'][str(Path(__file__).relative_to(ROOT))]=sha(Path(__file__));return answer
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--verify',action='store_true');a=p.parse_args();data=produce();target=HERE/'calculation.json'
 if a.verify:assert json.loads(target.read_text())==data;print('Verified bounded compatible elastic calculation')
 else:target.write_text(json.dumps(data,indent=2,allow_nan=False)+'\n');print('Wrote',len(data['results']),'case/bolt/parameter combinations')
