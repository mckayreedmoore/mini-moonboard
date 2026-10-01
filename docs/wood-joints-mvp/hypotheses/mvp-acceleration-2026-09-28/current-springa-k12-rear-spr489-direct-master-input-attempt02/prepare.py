#!/usr/bin/env python3
"""Prepare attempt02: SPR489-only direct-master qghost input; never run CCX."""
from __future__ import annotations

import copy
import difflib
import hashlib
import json
import math
import re
from decimal import Decimal
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[5]
BASE = ROOT / "docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28"
HERE = Path(__file__).resolve().parent
SOURCE = BASE / "current-springa-selected-floor-k12-rear-attempt03"
COUPON = BASE / "current-k12-rear-spr489-cascade-trace-attempt01/direct-scalar-coupon"
METHOD02 = BASE / "current-k12-rear-direct-scalar-parent-method-attempt02"
EXPECTED_SOURCE = {
    "model.json": "9591669b74af719e72df2a681504cab4e283d693eaac5e42920558b30773168f",
    "model.inp": "6b630749e918189583147833e3ef94a1338dc5bb28f42171cefc05cb039695e9",
    "model.dat": "29ec3cca415ee8f1ddb6cccd07a70aade816fd4c71eca98a5944d441f6d42f7a",
    "execution.json": "805e2b43da0f612de7801eca6fa4e05c834e90d805ceb12c23a3cf03c72dae71",
    "case-context.json": "1a352178c8fe2ad64681d2f456d9fdf29e67b72d0a1cbce3aa3ed5df21259a93",
    "freeze.json": "f1d9245626d18007e68732fb79f1a0630adc292397d0ba2fd7c2ca17c48b1cfd",
}
EXPECTED_COUPON = {
    "model.inp": "95057c23311105f953a9e99a35ae1e73e76d8c6f3137f464af957ef32e5a489c",
    "model.json": "6fcc8a55afd156c3516146bb6e98aabe4f3d4366647d6e57ea0924703e4e68ff",
}
EXPECTED_REPLAY = {
    "check.py": "fd0865f47da15f88be3ca95a6821e74311b1e88412cffe63a29c7073226d164c",
    "native-output-audit.json": "baab193eea8b1566a4af3afa210bdc0a42a0fcc7630c6fda2ea8f56fd0731611",
}

VARIANT = "spr489_direct_c3d20_master_interpolation/v1"
Q_NODE = 19800
SOURCE_ROW = "SPR489"
SOURCE_INDEX = 488


class InputError(RuntimeError):
    pass


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def digest(value: Any) -> str:
    data = json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)
    return hashlib.sha256(data.encode()).hexdigest()


def write_json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8")


def rel(path: Path) -> str:
    return path.resolve().relative_to(ROOT).as_posix()


def real(value: Decimal | float) -> str:
    token = format(float(value), ".14g")
    if "e" in token.lower():
        mantissa, exponent = re.split("[eE]", token, maxsplit=1)
        if "." not in mantissa:
            mantissa += ".0"
        token = mantissa + "e" + exponent
    elif "." not in token:
        token += ".0"
    if len(token) > 20:
        raise InputError(f"Real token exceeds 20 columns: {token}")
    return token


def parse_equations(lines: list[str]) -> tuple[list[list[list[Decimal | int]]], list[tuple[int, int]]]:
    rows: list[list[list[Decimal | int]]] = []
    spans: list[tuple[int, int]] = []
    i = 0
    while i < len(lines):
        if lines[i].strip().upper() != "*EQUATION":
            i += 1
            continue
        start = i
        i += 1
        while i < len(lines) and not lines[i].strip():
            i += 1
        if i >= len(lines):
            raise InputError("Truncated *EQUATION term count")
        count = int(lines[i].strip())
        i += 1
        tokens: list[str] = []
        while len(tokens) < 3 * count and i < len(lines):
            line = lines[i].strip()
            if line.startswith("*"):
                raise InputError("Truncated *EQUATION data")
            if line:
                tokens.extend(x.strip() for x in line.split(","))
            i += 1
        if len(tokens) != 3 * count:
            raise InputError("Equation term count does not match serialized fields")
        row: list[list[Decimal | int]] = []
        for j in range(0, len(tokens), 3):
            row.append([int(tokens[j]), int(tokens[j + 1]), Decimal(tokens[j + 2].replace("D", "E").replace("d", "e"))])
        rows.append(row)
        spans.append((start, i))
    return rows, spans


def dep_map(rows: list[list[list[Decimal | int]]]) -> dict[tuple[int, int], int]:
    out: dict[tuple[int, int], int] = {}
    for i, row in enumerate(rows):
        key = (int(row[0][0]), int(row[0][1]))
        if key in out:
            raise InputError(f"Duplicate dependent DOF {key}")
        out[key] = i
    return out


def serialize_equation(row: list[list[Decimal | int]]) -> list[str]:
    fields: list[str] = []
    for node, dof, coefficient in row:
        fields.extend([str(int(node)), str(int(dof)), real(coefficient)])
    out = ["*EQUATION", str(len(row))]
    for i in range(0, len(fields), 9):
        out.append(",".join(fields[i:i + 9]))
    return out


def equation_from_card(lines: list[str], spans: list[tuple[int, int]], index: int) -> list[list[list[Decimal | int]]]:
    rows, _ = parse_equations(lines)
    return copy.deepcopy(rows[index])


def row_json(row: list[list[Decimal | int]]) -> list[list[int | float]]:
    return [[int(n), int(d), float(c)] for n, d, c in row]


def equation_meta(dep: tuple[int, int], row: list[list[Decimal | int]]) -> dict[str, Any]:
    return {"dependent_q_dof": [int(dep[0]), int(dep[1])], "terms": row_json(row)}


def fsum_decimal(values: list[Decimal]) -> float:
    return math.fsum(float(x) for x in values)


def cross(a: list[float], b: list[float]) -> list[float]:
    return [a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0]]


def add3(a: list[float], b: list[float]) -> list[float]:
    return [a[i] + b[i] for i in range(3)]


def max_abs(values: list[float]) -> float:
    return max((abs(v) for v in values), default=0.0)


def source_binding(model: dict[str, Any]) -> dict[str, Any]:
    found = [x for x in model["unilateral_springa_bindings"] if x.get("source_row_id") == SOURCE_ROW]
    if len(found) != 1:
        raise InputError(f"Expected one unilateral binding for {SOURCE_ROW}")
    return found[0]


def normalize_row(row: list[list[Decimal | int]]) -> dict[tuple[int, int], Decimal]:
    if row[0][2] == 0:
        raise InputError("Zero dependent coefficient")
    return {(int(n), int(d)): -Decimal(c) / Decimal(row[0][2]) for n, d, c in row[1:]}


def make_source_map(rows: list[list[list[Decimal | int]]], model: dict[str, Any], binding: dict[str, Any]) -> dict[str, Any]:
    by_dep = dep_map(rows)
    interpolation: dict[str, dict[str, Any]] = {}
    side_spec = {
        "first": {"node": 13526, "owner": binding["physical_owner"]["first"], "projection": int(binding["source_projection_nodes"][0])},
        "second": {"node": 13527, "owner": binding["physical_owner"]["second"], "projection": int(binding["source_projection_nodes"][1])},
    }
    for side, spec in side_spec.items():
        yi, zi = by_dep[(spec["node"], 2)], by_dep[(spec["node"], 3)]
        yrow, zrow = rows[yi], rows[zi]
        if len(yrow) != 21 or len(zrow) != 21:
            raise InputError(f"{side} source interpolation is not the pinned 20-master C3D20 row")
        wy, wz = normalize_row(yrow), normalize_row(zrow)
        wy_by_node = {n: w for (n, _d), w in wy.items()}
        wz_by_node = {n: w for (n, _d), w in wz.items()}
        if wy_by_node.keys() != wz_by_node.keys() or any(wy_by_node[n] != wz_by_node[n] for n in wy_by_node):
            raise InputError(f"{side} C3D20 y/z source rows do not share exact scalar weights")
        if any(d != 2 for _, d in wy) or any(d != 3 for _, d in wz):
            raise InputError("Unexpected C3D20 y/z interpolation DOF")
        master_rows = [{"node": n, "weight": float(wy[(n, 2)])} for n, _d, _c in yrow[1:]]
        owner_nodes = set(map(int, model["physical_body_nodes"][spec["owner"]]))
        if not {r["node"] for r in master_rows}.issubset(owner_nodes):
            raise InputError(f"{side} interpolation masters are not owned by {spec['owner']}")
        interpolation[side] = {
            "physical_owner": spec["owner"],
            "projection_node": spec["projection"],
            "c3d20_interpolation_node": spec["node"],
            "source_equation_indices_zero_based": {"global_y": yi, "global_z": zi},
            "source_equations": {"global_y": row_json(yrow), "global_z": row_json(zrow)},
            "master_shape_weights": master_rows,
        }
    point_a, point_b = (int(x) for x in binding["source_projection_nodes"])
    ny_json, nz_json = (Decimal(str(float(x))) for x in binding["physical_owner"]["scalar_normal"][1:])
    ny_deck, nz_deck = Decimal(real(ny_json)), Decimal(real(nz_json))
    if float(binding["physical_owner"]["scalar_normal"][0]) != 0.0:
        raise InputError("This narrow direct-master replacement expects the source SPR489 x normal to be zero")
    # The emitted old point rows must bind the two actual C3D20 interpolation nodes
    # through the preserved source normal; they remain in the deck unchanged.
    for dep, interp_node in ((point_a, 13526), (point_b, 13527)):
        i = by_dep[(dep, 1)]
        row = rows[i]
        expected = [[dep, 1, Decimal(1)], [interp_node, 2, -ny_deck], [interp_node, 3, -nz_deck]]
        if len(row) != 3 or any(row[j][:2] != expected[j][:2] or row[j][2] != expected[j][2] for j in range(3)):
            raise InputError(f"Preserved projection row {dep}:1 differs from source normal/interpolation point")
    owner_point = list(map(float, binding["physical_owner"]["point"]))
    node_xyz = {int(n): list(map(float, xyz)) for n, xyz in model["nodes"].items()}
    point_reconstruction = {}
    for side in ("first", "second"):
        weights = interpolation[side]["master_shape_weights"]
        total = math.fsum(item["weight"] for item in weights)
        reconstructed = [math.fsum(item["weight"] * node_xyz[item["node"]][j] for item in weights) for j in range(3)]
        point_reconstruction[side] = {
            "weight_sum": total,
            "weighted_master_point_global_mm": reconstructed,
            "owner_point_global_mm": owner_point,
            "point_error_xyz_mm": [reconstructed[j] - owner_point[j] for j in range(3)],
        }
    return {
        "source_q_formula": "q_mm = p_second - p_first; p_side = sum_i(w_i * (n_y*u_i,y + n_z*u_i,z))",
        "source_projection_nodes_original_order": [point_a, point_b],
        "physical_owner_axis_global_xyz": list(map(float, binding["physical_owner"]["scalar_normal"])),
        "physical_owner_point_global_mm": owner_point,
        "source_interpolation_sides": interpolation,
        "master_point_reconstruction": point_reconstruction,
        "source_equation_count": len(rows),
    }


def build_component_rows(source_map: dict[str, Any], binding: dict[str, Any]) -> tuple[list[list[Decimal | int]], list[list[Decimal | int]], list[list[Decimal | int]]]:
    axis = [Decimal(str(float(x))) for x in binding["physical_owner"]["scalar_normal"]]
    ny, nz = axis[1], axis[2]
    q_scalar: list[list[Decimal | int]] = [[Q_NODE, 1, Decimal(1)]]
    for side, sign in (("first", Decimal(1)), ("second", Decimal(-1))):
        for item in source_map["source_interpolation_sides"][side]["master_shape_weights"]:
            node = int(item["node"])
            w = Decimal(str(float(item["weight"])))
            q_scalar.extend([[node, 2, sign * ny * w], [node, 3, sign * nz * w]])
    qy: list[list[Decimal | int]] = [[Q_NODE, 2, Decimal(1)]]
    qz: list[list[Decimal | int]] = [[Q_NODE, 3, Decimal(1)]]
    for node, dof, coefficient in q_scalar[1:]:
        qy.append([node, dof, ny * Decimal(coefficient)])
        qz.append([node, dof, nz * Decimal(coefficient)])
    return q_scalar, qy, qz


def coefficient_map(row: list[list[Decimal | int]]) -> dict[tuple[int, int], Decimal]:
    return {(int(n), int(d)): Decimal(c) for n, d, c in row[1:]}


def emit_and_parse_row(row: list[list[Decimal | int]]) -> tuple[list[str], list[list[Decimal | int]]]:
    lines = serialize_equation(row)
    parsed, _ = parse_equations(lines)
    if len(parsed) != 1 or len(parsed[0]) != len(row):
        raise InputError("Direct qghost row failed its own serialization round-trip")
    return lines, parsed[0]


def actual_effective_scalar_map(qy: list[list[Decimal | int]], qz: list[list[Decimal | int]], binding: dict[str, Any]) -> dict[tuple[int, int], Decimal]:
    axis = [Decimal(str(float(x))) for x in binding["physical_owner"]["scalar_normal"]]
    cy, cz = coefficient_map(qy), coefficient_map(qz)
    if cy.keys() != cz.keys():
        raise InputError("Direct Qy/Qz rows do not share the same physical master set")
    return {key: axis[1] * cy[key] + axis[2] * cz[key] for key in cy}


def owner_wrench_from_effective_map(effective: dict[tuple[int, int], Decimal], model: dict[str, Any], binding: dict[str, Any]) -> dict[str, Any]:
    axis = list(map(float, binding["physical_owner"]["scalar_normal"]))
    point = list(map(float, binding["physical_owner"]["point"]))
    coords = {int(n): list(map(float, xyz)) for n, xyz in model["nodes"].items()}
    masters = {int(n) for n, _d in effective}
    owner_first = str(binding["physical_owner"]["first"])
    owner_second = str(binding["physical_owner"]["second"])
    first_nodes = set(map(int, model["physical_body_nodes"][owner_first]))
    second_nodes = set(map(int, model["physical_body_nodes"][owner_second]))
    if not masters.issubset(first_nodes | second_nodes) or masters & first_nodes & second_nodes:
        raise InputError("Effective force map is not split across distinct physical owner node sets")
    unit_force = {"first": [0.0, 0.0, 0.0], "second": [0.0, 0.0, 0.0]}
    unit_moment = {"first": [0.0, 0.0, 0.0], "second": [0.0, 0.0, 0.0]}
    for (node, dof), coefficient in effective.items():
        side = "first" if node in first_nodes else "second"
        force = [0.0, 0.0, 0.0]
        force[dof - 1] = float(coefficient)
        unit_force[side] = add3(unit_force[side], force)
        unit_moment[side] = add3(unit_moment[side], cross(coords[node], force))
    target = {"first": axis, "second": [-x for x in axis]}
    target_m = {side: cross(point, target[side]) for side in ("first", "second")}
    return {
        "interpretation": "unit SPRINGA scalar force; virtual-work transfer from the two direct carrier rows",
        "actual_force_xyz_by_physical_owner_N_per_N": unit_force,
        "target_force_xyz_by_physical_owner_N_per_N": target,
        "force_residual_xyz_by_owner_N_per_N": {s: [unit_force[s][i] - target[s][i] for i in range(3)] for s in target},
        "actual_moment_global_origin_xyz_by_physical_owner_Nmm_per_N": unit_moment,
        "target_moment_global_origin_xyz_by_physical_owner_Nmm_per_N": target_m,
        "moment_residual_xyz_by_owner_Nmm_per_N": {s: [unit_moment[s][i] - target_m[s][i] for i in range(3)] for s in target},
    }


def protected_model_projection(model: dict[str, Any]) -> dict[str, Any]:
    return {k: v for k, v in model.items() if k not in ("equations", "unilateral_springa_bindings", "nonlinear_native_carrier_bindings", "input_method_variant")}


def main() -> None:
    source_model_path, source_deck_path = SOURCE / "model.json", SOURCE / "model.inp"
    for name, expected in EXPECTED_SOURCE.items():
        actual = sha(SOURCE / name)
        if actual != expected:
            raise InputError(f"Frozen K12-rear attempt03 source pin changed for {name}: {actual}")
    for name, expected in EXPECTED_COUPON.items():
        actual = sha(COUPON / name)
        if actual != expected:
            raise InputError(f"Validated direct scalar coupon source pin changed for {name}: {actual}")
    for name, expected in EXPECTED_REPLAY.items():
        path = METHOD02 / name
        actual = sha(path)
        if actual != expected:
            raise InputError(f"Corrected 18-state replay source pin changed for {name}: {actual}")

    original_model = json.loads(source_model_path.read_text(encoding="utf-8"))
    if original_model.get("case_id") != "k12-rear" or original_model.get("frame_ready_for_native_run") is not False:
        raise InputError("Unexpected source case or readiness state")
    if original_model.get("input_adapter_status") != "ASSEMBLED_SELECTED_FLOOR_BRANCH_INPUT_ONLY":
        raise InputError("Unexpected selected-floor source status")
    original_deck = source_deck_path.read_text(encoding="utf-8")
    source_lines = original_deck.splitlines()
    source_rows, source_spans = parse_equations(source_lines)
    if len(source_rows) != len(original_model["equations"]):
        raise InputError("Frozen source model/deck equation counts differ")
    for i, (deck_row, model_row) in enumerate(zip(source_rows, original_model["equations"], strict=True)):
        if len(deck_row) != len(model_row) or any(
            int(x[0]) != int(y[0]) or int(x[1]) != int(y[1]) or abs(float(x[2]) - float(y[2])) > 1e-12
            for x, y in zip(deck_row, model_row, strict=True)
        ):
            raise InputError(f"Frozen model/deck equation mismatch at row {i}")
    source_deps = dep_map(source_rows)
    binding = source_binding(original_model)
    if int(binding["source_inventory_row_index"]) != SOURCE_INDEX or int(binding["source_element"]) != 2392:
        raise InputError("SPR489 source inventory binding changed")
    variant_row_ids = [x["source_row_id"] for x in original_model["unilateral_springa_bindings"] if x.get("qghost_equations_method_variant")]
    if variant_row_ids:
        raise InputError(f"Source unexpectedly already has a direct-master variant: {variant_row_ids}")

    # Direct source coordinate basis: the source C3D20 interpolation equation rows
    # for both owners, followed by the preserved projection-node normal map.
    source_map = make_source_map(source_rows, original_model, binding)
    q_scalar_ideal, qy_ideal, qz_ideal = build_component_rows(source_map, binding)
    _, qy_emitted = emit_and_parse_row(qy_ideal)
    _, qz_emitted = emit_and_parse_row(qz_ideal)
    _, q_scalar_emitted = emit_and_parse_row(q_scalar_ideal)
    qy_index, qz_index = source_deps[(Q_NODE, 2)], source_deps[(Q_NODE, 3)]
    if qy_index == qz_index:
        raise InputError("SPR489 Qy and Qz equation indices collide")
    if len(qy_emitted) != 81 or len(qz_emitted) != 81 or len(q_scalar_emitted) != 81:
        raise InputError("Expected Q component rows and source scalar map to have 80 C3D20 master terms each")

    old_qy, old_qz = copy.deepcopy(source_rows[qy_index]), copy.deepcopy(source_rows[qz_index])
    # Verify the original two-level qghost projection before replacing only its
    # final two equations. The point and C3D20 interpolation rows stay untouched.
    point_a, point_b = map(int, binding["source_projection_nodes"])
    ny = Decimal(str(float(binding["physical_owner"]["scalar_normal"][1])))
    nz = Decimal(str(float(binding["physical_owner"]["scalar_normal"][2])))
    ny_deck, nz_deck = Decimal(real(ny)), Decimal(real(nz))
    expected_old_qy = [[Q_NODE, 2, Decimal(1)], [point_b, 1, -ny_deck], [point_a, 1, ny_deck]]
    expected_old_qz = [[Q_NODE, 3, Decimal(1)], [point_b, 1, -nz_deck], [point_a, 1, nz_deck]]
    if old_qy != expected_old_qy or old_qz != expected_old_qz:
        raise InputError("SPR489 original qghost equations differ from the reviewed source mapping")

    # Replace only qnode DOFs 2 and 3. Keep the projection points, original source
    # interpolation equations, all other MPCs, carrier nodes/axis, and SPRINGA law.
    output_lines = list(source_lines)
    for index, row in sorted(((qy_index, qy_emitted), (qz_index, qz_emitted)), reverse=True):
        start, end = source_spans[index]
        output_lines[start:end] = serialize_equation(row)
    output_deck = "\n".join(output_lines) + ("\n" if original_deck.endswith("\n") else "")
    output_deck_lines = output_deck.splitlines()
    emitted_rows, output_spans = parse_equations(output_deck_lines)
    if len(emitted_rows) != len(source_rows):
        raise InputError("Equation row count changed during direct-master replacement")
    if any(emitted_rows[i] != source_rows[i] for i in range(len(source_rows)) if i not in (qy_index, qz_index)):
        raise InputError("A source *EQUATION row outside SPR489 Qy/Qz changed")
    if emitted_rows[qy_index] != qy_emitted or emitted_rows[qz_index] != qz_emitted:
        raise InputError("Serialized direct-master equation rows differ from the replacement map")
    source_target_lines = {line for start, end in (source_spans[qy_index], source_spans[qz_index]) for line in range(start, end)}
    output_target_lines = {line for start, end in (output_spans[qy_index], output_spans[qz_index]) for line in range(start, end)}
    source_without_target_cards = [line for i, line in enumerate(source_lines) if i not in source_target_lines]
    output_without_target_cards = [line for i, line in enumerate(output_deck_lines) if i not in output_target_lines]
    if source_without_target_cards != output_without_target_cards:
        raise InputError("Deck text outside the two SPR489 qghost cards changed")

    output_model = copy.deepcopy(original_model)
    # Keep the high-precision source model records byte-for-byte in memory for
    # every untouched equation. Only the two replacement rows are represented
    # by their actual serialized direct-master coefficients.
    output_model["equations"] = copy.deepcopy(original_model["equations"])
    output_model["equations"][qy_index] = row_json(emitted_rows[qy_index])
    output_model["equations"][qz_index] = row_json(emitted_rows[qz_index])
    changed_model_equation_indices = [
        i for i, (before, after) in enumerate(zip(original_model["equations"], output_model["equations"], strict=True))
        if before != after
    ]
    if changed_model_equation_indices != sorted([qy_index, qz_index]):
        raise InputError(f"Model JSON equations changed outside the two SPR489 qghost rows: {changed_model_equation_indices[:10]}")
    original_binding = copy.deepcopy(binding)
    direct_q_rows = [
        equation_meta((Q_NODE, 1), source_rows[source_deps[(Q_NODE, 1)]]),
        equation_meta((Q_NODE, 2), emitted_rows[qy_index]),
        equation_meta((Q_NODE, 3), emitted_rows[qz_index]),
    ]
    output_source_map = copy.deepcopy(source_map)
    output_source_map["scalar_equation_terms_serialized"] = row_json(q_scalar_emitted)
    output_source_map["scalar_coordinate_linear_functional"] = [
        {"node": int(n), "dof": int(d), "coefficient_in_equation": float(c)} for n, d, c in q_scalar_emitted[1:]
    ]
    output_source_map["carrier_component_equations"] = {
        "Qy": row_json(emitted_rows[qy_index]),
        "Qz": row_json(emitted_rows[qz_index]),
        "meaning": "Q_y=n_y*q and Q_z=n_z*q; the SPRINGA axis and initial 100 mm span are unchanged",
    }
    output_source_map["source_map_recovery_rule"] = "q_source = -sum(c_i*U_i) from scalar_coordinate_linear_functional; radius = sum(abs(c_i)*U_radius_i)"
    output_source_map["source_projection_ghosts_preserved_as_source_provenance"] = True
    original_qghost = copy.deepcopy(original_binding["qghost_equations"])

    def bind_variant(target: dict[str, Any]) -> None:
        target["qghost_equations_before_direct_master_variant"] = copy.deepcopy(original_qghost)
        target["qghost_equations"] = copy.deepcopy(direct_q_rows)
        target["qghost_equations_method_variant"] = VARIANT
        target["q_endpoint_components_use_projection_ghosts_before_method_variant"] = bool(
            target.get("q_endpoint_components_use_projection_ghosts", True)
        )
        target["q_endpoint_components_use_projection_ghosts"] = False
        target["direct_master_source_coordinate"] = copy.deepcopy(output_source_map)
        target["relative_coordinate_output_evaluation"] = "direct C3D20 master interpolation; source projection nodes are retained as provenance but are not used to recover SPR489 q"

    for b in output_model["unilateral_springa_bindings"]:
        if b.get("source_row_id") == SOURCE_ROW:
            bind_variant(b)
    for b in output_model["nonlinear_native_carrier_bindings"]:
        if b.get("source_row_id") == SOURCE_ROW:
            bind_variant(b)
    output_model["input_method_variant"] = {
        "schema": "current_springa_direct_master_qghost_method_variant/v1",
        "variant_id": VARIANT,
        "scope": "one explicit SPR489 qghost replacement in K12-rear; no other source row or solver method changed",
        "source_row_id": SOURCE_ROW,
        "source_inventory_row_index": SOURCE_INDEX,
        "affected_equation_dependent_dofs": [[Q_NODE, 2], [Q_NODE, 3]],
        "affected_equation_indices_zero_based": [qy_index, qz_index],
        "source_projection_inventory_preserved": True,
        "all_other_equations_preserved": True,
        "carrier_geometry_axis_spring_and_table_preserved": True,
        "frame_ready_for_native_run": False,
        "mechanical_acceptance": False,
        "force_adoption": False,
        "automatic_mask_iteration_authorized": False,
        "direct_master_source_coordinate": copy.deepcopy(output_source_map),
    }

    # Exact method arithmetic from the emitted rows. The virtual-work source
    # action map is n_y*c_Qy + n_z*c_Qz and must reproduce the source-point
    # unit wrench on the two original physical owners.
    effective = actual_effective_scalar_map(emitted_rows[qy_index], emitted_rows[qz_index], binding)
    scalar_map_emitted = coefficient_map(q_scalar_emitted)
    keys = effective.keys() | scalar_map_emitted.keys()
    effective_vs_scalar = {f"{n}:{d}": float(effective.get((n, d), Decimal(0)) - scalar_map_emitted.get((n, d), Decimal(0))) for n, d in keys}
    source_axis = list(map(float, binding["physical_owner"]["scalar_normal"]))
    source_projection_n = [float(-source_rows[source_deps[(point_a, 1)]][1][2]), float(-source_rows[source_deps[(point_a, 1)]][2][2])]
    source_substituted_map: dict[tuple[int, int], Decimal] = {}
    # Expanded original nested source relation, with deck-emitted projection normal
    # and deck-emitted C3D20 rows (the same source values feeding the old cascaded MPC).
    for side, sign in (("first", Decimal(1)), ("second", Decimal(-1))):
        weights = source_map["source_interpolation_sides"][side]["master_shape_weights"]
        for item in weights:
            n = int(item["node"])
            w = Decimal(str(float(item["weight"])))
            source_substituted_map[(n, 2)] = sign * Decimal(str(source_projection_n[0])) * w
            source_substituted_map[(n, 3)] = sign * Decimal(str(source_projection_n[1])) * w
    source_direct_delta = {
        f"{n}:{d}": float(scalar_map_emitted.get((n, d), Decimal(0)) - source_substituted_map.get((n, d), Decimal(0)))
        for n, d in keys | source_substituted_map.keys()
    }
    owner_wrench = owner_wrench_from_effective_map(effective, original_model, binding)
    node_xyz = {int(n): list(map(float, xyz)) for n, xyz in original_model["nodes"].items()}
    interpolation_sums = {side: float(record["weight_sum"]) for side, record in source_map["master_point_reconstruction"].items()}
    point_error = max_abs([
        value for record in source_map["master_point_reconstruction"].values() for value in record["point_error_xyz_mm"]
    ])
    axis_from_carrier = [
        (float(original_model["nodes"][str(Q_NODE)][i]) - float(original_model["nodes"][str(binding["springa_nodes"][1])][i]))
        / float(binding["initial_span_mm"])
        for i in range(3)
    ]
    # A small length/rounding discrepancy is reported, never silently corrected.
    c3d20_rows = [
        (side, mapping["source_equation_indices_zero_based"])
        for side, mapping in output_source_map["source_interpolation_sides"].items()
    ]
    max_component_rounding = max(
        abs(float(Decimal(c) - Decimal(real(Decimal(c)))))
        for row in (qy_ideal, qz_ideal) for _n, _d, c in row[1:]
    )
    component_identities = {
        "effective_scalar_coefficients_vs_serialized_source_scalar_max_abs": max_abs(list(effective_vs_scalar.values())),
        "effective_scalar_map_vs_full_source_projection_substitution_max_abs": max_abs(list(source_direct_delta.values())),
        "full_source_projection_substitution_source_normal_xyz": [0.0, source_projection_n[0], source_projection_n[1]],
        "owner_normal_global_xyz": source_axis,
        "normal_dot_product": math.fsum(x * x for x in source_axis),
        "carrier_axis_from_serialized_nodes_xyz_over_nominal_span": axis_from_carrier,
        "carrier_axis_vs_owner_axis_max_abs": max_abs([axis_from_carrier[i] - source_axis[i] for i in range(3)]),
        "maximum_component_coefficient_14_digit_rounding_abs": max_component_rounding,
        "direct_rows_each_have_terms": [len(emitted_rows[qy_index]), len(emitted_rows[qz_index])],
        "direct_rows_each_use_c3d20_master_dofs": [len(emitted_rows[qy_index]) - 1, len(emitted_rows[qz_index]) - 1],
        "source_master_nodes_by_owner": {
            side: len(output_source_map["source_interpolation_sides"][side]["master_shape_weights"])
            for side in ("first", "second")
        },
        "source_basis_weight_sum_by_owner": interpolation_sums,
        "source_point_reconstruction_max_abs_error_mm": point_error,
    }

    # The base model is immutable apart from the two equation rows, their exact
    # matching carrier metadata, and the explicit method-variant description.
    if protected_model_projection(output_model) != protected_model_projection(original_model):
        raise InputError("Physical source/model fields changed outside the explicit SPR489 method variant")
    if len(output_model["unilateral_springa_bindings"]) != 1292 or len(output_model["nonlinear_native_carrier_bindings"]) != 1292:
        raise InputError("SPRINGA binding counts changed")
    for key in ("nodes", "elements", "loads", "physical_external_loads", "springs", "raw_source_carrier_law_inventory_rows", "physical_body_nodes", "physical_body_elements", "connection_ownership", "physical_body_wrenches", "material_binding", "floor_branch_metadata", "floor_constraint_audit", "floor_selected_branch_constraint_audit"):
        if output_model[key] != original_model[key]:
            raise InputError(f"Source invariant changed: {key}")
    if output_model["floor_branch_metadata"]["selected_cell_count"] != 23 or output_model["floor_branch_metadata"]["inactive_cell_count"] != 77:
        raise InputError("K12-rear selected 23/77 floor proposal changed")
    if output_model["floor_branch_metadata"]["selected_source_tangent_row_count"] != 46 or output_model["floor_branch_metadata"]["inactive_source_tangent_row_count"] != 154:
        raise InputError("K12-rear selected/inactive floor tangent counts changed")
    corner_audit = output_model["corner_demand_contract_audit"]
    if (corner_audit.get("new_block_axis_count") != 92
            or corner_audit.get("retained_original_leg_runner_axis_count") != 12
            or output_model["connection_counts"].get("parametric_screw_axial_ties") != 66):
        raise InputError("Reviewed 92/12/66 source connection-axis register changed")
    if output_model["frame_ready_for_native_run"] is not False or output_model["native_solve_executed"] is not False:
        raise InputError("Input-only packet must not claim native readiness or execution")

    model_path, deck_path = HERE / "model.json", HERE / "model.inp"
    write_json(model_path, output_model)
    deck_path.write_text(output_deck, encoding="utf-8")
    diff = "".join(difflib.unified_diff(
        original_deck.splitlines(keepends=True), output_deck.splitlines(keepends=True),
        fromfile="attempt03/model.inp", tofile="direct-master/model.inp",
    ))
    (HERE / "deck-diff.patch").write_text(diff, encoding="utf-8")

    coupon_model = json.loads((COUPON / "model.json").read_text(encoding="utf-8"))
    coupon_scalar = coupon_model["source_interpolation"]["direct_scalar_equation_terms_serialized"]
    coupon_coeff = {(int(n), int(d)): float(c) for n, d, c in coupon_scalar[1:]}
    emitted_scalar_coeff = {(n, d): float(c) for (n, d), c in scalar_map_emitted.items()}
    coupon_q_map_error = max_abs([emitted_scalar_coeff.get(k, 0.0) - coupon_coeff.get(k, 0.0) for k in set(emitted_scalar_coeff) | set(coupon_coeff)])
    audit = {
        "schema": "current_spr489_direct_master_frame_input_audit/v1",
        "status": "PASS_EXACT_SPR489_DIRECT_MASTER_INPUT_ARITHMETIC_ONLY",
        "scope": "Input method candidate only; no native run, freeze, response export, force adoption, or joint acceptance.",
        "method_variant": VARIANT,
        "case_id": output_model["case_id"],
        "source_model_sha256": sha(source_model_path),
        "source_deck_sha256": sha(source_deck_path),
        "emitted_model_sha256": sha(model_path),
        "emitted_deck_sha256": sha(deck_path),
        "changed_equation_indices_zero_based": [qy_index, qz_index],
        "changed_equation_dependent_dofs": [[Q_NODE, 2], [Q_NODE, 3]],
        "changed_model_json_equation_indices_zero_based": changed_model_equation_indices,
        "all_other_model_json_equation_records_exactly_preserved": all(
            output_model["equations"][i] == original_model["equations"][i]
            for i in range(len(original_model["equations"])) if i not in (qy_index, qz_index)
        ),
        "equation_count_source_and_emitted": [len(source_rows), len(emitted_rows)],
        "changed_deck_cards_only": ["SPR489 qnode 19800 DOF 2", "SPR489 qnode 19800 DOF 3"],
        "all_deck_lines_outside_two_replaced_equation_cards_identical": True,
        "all_equations_outside_two_SPR489_qghost_rows_exactly_unchanged": all(emitted_rows[i] == source_rows[i] for i in range(len(source_rows)) if i not in (qy_index, qz_index)),
        "source_projection_equations_and_nodes_preserved": True,
        "raw_source_inventory_sha256": digest(original_model["raw_source_carrier_law_inventory_rows"]),
        "physical_geometry_sha256": digest({k: original_model[k] for k in ("nodes", "elements", "body_geometry", "physical_body_nodes", "physical_body_elements")}),
        "reviewed_connection_axis_ledger_sha256": digest({k: original_model[k] for k in ("connection_attachment_rows", "connection_counts", "connection_ownership", "connection_scenario", "corner_demand_contract_audit")}),
        "reviewed_axis_counts": {"new_block_bolt_axes": 92, "retained_original_leg_runner_arrangements": 12, "hillman_axes": 66},
        "physical_load_records_sha256": digest({k: original_model[k] for k in ("loads", "physical_external_loads", "physical_body_loads", "physical_body_wrenches", "source_wrench_ledger")}),
        "material_binding_sha256": digest(original_model["material_binding"]),
        "springs_sha256": digest(original_model["springs"]),
        "floor_selected_23_inactive_77_preserved": True,
        "floor_tangent_rows_46_active_154_inert_preserved": True,
        "all_1292_unilateral_laws_stiffnesses_owner_records_and_100mm_carrier_geometries_preserved_except_SPR489_qghost_method_mapping": True,
        "normal_and_numerical_carrier_axis_preserved": True,
        "source_master_interpolation_equation_rows_used": c3d20_rows,
        "candidate_specific_scalar_and_axis_arithmetic": component_identities,
        "direct_scalar_map_matches_validated_known_answer_coupon_max_abs": coupon_q_map_error,
        "unit_owner_wrench_from_emitted_component_rows": owner_wrench,
        "source_map_provenance": output_source_map,
        "strict_existing_auditor_adaptation_needed": {
            "response_auditor_path": rel(BASE / "current-springa-zero-u-token-response-audit-attempt01/stable_response_audit.py"),
            "input_contract_change": "Whitelist only SPR489 variant spr489_direct_c3d20_master_interpolation/v1; verify its exact two serialized 81-term rows against the recorded C3D20 basis and preserve original source projection rows as provenance.",
            "response_recovery_change": "For SPR489 only, derive source_q and source_q_radius from the serialized direct_master_source_coordinate.scalar_coordinate_linear_functional using physical-master U tokens and their existing radii. Leave every carrier geometric-length, actual dd-dd0 table, q-coordinate, action/reaction, RF, floor, force-owner, moment, 1,291 other SPRINGA, and all SPRING2 checks unchanged.",
            "do_not_use_projection_ghost_U_for_SPR489_gate": "The projection ghosts stay in the equation inventory but are not the response scalar authority for this one method variant; retain source_projection_nodes and their original inventory mapping.",
            "parent_input_checker_exception": "Allow only the declared SPR489 qghost equation/method metadata replacement in unilateral_springa_bindings and nonlinear_native_carrier_bindings; compare all remaining fields and all other rows byte-for-byte/numerically exact.",
        },
        "readiness_flags": {"frame_ready_for_native_run": False, "native_solve_executed": False, "force_adoption": False, "mechanical_acceptance": False},
    }
    write_json(HERE / "input-audit.json", audit)

    source_paths = [
        *[SOURCE / name for name in EXPECTED_SOURCE],
        *[COUPON / name for name in EXPECTED_COUPON],
        *[METHOD02 / name for name in EXPECTED_REPLAY],
        METHOD02 / "diagnosis.json",
        SOURCE / "parent-terminal-assessment.json",
        BASE / "current-k12-rear-all-carrier-exception-preflight-attempt01/diagnosis.json",
        BASE / "current-k12-rear-spr489-cascade-trace-attempt01/cascade-trace.json",
        BASE / "current-k12-rear-spr489-cascade-trace-attempt01/source-pins.json",
    ]
    pins = {
        "schema": "current_spr489_direct_master_frame_input_source_pins/v1",
        "scope": "One input-only method variant for source SPR489; no native/freeze/response adoption.",
        "source_files_sha256": {rel(p): sha(p) for p in source_paths},
        "producer_sha256": sha(Path(__file__)),
        "output_files_sha256": {
            "model.json": sha(model_path),
            "model.inp": sha(deck_path),
            "deck-diff.patch": sha(HERE / "deck-diff.patch"),
            "input-audit.json": sha(HERE / "input-audit.json"),
        },
        "exact_replacement": {
            "source_row_id": SOURCE_ROW,
            "source_inventory_row_index": SOURCE_INDEX,
            "dependent_dofs": [[Q_NODE, 2], [Q_NODE, 3]],
            "source_model_path": rel(source_model_path),
            "source_model_sha256": sha(source_model_path),
            "source_deck_path": rel(source_deck_path),
            "source_deck_sha256": sha(source_deck_path),
            "emitted_model_sha256": sha(model_path),
            "emitted_deck_sha256": sha(deck_path),
        },
    }
    write_json(HERE / "source-pins.json", pins)
    readme = f"""# K12-rear SPR489 direct-master input candidate, attempt02

This input-only packet replaces only the two SPR489 q-carrier equations for
node {Q_NODE}, DOFs 2 and 3. It derives the source scalar from the actual
twenty-node C3D20 interpolation rows for the two recorded owners, then maps
that scalar onto the unchanged carrier axis. The original projection points,
their source equations and the complete source inventory remain in the model
as provenance. The physical geometry, all source loads, carrier laws and
stiffnesses, 23/77 floor mask, and all other equations/cards are preserved.

The direct scalar equation is `q = p_second - p_first`, with each `p` the
normal projection of the weighted C3D20 master displacements. The emitted
carrier rows implement `Q_y = n_y*q` and `Q_z = n_z*q`; because the source
normal has `n_x=0` and unit length, the unchanged 100 mm SPRINGA axis gives
the same scalar extension. The actual serialized unit-force transfer from
those two rows is audited against the recorded first-owner `+n` and
second-owner `-n` force and source-point moment in `input-audit.json`.

The same 80-master scalar linear functional appears in the previously
validated direct-scalar known-answer coupon. This packet does not run CCX and
does not adopt forces or qualify the floor branch. The strict existing 711
response method needs the narrow SPR489-only source-coordinate path recorded
in `input-audit.json`: recover `source_q` and its output-token radius from the
direct physical-master functional. Preserve every other DAT, geometric SPRINGA
table, endpoint RF, action/reaction, floor, source-load, owner-wrench and
connector check.

The candidate model remains `frame_ready_for_native_run=false` and has no
mechanical-acceptance or force-adoption claim. See `deck-diff.patch` for the
two exact input-card changes and `source-pins.json` for its frozen sources.
Attempt02 also preserves every untouched high-precision model JSON equation
record exactly; only equation indices {qy_index} and {qz_index} are replaced.
"""
    (HERE / "README.md").write_text(readme, encoding="utf-8")
    # Include the final README in the output pin inventory without making the
    # producer depend on a self-hash.
    pins["output_files_sha256"]["README.md"] = sha(HERE / "README.md")
    write_json(HERE / "source-pins.json", pins)
    print(json.dumps({"status": audit["status"], "model_sha256": sha(model_path), "deck_sha256": sha(deck_path),
                      "audit_sha256": sha(HERE / "input-audit.json"), "source_pins_sha256": sha(HERE / "source-pins.json"),
                      "changed_rows": audit["changed_equation_dependent_dofs"],
                      "unit_owner_wrench": owner_wrench,
                      "coefficient_residuals": component_identities}, indent=2))


if __name__ == "__main__":
    main()
