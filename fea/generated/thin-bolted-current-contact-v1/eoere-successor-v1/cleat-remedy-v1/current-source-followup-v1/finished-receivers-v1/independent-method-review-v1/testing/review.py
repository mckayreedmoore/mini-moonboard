"""Bounded frozen-v1 testing review; no native imports or geometry execution."""
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
from types import SimpleNamespace
from unittest.mock import patch

sys.dont_write_bytecode = True
OWN = Path(__file__).resolve()
OUT = OWN.parent
PACKET = OUT.parent.parent
ROOT = next(p for p in OWN.parents if (p / "AGENTS.md").is_file())
EXPECTED = {
    "query.py": "b9a888032c19a7616619bb27355aa2aeb5a0ade862aa748ad08d80ababd0ebfb",
    "inputs.json": "1480f590f0b870a86acf489b780d4eb34c4ef7760a8dc88bc0c70c58b311bf24",
    "parent-method-readiness-v1.json": "4c32ef7dd354049921f88511dbba969775701379634c9b8764030d7cc3208e09",
    "runs-v1/method01/result.json": "f833ad8f03a3cedaab27c9af4c91a0584a808cfce183958b75d3536499c7750a",
}


def sha(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def require(ok, message):
    if not ok:
        raise AssertionError(message)


def rejected(call, text=None):
    try:
        call()
    except (ValueError, KeyError, FileNotFoundError, FileExistsError, BlockingIOError) as exc:
        require(text is None or text in str(exc), "unexpected rejection: " + str(exc))
        return str(exc)
    raise AssertionError("expected rejection")


def nested_change(value, path, replacement):
    target = value
    for key in path[:-1]:
        target = target[key]
    target[path[-1]] = replacement


class BoundaryReached(Exception):
    """Native boundary sentinel; no native function was called."""


def review():
    targets = {str((PACKET / name).relative_to(ROOT)): sha(PACKET / name) for name in EXPECTED}
    require(all(targets[str((PACKET / name).relative_to(ROOT))] == expected for name, expected in EXPECTED.items()), "frozen target mismatch")
    spec = importlib.util.spec_from_file_location("frozen_four_receiver_query_review", PACKET / "query.py")
    q = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(q)
    permit_path = PACKET / "parent-method-readiness-v1.json"
    input_path = PACKET / "inputs.json"
    toy_path = PACKET / "runs-v1/method01/result.json"
    inp, pins, permit, runtime = q.preflight(permit_path, True)
    toy = q.read(toy_path)
    require(toy["schema"] == "eoere_four_receiver_native_method_fixtures/v1" and toy["pass"] is True, "toy status")
    require(toy["fixtures"]["known_answer_or_negative_checks"] == 7 and toy["fixtures"]["candidate_BREP_imports"] == 0, "toy scope")
    require(toy["release"] == q.RELEASE and toy["runtime"] == runtime and toy["sources_unchanged_before_after"] is True, "toy boundaries")
    require(toy["query_sha256"] == sha(q.OWN) and toy["inputs_sha256"] == sha(input_path), "toy bindings")
    require(all(sha(ROOT / path) == digest for path, digest in toy["source_sha256"].items()), "toy source hashes")
    require(toy["source_sha256"] == {**pins, str(permit_path.relative_to(ROOT)): sha(permit_path)}, "exact toy pin map")

    preflight_controls = []
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

    # This virtual permit exercises the candidate gate only; it grants no real authorization.
    virtual_preflight(candidate_permit, inp, toy, False)
    preflight_controls.append({"name": "current_permit_blocks_candidate", "rejection": rejected(lambda: q.preflight(permit_path, False), "mode not authorized")})
    mutations = [
        ("permit_schema", "permit", ("schema",), "other"),
        ("fixtures_authority", "permit", ("fixtures_authorized",), False),
        ("fixture_mode_mismatch", "permit", ("candidate_query_authorized",), True),
        ("permit_release", "permit", ("release", "geometry_adopted"), True),
        ("query_hash", "permit", ("query", "sha256"), "0" * 64),
        ("query_path", "permit", ("query", "path"), "other.py"),
        ("input_hash", "permit", ("inputs", "sha256"), "0" * 64),
        ("input_path", "permit", ("inputs", "path"), "other.json"),
        ("input_schema", "input", ("schema",), "other"),
        ("current_revision", "input", ("current_revision",), "historical"),
        ("optional_grid", "input", ("optional_2026_extra",), True),
        ("input_release", "input", ("release", "capacity_established"), True),
        ("scenario_missing", "input", ("scenarios",), inp["scenarios"][:-1]),
        ("scenario_order", "input", ("scenarios",), list(reversed(inp["scenarios"]))),
        ("runtime_python", "input", ("runtime", "python"), "0.0"),
        ("runtime_cadquery", "input", ("runtime", "cadquery"), "0.0"),
        ("source_hash", "input", ("source_sha256", next(iter(inp["source_sha256"]))), "0" * 64),
        ("missing_fixtures", "candidate", ("prerequisite_results",), []),
        ("fixture_schema", "fixture", ("schema",), "other"),
        ("failed_fixtures", "fixture", ("pass",), False),
        ("fixture_query_binding", "fixture", ("query_sha256",), "0" * 64),
        ("fixture_input_binding", "fixture", ("inputs_sha256",), "0" * 64),
    ]
    for name, kind, path, replacement in mutations:
        p = copy.deepcopy(candidate_permit if kind in ("candidate", "fixture") else permit)
        i, fixture = copy.deepcopy(inp), copy.deepcopy(toy)
        nested_change({"permit": p, "candidate": p, "input": i, "fixture": fixture}[kind], path, replacement)
        reason = rejected(lambda p=p, i=i, fixture=fixture, kind=kind: virtual_preflight(p, i, fixture, kind not in ("candidate", "fixture")))
        preflight_controls.append({"name": name, "rejection": reason})
    conflict = copy.deepcopy(permit)
    conflict["prerequisite_results"] = [{"path": str(input_path.relative_to(ROOT)), "sha256": "0" * 64}]
    preflight_controls.append({"name": "conflicting_prerequisite_pin", "rejection": rejected(lambda: virtual_preflight(conflict, inp, toy, True), "conflicting")})
    with patch.dict(sys.modules, {"OCP.review_sentinel": object()}):
        preflight_controls.append({"name": "loaded_native_module", "rejection": rejected(lambda: q.preflight(permit_path, True), "fresh pre-native")})

    inventory_failure = rejected(lambda: q.source_inventory(inp), "analytic source inventory differs")
    analytic = q.module(inp["helpers"]["analytic_inventory"], "review_frozen_analytic_inventory")
    bound_input = q.read(ROOT / inp["analytic_inputs"]["path"])
    data = {key: q.read(ROOT / ref["path"]) for key, ref in bound_input["sources"].items() if ref["path"].endswith(".json")}
    datum = q.module(bound_input["sources"]["datum_helper"], "review_frozen_datums")
    axes, proposed, members, cuts = analytic.existing_inventory(bound_input, data, datum)
    prior = q.read(ROOT / inp["analytic_result"]["path"])
    require(members != prior["affected_members"] and q.canonical(members) == q.canonical(prior["affected_members"]), "typed inventory reproduction")
    require(list(proposed.values()) == prior["proposed_axes"], "proposal records differ")
    tuple_vertices = sum(isinstance(vertex, tuple) for member in members.values() for vertex in member["YZ_polygon_mm"])
    require(tuple_vertices == 16, "four quadrilateral polygon tuple vertices")

    inventory_controls = []
    inventory_mutations = [
        ("axis_census", ("geometry", "axes"), data["geometry"]["axes"][:-1]),
        ("screw_census", ("geometry", "screw_axes"), data["geometry"]["screw_axes"][:-1]),
        ("placement_adoption", ("placement", "geometry_adopted"), True),
        ("placement_revision", ("placement", "base_revision"), "historical"),
        ("current_v3_axis", ("base", "axes", 0, "grip_mm"), -1),
        ("cache_axis_identity", ("cache", "shafts", 0, "source_axis", "grip_mm"), -1),
        ("proposal_extra_change", ("placement", "proposed_axes", 0, "grip_mm"), -1),
        ("existing_wall_length", ("cache", "finished_receiver_wall_queries", 0, "full_wall_length_mm"), -1),
    ]
    # Pick a wall on an affected host instead of relying on global report ordering.
    own_wall_index = next(i for i, row in enumerate(data["cache"]["finished_receiver_wall_queries"]) if row["receiver"] in members)
    inventory_mutations[-1] = ("existing_wall_length", ("cache", "finished_receiver_wall_queries", own_wall_index, "full_wall_length_mm"), -1)
    for name, path, replacement in inventory_mutations:
        changed = copy.deepcopy(data)
        nested_change(changed, path, replacement)
        inventory_controls.append({"name": name, "rejection": rejected(lambda changed=changed: analytic.existing_inventory(bound_input, changed, datum))})
    changed = copy.deepcopy(data)
    changed["bottom"]["service_cuts"].append({"receiver": next(iter(members))})
    inventory_controls.append({"name": "affected_service_cut", "rejection": rejected(lambda: analytic.existing_inventory(bound_input, changed, datum), "service cut")})

    # Test the downstream scope guard in isolation after JSON-normalizing the join.
    original_module = q.module
    normalized_members = json.loads(json.dumps(members))
    stub_analytic = SimpleNamespace(existing_inventory=lambda *_: (axes, proposed, normalized_members, cuts))
    with patch.object(q, "module", side_effect=lambda ref, name: stub_analytic if ref == inp["helpers"]["analytic_inventory"] else original_module(ref, name)):
        q.source_inventory(inp)
        for key in ("receivers", "axis_ids"):
            changed = copy.deepcopy(inp)
            changed[key] = changed[key][:-1]
            inventory_controls.append({"name": "query_exact_" + key, "rejection": rejected(lambda changed=changed: q.source_inventory(changed), "exact four-host/axis")})

    geometry_before = q.canonical(data["geometry"])
    tiny = SimpleNamespace(cq=SimpleNamespace(Vector=lambda *xyz: tuple(xyz)))
    scenario_checks = []
    for scenario in inp["scenarios"]:
        selected = q.local_axes(data["geometry"], proposed, members, tiny, scenario=scenario)
        plain = [{key: value for key, value in row.items() if key not in ("point", "direction")} for row in selected]
        expected = []
        for row in data["geometry"]["axes"]:
            hosts = [name for name in row["receivers"] if name in members]
            if not hosts:
                continue
            row = copy.deepcopy(row if scenario == "current_Z200_modeled" else proposed.get(row["id"], row))
            row["receivers"] = hosts
            if scenario == "proposed_Z180_all11p1125":
                row["bore_diameter_mm"] = 11.1125
            expected.append(row)
        require(plain == expected and len(plain) == 12 and sum(len(row["receivers"]) for row in plain) == 16, "scenario mapping")
        require(all(sum(name in row["receivers"] for row in plain) == 4 for name in members), "four own holes per host")
        require(all(row["point_xyz_mm"][2] == (200 if scenario == "current_Z200_modeled" else 180) for row in plain if row["id"] in proposed), "target Z mapping")
        scenario_checks.append({"scenario": scenario, "axes": len(plain), "receiver_occurrences": 16, "canonical_sha256": q.canonical(plain)})
    require(q.canonical(data["geometry"]) == geometry_before, "scenario mutated source")
    changed = copy.deepcopy(data["geometry"])
    changed["axes"] = [row for row in changed["axes"] if row["id"] != next(iter(proposed))]
    inventory_controls.append({"name": "local_axis_census", "rejection": rejected(lambda: q.local_axes(changed, proposed, members, tiny, scenario=inp["scenarios"][0]), "census")})

    output_controls = []
    with tempfile.TemporaryDirectory(prefix="review-scratch-", dir=OUT) as directory:
        scratch = Path(directory)
        (scratch / "runs-v1").mkdir()
        lock_path = scratch / "review.lock"
        open_original = Path.open

        def redirect_lock(path, *args, **kwargs):
            return open_original(lock_path if str(path) == "/tmp/moonboard-four-receiver-native-geometry.lock" else path, *args, **kwargs)

        def run_cli(path, *, stale=False):
            calls = []

            def stop(_):
                calls.append("methods_boundary")
                raise BoundaryReached

            def verify(_):
                if stale:
                    raise ValueError("mock source changed immediately before native load")

            with patch.object(q, "HERE", scratch), patch.object(q, "preflight", return_value=({}, {}, {}, {})), patch.object(q, "verify", side_effect=verify), patch.object(q, "methods", side_effect=stop), patch.object(Path, "open", redirect_lock), patch.object(sys, "argv", [str(q.OWN), "--permit", str(permit_path), "--outdir", str(path), "--fixtures-only"]):
                try:
                    q.main()
                except (BoundaryReached, ValueError, FileExistsError, BlockingIOError) as exc:
                    return type(exc).__name__, str(exc), calls
            raise AssertionError("CLI unexpectedly returned")

        fresh = scratch / "runs-v1" / "fresh"
        outcome = run_cli(fresh)
        require(outcome[0] == "BoundaryReached" and fresh.is_dir(), "fresh reservation path")
        output_controls.append({"name": "fresh_reservation_before_mock_boundary", "outcome": outcome[0]})
        existing_file = scratch / "runs-v1" / "existing-file"
        existing_file.write_bytes(b"preserve")
        for name, path in (("existing_directory", fresh), ("existing_file", existing_file), ("outside", scratch / "outside")):
            outcome = run_cli(path)
            require(outcome[0] == "ValueError" and outcome[2] == [], "output guard reached native boundary")
            output_controls.append({"name": name, "outcome": outcome[0]})
        require(existing_file.read_bytes() == b"preserve", "existing file overwritten")
        outcome = run_cli(scratch / "runs-v1" / "stale", stale=True)
        require(outcome[0] == "ValueError" and outcome[2] == [], "stale source reached native")
        output_controls.append({"name": "source_changed_before_methods", "outcome": outcome[0]})
        with lock_path.open("a+") as held:
            fcntl.flock(held, fcntl.LOCK_EX | fcntl.LOCK_NB)
            contended = scratch / "runs-v1" / "contended"
            outcome = run_cli(contended)
            require(outcome[0] == "BlockingIOError" and outcome[2] == [] and not contended.exists(), "exclusive lock guard")
        output_controls.append({"name": "concurrent_lock_contention", "outcome": outcome[0]})
        target = scratch / "runs-v1" / "absent-target"
        occupied = scratch / "runs-v1" / "occupied-symlink"
        occupied.symlink_to(target)
        outcome = run_cli(occupied)
        require(outcome[0] == "BoundaryReached" and target.is_dir() and occupied.is_symlink(), "dangling-symlink finding no longer reproduced")
        output_controls.append({"name": "occupied_dangling_symlink_accepted", "outcome": outcome[0], "resolved_target_created": True})
        result_path = scratch / "existing-result.json"
        result_path.write_bytes(b"frozen")
        rejected(lambda: q.write(result_path, {"replacement": True}))
        require(result_path.read_bytes() == b"frozen", "exclusive result write")
        output_controls.append({"name": "exclusive_result_write", "outcome": "FileExistsError"})
        nonfinite = scratch / "nonfinite.json"
        nonfinite.write_text('{"x": NaN}\n')
        rejected(lambda: q.read(nonfinite), "nonfinite JSON")
        preflight_controls.append({"name": "nonfinite_json", "rejection": "nonfinite JSON: NaN"})

    require(all(sha(ROOT / path) == digest for path, digest in targets.items()), "targets changed during review")
    require(all(sha(ROOT / path) == digest for path, digest in toy["source_sha256"].items()), "source changed during review")
    return {
        "schema": "eoere_finished_receivers_frozen_v1_independent_testing_review/v1",
        "review_helper": {"path": str(OWN.relative_to(ROOT)), "sha256": sha(OWN)},
        "targets_sha256": targets,
        "authenticated_reused_toy_source_pins": len(toy["source_sha256"]),
        "input_source_pins": len(inp["source_sha256"]),
        "preflight_controls": preflight_controls,
        "source_inventory_controls": inventory_controls,
        "scenario_checks": scenario_checks,
        "output_controls": output_controls,
        "findings": [
            {"severity": "medium", "file": str(q.OWN.relative_to(ROOT)), "line": 168,
             "problem": "Exact current source inventory rejects its own frozen JSON observation: 16 in-memory YZ polygon vertices are tuples and the saved vertices are lists.",
             "evidence": {"actual_error": inventory_failure, "members_direct_equal": False, "members_canonical_equal": True, "proposed_axes_direct_equal": True, "tuple_polygon_vertices": tuple_vertices},
             "impact": "The candidate path cannot proceed past source_inventory on unchanged inputs; passing native toys do not cover this source-only join.",
             "fix": "Normalize the typed inventory to canonical JSON data before equality, preserving full member/proposal and exact four-host/axis guards; retain this as a source-only regression check."},
            {"severity": "medium", "file": str(q.OWN.relative_to(ROOT)), "line": 293,
             "problem": "Resolving the requested output before its occupied-entry test accepts a dangling symlink pointing to an absent owned run directory.",
             "evidence": "Mock CLI preserved the occupied symlink, created its resolved target and reached methods(); no native function was called.",
             "impact": "The claimed fresh output entry guard permits an already occupied requested path and follows its alias into work.",
             "fix": "Reject any pre-existing requested entry with lstat/lexists, including dangling links; reserve the exact permitted directory without following its final component, retaining exclusive locking and mkdir."},
        ],
        "sources_unchanged_before_after": True,
        "candidate_query_authorized": False,
        "release": q.RELEASE,
        "scope": "Source/metadata hashes, stdlib source inventory, tiny tuple-vector scenario mapping, in-memory preflight mutations, CLI sentinels with reviewer-local lock/output only. Saved seven native toy observations authenticated and reused, not executed.",
        "excluded": ["native imports", "candidate BREP import/query/reconstruction", "native toy rerun", "FEA/frame/global solve", "mechanics/admission/reducer audit", "model/shared evidence edits", "V2 review"],
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
    require(not native_attempts, "native import attempted")
    receipt["native_import_attempts"] = native_attempts
    path = OUT / "receipt.json"
    with path.open("xb") as stream:
        stream.write((json.dumps(receipt, sort_keys=True, indent=2, allow_nan=False) + "\n").encode())
    print(json.dumps({"receipt": str(path.relative_to(ROOT)), "sha256": sha(path), "findings": len(receipt["findings"])}))
