"""Screen one terminal a12-forward selected-floor output; do not solve or adopt forces."""
from __future__ import annotations

import hashlib
import importlib.util
import json
from collections import Counter
from pathlib import Path
from typing import Any

import numpy as np

ROOT = Path(__file__).resolve().parents[5]
BASE = Path("docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28")
HERE = ROOT / BASE / "current-springa-a12-forward-selected-floor-screen-attempt01"
RUN = BASE / "current-springa-selected-floor-a12-forward-attempt01"
CASE_CONTEXT = RUN / "case-context.json"
AUDITOR = BASE / "current-springa-case-bound-response-audit-attempt01/response_audit.py"
STABLE_RECOVERY = BASE / "current-springa-frame-response-audit-attempt01/response_audit.py"
SOURCE_SCREEN = BASE / "current-springa-a12-forward-floor-screen-attempt01/screen.json"

PINNED = {
    str(RUN / "model.json"): "50edee6194d3abdb758e8e7eb17f361b10cae7fc839dcedfa9f24f070d25324b",
    str(RUN / "model.inp"): "401930f909d503e388a68f3eade5ebfaa1e228d5bc48712a217e170fe8bef553",
    str(RUN / "model.dat"): "83982a4eb95d7201b05bf2dc895974ee2e3e4cd32aae7ab6104f8bd166bd93ad",
    str(RUN / "execution.json"): "65d0b804abbba9748170519605d75a09009224985ce90ce82709a12a001a1e3b",
    str(RUN / "freeze.json"): "5c0ff289a1ee32254160e3db0d7f9276de409f525cb665d59c17186b2586b45e",
    str(CASE_CONTEXT): "fd756639f097509bc4da18da9aff552c7c56f45d4717e7a19ac08abbff519da5",
    str(RUN / "parent-readiness-review.json"): "13c5876b7315fdffa9f27c23001725d4e655034f51570893e59dd8fb7a01ad96",
    str(RUN / "parent-serialized-input-audit.json"): "408c65a833fbb1b06f574323611ad3a2d14a3161682412801c2ae9c92c67aacf",
    str(RUN / "parent-case-context-check.json"): "66444fd12e5d422943a9999559437e1555304068b70f54a08e1b6eb300ec0098",
    str(RUN / "authorization.json"): "b1f21a63a60a5669bd0f3858fef67d22d391ba4fd0dfa0a0d250f63ff374e6ec",
    str(SOURCE_SCREEN): "a4abd064c43de600d857d7f3adcae3fbae9690c3b8bb92dbf8cb7bd77ee809b9",
    str(BASE / "current-six-case-source-load-register-attempt01/register.json"): "7a638a49fc5086b4d5fed52148286a300b8b271f7d380b1a131ea8e17b094508",
    str(AUDITOR): "df1ed0eedb62ed3657a05a6d679d105e15e63b5ee18b999a731adab190b1b479",
    str(STABLE_RECOVERY): "b20dae471e9826a55c40bbeed028375e6d082913e3f3917665514f2763ddd49c",
    str(BASE / "current-springa-case-bound-floor-input-adapter-attempt01/audit.json"): "45bbd100bf9638d09eb741da1c3be457dbba68ca63261836e539e9fae2de3f6d",
}


class ScreenError(RuntimeError):
    pass


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def jsonable(value: Any) -> Any:
    if isinstance(value, np.generic):
        return value.item()
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, dict):
        return {str(key): jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [jsonable(item) for item in value]
    if isinstance(value, set):
        return [jsonable(item) for item in sorted(value, key=str)]
    return value


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(jsonable(value), indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8")


def load_auditor():
    observed = sha(ROOT / AUDITOR)
    if observed != PINNED[str(AUDITOR)]:
        raise ScreenError(f"Pinned case-bound response auditor changed: {observed}")
    spec = importlib.util.spec_from_file_location("case_bound_selected_floor_response_audit", ROOT / AUDITOR)
    if spec is None or spec.loader is None:
        raise ScreenError("Could not import the pinned case-bound response auditor")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def interval_row(audit: Any, binding: dict[str, Any], check: dict[str, Any], state: dict[str, Any], contract: dict[str, Any], original_selected: bool) -> dict[str, Any]:
    positive_result = None
    separated_result = None
    positive_error = None
    separated_error = None
    try:
        positive_result = audit._strict_normal_branch_check(binding, check, state, contract, True)
    except audit.ResponseAuditError as error:
        positive_error = str(error)
    try:
        separated_result = audit._strict_normal_branch_check(binding, check, state, contract, False)
    except audit.ResponseAuditError as error:
        separated_error = str(error)

    if positive_result is not None and separated_result is not None:
        raise ScreenError(f"Normal carrier passed mutually exclusive positive and separation screens: {binding['group']}")
    if positive_result is not None:
        classification = "STRICTLY_POSITIVE"
        result = positive_result
    elif separated_result is not None:
        classification = "STRICTLY_SEPARATED_WITH_ZERO_ENDPOINT_RF"
        result = separated_result
    else:
        classification = "INTERVAL_AMBIGUOUS_OR_NOT_COMPLEMENTARY"
        result = {
            "normal_cell": str(binding["name"]),
            "source_group": str(binding["group"]),
            "projected_q_mm": float(check["q_relative_projection_mm"]),
            "projected_q_rounding_radius_mm": float(check["q_relative_projection_radius_mm"]),
            "native_table_force_N": float(check["native_table_force_N_from_actual_dd_minus_dd0"]),
            "native_table_force_interval_N": list(map(float, check["native_table_force_interval_N"])),
            "native_endpoint_internal_force_N": float(check["native_endpoint_internal_force_N"]),
            "native_endpoint_internal_interval_N": [
                float(check["native_endpoint_internal_force_N"] - check["native_endpoint_internal_radius_N"]),
                float(check["native_endpoint_internal_force_N"] + check["native_endpoint_internal_radius_N"]),
            ],
        }

    q_node, ground = map(int, binding["springa_nodes"])
    guard_n = float(check["native_endpoint_force_arithmetic_guard_N"])
    endpoint_rf = []
    for role, node in (("q_endpoint", q_node), ("numerical_ground_endpoint", ground)):
        dofs = []
        for dof in range(3):
            raw = float(state["rf"][node][dof])
            radius = float(state["rf_radius"][node][dof])
            dofs.append({
                "dof": dof + 1,
                "raw_rf_N": raw,
                "rounding_radius_N": radius,
                "interval_N": [raw - radius, raw + radius],
                "contains_zero_with_pinned_guard": abs(raw) <= radius + guard_n,
            })
        endpoint_rf.append({"role": role, "node": node, "components": dofs})

    return {
        **result,
        "classification": classification,
        "original_35_cell_proposal_selected": original_selected,
        "endpoint_rf_intervals": endpoint_rf,
        "endpoint_rf_arithmetic_guard_N": guard_n,
        "positive_test_failure_detail": positive_error,
        "separation_test_failure_detail": separated_error,
        "physical_force_adoption": False,
    }


def produce() -> dict[str, Any]:
    source_hashes = {}
    for relative, expected in PINNED.items():
        observed = sha(ROOT / relative)
        if observed != expected:
            raise ScreenError(f"Source pin mismatch for {relative}: expected {expected}, observed {observed}")
        source_hashes[relative] = observed

    packet = ROOT / RUN
    model_path, deck_path, data_path = packet / "model.json", packet / "model.inp", packet / "model.dat"
    execution_path = packet / "execution.json"
    model = json.loads(model_path.read_text())
    deck = deck_path.read_text()
    data = data_path.read_text()
    context = json.loads((ROOT / CASE_CONTEXT).read_text())
    execution = json.loads(execution_path.read_text())
    auditor = load_auditor()
    terminal_provenance = auditor._validate_execution(model_path, data_path, deck_path, execution_path, data, context)
    contract = auditor._validate_model(model, deck, context)
    if execution.get("run_id") != "springa-selected-a12-forward-attempt01":
        raise ScreenError("Terminal output does not match the pinned selected-floor a12-forward run")
    if model.get("case_id") != "a12-forward" or len(contract["selected_cells"]) != 35:
        raise ScreenError("The terminal run is not bound to the original 35-cell a12-forward proposal")
    parsed = auditor.parse_native_blocks(data)
    expected_nodes = set(map(int, model["nodes"]))
    if not parsed or any(set(state["u"]) != expected_nodes or set(state["rf"]) != expected_nodes for state in parsed.values()):
        raise ScreenError("Terminal output is missing complete nodal U/RF blocks")

    normals = [binding for binding in contract["bindings"] if binding.get("physical_owner", {}).get("role") == "floor_normal"]
    if len(normals) != 100 or {str(binding["name"]) for binding in normals} != set(contract["selected_cells"] | contract["inactive_cells"]):
        raise ScreenError("The selected input does not map the complete 100-source-cell normal inventory")
    original_selected = set(map(str, contract["selected_cells"]))
    original_inactive = set(map(str, contract["inactive_cells"]))
    rows_by_time = []
    for time, state in parsed.items():
        cell_rows = []
        for binding in sorted(normals, key=lambda row: str(row["name"])):
            source = contract["source_by_group"].get(str(binding["group"]))
            if source is None or source.get("role") != "floor_normal" or source.get("name") != binding.get("name"):
                raise ScreenError(f"Native normal binding is not source-inventory bound: {binding['group']}")
            _, _, check = auditor.audit_springa(binding, source, state, contract["emitted_nodes"])
            classified = interval_row(auditor, binding, check, state, contract, str(binding["name"]) in original_selected)
            classified.update({
                "source_row_id": str(binding["source_row_id"]),
                "source_inventory_row_index": int(binding["source_inventory_row_index"]),
                "physical_owner": binding["physical_owner"],
                "source_force_law": binding["force_law"],
                "load_factor": float(auditor.load_scale(time, contract["total_time"])),
                "table_domain_mm": list(map(float, binding["table_domain_mm"])),
                "native_law_check": check,
            })
            cell_rows.append(classified)
        counts = Counter(str(row["classification"]) for row in cell_rows)
        positive = {str(row["normal_cell"]) for row in cell_rows if row["classification"] == "STRICTLY_POSITIVE"}
        separated = {str(row["normal_cell"]) for row in cell_rows if row["classification"] == "STRICTLY_SEPARATED_WITH_ZERO_ENDPOINT_RF"}
        ambiguous = {str(row["normal_cell"]) for row in cell_rows if row["classification"] == "INTERVAL_AMBIGUOUS_OR_NOT_COMPLEMENTARY"}
        if len(cell_rows) != 100 or len(positive | separated | ambiguous) != 100 or positive & separated or positive & ambiguous or separated & ambiguous:
            raise ScreenError(f"Normal-law classifications do not partition all cells at t={time}")
        rows_by_time.append({
            "time": float(time),
            "load_factor": float(auditor.load_scale(time, contract["total_time"])),
            "strictly_positive_count": len(positive),
            "strictly_separated_with_zero_endpoint_rf_count": len(separated),
            "interval_ambiguous_or_noncomplementary_count": len(ambiguous),
            "strictly_positive_cells": sorted(positive),
            "strictly_separated_with_zero_endpoint_rf_cells": sorted(separated),
            "interval_ambiguous_or_noncomplementary_cells": sorted(ambiguous),
            "same_as_original_35_cell_mask": positive == original_selected and separated == original_inactive and not ambiguous,
            "rows": cell_rows,
        })

    initial_positive = set(rows_by_time[0]["strictly_positive_cells"])
    initial_separated = set(rows_by_time[0]["strictly_separated_with_zero_endpoint_rf_cells"])
    initial_ambiguous = set(rows_by_time[0]["interval_ambiguous_or_noncomplementary_cells"])
    mask_stable = all(
        set(row["strictly_positive_cells"]) == initial_positive
        and set(row["strictly_separated_with_zero_endpoint_rf_cells"]) == initial_separated
        and set(row["interval_ambiguous_or_noncomplementary_cells"]) == initial_ambiguous
        for row in rows_by_time[1:]
    )
    final_rows = {str(row["normal_cell"]): row for row in rows_by_time[-1]["rows"]}
    original_selected_lost = sorted(original_selected - initial_positive)
    original_inactive_now_positive = sorted(original_inactive & initial_positive)
    original_inactive_not_strictly_separated = sorted(original_inactive - initial_separated)
    original_selected_not_strictly_positive = sorted(original_selected - initial_positive)
    if any(set(row["strictly_positive_cells"]) != initial_positive for row in rows_by_time):
        raise ScreenError("This attempt is bounded to a stable normal-law screen; positive set changed")

    offender = final_rows.get("floor_base_floor_left_1")
    if offender is None or offender.get("source_group") != "SPR1026":
        raise ScreenError("Pinned response failure SPR1026 does not map to the expected source floor cell")
    if offender["classification"] != "STRICTLY_POSITIVE" or "floor_base_floor_left_1" not in original_inactive:
        raise ScreenError("The expected released SPR1026 compatibility failure was not reproduced")

    screen = {
        "schema": "current_case_bound_selected_floor_law_screen/v1",
        "status": "REJECTED_SELECTED_FLOOR_MASK_STRICT_COMPLEMENTARITY",
        "case_id": model["case_id"],
        "candidate": model["candidate"],
        "geometry_revision_id": model["geometry_revision_id"],
        "branch_id": model["floor_branch_metadata"]["branch_id"],
        "source_selected_floor_run_id": execution["run_id"],
        "source_selected_floor_model_sha256": PINNED[str(RUN / "model.json")],
        "source_selected_floor_deck_sha256": PINNED[str(RUN / "model.inp")],
        "source_selected_floor_execution_sha256": PINNED[str(RUN / "execution.json")],
        "source_selected_floor_terminal_data_sha256": PINNED[str(RUN / "model.dat")],
        "native_solve_executed_by_screen_producer": False,
        "terminal_native_output_consumed": True,
        "full_step_native_convergence": True,
        "all_100_normal_laws_checked_at_every_increment": True,
        "all_endpoint_rounding_intervals_checked": True,
        "conservative_method": {
            "case_bound_auditor_path": str(AUDITOR),
            "case_bound_auditor_sha256": PINNED[str(AUDITOR)],
            "stable_recovery_kernel_path": str(STABLE_RECOVERY),
            "stable_recovery_kernel_sha256": PINNED[str(STABLE_RECOVERY)],
            "law_and_interval_functions": ["audit_springa", "_strict_normal_branch_check", "parse_native_blocks"],
            "classification_rule": "Pinned strict positive or strict separated-with-zero-endpoint-RF checks are attempted unchanged; a cell is interval_ambiguous_or_noncomplementary only when neither strict result is admissible.",
            "zero_endpoint_rf_improvement_used": False,
        },
        "original_proposed_mask": {
            "selected_cell_count": len(original_selected),
            "inactive_cell_count": len(original_inactive),
            "selected_cells": sorted(original_selected),
            "inactive_cells": sorted(original_inactive),
            "screen_source_path": str(SOURCE_SCREEN),
            "screen_source_sha256": PINNED[str(SOURCE_SCREEN)],
        },
        "stable_actual_normal_law_mask": {
            "same_classification_sets_at_every_printed_increment": mask_stable,
            "strictly_positive_count": len(initial_positive),
            "strictly_separated_with_zero_endpoint_rf_count": len(initial_separated),
            "interval_ambiguous_or_noncomplementary_count": len(initial_ambiguous),
            "strictly_positive_cells": sorted(initial_positive),
            "strictly_separated_with_zero_endpoint_rf_cells": sorted(initial_separated),
            "interval_ambiguous_or_noncomplementary_cells": sorted(initial_ambiguous),
        },
        "mask_deltas_vs_original_35_cell_proposal": {
            "original_selected_cells_not_strictly_positive": original_selected_not_strictly_positive,
            "original_selected_cells_now_strictly_separated": sorted(original_selected & initial_separated),
            "original_inactive_cells_now_strictly_positive": original_inactive_now_positive,
            "original_inactive_cells_not_strictly_separated": original_inactive_not_strictly_separated,
            "original_selected_cells_still_strictly_positive": sorted(original_selected & initial_positive),
            "stable_across_all_printed_increments": mask_stable,
        },
        "offending_inactive_normal": {
            "source_group": "SPR1026",
            "cell_name": "floor_base_floor_left_1",
            "was_in_original_35_cell_proposal": False,
            "actual_classification": offender["classification"],
            "every_increment_row": [
                {"time": state["time"], "load_factor": state["load_factor"],
                 **next(row for row in state["rows"] if row["source_group"] == "SPR1026")}
                for state in rows_by_time
            ],
            "effect": "The proposed inactive branch requires strict separation with zero endpoint RF; source normal SPR1026 instead screens strictly positive at every increment.",
        },
        "proposed_mask_strictly_compatible_at_every_increment": all(row["same_as_original_35_cell_mask"] for row in rows_by_time),
        "corner_demands_usable": False,
        "physical_force_adoption": False,
        "mechanical_acceptance": False,
        "qualified_for_design": False,
        "source_sha256": source_hashes,
        "times": rows_by_time,
        "limits": [
            "This screen uses only the exact case-bound a12-forward selected-floor terminal output and does not transfer forces or masks to another case.",
            "It classifies all 100 normal carriers using the pinned conservative interval method; it does not produce accepted joint demands.",
            "The 35/65 proposed mask is rejected by the actual normal-law screen; no alternate mask is selected, assembled, or iterated here.",
            "No zero-SPC or endpoint-RF tolerance improvement, preload, friction, anchor, or floor qualification is introduced.",
            "No native solve, freeze, response ledger, or additional solver launch was created by this producer.",
        ],
        "terminal_run_provenance": terminal_provenance,
    }
    write_json(HERE / "screen.json", screen)
    write_json(HERE / "source-pins.json", {
        "schema": "current_case_bound_selected_floor_screen_source_pins/v1",
        "pinned_inputs": {key: {"sha256": value} for key, value in source_hashes.items()},
        "producer_sha256": sha(HERE / "produce.py"),
        "screen_sha256": sha(HERE / "screen.json"),
        "scope": "Read-only normal-law screen of one terminal a12-forward selected-floor output; no mask iteration or force adoption.",
    })
    (HERE / "README.md").write_text(
        "# a12-forward selected-floor normal-law screen, attempt 01\n\n"
        "This read-only packet screens all 100 unchanged SPRINGA floor-normal laws at every recorded increment of the terminal, case-bound a12-forward selected-floor run. It reuses the exact pinned `audit_springa` and `_strict_normal_branch_check` methods with their conservative printed-token interval treatment. The producer does not run CalculiX.\n\n"
        f"The original 35/65 proposal is rejected by the observed branch: across {len(rows_by_time)} recorded increments the stable normal-law mask is {len(initial_positive)} strictly positive, {len(initial_separated)} strictly separated with zero endpoint RF, and {len(initial_ambiguous)} interval ambiguous or noncomplementary. The source selected set has {len(original_selected_not_strictly_positive)} cells that no longer screen strictly positive; {len(original_inactive_now_positive)} originally inactive cells screen strictly positive, including `floor_base_floor_left_1` / `SPR1026`. Every cell’s displacement, geometric elongation, spring force, endpoint internal force, and endpoint RF intervals are recorded per increment in `screen.json`.\n\n"
        "This identifies the case-specific support incompatibility only. No replacement mask, new input, accepted force, corner demand, or solver run is included. The branch remains diagnostic and cannot support demand adoption.\n",
        encoding="utf-8",
    )
    return screen


if __name__ == "__main__":
    result = produce()
    print(json.dumps({
        "status": result["status"],
        "increments": len(result["times"]),
        "counts": [
            [row["strictly_positive_count"], row["strictly_separated_with_zero_endpoint_rf_count"], row["interval_ambiguous_or_noncomplementary_count"]]
            for row in result["times"]
        ],
        "mask_deltas": result["mask_deltas_vs_original_35_cell_proposal"],
        "offender": result["offending_inactive_normal"]["source_group"],
        "screen_sha256": sha(HERE / "screen.json"),
    }, indent=2))
