"""Actual-CAD bearing-traction submodels, not a full nonlinear joint solve."""
import argparse
import json
import math
import subprocess
from pathlib import Path

import gmsh
from joint_math import bolt_forces, parse_joint_results, radial_loads


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--size", type=float, default=8)
    parser.add_argument("--modulus", type=float, default=7000)
    args = parser.parse_args()
    if not all(math.isfinite(v) and v>0 for v in (args.size, args.modulus)):
        parser.error("positive finite mesh size and modulus required")
    directory = Path("fea/generated")
    records = json.loads((directory/"joints.json").read_text())
    results = []
    def local(xyz, origin):
        y, z = xyz[1]-origin[1], xyz[2]-origin[2]
        return y*sn+z*cs, -y*cs+z*sn
    def world(s, n):
        return 0., s*sn-n*cs, s*cs+n*sn
    def nset(name, tags):
        return [f"*NSET,NSET={name}", *(" ,".join(map(str,tags[i:i+16])) for i in range(0,len(tags),16))]
    for record in records:
        sn, cs = math.sin(math.radians(record["angle_deg"])), math.cos(math.radians(record["angle_deg"]))
        name = record["name"]
        prefix = directory/f"joint_{name}_{args.size:g}_{args.modulus:g}".replace(".", "p")
        gmsh.initialize()
        gmsh.option.setNumber("General.Verbosity", 2)
        gmsh.model.add(name)
        gmsh.model.occ.importShapes(str(directory/f"joint_{name}.step"))
        gmsh.model.occ.synchronize()
        gmsh.model.addPhysicalGroup(3, [tag for _,tag in gmsh.model.getEntities(3)], 1)
        gmsh.model.setPhysicalName(3, 1, "WOOD")
        gmsh.option.setNumber("Mesh.MeshSizeMax", args.size)
        gmsh.option.setNumber("Mesh.MeshSizeMin", args.size/4)
        gmsh.option.setNumber("Mesh.MeshSizeFromCurvature", 12)
        gmsh.option.setNumber("Mesh.MeshSizeExtendFromBoundary", 0)
        gmsh.option.setNumber("Mesh.ElementOrder", 2)
        gmsh.model.mesh.generate(3)
        gmsh.model.mesh.optimize("HighOrder")
        element_tags = gmsh.model.mesh.getElements(3)[1]
        min_jacobian = min(float(v) for tags3 in element_tags for v in gmsh.model.mesh.getElementQualities(tags3, "minDetJac"))
        if min_jacobian <= 0:
            raise ValueError("Inverted joint mesh after high-order optimization")
        gmsh.write(str(prefix.with_suffix(".inp")))
        tags, coords, _ = gmsh.model.mesh.getNodes()
        nodes = {int(t):tuple(float(v) for v in coords[i*3:i*3+3]) for i,t in enumerate(tags)}
        loc = {tag:local(xyz,record["origin_mm"]) for tag,xyz in nodes.items()}
        clamp = [t for t,(s,n) in loc.items() if abs(s-record["clamp_s_mm"])<1e-5]
        weights = [{} for _ in record["stations_mm"]]
        for _, face in gmsh.model.getEntities(2):
            types, _, connectivity = gmsh.model.mesh.getElements(2, face)
            for kind, flat in zip(types, connectivity, strict=True):
                if kind != 9:
                    raise ValueError("Expected six-node surface triangles")
                for i in range(0,len(flat),6):
                    tri = [int(t) for t in flat[i:i+6]]
                    for j, station in enumerate(record["stations_mm"]):
                        if not all(abs(math.hypot(loc[t][0]-station,loc[t][1]-record["normal_mm"])-record["hole_radius_mm"])<1e-4 for t in tri):
                            continue
                        a,b,c = [nodes[t] for t in tri[:3]]
                        u,v = [b[k]-a[k] for k in range(3)], [c[k]-a[k] for k in range(3)]
                        area = math.sqrt(sum((u[k]*v[(k+1)%3]-u[(k+1)%3]*v[k])**2 for k in range(3)))/2
                        # Three-point midside surface quadrature: exact for a
                        # constant traction on a quadratic triangle, unlike
                        # equal corner/midside lumping. Bore-pressure variation
                        # is sampled at these quadrature nodes and refined.
                        for t in tri[3:]:
                            weights[j][t] = weights[j].get(t,0)+area/3
        gmsh.finalize()
        if not clamp or not all(weights):
            raise ValueError("Missing clamp or bore surfaces")
        base = prefix.with_suffix(".inp").read_text()
        if "C3D10" not in base.upper():
            raise ValueError("Expected C3D10 timber")
        for case, fs, fn, moment in (("shear_s",1000,0,0), ("shear_n",0,1000,0), ("moment",0,0,100000)):
            forces = {}
            for station, areas, target in zip(record["stations_mm"],weights,bolt_forces(record["stations_mm"],fs,fn,moment),strict=True):
                samples = [(t,w,(loc[t][0]-station)/record["hole_radius_mm"],(loc[t][1]-record["normal_mm"])/record["hole_radius_mm"]) for t,w in areas.items()]
                for tag, force in radial_loads(samples,target).items():
                    forces[tag] = world(*force)
            applied = [sum(v[i] for v in forces.values()) for i in range(3)]
            expected = world(fs,fn)
            if any(abs(a-b)>.001 for a,b in zip(applied,expected,strict=True)):
                raise ValueError("Incorrect applied resultant")
            centre = sum(record["stations_mm"])/len(record["stations_mm"])
            actual_moment = sum((loc[t][0]-centre)*(-v[1]*cs+v[2]*sn)-(loc[t][1]-record["normal_mm"])*(v[1]*sn+v[2]*cs) for t,v in forces.items())
            if abs(actual_moment-moment)>.01:
                raise ValueError("Incorrect applied bolt-group moment")
            job = prefix.with_name(prefix.name+"_"+case)
            lines = [base, *nset("CLAMP",clamp), *nset("ALLN",list(nodes)),
                     "*MATERIAL,NAME=ISOTROPIC_SCREEN", "*ELASTIC", f"{args.modulus},0.3",
                     "*SOLID SECTION,ELSET=WOOD,MATERIAL=ISOTROPIC_SCREEN", "*STEP", "*STATIC",
                     "*BOUNDARY", "CLAMP,1,3,0", "*CLOAD"]
            lines += [f"{t},{i+1},{v:.12g}" for t,xyz in forces.items() for i,v in enumerate(xyz) if v]
            lines += ["*NODE PRINT,NSET=ALLN", "U", "*EL PRINT,ELSET=WOOD", "S",
                      "*NODE PRINT,NSET=CLAMP,TOTALS=YES", "RF", "*NODE FILE", "U", "*EL FILE", "S", "*END STEP"]
            job.with_suffix(".inp").write_text("\n".join(lines)+"\n")
            run = subprocess.run(["ccx","-i",job.name],cwd=directory,capture_output=True,text=True,check=False)
            job.with_suffix(".log").write_text(run.stdout+run.stderr)
            if run.returncode or "*ERROR" in run.stdout.upper():
                raise RuntimeError(f"CalculiX failed: {job}")
            applied_moment = [sum(nodes[t][(i+1)%3]*v[(i+2)%3]-nodes[t][(i+2)%3]*v[(i+1)%3] for t,v in forces.items()) for i in range(3)]
            elements = {int(t) for tags3 in element_tags for t in tags3}
            result = parse_joint_results(job.with_suffix(".dat").read_text(),applied,nodes,applied_moment,elements)
            results.append(dict(part=name,case=case,mesh_mm=args.size,modulus_mpa=args.modulus,nodes=len(nodes),min_jacobian=min_jacobian,
                                applied_force_n=applied,applied_group_moment_nmm=actual_moment,**result))
            print(json.dumps(results[-1]),flush=True)
    out = directory/f"joint_results_{args.size:g}_{args.modulus:g}".replace(".","p")
    out.with_suffix(".json").write_text(json.dumps(results,indent=2)+"\n")


if __name__ == "__main__":
    main()
