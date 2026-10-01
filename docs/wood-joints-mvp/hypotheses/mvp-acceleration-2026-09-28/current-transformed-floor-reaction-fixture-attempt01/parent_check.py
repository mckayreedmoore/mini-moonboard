"""Parent independent transformed reaction and physical balance hand check."""
import hashlib
import json
from pathlib import Path
import re

HERE=Path(__file__).resolve().parent
path=HERE/'native/model.dat'
data=path.read_text()
blocks={}
for match in re.finditer(r'^\s*(displacements|forces) [^\n]*time\s+([\d.E+-]+)\n',data,re.M):
    rows={}
    for line in data[match.end():].splitlines():
        fields=line.split()
        if len(fields)==4 and fields[0].isdigit():
            rows[int(fields[0])]=tuple(map(float,fields[1:]))
        elif rows:
            break
    key=(match[1],float(match[2])); assert key not in blocks
    blocks[key]=rows
records=[]
max_u=max_rf=max_balance=max_moment=0.
for kind,time in sorted(blocks):
    if kind!='displacements': continue
    u,rf=blocks[(kind,time)],blocks[('forces',time)]
    assert set(u)==set(rf)==set(range(1,17))
    if time<=1:
        fx=[6*time,-4*time]; fz=[-20*time,-40*time]
    else:
        s=time-1; fx=[6-9*s,-4+9*s]; fz=[-20-10*s,-40+30*s]
    z=[f/200 for f in fz]; gx=[5*v for v in z]
    raw_expected=[1.5*gx[0]-.5*gx[1],-.5*gx[0]+1.5*gx[1]]
    corrections=[1.5*fx[0]-.5*fx[1],-.5*fx[0]+1.5*fx[1]]
    raw=[rf[3][0],rf[4][0]]
    source_reactions=[raw[j]-corrections[j] for j in (0,1)]
    body_reactions=[.75*source_reactions[0]+.25*source_reactions[1],
                    .25*source_reactions[0]+.75*source_reactions[1]]
    body_residual=[]
    for j,(p,xz,xzg,zp,zg,q,qg) in enumerate(((1,5,6,7,8,9,10),(2,11,12,13,14,15,16))):
        expected_u={p:(0.,0.,z[j]),xz:(z[j]/4,0.,0.),xzg:(0.,0.,0.),
                    zp:(0.,0.,z[j]),zg:(0.,0.,0.),q:(0.,0.,-z[j]),qg:(0.,0.,0.)}
        sx,sz,normal=5*z[j],98.75*z[j],-100*z[j]
        assert normal>0
        expected_rf={p:(0.,0.,fz[j]),xz:(sx,0.,0.),xzg:(-sx,0.,0.),
                     zp:(0.,0.,sz),zg:(0.,0.,-sz),q:(0.,0.,normal),qg:(0.,0.,-normal)}
        max_u=max(max_u,*(abs(u[n][d]-v[d]) for n,v in expected_u.items() for d in range(3)))
        max_rf=max(max_rf,*(abs(rf[n][d]-v[d]) for n,v in expected_rf.items() for d in range(3)))
        residual=(fx[j]+body_reactions[j]-rf[xz][0],
                  fz[j]-.25*rf[xz][0]-rf[zp][2]+rf[q][2])
        max_balance=max(max_balance,*map(abs,residual))
        body_residual.append(residual)
    for j,n in enumerate((3,4)):
        max_u=max(max_u,*map(abs,u[n]))
        max_rf=max(max_rf,abs(raw[j]-raw_expected[j]),abs(rf[n][1]),abs(rf[n][2]))
    source_moment=-25*source_reactions[0]-75*source_reactions[1]
    physical_moment=-100*body_reactions[1]
    global_yaw=-100*fx[1]+100*rf[11][0]+source_moment
    max_moment=max(max_moment,abs(source_moment-physical_moment),abs(global_yaw))
    records.append({'time':time,'source_reactions_N':source_reactions,
                    'body_support_x_N':body_reactions,'body_residual_x_z_N':body_residual,
                    'global_yaw_residual_Nmm':global_yaw})
assert len(records)==12 and max_u<2e-6 and max_rf<.002 and max_balance<.002 and max_moment<.02
result={'status':'PASS_PARENT_ALL_PRINTED_TRANSFORMED_REACTION_INCREMENTS',
        'printed_increment_count':len(records),'max_displacement_error_mm':max_u,
        'max_RF_error_N':max_rf,'max_body_balance_residual_N':max_balance,
        'max_source_physical_and_global_yaw_residual_Nmm':max_moment,
        'model_dat_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
        'frame_ready_for_native_run':False,'complete_joint_validated':False,'records':records}
(HERE/'parent-all-increment-check.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({k:v for k,v in result.items() if k!='records'}))
