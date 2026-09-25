"""Audit accepted transient q-work and sampled load-factor impulse history.

The signed coordinate is the complete nodal displacement field projected on
the frozen unit-force pattern. It is not a center-of-mass displacement or a
contact-force impulse. Work is only reconstructed when every accepted status
time has a complete monitor block in the native DAT output.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
from itertools import pairwise
from pathlib import Path

from fea.wood_joint_current_transient_launch import observations

_DAT_HEADER = re.compile(
    r"displacements \(vx,vy,vz\) for set PILOT_MONITOR and time\s+(\S+)",
    re.IGNORECASE,
)
_NUMBER = re.compile(r"^[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[EeDd][+-]?\d+)?$")
_STA_ATTEMPT = re.compile(r"^(\d+)(U?)$", re.IGNORECASE)
_ACTUAL_TOTAL_TIME = re.compile(r"actual total time\s*=\s*(\S+)", re.IGNORECASE)
_EXTERNAL_WORK = re.compile(r"^\s*external work\s*=\s*(\S+)", re.IGNORECASE)

TIME_MATCH_ATOL_SECONDS = 1.0e-8


def _number(token: str) -> float:
    value = float(token.replace("D", "E").replace("d", "e"))
    if not math.isfinite(value):
        raise ValueError("nonfinite numeric value")
    return value


def _half_print_quantum(token: str) -> float:
    """Half a last-place unit for an E-format number as printed by CCX."""
    normalized = token.replace("D", "E").replace("d", "e")
    if "e" not in normalized.lower():
        return 0.0
    mantissa, exponent = re.split("[Ee]", normalized)
    digits = len(mantissa.partition(".")[2])
    return 0.5 * 10.0 ** (int(exponent) - digits)


def parse_accepted_sta(text: str) -> tuple[list[dict], int]:
    """Return accepted `.sta` rows and the count of rejected `U` attempts."""
    accepted = []
    rejected = 0
    seen = set()
    for line in text.splitlines():
        fields = line.split()
        if not fields or not fields[0].isdigit():
            continue
        if len(fields) != 7 or not fields[1].isdigit():
            raise ValueError("malformed numeric row in .sta")
        attempt_match = _STA_ATTEMPT.fullmatch(fields[2])
        if attempt_match is None or not fields[3].isdigit():
            raise ValueError("malformed attempt or iteration in .sta")
        row = {
            "step": int(fields[0]),
            "increment": int(fields[1]),
            "attempt": int(attempt_match.group(1)),
            "unaccepted": bool(attempt_match.group(2)),
            "iterations": int(fields[3]),
            "total_time_seconds": _number(fields[4]),
            "total_time_print_bound_seconds": _half_print_quantum(fields[4]),
            "step_time_seconds": _number(fields[5]),
            "increment_time_seconds": _number(fields[6]),
        }
        if row["unaccepted"]:
            rejected += 1
            continue
        key = (row["step"], row["increment"])
        if key in seen:
            raise ValueError("duplicate accepted .sta increment")
        seen.add(key)
        if accepted and row["total_time_seconds"] <= accepted[-1]["total_time_seconds"]:
            raise ValueError("accepted .sta times must increase")
        accepted.append(row)
    if not accepted:
        raise ValueError(".sta contains no accepted increment rows")
    return accepted, rejected


def _unit_weights(freeze: dict) -> dict[int, tuple[float, float, float]]:
    result = {}
    for raw_node, row in freeze["serialized_unit_load_nodes"].items():
        node = int(raw_node)
        force = tuple(float(x) for x in row["force_xyz_n"])
        if len(force) != 3 or not all(math.isfinite(x) for x in force):
            raise ValueError("invalid frozen unit-force row")
        if node in result:
            raise ValueError("duplicate frozen unit-force node")
        result[node] = force
    if not result:
        raise ValueError("frozen unit-force field is empty")
    return result


def _complete_dat_precision_rows(text: str, freeze: dict) -> dict[float, dict]:
    """Parse complete monitor blocks once and estimate q rounding bounds."""
    # A running solver may leave a partial final numeric line. Only complete
    # newline-terminated records can be used as native observations.
    text = text[: text.rfind("\n") + 1]
    lines = text.splitlines()
    expected = {int(node) for node in freeze["monitor_nodes"]}
    weights = _unit_weights(freeze)
    samples = {}
    index = 0
    while index < len(lines):
        match = _DAT_HEADER.search(lines[index])
        if match is None:
            index += 1
            continue
        time_token = match.group(1)
        time = _number(time_token)
        rows = {}
        row_tokens = {}
        cursor = index + 1
        while cursor < len(lines):
            fields = lines[cursor].split()
            if not fields and not rows:
                cursor += 1
                continue
            if len(fields) != 4 or not fields[0].isdigit():
                break
            node = int(fields[0])
            if node not in expected or node in rows:
                raise ValueError("unexpected or duplicate monitor node in .dat")
            values = tuple(_number(token) for token in fields[1:])
            rows[node] = values
            row_tokens[node] = fields[1:]
            if len(rows) == len(expected):
                break
            cursor += 1
        if set(rows) == expected:
            q = math.fsum(
                force[axis] * rows[node][axis]
                for node, force in weights.items()
                for axis in range(3)
            )
            q_bound = math.fsum(
                abs(force[axis]) * _half_print_quantum(row_tokens[node][axis])
                for node, force in weights.items()
                for axis in range(3)
            )
            if time in samples:
                raise ValueError("duplicate complete monitor block time in .dat")
            samples[time] = {
                "time_seconds": time,
                "time_token": time_token,
                "time_print_bound_seconds": _half_print_quantum(time_token),
                "q_mm": q,
                "q_print_bound_mm": q_bound,
            }
            index = cursor + 1
        else:
            # Incomplete blocks, including the live-file tail case, are not
            # samples. Move past the header and continue looking for another.
            index += 1
    return samples


def _time_close(left: float, right: float) -> bool:
    return abs(left - right) <= TIME_MATCH_ATOL_SECONDS


def _match_by_time(
    targets: list[float], samples: dict[float, dict]
) -> tuple[dict, list]:
    matched = {}
    used = set()
    missing = []
    for target in targets:
        candidates = [
            sample_time
            for sample_time in samples
            if sample_time not in used and _time_close(sample_time, target)
        ]
        if len(candidates) != 1:
            missing.append(target)
            continue
        key = candidates[0]
        used.add(key)
        matched[target] = samples[key]
    extras = [
        time for time in samples if time not in used and not _time_close(time, 0.0)
    ]
    return matched, extras + missing


def _cards(text: str):
    """Yield each card header and its following data rows from one input file."""
    header = None
    data = []
    for raw in text.splitlines():
        stripped = raw.strip()
        if stripped.startswith("**") or not stripped:
            continue
        if stripped.startswith("*"):
            if header is not None:
                yield header, data
            header, data = stripped, []
        elif header is not None:
            data.append(stripped)
    if header is not None:
        yield header, data


def _attributes(header: str) -> tuple[str, dict[str, str]]:
    pieces = header.strip().replace(" ", "").split(",")
    keyword = pieces[0].upper()
    attrs = {}
    for piece in pieces[1:]:
        if "=" in piece:
            key, value = piece.split("=", 1)
            attrs[key.upper()] = value
        else:
            attrs[piece.upper()] = ""
    return keyword, attrs


def _parse_deck_patterns(input_texts: list[str], freeze: dict):
    amplitudes = []
    cloads = {}
    cload_count = 0
    prohibited = {"*DLOAD", "*DSLOAD", "*GRAVITY", "*BOUNDARY", "*INITIALCONDITIONS"}
    for text in input_texts:
        for header, data in _cards(text):
            keyword, attrs = _attributes(header)
            if keyword in prohibited:
                raise ValueError(f"unexpected external constraint/load card {keyword}")
            if keyword == "*AMPLITUDE" and attrs.get("NAME", "").upper() == "RAMP_N":
                time_basis = attrs.get("TIME", "STEPTIME").upper().replace(" ", "")
                if time_basis not in ("STEPTIME", ""):
                    raise ValueError("RAMP_N must use STEP TIME coordinates")
                points = []
                for line in data:
                    fields = [
                        field.strip() for field in line.split(",") if field.strip()
                    ]
                    if not fields:
                        continue
                    if len(fields) % 2:
                        raise ValueError("RAMP_N data must contain time/value pairs")
                    points.extend(
                        (_number(fields[i]), _number(fields[i + 1]))
                        for i in range(0, len(fields), 2)
                    )
                amplitudes.append((attrs, points))
            elif keyword == "*CLOAD":
                if attrs.get("AMPLITUDE", "").upper() != "RAMP_N":
                    raise ValueError("all pilot CLOADs must use RAMP_N")
                cload_count += 1
                for line in data:
                    fields = [field.strip() for field in line.split(",")]
                    if (
                        len(fields) < 3
                        or not fields[0].isdigit()
                        or not fields[1].isdigit()
                    ):
                        raise ValueError("invalid numeric CLOAD row")
                    node = int(fields[0])
                    dof = int(fields[1])
                    value = _number(fields[2])
                    if dof not in (1, 2, 3) or value == 0.0:
                        raise ValueError(
                            "pilot CLOAD must be nonzero translational force"
                        )
                    key = (node, dof)
                    if key in cloads:
                        raise ValueError("duplicate actual CLOAD node/DOF")
                    cloads[key] = value
    if len(amplitudes) != 1:
        raise ValueError("expected exactly one RAMP_N amplitude definition")
    attrs, points = amplitudes[0]
    if freeze.get("amplitude_time_basis") != "STEP TIME":
        raise ValueError(
            "input freeze does not declare STEP TIME amplitude coordinates"
        )
    if attrs.get("DEFINITION", "TABULAR").upper() not in ("TABULAR", ""):
        raise ValueError("only the serialized tabular RAMP_N is supported")
    if len(points) < 2 or any(
        points[i][0] >= points[i + 1][0] for i in range(len(points) - 1)
    ):
        raise ValueError("RAMP_N times must be strictly increasing")
    if points[0][0] != 0.0 or points[0][1] != 0.0:
        raise ValueError("the audited ramp must start at zero force at t=0")
    if cload_count != 1 or not cloads:
        raise ValueError("expected one nonempty CLOAD card")

    unit = _unit_weights(freeze)
    expected = {
        (node, axis + 1): component
        for node, vector in unit.items()
        for axis, component in enumerate(vector)
        if component != 0.0
    }
    if set(cloads) != set(expected):
        raise ValueError(
            "actual CLOAD node/DOF support differs from frozen unit pattern"
        )
    scales = [cloads[key] / expected[key] for key in expected]
    load_scale = scales[0]
    if not math.isfinite(load_scale) or load_scale == 0.0:
        raise ValueError("invalid actual CLOAD scale")
    if any(
        not math.isclose(scale, load_scale, rel_tol=1e-12, abs_tol=1e-14)
        for scale in scales
    ):
        raise ValueError(
            "actual CLOAD field is not proportional to frozen unit pattern"
        )
    return points, load_scale


def _amplitude_at(points: list[tuple[float, float]], time: float) -> float:
    if (
        time < points[0][0] - TIME_MATCH_ATOL_SECONDS
        or time > points[-1][0] + TIME_MATCH_ATOL_SECONDS
    ):
        raise ValueError("accepted time is outside RAMP_N data")
    if time <= points[0][0]:
        return points[0][1]
    if time >= points[-1][0]:
        return points[-1][1]
    for (left_t, left_a), (right_t, right_a) in pairwise(points):
        if left_t <= time <= right_t:
            fraction = (time - left_t) / (right_t - left_t)
            return left_a + fraction * (right_a - left_a)
    raise ValueError("could not interpolate RAMP_N")


def _factor_integral(points, start: float, end: float, scale: float) -> float:
    if end < start:
        raise ValueError("impulse interval runs backward")
    if end == start:
        return 0.0
    cuts = [start, *(t for t, _ in points if start < t < end), end]
    return scale * math.fsum(
        0.5 * (_amplitude_at(points, a) + _amplitude_at(points, b)) * (b - a)
        for a, b in pairwise(cuts)
    )


def _amplitude_time_bound(points, time: float, time_bound: float) -> float:
    """Bound amplitude change from printed-time rounding near one sample."""
    if time_bound == 0.0:
        return 0.0
    nominal = _amplitude_at(points, time)
    left = max(points[0][0], time - time_bound)
    right = min(points[-1][0], time + time_bound)
    candidates = [left, right]
    candidates.extend(t for t, _ in points if left < t < right)
    return max(
        abs(_amplitude_at(points, candidate) - nominal) for candidate in candidates
    )


def _integral_time_bound(points, start, end, start_bound, end_bound, scale):
    """Conservative first-order endpoint-time bound for both integral estimates."""
    start_amp = _amplitude_at(points, start)
    end_amp = _amplitude_at(points, end)
    start_amp_bound = _amplitude_time_bound(points, start, start_bound)
    end_amp_bound = _amplitude_time_bound(points, end, end_bound)
    exact = abs(scale) * (
        (abs(start_amp) + start_amp_bound) * start_bound
        + (abs(end_amp) + end_amp_bound) * end_bound
    )
    duration = end - start
    delta_duration = start_bound + end_bound
    amplitude_sum = abs(start_amp + end_amp)
    amplitude_sum_bound = start_amp_bound + end_amp_bound
    endpoint = (
        0.5
        * abs(scale)
        * (
            amplitude_sum * delta_duration
            + abs(duration) * amplitude_sum_bound
            + amplitude_sum_bound * delta_duration
        )
    )
    return exact, endpoint, start_amp_bound, end_amp_bound


def _native_work_samples(log_text: str) -> list[dict]:
    """Read external-work totals and the attempted total time they close at."""
    samples = []
    total_time = None
    waiting_for_external = False
    for line in log_text.splitlines():
        time_match = _ACTUAL_TOTAL_TIME.search(line)
        if time_match:
            total_time = time_match.group(1)
        if "since start of the step" in line.lower():
            waiting_for_external = True
            continue
        work_match = _EXTERNAL_WORK.match(line)
        if waiting_for_external and work_match:
            if total_time is None:
                raise ValueError(
                    "native external-work print lacks preceding total time"
                )
            token = work_match.group(1)
            samples.append(
                {
                    "time_seconds": _number(total_time),
                    "time_token": total_time,
                    "external_work_nmm": _number(token),
                    "work_token": token,
                    "work_print_bound_nmm": _half_print_quantum(token),
                }
            )
            waiting_for_external = False
    return samples


def audit_history_texts(
    *, freeze: dict, deck_texts: list[str], sta_text: str, dat_text: str, log_text: str
) -> dict:
    """Audit a one-step current transient from frozen cards and terminal outputs.

    Missing monitor data at any accepted `.sta` time makes the reconstructed
    work unavailable; the function never bridges over an unobserved increment.
    """
    if freeze.get("schema") != "wood_joint_current_transient/v1":
        raise ValueError("unexpected transient input-freeze schema")
    accepted, rejected_count = parse_accepted_sta(sta_text)
    if any(row["step"] != 1 for row in accepted):
        raise ValueError("history audit currently requires the frozen one-step pilot")
    if any(
        not _time_close(row["step_time_seconds"], row["total_time_seconds"])
        for row in accepted
    ):
        raise ValueError("single-step total and step time differ")
    points, load_scale = _parse_deck_patterns(deck_texts, freeze)

    observed = observations(dat_text, freeze)
    observed_by_time = {}
    for row in observed:
        time = float(row["time_seconds"])
        if time in observed_by_time:
            raise ValueError("duplicate complete monitor observation time")
        observed_by_time[time] = row
    precision_by_time = _complete_dat_precision_rows(dat_text, freeze)
    if set(observed_by_time) != set(precision_by_time):
        raise ValueError("launcher observations and precision parser disagree")
    for time, row in observed_by_time.items():
        q = precision_by_time[time]["q_mm"]
        if not math.isclose(float(row["q_mm"]), q, rel_tol=1e-12, abs_tol=1e-15):
            raise ValueError("launcher q differs from independently read monitor rows")

    accepted_times = [row["total_time_seconds"] for row in accepted]
    matched, unmatched = _match_by_time(accepted_times, precision_by_time)
    zero_extras = [time for time in precision_by_time if _time_close(time, 0.0)]
    coverage_complete = not unmatched and len(matched) == len(accepted)
    native_samples = _native_work_samples(log_text)
    native_by_time = {}
    for row in native_samples:
        key = row["time_seconds"]
        if key in native_by_time:
            raise ValueError("duplicate native external-work summary time")
        native_by_time[key] = row
    matched_native, native_unmatched = _match_by_time(accepted_times, native_by_time)
    native_complete = not native_unmatched and len(matched_native) == len(accepted)

    impulse_rows = []
    previous_time = 0.0
    previous_time_bound = 0.0
    for status in accepted:
        status_time = status["total_time_seconds"]
        if status_time in matched:
            sample = matched[status_time]
            time = sample["time_seconds"]
            time_bound = sample["time_print_bound_seconds"]
            time_source = "complete_dat_monitor_header"
        else:
            time = status["step_time_seconds"]
            time_bound = status["total_time_print_bound_seconds"]
            time_source = "accepted_sta_label_no_complete_dat_block"
        a0 = _amplitude_at(points, previous_time)
        a1 = _amplitude_at(points, time)
        exact = _factor_integral(points, previous_time, time, load_scale)
        endpoint = 0.5 * (a0 + a1) * (time - previous_time) * load_scale
        exact_time_bound, endpoint_time_bound, a0_time_bound, a1_time_bound = (
            _integral_time_bound(
                points,
                previous_time,
                time,
                previous_time_bound,
                time_bound,
                load_scale,
            )
        )
        impulse_rows.append(
            {
                "increment": status["increment"],
                "start_time_seconds": previous_time,
                "end_time_seconds": time,
                "start_time_print_bound_seconds": previous_time_bound,
                "end_time_print_bound_seconds": time_bound,
                "end_time_source": time_source,
                "start_amplitude": a0,
                "end_amplitude": a1,
                "start_amplitude_time_bound": a0_time_bound,
                "end_amplitude_time_bound": a1_time_bound,
                "piecewise_linear_pattern_impulse_ns": exact,
                "piecewise_linear_impulse_time_print_bound_ns": exact_time_bound,
                "whole_interval_endpoint_trapezoid_pattern_impulse_ns": endpoint,
                "endpoint_trapezoid_time_print_bound_ns": endpoint_time_bound,
                "endpoint_trapezoid_minus_exact_pattern_impulse_ns": endpoint - exact,
            }
        )
        previous_time = time
        previous_time_bound = time_bound

    work_rows = []
    reconstructed_total = None
    comparison_complete = coverage_complete and native_complete
    if coverage_complete:
        previous_time = 0.0
        previous_q = 0.0
        previous_q_bound = 0.0
        previous_a = _amplitude_at(points, 0.0)
        previous_a_time_bound = 0.0
        reconstructed_total = 0.0
        cumulative_q_print_bound = 0.0
        cumulative_amplitude_time_bound = 0.0
        for status in accepted:
            status_time = status["total_time_seconds"]
            sample = matched[status_time]
            time = sample["time_seconds"]
            q = sample["q_mm"]
            q_bound = sample["q_print_bound_mm"]
            amplitude_time_bound = _amplitude_time_bound(
                points, time, sample["time_print_bound_seconds"]
            )
            amplitude = _amplitude_at(points, time)
            increment_work = (
                0.5 * (previous_a + amplitude) * (q - previous_q) * load_scale
            )
            reconstructed_total += increment_work
            delta_q_bound = previous_q_bound + q_bound
            delta_a_bound = previous_a_time_bound + amplitude_time_bound
            cumulative_q_print_bound += (
                0.5 * abs(load_scale) * abs(previous_a + amplitude) * delta_q_bound
            )
            cumulative_amplitude_time_bound += (
                0.5
                * abs(load_scale)
                * (abs(q - previous_q) * delta_a_bound + delta_a_bound * delta_q_bound)
            )
            row = {
                "step": status["step"],
                "increment": status["increment"],
                "attempt": status["attempt"],
                "time_seconds": time,
                "time_print_bound_seconds": sample["time_print_bound_seconds"],
                "q_mm": q,
                "q_print_bound_mm": q_bound,
                "amplitude": amplitude,
                "amplitude_time_print_bound": amplitude_time_bound,
                "increment_discrete_work_nmm": increment_work,
                "cumulative_discrete_work_nmm": reconstructed_total,
            }
            if native_complete:
                native = matched_native[status_time]
                native_print_bound = native["work_print_bound_nmm"]
                total_print_bound = (
                    cumulative_q_print_bound
                    + cumulative_amplitude_time_bound
                    + native_print_bound
                )
                residual = reconstructed_total - native["external_work_nmm"]
                row.update(
                    {
                        "native_cumulative_external_work_nmm": native[
                            "external_work_nmm"
                        ],
                        "native_work_print_bound_nmm": native_print_bound,
                        "cumulative_q_print_bound_nmm": cumulative_q_print_bound,
                        "cumulative_amplitude_time_print_bound_nmm": cumulative_amplitude_time_bound,
                        "combined_work_print_bound_nmm": total_print_bound,
                        "work_residual_nmm": residual,
                        "within_print_bound": abs(residual) <= total_print_bound,
                    }
                )
            work_rows.append(row)
            previous_time, previous_q, previous_q_bound, previous_a = (
                time,
                q,
                q_bound,
                amplitude,
            )
            previous_a_time_bound = amplitude_time_bound

    unmatched_dat_times = [
        sample_time
        for sample_time in precision_by_time
        if not _time_close(sample_time, 0.0)
        and not any(
            _time_close(sample_time, accepted_time) for accepted_time in accepted_times
        )
    ]
    missing_dat_times = [time for time in accepted_times if time not in matched]
    missing_native_times = [
        time for time in accepted_times if time not in matched_native
    ]
    return {
        "schema": "wood_joint_current_transient_history/v1",
        "status": "complete" if coverage_complete else "work_unavailable",
        "accepted_increment_count": len(accepted),
        "rejected_attempt_count": rejected_count,
        "load_scale_from_actual_cload": load_scale,
        "actual_cload_proportional_to_frozen_unit_pattern": True,
        "time_match_tolerance_seconds": TIME_MATCH_ATOL_SECONDS,
        "monitor_coverage": {
            "status": "complete" if coverage_complete else "incomplete",
            "missing_accepted_times_seconds": missing_dat_times,
            "unmatched_monitor_times_seconds": unmatched_dat_times,
            "initial_zero_time_monitor_blocks_ignored": len(zero_extras),
        },
        "force_impulse": {
            "status": "available",
            "interpretation": "integral of the scalar force coefficient load_scale*A(t), in N*s, multiplying the frozen unit-load nodal pattern; it is not a net-resultant vector impulse or transferred contact impulse",
            "intervals": impulse_rows,
            "cumulative_piecewise_linear_pattern_impulse_ns": math.fsum(
                row["piecewise_linear_pattern_impulse_ns"] for row in impulse_rows
            ),
            "cumulative_piecewise_linear_impulse_time_print_bound_ns": math.fsum(
                row["piecewise_linear_impulse_time_print_bound_ns"]
                for row in impulse_rows
            ),
            "cumulative_endpoint_trapezoid_pattern_impulse_ns": math.fsum(
                row["whole_interval_endpoint_trapezoid_pattern_impulse_ns"]
                for row in impulse_rows
            ),
            "cumulative_endpoint_trapezoid_time_print_bound_ns": math.fsum(
                row["endpoint_trapezoid_time_print_bound_ns"] for row in impulse_rows
            ),
        },
        "work": {
            "status": "available"
            if coverage_complete
            else "unavailable_missing_accepted_displacements",
            "coordinate": "signed complete-field virtual-work projection on the frozen 1 N reference-force pattern, reported in mm-equivalent; not center of mass",
            "reconstruction": "sum 0.5*(A_i+A_prev)*(q_i-q_prev)*load_scale over accepted increments",
            "cumulative_discrete_work_nmm": reconstructed_total,
            "native_comparison_status": "available"
            if comparison_complete
            else "unavailable_missing_accepted_native_work_or_displacements",
            "native_missing_accepted_times_seconds": missing_native_times,
            "accepted_rows": work_rows,
            "print_bound_scope": "q-coordinate displacement print rounding, sampled ramp-amplitude change from DAT timestamp print rounding, and native external-work print rounding; solver integration error and stepwise-versus-continuous work error are not included",
        },
        "accepted_status_rows": accepted,
        "limits": [
            "Discrete work is evaluated only from complete U blocks at every accepted .sta time; missing samples make the work history unavailable rather than bridged.",
            "The exact load-factor integral follows the deck's serialized piecewise-linear amplitude table; it is not contact force or transferred impulse.",
            "The native external-work comparison does not validate contact equilibrium, material response, or quasi-static behavior.",
        ],
        "implementation_sha256": _implementation_pins(),
    }


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _implementation_pins() -> dict[str, str]:
    launcher_path = Path(observations.__code__.co_filename).resolve()
    return {
        "history_helper_sha256": _sha256(Path(__file__).resolve()),
        "launcher_observations_source_sha256": _sha256(launcher_path),
    }


def _input_closure(
    directory: Path, main_name: str, pinned_names: set[str]
) -> list[str]:
    """Read only frozen input files, expanding `*INCLUDE` within the folder."""
    root = directory.resolve()
    pending = [root / main_name]
    seen = set()
    texts = []
    while pending:
        path = pending.pop(0).resolve()
        if root not in path.parents or not path.is_file():
            raise ValueError("input include is missing or escapes frozen run folder")
        relative_name = path.relative_to(root).as_posix()
        if relative_name not in pinned_names:
            raise ValueError(
                f"input deck file is not pinned by input freeze: {relative_name}"
            )
        if path in seen:
            continue
        seen.add(path)
        text = path.read_text()
        texts.append(text)
        for line in text.splitlines():
            stripped = line.strip()
            if not stripped.upper().startswith("*INCLUDE"):
                continue
            _, attrs = _attributes(stripped)
            name = attrs.get("INPUT")
            if not name:
                raise ValueError("frozen include must name INPUT")
            pending.append(path.parent / name)
    return texts


def audit_directory(directory: str | Path) -> dict:
    """Audit a terminal pilot directory without modifying it."""
    directory = Path(directory).resolve()
    freeze_path = directory / "input-freeze.json"
    execution_path = directory / "execution.json"
    freeze = json.loads(freeze_path.read_text())
    if not execution_path.is_file():
        raise ValueError("terminal execution.json is required")
    execution = json.loads(execution_path.read_text())
    if execution.get("status") == "running":
        raise ValueError("refusing to audit a live native output directory")
    for name, expected in freeze["artifacts_sha256"].items():
        path = directory / name
        if not path.is_file() or _sha256(path) != expected:
            raise ValueError(f"frozen input artifact changed: {name}")
    if execution.get("input_freeze_sha256") != _sha256(freeze_path):
        raise ValueError("execution manifest points to a different input freeze")
    required_outputs = ("pilot.sta", "pilot.dat", "pilot.log")
    for name in required_outputs:
        output_path = directory / name
        if not output_path.is_file():
            raise ValueError(f"terminal run lacks {name}")
        pinned_output = execution.get("outputs_sha256", {}).get(name)
        if pinned_output != _sha256(output_path):
            raise ValueError(f"terminal output differs from execution pin: {name}")
    result = audit_history_texts(
        freeze=freeze,
        deck_texts=_input_closure(
            directory, "pilot.inp", set(freeze["artifacts_sha256"])
        ),
        sta_text=(directory / "pilot.sta").read_text(errors="replace"),
        dat_text=(directory / "pilot.dat").read_text(errors="replace"),
        log_text=(directory / "pilot.log").read_text(errors="replace"),
    )
    result["provenance"] = {
        "execution_status": execution.get("status"),
        "input_freeze_sha256": _sha256(freeze_path),
        "frozen_input_artifacts_sha256": freeze["artifacts_sha256"],
        "implementation_sha256": result["implementation_sha256"],
        "execution_sha256": _sha256(execution_path),
        "terminal_output_sha256": {
            name: execution["outputs_sha256"][name] for name in required_outputs
        },
    }
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path, help="terminal frozen pilot folder")
    parser.add_argument(
        "--output", type=Path, help="optional JSON destination outside the pilot"
    )
    args = parser.parse_args()
    result = audit_directory(args.directory)
    encoded = json.dumps(result, indent=2, allow_nan=False) + "\n"
    if args.output:
        destination = args.output.resolve()
        if args.directory.resolve() in destination.parents:
            raise ValueError("audit output must be outside the frozen pilot directory")
        destination.write_text(encoded)
    else:
        print(encoded, end="")


if __name__ == "__main__":
    main()
