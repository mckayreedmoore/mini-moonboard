"""Bounded shop-adapter architecture/source review; genuine outputs stay held.

Run authenticated metadata prepare only, with the deferred builder disabled.
Read/hash frozen sources and inspect pure helper selection; generate no CSV/SVG.
"""
from __future__ import annotations

import ast
import builtins
import hashlib
import json
import runpy
import sys
from pathlib import Path
from unittest.mock import patch

OWN = Path(__file__).resolve()
ROOT = next(p for p in OWN.parents if (p / "AGENTS.md").is_file())
HERE = OWN.parents[2]
EXPECTED = {
    "adapter.py": "805dd6afe0921cb14f7e24fea4974714de6ee4c94cc50e74daca3b5595c951c2",
    "test_adapter.py": "e243ed889154b21f4f380ee20c6a012cda87f80bc5ffdb1d42240cf11767eddb",
    "inputs.json": "24168aba426c8a3e65035e877b03fc58347a3c00f450980cba9319f4d6e19918",
    "preflight.json": "cd7e28c42e59f41d9fae96378a5cc1cf005a5b04cbc7613db23088fef1a08854",
}


def sha(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def read(path):
    return json.loads(path.read_bytes())


def relative(path):
    return path.relative_to(ROOT).as_posix()


def canonical(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()).hexdigest()


def join(pins, extra):
    for name, digest in extra.items():
        assert name not in pins or pins[name] == digest
        pins[name] = digest


def main():
    assert all(sha(HERE / name) == digest for name, digest in EXPECTED.items())
    inp, preflight = read(HERE / "inputs.json"), read(HERE / "preflight.json")
    descriptor = read(ROOT / inp["sources"]["descriptor"]["path"])
    profiles = read(ROOT / inp["saved_files"]["current_profiles.json"]["path"])
    pins = {relative(HERE / "inputs.json"): EXPECTED["inputs.json"], inp["helper"]["path"]: inp["helper"]["sha256"]}
    join(pins, {ref["path"]: ref["sha256"] for ref in inp["sources"].values()})
    join(pins, {ref["path"]: ref["sha256"] for ref in inp["saved_files"].values()})
    join(pins, descriptor["source_sha256"])
    join(pins, {row["finished"]["path"]: row["finished"]["sha256"] for row in profiles.values()})
    generated_before = sorted(relative(path) for pattern in ("*.csv", "*.svg") for path in HERE.glob(pattern))
    assert generated_before == []

    def unchanged():
        assert all(sha(HERE / name) == digest for name, digest in EXPECTED.items())
        assert all(sha(Path(path) if Path(path).is_absolute() else ROOT / path) == digest for path, digest in pins.items())
        assert sorted(relative(path) for pattern in ("*.csv", "*.svg") for path in HERE.glob(pattern)) == generated_before

    unchanged()
    subject = runpy.run_path(str(HERE / "adapter.py"))
    globals_ = subject["prepare"].__globals__
    original_import = builtins.__import__

    def guarded_import(name, *args, **kwargs):
        assert name.split(".")[0] not in {"cadquery", "OCP", "OCC", "build123d", "numpy", "scipy"}
        return original_import(name, *args, **kwargs)

    def held_builder(*args, **kwargs):
        raise AssertionError("genuine output builder remains held")

    with patch.dict(globals_, {"build_outputs": held_builder}), patch.object(builtins, "__import__", guarded_import):
        bundle = subject["prepare"](HERE / "inputs.json", EXPECTED["inputs.json"])
    assert bundle["pins"] == pins and len(pins) == preflight["source_pin_count"] == 1141
    assert canonical(pins) == preflight["source_map_canonical_sha256"]
    assert bundle["inputs"] == inp and bundle["data"]["profiles"] == profiles
    assert preflight["helper"] == inp["helper"]
    assert preflight["inputs"] == {"path": relative(HERE / "inputs.json"), "sha256": EXPECTED["inputs.json"]}
    assert inp["release"] == preflight["release"] == subject["RELEASE"] and not any(inp["release"].values())
    assert inp["execution_scope"]["genuine_candidate_output_trial_authorized"] is False
    assert preflight["readiness"]["genuine_nominal_output_trial"] is False
    assert preflight["open_inputs"] == subject["OPEN_INPUTS"]
    methods = {"shop": sorted(vars(bundle["shop"])), "datum": sorted(vars(bundle["datum"])), "draw": sorted(vars(bundle["draw"]))}
    assert methods == {
        "shop": ["canonical", "drawings", "put", "require", "sha", "table", "vector"],
        "datum": ["add", "csv_bytes", "dot", "json_bytes", "local", "require", "scale", "subtract", "world"],
        "draw": ["SVG", "hull"],
    }
    assert not hasattr(bundle["shop"], "build") and not hasattr(bundle["shop"], "main")
    data = bundle["data"]
    for name in ("members.csv", "receiver-holes.csv", "bolt-stacks.csv", "access-sides.csv", "panel-screw-datums.csv", "panel-machining.csv"):
        subject["blank_observations"](data[name][1])
    assert all(row["current_tool_access_disposition"] == row["current_axial_removal_disposition"] == "UNVERIFIED" for row in data["access-sides.csv"][1])
    assert all(row["part_receiving_disposition"] == "UNVERIFIED" for row in data["bolt-stacks.csv"][1])
    assert len(bundle["old_axes"]) == len(bundle["new_axes"]) == 100
    assert {name for name in bundle["old_axes"] if bundle["old_axes"][name] != bundle["new_axes"][name]} == set(subject["AXES"])
    assert all(bundle["old_axes"][name]["point_xyz_mm"][2] == 200.
               and bundle["new_axes"][name]["point_xyz_mm"][2] == 180.
               and bundle["new_axes"][name]["nominal_under_head_length_mm"] == 101.6 for name in subject["AXES"])
    assert len(bundle["scenario"]["wall_queries"]) == 16
    assert sum(row["changed_axis"] for row in bundle["scenario"]["wall_queries"]) == 8
    role_ids = {role["id"] for shaft in descriptor["shafts"] if shaft["axis_id"] in subject["AXES"] for role in shaft["metal_roles"]}
    assert len(role_ids) == 20
    assert {sorted(profiles).index(host)//7+1 for host in subject["HOSTS"]} == {1, 3}
    expected_census = {"raw_profiles": 28, "timbers": 22, "panels": 6, "stock_sticks": 13,
        "nominal_board_feet": 150, "nominal_bolt_recipes": 100, "receiver_hole_occurrences": 120,
        "head_nut_access_sides": 200, "Hillman_screw_datums": 66, "panel_machining_features": 340}
    assert preflight["protected_saved_census"] == expected_census
    inherited_drawings, inherited_data = subject["REUSED_DRAWINGS"], subject["UNCHANGED_FILES"]
    assert len(inherited_drawings) == 6 and len(inherited_data) == 5 and len(subject["CHANGED_DRAWINGS"]) == 3
    assert preflight["deferred_changes"]["inherited_drawing_links"] == {name: inp["saved_files"][name] for name in inherited_drawings}
    assert preflight["deferred_changes"]["inherited_data_links"] == {name: inp["saved_files"][name] for name in inherited_data}
    for host in subject["HOSTS"]:
        observation = bundle["observations"][host]
        assert observation["source_only_analytic_centroid"] is True
        assert observation["provenance"]["new_native_COM_query_performed"] is False
    tree = ast.parse((HERE / "adapter.py").read_bytes())
    imports = {node.module.split(".")[0] for node in ast.walk(tree) if isinstance(node, ast.ImportFrom)}
    imports.update(alias.name.split(".")[0] for node in ast.walk(tree) if isinstance(node, ast.Import) for alias in node.names)
    assert imports <= sys.stdlib_module_names
    functions = {node.name: node for node in tree.body if isinstance(node, ast.FunctionDef)}
    assert "main" not in functions
    metadata_calls = {node.func.attr for node in ast.walk(functions["prepare"]) if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)}
    assert not (metadata_calls & {"drawings", "SVG", "csv_bytes", "json_bytes", "write_text", "write_bytes"})
    assert not any(isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "build_outputs"
                   for node in ast.walk(functions["prepare"]))
    assert not any(isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
                   and node.func.attr in {"write_text", "write_bytes", "mkdir", "unlink"} for node in ast.walk(tree))
    assert not any(name in sys.modules for name in ("cadquery", "OCP", "numpy", "scipy"))
    unchanged()
    receipt = {
        "schema": "eoere_z180_proposal_shop_independent_structure_review/v1",
        "status": "CLEAN_SOURCE_METADATA_AND_DEFERRED_PURE_ADAPTER_SCOPE", "findings": [],
        "target_sha256": {relative(HERE / name): digest for name, digest in EXPECTED.items()},
        "release": inp["release"], "all_release_false": True,
        "source_closure": {"pins_verified_before_after": len(pins), "canonical_sha256": canonical(pins),
                           "exact_direct_refs_saved19_descriptor_closure_and_finished_sources_union": True,
                           "source_refs": inp["sources"], "closure_is_not_a_complete_historical_shop_producer_claim": True},
        "checks": {"metadata_prepare_ran_with_genuine_builder_disabled": True,
                   "no_candidate_CSV_SVG_or_manifest_bytes_generated": True,
                   "selected_pure_method_names": methods, "stdlib_imports": sorted(imports),
                   "protected_saved_census": expected_census,
                   "four_Z200_to_Z180_axes_96_other_axes_and_original4in_recipe": True,
                   "six_drawing_and_five_data_links_keep_original_paths_hashes_and_namespaces": True,
                   "own_saved16_walls_four_native_sources_separate_analytic_COM_and_twenty_roles": True,
                   "all_Actual_Disposition_blank_and_installed_access_unverified": True,
                   "all_frozen_Z200_HOLD_sources_and_proposal_inputs_unchanged": True},
        "architecture": {
            "ownership": "The separate adapter owns source joins, allowed row edits and the future proposal byte map. The authenticated old exporter contributes only selected pure CSV/vector/drawing definitions, datum helper only selected transforms/serializers, and drawing helper only hull/SVG. Old top-level code, build, axis-equality and Z200/HOLD contracts are excluded from execution and remain unchanged.",
            "datums": "Receiving coordinates are measured in each preserved raw-profile datum and own basis. Only four axis points move20mm; own interval/direction/full-wall joins govern eight moved and eight retained source rebindings. Modeled bore/shaft/hardware envelopes keep their analysis labels; catalog/nominal comparisons and local datum projections establish no bit, delivered shank, tool or installation acceptance.",
            "native_vs_analytic": "Saved native receiver paths, hashes, volumes, bounds and16 walls keep their original saved-result binding. Four future finished records use explicit analytic_center_xyz_mm and analytic_center_source, with no new native COM claim. Twenty role centers come from the exact source-only Z180 descriptor. No old Z200 force/pass, spacer or4.5in substitution is transferred.",
            "deferred_output": "prepare creates metadata only. build_outputs remains a deferred pure byte-map API with no writer or CLI. A future authorized trial must independently own fresh reservation/publication and verify its emitted bytes; this clean review does not issue tables, drawings or operation instructions.",
            "retention": "Six unchanged plates and five unchanged data records remain exact original-path links. Future own bytes are limited to changed tables/profile provenance,20 roles/source bindings and three changed drawings. Original Z200/current authority and HOLD instructions stay active and unchanged; no copied CAD, cache, manuals, raw assets, archive or cleanup action is added.",
        },
        "limits": ["Source-only unadopted method and metadata review; the genuine build_outputs call and output-byte equality remain deferred.",
                   "No candidate CSV/SVG generation, CAD/BREP query, native method, mechanics input/K/q/force/solve, other docs or Git operation.",
                   "Native full walls and analytic COM do not establish end/edge/net-section or complete-joint resistance. Actual observations remain blank, and physical tool access/placement tolerances remain unresolved.",
                   "No physical or sign-off prerequisite is added by this review."],
        "review_artifacts": {"helper": relative(OWN), "helper_sha256": sha(OWN), "receipt": relative(OWN.with_name("receipt.json"))},
    }
    OWN.with_name("receipt.json").write_text(json.dumps(receipt, indent=2, sort_keys=True, allow_nan=False) + "\n")
    print(json.dumps({"status": receipt["status"], "findings": 0, "pins": len(pins),
                      "helper_sha256": sha(OWN), "receipt_sha256": sha(OWN.with_name("receipt.json"))}))


if __name__ == "__main__":
    main()
