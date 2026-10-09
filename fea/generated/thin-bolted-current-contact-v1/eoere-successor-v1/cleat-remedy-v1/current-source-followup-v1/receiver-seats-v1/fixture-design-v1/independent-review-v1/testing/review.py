"""Frozen fixture design: stdlib replay, verifier API and guard controls only."""
from __future__ import annotations

import builtins
import copy
import hashlib
import importlib.util
import io
import json
import math
import os
import sys
import tempfile
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

sys.dont_write_bytecode = True
OWN = Path(__file__).resolve()
OUT = OWN.parent
PACKET = OUT.parent.parent
ROOT = next(p for p in OWN.parents if (p / "AGENTS.md").is_file())
EXPECTED = {
    "inputs.json": "b17a8f72f41ab2b8ce75ffaac15af075432a0ffe7111daead6597cb34eff86be",
    "design.py": "4c84897e42d4d32b1692bec8801a3c002b1c5684f984a907bde8e2cc73e4a3db",
    "result.json": "ec1c101da8f16f29cf0949c75086418e01e3b89268f55e27379fdb6a83a212f5",
    "result.svg": "60b5b105d42d35350bfe5a263f1c997974f7b3f9b1a27eea0317f88a84bd37c7",
    "verify.py": "b91887fa829c4bda60332dd1541ef26f3648d4613c5725e7f6a25d74e4cd3513",
    "verification-v1.json": "28fe869385596b6b09b562ee009654da491c7fc4e10013de99ba6edc5977aab4",
}


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def require(ok, message):
    if not ok:
        raise AssertionError(message)


def rejected(call):
    try:
        call()
    except (ValueError, KeyError, FileNotFoundError, FileExistsError) as exc:
        return str(exc)
    raise AssertionError("expected rejection")


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def change(value, path, replacement):
    for key in path[:-1]:
        value = value[key]
    value[path[-1]] = replacement


def review():
    before = {name: sha(PACKET / name) for name in EXPECTED}
    require(before == EXPECTED, "frozen six-file packet mismatch")
    design = load(PACKET / "design.py", "frozen_fixture_design_testing")
    verifier = load(PACKET / "verify.py", "frozen_fixture_verifier_testing")
    saved = design.read(PACKET / "result.json")
    issued_verification = design.read(PACKET / "verification-v1.json")
    inp, result, shapes = design.evaluate()
    require(result == {key: value for key, value in saved.items() if key != "drawing"}, "actual scalar producer replay differs")
    picture = design.drawing(inp, result, shapes)
    require(picture == (PACKET / "result.svg").read_bytes(), "actual drawing replay differs")
    require(verifier.decimal_checks(saved) == issued_verification["independent_decimal_checks"], "actual independent Decimal API replay differs")
    require(len(saved["source_sha256"]) == 17 and all(sha(ROOT / name) == digest for name, digest in saved["source_sha256"].items()), "seventeen direct pins")
    require(saved["release"] == inp["release"] == issued_verification["release"] and len(saved["release"]) == 10 and all(value is False for value in saved["release"].values()), "ten release claims")
    require(len(saved["actual_observations"]) == 7 and all(row["Actual"] == row["Disposition"] == "" for row in saved["actual_observations"]), "blank observations")
    require(saved["saved_signed_end_scope"]["current_Z200_actions_assigned_to_Z180"] is False and saved["saved_signed_end_scope"]["complete_Cdelta_or_strength"] is None, "force/strength separation")
    require(saved["pointwise_error_and_reach_budget"]["actual_terms_observed_or_achieved"] is False and saved["support_and_clamp_requirements"]["full_drill_clamp_handle_hand_or_workholding_qualification"] is False, "unobserved conditional requirements")
    _, data, _, profile, datum, capsule = design.prepare()
    proposed, _, cuts, _ = design.source_inventory(inp, data, profile, datum)
    require(design.controls(capsule) == saved["method_controls"], "known-answer API replay")

    rectangle_cases = [([1, 1], [[0, 2], [0, 2]], 0.), ([0, 0], [[0, 2], [0, 2]], 0.),
                       ([3, 4], [[0, 2], [0, 2]], math.sqrt(5)), ([-3, 1], [[0, 2], [0, 2]], 3.),
                       ([3, -1], [[0, 2], [0, 2]], math.sqrt(2)), ([4, 6], [[0, 0], [0, 0]], math.sqrt(52))]
    for point, rectangle, expected in rectangle_cases:
        require(design.point_rectangle(point, rectangle) == expected, "independent rectangle known answer")
    require(design.point_rectangle([1, 0], [[0, 2], [0, 2]]) - 1 < 0, "contact-circle crossing")
    base = capsule.primitive("base", "axis", [0., 0., 0.], [1., 0., 0.], 0., 10., 0.)
    segment_cases = [([10., 0., 0.], [1., 0., 0.], 0., 2., 0.),
                     ([12., 0., 0.], [1., 0., 0.], 0., 2., 2.),
                     ([5., 3., 4.], [1., 0., 0.], 0., 0., 5.),
                     ([5., 3., 4.], [0., -.6, -.8], 0., 10., 0.),
                     ([12., 3., 4.], [0., .6, .8], 0., 10., math.sqrt(29))]
    for point, direction, near, far, expected in segment_cases:
        other = capsule.primitive("other", "axis", point, direction, near, far, 0.)
        require(abs(capsule.axis_distance(base, other) - expected) < 1e-12, "finite capsule known answer")
    rejected(lambda: capsule.primitive("bad", "axis", [0., 0., 0.], [2., 0., 0.], 0., 1., 0.))

    source_controls = []
    original_sha = design.sha
    with patch.object(design, "sha", side_effect=lambda path: "0" * 64 if Path(path) == design.INPUT else original_sha(path)):
        source_controls.append({"name": "input_bytes", "rejection": rejected(design.prepare)})
    corrupted_pins = dict(saved["source_sha256"])
    corrupted_pins[next(iter(corrupted_pins))] = "0" * 64
    source_controls.append({"name": "direct_source_hash", "rejection": rejected(lambda: design.verify(corrupted_pins))})
    source_mutations = [("axis_census", ("geometry", "axes"), data["geometry"]["axes"][:-1]),
                        ("screw_census", ("geometry", "screw_axes"), data["geometry"]["screw_axes"][:-1]),
                        ("revision_join", ("placement", "base_revision"), "historical"),
                        ("proposal_adoption", ("placement", "geometry_adopted"), True),
                        ("proposal_only_Z", ("placement", "proposed_axes", 0, "grip_mm"), -1),
                        ("native_full_wall", ("native_result", "scenarios", 0, "wall_queries", 0, "full_wall_length_mm"), 0),
                        ("native_partial_wall", ("native_result", "scenarios", 0, "wall_queries", 0, "partial_wall_present"), True),
                        ("native_annulus", ("native_result", "scenarios", 0, "annular_queries", 0, "observed_backing_fraction"), .5)]
    for name, path, replacement in source_mutations:
        altered = copy.deepcopy(data)
        change(altered, path, replacement)
        source_controls.append({"name": name, "rejection": rejected(lambda altered=altered: design.source_inventory(inp, altered, profile, datum))})
    altered = copy.deepcopy(proposed)
    altered[0]["direction_xyz"] = [-value for value in altered[0]["direction_xyz"]]
    source_controls.append({"name": "handed_drill_direction", "rejection": rejected(lambda: design.transforms(inp, altered, shapes))})

    constraint_controls = []
    mutations = [("full_path_guide_angle", ("error_budget", "guide_normal_angle_max_deg"), .2, design.budget),
                 ("full_path_insert_play", ("error_budget", "bushing_diametral_play_max_mm"), .2, design.budget),
                 ("effective_insert_length", ("dimensions_mm", "bushing_effective_length_min"), 10., design.budget),
                 ("total_allocation", ("error_budget", "terms_mm", "future_screw_axis_placement"), .5, design.budget),
                 ("capture_lip", ("dimensions_mm", "retainer_clearance_hole_D"), 23., design.retainer),
                 ("swept_cap_opening", ("dimensions_mm", "retainer_clearance_hole_D"), 11.1125, design.retainer),
                 ("local_chuck_nose", ("dimensions_mm", "chuck_nose_keepout_radius"), 40., design.retainer)]
    for name, path, replacement, function in mutations:
        altered = copy.deepcopy(inp)
        change(altered, path, replacement)
        arguments = (altered, saved["nominal_primitive_clearance"]) if function is design.budget else (altered,)
        constraint_controls.append({"name": name, "rejection": rejected(lambda function=function, arguments=arguments: function(*arguments))})
    altered = copy.deepcopy(inp)
    altered["dimensions_mm"]["guide_clamp_centers_uv"][0] = [44.45, 180.]
    constraint_controls.append({"name": "actual_contact_circle_crossing_rejected_by_footprints", "rejection": rejected(lambda: design.footprints(altered, shapes, cuts, profile))})

    verifier_controls = []
    checked_paths = [("pointwise_error_and_reach_budget", "guide_tilt_max_mm"),
                     ("pointwise_error_and_reach_budget", "insert_slop_max_mm"),
                     ("pointwise_error_and_reach_budget", "allocated_sum_mm"),
                     ("pointwise_error_and_reach_budget", "unallocated_reserve_mm"),
                     ("pointwise_error_and_reach_budget", "minimum_declared_body_clearance_after_budget_mm"),
                     ("pointwise_error_and_reach_budget", "conditional_whole_screw9p525_clearance_after_budget_mm"),
                     ("support_and_clamp_requirements", "minimum_chuck_nose_to_clamp_lane_margin_mm")]
    checked_paths += [("pointwise_error_and_reach_budget", "reach_requirements_mm", key) for key in saved["pointwise_error_and_reach_budget"]["reach_requirements_mm"]]
    checked_paths += [("pointwise_error_and_reach_budget", "geometric_tie_lower_bounds_mm", key) for key in saved["pointwise_error_and_reach_budget"]["geometric_tie_lower_bounds_mm"]]
    checked_paths += [("support_and_clamp_requirements", "bare_opening_mm", key) for key in saved["support_and_clamp_requirements"]["bare_opening_mm"]]
    for path in checked_paths:
        altered = copy.deepcopy(saved)
        value = altered
        for key in path:
            value = value[key]
        change(altered, path, value + 1e-6)
        verifier_controls.append({"field": ".".join(path), "rejection": rejected(lambda altered=altered: verifier.decimal_checks(altered))})

    with tempfile.TemporaryDirectory(prefix="review-scratch-", dir=OUT) as raw:
        scratch = Path(raw)
        (scratch / "controls01").mkdir()
        (scratch / "result.json").write_bytes(b"owned occupied guard fixture")
        original_guards = verifier.guard_checks

        def owned_guards(function):
            with patch.object(verifier, "HERE", scratch), patch.dict(function.__globals__, {"HERE": scratch}):
                return original_guards(function)

        guards = owned_guards(design.output_paths)
        require(guards == issued_verification["output_guard_controls"], "independent verifier guard API replay")
        original_paths = design.output_paths

        def own_paths(requested):
            with patch.object(design, "HERE", scratch):
                return original_paths(requested)

        producer_path = scratch / "producer-replay.json"
        with patch.object(design, "output_paths", side_effect=own_paths), patch.object(sys, "argv", [str(PACKET / "design.py"), "--out", str(producer_path)]), redirect_stdout(io.StringIO()):
            design.main()
        producer = design.read(producer_path)
        producer["drawing"]["path"] = saved["drawing"]["path"]
        require(producer == saved and producer_path.with_suffix(".svg").read_bytes() == picture, "owned producer CLI replay differs beyond drawing path")
        producer_replay = {"json_sha256_before_path_normalization": sha(producer_path), "svg_sha256": sha(producer_path.with_suffix(".svg")), "sole_difference_from_frozen_result": "drawing.path points to own fresh temporary output"}
        with patch.object(design, "output_paths", side_effect=own_paths), patch.object(sys, "argv", [str(PACKET / "design.py"), "--out", str(producer_path)]):
            rejected(design.main)
        require(sha(producer_path) == producer_replay["json_sha256_before_path_normalization"], "producer overwrote existing output")

        # Keep the verifier's frozen input scope; redirect only its final receipt
        # IO and run its hardcoded guard scratch routine in this reviewer directory.
        virtual_leaf = PACKET / ("_testing_unwritten_" + str(os.getpid()) + ".json")
        require(not os.path.lexists(virtual_leaf), "virtual verification destination occupied")
        owned_receipt = scratch / "verifier-replay.json"
        original_open, original_stat = Path.open, Path.stat

        def redirect_open(path, *args, **kwargs):
            return original_open(owned_receipt if path == virtual_leaf else path, *args, **kwargs)

        def redirect_stat(path, *args, **kwargs):
            return original_stat(owned_receipt if path == virtual_leaf else path, *args, **kwargs)

        with patch.object(verifier, "guard_checks", side_effect=owned_guards), patch.object(Path, "open", redirect_open), patch.object(Path, "stat", redirect_stat), patch.object(sys, "argv", [str(PACKET / "verify.py"), "--out", str(virtual_leaf)]), redirect_stdout(io.StringIO()):
            verifier.main()
        require(owned_receipt.read_bytes() == (PACKET / "verification-v1.json").read_bytes() and not os.path.lexists(virtual_leaf), "owned verifier CLI replay differs or wrote shared path")
        verifier_replay_hash = sha(owned_receipt)
        nonfinite = scratch / "nonfinite.json"
        nonfinite.write_bytes(b'{"x": NaN}\n')
        source_controls.append({"name": "nonfinite_JSON", "rejection": rejected(lambda: design.read(nonfinite))})

    require(before == {name: sha(PACKET / name) for name in EXPECTED}, "six frozen files changed")
    require(all(sha(ROOT / name) == digest for name, digest in saved["source_sha256"].items()), "direct sources changed")
    return {"schema": "eoere_Z180_fixture_design_independent_testing_review/v1",
            "review_helper": {"path": str(OWN.relative_to(ROOT)), "sha256": sha(OWN)},
            "six_file_sha256_before_after": before, "direct_source_pins": 17,
            "actual_evaluate_and_drawing_replay_exact": True,
            "owned_producer_CLI_replay": producer_replay,
            "owned_verifier_CLI_replay_sha256": verifier_replay_hash,
            "independent_Decimal_API_replay_exact": True, "verifier_output_guard_API_controls": guards,
            "additional_rectangle_known_answers": len(rectangle_cases), "additional_finite_segment_known_answers": len(segment_cases),
            "source_census_direction_controls": source_controls, "fixture_constraint_controls": constraint_controls,
            "independent_verifier_tamper_controls": verifier_controls,
            "blank_actual_disposition_rows": 7, "all10_release_fields_false": True,
            "findings": [], "sources_unchanged_before_after": True,
            "scope": "Actual stdlib evaluate/drawing and independent Decimal/guard APIs; producer main with only the owned destination binder substituted; verifier main with only final receipt IO and guard temporary paths redirected into reviewer scratch. All scratch removed after hashes. Saved native/profile/capsule evidence reused within declared scalar scope; no independent native or all-pairs geometry audit.",
            "generic_insert_catalog_or_actual_fit_qualified": False, "mechanics_or_physical_release": False,
            "excluded": ["native/CAD/BREP imports, queries or reconstruction", "browser or SVG rendering", "tessellation", "FEA/frame/global solve", "actual tool/stock/workholding/tolerance evidence", "catalog hardware selection", "strength acceptance", "shared/model/index edits or commits"]}


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
    require(not native_attempts, "non-stdlib import attempted")
    receipt["native_or_numeric_library_import_attempts"] = native_attempts
    output = OUT / "receipt.json"
    with output.open("xb") as stream:
        stream.write((json.dumps(receipt, sort_keys=True, indent=2, allow_nan=False) + "\n").encode())
    print(json.dumps({"receipt": str(output.relative_to(ROOT)), "sha256": sha(output), "findings": len(receipt["findings"])}))
