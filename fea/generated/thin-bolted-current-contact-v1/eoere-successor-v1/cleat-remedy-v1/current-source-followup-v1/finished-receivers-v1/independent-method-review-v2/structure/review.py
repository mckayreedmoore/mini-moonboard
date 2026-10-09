"""Source-only review of the separate frozen v2 finished-receiver adapter."""
from __future__ import annotations

import argparse
import ast
import copy
import hashlib
import importlib.util
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
    "query-v2.py": "88edea7a233963e32f6d56fc7fd0dd86322acc65f69bbefdd4f53cc01d919912",
    "inputs.json": "1480f590f0b870a86acf489b780d4eb34c4ef7760a8dc88bc0c70c58b311bf24",
    "parent-method-readiness-v2.json": "b1d4e988f0af656f5d9b967af31a62e019e84625cdd4a4e70f5d27810efffe5a",
    "runs-v1/method02/result.json": "e054fbd0fd9015f31a17c0c3887937e00a3793c2f40795c53e9ea535db50e2e7",
}
FROZEN_V1 = {
    "query.py": "b9a888032c19a7616619bb27355aa2aeb5a0ade862aa748ad08d80ababd0ebfb",
    "parent-method-readiness-v1.json": "4c32ef7dd354049921f88511dbba969775701379634c9b8764030d7cc3208e09",
    "runs-v1/method01/result.json": "f833ad8f03a3cedaab27c9af4c91a0584a808cfce183958b75d3536499c7750a",
    "independent-method-review-v1/structure/review.py": "65406ee05e8dc124d3f2507d319ec45b674424b5d8bfa712e485cad9e5d8a2c0",
    "independent-method-review-v1/structure/receipt.json": "5fde190f31a4953cc9b28cd0d4ff54bb4b96bc9f354d0340958f99b6f1fab117",
}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require(ok, message):
    if not ok:
        raise AssertionError(message)


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def output_entry_controls(wrapper, query):
    """Replace only the delegate closure; exercise guards without any output IO."""
    cell = next(cell for name, cell in zip(query.main.__code__.co_freevars, query.main.__closure__, strict=True) if name == "original_main")
    original = cell.cell_contents
    results = {}
    for mode, parts, symlink, exists in (
        ("fresh", ("runs-v1", "inert-new"), False, False),
        ("occupied", ("runs-v1", "method02"), False, True),
        ("dangling_symlink", ("runs-v1", "inert-link"), True, False),
        ("parent_traversal", ("runs-v1", "method02", "..", "inert-new"), False, False),
    ):
        events = []
        fake = SimpleNamespace(parts=parts, is_symlink=lambda symlink=symlink: symlink, exists=lambda exists=exists: exists)
        parser = MagicMock()
        parser.parse_known_args.return_value = (SimpleNamespace(outdir=fake), [])
        cell.cell_contents = lambda events=events: events.append("original_main_stub")
        try:
            with patch.object(wrapper.argparse, "ArgumentParser", return_value=parser):
                try:
                    query.main()
                    error = None
                except ValueError as caught:
                    error = str(caught)
        finally:
            cell.cell_contents = original
        require(events == (["original_main_stub"] if mode == "fresh" else []), "raw entry guard delegated unexpectedly")
        require((error is None) == (mode == "fresh"), "raw entry guard result differs")
        results[mode] = {"events": events, "error": error, "filesystem_writes": 0}
    require(cell.cell_contents is original, "private delegate closure not restored")
    return results, original


def review():
    for name, digest in {**TARGETS, **FROZEN_V1}.items():
        require(sha(PACKET / name) == digest, "frozen target changed: " + name)
    common = load(PACKET / "independent-method-review-v1/structure/review.py", "frozen_v1_architecture_checks")
    require(not common.native_modules(), "native modules already loaded")
    inp = common.read(PACKET / "inputs.json")
    toy = common.read(PACKET / "runs-v1/method02/result.json")
    v1 = common.read(PACKET / "independent-method-review-v1/structure/receipt.json")
    permit = common.read(PACKET / "parent-method-readiness-v2.json")
    pins = {**inp["source_sha256"], **{str((PACKET / name).relative_to(ROOT)): digest for name, digest in {**TARGETS, **FROZEN_V1}.items()}}
    pins.update(v1["retained_prior_packets_sha256"])
    before = {name: sha(ROOT / name) for name in pins}
    require(before == pins, "frozen source union changed")
    context = {name: sha(ROOT / name) for name in ("AGENTS.md", "docs/wood-joints-mvp/README.md")}
    require(permit["fixtures_authorized"] is True and permit["candidate_query_authorized"] is False and permit["prerequisite_results"] == [], "fixture-only authority differs")
    require(permit["release"] == inp["release"] == toy["release"] and all(value is False for value in permit["release"].values()), "release boundary differs")
    require(toy["query_sha256"] == TARGETS["query-v2.py"] and toy["inputs_sha256"] == TARGETS["inputs.json"] and toy["pass"] is True, "issued toy provenance differs")
    require(toy["parent_readiness"] == {"path": str((PACKET / "parent-method-readiness-v2.json").relative_to(ROOT)), "sha256": TARGETS["parent-method-readiness-v2.json"]}, "toy readiness binding differs")
    require(len(inp["source_sha256"]) == 38 and len(toy["source_sha256"]) == 42, "source counts differ")
    require(all(pins[name] == digest for name, digest in toy["source_sha256"].items()), "toy source closure differs")
    require(toy["fixtures"] == common.read(PACKET / "runs-v1/method01/result.json")["fixtures"], "reported toy observations differ")
    require(toy["fixtures"]["known_answer_or_negative_checks"] == 7 and toy["fixtures"]["candidate_BREP_imports"] == 0, "toy scope differs")
    require(toy["runtime"] == inp["runtime"] and toy["sources_unchanged_before_after"] is True, "toy runtime/integrity differs")

    wrapper = load(PACKET / "query-v2.py", "frozen_four_receiver_wrapper_v2")
    query = wrapper.load_adapter()
    other = wrapper.load_adapter()
    require(query is not other and query.source_inventory is not other.source_inventory, "adapter state is not private")
    require(query.OWN == PACKET / "query-v2.py" and query.HERE == PACKET, "query/readiness ownership differs")
    for name in ("methods", "method_fixtures", "reconstruct", "local_axes", "query_scenario", "write"):
        require(Path(getattr(query, name).__code__.co_filename) == PACKET / "query.py", "native/output method was copied or overridden: " + name)
    with patch.object(query.platform, "python_version", return_value=inp["runtime"]["python"]), patch.object(
        query.importlib.metadata, "version", side_effect=lambda name: inp["runtime"][name]
    ):
        admitted, source_union, _, _ = query.preflight(PACKET / "parent-method-readiness-v2.json", True)
        require(admitted == inp and len(source_union) == 41, "v2 preflight source union differs")
        require(source_union[str((PACKET / "query.py").relative_to(ROOT))] == FROZEN_V1["query.py"], "legacy source omitted from gate")
        try:
            query.preflight(PACKET / "parent-method-readiness-v2.json", False)
        except ValueError as error:
            require(str(error) == "mode not authorized by parent", "candidate failure differs")
        else:
            raise AssertionError("candidate mode authorized unexpectedly")
    geometry, axes, proposed, members, cuts = query.source_inventory(inp)
    counts = {"current_axes": len(geometry["axes"]), "current_screws": len(geometry["screw_axes"]), "current_axis_map": len(axes), "proposed_axes": len(proposed), "hosts": len(members), "own_cuts": sum(map(len, cuts.values()))}
    require(counts == {"current_axes": 100, "current_screws": 66, "current_axis_map": 100, "proposed_axes": 4, "hosts": 4, "own_cuts": 16}, "source-only inventory scope differs")
    saved = common.read(ROOT / inp["analytic_result"]["path"])
    require(common.canonical(members) == common.canonical(saved["affected_members"]) and common.canonical(list(proposed.values())) == common.canonical(saved["proposed_axes"]), "canonical inventory differs")
    controls, original_main = output_entry_controls(wrapper, query)
    # Reuse the frozen inert original-main checks rather than copy their logic.
    adapted_main = query.main
    query.main = original_main
    try:
        inherited = {mode: common.mock_main(query, copy.deepcopy(inp), permit, toy["runtime"], mode) for mode in (
            "fresh_fixture", "existing_output", "busy_lock", "changed_source")}
    finally:
        query.main = adapted_main
    require(query.main is adapted_main, "private main not restored")
    require(not common.native_modules(), "review imported native modules")
    tree = ast.parse((PACKET / "query-v2.py").read_bytes())
    require(not any("cadquery" in ast.unparse(node) or "OCP" in ast.unparse(node) for node in tree.body if isinstance(node, (ast.Import, ast.ImportFrom))), "wrapper native import")
    require({name: sha(ROOT / name) for name in pins} == before, "review changed source or retained evidence")
    require({name: sha(ROOT / name) for name in context} == context, "review context drifted")
    ruff = subprocess.run([str(ROOT / ".venv/bin/ruff"), "check", str(OWN)], cwd=ROOT, capture_output=True, text=True, check=False)
    require(ruff.returncode == 0, "own Ruff failed: " + ruff.stdout + ruff.stderr)
    return {
        "schema": "eoere_finished_receiver_v2_architecture_method_review/v1",
        "target_sha256": TARGETS,
        "retained_v1_sha256": FROZEN_V1,
        "review_helper_sha256": sha(OWN),
        "context_sha256": context,
        "source_integrity": {"input_pins": 38, "preflight_before_readiness_pin": 41, "toy_union_pins": 42, "review_verified_union_including_retained_prior_packets": len(pins), "input_map_canonical_sha256": common.canonical(inp["source_sha256"]), "unchanged_before_after": True, "prior_packets_checked_from_frozen_v1_receipt": len(v1["retained_prior_packets_sha256"])},
        "findings": [],
        "assessment": {"v1_tuple_list_blocker_resolved_by_canonical_join": True, "native_methods_reused_unchanged_from_pinned_private_v1_module": True, "legacy_adapter_in_preflight_and_toy_source_union": True, "private_overrides_do_not_mutate_v1_or_peer_module_state": True, "candidate_query_authorized": False, "toy_fixtures_independently_rerun_by_this_review": False, "geometry_or_physical_acceptance": False, "serial_lock_fresh_output_exclusive_result_inherited": True, "raw_output_entry_guards": controls, "inherited_inert_orchestration": inherited},
        "source_only_inventory_counts": counts,
        "ruff": {"command": ".venv/bin/ruff check " + str(OWN.relative_to(ROOT)), "exit_code": ruff.returncode, "output": ruff.stdout.strip()},
        "limits": ["Standard-library reads, hashes, source intake and inert mocks only. No CAD/BREP/FEA/frame/browser/candidate query or native toy rerun.", "Pinned runtime metadata was mocked for preflight; no independent runtime qualification.", "Passing seven method fixtures are source-bound geometry-method evidence, not a candidate finished-solid observation or mechanics/physical release.", "All original v1 source/readiness/toy/review bytes and prior source packets remain active and unchanged; no deletion, source/docs/model/shop changes or publication.", "Existing complete source closures and numerical operators were not independently re-audited."],
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    receipt = review()
    output = OWN.with_name("receipt.json")
    if args.write:
        with output.open("x") as stream:
            stream.write(json.dumps(receipt, sort_keys=True, indent=2, allow_nan=False) + "\n")
        print(json.dumps({"path": str(output.relative_to(ROOT)), "sha256": sha(output), "findings": 0}))
    else:
        print(json.dumps(receipt, sort_keys=True, indent=2, allow_nan=False))


if __name__ == "__main__":
    main()
