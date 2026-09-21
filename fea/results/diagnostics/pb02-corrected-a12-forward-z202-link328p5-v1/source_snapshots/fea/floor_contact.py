"""Bounded, unpinned floor-contact feasibility experiment; not joint validation."""
import argparse
import hashlib
import json
import math
import subprocess
from pathlib import Path

SOURCE = Path("fea/generated/hybrid/2x8-foot100/box_audited_60_7000.inp")
DIRECTORY = Path("fea/generated/floor-contact")
FACES = ((0, 1, 2, 4, 5, 6), (0, 3, 1, 7, 8, 4),
         (1, 3, 2, 8, 9, 5), (2, 3, 0, 9, 7, 6))


def mesh(text):
    nodes, elements = {}, {}
    mode = None
    for line in text.splitlines():
        if line.startswith("**") or not line.strip():
            continue
        if line.startswith("*"):
            mode = "nodes" if line.upper().startswith("*NODE\n") or line.upper() == "*NODE" else (
                "elements" if line.upper().startswith("*ELEMENT,") and "C3D10" in line.upper() else None)
            continue
        cells = line.split(",")
        if mode == "nodes":
            nodes[int(cells[0])] = tuple(map(float, cells[1:4]))
        elif mode == "elements":
            if len(cells) != 11:
                raise ValueError("Expected single-line C3D10 element")
            elements[int(cells[0])] = tuple(map(int, cells[1:]))
    if not nodes or not elements:
        raise ValueError("Missing frozen mesh")
    return nodes, elements


def floor_faces(nodes, elements):
    groups = {"LEFT": [], "RIGHT": [], "KICKER": []}
    for tag, ids in elements.items():
        for face, indices in enumerate(FACES, 1):
            xyz = [nodes[ids[i]] for i in indices]
            if all(abs(p[2]) < 1e-5 for p in xyz):
                centre = [sum(p[i] for p in xyz)/6 for i in range(3)]
                group = ("LEFT" if centre[0] < 0 else "RIGHT") if centre[1] > 1000 else "KICKER"
                groups[group].append((tag, face))
    if not all(groups.values()):
        raise ValueError("Missing floor contact group")
    return groups


def prepare():
    from mini_moonboard.footprint_frame import parts

    timber = [p.shape for p in parts(100, False) if not p.name.startswith("angle_")]
    volume = sum(p.Volume() for p in timber)
    cg = [sum(p.Volume()*p.centerOfMass(p).toTuple()[i] for p in timber)/volume for i in range(3)]
    summary = json.loads(SOURCE.with_suffix(".json").read_text())
    if summary["candidate"] != "2x8-foot100" or summary["evidence_sha256"][SOURCE.name] != hashlib.sha256(SOURCE.read_bytes()).hexdigest():
        raise ValueError("Frozen candidate provenance mismatch")
    geometry = summary["frozen_geometry"]["geometry_source_sha256"]
    if any(hashlib.sha256(Path(p).read_bytes()).hexdigest() != digest for p,digest in geometry.items()):
        raise ValueError("Current CAD sources differ from frozen geometry")
    DIRECTORY.mkdir(parents=True, exist_ok=True)
    result = {"source": str(SOURCE), "source_sha256": hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
              "cad_volume_mm3": volume, "cad_centre_mm": cg, "cad_mass_kg": volume*600/1e9,
              "geometry_source_sha256": geometry,
              "assumptions": "Undrilled timber only at600kg/m3, no angles/fasteners/holds/glue/LEDmass. Bonded timber retained. No joint capacity."}
    (DIRECTORY/"input.json").write_text(json.dumps(result, indent=2)+"\n")
    print(json.dumps(result, indent=2))


def integrated_weights(elements, nodes):
    """Consistent nodal volume weights integrate gravity and its deformed moment."""
    import gmsh

    if not nodes or any(len(xyz)!=3 or not all(map(math.isfinite,xyz)) for xyz in nodes.values()):
        raise ValueError("Finite three-coordinate nodes required")
    gmsh.initialize()
    gmsh.option.setNumber("General.Verbosity", 1)
    gmsh.model.add("frozen_mesh")
    entity = gmsh.model.addDiscreteEntity(3)
    gmsh.model.mesh.addNodes(3, entity, list(nodes), [v for xyz in nodes.values() for v in xyz])
    # Abaqus C3D10 and Gmsh tetra10 exchange their last two edge nodes.
    gmsh.model.mesh.addElementsByType(entity, 11, list(elements),
                                    [ids[i] for ids in elements.values() for i in (0,1,2,3,4,5,6,7,9,8)])
    points, weights = gmsh.model.mesh.getIntegrationPoints(11, "Gauss5")
    _, basis, _ = gmsh.model.mesh.getBasisFunctions(11, points, "Lagrange")
    result = dict.fromkeys(nodes, 0.0)
    for _, entity in gmsh.model.getEntities(3):
        tags, ids = gmsh.model.mesh.getElementsByType(11, entity)
        _, determinants, _ = gmsh.model.mesh.getJacobians(11, points, entity)
        for e in range(len(tags)):
            for q, weight in enumerate(weights):
                determinant = determinants[e*len(weights)+q]
                if not math.isfinite(determinant) or determinant <= 0:
                    raise ValueError("Nonpositive integration Jacobian")
                factor = determinant*weight
                for i in range(10):
                    result[int(ids[e*10+i])] += factor*basis[q*10+i]
    gmsh.finalize()
    if not all(map(math.isfinite,result.values())) or sum(result.values()) <= 0:
        raise ValueError("Nonfinite or nonpositive integrated volume")
    return result


def node_set(name, ids):
    ids = list(ids)
    return [f"*NSET,NSET={name}", *( ",".join(map(str, ids[i:i+16])) for i in range(0, len(ids), 16))]


def job_name(mu, stiffness):
    values = [repr(float(value)).removesuffix(".0").replace(".","p") for value in (mu,stiffness)]
    return f"floor_mu{values[0]}_k{values[1]}"


def deck(nodes, elements, groups, top, mu, stiffness):
    lines = ["*HEADING", "UNPINNED FLOOR CONTACT FEASIBILITY", "*NODE"]
    lines += [f"{n},"+",".join(f"{x:.12g}" for x in xyz) for n, xyz in nodes.items()]
    lines += ["*ELEMENT,TYPE=C3D10,ELSET=TIMBER"]
    lines += [f"{e},"+",".join(map(str, ids)) for e, ids in elements.items()]
    ground = {}
    next_node, next_element = max(nodes)+1, max(elements)+1
    for index, (name, faces) in enumerate(groups.items()):
        points = [nodes[elements[e][i]] for e, face in faces for i in FACES[face-1]]
        x0, x1 = min(p[0] for p in points)-100, max(p[0] for p in points)+100
        y0, y1 = min(p[1] for p in points)-100, max(p[1] for p in points)+100
        xyz = [(x0,y0,-100), (x1,y0,-100), (x1,y1,-100), (x0,y1,-100),
               (x0,y0,0), (x1,y0,0), (x1,y1,0), (x0,y1,0)]
        ids = list(range(next_node+index*8, next_node+(index+1)*8))
        ground[name] = dict(zip(ids, xyz, strict=True))
        lines += ["*NODE"]+[f"{n},"+",".join(map(str,p)) for n,p in ground[name].items()]
        lines += [f"*ELEMENT,TYPE=C3D8,ELSET=GROUND_{name}",
                  f"{next_element+index},"+",".join(map(str,ids)),
                  f"*SOLID SECTION,ELSET=GROUND_{name},MATERIAL=WOOD", *node_set("GROUND_"+name, ids),
                  f"*SURFACE,NAME=MASTER_{name}",f"{next_element+index},S2",
                  f"*SURFACE,NAME=SLAVE_{name}"]
        lines += [f"{e},S{face}" for e,face in faces]
        lines += ["*CONTACT PAIR,INTERACTION=FLOOR,TYPE=SURFACE TO SURFACE",f"SLAVE_{name},MASTER_{name}"]
    lines += ["*MATERIAL,NAME=WOOD", "*ELASTIC", "7000,0.3", "*DENSITY", "6e-10",
              "*SOLID SECTION,ELSET=TIMBER,MATERIAL=WOOD", "*SURFACE INTERACTION,NAME=FLOOR",
              "*SURFACE BEHAVIOR,PRESSURE-OVERCLOSURE=LINEAR", str(stiffness),
              "*FRICTION", f"{mu},{stiffness/100}", *node_set("WOODN",nodes), *node_set("TOP",top), "*BOUNDARY"]
    lines += [f"GROUND_{name},1,3,0" for name in ground]
    for load in (0, 1200):
        lines += ["*STEP,NLGEOM,INC=200", "*STATIC", "0.05,1,1e-6,0.1", "*DLOAD", "TIMBER,GRAV,9806.65,0,0,-1"]
        if load:
            lines += ["*CLOAD,OP=NEW"]+[f"{node},3,{-load/len(top)}" for node in top]
        lines += ["*NODE PRINT,NSET=WOODN", "U"]
        for name in ground:
            lines += [f"*NODE PRINT,NSET=GROUND_{name}", "RF"]
        lines += ["*CONTACT FILE", "CDIS,CSTR", "*NODE FILE", "U", "*END STEP"]
    return "\n".join(lines)+"\n", ground


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--prepare", action="store_true")
    parser.add_argument("--mu", type=float, default=.3)
    parser.add_argument("--stiffness", type=float, default=10000)
    parser.add_argument("--max-seconds", type=float, default=240)
    args = parser.parse_args()
    if args.prepare:
        prepare()
        return
    if not 0 < args.mu <= 1 or any(not math.isfinite(v) or v <= 0 for v in (args.stiffness,args.max_seconds)):
        parser.error("finite positive stiffness/runtime and 0<mu<=1 required")
    info = json.loads((DIRECTORY/"input.json").read_text())
    if hashlib.sha256(SOURCE.read_bytes()).hexdigest() != info["source_sha256"]:
        raise ValueError("Frozen mesh changed")
    if any(hashlib.sha256(Path(p).read_bytes()).hexdigest() != digest for p,digest in info["geometry_source_sha256"].items()):
        raise ValueError("Current CAD sources differ from prepared mesh")
    nodes, elements = mesh(SOURCE.read_text())
    nodal_volumes = integrated_weights(elements, nodes)
    volume = sum(nodal_volumes.values())
    cg = [sum(v*nodes[n][i] for n,v in nodal_volumes.items())/volume for i in range(3)]
    if abs(volume/info["cad_volume_mm3"]-1) > .001 or math.dist(cg,info["cad_centre_mm"]) > 1:
        raise ValueError("Integrated mesh mass/CG inconsistent with actual timber CAD")
    groups = floor_faces(nodes, elements)
    summary = json.loads(SOURCE.with_suffix(".json").read_text())
    text, ground = deck(nodes,elements,groups,summary["load_nodes"],args.mu,args.stiffness)
    # Keep decimal parameters out of suffix parsing.
    job = DIRECTORY/job_name(args.mu,args.stiffness)
    job.with_suffix(".inp").write_text(text)
    record = dict(info, mesh_volume_mm3=volume, mesh_mass_kg=volume*600/1e9, mesh_centre_mm=cg,
                  mu=args.mu, normal_penalty_n_mm3=args.stiffness, tangent_penalty_n_mm3=args.stiffness/100,
                  ground_nodes=ground, nodal_volume_mm3=nodal_volumes,
                  floor_face_counts={k:len(v) for k,v in groups.items()}, load_nodes=summary["load_nodes"],
                  run_source_sha256={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in
                                     (Path("fea/floor_contact.py"),Path("fea/floor_contact_results.py"))},
                  deck_sha256=hashlib.sha256(text.encode()).hexdigest(), status="NOT RUN")
    job.with_suffix(".json").write_text(json.dumps(record,indent=2)+"\n")
    command = ["ccx","-i",job.name]
    try:
        result = subprocess.run(command,cwd=DIRECTORY,capture_output=True,text=True,check=False,timeout=args.max_seconds)
    except subprocess.TimeoutExpired as error:
        result = subprocess.CompletedProcess(command,-999,
            error.stdout.decode() if isinstance(error.stdout,bytes) else error.stdout or "",
            error.stderr.decode() if isinstance(error.stderr,bytes) else error.stderr or "")
        record["runtime_stop"] = f"Deliberately stopped after {args.max_seconds:g}s; not a physical failure conclusion"
    job.with_suffix(".log").write_text(result.stdout+result.stderr)
    record["exit_code"] = result.returncode
    record["status"] = "UNRESOLVED SOLVER FAILURE; NOT A STABILITY CONCLUSION"
    if result.returncode == 0 and "*ERROR" not in (result.stdout+result.stderr).upper():
        if __package__:
            from .floor_contact_results import audit, verify_deck
        else:
            from floor_contact_results import audit, verify_deck
        try:
            verify_deck(job.with_suffix(".inp").read_text(),nodes,elements,groups,record)
            record["audited_steps"] = audit(job.with_suffix(".dat").read_text(),nodes,elements,groups,record)
            record["status"] = "TWO COMPLETE EQUILIBRIUM-AUDITED STEPS; LOCAL CONTACT AUDIT STILL REQUIRED"
        except ValueError as error:
            record["status"] = "UNRESOLVED OUTPUT/EQUILIBRIUM AUDIT"
            record["audit_error"] = str(error)
    job.with_suffix(".json").write_text(json.dumps(record,indent=2)+"\n")
    print(record["status"])


if __name__ == "__main__":
    main()
