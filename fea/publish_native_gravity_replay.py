"""Publish and independently replay retained gravity corrections without Gmsh/FEA."""

import argparse
import hashlib
import json
import math
import tarfile
from pathlib import Path

from fea.floor_contact import mesh
from fea.floor_contact_results import blocks

DIRECTORY = Path("fea/results/native_gravity_replay")
ORIGINAL_ARCHIVE = Path("fea/results/full_frame_refinement/0.0625.tar.gz")
ORIGINAL_REPORT = Path("fea/results/full_frame_refinement/report.json")
FAILED_TIMES = [1.0625,1.125,1.1875,1.25,1.3125,1.75,1.8125]


def digest(data):
    return hashlib.sha256(data).hexdigest()


def sha(path):
    with Path(path).open("rb") as stream:
        return hashlib.file_digest(stream,"sha256").hexdigest()


def member_bytes(path):
    with tarfile.open(path) as archive:
        members = archive.getmembers()
        if any(not m.isfile() for m in members) or len({m.name for m in members}) != len(members):
            raise ValueError("Duplicate or non-file publication member")
        return {m.name:archive.extractfile(m).read() for m in members}


def close(actual, expected):
    if len(actual) != len(expected) or any(not math.isclose(a,b,rel_tol=1e-12,abs_tol=1e-10)
                                          for a,b in zip(actual,expected,strict=True)):
        raise ValueError("Independent gravity arithmetic differs")


def verify(directory=DIRECTORY):
    """Independently use original DAT U and raw retained weights at all 32 times."""
    publication = json.loads((directory/"report.json").read_text())
    evidence = directory/publication["archive"]
    if sha(evidence) != publication["archive_sha256"]:
        raise ValueError("Published archive digest differs")
    files = member_bytes(evidence)
    if {name:digest(data) for name,data in files.items()} != publication["archive_members_sha256"]:
        raise ValueError("Published member digests differ")
    report, launch = json.loads(files["report.json"]), json.loads(files["launch.json"])
    output = json.loads(files["output_manifest.json"])
    if any(digest(files[name]) != expected for name,expected in output.items()):
        raise ValueError("Retained output manifest differs")
    if digest(files["launch.json"]) != report["launch_sha256"]:
        raise ValueError("Retained launch differs")
    for name,expected in launch["sources_sha256"].items():
        if digest(files["sources/"+name]) != expected:
            raise ValueError("Frozen executed source differs")
    if report["sources_sha256"] != launch["sources_sha256"]:
        raise ValueError("Source manifests differ")
    if sha(ORIGINAL_ARCHIVE) != report["input_archive_sha256"] or sha(ORIGINAL_REPORT) != report["published_report_sha256"]:
        raise ValueError("Original retained input identity differs")
    baseline = json.loads(ORIGINAL_REPORT.read_text())["runs"]["0.0625"]
    if baseline["archive_sha256"] != report["input_archive_sha256"]:
        raise ValueError("Original publication archive identity differs")
    with tarfile.open(ORIGINAL_ARCHIVE) as archive:
        original = {name:archive.extractfile(name).read() for name in report["input_members_sha256"]}
    if {name:digest(data) for name,data in original.items()} != report["input_members_sha256"]:
        raise ValueError("Original member digests differ")
    if any(digest(data) != baseline["archive_contents_sha256"][name] for name,data in original.items()):
        raise ValueError("Original published member identity differs")
    record = json.loads(original["frame.json"])
    old_weights = {int(n):w for n,w in record["nodal_volume_mm3"].items()}
    mesh_input = json.loads(files["mesh.json"])
    nodes = {int(n):p for n,p in mesh_input["nodes"].items()}
    original_nodes, original_elements = mesh(original["frame.inp"].decode())
    if nodes != {n:list(original_nodes[n]) for n in old_weights} or mesh_input["elements"] != {str(e):list(ids) for e,ids in original_elements.items()}:
        raise ValueError("Integration mesh differs from original deck")
    integration = json.loads(files["integration.json"])
    if integration["mesh_sha256"] != digest(files["mesh.json"]) or report["integration_sha256"] != digest(files["integration.json"]):
        raise ValueError("Integration input/output identity differs")
    native = {int(n):w for n,w in integration["weights_mm3"].items()}
    if native.keys() != nodes.keys() or old_weights.keys() != nodes.keys():
        raise ValueError("Incomplete weight inventory")
    if not all(math.isfinite(w) for field in (native,old_weights) for w in field.values()):
        raise ValueError("Nonfinite weight inventory")
    parsed = blocks(original["frame.dat"].decode())
    rows = report["endpoints"]
    if len(rows) != 32 or [r["original"] for r in rows] != baseline["diagnostic_endpoints"]:
        raise ValueError("Original 32 published rows changed")
    if report["gates"] != {"force_n":.1,"moment_nmm":1.}:
        raise ValueError("Original gates changed")
    for row in rows:
        time = row["time"]
        if time != row["original"]["time"]:
            raise ValueError("Correction time differs")
        displacement = parsed.get(("displacements","WOODN",time),{})
        if displacement.keys() != nodes.keys():
            raise ValueError("Incomplete original DAT state")
        # Independent vertical-gravity arithmetic; no replay helper or Gmsh import.
        fz = {n:-(6e-10*9806.65)*min(time,1.)*(native[n]-old_weights[n]) for n in nodes}
        delta_force = [0.,0.,math.fsum(fz.values())]
        delta_moment = [math.fsum((nodes[n][1]+displacement[n][1])*f for n,f in fz.items()),
                        -math.fsum((nodes[n][0]+displacement[n][0])*f for n,f in fz.items()),0.]
        force = [a+b for a,b in zip(row["original"]["force_residual_n"],delta_force,strict=True)]
        moment = [a+b for a,b in zip(row["original"]["moment_residual_nmm"],delta_moment,strict=True)]
        close(row["delta_gravity_force_n"],delta_force)
        close(row["delta_gravity_moment_nmm"],delta_moment)
        close(row["candidate_force_residual_n"],force)
        close(row["candidate_moment_residual_nmm"],moment)
        if row["candidate_global_gate_pass"] != (max(map(abs,force)) <= .1 and max(map(abs,moment)) <= 1.):
            raise ValueError("Candidate gate differs")
    if [r["time"] for r in rows if not r["candidate_global_gate_pass"]] != FAILED_TIMES or [r["time"] for r in rows if not r["original"]["global_gate_pass"]] != FAILED_TIMES:
        raise ValueError("Seven retained failed times changed")
    return report


def publish(source, directory=DIRECTORY):
    directory.mkdir(parents=True,exist_ok=True)
    archive_path = directory/"retained-replay.tar.gz"
    if archive_path.exists() or (directory/"report.json").exists():
        raise ValueError("Publication already exists; refusing overwrite")
    sources = sorted(path for path in source.rglob("*") if path.is_file())
    manifest = {str(path.relative_to(source)):sha(path) for path in sources}
    with tarfile.open(archive_path,"x:gz") as archive:
        for path in sources:
            archive.add(path,arcname=str(path.relative_to(source)),recursive=False)
    retained = json.loads((source/"report.json").read_text())
    publication = {"qualification":retained["limits"],"archive":archive_path.name,
                   "archive_sha256":sha(archive_path),"archive_members_sha256":manifest,
                   "original_archive":str(ORIGINAL_ARCHIVE),"original_archive_sha256":retained["input_archive_sha256"],
                   "original_report":str(ORIGINAL_REPORT),"original_report_sha256":retained["published_report_sha256"],
                   "publisher_sha256":sha(Path(__file__)),"original_and_candidate_failed_times":FAILED_TIMES}
    with (directory/"report.json").open("x") as stream:
        json.dump(publication,stream,indent=2,allow_nan=False)
        stream.write("\n")
    verify(directory)
    print(archive_path)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source",type=Path)
    args = parser.parse_args()
    if args.source:
        publish(args.source)
    else:
        verify()
