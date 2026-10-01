"""Offline force, geometry, convergence, and provenance audit of the two fixtures."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import re


HERE = Path(__file__).resolve().parent
CASES = {"mortar_c3d10", "penalty_c3d10"}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def number(value):
    # Fortran Ew.d omits E when an exponent has three digits (Intel reference).
    match = re.fullmatch(r"\s*([+-]?(?:\d+\.\d*|\.\d+))([+-]\d{3})\s*", value)
    if match and abs(int(match[2])) > 99:
        value = match[1] + "E" + match[2]
    result = float(value.replace("D", "E"))
    require(math.isfinite(result), "Nonfinite numeric evidence")
    return result


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_json(path):
    def pairs(items):
        result = {}
        for name, value in items:
            require(name not in result, f"Duplicate JSON key: {name}")
            result[name] = value
        return result
    return json.loads(path.read_text(), object_pairs_hook=pairs,
                      parse_constant=lambda x: number(x))


def mesh(path):
    nodes, parts, section = {}, {"UPPER": set(), "LOWER": set()}, None
    for line in path.read_text().splitlines():
        if line.startswith("**") or not line.strip():
            continue
        if line.startswith("*"):
            section = "NODE" if line == "*NODE" else None
            if line.startswith("*ELEMENT,TYPE=C3D10,ELSET="):
                section = line.split("ELSET=")[1]
            continue
        values = line.split(",")
        if section == "NODE":
            node = int(values[0])
            require(node not in nodes and len(values) == 4, "Bad mesh node")
            nodes[node] = tuple(map(number, values[1:]))
        elif section in parts:
            require(len(values) == 11, "Not a C3D10 element")
            parts[section].update(map(int, values[1:]))
    require(len(nodes) == 54 and all(len(p) == 27 for p in parts.values()),
            "Fixture mesh coverage differs")
    require(parts["UPPER"].isdisjoint(parts["LOWER"]) and
            parts["UPPER"] | parts["LOWER"] == set(nodes), "Body ownership differs")
    faces = {
        "top": {n for n in parts["UPPER"] if nodes[n][2] == 2},
        "bottom": {n for n in parts["LOWER"] if nodes[n][2] == -2},
        "upper_interface": {n for n in parts["UPPER"] if nodes[n][2] == 0},
        "lower_interface": {n for n in parts["LOWER"] if nodes[n][2] == 0},
    }
    require(all(len(v) == 9 for v in faces.values()), "Face node coverage differs")
    return nodes, parts, faces


def dat(path, node_ids):
    result, active = {}, None
    for line in path.read_text().splitlines():
        match = re.match(r"\s*(displacements|forces).*for set (\w+) and time\s+(\S+)", line)
        if match:
            quantity, nset, time = match.groups()
            require(nset == "ALLNODES", f"Unexpected DAT set {nset}")
            key = (number(time), quantity)
            require(key not in result, f"Duplicate DAT field {key}")
            active = result[key] = {}
            continue
        fields = line.split()
        if active is not None and len(fields) == 4 and fields[0].isdigit():
            node = int(fields[0])
            require(node in node_ids and node not in active, "Bad/duplicate DAT node")
            active[node] = tuple(map(number, fields[1:]))
    require(result, "No nodal DAT evidence")
    require(all(set(v) == node_ids for v in result.values()), "Incomplete DAT node coverage")
    return result


def numeric_rows(path, count):
    rows = []
    for line in path.read_text().splitlines():
        fields = line.split()
        if not fields or not fields[0].isdigit():
            continue
        require(len(fields) == count, f"Malformed row in {path.name}: {line}")
        rows.append(fields)
    require(rows, f"No numeric rows in {path.name}")
    return rows


def convergence(folder, mortar):
    cvg = numeric_rows(folder / "coupon.cvg", 9)
    keys = [tuple(map(int, row[:4])) for row in cvg]
    require(len(keys) == len(set(keys)), "Duplicate CVG key")
    for row in cvg:
        for value in row[4:]:
            number(value)
    groups = {}
    for key in keys:
        groups.setdefault(key[:3], []).append(key[3])
    for key, iterations in groups.items():
        require(iterations == list(range(1, max(iterations) + 1)),
                f"Incomplete iteration sequence {key}")
    transcripts = {}
    full_transcript = False
    for path in (folder / "coupon.stdout", folder / "coupon.log"):
        if not path.exists():
            continue
        contents = path.read_text()
        require("*ERROR" not in contents.upper(), f"Native error in {path.name}")
        step = inc = attempt = None
        printed = []
        for line in contents.splitlines():
            if match := re.fullmatch(r"\s*STEP\s+(\d+)\s*", line):
                step = int(match[1])
                inc = attempt = None
            elif match := re.fullmatch(r"\s*increment\s+(\d+)\s+attempt\s+(\d+)\s*", line):
                inc, attempt = map(int, match.groups())
            elif match := re.fullmatch(r"\s*iteration\s+(\d+)\s*", line):
                require(None not in (step, inc, attempt), "Iteration lacks full identity")
                printed.append((step, inc, attempt, int(match[1])))
        if printed:
            require(len(printed) == len(set(printed)) and all(k in keys for k in printed),
                    f"{path.name}/CVG iteration identities differ")
            indices = [keys.index(k) for k in printed]
            require(indices == sorted(indices), f"{path.name} iteration order differs")
            full_transcript = full_transcript or printed == keys
            transcripts[path.name] = len(printed)
    require(full_transcript, "Missing full native iteration transcript")
    max_iteration = max(k[3] for k in keys)
    if mortar:
        require(max_iteration <= 14, "MORTAR source override threshold reached")
    states, rejected_attempts = [], []
    for row in numeric_rows(folder / "coupon.sta", 7):
        rejected = row[2].endswith("U")
        step, inc, attempt, iterations = map(int, (row[0], row[1], row[2].removesuffix("U"), row[3]))
        require(groups.get((step, inc, attempt), [])[-1:] == [iterations],
                "STA iteration differs from final CVG row")
        total, relative, dt = map(number, row[4:])
        if rejected:
            rejected_attempts.append([step, inc, attempt, iterations])
            continue
        # Pinned 2.23 checkconvergence.c:149-162 requires iit>1 for mechanical
        # convergence. This is a source identity check, not a new tolerance.
        require(step == 1 and inc > 0 and attempt > 0 and iterations >= 2,
                "Invalid accepted state identity")
        require(0 < relative <= 1.000001 and 0 < dt <= 0.100001,
                "Accepted increment outside frozen schedule")
        require(abs(total - (step - 1 + relative)) < 2e-6, "STA step/total time differs")
        require(not states or total > states[-1]["total"], "Nonincreasing accepted time")
        states.append({"step": step, "increment": inc, "attempt": attempt,
                       "iterations": iterations, "total": total, "relative": relative})
    require({s["step"] for s in states} == {1}, "Missing accepted step")
    for step in (1,):
        sequence = [s for s in states if s["step"] == step]
        require([s["increment"] for s in sequence] == list(range(1, len(sequence) + 1)),
                "Missing accepted increment")
        require(abs(sequence[-1]["relative"] - 1) < 1e-6, "Incomplete step endpoint")
    require(keys[-1] == tuple(states[-1][k] for k in
                             ("step", "increment", "attempt", "iterations")),
            "Unaccepted terminal CVG tail")
    return states, {"cvg_rows": len(keys), "transcript_iteration_counts": transcripts,
                    "max_iteration": max_iteration, "rejected_attempts": rejected_attempts}


def frd_fields(path, states, node_ids):
    blocks, time, active, labels = [], None, None, []
    identity = kind = None
    for line in path.read_text().splitlines():
        fields = line.split()
        if fields and fields[0] == "1PSTEP":
            require(active is None, "Unterminated FRD dataset")
            identity = (int(fields[3]), int(fields[2]))
        elif fields and fields[0] == "100CL":
            time = number(fields[2])
        elif line.startswith(" -4"):
            require(active is None, "Unterminated FRD field")
            kind = fields[1]
            require(kind in ("DISP", "FORC", "CONTACT"), f"Unexpected FRD field {kind}")
            active = {}
            labels = []
        elif active is not None and line.startswith(" -5"):
            labels.append(fields[1])
        elif active is not None and line.startswith(" -1"):
            node = int(line[3:13])
            require(node in node_ids and node not in active, "Bad/duplicate FRD node")
            values = [number(line[i:i+12]) for i in range(13, len(line.rstrip()), 12)]
            require(len(values) == (6 if kind == "CONTACT" else 3), "Malformed FRD record")
            active[node] = values
        elif active is not None and line.startswith(" -3"):
            require(time is not None and identity is not None and active, "Empty/untimed FRD block")
            matches = [s for s in states if (s["step"], s["increment"]) == identity
                       and abs(s["total"]-time) < 2e-6]
            require(len(matches) == 1, "FRD dataset does not match an accepted state")
            require(not any(b["identity"] == identity and b["kind"] == kind for b in blocks),
                    "Duplicate FRD field/state")
            summary = {"time": time, "identity": identity, "kind": kind, "nodes": len(active)}
            if kind == "CONTACT":
                require(labels == ["COPEN", "CSLIP1", "CSLIP2", "CPRESS", "CSHEAR1", "CSHEAR2"],
                        "Unexpected contact components")
                summary.update(COPEN_min=min(v[0] for v in active.values()),
                               COPEN_max=max(v[0] for v in active.values()),
                               CPRESS_min=min(v[3] for v in active.values()),
                               CPRESS_max=max(v[3] for v in active.values()))
            else:
                require(set(active) == node_ids, "Incomplete FRD nodal coverage")
                require(labels == (["D1", "D2", "D3", "ALL"] if kind == "DISP"
                                   else ["F1", "F2", "F3", "ALL"]), "Wrong FRD nodal components")
            blocks.append(summary)
            active = None
    require(active is None, "Truncated FRD block")
    for state in states:
        identity = (state["step"], state["increment"])
        require({b["kind"] for b in blocks if b["identity"] == identity} >= {"DISP", "FORC"},
                "Missing accepted-state FRD nodal output")
    require(any(b["kind"] == "CONTACT" and abs(b["time"] - 1) < 1e-6 for b in blocks),
            "Missing compression-endpoint contact field evidence")
    return blocks


def norm(vector):
    return math.sqrt(sum(x*x for x in vector))


def sum_vector(values, nodes):
    return tuple(sum(values[n][d] for n in nodes) for d in range(3))


def audit_case(case, expected, execution):
    folder = HERE / "output" / case
    require(execution == read_json(folder / "execution.json"), "Execution record copies differ")
    require(execution["status"] == "completed" and execution["stop_reason"] is None,
            "Case did not finish normally")
    state = execution["container_state"]
    require(execution["docker_cli_exit_code"] == state["ExitCode"] == 0 and
            not state["Running"] and not state["OOMKilled"], "Bad terminal container state")
    require(execution["container_image"] == expected["solver"]["base_image_id"], "Wrong image")
    command = execution["command"]
    require(command[:2] == ["docker", "run"] and "--pull=never" in command and
            command[-4:] == [expected["solver"]["base_image_id"],
                             expected["solver"]["binary_path"], "-i", "coupon"],
            "Invoked image/binary/input command differs")
    actual_files = {p.name for p in folder.iterdir() if p.is_file() and p.name != "execution.json"}
    required = {"coupon." + suffix for suffix in ("inp", "dat", "cvg", "sta", "frd", "stdout", "stderr")}
    require(actual_files >= required, "Required native output missing")
    require(actual_files == set(execution["outputs_sha256"]), "Output file inventory differs")
    for name, digest in execution["outputs_sha256"].items():
        require(sha(folder / name) == digest, f"Output hash mismatch: {name}")
    require(sha(folder / "coupon.inp") == expected["cases"][case]["input_sha256"],
            "Executed deck differs")
    require(max((folder / "coupon.stdout").stat().st_size,
                (folder / "coupon.stderr").stat().st_size) <= 5*1024*1024,
            "Captured stream exceeded declared bound")
    nodes, parts, faces = mesh(folder / "coupon.inp")
    fields = dat(folder / "coupon.dat", set(nodes))
    states, iteration_audit = convergence(folder, case == "mortar_c3d10")
    require(len(fields) == 2 * len(states), "DAT/STA state count mismatch")
    report, consumed = [], set()
    tolerance = expected["analytical_known_answer"]["predeclared_tolerances"]
    u_limit = tolerance["accepted_state_u3_profile_interface_gap_and_face_warp_mm"]
    for state in states:
        selected = {}
        for quantity in ("displacements", "forces"):
            matches = [key for key in fields if key[1] == quantity and
                       abs(key[0] - state["total"]) < 2e-6]
            require(len(matches) == 1 and matches[0] not in consumed, "Unmatched/duplicate DAT state")
            consumed.add(matches[0])
            selected[quantity] = fields[matches[0]]
        u, rf = selected["displacements"], selected["forces"]
        q = -.005 * state["relative"]
        pressure = max(-q, 0) / 5e-5
        force = pressure * 4
        force_limit = tolerance["force_relative_error"] * force + tolerance["force_abs_error_N"]
        top, bottom = sum_vector(rf, faces["top"]), sum_vector(rf, faces["bottom"])
        require(abs(top[2] + force) <= force_limit and abs(bottom[2] - force) <= force_limit,
                f"Reaction disagrees with analytical force at {state['total']}")
        require(norm(tuple(a+b for a,b in zip(top,bottom))) <= force_limit,
                "Support force closure fails")
        require(norm(top[:2]) <= force_limit and norm(bottom[:2]) <= force_limit,
                "Tangential support reaction exceeds tolerance")
        if q >= 0:
            require(max(norm(top), norm(bottom)) <= tolerance["open_reopen_resultant_support_force_norm_N"],
                    "Open/reopened state carries support force")
        errors = []
        for n, xyz in nodes.items():
            predicted = (q + pressure*(2-xyz[2])/100000 if n in parts["UPPER"]
                         else -pressure*(xyz[2]+2)/100000)
            errors.append(abs(u[n][2]-predicted))
        require(max(errors) <= u_limit, f"Displacement profile fails at {state['total']}")
        means = {name: sum(u[n][2] for n in ids)/len(ids) for name,ids in faces.items()}
        warp = max(max(u[n][2] for n in ids)-min(u[n][2] for n in ids) for ids in faces.values())
        gap = means["upper_interface"] - means["lower_interface"]
        predicted_gap = q if q >= 0 else -pressure/100000
        require(abs(gap-predicted_gap) <= u_limit and warp <= u_limit, "Gap/face warp fails")
        lower_xy = {nodes[n][:2]: n for n in faces["lower_interface"]}
        gap_error = max(abs(u[n][2]-u[lower_xy[nodes[n][:2]]][2]-predicted_gap)
                        for n in faces["upper_interface"])
        require(gap_error <= u_limit, "Matched interface nodal gap fails")
        row = dict(state, imposed_top_u3_mm=q, analytic_force_N=force,
                   top_RF_N=top, bottom_RF_N=bottom, geometric_gap_mm=gap,
                   max_profile_error_mm=max(errors), face_warp_mm=warp,
                   max_tangential_displacement_diagnostic_mm=max(
                       abs(u[n][d]) for n in nodes for d in (0, 1)),
                   max_matched_gap_error_mm=gap_error,
                   interface_DAT_RF_diagnostic_N={name: sum_vector(rf, faces[name])
                       for name in ("upper_interface", "lower_interface")})
        if state["step"] == 1 and abs(state["relative"]-1) < 1e-6:
            compliance = 4*abs(means["top"])/abs(top[2])
            limit = tolerance["pressure_compliance_relative_error"]*5e-5 + tolerance["pressure_compliance_abs_error_mm3_per_N"]
            require(abs(compliance-5e-5) <= limit, "Endpoint pressure compliance fails")
            row["pressure_compliance_mm3_per_N"] = compliance
        report.append(row)
    require(consumed == set(fields), "Unconsumed DAT evidence")
    return {"status": "PASS", "accepted_states": len(states), "iterations": iteration_audit,
            "states": report, "FRD_field_diagnostics": frd_fields(folder / "coupon.frd", states, set(nodes))}


def audit():
    expected = read_json(HERE / "expected.json")
    freeze = read_json(HERE / "input-freeze.json")
    execution = read_json(HERE / "execution.json")
    require(execution["input_freeze_sha256"] == sha(HERE / "input-freeze.json"), "Freeze mismatch")
    for name, digest in freeze["files_sha256"].items():
        require(sha(HERE / name) == digest, f"Frozen artifact differs: {name}")
    for case, spec in expected["cases"].items():
        require(spec["input_sha256"] == freeze["files_sha256"][spec["input"]],
                "Expected/copy deck digest differs from frozen source")
    require(execution["image_id"] == freeze["image_id"] == expected["solver"]["base_image_id"],
            "Root/freeze image pin mismatch")
    require(execution["binary_sha256"] == expected["solver"]["binary_sha256"], "Binary mismatch")
    require(execution["status"] == "completed_pending_audit" and execution["frozen_inputs_unchanged"] is True,
            "Execution incomplete or inputs changed")
    runs = execution["runs"]
    require(len(runs) == 2 and {r["case"] for r in runs} == CASES, "Missing/duplicate case")
    results = {}
    for run in runs:
        try:
            results[run["case"]] = audit_case(run["case"], expected, run)
        except Exception as exc:
            results[run["case"]] = {"status": "FAIL", "error": str(exc)}
    if not all(r["status"] == "PASS" for r in results.values()):
        return {"status": "FAIL", "error": "One or more case audits failed", "cases": results,
                "mechanical_acceptance": False, "joint_acceptance": False, "release": False}
    peaks = [next(s for s in r["states"] if "pressure_compliance_mm3_per_N" in s)
             for r in results.values()]
    difference = abs(peaks[0]["top_RF_N"][2] - peaks[1]["top_RF_N"][2])
    require(difference <= .01*400, "Formulation endpoint force comparison fails")
    return {"status": "PASS_METHOD_FIXTURE", "cases": results,
            "formulation_endpoint_force_difference_N": difference,
            "mechanical_acceptance": False, "joint_acceptance": False, "release": False}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    try:
        result = audit()
    except Exception as exc:
        result = {"status": "FAIL", "error": str(exc), "mechanical_acceptance": False,
                  "joint_acceptance": False, "release": False}
    result["verifier_sha256"] = sha(Path(__file__))
    result["execution_sha256"] = sha(HERE / "execution.json") if (HERE / "execution.json").exists() else None
    if args.write:
        with (HERE / "verifier.json").open("x") as stream:
            json.dump(result, stream, indent=2, sort_keys=True)
            stream.write("\n")
    print(json.dumps({k: v for k,v in result.items() if k != "cases"}))
    raise SystemExit(0 if result["status"] == "PASS_METHOD_FIXTURE" else 1)
