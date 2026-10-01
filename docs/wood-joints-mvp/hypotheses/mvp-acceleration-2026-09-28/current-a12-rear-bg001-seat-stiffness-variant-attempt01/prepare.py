#!/usr/bin/env python3
"""Prepare one source-pinned, input-only BG001 outer-seat stiffness variant."""

from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[5]
PACKET = Path(__file__).resolve().parent
DATE_DIR = ROOT / "docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28"
BASELINE_DIR = DATE_DIR / "current-springa-selected-floor-a12-rear-attempt03"
SENSITIVITY_DIR = DATE_DIR / "current-post-spine-compliance-sensitivity-attempt01"

BASELINE_PINS = {
    "model.json": "8a90452d8afa1f1722b3253b18d5aeec72c432033a22d5d0828082022cc1cda8",
    "model.inp": "e8f7376817daa1e3ac0b7d5f85c52b16115c2cef39291486d1800e0e847e0aff",
    "response.json": "892dadeed0b20d809ce5250d3cd1c3deb31697f69208d8bbefb5f702160e1274",
}
SENSITIVITY_PINS = {
    "sensitivity.json": "0994ae3f5a54c6eb985141c54eb3d38d455678482ed2ac5a6205e2a84096a9c0",
    "produce.py": "7f00f6e5679e36eb5233dc5247a2dcf3aeb0ea0d5078f82dae4722ba7f5718d5",
}
PROPERTY_PRODUCER = ROOT / "fea/wood_joint_reduced_properties.py"
PROPERTY_PRODUCER_SHA256 = "26b6e8bf8800208bfb867439694afa705558ac63ca338778e9210e940a55d9a1"

OLD_K = 4670.054188242363
NEW_K = 2401.714359616974
TARGETS = {
    "knee_outer_left_post_1/outer-seat-axial-tie": {
        "group": "SPR1771",
        "source_inventory_row_index": 1770,
        "element": 3674,
        "axis_id": "knee_outer_left_post_1",
    },
    "knee_outer_left_post_2/outer-seat-axial-tie": {
        "group": "SPR1772",
        "source_inventory_row_index": 1771,
        "element": 3675,
        "axis_id": "knee_outer_left_post_2",
    },
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require_pin(path: Path, expected: str) -> None:
    actual = sha256(path)
    if actual != expected:
        raise SystemExit(f"source pin mismatch for {path}: {actual} != {expected}")


def find_exact(rows: list[dict], name: str, group: str) -> tuple[int, dict]:
    found = [(i, row) for i, row in enumerate(rows)
             if row.get("name") == name and row.get("group") == group]
    if len(found) != 1:
        raise SystemExit(f"expected exactly one {name}/{group}, found {len(found)}")
    return found[0]


def table_value(k: float) -> float:
    return k * 10.0


def update_runtime_bindings(model: dict) -> list[dict]:
    changed = []
    for field in ("nonlinear_native_carrier_bindings", "unilateral_springa_bindings"):
        rows = model[field]
        for name, target in TARGETS.items():
            index, row = find_exact(rows, name, target["group"])
            if row.get("source_inventory_row_index") != target["source_inventory_row_index"]:
                raise SystemExit(f"{field}/{name}: inventory row changed")
            if row.get("source_element") != target["element"]:
                raise SystemExit(f"{field}/{name}: source element changed")
            if row.get("force_law") != "k * max(q_mm, 0)":
                raise SystemExit(f"{field}/{name}: unexpected force law")
            if row.get("table_domain_mm") != [-10.0, 10.0]:
                raise SystemExit(f"{field}/{name}: unexpected table domain")
            if row.get("initial_span_mm") != 100.0:
                raise SystemExit(f"{field}/{name}: unexpected initial span")
            owner = row.get("physical_owner", {})
            if (owner.get("role") != "physical_bolt_outer_seat_tension"
                    or owner.get("axis_id") != target["axis_id"]
                    or owner.get("first") != "knee_outer_left_spine"
                    or owner.get("second") != "base_post_outer_left"):
                raise SystemExit(f"{field}/{name}: physical owner changed")
            axis = owner.get("axis", [])
            if (len(axis) != 3 or abs(float(axis[0]) - 1.0) > 1.0e-12
                    or abs(float(axis[1])) > 1.0e-12 or abs(float(axis[2])) > 1.0e-12):
                raise SystemExit(f"{field}/{name}: expected preserved global-X axis")
            if abs(float(row.get("stiffness_n_per_mm", -1)) - OLD_K) > 1.0e-10:
                raise SystemExit(f"{field}/{name}: unexpected baseline stiffness")
            table = row.get("force_vs_elongation_table_N_mm")
            if table != [[0.0, -10.0], [0.0, 0.0], [OLD_K * 10.0, 10.0]]:
                raise SystemExit(f"{field}/{name}: unexpected baseline force table")
            row["stiffness_n_per_mm"] = NEW_K
            row["force_vs_elongation_table_N_mm"][2][0] = table_value(NEW_K)
            changed.append({
                "model_field": field,
                "index": index,
                "name": name,
                "group": target["group"],
                "stiffness_n_per_mm": [OLD_K, NEW_K],
                "positive_10mm_force_N": [OLD_K * 10.0, NEW_K * 10.0],
            })
    return changed


def update_deck(deck_text: str) -> tuple[str, list[dict]]:
    lines = deck_text.splitlines(keepends=True)
    changes = []
    for name, target in TARGETS.items():
        header = f"*SPRING,ELSET={target['group']},NONLINEAR"
        headers = [i for i, line in enumerate(lines) if line.rstrip("\r\n") == header]
        if len(headers) != 1:
            raise SystemExit(f"expected one native *SPRING table for {name}")
        header_index = headers[0]
        data_indices = []
        for i in range(header_index + 1, len(lines)):
            stripped = lines[i].strip()
            if not stripped:
                continue
            if stripped.startswith("*"):
                break
            data_indices.append(i)
        if len(data_indices) != 3:
            raise SystemExit(f"{name}: expected three force/elongation rows")
        parsed = [[float(value.strip()) for value in lines[i].split(",")]
                  for i in data_indices]
        expected = [[0.0, -10.0], [0.0, 0.0], [OLD_K * 10.0, 10.0]]
        if (any(len(actual) != 2 for actual in parsed)
                or parsed[0] != expected[0]
                or parsed[1] != expected[1]
                or abs(parsed[2][0] - expected[2][0]) > 1.0e-8
                or parsed[2][1] != expected[2][1]):
            raise SystemExit(f"{name}: baseline deck table differs: {parsed!r}")
        table_index = data_indices[2]
        ending = "\r\n" if lines[table_index].endswith("\r\n") else "\n"
        lines[table_index] = f"{NEW_K * 10.0:.14g},10.0{ending}"
        changes.append({
            "name": name,
            "group": target["group"],
            "element": target["element"],
            "deck_line_1based": table_index + 1,
            "old_force_record": f"{OLD_K * 10.0:.14g},10.0",
            "new_force_record": f"{NEW_K * 10.0:.14g},10.0",
        })
    return "".join(lines), changes


def compare_json_paths(before, after, path="") -> list[str]:
    if type(before) is not type(after):
        return [path or "/"]
    if isinstance(before, dict):
        if before.keys() != after.keys():
            return [path + "/<keys>"]
        differences = []
        for key in before:
            differences.extend(compare_json_paths(before[key], after[key], f"{path}/{key}"))
        return differences
    if isinstance(before, list):
        if len(before) != len(after):
            return [path + "/<length>"]
        differences = []
        for index, (left, right) in enumerate(zip(before, after, strict=True)):
            differences.extend(compare_json_paths(left, right, f"{path}/{index}"))
        return differences
    return [] if before == after else [path or "/"]


def expected_json_paths(before: dict) -> set[str]:
    paths = set()
    for field in ("nonlinear_native_carrier_bindings", "unilateral_springa_bindings"):
        for name, target in TARGETS.items():
            index, _ = find_exact(before[field], name, target["group"])
            prefix = f"/{field}/{index}"
            paths.add(prefix + "/stiffness_n_per_mm")
            paths.add(prefix + "/force_vs_elongation_table_N_mm/2/0")
    return paths


def main() -> None:
    for name, pin in BASELINE_PINS.items():
        require_pin(BASELINE_DIR / name, pin)
    for name, pin in SENSITIVITY_PINS.items():
        require_pin(SENSITIVITY_DIR / name, pin)
    require_pin(PROPERTY_PRODUCER, PROPERTY_PRODUCER_SHA256)

    source_model = json.loads((BASELINE_DIR / "model.json").read_text())
    model = copy.deepcopy(source_model)
    runtime_changes = update_runtime_bindings(model)
    actual_paths = set(compare_json_paths(source_model, model))
    expected_paths = expected_json_paths(source_model)
    if actual_paths != expected_paths:
        raise SystemExit(
            "unexpected JSON changes: "
            f"missing={sorted(expected_paths - actual_paths)!r}; "
            f"extra={sorted(actual_paths - expected_paths)!r}"
        )

    source_deck_text = (BASELINE_DIR / "model.inp").read_text()
    deck_text, deck_changes = update_deck(source_deck_text)
    old_lines = source_deck_text.splitlines(keepends=True)
    new_lines = deck_text.splitlines(keepends=True)
    deck_diff_lines = [i for i, (old, new) in enumerate(zip(old_lines, new_lines, strict=True))
                       if old != new]
    expected_deck_line_indices = [row["deck_line_1based"] - 1 for row in deck_changes]
    if deck_diff_lines != expected_deck_line_indices:
        raise SystemExit(f"unexpected native deck diff lines: {deck_diff_lines!r}")

    # The one-sided law and table domains are unchanged. Check representative values.
    law_samples = []
    for q in (-10.0, 0.0, 5.0, 10.0):
        expected_force = NEW_K * max(q, 0.0)
        law_samples.append({"q_mm": q, "force_N": expected_force})
    if not (law_samples[0]["force_N"] == 0.0
            and law_samples[1]["force_N"] == 0.0
            and abs(law_samples[2]["force_N"] - 12008.57179808487) < 1.0e-9
            and abs(law_samples[3]["force_N"] - NEW_K * 10.0) < 1.0e-9):
        raise SystemExit("source-law arithmetic check failed")

    PACKET.mkdir(parents=True, exist_ok=True)
    model_path = PACKET / "model.json"
    deck_path = PACKET / "model.inp"
    model_path.write_text(json.dumps(model, indent=2) + "\n")
    deck_path.write_text(deck_text)

    sensitivity = json.loads((SENSITIVITY_DIR / "sensitivity.json").read_text())
    chosen = sensitivity["post_1_exact_stiffness_basis"]["sensitivity_scenarios"][4]
    if chosen != {
        "first_outer_seat_E_axis_mpa": 750.176,
        "first_outer_seat_frame_scenario_id": "ring_R_on_X",
        "first_outer_wood_seat_stiffness_n_per_mm": 4960.93773810716,
        "second_outer_seat_E_axis_mpa": 750.1495934967178,
        "second_outer_seat_frame_scenario_id": "ring_R_on_source_X",
        "second_outer_wood_seat_stiffness_n_per_mm": 4960.76311106142,
        "steel_E_mpa": 190000.0,
        "steel_extension_stiffness_n_per_mm": 75685.53387692064,
        "wood_column_depth_factor_of_equivalent_washer_diameter": 2.0,
        "wood_column_depth_mm": 33.67989435613535,
        "effective_axial_stiffness_n_per_mm": NEW_K,
    }:
        raise SystemExit("selected source sensitivity row 4 changed")

    manifest = {
        "schema": "conditional_frame_joint_stiffness_sensitivity_input/v1",
        "status": "PREPARED_INPUT_ONLY_NO_NATIVE_READINESS",
        "native_solve_executed": False,
        "mechanical_acceptance": False,
        "qualified_for_design": False,
        "variant_purpose": "A12-rear response sensitivity for the two BG001 left-post outer bolt-seat axial ties",
        "baseline": {
            "packet": str(BASELINE_DIR.relative_to(ROOT)),
            "model_json_sha256": BASELINE_PINS["model.json"],
            "model_inp_sha256": BASELINE_PINS["model.inp"],
            "response_json_sha256": BASELINE_PINS["response.json"],
            "case_id": source_model["case_id"],
            "candidate": source_model["candidate"],
            "geometry_revision_id": source_model["geometry_revision_id"],
        },
        "source_sensitivity": {
            "packet": str(SENSITIVITY_DIR.relative_to(ROOT)),
            "sensitivity_json_sha256": SENSITIVITY_PINS["sensitivity.json"],
            "producer_sha256": SENSITIVITY_PINS["produce.py"],
            "property_producer": str(PROPERTY_PRODUCER.relative_to(ROOT)),
            "property_producer_sha256": PROPERTY_PRODUCER_SHA256,
            "selected_scenario_index": 4,
            "scenario": chosen,
            "source_method": "conditional series compliance: steel extension plus two outer washer-seat wood-column compliances",
            "selected_frame_pair_is_local_nominal_ring_case_a": True,
            "limits": [
                "The two-times-equivalent-washer-diameter wood influence depth is an uncalibrated idealization.",
                "The local sensitivity is not measured, calibrated, statistical, or a physical stiffness bound.",
                "The local imposed-moment study does not itself predict whole-frame response.",
                "Bolt thread/root area, thread engagement, head/nut deformation, washer bending, preload, gaps, and crushing are not added.",
            ],
        },
        "changed_runtime_springs": [
            {
                "name": name,
                "group": target["group"],
                "source_inventory_row_index": target["source_inventory_row_index"],
                "source_element": target["element"],
                "spring_family": "physical_bolt_outer_seat_tension",
                "physical_owner": "knee_outer_left_spine to base_post_outer_left",
                "axis": "global X; q remains u(second projection)-u(first projection)",
                "baseline_stiffness_N_per_mm": OLD_K,
                "variant_stiffness_N_per_mm": NEW_K,
                "stiffness_ratio_to_baseline": NEW_K / OLD_K,
                "baseline_positive_10mm_force_N": OLD_K * 10.0,
                "variant_positive_10mm_force_N": NEW_K * 10.0,
                "force_law": "k * max(q_mm, 0), unchanged",
                "table_domain_mm": [-10.0, 10.0],
                "initial_span_mm": 100.0,
            }
            for name, target in TARGETS.items()
        ],
        "changed_fields": {
            "model_json": sorted(actual_paths),
            "native_deck_changed_line_numbers_1based": [
                row["deck_line_1based"] for row in deck_changes
            ],
            "native_deck_changed_groups": [row["group"] for row in deck_changes],
            "native_deck_changed_records": deck_changes,
            "global_material_cards_changed": [],
        },
        "unchanged_invariants": [
            "All physical nodes, elements, body geometry, and member material/orientation cards.",
            "All emitted physical CLOAD/source loads and the source load ledger.",
            "All floor support laws, normal springs, selected-floor input mask, floor MPCs, and support geometry.",
            "All other SPRINGA carriers and all 348 retained bilateral SPRING2 rows.",
            "Both target ties retain their existing one-sided tensile law, coordinate orientation, zero gap/preload assumption, 100 mm numerical span, and [-10,+10] mm force table domain.",
            "The baseline raw/source carrier inventories remain unchanged as provenance; the declared override applies only to the two runtime native bindings above.",
        ],
        "validation": {
            "source_hash_pins_passed": True,
            "exact_model_json_diff_passed": True,
            "exact_native_deck_diff_passed": True,
            "force_law_sample_arithmetic_passed": True,
            "law_sample_points": law_samples,
            "native_run_performed": False,
        },
        "required_before_any_native_run": [
            "Parent must independently freeze/review this exact model/deck and authorize a single scoped run.",
            "A sensitivity-aware input validator must allow only the declared two stiffness/table overrides while keeping source inventories, geometry, material cards, equations, and CLOADs exact; existing baseline validators intentionally reject stiffness/law overrides and are not modified here.",
            "Recheck A12-rear selected-floor bearing/separation complementarity for this variant; do not inherit the baseline 25-cell mask as an accepted state or auto-iterate it.",
            "Use the unchanged native known-answer SPRINGA method fixture and response recovery, then check this run's all-carrier table domains, nonlinear laws, floor gates, and all-50-body/global equilibrium.",
            "Compare output only as conditional sensitivity relative to the frozen baseline response; this does not establish physical stiffness bounds or joint acceptance.",
        ],
        "prepared_outputs": {
            "model_json_sha256": sha256(model_path),
            "model_inp_sha256": sha256(deck_path),
        },
    }
    (PACKET / "variant.json").write_text(json.dumps(manifest, indent=2) + "\n")

    print(json.dumps({
        "status": manifest["status"],
        "model_json_sha256": manifest["prepared_outputs"]["model_json_sha256"],
        "model_inp_sha256": manifest["prepared_outputs"]["model_inp_sha256"],
        "variant_json_sha256": sha256(PACKET / "variant.json"),
        "changed_model_json_paths": sorted(actual_paths),
        "deck_changed_lines_1based": [row["deck_line_1based"] for row in deck_changes],
    }, indent=2))


if __name__ == "__main__":
    main()
