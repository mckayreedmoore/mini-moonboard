"""Independent 26-body curved C3D10 mesh; no contact law or joint solve."""
import argparse
import hashlib
import json
import math
import os
import subprocess
from pathlib import Path

from fea.stitch_joint_mesh import (
    GMSH_TO_CCX,
    append_body,
    external_faces,
    surface_faces,
    validate_ownership,
)

LIMITS = "Mesh and interface inventory only; unverified hardware hypotheses, no joint solve or strength acceptance."
WORKER_SOURCES = ("fea/compact_joint_mesh.py", "fea/stitch_joint_mesh.py", "fea/floor_contact.py")


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def geometry(directory):
    directory = Path(directory)
    info = json.loads((directory/"geometry.json").read_text())
    if info["variant"] not in ("smooth", "root-reference") or info["body_count"] != 26:
        raise ValueError("Require the complete contact geometry hypothesis")
    expected = set(info["wood_members"]) | {n for c in info["connections"] for n in c["hardware_bodies"]}
    if len(expected) != 26 or set(info["bodies"]) != expected or set(info["step_sha256"]) != {n+".step" for n in expected}:
        raise ValueError("Body/STEP ownership differs")
    if len(info["planar_adjacencies"]) != 25 or len({frozenset(p["bodies"]) for p in info["planar_adjacencies"]}) != 25:
        raise ValueError("Require 25 unique planar interfaces")
    for name, sha in info["step_sha256"].items():
        if digest(directory/name) != sha:
            raise ValueError("Frozen STEP changed")
    for name, sha in info["source_sha256"].items():
        if digest(directory/"launch_sources"/name) != sha:
            raise ValueError("Frozen geometry source snapshot changed")
    return info


def settings(wood, local, washer):
    if any(isinstance(v, bool) or not math.isfinite(v) or v <= 0 for v in (wood,local,washer)):
        raise ValueError("Require positive finite mesh sizes")
    if not washer <= local <= wood:
        raise ValueError("Require washer <= local <= wood mesh size")
    return {"wood_mm":wood,"local_mm":local,"washer_mm":washer}


def partition_bolt(gmsh, volume, connection):
    """Fragment this bolt only; preserve integral volume across internal planes."""
    start, axis = connection["start_xyz_mm"], connection["axis_xyz"]
    cuts = connection["planned_tied_engagement"]["underhead_interval_mm"]
    tools = []
    for s in cuts:
        x = start[0]+axis[0]*s
        # A bounded transverse disk spans the complete shaft at this station.
        surface = gmsh.model.occ.addDisk(0,0,0,20,20)
        gmsh.model.occ.rotate([(2,surface)],0,0,0,0,1,0,math.pi/2)
        gmsh.model.occ.translate([(2,surface)],x,start[1],start[2])
        tools.append((2,surface))
    out, _ = gmsh.model.occ.fragment([volume],tools)
    volumes = [p for p in out if p[0] == 3]
    gmsh.model.occ.synchronize()
    if len(volumes) != 3:
        raise ValueError("Nut engagement planes did not partition one bolt into three volumes")
    return volumes


def cad_surfaces(gmsh, volumes):
    # Combined boundary removes internal fragmentation faces within a bolt.
    boundary = gmsh.model.getBoundary(volumes,combined=True,oriented=False)
    result = {}
    for dim,tag in boundary:
        if dim != 2:
            raise ValueError("Expected exterior surfaces")
        low,high = gmsh.model.getParametrizationBounds(2,tag)
        uv = [(float(a)+float(b))/2 for a,b in zip(low,high,strict=True)]
        result[tag] = {"cad_type":gmsh.model.getType(2,tag),
            "bounds_mm":list(gmsh.model.getBoundingBox(2,tag)),
            "area_mm2":gmsh.model.occ.getMass(2,tag),
            "sample_xyz_mm":list(gmsh.model.getValue(2,tag,uv))}
    return result


def cylinder_surfaces(surfaces, connection, radius, interval=None):
    start,axis = connection["start_xyz_mm"],connection["axis_xyz"]
    result = []
    for tag,s in surfaces.items():
        if s["cad_type"] != "Cylinder":
            continue
        p = s["sample_xyz_mm"]
        if abs(math.hypot(p[1]-start[1],p[2]-start[2])-radius) > 1e-5:
            continue
        b = s["bounds_mm"]
        a,z = sorted(((b[0]-start[0])*axis[0],(b[3]-start[0])*axis[0]))
        if interval is not None and (abs(a-interval[0]) > 1e-5 or abs(z-interval[1]) > 1e-5):
            continue
        result.append(tag)
    if not result:
        raise ValueError("Missing exact cylindrical patch")
    return result


def engagement(surfaces, connection):
    spec = connection["planned_tied_engagement"]
    tags = cylinder_surfaces(surfaces,connection,spec["diameter_mm"]/2,spec["underhead_interval_mm"])
    expected = math.pi*spec["diameter_mm"]*(spec["underhead_interval_mm"][1]-spec["underhead_interval_mm"][0])
    if abs(sum(surfaces[t]["area_mm2"] for t in tags)/expected-1) > 1e-7:
        raise ValueError("Engagement patch area differs from complete cylindrical interval")
    return tags


def worker(directory, output, configuration, preflight=False):
    import gmsh

    directory,output = Path(directory),Path(output)
    info = geometry(directory)
    initial_hash = digest(directory/"geometry.json")
    all_nodes,all_elements,bodies = {},{},{ }
    by_bolt = {c["hardware_bodies"][0]:c for c in info["connections"]}
    record = {"limits":LIMITS,"qualified_for_design":False,"solved":False,"status":"PREPARING",
        "geometry_sha256":initial_hash,"geometry":info,"configuration":configuration,
        "body_count":26,"partition_preflight":preflight}
    gmsh.initialize()
    try:
        gmsh.option.setNumber("General.NumThreads",1)
        gmsh.option.setNumber("General.Verbosity",2)
        for name in sorted(info["bodies"]):
            if preflight and name not in by_bolt:
                continue
            gmsh.model.add(name)
            imported = gmsh.model.occ.importShapes(str(directory/(name+".step")))
            gmsh.model.occ.synchronize()
            if len(imported) != 1 or imported[0][0] != 3:
                raise ValueError("One separate body per Gmsh model required")
            volumes = partition_bolt(gmsh,imported[0],by_bolt[name]) if name in by_bolt else imported
            cad_volume = sum(gmsh.model.occ.getMass(*v) for v in volumes)
            if abs(cad_volume/info["bodies"][name]["volume_mm3"]-1) > 1e-7:
                raise ValueError("Partition/import changed body volume")
            surfaces = cad_surfaces(gmsh,volumes)
            tie_tags = engagement(surfaces,by_bolt[name]) if name in by_bolt else []
            if preflight:
                bodies[name] = {"volume_mm3":cad_volume,"engagement_surfaces":tie_tags,"surfaces":surfaces}
                gmsh.model.remove()
                continue
            target = configuration["wood_mm"] if name in info["wood_members"] else (
                configuration["washer_mm"] if "washer" in name else configuration["local_mm"])
            for option,value in {"Mesh.MeshSizeMax":target,"Mesh.MeshSizeMin":configuration["washer_mm"],
                "Mesh.MeshSizeFromCurvature":32,"Mesh.MeshSizeExtendFromBoundary":0,"Mesh.ElementOrder":2,
                "Mesh.SecondOrderLinear":0}.items():
                gmsh.option.setNumber(option,value)
            if name in info["wood_members"]:
                local_surfaces = [tag for tag,s in surfaces.items() if s["cad_type"] == "Cylinder"]
                field = gmsh.model.mesh.field.add("Distance")
                gmsh.model.mesh.field.setNumbers(field,"FacesList",local_surfaces)
                threshold = gmsh.model.mesh.field.add("Threshold")
                for key,value in {"InField":field,"SizeMin":configuration["local_mm"],"SizeMax":target,
                                  "DistMin":3.,"DistMax":20.}.items():
                    gmsh.model.mesh.field.setNumber(threshold,key,value)
                gmsh.model.mesh.field.setAsBackgroundMesh(threshold)
            gmsh.model.mesh.generate(3)
            gmsh.model.mesh.optimize("HighOrder")
            kinds,tags,connectivity = gmsh.model.mesh.getElements(3)
            if list(kinds) != [11]:
                raise ValueError("Require C3D10 only")
            elements = {int(e):tuple(int(connectivity[0][10*i+j]) for j in GMSH_TO_CCX) for i,e in enumerate(tags[0])}
            used = {n for row in elements.values() for n in row}
            nt,xyz,_ = gmsh.model.mesh.getNodes()
            nodes = {int(n):tuple(float(v) for v in xyz[3*i:3*i+3]) for i,n in enumerate(nt) if int(n) in used}
            exterior = external_faces(elements)
            minimum = min(float(v) for v in gmsh.model.mesh.getElementQualities(tags[0],"minDetJac"))
            ip,weights = gmsh.model.mesh.getIntegrationPoints(11,"Gauss5")
            terms,first_moments,jacobians = [],[[],[],[]],[]
            for _,v in volumes:
                _,dets,coords = gmsh.model.mesh.getJacobians(11,ip,v)
                for i,det in enumerate(dets):
                    dv = float(det)*float(weights[i%len(weights)])
                    jacobians.append(float(det)); terms.append(dv)
                    for axis in range(3):
                        first_moments[axis].append(dv*float(coords[3*i+axis]))
            volume = math.fsum(terms)
            centre = [math.fsum(v)/volume for v in first_moments]
            if not math.isfinite(minimum) or minimum <= 0 or any(not math.isfinite(d) or d <= 0 for d in jacobians):
                raise ValueError("Nonpositive curved quadratic Jacobian")
            if abs(volume/cad_volume-1) > .001 or math.dist(centre,info["bodies"][name]["centroid_xyz_mm"]) > .05:
                raise ValueError("Integrated mesh volume/centroid differs from CAD")
            nm,em = append_body(all_nodes,all_elements,nodes,elements)
            covered = set()
            for tag,s in surfaces.items():
                kinds,_,flat = gmsh.model.mesh.getElements(2,tag)
                if list(kinds) != [9]:
                    raise ValueError("Require quadratic exterior triangles")
                selected = surface_faces([tuple(map(int,flat[0][i:i+6])) for i in range(0,len(flat[0]),6)],exterior)
                keys = {tuple(v) for v in selected["faces"]}
                if keys & covered:
                    raise ValueError("Repeated exterior face")
                covered.update(keys)
                s.update(faces=[[em[e],f] for e,f in selected["faces"]],nodes=[nm[n] for n in selected["nodes"]])
            if covered != {(e,f) for e,f,_ in exterior.values()}:
                raise ValueError("Incomplete exterior surface ownership")
            bodies[name] = {"nodes":sorted(nm.values()),"elements":sorted(em.values()),"surfaces":surfaces,
                "engagement_surfaces":tie_tags,"mesh_volume_mm3":volume,"mesh_centroid_mm":centre,
                "cad_volume_mm3":cad_volume,"min_sampled_jacobian":minimum,"min_integration_jacobian":min(jacobians)}
            print(name,len(elements),flush=True)
            gmsh.model.remove()
        record["gmsh_version"] = gmsh.__version__
    except Exception as error:
        record.update(status="FAILED MESH PREPARATION",error=f"{type(error).__name__}: {error}",bodies=bodies)
        (output/"mesh.json").write_text(json.dumps(record,allow_nan=False)+"\n")
        raise
    finally:
        gmsh.finalize()
    if digest(directory/"geometry.json") != initial_hash or geometry(directory) != info:
        raise ValueError("Frozen geometry changed during worker")
    record["bodies"] = bodies
    if not preflight:
        validate_ownership(all_nodes,all_elements,bodies)
        record["interfaces"] = interface_inventory(info,bodies,all_nodes)
        lines = ["*HEADING",LIMITS,"*NODE"]+[f"{n},"+",".join(map(repr,p)) for n,p in all_nodes.items()]
        for name,body in bodies.items():
            lines += [f"*ELEMENT,TYPE=C3D10,ELSET={name.upper()}"]
            lines += [f"{e},"+",".join(map(str,all_elements[e])) for e in body["elements"]]
        (output/"mesh.inp").write_text("\n".join(lines)+"\n")
        record.update(mesh_sha256=digest(output/"mesh.inp"),node_count=len(all_nodes),element_count=len(all_elements))
    record["status"] = "VERIFIED PARTITION ONLY" if preflight else "VERIFIED MESH ONLY; NO SOLVER"
    (output/"mesh.json").write_text(json.dumps(record,allow_nan=False)+"\n")
    return record


def interface_inventory(info,bodies,nodes):
    planar,bores,ties = [],[],[]
    for pair in info["planar_adjacencies"]:
        x = pair["source_faces"][0]["centroid_xyz_mm"][0]
        selected = []
        for name in pair["bodies"]:
            tags = [tag for tag,s in bodies[name]["surfaces"].items()
                    if abs(s["bounds_mm"][0]-x) < 1e-5 and abs(s["bounds_mm"][3]-x) < 1e-5]
            if not tags:
                raise ValueError("Missing mapped planar interface")
            selected.append({"body":name,"surface_tags":tags})
        planar.append({"members":selected,"kind":"contact candidate; no law applied"})
    for c in info["connections"]:
        bolt,nut = c["planned_tied_engagement"]["bodies"]
        bolt_tags = bodies[bolt]["engagement_surfaces"]
        nut_tags = engagement(bodies[nut]["surfaces"],c)
        interval = c["planned_tied_engagement"]["underhead_interval_mm"]
        for name,tags in ((bolt,bolt_tags),(nut,nut_tags)):
            for tag in tags:
                for n in bodies[name]["surfaces"][tag]["nodes"]:
                    s = (nodes[n][0]-c["start_xyz_mm"][0])*c["axis_xyz"][0]
                    if not interval[0]-1e-5 <= s <= interval[1]+1e-5:
                        raise ValueError("Engagement mesh triangle straddles prescribed patch")
        ties.append({"members":[{"body":bolt,"surface_tags":bolt_tags},{"body":nut,"surface_tags":nut_tags}],
                     "underhead_interval_mm":interval,"kind":"planned tie; not applied"})
        shaft_tags = cylinder_surfaces(bodies[bolt]["surfaces"],c,c["body_diameter_mm"]/2)
        if c["distal_diameter_mm"] != c["body_diameter_mm"]:
            shaft_tags += cylinder_surfaces(bodies[bolt]["surfaces"],c,c["distal_diameter_mm"]/2)
        shaft_tags = sorted(set(shaft_tags)-set(bolt_tags))
        for wood in c["members"]:
            tags = cylinder_surfaces(bodies[wood]["surfaces"],c,c["wood_bore_diameter_mm"]/2)
            bores.append({"members":[{"body":bolt,"surface_tags":shaft_tags},{"body":wood,"surface_tags":tags}],
                          "kind":"shaft/bore contact candidate; no law applied"})
    if (len(planar),len(bores),len(ties)) != (25,8,4):
        raise ValueError("Incomplete contact/tie inventory")
    return {"planar_contacts":planar,"shaft_bore_contacts":bores,"planned_nut_ties":ties}


def run(directory,output,wood=40.,local=2.,washer=.9,preflight=False):
    from fea.prescribed_tet_control import IMAGE

    configuration = settings(wood,local,washer)
    geometry(directory)
    directory,output = Path(directory).resolve(),Path(output).resolve()
    output.mkdir(parents=True,exist_ok=False)
    sources = {}
    for name in (*WORKER_SOURCES,"fea/prescribed_tet_control.py"):
        data = Path(name).read_bytes()
        sources[name] = hashlib.sha256(data).hexdigest()
        target = output/"launch_sources"/name
        target.parent.mkdir(parents=True,exist_ok=True)
        target.write_bytes(data)
    command = ["docker","run","--rm","--network=none","--cpus=1","--memory=4g","--read-only",
        "--tmpfs","/tmp:rw,noexec,nosuid,size=64m","--user",f"{os.getuid()}:{os.getgid()}",
        "-e","OMP_NUM_THREADS=1","-e","PYTHONPATH=/work/launch_sources",
        "-v",f"{directory}:/geometry:ro","-v",f"{output}:/work","-w","/work",IMAGE,
        "timeout","--signal=TERM","--kill-after=10s","300s","python3","-m","fea.compact_joint_mesh",
        "--worker","--geometry","/geometry","--output","/work","--wood",str(wood),"--local",str(local),"--washer",str(washer)]
    if preflight:
        command.append("--preflight")
    launch = {"image":IMAGE,"command":command,"source_sha256":sources,"configuration":configuration,"qualified_for_design":False}
    (output/"launch.json").write_text(json.dumps(launch,indent=2)+"\n")
    with (output/"mesh.log").open("w") as log:
        done = subprocess.run(command,stdout=log,stderr=subprocess.STDOUT,timeout=330,check=False)
    launch["returncode"] = done.returncode
    (output/"launch.json").write_text(json.dumps(launch,indent=2)+"\n")
    if done.returncode:
        raise RuntimeError(f"Mesh worker failed; preserved output at {output}")
    if any(digest(p) != sha or digest(output/"launch_sources"/p) != sha for p,sha in sources.items()):
        raise ValueError("Worker source changed during meshing")
    return output


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--geometry",type=Path,required=True)
    parser.add_argument("--output",type=Path,required=True)
    parser.add_argument("--wood",type=float,default=40.)
    parser.add_argument("--local",type=float,default=2.)
    parser.add_argument("--washer",type=float,default=.9)
    parser.add_argument("--preflight",action="store_true")
    parser.add_argument("--worker",action="store_true")
    args = parser.parse_args()
    if args.worker:
        worker(args.geometry,args.output,settings(args.wood,args.local,args.washer),args.preflight)
    else:
        print(run(args.geometry,args.output,args.wood,args.local,args.washer,args.preflight))
