#!/usr/bin/env python3
"""Read-only polynomial surface envelopes for an assumed rigid translation.

No meshing, CAD mutation, contact evaluation or native mechanics is performed.
"""
from pathlib import Path
import argparse
import hashlib
import json
import re
import sys
import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
SOURCE = HERE.parent / 'ordinary-port-motion-attempt09-common-map'
PINS = {
    'mesh.inp': '117fdc67c8d3f7f7e3bf1df41d842c9d8e7fa57e1c941676bccd882878bb4803',
    'mesh.json': '1043bd4a7ac03e589d6f8819f98231b33a866ee917d1e9c7099d0104092d0a07',
    'contact-fragment.inc': '35a4513b7877b04b0c2be053f3084d07178a148c606780d12d54388636574b24',
    'contact-manifest.json': '50f7d8c9b85197f43732d49d13e75240fa6d5423673d28274e278829878a594d',
    'port-motion_n_plus.json': 'a28c0ba399842f96801ce5ce982dc6b52d459c537c132d283de01298d63b31bc',
}
HELPERS = {
    'fea/floor_contact.py': 'f72c9de2f046f6f207974779de555bfa37f5964484ffae2293fc450c35025825',
    'fea/wood_joint_patch_contact_contract.py': '4e912fc02d024b1217eaafcff808ab2b76a9a19c4dc05d72796f5df4854eaead',
}
FACES_EXPECTED = ((0,1,2,4,5,6),(0,3,1,7,8,4),(1,3,2,8,9,5),(2,3,0,9,7,6))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def shape(bary):
    u,v,w=np.asarray(bary).T
    return np.array([u*(2*u-1),v*(2*v-1),w*(2*w-1),4*u*v,4*v*w,4*w*u]).T


def controls(points):
    # B_ij=2*x(mid_ij)-(x_i+x_j)/2 for quadratic Bernstein basis 2*Li*Lj.
    return np.concatenate([points[:3],np.array([
        2*points[3]-(points[0]+points[1])/2,
        2*points[4]-(points[1]+points[2])/2,
        2*points[5]-(points[2]+points[0])/2])])


def domains(level):
    a,b,c=np.eye(3);ab=(a+b)/2;bc=(b+c)/2;ca=(c+a)/2
    if level==0:return [np.array([a,b,c])]
    assert level==1
    return [np.array(x) for x in [(a,ab,ca),(ab,b,bc),(ca,bc,c),(ab,bc,ca)]]


def polynomial_preflight():
    # An independent Bernstein evaluation must reproduce quadratic Lagrange
    # evaluation, including exact restriction to the four parameter subdomains.
    points=np.array([[1,2,3],[5,-1,2],[-2,1,4],[3,4,1],[0,-2,5],[2,0,3]],float)
    samples=np.array([[i/10,j/10,1-(i+j)/10] for i in range(11) for j in range(11-i)])
    error=0.0
    for tri in domains(1):
        six=np.concatenate([tri,[(tri[0]+tri[1])/2,(tri[1]+tri[2])/2,(tri[2]+tri[0])/2]])
        cp=controls(shape(six)@points)
        u,v,w=samples.T
        bern=np.array([u*u,v*v,w*w,2*u*v,2*v*w,2*w*u]).T
        error=max(error,float(np.max(abs(bern@cp-shape(samples@tri)@points))))
        assert np.max(abs(bern.sum(axis=1)-1))<1e-14 and bern.min()>=-1e-14
    assert error<1e-12
    return {'quadratic_restriction_reconstruction_error':error,'sample_count_per_subdomain':len(samples),
            'basis':'nonnegative quadratic Bernstein weights sum to one over each closed triangle'}


def build():
    for f,h in PINS.items():assert sha(SOURCE/f)==h,f
    for f,h in HELPERS.items():assert sha(ROOT/f)==h,f
    sys.path.insert(0,str(ROOT))
    from fea.wood_joint_patch_contact_contract import parse_c3d10_deck
    from fea.floor_contact import FACES
    assert FACES==FACES_EXPECTED
    nodes,elements,_=parse_c3d10_deck((SOURCE/'mesh.inp').read_text(),context='polynomial radial envelope')
    report=json.loads((SOURCE/'mesh.json').read_text())
    manifest=json.loads((SOURCE/'contact-manifest.json').read_text())
    motion=json.loads((SOURCE/'port-motion_n_plus.json').read_text())
    assert motion['relative_joint_coordinate_mm']==[0,0,1,0,0,0]
    axes={r['physical_bolt_id']:r for r in report['input_geometry_context']['physical_bolts']}
    surfaces={};pairs=[];mode=None
    for raw in (SOURCE/'contact-fragment.inc').read_text().splitlines():
        line=raw.strip()
        if not line or line.startswith('**'):continue
        if line.startswith('*SURFACE,'):
            name=re.search(r'(?:^|,)NAME=([^,]+)',line)[1];assert name not in surfaces
            surfaces[name]=[];mode=('surface',name)
        elif line.startswith('*CONTACT PAIR,'):mode=('pair',None)
        elif line.startswith('*'):mode=None
        elif mode and mode[0]=='surface':
            e,s=line.split(',');surfaces[mode[1]].append((int(e),int(s.removeprefix('S'))))
        elif mode and mode[0]=='pair':pairs.append(tuple(line.split(',')));mode=None
    assert len(pairs)==len(manifest['pairs'])==35
    results=[]
    for i,(row,(sn,mn)) in enumerate(zip(manifest['pairs'],pairs),1):
        assert (sn,mn)==(f'WJCP_{i:03d}_S',f'WJCP_{i:03d}_M')
        if row['category'] not in ['open_bolt_shank_to_wood_bore','open_bolt_shank_to_washer_bore']:continue
        axis=axes[row['physical_bolt_id']]
        origin=np.array(axis['axis_origin_global_xyz_mm']);a=np.array(axis['axis_direction_head_to_nut_global_xyz']);a=a/np.linalg.norm(a)
        stages=[]
        for level in [0,1]:
            bounds=[]
            for name,count in [(sn,row['slave_face_count']),(mn,row['master_face_count'])]:
                assert len(surfaces[name])==count
                lower=[];upper=[]
                for eid,side in surfaces[name]:
                    points=np.array([nodes[elements[eid][j]] for j in FACES[side-1]])
                    for tri in domains(level):
                        six=np.concatenate([tri,[(tri[0]+tri[1])/2,(tri[1]+tri[2])/2,(tri[2]+tri[0])/2]])
                        cp=controls(shape(six)@points)
                        radial=cp-origin;radial-=np.outer(radial@a,a)
                        direction=np.mean(radial[:3],axis=0);direction/=np.linalg.norm(direction)
                        lower.append(float(np.min(radial@direction)))
                        upper.append(float(np.max(np.linalg.norm(radial,axis=1))))
                bounds.append({'surface':name,'face_count':count,'subpatch_count':len(lower),
                               'radial_lower_bound_mm':min(lower),'radial_upper_bound_mm':max(upper)})
            offset=.25 if row['category']=='open_bolt_shank_to_wood_bore' else 0.
            margin=bounds[1]['radial_lower_bound_mm']-bounds[0]['radial_upper_bound_mm']-offset
            stages.append({'parameter_subdivision_level':level,'shaft':bounds[0],'bore':bounds[1],
                           'relative_translation_norm_assumption_mm':offset,
                           'computed_radial_separation_lower_bound_mm':margin,
                           'numerical_reporting_reserve_mm':1e-6,'margin_after_reserve_mm':margin-1e-6})
        results.append({'pair_number':i,'pair_id':row['pair_id'],'physical_bolt_id':row['physical_bolt_id'],
                        'category':row['category'],'axis_origin_global_xyz_mm':origin.tolist(),
                        'axis_unit_global_xyz':a.tolist(),'bounds':stages})
    assert [r['pair_number'] for r in results]==list(range(20,36))
    positive=all(r['bounds'][1]['margin_after_reserve_mm']>0 for r in results)
    return {'schema':'ordinary_n_motion_radial_envelope/v1',
            'status':'POSITIVE_GEOMETRIC_SEPARATION_BOUND_UNDER_DECLARED_TRANSLATIONS' if positive else 'BOUND_INCONCLUSIVE',
            'producer_sha256':sha(Path(__file__)),'source_sha256':PINS,'helper_sha256':HELPERS,
            'numpy_version':np.__version__,'polynomial_preflight':polynomial_preflight(),'pairs':results,
            'minimum_subdivided_margin_after_reserve_mm':min(r['bounds'][1]['margin_after_reserve_mm'] for r in results),
            'assumptions':['Each wood-to-shaft relative rigid translation has norm at most0.25mm.','Each washer co-translates with its shaft.','All bodies retain the source coordinates plus rigid translations; no elastic deformation is modeled.'],
            'limits':['Computed floating-point envelope, not an outward-rounded interval-arithmetic certificate.','Parameter subdivision restricts the existing quadratic surface; no remesh or geometry change.','Unsubdivided inconclusive bounds are preserved and are not evidence of overlap.','Only16 radial surface pairs are addressed, not19 planar pairs or trimmed-seat overlap.','This does not evaluate CalculiX contact projection, penalty activation, equilibrium, first-bearing onset, complete-joint nullity or a physical assembly.'],
            'mesh_changed':False,'native_solve_executed':False,'contact_feasibility_proved':False,
            'mechanical_acceptance':False,'joint_acceptance':False,'release':False}


if __name__=='__main__':
    ap=argparse.ArgumentParser();g=ap.add_mutually_exclusive_group(required=True);g.add_argument('--write',action='store_true');g.add_argument('--verify',action='store_true');args=ap.parse_args()
    result=build();payload=json.dumps(result,indent=2,sort_keys=True,allow_nan=False)+'\n';out=HERE/'radial-envelope.json'
    if args.write:
        with out.open('x') as f:f.write(payload)
    else:assert out.read_text()==payload,'Stored envelope differs from source reproduction'
    print(json.dumps({'status':result['status'],'result_sha256':sha(out),'minimum_margin_mm':result['minimum_subdivided_margin_after_reserve_mm'],'native_solve_executed':False}))
