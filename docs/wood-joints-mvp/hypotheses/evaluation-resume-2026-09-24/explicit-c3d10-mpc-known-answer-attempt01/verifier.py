#!/usr/bin/env python3
"""Audit the explicit C3D10 direct/mapped coordinate-invariance fixture."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import re


HERE = Path(__file__).resolve().parent
CASES = ("direct", "mapped")
TIME_TOL = 2e-7


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_json(path: Path) -> dict:
    def unique_pairs(items):
        result = {}
        for key, value in items:
            require(key not in result, f"Duplicate JSON key {key} in {path}")
            result[key] = value
        return result
    def bad_constant(value):
        raise ValueError(f"Non-finite JSON number {value} in {path}")
    return json.loads(path.read_text(), object_pairs_hook=unique_pairs,
                      parse_constant=bad_constant)


def number(token: str) -> float:
    value = float(token.replace("D", "E").replace("d", "e"))
    require(math.isfinite(value), f"Non-finite numeric output: {token}")
    return value


def json_safe(value):
    if isinstance(value, float):
        return value if math.isfinite(value) else None
    if isinstance(value, dict):
        return {str(key): json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [json_safe(item) for item in value]
    return value


def within(actual: float, reference: float, relative: float, absolute: float) -> bool:
    return math.isfinite(actual) and abs(actual - reference) <= absolute + relative * abs(reference)


def parse_dat(text: str) -> tuple[list[dict], list[dict], list[str]]:
    """Parse actual-time DAT nodal fields and one-value EL PRINT totals."""
    fields, energy, errors = [], [], []
    active_nodes = None
    active_energy = None
    nodal_re = re.compile(
        r"\b(displacements|velocities|forces)\s*\([^)]*\)\s*for set\s+(\w+)\s+and time\s+(\S+)", re.I)
    energy_re = re.compile(
        r"total\s+(internal energy|kinetic energy|mass|volume)\s+for set\s+(\w+)\s+and time\s+(\S+)", re.I)
    energy_name = {"internal energy": "ELSE", "kinetic energy": "ELKE",
                   "mass": "EMAS", "volume": "EVOL"}
    for line in text.splitlines():
        match = nodal_re.search(line)
        if match:
            word, set_name, time_text = match.groups()
            try:
                kind = {"displacements": "U", "velocities": "V", "forces": "RF"}[word.lower()]
                record = {"kind": kind, "set": set_name.upper(), "time": number(time_text), "nodes": {}}
                fields.append(record)
                active_nodes, active_energy = record["nodes"], None
            except Exception as exc:
                errors.append(f"bad DAT nodal header: {exc}")
                active_nodes = None
            continue
        match = energy_re.search(line)
        if match:
            name, set_name, time_text = match.groups()
            try:
                record = {"kind": energy_name[name.lower()], "set": set_name.upper(),
                          "time": number(time_text), "value": None}
                energy.append(record)
                active_energy, active_nodes = record, None
            except Exception as exc:
                errors.append(f"bad DAT energy header: {exc}")
                active_energy = None
            continue
        tokens = line.split()
        if active_nodes is not None and len(tokens) == 4 and tokens[0].isdigit():
            node = int(tokens[0])
            try:
                vector = [number(token) for token in tokens[1:]]
                if node in active_nodes:
                    errors.append(f"duplicate DAT node {node} in {active_nodes}")
                active_nodes[node] = vector
            except Exception as exc:
                errors.append(f"invalid DAT nodal row: {exc}")
        elif active_energy is not None and active_energy["value"] is None and tokens:
            try:
                values = [number(token) for token in tokens]
                if len(values) == 1:
                    active_energy["value"] = values[0]
            except Exception:
                pass
    for record in energy:
        if record["value"] is None:
            errors.append(f"missing scalar after DAT {record['kind']} header")
    keys = [(f["set"], f["kind"], f["time"]) for f in fields]
    if len(keys) != len(set(keys)):
        errors.append("duplicate DAT set/field/time header")
    keys = [(e["set"], e["kind"], e["time"]) for e in energy]
    if len(keys) != len(set(keys)):
        errors.append("duplicate DAT energy set/field/time header")
    return fields, energy, errors


def parse_frd(text: str) -> tuple[list[dict], list[str]]:
    """Parse FRD step/increment/time fields; ENER is reported diagnostically."""
    blocks, errors = [], []
    step_inc, time, active, labels = None, None, None, []
    for line in text.splitlines():
        words = line.split()
        if words and words[0] == "1PSTEP":
            try:
                # FRD: output counter, actual increment, step.
                step_inc = (int(words[3]), int(words[2])) if len(words) >= 4 else None
            except Exception:
                step_inc = None
                errors.append("malformed FRD 1PSTEP identity")
        elif words and words[0] == "100CL":
            try:
                time = number(words[2])
            except Exception as exc:
                time = None
                errors.append(f"malformed FRD time: {exc}")
        elif line.startswith(" -4"):
            if active is not None:
                errors.append(f"unterminated FRD {active['kind']} field")
            active = {"kind": words[1], "nodes": {}} if len(words) >= 2 else None
            labels = []
        elif active is not None and line.startswith(" -5"):
            if len(words) >= 2:
                labels.append(words[1])
        elif active is not None and line.startswith(" -1"):
            try:
                node = int(line[3:13])
                tail = line.rstrip()[13:]
                values = [number(tail[i:i + 12]) for i in range(0, len(tail), 12)
                          if tail[i:i + 12].strip()]
                require(node not in active["nodes"], f"duplicate FRD node {node}")
                active["nodes"][node] = values
            except Exception as exc:
                errors.append(f"invalid FRD {active['kind']} row: {exc}")
        elif active is not None and line.startswith(" -3"):
            kind = active["kind"]
            if step_inc is None or time is None:
                errors.append(f"untimed FRD {kind} field")
            if kind in ("DISP", "VELO", "FORC"):
                for node, values in active["nodes"].items():
                    if len(values) != 3:
                        errors.append(f"FRD {kind} node {node} has {len(values)} components")
            flat = [value for values in active["nodes"].values() for value in values]
            blocks.append({"kind": kind, "identity": step_inc, "time": time,
                           "nodes": active["nodes"], "labels": labels[:],
                           "value_count": len(flat),
                           "max_abs": max((abs(v) for v in flat), default=None)})
            active = None
    if active is not None:
        errors.append("truncated FRD field")
    keys = [(b["kind"], b["identity"]) for b in blocks]
    if len(keys) != len(set(keys)):
        duplicates = {key for key in keys if keys.count(key) > 1}
        errors.extend(f"duplicate FRD {kind} field at {identity}"
                      for kind, identity in sorted(duplicates, key=repr))
    return blocks, errors


def at_time(records: list[dict], time: float, time_key="time") -> dict | None:
    found = [record for record in records if record.get(time_key) is not None
             and abs(record[time_key] - time) <= TIME_TOL]
    return found[0] if len(found) == 1 else None


def deck_audit(case: str, path: Path, expected: dict, preflight: dict) -> dict:
    text = path.read_text()
    upper = text.upper()
    errors = []
    lines = [line.strip() for line in upper.splitlines()]
    dynamic = [i for i, line in enumerate(lines) if line.startswith("*DYNAMIC")]
    if len(dynamic) != 1 or lines[dynamic[0]] != "*DYNAMIC,EXPLICIT=2,ALPHA=0":
        errors.append("expected one *DYNAMIC,EXPLICIT=2,ALPHA=0 card")
    else:
        values = lines[dynamic[0] + 1].split(",") if dynamic[0] + 1 < len(lines) else []
        wanted = [preflight["time_control"]["initial_time_increment_s"],
                  preflight["time_control"]["step_period_s"], None,
                  preflight["time_control"]["maximum_time_increment_s"]]
        try:
            actual = [number(v) if v.strip() else None for v in values]
            if len(actual) != 4 or actual[:2] != wanted[:2] or actual[2:] != wanted[2:]:
                errors.append("explicit dt/minimum/period/maximum data row differs")
        except Exception as exc:
            errors.append(f"invalid explicit time-control data: {exc}")
    if any(line.startswith("*MASS SCALING") for line in lines):
        errors.append("deck requests mass scaling")
    if any(line.startswith("*DAMPING") for line in lines):
        errors.append("deck requests damping/stiffness scaling")
    if any("DIRECT" in line.split(",") for line in lines if line.startswith("*DYNAMIC")):
        errors.append("deck requests DIRECT explicit update")
    if case == "mapped":
        nonempty = [re.sub(r"\s+", "", line) for line in lines if line and not line.startswith("**")]
        try:
            pos = nonempty.index("*EQUATION")
            equation = nonempty[pos + 1:pos + 4]
        except (ValueError, IndexError):
            equation = []
        if equation != ["5", "1,1,1,2,1,1,3,1,1,4,1,1", "11,1,-4"]:
            errors.append("mapped physical/controller equation differs")
    elif "*EQUATION" in upper:
        errors.append("direct case unexpectedly contains an equation")
    return {"pass": not errors, "errors": errors,
            "dynamic_card_count": len(dynamic), "mass_scaling_card": "*MASS SCALING" in upper}


def observed_scaling_or_errors(folder: Path) -> dict:
    markers = ("Selective Mass Scaling is active",
               "Selective Spring Scaling is active",
               "Reduction of spring stiffness by (maximum) =",
               "WarnElementMassScaled")
    hits, native_errors = [], []
    for path in folder.iterdir() if folder.is_dir() else []:
        if not path.is_file():
            continue
        if "WarnElementMassScaled" in path.name:
            hits.append(path.name)
        if path.suffix.lower() not in (".stdout", ".stderr", ".dat", ".frd", ".log"):
            continue
        text = path.read_text(errors="replace")
        for marker in markers:
            if marker.lower() in text.lower():
                hits.append(f"{path.name}: {marker}")
        for line in text.splitlines():
            if re.search(r"(?i)(^\s*\*ERROR\b|FATAL ERROR|ERROR IN \w+)", line):
                native_errors.append(f"{path.name}: {line.strip()[:240]}")
    return {"mass_or_spring_scaling_signals": hits,
            "native_error_lines": native_errors,
            "pass": not hits and not native_errors}


def compare_value(actual: float, reference: float, relative: float, absolute: float) -> dict:
    error = abs(actual - reference)
    limit = absolute + relative * abs(reference)
    return {"actual": actual, "reference": reference, "absolute_error": error,
            "allowed_error": limit, "pass": error <= limit}


def summarize_checks(checks: dict[str, list[dict]]) -> tuple[dict, dict]:
    metrics, gates = {}, {}
    for name, items in checks.items():
        if not items:
            metrics[name] = None
            gates[name] = False
        else:
            metrics[name] = {"max_absolute_error": max(item["absolute_error"] for item in items),
                             "max_allowed_error": max(item["allowed_error"] for item in items),
                             "samples": len(items)}
            gates[name] = all(item["pass"] for item in items)
    return metrics, gates


def compare_histories(direct_states: list[dict], mapped_states: list[dict],
                      relative: float, absolute: float) -> dict:
    comparisons = []
    for direct in direct_states:
        mapped = at_time(mapped_states, direct["time_s"], "time_s")
        if mapped is None:
            continue
        for field, expected in (("physical_U_mm", (0.5 * direct["time_s"] ** 2, 0.0, 0.0)),
                                ("physical_V_mm_per_s", (direct["time_s"], 0.0, 0.0))):
            for node, values in direct[field].items():
                other = mapped[field].get(node)
                if other is None or len(values) != 3 or len(other) != 3:
                    continue
                for index in range(3):
                    difference = abs(other[index] - values[index])
                    limit = absolute + relative * abs(expected[index])
                    comparisons.append({"time_s": direct["time_s"], "field": field,
                                        "node": int(node), "component": index + 1,
                                        "absolute_difference": difference,
                                        "allowed_difference": limit,
                                        "pass": difference <= limit})
    return {"pass": bool(comparisons) and all(item["pass"] for item in comparisons),
            "matched_component_count": len(comparisons),
            "max_absolute_difference": max((item["absolute_difference"] for item in comparisons), default=None),
            "max_allowed_difference": max((item["allowed_difference"] for item in comparisons), default=None)}


def evaluate_case(case: str, expected: dict, preflight: dict, run: dict) -> dict:
    folder = HERE / "output" / case
    errors = []
    hashes = run.get("outputs_sha256", {})
    hash_errors = []
    for name, digest in hashes.items():
        path = folder / name
        if not path.is_file() or sha(path) != digest:
            hash_errors.append(f"missing/hash mismatch: {name}")
    actual_names = {p.name for p in folder.iterdir() if p.is_file() and p.name != "execution.json"} if folder.is_dir() else set()
    if actual_names != set(hashes):
        hash_errors.append("output inventory differs from run record")
    errors.extend(hash_errors)
    scaling = observed_scaling_or_errors(folder)
    errors.extend(scaling["mass_or_spring_scaling_signals"])
    errors.extend(scaling["native_error_lines"])
    run_state = run.get("container_state", {})
    runtime_ok = (run.get("status") == "completed" and run.get("docker_cli_exit_code") == 0
                  and run_state.get("ExitCode") == 0 and run_state.get("OOMKilled") is False
                  and run_state.get("Running") is False)
    if not runtime_ok:
        errors.append("native run did not complete cleanly")

    frd_path, dat_path = folder / "coupon.frd", folder / "coupon.dat"
    frd, frd_errors = parse_frd(frd_path.read_text(errors="replace")) if frd_path.is_file() else ([], ["coupon.frd missing"])
    fields, energies, dat_errors = parse_dat(dat_path.read_text(errors="replace")) if dat_path.is_file() else ([], [], ["coupon.dat missing"])
    ener_errors = [error for error in frd_errors if "FRD ENER" in error]
    errors.extend(error for error in frd_errors if "FRD ENER" not in error)
    errors.extend(dat_errors)
    node_ids = set(expected["cases"][case]["physical_node_ids"])
    control_ids = set(expected["cases"][case]["controller_node_ids"])
    rel, absolute = expected["known_answer"]["tolerance_relative"], expected["known_answer"]["tolerance_absolute"]
    loads = expected["source_lumped_mass"]["CLOAD_N_each_serialized"]
    disp_blocks = [b for b in frd if b["kind"] == "DISP"]
    states = sorted([{**b, "step": b["identity"][0], "increment": b["identity"][1]}
                     for b in disp_blocks if b["identity"] and b["time"] is not None],
                    key=lambda s: (s["step"], s["increment"]))
    trace_errors = []
    if not states:
        trace_errors.append("FRD has no timed DISP state blocks")
    max_dt = preflight["time_control"]["maximum_time_increment_s"]
    for idx, state in enumerate(states):
        if state["step"] != 1 or (idx == 0 and state["increment"] != 1):
            trace_errors.append("FRD step/increment sequence has unexpected start")
        if idx and (state["increment"] != states[idx - 1]["increment"] + 1
                    or state["time"] <= states[idx - 1]["time"]):
            trace_errors.append("FRD output increments are not contiguous/increasing")
        if idx == 0 and not 0 < state["time"] <= max_dt + TIME_TOL:
            trace_errors.append("first emitted FRD state is outside the initial increment bound")
        if idx and state["time"] - states[idx - 1]["time"] > max_dt + TIME_TOL:
            trace_errors.append("emitted FRD time gap exceeds the configured maximum increment")
    final_time = preflight["time_control"]["step_period_s"]
    if states and abs(states[-1]["time"] - final_time) > TIME_TOL:
        trace_errors.append("FRD output does not include the prescribed terminal time")
    errors.extend(trace_errors)

    coverage_errors = []
    state_by_id = {b["identity"]: b for b in states}
    state_ids = set(state_by_id)
    for kind in ("DISP", "VELO", "FORC", "ENER"):
        selected = [b for b in frd if b["kind"] == kind]
        if kind == "ENER":
            continue  # Separate diagnostic contract below.
        if {b["identity"] for b in selected if b["identity"]} != state_ids or len(selected) != len(states):
            coverage_errors.append(f"FRD {kind} field/time inventory differs from DISP frames")
        for block in selected:
            reference = state_by_id.get(block["identity"])
            if reference is None or block["time"] is None or abs(block["time"] - reference["time"]) > TIME_TOL:
                coverage_errors.append(f"FRD {kind} time does not match its DISP frame")

    expected_times = [state["time"] for state in states]
    dat_contract = [("U", "PHYSICAL"), ("V", "PHYSICAL"), ("RF", "PHYSICAL")]
    if case == "mapped":
        dat_contract.append(("U", "CONTROLLER"))
    for kind, set_name in dat_contract:
        selected = [f for f in fields if f["kind"] == kind and f["set"] == set_name]
        if len(selected) != len(states) or any(not any(abs(f["time"] - t) <= TIME_TOL for t in expected_times)
                                               for f in selected):
            coverage_errors.append(f"DAT {set_name} {kind} field/time inventory differs from FRD frames")
    for kind in ("ELSE", "ELKE", "EMAS", "EVOL"):
        selected = [e for e in energies if e["kind"] == kind and e["set"] == "BODY"]
        if len(selected) != len(states) or any(not any(abs(e["time"] - t) <= TIME_TOL for t in expected_times)
                                               for e in selected):
            coverage_errors.append(f"DAT BODY {kind} energy/time inventory differs from FRD frames")

    ener_checks = []
    ener_blocks = [block for block in frd if block["kind"] == "ENER"]
    if len(ener_blocks) != len(states):
        ener_errors.append("FRD ENER field/time inventory differs from DISP frames")
    for state in states:
        matches = [block for block in ener_blocks if block["identity"] == state["identity"]]
        if len(matches) != 1:
            ener_errors.append(f"FRD ENER missing/duplicate at {state['identity']}")
            continue
        block = matches[0]
        if block["time"] is None or abs(block["time"] - state["time"]) > TIME_TOL:
            ener_errors.append(f"FRD ENER time differs from DISP frame at {state['identity']}")
        if set(block["nodes"]) != node_ids:
            ener_errors.append(f"FRD ENER node coverage differs at {state['identity']}")
        if "ENER" not in block["labels"]:
            ener_errors.append(f"FRD ENER component label missing at {state['identity']}")
        for node, values in block["nodes"].items():
            if len(values) != 1:
                ener_errors.append(f"FRD ENER node {node} does not have one scalar")
            else:
                ener_checks.append(compare_value(values[0], 0.0, rel, absolute))
    ener_ok = bool(ener_checks) and all(item["pass"] for item in ener_checks) and not ener_errors

    checks = {name: [] for name in ("physical_U", "physical_V", "controller_U",
             "mapped_equation", "external_work", "ELSE", "ELKE", "EMAS", "EVOL")}
    state_rows = []
    for state in states:
        t, identity = state["time"], state["identity"]
        frd_fields = {kind: [b for b in frd if b["kind"] == kind and b["identity"] == identity]
                      for kind in ("DISP", "VELO", "FORC", "ENER")}
        frd_for = {kind: values[0] if len(values) == 1 else None for kind, values in frd_fields.items()}
        if len(frd_fields["VELO"]) != 1 or len(frd_fields["FORC"]) != 1:
            coverage_errors.append(f"FRD VELO/FORC missing or duplicate at {identity}")
        for kind in ("DISP", "VELO", "FORC"):
            block = frd_for[kind]
            if not block or set(block["nodes"]) != node_ids:
                coverage_errors.append(f"FRD {kind} physical coverage missing at {identity}")
        dat_fields = {}
        for kind in ("U", "V", "RF"):
            matches = [f for f in fields if f["kind"] == kind and f["set"] == "PHYSICAL"
                       and abs(f["time"] - t) <= TIME_TOL]
            if len(matches) != 1 or set(matches[0]["nodes"]) != node_ids:
                coverage_errors.append(f"DAT {kind} physical coverage missing/duplicate at {identity}")
            else:
                dat_fields[kind] = matches[0]["nodes"]
        ctrl = None
        if case == "mapped":
            matches = [f for f in fields if f["kind"] == "U" and f["set"] == "CONTROLLER"
                       and abs(f["time"] - t) <= TIME_TOL]
            if len(matches) != 1 or set(matches[0]["nodes"]) != control_ids:
                coverage_errors.append(f"DAT controller U coverage missing/duplicate at {identity}")
            else:
                ctrl = matches[0]["nodes"]

        u = dat_fields.get("U", {})
        v = dat_fields.get("V", {})
        state_row = {"step": state["step"], "increment": state["increment"], "time_s": t,
                     "physical_U_mm": {str(n): u[n] for n in sorted(u)},
                     "physical_V_mm_per_s": {str(n): v[n] for n in sorted(v)},
                     "controller_U_mm": {str(n): vec for n, vec in sorted(ctrl.items())} if ctrl else None,
                     "energies": {}, "external_work_Nmm": None, "mpc_residual_mm": None}
        state_rows.append(state_row)
        for node in sorted(node_ids & set(u)):
            for d, reference in enumerate((0.5 * t * t, 0.0, 0.0)):
                checks["physical_U"].append(compare_value(u[node][d], reference, rel, absolute))
        for node in sorted(node_ids & set(v)):
            for d, reference in enumerate((t, 0.0, 0.0)):
                checks["physical_V"].append(compare_value(v[node][d], reference, rel, absolute))
        if case == "mapped" and ctrl and 11 in ctrl and len(u) == 10:
            checks["controller_U"].append(compare_value(ctrl[11][0], 0.5 * t * t, rel, absolute))
            residual = u[1][0] + u[2][0] + u[3][0] + u[4][0] - 4 * ctrl[11][0]
            state_row["mpc_residual_mm"] = residual
            checks["mapped_equation"].append(compare_value(residual, 0.0, 0.0, absolute))

        if set(u) == node_ids:
            work = sum(loads[i] * u[node][0] for i, node in enumerate(sorted(node_ids)))
            state_row["external_work_Nmm"] = work
            checks["external_work"].append(compare_value(work, 0.5 * t * t, rel, absolute))
        for label, reference in (("ELSE", 0.0), ("ELKE", 0.5 * t * t),
                                 ("EMAS", 1.0), ("EVOL", expected["known_answer"]["body_EVOL_mm3"])):
            found = [e for e in energies if e["set"] == "BODY" and e["kind"] == label
                     and abs(e["time"] - t) <= TIME_TOL]
            if len(found) != 1 or found[0]["value"] is None:
                coverage_errors.append(f"DAT BODY {label} energy missing/duplicate at {identity}")
            else:
                actual = found[0]["value"]
                state_row["energies"][label] = actual
                checks[label].append(compare_value(actual, reference, rel, absolute))

    # Compare FRD nodal fields with DAT at the same emitted time and identity.
    parity_errors = {"U": [], "V": [], "RF": []}
    for state in states:
        t, identity = state["time"], state["identity"]
        for kind, frd_kind in (("U", "DISP"), ("V", "VELO"), ("RF", "FORC")):
            dat = [f for f in fields if f["kind"] == kind and f["set"] == "PHYSICAL"
                   and abs(f["time"] - t) <= TIME_TOL]
            fr = [b for b in frd if b["kind"] == frd_kind and b["identity"] == identity]
            if len(dat) == 1 and len(fr) == 1 and set(dat[0]["nodes"]) == set(fr[0]["nodes"]) == node_ids:
                parity_errors[kind].extend(compare_value(fr[0]["nodes"][n][d], dat[0]["nodes"][n][d], rel, absolute)
                                           for n in node_ids for d in range(3))
    parity_gates = {kind: bool(values) and all(v["pass"] for v in values)
                    for kind, values in parity_errors.items()}
    parity_max = {kind: max((item["absolute_error"] for item in values), default=None)
                  for kind, values in parity_errors.items()}
    gate_metrics, gate_results = {}, {}
    for name, items in checks.items():
        gate_metrics[name] = {"sample_count": len(items),
                              "max_absolute_error": max((i["absolute_error"] for i in items), default=None),
                              "max_allowed_error": max((i["allowed_error"] for i in items), default=None)}
        gate_results[name] = bool(items) and all(i["pass"] for i in items)
    if case == "direct":
        gate_results["controller_U"] = gate_results["mapped_equation"] = True
    # RF is required finite and complete but is deliberately not an inertia or
    # reaction-magnitude oracle. Report transverse SPC sums as diagnostics.
    rf_transverse = []
    for f in fields:
        if f["kind"] == "RF" and f["set"] == "PHYSICAL" and set(f["nodes"]) == node_ids:
            rf_transverse.append([sum(f["nodes"][n][d] for n in node_ids) for d in (1, 2)])
    for kind, result in parity_gates.items():
        if not result:
            coverage_errors.append(f"DAT/FRD {kind} parity outside frozen precision gate")
    errors.extend(coverage_errors)
    deck = deck_audit(case, HERE / expected["inputs"][case], expected, preflight)
    errors.extend(deck["errors"])
    diagnostic_ener = [{"identity": b["identity"], "time": b["time"],
                        "nodes": sorted(b["nodes"]), "labels": b["labels"],
                        "value_count": b["value_count"], "max_abs": b["max_abs"]}
                       for b in frd if b["kind"] == "ENER"]
    ener_diagnostic = {"status": "PASS" if ener_ok else "FAIL",
                       "errors": ener_errors,
                       "blocks": diagnostic_ener,
                       "expected_node_count": len(node_ids),
                       "max_absolute_value": max((item["absolute_error"] for item in ener_checks), default=None),
                       "interpretation": "Nodal energy-density diagnostic only; not the ELKE kinetic-energy oracle."}
    if not states:
        errors.append("no accepted state outputs to assess")
    gates_pass = all(gate_results.values()) and all(parity_gates.values())
    aggregate_errors = errors + ener_errors
    mechanics_pass = (not hash_errors and runtime_ok and scaling["pass"]
                      and not trace_errors and not coverage_errors and deck["pass"]
                      and gates_pass and not errors)
    result_pass = mechanics_pass and ener_ok and not aggregate_errors
    return {"status": "PASS" if result_pass else "FAIL",
            "mechanics_known_answer_pass": mechanics_pass,
            "errors": aggregate_errors,
            "runtime_ok": runtime_ok, "output_hashes_ok": not hash_errors,
            "scaling_and_native_error_audit": scaling,
            "trace": {"pass": not trace_errors, "errors": trace_errors,
                      "accepted_state_count": len(states),
                      "first_identity_time": ({"step": states[0]["step"], "increment": states[0]["increment"], "time_s": states[0]["time"]} if states else None),
                      "final_identity_time": ({"step": states[-1]["step"], "increment": states[-1]["increment"], "time_s": states[-1]["time"]} if states else None),
                      "STA_rows_diagnostic_only": (sum(1 for x in (folder / "coupon.sta").read_text(errors="replace").splitlines() if x.split() and x.split()[0].isdigit()) if (folder / "coupon.sta").is_file() else None),
                      "CVG_rows_diagnostic_only": (sum(1 for x in (folder / "coupon.cvg").read_text(errors="replace").splitlines() if x.split() and x.split()[0].isdigit()) if (folder / "coupon.cvg").is_file() else None)},
            "deck_contract": deck, "gate_results": gate_results, "gate_metrics": gate_metrics,
            "DAT_FRD_parity": {"pass": all(parity_gates.values()), "per_field_pass": parity_gates,
                               "max_absolute_difference": parity_max},
            "states": state_rows, "first_state": state_rows[0] if state_rows else None,
            "final_state": state_rows[-1] if state_rows else None,
            "transverse_SPC_RF_resultants_N_diagnostic": rf_transverse,
            "FRD_ENER_diagnostic": ener_diagnostic,
            "coverage_errors": coverage_errors}


def audit() -> dict:
    expected = read_json(HERE / "expected.json")
    preflight = read_json(HERE / "preflight.json")
    freeze = read_json(HERE / "input-freeze.json")
    execution = read_json(HERE / "execution.json")
    require(expected.get("schema") == "calculix_explicit_c3d10_mpc_known_answer/v1",
            "Unexpected expected.json schema")
    require(preflight.get("schema") == "calculix_explicit_c3d10_mpc_preflight/v1",
            "Unexpected preflight.json schema")
    require(freeze.get("schema") == "explicit_c3d10_mpc_freeze/v1",
            "Unexpected freeze schema")
    require(execution.get("schema") == "explicit_c3d10_mpc_execution/v1",
            "Unexpected execution schema")
    frozen = freeze["files_sha256"]
    input_errors = [name for name, digest in frozen.items()
                    if not (HERE / name).is_file() or sha(HERE / name) != digest]
    require(not input_errors, f"Frozen input hashes differ: {input_errors}")
    require(execution.get("input_freeze_sha256") == sha(HERE / "input-freeze.json"),
            "Execution freeze SHA differs")
    require(execution.get("image_id") == freeze["image_id"] == expected["solver"]["image_id"],
            "Image pin differs")
    require(execution.get("binary_sha256") == freeze["binary_sha256"] == expected["solver"]["binary_sha256"],
            "Binary pin differs")
    require(expected["case_order"] == list(CASES), "Case order differs")
    for case in CASES:
        path = expected["inputs"][case]
        require(frozen.get(path) == expected["deck_sha256"][case], f"Deck pin differs: {case}")
    runs = {record.get("case"): record for record in execution.get("runs", [])}
    case_results = {}
    for case in CASES:
        if case not in runs:
            case_results[case] = {"status": "FAIL", "errors": ["case has no run record"],
                                  "states": [], "first_state": None, "final_state": None}
            continue
        try:
            case_results[case] = evaluate_case(case, expected, preflight, runs[case])
        except Exception as exc:
            case_results[case] = {"status": "FAIL", "errors": [str(exc)],
                                  "states": [], "first_state": None, "final_state": None}
    direct_states, mapped_states = (case_results["direct"].get("states", []),
                                    case_results["mapped"].get("states", []))
    relative, absolute = (expected["known_answer"]["tolerance_relative"],
                          expected["known_answer"]["tolerance_absolute"])
    history = compare_histories(direct_states, mapped_states, relative, absolute)
    passed = (all(case_results[c].get("status") == "PASS" for c in CASES)
              and history["pass"])
    return {"schema": "calculix_explicit_c3d10_mpc_verifier/v1",
            "status": "PASS_EXPLICIT_C3D10_MPC_KNOWN_ANSWER" if passed else "FAIL",
            "input_freeze_sha256": sha(HERE / "input-freeze.json"),
            "execution_sha256": sha(HERE / "execution.json"),
            "verifier_sha256": sha(Path(__file__)), "execution_status": execution.get("status"),
            "frozen_inputs_unchanged": execution.get("frozen_inputs_unchanged"),
            "cases": case_results, "direct_mapped_history_comparison": history,
            "mechanical_acceptance": False, "work_energy_acceptance": False,
            "joint_acceptance": False, "release": False}


def self_test() -> dict:
    dat = ("displacements (vx,vy,vz) for set PHYSICAL and time 1.0\n"
           "1 0.5 0 0\n\nvelocities (vx,vy,vz) for set PHYSICAL and time 1.0\n"
           "1 1 0 0\n\nforces (fx,fy,fz) for set PHYSICAL and time 1.0\n1 0 0 0\n"
           "\n total internal energy for set BODY and time 1.0\n\n0\n")
    fields, energy, errors = parse_dat(dat)
    require(not errors and len(fields) == 3 and energy[0]["value"] == 0.0,
            "Synthetic DAT positive case failed")
    frd_row = lambda node, vals: " -1" + f"{node:10d}" + "".join(f"{v:12.5E}" for v in vals)
    frd = ("    1PSTEP           1           1           1\n"
           " 100CL  101 1.00000E+00 10 0 1 1 1\n"
           " -4 DISP 4 1\n -5 D1\n -5 D2\n -5 D3\n"
           + frd_row(1, [0.5, 0, 0]) + "\n -3\n")
    blocks, frd_errors = parse_frd(frd)
    require(not frd_errors and len(blocks) == 1 and blocks[0]["identity"] == (1, 1),
            "Synthetic FRD positive case failed")
    rejected = False
    try:
        number("nan")
    except ValueError:
        rejected = True
    require(rejected, "Synthetic non-finite negative case failed")
    require(json.dumps(json_safe({"value": float("nan")}), allow_nan=False) == '{"value": null}',
            "JSON-safe preflight failed")
    correct = [{"time_s": 1.0, "physical_U_mm": {"1": [0.5, 0.0, 0.0]},
                "physical_V_mm_per_s": {"1": [1.0, 0.0, 0.0]}}]
    require(compare_histories(correct, correct, 1e-4, 1e-9)["pass"],
            "Synthetic history positive comparison failed")
    wrong = json.loads(json.dumps(correct))
    wrong[0]["physical_U_mm"]["1"][0] = 0.6
    require(not compare_histories(correct, wrong, 1e-4, 1e-9)["pass"],
            "Synthetic history negative comparison failed")
    return {"status": "PASS_SYNTHETIC_EXPLICIT_OUTPUT_PREFLIGHT",
            "DAT_positive": True, "FRD_positive": True, "history_positive_negative": True,
            "nonfinite_negative": True, "JSON_safe": True,
            "native_execution": False}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true",
                        help="Run synthetic parser tests only; never invokes CalculiX")
    parser.add_argument("--write", action="store_true",
                        help="Write verifier.json once after auditing existing outputs")
    args = parser.parse_args()
    try:
        result = self_test() if args.self_test else audit()
    except Exception as exc:
        result = {"schema": "calculix_explicit_c3d10_mpc_verifier/v1",
                  "status": "FAIL", "error": str(exc), "mechanical_acceptance": False,
                  "work_energy_acceptance": False, "joint_acceptance": False,
                  "release": False}
    result = json_safe(result)
    if args.write:
        with (HERE / "verifier.json").open("x") as stream:
            json.dump(result, stream, indent=2, sort_keys=True, allow_nan=False)
            stream.write("\n")
    print(json.dumps(result, sort_keys=True, allow_nan=False))
    raise SystemExit(0 if result.get("status") in (
        "PASS_SYNTHETIC_EXPLICIT_OUTPUT_PREFLIGHT",
        "PASS_EXPLICIT_C3D10_MPC_KNOWN_ANSWER") else 1)
