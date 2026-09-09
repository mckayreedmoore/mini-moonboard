"""Prepare, but do not solve, the archived spread frame with unpinned floor contact."""
import argparse
import hashlib
import json
import math
import tarfile
from pathlib import Path

from fea import floor_contact as floor
from fea import lumber_leg_response as response
from fea.user_load_envelope import GRAVITY, LB_KG

ARCHIVE = Path("fea/results/spread-leg-response/2x6-e300-m40-E7000.tar.gz")
LIMITS = ("UNSOLVED contact preparation only; original spread wood and assumed connector stiffness; "
          "no hardware-trial transfer, bracing, calibrated friction, joint resistance or approval.")


def authenticated_input(path):
    with tarfile.open(path) as archive:
        members = archive.getmembers()
        if any(not m.isfile() for m in members) or len({m.name for m in members}) != len(members):
            raise ValueError("Require unique regular archive files")
        files = {m.name: archive.extractfile(m).read() for m in members}
    report = json.loads(files["report.json"])
    if set(report["artifact_sha256"]) != set(files)-{"report.json"} or any(
            hashlib.sha256(files[name]).hexdigest() != sha
            for name, sha in report["artifact_sha256"].items()):
        raise ValueError("Archive artifact identity differs")
    response.unchanged(report["source_sha256"])
    if (report["geometry"], report["stock"], report["extension_mm"], report["mesh_size_mm"],
            report["leg_modulus_mpa"]) != ("spread-100x50-top150", "2x6", 300., 40., 7000.):
        raise ValueError("Require the frozen 2x6/e300/m40/E7000 spread candidate")
    if not report["passed"] or report["qualified_for_design"]:
        raise ValueError("Require accepted numerical evidence, not a qualification claim")
    value = json.loads(files["input.json"])
    value["nodes"] = {int(n): p for n, p in value["nodes"].items()}
    value["elements"] = {int(e): ids for e, ids in value["elements"].items()}
    return files, report, value


def prepare(mu=.2, stiffness=1000., normal_penalty=100., archive=ARCHIVE):
    if not math.isfinite(mu) or not 0 < mu <= 1:
        raise ValueError("Require finite 0 < mu <= 1")
    if stiffness not in response.base.STIFFNESSES:
        raise ValueError("Require an archived connector stiffness")
    if not math.isfinite(normal_penalty) or normal_penalty <= 0:
        raise ValueError("Require positive finite normal contact penalty")
    files, report, value = authenticated_input(archive)
    nodes, elements = value["nodes"], value["elements"]
    original, context = response.deck(nodes, elements, value["points"], value["cases"],
                                      stiffness, value["legs"], report["leg_modulus_mpa"])
    if original != files[f"k{int(stiffness)}.inp"].decode():
        raise ValueError("Archived deck does not replay from mapped input")
    # Preserve all solids, spring elements and interpolation equations; discard
    # the original fixed-floor steps entirely, not just their load cards.
    prefix = original.split("*STEP\n", 1)[0]
    prefix = prefix.split("\n", 1)[1]  # Remove the predecessor's fixed-floor caption.
    prefix = prefix.replace("*SOLID SECTION", "*DENSITY\n6e-10\n*SOLID SECTION")
    lines = ["** "+LIMITS, prefix]
    groups = floor.floor_faces(nodes, elements)
    for side in ("left", "right"):
        actual = {elements[e][i] for e, f in groups[side.upper()] for i in floor.FACES[f-1]}
        if actual != set(value["legs"][side]["floor_nodes"]):
            raise ValueError("Floor faces do not match archived leg floor ownership")
    covered = {elements[e][i] for faces in groups.values() for e, f in faces for i in floor.FACES[f-1]}
    if covered != set(context["feet"]):
        raise ValueError("Incomplete floor face coverage")
    ground, bottom = {}, {}
    next_node = max(context["nodes"])+1
    # response.deck appends three SPRING2 elements per connector.
    next_element = max(elements)+3*len(context["connections"])+1
    for index, (name, faces) in enumerate(groups.items()):
        xyz = [nodes[elements[e][i]] for e, f in faces for i in floor.FACES[f-1]]
        x0, x1 = min(p[0] for p in xyz)-100, max(p[0] for p in xyz)+100
        y0, y1 = min(p[1] for p in xyz)-100, max(p[1] for p in xyz)+100
        corners = [(x0,y0,-100), (x1,y0,-100), (x1,y1,-100), (x0,y1,-100),
                   (x0,y0,0), (x1,y0,0), (x1,y1,0), (x0,y1,0)]
        ids = list(range(next_node+index*8, next_node+(index+1)*8))
        ground[name] = dict(zip(ids, corners, strict=True))
        bottom[name] = ids[:4]
        eid = next_element+index
        lines += ["*NODE"]+[f"{n},"+",".join(map(str,p)) for n,p in ground[name].items()]
        lines += [f"*ELEMENT,TYPE=C3D8,ELSET=GROUND_{name}", f"{eid},"+",".join(map(str,ids)),
                  f"*SOLID SECTION,ELSET=GROUND_{name},MATERIAL=GROUND",
                  *floor.node_set("GROUND_"+name, ids), *floor.node_set("BOTTOM_"+name, ids[:4]),
                  f"*SURFACE,NAME=MASTER_{name}",
                  f"{eid},S2", f"*SURFACE,NAME=SLAVE_{name}"]
        lines += [f"{e},S{f}" for e,f in faces]
        lines += ["*CONTACT PAIR,INTERACTION=FLOOR,TYPE=MORTAR",
                  f"SLAVE_{name},MASTER_{name}"]
    targets = {c["node"] for c in value["cases"] if c["hold"] == "A12"}
    if len(targets) != 1:
        raise ValueError("Require one authenticated A12 load target")
    target = targets.pop()
    force = [0., 300., -250*2*LB_KG*GRAVITY]
    lines += ["*MATERIAL,NAME=GROUND", "*ELASTIC", "7000,0.3",
              "*SURFACE INTERACTION,NAME=FLOOR", "*SURFACE BEHAVIOR,PRESSURE-OVERCLOSURE=LINEAR",
              str(normal_penalty), "*FRICTION", f"{mu},{normal_penalty/100}",
              *floor.node_set("WOODN", sorted(context["nodes"])), "*BOUNDARY"]
    lines += [f"BOTTOM_{name},1,3,0" for name in ground]
    for loaded in (False, True):
        lines += ["*STEP,NLGEOM,INC=200", "*STATIC", "0.05,1,1e-6,0.1",
                  "*DLOAD,OP=NEW", "TIMBER,GRAV,9806.65,0,0,-1"]
        if loaded:
            lines += ["*CLOAD,OP=NEW"]+[f"{target},{i},{f:.12g}" for i,f in enumerate(force, 1) if f]
        lines += ["*NODE PRINT,NSET=WOODN", "U", "*NODE PRINT,NSET=WOODN", "RF"]
        for name in ground:
            lines += [f"*NODE PRINT,NSET=GROUND_{name}", "U,RF"]
        lines += ["*CONTACT FILE", "CDIS,CSTR", "*NODE FILE", "U", "*END STEP"]
    text = "\n".join(lines)+"\n"
    sources = dict(report["source_sha256"])
    for path in ("fea/spread_floor_contact.py", "fea/floor_contact.py", "fea/user_load_envelope.py",
                 "fea/full_frame_mortar.py"):
        sources[path] = response.digest(path)
    record = {"limits": LIMITS, "solved": False, "qualified_for_design": False,
              "archive": str(archive), "archive_sha256": response.digest(archive),
              "parent_report": report, "source_sha256": sources, "image": report["image"],
              "mu": mu, "connector_stiffness_n_mm": stiffness,
              "normal_penalty_n_mm3": normal_penalty, "density_tonne_mm3": 6e-10,
              "load": {"hold": "A12", "node": target, "climber_lb": 250,
                       "weight_factor": 2, "force_n": force},
              "floor_faces": groups, "ground_nodes": ground, "bottom_nodes": bottom,
              "formulation": "mortar", "tangent_penalty_n_mm3": normal_penalty/100,
              "connector_context": context, "mapped_input": value,
              "deck_sha256": hashlib.sha256(text.encode()).hexdigest()}
    return text, record


def write(directory, **settings):
    text, record = prepare(**settings)
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=False)
    (directory/"contact.inp").write_text(text)
    (directory/"input.json").write_text(json.dumps(record, allow_nan=False)+"\n")
    return directory


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--mu", type=float, default=.2)
    parser.add_argument("--stiffness", type=float, default=1000.)
    parser.add_argument("--normal-penalty", type=float, default=100.)
    args = parser.parse_args()
    print(write(args.output, mu=args.mu, stiffness=args.stiffness, normal_penalty=args.normal_penalty))
