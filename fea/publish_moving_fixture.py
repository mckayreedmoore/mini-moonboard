"""Publish geometry and mass preparation evidence; never launch a solver."""
import argparse
import gzip
import io
import json
import math
import tarfile
from pathlib import Path

from fea import hardware_mass_cache as mass
from fea import moving_hardware_pose as pose
from fea.results.stitch_joint_mesh.publisher import archive_files, sha

HERE = Path(__file__).parent / "results/moving_fixture_preparation"
REFERENCE = HERE.parent / "moving_hardware_control/fourth-direct-quiescent.tar.gz"
REFERENCE_SHA = "978f55507db7a92bf6d985b841dae38ecdb6748063802119c811a13cff808631"


def require(condition, message):
    if not condition:
        raise ValueError(message)


def checked_members(path, digest):
    require(sha(path.read_bytes()) == digest, "Archive hash differs")
    files = archive_files(path)
    inventory = json.loads(files["members.json"])
    require(set(inventory) == set(files) - {"members.json"}, "Archive inventory differs")
    require(all(sha(files[n]) == h for n, h in inventory.items()), "Member hash differs")
    return files


def verify(directory=HERE):
    directory = Path(directory)
    manifest = json.loads((directory / "manifest.json").read_text())
    require(manifest["reference_archive"] == str(REFERENCE.relative_to(HERE.parent))
            and manifest["reference_sha256"] == REFERENCE_SHA, "Reference archive declaration differs")
    reference = checked_members(REFERENCE, REFERENCE_SHA)
    prepared = reference["prepared/context.json"]
    context = json.loads(prepared)
    reports = {}
    datasets = {}
    for name in ("pose", "mass"):
        files = checked_members(directory / manifest[name]["archive"], manifest[name]["sha256"])
        report = json.loads(files["report.json"])
        require(all(sha(files[n + ".snapshot"]) == h for n, h in report["source_sha256"].items()), "Source snapshot differs")
        require(report["context_sha256"] == sha(prepared)
                and report["prepared_freeze_sha256"] == sha(reference["prepared/freeze.json"]), "Reference preparation differs")
        datasets[name], reports[name] = files, report
    files, report = datasets["pose"], reports["pose"]
    require(tuple(report["translation_local_mm"]) == pose.TRANSLATION_MM, "Declared pose differs")
    require(files["original-context.json"] == prepared, "Pose original context differs")
    require(sha(files["posed-nodes.json"]) == report["posed_nodes_sha256"], "Posed coordinate hash differs")
    nodes, metadata = pose.posed_nodes(context)
    require(json.loads(files["posed-nodes.json"]) == json.loads(json.dumps({"nodes": nodes, "quantization": metadata})), "Posed coordinate replay differs")
    require(json.loads(json.dumps(pose.mesh_clearance(context))) == report["quadratic_mesh"], "Full-patch clearance replay differs")
    require(report["quadratic_mesh"]["strictly_separated_selected_surfaces"] is True, "Selected interfaces not proven separate")
    require(report["CAD"]["geometry_sha256"] == sha(reference["geometry/geometry.json"])
            and all(sha(reference["geometry/" + n]) == h for n, h in report["CAD"]["step_sha256"].items()), "CAD input identity differs")
    files, report = datasets["mass"], reports["mass"]
    require(files["context.json"] == prepared and files["quiescent.inp"] == reference["prepared/quiescent.inp"]
            and files["prepared-freeze.json"] == reference["prepared/freeze.json"], "Mass preparation differs")
    require(report["deck_sha256"] == sha(files["quiescent.inp"]), "Mass report deck hash differs")
    require(sha(files["blocks.json.gz"]) == report["blocks_sha256"], "Mass block hash differs")
    cache = json.loads(gzip.decompress(files["blocks.json.gz"]))
    mass.deck_mesh(files["quiescent.inp"].decode(), context)
    totals = mass.validate_cache(cache, prepared)
    require(totals == report["body_mass_tonne"] and cache["gmsh_version"] == report["gmsh_version"], "Cached totals/version differ")
    # Compare every printed mass, not a rounded value copied into this publisher.
    from fea.quiescent_hardware_audit import blocks, history, numeric
    times = history(reference["solve/result/control.sta"].decode(), 2e-6)
    states = blocks(reference["solve/result/control.dat"].decode(), times)
    errors = {}
    for body in ("BOLT_NUT", "WASHER"):
        values = [numeric(s[f"total mass for set {body} and time"], 1) for s in states]
        require(all(len(v) == 1 and v[0][0] > 0 for v in values), "Missing native body mass")
        errors[body] = max(abs(v[0][0] / totals["native_four_point"][body] - 1) for v in values)
        require(math.isfinite(errors[body]) and errors[body] <= 5e-6, "Native body mass comparison failed")
    return {"native_mass_max_relative_error": errors, "native_mass_states": len(states),
            "body_mass_tonne": totals, "radial_gap_lower_mm": reports["pose"]["quadratic_mesh"]["radial_gap_lower_mm"],
            "limits": "Centred native EMAS comparison and source-derived operators; posed geometry only. No posed mass cache, moving energy/momentum/contact or strength qualification. CAD/Jacobians are retained evidence, not recomputed by portable replay."}


def publish(pose_directory, mass_directory):
    HERE.mkdir(parents=True, exist_ok=True)
    manifest = {"reference_archive": str(REFERENCE.relative_to(HERE.parent)), "reference_sha256": REFERENCE_SHA}
    for name, directory in (("pose", Path(pose_directory)), ("mass", Path(mass_directory))):
        files = {p.name: p.read_bytes() for p in directory.iterdir() if p.is_file()}
        files["members.json"] = json.dumps({n: sha(b) for n, b in files.items()}, sort_keys=True).encode()
        target = HERE / (name + ".tar.gz")
        with tarfile.open(target, "x:gz") as archive:
            for filename, data in sorted(files.items()):
                item = tarfile.TarInfo(filename)
                item.size, item.mode = len(data), 0o644
                archive.addfile(item, io.BytesIO(data))
        manifest[name] = {"archive": target.name, "sha256": sha(target.read_bytes())}
    with (HERE / "manifest.json").open("x") as output:
        json.dump(manifest, output, indent=2)
        output.write("\n")
    result = verify()
    with (HERE / "comparison.json").open("x") as output:
        json.dump(result, output, indent=2, allow_nan=False)
        output.write("\n")
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pose", type=Path)
    parser.add_argument("mass", type=Path)
    args = parser.parse_args()
    print(json.dumps(publish(args.pose, args.mass), indent=2))
