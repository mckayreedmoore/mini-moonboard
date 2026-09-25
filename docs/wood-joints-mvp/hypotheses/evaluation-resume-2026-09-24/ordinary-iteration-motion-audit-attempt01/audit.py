"""Audit complete CalculiX trial-displacement fields from one terminated run.

Run from the repository root after the parent has recorded terminal status.
This script reads the immutable run artifacts and writes only to this audit
folder. It runs no solver and imports no CAD.
"""

from __future__ import annotations

import hashlib
import json
import math
import re
from pathlib import Path


ROOT = Path.cwd().resolve()
BASE = ROOT / "docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24"
RUN = BASE / "ordinary-transient-checkpoint-attempt01"
PILOT = BASE / "ordinary-transient-pilot-attempt03"
OUT = BASE / "ordinary-iteration-motion-audit-attempt01"
PILOT_Q_MM = 6.989744242963423e-6
LATE_WINDOW = 5
EXPECTED_STEP = 1
EXPECTED_INCREMENT = 1
TARGET_END_TIME_S = 0.0025


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def require_hash(path: Path, expected: str, label: str) -> str:
    actual = sha256(path)
    if actual != expected:
        raise ValueError(f"{label} hash mismatch: {actual} != {expected}")
    return actual


def parse_nset(path: Path, name: str) -> set[int]:
    lines = path.read_text(encoding="ascii").splitlines()
    start = next((i for i, line in enumerate(lines)
                  if line.strip().upper() == f"*NSET,NSET={name}"), None)
    if start is None:
        raise ValueError(f"{name} is absent from {path.name}")
    nodes: set[int] = set()
    for line in lines[start + 1:]:
        if line.startswith("*"):
            break
        for token in line.split(","):
            token = token.strip()
            if token:
                node = int(token)
                if node in nodes:
                    raise ValueError(f"duplicate node {node} in {name}")
                nodes.add(node)
    if not nodes:
        raise ValueError(f"{name} is empty")
    return nodes


def parse_weights(path: Path) -> tuple[list[str], list[dict[int, tuple[float, float, float]]]]:
    actuator = json.loads(path.read_text())
    distributions = actuator["owner_unit_wrench_distributions"]
    owner_names = actuator["owner_order_positive_then_negative"]
    if len(distributions) != 2 or len(owner_names) != 2:
        raise ValueError("expected the frozen two-owner unit-load pattern")
    owner_weights: list[dict[int, tuple[float, float, float]]] = []
    all_nodes: set[int] = set()
    for distribution in distributions:
        weights: dict[int, tuple[float, float, float]] = {}
        for row in distribution["nodal_forces"]:
            node = int(row["node_id"])
            if node in all_nodes:
                raise ValueError(f"duplicate weighted node id {node}")
            force = tuple(float(x) for x in row["force_xyz_n"])
            if len(force) != 3 or not all(math.isfinite(x) for x in force):
                raise ValueError(f"invalid weight at node {node}")
            weights[node] = force
            all_nodes.add(node)
        owner_weights.append(weights)
    if [len(weights) for weights in owner_weights] != [151, 180]:
        raise ValueError("unexpected serialized actuator owner node counts")
    return [str(name) for name in owner_names], owner_weights


def parse_fixed_vector(line: str, line_number: int) -> tuple[int, tuple[float, float, float]]:
    try:
        node = int(line[3:13])
        values = [float(line[i:i + 12]) for i in range(13, len(line), 12)
                  if line[i:i + 12].strip()]
    except ValueError as error:
        raise ValueError(f"malformed FRD node record at line {line_number}") from error
    if len(values) != 3 or not all(math.isfinite(x) for x in values):
        raise ValueError(f"invalid FRD displacement at line {line_number}")
    return node, (values[0], values[1], values[2])


def norm(vector: tuple[float, float, float]) -> float:
    return math.sqrt(math.fsum(x * x for x in vector))


def dot(left: tuple[float, float, float], right: tuple[float, float, float]) -> float:
    return math.fsum(a * b for a, b in zip(left, right))


def parse_iteration_fields(path: Path, physical_nodes: set[int],
                           owner_names: list[str],
                           owner_weights: list[dict[int, tuple[float, float, float]]]) -> list[dict]:
    frames: list[dict] = []
    previous_nodes: set[int] | None = None
    previous_u: dict[int, tuple[float, float, float]] | None = None
    with path.open("rt", encoding="ascii", errors="strict") as stream:
        line_number = 0
        while True:
            line = stream.readline()
            if not line:
                break
            line_number += 1
            line = line.rstrip("\r\n")
            if not line.startswith("    1PSTEP"):
                continue

            match = re.search(r"STP\s*(\d+)INC\s*(\d+)", line)
            if not match:
                raise ValueError(f"unrecognized FRD step/increment at line {line_number}")
            step, increment = int(match.group(1)), int(match.group(2))
            header = stream.readline()
            line_number += 1
            if not header.startswith("  100CL"):
                raise ValueError(f"missing 100CL header after line {line_number - 1}")
            parts = header.split()
            if len(parts) < 6:
                raise ValueError(f"short 100CL header at line {line_number}")
            dataset_id, time_s, expected_nodes = int(parts[1]), float(parts[2]), int(parts[3])
            iteration = dataset_id - 100
            if iteration <= 0 or int(parts[5]) != iteration or int(header[58:63]) != iteration:
                raise ValueError(f"inconsistent iteration label in header line {line_number}")

            field_header = stream.readline().rstrip("\r\n")
            line_number += 1
            if not field_header.startswith(" -4  DISP"):
                raise ValueError(f"expected DISP field for iteration {iteration}")
            labels = []
            for _ in range(4):
                label_line = stream.readline()
                line_number += 1
                if not label_line.startswith(" -5"):
                    raise ValueError(f"incomplete DISP labels for iteration {iteration}")
                labels.append(label_line.split()[1])
            if labels != ["D1", "D2", "D3", "ALL"]:
                raise ValueError(f"unexpected DISP labels for iteration {iteration}: {labels}")

            u: dict[int, tuple[float, float, float]] = {}
            node_ids: set[int] = set()
            while True:
                row = stream.readline()
                if not row:
                    raise ValueError(f"truncated DISP block for iteration {iteration}")
                line_number += 1
                row = row.rstrip("\r\n")
                if row.startswith(" -3"):
                    break
                if not row.startswith(" -1"):
                    raise ValueError(f"unexpected FRD row in iteration {iteration} at {line_number}")
                node, displacement = parse_fixed_vector(row, line_number)
                if node in node_ids:
                    raise ValueError(f"duplicate node {node} in iteration {iteration}")
                node_ids.add(node)
                if node in physical_nodes:
                    u[node] = displacement

            if len(node_ids) != expected_nodes:
                raise ValueError(f"iteration {iteration} has {len(node_ids)} rows, expected {expected_nodes}")
            if previous_nodes is not None and node_ids != previous_nodes:
                raise ValueError(f"node identity changed at iteration {iteration}")
            if set(u) != physical_nodes:
                raise ValueError(f"physical-node coverage incomplete at iteration {iteration}")
            if any(not weights.keys() <= physical_nodes for weights in owner_weights):
                raise ValueError("actuator weight references a nonphysical or missing node")
            previous_nodes = node_ids

            q_by_owner = {
                owner: math.fsum(dot(weights[node], u[node]) for node in weights)
                for owner, weights in zip(owner_names, owner_weights)
            }
            q_mm = math.fsum(q_by_owner.values())
            max_u_node, max_u_mm = max(((node, norm(value)) for node, value in u.items()),
                                       key=lambda pair: pair[1])
            if previous_u is None:
                correction_node, correction_mm = None, None
            else:
                updates = {
                    node: tuple(u[node][axis] - previous_u[node][axis] for axis in range(3))
                    for node in physical_nodes
                }
                correction_node, correction_mm = max(
                    ((node, norm(value)) for node, value in updates.items()),
                    key=lambda pair: pair[1],
                )
            frames.append({
                "iteration": iteration,
                "step": step,
                "increment": increment,
                "frd_header_time_seconds": time_s,
                "frd_declared_node_count": expected_nodes,
                "q_mm": q_mm,
                "q_by_owner_mm": q_by_owner,
                "max_physical_u_mm": max_u_mm,
                "max_physical_u_node_id": max_u_node,
                "max_iterate_update_mm": correction_mm,
                "max_iterate_update_node_id": correction_node,
            })
            previous_u = u

    if not frames:
        raise ValueError("no complete iteration DISP fields found")
    if [frame["iteration"] for frame in frames] != list(range(1, len(frames) + 1)):
        raise ValueError("iteration labels are not consecutive from 1")
    if any(frame["step"] != EXPECTED_STEP or frame["increment"] != EXPECTED_INCREMENT
           for frame in frames):
        raise ValueError("iteration records do not belong to the first checkpoint increment")
    return frames


def main() -> None:
    execution_path = RUN / "execution.json"
    execution_sha = sha256(execution_path)
    execution = json.loads(execution_path.read_text())
    if (execution["status"] != "bounded_timeout" or execution["returncode"] != 137
            or execution["mechanical_acceptance"] or execution["observations"]):
        raise ValueError("terminal run metadata differs from the reported no-convergence timeout")
    if not execution["frozen_inputs_unchanged"]:
        raise ValueError("execution record does not confirm frozen input preservation")

    freeze_path = RUN / "input-freeze.json"
    freeze_sha = require_hash(freeze_path, execution["input_freeze_sha256"], "input freeze")
    freeze = json.loads(freeze_path.read_text())
    if not freeze["iteration_diagnostics"] or freeze["mechanical_acceptance"]:
        raise ValueError("frozen scope is not the iteration-only diagnostic")
    if freeze["end_seconds"] != TARGET_END_TIME_S:
        raise ValueError("unexpected frozen checkpoint end time")

    inputs = ["pilot.inp", "actuator.json", "output-sets.inp", "mesh.inp", "mesh.json"]
    input_hashes = {
        name: require_hash(RUN / name, freeze["artifacts_sha256"][name], name)
        for name in inputs
    }
    frd_path = RUN / "ResultsForLastIterations.frd"
    frd_sha = require_hash(frd_path, execution["outputs_sha256"][frd_path.name], "iteration FRD")
    physical_nodes = parse_nset(RUN / "output-sets.inp", "CURRENT_ALL_PHYSICAL_NODES")
    owner_names, owner_weights = parse_weights(RUN / "actuator.json")
    pilot_execution = json.loads((PILOT / "execution.json").read_text())
    pilot_q = float(pilot_execution["observations"][0]["q_mm"])
    if not math.isclose(pilot_q, PILOT_Q_MM, rel_tol=0.0, abs_tol=1e-18):
        raise ValueError(f"pilot03 q does not match the frozen comparison point: {pilot_q}")

    frames = parse_iteration_fields(frd_path, physical_nodes, owner_names, owner_weights)
    if sha256(frd_path) != frd_sha or sha256(execution_path) != execution_sha:
        raise ValueError("terminal artifacts changed while the audit was reading them")
    for frame in frames:
        frame["q_minus_pilot03_mm"] = frame["q_mm"] - pilot_q
        frame["q_relative_difference_from_pilot03"] = frame["q_minus_pilot03_mm"] / pilot_q
    late = frames[-LATE_WINDOW:]
    late_q = [frame["q_mm"] for frame in late]
    late_owner_q = {
        owner: [frame["q_by_owner_mm"][owner] for frame in late]
        for owner in owner_names
    }
    q_spread = max(late_q) - min(late_q)
    last_delta = frames[-1]["q_mm"] - pilot_q

    report = {
        "schema": "wood_joint_iteration_motion_audit/v1",
        "scope": "Complete per-iteration DISP trial fields from one bounded-timeout first-increment run; no accepted response or mechanical acceptance.",
        "interpretation": [
            "Trials 2 and 8 are near pilot03's accepted q (-1.060% and -0.636%), and trial 13 is +0.040%; this closeness does not persist.",
            "The recorded q rises monotonically across trials 30-34, while max physical |U| also increases. The last-five q range is 1.382% of pilot03 q, but it is a one-way drift, not a settled endpoint.",
            "Trial 18 jumps from 7.067239311e-6 to 7.315633829e-6 mm and has the largest adjacent-iterate physical displacement update. Trial 34 is +11.921% from pilot03; it is not a reproducible accepted endpoint.",
            "Both owner terms drift, with the cleat term accounting for more of the late-window increase. These data do not support relaxing convergence criteria or treating changing contact counts as harmless.",
        ],
        "terminal_run": {
            "status": execution["status"],
            "returncode": execution["returncode"],
            "elapsed_seconds": execution["elapsed_seconds"],
            "observations": execution["observations"],
            "mechanical_acceptance": execution["mechanical_acceptance"],
            "execution_json_sha256": execution_sha,
            "input_freeze_sha256": freeze_sha,
            "iteration_frd_sha256": frd_sha,
            "solver_reported_endpoint_time_seconds": TARGET_END_TIME_S,
            "frd_header_time_seconds": sorted({frame["frd_header_time_seconds"] for frame in frames}),
            "frd_time_note": "These are trial iterate blocks for step 1/increment 1. CalculiX 2.21 results.c passes ttime to frditeration; in this first increment its FRD header time is 0, the prior accepted total time, not an accepted t=0 solution.",
        },
        "frozen_input_sha256": input_hashes,
        "helper_sha256": sha256(Path(__file__)),
        "node_identity": {
            "physical_node_set": "CURRENT_ALL_PHYSICAL_NODES",
            "physical_node_count": len(physical_nodes),
            "serialized_unit_load_weight_node_count": sum(len(weights) for weights in owner_weights),
            "full_frd_nodes_per_iteration": frames[0]["frd_declared_node_count"],
            "all_iteration_node_ids_identical": True,
            "maxima_exclude_control_and_generated_nonphysical_nodes": True,
        },
        "actuator_observation": {
            "definition": "q = sum(weight_force_xyz_n[node] dot U_xyz_mm[node]) using the two owner_unit_wrench_distributions from frozen actuator.json",
            "weight_units": "N per unit scalar actuator load; q is mm per unit N",
            "pilot03_accepted_first_increment_q_mm": pilot_q,
            "pilot03_source": "ordinary-transient-pilot-attempt03/execution.json observation at t=0.0025 s",
            "late_trial_window_iterations": [frame["iteration"] for frame in late],
            "late_trial_q_mm": late_q,
            "late_trial_q_min_mm": min(late_q),
            "late_trial_q_max_mm": max(late_q),
            "late_trial_q_spread_mm": q_spread,
            "late_trial_spread_fraction_of_pilot_q": q_spread / pilot_q,
            "owner_order": owner_names,
            "late_trial_owner_q_mm": late_owner_q,
            "late_trial_owner_q_spread_mm": {
                owner: max(values) - min(values) for owner, values in late_owner_q.items()
            },
            "last_trial_q_mm": frames[-1]["q_mm"],
            "last_trial_minus_pilot_q_mm": last_delta,
            "last_trial_relative_difference_from_pilot": last_delta / pilot_q,
            "early_trial_points": [frame for frame in frames if frame["iteration"] in (2, 8)],
        },
        "trial_motion": {
            "definition": "max physical-node Euclidean |U| per written trial field; iterate update is max |U_k-U_(k-1)| over the same physical node IDs and is a trial-to-trial displacement-difference proxy, not a solver residual norm.",
            "all_iterations": frames,
            "maximum_physical_u_mm_over_run": max(frame["max_physical_u_mm"] for frame in frames),
            "maximum_iterate_update_mm_over_run": max(
                frame["max_iterate_update_mm"] for frame in frames if frame["max_iterate_update_mm"] is not None
            ),
        },
        "limits": [
            "The parent launcher terminated the job at the 600 s bound; no endpoint observation was accepted and no .rout was written.",
            "Every FRD state is a trial iterate in step 1/increment 1. The final written iterate is not a converged state.",
            "The 0.0025 s checkpoint has a different period-dependent energy-control context from pilot03; q agreement or stability in these trial iterates does not establish equivalence or correctness.",
            "This diagnostic does not qualify contact, wood, bolt/thread behavior, stiffness, capacity, or joint acceptance.",
        ],
    }
    report_path = OUT / "report.json"
    report_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps({
        "report": str(report_path.relative_to(ROOT)),
        "iterations": len(frames),
        "physical_nodes": len(physical_nodes),
        "q_iteration_2_mm": next(f["q_mm"] for f in frames if f["iteration"] == 2),
        "q_iteration_8_mm": next(f["q_mm"] for f in frames if f["iteration"] == 8),
        "q_by_owner_iteration_2_mm": next(f["q_by_owner_mm"] for f in frames if f["iteration"] == 2),
        "q_by_owner_iteration_8_mm": next(f["q_by_owner_mm"] for f in frames if f["iteration"] == 8),
        "pilot03_q_mm": pilot_q,
        "late_iterations": [f["iteration"] for f in late],
        "late_q_spread_mm": q_spread,
        "late_owner_q_spread_mm": report["actuator_observation"]["late_trial_owner_q_spread_mm"],
        "last_trial_q_mm": frames[-1]["q_mm"],
        "last_trial_relative_difference_from_pilot": last_delta / pilot_q,
        "max_physical_u_mm": report["trial_motion"]["maximum_physical_u_mm_over_run"],
        "max_iterate_update_mm": report["trial_motion"]["maximum_iterate_update_mm_over_run"],
    }, indent=2))


if __name__ == "__main__":
    main()
