"""Fail-only partial quiescent diagnosis from retained bytes; never run a solver."""
import argparse
import hashlib
import json
import math
import re
import sys
import tempfile
import types
from pathlib import Path

_SOURCE_HASH_AT_IMPORT = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
INPUTS = ("context.json", "control.inp", "control.dat", "control.sta", "exit.json", "container-probe.json", "freeze.json", "launch.json")
FACES = ((0, 1, 2, 4, 5, 6), (0, 3, 1, 7, 8, 4),
         (1, 3, 2, 8, 9, 5), (2, 3, 0, 9, 7, 6))
LIMITS = ("Partial accepted-state failure diagnosis only. No complete contact-output, CF impulse, "
          "native total contact energy, total-energy balance, moving-case or physical qualification.")
_CONFIGURATION_AT_IMPORT = (INPUTS, FACES, LIMITS)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def input_path(name):
    return Path("frozen" if name == "context.json" else "" if name in ("freeze.json", "launch.json") else "result") / name


def source_snapshot():
    """Reject changed source bytes, constants or loaded functions before publication."""
    if (INPUTS, FACES, LIMITS) != _CONFIGURATION_AT_IMPORT:
        raise ValueError("Diagnostic configuration changed after import")
    path = Path(__file__).resolve()
    data = path.read_bytes()
    if hashlib.sha256(data).hexdigest() != _SOURCE_HASH_AT_IMPORT:
        raise ValueError("Diagnostic source changed after import")
    module = sys.modules[__name__]
    for code in compile(data, str(path), "exec").co_consts:
        if isinstance(code, types.CodeType) and code.co_name.isidentifier():
            loaded = getattr(module, code.co_name, None)
            if not isinstance(loaded, types.FunctionType) or loaded.__code__ != code:
                raise ValueError("Loaded diagnostic function differs from source")
    return data


def actual_mesh(text, context):
    nodes, elements, surfaces, owners = {}, {}, {}, {}
    mode, name = None, None
    for line in text.splitlines():
        if not line or line.startswith("**"):
            continue
        if line.startswith("*"):
            mode = None
            if line == "*NODE":
                mode = "node"
            elif line.startswith("*ELEMENT,TYPE=C3D10,ELSET="):
                mode, name = "element", line.split("ELSET=")[1]
                if name in owners:
                    raise ValueError("Duplicate body element section")
                owners[name] = []
            elif line.startswith("*SURFACE,NAME="):
                mode, name = "surface", line.split("NAME=")[1]
                if name in surfaces:
                    raise ValueError("Duplicate deck surface")
                surfaces[name] = []
            continue
        fields = line.split(",")
        if mode == "node":
            tag, xyz = int(fields[0]), tuple(map(float, fields[1:]))
            if tag in nodes or len(xyz) != 3 or not all(map(math.isfinite, xyz)):
                raise ValueError("Invalid or duplicate deck node")
            nodes[tag] = xyz
        elif mode == "element":
            tag, ids = int(fields[0]), tuple(map(int, fields[1:]))
            if tag in elements or len(ids) != 10 or len(set(ids)) != 10:
                raise ValueError("Invalid or duplicate C3D10")
            elements[tag] = ids
            owners[name].append(tag)
        elif mode == "surface":
            if len(fields) != 2 or not re.fullmatch(r"S[1-4]", fields[1]):
                raise ValueError("Invalid quadratic surface face")
            surfaces[name].append((int(fields[0]), int(fields[1][1:])))
    if nodes != {int(n): tuple(p) for n, p in context["nodes"].items()} or elements != {int(e): tuple(ns) for e, ns in context["elements"].items()}:
        raise ValueError("Actual deck mesh differs from frozen context")
    if set(owners) != {"BOLT_NUT", "WASHER"} or set(surfaces) != set(context["surfaces"]):
        raise ValueError("Missing body or surface inventory")
    seen, exterior = set(), {}
    for name, ids in owners.items():
        body = context["bodies"][name]
        ns = {n for e in ids for n in elements[e]}
        if set(ids) != set(body["elements"]) or ns != set(body["nodes"]) or seen & ns:
            raise ValueError("Actual body ownership differs")
        seen.update(ns)
        for e in ids:
            for f, indices in enumerate(FACES, 1):
                face = tuple(elements[e][i] for i in indices)
                exterior.setdefault(tuple(sorted(face[:3])), []).append((e, f, face))
    if seen != set(nodes):
        raise ValueError("Body ownership does not cover nodes")
    boundary = {(e, f): ns for entries in exterior.values() if len(entries) == 1 for e, f, ns in entries}
    for name, pairs in surfaces.items():
        saved = context["surfaces"][name]
        if (not pairs or len(pairs) != len(set(pairs)) or set(pairs) != {tuple(p) for p in saved["faces"]}
                or not set(pairs) <= boundary.keys()
                or {n for pair in pairs for n in boundary[pair]} != set(saved["nodes"])):
            raise ValueError("Actual quadratic surface/context selection differs")
    return nodes, surfaces


def sections(text):
    """Keep numeric rows in order; repeated element/face keys are integration points."""
    result = []
    for line in text.splitlines():
        value = line.strip()
        if not value:
            continue
        if value[0].isalpha():
            result.append([value, []])
        elif result:
            result[-1][1].append(value.split())
    return result


def accepted_time(text):
    accepted = []
    for line in text.splitlines():
        row = line.split()
        if not row or not row[0].isdigit():
            continue
        if len(row) != 7:
            raise ValueError("Malformed STA row")
        if row[2].endswith("U"):
            continue
        if int(row[0]) != 1 or int(row[1]) != len(accepted) + 1:
            raise ValueError("Unexpected accepted increment sequence")
        accepted.append(float(row[4].replace("D", "E")))
    if len(accepted) != 1 or not math.isfinite(accepted[0]) or accepted[0] <= 0:
        raise ValueError("This partial diagnostic requires exactly one accepted state")
    return accepted[0]


def diagnose(files):
    """Return observed failures, never infer success from partial output."""
    if set(files) != set(INPUTS):
        raise ValueError("Missing or extra diagnostic inputs")
    freeze = json.loads(files["freeze.json"])
    launch = json.loads(files["launch.json"])
    if sha(files["freeze.json"]) != launch["freeze_sha256"] or freeze["case"] != "quiescent":
        raise ValueError("Launch/freeze identity differs")
    for name in ("context.json", "control.inp"):
        if sha(files[name]) != freeze["inputs_sha256"][name]:
            raise ValueError("Frozen diagnostic input hash differs: " + name)
    context = json.loads(files["context.json"])
    if sha(files["control.inp"]) != context["deck_sha256"]["quiescent"]:
        raise ValueError("Quiescent deck hash differs")
    exit_record = json.loads(files["exit.json"])
    for name in ("control.inp", "control.dat", "control.sta", "container-probe.json"):
        if sha(files[name]) != exit_record["output_sha256"][name]:
            raise ValueError("Retained native output hash differs")
    probe = json.loads(files["container-probe.json"])
    inspected = json.loads(probe["stdout"])
    if (exit_record["returncode"] != 124 or exit_record["cleanup_returncode"] != 0
            or probe["returncode"] != 0 or len(inspected) != 1
            or inspected[0]["Id"] != exit_record["owned_container_id"]
            or inspected[0]["State"]["Running"] is not False
            or inspected[0]["State"]["ExitCode"] != 124 or inspected[0]["State"]["OOMKilled"] is not False):
        raise ValueError("Expected retained stopped timeout with successful cleanup")
    _, surfaces = actual_mesh(files["control.inp"].decode(), context)
    time = accepted_time(files["control.sta"].decode())
    if time >= context["cases"]["quiescent"]["total_time_s"]:
        raise ValueError("Expected an incomplete quiescent time window")
    parsed = sections(files["control.dat"].decode())

    def block(prefix, width):
        found = [(i, h, rows) for i, (h, rows) in enumerate(parsed) if h.startswith(prefix)]
        if len(found) != 1:
            raise ValueError("Missing or duplicate DAT block: " + prefix)
        index, header, raw = found[0]
        match = re.search(r"and time\s+(\S+)$", header)
        if index == len(parsed)-1 or not match or float(match[1]) != time:
            raise ValueError("Unterminated or mismatched-time DAT block")
        if not raw or any(len(r) != width for r in raw):
            raise ValueError("Missing or malformed DAT rows")
        rows = [tuple(map(float, r)) for r in raw]
        if not all(math.isfinite(v) for row in rows for v in row):
            raise ValueError("Nonfinite DAT value")
        return rows

    body_results = {}
    for name in ("BOLT_NUT", "WASHER"):
        result = {}
        for label, key in (("displacements", "max_displacement_mm"), ("velocities", "max_speed_mm_s")):
            rows = block(f"{label} (vx,vy,vz) for set {name} and time", 4)
            ids = [r[0] for r in rows]
            if len(ids) != len(set(ids)) or set(ids) != set(context["bodies"][name]["nodes"]):
                raise ValueError("Missing or duplicate body U/V nodes")
            result[key] = max(math.hypot(*r[1:]) for r in rows)
        body_results[name] = result
    dis = block("relative contact displacement (slave element+face,normal,tang1,tang2)", 5)
    stress = block("contact stress (slave element+face,press,tang1,tang2)", 5)
    energy = block("contact spring energy (slave element+face,energy)", 3)
    if not ([r[:2] for r in dis] == [r[:2] for r in stress] == [r[:2] for r in energy]):
        raise ValueError("Contact point row counts/order do not align")
    pairs = {p["slave"]: p for p in context["contact_pairs"]}
    if set(pairs) != {"WASHER_HEAD", "WASHER_BORE"}:
        raise ValueError("Expected two washer slave pairs")
    grouped = {name: [] for name in pairs}
    for d, s, e in zip(dis, stress, energy, strict=True):
        names = [name for name in pairs if d[:2] in surfaces[name]]
        if len(names) != 1 or any(v != int(v) for v in d[:2]):
            raise ValueError("Contact output references unknown or ambiguous slave face")
        if s[2] < 0 or e[2] < 0:
            raise ValueError("Negative pressure or contact energy")
        penalty = pairs[names[0]]["normal_penalty_n_mm3"]
        if not math.isclose(s[2], max(0., -penalty*d[2]), rel_tol=2e-6, abs_tol=1e-10):
            raise ValueError("Native contact pressure/penetration convention differs")
        grouped[names[0]].append((d, s, e))
    pair_results = {}
    for name, rows in grouped.items():
        if not rows:
            raise ValueError("No recorded points for one expected interface")
        pair_results[name] = {"point_rows": len(rows), "reported_slave_faces": len({d[:2] for d, _, _ in rows}),
            "selected_quadratic_slave_faces": len(surfaces[name]),
            "max_penetration_mm": max(max(0., -d[2]) for d, _, _ in rows),
            "max_pressure_N_mm2": max(s[2] for _, s, _ in rows),
            "max_abs_tangential_stress_N_mm2": max(abs(v) for _, s, _ in rows for v in s[3:]),
            "sum_recorded_CELS_N_mm": math.fsum(e[2] for _, _, e in rows)}
    gates = context["quiescent_diagnostic_gates"]
    energy_limit = gates["max_total_ELSE_ELKE_CELS_over_E_star"] * context["diagnostic_reference_scales"]["E_star_N_mm"]
    failures = []
    for name, result in body_results.items():
        for field, gate in (("max_speed_mm_s", "max_velocity_mm_s"), ("max_displacement_mm", "max_displacement_mm")):
            if result[field] > gates[gate]:
                failures.append({"body": name, "quantity": field, "observed": result[field], "limit": gates[gate]})
    for name, result in pair_results.items():
        if result["max_penetration_mm"] > gates["max_normal_penetration_mm"]:
            failures.append({"pair": name, "quantity": "max_penetration_mm", "observed": result["max_penetration_mm"], "limit": gates["max_normal_penetration_mm"]})
    energy_sum = math.fsum(r["sum_recorded_CELS_N_mm"] for r in pair_results.values())
    if energy_sum > energy_limit:
        failures.append({"quantity": "sum_recorded_CELS_alone_N_mm", "observed": energy_sum, "limit": energy_limit})
    missing = [label for label, prefix in (("native total CELS scalar", "total contact spring energy for time"),
               ("CNUM", "total number of contact elements for time"), ("pair CF statistics", "statistics for slave"))
               if not any(h.startswith(prefix) and rows for h, rows in parsed)]
    return {"status": "PARTIAL QUIESCENT GATES FAILED" if failures else "PARTIAL OUTPUT; NO ACCEPTANCE INFERRED",
            "limits": LIMITS, "accepted_time_s": time, "body_results": body_results, "pair_results": pair_results,
            "aligned_contact_point_rows": len(dis), "failures": failures,
            "native_total_contact_energy_qualified": False, "CF_impulse_qualified": False,
            "missing_tail": missing,
            "input_sha256": {name: sha(data) for name, data in files.items()}}


def write_diagnostic(directory, parent):
    directory, parent = Path(directory), Path(parent)
    source = source_snapshot()
    files = {name: (directory / input_path(name)).read_bytes() for name in INPUTS}
    report = diagnose(files)
    if source_snapshot() != source:
        raise ValueError("Diagnostic source changed while reading evidence")
    parent.mkdir(parents=True, exist_ok=True)
    destination = Path(tempfile.mkdtemp(prefix="partial-quiescent-", dir=parent))
    (destination / "quiescent_hardware_diagnostic.py.snapshot").write_bytes(source)
    report["diagnostic_source_sha256"] = sha(source)
    (destination / "report.json").write_text(json.dumps(report, indent=2, allow_nan=False) + "\n")
    return destination


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path)
    parser.add_argument("--output", type=Path, default=Path("fea/generated/quiescent-diagnostics"))
    args = parser.parse_args()
    print(write_diagnostic(args.directory, args.output))
