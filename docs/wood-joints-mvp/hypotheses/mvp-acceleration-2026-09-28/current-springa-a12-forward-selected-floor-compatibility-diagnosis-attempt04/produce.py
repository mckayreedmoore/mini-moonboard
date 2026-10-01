#!/usr/bin/env python3
"""Read-only strict-normal classification of frozen A12-forward M5 output."""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[5]
BASE = ROOT / "docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28"
HERE = Path(__file__).resolve().parent
RUNS = {
    "M1": BASE / "current-springa-selected-floor-a12-forward-attempt01",
    "M2": BASE / "current-springa-selected-floor-a12-forward-attempt02",
    "M3": BASE / "current-springa-selected-floor-a12-forward-attempt03",
    "M4": BASE / "current-springa-selected-floor-a12-forward-attempt04",
    "M5": BASE / "current-springa-selected-floor-a12-forward-attempt05",
}
PREPARED = {
    "M4": BASE / "current-springa-a12-forward-mask-update-proposal-attempt01/a12-forward",
    "M5": BASE / "current-springa-a12-forward-mask-update-proposal-attempt02/a12-forward",
}
M5_PACKET = BASE / "current-springa-a12-forward-mask-update-proposal-attempt02"
M1_SCREEN = BASE / "current-springa-a12-forward-selected-floor-screen-attempt01/screen.json"
DIAGS = {
    "M2": BASE / "current-springa-a12-forward-selected-floor-compatibility-diagnosis-attempt01/diagnosis.json",
    "M3": BASE / "current-springa-a12-forward-selected-floor-compatibility-diagnosis-attempt02/diagnosis.json",
    "M4": BASE / "current-springa-a12-forward-selected-floor-compatibility-diagnosis-attempt03/diagnosis.json",
}
METHODS = BASE / "current-springa-a12-forward-selected-floor-compatibility-diagnosis-attempt02/produce.py"
AUDITOR = BASE / "current-springa-zero-u-token-response-audit-attempt01/response_audit.py"
KERNEL = BASE / "current-springa-zero-u-token-response-audit-attempt01/stable_response_audit.py"
TOKEN_REPLAY = BASE / "current-springa-zero-u-token-response-audit-attempt01/zero_u_token_replay.json"
RUN_EXPECTED = {
    "M1": {
        "model.json": "50edee6194d3abdb758e8e7eb17f361b10cae7fc839dcedfa9f24f070d25324b",
        "model.inp": "401930f909d503e388a68f3eade5ebfaa1e228d5bc48712a217e170fe8bef553",
        "freeze.json": "5c0ff289a1ee32254160e3db0d7f9276de409f525cb665d59c17186b2586b45e",
    },
    "M2": {
        "model.json": "b50f560a1296f13a567bf37c17e6cd532ce9699d16b7700421b098aedd1420fe",
        "model.inp": "945c9d568e46e3fe6d68d4e2af8f93c9424cb9f728e6ee555df81b3fd274fa02",
        "freeze.json": "0bcd8b1a0da170c69e2e2dc1f52397cfcad0c9c10b9a524da3b07c27543f1f42",
    },
    "M3": {
        "model.json": "4f7d3f0a70a534a1c38cd0ce6e48990eb7b098dc82dc5fc2f412ff34eca3ff0f",
        "model.inp": "c9d926bd31b970f33f49dc6edf3627244a75d246124a5fef3e393b058bfa5aa4",
        "freeze.json": "204c1402c145d7f29c16314fc6f2f8231a9bbbc1f58eb2a9d100fb5aeaf8b9bf",
    },
    "M4": {
        "model.json": "c6ff4f67459bef5217502d0f61b25e19ef2aae0c21c0f10444de0c9936795cfc",
        "model.inp": "394653fbe1aa0d6ad5d36f66f19eabf6ddd45fef072466ec828d044aa3cf67e1",
        "freeze.json": "0274ab6ef907bb471ec1f0ea541a8a36074656e5df13177361fbf4a4be4264ae",
    },
    "M5": {
        "model.json": "fc24c64fba9e2a88e3d1604500798063a13f8e45bf612fa912c7618d5c40c7b0",
        "model.inp": "7b3baa0232ba9b76874607ac20019feec28ce54e5071276e54e68e9acbb9585d",
        "freeze.json": "a3c61c15df5b525ec910f4b33279e16a8e6a21bbf7678329950a8071b7b4f6d7",
    },
}
M5_EXPECTED = {
    "model.dat": "abbdfd31d5cac70b90a0979c19131940b30f40b0e04bb81e0c12c3330baecd58",
    "execution.json": "378048b549f49d743d42e6f47e2b8778e69db31f366c7ef30f19651ecc7d61a7",
    "case-context.json": "84948ddde202f1c59d212d35721ecaaab523f285782374034744dc5585988d26",
    "authorization.json": "a32249eef57b42d0dfe571b2f78419f26843ec08ff8cd75dbc66ef482acc9db1",
    "parent-readiness-review.json": "58de0c8d3869e4182564cae930f353391dcfe98cc242364df5fd43c2f2808927",
    "parent-response-rejection.json": "1764a8231a951746ed8ae9931e1c989269b412d13006b97f4e7de4ee305bc8c4",
    "parent-terminal-assessment.json": "82dcd7ad94c095005a21ec7d5207abceae246ce7047bb5fa6c61017f0250bbd3",
    "native.stdout": "f9905e28f5794f2f04b815f18a2af6e2e268387c8c875d247c1c83e8a7619995",
    "native.stderr": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "model.sta": "f898c1f5c7fa419035ef6b92924e3384c744470572f9d277b39c41c84256d9c4",
    "model.cvg": "8a77b76072bb001722db132711166341df796b4293dc2d1885fef2f1a7d13843",
    "model.frd": "a56b417b34cfa8d7bceb11149d50387cfe6abf6f8fd1a5a6c526f72516fe6216",
    "model.12d": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "spooles.out": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
}
EXPECTED = {
    "M1_screen": "e4c1c0f9b570b0225264c6f9610820d0ffc35bdf51a531bca100fc450504fee7",
    "M2_diagnosis": "acdf6c1a359439c441f4378799c987affc9b62168ac2992fb69d78409b6927a9",
    "M3_diagnosis": "03d77cde6c1ca73f32fe7036cdf462df60de5fd929207f585d594fbacafb9194",
    "M4_diagnosis": "888e64e575c49e3169d55007d691e823701ad4b364e500cb3db945c8a9b2ab39",
    "M5_prepared_model": "8195bb9939380606df6dffa7a7d4188f97f321b390d252025a60092e8d43101e",
    "M5_prepared_deck": "7b3baa0232ba9b76874607ac20019feec28ce54e5071276e54e68e9acbb9585d",
    "M5_screen": "d808ded95fe0838aef41eb6c9fa27640a8dab522a671c33599138abe4110c324",
    "auditor": "711fa96e8faff12dc4b21fa939ae28822be8abba65bc12a896b558f0a54bfff0",
    "kernel": "bdcfa2dd85e152503b740a2f49bb1de6b67462565eb610ff5ee451990335a77d",
    "methods": "da112686f540e0576fa06ab7391ccd9d0c855b0320ade09932499128b538e2ad",
    "token_replay": "da1116b04390837425133af1b74fdf36fa647ecb7c181afbd49a33f0fda285c1",
}
STATE_TIMES = [0.1, 0.2, 0.3, 0.45, 0.675, 0.925, 1.0]


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def rel(path: Path) -> str:
    return path.resolve().relative_to(ROOT.resolve()).as_posix()


def read(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def mask_sha(mask: set[str]) -> str:
    return hashlib.sha256("\n".join(sorted(mask)).encode("utf-8")).hexdigest()


def import_methods():
    if sha(METHODS) != EXPECTED["methods"]:
        raise RuntimeError("Pinned M1-M4 strict interval helper changed")
    spec = importlib.util.spec_from_file_location("pinned_a12_mask_methods_m5_diagnosis", METHODS)
    if spec is None or spec.loader is None:
        raise RuntimeError("Cannot load pinned normal interval method helpers")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def add_source(sources: dict[str, str], path: Path) -> None:
    key, digest = rel(path), sha(path)
    if key in sources and sources[key] != digest:
        raise RuntimeError(f"Conflicting source hashes for {key}")
    sources[key] = digest


def rehash_embedded_closure(obj: dict[str, Any], field: str = "source_sha256") -> dict[str, str]:
    closure = obj.get(field)
    if not isinstance(closure, dict) or not closure:
        raise RuntimeError("Prior evidence is missing a source closure")
    checked: dict[str, str] = {}
    for raw_path, expected in closure.items():
        path = Path(raw_path)
        path = path if path.is_absolute() else ROOT / path
        if not path.is_file() or sha(path) != expected:
            raise RuntimeError(f"Prior source closure changed: {raw_path}")
        checked[rel(path)] = expected
    return checked


def load_input_masks() -> tuple[dict[str, set[str]], dict[str, dict[str, Any]]]:
    inputs: dict[str, set[str]] = {}
    metadata: dict[str, dict[str, Any]] = {}
    for label, directory in RUNS.items():
        for filename, expected in RUN_EXPECTED[label].items():
            if sha(directory / filename) != expected:
                raise RuntimeError(f"Pinned {label} input/run file changed: {filename}")
        model_path, deck_path, freeze_path = directory / "model.json", directory / "model.inp", directory / "freeze.json"
        model, freeze = read(model_path), read(freeze_path)
        if freeze.get("files_sha256", {}).get("model.json") != sha(model_path):
            raise RuntimeError(f"{label} freeze does not bind its model.json")
        if freeze.get("files_sha256", {}).get("model.inp") != sha(deck_path):
            raise RuntimeError(f"{label} freeze does not bind its model.inp")
        if model.get("case_id") != "a12-forward":
            raise RuntimeError(f"{label} model is not the A12-forward case")
        mask = set(map(str, model["floor_selected_bearing_cells"]))
        expected_counts = {"M1": 35, "M2": 31, "M3": 37, "M4": 37, "M5": 34}
        if len(mask) != expected_counts[label]:
            raise RuntimeError(f"{label} input mask count changed")
        inputs[label] = mask
        metadata[label] = {
            "model_path": rel(model_path), "model_sha256": sha(model_path),
            "deck_path": rel(deck_path), "deck_sha256": sha(deck_path),
            "freeze_path": rel(freeze_path), "freeze_sha256": sha(freeze_path),
            "selected_cell_count": len(mask), "selected_cells": sorted(mask),
            "selected_mask_sha256": mask_sha(mask),
        }

    for label in ("M4", "M5"):
        prep_model, prep_deck = PREPARED[label] / "model.json", PREPARED[label] / "model.inp"
        prepared_mask = set(map(str, read(prep_model)["floor_selected_bearing_cells"]))
        if (prepared_mask != inputs[label]
                or sha(prep_deck) != RUN_EXPECTED[label]["model.inp"]):
            raise RuntimeError(f"Frozen {label} run changed its prepared selected-floor input")
        metadata[label]["prepared_model_path"] = rel(prep_model)
        metadata[label]["prepared_model_sha256"] = sha(prep_model)
        metadata[label]["prepared_deck_path"] = rel(prep_deck)
        metadata[label]["prepared_deck_sha256"] = sha(prep_deck)
    return inputs, metadata


def main() -> None:
    diagnosis_path = HERE / "diagnosis.json"
    pins_path = HERE / "source-pins.json"
    if diagnosis_path.exists() or pins_path.exists():
        raise RuntimeError("Refusing to overwrite M5 compatibility diagnosis")

    for filename, expected in RUN_EXPECTED["M5"].items():
        if sha(RUNS["M5"] / filename) != expected:
            raise RuntimeError(f"Frozen M5 input changed: {filename}")
    for filename, expected in M5_EXPECTED.items():
        if sha(RUNS["M5"] / filename) != expected:
            raise RuntimeError(f"Frozen M5 native artifact changed: {filename}")
    for key, path in (("M1_screen", M1_SCREEN), ("M2_diagnosis", DIAGS["M2"]),
                      ("M3_diagnosis", DIAGS["M3"]), ("M4_diagnosis", DIAGS["M4"]),
                      ("M5_prepared_model", PREPARED["M5"] / "model.json"),
                      ("M5_prepared_deck", PREPARED["M5"] / "model.inp"),
                      ("M5_screen", M5_PACKET / "screen.json"),
                      ("auditor", AUDITOR), ("kernel", KERNEL), ("methods", METHODS)):
        if sha(path) != EXPECTED[key]:
            raise RuntimeError(f"Pinned M5 diagnosis input changed: {key}")

    execution = read(RUNS["M5"] / "execution.json")
    freeze = read(RUNS["M5"] / "freeze.json")
    context_path = RUNS["M5"] / "case-context.json"
    rejection = read(RUNS["M5"] / "parent-response-rejection.json")
    assessment = read(RUNS["M5"] / "parent-terminal-assessment.json")
    model_path, deck_path, data_path = (RUNS["M5"] / name for name in ("model.json", "model.inp", "model.dat"))
    model, deck, data, context = read(model_path), deck_path.read_text(encoding="utf-8"), data_path.read_text(encoding="utf-8", errors="replace"), read(context_path)
    if (execution.get("run_id") != "springa-selected-a12-forward-attempt05"
            or execution.get("native_solve_executed") is not True
            or execution.get("returncode") != 0
            or execution.get("container_confirmed_terminal") is not True):
        raise RuntimeError("M5 is not the expected completed native execution")
    if (rejection.get("status") != "REJECTED_UNCHANGED_PHYSICAL_RESPONSE_GATE"
            or rejection.get("reason") != "Inactive floor normal is not strictly separated with zero endpoint RF: SPR1026"
            or rejection.get("usable_corner_demands") is not False):
        raise RuntimeError("M5 rejection is absent or differs from the exact parent strict-gate result")
    if (assessment.get("status") != "REJECTED_PARENT_A12_FORWARD_M5_PHYSICAL_COMPATIBILITY"
            or assessment.get("strict_rejection") != rejection["reason"]
            or assessment.get("response_usable_for_conditional_joint_checks") is not False
            or assessment.get("physical_failure_inferred") is not False
            or assessment.get("no_further_forward_mask_native_runs_queued") is not True):
        raise RuntimeError("M5 parent assessment is absent, altered, or implies additional mask iteration")
    if (freeze.get("files_sha256") != {
            "model.inp": RUN_EXPECTED["M5"]["model.inp"],
            "model.json": RUN_EXPECTED["M5"]["model.json"],
            "case-context.json": M5_EXPECTED["case-context.json"],
    }):
        raise RuntimeError("Frozen M5 model/deck/context bindings differ")
    if (context.get("selected_input_model_json_sha256") != sha(model_path)
            or context.get("selected_input_deck_sha256") != sha(deck_path)
            or context.get("diagnostic_floor_screen_sha256") != sha(M5_PACKET / "screen.json")
            or set(model["floor_selected_bearing_cells"]) != set(context["selected_cells"])):
        raise RuntimeError("M5 frozen context does not bind its exact input mask and source screen")
    if set(model["floor_selected_bearing_cells"]) != set(read(PREPARED["M5"] / "model.json")["floor_selected_bearing_cells"]):
        raise RuntimeError("M5 frozen model mask differs from the source-prepared proposal")

    freeze_sources = freeze.get("source_sha256")
    if not isinstance(freeze_sources, dict) or not freeze_sources:
        raise RuntimeError("M5 freeze lacks a pinned source closure")
    frozen_source_hashes: dict[str, str] = {}
    for raw_path, expected in freeze_sources.items():
        path = Path(raw_path)
        path = path if path.is_absolute() else ROOT / path
        if not path.is_file() or sha(path) != expected:
            raise RuntimeError(f"Frozen M5 source closure changed: {raw_path}")
        frozen_source_hashes[rel(path)] = expected
    for name, expected in execution.get("outputs_sha256", {}).items():
        if sha(RUNS["M5"] / name) != expected:
            raise RuntimeError(f"M5 native output differs from execution record: {name}")

    inputs, input_metadata = load_input_masks()
    # Revalidate all prior comparison sources through their recorded closures.
    m1_screen = read(M1_SCREEN)
    if (m1_screen.get("source_selected_floor_run_id") != "springa-selected-a12-forward-attempt01"
            or m1_screen.get("stable_actual_normal_law_mask", {}).get("same_classification_sets_at_every_printed_increment") is not True
            or m1_screen.get("stable_actual_normal_law_mask", {}).get("interval_ambiguous_or_noncomplementary_count") != 0):
        raise RuntimeError("M1 historical output screen is not a stable strict classification")
    for source, expected in m1_screen.get("source_sha256", {}).items():
        path = Path(source)
        path = path if path.is_absolute() else ROOT / path
        if not path.is_file() or sha(path) != expected:
            raise RuntimeError(f"M1 source-screen closure changed: {source}")

    prior = {label: read(path) for label, path in DIAGS.items()}
    expected_prior_run_ids = {"M2": "springa-selected-a12-forward-attempt02",
                              "M3": "springa-selected-a12-forward-attempt03",
                              "M4": "springa-selected-a12-forward-attempt04"}
    for label, report in prior.items():
        if report.get("native_run_id") != expected_prior_run_ids[label]:
            raise RuntimeError(f"{label} prior diagnostic names a different native run")
        for source, expected in report.get("source_sha256", {}).items():
            path = Path(source)
            path = path if path.is_absolute() else ROOT / path
            if not path.is_file() or sha(path) != expected:
                raise RuntimeError(f"{label} diagnostic source closure changed: {source}")

    output_masks: dict[str, set[str]] = {
        "M1": set(map(str, m1_screen["stable_actual_normal_law_mask"]["strictly_positive_cells"])),
        "M2": set(map(str, prior["M2"]["zero_u_711_observed_positive_cells_diagnostic_only"])),
        "M3": set(map(str, prior["M3"]["strict_positive_cells_diagnostic_only"])),
        "M4": set(map(str, prior["M4"]["history"][0]["observed_positive_cells_diagnostic_only"])),
    }
    prior_stable = {
        "M1": m1_screen["stable_actual_normal_law_mask"]["same_classification_sets_at_every_printed_increment"],
        "M2": prior["M2"]["zero_u_711_stable_observed_positive_mask"],
        "M3": prior["M3"]["strict_positive_pattern_constant_across_seven_states"],
        "M4": prior["M4"]["state_positive_set_constant_across_seven_states"],
    }
    for label, mask in output_masks.items():
        if len(mask) != {"M1": 31, "M2": 37, "M3": 37, "M4": 34}[label] or prior_stable[label] is not True:
            raise RuntimeError(f"{label} prior output set is not the pinned stable set")

    methods = import_methods()
    auditor = methods.import_zero_u_auditor()
    if sha(AUDITOR) != EXPECTED["auditor"] or sha(KERNEL) != EXPECTED["kernel"]:
        raise RuntimeError("Pinned zero-U response auditor/recovery source changed after import")
    case_pin = auditor._validate_case_context(context)
    contract = auditor._validate_model(model, deck, context)
    terminal = auditor._validate_execution(model_path, data_path, deck_path, RUNS["M5"] / "execution.json", data, context)
    if terminal.get("native_output_hashes_match") is not True:
        raise RuntimeError("Pinned 711 output integrity check failed")
    if case_pin.get("selected_cell_count") != 34 or case_pin.get("inactive_cell_count") != 66:
        raise RuntimeError("M5 frozen input context does not validate as 34/66")
    states = auditor.parse_native_blocks(data)
    if list(states) != STATE_TIMES:
        raise RuntimeError(f"Expected the seven exact M5 printed load factors, got {list(states)}")

    normal_bindings = []
    for binding in contract["bindings"]:
        source = contract["source_by_group"][str(binding["group"])]
        if source.get("role") == "floor_normal":
            normal_bindings.append((binding, source))
    if len(normal_bindings) != 100:
        raise RuntimeError(f"Expected 100 source floor-normal carriers, got {len(normal_bindings)}")

    input_mask = inputs["M5"]
    history: list[dict[str, Any]] = []
    output_by_state: list[set[str]] = []
    exceptions_by_cell: dict[str, list[dict[str, Any]]] = {}
    for time, state in states.items():
        rows = []
        positive, separated, ambiguous = set(), set(), set()
        for binding, source in normal_bindings:
            # Native spring/RF outputs are consumed only inside the pinned
            # strict classifier. Numeric forces and RF values are discarded.
            _native_force, _native_radius, check = auditor.audit_springa(
                binding, source, state, contract["emitted_nodes"]
            )
            classification = methods.classify(auditor, binding, check, state, contract)
            q_interval, geometric_interval = methods.intervals(binding, check, state, contract)
            cell = str(binding["name"])
            selected = cell in input_mask
            row = {
                "cell_name": cell,
                "source_group": str(binding["group"]),
                "source_row_id": str(binding["source_row_id"]),
                "input_status": "selected" if selected else "inactive",
                "classification": classification,
                "q_interval_mm": q_interval,
                "geometric_elongation_interval_mm": geometric_interval,
            }
            rows.append(row)
            if classification == "STRICTLY_POSITIVE":
                positive.add(cell)
            elif classification == "STRICTLY_SEPARATED_WITH_ZERO_ENDPOINT_RF":
                separated.add(cell)
            else:
                ambiguous.add(cell)
            incompatible = (selected and classification != "STRICTLY_POSITIVE") or (
                not selected and classification != "STRICTLY_SEPARATED_WITH_ZERO_ENDPOINT_RF"
            )
            if incompatible:
                exceptions_by_cell.setdefault(cell, []).append({
                    "load_factor": float(time),
                    "input_status": row["input_status"],
                    "classification": classification,
                    "q_interval_mm": q_interval,
                    "geometric_elongation_interval_mm": geometric_interval,
                })
        rows.sort(key=lambda row: row["cell_name"])
        if len(rows) != 100 or len({row["cell_name"] for row in rows}) != 100:
            raise RuntimeError(f"M5 normal rows are incomplete at load factor {time}")
        if (len(positive | separated | ambiguous) != 100 or positive & separated
                or positive & ambiguous or separated & ambiguous):
            raise RuntimeError(f"Strict normal classifications do not partition all cells at {time}")
        output_by_state.append(positive)
        history.append({
            "load_factor": float(time),
            "strictly_positive_count": len(positive),
            "strictly_separated_count": len(separated),
            "ambiguous_or_noncomplementary_count": len(ambiguous),
            "observed_positive_cells_diagnostic_only": sorted(positive),
            "observed_positive_mask_sha256": mask_sha(positive),
            "observed_separated_cells_diagnostic_only": sorted(separated),
            "observed_ambiguous_cells_diagnostic_only": sorted(ambiguous),
            "input_mask_comparison": {
                label: {
                    "input_cell_count": len(mask),
                    "exact_match": positive == mask,
                    "overlap_count": len(positive & mask),
                    "symmetric_difference_count": len(positive ^ mask),
                    "observed_positive_outside_input": sorted(positive - mask),
                    "input_cells_not_strictly_positive": sorted(mask - positive),
                }
                for label, mask in inputs.items()
            },
            "rows": rows,
        })

    stable = all(mask == output_by_state[0] for mask in output_by_state[1:])
    if not stable:
        raise RuntimeError("M5 strict-positive normal mask changes across its seven printed states")
    m5_output = output_by_state[0]
    if output_masks["M4"] != input_mask:
        raise RuntimeError("The known M4-output-to-M5-input source handoff changed")
    output_masks["M5"] = m5_output
    output_stable = {**prior_stable, "M5": stable}
    output_matches = {
        label: sorted(other for other, input_mask_i in inputs.items() if mask == input_mask_i)
        for label, mask in output_masks.items()
    }
    previous_output_matches = {
        label: sorted(other for other, other_mask in output_masks.items() if other != label and mask == other_mask)
        for label, mask in output_masks.items()
    }
    handoffs = [
        {"observed_from": f"M{i}", "proposed_as": f"M{i+1}",
         "exact_set_match": output_masks[f"M{i}"] == inputs[f"M{i+1}"]}
        for i in range(1, 5)
    ]
    if not all(item["exact_set_match"] for item in handoffs):
        raise RuntimeError("A prior diagnostic output does not bind the next recorded input")

    input_output_summary = {
        label: {
            "input_cell_count": len(inputs[label]),
            "input_cells": sorted(inputs[label]),
            "input_mask_sha256": mask_sha(inputs[label]),
            "output_cell_count": len(output_masks[label]),
            "output_cells": sorted(output_masks[label]),
            "output_mask_sha256": mask_sha(output_masks[label]),
            "output_stable_across_seven_printed_states": output_stable[label],
            "output_matches_input_labels": output_matches[label],
            "output_matches_other_output_labels": previous_output_matches[label],
            **input_metadata[label],
        }
        for label in inputs
    }
    source_sha256: dict[str, str] = {}
    # M5 freeze is the exact source closure for the native input and output.
    for source, expected in frozen_source_hashes.items():
        add_source(source_sha256, ROOT / source)
    # Revalidate and carry forward the exact history used for M1-M4 masks.
    historic_paths = [M1_SCREEN, Path(__file__).resolve(), HERE / "README.md"]
    historic_paths.extend(DIAGS.values())
    historic_paths.extend([
        BASE / "current-springa-a12-forward-selected-floor-screen-attempt01/produce.py",
        BASE / "current-springa-a12-forward-selected-floor-compatibility-diagnosis-attempt01/produce.py",
        BASE / "current-springa-a12-forward-selected-floor-compatibility-diagnosis-attempt02/produce.py",
        BASE / "current-springa-a12-forward-selected-floor-compatibility-diagnosis-attempt03/produce.py",
        BASE / "current-springa-a12-forward-selected-floor-compatibility-diagnosis-attempt01/source-pins.json",
        BASE / "current-springa-a12-forward-selected-floor-compatibility-diagnosis-attempt02/source-pins.json",
        BASE / "current-springa-a12-forward-selected-floor-compatibility-diagnosis-attempt03/source-pins.json",
    ])
    historic_paths.extend(path for path in PREPARED.values() for path in (path / "model.json", path / "model.inp", path / "audit.json"))
    historic_paths.extend([M5_PACKET / name for name in ("prepare_m5_proposal.py", "check_m5_input_gate.py", "README.md", "screen.json", "proposal.json", "case-context.json", "input-gate.json", "input-gate-source-pins.json")])
    historic_paths.extend([METHODS, AUDITOR, KERNEL, TOKEN_REPLAY])
    for directory in RUNS.values():
        historic_paths.extend(directory / name for name in ("model.json", "model.inp", "freeze.json"))
    historic_paths.extend(RUNS["M5"] / name for name in M5_EXPECTED)
    historic_paths.extend(RUNS["M5"] / name for name in ("model.json", "model.inp", "freeze.json"))
    historic_paths.extend([RUNS["M5"] / "execution.json", context_path, RUNS["M5"] / "parent-readiness-review.json", RUNS["M5"] / "parent-response-rejection.json", RUNS["M5"] / "parent-terminal-assessment.json"])
    for path in historic_paths:
        add_source(source_sha256, path)

    assessment = {
        "schema": "current_springa_a12_forward_attempt05_floor_mask_compatibility_diagnosis/v1",
        "status": "REJECTED_M5_SELECTED_BEARING_BRANCH_INCOMPATIBLE_DIAGNOSTIC_ONLY",
        "case_id": model["case_id"],
        "candidate": model["candidate"],
        "geometry_revision_id": model["geometry_revision_id"],
        "native_run_id": execution["run_id"],
        "terminal_native_output_consumed": True,
        "native_solve_launched_by_diagnosis": False,
        "run_returncode": execution["returncode"],
        "elapsed_seconds": execution["elapsed_seconds"],
        "parent_response_gate_status": rejection["status"],
        "parent_response_gate_exception": rejection["reason"],
        "parent_terminal_assessment_status": assessment["status"],
        "parent_reported_first_offending_inactive_normal": "SPR1026",
        "strict_complementarity_passed": False,
        "corner_demands_usable": False,
        "physical_force_adoption": False,
        "response_force_exported": False,
        "numeric_spring_force_or_reference_rf_values_written": False,
        "input_mask_label": "M5",
        "input_selected_cell_count": len(input_mask),
        "input_selected_cells": sorted(input_mask),
        "all_100_floor_normal_laws_checked_at_every_printed_state": True,
        "all_printed_load_factors": [float(time) for time in states],
        "strict_method": {
            "name": "unchanged pinned zero-U 711-token strict signed normal interval classification",
            "response_auditor_path": rel(AUDITOR),
            "response_auditor_sha256": sha(AUDITOR),
            "recovery_kernel_path": rel(KERNEL),
            "recovery_kernel_sha256": sha(KERNEL),
            "prior_interval_method_helper_path": rel(METHODS),
            "prior_interval_method_helper_sha256": sha(METHODS),
            "token_replay_path": rel(TOKEN_REPLAY),
            "token_replay_sha256": sha(TOKEN_REPLAY),
            "classifier_tolerance_or_branch_rule_changed": False,
        },
        "input_output_sets_M1_to_M5": input_output_summary,
        "observed_positive_set_constant_across_seven_states": stable,
        "strict_positive_count_by_state": [entry["strictly_positive_count"] for entry in history],
        "strict_separated_count_by_state": [entry["strictly_separated_count"] for entry in history],
        "ambiguous_or_noncomplementary_count_by_state": [entry["ambiguous_or_noncomplementary_count"] for entry in history],
        "M5_inactive_positive_cells": sorted(m5_output - input_mask),
        "M5_selected_not_strictly_positive_cells": sorted(input_mask - m5_output),
        "M5_symmetric_difference_count": len(m5_output ^ input_mask),
        "M5_output_matches_any_M1_to_M5_input": bool(output_matches["M5"]),
        "M5_output_matches_any_prior_output": bool(previous_output_matches["M5"]),
        "historical_output_to_next_input_handoffs": handoffs,
        "exact_feedback_or_fixed_point_matches": {
            "definition": "Output M_i equals input M_j with j <= i; this detects a fixed point or return to a prior mask, excluding ordinary forward handoff to the next proposal.",
            "matches": [
                {"output_label": label, "input_label": input_label}
                for i, label in enumerate(("M1", "M2", "M3", "M4", "M5"), start=1)
                for input_index, input_label in enumerate(("M1", "M2", "M3", "M4", "M5"), start=1)
                if input_index <= i and output_masks[label] == inputs[input_label]
            ],
        },
        "incompatible_cell_interval_history": {
            cell: {
                "source_group": next(row["source_group"] for row in history[-1]["rows"] if row["cell_name"] == cell),
                "input_status": exceptions[0]["input_status"],
                "classification_by_state": [item["classification"] for item in exceptions],
                "states": exceptions,
            }
            for cell, exceptions in sorted(exceptions_by_cell.items())
        },
        "case_context_validation": {
            "case_context_sha256": sha(context_path),
            "selected_input_model_sha256": sha(model_path),
            "selected_input_deck_sha256": sha(deck_path),
            "case_context_validation_passed": True,
            "pinned_711_model_input_validation_passed": True,
            "execution_hash_validation_passed": terminal["native_output_hashes_match"],
            "selected_count": case_pin["selected_cell_count"],
            "inactive_count": case_pin["inactive_cell_count"],
        },
        "native_output_hashes": {name: sha(RUNS["M5"] / name) for name in M5_EXPECTED},
        "freeze_source_closure": {
            "freeze_sha256": sha(RUNS["M5"] / "freeze.json"),
            "source_pin_count": len(freeze_sources),
            "all_frozen_source_hashes_revalidated": True,
        },
        "history": history,
        "source_sha256": dict(sorted(source_sha256.items())),
        "limits": [
            "This diagnostic reads only the already-frozen M5 DAT and prior source-bound mask reports; it changes no run or input file.",
            "Native force/RF values are consumed only internally by the unchanged pinned classifier and are discarded; no corner demands are recovered or adopted.",
            "M5 is rejected because inactive SPR1026 is strictly positive; two additional inactive cells are also positive, and five selected cells are strictly separated.",
            "All seven M5 states have the same 32/68/0 strict classifications. This establishes compatibility failure for this frozen proposal, not physical failure or exhaustive behavior over every possible support mask.",
            "The recorded M1-M5 output/input comparison shows sequential proposal handoffs but no output equal to its own or an earlier input; M5 output matches none of M1-M5 inputs.",
            "No M6 mask, solver launch, contact law, tolerance, geometry, or load proposal is produced.",
        ],
    }
    diagnosis_path.write_text(json.dumps(assessment, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8")
    pins = {
        "schema": "current_springa_a12_forward_attempt05_floor_mask_compatibility_diagnosis_source_pins/v1",
        "status": "PASS_M5_DIAGNOSTIC_SOURCE_REHASH",
        "diagnosis_path": rel(diagnosis_path),
        "diagnosis_sha256": sha(diagnosis_path),
        "producer_path": rel(Path(__file__).resolve()),
        "producer_sha256": sha(Path(__file__).resolve()),
        "source_sha256": dict(sorted(source_sha256.items())),
        "frozen_source_pin_count_revalidated": len(freeze_sources),
        "input_mask_cell_counts": {label: len(mask) for label, mask in inputs.items()},
        "observed_positive_count_by_state": assessment["strict_positive_count_by_state"],
        "native_solve_launched_by_producer": False,
        "spring_force_or_rf_values_exported": False,
        "M6_or_follow_on_mask_proposed": False,
    }
    pins_path.write_text(json.dumps(pins, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8")
    print(json.dumps({
        "status": assessment["status"],
        "native_run_id": execution["run_id"],
        "response_rejection": rejection["reason"],
        "positive_counts": assessment["strict_positive_count_by_state"],
        "separated_counts": assessment["strict_separated_count_by_state"],
        "ambiguous_counts": assessment["ambiguous_or_noncomplementary_count_by_state"],
        "stable_across_states": stable,
        "M5_inactive_positive": assessment["M5_inactive_positive_cells"],
        "M5_selected_not_positive": assessment["M5_selected_not_strictly_positive_cells"],
        "M5_output_matches_prior_input": assessment["M5_output_matches_any_M1_to_M5_input"],
        "diagnosis_sha256": sha(diagnosis_path),
    }, sort_keys=True))


if __name__ == "__main__":
    main()
