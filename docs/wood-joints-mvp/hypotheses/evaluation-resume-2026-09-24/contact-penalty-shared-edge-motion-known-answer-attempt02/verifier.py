#!/usr/bin/env python3
"""Audit the frozen penalty shared-edge/full-cap-motion method fixture.

This verifier accepts only a complete, hash-matched parent execution with one
accepted endpoint for each case. It does not launch CalculiX and never grants
mechanical, work-energy, joint, or release acceptance.
"""

from __future__ import annotations

from fractions import Fraction
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import re
import sys


HERE = Path(__file__).resolve().parent
PAIR_PARSER_RELATIVE = "../contact-penalty-touch-work-known-answer-attempt01/pair_output.py"
PAIR_PARSER_SHA256 = "c729729c9f7d520dfaa4d835e5a0c2ce633ab9e12e0e60aef931b1c98df03496"
CASES = ["shared_slave_motion", "cross_role_motion"]
EXPECTED_SCHEMA = "calculix_penalty_shared_edge_motion_known_answer/v1"
FREEZE_SCHEMA = "contact_penalty_shared_edge_motion_freeze/v1"
EXECUTION_SCHEMA = "contact_penalty_shared_edge_motion_execution/v1"
PRECOMMITTED_GATES = {
    "force_abs_tolerance_N": 0.041,
    "pair_resultant_moment_abs_tolerance_Nmm": 0.041,
    "moment_closure_tolerance_Nmm": 0.041,
    "profile_gap_warp_absolute_tolerance_mm": 1e-7,
    "normal_compliance_relative_tolerance": 0.01,
    "normal_compliance_absolute_tolerance_mm3_per_N": 1e-10,
    "energy_relative_tolerance": 0.01,
    "energy_absolute_tolerance_Nmm": 1e-6,
    "transverse_auxiliary_and_force_closure_tolerance_N": 0.041,
}


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

    def reject_constant(value):
        raise ValueError(f"Nonfinite JSON number {value} in {path}")

    def finite_float(value):
        result = float(value)
        require(math.isfinite(result), f"Nonfinite JSON number {value} in {path}")
        return result

    return json.loads(path.read_text(), object_pairs_hook=unique_pairs,
                      parse_float=finite_float, parse_constant=reject_constant)


def number(token: str) -> float:
    value = str(token).strip()
    # Some Fortran E formats omit the E before a three-digit exponent.
    match = re.fullmatch(r"([+-]?(?:\d+\.\d*|\.\d+))([+-]\d{3})", value)
    if match:
        value = match[1] + "E" + match[2]
    result = float(value.replace("D", "E").replace("d", "e"))
    require(math.isfinite(result), f"Nonfinite numeric output: {token}")
    return result


def close_vector(actual, expected, tolerance: float) -> float:
    require(len(actual) == len(expected), "Vector length differs")
    error = math.sqrt(sum((float(a) - float(b)) ** 2
                          for a, b in zip(actual, expected)))
    require(error <= tolerance,
            f"Vector error {error:.8g} exceeds {tolerance:.8g}")
    return error


def cross(a, b):
    return (a[1] * b[2] - a[2] * b[1],
            a[2] * b[0] - a[0] * b[2],
            a[0] * b[1] - a[1] * b[0])


def vector_add(a, b):
    return tuple(x + y for x, y in zip(a, b))


def vector_norm(v):
    return math.sqrt(sum(float(x) * float(x) for x in v))


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    require(spec is not None and spec.loader is not None,
            f"Cannot load pinned local module {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def check_preparation(expected: dict) -> dict:
    require(expected.get("schema") == EXPECTED_SCHEMA,
            "Unexpected expected.json schema")
    require(expected.get("case_order") == CASES,
            "Expected case order differs")
    require(set(expected.get("cases", {})) == set(CASES),
            "Expected case set differs")
    require(len(expected["analytical_known_answer"][
                "affine_endpoint_displacement_mm_by_physical_node"]) == 375,
            "The prepared three-body mesh oracle must contain exactly 375 physical nodes")
    require(expected.get("native_execution_authorized") is False and
            expected.get("mechanical_or_joint_acceptance") is False,
            "Known-answer contract overclaims native or joint acceptance")
    for key, value in PRECOMMITTED_GATES.items():
        require(expected["inherited_numerical_gates"].get(key) == value,
                f"Precommitted numerical gate changed: {key}")

    prepare_path = HERE / "prepare.py"
    require(expected.get("preparation_script_sha256") == sha(prepare_path),
            "Preparation hash cross-link differs")
    readiness = read_json(HERE / "readiness.json")
    source_snapshot = read_json(HERE / "source-snapshot.json")
    preflight = read_json(HERE / "preflight.json")
    require(readiness.get("status") == "PREPARED_FOR_PARENT_REVIEW" and
            readiness.get("native_execution_authorized") is False and
            readiness.get("input_freeze_created") is False,
            "Preparation readiness overclaims execution or freeze")
    require(readiness.get("expected_sha256") == sha(HERE / "expected.json") and
            readiness.get("source_snapshot_sha256") == sha(HERE / "source-snapshot.json") and
            readiness.get("preflight_sha256") == sha(HERE / "preflight.json"),
            "Readiness hash links differ")
    require(expected.get("source_snapshot") == "source-snapshot.json" and
            source_snapshot["preparation_script"]["sha256"] == sha(prepare_path),
            "Source snapshot does not bind the current producer")
    require(preflight.get("status") ==
            "PASS_STATIC_ORACLE_AND_INPUT_PREFLIGHT_NO_NATIVE_EXECUTION" and
            preflight.get("native_execution") is False and
            preflight.get("freeze_created") is False,
            "Static preflight overclaims native execution or freeze")

    producer = load_module("shared_edge_motion_prepare_for_audit", prepare_path)
    generated, regenerated_preflight = producer.build_all()
    for relative, content in generated.items():
        path = HERE / relative
        require(path.is_file() and path.read_bytes() == content,
                f"Prepared input/output does not reproduce: {relative}")
    require(regenerated_preflight["status"] == preflight["status"],
            "In-memory preflight status differs from saved preflight")

    require(expected.get("mesh_sha256") == readiness.get("input_sha256"),
            "Expected/readiness deck hash inventories differ")
    expected_paths = {f"input/{case}.inp" for case in CASES}
    require(set(expected["mesh_sha256"]) == expected_paths,
            "Expected deck inventory differs from the exact two-case paths")
    for case in CASES:
        spec = expected["cases"][case]
        path = f"input/{case}.inp"
        require(spec["case_order"] == CASES.index(case) + 1 and
                path in expected["mesh_sha256"],
                f"{case}: case order/path differs from expected mesh inventory")
        require(readiness["input_sha256"][path] == expected["mesh_sha256"][path],
                f"{case}: readiness input hash differs")
    require(expected["motion_map"]["coarse_rank5_obstruction"]["PORT_TOP"]["exact_rank"] == 5
            and expected["motion_map"]["coarse_rank5_obstruction"]["PORT_RIGHT"]["exact_rank"] == 5,
            "The documented coarse rank-5 obstruction changed")
    for port, spec in expected["motion_map"]["maps"].items():
        require(spec["pivot_rank"] == 6 and len(spec["dependent_dofs"]) == 6 and
                len(spec["controller_node_ids"]) == 6,
                f"{port}: full six-component motion map incomplete")
    for case in CASES:
        audit = expected["serialized_equation_audits"][case]
        require(audit["equation_count"] == 12 and
                audit["max_affine_field_equation_residual_mm"] <= 1e-15,
                f"{case}: serialized equation audit failed")
        for port in ("PORT_TOP", "PORT_RIGHT"):
            row = audit["per_port"][port]
            require(row["contact_nodes_remain_independent"] is True and
                    row["no_pivot_term_in_opposite_port_map"] is True and
                    row["deterministic_state_virtual_work_error_Nmm"] <= 1e-15,
                    f"{case}/{port}: equation work/independence audit failed")

    return {"status": "PASS_STATIC_PACKET_LINKS", "preflight_status": preflight["status"],
            "source_member_count": source_snapshot["source_archive"]["pinned_member_sha256"].__len__(),
            "deck_sha256": expected["mesh_sha256"]}


def parse_cards(text: str) -> list[dict]:
    result = []
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("**"):
            continue
        if line.startswith("*"):
            fields = [field.strip() for field in line[1:].split(",")]
            options, flags = {}, set()
            for field in fields[1:]:
                if "=" in field:
                    key, value = field.split("=", 1)
                    options[key.strip().upper()] = value.strip().upper()
                elif field:
                    flags.add(field.upper())
            result.append({"keyword": fields[0].upper(), "options": options,
                           "flags": flags, "data": []})
        else:
            require(result, "Input data precedes the first keyword")
            result[-1]["data"].append(line)
    return result


def audit_deck(case: str, expected: dict, text: str) -> dict:
    spec = expected["cases"][case]
    require(hashlib.sha256(text.encode()).hexdigest() ==
            expected["mesh_sha256"][f"input/{case}.inp"],
            f"{case}: executed deck SHA differs")
    cards = parse_cards(text)
    by_name = {}
    for card in cards:
        by_name.setdefault(card["keyword"], []).append(card)
    require(not by_name.get("CLOAD"), f"{case}: force-driven CLOAD found")
    require(len(by_name.get("EQUATION", [])) == 12,
            f"{case}: expected twelve serialized map equations")
    require(len(by_name.get("CONTACT PAIR", [])) == 2,
            f"{case}: expected two contact pairs")
    expected_pairs = [(row["slave"], row["master"]) for row in spec["contact_pairs"]]
    actual_pairs = []
    for card in by_name["CONTACT PAIR"]:
        require(len(card["data"]) == 1, "Malformed *CONTACT PAIR card")
        actual_pairs.append(tuple(part.strip().upper()
                                  for part in card["data"][0].split(",")))
    require(actual_pairs == expected_pairs,
            f"{case}: contact pair roles/order differ from the oracle")
    node_file = by_name.get("NODE FILE", [])
    require(len(node_file) == 1 and
            node_file[0]["options"].get("NSET") == "ALL_PHYSICAL_NODES" and
            [item.upper() for line in node_file[0]["data"]
             for item in line.split(",") if item.strip()] == ["U", "RF"],
            f"{case}: physical-node FRD U/RF request differs")
    control_print = [card for card in by_name.get("NODE PRINT", [])
                     if card["options"].get("NSET") == "PORT_CONTROLS"]
    require(len(control_print) == 1 and
            [item.upper() for line in control_print[0]["data"]
             for item in line.split(",") if item.strip()] == ["U"],
            f"{case}: control-node DAT U request differs")
    require(not [card for card in node_file
                 if card["options"].get("NSET") == "PORT_CONTROLS"],
            f"{case}: unsupported separate control-node FRD request")
    el_file = by_name.get("EL FILE", [])
    require(len(el_file) == 1 and el_file[0]["options"].get("FREQUENCY") == "1" and
            [item.upper() for line in el_file[0]["data"]
             for item in line.split(",") if item.strip()] == ["S"],
            f"{case}: full physical stress FRD request required for SOF")
    section_surfaces = [card["options"].get("SURFACE")
                        for card in by_name.get("SECTION PRINT", [])]
    require(section_surfaces == ["PORT_TOP", "PORT_RIGHT"] and
            all([item.upper() for line in card["data"] for item in line.split(",")
                 if item.strip()] == ["SOF"]
                for card in by_name["SECTION PRINT"]),
            f"{case}: cap SOF output requests differ")
    require(len(by_name.get("CONTACT FILE", [])) == 1 and
            [item.upper() for line in by_name["CONTACT FILE"][0]["data"]
             for item in line.split(",") if item.strip()] == ["CDIS", "CSTR"],
            f"{case}: CDIS/CSTR output request differs")
    require(len(by_name.get("CONTACT PRINT", [])) == 3,
            f"{case}: expected CELS plus two pair-specific print requests")
    pair_prints = {(card["options"].get("SLAVE"), card["options"].get("MASTER")):
                   [item.upper() for line in card["data"] for item in line.split(",")
                    if item.strip()]
                   for card in by_name["CONTACT PRINT"]
                   if "SLAVE" in card["options"]}
    require(set(pair_prints) == set(expected_pairs) and
            all(value == ["CF", "CFN", "CFS"] for value in pair_prints.values()),
            f"{case}: pair resultant output selection differs")
    totals = [card for card in by_name["CONTACT PRINT"]
              if "SLAVE" not in card["options"]]
    require(len(totals) == 1 and
            [item.upper() for line in totals[0]["data"]
             for item in line.split(",") if item.strip()] == ["CELS"],
            f"{case}: penalty CELS output request differs")
    require(len(by_name.get("EL PRINT", [])) == 3 and
            {card["options"].get("ELSET") for card in by_name["EL PRINT"]} ==
            {"CENTRAL", "LOWER", "LEFT"} and
            all([item.upper() for line in card["data"] for item in line.split(",")
                 if item.strip()] == ["ELSE"] for card in by_name["EL PRINT"]),
            f"{case}: per-body ELSE request differs")
    return {"contact_pairs": actual_pairs, "node_file_cards": len(node_file),
            "stress_file_cards": len(el_file), "section_surfaces": section_surfaces,
            "pair_output_count": len(pair_prints)}


def numeric_rows(path: Path, width: int) -> list[list[str]]:
    rows = []
    for line in path.read_text(errors="replace").splitlines():
        fields = line.split()
        if not fields or not re.fullmatch(r"\d+", fields[0]):
            continue
        require(len(fields) == width, f"Malformed numeric row in {path.name}: {line}")
        for token in fields[1:]:
            number(token)
        rows.append(fields)
    require(rows, f"No numeric records in {path.name}")
    return rows


def accepted_trace(folder: Path, output_limit: int) -> dict:
    cvg = numeric_rows(folder / "coupon.cvg", 9)
    keys = [tuple(int(number(token)) for token in row[:4]) for row in cvg]
    require(len(keys) == len(set(keys)), "Duplicate CVG state/iteration identity")
    groups = {}
    for step, increment, attempt, iteration in keys:
        groups.setdefault((step, increment, attempt), []).append(iteration)
    require(set(groups) == {(1, 1, 1)}, "Unexpected CVG attempt, increment, or step")
    for identity, iterations in groups.items():
        require(iterations == list(range(1, len(iterations) + 1)),
                f"Incomplete convergence iteration sequence {identity}")

    sta = numeric_rows(folder / "coupon.sta", 7)
    accepted, rejected = [], []
    for row in sta:
        attempt_token = row[2]
        is_rejected = attempt_token.endswith("U")
        attempt = int(attempt_token.removesuffix("U"))
        state = (int(number(row[0])), int(number(row[1])), attempt)
        iterations = int(number(row[3]))
        require(groups.get(state, [])[-1:] == [iterations],
                "STA final iteration differs from CVG")
        total, step_time, increment_time = (number(token) for token in row[4:7])
        if is_rejected:
            rejected.append([*state, iterations])
        else:
            accepted.append({"step": state[0], "increment": state[1],
                             "attempt": state[2], "iterations": iterations,
                             "total_time": total, "step_time": step_time,
                             "increment_time": increment_time})
    require(not rejected, "A rejected attempt/cutback is present")
    require(len(accepted) == 1, "Expected exactly one accepted full increment")
    state = accepted[0]
    require((state["step"], state["increment"], state["attempt"]) == (1, 1, 1) and
            state["iterations"] > 0 and keys[-1] == (1, 1, 1, state["iterations"]),
            "Accepted state identity or terminal CVG row differs")
    require(all(abs(state[key] - 1.0) <= 2e-6
                for key in ("total_time", "step_time", "increment_time")),
            "Accepted state is not at full endpoint time 1")

    stdout = (folder / "coupon.stdout").read_text(errors="replace")
    stderr = (folder / "coupon.stderr").read_text(errors="replace")
    require("*ERROR" not in (stdout + "\n" + stderr).upper(),
            "Native output contains an error")
    printed = []
    step = increment = attempt = None
    for line in stdout.splitlines():
        match = re.fullmatch(r"\s*STEP\s+(\d+)\s*", line, re.IGNORECASE)
        if match:
            step = int(match[1]); increment = attempt = None
        elif match := re.fullmatch(r"\s*increment\s+(\d+)\s+attempt\s+(\d+)\s*",
                                   line, re.IGNORECASE):
            increment, attempt = map(int, match.groups())
        elif match := re.fullmatch(r"\s*iteration\s+(\d+)\s*", line,
                                   re.IGNORECASE):
            require(None not in (step, increment, attempt),
                    "Native iteration transcript omits state identity")
            printed.append((step, increment, attempt, int(match[1])))
    require(printed == keys, "Native stdout does not reproduce the complete CVG trace")
    require((folder / "coupon.stdout").stat().st_size <= output_limit and
            (folder / "coupon.stderr").stat().st_size <= output_limit,
            "Native stdout/stderr exceeds frozen bound")
    return {"accepted_state": state, "cvg_rows": len(keys),
            "iterations": len(keys), "rejected_attempts": rejected,
            "stdout_iteration_rows": len(printed)}


DAT_HEADER = re.compile(
    r"^\s*(displacements\s*\([^)]*\)|forces\s*\([^)]*\))\s+for set\s+(\w+)\s+and time\s+(\S+)",
    re.IGNORECASE)


def parse_dat(path: Path, physical_nodes: set[int], controller_nodes: set[int]) -> tuple[dict, dict, dict]:
    fields, active = {}, None
    for line in path.read_text(errors="replace").splitlines():
        if match := DAT_HEADER.match(line):
            raw_quantity, nset, time_token = match.groups()
            quantity = "U" if raw_quantity.lower().startswith("displacements") else "RF"
            key = (quantity, nset.upper(), number(time_token))
            require(key not in fields, f"Duplicate DAT field selection: {key}")
            fields[key] = {}
            active = key
            continue
        if active is None:
            continue
        row = line.split()
        if len(row) == 4 and row[0].isdigit():
            node = int(row[0])
            values = tuple(number(token) for token in row[1:])
            require(node not in fields[active], f"Duplicate DAT node {node} in {active}")
            fields[active][node] = values

    expected_keys = {("U", "ALL_PHYSICAL_NODES", 1.0),
                     ("RF", "ALL_PHYSICAL_NODES", 1.0),
                     ("U", "PORT_CONTROLS", 1.0)}
    require(set(fields) == expected_keys,
            f"DAT field/state/NSET identities differ: {sorted(fields)}")
    require(set(fields[("U", "ALL_PHYSICAL_NODES", 1.0)]) == physical_nodes and
            set(fields[("RF", "ALL_PHYSICAL_NODES", 1.0)]) == physical_nodes,
            "DAT physical U/RF node coverage is incomplete or extra")
    require(set(fields[("U", "PORT_CONTROLS", 1.0)]) == controller_nodes,
            "DAT controller U node coverage is incomplete or extra")
    return ({node: value for node, value in fields[("U", "ALL_PHYSICAL_NODES", 1.0)].items()},
            {node: value for node, value in fields[("RF", "ALL_PHYSICAL_NODES", 1.0)].items()},
            {node: value for node, value in fields[("U", "PORT_CONTROLS", 1.0)].items()})


ENERGY_HEADER = re.compile(
    r"^\s*total internal energy for set\s+(\w+)\s+and time\s+(\S+)\s*$",
    re.IGNORECASE)
CELS_HEADER = re.compile(r"^\s*total contact spring energy for time\s+(\S+)\s*$",
                         re.IGNORECASE)


def parse_energies(path: Path) -> tuple[dict, dict]:
    lines = path.read_text(errors="replace").splitlines()
    else_rows, cels_rows = {}, {}
    for i, line in enumerate(lines):
        if match := ENERGY_HEADER.match(line):
            body, time_token = match.groups()
            require(body.upper() not in else_rows, f"Duplicate ELSE total: {body}")
            value_line = next((row.strip() for row in lines[i + 1:] if row.strip()), None)
            require(value_line is not None and len(value_line.split()) == 1,
                    f"Missing or malformed ELSE value for {body}")
            else_rows[body.upper()] = (number(time_token), number(value_line))
        elif match := CELS_HEADER.match(line):
            time_token = match[1]
            require("CELS" not in cels_rows, "Duplicate CELS total")
            value_line = next((row.strip() for row in lines[i + 1:] if row.strip()), None)
            require(value_line is not None and len(value_line.split()) == 1,
                    "Missing or malformed CELS value")
            cels_rows["CELS"] = (number(time_token), number(value_line))
    require(set(else_rows) == {"CENTRAL", "LOWER", "LEFT"} and set(cels_rows) == {"CELS"},
            "DAT is missing body ELSE or penalty CELS channel")
    require(all(abs(time - 1.0) <= 2e-6 for time, _ in else_rows.values()) and
            abs(cels_rows["CELS"][0] - 1.0) <= 2e-6,
            "Energy totals do not refer to accepted endpoint time 1")
    return ({body: value for body, (_time, value) in else_rows.items()},
            cels_rows["CELS"][1])


SECTION_HEADERS = [
    "total surface force (fx,fy,fz) and moment about the origin(mx,my,mz)",
    "center of gravity and mean normal",
    "moment about the center of gravity(mx,my,mz)",
    "area, normal force (+ = tension), shear force (size), torque and bending moment (size)",
]


def parse_sections(path: Path) -> dict:
    lines = [" ".join(line.split()) for line in path.read_text(errors="replace").splitlines()]
    reports = {}
    for i, line in enumerate(lines):
        match = re.fullmatch(r"statistics for surface set (\w+) and time (\S+)", line,
                             re.IGNORECASE)
        if not match:
            continue
        surface, time_token = match.groups()
        key = (surface.upper(), number(time_token))
        require(key not in reports, f"Duplicate SOF report {key}")
        vectors = []
        cursor = i + 1
        for heading in SECTION_HEADERS:
            while cursor < len(lines) and not lines[cursor]:
                cursor += 1
            require(cursor < len(lines) and
                    lines[cursor].replace(" ", "").lower() == heading.replace(" ", "").lower(),
                    f"Unexpected/truncated SOF section {key}")
            cursor += 1
            while cursor < len(lines) and not lines[cursor]:
                cursor += 1
            require(cursor < len(lines), f"Missing SOF row in {key}")
            vectors.append([number(token) for token in lines[cursor].split()])
            cursor += 1
        require([len(row) for row in vectors] == [6, 6, 3, 5],
                f"Wrong SOF report component count {key}")
        reports[key] = {"force_N": vectors[0][:3], "moment_origin_Nmm": vectors[0][3:],
                        "centroid_mm": vectors[1][:3], "mean_normal": vectors[1][3:],
                        "moment_centroid_Nmm": vectors[2], "area_mm2": vectors[3][0],
                        "normal_force_N_tension_positive": vectors[3][1],
                        "shear_N": vectors[3][2], "torque_Nmm": vectors[3][3],
                        "bending_Nmm": vectors[3][4]}
    require(set(reports) == {("PORT_TOP", 1.0), ("PORT_RIGHT", 1.0)},
            "Missing, extra, or untimed cap SOF report")
    return {surface: row for (surface, _time), row in reports.items()}


def parse_frd(path: Path, physical_nodes: set[int], accepted_state: dict) -> dict:
    blocks = []
    active_kind, active_labels, active_rows = None, [], {}
    state_identity, time = None, None
    for line in path.read_text(errors="replace").splitlines():
        fields = line.split()
        if fields and fields[0] == "1PSTEP":
            require(active_kind is None and len(fields) >= 4, "Malformed FRD state marker")
            state_identity = (int(number(fields[3])), int(number(fields[2])))
        elif fields and fields[0] == "100CL":
            require(len(fields) >= 3, "Malformed FRD time marker")
            time = number(fields[2])
        elif line.startswith(" -4"):
            require(active_kind is None and len(fields) >= 2, "Malformed FRD field marker")
            active_kind = fields[1].upper()
            require(active_kind in {"DISP", "FORC", "CONTACT", "STRESS", "ERROR"},
                    f"Unexpected FRD field {active_kind}")
            active_labels, active_rows = [], {}
        elif active_kind and line.startswith(" -5"):
            require(len(fields) >= 2, "Malformed FRD component label")
            active_labels.append(fields[1].upper())
        elif active_kind and line.startswith(" -1"):
            require(len(line) >= 13, "Malformed FRD field row")
            entity = int(number(line[3:13]))
            values = [number(line[offset:offset + 12])
                      for offset in range(13, len(line.rstrip()), 12)
                      if line[offset:offset + 12].strip()]
            expected_width = (6 if active_kind in {"CONTACT", "STRESS"}
                              else 1 if active_kind == "ERROR" else 3)
            require(len(values) == expected_width,
                    f"Malformed FRD {active_kind} component row")
            # Contact and stress output may report multiple field locations for
            # one entity. Their finite rows are checked, while coverage remains
            # diagnostic. U/RF must have unique physical-node identities.
            if active_kind in {"DISP", "FORC", "STRESS", "ERROR"}:
                require(entity not in active_rows, f"Duplicate FRD {active_kind} node {entity}")
            if active_kind == "ERROR":
                require(entity in physical_nodes,
                        f"FRD ERROR field references nonphysical node {entity}")
            active_rows.setdefault(entity, values)
        elif active_kind and line.startswith(" -3"):
            require(state_identity == (accepted_state["step"], accepted_state["increment"])
                    and time is not None and abs(time - accepted_state["total_time"]) <= 2e-6,
                    "FRD block is not at the accepted endpoint")
            required_labels = {
                "DISP": ["D1", "D2", "D3", "ALL"],
                "FORC": ["F1", "F2", "F3", "ALL"],
                "CONTACT": ["COPEN", "CSLIP1", "CSLIP2", "CPRESS", "CSHEAR1", "CSHEAR2"],
                "STRESS": ["SXX", "SYY", "SZZ", "SXY", "SYZ", "SZX"],
                "ERROR": ["STR(%)"],
            }[active_kind]
            require(active_labels == required_labels,
                    f"Unexpected FRD {active_kind} component labels")
            if active_kind != "ERROR":
                require(active_rows, f"Empty FRD {active_kind} field")
            if active_kind == "STRESS":
                require(set(active_rows) == physical_nodes,
                        "FRD STRESS must cover each of the 375 physical nodes exactly once")
            if active_kind == "ERROR":
                require(not any(block["kind"] == "ERROR" and
                                block["state"] == state_identity for block in blocks),
                        "Duplicate FRD ERROR field at the accepted state")
            blocks.append({"kind": active_kind, "labels": active_labels,
                           "nodes": active_rows, "state": state_identity, "time": time})
            active_kind, active_labels, active_rows = None, [], {}
    require(active_kind is None, "Truncated FRD field block")
    displacements = [block for block in blocks if block["kind"] == "DISP"]
    forces = [block for block in blocks if block["kind"] == "FORC"]
    contacts = [block for block in blocks if block["kind"] == "CONTACT"]
    stresses = [block for block in blocks if block["kind"] == "STRESS"]
    errors = [block for block in blocks if block["kind"] == "ERROR"]
    require(len(displacements) == len(forces) == 1,
            "Expected one accepted physical DISP and FORC FRD block")
    require(set(displacements[0]["nodes"]) == physical_nodes and
            set(forces[0]["nodes"]) == physical_nodes,
            "FRD physical U/RF node coverage is incomplete or extra")
    require(len(stresses) == 1,
            "FRD is missing the complete full-mesh EL FILE S output")
    return {"displacements": displacements[0]["nodes"],
            "forces": forces[0]["nodes"],
            "contact_blocks": len(contacts),
            "contact_entity_coverage_diagnostic": sorted(
                {entity for block in contacts for entity in block["nodes"]}),
            "stress_blocks": len(stresses),
            "stress_node_count": len(stresses[0]["nodes"]),
            "error_blocks": len(errors),
            "error_row_counts": [len(block["nodes"]) for block in errors],
            "stress_entity_coverage_diagnostic": sorted(
                {entity for block in stresses for entity in block["nodes"]})}


def load_pair_parser(freeze: dict):
    parser_path = HERE / PAIR_PARSER_RELATIVE
    require(parser_path.is_file() and sha(parser_path) == PAIR_PARSER_SHA256,
            "Pinned pair-resultant parser changed")
    require(freeze["files_sha256"].get(PAIR_PARSER_RELATIVE) == PAIR_PARSER_SHA256,
            "Freeze does not bind the pair-resultant parser")
    module = load_module("pinned_pair_output_parser", parser_path)
    synthetic = module.synthetic_preflight()
    require(synthetic["status"] == "PASS_SYNTHETIC_PAIR_RESULTANT_PARSER" and
            synthetic["native_output_qualified"] is False,
            "Pinned pair parser synthetic contract failed")
    return module, synthetic


def parse_boundaries(text: str) -> tuple[dict, dict]:
    fixed, motion = {}, {}
    for card in parse_cards(text):
        if card["keyword"] != "BOUNDARY":
            continue
        is_motion = "AMPLITUDE" in card["options"]
        target = motion if is_motion else fixed
        for line in card["data"]:
            values = [part.strip() for part in line.split(",")]
            require(len(values) in (3, 4) and values[0].isdigit(),
                    f"Malformed explicit nodal boundary row: {line}")
            node, first, last = int(values[0]), int(values[1]), int(values[2])
            value = number(values[3]) if len(values) == 4 else 0.0
            for dof in range(first, last + 1):
                key = (node, dof)
                require(key not in target, f"Duplicate boundary DOF {key}")
                target[key] = value
    return fixed, motion


def audit_known_answer(case: str, expected: dict, mesh: dict, deck_text: str,
                       displacement: dict, reactions: dict, controls: dict,
                       energies: tuple[dict, float], sections: dict,
                       pairs: list[dict], frd: dict) -> dict:
    oracle = expected["analytical_known_answer"]
    gates = expected["inherited_numerical_gates"]
    case_spec = expected["cases"][case]
    physical_nodes = set(map(int, oracle["affine_endpoint_displacement_mm_by_physical_node"]))
    oracle_u = {int(node): tuple(map(float, values)) for node, values in
                oracle["affine_endpoint_displacement_mm_by_physical_node"].items()}
    require(set(displacement) == physical_nodes and set(reactions) == physical_nodes,
            "DAT physical fields do not cover the analytical node inventory")

    profile_error = {"CENTRAL_UX": 0.0, "CENTRAL_UZ": 0.0,
                     "LOWER_UZ": 0.0, "LEFT_UX": 0.0}
    for node in physical_nodes:
        body = "CENTRAL" if node < 10000 else "LOWER" if node < 20000 else "LEFT"
        component_names = {"CENTRAL": (0, 2), "LOWER": (2,), "LEFT": (0,)}[body]
        for component in component_names:
            key = {("CENTRAL", 0): "CENTRAL_UX", ("CENTRAL", 2): "CENTRAL_UZ",
                   ("LOWER", 2): "LOWER_UZ", ("LEFT", 0): "LEFT_UX"}[(body, component)]
            profile_error[key] = max(profile_error[key],
                                     abs(displacement[node][component] - oracle_u[node][component]))
    profile_limit = gates["profile_gap_warp_absolute_tolerance_mm"]
    require(max(profile_error.values()) <= profile_limit,
            "Inherited normal displacement profile differs from affine oracle")

    # Match coincident six-node face nodes by exact undeformed coordinates.
    contact_specs = oracle["contact_pairs"]
    gap_errors, warp_errors = {}, {}
    for central_surface, axis_name, component, outer_surface in (
            ("Z_CENTRAL", "Z", 2, "Z_LOWER"),
            ("X_CENTRAL", "X", 0, "X_LEFT")):
        central = contact_specs[central_surface]
        outer_nodes = set(central["outer_nodes"])
        coord_lookup = {mesh["nodes"][node]: node for node in outer_nodes}
        require(len(coord_lookup) == len(outer_nodes), f"{axis_name}: duplicate outer coordinates")
        central_nodes = set(central["central_nodes"])
        matched = []
        for node in central_nodes:
            point = mesh["nodes"][node]
            require(point in coord_lookup, f"{axis_name}: contact mesh node does not match")
            matched.append((node, coord_lookup[point]))
        require(len(matched) == 25, f"{axis_name}: expected 25 matching quadratic face nodes")
        actual_gaps = [displacement[a][component] - displacement[b][component]
                       for a, b in matched]
        target_gap = oracle["signed_central_minus_outer_interface_gap_mm_each_pair"]
        gap_errors[axis_name] = max(abs(value - target_gap) for value in actual_gaps)
        require(gap_errors[axis_name] <= profile_limit,
                f"{axis_name}: central-minus-outer signed interface gap differs")
        central_warp = max(displacement[node][component] for node in central_nodes) - min(
            displacement[node][component] for node in central_nodes)
        expected_central_warp = max(oracle_u[node][component] for node in central_nodes) - min(
            oracle_u[node][component] for node in central_nodes)
        outer_warp = max(displacement[node][component] for node in outer_nodes) - min(
            displacement[node][component] for node in outer_nodes)
        expected_outer_warp = max(oracle_u[node][component] for node in outer_nodes) - min(
            oracle_u[node][component] for node in outer_nodes)
        warp_errors[axis_name] = max(abs(central_warp - expected_central_warp),
                                     abs(outer_warp - expected_outer_warp))
        require(warp_errors[axis_name] <= profile_limit,
                f"{axis_name}: interface face warp differs")

    # Controller U is DAT-only. Reconstruct q independently from the physical
    # cap field using the serialized exact P matrices and the same DOF ordering.
    q_by_port = {}
    for port, port_spec in expected["motion_map"]["maps"].items():
        controllers = port_spec["controller_node_ids"]
        q_control = [controls[node][0] for node in controllers]
        q_expected = list(map(float, port_spec["prescribed_q"]))
        for index, (actual, wanted) in enumerate(zip(q_control, q_expected)):
            require(abs(actual - wanted) <= profile_limit,
                    f"{port}: controller q[{index}] differs from prescribed endpoint")
        columns = port_spec["projection_dof_columns"]
        projection = [[float(Fraction(value)) for value in row]
                      for row in port_spec["projection_matrix_P_exact"]]
        require(len(projection) == 6 and all(len(row) == len(columns) for row in projection),
                f"{port}: serialized projection dimensions differ")
        physical_state = [displacement[int(node)][int(dof) - 1] for node, dof in columns]
        q_physical = [sum(coefficient * value for coefficient, value in zip(row, physical_state))
                      for row in projection]
        for index, (actual, controller, wanted) in enumerate(
                zip(q_physical, q_control, q_expected)):
            require(abs(actual - controller) <= profile_limit and
                    abs(actual - wanted) <= profile_limit,
                    f"{port}: physical cap field does not reconstruct q[{index}]")
        q_by_port[port] = {"controller_q": q_control, "physical_q": q_physical,
                           "prescribed_q": q_expected}

    force_limit = gates["force_abs_tolerance_N"]
    moment_limit = gates["pair_resultant_moment_abs_tolerance_Nmm"]
    want_pairs = {(row["slave"], row["master"], quantity)
                  for row in case_spec["contact_pairs"]
                  for quantity in ("CF", "CFN", "CFS")}
    actual_pairs = {(row["slave"], row["master"], row["quantity"]) for row in pairs
                    if abs(row["time"] - 1.0) <= 2e-6}
    require(len(pairs) == 6 and actual_pairs == want_pairs,
            f"{case}: pair CF/CFN/CFS identities are missing, duplicated, or extra")
    pair_rows = {(row["slave"], row["master"], row["quantity"]): row for row in pairs}
    normals = {"Z_CENTRAL": (0.0, 0.0, -1.0),
               "X_CENTRAL": (-1.0, 0.0, 0.0),
               "X_LEFT": (1.0, 0.0, 0.0)}
    pair_diagnostics = []
    pair_forces = {}
    for pair_spec in case_spec["contact_pairs"]:
        slave, master = pair_spec["slave"], pair_spec["master"]
        for quantity, force_key, moment_key in (
                ("CF", "expected_CF_vector_N", "expected_CF_moment_about_origin_Nmm"),
                ("CFN", "expected_CFN_vector_N", "expected_CFN_moment_about_origin_Nmm"),
                ("CFS", "expected_CFS_vector_N", "expected_CFS_moment_about_origin_Nmm")):
            row = pair_rows[(slave, master, quantity)]
            require(abs(row["time"] - 1.0) <= 2e-6,
                    f"{slave}/{master}/{quantity}: wrong endpoint time")
            ferr = close_vector(row["force_N"], pair_spec[force_key], force_limit)
            merr = close_vector(row["moment_N_mm"], pair_spec[moment_key], moment_limit)
            if quantity == "CFN":
                projected = sum(a * b for a, b in zip(row["force_N"], normals[slave]))
                require(abs(projected - pair_spec[
                    "expected_projected_normal_force_N_tension_positive"]) <= force_limit,
                    f"{slave}/{master}: tension-positive compression projection differs")
                pair_forces[(slave, master)] = (tuple(row["force_N"]),
                                                tuple(row["moment_N_mm"]))
            pair_diagnostics.append({"slave": slave, "master": master,
                                     "quantity": quantity, "force_error_N": ferr,
                                     "moment_error_Nmm": merr})

    section_forces, section_moments = {}, {}
    for surface, force, moment_value in (
            ("PORT_TOP", (0.0, 0.0, -4.0), (-4.0, 4.0, 0.0)),
            ("PORT_RIGHT", (-4.0, 0.0, 0.0), (0.0, -4.0, 4.0))):
        report = sections[surface]
        require(vector_norm(report["force_N"]) > 0,
                f"{surface}: zero SOF resultant cannot establish this known-answer output")
        ferr = close_vector(report["force_N"], force, force_limit)
        merr = close_vector(report["moment_origin_Nmm"], moment_value, moment_limit)
        require(report["area_mm2"] > 0 and all(math.isfinite(v) for v in report["centroid_mm"]),
                f"{surface}: SOF section geometry is missing or nonfinite")
        section_forces[surface] = tuple(report["force_N"])
        section_moments[surface] = tuple(report["moment_origin_Nmm"])

    fixed_boundaries, motion_boundaries = parse_boundaries(deck_text)
    require(len(fixed_boundaries) == 57,
            "Explicit support/gauge scalar DOF inventory differs from reviewed fixture")
    control_to_q = {}
    for port_spec in expected["motion_map"]["maps"].values():
        for node, value in zip(port_spec["controller_node_ids"],
                               port_spec["prescribed_q"]):
            control_to_q[node] = float(value)
    require(set(motion_boundaries) == {(node, 1) for node in control_to_q} and
            all(abs(motion_boundaries[(node, 1)] - value) <= 1e-15
                for node, value in control_to_q.items()),
            "Prescribed controller boundary rows differ from q oracle")

    lower_nodes = {node for node, xyz in mesh["nodes"].items()
                   if 10000 < node < 20000 and float(xyz[2]) == -2.0}
    left_nodes = {node for node, xyz in mesh["nodes"].items()
                  if 20000 < node < 30000 and float(xyz[0]) == -2.0}
    require(len(lower_nodes) == len(left_nodes) == 25 and
            all((node, 3) in fixed_boundaries for node in lower_nodes) and
            all((node, 1) in fixed_boundaries for node in left_nodes),
            "Remote-plane support normals differ from reviewed geometry")
    lower_reaction = sum(reactions[node][2] for node in lower_nodes)
    left_reaction = sum(reactions[node][0] for node in left_nodes)
    target_force = oracle["normal_force_N_each_pair"]
    require(abs(lower_reaction - target_force) <= force_limit and
            abs(left_reaction - target_force) <= force_limit,
            "Remote physical support reaction resultants differ from the 4 N oracle")
    normal_support_rows = {(node, 3) for node in lower_nodes} | {(node, 1) for node in left_nodes}
    auxiliary = [0.0, 0.0, 0.0]
    support_moment = [0.0, 0.0, 0.0]
    support_force_total = [0.0, 0.0, 0.0]
    for node, dof in fixed_boundaries:
        value = reactions[node][dof - 1]
        support_force_total[dof - 1] += value
        if (node, dof) not in normal_support_rows:
            auxiliary[dof - 1] += value
        position = tuple(float(mesh["nodes"][node][axis]) + displacement[node][axis]
                         for axis in range(3))
        force_vector = [0.0, 0.0, 0.0]
        force_vector[dof - 1] = value
        contribution = cross(position, force_vector)
        for axis in range(3):
            support_moment[axis] += contribution[axis]
    aux_limit = gates["transverse_auxiliary_and_force_closure_tolerance_N"]
    require(vector_norm(auxiliary) <= aux_limit,
            "Auxiliary/gauge support reaction resultant exceeds inherited limit")

    # Only explicit physical SPC RF values are interpreted as reactions here.
    # Controller or equation-dependent RF values are never summed as generalized
    # port forces. Cap SOF is the pinned section-stress method observation.
    external_force_sum = vector_add(vector_add(section_forces["PORT_TOP"],
                                               section_forces["PORT_RIGHT"]),
                                   tuple(support_force_total))
    force_closure = vector_norm(external_force_sum)
    require(force_closure <= gates["transverse_auxiliary_and_force_closure_tolerance_N"],
            "Physical support plus cap SOF force closure exceeds inherited limit")
    moment_closure_vector = tuple(section_moments["PORT_TOP"][i] +
                                  section_moments["PORT_RIGHT"][i] + support_moment[i]
                                  for i in range(3))
    moment_closure = vector_norm(moment_closure_vector)
    require(moment_closure <= gates["moment_closure_tolerance_Nmm"],
            "Physical support plus cap SOF moment closure exceeds inherited limit")

    compliance = {}
    area = float(oracle["contact_pairs"]["Z_CENTRAL"]["area_central_mm2"])
    compliance_ref = float(oracle["series_compliance_mm3_per_N"])
    compliance_rel = gates["normal_compliance_relative_tolerance"]
    compliance_abs = gates["normal_compliance_absolute_tolerance_mm3_per_N"]
    for axis, port, q_index, force in (
            ("Z", "PORT_TOP", 2, lower_reaction),
            ("X", "PORT_RIGHT", 0, left_reaction)):
        approach = abs(q_by_port[port]["physical_q"][q_index])
        measured = area * approach / abs(force)
        limit = compliance_rel * compliance_ref + compliance_abs
        require(abs(measured - compliance_ref) <= limit,
                f"{axis}: area-normalized endpoint compliance differs")
        compliance[axis] = {"approach_mm": approach, "support_force_N": force,
                            "contact_area_mm2": area,
                            "area_times_approach_over_force_mm3_per_N": measured,
                            "reference_mm3_per_N": compliance_ref,
                            "limit_mm3_per_N": limit}

    observed_else, observed_cels = energies
    energy_ref = oracle["energy_Nmm"]
    energy_rel = gates["energy_relative_tolerance"]
    energy_abs = gates["energy_absolute_tolerance_Nmm"]
    energy_diagnostics = {}
    for body, reference in energy_ref["body_ELSE_Nmm"].items():
        value = observed_else[body]
        limit = energy_rel * reference + energy_abs
        require(abs(value - reference) <= limit,
                f"{body} ELSE differs from analytic strain-energy oracle")
        energy_diagnostics[body] = {"observed_Nmm": value,
                                    "reference_Nmm": reference, "limit_Nmm": limit}
    cels_ref = energy_ref["penalty_CELS_Nmm"]
    cels_limit = energy_rel * cels_ref + energy_abs
    require(abs(observed_cels - cels_ref) <= cels_limit,
            "Penalty CELS differs from analytic mode-1 contact-energy oracle")
    observed_else_sum = sum(observed_else.values())
    observed_total_energy = observed_else_sum + observed_cels
    total_ref = energy_ref["ELSE_plus_CELS_total_Nmm"]
    total_limit = energy_rel * total_ref + energy_abs
    require(abs(observed_total_energy - total_ref) <= total_limit,
            "ELSE plus CELS endpoint sum differs from analytic energy oracle")
    energy_diagnostics["CELS"] = {"observed_Nmm": observed_cels,
                                  "reference_Nmm": cels_ref,
                                  "limit_Nmm": cels_limit}
    energy_diagnostics["ELSE_plus_CELS"] = {
        "observed_Nmm": observed_total_energy, "reference_Nmm": total_ref,
        "limit_Nmm": total_limit,
        "is_external_work_or_path_quadrature": False}

    # Check DAT/FRD parity at all physical nodes without relying on controller
    # fields in FRD (CalculiX 2.23 omits orphan controller nodes there).
    frd_u_error = max(abs(displacement[node][i] - frd["displacements"][node][i])
                      for node in physical_nodes for i in range(3))
    frd_rf_error = max(abs(reactions[node][i] - frd["forces"][node][i])
                       for node in physical_nodes for i in range(3))
    require(frd_u_error <= profile_limit,
            "FRD/DAT physical displacement fields differ beyond the profile gate")
    require(frd_rf_error <= force_limit,
            "FRD/DAT physical reaction fields differ beyond the force gate")

    return {
        "status": "PASS",
        "affine_profile_max_abs_error_mm_by_gate": profile_error,
        "interface_gap_max_abs_error_mm": gap_errors,
        "interface_warp_max_abs_error_mm": warp_errors,
        "port_q_reconstruction": q_by_port,
        "pair_resultants": pair_diagnostics,
        "pair_resultant_zero_means_no_bearing": False,
        "remote_support_reactions_N": {"LOWER_UZ": lower_reaction,
                                        "LEFT_UX": left_reaction},
        "auxiliary_support_resultant_N": auxiliary,
        "cap_sof_bulk_stress_proxy": sections,
        "physical_support_plus_cap_sof_force_closure_N": external_force_sum,
        "physical_support_plus_cap_sof_force_closure_norm_N": force_closure,
        "physical_support_plus_cap_sof_moment_closure_Nmm": moment_closure_vector,
        "physical_support_plus_cap_sof_moment_closure_norm_Nmm": moment_closure,
        "area_normalized_compliance": compliance,
        "endpoint_energy_channels": energy_diagnostics,
        "energy_interpretation": "ELSE/CELS endpoint channel check only; no external-work or path-quadrature inference.",
        "FRD_DAT_physical_U_max_abs_difference_mm": frd_u_error,
        "FRD_DAT_physical_RF_max_abs_difference_N": frd_rf_error,
        "FRD_coverage": {"physical_U_nodes": len(frd["displacements"]),
                         "physical_RF_nodes": len(frd["forces"]),
                         "contact_field_count_is_diagnostic": True,
                         "contact_entity_coverage_is_diagnostic": True,
                         "stress_entity_coverage_is_diagnostic": False,
                         "stress_node_count": frd["stress_node_count"],
                         "incidental_error_fields": frd["error_blocks"],
                         "incidental_error_row_counts": frd["error_row_counts"]},
    }


def synthetic_preflight() -> dict:
    """Exercise the frozen verifier gates with generated data; never runs CCX."""
    from copy import deepcopy
    import tempfile

    expected = read_json(HERE / "expected.json")
    static = check_preparation(expected)
    producer = load_module("shared_edge_motion_prepare_for_synthetic", HERE / "prepare.py")
    mesh = producer.build_mesh()
    generated, _ = producer.build_all()
    decks = {}
    for case in CASES:
        deck_text = generated[f"input/{case}.inp"].decode()
        decks[case] = audit_deck(case, expected, deck_text)

    parser_path = HERE / PAIR_PARSER_RELATIVE
    require(sha(parser_path) == PAIR_PARSER_SHA256,
            "Synthetic preflight found changed pinned pair parser")
    pair_module = load_module("shared_edge_pair_parser_for_synthetic", parser_path)
    pair_test = pair_module.synthetic_preflight()
    require(pair_test["status"] == "PASS_SYNTHETIC_PAIR_RESULTANT_PARSER" and
            pair_test["native_output_qualified"] is False,
            "Pinned pair parser synthetic fixture failed")

    oracle = expected["analytical_known_answer"]
    physical = {int(node) for node in
                oracle["affine_endpoint_displacement_mm_by_physical_node"]}
    displacement = {int(node): tuple(map(float, value)) for node, value in
                    oracle["affine_endpoint_displacement_mm_by_physical_node"].items()}
    reactions = {node: (0.0, 0.0, 0.0) for node in physical}
    lower = {node for node, xyz in mesh["nodes"].items()
             if 10000 < node < 20000 and float(xyz[2]) == -2.0}
    left = {node for node, xyz in mesh["nodes"].items()
            if 20000 < node < 30000 and float(xyz[0]) == -2.0}
    require(len(lower) == len(left) == 25,
            "Synthetic reaction fixture has wrong remote support node count")
    for node in lower:
        reactions[node] = (0.0, 0.0, 4.0 / len(lower))
    for node in left:
        reactions[node] = (4.0 / len(left), 0.0, 0.0)

    controls = {}
    for port_spec in expected["motion_map"]["maps"].values():
        for node, value in zip(port_spec["controller_node_ids"],
                               port_spec["prescribed_q"]):
            controls[int(node)] = (float(value), 0.0, 0.0)
    energy = (dict(oracle["energy_Nmm"]["body_ELSE_Nmm"]),
              float(oracle["energy_Nmm"]["penalty_CELS_Nmm"]))

    sections = {
        "PORT_TOP": {"force_N": (0.0, 0.0, -4.0),
                     "moment_origin_Nmm": (-4.0, 4.0, 0.0),
                     "centroid_mm": (1.0, 1.0, 1.0), "mean_normal": (0.0, 0.0, 1.0),
                     "moment_centroid_Nmm": (0.0, 0.0, 0.0), "area_mm2": 4.0,
                     "normal_force_N_tension_positive": 4.0, "shear_N": 0.0,
                     "torque_Nmm": 0.0, "bending_Nmm": 0.0},
        "PORT_RIGHT": {"force_N": (-4.0, 0.0, 0.0),
                       "moment_origin_Nmm": (0.0, -4.0, 4.0),
                       "centroid_mm": (-1.0, 1.0, 1.0), "mean_normal": (1.0, 0.0, 0.0),
                       "moment_centroid_Nmm": (0.0, 0.0, 0.0), "area_mm2": 4.0,
                       "normal_force_N_tension_positive": 4.0, "shear_N": 0.0,
                       "torque_Nmm": 0.0, "bending_Nmm": 0.0},
    }
    pair_rows_by_case = {}
    for case in CASES:
        rows = []
        for pair_spec in expected["cases"][case]["contact_pairs"]:
            for quantity in ("CF", "CFN", "CFS"):
                rows.append({"slave": pair_spec["slave"], "master": pair_spec["master"],
                             "quantity": quantity, "time": 1.0,
                             "force_N": pair_spec[f"expected_{quantity}_vector_N"],
                             "moment_N_mm": pair_spec[
                                 f"expected_{quantity}_moment_about_origin_Nmm"]})
        pair_rows_by_case[case] = rows

    def row(node: int, values) -> str:
        return f" -1{node:10d}" + "".join(f"{float(value):12.5E}" for value in values)

    # Materialize minimal endpoint DAT/FRD parser fixtures. They are generated
    # in a temporary directory and are never solver output or native evidence.
    dat_lines = []
    for quantity, nset, rows in (
            ("displacements", "ALL_PHYSICAL_NODES", displacement),
            ("forces", "ALL_PHYSICAL_NODES", reactions),
            ("displacements", "PORT_CONTROLS", controls)):
        dat_lines.append(f" {quantity} (vx,vy,vz) for set {nset} and time 1.0000000E+00")
        dat_lines.extend(f"{node} " + " ".join(f"{value:.12E}" for value in values)
                         for node, values in sorted(rows.items()))
    for body, value in energy[0].items():
        dat_lines.extend([f" total internal energy for set {body} and time 1.0000000E+00",
                          f" {value:.12E}"])
    dat_lines.extend([" total contact spring energy for time 1.0000000E+00",
                      f" {energy[1]:.12E}"])
    from_sections = {
        "PORT_TOP": ((0, 0, -4, -4, 4, 0), (1, 1, 1, 0, 0, 1),
                     (0, 0, 0), (4, 4, 0, 0, 0)),
        "PORT_RIGHT": ((-4, 0, 0, 0, -4, 4), (-1, 1, 1, 1, 0, 0),
                       (0, 0, 0), (4, 4, 0, 0, 0)),
    }
    for surface, vectors in from_sections.items():
        dat_lines.append(f" statistics for surface set {surface} and time 1.0")
        for heading, values in zip(SECTION_HEADERS, vectors):
            dat_lines.extend([heading, " ".join(str(value) for value in values)])

    frd_lines = ["1PSTEP 1 1 1", "100CL 1 1.0000000E+00"]
    field_specs = [
        ("DISP", ("D1", "D2", "D3", "ALL"), displacement),
        ("FORC", ("F1", "F2", "F3", "ALL"), reactions),
        ("CONTACT", ("COPEN", "CSLIP1", "CSLIP2", "CPRESS", "CSHEAR1", "CSHEAR2"),
         {min(physical): (0.0,) * 6}),
        ("STRESS", ("SXX", "SYY", "SZZ", "SXY", "SYZ", "SZX"),
         {node: (0.0,) * 6 for node in physical}),
        ("ERROR", ("STR(%)",), {min(physical): (0.0,)}),
    ]
    for kind, labels, rows in field_specs:
        frd_lines.append(f" -4 {kind}")
        frd_lines.extend(f" -5 {label}" for label in labels)
        frd_lines.extend(row(node, values) for node, values in sorted(rows.items()))
        frd_lines.append(" -3")

    with tempfile.TemporaryDirectory(prefix="shared-edge-motion-synthetic-") as folder:
        dat_path, frd_path = Path(folder) / "coupon.dat", Path(folder) / "coupon.frd"
        dat_path.write_text("\n".join(dat_lines) + "\n")
        frd_path.write_text("\n".join(frd_lines) + "\n")
        parsed_u, parsed_rf, parsed_controls = parse_dat(
            dat_path, physical, set(controls))
        parsed_energy = parse_energies(dat_path)
        parsed_sections = parse_sections(dat_path)
        parsed_frd = parse_frd(frd_path, physical,
                               {"step": 1, "increment": 1, "total_time": 1.0})

    positive = {}
    for case in CASES:
        result = audit_known_answer(case, expected, mesh, generated[
            f"input/{case}.inp"].decode(), parsed_u, parsed_rf, parsed_controls,
            parsed_energy, parsed_sections, pair_rows_by_case[case], parsed_frd)
        positive[case] = json.loads(json.dumps(result, allow_nan=False))["status"]
        require(positive[case] == "PASS", f"Synthetic {case} known answer did not pass")

    rejected = {}

    def rejection(name: str, operation) -> None:
        try:
            operation()
        except ValueError as exc:
            rejected[name] = str(exc)
        else:
            raise ValueError(f"Synthetic negative case was incorrectly accepted: {name}")

    def check_known_answer(case: str, expected_arg=expected, u_arg=parsed_u,
                           pairs_arg=None) -> dict:
        return audit_known_answer(
            case, expected_arg, mesh, generated[f"input/{case}.inp"].decode(),
            u_arg, parsed_rf, parsed_controls, parsed_energy, parsed_sections,
            pair_rows_by_case[case] if pairs_arg is None else pairs_arg, parsed_frd)

    wrong_force_pairs = deepcopy(pair_rows_by_case["shared_slave_motion"])
    wrong_force_pairs[0]["force_N"][2] += 0.1
    rejection("wrong_pair_force", lambda: check_known_answer(
        "shared_slave_motion", pairs_arg=wrong_force_pairs))

    wrong_gap_expected = deepcopy(expected)
    wrong_gap_expected["analytical_known_answer"][
        "signed_central_minus_outer_interface_gap_mm_each_pair"] += 0.001
    rejection("wrong_signed_interface_gap", lambda: check_known_answer(
        "shared_slave_motion", expected_arg=wrong_gap_expected))

    missing_node_u = deepcopy(parsed_u)
    missing_node_u.pop(min(physical))
    rejection("missing_physical_node", lambda: check_known_answer(
        "shared_slave_motion", u_arg=missing_node_u))

    missing_pair_rows = deepcopy(pair_rows_by_case["shared_slave_motion"])
    missing_pair_rows.pop()
    rejection("missing_pair_record", lambda: check_known_answer(
        "shared_slave_motion", pairs_arg=missing_pair_rows))

    return {"status": "PASS_SYNTHETIC_METHOD_VERIFIER_PREFLIGHT",
            "native_execution": False, "freeze_created": False,
            "static_packet": static, "deck_audits": decks,
            "pair_parser_preflight": pair_test,
            "DAT_parser": "PASS_SYNTHETIC_ENDPOINT_FIELDS_AND_ENERGY",
            "FRD_parser": {"status": "PASS_SYNTHETIC_DISP_FORC_CONTACT_STRESS_ERROR",
                           "stress_nodes": parsed_frd["stress_node_count"],
                           "error_blocks": parsed_frd["error_blocks"]},
            "known_answer_cases": positive,
            "rejected_negative_cases": rejected,
            "serialized_json": True,
            "mechanical_acceptance": False, "work_energy_acceptance": False,
            "joint_acceptance": False, "release": False}


def audit_case(case: str, expected: dict, freeze: dict, run: dict,
               pair_parser, mesh: dict) -> dict:
    require(run.get("case") == case and run.get("status") == "completed",
            f"{case}: run did not complete successfully")
    state = run.get("container_state", {})
    require(run.get("docker_cli_exit_code") == 0 and state.get("ExitCode") == 0 and
            state.get("OOMKilled") is False and state.get("Running") is False and
            run.get("stop_reason") is None and run.get("container_image") == freeze["image_id"],
            f"{case}: container result/exit/image is not a clean completion")
    limits = freeze["limits"]
    require(run.get("elapsed_seconds", math.inf) <= limits["seconds_per_case"] and
            run.get("total_output_bytes", math.inf) <= limits["output_bytes_per_case"] and
            run.get("max_log_bytes", math.inf) <= limits["stdout_or_stderr_bytes"],
            f"{case}: execution exceeded a frozen resource/output limit")
    folder = HERE / "output" / case
    command = run.get("command", [])
    expected_command = [
        "docker", "run", "--pull=never", "--name", run.get("container"),
        "--network", "none", "--cpus", "1", "--memory", "1g",
        "--memory-swap", "1g", "--user", "__UID_GID__",
        "--env", "OMP_NUM_THREADS=1", "--env", "CCX_NPROC_EQUATION_SOLVER=1",
        "--mount", f"type=bind,src={folder.resolve()},dst=/work",
        "--workdir", "/work", freeze["image_id"],
        expected["solver"]["binary_path"], "-i", "coupon",
    ]
    require(len(command) == len(expected_command) and "--user" in command,
            f"{case}: malformed serial-runner command")
    user_index = command.index("--user") + 1
    expected_command[expected_command.index("__UID_GID__")] = command[user_index]
    require(re.fullmatch(r"\d+:\d+", command[user_index]) and command == expected_command,
            f"{case}: container command differs from frozen serial runner contract")
    require(folder.is_dir() and all(path.is_file() for path in folder.iterdir()),
            f"{case}: output directory missing or contains nested/unexpected items")
    actual_files = {path.name for path in folder.iterdir() if path.name != "execution.json"}
    required_files = {"coupon.inp", "coupon.dat", "coupon.cvg", "coupon.sta",
                      "coupon.frd", "coupon.stdout", "coupon.stderr"}
    require(required_files <= actual_files and actual_files == set(run["outputs_sha256"]),
            f"{case}: captured output inventory differs")
    for name, digest in run["outputs_sha256"].items():
        require(sha(folder / name) == digest, f"{case}: output hash differs: {name}")
    require(sha(folder / "coupon.inp") ==
            expected["mesh_sha256"][f"input/{case}.inp"],
            f"{case}: copied native input differs from the case deck")
    text = (folder / "coupon.inp").read_text()
    deck_audit = audit_deck(case, expected, text)
    trace = accepted_trace(folder, limits["stdout_or_stderr_bytes"])

    physical = set(map(int, expected["analytical_known_answer"][
        "affine_endpoint_displacement_mm_by_physical_node"]))
    controllers = {node for port in expected["motion_map"]["maps"].values()
                   for node in port["controller_node_ids"]}
    displacement, reactions, controls = parse_dat(folder / "coupon.dat", physical, controllers)
    energies = parse_energies(folder / "coupon.dat")
    sections = parse_sections(folder / "coupon.dat")
    pair_rows = pair_parser.parse_pairs((folder / "coupon.dat").read_text())
    frd = parse_frd(folder / "coupon.frd", physical, trace["accepted_state"])
    known_answer = audit_known_answer(case, expected, mesh, text, displacement,
                                     reactions, controls, energies, sections,
                                     pair_rows, frd)
    return {"status": "PASS", "case": case, "deck_output_audit": deck_audit,
            "trace": trace, "known_answer": known_answer,
            "pair_parser_records": len(pair_rows), "FRD_diagnostics": {
                "contact_blocks": frd["contact_blocks"],
                "stress_blocks": frd["stress_blocks"],
                "contact_entity_coverage_diagnostic": frd[
                    "contact_entity_coverage_diagnostic"],
                "stress_entity_coverage_diagnostic": frd[
                    "stress_entity_coverage_diagnostic"]}}


def audit_root() -> dict:
    expected = read_json(HERE / "expected.json")
    static = check_preparation(expected)
    freeze_path, execution_path = HERE / "input-freeze.json", HERE / "execution.json"
    require(freeze_path.is_file() and execution_path.is_file(),
            "Parent freeze and complete execution records are required")
    freeze, execution = read_json(freeze_path), read_json(execution_path)
    require(freeze.get("schema") == FREEZE_SCHEMA and
            execution.get("schema") == EXECUTION_SCHEMA,
            "Unexpected freeze or execution schema")
    require(freeze.get("cases") == expected["case_order"] == CASES,
            "Frozen case inventory/order differs from expected order")
    require(freeze.get("parent_reviewed_expected_sha256") == sha(HERE / "expected.json") and
            execution.get("input_freeze_sha256") == sha(freeze_path),
            "Execution is not bound to the exact parent-reviewed freeze/expected")
    require(freeze.get("image_id") == expected["solver"]["base_image_id"] and
            freeze.get("binary_sha256") == expected["solver"]["binary_sha256"] and
            freeze.get("binary_path") == expected["solver"]["binary_path"],
            "Pinned 2.23 image/executable differs")
    require(freeze.get("mechanical_acceptance") is False and
            freeze.get("work_energy_acceptance") is False and
            freeze.get("joint_acceptance") is False and freeze.get("release") is False and
            execution.get("mechanical_acceptance") is False and
            execution.get("work_energy_acceptance") is False and
            execution.get("joint_acceptance") is False and execution.get("release") is False,
            "Method fixture freeze/execution overclaims acceptance")
    for relative, digest in freeze.get("files_sha256", {}).items():
        require(sha(HERE / relative) == digest, f"Frozen artifact differs: {relative}")
    required_frozen = {
        "README.md", "prepare.py", "readiness.json", "expected.json",
        "source-snapshot.json", "preflight.json", "prefreeze-amendment.md",
        "parent-review.json", "parent-map-audit.py", "verifier.py", "run.py",
        PAIR_PARSER_RELATIVE,
        "input/shared_slave_motion.inp", "input/cross_role_motion.inp",
    }
    require(required_frozen <= set(freeze.get("files_sha256", {})),
            "Frozen inventory omits a preparation, review, runner, parser, or input file")
    review = read_json(HERE / "parent-review.json")
    require(review.get("ready_for_bounded_fixture") is True and
            review.get("motion_pair_energy_contract_reviewed") is True and
            review.get("reviewed_expected_sha256") == sha(HERE / "expected.json"),
            "Parent review does not approve the exact motion/pair/energy contract")
    require(execution.get("status") == "completed_pending_audit" and
            execution.get("frozen_inputs_unchanged") is True,
            "Parent serial execution is incomplete or changed frozen inputs")
    runs = execution.get("runs", [])
    require(len(runs) == len(CASES) and [row.get("case") for row in runs] == CASES and
            all(row.get("status") == "completed" for row in runs) and
            len({row.get("container") for row in runs}) == len(CASES),
            "Missing, reordered, duplicate, or failed case run")
    for case in CASES:
        input_path = f"input/{case}.inp"
        require(input_path in freeze["files_sha256"] and
                freeze["files_sha256"][input_path] == expected["mesh_sha256"][input_path],
                f"{case}: freeze input digest differs from expected case")
    pair_parser, pair_parser_test = load_pair_parser(freeze)
    prep_module = load_module("shared_edge_motion_prepare_for_runtime_audit",
                              HERE / "prepare.py")
    mesh = prep_module.build_mesh()
    results = {}
    for case, run in zip(CASES, runs):
        try:
            results[case] = audit_case(case, expected, freeze, run, pair_parser, mesh)
        except Exception as exc:
            results[case] = {"status": "FAIL", "error": str(exc)}
    if not all(row.get("status") == "PASS" for row in results.values()):
        return {"status": "FAIL", "error": "One or more motion cases failed audit",
                "static_packet": static, "cases": results,
                "pair_parser_synthetic_preflight": pair_parser_test,
                "mechanical_acceptance": False, "work_energy_acceptance": False,
                "joint_acceptance": False, "release": False}
    return {"status": "PASS_SHARED_EDGE_PENALTY_MOTION_METHOD_FIXTURE",
            "static_packet": static, "cases": results,
            "pair_parser_synthetic_preflight": pair_parser_test,
            "mechanical_acceptance": False, "work_energy_acceptance": False,
            "joint_acceptance": False, "release": False,
            "applicability": "Penalty two-pair shared-edge/full-cap-motion coupon only; no current-joint transfer, MORTAR applicability, onset, strength, structural criterion, or release."}


def audit() -> dict:
    try:
        return audit_root()
    except Exception as exc:
        return {"status": "FAIL", "error": str(exc),
                "mechanical_acceptance": False, "work_energy_acceptance": False,
                "joint_acceptance": False, "release": False}


if __name__ == "__main__":
    arguments = set(sys.argv[1:])
    if "--synthetic-preflight" in arguments:
        require(arguments == {"--synthetic-preflight"},
                "--synthetic-preflight cannot be combined with other options")
        result = synthetic_preflight()
        result["verifier_sha256"] = sha(Path(__file__))
        print(json.dumps(result, sort_keys=True, allow_nan=False))
        raise SystemExit(0 if result["status"] ==
                         "PASS_SYNTHETIC_METHOD_VERIFIER_PREFLIGHT" else 1)
    write = "--write" in arguments
    require(arguments <= {"--write"}, "Unknown verifier command-line option")
    result = audit()
    result["verifier_sha256"] = sha(Path(__file__))
    result["execution_sha256"] = sha(HERE / "execution.json") if (HERE / "execution.json").exists() else None
    if write:
        with (HERE / "verifier.json").open("x") as stream:
            json.dump(result, stream, indent=2, sort_keys=True)
            stream.write("\n")
    print(json.dumps({key: value for key, value in result.items()
                      if key != "cases"}, sort_keys=True))
    raise SystemExit(0 if result["status"] ==
                     "PASS_SHARED_EDGE_PENALTY_MOTION_METHOD_FIXTURE" else 1)
