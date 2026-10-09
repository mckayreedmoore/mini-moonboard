"""Frozen supported preview v2: source/readiness and output-evidence review."""
from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import subprocess
import sys
from pathlib import Path
from unittest.mock import patch

OWN = Path(__file__).resolve()
ROOT = next(p for p in OWN.parents if (p / "AGENTS.md").is_file())
PACKET = OWN.parents[2]
MANIFEST = PACKET/"review-target-v2.json"
MANIFEST_SHA = "f2a2548a638f152306b9279b8498ac226ba3b4589b9ebd8725b09743bf69bd37"


def require(ok, message):
    if not ok:
        raise ValueError(message)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(path):
    return json.loads(Path(path).read_bytes())


def load(path):
    spec = importlib.util.spec_from_file_location("independent_supported_z180_preview_v2", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def rejection(call, expected):
    try:
        call()
    except ValueError as error:
        require(expected in str(error), "unexpected rejection: "+str(error))
        return str(error)
    raise ValueError("mutated control accepted: "+expected)


class StopBeforeDisplay(RuntimeError):
    pass


def main():
    require(sha(MANIFEST) == MANIFEST_SHA, "frozen v2 target manifest changed")
    manifest = read(MANIFEST)
    targets = manifest["files"]
    require(len(targets) == 15, "15 frozen target pins required")
    pins = {**targets, str(MANIFEST.relative_to(ROOT)): MANIFEST_SHA}

    def verify():
        for path, digest in pins.items():
            require(sha(ROOT/path) == digest, "reviewed source changed: "+path)

    verify()
    supported = load(PACKET/"export-v2.py")
    replay = supported.verify_current()
    saved = read(PACKET/"source-verification-v2.json")
    require(replay == saved and replay["passed"] is True
            and replay["native_geometry_or_mechanics_executed"] is False,
            "source-only output verification replay differs")
    require(len(replay["source_sha256"]) == 17, "17 supported source pins required")
    for path, digest in replay["source_sha256"].items():
        require(path not in pins or pins[path] == digest, "conflicting supported source pin")
        pins[path] = digest
    for row in replay["original_outputs"].values():
        require(sha(ROOT/row["path"]) == row["sha256"]
                and (ROOT/row["path"]).stat().st_size == row["bytes"], "preserved output hash/size differs")
        pins[row["path"]] = row["sha256"]
    require((ROOT/replay["original_outputs"]["scene.json.gz"]["path"]).read_bytes()
            == (ROOT/"site/eoere-lower-cleat-z180-scene.json.gz").read_bytes(), "site asset is not exact display output")
    original_read, original_sha = supported.read, supported.sha
    guard_path, parent_path = PACKET/"parent-readiness-v2.json", PACKET/"parent-readiness.json"
    input_path, report_path = PACKET/"inputs.json", PACKET/"runs-v1/export01/export-result.json"
    native_path = ROOT/read(input_path)["native_result"]
    controls = []
    changes = [
        ("v2_reviewed_native_digest", guard_path, lambda v: v.__setitem__("reviewed_native_result_sha256", "0"*64),
         "parent review and consumed native-result digest differ"),
        ("v1_reviewed_native_digest", parent_path, lambda v: v.__setitem__("reviewed_native_result_sha256", "0"*64),
         "parent review and consumed native-result digest differ"),
        ("input_native_digest", input_path, lambda v: v["source_sha256"].__setitem__(v["native_result"], "0"*64),
         "parent review and consumed native-result digest differ"),
        ("wrong_v2_exporter", guard_path, lambda v: v.__setitem__("exporter_sha256", "0"*64),
         "source-bound v2 parent readiness required"),
        ("native_scope_expanded", guard_path, lambda v: v.__setitem__("native_mechanics_or_full_frame_CAD_authorized", True),
         "source-bound v2 parent readiness required"),
        ("adoption_scope_expanded", guard_path, lambda v: v.__setitem__("geometry_adoption_authorized_by_this_file", True),
         "source-bound v2 parent readiness required"),
        ("display_scope_revoked", guard_path, lambda v: v.__setitem__("only_four_saved_BREP_display_tessellations", False),
         "source-bound v2 parent readiness required"),
        ("wrong_pinned_original_source", guard_path,
         lambda v: v["source_sha256"].__setitem__(str((PACKET/"export.py").relative_to(ROOT)), "0"*64), "source changed"),
    ]
    for name, changed_path, mutate, message in changes:
        def synthetic_read(path, selected=changed_path, change=mutate):
            value = original_read(path)
            if Path(path) == selected:
                value = copy.deepcopy(value)
                change(value)
            return value

        with patch.object(supported, "read", side_effect=synthetic_read):
            controls.append({"control": name, "rejection": rejection(supported.guarded_original, message)})
    for name, changed_path, message in (
        ("actual_native_bytes", native_path, "parent review and consumed native-result digest differ"),
        ("actual_original_bytes", PACKET/"export.py", "original exporter changed"),
    ):
        with patch.object(supported, "sha", side_effect=lambda p, selected=changed_path: "0"*64
                          if Path(p) == selected else original_sha(p)):
            controls.append({"control": name, "rejection": rejection(supported.guarded_original, message)})
    output_controls = [
        ("response_transfer", lambda v: v.__setitem__("saved_response_transferred", True), "original display scope differs"),
        ("native_work_claim", lambda v: v.__setitem__("native_cuts_Boolean_or_mechanics", True), "original display scope differs"),
        ("release_claim", lambda v: v["release"].__setitem__("geometry_adopted", True), "original display scope differs"),
        ("wrong_output_path", lambda v: v["output"]["scene.json.gz"].__setitem__("path", "wrong"), "original output binding differs"),
        ("wrong_output_digest", lambda v: v["output"]["scene.json.gz"].__setitem__("sha256", "0"*64), "original output binding differs"),
        ("wrong_output_bytes", lambda v: v["output"]["scene.json.gz"].__setitem__("bytes", 1), "original output binding differs"),
    ]
    for name, mutate, message in output_controls:
        def synthetic_report(path, change=mutate):
            value = original_read(path)
            if Path(path) == report_path:
                value = copy.deepcopy(value)
                change(value)
            return value

        with patch.object(supported, "read", side_effect=synthetic_report):
            controls.append({"control": name, "rejection": rejection(supported.verify_current, message)})
    original = supported.guarded_original()
    values = original.prepare()
    require(values[1] == replay["source_sha256"], "supported prepare source union differs")
    require(original.main.__code__.co_filename == str(PACKET/"export.py")
            and original.OWN == PACKET/"export.py", "frozen original entrypoint composition differs")
    with patch.object(original, "prepare", return_value=values), patch.object(Path, "mkdir", side_effect=StopBeforeDisplay) as reserve:
        try:
            original.main()
        except StopBeforeDisplay:
            require(reserve.call_count == 1, "exclusive fixed output not reserved once before display")
        else:
            raise ValueError("original main bypassed synthetic pre-display stop")
    require(not any(n == "cadquery" or n == "OCP" or n.startswith("OCP.") for n in sys.modules),
            "native module imported during bounded review")

    browser_v1 = (ROOT/"scripts/check_eoere_lower_cleat_z180_browser.cjs").read_text()
    browser_v2 = (ROOT/"scripts/check_eoere_lower_cleat_z180_browser_v2.cjs").read_text()
    expected_browser = browser_v1.replace(
        "assert.equal(await page.locator('#part-visibility').isDisabled(), true);",
        "assert.notEqual(await page.locator('#part-visibility').getAttribute('disabled'), null);")
    expected_browser = expected_browser.replace("check_eoere_lower_cleat_z180_browser.cjs", "check_eoere_lower_cleat_z180_browser_v2.cjs")
    expected_browser = expected_browser.replace("eoere_lower_cleat_z180_browser_check/v1", "eoere_lower_cleat_z180_browser_check/v2")
    require(browser_v2 == expected_browser, "browser v2 exceeds bounded assertion/source-schema correction")
    index = (ROOT/"site/index.html").read_text()
    require("document.createElement('fieldset'); visibility.id = 'part-visibility'" in index
            and "visibility.disabled = Boolean(inspectedBolt);" in index, "browser attribute check not joined to actual fieldset")
    subprocess.run(["node", "--check", str(ROOT/"scripts/check_eoere_lower_cleat_z180_browser_v2.cjs")], check=True)
    verify()
    receipt = {
        "schema": "eoere_lower_cleat_z180_supported_v2_independent_correctness_review/v1",
        "status": "NO_SUBSTANTIAL_FINDINGS_WITHIN_SOURCE_AND_MOCK_SCOPE", "findings": [],
        "target_manifest": {"path": str(MANIFEST.relative_to(ROOT)), "sha256": MANIFEST_SHA},
        "target_file_count": 15, "target_sha256": targets, "review_helper_sha256": sha(OWN),
        "sources_unchanged_before_after": True, "target_and_direct_files_rehashed_before_after": len(pins),
        "checks": {"saved_source_verification_exact_replay": True, "supported_source_union_files": 17,
                   "reviewed_native_digest_actual_input_v1_and_v2_join": True, "negative_readiness_and_output_controls": controls,
                   "original_display_main_reused_with_pre_display_mock_stop": True,
                   "unchanged_scene_layout_and_mesh_proofs_reused": True,
                   "browser_v2_exact_bounded_source_diff_and_fieldset_join": True, "browser_helper_node_syntax": "pass"},
        "reviewed_scope": [
            "Frozen v2 wrapper/readiness/source verification and all15 target pins; exact source-only verify_current() replay, original output byte/hash/size bindings and byte-identical site scene.",
            "Both readiness reviewed-native digests join the input native-result pin and actual bytes before any original prepare/display work; expanded/revoked permissions, stale exporter and native digests fail closed.",
            "Supported prepare composes the exact original exporter and carries the guard/original/input/readiness union without changing the descriptor, saved receiver audit, release flags or output bytes.",
            "False response/native/release claims and wrong output path/digest/size are rejected; original fixed exclusive output reservation precedes native display, tested with an inert stop.",
            "Browser v2 changes only the reflected fieldset disabled-attribute assertion, source path and result schema; inspection/navigation/hash/error/screenshot scope remains the frozen v1 scope.",
        ],
        "limits": [
            "Only stdlib source/output replay, mock read/hash/entrypoint controls and Node syntax. No CAD/OCP/BREP import, tessellation, model rebuild, native/FEA/global mechanics or browser execution.",
            "Unchanged valid four-axis/eight-bore arithmetic, real Three997+4+20 composition and prior failure-ownership/routing proofs are reused within their frozen scope; no mesh proof rerun.",
            "Verification authenticates existing output evidence and fresh source joins; it does not independently regenerate displayed mesh geometry or native observations.",
            "The separate Z180 preview remains unadopted; current Z200 authority and its100/66 inventory/actions stay intact. No panel remedy, force/acceptance transfer, complete resistance, drilling, fabrication or climbing release.",
            "Parent-owned browser helper was running according to the frozen manifest; this review makes no browser-pass claim. The frozen target's two unused local names have the explicit RUF059 waiver and are not correctness findings.",
        ],
    }
    out = OWN.with_name("receipt.json")
    with out.open("x") as stream:
        json.dump(receipt, stream, sort_keys=True, indent=2, allow_nan=False)
        stream.write("\n")
    verify()
    print(json.dumps({"receipt": str(out.relative_to(ROOT)), "sha256": sha(out), "helper_sha256": sha(OWN),
                      "target_files": 15, "files": len(pins), "controls": len(controls), "findings": 0}, sort_keys=True))


if __name__ == "__main__":
    main()
