"""Independent DAT-to-normal classification replay; no imported FEA kernel."""
from pathlib import Path
import hashlib,json,math,re
HERE=Path(__file__).resolve().parent
BASE=HERE.parent
RUN=BASE/'current-springa-selected-floor-a12-forward-attempt01'
SCREEN=BASE/'current-springa-a12-forward-selected-floor-screen-attempt01/screen.json'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def number(t):return float(t.replace('D','E'))
def radius(t):
 mant,exp=t.upper().replace('D','E').split('E');return .5*10**(int(exp)-len(mant.split('.')[1]))
def parse(text):
 matches=list(re.finditer(r'^\s*(displacements|forces)\s*\([^\n]*\btime\s+([0-9.EeDd+-]+)\s*\n',text,re.M));out={}
 for i,m in enumerate(matches):
  kind='u' if m[1]=='displacements' else 'rf';rows={};radii={};started=False
  for line in text[m.end():matches[i+1].start() if i+1<len(matches) else len(text)].splitlines():
   f=line.split()
   if len(f)==4 and f[0].isdigit():
    n=int(f[0]);assert n not in rows;rows[n]=list(map(number,f[1:]));radii[n]=list(map(radius,f[1:]));started=True
   elif started:break
  out.setdefault(number(m[2]),{})[kind]=(rows,radii)
 return out
def main():
 model=json.loads((RUN/'model.json').read_text());screen=json.loads(SCREEN.read_text());states=parse((RUN/'model.dat').read_text());nodes={}
 in_nodes=False
 for line in (RUN/'model.inp').read_text().splitlines():
  if line.startswith('*'):in_nodes=line.upper().split(',')[0]=='*NODE';continue
  if in_nodes and line.strip():
   f=line.split(',');nodes[int(f[0])]=[number(x) for x in f[1:4]]
 bindings={b['group']:b for b in model['unilateral_springa_bindings'] if b['physical_owner']['role']=='floor_normal'};assert len(bindings)==100
 assert {step['time'] for step in screen['times']}==set(states) and len(states)==7 and max(states)==1.0
 reports=[]
 for step in screen['times']:
  u,ur=states[step['time']]['u'];rf,rr=states[step['time']]['rf'];counts={'STRICTLY_POSITIVE':0,'STRICTLY_SEPARATED_WITH_ZERO_ENDPOINT_RF':0,'AMBIGUOUS_OR_NONCOMPLEMENTARY':0}
  assert len(step['rows'])==100 and {row['source_group'] for row in step['rows']}==set(bindings)
  for row in step['rows']:
   b=bindings[row['source_group']];a,z=map(int,b['springa_nodes']);p1,p2=map(int,b['source_projection_nodes']);d=int(b['source_projection_dof'])-1
   q=u[p2][d]-u[p1][d];qr=ur[p2][d]+ur[p1][d];initial=[nodes[a][j]-nodes[z][j] for j in range(3)];current=[initial[j]+u[a][j]-u[z][j] for j in range(3)]
   l0=math.sqrt(math.fsum(x*x for x in initial));length=math.sqrt(math.fsum(x*x for x in current));elong=length-l0;guard=16*math.ulp(1.)*max(length,l0,1.);er=math.fsum(abs(current[j]/length)*(ur[a][j]+ur[z][j]) for j in range(3))+guard
   axis=b['numerical_axis_global_xyz'];internal=math.fsum(rf[a][j]*axis[j] for j in range(3));ir=math.fsum(rr[a][j]*abs(axis[j]) for j in range(3));k=b['stiffness_n_per_mm'];fi=[k*max(elong-er,0),k*max(elong+er,0)]
   fg=32*math.ulp(1.)*max(1.,abs(internal),k*max(elong,0));zero=all(abs(rf[n][j])<=rr[n][j]+fg for n in (a,z) for j in range(3))
   positive=q-qr>0 and elong-er>0 and fi[0]>0 and internal-ir>0
   separated=q+qr<0 and elong+er<0 and fi==[0.,0.] and zero
   assert not (positive and separated)
   label='STRICTLY_POSITIVE' if positive else 'STRICTLY_SEPARATED_WITH_ZERO_ENDPOINT_RF' if separated else 'AMBIGUOUS_OR_NONCOMPLEMENTARY'
   assert label==row['classification'],(step['time'],b['group'],label,row['classification'])
   assert abs(q-row['projected_q_mm'])<1e-12 and abs(qr-row['projected_q_rounding_radius_mm'])<1e-12
   assert abs(elong-row['geometric_elongation_mm'])<1e-12
   counts[label]+=1
  assert counts=={'STRICTLY_POSITIVE':31,'STRICTLY_SEPARATED_WITH_ZERO_ENDPOINT_RF':69,'AMBIGUOUS_OR_NONCOMPLEMENTARY':0}
  reports.append({'time':step['time'],'counts':counts})
 result={'status':'PASS_PARENT_INDEPENDENT_NATIVE_NORMAL_CLASSIFICATIONS','source_sha256':{str(p):sha(p) for p in (SCREEN,RUN/'model.json',RUN/'model.inp',RUN/'model.dat',Path(__file__))},'increments':reports,'cells_checked':700,'imported_fea_kernel':False,'corner_demands_usable':False,'scope':'Independent native token, emitted-node geometry and strict normal classification replay only; no physical force adoption or joint resistance qualification.'}
 (HERE/'audit.json').write_text(json.dumps(result,indent=2)+'\n');print(result['status'])
if __name__=='__main__':main()
