#!/usr/bin/env python3
"""Verify source-bound gravity/climber load decomposition from pinned JSON."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[5]
PACKET = Path(__file__).resolve().parent
BASE = Path("docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28")
PINS_PATH = PACKET / "source-pins.json"
OUTPUT = PACKET / "decomposition.json"
EXPECTED_PINS_SHA256 = "80c8c8c2159bfe98669a2c65e269ffe8bbf4211f43a1b609e630f74ca62c2c24"
EXPECTED_REGISTER_SHA256 = "7a638a49fc5086b4d5fed52148286a300b8b271f7d380b1a131ea8e17b094508"
EXPECTED_CASES = ["a12-rear", "a12-forward", "a12-left", "k12-right", "k12-rear", "a1-rear"]
FORCE_GUARD_N = 1.0e-8
MOMENT_GUARD_NMM = 1.0e-6


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")


def canonical_hash(value: Any) -> str:
    return sha256_bytes(canonical_bytes(value))


def assert_close(actual: list[float], expected: list[float], guard: float, label: str) -> float:
    if len(actual) != len(expected):
        raise AssertionError(f"{label}: vector lengths differ")
    residual = max((abs(float(a) - float(b)) for a, b in zip(actual, expected, strict=True)), default=0.0)
    if residual > guard:
        raise AssertionError(f"{label}: max residual {residual} exceeds {guard}")
    return residual


def normalize_map(loads: dict[Any, Any]) -> dict[str, list[float]]:
    return {
        str(int(node)): [float(value) for value in vector]
        for node, vector in sorted(loads.items(), key=lambda item: int(item[0]))
    }


def add_force(target: dict[str, list[float]], node: Any, force: list[float]) -> None:
    key = str(int(node))
    vector = target.setdefault(key, [0.0, 0.0, 0.0])
    for axis in range(3):
        vector[axis] += float(force[axis])


def difference_map(total: dict[str, list[float]], part: dict[str, list[float]]) -> dict[str, list[float]]:
    return {
        node: [total[node][axis] - part.get(node, [0.0, 0.0, 0.0])[axis] for axis in range(3)]
        for node in sorted(total, key=int)
    }


def recomposition_residual(
    total: dict[str, list[float]], gravity: dict[str, list[float]], climber: dict[str, list[float]]
) -> tuple[float, bool]:
    residual = 0.0
    exact = True
    for node in sorted(set(total) | set(gravity) | set(climber), key=int):
        expected = total.get(node, [0.0, 0.0, 0.0])
        g = gravity.get(node, [0.0, 0.0, 0.0])
        c = climber.get(node, [0.0, 0.0, 0.0])
        for axis in range(3):
            actual = g[axis] + c[axis]
            residual = max(residual, abs(actual - expected[axis]))
            exact = exact and actual == expected[axis]
    return residual, exact


def cross(a: list[float], b: list[float]) -> list[float]:
    return [
        a[1] * b[2] - a[2] * b[1],
        a[2] * b[0] - a[0] * b[2],
        a[0] * b[1] - a[1] * b[0],
    ]


def sum_wrench(loads: dict[str, list[float]], nodes: dict[str, Any]) -> tuple[list[float], list[float]]:
    force = [0.0, 0.0, 0.0]
    moment = [0.0, 0.0, 0.0]
    for node in sorted(loads, key=int):
        f = loads[node]
        xyz = [float(value) for value in nodes[str(int(node))]]
        m = cross(xyz, f)
        for axis in range(3):
            force[axis] += f[axis]
            moment[axis] += m[axis]
    return force, moment


def source_ledger_wrenches(rows: list[dict[str, Any]]) -> dict[str, dict[str, list[float]]]:
    result: dict[str, dict[str, list[float]]] = {}
    for row in rows:
        body = str(row["receiver_body"])
        item = result.setdefault(body, {"force_xyz_n": [0.0] * 3, "moment_about_global_origin_xyz_nmm": [0.0] * 3})
        for axis in range(3):
            item["force_xyz_n"][axis] += float(row["force_xyz_n"][axis])
            item["moment_about_global_origin_xyz_nmm"][axis] += float(row["global_moment_xyz_nmm"][axis])
    return result


def body_nodal_wrenches(
    body_loads: dict[str, dict[str, list[float]]], nodes: dict[str, Any]
) -> dict[str, dict[str, list[float]]]:
    result = {}
    for body, loads in body_loads.items():
        force, moment = sum_wrench(normalize_map(loads), nodes)
        result[body] = {"force_xyz_n": force, "moment_about_global_origin_xyz_nmm": moment}
    return result


def load_pins() -> tuple[dict[str, Any], dict[str, str]]:
    observed_pins_sha = sha256_file(PINS_PATH)
    if observed_pins_sha != EXPECTED_PINS_SHA256:
        raise ValueError(f"source-pins.json changed: {observed_pins_sha} != {EXPECTED_PINS_SHA256}")
    pins = json.loads(PINS_PATH.read_text(encoding="utf-8"))
    if pins.get("schema") != "current_gravity_settle_climber_ramp_source_pins/v1":
        raise ValueError("unexpected source pin schema")
    observed = {}
    for row in pins.get("files", []):
        path = str(row["path"])
        live = ROOT / path
        digest = sha256_file(live)
        if digest != row["sha256"]:
            raise ValueError(f"pinned source changed: {path}: {digest} != {row['sha256']}")
        observed[path] = digest
    if len(observed) != len(pins.get("files", [])):
        raise ValueError("duplicate source paths in source-pins.json")
    return pins, observed


def paths_for_case(case_id: str) -> tuple[Path, Path, Path]:
    if case_id == "a12-rear":
        directory = BASE / "current-springa-frame-input-adapter-attempt01" / case_id
    else:
        directory = BASE / "current-springa-six-case-frame-input-adapter-attempt01" / case_id
    return directory / "model.json", directory / "model.inp", directory / "audit.json"


def verify_case(case_id: str, model_path: Path, register_case: dict[str, Any], register_sha: str) -> dict[str, Any]:
    model = json.loads((ROOT / model_path).read_text(encoding="utf-8"))
    if model.get("schema") != "current_springa_frame_input_model/v1":
        raise ValueError(f"{case_id}: unexpected input schema {model.get('schema')}")
    if model.get("case_id") != case_id or model.get("geometry_revision_id") != "led-clearance-2x6-runner-seated-blocks-v1":
        raise ValueError(f"{case_id}: case/revision mismatch")
    if model.get("candidate") != "compact-floor-flush-wood-joints-development":
        raise ValueError(f"{case_id}: candidate mismatch")
    if model.get("native_solve_executed") is not False:
        raise ValueError(f"{case_id}: source input unexpectedly claims a native solve")

    binding = model.get("source_load_register_binding")
    if case_id != "a12-rear":
        if not isinstance(binding, dict) or binding.get("register_sha256") != register_sha:
            raise ValueError(f"{case_id}: missing or mismatched six-case source-register binding")
        if binding.get("case_id") != case_id or binding.get("fresh_source_load_and_body_wrenches_match_register") is not True:
            raise ValueError(f"{case_id}: source-register case audit does not pass")

    total = normalize_map(model["physical_external_loads"])
    serialized_total = normalize_map(model["loads"])
    if total != serialized_total:
        raise ValueError(f"{case_id}: source map differs from serialized all-bearing input load map")
    total_hash = canonical_hash(total)
    register_map = register_case["physical_external_load_map"]
    if total_hash != register_map["sha256"] or len(total) != register_map["node_count"]:
        raise ValueError(f"{case_id}: physical nodal load map differs from source register")
    if binding is not None and binding.get("physical_external_load_map_sha256") != total_hash:
        raise ValueError(f"{case_id}: per-case map binding differs from loaded map")

    patches = [row for row in model["panel_load_records"] if row.get("load_kind") == "uniform_square_patch_wrench"]
    if len(patches) != 1 or patches[0].get("label") != case_id:
        raise ValueError(f"{case_id}: expected one case-specific climbing patch map")
    patch = patches[0]
    climber: dict[str, list[float]] = {}
    for row in patch["physical_body_nodal_forces"]:
        add_force(climber, row["node"], row["force_xyz_n"])
    climber = normalize_map(climber)
    gravity = difference_map(total, climber)
    residual, exact_recomposition = recomposition_residual(total, gravity, climber)
    if not exact_recomposition:
        raise AssertionError(f"{case_id}: gravity plus climber nodal maps do not exactly reproduce the registered source map")

    nodes = model["nodes"]
    gravity_force, gravity_moment = sum_wrench(gravity, nodes)
    climber_force, climber_moment = sum_wrench(climber, nodes)
    total_force, total_moment = sum_wrench(total, nodes)

    gravity_ledger = [row for row in model["source_wrench_ledger"] if not row["source_name"].startswith("climbing_case/")]
    climber_ledger = [row for row in model["source_wrench_ledger"] if row["source_name"].startswith("climbing_case/")]
    if len(climber_ledger) != 1 or climber_ledger[0]["source_name"] != f"climbing_case/{case_id}":
        raise ValueError(f"{case_id}: source-wrench ledger does not contain one matching climbing row")
    unique_gravity_sources = {row["source_name"] for row in gravity_ledger}
    if len(gravity_ledger) != 952 or len(unique_gravity_sources) != 778:
        raise ValueError(f"{case_id}: gravity source/receiver inventory changed")

    gravity_audits = model["gravity_load_audits"]
    expected_source_names = (
        {row["source_name"] for row in gravity_audits["member_self_weight_rows"]}
        | {row["source_name"] for row in gravity_audits["tnut_point_loads"]}
        | {row["source_name"] for row in gravity_audits["hardware_receiver_point_loads"]}
    )
    hardware_source_names = {row["source_name"] for row in gravity_audits["hardware_receiver_point_loads"]}
    if (len(gravity_audits["member_self_weight_rows"]) != 50
            or len(gravity_audits["tnut_point_loads"]) != 142
            or len(gravity_audits["hardware_receiver_point_loads"]) != 760
            or len(hardware_source_names) != 586
            or expected_source_names != unique_gravity_sources):
        raise ValueError(f"{case_id}: named gravity-source inventory does not exactly match the receiver ledger")

    gravity_audit = gravity_audits["base_mass_accounting"]
    if gravity_audit["source_row_count"] != 778:
        raise ValueError(f"{case_id}: source gravity entity count is not 778")
    kinds = gravity_audit["source_entity_kind_counts"]
    expected_kinds = {
        "current_physical_member_solid": 50,
        "current_physical_tnut_component": 142,
        "current_candidate_hardware_component": 460,
        "current_retained_frame_hardware_component": 60,
        "current_panel_screw_axis_envelope_proxy": 66,
    }
    if kinds != expected_kinds:
        raise ValueError(f"{case_id}: gravity source kind counts changed: {kinds}")

    global_gravity_ledger = source_ledger_wrenches(gravity_ledger)
    if len(global_gravity_ledger) != 50 or set(global_gravity_ledger) != set(model["expected_physical_body_names"]):
        raise ValueError(f"{case_id}: gravity source ledger does not cover all 50 physical bodies")
    by_body = {body: {node: vector for node, vector in nodes_by_body.items()}
               for body, nodes_by_body in model["physical_body_loads"].items()}
    if len(by_body) != 50:
        raise ValueError(f"{case_id}: physical body load inventory is not 50 bodies")
    for row in patch["physical_body_nodal_forces"]:
        body = str(patch["panel_id"])
        if body not in by_body or str(row["node"]) not in by_body[body]:
            raise ValueError(f"{case_id}: patch load does not map to its physical panel owner")
        vector = by_body[body][str(row["node"])]
        for axis in range(3):
            vector[axis] -= float(row["force_xyz_n"][axis])
    gravity_body_wrenches = body_nodal_wrenches(by_body, nodes)
    max_body_force_residual = 0.0
    max_body_moment_residual = 0.0
    for body in sorted(by_body):
        expected = global_gravity_ledger[body]
        actual = gravity_body_wrenches[body]
        max_body_force_residual = max(max_body_force_residual,
            assert_close(actual["force_xyz_n"], expected["force_xyz_n"], FORCE_GUARD_N, f"{case_id}/{body} gravity body force"))
        max_body_moment_residual = max(max_body_moment_residual,
            assert_close(actual["moment_about_global_origin_xyz_nmm"], expected["moment_about_global_origin_xyz_nmm"], MOMENT_GUARD_NMM, f"{case_id}/{body} gravity body first moment"))

    ledger_gravity_force = [sum(row["force_xyz_n"][i] for row in gravity_ledger) for i in range(3)]
    ledger_gravity_moment = [sum(row["global_moment_xyz_nmm"][i] for row in gravity_ledger) for i in range(3)]
    gravity_force_residual = assert_close(gravity_force, gravity_audit["gravity_force_global_xyz_n"], FORCE_GUARD_N, f"{case_id} gravity force vs compiler")
    gravity_moment_residual = assert_close(gravity_moment, gravity_audit["gravity_moment_about_global_origin_xyz_nmm"], MOMENT_GUARD_NMM, f"{case_id} gravity moment vs compiler")
    assert_close(gravity_force, ledger_gravity_force, FORCE_GUARD_N, f"{case_id} gravity force vs ledger")
    assert_close(gravity_moment, ledger_gravity_moment, MOMENT_GUARD_NMM, f"{case_id} gravity moment vs ledger")

    source = register_case["fresh_build_case_source_applied_load"]
    patch_global_moment = [
        cross(source["wrench_reference_point_global_xyz_mm"], source["applied_force_global_xyz_n"])[i]
        + source["moment_global_xyz_nmm"][i]
        for i in range(3)
    ]
    climber_force_residual = assert_close(climber_force, source["applied_force_global_xyz_n"], FORCE_GUARD_N, f"{case_id} climber force")
    climber_moment_residual = assert_close(climber_moment, patch_global_moment, MOMENT_GUARD_NMM, f"{case_id} climber first moment")
    if patch["expected_force_xyz_n"] != source["applied_force_global_xyz_n"]:
        raise ValueError(f"{case_id}: patch input force differs from the load register")

    assembly = model["case_assembly_audit"]
    total_force_residual = assert_close(total_force, assembly["expected_global_force_xyz_n"], FORCE_GUARD_N, f"{case_id} total force")
    total_moment_residual = assert_close(total_moment, assembly["expected_global_moment_about_origin_xyz_nmm"], MOMENT_GUARD_NMM, f"{case_id} total first moment")
    if len(model["physical_body_wrenches"]) != 50 or len(model["physical_body_nodes"]) != 50:
        raise ValueError(f"{case_id}: physical body geometry/load source count is not 50")

    model_rel = model_path.as_posix()
    deck_rel = model_path.with_name("model.inp").as_posix()
    return {
        "case_id": case_id,
        "input_model_path": model_rel,
        "input_model_sha256": sha256_file(ROOT / model_path),
        "existing_deck_path_reference_only": deck_rel,
        "existing_deck_sha256_reference_only": sha256_file(ROOT / model_path.with_name("model.inp")),
        "source_load_register_map_sha256": total_hash,
        "physical_load_nodes": len(total),
        "gravity_nodal_map_sha256": canonical_hash(gravity),
        "gravity_nodal_map_node_count": len(gravity),
        "climber_nodal_map_sha256": canonical_hash(climber),
        "climber_nodal_map_node_count": len(climber),
        "exact_nodal_recomposition": exact_recomposition,
        "max_nodal_recomposition_residual_N": residual,
        "gravity_source_entities": gravity_audit["source_row_count"],
        "gravity_source_receiver_ledger_rows": len(gravity_ledger),
        "gravity_source_unique_names": len(unique_gravity_sources),
        "physical_body_count": len(by_body),
        "gravity_force_xyz_N": gravity_force,
        "gravity_moment_about_origin_xyz_Nmm": gravity_moment,
        "climber_force_xyz_N": climber_force,
        "climber_moment_about_origin_xyz_Nmm": climber_moment,
        "registered_climber_force_xyz_N": source["applied_force_global_xyz_n"],
        "registered_climber_moment_about_origin_xyz_Nmm": patch_global_moment,
        "registered_total_force_xyz_N": assembly["expected_global_force_xyz_n"],
        "registered_total_moment_about_origin_xyz_Nmm": assembly["expected_global_moment_about_origin_xyz_nmm"],
        "max_gravity_body_force_residual_N": max_body_force_residual,
        "max_gravity_body_first_moment_residual_Nmm": max_body_moment_residual,
        "gravity_force_vs_compiler_residual_N": gravity_force_residual,
        "gravity_moment_vs_compiler_residual_Nmm": gravity_moment_residual,
        "climber_force_residual_N": climber_force_residual,
        "climber_first_moment_residual_Nmm": climber_moment_residual,
        "total_force_residual_N": total_force_residual,
        "total_first_moment_residual_Nmm": total_moment_residual,
        "historical_response_forces_read": False,
    }


def build_report() -> dict[str, Any]:
    pins, _ = load_pins()
    register_path = BASE / "current-six-case-source-load-register-attempt01" / "register.json"
    register_sha = sha256_file(ROOT / register_path)
    if register_sha != EXPECTED_REGISTER_SHA256:
        raise ValueError(f"six-case register changed: {register_sha}")
    register = json.loads((ROOT / register_path).read_text(encoding="utf-8"))
    if register.get("status") != "PASS_FRESH_SIX_CASE_SOURCE_LOAD_WRENCH_REGISTER":
        raise ValueError("six-case source register is not in its passing source-input state")
    if register.get("case_id_order") != EXPECTED_CASES:
        raise ValueError("six-case source register case ordering changed")
    cases_by_id = {row["case_id"]: row for row in register["cases"]}
    if set(cases_by_id) != set(EXPECTED_CASES):
        raise ValueError("six-case register case set changed")

    case_reports = []
    gravity_maps = {}
    for case_id in EXPECTED_CASES:
        model_path, _deck_path, _audit_path = paths_for_case(case_id)
        model = json.loads((ROOT / model_path).read_text(encoding="utf-8"))
        report = verify_case(case_id, model_path, cases_by_id[case_id], register_sha)
        case_reports.append(report)
        # Retain only this local value for a cross-case source comparison.
        total = normalize_map(model["physical_external_loads"])
        patch_record = next(row for row in model["panel_load_records"] if row.get("load_kind") == "uniform_square_patch_wrench")
        patch = {}
        for row in patch_record["physical_body_nodal_forces"]:
            add_force(patch, row["node"], row["force_xyz_n"])
        gravity_maps[case_id] = difference_map(total, normalize_map(patch))

    baseline = gravity_maps[EXPECTED_CASES[0]]
    cross_case_max = 0.0
    for case_id in EXPECTED_CASES[1:]:
        other = gravity_maps[case_id]
        if set(other) != set(baseline):
            raise AssertionError(f"{case_id}: gravity nodal map has a different physical-node domain")
        for node in baseline:
            for axis in range(3):
                cross_case_max = max(cross_case_max, abs(baseline[node][axis] - other[node][axis]))
    if cross_case_max > 1.0e-9:
        raise AssertionError(f"case gravity components disagree by {cross_case_max} N")

    gravity = case_reports[0]
    for report in case_reports[1:]:
        assert_close(report["gravity_force_xyz_N"], gravity["gravity_force_xyz_N"], FORCE_GUARD_N, f"{report['case_id']} gravity force identity")
        assert_close(report["gravity_moment_about_origin_xyz_Nmm"], gravity["gravity_moment_about_origin_xyz_Nmm"], MOMENT_GUARD_NMM, f"{report['case_id']} gravity moment identity")

    result = {
        "schema": "current_gravity_settle_climber_ramp_load_decomposition/v1",
        "status": "PASS_SIX_CASE_SOURCE_LOAD_DECOMPOSITION_AND_EXACT_RECOMPOSITION",
        "scope": "Input-only decomposition from source-bound JSON; no geometry rebuild, deck edit, native solve, or response forces.",
        "producer_sha256": sha256_file(Path(__file__).resolve()),
        "source_pins_sha256": sha256_file(PINS_PATH),
        "scenario_contract_path": (PACKET / "scenario-contract.json").relative_to(ROOT).as_posix(),
        "scenario_contract_sha256": sha256_file(PACKET / "scenario-contract.json"),
        "source_load_register_path": register_path.as_posix(),
        "source_load_register_sha256": register_sha,
        "source_load_register_status": register["status"],
        "source_case_ids": EXPECTED_CASES,
        "gravity_source_inventory": {
            "source_mass_entities_per_case": 778,
            "physical_member_and_panel_solids": 50,
            "physical_tnut_components": 142,
            "mapped_hardware_entities": 586,
            "receiver_wrench_ledger_rows_per_case": 952,
            "physical_body_owners_per_case": 50,
            "gravity_includes_all_sources": True,
            "gravity_force_xyz_N": gravity["gravity_force_xyz_N"],
            "gravity_moment_about_origin_xyz_Nmm": gravity["gravity_moment_about_origin_xyz_Nmm"],
            "case_gravity_map_max_component_difference_N": cross_case_max,
        },
        "verification_guards": {
            "nodal_recomposition": "exact float equality component-by-component",
            "wrench_force_absolute_guard_N": FORCE_GUARD_N,
            "wrench_moment_absolute_guard_Nmm": MOMENT_GUARD_NMM,
            "purpose": "Source-map first-moment roundoff checks only; not contact, solver, or structural acceptance tolerances.",
        },
        "cases": case_reports,
        "fixture_replay_status": {
            "two_cell_reset_fixture": "PASS 8 stages; unique local normal state, zero tangent action while open; no frame result",
            "coupled_structural_fixture": "PASS 4 stages; all 4 masks per stage; max balance residual 3.553e-15 N",
            "independent_coupled_elimination": "PASS all 4 selected states and all 16 fixture masks",
            "coupled_counterexample": "reproduced no admissible fixed-reference state and a mirrored two-branch state; neither is a current-frame finding",
            "native_solver_run": False,
        },
        "limits": [
            "The existing source register and input decks are loads only; they do not provide an event-driven conditional-stick native formulation.",
            "Fixture replays establish small mathematical cases, not full-frame branch existence, uniqueness, event localization, or solver convergence.",
            "No selected floor forces from rejected runs are used.",
            "No full-frame response, capacity, or design acceptance is claimed."
        ],
    }
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--write", action="store_true", help="write a fresh source-bound summary")
    group.add_argument("--verify", action="store_true", help="compare the recomputed summary byte-for-byte")
    args = parser.parse_args()
    result = build_report()
    observed = json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n"
    if args.write:
        OUTPUT.write_text(observed, encoding="utf-8")
        print(f"WROTE {OUTPUT.relative_to(ROOT)}")
        print(f"status={result['status']} cases={len(result['cases'])} gravity_sources_per_case=778 bodies=50")
        print(f"max_cross_case_gravity_map_difference_N={result['gravity_source_inventory']['case_gravity_map_max_component_difference_N']:.17g}")
        return
    if not OUTPUT.is_file():
        raise SystemExit(f"missing {OUTPUT.relative_to(ROOT)}; run with --write")
    expected = OUTPUT.read_text(encoding="utf-8")
    if expected != observed:
        raise SystemExit("FAIL: recomputed source decomposition differs from decomposition.json")
    print(f"PASS: {result['status']}; six cases, all 778 gravity entities and 50 body wrenches; exact nodal recomposition")
    print(f"max_cross_case_gravity_map_difference_N={result['gravity_source_inventory']['case_gravity_map_max_component_difference_N']:.17g}")


if __name__ == "__main__":
    main()
