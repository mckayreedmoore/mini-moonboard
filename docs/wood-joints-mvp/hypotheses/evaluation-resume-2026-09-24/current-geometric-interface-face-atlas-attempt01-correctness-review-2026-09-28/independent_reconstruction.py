import hashlib, json, math
from collections import Counter
from importlib.metadata import version
from pathlib import Path
import sys
import cadquery as cq

root=next(
    parent for parent in Path(__file__).resolve().parents
    if (parent/'current-candidate.json').is_file() and (parent/'.git').is_dir()
)
observed_toolchain={
    'python':'.'.join(map(str,sys.version_info[:3])),
    'cadquery':str(cq.__version__),
    'cadquery_ocp':version('cadquery-ocp'),
}
assert observed_toolchain=={'python':'3.12.3','cadquery':'2.8.0','cadquery_ocp':'7.9.3.1.1'}, observed_toolchain
base=root/'docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24'
packet=base/'current-geometric-interface-face-atlas-attempt01-2026-09-28'
a=json.loads((packet/'face-pair-atlas.json').read_text())
pins=json.loads((packet/'source-pins.json').read_text())
manifest=json.loads((base/'current-full-frame-member-solids-attempt01/bundle/current-full-frame-member-solids.json').read_text())
graph=json.loads((base/'current-geometric-interface-map-attempt02-2026-09-28/complete-contact-graph.json').read_text())
evidence=json.loads((base/'current-overlap-contact-geometry-evidence-attempt07/geometry-evidence.json').read_text())

def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def canon(x): return json.dumps(x,sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False)
def rnd(x):
    v=round(float(x),9)
    return 0.0 if v==0.0 else v
def vec(v):
    if hasattr(v,'toTuple'): v=v.toTuple()
    return [rnd(x) for x in v]
def bounds(s):
    b=s.BoundingBox(); return [rnd(x) for x in (b.xmin,b.xmax,b.ymin,b.ymax,b.zmin,b.zmax)]
def edgesig(e):
    verts=sorted(vec(v.Center()) for v in e.Vertices())
    return {'curve_type':str(e.geomType()),'length_mm':rnd(e.Length()),'center_xyz_mm':vec(e.Center()),'bounds_xyz_mm':bounds(e),'vertex_xyz_mm':verts}
def facesig(f):
    n=f.normalAt().normalized()
    es=[edgesig(e) for e in f.Edges()]; es.sort(key=canon)
    vs=sorted(vec(v.Center()) for v in f.Vertices())
    return {'surface_type':'PLANE','area_mm2':rnd(f.Area()),'center_xyz_mm':vec(f.Center()),'oriented_normal_xyz':vec(n),'bounds_xyz_mm':bounds(f),'vertex_xyz_mm':vs,'edge_signatures':es,'wire_count':len(f.Wires())}
def regionsig(f):
    es=[edgesig(e) for e in f.Edges()]; es.sort(key=canon)
    vs=sorted(vec(v.Center()) for v in f.Vertices())
    return {'surface_type':str(f.geomType()),'area_mm2':rnd(f.Area()),'center_xyz_mm':vec(f.Center()),'bounds_xyz_mm':bounds(f),'vertex_xyz_mm':vs,'edge_signatures':es,'wire_count':len(f.Wires())}
def boxoverlap(x,y,tol):
    u,v=bounds(x),bounds(y)
    return all(not(u[2*i+1] < v[2*i]-tol or v[2*i+1] < u[2*i]-tol) for i in range(3))

assert a['candidate']=='compact-floor-flush-wood-joints-development'
assert pins['candidate']==a['candidate']
assert a['revision_id']=='led-clearance-2x6-runner-seated-blocks-v1'==pins['revision_id']
assert pins['criterion_disposition']=='pending' and a['criterion_disposition']=='pending'
assert sha(packet/'face-pair-atlas.json')==pins['output_sha256']
for rel,digest in pins['source_hashes'].items(): assert sha(root/rel)==digest, rel

body_rows={x['member_id']:x for x in manifest['members']}
assert len(body_rows)==50==len(a['body_inventory'])
assert set(body_rows)=={x['member_id'] for x in a['body_inventory']}
atlas_bodies={x['member_id']:x for x in a['body_inventory']}
allfaces={}
body_totals={}
for member,row in body_rows.items():
    step=base/'current-full-frame-member-solids-attempt01'/row['step_file']
    assert sha(step)==row['step_sha256']==atlas_bodies[member]['step_sha256']
    sh=cq.importers.importStep(str(step)).val()
    assert sh.isValid() and len(sh.Solids())==1
    records=[]
    for ordinal,f in enumerate(sh.Faces(),1):
        if f.geomType()!='PLANE' or float(f.Area())<=1e-8: continue
        sig=facesig(f); digest=hashlib.sha256(canon(sig).encode()).hexdigest()
        fid=f'{member}/step-face-{ordinal:04d}-{digest[:16]}'
        records.append({'id':fid,'ordinal':ordinal,'sha':digest,'shape':f})
    expected=atlas_bodies[member]['planar_faces']
    assert len(records)==len(expected), (member,len(records),len(expected))
    exp_byid={x['face_id']:x for x in expected}
    assert len(exp_byid)==len(expected)
    for rec in records:
        exp=exp_byid[rec['id']]
        assert rec['ordinal']==exp['face_ordinal_1_based']
        assert rec['sha']==exp['signature_sha256']
        assert json.loads(canon(facesig(rec['shape'])))==exp['signature']
    allfaces[member]=records
    body_totals[member]=len(records)

edges={ 'pair:'+ '|'.join(sorted(r['member_ids'])):r for r in graph['edges'] }
evrows={r['pair_id']:r for r in evidence['pairs']}
assert len(edges)==len(evrows)==1225
finite=[(pid,row) for pid,row in edges.items() if row['geometry_state']=='finite_opposed_planar_touch']
unresolved=[(pid,row) for pid,row in edges.items() if row['geometry_state']=='zero_area_touch_or_unresolved']
assert len(finite)==115 and len(unresolved)==6
assert len(a['finite_opposed_interfaces'])==115 and len(a['unresolved_pairs'])==6
assert {x['pair_id'] for x in a['finite_opposed_interfaces']}=={p for p,r in finite}
assert {x['pair_id'] for x in a['unresolved_pairs']}=={p for p,r in unresolved}
assert not ({x['pair_id'] for x in a['finite_opposed_interfaces']} & {p for p,r in unresolved})
assert all(x['face_pair_mapping']=='unresolved; no source face identity assigned' for x in a['unresolved_pairs'])

observed_region_count=0; face_pair_count=0; pair_max_area_error=0; pair_max_shared_error=0; mapped_rows=0
for pid,row in finite:
    interface=next(x for x in a['finite_opposed_interfaces'] if x['pair_id']==pid)
    m1,m2=row['member_ids']
    seen=[]; area_sum=0.0; raw_region_count=0
    for fa in allfaces[m1]:
        sa=fa['shape']; na=sa.normalAt().normalized(); ca=sa.Center()
        for fb in allfaces[m2]:
            sb=fb['shape']
            if not boxoverlap(sa,sb,1e-5): continue
            nb=sb.normalAt().normalized(); dot=float(na.dot(nb))
            if abs(abs(dot)-1.0)>1e-7: continue
            offset=abs(float((sb.Center()-ca).dot(na)))
            if offset>1e-5: continue
            common=sa.intersect(sb)
            regs=[]
            for rf in common.Faces():
                area=float(rf.Area())
                if not math.isfinite(area): raise AssertionError('nonfinite Boolean face area')
                if area<=1e-6: continue
                sg=regionsig(rf); sh=hashlib.sha256(canon(sg).encode()).hexdigest()
                regs.append({'region_signature_sha256':sh,**sg})
            regs.sort(key=lambda x:(x['region_signature_sha256'],x['area_mm2'],x['center_xyz_mm']))
            area=sum(float(x['area_mm2']) for x in regs)
            if area<=1e-6: continue
            assert dot<0, (pid,fa['id'],fb['id'],dot)
            seen.append((fa,fb,dot,offset,area,regs)); area_sum += area; raw_region_count += len(regs)
    expected_pairs=interface['face_pairs']
    byids={(x['face_a_id'],x['face_b_id']):x for x in expected_pairs}
    assert len(byids)==len(expected_pairs)
    assert {(x[0]['id'],x[1]['id']) for x in seen}==set(byids), (pid,len(seen),len(byids))
    for fa,fb,dot,offset,area,regs in seen:
        exp=byids[(fa['id'],fb['id'])]
        assert exp['face_a_signature_sha256']==fa['sha'] and exp['face_b_signature_sha256']==fb['sha']
        assert exp['face_a_oriented_normal_xyz']==vec(fa['shape'].normalAt().normalized())
        assert exp['face_b_oriented_normal_xyz']==vec(fb['shape'].normalAt().normalized())
        assert exp['normal_dot']==rnd(dot)
        assert exp['coplanar_offset_mm']==rnd(offset)
        assert exp['overlap_area_mm2']==rnd(area)
        assert canon(exp['overlap_regions'])==canon(regs)
        assert all(r['surface_type']=='PLANE' and r['area_mm2']>1e-6 for r in regs)
    expected_area=float(row['opposed_planar_face_contact_area_mm2'])
    expected_shared=float(row['finite_shared_planar_face_area_mm2'])
    allowed=max(1e-6,expected_area*1e-10)
    allowed_shared=max(1e-6,expected_shared*1e-10)
    err=abs(area_sum-expected_area); err2=abs(area_sum-expected_shared)
    pair_max_area_error=max(pair_max_area_error,err); pair_max_shared_error=max(pair_max_shared_error,err2)
    assert seen and err<=allowed, (pid,area_sum,expected_area,allowed)
    assert err2<=allowed_shared, (pid,area_sum,expected_shared,allowed_shared)
    assert interface['face_pair_count']==len(seen)
    assert interface['reconstructed_opposed_area_mm2']==rnd(area_sum)
    assert interface['frozen_graph_opposed_area_mm2']==rnd(expected_area)
    assert interface['frozen_graph_shared_area_mm2']==rnd(expected_shared)
    assert interface['area_reconciliation_tolerance_mm2']==rnd(allowed)
    mapped_rows+=len(seen); observed_region_count+=raw_region_count; face_pair_count+=len(seen)

print(json.dumps({'bodies_verified':len(allfaces),'planar_faces_verified':sum(body_totals.values()),'body_planar_face_counts':dict(sorted(body_totals.items())),'graph_pairs':len(edges),'finite_body_pairs_reconstructed':len(finite),'unresolved_pairs_unmapped':len(unresolved),'mapped_source_face_pairs':mapped_rows,'boolean_overlap_regions':observed_region_count,'max_pair_opposed_area_abs_error_mm2':pair_max_area_error,'max_pair_shared_area_abs_error_mm2':pair_max_shared_error,'source_hashes_rechecked':len(pins['source_hashes']),'candidate':a['candidate'],'revision':a['revision_id']},sort_keys=True,indent=2))
