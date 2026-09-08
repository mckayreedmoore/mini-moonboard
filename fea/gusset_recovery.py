"""Native prescribed-displacement gusset diagnostic, not physical bolt demand."""
import gzip
import json
import math
import os
import subprocess
import tarfile
import tempfile
from pathlib import Path

from fea.floor_contact import mesh
from fea.floor_contact_results import blocks, cross
from fea.frd_displacements import read
from fea.prescribed_tet_control import IMAGE
from fea.solve_easy_frame import digest
from fea.timber_asymmetric import HOLDS, mesh_text, unchanged
from fea.wide_asymmetric import authenticated_inputs

MAP = Path("fea/results/gusset-interfaces.json")
ARCHIVE = Path("fea/results/gusset-recovery.tar.gz")
LIMITS = "Bonded isotropic parent-model recovery only; no actual bolt demands or joint qualification."
# Frozen before the first actual recovery run. Numerical gates, not safety factors.
GATES = {"unshared_node_force_n": 1., "displacement_error_mm": 1e-8,
         "rounding_force_absolute_n": 1., "rounding_moment_absolute_nmm": 1000.,
         "rounding_relative": .01}


def prescribed_deck(nodes, elements, fields, digits):
    if digits not in (5, 6) or set(fields) != {1., 2., 3.}:
        raise ValueError("Require three bases at five or six significant digits")
    lines = [mesh_text(nodes, elements), "*NSET,NSET=ALLN"]
    ids = sorted(nodes)
    lines += [",".join(map(str, ids[i:i+16])) for i in range(0, len(ids), 16)]
    lines += ["*MATERIAL,NAME=MAT", "*ELASTIC", "7000,0.3",
              "*SOLID SECTION,ELSET=TIMBER,MATERIAL=MAT"]
    for time in sorted(fields):
        if set(fields[time]) != set(nodes):
            raise ValueError("Prescribed node coverage differs")
        lines += ["*STEP", "*STATIC", "*BOUNDARY,OP=NEW"]
        for n in ids:
            values = fields[time][n]
            if len(values) != 3 or not all(map(math.isfinite, values)):
                raise ValueError("Invalid displacement vector")
            lines += [f"{n},{i},{i},{v:.{digits}g}" for i, v in enumerate(values, 1)]
        lines += ["*NODE PRINT,NSET=ALLN", "U,RF", "*END STEP"]
    return "\n".join(lines)+"\n"


def partition(gusset):
    """Disjoint membership buckets; shared-edge forces have no unique interface."""
    membership = {n: [] for n in gusset["node_ids"]}
    for name, faces in sorted(gusset["interfaces"].items()):
        for n in {n for face in faces for n in face["nodes"]}:
            membership[n].append(name)
    result = {}
    for n, names in membership.items():
        result.setdefault(" & ".join(names) or "unshared", []).append(n)
    if set(gusset["shared_nodes"]) != {n for n, names in membership.items() if names}:
        raise ValueError("Unclassified shared node")
    return result


def summarize(data, nodes, fields, digits, gussets):
    parsed = blocks(data)
    if set(parsed) != {(kind, "ALLN", t) for kind in ("displacements", "forces") for t in fields}:
        raise ValueError("Incomplete or unexpected output steps")
    result = {}
    for t in sorted(fields):
        u, forces = (parsed[kind, "ALLN", t] for kind in ("displacements", "forces"))
        if set(u) != set(forces) or set(u) != set(nodes):
            raise ValueError("Incomplete recovery output nodes")
        error = max(abs(u[n][i]-float(f"{v:.{digits}g}"))
                    for n, values in fields[t].items() for i, v in enumerate(values))
        sides = {}
        for side, gusset in gussets.items():
            groups = partition(gusset)
            # Local moment origin avoids making rounding checks depend on frame width.
            origin = [math.fsum(nodes[n][i] for n in gusset["node_ids"])/len(gusset["node_ids"])
                      for i in range(3)]
            buckets = {}
            for name, ids in groups.items():
                moments = [cross([nodes[n][i]-origin[i] for i in range(3)], forces[n]) for n in ids]
                buckets[name] = {"node_count": len(ids),
                    "force_n": [math.fsum(forces[n][i] for n in ids) for i in range(3)],
                    "moment_nmm": [math.fsum(m[i] for m in moments) for i in range(3)],
                    "maximum_node_force_n": max(math.hypot(*forces[n]) for n in ids)}
            residual = [math.fsum(row[key][i] for row in buckets.values())
                        for key in ("force_n", "moment_nmm") for i in range(3)]
            sides[side] = {"moment_origin_mm": origin, "buckets": buckets,
                           "body_residual_n_nmm": residual}
        result[str(t)] = {"maximum_displacement_error_mm": error, "sides": sides}
    return result


def compare(nominal, rounded):
    failures, changes = [], []
    for time, step in nominal.items():
        for label, run in (("six_digit", nominal), ("five_digit", rounded)):
            if run[time]["maximum_displacement_error_mm"] > GATES["displacement_error_mm"]:
                failures.append(f"{time}/{label}: displacement mismatch")
        for side, row in step["sides"].items():
            for label, run in (("six_digit", nominal), ("five_digit", rounded)):
                if run[time]["sides"][side]["buckets"]["unshared"]["maximum_node_force_n"] > GATES["unshared_node_force_n"]:
                    failures.append(f"{time}/{side}/{label}: unshared node residual")
            for name, bucket in row["buckets"].items():
                other = rounded[time]["sides"][side]["buckets"][name]
                for key, absolute in (("force_n", GATES["rounding_force_absolute_n"]),
                                      ("moment_nmm", GATES["rounding_moment_absolute_nmm"])):
                    delta = math.dist(bucket[key], other[key])
                    limit = max(absolute, GATES["rounding_relative"]*math.hypot(*bucket[key]))
                    changes.append({"time": time, "side": side, "bucket": name,
                                    "quantity": key, "difference": delta, "limit": limit})
                    if delta > limit:
                        failures.append(f"{time}/{side}/{name}/{key}: rounding sensitivity")
    return {"passed_numerical_gates": not failures, "failures": failures, "rounding_checks": changes}


def run():
    if ARCHIVE.exists():
        raise FileExistsError("Refusing to overwrite recovery evidence")
    _, parent, _, sources = authenticated_inputs()
    mapping = json.loads(MAP.read_text())
    unchanged(mapping["source_sha256"])
    sources.update(mapping["source_sha256"])
    for p in (MAP, Path("fea/gusset_recovery.py"), Path("fea/frd_displacements.py"), Path("fea/prescribed_tet_control.py"),
              Path("fea/floor_contact.py"), Path("fea/floor_contact_results.py")):
        sources[str(p)] = digest(p)
    all_nodes, all_elements = mesh(parent)
    gussets = mapping["gussets"]
    ids = {n for g in gussets.values() for n in g["node_ids"]}
    nodes = {n: all_nodes[n] for n in ids}
    elements = {e: all_elements[e] for g in gussets.values() for e in g["element_ids"]}
    if {n for row in elements.values() for n in row} != ids:
        raise ValueError("Gusset mesh coverage differs")
    directory = Path(tempfile.mkdtemp(prefix="gusset-recovery-", dir="fea/generated")).resolve()
    report = {"limits": LIMITS, "image": IMAGE, "gates": GATES, "source_sha256": sources,
              "parent_frd_sha256": {}, "runs": {}, "comparisons": {}}
    for hold in HOLDS:
        record_path = Path(f"fea/results/wide-asymmetric/{hold}.json.gz")
        record = json.loads(gzip.decompress(record_path.read_bytes()))
        sources[str(record_path)] = digest(record_path)
        prefix = Path(f"fea/generated/wide-asymmetric/{hold}")
        for suffix in (".inp", ".frd"):
            p = prefix.with_suffix(suffix)
            if digest(p) != record["artifacts"][p.name]:
                raise ValueError("Parent input/FRD identity differs")
        if mesh(prefix.with_suffix(".inp").read_text()) != (all_nodes, all_elements):
            raise ValueError("Basis mesh differs from accepted mesh")
        report["parent_frd_sha256"][hold] = digest(prefix.with_suffix(".frd"))
        fields = read(prefix.with_suffix(".frd").read_text(), all_nodes, ids)
        (directory/f"{hold}.selected.json").write_text(json.dumps(fields, sort_keys=True)+"\n")
        for digits in (6, 5):
            name = f"{hold}-{digits}"
            (directory/f"{name}.inp").write_text(prescribed_deck(nodes, elements, fields, digits))
            command = ["docker", "run", "--rm", "--network=none", "--cpus=1", "--memory=1g",
                       "--read-only", "--tmpfs", "/tmp:rw,noexec,nosuid,size=64m",
                       "--user", f"{os.getuid()}:{os.getgid()}", "-e", "OMP_NUM_THREADS=1",
                       "-v", f"{directory}:/work", "-w", "/work", IMAGE, "ccx", "-i", name]
            with (directory/f"{name}.log").open("w") as log:
                done = subprocess.run(command, stdout=log, stderr=subprocess.STDOUT, timeout=60, check=False)
            if done.returncode or "*ERROR" in (directory/f"{name}.log").read_text().upper():
                raise RuntimeError(f"Solver failure retained in {directory}")
            report["runs"][name] = summarize((directory/f"{name}.dat").read_text(), nodes, fields, digits, gussets)
        report["comparisons"][hold] = compare(report["runs"][f"{hold}-6"], report["runs"][f"{hold}-5"])
    unchanged(sources)
    report["passed_numerical_gates"] = all(r["passed_numerical_gates"] for r in report["comparisons"].values())
    report["artifact_sha256"] = {p.name: digest(p) for p in directory.iterdir() if p.is_file()}
    (directory/"report.json").write_text(json.dumps(report, indent=2, allow_nan=False)+"\n")
    with tarfile.open(ARCHIVE, "x:gz") as archive:
        for p in sorted(directory.iterdir()):
            archive.add(p, arcname=p.name)
    print(directory)
    print(json.dumps({k: v["failures"] for k, v in report["comparisons"].items()}))


if __name__ == "__main__":
    run()
