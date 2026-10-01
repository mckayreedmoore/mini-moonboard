#!/usr/bin/env python3
"""Offline audit for the five-state penalty exact-touch work fixture.

The result is limited to a known-answer method fixture. Mechanical fixture
checks, body ELSE, penalty CELS, reaction work, and contact-pair resultants are
reported separately; no output can set mechanical, joint, or release
acceptance true.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import re


HERE = Path(__file__).resolve().parent
EVAL = HERE.parent
FULLSTEP = EVAL / "contact-mortar-c3d10-fullstep-attempt01"
SECTION = EVAL / "contact-section-force-known-answer-attempt02"
CASE = "penalty_touch_work"
EXPECTED_INVENTORY = {
    "README.md", "prepare.py", "preparation.json", "expected.json",
    "parent-review.json", "verifier.py", "run.py", "pair_output.py",
    "prefreeze-amendment.md", "input/penalty_touch_work.inp",
}
STRESS_LABELS = ["SXX", "SYY", "SZZ", "SXY", "SYZ", "SZX"]
CONTACT_LABELS = ["COPEN", "CSLIP1", "CSLIP2", "CPRESS", "CSHEAR1", "CSHEAR2"]
SECTION_HEADERS = [
    ("total surface force (fx,fy,fz) and moment about the origin(mx,my,mz)", 6),
    ("center of gravity and mean normal", 6),
    ("moment about the center of gravity(mx,my,mz)", 3),
    ("area, normal force (+ = tension), shear force (size), torque and bending moment (size)", 5),
]


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def read_json(path: Path) -> dict:
    def unique_pairs(items):
        result = {}
        for key, value in items:
            require(key not in result, f"Duplicate JSON key {key} in {path}")
            result[key] = value
        return result

    return json.loads(path.read_text(), object_pairs_hook=unique_pairs,
                      parse_constant=lambda value: (_ for _ in ()).throw(
                          ValueError(f"Nonstandard JSON number {value} in {path}")))


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    require(spec is not None and spec.loader is not None, f"Cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def number(value: str) -> float:
    # Fortran Ew.d omits E when the exponent has three digits.
    match = re.fullmatch(r"\s*([+-]?(?:\d+\.\d*|\.\d+))([+-]\d{3})\s*", value)
    if match and abs(int(match[2])) > 99:
        value = match[1] + "E" + match[2]
    result = float(value.replace("D", "E").replace("d", "E"))
    require(math.isfinite(result), f"Nonfinite numeric evidence: {value}")
    return result


def norm(vector) -> float:
    return math.sqrt(sum(value * value for value in vector))


def subtract(a, b):
    return tuple(x - y for x, y in zip(a, b))


def add(a, b):
    return tuple(x + y for x, y in zip(a, b))


def dot(a, b):
    return sum(x * y for x, y in zip(a, b))


def close_with_limit(actual: float, reference: float, absolute: float,
                     relative: float) -> dict:
    error = abs(actual - reference)
    limit = max(absolute, relative * max(abs(actual), abs(reference)))
    return {"actual": actual, "reference": reference, "absolute_error": error,
            "limit": limit, "pass": error <= limit}


def vector_close(actual, reference, absolute: float, relative_scale: float) -> dict:
    error = norm(subtract(actual, reference))
    limit = absolute + relative_scale
    return {"actual": list(actual), "reference": list(reference),
            "error_norm": error, "limit": limit, "pass": error <= limit}


def accepted_schedule(expected: dict) -> list[dict]:
    states = expected["solver_contract"]["states"]
    require(len(states) == 5, "Expected exactly five predeclared displacement states")
    times = expected["solver_contract"]["expected_accepted_total_times"]
    require(times == [1.0, 2.0, 3.0, 4.0, 5.0], "Touch-work endpoint times changed")
    result = []
    for step, (state, total_time) in enumerate(zip(states, times), 1):
        require(abs(float(state["total_time"]) - total_time) <= 1e-12,
                "Contract state time differs from declared endpoint times")
        result.append({"step": step, "increment": 1, "attempt": 1,
                       "relative": 1.0, "total": total_time,
                       "name": state["name"], "target_u3": float(state["target_U3_mm"]),
                       "expected_energy": float(state["expected_energy_N_mm"]),
                       "analytical_segment_work": float(state["analytical_segment_work_N_mm"])})
    return result


def audit_prepared_lineage(expected: dict) -> dict:
    """Recreate the exact deck and contract from the pinned known-answer inputs."""
    prep = load_module("touch_work_prepare_for_audit", HERE / "prepare.py")
    source = prep.verify_source()
    prep.verify_baseline()
    mechanical_expected, mechanical_pin = prep.verify_mechanical_baseline()
    deck, lineage = prep.build_deck()
    input_path = HERE / expected["input"]["path"]
    require(input_path.read_text() == deck and sha(input_path) == expected["input"]["sha256"],
            "Current frozen input differs from source-derived five-state deck")
    observation = prep.actual_base_observation()
    reproduced = prep.analytical_contract(source, observation, sha(input_path))
    reproduced_json = json.loads(json.dumps(reproduced, allow_nan=False))
    require(expected == reproduced_json, "Expected contract differs from its pinned producer")
    require(expected["inherited_mechanical_gates"]["expected_sha256"]
            == mechanical_pin["expected_sha256"], "Inherited mechanical contract pin differs")
    require(expected["inherited_mechanical_gates"]["section_force_contract"]
            == mechanical_expected["section_force_contract"],
            "Inherited SOF force/moment contract differs")
    return {"status": "PASS_LINEAGE", "source_and_energy_baseline_revalidated": True,
            "mechanical_baseline_pins": mechanical_pin,
            "normalized_step_templates_preserved": lineage["normalized_templates_preserved"],
            "input_sha256": sha(input_path)}


def audit_packet_and_terminal() -> tuple[dict, dict, dict, dict]:
    expected = read_json(HERE / "expected.json")
    freeze = read_json(HERE / "input-freeze.json")
    execution = read_json(HERE / "execution.json")
    require(expected.get("schema") == "calculix_penalty_exact_touch_work_known_answer/v1",
            "Unexpected expected.json schema")
    require(expected.get("native_execution_authorized") is False
            and expected.get("mechanical_acceptance") is False
            and expected.get("work_energy_acceptance") is False
            and expected.get("joint_acceptance") is False
            and expected.get("release") is False,
            "Prepared authority flags changed")
    require(freeze.get("schema") == "contact_penalty_touch_work_freeze/v1",
            "Unexpected touch-work freeze schema")
    require(execution.get("schema") == "contact_penalty_touch_work_execution/v1",
            "Unexpected touch-work execution schema")
    require(freeze.get("files_sha256", {}) and set(freeze["files_sha256"]) == EXPECTED_INVENTORY,
            "Frozen inventory differs from the reviewed ten-file packet")
    for relative, digest in freeze["files_sha256"].items():
        require(sha(HERE / relative) == digest, f"Frozen input differs: {relative}")
    require(execution.get("input_freeze_sha256") == sha(HERE / "input-freeze.json"),
            "Execution is bound to another freeze")
    require(execution.get("image_id") == freeze.get("image_id")
            and execution.get("binary_sha256") == freeze.get("binary_sha256"),
            "Execution toolchain differs from freeze")
    require(execution.get("status") == "completed_pending_audit"
            and execution.get("frozen_inputs_unchanged") is True,
            "Native run is not a completed pending audit")
    require(execution.get("mechanical_acceptance") is False
            and execution.get("work_energy_acceptance") is False
            and execution.get("joint_acceptance") is False
            and execution.get("release") is False,
            "Execution acceptance flags changed")
    require(freeze.get("mechanical_acceptance") is False
            and freeze.get("work_energy_acceptance") is False
            and freeze.get("joint_acceptance") is False
            and freeze.get("release") is False,
            "Freeze acceptance flags changed")
    require(execution.get("runs") and len(execution["runs"]) == 1
            and execution["runs"][0].get("case") == CASE,
            "Expected one serialized penalty-only case")
    review = read_json(HERE / "parent-review.json")
    require(review.get("ready_for_bounded_fixture") is True
            and review.get("work_energy_contract_reviewed") is True
            and review.get("reviewed_expected_sha256") == sha(HERE / "expected.json"),
            "Parent readiness record does not authorize these exact prepared bytes")
    lineage = audit_prepared_lineage(expected)
    return expected, freeze, execution, {"lineage": lineage, "parent_review": review}


def audit_case_envelope(expected: dict, freeze: dict, top_execution: dict) -> tuple[Path, dict]:
    folder = HERE / "output" / CASE
    require(folder.is_dir(), "Penalty output directory is missing")
    run = top_execution["runs"][0]
    case_execution = read_json(folder / "execution.json")
    require(case_execution == run, "Case and root execution records differ")
    require(run.get("status") == "completed" and run.get("stop_reason") is None,
            "Native case did not complete normally")
    state = run.get("container_state", {})
    require(run.get("docker_cli_exit_code") == 0 and state.get("ExitCode") == 0
            and state.get("Running") is False and state.get("OOMKilled") is False,
            "Native container terminal state is not a clean exit")
    require(run.get("container_image") == freeze["image_id"], "Case used another image")
    command = run.get("command", [])
    require(command[:2] == ["docker", "run"] and "--pull=never" in command
            and "--network" in command and command[command.index("--network") + 1] == "none"
            and "--cpus" in command and command[command.index("--cpus") + 1] == "1"
            and "--memory" in command and command[command.index("--memory") + 1] == "1g"
            and "--memory-swap" in command
            and command[command.index("--memory-swap") + 1] == "1g"
            and command[-4:] == [freeze["image_id"], freeze["binary_path"], "-i", "coupon"],
            "Native command/image/resource contract differs")
    actual_files = {path.name for path in folder.iterdir() if path.is_file()
                    and path.name not in {"execution.json", "execution.json.tmp"}}
    required = {f"coupon.{suffix}" for suffix in
                ("inp", "dat", "cvg", "sta", "frd", "stdout", "stderr")}
    require(actual_files >= required and actual_files == set(run.get("outputs_sha256", {})),
            "Native output inventory is incomplete or differs from capture record")
    for name, digest in run["outputs_sha256"].items():
        require(sha(folder / name) == digest, f"Output hash mismatch: {name}")
    require(sha(folder / "coupon.inp") == expected["input"]["sha256"],
            "Executed input differs from the prepared deck")
    limits = freeze["limits"]
    require(sum(path.stat().st_size for path in folder.iterdir() if path.is_file())
            <= limits["output_bytes_per_case"], "Case output exceeded frozen byte limit")
    require(max((folder / "coupon.stdout").stat().st_size,
                (folder / "coupon.stderr").stat().st_size) <= limits["stdout_or_stderr_bytes"],
            "Captured terminal stream exceeded frozen byte limit")
    for filename in ("coupon.stdout", "coupon.stderr", "coupon.log"):
        path = folder / filename
        if path.exists():
            require("*ERROR" not in path.read_text(errors="replace").upper(),
                    f"Native error marker in {filename}")
    return folder, run


def audit_convergence(folder: Path, base, expected: dict) -> dict:
    cvg_rows = base.numeric_rows(folder / "coupon.cvg", 9)
    keys = [tuple(map(int, row[:4])) for row in cvg_rows]
    require(len(keys) == len(set(keys)), "Duplicate CVG iteration identity")
    for row in cvg_rows:
        for token in row[4:]:
            base.number(token)
    groups = {}
    for step, inc, attempt, iteration in keys:
        require(step in range(1, 6) and inc == 1 and attempt == 1 and iteration > 0,
                "CVG contains an unplanned step/increment/attempt")
        groups.setdefault((step, inc, attempt), []).append(iteration)
    require(set(groups) == {(step, 1, 1) for step in range(1, 6)},
            "CVG is missing or adds a fixed DIRECT step")
    for identity, iterations in groups.items():
        require(iterations == list(range(1, len(iterations) + 1)),
                f"CVG iteration sequence is incomplete at {identity}")
    transcript_counts = {}
    complete_transcript = False
    for name in ("coupon.stdout", "coupon.log"):
        path = folder / name
        if not path.exists():
            continue
        step = inc = attempt = None
        printed = []
        for line in path.read_text(errors="replace").splitlines():
            if match := re.fullmatch(r"\s*STEP\s+(\d+)\s*", line):
                step = int(match[1])
                inc = attempt = None
            elif match := re.fullmatch(r"\s*increment\s+(\d+)\s+attempt\s+(\d+)\s*", line):
                inc, attempt = map(int, match.groups())
            elif match := re.fullmatch(r"\s*iteration\s+(\d+)\s*", line):
                require(None not in (step, inc, attempt), "Iteration transcript lacks identity")
                printed.append((step, inc, attempt, int(match[1])))
        if printed:
            require(len(printed) == len(set(printed)) and all(key in keys for key in printed),
                    f"{name} iteration identities differ from CVG")
            indices = [keys.index(key) for key in printed]
            require(indices == sorted(indices), f"{name} iteration order differs from CVG")
            complete_transcript = complete_transcript or printed == keys
            transcript_counts[name] = len(printed)
    require(complete_transcript, "No full native iteration transcript was captured")
    accepted = []
    rejected = []
    for row in base.numeric_rows(folder / "coupon.sta", 7):
        rejected_attempt = row[2].endswith("U")
        step, inc, attempt, iterations = map(
            int, (row[0], row[1], row[2].removesuffix("U"), row[3]))
        require(groups.get((step, inc, attempt), [])[-1:] == [iterations],
                "STA final iteration differs from CVG")
        total, relative, dt = map(base.number, row[4:])
        if rejected_attempt:
            rejected.append([step, inc, attempt, iterations])
            continue
        require(step in range(1, 6) and inc == 1 and attempt == 1 and iterations >= 2,
                "STA accepted identity is outside the five-step schedule")
        require(abs(relative - 1.0) <= 1e-6 and abs(dt - 1.0) <= 1e-6,
                "STA accepted row is not one complete DIRECT increment")
        require(abs(total - step) <= 2e-6,
                "STA accepted total time differs from its step endpoint")
        require(not accepted or total > accepted[-1]["total"],
                "STA accepted time is not strictly increasing")
        accepted.append({"step": step, "increment": inc, "attempt": attempt,
                         "iterations": iterations, "total": total,
                         "relative": relative, "dt": dt})
    require(not rejected, "Fixed full-step fixture contains a rejected attempt/cutback")
    require(len(accepted) == 5 and [state["step"] for state in accepted] == [1, 2, 3, 4, 5],
            "STA does not contain exactly five accepted endpoints")
    require(set(groups) == {(state["step"], 1, 1) for state in accepted},
            "CVG contains an attempt with no accepted STA state")
    require(keys[-1] == (5, 1, 1, accepted[-1]["iterations"]),
            "CVG has an unaccepted terminal iteration tail")
    for actual, planned in zip(accepted, accepted_schedule(expected)):
        require(actual["step"] == planned["step"]
                and abs(actual["total"] - planned["total"]) <= 2e-6,
                "Accepted state identity/time differs from the reviewed contract")
    return {"status": "PASS", "accepted_states": accepted,
            "cvg_rows": len(cvg_rows), "transcript_iteration_counts": transcript_counts,
            "max_iteration": max(key[3] for key in keys), "rejected_attempts": rejected}


def parse_frd(path_or_text, accepted: list[dict], node_ids: set[int], base) -> dict:
    blocks = []
    current_time = None
    identity = None
    kind = None
    labels = []
    active = None
    frd_text = (path_or_text.read_text(errors="replace")
                if isinstance(path_or_text, Path) else str(path_or_text))
    for line in frd_text.splitlines():
        fields = line.split()
        if fields and fields[0] == "1PSTEP":
            require(active is None and len(fields) >= 4, "Malformed/truncated FRD state header")
            # Pinned writer order: fields[3] is STEP, fields[2] is INC.
            identity = (int(fields[3]), int(fields[2]))
        elif fields and fields[0] == "100CL":
            require(len(fields) >= 3, "Malformed FRD time header")
            current_time = base.number(fields[2])
        elif line.startswith(" -4"):
            require(active is None and len(fields) >= 2, "Nested or malformed FRD field")
            kind = fields[1]
            require(kind in {"DISP", "FORC", "CONTACT", "STRESS", "ERROR"},
                    f"Unexpected FRD field kind {kind}")
            active = {}
            labels = []
        elif active is not None and line.startswith(" -5"):
            require(len(fields) >= 2, "Malformed FRD component label")
            labels.append(fields[1])
        elif active is not None and line.startswith(" -1"):
            require(len(line) >= 13, "Truncated FRD nodal row")
            node = int(line[3:13])
            require(node in node_ids and node not in active, "Unknown or duplicate FRD node")
            values = [base.number(line[index:index + 12])
                      for index in range(13, len(line.rstrip()), 12)]
            width = 6 if kind in {"CONTACT", "STRESS"} else (1 if kind == "ERROR" else 3)
            require(len(values) == width, f"Malformed {kind} component row")
            active[node] = values
        elif active is not None and line.startswith(" -3"):
            require(current_time is not None and identity is not None,
                    f"Untimed FRD {kind} dataset")
            if kind != "ERROR":
                require(active, f"Empty FRD {kind} dataset")
            matches = [state for state in accepted
                       if (state["step"], state["increment"]) == identity
                       and abs(state["total"] - current_time) <= 2e-6]
            require(len(matches) == 1, "FRD field does not match one accepted STA identity")
            require(not any(block["identity"] == identity and block["kind"] == kind
                            for block in blocks), "Duplicate FRD field for accepted state")
            if kind == "DISP":
                require(set(active) == node_ids
                        and labels == ["D1", "D2", "D3", "ALL"],
                        "Incomplete/mislabeled full-mesh DISP dataset")
            elif kind == "FORC":
                require(set(active) == node_ids
                        and labels == ["F1", "F2", "F3", "ALL"],
                        "Incomplete/mislabeled full-mesh FORC dataset")
            elif kind == "STRESS":
                require(set(active) == node_ids and labels == STRESS_LABELS,
                        "Incomplete/mislabeled full-mesh STRESS dataset")
            elif kind == "CONTACT":
                require(labels == CONTACT_LABELS, "Unexpected CONTACT FRD components")
            elif kind == "ERROR":
                require(labels == ["STR(%)"], "Unexpected incidental ERR component")
            summary = {"identity": list(identity), "time": current_time,
                       "kind": kind, "nodes": len(active), "labels": labels}
            if kind == "STRESS":
                summary["component_abs_max"] = [
                    max(abs(values[index]) for values in active.values()) for index in range(6)
                ]
                summary["all_values_finite"] = True
            elif kind == "CONTACT":
                summary.update(COPEN_min=min(row[0] for row in active.values()),
                               COPEN_max=max(row[0] for row in active.values()),
                               CPRESS_min=min(row[3] for row in active.values()),
                               CPRESS_max=max(row[3] for row in active.values()))
            blocks.append(summary)
            active = None
    require(active is None, "Truncated final FRD field")
    for state in accepted:
        identity_key = (state["step"], state["increment"])
        kinds = {block["kind"] for block in blocks if tuple(block["identity"]) == identity_key}
        require(kinds >= {"DISP", "FORC", "STRESS"},
                f"Accepted state lacks full DISP/FORC/STRESS trace: {identity_key}")
    stress = [block for block in blocks if block["kind"] == "STRESS"]
    require(len(stress) == 5, "Expected one complete full-mesh STRESS field per endpoint")
    compression = [block for block in blocks if block["kind"] == "CONTACT"
                   and block["identity"] == [3, 1] and abs(block["time"] - 3.0) <= 2e-6]
    require(len(compression) == 1, "Missing step-3/time-3 CONTACT field at compression")
    return {"status": "PASS", "fields": blocks,
            "stress_state_count": len(stress),
            "full_mesh_stress_coverage": all(row["nodes"] == len(node_ids) for row in stress),
            "compression_contact_field": compression[0]}


def dat_fields(folder: Path, base):
    nodes, parts, faces = base.mesh(folder / "coupon.inp")
    fields = base.dat(folder / "coupon.dat", set(nodes))
    return nodes, parts, faces, fields


def audit_mechanical_dat(folder: Path, expected: dict, accepted: list[dict], base) -> dict:
    nodes, parts, faces, fields = dat_fields(folder, base)
    require(len(fields) == 2 * len(accepted), "DAT does not have exactly U/RF at each accepted state")
    times = [state["total"] for state in accepted]
    require(sorted(set(time for time, _ in fields)) == times,
            "DAT time inventory differs from five accepted states")
    tolerances = expected["inherited_mechanical_gates"]["predeclared_tolerances"]
    profile_limit = tolerances["accepted_state_u3_profile_interface_gap_and_face_warp_mm"]
    area = expected["analytical_reference"]["body_area_mm2"]
    modulus = expected["analytical_reference"]["youngs_modulus_N_per_mm2"]
    compliance_ref = expected["analytical_reference"]["effective_compliance_mm3_per_N"]
    compression = expected["analytical_reference"]["compression"]
    used = set()
    reports = []
    reaction_by_time = {}
    u3_by_time = {}
    displacement_by_time = {}
    force_by_time = {}
    for state, accepted_state in zip(expected["solver_contract"]["states"], accepted):
        total = accepted_state["total"]
        require(abs(float(state["total_time"]) - total) <= 2e-6,
                "DAT and contract endpoint times differ")
        selected = {}
        for quantity in ("displacements", "forces"):
            candidates = [key for key in fields if key[1] == quantity and abs(key[0] - total) <= 2e-6]
            require(len(candidates) == 1 and candidates[0] not in used,
                    f"Missing or duplicate {quantity} DAT state at {total}")
            key = candidates[0]
            used.add(key)
            selected[quantity] = fields[key]
        u = selected["displacements"]
        rf = selected["forces"]
        target = float(state["target_U3_mm"])
        top = faces["top"]
        bottom = faces["bottom"]
        top_u3 = [u[node][2] for node in sorted(top)]
        u_mean = sum(top_u3) / len(top_u3)
        require(max(abs(value - u_mean) for value in top_u3) <= 1e-9,
                f"Prescribed top-face U3 is nonuniform at time {total}")
        q_reaction = sum(rf[node][2] for node in top)
        pressure = max(-target, 0.0) / compliance_ref
        analytic_force = pressure * area
        force_limit = (tolerances["force_relative_error"] * analytic_force
                       + tolerances["force_abs_error_N"])
        top_reaction = base.sum_vector(rf, top)
        bottom_reaction = base.sum_vector(rf, bottom)
        require(abs(top_reaction[2] + analytic_force) <= force_limit
                and abs(bottom_reaction[2] - analytic_force) <= force_limit,
                f"Top/bottom RF disagrees with inherited force oracle at {total}")
        require(base.norm(add(top_reaction, bottom_reaction)) <= force_limit,
                f"Support force closure fails at {total}")
        require(base.norm(top_reaction[:2]) <= force_limit
                and base.norm(bottom_reaction[:2]) <= force_limit,
                f"Tangential support reaction exceeds inherited tolerance at {total}")
        if target >= 0:
            open_limit = tolerances["open_reopen_resultant_support_force_norm_N"]
            require(max(base.norm(top_reaction), base.norm(bottom_reaction)) <= open_limit,
                    f"Open/touch state carries reaction at {total}")
        profile_errors = []
        for node, xyz in nodes.items():
            predicted = (target + pressure * (2.0 - xyz[2]) / modulus
                         if node in parts["UPPER"]
                         else -pressure * (xyz[2] + 2.0) / modulus)
            profile_errors.append(abs(u[node][2] - predicted))
        max_profile = max(profile_errors)
        require(max_profile <= profile_limit,
                f"Inherited axial displacement profile fails at {total}")
        means = {name: sum(u[node][2] for node in face_nodes) / len(face_nodes)
                 for name, face_nodes in faces.items()}
        warp = max(max(u[node][2] for node in face_nodes)
                   - min(u[node][2] for node in face_nodes)
                   for face_nodes in faces.values())
        gap = means["upper_interface"] - means["lower_interface"]
        predicted_gap = target if target >= 0 else -pressure / modulus
        require(abs(gap - predicted_gap) <= profile_limit and warp <= profile_limit,
                f"Inherited interface gap/face warp fails at {total}")
        lower_by_xy = {nodes[node][:2]: node for node in faces["lower_interface"]}
        matched_gap_error = max(abs(u[node][2] - u[lower_by_xy[nodes[node][:2]]][2]
                                   - predicted_gap)
                               for node in faces["upper_interface"])
        require(matched_gap_error <= profile_limit,
                f"Inherited matched-node gap fails at {total}")
        row = {"step": accepted_state["step"], "time": total, "name": state["name"],
               "target_U3_mm": target, "top_RF3_sum_N": q_reaction,
               "top_RF_vector_N": list(top_reaction),
               "bottom_RF_vector_N": list(bottom_reaction),
               "analytic_compression_force_N": analytic_force,
               "max_profile_error_mm": max_profile, "interface_gap_mm": gap,
               "face_warp_mm": warp, "matched_gap_error_mm": matched_gap_error,
               "max_tangential_displacement_diagnostic_mm": max(
                   abs(u[node][dim]) for node in nodes for dim in (0, 1))}
        if state["name"] == "COMPRESSION":
            require(accepted_state["step"] == 3 and abs(total - 3.0) <= 2e-6,
                    "Compression state is not the declared step-3/time-3 endpoint")
            measured_compliance = area * abs(means["top"]) / abs(top_reaction[2])
            compliance_limit = (tolerances["pressure_compliance_relative_error"] * compliance_ref
                                + tolerances["pressure_compliance_abs_error_mm3_per_N"])
            require(abs(measured_compliance - compliance_ref) <= compliance_limit,
                    "Inherited compression pressure compliance fails")
            row["pressure_compliance_mm3_per_N"] = measured_compliance
        reaction_by_time[total] = q_reaction
        u3_by_time[total] = u_mean
        displacement_by_time[total] = u
        force_by_time[total] = rf
        reports.append(row)
    require(used == set(fields), "Unconsumed DAT U/RF evidence")
    return {"status": "PASS", "accepted_state_count": len(reports), "states": reports,
            "reaction_by_time_N": reaction_by_time, "top_u3_by_time_mm": u3_by_time,
            "displacements_by_time": displacement_by_time,
            "forces_by_time": force_by_time,
            "mesh_node_count": len(nodes), "parts": parts, "faces": faces,
            "nodes": nodes, "dat_fields": fields}


def parse_section_reports(dat_text: str, base, expected_times: list[float]) -> dict:
    lines = [" ".join(line.split()) for line in dat_text.splitlines() if line.strip()]
    reports = {}
    for index, line in enumerate(lines):
        match = re.fullmatch(r"statistics for surface set (\w+) and time (\S+)", line)
        if not match:
            continue
        surface = match[1]
        total = base.number(match[2])
        require(surface in {"SLAVE", "MASTER"}, "Unexpected SOF surface")
        matching_times = [value for value in expected_times if abs(total - value) <= 2e-6]
        require(len(matching_times) == 1, "SOF report time is not a unique accepted state")
        key = (surface, matching_times[0])
        require(key not in reports, f"Duplicate SOF report: {key}")
        arrays = []
        for offset, (header, count) in enumerate(SECTION_HEADERS):
            header_index = index + 2 * offset + 1
            value_index = header_index + 1
            require(value_index < len(lines), "Truncated SOF report")
            require(lines[header_index].replace(" ", "") == header.replace(" ", ""),
                    "Unexpected SOF report field header")
            values = [base.number(token) for token in lines[value_index].split()]
            require(len(values) == count, "Malformed SOF component row")
            arrays.append(values)
        reports[key] = {
            "force_N": arrays[0][:3], "moment_origin_N_mm": arrays[0][3:],
            "centroid_mm": arrays[1][:3], "mean_normal": arrays[1][3:],
            "moment_centroid_N_mm": arrays[2], "area_mm2": arrays[3][0],
            "normal_force_N": arrays[3][1], "shear_N": arrays[3][2],
            "torque_N_mm": arrays[3][3], "bending_N_mm": arrays[3][4],
        }
    expected_keys = {(surface, time) for surface in ("SLAVE", "MASTER")
                     for time in expected_times}
    require(set(reports) == expected_keys, "SOF surface/time report inventory is incomplete")
    return reports


def audit_section_reports(folder: Path, expected: dict, mechanics: dict, base) -> dict:
    section_contract = expected["inherited_mechanical_gates"]["section_force_contract"]
    mechanical_tolerances = expected["inherited_mechanical_gates"]["predeclared_tolerances"]
    geometric_tolerance = mechanical_tolerances[
        "accepted_state_u3_profile_interface_gap_and_face_warp_mm"]
    states = accepted_schedule(expected)
    times = [state["total"] for state in states]
    dat_text = (folder / "coupon.dat").read_text(errors="replace")
    reports = parse_section_reports(dat_text, base, times)
    force_abs = mechanical_tolerances["force_abs_error_N"]
    force_rel = mechanical_tolerances["force_relative_error"]
    area_tol = section_contract["area_abs_tolerance_mm2"]
    expected_area = section_contract["expected_area_mm2_each_surface"]
    compression_magnitude = expected["analytical_reference"]["compression"]["top_RF3_sum_N"]
    compression_magnitude = abs(compression_magnitude)
    compression_limit = force_rel * compression_magnitude + force_abs
    open_limit = section_contract["force_sign_and_tolerance"][
        "open_reopen_section_force_norm_N"]
    state_lookup = {state["total"]: state for state in states}
    section_rows = []
    for (surface, total), report in reports.items():
        is_compression = state_lookup[total]["name"] == "COMPRESSION"
        sign = 1.0 if surface == "SLAVE" else -1.0
        force_mag = compression_magnitude if is_compression else 0.0
        limit = compression_limit if is_compression else open_limit
        force_target = [0.0, 0.0, sign * force_mag]
        moment_target = [sign * force_mag, -sign * force_mag, 0.0]
        force_check = {"error_norm": norm(subtract(report["force_N"], force_target)),
                       "limit": limit}
        moment_check = {"error_norm": norm(subtract(report["moment_origin_N_mm"], moment_target)),
                        "limit": compression_limit if is_compression else 0.001}
        require(force_check["error_norm"] <= force_check["limit"],
                f"SOF force vector disagrees with oracle for {surface}/{total}")
        require(moment_check["error_norm"] <= moment_check["limit"],
                f"SOF origin moment disagrees with oracle for {surface}/{total}")
        require(norm(report["moment_centroid_N_mm"]) <= (compression_limit if is_compression else 0.001),
                f"SOF centroid moment exceeds inherited bound for {surface}/{total}")
        require(abs(report["area_mm2"] - expected_area) <= area_tol,
                f"SOF area differs for {surface}/{total}")
        normal_target = [0.0, 0.0, -sign]
        require(norm(subtract(report["mean_normal"], normal_target)) <= geometric_tolerance,
                f"SOF face normal differs for {surface}/{total}")
        face_name = "upper_interface" if surface == "SLAVE" else "lower_interface"
        face_nodes = mechanics["faces"][face_name]
        u = mechanics["displacements_by_time"][total]
        nodes = mechanics["nodes"]
        centroid_target = [sum(nodes[node][dim] + u[node][dim] for node in face_nodes)
                           / len(face_nodes) for dim in range(3)]
        require(norm(subtract(report["centroid_mm"], centroid_target)) <= geometric_tolerance,
                f"SOF deformed centroid differs from nodal geometry for {surface}/{total}")
        expected_normal_scalar = -force_mag
        require(abs(report["normal_force_N"] - expected_normal_scalar) <= limit,
                f"SOF tension-positive normal scalar differs for {surface}/{total}")
        require(abs(report["shear_N"]) <= limit,
                f"SOF shear exceeds inherited bound for {surface}/{total}")
        require(max(abs(report["torque_N_mm"]), abs(report["bending_N_mm"]))
                <= (compression_limit if is_compression else 0.001),
                f"SOF torque/bending differs for {surface}/{total}")
        section_rows.append({"surface": surface, "time": total,
                             "force_check": force_check, "moment_check": moment_check,
                             **report})
    opposed = []
    for total in times:
        slave = reports[("SLAVE", total)]
        master = reports[("MASTER", total)]
        limit = compression_limit if state_lookup[total]["name"] == "COMPRESSION" else 0.001
        force_error = norm(add(slave["force_N"], master["force_N"]))
        moment_error = norm(add(slave["moment_origin_N_mm"], master["moment_origin_N_mm"]))
        require(force_error <= limit and moment_error <= limit,
                f"Opposed SOF force/moment closure fails at {total}")
        opposed.append({"time": total, "force_sum_error_N": force_error,
                        "origin_moment_sum_error_N_mm": moment_error, "limit": limit})
    return {"status": "PASS", "report_count": len(section_rows),
            "reports": section_rows, "opposed_surface_closure": opposed,
            "geometry_tolerance_mm": geometric_tolerance,
            "interpretation": section_contract["result_interpretation"]}


def parse_energy_records(dat_text: str, base) -> dict:
    records = {}
    errors = []
    lines = dat_text.splitlines()
    channel_pattern = re.compile(r"total internal energy for set (UPPER|LOWER) and time\s+(\S+)",
                                 re.IGNORECASE)
    cels_pattern = re.compile(r"total contact spring energy for time\s+(\S+)", re.IGNORECASE)
    for index, line in enumerate(lines):
        header = " ".join(line.split())
        match = channel_pattern.fullmatch(header)
        if match:
            channel, time_token = match.groups()
            channel = channel.upper()
        else:
            match = cels_pattern.fullmatch(header)
            if not match:
                continue
            channel, time_token = "CELS", match.group(1)
        try:
            total = base.number(time_token)
        except Exception as exc:
            errors.append({"channel": channel, "time": None,
                           "message": f"invalid time token: {exc}"})
            continue
        value_index = index + 1
        while value_index < len(lines) and not lines[value_index].strip():
            value_index += 1
        if value_index >= len(lines):
            errors.append({"channel": channel, "time": total,
                           "message": "missing numeric row"})
            continue
        fields = lines[value_index].split()
        if len(fields) != 1:
            errors.append({"channel": channel, "time": total,
                           "message": "malformed numeric row"})
            continue
        try:
            value = base.number(fields[0])
        except Exception as exc:
            errors.append({"channel": channel, "time": total,
                           "message": f"invalid value: {exc}"})
            continue
        state = records.setdefault(total, {})
        if channel in state:
            errors.append({"channel": channel, "time": total,
                           "message": "duplicate channel"})
            continue
        state[channel] = value
    return {"records": records, "errors": errors}


def audit_energy_channels(dat_text: str, expected: dict, base) -> dict:
    parsed = parse_energy_records(dat_text, base)
    errors = list(parsed["errors"])
    records = parsed["records"]
    states = accepted_schedule(expected)
    times = [state["total"] for state in states]
    unexpected_times = sorted(time for time in records
                              if not any(abs(time - wanted) <= 2e-6 for wanted in times))
    for total in unexpected_times:
        errors.append({"channel": None, "time": total,
                       "message": "energy output at an unaccepted time"})
    analytic = expected["analytical_reference"]["compression"]
    component_abs = expected["energy_output_contract"]["endpoint_component_absolute_tolerance_N_mm"]
    component_rel = expected["energy_output_contract"]["endpoint_component_relative_tolerance"]
    by_channel = {"UPPER": [], "LOWER": [], "CELS": []}
    combined_rows = []
    values_by_time = {}
    energy_targets = {}
    for state in states:
        total = state["total"]
        compression = state["name"] == "COMPRESSION"
        target_each = analytic["body_ELSE_each_N_mm"] if compression else 0.0
        target_cels = analytic["contact_CELS_N_mm"] if compression else 0.0
        target_combined = float(state["expected_energy"])
        energy_targets[total] = {"UPPER": target_each, "LOWER": target_each,
                                 "CELS": target_cels, "COMBINED": target_combined}
        matching_records = [records[key] for key in records if abs(key - total) <= 2e-6]
        channels = matching_records[0] if len(matching_records) == 1 else {}
        if len(matching_records) > 1:
            errors.append({"channel": None, "time": total,
                           "message": "multiple energy time keys match one accepted state"})
        values_by_time[total] = channels
        for channel, target in (("UPPER", target_each), ("LOWER", target_each),
                                ("CELS", target_cels)):
            if channel not in channels:
                by_channel[channel].append({"time": total, "pass": False,
                                            "error": f"missing {channel} record"})
                continue
            error = abs(channels[channel] - target)
            limit = component_abs + component_rel * abs(target)
            comparison = {"actual": channels[channel], "reference": target,
                          "absolute_error": error, "limit": limit,
                          "pass": error <= limit}
            comparison["time"] = total
            by_channel[channel].append(comparison)
        if set(channels) != {"UPPER", "LOWER", "CELS"}:
            combined_rows.append({"time": total, "pass": False,
                                  "error": "combined total unavailable: incomplete ELSE/CELS channels"})
            continue
        combined = channels["UPPER"] + channels["LOWER"] + channels["CELS"]
        error = abs(combined - target_combined)
        limit = component_abs + component_rel * abs(target_combined)
        comparison = {"actual": combined, "reference": target_combined,
                      "absolute_error": error, "limit": limit,
                      "pass": error <= limit}
        comparison["time"] = total
        comparison["components_N_mm"] = dict(channels)
        combined_rows.append(comparison)
    channel_errors = {channel: [item for item in errors if item["channel"] == channel]
                      for channel in ("UPPER", "LOWER", "CELS")}
    for channel, channel_error_rows in channel_errors.items():
        if channel_error_rows and by_channel[channel]:
            by_channel[channel][0]["parse_errors"] = channel_error_rows
            by_channel[channel][0]["pass"] = False
    body_pass = all(row.get("pass") is True for name in ("UPPER", "LOWER")
                    for row in by_channel[name]) and not channel_errors["UPPER"] \
        and not channel_errors["LOWER"]
    cels_pass = all(row.get("pass") is True for row in by_channel["CELS"]) \
        and not channel_errors["CELS"]
    combined_pass = all(row.get("pass") is True for row in combined_rows) and not errors
    return {"body_ELSE": {"status": "PASS" if body_pass else "FAIL",
                           "upper": by_channel["UPPER"], "lower": by_channel["LOWER"]},
            "penalty_CELS": {"status": "PASS" if cels_pass else "FAIL",
                             "states": by_channel["CELS"],
                             "scope": "penalty known-answer channel only"},
            "combined_ELSE_plus_CELS": {"status": "PASS" if combined_pass else "FAIL",
                                        "states": combined_rows},
            "mortar_CELS": {"status": "EXCLUDED_NOT_RUN", "accepted_as_zero": False},
            "energy_parse_errors": errors, "values_by_time": values_by_time,
            "energy_targets_by_time": energy_targets,
            "energy_complete": (body_pass and cels_pass and combined_pass and not errors)}


def work_energy_audit(u_values: list[float], q_values: list[float],
                      energy_values: list[float], analytic_segment_work: list[float],
                      relative_tolerance: float, absolute_tolerance: float) -> dict:
    require(len(u_values) == len(q_values) == len(energy_values) == 6,
            "Work history must include the initial reference plus five accepted states")
    require(len(analytic_segment_work) == 5, "Expected five analytical segment work values")
    require(all(math.isfinite(value) for value in u_values + q_values + energy_values
                + analytic_segment_work), "Nonfinite work/energy history input")
    segment_rows = []
    cumulative = 0.0
    segment_pass = True
    for index, analytic in enumerate(analytic_segment_work):
        du = u_values[index + 1] - u_values[index]
        work = 0.5 * (q_values[index] + q_values[index + 1]) * du
        delta_energy = energy_values[index + 1] - energy_values[index]
        closure = close_with_limit(work, delta_energy,
                                   absolute_tolerance, relative_tolerance)
        analytical = close_with_limit(work, analytic,
                                      absolute_tolerance, relative_tolerance)
        cumulative += work
        state_energy_target = sum(analytic_segment_work[:index + 1])
        cumulative_check = close_with_limit(cumulative, state_energy_target,
                                            absolute_tolerance, relative_tolerance)
        passed = closure["pass"] and analytical["pass"] and cumulative_check["pass"]
        segment_pass = segment_pass and passed
        segment_rows.append({"segment_index": index + 1,
                             "du_mm": du, "trapezoidal_reaction_work_N_mm": work,
                             "stored_energy_change_N_mm": delta_energy,
                             "analytical_segment_work_N_mm": analytic,
                             "work_vs_delta_energy": closure,
                             "work_vs_analytical": analytical,
                             "cumulative_work_vs_analytical_state_energy": cumulative_check,
                             "pass": passed})
    return {"status": "PASS" if segment_pass else "FAIL",
            "relative_tolerance": relative_tolerance,
            "absolute_tolerance_N_mm": absolute_tolerance,
            "segments": segment_rows,
            "method": "independent top reaction trapezoid versus observed ELSE+CELS change and analytical work; no residual-derived component"}


def audit_work_from_outputs(folder: Path, expected: dict, energy: dict, base) -> dict:
    nodes, parts, faces, fields = dat_fields(folder, base)
    accepted = accepted_schedule(expected)
    top_nodes = faces["top"]
    actual_u = []
    actual_q = []
    actual_e = []
    initial = expected["solver_contract"]["initial_reference"]
    actual_u.append(float(initial["top_U3_mm"]))
    actual_q.append(float(initial["top_RF3_sum_N"]))
    actual_e.append(float(initial["stored_energy_N_mm"]))
    for state in accepted:
        ukey = next((key for key in fields if key[1] == "displacements"
                     and abs(key[0] - state["total"]) <= 2e-6), None)
        rkey = next((key for key in fields if key[1] == "forces"
                     and abs(key[0] - state["total"]) <= 2e-6), None)
        require(ukey is not None and rkey is not None, "Work history lacks U/RF at an accepted state")
        u = fields[ukey]
        rf = fields[rkey]
        top_u3 = [u[node][2] for node in sorted(top_nodes)]
        mean_u = sum(top_u3) / len(top_u3)
        require(max(abs(value - mean_u) for value in top_u3) <= 1e-9,
                "Trapezoidal work requires uniform top U3 at every endpoint")
        actual_u.append(mean_u)
        actual_q.append(sum(rf[node][2] for node in top_nodes))
        channels = energy["values_by_time"].get(state["total"], {})
        require(set(channels) == {"UPPER", "LOWER", "CELS"},
                f"Stored energy is incomplete at {state['total']}; work gate unavailable")
        actual_e.append(channels["UPPER"] + channels["LOWER"] + channels["CELS"])
    analytical_segments = [float(state["analytical_segment_work_N_mm"])
                           for state in expected["solver_contract"]["states"]]
    contract = expected["work_energy_contract"]
    evidence = work_energy_audit(actual_u, actual_q, actual_e, analytical_segments,
                                 contract["relative_tolerance"],
                                 contract["absolute_work_tolerance_N_mm"])
    evidence.update({"top_U3_mm": actual_u, "top_RF3_sum_N": actual_q,
                     "combined_ELSE_plus_CELS_N_mm": actual_e,
                     "initial_reference_included": True})
    return evidence


def audit_pair_records(dat_text: str, expected: dict) -> dict:
    pair_parser = load_module("touch_work_pair_output", HERE / "pair_output.py")
    records = pair_parser.parse_pairs(dat_text)
    require(len(records) == 15, "Expected exactly 15 pair-resultant records")
    pair_force = expected["analytical_reference"]["pair_force"]
    surfaces = pair_force["selected_surfaces"]
    target_times = [state["total_time"] for state in expected["solver_contract"]["states"]]
    required_identities = {(surfaces["slave"], surfaces["master"], time, quantity)
                           for time in target_times for quantity in ("CF", "CFN", "CFS")}
    found = set()
    by_identity = {}
    for record in records:
        require(record["slave"] == surfaces["slave"]
                and record["master"] == surfaces["master"],
                "Pair result was emitted for an unexpected surface pair")
        matching_times = [time for time in target_times if abs(record["time"] - time) <= 2e-6]
        require(len(matching_times) == 1, "Pair record time is outside a unique accepted state")
        identity = (record["slave"], record["master"], matching_times[0], record["quantity"])
        require(identity not in found, f"Duplicate accepted pair result: {identity}")
        require(len(record["force_N"]) == len(record["moment_N_mm"]) == 3
                and all(math.isfinite(value) for value in record["force_N"] + record["moment_N_mm"]),
                "Pair force or moment vector is incomplete/nonfinite")
        found.add(identity)
        by_identity[identity] = record
    require(found == required_identities, "Pair CF/CFN/CFS time/quantity coverage is incomplete")
    force_rel = pair_force["force_relative_error"]
    force_abs = pair_force["force_abs_error_N"]
    zero_force_abs = pair_force["zero_force_abs_error_N"]
    moment_rel = pair_force["moment_relative_error"]
    moment_abs = pair_force["moment_abs_error_N_mm"]
    moment_reference = pair_force["moment_reference_scale_N_mm"]
    reports = []
    all_pass = True
    for state in expected["solver_contract"]["states"]:
        time = float(state["total_time"])
        compressed = state["name"] == "COMPRESSION"
        force_targets = {
            "CF": pair_force["compression_CF_N"] if compressed else pair_force["open_touch_CF_CFN_CFS_N"],
            "CFN": pair_force["compression_CFN_N"] if compressed else pair_force["open_touch_CF_CFN_CFS_N"],
            "CFS": pair_force["compression_CFS_N"] if compressed else pair_force["open_touch_CF_CFN_CFS_N"],
        }
        moment_targets = {
            "CF": pair_force["compression_CF_origin_moment_N_mm"] if compressed else pair_force["open_touch_CF_CFN_CFS_origin_moment_N_mm"],
            "CFN": pair_force["compression_CFN_origin_moment_N_mm"] if compressed else pair_force["open_touch_CF_CFN_CFS_origin_moment_N_mm"],
            "CFS": pair_force["compression_CFS_origin_moment_N_mm"] if compressed else pair_force["open_touch_CF_CFN_CFS_origin_moment_N_mm"],
        }
        state_rows = []
        for quantity in ("CF", "CFN", "CFS"):
            identity = (surfaces["slave"], surfaces["master"], time, quantity)
            record = by_identity[identity]
            force_target = force_targets[quantity]
            force_limit = (force_rel * 400.0 + force_abs) if compressed else zero_force_abs
            force_error = norm(subtract(record["force_N"], force_target))
            moment_target = moment_targets[quantity]
            moment_limit = (moment_rel * moment_reference + moment_abs) if compressed else moment_abs
            moment_error = norm(subtract(record["moment_N_mm"], moment_target))
            require(force_error <= force_limit,
                    f"{quantity} vector differs from known answer at time {time}")
            require(moment_error <= moment_limit,
                    f"{quantity} origin moment differs from known answer at time {time}")
            row = {"quantity": quantity, "force_N": record["force_N"],
                   "force_error_norm_N": force_error, "force_limit_N": force_limit,
                   "moment_N_mm": record["moment_N_mm"],
                   "moment_error_norm_N_mm": moment_error,
                   "moment_limit_N_mm": moment_limit, "pass": True}
            state_rows.append(row)
        if compressed:
            cfn = by_identity[(surfaces["slave"], surfaces["master"], time, "CFN")]["force_N"]
            projection = dot(cfn, pair_force["mean_slave_normal_unit"])
            expected_projection = pair_force["CFN_projection_on_mean_normal_N_tension_positive"]
            projection_error = abs(projection - expected_projection)
            require(projection_error <= force_rel * 400.0 + force_abs,
                    "CFN tension-positive projection has wrong compression sign/magnitude")
        else:
            projection = 0.0
            projection_error = 0.0
        # Frictionless decomposition: CF equals its normal plus shear components.
        cf = by_identity[(surfaces["slave"], surfaces["master"], time, "CF")]["force_N"]
        cfn = by_identity[(surfaces["slave"], surfaces["master"], time, "CFN")]["force_N"]
        cfs = by_identity[(surfaces["slave"], surfaces["master"], time, "CFS")]["force_N"]
        decomposition_error = norm(subtract(cf, add(cfn, cfs)))
        require(decomposition_error <= (force_rel * 400.0 + force_abs if compressed else zero_force_abs),
                f"CF/CFN/CFS decomposition differs at time {time}")
        all_pass = all_pass and all(row["pass"] for row in state_rows)
        reports.append({"time": time, "name": state["name"], "components": state_rows,
                        "CFN_projection_on_mean_normal_N": projection,
                        "CFN_projection_error_N": projection_error,
                        "decomposition_error_N": decomposition_error})
    return {"status": "PASS" if all_pass else "FAIL", "record_count": len(records),
            "identity_count": len(found), "states": reports,
            "zero_area_diagnostics_ignored": True,
            "interpretation": "Pair force/moment output known-answer only; not a strength/capacity result"}


def component_gate(function):
    try:
        result = function()
        if isinstance(result, dict):
            return {**result, "status": result.get("status", "PASS"), "value": result}
        return {"status": "PASS", "value": result}
    except Exception as exc:
        return {"status": "FAIL", "error": str(exc)}


def public_component(result: dict, omitted: set[str] | None = None) -> dict:
    omitted = (omitted or set()) | {"value"}
    return {key: value for key, value in result.items() if key not in omitted}


def assemble_case_result(envelope: dict, convergence: dict, mechanical_dat: dict,
                         frd: dict, sof: dict, body: dict, cels: dict,
                         combined: dict, work: dict, pair: dict,
                         energy_parse_errors: list | None = None) -> dict:
    mechanical_ok = all(result.get("status") == "PASS"
                        for result in (convergence, mechanical_dat, frd, sof))
    energy_ok = (body.get("status") == "PASS" and cels.get("status") == "PASS"
                 and combined.get("status") == "PASS" and work.get("status") == "PASS")
    pair_ok = pair.get("status") == "PASS"
    case_ok = mechanical_ok and energy_ok and pair_ok
    dat_public = public_component(mechanical_dat, {
        "value", "reaction_by_time_N", "top_u3_by_time_mm", "displacements_by_time",
        "forces_by_time", "mesh_node_count", "parts", "faces", "nodes", "dat_fields",
    })
    return {
        "execution_envelope": public_component(envelope),
        "inherited_mechanical_gates": {
            "status": "PASS" if mechanical_ok else "FAIL",
            "accepted_history": public_component(convergence),
            "DAT_profile_force_compliance": dat_public,
            "FRD_full_mesh_trace": public_component(frd),
            "SOF_section_output": public_component(sof),
            "mechanical_acceptance": False,
            "joint_acceptance": False,
            "interpretation": "Inherited method-fixture output gates only; no mechanical or joint acceptance",
        },
        "body_ELSE": body,
        "penalty_CELS": cels,
        "combined_energy": combined,
        "energy_parse_errors": energy_parse_errors or [],
        "reaction_work": public_component(work),
        "pair_CF_CFN_CFS": public_component(pair),
        "mortar_CELS": {"status": "EXCLUDED_NOT_RUN", "accepted_as_zero": False},
        "work_energy_acceptance": False,
        "mechanical_acceptance": False,
        "joint_acceptance": False,
        "release": False,
        "status": "PASS_TOUCH_WORK_METHOD_FIXTURE" if case_ok else "FAIL",
    }


def audit_case(folder: Path, expected: dict, freeze: dict, top_execution: dict, base) -> dict:
    # The execution envelope is a prerequisite for interpreting any output.
    envelope_result = component_gate(lambda: audit_case_envelope(expected, freeze, top_execution))
    if envelope_result["status"] == "FAIL":
        fail = {"status": "FAIL", "error": envelope_result["error"]}
        return assemble_case_result(envelope_result, fail, fail, fail, fail,
                                    fail, fail, fail, fail, fail)
    folder, run = envelope_result["value"]
    del run
    accepted = accepted_schedule(expected)
    convergence = component_gate(lambda: audit_convergence(folder, base, expected))
    if convergence["status"] == "PASS":
        accepted_for_frd = convergence["accepted_states"]
    else:
        accepted_for_frd = accepted
    mechanical_dat = component_gate(lambda: audit_mechanical_dat(folder, expected, accepted, base))
    frd = component_gate(lambda: parse_frd(folder / "coupon.frd", accepted_for_frd,
                                          set(base.mesh(folder / "coupon.inp")[0]), base))
    if mechanical_dat["status"] == "PASS":
        mechanics_value = mechanical_dat["value"]
        sof = component_gate(lambda: audit_section_reports(folder, expected, mechanics_value, base))
    else:
        mechanics_value = None
        sof = {"status": "FAIL", "error": "SOF centroid check requires complete mechanical DAT evidence"}
    mechanical_components_pass = all(item.get("status") == "PASS"
                                     for item in (convergence, mechanical_dat, frd, sof))
    energy_gate = component_gate(lambda: audit_energy_channels(
        (folder / "coupon.dat").read_text(errors="replace"), expected, base))
    if energy_gate["status"] == "PASS":
        energy_detail = energy_gate["value"]
        body = energy_detail["body_ELSE"]
        cels = energy_detail["penalty_CELS"]
        combined = energy_detail["combined_ELSE_plus_CELS"]
    else:
        energy_detail = {}
        body = {"status": "FAIL", "error": energy_gate["error"]}
        cels = {"status": "FAIL", "error": energy_gate["error"]}
        combined = {"status": "FAIL", "error": energy_gate["error"]}
    if energy_gate["status"] == "PASS" and mechanics_value is not None:
        work = component_gate(lambda: audit_work_from_outputs(folder, expected,
                                                              energy_detail, base))
    else:
        work = {"status": "FAIL", "error": "Work gate requires complete DAT and all ELSE/CELS channels"}
    pair = component_gate(lambda: audit_pair_records(
        (folder / "coupon.dat").read_text(errors="replace"), expected))
    return assemble_case_result(
        envelope_result, convergence, mechanical_dat, frd, sof, body, cels,
        combined, work, pair, energy_detail.get("energy_parse_errors", []))


def audit() -> dict:
    expected, freeze, execution, packet = audit_packet_and_terminal()
    base = load_module("touch_work_fullstep_mechanical_helpers", FULLSTEP / "verifier.py")
    try:
        case_result = audit_case(HERE / "output" / CASE, expected, freeze, execution, base)
    except Exception as exc:
        case_result = {"status": "FAIL", "error": str(exc),
                       "mortar_CELS": {"status": "EXCLUDED_NOT_RUN", "accepted_as_zero": False},
                       "mechanical_acceptance": False, "work_energy_acceptance": False,
                       "joint_acceptance": False, "release": False}
    passed = case_result.get("status") == "PASS_TOUCH_WORK_METHOD_FIXTURE"
    return {
        "schema": "calculix_penalty_exact_touch_work_audit/v1",
        "status": "PASS_TOUCH_WORK_METHOD_FIXTURE" if passed else "FAIL",
        "case": case_result,
        "lineage_audit": packet["lineage"],
        "parent_review": packet["parent_review"],
        "mechanical_acceptance": False,
        "work_energy_acceptance": False,
        "joint_acceptance": False,
        "release": False,
        "verifier_sha256": sha(Path(__file__)),
        "execution_sha256": sha(HERE / "execution.json"),
        "interpretation": "A method-fixture pass validates only this two-body penalty output method; it is not joint acceptance or release.",
    }


def synthetic_energy_parser_preflight(base) -> dict:
    valid = """total internal energy for set UPPER and time 1.0000000E+00
0.400000E+00
total internal energy for set LOWER and time 1.0000000E+00
0.400000E+00
total contact spring energy for time 1.0000000E+00
0.200000E+00
"""
    parsed = parse_energy_records(valid, base)
    require(not parsed["errors"] and parsed["records"][1.0]
            == {"UPPER": 0.4, "LOWER": 0.4, "CELS": 0.2},
            "Synthetic ELSE/CELS parser oracle failed")
    cases = {
        "missing_lower": valid.replace(
            "total internal energy for set LOWER and time 1.0000000E+00\n0.400000E+00\n", ""),
        "duplicate_cels": valid + "total contact spring energy for time 1.0000000E+00\n0.200000E+00\n",
        "nonfinite_cels": valid.replace("0.200000E+00", "NaN"),
    }
    rejected = {}
    for name, text in cases.items():
        result = parse_energy_records(text, base)
        if name == "missing_lower":
            rejected[name] = "LOWER" not in result["records"].get(1.0, {})
        else:
            rejected[name] = bool(result["errors"])
    require(all(rejected.values()), "Missing/duplicate/nonfinite energy channel was not rejected")
    return {"status": "PASS_SYNTHETIC_ENERGY_PARSER", "records": 3,
            "rejected": rejected, "native_output_qualified": False}


def synthetic_energy_gate_preflight(expected: dict, base) -> dict:
    def deck_text(override=None, omit=None):
        override = override or {}
        omit = omit or set()
        rows = []
        for state in expected["solver_contract"]["states"]:
            time = float(state["total_time"])
            compressed = state["name"] == "COMPRESSION"
            values = {"UPPER": 0.4 if compressed else 0.0,
                      "LOWER": 0.4 if compressed else 0.0,
                      "CELS": 0.2 if compressed else 0.0}
            values.update(override.get(time, {}))
            for channel in ("UPPER", "LOWER", "CELS"):
                if (time, channel) in omit:
                    continue
                if channel == "CELS":
                    rows.append(f"total contact spring energy for time {time:.7E}")
                else:
                    rows.append(f"total internal energy for set {channel} and time {time:.7E}")
                rows.append(f"{values[channel]:.6E}")
        return "\n".join(rows) + "\n"

    good = audit_energy_channels(deck_text(), expected, base)
    require(good["body_ELSE"]["status"] == "PASS"
            and good["penalty_CELS"]["status"] == "PASS"
            and good["combined_ELSE_plus_CELS"]["status"] == "PASS"
            and good["energy_complete"],
            "Five-state separated energy gate synthetic did not pass")
    bad_cels = audit_energy_channels(
        deck_text(override={3.0: {"CELS": 0.25}}), expected, base)
    require(bad_cels["body_ELSE"]["status"] == "PASS"
            and bad_cels["penalty_CELS"]["status"] == "FAIL"
            and bad_cels["combined_ELSE_plus_CELS"]["status"] == "FAIL",
            "CELS mismatch was not isolated from passing ELSE channels")
    missing_lower = audit_energy_channels(
        deck_text(omit={(3.0, "LOWER")}), expected, base)
    require(missing_lower["body_ELSE"]["status"] == "FAIL"
            and missing_lower["penalty_CELS"]["status"] == "PASS"
            and missing_lower["combined_ELSE_plus_CELS"]["status"] == "FAIL",
            "Missing lower ELSE was not isolated from passing CELS")
    return {"status": "PASS_SYNTHETIC_FIVE_STATE_ENERGY_GATES",
            "valid_channels": {"body_ELSE": good["body_ELSE"]["status"],
                               "penalty_CELS": good["penalty_CELS"]["status"],
                               "combined": good["combined_ELSE_plus_CELS"]["status"]},
            "isolated_failures": {
                "CELS_mismatch": {"body_ELSE": bad_cels["body_ELSE"]["status"],
                                  "penalty_CELS": bad_cels["penalty_CELS"]["status"],
                                  "combined": bad_cels["combined_ELSE_plus_CELS"]["status"]},
                "missing_lower_ELSE": {"body_ELSE": missing_lower["body_ELSE"]["status"],
                                       "penalty_CELS": missing_lower["penalty_CELS"]["status"],
                                       "combined": missing_lower["combined_ELSE_plus_CELS"]["status"]},
            }, "native_output_qualified": False}


def synthetic_frd_preflight(expected: dict, base) -> dict:
    node_ids = set(base.mesh(FULLSTEP / "input/penalty_c3d10.inp")[0])
    accepted = accepted_schedule(expected)
    labels = {"DISP": ["D1", "D2", "D3", "ALL"],
              "FORC": ["F1", "F2", "F3", "ALL"],
              "STRESS": STRESS_LABELS, "CONTACT": CONTACT_LABELS}
    width = {"DISP": 3, "FORC": 3, "STRESS": 6, "CONTACT": 6}

    def field(index, state, kind):
        rows = [f"    1PSTEP {index} {state['increment']} {state['step']}",
                f"  100CL  101 {state['total']:.9f}          54                     0    1           1",
                f" -4  {kind}      {width[kind]}    1"]
        rows.extend(f" -5  {label}" for label in labels[kind])
        values = "".join(f"{0.0:12.5E}" for _ in range(width[kind]))
        rows.extend(f" -1{node:10d}{values}" for node in sorted(node_ids))
        rows.append(" -3")
        return "\n".join(rows)

    def complete_text(include_stress_at_step5=True, swapped_step2=False,
                      nonfinite_stress=False):
        output = []
        dataset = 1
        for state in accepted:
            current = dict(state)
            if swapped_step2 and state["step"] == 2:
                current["step"], current["increment"] = state["increment"], state["step"]
            for kind in ("DISP", "FORC", "STRESS"):
                if kind == "STRESS" and state["step"] == 5 and not include_stress_at_step5:
                    continue
                block = field(dataset, current, kind)
                if nonfinite_stress and kind == "STRESS" and state["step"] == 3:
                    block = block.replace(f"{0.0:12.5E}", f"{'NaN':>12}", 1)
                output.append(block)
                dataset += 1
            if state["step"] == 3:
                output.append(field(dataset, current, "CONTACT"))
                dataset += 1
        return "\n".join(output) + "\n"

    good = parse_frd(complete_text(), accepted, node_ids, base)
    require(good["status"] == "PASS" and good["stress_state_count"] == 5,
            "Synthetic five-state FRD coverage failed")
    rejected = {}
    for name, text in {
        "swapped_step_inc_identity": complete_text(swapped_step2=True),
        "missing_final_stress": complete_text(include_stress_at_step5=False),
        "nonfinite_stress": complete_text(nonfinite_stress=True),
    }.items():
        try:
            parse_frd(text, accepted, node_ids, base)
        except ValueError:
            rejected[name] = True
        else:
            rejected[name] = False
    require(all(rejected.values()), "Invalid FRD state/coverage/value passed synthetic checks")
    return {"status": "PASS_SYNTHETIC_FIVE_STATE_FRD", "stress_states": 5,
            "rejected": rejected, "native_output_qualified": False}


def synthetic_assembly_preflight() -> dict:
    opaque = {"status": "PASS", "value": (Path("/synthetic"), object())}
    convergence = {"status": "PASS", "accepted_states": [], "value": object()}
    mechanics = {"status": "PASS", "accepted_state_count": 5, "states": [],
                 "parts": {"UPPER": {1}}, "dat_fields": {(1.0, "displacements"): {}},
                 "value": object()}
    frd = {"status": "PASS", "fields": [], "value": object()}
    sof = {"status": "PASS", "reports": [], "value": object()}
    body = {"status": "PASS", "upper": [], "lower": []}
    cels = {"status": "PASS", "states": []}
    combined = {"status": "PASS", "states": []}
    work = {"status": "PASS", "segments": [], "value": object()}
    pair = {"status": "PASS", "states": [], "value": object()}
    result = assemble_case_result(opaque, convergence, mechanics, frd, sof,
                                  body, cels, combined, work, pair)
    encoded = json.dumps(result, allow_nan=False)
    require(json.loads(encoded)["status"] == "PASS_TOUCH_WORK_METHOD_FIXTURE",
            "Synthetic assembled case report is not JSON-safe or did not pass")
    fail_result = assemble_case_result(opaque, convergence, mechanics, frd, sof,
                                       body, {"status": "FAIL"},
                                       {"status": "FAIL"}, work, pair)
    require(fail_result["status"] == "FAIL"
            and fail_result["work_energy_acceptance"] is False
            and fail_result["joint_acceptance"] is False,
            "A missing energy channel was not prevented from overall acceptance")
    json.dumps(fail_result, allow_nan=False)
    return {"status": "PASS_SYNTHETIC_AUDIT_ASSEMBLY",
            "json_allow_nan_false": True,
            "energy_failure_blocks_overall_pass": True,
            "acceptance_flags_remain_false": True}


def synthetic_preflight() -> dict:
    expected = read_json(HERE / "expected.json")
    base = load_module("touch_work_preflight_base_helpers", FULLSTEP / "verifier.py")
    pair_parser = load_module("touch_work_pair_preflight", HERE / "pair_output.py")
    pair = pair_parser.synthetic_preflight()
    displacement = [0.0, 0.001, 0.0, -0.005, 0.0, 0.001]
    reaction = [0.0, 0.0, 0.0, -400.0, 0.0, 0.0]
    energy = [0.0, 0.0, 0.0, 1.0, 0.0, 0.0]
    analytic = [0.0, 0.0, 1.0, -1.0, 0.0]
    contract = expected["work_energy_contract"]
    good = work_energy_audit(displacement, reaction, energy, analytic,
                             contract["relative_tolerance"],
                             contract["absolute_work_tolerance_N_mm"])
    require(good["status"] == "PASS", "Synthetic analytical exact-touch work failed")
    wrong_sign = reaction.copy()
    wrong_sign[3] = 400.0
    sign_case = work_energy_audit(displacement, wrong_sign, energy, analytic,
                                  contract["relative_tolerance"],
                                  contract["absolute_work_tolerance_N_mm"])
    require(sign_case["status"] == "FAIL",
            "Wrong-sign reaction synthetic unexpectedly passed work gates")
    rejected = {}
    for name, inputs in {
        "missing_state": (displacement[:-1], reaction, energy, analytic),
        "nonfinite_reaction": (displacement, reaction[:3] + [float("nan")] + reaction[4:], energy, analytic),
    }.items():
        try:
            work_energy_audit(*inputs, contract["relative_tolerance"],
                              contract["absolute_work_tolerance_N_mm"])
        except (ValueError, TypeError):
            rejected[name] = True
        else:
            rejected[name] = False
    require(all(rejected.values()), "Missing/nonfinite work history was accepted")
    energy_parser = synthetic_energy_parser_preflight(base)
    energy_gates = synthetic_energy_gate_preflight(expected, base)
    frd = synthetic_frd_preflight(expected, base)
    assembly = synthetic_assembly_preflight()
    return {"status": "PASS_SYNTHETIC_TOUCH_WORK_PREFLIGHT",
            "native_run_performed": False, "freeze_created": False,
            "analytical_work_energy": good,
            "wrong_sign_rejected": True,
            "rejected_incomplete_work_histories": rejected,
            "energy_parser": energy_parser, "energy_gates": energy_gates,
            "frd_parser": frd, "case_result_assembly": assembly,
            "pair_parser": pair}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--preflight", action="store_true",
                        help="Run only synthetic parsers and analytical known-answer checks")
    parser.add_argument("--write", action="store_true",
                        help="Write verifier.json after a completed run")
    args = parser.parse_args()
    if args.preflight:
        result = synthetic_preflight()
        exit_code = 0
    else:
        try:
            result = audit()
        except Exception as exc:
            result = {"schema": "calculix_penalty_exact_touch_work_audit/v1",
                      "status": "FAIL", "error": str(exc),
                      "mechanical_acceptance": False, "work_energy_acceptance": False,
                      "joint_acceptance": False, "release": False}
        exit_code = 0 if result.get("status") == "PASS_TOUCH_WORK_METHOD_FIXTURE" else 1
    if args.write:
        output = HERE / "verifier.json"
        require(not output.exists(), "Refusing to overwrite verifier.json")
        with output.open("x") as stream:
            json.dump(result, stream, indent=2, sort_keys=True)
            stream.write("\n")
    print(json.dumps(result, sort_keys=True))
    raise SystemExit(exit_code)
