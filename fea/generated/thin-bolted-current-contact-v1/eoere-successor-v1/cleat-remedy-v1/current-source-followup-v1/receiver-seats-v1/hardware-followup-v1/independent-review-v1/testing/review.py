"""Bounded source/scalar testing review; private CLI outputs only in /tmp."""
from __future__ import annotations

import hashlib
import importlib.util
import itertools
import json
import shutil
import subprocess
import sys
import tempfile
from decimal import Decimal
from pathlib import Path
from unittest.mock import patch

OWN = Path(__file__).resolve()
TARGET = OWN.parents[2]
ROOT = next(p for p in OWN.parents if (p / "AGENTS.md").is_file())
EXPECTED = {"inputs.json": "6cba1fb87b9cfa337f2c5418afe6c0f7fa6def8d6ae463e9f355701df3d75e33",
            "calculate.py": "ed7a16cbdb97bf15ddc74e2af49bb3b512dc57c7541358392db55ea25d8dfc0e",
            "result.json": "fbe6983488fc5c3017810654f43df0e0ef2188657387cc6a3b92b4e02fbb4c0a"}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    return json.loads(path.read_bytes())


def load():
    spec = importlib.util.spec_from_file_location("hardware_test_subject", TARGET / "calculate.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def decimal(value):
    return Decimal(str(value))


def close(value, expected):
    assert abs(decimal(value) - decimal(expected)) < Decimal("1e-8"), (value, expected)


def independent_scalars(result, inp, catalog):
    unit = Decimal("25.4")
    diameter = next(d for d in catalog["diameters"] if d["diameter_in"] == .375)
    products = {p["sku"]: p for p in catalog["bolts"]}
    washer = [decimal(v) * unit for v in diameter["washer"]["thickness_bounds_in"]]
    nut = [decimal(v) * unit for v in diameter["nut"]["height_bounds_in"]]
    pitch = unit / decimal(diameter["threads_per_inch"])
    assert [s["axis_id"] for s in result["four_stations"]] == inp["axis_ids"]
    assert result["release"] == inp["release"] and all(v is False for v in result["release"].values())
    assert result["current_axes_stay_Z_mm"] == 200. and result["proposed_Z_mm_unadopted"] == 180.
    assert result["limits"] == inp["limits"] and result["actual_observation_cells_remain_blank"] is True
    checked = 0
    for station in result["four_stations"]:
        stack = Decimal("76.2")
        wh = Decimal("2.6416")
        model_nut = Decimal("8.5598")
        assert [c["sku"] for c in station["comparisons"]] == [367, 368]
        close(station["matched_wood_travel_mm"], stack)
        close(station["planning_usable_bit_reach_mm"], stack + decimal(inp["guide_mm"]) + decimal(inp["backer_travel_mm"]))
        assert station["current_point_xyz_mm"][2] == station["drill_entry_xyz_mm"][2] == 200.
        assert station["unadopted_proposed_point_xyz_mm"][2] == 180.
        for comparison in station["comparisons"]:
            product = products[comparison["sku"]]
            length = decimal(product["nominal_length_in"]) * unit
            lengths = [length - decimal(product["length_tolerance_minus_in"]) * unit, length]
            gage = decimal(product["Lg_max_in"]) * unit
            # Independently enumerate exact-decimal box corners. The production
            # analytic-extrema helper does not participate in these expectations.
            corners = [(l - stack - h - w - n, stack + h + w - g)
                       for l, h, w, n, g in itertools.product(lengths, washer, washer, nut, [Decimal(0), gage])]
            tips, seats = zip(*corners, strict=True)
            window = comparison["window"]
            for observed, expected in zip(window["tip_projection_bounds_mm"], [min(tips), max(tips)], strict=True):
                close(observed, expected)
            close(window["catalog_min_length_max_stack_two_tip_margin_mm"], min(tips) - 2 * pitch)
            close(window["nut_near_minus_Lg_max_bounds_mm"][0], min(seats))
            close(window["nut_near_minus_Lg_max_bounds_mm"][1], stack + 2 * max(washer) - gage)
            close(comparison["independent_box_corners"]["minimum_two_pitch_margin_mm"], min(tips) - 2 * pitch)
            close(comparison["independent_box_corners"]["minimum_nut_near_minus_gage_mm"], min(seats))
            assert comparison["independent_box_corners"]["corner_count"] == len(corners) == 32
            body_margin = decimal(product["Lb_min_in"]) * unit - (stack + wh)
            close(comparison["minimum_body_minus_model_farthest_bearing_mm"], body_margin)
            close(comparison["possible_thread_or_runout_in_far_receiver_mm"], max(Decimal(0), -body_margin))
            close(comparison["possible_thread_or_runout_far_receiver_fraction"], max(Decimal(0), -body_margin) / Decimal("38.1"))
            model_well = length - stack - 2 * wh
            catalog_well = length - stack - 2 * min(washer)
            for key, expected in {
                "nominal_length_mm": length, "nominal_tip_beyond_nut_mm": model_well - model_nut,
                "blind_socket_required_clear_depth_model_mm": model_well,
                "blind_socket_required_clear_depth_catalog_max_mm": catalog_well,
                "conditional_36mm_well_minus_required_catalog_max_mm": Decimal(36) - catalog_well,
                "saved_method_bolt_headward_travel_mm": length + 2,
                "saved_method_nut_nutward_travel_model_mm": model_well + 2,
                "saved_method_nut_washer_nutward_travel_model_mm": model_well + 4,
                "incremental_nominal_tip_and_withdrawal_mm": length - Decimal("101.6"),
                "four_bolt_individual_price_increment_usd": 4 * (decimal(product["unit_price_usd"]) - decimal(products[367]["unit_price_usd"])),
            }.items():
                close(comparison[key], expected)
            assert comparison["actual_fit_or_access_or_thread_bearing_verified"] is False
            checked += len(corners)
        short, long = station["comparisons"]
        assert short["minimum_body_minus_model_farthest_bearing_mm"] < 0 < long["minimum_body_minus_model_farthest_bearing_mm"]
        assert short["window"]["nut_near_minus_Lg_max_bounds_mm"][0] > 0 > long["window"]["nut_near_minus_Lg_max_bounds_mm"][1]
    limits = result["washer_and_fillet_limits"]
    close(limits["minimum_catalog_ID_minus_maximum_reference_wood_hole_mm"], Decimal(".433") * unit - decimal(inp["maximum_wood_hole_mm"]))
    close(limits["minimum_ID_minus_maximum_fillet_diameter_mm"], Decimal(".008") * unit)
    close(limits["minimum_catalog_washer_thickness_minus_maximum_fillet_length_mm"], Decimal("-.023") * unit)
    assert limits["full_nominal_annular_seat_proof_covers_all_catalog_corners"] is False
    assert limits["actual_washer_material_or_contact_or_fillet_seating_verified"] is False
    return {"station_comparisons": 8, "exact_decimal_box_corners": checked,
            "four_inch_body_exposure_mm": 10.5156, "four_p5_inch_body_margin_mm": 2.1844,
            "longer_nut_near_minus_gage_range_mm": [-9.4488, -7.4168],
            "longer_conditional_socket_well_margin_mm": 1.1512,
            "guide_plus_pair_plus_backer_reach_mm": 101.6}


def semantic_controls(m, inp):
    json_original, csv_original = m.json.loads, m.csv.DictReader
    observed = {}
    cases = (("geometry", "axis_census"), ("placement", "proposal_translation"), ("bottom", "prior_axis_join"),
             ("catalog", "full_thread"), ("catalog", "reversed_washer_bounds"), ("catalog", "nonfinite_length"),
             ("stacks", "stack_length"), ("stacks", "body_target"), ("stacks", "actual_observation"),
             ("access", "missing_own_side"), ("holes", "wrong_receiver"), ("holes", "wall_length"))
    for source, mode in cases:
        path = ROOT / inp["sources"][source]["path"]
        raw = path.read_bytes()

        def decode(value, *args, source=source, mode=mode, raw=raw, **kwargs):
            result = json_original(value, *args, **kwargs)
            if value != raw or source in {"stacks", "access", "holes"}:
                return result
            if mode == "axis_census":
                result["axes"].pop()
            elif mode == "proposal_translation":
                result["proposed_axes"][0]["point_xyz_mm"][0] += 1.
            elif mode == "prior_axis_join":
                next(a for a in result["axes"] if a["id"] == inp["axis_ids"][0])["grip_mm"] += 1.
            elif mode == "full_thread":
                next(p for p in result["bolts"] if p["sku"] == 367)["partially_threaded"] = False
            elif mode == "nonfinite_length":
                next(p for p in result["bolts"] if p["sku"] == 367)["nominal_length_in"] = float("nan")
            else:
                next(d for d in result["diameters"] if d["diameter_in"] == .375)["washer"]["thickness_bounds_in"].reverse()
            return result

        def rows(stream, *args, mode=mode, path=path, **kwargs):
            result = list(csv_original(stream, *args, **kwargs))
            if Path(stream.name) != path:
                return result
            own = next(r for r in result if r["axis_id"] == inp["axis_ids"][0])
            if mode == "stack_length":
                own["receiver_plus_plate_mm"] = "75"
            elif mode == "body_target":
                own["model_body_to_farthest_bearing_target_mm"] = "75"
            elif mode == "actual_observation":
                key = next(k for k in own if k.startswith("Actual"))
                own[key] = "unobserved invented value"
            elif mode == "missing_own_side":
                own["axis_id"] = "foreign-axis"
            elif mode == "wrong_receiver":
                own["receiver"] = "foreign"
            elif mode == "wall_length":
                own["saved_full_wall_length_mm"] = "37"
            return result

        with patch.object(m.json, "loads", decode), patch.object(m.csv, "DictReader", rows):
            try:
                m.evaluate()
            except ValueError as error:
                observed[mode] = str(error)
            else:
                raise AssertionError("semantic corruption accepted: " + mode)
    return observed


def temporary_cli(directory, result):
    mirror = directory / "mirror"
    packet = mirror / TARGET.relative_to(ROOT)
    packet.mkdir(parents=True)
    for name in ("calculate.py", "inputs.json"):
        shutil.copyfile(TARGET / name, packet / name)
    for relative, expected in result["source_sha256"].items():
        path = mirror / relative
        if path.exists():
            assert sha(path) == expected
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.symlink_to(ROOT / relative)
    command = [sys.executable, "-B", str(packet / "calculate.py"), "--out"]
    output = packet / "replay.json"
    run = subprocess.run([*command, str(output)], text=True, capture_output=True, check=False, timeout=30)
    assert run.returncode == 0, run.stderr
    assert read(output) == result
    protected = {output: sha(output), packet / "inputs.json": sha(packet / "inputs.json")}
    negatives = {}
    for mode, target in (("occupied", output), ("input_alias", packet / "inputs.json"),
                         ("outside_packet", mirror / "outside.json"), ("wrong_suffix", packet / "wrong.txt")):
        run = subprocess.run([*command, str(target)], text=True, capture_output=True, check=False, timeout=30)
        assert run.returncode != 0 and all(sha(p) == h for p, h in protected.items())
        negatives[mode] = "rejected without changing protected files"
    destination, link = packet / "redirected.json", packet / "already-existing-link.json"
    link.symlink_to(destination)
    assert link.is_symlink() and not destination.exists()
    redirected = subprocess.run([*command, str(link)], text=True, capture_output=True, check=False, timeout=30)
    assert redirected.returncode == 0 and link.is_symlink() and read(destination) == result
    race = packet / "contended.json"
    processes = [subprocess.Popen([*command, str(race)], stdout=subprocess.PIPE, stderr=subprocess.PIPE) for _ in range(2)]
    for process in processes:
        process.communicate(timeout=30)
    assert sorted(p.returncode for p in processes) == [0, 1] and read(race) == result
    return {"byte_identical_producer_and_inputs_reproduced_full_result": True, "all_outputs_in_private_tmp_root": True,
            "ordinary_negative_output_controls": negatives, "ordinary_same_output_race_returncodes": [0, 1],
            "confirmed_dangling_symlink_behavior": {"requested_entry_preexisted_as_symlink": True,
                "returncode": redirected.returncode, "previously_absent_target_created": True,
                "target_is_complete_unadopted_result": True}}


def main():
    result, inp = read(TARGET / "result.json"), read(TARGET / "inputs.json")
    frozen = read(ROOT / inp["sources"]["frozen_receiver_packet"]["path"])

    def unchanged():
        assert all(sha(TARGET / name) == expected for name, expected in EXPECTED.items())
        assert all(sha(ROOT / path) == expected for path, expected in result["source_sha256"].items())
        assert all(sha(ROOT / r["path"]) == r["sha256"] for r in frozen["final_files"] + frozen["retained_development_files"])

    unchanged()
    m = load()
    assert m.evaluate() == result
    scalars = independent_scalars(result, inp, read(ROOT / inp["sources"]["catalog"]["path"]))
    semantics = semantic_controls(m, inp)
    with tempfile.TemporaryDirectory(prefix="hardware-testing-review-") as scratch:
        cli = temporary_cli(Path(scratch), result)
    unchanged()
    assert not any(n in sys.modules for n in ("cadquery", "OCP", "numpy", "scipy"))
    findings = [{"priority": "P2", "path": str((TARGET / "calculate.py").relative_to(ROOT)), "line": 213,
        "title": "Preserve the requested output entry when checking and opening a fresh result",
        "impact": "An existing dangling --out symlink to an absent .json target inside the owned subpacket is accepted. Path.resolve() replaces the requested directory entry before exists/open(x), so the genuine CLI creates the target and succeeds instead of rejecting the already occupied output entry. Ordinary files and competing regular writers remain protected.",
        "reproduction": "Byte-identical frozen producer and inputs replayed in a private source-linked /tmp mirror. Create already-existing-link.json -> redirected.json with the latter absent; the actual CLI returns 0 and creates redirected.json containing the complete frozen result.",
        "fix": "Preserve the frozen packet. In a new CLI revision, retain the original requested Path for exclusive creation and use its resolved parent only for ownership checks; reject existing symlink entries. Add a dangling-symlink regression asserting no callback/target creation."}]
    report = {"schema": "eoere_four_cleat_post_hardware_independent_testing_review/v1",
        "status": "SCALAR_REPRODUCTION_PASSES_OUTPUT_ENTRY_GUARD_REVISION_REQUIRED", "confirmed_substantial_findings": findings,
        "source_sha256": {str((TARGET / name).relative_to(ROOT)): expected for name, expected in EXPECTED.items()},
        "review_source_sha256": {str(OWN.relative_to(ROOT)): sha(OWN)}, "source_pins_unchanged_before_after": len(result["source_sha256"]),
        "retained_receiver_final_and_development_files_unchanged": 10, "full_source_evaluate_matches_result": True,
        "independent_decimal_scalar_checks": scalars, "in_memory_semantic_corruptions_rejected": semantics,
        "temporary_actual_CLI_checks": cli, "limits": inp["limits"], "release": inp["release"],
        "scope": "Frozen scalar/tool-planning evidence only. Four-inch projection/seating and longer-body/nut-seating tradeoff are reproduced; no hardware adoption, delivered fit, actual tool access, root resistance or complete-joint acceptance follows.",
        "execution": {"stdlib_source_and_scalar_only": True, "CAD_native_global_field_or_bulk_execution": False,
                      "shared_documents_index_staging_or_commit_changes": False},
        "retention": "Keep this compact review helper/receipt active. Source-linked temporary CLI outputs and in-memory corruptions were private; all old reviewed packets and original target files remain unchanged."}
    output = OWN.with_name("receipt.json")
    output.write_text(json.dumps(report, indent=2, sort_keys=True, allow_nan=False) + "\n")
    print(json.dumps({"path": str(output.relative_to(ROOT)), "sha256": sha(output), "bytes": output.stat().st_size,
                      "confirmed_substantial_findings": len(findings)}, sort_keys=True))


if __name__ == "__main__":
    main()
