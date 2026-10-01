#!/usr/bin/env python3
"""Read-only comparison of baseline/refined DAT parsing on the transformed-floor coupon."""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import re
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[5]
SERIES = ROOT / "docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28"
FIXTURE = SERIES / "current-transformed-floor-reaction-fixture-attempt01"
BASELINE = SERIES / "current-springa-frame-response-audit-attempt01/response_audit.py"
REFINED = SERIES / "current-springa-zero-u-token-response-audit-attempt01/stable_response_audit.py"
METHOD_PROOF = SERIES / "current-springa-zero-u-token-response-audit-attempt01/zero_u_token_replay.json"
OUTPUT = Path(__file__).with_name("transformed_floor_coupon_replay.json")

PINS = {
    FIXTURE / "model.json": "8d8b9ad846b519e45ef07efe00a7f9cc5ac7f8615e9bd6cf25a6fe34d49a2f2f",
    FIXTURE / "model.inp": "97c5bb1ec6482a3c283a3a96d8fb785f2042e559f425ae827e609a34ef19e543",
    FIXTURE / "assessment.json": "d09e314969cc0dbb99d3a6c8cda55563a5244d590f25884f925838fed7a54a51",
    FIXTURE / "parent-all-increment-check.json": "284f67ade3fc7c92d4bf096eb4843e3decff5ec481a1112f7d87513677971747",
    FIXTURE / "native/model.json": "8d8b9ad846b519e45ef07efe00a7f9cc5ac7f8615e9bd6cf25a6fe34d49a2f2f",
    FIXTURE / "native/model.inp": "97c5bb1ec6482a3c283a3a96d8fb785f2042e559f425ae827e609a34ef19e543",
    FIXTURE / "native/model.dat": "1ff66c70e8acc194ac9903d23fc92195a3e8e77945e934077013b28b7b2e9670",
    FIXTURE / "native/execution.json": "04ffc2998c06b5b79da0766f0729e92b3d115cc9f85aca339bc759f022671c53",
    FIXTURE / "native/freeze.json": "5e1ebad5da91caa904ed9534bc7869400d06dbf4acdf0091458bde7221765438",
    BASELINE: "b20dae471e9826a55c40bbeed028375e6d082913e3f3917665514f2763ddd49c",
    REFINED: "bdcfa2dd85e152503b740a2f49bb1de6b67462565eb610ff5ee451990335a77d",
    METHOD_PROOF: "da1116b04390837425133af1b74fdf36fa647ecb7c181afbd49a33f0fda285c1",
}


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text())


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    require(spec is not None and spec.loader is not None, f"cannot load parser: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def replay() -> dict[str, Any]:
    for path, expected in PINS.items():
        require(sha(path) == expected, f"transformed-floor source pin mismatch: {path}")
    dat_path = FIXTURE / "native/model.dat"
    execution = load(FIXTURE / "native/execution.json")
    freeze = load(FIXTURE / "native/freeze.json")
    assessment = load(FIXTURE / "assessment.json")
    parent = load(FIXTURE / "parent-all-increment-check.json")
    model = load(FIXTURE / "model.json")
    deck = (FIXTURE / "native/model.inp").read_text()
    require(execution.get("native_solve_executed") is True
            and execution.get("returncode") == 0
            and execution.get("container_confirmed_terminal") is True,
            "transformed-floor fixture lacks a successful terminal source execution")
    require(execution.get("outputs_sha256", {}).get("model.dat") == sha(dat_path),
            "transformed-floor execution does not bind native DAT")
    require(execution.get("outputs_sha256", {}).get("model.inp") == sha(FIXTURE / "native/model.inp")
            and execution.get("outputs_sha256", {}).get("model.json") == sha(FIXTURE / "native/model.json"),
            "transformed-floor execution does not bind native model inputs")
    require(freeze.get("files_sha256", {}).get("model.inp") == sha(FIXTURE / "native/model.inp")
            and freeze.get("files_sha256", {}).get("model.json") == sha(FIXTURE / "native/model.json"),
            "transformed-floor freeze does not bind native model inputs")
    require(assessment.get("status") == "PASS_NATIVE_TRANSFORMED_FLOOR_REACTION_KNOWN_ANSWER"
            and assessment.get("method_fixture_passed") is True
            and parent.get("status") == "PASS_PARENT_ALL_PRINTED_TRANSFORMED_REACTION_INCREMENTS"
            and parent.get("printed_increment_count") == 12
            and parent.get("model_dat_sha256") == sha(dat_path),
            "transformed-floor known-answer fixture evidence is no longer passing")
    require(model.get("source_reaction_transform", {}).get("selected_source_rows_zero_based") == [1, 0]
            and model.get("source_reaction_transform", {}).get("pivot_physical_node_order") == ["B", "A"],
            "transformed-floor fixture no longer exercises the pinned nonidentity row/pivot permutation")

    old = load_module(BASELINE, "baseline_transformed_floor_parser")
    new = load_module(REFINED, "refined_transformed_floor_parser")
    data = dat_path.read_text()
    old_states = old.parse_native_blocks(data)
    new_states = new.parse_native_blocks(data)
    require(list(old_states) == list(new_states) and len(new_states) == 12,
            "baseline/refined parser state inventories differ")
    zero_u = nonzero_u = rf_components = 0
    for time, new_state in new_states.items():
        old_state = old_states[time]
        require(new_state["u"] == old_state["u"] and new_state["rf"] == old_state["rf"],
                f"parser values changed at transformed-floor time {time}")
        for node, values in new_state["u"].items():
            for dof, value in enumerate(values):
                old_radius = old_state["u_radius"][node][dof]
                new_radius = new_state["u_radius"][node][dof]
                if value == 0.0:
                    require(old_radius == 5e-7 and new_radius == 0.0,
                            f"zero U interval mismatch at time {time}, node {node}, DOF {dof+1}")
                    zero_u += 1
                else:
                    require(old_radius == new_radius,
                            f"nonzero U interval changed at time {time}, node {node}, DOF {dof+1}")
                    nonzero_u += 1
        for node, values in new_state["rf"].items():
            require(new_state["rf_radius"][node] == old_state["rf_radius"][node],
                    f"RF interval changed at time {time}, node {node}")
            rf_components += len(values)

    require(not re.search(r"^\s*\*TRANSFORM\b", deck, re.MULTILINE | re.IGNORECASE),
            "transformed source-reaction fixture unexpectedly contains a coordinate *TRANSFORM card")
    return {
        "schema": "ccx223_transformed_floor_zero_u_parser_replay/v1",
        "status": "PASS_READ_ONLY_BASELINE_REFINED_PARSER_COMPARISON",
        "fixture": "current-transformed-floor-reaction-fixture-attempt01",
        "fixture_assessment_status": assessment["status"],
        "parent_known_answer_status": parent["status"],
        "native_run_performed_by_this_replay": False,
        "physical_or_design_acceptance": False,
        "source_sha256": {str(path.relative_to(ROOT)): value for path, value in PINS.items()},
        "transformed_reaction_mapping": {
            "selected_source_rows_zero_based": model["source_reaction_transform"]["selected_source_rows_zero_based"],
            "pivot_physical_node_order": model["source_reaction_transform"]["pivot_physical_node_order"],
            "nonidentity_permuted_map_exercised": True,
            "coordinate_transform_card_present": False,
        },
        "increment_count": len(new_states),
        "exact_zero_u_components_radius_5e_minus_7_to_zero": zero_u,
        "nonzero_u_components_and_radii_unchanged": nonzero_u,
        "rf_components_and_radii_unchanged": rf_components,
        "all_parsed_u_and_rf_values_unchanged": True,
        "scope_limit": "This checks serialization-interval handling on the existing transformed source-reaction floor coupon only; it does not re-run its mechanics checks or establish frame response, floor support, or design acceptance.",
        "producer_sha256": sha(Path(__file__)),
    }


if __name__ == "__main__":
    result = replay()
    OUTPUT.write_text(json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n")
    print(json.dumps(result, indent=2, sort_keys=True, allow_nan=False))
