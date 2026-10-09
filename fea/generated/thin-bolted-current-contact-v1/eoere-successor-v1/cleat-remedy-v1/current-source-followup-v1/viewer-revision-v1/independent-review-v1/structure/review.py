"""Source-only ownership/provenance review of the frozen Z180 viewer preview."""
from __future__ import annotations

import argparse
import ast
import copy
import gzip
import hashlib
import importlib.util
import json
import re
import subprocess
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.dont_write_bytecode = True
OWN = Path(__file__).resolve()
ROOT = next(p for p in OWN.parents if (p / "AGENTS.md").is_file())
PACKET = OWN.parents[2]
MANIFEST_SHA = "9bd09c57b337c7176d3965e79d620341d2d63b4aeec1b5afbd36d191786f7310"
HISTORY = "bedb85b8d6ce2cf7f2b2d61cb458e428c3dc4d7c"
MODEL = "eoere-lower-cleat-z180-development"


def require(ok, message):
    if not ok:
        raise AssertionError(message)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()).hexdigest()


def read(path):
    return json.loads(path.read_bytes())


def native_modules():
    return [name for name in sys.modules if name == "cadquery" or name == "OCP" or name.startswith("OCP.")]


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def union(*maps):
    result = {}
    for mapping in maps:
        for name, digest in mapping.items():
            require(name not in result or result[name] == digest, "conflicting source pin: " + name)
            result[name] = digest
    return result


def review():
    require(not native_modules(), "review must remain source-only")
    manifest_path = PACKET / "review-target-v1.json"
    require(sha(manifest_path) == MANIFEST_SHA, "review manifest changed")
    manifest = read(manifest_path)
    require(manifest["schema"] == "eoere_lower_cleat_z180_source_review_target/v1" and len(manifest["files"]) == 11, "target scope differs")
    inp = read(PACKET / "inputs.json")
    issued = read(PACKET / "runs-v1/export01/export-result.json")
    layout = read(PACKET / "runs-v1/export01/layout.json")
    mesh_check = read(PACKET / "mesh-check-v1.json")
    native = read(ROOT / inp["native_result"])
    output_pins = {row["path"]: row["sha256"] for row in issued["output"].values()}
    audit_exports = issued["saved_receiver_audit"]["export_sha256"]
    pins = union(manifest["files"], inp["source_sha256"], issued["source_sha256"], mesh_check["source_sha256"],
                 native["source_sha256"], output_pins, audit_exports, {str(manifest_path.relative_to(ROOT)): MANIFEST_SHA})
    # Hash only these preserved numerical artifacts; no saved-field consumption.
    mechanics = ROOT / "fea/generated/thin-bolted-current-contact-v1/eoere-successor-v1/adjusted-base-mechanics-v1"
    retained = [mechanics / "current-cases-v1" / name for name in ("result-v1.json", "parent-verification-v1.json")]
    retained.append(mechanics / "current-component-results-v1/summary.json")
    retained_pins = {str(path.relative_to(ROOT)): sha(path) for path in retained}
    pins = union(pins, retained_pins)
    before = {name: sha(ROOT / name) for name in pins}
    require(before == pins, "frozen target/source/output hash mismatch")
    contexts = {name: sha(ROOT / name) for name in ("AGENTS.md", "docs/wood-joints-mvp/README.md", "docs/wood-joints-mvp/completion-ledger.md")}

    exporter = load(PACKET / "export.py", "structure_z180_display_export")
    with patch.object(exporter.platform, "python_version", return_value=inp["runtime"]["python"]), patch.object(
        exporter.importlib.metadata, "version", side_effect=lambda name: inp["runtime"][name]
    ):
        _, prepared_pins, runtime, descriptor, bodies, audit = exporter.prepare()
    require(descriptor == layout and prepared_pins == issued["source_sha256"] and runtime == issued["runtime"], "source-only preparation differs from issued output")
    require(audit == issued["saved_receiver_audit"] and audit["pass"] is True, "saved-field consumer audit differs")
    require(len(prepared_pins) == 15 and len(bodies) == 4 and len(descriptor["axis_changes"]) == 4 and len(descriptor["receiver_datums"]) == 8, "display scope differs")
    require(descriptor["status"] == "UNADOPTED_GEOMETRY_PREVIEW" and descriptor["saved_response_transferred"] is False and descriptor["complete_joint_resistance"] is None, "authority/response/capacity boundary differs")
    require(all(value is False for value in descriptor["release"].values()), "release flags differ")
    require(all(row["bit_instruction"] is None and row["actual"] is None for row in descriptor["receiver_datums"]), "nominal datums became actual or bit instructions")

    # Negative readiness and repository-source controls do not change any file.
    controls = []
    actual_read = exporter.read
    for flag in ("only_four_saved_BREP_display_tessellations", "native_mechanics_or_full_frame_CAD_authorized", "geometry_adoption_authorized_by_this_file"):
        def controlled_read(path, flag=flag):
            value = actual_read(path)
            if Path(path) == PACKET / "parent-readiness.json":
                value = copy.deepcopy(value)
                value[flag] = not value[flag]
            return value
        with patch.object(exporter, "read", controlled_read):
            try:
                exporter.prepare()
            except ValueError as error:
                require(str(error) == "bounded parent readiness required", "wrong readiness rejection")
            else:
                raise AssertionError("unbounded display readiness accepted")
        controls.append(flag)
    for name in ("../AGENTS.md", str(ROOT / "AGENTS.md")):
        try:
            exporter.verify({name: "0" * 64})
        except ValueError as error:
            require(str(error) == "canonical repository source required", "wrong source path rejection")
        else:
            raise AssertionError("noncanonical source accepted")

    # A failed reservation must stop before the native import or helper load.
    out, fake_here = MagicMock(), MagicMock()
    fake_here.__truediv__.return_value = out
    out.parent.resolve.return_value = out.parent.absolute.return_value
    out.mkdir.side_effect = FileExistsError("inert occupied issued output")
    with patch.object(exporter, "HERE", fake_here), patch.object(exporter, "prepare", return_value=({}, {}, {}, {}, {}, {})), patch.object(exporter, "load", side_effect=AssertionError("unexpected native/export helper load")):
        try:
            exporter.main()
        except FileExistsError:
            pass
        else:
            raise AssertionError("occupied output entry accepted")
    require(out.mkdir.call_count == 1 and not native_modules(), "failed reservation reached native execution")

    scene_path = ROOT / "site/eoere-lower-cleat-z180-scene.json.gz"
    scene_bytes = scene_path.read_bytes()
    decoded = gzip.decompress(scene_bytes)
    scene = json.loads(decoded)
    require(scene_bytes == (PACKET / "runs-v1/export01/scene.json.gz").read_bytes(), "site asset differs from issued export")
    require(hashlib.sha256(decoded).hexdigest() == issued["scene_decoded_sha256"], "decoded scene differs")
    require(len(scene["replacements"]) == 4 and len(scene["bolt_translations"]) == 4 and "parts" not in scene, "whole scene copied into patch")
    require(scene["parent_scene"] == inp["parent_scene"] and scene["layout_report"]["sha256"] == sha(PACKET / "runs-v1/export01/layout.json"), "parent/descriptor binding differs")
    require(scene["counts"]["physical_bolt_axes"] == 100 and scene["counts"]["screw"] == 66 and scene["optional_2026_extra"] is False, "retained hardware/grid scope differs")
    require(scene["release"] == descriptor["release"] and scene["saved_response_transferred"] is False and scene["complete_joint_resistance"] is None, "scene claims differ")
    for row in scene["replacements"]:
        require(row["source_brep_sha256"] == bodies[row["name"]]["sha256"], "display receiver provenance differs")
    require(all(row["translation_xyz_mm"] == [0, 0, -20] for row in scene["bolt_translations"]), "hardware move differs")

    old_bytes = subprocess.run(["git", "show", HISTORY + ":site/index.html"], cwd=ROOT, capture_output=True, check=True).stdout
    old_index, index = old_bytes.decode(), (ROOT / "site/index.html").read_text()
    def model_choices(text):
        section = text[text.index("const woodJointModels"):text.index("const isWoodJoint")]
        return dict(re.findall(r"\['([^']+)', '([^']*)'\]", section))
    prior_choices, choices = model_choices(old_index), model_choices(index)
    require(len(prior_choices) == 14 and len(choices) == 15 and set(choices)-set(prior_choices) == {MODEL}, "historical model choices differ")
    require(all(choices[name] == label for name, label in prior_choices.items()), "historical model label changed")
    require('href="?model=eoere-extended-cleat-frame-development&view=rear">Current eoere geometry' in index, "current authority link changed")
    require("Current six-case results remain bound to Z200" in index and "Drilling, tool access and revised joint resistance unresolved" in index, "preview boundaries missing")
    old_loader = next(line.strip() for line in old_index.splitlines() if "const sceneLoader =" in line)
    new_loader = next(line.strip() for line in index.splitlines() if "const sceneLoader =" in line)
    require(new_loader.replace("lowerCleatZ180 ? loadLowerCleatPreviewScene : ", "") == old_loader, "historical loader route changed")
    overlay = (ROOT / "site/eoere-lower-cleat-z180-overlay.mjs").read_text()
    require("loadExtendedCleatBaseScene(THREE" in overlay and "part.geometry.clone().translate(0, 0, -20)" in overlay, "parent/stack reuse differs")
    require("old.get(name).geometry?.dispose()" in overlay and "for (const geometry of allocated) geometry.dispose()" in overlay, "replacement/failure resource ownership differs")
    require("analysis_pass_transferred: false" in overlay and "physical_release: false" in overlay and "qualified_for_design: false" in overlay, "viewer metadata claims differ")
    require("planning_mass_kg: null" in overlay, "parent planning mass transferred")
    tree = ast.parse((PACKET / "export.py").read_bytes())
    require(not any("cadquery" in ast.unparse(node) or "OCP" in ast.unparse(node) for node in tree.body if isinstance(node, (ast.Import, ast.ImportFrom))), "native top-level import")
    require(mesh_check["passed"] is True and mesh_check["unchanged_parts"] == 997 and mesh_check["replaced_receivers"] == 4 and mesh_check["translated_bolt_components"] == 20 and len(mesh_check["rejected_controls"]) == 13 and mesh_check["rejected_hash_options"] == 3 and mesh_check["mechanics_or_physical_release"] is False, "issued Three.js check scope differs")
    require(not native_modules(), "native module imported during source review")
    require({name: sha(ROOT / name) for name in pins} == before, "target/source/history changed during review")
    require({name: sha(ROOT / name) for name in contexts} == contexts, "maintained context changed")
    ruff = subprocess.run([str(ROOT / ".venv/bin/ruff"), "check", str(OWN)], cwd=ROOT, capture_output=True, text=True, check=False)
    require(ruff.returncode == 0, "own Ruff failed: " + ruff.stdout + ruff.stderr)
    return {
        "schema": "eoere_z180_viewer_architecture_review/v1", "review_helper_sha256": sha(OWN),
        "target_manifest": {"path": str(manifest_path.relative_to(ROOT)), "sha256": MANIFEST_SHA},
        "frozen_target_sha256": manifest["files"], "context_sha256": contexts, "findings": [],
        "provenance": {"verified_union_files": len(pins), "native_result_direct_source_pins_hashed": len(native["source_sha256"]), "issued_export_source_pins": len(issued["source_sha256"]), "saved_BREP_bytes_hashed_only": len(audit_exports), "unchanged_before_after": True, "current_numerical_records_retained_sha256": retained_pins, "native_queries_rerun": False},
        "source_intake": {"descriptor_matches_issued_layout": True, "existing_saved_result_consumer_reused": True, "metadata_mocked_to_pinned_versions": True, "rejected_readiness_controls": controls, "rejected_noncanonical_source_paths": 2, "occupied_output_mock_stops_before_native_import": True},
        "ownership": {"shared_stdlib_display_mesh_exporter_reused": True, "whole_CAD_or_frame_modules_imported": False, "four_receiver_patch_bytes": len(scene_bytes), "unchanged_visible_parts_reused": 997, "translated_existing_hardware_components": 20, "new_receiver_meshes": 4, "new_whole_model_asset": False, "failed_or_historical_files_pruned_or_replaced": False, "serialization_owner": "parent; exporter does not acquire its own native lock", "issued_output_directory": "exclusive fixed runs-v1/export01; reproduction needs separately owned fresh output, never overwrite issued bytes"},
        "authority_and_history": {"preview_unadopted": True, "current_Z200_geometry_and_responses_preserved": True, "current100_axes_and66_screws_retained": True, "Z200_action_transfer_or_joint_capacity": False, "extra_grid_preview_enabled": False, "historical_model_options_retained": len(prior_choices), "comparison_commit": HISTORY, "comparison_index_sha256": hashlib.sha256(old_bytes).hexdigest(), "existing_loader_routes_retained": True, "current_authority_link_preserved": True, "all_release_flags_false": True},
        "issued_ThreeJS_evidence": {"review_reran_check": False, "source_bound": True, "rejected_claim_controls": 13, "rejected_hash_options": 3},
        "ruff": {"command": ".venv/bin/ruff check " + str(OWN.relative_to(ROOT)), "exit_code": ruff.returncode, "output": ruff.stdout.strip()},
        "limits": ["Standard-library/source/synthetic review only; no CAD/native/BREP/tessellation/mechanics/browser execution.", "Saved geometry audit replays source identities and saved observations; BREP files were hashed, not queried. Current numerical records were hashed only.", "Native runtime metadata was mocked for source-only prepare; this does not qualify the runtime. Parent owns serialization and browser validation.", "All frozen targets, issued outputs, current geometry/responses, historical choices and dependent packets remain active and unchanged. No shared edits, staging, commit or publication.", "This preview cannot establish drilling/tool/installation, changed-case action, complete-joint resistance, physical acceptance or release."],
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
