#!/usr/bin/env python3
"""Audit inherited fixture gates and separately report ELSE/CELS energy evidence."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import re
import tarfile


HERE = Path(__file__).resolve().parent
EVAL = HERE.parent
BASELINE = EVAL / "contact-section-force-known-answer-attempt02"
FULLSTEP = EVAL / "contact-mortar-c3d10-fullstep-attempt01"
PREPARE = HERE / "prepare.py"
IMAGE = "sha256:31336f517557f5dd5f97d85b1e6e15947fd1c10b44edc1364dbba4c1a5ab6c38"
BINARY_SHA = "c6882d262b44525a563250673420dff1506c41b95e6d82d50392f9af26111863"
CASES = ["mortar_c3d10", "penalty_c3d10"]

BASELINE_PINS = {
    "input-freeze.json": "0603288af8a4385000d029eca0e31bda57fc63f39e474796033213026b5aa8f7",
    "execution.json": "2736908e0f59c73a43330021c6c3798e46fc3726b22a179ec3dcb1ee07b43435",
    "verifier.py": "c68a9fd998d8ed601d4223118af1699b343cc6688e37818e03131fd84321524b",
    "verifier.json": "4a0fe723f21686ffa6e0d41ca7724b5f901b6234db87a4ac7b3a376dd73da215",
    "RESULTS.md": "99a1768739ad988fa91a6eaf46e6561264d948bfc629095739d7f48b45c318ca",
    "expected.json": "9298fdce2f9e3e04d5cc12112361a06c6029ecfbbf0f1fa9fa329925d1f42bfd",
}
ENERGY_BLOCK = (
    "*EL PRINT,ELSET=UPPER,TOTALS=ONLY,FREQUENCY=1\nELSE\n"
    "*EL PRINT,ELSET=LOWER,TOTALS=ONLY,FREQUENCY=1\nELSE\n"
    "*CONTACT PRINT,TOTALS=ONLY,FREQUENCY=1\nCELS\n"
)
SECTION_AND_STRESS_AND_ENERGY_BLOCK = (
    "*SECTION PRINT,SURFACE=SLAVE,NAME=SLAVE_IF,FREQUENCYF=1\nSOF\n"
    "*SECTION PRINT,SURFACE=MASTER,NAME=MASTER_IF,FREQUENCYF=1\nSOF\n"
    "*EL FILE,FREQUENCY=1\nS\n"
    + ENERGY_BLOCK
)
MECHANICAL_VERIFIER = BASELINE / "verifier.py"
ENERGY_SOURCE_MEMBERS = {
    "CalculiX/ccx_2.23/src/contactpairs.f":
        "e2b7e8176adc70f02f5140308a0c6a591fc9f7f620026867708e6345a9d9c488",
    "CalculiX/ccx_2.23/src/contactprints.f":
        "88a2fc1a15caa2ab9b28de6ff6c4566f34e7f24c9db5c2c3ee4ef333439c717d",
    "CalculiX/ccx_2.23/src/elprints.f":
        "15d4ad6001e3ecb4eeaa05cba39333626b6c079cbe9d696879092dc2c73ff7b7",
    "CalculiX/ccx_2.23/src/getcontactparams.f":
        "03384b3d55deb22010f19a4521f3b10380caaf16441d270bf35f886ec0aadbaa",
    "CalculiX/ccx_2.23/src/printout.f":
        "ae2b60b4e086846e2833a1d723c37645c0ff6701d2e28dc7e3163d0a4d136f32",
    "CalculiX/ccx_2.23/src/printoutelem.f":
        "e5da47dd83dd8e796fcbf8ec81e220b5139211b8f411c03adb17a782436e2544",
    "CalculiX/ccx_2.23/src/resultsmech.f":
        "15fccc9fb553f259af5d33bc78e8d3808f1f9f338ee266ce92192bae33026fa6",
    "CalculiX/ccx_2.23/src/springforc_f2f.f":
        "3be67688eb16a95739e09990c34ae0d2614acff216b254ea474bbf7c4d9e1ba4",
}


def require(ok: bool, message: str) -> None:
    if not ok:
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
    return json.loads(path.read_text(), object_pairs_hook=unique_pairs,
                      parse_constant=lambda token: (_ for _ in ()).throw(
                          ValueError(f"Nonstandard JSON number {token} in {path}")))


def number(value: str) -> float:
    # Fortran Ew.d may omit E when an exponent has three digits.
    match = re.fullmatch(r"\s*([+-]?(?:\d+\.\d*|\.\d+))([+-]\d{3})\s*", value)
    if match and abs(int(match[2])) > 99:
        value = match[1] + "E" + match[2]
    result = float(value.strip().replace("D", "E").replace("d", "E"))
    require(math.isfinite(result), f"Nonfinite numeric evidence: {value!r}")
    return result


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    require(spec is not None and spec.loader is not None, f"Cannot load verifier {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def verify_source(expected: dict) -> dict:
    source = expected["pinned_2_23_source"]
    archive = EVAL / "ordinary-external-force-transient-attempt04-diagnostic" / "build-attempt02/source.tar.bz2"
    manual = HERE.parents[4] / source["manual_path"]
    require(sha(archive) == source["archive_sha256"], "Pinned 2.23 source archive changed")
    require(sha(manual) == source["manual_sha256"], "Pinned 2.23 manual changed")
    require(source["source_members_sha256"] == ENERGY_SOURCE_MEMBERS,
            "Energy source-member pins changed")
    with tarfile.open(archive, "r:bz2") as tar:
        for member_path, digest in ENERGY_SOURCE_MEMBERS.items():
            member = tar.extractfile(tar.getmember("./" + member_path))
            require(member is not None and hashlib.sha256(member.read()).hexdigest() == digest,
                    f"Pinned 2.23 source member changed: {member_path}")
    source_note = HERE.parents[0] / "contact-mortar-c3d10-fullstep-attempt01" / "energy-method-review-2026-09-27.md"
    require(sha(source_note) == source["method_review_sha256"],
            "Pinned energy-method review changed")
    return {"archive_sha256": source["archive_sha256"],
            "manual_sha256": source["manual_sha256"],
            "source_members_sha256": ENERGY_SOURCE_MEMBERS,
            "method_review_sha256": source["method_review_sha256"]}


def parent_review_audit(expected: dict) -> dict:
    review = read_json(HERE / "parent-review.json")
    require(review.get("ready_for_bounded_fixture") is True
            and review.get("energy_contract_reviewed") is True,
            "Parent review does not approve the energy contract")
    require(review.get("reviewed_expected_sha256") == sha(HERE / "expected.json"),
            "Parent review does not bind expected.json")
    return {"status": "PASS_PARENT_REVIEW_BINDING",
            "reviewed_expected_sha256": review["reviewed_expected_sha256"]}


def verify_frozen_packet(expected: dict) -> tuple[dict, dict, dict]:
    freeze_path = HERE / "input-freeze.json"
    execution_path = HERE / "execution.json"
    freeze = read_json(freeze_path)
    execution = read_json(execution_path)
    require(freeze.get("schema") == "contact_energy_known_answer_freeze/v1",
            "Unexpected energy input-freeze schema")
    require(execution.get("schema") == "contact_energy_known_answer_execution/v1",
            "Unexpected energy execution schema")
    expected_review = parent_review_audit(expected)
    require(execution.get("input_freeze_sha256") == sha(freeze_path), "Execution/freeze hash mismatch")
    require(freeze.get("parent_reviewed_expected_sha256") == sha(HERE / "expected.json"),
            "Freeze does not bind reviewed energy contract")
    require(freeze.get("cases") == CASES and execution.get("image_id") == IMAGE
            and freeze.get("image_id") == IMAGE, "Case or image identity mismatch")
    require(freeze.get("binary_sha256") == BINARY_SHA
            and execution.get("binary_sha256") == BINARY_SHA,
            "Pinned executable identity mismatch")
    require(freeze.get("limits") == {"seconds_per_case": 60,
                                     "output_bytes_per_case": 100 * 1024 * 1024,
                                     "stdout_or_stderr_bytes": 5 * 1024 * 1024,
                                     "cpus": 1, "memory": "1g", "memory_plus_swap": "1g"},
            "Frozen resource limits differ")
    required_files = {
        "README.md", "prepare.py", "preparation.json", "expected.json",
        "parent-review.json", "verifier.py", "run.py",
        "input/mortar_c3d10.inp", "input/penalty_c3d10.inp",
    }
    require(set(freeze.get("files_sha256", {})) == required_files,
            "Freeze file inventory differs from the energy packet contract")
    for path, digest in freeze["files_sha256"].items():
        require(sha(HERE / path) == digest, f"Frozen file changed: {path}")
    require(execution.get("status") == "completed_pending_audit"
            and execution.get("frozen_inputs_unchanged") is True,
            "Execution incomplete or frozen inputs changed")
    require(execution.get("mechanical_acceptance") is False
            and execution.get("energy_acceptance") is False
            and execution.get("joint_acceptance") is False
            and execution.get("release") is False,
            "Execution record overstates acceptance")
    runs = execution.get("runs", [])
    require([run.get("case") for run in runs] == CASES,
            "Missing, duplicated, or nonserial case order")
    for run in runs:
        folder = HERE / "output" / run["case"]
        local = read_json(folder / "execution.json")
        require(local == run, "Per-case and root execution records differ")
        require(run.get("status") == "completed" and run.get("stop_reason") is None,
                f"Case did not complete normally: {run['case']}")
        state = run.get("container_state", {})
        require(run.get("docker_cli_exit_code") == 0 and state.get("ExitCode") == 0
                and state.get("OOMKilled") is False and state.get("Running") is False,
                f"Invalid native terminal state: {run['case']}")
        require(run.get("container_image") == IMAGE, "Container image differs")
        command = run.get("command", [])
        require(command[:2] == ["docker", "run"] and "--pull=never" in command
                and "--network" in command and command[command.index("--network") + 1] == "none"
                and command[-4:] == [IMAGE, "/usr/local/bin/ccx-upstream-2.23", "-i", "coupon"],
                f"Native invocation differs: {run['case']}")
        folder_files = {path.name for path in folder.iterdir() if path.is_file()
                        and path.name not in {"execution.json", "execution.json.tmp"}}
        require(folder_files == set(run.get("outputs_sha256", {})),
                f"Output inventory/hash inventory differs: {run['case']}")
        required_outputs = {"coupon.inp", "coupon.dat", "coupon.sta", "coupon.cvg",
                            "coupon.frd", "coupon.stdout", "coupon.stderr"}
        require(folder_files >= required_outputs, f"Native output missing: {run['case']}")
        for filename, digest in run["outputs_sha256"].items():
            require(sha(folder / filename) == digest,
                    f"Native output hash mismatch {run['case']}/{filename}")
        input_spec = expected["cases"][run["case"]]
        require(sha(folder / "coupon.inp") == input_spec["input_sha256"],
                f"Executed input differs: {run['case']}")
    return freeze, execution, expected_review


def lineage_audit(expected: dict) -> dict:
    for filename, digest in BASELINE_PINS.items():
        require(sha(BASELINE / filename) == digest,
                f"Passing section-force attempt02 changed: {filename}")
    baseline_freeze = read_json(BASELINE / "input-freeze.json")
    for relative, digest in baseline_freeze["files_sha256"].items():
        require(sha(BASELINE / relative) == digest,
                f"Baseline frozen file changed: {relative}")
    baseline_result = read_json(BASELINE / "verifier.json")
    require(baseline_result.get("status") == "PASS_SECTION_STRESS_FIXTURE",
            "Pinned section-force attempt02 is not passing")
    baseline_execution = read_json(BASELINE / "execution.json")
    require(baseline_execution.get("status") == "completed_pending_audit",
            "Pinned section-force attempt02 execution is incomplete")
    deck_hashes = {}
    for case in CASES:
        filename = case + ".inp"
        source = BASELINE / "input" / filename
        current = HERE / "input" / filename
        source_hash = expected["baseline_source"]["input_sha256"][filename]
        require(sha(source) == source_hash == baseline_freeze["files_sha256"]["input/" + filename],
                f"Immutable attempt02 input changed: {filename}")
        raw = current.read_text()
        require(raw.count(ENERGY_BLOCK) == 3 and raw.replace(ENERGY_BLOCK, "") == source.read_text(),
                f"Energy packet changed beyond three output-only blocks: {filename}")
        spec = expected["cases"][case]
        deck_hashes[case] = sha(current)
        require(deck_hashes[case] == spec["input_sha256"],
                f"Prepared energy deck hash differs: {filename}")
        prior_case_exec = read_json(BASELINE / "output" / case / "execution.json")
        require(prior_case_exec.get("status") == "completed"
                and prior_case_exec.get("docker_cli_exit_code") == 0,
                f"Baseline native case is not complete: {case}")
        for output_name, output_hash in prior_case_exec.get("outputs_sha256", {}).items():
            require(sha(BASELINE / "output" / case / output_name) == output_hash,
                    f"Baseline output changed: {case}/{output_name}")
    require(expected["baseline_source"]["status"] == "PASS_SECTION_STRESS_FIXTURE",
            "Expected baseline status changed")
    return {"status": "PASS_LINEAGE", "baseline_verifier_status": baseline_result["status"],
            "baseline_input_sha256": expected["baseline_source"]["input_sha256"],
            "prepared_energy_input_sha256": deck_hashes,
            "only_added_output": "ELSE totals per body plus CELS total per state"}


def accepted_time_step(states: list[dict], time_value: float) -> int:
    matches = [state for state in states if abs(state["total"] - time_value) < 2e-6]
    require(len(matches) == 1, f"Energy output time does not map to one accepted state: {time_value}")
    return matches[0]["step"]


def parse_energy_records(text: str, states: list[dict]) -> dict:
    """Parse pinned *PRINT total headers; reject duplicate, malformed, or unmatched records."""
    records = {"ELSE": {"UPPER": {}, "LOWER": {}}, "CELS": {}}
    seen_keys = set()
    lines = text.splitlines()
    else_re = re.compile(
        r"^total internal energy for set\s+([A-Za-z0-9_]+)\s+and time\s+(\S+)$",
        re.IGNORECASE,
    )
    cels_re = re.compile(r"^total contact spring energy for time\s+(\S+)$", re.IGNORECASE)
    for index, line in enumerate(lines):
        normalized = " ".join(line.split())
        match = else_re.fullmatch(normalized)
        kind = None
        set_name = None
        time_token = None
        if match:
            kind = "ELSE"
            set_name, time_token = match.groups()
            set_name = set_name.upper()
            require(set_name in records["ELSE"], f"Unexpected ELSE element set: {set_name}")
        else:
            match = cels_re.fullmatch(normalized)
            if match:
                kind = "CELS"
                time_token = match.group(1)
        if kind is None:
            continue
        time_value = number(time_token)
        step = accepted_time_step(states, time_value)
        key = (kind, set_name, step)
        require(key not in seen_keys, f"Duplicate energy header {key}")
        seen_keys.add(key)
        value_index = index + 1
        while value_index < len(lines) and not lines[value_index].strip():
            value_index += 1
        require(value_index < len(lines), f"Missing value after energy header {key}")
        value_tokens = lines[value_index].split()
        require(len(value_tokens) == 1, f"Malformed total energy value after {key}")
        value = number(value_tokens[0])
        if kind == "ELSE":
            records["ELSE"][set_name][step] = value
        else:
            records["CELS"][step] = value
    accepted_steps = {int(state["step"]) for state in states}
    for body in ("UPPER", "LOWER"):
        require(set(records["ELSE"][body]) == accepted_steps,
                f"Missing or extra ELSE accepted-state record for {body}")
    require(set(records["CELS"]) in (set(), accepted_steps),
            "CELS output is partial or contains an extra accepted-state record")
    return records


def compare_value(observed: float, reference: float, rel: float, abs_tol: float) -> dict:
    error = abs(observed - reference)
    tolerance = abs_tol if reference == 0 else rel * abs(reference) + abs_tol
    return {"observed_N_mm": observed, "reference_N_mm": reference,
            "absolute_error_N_mm": error, "tolerance_N_mm": tolerance,
            "pass": error <= tolerance}


def audit_body_else(records: dict, expected: dict) -> dict:
    contract = expected["energy_contract"]
    states = contract["states"]
    tolerances = contract["predeclared_energy_tolerances"]
    rel = float(tolerances["relative_component_tolerance"])
    abs_tol = float(tolerances["absolute_energy_tolerance_N_mm"])
    body_results = {}
    all_pass = True
    for body in ("UPPER", "LOWER"):
        values = records["ELSE"][body]
        step_results = {}
        for label, spec in (("open", states["open"]),
                            ("compression", states["compression"]),
                            ("reopen", states["reopen"])):
            step = int(spec["step"])
            reference = float(spec["body_ELSE_each_N_mm"])
            if step not in values:
                step_results[label] = {"pass": False, "error": "missing ELSE total"}
            else:
                step_results[label] = compare_value(values[step], reference, rel, abs_tol)
            all_pass = all_pass and step_results[label]["pass"]
        body_results[body] = {"status": "PASS" if all(x["pass"] for x in step_results.values()) else "FAIL",
                              "states": step_results}
    bulk_pair = {}
    for label, spec in (("open", states["open"]),
                        ("compression", states["compression"]),
                        ("reopen", states["reopen"])):
        step = int(spec["step"])
        ref_key = "bulk_ELSE_pair_N_mm"
        if ref_key not in spec:
            reference = 2 * float(spec["body_ELSE_each_N_mm"])
        else:
            reference = float(spec[ref_key])
        upper = records["ELSE"]["UPPER"].get(step)
        lower = records["ELSE"]["LOWER"].get(step)
        if upper is None or lower is None:
            bulk_pair[label] = {"pass": False, "error": "incomplete per-body ELSE totals"}
        else:
            bulk_pair[label] = compare_value(upper + lower, reference, rel, abs_tol)
        all_pass = all_pass and bulk_pair[label]["pass"]
    return {"status": "PASS_KNOWN_ANSWER" if all_pass else "FAIL_KNOWN_ANSWER",
            "bodies": body_results, "bulk_pair": bulk_pair}


def audit_penalty_cels(records: dict, expected: dict) -> dict:
    contract = expected["energy_contract"]
    values = records["CELS"]
    rel = float(contract["predeclared_energy_tolerances"]["relative_component_tolerance"])
    abs_tol = float(contract["predeclared_energy_tolerances"]["absolute_energy_tolerance_N_mm"])
    states = contract["states"]
    if not values:
        return {"status": "UNAVAILABLE_UNVALIDATED", "available": False,
                "records_N_mm": {}, "reason": "No CELS totals were printed."}
    state_results = {}
    all_pass = True
    for label in ("open", "compression", "reopen"):
        spec = states[label]
        step = int(spec["step"])
        reference = float(spec["contact_CELS_N_mm"])
        if step not in values:
            state_results[label] = {"pass": False, "error": "missing CELS total"}
        else:
            state_results[label] = compare_value(values[step], reference, rel, abs_tol)
        all_pass = all_pass and state_results[label]["pass"]
    complete = len(values) == 3 and all(int(states[key]["step"]) in values
                                         for key in ("open", "compression", "reopen"))
    status = "PASS_KNOWN_ANSWER" if complete and all_pass else (
        "FAIL_KNOWN_ANSWER" if complete else "INCOMPLETE_UNVALIDATED")
    return {"status": status, "available": True, "records_N_mm": values,
            "states": state_results}


def audit_mortar_cels(records: dict, expected: dict, source_supported: bool) -> dict:
    contract = expected["energy_contract"]
    values = records["CELS"]
    if not values:
        return {"status": "UNAVAILABLE_UNVALIDATED", "available": False,
                "source_supported": source_supported, "records_N_mm": {},
                "reason": "No MORTAR CELS totals were printed; this is unavailable, not zero."}
    rel = float(contract["predeclared_energy_tolerances"]["relative_component_tolerance"])
    abs_tol = float(contract["predeclared_energy_tolerances"]["absolute_energy_tolerance_N_mm"])
    states = contract["states"]
    comparisons = {}
    all_match = True
    complete = len(values) == 3
    for label in ("open", "compression", "reopen"):
        spec = states[label]
        step = int(spec["step"])
        reference = float(spec["contact_CELS_N_mm"])
        if step not in values:
            comparisons[label] = {"pass": False, "error": "missing CELS total"}
            complete = False
        else:
            comparisons[label] = compare_value(values[step], reference, rel, abs_tol)
            all_match = all_match and comparisons[label]["pass"]
    if not complete:
        status = "INCOMPLETE_UNVALIDATED"
    elif not all_match:
        status = "OBSERVED_MISMATCH_UNVALIDATED"
    elif not source_supported:
        status = "OBSERVED_MATCH_SOURCE_UNVALIDATED"
    else:
        status = "PASS_KNOWN_ANSWER"
    return {"status": status, "available": True, "source_supported": source_supported,
            "records_N_mm": values, "comparisons": comparisons}


def audit_combined_energy(records: dict, expected: dict, contact_cels: dict,
                          source_supported: bool) -> dict:
    """Compare printed bulk ELSE plus contact CELS against the analytical sum."""
    contract = expected["energy_contract"]
    states = contract["states"]
    rel = float(contract["predeclared_energy_tolerances"]["relative_component_tolerance"])
    abs_tol = float(contract["predeclared_energy_tolerances"]["absolute_energy_tolerance_N_mm"])
    cels_values = records["CELS"]
    if not contact_cels.get("available"):
        return {"status": "UNAVAILABLE_UNVALIDATED", "available": False,
                "states": {},
                "reason": "Combined energy requires an observed contact CELS channel."}
    results = {}
    all_pass = True
    complete = True
    for label in ("open", "compression", "reopen"):
        spec = states[label]
        step = int(spec["step"])
        upper = records["ELSE"]["UPPER"].get(step)
        lower = records["ELSE"]["LOWER"].get(step)
        cels = cels_values.get(step)
        if upper is None or lower is None or cels is None:
            results[label] = {"pass": False, "error": "incomplete observed ELSE/CELS components"}
            complete = False
            all_pass = False
            continue
        reference = float(spec.get(
            "combined_energy_N_mm",
            2 * float(spec["body_ELSE_each_N_mm"]) + float(spec["contact_CELS_N_mm"]),
        ))
        # References come from the separately stated analytical components;
        # observations are the direct sum of the printed channels.
        measured = upper + lower + cels
        results[label] = {
            **compare_value(measured, reference, rel, abs_tol),
            "observed_bulk_ELSE_N_mm": upper + lower,
            "observed_contact_CELS_N_mm": cels,
            "reference_basis": "explicit combined oracle or sum of analytical ELSE and CELS references",
        }
        all_pass = all_pass and results[label]["pass"]
    if not complete:
        status = "INCOMPLETE_UNVALIDATED"
    elif not all_pass:
        status = "OBSERVED_MISMATCH_UNVALIDATED" if not source_supported else "FAIL_KNOWN_ANSWER"
    elif not source_supported:
        status = "OBSERVED_MATCH_SOURCE_UNVALIDATED"
    else:
        status = "PASS_KNOWN_ANSWER"
    return {"status": status, "available": True,
            "source_supported": source_supported, "states": results}


def source_supports_mortar_cels(expected: dict) -> bool:
    statement = expected["pinned_2_23_source"]["source_interpretation"]["CELS_mortar"]
    require(statement == (
        "TYPE=MORTAR maps to mode 2; audited storage/print paths do not establish mode-2 CELS energy."
    ), "Pinned MORTAR CELS interpretation changed; a new source review is required")
    # The reviewed mode-2 channel is unsupported. Do not infer capability from
    # free-text negation or from a present numeric output.
    return False


def audit_energy_case(case: str, states: list[dict], expected: dict) -> dict:
    dat_path = HERE / "output" / case / "coupon.dat"
    try:
        records = parse_energy_records(dat_path.read_text(), states)
    except Exception as exc:
        return {
            "body_ELSE": {"status": "FAIL_INVALID", "error": str(exc)},
            "contact_CELS": {"status": "FAIL_INVALID", "error": str(exc)},
            "combined_ELSE_plus_CELS": {"status": "FAIL_INVALID", "error": str(exc)},
        }
    body = audit_body_else(records, expected)
    if case == "penalty_c3d10":
        cels = audit_penalty_cels(records, expected)
        cels_source_supported = True
    else:
        cels_source_supported = source_supports_mortar_cels(expected)
        cels = audit_mortar_cels(records, expected, cels_source_supported)
    combined = audit_combined_energy(records, expected, cels, cels_source_supported)
    return {"body_ELSE": body, "contact_CELS": cels,
            "combined_ELSE_plus_CELS": combined}


def direct_attempt02_parity(expected: dict, inherited) -> dict:
    baseline_results = {}
    base_verifier = inherited.pinned_module(
        FULLSTEP, "energy_parity_fullstep_verifier", inherited.BASE_PINS
    )
    for case in CASES:
        current_dir = HERE / "output" / case
        baseline_dir = BASELINE / "output" / case
        nodes, _, _ = base_verifier.mesh(BASELINE / "input" / f"{case}.inp")
        node_ids = set(nodes)
        current_dat = base_verifier.dat(current_dir / "coupon.dat", node_ids)
        baseline_dat = base_verifier.dat(baseline_dir / "coupon.dat", node_ids)
        require(current_dat == baseline_dat,
                f"Attempt02 nodal DAT U/RF arrays changed: {case}")
        current_sta = base_verifier.numeric_rows(current_dir / "coupon.sta", 7)
        baseline_sta = base_verifier.numeric_rows(baseline_dir / "coupon.sta", 7)
        require(current_sta == baseline_sta, f"Attempt02 STA trace changed: {case}")
        current_cvg = base_verifier.numeric_rows(current_dir / "coupon.cvg", 9)
        baseline_cvg = base_verifier.numeric_rows(baseline_dir / "coupon.cvg", 9)
        require(current_cvg == baseline_cvg, f"Attempt02 CVG trace changed: {case}")
        baseline_results[case] = {
            "status": "PASS",
            "exact_nodal_DAT_U_RF_parity": True,
            "exact_STA_row_parity": True,
            "exact_CVG_row_parity": True,
            "node_count": len(node_ids),
            "sta_rows": len(current_sta),
            "cvg_rows": len(current_cvg),
            "whole_DAT_file_compared": False,
        }
    return {"status": "PASS_ATTEMPT02_NODAL_AND_TRACE_PARITY",
            "cases": baseline_results}


def audit_mechanics(expected: dict, source_pins: dict) -> tuple[dict, object]:
    inherited = load_module("attempt02_mechanical_verifier", MECHANICAL_VERIFIER)
    inherited.HERE = HERE
    inherited.SECTION_AND_STRESS_BLOCK = SECTION_AND_STRESS_AND_ENERGY_BLOCK
    inherited.lineage_audit = lineage_audit
    result = inherited.audit()
    if result.get("status") != "PASS_SECTION_STRESS_FIXTURE":
        return {"status": "FAIL", "inherited_audit": result,
                "attempt02_parity": {"status": "NOT_RUN_MECHANICS_FAILED"}}, inherited
    parity = direct_attempt02_parity(expected, inherited)
    return {"status": "PASS_SECTION_STRESS_FIXTURE",
            "inherited_audit": result,
            "attempt02_parity": parity,
            "source_pins": source_pins}, inherited


def energy_audit(expected: dict, mechanical: dict) -> dict:
    cases = {}
    if mechanical.get("status") != "PASS_SECTION_STRESS_FIXTURE":
        for case in CASES:
            cases[case] = {"status": "SKIPPED_NO_ACCEPTED_MECHANICAL_STATES"}
        return {"status": "NOT_ACCEPTED_MECHANICS_NOT_PASS", "accepted": False,
                "cases": cases}

    inherited = mechanical["inherited_audit"]
    fixture_cases = inherited.get("unchanged_fixture_audit", {}).get("cases", {})
    if not fixture_cases:
        fixture_cases = inherited.get("fixture_audit", {}).get("cases", {})
    source_supported = source_supports_mortar_cels(expected)
    for case in CASES:
        state_records = fixture_cases[case]["states"]
        cases[case] = audit_energy_case(case, state_records, expected)
    body_ok = all(cases[case]["body_ELSE"].get("status") == "PASS_KNOWN_ANSWER"
                  for case in CASES)
    penalty_cels_ok = cases["penalty_c3d10"]["contact_CELS"].get("status") == "PASS_KNOWN_ANSWER"
    mortar_cels_ok = cases["mortar_c3d10"]["contact_CELS"].get("status") == "PASS_KNOWN_ANSWER"
    combined_ok = all(cases[case]["combined_ELSE_plus_CELS"].get("status") == "PASS_KNOWN_ANSWER"
                      for case in CASES)
    accepted = body_ok and penalty_cels_ok and mortar_cels_ok and combined_ok and source_supported
    if accepted:
        status = "PASS_KNOWN_ANSWER_METHOD_FIXTURE_ONLY"
    else:
        status = "NOT_ACCEPTED_REQUIRED_CHANNEL_MISSING_MISMATCH_OR_SOURCE_UNVALIDATED"
    return {"status": status, "accepted": accepted,
            "required_channels": {
                "body_ELSE_both_formulations": body_ok,
                "penalty_CELS": penalty_cels_ok,
                "mortar_CELS_known_answer_and_source_supported": mortar_cels_ok and source_supported,
                "combined_ELSE_plus_CELS_both_formulations": combined_ok,
            },
            "mortar_CELS_source_supported": source_supported,
            "cases": cases,
            "reason": (
                "MORTAR CELS source semantics are not established for mode 2; a missing "
                "channel or numeric zero at compression cannot be accepted as zero contact energy."
            ) if not accepted else "All required method-fixture energy channels passed.",
            "work_energy_gate_eligible": False}


def audit() -> dict:
    expected = read_json(HERE / "expected.json")
    require(expected.get("schema") == "calculix_mortar_c3d10_energy_known_answer/v1",
            "Unexpected energy expected.json schema")
    require(expected["energy_contract"]["predeclared_energy_tolerances"].get(
        "parent_review_required_before_freeze") is True,
        "Tolerance provenance field changed")
    source_pins = verify_source(expected)
    freeze, execution, review = verify_frozen_packet(expected)
    lineage = lineage_audit(expected)
    mechanical, inherited = audit_mechanics(expected, source_pins)
    energy = energy_audit(expected, mechanical)
    if mechanical["status"] == "PASS_SECTION_STRESS_FIXTURE":
        status = "PASS_MECHANICAL_FIXTURE_ONLY"
    else:
        status = "FAIL_MECHANICAL_FIXTURE"
    return {
        "schema": "calculix_mortar_c3d10_energy_output_audit/v1",
        "status": status,
        "mechanical_status": mechanical["status"],
        "mechanical_audit": mechanical,
        "lineage_audit": lineage,
        "source_audit": source_pins,
        "parent_review_audit": review,
        "energy_status": energy["status"],
        "energy_acceptance": energy["accepted"],
        "energy_audit": energy,
        "mechanical_acceptance": False,
        "joint_acceptance": False,
        "release": False,
        "input_freeze_sha256": sha(HERE / "input-freeze.json"),
        "execution_sha256": sha(HERE / "execution.json"),
        "verifier_sha256": sha(Path(__file__)),
        "freeze_schema": freeze["schema"],
        "execution_schema": execution["schema"],
    }


def _synthetic_block(set_name: str, values: list[float]) -> str:
    times = (1.0, 2.0, 3.0)
    chunks = []
    for time_value, value in zip(times, values):
        chunks.append(
            f"total internal energy for set {set_name} and time {time_value:0.7E}\n\n"
            f"      {value:0.6E}\n"
        )
    return "\n".join(chunks)


def _synthetic_cels(values: list[float]) -> str:
    chunks = []
    for time_value, value in zip((1.0, 2.0, 3.0), values):
        chunks.append(
            f"total contact spring energy for time {time_value:0.7E}\n\n"
            f"      {value:0.6E}\n"
        )
    return "\n".join(chunks)


def synthetic_parser_preflight() -> dict:
    states = [
        {"step": 1, "increment": 1, "total": 1.0},
        {"step": 2, "increment": 1, "total": 2.0},
        {"step": 3, "increment": 1, "total": 3.0},
    ]
    expected = read_json(HERE / "expected.json")
    text = (
        _synthetic_block("UPPER", [0.0, 0.4, 0.0])
        + _synthetic_block("LOWER", [0.0, 0.4, 0.0])
        + _synthetic_cels([0.0, 0.2, 0.0])
    )
    require(source_supports_mortar_cels(expected) is False,
            "Actual pinned source interpretation must keep MORTAR CELS unsupported")
    parsed = parse_energy_records(text, states)
    require(parsed["ELSE"]["UPPER"] == {1: 0.0, 2: 0.4, 3: 0.0}
            and parsed["ELSE"]["LOWER"] == {1: 0.0, 2: 0.4, 3: 0.0},
            "Synthetic ELSE records did not parse exactly")
    require(parsed["CELS"] == {1: 0.0, 2: 0.2, 3: 0.0},
            "Synthetic CELS totals did not parse exactly")
    body = audit_body_else(parsed, expected)
    penalty_cels = audit_penalty_cels(parsed, expected)
    combined = audit_combined_energy(parsed, expected, penalty_cels, True)
    require(body["status"] == "PASS_KNOWN_ANSWER"
            and penalty_cels["status"] == "PASS_KNOWN_ANSWER"
            and combined["status"] == "PASS_KNOWN_ANSWER"
            and combined["states"]["compression"]["observed_bulk_ELSE_N_mm"]
                == 0.8
            and combined["states"]["compression"]["observed_contact_CELS_N_mm"]
                == 0.2
            and combined["states"]["compression"]["observed_N_mm"] == 1.0,
            "Synthetic known-answer energy values did not pass")

    missing_cels = parse_energy_records(
        _synthetic_block("UPPER", [0.0, 0.4, 0.0])
        + _synthetic_block("LOWER", [0.0, 0.4, 0.0]), states
    )
    mortar_absent = audit_mortar_cels(missing_cels, expected, False)
    mortar_absent_combined = audit_combined_energy(
        missing_cels, expected, mortar_absent, False
    )
    require(mortar_absent["status"] == "UNAVAILABLE_UNVALIDATED"
            and mortar_absent["records_N_mm"] == {}
            and mortar_absent_combined["status"] == "UNAVAILABLE_UNVALIDATED",
            "Absent MORTAR CELS must remain unavailable, not be filled with zeros")

    mortar_zero = parse_energy_records(
        _synthetic_block("UPPER", [0.0, 0.4, 0.0])
        + _synthetic_block("LOWER", [0.0, 0.4, 0.0])
        + _synthetic_cels([0.0, 0.0, 0.0]), states
    )
    mortar_zero_status = audit_mortar_cels(mortar_zero, expected, False)
    mortar_zero_combined = audit_combined_energy(mortar_zero, expected, mortar_zero_status, False)
    require(mortar_zero_status["status"] == "OBSERVED_MISMATCH_UNVALIDATED"
            and mortar_zero_status["comparisons"]["compression"]["pass"] is False
            and mortar_zero_combined["status"] == "OBSERVED_MISMATCH_UNVALIDATED"
            and mortar_zero_combined["states"]["compression"]["observed_N_mm"] == 0.8
            and mortar_zero_combined["states"]["compression"]["reference_N_mm"] == 1.0,
            "Numeric zero MORTAR compression energy must fail the 0.2 N*mm oracle")

    bad_inputs = {
        "duplicate": text + _synthetic_block("UPPER", [0.0, 0.4, 0.0]),
        "nonfinite": text.replace("4.000000E-01", "NaN", 1),
        "unmatched_time": text.replace("1.0000000E+00", "4.0000000E+00", 1),
        "malformed_value": text.replace("4.000000E-01", "not-a-number", 1),
    }
    rejected = {}
    for name, sample in bad_inputs.items():
        try:
            parse_energy_records(sample, states)
            rejected[name] = False
        except (ValueError, OverflowError):
            rejected[name] = True
    require(all(rejected.values()), "Parser accepted a duplicate, bad identity, or nonfinite total")

    missing_else_input = (
        _synthetic_block("UPPER", [0.0, 0.4, 0.0])
        + _synthetic_block("LOWER", [0.0, 0.4, 0.0]).replace(
            "total internal energy for set LOWER and time 3.0000000E+00\n\n      0.000000E+00\n", ""
        )
    )
    try:
        parse_energy_records(missing_else_input, states)
        missing_else_rejected = False
    except ValueError:
        missing_else_rejected = True
    require(missing_else_rejected, "Missing per-body energy state must be rejected")

    return {
        "status": "PASS_SYNTHETIC_ENERGY_PARSER_PREFLIGHT",
        "native_run_performed": False,
        "input_freeze_created": False,
        "source_format_basis": "Pinned printout.f and printoutelem.f headers and E13.6 total values",
            "exact_known_answer_values_N_mm": {
            "body_each": [0.0, 0.4, 0.0],
            "penalty_CELS": [0.0, 0.2, 0.0],
        },
        "mortar_absent_status": mortar_absent["status"],
        "mortar_absent_combined_status": mortar_absent_combined["status"],
        "mortar_zero_compression_status": mortar_zero_status["status"],
        "mortar_zero_combined_status": mortar_zero_combined["status"],
        "rejected_malformed_cases": rejected,
        "missing_body_state_status": "REJECTED_MISSING_ACCEPTED_STATE",
        "combined_compression_oracle_N_mm": {
            "observed": combined["states"]["compression"]["observed_N_mm"],
            "reference": combined["states"]["compression"]["reference_N_mm"],
        },
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--preflight", action="store_true",
                        help="Run only synthetic energy-parser checks; no freeze/native outputs")
    parser.add_argument("--write", action="store_true",
                        help="Write verifier.json exclusively after parent-reviewed native run")
    args = parser.parse_args()
    if args.preflight:
        require(not args.write, "Synthetic preflight does not write a result artifact")
        result = synthetic_parser_preflight()
    else:
        try:
            result = audit()
        except Exception as exc:
            result = {"schema": "calculix_mortar_c3d10_energy_output_audit/v1",
                      "status": "FAIL_MECHANICAL_OR_PROVENANCE",
                      "error": str(exc), "energy_acceptance": False,
                      "mechanical_acceptance": False, "joint_acceptance": False,
                      "release": False}
        if args.write:
            result_path = HERE / "verifier.json"
            with result_path.open("x") as stream:
                json.dump(result, stream, indent=2, sort_keys=True)
                stream.write("\n")
    print(json.dumps(result, sort_keys=True))
    if args.preflight:
        raise SystemExit(0 if result["status"] == "PASS_SYNTHETIC_ENERGY_PARSER_PREFLIGHT" else 1)
    raise SystemExit(0 if result.get("status") == "PASS_MECHANICAL_FIXTURE_ONLY" else 1)
