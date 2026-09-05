"""Mesh and solve bulk CAD in the FEA Docker image (Gmsh + CalculiX)."""
import argparse
import hashlib
import json
import math
import subprocess
from pathlib import Path

import gmsh
from box_results import parse_results


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--size",type=float,default=100)
    parser.add_argument("--modulus",type=float,default=7000)
    parser.add_argument("--audited",action="store_true",help="Use audited row-12 targets and classified load cases")
    parser.add_argument("--candidate",choices=("2x10","2x12"),help="Separate hybrid timber-only bonded screen")
    args=parser.parse_args()
    if not all(math.isfinite(v) and v>0 for v in (args.size,args.modulus)):
        parser.error("size and modulus must be positive finite numbers")
    if args.candidate and not args.audited:
        parser.error("Hybrid comparisons require --audited load cases")
    directory=Path("fea/generated")
    if args.candidate:
        directory=directory/"hybrid"/args.candidate
    prefix=directory/f"box_{'audited_' if args.audited else ''}{args.size:g}_{args.modulus:g}".replace(".","p")
    info=json.loads((directory/"box_frame_bulk.json").read_text())
    if args.candidate and hashlib.sha256((directory/"box_frame_bulk.step").read_bytes()).hexdigest()!=info["step_sha256"]:
        raise ValueError("Hybrid STEP differs from frozen metadata")
    gmsh.initialize()
    gmsh.option.setNumber("General.Verbosity",2)
    gmsh.model.add("ideal_bonded_box")
    shapes=gmsh.model.occ.importShapes(str(directory/"box_frame_bulk.step"))
    gmsh.model.occ.fragment(shapes[:1],shapes[1:])
    gmsh.model.occ.synchronize()
    volumes=[tag for dim,tag in gmsh.model.getEntities(3)]
    gmsh.model.addPhysicalGroup(3,volumes,1)
    gmsh.model.setPhysicalName(3,1,"TIMBER")
    gmsh.option.setNumber("Mesh.MeshSizeMax",args.size)
    gmsh.option.setNumber("Mesh.MeshSizeMin",args.size/5)
    gmsh.option.setNumber("Mesh.MeshSizeFromCurvature",0)
    gmsh.option.setNumber("Mesh.ElementOrder",2)
    gmsh.model.mesh.generate(3)
    gmsh.model.mesh.optimize("HighOrder")
    min_jacobian=min(float(v) for tags3 in gmsh.model.mesh.getElements(3)[1] for v in gmsh.model.mesh.getElementQualities(tags3,"minDetJac"))
    if min_jacobian<=0:
        raise RuntimeError("Inverted bulk mesh")
    gmsh.write(str(prefix.with_suffix(".inp")))
    tags,coords,_=gmsh.model.mesh.getNodes()
    nodes={int(tag):tuple(float(v) for v in coords[i*3:i*3+3]) for i,tag in enumerate(tags)}
    feet=[tag for tag,xyz in nodes.items() if abs(xyz[2])<1e-5]
    targets=info["audited_load_targets_mm" if args.audited else "load_targets_mm"]
    top=sorted({min(nodes,key=lambda tag:math.dist(nodes[tag],target)) for target in targets})
    gmsh.finalize()
    deck=prefix.with_suffix(".inp").read_text()
    # Gmsh writes Abaqus node ordering for C3D10 directly; let the exporter
    # own that mapping. Keep only volume elements in the physical group.
    if "C3D10" not in deck.upper():
        raise RuntimeError("Expected quadratic tetrahedra in Abaqus export")
    if not feet or len(top)!=5:
        raise RuntimeError("Missing floor or distinct top load nodes")
    def node_set(name,values):
        return [f"*NSET,NSET={name}",*(", ".join(map(str,values[i:i+16])) for i in range(0,len(values),16))]
    lines=["** IDEAL BONDED BULK BOX SCREEN. NOT JOINT OR UNANCHORED VALIDATION.",deck,
           *node_set("FEET",feet),*node_set("TOP",top),*node_set("ALLN",list(nodes)),
           "*MATERIAL,NAME=PLYWOOD_SCREEN","*ELASTIC",f"{args.modulus},0.3",
           "*SOLID SECTION,ELSET=TIMBER,MATERIAL=PLYWOOD_SCREEN"]
    cases=[("normal_support",(0,-.7660444431,.6427876097)),("normal_climbing",(0,.7660444431,-.6427876097)),("down_board",(0,-.6427876097,-.7660444431)),("lateral",(1,0,0)),("combined",(.4,.7660444431,-.6427876097))]
    if args.audited:
        cases=[(c["name"],tuple(v/1200 for v in c["force_n"])) for c in info["audited_cases"]]
    for name,force in cases:
        lines += [f"** CASE {name}","*STEP","*STATIC","*BOUNDARY","FEET,1,3,0","*CLOAD,OP=NEW"]
        for node in top:
            lines += [f"{node},{dof},{1200*value/len(top):.9f}" for dof,value in enumerate(force,1) if value]
        lines += ["*NODE PRINT,NSET=TOP","U",f"*NODE PRINT,NSET=FEET,TOTALS={'YES' if args.candidate else 'ONLY'}","RF","*NODE FILE","U","*END STEP"]
    prefix.with_suffix(".inp").write_text("\n".join(lines)+"\n")
    result=subprocess.run(["ccx","-i",prefix.name],cwd=directory,capture_output=True,text=True,check=False)
    prefix.with_suffix(".log").write_text(result.stdout+result.stderr)
    if result.returncode or "*ERROR" in result.stdout.upper():
        raise RuntimeError(f"CalculiX failed; see {prefix}.log")
    data=prefix.with_suffix(".dat").read_text()
    maxima,reactions=parse_results(data,cases)
    summary={"mesh_size_mm":args.size,"modulus_mpa":args.modulus,"nodes":len(nodes),"floor_nodes":len(feet),"load_nodes":top,
             "min_jacobian":min_jacobian,"geometry_commit":info["geometry_commit"],
             "load_target_distances_mm":[min(math.dist(nodes[tag],target) for tag in top) for target in targets],
             "load_basis":info["audited_cases"] if args.audited else "historical top-edge vectors",
             "assumptions":info["assumptions"].replace("E=7000MPa",f"E={args.modulus:g}MPa"),"max_top_displacement_mm":maxima,"reaction_totals_n":reactions}
    summary["evidence_sha256"]={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in (prefix.with_suffix(".inp"),prefix.with_suffix(".dat"))}
    if args.candidate:
        from hybrid_results import support_moments
        summary["reaction_moment_nmm"]=support_moments(data,nodes,feet,top,cases)
        summary["candidate"]=args.candidate
        summary["frozen_geometry"]=info
    prefix.with_suffix(".json").write_text(json.dumps(summary,indent=2)+"\n")
    print(json.dumps(summary,indent=2))


if __name__=="__main__":
    main()
