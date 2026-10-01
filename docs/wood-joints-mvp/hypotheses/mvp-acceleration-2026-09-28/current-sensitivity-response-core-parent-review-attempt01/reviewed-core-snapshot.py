"""Pinned 711 response-core fork for one sealed two-tie sensitivity input.

The ordinary 711 `audit_record` keeps its original strict context/input path.
The separate validated-contract entrypoint changes only how that same core
obtains its force-recovery contract; it does not execute a solver.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import math
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

import numpy as np


ROOT = Path(__file__).resolve().parents[5]
SERIES = ROOT / "docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28"
HERE = Path(__file__).resolve().parent
PINNED_711_PACKET = SERIES / "current-springa-zero-u-token-response-audit-attempt01"
PINNED_711_RESPONSE = PINNED_711_PACKET / "response_audit.py"
PINNED_711_RESPONSE_SHA256 = "711fa96e8faff12dc4b21fa939ae28822be8abba65bc12a896b558f0a54bfff0"
STABLE_PACKET = PINNED_711_PACKET
STABLE_AUDIT = STABLE_PACKET / "stable_response_audit.py"
STABLE_AUDIT_SHA256 = "bdcfa2dd85e152503b740a2f49bb1de6b67462565eb610ff5ee451990335a77d"
CASE_CONTEXT_SCHEMA = "current_springa_case_bound_input_context/v1"
EMBEDDED_CONTEXT_SCHEMA = "current_springa_case_bound_input_context/v1"
CASE_REGISTER_PATH = SERIES / "current-six-case-source-load-register-attempt01/register.json"
CASE_REGISTER_SHA256 = "7a638a49fc5086b4d5fed52148286a300b8b271f7d380b1a131ea8e17b094508"
INPUT_SCHEMA = "current_springa_selected_floor_input_model/v1"
OUTPUT_SCHEMA = "current_springa_selected_floor_physical_response_audit/v1"
BRANCH_ID = "monotone_zero_gap_first_bearing_reference_zero"
NORMAL_CELL_COUNT = 100
SOURCE_TANGENT_ROW_COUNT = 200
MPC_INTERVAL_TOL_MM = 1.0e-5


class ResponseAuditError(ValueError):
    """Raised when source inputs, native output, or recovered forces fail."""


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _load_stable():
    if _sha(PINNED_711_RESPONSE) != PINNED_711_RESPONSE_SHA256:
        raise ResponseAuditError("Pinned 711 response wrapper changed")
    if _sha(STABLE_AUDIT) != STABLE_AUDIT_SHA256:
        raise ResponseAuditError("Pinned stable SPRINGA recovery source changed")
    spec = importlib.util.spec_from_file_location("pinned_springa_response_audit", STABLE_AUDIT)
    if spec is None or spec.loader is None:
        raise ResponseAuditError("Cannot import pinned SPRINGA recovery methods")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


_stable = _load_stable()
parse_native_blocks = _stable.parse_native_blocks
parse_equation_cards = _stable._parse_equation_cards
parse_cload_cards = _stable._parse_cload_cards
parse_node_cards = _stable._parse_node_cards
audit_all_mpcs = _stable._audit_all_mpcs
audit_linear_spring = _stable._audit_linear_spring
audit_springa = _stable._audit_springa
load_scale = _stable._load_scale
balance_physical_state = _stable._balance_physical_state
map_physical_forces = _stable.map_physical_forces
balance_force_tol = _stable.BALANCE_FORCE_TOL_N
balance_moment_tol = _stable.BALANCE_MOMENT_TOL_NMM


def _canonical(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)


def _canonical_sha(value: Any) -> str:
    return hashlib.sha256(_canonical(value).encode("utf-8")).hexdigest()


def _load_sensitivity_validator():
    """Load the one fixed validator under a stable module identity."""
    validator_path = HERE / "validate_sensitivity_input.py"
    module_name = "current_a12_bg001_sensitivity_input_validator"
    loaded = sys.modules.get(module_name)
    if loaded is not None:
        if Path(getattr(loaded, "__file__", "")).resolve() != validator_path.resolve():
            raise ResponseAuditError("Sensitivity validator module identity is bound to another file")
        return loaded
    spec = importlib.util.spec_from_file_location(module_name, validator_path)
    if spec is None or spec.loader is None:
        raise ResponseAuditError("Cannot load the pinned sensitivity input validator")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    try:
        spec.loader.exec_module(module)
    except Exception:
        sys.modules.pop(module_name, None)
        raise
    return module


def _vector(value: Any, size: int = 3) -> np.ndarray:
    result = np.asarray(value, dtype=float)
    if result.shape != (size,) or not np.all(np.isfinite(result)):
        raise ResponseAuditError(f"Expected a finite {size}-vector")
    return result


def _cards(deck: str) -> list[tuple[str, list[str]]]:
    cards: list[tuple[str, list[str]]] = []
    header: str | None = None
    rows: list[str] = []
    for line in deck.splitlines():
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
    return cards


def _header_name(header: str) -> str:
    return header.split(",", 1)[0].strip().upper()


def _equation_key(equation: Any) -> str:
    return _canonical(equation)


def _validate_execution(model_path: Path, data_path: Path, deck_path: Path,
                        execution_path: Path, data: str,
                        case_context: dict[str, Any]) -> dict[str, Any]:
    model_path, data_path = model_path.resolve(), data_path.resolve()
    deck_path, execution_path = deck_path.resolve(), execution_path.resolve()
    packet = model_path.parent
    freeze_path = packet / "freeze.json"
    stdout_path, stderr_path = packet / "native.stdout", packet / "native.stderr"
    required = (model_path, data_path, deck_path, execution_path, freeze_path,
                stdout_path, stderr_path)
    if any(not path.is_file() for path in required):
        missing = [str(path) for path in required if not path.is_file()]
        raise ResponseAuditError("Terminal run provenance is incomplete: " + ", ".join(missing))
    execution = json.loads(execution_path.read_text())
    freeze = json.loads(freeze_path.read_text())
    if execution.get("native_solve_executed") is not True or execution.get("returncode") != 0:
        raise ResponseAuditError("Selected-floor run is not a successful native execution")
    if execution.get("container_confirmed_terminal") is not True:
        raise ResponseAuditError("Native container was not confirmed terminal")
    if freeze.get("schema") != "wood_joint_reduced_native_freeze/v1":
        raise ResponseAuditError("Adjacent freeze has an unsupported schema")
    if freeze.get("native_solve_executed") is not False or freeze.get("mechanical_acceptance") is not False:
        raise ResponseAuditError("Freeze must bind input only and must not claim acceptance")
    if freeze.get("candidate") != case_context["candidate"]:
        raise ResponseAuditError("Freeze candidate does not match the wood-joints development lane")
    if freeze.get("geometry_revision_id") != case_context["geometry_revision_id"]:
        raise ResponseAuditError("Freeze geometry revision is not the reviewed current model")
    if freeze.get("case_id") not in (None, case_context["case_id"]):
        raise ResponseAuditError("Native freeze case does not match the explicit context")
    profile = freeze.get("solver_profile", {})
    if (profile.get("version") != "2.23"
            or profile.get("image_id") != "sha256:31336f517557f5dd5f97d85b1e6e15947fd1c10b44edc1364dbba4c1a5ab6c38"):
        raise ResponseAuditError("Native execution freeze does not identify the pinned CalculiX 2.23 image")
    files = {
        "model.json": model_path,
        "model.inp": deck_path,
        "model.dat": data_path,
        "native.stdout": stdout_path,
        "native.stderr": stderr_path,
    }
    actual = {name: _sha(path) for name, path in files.items()}
    frozen = freeze.get("files_sha256", {})
    output_hashes = execution.get("outputs_sha256", {})
    if any(frozen.get(name) != actual[name] for name in ("model.json", "model.inp")):
        raise ResponseAuditError("Frozen model/deck hashes differ from audited inputs")
    if any(output_hashes.get(name) != actual[name] for name in files):
        raise ResponseAuditError("Terminal execution output hashes do not match audited files")
    if (actual["model.json"] != case_context["selected_input_model_json_sha256"]
            or actual["model.inp"] != case_context["selected_input_deck_sha256"]):
        raise ResponseAuditError("Native run inputs differ from the selected-floor model/deck pinned by context")
    stdout, stderr = stdout_path.read_text(errors="replace"), stderr_path.read_text(errors="replace")
    error_pattern = re.compile(r"(?:\*ERROR|\*\*\s*ERROR|FATAL ERROR)", re.IGNORECASE)
    if error_pattern.search(data) or error_pattern.search(stdout) or error_pattern.search(stderr):
        raise ResponseAuditError("Native DAT/stdout/stderr contains a solver error marker")
    return {
        "execution_path": str(execution_path),
        "execution_sha256": _sha(execution_path),
        "freeze_path": str(freeze_path),
        "freeze_sha256": _sha(freeze_path),
        "returncode": 0,
        "container_confirmed_terminal": True,
        "native_output_hashes_match": True,
        "solver_error_markers_absent": True,
        "observed_file_sha256": actual,
    }


def _context_path(value: str) -> Path:
    path = Path(value)
    return path.resolve() if path.is_absolute() else (ROOT / path).resolve()


def _validate_case_context(context: dict[str, Any]) -> dict[str, Any]:
    if context.get("schema") != CASE_CONTEXT_SCHEMA:
        raise ResponseAuditError(f"Expected case context schema {CASE_CONTEXT_SCHEMA}")
    if (context.get("candidate") != "compact-floor-flush-wood-joints-development"
            or context.get("geometry_revision_id") != "led-clearance-2x6-runner-seated-blocks-v1"):
        raise ResponseAuditError("Case context candidate/revision does not match reviewed wood-joints geometry")
    case_id = str(context.get("case_id", ""))
    branch_id = context.get("selected_floor_branch_id")
    if not case_id or branch_id != BRANCH_ID:
        raise ResponseAuditError("Case context must explicitly name a case and the supported diagnostic branch")
    for claim in ("native_solve_authorized_by_context", "mechanical_acceptance",
                  "qualified_for_design", "frame_ready_for_native_run"):
        if context.get(claim) is True:
            raise ResponseAuditError(f"Case context cannot make a readiness/acceptance claim: {claim}")

    register_path = _context_path(str(context.get("source_case_load_register_path", "")))
    if not register_path.is_file() or _sha(register_path) != CASE_REGISTER_SHA256:
        raise ResponseAuditError("Pinned fresh six-case source-load register is missing or changed")
    if context.get("source_case_load_register_sha256") != CASE_REGISTER_SHA256:
        raise ResponseAuditError("Context does not pin the current source-load register")
    register = json.loads(register_path.read_text())
    if (register.get("status") != "PASS_FRESH_SIX_CASE_SOURCE_LOAD_WRENCH_REGISTER"
            or register.get("candidate") != context["candidate"]
            or register.get("geometry_revision_id") != context["geometry_revision_id"]):
        raise ResponseAuditError("Source-load register candidate, revision, or status is invalid")
    rows = [row for row in register.get("cases", []) if row.get("case_id") == case_id]
    if len(rows) != 1:
        raise ResponseAuditError("Explicit case is not uniquely present in the pinned source-load register")
    case_row = rows[0]
    case_record_sha = _canonical_sha(case_row)
    if context.get("case_record_sha256") != case_record_sha:
        raise ResponseAuditError("Context case-record hash differs from the pinned source-load register row")

    required_file_pins = (
        ("source_controls_model_json_path", "source_controls_model_json_sha256"),
        ("source_controls_deck_path", "source_controls_deck_sha256"),
        ("diagnostic_floor_screen_path", "diagnostic_floor_screen_sha256"),
        ("selected_input_model_json_path", "selected_input_model_json_sha256"),
        ("selected_input_deck_path", "selected_input_deck_sha256"),
    )
    resolved: dict[str, Path] = {}
    for path_key, hash_key in required_file_pins:
        value = context.get(path_key)
        expected = context.get(hash_key)
        if not isinstance(value, str) or not isinstance(expected, str) or not re.fullmatch(r"[0-9a-f]{64}", expected):
            raise ResponseAuditError(f"Case context lacks an exact path/hash pair for {path_key}")
        path = _context_path(value)
        if not path.is_file() or _sha(path) != expected:
            raise ResponseAuditError(f"Case context file pin does not match: {path_key}")
        resolved[path_key] = path

    baseline = json.loads(resolved["source_controls_model_json_path"].read_text())
    baseline_deck = resolved["source_controls_deck_path"].read_text()
    if (baseline.get("case_id") != case_id
            or baseline.get("candidate") != context["candidate"]
            or baseline.get("geometry_revision_id") != context["geometry_revision_id"]
            or baseline.get("source_model_inputs_sha256") != case_row.get("source_model_inputs_sha256")):
        raise ResponseAuditError("Case-specific controls baseline does not match the bound case/load source")
    _stable._validate_input_contract(baseline, baseline_deck)
    baseline_register_binding = baseline.get("source_load_register_binding")
    if baseline_register_binding is None:
        # The already-frozen a12-rear controls record predates the six-case
        # register binding field. Permit it only for its exact pinned input.
        if case_id != "a12-rear" or _sha(resolved["source_controls_model_json_path"]) != "b89e69abd004bd788d3619f73270375bbd8d8a195edf29313a77baee3c1a8f1e":
            raise ResponseAuditError("Per-case controls baseline lacks its source-load register binding")
    else:
        binding = baseline_register_binding
        if (binding.get("case_id") != case_id
                or binding.get("case_record_sha256") != case_record_sha
                or binding.get("register_path") != str(register_path.relative_to(ROOT))
                or binding.get("register_sha256") != CASE_REGISTER_SHA256
                or binding.get("register_status") != register["status"]
                or binding.get("fresh_source_load_and_body_wrenches_match_register") is not True
                or binding.get("historical_response_forces_read") is not False):
            raise ResponseAuditError("Controls baseline source-load binding differs from the case register")

    screen_path = resolved["diagnostic_floor_screen_path"]
    screen = json.loads(screen_path.read_text())
    screen_case_id = context.get("diagnostic_floor_screen_case_id", case_id)
    if screen_case_id != case_id or screen.get("case_id") not in (None, case_id):
        raise ResponseAuditError("Diagnostic screen is not explicitly bound to the selected case")
    if (screen.get("status") not in {
                "REJECTED_PROPOSED_SELECTED_BEARING_SUPPORT_BRANCH",
                "REJECTED_ALL_BEARING_SUPPORT_BRANCH",
            }
            or screen.get("corner_demands_usable") is not False
            or screen.get("full_step_native_convergence") is not True
            or screen.get("all_printed_floor_laws_checked") is not True
            or screen.get("same_positive_cell_set_at_all_printed_times") is not True):
        raise ResponseAuditError("Diagnostic screen lacks the required rejected, stable, non-demand status")
    times = screen.get("all_printed_times", [])
    if (not isinstance(times, list) or not times
            or any(not isinstance(x, (int, float)) or not math.isfinite(float(x)) for x in times)
            or any(float(b) <= float(a) for a, b in zip(times, times[1:]))):
        raise ResponseAuditError("Diagnostic screen has no finite printed-state history")
    selected = set(map(str, screen.get("diagnostic_positive_cells_at_final_time", [])))
    inactive = set(map(str, screen.get("diagnostic_separating_cells_at_final_time", [])))
    selected_raw = list(map(str, screen.get("diagnostic_positive_cells_at_final_time", [])))
    inactive_raw = list(map(str, screen.get("diagnostic_separating_cells_at_final_time", [])))
    if (len(selected) != len(selected_raw) or len(inactive) != len(inactive_raw)
            or len(selected) + len(inactive) != NORMAL_CELL_COUNT or selected & inactive):
        raise ResponseAuditError("Diagnostic selected/inactive cell sets do not partition 100 unique normals")
    source_pins = screen.get("source_sha256", {})
    if not isinstance(source_pins, dict) or not source_pins:
        raise ResponseAuditError("Diagnostic screen lacks source provenance hashes")
    resolved_screen_pins: dict[Path, str] = {}
    for source_path, expected_hash in source_pins.items():
        path = _context_path(str(source_path))
        if not path.is_file() or _sha(path) != expected_hash:
            raise ResponseAuditError(f"Diagnostic screen source pin is missing or changed: {source_path}")
        resolved_screen_pins[path] = str(expected_hash)
    # A proposed mask must derive from this case's exact all-bearing controls
    # run. Bind the screen provenance to both exact controls inputs.
    controls_model_path = resolved["source_controls_model_json_path"]
    controls_deck_path = resolved["source_controls_deck_path"]
    if (resolved_screen_pins.get(controls_model_path) != context["source_controls_model_json_sha256"]
            or resolved_screen_pins.get(controls_deck_path) != context["source_controls_deck_sha256"]):
        raise ResponseAuditError("Diagnostic screen does not bind the exact case-specific all-bearing controls model/deck")
    if context.get("diagnostic_floor_screen_status") != screen["status"]:
        raise ResponseAuditError("Context diagnostic screen status differs from the pinned screen")
    return {
        "case_id": case_id,
        "case_record_sha256": case_record_sha,
        "source_model_inputs_sha256": case_row["source_model_inputs_sha256"],
        "register_path": str(register_path.relative_to(ROOT)),
        "register_sha256": CASE_REGISTER_SHA256,
        "controls_model_path": str(resolved["source_controls_model_json_path"].relative_to(ROOT)),
        "controls_model_sha256": context["source_controls_model_json_sha256"],
        "controls_deck_path": str(resolved["source_controls_deck_path"].relative_to(ROOT)),
        "controls_deck_sha256": context["source_controls_deck_sha256"],
        "screen_path": str(screen_path.relative_to(ROOT)),
        "screen_sha256": context["diagnostic_floor_screen_sha256"],
        "screen_status": screen["status"],
        "selected_cells": selected,
        "inactive_cells": inactive,
        "selected_cell_count": len(selected),
        "inactive_cell_count": len(inactive),
        "active_tangent_row_count": 2 * len(selected),
        "inactive_tangent_row_count": SOURCE_TANGENT_ROW_COUNT - 2 * len(selected),
        "screen_printed_state_count": len(times),
        "source_case_row": case_row,
        "case_context": context,
        "resolved": resolved,
    }


def _validate_model(record: dict[str, Any], deck: str,
                    case_context: dict[str, Any]) -> dict[str, Any]:
    case_pin = _validate_case_context(case_context)
    if record.get("schema") != INPUT_SCHEMA:
        raise ResponseAuditError("Only the selected-floor SPRINGA input schema is accepted")
    if record.get("case_id") != case_pin["case_id"]:
        raise ResponseAuditError("Selected model case_id differs from the explicitly bound case")
    selected_model_path = case_pin["resolved"]["selected_input_model_json_path"]
    selected_deck_path = case_pin["resolved"]["selected_input_deck_path"]
    if record != json.loads(selected_model_path.read_text()):
        raise ResponseAuditError("Loaded selected-floor model differs from its pinned serialized record")
    if deck != selected_deck_path.read_text():
        raise ResponseAuditError("Loaded selected-floor deck differs from its pinned serialized deck")
    if record.get("schema") != INPUT_SCHEMA:
        raise ResponseAuditError("Only the selected-floor SPRINGA input schema is accepted")
    if record.get("legacy_reduced_static_linear_response_schema_compatible") is not False:
        raise ResponseAuditError("Legacy linear response compatibility must be explicitly false")
    if record.get("input_adapter_status") != "ASSEMBLED_SELECTED_FLOOR_BRANCH_INPUT_ONLY":
        raise ResponseAuditError("Selected-floor record is not an input-only adapter output")
    if record.get("native_solve_executed") is not False or record.get("input_only") is not True:
        raise ResponseAuditError("Source model must record that the adapter did not execute a solve")
    if record.get("frame_ready_for_native_run") is not False or record.get("mechanical_acceptance") is not False:
        raise ResponseAuditError("Input record cannot assert readiness or mechanical acceptance")
    if record.get("candidate") != case_context["candidate"]:
        raise ResponseAuditError("Input candidate is not the selected wood-joints development lane")
    if record.get("geometry_revision_id") != case_context["geometry_revision_id"]:
        raise ResponseAuditError("Input geometry does not match the reviewed current revision")

    baseline_path = case_pin["resolved"]["source_controls_model_json_path"]
    baseline_deck_path = case_pin["resolved"]["source_controls_deck_path"]
    baseline = json.loads(baseline_path.read_text())
    baseline_deck = baseline_deck_path.read_text()
    # Validate the trusted all-bearing source inventory with the pinned method,
    # then require the selected adapter to preserve its unchanged physical and
    # constitutive data exactly.
    baseline_contract = _stable._validate_input_contract(baseline, baseline_deck)
    if (record.get("candidate") != baseline.get("candidate")
            or record.get("geometry_revision_id") != baseline.get("geometry_revision_id")
            or record.get("case_id") != baseline.get("case_id")):
        raise ResponseAuditError("Selected adapter changed candidate or reviewed geometry")
    exact_preservation = (
        "raw_source_carrier_law_inventory_rows", "unilateral_springa_bindings", "springs",
        "connection_ownership", "physical_body_nodes", "physical_body_elements", "body_geometry",
        "physical_body_loads", "physical_external_loads", "loads", "elements", "fixed_nodes",
        "nodes", "connection_attachment_rows", "connection_counts", "contact_cell_ownership",
        "floor_support_nodes", "geometry_audit", "case_assembly_audit",
        "case_input", "load_case_scope", "scenario", "connection_scenario",
        "source_model_inputs_sha256", "source_model_pin", "source_wrench_ledger",
        "physical_load_sources_by_body", "body_wrench_audit_rows", "physical_body_wrenches",
        "expected_physical_body_wrenches", "source_geometry_hashes", "source_geometry_rebinding",
        "material_binding", "material_deck_audit", "source_load_register_binding",
    )
    for key in exact_preservation:
        if record.get(key) != baseline.get(key):
            raise ResponseAuditError(f"Selected-floor adapter changed source input field {key}")
    if record.get("source_response_schema") == "wood_joint_reduced_rf_force_recovery/v1":
        raise ResponseAuditError("Legacy linear response schema cannot assess a nonlinear-carrier record")
    if record.get("source_response_forces_read") is True:
        raise ResponseAuditError("Historical response forces cannot supply this response")
    normalization = record.get("source_load_normalization_audit", {})
    for key in ("structure_loads_normalized_to_fresh_physical_external_map",
                "expanded_map_matches_fresh_physical_external_loads",
                "raw_and_expanded_wrench_transfer_passed"):
        if normalization.get(key) is not True:
            raise ResponseAuditError(f"Fresh source load normalization failed: {key}")
    if normalization.get("historical_response_forces_read") is not False:
        raise ResponseAuditError("Source load normalization refers to historical force output")
    emission = record.get("source_load_emission_audit", {})
    if (emission.get("source_cload_card_text_unchanged_from_frozen_controls") is not True
            or emission.get("source_cload_map_unchanged_from_frozen_controls") is not True
            or emission.get("floor_reference_nodes_receive_no_direct_cload") is not True):
        raise ResponseAuditError("Selected branch source CLOAD emission differs from frozen controls")
    if any(token in deck.upper() for token in ("*FRICTION", "*INITIAL CONDITIONS,TYPE=STRESS", "*CONTACT PAIR")):
        raise ResponseAuditError("Friction, stress preload, or added contact input is outside this branch")

    screen_path = case_pin["resolved"]["diagnostic_floor_screen_path"]
    screen = json.loads(screen_path.read_text())
    selected = case_pin["selected_cells"]
    inactive = case_pin["inactive_cells"]
    selected_count = case_pin["selected_cell_count"]
    inactive_count = case_pin["inactive_cell_count"]
    active_tangent_rows = case_pin["active_tangent_row_count"]
    inactive_tangent_rows = case_pin["inactive_tangent_row_count"]
    if record.get("source_model_inputs_sha256") != case_pin["source_model_inputs_sha256"]:
        raise ResponseAuditError("Selected-floor source input hash differs from its case load register")
    embedded_context = record.get("case_bound_input_context")
    if embedded_context is not None:
        shared_context_keys = (
            "case_id", "candidate", "geometry_revision_id", "case_record_sha256",
            "source_model_inputs_sha256", "source_case_load_register_path", "source_case_load_register_sha256",
            "source_controls_model_json_path", "source_controls_model_json_sha256",
            "source_controls_deck_path", "source_controls_deck_sha256",
            "diagnostic_floor_screen_path", "diagnostic_floor_screen_sha256",
            "selected_floor_branch_id",
        )
        if embedded_context.get("schema") != EMBEDDED_CONTEXT_SCHEMA or any(
            embedded_context.get(key) != case_context.get(key) for key in shared_context_keys
        ):
            raise ResponseAuditError("Embedded case context differs from the explicit run context")
    metadata = record.get("floor_branch_metadata")
    if not isinstance(metadata, dict):
        raise ResponseAuditError("Selected-floor branch metadata is missing")
    if metadata.get("branch_id") != BRANCH_ID or metadata.get("status") != "proposed_diagnostic_mask_only":
        raise ResponseAuditError("Selected-floor record does not declare the required diagnostic branch")
    if metadata.get("screen_packet_sha256") != case_pin["screen_sha256"]:
        raise ResponseAuditError("Selected-floor model is not bound to the pinned parent screen")
    if metadata.get("screen_packet_path") not in (case_pin["screen_path"], str(screen_path)):
        raise ResponseAuditError("Selected-floor model names a different parent screen")
    screen_pin = record.get("selected_floor_branch_screen_pin", {})
    if (screen_pin.get("diagnostic_only") is not True
            or screen_pin.get("path") not in (case_pin["screen_path"], str(screen_path))
            or screen_pin.get("sha256") != case_pin["screen_sha256"]
            or screen_pin.get("status") != case_pin["screen_status"]
            or screen_pin.get("screen_positive_forces_or_active_states_reused_as_response") is not False):
        raise ResponseAuditError("Selected floor screen is not pinned as a rejected, diagnostic-only proposal")
    if set(map(str, record.get("floor_selected_bearing_cells", []))) != selected:
        raise ResponseAuditError("Selected bearing cells differ from the pinned screen")
    if set(map(str, record.get("floor_inactive_cells", []))) != inactive:
        raise ResponseAuditError("Inactive cells differ from the pinned screen")
    if (set(map(str, metadata.get("selected_cells", []))) != selected
            or set(map(str, metadata.get("inactive_cells", []))) != inactive):
        raise ResponseAuditError("Branch metadata mask differs from the pinned selected/inactive cells")

    raw = record["raw_source_carrier_law_inventory_rows"]
    source_rows = [row for row in raw if row.get("intended_law") == "floor_tangent_all_bearing_hypothesis"]
    if len(source_rows) != SOURCE_TANGENT_ROW_COUNT:
        raise ResponseAuditError("Original source tangent inventory must retain all 200 rows")
    mask = record.get("floor_selected_mask_by_original_row")
    if not isinstance(mask, list) or len(mask) != SOURCE_TANGENT_ROW_COUNT:
        raise ResponseAuditError("Selected-floor original-row mask must contain all 200 source rows")
    mask_by_index: dict[int, dict[str, Any]] = {}
    for row in mask:
        index = int(row["source_row_original_index"])
        if index in mask_by_index or not 0 <= index < SOURCE_TANGENT_ROW_COUNT:
            raise ResponseAuditError("Floor row mask contains duplicate or invalid original indices")
        mask_by_index[index] = row
    if set(mask_by_index) != set(range(SOURCE_TANGENT_ROW_COUNT)):
        raise ResponseAuditError("Floor row mask does not cover every original tangent row")
    selected_indices = list(map(int, record.get("floor_selected_original_row_indices", [])))
    active_alias = list(map(int, record.get("floor_active_original_row_indices", [])))
    inactive_indices = list(map(int, record.get("floor_inactive_original_row_indices", [])))
    if selected_indices != sorted(selected_indices) or selected_indices != active_alias:
        raise ResponseAuditError("Selected and active floor row indices are not the same sorted list")
    if inactive_indices != sorted(inactive_indices) or set(selected_indices) & set(inactive_indices):
        raise ResponseAuditError("Active/inactive floor row indices are not sorted disjoint sets")
    if (set(selected_indices) | set(inactive_indices) != set(range(SOURCE_TANGENT_ROW_COUNT))
            or len(selected_indices) != active_tangent_rows
            or len(inactive_indices) != inactive_tangent_rows):
        raise ResponseAuditError("Active/inactive tangent rows do not match the explicitly pinned mask")
    by_original_source = {i: row for i, row in enumerate(source_rows)}
    if len(by_original_source) != SOURCE_TANGENT_ROW_COUNT:
        raise ResponseAuditError("Source tangent original-row order is malformed")
    expected_active: set[int] = set()
    for index, mask_row in mask_by_index.items():
        source = by_original_source[index]
        cell = str(source["floor_normal_gate"])
        source_id = f"{cell}_friction/local-dof-{int(source['dof'])}"
        is_selected = cell in selected
        if (str(mask_row.get("source_row_id")) != source_id
                or str(mask_row.get("normal_cell")) != cell
                or int(mask_row.get("local_dof")) != int(source["dof"])
                or mask_row.get("selected") is not is_selected):
            raise ResponseAuditError(f"Floor source-row mask disagrees with original row {index}")
        if is_selected:
            expected_active.add(index)
    if expected_active != set(selected_indices):
        raise ResponseAuditError("Selected original tangent rows do not correspond to the pinned screen cells")

    baseline_refs = {int(row["source_row_original_index"]): row for row in baseline["floor_reference_nodes_and_load_map"]}
    refs = record.get("floor_reference_nodes_and_load_map")
    if not isinstance(refs, list) or len(refs) != active_tangent_rows:
        raise ResponseAuditError("Selected-floor input reference rows do not match the pinned active mask")
    refs_by_original: dict[int, dict[str, Any]] = {}
    for ref in refs:
        index = int(ref["source_row_original_index"])
        if index in refs_by_original:
            raise ResponseAuditError("Duplicate active floor reference row")
        refs_by_original[index] = ref
    if list(refs_by_original) != selected_indices:
        raise ResponseAuditError("Active floor reference rows are not sorted in original source-row order")
    for index, ref in refs_by_original.items():
        prior = baseline_refs[index]
        for key in ("source_row_id", "normal_cell", "physical_owner", "owner_tangent_basis_global_xyz", "owner_floorpoint_xyz_mm"):
            if ref.get(key) != prior.get(key):
                raise ResponseAuditError(f"Selected floor source ownership changed at original row {index}: {key}")
        if str(ref.get("source_row_id")) != str(mask_by_index[index]["source_row_id"]):
            raise ResponseAuditError(f"Active reference/source-row ID mismatch at original row {index}")
        if int(ref["node"]) != int(prior["node"]):
            raise ResponseAuditError(f"Selected scalar reference node changed at original row {index}")
    if list(map(int, record.get("floor_reference_nodes", []))) != [int(ref["node"]) for ref in refs]:
        raise ResponseAuditError("Selected scalar reference-node list differs from its active source-row map")

    inactive_cells_by_index = {i: str(by_original_source[i]["floor_normal_gate"]) for i in inactive_indices}
    if {inactive_cells_by_index[i] for i in inactive_indices} != inactive:
        raise ResponseAuditError("Inactive row inventory does not cover the pinned inactive cells")
    floor_audit = record.get("floor_constraint_audit", {})
    floor_rows = floor_audit.get("floor_reference_rows", [])
    normalized_rows = list(map(int, floor_audit.get("selected_rows_original_indices", [])))
    if len(floor_rows) != active_tangent_rows or normalized_rows != selected_indices:
        raise ResponseAuditError("Selected-floor transform does not map normalized equations to active source rows")
    if (floor_audit.get("independent_constraint_rank") != active_tangent_rows
            or floor_audit.get("floor_reference_count") != active_tangent_rows):
        raise ResponseAuditError("Selected floor reference transform rank/channel count differs from the pinned mask")
    serialized_equation_audit = record.get("serialized_selected_floor_equation_audit", {})
    if serialized_equation_audit.get("selected_reference_node_tags_unique") is not True:
        raise ResponseAuditError("Selected floor reference nodes are not unique/fresh")
    if (metadata.get("selected_cell_count") != selected_count
            or metadata.get("inactive_cell_count") != inactive_count
            or metadata.get("selected_source_tangent_row_count") != active_tangent_rows
            or metadata.get("inactive_source_tangent_row_count") != inactive_tangent_rows
            or metadata.get("printed_state_count") != case_pin["screen_printed_state_count"]
            or metadata.get(f"positive_set_stable_at_all_{case_pin['screen_printed_state_count']}_printed_states") is not True
            or metadata.get("selected_branch_screen_status") != case_pin["screen_status"]
            or metadata.get("selected_branch_screen_outputs_adopted") is not False
            or metadata.get("automatic_mask_iteration_authorized") is not False
            or metadata.get("general_release_recontact_or_uniqueness_claimed") is not False
            or metadata.get("physical_force_adoption") is not False
            or metadata.get("first_bearing_reference") != "zero"
            or metadata.get("friction_added") is not False
            or metadata.get("displacement_preload_added") is not False
            or metadata.get("anchor_added") is not False
            or metadata.get("normal_springa_carriers_changed") is not False):
        raise ResponseAuditError("Selected-floor branch scope or non-addition claims are inconsistent")
    wrench_proof = floor_audit.get("wrench_mapping", {})
    if wrench_proof.get("selected_source_row_point_wrenches_preserved") is not True:
        raise ResponseAuditError("Selected floor transform lacks source-point wrench proof")
    if floor_audit.get("active_original_row_indices") != selected_indices:
        raise ResponseAuditError("Selected-floor matrix rows are not in original-source order")
    try:
        matrix_a = np.asarray(floor_audit["selected_A"], dtype=float)
        matrix_s = np.asarray(floor_audit["selected_S"], dtype=float)
        matrix_h = np.asarray(floor_audit["selected_H"], dtype=float)
        matrix_d = np.asarray(floor_audit["selected_D"], dtype=float)
        masters = [tuple(map(int, dof)) for dof in floor_audit["physical_master_dofs"]]
        pivots = [tuple(map(int, dof)) for dof in floor_audit["selected_pivot_physical_dofs"]]
    except (KeyError, TypeError, ValueError) as error:
        raise ResponseAuditError("Selected floor H/D/S/A source-point transform is incomplete") from error
    if (matrix_a.shape != (active_tangent_rows, len(masters))
            or matrix_h.shape != matrix_a.shape
            or matrix_s.shape != (active_tangent_rows, active_tangent_rows)
            or matrix_d.shape != (active_tangent_rows, active_tangent_rows)):
        raise ResponseAuditError("Selected floor A/S/H/D matrices have unexpected dimensions")
    if len(pivots) != active_tangent_rows or len(set(pivots)) != active_tangent_rows or len(set(masters)) != len(masters):
        raise ResponseAuditError("Selected floor transform pivot/master DOF map is not unique")
    master_col = {key: col for col, key in enumerate(masters)}
    if any(pivot not in master_col for pivot in pivots):
        raise ResponseAuditError("Selected floor pivot is not a physical master DOF")
    transform_residual = float(np.max(np.abs(matrix_s @ matrix_h - matrix_a)))
    reference_residual = float(np.max(np.abs(matrix_s @ matrix_d - np.eye(active_tangent_rows))))
    pivot_residual = float(np.max(np.abs(matrix_h[:, [master_col[key] for key in pivots]] - np.eye(active_tangent_rows))))
    if max(transform_residual, reference_residual, pivot_residual) > 1.0e-10:
        raise ResponseAuditError("Selected floor serialized source constraint reconstruction is inaccurate")
    coordinate_map = {int(node): _vector(point) for node, point in record["nodes"].items()}
    source_point_wrench = np.zeros((6, len(masters)), dtype=float)
    for col, (node, dof) in enumerate(masters):
        if node not in coordinate_map or dof not in (1, 2, 3):
            raise ResponseAuditError("Selected floor transform contains an invalid physical master DOF")
        unit = np.eye(3)[dof - 1]
        source_point_wrench[:3, col] = unit
        source_point_wrench[3:, col] = np.cross(coordinate_map[node], unit)
    force_action_map = matrix_h.T @ np.linalg.inv(matrix_d.T)
    expected_wrenches = np.column_stack([
        np.concatenate((_vector(ref["owner_tangent_basis_global_xyz"]),
                        np.cross(_vector(ref["owner_floorpoint_xyz_mm"]),
                                 _vector(ref["owner_tangent_basis_global_xyz"]))))
        for ref in refs
    ])
    observed_wrenches = source_point_wrench @ force_action_map
    source_point_force_error = float(np.max(np.abs(observed_wrenches[:3] - expected_wrenches[:3])))
    source_point_moment_error = float(np.max(np.abs(observed_wrenches[3:] - expected_wrenches[3:])))
    if source_point_force_error > 1.0e-9 or source_point_moment_error > 1.0e-6:
        raise ResponseAuditError("Selected floor reference forces do not preserve source-point unit wrenches")

    rows_by_eq: dict[int, dict[str, Any]] = {}
    for row in floor_rows:
        eq_index = int(row["normalized_equation_index"])
        original = int(row["source_row_original_index"])
        if eq_index in rows_by_eq or eq_index not in range(active_tangent_rows):
            raise ResponseAuditError("Selected floor equation audit has duplicate/invalid normalized index")
        if normalized_rows[eq_index] != original or original not in refs_by_original:
            raise ResponseAuditError("Selected floor equation permutation does not return to the original row")
        if int(row["dependent_reference_node"]) != int(refs_by_original[original]["node"]):
            raise ResponseAuditError("Selected floor equation points to a different reference channel")
        if (str(row.get("source_row_id")) != str(refs_by_original[original]["source_row_id"])
                or str(row.get("normal_cell")) != str(refs_by_original[original]["normal_cell"])
                or int(row.get("local_dof", -1)) != int(refs_by_original[original]["source_spring_local_dof"])):
            raise ResponseAuditError("Selected-floor equation/source row ID or tangent axis changed")
        rows_by_eq[eq_index] = row
    if set(rows_by_eq) != set(range(active_tangent_rows)):
        raise ResponseAuditError("Selected floor equation/reference map is incomplete")

    # Check that the proposed release actually removes every inactive scalar
    # channel while preserving every non-floor projection/MPC equation.
    old_floor_pivots = {
        tuple(map(int, row["dependent_physical_pivot_dof"]))
        for row in baseline["floor_constraint_audit"]["floor_reference_rows"]
    }
    # The selected reference channels are the only transformed floor rows.
    new_floor_pivots = {
        tuple(map(int, row["dependent_physical_pivot_dof"])) for row in floor_rows
    }
    if len(new_floor_pivots) != active_tangent_rows:
        raise ResponseAuditError("Selected floor equations do not have unique pivots per active row")
    current_nodes = {int(node) for node in record["nodes"]}
    cload = parse_cload_cards(deck)
    inactive_output_rows = record.get("floor_inactive_scalar_output_nodes", [])
    if len(inactive_output_rows) != inactive_tangent_rows:
        raise ResponseAuditError("Inactive scalar output-only carryover inventory differs from the pinned mask")
    inactive_output_tags = {int(row["node"]) for row in inactive_output_rows}
    if len(inactive_output_tags) != inactive_tangent_rows or not inactive_output_tags <= current_nodes:
        raise ResponseAuditError("Inactive output-only scalar tags are not a unique subset of emitted nodes")
    required_inactive_role = "isolated fixed scalar output carryover; no equation, load, or floor force map"
    if any(row.get("role") != required_inactive_role for row in inactive_output_rows):
        raise ResponseAuditError("Inactive scalar carryovers are not explicitly output-only")
    active_ref_tags = {int(ref["node"]) for ref in refs}
    if inactive_output_tags & active_ref_tags:
        raise ResponseAuditError("Inactive scalar output-only tags overlap active floor force channels")
    for index in inactive_indices:
        output_row = next((row for row in inactive_output_rows
                           if int(row["source_row_original_index"]) == index), None)
        if output_row is None:
            raise ResponseAuditError(f"Inactive output-only node is missing original row {index}")
        if int(output_row["node"]) != int(baseline_refs[index]["node"]):
            raise ResponseAuditError(f"Inactive output-only node identity changed at original row {index}")
        if int(output_row["node"]) not in set(map(int, record.get("fixed_nodes", []))):
            raise ResponseAuditError(f"Inactive output-only scalar is not isolated/fixed at original row {index}")
        if int(output_row["node"]) in {int(term[0]) for eq in record["equations"] for term in eq}:
            raise ResponseAuditError(f"Inactive output-only node appears in an equation at original row {index}")
        if any(int(node) == int(output_row["node"]) and abs(float(value)) > 1.0e-14
               for (node, dof), value in cload.items()):
            raise ResponseAuditError(f"Inactive output-only node carries a source load at original row {index}")
    current_equations = record.get("equations", [])
    emitted_equations = parse_equation_cards(deck)
    if len(emitted_equations) != len(current_equations):
        raise ResponseAuditError("Emitted equation count differs from the selected model")
    for i, (actual, expected) in enumerate(zip(emitted_equations, current_equations, strict=True)):
        if len(actual) != len(expected) or any(
            int(term_a[0]) != int(term_e[0]) or int(term_a[1]) != int(term_e[1])
            or abs(float(term_a[2]) - float(term_e[2])) > max(1.0e-12, abs(float(term_e[2])) * 1.0e-13)
            for term_a, term_e in zip(actual, expected, strict=True)
        ):
            raise ResponseAuditError(f"Emitted equation differs from selected record at index {i}")
    old_equations = baseline["equations"]
    old_nonfloor = [eq for eq in old_equations if tuple(map(int, eq[0][:2])) not in old_floor_pivots]
    new_nonfloor = [eq for eq in current_equations if tuple(map(int, eq[0][:2])) not in new_floor_pivots]
    if Counter(map(_equation_key, old_nonfloor)) != Counter(map(_equation_key, new_nonfloor)):
        raise ResponseAuditError("Original projection and non-floor MPC equations changed")
    emitted_nodes = parse_node_cards(deck)
    declared_nodes = {int(node): _vector(point) for node, point in record["nodes"].items()}
    if set(emitted_nodes) != set(declared_nodes):
        raise ResponseAuditError("Emitted node inventory differs from selected model")
    for node in declared_nodes:
        if not np.allclose(emitted_nodes[node], declared_nodes[node], rtol=0.0,
                           atol=1.0e-12 + np.abs(declared_nodes[node]) * 1.0e-13):
            raise ResponseAuditError(f"Emitted node position differs from source record at node {node}")
    for node in baseline["physical_body_nodes"].values():
        if not set(map(int, node)) <= current_nodes:
            raise ResponseAuditError("Selected model removed a physical body node")
    declared_loads = {
        (int(node), dof): float(value)
        for node, force in record["loads"].items()
        for dof, value in enumerate(force, start=1) if abs(float(value)) > 1.0e-14
    }
    if set(cload) != set(declared_loads) or any(
        abs(cload[key] - declared_loads[key]) > max(1.0e-10, abs(declared_loads[key]) * 1.0e-13)
        for key in declared_loads
    ):
        raise ResponseAuditError("Selected model CLOAD inventory differs from emitted source CLOADs")
    expected_nonmutable = [card for card in _cards(baseline_deck)
                           if _header_name(card[0]) not in {"*NODE", "*BOUNDARY", "*EQUATION", "*CLOAD"}]
    actual_nonmutable = [card for card in _cards(deck)
                         if _header_name(card[0]) not in {"*NODE", "*BOUNDARY", "*EQUATION", "*CLOAD"}]
    if expected_nonmutable != actual_nonmutable:
        raise ResponseAuditError("Non-mutable native law/material/element deck cards changed")
    old_boundaries = [card for card in _cards(baseline_deck) if _header_name(card[0]) == "*BOUNDARY"]
    new_boundaries = [card for card in _cards(deck) if _header_name(card[0]) == "*BOUNDARY"]
    if old_boundaries != new_boundaries:
        raise ResponseAuditError("Native boundary constraints changed with the selected floor mask")

    # Reconstruct active reference source-load corrections from emitted E and CLOAD values.
    pivot_equation: dict[tuple[int, int], list[Any]] = {}
    for equation in current_equations:
        if equation and len(equation[0]) == 3 and abs(float(equation[0][2]) - 1.0) < 1.0e-13:
            pivot_equation[(int(equation[0][0]), int(equation[0][1]))] = equation
    pivot_load = np.zeros(active_tangent_rows, dtype=float)
    correction = np.zeros(active_tangent_rows, dtype=float)
    for eq_index, audit_row in rows_by_eq.items():
        pivot = tuple(map(int, audit_row["dependent_physical_pivot_dof"]))
        equation = pivot_equation.get(pivot)
        if equation is None:
            raise ResponseAuditError(f"Selected floor physical pivot equation is missing: {pivot}")
        pivot_load[eq_index] = cload.get(pivot, 0.0)
        for ref_index, original in enumerate(normalized_rows):
            ref_node = int(refs_by_original[original]["node"])
            e_coefficient = sum(float(term[2]) for term in equation
                                if int(term[0]) == ref_node and int(term[1]) == 1)
            correction[ref_index] += -e_coefficient * pivot_load[eq_index]
    omission_bound = active_tangent_rows * 1.0e-13 * max(1.0, float(np.max(np.abs(pivot_load))))
    correction_tolerance = max(1.0e-7, omission_bound + 1.0e-10)
    max_correction_error = 0.0
    for column, original in enumerate(normalized_rows):
        ref, audit_row = refs_by_original[original], rows_by_eq[column]
        for expected_correction in (ref.get("source_load_correction_N"), audit_row.get("reference_load_correction_N")):
            if expected_correction is None:
                raise ResponseAuditError("Selected floor reference lacks emitted-source-load correction")
            difference = abs(float(expected_correction) - correction[column])
            max_correction_error = max(max_correction_error, difference)
            if difference > correction_tolerance:
                raise ResponseAuditError("Selected floor correction differs from emitted CLOAD/E transfer")
    serialized_transfer = record.get("serialized_selected_floor_equation_audit", {})
    if (serialized_transfer.get("correction_derived_from_emitted_E_and_CLOAD") is not True
            or serialized_transfer.get("no_equation_or_reference_for_inactive_rows") is not True
            or serialized_transfer.get("inactive_fixed_scalar_nodes_are_unconnected_carryovers") is not True
            or serialized_transfer.get("all_nonfloor_equations_unchanged") is not True):
        raise ResponseAuditError("Selected floor transform lacks emitted-CLOAD correction evidence")
    source_transfer = floor_audit.get("source_load_transfer", {})
    if source_transfer.get("inactive_rows_have_no_reference_and_zero_correction") is not True:
        raise ResponseAuditError("Selected floor source transfer does not exclude every inactive row")

    source_by_group = {str(row["group"]): row for row in raw}
    if len(source_by_group) != len(raw):
        raise ResponseAuditError("Source inventory contains duplicate carrier groups")
    if len(record["unilateral_springa_bindings"]) != 1292 or len(record["springs"]) != 348:
        raise ResponseAuditError("Selected model changed the 1,292 SPRINGA / 348 bilateral carrier counts")
    removed_tangents = {str(row["group"]) for row in source_rows}
    if removed_tangents & ({str(x["group"]) for x in record["unilateral_springa_bindings"]}
                           | {str(x["group"]) for x in record["springs"]}):
        raise ResponseAuditError("Removed floor tangents remain in native carrier inventories")
    for index, ref in refs_by_original.items():
        source = by_original_source[index]
        if int(ref.get("source_spring_element", -1)) != int(source["element"]):
            raise ResponseAuditError(f"Active exact-floor source element changed at original row {index}")
        if str(ref.get("source_spring_group")) != str(source["group"]):
            raise ResponseAuditError(f"Active exact-floor source group changed at original row {index}")
        if int(ref.get("source_spring_local_dof", -1)) != int(source["dof"]):
            raise ResponseAuditError(f"Active exact-floor tangent axis changed at original row {index}")
        owner = source["physical_owner"]
        basis = _vector(ref["owner_tangent_basis_global_xyz"])
        expected_basis = _vector(owner["force_basis"][int(source["dof"]) - 1])
        if not np.allclose(basis, expected_basis, rtol=0.0, atol=1.0e-12):
            raise ResponseAuditError(f"Active exact-floor basis changed at original row {index}")
        if not np.allclose(_vector(ref["owner_floorpoint_xyz_mm"]), _vector(owner["point"]), rtol=0.0, atol=1.0e-9):
            raise ResponseAuditError(f"Active exact-floor point changed at original row {index}")

    bodies = record["physical_body_nodes"]
    if len(bodies) != 50 or any(not values for values in bodies.values()):
        raise ResponseAuditError("Expected 50 nonempty source-owned physical bodies")
    node_sets = {name: set(map(int, values)) for name, values in bodies.items()}
    union: set[int] = set()
    for name, values in node_sets.items():
        if union & values:
            raise ResponseAuditError(f"Physical nodes have duplicate body ownership near {name}")
        union |= values
    c3d20_nodes = {int(node) for element in record["elements"].values()
                   if str(element[0]).upper() == "C3D20" for node in element[1]}
    if c3d20_nodes != union:
        raise ResponseAuditError("Physical body-node ownership does not cover the solid mesh exactly")
    new_axes = {
        str(row["physical_owner"]["axis_id"])
        for row in raw if row["role"] == "candidate_bolt_lateral_plane"
    }
    retained_axes = {
        str(row["physical_owner"]["axis_id"])
        for row in raw if row["role"] == "retained_bolt_lateral_plane"
    }
    panel_axes = {
        str(row["physical_owner"]["axis_id"])
        for row in raw if row["role"] == "panel_screw_lateral_plane"
    }
    outer_seat_axes = {
        str(row["physical_owner"]["axis_id"])
        for row in raw if row["role"] == "physical_bolt_outer_seat_tension"
    }
    if (len(new_axes) != 92 or len(retained_axes) != 12 or new_axes & retained_axes
            or len(panel_axes) != 66 or outer_seat_axes != new_axes | retained_axes):
        raise ResponseAuditError("The 92 new / 12 retained bolt axes or 66 panel-screw axes changed")
    return {
        "source_by_group": source_by_group,
        "source_rows": raw,
        "source_index_by_group": {str(row["group"]): i for i, row in enumerate(raw)},
        "bindings": record["unilateral_springa_bindings"],
        "springs": record["springs"],
        "floor_by_original": refs_by_original,
        "floor_by_equation": rows_by_eq,
        "selected_indices": selected_indices,
        "inactive_indices": inactive_indices,
        "inactive_output_nodes": inactive_output_rows,
        "selected_cells": selected,
        "inactive_cells": inactive,
        "mask_by_index": mask_by_index,
        "physical_body_nodes": node_sets,
        "emitted_nodes": emitted_nodes,
        "emitted_cloads": cload,
        "total_time": baseline_contract["total_time"],
        "screen_sha256": case_pin["screen_sha256"],
        "case_id": case_pin["case_id"],
        "case_record_sha256": case_pin["case_record_sha256"],
        "case_load_register_sha256": case_pin["register_sha256"],
        "selected_cell_count": selected_count,
        "inactive_cell_count": inactive_count,
        "active_tangent_row_count": active_tangent_rows,
        "inactive_tangent_row_count": inactive_tangent_rows,
        "case_context_provenance": {
            key: case_pin[key] for key in (
                "case_id", "case_record_sha256", "source_model_inputs_sha256", "register_path",
                "register_sha256", "controls_model_path", "controls_model_sha256",
                "controls_deck_path", "controls_deck_sha256", "screen_path", "screen_sha256", "screen_status",
            )
        },
        "floor_load_correction_max_abs_error_N": max_correction_error,
        "floor_load_transfer_omission_bound_N": omission_bound,
        "source_constraint_reconstruction_residual": transform_residual,
        "source_reference_transform_residual": reference_residual,
        "source_pivot_identity_residual": pivot_residual,
        "source_point_wrench_force_error_N": source_point_force_error,
        "source_point_wrench_moment_error_Nmm": source_point_moment_error,
        "new_candidate_bolt_axis_count": len(new_axes),
        "retained_leg_runner_bolt_axis_count": len(retained_axes),
        "new_and_retained_bolt_axes_disjoint": True,
        "panel_screw_axis_count": len(panel_axes),
        "inventory_summary": {
            "source_carrier_rows": len(raw),
            "native_springa_rows": len(record["unilateral_springa_bindings"]),
            "retained_bilateral_spring2_rows": len(record["springs"]),
            "selected_floor_tangent_reaction_rows": len(refs_by_original),
            "inactive_floor_tangent_rows_without_restraint": len(inactive_indices),
            "selected_bearing_cells": len(selected),
            "inactive_separated_cells": len(inactive),
            "physical_body_count": len(bodies),
            "new_candidate_bolt_axes": len(new_axes),
            "retained_leg_runner_bolt_axes": len(retained_axes),
            "new_and_retained_bolt_axes_disjoint": True,
            "panel_screw_axes": len(panel_axes),
            "legacy_linear_auditor_reused": False,
        },
    }


def _audit_selected_floor_rows(contract: dict[str, Any], record: dict[str, Any],
                               state: dict[str, Any], scale: float) -> list[dict[str, Any]]:
    rows = []
    for original, reference in sorted(contract["floor_by_original"].items()):
        node = int(reference["node"])
        basis = _vector(reference["owner_tangent_basis_global_xyz"])
        if node not in state["rf"]:
            raise ResponseAuditError(f"Selected exact-floor RF channel is absent at row {original}")
        if int(reference.get("reference_dof", 0)) != 1:
            raise ResponseAuditError(f"Selected exact-floor reference is not scalar DOF 1 at row {original}")
        raw_rf = float(state["rf"][node][0])
        rf_radius = float(state["rf_radius"][node][0])
        source_load = float(reference["source_load_correction_N"]) * scale
        recovered = raw_rf - source_load
        source = contract["source_by_group"][str(reference["source_spring_group"])]
        owner = source["physical_owner"]
        if owner.get("second") != "floor" or owner.get("first") not in contract["physical_body_nodes"]:
            raise ResponseAuditError(f"Selected floor tangent row has an invalid physical owner: {original}")
        force = recovered * basis
        force_radius = rf_radius * np.abs(basis)
        rows.append({
            "name": "exact-floor/" + str(reference["source_row_id"]),
            "connector_name": str(reference["source_spring_name"]),
            "source_row_id": str(reference["source_row_id"]),
            "source_spring_group": str(reference["source_spring_group"]),
            "source_inventory_row_index": contract["source_index_by_group"][str(reference["source_spring_group"])],
            "source_row_original_index": original,
            "source_connection_name": str(source["name"]),
            "normal_cell": str(reference["normal_cell"]),
            "local_dof": int(reference["source_spring_local_dof"]),
            "first": owner["first"],
            "second": "floor",
            "point": _vector(reference["owner_floorpoint_xyz_mm"]).tolist(),
            "first_point": _vector(reference["owner_floorpoint_xyz_mm"]).tolist(),
            "second_point": _vector(reference["owner_floorpoint_xyz_mm"]).tolist(),
            "force_on_first_xyz_n": force.tolist(),
            "force_on_second_xyz_n": (-force).tolist(),
            "force_rounding_radius_xyz_n": force_radius.tolist(),
            "raw_reference_rf_N": raw_rf,
            "reference_rf_rounding_radius_N": rf_radius,
            "transferred_source_load_N": source_load,
            "recovered_physical_tangent_reaction_N": recovered,
            "owner_tangent_basis_global_xyz": basis.tolist(),
            "numerical_spring_ground_counted": False,
        })
    if len(rows) != contract["active_tangent_row_count"]:
        raise ResponseAuditError("Selected exact-floor reaction recovery count differs from the pinned active mask")
    return rows


def _inactive_zero_actions(contract: dict[str, Any], state: dict[str, Any]) -> list[dict[str, Any]]:
    by_original = {
        i: row for i, row in enumerate(
            row for row in contract["source_rows"]
            if row["intended_law"] == "floor_tangent_all_bearing_hypothesis"
        )
    }
    inactive_nodes = {
        int(row["source_row_original_index"]): row
        for row in contract["inactive_output_nodes"]
    }
    actions = []
    for index in contract["inactive_indices"]:
        source = by_original[index]
        carryover = inactive_nodes[index]
        node = int(carryover["node"])
        if node not in state["rf"]:
            raise ResponseAuditError(f"Inactive scalar output-only RF is missing at original row {index}")
        rf = np.asarray(state["rf"][node], dtype=float)
        radius = np.asarray(state["rf_radius"][node], dtype=float)
        guard = 32.0 * np.finfo(float).eps * np.maximum(1.0, np.abs(rf))
        zero_rf = bool(np.all(np.abs(rf) <= radius + guard))
        if not zero_rf:
            raise ResponseAuditError(f"Inactive output-only scalar has nonzero native RF at original row {index}")
        owner = source["physical_owner"]
        local_dof = int(source["dof"])
        basis = _vector(owner["force_basis"][local_dof - 1])
        cell = str(source["floor_normal_gate"])
        row_id = f"{cell}_friction/local-dof-{local_dof}"
        if index in contract["floor_by_original"]:
            raise ResponseAuditError(f"Inactive tangent row unexpectedly has an exact reference: {index}")
        actions.append({
            "name": "inactive-floor-zero/" + row_id,
            "source_row_id": row_id,
            "source_spring_group": str(source["group"]),
            "source_inventory_row_index": contract["source_index_by_group"][str(source["group"])],
            "source_row_original_index": index,
            "source_connection_name": str(source["name"]),
            "normal_cell": cell,
            "local_dof": local_dof,
            "first": owner["first"],
            "second": "floor",
            "point": _vector(owner["point"]).tolist(),
            "force_on_first_xyz_n": [0.0, 0.0, 0.0],
            "force_on_second_xyz_n": [0.0, 0.0, 0.0],
            "force_rounding_radius_xyz_n": [0.0, 0.0, 0.0],
            "native_reference_or_tangent_equation_present": False,
            "native_tangent_spring_present": False,
            "isolated_scalar_output_node": node,
            "carryover_rf_N": rf.tolist(),
            "carryover_rf_rounding_radius_N": radius.tolist(),
            "carryover_rf_interval_contains_zero": zero_rf,
            "reason": "Released floor tangent row: no reference/equation/spring in the selected input; its paired normal is strictly separated at every reported increment.",
        })
    if len(actions) != contract["inactive_tangent_row_count"]:
        raise ResponseAuditError("Inactive exact-floor zero-action inventory differs from the pinned mask")
    return actions


def _strict_normal_branch_check(binding: dict[str, Any], check: dict[str, Any],
                                state: dict[str, Any], contract: dict[str, Any],
                                selected: bool) -> dict[str, Any]:
    q = float(check["q_relative_projection_mm"])
    q_radius = float(check["q_relative_projection_radius_mm"])
    elongation = float(check["geometric_spring_elongation_mm"])
    q_node, ground = map(int, binding["springa_nodes"])
    axis = _vector(binding["numerical_axis_global_xyz"])
    q_vector = np.asarray(state["u"][q_node]) - np.asarray(state["u"][ground])
    q_vector_radius = np.asarray(state["u_radius"][q_node]) + np.asarray(state["u_radius"][ground])
    current_vector = (np.asarray(contract["emitted_nodes"][q_node])
                      - np.asarray(contract["emitted_nodes"][ground]) + q_vector)
    current_length = float(np.linalg.norm(current_vector))
    initial_length = float(check["actual_initial_spring_length_mm"])
    geometry_guard = float(check["geometric_length_subtraction_arithmetic_guard_mm"])
    current_axis = current_vector / current_length if current_length > 0.0 else axis
    geometric_radius = float(np.abs(current_axis) @ q_vector_radius) + geometry_guard
    low, high = elongation - geometric_radius, elongation + geometric_radius
    force_interval = list(map(float, check["native_table_force_interval_N"]))
    force_value = float(check["native_table_force_N_from_actual_dd_minus_dd0"])
    internal = float(check["native_endpoint_internal_force_N"])
    internal_radius = float(check["native_endpoint_internal_radius_N"])
    guard_n = float(check["native_endpoint_force_arithmetic_guard_N"])
    rf_containing_zero = True
    for node in (q_node, ground):
        for dof in range(3):
            if abs(float(state["rf"][node][dof])) > float(state["rf_radius"][node][dof]) + guard_n:
                rf_containing_zero = False
    strict_selected = q - q_radius > 0.0 and low > 0.0 and force_interval[0] > 0.0 and internal - internal_radius > 0.0
    strict_inactive = q + q_radius < 0.0 and high < 0.0 and force_interval == [0.0, 0.0]
    inactive_rf_zero = strict_inactive and rf_containing_zero
    if selected and not strict_selected:
        raise ResponseAuditError(f"Selected floor normal is not strictly positive after rounding: {binding['group']}")
    if not selected and not inactive_rf_zero:
        raise ResponseAuditError(f"Inactive floor normal is not strictly separated with zero endpoint RF: {binding['group']}")
    return {
        "normal_cell": str(binding["name"]),
        "source_group": str(binding["group"]),
        "selected_bearing": selected,
        "inactive_separated": not selected,
        "projected_q_mm": q,
        "projected_q_rounding_radius_mm": q_radius,
        "geometric_elongation_mm": elongation,
        "geometric_elongation_interval_mm": [low, high],
        "geometric_length_arithmetic_guard_mm": geometry_guard,
        "native_table_force_N": force_value,
        "native_table_force_interval_N": force_interval,
        "native_endpoint_internal_force_N": internal,
        "native_endpoint_internal_interval_N": [internal - internal_radius, internal + internal_radius],
        "both_endpoint_rf_intervals_contain_zero": rf_containing_zero,
        "strictly_positive_after_rounding": strict_selected,
        "strictly_separated_with_zero_rf_after_rounding": inactive_rf_zero,
        "no_inactive_tangent_restraint_or_reaction_assigned": not selected,
    }


def audit_record(record: dict[str, Any], data: str, deck: str,
                 case_context: dict[str, Any]) -> dict[str, Any]:
    """Original strict no-injection path; its input validation remains unchanged."""
    contract = _validate_model(record, deck, case_context)
    return _audit_record_with_contract(record, data, deck, contract)


def audit_record_with_validated_contract(
    record: dict[str, Any], data: str, deck: str, *, validated_contract: Any,
    model_path: Path, deck_path: Path, contract_mode: str,
) -> dict[str, Any]:
    """Run the unchanged physical audit using only the sealed sensitivity contract.

    `contract_mode` is limited to an exact baseline replay or the one approved
    two-tie variant. The contract object authenticates the exact serialized
    model/deck and refuses arbitrary dictionaries or unlisted overrides.
    """
    if _sha(PINNED_711_RESPONSE) != PINNED_711_RESPONSE_SHA256:
        raise ResponseAuditError("Pinned 711 response wrapper changed")
    if _sha(STABLE_AUDIT) != STABLE_AUDIT_SHA256:
        raise ResponseAuditError("Pinned 711 recovery kernel changed")
    if contract_mode == "baseline_replay":
        builder_name = "build_baseline_response_core_contract"
    elif contract_mode == "approved_sensitivity_variant":
        builder_name = "build_response_core_contract"
    else:
        raise ResponseAuditError("Unsupported validated response contract mode")
    validator = _load_sensitivity_validator()
    if (type(validated_contract) is not validator.ValidatedSensitivityContract
            or getattr(validated_contract, "_seal", None) is not validator._CONTRACT_SEAL):
        raise ResponseAuditError("A validator-produced sealed sensitivity contract is required")
    builder = getattr(validated_contract, builder_name, None)
    if not callable(builder):
        raise ResponseAuditError("The pinned sensitivity validator lacks the required contract builder")
    try:
        contract = builder(record, deck, model_path=model_path, deck_path=deck_path)
    except Exception as error:
        raise ResponseAuditError(f"Sensitivity contract authentication failed: {error}") from error
    if not isinstance(contract, dict) or not isinstance(contract.get("bindings"), list):
        raise ResponseAuditError("Validated response contract has an unsupported core shape")
    if contract_mode == "approved_sensitivity_variant":
        authority = contract.get("sensitivity_override_authority")
        if (not isinstance(authority, dict)
                or authority.get("variant_model_sha256") != _sha(model_path)
                or authority.get("variant_deck_sha256") != _sha(deck_path)
                or len(authority.get("approved_overrides", [])) != 2):
            raise ResponseAuditError("Validated sensitivity authority is incomplete or mismatched")
    elif "sensitivity_override_authority" in contract:
        raise ResponseAuditError("Baseline replay contract unexpectedly contains a sensitivity override")
    contract["_sensitivity_contract_mode"] = contract_mode
    return _audit_record_with_contract(record, data, deck, contract)


def _audit_record_with_contract(
    record: dict[str, Any], data: str, deck: str, contract: dict[str, Any],
) -> dict[str, Any]:
    """The 711 physical audit body, with only its contract acquisition factored out."""
    parsed = parse_native_blocks(data)
    expected_nodes = set(map(int, record["nodes"]))
    if not parsed:
        raise ResponseAuditError("Native DAT contains no accepted output increments")
    for time, state in parsed.items():
        if set(state["u"]) != expected_nodes or set(state["rf"]) != expected_nodes:
            raise ResponseAuditError(f"Native U/RF node set is incomplete at time {time}")

    springs = contract["springs"]
    bindings = contract["bindings"]
    linear_names = {str(row["name"]) for row in springs}
    nonlinear_names = {str(row["name"]) for row in bindings}
    if linear_names & nonlinear_names:
        raise ResponseAuditError("Physical owner name is reused by bilateral and unilateral carriers")
    owners: dict[str, dict[str, Any]] = {}
    source_ids: dict[str, list[str]] = defaultdict(list)
    source_inventory_refs: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for binding in bindings:
        name = str(binding["name"])
        owner = binding["physical_owner"]
        if record["connection_ownership"].get(name) != owner:
            raise ResponseAuditError(f"SPRINGA physical owner changed at {name}")
        owners[name] = owner
        source = contract["source_by_group"][str(binding["group"])]
        source_ids[name].append(str(binding["source_row_id"]))
        source_inventory_refs[name].append({
            "source_inventory_row_index": int(binding["source_inventory_row_index"]),
            "source_row_id": str(binding["source_row_id"]),
            "source_connection_name": str(source["name"]),
            "intended_law": str(source["intended_law"]),
        })
    for spring in springs:
        name = str(spring["name"])
        owners[name] = record["connection_ownership"][name]
        source = contract["source_by_group"][str(spring["group"])]
        source_ids[name].append(str(spring["source_row_id"]))
        source_inventory_refs[name].append({
            "source_inventory_row_index": int(spring["source_inventory_row_index"]),
            "source_row_id": str(spring["source_row_id"]),
            "source_connection_name": str(source["name"]),
            "intended_law": str(source["intended_law"]),
        })

    body_union = set().union(*contract["physical_body_nodes"].values())
    spring2_endpoints = {int(node) for row in springs for node in row["nodes"]}
    all_mpc_pass = all_bilateral_pass = all_springa_pass = True
    all_complementarity_pass = all_raw_balance_pass = all_interval_balance_pass = True
    reports: list[dict[str, Any]] = []
    normal_names = {
        str(row["name"]) for row in contract["source_rows"]
        if row.get("role") == "floor_normal" and row.get("intended_law") == "compression_only"
    }
    if len(normal_names) != NORMAL_CELL_COUNT:
        raise ResponseAuditError("Expected exactly 100 source floor normal carriers")
    normal_binding_by_name = {str(row["name"]): row for row in bindings if row["group"] in contract["source_by_group"]}
    if not normal_names <= set(normal_binding_by_name):
        raise ResponseAuditError("A source floor normal lacks its unchanged SPRINGA binding")

    for time, state in parsed.items():
        scale = load_scale(time, contract["total_time"])
        mpc = audit_all_mpcs(record["equations"], state)
        all_mpc_pass &= bool(mpc["passed"])
        local_vectors: dict[str, np.ndarray] = defaultdict(lambda: np.zeros(3))
        local_radii: dict[str, np.ndarray] = defaultdict(lambda: np.zeros(3))
        spring2_checks = []
        occupied_endpoint_dofs: set[tuple[int, int]] = set()
        for spring in springs:
            first, second = map(int, spring["nodes"])
            dof = int(spring["dof"])
            for node in (first, second):
                key = (node, dof)
                if key in occupied_endpoint_dofs:
                    raise ResponseAuditError(f"Retained SPRING2 endpoint DOF is shared: {key}")
                occupied_endpoint_dofs.add(key)
            force, radius, check = audit_linear_spring(spring, state)
            local_vectors[str(spring["name"])][dof - 1] += force
            local_radii[str(spring["name"])][dof - 1] += radius
            spring2_checks.append(check)
        bilateral_pass = all(row["rf_action_reaction_passed"] and row["rf_kdu_intervals_intersect"]
                             for row in spring2_checks)
        all_bilateral_pass &= bilateral_pass

        springa_checks = []
        endpoint_nodes: set[int] = set()
        q_endpoint_dofs: set[tuple[int, int]] = set()
        normal_checks = []
        current_bearing: set[str] = set()
        current_inactive: set[str] = set()
        for binding in bindings:
            q_node, ground = map(int, binding["springa_nodes"])
            for node in (q_node, ground):
                if node in body_union or node in spring2_endpoints:
                    raise ResponseAuditError(f"SPRINGA numerical endpoint overlaps a physical/SPRING2 node: {node}")
                if node in endpoint_nodes:
                    raise ResponseAuditError(f"SPRINGA numerical node is shared across carriers: {node}")
                endpoint_nodes.add(node)
            for dof in (1, 2, 3):
                for node in (q_node, ground):
                    key = (node, dof)
                    if key in q_endpoint_dofs:
                        raise ResponseAuditError(f"SPRINGA numerical endpoint DOF is shared: {key}")
                    q_endpoint_dofs.add(key)
            source = contract["source_by_group"][str(binding["group"])]
            force, radius, check = audit_springa(binding, source, state, contract["emitted_nodes"])
            local_vectors[str(binding["name"])][0] += force
            local_radii[str(binding["name"])][0] += radius
            if str(binding["name"]) in normal_names:
                is_selected = str(binding["name"]) in contract["selected_cells"]
                normal = _strict_normal_branch_check(binding, check, state, contract, is_selected)
                if is_selected:
                    current_bearing.add(str(binding["name"]))
                else:
                    current_inactive.add(str(binding["name"]))
                normal_checks.append(normal)
                check["strictly_positive_floor_normal_after_rounding"] = is_selected and normal["strictly_positive_after_rounding"]
                check["strictly_separated_floor_normal_with_zero_rf_after_rounding"] = (
                    not is_selected and normal["strictly_separated_with_zero_rf_after_rounding"]
                )
            springa_checks.append(check)
        if current_bearing != contract["selected_cells"] or current_inactive != contract["inactive_cells"]:
            raise ResponseAuditError(f"Output increment {time} changed the selected floor normal active set")
        complementarity = (
            len(normal_checks) == NORMAL_CELL_COUNT
            and sum(bool(row["strictly_positive_after_rounding"]) for row in normal_checks) == contract["selected_cell_count"]
            and sum(bool(row["strictly_separated_with_zero_rf_after_rounding"]) for row in normal_checks) == contract["inactive_cell_count"]
        )
        all_complementarity_pass &= complementarity
        springa_pass = all(row["table_force_interval_intersects_native_rf"]
                           and row["native_endpoint_action_reaction_passed"]
                           and row["inside_table_domain_including_rounding"] for row in springa_checks)
        all_springa_pass &= springa_pass

        mapped = map_physical_forces(
            {"springs": [], "connection_ownership": owners},
            {"connector_forces": {
                name: {"force_on_first_xyz_n": vector.tolist()}
                for name, vector in local_vectors.items()
            }}, precision=None,
        )
        radii_by_public: dict[str, np.ndarray] = defaultdict(lambda: np.zeros(3))
        for name, owner in owners.items():
            radius = local_radii.get(name, np.zeros(3))
            if "force_basis" in owner:
                radius = np.abs(np.asarray(owner["force_basis"], dtype=float).T) @ radius
            elif "scalar_normal" in owner:
                radius = radius[0] * np.abs(np.asarray(owner["scalar_normal"], dtype=float))
            else:
                raise ResponseAuditError(f"Physical owner lacks a force basis: {name}")
            radii_by_public[str(owner.get("connector_name", name))] += radius
        for name, row in mapped.items():
            row["force_rounding_radius_xyz_n"] = radii_by_public[name].tolist()
            row["force_precision_basis"] = "Native RF token half-last-place intervals propagated through the unchanged source force basis."
        _stable._attach_source_ids(mapped, owners, source_ids, source_inventory_refs)

        active_floor_rows = _audit_selected_floor_rows(contract, record, state, scale)
        inactive_zero_rows = _inactive_zero_actions(contract, state)
        inactive_tangent_zero_pass = all(
            row["native_reference_or_tangent_equation_present"] is False
            and row["native_tangent_spring_present"] is False
            and row["carryover_rf_interval_contains_zero"] is True
            for row in inactive_zero_rows
        )
        balances = balance_physical_state(record, contract, mapped, active_floor_rows, scale)
        global_balance = balances["global_equilibrium"]
        body_balances = balances["body_equilibrium"]
        raw_balance = global_balance["printed_resultants_passed"] and all(
            row["printed_resultants_passed"] for row in body_balances.values()
        )
        interval_balance = global_balance["interval_resultants_passed"] and all(
            row["interval_resultants_passed"] for row in body_balances.values()
        )
        all_raw_balance_pass &= raw_balance
        all_interval_balance_pass &= interval_balance
        reports.append({
            "time": time,
            "load_factor": scale,
            "all_mpc_equations": mpc,
            "mpc_interval_checks_passed": bool(mpc["passed"]),
            "retained_bilateral_component_count": len(spring2_checks),
            "retained_bilateral_checks_passed": bilateral_pass,
            "retained_bilateral_spring2_components": spring2_checks,
            "springa_component_count": len(springa_checks),
            "springa_law_checks_passed": springa_pass,
            "springa_components": springa_checks,
            "floor_normal_complementarity": {
                "selected_bearing_cell_count": sum(row["selected_bearing"] for row in normal_checks),
                "inactive_separated_cell_count": sum(row["inactive_separated"] for row in normal_checks),
                "selected_cell_ids": sorted(current_bearing),
                "inactive_cell_ids": sorted(current_inactive),
                "checks": normal_checks,
            },
            "selected_floor_complementarity_passed": complementarity,
            "inactive_floor_tangent_no_restraint_or_reaction_passed": inactive_tangent_zero_pass,
            "physical_connection_forces": mapped,
            "exact_floor_tangent_reactions": active_floor_rows,
            "inactive_floor_tangent_zero_actions": inactive_zero_rows,
            "physical_balance": balances,
            "raw_balance_passed": raw_balance,
            "rounding_interval_balance_passed": interval_balance,
        })

    if not math.isclose(reports[-1]["load_factor"], 1.0, rel_tol=0.0, abs_tol=1.0e-8):
        raise ResponseAuditError("Native response does not contain the full load-factor-one state")
    gates = {
        "mpc_interval_checks_passed": all(row["mpc_interval_checks_passed"] for row in reports),
        "springa_law_checks_passed": all(row["springa_law_checks_passed"] for row in reports),
        "retained_bilateral_checks_passed": all(row["retained_bilateral_checks_passed"] for row in reports),
        "selected_floor_complementarity_passed": all(row["selected_floor_complementarity_passed"] for row in reports),
        "inactive_floor_tangent_no_restraint_or_reaction_passed": all(
            row["inactive_floor_tangent_no_restraint_or_reaction_passed"] for row in reports
        ),
        "raw_body_and_global_balance_passed": all(row["raw_balance_passed"] for row in reports),
        "rounding_interval_body_and_global_balance_passed": all(row["rounding_interval_balance_passed"] for row in reports),
    }
    if not all(gates.values()):
        failed = [key for key, passed in gates.items() if not passed]
        raise ResponseAuditError("Selected-floor numerical response gates failed: " + ", ".join(failed))
    report = {
        "schema": OUTPUT_SCHEMA,
        "status": "PASS_SELECTED_FLOOR_PHYSICAL_RESPONSE_AUDIT_ONLY",
        "candidate": record["candidate"],
        "geometry_revision_id": record["geometry_revision_id"],
        "case_id": contract["case_id"],
        "branch_id": BRANCH_ID,
        "branch_scope": f"Monotone zero-gap reference branch with the explicitly pinned {contract['selected_cell_count']} selected bearing cells; not a release/recontact or uniqueness result.",
        "native_solve_launched_by_postprocessor": False,
        "native_output_consumed": True,
        "qualified_for_design": False,
        "mechanical_acceptance": False,
        "joint_demand_accepted": False,
        "floor_capacity_established": False,
        "friction_qualified": False,
        "historical_c11_forces_or_active_states_used": False,
        **gates,
        "source_inventory": contract["inventory_summary"],
        "case_context_provenance": contract.get("case_context_provenance"),
        "source_load_normalization_audit": record["source_load_normalization_audit"],
        "source_load_emission_audit": record["source_load_emission_audit"],
        "floor_source_load_transfer": {
            "formula": "F_ref=(S^-1)^T F_pivot reconstructed from emitted equation coefficients and emitted physical pivot CLOADs; R_tangent=RF(reference,1)-F_ref*load_factor.",
            "active_reference_rows": contract["active_tangent_row_count"],
            "inactive_original_rows": contract["inactive_tangent_row_count"],
            "emitted_transfer_max_abs_difference_N": contract["floor_load_correction_max_abs_error_N"],
            "serialized_coefficient_omission_bound_N": contract["floor_load_transfer_omission_bound_N"],
            "numerical_spring_grounds_counted_as_support": False,
            "inactive_rows_have_reference_equation_or_native_tangent": False,
        },
        "recovery_summary": {
            **gates,
            "native_increment_count": len(reports),
            "retained_bilateral_spring2_component_checks": sum(len(row["retained_bilateral_spring2_components"]) for row in reports),
            "nonlinear_springa_component_checks": sum(len(row["springa_components"]) for row in reports),
            "active_exact_floor_tangent_reaction_rows_per_increment": contract["active_tangent_row_count"],
            "inactive_floor_tangent_rows_per_increment": contract["inactive_tangent_row_count"],
            "all_original_projection_and_mpc_equations_checked": True,
            "all_springa_table_domains_checked": True,
            "all_unilateral_table_endpoint_pairs_checked": True,
            "all_retained_bilateral_laws_checked": True,
            "all_100_floor_normals_checked_at_every_increment": True,
            "selected_floor_complementarity_passed": gates["selected_floor_complementarity_passed"],
            "physical_body_count": 50,
            "floor_branch_screen_sha256": contract["screen_sha256"],
            "case_record_sha256": contract["case_record_sha256"],
            "legacy_linear_auditor_reused": False,
            "numerical_grounds_counted_as_physical_support": False,
        },
        "source_input_model_json_sha256": None,
        "source_input_deck_sha256": hashlib.sha256(deck.encode("utf-8")).hexdigest(),
        "native_data_sha256": hashlib.sha256(data.encode("utf-8")).hexdigest(),
        "source_model_record_canonical_sha256": _canonical_sha(record),
        "increments": reports,
        "limits": [
            f"One explicitly bound {contract['case_id']} case and one proportional load ramp only; no other load case is inferred.",
            f"The floor support is conditional on the exact {contract['selected_cell_count']}/{contract['inactive_cell_count']} mask remaining strictly bearing/separated in every accepted increment.",
            "The monotone zero-gap branch does not establish recontact, branch uniqueness, floor friction, or floor qualification.",
            f"The {contract['inactive_tangent_row_count']} released tangent rows receive no physical force action and are not anchors or floor-restraint reactions.",
            "The 100 mm SPRINGA endpoints and fixed numerical grounds are numerical devices; their RF values are excluded from physical balances.",
            "No capacity, resistance, actual material/hardware inspection, fabrication approval, floor anchorage, or climbing release is established.",
            "The 92 new block bolt axes and 12 retained leg/runner axes remain separately identified; no prior C11 forces or active states are reused.",
        ],
    }
    if contract.get("_sensitivity_contract_mode") is not None:
        report["case_context_provenance"] = None
        report["sensitivity_input_contract_provenance"] = contract["sensitivity_input_contract_provenance"]
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("case_context_json", type=Path)
    parser.add_argument("model_json", type=Path)
    parser.add_argument("model_dat", type=Path)
    parser.add_argument("model_inp", type=Path)
    parser.add_argument("execution_json", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    case_context = json.loads(args.case_context_json.read_text())
    case_context_sha256 = _sha(args.case_context_json)
    record = json.loads(args.model_json.read_text())
    data, deck = args.model_dat.read_text(), args.model_inp.read_text()
    provenance = _validate_execution(args.model_json, args.model_dat, args.model_inp,
                                     args.execution_json, data, case_context)
    report = audit_record(record, data, deck, case_context)
    report["source_input_model_json_sha256"] = _sha(args.model_json)
    report["source_input_model_json_path"] = str(args.model_json.resolve())
    report["source_input_deck_path"] = str(args.model_inp.resolve())
    report["native_data_path"] = str(args.model_dat.resolve())
    report["case_context_path"] = str(args.case_context_json.resolve())
    report["case_context_sha256"] = case_context_sha256
    report["terminal_execution_provenance"] = provenance
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, allow_nan=False) + "\n")
    print(report["status"])
if __name__ == "__main__":
    main()
