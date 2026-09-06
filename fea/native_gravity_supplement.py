"""Supplement prior gravity evidence with isolated imports; Gmsh only, no solver."""

import argparse
import json
import subprocess
import tarfile
import tempfile
from pathlib import Path

from fea.native_gravity_replay import (
    IMAGE,
    freeze_sources,
    isolated_environment,
    save,
    sha,
)
from fea.publish_native_gravity_replay import DIRECTORY, digest, member_bytes


def verify():
    publication = json.loads((DIRECTORY/"supplement.json").read_text())
    path = DIRECTORY/publication["archive"]
    if sha(path) != publication["archive_sha256"]:
        raise ValueError("Supplement archive changed")
    files = member_bytes(path)
    if {name:digest(value) for name,value in files.items()} != publication["archive_members_sha256"]:
        raise ValueError("Supplement members changed")
    report, launch = json.loads(files["report.json"]), json.loads(files["launch.json"])
    prior_publication = json.loads((DIRECTORY/"report.json").read_text())
    prior_path = DIRECTORY/prior_publication["archive"]
    if sha(prior_path) != report["prior_archive_sha256"] or sha(prior_path) != prior_publication["archive_sha256"]:
        raise ValueError("Prior archive changed")
    prior = member_bytes(prior_path)
    if files["mesh.json"] != prior["mesh.json"]:
        raise ValueError("Supplement changed original integration mesh")
    integrated = json.loads(files["integration.json"])
    old = json.loads(prior["integration.json"])
    if integrated["weights_mm3"] != old["weights_mm3"] or len(integrated["weights_mm3"]) != 62020:
        raise ValueError("Supplement weights differ from retained weights")
    if integrated["mesh_sha256"] != digest(files["mesh.json"]):
        raise ValueError("Supplement integration mesh digest differs")
    if digest(files["launch.json"]) != report["launch_sha256"] or digest(files["integration.json"]) != report["integration_sha256"]:
        raise ValueError("Supplement input/output identity differs")
    for name,expected in launch["sources_sha256"].items():
        if digest(files["sources/"+name]) != expected:
            raise ValueError("Supplement frozen source changed")
    origins = integrated["verified_origins"]
    if set(origins) != set(launch["sources_sha256"])-{"fea/__init__.py"}:
        raise ValueError("Incomplete verified source origins")
    for name,entry in origins.items():
        expected = launch["sources_sha256"][name]
        if entry != {"origin":"/sources/"+name,"loaded_sha256":expected,
                     "current_sha256":expected,"snapshot_sha256":expected}:
            raise ValueError("Unexpected supplement execution origin")
    if digest(files["integration.log"]) != report["integration_log_sha256"]:
        raise ValueError("Supplement log changed")
    return report


def run():
    publication = json.loads((DIRECTORY/"report.json").read_text())
    prior_path = DIRECTORY/publication["archive"]
    if sha(prior_path) != publication["archive_sha256"]:
        raise ValueError("Prior archive changed")
    prior = member_bytes(prior_path)
    if {name:digest(value) for name,value in prior.items()} != publication["archive_members_sha256"]:
        raise ValueError("Prior members changed")
    directory = Path(tempfile.mkdtemp(prefix="native-gravity-origins-",dir="fea/generated")).resolve()
    print(directory,flush=True)
    hashes = freeze_sources(directory)
    with (directory/"mesh.json").open("xb") as stream:
        stream.write(prior["mesh.json"])
    own_source = Path(__file__).read_bytes()
    with (directory/"supplement_launcher.py").open("xb") as stream:
        stream.write(own_source)
    save(directory/"launch.json",{"sources_sha256":hashes,"mesh_sha256":sha(directory/"mesh.json"),
         "prior_archive_sha256":sha(prior_path),"image_id":IMAGE,
         "launcher_sha256":digest(own_source),"prior_run_origins_verified":False})
    command = ["docker","run","--rm","--network=none","--read-only","--memory=2g","--cpus=2",
               "--tmpfs","/tmp:size=128m","-e","PYTHONDONTWRITEBYTECODE=1","-e","PYTHONPATH=",
               "-v",f"{directory}:/evidence:rw","-v",f"{directory/'sources'}:/sources:ro",
               "-w","/sources",IMAGE,"timeout","--kill-after=5s","110s","python3","-m",
               "fea.native_gravity_replay","--integrate","/evidence"]
    with (directory/"integration.log").open("x") as log:
        result = subprocess.run(command,stdout=log,stderr=subprocess.STDOUT,env=isolated_environment(),
                                timeout=120,check=False)
    if result.returncode:
        raise ValueError("Strict supplementary Gmsh integration failed; retained "+str(directory))
    integrated = json.loads((directory/"integration.json").read_text())
    old = json.loads(prior["integration.json"])
    if integrated["weights_mm3"] != old["weights_mm3"]:
        raise ValueError("Strict weights differ; no replacement or publication")
    for name,expected in hashes.items():
        if sha(directory/"sources"/name) != expected:
            raise ValueError("Strict snapshot changed")
    save(directory/"report.json",{"qualification":"Separate strict-import Gmsh corroboration only. Original run import origins were not recorded; snapshots alone do not prove executed module paths. All 62020 retained weights reproduced exactly; portable original-state arithmetic remains independently verified. No solver or mortar qualification.",
         "prior_archive_sha256":sha(prior_path),"launch_sha256":sha(directory/"launch.json"),
         "integration_sha256":sha(directory/"integration.json"),"integration_log_sha256":sha(directory/"integration.log"),
         "verified_weight_count":len(integrated["weights_mm3"]),"all_weights_exactly_equal":True,
         "integration_command":command})
    destination = DIRECTORY/"strict-origins-supplement.tar.gz"
    if destination.exists() or (DIRECTORY/"supplement.json").exists():
        raise ValueError("Supplement publication already exists")
    sources = sorted(path for path in directory.rglob("*") if path.is_file())
    manifest = {str(path.relative_to(directory)):sha(path) for path in sources}
    with tarfile.open(destination,"x:gz") as archive:
        for path in sources:
            archive.add(path,arcname=str(path.relative_to(directory)),recursive=False)
    save(DIRECTORY/"supplement.json",{"archive":destination.name,"archive_sha256":sha(destination),
         "archive_members_sha256":manifest,"prior_archive_sha256":sha(prior_path)})
    verify()
    print(destination,flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run",action="store_true")
    args = parser.parse_args()
    if args.run:
        run()
    else:
        verify()
