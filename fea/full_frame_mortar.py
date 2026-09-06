"""Matched unrestrained-frame contact diagnostic; global balance is not validation."""
import argparse
import hashlib
import json
import math
import os
import shutil
import signal
import subprocess
import tempfile
import time
from pathlib import Path

from fea.floor_contact import (
    FACES,
    SOURCE,
    floor_faces,
    integrated_weights,
    mesh,
    node_set,
)
from fea.floor_contact import deck as original_deck
from fea.floor_contact_recovery import validate_context
from fea.floor_contact_results import blocks, cross

MU = .5
NORMAL_SLOPE = 10000.
TANGENT_SLOPE = 100.
INCREMENT = .25
GRAVITY_PER_MM3_N = 6e-10*9806.65
LOAD_N = 1200.


def mesh_digest(nodes, elements):
    return hashlib.sha256(json.dumps([nodes, elements], sort_keys=True, allow_nan=False).encode()).hexdigest()


def build_deck(nodes, elements, groups, top, formulation):
    if formulation not in ("penalty", "mortar"):
        raise ValueError("Formulation must be penalty or mortar")
    if not nodes or any(len(p) != 3 or not all(map(math.isfinite, p)) for p in nodes.values()):
        raise ValueError("Finite three-coordinate wood nodes required")
    if not elements or {n for ids in elements.values() for n in ids} != nodes.keys():
        raise ValueError("Mesh node/element coverage differs")
    if any(len(ids) != 10 or len(set(ids)) != 10 for ids in elements.values()):
        raise ValueError("Ten unique nodes per tetrahedron required")
    actual = floor_faces(nodes, elements)
    if groups != actual:
        raise ValueError("Contact patches must match actual complete floor faces")
    feet = {elements[e][i] for faces in actual.values() for e, f in faces for i in FACES[f-1]}
    if len(top) != 5 or len(set(top)) != 5 or not set(top) <= nodes.keys() or set(top) & feet:
        raise ValueError("Five distinct non-floor load nodes required")
    text, ground = original_deck(nodes, elements, actual, top, MU, NORMAL_SLOPE)
    supports = {name: [n for n, p in xyz.items() if p[2] == -100.] for name, xyz in ground.items()}
    if any(len(ids) != 4 for ids in supports.values()):
        raise ValueError("Each ground brick needs four bottom supports")
    sets = "\n".join(line for name, ids in supports.items() for line in node_set("BOTTOM_"+name, ids))+"\n"
    text = text.replace("*BOUNDARY\n", sets+"*BOUNDARY\n", 1)
    for name in ground:
        text = text.replace(f"GROUND_{name},1,3,0\n", f"BOTTOM_{name},1,3,0\n")
        text = text.replace(f"*NODE PRINT,NSET=GROUND_{name}\nRF\n", f"*NODE PRINT,NSET=GROUND_{name}\nU,RF\n")
    text = text.replace("*STATIC\n0.05,1,1e-6,0.1\n", "*STATIC\n0.25,1,1e-6,0.25\n")
    if formulation == "mortar":
        text = text.replace("TYPE=SURFACE TO SURFACE", "TYPE=MORTAR")
    else:
        contact = "*CONTACT PRINT\nCDIS,CSTR\n"
        contact += "".join(f"*CONTACT PRINT,SLAVE=SLAVE_{name},MASTER=MASTER_{name}\nCF,CFN,CFS\n" for name in ground)
        text = text.replace("*END STEP\n", contact+"*END STEP\n")
    return text, ground, supports


def verify_deck(text, record):
    if hashlib.sha256(text.encode()).hexdigest() != record["deck_sha256"]:
        raise ValueError("Launched deck digest differs")
    nodes = {int(n): p for n, p in record["wood_nodes"].items()}
    _, elements = mesh(text)
    if mesh_digest(nodes, elements) != record["wood_mesh_sha256"]:
        raise ValueError("Wood mesh differs from frozen launch context")
    groups = floor_faces(nodes, elements)
    if (record["mu"] != MU or record["normal_penalty_n_mm3"] != NORMAL_SLOPE or
            record["tangent_penalty_n_mm3"] != TANGENT_SLOPE or record["increment"] != INCREMENT):
        raise ValueError("Recorded contact or increment context differs")
    expected, ground, supports = build_deck(nodes, elements, groups, record["load_nodes"], record["formulation"])
    if text != expected:
        raise ValueError("Deck differs from intended mesh/materials/loads/boundaries/contact")
    recorded_ground = {name: {int(n): tuple(p) for n, p in xyz.items()} for name, xyz in record["ground_nodes"].items()}
    if recorded_ground != ground or record["bottom_nodes"] != supports:
        raise ValueError("Ground/support context differs from actual deck")
    return nodes, elements, groups, ground, supports


def audit(text, data, record):
    nodes, elements, groups, ground, supports = verify_deck(text, record)
    weights = {int(n): v for n, v in record["nodal_volume_mm3"].items()}
    if (weights.keys() != nodes.keys() or not all(map(math.isfinite, weights.values())) or
            not math.isfinite(sum(weights.values())) or sum(weights.values()) <= 0):
        raise ValueError("Invalid nodal gravity context")
    # Reintegrate the verified curved mesh; finite weights or matching total
    # volume alone cannot establish its deformed gravity moment. Requires Gmsh.
    expected_weights = integrated_weights(elements, nodes)
    if expected_weights.keys() != weights.keys() or any(
            not math.isclose(weights[n], expected_weights[n], rel_tol=1e-10, abs_tol=1e-8)
            for n in weights):
        raise ValueError("Nodal gravity weights differ from verified mesh integration")
    parsed, output = blocks(data), []
    for endpoint, load in ((1., 0.), (2., LOAD_N)):
        u = parsed.get(("displacements", "WOODN", endpoint), {})
        if u.keys() != nodes.keys():
            raise ValueError(f"Incomplete timber endpoint {endpoint}")
        positions = {n: tuple(a+b for a, b in zip(p, u[n], strict=True)) for n, p in nodes.items()}
        forces, patches = [], {}
        for name, xyz in ground.items():
            displacements = parsed.get(("displacements", "GROUND_"+name, endpoint), {})
            reactions = parsed.get(("forces", "GROUND_"+name, endpoint), {})
            if displacements.keys() != xyz.keys() or reactions.keys() != xyz.keys():
                raise ValueError(f"Incomplete ground {name} endpoint {endpoint}")
            if any(abs(v) > 1e-9 for n in supports[name] for v in displacements[n]):
                raise ValueError("Fixed noncontact bottom support moved")
            ground_positions = {n: tuple(a+b for a, b in zip(p, displacements[n], strict=True)) for n, p in xyz.items()}
            if not all(math.isfinite(v) for p in ground_positions.values() for v in p):
                raise ValueError("Nonfinite deformed ground positions")
            # Free master-node RF is not another external support in MORTAR.
            forces += [(ground_positions[n], reactions[n]) for n in supports[name]]
            total = [sum(reactions[n][i] for n in supports[name]) for i in range(3)]
            feet = {elements[e][i] for e, f in groups[name] for i in FACES[f-1]}
            patches[name] = {"bottom_reaction_n": total,
                             "approximate_horizontal_friction_diagnostic_pass": (total[2] >= -.1 and math.hypot(*total[:2]) <= MU*max(0., total[2])+.1),
                             "friction_qualification": "Initial-horizontal resultant diagnostic only; deforming master may tilt/warp, so this is neither a necessary deformed contact cone nor a local-law acceptance gate",
                             "wood_floor_z_displacement_mm": [min(u[n][2] for n in feet), max(u[n][2] for n in feet)],
                             "ground_master_displacement_mm": {n: displacements[n] for n in xyz if n not in supports[name]},
                             "maximum_ground_displacement_mm": max(math.hypot(*v) for v in displacements.values()),
                             "gap_qualification": "Wood Z displacement is not clearance against deforming master geometry; local gap remains unaudited"}
        forces += [(positions[n], (0., 0., -v*GRAVITY_PER_MM3_N)) for n, v in weights.items()]
        forces += [(positions[n], (0., 0., -load/5)) for n in record["load_nodes"]]
        residual_force = [sum(f[i] for _, f in forces) for i in range(3)]
        residual_moment = [sum(cross(p, f)[i] for p, f in forces) for i in range(3)]
        values = residual_force+residual_moment+[v for p in positions.values() for v in p]
        values += [v for patch in patches.values() for v in patch["bottom_reaction_n"]]
        if not all(map(math.isfinite, values)):
            raise ValueError("Nonfinite deformed equilibrium calculation")
        if max(map(abs, residual_force)) > .1 or max(map(abs, residual_moment)) > 1:
            raise ValueError(f"Deformed equilibrium failed at {endpoint}: {residual_force}, {residual_moment}")
        output.append({"time": endpoint, "load_n": load, "force_residual_n": residual_force,
                       "moment_residual_nmm": residual_moment, "patches": patches,
                       "maximum_loaded_node_displacement_mm": max(math.hypot(*u[n]) for n in record["load_nodes"])})
    return output


def save(path, record):
    temporary = path.with_suffix(".json.tmp")
    temporary.write_text(json.dumps(record, indent=2, allow_nan=False)+"\n")
    temporary.replace(path)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--formulation", choices=("penalty", "mortar"), required=True)
    parser.add_argument("--max-seconds", type=float, default=600.)
    args = parser.parse_args()
    if not math.isfinite(args.max_seconds) or args.max_seconds <= 0:
        parser.error("Positive finite runtime required")
    digest = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
    prepared = Path("fea/generated/floor-contact/input.json")
    info = json.loads(prepared.read_text())
    summary = json.loads(SOURCE.with_suffix(".json").read_text())
    validate_context(info, summary, digest(SOURCE))
    if summary["candidate"] != "2x8-foot100" or any(digest(Path(p)) != h for p, h in info["geometry_source_sha256"].items()):
        raise ValueError("Frozen frame identity or geometry changed")
    nodes, elements = mesh(SOURCE.read_text())
    if len(nodes) != 62020 or len(elements) != 32511:
        raise ValueError("Expected frozen 62020-node/32511-element timber mesh")
    groups = floor_faces(nodes, elements)
    weights = integrated_weights(elements, nodes)
    volume = sum(weights.values())
    centre = [sum(nodes[n][i]*v for n, v in weights.items())/volume for i in range(3)]
    if abs(volume/info["cad_volume_mm3"]-1) > .001 or math.dist(centre, info["cad_centre_mm"]) > 1:
        raise ValueError("Integrated mesh mass/centroid differs from CAD")
    text, ground, bottom = build_deck(nodes, elements, groups, summary["load_nodes"], args.formulation)
    parent = Path("fea/generated")
    parent.mkdir(parents=True, exist_ok=True)
    directory = Path(tempfile.mkdtemp(prefix="full-frame-"+args.formulation+"-", dir=parent))
    snapshot = directory/"launch_sources"
    snapshot.mkdir()
    sources = (Path(__file__), Path("fea/floor_contact.py"), Path("fea/floor_contact_recovery.py"), Path("fea/floor_contact_results.py"))
    for path in sources:
        shutil.copyfile(path, snapshot/path.name)
    job = directory/"frame"
    job.with_suffix(".inp").write_text(text)
    record = dict(info, formulation=args.formulation, mu=MU, normal_penalty_n_mm3=NORMAL_SLOPE,
                  tangent_penalty_n_mm3=TANGENT_SLOPE, increment=INCREMENT, wood_nodes=nodes,
                  ground_nodes=ground, bottom_nodes=bottom, load_nodes=summary["load_nodes"],
                  nodal_volume_mm3=weights, mesh_volume_mm3=volume, mesh_mass_kg=volume*600/1e9,
                  mesh_centre_mm=centre, deck_sha256=hashlib.sha256(text.encode()).hexdigest(),
                  wood_mesh_sha256=mesh_digest(nodes, elements),
                  prelaunch_sha256={str(p): digest(p) for p in (*sources, SOURCE, SOURCE.with_suffix(".json"), prepared)},
                  max_seconds=args.max_seconds, status="RUNNING; NO PHYSICAL ACCEPTANCE",
                  boundary_basis="Only12noncontact ground bottom SPCs; no timber guides/SPCs/springs/MPCs",
                  ground_basis="Three independent C3D8 bricks,E7000MPa,nu.3,depth100mm; compliant numerical ground,not identified flooring",
                  friction_audit_basis="Only approximate initial-horizontal resultant diagnostic; no deformed local-cone acceptance is claimed",
                  local_contact_status="NOT VALIDATED; mortar CONTACT FILE retained without penalty pointwise-law or CF assumptions")
    verify_deck(text, record)
    save(job.with_suffix(".json"), record)
    print(f"Evidence: {directory}", flush=True)
    started = time.monotonic()
    with job.with_suffix(".log").open("w") as log:
        process = subprocess.Popen(["ccx", "-i", job.name], cwd=directory, stdout=log,
                                   stderr=subprocess.STDOUT, start_new_session=True,
                                   env=dict(os.environ, OMP_NUM_THREADS="2"))
        try:
            record["exit_code"] = process.wait(timeout=args.max_seconds)
        except subprocess.TimeoutExpired:
            os.killpg(process.pid, signal.SIGKILL)
            process.wait()
            record["exit_code"] = -999
            record["runtime_stop"] = "Bounded timeout; not physical instability evidence"
    record["elapsed_seconds"] = time.monotonic()-started
    record["status"] = "UNRESOLVED SOLVER/OUTPUT; NO ACCEPTED FRAME SOLUTION"
    if record["exit_code"] == 0 and "*ERROR" not in job.with_suffix(".log").read_text().upper():
        try:
            record["endpoints"] = audit(job.with_suffix(".inp").read_text(), job.with_suffix(".dat").read_text(), record)
            record["status"] = "GLOBAL TWO-STEP DIAGNOSTIC CHECKS PASS; LOCAL CONTACT AND SENSITIVITIES NOT VALIDATED"
        except (ValueError, FileNotFoundError) as error:
            record["audit_error"] = str(error)
    record["output_sha256"] = {p.name: digest(p) for p in directory.iterdir() if p.suffix in (".dat", ".frd", ".log", ".sta", ".cvg")}
    save(job.with_suffix(".json"), record)
    print(record["status"], flush=True)


if __name__ == "__main__":
    main()
