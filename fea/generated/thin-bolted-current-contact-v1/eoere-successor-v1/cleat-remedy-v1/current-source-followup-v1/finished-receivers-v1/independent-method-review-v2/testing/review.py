"""Bounded v2 testing review, reusing frozen v1 review utilities; no native work."""
from __future__ import annotations

import builtins
import copy
import fcntl
import hashlib
import importlib.util
import json
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

sys.dont_write_bytecode = True
OWN = Path(__file__).resolve()
OUT = OWN.parent
PACKET = OUT.parent.parent
ROOT = next(p for p in OWN.parents if (p / "AGENTS.md").is_file())
V1 = PACKET / "independent-method-review-v1/testing"
EXPECTED = {
    "query.py": "b9a888032c19a7616619bb27355aa2aeb5a0ade862aa748ad08d80ababd0ebfb",
    "query-v2.py": "88edea7a233963e32f6d56fc7fd0dd86322acc65f69bbefdd4f53cc01d919912",
    "inputs.json": "1480f590f0b870a86acf489b780d4eb34c4ef7760a8dc88bc0c70c58b311bf24",
    "parent-method-readiness-v2.json": "b1d4e988f0af656f5d9b967af31a62e019e84625cdd4a4e70f5d27810efffe5a",
    "runs-v1/method02/result.json": "e054fbd0fd9015f31a17c0c3887937e00a3793c2f40795c53e9ea535db50e2e7",
    "independent-method-review-v1/testing/review.py": "101650723fa1747406c5379df27fff198e2dadfc7c37f8454c9eb611de9ff284",
    "independent-method-review-v1/testing/receipt.json": "140ae567f99ca0fc4c4b21fc0a49d7a53a378a6be9bdb373ad9e44cca983896f",
}


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def review():
    helpers = load(V1 / "review.py", "frozen_v1_testing_utilities")
    sha, require, rejected = helpers.sha, helpers.require, helpers.rejected
    targets = {str((PACKET / name).relative_to(ROOT)): sha(PACKET / name) for name in EXPECTED}
    require(all(sha(PACKET / name) == digest for name, digest in EXPECTED.items()), "frozen v2/reused v1 mismatch")
    wrapper = load(PACKET / "query-v2.py", "frozen_v2_geometry_wrapper")
    q = wrapper.load_adapter()
    require(q.OWN == wrapper.OWN and q.OWN.name == "query-v2.py", "adapter source identity")
    permit_path = PACKET / "parent-method-readiness-v2.json"
    input_path = PACKET / "inputs.json"
    toy_path = PACKET / "runs-v1/method02/result.json"
    inp, pins, permit, runtime = q.preflight(permit_path, True)
    toy = q.read(toy_path)
    require(toy["pass"] is True and toy["schema"] == "eoere_four_receiver_native_method_fixtures/v1", "toy schema/status")
    require(toy["fixtures"]["known_answer_or_negative_checks"] == 7 and toy["fixtures"]["candidate_BREP_imports"] == 0, "toy scope")
    require(toy["release"] == q.RELEASE and toy["runtime"] == runtime and toy["sources_unchanged_before_after"] is True, "toy boundaries")
    require(toy["query_sha256"] == sha(q.OWN) and toy["inputs_sha256"] == sha(input_path), "toy source bindings")
    require(toy["source_sha256"] == {**pins, str(permit_path.relative_to(ROOT)): sha(permit_path)}, "exact 42-pin toy map")
    require(len(pins) == 41 and len(toy["source_sha256"]) == 42 and all(sha(ROOT / path) == digest for path, digest in toy["source_sha256"].items()), "toy source verification")

    original_read = q.read
    candidate_permit = copy.deepcopy(permit)
    candidate_permit["candidate_query_authorized"] = True
    candidate_permit["prerequisite_results"] = [{"path": str(toy_path.relative_to(ROOT)), "sha256": sha(toy_path)}]

    def virtual_preflight(p, i, fixture, fixtures_only):
        def read(path):
            path = Path(path)
            if path == permit_path:
                return copy.deepcopy(p)
            if path == input_path:
                return copy.deepcopy(i)
            if path == toy_path:
                return copy.deepcopy(fixture)
            return original_read(path)
        with patch.object(q, "read", side_effect=read):
            return q.preflight(permit_path, fixtures_only)

    # Gate-only virtual authority; the actual frozen candidate flag remains false.
    virtual_preflight(candidate_permit, inp, toy, False)
    preflight_controls = [{"name": "frozen_candidate_flag_blocks", "rejection": rejected(lambda: q.preflight(permit_path, False), "mode not authorized")}]
    mutations = [
        ("v1_readiness_cannot_authorize_v2", "permit", ("query",), q.read(PACKET / "parent-method-readiness-v1.json")["query"]),
        ("wrapper_hash", "permit", ("query", "sha256"), "0" * 64),
        ("input_hash", "permit", ("inputs", "sha256"), "0" * 64),
        ("readiness_schema", "permit", ("schema",), "other"),
        ("fixture_authority", "permit", ("fixtures_authorized",), False),
        ("release", "permit", ("release", "fabrication_released"), True),
        ("current_revision", "input", ("current_revision",), "historical"),
        ("extra_grid", "input", ("optional_2026_extra",), True),
        ("scenario_census", "input", ("scenarios",), inp["scenarios"][:-1]),
        ("native_runtime", "input", ("runtime", "cadquery-ocp"), "0.0"),
        ("current_source_hash", "input", ("source_sha256", next(iter(inp["source_sha256"]))), "0" * 64),
        ("missing_fixture_proof", "candidate", ("prerequisite_results",), []),
        ("failed_fixture_proof", "fixture", ("pass",), False),
        ("fixture_schema", "fixture", ("schema",), "other"),
        ("v1_fixture_cannot_authorize_v2", "fixture", ("query_sha256",), wrapper.LEGACY_SHA),
        ("fixture_input_binding", "fixture", ("inputs_sha256",), "0" * 64),
    ]
    for name, kind, path, replacement in mutations:
        p = copy.deepcopy(candidate_permit if kind in ("candidate", "fixture") else permit)
        i, fixture = copy.deepcopy(inp), copy.deepcopy(toy)
        helpers.nested_change({"permit": p, "candidate": p, "input": i, "fixture": fixture}[kind], path, replacement)
        reason = rejected(lambda p=p, i=i, fixture=fixture, kind=kind: virtual_preflight(p, i, fixture, kind not in ("candidate", "fixture")))
        preflight_controls.append({"name": name, "rejection": reason})
    original_bytes = Path.read_bytes
    with patch.object(Path, "read_bytes", lambda path: b"altered legacy" if path == wrapper.LEGACY else original_bytes(path)):
        preflight_controls.append({"name": "legacy_tamper_before_adapter_import", "rejection": rejected(wrapper.load_adapter, "exact frozen v1")})
    with patch.dict(sys.modules, {"OCP.review_sentinel": object()}):
        preflight_controls.append({"name": "fresh_process_gate", "rejection": rejected(lambda: q.preflight(permit_path, True), "fresh pre-native")})
    conflicting_input = copy.deepcopy(inp)
    conflicting_input["source_sha256"][str(wrapper.LEGACY.relative_to(ROOT))] = "0" * 64
    preflight_controls.append({"name": "legacy_source_pin_tamper", "rejection": rejected(lambda: virtual_preflight(permit, conflicting_input, toy, True), "source changed")})

    geometry, axes, proposed, members, cuts = q.source_inventory(inp)
    prior = q.read(ROOT / inp["analytic_result"]["path"])
    require(len(geometry["axes"]) == len(axes) == 100 and len(geometry["screw_axes"]) == 66, "current 100/66 intake")
    require(set(members) == set(inp["receivers"]) and set(proposed) == set(inp["axis_ids"]) and len(members) == len(proposed) == 4, "four-host/four-proposal intake")
    require(sum(len(rows) for rows in cuts.values()) == 16, "four current own holes per receiver")
    require(q.canonical(members) == q.canonical(prior["affected_members"]) and q.canonical(list(proposed.values())) == q.canonical(prior["proposed_axes"]), "canonical join")
    member_name = next(iter(members))
    require(isinstance(members[member_name]["YZ_polygon_mm"][0], tuple) and isinstance(prior["affected_members"][member_name]["YZ_polygon_mm"][0], list), "actual tuple/list regression coverage")
    bound = q.read(ROOT / inp["analytic_inputs"]["path"])
    inventory_controls = []
    prior_mutations = [
        ("prior_member_volume", ("affected_members", member_name, "raw_volume_mm3"), -1),
        ("prior_polygon_coordinate", ("affected_members", member_name, "YZ_polygon_mm", 0, 0), -999),
        ("prior_proposed_coordinate", ("proposed_axes", 0, "point_xyz_mm", 2), 179),
        ("prior_proposed_census", ("proposed_axes",), prior["proposed_axes"][:-1]),
    ]
    for name, path, replacement in prior_mutations:
        altered = copy.deepcopy(prior)
        helpers.nested_change(altered, path, replacement)
        with patch.object(q, "read", side_effect=lambda path, altered=altered: copy.deepcopy(altered) if Path(path) == ROOT / inp["analytic_result"]["path"] else original_read(path)):
            inventory_controls.append({"name": name, "rejection": rejected(lambda: q.source_inventory(inp), "canonical source inventory differs")})
    source_mutations = [
        ("current_axis_census", "geometry", ("axes",), geometry["axes"][:-1]),
        ("current_screw_census", "geometry", ("screw_axes",), geometry["screw_axes"][:-1]),
        ("unadopted_scope", "placement", ("geometry_adopted",), True),
        ("proposal_not_only_Z", "placement", ("proposed_axes", 0, "grip_mm"), -1),
        ("profile_source_hash", "profiles", (member_name, "finished", "sha256"), "0" * 64),
    ]
    for name, source, path, replacement in source_mutations:
        source_path = ROOT / bound["sources"][source]["path"]
        altered = original_read(source_path)
        helpers.nested_change(altered, path, replacement)
        with patch.object(q, "read", side_effect=lambda path, altered=altered, source_path=source_path: copy.deepcopy(altered) if Path(path) == source_path else original_read(path)):
            inventory_controls.append({"name": name, "rejection": rejected(lambda: q.source_inventory(inp))})
    for key in ("receivers", "axis_ids"):
        altered_input = copy.deepcopy(inp)
        altered_input[key] = altered_input[key][:-1]
        inventory_controls.append({"name": "exact_query_" + key, "rejection": rejected(lambda altered_input=altered_input: q.source_inventory(altered_input), "exact four-host/axis")})

    output_controls = []
    with tempfile.TemporaryDirectory(prefix="review-scratch-", dir=OUT) as directory:
        scratch = Path(directory)
        (scratch / "runs-v1").mkdir()
        lock_path = scratch / "review.lock"
        original_open = Path.open

        def redirect_lock(path, *args, **kwargs):
            return original_open(lock_path if str(path) == "/tmp/moonboard-four-receiver-native-geometry.lock" else path, *args, **kwargs)

        def run_cli(path, *, stale=False):
            calls = []

            def preflight(*_):
                calls.append("preflight")
                return {}, {}, {}, {}

            def stop(_):
                calls.append("methods_boundary")
                raise helpers.BoundaryReached

            def verify(_):
                if stale:
                    raise ValueError("mock source changed immediately before native load")

            with patch.object(q, "HERE", scratch), patch.object(q, "preflight", side_effect=preflight), patch.object(q, "verify", side_effect=verify), patch.object(q, "methods", side_effect=stop), patch.object(Path, "open", redirect_lock), patch.object(sys, "argv", [str(q.OWN), "--permit", str(permit_path), "--outdir", str(path), "--fixtures-only"]):
                try:
                    q.main()
                except (helpers.BoundaryReached, ValueError, FileExistsError, BlockingIOError) as exc:
                    return type(exc).__name__, str(exc), calls
            raise AssertionError("CLI unexpectedly returned")

        absent_target = scratch / "runs-v1" / "absent-target"
        dangling = scratch / "runs-v1" / "occupied-dangling"
        dangling.symlink_to(absent_target)
        existing_file = scratch / "runs-v1" / "existing-file"
        existing_file.write_bytes(b"preserve file")
        existing_dir = scratch / "runs-v1" / "existing-directory"
        existing_dir.mkdir()
        (existing_dir / "sentinel").write_bytes(b"preserve directory")
        live_link = scratch / "runs-v1" / "occupied-live-link"
        live_link.symlink_to(existing_dir)
        outside_link = scratch / "outside-link"
        outside_link.symlink_to(absent_target)
        traversal = scratch / "runs-v1" / ".." / "runs-v1" / "traversal"
        for name, path in (("dangling_symlink", dangling), ("existing_file", existing_file), ("existing_directory", existing_dir), ("live_symlink", live_link), ("outside_final_symlink", outside_link), ("parent_traversal", traversal)):
            outcome = run_cli(path)
            require(outcome[0] == "ValueError" and outcome[2] == [], "raw requested entry guard ordering")
            output_controls.append({"name": name, "outcome": outcome[0], "preflight_calls": 0, "native_boundary_calls": 0})
        require(dangling.is_symlink() and not absent_target.exists() and live_link.is_symlink() and outside_link.is_symlink(), "symlink controls changed occupied entries")
        require(existing_file.read_bytes() == b"preserve file" and (existing_dir / "sentinel").read_bytes() == b"preserve directory", "existing outputs changed")
        outside = scratch / "outside"
        outcome = run_cli(outside)
        require(outcome[0] == "ValueError" and outcome[2] == ["preflight"] and not outside.exists(), "outside ownership guard")
        output_controls.append({"name": "outside_new_directory", "outcome": outcome[0], "native_boundary_calls": 0})
        fresh = scratch / "runs-v1" / "fresh"
        outcome = run_cli(fresh)
        require(outcome[0] == "BoundaryReached" and outcome[2] == ["preflight", "methods_boundary"] and fresh.is_dir(), "fresh reservation")
        output_controls.append({"name": "fresh_owned_reservation", "outcome": outcome[0]})
        outcome = run_cli(fresh)
        require(outcome[0] == "ValueError" and outcome[2] == [], "same output reuse")
        output_controls.append({"name": "reserved_output_reuse", "outcome": outcome[0], "native_boundary_calls": 0})
        with lock_path.open("a+") as held:
            fcntl.flock(held, fcntl.LOCK_EX | fcntl.LOCK_NB)
            contended = scratch / "runs-v1" / "contended"
            outcome = run_cli(contended)
            require(outcome[0] == "BlockingIOError" and outcome[2] == ["preflight"] and not contended.exists(), "exclusive lock contention")
        output_controls.append({"name": "concurrent_lock_contention", "outcome": outcome[0], "native_boundary_calls": 0})
        outcome = run_cli(scratch / "runs-v1" / "stale", stale=True)
        require(outcome[0] == "ValueError" and outcome[2] == ["preflight"], "source pin recheck before methods")
        output_controls.append({"name": "source_changed_before_methods", "outcome": outcome[0], "native_boundary_calls": 0})

    require(all(sha(ROOT / path) == digest for path, digest in targets.items()), "targets/reused review changed")
    require(all(sha(ROOT / path) == digest for path, digest in toy["source_sha256"].items()), "toy input sources changed")
    return {
        "schema": "eoere_finished_receivers_frozen_v2_independent_testing_review/v1",
        "review_helper": {"path": str(OWN.relative_to(ROOT)), "sha256": sha(OWN)},
        "targets_sha256": targets,
        "authenticated_reused_toy_source_pins": len(toy["source_sha256"]),
        "input_source_pins": len(inp["source_sha256"]),
        "preflight_controls": preflight_controls,
        "source_inventory_controls": inventory_controls,
        "output_controls": output_controls,
        "actual_stdlib_source_inventory": {"passed": True, "current_axes": len(axes), "current_screws": len(geometry["screw_axes"]), "receivers": sorted(members), "proposed_axes": sorted(proposed), "own_bore_occurrences": sum(len(rows) for rows in cuts.values()), "members_canonical_sha256": q.canonical(members), "proposed_axes_canonical_sha256": q.canonical(list(proposed.values())), "tuple_vs_list_join_exercised": True},
        "v1_findings_closed_in_v2": ["Canonical member/proposal JSON join admits exact typed inventory and rejects changed data.", "Raw requested output guard rejects occupied final symlinks and parent traversal before preflight/native loading."],
        "findings": [],
        "sources_unchanged_before_after": True,
        "candidate_query_authorized": False,
        "release": q.RELEASE,
        "scope": "Actual stdlib source intake, source/metadata hashes, virtual readiness/input/fixture mutations, mock CLI reservation/contention with reviewer-local lock and output paths only. Saved v2 seven native toy observations authenticated and reused, not executed. V1 review utilities and unchanged-method scenario coverage explicitly reused.",
        "excluded": ["native imports", "candidate BREP import/query/reconstruction", "native toy rerun", "FEA/frame/global solve", "mechanics/admission/reducer audit", "model/shared evidence edits"],
    }


if __name__ == "__main__":
    original_import = builtins.__import__
    native_attempts = []

    def no_native(name, *args, **kwargs):
        if name.split(".")[0] in ("cadquery", "OCP"):
            native_attempts.append(name)
            raise AssertionError("forbidden native import: " + name)
        return original_import(name, *args, **kwargs)

    with patch("builtins.__import__", side_effect=no_native):
        receipt = review()
    if native_attempts:
        raise AssertionError("native import attempted")
    receipt["native_import_attempts"] = native_attempts
    path = OUT / "receipt.json"
    with path.open("xb") as stream:
        stream.write((json.dumps(receipt, sort_keys=True, indent=2, allow_nan=False) + "\n").encode())
    print(json.dumps({"receipt": str(path.relative_to(ROOT)), "helper_sha256": receipt["review_helper"]["sha256"], "receipt_sha256": hashlib.sha256(path.read_bytes()).hexdigest(), "findings": len(receipt["findings"])}))
