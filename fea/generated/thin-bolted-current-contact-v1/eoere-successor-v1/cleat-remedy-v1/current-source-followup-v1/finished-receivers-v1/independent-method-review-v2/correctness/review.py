"""Frozen v2 adapter review: stdlib intake, guards and synthetic axis views only."""
from __future__ import annotations

import ast
import copy
import hashlib
import importlib.util
import json
import sys
import tempfile
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

OWN = Path(__file__).resolve()
ROOT = next(p for p in OWN.parents if (p / "AGENTS.md").is_file())
PACKET = OWN.parents[2]
EXPECTED = {
    "query-v2.py": "88edea7a233963e32f6d56fc7fd0dd86322acc65f69bbefdd4f53cc01d919912",
    "query.py": "b9a888032c19a7616619bb27355aa2aeb5a0ade862aa748ad08d80ababd0ebfb",
    "inputs.json": "1480f590f0b870a86acf489b780d4eb34c4ef7760a8dc88bc0c70c58b311bf24",
    "parent-method-readiness-v2.json": "b1d4e988f0af656f5d9b967af31a62e019e84625cdd4a4e70f5d27810efffe5a",
    "runs-v1/method02/result.json": "e054fbd0fd9015f31a17c0c3887937e00a3793c2f40795c53e9ea535db50e2e7",
}


def require(ok, message):
    if not ok:
        raise ValueError(message)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def load(path):
    spec = importlib.util.spec_from_file_location("independent_frozen_v2_adapter", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def reject(call, expected):
    try:
        call()
    except ValueError as error:
        require(expected in str(error), "unexpected rejection: " + str(error))
        return str(error)
    raise ValueError("negative control accepted: " + expected)


class StoppedBeforeNative(RuntimeError):
    pass


def main():
    target = {str((PACKET/p).relative_to(ROOT)): h for p, h in EXPECTED.items()}
    require(all(sha(ROOT/p) == h for p, h in target.items()), "target changed before review")
    wrapper = load(PACKET/"query-v2.py")
    query = wrapper.load_adapter()
    permit_path = PACKET/"parent-method-readiness-v2.json"
    inp, preflight_pins, permit, runtime = query.preflight(permit_path, True)
    pins = {**inp["source_sha256"], **target}
    query.verify(pins)
    legacy_path = str((PACKET/"query.py").relative_to(ROOT))
    require(query.OWN == PACKET/"query-v2.py" and query.HERE == PACKET
            and preflight_pins[legacy_path] == EXPECTED["query.py"]
            and len(preflight_pins) == 41, "wrapper/original source union differs")
    fixture = query.read(PACKET/"runs-v1/method02/result.json")
    expected_fixture_pins = {**preflight_pins, str(permit_path.relative_to(ROOT)): sha(permit_path)}
    require(fixture["source_sha256"] == expected_fixture_pins and len(expected_fixture_pins) == 42,
            "fixture does not bind exact original/wrapper/input/permit union")
    require(fixture["query_sha256"] == EXPECTED["query-v2.py"]
            and fixture["inputs_sha256"] == EXPECTED["inputs.json"] and fixture["runtime"] == runtime
            and fixture["parent_readiness"] == {"path": str(permit_path.relative_to(ROOT)), "sha256": sha(permit_path)}
            and fixture["pass"] is True and fixture["fixtures"]["known_answer_or_negative_checks"] == 7
            and fixture["fixtures"]["candidate_BREP_imports"] == 0
            and fixture["release"] == permit["release"] == inp["release"] == query.RELEASE,
            "native toy receipt binding/scope differs")
    controls = {"unissued_candidate_mode": reject(lambda: query.preflight(permit_path, False),
                                                   "mode not authorized by parent")}
    geometry, axes, proposed, members, cuts = query.source_inventory(inp)
    require((len(axes), len(geometry["screw_axes"]), len(proposed), len(members), sum(map(len, cuts.values())))
            == (100, 66, 4, 4, 16), "canonical intake census differs")
    intake_before = query.canonical([geometry, axes, proposed, members, cuts])
    original_read = query.read
    prior_path = ROOT/inp["analytic_result"]["path"]
    bound = original_read(ROOT/inp["analytic_inputs"]["path"])

    def corrupted_read(path, changed_path, mutate):
        value = original_read(path)
        if Path(path) == changed_path:
            value = copy.deepcopy(value)
            mutate(value)
        return value

    mutations = [
        ("changed_saved_member", prior_path,
         lambda v: v["affected_members"]["eoere_cleat_left"].__setitem__("raw_volume_mm3", 1.),
         "analytic canonical source inventory differs"),
        ("changed_saved_proposal", prior_path,
         lambda v: v["proposed_axes"][0]["point_xyz_mm"].__setitem__(2, 181.),
         "analytic canonical source inventory differs"),
        ("moved_retained_current_axis", ROOT/bound["sources"]["geometry"]["path"],
         lambda v: v["axes"][0]["point_xyz_mm"].__setitem__(0, v["axes"][0]["point_xyz_mm"][0]+1.),
         "unchanged current v3 axes required"),
        ("moved_current_screw", ROOT/bound["sources"]["geometry"]["path"],
         lambda v: v["screw_axes"][0]["origin_xyz_mm"].__setitem__(0, v["screw_axes"][0]["origin_xyz_mm"][0]+1.),
         "unchanged current v3 axes required"),
    ]
    for name, changed_path, mutate, expected in mutations:
        with patch.object(query, "read", side_effect=lambda p, cp=changed_path, f=mutate: corrupted_read(p, cp, f)):
            controls[name] = reject(lambda: query.source_inventory(inp), expected)
    for field in ("receivers", "axis_ids"):
        changed = copy.deepcopy(inp)
        changed[field].pop()
        controls["changed_"+field+"_scope"] = reject(lambda c=changed: query.source_inventory(c),
                                                     "exact four-host/axis scope required")
    # Synthetic permit/read substitutions are negative gate controls only;
    # no new permit file or native method invocation is created.
    for name, mutate, expected in (
        ("old_fixture_cannot_authorize_v2", lambda v: v.__setitem__("query_sha256", EXPECTED["query.py"]),
         "fixture source binding differs"),
        ("nonpassing_fixture_rejected", lambda v: v.__setitem__("pass", False),
         "passing exact method fixtures required"),
    ):
        fake_permit = copy.deepcopy(permit)
        fake_permit["candidate_query_authorized"] = True
        fake_permit["prerequisite_results"] = [{"path": str((PACKET/"runs-v1/method02/result.json").relative_to(ROOT)),
                                                  "sha256": EXPECTED["runs-v1/method02/result.json"]}]
        fake_fixture = copy.deepcopy(fixture)
        mutate(fake_fixture)

        def fake_read(path, permit_value=fake_permit, fixture_value=fake_fixture):
            if Path(path) == permit_path:
                return permit_value
            if Path(path) == PACKET/"runs-v1/method02/result.json":
                return fixture_value
            return original_read(path)

        with patch.object(query, "read", side_effect=fake_read):
            controls[name] = reject(lambda: query.preflight(permit_path, False), expected)

    scenarios = []
    stub = SimpleNamespace(cq=SimpleNamespace(Vector=lambda *values: tuple(values)))
    for scenario in inp["scenarios"]:
        selected = query.local_axes(geometry, proposed, members, stub, scenario=scenario)
        changes = []
        require(len(selected) == 12 and sum(len(a["receivers"]) for a in selected) == 16,
                "local view census differs")
        for axis in selected:
            expected = copy.deepcopy(axes[axis["id"]])
            expected["receivers"] = [n for n in expected["receivers"] if n in members]
            if axis["id"] in proposed and scenario != "current_Z200_modeled":
                expected["point_xyz_mm"][2] = 180.
                changes.append(axis["id"])
            if scenario == "proposed_Z180_all11p1125":
                expected["bore_diameter_mm"] = 11.1125
            require({k: v for k, v in axis.items() if k not in ("point", "direction")} == expected,
                    "unexpected local view mutation")
            require(axis["point"] == tuple(axis["point_xyz_mm"])
                    and axis["direction"] == tuple(axis["direction_xyz"]), "vector construction differs")
        require(len(changes) == (0 if scenario == "current_Z200_modeled" else 4), "exact four substitutions differ")
        scenarios.append({"scenario": scenario, "axes": 12, "receiver_occurrences": 16,
                          "translated_axis_ids": sorted(changes)})
    require(query.canonical([geometry, axes, proposed, members, cuts]) == intake_before,
            "source intake or local view mutated original inputs")

    output_controls = {}
    with tempfile.TemporaryDirectory(prefix=".source-controls-", dir=OWN.parent) as temp:
        folder = Path(temp)
        existing_dir = folder/"existing-dir"
        existing_dir.mkdir()
        existing_file = folder/"existing-file"
        existing_file.write_text("synthetic guard fixture\n")
        dangling = folder/"dangling"
        dangling.symlink_to(folder/"absent-target")
        live_link = folder/"live-link"
        live_link.symlink_to(existing_dir, target_is_directory=True)
        for name, path, expected in (
            ("existing_directory", existing_dir, "requested output entry already exists"),
            ("existing_file", existing_file, "requested output entry already exists"),
            ("dangling_symlink", dangling, "requested output entry already exists"),
            ("live_symlink", live_link, "requested output entry already exists"),
            ("parent_traversal", folder/"child"/".."/"fresh", "parent traversal output rejected"),
        ):
            argv = [str(PACKET/"query-v2.py"), "--permit", str(permit_path), "--outdir", str(path), "--fixtures-only"]
            with patch.object(sys, "argv", argv), patch.object(query, "preflight", side_effect=StoppedBeforeNative) as gate:
                output_controls[name] = reject(query.main, expected)
                require(gate.call_count == 0, "guard failed to precede original preflight")
        fresh = folder/"fresh-unused"
        argv = [str(PACKET/"query-v2.py"), "--permit", str(permit_path), "--outdir", str(fresh), "--fixtures-only"]
        with patch.object(sys, "argv", argv), patch.object(query, "preflight", side_effect=StoppedBeforeNative) as gate:
            try:
                query.main()
            except StoppedBeforeNative:
                require(gate.call_count == 1 and not fresh.exists(), "fresh output guard did not defer exactly once")
            else:
                raise ValueError("synthetic main unexpectedly passed native stop")
        output_controls["fresh_entry_defers_to_original_preflight"] = True
    require(not folder.exists(), "temporary synthetic guard entries retained")
    native_names = ("methods", "method_fixtures", "reconstruct", "local_axes", "query_scenario", "bounds", "close_bounds")
    for name in native_names:
        require(getattr(query, name).__code__.co_filename == str(PACKET/"query.py"), "frozen method replaced: "+name)
    tree = ast.parse((PACKET/"query-v2.py").read_bytes())
    require(not any(isinstance(n, (ast.Import, ast.ImportFrom)) and
                    (getattr(n, "module", "") or "").startswith(("cadquery", "OCP")) for n in ast.walk(tree)),
            "wrapper adds native initializer")
    require(not any(n == "cadquery" or n == "OCP" or n.startswith("OCP.") for n in sys.modules),
            "native module imported by source review")
    query.verify(pins)
    receipt = {
        "schema": "eoere_four_finished_receiver_v2_independent_correctness_method_review/v1",
        "status": "NO_SUBSTANTIAL_FINDINGS_WITHIN_SOURCE_ONLY_METHOD_SCOPE", "findings": [],
        "target_sha256": target, "review_helper_sha256": sha(OWN),
        "source_files_rehashed_before_after": len(pins), "sources_unchanged_before_after": True,
        "checks": {"canonical_source_inventory_passes": {"axes": 100, "screws": 66, "proposed_axes": 4,
                    "hosts": 4, "own_cut_occurrences": 16}, "source_union_preflight_pins": 41,
                   "native_toy_receipt_pins": 42, "negative_source_and_gate_controls": controls,
                   "arithmetic_mock_scenario_views": scenarios, "output_entry_controls": output_controls,
                   "unchanged_original_native_facing_methods": list(native_names),
                   "current_sources_not_mutated": True},
        "reviewed_scope": [
            "Canonical member/proposal join fixes v1 tuple/list failure and still rejects changed member values, changed proposals, current-axis/screw moves and host/axis scope changes.",
            "Private module composition retains original HERE/ROOT and native-facing function code, changes OWN to the separately frozen wrapper, and rehashes the original adapter in the preflight/source union.",
            "Exact three local scenario views preserve current100 axes/current66 screws and apply exactly four Z200-to-Z180 substitutions with twelve axes/sixteen own receiver occurrences; all11p1125 modifies the local hole scenario only.",
            "Early requested-output checks reject existing files/directories, live/dangling symlinks and explicit parent traversal; a fresh entry defers once to the frozen original main/preflight. Original locked exclusive mkdir remains in force.",
            "Fixture-only parent permit, wrapper/original/input/permit-bound seven-toy receipt, rejection of candidate mode and wrong/nonpassing fixture mocks, unchanged false release/adoption boundaries.",
        ],
        "limits": [
            "Source-only correctness review and stdlib/synthetic controls. No CAD/OCP import, actual BREP import/query/reconstruction, native toy rerun, candidate geometry run, frame/global/native solve or physical work.",
            "Authenticated seven native toy checks are reused supporting evidence. No actual current or proposed finished receiver has been independently queried by this review.",
            "Existing v1 review remains frozen. Native method formulas, current Boolean-volume limitation, export/reimport and nominal one-host geometry boundaries retain that prior source-review scope; this v2 review concentrates on fix composition and guards.",
            "No geometry adoption, new force assignment, load/capacity transfer, physical contact/fit qualification, fabrication or climbing release. Candidate query authorization remains false in the issued permit.",
        ],
    }
    out = OWN.with_name("receipt.json")
    with out.open("x") as stream:
        json.dump(receipt, stream, sort_keys=True, indent=2, allow_nan=False)
        stream.write("\n")
    query.verify(pins)
    print(json.dumps({"receipt": str(out.relative_to(ROOT)), "sha256": sha(out), "helper_sha256": sha(OWN),
                      "source_files": len(pins), "findings": 0}, sort_keys=True))


if __name__ == "__main__":
    main()
