"""Matched fixed-floor, no-gravity, ideal-bonded tied-base stiffness comparisons."""
import argparse
import hashlib
import json
import math
import os
import signal
import subprocess
import sys
import tarfile
import time
from pathlib import Path

from fea.box_results import parse_results
from fea.floor_contact import FACES, floor_faces, integrated_weights, mesh, node_set
from fea.floor_contact_results import blocks, cross
from fea.hybrid_results import deck_geometry, support_moments
from fea.user_load_envelope import hull

ROOT = Path("fea/generated/tied-base-bulk")
ASSUMPTIONS = "Fixed actual floor nodes XYZ; no gravity; six independent original row12 loads; isotropic E7000MPa nu0.3; all touching timber including rail/spacer interfaces IDEALLY BONDED by conformal mesh. No actual joint capacity or unanchored friction/sliding/tipping acceptance. Floating rails/spacers receive no floor support."


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def save(path, data):
    temporary = path.with_suffix(path.suffix+".tmp")
    temporary.write_text(json.dumps(data, indent=2, allow_nan=False)+"\n")
    temporary.replace(path)


def prepare(candidate):
    import cadquery as cq

    from mini_moonboard import tied_base
    from mini_moonboard.box_frame import HALF, point
    from mini_moonboard.export import _export_step
    from mini_moonboard.panel_grid import main_tnut_datums
    from mini_moonboard.stability import load_cases

    directory = ROOT/candidate
    if directory.exists():
        raise ValueError("Prepared candidate directory already exists")
    if candidate == "baseline":
        items, published = tied_base.baseline(), None
        cad = tied_base.state(items)
        contacts = []
        # Same complete CAD dependency set as the published tied variants.
        reference = json.loads(Path("exports/tied-base/z275/summary.json").read_text())
    else:
        height = int(candidate[1:])
        published = Path("exports/tied-base")/candidate
        reference = json.loads((published/"summary.json").read_text())
        if reference["candidate"] != f"2x8-foot100-tied-base-z{height}" or digest(published/"candidate.step") != reference["artifact_sha256"]["candidate.step"]:
            raise ValueError("Published tied-base identity/STEP mismatch")
        current = tied_base.inspect(height)
        if json.loads(json.dumps(current["candidate_state"])) != reference["candidate_state"]:
            raise ValueError("Published CAD state differs from current candidate")
        items, cad, contacts = tied_base.parts(height), current["candidate_state"], current["intended_face_contacts"]
    if any(digest(p) != h for p, h in reference["source_sha256"].items()):
        raise ValueError("Published geometry source hash changed")
    directory.mkdir(parents=True)
    step = directory/"geometry.step"
    if published:
        step.write_bytes((published/"candidate.step").read_bytes())
    else:
        assembly = cq.Assembly(name="2x8-foot100_UNDRILLED_BASELINE")
        for part in items:
            assembly.add(part.shape, name=part.name)
        _export_step(assembly, step)
    labels = ("A12", "C12", "F12", "H12", "K12")
    targets = [point(main_tnut_datums()[label][0]-HALF, main_tnut_datums()[label][1], -18).toTuple() for label in labels]
    info = {"candidate": candidate, "assumptions": ASSUMPTIONS, "cad": cad,
            "parts": {p.name: {"volume_mm3": p.shape.Volume(), "centre_mm": p.shape.Center().toTuple()} for p in items},
            "intended_face_contacts": contacts, "load_labels": labels, "load_targets_mm": targets,
            "load_cases": [{"name": c.name, "basis": c.basis, "force_n": [0, c.force_y_n, c.force_z_n]} for c in load_cases()],
            "geometry_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
            "geometry_source_sha256": reference["source_sha256"], "step_sha256": digest(step),
            "published_summary_sha256": digest(published/"summary.json") if published else None}
    save(directory/"input.json", info)
    print(directory, flush=True)


def bulk_deck(mesh_text, feet, top, cases):
    lines = ["** "+ASSUMPTIONS, mesh_text, *node_set("FEET", feet), *node_set("TOP", top),
             "*MATERIAL,NAME=WOOD_SCREEN", "*ELASTIC", "7000,0.3", "*SOLID SECTION,ELSET=TIMBER,MATERIAL=WOOD_SCREEN"]
    for case in cases:
        lines += ["** CASE "+case["name"], "*STEP", "*STATIC", "*BOUNDARY", "FEET,1,3,0", "*CLOAD,OP=NEW"]
        lines += [f"{n},{i},{force/len(top):.9f}" for n in top for i, force in enumerate(case["force_n"], 1) if force]
        lines += ["*NODE PRINT,NSET=TOP", "U", "*NODE PRINT,NSET=FEET,TOTALS=YES", "RF", "*NODE FILE", "U", "*END STEP"]
    return "\n".join(lines)+"\n"


def validate_mesh(nodes, elements, owners, info):
    if set(owners) != set(info["parts"]) or not all(owners.values()):
        raise ValueError("Incomplete part ownership")
    flat = [tag for tags in owners.values() for tag in tags]
    if len(flat) != len(set(flat)) or set(flat) != set(elements):
        raise ValueError("Element ownership is overlapping or incomplete")
    used = {n for ids in elements.values() for n in ids}
    if used != set(nodes):
        raise ValueError("Mesh has unused/missing nodes")
    parent = {n: n for n in nodes}

    def root(n):
        while parent[n] != n:
            parent[n] = parent[parent[n]]
            n = parent[n]
        return n

    for ids in elements.values():
        for n in ids[1:]:
            parent[root(n)] = root(ids[0])
    if len({root(n) for n in nodes}) != 1:
        raise ValueError("Fragmented timber is not one connected conformal assembly")
    part_nodes = {name: {n for e in tags for n in elements[e]} for name, tags in owners.items()}
    shared = []
    for row in info["intended_face_contacts"]:
        if row["area_mm2"] > .01:
            a, b = row["parts"]
            count = len(part_nodes[a] & part_nodes[b])
            if count < 6:
                raise ValueError("An intended bonded interface lacks shared quadratic nodes")
            shared.append({"parts": [a, b], "shared_nodes": count})
    groups = floor_faces(nodes, elements)
    feet = sorted({elements[e][i] for faces in groups.values() for e, face in faces for i in FACES[face-1]})
    if set(feet) != {n for n, p in nodes.items() if abs(p[2]) < 1e-5}:
        raise ValueError("Floor node and actual face selections differ")
    if any(set(feet) & ids for name, ids in part_nodes.items() if name.startswith("base_")):
        raise ValueError("Floating base members received floor support")
    polygon = hull([nodes[n][:2] for n in feet])
    expected = info["cad"]["support_polygon_mm"]
    if len(polygon) != len(expected) or any(math.dist(a, b) > .001 for a, b in zip(polygon, expected, strict=True)):
        raise ValueError("Meshed floor polygon differs from CAD")
    return feet, groups, shared


def audit_results(text, data, info, record):
    if hashlib.sha256(text.encode()).hexdigest() != record["deck_sha256"]:
        raise ValueError("Launched deck text changed")
    cases = [(c["name"], tuple(v/1200 for v in c["force_n"])) for c in info["load_cases"]]
    nodes, feet, top = deck_geometry(text, cases)
    if feet != record["floor_nodes"] or top != record["load_nodes"]:
        raise ValueError("Launched deck/sets changed")
    mesh_nodes, elements = mesh(text)
    actual_groups = floor_faces(mesh_nodes, elements)
    expected_groups = {name: sorted({elements[element][i] for element, face in faces
                                    for i in FACES[face-1]})
                       for name, faces in actual_groups.items()}
    if (record.get("floor_group_nodes") != expected_groups
            or set(feet) != {node for tags in expected_groups.values() for node in tags}):
        raise ValueError("Recorded floor patch nodes differ from actual deck faces")
    maxima, reactions = parse_results(data, cases)
    moments = support_moments(data, nodes, feet, top, cases)
    parsed = blocks(data)
    patches = []
    for endpoint, case in enumerate(info["load_cases"], 1):
        u = parsed.get(("displacements", "TOP", float(endpoint)), {})
        rf = parsed.get(("forces", "FEET", float(endpoint)), {})
        if set(u) != set(top) or set(rf) != set(feet):
            raise ValueError("Incomplete or wrong-time bulk endpoint")
        for name, ids in record["floor_group_nodes"].items():
            force = [sum(rf[n][i] for n in ids) for i in range(3)]
            moment = [sum(cross(nodes[n], rf[n])[i] for n in ids) for i in range(3)]
            patches.append({"case": case["name"], "group": name, "reaction_n": force, "reaction_moment_nmm": moment})
    return {"max_loaded_node_displacement_mm": maxima, "reaction_totals_n": reactions,
            "reaction_moments_nmm": moments, "floor_patch_reactions": patches}


def worker(directory):
    import gmsh

    directory = Path(directory)
    record = json.loads((directory/"run.json").read_text())
    prepared = directory.parent
    info = json.loads((prepared/"input.json").read_text())
    if digest(prepared/"geometry.step") != info["step_sha256"]:
        raise ValueError("Frozen STEP changed")
    gmsh.initialize()
    gmsh.option.setNumber("General.Verbosity", 2)
    gmsh.model.add("ideal_bonded_tied_base")
    shapes = gmsh.model.occ.importShapes(str(prepared/"geometry.step"))
    gmsh.model.occ.synchronize()
    names = [gmsh.model.getEntityName(dim, tag).split("/")[-1] for dim, tag in shapes]
    if len(names) != len(set(names)) or set(names) != set(info["parts"]):
        raise ValueError("STEP part labels differ from frozen inventory")
    for name, (dim, tag) in zip(names, shapes, strict=True):
        if dim != 3 or abs(gmsh.model.occ.getMass(dim, tag)/info["parts"][name]["volume_mm3"]-1) > 1e-6:
            raise ValueError("Imported STEP part volume differs from CAD")
    _, fragment_map = gmsh.model.occ.fragment(shapes[:1], shapes[1:])
    gmsh.model.occ.synchronize()
    volumes = [tag for _, tag in gmsh.model.getEntities(3)]
    gmsh.model.addPhysicalGroup(3, volumes, 1)
    gmsh.model.setPhysicalName(3, 1, "TIMBER")
    for option, value in (("Mesh.MeshSizeMax", record["mesh_size_mm"]), ("Mesh.MeshSizeMin", record["mesh_size_mm"]/5),
                          ("Mesh.MeshSizeFromCurvature", 0), ("Mesh.ElementOrder", 2)):
        gmsh.option.setNumber(option, value)
    gmsh.model.mesh.generate(3)
    gmsh.model.mesh.optimize("HighOrder")
    qualities = [float(q) for tags in gmsh.model.mesh.getElements(3)[1] for q in gmsh.model.mesh.getElementQualities(tags, "minDetJac")]
    if not qualities or not all(map(math.isfinite, qualities)) or min(qualities) <= 0:
        raise ValueError("Invalid quadratic Jacobian")
    owners = {name: [int(e) for dim, tag in entities if dim == 3 for tags in gmsh.model.mesh.getElements(3, tag)[1] for e in tags]
              for name, entities in zip(names, fragment_map, strict=True)}
    gmsh.write(str(directory/"mesh.inp"))
    gmsh_version = gmsh.__version__
    gmsh.finalize()
    nodes, elements = mesh((directory/"mesh.inp").read_text())
    feet, groups, shared = validate_mesh(nodes, elements, owners, info)
    weights = integrated_weights(elements, nodes)
    volume = sum(weights.values())
    centre = [sum(weights[n]*p[i] for n, p in nodes.items())/volume for i in range(3)]
    if abs(volume/info["cad"]["volume_mm3"]-1) > .001 or math.dist(centre, info["cad"]["centre_mm"]) > 1:
        raise ValueError("Integrated mesh mass/CG differs from CAD")
    top = sorted({min(nodes, key=lambda n: math.dist(nodes[n], target)) for target in info["load_targets_mm"]})
    if len(top) != 5 or set(top) & set(feet):
        raise ValueError("Five distinct non-floor load nodes required")
    targets = [{"label": label, "target_mm": target, "node": min(top, key=lambda n: math.dist(nodes[n], target))}
               for label, target in zip(info["load_labels"], info["load_targets_mm"], strict=True)]
    for row in targets:
        row.update(coordinates_mm=nodes[row["node"]], distance_mm=math.dist(nodes[row["node"]], row["target_mm"]))
    text = bulk_deck((directory/"mesh.inp").read_text(), feet, top, info["load_cases"])
    job = directory/"bulk"
    job.with_suffix(".inp").write_text(text)
    record.update(status="MESH VERIFIED; SOLVER RUNNING", gmsh_version=gmsh_version, min_jacobian=min(qualities),
                  node_count=len(nodes), element_count=len(elements), part_elements=owners, shared_interfaces=shared,
                  mesh_volume_mm3=volume, mesh_mass_kg=volume*600/1e9, mesh_centre_mm=centre,
                  nodal_volume_mm3=weights, floor_faces=groups, floor_nodes=feet, load_nodes=top, load_targets=targets,
                  floor_group_nodes={name: sorted({elements[e][i] for e, face in faces for i in FACES[face-1]}) for name, faces in groups.items()},
                  audit_node_coordinates_mm={n: nodes[n] for n in feet+top},
                  mesh_sha256=digest(directory/"mesh.inp"), deck_path=str(job.with_suffix(".inp")), deck_sha256=digest(job.with_suffix(".inp")))
    save(directory/"run.json", record)
    with job.with_suffix(".log").open("w") as log:
        result = subprocess.run(["ccx", "-i", job.name], cwd=directory, stdout=log, stderr=subprocess.STDOUT, check=False)
    record["solver_exit_code"] = result.returncode
    if result.returncode or "*ERROR" in job.with_suffix(".log").read_text().upper():
        raise ValueError("CalculiX failed; raw output retained")
    if digest(job.with_suffix(".inp")) != record["deck_sha256"]:
        raise ValueError("Launched deck file changed")
    record["audited_results"] = audit_results(text, job.with_suffix(".dat").read_text(), info, record)
    record["status"] = "SIX EQUILIBRIUM-AUDITED IDEAL-BONDED FIXED-FLOOR CASES; NOT UNANCHORED OR JOINT VALIDATION"
    record["output_sha256"] = {p.name: digest(p) for p in directory.iterdir() if p.suffix in (".inp", ".dat", ".log", ".sta", ".cvg", ".frd")}
    save(directory/"run.json", record)


def run(candidate, size, max_seconds):
    prepared = ROOT/candidate
    info = json.loads((prepared/"input.json").read_text())
    if info["candidate"] != candidate or any(digest(p) != h for p, h in info["geometry_source_sha256"].items()):
        raise ValueError("Frozen candidate identity/sources changed")
    directory = prepared/f"mesh{size:g}".replace(".", "p")
    directory.mkdir()  # Fresh job required; preserve every previous result.
    source = Path(__file__)
    (directory/"tied_base_bulk.launch.py").write_bytes(source.read_bytes())
    dependencies = [source, prepared/"input.json", prepared/"geometry.step", *map(Path, (
        "fea/box_results.py", "fea/floor_contact.py", "fea/floor_contact_results.py", "fea/hybrid_results.py", "fea/user_load_envelope.py"))]
    record = {"candidate": candidate, "assumptions": ASSUMPTIONS, "mesh_size_mm": size,
              "max_seconds": max_seconds, "status": "MESHING; NOT VALIDATED",
              "prelaunch_sha256": {str(p): digest(p) for p in dependencies}}
    save(directory/"run.json", record)
    print(f"Evidence: {directory}", flush=True)
    started = time.monotonic()
    with (directory/"worker.log").open("w") as log:
        process = subprocess.Popen([sys.executable, "-m", "fea.tied_base_bulk", "--worker", str(directory)],
                                   stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
        try:
            code = process.wait(timeout=max_seconds)
        except subprocess.TimeoutExpired:
            os.killpg(process.pid, signal.SIGKILL)
            process.wait()
            code = -999
    record = json.loads((directory/"run.json").read_text())
    record.update(worker_exit_code=code, elapsed_seconds=time.monotonic()-started)
    if code:
        record["status"] = "UNRESOLVED BOUNDED MESH/SOLVER/AUDIT RESULT; NO PHYSICAL ACCEPTANCE"
    record["worker_log_sha256"] = digest(directory/"worker.log")
    save(directory/"run.json", record)
    print(json.dumps({k: record[k] for k in ("candidate", "status", "elapsed_seconds", "worker_exit_code")}), flush=True)


def replay_archive(path):
    """Recheck published evidence without a solver, CAD libraries, or generated files."""
    with tarfile.open(path, "r:gz") as archive:
        contents = {member.name: archive.extractfile(member).read() for member in archive.getmembers() if member.isfile()}
    record, info = json.loads(contents["run.json"]), json.loads(contents["input.json"])
    if record.get("worker_exit_code") != 0 or record.get("solver_exit_code") != 0 or record["candidate"] != info["candidate"]:
        raise ValueError("Archived run did not complete normally with matching identity")
    checks = dict(record["output_sha256"])
    checks.update({"bulk.inp": record["deck_sha256"], "mesh.inp": record["mesh_sha256"], "geometry.step": info["step_sha256"]})
    for original, expected in record["prelaunch_sha256"].items():
        name = Path(original).name
        name = "tied_base_bulk.launch.py" if name == "tied_base_bulk.py" else name
        if name not in ("input.json", "geometry.step", "tied_base_bulk.launch.py"):
            name = "helpers/"+name
        checks[name] = expected
    if any(name not in contents or hashlib.sha256(contents[name]).hexdigest() != expected for name, expected in checks.items()):
        raise ValueError("Archived evidence hash mismatch")
    mesh_nodes, elements = mesh(contents["mesh.inp"].decode())
    owners = record["part_elements"]
    feet, groups, shared = validate_mesh(mesh_nodes, elements, owners, info)
    if feet != record["floor_nodes"] or shared != record["shared_interfaces"] or json.loads(json.dumps(groups)) != record["floor_faces"]:
        raise ValueError("Archived mesh selections differ from recorded context")
    text, data = contents["bulk.inp"].decode(), contents["bulk.dat"].decode()
    expected = bulk_deck(contents["mesh.inp"].decode(), feet, record["load_nodes"], info["load_cases"])
    if text != expected:
        raise ValueError("Archived deck differs from intended fixed-floor cases")
    result = audit_results(text, data, info, record)
    if result != record["audited_results"]:
        raise ValueError("Archived outputs differ from reported audit")
    return record, info


def publish():
    destination = Path("fea/results/tied_base_bulk")
    if destination.exists():
        raise ValueError("Published bulk evidence must not be overwritten")
    # Validate all terminal contexts before creating publication output.
    records = {}
    for candidate in ("baseline", "z100", "z275"):
        directory = ROOT/candidate/"mesh60"
        record = json.loads((directory/"run.json").read_text())
        if record.get("worker_exit_code") != 0 or record.get("solver_exit_code") != 0 or "audited_results" not in record:
            raise ValueError("All three comparison runs must have complete audited output")
        if any(digest(directory/name) != expected for name, expected in record["output_sha256"].items()):
            raise ValueError("Terminal raw output changed")
        records[candidate] = record
    destination.mkdir(parents=True)
    report = {"status": "MATCHED SIX-CASE 60MM IDEAL-BONDED FIXED-FLOOR STIFFNESS COMPARISON ONLY",
              "assumptions": ASSUMPTIONS,
              "limits": "Fixed floor already prevents foot spreading. Small stiffness changes cannot reject ties under free contact, establish sliding benefit, or select tie height. No actual rail-force/connection-demand extraction; one mesh size only.",
              "publisher_source_sha256": digest(Path(__file__)), "candidates": {}, "comparisons": []}
    for candidate, record in records.items():
        directory = ROOT/candidate/"mesh60"
        output = destination/candidate
        output.mkdir()
        archive_path = output/"evidence.tar.gz"
        with tarfile.open(archive_path, "x:gz") as archive:
            for name in ("mesh.inp", "bulk.inp", "bulk.dat", "bulk.frd", "bulk.log", "bulk.sta", "bulk.cvg", "worker.log", "run.json", "tied_base_bulk.launch.py"):
                archive.add(directory/name, arcname=name)
            for name in ("input.json", "geometry.step"):
                archive.add(directory.parent/name, arcname=name)
            for name in ("box_results.py", "floor_contact.py", "floor_contact_results.py", "hybrid_results.py", "user_load_envelope.py"):
                archive.add(Path("fea")/name, arcname="helpers/"+name)
        checked, info = replay_archive(archive_path)
        report["candidates"][candidate] = {"archive": str(archive_path.relative_to(destination)),
            "archive_sha256": digest(archive_path), "archive_bytes": archive_path.stat().st_size,
            "run_json_sha256": digest(directory/"run.json"), "input_json_sha256": digest(directory.parent/"input.json"),
            "node_count": checked["node_count"], "element_count": checked["element_count"], "min_jacobian": checked["min_jacobian"],
            "cad_mass_kg": info["cad"]["mass_kg"], "mesh_mass_kg": checked["mesh_mass_kg"], "mesh_centre_mm": checked["mesh_centre_mm"],
            "elapsed_seconds": checked["elapsed_seconds"], "load_targets": checked["load_targets"],
            "audited_results": checked["audited_results"]}
    for case in records["baseline"]["audited_results"]["max_loaded_node_displacement_mm"]:
        displacement = {name: r["audited_results"]["max_loaded_node_displacement_mm"][case] for name, r in records.items()}
        patches = {group: {name: next(row["reaction_n"] for row in r["audited_results"]["floor_patch_reactions"] if row["case"] == case and row["group"] == group)
                           for name, r in records.items()} for group in ("LEFT", "RIGHT", "KICKER")}
        report["comparisons"].append({"case": case, "max_loaded_node_displacement_mm": displacement,
            "change_from_baseline_percent": {name: (u/displacement["baseline"]-1)*100 for name, u in displacement.items() if name != "baseline"},
            "floor_patch_reaction_n": patches})
    save(destination/"report.json", report)
    print(destination/"report.json")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidate", choices=("baseline", "z100", "z275"), default="baseline")
    parser.add_argument("--prepare", action="store_true")
    parser.add_argument("--publish", action="store_true")
    parser.add_argument("--size", type=float, default=60)
    parser.add_argument("--max-seconds", type=float, default=600)
    parser.add_argument("--worker", help=argparse.SUPPRESS)
    args = parser.parse_args()
    if not all(math.isfinite(v) and v > 0 for v in (args.size, args.max_seconds)):
        parser.error("Positive finite mesh size and runtime required")
    if args.worker:
        worker(args.worker)
    elif args.publish:
        publish()
    elif args.prepare:
        prepare(args.candidate)
    else:
        run(args.candidate, args.size, args.max_seconds)


if __name__ == "__main__":
    main()
