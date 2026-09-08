"""Small eccentric two-C3D10-cube contact coupon; not frame qualification."""
import argparse
import hashlib
import json
import math
import os
import subprocess
from pathlib import Path

from fea.floor_contact import FACES, mesh, node_set
from fea.solve_bearing_frame import straight_mesh_volume

SOURCE = Path("fea/results/floor_contact/toy_quadratic.inp")
DIRECTORY = Path("fea/generated/panel-contact-coupon")
LIMITS = "Frictionless prescribed-motion contact coupon only; contact wrench audit pending; no frame or joint capacity"


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def deck(source_text, penalty=10000., increment=.25):
    if not math.isfinite(penalty) or penalty <= 0 or not math.isfinite(increment) or not 0 < increment <= .25:
        raise ValueError("Finite positive penalty and bounded increment required")
    displacement = .001
    original, upper_elements = mesh(source_text)
    upper_ids = {n for ids in upper_elements.values() for n in ids}
    upper = {n: original[n] for n in sorted(upper_ids)}
    volume, _ = straight_mesh_volume(upper, upper_elements)
    if len(upper_elements) != 6 or abs(volume-1e6) > 1e-6 or any(
            not 0 <= value <= 100 for point in upper.values() for value in point):
        raise ValueError("Require preserved six-tetrahedron 100mm cube")
    offset = max(upper)+1
    lower = {n+offset: (p[0], p[1], p[2]-100.) for n, p in upper.items()}
    element_offset = max(upper_elements)+1
    lower_elements = {e+element_offset: tuple(n+offset for n in ids) for e, ids in upper_elements.items()}
    nodes, elements = {**upper, **lower}, {**upper_elements, **lower_elements}
    floor = sorted(n for n, p in lower.items() if p[2] == -100.)
    top = sorted(n for n, p in upper.items() if p[2] == 100.)
    surfaces = {}
    for name, group in (("SLAVE", upper_elements), ("MASTER", lower_elements)):
        faces = [(e, face) for e, ids in group.items() for face, indices in enumerate(FACES, 1)
                 if all(nodes[ids[i]][2] == 0. for i in indices)]
        if len(faces) != 2:
            raise ValueError("Expected two conforming quadratic interface triangles per cube")
        surfaces[name] = faces
    lines = ["** "+LIMITS, "*NODE"]
    lines += [f"{n},"+",".join(f"{v:.15g}" for v in p) for n, p in nodes.items()]
    for name, group in (("UPPER", upper_elements), ("LOWER", lower_elements)):
        lines += [f"*ELEMENT,TYPE=C3D10,ELSET={name}"]
        lines += [f"{e},"+",".join(map(str, ids)) for e, ids in group.items()]
    for name, ids in (("UPPER", upper), ("LOWER", lower), ("SUPPORT", floor), ("TOP", top)):
        lines += node_set(name, sorted(ids))
    lines += ["*MATERIAL,NAME=WOOD", "*ELASTIC", "7000,0.3",
              "*SOLID SECTION,ELSET=UPPER,MATERIAL=WOOD", "*SOLID SECTION,ELSET=LOWER,MATERIAL=WOOD"]
    for name, faces in surfaces.items():
        lines += [f"*SURFACE,NAME={name},TYPE=ELEMENT", *[f"{e},S{f}" for e, f in faces]]
    lines += ["*SURFACE INTERACTION,NAME=CONTACT", "*SURFACE BEHAVIOR,PRESSURE-OVERCLOSURE=LINEAR",
              f"{penalty:g}", "** No friction law: frictionless contact",
              "*CONTACT PAIR,INTERACTION=CONTACT,TYPE=SURFACE TO SURFACE", "SLAVE,MASTER",
              "*BOUNDARY", "SUPPORT,1,3,0", "TOP,1,2,0", "*STEP,NLGEOM,INC=100",
              "*STATIC", f"{min(.05,increment):g},1,1e-6,{increment:g}", "*BOUNDARY"]
    prescribed = {n: -displacement*(1+nodes[n][0]/100.) for n in top}
    lines += [f"{n},3,3,{value:.15g}" for n, value in prescribed.items()]
    for name in ("UPPER", "LOWER", "SUPPORT", "TOP"):
        lines += [f"*NODE PRINT,NSET={name},FREQUENCY=1", "U" if name in ("UPPER", "LOWER") else "RF"]
    lines += ["*NODE FILE,FREQUENCY=1", "U,RF", "*CONTACT FILE,FREQUENCY=1", "CDIS,CSTR",
              "*CONTACT PRINT,FREQUENCY=1", "CDIS,CSTR,CNUM",
              "*CONTACT PRINT,SLAVE=SLAVE,MASTER=MASTER,FREQUENCY=1", "CF", "*END STEP"]
    return "\n".join(lines)+"\n", {"limits": LIMITS, "nodes": nodes, "upper": sorted(upper),
        "lower": sorted(lower), "support": floor, "top": top,
        "prescribed_top_z_mm": prescribed, "surfaces": surfaces,
        "volume_each_mm3": volume, "node_count": len(nodes), "element_count": len(elements),
        "penalty": penalty, "increment": increment, "modulus_mpa": 7000., "maximum_runtime_seconds": 60}


def prepare(penalty=10000., increment=.25, directory=None):
    directory = DIRECTORY if directory is None else Path(directory)
    if directory.exists():
        raise FileExistsError("Refusing to overwrite coupon preparation")
    sources = {str(p): digest(p) for p in (SOURCE, Path("fea/panel_contact_coupon.py"),
        Path("fea/floor_contact.py"), Path("fea/solve_bearing_frame.py"))}
    text, info = deck(SOURCE.read_text(), penalty, increment)
    info.update(source_sha256=sources, deck_sha256=hashlib.sha256(text.encode()).hexdigest())
    if any(digest(p) != sha for p, sha in sources.items()):
        raise ValueError("Coupon source changed during preparation")
    directory.mkdir(parents=True)
    (directory/"coupon.inp").write_text(text)
    (directory/"input.json").write_text(json.dumps(info, indent=2, allow_nan=False)+"\n")


def solve(directory=None):
    directory = DIRECTORY if directory is None else Path(directory)
    info_path = directory/"input.json"
    info = json.loads(info_path.read_text())
    if {p.name for p in directory.iterdir()} != {"input.json", "coupon.inp"}:
        raise FileExistsError("Refusing to overwrite coupon attempt")
    if not info.get("source_sha256") or any(digest(p) != sha for p, sha in info["source_sha256"].items()):
        raise ValueError("Coupon source changed")
    expected, _ = deck(SOURCE.read_text(), info["penalty"], info["increment"])
    if (digest(directory/"coupon.inp") != info["deck_sha256"] or
            (directory/"coupon.inp").read_text() != expected):
        raise ValueError("Prepared coupon deck differs")
    initial = digest(info_path)
    with (directory/"launch.json").open("x") as stream:
        json.dump({"input_sha256": initial, "deck_sha256": info["deck_sha256"],
                   "source_sha256": info["source_sha256"], "timeout_seconds": 60}, stream, indent=2)
    try:
        with (directory/"coupon.log").open("x") as stream:
            completed = subprocess.run(["ccx", "-i", "coupon"], cwd=directory,
                env={**os.environ, "OMP_NUM_THREADS": "2"}, stdout=stream,
                stderr=subprocess.STDOUT, timeout=60, check=False)
    except subprocess.TimeoutExpired as error:
        raise RuntimeError("Coupon timed out; attempt preserved") from error
    if completed.returncode or "*ERROR" in (directory/"coupon.log").read_text().upper():
        raise RuntimeError("Coupon solver failed; attempt preserved")
    if digest(info_path) != initial or any(digest(p) != sha for p, sha in info["source_sha256"].items()) or digest(directory/"coupon.inp") != info["deck_sha256"]:
        raise ValueError("Coupon inputs changed during solve")
    with (directory/"execution.json").open("x") as stream:
        json.dump({"status": "solver exited successfully; contact audit pending", "limits": LIMITS,
            "artifacts": {p.name: digest(p) for p in directory.iterdir() if p.name != "execution.json"}}, stream, indent=2)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("prepare", "solve"))
    parser.add_argument("--directory", type=Path, default=DIRECTORY)
    parser.add_argument("--penalty", type=float, choices=(10000., 100000.))
    parser.add_argument("--increment", type=float, choices=(.25, .125))
    args = parser.parse_args(argv)
    if args.command == "solve":
        if args.penalty is not None or args.increment is not None:
            parser.error("solve uses frozen input parameters; options belong to prepare")
        solve(args.directory)
    else:
        prepare(10000. if args.penalty is None else args.penalty,
                .25 if args.increment is None else args.increment, args.directory)


if __name__ == "__main__":
    main()
