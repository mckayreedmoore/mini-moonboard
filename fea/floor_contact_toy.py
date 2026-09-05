"""Two-brick unpinned gravity check of the same floor contact law."""
import argparse
import hashlib
import json
import math
import subprocess
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--quadratic",action="store_true")
    args = parser.parse_args()
    name = "toy_quadratic" if args.quadratic else "toy"
    directory = Path("fea/generated/floor-contact")
    directory.mkdir(parents=True,exist_ok=True)
    nodes = [(0,0,0),(100,0,0),(100,100,0),(0,100,0),
             (0,0,100),(100,0,100),(100,100,100),(0,100,100),
             (-10,-10,-100),(110,-10,-100),(110,110,-100),(-10,110,-100),
             (-10,-10,0),(110,-10,0),(110,110,0),(-10,110,0)]
    lines = ["*NODE"]+[f"{i},"+",".join(map(str,p)) for i,p in enumerate(nodes,1)]
    lines += ["*ELEMENT,TYPE=C3D8,ELSET=WOOD", "1,1,2,3,4,5,6,7,8",
              "*ELEMENT,TYPE=C3D8,ELSET=GROUND", "2,9,10,11,12,13,14,15,16",
              "*NSET,NSET=GROUND", "9,10,11,12,13,14,15,16",
              "*NSET,NSET=WOOD", "1,2,3,4,5,6,7,8", "*MATERIAL,NAME=WOOD",
              "*ELASTIC", "7000,.3", "*DENSITY", "6e-10",
              "*SOLID SECTION,ELSET=WOOD,MATERIAL=WOOD", "*SOLID SECTION,ELSET=GROUND,MATERIAL=WOOD",
              "*SURFACE,NAME=SLAVE", "1,S1", "*SURFACE,NAME=MASTER", "2,S2",
              "*SURFACE INTERACTION,NAME=FLOOR", "*SURFACE BEHAVIOR,PRESSURE-OVERCLOSURE=LINEAR", "10000",
              "*FRICTION", ".3,100", "*CONTACT PAIR,INTERACTION=FLOOR,TYPE=SURFACE TO SURFACE",
              "SLAVE,MASTER", "*BOUNDARY", "GROUND,1,3,0", "*STEP,NLGEOM,INC=100",
              "*STATIC", "0.05,1,1e-6,0.1", "*DLOAD", "WOOD,GRAV,9806.65,0,0,-1",
              "*NODE PRINT,NSET=WOOD", "U", "*NODE PRINT,NSET=GROUND", "RF",
              "*CONTACT FILE", "CDIS,CSTR", "*END STEP"]
    wood = list(range(1,9))
    nodal_volumes = dict.fromkeys(wood,1e6/8)
    if args.quadratic:
        if __package__:
            from .floor_contact import FACES, integrated_weights
        else:
            from floor_contact import FACES, integrated_weights
        edges, elements = {}, {}
        for tag, (a,b,c,d) in enumerate(((1,2,3,7),(1,3,4,7),(1,4,8,7),(1,8,5,7),(1,5,6,7),(1,6,2,7)),1):
            mids = []
            for edge in ((a,b),(b,c),(c,a),(a,d),(b,d),(c,d)):
                edge = tuple(sorted(edge))
                if edge not in edges:
                    nodes.append(tuple((nodes[edge[0]-1][i]+nodes[edge[1]-1][i])/2 for i in range(3)))
                    edges[edge] = len(nodes)
                mids.append(edges[edge])
            elements[tag] = (a,b,c,d,*mids)
        wood += list(range(17,len(nodes)+1))
        nodal_volumes = integrated_weights(elements,{n:nodes[n-1] for n in wood})
        start = lines.index("*ELEMENT,TYPE=C3D8,ELSET=WOOD")
        lines[start:start+2] = ([f"{n},"+",".join(map(str,nodes[n-1])) for n in range(17,len(nodes)+1)]
            +["*ELEMENT,TYPE=C3D10,ELSET=WOOD"]+[f"{e},"+",".join(map(str,ids)) for e,ids in elements.items()])
        lines[lines.index("2,9,10,11,12,13,14,15,16")] = "99,9,10,11,12,13,14,15,16"
        lines[lines.index("2,S2")] = "99,S2"
        start = lines.index("*NSET,NSET=WOOD")+1
        lines[start:start+1] = [",".join(map(str,wood[i:i+16])) for i in range(0,len(wood),16)]
        start = lines.index("1,S1")
        lines[start:start+1] = [f"{e},S{face}" for e,ids in elements.items() for face,indices in enumerate(FACES,1)
                               if all(nodes[ids[i]-1][2]==0 for i in indices)]
    (directory/f"{name}.inp").write_text("\n".join(lines)+"\n")
    result = subprocess.run(["ccx","-i",name],cwd=directory,capture_output=True,text=True,check=False,timeout=60)
    (directory/f"{name}.log").write_text(result.stdout+result.stderr)
    if __package__:
        from .floor_contact_results import blocks, cross
    else:
        from floor_contact_results import blocks, cross
    parsed = blocks((directory/f"{name}.dat").read_text())
    u = parsed.get(("displacements","WOOD",1.),{})
    rf = parsed.get(("forces","GROUND",1.),{})
    if result.returncode or "*ERROR" in (result.stdout+result.stderr).upper() or set(u)!=set(wood) or set(rf)!=set(range(9,17)):
        raise ValueError("Toy failed or final output incomplete")
    cg = [sum((nodes[n-1][i]+u[n][i])*nodal_volumes[n] for n in wood)/sum(nodal_volumes.values()) for i in range(3)]
    weight = .6*9.80665
    force = [sum(v[i] for v in rf.values())+(weight if i==2 else 0)*-1 for i in range(3)]
    moment = [sum(cross(nodes[n-1],v)[i] for n,v in rf.items())+cross(cg,(0,0,-weight))[i] for i in range(3)]
    if max(map(abs,force))>1e-5 or max(map(abs,moment))>.001:
        raise ValueError("Toy equilibrium audit failed")
    reaction = [sum(v[i] for v in rf.values()) for i in range(3)]
    if reaction[2]<0 or math.hypot(*reaction[:2])>.3*reaction[2]+1e-5:
        raise ValueError("Toy aggregate contact bound failed")
    report = {"status":"Complete gravity contact-law smoke test only; not whole-frame validation",
              "mass_kg":.6,"weight_n":weight,"force_residual_n":force,"moment_residual_nmm":moment,
              "ground_resultant_n":reaction,"minimum_physical_gap_mm":min(u[n][2] for n in wood if nodes[n-1][2]==0),
              "maximum_physical_gap_mm":max(u[n][2] for n in wood if nodes[n-1][2]==0),
              "sha256":{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in (directory/f"{name}.inp",directory/f"{name}.dat")}}
    (directory/f"{name}.json").write_text(json.dumps(report,indent=2)+"\n")
    print(result.returncode)
    print(result.stdout[-1500:])


if __name__ == "__main__":
    main()
