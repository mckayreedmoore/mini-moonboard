#!/usr/bin/env python3
"""Offline verifier for the implicit dynamic contact-point coupon capture."""

from __future__ import annotations

import argparse
from collections import defaultdict
import hashlib
import json
import math
from pathlib import Path
import re
import sys
import tarfile


HERE = Path(__file__).resolve().parent
FIXTURE = HERE.parent
EXPECTED_PATH = FIXTURE / "expected.json"
FLOAT_RE = re.compile(r"[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[EeDd][+-]?\d+)?\Z")
INT_RE = re.compile(r"[+-]?\d+\Z")
CELS_RE = re.compile(r"total contact spring energy for time\s+(\S+)", re.I)
CONV_FIELDS = {
    "event", "step", "increment", "attempt", "iteration",
    "mechanical_applicable", "iteration_ok", "mechanical_residual_ok",
    "displacement_ok", "visco_ok", "contact_change_gate_clear",
    "no_contact_now", "no_contact_at_start", "contact_present",
    "mechanical_gate_ok", "no_contact_energy_eligible",
    "contact_energy_eligible", "iconvergence", "idivergence",
    "final_convergence_ok",
}
CONTACT_FIELDS = {
    "event", "step", "increment", "attempt", "iteration", "contact_old",
    "contact_new", "delcon", "contact_change_flag",
}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def sha_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha_file(path: Path) -> str:
    require(path.is_file(), f"Missing pinned file: {path}")
    return sha_bytes(path.read_bytes())


def finite_float(token: str, where: str) -> float:
    require(FLOAT_RE.fullmatch(token) is not None,
            f"Malformed floating-point value at {where}: {token}")
    value = float(token.replace("D", "E").replace("d", "e"))
    require(math.isfinite(value), f"Nonfinite floating-point value at {where}")
    return value


def strict_json_bytes(data: bytes, where: str) -> dict:
    def unique_pairs(pairs):
        out = {}
        for key, value in pairs:
            require(key not in out, f"Duplicate JSON key {key} in {where}")
            out[key] = value
        return out

    def reject_constant(token):
        raise ValueError(f"Invalid JSON constant {token} in {where}")

    def parse_float(token):
        value = float(token)
        require(math.isfinite(value), f"Nonfinite JSON number in {where}")
        return value

    try:
        value = json.loads(data.decode("utf-8"), object_pairs_hook=unique_pairs,
                           parse_float=parse_float, parse_constant=reject_constant)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"Invalid JSON in {where}: {exc}") from exc
    require(isinstance(value, dict), f"JSON object required in {where}")
    return value


def load_json(path: Path) -> dict:
    return strict_json_bytes(path.read_bytes(), str(path))


def repo_root() -> Path:
    for candidate in HERE.parents:
        if (candidate / "AGENTS.md").is_file():
            return candidate
    raise ValueError("Could not locate repository AGENTS.md")


def verify_prepared_contract() -> tuple[dict, dict]:
    expected = load_json(EXPECTED_PATH)
    require(expected.get("schema") == "implicit_contact_point_trace_known_answer/v1",
            "Unexpected parent expected.json schema")
    source = expected["source_pins"]
    support = expected["supporting_artifacts"]
    trace_path = FIXTURE / support["trace_format_path"]
    patch_path = FIXTURE / support["diagnostic_patch_path"]
    audit_path = FIXTURE / support["geometry_dof_audit_path"]
    require(sha_file(trace_path) == support["trace_format_sha256"],
            "Trace format does not match its expected SHA-256")
    require(sha_file(patch_path) == support["diagnostic_patch_sha256"],
            "Diagnostic patch does not match its expected SHA-256")
    require(sha_file(audit_path) == support["geometry_dof_audit_sha256"],
            "Parent geometry audit does not match its expected SHA-256")
    input_path = FIXTURE / expected["input"]["path"]
    require(sha_file(input_path) == expected["input"]["sha256"],
            "Dynamic fixture input does not match expected SHA-256")
    geometry_path = FIXTURE / expected["input"]["geometry_source_path"]
    require(sha_file(geometry_path) == expected["input"]["geometry_source_sha256"],
            "Reused geometry source does not match expected SHA-256")

    audit = load_json(audit_path)
    require(audit.get("schema") == "contact_trace_fixture_parent_geometry_dof_audit/v1" and
            audit.get("status") == support["geometry_dof_audit_scope"] and
            audit.get("input_sha256") == expected["input"]["sha256"] and
            audit.get("node_count") == 58 and audit.get("element_count") == 13 and
            audit.get("free_dofs") == [[8004, 3]] and
            audit.get("disconnected_component_node_counts") == [4, 27, 27] and
            audit.get("all_C3D10_midnodes_are_exact_edge_midpoints") is True,
            "Parent geometry-only audit facts changed")

    archive_path = FIXTURE / source["archive_path"]
    require(sha_file(archive_path) == source["archive_sha256"],
            "Pinned CalculiX source archive hash differs")
    member_hashes = source["members"]
    with tarfile.open(archive_path, "r:bz2") as archive:
        members = {}
        for item in archive.getmembers():
            name = item.name[2:] if item.name.startswith("./") else item.name
            if item.isfile():
                require(name not in members, f"Duplicate archive member {name}")
                members[name] = item
        for name, digest in member_hashes.items():
            require(name in members, f"Pinned source member missing: {name}")
            stream = archive.extractfile(members[name])
            require(stream is not None and sha_bytes(stream.read()) == digest,
                    f"Pinned source member hash differs: {name}")

    manual_path = repo_root() / source["manual_path"]
    require(sha_file(manual_path) == source["manual_sha256"],
            "Pinned CalculiX 2.23 manual hash differs")
    trace_format = load_json(trace_path)
    require(trace_format.get("schema") == "ccx223_contact_point_trace_format/v1",
            "Unexpected trace-format schema")
    tags = trace_format.get("tags")
    require(isinstance(tags, dict) and set(tags) == {
        "CCXPT_MAP", "CCXPT_UNMAPPED", "CCXPT_TRIAL"},
        "Trace tag inventory changed")
    wanted = {"CCXPT_MAP": (13, 12), "CCXPT_UNMAPPED": (10, 0),
              "CCXPT_TRIAL": (11, 13)}
    for tag, (ni, nr) in wanted.items():
        require(len(tags[tag].get("integer_fields", [])) == ni and
                len(tags[tag].get("real_fields", [])) == nr,
                f"Trace field cardinality changed for {tag}")
        all_fields = tags[tag]["integer_fields"] + tags[tag]["real_fields"]
        require(len(set(all_fields)) == len(all_fields),
                f"Duplicate trace field name for {tag}")
    return expected, trace_format


def parse_trace(stdout: bytes, trace_format: dict) -> dict[str, list[dict]]:
    tags = trace_format["tags"]
    parsed = {tag: [] for tag in tags}
    try:
        lines = stdout.decode("ascii").splitlines()
    except UnicodeDecodeError as exc:
        raise ValueError("solver.stdout is not strict ASCII") from exc
    for lineno, line in enumerate(lines, 1):
        if "CCXPT_" not in line:
            continue
        tokens = line.split()
        require(tokens and tokens[0] in tags,
                f"Malformed or unknown contact trace at stdout line {lineno}")
        tag = tokens[0]
        integers = tags[tag]["integer_fields"]
        reals = tags[tag]["real_fields"]
        require(len(tokens) == 1 + len(integers) + len(reals),
                f"Wrong field count for {tag} at stdout line {lineno}")
        row = {"tag": tag}
        offset = 1
        for name in integers:
            require(INT_RE.fullmatch(tokens[offset]) is not None,
                    f"Noninteger {name} in {tag} at stdout line {lineno}")
            row[name] = int(tokens[offset], 10)
            offset += 1
        for name in reals:
            row[name] = finite_float(tokens[offset], f"{tag}.{name} line {lineno}")
            offset += 1
        if tag == "CCXPT_MAP":
            row["generated"] = row["native_isol"] != 0
        parsed[tag].append(row)
    require(parsed["CCXPT_MAP"], "No CCXPT_MAP rows captured")
    return parsed


def parse_events(stdout: bytes) -> tuple[list[dict], list[dict]]:
    conversions, contacts = [], []
    try:
        lines = stdout.decode("ascii").splitlines()
    except UnicodeDecodeError as exc:
        raise ValueError("solver.stdout is not strict ASCII") from exc
    for lineno, line in enumerate(lines, 1):
        if "CCX223_ATTEMPT04_" not in line:
            continue
        record = strict_json_bytes(line.strip().encode("ascii"),
                                   f"stdout event line {lineno}")
        event = record.get("event")
        wanted = CONV_FIELDS if event == "CCX223_ATTEMPT04_CONVERGENCE" else (
            CONTACT_FIELDS if event == "CCX223_ATTEMPT04_CONTACT" else None)
        require(wanted is not None and set(record) == wanted,
                f"Unexpected inherited event schema at stdout line {lineno}")
        if event == "CCX223_ATTEMPT04_CONVERGENCE":
            conversions.append(record)
        else:
            contacts.append(record)
    require(conversions, "No inherited convergence events found")
    for event in conversions:
        for name in CONV_FIELDS - {"event", "step", "increment", "attempt", "iteration"}:
            value = event[name]
            require(type(value) is int and value in (0, 1),
                    f"Convergence flag {name} is not 0/1")
        require(all(type(event[name]) is int and event[name] >= 0
                    for name in ("step", "increment", "attempt", "iteration")),
                "Invalid convergence identity")
        require(event["step"] == 1 and event["attempt"] == 1 and
                1 <= event["increment"] <= 50 and event["iteration"] >= 1,
                "Unexpected step, increment or cutback attempt in convergence trace")
        require(event["final_convergence_ok"] == int(
            event["iconvergence"] == 1 and event["idivergence"] == 0),
            "Final convergence flag contradicts native convergence fields")
    for event in contacts:
        require(event["step"] == 1 and event["attempt"] == 1 and
                1 <= event["increment"] <= 50 and event["iteration"] >= 1 and
                event["contact_old"] >= 0 and event["contact_new"] >= 0 and
                type(event["contact_change_flag"]) is int and
                event["contact_change_flag"] in (0, 1) and
                math.isfinite(float(event["delcon"])),
                "Invalid inherited contact-count event")
    return conversions, contacts


def parse_sta(data: bytes, expected: dict) -> dict[tuple[int, int, int], dict]:
    try:
        lines = data.decode("ascii").splitlines()
    except UnicodeDecodeError as exc:
        raise ValueError("coupon.sta is not strict ASCII") from exc
    states = {}
    for lineno, line in enumerate(lines, 1):
        tokens = line.split()
        if not tokens or INT_RE.fullmatch(tokens[0]) is None:
            continue
        require(len(tokens) == 7,
                f"Malformed numeric STA row at line {lineno}; expected seven fields")
        require(all(INT_RE.fullmatch(token) is not None for token in tokens[:4]),
                f"Malformed STA identity at line {lineno}")
        step, inc, attempt, iterations = map(int, tokens[:4])
        values = [finite_float(token, f"STA line {lineno}") for token in tokens[4:]]
        total_time, step_time, increment_time = values
        key = (step, inc, attempt)
        require(key not in states, f"Duplicate accepted STA identity {key}")
        states[key] = {"step": step, "increment": inc, "attempt": attempt,
                       "iterations": iterations, "total_time": total_time,
                       "step_time": step_time, "increment_time": increment_time}
    schedule = expected["procedure"]["required_accepted_state_records"]
    require(len(states) == schedule["accepted_sta_rows"],
            "STA does not contain exactly 50 accepted increment records")
    dt = schedule["increment_time_s"]
    for inc in range(1, schedule["accepted_sta_rows"] + 1):
        key = (schedule["step"], inc, schedule["accepted_attempt"])
        require(key in states, f"STA missing accepted increment {key}")
        row = states[key]
        target_time = inc * dt
        tol = expected["accepted_endpoint_oracle"]["accepted_time_abs_tolerance_s"]
        require(abs(row["total_time"] - target_time) <= tol and
                abs(row["step_time"] - target_time) <= tol and
                abs(row["increment_time"] - dt) <= tol,
                f"STA time/increment differs at {key}")
        require(row["iterations"] >= 2,
                f"STA reports fewer than two iterations at {key}")
    require(all(key[0] == 1 and key[2] == 1 for key in states),
            "STA contains a different step or rejected/cutback attempt")
    return states


def parse_cvg(data: bytes) -> dict[tuple[int, int, int, int], int]:
    try:
        lines = data.decode("ascii").splitlines()
    except UnicodeDecodeError as exc:
        raise ValueError("coupon.cvg is not strict ASCII") from exc
    rows = {}
    for lineno, line in enumerate(lines, 1):
        tokens = line.split()
        if not tokens or INT_RE.fullmatch(tokens[0]) is None:
            continue
        require(len(tokens) == 9,
                f"Malformed numeric CVG row at line {lineno}; expected nine fields")
        require(all(INT_RE.fullmatch(token) for token in tokens[:5]),
                f"Malformed CVG identity/count at line {lineno}")
        key = tuple(int(token, 10) for token in tokens[:4])
        count = int(tokens[4], 10)
        require(count >= 0, f"Negative CVG contact count at line {lineno}")
        for token in tokens[5:]:
            finite_float(token, f"CVG line {lineno}")
        require(key not in rows, f"Duplicate CVG identity {key}")
        rows[key] = count
    require(rows, "coupon.cvg has no parsed convergence states")
    return rows


def validate_event_schedule(events: list[dict], cvg: dict, sta: dict) -> dict:
    by_key = {}
    for event in events:
        key = (event["step"], event["increment"], event["attempt"], event["iteration"])
        require(key not in by_key, f"Duplicate convergence event identity {key}")
        by_key[key] = event
    require(set(by_key) == set(cvg),
            "Convergence event identities do not exactly match CVG identities")
    final_by_state = {}
    for state_key in sta:
        candidates = [(key, row) for key, row in by_key.items()
                      if key[:3] == state_key]
        final = [(key, row) for key, row in candidates
                 if row["final_convergence_ok"] == 1]
        require(len(final) == 1,
                f"Accepted STA state {state_key} lacks exactly one final convergence event")
        key, row = final[0]
        require(row["mechanical_applicable"] == 1 and
                row["mechanical_gate_ok"] == 1 and
                row["contact_change_gate_clear"] == 1,
                f"Final inherited convergence gate failed at {key}")
        require(sta[state_key]["iterations"] == key[3],
                f"STA iteration count differs from final convergence event at {state_key}")
        final_by_state[state_key] = {"key": key, "event": row,
                                     "contact_count": cvg[key]}
    require(len(final_by_state) == 50,
            "Accepted final-convergence state count is not 50")
    return final_by_state


def parse_frd(data: bytes, expected: dict) -> dict[tuple[int, int], dict]:
    try:
        lines = data.decode("ascii").splitlines()
    except UnicodeDecodeError as exc:
        raise ValueError("coupon.frd is not strict ASCII") from exc
    frames = {}
    current = None
    in_disp = False
    descriptors = []
    nodes = {}

    def finish_disp():
        nonlocal in_disp, descriptors, nodes
        require(current is not None and in_disp, "Unexpected FRD DISP terminator")
        require(descriptors == ["D1", "D2", "D3", "ALL"],
                "FRD DISP field descriptors differ from U output")
        require(set(nodes) == set(expected_nodes),
                f"FRD DISP node coverage differs: got {len(nodes)} nodes")
        current["nodes"] = nodes
        current["disp_count"] = len(nodes)
        in_disp = False
        descriptors = []
        nodes = {}

    def finish_frame():
        nonlocal current
        if current is None:
            return
        require(not in_disp, "FRD DISP dataset is not terminated")
        require("time" in current and "nodes" in current,
                "FRD frame lacks time or displacement dataset")
        key = (current["step"], current["increment"])
        require(key not in frames, f"Duplicate FRD state identity {key}")
        frames[key] = current
        current = None

    groups = expected["output_node_groups"]
    expected_nodes = set(groups["upper_slave_body"] + groups["lower_master_body"] +
                         groups["unloaded_witness"])
    for lineno, line in enumerate(lines, 1):
        if line.lstrip().startswith("1PSTEP"):
            finish_frame()
            tokens = line.split()
            require(len(tokens) >= 4,
                    f"Malformed FRD 1PSTEP header at line {lineno}")
            require(all(INT_RE.fullmatch(tokens[i]) is not None for i in (2, 3)),
                    f"Malformed FRD step/increment at line {lineno}")
            current = {"increment": int(tokens[2]), "step": int(tokens[3])}
            in_disp = False
            continue
        if current is None:
            continue
        if line.lstrip().startswith("100CL"):
            tokens = line.split()
            require(len(tokens) >= 4 and INT_RE.fullmatch(tokens[3]) is not None,
                    f"Malformed FRD 100CL state line at {lineno}")
            require("time" not in current, "Duplicate FRD 100CL time record")
            current["time"] = finite_float(tokens[2], f"FRD time line {lineno}")
            current["node_count_header"] = int(tokens[3])
            continue
        if line.startswith(" -4"):
            tokens = line.split()
            require(current.get("time") is not None and not in_disp and
                    len(tokens) >= 2 and tokens[1] == "DISP",
                    f"Unexpected FRD dataset at line {lineno}")
            in_disp = True
            continue
        if in_disp and line.startswith(" -5"):
            tokens = line.split()
            require(len(tokens) >= 2, f"Malformed FRD field descriptor at {lineno}")
            descriptors.append(tokens[1])
            continue
        if in_disp and line.startswith(" -1"):
            require(len(line) == 49,
                    f"Malformed FRD DISP nodal row width at line {lineno}")
            node_text = line[3:13].strip()
            require(INT_RE.fullmatch(node_text) is not None,
                    f"Malformed FRD node ID at line {lineno}")
            node = int(node_text)
            values = [finite_float(line[start:start + 12].strip(),
                                   f"FRD node {node} line {lineno}")
                      for start in (13, 25, 37)]
            require(node not in nodes, f"Duplicate FRD node {node} at line {lineno}")
            nodes[node] = values
            continue
        if in_disp and line.startswith(" -3"):
            finish_disp()
            continue
    finish_frame()
    require(len(frames) == 50, "FRD must contain exactly 50 accepted DISP states")
    require(all(frame["node_count_header"] == 58 and frame["disp_count"] == 58
                for frame in frames.values()),
            "FRD node count header or complete node coverage differs from 58")
    return frames


def parse_dat_cels(data: bytes) -> dict[float, float]:
    try:
        lines = data.decode("ascii").splitlines()
    except UnicodeDecodeError as exc:
        raise ValueError("coupon.dat is not strict ASCII") from exc
    records = {}
    for index, line in enumerate(lines):
        match = CELS_RE.search(line)
        if not match:
            continue
        time = finite_float(match.group(1), f"DAT CELS header line {index + 1}")
        value_line = index + 1
        while value_line < len(lines) and not lines[value_line].strip():
            value_line += 1
        require(value_line < len(lines),
                f"DAT CELS energy missing after line {index + 1}")
        tokens = lines[value_line].split()
        require(len(tokens) == 1,
                f"DAT CELS energy row must contain one scalar at line {value_line + 1}")
        value = finite_float(tokens[0], f"DAT CELS line {value_line + 1}")
        require(time not in records, f"Duplicate DAT CELS time {time}")
        records[time] = value
    return records


def amplitude_at(time_s: float, expected: dict) -> float:
    points = expected["procedure"]["amplitude"]
    reference = expected["procedure"]["amplitude_reference_displacement_mm"]
    require(points[0][0] <= time_s <= points[-1][0],
            f"Output time {time_s} falls outside the prescribed amplitude")
    for (ta, va), (tb, vb) in zip(points, points[1:]):
        if ta <= time_s <= tb:
            fraction = (time_s - ta) / (tb - ta)
            return reference * (va + fraction * (vb - va))
    raise ValueError(f"Could not interpolate prescribed amplitude at {time_s}")


def trial_coverage(parsed: dict, cvg: dict) -> tuple[dict, dict]:
    groups = defaultdict(list)
    for row in parsed["CCXPT_TRIAL"]:
        key = (row["step"], row["increment"], row["attempt"], row["iteration"])
        groups[key].append(row)
    extra = set(groups) - set(cvg)
    require(not extra, f"TRIAL rows contain identities absent from CVG: {sorted(extra)}")
    per_state = {}
    for key, count in cvg.items():
        rows = groups.get(key, [])
        require(len(rows) == count,
                f"TRIAL count {len(rows)} differs from CVG contact count {count} at {key}")
        identities = [(row["element"], row["gauss_index"]) for row in rows]
        require(len(identities) == len(set(identities)),
                f"Duplicate TRIAL element/Gauss identity at {key}")
        elements = [row["element"] for row in rows]
        gauss_points = [row["gauss_index"] for row in rows]
        require(len(elements) == len(set(elements)) and
                len(gauss_points) == len(set(gauss_points)),
                f"Duplicate TRIAL element or Gauss-point identity at {key}")
        per_state["/".join(map(str, key))] = {
            "cvg_contact_count": count, "trial_rows": len(rows)}
    return groups, {"cvg_state_count": len(cvg),
                    "trial_identity_count": len(groups),
                    "zero_contact_cvg_states_without_trial_rows": sum(
                        count == 0 and key not in groups for key, count in cvg.items()),
                    "per_state": per_state}


def assert_near(actual: float, reference: float, tolerance: float, label: str) -> None:
    require(abs(actual - reference) <= tolerance,
            f"{label}: observed {actual:.17g}, expected {reference:.17g} ± {tolerance:g}")


def check_normal(row: dict, fields: tuple[str, str, str], tol: float, label: str) -> list[float]:
    vec = [row[name] for name in fields]
    assert_near(vec[0], 0.0, tol, f"{label} normal x")
    assert_near(vec[1], 0.0, tol, f"{label} normal y")
    assert_near(vec[2], 1.0, tol, f"{label} master normal z")
    return vec


def audit_capture(stdout: bytes, frd_data: bytes, sta_data: bytes,
                  cvg_data: bytes, dat_data: bytes,
                  expected: dict, trace_format: dict) -> dict:
    require(b" Job finished" in stdout or b"\n Job finished" in stdout,
            "solver.stdout lacks normal CalculiX completion marker")
    parsed = parse_trace(stdout, trace_format)
    events, _contacts = parse_events(stdout)
    sta = parse_sta(sta_data, expected)
    cvg = parse_cvg(cvg_data)
    final_states = validate_event_schedule(events, cvg, sta)
    frd = parse_frd(frd_data, expected)
    groups, coverage = trial_coverage(parsed, cvg)
    dat_cels = parse_dat_cels(dat_data)

    oracle = expected["accepted_endpoint_oracle"]
    proc = expected["procedure"]
    total_time = proc["total_time_s"]
    gap_tol = oracle["trial_gap_abs_tolerance_mm"]
    normal_tol = oracle["unit_normal_abs_tolerance"]
    formula_p_tol = oracle["compression_pressure_abs_tolerance_N_per_mm2"]
    formula_e_tol = oracle["compression_energy_abs_tolerance_N_mm"]
    groups_by_key = groups
    final_contact_energy = {}
    map_rows = parsed["CCXPT_MAP"]
    trial_rows = parsed["CCXPT_TRIAL"]
    slave_faces = {11, 21}
    master_faces = {113, 123}
    map_groups = defaultdict(list)
    for row in map_rows:
        key = (row["step"], row["increment"], row["attempt"], row["native_iteration"])
        map_groups[key].append(row)
        require(row["tie"] == 1 and
                row["nmethod"] == proc["required_map_nmethod"] and
                row["pressure_law"] == 2 and row["slave_face_encoded"] in slave_faces and
                row["master_face_encoded"] in master_faces and
                row["slave_face_index"] > 0 and row["gauss_index"] > 0,
                "MAP identity, face, method or law differs from prepared coupon")
        assert_near(row["penalty_modulus"],
                    expected["contact_fixture"]["normal_slope_K_N_per_mm3"],
                    1e-8, "MAP penalty modulus")
        require(row["area"] > 0.0, "MAP reports nonpositive point area")
        check_normal(row, ("normal_x", "normal_y", "normal_z"), normal_tol, "MAP")
        if row["raw_signed_gap"] > 0.0:
            require(row["native_isol"] == 0,
                    "Dynamic mode-2 MAP retained a positive-gap contact spring")
    map_seen = set()
    for row in map_rows:
        identity = (row["step"], row["increment"], row["attempt"],
                    row["native_iteration"], row["generation_loop"], row["tie"],
                    row["slave_face_index"], row["gauss_index"])
        require(identity not in map_seen, f"Duplicate MAP identity {identity}")
        map_seen.add(identity)

    state_times = {}
    for state_key, sta_row in sta.items():
        step, inc, attempt = state_key
        frd_key = (step, inc)
        require(frd_key in frd, f"FRD missing STA state {frd_key}")
        frd_state = frd[frd_key]
        assert_near(frd_state["time"], sta_row["total_time"],
                    oracle["accepted_time_abs_tolerance_s"],
                    f"FRD/STA time at {state_key}")
        state_times[state_key] = sta_row["total_time"]
        target_gap = amplitude_at(sta_row["total_time"], expected)
        nodes = frd_state["nodes"]
        for node in expected["output_node_groups"]["upper_slave_body"]:
            u = nodes[node]
            assert_near(u[0], 0.0, oracle["frd_displacement_abs_tolerance_mm"],
                        f"FRD upper U1 node {node} at {state_key}")
            assert_near(u[1], 0.0, oracle["frd_displacement_abs_tolerance_mm"],
                        f"FRD upper U2 node {node} at {state_key}")
            assert_near(u[2], target_gap, oracle["frd_displacement_abs_tolerance_mm"],
                        f"FRD upper U3 node {node} at {state_key}")
        for node in expected["output_node_groups"]["lower_master_body"] + \
                    expected["output_node_groups"]["unloaded_witness"]:
            for component, value in enumerate(nodes[node], 1):
                assert_near(value, 0.0, oracle["frd_displacement_abs_tolerance_mm"],
                            f"FRD node {node} U{component} at {state_key}")

        final = final_states[state_key]
        final_key = final["key"]
        conv_key = (step, inc, attempt, final_key[3])
        candidates = map_groups.get(conv_key, [])
        require(candidates, f"No final-iteration MAP candidates at {conv_key}")
        last_loop = max(row["generation_loop"] for row in candidates)
        final_map = [row for row in candidates if row["generation_loop"] == last_loop]
        require(final_map, f"No rows in final MAP generation loop at {conv_key}")
        for row in final_map:
            assert_near(row["raw_signed_gap"], target_gap,
                        oracle["map_gap_abs_tolerance_mm"],
                        f"Final MAP gap at {conv_key}")

    # Validate each corrected spring row against its own absolute output time.
    trial_by_time = defaultdict(list)
    for row in trial_rows:
        key = (row["step"], row["increment"], row["attempt"], row["iteration"])
        state_key = key[:3]
        require(state_key in sta, f"TRIAL state absent from accepted STA: {key}")
        require(0.0 <= row["relative_time"] <= 1.0,
                f"TRIAL relative_time outside [0,1] at {key}")
        trial_time = row["relative_time"] * total_time
        accepted_time = sta[state_key]["total_time"]
        assert_near(trial_time, accepted_time,
                    oracle["accepted_time_abs_tolerance_s"],
                    f"TRIAL relative_time binding at {key}")
        assert_near(frd[(state_key[0], state_key[1])]["time"], trial_time,
                    oracle["accepted_time_abs_tolerance_s"],
                    f"TRIAL/FRD time binding at {key}")
        expected_gap = amplitude_at(accepted_time, expected)
        assert_near(row["corrected_gap"], expected_gap, gap_tol,
                    f"TRIAL corrected gap at {key}")
        require(row["tie"] == 1 and row["slave_face_encoded"] in slave_faces and
                row["master_face_encoded"] in master_faces and
                row["slave_face_index"] > 0 and row["gauss_index"] > 0 and
                row["element"] > 0,
                f"TRIAL identity/face differs from prepared coupon at {key}")
        require(row["energy_enabled"] == proc["required_trial_energy_enabled"],
                f"TRIAL energy is disabled at {key}")
        assert_near(row["kscale"], proc["required_trial_kscale"], 1e-12,
                    f"TRIAL kscale at {key}")
        require(row["area"] > 0.0, f"TRIAL has nonpositive area at {key}")
        n = check_normal(row, ("normal_x", "normal_y", "normal_z"), normal_tol,
                         f"TRIAL {key}")
        stiffness = expected["contact_fixture"]["normal_slope_K_N_per_mm3"]
        pressure_ref = -stiffness * row["corrected_gap"] / row["kscale"]
        energy_ref = (0.5 * stiffness * row["area"] *
                      row["corrected_gap"] ** 2 / row["kscale"])
        assert_near(row["signed_pressure"], pressure_ref, formula_p_tol,
                    f"TRIAL signed pressure law at {key}")
        assert_near(row["spring_energy"], energy_ref, formula_e_tol,
                    f"TRIAL spring energy law at {key}")
        require(row["spring_energy"] >= 0.0,
                f"TRIAL has negative spring energy at {key}")
        resultant = [row["signed_pressure"] * row["area"] * x for x in n]
        row["derived_normal_resultant_N"] = resultant
        trial_by_time[state_key].append(row)

    aggregate_law_checks = 0
    force_tol = oracle["compression_force_abs_tolerance_N"]
    energy_tol = oracle["compression_energy_abs_tolerance_N_mm"]
    for key, rows in groups_by_key.items():
        observed_vector = [sum(row["derived_normal_resultant_N"][i] for row in rows)
                           for i in range(3)]
        expected_vector = [0.0, 0.0, 0.0]
        expected_energy = 0.0
        observed_energy = 0.0
        for row in rows:
            p_ref = (-expected["contact_fixture"]["normal_slope_K_N_per_mm3"] *
                     row["corrected_gap"] / row["kscale"])
            for i, component in enumerate(("normal_x", "normal_y", "normal_z")):
                expected_vector[i] += p_ref * row["area"] * row[component]
            expected_energy += (0.5 * expected["contact_fixture"][
                "normal_slope_K_N_per_mm3"] * row["area"] *
                row["corrected_gap"] ** 2 / row["kscale"])
            observed_energy += row["spring_energy"]
        vector_error = math.sqrt(sum((observed_vector[i] - expected_vector[i]) ** 2
                                     for i in range(3)))
        require(vector_error <= force_tol,
                f"Aggregate derived normal resultant differs from point-law sum at {key}")
        assert_near(observed_energy, expected_energy, energy_tol,
                    f"Aggregate spring energy law at {key}")
        aggregate_law_checks += 1

    events_by_time = {}
    for state_key, final in final_states.items():
        final_key = final["key"]
        rows = groups_by_key.get(final_key, [])
        final_contact_energy[state_key] = sum(row["spring_energy"] for row in rows)
        events_by_time[state_key] = rows

    state_checks = []
    for state in oracle["states"]:
        state_key = (1, state["increment"], 1)
        require(state_key in final_states, f"Missing accepted event endpoint {state_key}")
        final = final_states[state_key]
        rows = events_by_time[state_key]
        count = final["contact_count"]
        if state["label"] == "open" or state["label"] == "reopened after compression":
            require(count == state["accepted_post_correction_active_spring_count"] and not rows,
                    f"Accepted open endpoint is not empty at {state_key}")
        elif state["label"].startswith("touch"):
            for row in rows:
                assert_near(row["signed_pressure"], 0.0,
                            oracle["touch_pressure_abs_tolerance_N_per_mm2"],
                            f"Touch pressure at {state_key}")
                assert_near(row["spring_energy"], 0.0,
                            oracle["zero_energy_tolerance_N_mm"],
                            f"Touch energy at {state_key}")
            vec = [sum(row["derived_normal_resultant_N"][i] for row in rows)
                   for i in range(3)]
            require(math.sqrt(sum(x * x for x in vec)) <=
                    oracle["touch_resultant_abs_tolerance_N"],
                    f"Touch derived resultant exceeds tolerance at {state_key}")
        elif state["label"] == "compression":
            require(count > 0 and rows, "Compression endpoint has no active TRIAL rows")
            area = sum(row["area"] for row in rows)
            assert_near(area, expected["contact_fixture"]["initial_face_area_mm2"],
                        oracle["compression_area_abs_tolerance_mm2"],
                        "Compression total active area")
            for row in rows:
                assert_near(row["signed_pressure"], state["pressure_N_per_mm2"],
                            oracle["compression_pressure_abs_tolerance_N_per_mm2"],
                            "Compression point pressure")
            vec = [sum(row["derived_normal_resultant_N"][i] for row in rows)
                   for i in range(3)]
            assert_near(vec[0], 0.0, state.get("force_tolerance_N", 0.004),
                        "Compression derived resultant x")
            assert_near(vec[1], 0.0, state.get("force_tolerance_N", 0.004),
                        "Compression derived resultant y")
            assert_near(vec[2], state["resultant_force_magnitude_N"],
                        oracle["compression_force_abs_tolerance_N"],
                        "Compression derived resultant z")
            energy = sum(row["spring_energy"] for row in rows)
            assert_near(energy, state["accepted_contact_spring_energy_N_mm"],
                        oracle["compression_energy_abs_tolerance_N_mm"],
                        "Compression contact spring energy")
            final_contact_energy[state_key] = energy
        state_checks.append({"label": state["label"], "state": list(state_key),
                             "contact_count": count, "trial_rows": len(rows),
                             "energy_N_mm": final_contact_energy[state_key]})

    positive_gap_threshold = expected["retained_open_trial_oracle"][
        "minimum_positive_gap_mm"]
    stale = [row for row in trial_rows
             if row["corrected_gap"] > positive_gap_threshold]
    require(len(stale) >= expected["retained_open_trial_oracle"][
        "minimum_positive_gap_active_trial_records"],
        "No positive-gap active corrected TRIAL row was observed")
    stale_groups = defaultdict(list)
    for row in stale:
        require(row["signed_pressure"] < 0.0,
                "Resolved positive-gap active TRIAL lacks negative pressure")
        key = (row["step"], row["increment"], row["attempt"], row["iteration"])
        stale_groups[key].append(row)
    stale_summaries = []
    for key, rows in sorted(stale_groups.items()):
        area = sum(row["area"] for row in rows)
        p_area = sum(row["signed_pressure"] * row["area"] for row in rows)
        vector = [sum(row["derived_normal_resultant_N"][i] for row in rows)
                  for i in range(3)]
        energy = sum(row["spring_energy"] for row in rows)
        analytic_vector = [0.0, 0.0, 0.0]
        analytic_energy = 0.0
        stiffness = expected["contact_fixture"]["normal_slope_K_N_per_mm3"]
        for row in rows:
            p_ref = -stiffness * row["corrected_gap"] / row["kscale"]
            for i, component in enumerate(("normal_x", "normal_y", "normal_z")):
                analytic_vector[i] += p_ref * row["area"] * row[component]
            analytic_energy += (0.5 * stiffness * row["area"] *
                                row["corrected_gap"] ** 2 / row["kscale"])
        vector_error = math.sqrt(sum((vector[i] - analytic_vector[i]) ** 2
                                     for i in range(3)))
        require(vector_error <= force_tol,
                f"Positive-gap aggregate resultant differs from its analytic sum at {key}")
        assert_near(energy, analytic_energy, energy_tol,
                    f"Positive-gap aggregate energy differs from its analytic sum at {key}")
        stale_summaries.append({"identity": list(key),
            "time_s": rows[0]["relative_time"] * total_time,
            "row_count": len(rows), "observed_area_mm2": area,
            "gap_min_mm": min(row["corrected_gap"] for row in rows),
            "gap_max_mm": max(row["corrected_gap"] for row in rows),
            "pressure_area_sum_N": p_area,
            "derived_resultant_N": vector,
            "analytic_resultant_N": analytic_vector,
            "resultant_error_norm_N": vector_error,
            "energy_N_mm": energy,
            "analytic_energy_N_mm": analytic_energy})

    cels_report = {"status": "UNAVAILABLE_UNVALIDATED", "records": len(dat_cels)}
    if dat_cels:
        if len(dat_cels) != 50:
            cels_report["status"] = "INCOMPLETE_UNVALIDATED"
        else:
            mismatches = []
            tolerance = max(oracle["compression_energy_abs_tolerance_N_mm"],
                            oracle["zero_energy_tolerance_N_mm"])
            for (step, inc, att), time in state_times.items():
                found = next((value for t, value in dat_cels.items()
                              if abs(t - time) <= oracle["accepted_time_abs_tolerance_s"]), None)
                if found is None:
                    mismatches.append({"state": [step, inc, att], "reason": "missing time"})
                    continue
                ref = final_contact_energy[(step, inc, att)]
                if abs(found - ref) > tolerance:
                    mismatches.append({"state": [step, inc, att],
                                       "observed": found, "trace_energy": ref})
            cels_report["status"] = "MATCHES_TRACE_SECONDARY" if not mismatches else \
                "MISMATCH_UNVALIDATED"
            cels_report["mismatches"] = mismatches

    return {
        "schema": "implicit_contact_point_trace_dynamic_verifier/v1",
        "status": "PASS_DYNAMIC_CONTACT_POINT_TRACE_KNOWN_ANSWER",
        "native_run": True,
        "accepted_states": 50,
        "map_rows": len(map_rows),
        "trial_rows": len(trial_rows),
        "aggregate_trial_law_groups_checked": aggregate_law_checks,
        "unmapped_rows": len(parsed["CCXPT_UNMAPPED"]),
        "zero_contact_cvg_states_without_trial_rows":
            coverage["zero_contact_cvg_states_without_trial_rows"],
        "trial_cvg_coverage": coverage,
        "endpoint_checks": state_checks,
        "positive_gap_active_trial_observations": stale_summaries,
        "normal_resultant_interpretation":
            "Derived as signed_pressure*observed_area*master_normal; neither fnl nor CFN is emitted.",
        "dat_cels_secondary": cels_report,
        "mechanical_acceptance": False,
        "contact_method_acceptance": False,
        "joint_acceptance": False,
        "release": False,
    }


def expect_rejection(callable_, label: str) -> None:
    try:
        callable_()
    except (ValueError, AssertionError):
        return
    raise AssertionError(f"Synthetic negative did not reject: {label}")


def synthetic_capture(expected: dict, trace_format: dict):
    node_groups = expected["output_node_groups"]
    nodes = sorted(set(sum(node_groups.values(), [])))
    k = expected["contact_fixture"]["normal_slope_K_N_per_mm3"]
    amplitude = expected["procedure"]["amplitude"]
    reference = expected["procedure"]["amplitude_reference_displacement_mm"]

    def prescribed(time):
        for (ta, va), (tb, vb) in zip(amplitude, amplitude[1:]):
            if ta <= time <= tb:
                return reference * (va + (time - ta) / (tb - ta) * (vb - va))
        return 0.0

    trace_lines, cvg_lines, event_lines, sta_lines = [], [], [], []
    frd_lines, dat_lines = [], []
    final_energy = {}
    for inc in range(1, 51):
        time = inc * 0.1
        gap = prescribed(time)
        active = gap <= 0.0 or inc == 41
        pressure = -k * gap
        energy = 0.5 * k * 4.0 * gap * gap
        final_energy[inc] = energy if gap <= 0.0 else 0.0
        sta_lines.append(f"  1 {inc:10d} 1 2 {time:.8E} {time:.8E} 1.00000000E-01")
        for iteration in (1, 2):
            count = 4 if active and not (inc == 41 and iteration == 2) else 0
            cvg_lines.append(f"1 {inc} 1 {iteration} {count} 0.0 0.0 0.0 0.0")
            event = {
                "event": "CCX223_ATTEMPT04_CONVERGENCE", "step": 1,
                "increment": inc, "attempt": 1, "iteration": iteration,
                "mechanical_applicable": 1,
                "iteration_ok": int(iteration > 1),
                "mechanical_residual_ok": 1,
                "displacement_ok": 1, "visco_ok": 1,
                "contact_change_gate_clear": 1,
                "no_contact_now": int(count == 0),
                "no_contact_at_start": int(count == 0),
                "contact_present": int(count > 0),
                "mechanical_gate_ok": int(iteration > 1),
                "no_contact_energy_eligible": 0,
                "contact_energy_eligible": 0,
                "iconvergence": int(iteration > 1), "idivergence": 0,
                "final_convergence_ok": int(iteration > 1),
            }
            event_lines.append(json.dumps(event, separators=(",", ":")))
            map_gap = -0.00001 if inc == 41 and iteration == 1 else gap
            isol = 0 if map_gap > 0.0 else 2
            map_ints = [1, inc, 1, iteration, 1, 1, 1, 1, 11, 113,
                        isol, 4, 2]
            map_reals = [map_gap, map_gap, 4.0, k, 0.0, 0.0, 0.0, 1.0,
                         0.0, 0.0, 0.0, 0.0]
            trace_lines.append("CCXPT_MAP " + " ".join(map(str, map_ints + map_reals)))
            for point in range(count):
                point_area = 1.0
                point_energy = 0.5 * k * point_area * gap * gap
                trial_ints = [1, inc, 1, iteration, 9000 + inc * 4 + point,
                              point + 1, 1, 11, 113, 1, 1]
                trial_reals = [gap, 0.0, 0.0, pressure, 0.0, 0.0, point_area,
                               point_energy, 0.0, 0.0, 1.0, 1.0, time / 5.0]
                trace_lines.append("CCXPT_TRIAL " + " ".join(
                    map(str, trial_ints + trial_reals)))
        dat_lines += [f" total contact spring energy for time {time:.8E}",
                      "", f"        {final_energy[inc]:.8E}", ""]
        frd_lines += [f"    1PSTEP                         1 {inc:11d} {1:11d}",
                      f"  100CL 101 {time:.8E} 58 0 1 1",
                      " -4 DISP        4    1",
                      " -5 D1          1    2    1    0",
                      " -5 D2          1    2    2    0",
                      " -5 D3          1    2    3    0",
                      " -5 ALL         1    2    0    0    1ALL"]
        upper = set(node_groups["upper_slave_body"])
        for node in nodes:
            u3 = gap if node in upper else 0.0
            frd_lines.append(f" -1{node:10d}{0.0:12.5E}{0.0:12.5E}{u3:12.5E}")
        frd_lines.append(" -3")
    stdout = ("Synthetic offline capture; no solver was run.\n Job finished\n" +
              "\n".join(event_lines + trace_lines) + "\n").encode("ascii")
    return (stdout, ("\n".join(frd_lines) + "\n").encode("ascii"),
            ("SUMMARY OF JOB INFORMATION\n" + "\n".join(sta_lines) + "\n").encode("ascii"),
            ("SUMMARY OF C0NVERGENCE INFORMATION\n" + "\n".join(cvg_lines) + "\n").encode("ascii"),
            ("\n".join(dat_lines) + "\n").encode("ascii"))


def run_self_test() -> dict:
    expected, trace_format = verify_prepared_contract()
    capture = synthetic_capture(expected, trace_format)
    report = audit_capture(*capture, expected, trace_format)
    require(report["status"] == "PASS_DYNAMIC_CONTACT_POINT_TRACE_KNOWN_ANSWER" and
            report["zero_contact_cvg_states_without_trial_rows"] > 0,
            "Synthetic complete capture did not pass with zero-count CVG states")
    require(any(abs(row["time_s"] - 4.1) < 1e-8
                for row in report["positive_gap_active_trial_observations"]),
            "Synthetic stale positive-gap TRIAL was not reported")

    stdout, frd, sta, cvg, dat = capture
    traces = stdout.decode("ascii").splitlines()
    active_key = "CCXPT_TRIAL 1 30 1 2 "
    missing_trial = "\n".join(line for line in traces
                               if not line.startswith(active_key)).encode("ascii")
    expect_rejection(lambda: audit_capture(missing_trial, frd, sta, cvg, dat,
                                           expected, trace_format),
                     "missing positive-count TRIAL")
    extra_trial_row = None
    for line in traces:
        if line.startswith("CCXPT_TRIAL 1 30 1 2 "):
            tokens = line.split()
            tokens[2] = "10"
            tokens[4] = "2"
            extra_trial_row = " ".join(tokens)
            break
    require(extra_trial_row is not None, "Synthetic active TRIAL not built")
    extra_stdout = ("\n".join(traces + [extra_trial_row]) + "\n").encode("ascii")
    expect_rejection(lambda: audit_capture(extra_stdout, frd, sta, cvg, dat,
                                           expected, trace_format),
                     "TRIAL row for zero-count CVG identity")
    disabled_energy = []
    for line in traces:
        if line.startswith("CCXPT_TRIAL "):
            tokens = line.split()
            tokens[11] = "0"
            disabled_energy.append(" ".join(tokens))
        else:
            disabled_energy.append(line)
    expect_rejection(lambda: audit_capture(("\n".join(disabled_energy) + "\n").encode(),
                                           frd, sta, cvg, dat, expected, trace_format),
                     "disabled spring energy")
    wrong_scale = []
    for line in traces:
        if line.startswith("CCXPT_TRIAL "):
            tokens = line.split()
            tokens[23] = "0.5"
            wrong_scale.append(" ".join(tokens))
        else:
            wrong_scale.append(line)
    expect_rejection(lambda: audit_capture(("\n".join(wrong_scale) + "\n").encode(),
                                           frd, sta, cvg, dat, expected, trace_format),
                     "nonunit spring scale")
    wrong_trial_time = []
    for line in traces:
        if line.startswith("CCXPT_TRIAL "):
            tokens = line.split()
            tokens[-1] = "0.5"
            wrong_trial_time.append(" ".join(tokens))
        else:
            wrong_trial_time.append(line)
    expect_rejection(lambda: audit_capture(("\n".join(wrong_trial_time) + "\n").encode(),
                                           frd, sta, cvg, dat, expected, trace_format),
                     "TRIAL relative time not bound to accepted state")
    wrong_map_filter = []
    changed = False
    for line in traces:
        if not changed and line.startswith("CCXPT_MAP "):
            tokens = line.split()
            if finite_float(tokens[14], "synthetic MAP raw gap") > 0.0:
                tokens[11] = "2"
                line = " ".join(tokens)
                changed = True
        wrong_map_filter.append(line)
    require(changed, "Synthetic capture lacks a positive-gap MAP row")
    expect_rejection(lambda: audit_capture(("\n".join(wrong_map_filter) + "\n").encode(),
                                           frd, sta, cvg, dat, expected, trace_format),
                     "positive-gap MAP retained in active set")
    wrong_pressure = []
    for line in traces:
        if line.startswith("CCXPT_TRIAL 1 30 1 2 "):
            tokens = line.split()
            tokens[15] = "99.0"
            wrong_pressure.append(" ".join(tokens))
        else:
            wrong_pressure.append(line)
    expect_rejection(lambda: audit_capture(("\n".join(wrong_pressure) + "\n").encode(),
                                           frd, sta, cvg, dat, expected, trace_format),
                     "signed pressure law mismatch")
    biased_aggregate_energy = []
    for line in traces:
        if line.startswith("CCXPT_TRIAL 1 41 1 1 "):
            tokens = line.split()
            tokens[19] = f"{float(tokens[19]) + 7.5e-7:.17e}"
            biased_aggregate_energy.append(" ".join(tokens))
        else:
            biased_aggregate_energy.append(line)
    expect_rejection(lambda: audit_capture(
        ("\n".join(biased_aggregate_energy) + "\n").encode(),
        frd, sta, cvg, dat, expected, trace_format),
        "coherent small per-point energy bias exceeding the aggregate tolerance")
    broken_frd = b"\n".join(frd.splitlines()[:-60]) + b"\n"
    expect_rejection(lambda: audit_capture(stdout, broken_frd, sta, cvg, dat,
                                           expected, trace_format),
                     "incomplete FRD state/node coverage")
    return {"status": "PASS_SYNTHETIC_DYNAMIC_AUDIT_AND_NEGATIVE_CONTROLS",
            "native_run": False,
            "accepted_states": report["accepted_states"],
            "trial_rows": report["trial_rows"],
            "zero_count_cvg_states_without_trial_rows":
                report["zero_contact_cvg_states_without_trial_rows"],
            "positive_gap_example_time_s": 4.1,
            "negative_controls_rejected": [
                "missing TRIAL row for positive CVG count",
                "extra TRIAL row for zero-count CVG identity",
                "energy_enabled=0",
                "nonunit kscale",
                "TRIAL relative time mismatch",
                "positive-gap MAP kept in active set",
                "signed pressure law mismatch",
                "aggregate energy sum error beyond tolerance",
                "incomplete FRD state/node coverage",
            ]}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--self-test", action="store_true",
                      help="run native-free synthetic acceptance and negative controls")
    mode.add_argument("--audit-dir", type=Path,
                      help="audit an existing capture directory; never launches a solver")
    args = parser.parse_args()
    try:
        if args.self_test:
            report = run_self_test()
        else:
            expected, trace_format = verify_prepared_contract()
            root = args.audit_dir
            report = audit_capture(
                (root / "solver.stdout").read_bytes(),
                (root / "coupon.frd").read_bytes(),
                (root / "coupon.sta").read_bytes(),
                (root / "coupon.cvg").read_bytes(),
                (root / "coupon.dat").read_bytes(), expected, trace_format)
        print(json.dumps(report, indent=2, sort_keys=True, allow_nan=False))
        return 0
    except Exception as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
