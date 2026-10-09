"""Source-only spacer-window testing, immutable targets and owned scratch IO."""
from __future__ import annotations

import builtins
import copy
import hashlib
import io
import itertools
import json
import os
import runpy
import sys
import tempfile
from contextlib import redirect_stdout
from decimal import Decimal
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

sys.dont_write_bytecode = True
OWN = Path(__file__).resolve()
OUT = OWN.parent
PACKET = OUT.parent.parent
ROOT = next(p for p in OWN.parents if (p / "AGENTS.md").is_file())
EXPECTED = {
    "spacer-window-inputs-v1.json": "9326e6cfb8280760c47d00dace8967b84eecccbf813f5ea2e7dfb96841b49813",
    "spacer-window-v1.py": "59f429916ff26f897f5ace94fee610b0e420e261094e9f10659e937b44b0b3d6",
    "spacer-window-result-v1.json": "592c237e8f98456f936deaf3b8613f60c493008851e65f43a9fbde6300929896",
}
D = Decimal


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def review():
    retained = PACKET.parent / "fixture-design-v1/catalog-adapter-v1/independent-review-v1/testing/review.py"
    assert sha(retained) == "9fddef5ba3f4c8148eab1ce2858671ef54aceda46b9bb6bae0434353893bd00e"
    utilities = runpy.run_path(str(retained))
    load, require, rejected, change = (utilities[key] for key in ("load", "require", "rejected", "change"))
    before = {name: sha(PACKET / name) for name in EXPECTED}
    require(before == EXPECTED, "three frozen spacer targets")
    method = load(PACKET / "spacer-window-v1.py", "frozen_spacer_window_testing")
    inputs_raw = (PACKET / "spacer-window-inputs-v1.json").read_bytes()
    prior_raw = (PACKET / "result-v3.json").read_bytes()
    inputs, prior = json.loads(inputs_raw), json.loads(prior_raw)
    saved = json.loads((PACKET / "spacer-window-result-v1.json").read_bytes())
    pins = saved["source_sha256"]
    require(len(pins) == 34 and saved["source_pin_count"] == 34 and all(sha(ROOT / name) == digest for name, digest in pins.items()), "thirty-four source pins")
    catalog_path = next(name for name in inputs["sources"] if name.endswith("/catalog-inputs.json"))
    catalog = json.loads((ROOT / catalog_path).read_bytes())
    bolt = next(row for row in catalog["bolts"] if row["sku"] == 368)
    diameter = next(row for row in catalog["diameters"] if row["diameter_in"] == bolt["diameter_in"])
    mm = D("25.4")
    length_max = D(str(bolt["nominal_length_in"])) * mm
    length_min = length_max - D(str(bolt["length_tolerance_minus_in"])) * mm
    washer = tuple(D(str(value)) * mm for value in diameter["washer"]["thickness_bounds_in"])
    nut = tuple(D(str(value)) * mm for value in diameter["nut"]["height_bounds_in"])
    pitch = mm / D(str(diameter["threads_per_inch"]))
    grip = D(str(bolt["Lg_max_in"])) * mm
    body = D(str(bolt["Lb_min_in"])) * mm
    nominal = D(str(inputs["spacer"]["length_in"])) * mm
    independent = []
    for row in saved["station_comparisons"]:
        wood = D(str(row["wood_stack_mm"]))
        lower = grip - wood - 2 * min(washer)
        upper = length_min - wood - 2 * max(washer) - max(nut) - 2 * pitch
        require([float(lower), float(upper)] == row["derived_spacer_length_interval_mm"] and lower <= nominal <= upper, "independent exact interval")
        count = 0
        for length, wh, wn, nh, spacing in itertools.product((length_min, length_max), washer, washer, nut, (lower, upper)):
            near = wood + wh + wn + spacing
            require(near >= grip and length - near - nh >= 2 * pitch, "independent inclusive corner")
            count += 1
        require(wood + 2 * min(washer) + lower - D(".001") < grip, "below-boundary negative")
        require(length_min - wood - 2 * max(washer) - upper - D(".001") - max(nut) < 2 * pitch, "above-boundary negative")
        smooth = body - wood - max(washer)
        require(smooth > 0 and smooth - nominal < 0 and float(smooth) == row["smooth_body_reserve_beyond_far_wood_mm"] and float(smooth - nominal) == row["hypothetical_head_side_spacer_smooth_body_reserve_mm"], "nut-side/head-side topology distinction")
        well = length_max - wood - 2 * min(washer) - nominal
        require(float(well) == row["max_socket_well_from_nut_near_face_mm"] and float(D("36") - well) == row["conditional_36mm_socket_well_reserve_mm"], "independent conditional well")
        independent.append({"axis_id": row["axis_id"], "interval_mm": [str(lower), str(upper)], "endpoint_combinations": count, "smooth_wood_reserve_mm": str(smooth), "wrong_head_side_reserve_mm": str(smooth - nominal)})

    original_loads = json.loads

    def evaluated_fixture(*, changed_inputs=None, changed_prior=None):
        def parsed(raw, *args, **kwargs):
            if changed_inputs is not None and raw == inputs_raw:
                return copy.deepcopy(changed_inputs)
            if changed_prior is not None and raw == prior_raw:
                return copy.deepcopy(changed_prior)
            return original_loads(raw, *args, **kwargs)

        with patch.object(method, "json", SimpleNamespace(loads=parsed)):
            return method.evaluate()

    boundary_controls = []
    for label, length_in, accepted in (("lower_inclusive", ".372", True), ("upper_inclusive", ".73", True),
                                       ("below_lower", ".37199", False), ("above_upper", ".73001", False)):
        changed = copy.deepcopy(inputs)
        changed["spacer"]["length_in"] = length_in
        if accepted:
            result = evaluated_fixture(changed_inputs=changed)
            require(len(result["station_comparisons"]) == 4, "inclusive boundary four stations")
            boundary_controls.append({"case": label, "nominal_length_mm": str(D(length_in) * mm), "accepted": True})
        else:
            boundary_controls.append({"case": label, "rejection": rejected(lambda changed=changed: evaluated_fixture(changed_inputs=changed))})
    census_controls = []
    changed = copy.deepcopy(prior)
    changed["four_stations"] = list(reversed(changed["four_stations"]))
    census_controls.append({"case": "reordered_axes", "rejection": rejected(lambda: evaluated_fixture(changed_prior=changed))})
    changed = copy.deepcopy(prior)
    changed["four_stations"].pop()
    census_controls.append({"case": "missing_station", "rejection": rejected(lambda: evaluated_fixture(changed_prior=changed))})
    for path in (("four_stations", 0, "comparisons", 1, "window", "ASME_Lb_min_mm"),
                 ("four_stations", 0, "comparisons", 1, "minimum_body_minus_model_farthest_bearing_mm")):
        changed = copy.deepcopy(prior)
        row = next(value for value in changed["four_stations"][0]["comparisons"] if value["sku"] == 368)
        target = row["window"] if "window" in path else row
        target[path[-1]] += .001
        census_controls.append({"case": "frozen_old_" + path[-1], "rejection": rejected(lambda changed=changed: evaluated_fixture(changed_prior=changed))})
    for path, replacement in ((("release", "fabrication"), True), (("actual_observations", "spacer_dimensions"), "unobserved")):
        changed = copy.deepcopy(inputs)
        change(changed, path, replacement)
        census_controls.append({"case": ".".join(path), "rejection": rejected(lambda changed=changed: evaluated_fixture(changed_inputs=changed))})

    source_controls = []
    original_sha = method.sha
    inherited = next(name for name in pins if name not in inputs["sources"] and not name.endswith(("spacer-window-v1.py", "spacer-window-inputs-v1.json")))
    for source in (str(method.INPUT.relative_to(ROOT)), *inputs["sources"], inherited):
        boundary = Mock(side_effect=AssertionError("shared helper loaded before source rejection"))
        with patch.object(method, "sha", side_effect=lambda path, source=source: "0" * 64 if path == ROOT / source else original_sha(path)), patch.object(method, "runpy", SimpleNamespace(run_path=boundary)):
            message = rejected(method.evaluate)
        require(not boundary.called, "source drift entered helper")
        source_controls.append({"path": source, "rejection": message, "before_helper_load": True})
    original_loader = runpy.run_path
    helper_path = ROOT / next(name for name in inputs["sources"] if name.endswith("/shop_windows.py"))

    def corrupted_helper(path, *args, **kwargs):
        module = original_loader(path, *args, **kwargs)
        if Path(path) == helper_path:
            measured = module["measured_window"]

            def bad_window(**options):
                value = measured(**options)
                value["two_pitch_margin_mm"] += .000001
                return value

            module["measured_window"] = bad_window
        return module

    with patch.object(method, "runpy", SimpleNamespace(run_path=corrupted_helper)):
        helper_control = rejected(method.evaluate)
    require(helper_control == "shared floating-point helper differs from independent Decimal arithmetic", "helper corruption wrong rejection")

    with tempfile.TemporaryDirectory(prefix="scratch-", dir=OUT) as raw:
        scratch = Path(raw)
        destination = scratch / "replay.json"
        virtual = PACKET / ("_testing_spacer_unwritten_" + str(os.getpid()) + ".json")
        require(not os.path.lexists(virtual), "virtual output occupied")
        original_open, original_stat = Path.open, Path.stat

        def redirect_open(path, *args, **kwargs):
            return original_open(destination if path == virtual else path, *args, **kwargs)

        def redirect_stat(path, *args, **kwargs):
            return original_stat(destination if path == virtual else path, *args, **kwargs)

        # Exactly one fresh genuine main/CLI parse/evaluate/write replay; only
        # final receipt IO is redirected into the exclusive owned scratch.
        with patch.object(Path, "open", redirect_open), patch.object(Path, "stat", redirect_stat), patch.object(sys, "argv", [str(PACKET / "spacer-window-v1.py"), "--out", str(virtual)]), redirect_stdout(io.StringIO()):
            method.main()
        require(destination.read_bytes() == (PACKET / "spacer-window-result-v1.json").read_bytes() and not os.path.lexists(virtual), "exact fresh CLI replay or shared write")
        replay_sha = sha(destination)
        occupied = scratch / "occupied.json"
        occupied.write_bytes(b"owned bytes must remain")
        dangling = scratch / "dangling.json"
        dangling.symlink_to(scratch / "absent.json")
        output_controls = []
        for label, requested in (("occupied", occupied), ("dangling", dangling), ("outside", OUT / "unwritten.json"), ("wrong_suffix", scratch / "unwritten.txt"), ("nested", scratch / "nested/unwritten.json")):
            boundary = Mock(side_effect=AssertionError("evaluate before output rejection"))
            with patch.object(method, "HERE", scratch), patch.object(method, "evaluate", boundary), patch.object(sys, "argv", [str(PACKET / "spacer-window-v1.py"), "--out", str(requested)]):
                message = rejected(method.main)
            require(not boundary.called and occupied.read_bytes() == b"owned bytes must remain" and dangling.is_symlink() and not dangling.exists(), "output guard work or overwrite")
            output_controls.append({"case": label, "rejection": message, "before_evaluate": True})
        late = scratch / "late.json"

        def late_occupied():
            late.write_bytes(b"owned late occupied bytes")
            return copy.deepcopy(saved)

        with patch.object(method, "HERE", scratch), patch.object(method, "evaluate", side_effect=late_occupied), patch.object(sys, "argv", [str(PACKET / "spacer-window-v1.py"), "--out", str(late)]):
            late_rejection = rejected(method.main)
        require(late.read_bytes() == b"owned late occupied bytes", "mode-x overwritten late output")

    require(before == {name: sha(PACKET / name) for name in EXPECTED} and all(sha(ROOT / name) == digest for name, digest in pins.items()), "target/source preservation")
    require(len(saved["release"]) == 8 and all(value is False for value in saved["release"].values()) and len(saved["actual_observations"]) == 5 and all(value == "" for value in saved["actual_observations"].values()), "release/observation boundary")
    require(saved["current_revision"] == prior["current_revision"] and saved["current_100_axes_canonical_sha256"] == prior["current_100_axes_canonical_sha256"] and saved["current_66_screw_axes_canonical_sha256"] == prior["current_66_screw_axes_canonical_sha256"], "current source identity")
    return {"schema": "eoere_four_station_spacer_window_independent_testing/v1",
            "review_helper": {"path": str(OWN.relative_to(ROOT)), "sha256": sha(OWN)},
            "three_target_sha256_before_after": before, "thirty_four_source_pins_authenticated_before_after": pins,
            "exactly_one_fresh_actual_CLI_replay_sha256": replay_sha,
            "CLI_replay_IO_only_redirection": "Final virtual hardware-followup output leaf to exclusive own scratch; canonical guard, genuine evaluate and serialization retained. No old helper CLI or native/CAD/browser execution.",
            "independent_Decimal_station_and_topology_checks": independent,
            "inclusive_and_outside_boundary_controls": boundary_controls,
            "parsed_in_memory_census_and_claim_controls": census_controls,
            "source_drift_rejections_before_shared_helper_load": source_controls,
            "corrupted_shared_measured_window_rejection": helper_control,
            "owned_output_rejections_before_evaluate": output_controls,
            "late_occupied_mode_x_preservation_rejection": late_rejection,
            "all8_release_flags_false_and5_actual_rows_blank": True,
            "all_sources_and_targets_unchanged": True, "findings": [],
            "scope": "Three frozen new files only. Reuse authenticated prior hardware source evidence and standard review utilities; independent Decimal interval/corner/socket/topology arithmetic, inclusive/outside and parsed in-memory source/schema/census fixtures, shared-helper corruption, source drift and owned output controls. Parsed-input fixtures deliberately intercept JSON values after unchanged byte authentication; they are not production inputs or changed catalog evidence. Current Z200/100 bolts/66 screws/forces/HOLD and unadopted Z180 unchanged.",
            "excluded": ["old case/native/CAD/BREP/FEA/browser/physical work", "broad historical or manufacturer source re-audit", "actual spacer tolerance, seating/tool/removal/strength qualification", "runtime or second-interpreter controls", "shared files/docs/index edits, staging or commit"],
            "mechanics_or_physical_release": False}


if __name__ == "__main__":
    original_import = builtins.__import__
    native_attempts = []

    def no_native(name, *args, **kwargs):
        if name.split(".")[0] in ("cadquery", "OCP", "numpy", "scipy"):
            native_attempts.append(name)
            raise AssertionError("forbidden import: " + name)
        return original_import(name, *args, **kwargs)

    with patch("builtins.__import__", side_effect=no_native):
        receipt = review()
    assert not native_attempts
    receipt["native_or_numeric_library_import_attempts"] = native_attempts
    destination = OUT / "receipt.json"
    with destination.open("xb") as stream:
        stream.write((json.dumps(receipt, sort_keys=True, indent=2, allow_nan=False) + "\n").encode())
    print(json.dumps({"receipt": str(destination.relative_to(ROOT)), "sha256": sha(destination), "findings": len(receipt["findings"])}))
