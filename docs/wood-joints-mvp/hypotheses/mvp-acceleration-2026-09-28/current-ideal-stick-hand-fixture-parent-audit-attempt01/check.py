"""Exact arithmetic enumeration of the declared three-DOF ideal-stick fixture."""
from fractions import Fraction as F
from pathlib import Path
import hashlib, json
HERE=Path(__file__).resolve().parent
SPEC=HERE.parent/'current-springa-ideal-stick-branch-cycle-method-attempt01/fixture-spec.json'
def solve(a,b):
    rows=[[F(x) for x in row]+[F(y)] for row,y in zip(a,b)]
    n=len(rows)
    for i in range(n):
        p=next(j for j in range(i,n) if rows[j][i]); rows[i],rows[p]=rows[p],rows[i]
        scale=rows[i][i]; rows[i]=[x/scale for x in rows[i]]
        for j in range(n):
            if j!=i:
                factor=rows[j][i]; rows[j]=[x-factor*y for x,y in zip(rows[j],rows[i])]
    return [r[-1] for r in rows]
def main():
    spec=json.loads(SPEC.read_text());k=spec['structure']['stiffness_matrix_N_per_mm'];load=spec['load_N']
    assert k==[[2,0,1],[0,1,0],[1,0,2]] and load==[-4,0,-1]
    assert spec['normal_support']['stiffness_N_per_mm']==2
    rows=[]
    for mask in [0,1]:
        for bearing in [False,True]:
            effective=[[F(x) for x in row] for row in k]
            if bearing: effective[2][2]+=2
            if mask:
                u=[F(0),F(0),F(load[2])/effective[2][2]]
                reaction=[F(load[i])-sum(effective[i][j]*u[j] for j in range(3)) for i in range(2)]
            else: u=solve(effective,load);reaction=[F(0),F(0)]
            n=2*u[2] if bearing else F(0)
            residual=[sum(F(k[i][j])*u[j] for j in range(3))+(reaction[i] if i<2 else n)-load[i] for i in range(3)]
            assert residual==[0,0,0]
            sector=(u[2]>0) if bearing else (u[2]<=0)
            gate=bool(mask)==(u[2]>0)
            rows.append({'mask':mask,'normal_bearing_sector':bearing,'u_exact_mm':list(map(str,u)),
                         'tangent_reactions_exact_N':list(map(str,reaction)),'normal_force_exact_N':str(n),
                         'equilibrium_residual_exact':list(map(str,residual)),
                         'normal_sector_consistent':sector,'stick_gate_consistent':gate,
                         'admissible':sector and gate})
    assert not any(r['admissible'] for r in rows)
    valid=[r for r in rows if r['normal_sector_consistent']]
    assert len(valid)==2
    assert next(r for r in valid if r['mask']==1)['u_exact_mm']==['0','0','-1/2']
    assert next(r for r in valid if r['mask']==0)['u_exact_mm']==['-15/7','0','2/7']
    out={'status':'PASS_EXACT_HAND_FIXTURE_NO_ADMISSIBLE_STATIC_BRANCH',
         'source_spec_sha256':hashlib.sha256(SPEC.read_bytes()).hexdigest(),'rows':rows,
         'all_mask_and_normal_sectors_enumerated':True,'native_method_verified':False,
         'full_frame_branch_existence_decided':False,'joint_accepted':False}
    (HERE/'audit.json').write_text(json.dumps(out,indent=2)+'\n')
    print(out['status'])
if __name__=='__main__': main()
