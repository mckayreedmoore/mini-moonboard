"""Archive/replay the predeclared increment study; no solver or local-law acceptance."""
import argparse
import hashlib
import json
import math
import re
import tarfile
import tempfile
from decimal import Decimal
from pathlib import Path

from fea.full_frame_mortar import GRAVITY_PER_MM3_N, blocks, cross, verify_deck


def digest(data):
    return hashlib.sha256(data).hexdigest()


def print_bounds(data):
    """Half last printed unit, full endpoints only; not solver/model uncertainty."""
    result = {}
    pattern = r"(displacements|forces)[^\n]*for set (\w+) and time\s+([\d.Ee+\-]+)\n(.*?)(?=\n\s*[A-Za-z]|\Z)"
    for kind, name, time, body in re.findall(pattern, data, re.DOTALL | re.IGNORECASE):
        if float(time) not in (1., 2.):
            continue
        result[kind.lower(), name.upper(), float(time)] = {
            int(cells[0]): tuple(float(Decimal(5).scaleb(Decimal(token).as_tuple().exponent-1)) for token in cells[1:])
            for line in body.splitlines() if len(cells := line.split()) == 4 and cells[0].isdigit()}
    return result


def equilibrium_print_bound(time, bounds, weights, ground, supports, load_nodes):
    force, moment = [0., 0., 0.], [0., 0., 0.]
    for name, xyz in ground.items():
        rf = bounds["forces", "GROUND_"+name, time]
        for n in supports[name]:
            for i in range(3):
                j, k = (i+1)%3, (i+2)%3
                force[i] += rf[n][i]
                # Noncontact support coordinates are fixed exactly by SPCs.
                moment[i] += abs(xyz[n][j])*rf[n][k]+abs(xyz[n][k])*rf[n][j]
    u = bounds["displacements", "WOODN", time]
    for n, weight in weights.items():
        magnitude = abs(weight*GRAVITY_PER_MM3_N)
        moment[0] += magnitude*u[n][1]
        moment[1] += magnitude*u[n][0]
    if time == 2.:
        for n in load_nodes:
            moment[0] += 240*u[n][1]
            moment[1] += 240*u[n][0]
    return {"force_n": force, "moment_nmm": moment,
            "qualification": "Conservative independent half-last-digit DAT RF/U rounding only; fixed SPC positions and archived consistent gravity treated exact. Excludes input/integration/floating-point, solver, contact, material and model errors. Nominal diagnostic gates unchanged."}


def replay(files):
    record = json.loads(files["frame.json"])
    nodes, _, _, ground, supports = verify_deck(files["frame.inp"].decode(), record)
    weights = {int(n): v for n, v in record["nodal_volume_mm3"].items()}
    if weights.keys() != nodes.keys() or not all(map(math.isfinite, weights.values())):
        raise ValueError("Incomplete/nonfinite gravity weights")
    # Publication replays archived weights. Independent reintegration is a
    # prelaunch production guard, not falsely repeated by this portable reader.
    for name, sha in record["output_sha256"].items():
        if digest(files[name]) != sha:
            raise ValueError("Terminal output digest differs")
    for name, sha in record["prelaunch_sha256"].items():
        key = "launch_sources/"+Path(name).name
        if key in files and digest(files[key]) != sha:
            raise ValueError("Launch source digest differs")
    data = files["frame.dat"].decode()
    parsed, rows = blocks(data), []
    rounding = print_bounds(data)
    for line in files["frame.sta"].decode().splitlines():
        fields = line.split()
        if len(fields) == 7 and all(v.isdigit() for v in fields[:4]):
            rows.append(dict(zip(("step", "increment", "attempt", "iterations", "time", "step_time", "increment_time"),
                                 [*map(int, fields[:4]), *map(float, fields[4:])], strict=True)))
    times = [row["time"] for row in rows]
    if any(not math.isfinite(t) or not 0 < t <= 2 for t in times) or times != sorted(set(times)):
        raise ValueError("Invalid accepted increment times")
    endpoints = []
    for time in times:
        u = parsed.get(("displacements", "WOODN", time), {})
        if u.keys() != nodes.keys():
            raise ValueError("Incomplete accepted timber displacement")
        positions = {n: tuple(a+b for a, b in zip(p, u[n], strict=True)) for n, p in nodes.items()}
        forces, patches = [], {}
        for name, xyz in ground.items():
            gu = parsed.get(("displacements", "GROUND_"+name, time), {})
            rf = parsed.get(("forces", "GROUND_"+name, time), {})
            if gu.keys() != xyz.keys() or rf.keys() != xyz.keys():
                raise ValueError("Incomplete accepted ground output")
            if any(abs(v) > 1e-9 for n in supports[name] for v in gu[n]):
                raise ValueError("Fixed support moved")
            patch = [(tuple(a+b for a, b in zip(xyz[n], gu[n], strict=True)), rf[n]) for n in supports[name]]
            forces.extend(patch)
            centre = [sum(xyz[n][i] for n in supports[name])/len(supports[name]) for i in range(3)]
            patches[name] = {
                "bottom_reaction_n": [sum(f[i] for _, f in patch) for i in range(3)],
                "moment_about_origin_nmm": [sum(cross(p, f)[i] for p, f in patch) for i in range(3)],
                "reference_mm": centre,
                "moment_about_bottom_centroid_nmm": [sum(cross([p[j]-centre[j] for j in range(3)], f)[i] for p, f in patch) for i in range(3)],
            }
        load = max(0., time-1.)*1200
        forces.extend((positions[n], (0., 0., -v*GRAVITY_PER_MM3_N*min(time, 1.))) for n, v in weights.items())
        forces.extend((positions[n], (0., 0., -load/5)) for n in record["load_nodes"])
        force = [sum(f[i] for _, f in forces) for i in range(3)]
        moment = [sum(cross(p, f)[i] for p, f in forces) for i in range(3)]
        if not all(math.isfinite(v) for p, f in forces for v in (*p, *f)):
            raise ValueError("Nonfinite force/moment arithmetic")
        endpoints.append({"time": time, "force_residual_n": force, "moment_residual_nmm": moment,
                          "global_gate_pass": max(map(abs, force)) <= .1 and max(map(abs, moment)) <= 1.,
                          "loaded_node_displacement_mm": {str(n): list(u[n]) for n in record["load_nodes"]},
                          "maximum_loaded_node_displacement_mm": max(math.hypot(*u[n]) for n in record["load_nodes"]),
                          "patches": patches})
        if time in (1., 2.):
            bound = equilibrium_print_bound(time, rounding, weights, ground, supports, record["load_nodes"])
            bound["moment_interval_nmm"] = [[m-e, m+e] for m, e in zip(moment, bound["moment_nmm"], strict=True)]
            endpoints[-1]["dat_print_rounding_bound"] = bound
    return {"increment": record["increment"], "exit_code": record["exit_code"],
            "elapsed_seconds": record["elapsed_seconds"], "status": record["status"],
            "accepted_increments": rows, "diagnostic_endpoints": endpoints}


def read_archive(path):
    with tarfile.open(path) as archive:
        members = [m for m in archive.getmembers() if m.isfile()]
        if len({m.name for m in members}) != len(members):
            raise ValueError("Duplicate archive members")
        return {m.name: archive.extractfile(m).read() for m in members}


def verified_baseline(root):
    report = json.loads((root/"report.json").read_text())
    validation_bytes = (root/"weight_validation.json").read_bytes()
    if digest(validation_bytes) != report["weight_validation_sha256"]:
        raise ValueError("Baseline integration witness digest differs")
    item = report["formulations"]["mortar"]
    path = root/item["archive"]
    if digest(path.read_bytes()) != item["archive_sha256"]:
        raise ValueError("Baseline archive differs from published witness")
    files = read_archive(path)
    if {n: digest(v) for n, v in files.items()} != item["archive_contents_sha256"]:
        raise ValueError("Baseline archive contents differ")
    witness = json.loads(validation_bytes)["formulations"]["mortar"]
    record = json.loads(files["frame.json"])
    weights = {int(n): v for n, v in record["nodal_volume_mm3"].items()}
    if (witness["weight_validation_pass"] is not True or
            digest(files["frame.json"]) != witness["terminal_context_sha256"] or
            digest(files["frame.dat"]) != witness["dat_sha256"] or
            record["deck_sha256"] != witness["deck_sha256"] or
            digest(json.dumps(weights, sort_keys=True).encode()) != witness["integrated_weights_sha256"] or
            len(weights) != witness["weight_count"] or
            sum(v < 0 for v in weights.values()) != witness["negative_weight_count"]):
        raise ValueError("Baseline nodal weights are not bound to integration witness")
    return path, files


def publish(directories, destination):
    if destination.exists():
        raise ValueError("Refusing to overwrite published study")
    baseline, baseline_files = verified_baseline(Path("fea/results/full_frame_mortar"))
    filesets = [("baseline", baseline_files)]
    for directory in directories:
        record = json.loads((directory/"frame.json").read_text())
        if "RUNNING" in record["status"] or record["formulation"] != "mortar":
            raise ValueError("Expected terminal MORTAR run")
        filesets.append((str(record["increment"]), {str(p.relative_to(directory)): p.read_bytes()
                                                  for p in directory.rglob("*") if p.is_file()}))
    if {json.loads(files["frame.json"])["increment"] for _, files in filesets} != {.25, .125, .0625} or len(filesets) != 3:
        raise ValueError("Expected exactly the predeclared three increments")
    baseline_deck = filesets[0][1]["frame.inp"]
    baseline_weights = json.loads(filesets[0][1]["frame.json"])["nodal_volume_mm3"]
    result = {"qualification": "Increment sensitivity only; unchanged global gates, no local contact/physical acceptance",
              "baseline_archive": str(baseline), "baseline_archive_sha256": digest(baseline.read_bytes()), "runs": {}}
    for name, files in filesets:
        item = replay(files)
        increment = item["increment"]
        if files["frame.inp"] != baseline_deck.replace(b"0.25,1,1e-6,0.25", f"{increment:g},1,1e-6,{increment:g}".encode()):
            raise ValueError("Refined deck changes more than declared increments")
        if json.loads(files["frame.json"])["nodal_volume_mm3"] != baseline_weights:
            raise ValueError("Refinement weights differ from independently reintegrated baseline")
        result["runs"][name] = item
    common = set.intersection(*({row["time"] for row in item["diagnostic_endpoints"]} for item in result["runs"].values()))
    result["common_accepted_times"] = sorted(common)
    # Keep a failed packaging attempt out of the public destination and retain
    # its evidence for diagnosis. This does not overwrite any prior study.
    staging = Path(tempfile.mkdtemp(prefix="refinement-publication-", dir="fea/generated"))
    for name, files in filesets[1:]:
        directory = next(d for d in directories if json.loads((d/"frame.json").read_text())["increment"] == float(name))
        path = staging/(name+".tar.gz")
        with tarfile.open(path, "w:gz") as archive:
            for member in sorted(files):
                archive.add(directory/member, arcname=member, recursive=False)
        if path.stat().st_size >= 100_000_000:
            raise ValueError("Archive exceeds GitHub file limit; retain generated evidence and split packaging")
        result["runs"][name].update(archive=path.name, archive_sha256=digest(path.read_bytes()),
                                    archive_contents_sha256={n: digest(v) for n, v in files.items()})
    result["publisher_sha256"] = digest(Path(__file__).read_bytes())
    (staging/"publisher.py").write_bytes(Path(__file__).read_bytes())
    (staging/"report.json").write_text(json.dumps(result, indent=2, allow_nan=False)+"\n")
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists():
        raise ValueError("Destination appeared during packaging; preserving staged evidence")
    staging.rename(destination)
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directories", nargs=2, type=Path)
    parser.add_argument("--output", type=Path, default=Path("fea/results/full_frame_refinement"))
    args = parser.parse_args()
    publish(args.directories, args.output)
