"""Audit the accepted work split for the frozen current finite-actuator pilot.

The command reads one immutable snapshot directory only.  It never opens the
live case directory, starts CalculiX, or treats solver convergence as joint
acceptance.  Work is unavailable if any accepted status time lacks complete
physical-monitor U and driver U/RF rows.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from pathlib import Path

EXPECTED_SNAPSHOT_SHA256 = (
    "2078b21dc37d5c97b95d7f0cfdc4d21ebb034b2445f555e3eeb48c2812a634af"
)
FLOAT_RE = re.compile(r"^[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[EeDd][+-]?\d+)?$")
STA_ATTEMPT_RE = re.compile(r"^(\d+)(U?)$", re.IGNORECASE)
DAT_NODE_RE = re.compile(
    r"^\s*(displacements\s*\(vx,vy,vz\)|forces\s*\(fx,fy,fz\))\s+"
    r"for\s+set\s+(\S+)\s+and\s+time\s+(\S+)\s*$",
    re.IGNORECASE,
)
ENERGY_RE = re.compile(
    r"^\s*total\s+(internal|kinetic)\s+energy\s+for\s+set\s+"
    r"(\S+)\s+and\s+time\s+(\S+)\s*$",
    re.IGNORECASE,
)
CONTACT_COUNT_RE = re.compile(
    r"^\s*total\s+number\s+of\s+contact\s+elements\s+for\s+time\s+(\S+)\s*$",
    re.IGNORECASE,
)
CELS_RE = re.compile(
    r"^\s*contact\s+spring\s+energy\s+\(slave\s+element\+face,energy\)\s+"
    r"for\s+all\s+contact\s+elements\s+(?:and|for)\s+time\s+(\S+)\s*$",
    re.IGNORECASE,
)


class AuditError(ValueError):
    """Input or observation coverage is insufficient for a bounded audit."""


@dataclass(frozen=True)
class Number:
    value: Decimal
    token: str
    half_quantum: Decimal


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _number(token: str) -> Number:
    if not FLOAT_RE.fullmatch(token):
        raise AuditError(f"invalid numeric token: {token!r}")
    try:
        value = Decimal(token.replace("D", "E").replace("d", "e"))
    except InvalidOperation as error:
        raise AuditError(f"invalid numeric token: {token!r}") from error
    if not value.is_finite():
        raise AuditError(f"nonfinite numeric token: {token!r}")
    exponent = value.as_tuple().exponent
    half_quantum = Decimal(5).scaleb(exponent - 1)
    return Number(value, token, abs(half_quantum))


def _json_decimal(data: bytes, name: str):
    try:
        return json.loads(data.decode("utf-8"), parse_float=Decimal)
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise AuditError(f"invalid JSON artifact {name}") from error


def _cards(text: str):
    header = None
    rows = []
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("**"):
            continue
        if line.startswith("*"):
            if header is not None:
                yield header, rows
            header, rows = line, []
        elif header is not None:
            rows.append(line)
    if header is not None:
        yield header, rows


def _attrs(header: str) -> tuple[str, dict[str, str]]:
    pieces = header.replace(" ", "").split(",")
    keyword = pieces[0].upper()
    attrs = {}
    for part in pieces[1:]:
        if "=" in part:
            key, value = part.split("=", 1)
            attrs[key.upper()] = value
        else:
            attrs[part.upper()] = ""
    return keyword, attrs


def _single_card(cards, keyword: str, predicate=lambda _attrs: True):
    matches = []
    for header, rows in cards:
        found_keyword, attrs = _attrs(header)
        if found_keyword == keyword and predicate(attrs):
            matches.append((header, attrs, rows))
    if len(matches) != 1:
        raise AuditError(f"expected exactly one {keyword} card; found {len(matches)}")
    return matches[0]


def _input_bundle(snapshot_dir: Path, manifest: dict) -> dict:
    files = manifest.get("files")
    if not isinstance(files, dict):
        raise AuditError("snapshot manifest has no file map")

    def read_pinned(name: str) -> bytes:
        info = files.get(name)
        if not isinstance(info, dict):
            raise AuditError(f"snapshot is missing required artifact {name}")
        path = snapshot_dir / name
        data = path.read_bytes()
        digest = _sha256(data)
        if len(data) != info.get("bytes") or digest != info.get("sha256"):
            raise AuditError(f"snapshot artifact pin mismatch: {name}")
        return data

    freeze_bytes = read_pinned("input-freeze.json")
    freeze = _json_decimal(freeze_bytes, "input-freeze.json")
    if freeze.get("schema") != "wood_joint_current_spring_actuator_input/v1":
        raise AuditError("unexpected current finite-actuator input freeze")
    if freeze.get("mechanical_acceptance") is not False:
        raise AuditError("input freeze must explicitly withhold mechanical acceptance")

    frozen_artifacts = freeze.get("artifacts_sha256")
    if not isinstance(frozen_artifacts, dict) or not frozen_artifacts:
        raise AuditError("input freeze has no artifact pins")
    input_hashes = {}
    for name, expected in frozen_artifacts.items():
        data = read_pinned(name)
        if _sha256(data) != expected:
            raise AuditError(f"input-freeze artifact hash mismatch: {name}")
        input_hashes[name] = expected

    driver = _json_decimal(
        read_pinned("actuator-driving.json"), "actuator-driving.json"
    )
    source = _json_decimal(
        read_pinned("source-actuator-reference.json"),
        "source-actuator-reference.json",
    )
    initial = _json_decimal(
        read_pinned("initial-driver-state.json"), "initial-driver-state.json"
    )
    deck_bytes = read_pinned("pilot.inp")
    deck_text = deck_bytes.decode("utf-8")
    cards = list(_cards(deck_text))
    driver_nodes = driver.get("driver_nodes", {})
    proxy = int(driver_nodes.get("proxy_node", -1))
    target = int(driver_nodes.get("target_node", -1))
    if (proxy, target) != (117162, 117163):
        raise AuditError("driver nodes do not match the frozen diagnostic contract")

    equation_header, _equation_attrs, equation_rows = _single_card(cards, "*EQUATION")
    del equation_header
    if not equation_rows or not equation_rows[0].strip().isdigit():
        raise AuditError("malformed emitted MPC term count")
    term_count = int(equation_rows[0])
    fields = [
        field.strip()
        for row in equation_rows[1:]
        for field in row.split(",")
        if field.strip()
    ]
    if term_count <= 1 or len(fields) != 3 * term_count:
        raise AuditError("emitted MPC term count does not match its serialized triples")
    actual_coefficients: dict[tuple[int, int], tuple[Decimal, str]] = {}
    terms = []
    for index in range(0, len(fields), 3):
        try:
            node_id, dof = int(fields[index]), int(fields[index + 1])
        except ValueError as error:
            raise AuditError("invalid emitted MPC node/DOF") from error
        coefficient = _number(fields[index + 2])
        key = (node_id, dof)
        if key in actual_coefficients:
            raise AuditError(f"duplicate emitted MPC term {key}")
        actual_coefficients[key] = (coefficient.value, coefficient.token)
        terms.append((node_id, dof, coefficient))
    if terms[0][0:2] != (proxy, 1) or terms[0][2].value != Decimal(1):
        raise AuditError("proxy must be the first MPC term with coefficient +1")
    if any(node in (proxy, target) for node, _dof, _coefficient in terms[1:]):
        raise AuditError("physical MPC support includes a driver node")
    if target in {node for node, _dof in actual_coefficients}:
        raise AuditError("prescribed target must remain outside the physical MPC")
    mpc_weights = {
        key: (-coefficient, token)
        for key, (coefficient, token) in actual_coefficients.items()
        if key != (proxy, 1)
    }

    reference_terms = source.get("equation", {}).get(
        "physical_terms_before_normalization", []
    )
    reference_weights: dict[tuple[int, int], Decimal] = {}
    for raw_node, raw_dof, raw_weight in reference_terms:
        key = (int(raw_node), int(raw_dof))
        if key in reference_weights:
            raise AuditError(f"duplicate source unit weight {key}")
        reference_weights[key] = (
            raw_weight if isinstance(raw_weight, Decimal) else Decimal(str(raw_weight))
        )
    if len(reference_weights) != term_count - 1 or set(reference_weights) != set(
        mpc_weights
    ):
        raise AuditError(
            "emitted MPC support differs from the frozen source unit pattern"
        )

    serialization_rows = []
    max_coefficient_error = Decimal(0)
    max_source_text_bound = Decimal(0)
    for key, (weight, coefficient_token) in mpc_weights.items():
        error = abs(weight - reference_weights[key])
        bound = _number(coefficient_token).half_quantum
        if error > bound:
            raise AuditError(
                f"serialized source unit coefficient exceeds rounding bound: {key}"
            )
        max_coefficient_error = max(max_coefficient_error, error)
        max_source_text_bound = max(max_source_text_bound, bound)
        serialization_rows.append(
            {
                "node": key[0],
                "dof": key[1],
                "serialized_weight": weight,
                "source_weight": reference_weights[key],
                "half_text_quantum": bound,
            }
        )

    spring_element = _single_card(
        cards, "*ELEMENT", lambda attrs: attrs.get("TYPE", "").upper() == "SPRING2"
    )
    if spring_element[1].get("ELSET", "").upper() != "ACTUATOR_SPRING":
        raise AuditError("actuator spring element set does not match metadata")
    if len(spring_element[2]) != 1:
        raise AuditError("expected one serialized actuator spring element")
    spring_fields = [part.strip() for part in spring_element[2][0].split(",")]
    if len(spring_fields) != 3:
        raise AuditError("malformed actuator SPRING2 row")
    element_id, end_a, end_b = map(int, spring_fields)
    expected_ends = (proxy, target)
    stiffness_card = _single_card(
        cards,
        "*SPRING",
        lambda attrs: attrs.get("ELSET", "").upper() == "ACTUATOR_SPRING",
    )
    if len(stiffness_card[2]) != 2 or stiffness_card[2][0].replace(" ", "") != "1,1":
        raise AuditError("unsupported actuator spring component declaration")
    stiffness = _number(stiffness_card[2][1].strip()).value
    declared_stiffness = driver.get("actuator_spring", {}).get("stiffness_n_per_mm")
    if Decimal(str(declared_stiffness)) != stiffness or (end_a, end_b) != expected_ends:
        raise AuditError(
            "actual actuator spring order or stiffness differs from metadata"
        )

    if any(
        _attrs(header)[0] in {"*CLOAD", "*DLOAD", "*DSLOAD"} for header, _rows in cards
    ):
        raise AuditError("pilot contains an uncontracted direct load card")
    boundary_cards = [
        (attrs, rows)
        for header, rows in cards
        if _attrs(header)[0] == "*BOUNDARY"
        for attrs in [_attrs(header)[1]]
    ]
    target_boundaries = []
    for attrs, rows in boundary_cards:
        if attrs.get("AMPLITUDE", "").upper() != "Q_TARGET_HISTORY":
            continue
        target_boundaries.extend(rows)
    if target_boundaries != ["117163,1,1,1.15"]:
        raise AuditError("actual prescribed target boundary differs from frozen target")
    if not any(
        _attrs(header)[0] == "*AMPLITUDE"
        and _attrs(header)[1].get("NAME", "").upper() == "Q_TARGET_HISTORY"
        for header, _rows in cards
    ):
        raise AuditError("target amplitude table is absent")

    monitor_nodes = tuple(int(node) for node in freeze.get("monitor_nodes", []))
    if len(set(monitor_nodes)) != len(monitor_nodes) or not monitor_nodes:
        raise AuditError("physical monitor node set is missing or duplicated")
    if initial.get("status") != "PARENT_CHECKED_INPUT_DEFINED_INITIAL_DRIVER_STATE":
        raise AuditError(
            "input-defined initial driver state has not been parent checked"
        )
    if initial.get("source_pilot_sha256") != files["pilot.inp"]["sha256"]:
        raise AuditError("initial-state record is not bound to the frozen pilot bytes")
    if initial.get("input_freeze_sha256") != files["input-freeze.json"]["sha256"]:
        raise AuditError("initial-state record is not bound to the frozen input freeze")
    if [int(x) for x in initial.get("spring_end_node_ids", [])] != list(expected_ends):
        raise AuditError("initial-state record spring order differs from actual deck")
    if (
        Decimal(str(initial.get("actuator_spring", {}).get("stiffness_n_per_mm")))
        != stiffness
    ):
        raise AuditError("initial-state record stiffness differs from actual deck")
    q0 = {
        "q_physical_mm": Decimal(str(initial["q_physical_mm"])),
        "q_proxy_mm": Decimal(str(initial["q_proxy_mm"])),
        "q_target_mm": Decimal(str(initial["q_target_mm"])),
        "gap_mm": Decimal(str(initial["spring_gap_mm"])),
        "energy_nmm": Decimal(str(initial["spring_energy_nmm"])),
        "force_n": Decimal(str(initial["actuator_force_n"])),
    }
    expected_gap = q0["q_target_mm"] - q0["q_proxy_mm"]
    expected_energy = Decimal("0.5") * stiffness * expected_gap**2
    expected_force = stiffness * expected_gap
    if (
        q0["gap_mm"] != expected_gap
        or q0["energy_nmm"] != expected_energy
        or q0["force_n"] != expected_force
    ):
        raise AuditError("checked initial spring state is internally inconsistent")
    if initial.get("physical_or_contact_initial_energy_assigned") is not False:
        raise AuditError("initial record must not assign physical/contact energy")

    return {
        "freeze": freeze,
        "driver": driver,
        "source": source,
        "initial": initial,
        "initial_state": q0,
        "monitor_nodes": frozenset(monitor_nodes),
        "proxy_node": proxy,
        "target_node": target,
        "stiffness": stiffness,
        "spring_element_id": element_id,
        "spring_endpoints": (end_a, end_b),
        "mpc_weights": mpc_weights,
        "source_weights": reference_weights,
        "coefficient_serialization": serialization_rows,
        "max_coefficient_error": max_coefficient_error,
        "max_source_text_bound": max_source_text_bound,
        "input_hashes": input_hashes,
        "freeze_hash": _sha256(freeze_bytes),
        "pilot_hash": files["pilot.inp"]["sha256"],
        "driver_hash": files["actuator-driving.json"]["sha256"],
        "source_reference_hash": files["source-actuator-reference.json"]["sha256"],
    }


def _parse_sta(text: str) -> tuple[list[dict], int]:
    accepted = []
    rejected = 0
    seen = set()
    for line in text.splitlines():
        fields = line.split()
        if not fields or not fields[0].isdigit():
            continue
        if len(fields) != 7 or not fields[1].isdigit():
            raise AuditError("malformed numeric row in accepted status history")
        attempt = STA_ATTEMPT_RE.fullmatch(fields[2])
        if attempt is None or not fields[3].isdigit():
            raise AuditError("malformed status-history attempt row")
        row = {
            "step": int(fields[0]),
            "increment": int(fields[1]),
            "attempt": int(attempt.group(1)),
            "unaccepted": bool(attempt.group(2)),
            "iterations": int(fields[3]),
            "total_time": _number(fields[4]),
            "step_time": _number(fields[5]),
            "increment_time": _number(fields[6]),
        }
        if row["unaccepted"]:
            rejected += 1
            continue
        key = (row["step"], row["increment"])
        if key in seen:
            raise AuditError("duplicate accepted status-history increment")
        seen.add(key)
        if accepted and row["total_time"].value <= accepted[-1]["total_time"].value:
            raise AuditError("accepted status times are not increasing")
        if row["step"] != 1 or row["step_time"].value != row["total_time"].value:
            raise AuditError("unsupported or internally inconsistent step time")
        accepted.append(row)
    if not accepted:
        raise AuditError("status history contains no accepted increment")
    accepted_increments = [row["increment"] for row in accepted]
    if accepted_increments != list(range(1, len(accepted_increments) + 1)):
        raise AuditError(
            "accepted status history has a missing increment; refusing to bridge it"
        )
    return accepted, rejected


def _dat_blocks(text: str, bundle: dict) -> dict:
    """Read complete physical U and driver U/RF blocks in one text pass."""
    expected = {
        ("displacements", "PILOT_MONITOR"): bundle["monitor_nodes"],
        ("displacements", "ACTUATOR_DRIVER"): frozenset(
            {bundle["proxy_node"], bundle["target_node"]}
        ),
        ("forces", "ACTUATOR_DRIVER"): frozenset(
            {bundle["proxy_node"], bundle["target_node"]}
        ),
    }
    records: dict[Decimal, dict] = {}
    lines = text.splitlines()
    index = 0
    while index < len(lines):
        match = DAT_NODE_RE.fullmatch(lines[index])
        if match is None:
            index += 1
            continue
        field = (
            "displacements"
            if match.group(1).lower().startswith("displacements")
            else "forces"
        )
        set_name = match.group(2).upper()
        key = (field, set_name)
        if key not in expected:
            index += 1
            continue
        time = _number(match.group(3))
        rows = {}
        cursor = index + 1
        while cursor < len(lines):
            line = lines[cursor].strip()
            if not line:
                if rows:
                    break
                cursor += 1
                continue
            fields = line.split()
            if (
                len(fields) != 4
                or not fields[0].isdigit()
                or not all(FLOAT_RE.fullmatch(x) for x in fields[1:])
            ):
                break
            node = int(fields[0])
            if node not in expected[key] or node in rows:
                raise AuditError(f"unexpected or duplicate node row in DAT {key}")
            values = tuple(_number(token) for token in fields[1:])
            rows[node] = values
            cursor += 1
        if set(rows) == set(expected[key]):
            state = records.setdefault(time.value, {"time": time})
            if key in state:
                raise AuditError(
                    f"duplicate complete DAT block at time {time.token}: {key}"
                )
            state[key] = rows
        # Partial blocks are deliberately ignored. If one belongs to an
        # accepted status time, the coverage check below refuses the audit.
        index = max(index + 1, cursor)
    return records


def _match_time(status_time: Number, sample_time: Number) -> bool:
    return abs(status_time.value - sample_time.value) <= (
        status_time.half_quantum + sample_time.half_quantum
    )


def _bound(row: tuple[Number, Number, Number], dof: int) -> Decimal:
    return row[dof - 1].half_quantum


def _weighted_projection(weights: dict, displacements: dict) -> tuple[Decimal, Decimal]:
    value_terms = []
    bound_terms = []
    for (node, dof), raw_weight in weights.items():
        weight = raw_weight[0] if isinstance(raw_weight, tuple) else raw_weight
        coordinate = displacements[node][dof - 1]
        value_terms.append(weight * coordinate.value)
        bound_terms.append(abs(weight) * coordinate.half_quantum)
    return sum(value_terms, Decimal(0)), sum(bound_terms, Decimal(0))


def _parse_energy(text: str) -> dict:
    lines = text.splitlines()
    result: dict[Decimal, dict] = {}
    index = 0
    while index < len(lines):
        match = ENERGY_RE.fullmatch(" ".join(lines[index].split()))
        if match is None:
            index += 1
            continue
        kind = match.group(1).lower()
        set_name = match.group(2).upper()
        time = _number(match.group(3))
        cursor = index + 1
        while cursor < len(lines) and not lines[cursor].strip():
            cursor += 1
        if (
            cursor < len(lines)
            and len(lines[cursor].split()) == 1
            and FLOAT_RE.fullmatch(lines[cursor].strip())
        ):
            value = _number(lines[cursor].strip())
            row = result.setdefault(time.value, {"time": time})
            key = (kind, set_name)
            if key in row:
                raise AuditError(f"duplicate DAT energy total {key} at {time.token}")
            row[key] = value
            index = cursor + 1
        else:
            index += 1
    return result


def _parse_contact_diagnostics(text: str) -> dict:
    lines = text.splitlines()
    counts = []
    cels_rows = []
    index = 0
    while index < len(lines):
        count_match = CONTACT_COUNT_RE.fullmatch(" ".join(lines[index].split()))
        if count_match is not None:
            time = _number(count_match.group(1))
            cursor = index + 1
            while cursor < len(lines) and not lines[cursor].strip():
                cursor += 1
            if cursor < len(lines) and lines[cursor].strip().isdigit():
                counts.append((time, int(lines[cursor].strip())))
        cels_match = CELS_RE.fullmatch(" ".join(lines[index].split()))
        if cels_match is not None:
            time = _number(cels_match.group(1))
            cursor = index + 1
            block = []
            while cursor < len(lines):
                fields = lines[cursor].split()
                if (
                    len(fields) == 3
                    and fields[0].isdigit()
                    and fields[1].isdigit()
                    and FLOAT_RE.fullmatch(fields[2])
                ):
                    block.append((int(fields[0]), int(fields[1]), _number(fields[2])))
                    cursor += 1
                elif not fields and not block:
                    cursor += 1
                else:
                    break
            if block:
                cels_rows.append((time, block))
        index += 1
    return {"counts": counts, "cels_rows": cels_rows}


def _log_increment(text: str, status: dict) -> dict:
    wanted = (status["step"], status["increment"], status["attempt"])
    lines = text.splitlines()
    begin = None
    end = len(lines)
    header = re.compile(r"\bincrement\s+(\d+)\s+attempt\s+(\d+)\b", re.IGNORECASE)
    for index, line in enumerate(lines):
        match = header.search(line)
        if (
            match
            and begin is None
            and (1, int(match.group(1)), int(match.group(2))) == wanted
        ):
            begin = index
        elif match and begin is not None:
            end = index
            break
    if begin is None:
        return {}
    block = "\n".join(lines[begin:end])
    labels = (
        "external work",
        "internal energy",
        "kinetic energy",
        "elastic contact energy",
        "total energy",
        "energy balance (absolute)",
        "energy balance (relative)",
    )
    values = {}
    for label in labels:
        match = re.search(
            rf"{re.escape(label)}\s*=\s*({FLOAT_RE.pattern[1:-1]})",
            block,
            re.IGNORECASE,
        )
        if match:
            values[label] = _number(match.group(1))
    actual_time = re.search(r"actual total time\s*=\s*(\S+)", block, re.IGNORECASE)
    if actual_time:
        values["actual_total_time"] = _number(actual_time.group(1))
    return values


def _f(value: Decimal | None):
    return None if value is None else float(value)


def audit_response(
    *,
    bundle: dict,
    sta_text: str,
    dat_text: str,
    log_text: str,
) -> dict:
    accepted, rejected = _parse_sta(sta_text)
    records = _dat_blocks(dat_text, bundle)
    energy = _parse_energy(dat_text)
    contact = _parse_contact_diagnostics(dat_text)

    matched = []
    used_times = set()
    for status in accepted:
        candidates = []
        for time, state in records.items():
            if time in used_times or not _match_time(
                status["total_time"], state["time"]
            ):
                continue
            needed = {
                ("displacements", "PILOT_MONITOR"),
                ("displacements", "ACTUATOR_DRIVER"),
                ("forces", "ACTUATOR_DRIVER"),
            }
            if needed.issubset(state):
                candidates.append((time, state))
        if len(candidates) != 1:
            raise AuditError(
                "accepted .sta time lacks one unique complete physical-U and "
                f"driver-U/RF DAT state: {status['total_time'].token}"
            )
        time, state = candidates[0]
        used_times.add(time)
        matched.append((status, state))

    initial = bundle["initial_state"]
    stiffness = bundle["stiffness"]
    states = []
    for status, sample in matched:
        monitor = sample[("displacements", "PILOT_MONITOR")]
        driver_u = sample[("displacements", "ACTUATOR_DRIVER")]
        driver_rf = sample[("forces", "ACTUATOR_DRIVER")]
        q_a, q_a_bound = _weighted_projection(bundle["mpc_weights"], monitor)
        q_source, q_source_bound = _weighted_projection(
            bundle["source_weights"], monitor
        )
        q_proxy = driver_u[bundle["proxy_node"]][0].value
        q_proxy_bound = driver_u[bundle["proxy_node"]][0].half_quantum
        q_target = driver_u[bundle["target_node"]][0].value
        q_target_bound = driver_u[bundle["target_node"]][0].half_quantum
        force_measured = driver_rf[bundle["target_node"]][0]
        force_proxy_rf = driver_rf[bundle["proxy_node"]][0]
        gap = q_target - q_proxy
        gap_bound = q_target_bound + q_proxy_bound
        force_model = stiffness * gap
        force_model_bound = stiffness * gap_bound
        force_residual = force_measured.value - force_model
        force_bound = force_measured.half_quantum + force_model_bound
        mpc_residual = q_a - q_proxy
        mpc_bound = q_a_bound + q_proxy_bound
        source_mpc_residual = q_source - q_proxy
        input_rounding_projection_bound = (
            sum(
                abs(bundle["mpc_weights"][key][0] - bundle["source_weights"][key])
                * abs(monitor[key[0]][key[1] - 1].value)
                + abs(bundle["source_weights"][key])
                * monitor[key[0]][key[1] - 1].half_quantum
                for key in bundle["mpc_weights"]
            )
            + q_proxy_bound
        )
        spring_energy = Decimal("0.5") * stiffness * gap**2
        spring_energy_bound = (
            Decimal("0.5") * stiffness * (2 * abs(gap) * gap_bound + gap_bound**2)
        )

        time = sample["time"]
        energies = energy.get(time.value, {})
        states.append(
            {
                "step": status["step"],
                "increment": status["increment"],
                "attempt": status["attempt"],
                "iterations": status["iterations"],
                "accepted_time_seconds": float(status["total_time"].value),
                "dat_time_seconds": float(time.value),
                "dat_time_token": time.token,
                "q_physical_emitted_mm": _f(q_a),
                "q_physical_emitted_print_bound_mm": _f(q_a_bound),
                "q_physical_source_weights_mm": _f(q_source),
                "q_physical_source_print_bound_mm": _f(q_source_bound),
                "q_proxy_mm": _f(q_proxy),
                "q_proxy_print_bound_mm": _f(q_proxy_bound),
                "q_target_mm": _f(q_target),
                "q_target_print_bound_mm": _f(q_target_bound),
                "spring_gap_mm": _f(gap),
                "spring_gap_print_bound_mm": _f(gap_bound),
                "actuator_force_model_n": _f(force_model),
                "actuator_force_measured_target_rf_n": _f(force_measured.value),
                "actuator_force_target_rf_print_bound_n": _f(
                    force_measured.half_quantum
                ),
                "actuator_force_model_print_bound_n": _f(force_model_bound),
                "actuator_force_residual_n": _f(force_residual),
                "actuator_force_residual_bound_n": _f(force_bound),
                "actuator_force_within_print_bound": abs(force_residual) <= force_bound,
                "proxy_raw_rf_n_diagnostic_only": _f(force_proxy_rf.value),
                "mpc_q_emitted_minus_proxy_mm": _f(mpc_residual),
                "mpc_q_emitted_minus_proxy_bound_mm": _f(mpc_bound),
                "mpc_q_emitted_closure_within_print_bound": abs(mpc_residual)
                <= mpc_bound,
                "source_weight_q_minus_proxy_mm": _f(source_mpc_residual),
                "source_weight_q_minus_proxy_bound_mm": _f(
                    input_rounding_projection_bound
                ),
                "source_weight_q_within_print_and_mpc_rounding_bound": abs(
                    source_mpc_residual
                )
                <= input_rounding_projection_bound,
                "actuator_spring_energy_nmm": _f(spring_energy),
                "actuator_spring_energy_print_bound_nmm": _f(spring_energy_bound),
                "continuum_internal_energy_nmm": _f(
                    energies.get(
                        ("internal", "CURRENT_ALL_ELEMENTS"),
                        Number(Decimal(0), "", Decimal(0)),
                    ).value
                )
                if ("internal", "CURRENT_ALL_ELEMENTS") in energies
                else None,
                "continuum_kinetic_energy_nmm": _f(
                    energies.get(
                        ("kinetic", "CURRENT_ALL_ELEMENTS"),
                        Number(Decimal(0), "", Decimal(0)),
                    ).value
                )
                if ("kinetic", "CURRENT_ALL_ELEMENTS") in energies
                else None,
                "nut_carrier_internal_energy_subset_nmm": _f(
                    energies[("internal", "CURRENT_NUT_CARRIERS")].value
                )
                if ("internal", "CURRENT_NUT_CARRIERS") in energies
                else None,
                "nut_carrier_kinetic_energy_subset_nmm": _f(
                    energies[("kinetic", "CURRENT_NUT_CARRIERS")].value
                )
                if ("kinetic", "CURRENT_NUT_CARRIERS") in energies
                else None,
            }
        )

    work = []
    previous = {
        "q_a": initial["q_physical_mm"],
        "q_proxy": initial["q_proxy_mm"],
        "q_target": initial["q_target_mm"],
        "gap": initial["gap_mm"],
        "force": initial["force_n"],
        "force_bound": Decimal(0),
        "q_a_bound": Decimal(0),
        "q_proxy_bound": Decimal(0),
        "q_target_bound": Decimal(0),
        "gap_bound": Decimal(0),
        "physical_energy": None,
    }
    cumulative = {
        "target_work": Decimal(0),
        "spring_energy_change": Decimal(0),
        "proxy_work": Decimal(0),
        "physical_work": Decimal(0),
        "mpc_work_closure": Decimal(0),
    }
    for state in states:
        current = {
            "q_a": Decimal(str(state["q_physical_emitted_mm"])),
            "q_proxy": Decimal(str(state["q_proxy_mm"])),
            "q_target": Decimal(str(state["q_target_mm"])),
            "gap": Decimal(str(state["spring_gap_mm"])),
            "force": Decimal(str(state["actuator_force_measured_target_rf_n"])),
            "force_bound": Decimal(
                str(state["actuator_force_target_rf_print_bound_n"])
            ),
            "q_a_bound": Decimal(str(state["q_physical_emitted_print_bound_mm"])),
            "q_proxy_bound": Decimal(str(state["q_proxy_print_bound_mm"])),
            "q_target_bound": Decimal(str(state["q_target_print_bound_mm"])),
            "gap_bound": Decimal(str(state["spring_gap_print_bound_mm"])),
            "physical_energy": None,
        }
        if (
            state["continuum_internal_energy_nmm"] is not None
            and state["continuum_kinetic_energy_nmm"] is not None
        ):
            current["physical_energy"] = Decimal(
                str(state["continuum_internal_energy_nmm"])
            ) + Decimal(str(state["continuum_kinetic_energy_nmm"]))
        average_force = (previous["force"] + current["force"]) / 2
        average_force_bound = (previous["force_bound"] + current["force_bound"]) / 2
        work_target = average_force * (current["q_target"] - previous["q_target"])
        delta_spring = (
            Decimal("0.5") * stiffness * (current["gap"] ** 2 - previous["gap"] ** 2)
        )
        work_proxy = average_force * (current["q_proxy"] - previous["q_proxy"])
        work_physical = average_force * (current["q_a"] - previous["q_a"])
        mpc_work_closure = work_proxy - work_physical
        identity_residual = work_target - delta_spring - work_proxy
        target_work_bound = (
            abs(current["q_target"] - previous["q_target"]) * average_force_bound
            + abs(average_force)
            * (current["q_target_bound"] + previous["q_target_bound"])
            + average_force_bound
            * (current["q_target_bound"] + previous["q_target_bound"])
        )
        proxy_work_bound = (
            abs(current["q_proxy"] - previous["q_proxy"]) * average_force_bound
            + abs(average_force)
            * (current["q_proxy_bound"] + previous["q_proxy_bound"])
            + average_force_bound
            * (current["q_proxy_bound"] + previous["q_proxy_bound"])
        )
        physical_work_bound = (
            abs(current["q_a"] - previous["q_a"]) * average_force_bound
            + abs(average_force) * (current["q_a_bound"] + previous["q_a_bound"])
            + average_force_bound * (current["q_a_bound"] + previous["q_a_bound"])
        )
        spring_bound = (
            Decimal("0.5")
            * stiffness
            * (
                2 * abs(current["gap"]) * current["gap_bound"]
                + current["gap_bound"] ** 2
                + 2 * abs(previous["gap"]) * previous["gap_bound"]
                + previous["gap_bound"] ** 2
            )
        )
        identity_bound = target_work_bound + proxy_work_bound + spring_bound
        cumulative["target_work"] += work_target
        cumulative["spring_energy_change"] += delta_spring
        cumulative["proxy_work"] += work_proxy
        cumulative["physical_work"] += work_physical
        cumulative["mpc_work_closure"] += mpc_work_closure
        energy_increment = None
        energy_comparison = "unavailable_no_prior_native_physical_energy_state"
        if (
            previous["physical_energy"] is not None
            and current["physical_energy"] is not None
        ):
            energy_increment = current["physical_energy"] - previous["physical_energy"]
            energy_comparison = "change_between_adjacent_accepted_continuum_energy_rows"
        work.append(
            {
                "increment": state["increment"],
                "time_seconds": state["accepted_time_seconds"],
                "delta_target_work_nmm": _f(work_target),
                "delta_target_work_print_bound_nmm": _f(target_work_bound),
                "delta_actuator_spring_energy_nmm": _f(delta_spring),
                "delta_actuator_spring_energy_print_bound_nmm": _f(spring_bound),
                "delta_proxy_work_nmm": _f(work_proxy),
                "delta_proxy_work_print_bound_nmm": _f(proxy_work_bound),
                "delta_physical_weighted_work_nmm": _f(work_physical),
                "delta_physical_weighted_work_print_bound_nmm": _f(physical_work_bound),
                "proxy_minus_physical_work_nmm": _f(mpc_work_closure),
                "target_minus_spring_and_proxy_work_nmm": _f(identity_residual),
                "target_spring_proxy_identity_print_bound_nmm": _f(identity_bound),
                "target_spring_proxy_identity_within_print_bound": abs(
                    identity_residual
                )
                <= identity_bound,
                "continuum_else_plus_elke_change_nmm": _f(energy_increment),
                "continuum_energy_comparison_scope": energy_comparison,
                "cumulative_target_work_nmm": _f(cumulative["target_work"]),
                "cumulative_actuator_spring_energy_change_nmm": _f(
                    cumulative["spring_energy_change"]
                ),
                "cumulative_proxy_work_nmm": _f(cumulative["proxy_work"]),
                "cumulative_physical_weighted_work_nmm": _f(
                    cumulative["physical_work"]
                ),
                "cumulative_proxy_minus_physical_work_nmm": _f(
                    cumulative["mpc_work_closure"]
                ),
            }
        )
        previous = current

    contact_matches = []
    for time, rows in contact["cels_rows"]:
        status_matches = [
            row for row in accepted if _match_time(row["total_time"], time)
        ]
        if len(status_matches) == 1:
            cnum_matches = [
                count
                for count_time, count in contact["counts"]
                if _match_time(status_matches[0]["total_time"], count_time)
            ]
            contact_matches.append(
                {
                    "time_seconds": float(time.value),
                    "cels_row_count": len(rows),
                    "cels_raw_sum_nmm_diagnostic_only": _f(
                        sum((row[2].value for row in rows), Decimal(0))
                    ),
                    "cnum": cnum_matches[0] if len(cnum_matches) == 1 else None,
                    "cels_count_matches_cnum": len(cnum_matches) == 1
                    and len(rows) == cnum_matches[0],
                    "qualified_for_energy_closure": False,
                }
            )

    log_rows = []
    for status in accepted:
        log_row = _log_increment(log_text, status)
        if log_row:
            log_rows.append(
                {
                    "step": status["step"],
                    "increment": status["increment"],
                    "attempt": status["attempt"],
                    "values": {key: _f(value.value) for key, value in log_row.items()},
                    "scope": "native global solver summary; not the controller-work oracle",
                }
            )

    checks = {
        "all_accepted_sta_times_have_complete_monitor_and_driver_rows": True,
        "all_target_rf_rows_match_200_times_target_minus_proxy_with_print_bounds": all(
            row["actuator_force_within_print_bound"] for row in states
        ),
        "all_emitted_mpc_physical_projection_rows_match_proxy_with_print_bounds": all(
            row["mpc_q_emitted_closure_within_print_bound"] for row in states
        ),
        "all_source_weight_projections_match_proxy_with_mpc_rounding_bounds": all(
            row["source_weight_q_within_print_and_mpc_rounding_bound"] for row in states
        ),
        "all_increment_spring_proxy_work_identities_close_with_print_bounds": all(
            row["target_spring_proxy_identity_within_print_bound"] for row in work
        ),
    }
    return {
        "schema": "wood_joint_current_finite_actuator_work_audit/v1",
        "status": "ACCOUNTING_REPRODUCED_PREFIX_ONLY"
        if all(checks.values())
        else "ACCOUNTING_CHECKS_REVIEW_REQUIRED",
        "scope": "Accepted immutable output prefix only; no complete-joint acceptance, capacity, time-accuracy, or mechanical acceptance.",
        "input_coordinates": {
            "convention": "q_proxy + sum(a_i U_i) = 0; q_physical_emitted = sum(-a_i U_i)",
            "proxy_node": bundle["proxy_node"],
            "target_node": bundle["target_node"],
            "spring_element_id": bundle["spring_element_id"],
            "spring_endpoints": list(bundle["spring_endpoints"]),
            "stiffness_n_per_mm": _f(stiffness),
            "physical_mpc_term_count": len(bundle["mpc_weights"]),
            "source_unit_coefficients_checked": len(
                bundle["coefficient_serialization"]
            ),
            "max_source_weight_serialization_error": _f(
                bundle["max_coefficient_error"]
            ),
            "max_source_text_half_quantum": _f(bundle["max_source_text_bound"]),
            "initial_driver_state": {
                key: _f(value) for key, value in bundle["initial_state"].items()
            },
            "initial_physical_or_contact_energy_assigned": False,
        },
        "coverage": {
            "accepted_sta_increments": len(accepted),
            "rejected_sta_attempt_rows": rejected,
            "complete_matched_states": len(states),
            "extra_complete_DAT_state_times_not_used": sorted(
                float(time) for time in records if time not in used_times
            ),
            "all_monitor_nodes_per_state": len(bundle["monitor_nodes"]),
        },
        "checks": checks,
        "states": states,
        "accepted_interval_work": work,
        "native_global_energy": {
            "records": log_rows,
            "note": "Keep this solver summary separate from reconstructed target work and the physical continuum ELSE+ELKE state changes.",
        },
        "contact_cels_diagnostic": {
            "records": contact_matches,
            "note": "Raw DAT CELS sums/counts are diagnostic only and excluded from accepted energy closure because the pinned output investigation found a sparse writer/printer index mismatch.",
        },
        "mechanical_acceptance": False,
        "rejected_sta_rows_are_not_bridged": True,
    }


def audit_snapshot(
    snapshot_dir: Path, expected_snapshot_hash: str = EXPECTED_SNAPSHOT_SHA256
) -> dict:
    snapshot_dir = snapshot_dir.resolve()
    snapshot_path = snapshot_dir / "snapshot.json"
    manifest_bytes = snapshot_path.read_bytes()
    manifest_hash = _sha256(manifest_bytes)
    if manifest_hash != expected_snapshot_hash:
        raise AuditError(
            "snapshot.json hash differs from the parent-frozen immutable snapshot"
        )
    manifest = _json_decimal(manifest_bytes, "snapshot.json")
    if manifest.get("status") != "IMMUTABLE_LIVE_OUTPUT_PREFIX_SNAPSHOT":
        raise AuditError("snapshot status is not immutable output prefix")
    if manifest.get("mechanical_acceptance") is not False:
        raise AuditError("snapshot must explicitly withhold mechanical acceptance")
    bundle = _input_bundle(snapshot_dir, manifest)
    for filename in ("pilot.sta", "pilot.dat", "pilot.log"):
        if filename not in manifest.get("files", {}):
            raise AuditError(f"snapshot is missing required output {filename}")
    sta_text = (snapshot_dir / "pilot.sta").read_text(encoding="utf-8")
    dat_text = (snapshot_dir / "pilot.dat").read_text(encoding="ascii")
    log_text = (snapshot_dir / "pilot.log").read_text(
        encoding="utf-8", errors="replace"
    )
    for filename, text in (
        ("pilot.sta", sta_text),
        ("pilot.dat", dat_text),
        ("pilot.log", log_text),
    ):
        expected = manifest["files"][filename]["sha256"]
        if (
            _sha256(text.encode("utf-8" if filename != "pilot.dat" else "ascii"))
            != expected
        ):
            raise AuditError(f"snapshot output changed during audit: {filename}")
    sta_rows = [
        " ".join(line.split())
        for line in sta_text.splitlines()
        if line.strip()
        and line.split()[0].isdigit()
        and len(line.split()) == 7
        and not line.split()[2].upper().endswith("U")
    ]
    manifest_sta_rows = [
        " ".join(row.split()) for row in manifest.get("accepted_sta_rows", [])
    ]
    if sta_rows != manifest_sta_rows:
        raise AuditError(
            "accepted .sta row differs from the immutable snapshot manifest"
        )
    result = audit_response(
        bundle=bundle, sta_text=sta_text, dat_text=dat_text, log_text=log_text
    )
    result["provenance"] = {
        "audit_script_sha256": _sha256(Path(__file__).read_bytes()),
        "snapshot_json_sha256": manifest_hash,
        "snapshot_capture_atomic_across_files": manifest.get(
            "capture_atomic_across_files"
        ),
        "snapshot_capture_policy": manifest.get("capture_policy"),
        "snapshot_scope": manifest.get("scope"),
        "source_process_status_at_capture": manifest.get(
            "source_process_status_at_execution_capture"
        ),
        "input_freeze_sha256": bundle["freeze_hash"],
        "pilot_input_sha256": bundle["pilot_hash"],
        "source_actuator_reference_sha256": bundle["source_reference_hash"],
        "actuator_driver_metadata_sha256": bundle["driver_hash"],
        "initial_driver_state_sha256": manifest["files"]["initial-driver-state.json"][
            "sha256"
        ],
        "accepted_status_sha256": manifest["files"]["pilot.sta"]["sha256"],
        "DAT_sha256": manifest["files"]["pilot.dat"]["sha256"],
        "native_log_sha256": manifest["files"]["pilot.log"]["sha256"],
        "snapshot_manifest_file_pins": {
            name: item["sha256"] for name, item in manifest["files"].items()
        },
        "verified_snapshot_file_hashes": {
            name: manifest["files"][name]["sha256"]
            for name in (
                "input-freeze.json",
                "actuator-driving.json",
                "source-actuator-reference.json",
                "initial-driver-state.json",
                "pilot.inp",
                "pilot.sta",
                "pilot.dat",
                "pilot.log",
                *bundle["input_hashes"].keys(),
            )
        },
        "unread_large_artifacts": ["pilot.cel", "pilot.frd", "pilot.cvg"],
    }
    return result


def _main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("snapshot", type=Path, help="immutable snapshot directory only")
    parser.add_argument(
        "--output", type=Path, default=Path(__file__).with_name("report.json")
    )
    parser.add_argument("--expected-snapshot-sha256", default=EXPECTED_SNAPSHOT_SHA256)
    args = parser.parse_args()
    report = audit_snapshot(args.snapshot, args.expected_snapshot_sha256)
    args.output.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(
        json.dumps(
            {
                "status": report["status"],
                "accepted_states": report["coverage"]["complete_matched_states"],
                "work_intervals": len(report["accepted_interval_work"]),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    _main()
