from pathlib import Path
import json,hashlib
from fractions import Fraction
import numpy as np
p=Path(__file__).resolve().parent
d=json.loads((p/'expected.json').read_text()); lines=(p/'input/shared_slave_motion.inp').read_text().splitlines()
nodes={};equations=[];mode=None;i=0
while i<len(lines):
 line=lines[i].strip();i+=1
 if not line or line.startswith('**'):continue
 if line.upper().startswith('*NODE,') or line.upper()=='*NODE':mode='node';continue
 if line.upper()=='*EQUATION':
  count=int(lines[i]);i+=1;terms=[]
  while len(terms)<count:
   tok=[x.strip() for x in lines[i].split(',') if x.strip()];i+=1
   assert len(tok)%3==0
   terms.extend((int(tok[j]),int(tok[j+1]),float(tok[j+2])) for j in range(0,len(tok),3))
  assert len(terms)==count;equations.append(terms);mode=None;continue
 if line.startswith('*'):mode=None;continue
 if mode=='node':
  tok=line.split(',');nodes[int(tok[0])]=np.array([float(x) for x in tok[1:4]])
assert len(equations)==12
report={}
for index,name in enumerate(('PORT_TOP','PORT_RIGHT')):
 m=d['motion_map']['maps'][name];cols=[tuple(x) for x in m['projection_dof_columns']];center=np.array([float(Fraction(x)) for x in m['area_centroid_mm']]);weights={int(k):float(Fraction(v)) for k,v in m['face_weights_mm2_by_node'].items()}
 a=[];w=[]
 for n,j in cols:
  x,y,z=nodes[n]-center
  rows=[[1,0,0,0,z,-y],[0,1,0,-z,0,x],[0,0,1,y,-x,0]]
  a.append(rows[j-1]);w.append(weights[n])
 a=np.array(a);w=np.array(w);P=np.linalg.solve(a.T@(w[:,None]*a),a.T*w)
 declared=np.array([[float(Fraction(x)) for x in row] for row in m['projection_matrix_P_exact']])
 p_error=float(np.max(np.abs(P-declared)));assert p_error<1e-13
 deps=[tuple(x) for x in m['dependent_dofs']];depcols=[cols.index(x) for x in deps];pivot=P[:,depcols]
 assert np.linalg.matrix_rank(pivot)==6
 controls=m['controller_node_ids'];eq=equations[index*6:index*6+6];maxerr=0
 for k,terms in enumerate(eq):
  assert terms[0][:2]==deps[k] and terms[0][2]==1
  actual={(n,j):v for n,j,v in terms};expected={cols[c]:v for c,v in enumerate(np.linalg.solve(pivot,P)[k]) if c not in depcols};expected[deps[k]]=1
  for q,n in enumerate(controls):expected[(n,1)]=-np.linalg.inv(pivot)[k,q]
  maxerr=max(maxerr,max(abs(actual.get(key,0)-expected.get(key,0)) for key in actual.keys()|expected.keys()))
 assert maxerr<1e-12
 u=np.array([d['analytical_known_answer']['affine_endpoint_displacement_mm_by_physical_node'][str(n)][j-1] for n,j in cols]);q=P@u;assert np.max(abs(q-m['prescribed_q']))<1e-18
 Q=np.array([0,0,-4,0,0,0] if name=='PORT_TOP' else [-4,0,0,0,0,0]);dual=P.T@Q
 target=np.array([-weights[n] if j==(3 if name=='PORT_TOP' else 1) else 0 for n,j in cols]);dualerr=float(np.max(abs(dual-target)));assert dualerr<1e-13
 report[name]={'rank':6,'condition_inf':float(np.linalg.cond(pivot,np.inf)),'projection_error':p_error,'serialized_equation_error':maxerr,'pressure_dual_error':dualerr,'affine_q':q.tolist()}
print(json.dumps({'status':'PASS_INDEPENDENT_NUMPY_MAP_AND_SERIALIZED_EQUATION_RECONSTRUCTION','input_sha256':hashlib.sha256((p/'input/shared_slave_motion.inp').read_bytes()).hexdigest(),'expected_sha256':hashlib.sha256((p/'expected.json').read_bytes()).hexdigest(),'ports':report},indent=2))
