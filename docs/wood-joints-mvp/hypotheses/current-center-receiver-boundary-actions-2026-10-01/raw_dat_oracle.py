#!/usr/bin/env python3
"""Independently reconstruct center-boundary actions from frozen native DAT files."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[4]
PACKET = Path(__file__).resolve().parent
FREEZE_PATH = (
    ROOT
    / "docs/wood-joints-mvp/hypotheses/upper-frame-joint-review-2026-09-30/freeze.json"
)
FREEZE_SHA256 = "d4ba1c78eb358d25e32819201e9c59e05d425a06d9e4e5cca3dc09d7139ffd73"
MEMBERS = (
    "base_header",
    "base_post_center_left",
    "base_post_center_right",
    "center_post_cleat_left",
    "center_post_cleat_right",
)
FACTORS = (0.1, 0.2, 0.3, 0.45, 0.675, 0.925, 1.0)
CANDIDATE = "compact-floor-flush-wood-joints-development"
REVISION = "led-clearance-2x6-runner-seated-blocks-v1"
FLOOR_TANGENT_LAW = "floor_tangent_all_bearing_hypothesis"
BALANCE_FORCE_TOL_N = 0.1
BALANCE_MOMENT_TOL_NMM = 2.0

_DAT_HEADER = re.compile(
    r"^\s*(displacements|forces)\s*\([^)]*\).*?\btime\s+([0-9.+\-EeDd]+)\s*$",
    re.IGNORECASE,
)
_NUMBER = re.compile(r"^[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[EeDd][+-]?\d+)?$")


class OracleError(ValueError):
    """Raised when a frozen source or raw DAT reconstruction is inconsistent."""


def require(condition: Any, message: str) -> None:
    if not condition:
        raise OracleError(message)


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def _number(token: str) -> float:
    require(_NUMBER.fullmatch(token) is not None, f"invalid numeric token: {token!r}")
    value = float(token.replace("D", "E").replace("d", "e"))
    require(math.isfinite(value), f"nonfinite numeric token: {token!r}")
    return value


def half_last_place(token: str) -> float:
    """Return the round-to-nearest interval radius represented by one printed token."""
    _number(token)
    parts = re.split("[EeDd]", token)
    mantissa = parts[0]
    exponent = int(parts[1]) if len(parts) == 2 else 0
    decimals = len(mantissa.split(".", 1)[1]) if "." in mantissa else 0
    radius = 0.5 * 10.0 ** (exponent - decimals)
    require(math.isfinite(radius) and radius >= 0.0, f"invalid token radius: {token!r}")
    return radius


def _finish_dat_block(
    current: dict[str, Any] | None,
    blocks: dict[float, dict[str, Any]],
) -> None:
    if current is None:
        return
    require(bool(current["values"]), f"empty ALLN {current['kind']} block at {current['time']}")
    state = blocks.setdefault(current["time"], {})
    kind = current["kind"]
    require(kind not in state, f"duplicate ALLN {kind} block at {current['time']}")
    state[kind] = current["values"]
    state[kind + "_radius"] = current["radii"]
    state[kind + "_tokens"] = current["tokens"]


def parse_dat_text(
    text: str,
    *,
    expected_count: int | None = 7,
    expected_nodes: set[int] | None = None,
) -> dict[float, dict[str, Any]]:
    """Parse token-preserving paired ALLN U/RF blocks from a CalculiX DAT string."""
    blocks: dict[float, dict[str, Any]] = {}
    current: dict[str, Any] | None = None

    for line in text.splitlines():
        match = _DAT_HEADER.match(line)
        if match:
            _finish_dat_block(current, blocks)
            current = None
            if "FOR SET ALLN" not in line.upper():
                continue
            kind = "u" if match.group(1).lower() == "displacements" else "rf"
            time = _number(match.group(2))
            current = {
                "kind": kind,
                "time": time,
                "values": {},
                "radii": {},
                "tokens": {},
                "started": False,
            }
            continue

        if current is None:
            continue
        fields = line.split()
        if len(fields) == 4 and fields[0].isdigit():
            node = int(fields[0])
            require(node not in current["values"], f"duplicate node {node} in {current['kind']} block")
            tokens = fields[1:]
            values = [_number(token) for token in tokens]
            radii = [half_last_place(token) for token in tokens]
            current["values"][node] = values
            current["radii"][node] = radii
            current["tokens"][node] = tokens
            current["started"] = True
        elif current["started"]:
            _finish_dat_block(current, blocks)
            current = None
        elif fields:
            # DAT headings between the block title and its first node row are harmless.
            continue

    _finish_dat_block(current, blocks)
    require(bool(blocks), "native DAT contains no ALLN displacement/reaction blocks")
    if expected_count is not None:
        require(len(blocks) == expected_count, f"expected {expected_count} ALLN states, got {len(blocks)}")
    for time, state in sorted(blocks.items()):
        require(set(state) == {"u", "u_radius", "u_tokens", "rf", "rf_radius", "rf_tokens"},
                f"unmatched ALLN U/RF block at time {time}")
        require(set(state["u"]) == set(state["rf"]), f"ALLN U/RF node inventories differ at {time}")
        if expected_nodes is not None:
            require(set(state["rf"]) == expected_nodes, f"ALLN node inventory differs at {time}")
    return dict(sorted(blocks.items()))


def parse_deck_text(text: str) -> dict[str, Any]:
    """Read emitted node, element, CLOAD and static-step cards without a solver."""
    cards: list[tuple[str, list[str]]] = []
    header: str | None = None
    rows: list[str] = []
    for line in text.splitlines():
        value = line.strip()
        if not value or value.startswith("**"):
            continue
        if value.startswith("*"):
            if header is not None:
                cards.append((header, rows))
            header, rows = value, []
        elif header is not None:
            rows.append(value)
    if header is not None:
        cards.append((header, rows))

    nodes: dict[int, dict[str, Any]] = {}
    elements: dict[int, dict[str, Any]] = {}
    element_sets: set[str] = set()
    cload_terms: dict[tuple[int, int], list[tuple[float, float]]] = defaultdict(list)
    static_times: list[float] = []

    for card_header, card_rows in cards:
        card = card_header.split(",", 1)[0].strip().upper()
        parameters = {}
        for part in card_header.split(",")[1:]:
            if "=" in part:
                key, value = part.split("=", 1)
                parameters[key.strip().upper()] = value.strip()
        if card == "*NODE":
            for row in card_rows:
                fields = [field.strip() for field in row.split(",")]
                require(len(fields) == 4, f"unexpected emitted node row: {row!r}")
                node = int(fields[0])
                require(node not in nodes, f"duplicate emitted node {node}")
                tokens = fields[1:]
                nodes[node] = {
                    "values": [_number(token) for token in tokens],
                    "radii": [half_last_place(token) for token in tokens],
                    "tokens": tokens,
                }
        elif card == "*ELEMENT":
            element_type = parameters.get("TYPE", "").upper()
            element_set = parameters.get("ELSET")
            if element_set:
                element_sets.add(element_set)
            require(bool(element_type), "emitted *ELEMENT card has no TYPE")
            node_counts = {"C3D20": 20, "SPRING2": 2, "SPRINGA": 2}
            require(element_type in node_counts,
                    f"unsupported emitted element type: {element_type}")
            expected_node_count = node_counts[element_type]
            current_element: int | None = None
            current_nodes: list[int] = []

            def save_element(node_count=expected_node_count, kind=element_type, group=element_set) -> None:
                nonlocal current_element, current_nodes
                if current_element is None:
                    return
                require(len(current_nodes) == node_count,
                        f"emitted {kind} {current_element} has "
                        f"{len(current_nodes)} nodes, expected {node_count}")
                require(current_element not in elements,
                        f"duplicate emitted element {current_element}")
                elements[current_element] = {
                    "type": kind,
                    "nodes": current_nodes,
                    "elset": group,
                }
                current_element, current_nodes = None, []

            for row in card_rows:
                fields = [field.strip() for field in row.split(",") if field.strip()]
                require(bool(fields), f"empty emitted element row: {row!r}")
                if current_element is None or len(current_nodes) == expected_node_count:
                    save_element()
                    require(len(fields) >= 2, f"unexpected emitted element row: {row!r}")
                    current_element = int(fields[0])
                    current_nodes = [int(value) for value in fields[1:]]
                else:
                    current_nodes.extend(int(value) for value in fields)
                require(len(current_nodes) <= expected_node_count,
                        f"emitted {element_type} row exceeds its connectivity width")
            save_element()
        elif card == "*CLOAD":
            for row in card_rows:
                fields = [field.strip() for field in row.split(",")]
                require(len(fields) == 3, f"unexpected emitted CLOAD row: {row!r}")
                node, dof = int(fields[0]), int(fields[1])
                token = fields[2]
                cload_terms[(node, dof)].append((_number(token), half_last_place(token)))
        elif card == "*STATIC":
            require(bool(card_rows), "emitted *STATIC card has no data row")
            fields = [field.strip() for field in card_rows[0].split(",")]
            require(len(fields) >= 2, "emitted *STATIC row has no total time")
            static_times.append(_number(fields[1]))

    require(bool(nodes), "emitted deck contains no *NODE records")
    require(len(static_times) == 1 and static_times[0] > 0.0,
            "expected one positive single-step *STATIC total time")
    require(all(set(row["nodes"]) <= set(nodes) for row in elements.values()),
            "emitted element references a missing node")
    cload: dict[tuple[int, int], dict[str, float]] = {}
    for key, terms in cload_terms.items():
        cload[key] = {
            "value": math.fsum(value for value, _ in terms),
            "radius": math.fsum(radius for _, radius in terms),
        }
    return {
        "nodes": nodes,
        "elements": elements,
        "element_sets": element_sets,
        "cload": cload,
        "total_time": static_times[0],
    }


def recover_spring2_scalar(
    rf: dict[int, list[float]],
    rf_radius: dict[int, list[float]],
    nodes: list[int],
    dof: int,
) -> tuple[float, float]:
    """Recover the physical force on endpoint one and its token interval radius."""
    require(len(nodes) == 2 and dof in (1, 2, 3), "invalid SPRING2 source channel")
    first, second = map(int, nodes)
    require(first in rf and second in rf, "SPRING2 RF endpoint is absent")
    index = dof - 1
    force = 0.5 * (rf[second][index] - rf[first][index])
    radius = 0.5 * (rf_radius[first][index] + rf_radius[second][index])
    guard = 64.0 * math.ulp(max(1.0, abs(rf[first][index]), abs(rf[second][index])))
    require(abs(rf[first][index] + rf[second][index])
            <= rf_radius[first][index] + rf_radius[second][index] + guard,
            "SPRING2 endpoint RF intervals do not satisfy action/reaction")
    return force, radius


def recover_springa_scalar(
    rf: dict[int, list[float]],
    rf_radius: dict[int, list[float]],
    nodes: list[int],
    axis: list[float],
) -> tuple[float, float]:
    """Recover the physical first-body scalar from the SPRINGA q endpoint RF."""
    require(len(nodes) == 2, "invalid SPRINGA endpoint mapping")
    q_node, ground = map(int, nodes)
    require(q_node in rf and ground in rf, "SPRINGA RF endpoint is absent")
    direction = _vec(axis)
    require(abs(math.sqrt(math.fsum(value * value for value in direction)) - 1.0) <= 1e-10,
            "SPRINGA physical axis is not unit length")
    force = math.fsum(rf[q_node][index] * direction[index] for index in range(3))
    radius = math.fsum(abs(direction[index]) * rf_radius[q_node][index] for index in range(3))
    guard = 64.0 * math.ulp(max(1.0, *(abs(value) for value in rf[q_node] + rf[ground])))
    require(all(
        abs(rf[q_node][index] + rf[ground][index])
        <= rf_radius[q_node][index] + rf_radius[ground][index] + guard
        for index in range(3)
    ), "SPRINGA endpoint RF intervals do not satisfy action/reaction")
    return force, radius


def recover_selected_floor_scalar(
    reference_rf: float,
    reference_radius: float,
    source_load_correction: float,
    load_factor: float,
) -> tuple[float, float]:
    """Remove the source-load transfer at the selected scalar reference DOF."""
    require(all(math.isfinite(value) for value in (
        reference_rf, reference_radius, source_load_correction, load_factor
    )), "nonfinite selected-floor scalar input")
    require(reference_radius >= 0.0 and 0.0 <= load_factor <= 1.0 + 1e-8,
            "invalid selected-floor scalar interval or load factor")
    return reference_rf - source_load_correction * load_factor, reference_radius


def verify_inactive_floor_zero(
    rf: dict[int, list[float]],
    rf_radius: dict[int, list[float]],
    node: int,
) -> tuple[list[float], list[float]]:
    """Require an omitted tangent channel's isolated carryover RF intervals to contain zero."""
    require(node in rf and node in rf_radius, "inactive floor output node is absent")
    value = _vec(rf[node])
    radius = _vec(rf_radius[node], nonnegative=True)
    for center, bound in zip(value, radius, strict=True):
        guard = 64.0 * math.ulp(max(1.0, abs(center)))
        require(abs(center) <= bound + guard, "inactive floor carryover RF interval excludes zero")
    return value, radius


def _vec(values: Any, *, nonnegative: bool = False) -> list[float]:
    require(isinstance(values, (list, tuple)) and len(values) == 3, "expected a three-vector")
    result = [float(value) for value in values]
    require(all(math.isfinite(value) and (not nonnegative or value >= 0.0) for value in result),
            "nonfinite vector or invalid radius")
    return result


def _add(a: list[float], b: list[float]) -> list[float]:
    return [x + y for x, y in zip(a, b, strict=True)]


def _sum_vectors(vectors: list[list[float]]) -> list[float]:
    return [math.fsum(vector[index] for vector in vectors) for index in range(3)]


def _cross(a: list[float], b: list[float]) -> list[float]:
    return [
        a[1] * b[2] - a[2] * b[1],
        a[2] * b[0] - a[0] * b[2],
        a[0] * b[1] - a[1] * b[0],
    ]


def _moment_radius(arm: list[float], radius: list[float]) -> list[float]:
    return [
        abs(arm[1]) * radius[2] + abs(arm[2]) * radius[1],
        abs(arm[2]) * radius[0] + abs(arm[0]) * radius[2],
        abs(arm[0]) * radius[1] + abs(arm[1]) * radius[0],
    ]


def _wrench_at_origin(point: list[float], force: list[float]) -> list[float]:
    return force + _cross(point, force)


def _wrench_sum(rows: list[list[float]]) -> list[float]:
    return [math.fsum(row[index] for row in rows) for index in range(6)]


def _close(actual: Any, expected: Any, label: str, tolerance: float = 1e-8) -> float:
    left, right = _vec(actual), _vec(expected)
    error = max(abs(a - b) for a, b in zip(left, right, strict=True))
    require(error <= tolerance, f"{label} differs by {error:g} (limit {tolerance:g})")
    return error


def _close6(actual: Any, expected: Any, label: str, tolerance: float = 1e-8) -> float:
    require(isinstance(actual, (list, tuple)) and len(actual) == 6, f"{label} is not a six-vector")
    require(isinstance(expected, (list, tuple)) and len(expected) == 6,
            f"expected {label} is not a six-vector")
    left, right = [float(x) for x in actual], [float(x) for x in expected]
    require(all(math.isfinite(x) for x in left + right), f"{label} contains nonfinite values")
    error = max(abs(a - b) for a, b in zip(left, right, strict=True))
    require(error <= tolerance, f"{label} differs by {error:g} (limit {tolerance:g})")
    return error


def _read_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise OracleError(f"cannot read JSON {path}: {error}") from error
    require(isinstance(value, dict), f"expected JSON object in {path}")
    return value


def _load_freeze() -> dict[str, Any]:
    require(FREEZE_PATH.is_file(), f"missing source freeze: {FREEZE_PATH}")
    observed = sha256_file(FREEZE_PATH)
    require(observed == FREEZE_SHA256, f"source freeze hash changed: {observed}")
    freeze = _read_json(FREEZE_PATH)
    require(freeze.get("candidate") == CANDIDATE, "freeze candidate differs")
    require(freeze.get("geometry_revision_id") == REVISION, "freeze geometry revision differs")
    require(set(freeze.get("cases", {})) == {"a1-rear", "a12-rear", "k12-rear"},
            "freeze rear-case inventory differs")
    return freeze


def _load_bundle(freeze: dict[str, Any], case: str) -> dict[str, Any]:
    source = freeze["cases"][case]
    required = {"model", "deck", "native_data", "response", "all_body_audit", "terminal"}
    require(required <= set(source), f"{case} freeze is missing required input records")
    if case == "a1-rear":
        require("serialization" in source, "A1 serialization record is missing from freeze")
    paths: dict[str, Path] = {}
    hashes: dict[str, str] = {}
    for name, pin in source.items():
        require(isinstance(pin, dict) and {"path", "sha256"} <= set(pin),
                f"{case} freeze record is malformed: {name}")
        path = ROOT / pin["path"]
        require(path.is_file(), f"{case} frozen source is missing: {pin['path']}")
        actual = sha256_file(path)
        require(actual == pin["sha256"], f"{case} frozen source hash changed: {pin['path']}")
        paths[name] = path
        hashes[name] = actual

    model = _read_json(paths["model"])
    audit = _read_json(paths["all_body_audit"])
    require(model.get("candidate") == CANDIDATE, f"{case} model candidate differs")
    require(model.get("geometry_revision_id") == REVISION, f"{case} model revision differs")
    require(model.get("case_id") == case, f"{case} model case identity differs")
    require(model.get("qualified_for_design") is False, f"{case} model claims qualification")
    require(model.get("mechanical_acceptance") is False, f"{case} model claims mechanical acceptance")
    require(model.get("complete_joint_validated") is False, f"{case} model claims joint validation")
    require(audit.get("source_model_sha256") == hashes["model"],
            f"{case} all-body audit is bound to a different model")
    require(audit.get("source_response_sha256") == hashes["response"],
            f"{case} all-body audit is bound to a different response")
    require(audit.get("joint_accepted") is False, f"{case} all-body audit claims joint acceptance")

    deck = parse_deck_text(paths["deck"].read_text(encoding="utf-8"))
    native = parse_dat_text(
        paths["native_data"].read_text(encoding="utf-8"),
        expected_count=7,
        expected_nodes=set(deck["nodes"]),
    )
    _bind_model_to_deck(model, deck, case)
    return {
        "case": case,
        "paths": paths,
        "hashes": hashes,
        "model": model,
        "audit": audit,
        "deck": deck,
        "native": native,
    }


def _bind_model_to_deck(model: dict[str, Any], deck: dict[str, Any], case: str) -> None:
    model_nodes = {int(node): _vec(point) for node, point in model["nodes"].items()}
    require(set(model_nodes) == set(deck["nodes"]), f"{case} model/deck node IDs differ")
    for node, source_point in model_nodes.items():
        emitted = deck["nodes"][node]
        for index in range(3):
            center, radius = emitted["values"][index], emitted["radii"][index]
            guard = 64.0 * math.ulp(max(1.0, abs(center), abs(source_point[index])))
            require(abs(source_point[index] - center) <= radius + guard,
                    f"{case} emitted node coordinate is outside its token interval: {node}/{index+1}")

    body_loads = model["physical_body_loads"]
    external = {int(node): _vec(force) for node, force in model["physical_external_loads"].items()}
    native_loads = {int(node): _vec(force) for node, force in model["loads"].items()}
    owned: dict[int, list[float]] = {}
    for body, load_map in body_loads.items():
        require(body in model["physical_body_nodes"], f"{case} body load has unknown owner {body}")
        body_nodes = set(map(int, model["physical_body_nodes"][body]))
        for node_key, force_value in load_map.items():
            node = int(node_key)
            require(node in body_nodes and node not in owned,
                    f"{case} physical body load has invalid/duplicate owner: {node}")
            owned[node] = _vec(force_value)
    require(set(owned) == set(external) == set(native_loads),
            f"{case} body/external/native load node inventories differ")
    for node, force in owned.items():
        _close(force, external[node], f"{case} body/external load {node}", 1e-10)
        _close(force, native_loads[node], f"{case} body/native load {node}", 1e-10)

    cload_nodes = {node for node, _ in deck["cload"]}
    cload_keys = set(deck["cload"])
    source_keys = {
        (node, dof)
        for node, force in native_loads.items()
        for dof in (1, 2, 3)
        if force[dof - 1] != 0.0
    }
    for node, dof in cload_keys | source_keys:
        source_value = native_loads.get(node, [0.0, 0.0, 0.0])[dof - 1]
        emitted = deck["cload"].get((node, dof), {"value": 0.0, "radius": 0.0})
        guard = 64.0 * math.ulp(max(1.0, abs(source_value), abs(emitted["value"])))
        require(abs(source_value - emitted["value"]) <= emitted["radius"] + guard,
                f"{case} emitted CLOAD differs from saved source load: {node}/{dof}")

    for case_record in model["floor_reference_nodes_and_load_map"]:
        node = int(case_record["node"])
        require(node not in cload_nodes, f"{case} selected floor reference has a direct CLOAD: {node}")
    for case_record in model["floor_inactive_scalar_output_nodes"]:
        node = int(case_record["node"])
        require(node not in cload_nodes, f"{case} inactive floor output node has a CLOAD: {node}")

    elements = deck["elements"]
    raw = model["raw_source_carrier_law_inventory_rows"]
    bilateral = {str(row["group"]): row for row in model["springs"]}
    nonlinear = {str(row["source_row_id"]): row for row in model["unilateral_springa_bindings"]}
    require(len(bilateral) == len(model["springs"]), f"{case} duplicate SPRING2 binding")
    require(len(nonlinear) == len(model["unilateral_springa_bindings"]),
            f"{case} duplicate SPRINGA binding")
    for row in raw:
        law, group = row["intended_law"], str(row["group"])
        if law == "bilateral":
            binding = bilateral.get(group)
            require(binding is not None, f"{case} missing source SPRING2 {group}")
            element = int(binding["element"])
            actual = elements.get(element)
            require(actual is not None and actual["type"] == "SPRING2",
                    f"{case} emitted SPRING2 element is missing: {group}")
            require(actual["nodes"] == list(map(int, row["nodes"])),
                    f"{case} emitted SPRING2 node pair differs: {group}")
        elif law in ("compression_only", "tension_only"):
            binding = nonlinear.get(group)
            require(binding is not None, f"{case} missing source SPRINGA {group}")
            owner = row["physical_owner"]
            if owner["first"] in MEMBERS or owner["second"] in MEMBERS:
                require("direct_master_source_coordinate" not in binding,
                        f"{case} unexpected direct-master recovery in center boundary: {group}")
            element = int(binding["source_element"])
            actual = elements.get(element)
            require(actual is not None and actual["type"] == "SPRINGA",
                    f"{case} emitted SPRINGA element is missing: {group}")
            require(actual["nodes"] == list(map(int, binding["springa_nodes"])),
                    f"{case} emitted SPRINGA node pair differs: {group}")
        elif law == FLOOR_TANGENT_LAW:
            require(group not in bilateral and group not in nonlinear,
                    f"{case} released floor tangent is still a native carrier: {group}")
            require(int(row["element"]) not in elements,
                    f"{case} released floor tangent element remains in deck: {group}")
        else:
            require(False, f"{case} has unsupported source carrier law {law!r}")


def _body_datums(model: dict[str, Any]) -> dict[str, list[float]]:
    result = {}
    for body in MEMBERS:
        geometry = model["body_geometry"][body]["geometry_record"]
        start, end = _vec(geometry["start"]), _vec(geometry["end"])
        result[body] = [(a + b) / 2.0 for a, b in zip(start, end, strict=True)]
    return result


def _source_inventory(model: dict[str, Any]) -> tuple[list[dict[str, Any]], dict[str, list[dict[str, Any]]]]:
    raw_inventory = model["raw_source_carrier_law_inventory_rows"]
    floor_rows = [row for row in raw_inventory if row["intended_law"] == FLOOR_TANGENT_LAW]
    floor_index = {str(row["group"]): index for index, row in enumerate(floor_rows)}
    active_floor = set(map(int, model["floor_selected_original_row_indices"]))
    inactive_floor = set(map(int, model["floor_inactive_original_row_indices"]))
    require(active_floor.isdisjoint(inactive_floor)
            and active_floor | inactive_floor == set(range(len(floor_rows))),
            "selected/inactive floor indices do not partition the filtered tangent inventory")
    active_refs = {
        int(row["source_row_original_index"]): row
        for row in model["floor_reference_nodes_and_load_map"]
    }
    inactive_refs = {
        int(row["source_row_original_index"]): row
        for row in model["floor_inactive_scalar_output_nodes"]
    }
    require(set(active_refs) == active_floor, "selected floor reference map differs from selected mask")
    require(set(inactive_refs) == inactive_floor, "inactive floor output map differs from inactive mask")

    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for full_index, raw in enumerate(raw_inventory):
        owner = raw["physical_owner"]
        require(owner["first"] == raw["first_body"] and owner["second"] == raw["second_body"],
                "source carrier owner/body differs")
        if owner["first"] not in MEMBERS and owner["second"] not in MEMBERS:
            continue
        entry = dict(raw)
        entry["_source_inventory_row_index"] = full_index
        if raw["intended_law"] == FLOOR_TANGENT_LAW:
            entry["_source_row_original_index"] = floor_index[str(raw["group"])]
        groups[str(raw["name"])].append(entry)

    require(len(groups) == 212, "center boundary interface-group count changed")
    require(sum(len(rows) for rows in groups.values()) == 250,
            "center boundary scalar-row count changed")
    internal = sum(
        rows[0]["physical_owner"]["first"] in MEMBERS
        and rows[0]["physical_owner"]["second"] in MEMBERS
        for rows in groups.values()
    )
    require(internal == 40 and len(groups) - internal == 172,
            "center boundary internal/external group census changed")
    return raw_inventory, groups


def _scalar_record(raw: dict[str, Any], scalar: float, radius: float) -> dict[str, Any]:
    floor = raw["intended_law"] == FLOOR_TANGENT_LAW
    source_id = (
        f'{raw["floor_normal_gate"]}_friction/local-dof-{int(raw["dof"])}'
        if floor
        else str(raw["group"])
    )
    record = {
        "source_row_id": source_id,
        "source_inventory_row_index": int(raw["_source_inventory_row_index"]),
        "source_connection_name": str(raw["name"]),
        "intended_law": raw["intended_law"],
        "scalar_force_N": scalar,
        "scalar_rounding_radius_N": radius,
    }
    if floor:
        record["source_row_original_index"] = int(raw["_source_row_original_index"])
        record["local_dof"] = int(raw["dof"])
    return record


def _recover_floor_row(
    model: dict[str, Any],
    raw: dict[str, Any],
    state: dict[str, Any],
    factor: float,
) -> tuple[float, float, dict[str, Any]]:
    original = int(raw["_source_row_original_index"])
    owner = raw["physical_owner"]
    dof = int(raw["dof"])
    active = original in set(map(int, model["floor_selected_original_row_indices"]))
    if active:
        reference = next(
            row for row in model["floor_reference_nodes_and_load_map"]
            if int(row["source_row_original_index"]) == original
        )
        require(int(reference["reference_dof"]) == 1, "selected floor output is not scalar DOF 1")
        require(str(reference["source_spring_group"]) == str(raw["group"]),
                "selected floor reference source group differs")
        require(int(reference["source_inventory_row_index"])
                == int(raw["_source_inventory_row_index"]),
                "selected floor full-inventory index differs")
        basis = _vec(reference["owner_tangent_basis_global_xyz"])
        expected_basis = _vec(owner["force_basis"][dof - 1])
        require(_close(basis, expected_basis, "selected floor tangent basis", 1e-12) <= 1e-12,
                "selected floor tangent basis differs")
        node = int(reference["node"])
        require(node in state["rf"], "selected floor reference node is absent from DAT")
        source_correction = float(reference["source_load_correction_N"])
        scalar, scalar_radius = recover_selected_floor_scalar(
            state["rf"][node][0],
            state["rf_radius"][node][0],
            source_correction,
            factor,
        )
        force = [scalar * value for value in basis]
        radius = [scalar_radius * abs(value) for value in basis]
        channel = {
            "name": "exact-floor/" + str(reference["source_row_id"]),
            "source_row_id": str(reference["source_row_id"]),
            "source_inventory_row_index": int(raw["_source_inventory_row_index"]),
            "source_row_original_index": original,
            "source_connection_name": str(raw["name"]),
            "local_dof": dof,
            "first": owner["first"],
            "second": "floor",
            "point": _vec(reference["owner_floorpoint_xyz_mm"]),
            "first_point": _vec(reference["owner_floorpoint_xyz_mm"]),
            "second_point": _vec(reference["owner_floorpoint_xyz_mm"]),
            "force_on_first_xyz_n": force,
            "force_on_second_xyz_n": [-value for value in force],
            "force_rounding_radius_xyz_n": radius,
            "raw_reference_rf_N": state["rf"][node][0],
            "reference_rf_rounding_radius_N": state["rf_radius"][node][0],
            "transferred_source_load_N": source_correction * factor,
            "recovered_physical_tangent_reaction_N": scalar,
            "owner_tangent_basis_global_xyz": basis,
            "owner_tangent_basis_source": "selected floor reference map",
            "numerical_spring_ground_counted": False,
        }
        return scalar, scalar_radius, channel

    output = next(
        row for row in model["floor_inactive_scalar_output_nodes"]
        if int(row["source_row_original_index"]) == original
    )
    node = int(output["node"])
    carryover, carryover_radius = verify_inactive_floor_zero(
        state["rf"], state["rf_radius"], node
    )
    basis = _vec(owner["force_basis"][dof - 1])
    channel = {
        "name": "inactive-floor-zero/"
        + f'{raw["floor_normal_gate"]}_friction/local-dof-{dof}',
        "source_row_id": f'{raw["floor_normal_gate"]}_friction/local-dof-{dof}',
        "source_inventory_row_index": int(raw["_source_inventory_row_index"]),
        "source_row_original_index": original,
        "source_connection_name": str(raw["name"]),
        "local_dof": dof,
        "first": owner["first"],
        "second": "floor",
        "point": _vec(owner["point"]),
        "first_point": _vec(owner["point"]),
        "second_point": _vec(owner["point"]),
        "force_on_first_xyz_n": [0.0, 0.0, 0.0],
        "force_on_second_xyz_n": [0.0, 0.0, 0.0],
        "force_rounding_radius_xyz_n": [0.0, 0.0, 0.0],
        "native_reference_or_tangent_equation_present": False,
        "native_tangent_spring_present": False,
        "isolated_scalar_output_node": node,
        "carryover_rf_N": carryover,
        "carryover_rf_rounding_radius_N": carryover_radius,
        "carryover_rf_interval_contains_zero": True,
        "owner_tangent_basis_global_xyz": basis,
        "owner_tangent_basis_source": (
            "source owner force_basis indexed by released source local DOF"
        ),
    }
    return 0.0, 0.0, channel


def _recover_interface(
    model: dict[str, Any],
    name: str,
    source_rows: list[dict[str, Any]],
    state: dict[str, Any],
    factor: float,
) -> dict[str, Any]:
    owner = source_rows[0]["physical_owner"]
    require(all(row["physical_owner"] == owner for row in source_rows),
            f"source rows under {name} have inconsistent owners")
    scalars: list[dict[str, Any]] = []
    first_vectors: list[list[float]] = []
    first_radii: list[list[float]] = []
    floor_channels_active: list[dict[str, Any]] = []
    floor_channels_inactive: list[dict[str, Any]] = []

    spring2 = {str(row["group"]): row for row in model["springs"]}
    springa = {str(row["source_row_id"]): row for row in model["unilateral_springa_bindings"]}
    for raw in source_rows:
        law, group = raw["intended_law"], str(raw["group"])
        if law == "bilateral":
            binding = spring2[group]
            require(int(binding["dof"]) == int(raw["dof"]), f"{name}/{group} SPRING2 DOF differs")
            scalar, scalar_radius = recover_spring2_scalar(
                state["rf"], state["rf_radius"], list(map(int, binding["nodes"])), int(raw["dof"])
            )
            basis = _vec(owner["force_basis"][int(raw["dof"]) - 1])
            force = [scalar * value for value in basis]
            radius = [scalar_radius * abs(value) for value in basis]
        elif law in ("compression_only", "tension_only"):
            binding = springa[group]
            require(binding.get("physical_owner") == owner, f"{name}/{group} SPRINGA owner differs")
            axis = _vec(binding["numerical_axis_global_xyz"])
            scalar, scalar_radius = recover_springa_scalar(
                state["rf"], state["rf_radius"], list(map(int, binding["springa_nodes"])), axis
            )
            force = [scalar * value for value in axis]
            radius = [scalar_radius * abs(value) for value in axis]
        elif law == FLOOR_TANGENT_LAW:
            scalar, scalar_radius, channel = _recover_floor_row(model, raw, state, factor)
            basis = _vec(channel["owner_tangent_basis_global_xyz"])
            force = [scalar * value for value in basis]
            radius = [scalar_radius * abs(value) for value in basis]
            if channel.get("carryover_rf_interval_contains_zero") is True:
                floor_channels_inactive.append(channel)
            else:
                floor_channels_active.append(channel)
        else:
            raise OracleError(f"{name}/{group} uses unsupported source law {law!r}")

        first_vectors.append(force)
        first_radii.append(radius)
        scalars.append(_scalar_record(raw, scalar, scalar_radius))

    first_force = _sum_vectors(first_vectors)
    first_radius = _sum_vectors(first_radii)
    first_point = _vec(owner.get("first_point", owner["point"]))
    second_point = _vec(owner.get("second_point", owner["point"]))
    second_force = [-value for value in first_force]
    force_action_error = max(
        abs(a + b) for a, b in zip(first_force, second_force, strict=True)
    )
    require(force_action_error == 0.0, f"{name} action/reaction vector differs")
    action = {
        "source_connection_name": name,
        "name": name,
        "connector_name": name,
        "role": owner.get("role"),
        "first": owner["first"],
        "second": owner["second"],
        "point": _vec(owner["point"]),
        "first_point": first_point,
        "second_point": second_point,
        "force_on_first_xyz_n": first_force,
        "force_on_second_xyz_n": second_force,
        "force_rounding_radius_xyz_n": first_radius,
        "source_row_ids": [row["source_row_id"] for row in scalars],
        "source_inventory_rows": scalars,
        "_owner": owner,
    }
    if owner.get("role") == "assumed_no_slip_floor":
        active = bool(floor_channels_active)
        require(active != bool(floor_channels_inactive),
                f"{name} floor tangent has no unique active/released state")
        channels = floor_channels_active or floor_channels_inactive
        channels.sort(key=lambda row: int(row["local_dof"]))
        require([row["local_dof"] for row in channels] == [2, 3],
                f"{name} floor tangent does not contain DOFs 2 and 3")
        action["floor_tangent_state"] = (
            "active_selected_floor_tangent_reaction"
            if active
            else "released_inactive_floor_tangent_zero_action"
        )
        action["source_row_ids"] = [row["source_row_id"] for row in channels]
        action["source_inventory_rows"] = [
            {
                "source_row_id": row["source_row_id"],
                "source_inventory_row_index": row["source_inventory_row_index"],
                "source_connection_name": name,
                "source_row_original_index": row["source_row_original_index"],
                "local_dof": row["local_dof"],
            }
            for row in channels
        ]
        action["exact_floor_tangent_channels"] = channels if active else []
        action["inactive_floor_tangent_zero_channels"] = channels if not active else []
    return action


def _load_actions(model: dict[str, Any], factor: float) -> list[dict[str, Any]]:
    actions = []
    for body in MEMBERS:
        require(body in model["physical_body_loads"], f"missing body-load map for {body}")
        for node_key, source_force in sorted(
            model["physical_body_loads"][body].items(), key=lambda item: int(item[0])
        ):
            node = str(node_key)
            require(node in model["nodes"], f"missing source load coordinate {body}/{node}")
            force = _vec(source_force)
            actions.append(
                {
                    "body": body,
                    "node": node,
                    "point_xyz_mm": _vec(model["nodes"][node]),
                    "unscaled_force_xyz_N": force,
                    "force_xyz_N": [factor * value for value in force],
                    "load_factor": factor,
                    "precision_basis": "saved model nodal load, not a printed RF token",
                }
            )
    return actions


def _member_balances(
    model: dict[str, Any],
    audit_increment: dict[str, Any],
    actions: dict[str, dict[str, Any]],
    loads: list[dict[str, Any]],
) -> tuple[dict[str, Any], dict[str, list[float]]]:
    datums = _body_datums(model)
    loads_by_body: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in loads:
        loads_by_body[row["body"]].append(row)
    result: dict[str, Any] = {}
    precisions: dict[str, list[float]] = {}

    for body in MEMBERS:
        load_force_rows = [row["force_xyz_N"] for row in loads_by_body[body]]
        load_moment_rows = [
            _cross(
                [p - d for p, d in zip(row["point_xyz_mm"], datums[body], strict=True)],
                row["force_xyz_N"],
            )
            for row in loads_by_body[body]
        ]
        external_force = _sum_vectors(load_force_rows)
        external_moment = _sum_vectors(load_moment_rows)
        interface_force_rows: list[list[float]] = []
        interface_moment_rows: list[list[float]] = []
        force_radii: list[list[float]] = []
        moment_radii: list[list[float]] = []
        contributing: list[str] = []
        for name, action in actions.items():
            if action["first"] == body:
                point = action["first_point"]
                force = action["force_on_first_xyz_n"]
            elif action["second"] == body:
                point = action["second_point"]
                force = action["force_on_second_xyz_n"]
            else:
                continue
            arm = [p - d for p, d in zip(point, datums[body], strict=True)]
            interface_force_rows.append(force)
            interface_moment_rows.append(_cross(arm, force))
            radius = action["force_rounding_radius_xyz_n"]
            force_radii.append(radius)
            moment_radii.append(_moment_radius(arm, radius))
            contributing.append(name)

        interface_force = _sum_vectors(interface_force_rows)
        interface_moment = _sum_vectors(interface_moment_rows)
        force_radius = _sum_vectors(force_radii)
        moment_radius = _sum_vectors(moment_radii)
        residual_force = _add(external_force, interface_force)
        residual_moment = _add(external_moment, interface_moment)
        force_excess = [max(0.0, abs(value) - radius)
                        for value, radius in zip(residual_force, force_radius, strict=True)]
        moment_excess = [max(0.0, abs(value) - radius)
                         for value, radius in zip(residual_moment, moment_radius, strict=True)]
        raw_pass = (
            max(map(abs, residual_force)) <= BALANCE_FORCE_TOL_N
            and max(map(abs, residual_moment)) <= BALANCE_MOMENT_TOL_NMM
        )
        interval_pass = (
            max(force_excess) <= BALANCE_FORCE_TOL_N
            and max(moment_excess) <= BALANCE_MOMENT_TOL_NMM
        )
        expected = audit_increment["body_equilibrium"][body]
        _close(datums[body], expected["reference_xyz_mm"], f"{body} source datum", 1e-8)
        _close(residual_force, expected["force_residual_xyz_n"], f"{body} force residual", 1e-8)
        _close(residual_moment, expected["moment_residual_xyz_nmm"], f"{body} moment residual", 1e-6)
        _close(force_radius, expected["force_rounding_radius_xyz_n"], f"{body} force radius", 1e-8)
        _close(moment_radius, expected["moment_rounding_radius_xyz_nmm"], f"{body} moment radius", 1e-6)
        require(raw_pass == expected["printed_resultants_passed"], f"{body} raw balance gate differs")
        require(interval_pass == expected["interval_resultants_passed"],
                f"{body} rounding-interval balance gate differs")
        require(raw_pass and interval_pass, f"{body} source balance audit does not pass")

        result[body] = {
            "datum_global_xyz_mm": datums[body],
            "datum_status": (
                "source descriptor midpoint; moment-reporting reference only, "
                "not a physical cut/support/mass centroid"
            ),
            "external_load_wrench": {
                "force_xyz_n": external_force,
                "moment_xyz_nmm": external_moment,
            },
            "interface_action_wrench": {
                "force_xyz_n": interface_force,
                "moment_xyz_nmm": interface_moment,
            },
            "combined_residual_wrench": {
                "force_xyz_n": residual_force,
                "moment_xyz_nmm": residual_moment,
            },
            "rounding_interval_excess_force_xyz_n": force_excess,
            "rounding_interval_excess_moment_xyz_nmm": moment_excess,
            "raw_balance_passed": raw_pass,
            "rounding_interval_balance_passed": interval_pass,
            "interface_source_connection_names": sorted(contributing),
            "source_force_radius_xyz_N": force_radius,
            "source_moment_radius_xyz_Nmm": moment_radius,
        }
        precisions[body] = force_radius + moment_radius
    return result, precisions


def _state_actions(bundle: dict[str, Any], state: dict[str, Any], index: int) -> dict[str, Any]:
    model, case, deck = bundle["model"], bundle["case"], bundle["deck"]
    time = next(
        time for time, parsed in bundle["native"].items()
        if parsed is state
    )
    factor = time / deck["total_time"]
    require(index < len(FACTORS) and abs(factor - FACTORS[index]) <= 1e-8,
            f"{case} DAT time/factor sequence differs at index {index}")
    action_groups = _source_inventory(model)[1]
    actions = {
        name: _recover_interface(model, name, rows, state, factor)
        for name, rows in action_groups.items()
    }
    require(len(actions) == 212, f"{case} interface-action count changed")
    scalar_count = sum(len(row["source_inventory_rows"]) for row in actions.values())
    require(scalar_count == 250, f"{case} recovered scalar count changed")
    endpoints: list[dict[str, Any]] = []
    internal_wrenches: list[list[float]] = []
    boundary_wrenches: list[list[float]] = []
    for name, action in sorted(actions.items()):
        first_inside = action["first"] in MEMBERS
        second_inside = action["second"] in MEMBERS
        internal = first_inside and second_inside
        pair_actions: list[list[float]] = []
        for side in ("first", "second"):
            body = action[side]
            if body not in MEMBERS:
                continue
            point = action[side + "_point"]
            force = action["force_on_" + side + "_xyz_n"]
            radius = action["force_rounding_radius_xyz_n"]
            datum = _body_datums(model)[body]
            arm = [p - d for p, d in zip(point, datum, strict=True)]
            endpoints.append(
                {
                    "connection_name": name,
                    "body": body,
                    "side": side,
                    "point_xyz_mm": point,
                    "force_xyz_N": force,
                    "force_radius_xyz_N": radius,
                    "moment_about_body_datum_xyz_Nmm": _cross(arm, force),
                    "moment_radius_about_body_datum_xyz_Nmm": _moment_radius(arm, radius),
                    "internal_to_assembly": internal,
                }
            )
            pair_actions.append(_wrench_at_origin(point, force))
        if internal:
            require(
                max(abs(value) for value in _add(
                    action["force_on_first_xyz_n"], action["force_on_second_xyz_n"]
                )) <= 1e-12,
                f"{case}/{name} internal forces do not cancel",
            )
            internal_wrenches.extend(pair_actions)
        else:
            boundary_wrenches.extend(pair_actions)

    require(len(endpoints) == 252, f"{case} target-body endpoint count changed")
    loads = _load_actions(model, factor)
    require(len(loads) == 316, f"{case} target-body body-load count changed")
    balances, _ = _member_balances(model, bundle["audit"]["increments"][index], actions, loads)
    body_load_wrenches = [
        _wrench_at_origin(row["point_xyz_mm"], row["force_xyz_N"]) for row in loads
    ]
    internal_wrench = _wrench_sum(internal_wrenches)
    boundary_wrench = _wrench_sum(boundary_wrenches)
    load_wrench = _wrench_sum(body_load_wrenches)
    combined = _add(_add(internal_wrench, boundary_wrench), load_wrench)
    transported_rows = []
    for body, balance in balances.items():
        residual = balance["combined_residual_wrench"]
        datum = balance["datum_global_xyz_mm"]
        force = residual["force_xyz_n"]
        moment = residual["moment_xyz_nmm"]
        transported_rows.append(force + _add(moment, _cross(datum, force)))
    transported = _wrench_sum(transported_rows)
    _close(combined[:3], transported[:3], f"{case} assembly force transport", 1e-7)
    _close(combined[3:], transported[3:], f"{case} assembly moment transport", 1e-5)
    return {
        "case_id": case,
        "increment_index": index,
        "time": time,
        "load_factor": factor,
        "interface_actions": actions,
        "endpoint_actions": endpoints,
        "body_load_actions": loads,
        "member_balances": balances,
        "internal_interface_count": 40,
        "boundary_interface_count": 172,
        "internal_cancellation_wrench_N_Nmm": internal_wrench,
        "boundary_wrench_about_origin_N_Nmm": boundary_wrench,
        "body_load_wrench_about_origin_N_Nmm": load_wrench,
        "combined_residual_wrench_about_origin_N_Nmm": combined,
        "transported_source_residual_wrench_N_Nmm": transported,
    }


def _state_index(report: dict[str, Any]) -> dict[tuple[str, int], dict[str, Any]]:
    cases = report.get("cases")
    require(isinstance(cases, (dict, list)), "report cases must be an object or list")
    indexed: dict[tuple[str, int], dict[str, Any]] = {}
    state_rows = report.get("states")
    if isinstance(state_rows, list):
        require(all(isinstance(row, dict) for row in state_rows),
                "report state list contains a malformed row")
    else:
        state_rows = []
        if isinstance(cases, dict):
            for case, value in cases.items():
                require(isinstance(value, dict) and isinstance(value.get("states"), list),
                        f"report case {case} has no state list")
                for row in value["states"]:
                    require(row.get("case_id", case) == case,
                            f"report state case identity differs: {case}")
                    state_rows.append(row)
        else:
            for value in cases:
                require(isinstance(value, dict), "report case row is malformed")
                require(isinstance(value.get("states"), list), "report case row has no state list")
                state_rows.extend(value["states"])
    for row in state_rows:
        key = (str(row.get("case_id")), int(row.get("increment_index", -1)))
        require(key not in indexed, f"duplicate report state {key}")
        indexed[key] = row
    require(len(indexed) == 21, f"expected 21 report states, got {len(indexed)}")
    return indexed


def _compare_scalar_refs(
    observed: Any,
    expected: list[dict[str, Any]],
    label: str,
) -> None:
    require(isinstance(observed, list), f"{label} source rows are missing")
    require(len(observed) == len(expected), f"{label} source-row count differs")
    fields = (
        "source_row_id",
        "source_inventory_row_index",
        "source_row_original_index",
        "source_connection_name",
        "intended_law",
        "local_dof",
    )
    for index, (actual, wanted) in enumerate(zip(observed, expected, strict=True)):
        require(isinstance(actual, dict), f"{label} source row {index} is malformed")
        for field in fields:
            if field in wanted:
                require(actual.get(field) == wanted[field],
                        f"{label} source row {index} {field} differs")


def _observed_field(row: dict[str, Any], key: str) -> Any:
    # Frozen common-point records omit endpoint fields. Explicit outer-seat
    # coordinates take precedence and must never be collapsed to that point.
    return row.get(key, row.get("point")) if key in ("first_point", "second_point") else row.get(key)


def _compare_channel_rows(
    observed: Any,
    expected: list[dict[str, Any]],
    label: str,
    maxima: dict[str, float],
) -> None:
    require(isinstance(observed, list) and len(observed) == len(expected),
            f"{label} channel count differs")
    actual_rows = {int(row["local_dof"]): row for row in observed}
    wanted_rows = {int(row["local_dof"]): row for row in expected}
    require(set(actual_rows) == set(wanted_rows), f"{label} channel DOFs differ")
    for dof, wanted in wanted_rows.items():
        actual = actual_rows[dof]
        for key in ("source_row_id", "source_inventory_row_index", "source_row_original_index",
                    "source_connection_name", "local_dof"):
            if key in wanted:
                require(actual.get(key) == wanted[key], f"{label} DOF {dof} {key} differs")
        for key in ("first", "second", "native_reference_or_tangent_equation_present",
                    "native_tangent_spring_present", "carryover_rf_interval_contains_zero"):
            if key in wanted:
                require(actual.get(key) == wanted[key], f"{label} DOF {dof} {key} differs")
        for key, tolerance in (
            ("point", 1e-8),
            ("first_point", 1e-8),
            ("second_point", 1e-8),
            ("force_on_first_xyz_n", 1e-8),
            ("force_on_second_xyz_n", 1e-8),
            ("force_rounding_radius_xyz_n", 1e-9),
            ("owner_tangent_basis_global_xyz", 1e-12),
            ("carryover_rf_N", 1e-9),
            ("carryover_rf_rounding_radius_N", 1e-10),
        ):
            if key in wanted:
                maxima[key] = max(maxima.get(key, 0.0), _close(_observed_field(actual, key), wanted[key],
                                                               f"{label} DOF {dof} {key}", tolerance))
        for key in ("raw_reference_rf_N", "reference_rf_rounding_radius_N",
                    "transferred_source_load_N", "recovered_physical_tangent_reaction_N"):
            if key in wanted:
                delta = abs(float(actual.get(key)) - float(wanted[key]))
                maxima[key] = max(maxima.get(key, 0.0), delta)
                require(delta <= 1e-8, f"{label} DOF {dof} {key} differs by {delta:g}")


def _compare_report_state(
    actual: dict[str, Any],
    expected: dict[str, Any],
    maxima: dict[str, float],
) -> None:
    case, index = expected["case_id"], expected["increment_index"]
    prefix = f"{case}/{index}"
    require(actual.get("case_id") == case and int(actual.get("increment_index", -1)) == index,
            f"{prefix} report state identity differs")
    require(abs(float(actual.get("load_factor", -1.0)) - expected["load_factor"]) <= 1e-10,
            f"{prefix} report load factor differs")

    actual_actions = actual.get("interface_actions")
    expected_actions = expected["interface_actions"]
    require(isinstance(actual_actions, dict) and set(actual_actions) == set(expected_actions),
            f"{prefix} interface-action names differ")
    for name, wanted in expected_actions.items():
        row = actual_actions[name]
        for key in ("first", "second", "role", "floor_tangent_state"):
            if key in wanted:
                require(row.get(key) == wanted[key], f"{prefix}/{name} {key} differs")
        for key, tolerance in (
            ("point", 1e-8),
            ("first_point", 1e-8),
            ("second_point", 1e-8),
            ("force_on_first_xyz_n", 1e-7),
            ("force_on_second_xyz_n", 1e-7),
            ("force_rounding_radius_xyz_n", 1e-9),
        ):
            if key in wanted:
                maxima[key] = max(maxima.get(key, 0.0), _close(
                    _observed_field(row, key), wanted[key], f"{prefix}/{name} {key}", tolerance
                ))
        require(row.get("source_row_ids") == wanted["source_row_ids"],
                f"{prefix}/{name} source row IDs differ")
        _compare_scalar_refs(row.get("source_inventory_rows"),
                             wanted["source_inventory_rows"], f"{prefix}/{name}")
        if wanted.get("floor_tangent_state") == "active_selected_floor_tangent_reaction":
            _compare_channel_rows(row.get("exact_floor_tangent_channels"),
                                  wanted["exact_floor_tangent_channels"],
                                  f"{prefix}/{name} active floor", maxima)
            require(row.get("inactive_floor_tangent_zero_channels") == [],
                    f"{prefix}/{name} has inactive floor channels on an active row")
        elif wanted.get("floor_tangent_state") == "released_inactive_floor_tangent_zero_action":
            _compare_channel_rows(row.get("inactive_floor_tangent_zero_channels"),
                                  wanted["inactive_floor_tangent_zero_channels"],
                                  f"{prefix}/{name} inactive floor", maxima)
            require(row.get("exact_floor_tangent_channels") == [],
                    f"{prefix}/{name} has active floor channels on a released row")

    endpoints_by_key = {
        (row["connection_name"], row["body"], row["side"]): row
        for row in actual.get("endpoint_actions", [])
    }
    require(len(endpoints_by_key) == len(actual.get("endpoint_actions", [])),
            f"{prefix} duplicate report endpoint action")
    expected_endpoints = {
        (row["connection_name"], row["body"], row["side"]): row
        for row in expected["endpoint_actions"]
    }
    require(set(endpoints_by_key) == set(expected_endpoints), f"{prefix} endpoint-action census differs")
    for key, wanted in expected_endpoints.items():
        row = endpoints_by_key[key]
        for field, tolerance in (
            ("point_xyz_mm", 1e-8),
            ("force_xyz_N", 1e-7),
            ("force_radius_xyz_N", 1e-9),
            ("moment_about_body_datum_xyz_Nmm", 1e-6),
            ("moment_radius_about_body_datum_xyz_Nmm", 1e-6),
        ):
            maxima[field] = max(maxima.get(field, 0.0), _close(
                row.get(field), wanted[field], f"{prefix} endpoint {key} {field}", tolerance
            ))
        require(row.get("internal_to_assembly") is wanted["internal_to_assembly"],
                f"{prefix} endpoint {key} internal flag differs")

    loads_by_key = {
        (row["body"], str(row["node"])): row for row in actual.get("body_load_actions", [])
    }
    require(len(loads_by_key) == len(actual.get("body_load_actions", [])),
            f"{prefix} duplicate report body load")
    expected_loads = {(row["body"], str(row["node"])): row for row in expected["body_load_actions"]}
    require(set(loads_by_key) == set(expected_loads), f"{prefix} body-load census differs")
    for key, wanted in expected_loads.items():
        row = loads_by_key[key]
        for field, tolerance in (
            ("point_xyz_mm", 1e-8),
            ("unscaled_force_xyz_N", 1e-10),
            ("force_xyz_N", 1e-10),
        ):
            maxima[field] = max(maxima.get(field, 0.0), _close(
                row.get(field), wanted[field], f"{prefix} body load {key} {field}", tolerance
            ))
        require(row.get("load_factor") == wanted["load_factor"],
                f"{prefix} body load {key} factor differs")

    actual_balances = actual.get("member_balances")
    expected_balances = expected["member_balances"]
    require(isinstance(actual_balances, dict) and set(actual_balances) == set(expected_balances),
            f"{prefix} member-balance body set differs")
    for body, wanted in expected_balances.items():
        row = actual_balances[body]
        require(row.get("raw_balance_passed") is wanted["raw_balance_passed"],
                f"{prefix}/{body} raw balance flag differs")
        require(row.get("rounding_interval_balance_passed")
                is wanted["rounding_interval_balance_passed"],
                f"{prefix}/{body} interval balance flag differs")
        for key in (
            "datum_global_xyz_mm",
            "rounding_interval_excess_force_xyz_n",
            "rounding_interval_excess_moment_xyz_nmm",
            "source_force_radius_xyz_N",
            "source_moment_radius_xyz_Nmm",
        ):
            maxima[key] = max(maxima.get(key, 0.0), _close(
                row.get(key), wanted[key], f"{prefix}/{body} {key}", 1e-6
            ))
        for key in ("external_load_wrench", "interface_action_wrench", "combined_residual_wrench"):
            for component, tolerance in (("force_xyz_n", 1e-8), ("moment_xyz_nmm", 1e-6)):
                maxima[key + "/" + component] = max(
                    maxima.get(key + "/" + component, 0.0),
                    _close(row.get(key, {}).get(component), wanted[key][component],
                           f"{prefix}/{body} {key}/{component}", tolerance),
                )
        require(row.get("interface_source_connection_names")
                == wanted["interface_source_connection_names"],
                f"{prefix}/{body} contributing interface names differ")

    for key, tolerance in (
        ("internal_cancellation_wrench_N_Nmm", 1e-5),
        ("boundary_wrench_about_origin_N_Nmm", 1e-5),
        ("body_load_wrench_about_origin_N_Nmm", 1e-5),
        ("combined_residual_wrench_about_origin_N_Nmm", 1e-5),
        ("transported_source_residual_wrench_N_Nmm", 1e-5),
    ):
        maxima[key] = max(maxima.get(key, 0.0), _close6(
            actual.get(key), expected[key], f"{prefix} {key}", tolerance
        ))


def check_report(report_path: Path) -> dict[str, Any]:
    freeze = _load_freeze()
    report = _read_json(report_path)
    require(report.get("candidate") == CANDIDATE, "boundary report candidate differs")
    require(report.get("geometry_revision_id", report.get("revision")) == REVISION,
            "boundary report geometry revision differs")
    if "freeze_sha256" in report:
        require(report["freeze_sha256"] == FREEZE_SHA256, "boundary report freeze pin differs")
    actual_states = _state_index(report)
    maxima: dict[str, float] = {}
    scalar_count = endpoint_count = load_count = balance_count = 0
    floor_active_channels = floor_inactive_channels = 0
    for case in sorted(freeze["cases"]):
        bundle = _load_bundle(freeze, case)
        require(len(bundle["audit"]["increments"]) == 7, f"{case} all-body audit has wrong state count")
        for index, (time, native_state) in enumerate(bundle["native"].items()):
            expected = _state_actions(bundle, native_state, index)
            audit_increment = bundle["audit"]["increments"][index]
            require(abs(float(audit_increment["load_factor"]) - expected["load_factor"]) <= 1e-8,
                    f"{case}/{index} saved all-body audit factor differs from DAT")
            key = (case, index)
            require(key in actual_states, f"missing boundary report state {key}")
            _compare_report_state(actual_states[key], expected, maxima)
            scalar_count += sum(len(row["source_inventory_rows"])
                                for row in expected["interface_actions"].values())
            endpoint_count += len(expected["endpoint_actions"])
            load_count += len(expected["body_load_actions"])
            balance_count += len(expected["member_balances"])
            floor_active_channels += sum(
                len(row.get("exact_floor_tangent_channels", []))
                for row in expected["interface_actions"].values()
            )
            floor_inactive_channels += sum(
                len(row.get("inactive_floor_tangent_zero_channels", []))
                for row in expected["interface_actions"].values()
            )
    require(scalar_count == 5250, f"checked scalar count differs: {scalar_count}")
    require(endpoint_count == 5292, f"checked endpoint count differs: {endpoint_count}")
    require(load_count == 6636, f"checked body-load count differs: {load_count}")
    require(balance_count == 105, f"checked member-balance count differs: {balance_count}")
    return {
        "schema": "current_center_boundary_raw_dat_oracle/v1",
        "status": "PASS_RAW_DAT_RECONSTRUCTION_ONLY",
        "source_freeze_sha256": FREEZE_SHA256,
        "report_sha256": sha256_file(report_path.resolve()),
        "case_count": 3,
        "state_count": 21,
        "source_scalar_rows_checked": scalar_count,
        "interface_action_records_checked": 4452,
        "target_body_endpoint_records_checked": endpoint_count,
        "body_load_records_checked": load_count,
        "member_balance_records_checked": balance_count,
        "active_floor_tangent_channels_checked": floor_active_channels,
        "released_floor_tangent_channels_checked": floor_inactive_channels,
        "max_differences": dict(sorted(maxima.items())),
        "complete_joint_accepted": False,
        "criterion_dispositions_closed": False,
        "limits": (
            "Independent frozen-source and raw DAT action reconstruction only. "
            "No spring-law acceptance, force allocation, resistance, floor qualification, "
            "joint acceptance or criterion disposition is established."
        ),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", type=Path, required=True, metavar="REPORT")
    args = parser.parse_args(argv)
    try:
        result = check_report(args.check)
    except (OracleError, OSError, KeyError, TypeError, ValueError) as error:
        print(f"raw DAT oracle failed: {error}", file=sys.stderr)
        return 1
    print(json.dumps(result, indent=2, sort_keys=True, allow_nan=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
