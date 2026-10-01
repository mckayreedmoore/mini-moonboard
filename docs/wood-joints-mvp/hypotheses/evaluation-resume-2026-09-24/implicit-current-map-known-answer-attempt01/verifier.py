#!/usr/bin/env python3
"""Audit frozen DAT/FRD captures for the bounded implicit current-map fixture.

This verifier qualifies one measured M00 A00 map and its zero-density carrier.
It is not a joint acceptance or structural capacity check.  It never launches
CalculiX and writes only the optional post-run verifier.json report.
"""

from __future__ import annotations

import argparse
import ast
from collections import Counter, defaultdict
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation, localcontext
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
ROOT = next(parent for parent in HERE.parents if (parent / ".git").exists())
OUTPUT = HERE / "output"
FREEZE = HERE / "input-freeze.json"
EXPECTED_SCHEMA = "ccx223_implicit_current_map_expected/v1"
ACCEPTANCE_SCHEMA = "ccx223_implicit_current_map_acceptance/v1"
FREEZE_SCHEMA = "ccx223_implicit_current_map_freeze/v1"
EXECUTION_SCHEMA = "ccx223_implicit_current_map_execution/v1"
CASES = ("direct", "mapped_no_carrier", "mapped_carrier")
NATIVE_FILES = ("coupon.dat", "coupon.sta", "coupon.frd", "solver.stdout", "solver.stderr")
REQUIRED_STATIC_FILES = {
    "fixture-design.md", "prepare.py", "run.py", "verifier.py", "expected.json",
    "acceptance.json", "acceptance-proposal.json", "input/direct.inp",
    "input/mapped_no_carrier.inp", "input/mapped_carrier.inp",
    "reference-preflight.md", "rigid-reference-review.md", "parent-review.json",
    "parent-mass-reference.py", "parent-mass-reference.json",
    "parent-rigid-reference.py", "parent-rigid-reference.json",
    "parent-rigid-deviation.py", "parent-rigid-deviation.json",
    "parent-input-audit.py", "parent-input-audit.json",
}
MAX_EXAMPLES_PER_CATEGORY = 20
ARITHMETIC_DECIMAL_FLOOR = Decimal("1e-40")
ARITHMETIC_DECIMAL_PRECISION = 60


def fail(message: str) -> None:
    raise ValueError(message)


def sha_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha(path: Path) -> str:
    return sha_bytes(path.read_bytes())


def strict_json(path: Path) -> dict:
    def unique_pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                fail(f"duplicate JSON key {key!r} in {path}")
            result[key] = value
        return result

    def reject_constant(value):
        fail(f"non-finite JSON value {value!r} in {path}")

    return json.loads(path.read_text(), object_pairs_hook=unique_pairs,
                      parse_constant=reject_constant)


def finite_number(token: str) -> float:
    value = float(token.replace("D", "E").replace("d", "e"))
    if not math.isfinite(value):
        fail(f"non-finite output token {token!r}")
    return value


def decimal_number(token: str) -> Decimal:
    try:
        value = Decimal(token.replace("D", "E").replace("d", "e"))
    except InvalidOperation as exc:
        raise ValueError(f"invalid decimal output token {token!r}") from exc
    if not value.is_finite():
        fail(f"non-finite decimal output token {token!r}")
    return value


def decimal_half_ulp(token: str) -> Decimal:
    """Half the last printed decimal place; normalized scientific zero is exact here."""
    value = decimal_number(token)
    if value == 0:
        return Decimal(0)
    exponent = value.as_tuple().exponent
    return Decimal(5).scaleb(exponent - 1)


def id_digest(ids) -> str:
    return sha_bytes(("\n".join(str(value) for value in sorted(ids)) + "\n").encode("ascii"))


def load_parser(acceptance: dict):
    dependency = acceptance["parser_dependency"]
    parser_path = (HERE / dependency["path"]).resolve()
    if sha(parser_path) != dependency["sha256"]:
        fail("pinned output parser hash differs")
    spec = importlib.util.spec_from_file_location("current_map_pinned_output_parser", parser_path)
    if spec is None or spec.loader is None:
        fail("could not load pinned DAT/FRD parser")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    for name in dependency["functions"]:
        if not callable(getattr(module, name, None)):
            fail(f"pinned parser function {name!r} is unavailable")
    return module


def load_contract(require_ready: bool = False) -> tuple[dict, dict, object]:
    expected = strict_json(HERE / "expected.json")
    acceptance = strict_json(HERE / "acceptance.json")
    if expected.get("schema") != EXPECTED_SCHEMA or expected.get("case_order") != list(CASES):
        fail("unexpected current-map expected schema or case order")
    if acceptance.get("schema") != ACCEPTANCE_SCHEMA or acceptance.get("case_order") != list(CASES):
        fail("unexpected current-map acceptance schema or case order")
    if require_ready and acceptance.get("ready_for_native") is not True:
        fail("acceptance is not marked ready for native capture")
    arithmetic = acceptance["equation_arithmetic_allowance"]
    if Decimal(str(arithmetic["decimal_accumulation_reserve_multiplier"])) != ARITHMETIC_DECIMAL_FLOOR:
        fail("verifier Decimal accumulation reserve differs from acceptance.json")
    if int(arithmetic["decimal_precision_digits"]) != ARITHMETIC_DECIMAL_PRECISION:
        fail("verifier Decimal precision differs from acceptance.json")
    state_rows = expected["linearized_discrete_reference"]["states"]
    if len(state_rows) != acceptance["states"]["accepted_count"]:
        fail("known-answer state count differs from acceptance")
    if len(state_rows) != expected["procedure"]["accepted_increment_count_expected"]:
        fail("known-answer state count differs from procedure")
    if [row["increment"] for row in state_rows] != list(range(1, len(state_rows) + 1)):
        fail("known-answer increments are not contiguous from one")

    output_contract = expected["output_contract"]
    groups = output_contract["node_id_sets"]
    for name, group in groups.items():
        ids = [int(value) for value in group["node_ids"]]
        if len(ids) != group["count"] or len(set(ids)) != len(ids):
            fail(f"bad expected node membership for {name}")
        if ids != sorted(ids):
            fail(f"expected node membership for {name} is not sorted")
        digest = group.get("sha256_sorted_decimal_ids")
        if digest is not None and id_digest(ids) != digest:
            fail(f"expected node membership digest differs for {name}")
    physical = set(map(int, groups["physical_body"]["node_ids"]))
    controls = set(map(int, groups["mapping_controls"]["node_ids"]))
    carrier = set(map(int, groups["zero_density_carrier"]["node_ids"]))
    if physical & controls or physical & carrier or controls & carrier:
        fail("expected physical, controller, and carrier node sets overlap")
    if len(physical) != 11348 or len(controls) != 2 or len(carrier) != 1107:
        fail("unexpected fixture node-set sizes")
    if len(expected["inputs"]) != len(CASES):
        fail("expected input inventory is incomplete")
    for case in CASES:
        if case not in expected["inputs"]:
            fail(f"missing input binding for {case}")
        item = expected["inputs"][case]
        if sha(HERE / item["path"]) != item["sha256"]:
            fail(f"frozen input bytes differ for {case}")
    parser = load_parser(acceptance)
    return expected, acceptance, parser


class Audit:
    """Bounded diagnostics: test every datum but retain only a few examples."""

    def __init__(self):
        self.failures = Counter()
        self.examples = defaultdict(list)
        self.metrics = defaultdict(lambda: {
            "samples": 0, "failures": 0, "max_absolute_error": 0.0,
            "max_allowed_error": 0.0, "max_error_to_allowance": 0.0,
        })

    def problem(self, category: str, message: str) -> None:
        self.failures[category] += 1
        if len(self.examples[category]) < MAX_EXAMPLES_PER_CATEGORY:
            self.examples[category].append(message)

    def scalar(self, metric: str, category: str, actual: float, reference: float,
               absolute: float, relative: float, where: str) -> None:
        row = self.metrics[metric]
        row["samples"] += 1
        try:
            actual, reference = float(actual), float(reference)
        except (TypeError, ValueError, OverflowError):
            self.problem(category, f"{where}: missing or nonnumeric actual/reference")
            row["failures"] += 1
            return
        if not (math.isfinite(actual) and math.isfinite(reference)):
            self.problem(category, f"{where}: non-finite actual/reference")
            row["failures"] += 1
            return
        error = abs(actual - reference)
        allowed = absolute + relative * abs(reference)
        row["max_absolute_error"] = max(row["max_absolute_error"], error)
        row["max_allowed_error"] = max(row["max_allowed_error"], allowed)
        ratio = error / allowed if allowed > 0 else (0.0 if error == 0 else math.inf)
        row["max_error_to_allowance"] = max(row["max_error_to_allowance"], ratio)
        if error > allowed:
            row["failures"] += 1
            self.problem(category,
                         f"{where}: actual={actual:.17g}, reference={reference:.17g}, "
                         f"error={error:.6g}, allowed={allowed:.6g}")

    def upper(self, metric: str, category: str, actual: float, allowed: float,
              where: str) -> None:
        row = self.metrics[metric]
        row["samples"] += 1
        try:
            actual, allowed = float(actual), float(allowed)
        except (TypeError, ValueError, OverflowError):
            self.problem(category, f"{where}: missing or nonnumeric actual/allowance")
            row["failures"] += 1
            return
        if not (math.isfinite(actual) and math.isfinite(allowed)):
            self.problem(category, f"{where}: non-finite actual/allowance")
            row["failures"] += 1
            return
        error = abs(actual)
        row["max_absolute_error"] = max(row["max_absolute_error"], error)
        row["max_allowed_error"] = max(row["max_allowed_error"], allowed)
        ratio = error / allowed if allowed > 0 else (0.0 if error == 0 else math.inf)
        row["max_error_to_allowance"] = max(row["max_error_to_allowance"], ratio)
        if error > allowed:
            row["failures"] += 1
            self.problem(category,
                         f"{where}: abs(actual)={error:.6g}, allowed={allowed:.6g}")

    def result(self) -> dict:
        return {
            "failure_counts": dict(sorted(self.failures.items())),
            "failure_examples_first_20_per_category": dict(sorted(self.examples.items())),
            "metrics": {name: value for name, value in sorted(self.metrics.items())},
        }


def parse_node_coordinates(path: Path) -> dict[int, tuple[float, float, float]]:
    nodes = {}
    in_nodes = False
    for line_no, line in enumerate(path.read_text().splitlines(), 1):
        stripped = line.strip()
        if not stripped or stripped.startswith("**"):
            continue
        if stripped.startswith("*"):
            in_nodes = stripped.split(",", 1)[0].upper() == "*NODE"
            continue
        if not in_nodes:
            continue
        fields = [field.strip() for field in line.split(",")]
        if len(fields) != 4:
            fail(f"{path.name}:{line_no}: malformed node row")
        node = int(fields[0])
        if node in nodes:
            fail(f"{path.name}:{line_no}: duplicate node {node}")
        xyz = tuple(finite_number(value) for value in fields[1:])
        nodes[node] = xyz
    return nodes


def expected_node_sets(expected: dict, case: str, kind: str) -> set[int]:
    groups = expected["output_contract"]["coverage_by_case"][case][f"{kind}_node_groups"]
    return set().union(*(set(map(int, expected["output_contract"]["node_id_sets"][name]["node_ids"]))
                         for name in groups))


def state_index(time_s: float, expected: dict, tolerance: float) -> int:
    states = expected["linearized_discrete_reference"]["states"]
    diffs = [abs(time_s - row["time_s"]) for row in states]
    index = min(range(len(diffs)), key=diffs.__getitem__)
    if diffs[index] > tolerance:
        fail(f"output time {time_s:.17g} does not match a requested state")
    return index


def parse_dat_tokens(text: str) -> tuple[dict, dict, list[str]]:
    """Keep source lexemes for U/V residual and pairwise-print-rounding bounds."""
    field_records, energy_records, errors = {}, {}, []
    node_header = re.compile(
        r"\b(displacements|velocities|forces)\s*\([^)]*\)\s*for set\s+(\w+)\s+and time\s+(\S+)", re.I)
    energy_header = re.compile(
        r"total\s+(internal energy|kinetic energy|mass|volume)\s+for set\s+(\w+)\s+and time\s+(\S+)", re.I)
    kind_by_word = {"displacements": "U", "velocities": "V", "forces": "RF"}
    kind_by_energy = {"internal energy": "ELSE", "kinetic energy": "ELKE",
                      "mass": "EMAS", "volume": "EVOL"}
    active_field = None
    active_energy = None
    for line in text.splitlines():
        match = node_header.search(line)
        if match:
            word, set_name, raw_time = match.groups()
            try:
                kind, time_s = kind_by_word[word.lower()], finite_number(raw_time)
                key = (kind, set_name.upper(), time_s)
                if key in field_records:
                    errors.append(f"duplicate DAT {kind}/{set_name}/{raw_time} header")
                else:
                    field_records[key] = {"time": time_s, "tokens": {}}
                active_field, active_energy = key, None
            except Exception as exc:
                errors.append(f"malformed DAT nodal header: {exc}")
                active_field = None
            continue
        match = energy_header.search(line)
        if match:
            word, set_name, raw_time = match.groups()
            try:
                kind, time_s = kind_by_energy[word.lower()], finite_number(raw_time)
                key = (kind, set_name.upper(), time_s)
                if key in energy_records:
                    errors.append(f"duplicate DAT {kind}/{set_name}/{raw_time} header")
                else:
                    energy_records[key] = {"time": time_s, "token": None}
                active_energy, active_field = key, None
            except Exception as exc:
                errors.append(f"malformed DAT energy header: {exc}")
                active_energy = None
            continue
        words = line.split()
        if active_field is not None and len(words) == 4 and words[0].isdigit():
            node = int(words[0])
            try:
                for token in words[1:]:
                    decimal_number(token)
                values = words[1:]
                if node in field_records[active_field]["tokens"]:
                    errors.append(f"duplicate DAT node {node} for {active_field[:2]}")
                else:
                    field_records[active_field]["tokens"][node] = values
            except Exception as exc:
                errors.append(f"bad DAT node {node} token row: {exc}")
        elif active_energy is not None and energy_records[active_energy]["token"] is None and words:
            if len(words) == 1:
                try:
                    decimal_number(words[0])
                    energy_records[active_energy]["token"] = words[0]
                except Exception:
                    pass
    for key, item in energy_records.items():
        if item["token"] is None:
            errors.append(f"missing lexical DAT scalar for {key}")
    return field_records, energy_records, errors


def parse_frd_tokens(text: str) -> tuple[list[dict], list[str]]:
    records, errors = [], []
    identity, time_s, active = None, None, None
    for line in text.splitlines():
        words = line.split()
        if words and words[0] == "1PSTEP":
            try:
                identity = (int(words[3]), int(words[2])) if len(words) >= 4 else None
            except Exception:
                identity = None
                errors.append("malformed FRD 1PSTEP")
        elif words and words[0] == "100CL":
            try:
                time_s = finite_number(words[2])
            except Exception as exc:
                time_s = None
                errors.append(f"malformed FRD 100CL time: {exc}")
        elif line.startswith(" -4"):
            if active is not None:
                errors.append(f"unterminated FRD {active['kind']} field")
            active = {"kind": words[1] if len(words) >= 2 else "?",
                      "identity": identity, "time": time_s, "tokens": {}}
        elif active is not None and line.startswith(" -1"):
            try:
                node = int(line[3:13])
                raw = line.rstrip("\r\n")[13:]
                tokens = [raw[start:start + 12].strip() for start in range(0, len(raw), 12)
                          if raw[start:start + 12].strip()]
                for token in tokens:
                    decimal_number(token)
                if len(tokens) != 3:
                    errors.append(f"FRD {active['kind']} node {node} has {len(tokens)} components")
                if node in active["tokens"]:
                    errors.append(f"duplicate FRD node {node} in {active['kind']}")
                else:
                    active["tokens"][node] = tokens
            except Exception as exc:
                errors.append(f"malformed FRD node row: {exc}")
        elif active is not None and line.startswith(" -3"):
            records.append(active)
            active = None
    if active is not None:
        errors.append("truncated FRD data field")
    return records, errors


def reindex_dat(parsed_fields: list[dict], lexical_fields: dict,
                expected: dict, acceptance: dict, audit: Audit, case: str) -> tuple[dict, dict]:
    time_tol = acceptance["tolerances"]["time_s"]["absolute"]
    state_fields, token_fields = {}, {}
    for record in parsed_fields:
        kind, set_name = record["kind"], record["set"]
        try:
            i = state_index(record["time"], expected, time_tol)
        except Exception as exc:
            audit.problem("DAT_state_identity", f"{case}: {exc}")
            continue
        key = (kind, set_name, i)
        if key in state_fields:
            audit.problem("DAT_duplicate_field", f"{case}: duplicate field {key}")
            continue
        state_fields[key] = record
        lex_key = (kind, set_name, record["time"])
        lex = lexical_fields.get(lex_key)
        if lex is None:
            audit.problem("DAT_lexical_identity", f"{case}: missing lexical field {lex_key}")
        else:
            token_fields[key] = lex["tokens"]
    return state_fields, token_fields


def reindex_energies(parsed_energy: list[dict], lexical_energy: dict,
                     expected: dict, acceptance: dict, audit: Audit, case: str) -> tuple[dict, dict]:
    time_tol = acceptance["tolerances"]["time_s"]["absolute"]
    values, tokens = {}, {}
    for record in parsed_energy:
        try:
            i = state_index(record["time"], expected, time_tol)
        except Exception as exc:
            audit.problem("DAT_energy_state_identity", f"{case}: {exc}")
            continue
        key = (record["set"], record["kind"], i)
        if key in values:
            audit.problem("DAT_duplicate_energy", f"{case}: duplicate energy {key}")
            continue
        values[key] = record["value"]
        lex_key = (record["kind"], record["set"], record["time"])
        item = lexical_energy.get(lex_key)
        if item is None or item["token"] is None:
            audit.problem("DAT_energy_lexical_identity", f"{case}: missing lexical energy {lex_key}")
        else:
            tokens[key] = item["token"]
    return values, tokens


def reindex_frd(helper_blocks: list[dict], raw_records: list[dict],
                expected: dict, acceptance: dict, audit: Audit, case: str) -> tuple[dict, dict]:
    time_tol = acceptance["tolerances"]["time_s"]["absolute"]
    parsed = {(block["kind"], block["identity"], block["time"]): block for block in helper_blocks}
    raw = {(record["kind"], record["identity"], record["time"]): record for record in raw_records}
    if len(parsed) != len(helper_blocks) or len(raw) != len(raw_records):
        audit.problem("FRD_duplicate_field", f"{case}: duplicate FRD field identity")
    state_fields, token_fields = {}, {}
    for block in helper_blocks:
        try:
            i = state_index(block["time"], expected, time_tol)
        except Exception as exc:
            audit.problem("FRD_state_identity", f"{case}: {exc}")
            continue
        identity = block["identity"]
        if identity != (1, i + 1):
            audit.problem("FRD_increment_identity",
                          f"{case}: FRD identity {identity!r} does not match increment {i + 1}")
        key = (block["kind"], i)
        expected_labels = {
            "DISP": ["D1", "D2", "D3", "ALL"],
            "VELO": ["V1", "V2", "V3", "ALL"],
        }.get(block["kind"])
        if expected_labels is not None and block.get("labels") != expected_labels:
            audit.problem("FRD_component_labels",
                          f"{case} {block['kind']} labels {block.get('labels')!r} != {expected_labels!r}")
        if key in state_fields:
            audit.problem("FRD_duplicate_field", f"{case}: duplicate field {key}")
            continue
        state_fields[key] = block
        raw_key = (block["kind"], identity, block["time"])
        record = raw.get(raw_key)
        if record is None:
            audit.problem("FRD_lexical_identity", f"{case}: missing lexical record {raw_key}")
        else:
            token_fields[key] = record["tokens"]
    return state_fields, token_fields


def scalar_close(a: float, b: float, absolute: float, relative: float) -> bool:
    return math.isfinite(a) and math.isfinite(b) and abs(a - b) <= absolute + relative * abs(b)


def expected_vector(kind: str, node: int, xyz: tuple[float, float, float],
                    state: dict, pivot: tuple[float, float, float]) -> tuple[float, float, float]:
    theta = state["rotation_vector_y_rad"]
    omega = state["angular_velocity_y_rad_s"]
    direction = (xyz[2] - pivot[2], 0.0, -(xyz[0] - pivot[0]))
    scale = theta if kind == "U" else omega
    return tuple(scale * value for value in direction)


def skew(vector: tuple[float, float, float]) -> list[list[float]]:
    x, y, z = vector
    return [[0.0, -z, y], [z, 0.0, -x], [-y, x, 0.0]]


def matrix_multiply(a: list[list[float]], b: list[list[float]]) -> list[list[float]]:
    return [[math.fsum(a[i][k] * b[k][j] for k in range(len(b)))
             for j in range(len(b[0]))] for i in range(len(a))]


def matrix_add_scaled(a: list[list[float]], b: list[list[float]], scale: float) -> list[list[float]]:
    return [[a[i][j] + scale * b[i][j] for j in range(len(a[0]))]
            for i in range(len(a))]


def rotation_and_derivatives(w: tuple[float, float, float]) -> tuple[list[list[float]], list[list[list[float]]]]:
    """Rodrigues R(w) and dR/dw_j, stable at the tiny angles in this fixture."""
    theta2 = math.fsum(value * value for value in w)
    theta = math.sqrt(theta2)
    W = skew(w)
    W2 = matrix_multiply(W, W)
    identity = [[1.0 if i == j else 0.0 for j in range(3)] for i in range(3)]
    if theta < 1e-4:
        s = theta2
        A = 1 - s / 6 + s * s / 120 - s * s * s / 5040 + s**4 / 362880
        B = 0.5 - s / 24 + s * s / 720 - s * s * s / 40320 + s**4 / 3628800
        a_over_theta = -1 / 3 + s / 30 - s * s / 840 + s**3 / 45360
        b_over_theta = -1 / 12 + s / 180 - s * s / 6720 + s**3 / 453600
    else:
        A = math.sin(theta) / theta
        B = (1.0 - math.cos(theta)) / theta2
        a_over_theta = (theta * math.cos(theta) - math.sin(theta)) / (theta**3)
        b_over_theta = (theta * math.sin(theta) - 2.0 * (1.0 - math.cos(theta))) / (theta**4)
    rotation = matrix_add_scaled(matrix_add_scaled(identity, W, A), W2, B)
    derivatives = []
    for axis in range(3):
        unit = [0.0, 0.0, 0.0]
        unit[axis] = 1.0
        E = skew(tuple(unit))
        dR = [[A * E[i][j] + a_over_theta * w[axis] * W[i][j]
               + B * (matrix_multiply(E, W)[i][j] + matrix_multiply(W, E)[i][j])
               + b_over_theta * w[axis] * W2[i][j]
               for j in range(3)] for i in range(3)]
        derivatives.append(dR)
    return rotation, derivatives


def matvec(matrix: list[list[float]], vector: tuple[float, float, float]) -> tuple[float, float, float]:
    return tuple(math.fsum(matrix[i][j] * vector[j] for j in range(3)) for i in range(3))


def carrier_prediction(xyz: tuple[float, float, float], pivot: tuple[float, float, float],
                       ref_u: tuple[float, float, float], rot_u: tuple[float, float, float],
                       ref_v: tuple[float, float, float], rot_v: tuple[float, float, float]) -> tuple[tuple[float, ...], tuple[float, ...]]:
    relative = tuple(xyz[i] - pivot[i] for i in range(3))
    rotation, derivatives = rotation_and_derivatives(rot_u)
    rotated = matvec(rotation, relative)
    displacement = tuple(ref_u[i] + rotated[i] - relative[i] for i in range(3))
    velocity_rot = [matvec(derivatives[i], relative) for i in range(3)]
    velocity = tuple(ref_v[row] + math.fsum(velocity_rot[col][row] * rot_v[col]
                                            for col in range(3)) for row in range(3))
    return displacement, velocity


def parse_equation_cards(path: Path) -> list[list[dict]]:
    lines = path.read_text().splitlines()
    parsed = []
    index = 0
    while index < len(lines):
        if lines[index].strip().upper() != "*EQUATION":
            index += 1
            continue
        index += 1
        while index < len(lines) and (not lines[index].strip() or lines[index].lstrip().startswith("**")):
            index += 1
        if index >= len(lines):
            fail(f"truncated equation count in {path}")
        count = int(lines[index].strip())
        index += 1
        tokens = []
        while len(tokens) < 3 * count and index < len(lines):
            line = lines[index]
            if line.lstrip().startswith("*"):
                fail(f"truncated equation term list in {path}")
            tokens.extend(field.strip() for field in line.split(",") if field.strip())
            index += 1
        if len(tokens) != 3 * count:
            fail(f"equation term count mismatch in {path}")
        terms = []
        for term in range(count):
            node_token, dof_token, coefficient_token = tokens[3 * term:3 * term + 3]
            coefficient = decimal_number(coefficient_token)
            if len(coefficient_token) > 20:
                fail(f"equation coefficient exceeds source field width in {path}")
            terms.append({"node": int(node_token), "dof": int(dof_token),
                          "coefficient_token": coefficient_token,
                          "coefficient": coefficient})
        parsed.append(terms)
    return parsed


def equation_source(expected: dict) -> tuple[list[list[dict]], dict]:
    source = HERE.parent / expected["source_files"]["nut-coupling.inp"]["path"]
    data = strict_json(HERE.parent / expected["source_files"]["nut-coupling.json"]["path"])
    nut = data["per_nut"][0]
    fit = nut["least_squares_rigid_motion_fit"]
    nodes = list(map(int, fit["node_ids"]))
    coefficients = fit["fit_coefficients_u0_then_theta"]
    if len(coefficients) != 6 or any(len(row) != 3 * len(nodes) for row in coefficients):
        fail("pinned weighted-fit matrix does not have six rows over all fit nodes")
    if len(set(nodes)) != len(nodes):
        fail("pinned weighted-fit node list contains duplicates")
    return parse_equation_cards(source)[:6], {"fit_nodes": nodes, "fit_coefficients": coefficients}


def equation_rounding_allowance(terms: list[dict], tokens_by_node: dict,
                                acceptance: dict) -> tuple[Decimal, Decimal]:
    """Return lexical-output uncertainty plus coefficient-read/dot arithmetic bounds."""
    active = []
    for term in terms:
        coefficient = term["coefficient"]
        if coefficient == 0:
            continue
        token = tokens_by_node[term["node"]][term["dof"] - 1]
        value = decimal_number(token)
        active.append((coefficient, float(coefficient), token, value))
    n = len(active)
    if n == 0:
        return Decimal(0), Decimal(0)
    allowance_spec = acceptance["equation_arithmetic_allowance"]
    unit_roundoff = float(allowance_spec["unit_roundoff"])
    product_sum_roundoff = (2.0 * n * unit_roundoff) / (1.0 - 2.0 * n * unit_roundoff)
    lexical = Decimal(0)
    coefficient_parse = Decimal(0)
    magnitude_sum = Decimal(0)
    with localcontext() as ctx:
        ctx.prec = ARITHMETIC_DECIMAL_PRECISION
        for coefficient_decimal, coefficient_float, token, value in active:
            lexical += abs(coefficient_decimal) * decimal_half_ulp(token)
            if coefficient_float != 0.0:
                coeff_rounding = Decimal.from_float(math.ulp(coefficient_float) / 2.0)
                coefficient_parse += coeff_rounding * abs(value)
            magnitude_sum += abs(Decimal.from_float(coefficient_float) * value)
        arithmetic = coefficient_parse + Decimal.from_float(product_sum_roundoff) * magnitude_sum
        arithmetic += ARITHMETIC_DECIMAL_FLOOR * max(Decimal(1), magnitude_sum)
    return lexical, arithmetic


def verify_equation_residuals(case: str, state_fields: dict, token_fields: dict,
                              equation_cards: list[list[dict]], expected: dict,
                              acceptance: dict, audit: Audit) -> None:
    if case == "direct":
        return
    for index, terms in enumerate(equation_cards):
        if len(terms) != expected["pivot_and_current_map"]["equation_term_counts"][index]:
            audit.problem("equation_source_shape", f"{case}: equation {index + 1} term count differs")
    for state_index_value in range(len(expected["linearized_discrete_reference"]["states"])):
        key = ("U", "N_OBSERVE", state_index_value)
        vectors = state_fields.get(key, {}).get("nodes", {})
        lexical_vectors = token_fields.get(key, {})
        for equation_index, terms in enumerate(equation_cards, 1):
            missing = next((term["node"] for term in terms
                            if term["node"] not in vectors or term["node"] not in lexical_vectors), None)
            if missing is not None:
                audit.problem("equation_residual_coverage",
                              f"{case} increment {state_index_value + 1} equation {equation_index}: missing node {missing}")
                continue
            with localcontext() as ctx:
                ctx.prec = ARITHMETIC_DECIMAL_PRECISION
                residual = Decimal(0)
                for term in terms:
                    token = lexical_vectors[term["node"]][term["dof"] - 1]
                    residual += term["coefficient"] * decimal_number(token)
                lexical_bound, arithmetic_bound = equation_rounding_allowance(
                    terms, lexical_vectors, acceptance)
                allowed = lexical_bound + arithmetic_bound
            error = abs(residual)
            category = "equation_residual"
            metric = audit.metrics[category]
            metric["samples"] += 1
            err, lim = float(error), float(allowed)
            metric["max_absolute_error"] = max(metric["max_absolute_error"], err)
            metric["max_allowed_error"] = max(metric["max_allowed_error"], lim)
            ratio = err / lim if lim > 0 else (0.0 if err == 0 else math.inf)
            metric["max_error_to_allowance"] = max(metric["max_error_to_allowance"], ratio)
            if error > allowed:
                metric["failures"] += 1
                audit.problem(category,
                              f"{case} increment {state_index_value + 1} equation {equation_index}: "
                              f"abs(residual)={err:.6g}, lexical={float(lexical_bound):.6g}, "
                              f"arithmetic={float(arithmetic_bound):.6g}")


def parse_capture(case: str, folder: Path, expected: dict, acceptance: dict,
                  parser: object, audit: Audit) -> dict:
    dat_path, frd_path = folder / "coupon.dat", folder / "coupon.frd"
    sta_path = folder / "coupon.sta"
    if not dat_path.is_file() or not frd_path.is_file() or not sta_path.is_file():
        fail(f"{case}: STA/DAT/FRD capture is incomplete")
    sta_rows = parse_sta(sta_path.read_text(errors="strict"), expected, acceptance)
    dat_text, frd_text = dat_path.read_text(errors="strict"), frd_path.read_text(errors="strict")
    dat_fields, dat_energy, dat_errors = parser.parse_dat(dat_text)
    dat_lex_fields, dat_lex_energy, lexical_errors = parse_dat_tokens(dat_text)
    frd_blocks, frd_errors = parser.parse_frd(frd_text)
    frd_lex_records, frd_lex_errors = parse_frd_tokens(frd_text)
    for error in dat_errors + lexical_errors:
        audit.problem("DAT_parse", f"{case}: {error}")
    for error in frd_errors + frd_lex_errors:
        audit.problem("FRD_parse", f"{case}: {error}")
    dat_state, dat_tokens = reindex_dat(dat_fields, dat_lex_fields, expected, acceptance, audit, case)
    energy_values, energy_tokens = reindex_energies(dat_energy, dat_lex_energy,
                                                    expected, acceptance, audit, case)
    frd_state, frd_tokens = reindex_frd(frd_blocks, frd_lex_records,
                                        expected, acceptance, audit, case)
    states = expected["linearized_discrete_reference"]["states"]
    time_tolerance = acceptance["tolerances"]["time_s"]["absolute"]
    for (kind, set_name, i), record in dat_state.items():
        if abs(record["time"] - sta_rows[i]["total_time"]) > time_tolerance:
            audit.problem("DAT_STA_time_identity",
                          f"{case} {kind}/{set_name} time {record['time']:.17g} differs from accepted STA increment {i + 1}")
    for (kind, i), record in frd_state.items():
        if abs(record["time"] - sta_rows[i]["total_time"]) > time_tolerance:
            audit.problem("FRD_STA_time_identity",
                          f"{case} {kind} time {record['time']:.17g} differs from accepted STA increment {i + 1}")
    dat_expected_ids = expected_node_sets(expected, case, "DAT")
    frd_expected_ids = expected_node_sets(expected, case, "FRD")
    for i in range(len(states)):
        for kind in ("U", "V"):
            key = (kind, "N_OBSERVE", i)
            record, tokens = dat_state.get(key), dat_tokens.get(key)
            if record is None or tokens is None:
                audit.problem("DAT_required_field", f"{case} increment {i + 1}: missing {kind}/N_OBSERVE")
                continue
            actual_ids = set(record["nodes"])
            if actual_ids != dat_expected_ids:
                missing = sorted(dat_expected_ids - actual_ids)
                extra = sorted(actual_ids - dat_expected_ids)
                audit.problem("DAT_node_coverage",
                              f"{case} increment {i + 1} {kind}: missing={len(missing)} {missing[:3]}, "
                              f"extra={len(extra)} {extra[:3]}")
            token_ids = set(tokens)
            if token_ids != actual_ids:
                audit.problem("DAT_token_coverage", f"{case} increment {i + 1} {kind}: parsed/lexical rows differ")
        for kind in ("DISP", "VELO"):
            key = (kind, i)
            block, tokens = frd_state.get(key), frd_tokens.get(key)
            if block is None or tokens is None:
                audit.problem("FRD_required_field", f"{case} increment {i + 1}: missing {kind}")
                continue
            actual_ids = set(block["nodes"])
            if actual_ids != frd_expected_ids:
                missing = sorted(frd_expected_ids - actual_ids)
                extra = sorted(actual_ids - frd_expected_ids)
                audit.problem("FRD_node_coverage",
                              f"{case} increment {i + 1} {kind}: missing={len(missing)} {missing[:3]}, "
                              f"extra={len(extra)} {extra[:3]}")
            if set(tokens) != actual_ids:
                audit.problem("FRD_token_coverage", f"{case} increment {i + 1} {kind}: parsed/lexical rows differ")

    # Reject unrequested extra state/field blocks instead of silently ignoring them.
    required_dat_keys = {(kind, "N_OBSERVE", i) for kind in ("U", "V") for i in range(len(states))}
    required_frd_keys = {(kind, i) for kind in ("DISP", "VELO") for i in range(len(states))}
    if set(dat_state) != required_dat_keys:
        audit.problem("DAT_field_inventory",
                      f"{case}: DAT fields expected {len(required_dat_keys)}, observed {len(dat_state)}")
    if set(frd_state) != required_frd_keys:
        audit.problem("FRD_field_inventory",
                      f"{case}: FRD fields expected {len(required_frd_keys)}, observed {len(frd_state)}")

    expected_energy_sets = expected["output_contract"]["EL_PRINT_by_case"][case]
    required_energy_keys = {(set_name.upper(), kind, i)
                            for set_name, kinds in expected_energy_sets.items()
                            for kind in kinds for i in range(len(states))}
    if set(energy_values) != required_energy_keys:
        missing = sorted(required_energy_keys - set(energy_values))[:5]
        extra = sorted(set(energy_values) - required_energy_keys)[:5]
        audit.problem("DAT_energy_coverage",
                      f"{case}: missing={len(required_energy_keys - set(energy_values))} {missing}, "
                      f"extra={len(set(energy_values) - required_energy_keys)} {extra}")
    dat_complete = sum(1 for i in range(len(states))
                       if all((kind, "N_OBSERVE", i) in dat_state and
                              set(dat_state[(kind, "N_OBSERVE", i)]["nodes"]) == dat_expected_ids
                              for kind in ("U", "V")))
    frd_complete = sum(1 for i in range(len(states))
                       if all((kind, i) in frd_state and
                              set(frd_state[(kind, i)]["nodes"]) == frd_expected_ids
                              for kind in ("DISP", "VELO")))
    return {"sta": sta_rows, "complete_dat_state_count": dat_complete,
            "complete_frd_state_count": frd_complete,
            "dat": dat_state, "dat_tokens": dat_tokens,
            "energy": energy_values, "energy_tokens": energy_tokens,
            "frd": frd_state, "frd_tokens": frd_tokens,
            "dat_expected_ids": dat_expected_ids, "frd_expected_ids": frd_expected_ids}


def check_node_vector(audit: Audit, metric: str, category: str, actual: list[float],
                      reference: tuple[float, float, float], tolerance: dict, where: str) -> None:
    if len(actual) != 3:
        audit.problem(category, f"{where}: expected three components, found {len(actual)}")
        return
    for axis in range(3):
        audit.scalar(metric, category, actual[axis], reference[axis],
                     tolerance["absolute"], tolerance.get("relative", 0.0),
                     f"{where} component {axis + 1}")


def fit_controls(fit: dict, physical_vectors: dict[int, list[float]]) -> list[float]:
    flat = []
    for node in fit["fit_nodes"]:
        vector = physical_vectors.get(node)
        if vector is None or len(vector) != 3:
            fail(f"weighted-fit node {node} is missing from physical output")
        flat.extend(vector)
    return [math.fsum(float(coef) * value for coef, value in zip(row, flat))
            for row in fit["fit_coefficients"]]


def measured_fit_allowance(coefficients: list[float], physical_tokens: list[str],
                           controller_token: str, fitted_value: float,
                           channel_tolerance: dict, acceptance: dict) -> float:
    """Fit tolerance plus both record quantizers and explicit dot-product arithmetic."""
    if len(coefficients) != len(physical_tokens):
        fail("weighted-fit coefficient and printed-value lengths differ")
    active = []
    for coefficient, token in zip(coefficients, physical_tokens):
        coefficient = float(coefficient)
        value = decimal_number(token)
        if coefficient != 0.0:
            active.append((coefficient, token, value))
    spec = acceptance["equation_arithmetic_allowance"]
    unit = float(spec["unit_roundoff"])
    n = len(active)
    gamma = (2.0 * n * unit) / (1.0 - 2.0 * n * unit) if n else 0.0
    print_bound = decimal_half_ulp(controller_token)
    coefficient_bound = Decimal(0)
    magnitude_sum = Decimal(0)
    with localcontext() as ctx:
        ctx.prec = ARITHMETIC_DECIMAL_PRECISION
        for coefficient, token, value in active:
            binary_coefficient = Decimal.from_float(coefficient)
            print_bound += abs(binary_coefficient) * decimal_half_ulp(token)
            coefficient_bound += Decimal.from_float(math.ulp(coefficient) / 2.0) * abs(value)
            magnitude_sum += abs(binary_coefficient * value)
        arithmetic = coefficient_bound + Decimal.from_float(gamma) * magnitude_sum
        arithmetic += ARITHMETIC_DECIMAL_FLOOR * max(Decimal(1), magnitude_sum)
    base = channel_tolerance["absolute"] + channel_tolerance.get("relative", 0.0) * abs(fitted_value)
    return base + float(print_bound + arithmetic)


def verify_case_numerics(case: str, result: dict, coordinates: dict[int, tuple[float, float, float]],
                         fit: dict, equation_cards: list[list[dict]], expected: dict,
                         acceptance: dict, audit: Audit) -> None:
    states = expected["linearized_discrete_reference"]["states"]
    groups = expected["output_contract"]["node_id_sets"]
    physical_ids = set(map(int, groups["physical_body"]["node_ids"]))
    control_ids = list(map(int, groups["mapping_controls"]["node_ids"]))
    carrier_ids = set(map(int, groups["zero_density_carrier"]["node_ids"]))
    pivot = tuple(map(float, expected["pivot_and_current_map"]["pivot_xyz_mm"]))
    tolerance = acceptance["tolerances"]
    body = expected["physical_body_reference"]
    carrier = expected["zero_density_carrier_reference"]
    body_set = body["body_id"].upper()
    carrier_set = carrier["body_id"].upper()
    if case != "direct":
        verify_equation_residuals(case, result["dat"], result["dat_tokens"],
                                  equation_cards, expected, acceptance, audit)

    for state_index_value, state in enumerate(states):
        for kind, channel, field_key, frd_kind, frd_channel in (
            ("U", "DAT_U_mm", "U", "DISP", "FRD_U_mm"),
            ("V", "DAT_V_mm_s", "V", "VELO", "FRD_V_mm_s"),
        ):
            dat_key = (field_key, "N_OBSERVE", state_index_value)
            record = result["dat"].get(dat_key)
            if record is not None:
                for node in sorted(physical_ids & set(record["nodes"])):
                    ref = expected_vector(kind, node, coordinates[node], state, pivot)
                    check_node_vector(audit, f"{case}_{channel}", f"{case}_{channel}_oracle",
                                      record["nodes"][node], ref, tolerance[channel],
                                      f"{case} increment {state_index_value + 1} node {node}")
            frd_record = result["frd"].get((frd_kind, state_index_value))
            if frd_record is not None:
                for node in sorted(physical_ids & set(frd_record["nodes"])):
                    ref = expected_vector(kind, node, coordinates[node], state, pivot)
                    check_node_vector(audit, f"{case}_{frd_channel}", f"{case}_{frd_channel}_oracle",
                                      frd_record["nodes"][node], ref, tolerance[frd_channel],
                                      f"{case} increment {state_index_value + 1} node {node}")

        if case != "direct":
            u_record = result["dat"].get(("U", "N_OBSERVE", state_index_value))
            v_record = result["dat"].get(("V", "N_OBSERVE", state_index_value))
            u_tokens = result["dat_tokens"].get(("U", "N_OBSERVE", state_index_value), {})
            v_tokens = result["dat_tokens"].get(("V", "N_OBSERVE", state_index_value), {})
            if u_record is not None and v_record is not None:
                ref_id, rot_id = control_ids
                actual_u = list(u_record["nodes"].get(ref_id, [])) + list(u_record["nodes"].get(rot_id, []))
                actual_v = list(v_record["nodes"].get(ref_id, [])) + list(v_record["nodes"].get(rot_id, []))
                actual_u_tokens = list(u_tokens.get(ref_id, [])) + list(u_tokens.get(rot_id, []))
                actual_v_tokens = list(v_tokens.get(ref_id, [])) + list(v_tokens.get(rot_id, []))
                fit_available = all(
                    node in u_record["nodes"] and node in v_record["nodes"] and
                    node in u_tokens and node in v_tokens
                    for node in fit["fit_nodes"])
                fit_u = fit_controls(fit, u_record["nodes"]) if fit_available else None
                fit_v = fit_controls(fit, v_record["nodes"]) if fit_available else None
                if not fit_available:
                    audit.problem("controller_fit_coverage",
                                  f"{case} increment {state_index_value + 1}: weighted-fit physical nodes/tokens missing")
                if (len(actual_u) != 6 or len(actual_v) != 6 or
                        len(actual_u_tokens) != 6 or len(actual_v_tokens) != 6):
                    audit.problem("controller_coverage",
                                  f"{case} increment {state_index_value + 1}: controller vector missing")
                else:
                    for component in range(6):
                        u_tol = tolerance["REF_U_mm"] if component < 3 else tolerance["ROT_U_rad"]
                        v_tol = tolerance["REF_V_mm_s"] if component < 3 else tolerance["ROT_V_rad_s"]
                        if fit_available:
                            fit_u_tokens = [u_tokens[node][axis] for node in fit["fit_nodes"] for axis in range(3)]
                            fit_v_tokens = [v_tokens[node][axis] for node in fit["fit_nodes"] for axis in range(3)]
                            allowed_fit_u = measured_fit_allowance(
                                fit["fit_coefficients"][component], fit_u_tokens,
                                actual_u_tokens[component], fit_u[component], u_tol, acceptance)
                            allowed_fit_v = measured_fit_allowance(
                                fit["fit_coefficients"][component], fit_v_tokens,
                                actual_v_tokens[component], fit_v[component], v_tol, acceptance)
                            audit.scalar(f"{case}_controller_fit_U", "controller_fit_U",
                                         actual_u[component], fit_u[component], allowed_fit_u, 0.0,
                                         f"{case} increment {state_index_value + 1} control {component}")
                            audit.scalar(f"{case}_controller_fit_V", "controller_fit_V",
                                         actual_v[component], fit_v[component], allowed_fit_v, 0.0,
                                         f"{case} increment {state_index_value + 1} control {component}")
                        target_u = 0.0 if component != 4 else state["rotation_vector_y_rad"]
                        target_v = 0.0 if component != 4 else state["angular_velocity_y_rad_s"]
                        audit.scalar(f"{case}_controller_oracle_U", "controller_oracle_U",
                                     actual_u[component], target_u, u_tol["absolute"],
                                     u_tol.get("relative", 0.0),
                                     f"{case} increment {state_index_value + 1} control {component}")
                        audit.scalar(f"{case}_controller_oracle_V", "controller_oracle_V",
                                     actual_v[component], target_v, v_tol["absolute"],
                                     v_tol.get("relative", 0.0),
                                     f"{case} increment {state_index_value + 1} control {component}")

        # Total EL PRINT channels are checked for every requested state.
        for set_name, reference in ((body_set, body),):
            ref_elke = state["linearized_ELKE_Nmm"]
            for kind, ref_value, tol_name in (
                ("ELKE", ref_elke, "ELKE_Nmm"),
                ("EMAS", reference["mass_tonne"], "EMAS_tonne"),
                ("EVOL", reference["volume_mm3"], "EVOL_mm3"),
            ):
                key = (set_name, kind, state_index_value)
                if key not in result["energy"]:
                    continue
                tol = tolerance[tol_name]
                audit.scalar(f"{case}_{set_name}_{kind}", "energy_oracle",
                             result["energy"][key], ref_value, tol["absolute"],
                             tol.get("relative", 0.0),
                             f"{case} increment {state_index_value + 1} {set_name} {kind}")
            key = (set_name, "ELSE", state_index_value)
            if key in result["energy"]:
                tol = tolerance["ELSE_Nmm"]
                allowed = tol["absolute"] + tol["relative_to_positive_body_reference_ELKE"] * ref_elke
                audit.upper(f"{case}_{set_name}_ELSE", "energy_oracle",
                            result["energy"][key], allowed,
                            f"{case} increment {state_index_value + 1} {set_name} ELSE")

        if case == "mapped_carrier":
            for kind, tol_name in (("ELKE", "ELKE_Nmm"), ("EMAS", "EMAS_tonne")):
                key = (carrier_set, kind, state_index_value)
                if key in result["energy"]:
                    tol = tolerance[tol_name]
                    audit.scalar(f"{case}_{carrier_set}_{kind}", "carrier_energy_oracle",
                                 result["energy"][key], 0.0, tol["absolute"], 0.0,
                                 f"{case} increment {state_index_value + 1} {carrier_set} {kind}")
            key = (carrier_set, "ELSE", state_index_value)
            if key in result["energy"]:
                tol = tolerance["ELSE_Nmm"]
                allowed = tol["absolute"] + tol["relative_to_positive_body_reference_ELKE"] * state["linearized_ELKE_Nmm"]
                audit.upper(f"{case}_{carrier_set}_ELSE", "carrier_energy_oracle",
                            result["energy"][key], allowed,
                            f"{case} increment {state_index_value + 1} {carrier_set} ELSE")
            key = (carrier_set, "EVOL", state_index_value)
            if key in result["energy"]:
                tol = tolerance["EVOL_mm3"]
                audit.scalar(f"{case}_{carrier_set}_EVOL", "carrier_energy_oracle",
                             result["energy"][key], carrier["volume_mm3"], tol["absolute"],
                             tol["relative"],
                             f"{case} increment {state_index_value + 1} {carrier_set} EVOL")

            u_record = result["dat"].get(("U", "N_OBSERVE", state_index_value))
            v_record = result["dat"].get(("V", "N_OBSERVE", state_index_value))
            if u_record is not None and v_record is not None:
                ref_id, rot_id = control_ids
                ref_u = tuple(u_record["nodes"].get(ref_id, [math.nan] * 3))
                rot_u = tuple(u_record["nodes"].get(rot_id, [math.nan] * 3))
                ref_v = tuple(v_record["nodes"].get(ref_id, [math.nan] * 3))
                rot_v = tuple(v_record["nodes"].get(rot_id, [math.nan] * 3))
                for kind, record, channel in (("U", u_record, "DAT_U_mm"), ("V", v_record, "DAT_V_mm_s")):
                    for node in sorted(carrier_ids & set(record["nodes"])):
                        pred_u, pred_v = carrier_prediction(coordinates[node], pivot,
                                                            ref_u, rot_u, ref_v, rot_v)
                        predicted = pred_u if kind == "U" else pred_v
                        check_node_vector(audit, f"carrier_{kind}_kinematics_DAT",
                                          "carrier_kinematics_DAT", record["nodes"][node], predicted,
                                          tolerance[channel],
                                          f"mapped_carrier increment {state_index_value + 1} node {node}")
                for frd_kind, kind, channel in (("DISP", "U", "FRD_U_mm"),
                                                ("VELO", "V", "FRD_V_mm_s")):
                    record = result["frd"].get((frd_kind, state_index_value))
                    if record is None:
                        continue
                    for node in sorted(carrier_ids & set(record["nodes"])):
                        pred_u, pred_v = carrier_prediction(coordinates[node], pivot,
                                                            ref_u, rot_u, ref_v, rot_v)
                        predicted = pred_u if kind == "U" else pred_v
                        check_node_vector(audit, f"carrier_{kind}_kinematics_FRD",
                                          "carrier_kinematics_FRD", record["nodes"][node], predicted,
                                          tolerance[channel],
                                          f"mapped_carrier increment {state_index_value + 1} node {node}")


def cross_field_parity(left_case: str, right_case: str, field_name: str,
                       left_result: dict, right_result: dict, node_ids: set[int],
                       expected: dict, acceptance: dict, audit: Audit,
                       *, frd: bool = False) -> None:
    tolerance = acceptance["tolerances"][field_name]
    parity = acceptance["cross_case_field_parity"]
    relative = parity["relative"]
    multiplier = parity["absolute_floor_multiplier"]
    kind = "DISP" if field_name.endswith("U_mm") else "VELO"
    dat_kind = "U" if kind == "DISP" else "V"
    for i in range(len(expected["linearized_discrete_reference"]["states"])):
        if frd:
            a = left_result["frd"].get((kind, i))
            b = right_result["frd"].get((kind, i))
            at = left_result["frd_tokens"].get((kind, i), {})
            bt = right_result["frd_tokens"].get((kind, i), {})
        else:
            a = left_result["dat"].get((dat_kind, "N_OBSERVE", i))
            b = right_result["dat"].get((dat_kind, "N_OBSERVE", i))
            at = left_result["dat_tokens"].get((dat_kind, "N_OBSERVE", i), {})
            bt = right_result["dat_tokens"].get((dat_kind, "N_OBSERVE", i), {})
        if a is None or b is None:
            audit.problem("cross_case_field_coverage", f"{left_case}/{right_case} missing {field_name} increment {i + 1}")
            continue
        for node in sorted(node_ids):
            av, bv = a["nodes"].get(node), b["nodes"].get(node)
            atok, btok = at.get(node), bt.get(node)
            if av is None or bv is None or atok is None or btok is None:
                audit.problem("cross_case_field_coverage",
                              f"{left_case}/{right_case} missing node {node} {field_name} increment {i + 1}")
                continue
            for axis in range(3):
                a_value, b_value = av[axis], bv[axis]
                allowed = (multiplier * tolerance["absolute"]
                           + relative * max(abs(a_value), abs(b_value))
                           + float(decimal_half_ulp(atok[axis]))
                           + float(decimal_half_ulp(btok[axis])))
                audit.scalar(f"parity_{left_case}_{right_case}_{field_name}",
                             "cross_case_field_parity", a_value, b_value, allowed, 0.0,
                             f"increment {i + 1} node {node} component {axis + 1}")


def cross_case_controls(left_case: str, right_case: str, left_result: dict,
                        right_result: dict, expected: dict, acceptance: dict,
                        audit: Audit) -> None:
    controls = set(map(int, expected["output_contract"]["node_id_sets"]["mapping_controls"]["node_ids"]))
    ref_id, rot_id = map(int, expected["pivot_and_current_map"]["control_node_ids"])
    for kind, channel in (("U", "DAT_U_mm"), ("V", "DAT_V_mm_s")):
        parity = acceptance["cross_case_field_parity"]
        for i in range(len(expected["linearized_discrete_reference"]["states"])):
            key = (kind, "N_OBSERVE", i)
            a, b = left_result["dat"].get(key), right_result["dat"].get(key)
            at, bt = left_result["dat_tokens"].get(key, {}), right_result["dat_tokens"].get(key, {})
            if a is None or b is None:
                audit.problem("cross_case_control_coverage", f"missing {kind} controls at increment {i + 1}")
                continue
            for node in sorted(controls):
                if node not in a["nodes"] or node not in b["nodes"] or node not in at or node not in bt:
                    audit.problem("cross_case_control_coverage", f"missing controller node {node} increment {i + 1}")
                    continue
                if node == ref_id:
                    tol_name = "REF_U_mm" if kind == "U" else "REF_V_mm_s"
                elif node == rot_id:
                    tol_name = "ROT_U_rad" if kind == "U" else "ROT_V_rad_s"
                else:
                    audit.problem("cross_case_control_identity", f"unexpected controller id {node}")
                    continue
                tol = acceptance["tolerances"][tol_name]
                for axis in range(3):
                    av, bv = a["nodes"][node][axis], b["nodes"][node][axis]
                    allowed = (parity["absolute_floor_multiplier"] * tol["absolute"]
                               + parity["relative"] * max(abs(av), abs(bv))
                               + float(decimal_half_ulp(at[node][axis]))
                               + float(decimal_half_ulp(bt[node][axis])))
                    audit.scalar(f"parity_{left_case}_{right_case}_controller_{kind}",
                                 "cross_case_control_parity", av, bv, allowed, 0.0,
                                 f"increment {i + 1} node {node} component {axis + 1}")


def cross_energy_parity(left_case: str, right_case: str, left_result: dict,
                        right_result: dict, expected: dict, acceptance: dict,
                        audit: Audit) -> None:
    body_set = expected["physical_body_reference"]["body_id"].upper()
    for i, state in enumerate(expected["linearized_discrete_reference"]["states"]):
        for kind in ("ELSE", "ELKE", "EMAS", "EVOL"):
            key = (body_set, kind, i)
            if key not in left_result["energy"] or key not in right_result["energy"]:
                audit.problem("cross_case_energy_coverage", f"missing {kind} energy at increment {i + 1}")
                continue
            left, right = left_result["energy"][key], right_result["energy"][key]
            if kind == "ELSE":
                t = acceptance["tolerances"]["ELSE_Nmm"]
                allowed = t["absolute"] + t["relative_to_positive_body_reference_ELKE"] * state["linearized_ELKE_Nmm"]
            else:
                t = acceptance["tolerances"][{"ELKE": "ELKE_Nmm", "EMAS": "EMAS_tonne", "EVOL": "EVOL_mm3"}[kind]]
                allowed = t["absolute"] + t.get("relative", 0.0) * max(abs(left), abs(right))
            token_a = left_result["energy_tokens"].get(key)
            token_b = right_result["energy_tokens"].get(key)
            if token_a is None or token_b is None:
                audit.problem("cross_case_energy_coverage", f"missing lexical {kind} energy at increment {i + 1}")
                continue
            allowed += float(decimal_half_ulp(token_a) + decimal_half_ulp(token_b))
            audit.scalar(f"parity_{left_case}_{right_case}_{kind}", "cross_case_energy_parity",
                         left, right, allowed, 0.0, f"increment {i + 1} {kind}")


def read_static_files_from_runner() -> tuple[str, ...]:
    tree = ast.parse((HERE / "run.py").read_text())
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == "STATIC_FILES"
                                                for t in node.targets):
            value = ast.literal_eval(node.value)
            return tuple(value)
    fail("could not read STATIC_FILES from frozen run.py")


def read_runner_build_pins() -> dict:
    tree = ast.parse((HERE / "run.py").read_text())
    values = {}
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id in {"IMAGE", "BINARY", "BINARY_SHA"}:
                    values[target.id] = ast.literal_eval(node.value)
    if set(values) != {"IMAGE", "BINARY", "BINARY_SHA"}:
        fail("could not read image/binary pins from frozen run.py")
    return {"image_id": values["IMAGE"], "binary_path": values["BINARY"],
            "binary_sha256": values["BINARY_SHA"]}


def parse_sta(text: str, expected: dict, acceptance: dict) -> list[dict]:
    """Require the one-step fixed-dt accepted schedule recorded by CalculiX."""
    rows = []
    time_tolerance = acceptance["tolerances"]["time_s"]["absolute"]
    expected_states = expected["linearized_discrete_reference"]["states"]
    dt = expected["procedure"]["dt_s"]
    saw_header = False
    for line in text.splitlines():
        words = line.split()
        if words[:2] == ["STEP", "INC"]:
            saw_header = True
            continue
        if not words or not re.match(r"^[+-]?(?:\d|\.\d)", words[0]):
            continue
        if len(words) != 7:
            fail(f"malformed numeric STA table row: expected 7 columns, found {len(words)}")
        try:
            step, increment, attempt, iterations = map(int, words[:4])
            total_time, step_time, increment_time = map(finite_number, words[4:])
        except Exception as exc:
            fail(f"malformed STA accepted-state row: {exc}")
        rows.append({"step": step, "increment": increment, "attempt": attempt,
                     "iterations": iterations, "total_time": total_time,
                     "step_time": step_time, "increment_time": increment_time})
    if not saw_header:
        fail("coupon.sta lacks the standard accepted-increment table header")
    if len(rows) != len(expected_states):
        fail(f"coupon.sta accepted-state count {len(rows)} != {len(expected_states)}")
    seen = set()
    for index, row in enumerate(rows):
        state = expected_states[index]
        if (row["step"], row["increment"]) != (1, index + 1) or (row["step"], row["increment"]) in seen:
            fail(f"coupon.sta has duplicate/unexpected accepted identity at row {index + 1}")
        seen.add((row["step"], row["increment"]))
        if row["attempt"] != 1 or row["iterations"] < 1:
            fail(f"coupon.sta has retry or invalid iteration count at increment {index + 1}")
        if abs(row["total_time"] - state["time_s"]) > time_tolerance:
            fail(f"coupon.sta total time differs at increment {index + 1}")
        if abs(row["step_time"] - state["time_s"]) > time_tolerance:
            fail(f"coupon.sta step time differs at increment {index + 1}")
        if abs(row["increment_time"] - dt) > time_tolerance:
            fail(f"coupon.sta increment time differs at increment {index + 1}")
    return rows


def parse_utc(value: str, where: str) -> datetime:
    try:
        result = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except Exception as exc:
        raise ValueError(f"invalid UTC timestamp {where}: {value!r}") from exc
    if result.tzinfo is None:
        fail(f"timestamp lacks timezone: {where}")
    return result.astimezone(timezone.utc)


def verify_freeze_and_execution(audit_dir: Path, expected: dict, acceptance: dict) -> dict:
    if not FREEZE.is_file():
        fail("input-freeze.json is missing")
    if not (audit_dir / "execution.json").is_file():
        fail("output execution.json is missing")
    freeze_hash = sha(FREEZE)
    frozen = strict_json(FREEZE)
    execution_path = audit_dir / "execution.json"
    execution_hash = sha(execution_path)
    execution = strict_json(execution_path)
    expected_hash = sha(HERE / "expected.json")
    if frozen.get("schema") != FREEZE_SCHEMA:
        fail("unexpected freeze schema")
    if frozen.get("expected_sha256") != expected_hash:
        fail("freeze does not bind current expected.json")
    if frozen.get("case_order") != list(CASES) or execution.get("case_order") != list(CASES):
        fail("freeze/execution case order differs")
    if frozen.get("native_execution") is not False or frozen.get("mechanical_acceptance") is not False or frozen.get("joint_acceptance") is not False:
        fail("freeze scope flags are not false")
    if acceptance.get("ready_for_native") is not True:
        fail("frozen capture exists but acceptance readiness is not true")

    static_names = read_static_files_from_runner()
    if not REQUIRED_STATIC_FILES <= set(static_names):
        fail(f"run.py static inventory omits verifier requirements: {sorted(REQUIRED_STATIC_FILES - set(static_names))}")
    actual_local = {name: sha(HERE / name) for name in sorted(static_names)}
    if frozen.get("files_sha256") != actual_local:
        fail("frozen local files differ from current packet files")
    external = frozen.get("external_dependencies_sha256")
    if not isinstance(external, dict) or not external:
        fail("freeze external dependency inventory is missing")
    for rel, digest in external.items():
        path = ROOT / rel
        if not path.is_file() or sha(path) != digest:
            fail(f"frozen external dependency changed or missing: {rel}")
    expected_input_hashes = {case: expected["inputs"][case]["sha256"] for case in CASES}
    if frozen.get("input_sha256") != expected_input_hashes:
        fail("freeze input hashes differ from expected.json")
    if execution.get("schema") != EXECUTION_SCHEMA:
        fail("unexpected execution schema")
    if execution.get("freeze_sha256") != freeze_hash or execution.get("expected_sha256") != expected_hash:
        fail("execution record does not bind the frozen packet")
    if execution.get("input_sha256") != expected_input_hashes:
        fail("execution input hashes differ")
    if execution.get("serialized") is not True or execution.get("native_execution") is not True:
        fail("execution record does not establish serialized native capture")
    if execution.get("status") != "CAPTURES_COMPLETE_PENDING_VERIFICATION":
        fail(f"execution is incomplete or failed: {execution.get('status')!r}")
    if execution.get("mechanical_acceptance") is not False or execution.get("joint_acceptance") is not False:
        fail("execution scope flags are not false")
    if [row.get("case") for row in execution.get("cases", [])] != list(CASES):
        fail("execution case records are incomplete or out of order")
    if set(frozen.get("build_pins", {})) != set(CASES):
        fail("freeze build pins do not cover all cases")
    runner_pin = read_runner_build_pins()
    if any(frozen["build_pins"].get(case) != runner_pin for case in CASES):
        fail("freeze build pins differ from the frozen runner's image/binary constants")
    limits = frozen.get("limits", {})
    proposed = acceptance["native_limits_proposed"]
    limit_checks = {
        "wall_seconds_each_case": proposed["wall_seconds_per_case"],
        "cpus_each_case": proposed["cpu_count"],
        "memory_bytes_each_case": proposed["memory_bytes"],
        "memory_plus_swap_bytes_each_case": proposed["memory_bytes"],
        "network_each_case": proposed["network"],
        "aggregate_native_output_bytes_each_case": proposed["output_bytes_per_case"],
        "no_overlap": True,
    }
    for key, value in limit_checks.items():
        if limits.get(key) != value:
            fail(f"freeze run limit {key} differs from acceptance")
    if limits.get("serialized_case_order") != list(CASES) or limits.get("omp_threads") != 1 or limits.get("ccx_solver_processes") != 1:
        fail("freeze does not bind single-thread serialized execution")

    output_names = {path.name for path in audit_dir.iterdir()}
    if output_names != set(CASES) | {"execution.json"}:
        fail(f"unexpected output directory inventory: {sorted(output_names)}")
    previous_end = None
    case_records = {}
    binary_set = set()
    image_set = set()
    for index, case in enumerate(CASES, 1):
        folder = audit_dir / case
        if not folder.is_dir():
            fail(f"missing native case directory {case}")
        case_record_path = folder / "case-execution.json"
        if not case_record_path.is_file():
            fail(f"missing case-execution.json for {case}")
        record = strict_json(case_record_path)
        entry = execution["cases"][index - 1]
        if entry.get("status") != "PASS_NATIVE_CAPTURE" or sha(case_record_path) != entry.get("execution_sha256"):
            fail(f"root execution record does not bind passing case record {case}")
        if record.get("schema") != "ccx223_implicit_current_map_case_execution/v1" or record.get("case") != case or record.get("case_order_index") != index:
            fail(f"invalid case execution identity for {case}")
        if record.get("status") != "PASS_NATIVE_CAPTURE" or record.get("native_execution") is not True:
            fail(f"native capture did not pass for {case}")
        if record.get("mechanical_acceptance") is not False or record.get("joint_acceptance") is not False:
            fail(f"case {case} scope flags are not false")
        image = frozen["build_pins"][case]["image_id"]
        binary = frozen["build_pins"][case]["binary_sha256"]
        if record.get("image_id") != image or record.get("container_image_id") != image:
            fail(f"container image identity is unverified for {case}")
        if record.get("binary_sha256") != binary or record.get("binary_path") != frozen["build_pins"][case]["binary_path"]:
            fail(f"binary pin differs for {case}")
        binary_set.add(binary)
        image_set.add(image)
        state = record.get("container_state") or {}
        if record.get("docker_cli_exit_code") != 0 or state.get("ExitCode") != 0 or state.get("OOMKilled") is not False or state.get("Running") is not False:
            fail(f"native container did not exit normally for {case}")
        if record.get("stop_reason") is not None:
            fail(f"native case {case} has stop reason {record.get('stop_reason')!r}")
        if record.get("limits") != limits:
            fail(f"native case {case} limits differ from frozen limits")
        started, ended = parse_utc(record.get("started_utc", ""), f"{case}.started_utc"), parse_utc(record.get("ended_utc", ""), f"{case}.ended_utc")
        if ended < started or (ended - started).total_seconds() > proposed["wall_seconds_per_case"] + 10:
            fail(f"invalid or over-limit capture duration for {case}")
        if previous_end is not None and started < previous_end:
            fail(f"serialized cases overlap at {case}")
        previous_end = ended
        if record.get("elapsed_seconds", 0.0) > proposed["wall_seconds_per_case"]:
            fail(f"recorded capture exceeds wall limit for {case}")
        if record.get("stop_reason") is not None:
            fail(f"case {case} stopped before normal completion")
        outputs = record.get("outputs_sha256")
        if not isinstance(outputs, dict) or not set(NATIVE_FILES) <= set(outputs):
            fail(f"case {case} native output manifest is incomplete")
        actual_names = {path.name for path in folder.iterdir() if path.is_file() and path.name != "case-execution.json"}
        if any(path.is_dir() for path in folder.iterdir()) or actual_names != set(outputs):
            fail(f"case {case} output directory differs from its manifest")
        actual_hashes = {name: sha(folder / name) for name in sorted(actual_names)}
        if actual_hashes != outputs:
            fail(f"case {case} output file hash mismatch")
        input_path = folder / "coupon.inp"
        if not input_path.is_file() or sha(input_path) != expected_input_hashes[case]:
            fail(f"case {case} native working input differs from frozen input")
        native_bytes = sum((folder / name).stat().st_size for name in actual_names if name != "coupon.inp")
        if native_bytes != record.get("native_output_bytes") or native_bytes > limits["aggregate_native_output_bytes_each_case"]:
            fail(f"case {case} native output byte count differs or exceeds cap")
        stdout = (folder / "solver.stdout").read_bytes()
        if b" Job finished" not in stdout:
            fail(f"case {case} lacks normal CalculiX completion marker")
        case_records[case] = {"record": record, "folder": folder,
                              "output_hashes": actual_hashes,
                              "started_utc": started.isoformat(), "ended_utc": ended.isoformat()}
    if len(binary_set) != 1 or len(image_set) != 1:
        fail("cases did not use one pinned solver binary/image")
    return {"freeze_sha256": freeze_hash, "expected_sha256": expected_hash,
            "execution_sha256": execution_hash, "case_records": case_records,
            "local_file_count": len(actual_local), "external_file_count": len(external),
            "image_ids": sorted(image_set), "binary_sha256": sorted(binary_set)}


def audit(audit_dir: Path = OUTPUT) -> dict:
    expected, acceptance, parser = load_contract(require_ready=True)
    audit_dir = audit_dir.resolve()
    integrity = verify_freeze_and_execution(audit_dir, expected, acceptance)
    diagnostics = Audit()
    groups = expected["output_contract"]["node_id_sets"]
    physical_ids = set(map(int, groups["physical_body"]["node_ids"]))
    control_ids = set(map(int, groups["mapping_controls"]["node_ids"]))
    carrier_ids = set(map(int, groups["zero_density_carrier"]["node_ids"]))
    coordinates_by_case = {}
    captures = {}
    input_coordinates = {}
    for case in CASES:
        coordinates = parse_node_coordinates(HERE / expected["inputs"][case]["path"])
        expected_nodes = expected_node_sets(expected, case, "DAT")
        if set(coordinates) != expected_nodes:
            fail(f"{case}: deck node inventory differs from DAT expected node groups")
        coordinates_by_case[case] = coordinates
        input_coordinates[case] = {node: coordinates[node] for node in physical_ids | control_ids
                                   if node in coordinates}
    if input_coordinates["direct"] != {node: input_coordinates["mapped_no_carrier"][node]
                                          for node in physical_ids}:
        fail("physical parser-visible node coordinates differ between direct and mapped_no_carrier")
    if any(coordinates_by_case["mapped_carrier"].get(node) != coordinates_by_case["mapped_no_carrier"].get(node)
           for node in physical_ids | control_ids):
        fail("common physical/control parser-visible coordinates differ between mapped cases")

    equation_cards, fit = equation_source(expected)
    if len(equation_cards) != 6:
        fail("pinned current-map source does not have six equation cards")
    source_equation_path = HERE.parent / expected["source_files"]["nut-coupling.inp"]["path"]
    source_equations = parse_equation_cards(source_equation_path)[:6]
    for case in CASES[1:]:
        deck_equations = parse_equation_cards(HERE / expected["inputs"][case]["path"])
        if len(deck_equations) != 6:
            fail(f"{case}: expected six source equation rows")
        for i, (source_row, deck_row) in enumerate(zip(source_equations, deck_equations)):
            signature = lambda row: [(t["node"], t["dof"], t["coefficient_token"]) for t in row]
            if signature(source_row) != signature(deck_row):
                fail(f"{case}: current-map equation {i + 1} differs from pinned source")
    if len(fit["fit_nodes"]) != 251 or not set(fit["fit_nodes"]) <= physical_ids:
        fail("weighted-fit node membership is not the original 251-node physical set")

    per_case_audits, results = {}, {}
    for case in CASES:
        local_audit = Audit()
        cap = parse_capture(case, integrity["case_records"][case]["folder"],
                            expected, acceptance, parser, local_audit)
        verify_case_numerics(case, cap, coordinates_by_case[case], fit,
                             equation_cards, expected, acceptance, local_audit)
        per_case_audits[case] = local_audit
        results[case] = cap

    cross = Audit()
    for left_case, right_case in (("direct", "mapped_no_carrier"),
                                  ("mapped_no_carrier", "mapped_carrier")):
        for field_name in ("DAT_U_mm", "DAT_V_mm_s", "FRD_U_mm", "FRD_V_mm_s"):
            frd = field_name.startswith("FRD")
            cross_field_parity(left_case, right_case, field_name,
                               results[left_case], results[right_case], physical_ids,
                               expected, acceptance, cross, frd=frd)
        cross_energy_parity(left_case, right_case, results[left_case], results[right_case],
                            expected, acceptance, cross)
        if left_case != "direct":
            cross_case_controls(left_case, right_case, results[left_case], results[right_case],
                                expected, acceptance, cross)

    all_failures = sum(sum(audit.failures.values()) for audit in per_case_audits.values()) + sum(cross.failures.values())
    report = {
        "schema": "ccx223_implicit_current_map_verifier/v1",
        "status": "FAIL" if all_failures else "PASS_CURRENT_MAP_KNOWN_ANSWER",
        "input_freeze_sha256": integrity["freeze_sha256"],
        "expected_sha256": integrity["expected_sha256"],
        "execution_sha256": integrity["execution_sha256"],
        "case_order": list(CASES),
        "native_cases": {case: {"status": "FAIL" if sum(per_case_audits[case].failures.values()) else "PASS",
                                 "accepted_sta_state_count": len(results[case]["sta"]),
                                 "complete_dat_state_count": results[case]["complete_dat_state_count"],
                                 "complete_frd_state_count": results[case]["complete_frd_state_count"],
                                 "dat_node_count": len(results[case]["dat_expected_ids"]),
                                 "frd_node_count": len(results[case]["frd_expected_ids"]),
                                 "output_sha256": integrity["case_records"][case]["output_hashes"],
                                 **per_case_audits[case].result()}
                         for case in CASES},
        "direct_mapped_and_carrier_comparisons": {"status": "FAIL" if cross.failures else "PASS",
                                                    **cross.result()},
        "pinned_execution": {"local_file_count": integrity["local_file_count"],
                             "external_dependency_count": integrity["external_file_count"],
                             "image_ids": integrity["image_ids"],
                             "binary_sha256": integrity["binary_sha256"],
                             "serialized": True, "native_exit_normal": True},
        "scope": "One M00 A00 current-map coefficient set and its optional M03 zero-density rigid carrier under a small one-axis forcing; observed-method qualification only.",
        "interpretation_limit": "The linearized rigid-mode comparisons are predeclared observed-response gates, not a rigorous elastic-error bound. A failure is a fixture/method qualification failure, not a joint-capacity result or by itself a solver defect.",
        "mechanical_acceptance": False,
        "joint_acceptance": False,
        "release": False,
    }
    return report


def synthetic_expected(expected: dict, fit: dict, equations: list[list[dict]]) -> dict:
    """Small capture contract retaining all original fit/equation nodes."""
    clone = json.loads(json.dumps(expected))
    control_ids = set(map(int, clone["output_contract"]["node_id_sets"]["mapping_controls"]["node_ids"]))
    physical_ids = set(fit["fit_nodes"])
    physical_ids.update(term["node"] for row in equations for term in row if term["node"] not in control_ids)
    physical = clone["output_contract"]["node_id_sets"]["physical_body"]
    physical["node_ids"] = sorted(physical_ids)
    physical["count"] = len(physical_ids)
    physical["sha256_sorted_decimal_ids"] = id_digest(physical_ids)
    carrier = clone["output_contract"]["node_id_sets"]["zero_density_carrier"]
    carrier["node_ids"] = sorted(carrier["node_ids"][:4])
    carrier["count"] = len(carrier["node_ids"])
    carrier["sha256_sorted_decimal_ids"] = id_digest(carrier["node_ids"])
    return clone


def synthetic_sta(expected: dict) -> str:
    lines = ["SUMMARY OF JOB INFORMATION",
             "  STEP      INC     ATT  ITRS     TOT TIME     STEP TIME      INC TIME"]
    dt = expected["procedure"]["dt_s"]
    for state in expected["linearized_discrete_reference"]["states"]:
        increment = state["increment"]
        time_s = state["time_s"]
        lines.append(f"     1 {increment:10d}     1     2 {time_s:.12E} {time_s:.12E} {dt:.12E}")
    return "\n".join(lines) + "\n"


def synthetic_sta_controls(expected: dict, acceptance: dict) -> dict[str, bool]:
    """Exercise accepted-state parsing and fail-closed numeric table mutations."""
    good = synthetic_sta(expected)
    rows = parse_sta(good, expected, acceptance)
    if len(rows) != len(expected["linearized_discrete_reference"]["states"]):
        fail("synthetic STA positive control did not preserve all accepted rows")
    lines = good.splitlines()
    numeric_indices = [i for i, line in enumerate(lines) if line.split() and line.split()[0].isdigit()]
    if len(numeric_indices) != len(rows):
        fail("synthetic STA builder produced an unexpected numeric row count")

    mutations: dict[str, str] = {}
    mutations["missing"] = "\n".join(lines[:numeric_indices[-1]] + lines[numeric_indices[-1] + 1:]) + "\n"
    duplicate_lines = lines[:]
    duplicate_lines[numeric_indices[-1]] = lines[numeric_indices[-2]]
    mutations["duplicate"] = "\n".join(duplicate_lines) + "\n"

    def replace_column(line: str, column: int, token: str) -> str:
        words = line.split()
        words[column] = token
        return " ".join(words)

    wrong_time = lines[:]
    wrong_time[numeric_indices[0]] = replace_column(wrong_time[numeric_indices[0]], 4, "9.000000E-03")
    mutations["wrong_time"] = "\n".join(wrong_time) + "\n"
    wrong_dt = lines[:]
    wrong_dt[numeric_indices[0]] = replace_column(wrong_dt[numeric_indices[0]], 6, "2.000000E-03")
    mutations["wrong_dt"] = "\n".join(wrong_dt) + "\n"
    retry = lines[:]
    retry[numeric_indices[0]] = replace_column(retry[numeric_indices[0]], 2, "1U")
    mutations["retry_ATT_1U"] = "\n".join(retry) + "\n"
    malformed_extra = lines + ["     1         11     1     2 1.100000E-02 1.100000E-02"]
    mutations["malformed_extra_numeric_row"] = "\n".join(malformed_extra) + "\n"

    passed = {"valid_accepted_schedule": True}
    for name, text in mutations.items():
        try:
            parse_sta(text, expected, acceptance)
        except (ValueError, TypeError, OverflowError):
            passed[name] = True
        else:
            fail(f"synthetic STA negative control {name} was accepted")
    return passed


def synthetic_capture(folder: Path, case: str, expected: dict, acceptance: dict,
                      coordinates: dict[int, tuple[float, float, float]], *,
                      equations: list[list[dict]],
                      wrong_gain: bool = False, missing_dat_node: bool = False,
                      missing_dat_state: bool = False, wrong_energy: bool = False,
                      wrong_mass: bool = False,
                      wrong_energy_nan: bool = False, wrong_frd_axis: bool = False,
                      nonfinite_frd: bool = False, duplicate_frd: bool = False,
                      wrong_frd_labels: bool = False) -> None:
    folder.mkdir(parents=True, exist_ok=True)
    groups = expected["output_contract"]["node_id_sets"]
    physical = set(map(int, groups["physical_body"]["node_ids"]))
    controls = set(map(int, groups["mapping_controls"]["node_ids"]))
    carrier = set(map(int, groups["zero_density_carrier"]["node_ids"]))
    dat_ids = expected_node_sets(expected, case, "DAT")
    frd_ids = expected_node_sets(expected, case, "FRD")
    ref_id, rot_id = map(int, expected["pivot_and_current_map"]["control_node_ids"])
    pivot = tuple(map(float, expected["pivot_and_current_map"]["pivot_xyz_mm"]))
    body_set = expected["physical_body_reference"]["body_id"].upper()
    carrier_set = expected["zero_density_carrier_reference"]["body_id"].upper()
    states = expected["linearized_discrete_reference"]["states"]
    dat_lines = []
    frd_lines = []
    if case != "mapped_carrier":
        carrier = set()
    for state_index_value, state in enumerate(states):
        time_s = state["time_s"]
        theta = state["rotation_vector_y_rad"]
        omega = state["angular_velocity_y_rad_s"]
        equation_control_u = {ref_id: (0.0, 0.0, 0.0), rot_id: (0.0, theta, 0.0)}
        control_u = dict(equation_control_u)
        control_v = {ref_id: (0.0, 0.0, 0.0), rot_id: (0.0, omega, 0.0)}
        if wrong_gain and case == "mapped_carrier" and state_index_value == len(states) - 1:
            control_u[rot_id] = (0.0, theta * 1.0001, 0.0)
        dat_vectors = {}
        for node in physical:
            dat_vectors[node] = (expected_vector("U", node, coordinates[node], state, pivot),
                                 expected_vector("V", node, coordinates[node], state, pivot))
        for node in controls:
            dat_vectors[node] = (control_u[node], control_v[node])
        for node in carrier:
            dat_vectors[node] = carrier_prediction(coordinates[node], pivot,
                                                   control_u[ref_id], control_u[rot_id],
                                                   control_v[ref_id], control_v[rot_id])
        equation_u_tokens = {}
        if case != "direct":
            for equation_index, terms in enumerate(equations):
                dep_node, dep_dof = map(int, expected["pivot_and_current_map"]["dependent_node_dofs"][equation_index])
                dependent = [term for term in terms if (term["node"], term["dof"]) == (dep_node, dep_dof)]
                if len(dependent) != 1 or dependent[0]["coefficient"] == 0:
                    fail(f"synthetic equation {equation_index + 1} lacks its unique unit dependent DOF")
                other_sum = Decimal(0)
                for term in terms:
                    if (term["node"], term["dof"]) == (dep_node, dep_dof):
                        continue
                    source_vector = equation_control_u[term["node"]] if term["node"] in controls else dat_vectors[term["node"]][0]
                    lexical_value = format(source_vector[term["dof"] - 1], ".6E")
                    other_sum += term["coefficient"] * decimal_number(lexical_value)
                exact_dependent = -other_sum / dependent[0]["coefficient"]
                equation_u_tokens[(dep_node, dep_dof)] = format(exact_dependent, ".6E")

        for kind_index, (kind, selector, description) in enumerate((
                ("U", 0, "displacements (vx,vy,vz)"),
                ("V", 1, "velocities (vx,vy,vz)"))):
            if missing_dat_state and case == "mapped_no_carrier" and kind == "U" and state_index_value == len(states) - 1:
                continue
            dat_lines.append(f"{description} for set N_OBSERVE and time {time_s:.12E}")
            for node in sorted(dat_ids):
                if missing_dat_node and case == "mapped_no_carrier" and kind == "V" and state_index_value == len(states) - 1 and node == min(physical):
                    continue
                vector = dat_vectors[node][selector]
                tokens = [equation_u_tokens.get((node, axis + 1), format(value, ".6E"))
                          if kind == "U" else format(value, ".6E")
                          for axis, value in enumerate(vector)]
                dat_lines.append(f"{node} " + " ".join(tokens))
            dat_lines.append("")

        energy_sets = expected["output_contract"]["EL_PRINT_by_case"][case]
        for set_name, channels in energy_sets.items():
            if set_name.upper() == body_set:
                energy_values = {"ELSE": 0.0, "ELKE": state["linearized_ELKE_Nmm"],
                                 "EMAS": expected["physical_body_reference"]["mass_tonne"],
                                 "EVOL": expected["physical_body_reference"]["volume_mm3"]}
            else:
                energy_values = {"ELSE": 0.0, "ELKE": 0.0, "EMAS": 0.0,
                                 "EVOL": expected["zero_density_carrier_reference"]["volume_mm3"]}
            for kind, label in (("ELSE", "internal energy"), ("ELKE", "kinetic energy"),
                                ("EMAS", "mass"), ("EVOL", "volume")):
                if kind not in channels:
                    continue
                value = energy_values[kind]
                token = f"{value:.6E}"
                if wrong_energy and case == "direct" and set_name.upper() == body_set and kind == "ELKE" and state_index_value == len(states) - 1:
                    token = f"{value * 1.1:.6E}"
                if wrong_mass and case == "direct" and set_name.upper() == body_set and kind == "EMAS" and state_index_value == len(states) - 1:
                    token = f"{value * 1.1:.6E}"
                if wrong_energy_nan and case == "mapped_carrier" and set_name.upper() == carrier_set and kind == "EMAS" and state_index_value == len(states) - 1:
                    token = "NaN"
                dat_lines.extend((f"total {label} for set {set_name} and time {time_s:.12E}", token, ""))

        # The real source prints these auxiliary inertia and center-of-gravity
        # blocks after the M03 mass row. They are undefined at zero mass and
        # outside this verifier's required finite-output scope.
        if case == "mapped_carrier" and state_index_value == len(states) - 1:
            dat_lines.extend((
                f"total mass moment of inertia (xx,yy,zz,xy,xz,yz) for set {carrier_set} and time {time_s:.7E}",
                "NaN NaN NaN NaN NaN NaN",
                f"center of gravity for set {carrier_set} and time {time_s:.7E}",
                "NaN NaN NaN",
                f"total mass moment of inertia about the center ofgravity (xx,yy,zz,xy,xz,yz) for set {carrier_set} and time {time_s:.7E}",
                "NaN NaN NaN NaN NaN NaN",
                ""))

        increment = state["increment"]
        frd_lines.extend((f"    1PSTEP                         {increment}           {increment}           1",
                          f"  100CL  {100 + increment} {time_s:.12E} {len(frd_ids)} 0 1 {increment} 1"))
        for kind, selector, labels in (("DISP", 0, ("D1", "D2", "D3")),
                                       ("VELO", 1, ("V1", "V2", "V3"))):
            output_labels = list(labels)
            if wrong_frd_labels and case == "direct" and kind == "DISP" and state_index_value == 0:
                output_labels[0] = "Q1"
            frd_lines.extend((f" -4 {kind} 4 1",
                              f" -5 {output_labels[0]} 1 2 1 0",
                              f" -5 {output_labels[1]} 1 2 2 0",
                              f" -5 {output_labels[2]} 1 2 3 0",
                              " -5 ALL 1 2 0 0 1ALL"))
            for node in sorted(frd_ids):
                vector = dat_vectors[node][selector]
                if wrong_frd_axis and case == "direct" and kind == "DISP" and state_index_value == len(states) - 1 and node == min(physical):
                    vector = (vector[0] + 1.0e-3, vector[1], vector[2])
                token_values = [f"{value:12.5E}" for value in vector]
                if nonfinite_frd and case == "direct" and kind == "DISP" and state_index_value == 0 and node == min(physical):
                    token_values[0] = f"{'NaN':>12}"
                row = " -1" + f"{node:10d}" + "".join(token_values)
                frd_lines.append(row)
                if duplicate_frd and case == "direct" and kind == "DISP" and state_index_value == 0 and node == min(physical):
                    frd_lines.append(row)
            frd_lines.append(" -3")
    (folder / "coupon.dat").write_text("\n".join(dat_lines) + "\n")
    (folder / "coupon.frd").write_text("\n".join(frd_lines) + "\n")
    (folder / "coupon.sta").write_text(synthetic_sta(expected))


def synthetic_case_audit(folder: Path, case: str, expected: dict, acceptance: dict,
                         parser: object, coordinates: dict[int, tuple[float, float, float]],
                         fit: dict, equations: list[list[dict]], **flags):
    synthetic_capture(folder, case, expected, acceptance, coordinates,
                      equations=equations, **flags)
    local = Audit()
    capture = parse_capture(case, folder, expected, acceptance, parser, local)
    verify_case_numerics(case, capture, coordinates, fit, equations,
                         expected, acceptance, local)
    return capture, local


def self_test() -> dict:
    expected, acceptance, parser = load_contract(require_ready=False)
    controls = {}
    if "FRD_U_mm" not in acceptance["tolerances"] or not callable(parser.parse_frd):
        fail("pinned parser/acceptance self-test contract failed")
    controls["pinned_parser_loaded"] = True
    if decimal_half_ulp("0.000000E+00") != 0 or decimal_half_ulp("1.234567E-05") != Decimal("5e-12"):
        fail("scientific-token half-ULP calculation failed")
    controls["zero_token_has_zero_half_ulp"] = True
    controls.update({f"STA_{name}": passed
                     for name, passed in synthetic_sta_controls(expected, acceptance).items()})

    equations, fit = equation_source(expected)
    test_expected = synthetic_expected(expected, fit, equations)
    direct_coordinates = parse_node_coordinates(HERE / expected["inputs"]["direct"]["path"])
    carrier_coordinates = parse_node_coordinates(HERE / expected["inputs"]["mapped_carrier"]["path"])
    coordinates_by_case = {
        "direct": direct_coordinates,
        "mapped_no_carrier": direct_coordinates,
        "mapped_carrier": carrier_coordinates,
    }

    dat_probe = ("displacements (vx,vy,vz) for set N_OBSERVE and time 1.000000E-03\n"
                 "116163 0.000000E+00 0.000000E+00 0.000000E+00\n\n"
                 "velocities (vx,vy,vz) for set N_OBSERVE and time 1.000000E-03\n"
                 "116163 0.000000E+00 0.000000E+00 0.000000E+00\n\n")
    dat_fields, _, dat_errors = parser.parse_dat(dat_probe)
    if dat_errors or len(dat_fields) != 2:
        fail("synthetic DAT parser positive control failed")
    if not parser.parse_dat(dat_probe.replace("116163 0.000000E+00 0.000000E+00 0.000000E+00\n\n",
                                              "116163 0.000000E+00 0.000000E+00 0.000000E+00\n"
                                              "116163 0.000000E+00 0.000000E+00 0.000000E+00\n\n", 1))[2]:
        fail("synthetic duplicate DAT row was not rejected")
    controls["dat_parser_positive_duplicate_negative"] = True

    example_terms = [
        {"node": 1, "dof": 1, "coefficient": Decimal("1"), "coefficient_token": "1"},
        {"node": 2, "dof": 1, "coefficient": Decimal("-1"), "coefficient_token": "-1"},
    ]
    lexical_nodes = {1: ["1.000000E-03", "0.000000E+00", "0.000000E+00"],
                     2: ["1.000000E-03", "0.000000E+00", "0.000000E+00"]}
    lexical_bound, arithmetic_bound = equation_rounding_allowance(example_terms, lexical_nodes, acceptance)
    exact_residual = abs(sum(t["coefficient"] * decimal_number(lexical_nodes[t["node"]][0])
                             for t in example_terms))
    if exact_residual > lexical_bound + arithmetic_bound:
        fail("synthetic equation residual positive control failed")
    lexical_nodes[2][0] = "1.001000E-03"
    wrong_residual = abs(sum(t["coefficient"] * decimal_number(lexical_nodes[t["node"]][0])
                             for t in example_terms))
    if wrong_residual <= lexical_bound + arithmetic_bound:
        fail("synthetic equation residual negative control was accepted")
    controls["equation_rounding_positive_negative"] = True

    with tempfile.TemporaryDirectory(prefix="current-map-verifier-self-test-") as temporary:
        root = Path(temporary)
        captures, meters = {}, {}
        for case in CASES:
            captures[case], meters[case] = synthetic_case_audit(
                root / "positive" / case, case, test_expected, acceptance, parser,
                coordinates_by_case[case], fit, equations)
            if meters[case].failures:
                fail(f"synthetic positive {case} capture failed: {meters[case].result()}")
        parity = Audit()
        physical_ids = set(map(int, test_expected["output_contract"]["node_id_sets"]["physical_body"]["node_ids"]))
        for left_case, right_case in (("direct", "mapped_no_carrier"),
                                      ("mapped_no_carrier", "mapped_carrier")):
            for channel in ("DAT_U_mm", "DAT_V_mm_s", "FRD_U_mm", "FRD_V_mm_s"):
                cross_field_parity(left_case, right_case, channel, captures[left_case], captures[right_case],
                                   physical_ids, test_expected, acceptance, parity,
                                   frd=channel.startswith("FRD"))
            cross_energy_parity(left_case, right_case, captures[left_case], captures[right_case],
                                test_expected, acceptance, parity)
            if left_case != "direct":
                cross_case_controls(left_case, right_case, captures[left_case], captures[right_case],
                                    test_expected, acceptance, parity)
        if parity.failures:
            fail(f"synthetic cross-case positive comparison failed: {parity.result()}")
        controls["three_case_parser_and_numerical_positive"] = True
        controls["synthetic_STA_and_all_DAT_FRD_states"] = True
        controls["zero_mass_auxiliary_nan_ignored"] = True

        # Wrong controller gain changes only the controller value; physical M00
        # output rows stay byte-for-byte numerically identical to the positive capture.
        bad_capture, bad_audit = synthetic_case_audit(
            root / "wrong-gain" / "mapped_carrier", "mapped_carrier", test_expected,
            acceptance, parser, coordinates_by_case["mapped_carrier"], fit, equations,
            wrong_gain=True)
        good_capture = captures["mapped_carrier"]
        physical_ids_test = set(map(int, test_expected["output_contract"]["node_id_sets"]["physical_body"]["node_ids"]))
        physical_unchanged = all(
            good_capture["dat"][(kind, "N_OBSERVE", i)]["nodes"][node] ==
            bad_capture["dat"][(kind, "N_OBSERVE", i)]["nodes"][node]
            for kind in ("U", "V") for i in range(len(test_expected["linearized_discrete_reference"]["states"]))
            for node in physical_ids_test)
        if not physical_unchanged or not (bad_audit.failures.get("controller_oracle_U", 0)
                                           or bad_audit.failures.get("controller_fit_U", 0)):
            fail("wrong-controller-gain synthetic control did not fail with physical fields unchanged")
        controls["wrong_controller_gain_rejected_physical_fields_unchanged"] = True

        negatives = [
            ("missing_node", "mapped_no_carrier", {"missing_dat_node": True}, "DAT_node_coverage"),
            ("missing_state", "mapped_no_carrier", {"missing_dat_state": True}, "DAT_required_field"),
            ("wrong_energy", "direct", {"wrong_energy": True}, "energy_oracle"),
            ("wrong_finite_mass", "direct", {"wrong_mass": True}, "energy_oracle"),
            ("wrong_FRD_axis", "direct", {"wrong_frd_axis": True}, "direct_FRD_U_mm_oracle"),
            ("wrong_FRD_component_labels", "direct", {"wrong_frd_labels": True}, "FRD_component_labels"),
            ("nonfinite_FRD", "direct", {"nonfinite_frd": True}, "FRD_parse"),
            ("duplicate_FRD", "direct", {"duplicate_frd": True}, "FRD_parse"),
            ("nonfinite_required_energy", "mapped_carrier", {"wrong_energy_nan": True}, "DAT_parse"),
        ]
        for name, case, flags, category in negatives:
            _capture, negative_audit = synthetic_case_audit(
                root / name / case, case, test_expected, acceptance, parser,
                coordinates_by_case[case], fit, equations, **flags)
            if not negative_audit.failures.get(category):
                fail(f"synthetic negative control {name} was not rejected by {category}")
            controls[f"{name}_rejected"] = True

    return {"schema": "ccx223_implicit_current_map_verifier_self_test/v1",
            "status": "PASS_SYNTHETIC_CONTROLS", "controls": controls,
            "native_execution": False, "native_run_performed": False,
            "mechanical_acceptance": False, "joint_acceptance": False}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--audit-dir", type=Path, help="directory created by the parent serialized runner")
    mode.add_argument("--self-test", action="store_true", help="run synthetic parser and arithmetic controls only")
    parser.add_argument("--write", action="store_true", help="write the post-run verifier.json once")
    args = parser.parse_args()
    try:
        report = self_test() if args.self_test else audit(args.audit_dir or OUTPUT)
    except Exception as exc:
        report = {"schema": "ccx223_implicit_current_map_verifier/v1",
                  "status": "FAIL_CLOSED", "errors": [str(exc)],
                  "mechanical_acceptance": False, "joint_acceptance": False,
                  "release": False}
    rendered = json.dumps(report, indent=2, sort_keys=True, allow_nan=False) + "\n"
    if args.write:
        target = HERE / "verifier.json"
        with target.open("x", encoding="utf-8") as stream:
            stream.write(rendered)
    print(rendered, end="")
    return 0 if report["status"] in ("PASS_SYNTHETIC_CONTROLS", "PASS_CURRENT_MAP_KNOWN_ANSWER") else 1


if __name__ == "__main__":
    raise SystemExit(main())
