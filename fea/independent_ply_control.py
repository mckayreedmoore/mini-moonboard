"""Conditional no-contact stiffness control; unequal loads may interpenetrate.

This mathematical comparison is not a physically admissible assembly model,
nor a plywood strength or buckling claim.
"""
import hashlib
import json
import math
import os
import subprocess
import tempfile
from pathlib import Path

from fea.floor_contact import FACES, node_set
from fea.floor_contact_results import blocks, cross
from fea.section_force_coupon import format_cload
from fea.section_force_tet_coupon import deck as mesh_deck
from fea.section_force_tet_coupon import triangle_loads

E, LENGTH, WIDTH, THICKNESS, MOMENT = 7000., 400., 100., 38.1, 1000.
# Frozen before solver launch. nu=0 makes the quadratic pure-bending field
# satisfy the fully fixed end exactly; no shear/clamp correction is fitted.
GATES = {"relative_analytic": .001, "relative_ratios": .001,
         "relative_mesh_change": .001, "force_n": .001, "moment_nmm": .01,
         "unloaded_displacement_mm": 1e-10, "unloaded_energy_nmm": 1e-10,
         "serialized_resultant": 1e-8}


def resultant(nodes, loads):
    return [sum(f[i] for f in loads.values()) for i in range(3)]+[
        sum(cross(nodes[n], f)[i] for n, f in loads.items()) for i in range(3)]


def deck(divisions, independent):
    _, seed = mesh_deck(divisions)
    nodes, elements, plies = {}, {}, []
    thickness = THICKNESS/(2 if independent else 1)
    for index in range(2 if independent else 1):
        offset, eoffset = len(nodes), len(elements)
        center = (-THICKNESS/4 if index == 0 else THICKNESS/4) if independent else 0.
        ids = {n+offset for n in seed["nodes"]}
        nodes.update({n+offset: (center+p[0]*thickness/10, p[1]*WIDTH/10, p[2]*LENGTH/100)
                      for n,p in seed["nodes"].items()})
        elements.update({e+eoffset: [n+offset for n in ns] for e,ns in seed["elements"].items()})
        fixed = sorted(n for n in ids if nodes[n][2] == 0)
        top = next(n for n in ids if nodes[n] == (center, 0., LENGTH))
        plies.append({"nodes": sorted(ids), "fixed": fixed, "tip_centroid_node": top,
                      "center_x": center, "thickness": thickness,
                      "top_faces": [(e+eoffset, f) for e,f in seed["surfaces"]["TOP"]]})
    if independent and set(plies[0]["nodes"]) & set(plies[1]["nodes"]):
        raise ValueError("Interface node sharing")
    for ids in elements.values():
        if sum(set(ids) <= set(p["nodes"]) for p in plies) != 1:
            raise ValueError("Element couples plies")
    lines = ["*HEADING", "HOMOGENEOUS INDEPENDENT PLY PURE BENDING CONTROL", "*NODE"]
    lines += [f"{n},"+",".join(map(str,p)) for n,p in nodes.items()]
    lines += ["*ELEMENT,TYPE=C3D10,ELSET=BEAM"]+[f"{e},"+",".join(map(str,ns)) for e,ns in elements.items()]
    lines += ["*MATERIAL,NAME=CONTROL", "*ELASTIC", f"{E},0", "*SOLID SECTION,ELSET=BEAM,MATERIAL=CONTROL",
              *node_set("ALLN", nodes), *node_set("FIXED", [n for p in plies for n in p["fixed"]])]
    cases = []
    for sharing in (["symmetric", "inner_only"] if independent else ["composite"]):
        for axis, name in ((1,"in_plane"), (0,"out_of_plane")):
            loads, exact = {}, []
            for index, ply in enumerate(plies):
                moment = MOMENT*(.5 if sharing == "symmetric" else (0. if sharing == "inner_only" and index else 1.))
                inertia = thickness*WIDTH**3/12 if axis == 1 else WIDTH*thickness**3/12
                curvature = moment/(E*inertia)
                for element, face in ply["top_faces"]:
                    ns = [elements[element][i] for i in FACES[face-1]]
                    corners = [nodes[n] for n in ns[:3]]
                    stresses = [moment/inertia*(p[axis]-(ply["center_x"] if axis == 0 else 0.)) for p in corners]
                    for n,force in zip(ns, triangle_loads(corners, stresses), strict=True):
                        loads[n] = loads.get(n, 0.)+force
                exact.append({"moment_nmm": moment, "inertia_mm4": inertia,
                              "tip_displacement_mm": -curvature*LENGTH**2/2,
                              "energy_nmm": moment**2*LENGTH/(2*E*inertia)})
            cases.append({"sharing": sharing, "direction": name, "axis": axis, "loads": loads, "exact": exact})
            lines += ["*STEP", "*STATIC", "*BOUNDARY", "FIXED,1,3,0", "*CLOAD,OP=NEW"]
            lines += [f"{n},3,{format_cload(f)}" for n,f in loads.items() if f]
            lines += ["*NODE PRINT,NSET=FIXED", "RF", "*NODE PRINT,NSET=ALLN", "U", "*END STEP"]
    text = "\n".join(lines)+"\n"
    context = {"nodes": nodes, "elements": elements, "plies": plies, "cases": cases,
               "divisions": divisions, "independent": independent, "gates": GATES}
    context["serialized_loads"] = verify_serialized(text, context)
    return text, context


def verify_serialized(text, context):
    if any(token in text.upper() for token in ("*TIE", "*EQUATION", "*COUPLING", "*CONTACT")):
        raise ValueError("Unexpected ply coupling")
    groups = []
    for part in text.split("*CLOAD,OP=NEW\n")[1:]:
        loads = {}
        for line in part.split("*",1)[0].splitlines():
            n, direction, value = line.split(",")
            if direction != "3" or len(value)>20 or int(n) in loads or not math.isfinite(float(value)):
                raise ValueError("Invalid serialized load")
            loads[int(n)] = float(value)
        groups.append(loads)
    if len(groups) != len(context["cases"]):
        raise ValueError("Incomplete serialized cases")
    results = []
    for actual, case in zip(groups, context["cases"], strict=True):
        intended = {n:f for n,f in case["loads"].items() if f}
        if actual.keys()!=intended.keys() or any(not math.isclose(f,intended[n],rel_tol=1e-12,abs_tol=1e-12) for n,f in actual.items()):
            raise ValueError("Serialized load mismatch")
        per_ply = []
        for ply, exact in zip(context["plies"],case["exact"],strict=True):
            values = resultant(context["nodes"], {n:(0.,0.,actual[n]) for n in ply["nodes"] if n in actual})
            target = [0.]*6
            target[3 if case["axis"] == 1 else 4] = exact["moment_nmm"]*(1 if case["axis"] == 1 else -1)
            if max(abs(a-b) for a,b in zip(values,target,strict=True)) > GATES["serialized_resultant"]:
                raise ValueError("Per-ply serialized resultant mismatch")
            per_ply.append(values)
        results.append(per_ply)
    return results


def audit(data, context):
    parsed = blocks(data)
    expected = {(kind,name,float(t)) for t in range(1,len(context["cases"])+1)
                for kind,name in (("forces","FIXED"),("displacements","ALLN"))}
    if set(parsed) != expected:
        raise ValueError("Incomplete/extra output endpoints")
    records = []
    for time,case in enumerate(context["cases"],1):
        u,rf = parsed["displacements","ALLN",float(time)], parsed["forces","FIXED",float(time)]
        if set(u)!=set(context["nodes"]) or set(rf)!={n for p in context["plies"] for n in p["fixed"]}:
            raise ValueError("Incomplete node output")
        per_ply = []
        for index,(ply,exact) in enumerate(zip(context["plies"],case["exact"],strict=True)):
            reaction = resultant(context["nodes"],{n:rf[n] for n in ply["fixed"]})
            applied = context["serialized_loads"][time-1][index]
            residual = [a+b for a,b in zip(reaction,applied,strict=True)]
            displacement = u[ply["tip_centroid_node"]][case["axis"]]
            energy = sum(case["loads"].get(n,0.)*u[n][2] for n in ply["nodes"])/2
            # Linear elastic zero prescribed displacement: external work/2
            # equals strain energy. This is not native element energy output.
            fixed_u = max(math.hypot(*u[n]) for n in ply["fixed"])
            passed = (max(map(abs,residual[:3]))<=GATES["force_n"] and max(map(abs,residual[3:]))<=GATES["moment_nmm"]
                      and fixed_u<=GATES["unloaded_displacement_mm"])
            max_u = max(math.hypot(*u[n]) for n in ply["nodes"])
            if exact["moment_nmm"]:
                passed &= abs(displacement/exact["tip_displacement_mm"]-1)<=GATES["relative_analytic"] and abs(energy/exact["energy_nmm"]-1)<=GATES["relative_analytic"]
            else:
                passed &= max_u<=GATES["unloaded_displacement_mm"] and abs(energy)<=GATES["unloaded_energy_nmm"]
            per_ply.append({"reaction_force_moment": reaction, "applied_force_moment": applied,
                            "balance_residual": residual, "tip_displacement_mm": displacement,
                            "energy_from_half_external_work_nmm": energy, "maximum_displacement_mm": max_u,
                            "maximum_fixed_displacement_mm": fixed_u, "exact": exact, "pass": bool(passed)})
        records.append({"sharing":case["sharing"],"direction":case["direction"],"plies":per_ply})
    return records


def comparisons(records):
    checks = []
    for n in (2,4):
        for direction,target in (("in_plane",1.),("out_of_plane",4.)):
            reference = next(c for c in records[f"composite{n}"] if c["direction"]==direction)["plies"][0]
            for sharing,multiplier in (("symmetric",1.),("inner_only",2.)):
                plies = next(c for c in records[f"independent{n}"] if c["direction"]==direction and c["sharing"]==sharing)["plies"]
                displacement_ratio = plies[0]["tip_displacement_mm"]/reference["tip_displacement_mm"]
                energy_ratio = sum(p["energy_from_half_external_work_nmm"] for p in plies)/reference["energy_from_half_external_work_nmm"]
                checks.append({"mesh":n,"direction":direction,"sharing":sharing,"target":target*multiplier,
                               "displacement_ratio":displacement_ratio,"energy_ratio":energy_ratio,
                               "pass": all(abs(r/(target*multiplier)-1)<=GATES["relative_ratios"] for r in (displacement_ratio,energy_ratio))})
    mesh_checks = []
    for model in ("composite","independent"):
        for coarse,fine in zip(records[f"{model}2"],records[f"{model}4"],strict=True):
            for p,q in zip(coarse["plies"],fine["plies"],strict=True):
                if p["exact"]["moment_nmm"]:
                    change = {key:abs(q[key]/p[key]-1) for key in ("tip_displacement_mm","energy_from_half_external_work_nmm")}
                    mesh_checks.append({"model":model,"sharing":coarse["sharing"],"direction":coarse["direction"],"relative_change":change,
                                        "pass": max(change.values())<=GATES["relative_mesh_change"]})
    return {"ratios":checks,"mesh_checks":mesh_checks,"pass":all(c["pass"] for c in checks+mesh_checks)}


def main():
    directory = Path(tempfile.mkdtemp(prefix="independent-ply-control-",dir="fea/generated"))
    snapshot = directory/"launch_sources"
    snapshot.mkdir()
    sources = [Path(__file__), *map(Path,("fea/section_force_tet_coupon.py","fea/section_force_coupon.py","fea/floor_contact.py","fea/floor_contact_results.py","tests/test_independent_ply_control.py"))]
    hashes = {}
    for source in sources:
        content = source.read_bytes()
        (snapshot/source.name).write_bytes(content)
        hashes[str(source)] = hashlib.sha256(content).hexdigest()
    manifest = {"gates":GATES,"source_sha256":hashes,"scope":"Homogeneous linear stiffness CONTROL only; no plywood, connection, strength or buckling validation",
                "max_seconds_per_job":60,"omp_threads":2,"solver_image_id":os.environ.get("CONTROL_IMAGE_ID","unrecorded"),"jobs":{}}
    (directory/"manifest.json").write_text(json.dumps(manifest,indent=2)+"\n")
    print(directory,flush=True)
    records = {}
    for n in (2,4):
        for independent in (False,True):
            name = f"{'independent' if independent else 'composite'}{n}"
            text,context = deck(n,independent)
            job = directory/name
            job.with_suffix(".inp").write_text(text)
            record = dict(context,deck_sha256=hashlib.sha256(text.encode()).hexdigest(),status="PREDECLARED; NOT YET RUN")
            job.with_suffix(".json").write_text(json.dumps(record,indent=2,allow_nan=False)+"\n")
            with job.with_suffix(".log").open("w") as log:
                try:
                    run = subprocess.run(["ccx","-i",name],cwd=directory,stdout=log,stderr=subprocess.STDOUT,timeout=60,check=False,env=dict(os.environ,OMP_NUM_THREADS="2"))
                    record["exit_code"] = run.returncode
                except subprocess.TimeoutExpired:
                    record["exit_code"] = -999
            record["status"] = "FAIL_OR_UNRESOLVED"
            try:
                if record["exit_code"] != 0 or "*ERROR" in job.with_suffix(".log").read_text().upper():
                    raise ValueError("Solver failure/timeout/error")
                if hashlib.sha256(job.with_suffix(".inp").read_bytes()).hexdigest()!=record["deck_sha256"]:
                    raise ValueError("Changed launch deck")
                record["results"] = audit(job.with_suffix(".dat").read_text(),context)
                records[name] = record["results"]
                if all(p["pass"] for c in record["results"] for p in c["plies"]):
                    record["status"] = "PASS_HOMOGENEOUS_CONTROL_ONLY"
            except (ValueError,FileNotFoundError) as error:
                record["audit_error"] = str(error)
            record["output_sha256"] = {p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in directory.glob(name+".*") if p.suffix not in (".inp",".json")}
            job.with_suffix(".json").write_text(json.dumps(record,indent=2,allow_nan=False)+"\n")
            manifest["jobs"][name] = record["status"]
            print(name,record["status"],flush=True)
    if len(records)==4:
        manifest["comparisons"] = comparisons(records)
    manifest["pass"] = len(records)==4 and all(s=="PASS_HOMOGENEOUS_CONTROL_ONLY" for s in manifest["jobs"].values()) and manifest["comparisons"]["pass"]
    (directory/"manifest.json").write_text(json.dumps(manifest,indent=2,allow_nan=False)+"\n")
    if not manifest["pass"]:
        raise SystemExit("Control failed: profile interpretation must stop")


if __name__ == "__main__":
    main()
