"""Audit an output-only SOF extension without weakening the passing fixture gates."""

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import re

HERE = Path(__file__).resolve().parent
BASE = HERE.parent / "contact-mortar-c3d10-fullstep-attempt01"
BASE_PINS = {
    "input-freeze.json": "978f8e49e79d6569dc033595ce565ce8587e36c4c5845c5615f120582634e8b0",
    "execution.json": "a485410aada87d2e149b39ee77b78d3efcada065c833a0c7e91acf1a60312574",
    "verifier.py": "d86d98494241657b1f8dda8ea42d747dac851c2319b914458f520008bc3a572b",
    "verifier.json": "813b7b2e2613a1aea7f3026517ca0d5fefef099164f136ce42cc5ed9314b0d14",
}
HEADERS = [
    ("total surface force (fx,fy,fz) and moment about the origin(mx,my,mz)", 6),
    ("center of gravity and mean normal", 6),
    ("moment about the center of gravity(mx,my,mz)", 3),
    ("area, normal force (+ = tension), shear force (size), torque and bending moment (size)", 5),
]
SECTION_CARDS = (
    "*SECTION PRINT,SURFACE=SLAVE,NAME=SLAVE_IF,FREQUENCYF=1\nSOF\n"
    "*SECTION PRINT,SURFACE=MASTER,NAME=MASTER_IF,FREQUENCYF=1\nSOF\n"
)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require(condition, message):
    if not condition:
        raise ValueError(message)


def load_base():
    for name, digest in BASE_PINS.items():
        require(sha(BASE / name) == digest, f"Passing baseline changed: {name}")
    spec = importlib.util.spec_from_file_location("passing_fullstep_verifier", BASE / "verifier.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    require(module.read_json(BASE / "verifier.json")["status"] == "PASS_METHOD_FIXTURE",
            "Source fixture does not pass")
    require(module.audit()["status"] == "PASS_METHOD_FIXTURE",
            "Passing baseline no longer passes its immutable evidence audit")
    # All baseline mechanical and provenance gates execute on the new packet.
    module.HERE = HERE
    return module


def sections(path, v):
    """Parse complete section reports, keeping their native surface/time identities."""
    lines = [" ".join(line.split()) for line in path.read_text().splitlines() if line.strip()]
    reports = {}
    for i, line in enumerate(lines):
        match = re.fullmatch(r"statistics for surface set (\w+) and time (\S+)", line)
        if not match:
            continue
        surface, time = match[1], v.number(match[2])
        require(surface in {"SLAVE", "MASTER"}, "Unexpected section surface")
        require(time in {1.0, 2.0, 3.0}, "Unexpected section time")
        key = (surface, time)
        require(key not in reports, "Duplicate section report")
        vectors = []
        for j, (header, count) in enumerate(HEADERS):
            require(i + 2*j + 2 < len(lines), "Truncated section report")
            require(lines[i+2*j+1].replace(" ", "") == header.replace(" ", ""),
                    "Unexpected section report header")
            values = [v.number(token) for token in lines[i+2*j+2].split()]
            require(len(values) == count, "Wrong section component count")
            vectors.append(values)
        reports[key] = {"force": vectors[0][:3], "moment_origin": vectors[0][3:],
                        "centroid": vectors[1][:3], "normal": vectors[1][3:],
                        "moment_centroid": vectors[2], "area": vectors[3][0],
                        "normal_force": vectors[3][1], "shear": vectors[3][2],
                        "torque": vectors[3][3], "bending": vectors[3][4]}
    require(set(reports) == {(s, t) for s in ("SLAVE", "MASTER") for t in (1., 2., 3.)},
            "Missing section/time report")
    return reports


def audit_sections(case, v):
    folder, baseline = HERE / "output" / case, BASE / "output" / case
    original = (baseline / "coupon.inp").read_text()
    derived = (folder / "coupon.inp").read_text()
    require(derived.count(SECTION_CARDS) == 3 and
            derived.replace(SECTION_CARDS, "") == original, "Deck has changes beyond section output")
    require("*SURFACE,NAME=SLAVE,TYPE=ELEMENT\n1,S1\n2,S1\n" in original and
            "*SURFACE,NAME=MASTER,TYPE=ELEMENT\n11,S3\n12,S3\n" in original,
            "Two-face section inventory differs")
    nodes, parts, faces = v.mesh(folder / "coupon.inp")
    current = v.dat(folder / "coupon.dat", set(nodes))
    before = v.dat(baseline / "coupon.dat", set(nodes))
    require(current == before, "Output-only extension changed printed nodal U/RF")
    require(v.numeric_rows(folder / "coupon.sta", 7) == v.numeric_rows(baseline / "coupon.sta", 7),
            "Output-only extension changed accepted history")
    require(v.numeric_rows(folder / "coupon.cvg", 9) == v.numeric_rows(baseline / "coupon.cvg", 9),
            "Output-only extension changed convergence history")
    reports = sections(folder / "coupon.dat", v)
    for (surface, time), item in reports.items():
        sign = 1 if surface == "SLAVE" else -1
        force = 400.0 if time == 2 else 0.0
        limit = .01*force + .001
        require(v.norm(tuple(a-b for a,b in zip(item["force"], (0., 0., sign*force)))) <= limit,
                f"Section force disagrees with oracle: {surface}/{time}")
        require(v.norm(tuple(a-b for a,b in zip(item["moment_origin"],
                    (sign*force, -sign*force, 0.)))) <= .01*force + .001,
                "Section origin moment disagrees with oracle")
        require(v.norm(item["moment_centroid"]) <= .01*force + .001,
                "Section centroid moment disagrees with oracle")
        require(abs(item["area"]-4.) <= 1e-5, "Section area differs")
        require(v.norm(tuple(a-b for a,b in zip(item["normal"], (0., 0., -sign)))) <= 1e-5,
                "Section normal differs")
        face = faces["upper_interface" if surface == "SLAVE" else "lower_interface"]
        u = current[(time, "displacements")]
        center = tuple(sum(nodes[n][d]+u[n][d] for n in face)/len(face) for d in range(3))
        require(v.norm(tuple(a-b for a,b in zip(item["centroid"], center))) <= 1e-5,
                "Section centroid differs from uniform nodal geometry")
        require(abs(item["normal_force"]+force) <= limit, "Compression sign differs")
        require(abs(item["shear"]) <= limit, "Section shear differs")
        require(max(abs(item["torque"]), abs(item["bending"])) <= .01*force + .001,
                "Section torque/bending differs")
    for time in (1., 2., 3.):
        a, b = reports[("SLAVE", time)], reports[("MASTER", time)]
        limit = 4.001 if time == 2 else .001
        require(v.norm(tuple(x+y for x,y in zip(a["force"], b["force"]))) <= limit,
                "Opposite section force sum fails")
        require(v.norm(tuple(x+y for x,y in zip(a["moment_origin"], b["moment_origin"]))) <= limit,
                "Opposite section moment sum fails")
    return {"status": "PASS", "nodal_and_history_parity": True,
            "reports": [{"surface": s, "time": t, **item} for (s,t),item in reports.items()],
            "interpretation": "Bulk-stress section proxy; not exact contact traction at stress jumps"}


def audit():
    v = load_base()
    result = v.audit()
    require(result["status"] == "PASS_METHOD_FIXTURE", "Baseline mechanical/provenance gates fail")
    extensions = {}
    for case in sorted(v.CASES):
        try:
            extensions[case] = audit_sections(case, v)
        except Exception as exc:
            extensions[case] = {"status": "FAIL", "error": str(exc)}
    result["section_force_audits"] = extensions
    result["source_baseline_pins"] = BASE_PINS
    result["status"] = "PASS_SECTION_FORCE_FIXTURE" if all(
        item["status"] == "PASS" for item in extensions.values()) else "FAIL"
    result["verifier_sha256"] = sha(Path(__file__))
    result["execution_sha256"] = sha(HERE / "execution.json")
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    try:
        result = audit()
    except Exception as exc:
        result = {"status": "FAIL", "error": str(exc), "mechanical_acceptance": False,
                  "joint_acceptance": False, "release": False}
    if args.write:
        with (HERE / "verifier.json").open("x") as stream:
            json.dump(result, stream, indent=2, sort_keys=True)
            stream.write("\n")
    print(json.dumps({"status": result["status"], "error": result.get("error"),
                      "section_force_audits": {k: {a:b for a,b in val.items() if a in ("status", "error")}
                                               for k,val in result.get("section_force_audits", {}).items()}}))
    raise SystemExit(0 if result["status"] == "PASS_SECTION_FORCE_FIXTURE" else 1)
