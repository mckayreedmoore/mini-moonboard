#!/usr/bin/env python3
"""Offline DAT/FRD known-answer audit for the implicit C3D10 fixture."""

from __future__ import annotations

from collections import defaultdict
from decimal import Decimal
import argparse
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import re
import sys
import tempfile

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
PARSER = HERE.parent / "explicit-c3d10-mpc-known-answer-attempt01" / "verifier.py"
CASES = ("direct", "mapped")


def fail(message: str) -> None:
    raise ValueError(message)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def strict_json(path: Path) -> dict:
    def unique_pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                fail(f"duplicate JSON key {key} in {path}")
            result[key] = value
        return result

    def reject_constant(value):
        fail(f"non-finite JSON value {value} in {path}")

    return json.loads(path.read_text(), object_pairs_hook=unique_pairs,
                      parse_constant=reject_constant)


def load_contract() -> tuple[dict, dict, object]:
    expected = strict_json(HERE / "expected.json")
    acceptance = strict_json(HERE / "acceptance.json")
    if expected.get("schema") != "implicit_c3d10_mpc_known_answer_expected/v1":
        fail("unexpected expected.json schema")
    if acceptance.get("schema") != "implicit_c3d10_mpc_known_answer_acceptance/v1":
        fail("unexpected acceptance.json schema")
    if sha(PARSER) != acceptance["parser_dependency"]["sha256"]:
        fail("pinned DAT/FRD parser SHA differs")
    spec = importlib.util.spec_from_file_location("pinned_c3d10_output_parser", PARSER)
    if spec is None or spec.loader is None:
        fail("could not load pinned parser")
    helper = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(helper)
    for name in acceptance["parser_dependency"]["functions"]:
        if not callable(getattr(helper, name, None)):
            fail(f"pinned parser function missing: {name}")
    if expected.get("case_order") != list(CASES):
        fail("case order differs")
    integration = expected["integration"]
    if (integration["increments"] != acceptance["state_coverage"]["accepted_increment_count"]
            or not math.isclose(integration["time_increment_s"] * integration["increments"],
                                integration["period_s"], rel_tol=0.0, abs_tol=1e-15)):
        fail("expected schedule and acceptance state count differ")
    return expected, acceptance, helper


def within(actual: float, reference: float, tolerance: dict) -> tuple[bool, float, float]:
    if not math.isfinite(actual) or not math.isfinite(reference):
        return False, math.inf, 0.0
    error = abs(actual - reference)
    allowed = tolerance["absolute"] + tolerance.get("relative", 0.0) * abs(reference)
    return error <= allowed, error, allowed


class Metrics:
    def __init__(self):
        self.values = defaultdict(lambda: {"samples": 0, "max_absolute_error": 0.0,
                                            "max_allowed_error": 0.0})

    def check(self, name: str, actual: float, reference: float, tolerance: dict,
              errors: list[str], where: str) -> None:
        passed, error, allowed = within(actual, reference, tolerance)
        row = self.values[name]
        row["samples"] += 1
        if math.isfinite(error):
            row["max_absolute_error"] = max(row["max_absolute_error"], error)
        if math.isfinite(allowed):
            row["max_allowed_error"] = max(row["max_allowed_error"], allowed)
        if not passed:
            errors.append(f"{where}: {name} actual={actual!r} reference={reference!r} error={error!r} allowed={allowed!r}")

    def limit_check(self, name: str, observed: float, allowed: float,
                    errors: list[str], where: str) -> None:
        row = self.values[name]
        row["samples"] += 1
        row["max_absolute_error"] = max(row["max_absolute_error"], observed)
        row["max_allowed_error"] = max(row["max_allowed_error"], allowed)
        if not math.isfinite(observed) or not math.isfinite(allowed) or observed > allowed:
            errors.append(f"{where}: {name} observed={observed!r} exceeds component-rounding bound {allowed!r}")

    def report(self) -> dict:
        return {key: value for key, value in sorted(self.values.items())}


def find_unique(records: list[dict], kind: str, set_name: str, time_s: float,
                time_tol: float, *, energy: bool = False) -> dict | None:
    found = [record for record in records
             if record.get("kind") == kind and record.get("set") == set_name
             and record.get("time") is not None
             and abs(record["time"] - time_s) <= time_tol]
    return found[0] if len(found) == 1 else None


def parse_u_tokens(text: str) -> tuple[list[dict], list[str]]:
    """Retain DAT's lexical precision for the printed homogeneous-MPC residual."""
    records, errors = [], []
    active = None
    header = re.compile(r"\b(displacements|velocities|forces)\s*\([^)]*\)\s*for set\s+(\w+)\s+and time\s+(\S+)", re.I)
    for line in text.splitlines():
        match = header.search(line)
        if match:
            word, set_name, time_token = match.groups()
            if word.lower() == "displacements":
                try:
                    active = {"kind": "U", "set": set_name.upper(),
                              "time": float(time_token.replace("D", "E").replace("d", "e")),
                              "tokens": {}}
                    if not math.isfinite(active["time"]):
                        fail("non-finite DAT displacement time")
                    records.append(active)
                except Exception as exc:
                    errors.append(f"invalid DAT displacement token header: {exc}")
                    active = None
            else:
                active = None
            continue
        if active is None:
            continue
        tokens = line.split()
        if len(tokens) == 4 and tokens[0].isdigit():
            node = int(tokens[0])
            if node in active["tokens"]:
                errors.append(f"duplicate lexical DAT displacement node {node}")
                continue
            try:
                vals = [Decimal(item.replace("D", "E").replace("d", "e")) for item in tokens[1:]]
                if any(not value.is_finite() for value in vals):
                    fail("non-finite DAT lexical displacement")
                active["tokens"][node] = vals
            except Exception as exc:
                errors.append(f"invalid lexical DAT displacement row: {exc}")
    keys = [(row["set"], row["time"]) for row in records]
    if len(keys) != len(set(keys)):
        errors.append("duplicate lexical DAT displacement header")
    return records, errors


def parse_sta(text: str) -> tuple[list[dict], list[str]]:
    """Read accepted increment rows from the native CalculiX .sta summary."""
    rows, errors = [], []
    in_table = False
    header_seen = False
    for line in text.splitlines():
        upper = line.upper()
        if all(token in upper for token in ("STEP", "INC", "ATT", "ITRS", "TOT TIME")):
            in_table = True
            header_seen = True
            continue
        if not in_table:
            continue
        tokens = line.split()
        if not tokens:
            continue
        if tokens[0].isdigit():
            if len(tokens) < 7 or not all(token.isdigit() for token in tokens[:4]):
                errors.append(f"malformed .sta accepted-increment row: {line.strip()}")
                continue
            try:
                values = [float(token.replace("D", "E").replace("d", "e")) for token in tokens[4:7]]
                if not all(math.isfinite(value) for value in values):
                    fail("non-finite .sta time")
                rows.append({"step": int(tokens[0]), "increment": int(tokens[1]),
                             "attempt": int(tokens[2]), "iterations": int(tokens[3]),
                             "total_time": values[0], "step_time": values[1],
                             "increment_time": values[2]})
            except Exception as exc:
                errors.append(f"invalid .sta time row: {exc}")
    if not header_seen:
        errors.append(".sta accepted-increment table header missing")
    return rows, errors


def lexical_row(records: list[dict], set_name: str, time_s: float,
                time_tol: float) -> dict | None:
    rows = [row for row in records if row["set"] == set_name
            and abs(row["time"] - time_s) <= time_tol]
    return rows[0] if len(rows) == 1 else None


def audit_case(case: str, folder: Path, expected: dict, acceptance: dict,
               helper: object) -> tuple[dict, list[dict]]:
    errors: list[str] = []
    metrics = Metrics()
    dat_path, frd_path = folder / "coupon.dat", folder / "coupon.frd"
    sta_path, stdout_path, stderr_path = (folder / "coupon.sta", folder / "solver.stdout",
                                         folder / "solver.stderr")
    if not dat_path.is_file() or not frd_path.is_file() or not sta_path.is_file():
        return ({"status": "FAIL", "errors": ["coupon.dat, coupon.frd, and coupon.sta are required"],
                 "accepted_state_count": 0, "metrics": {}}, [])

    if not stdout_path.is_file() or not stderr_path.is_file():
        errors.append("solver.stdout and solver.stderr capture files are required")
    else:
        stdout_text = stdout_path.read_text(errors="replace")
        stderr_text = stderr_path.read_text(errors="replace")
        if acceptance["state_coverage"]["completion_marker"] not in stdout_text:
            errors.append("normal solver completion marker is missing from stdout")
        if acceptance["state_coverage"]["stderr_must_be_empty"] and stderr_text.strip():
            errors.append("solver stderr is not empty")
        for line in stdout_text.splitlines():
            if re.search(r"(?i)(^\s*\*ERROR\b|FATAL ERROR|ERROR IN \w+)", line):
                errors.append(f"solver stdout error marker: {line.strip()[:200]}")

    item = expected["inputs"][case]
    input_path = HERE / item["path"]
    if not input_path.is_file() or sha(input_path) != item["sha256"]:
        errors.append("prepared input SHA differs from expected.json")

    dat_text = dat_path.read_text(errors="replace")
    frd_text = frd_path.read_text(errors="replace")
    sta_text = sta_path.read_text(errors="replace")
    fields, energies, dat_errors = helper.parse_dat(dat_text)
    blocks, frd_errors = helper.parse_frd(frd_text)
    token_records, token_errors = parse_u_tokens(dat_text)
    sta_rows, sta_errors = parse_sta(sta_text)
    errors.extend(f"DAT: {error}" for error in dat_errors)
    errors.extend(f"FRD: {error}" for error in frd_errors)
    errors.extend(token_errors)
    errors.extend(f"STA: {error}" for error in sta_errors)

    coverage = acceptance["state_coverage"]
    physical_ids = set(coverage["frd_physical_node_ids"])
    dat_ids = set(coverage[f"dat_{case}_node_ids"])
    state_count = coverage["accepted_increment_count"]
    time_tol = acceptance["tolerances"]["time_s"]["absolute"]
    dt = expected["integration"]["time_increment_s"]
    period = expected["integration"]["period_s"]

    if len(sta_rows) != state_count:
        errors.append(f".sta accepted row count {len(sta_rows)} differs from expected {state_count}")
    for index, row in enumerate(sta_rows, start=1):
        if (row["step"] != coverage["sta_expected_step"] or row["increment"] != index
                or row["attempt"] != coverage["sta_expected_attempt"]):
            errors.append(f".sta accepted schedule/attempt differs at row {index}: {row}")
        for field, reference in (("total_time", index * dt), ("step_time", index * dt),
                                 ("increment_time", dt)):
            metrics.check("STA_time_s", row[field], reference,
                          acceptance["tolerances"]["time_s"], errors,
                          f"{case} .sta row {index} {field}")

    disp_blocks = [block for block in blocks if block["kind"] == "DISP"]
    velo_blocks = [block for block in blocks if block["kind"] == "VELO"]
    expected_identities = [(1, increment) for increment in range(1, state_count + 1)]
    for kind, selected in (("DISP", disp_blocks), ("VELO", velo_blocks)):
        identities = [block["identity"] for block in selected]
        if len(selected) != state_count or identities != expected_identities:
            # Preserve source order for the normal case, but accept output block
            # order only if the complete unique identity set is present.
            if len(selected) != state_count or set(identities) != set(expected_identities):
                errors.append(f"FRD {kind} does not cover exactly {state_count} ordered accepted identities")
        for block in selected:
            if block["identity"] not in expected_identities:
                errors.append(f"FRD {kind} has unexpected identity {block['identity']}")

    if len(fields) != state_count * 2:
        errors.append("DAT OBSERVE U/V field count is not exactly two per accepted state")
    for kind in ("U", "V"):
        selected = [row for row in fields if row["kind"] == kind and row["set"] == "OBSERVE"]
        if len(selected) != state_count:
            errors.append(f"DAT OBSERVE {kind} state count differs from accepted increment count")
    if any(row["set"] != "OBSERVE" or row["kind"] not in ("U", "V") for row in fields):
        errors.append("DAT contains an unexpected nodal field/set for this fixture")

    energy_kinds = acceptance["state_coverage"]["dat_energy_fields"]
    for kind in energy_kinds:
        selected = [row for row in energies if row["kind"] == kind and row["set"] == "BODY"]
        if len(selected) != state_count:
            errors.append(f"DAT BODY {kind} state count differs from accepted increment count")
    if len(energies) != state_count * len(energy_kinds):
        errors.append("DAT energy output includes missing or unexpected totals")

    history: list[dict] = []
    energy_tolerances = acceptance["tolerances"]
    for increment in range(1, state_count + 1):
        identity = (1, increment)
        disp = [block for block in disp_blocks if block["identity"] == identity]
        velo = [block for block in velo_blocks if block["identity"] == identity]
        if len(disp) != 1 or len(velo) != 1:
            errors.append(f"FRD DISP/VELO missing or duplicate at {identity}")
            continue
        db, vb = disp[0], velo[0]
        t = db["time"]
        if t is None or vb["time"] is None:
            errors.append(f"FRD missing actual time at {identity}")
            continue
        metrics.check("FRD_time_s", t, increment * dt, energy_tolerances["time_s"], errors,
                      f"{case} increment {increment}")
        metrics.check("FRD_DAT_frame_time_s", vb["time"], t, energy_tolerances["time_s"], errors,
                      f"{case} increment {increment}")
        if abs(t - period) < time_tol and increment != state_count:
            errors.append("unexpected intermediate FRD state at prescribed terminal time")
        u_dat = find_unique(fields, "U", "OBSERVE", t, time_tol)
        v_dat = find_unique(fields, "V", "OBSERVE", t, time_tol)
        if u_dat is None or v_dat is None:
            errors.append(f"DAT OBSERVE U/V missing or ambiguous at {identity}")
            continue
        if set(u_dat["nodes"]) != dat_ids or set(v_dat["nodes"]) != dat_ids:
            errors.append(f"DAT OBSERVE node coverage differs at {identity}")
            continue
        if set(db["nodes"]) != physical_ids or set(vb["nodes"]) != physical_ids:
            errors.append(f"FRD connected-node coverage differs at {identity}")
            continue

        # The actual FRD state time is authoritative for the trajectory check.
        target_u = t**3 / 6.0 + t * dt**2 / 12.0
        target_v = t**2 / 2.0
        state_u, state_v = {}, {}
        for node in sorted(physical_ids):
            uvec, vvec = u_dat["nodes"][node], v_dat["nodes"][node]
            frd_u, frd_v = db["nodes"][node], vb["nodes"][node]
            if len(uvec) != 3 or len(vvec) != 3 or len(frd_u) != 3 or len(frd_v) != 3:
                errors.append(f"three-component U/V required at node {node}, {identity}")
                continue
            state_u[node], state_v[node] = uvec, vvec
            for component, reference in enumerate((target_u, 0.0, 0.0)):
                metrics.check("DAT_U_mm", uvec[component], reference, energy_tolerances["U_mm"], errors,
                              f"{case} node {node} component {component+1} increment {increment}")
                metrics.check("FRD_U_mm", frd_u[component], reference, energy_tolerances["U_mm"], errors,
                              f"{case} FRD node {node} component {component+1} increment {increment}")
                metrics.check("FRD_DAT_U_mm", frd_u[component], uvec[component], energy_tolerances["U_mm"], errors,
                              f"{case} U parity node {node} component {component+1} increment {increment}")
            for component, reference in enumerate((target_v, 0.0, 0.0)):
                metrics.check("DAT_V_mm_per_s", vvec[component], reference, energy_tolerances["V_mm_per_s"], errors,
                              f"{case} node {node} component {component+1} increment {increment}")
                metrics.check("FRD_V_mm_per_s", frd_v[component], reference, energy_tolerances["V_mm_per_s"], errors,
                              f"{case} FRD node {node} component {component+1} increment {increment}")
                metrics.check("FRD_DAT_V_mm_per_s", frd_v[component], vvec[component], energy_tolerances["V_mm_per_s"], errors,
                              f"{case} V parity node {node} component {component+1} increment {increment}")

        controller = None
        if case == "mapped":
            controller = u_dat["nodes"].get(11)
            v_controller = v_dat["nodes"].get(11)
            if controller is None or v_controller is None or len(controller) != 3 or len(v_controller) != 3:
                errors.append(f"DAT controller node 11 U/V missing at {identity}")
            else:
                metrics.check("controller_U_mm", controller[0], target_u,
                              energy_tolerances["U_mm"], errors, f"mapped q11 U increment {increment}")
                metrics.check("controller_V_mm_per_s", v_controller[0], target_v,
                              energy_tolerances["V_mm_per_s"], errors, f"mapped q11 V increment {increment}")
                for component in (1, 2):
                    metrics.check("controller_U_mm", controller[component], 0.0,
                                  energy_tolerances["U_mm"], errors, f"mapped q11 U{component+1} increment {increment}")
                    metrics.check("controller_V_mm_per_s", v_controller[component], 0.0,
                                  energy_tolerances["V_mm_per_s"], errors, f"mapped q11 V{component+1} increment {increment}")
                lexical = lexical_row(token_records, "OBSERVE", t, time_tol)
                if lexical is None or any(node not in lexical["tokens"] for node in (1, 2, 3, 4, 11)):
                    errors.append(f"mapped DAT U lexical rows missing for equation at {identity}")
                    residual_value = None
                    residual_bound = None
                else:
                    coefficients = ((1, 1), (2, 1), (3, 1), (4, 1), (11, -4))
                    residual = sum(lexical["tokens"][node][0] * coefficient
                                   for node, coefficient in coefficients)
                    bound = sum(Decimal(abs(coefficient)) *
                                Decimal(1).scaleb(lexical["tokens"][node][0].as_tuple().exponent) / 2
                                for node, coefficient in coefficients)
                    residual_value, residual_bound = float(residual), float(bound)
                    metrics.limit_check("MPC_residual_bound_mm", abs(residual_value), residual_bound,
                                        errors, f"mapped MPC increment {increment}")

        energy_values = {}
        reference_energy = {
            "ELSE": 0.0,
            "ELKE": 0.5 * expected["material"]["body_mass_tonne"] * target_v**2,
            "EMAS": expected["material"]["body_mass_tonne"],
            "EVOL": expected["mesh"]["volume_mm3"],
        }
        tolerance_key = {"ELSE": "ELSE_Nmm", "ELKE": "ELKE_Nmm",
                         "EMAS": "EMAS_tonne", "EVOL": "EVOL_mm3"}
        energy_ok = True
        for kind in energy_kinds:
            record = find_unique(energies, kind, "BODY", t, time_tol)
            if record is None:
                errors.append(f"DAT BODY {kind} missing or ambiguous at {identity}")
                energy_ok = False
                continue
            energy_values[kind] = record["value"]
            metrics.check(tolerance_key[kind], record["value"], reference_energy[kind],
                          energy_tolerances[tolerance_key[kind]], errors,
                          f"{case} {kind} increment {increment}")
        history.append({"identity": identity, "time_s": t, "physical_U": state_u,
                        "physical_V": state_v, "controller_U": controller,
                        "controller_V": (v_dat["nodes"].get(11) if case == "mapped" else None),
                        "energies": energy_values, "energy_records_complete": energy_ok})

    case_pass = not errors and len(history) == state_count
    first = history[0]["time_s"] if history else None
    last = history[-1]["time_s"] if history else None
    return ({"status": "PASS" if case_pass else "FAIL", "errors": errors,
             "accepted_state_count": len(history), "first_time_s": first,
             "last_time_s": last, "metrics": metrics.report()}, history)


def audit(audit_dir: Path) -> dict:
    expected, acceptance, helper = load_contract()
    result_cases, histories = {}, {}
    for case in CASES:
        result_cases[case], histories[case] = audit_case(
            case, audit_dir / case, expected, acceptance, helper)

    cross_errors = []
    cross_metrics = Metrics()
    if len(histories["direct"]) != acceptance["state_coverage"]["accepted_increment_count"] or len(histories["mapped"]) != acceptance["state_coverage"]["accepted_increment_count"]:
        cross_errors.append("direct and mapped outputs do not both contain the accepted state count")
    else:
        tolerances = acceptance["tolerances"]
        physical_ids = acceptance["state_coverage"]["frd_physical_node_ids"]
        for direct, mapped in zip(histories["direct"], histories["mapped"]):
            inc = direct["identity"][1]
            cross_metrics.check("direct_mapped_time_s", mapped["time_s"], direct["time_s"],
                                tolerances["time_s"], cross_errors, f"increment {inc}")
            for node in physical_ids:
                for component in range(3):
                    cross_metrics.check("direct_mapped_U_mm",
                                        mapped["physical_U"].get(node, [math.nan]*3)[component],
                                        direct["physical_U"].get(node, [math.nan]*3)[component],
                                        tolerances["U_mm"], cross_errors,
                                        f"increment {inc}, node {node}, U{component+1}")
                    cross_metrics.check("direct_mapped_V_mm_per_s",
                                        mapped["physical_V"].get(node, [math.nan]*3)[component],
                                        direct["physical_V"].get(node, [math.nan]*3)[component],
                                        tolerances["V_mm_per_s"], cross_errors,
                                        f"increment {inc}, node {node}, V{component+1}")
    cross_pass = not cross_errors and len(histories["direct"]) == len(histories["mapped"])
    passed = cross_pass and all(result_cases[case]["status"] == "PASS" for case in CASES)
    return {
        "schema": "implicit_c3d10_mpc_known_answer_verifier/v1",
        "status": "PASS_IMPLICIT_C3D10_MPC_KNOWN_ANSWER" if passed else "FAIL",
        "audit_directory": str(audit_dir),
        "parser_sha256": sha(PARSER),
        "cases": result_cases,
        "direct_mapped_coordinate_invariance": {
            "status": "PASS" if cross_pass else "FAIL",
            "errors": cross_errors,
            "metrics": cross_metrics.report(),
        },
        "mechanical_acceptance": False,
        "work_energy_acceptance": False,
        "joint_acceptance": False,
        "release": False,
    }


def synthetic_capture(case: str, *, missing_last_velocity: bool = False,
                      wrong_motion: bool = False) -> tuple[str, str]:
    physical = range(1, 11)
    observed = list(physical) + ([11] if case == "mapped" else [])
    dt, period = 0.001, 0.1
    dat_lines, frd_lines = [], []
    for increment in range(1, 101):
        t = increment * dt
        u = t**3 / 6.0 + t * dt**2 / 12.0
        v = t**2 / 2.0
        displacement = {node: u for node in observed}
        velocity = {node: v for node in observed}
        if wrong_motion and case == "mapped" and increment == 50:
            displacement[7] += 0.001
        for label, values in (("displacements", displacement), ("velocities", velocity)):
            dat_lines.append(f"{label} (vx,vy,vz) for set OBSERVE and time {t:.12E}")
            dat_lines.extend(f"{node} {value:.12E} 0.000000E+00 0.000000E+00"
                             for node, value in values.items())
            dat_lines.append("")
        elke = 0.5 * (v**2)
        for label, value in (("internal energy", 0.0), ("kinetic energy", elke),
                             ("mass", 1.0), ("volume", 1.0/6.0)):
            dat_lines.extend((f"total {label} for set BODY and time {t:.12E}",
                              f"{value:.12E}", ""))

        frd_lines.extend((f"    1PSTEP                         1{increment:12d}           1",
                          f" 100CL  {increment+1} {t:.12E} 10 0 1 1 1"))
        for kind, value in (("DISP", u), ("VELO", v)):
            if missing_last_velocity and increment == 100 and kind == "VELO":
                continue
            frd_lines.extend((f" -4 {kind} 4 1", " -5 X1", " -5 X2", " -5 X3"))
            for node in physical:
                frd_lines.append(" -1" + f"{node:10d}" +
                                 f"{value:12.5E}{0.0:12.5E}{0.0:12.5E}")
            frd_lines.append(" -3")
    return "\n".join(dat_lines) + "\n", "\n".join(frd_lines) + "\n"


def synthetic_sta() -> str:
    lines = ["SUMMARY OF JOB INFORMATION",
             "  STEP      INC     ATT  ITRS     TOT TIME     STEP TIME      INC TIME"]
    for increment in range(1, 101):
        time_s = increment * 0.001
        lines.append(f"     1 {increment:10d}     1     2 {time_s:.8E} {time_s:.8E} {0.001:.8E}")
    return "\n".join(lines) + "\n"


def write_synthetic_case(folder: Path, case: str, *, missing_last_velocity: bool = False,
                         wrong_motion: bool = False) -> None:
    folder.mkdir(parents=True, exist_ok=True)
    dat, frd = synthetic_capture(case, missing_last_velocity=missing_last_velocity,
                                 wrong_motion=wrong_motion)
    (folder / "coupon.dat").write_text(dat)
    (folder / "coupon.frd").write_text(frd)
    (folder / "coupon.sta").write_text(synthetic_sta())
    (folder / "solver.stdout").write_text(" Job finished\n")
    (folder / "solver.stderr").write_text("")


def self_test() -> dict:
    expected, acceptance, helper = load_contract()
    controls = {}
    with tempfile.TemporaryDirectory(prefix="implicit-c3d10-preflight-") as temp:
        root = Path(temp)
        for case in CASES:
            write_synthetic_case(root / case, case)
        normal = audit(root)
        controls["synthetic_normal"] = normal["status"]
        if normal["status"] != "PASS_IMPLICIT_C3D10_MPC_KNOWN_ANSWER":
            fail("synthetic normal capture was rejected: " + json.dumps(normal["cases"], sort_keys=True))

        folder = root / "mapped"
        write_synthetic_case(folder, "mapped", missing_last_velocity=True)
        missing = audit(root)
        controls["missing_state_rejected"] = missing["status"] == "FAIL"
        if not controls["missing_state_rejected"]:
            fail("synthetic missing-state capture was accepted")

        write_synthetic_case(folder, "mapped", wrong_motion=True)
        wrong = audit(root)
        controls["wrong_motion_rejected"] = wrong["status"] == "FAIL"
        if not controls["wrong_motion_rejected"]:
            fail("synthetic wrong-motion capture was accepted")
    return {"schema": "implicit_c3d10_mpc_known_answer_self_test/v1",
            "status": "PASS_SYNTHETIC_CONTROLS", "controls": controls,
            "native_run_performed": False}


def main() -> int:
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--audit-dir", type=Path, help="directory containing direct/ and mapped/ output folders")
    mode.add_argument("--self-test", action="store_true", help="run positive and negative synthetic controls")
    args = parser.parse_args()
    result = self_test() if args.self_test else audit(args.audit_dir.resolve())
    print(json.dumps(result, indent=2, sort_keys=True, allow_nan=False))
    return 0 if result["status"] != "FAIL" else 1


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(json.dumps({"status": "FAIL_CLOSED", "error": str(exc)}, sort_keys=True), file=sys.stderr)
        raise SystemExit(2)
