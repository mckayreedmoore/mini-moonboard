"""C10 comparison with unilateral axial head springs and compression backing."""
import argparse
import hashlib
import json
import math
import re
import subprocess
from pathlib import Path


def final_block(data,title):
    matches=list(re.finditer(r"^\s*"+title+r"[^\n]*\n(.*?)(?=\n\s*[A-Za-z]|\Z)",data,re.MULTILINE|re.IGNORECASE|re.DOTALL))
    time=re.search(r"time\s+([-+\d.E]+)",matches[-1][0],re.IGNORECASE) if matches else None
    if time is None or not math.isclose(float(time[1]),1.,abs_tol=1e-9):
        raise ValueError(f"Missing final-time {title}")
    return matches[-1][0]


def seat_stiffness(weights,total):
    if not weights or not math.isfinite(total) or total<=0 or any(not math.isfinite(w) or w<=0 for w in weights.values()):
        raise ValueError("Positive finite seating weights and stiffness required")
    area=sum(weights.values())
    return {int(t):total*w/area for t,w in weights.items()}


def main():
    from joint_math import parse_joint_results

    parser=argparse.ArgumentParser()
    parser.add_argument("--size",type=int,choices=(20,15),default=20)
    parser.add_argument("--variant",choices=("baseline","stiffer_attachment","closer_backing"),default="baseline")
    parser.add_argument("--stiffness",type=float,default=1000,help="assumed total axial N/mm per head")
    parser.add_argument("--penalty",type=float,default=100,help="backing N/mm^3, numerical penalty")
    parser.add_argument("--modulus",type=float,default=7000)
    parser.add_argument("--contact-gap",type=float,default=0,help="initial backing clearance in mm")
    parser.add_argument("--tight",action="store_true",help="stricter nonlinear residual and correction tolerances")
    parser.add_argument("--push",action="store_true")
    parser.add_argument("--reparse",action="store_true",help="validate existing evidence without rerunning solver")
    args=parser.parse_args()
    if not all(math.isfinite(v) and v>0 for v in (args.stiffness,args.penalty,args.modulus)):
        parser.error("positive finite properties required")
    if not math.isfinite(args.contact_gap) or not 0<=args.contact_gap<1:
        parser.error("contact gap must be finite and between 0 and 1 mm")
    directory=Path("fea/generated/connection")
    meta_path=directory/f"mesh_{args.size}.json"
    meta=json.loads(meta_path.read_text())
    mesh_path=directory/f"mesh_{args.size}.inp"
    mesh=mesh_path.read_text()
    if hashlib.sha256(mesh_path.read_bytes()).hexdigest()!=meta["source_sha256"][mesh_path.name]:
        raise ValueError("Mesh changed since freeze")
    nodes={}
    elements=set()
    section=""
    for line in mesh.splitlines():
        if line.startswith("*"):
            section=line.upper()
        elif line.strip() and section=="*NODE":
            cells=line.split(",")
            nodes[int(cells[0])]=tuple(map(float,cells[1:]))
        elif line.strip() and section.startswith("*ELEMENT"):
            elements.add(int(line.split(",")[0]))
    original=set(nodes)
    all_heads={int(t) for weights in meta["heads"].values() for t in weights}
    # Three in-plane constraints remove rigid-body X/Y translation and Z
    # rotation. No panel-normal displacement or rotation is prescribed.
    pin=min(all_heads,key=lambda t:nodes[t][:2])
    pin2=max(all_heads,key=lambda t:nodes[t][0])
    stiffness=args.stiffness*(2 if args.variant=="stiffer_attachment" else 1)
    springs=[]
    for name,weights in meta["heads"].items():
        springs += [(t,k,"head",name) for t,k in seat_stiffness(weights,stiffness).items()]
    patches=meta["backing"]["closer_backing" if args.variant=="closer_backing" else "baseline"]
    springs += [(int(t),args.penalty*w,"back","backing") for t,w in patches.items()]
    lines=[mesh]
    next_node=max(nodes)+1
    next_element=max(elements)+1
    supports=[]
    for i,(tag,k,kind,name) in enumerate(springs):
        anchor=next_node+i
        x,y,z=nodes[tag]
        nodes[anchor]=(x,y,z+10000)
        supports.append(anchor)
        # A 1e-9 mm transition gives a defined initial tangent at zero.
        # Its bounded wrong-sign force is checked and reported below.
        curve=[(-100.,-k*1e-9),(-1e-9,-k*1e-9),(0.,0.),(100.,100*k)] if kind=="head" else [(-100.,-100*k),(0.,0.),(1e-9,k*1e-9),(100.,k*1e-9)]
        if kind=="back" and args.contact_gap:
            curve=[(-100.,k*(-100+args.contact_gap)),(-args.contact_gap,0.),(0.,0.),(100.,0.)]
        lines += ["*NODE",f"{anchor},{x:.12g},{y:.12g},{z+10000:.12g}",f"*ELEMENT,TYPE=SPRINGA,ELSET=SP{i}",
                  f"{next_element+i},{tag},{anchor}",f"*SPRING,ELSET=SP{i},NONLINEAR",
                  *(f"{f:.12e},{u:.12e}" for u,f in curve)]
    def nset(name,tags):
        tags=list(tags)
        return [f"*NSET,NSET={name}",*(", ".join(map(str,tags[i:i+16])) for i in range(0,len(tags),16))]
    loads={int(t):(-1 if args.push else 1)*v for t,v in meta["loads"].items()}
    lines += [*nset("ALLN",nodes),*nset("GROUND",supports+[pin,pin2]),
              "*MATERIAL,NAME=ASSUMED_PLY","*ELASTIC",f"{args.modulus},0.3",
              "*SOLID SECTION,ELSET=PANEL,MATERIAL=ASSUMED_PLY","*BOUNDARY"]
    lines += [f"{t},1,3" for t in supports]
    lines += [f"{pin},1,2",f"{pin2},2,2","*STEP,NLGEOM,INC=100",
              "*CONTROLS,PARAMETERS=TIME INCREMENTATION","12,30,9,60,30,4,0,5,0,0","0.25,0.5,0.75,0.85,0,0,1.5,0"]
    if args.tight:
        lines += ["*CONTROLS,PARAMETERS=FIELD","1.e-5,1.e-4,0.01,,1.e-5,1.e-5,1.e-3,1.e-8"]
    lines += ["*STATIC","1.,1.,1.e-6,1.","*CLOAD"]
    lines += [f"{t},3,{v:.12g}" for t,v in loads.items()]
    lines += ["*NODE PRINT,NSET=ALLN,FREQUENCY=999999","U","*EL PRINT,ELSET=PANEL,FREQUENCY=999999","S",
              "*NODE PRINT,NSET=GROUND,TOTALS=YES,FREQUENCY=999999","RF","*NODE FILE,FREQUENCY=999999","U","*END STEP"]
    name=f"c10_{args.size}_{args.variant}_k{args.stiffness:g}_p{args.penalty:g}_e{args.modulus:g}_{'push' if args.push else 'pull'}".replace(".","p")
    if args.contact_gap:
        name+=f"_g{args.contact_gap:g}".replace(".","p")
    if args.tight:
        name+="_tight"
    job=directory/name
    deck="\n".join(lines)+"\n"
    if args.reparse:
        if job.with_suffix(".inp").read_text()!=deck:
            raise ValueError("Existing input differs from requested case")
    else:
        job.with_suffix(".inp").write_text(deck)
        run=subprocess.run(["ccx","-i",name],cwd=directory,capture_output=True,text=True,check=False)
        job.with_suffix(".log").write_text(run.stdout+run.stderr)
        if run.returncode or "*ERROR" in run.stdout.upper():
            raise RuntimeError(f"Failed connection solve: {job}")
    raw=job.with_suffix(".dat").read_text()
    blocks={title:final_block(raw,title) for title in ("displacements","stresses","forces","total force")}
    def vectors(block):
        return {int(c[0]):tuple(map(float,c[1:])) for line in block.splitlines() if len(c:=line.split())==4 and c[0].isdigit()}
    displacements=vectors(blocks["displacements"])
    reactions=vectors(blocks["forces"])
    deformed={t:tuple(a+b for a,b in zip(xyz,displacements[t],strict=True)) for t,xyz in nodes.items()}
    applied=(0,0,sum(loads.values()))
    moment=(sum(deformed[t][1]*v for t,v in loads.items()),-sum(deformed[t][0]*v for t,v in loads.items()),0)
    result=parse_joint_results("\n".join(blocks.values()),applied,deformed,moment,elements)
    head_forces={key:0. for key in meta["heads"]}
    contact=0.
    extra_contact=0.
    active_contact=0
    spring_error=0.
    for anchor,(tag,k,kind,name) in zip(supports,springs,strict=True):
        delta=tuple(nodes[anchor][i]-deformed[tag][i] for i in range(3))
        length=math.sqrt(sum(v*v for v in delta))
        extension=length-10000
        if abs(extension)>=100:
            raise ValueError("Spring table range exceeded")
        force=k*(max(extension,-1e-9) if kind=="head" else min(extension,1e-9))
        if kind=="back" and args.contact_gap:
            force=k*min(extension+args.contact_gap,0)
        expected=tuple(force*v/length for v in delta)
        spring_error=max(spring_error,max(abs(a-b) for a,b in zip(reactions[anchor],expected,strict=True)))
        if any(abs(a-b)>.05 for a,b in zip(reactions[anchor],expected,strict=True)):
            raise ValueError("Spring law / reaction mismatch")
        if kind=="head":
            head_forces[name]+=force
        else:
            contact-=force
            if str(tag) not in meta["backing"]["baseline"]:
                extra_contact-=force
            active_contact+=extension < -args.contact_gap
    result.update({"revision":meta["revision"],"mesh_mm":args.size,"variant":args.variant,
                   "assumed_axial_stiffness_n_per_mm":stiffness,"backing_penalty_n_per_mm3":args.penalty,"modulus_mpa":args.modulus,
                   "load_direction":"push" if args.push else "pull","applied_force_n":applied,"applied_moment_nmm":moment,
                   "initial_backing_gap_mm":args.contact_gap,
                   "tight_convergence":args.tight,
                   "head_tension_n":head_forces,"backing_compression_n":contact,"active_contact_nodes":active_contact,
                   "extra_backing_compression_n":extra_contact,
                   "backing_area_mm2":sum(patches.values()),"panel_nodes":len(original),
                   "wrong_sign_force_bound_n":sum(k*1e-9 for _,k,kind,_ in springs if kind=="head" or not args.contact_gap),
                   "max_spring_law_residual_n":spring_error,
                   "sum_abs_transverse_anchor_force_n":sum(math.hypot(*reactions[t][:2]) for t in supports),
                   "in_plane_pin_reactions_n":{t:reactions[t] for t in (pin,pin2)},
                   "max_panel_separation_mm":max(-displacements[t][2] for t in original),
                   "max_backing_penetration_mm":max(0,max(displacements[int(t)][2]-args.contact_gap for t in patches)),
                   "evidence_sha256":{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in (job.with_suffix(".inp"),job.with_suffix(".dat"))},
                   "audit_context_sha256":{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in (meta_path,Path(__file__))}})
    job.with_suffix(".json").write_text(json.dumps(result,indent=2)+"\n")
    print(json.dumps(result),flush=True)


if __name__=="__main__":
    main()
