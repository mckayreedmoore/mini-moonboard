"""Conditional fixed-bore leg compliance, not physical bolt/contact or capacity."""
import hashlib
import json
import math
import os
import re
import subprocess
import tarfile
import tempfile
from pathlib import Path

from fea.floor_contact import mesh, node_set
from fea.floor_contact_results import blocks
from fea.independent_ply_control import resultant
from fea.section_force_coupon import format_cload

# Predeclared before the profile solver runs. Mesh change is a comparison gate,
# not a physical allowable. No stress/strength or buckling acceptance is defined.
GATES = {"force_n": .001, "moment_nmm": .01, "fixed_displacement_mm": 1e-9,
         "unloaded_displacement_mm": 1e-9, "relative_mesh_compliance": .05,
         "relative_energy_work": .001, "unloaded_energy_nmm": 1e-10}


def deck(source, metadata, independent):
    if hashlib.sha256(source.encode()).hexdigest() != metadata["mesh_sha256"]:
        raise ValueError("Prepared mesh digest differs")
    nodes, elements = mesh(source)
    owners = metadata["part_elements"]
    if set(owners) != {"inner", "outer"} or set(owners["inner"]) & set(owners["outer"]) or set(owners["inner"]+owners["outer"]) != set(elements):
        raise ValueError("Invalid ply element ownership")
    ply_nodes = {name: {n for e in ids for n in elements[e]} for name, ids in owners.items()}
    shared = ply_nodes["inner"] & ply_nodes["outer"]
    if shared != set(metadata["shared_interface_nodes"]) or any(ply_nodes[name] != set(metadata["part_nodes"][name]) for name in owners):
        raise ValueError("Invalid interface/node ownership")
    duplicate = {n: max(nodes)+i+1 for i, n in enumerate(sorted(shared))} if independent else {}
    nodes.update({new: nodes[old] for old, new in duplicate.items()})
    for e in owners["outer"]:
        elements[e] = [duplicate.get(n, n) for n in elements[e]]
    plies = {}
    for name in owners:
        remap = (lambda n: duplicate.get(n, n)) if name == "outer" else (lambda n: n)
        ids = {n for e in owners[name] for n in elements[e]}
        fixed = {remap(n) for hole in metadata["bore_nodes"][name] for n in hole}
        if len(metadata["bore_nodes"][name]) != 4 or any(not hole for hole in metadata["bore_nodes"][name]):
            raise ValueError("Four complete bore fixtures required")
        weights = {remap(int(n)): w for n, w in metadata["floor"][name]["weights_mm2"].items()}
        if not fixed or not weights or not fixed <= ids or not set(weights) <= ids or fixed & set(weights):
            raise ValueError("Invalid fixed bore/floor selection")
        if not all(math.isfinite(w) and w >= 0 for w in weights.values()) or sum(weights.values()) <= 0:
            raise ValueError("Invalid planar floor weights")
        plies[name] = {"nodes": sorted(ids), "fixed": sorted(fixed), "weights_mm2": weights}
    if independent and set(plies["inner"]["nodes"]) & set(plies["outer"]["nodes"]):
        raise ValueError("Independent plies share nodes")
    fixed = sorted({n for p in plies.values() for n in p["fixed"]})
    lines = ["*HEADING", "CONDITIONAL FIXED BORE PROFILE COMPLIANCE ONLY", "*NODE"]
    lines += [f"{n},"+",".join(map(str, p)) for n, p in nodes.items()]
    lines += ["*ELEMENT,TYPE=C3D10,ELSET=TIMBER"]+[f"{e},"+",".join(map(str, ns)) for e, ns in elements.items()]
    for name, ids in owners.items():
        lines += [line.replace("NSET", "ELSET") for line in node_set(name.upper(), ids)]
    lines += ["*MATERIAL,NAME=GENERIC", "*ELASTIC", "7000,0.3", "*SOLID SECTION,ELSET=TIMBER,MATERIAL=GENERIC",
              *node_set("ALLN", nodes), *node_set("FIXED", fixed)]
    cases = []
    for sharing in (["symmetric", "inner_only", "outer_only"] if independent else ["composite"]):
        for axis in range(3):
            loads = {}
            for name, ply in plies.items():
                force = float(sharing == name+"_only") if sharing.endswith("_only") else .5
                area = sum(ply["weights_mm2"].values())
                for n, weight in ply["weights_mm2"].items():
                    loads[n] = loads.get(n, 0.)+force*weight/area
            # These are the exact serialized values used for the audit too.
            loads = {n: float(format_cload(f)) for n, f in loads.items() if f}
            vectors = {n: tuple(f if i == axis else 0. for i in range(3)) for n, f in loads.items()}
            applied = resultant(nodes, vectors)
            if abs(sum(loads.values())-1.) > 1e-10:
                raise ValueError("Unit applied force lost")
            cases.append({"sharing": sharing, "axis": axis, "loads": vectors, "applied_force_moment": applied})
            lines += ["*STEP", "*STATIC", "*BOUNDARY", "FIXED,1,3,0", "*CLOAD,OP=NEW"]
            lines += [f"{n},{axis+1},{format_cload(f)}" for n, f in loads.items()]
            lines += ["*NODE PRINT,NSET=FIXED", "RF", "*NODE PRINT,NSET=ALLN", "U",
                      "*EL PRINT,ELSET=INNER,TOTALS=ONLY", "ELSE",
                      "*EL PRINT,ELSET=OUTER,TOTALS=ONLY", "ELSE", "*END STEP"]
    return "\n".join(lines)+"\n", {"nodes": nodes, "fixed": fixed, "plies": plies,
            "cases": cases, "independent": independent, "gates": GATES}


def audit(data, context):
    parsed = blocks(data)
    energy = {}
    for name, time, value in re.findall(r"total internal energy for set (\w+) and time\s+(\S+)\s+([\d.Ee+\-]+)", data):
        key = name, float(time)
        if key in energy or not math.isfinite(float(value)) or float(value) < -1e-12:
            raise ValueError("Invalid/duplicate native energy")
        energy[key] = float(value)
    expected = {(kind, name, float(t)) for t in range(1, len(context["cases"])+1)
                for kind, name in (("forces", "FIXED"), ("displacements", "ALLN"))}
    if set(parsed) != expected:
        raise ValueError("Incomplete/extra profile endpoints")
    if set(energy) != {(name, float(t)) for name in ("INNER", "OUTER") for t in range(1, len(context["cases"])+1)}:
        raise ValueError("Incomplete native ply energy endpoints")
    results = []
    for time, case in enumerate(context["cases"], 1):
        u, rf = parsed["displacements", "ALLN", float(time)], parsed["forces", "FIXED", float(time)]
        if set(u) != set(context["nodes"]) or set(rf) != set(context["fixed"]):
            raise ValueError("Incomplete node output")
        if max(abs(v) for n in context["fixed"] for v in u[n]) > GATES["fixed_displacement_mm"]:
            raise ValueError("Ideal fixed bore moved")
        reactions = resultant(context["nodes"], rf)
        residual = [a+b for a, b in zip(reactions, case["applied_force_moment"], strict=True)]
        work = sum(sum(f*v for f, v in zip(force, u[n], strict=True)) for n, force in case["loads"].items())
        per_ply = {}
        for name, ply in context["plies"].items():
            value = {"maximum_displacement_mm": max(math.hypot(*u[n]) for n in ply["nodes"]),
                     "native_internal_energy_nmm": energy[name.upper(), float(time)]}
            if context["independent"]:
                selected = set(ply["nodes"])
                value["energy_from_half_external_work_nmm"] = sum(
                    sum(f*v for f, v in zip(force, u[n], strict=True))
                    for n, force in case["loads"].items() if n in selected)/2
                value["reaction_force_moment"] = resultant(context["nodes"], {n: rf[n] for n in ply["fixed"]})
                value["applied_force_moment"] = resultant(context["nodes"], {n: f for n, f in case["loads"].items() if n in set(ply["nodes"])})
                value["balance_residual"] = [a+b for a, b in zip(value["reaction_force_moment"], value["applied_force_moment"], strict=True)]
            per_ply[name] = value
        passed = max(map(abs, residual[:3])) <= GATES["force_n"] and max(map(abs, residual[3:])) <= GATES["moment_nmm"] and work > 0
        total_energy = sum(p["native_internal_energy_nmm"] for p in per_ply.values())
        passed &= work > 0 and abs(2*total_energy/work-1) <= GATES["relative_energy_work"]
        if context["independent"]:
            passed &= all(max(map(abs, p["balance_residual"][:3])) <= GATES["force_n"] and max(map(abs, p["balance_residual"][3:])) <= GATES["moment_nmm"] for p in per_ply.values())
            for p in per_ply.values():
                halfwork = p["energy_from_half_external_work_nmm"]
                passed &= (abs(p["native_internal_energy_nmm"]/halfwork-1) <= GATES["relative_energy_work"] if halfwork > 0
                           else abs(p["native_internal_energy_nmm"]) <= GATES["unloaded_energy_nmm"])
        if case["sharing"].endswith("_only"):
            unloaded = "outer" if case["sharing"] == "inner_only" else "inner"
            passed &= per_ply[unloaded]["maximum_displacement_mm"] <= GATES["unloaded_displacement_mm"]
        results.append({"sharing": case["sharing"], "axis": case["axis"], "applied_force_moment": case["applied_force_moment"],
                        "reaction_force_moment": reactions, "balance_residual": residual, "unit_load_compliance_mm_per_n": work,
                        "energy_from_half_external_work_nmm": work/2, "plies": per_ply, "pass": bool(passed)})
    return results


def comparisons(jobs):
    results = []
    for model in ("composite", "independent"):
        coarse, fine = [jobs[f"{model}{size}"].get("results", []) for size in (40, 25)]
        if not coarse or len(coarse) != len(fine):
            return {"pass": False, "reason": "Incomplete mesh pair"}
        for a, b in zip(coarse, fine, strict=True):
            if (a["sharing"], a["axis"]) != (b["sharing"], b["axis"]):
                raise ValueError("Unmatched mesh cases")
            change = abs(b["unit_load_compliance_mm_per_n"]/a["unit_load_compliance_mm_per_n"]-1)
            results.append({"model": model, "sharing": a["sharing"], "axis": a["axis"],
                            "relative_compliance_change": change, "pass": change <= GATES["relative_mesh_compliance"]})
    return {"mesh_checks": results, "pass": all(r["pass"] for r in results)}


def validate_prepared(prepared):
    from fea.independent_leg_mesh import replay_archive
    publication = Path("fea/results/independent_leg_mesh")
    archive = publication/"evidence.tar.gz"
    digest = hashlib.sha256(archive.read_bytes()).hexdigest()
    if digest != json.loads((publication/"report.json").read_text())["archive_sha256"]:
        raise ValueError("Published mesh archive changed")
    replay_archive(archive)
    with tarfile.open(archive) as bundle:
        manifest = json.loads(bundle.extractfile("manifest.json").read())
    for name in ("input.json", "mesh40/mesh.inp", "mesh40/mesh.json", "mesh25/mesh.inp", "mesh25/mesh.json"):
        if hashlib.sha256((Path(prepared)/name).read_bytes()).hexdigest() != manifest[name]:
            raise ValueError("Prepared fixture/mesh differs from verified publication")
    return digest


def main(prepared):
    prepared = Path(prepared)
    mesh_archive_digest = validate_prepared(prepared)
    directory = Path(tempfile.mkdtemp(prefix="independent-leg-response-", dir="fea/generated"))
    sources = (Path(__file__), Path("fea/independent_ply_control.py"), Path("fea/floor_contact.py"),
               Path("fea/floor_contact_results.py"), Path("fea/section_force_coupon.py"),
               Path("fea/section_force_tet_coupon.py"), Path("fea/independent_leg_mesh.py"))
    snapshot = directory/"launch_sources"
    snapshot.mkdir()
    for p in sources:
        (snapshot/p.name).write_bytes(p.read_bytes())
    manifest = {"scope": "CONDITIONAL LINEAR FIXED-BORE COMPLIANCE; NO CAPACITY OR PHYSICAL CONTACT ACCEPTANCE",
                "gates": GATES, "max_seconds_per_job": 120, "verified_mesh_archive_sha256": mesh_archive_digest,
                "solver_image_id": os.environ.get("CONTROL_IMAGE_ID", "unrecorded"),
                "source_sha256": {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in sources}, "jobs": {}}
    (directory/"prepared_input.json").write_bytes((prepared/"input.json").read_bytes())
    manifest["prepared_input_sha256"] = hashlib.sha256((directory/"prepared_input.json").read_bytes()).hexdigest()
    (directory/"manifest.json").write_text(json.dumps(manifest, indent=2)+"\n")
    print(directory, flush=True)
    for size in (40, 25):
        source = (prepared/f"mesh{size}"/"mesh.inp").read_text()
        metadata = json.loads((prepared/f"mesh{size}"/"mesh.json").read_text())
        (directory/f"mesh{size}.inp").write_text(source)
        (directory/f"mesh{size}.json").write_text(json.dumps(metadata, indent=2)+"\n")
        for independent in (False, True):
            name = f"{'independent' if independent else 'composite'}{size}"
            text, context = deck(source, metadata, independent)
            job = directory/name
            job.with_suffix(".inp").write_text(text)
            record = {"status": "PREDECLARED; NOT YET RUN", "deck_sha256": hashlib.sha256(text.encode()).hexdigest()}
            job.with_suffix(".json").write_text(json.dumps(record)+"\n")
            with job.with_suffix(".log").open("w") as log:
                try:
                    run = subprocess.run(["ccx", "-i", name], cwd=directory, stdout=log, stderr=subprocess.STDOUT,
                                         timeout=120, check=False, env=dict(os.environ, OMP_NUM_THREADS="2"))
                    record["exit_code"] = run.returncode
                except subprocess.TimeoutExpired:
                    record["exit_code"] = -999
            record["status"] = "FAIL_OR_UNRESOLVED"
            if record["exit_code"] == 0 and "*ERROR" not in job.with_suffix(".log").read_text().upper():
                if hashlib.sha256(job.with_suffix(".inp").read_bytes()).hexdigest() != record["deck_sha256"]:
                    raise ValueError("Changed launch deck")
                record["results"] = audit(job.with_suffix(".dat").read_text(), context)
                if all(r["pass"] for r in record["results"]):
                    record["status"] = "PASS_CONDITIONAL_GLOBAL_DIAGNOSTICS_ONLY"
            record["output_sha256"] = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in directory.glob(name+".*") if p.suffix not in (".inp", ".json")}
            job.with_suffix(".json").write_text(json.dumps(record, indent=2, allow_nan=False)+"\n")
            manifest["jobs"][name] = record
            (directory/"manifest.json").write_text(json.dumps(manifest, indent=2, allow_nan=False)+"\n")
            print(name, record["status"], flush=True)
    manifest["comparisons"] = comparisons(manifest["jobs"])
    manifest["pass"] = manifest["comparisons"]["pass"] and all(j["status"] == "PASS_CONDITIONAL_GLOBAL_DIAGNOSTICS_ONLY" for j in manifest["jobs"].values())
    (directory/"manifest.json").write_text(json.dumps(manifest, indent=2, allow_nan=False)+"\n")


def replay_archive(path):
    with tarfile.open(path) as archive:
        entries = [m for m in archive.getmembers() if m.isfile()]
        if len({m.name for m in entries}) != len(entries):
            raise ValueError("Duplicate response archive members")
        files = {m.name: archive.extractfile(m).read() for m in entries}
    manifest = json.loads(files["manifest.json"])
    if manifest["gates"] != GATES:
        raise ValueError("Replay diagnostic gates differ from predeclared experiment")
    for source, digest in manifest["source_sha256"].items():
        if hashlib.sha256(files["launch_sources/"+Path(source).name]).hexdigest() != digest:
            raise ValueError("Response launch snapshot changed")
    mesh_archive = Path("fea/results/independent_leg_mesh/evidence.tar.gz")
    if hashlib.sha256(mesh_archive.read_bytes()).hexdigest() != manifest["verified_mesh_archive_sha256"]:
        raise ValueError("Verified mesh publication changed")
    from fea.independent_leg_mesh import replay_archive as replay_mesh
    replay_mesh(mesh_archive)
    with tarfile.open(mesh_archive) as archive:
        if archive.extractfile("input.json").read() != files["prepared_input.json"]:
            raise ValueError("Prepared CAD context differs")
        for size in (40, 25):
            for extension in ("inp", "json"):
                if archive.extractfile(f"mesh{size}/mesh.{extension}").read() != files[f"mesh{size}.{extension}"]:
                    raise ValueError("Response mesh/fixture differs from verified publication")
    if hashlib.sha256(files["prepared_input.json"]).hexdigest() != manifest["prepared_input_sha256"]:
        raise ValueError("Prepared input digest differs")
    jobs = {}
    for size in (40, 25):
        for independent in (False, True):
            name = f"{'independent' if independent else 'composite'}{size}"
            record = json.loads(files[name+".json"])
            text, context = deck(files[f"mesh{size}.inp"].decode(), json.loads(files[f"mesh{size}.json"]), independent)
            if text.encode() != files[name+".inp"] or hashlib.sha256(text.encode()).hexdigest() != record["deck_sha256"]:
                raise ValueError("Response deck differs from intended experiment")
            if record["exit_code"] != 0 or "*ERROR" in files[name+".log"].decode().upper():
                raise ValueError("Incomplete/failed response solver")
            if any(hashlib.sha256(files[n]).hexdigest() != h for n, h in record["output_sha256"].items()):
                raise ValueError("Raw response output digest differs")
            results = audit(files[name+".dat"].decode(), context)
            if results != record["results"] or record != manifest["jobs"][name]:
                raise ValueError("Response results differ from raw replay")
            jobs[name] = record
    compared = comparisons(jobs)
    if compared != manifest["comparisons"] or manifest["pass"] != (compared["pass"] and all(r["pass"] for j in jobs.values() for r in j["results"])):
        raise ValueError("Response comparison status differs")
    return manifest


def publish(directory):
    directory = Path(directory)
    destination = Path("fea/results/independent_leg_response")
    destination.mkdir()  # Preserve any prior publication; never overwrite it.
    archive = destination/"evidence.tar.gz"
    with tarfile.open(archive, "x:gz") as bundle:
        for p in sorted(directory.rglob("*")):
            if p.is_file():
                bundle.add(p, arcname=str(p.relative_to(directory)))
    manifest = replay_archive(archive)
    report = dict(manifest, archive_sha256=hashlib.sha256(archive.read_bytes()).hexdigest(),
                  original_directory=str(directory), publisher_source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
    (destination/"publisher.py").write_bytes(Path(__file__).read_bytes())
    (destination/"report.json").write_text(json.dumps(report, indent=2, allow_nan=False)+"\n")
    return report


if __name__ == "__main__":
    import sys
    main(sys.argv[1])
