"""Retrospective untransformed gravity-quadrature diagnostic; never runs FEA."""

import argparse
import hashlib
import json
import math
import os
import subprocess
import sys
import tarfile
import tempfile
from pathlib import Path

from fea.dynamic_momentum import calculix_221_quadrature
from fea.floor_contact import mesh
from fea.floor_contact_results import blocks, cross

ARCHIVE = Path("fea/results/full_frame_refinement/0.0625.tar.gz")
ARCHIVE_SHA = "b7191366c224835aa6f790996671cc491ad3ae878cb9b797698a04d45e0b373b"
PUBLISHED = Path("fea/results/full_frame_refinement/report.json")
IMAGE = "sha256:37671083a88ded305c4fcd83960a767dad4c2acb480976cb75fab5df261e2646"
GRAVITY = 6e-10*9806.65
LIMITS = ("Untransformed native four-point gravity candidate only; mortar basis is not qualified. "
          "Original outputs, residuals and 0.1 N / 1 Nmm gates retained. No new solver run, "
          "contact acceptance or physical validation.")


def sha(path):
    with Path(path).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


SOURCE_ORIGINS = {"fea/native_gravity_replay.py":Path(__file__).resolve(),
                  **{f"fea/{name}.py":Path(sys.modules[f"fea.{name}"].__file__).resolve()
                     for name in ("dynamic_momentum","floor_contact","floor_contact_results")}}
LOADED_SOURCE_SHA256 = {name:sha(path) for name,path in SOURCE_ORIGINS.items()}


def isolated_environment():
    return {**{k:v for k,v in os.environ.items() if k != "PYTHONPATH"},
            "PYTHONDONTWRITEBYTECODE":"1"}


def verify_origins(directory):
    expected = json.loads((directory/"launch.json").read_text())["sources_sha256"]
    for name,origin in SOURCE_ORIGINS.items():
        if not origin.samefile(directory/"sources"/name) or LOADED_SOURCE_SHA256[name] != expected.get(name) or sha(origin) != expected.get(name):
            raise ValueError("Loaded/current/snapshot source identity differs: "+name)
    package = directory/"sources/fea/__init__.py"
    if sha(package) != expected.get("fea/__init__.py") or not Path(sys.modules["fea"].__file__).samefile(package):
        raise ValueError("Frozen package origin differs")
    return {name:{"origin":str(origin),"loaded_sha256":LOADED_SOURCE_SHA256[name],
                  "current_sha256":sha(origin),"snapshot_sha256":expected[name]}
            for name,origin in SOURCE_ORIGINS.items()}


def freeze_sources(directory):
    hashes = {}
    for name,source in SOURCE_ORIGINS.items():
        if sha(source) != LOADED_SOURCE_SHA256[name]:
            raise ValueError("Source changed since launcher import: "+name)
        target = directory/"sources"/name
        target.parent.mkdir(parents=True,exist_ok=True)
        with target.open("xb") as stream:
            stream.write(source.read_bytes())
        hashes[name] = sha(target)
        if hashes[name] != LOADED_SOURCE_SHA256[name]:
            raise ValueError("Snapshot differs from loaded launcher source")
    package = directory/"sources/fea/__init__.py"
    with package.open("xb"):
        pass
    hashes["fea/__init__.py"] = sha(package)
    return hashes


def save(path, data):
    with Path(path).open("x") as stream:
        json.dump(data, stream, indent=2, allow_nan=False)
        stream.write("\n")


def native_volume_weights(nodes, elements):
    """Integrate N_i detJ at the four source-specified points, without mass blocks."""
    import gmsh

    if not nodes or any(len(p) != 3 or not all(map(math.isfinite,p)) for p in nodes.values()):
        raise ValueError("Finite three-coordinate mesh required")
    if not elements or any(len(ids) != 10 or len(set(ids)) != 10 or
                           any(n not in nodes for n in ids) for ids in elements.values()):
        raise ValueError("Complete distinct C3D10 connectivity required")
    if gmsh.isInitialized():
        raise ValueError("Independent Gmsh session required")
    gmsh.initialize()
    try:
        gmsh.option.setNumber("General.Verbosity", 1)
        gmsh.model.add("native_gravity")
        entity = gmsh.model.addDiscreteEntity(3)
        gmsh.model.mesh.addNodes(3, entity, list(nodes), [x for p in nodes.values() for x in p])
        gmsh.model.mesh.addElementsByType(entity, 11, list(elements),
                                        [ids[i] for ids in elements.values() for i in (0,1,2,3,4,5,6,7,9,8)])
        coordinates, weights = calculix_221_quadrature()
        points = [x for p in coordinates for x in p]
        _, basis, _ = gmsh.model.mesh.getBasisFunctions(11, points, "Lagrange")
        tags, ids = gmsh.model.mesh.getElementsByType(11, entity)
        _, determinants, _ = gmsh.model.mesh.getJacobians(11, points, entity)
        result = dict.fromkeys(nodes, 0.)
        for e in range(len(tags)):
            for q,w in enumerate(weights):
                determinant = float(determinants[4*e+q])
                if not math.isfinite(determinant) or determinant <= 0:
                    raise ValueError("Nonpositive/nonfinite native Jacobian")
                for i in range(10):
                    result[int(ids[10*e+i])] += float(basis[10*q+i])*w*determinant
        if not all(map(math.isfinite,result.values())) or math.fsum(result.values()) <= 0:
            raise ValueError("Invalid integrated weights")
        return result
    finally:
        gmsh.finalize()


def corrected_residual(nodes, displacement, delta_weights, original):
    """Add native-minus-archived gravity loads to an unchanged published residual."""
    if nodes.keys() != displacement.keys() or nodes.keys() != delta_weights.keys():
        raise ValueError("Incomplete displacement or weight correction")
    time = original["time"]
    if not math.isfinite(time) or not 0 < time <= 2:
        raise ValueError("Invalid accepted time")
    if any(len(p) != 3 or not all(map(math.isfinite,p)) for field in (nodes,displacement)
           for p in field.values()) or not all(map(math.isfinite,delta_weights.values())):
        raise ValueError("Nonfinite correction context")
    ramp = min(time,1.)
    loads = {n:(0.,0.,-GRAVITY*ramp*w) for n,w in delta_weights.items()}
    moments = [cross(tuple(x+u for x,u in zip(nodes[n],displacement[n],strict=True)), f)
               for n,f in loads.items()]
    delta_force = [math.fsum(f[a] for f in loads.values()) for a in range(3)]
    delta_moment = [math.fsum(m[a] for m in moments) for a in range(3)]
    force = [a+b for a,b in zip(original["force_residual_n"],delta_force,strict=True)]
    moment = [a+b for a,b in zip(original["moment_residual_nmm"],delta_moment,strict=True)]
    if len(force) != 3 or len(moment) != 3 or not all(map(math.isfinite,force+moment)):
        raise ValueError("Invalid residual")
    original_pass = max(map(abs,original["force_residual_n"])) <= .1 and max(map(abs,original["moment_residual_nmm"])) <= 1
    if original_pass != original["global_gate_pass"]:
        raise ValueError("Published gate disagrees with preserved thresholds")
    return {"time":time, "original":original, "delta_gravity_force_n":delta_force,
            "delta_gravity_moment_nmm":delta_moment, "candidate_force_residual_n":force,
            "candidate_moment_residual_nmm":moment,
            "candidate_global_gate_pass":max(map(abs,force)) <= .1 and max(map(abs,moment)) <= 1}


def integrate(directory):
    origins = verify_origins(directory)
    data = json.loads((directory/"mesh.json").read_text())
    nodes = {int(n):p for n,p in data["nodes"].items()}
    elements = {int(e):ids for e,ids in data["elements"].items()}
    weights = native_volume_weights(nodes,elements)
    verify_origins(directory)
    save(directory/"integration.json", {"mesh_sha256":sha(directory/"mesh.json"),
         "verified_origins":origins,"weights_mm3":weights})


def analyze(directory):
    save(directory/"analysis_origins.json",verify_origins(directory))
    launch = json.loads((directory/"launch.json").read_text())
    archive, published = Path(launch["archive"]), Path(launch["published"])
    if sha(archive) != ARCHIVE_SHA or sha(published) != launch["published_sha256"]:
        raise ValueError("Retained input changed")
    baseline = json.loads(published.read_text())["runs"]["0.0625"]
    if baseline["archive_sha256"] != ARCHIVE_SHA:
        raise ValueError("Published archive identity differs")
    names = ("frame.inp","frame.json","frame.dat","frame.sta")
    with tarfile.open(archive) as source:
        if len({m.name for m in source.getmembers()}) != len(source.getmembers()):
            raise ValueError("Duplicate archive members")
        files = {name:source.extractfile(name).read() for name in names}
    hashes = {name:hashlib.sha256(value).hexdigest() for name,value in files.items()}
    if any(hashes[name] != baseline["archive_contents_sha256"][name] for name in names):
        raise ValueError("Published archive member identity differs")
    record = json.loads(files["frame.json"])
    if hashes["frame.inp"] != record["deck_sha256"]:
        raise ValueError("Frozen deck identity differs")
    nodes, elements = mesh(files["frame.inp"].decode())
    used = {n for ids in elements.values() for n in ids}
    nodes = {n:p for n,p in nodes.items() if n in used}
    old_weights = {int(n):w for n,w in record["nodal_volume_mm3"].items()}
    if nodes.keys() != old_weights.keys() or not all(map(math.isfinite,old_weights.values())):
        raise ValueError("Incomplete archived gravity weights")
    save(directory/"mesh.json", {"nodes":nodes,"elements":elements})
    command = ["docker","run","--rm","--network=none","--read-only","--memory=2g","--cpus=2",
               "--tmpfs","/tmp:size=128m","-e","PYTHONDONTWRITEBYTECODE=1","-e","PYTHONPATH=",
               "-v",f"{directory}:/evidence:rw","-v",f"{directory/'sources'}:/sources:ro",
               "-w","/sources",IMAGE,"timeout","--kill-after=5s","110s","python3","-m",
               "fea.native_gravity_replay","--integrate","/evidence"]
    with (directory/"integration.log").open("x") as log:
        result = subprocess.run(command, stdout=log, stderr=subprocess.STDOUT, timeout=120,
                                env=isolated_environment(), check=False)
    if result.returncode:
        raise ValueError(f"Bounded Gmsh integration failed: {directory}")
    integration = json.loads((directory/"integration.json").read_text())
    if integration["mesh_sha256"] != sha(directory/"mesh.json"):
        raise ValueError("Integration mesh identity differs")
    native = {int(n):w for n,w in integration["weights_mm3"].items()}
    if native.keys() != nodes.keys():
        raise ValueError("Incomplete native weights")
    delta = {n:native[n]-old_weights[n] for n in nodes}
    parsed = blocks(files["frame.dat"].decode())
    rows = baseline["diagnostic_endpoints"]
    sta_times = [float(cells[4]) for line in files["frame.sta"].decode().splitlines()
                 if len(cells:=line.split()) == 7 and all(v.isdigit() for v in cells[:4])]
    times = [row["time"] for row in rows]
    if len(rows) != 32 or times != sorted(set(times)) or times != sta_times:
        raise ValueError("Original 32 accepted times differ")
    endpoints = [corrected_residual(nodes,parsed.get(("displacements","WOODN",row["time"]),{}),delta,row)
                 for row in rows]
    deviation = max(math.dist(nodes[ids[i+4]],tuple((nodes[ids[a]][k]+nodes[ids[b]][k])/2 for k in range(3)))
                    for ids in elements.values() for i,(a,b) in enumerate(((0,1),(1,2),(2,0),(0,3),(1,3),(2,3))))
    for source, expected in launch["sources_sha256"].items():
        if sha(directory/"sources"/source) != expected:
            raise ValueError("Frozen executed source changed")
    if sha(archive) != ARCHIVE_SHA or sha(published) != launch["published_sha256"]:
        raise ValueError("Retained input changed during replay")
    save(directory/"report.json", {"limits":LIMITS,"launch_sha256":sha(directory/"launch.json"),
         "analysis_origins_sha256":sha(directory/"analysis_origins.json"),
         "input_archive_sha256":ARCHIVE_SHA,"input_members_sha256":hashes,
         "published_report_sha256":launch["published_sha256"],"sources_sha256":launch["sources_sha256"],
         "mesh_sha256":sha(directory/"mesh.json"),"integration_sha256":sha(directory/"integration.json"),
         "integration_log_sha256":sha(directory/"integration.log"),"integration_command":command,
         "node_count":len(nodes),"element_count":len(elements),"maximum_midside_offset_mm":deviation,
         "archived_volume_mm3":math.fsum(old_weights.values()),"native_volume_mm3":math.fsum(native.values()),
         "maximum_absolute_weight_delta_mm3":max(map(abs,delta.values())),
         "gates":{"force_n":.1,"moment_nmm":1.},"endpoints":endpoints})
    save(directory/"output_manifest.json", {name:sha(directory/name) for name in
         ("report.json","mesh.json","integration.json","integration.log","launch.json","analysis_origins.json")})
    print(json.dumps({"directory":str(directory),"original_failed_times":[r["time"] for r in endpoints if not r["original"]["global_gate_pass"]],
                      "candidate_failed_times":[r["time"] for r in endpoints if not r["candidate_global_gate_pass"]],
                      "max_delta_moment_nmm":max(abs(v) for r in endpoints for v in r["delta_gravity_moment_nmm"])}),flush=True)


def run():
    directory = Path(tempfile.mkdtemp(prefix="native-gravity-replay-",dir="fea/generated")).resolve()
    print(directory,flush=True)
    hashes = freeze_sources(directory)
    save(directory/"launch.json", {"archive":str(ARCHIVE.resolve()),"archive_sha256":ARCHIVE_SHA,
         "published":str(PUBLISHED.resolve()),"published_sha256":sha(PUBLISHED),"sources_sha256":hashes,
         "image_id":IMAGE,"limits":LIMITS})
    subprocess.run([sys.executable,"-m","fea.native_gravity_replay","--analyze",str(directory)],
                   cwd=directory/"sources",env=isolated_environment(),timeout=240,check=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--integrate",type=Path)
    parser.add_argument("--analyze",type=Path)
    parser.add_argument("--verify-origins",type=Path)
    args = parser.parse_args()
    if args.verify_origins:
        print(json.dumps(verify_origins(args.verify_origins)))
    elif args.integrate:
        integrate(args.integrate)
    elif args.analyze:
        analyze(args.analyze)
    else:
        run()
