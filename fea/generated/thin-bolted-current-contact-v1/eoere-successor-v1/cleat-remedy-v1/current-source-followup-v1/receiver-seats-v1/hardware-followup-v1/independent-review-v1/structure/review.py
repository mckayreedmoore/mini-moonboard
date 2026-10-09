"""Bounded structure/provenance/retention review of frozen scalar hardware work.

Only JSON/CSV/source reads and the existing stdlib scalar evaluate API run.
No target CLI, CAD, native method, global/current component field or model runs.
Writes the owned compact receipt only.
"""
from __future__ import annotations

import ast
import csv
import hashlib
import json
import runpy
import sys
from pathlib import Path

OWN = Path(__file__).resolve()
ROOT = next(p for p in OWN.parents if (p / "AGENTS.md").is_file())
HERE = OWN.parents[2]
EXPECTED = {
    "inputs.json": "6cba1fb87b9cfa337f2c5418afe6c0f7fa6def8d6ae463e9f355701df3d75e33",
    "calculate.py": "ed7a16cbdb97bf15ddc74e2af49bb3b512dc57c7541358392db55ea25d8dfc0e",
    "result.json": "fbe6983488fc5c3017810654f43df0e0ef2188657387cc6a3b92b4e02fbb4c0a",
}


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(path):
    return json.loads(Path(path).read_bytes())


def canonical(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()).hexdigest()


def relative(path):
    return Path(path).relative_to(ROOT).as_posix()


def main():
    assert all(sha(HERE / path) == digest for path, digest in EXPECTED.items())
    inp, result = read(HERE / "inputs.json"), read(HERE / "result.json")
    pins = result["source_sha256"]
    assert len(pins) == result["source_pin_count"] == 27
    assert all(pins[ref["path"]] == ref["sha256"] for ref in inp["sources"].values())
    prior_manifest_ref = inp["sources"]["frozen_receiver_packet"]
    prior = read(ROOT / prior_manifest_ref["path"])
    old_files = prior["final_files"] + prior["retained_development_files"]
    assert len(old_files) == 10

    def unchanged():
        assert all(sha(HERE / path) == digest for path, digest in EXPECTED.items())
        assert all(sha(ROOT / path) == digest for path, digest in pins.items())
        assert all(pins[row["path"]] == row["sha256"] and sha(ROOT / row["path"]) == row["sha256"]
                   and (ROOT / row["path"]).stat().st_size == row["bytes"] for row in old_files)

    unchanged()
    sources = [HERE / "calculate.py", *[ROOT / inp["sources"][key]["path"] for key in ("hardware_method", "corner_method", "window_method")]]
    stdlib_imports = {}
    for path in sources:
        tree = ast.parse(path.read_bytes())
        names = {node.module.split(".")[0] for node in tree.body if isinstance(node, ast.ImportFrom)}
        names.update(alias.name.split(".")[0] for node in tree.body if isinstance(node, ast.Import) for alias in node.names)
        assert names <= sys.stdlib_module_names
        stdlib_imports[relative(path)] = sorted(names)
    subject = runpy.run_path(str(HERE / "calculate.py"))
    reproduced = subject["evaluate"]()
    assert canonical(reproduced) == canonical(result)
    geometry = read(ROOT / inp["sources"]["geometry"]["path"])
    placement = read(ROOT / inp["sources"]["placement"]["path"])
    axes = {row["id"]: row for row in geometry["axes"]}
    proposed = {row["id"]: row for row in placement["proposed_axes"]}
    assert len(axes) == 100 and len(geometry["screw_axes"]) == 66
    assert {row["axis_id"] for row in result["four_stations"]} == set(inp["axis_ids"]) == set(proposed)
    for row in result["four_stations"]:
        assert row["current_point_xyz_mm"] == axes[row["axis_id"]]["point_xyz_mm"]
        assert row["current_point_xyz_mm"][2] == result["current_axes_stay_Z_mm"] == 200
        assert row["unadopted_proposed_point_xyz_mm"] == proposed[row["axis_id"]]["point_xyz_mm"]
        assert row["unadopted_proposed_point_xyz_mm"][2] == result["proposed_Z_mm_unadopted"] == 180
        assert row["matched_wood_travel_mm"] == 76.2 and row["planning_usable_bit_reach_mm"] == 101.6
        assert [comparison["sku"] for comparison in row["comparisons"]] == [367, 368]
        assert all(comparison["actual_fit_or_access_or_thread_bearing_verified"] is False for comparison in row["comparisons"])
    for key in ("stacks", "access", "holes"):
        with (ROOT / inp["sources"][key]["path"]).open(newline="") as stream:
            rows = list(csv.DictReader(stream))
        assert all(value == "" for row in rows for name, value in row.items() if name.startswith("Actual") or name == "Disposition")
    assert result["washer_and_fillet_limits"]["full_nominal_annular_seat_proof_covers_all_catalog_corners"] is False
    assert result["washer_and_fillet_limits"]["actual_washer_material_or_contact_or_fillet_seating_verified"] is False
    assert result["conditional_tool_outline_from_existing_method"]["status"] == "conditional maximum envelopes; no measured or selected tools"
    assert all(flag is False for flag in result["release"].values())
    assert not any(module in sys.modules for module in ("cadquery", "OCP", "numpy", "scipy"))
    unchanged()
    receipt = {
        "schema": "eoere_cleat_hardware_scalar_independent_structure_review/v1",
        "status": "PASS_NO_SUBSTANTIAL_FINDINGS_SCALAR_SOURCE_SCOPE",
        "confirmed_findings": [],
        "target_sha256": {relative(HERE / path): digest for path, digest in EXPECTED.items()},
        "source_checks": {"pins_verified_before_after": 27, "source_map_canonical_sha256": canonical(pins),
                          "all_ten_prior_receiver_files_unchanged": True,
                          "prior_frozen_manifest": prior_manifest_ref,
                          "scalar_evaluate_canonical_result_matches_frozen": True,
                          "exact_four_current_stations": inp["axis_ids"], "current_Z_mm": 200, "unadopted_proposed_Z_mm": 180,
                          "all100_current_axes_and66_screws_retained": True, "Actual_Disposition_cells_remain_blank": True,
                          "stdlib_imports": stdlib_imports},
        "architecture": {
            "ownership": "The followup owns four-station joins and scalar specification comparisons; hardware.pure_functions selects the authenticated bounds_for/number/require functions. Existing corner_check owns endpoint enumeration. TOOL is read as an AST literal.",
            "reuse_boundary": "runpy loads only standard-library modules and selects scalar callables. hardware.prepare and corner.evaluate are not called; window-method intake and access CAD module are not imported. No legacy geometry generator, force field, component reducer or swept-clear result is used.",
            "provenance": "The 27-pin closure is intentionally direct scalar/reference inputs plus all ten retained receiver files. Current geometry and placement digests bind complete 100/66 records. The four stations additionally match the preserved raised-rail complete records before scalar reuse. This is no claim of a complete historical producer closure.",
            "catalog_vs_actual": "Frozen catalog dimension boxes and retained uncoated ASME Lb/Lg scenario govern arithmetic. Current catalog reading remains a dated observation; external pages/image were not independently re-fetched by this review. Delivered coating, body/transition/root, actual dimensions, washer material and nut seating remain unverified.",
            "claim_boundary": "The 4in family retains positive catalog projection/gage comparisons with possible thread/runout bearing; 4.5in improves body coverage while retaining the failed nut-seating guarantee. Neither is adopted. Nominal washer support is not extended to every catalog ID/thickness/fillet corner. Drill reach, guide/backer and conditional tool/removal envelopes are planning inputs, with no tool, installation or physical acceptance.",
            "retention": "Three small frozen scalar records reuse shared helpers, catalog/reference inputs and ten preserved receiver records. Those witnesses and earlier failures remain active. This review creates no CAD/cache/manual/installation copy, raw external asset or cleanup action.",
        },
        "remaining": ["Current Z200 HOLD4 and the unadopted Z180 placement/receiver checks retain their separate authority.",
                      "Delivered stack/thread/root/washer/fillet measurements, guide registration/error budget and actual tool/removal envelopes remain exact missing inputs.",
                      "No scalar dimensional result establishes finished-geometry access, thread-bearing resistance, complete-joint strength, fabrication or climbing release."],
        "CAD_native_global_current_component_fields_or_model_execution": False,
        "target_shared_docs_index_staging_commit_or_cleanup_action": False,
        "review_artifacts": {"helper": relative(OWN), "helper_sha256": sha(OWN), "receipt": relative(OWN.with_name("receipt.json"))},
    }
    OWN.with_name("receipt.json").write_text(json.dumps(receipt, indent=2, sort_keys=True, allow_nan=False) + "\n")
    print(json.dumps({"status": receipt["status"], "pins": 27, "helper_sha256": sha(OWN),
                      "receipt_sha256": sha(OWN.with_name("receipt.json"))}))


if __name__ == "__main__":
    main()
