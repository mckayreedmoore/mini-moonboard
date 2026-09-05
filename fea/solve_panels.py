"""Current-panel bending screen with ideal fixed screw-head seating surfaces."""
import argparse
import hashlib
import json
import math
import re
import subprocess
from pathlib import Path

import gmsh
from joint_math import parse_joint_results
from panel_math import dot, head_nodes, minus


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--size",type=float,default=30)
    parser.add_argument("--panel",choices=("main_upper_left","kicker_left"))
    args=parser.parse_args()
    if not math.isfinite(args.size) or args.size<=0:
        parser.error("positive finite mesh size required")
    directory=Path("fea/generated")
    records=json.loads((directory/"panels.json").read_text())
    results=[]
    for record in records:
        name=record["name"]
        if args.panel and name!=args.panel:
            continue
        base=directory/f"panel_{name}_{args.size:g}".replace(".","p")
        gmsh.initialize()
        gmsh.option.setNumber("General.Verbosity",2)
        gmsh.model.add(name)
        volumes=gmsh.model.occ.importShapes(str(directory/f"panel_{name}.step"))
        # Imprint the actual T-nut flange outline on the back face so surface
        # quadrature has a bounded load patch instead of nearest-node loading.
        disks=[]
        for target in record["targets"]:
            r=target["patch_radius_mm"]
            disk=gmsh.model.occ.addDisk(0,0,0,r,r)
            angle=math.atan2(-record["normal"][1],record["normal"][2])
            gmsh.model.occ.rotate([(2,disk)],0,0,0,1,0,0,angle)
            gmsh.model.occ.translate([(2,disk)],*target["back_centre_mm"])
            disks.append((2,disk))
        gmsh.model.occ.fragment(volumes,disks)
        gmsh.model.occ.synchronize()
        volumes=gmsh.model.getEntities(3)
        gmsh.model.addPhysicalGroup(3,[t for _,t in volumes],1)
        gmsh.model.setPhysicalName(3,1,"PANEL")
        for key,value in {"Mesh.MeshSizeMax":args.size,"Mesh.MeshSizeMin":1,
                          "Mesh.MeshSizeExtendFromBoundary":0,"Mesh.MeshSizeFromCurvature":16,
                          "Mesh.ElementOrder":2}.items():
            gmsh.option.setNumber(key,value)
        gmsh.model.mesh.generate(3)
        gmsh.model.mesh.optimize("HighOrder")
        types,element_tags,element_nodes=gmsh.model.mesh.getElements(3)
        if set(types)!={11}:
            raise ValueError("Expected quadratic tetrahedra")
        elements={int(t) for tags in element_tags for t in tags}
        used={int(t) for tags in element_nodes for t in tags}
        quality=min(float(v) for tags in element_tags for v in gmsh.model.mesh.getElementQualities(tags,"minDetJac"))
        if quality<=0:
            raise ValueError("Inverted panel elements")
        gmsh.write(str(base.with_suffix(".inp")))
        tags,coords,_=gmsh.model.mesh.getNodes()
        nodes={int(t):tuple(float(v) for v in coords[i*3:i*3+3]) for i,t in enumerate(tags) if int(t) in used}
        heads={s["name"]:head_nodes(nodes,record,s) for s in record["screws"]}
        clamp=sorted({t for values in heads.values() for t in values})
        if len(clamp)!=sum(len(v) for v in heads.values()):
            raise ValueError("Overlapping screw-head constraints")
        patches=[{} for _ in record["targets"]]
        faces=gmsh.model.getBoundary(volumes,combined=True,oriented=False)
        for _,face in faces:
            kinds,_,conn=gmsh.model.mesh.getElements(2,face)
            for kind,flat in zip(kinds,conn,strict=True):
                if kind!=9:
                    raise ValueError("Expected quadratic surface triangles")
                for i in range(0,len(flat),6):
                    tri=[int(t) for t in flat[i:i+6]]
                    for j,target in enumerate(record["targets"]):
                        deltas=[minus(nodes[t],target["back_centre_mm"]) for t in tri]
                        if not all(abs(dot(d,record["normal"]))<1e-4 and math.sqrt(dot(d,d))<=target["patch_radius_mm"]+1e-4 for d in deltas):
                            continue
                        a,b,c=[nodes[t] for t in tri[:3]]
                        u,v=minus(b,a),minus(c,a)
                        area=math.sqrt(sum((u[k]*v[(k+1)%3]-u[(k+1)%3]*v[k])**2 for k in range(3)))/2
                        for t in tri[3:]:
                            patches[j][t]=patches[j].get(t,0)+area/3
        gmsh.finalize()
        deck=base.with_suffix(".inp").read_text()
        def nset(name,tags):
            return [f"*NSET,NSET={name}",*(", ".join(map(str,tags[i:i+16])) for i in range(0,len(tags),16))]
        for target,weights in zip(record["targets"],patches,strict=True):
            if not weights or set(weights)&set(clamp):
                raise ValueError("Missing load patch or direct constraint/load overlap")
            area=sum(weights.values())
            forces={t:tuple(-1200*w/area*n for n in record["normal"]) for t,w in weights.items()}
            applied=[sum(v[k] for v in forces.values()) for k in range(3)]
            moment=[sum(nodes[t][(k+1)%3]*v[(k+2)%3]-nodes[t][(k+2)%3]*v[(k+1)%3] for t,v in forces.items()) for k in range(3)]
            job=base.with_name(base.name+"_"+target["label"])
            lines=[deck,*nset("ALLN",list(nodes)),*nset("CLAMP",clamp),"*MATERIAL,NAME=ISOTROPIC_SCREEN","*ELASTIC","7000,0.3",
                   "*SOLID SECTION,ELSET=PANEL,MATERIAL=ISOTROPIC_SCREEN","*STEP","*STATIC","*BOUNDARY","CLAMP,1,3,0","*CLOAD"]
            lines += [f"{t},{k+1},{v:.12g}" for t,xyz in forces.items() for k,v in enumerate(xyz) if v]
            lines += ["*NODE PRINT,NSET=ALLN","U","*EL PRINT,ELSET=PANEL","S","*NODE PRINT,NSET=CLAMP,TOTALS=YES","RF","*NODE FILE","U","*EL FILE","S","*END STEP"]
            job.with_suffix(".inp").write_text("\n".join(lines)+"\n")
            run=subprocess.run(["ccx","-i",job.name],cwd=directory,capture_output=True,text=True,check=False)
            job.with_suffix(".log").write_text(run.stdout+run.stderr)
            if run.returncode or "*ERROR" in run.stdout.upper():
                raise RuntimeError(f"Failed panel solve: {job}")
            data=job.with_suffix(".dat").read_text()
            result=parse_joint_results(data,applied,nodes,moment,elements)
            block=re.search(r"forces[^\n]*\n(.*?)(?=\n\s*[A-Za-z]|\Z)",data,re.IGNORECASE|re.DOTALL)
            reactions={int(c[0]):[float(v) for v in c[1:]] for line in block[1].splitlines() if len(c:=line.split())==4 and c[0].isdigit()}
            grouped={key:[sum(reactions[t][k] for t in tags) for k in range(3)] for key,tags in heads.items()}
            result.update({"panel":name,"target":target["label"],"mesh_mm":args.size,"nodes":len(nodes),"min_jacobian":quality,
                           "screw_count":len(heads),"head_reactions_n":grouped,"load_patch_area_mm2":area,
                           "applied_force_n":applied,"applied_moment_nmm":moment,"geometry_commit":record["geometry_commit"],
                           "evidence_sha256":{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in (job.with_suffix(".inp"),job.with_suffix(".dat"))}})
            results.append(result)
            job.with_suffix(".json").write_text(json.dumps(result,indent=2)+"\n")
            print(json.dumps(result),flush=True)
    output=directory/f"panel_results_{args.panel or 'all'}_{args.size:g}".replace(".","p")
    output.with_suffix(".json").write_text(json.dumps(results,indent=2)+"\n")


if __name__=="__main__":
    main()
