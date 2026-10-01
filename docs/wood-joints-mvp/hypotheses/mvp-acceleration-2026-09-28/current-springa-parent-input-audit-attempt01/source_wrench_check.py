"""Verify the original floor rows' owned physical force and moment mapping."""
from pathlib import Path
import hashlib
import json
import numpy as np

HERE=Path(__file__).resolve().parent
BASE=HERE.parent
source=BASE/'reduced-static-a12-rear-ratio1-gap0-attempt02/cycle-11-sign-closure-r1/model.json'
pin=hashlib.sha256(source.read_bytes()).hexdigest()
assert pin=='d3417111926c982a07ced393aa1c12f815aa87b5b8eb851b45bc63a1ea10fac0'
model=json.loads(source.read_text())
floor=json.loads((BASE/'current-floor-stick-constraint-audit-attempt01/audit.json').read_text())
A=np.load(BASE/'current-floor-stick-constraint-audit-attempt01/constraint-matrices.npz')['original']
B=np.zeros((6,A.shape[1]))
for j,(n,d) in enumerate(floor['physical_master_dofs']):
    unit=np.eye(3)[d-1]
    B[:3,j]=unit
    B[3:,j]=np.cross(model['nodes'][str(n)],unit)
expected=[]
for row in floor['row_owners']:
    owner=model['connection_ownership'][row['normal_cell']+'_friction']
    axis=owner['force_basis'][row['local_dof']-1]
    expected.append(np.r_[axis,np.cross(owner['point'],axis)])
difference=B@A.T-np.array(expected).T
force=float(np.max(np.abs(difference[:3])))
moment=float(np.max(np.abs(difference[3:])))
assert force<1e-9 and moment<1e-6
result={'status':'PASS_SOURCE_FLOOR_CHANNEL_FORCE_AND_MOMENT_MAP',
        'channels_checked':200,'max_unit_channel_force_error':force,
        'max_unit_channel_moment_error_mm':moment,'source_input_sha256':pin,
        'source_response_used':False,'native_solve_executed':False,
        'serialized_adapter_checked':False,'frame_ready_for_native_run':False,
        'complete_joint_validated':False}
(HERE/'source-reference-wrench-audit.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result))
