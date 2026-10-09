"""Independent Decimal scalar review; no CAD, native, field or global work."""

from __future__ import annotations

import ast
import copy
import csv
import hashlib
import itertools
import json
import math
import platform
import runpy
import sys
from decimal import Decimal as D
from pathlib import Path

OWN = Path(__file__).resolve()
HERE = OWN.parent
PACKET = HERE.parents[1]
ROOT = next(p for p in OWN.parents if (p / "AGENTS.md").is_file())
FROZEN = {
    "inputs.json": "6cba1fb87b9cfa337f2c5418afe6c0f7fa6def8d6ae463e9f355701df3d75e33",
    "calculate.py": "ed7a16cbdb97bf15ddc74e2af49bb3b512dc57c7541358392db55ea25d8dfc0e",
    "result.json": "fbe6983488fc5c3017810654f43df0e0ef2188657387cc6a3b92b4e02fbb4c0a",
}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    return json.loads(path.read_bytes())


def equal(actual, expected):
    if isinstance(expected, dict):
        assert actual.keys() == expected.keys(), (actual.keys(), expected.keys())
        for key in expected:
            equal(actual[key], expected[key])
    elif isinstance(expected, list):
        assert len(actual) == len(expected)
        for a, b in zip(actual, expected, strict=True):
            equal(a, b)
    elif isinstance(expected, (D, float)):
        assert math.isclose(actual, float(expected), rel_tol=0, abs_tol=1e-9), (actual, expected)
    else:
        assert actual == expected, (actual, expected)


def mm(value):
    return D(str(value)) * D("25.4")


def box(stack, product, diameter):
    """Enumerate endpoints before deriving independent extrema and budgets."""
    upper = mm(product["nominal_length_in"])
    lower = upper - mm(product["length_tolerance_minus_in"])
    ws = [mm(v) for v in diameter["washer"]["thickness_bounds_in"]]
    ns = [mm(v) for v in diameter["nut"]["height_bounds_in"]]
    pitch = D("25.4") / D(str(diameter["threads_per_inch"]))
    gage = mm(product["Lg_max_in"])
    corners = list(itertools.product((lower, upper), ws, ws, ns, (D(0), gage)))
    tips = [length - stack - head - washer - nut for length, head, washer, nut, _ in corners]
    seats = [stack + head + washer - grip for _, head, washer, _, grip in corners]
    window = {
        "underhead_length_bounds_mm": [lower, upper], "washer_each_bounds_mm": ws,
        "nut_height_bounds_mm": ns, "two_tip_pitches_mm": 2 * pitch,
        "required_length_at_max_catalog_stack_mm": stack + 2 * max(ws) + max(ns) + 2 * pitch,
        "combined_washers_plus_nut_budget_at_shortest_length_mm": lower - stack - 2 * pitch,
        "equal_washer_ceiling_at_shortest_length_and_max_nut_mm": (lower - stack - 2 * pitch - max(ns)) / 2,
        "tip_projection_bounds_mm": [min(tips), max(tips)],
        "nut_near_underhead_bounds_mm": [stack + 2 * min(ws), stack + 2 * max(ws)],
        "ASME_Lg_max_mm": gage, "ASME_Lb_min_mm": mm(product["Lb_min_in"]),
        "nut_near_minus_Lg_max_bounds_mm": [min(seats), stack + 2 * max(ws) - gage],
        "catalog_min_length_max_stack_two_tip_margin_mm": min(tips) - 2 * pitch,
    }
    return window, len(corners)


def review():
    for name, digest in FROZEN.items():
        assert sha(PACKET / name) == digest, name
    spec, saved = read(PACKET / "inputs.json"), read(PACKET / "result.json")
    source = lambda name: ROOT / spec["sources"][name]["path"]
    pins = {ref["path"]: ref["sha256"] for ref in spec["sources"].values()}
    for name in ("inputs.json", "calculate.py"):
        pins[str((PACKET / name).relative_to(ROOT))] = FROZEN[name]
    frozen = read(source("frozen_receiver_packet"))
    for record in frozen["final_files"] + frozen["retained_development_files"]:
        assert record["path"] not in pins or pins[record["path"]] == record["sha256"]
        pins[record["path"]] = record["sha256"]
    assert pins == saved["source_sha256"] and len(pins) == saved["source_pin_count"] == 27
    pins[str((PACKET / "result.json").relative_to(ROOT))] = FROZEN["result.json"]
    before = {p: sha(ROOT / p) for p in pins}
    assert before == pins
    geometry, bottom, placement = [read(source(n)) for n in ("geometry", "bottom", "placement")]
    axes = {a["id"]: a for a in geometry["axes"]}
    old = {a["id"]: a for a in bottom["axes"]}
    proposed = {a["id"]: a for a in placement["proposed_axes"]}
    assert len(axes) == 100 and len(geometry["screw_axes"]) == 66
    assert geometry["revision"] == spec["current_revision"] and placement["geometry_adopted"] is False
    tables = {}
    for name in ("stacks", "holes", "access"):
        with source(name).open(newline="") as stream:
            tables[name] = list(csv.DictReader(stream))
        assert all(v == "" for row in tables[name] for k, v in row.items()
                   if k.startswith("Actual") or k == "Disposition")
    assert [len(tables[n]) for n in ("stacks", "holes", "access")] == [100, 120, 200]
    stacks = {r["axis_id"]: r for r in tables["stacks"]}
    assert set(stacks) == set(axes)
    catalog = read(source("catalog"))
    diameter = next(d for d in catalog["diameters"] if d["diameter_in"] == .375)
    products = {b["sku"]: b for b in catalog["bolts"]}
    assert spec["comparison_skus"] == [367, 368] and len(set(spec["axis_ids"])) == 4
    assert [r["axis_id"] for r in saved["four_stations"]] == spec["axis_ids"]
    checked = []
    for row in saved["four_stations"]:
        name = row["axis_id"]
        axis, sheet = axes[name], stacks[name]
        assert axis == old[name] and int(sheet["comparison_bolt_SKU"]) == 367
        assert axis["diameter_mm"] == 9.525 and axis["nominal_under_head_length_mm"] == 101.6
        assert axis["point_xyz_mm"][2] == 200 and not axis["attachments"]
        altered = copy.deepcopy(axis)
        altered["point_xyz_mm"][2] = 180
        assert altered == proposed[name]
        equal(row["current_point_xyz_mm"], axis["point_xyz_mm"])
        equal(row["unadopted_proposed_point_xyz_mm"], altered["point_xyz_mm"])
        equal(row["receivers"], axis["receivers"])
        for key in ("drill_entry_xyz_mm",):
            equal(row[key], axis["point_xyz_mm"])
        for key in ("drill_inward_xyz", "nut_outward_xyz"):
            equal(row[key], axis["direction_xyz"])
        equal(row["head_bolt_outward_xyz"], [-v for v in axis["direction_xyz"]])
        holes = sorted((r for r in tables["holes"] if r["axis_id"] == name),
                       key=lambda r: float(r["entry_from_axis_point_mm"]))
        assert [r["receiver"] for r in holes] == axis["receivers"]
        equal([float(r["entry_from_axis_point_mm"]) for r in holes], [0., 38.1])
        equal([float(r["exit_from_axis_point_mm"]) for r in holes], [38.1, 76.2])
        own_access = [r for r in tables["access"] if r["axis_id"] == name]
        assert {r["side"] for r in own_access} == {"head", "nut"}
        for access in own_access:
            equal([float(v) for v in access["axis_origin_xyz_mm"].split(";")], axis["point_xyz_mm"])
            equal([float(v) for v in access["axis_positive_xyz"].split(";")], axis["direction_xyz"])
            assert access["reference_catalog_wrench_in"] == "9/16"
        stack, washer = D(sheet["receiver_plus_plate_mm"]), D(str(axis["hardware_scenario"]["washer_thickness_mm"]))
        assert stack == D("76.2") and D(sheet["model_body_to_farthest_bearing_target_mm"]) == stack + washer
        equal(row["matched_wood_travel_mm"], stack)
        equal(row["planning_usable_bit_reach_mm"], stack + D(str(spec["guide_mm"])) + D(str(spec["backer_travel_mm"])))
        for comparison in row["comparisons"]:
            product = products[comparison["sku"]]
            assert product["partially_threaded"] is True and product["diameter_in"] == .375
            window, count = box(stack, product, diameter)
            equal(comparison["window"], window)
            corners = comparison["independent_box_corners"]
            assert corners["corner_count"] == count == 32
            equal(corners["minimum_two_pitch_margin_mm"], window["catalog_min_length_max_stack_two_tip_margin_mm"])
            equal(corners["minimum_nut_near_minus_gage_mm"], window["nut_near_minus_Lg_max_bounds_mm"][0])
            length = mm(product["nominal_length_in"])
            well = length - stack - 2 * washer
            well_max = length - stack - 2 * min(window["washer_each_bounds_mm"])
            exposure = max(D(0), stack + washer - window["ASME_Lb_min_mm"])
            expectations = {
                "nominal_length_mm": length,
                "minimum_body_minus_model_farthest_bearing_mm": window["ASME_Lb_min_mm"] - stack - washer,
                "possible_thread_or_runout_in_far_receiver_mm": exposure,
                "possible_thread_or_runout_far_receiver_fraction": exposure / D("38.1"),
                "nominal_tip_beyond_nut_mm": well - D(str(axis["hardware_scenario"]["nut_height_mm"])),
                "blind_socket_required_clear_depth_model_mm": well,
                "blind_socket_required_clear_depth_catalog_max_mm": well_max,
                "conditional_36mm_well_minus_required_catalog_max_mm": 36 - well_max,
                "saved_method_bolt_headward_travel_mm": length + 2,
                "saved_method_nut_nutward_travel_model_mm": well + 2,
                "saved_method_nut_washer_nutward_travel_model_mm": well + 4,
                "incremental_nominal_tip_and_withdrawal_mm": length - D("101.6"),
                "four_bolt_individual_price_increment_usd": 4 * (D(str(product["unit_price_usd"])) - D(str(products[367]["unit_price_usd"]))),
                "actual_fit_or_access_or_thread_bearing_verified": False,
            }
            for key, value in expectations.items():
                equal(comparison[key], value)
            checked.append({"axis_id": name, "sku": product["sku"], "corners": count})
    limits = saved["washer_and_fillet_limits"]
    w = diameter["washer"]
    for prefix in ("OD", "ID", "thickness"):
        equal(limits[f"catalog_{prefix}_bounds_mm"], [mm(v) for v in w[f"{prefix}_bounds_in"]])
    fd, fl = mm(diameter["underhead_fillet_max_diameter_in"]), mm(diameter["underhead_fillet_max_length_in"])
    for key, value in {
        "fillet_max_diameter_mm": fd, "fillet_max_length_mm": fl,
        "minimum_ID_minus_maximum_fillet_diameter_mm": mm(w["ID_bounds_in"][0]) - fd,
        "model_washer_thickness_minus_maximum_fillet_length_mm": washer - fl,
        "minimum_catalog_washer_thickness_minus_maximum_fillet_length_mm": mm(w["thickness_bounds_in"][0]) - fl,
        "minimum_catalog_ID_minus_maximum_reference_wood_hole_mm": mm(w["ID_bounds_in"][0]) - D(str(spec["maximum_wood_hole_mm"])),
    }.items():
        equal(limits[key], value)
    assert limits["full_nominal_annular_seat_proof_covers_all_catalog_corners"] is False
    assert limits["actual_washer_material_or_contact_or_fillet_seating_verified"] is False
    assert all(v is False for v in spec["release"].values()) and saved["release"] == spec["release"]
    # Run only the authenticated stdlib evaluator; deny its historical preparation.
    for path in (PACKET / "calculate.py", source("hardware_method"), source("corner_method")):
        tree = ast.parse(path.read_text())
        imports = [n.module for n in ast.walk(tree) if isinstance(n, ast.ImportFrom)]
        imports += [a.name for n in ast.walk(tree) if isinstance(n, ast.Import) for a in n.names]
        assert all(name.split(".")[0] in sys.stdlib_module_names for name in imports)
    original = runpy.run_path
    evaluator = original(str(PACKET / "calculate.py"))["evaluate"]

    def forbidden(*args, **kwargs):
        raise AssertionError("Historical preparation/evaluation is outside this review")

    def guarded(path, *args, **kwargs):
        assert Path(path) in (source("hardware_method"), source("corner_method"))
        module = original(path, *args, **kwargs)
        for name in ("prepare", "evaluate"):
            if name in module:
                module[name] = forbidden
        return module

    runpy.run_path = guarded
    try:
        replay = evaluator()
    finally:
        runpy.run_path = original
    replay["execution"]["python_version"] = saved["execution"]["python_version"]
    assert replay == saved, "Exact replay differs beyond Python version"
    after = {p: sha(ROOT / p) for p in pins}
    assert before == after == pins
    return {
        "schema": "bounded_hardware_correctness_review/v1", "findings": [],
        "scope": "Frozen scalar arithmetic and current four-station metadata; no physical fit, adoption, capacity or primary-source requalification.",
        "helper_sha256": sha(OWN), "source_sha256": pins,
        "source_count_verified_before_after": len(pins), "sources_unchanged": True,
        "stdlib_replay_matches_saved_except_environment_version": True,
        "independent_Decimal_comparisons": checked, "box_corner_total": sum(r["corners"] for r in checked),
        "checks": ["Current Z200/two-receiver joins and separate Z180-only proposal", "All catalog length/washer/nut/gage endpoints", "Smooth-body exposure and conservative nut seating", "Nut-plus-tip well, model tip, saved removal convention and guide reach", "Washer ID/OD/thickness/fillet limits and explicit unknown contact", "All Actual/Disposition cells blank; all release flags false"],
        "limits": "No CAD/native/solver/global run or force-field consumption. Historical prepare/evaluate denied during replay. No shared edits, staging, commit or physical work.",
        "python_version": platform.python_version(),
        "reproduction_command": f"uv run python -B {OWN.relative_to(ROOT)}",
    }


if __name__ == "__main__":
    receipt = review()
    output = HERE / "receipt.json"
    with output.open("x") as stream:
        json.dump(receipt, stream, indent=2, allow_nan=False)
        stream.write("\n")
    print(json.dumps({"receipt": str(output.relative_to(ROOT)), "sha256": sha(output),
                      "sources": receipt["source_count_verified_before_after"], "findings": receipt["findings"]}))
