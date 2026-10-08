"""Preserved independent annular numerical review, from successful inline checks.

Run from the repository root; prints observations and writes no files.
This is a pure coupon check, not a candidate, native or K solve.
"""

import json, math, runpy, hashlib
from pathlib import Path
from decimal import Decimal as D, localcontext
from fractions import Fraction
import numpy as np

P=Path('fea/generated/thin-bolted-v4-geometry/annular-seat-response-v2')
mod=runpy.run_path(str(P/'outer_cap_dispatch_final.py'))
report=json.loads((P/'dispatch-result-final.json').read_bytes())
before={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in [P/'outer_cap_dispatch_final.py',P/'dispatch-input.json',P/'dispatch-result-final.json']}
PI=D('3.141592653589793238462643383279502884197169399375105820974944592307816406286208998628034825342117067982148086513282306647093844609550582231725359408')
with localcontext() as ctx:
 ctx.prec=120
 nodes=[]
 n=96
 for i in range(1,n+1):
  x=D.from_float(math.cos(math.pi*(i-.25)/(n+.5)))
  for _ in range(20):
   p0,p1=D(1),x
   for j in range(2,n+1): p0,p1=p1,((2*j-1)*x*p1-(j-1)*p0)/j
   derivative=n*(x*p1-p0)/(x*x-1)
   dx=p1/derivative
   x-=dx
   if abs(dx)<D('1e-112'): break
  else: raise ArithmeticError('independent96 root convergence')
  # mapped [-1,1] -> [0,1]
  nodes.append(((x+1)/2,1/((1-x*x)*derivative*derivative)))

def disk_positive(r,c):
 # Integrate radial polynomials over theta, using rational tan(theta/2).
 # Return [E/(k*t^2), N/(k*t), G/(k*t), A,Q,Jx,Jy].
 if c>=r: return [D(0)]*7
 assert 0<c<r
 u0=((r-c)/(r+c)).sqrt()
 sums=[D(0)]*7
 for v,w in nodes:
  u=u0*v; ct=(1-u*u)/(1+u*u); st=2*u/(1+u*u)
  r0=c/ct; d=r-r0
  assert d>=0
  angular=4*u0/(1+u*u)*w
  E=ct*ct*(r0*d**3/3+d**4/4)/2
  N=ct*(r0*d*d/2+d**3/3)
  G=ct*ct*(r0*r0*d*d/2+2*r0*d**3/3+d**4/4)
  A=r0*d+d*d/2
  Q=ct*(r0*r0*d+r0*d*d+d**3/3)
  radial4=r0**3*d+D('1.5')*r0*r0*d*d+r0*d**3+d**4/4
  vals=[E,N,G,A,Q,ct*ct*radial4,st*st*radial4]
  sums=[s+angular*z for s,z in zip(sums,vals,strict=True)]
 return sums

def disk(r,c):
 full=[PI*r*r,D(0),PI*r**4/4,PI*r**4/4]
 if c>=r:return [D(0)]*4
 if c<=-r:return full
 if c==0:return [full[0]/2,2*r**3/3,full[2]/2,full[3]/2]
 if c>0:return disk_positive(r,c)[3:]
 cap=disk_positive(r,-c)[3:]
 return [full[0]-cap[0],cap[1],full[2]-cap[2],full[3]-cap[3]]

def oracle(q):
 with localcontext() as ctx:
  ctx.prec=120
  a,b,k=map(D.from_float,[7.14375,17.526,1.])
  delta,sx,sy=map(D.from_float,q)
  t=(sx*sx+sy*sy).sqrt()
  if t==0:
   A=PI*(b*b-a*a) if delta>0 else D(0)
   J=PI*(b**4-a**4)/4 if delta>0 else D(0)
   return [k*delta*delta*A/2,k*delta*A,D(0),D(0),k*A,D(0),D(0),k*J,D(0),k*J]
  c=-delta/t
  outer=disk(b,c);inner=disk(a,c)
  A,Q,JX,JY=[x-y for x,y in zip(outer,inner,strict=True)]
  if 0<c<b:
   bp=disk_positive(b,c);ap=disk_positive(a,c) if c<a else [D(0)]*7
   E,N,G=[x-y for x,y in zip(bp[:3],ap[:3],strict=True)]
   E*=k*t*t;N*=k*t;G*=k*t
  else:
   E=k*t*t*(JX-2*c*Q+c*c*A)/2
   N=k*t*(Q-c*A);G=k*t*(JX-c*Q)
  ex,ey=sx/t,sy/t
  return [E,N,G*ex,G*ey,k*A,k*Q*ex,k*Q*ey,
    k*(JX*ex*ex+JY*ey*ey),k*(JX-JY)*ex*ey,k*(JX*ey*ey+JY*ex*ex)]

def exact_psd(mat):
 m=[[Fraction.from_float(float(x)) for x in row] for row in mat]
 minors=[m[i][i] for i in range(3)]
 minors += [m[i][i]*m[j][j]-m[i][j]*m[j][i] for i,j in [(0,1),(0,2),(1,2)]]
 minors += [m[0][0]*(m[1][1]*m[2][2]-m[1][2]*m[2][1])-m[0][1]*(m[1][0]*m[2][2]-m[1][2]*m[2][0])+m[0][2]*(m[1][0]*m[2][1]-m[1][1]*m[2][0])]
 return all(x>=0 for x in minors), min(minors)

checks=[]
states=[('tiny-'+str(i),r['q'],r['stable_response']) for i,r in enumerate(report['positive_tiny_caps'])]
states += [('inner-'+str(i),r['q'],r['response']) for i,r in enumerate(report['inner_rim_dispatch_checks'])]
base=json.loads((P.parent/'annular-seat-response-v1/input.json').read_bytes())
states += [(r['id'],s['q'],r['response']) for r,s in zip(report['immutable_v1_moderate_replay'],base['states'],strict=True)]
gram_error=D(0); min_weight=None; dense_rejected=0
for label,q,out in states:
 expected=oracle(q)
 if 'highprecision_energy_nmm' in out:
  H=[[D(x) for x in row] for row in out['highprecision_tangent_delta_sx_sy']]
  actual=[D(out['highprecision_energy_nmm']),*map(D,out['highprecision_resisting_gradient_N_Gx_Gy']),
          H[0][0],H[0][1],H[0][2],H[1][1],H[1][2],H[2][2]]
  with localcontext() as ctx:
   ctx.prec=120
   W=list(map(D,out['positive_Gram_weights']));V=[[D(x) for x in row] for row in out['positive_Gram_vectors']]
   assert all(w>0 for w in W)
   min_weight=min([*W,*([min_weight] if min_weight is not None else [])])
   rebuilt=[[sum(w*v[i]*v[j] for w,v in zip(W,V,strict=True)) for j in range(3)] for i in range(3)]
   gram_error=max(gram_error,max(abs(H[i][j]-rebuilt[i][j])/abs(rebuilt[i][j]) if rebuilt[i][j] else abs(H[i][j]) for i in range(3) for j in range(3)))
  usable,_=exact_psd(out['rounded_dense_tangent_diagnostic'])
  assert usable==out['rounded_dense_tangent_usable']
  if not usable:
   dense_rejected+=1;assert out['tangent_delta_sx_sy'] is None and out['relative_six_dof_tangent'] is None
  with localcontext() as ctx:
   ctx.prec=120
   err=max(abs(x-y)/abs(y) if y else abs(x-y) for x,y in zip(actual,expected,strict=True))
  assert err<D('1e-75'),(label,str(err))
 else:
  H=out['tangent_delta_sx_sy']
  actual=[out['energy_nmm'],*out['resisting_gradient_N_Gx_Gy'],H[0][0],H[0][1],H[0][2],H[1][1],H[1][2],H[2][2]]
  err=max(abs(D.from_float(float(x))-y)/abs(y) if abs(y)>D('1e-12') else abs(D.from_float(float(x))-y) for x,y in zip(actual,expected,strict=True))
  assert err<D('5e-13'),(label,str(err))
 force=np.array(out['force_on_washer_local_xyz_n']);moment=np.array(out['moment_on_washer_at_annulus_center_local_xyz_nmm']);R=np.array(out['resisting_gradient_N_Gx_Gy'])
 assert np.array_equal(force,[0.,0.,R[0]]) and np.array_equal(moment,[R[2],-R[1],0.])
 assert np.array_equal(-force,out['force_on_receiving_body_local_xyz_n']) and np.array_equal(-moment,out['moment_on_receiving_body_at_annulus_center_local_xyz_nmm'])
 checks.append({'id':label,'relative_max_E_R_H_error':str(err),'normal_n':out['resisting_gradient_N_Gx_Gy'][0],'energy_nmm':out['energy_nmm'],'dense_usable':out['rounded_dense_tangent_usable']})
integration_observations = {'independent_angular_radial_oracle':'Decimal120/96pointGauss, positive radial polynomials',
 'cases':checks,'Gram_relative_max_reconstruction_error':str(gram_error),'minimum_positive_Gram_weight':str(min_weight),'dense_rejected_checked':dense_rejected,
 'loaded_hashes':before,'after_hashes':{str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in [P/'outer_cap_dispatch_final.py',P/'dispatch-input.json',P/'dispatch-result-final.json']}}

derivative_observations=[]
states=[('tiny-'+str(i),r['q']) for i,r in enumerate(report['positive_tiny_caps'])]
states += [('inner-rim',[-7.14375,1.,0.]),('former-switch',[-17.526+17.526*1e-4,1.,0.])]
for label,q in states:
 kwargs=dict(inner_radius_mm=7.14375,outer_radius_mm=17.526,bedding_n_mm3=1.,normal_approach_mm=q[0],closure_slopes=q[1:])
 out=mod['response'](**kwargs)
 if 'highprecision_energy_nmm' in out:
  R=list(map(D,out['highprecision_resisting_gradient_N_Gx_Gy']))
  H=[[D(v) for v in row] for row in out['highprecision_tangent_delta_sx_sy']]
 else:
  R=list(map(D.from_float,out['resisting_gradient_N_Gx_Gy']))
  H=[[D.from_float(v) for v in row] for row in out['tangent_delta_sx_sy']]
 a,b,t,h=mod['cap_kinematics'](kwargs)
 errs=[]
 for j in range(3):
  step=float(h*t)*1e-4/(1. if j==0 else 17.526)
  if label=='inner-rim':step=[1e-5,1e-7,1e-7][j]
  if q[j]:
   quantum=math.ulp(q[j]);step=max(1,round(step/quantum))*quantum
  pp,pm=q.copy(),q.copy();pp[j]+=step;pm[j]-=step
  op,om=oracle(pp),oracle(pm)
  with localcontext() as ctx:
   ctx.prec=120
   span=D.from_float(pp[j])-D.from_float(pm[j])
   assert span>0
   assert (D.from_float(pp[j])+D.from_float(pm[j]))/2==D.from_float(q[j])
   actual=[(op[0]-om[0])/span,*[(op[i]-om[i])/span for i in range(1,4)]]
   target=[R[j],*[H[i][j] for i in range(3)]]
   errs += [abs(x-y)/abs(y) if y else abs(x-y) for x,y in zip(actual,target,strict=True)]
 assert max(errs)<D('2e-7'),(label,str(max(errs)))
 derivative_observations.append({'id':label,'independent_energy_gradient_H_FD_relative_max_error':str(max(errs))})
# Whole-annulus zero-pressure touch has a branch-dependent tangent.
def call(q):return mod['response'](inner_radius_mm=7.14375,outer_radius_mm=17.526,bedding_n_mm3=1.,normal_approach_mm=q[0],closure_slopes=q[1:])
whole=[call([v,0.,0.]) for v in [-1e-10,0.,1e-10]]
assert whole[0]['energy_nmm']==whole[1]['energy_nmm']==0.
assert whole[0]['resisting_gradient_N_Gx_Gy']==whole[1]['resisting_gradient_N_Gx_Gy']==[0.,0.,0.]
assert not np.any(whole[1]['tangent_delta_sx_sy'])
assert whole[2]['resisting_gradient_N_Gx_Gy'][0]>0. and whole[2]['tangent_delta_sx_sy'][0][0]>0.
exact=call([-17.526,1.,0.])
assert exact['energy_nmm']==0. and exact['resisting_gradient_N_Gx_Gy']==[0.,0.,0.]
for path,digest in report['source_sha256'].items():
 assert hashlib.sha256(Path(path).read_bytes()).hexdigest()==digest,path
fixed={
 str(P/'outer_cap_dispatch_final.py'):'f1e5a02537fdb6dcaf6521862457ddbab195708221f02bd5f6fd4964cccebf12',
 str(P/'dispatch-input.json'):'910fbac9d936da2786170c5a76b201e3f70ce7a4c96a2fffdb3ad26e3764631c',
 str(P/'dispatch-result-final.json'):'33d05dbc2e0887ab44a2ba971147a20a21b6948b150b16d66a492f800730a061',
}
assert before==fixed
assert all(hashlib.sha256(Path(path).read_bytes()).hexdigest()==digest for path,digest in fixed.items())
print(json.dumps({'integration':integration_observations,'derivatives':derivative_observations,
 'whole_zero_touch':'zero energy/force; inactive tangent0 is generalized branch choice; positive-side unit derivative804.648309885082',
 'exact_binary_point_grazing_zero':True,'verified_source_pin_count':len(report['source_sha256']),
 'float_tangent_no_horizontal_or_yaw_action':all(not np.any(np.array(call(q)['relative_six_dof_tangent'])[:,[0,1,5]]) for q in [[.1,.001,.002],[0.,.003,.004],[-7.14375,1.,0.]])}))

