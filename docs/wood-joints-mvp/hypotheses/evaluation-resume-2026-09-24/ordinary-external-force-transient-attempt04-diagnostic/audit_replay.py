"""Audit completed trace rows and retain interrupted tails as unresolved evidence."""

from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
import math
from pathlib import Path
import re


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
RUN = HERE / "replay-attempt01"
KEYS = ("step", "increment", "attempt", "iteration")
GATES = (
    "iteration_ok", "mechanical_residual_ok", "displacement_ok", "visco_ok",
    "contact_change_gate_clear",
)
BOOLS = GATES + (
    "mechanical_applicable", "no_contact_now", "no_contact_at_start",
    "contact_present", "mechanical_gate_ok", "no_contact_energy_eligible",
    "contact_energy_eligible", "final_convergence_ok",
)
CEL_HEADER = re.compile(
    r"\*ELEMENT,TYPE=C3D6,ELSET=contactelements_st(\d+)_in(\d+)_at(\d+)_it(\d+)",
    re.IGNORECASE,
)
CEL_TAIL_HEADER = re.compile(
    r"^\*ELEMENT,\s*TYPE=C3D6,\s*ELSET=contactelements_st(\d+)_in(\d+)_at(\d+)_it(\d+)",
    re.IGNORECASE,
)


def tail_record(source: str, line: str, key: tuple | None, reason: str,
                affects_cvg_rows: bool, trace_candidate: bool = False) -> dict:
    fragment = line.encode("utf-8", errors="replace")
    record = {
        "source": source,
        "key": list(key) if key is not None else None,
        "reason": reason,
        "fragment_bytes": len(fragment),
        "fragment_sha256": hashlib.sha256(fragment).hexdigest(),
        "fragment_text_prefix": fragment[:512].decode("utf-8", errors="replace"),
        "affects_cvg_rows": affects_cvg_rows,
    }
    if trace_candidate:
        record["trace_candidate"] = True
    return record


def digest(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(4 * 1024 * 1024), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def identity(row: dict) -> tuple[int, ...]:
    result = tuple(row[field] for field in KEYS)
    if any(type(value) is not int or value < 1 for value in result):
        raise ValueError(f"invalid event identity: {result}")
    return result


def cvg_rows(path: Path, partial: list | None = None) -> dict:
    rows = {}
    for line in path.read_text().splitlines(keepends=True):
        parts = line.split()
        if not line.endswith("\n"):
            key = None
            if len(parts) >= 4 and all(re.fullmatch(r"\d+", value) for value in parts[:4]):
                key = tuple(map(int, parts[:4]))
            if partial is not None:
                partial.append(tail_record(
                    "pilot.cvg", line, key, "unterminated CVG line",
                    affects_cvg_rows=True,
                ))
            continue
        if len(parts) < 5:
            continue
        if not all(re.fullmatch(r"\d+", value) for value in parts[:5]):
            continue
        key = tuple(map(int, parts[:4]))
        if key in rows:
            raise ValueError(f"duplicate CVG key {key}")
        rows[key] = {"count": int(parts[4]), "tokens": parts}
    if not rows:
        raise ValueError("no complete CVG rows")
    return rows


def cel_counts(path: Path) -> tuple[dict, list]:
    """Count complete element cards, not headers; a stopped write can end between them."""
    counts, partial = {}, []
    current = None
    with path.open() as stream:
        for line in stream:
            if not line.endswith("\n"):
                fragment = line.strip()
                header_match = CEL_TAIL_HEADER.match(fragment)
                if header_match:
                    tail_key = tuple(map(int, header_match.groups()))
                    affects_rows = True
                elif fragment.startswith("*"):
                    # A partial header must not be attributed to the prior CEL group.
                    tail_key = None
                    affects_rows = fragment.upper().startswith("*ELEMENT") or (
                        "*ELEMENT".startswith(fragment.upper())
                    )
                else:
                    tail_key = current
                    affects_rows = current is not None
                partial.append(tail_record(
                    "pilot.cel", line, tail_key, "unterminated CEL line",
                    affects_cvg_rows=affects_rows,
                ))
                break
            match = CEL_HEADER.fullmatch(line.strip())
            if match:
                current = tuple(map(int, match.groups()))
                counts.setdefault(current, 0)
            elif line.lstrip().startswith("*"):
                if line.upper().startswith("*ELEMENT"):
                    raise ValueError("unexpected CEL element type/header")
                current = None
            elif line.strip():
                fields = [value.strip() for value in line.strip().split(",")]
                if current is None or len(fields) != 7 or not all(
                    re.fullmatch(r"\d+", value) for value in fields
                ):
                    raise ValueError("unrecognized CEL element card")
                counts[current] += 1
    return counts, partial


def reject_constant(value: str) -> None:
    raise ValueError(f"nonfinite JSON constant {value}")


def events(path: Path) -> tuple[dict, dict, list]:
    contact, convergence, partial = {}, {}, []
    for line in path.read_text().splitlines(keepends=True):
        if not line.endswith("\n"):
            stripped = line.lstrip()
            trace_candidate = (
                "CCX223_ATTEMPT04_" in line
                or (stripped.startswith("{") and '"event"' in line)
                or '"event":"CCX223_' in line
            )
            key_values = []
            for field in KEYS:
                match = re.search(rf'"{field}"\s*:\s*(\d+)', line)
                if match is None:
                    key_values = []
                    break
                key_values.append(int(match.group(1)))
            key = tuple(key_values) if len(key_values) == len(KEYS) else None
            partial.append(tail_record(
                "pilot.stdout", line, key, "unterminated stdout line",
                affects_cvg_rows=trace_candidate, trace_candidate=trace_candidate,
            ))
            continue
        if "CCX223_ATTEMPT04_" not in line:
            continue
        row = json.loads(line, parse_constant=reject_constant)
        key = identity(row)
        if row.get("event") == "CCX223_ATTEMPT04_CONTACT":
            target = contact
            expected = set(KEYS) | {
                "event", "contact_old", "contact_new", "delcon", "contact_change_flag",
            }
            if set(row) != expected:
                raise ValueError(f"contact event fields differ at {key}")
            for field in ("contact_old", "contact_new", "contact_change_flag"):
                if type(row[field]) is not int or row[field] < 0:
                    raise ValueError(f"invalid {field} at {key}")
            if row["contact_change_flag"] not in (0, 1):
                raise ValueError(f"invalid contact flag at {key}")
            if type(row["delcon"]) not in (int, float) or not math.isfinite(row["delcon"]):
                raise ValueError(f"invalid delcon at {key}")
            if row["delcon"] != 0.001:
                raise ValueError(f"unpinned delcon at {key}")
        elif row.get("event") == "CCX223_ATTEMPT04_CONVERGENCE":
            target = convergence
            if set(row) != set(KEYS) | set(BOOLS) | {"event", "iconvergence", "idivergence"}:
                raise ValueError(f"convergence event fields differ at {key}")
            if any(type(row[field]) is not int or row[field] not in (0, 1) for field in BOOLS):
                raise ValueError(f"invalid convergence boolean at {key}")
            if any(type(row[field]) is not int for field in ("iconvergence", "idivergence")):
                raise ValueError(f"invalid convergence state at {key}")
        else:
            raise ValueError(f"unexpected event type at {key}")
        if key in target:
            raise ValueError(f"duplicate event {row['event']} at {key}")
        target[key] = row
    return contact, convergence, partial


def inspect_rows(cvg: dict, cel: dict, contact: dict, convergence: dict,
                 partial_lines: list | None = None, nmethod: int = 4,
                 uncoupled: int = 0, idrct: int = 0,
                 interrupted_terminal: bool = False) -> dict:
    errors, unresolved, rows = [], [], []
    partial_lines = partial_lines or []
    tail_by_key = {}
    stdout_trace_tail_keys = set()
    unknown_stdout_trace_tail = False
    last_key = max(cvg)
    for tail in partial_lines:
        if not tail.get("affects_cvg_rows"):
            continue
        raw_key = tail.get("key")
        key = tuple(raw_key) if isinstance(raw_key, (list, tuple)) else None
        if key is None:
            if tail.get("source") == "pilot.stdout" and tail.get("trace_candidate"):
                unknown_stdout_trace_tail = True
        else:
            tail_by_key.setdefault(key, []).append(tail)
            if tail.get("source") == "pilot.stdout" and tail.get("trace_candidate"):
                stdout_trace_tail_keys.add(key)
            if key < last_key:
                errors.append(f"incomplete trace evidence precedes the terminal row: {key}")

    expected_contact = {key for key in cvg if key[3] > 1}
    missing_contact = expected_contact - set(contact)
    unexpected_contact = {
        key for key in set(contact) - expected_contact
        if key in cvg or key < last_key
    }
    if unexpected_contact:
        errors.append(
            "contact events exist outside the expected later-iteration CVG rows: "
            f"{sorted(unexpected_contact)}"
        )
    terminal_contact_extras = {
        key for key in set(contact) - expected_contact
        if key not in cvg and key >= last_key
    }
    if terminal_contact_extras and not interrupted_terminal:
        errors.append(
            "contact events extend beyond the final CVG row in a completed execution: "
            f"{sorted(terminal_contact_extras)}"
        )
    terminal_contact_tail = {
        key for key in missing_contact
        if key == last_key and (
            key in stdout_trace_tail_keys or unknown_stdout_trace_tail
        )
    }
    if missing_contact - terminal_contact_tail:
        errors.append("completed CVG rows do not have exactly the expected later contact events")
    for key in set(convergence) - set(cvg):
        if key < last_key:
            errors.append(f"interior convergence event has no CVG row: {key}")
        elif not interrupted_terminal:
            errors.append(f"convergence event extends beyond the final CVG row: {key}")
    for key in sorted(set(contact) | set(cel) | set(cvg) | set(convergence) | set(tail_by_key)):
        terminal_cel_mismatch = (
            interrupted_terminal and key == last_key
            and cel.get(key) != cvg[key]["count"]
        )
        row_has_terminal_tail = (
            key in tail_by_key
            or (key == last_key and unknown_stdout_trace_tail)
            or terminal_cel_mismatch
        )
        if key not in cvg or key not in convergence or row_has_terminal_tail:
            if key < last_key:
                errors.append(f"interior row is missing completion evidence: {key}")
            unresolved.append({"key": key, "cvg": key in cvg, "contact": key in contact,
                               "cel": key in cel, "convergence": key in convergence,
                               "partial_tail": row_has_terminal_tail,
                               "reason": (
                                   "terminal CEL group is incomplete at interrupted execution"
                                   if terminal_cel_mismatch else None
                               )})
            continue
        count, record = cvg[key]["count"], convergence[key]
        if cel.get(key) != count:
            errors.append(f"complete CEL count differs from CVG at {key}")
        if record["iteration_ok"] != int(key[3] > 1):
            errors.append(f"iteration gate differs from source at {key}")
        if record["no_contact_now"] != int(count == 0):
            errors.append(f"contact presence differs from CVG at {key}")
        contact_present = int(not record["no_contact_now"] or not record["no_contact_at_start"])
        if record["contact_present"] != contact_present:
            errors.append(f"contact-present conjunction differs at {key}")
        mechanical = record["mechanical_applicable"] and all(record[field] for field in GATES)
        if record["mechanical_gate_ok"] != int(mechanical):
            errors.append(f"mechanical conjunction differs at {key}")
        final = record["iconvergence"] == 1 and record["idivergence"] == 0
        if record["final_convergence_ok"] != int(final):
            errors.append(f"final convergence conjunction differs at {key}")
        energy_base = (
            nmethod == 4 and uncoupled == 0 and record["mechanical_applicable"] == 1
            and record["iconvergence"] == 1
        )
        no_contact_energy = int(
            energy_base and record["no_contact_now"] == 1
            and record["no_contact_at_start"] == 1 and idrct == 0
        )
        contact_energy = int(energy_base and contact_present == 1)
        if record["no_contact_energy_eligible"] != no_contact_energy:
            errors.append(f"no-contact energy eligibility differs at {key}")
        if record["contact_energy_eligible"] != contact_energy:
            errors.append(f"contact energy eligibility differs at {key}")
        count_event = contact.get(key)
        if count_event is not None:
            previous = cvg.get((*key[:3], key[3] - 1))
            if previous is None or count_event["contact_old"] != previous["count"]:
                errors.append(f"prior count differs at {key}")
            if count_event["contact_new"] != count:
                errors.append(f"new count differs at {key}")
            old = count_event["contact_old"]
            changed = count < old * (1 - 0.001) or count > old * (1 + 0.001)
            if changed and count_event["contact_change_flag"] != 1:
                errors.append(f"count comparison must set flag at {key}")
            if record["contact_change_gate_clear"] != 1 - count_event["contact_change_flag"]:
                errors.append(f"count and convergence flags differ at {key}")
        rows.append({"key": key, "contact_elements": count, "contact": count_event,
                     "convergence": record,
                     "failed_mechanical_prerequisites": [name for name in GATES if not record[name]]})
    combinations = Counter(tuple(row["failed_mechanical_prerequisites"]) for row in rows)
    return {
        "errors": errors, "completed_rows": rows, "unresolved_tail": unresolved,
        "counts": {"cvg": len(cvg), "cel": len(cel), "contact_events": len(contact),
                   "convergence_events": len(convergence), "completed_rows": len(rows)},
        "failure_combinations": [{"prerequisites": names, "rows": count}
                                 for names, count in sorted(combinations.items())],
        "all_cvg_rows_audited": len(rows) == len(cvg) and not errors,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    execution = json.loads((RUN / "execution.json").read_text())
    if execution.get("status") == "running" or not execution.get("ended_utc"):
        raise ValueError("terminal execution record required")
    if execution.get("container_state", {}).get("Running") is not False:
        raise ValueError("confirmed stopped container required")
    command = execution["command"]
    if command[-4:] != [
        "sha256:1cc1d52946c5acddc9d4eeaf1dd1bf0bc4d3f564eb1c264f5d29b67c6386b7fa",
        "/usr/local/bin/ccx-attempt04-diagnostic-2.23", "-i", "pilot",
    ]:
        raise ValueError("execution does not use the pinned diagnostic image/binary/deck")
    for name, expected in execution["outputs_sha256"].items():
        if digest(RUN / name) != expected:
            raise ValueError(f"recorded replay output differs: {name}")
    lock = json.loads((HERE / "diagnostic-lock.json").read_text())
    if digest(HERE / "attempt03-input-binding.json") != lock["attempt03_binding_sha256"]:
        raise ValueError("attempt03 binding differs from diagnostic lock")
    binding = json.loads((HERE / "attempt03-input-binding.json").read_text())
    original = ROOT / binding["attempt03_path"]
    for name, expected in binding["frozen_artifacts_sha256"].items():
        if digest(RUN / name) != expected or digest(original / name) != expected:
            raise ValueError(f"frozen input differs: {name}")
    for name, expected in binding["outputs_sha256"].items():
        if digest(original / name) != expected:
            raise ValueError(f"original output differs: {name}")
    partial_cvg = []
    cvg = cvg_rows(RUN / "pilot.cvg", partial_cvg)
    cel, partial_cel = cel_counts(RUN / "pilot.cel")
    contact, convergence, partial_json = events(RUN / "pilot.stdout")
    partial_lines = partial_cvg + partial_cel + partial_json
    normal_execution = (
        execution.get("status") == "container_exited"
        and execution.get("container_exit_code") == 0
        and execution.get("container_oom_killed") is False
        and execution.get("stop_reason") == "container_exited_normally"
    )
    result = inspect_rows(
        cvg, cel, contact, convergence, partial_lines,
        interrupted_terminal=not normal_execution,
    )
    baseline = cvg_rows(original / "pilot.cvg")
    common = sorted(set(cvg) & set(baseline))
    result.update({
        "schema": "calculix_attempt04_completed_trace_audit/v1",
        "scope": "Frozen mechanical mortar=1 large-sliding diagnostic; no physical response acceptance.",
        "execution_sha256": digest(RUN / "execution.json"),
        "auditor_sha256": digest(Path(__file__)),
        "binding_sha256": digest(HERE / "attempt03-input-binding.json"),
        "output_sha256": execution["outputs_sha256"],
        "partial_lines": partial_lines,
        "execution_termination": {
            "status": execution.get("status"),
            "stop_reason": execution.get("stop_reason"),
            "runner_stop_request_reason": execution.get("runner_stop_request_reason"),
            "container_state_confirmed": execution.get("container_state_confirmed"),
            "container_exit_code": execution.get("container_exit_code"),
            "container_oom_killed": execution.get("container_oom_killed"),
        },
        "execution_complete": normal_execution,
        "audit_complete": (
            result["all_cvg_rows_audited"]
            and not result["unresolved_tail"]
            and not partial_lines
            and not result["errors"]
        ),
        "reference_common_cvg_rows": len(common),
        "reference_replay_only_cvg_keys": [list(key) for key in sorted(set(cvg) - set(baseline))],
        "reference_original_only_cvg_keys": [list(key) for key in sorted(set(baseline) - set(cvg))],
        "reference_cvg_token_mismatches": [key for key in common
                                          if cvg[key]["tokens"] != baseline[key]["tokens"]],
        "baseline_cvg_parity": {
            "common_rows": len(common),
            "replay_only_keys": [list(key) for key in sorted(set(cvg) - set(baseline))],
            "original_only_keys": [list(key) for key in sorted(set(baseline) - set(cvg))],
            "token_mismatch_keys": [list(key) for key in common
                                    if cvg[key]["tokens"] != baseline[key]["tokens"]],
            "parity_pass": (
                set(cvg) == set(baseline)
                and all(cvg[key]["tokens"] == baseline[key]["tokens"] for key in common)
            ),
            "interpretation": "diagnostic comparison only; does not affect acceptance",
        },
        "mechanical_acceptance": False, "joint_acceptance": False,
    })
    if args.write:
        (RUN / "trace-audit.json").write_text(json.dumps(result, indent=2, allow_nan=False) + "\n")
    print(json.dumps({key: result[key] for key in (
        "counts", "errors", "failure_combinations", "all_cvg_rows_audited",
        "unresolved_tail", "partial_lines", "execution_termination", "execution_complete",
        "audit_complete", "baseline_cvg_parity", "reference_cvg_token_mismatches",
        "mechanical_acceptance", "joint_acceptance",
    )}, indent=2))
    if result["errors"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
