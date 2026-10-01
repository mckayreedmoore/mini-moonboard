#!/usr/bin/env python3
"""Project the refined K12 diagnostic rows into the immutable input-adapter screen contract."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[5]
SERIES = ROOT / "docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28"
CONTROL = SERIES / "current-springa-frame-k12-rear-all-bearing-attempt01"
ORIGINAL = SERIES / "current-springa-k12-rear-floor-screen-attempt01/screen.json"
REFINED_DIR = SERIES / "current-springa-k12-rear-zero-u-token-screen-attempt01"
REFINED = REFINED_DIR / "screen.json"
REFINED_PRODUCER = REFINED_DIR / "produce.py"
METHOD_DIR = SERIES / "current-springa-zero-u-token-response-audit-attempt01"
METHOD = METHOD_DIR / "stable_response_audit.py"
METHOD_WRAPPER = METHOD_DIR / "response_audit.py"
METHOD_REPLAY = METHOD_DIR / "zero_u_token_replay.json"
METHOD_REPLAY_PRODUCER = METHOD_DIR / "replay_zero_u_tokens.py"
SPC_DIR = SERIES / "current-zero-spc-displacement-interval-proof-attempt01"
SPC_PROOF = SPC_DIR / "zero_spc_replay.json"
TRANSFORMED_DIR = SERIES / "current-springa-k12-rear-zero-u-token-screen-attempt02"
TRANSFORMED_REPLAY = TRANSFORMED_DIR / "transformed_floor_coupon_replay.json"
TRANSFORMED_PRODUCER = TRANSFORMED_DIR / "replay_transformed_floor_coupon.py"
OUTPUT = Path(__file__).with_name("floor-diagnostic-screen.json")

PINS = {
    CONTROL / "model.json": "72cc39411bb92d3ee739a9b9aa9b025fe466f2b818f29feaa76a26c284366424",
    CONTROL / "model.inp": "0cdcee16de7be40e8a7a511c26f6cbf67f116d2475f76eab294fa661ee6fac68",
    CONTROL / "model.dat": "8c3c7590e11df6c8bce52e814ece2aba2f05ff24eb261517e95e74db41528807",
    CONTROL / "execution.json": "4e10033ba2a12952122ac790ae6c4dcf4a9585b936d239e86d73465be6db6ccc",
    CONTROL / "freeze.json": "161e9b8bfecb7ef4d5060db4d6fb25aeeb38df5fa4332a3ba47fbd92df70ac92",
    CONTROL / "authorization.json": "13050058f4090bb347503c64e18fad137da3ee1a8fcd24b6c5b40d56f116f670",
    CONTROL / "parent-serialized-input-audit.json": "31752ce76ff4310ae2d85327e4ea9436fc273fcfeddd025f7609e217b6533d80",
    CONTROL / "parent-terminal-assessment.json": "ee71874e16744a6942cc7ba5439916ca65c29b72cd3a1b60947e2b352ee3af1e",
    ORIGINAL: "445e809585be0efed9acbac9bd853a31de6a929c845b20b114c0ec50f843974b",
    REFINED: "2c4990ac95507208e42ec2fce4261b2d7582694861e0c31b653240a45fcf9a9e",
    REFINED_PRODUCER: "437eff3359406af12e2aad35fd20f699c9aa71c3cc5399d5370aeb669277caf0",
    METHOD: "bdcfa2dd85e152503b740a2f49bb1de6b67462565eb610ff5ee451990335a77d",
    METHOD_WRAPPER: "711fa96e8faff12dc4b21fa939ae28822be8abba65bc12a896b558f0a54bfff0",
    METHOD_REPLAY: "da1116b04390837425133af1b74fdf36fa647ecb7c181afbd49a33f0fda285c1",
    METHOD_REPLAY_PRODUCER: "6b49312429c78e04d0a70a7a428382028ac9e75ab01a69b53271d9feca91bd32",
    SPC_PROOF: "9b19ae1502bbef213a91e9f68f9aa9799e68978666726d240aa76784052fd610",
    SERIES / "current-springa-frame-response-audit-attempt01/response_audit.py":
        "b20dae471e9826a55c40bbeed028375e6d082913e3f3917665514f2763ddd49c",
    TRANSFORMED_REPLAY:
        "41d0b046435b80b06bd582d8a5948c7dd740ebfcf67c090e286fc086e7e4784b",
    TRANSFORMED_PRODUCER:
        "628ea0dad0cc76cc1a48d4a5efd674ae1ec2ea5042ac14cd9c305b96479873ba",
}


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text())


def project() -> dict[str, Any]:
    for path, expected in PINS.items():
        if expected:
            require(sha(path) == expected, f"K12 diagnostic projection pin mismatch: {path}")

    model = load(CONTROL / "model.json")
    execution = load(CONTROL / "execution.json")
    freeze = load(CONTROL / "freeze.json")
    authorization = load(CONTROL / "authorization.json")
    parent_audit = load(CONTROL / "parent-serialized-input-audit.json")
    terminal = load(CONTROL / "parent-terminal-assessment.json")
    original = load(ORIGINAL)
    refined = load(REFINED)
    require(execution.get("native_solve_executed") is True
            and execution.get("returncode") == 0
            and execution.get("container_confirmed_terminal") is True
            and execution.get("outputs_sha256", {}).get("model.dat") == sha(CONTROL / "model.dat"),
            "K12 frozen all-bearing run is not terminal and DAT-bound")
    for name in ("model.json", "model.inp"):
        require(execution.get("outputs_sha256", {}).get(name) == sha(CONTROL / name)
                and freeze.get("files_sha256", {}).get(name) == sha(CONTROL / name),
                f"K12 frozen source input changed: {name}")
    require(authorization.get("input_freeze_sha256") == sha(CONTROL / "freeze.json")
            and authorization.get("native_execution_authorized") is True
            and authorization.get("mechanical_acceptance") is False,
            "K12 authorization is not scoped to the pinned diagnostic freeze")
    require(parent_audit.get("status") == "PASS_PARENT_SERIALIZED_INPUT_AUDIT"
            and parent_audit.get("case_id") == "k12-rear"
            and parent_audit.get("frame_ready_for_native_run") is False
            and parent_audit.get("complete_joint_validated") is False,
            "K12 parent input audit is not the expected input-only result")
    require(terminal.get("status") == "REJECTED_ALL_BEARING_SUPPORT_BRANCH"
            and terminal.get("corner_demands_usable") is False,
            "K12 parent terminal assessment does not reject all-bearing support")
    require(original.get("schema") == "current_case_bound_floor_diagnostic_screen/v1"
            and original.get("status") == "REJECTED_ALL_BEARING_SUPPORT_BRANCH"
            and original.get("case_id") == "k12-rear",
            "Original K12 screen is not the preserved rejected all-bearing control")
    require(refined.get("status") == "COMPLETED_NORMAL_LAW_DIAGNOSTIC_ONLY"
            and refined.get("case_id") == "k12-rear"
            and refined.get("full_factor_response_confirmed") is True
            and refined.get("all_printed_floor_normal_laws_checked") is True
            and refined.get("all_cells_classified_strictly_every_state") is True
            and refined.get("unresolved_count_each_state") == [0] * 7,
            "Refined K12 normal-law diagnostic is not full-factor and complete")
    require(model.get("case_id") == refined["case_id"]
            and model.get("candidate") == refined["candidate"]
            and model.get("geometry_revision_id") == refined["geometry_revision_id"],
            "Refined K12 screen identity differs from frozen controls")
    require(original.get("all_printed_floor_laws_checked") is True
            and original.get("same_positive_cell_set_at_all_printed_times") is True,
            "Original all-bearing diagnostic inventory is incomplete")

    states = []
    for state in refined["states"]:
        rows = []
        for row in state["full_rows"]:
            rows.append({
                "source_group": row["source_group"],
                "cell_name": row["cell_name"],
                "physical_owner": row["physical_owner"],
                "strictly_positive_after_rounding": row["strictly_positive_after_rounding"],
                "strictly_separating_after_rounding": row["strictly_separating_after_rounding"],
                "normal_force_diagnostic_N": row["normal_force_diagnostic_N"],
                "normal_force_radius_N": row["normal_force_radius_N"],
                "table_force_interval_N": row["table_force_interval_N"],
                "q_diagnostic_mm": row["q_diagnostic_mm"],
                "q_radius_mm": row["q_radius_mm"],
                "projected_q_interval_mm": row["projected_q_interval_mm"],
                "geometric_spring_elongation_mm": row["geometric_spring_elongation_mm"],
                "geometric_spring_elongation_radius_mm": row["geometric_spring_elongation_radius_mm"],
                "geometric_spring_elongation_interval_mm": row["geometric_spring_elongation_interval_mm"],
            })
        require(len(rows) == 100, f"K12 time {state['time']} does not cover all 100 floor cells")
        positive = [row["cell_name"] for row in rows if row["strictly_positive_after_rounding"]]
        separated = [row["cell_name"] for row in rows if row["strictly_separating_after_rounding"]]
        require(len(positive) == 16 and len(separated) == 84
                and set(positive).isdisjoint(separated)
                and set(positive) | set(separated) == {row["cell_name"] for row in rows},
                f"K12 time {state['time']} is not a strict 16/84 partition")
        states.append({
            "time": state["time"],
            "bearing_count": len(positive),
            "separating_count": len(separated),
            "rows": rows,
        })
    positive_sets = [
        {row["cell_name"] for row in state["rows"] if row["strictly_positive_after_rounding"]}
        for state in states
    ]
    require(all(values == positive_sets[0] for values in positive_sets[1:]),
            "K12 positive-cell set changes across the seven printed states")
    final_rows = states[-1]["rows"]
    return {
        "schema": "current_case_bound_floor_diagnostic_screen/v1",
        "status": "REJECTED_ALL_BEARING_SUPPORT_BRANCH",
        "candidate": model["candidate"],
        "case_id": "k12-rear",
        "geometry_revision_id": model["geometry_revision_id"],
        "corner_demands_usable": False,
        "full_step_native_convergence": True,
        "all_printed_floor_laws_checked": True,
        "all_printed_times": [state["time"] for state in states],
        "same_positive_cell_set_at_all_printed_times": True,
        "diagnostic_positive_cells_at_final_time": sorted(positive_sets[-1]),
        "diagnostic_separating_cells_at_final_time": sorted(
            row["cell_name"] for row in final_rows if row["strictly_separating_after_rounding"]
        ),
        "source_sha256": {
            str((CONTROL / name).relative_to(ROOT)): sha(CONTROL / name)
            for name in ("model.json", "model.inp", "model.dat", "execution.json")
        } | {
            str((SERIES / "current-springa-frame-response-audit-attempt01/response_audit.py").relative_to(ROOT)):
            sha(SERIES / "current-springa-frame-response-audit-attempt01/response_audit.py"),
        },
        "source_evidence_sha256": {
            str(path.relative_to(ROOT)): expected for path, expected in PINS.items()
        },
        "states": states,
        "limits": [
            "This is a contract projection of the pinned refined K12 all-bearing normal-law diagnostic, not a new response audit or solver output.",
            "The status rejects the all-bearing support branch. Its 16-cell positive set is only an input proposal basis; diagnostic forces and active states are not adopted as response.",
            "No corner demand, selected support acceptance, physical floor qualification, joint acceptance, or stability finding is produced.",
            "The parser correction changes only representation radii for canonical all-zero U tokens; all native U/RF values, nonzero-U intervals, RF intervals, geometric guards, and constitutive criteria are retained.",
        ],
        "zero_u_token_method": {
            "stable_auditor_path": str(METHOD.relative_to(ROOT)),
            "stable_auditor_sha256": sha(METHOD),
            "case_bound_wrapper_sha256": sha(METHOD_WRAPPER),
            "proof_replay_path": str(METHOD_REPLAY.relative_to(ROOT)),
            "proof_replay_sha256": sha(METHOD_REPLAY),
            "k12_source_screen_path": str(REFINED.relative_to(ROOT)),
            "k12_source_screen_sha256": sha(REFINED),
            "k12_source_producer_sha256": sha(REFINED_PRODUCER),
            "old_spc_only_proof_sha256": sha(SPC_PROOF),
            "old_spc_only_rule_alone_clears_q_projection": False,
        },
        "transformed_floor_coupon_replay": {
            "path": str(TRANSFORMED_REPLAY.relative_to(ROOT)),
            "sha256": sha(TRANSFORMED_REPLAY),
            "producer_sha256": sha(TRANSFORMED_PRODUCER),
            "status": load(TRANSFORMED_REPLAY)["status"],
            "zero_u_components_radius_5e_minus_7_to_zero":
                load(TRANSFORMED_REPLAY)["exact_zero_u_components_radius_5e_minus_7_to_zero"],
            "nonzero_u_radii_and_all_rf_radii_unchanged": True,
        },
        "parser_delta_summary": refined["parser_delta_summary"],
        "original_ambiguous_screen_sha256": sha(ORIGINAL),
        "refined_normal_law_diagnostic_sha256": sha(REFINED),
        "native_run_performed_by_this_projection": False,
        "producer_sha256": sha(Path(__file__)),
    }


if __name__ == "__main__":
    projected = project()
    OUTPUT.write_text(json.dumps(projected, indent=2, sort_keys=True, allow_nan=False) + "\n")
    print(json.dumps({
        "status": projected["status"],
        "schema": projected["schema"],
        "case_id": projected["case_id"],
        "times": projected["all_printed_times"],
        "counts": [(state["time"], state["bearing_count"], state["separating_count"])
                   for state in projected["states"]],
        "corner_demands_usable": projected["corner_demands_usable"],
    }, indent=2))
