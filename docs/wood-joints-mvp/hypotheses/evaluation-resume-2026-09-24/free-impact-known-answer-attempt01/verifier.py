#!/usr/bin/env python3
"""Offline verifier for the two-case free-coordinate C3D10 impact fixture."""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime
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
CASES = ("baseline", "trace")


def fail(message: str) -> None:
    raise ValueError(message)


def require(ok: bool, message: str) -> None:
    if not ok:
        fail(message)


def sha(path: Path) -> str:
    require(path.is_file(), f"Required file is missing: {path}")
    return hashlib.sha256(path.read_bytes()).hexdigest()


def strict_json(path: Path) -> dict:
    def unique_pairs(items):
        result = {}
        for key, value in items:
            require(key not in result, f"Duplicate JSON key {key} in {path}")
            result[key] = value
        return result

    def parse_float(token):
        value = float(token)
        require(math.isfinite(value), f"Nonfinite JSON number in {path}")
        return value

    def reject_constant(token):
        fail(f"Invalid JSON constant {token} in {path}")

    try:
        value = json.loads(path.read_text(), object_pairs_hook=unique_pairs,
                           parse_float=parse_float, parse_constant=reject_constant)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        fail(f"Invalid JSON in {path}: {exc}")
    require(isinstance(value, dict), f"JSON object required in {path}")
    return value


def load_module(name: str, path: Path):
    require(path.is_file(), f"Pinned helper missing: {path}")
    spec = importlib.util.spec_from_file_location(name, path)
    require(spec is not None and spec.loader is not None, f"Cannot load pinned helper: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def repo_root() -> Path:
    for candidate in HERE.parents:
        if (candidate / "AGENTS.md").is_file():
            return candidate
    fail("Could not locate repository AGENTS.md")


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
        self.errors: list[str] = []

    def check(self, name: str, actual: float, reference: float, tolerance: dict,
              where: str) -> None:
        passed, error, allowed = within(actual, reference, tolerance)
        row = self.values[name]
        row["samples"] += 1
        if math.isfinite(error):
            row["max_absolute_error"] = max(row["max_absolute_error"], error)
        if math.isfinite(allowed):
            row["max_allowed_error"] = max(row["max_allowed_error"], allowed)
        if not passed and len(self.errors) < 100:
            self.errors.append(
                f"{where}: {name} actual={actual!r} reference={reference!r} "
                f"error={error!r} allowed={allowed!r}")

    def limit(self, name: str, observed: float, allowed: float, where: str) -> None:
        row = self.values[name]
        row["samples"] += 1
        if math.isfinite(observed):
            row["max_absolute_error"] = max(row["max_absolute_error"], observed)
        if math.isfinite(allowed):
            row["max_allowed_error"] = max(row["max_allowed_error"], allowed)
        if (not math.isfinite(observed) or not math.isfinite(allowed) or observed > allowed) \
                and len(self.errors) < 100:
            self.errors.append(f"{where}: {name} {observed!r} exceeds {allowed!r}")

    def report(self) -> dict:
        return {name: values for name, values in sorted(self.values.items())}


def near(actual: float, reference: float, tol: dict, label: str) -> None:
    ok, error, bound = within(actual, reference, tol)
    require(ok, f"{label}: actual={actual:.17g} expected={reference:.17g} "
            f"error={error:.6g} bound={bound:.6g}")


def load_contract() -> tuple[dict, dict, dict, dict]:
    expected = strict_json(HERE / "expected.json")
    acceptance = strict_json(HERE / "acceptance.json")
    require(expected.get("schema") == "ccx223_free_impact_expected/v1",
            "Unexpected expected.json schema")
    require(acceptance.get("schema") == "ccx223_free_impact_acceptance/v1",
            "Unexpected acceptance.json schema")
    require(expected.get("case_order") == list(CASES) and
            acceptance.get("case_order") == list(CASES), "Case order differs")
    require(expected.get("limits", {}).get("native_execution") is False and
            expected.get("limits", {}).get("model_acceptance") is False and
            expected.get("limits", {}).get("joint_acceptance") is False,
            "Expected contract crosses its method-fixture authority boundary")
    require(acceptance.get("acceptance_boundary") == {
        "method_fixture_only": True, "mechanical_acceptance": False,
        "work_energy_acceptance": False, "joint_acceptance": False, "release": False},
        "Acceptance flags must remain method-fixture-only")

    procedure = expected["procedure"]
    require(procedure["nmethod"] == 4 and procedure["alpha"] == 0.0 and
            procedure["beta"] == 0.25 and procedure["gamma"] == 0.5 and
            procedure["accepted_state_count"] == 70 and
            procedure["input_increment_count"] == 70 and
            procedure["time_increment_s"] == 0.0001 and
            procedure["total_time_s"] == 0.007 and
            procedure["direct_fixed_increment"] is True and
            procedure["damping"] is False and procedure["external_loads"] == [] and
            procedure["amplitudes"] == [], "Procedure differs from the frozen impact method")
    contact = expected["contact"]
    model = acceptance["model"]
    for observed, wanted, label in (
        (contact["normal_slope_N_per_mm3"], model["normal_penalty_K_N_per_mm3"], "K"),
        (contact["aggregate_linear_stiffness_N_per_mm"], model["scalar_stiffness_N_per_mm"], "k"),
        (contact["initial_face_area_mm2"], model["interface_area_mm2"], "contact area"),
        (expected["material_and_mass"]["upper_mass_tonne"], model["mass_tonne_each_body"], "upper mass"),
        (expected["material_and_mass"]["lower_mass_tonne"], model["mass_tonne_each_body"], "lower mass"),
        (expected["material_and_mass"]["upper_volume_mm3"], model["volume_mm3_each_body"], "upper volume"),
        (expected["material_and_mass"]["lower_volume_mm3"], model["volume_mm3_each_body"], "lower volume"),
    ):
        require(observed == wanted, f"Prepared {label} differs from acceptance")
    require(contact["friction_card"] is False and
            contact["signed_gap"] == "u3_upper - u3_lower; negative is compression, positive is open",
            "Contact law or gap convention changed")
    require(procedure["initial_conditions"]["velocity_u3_mm_per_s"] ==
            model["initial_upper_and_q_velocity_mm_per_s"] and
            procedure["initial_conditions"]["displacement_u3_mm"] == model["initial_gap_mm"],
            "Initial velocity/displacement differs from the scalar oracle")

    inputs = expected["inputs"]
    require(set(inputs) == set(CASES), "Expected input cases differ")
    require(inputs["baseline"] == inputs["trace"],
            "Baseline and trace cases must use byte-identical input paths and hashes")
    require(inputs["baseline"]["path"] == expected["input"]["path"] and
            inputs["baseline"]["sha256"] == expected["input"]["sha256"],
            "Shared input entry differs from case entries")
    deck = HERE / expected["input"]["path"]
    require(sha(deck) == expected["input"]["sha256"], "Prepared input hash differs")

    geometry = expected["geometry"]
    groups = {
        "upper": set(geometry["upper_nodes"]),
        "lower": set(geometry["lower_nodes"]),
        "physical": set(geometry["physical_nodes"]),
        "all": set(geometry["all_output_nodes"]),
        "controller": {geometry["controller_node"]},
    }
    require(len(groups["upper"]) == 27 and len(groups["lower"]) == 27 and
            len(groups["physical"]) == 54 and len(groups["all"]) == 55 and
            groups["upper"].isdisjoint(groups["lower"]) and
            groups["upper"] | groups["lower"] == groups["physical"] and
            groups["all"] == groups["physical"] | groups["controller"] and
            groups["controller"] == {8001}, "Expected node inventory is inconsistent")
    nsets = geometry["nsets"]
    require(nsets["N_UPPER"] == sorted(groups["upper"]) and
            nsets["N_LOWER"] == sorted(groups["lower"]) and
            nsets["N_PHYSICAL"] == sorted(groups["physical"]) and
            nsets["N_ALL"] == sorted(groups["all"]) and
            nsets["Q_NODE"] == [8001], "Expected NSETs differ from output coverage contract")
    require(expected["outputs"]["dat"]["node_set"] == acceptance["output_contract"]["dat_node_set"] and
            expected["outputs"]["frd"]["node_set"] == acceptance["output_contract"]["frd_physical_node_set"] and
            expected["outputs"]["contact_print_pair"]["fields"] == ["CFN"] and
            expected["outputs"]["contact_print_total"]["fields"] == ["CELS"],
            "Prepared output requests differ from frozen acceptance")
    require(acceptance["trace_contract"]["release_requires_positive_gap_old_set_trial"] is False and
            acceptance["trace_contract"]["positive_gap_trial_max_iteration"] == 1,
            "Release/positive-gap trace gates differ from source-bounded contract")

    # Independently reproduce the pinned scalar Newmark recurrence.
    ref_path = HERE / expected["reference"]["path"]
    ref = strict_json(ref_path)
    ref_sha = acceptance["parser_dependencies"]["scalar_reference"]["sha256"]
    require(sha(ref_path) == ref_sha == expected["reference"]["sha256"] ==
            expected["dependencies"]["reference_sha256"], "Scalar reference SHA differs")
    require(ref["schema"] == "proposed_scalar_free_contact_reference/v1" and
            ref["increments"] == 70 and len(ref["states"]) == 70 and
            ref["mass_tonne"] == 1.0 and ref["spring_stiffness_N_mm"] == 400000.0 and
            ref["time_increment_s"] == 0.0001 and ref["native_execution"] is False,
            "Scalar reference contract differs")
    m = model["mass_tonne_each_body"]
    k = model["scalar_stiffness_N_per_mm"]
    dt = acceptance["states"]["time_increment_s"]
    u, v, a = 0.0, model["initial_upper_and_q_velocity_mm_per_s"], 0.0
    reproduced = []
    for increment in range(1, 71):
        predictor = u + dt * v + dt * dt * a / 4.0
        if predictor < 0.0:
            next_u = predictor / (1.0 + k * dt * dt / (4.0 * m))
            next_a = -k * next_u / m
        else:
            next_u, next_a = predictor, 0.0
        next_v = v + dt * (a + next_a) / 2.0
        contact_energy = 0.5 * k * min(next_u, 0.0) ** 2
        kinetic_energy = 0.5 * m * next_v ** 2
        reproduced.append({"increment": increment, "time_s": increment * dt,
                           "displacement_mm": next_u, "velocity_mm_s": next_v,
                           "acceleration_mm_s2": next_a,
                           "contact_energy_Nmm": contact_energy,
                           "kinetic_energy_Nmm": kinetic_energy,
                           "total_energy_Nmm": kinetic_energy + contact_energy})
        u, v, a = next_u, next_v, next_a
    for observed, calculated in zip(ref["states"], reproduced):
        require(observed["increment"] == calculated["increment"],
                "Scalar reference increment order differs")
        for key, value in calculated.items():
            if key == "increment":
                continue
            require(math.isclose(observed[key], value, rel_tol=1e-12, abs_tol=1e-15),
                    f"Pinned scalar reference fails recurrence at {calculated['increment']} {key}")
    ref_states = ref["states"]
    event_checks = expected["event_checks"]
    require(min(ref_states, key=lambda row: row["displacement_mm"])["increment"] ==
            event_checks["max_compression_increment"] == 25 and
            ref_states[49]["increment"] == event_checks["first_open_increment"] == 50 and
            ref_states[69]["increment"] == event_checks["last_increment"] == 70 and
            ref_states[49]["displacement_mm"] > 0.0 and
            all(ref_states[i]["displacement_mm"] < 0.0 for i in range(49)),
            "Compression/release/reopening state boundaries differ")

    repo = repo_root()
    deps = acceptance["parser_dependencies"]
    helper_paths = {}
    for key in ("dat_frd", "sta", "trace_and_cvg", "pair_resultant", "trace_format"):
        path = (HERE / deps[key]["path"]).resolve()
        require(sha(path) == deps[key]["sha256"], f"Pinned parser dependency changed: {key}")
        helper_paths[key] = path
    modules = {
        "dat_frd": load_module("free_impact_dat_frd_parser", helper_paths["dat_frd"]),
        "sta": load_module("free_impact_sta_parser", helper_paths["sta"]),
        "trace": load_module("free_impact_trace_parser", helper_paths["trace_and_cvg"]),
        "pair": load_module("free_impact_pair_parser", helper_paths["pair_resultant"]),
    }
    for function in deps["dat_frd"]["functions"]:
        require(callable(getattr(modules["dat_frd"], function, None)),
                f"DAT/FRD helper missing {function}")
    for function in deps["trace_and_cvg"]["functions"]:
        require(callable(getattr(modules["trace"], function, None)),
                f"Trace helper missing {function}")
    require(callable(getattr(modules["pair"], deps["pair_resultant"]["function"], None)),
            "Pair-resultant parser function missing")
    trace_format = strict_json(helper_paths["trace_format"])
    require(trace_format.get("schema") == "ccx223_contact_point_trace_format/v1" and
            set(trace_format.get("tags", {})) ==
            {"CCXPT_MAP", "CCXPT_UNMAPPED", "CCXPT_TRIAL"},
            "Pinned point-trace format schema differs")

    # Recheck the source archive and source members whose behavior is audited.
    pins = expected["pinned_sources"]
    archive_path = (HERE / pins["source_archive_path"]).resolve()
    manual_path = (HERE / pins["manual_pdf_path"]).resolve()
    require(sha(archive_path) == pins["source_archive_sha256"] and
            sha(manual_path) == pins["manual_pdf_sha256"],
            "Pinned 2.23 source archive or manual differs")
    import tarfile
    with tarfile.open(archive_path, "r:bz2") as archive:
        by_name = {member.name.removeprefix("./"): member for member in archive.getmembers()
                   if member.isfile()}
        for name, item in pins["source_files"].items():
            member_name = "CalculiX/ccx_2.23/src/" + name
            require(member_name in by_name, f"Pinned source member is absent: {name}")
            stream = archive.extractfile(by_name[member_name])
            require(stream is not None and
                    hashlib.sha256(stream.read()).hexdigest() == item["sha256"],
                    f"Pinned source member hash differs: {name}")
    design_path = HERE / "fixture-design.md"
    geometry_source = (HERE / expected["input"]["geometry_source_path"]).resolve()
    require(sha(design_path) == expected["dependencies"]["design_sha256"] and
            sha(geometry_source) == expected["input"]["geometry_source_sha256"],
            "Pinned design or source geometry changed")
    return expected, acceptance, ref, {**modules, "trace_format": trace_format,
                                      "helper_paths": helper_paths,
                                      "reference_states": reproduced, "repo": repo}


def parse_conversion_events(stdout: bytes, trace_helper, max_increment: int = 70):
    conversions, contacts = [], []
    try:
        lines = stdout.decode("ascii").splitlines()
    except UnicodeDecodeError as exc:
        fail(f"solver.stdout is not strict ASCII: {exc}")
    for line_number, line in enumerate(lines, 1):
        if "CCX223_ATTEMPT04_" not in line:
            continue
        record = trace_helper.strict_json_bytes(
            line.strip().encode("ascii"), f"attempt event line {line_number}")
        event = record.get("event")
        wanted = (trace_helper.CONV_FIELDS if event == "CCX223_ATTEMPT04_CONVERGENCE"
                  else trace_helper.CONTACT_FIELDS
                  if event == "CCX223_ATTEMPT04_CONTACT" else None)
        require(wanted is not None and set(record) == wanted,
                f"Unexpected inherited event schema at stdout line {line_number}")
        if event == "CCX223_ATTEMPT04_CONVERGENCE":
            conversions.append(record)
        else:
            contacts.append(record)
    require(conversions, "Trace stdout has no inherited convergence events")
    for row in conversions:
        for name in trace_helper.CONV_FIELDS - {"event", "step", "increment", "attempt", "iteration"}:
            require(type(row[name]) is int and row[name] in (0, 1),
                    f"Invalid convergence flag {name}")
        require(all(type(row[name]) is int and row[name] >= 0
                    for name in ("step", "increment", "attempt", "iteration")) and
                row["step"] == 1 and row["attempt"] == 1 and
                1 <= row["increment"] <= max_increment and row["iteration"] >= 1,
                "Convergence event has invalid step/increment/attempt/iteration")
        require(row["final_convergence_ok"] == int(
            row["iconvergence"] == 1 and row["idivergence"] == 0),
            "Final-convergence flag contradicts native convergence fields")
    for row in contacts:
        require(row["step"] == 1 and row["attempt"] == 1 and
                1 <= row["increment"] <= max_increment and row["iteration"] >= 1 and
                row["contact_old"] >= 0 and row["contact_new"] >= 0 and
                row["contact_change_flag"] in (0, 1) and
                math.isfinite(float(row["delcon"])),
                "Contact-count event has invalid identity or values")
    return conversions, contacts


def accepted_schedule(case: str, stdout: bytes, sta_rows: list[dict],
                      cvg: dict, trace_helper) -> tuple[dict, dict]:
    expected_keys = {(1, increment, 1) for increment in range(1, 71)}
    sta_by_key = {}
    for row in sta_rows:
        key = (row["step"], row["increment"], row["attempt"])
        require(key not in sta_by_key, f"Duplicate STA identity {key}")
        sta_by_key[key] = row
    require(set(sta_by_key) == expected_keys,
            "STA does not contain exactly the 70 accepted step/increment/attempt identities")
    dt = 0.0001
    time_tol = {"absolute": 1e-10}
    for inc in range(1, 71):
        row = sta_by_key[(1, inc, 1)]
        require(row["iterations"] >= 2, f"STA has fewer than two iterations at increment {inc}")
        for field in ("total_time", "step_time"):
            near(row[field], inc * dt, time_tol, f"STA {field} increment {inc}")
        near(row["increment_time"], dt, time_tol, f"STA increment_time {inc}")

    require(cvg, "CVG has no iteration records")
    for key, count in cvg.items():
        step, inc, attempt, iteration = key
        require(step == 1 and 1 <= inc <= 70 and attempt == 1 and iteration >= 1,
                f"CVG contains unplanned identity {key}")
    final_keys = {}
    for state_key, row in sta_by_key.items():
        key = (*state_key, row["iterations"])
        require(key in cvg, f"CVG lacks the STA final iteration identity {key}")
        final_keys[state_key] = key
    if case == "baseline":
        require(b"CCXPT_" not in stdout and b"CCX223_ATTEMPT04_" not in stdout,
                "Unmodified baseline stdout unexpectedly contains diagnostic patch records")
        return sta_by_key, final_keys

    conversions, contacts = parse_conversion_events(stdout, trace_helper)
    event_by_key = {}
    for row in conversions:
        key = (row["step"], row["increment"], row["attempt"], row["iteration"])
        require(key not in event_by_key, f"Duplicate convergence event {key}")
        event_by_key[key] = row
    require(set(event_by_key) == set(cvg),
            "Trace convergence-event identities do not exactly match CVG")
    for state_key, final_key in final_keys.items():
        row = event_by_key[final_key]
        require(row["final_convergence_ok"] == 1 and row["mechanical_applicable"] == 1 and
                row["mechanical_gate_ok"] == 1 and row["contact_change_gate_clear"] == 1,
                f"Accepted final convergence gate failed at {final_key}")
    return sta_by_key, final_keys


def matching(records: list[dict], *, kind: str, set_name: str, time: float,
             tolerance: float) -> dict:
    found = [row for row in records if row.get("kind") == kind and
             row.get("set") == set_name and row.get("time") is not None and
             abs(row["time"] - time) <= tolerance]
    require(len(found) == 1,
            f"Expected one {kind}/{set_name} DAT record at {time:.12g}s; got {len(found)}")
    return found[0]


def accepted_energy(energies: list[dict], kind: str, set_name: str,
                    time: float, time_tolerance: float) -> float:
    found = [row for row in energies if row["kind"] == kind and
             row["set"] == set_name and row["time"] is not None and
             abs(row["time"] - time) <= time_tolerance]
    require(len(found) == 1,
            f"Expected one {kind}/{set_name} energy at {time:.12g}s; got {len(found)}")
    return found[0]["value"]


def parse_cels(dat_text: str, trace_helper) -> dict[float, float]:
    return trace_helper.parse_dat_cels(dat_text.encode("ascii"))


def rows_at_time(records: list[dict], time: float, tolerance: float) -> list[dict]:
    return [row for row in records if row["time"] is not None and
            abs(row["time"] - time) <= tolerance]


def check_pair_records(records: list[dict], expected: dict, acceptance: dict,
                       reference_states: list[dict], metrics: Metrics,
                       context: str) -> list[dict]:
    out = acceptance["output_contract"]
    require(len(records) == 70, f"{context}: expected 70 CFN pair records, got {len(records)}")
    tol_time = acceptance["tolerances"]["time_s"]["absolute"]
    contact = expected["contact"]
    k = acceptance["model"]["scalar_stiffness_N_per_mm"]
    x0, y0, _z0 = expected["geometry"]["controller_coordinate_mm"]
    selected = []
    for index, state in enumerate(reference_states, 1):
        t = state["time_s"]
        found = [row for row in records if row["slave"] == out["pair_slave_set"] and
                 row["master"] == out["pair_master_set"] and
                 row["quantity"] == out["pair_quantity"] and
                 abs(row["time"] - t) <= tol_time]
        require(len(found) == 1,
                f"{context}: CFN pair identity missing/duplicate at accepted increment {index}")
        row = found[0]
        force_z = -k * min(state["displacement_mm"], 0.0)
        force = [0.0, 0.0, force_z]
        moment = [y0 * force_z, -x0 * force_z, 0.0]
        for j, value in enumerate(force):
            metrics.check("CFN_component_N", row["force_N"][j], value,
                          acceptance["tolerances"]["CFN_component_N"],
                          f"{context} inc {index} CFN F{j+1}")
        for j, value in enumerate(moment):
            metrics.check("CFN_origin_moment_component_Nmm", row["moment_N_mm"][j], value,
                          acceptance["tolerances"]["CFN_origin_moment_component_Nmm"],
                          f"{context} inc {index} CFN M{j+1}")
        selected.append({"time_s": row["time"], "force_N": row["force_N"],
                         "moment_N_mm": row["moment_N_mm"],
                         "expected_force_N": force, "expected_moment_N_mm": moment})
    return selected


def audit_capture(case: str, capture: dict[str, bytes], expected: dict,
                  acceptance: dict, modules: dict, reference_states: list[dict]) -> dict:
    require(case in CASES, f"Unknown case {case}")
    for filename in ("solver.stdout", "solver.stderr", "coupon.dat", "coupon.frd",
                     "coupon.sta", "coupon.cvg"):
        require(filename in capture, f"{case}: missing {filename}")
    stdout, stderr = capture["solver.stdout"], capture["solver.stderr"]
    require(b" Job finished" in stdout, f"{case}: normal solver completion marker missing")
    require(not stderr.strip(), f"{case}: stderr is not empty")
    stdout_text = stdout.decode("ascii")
    for line in stdout_text.splitlines():
        require(not re.search(r"(?i)(^\s*\*ERROR\b|FATAL ERROR|ERROR IN \w+)", line),
                f"{case}: solver error marker: {line[:200]}")

    base = modules["dat_frd"]
    sta_helper = modules["sta"]
    trace_helper = modules["trace"]
    pair_helper = modules["pair"]
    dat_text = capture["coupon.dat"].decode("ascii")
    frd_text = capture["coupon.frd"].decode("ascii")
    sta_text = capture["coupon.sta"].decode("ascii")
    cvg_text = capture["coupon.cvg"].decode("ascii")
    fields, energies, dat_errors = base.parse_dat(dat_text)
    frd_blocks, frd_errors = base.parse_frd(frd_text)
    sta_rows, sta_errors = sta_helper.parse_sta(sta_text)
    cvg = trace_helper.parse_cvg(capture["coupon.cvg"])
    require(not dat_errors, f"{case}: DAT parse errors: {dat_errors[:8]}")
    require(not frd_errors, f"{case}: FRD parse errors: {frd_errors[:8]}")
    require(not sta_errors, f"{case}: STA parse errors: {sta_errors[:8]}")
    require(len(sta_rows) == 70, f"{case}: STA accepted-state count is {len(sta_rows)}, expected 70")
    sta_by_key, final_keys = accepted_schedule(case, stdout, sta_rows, cvg, trace_helper)

    trace_rows = None
    trace_cov = None
    trace_summary = {"map_rows": 0, "trial_rows": 0, "unmapped_rows": 0,
                     "release_positive_old_set_trial_rows": 0}
    if case == "trace":
        parsed = trace_helper.parse_trace(stdout, modules["trace_format"])
        require(not parsed["CCXPT_UNMAPPED"],
                f"Trace has {len(parsed['CCXPT_UNMAPPED'])} unmapped contact points")
        groups, trace_cov = trace_helper.trial_coverage(parsed, cvg)
        trace_rows = {"parsed": parsed, "groups": groups}
        trace_summary.update({"map_rows": len(parsed["CCXPT_MAP"]),
                              "trial_rows": len(parsed["CCXPT_TRIAL"]),
                              "unmapped_rows": len(parsed["CCXPT_UNMAPPED"]),
                              "trial_coverage": trace_cov})
        validate_map_rows(parsed["CCXPT_MAP"], expected, acceptance, trace_summary)
    else:
        require(b"CCXPT_" not in stdout and b"CCX223_ATTEMPT04_" not in stdout,
                "Baseline binary unexpectedly emitted diagnostic patch records")

    geometry = expected["geometry"]
    upper = set(geometry["upper_nodes"])
    lower = set(geometry["lower_nodes"])
    physical = set(geometry["physical_nodes"])
    all_nodes = set(geometry["all_output_nodes"])
    q_node = geometry["controller_node"]
    out = acceptance["output_contract"]
    tol = acceptance["tolerances"]
    time_tol = tol["time_s"]["absolute"]
    reference_by_increment = {row["increment"]: row for row in reference_states}
    frd_by_key = defaultdict(dict)
    for block in frd_blocks:
        identity = tuple(block["identity"]) if block["identity"] is not None else None
        if identity is not None:
            require(block["kind"] not in frd_by_key[identity],
                    f"{case}: duplicate FRD {block['kind']} block at {identity}")
            frd_by_key[identity][block["kind"]] = block

    cels = parse_cels(dat_text, trace_helper)
    require(len(cels) == 70, f"{case}: CELS output has {len(cels)} states, expected 70")
    pair_records = pair_helper.parse_pairs(dat_text)
    metrics = Metrics()
    pair_summary = check_pair_records(pair_records, expected, acceptance,
                                      reference_states, metrics, case)
    history = []
    for increment in range(1, 71):
        state_key = (1, increment, 1)
        sta = sta_by_key[state_key]
        reference = reference_by_increment[increment]
        time_s = sta["total_time"]
        metrics.check("STA_time_s", time_s, reference["time_s"], tol["time_s"],
                      f"{case} STA increment {increment}")
        final_key = final_keys[state_key]
        final_contact_count = cvg[final_key]
        expected_active = reference["displacement_mm"] < 0.0
        if expected_active:
            require(final_contact_count > 0,
                    f"{case}: compressed accepted increment {increment} has no contact springs")
        else:
            require(final_contact_count == 0,
                    f"{case}: open accepted increment {increment} retains active contact springs")
        u_dat = matching(fields, kind="U", set_name=out["dat_node_set"],
                         time=time_s, tolerance=time_tol)
        v_dat = matching(fields, kind="V", set_name=out["dat_node_set"],
                         time=time_s, tolerance=time_tol)
        require(set(u_dat["nodes"]) == all_nodes and set(v_dat["nodes"]) == all_nodes,
                f"{case}: DAT N_ALL coverage differs at increment {increment}")
        require(q_node in u_dat["nodes"] and q_node in v_dat["nodes"],
                f"{case}: DAT is missing free controller node {q_node}")

        frd_key = (1, increment)
        require(frd_key in frd_by_key and "DISP" in frd_by_key[frd_key] and
                "VELO" in frd_by_key[frd_key],
                f"{case}: FRD lacks accepted DISP/VELO identity {frd_key}")
        disp = frd_by_key[frd_key]["DISP"]
        velo = frd_by_key[frd_key]["VELO"]
        require(disp["time"] is not None and velo["time"] is not None,
                f"{case}: FRD lacks actual time at accepted increment {increment}")
        metrics.check("FRD_STA_time_s", disp["time"], time_s, tol["time_s"],
                      f"{case} FRD DISP increment {increment}")
        metrics.check("FRD_VELO_STA_time_s", velo["time"], time_s, tol["time_s"],
                      f"{case} FRD VELO increment {increment}")
        require(set(disp["nodes"]) == physical and set(velo["nodes"]) == physical,
                f"{case}: FRD physical node coverage differs at increment {increment}")
        require(q_node not in disp["nodes"] and q_node not in velo["nodes"],
                f"{case}: FRD unexpectedly reports disconnected controller {q_node}")

        q = reference["displacement_mm"]
        vq = reference["velocity_mm_s"]
        for node in sorted(physical):
            expected_u = [0.0, 0.0, q] if node in upper else [0.0, 0.0, 0.0]
            expected_v = [0.0, 0.0, vq] if node in upper else [0.0, 0.0, 0.0]
            actual_u = u_dat["nodes"][node]
            actual_v = v_dat["nodes"][node]
            frd_u = disp["nodes"][node]
            frd_v = velo["nodes"][node]
            require(len(actual_u) == len(actual_v) == len(frd_u) == len(frd_v) == 3,
                    f"{case}: three-component U/V required for node {node}")
            for component in range(3):
                metrics.check("DAT_U_mm", actual_u[component], expected_u[component],
                              tol["U_mm"], f"{case} DAT node {node} U{component+1} inc {increment}")
                metrics.check("DAT_V_mm_per_s", actual_v[component], expected_v[component],
                              tol["V_mm_per_s"], f"{case} DAT node {node} V{component+1} inc {increment}")
                metrics.check("FRD_U_mm", frd_u[component], expected_u[component],
                              tol["U_mm"], f"{case} FRD node {node} U{component+1} inc {increment}")
                metrics.check("FRD_V_mm_per_s", frd_v[component], expected_v[component],
                              tol["V_mm_per_s"], f"{case} FRD node {node} V{component+1} inc {increment}")
                metrics.check("FRD_DAT_U_mm", frd_u[component], actual_u[component],
                              tol["U_mm"], f"{case} FRD/DAT node {node} U{component+1} inc {increment}")
                metrics.check("FRD_DAT_V_mm_per_s", frd_v[component], actual_v[component],
                              tol["V_mm_per_s"], f"{case} FRD/DAT node {node} V{component+1} inc {increment}")
        controller_u = u_dat["nodes"][q_node]
        controller_v = v_dat["nodes"][q_node]
        require(len(controller_u) == len(controller_v) == 3,
                f"{case}: controller U/V does not have three components")
        for component, value in enumerate((0.0, 0.0, q)):
            metrics.check("controller_U_mm", controller_u[component], value, tol["U_mm"],
                          f"{case} q U{component+1} inc {increment}")
        for component, value in enumerate((0.0, 0.0, vq)):
            metrics.check("controller_V_mm_per_s", controller_v[component], value,
                          tol["V_mm_per_s"], f"{case} q V{component+1} inc {increment}")

        body_energy = {}
        for body, mass, volume, kinetic in (
            (out["dat_upper_energy_set"], 1.0, 8.0, reference["kinetic_energy_Nmm"]),
            (out["dat_lower_energy_set"], 1.0, 8.0, 0.0),
        ):
            body_energy[body] = {}
            for kind, value, key in (
                ("ELSE", 0.0, "ELSE_Nmm"), ("ELKE", kinetic, "ELKE_Nmm"),
                ("EMAS", mass, "EMAS_tonne"), ("EVOL", volume, "EVOL_mm3"),
            ):
                observed = accepted_energy(energies, kind, body, time_s, time_tol)
                metrics.check(key, observed, value, tol[key],
                              f"{case} {body} {kind} increment {increment}")
                body_energy[body][kind] = observed
        cels_match = [(time, value) for time, value in cels.items()
                      if abs(time - time_s) <= time_tol]
        require(len(cels_match) == 1,
                f"{case}: CELS missing/duplicate at accepted increment {increment}")
        cels_value = cels_match[0][1]
        metrics.check("CELS_Nmm", cels_value, reference["contact_energy_Nmm"],
                      tol["CELS_Nmm"], f"{case} CELS increment {increment}")
        total_energy = (body_energy[out["dat_upper_energy_set"]]["ELKE"] +
                        body_energy[out["dat_upper_energy_set"]]["ELSE"] + cels_value)
        metrics.check("total_energy_Nmm", total_energy, reference["total_energy_Nmm"],
                      tol["total_energy_Nmm"], f"{case} total energy inc {increment}")

        state = {"increment": increment, "time_s": time_s, "q_mm": q,
                 "q_velocity_mm_per_s": vq, "physical_U": u_dat["nodes"],
                 "physical_V": v_dat["nodes"], "controller_U": controller_u,
                 "controller_V": controller_v, "energies": body_energy,
                 "CELS_Nmm": cels_value, "total_energy_Nmm": total_energy,
                 "final_contact_count": final_contact_count}
        history.append(state)

        if case == "trace":
            trace_rows_for_state = trace_rows["groups"].get(final_key, [])
            if expected_active:
                require(len(trace_rows_for_state) == final_contact_count > 0,
                        f"Trace: final active trial rows/count differ at {final_key}")
                total_area = sum(row["area"] for row in trace_rows_for_state)
                metrics.check("final_active_area_mm2", total_area,
                              acceptance["model"]["interface_area_mm2"],
                              acceptance["trace_tolerances"]["compression_total_area_mm2"],
                              f"trace active area inc {increment}")
                total_trace_energy = sum(row["spring_energy"] for row in trace_rows_for_state)
                metrics.check("final_trial_CELS_Nmm", total_trace_energy, cels_value,
                              acceptance["trace_tolerances"]["aggregate_energy_Nmm"],
                              f"trace CELS/trial energy inc {increment}")
                point_force = [sum(row["signed_pressure"] * row["area"] *
                                   row[name] for row in trace_rows_for_state)
                               for name in ("normal_x", "normal_y", "normal_z")]
                cfn_state = pair_summary[increment - 1]["force_N"]
                for component in range(3):
                    metrics.check("TRIAL_CFN_force_N", point_force[component],
                                  cfn_state[component],
                                  acceptance["trace_tolerances"]["aggregate_force_N"],
                                  f"trace point resultant / CFN inc {increment} F{component+1}")
                for row in trace_rows_for_state:
                    metrics.check("final_trial_gap_mm", row["corrected_gap"], q,
                                  acceptance["trace_tolerances"]["corrected_gap_mm"],
                                  f"trace final corrected gap inc {increment}")
            else:
                require(final_contact_count == 0 and not trace_rows_for_state,
                        f"Trace: open final state retains active point rows at {final_key}")
                metrics.check("open_CFN_force_N", math.sqrt(sum(x*x for x in pair_summary[increment-1]["force_N"])),
                              0.0, acceptance["trace_tolerances"]["aggregate_force_N"],
                              f"trace open CFN inc {increment}")
                metrics.check("open_CELS_Nmm", cels_value, 0.0,
                              acceptance["trace_tolerances"]["aggregate_energy_Nmm"],
                              f"trace open CELS inc {increment}")

    if case == "trace":
        verify_trial_rows(trace_rows["parsed"]["CCXPT_TRIAL"], cvg, sta_by_key,
                          expected, acceptance, trace_summary)
    require(not metrics.errors,
            f"{case}: numerical gates failed ({len(metrics.errors)}): " +
            "; ".join(metrics.errors[:8]))
    return {"status": "PASS", "accepted_state_count": len(history),
            "first_time_s": history[0]["time_s"], "last_time_s": history[-1]["time_s"],
            "FRD_raw_frame_count": len(frd_by_key), "FRD_unaccepted_frame_count":
                len(set(frd_by_key) - {(1, i) for i in range(1, 71)}),
            "CVG_iteration_count": len(cvg), "CFN_pair_state_count": len(pair_records),
            "CELS_state_count": len(cels), "trace": trace_summary,
            "metrics": metrics.report(), "history": history,
            "pair_resultants": pair_summary}


def validate_map_rows(rows: list[dict], expected: dict, acceptance: dict,
                      report: dict) -> None:
    require(rows, "Trace contains no CCXPT_MAP rows")
    geometry = expected["geometry"]
    contact = expected["contact"]
    K = acceptance["model"]["normal_penalty_K_N_per_mm3"]
    slave_faces = {element * 10 + int(face[1:])
                   for element, face in geometry["upper_element_faces"]}
    master_faces = {element * 10 + int(face[1:])
                    for element, face in geometry["lower_element_faces"]}
    seen = set()
    generated, positive_gap_filtered = 0, 0
    for row in rows:
        require(row["tie"] == acceptance["trace_contract"]["map_tie"] and
                row["nmethod"] == acceptance["trace_contract"]["map_nmethod"] and
                row["pressure_law"] == acceptance["trace_contract"]["map_pressure_law"],
                "MAP method/tie/pressure-law identity differs")
        require(row["slave_face_encoded"] in slave_faces and
                row["master_face_encoded"] in master_faces and
                row["slave_face_index"] > 0 and row["gauss_index"] > 0,
                "MAP references a face outside the prepared interface")
        near(row["penalty_modulus"], K,
             acceptance["trace_tolerances"]["penalty_modulus_N_per_mm3"],
             "MAP penalty modulus")
        require(row["area"] > acceptance["trace_tolerances"]["point_area_positive_min_mm2"],
                "MAP has nonpositive integration area")
        n_tol = acceptance["trace_tolerances"]["unit_normal_component"]["absolute"]
        for name, ref in (("normal_x", 0.0), ("normal_y", 0.0), ("normal_z", 1.0)):
            require(abs(row[name] - ref) <= n_tol, f"MAP normal {name} differs from +Z")
        if row["native_isol"] != 0:
            generated += 1
        if row["raw_signed_gap"] > 0.0:
            positive_gap_filtered += 1
            require(row["native_isol"] == 0,
                    "Positive-gap MAP row was retained as a generated spring")
        identity = (row["step"], row["increment"], row["attempt"],
                    row["native_iteration"], row["generation_loop"], row["tie"],
                    row["slave_face_index"], row["gauss_index"])
        require(identity not in seen, f"Duplicate MAP identity {identity}")
        seen.add(identity)
    require(generated > 0, "MAP reports no generated compressed contact point")
    require(positive_gap_filtered > 0, "MAP shows no positive-gap filtered point")
    report["generated_map_rows"] = generated
    report["positive_gap_filtered_map_rows"] = positive_gap_filtered
    report["slave_face_codes"] = sorted(slave_faces)
    report["master_face_codes"] = sorted(master_faces)


def verify_trial_rows(rows: list[dict], cvg: dict, sta_by_key: dict,
                      expected: dict, acceptance: dict, report: dict) -> None:
    trace = acceptance["trace_tolerances"]
    K = acceptance["model"]["normal_penalty_K_N_per_mm3"]
    dt = acceptance["states"]["time_increment_s"]
    T = acceptance["states"]["terminal_time_s"]
    g = expected["geometry"]
    slave_faces = {element * 10 + int(face[1:]) for element, face in g["upper_element_faces"]}
    master_faces = {element * 10 + int(face[1:]) for element, face in g["lower_element_faces"]}
    all_gap_trials = 0
    release_positive = 0
    # The native scalar answer is fixed by expected.json's pinned recurrence.
    ref = expected["reference"]["states"]
    for row in rows:
        key = (row["step"], row["increment"], row["attempt"], row["iteration"])
        require(row["step"] == 1 and 1 <= row["increment"] <= 70 and
                row["attempt"] == 1 and row["iteration"] >= 1 and key in cvg,
                f"TRIAL has an unaccepted/out-of-contract identity {key}")
        state_key = (row["step"], row["increment"], row["attempt"])
        require(state_key in sta_by_key, f"TRIAL has no accepted STA state {key}")
        time_s = sta_by_key[state_key]["total_time"]
        require(row["relative_time"] >= 0.0 and row["relative_time"] <= 1.0,
                f"TRIAL relative_time outside [0,1] at {key}")
        near(row["relative_time"] * T, time_s, trace["relative_time_s"],
             f"TRIAL time binding at {key}")
        require(row["tie"] == 1 and row["slave_face_encoded"] in slave_faces and
                row["master_face_encoded"] in master_faces and row["slave_face_index"] > 0 and
                row["gauss_index"] > 0 and row["element"] > 0,
                f"TRIAL contact identity differs from prepared interface at {key}")
        require(row["energy_enabled"] == acceptance["trace_contract"]["trial_energy_enabled"],
                f"TRIAL spring energy is unavailable at {key}")
        near(row["kscale"], acceptance["trace_contract"]["trial_kscale"],
             trace["kscale"], f"TRIAL kscale at {key}")
        require(row["area"] > trace["point_area_positive_min_mm2"],
                f"TRIAL has nonpositive area at {key}")
        normal_tolerance = trace["unit_normal_component"]["absolute"]
        for name, reference in (("normal_x", 0.0), ("normal_y", 0.0), ("normal_z", 1.0)):
            require(abs(row[name] - reference) <= normal_tolerance,
                    f"TRIAL {name} differs from +Z at {key}")
        pressure = -K * row["corrected_gap"] / row["kscale"]
        spring_energy = (0.5 * K * row["area"] * row["corrected_gap"] ** 2 /
                         row["kscale"])
        near(row["signed_pressure"], pressure, trace["signed_pressure_N_per_mm2"],
             f"TRIAL signed pressure law at {key}")
        near(row["spring_energy"], spring_energy, trace["spring_energy_Nmm"],
             f"TRIAL spring energy law at {key}")
        require(row["spring_energy"] >= 0.0, f"TRIAL has negative energy at {key}")
        if row["corrected_gap"] > 0.0:
            require(row["iteration"] <= acceptance["trace_contract"][
                "positive_gap_trial_max_iteration"],
                    f"Positive-gap TRIAL survived regenerated contact set at {key}")
        if row["increment"] == acceptance["states"]["release_increment"] and \
                row["corrected_gap"] > 0.0:
            release_positive += 1
        all_gap_trials += int(row["corrected_gap"] > 0.0)
    report["positive_gap_trial_rows"] = all_gap_trials
    report["release_positive_gap_old_set_trial_rows_observed"] = release_positive
    report["release_positive_gap_old_set_trial_required"] = False


def audit_packet_and_outputs(audit_dir: Path, expected: dict, acceptance: dict) -> dict:
    freeze_path = HERE / "input-freeze.json"
    require(freeze_path.is_file(), "Native audit requires parent-owned input-freeze.json")
    freeze = strict_json(freeze_path)
    execution_path = audit_dir / "execution.json"
    execution = strict_json(execution_path)
    require(freeze.get("schema") == "ccx223_free_impact_freeze/v1" and
            execution.get("schema") == "ccx223_free_impact_execution/v1",
            "Unexpected freeze/execution schema")
    require(execution.get("freeze_sha256") == sha(freeze_path) and
            execution.get("expected_sha256") == sha(HERE / "expected.json") and
            execution.get("case_order") == list(CASES) and
            execution.get("serialized") is True and
            execution.get("status") == "CAPTURES_COMPLETE_PENDING_VERIFICATION",
            "Execution is not a completed, serialized run bound to this freeze")
    require(freeze.get("case_order") == list(CASES) and
            freeze.get("expected_sha256") == sha(HERE / "expected.json") and
            freeze.get("native_execution") is False and
            freeze.get("mechanical_acceptance") is False and
            freeze.get("joint_acceptance") is False,
            "Freeze acceptance boundary or expected binding changed")
    for relative, digest in freeze.get("files_sha256", {}).items():
        require(sha(HERE / relative) == digest, f"Frozen local artifact changed: {relative}")
    for relative, digest in freeze.get("external_dependencies_sha256", {}).items():
        require(sha(repo_root() / relative) == digest,
                f"Frozen external dependency changed: {relative}")
    runner = load_module("free_impact_runner_inventory", HERE / "run.py")
    require(set(freeze.get("files_sha256", {})) == set(runner.STATIC_FILES),
            "Frozen local inventory differs from runner STATIC_FILES")
    require(len(freeze.get("external_dependencies_sha256", {})) >= 20,
            "Expected source and parser dependency inventory is incomplete")
    require(execution.get("input_sha256") ==
            {case: expected["inputs"][case]["sha256"] for case in CASES},
            "Execution inputs differ from expected.json")
    case_records = {row["case"]: row for row in execution.get("cases", [])}
    require(list(row["case"] for row in execution.get("cases", [])) == list(CASES),
            "Execution case order differs")

    expected_builds = execution.get("build_pins", {})
    # The runner writes immutable case pins into each record and freeze fields.
    expected_pins = {
        "baseline": (freeze["baseline_image_id"], freeze["baseline_binary_sha256"]),
        "trace": (freeze["trace_image_id"], freeze["trace_binary_sha256"]),
    }
    require(expected_builds in ({}, None), "Unexpected top-level build-pin schema")
    outputs = {}
    for index, case in enumerate(CASES, 1):
        folder = audit_dir / case
        case_record = strict_json(folder / "case-execution.json")
        root_record = case_records[case]
        require(root_record["status"] == "PASS_NATIVE_CAPTURE" and
                root_record["execution_sha256"] == sha(folder / "case-execution.json"),
                f"Top-level execution record does not bind {case} capture")
        require(case_record.get("status") == "PASS_NATIVE_CAPTURE" and
                case_record.get("case") == case and case_record.get("case_order_index") == index and
                case_record.get("stop_reason") is None and
                case_record.get("docker_cli_exit_code") == 0,
                f"{case} native capture status is not clean")
        state = case_record.get("container_state", {})
        require(state.get("ExitCode") == 0 and state.get("Running") is False and
                state.get("OOMKilled") is False,
                f"{case} container did not exit normally without OOM")
        image, binary = expected_pins[case]
        require(case_record.get("container_image_id") == image and
                case_record.get("binary_sha256") == binary and
                case_record.get("image_id") == image,
                f"{case} image or executable differs from freeze")
        require(case_record.get("limits") == freeze["limits"],
                f"{case} resource limits differ from freeze")
        command = case_record.get("command", [])
        require(command[:2] == ["docker", "run"] and "--network" in command and
                command[command.index("--network") + 1] == "none" and
                "--cpus" in command and command[command.index("--cpus") + 1] == "1" and
                "--memory" in command and command[command.index("--memory") + 1] == "1g" and
                "--memory-swap" in command and
                command[command.index("--memory-swap") + 1] == "1g" and
                "OMP_NUM_THREADS=1" in command and
                "CCX_NPROC_EQUATION_SOLVER=1" in command,
                f"{case} Docker resource command differs")
        required_output = {"coupon.inp", "coupon.dat", "coupon.sta", "coupon.cvg",
                           "coupon.frd", "solver.stdout", "solver.stderr"}
        hashes = case_record.get("outputs_sha256", {})
        actual_names = {p.name for p in folder.iterdir() if p.is_file() and
                        p.name not in {"case-execution.json", "case-execution.json.tmp"}}
        require(required_output <= set(hashes) and actual_names == set(hashes),
                f"{case} native output inventory is incomplete or has extras")
        for name, digest in hashes.items():
            require(sha(folder / name) == digest, f"{case} output hash mismatch: {name}")
        input_item = expected["inputs"][case]
        require(hashes["coupon.inp"] == input_item["sha256"],
                f"{case} executed a different input deck")
        require(case_record.get("native_output_bytes", math.inf) <=
                freeze["limits"]["aggregate_native_output_bytes_each_case"],
                f"{case} output exceeds frozen byte cap")
        start = case_record.get("started_utc")
        end = case_record.get("ended_utc")
        require(start and end and case_record.get("elapsed_seconds", math.inf) <=
                freeze["limits"]["wall_seconds_each_case"],
                f"{case} is missing run timestamps or exceeded time cap")
        outputs[case] = {name: (folder / name).read_bytes() for name in required_output}
    baseline_end = datetime.fromisoformat(strict_json(audit_dir / "baseline/case-execution.json")["ended_utc"])
    trace_start = datetime.fromisoformat(strict_json(audit_dir / "trace/case-execution.json")["started_utc"])
    require(baseline_end <= trace_start, "Baseline and trace native runs overlapped")
    return {"execution": execution, "freeze": freeze, "case_records": case_records,
            "captures": outputs}


def compare_case_results(baseline: dict, trace: dict, expected: dict,
                         acceptance: dict) -> dict:
    """Compare measured baseline/trace histories after each passed its oracle."""
    cross_metrics = Metrics()
    tol = acceptance["tolerances"]
    pair_tol = tol["CFN_component_N"]
    moment_tol = tol["CFN_origin_moment_component_Nmm"]
    baseline_history = baseline["history"]
    trace_history = trace["history"]
    baseline_pairs = baseline["pair_resultants"]
    trace_pairs = trace["pair_resultants"]
    require(len(baseline_history) == len(trace_history) == 70 and
            len(baseline_pairs) == len(trace_pairs) == 70,
            "Cross-case histories or CFN pair states are incomplete")
    for index, (base, traced) in enumerate(zip(baseline_history, trace_history), 1):
        for component in range(3):
            cross_metrics.check("baseline_trace_controller_U_mm",
                                traced["controller_U"][component],
                                base["controller_U"][component], tol["U_mm"],
                                f"cross-case increment {index} controller U{component+1}")
            cross_metrics.check("baseline_trace_controller_V_mm_per_s",
                                traced["controller_V"][component],
                                base["controller_V"][component], tol["V_mm_per_s"],
                                f"cross-case increment {index} controller V{component+1}")
        for node in expected["geometry"]["physical_nodes"]:
            for component in range(3):
                cross_metrics.check("baseline_trace_U_mm",
                                    traced["physical_U"][node][component],
                                    base["physical_U"][node][component], tol["U_mm"],
                                    f"cross-case increment {index} node {node} U{component+1}")
                cross_metrics.check("baseline_trace_V_mm_per_s",
                                    traced["physical_V"][node][component],
                                    base["physical_V"][node][component], tol["V_mm_per_s"],
                                    f"cross-case increment {index} node {node} V{component+1}")
        for body in ("UPPER", "LOWER"):
            for kind in ("ELSE", "ELKE", "EMAS", "EVOL"):
                key = {"ELSE": "ELSE_Nmm", "ELKE": "ELKE_Nmm",
                       "EMAS": "EMAS_tonne", "EVOL": "EVOL_mm3"}[kind]
                cross_metrics.check("baseline_trace_" + key,
                                    traced["energies"][body][kind],
                                    base["energies"][body][kind], tol[key],
                                    f"cross-case increment {index} {body} {kind}")
        cross_metrics.check("baseline_trace_CELS_Nmm", traced["CELS_Nmm"],
                            base["CELS_Nmm"], tol["CELS_Nmm"],
                            f"cross-case increment {index} CELS")
        for component in range(3):
            cross_metrics.check("baseline_trace_CFN_N",
                                trace_pairs[index-1]["force_N"][component],
                                baseline_pairs[index-1]["force_N"][component], pair_tol,
                                f"cross-case increment {index} CFN F{component+1}")
            cross_metrics.check("baseline_trace_CFN_moment_Nmm",
                                trace_pairs[index-1]["moment_N_mm"][component],
                                baseline_pairs[index-1]["moment_N_mm"][component], moment_tol,
                                f"cross-case increment {index} CFN M{component+1}")
    return {"status": "PASS" if not cross_metrics.errors else "FAIL",
            "errors": cross_metrics.errors, "metrics": cross_metrics.report()}


def audit(audit_dir: Path) -> dict:
    expected, acceptance, reference, modules = load_contract()
    bound = audit_packet_and_outputs(audit_dir, expected, acceptance)
    results = {}
    histories = {}
    errors = {}
    for case in CASES:
        try:
            result = audit_capture(case, bound["captures"][case], expected,
                                   acceptance, modules,
                                   modules["reference_states"])
            results[case] = result
            histories[case] = result["history"]
        except Exception as exc:
            results[case] = {"status": "FAIL", "errors": [str(exc)]}
            errors[case] = str(exc)

    cross = {"status": "NOT_RUN", "errors": []}
    if all(results.get(case, {}).get("status") == "PASS" for case in CASES):
        cross = compare_case_results(results["baseline"], results["trace"],
                                     expected, acceptance)
    passed = all(results.get(case, {}).get("status") == "PASS" for case in CASES) and \
        cross["status"] == "PASS"
    for case in CASES:
        results.get(case, {}).pop("history", None)
        results.get(case, {}).pop("pair_resultants", None)
    return {"schema": "ccx223_free_impact_verifier/v1",
            "status": "PASS_FREE_IMPACT_KNOWN_ANSWER" if passed else "FAIL",
            "cases": results, "baseline_trace_comparison": cross,
            "freeze_sha256": sha(HERE / "input-freeze.json"),
            "execution_sha256": sha(audit_dir / "execution.json"),
            "mechanical_acceptance": False, "work_energy_acceptance": False,
            "joint_acceptance": False, "release": False}


def synthetic_capture(case: str, expected: dict, acceptance: dict,
                     trace_format: dict, reference_states: list[dict], *,
                     wrong_motion: bool = False, missing_trial: bool = False,
                     wrong_pressure: bool = False, wrong_force: bool = False):
    """Create a native-free capture with the exact output identities and oracle."""
    geometry = expected["geometry"]
    upper, lower = geometry["upper_nodes"], geometry["lower_nodes"]
    all_nodes, physical = geometry["all_output_nodes"], geometry["physical_nodes"]
    q_node = geometry["controller_node"]
    dt, total = 0.0001, 0.007
    tag_specs = trace_format["tags"]
    dat, frd, sta, cvg, stdout = [], [], [], [], ["Synthetic verifier control; no native solver ran.", " Job finished"]
    # A single aggregate contact point of area 4 is sufficient for parser and
    # arithmetic controls; it is not a mesh or solver result.
    for state in reference_states:
        inc, t = state["increment"], state["time_s"]
        u, v = state["displacement_mm"], state["velocity_mm_s"]
        if wrong_motion and inc == 7:
            u += 0.001
        active = u < 0.0
        count = 1 if active else 0
        final_iteration = 2
        cvg.append(f"{1} {inc} {1} {final_iteration} {count} 0.0 0.0 0.0 0.0")
        sta.append(f"1 {inc} 1 {final_iteration} {t:.12E} {t:.12E} {dt:.12E}")
        # DAT nodal translations and velocities on N_ALL (including q).
        for label, component in (("displacements", u), ("velocities", v)):
            dat.append(f"{label} (vx,vy,vz) for set N_ALL and time {t:.12E}")
            for node in all_nodes:
                z = component if node in upper or node == q_node else 0.0
                if wrong_motion and inc == 7 and node == upper[0] and label == "displacements":
                    z += 0.001
                dat.append(f"{node} 0.000000000000E+00 0.000000000000E+00 {z:.12E}")
            dat.append("")
        upper_energies = {"ELSE": 0.0, "ELKE": state["kinetic_energy_Nmm"],
                          "EMAS": 1.0, "EVOL": 8.0}
        lower_energies = {"ELSE": 0.0, "ELKE": 0.0, "EMAS": 1.0, "EVOL": 8.0}
        for set_name, values in (("UPPER", upper_energies), ("LOWER", lower_energies)):
            for kind, val in values.items():
                label = {"ELSE": "internal energy", "ELKE": "kinetic energy",
                         "EMAS": "mass", "EVOL": "volume"}[kind]
                dat.extend((f" total {label} for set {set_name} and time {t:.12E}",
                            f" {val:.12E}", ""))
        cels = state["contact_energy_Nmm"]
        dat.extend((f" total contact spring energy for time {t:.12E}",
                    "", f" {cels:.12E}", ""))
        fz = -400000.0 * min(u, 0.0)
        force = [0.0, 0.0, fz]
        if wrong_force and inc == 8:
            force[2] += 1.0
        moment = [fz, -fz, 0.0]
        pair_label = next(label for label, quantity in modules_pair_quantities().items()
                          if quantity == "CFN")
        dat.extend((f" statistics for slave set SLAVE, master set MASTER and time {t:.12E}",
                    "", f" {pair_label}", "", " " + " ".join(f"{x:.12E}" for x in force + moment), ""))

        # Two FRD fields use accepted (step, increment) identities and only
        # element-connected physical nodes; controller 8001 remains DAT-only.
        for counter, kind, component in ((inc, "DISP", u), (100 + inc, "VELO", v)):
            frd.extend((f"    1PSTEP                         {counter:12d} {inc:12d} {1:12d}",
                        f"  100CL  {counter} {t:.12E} {len(physical)} 0 1 {inc} 1",
                        f" -4  {kind}        4    1"))
            for axis in ("D1", "D2", "D3") if kind == "DISP" else ("V1", "V2", "V3"):
                frd.append(f" -5  {axis}          1    2    {axis[-1]}    0")
            frd.append(" -5  ALL         1    2    0    0    1ALL")
            for node in physical:
                z = component if node in upper else 0.0
                if wrong_motion and inc == 7 and node == upper[0] and kind == "DISP":
                    z += 0.001
                frd.append(f" -1{node:10d}{0.0:12.5E}{0.0:12.5E}{z:12.5E}")
            frd.append(" -3")

        if case == "trace":
            map_int = [1, inc, 1, final_iteration, 1, 1, 1, 1, 11, 113,
                       1 if active else 0, 4, 1]
            map_real = [u, u, 4.0, 100000.0, 0.0, 0.0, 0.0, 1.0,
                        0.0, 0.0, 0.0, 0.0]
            stdout.append("CCXPT_MAP " + " ".join(map(str, map_int + map_real)))
            if active:
                trial_int = [1, inc, 1, final_iteration, 1, 1, 1, 11, 113, 1, 1]
                pressure = -100000.0 * u
                energy = 0.5 * 100000.0 * 4.0 * u * u
                if wrong_pressure and inc == 8:
                    pressure += 0.1
                if not (missing_trial and inc == 8):
                    trial_real = [u, 0.0, 0.0, pressure, 0.0, 0.0, 4.0, energy,
                                  0.0, 0.0, 1.0, 1.0, t / total]
                    stdout.append("CCXPT_TRIAL " + " ".join(map(str, trial_int + trial_real)))
            conversion = {
                "event": "CCX223_ATTEMPT04_CONVERGENCE", "step": 1,
                "increment": inc, "attempt": 1, "iteration": final_iteration,
                "mechanical_applicable": 1, "iteration_ok": 1,
                "mechanical_residual_ok": 1, "displacement_ok": 1,
                "visco_ok": 1, "contact_change_gate_clear": 1,
                "no_contact_now": int(not active), "no_contact_at_start": int(not active),
                "contact_present": int(active), "mechanical_gate_ok": 1,
                "no_contact_energy_eligible": int(not active),
                "contact_energy_eligible": int(active), "iconvergence": 1,
                "idivergence": 0, "final_convergence_ok": 1,
            }
            stdout.append(json.dumps(conversion, sort_keys=True, separators=(",", ":")))
    if case == "trace":
        # One trace-count event per accepted increment. These are diagnostics,
        # not extra solver state or physical force evidence.
        for state in reference_states:
            inc = state["increment"]
            count = 1 if state["displacement_mm"] < 0 else 0
            contact_event = {"event": "CCX223_ATTEMPT04_CONTACT", "step": 1,
                             "increment": inc, "attempt": 1, "iteration": 2,
                             "contact_old": count, "contact_new": count,
                             "delcon": 0.0, "contact_change_flag": 0}
            stdout.append(json.dumps(contact_event, sort_keys=True, separators=(",", ":")))
    return {
        "coupon.dat": ("\n".join(dat) + "\n").encode(),
        "coupon.frd": ("\n".join(frd) + "\n").encode(),
        "coupon.sta": ("SUMMARY OF JOB INFORMATION\n STEP INC ATT ITRS TOT TIME STEP TIME INC TIME\n" +
                       "\n".join(sta) + "\n").encode(),
        "coupon.cvg": ("SUMMARY OF CONVERGENCE INFORMATION\n" + "\n".join(cvg) + "\n").encode(),
        "solver.stdout": ("\n".join(stdout) + "\n").encode(),
        "solver.stderr": b"",
    }


def modules_pair_quantities() -> dict:
    # Keep synthetic headers aligned with the exact pinned contact-output parser.
    return {"total normal surface force (fx,fy,fz) and its moment about the origin (mx,my,mz)": "CFN"}


def self_test() -> dict:
    expected, acceptance, _reference, modules = load_contract()
    reference_states = modules["reference_states"]
    controls = {}
    positive_results = {}
    for case in CASES:
        capture = synthetic_capture(case, expected, acceptance,
                                    modules["trace_format"], reference_states)
        result = audit_capture(case, capture, expected, acceptance, modules, reference_states)
        require(result["status"] == "PASS", f"Synthetic {case} capture failed")
        positive_results[case] = result
    controls["synthetic_baseline_and_trace_positive"] = True
    cross = compare_case_results(positive_results["baseline"], positive_results["trace"],
                                expected, acceptance)
    require(cross["status"] == "PASS", "Synthetic cross-case comparison failed")
    controls["synthetic_cross_case_measured_comparison"] = True

    altered_trace = {
        "history": [dict(row, controller_U=list(row["controller_U"]))
                    for row in positive_results["trace"]["history"]],
        "pair_resultants": positive_results["trace"]["pair_resultants"],
    }
    altered_trace["history"][24]["controller_U"][2] += 1e-3
    cross = compare_case_results(positive_results["baseline"], altered_trace,
                                expected, acceptance)
    require(cross["status"] == "FAIL",
            "Synthetic cross-case controller motion difference was accepted")
    controls["cross_case_measured_controller_difference_rejected"] = True

    negative = synthetic_capture("baseline", expected, acceptance,
                                 modules["trace_format"], reference_states,
                                 wrong_motion=True)
    try:
        audit_capture("baseline", negative, expected, acceptance, modules, reference_states)
    except ValueError:
        controls["wrong_motion_rejected"] = True
    else:
        fail("Synthetic wrong-motion capture was accepted")

    negative = synthetic_capture("trace", expected, acceptance,
                                 modules["trace_format"], reference_states,
                                 missing_trial=True)
    try:
        audit_capture("trace", negative, expected, acceptance, modules, reference_states)
    except ValueError:
        controls["trial_cvg_gap_rejected"] = True
    else:
        fail("Synthetic missing TRIAL/CVG coverage was accepted")

    negative = synthetic_capture("trace", expected, acceptance,
                                 modules["trace_format"], reference_states,
                                 wrong_pressure=True)
    try:
        audit_capture("trace", negative, expected, acceptance, modules, reference_states)
    except ValueError:
        controls["wrong_trial_pressure_law_rejected"] = True
    else:
        fail("Synthetic wrong TRIAL pressure was accepted")

    negative = synthetic_capture("baseline", expected, acceptance,
                                 modules["trace_format"], reference_states,
                                 wrong_force=True)
    try:
        audit_capture("baseline", negative, expected, acceptance, modules, reference_states)
    except ValueError:
        controls["wrong_pair_force_rejected"] = True
    else:
        fail("Synthetic wrong CFN force was accepted")
    return {"schema": "ccx223_free_impact_verifier_self_test/v1",
            "status": "PASS_SYNTHETIC_CONTROLS", "controls": controls,
            "native_run_performed": False}


def main() -> int:
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--audit-dir", type=Path,
                      help="parent-run output directory containing baseline/ and trace/")
    mode.add_argument("--self-test", action="store_true",
                      help="run synthetic positive and negative parser/arithmetic controls")
    args = parser.parse_args()
    if args.self_test:
        result = self_test()
    else:
        try:
            result = audit(args.audit_dir.resolve())
        except Exception as exc:
            result = {"schema": "ccx223_free_impact_verifier/v1", "status": "FAIL_CLOSED",
                      "errors": [str(exc)], "mechanical_acceptance": False,
                      "work_energy_acceptance": False, "joint_acceptance": False,
                      "release": False}
    print(json.dumps(result, sort_keys=True, indent=2, allow_nan=False))
    return 0 if result["status"] in ("PASS_FREE_IMPACT_KNOWN_ANSWER",
                                      "PASS_SYNTHETIC_CONTROLS") else 1


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(json.dumps({"status": "FAIL_CLOSED", "error": str(exc)},
                         sort_keys=True), file=sys.stderr)
        raise SystemExit(2)
