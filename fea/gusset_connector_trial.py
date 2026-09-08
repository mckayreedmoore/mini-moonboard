"""Released gusset, point connectors and frozen parent motions: sensitivity only."""
import json
import math
import os
import subprocess
import tarfile
import tempfile
from pathlib import Path

import numpy as np

from fea.floor_contact import mesh, node_set
from fea.floor_contact_results import blocks, cross
from fea.gusset_recovery import ARCHIVE as PARENT
from fea.gusset_recovery import MAP
from fea.prescribed_tet_control import IMAGE
from fea.section_force_coupon import format_cload
from fea.solve_easy_frame import digest
from fea.timber_asymmetric import HOLDS, mesh_text, unchanged
from mini_moonboard import wide_frame as frame

OUTPUT = Path("fea/results/gusset-connector-trial.tar.gz")
STIFFNESSES = (100., 1000., 10000.)  # Numerical parameters, NOT measured wood/bolt properties.
GATES = {"force_n": .01, "moment_nmm": 1., "spring_force_error_n": .01,
         "rigid_motion_force_n": .001, "constraint_error_mm": 1e-7}


def point_weights(nodes, faces, yz):
    """Quadratic straight-triangle interpolation at the actual bolt-axis intercept."""
    for face in sorted(faces, key=lambda r: (r["element"], r["face"])):
        ids = face["nodes"]
        p = np.array([nodes[n] for n in ids])
        if np.ptp(p[:, 0]) > 1e-6:
            raise ValueError("Require a planar constant-X member interface")
        uv = np.linalg.solve((p[1:3, 1:]-p[0, 1:]).T, np.array(yz)-p[0, 1:])
        a, b, c = 1.-sum(uv), *uv
        if min(a, b, c) < -1e-9:
            continue
        weights = np.array([a*(2*a-1), b*(2*b-1), c*(2*c-1), 4*a*b, 4*b*c, 4*c*a])
        target = [float(p[0, 0]), *map(float, yz)]
        if abs(sum(weights)-1) > 1e-10 or np.max(abs(weights@p-target)) > 1e-7:
            raise ValueError("Point coupling loses affine displacement/moment consistency")
        return {"face_element": face["element"], "face": face["face"], "nodes": ids,
                "weights": weights.tolist(), "point_mm": target,
                "nearest_face_node_distance_mm": min(math.dist(target, q) for q in p)}
    raise ValueError("Bolt intercept is outside its intended member interface")


def prepare():
    with tarfile.open(PARENT) as archive:
        files = {m.name: archive.extractfile(m).read() for m in archive.getmembers()}
    report = json.loads(files["report.json"])
    import hashlib
    if set(files)-{"report.json"} != set(report["artifact_sha256"]):
        raise ValueError("Incomplete recovery archive")
    if any(hashlib.sha256(files[n]).hexdigest() != h for n, h in report["artifact_sha256"].items()):
        raise ValueError("Recovery artifacts changed")
    unchanged(report["source_sha256"])
    if not report["passed_numerical_gates"]:
        raise ValueError("Require accepted displacement recovery")
    mapping = json.loads(MAP.read_text())
    unchanged(mapping["source_sha256"])
    nodes, elements = mesh(files["A12-6.inp"].decode())
    bolts = {c.name: c for c in frame.connections()}
    points = {}
    for side, gusset in mapping["gussets"].items():
        for i in range(1, 5):
            name = f"timber_base_{side}_{i}"
            bolt = bolts[name]
            member = f"base_side_{side}" if i <= 2 else f"base_post_outer_{side}"
            if bolt.members != (member, f"timber_base_gusset_{side}"):
                raise ValueError("Bolt member ownership differs")
            points[name] = {**point_weights(nodes, gusset["interfaces"][member], (bolt.start.y, bolt.start.z)),
                            "side": side, "member": member}
    fields = []
    for hold in HOLDS:
        selected = json.loads(files[f"{hold}.selected.json"])
        for time, rows in sorted(selected.items()):
            values = {name: [math.fsum(w*rows[str(n)][axis] for n, w in zip(p["nodes"], p["weights"], strict=True))
                             for axis in range(3)] for name, p in points.items()}
            fields.append({"name": f"{hold}-{time}", "anchor_u_mm": values, "rigid_control": False})
    for rotation in (False, True):
        for axis in range(3):
            vector = [(.0001 if rotation else .01) if i == axis else 0. for i in range(3)]
            values = {n: cross(vector, p["point_mm"]) if rotation else vector for n, p in points.items()}
            fields.append({"name": f"rigid-{'rotation' if rotation else 'translation'}-{axis}",
                           "anchor_u_mm": values, "rigid_control": True})
    sources = {**report["source_sha256"], str(PARENT): digest(PARENT),
               "fea/section_force_coupon.py": digest("fea/section_force_coupon.py"),
               "fea/gusset_connector_trial.py": digest("fea/gusset_connector_trial.py")}
    return nodes, elements, points, fields, sources


def deck(nodes, elements, points, fields, stiffness):
    if stiffness not in STIFFNESSES:
        raise ValueError("Unplanned connector stiffness")
    nodes = dict(nodes)
    connections = {}
    for name, p in points.items():
        virtual, anchor = max(nodes)+1, max(nodes)+2
        nodes[virtual] = nodes[anchor] = p["point_mm"]
        connections[name] = {**p, "virtual": virtual, "anchor": anchor}
    lines = [mesh_text(nodes, elements), "*MATERIAL,NAME=MAT", "*ELASTIC", "7000.,0.3",
             "*SOLID SECTION,ELSET=TIMBER,MATERIAL=MAT"]
    eid = max(elements)
    for name, p in connections.items():
        for axis in range(1, 4):
            eid += 1
            lines += [f"*ELEMENT,TYPE=SPRING2,ELSET=SP{eid}", f"{eid},{p['virtual']},{p['anchor']}",
                      f"*SPRING,ELSET=SP{eid}", f"{axis},{axis}", f"{stiffness:.1f}", "*EQUATION", "7"]
            terms = [(p["virtual"], axis, 1.)]+[(n, axis, -w) for n, w in zip(p["nodes"], p["weights"], strict=True)]
            lines += [",".join(f"{n},{a},{w:.15g}" for n, a, w in terms[i:i+4]) for i in (0, 4)]
    lines += node_set("ALLN", nodes)+node_set("ANCHORS", [p["anchor"] for p in connections.values()])
    for field in fields:
        lines += ["*STEP", "*STATIC", "*BOUNDARY,OP=NEW"]
        loads = {}
        for name, p in connections.items():
            lines += [f"{p['anchor']},1,3,0."]
            # Equivalent eigen-displacement: .5*k*(u_point-u_parent)^2.
            # Fixed spring + distributed k*u_parent load retains its Hessian
            # and gradient, avoiding prescribed-anchor/MPC RHS behavior.
            for n, weight in zip(p["nodes"], p["weights"], strict=True):
                for axis, value in enumerate(field["anchor_u_mm"][name], 1):
                    loads[n, axis] = loads.get((n, axis), 0.)+weight*stiffness*value
        lines += ["*CLOAD,OP=NEW"]+[f"{n},{axis},{format_cload(value)}" for (n, axis), value in sorted(loads.items())]
        lines += ["*NODE PRINT,NSET=ALLN", "U", "*NODE PRINT,NSET=ANCHORS", "RF", "*END STEP"]
    return "\n".join(lines)+"\n", nodes, connections


def audit(data, nodes, connections, fields, stiffness):
    parsed = blocks(data)
    if set(parsed) != {(kind, name, float(t)) for t in range(1, len(fields)+1)
                       for kind, name in (("displacements", "ALLN"), ("forces", "ANCHORS"))}:
        raise ValueError("Incomplete connector output")
    result = []
    for time, field in enumerate(fields, 1):
        u, rf = parsed["displacements", "ALLN", float(time)], parsed["forces", "ANCHORS", float(time)]
        if set(u) != set(nodes) or set(rf) != {p["anchor"] for p in connections.values()}:
            raise ValueError("Incomplete connector node coverage")
        errors, spring_errors, forces = [], [], {}
        for name, p in connections.items():
            expected = [math.fsum(w*u[n][i] for n, w in zip(p["nodes"], p["weights"], strict=True)) for i in range(3)]
            errors += [math.dist(u[p["virtual"]], expected), math.hypot(*u[p["anchor"]])]
            expected_rf = [stiffness*(u[p["anchor"]][i]-u[p["virtual"]][i]) for i in range(3)]
            spring_errors.append(math.dist(expected_rf, rf[p["anchor"]]))
            # RF is only the fixed-spring contribution; add the eigen-load to
            # recover the total connector force ON the gusset, k*(u_parent-u).
            forces[name] = [rf[p["anchor"]][i]+stiffness*field["anchor_u_mm"][name][i] for i in range(3)]
        residuals = {}
        for side in ("left", "right"):
            names = [n for n, p in connections.items() if p["side"] == side]
            moments = [cross(connections[n]["point_mm"], forces[n]) for n in names]
            residuals[side] = [math.fsum(forces[n][i] for n in names) for i in range(3)]+[math.fsum(m[i] for m in moments) for i in range(3)]
        passed = (max(errors) <= GATES["constraint_error_mm"]
                  and max(spring_errors) <= GATES["spring_force_error_n"]
                  and all(max(map(abs, r[:3])) <= GATES["force_n"] and max(map(abs, r[3:])) <= GATES["moment_nmm"] for r in residuals.values()))
        if field["rigid_control"]:
            passed &= max(math.hypot(*v) for v in forces.values()) <= GATES["rigid_motion_force_n"]
        result.append({"case": field["name"], "connector_force_on_gusset_n": forces,
                       "residual_n_nmm": residuals, "maximum_constraint_error_mm": max(errors),
                       "maximum_spring_force_error_n": max(spring_errors), "passed": bool(passed)})
    return result


def run():
    if OUTPUT.exists():
        raise FileExistsError("Refusing to overwrite connector trial")
    nodes, elements, points, fields, sources = prepare()
    directory = Path(tempfile.mkdtemp(prefix="gusset-connectors-", dir="fea/generated")).resolve()
    report = {"source_sha256": sources, "image": IMAGE, "gates": GATES, "points": points,
              "fields": fields, "runs": {}, "limits": "Frozen bonded-parent motions, point springs, no header contact, no holes; NOT actual bolt demand or strength."}
    for k in STIFFNESSES:
        name = f"k{int(k)}"
        text, all_nodes, connections = deck(nodes, elements, points, fields, k)
        (directory/f"{name}.inp").write_text(text)
        command = ["docker", "run", "--rm", "--network=none", "--cpus=1", "--memory=1g",
                   "--read-only", "--tmpfs", "/tmp:rw,noexec,nosuid,size=64m", "--user", f"{os.getuid()}:{os.getgid()}",
                   "-e", "OMP_NUM_THREADS=1", "-v", f"{directory}:/work", "-w", "/work", IMAGE, "ccx", "-i", name]
        with (directory/f"{name}.log").open("w") as log:
            done = subprocess.run(command, stdout=log, stderr=subprocess.STDOUT, timeout=60, check=False)
        if done.returncode or "*ERROR" in (directory/f"{name}.log").read_text().upper():
            raise RuntimeError(f"Failed trial retained at {directory}")
        report["runs"][name] = audit((directory/f"{name}.dat").read_text(), all_nodes, connections, fields, k)
    unchanged(sources)
    report["passed"] = all(row["passed"] for rows in report["runs"].values() for row in rows)
    report["artifact_sha256"] = {p.name: digest(p) for p in directory.iterdir() if p.is_file()}
    (directory/"report.json").write_text(json.dumps(report, indent=2, allow_nan=False)+"\n")
    with tarfile.open(OUTPUT, "x:gz") as archive:
        for p in sorted(directory.iterdir()):
            archive.add(p, arcname=p.name)
    print(directory)
    print(json.dumps({k: [r["case"] for r in rows if not r["passed"]] for k, rows in report["runs"].items()}))


if __name__ == "__main__":
    run()
