#!/usr/bin/env python3
"""Read-only exact ray/solid query for frozen ordinary-joint wood STEP bodies."""
import hashlib, json, math
from pathlib import Path
import cadquery as cq
from OCP.BRepIntCurveSurface import BRepIntCurveSurface_Inter
from OCP.gce import gce_MakeLin
from OCP.gp import gp_Dir, gp_Pnt
from mini_moonboard.connection_geometry import material_intervals

ROOT = Path.cwd()
REL = Path("docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/ordinary-patch-inputs-attempt01")
INV, HASHES = ROOT/REL/"inventory.json", ROOT/REL/"sha256.json"
HELPER = ROOT/"mini_moonboard/connection_geometry.py"
EXPECTED_HELPER_SHA = "f729bc64e7ea7fb9df9308411df07e02f98fc309efcf26038809a9e7bd4bc4a4"
TOL, FACE_TOL, MATCH_TOL, AXIAL_INSET = 1e-7, 2e-4, 2e-4, 0.01

def unit(v):
    n = math.sqrt(sum(x*x for x in v))
    if not n: raise ValueError("zero vector")
    return tuple(x/n for x in v)

def dot(a,b): return sum(x*y for x,y in zip(a,b))
def cross(a,b): return (a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0])
def add(p,a,s): return tuple(p[i]+a[i]*s for i in range(3))
def clean(x):
    if isinstance(x,float): return round(x,9)
    if isinstance(x,(tuple,list)): return [clean(v) for v in x]
    if isinstance(x,dict): return {k:clean(v) for k,v in x.items()}
    return x

def bbox_ray_limit(shape, origin, direction):
    b=shape.BoundingBox()
    cs=[(x,y,z) for x in (b.xmin,b.xmax) for y in (b.ymin,b.ymax) for z in (b.zmin,b.zmax)]
    return max(dot(tuple(c[i]-origin[i] for i in range(3)),direction) for c in cs)+5.0

def finite_face_hits(shape, origin, direction, limit):
    # OCC reports intersections with the actual trimmed faces of this solid.
    line=gce_MakeLin(gp_Pnt(*origin),gp_Dir(*direction)).Value()
    it=BRepIntCurveSurface_Inter(); it.Init(shape.wrapped,line,FACE_TOL)
    faces=shape.Faces(); hits=[]
    while it.More():
        p=it.Pnt(); xyz=(p.X(),p.Y(),p.Z())
        t=dot(tuple(xyz[i]-origin[i] for i in range(3)),direction)
        if -MATCH_TOL <= t <= limit+MATCH_TOL:
            raw=it.Face(); idx=next((i for i,f in enumerate(faces,1) if f.wrapped.IsSame(raw)),None)
            row={"t_mm":t,"point_global_xyz_mm":xyz,"face_index_1based":idx}
            if idx is not None:
                f=faces[idx-1]; row.update(surface_type=f.geomType(),face_area_mm2=f.Area(),face_center_global_xyz_mm=f.Center().toTuple())
                try:
                    n=f.normalAt(cq.Vector(*xyz)).toTuple()
                    row.update(normal_at_hit_global_xyz=n,abs_normal_dot_ray=abs(dot(n,direction)))
                except Exception as e: row["normal_error"]=type(e).__name__
            hits.append(row)
        it.Next()
    return sorted(hits,key=lambda h:h["t_mm"])

hashes=json.loads(HASHES.read_text())
actual_inv=hashlib.sha256(INV.read_bytes()).hexdigest()
if actual_inv != hashes["inventory.json"]: raise RuntimeError("inventory.json hash does not match its pin")
actual_helper=hashlib.sha256(HELPER.read_bytes()).hexdigest()
if actual_helper != EXPECTED_HELPER_SHA: raise RuntimeError("connection_geometry.py hash changed; review method before query")
inv=json.loads(INV.read_text()); bodies={x["part_id"]:x for x in inv["wood_bodies"]}; shapes={}
for mid,b in bodies.items():
    key=b["step_artifact_key"]; path=ROOT/REL/key
    if hashlib.sha256(path.read_bytes()).hexdigest()!=hashes[key]: raise RuntimeError(f"STEP hash mismatch: {key}")
    s=cq.importers.importStep(str(path)).val()
    if not s.isValid() or len(s.Solids())!=1: raise RuntimeError(f"invalid/non-single-solid STEP: {mid}")
    shapes[mid]=s

rays=[]
for bolt in inv["physical_bolts"]:
    bid=bolt["physical_bolt_id"]; datum=tuple(bolt["axis_origin_global_xyz_mm"]); a=unit(tuple(bolt["axis_direction_head_to_nut_global_xyz"]))
    for mid in bolt["receivers_head_to_nut"]:
        b=bodies[mid]; g=unit(tuple(b["grain"]["grain_axis_global_xyz"]))
        if abs(dot(g,a))>1e-6: raise RuntimeError(f"grain/bolt axes not orthogonal: {bid}/{mid}")
        e=unit(cross(g,a)); recv=next(r for r in bolt["raw_receiver_projected_intervals"] if r["member_id"]==mid)
        axial_intervals=recv["projected_intervals_from_underhead_datum_mm"]
        if not axial_intervals: raise RuntimeError(f"no pinned receiver axial interval: {bid}/{mid}")
        for ii,(lo,hi) in enumerate(axial_intervals,1):
            if hi-lo<=2*AXIAL_INSET: raise RuntimeError(f"receiver too thin for entry/mid/exit probes: {bid}/{mid}")
            stations=(("near_headward",lo+AXIAL_INSET),("mid_depth",(lo+hi)/2),("near_nutward",hi-AXIAL_INSET))
            for station_name,axial_t in stations:
                origin=add(datum,a,axial_t)
                for label,basis in (("g",g),("e",e)):
                    for sign,suffix in ((-1.,"-"),(1.,"+")):
                        direction=tuple(sign*x for x in basis); limit=bbox_ray_limit(shapes[mid],origin,direction)
                        intervals=material_intervals(shapes[mid],origin,direction,0.,limit,tolerance=TOL)
                        hits=finite_face_hits(shapes[mid],origin,direction,limit)
                        gaps=[]; last=0.
                        for start,end in intervals:
                            if start>last+MATCH_TOL: gaps.append([last,start])
                            last=end
                        terminal=intervals[-1][1] if intervals else None
                        terminal_faces=[h for h in hits if abs(h["t_mm"]-terminal)<=MATCH_TOL] if terminal is not None else []
                        rays.append({"bolt_id":bid,"member_id":mid,"receiver_interval_index":ii,
                            "receiver_axis_interval_from_head_datum_mm":[lo,hi],"axial_station_label":station_name,
                            "axial_station_from_head_datum_mm":axial_t,"ray_origin_global_xyz_mm":origin,
                            "grain_axis_global_xyz":g,"bolt_axis_global_xyz":a,"e_axis_global_xyz":e,
                            "ray_label":label+suffix,"ray_direction_global_xyz":direction,
                            "center_to_last_material_exit_mm":terminal,
                            "initial_and_intermediate_void_intervals_mm":gaps,"material_intervals_mm":intervals,
                            "exact_finite_face_hits":hits,"terminal_face_candidates":terminal_faces,
                            "terminal_face_match_count":len(terminal_faces),"query_limit_mm":limit})

out={"query":"read-only OCC intersection of frozen finished STEP; no CAD rebuild/native solve",
 "inventory_sha256_verified":actual_inv,"helper_sha256_verified":actual_helper,
 "step_sha256_verified":{b["step_artifact_key"]:hashes[b["step_artifact_key"]] for b in inv["wood_bodies"]},
 "tolerances_mm":{"solid_intervals":TOL,"trimmed_face_intersection":FACE_TOL,"interval_face_matching":MATCH_TOL,"near_end_axial_inset":AXIAL_INSET},
 "station_method":"for every raw receiver projected bolt-axis interval, query 0.01 mm inward of each end and at its midpoint; discrete stations do not prove continuous through-thickness extrema",
 "direction_method":"g is declared grain axis; e=unit(g cross bolt head-to-nut axis); query g-/g+/e-/e+ in each plane perpendicular to the bolt axis",
 "claim_boundary":"geometry only; intervals preserve bores/cuts; face candidates require exterior-profile identification; no NDS capacity, force, inspection, or acceptance",
 "rays":rays}
print(json.dumps(clean(out),indent=2,sort_keys=True))
