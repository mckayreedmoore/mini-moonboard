"""Native section resultants on straight C3D10, not curved frame interfaces."""
import hashlib
import json
import math
import os
import subprocess
import tempfile
from collections import Counter
from pathlib import Path

from fea.floor_contact import FACES, node_set
from fea.floor_contact_results import cross
from fea.section_force_coupon import audit
from fea.section_force_coupon import deck as brick_deck
from fea.section_force_coupon import format_cload as force_token

TETS = ((0,1,2,6), (0,2,3,6), (0,3,7,6), (0,7,4,6), (0,4,5,6), (0,5,1,6))
EDGES = ((0,1), (1,2), (2,0), (0,3), (1,3), (2,3))


def verify_serialized_loads(text, context):
    loads, section = [], ""
    for line in text.splitlines():
        if line.startswith("*"):
            section = line.split(",")[0]
            if section == "*CLOAD":
                if line != "*CLOAD,OP=NEW":
                    raise ValueError("Independent load replacement required")
                loads.append({})
        elif section == "*CLOAD":
            tag, direction, token = line.split(",")
            if len(token) > 20 or direction != "3" or int(tag) in loads[-1]:
                raise ValueError("Invalid or overwidth CLOAD field")
            loads[-1][int(tag)] = float(token[:20])
    if len(loads) != 2:
        raise ValueError("Two independent serialized load cases required")
    resultants = []
    for actual, expected in zip(loads, context["loads"], strict=True):
        expected = {tag: value for tag,value in expected.items() if value}
        if actual.keys() != expected.keys() or any(not math.isfinite(value) or not math.isclose(value, expected[tag], rel_tol=1e-12, abs_tol=1e-12) for tag,value in actual.items()):
            raise ValueError("Serialized CLOAD differs from analytic nodal tractions")
        resultants.append([sum(actual.values())]+[sum(cross(context["nodes"][tag], (0.,0.,value))[axis] for tag,value in actual.items()) for axis in range(3)])
    for actual, expected in zip(resultants, ([120.,0.,0.,0.], [0.,0.,-1200.,0.]), strict=True):
        if any(abs(a-b) > 1e-8 for a,b in zip(actual, expected, strict=True)):
            raise ValueError("Serialized force/moment differs from benchmark")
    return resultants


def triangle_loads(points, stresses):
    """Exact integral of quadratic Ni times linear traction on a flat triangle.

    Corner Ni=Li(2Li-1); midside Nij=4LiLj. Barycentric polynomial integrals
    give A*(2si-sj-sk)/60 and A*(2si+2sj+sk)/15 respectively.
    This applies end loads, never integrates computed element stresses.
    """
    if len(points) != 3 or len(stresses) != 3 or any(len(p) != 3 for p in points):
        raise ValueError("Three triangle corners and traction samples required")
    if not all(math.isfinite(x) for p in points for x in p) or not all(map(math.isfinite, stresses)):
        raise ValueError("Finite triangle coordinates and tractions required")
    ab, ac = [[points[j][i]-points[0][i] for i in range(3)] for j in (1, 2)]
    area = math.hypot(*cross(ab, ac))/2
    if not math.isfinite(area) or area <= 0:
        raise ValueError("Nondegenerate finite triangle required")
    corner = [area*(3*stress-sum(stresses))/60 for stress in stresses]
    midside = [area*(2*stresses[i]+2*stresses[j]+stresses[k])/15 for i,j,k in ((0,1,2), (1,2,0), (2,0,1))]
    return corner+midside


def geometry_audit(nodes, elements, surfaces):
    faces = Counter(tuple(sorted(ids[i] for i in face)) for ids in elements.values() for face in FACES)
    if any(count not in (1, 2) for count in faces.values()):
        raise ValueError("Nonmanifold quadratic faces")
    jacobians = []
    for ids in elements.values():
        if len(set(ids)) != 10:
            raise ValueError("Ten unique tetrahedron nodes required")
        a, b, c, d = [nodes[tag] for tag in ids[:4]]
        ab, ac, ad = [[p[i]-a[i] for i in range(3)] for p in (b,c,d)]
        determinant = sum(x*y for x,y in zip(cross(ab, ac), ad, strict=True))
        if not math.isfinite(determinant) or determinant <= 0:
            raise ValueError("Nonpositive straight-tetrahedron Jacobian")
        jacobians.append(determinant)
        for mid, (i, j) in zip(ids[4:], EDGES, strict=True):
            if nodes[mid] != tuple((nodes[ids[i]][axis]+nodes[ids[j]][axis])/2 for axis in range(3)):
                raise ValueError("This benchmark requires straight quadratic midsides")
    result = {"minimum_jacobian": min(jacobians), "volume_mm3": sum(jacobians)/6,
              "node_count": len(nodes), "element_count": len(elements), "surfaces": {}}
    selected = {}
    for name, items in surfaces.items():
        keys, area = [], 0.
        z = 100. if name == "TOP" else 50.
        for element, face in items:
            ids = [elements[element][i] for i in FACES[face-1]]
            if any(nodes[node][2] != z for node in ids):
                raise ValueError("Section/end face is not on its declared plane")
            key = tuple(sorted(ids))
            if faces[key] != (1 if name == "TOP" else 2):
                raise ValueError("Wrong internal/external face selection")
            keys.append(key)
            a, b, c = [nodes[node] for node in ids[:3]]
            area += math.hypot(*cross([b[i]-a[i] for i in range(3)], [c[i]-a[i] for i in range(3)]))/2
        if len(set(keys)) != len(keys) or not math.isclose(area, 100., abs_tol=1e-9, rel_tol=0):
            raise ValueError("Incomplete or duplicated section area")
        selected[name] = set(keys)
        result["surfaces"][name] = {"face_count": len(keys), "area_mm2": area}
    if selected["LOWER_CUT"] != selected["UPPER_CUT"]:
        raise ValueError("Opposed sections must select the identical quadratic interface")
    if not math.isclose(result["volume_mm3"], 10000., abs_tol=1e-8, rel_tol=0):
        raise ValueError("Wrong analytic beam volume")
    return result


def deck(divisions):
    source, original = brick_deck(divisions)
    nodes = dict(original["nodes"])
    element_block = source.split("*ELEMENT,TYPE=C3D8,ELSET=BEAM\n", 1)[1].split("*", 1)[0]
    bricks = [[int(value) for value in line.split(",")[1:]] for line in element_block.splitlines()]
    elements, midpoints = {}, {}
    for brick in bricks:
        for tet in TETS:
            corners = [brick[i] for i in tet]
            mids = []
            for i, j in EDGES:
                edge = tuple(sorted((corners[i], corners[j])))
                if edge not in midpoints:
                    tag = len(nodes)+1
                    nodes[tag] = tuple((nodes[edge[0]][axis]+nodes[edge[1]][axis])/2 for axis in range(3))
                    midpoints[edge] = tag
                mids.append(midpoints[edge])
            elements[len(elements)+1] = corners+mids
    surfaces = {name: [] for name in ("LOWER_CUT", "UPPER_CUT", "TOP")}
    for element, ids in elements.items():
        for face, indices in enumerate(FACES, 1):
            z = [nodes[ids[i]][2] for i in indices]
            if all(value == 100. for value in z):
                surfaces["TOP"].append((element, face))
            elif all(value == 50. for value in z):
                name = "LOWER_CUT" if sum(nodes[node][2] for node in ids[:4])/4 < 50. else "UPPER_CUT"
                surfaces[name].append((element, face))
    geometry = geometry_audit(nodes, elements, surfaces)
    fixed = [tag for tag,p in nodes.items() if p[2] == 0.]
    top = [tag for tag,p in nodes.items() if p[2] == 100.]
    loads = []
    for bending in (False, True):
        forces = dict.fromkeys(top, 0.)
        for element, face in surfaces["TOP"]:
            ids = [elements[element][i] for i in FACES[face-1]]
            corners = [nodes[tag] for tag in ids[:3]]
            stresses = [(1200/(10*10**3/12))*point[0] if bending else 1.2 for point in corners]
            for tag, force in zip(ids, triangle_loads(corners, stresses), strict=True):
                forces[tag] += force
        loads.append(forces)
    lines = ["*HEADING", "STRAIGHT C3D10 NATIVE MIDSECTION BENCHMARK", "*NODE"]
    lines += [f"{tag},"+",".join(map(str, p)) for tag,p in nodes.items()]
    lines += ["*ELEMENT,TYPE=C3D10,ELSET=BEAM"]+[f"{tag},"+",".join(map(str, ids)) for tag,ids in elements.items()]
    lines += ["*MATERIAL,NAME=ISOTROPIC", "*ELASTIC", "7000,0", "*SOLID SECTION,ELSET=BEAM,MATERIAL=ISOTROPIC",
              *node_set("FIXED", fixed), *node_set("ALLN", nodes)]
    for name in ("LOWER_CUT", "UPPER_CUT"):
        lines += [f"*SURFACE,NAME={name}"]+[f"{element},S{face}" for element,face in surfaces[name]]
    for forces in loads:
        lines += ["*STEP", "*STATIC", "*BOUNDARY", "FIXED,1,3,0", "*CLOAD,OP=NEW"]
        lines += [f"{tag},3,{force_token(force)}" for tag,force in forces.items() if force]
        lines += ["*NODE PRINT,NSET=FIXED", "RF", "*NODE PRINT,NSET=ALLN", "U",
                  "*SECTION PRINT,SURFACE=LOWER_CUT,NAME=LOWER", "SOF",
                  "*SECTION PRINT,SURFACE=UPPER_CUT,NAME=UPPER", "SOM", "*END STEP"]
    text = "\n".join(lines)+"\n"
    context = {"nodes": nodes, "elements": elements, "fixed": fixed,
               "loads": loads, "divisions": divisions, "surfaces": surfaces, "geometry": geometry}
    context["serialized_load_resultants_fz_mxyz"] = verify_serialized_loads(text, context)
    return text, context


def main():
    directory = Path(tempfile.mkdtemp(prefix="section-force-tet-", dir="fea/generated"))
    sources = (Path(__file__), *map(Path, ("fea/section_force_coupon.py", "fea/floor_contact.py", "fea/floor_contact_results.py")))
    snapshot = directory/"launch_sources"
    snapshot.mkdir()
    hashes = {}
    for path in sources:
        content = path.read_bytes()
        (snapshot/path.name).write_bytes(content)
        hashes[str(path)] = hashlib.sha256(content).hexdigest()
    print(directory, flush=True)
    for n in (2, 4):
        text, context = deck(n)
        job = directory/f"tet{n}"
        job.with_suffix(".inp").write_text(text)
        record = dict(context, deck_sha256=hashlib.sha256(text.encode()).hexdigest(), source_sha256=hashes,
                      status="RUNNING; STRAIGHT C3D10 BENCHMARK ONLY", max_seconds=60)
        job.with_suffix(".json").write_text(json.dumps(record, indent=2, allow_nan=False)+"\n")
        with job.with_suffix(".log").open("w") as log:
            try:
                result = subprocess.run(["ccx", "-i", job.name], cwd=directory, stdout=log, stderr=subprocess.STDOUT,
                                        timeout=60, check=False, env=dict(os.environ, OMP_NUM_THREADS="2"))
                record["exit_code"] = result.returncode
            except subprocess.TimeoutExpired:
                record["exit_code"] = -999
        record["status"] = "UNRESOLVED; NO MEMBER OR CONNECTION VALIDATION"
        if record["exit_code"] == 0:
            try:
                if hashlib.sha256(job.with_suffix(".inp").read_bytes()).hexdigest() != record["deck_sha256"] or "*ERROR" in job.with_suffix(".log").read_text().upper():
                    raise ValueError("Changed deck or solver log error")
                record["endpoints"] = audit(job.with_suffix(".dat").read_text(), context)
                record["status"] = "NATIVE STRAIGHT C3D10 MIDMEMBER DIAGNOSTIC; CURVED FRAME AND JOINTS NOT VALIDATED"
            except (ValueError, FileNotFoundError) as error:
                record["audit_error"] = str(error)
        record["output_sha256"] = {path.name: hashlib.sha256(path.read_bytes()).hexdigest() for path in directory.glob(job.name+".*") if path.suffix in (".dat", ".log", ".sta", ".cvg")}
        job.with_suffix(".json").write_text(json.dumps(record, indent=2, allow_nan=False)+"\n")
        print(job, record["status"], flush=True)


if __name__ == "__main__":
    main()
