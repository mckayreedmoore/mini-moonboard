"""Source-only structure/scope review of the frozen generic fixture design."""
from __future__ import annotations

import argparse
import ast
import hashlib
import importlib.util
import json
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

sys.dont_write_bytecode = True
OWN = Path(__file__).resolve()
ROOT = next(p for p in OWN.parents if (p / "AGENTS.md").is_file())
PACKET = OWN.parents[2]
TARGETS = {
    "inputs.json": "b17a8f72f41ab2b8ce75ffaac15af075432a0ffe7111daead6597cb34eff86be",
    "design.py": "4c84897e42d4d32b1692bec8801a3c002b1c5684f984a907bde8e2cc73e4a3db",
    "result.json": "ec1c101da8f16f29cf0949c75086418e01e3b89268f55e27379fdb6a83a212f5",
    "result.svg": "60b5b105d42d35350bfe5a263f1c997974f7b3f9b1a27eea0317f88a84bd37c7",
    "verify.py": "b91887fa829c4bda60332dd1541ef26f3648d4613c5725e7f6a25d74e4cd3513",
    "verification-v1.json": "28fe869385596b6b09b562ee009654da491c7fc4e10013de99ba6edc5977aab4",
}


def require(ok, message):
    if not ok:
        raise AssertionError(message)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    return json.loads(path.read_bytes())


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def native_modules():
    return [name for name in sys.modules if name == "cadquery" or name == "OCP" or name.startswith("OCP.") or name in ("numpy", "scipy")]


def output_controls(design):
    """No temporary leaves or symlinks: use existing reads and inert mocks."""
    checked = []
    for path, label in ((PACKET / "result.json", "existing_result"),
                        (PACKET / "wrong.txt", "non_JSON"),
                        (PACKET / "controls01/nested.json", "nested_output")):
        try:
            design.output_paths(path)
        except ValueError:
            checked.append(label)
        else:
            raise AssertionError("output control accepted: " + label)
    leaf = PACKET / "_structure_inert_fixture.json"
    for occupied in (leaf, leaf.with_suffix(".svg")):
        with patch.object(design.os.path, "lexists", side_effect=lambda path, occupied=occupied: Path(path) == occupied):
            try:
                design.output_paths(leaf)
            except ValueError:
                checked.append("occupied_" + occupied.suffix[1:] + "_inert_leaf")
            else:
                raise AssertionError("occupied output leaf accepted")
    fake_parent = MagicMock()
    fake_parent.resolve.return_value = PACKET
    requested = SimpleNamespace(parent=fake_parent, suffix=".json", name=leaf.name)
    with patch.object(design.os.path, "lexists", return_value=False):
        destination, svg = design.output_paths(requested)
    fake_parent.resolve.return_value = ROOT
    require(destination == leaf and svg == leaf.with_suffix(".svg"), "canonical binding retained caller alias")
    checked.append("parent_alias_retarget_inert_after_binding")
    require(fake_parent.resolve.call_count == 1, "parent alias revisited after binding")
    return checked


def review():
    require(not native_modules(), "source-only review process required")
    inp, saved, verification = (read(PACKET / name) for name in ("inputs.json", "result.json", "verification-v1.json"))
    targets = {str((PACKET / name).relative_to(ROOT)): digest for name, digest in TARGETS.items()}
    require(len(saved["source_sha256"]) == saved["source_pin_count"] == 17, "17 direct source pins required")
    require(all(saved["source_sha256"][ref["path"]] == ref["sha256"] for ref in inp["sources"].values()), "input/source join differs")
    pins = {**saved["source_sha256"], **targets}
    numerical = ROOT / "fea/generated/thin-bolted-current-contact-v1/eoere-successor-v1/adjusted-base-mechanics-v1"
    retained = [numerical / "current-cases-v1" / name for name in ("result-v1.json", "parent-verification-v1.json")]
    retained.append(numerical / "current-component-results-v1/summary.json")
    retained_pins = {str(path.relative_to(ROOT)): sha(path) for path in retained}
    pins.update(retained_pins)
    before = {name: sha(ROOT / name) for name in pins}
    require(before == pins, "frozen target/source hash mismatch")
    contexts = {name: sha(ROOT / name) for name in ("AGENTS.md", "docs/wood-joints-mvp/README.md", "docs/wood-joints-mvp/completion-ledger.md")}
    design = load(PACKET / "design.py", "structure_generic_fixture_design_v1")
    verifier = load(PACKET / "verify.py", "structure_generic_fixture_verifier_v1")
    replay_inp, replay, shapes = design.evaluate()
    require(replay_inp == inp and replay == {key: value for key, value in saved.items() if key != "drawing"}, "source-only result replay differs")
    picture = design.drawing(inp, replay, shapes)
    require(picture == (PACKET / "result.svg").read_bytes(), "drawing byte replay differs")
    require(saved["drawing"] == {"path": str((PACKET / "result.svg").relative_to(ROOT)), "sha256": TARGETS["result.svg"], "bytes": len(picture), "scale_is_not_a_template": True}, "result/drawing binding differs")
    require(verifier.decimal_checks(saved) == verification["independent_decimal_checks"], "saved pure Decimal checks differ")
    require(verification["passed"] is True and verification["before_after_frozen_packet_and_sources_unchanged"] is True and verification["verification_method_sha256"] == TARGETS["verify.py"], "issued verification provenance differs")
    require(verification["frozen_four_file_sha256"] == {name: TARGETS[name] for name in ("inputs.json", "design.py", "result.json", "result.svg")}, "verification source binding differs")
    guards = output_controls(design)

    coordinates = saved["four_station_coordinate_joins"]
    support = saved["support_and_clamp_requirements"]
    budget = saved["pointwise_error_and_reach_budget"]
    retainer = saved["guide_and_retainer_requirements"]
    d = inp["dimensions_mm"]
    require(len(coordinates) == 4 and len(saved["parts"]) == 8, "four stations/eight temporary parts required")
    require({row["hand"] for row in coordinates} == {"left", "right"} and all(row["fixture_entry_uvw_mm"][1] == 180 and abs(row["fixture_entry_uvw_mm"][2]-88.9) < 1e-8 for row in coordinates), "handed datum joins differ")
    require(all(abs(row["cleat_bottom_to_axis_mm"]-40.3) < 1e-8 and abs(row["post_top_to_axis_mm"]-58.9) < 1e-8 for row in coordinates), "proposal ties differ")
    require(len(support["pad_rectangles_uv_mm"]) == len(support["clamp_arm_plan_lanes_uv_mm"]) == 4 and support["four_simultaneous_clamps_required"] is True, "independent clamp ownership differs")
    require(len(support["source_profile_and_recorded_cut_checks"]) == 14 and all(row["minimum_profile_margin_mm"] >= 0 and row["minimum_recorded_bore_margin_mm"] > 0 for row in support["source_profile_and_recorded_cut_checks"]), "support footprint/cut relationship differs")
    require(support["minimum_chuck_nose_to_clamp_lane_margin_mm"] > 0 and support["full_drill_clamp_handle_hand_or_workholding_qualification"] is False, "local clearance/qualification scope differs")
    require(d["cleat_support_v"][0] > d["post_height"] and abs(d["cleat_support_w"][1]-d["backer_w"][1]-d["member_thickness"]) < 1e-8, "independent riser/backer support levels differ")
    require(retainer["retainer_radial_capture_lip_mm"] > 0 and retainer["conditional_cap_hole_swept_bit_radial_margin_mm"] > 0 and "actual product is unselected" in retainer["guide_ID"], "generic guide requirement scope differs")
    require(budget["actual_terms_observed_or_achieved"] is False and budget["allocated_sum_mm"] <= budget["relative_bore_screw_bound_mm"], "budget/actual boundary differs")
    require("Actual bit" in budget["chip_clearing_scope"] and "Overall bit length is not usable projection" in " ".join(saved["limits"]), "bit reach/chip-exit inputs missing")
    require(saved["status"] == "UNADOPTED_DIMENSIONED_SOURCE_ONLY_FIXTURE_REQUIREMENTS" and saved["current_Z_mm"] == 200 and saved["proposed_Z_mm"] == 180 and saved["current_geometry_or_100_axes_or_66_screws_changed"] is False, "current/proposal boundary differs")
    require(saved["saved_signed_end_scope"]["current_Z200_actions_assigned_to_Z180"] is False and saved["saved_signed_end_scope"]["complete_Cdelta_or_strength"] is None, "action/capacity transfer differs")
    require(all(value is False for value in saved["release"].values()) and saved["release"] == inp["release"] == verification["release"], "release flags differ")
    require(all(row["Actual"] == row["Disposition"] == "" for row in saved["actual_observations"]), "actual observations populated")
    require(len(saved["genuine_missing_inputs"]) == 6 and len(saved["planned_sequence"]) == 7, "explicit missing inputs/sequence differ")
    svg = ET.fromstring(picture)
    require(svg.attrib["viewBox"] == "0 0 1600 1260", "drawing bounds differ")
    text = " ".join(svg.itertext())
    for value in ("Z180 is unadopted", "v139.70", "113.125 nominal / 113.825 worst", "19.05", "actual tools", "Actuals remain blank", "This drawing authorizes no cut"):
        require(value.lower() in text.lower(), "drawing/source claim or dimension missing: " + value)
    tree = ast.parse((PACKET / "design.py").read_bytes())
    top_imports = [node for node in tree.body if isinstance(node, (ast.Import, ast.ImportFrom))]
    require(not any(any(name in ast.unparse(node) for name in ("cadquery", "OCP", "numpy", "scipy")) for node in top_imports), "native/scientific top-level import")
    prepare = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == "prepare")
    whole = [node for node in ast.walk(prepare) if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr == "run_path"]
    require(len(whole) == 1 and "hardware_method" in ast.unparse(whole[0]), "unexpected whole source module execution")
    require(not native_modules(), "scalar review imported native modules")
    require({name: sha(ROOT / name) for name in pins} == before, "frozen sources or current responses changed")
    require({name: sha(ROOT / name) for name in contexts} == contexts, "maintained context changed")
    ruff = subprocess.run([str(ROOT / ".venv/bin/ruff"), "check", str(OWN)], cwd=ROOT, capture_output=True, text=True, check=False)
    require(ruff.returncode == 0, "own Ruff failed: " + ruff.stdout + ruff.stderr)
    return {
        "schema": "eoere_Z180_fixture_structure_scope_review/v1", "review_helper_sha256": sha(OWN),
        "frozen_target_sha256": targets, "context_sha256": contexts, "findings": [],
        "integrity": {"target_files": 6, "direct_source_pins": 17, "verified_union_including_retained_numerical_records": len(pins), "unchanged_before_after": True, "retained_current_numerical_sha256": retained_pins},
        "source_reuse": {"authenticated_scalar_profile_datum_capsule_functions_reused": True, "existing_stdlib_AST_loader_reused": True, "whole_CAD_or_frame_modules_executed": False, "saved_native_evidence_authenticated_without_requery": True, "full_inherited_native_source_closures_independently_reaudited": False},
        "checks": {"result_and_SVG_byte_replay_exact": True, "saved_Decimal_checks_reproduced": True, "inert_or_read_only_output_controls": guards, "SVG_XML_and_claims_checked": True, "new_visual_render_or_browser": False, "source_profile_contact_rectangles": 14, "independent_clamp_lanes": 4, "temporary_fixture_parts": 8, "handed_coordinate_joins": 4},
        "ownership_and_scope": {"canonical_bound_JSON_SVG_destinations_and_exclusive_creation": True, "generic_requirements_are_not_catalog_selection": True, "fixture_attachment_workholding_force_and_full_tool_access_unqualified": True, "full_path_budget_is_requirement_not_observed_accuracy": True, "chip_exit_flute_and_projection_requirements_distinct": True, "actual_and_disposition_cells_blank": True, "current_Z200_authority_and_responses_unchanged": True, "Z180_unadopted_and_no_force_strength_transfer": True, "all_release_flags_false": True, "prior_attempts_sources_and_current_reports_active_without_pruning": True},
        "ruff": {"command": ".venv/bin/ruff check " + str(OWN.relative_to(ROOT)), "exit_code": ruff.returncode, "output": ruff.stdout.strip()},
        "limits": ["Standard-library reads, scalar replay and inert mocks only; no CAD/native/BREP/FEA/global/browser/physical execution.", "Generic fixture design requirements were reviewed within their declared scope. No catalog product, bit, clamp or actual fixture is selected or qualified.", "SVG source and exact generated bytes were checked; no new render or visual inspection is claimed.", "Current numerical records were hashed only. No current Z200 actions were assigned to Z180 and no complete-joint resistance was evaluated.", "Existing full source closures and native observations were not independently re-audited. No frozen source/shared docs/model/index edits, deletion, staging or commit."],
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    receipt = review()
    path = OWN.with_name("receipt.json")
    if args.write:
        with path.open("x") as stream:
            stream.write(json.dumps(receipt, sort_keys=True, indent=2, allow_nan=False) + "\n")
        print(json.dumps({"path": str(path.relative_to(ROOT)), "sha256": sha(path), "findings": 0}))
    else:
        print(json.dumps(receipt, sort_keys=True, indent=2, allow_nan=False))


if __name__ == "__main__":
    main()
