"""Native SECTION PRINT analytic homogeneous C3D8 check; not a frame rating."""
import hashlib
import json
import math
import os
import re
import subprocess
import tempfile
from pathlib import Path

from fea.floor_contact import node_set
from fea.floor_contact_results import blocks, cross


def format_cload(value):
    if not math.isfinite(value):
        raise ValueError("Finite load required")
    # CalculiX2.21 cloads.f:267 reads only textpart(3)(1:20). Keep existing
    # short tokens byte-identical; otherwise prevent exponent truncation.
    token = f"{value:.15g}"
    return token if len(token) <= 20 else f"{value:.12E}"


def deck(divisions):
    if divisions not in (2, 4):
        raise ValueError("Only two bounded structured mesh comparisons are defined")
    n, nz = divisions, 5*divisions
    node = lambda i, j, k: 1+i+(n+1)*j+(n+1)**2*k
    nodes = {node(i, j, k): (-5+10*i/n, -5+10*j/n, 100*k/nz)
             for k in range(nz+1) for j in range(n+1) for i in range(n+1)}
    elements, lower, upper = {}, [], []
    for k in range(nz):
        for j in range(n):
            for i in range(n):
                tag = len(elements)+1
                elements[tag] = [node(i+di, j+dj, k+dk) for di, dj, dk in
                                 ((0,0,0), (1,0,0), (1,1,0), (0,1,0), (0,0,1), (1,0,1), (1,1,1), (0,1,1))]
                if k == nz//2-1:
                    lower.append(tag)
                if k == nz//2:
                    upper.append(tag)
    fixed = [tag for tag, p in nodes.items() if p[2] == 0]
    top = [tag for tag, p in nodes.items() if p[2] == 100]
    loads = []
    for bending in (False, True):
        forces = dict.fromkeys(top, 0.)
        side = 10/n
        for j in range(n):
            for i in range(n):
                xc = -5+(i+.5)*side
                for di, dj in ((0,0), (1,0), (1,1), (0,1)):
                    # Integral Ni*sigma_z over a bilinear end face: constant
                    # traction or sigma_z=(M/I)*x. This is load application,
                    # not integration of computed element stresses.
                    traction = (1200/(10*10**3/12))*(xc+(2*di-1)*side/6) if bending else 120/100
                    forces[node(i+di, j+dj, nz)] += side**2/4*traction
        loads.append(forces)
    lines = ["*HEADING", "NATIVE SECTION RESULTANT HOMOGENEOUS C3D8 COUPON", "*NODE"]
    lines += [f"{tag},"+",".join(map(str, p)) for tag, p in nodes.items()]
    lines += ["*ELEMENT,TYPE=C3D8,ELSET=BEAM"]+[f"{tag},"+",".join(map(str, ids)) for tag, ids in elements.items()]
    lines += ["*MATERIAL,NAME=ISOTROPIC", "*ELASTIC", "7000,0", "*SOLID SECTION,ELSET=BEAM,MATERIAL=ISOTROPIC",
              *node_set("FIXED", fixed), *node_set("ALLN", nodes), "*SURFACE,NAME=LOWER_CUT"]
    lines += [f"{tag},S2" for tag in lower]+["*SURFACE,NAME=UPPER_CUT"]+[f"{tag},S1" for tag in upper]
    for forces in loads:
        lines += ["*STEP", "*STATIC", "*BOUNDARY", "FIXED,1,3,0", "*CLOAD,OP=NEW"]
        lines += [f"{tag},3,{format_cload(force)}" for tag, force in forces.items() if force]
        lines += ["*NODE PRINT,NSET=FIXED", "RF", "*NODE PRINT,NSET=ALLN", "U",
                  "*SECTION PRINT,SURFACE=LOWER_CUT,NAME=LOWER", "SOF",
                  "*SECTION PRINT,SURFACE=UPPER_CUT,NAME=UPPER", "SOM", "*END STEP"]
    return "\n".join(lines)+"\n", {"nodes": nodes, "fixed": fixed, "loads": loads, "divisions": divisions}


def sections(data):
    pattern = r"statistics for surface set\s+(\w+) and time\s+(\S+)(.*?)(?=\n\s*statistics|\n\s*(?:forces|displacements)|\Z)"
    result = {}
    for name, time, body in re.findall(pattern, data, re.DOTALL):
        rows = [line.split() for line in body.splitlines() if re.match(r"\s*[+\-\d.]", line)]
        if list(map(len, rows)) != [6, 6, 3, 5]:
            raise ValueError("Incomplete native section statistics")
        values = [list(map(float, row)) for row in rows]
        if not all(math.isfinite(v) for row in values for v in row):
            raise ValueError("Nonfinite native section statistics")
        key = name, float(time)
        if key in result:
            raise ValueError("Duplicate section endpoint")
        result[key] = values
    return result


def audit(data, context):
    native, nodal = sections(data), blocks(data)
    if set(native) != {(name, time) for name in ("LOWER_CUT", "UPPER_CUT") for time in (1., 2.)}:
        raise ValueError("Missing exact native section endpoints")
    nodes = {int(tag): p for tag, p in context["nodes"].items()}
    results = []
    for time, load in enumerate(context["loads"], 1):
        applied = [(nodes[int(tag)], (0., 0., force)) for tag, force in load.items()]
        rf = nodal.get(("forces", "FIXED", float(time)), {})
        u = nodal.get(("displacements", "ALLN", float(time)), {})
        if set(rf) != set(context["fixed"]) or set(u) != set(nodes):
            raise ValueError("Incomplete nodal endpoint")
        external = applied+[(nodes[tag], force) for tag, force in rf.items()]
        balance = [sum(force[i] for _, force in external) for i in range(3)]
        torque = [sum(cross(point, force)[i] for point, force in external) for i in range(3)]
        exact = [sum(force[i] for _, force in applied) for i in range(3)]+[sum(cross(point, force)[i] for point, force in applied) for i in range(3)]
        compared = {}
        for name, sign in (("LOWER_CUT", 1), ("UPPER_CUT", -1)):
            output = native[name, float(time)]
            error = [a-sign*b for a, b in zip(output[0], exact, strict=True)]
            compared[name] = {"native_force_moment": output[0], "exact_force_moment": [sign*v for v in exact],
                              "error": error, "centroid_normal": output[1], "centroid_moment": output[2], "area_normal_shear": output[3]}
        results.append({"time": time, "external_force_residual_n": balance, "external_moment_residual_nmm": torque,
                        "external_balance_pass": max(map(abs, balance)) <= .001 and max(map(abs, torque)) <= .01,
                        "sections": compared})
    return results


def main():
    directory = Path(tempfile.mkdtemp(prefix="section-force-", dir="fea/generated"))
    (directory/"section_force_coupon.launch.py").write_bytes(Path(__file__).read_bytes())
    print(directory, flush=True)
    for divisions in (2, 4):
        text, context = deck(divisions)
        job = directory/f"section{divisions}"
        job.with_suffix(".inp").write_text(text)
        record = dict(context, deck_sha256=hashlib.sha256(text.encode()).hexdigest(),
                      source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                      helper_sha256={name: hashlib.sha256(Path(name).read_bytes()).hexdigest()
                                     for name in ("fea/floor_contact.py", "fea/floor_contact_results.py")},
                      status="RUNNING; HOMOGENEOUS C3D8 MIDMEMBER COUPON ONLY")
        job.with_suffix(".json").write_text(json.dumps(record, indent=2)+"\n")
        with job.with_suffix(".log").open("w") as log:
            try:
                run = subprocess.run(["ccx", "-i", job.name], cwd=directory, stdout=log, stderr=subprocess.STDOUT,
                                     timeout=25, check=False, env=dict(os.environ, OMP_NUM_THREADS="2"))
                record["exit_code"] = run.returncode
            except subprocess.TimeoutExpired:
                record["exit_code"] = -999
        record["status"] = "UNRESOLVED; NOT MEMBER OR CONNECTION VALIDATION"
        if record["exit_code"] == 0:
            try:
                if hashlib.sha256(job.with_suffix(".inp").read_bytes()).hexdigest() != record["deck_sha256"]:
                    raise ValueError("Launched deck changed")
                if "*ERROR" in job.with_suffix(".log").read_text().upper():
                    raise ValueError("Solver error in log")
                record["endpoints"] = audit(job.with_suffix(".dat").read_text(), context)
                record["status"] = "NATIVE SECTION DIAGNOSTIC; C3D10 AND INTERFACE ACCURACY NOT VALIDATED"
            except (ValueError, FileNotFoundError) as error:
                record["audit_error"] = str(error)
        record["output_sha256"] = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in directory.glob(job.name+".*")
                                   if p.suffix in (".dat", ".log", ".sta", ".cvg")}
        job.with_suffix(".json").write_text(json.dumps(record, indent=2, allow_nan=False)+"\n")
        print(job, record["status"], flush=True)


if __name__ == "__main__":
    main()
