"""Frozen v1 architecture review: standard-library reads and inert mocks only."""
from __future__ import annotations

import argparse
import ast
import copy
import hashlib
import importlib.util
import io
import json
import subprocess
import sys
from contextlib import ExitStack, redirect_stdout
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

sys.dont_write_bytecode = True
OWN = Path(__file__).resolve()
ROOT = next(p for p in OWN.parents if (p / "AGENTS.md").is_file())
PACKET = OWN.parents[2]
TARGETS = {
    "query.py": "b9a888032c19a7616619bb27355aa2aeb5a0ade862aa748ad08d80ababd0ebfb",
    "inputs.json": "1480f590f0b870a86acf489b780d4eb34c4ef7760a8dc88bc0c70c58b311bf24",
    "parent-method-readiness-v1.json": "4c32ef7dd354049921f88511dbba969775701379634c9b8764030d7cc3208e09",
    "runs-v1/method01/result.json": "f833ad8f03a3cedaab27c9af4c91a0584a808cfce183958b75d3536499c7750a",
}


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
    return [n for n in sys.modules if n == "cadquery" or n == "OCP" or n.startswith("OCP.")]


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def mock_main(query, inp, permit, runtime, mode):
    """Exercise orchestration in memory, with all native entrypoints replaced."""
    events = []
    out = MagicMock()
    out.resolve.return_value = out
    out.parent = PACKET / "runs-v1"
    out.exists.return_value = mode == "existing_output"
    out.mkdir.side_effect = lambda **_: events.append("mkdir")
    fake_parser = MagicMock()
    fake_parser.parse_args.return_value = SimpleNamespace(
        permit=PACKET / "parent-method-readiness-v1.json", outdir=out, fixtures_only=True)
    fake_lock = MagicMock()
    fake_lock_path = MagicMock()
    fake_lock_path.open.return_value.__enter__.return_value = fake_lock

    def flock(*_):
        events.append("lock")
        if mode == "busy_lock":
            raise BlockingIOError("inert busy lock")

    def verify(_):
        events.append("verify")
        if mode == "changed_source":
            raise ValueError("inert changed source")

    def methods(_):
        events.append("methods_stub")
        return object()

    def fixtures(_):
        events.append("fixtures_stub")
        return {"candidate_BREP_imports": 0}

    def write(_, value):
        events.append("write_stub")
        require(value["sources_unchanged_before_after"] and value["pass"], "success record shape differs")

    with ExitStack() as stack:
        replacements = {
            "preflight": lambda *_: (inp, {}, permit, runtime),
            "Path": lambda _: fake_lock_path,
            "verify": verify,
            "methods": methods,
            "method_fixtures": fixtures,
            "write": write,
            "sha": lambda _: "0" * 64,
        }
        for name, value in replacements.items():
            stack.enter_context(patch.object(query, name, value))
        stack.enter_context(patch.object(query.argparse, "ArgumentParser", return_value=fake_parser))
        stack.enter_context(patch.object(query.fcntl, "flock", flock))
        stack.enter_context(redirect_stdout(io.StringIO()))
        try:
            query.main()
            error = None
        except (ValueError, BlockingIOError) as caught:
            error = type(caught).__name__
    expected = {
        "fresh_fixture": (["lock", "mkdir", "verify", "methods_stub", "fixtures_stub", "verify", "write_stub", "verify"], None),
        "existing_output": ([], "ValueError"),
        "busy_lock": (["lock"], "BlockingIOError"),
        "changed_source": (["lock", "mkdir", "verify"], "ValueError"),
    }
    require((events, error) == expected[mode], "inert orchestration differs: " + mode)
    return {"events": events, "error": error, "native_execution": False, "filesystem_writes": 0}


def review():
    require(not native_modules(), "review must start without native modules")
    inp = read(PACKET / "inputs.json")
    permit = read(PACKET / "parent-method-readiness-v1.json")
    toy = read(PACKET / "runs-v1/method01/result.json")
    targets = {str((PACKET / name).relative_to(ROOT)): digest for name, digest in TARGETS.items()}
    pins = {**inp["source_sha256"], **targets}
    require(len(inp["source_sha256"]) == 38 and len(toy["source_sha256"]) == 41, "source count differs")
    require(all(pins[path] == digest for path, digest in toy["source_sha256"].items()), "toy source union differs")
    contexts = [ROOT / "AGENTS.md", ROOT / "docs/wood-joints-mvp/README.md"]
    retained_names = ["inputs.json", "prepare.py", "placement.json", "result.json", "verify.py", "verification.json"]
    retained = [PACKET.parent / name for name in retained_names]
    retained += [PACKET.parent / "end-geometry-v1" / name for name in ("analyze.py", "result.json")]
    before = {path: sha(ROOT / path) for path in pins}
    require(before == pins, "frozen source hash mismatch")
    retained_before = {str(path.relative_to(ROOT)): sha(path) for path in retained}
    context_before = {str(path.relative_to(ROOT)): sha(path) for path in contexts}
    require(permit["fixtures_authorized"] is True and permit["candidate_query_authorized"] is False, "v1 candidate gate changed")
    require(permit["prerequisite_results"] == [], "v1 readiness is fixture-only")
    require(toy["pass"] is True and toy["sources_unchanged_before_after"] is True, "issued toy record differs")
    require(toy["runtime"] == inp["runtime"], "toy runtime differs")
    require(all(v is False for v in permit["release"].values()) and permit["release"] == toy["release"] == inp["release"], "release flags differ")
    require(toy["fixtures"]["known_answer_or_negative_checks"] == 7 and toy["fixtures"]["candidate_BREP_imports"] == 0, "toy scope differs")
    for ref in [*inp["helpers"].values(), inp["analytic_inputs"], inp["analytic_result"], inp["raw_post_manifest"], *inp["raw_post_sources"].values()]:
        require(inp["source_sha256"][ref["path"]] == ref["sha256"], "helper/input reference outside source union")

    query = load(PACKET / "query.py", "structure_frozen_four_receiver_query_v1")
    with patch.object(query.platform, "python_version", return_value=inp["runtime"]["python"]), patch.object(
        query.importlib.metadata, "version", side_effect=lambda name: inp["runtime"][name]
    ):
        admitted, _, _, _ = query.preflight(PACKET / "parent-method-readiness-v1.json", True)
        require(admitted == inp, "fixture preflight differs")
        try:
            query.preflight(PACKET / "parent-method-readiness-v1.json", False)
        except ValueError as error:
            require(str(error) == "mode not authorized by parent", "wrong candidate rejection")
        else:
            raise AssertionError("candidate mode unexpectedly authorized")
    try:
        query.source_inventory(inp)
    except ValueError as error:
        require(str(error) == "analytic source inventory differs", "unexpected inventory failure")
    else:
        raise AssertionError("expected frozen v1 schema boundary failure absent")
    analytic = query.module(inp["helpers"]["analytic_inventory"], "structure_receiver_inventory_v1")
    bound = query.read(ROOT / inp["analytic_inputs"]["path"])
    data = {key: query.read(ROOT / ref["path"]) for key, ref in bound["sources"].items() if ref["path"].endswith(".json")}
    datum = query.module(bound["sources"]["datum_helper"], "structure_receiver_datum_v1")
    _, proposed, members, _ = analytic.existing_inventory(bound, data, datum)
    prior = query.read(ROOT / inp["analytic_result"]["path"])
    require(members != prior["affected_members"] and canonical(members) == canonical(prior["affected_members"]), "tuple/list diagnosis differs")
    require(list(proposed.values()) == prior["proposed_axes"], "proposed axis inventory differs")
    name = next(iter(members))
    require(isinstance(members[name]["YZ_polygon_mm"][0], tuple) and isinstance(prior["affected_members"][name]["YZ_polygon_mm"][0], list), "vertex representation differs")

    # Confirm the CAD-heavy source modules are AST function dependencies only.
    tree = ast.parse((PACKET / "query.py").read_bytes())
    top_imports = [node for node in tree.body if isinstance(node, (ast.Import, ast.ImportFrom))]
    require(not any("cadquery" in ast.unparse(node) or "OCP" in ast.unparse(node) for node in top_imports), "native top-level import")
    methods = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == "methods")
    whole_imports = [node for node in ast.walk(methods) if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "module"]
    require(len(whole_imports) == 1 and "pure_loader" in ast.unparse(whole_imports[0]), "unexpected whole helper import")
    mock_checks = {mode: mock_main(query, copy.deepcopy(inp), permit, toy["runtime"], mode) for mode in (
        "fresh_fixture", "existing_output", "busy_lock", "changed_source")}
    require(not native_modules(), "review imported native modules")
    require({path: sha(ROOT / path) for path in pins} == before, "sources changed during review")
    require({path: sha(ROOT / path) for path in retained_before} == retained_before, "prior packet changed")
    require({path: sha(ROOT / path) for path in context_before} == context_before, "maintained context changed")
    ruff = subprocess.run([str(ROOT / ".venv/bin/ruff"), "check", str(OWN)], cwd=ROOT, capture_output=True, text=True, check=False)
    require(ruff.returncode == 0, "own Ruff failed: " + ruff.stdout + ruff.stderr)
    return {
        "schema": "eoere_finished_receiver_v1_architecture_method_review/v1",
        "target_sha256": targets,
        "review_helper_sha256": sha(OWN),
        "context_sha256": context_before,
        "source_pins": {"input_count": 38, "toy_union_count": 41, "verified_union_count_including_toy": len(pins), "input_map_canonical_sha256": canonical(inp["source_sha256"]), "unchanged_before_after": True},
        "retained_prior_packets_sha256": retained_before,
        "findings": [{
            "severity": "P2",
            "location": str((PACKET / "query.py").relative_to(ROOT)) + ":168",
            "issue": "The live pure inventory uses tuple YZ vertices; frozen JSON uses list vertices. Direct equality rejects identical serialized inventories.",
            "impact": "V1 candidate orchestration cannot reach reconstruct/query_scenario even with a later candidate permit; its passing toys do not exercise this source join.",
            "fix": "Preserve issued v1 bytes; use a separately pinned adapter that compares canonical JSON/schema-normalized inventory values before candidate queries.",
            "evidence": {"source_only_failure": "analytic source inventory differs", "raw_members_equal": False, "canonical_members_equal": True, "proposed_axes_equal": True, "native_modules_loaded": 0},
            "parent_already_identified": True,
        }],
        "boundary_assessment": {
            "whole_CAD_module_imports": False,
            "source_inventory_reuses_existing_pure_helper": True,
            "native_functions_loaded_by_authenticated_AST": True,
            "serial_nonblocking_lock_before_output_and_native_entry": True,
            "fresh_owned_output_and_exclusive_result": True,
            "four_hosts_12_axes_16_occurrences_only": True,
            "method_toys_are_not_candidate_or_mechanics_acceptance": True,
            "geometry_adoption_and_physical_release": False,
            "failed_or_historical_outputs_removed_or_replaced": False,
        },
        "standard_library_checks": {"actual_fixture_preflight": "pass with metadata mocked to pinned versions", "candidate_mode": "denied by unchanged false flag", "inventory_schema_join": "confirmed P2 without native imports", "inert_main": mock_checks},
        "ruff": {"command": ".venv/bin/ruff check " + str(OWN.relative_to(ROOT)), "exit_code": ruff.returncode, "output": ruff.stdout.strip()},
        "limits": ["Source-only architecture review; native toy result was read/hash-bound, not rerun.", "No CAD/BREP/FEA/frame/browser/candidate query executed; source BREP files were hashed only.", "Metadata was mocked for source preflight; this is not independent runtime qualification.", "No geometry/model/shop/source edits, new force inputs, capacity/admission or release; all old packets remain active.", "Existing complete source closures and numerical operators were not independently re-audited."],
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true", help="Exclusively create this review's receipt.json")
    args = parser.parse_args()
    receipt = review()
    output = OWN.with_name("receipt.json")
    if args.write:
        with output.open("x") as stream:
            stream.write(json.dumps(receipt, sort_keys=True, indent=2, allow_nan=False) + "\n")
        print(json.dumps({"path": str(output.relative_to(ROOT)), "sha256": sha(output), "findings": len(receipt["findings"])}))
    else:
        print(json.dumps(receipt, sort_keys=True, indent=2, allow_nan=False))


if __name__ == "__main__":
    main()
