#!/usr/bin/env python3
"""Export source-bound five-member corner demands from an audited frame response.

This program never launches a solver. Without a verified response-audit JSON it
emits a blocked preflight containing no response forces. A passing export is
only a numerical demand record for later conditional joint checks; it does not
establish resistance, complete-joint acceptance, or climbing/design release.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from collections import defaultdict
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[5]
BASE = Path("docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28")
DEFAULT_MODEL = BASE / "current-springa-frame-a12-rear-attempt01/model.json"
DEFAULT_CONTRACT = BASE / "current-corner-demand-contract-attempt01/contract.json"
DEFAULT_INTERFACE_MAP = BASE / "current-corner-interface-recovery-map-attempt01/interface-map.json"
DEFAULT_CASE_MANIFEST = Path(
    "docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/current-load-cases.json"
)
DEFAULT_OUTPUT = BASE / "current-corner-native-demand-export-attempt01/preflight.json"

SCHEMA = "current_corner_native_demand_report/v1"
RESPONSE_SCHEMA = "current_springa_frame_physical_response_audit/v1"
RESPONSE_AUDITOR = BASE / "current-springa-frame-response-audit-attempt01/response_audit.py"
RESPONSE_AUDITOR_SHA256 = "b20dae471e9826a55c40bbeed028375e6d082913e3f3917665514f2763ddd49c"
CASE_MANIFEST_SHA256 = "9c7c43c51ce635ebfeaeddabdbbe2a0ac80dfd7819ec357662dd132db648b83a"

# These pins preserve the reviewed conditional inputs and helper implementations.
# They do not turn any reference value into an adjusted resistance.
PINNED_EVIDENCE = {
    str(BASE / "current-corner-demand-contract-attempt01/contract.json"):
        "f09d341924b2aa4e50ad8ecea43e4fcd1a36d838c99ab4e0fb85712e7dfd6c74",
    str(DEFAULT_INTERFACE_MAP):
        "c5ce97cbe1fffbb18dfaf1a544fa9a300991b06056b21b37ba3e08b8a1c6aec8",
    str(BASE / "bolt-groups/bolt-groups.json"):
        "4a8b8f78db190d2e9841e5ad266356f0f0c5a402072d371938ad0760da0accb4",
    str(BASE / "current-knee-post-conditional-bolt-screen-attempt01/conditional-screen.json"):
        "adbedaceec692936dcd2b2393c04fc985c5590a1a5a557b74868cee94eb3175c",
    str(BASE / "current-knee-post-group-factor-attempt01/conditional-group-factor.json"):
        "9ea64b4160d95ad97e3cdb745eb7799111e55392ffc099b28c8f17c25b469ba7",
    str(BASE / "current-knee-three-member-transfer-attempt01/calculation.json"):
        "fb7fba30fdcdabf44c90a5ac7cfe167b6a9f659af8543a8070066f15ad45c5b1",
    str(BASE / "current-knee-header-endgrain-screen-attempt01/conditional-screen.json"):
        "2c4e3cac2c1b951ccd99cff69c5678cc605651b752ff5f9f5cc5b2f7ee3eff28",
    str(BASE / "current-corner-local-wood-screen-attempt01/section-screen.json"):
        "22209a82b0bda6dfc5c140ccc4e481717e0e7c71d30a5827271c81ac71070564",
    str(BASE / "current-corner-washer-seat-screen-attempt01/seat-screen.json"):
        "67dda5964a9c2a864cdb5ee0e898bae3c9e6bea212e2eeb71d5b33f765481ef0",
    "fea/dowel_yield.py":
        "d6c318e75c1a720d0b91f810a892e8309ef89735f66f48820ee853b753f8fe45",
    "mini_moonboard/nds_2024_group_action.py":
        "121ec9d5399aa3e856b4038232e6d61c628aac42ce2addf8d1ff7e3a0e4c3df9",
    "mini_moonboard/bolted_wood_wood_double_shear.py":
        "46a7be4202f32bdcb4631c6137574204f64aa44365b582ebe2369319052afcbd",
    "mini_moonboard/bolted_timber_checks.py":
        "a1414547d9eaa3d60e81482b4a2cac2d49e88f31aafa341dca5be9ec8ef4aa13",
    "mini_moonboard/wood_joint_bolt_resistance.py":
        "488e58bbd58fbc2f22af5d4122e734732bae09de79dad71bbf2623eeca60b166",
    "fea/wood_joint_reduced_properties.py":
        "26b6e8bf8800208bfb867439694afa705558ac63ca338778e9210e940a55d9a1",
}

ROOT_GATE_KEYS = (
    "mpc_interval_checks_passed",
    "springa_law_checks_passed",
    "retained_bilateral_checks_passed",
    "normal_positive_all_bearing_branch_passed",
    "raw_body_and_global_balance_passed",
    "rounding_interval_body_and_global_balance_passed",
)
INCREMENT_GATE_KEYS = (
    "mpc_interval_checks_passed",
    "springa_law_checks_passed",
    "retained_bilateral_checks_passed",
    "normal_positive_all_bearing_branch_passed",
    "raw_balance_passed",
    "rounding_interval_balance_passed",
)
BALANCE_FORCE_TOL_N = 0.1
BALANCE_MOMENT_TOL_NMM = 2.0


class ExportBlocked(ValueError):
    def __init__(self, gates: list[str]):
        self.gates = gates
        super().__init__(", ".join(gates))


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text())


def canonical_sha256(value: Any) -> str:
    raw = json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
    return hashlib.sha256(raw).hexdigest()


def normalized_text_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_text().encode("utf-8")).hexdigest()


def close(a: Any, b: Any, tol: float = 1e-8) -> bool:
    if isinstance(a, list) and isinstance(b, list):
        return len(a) == len(b) and all(close(x, y, tol) for x, y in zip(a, b))
    if isinstance(a, (int, float)) and isinstance(b, (int, float)):
        return math.isfinite(float(a)) and math.isfinite(float(b)) and abs(float(a) - float(b)) <= tol
    return a == b


def v3(value: Any) -> list[float]:
    result = [float(x) for x in value]
    if len(result) != 3 or not all(math.isfinite(x) for x in result):
        raise ValueError("Expected a finite three-vector")
    return result


def add(a: list[float], b: list[float]) -> list[float]:
    return [x + y for x, y in zip(a, b)]


def sub(a: list[float], b: list[float]) -> list[float]:
    return [x - y for x, y in zip(a, b)]


def dot(a: list[float], b: list[float]) -> float:
    return sum(x * y for x, y in zip(a, b))


def cross(a: list[float], b: list[float]) -> list[float]:
    return [a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0]]


def cross_interval_radius(r: list[float], radius: list[float]) -> list[float]:
    return [
        abs(r[1]) * radius[2] + abs(r[2]) * radius[1],
        abs(r[2]) * radius[0] + abs(r[0]) * radius[2],
        abs(r[0]) * radius[1] + abs(r[1]) * radius[0],
    ]


def sum_vectors(items: list[list[float]]) -> list[float]:
    result = [0.0, 0.0, 0.0]
    for item in items:
        result = add(result, item)
    return result


def six(force: list[float], moment: list[float]) -> dict[str, list[float]]:
    return {"force_xyz_n": force, "moment_xyz_nmm": moment}


def add_point_action(acc: dict[str, list[float]], datum: list[float], point: list[float], force: list[float]) -> None:
    acc["force"] = add(acc["force"], force)
    acc["moment"] = add(acc["moment"], cross(sub(point, datum), force))


def evidence_pins() -> tuple[dict[str, str], list[str]]:
    observed: dict[str, str] = {}
    failed: list[str] = []
    for rel, expected in PINNED_EVIDENCE.items():
        path = ROOT / rel
        key = f"source_sha256:{rel}"
        if not path.is_file():
            observed[rel] = "missing"
            failed.append(key)
            continue
        actual = sha256(path)
        observed[rel] = actual
        if actual != expected:
            failed.append(key)
    auditor_path = ROOT / RESPONSE_AUDITOR
    auditor_hash = sha256(auditor_path) if auditor_path.is_file() else "missing"
    observed[str(RESPONSE_AUDITOR)] = auditor_hash
    if auditor_hash != RESPONSE_AUDITOR_SHA256:
        failed.append(f"source_sha256:{RESPONSE_AUDITOR}")
    return observed, failed


def adjacent_native_provenance(model_path: Path, response: dict[str, Any] | None = None) -> dict[str, Any]:
    """Bind a response to adjacent frozen input and terminal native-run records."""
    model_path = model_path.resolve()
    run_dir = model_path.parent
    deck_path = run_dir / "model.inp"
    data_path = run_dir / "model.dat"
    freeze_path = run_dir / "freeze.json"
    execution_path = run_dir / "execution.json"
    authorization_path = run_dir / "authorization.json"
    readiness_path = run_dir / "parent-readiness-review.json"
    terminal_path = run_dir / "parent-terminal-assessment.json"
    gates: dict[str, bool] = {}
    observed: dict[str, Any] = {
        "run_directory": str(run_dir),
        "model_json_sha256": sha256(model_path) if model_path.is_file() else None,
        "model_inp_path": str(deck_path),
        "model_dat_path": str(data_path),
        "freeze_json_path": str(freeze_path),
        "execution_json_path": str(execution_path),
    }
    files_exist = all(path.is_file() for path in (deck_path, data_path, freeze_path, execution_path))
    gates["adjacent_model_inp_model_dat_freeze_and_execution_records_exist"] = files_exist
    if not files_exist:
        for key in (
            "model_inp_sha256", "model_dat_sha256", "model_inp_text_sha256", "model_dat_text_sha256",
            "freeze_json_sha256", "execution_json_sha256",
        ):
            observed[key] = None
        gates["freeze_matches_adjacent_model_and_deck"] = False
        gates["execution_output_hashes_match_model_deck_data"] = False
        gates["execution_run_id_matches_adjacent_directory"] = False
        gates["execution_native_run_completed"] = False
        gates["execution_returncode_zero"] = False
        gates["execution_container_terminal"] = False
        gates["authorization_and_parent_readiness_bind_freeze"] = False
        gates["parent_terminal_assessment_allows_corner_demands"] = False
        gates["response_deck_hash_matches_adjacent_model_inp"] = False
        gates["response_data_hash_matches_adjacent_model_dat"] = False
        gates["final_accepted_load_factor_exactly_one"] = False
        return {"gates": gates, "observed": observed}

    model_hash = sha256(model_path)
    deck_hash = sha256(deck_path)
    data_hash = sha256(data_path)
    deck_text_hash = normalized_text_sha256(deck_path)
    data_text_hash = normalized_text_sha256(data_path)
    freeze_hash = sha256(freeze_path)
    execution_hash = sha256(execution_path)
    freeze = load_json(freeze_path)
    execution = load_json(execution_path)
    observed.update({
        "model_inp_sha256": deck_hash,
        "model_dat_sha256": data_hash,
        "model_inp_text_sha256": deck_text_hash,
        "model_dat_text_sha256": data_text_hash,
        "freeze_json_sha256": freeze_hash,
        "execution_json_sha256": execution_hash,
        "execution": {
            "run_id": execution.get("run_id"),
            "native_solve_executed": execution.get("native_solve_executed"),
            "returncode": execution.get("returncode"),
            "container_confirmed_terminal": execution.get("container_confirmed_terminal"),
        },
    })
    frozen_files = freeze.get("files_sha256", {})
    output_files = execution.get("outputs_sha256", {})
    gates["freeze_matches_adjacent_model_and_deck"] = (
        freeze.get("schema") == "wood_joint_reduced_native_freeze/v1"
        and freeze.get("candidate") == "compact-floor-flush-wood-joints-development"
        and freeze.get("geometry_revision_id") == "led-clearance-2x6-runner-seated-blocks-v1"
        and frozen_files.get("model.json") == model_hash
        and frozen_files.get("model.inp") == deck_hash
    )
    gates["execution_output_hashes_match_model_deck_data"] = (
        output_files.get("model.json") == model_hash
        and output_files.get("model.inp") == deck_hash
        and output_files.get("model.dat") == data_hash
    )
    gates["execution_run_id_matches_adjacent_directory"] = execution.get("run_id") == run_dir.name
    gates["execution_native_run_completed"] = execution.get("native_solve_executed") is True
    gates["execution_returncode_zero"] = execution.get("returncode") == 0
    gates["execution_container_terminal"] = execution.get("container_confirmed_terminal") is True

    authorization_ok = False
    if authorization_path.is_file() and readiness_path.is_file():
        authorization = load_json(authorization_path)
        readiness = load_json(readiness_path)
        authorization_ok = (
            authorization.get("run_id") == execution.get("run_id")
            and authorization.get("native_execution_authorized") is True
            and authorization.get("input_freeze_sha256") == freeze_hash
            and authorization.get("parent_readiness") is True
            and authorization.get("independent_review_sha256") == sha256(readiness_path)
            and readiness.get("input_freeze_sha256") == freeze_hash
            and readiness.get("ready_for_scoped_native_run") is True
        )
    gates["authorization_and_parent_readiness_bind_freeze"] = authorization_ok
    observed["authorization_sha256"] = sha256(authorization_path) if authorization_path.is_file() else None
    observed["parent_readiness_review_sha256"] = sha256(readiness_path) if readiness_path.is_file() else None

    terminal_ok = True
    if terminal_path.is_file():
        terminal = load_json(terminal_path)
        terminal_ok = terminal.get("usable_corner_demands") is True
        observed["parent_terminal_assessment"] = {
            "sha256": sha256(terminal_path),
            "status": terminal.get("status"),
            "usable_corner_demands": terminal.get("usable_corner_demands"),
        }
    else:
        observed["parent_terminal_assessment"] = None
    gates["parent_terminal_assessment_allows_corner_demands"] = terminal_ok

    if response is None:
        gates["response_deck_hash_matches_adjacent_model_inp"] = False
        gates["response_data_hash_matches_adjacent_model_dat"] = False
        gates["final_accepted_load_factor_exactly_one"] = False
    else:
        gates["response_deck_hash_matches_adjacent_model_inp"] = response.get("input_deck_sha256") == deck_text_hash
        gates["response_data_hash_matches_adjacent_model_dat"] = response.get("native_data_sha256") == data_text_hash
        increments = response.get("increments", [])
        gates["final_accepted_load_factor_exactly_one"] = (
            isinstance(increments, list) and bool(increments)
            and isinstance(increments[-1].get("load_factor"), (int, float))
            and abs(float(increments[-1]["load_factor"]) - 1.0) <= 1e-8
        )
    return {"gates": gates, "observed": observed}


def validate_case_binding(model: dict[str, Any], manifest: dict[str, Any], case_id: str) -> list[str]:
    failed: list[str] = []
    if model.get("case_id") != case_id or model.get("case_input", {}).get("case_id") != case_id:
        failed.append("authenticated_case_id_matches_model_and_case_input")
        return failed
    cases = [row for row in manifest.get("cases", []) if row.get("case_id") == case_id]
    if len(cases) != 1:
        return ["authenticated_case_id_has_exactly_one_manifest_record"]
    source = model.get("case_input", {}).get("source_applied_load", {})
    record = cases[0]
    expected = {
        "case_id": record.get("case_id"),
        "hold_id": record.get("hold_id"),
        "applied_force_global_xyz_n": record.get("applied_force_global_xyz_n"),
        "force_application_point_global_xyz_mm": record.get("standoff", {}).get("force_application_point_global_xyz_mm"),
        "moment_global_xyz_nmm": record.get("moment_about_panel_midplane_applicationpoint_global_xyz_nmm"),
        "patch_center_global_xyz_mm": record.get("panel_patch", {}).get("center_global_xyz_mm"),
        "patch_size_mm": record.get("panel_patch", {}).get("size_mm"),
        "wrench_reference_point_global_xyz_mm": record.get("applied_wrench", {}).get("reference_point_global_xyz_mm"),
    }
    for key, value in expected.items():
        if value is None or not close(source.get(key), value):
            failed.append(f"case_source_load_binding:{key}")
    if model.get("source_sha256", {}).get(str(DEFAULT_CASE_MANIFEST)) != CASE_MANIFEST_SHA256:
        failed.append("case_manifest_sha256_bound_in_model")
    return failed


def validate_static_inputs(model_path: Path, contract_path: Path, map_path: Path,
                           case_manifest_path: Path) -> dict[str, Any]:
    model = load_json(model_path)
    contract = load_json(contract_path)
    interface_map = load_json(map_path)
    case_manifest = load_json(case_manifest_path)
    gates: dict[str, bool] = {}
    failures: list[str] = []

    expected_header = {
        "schema": "current_springa_frame_input_model/v1",
        "candidate": "compact-floor-flush-wood-joints-development",
        "geometry_revision_id": "led-clearance-2x6-runner-seated-blocks-v1",
        "input_adapter_status": "ASSEMBLED_INPUT_ONLY",
        "input_only": True,
        "native_solve_executed": False,
        "frame_ready_for_native_run": False,
        "legacy_reduced_static_linear_response_schema_compatible": False,
    }
    for key, expected in expected_header.items():
        gates[f"input_model:{key}"] = model.get(key) == expected
    if any(not ok for ok in gates.values()):
        failures.extend(key for key, ok in gates.items() if not ok)

    gates["response_auditor_source_pin"] = (
        (ROOT / RESPONSE_AUDITOR).is_file() and sha256(ROOT / RESPONSE_AUDITOR) == RESPONSE_AUDITOR_SHA256
    )
    if not gates["response_auditor_source_pin"]:
        failures.append(f"source_sha256:{RESPONSE_AUDITOR}")
    gates["case_manifest_source_pin"] = (
        case_manifest_path.resolve() == (ROOT / DEFAULT_CASE_MANIFEST).resolve()
        and sha256(case_manifest_path) == CASE_MANIFEST_SHA256
    )
    if not gates["case_manifest_source_pin"]:
        failures.append("case_manifest_source_pin")

    # The contract and map must be the reviewed records; each contract owner is
    # checked against the exact source-owned carrier row in this case model.
    contract_audit = model.get("corner_demand_contract_audit", {})
    gates["contract_source_pin"] = (
        contract_path.resolve() == (ROOT / DEFAULT_CONTRACT).resolve()
        and sha256(contract_path) == PINNED_EVIDENCE[str(DEFAULT_CONTRACT)]
        and contract.get("schema") == "current_complete_corner_demand_contract/v1"
        and contract_audit.get("contract_sha256") == sha256(contract_path)
        and contract_audit.get("source_input_sha256") == contract.get("source_input_sha256")
        and contract_audit.get("all_contract_owners_match_rebuilt_source") is True
    )
    if not gates["contract_source_pin"]:
        failures.append("contract_source_pin_and_model_contract_audit")
    gates["interface_map_source_pin"] = (
        map_path.resolve() == (ROOT / DEFAULT_INTERFACE_MAP).resolve()
        and sha256(map_path) == PINNED_EVIDENCE[str(DEFAULT_INTERFACE_MAP)]
        and interface_map.get("geometry_revision_id") == contract.get("geometry_revision_id")
        and interface_map.get("source_sha256") == contract.get("source_input_sha256")
    )
    if not gates["interface_map_source_pin"]:
        failures.append("interface_map_source_pin_and_geometry_binding")

    gates["manifest_case_binding"] = not validate_case_binding(model, case_manifest, str(model.get("case_id", "")))
    if not gates["manifest_case_binding"]:
        failures.extend(validate_case_binding(model, case_manifest, str(model.get("case_id", ""))))

    body_names = contract.get("corner_body_names", [])
    map_bodies = interface_map.get("bodies", [])
    datums = interface_map.get("descriptor_midpoint_datums_mm", {})
    gates["five_body_datum_inventory"] = (
        len(body_names) == 5 and set(body_names) == set(map_bodies) == set(datums)
        and all(body in model.get("physical_body_nodes", {}) for body in body_names)
    )
    if not gates["five_body_datum_inventory"]:
        failures.append("five_body_datum_inventory")

    owners = {row["source_connection_name"]: row for row in contract.get("interface_inventory", [])}
    model_owners = model.get("connection_ownership", {})
    owner_mismatches = []
    for name, row in owners.items():
        source_owner = model_owners.get(name)
        if source_owner is None or any(not close(source_owner.get(key), value) for key, value in row["owner"].items()):
            owner_mismatches.append(name)
    gates["all_contract_owner_rows_match_case_input"] = not owner_mismatches
    if owner_mismatches:
        failures.append("all_contract_owner_rows_match_case_input")

    primary = contract.get("primary_new_corner_groups", {})
    expected_totals = {"physical_axes": 6, "lateral_planes": 8, "outer_seat_ties": 6}
    axis_rows = [
        row for row in contract.get("interface_inventory", [])
        if row.get("owner", {}).get("role") == "candidate_bolt_lateral_plane"
        and row.get("owner", {}).get("axis_id") in {
            axis for group in primary.values() for axis in group.get("axis_ids", [])
        }
    ]
    tie_rows = [
        row for row in contract.get("interface_inventory", [])
        if row.get("owner", {}).get("role") == "physical_bolt_outer_seat_tension"
        and row.get("owner", {}).get("axis_id") in {
            axis for group in primary.values() for axis in group.get("axis_ids", [])
        }
    ]
    all_axes = {axis for group in primary.values() for axis in group.get("axis_ids", [])}
    gates["primary_group_physical_counts"] = (
        set(primary) == {"BG001", "BG003", "BG045"}
        and len(all_axes) == expected_totals["physical_axes"]
        and len(axis_rows) == expected_totals["lateral_planes"]
        and len(tie_rows) == expected_totals["outer_seat_ties"]
        and sum(group.get("lateral_plane_count", 0) for group in primary.values()) == expected_totals["lateral_planes"]
        and sum(group.get("outer_seat_tie_count", 0) for group in primary.values()) == expected_totals["outer_seat_ties"]
    )
    if not gates["primary_group_physical_counts"]:
        failures.append("primary_group_physical_counts")
    gates["retained_frame_bolts_separate"] = (
        contract.get("new_block_axis_count") == 92
        and contract.get("retained_original_leg_runner_axis_count") == 12
        and len(contract.get("retained_original_axis_ids", [])) == 12
        and set(contract.get("retained_original_axis_ids", [])).isdisjoint(all_axes)
    )
    if not gates["retained_frame_bolts_separate"]:
        failures.append("retained_frame_bolts_separate")

    observed_pins, pin_failures = evidence_pins()
    gates["conditional_evidence_and_helper_source_pins"] = not pin_failures
    failures.extend(pin_failures)
    if case_manifest.get("candidate") != contract.get("candidate") or case_manifest.get("geometry_revision_id") != contract.get("geometry_revision_id"):
        gates["manifest_candidate_and_revision_match"] = False
        failures.append("manifest_candidate_and_revision_match")
    else:
        gates["manifest_candidate_and_revision_match"] = True

    native_provenance = adjacent_native_provenance(model_path)

    return {
        "model": model,
        "contract": contract,
        "interface_map": interface_map,
        "case_manifest": case_manifest,
        "gates": gates,
        "failed_static_gates": sorted(set(failures)),
        "source_hashes": {
            "model_json": sha256(model_path),
            "contract_json": sha256(contract_path),
            "interface_map_json": sha256(map_path),
            "case_manifest_json": sha256(case_manifest_path),
            "current_knee_joint_check_summary_context_only": sha256(ROOT / BASE / "current-knee-joint-check-summary.md"),
            "response_auditor_py": observed_pins.get(str(RESPONSE_AUDITOR)),
            "pinned_conditional_packets_and_helpers": observed_pins,
            "adjacent_native_records": native_provenance["observed"],
        },
        "native_provenance": native_provenance,
        "paths": {
            "model_json": str(model_path.resolve()),
            "contract_json": str(contract_path.resolve()),
            "interface_map_json": str(map_path.resolve()),
            "case_manifest_json": str(case_manifest_path.resolve()),
        },
    }


def blocked_report(preflight: dict[str, Any], missing: list[str], response_path: Path | None = None) -> dict[str, Any]:
    model = preflight["model"]
    contract = preflight["contract"]
    gates = preflight["gates"]
    return {
        "schema": SCHEMA,
        "status": "BLOCKED_NO_USABLE_CASE_DEMAND",
        "candidate": contract.get("candidate"),
        "geometry_revision_id": contract.get("geometry_revision_id"),
        "case_id": model.get("case_id"),
        "scope": "left outer BG001/BG003/BG045 five-member assembly; one authenticated case per invocation",
        "input_only_exporter": True,
        "native_solve_launched_by_exporter": False,
        "source_response_forces_promoted": False,
        "no_force_rows_emitted": True,
        "actual_case_demand_usable_for_conditional_joint_checks": False,
        "static_preflight_gates": gates,
        "native_execution_preflight_gates": preflight["native_provenance"]["gates"],
        "native_execution_preflight_evidence": preflight["native_provenance"]["observed"],
        "failed_or_missing_gates": sorted(set(
            preflight["failed_static_gates"] + missing + [
                f"native_execution.{key}"
                for key, passed in preflight["native_provenance"]["gates"].items()
                if not passed
            ]
        )),
        "source_hashes": preflight["source_hashes"],
        "source_paths": {
            **preflight["paths"],
            "response_audit_json": str(response_path.resolve()) if response_path and response_path.exists() else None,
        },
        "demand_result_boundary": [
            "A blocked report carries no recovered force or resistance values.",
            "A rejected native diagnostic or FRD file is not an audited response and cannot supply demand rows.",
            "The current a12-rear input is one of six required cases; the remaining cases and sensitivity studies remain outstanding.",
        ],
    }


def check_response_gates(response: dict[str, Any], model: dict[str, Any], model_path: Path,
                         case_id: str, contract: dict[str, Any], native_provenance: dict[str, Any]) -> list[str]:
    failed: list[str] = []
    if response.get("schema") != RESPONSE_SCHEMA:
        failed.append("response.schema=current_springa_frame_physical_response_audit/v1")
    if response.get("status") != "PASS_NUMERICAL_RESPONSE_AUDIT_ONLY":
        failed.append("response.status=PASS_NUMERICAL_RESPONSE_AUDIT_ONLY")
    if response.get("candidate") != contract.get("candidate"):
        failed.append("response.candidate_matches_contract")
    if response.get("geometry_revision_id") != contract.get("geometry_revision_id"):
        failed.append("response.geometry_revision_id_matches_contract")
    if response.get("case_id") != case_id:
        failed.append("response.case_id_matches_authenticated_input_case")
    if response.get("native_output_consumed") is not True or response.get("native_solve_launched_by_postprocessor") is not False:
        failed.append("response.native_output_consumed_by_pinned_auditor")
    if response.get("qualified_for_design") is not False or response.get("joint_demand_accepted") is not False:
        failed.append("response.remains_numerical_only_and_unaccepted")
    if response.get("source_input_model_json_sha256") != sha256(model_path):
        failed.append("response.source_input_model_json_sha256_matches_exact_input_file")
    if response.get("source_model_record_canonical_sha256") != canonical_sha256(model):
        failed.append("response.source_model_record_canonical_sha256_matches_input_record")
    if response.get("source_input_model_json_path") != str(model_path.resolve()):
        failed.append("response.source_input_model_json_path_matches_exact_input_file")
    for key in ("input_deck_sha256", "native_data_sha256"):
        value = response.get(key)
        if not isinstance(value, str) or len(value) != 64 or any(ch not in "0123456789abcdef" for ch in value.lower()):
            failed.append(f"response.{key}_present_as_sha256")
    for key, passed in native_provenance.get("gates", {}).items():
        if passed is not True:
            failed.append(f"native_execution.{key}")
    summary = response.get("recovery_summary", {})
    for key in ROOT_GATE_KEYS:
        if summary.get(key) is not True:
            failed.append(f"response.recovery_summary.{key}")
    increments = response.get("increments")
    if not isinstance(increments, list) or not increments:
        failed.append("response.increments_nonempty")
        return failed
    for index, inc in enumerate(increments):
        prefix = f"response.increments[{index}]"
        for key in INCREMENT_GATE_KEYS:
            if inc.get(key) is not True:
                failed.append(f"{prefix}.{key}")
        if not isinstance(inc.get("load_factor"), (int, float)) or not 0.0 <= float(inc["load_factor"]) <= 1.0 + 1e-8:
            failed.append(f"{prefix}.load_factor_in_single_static_step")
        balance = inc.get("physical_balance", {})
        body_equilibrium = balance.get("body_equilibrium", {})
        for body in contract.get("corner_body_names", []):
            if body not in body_equilibrium:
                failed.append(f"{prefix}.physical_balance.body_equilibrium.{body}")
            else:
                audited_body = body_equilibrium[body]
                for key in ("printed_resultants_passed", "interval_resultants_passed"):
                    if audited_body.get(key) is not True:
                        failed.append(f"{prefix}.physical_balance.body_equilibrium.{body}.{key}")
        global_equilibrium = balance.get("global_equilibrium")
        if not isinstance(global_equilibrium, dict):
            failed.append(f"{prefix}.physical_balance.global_equilibrium")
        else:
            for key in ("printed_resultants_passed", "interval_resultants_passed"):
                if global_equilibrium.get(key) is not True:
                    failed.append(f"{prefix}.physical_balance.global_equilibrium.{key}")
    return failed


def response_interfaces(inc: dict[str, Any], inventory: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    expected = {row["source_connection_name"]: row for row in inventory}
    tangent_names = {
        name for name, row in expected.items()
        if row.get("owner", {}).get("role") == "assumed_no_slip_floor"
    }
    result: dict[str, dict[str, Any]] = {}
    for public_name, force_row in inc.get("physical_connection_forces", {}).items():
        refs = force_row.get("source_inventory_rows", [])
        if not refs:
            continue
        for ref in refs:
            name = ref.get("source_connection_name")
            if name not in expected or name in tangent_names:
                continue
            if name in result:
                if result[name].get("public_connector_name") == public_name:
                    continue
                raise ExportBlocked([f"increment.connector_source_name_unique:{name}"])
            mapped = dict(force_row)
            mapped["public_connector_name"] = public_name
            result[name] = mapped

    floor_channels: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in inc.get("exact_floor_tangent_reactions", []):
        name = row.get("source_connection_name")
        if name in tangent_names:
            floor_channels[str(name)].append(row)
    for name in tangent_names:
        channels = floor_channels.get(name, [])
        if len(channels) != 2:
            raise ExportBlocked([f"increment.exact_floor_tangent_channel_coverage:{name}"])
        owner = expected[name]["owner"]
        basis = [v3(vector) for vector in owner.get("force_basis", [])[1:]]
        observed_basis = [v3(row.get("owner_tangent_basis_global_xyz")) for row in channels]
        if len(basis) != 2 or any(not any(close(candidate, observed) for candidate in basis) for observed in observed_basis):
            raise ExportBlocked([f"increment.exact_floor_tangent_basis_matches_contract:{name}"])
        if any(row.get("first") != owner.get("first") or row.get("second") != owner.get("second")
               or not close(row.get("point"), owner.get("point")) for row in channels):
            raise ExportBlocked([f"increment.exact_floor_tangent_owner_points_match_contract:{name}"])
        result[name] = {
            "name": name,
            "connector_name": name,
            "source_connection_name": name,
            "first": owner["first"],
            "second": owner["second"],
            "point": owner["point"],
            "first_point": owner["point"],
            "second_point": owner["point"],
            "force_on_first_xyz_n": sum_vectors([v3(row["force_on_first_xyz_n"]) for row in channels]),
            "force_on_second_xyz_n": sum_vectors([v3(row["force_on_second_xyz_n"]) for row in channels]),
            "force_rounding_radius_xyz_n": sum_vectors([v3(row["force_rounding_radius_xyz_n"]) for row in channels]),
            "source_inventory_rows": [
                {"source_row_id": row.get("source_row_id"), "source_inventory_row_index": row.get("source_inventory_row_index"),
                 "source_connection_name": name}
                for row in channels
            ],
            "exact_floor_tangent_channels": channels,
        }
    missing = sorted(set(expected) - set(result))
    if missing:
        raise ExportBlocked([f"increment.corner_interface_force_coverage:{name}" for name in missing])
    return result


def validate_response_owner(row: dict[str, Any], contract_row: dict[str, Any], name: str) -> None:
    owner = contract_row["owner"]
    for key in ("first", "second"):
        if row.get(key) != owner.get(key):
            raise ExportBlocked([f"increment.interface_owner_matches_contract:{name}:{key}"])
    first_point = owner.get("first_point", owner.get("point"))
    second_point = owner.get("second_point", owner.get("point"))
    for key, expected in (("first_point", first_point), ("second_point", second_point)):
        observed = row.get(key, row.get("point"))
        if not close(observed, expected):
            raise ExportBlocked([f"increment.interface_owner_matches_contract:{name}:{key}"])
    first_force = v3(row.get("force_on_first_xyz_n"))
    second_force = v3(row.get("force_on_second_xyz_n"))
    if not close(first_force, [-x for x in second_force], 1e-7):
        raise ExportBlocked([f"increment.interface_action_reaction:{name}"])


def action_wrench(force: list[float], point: list[float], datum: list[float]) -> dict[str, list[float]]:
    return six(force, cross(sub(point, datum), force))


def member_balance(model: dict[str, Any], contract: dict[str, Any], interface_map: dict[str, Any],
                   rows: dict[str, dict[str, Any]], scale: float) -> dict[str, Any]:
    datums = interface_map["descriptor_midpoint_datums_mm"]
    nodes = {str(k): v3(v) for k, v in model["nodes"].items()}
    result: dict[str, Any] = {}
    for body in contract["corner_body_names"]:
        datum = v3(datums[body])
        ext_force = [0.0, 0.0, 0.0]
        ext_moment = [0.0, 0.0, 0.0]
        for node, force_source in model.get("physical_body_loads", {}).get(body, {}).items():
            force = [float(scale) * x for x in v3(force_source)]
            if str(node) not in nodes:
                raise ExportBlocked([f"model.physical_body_load_node_present:{body}:{node}"])
            ext_force = add(ext_force, force)
            ext_moment = add(ext_moment, cross(sub(nodes[str(node)], datum), force))
        int_force = [0.0, 0.0, 0.0]
        int_moment = [0.0, 0.0, 0.0]
        radius_force = [0.0, 0.0, 0.0]
        radius_moment = [0.0, 0.0, 0.0]
        contributing: list[str] = []
        for name, row in rows.items():
            first, second = row["first"], row["second"]
            if first == body:
                point = v3(row.get("first_point", row.get("point")))
                force = v3(row["force_on_first_xyz_n"])
            elif second == body:
                point = v3(row.get("second_point", row.get("point")))
                force = v3(row["force_on_second_xyz_n"])
            else:
                continue
            radius = v3(row.get("force_rounding_radius_xyz_n", [0.0, 0.0, 0.0]))
            int_force = add(int_force, force)
            int_moment = add(int_moment, cross(sub(point, datum), force))
            radius_force = add(radius_force, radius)
            radius_moment = add(radius_moment, cross_interval_radius(sub(point, datum), radius))
            contributing.append(name)
        residual_force = add(ext_force, int_force)
        residual_moment = add(ext_moment, int_moment)
        force_interval_excess = [max(0.0, abs(r) - rad) for r, rad in zip(residual_force, radius_force)]
        moment_interval_excess = [max(0.0, abs(r) - rad) for r, rad in zip(residual_moment, radius_moment)]
        raw_pass = all(abs(x) <= BALANCE_FORCE_TOL_N for x in residual_force) and all(
            abs(x) <= BALANCE_MOMENT_TOL_NMM for x in residual_moment
        )
        interval_pass = all(x <= BALANCE_FORCE_TOL_N for x in force_interval_excess) and all(
            x <= BALANCE_MOMENT_TOL_NMM for x in moment_interval_excess
        )
        result[body] = {
            "datum_global_xyz_mm": datum,
            "datum_status": "source descriptor midpoint; moment-reporting reference only, not a physical cut/support/mass centroid",
            "external_load_wrench": six(ext_force, ext_moment),
            "interface_action_wrench": six(int_force, int_moment),
            "combined_residual_wrench": six(residual_force, residual_moment),
            "rounding_interval_excess_force_xyz_n": force_interval_excess,
            "rounding_interval_excess_moment_xyz_nmm": moment_interval_excess,
            "raw_balance_passed": raw_pass,
            "rounding_interval_balance_passed": interval_pass,
            "interface_source_connection_names": sorted(contributing),
        }
    return result


def group_data(contract: dict[str, Any], interface_map: dict[str, Any], bolt_groups: dict[str, Any]) -> dict[str, Any]:
    groups: dict[str, Any] = {}
    all_axes: dict[str, dict[str, Any]] = {}
    for group_row in bolt_groups.get("candidate_groups", []):
        if group_row.get("group_id") in contract["primary_new_corner_groups"]:
            for axis in group_row.get("axes", []):
                all_axes[axis["axis_id"]] = axis
    for group_id, group in contract["primary_new_corner_groups"].items():
        axes = []
        for axis_id in group["axis_ids"]:
            axis = all_axes.get(axis_id)
            if axis is None or not axis.get("shaft_center_global_xyz_mm"):
                raise ExportBlocked([f"source_bolt_group_geometry_axis:{axis_id}"])
            axes.append(axis)
        if len(axes) != 2:
            raise ExportBlocked([f"source_bolt_group_two_physical_axes:{group_id}"])
        datum = [sum(float(axis["shaft_center_global_xyz_mm"][i]) for axis in axes) / 2.0 for i in range(3)]
        groups[group_id] = {
            "axis_ids": group["axis_ids"],
            "source_connection_names": group["source_connection_names"],
            "lateral_plane_count": group["lateral_plane_count"],
            "outer_seat_tie_count": group["outer_seat_tie_count"],
            "physical_bolt_count": len(axes),
            "group_datum_global_xyz_mm": datum,
            "group_datum_basis": "mean of the two source bolt-groups shaft_center_global_xyz_mm records",
            "bolts": [],
        }
        for axis in axes:
            axis_id = axis["axis_id"]
            axis_datum = v3(axis["shaft_center_global_xyz_mm"])
            rows = [row for row in contract["interface_inventory"] if row.get("owner", {}).get("axis_id") == axis_id]
            rows.sort(key=lambda row: row["source_connection_name"])
            groups[group_id]["bolts"].append({
                "axis_id": axis_id,
                "axis_datum_global_xyz_mm": axis_datum,
                "head_to_nut_unit_global_xyz": axis.get("axis_head_to_nut_unit_global_xyz"),
                "continuous_receiver_members": axis.get("receiver_member_ids"),
                "physical_member_wrenches_at_axis_datum": {},
                "actions": [],
                "source_inventory_names": [row["source_connection_name"] for row in rows],
            })
        groups[group_id]["_axes"] = {row["axis_id"]: row for row in groups[group_id]["bolts"]}
    return groups


def conditional_evidence() -> dict[str, Any]:
    def read(path: Path, keys: list[str]) -> dict[str, Any]:
        record = load_json(ROOT / path)
        return {"path": str(path), "sha256": sha256(ROOT / path), "status": record.get("status"),
                "mechanical_acceptance": record.get("mechanical_acceptance", False),
                "preserved_fields": {key: record.get(key) for key in keys},
                "use_limit": "conditional source reference only; no adjusted resistance, combined interaction, or DCR computed here"}
    return {
        "BG001_individual_bolt": read(BASE / "current-knee-post-conditional-bolt-screen-attempt01/conditional-screen.json",
                                      ["conditional_single_bolt_basis", "compatibility_exclusions"]),
        "BG001_group_factor": read(BASE / "current-knee-post-group-factor-attempt01/conditional-group-factor.json",
                                    ["cg_cdelta_only_reference_envelope", "compatibility_exclusions"]),
        "BG003_two_three_member_bolts": read(BASE / "current-knee-three-member-transfer-attempt01/calculation.json",
                                              ["scenarios", "no_capacity_or_acceptance"]),
        "BG045_endgrain": read(BASE / "current-knee-header-endgrain-screen-attempt01/conditional-screen.json",
                                ["rows", "exclusions"]),
        "geometry_only_splitting_and_net_section": read(BASE / "current-corner-local-wood-screen-attempt01/section-screen.json",
                                                         ["candidate_net_section_inputs", "conditional_method_mapping", "not_calculated", "no_capacity_stop"]),
        "washer_seats": read(BASE / "current-corner-washer-seat-screen-attempt01/seat-screen.json",
                              ["axes", "reference_basis", "scope_and_missing_inputs"]),
        "current_joint_check_summary_context_only": {
            "path": str(BASE / "current-knee-joint-check-summary.md"),
            "sha256": sha256(ROOT / BASE / "current-knee-joint-check-summary.md"),
            "use_limit": "context and missing-input record only; no case response demand or acceptance is imported",
        },
        "reviewed_helpers": {
            rel: PINNED_EVIDENCE[rel] for rel in (
                "fea/dowel_yield.py", "mini_moonboard/nds_2024_group_action.py",
                "mini_moonboard/bolted_wood_wood_double_shear.py", "mini_moonboard/bolted_timber_checks.py",
                "mini_moonboard/wood_joint_bolt_resistance.py", "fea/wood_joint_reduced_properties.py",
            )
        },
    }


def build_increment(model: dict[str, Any], contract: dict[str, Any], interface_map: dict[str, Any],
                    increment: dict[str, Any], case_id: str) -> dict[str, Any]:
    rows = response_interfaces(increment, contract["interface_inventory"])
    inventory = {row["source_connection_name"]: row for row in contract["interface_inventory"]}
    for name, row in rows.items():
        validate_response_owner(row, inventory[name], name)

    interfaces = []
    for name, source in inventory.items():
        owner = source["owner"]
        action = rows[name]
        first_force = v3(action["force_on_first_xyz_n"])
        second_force = v3(action["force_on_second_xyz_n"])
        out = {
            "source_connection_name": name,
            "relation": source["relation"],
            "role": owner.get("role"),
            "axis_id": owner.get("axis_id"),
            "first": owner["first"],
            "second": owner["second"],
            "first_point_global_xyz_mm": owner.get("first_point", owner.get("point")),
            "second_point_global_xyz_mm": owner.get("second_point", owner.get("point")),
            "force_on_first_xyz_n": first_force,
            "force_on_second_xyz_n": second_force,
            "first_side_wrench_at_owner_datum": action_wrench(first_force, v3(owner.get("first_point", owner.get("point"))), v3(owner.get("point"))),
            "second_side_wrench_at_owner_datum": action_wrench(second_force, v3(owner.get("second_point", owner.get("point"))), v3(owner.get("point"))),
            "force_rounding_radius_xyz_n": v3(action.get("force_rounding_radius_xyz_n", [0.0, 0.0, 0.0])),
            "source_row_ids": action.get("source_row_ids", []),
            "source_inventory_rows": action.get("source_inventory_rows", []),
        }
        if owner.get("axis") is not None:
            out["signed_axis_force_on_first_n"] = dot(first_force, v3(owner["axis"]
        ))
        if owner.get("force_basis") is not None:
            basis = [v3(vector) for vector in owner["force_basis"]]
            out["force_on_first_local_basis_components_n"] = [dot(vector, first_force) for vector in basis]
        if owner.get("role") == "timber_or_panel_contact":
            normal = v3(owner["scalar_normal"])
            normal_force = dot(first_force, normal)
            normal_radius = dot([abs(x) for x in normal], out["force_rounding_radius_xyz_n"])
            area = float(owner["source_area_mm2"])
            out["contact"] = {
                "source_area_mm2": area,
                "normal_action_on_first_n": normal_force,
                "normal_force_rounding_radius_n": normal_radius,
                "normal_state_from_force_interval": (
                    "compression_resolved" if normal_force - normal_radius > 0.0
                    else "zero_interval_or_open" if abs(normal_force) <= normal_radius
                    else "outside_compression_branch"
                ),
                "modeled_average_pressure_mpa": normal_force / area,
                "pressure_scope": "modeled area average only; not a contact-pressure distribution, wood stress, or resistance",
            }
        if action.get("exact_floor_tangent_channels"):
            out["exact_floor_tangent_channels"] = action["exact_floor_tangent_channels"]
        if owner.get("role") == "assumed_no_slip_floor":
            out["floor_support_assumption"] = "idealized no-slip tangent reaction; no friction property, anchor, or verified floor capacity"
        if owner.get("role") == "non_qualifying_parametric_screw_withdrawal":
            out["qualification_limit"] = "parametric axial carrier only; not a qualifying physical screw/product resistance"
        if owner.get("axis_id") in contract.get("retained_original_axis_ids", []):
            out["resistance_scope"] = "retained original LEG/FLOOR-RUNNER arrangement; kept separate, unchanged resistance not reopened"
        interfaces.append(out)

    balance_rows = member_balance(model, contract, interface_map, rows, float(increment["load_factor"]))
    failed_local = [
        f"corner_member_balance:{body}:{gate}"
        for body, record in balance_rows.items()
        for gate in ("raw_balance_passed", "rounding_interval_balance_passed")
        if record[gate] is not True
    ]
    if failed_local:
        raise ExportBlocked(failed_local)

    contact_groups: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in interfaces:
        if row.get("role") == "timber_or_panel_contact":
            contact_groups[(row["first"], row["second"])].append(row)
    contact_summary = []
    for (first, second), cells in sorted(contact_groups.items()):
        total_area = sum(float(cell["contact"]["source_area_mm2"]) for cell in cells)
        total_normal = sum(float(cell["contact"]["normal_action_on_first_n"]) for cell in cells)
        contact_summary.append({
            "first": first,
            "second": second,
            "contact_cell_count": len(cells),
            "modeled_area_mm2": total_area,
            "summed_normal_action_on_first_n": total_normal,
            "modeled_pair_average_pressure_mpa": total_normal / total_area,
            "source_connection_names": [cell["source_connection_name"] for cell in cells],
            "pressure_scope": "modeled area average only; no local pressure field or capacity implied",
        })

    groups = group_data(contract, interface_map, load_json(ROOT / (BASE / "bolt-groups/bolt-groups.json")))
    source_by_name = {item["source_connection_name"]: item for item in interfaces}
    for group_id, group in groups.items():
        for bolt in group["bolts"]:
            axis_id = bolt["axis_id"]
            axis_datum = bolt["axis_datum_global_xyz_mm"]
            accum: dict[str, dict[str, list[float]]] = {}
            for source in contract["interface_inventory"]:
                if source.get("owner", {}).get("axis_id") != axis_id:
                    continue
                entry = source_by_name[source["source_connection_name"]]
                bolt["actions"].append({
                    "source_connection_name": entry["source_connection_name"],
                    "role": entry["role"],
                    "first": entry["first"],
                    "second": entry["second"],
                    "first_point_global_xyz_mm": entry["first_point_global_xyz_mm"],
                    "second_point_global_xyz_mm": entry["second_point_global_xyz_mm"],
                    "force_on_first_xyz_n": entry["force_on_first_xyz_n"],
                    "force_on_second_xyz_n": entry["force_on_second_xyz_n"],
                })
                for side, body, point_key, force_key in (
                    ("first", entry["first"], "first_point_global_xyz_mm", "force_on_first_xyz_n"),
                    ("second", entry["second"], "second_point_global_xyz_mm", "force_on_second_xyz_n"),
                ):
                    if body == "floor":
                        continue
                    accum.setdefault(body, {"force": [0.0, 0.0, 0.0], "moment": [0.0, 0.0, 0.0]})
                    add_point_action(accum[body], axis_datum, v3(entry[point_key]), v3(entry[force_key]))
            bolt["physical_member_wrenches_at_axis_datum"] = {
                body: six(value["force"], value["moment"]) for body, value in sorted(accum.items())
            }
        # Group wrenches are demand-resultant sums only; no capacity or plane
        # resistance is summed or inferred here.
        group_accum: dict[str, dict[str, list[float]]] = {}
        datum = group["group_datum_global_xyz_mm"]
        for bolt in group["bolts"]:
            for source_name in bolt["source_inventory_names"]:
                entry = source_by_name[source_name]
                for body, point_key, force_key in (
                    (entry["first"], "first_point_global_xyz_mm", "force_on_first_xyz_n"),
                    (entry["second"], "second_point_global_xyz_mm", "force_on_second_xyz_n"),
                ):
                    if body == "floor":
                        continue
                    group_accum.setdefault(body, {"force": [0.0, 0.0, 0.0], "moment": [0.0, 0.0, 0.0]})
                    add_point_action(group_accum[body], datum, v3(entry[point_key]), v3(entry[force_key]))
        group["wrench_at_group_datum_by_member"] = {
            body: six(value["force"], value["moment"]) for body, value in sorted(group_accum.items())
        }
        del group["_axes"]

    tie_by_axis = {
        row["owner"]["axis_id"]: source_by_name[row["source_connection_name"]]
        for row in contract["interface_inventory"]
        if row.get("owner", {}).get("role") == "physical_bolt_outer_seat_tension"
        and row.get("owner", {}).get("axis_id") in {axis for group in contract["primary_new_corner_groups"].values() for axis in group["axis_ids"]}
    }
    washer_screen = load_json(ROOT / (BASE / "current-corner-washer-seat-screen-attempt01/seat-screen.json"))
    washer_by_axis = {row["axis_id"]: row for row in washer_screen.get("axes", [])}
    washer_seats = []
    for axis_id, tie in sorted(tie_by_axis.items()):
        screen_axis = washer_by_axis.get(axis_id)
        if not screen_axis:
            raise ExportBlocked([f"washer_seat_source_axis:{axis_id}"])
        owner = next(row["owner"] for row in contract["interface_inventory"] if row["source_connection_name"] == tie["source_connection_name"])
        tension = float(tie["signed_axis_force_on_first_n"])
        coefficient = float(screen_axis["one_N_full_annulus_average_pressure_MPa"])
        for seat in screen_axis.get("outer_seats", []):
            member = seat["outer_receiver_member_id"]
            side = "first" if member == owner["first"] else "second" if member == owner["second"] else None
            if side is None:
                raise ExportBlocked([f"washer_seat_member_matches_physical_tie:{axis_id}:{member}"])
            tie_point = owner.get(f"{side}_point", owner.get("point"))
            if not close(seat.get("seat_point_xyz_mm"), tie_point):
                raise ExportBlocked([f"washer_seat_point_matches_source_tie:{axis_id}:{member}"])
            washer_seats.append({
                "axis_id": axis_id,
                "physical_member": member,
                "seat_role": seat["seat_role"],
                "seat_point_global_xyz_mm": seat["seat_point_xyz_mm"],
                "seat_force_on_member_xyz_n": tie[f"force_on_{side}_xyz_n"],
                "signed_outer_seat_tie_action_n": tension,
                "modeled_outer_washer_annular_area_mm2": screen_axis["modeled_outer_washer_annular_area_mm2"],
                "conditional_full_annulus_uniform_average_pressure_mpa": tension * coefficient,
                "conditional_fc_perp_reference_n": seat.get("ideal_dfl2_fc_perp_reference_N"),
                "conditional_fc_perp_reference_status": seat.get("ideal_dfl2_fc_perp_reference_status"),
                "support_area_status": seat.get("effective_area_status"),
                "limitations": screen_axis.get("limits", []),
            })

    return {
        "time": increment.get("time"),
        "load_factor": increment["load_factor"],
        "response_audit_gates": {key: increment.get(key) for key in INCREMENT_GATE_KEYS},
        "audited_global_equilibrium": increment["physical_balance"]["global_equilibrium"],
        "corner_five_body_balance": balance_rows,
        "all_five_corner_bodies_raw_and_interval_balance_passed": True,
        "primary_physical_bolt_groups": groups,
        "all_corner_interfaces": interfaces,
        "member_contact_bearing": {
            "contact_cells": [row for row in interfaces if row.get("role") == "timber_or_panel_contact"],
            "pair_summaries": contact_summary,
            "parallel_routes_preserved": True,
        },
        "outer_washer_seats": washer_seats,
        "retained_original_leg_runner_interfaces": [
            row for row in interfaces if row.get("axis_id") in contract.get("retained_original_axis_ids", [])
        ],
        "retained_original_arrangement_count": contract.get("retained_original_leg_runner_axis_count"),
        "retained_resistance_reopened": False,
        "geometry_only_splitting_net_section_inputs": conditional_evidence()["geometry_only_splitting_and_net_section"],
        "local_complete_corner_inventory_count": len(interfaces),
        "incoming_and_onward_transfers_included": True,
        "floor_tangent_basis_is_unverified_no_slip_assumption": True,
    }


def export_report(preflight: dict[str, Any], response_path: Path) -> dict[str, Any]:
    if preflight["failed_static_gates"]:
        raise ExportBlocked(preflight["failed_static_gates"])
    response = load_json(response_path)
    model = preflight["model"]
    contract = preflight["contract"]
    case_id = str(model["case_id"])
    native_provenance = adjacent_native_provenance(Path(preflight["paths"]["model_json"]), response)
    gates = check_response_gates(response, model, Path(preflight["paths"]["model_json"]), case_id, contract,
                                 native_provenance)
    if gates:
        raise ExportBlocked(gates)

    increments = []
    for inc in response["increments"]:
        try:
            increments.append(build_increment(model, contract, preflight["interface_map"], inc, case_id))
        except ExportBlocked:
            raise
        except (KeyError, TypeError, ValueError, OverflowError) as error:
            raise ExportBlocked([f"increment.source_bound_extraction:{type(error).__name__}:{error}"]) from error
    audit_gates = response.get("recovery_summary", {})
    return {
        "schema": SCHEMA,
        "status": "PASS_NUMERICAL_CORNER_DEMAND_REPORT_ONLY",
        "candidate": contract["candidate"],
        "geometry_revision_id": contract["geometry_revision_id"],
        "case_id": case_id,
        "scope": "left outer BG001/BG003/BG045 five-member assembly; one authenticated case per invocation",
        "input_only_exporter": True,
        "native_solve_launched_by_exporter": False,
        "source_response_forces_promoted": True,
        "actual_case_demand_usable_for_conditional_joint_checks": True,
        "qualification_boundary": {
            "usable_scope": "source-bound numerical demand input to pending conditional joint checks for this one case",
            "qualified_for_design": False,
            "complete_joint_accepted": False,
            "climbing_or_fabrication_release": False,
            "six_case_coverage_complete": False,
            "six_case_sensitivities_complete": False,
            "floor_slip_or_anchorage_qualified": False,
        },
        "authenticated_source_case": {
            "case_id": case_id,
            "source_case_manifest_sha256": preflight["source_hashes"]["case_manifest_json"],
            "input_model_json_sha256": preflight["source_hashes"]["model_json"],
            "input_model_json_path": preflight["paths"]["model_json"],
            "response_audit_json_sha256": sha256(response_path),
            "response_audit_json_path": str(response_path.resolve()),
            "audited_deck_sha256": response["input_deck_sha256"],
            "audited_native_data_sha256": response["native_data_sha256"],
            "adjacent_native_execution_evidence": native_provenance["observed"],
        },
        "source_contract": {
            "contract_sha256": preflight["source_hashes"]["contract_json"],
            "interface_map_sha256": preflight["source_hashes"]["interface_map_json"],
            "body_names": contract["corner_body_names"],
            "descriptor_midpoint_datums_mm": preflight["interface_map"]["descriptor_midpoint_datums_mm"],
            "datum_scope": preflight["interface_map"]["datum_scope"],
            "new_block_axis_count": contract["new_block_axis_count"],
            "retained_original_leg_runner_axis_count": contract["retained_original_leg_runner_axis_count"],
        },
        "response_audit_root_gates": {key: audit_gates.get(key) for key in ROOT_GATE_KEYS},
        "conditional_reference_evidence": conditional_evidence(),
        "increments": increments,
        "limits": [
            "Perimeter/member cut forces are finite-element compatibility actions for the selected input and case; a group wrench is only a resultant at its declared datum.",
            "BG003 remains two physical continuous three-member bolts, each with two separate lateral planes and one outer-seat tie; plane forces are kept separate and no plane capacities are summed.",
            "Contact pressure is a modeled-area average. It is not a pressure distribution or wood-strength check.",
            "The six ties map to modeled outer washer seats; reported uniform annulus pressures are conditional geometry conversions, not seat-pressure solutions or resistance checks.",
            "Splitting and net-section rows are geometry inputs only; applicability and resistance remain unresolved.",
            "Twelve original LEG/FLOOR-RUNNER arrangements are retained as separate interface rows and their unchanged resistance work is not reopened.",
            "The idealized no-slip floor tangent route remains an unverified support assumption; numerical reaction recovery is not floor qualification.",
            "Parametric screw-withdrawal carriers are identified as nonqualifying and remain conditional model transfer only.",
            "One case does not establish the other five cases or the requested stiffness, engagement, material, accessory, and floor sensitivities.",
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", type=Path, default=DEFAULT_MODEL)
    parser.add_argument("--response", type=Path, help="JSON from the pinned audit; adjacent DAT is hashed but never parsed by this exporter")
    parser.add_argument("--contract", type=Path, default=DEFAULT_CONTRACT)
    parser.add_argument("--interface-map", type=Path, default=DEFAULT_INTERFACE_MAP)
    parser.add_argument("--case-manifest", type=Path, default=DEFAULT_CASE_MANIFEST)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    preflight = validate_static_inputs(args.model, args.contract, args.interface_map, args.case_manifest)
    if not args.response:
        gates = ["verified_response_file_not_supplied"]
        gates.extend(f"response.recovery_summary.{key}" for key in ROOT_GATE_KEYS)
        gates.extend((
            "response.increments[*].all_required_numerical_gates",
            "response.increments[*].physical_balance.body_equilibrium for all five corner bodies",
            "response.increments[*].physical_balance.global_equilibrium",
            "independent_corner_body_force_and_moment_closure_with_rounding_intervals",
            "response.input_deck_sha256_matches_adjacent_model.inp",
            "response.native_data_sha256_matches_adjacent_model.dat",
            "response.increments[-1].load_factor_equals_1.0",
        ))
        report = blocked_report(preflight, gates)
    else:
        try:
            if preflight["failed_static_gates"]:
                raise ExportBlocked(preflight["failed_static_gates"])
            response_record = load_json(args.response)
            native_provenance = adjacent_native_provenance(args.model.resolve(), response_record)
            failures = check_response_gates(response_record, preflight["model"], args.model.resolve(),
                                            str(preflight["model"].get("case_id", "")), preflight["contract"],
                                            native_provenance)
            if failures:
                raise ExportBlocked(failures)
            report = export_report(preflight, args.response)
        except (ExportBlocked, OSError, json.JSONDecodeError) as error:
            gates = error.gates if isinstance(error, ExportBlocked) else [f"response_file_readable_json:{type(error).__name__}"]
            report = blocked_report(preflight, gates, args.response)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, allow_nan=False) + "\n")
    print(report["status"])


if __name__ == "__main__":
    main()
