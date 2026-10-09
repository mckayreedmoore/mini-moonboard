"""Bounded source/ownership/retention review; no spacer calculation execution."""
from __future__ import annotations

import argparse
import ast
import contextlib
import hashlib
import importlib.util
import io
import json
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

sys.dont_write_bytecode = True
OWN = Path(__file__).resolve()
ROOT = next(p for p in OWN.parents if (p / "AGENTS.md").is_file())
PACKET = OWN.parents[2]
TARGETS = {
    "spacer-window-inputs-v1.json": "9326e6cfb8280760c47d00dace8967b84eecccbf813f5ea2e7dfb96841b49813",
    "spacer-window-v1.py": "59f429916ff26f897f5ace94fee610b0e420e261094e9f10659e937b44b0b3d6",
    "spacer-window-result-v1.json": "592c237e8f98456f936deaf3b8613f60c493008851e65f43a9fbde6300929896",
}
RECOVERY = Path("/home/mckay-linux/repos/mini-moonboard-cleanup-backups-navigation-v1")
RECOVERY_PINS = {
    "recovery-plan.json": "bcc2e8622fc4be3fe06fb5623e6f18085c657c9509eec027f123b78758a7b0af",
    "required-inputs.json": "7a2fc1e21801263ef3062350469c290cc562f1cb9e35aae352c39eec9fd689da",
    "eoere-current-input-gaps-v1.tar.gz.manifest.json": "1698cc4e67df800551e5e8bb595e95167bc314fe09fe9a656cfaedbb0c33b056",
}


def require(ok, message):
    if not ok:
        raise AssertionError(message)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    return json.loads(path.read_bytes())


def review():
    inputs, result, old = (read(PACKET / n) for n in ("spacer-window-inputs-v1.json", "spacer-window-result-v1.json", "result-v3.json"))
    pins = dict(result["source_sha256"])
    for name, digest in TARGETS.items():
        path = str((PACKET / name).relative_to(ROOT))
        require(path not in pins or pins[path] == digest, "target/source contradiction")
        pins[path] = digest
    before = {name: sha(ROOT / name) for name in pins}
    require(before == pins and len(old["source_sha256"]) == 31 and len(result["source_sha256"]) == result["source_pin_count"] == 34, "source/target join differs")
    require(all(result["source_sha256"][n] == h for n, h in old["source_sha256"].items())
            and all(result["source_sha256"][n] == h for n, h in inputs["sources"].items()), "inherited source pins changed")
    contexts = ("AGENTS.md", "docs/wood-joints-mvp/README.md", "docs/wood-joints-mvp/completion-ledger.md", "CONTRIBUTING.md", "docs/repository-cleanup-evaluation-2026-09-28.md")
    context_before = {n: sha(ROOT / n) for n in contexts}
    recovery_before = {n: sha(RECOVERY / n) for n in RECOVERY_PINS}
    require(recovery_before == RECOVERY_PINS, "documented recovery records changed")
    plan = {row["original_path"]: row for row in read(RECOVERY / "recovery-plan.json")["files"]}
    required = read(RECOVERY / "required-inputs.json")
    manifest = read(RECOVERY / "eoere-current-input-gaps-v1.tar.gz.manifest.json")
    members = {row["path"]: row for row in manifest["files"]}
    commit = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True, check=True).stdout.strip()
    coverage = {}
    restored = []
    for name, digest in pins.items():
        committed = subprocess.run(["git", "show", commit + ":" + name], cwd=ROOT, capture_output=True, check=False)
        if committed.returncode == 0 and hashlib.sha256(committed.stdout).hexdigest() == digest:
            coverage[name] = "committed_exact"
        elif name in {str((PACKET / n).relative_to(ROOT)) for n in TARGETS}:
            coverage[name] = "new_owned_publication_target"
        else:
            require(name in plan and required[str(ROOT / name)] == digest, "non-Git source lacks documented exact recovery: " + name)
            row = plan[name]
            require(row["sha256"] == digest and row["size"] == (ROOT / name).stat().st_size
                    and row["manifest"] == "eoere-current-input-gaps-v1.tar.gz.manifest.json"
                    and members[row["member"]]["sha256"] == digest
                    and members[row["member"]]["size"] == row["size"], "recovery map/member mismatch")
            coverage[name] = "documented_exact_external_recovery"
            restored.append({"path": name, "sha256": digest, "bytes": row["size"], "member": row["member"]})
    require(len(restored) == 4 and (RECOVERY / manifest["archive_file"]).is_file(), "inherited recovery boundary differs")

    source = PACKET / "spacer-window-v1.py"
    tree = ast.parse(source.read_bytes())
    helper_name = next(n for n in inputs["sources"] if n.endswith("/shop_windows.py"))
    helper_tree = ast.parse((ROOT / helper_name).read_bytes())
    for parsed in (tree, helper_tree):
        imported = [node for node in parsed.body if isinstance(node, (ast.Import, ast.ImportFrom))]
        require(all(all(word not in ast.unparse(node) for word in ("cadquery", "OCP", "numpy", "scipy")) for node in imported), "non-source-only import")
    functions = {node.name for node in tree.body if isinstance(node, ast.FunctionDef)}
    require("bounds_for" not in functions and "measured_window" not in functions, "shared window implementation copied")
    helper_calls = [node.func.slice.value for node in ast.walk(tree) if isinstance(node, ast.Call)
                    and isinstance(node.func, ast.Subscript) and isinstance(node.func.value, ast.Name)
                    and node.func.value.id == "helper" and isinstance(node.func.slice, ast.Constant)]
    require(set(helper_calls) == {"bounds_for", "measured_window"} and len(helper_calls) == 3, "pure-helper use differs")
    loader_calls = [node for node in ast.walk(tree) if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr == "run_path"]
    require(len(loader_calls) == 1 and "helper_path" in ast.unparse(loader_calls[0]), "unexpected whole-module execution")
    spec = importlib.util.spec_from_file_location("spacer_structure_source_only_target", source)
    method = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(method)
    inert = []
    for label, argv, error_type, message in (
        ("help", ["--help"], SystemExit, "0"),
        ("nested_output", ["--out", str(PACKET / "controls01/_spacer_structure.json")], ValueError, "owned JSON output required"),
        ("non_JSON", ["--out", str(PACKET / "_spacer_structure.txt")], ValueError, "owned JSON output required"),
        ("occupied_output", ["--out", str(PACKET / "spacer-window-result-v1.json")], ValueError, "fresh output required"),
    ):
        with patch.object(sys, "argv", [str(source), *argv]), patch.object(method, "evaluate") as evaluate, patch.object(Path, "open") as opened, contextlib.redirect_stdout(io.StringIO()):
            try:
                method.main()
            except error_type as error:
                require(str(error) == message, "unexpected output rejection: " + label)
            else:
                raise AssertionError("output guard accepted: " + label)
            require(not evaluate.called and not opened.called, "invalid output triggered evaluation or file access")
            inert.append(label)
    leaf = PACKET / "_spacer_structure_never_created.json"
    with patch.object(sys, "argv", [str(source), "--out", str(leaf)]), patch.object(method.os.path, "lexists", return_value=True), patch.object(method, "evaluate") as evaluate:
        try:
            method.main()
        except ValueError as error:
            require(str(error) == "fresh output required" and not evaluate.called, "occupied/dangling leaf guard differs")
        else:
            raise AssertionError("occupied/dangling output accepted")
    inert.append("occupied_or_dangling_JSON_entry")
    fake_parent = MagicMock()
    fake_parent.resolve.return_value = PACKET
    requested = SimpleNamespace(parent=fake_parent, suffix=".json", name=leaf.name)
    def retarget_after_binding():
        fake_parent.resolve.return_value = ROOT
        return {}
    with patch.object(method.argparse.ArgumentParser, "parse_args", return_value=SimpleNamespace(out=requested)), patch.object(method.os.path, "lexists", return_value=False), patch.object(method, "evaluate", side_effect=retarget_after_binding), patch.object(Path, "open", autospec=True, side_effect=FileExistsError("inert late collision")) as opened:
        try:
            method.main()
        except FileExistsError:
            opened.assert_called_once_with(leaf, "x")
        else:
            raise AssertionError("exclusive output guard missing")
    require(fake_parent.resolve.call_count == 1 and not leaf.exists(), "canonical output binding revisited or inert output created")
    inert.append("canonical_parent_binding_and_exclusive_late_collision_inert")

    require(result["status"] == "UNADOPTED_NOMINAL_DIMENSIONAL_FEASIBILITY" and result["spacer_catalog_candidate"] == inputs["spacer"], "nominal scenario/catalog join differs")
    spacer = inputs["spacer"]
    require(spacer["sku"] == 13731 and spacer["length_tolerance_mm"] is None and spacer["diameter_tolerances_mm"] is None and spacer["numeric_yield_or_compression_capacity"] is None, "unknown product tolerance/resistance invented")
    require(result["current_revision"] == old["current_revision"]
            and result["current_100_axes_canonical_sha256"] == old["current_100_axes_canonical_sha256"]
            and result["current_66_screw_axes_canonical_sha256"] == old["current_66_screw_axes_canonical_sha256"], "current authority/census changed")
    require([r["axis_id"] for r in result["station_comparisons"]] == inputs["axis_ids"] == [r["axis_id"] for r in old["four_stations"]], "four-station identity join differs")
    require(all(r["current_point_xyz_mm"] == o["current_point_xyz_mm"] and r["unadopted_proposed_point_xyz_mm"] == o["unadopted_proposed_point_xyz_mm"] and not r["spacer_removal_continuous_clearance_verified"] for r, o in zip(result["station_comparisons"], old["four_stations"], strict=True)), "current/proposal/removal claim differs")
    require(not result["nominal_contact_geometry"]["full_spacer_end_face_supported_by_washer"] and not result["nominal_contact_geometry"]["material_compression_washer_bending_eccentricity_or_joint_resistance_verified"], "coaxial overlap promoted to capacity")
    require(result["release"] == inputs["release"] and all(v is False for v in result["release"].values())
            and result["actual_observations"] == inputs["actual_observations"] and all(v == "" for v in result["actual_observations"].values()), "actuals/release changed")
    require("nut side only" in " ".join(result["limits"]) and "own six-case forces stay unchanged" in " ".join(result["limits"]), "nut-side/force boundary absent")
    require(result["dated_incremental_cost_before_shipping_tax_usd"]["current_hardware_basket_and_mass_unchanged"] and spacer["observed_utc"].startswith("2026-10-09"), "dated comparison promoted to adopted purchase")
    require({name: sha(ROOT / name) for name in pins} == before and {n: sha(RECOVERY / n) for n in RECOVERY_PINS} == recovery_before, "source/history/recovery drift")
    require(not any(n == "cadquery" or n == "OCP" or n.startswith("OCP.") or n in ("numpy", "scipy") for n in sys.modules), "native import occurred")
    ruff = subprocess.run([str(ROOT / ".venv/bin/ruff"), "check", "--no-cache", str(OWN)], cwd=ROOT, capture_output=True, text=True, check=False)
    require(ruff.returncode == 0, "own Ruff failed: " + ruff.stdout + ruff.stderr)
    return {
        "schema": "eoere_nut_side_spacer_structure_review/v1", "review_helper_sha256": sha(OWN), "frozen_target_sha256": TARGETS, "findings": [],
        "integrity": {"prior_H_source_pins": 31, "new_result_source_pins": 34, "source_target_union": len(pins), "unchanged_before_after": True,
                      "review_commit": commit, "Git_recovery_or_owned_publication_coverage": coverage, "documented_recovery_record_sha256": RECOVERY_PINS,
                      "four_inherited_non_Git_sources": restored, "exact_external_recovery_root": str(RECOVERY), "archive_contents_not_reaudited_or_restored": True},
        "architecture_and_ownership": {"existing_bounds_for_and_measured_window_reused": helper_name,
                                       "shared_math_not_copied_no_CAD_or_mechanics_module_import": True,
                                       "new_evaluate_and_shared_helper_functions_not_executed": True,
                                       "canonical_owned_JSON_destination_exclusive_creation": True, "inert_output_controls": inert,
                                       "new_three_file_bytes": 34419, "old_sources_snapshots_failed_results_and_current_reports_preserved": True},
        "claim_boundary": {"single_13731_nut_side_spacer_and_4p5in_bolt_unadopted_nominal_scenario": True,
                           "unknown_spacer_tolerances_material_strength_fit_and_tool_removal_conditions_explicit": True,
                           "annular_overlap_not_full_face_support_or_capacity": True, "cost_is_dated_increment_only_current_basket_and_mass_unchanged": True,
                           "current_Z200_100_shafts_66_screws_HOLD_fields_and_Z180_preview_unchanged": True,
                           "no_current_force_transfer_actuals_blank_release_false": True},
        "context": {"before_sha256": context_before, "after_sha256": {n: sha(ROOT / n) for n in contexts}, "parent_owns_later_maintained_summary_updates": True},
        "ruff": {"command": ".venv/bin/ruff check --no-cache " + str(OWN.relative_to(ROOT)), "exit_code": ruff.returncode, "output": ruff.stdout.strip()},
        "limits": ["Source/AST/hash reads and inert main guard mocks only. No spacer evaluate, shared window calculation, target CLI output, native/CAD/BREP/FEA/global/browser/physical or new method run.",
                   "Existing external recovery records and selected manifest entries were authenticated; no archive restore, broad historical source audit or clean-checkout execution was performed.",
                   "Catalog observations are frozen source claims, not a fresh product/price verification, selection, delivered fit or material qualification. Numerical correctness is owned by separate review.",
                   "No target/shared docs/site/index edits, staging, commit, archive/prune or geometry/force/resistance/physical acceptance change."],
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
        print(json.dumps({"path": str(path.relative_to(ROOT)), "sha256": sha(path), "findings": len(receipt["findings"])}))
    else:
        print(json.dumps(receipt, sort_keys=True, indent=2, allow_nan=False))


if __name__ == "__main__":
    main()
