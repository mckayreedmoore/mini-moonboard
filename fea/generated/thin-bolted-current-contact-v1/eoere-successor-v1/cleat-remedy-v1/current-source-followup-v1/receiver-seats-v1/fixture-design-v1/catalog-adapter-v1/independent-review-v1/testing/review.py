"""Catalog adapter testing: immutable source/scalar evidence, owned scratch only."""
from __future__ import annotations

import builtins
import copy
import hashlib
import importlib.util
import io
import itertools
import json
import math
import os
import sys
import tempfile
from contextlib import redirect_stdout
from pathlib import Path
from types import FunctionType
from unittest.mock import patch

sys.dont_write_bytecode = True
OWN = Path(__file__).resolve()
OUT = OWN.parent
PACKET = OUT.parent.parent
FIXTURE = PACKET.parent
ROOT = next(p for p in OWN.parents if (p / "AGENTS.md").is_file())
EXPECTED = {
    "inputs.json": "dd0df7d6b5eb30aab11184c4d4471333e545b270232333ba9577678c9155282d",
    "adapter.py": "f3831931d6c89330e07d76d1099cc4ecdf9a9a0c6e7be1b069413a7a1bc22a04",
    "result-v2.json": "e5e34e992365aedf30b56710efd9dcbb4d1a64e77e4ede29ff656d0479ff17de",
    "result-v2.svg": "4b52eaba8f98d5457b606061f5d51eace14bc222d38dc6bc0f873d91ff2e1b6b",
    "verify.py": "dd755dc20baf508cb03896062f317d5e4a6171e732b1a7329461da4b8a3931d3",
    "verification-v1.json": "7cc2edc01fbdf98536e0a2029ea7e090503e135df7d698395127bbc30bea55b1",
}


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def require(ok, message):
    if not ok:
        raise AssertionError(message)


def rejected(call):
    try:
        call()
    except (ValueError, KeyError, FileExistsError, FileNotFoundError) as exc:
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
    require(before == EXPECTED, "six frozen adapter targets differ")
    historical = [PACKET / name for name in ("result.json", "result.svg") if (PACKET / name).is_file()]
    development = PACKET / "development-v1"
    if development.is_dir():
        historical += [path for path in development.rglob("*") if path.is_file()]
    historical_hashes = {str(path.relative_to(ROOT)): sha(path) for path in historical}
    adapter = load(PACKET / "adapter.py", "frozen_catalog_adapter_testing")
    verifier = load(PACKET / "verify.py", "frozen_catalog_verifier_testing")
    generic_verifier = load(FIXTURE / "verify.py", "frozen_generic_guard_testing")
    saved = adapter.read(PACKET / "result-v2.json")
    issued = adapter.read(PACKET / "verification-v1.json")
    actual = adapter.calculate()
    require(actual == {key: value for key, value in saved.items() if key != "drawing"}, "actual catalog scalar replay differs")
    picture = adapter.drawing(saved)
    require(picture == (PACKET / "result-v2.svg").read_bytes(), "actual catalog SVG replay differs")
    corners = verifier.decimal_corners(saved)
    require(corners == issued["independent_decimal_checks"] and corners["independent_decimal_endpoint_corners"] == 256, "independent Decimal corner API replay differs")
    require(len(saved["source_sha256"]) == 25 and all(sha(ROOT / name) == digest for name, digest in saved["source_sha256"].items()), "twenty-five direct pins")
    require(len(saved["release"]) == 13 and all(value is False for value in saved["release"].values()) and saved["release"] == issued["release"], "thirteen false release fields")
    require(len(saved["actual_observations"]) == 9 and all(value == "" for value in saved["actual_observations"].values()), "nine blank observations")
    require(saved["preserved"]["current_forces_transferred_to_Z180"] is False and saved["preserved"]["current_Z200_and_four_HOLD_stations"] is True, "frame/force boundary")
    require(saved["FISCH_nominal_comparison"]["NL_minus_full_cap_chip_path_reference_mm"] < 0 and all(not row.get("within_generic_allocation", row.get("within_generic_target")) for row in saved["generic_error_allowance_comparisons"].values()), "negative references and unmet allocations must remain")

    values = adapter.load()
    inp, facts, generic_inp, _generic, _shapes, _method, pins = values
    d = generic_inp["dimensions_mm"]
    # Independent upstream line extrapolation at the cap: both possible sleeve
    # segment placements and both signs at its constrained ends, all extrema.
    slops = []
    for length, head, height_error, gap, location, entry, exit_ in itertools.product(
            (18.669, 19.431), (5.17525, 5.93725), (-.2, .2), (0., .05), (0., 1.), (-.05, .05), (-.05, .05)):
        segment_top_below_body_top = location * (length - 18.)
        free = head + 6.35 + height_error + gap + segment_top_below_body_top
        cap = entry + (entry - exit_) * free / 18.
        slops.append(abs(cap))
    cap_slop = max(slops)
    require(len(slops) == 128 and abs(cap_slop - saved["cap_and_mounting"]["cap_top_bit_center_slop_bound_mm"]) < 1e-12, "independent cap endpoint bound")
    cap_margin = (12.6 - 11.1125) / 2 - cap_slop - .15
    require(abs(cap_margin - saved["cap_and_mounting"]["conditional_cap_hole_swept_bit_margin_mm"]) < 1e-12 and cap_margin > 0, "independent swept cap opening")
    fastener = min(math.dist(a, [u, 180.]) for a in d["retainer_fastener_centers_uv"] for u in (44.45, 95.25)) - 20.621625 / 2 - 12.7 / 2
    require(abs(fastener - saved["cap_and_mounting"]["conditional_fastener_head_to_flange_gap_mm"]) < 1e-12, "independent catalog flange/fastener gap")
    require(saved["clamps"]["guide_bare_opening_nominal_mm"] == 133.35, "guide clamp stack with feet")

    source_controls = []
    original_sha = adapter.sha
    with patch.object(adapter, "sha", side_effect=lambda path: "0" * 64 if Path(path) == adapter.INPUT else original_sha(path)):
        source_controls.append({"name": "input_bytes", "rejection": rejected(adapter.load)})
    corrupted = dict(pins)
    corrupted[next(iter(corrupted))] = "0" * 64
    source_controls.append({"name": "source_hash", "rejection": rejected(lambda: adapter.verify(corrupted))})
    original_read = adapter.read
    altered_facts = copy.deepcopy(facts)
    altered_facts["sources"]["FISCH_pen_drill"]["raw_active_cache"]["bytes"] += 1
    with patch.object(adapter, "read", side_effect=lambda path: copy.deepcopy(altered_facts) if Path(path) == ROOT / inp["catalog_facts_path"] else original_read(path)):
        source_controls.append({"name": "primary_PDF_bytes", "rejection": rejected(adapter.load)})

    constraint_controls = []
    mutations = [
        ("H_body_diameter", "facts", ("sources", "Carr_Lane_H", "facts", "body_OD_nominal_mm"), 16.),
        ("H_underhead_length", "facts", ("sources", "Carr_Lane_H", "facts", "underhead_length_nominal_mm"), 20.),
        ("H_head_F", "facts", ("sources", "Carr_Lane_H", "facts", "head_OD_F_nominal_mm"), 21.),
        ("H_head_G", "facts", ("sources", "Carr_Lane_H", "facts", "head_height_G_nominal_mm"), 6.),
        ("counterbore_row", "facts", ("sources", "Carr_Lane_H", "facts", "H_40_12_row_has_counterbore_asterisk"), True),
        ("obsolete_catalog_tolerance", "facts", ("sources", "Carr_Lane_installation", "facts", "unlisted_standard_ANSI_dimension_plus_minus_mm"), .254),
        ("metal_fit_promoted_to_wood", "facts", ("sources", "Carr_Lane_installation", "facts", "recommended_metal_jig_hole_does_not_qualify_wood_plate"), False),
        ("guidance_longer_than_short_body", "input", ("changes", "effective_contiguous_guidance_min_mm"), 20.),
        ("feet_datum", "input", ("changes", "temporary_guide_feet_height_mm"), 6.),
        ("guide_datum", "input", ("changes", "guide_top_w_nominal_mm"), 115.),
        ("body_reaches_frame", "input", ("changes", "noncatalog_fixture_height_aggregate_deviation_max_mm"), 10.),
        ("cap_capture", "input", ("changes", "cap_hole_nominal_D_mm"), 25.),
        ("cap_swept_aperture", "input", ("changes", "cap_hole_nominal_D_mm"), 10.),
        ("false_budget_success", "input", ("retained_error_conditions", "relative_bore_screw_target_mm"), 2.),
    ]
    for name, kind, path, replacement in mutations:
        altered = list(values)
        index = 1 if kind == "facts" else 0
        altered[index] = copy.deepcopy(altered[index])
        change(altered[index], path, replacement)
        with patch.object(adapter, "load", return_value=tuple(altered)):
            constraint_controls.append({"name": name, "rejection": rejected(adapter.calculate)})

    decimal_controls = []
    paths = [("reach_and_guidance", key) for key in ("worst_cap_to_point_breakout_mm", "worst_free_chuck_projection_mm", "nominal_cap_to_point_breakout_mm", "nominal_free_chuck_projection_mm")]
    paths += [("chip_routes", "physical_bushing_exit_to_wood_gap_interval_mm", index) for index in (0, 1)]
    paths += [("cap_and_mounting", "conditional_minimum_radial_capture_lip_mm"), ("chip_routes", "gap_minimum_minus_general_reference_mm")]
    paths += [("generic_error_allowance_comparisons", key, "derived_bound_mm") for key in ("guide_tilt", "insert_play", "relative_bore_screw")]
    paths += [(key,) for key in ("minimum_body_capsule_separation_after_derived_bound_mm", "hypothetical_whole_screw9p525_separation_after_derived_bound_mm")]
    paths += [("FISCH_nominal_comparison", key) for key in ("NL_minus_full_cap_chip_path_reference_mm", "NL_minus_physical_lower_exit_reference_mm", "NL_minus_wood_exposure_reference_mm", "GL_minus_worst_projection_mm")]
    paths += [("configured_ID_cases", row, key, index) for row in range(3) for key in ("catalog_ID_interval_mm", "printed_nominal_diametral_gap_range_mm") for index in (0, 1)]
    for path in paths:
        altered = copy.deepcopy(saved)
        old_value = altered
        for key in path:
            old_value = old_value[key]
        change(altered, path, old_value + 1e-6)
        decimal_controls.append({"field": ".".join(map(str, path)), "rejection": rejected(lambda altered=altered: verifier.decimal_corners(altered))})
    for row in range(3):
        altered = copy.deepcopy(saved)
        altered["configured_ID_cases"][row]["actual_bit_fit_established"] = True
        decimal_controls.append({"field": f"configured_ID_cases.{row}.actual_bit_fit_established", "rejection": rejected(lambda altered=altered: verifier.decimal_corners(altered))})

    with tempfile.TemporaryDirectory(prefix="review-scratch-", dir=OUT) as raw:
        scratch = Path(raw)
        (scratch / "controls01").mkdir()
        (scratch / "result.json").write_bytes(b"owned historical-result guard fixture")
        actual_generic_guards = generic_verifier.guard_checks

        def owned_guards(function):
            with patch.object(generic_verifier, "HERE", scratch), patch.dict(function.__globals__, {"HERE": scratch}):
                return actual_generic_guards(function)

        guards = owned_guards(adapter.output_paths)
        require(guards == issued["output_guard_controls"] and len(guards) == 8, "reused output guard API replay")
        output_paths = adapter.output_paths

        def own_paths(requested):
            with patch.object(adapter, "HERE", scratch):
                return output_paths(requested)

        producer_path = scratch / "adapter-replay.json"
        with patch.object(adapter, "output_paths", side_effect=own_paths), patch.object(sys, "argv", [str(PACKET / "adapter.py"), "--out", str(producer_path)]), redirect_stdout(io.StringIO()):
            adapter.main()
        producer = adapter.read(producer_path)
        producer["drawing"]["path"] = saved["drawing"]["path"]
        require(producer == saved and producer_path.with_suffix(".svg").read_bytes() == picture, "owned producer CLI replay differs beyond drawing path")
        producer_hash = sha(producer_path)
        with patch.object(adapter, "output_paths", side_effect=own_paths), patch.object(sys, "argv", [str(PACKET / "adapter.py"), "--out", str(producer_path)]):
            rejected(adapter.main)
        require(sha(producer_path) == producer_hash, "existing producer output changed")

        # Preserve frozen verifier input paths. Redirect the final receipt and
        # the reused guard routine's scratch paths; no shared writes occur.
        virtual_leaf = PACKET / ("_testing_unwritten_" + str(os.getpid()) + ".json")
        require(not os.path.lexists(virtual_leaf), "virtual receipt path occupied")
        owned_receipt = scratch / "verification-replay.json"
        original_open, original_stat, original_mkdir = Path.open, Path.stat, Path.mkdir
        original_run_path = verifier.runpy.run_path
        def guard_proxy(function):
            return owned_guards(function)

        isolated_proxy = FunctionType(guard_proxy.__code__, {}, closure=guard_proxy.__closure__)

        def redirect_run_path(path, *args, **kwargs):
            return {"guard_checks": isolated_proxy} if Path(path) == FIXTURE / "verify.py" else original_run_path(path, *args, **kwargs)

        def redirect_open(path, *args, **kwargs):
            return original_open(owned_receipt if path == virtual_leaf else path, *args, **kwargs)

        def redirect_stat(path, *args, **kwargs):
            return original_stat(owned_receipt if path == virtual_leaf else path, *args, **kwargs)

        def redirect_mkdir(path, *args, **kwargs):
            return original_mkdir(scratch / "controls01" if path == PACKET / "controls01" else path, *args, **kwargs)

        with patch.object(verifier.runpy, "run_path", side_effect=redirect_run_path), patch.object(Path, "open", redirect_open), patch.object(Path, "stat", redirect_stat), patch.object(Path, "mkdir", redirect_mkdir), patch.object(sys, "argv", [str(PACKET / "verify.py"), "--out", str(virtual_leaf)]), redirect_stdout(io.StringIO()):
            verifier.main()
        require(owned_receipt.read_bytes() == (PACKET / "verification-v1.json").read_bytes() and not os.path.lexists(virtual_leaf), "owned verifier main replay differs or wrote shared path")
        verification_hash = sha(owned_receipt)
        nonfinite = scratch / "nonfinite.json"
        nonfinite.write_bytes(b'{"x": NaN}\n')
        source_controls.append({"name": "nonfinite_JSON", "rejection": rejected(lambda: adapter.read(nonfinite))})

    require(before == {name: sha(PACKET / name) for name in EXPECTED}, "six target files changed")
    require(all(sha(ROOT / name) == digest for name, digest in pins.items()), "twenty-five source pins changed")
    require(historical_hashes == {name: sha(ROOT / name) for name in historical_hashes}, "historical bytes changed")
    return {"schema": "eoere_Z180_catalog_adapter_independent_testing_review/v1",
            "review_helper": {"path": str(OWN.relative_to(ROOT)), "sha256": sha(OWN)},
            "six_target_sha256_before_after": before, "direct_source_pin_count": 25,
            "historical_hash_only_before_after": historical_hashes,
            "actual_scalar_and_SVG_replay_exact": True, "independent_Decimal_API_replay_exact": True,
            "independent_Decimal_endpoint_corners": 256, "additional_cap_line_endpoint_corners": len(slops),
            "additional_cap_slop_mm": cap_slop, "additional_cap_swept_margin_mm": cap_margin,
            "additional_fastener_flange_gap_mm": fastener,
            "source_controls": source_controls, "catalog_and_constraint_controls": constraint_controls,
            "independent_Decimal_tamper_controls": decimal_controls, "reused_output_guard_API_controls": guards,
            "owned_producer_CLI_JSON_sha256": producer_hash, "producer_CLI_sole_normalized_difference": "drawing.path points to own temporary SVG",
            "owned_verifier_main_exact_replay_sha256": verification_hash,
            "all13_release_fields_false": True, "all9_actual_observation_values_blank": True,
            "generic_allowances_remain_unmet": True, "negative_full_cap_bit_reference_retained": True,
            "findings": [], "sources_unchanged_before_after": True,
            "scope": "Actual scalar and SVG producer replay, actual independent Decimal API and 256 endpoint corners, additional 128 cap-endpoint corners, mutations, reused output guards, owned producer main replay and verifier main with only receipt/guard scratch IO redirected. Existing generic/native source evidence and manufacturer facts reused, not independently re-qualified or fetched.",
            "excluded": ["native/CAD/BREP/FEA/global/physical execution", "browser or SVG rendering", "site/model/shared documentation changes", "manufacturer fact or PDF interpretation re-audit", "actual catalog part/bit fit", "field tolerance or workholding proof", "budget relaxation or strength acceptance", "staging or commit"],
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
    require(not native_attempts, "non-stdlib import attempted")
    receipt["native_or_numeric_library_import_attempts"] = native_attempts
    output = OUT / "receipt.json"
    with output.open("xb") as stream:
        stream.write((json.dumps(receipt, sort_keys=True, indent=2, allow_nan=False) + "\n").encode())
    print(json.dumps({"receipt": str(output.relative_to(ROOT)), "sha256": sha(output), "findings": len(receipt["findings"])}))
