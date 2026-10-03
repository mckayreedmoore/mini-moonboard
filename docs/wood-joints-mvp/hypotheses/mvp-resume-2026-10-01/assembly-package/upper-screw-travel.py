"""Check four translated screw enclosures against 48 saved bolt-travel boxes."""

from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.util
import json
import math
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
UPPER = HERE.parent / "upper-corner-screw-layout"
HELPER = HERE / "hardware_length_fit.py"
LENGTH_DIR = HERE / "rawlocal/hardware-length-fit/saved-source-attempt02"
SETUP = LENGTH_DIR / "setup.json"
RESULT = LENGTH_DIR / "result.json"
OVERLAY_SETUP = UPPER / "rawlocal/attempt01/setup.json"
OVERLAY_RECEIPT = UPPER / "rawlocal/shop-axes/receipt.json"
OVERLAY_CSV = UPPER / "rawlocal/shop-axes/axes.csv"
DELTA = [0.0, 42.391842858827275, 50.5206310236966]
SCREWS = {
    "round_panel_upper_left_rim_4",
    "round_panel_upper_right_rim_4",
    "round_panel_upper_left_center_4",
    "round_panel_upper_right_center_4",
}
PINS = {
    HELPER: "fd54fbe3d7d59c504b4ec80519155a12802e593c98c8043867d80746977d5b8b",
    SETUP: "c49b72d742e1bce7c876860ec6c8c1d50e1d1c80bab6585636387df5f08a4529",
    RESULT: "df5271e4c65f90a620dff4630cfa5d0dec303456fa1bb4a1185fc950dbaf2aa5",
    OVERLAY_SETUP: "00cfa71d30a1d8d789df7c4a40770f9ec46e3e56c0ee9d23018d62e6c11583bc",
    OVERLAY_RECEIPT: "535bcdaeb85ed683e66040c8042dd6c3bdea7d835ca7a9d7c510de99d6cf773d",
    OVERLAY_CSV: "46406c559d1f427ad4422edf033759831a83d0ddcef4bbb871579da132853eca",
}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    return json.loads(path.read_text())


def same(first, second, label):
    require(len(first) == len(second) and all(
        math.isclose(a, b, rel_tol=0, abs_tol=1e-7)
        for a, b in zip(first, second, strict=True)
    ), label)


def box(values):
    require(len(values) == 6 and all(math.isfinite(value) for value in values), "invalid saved bounds")
    require(all(values[2 * i] <= values[2 * i + 1] for i in range(3)), "inverted saved bounds")
    return list(values)


def build(output: Path):
    output = Path(output).resolve()
    require(not output.exists(), f"preserve previous output: {output}")
    pins = {**PINS, Path(__file__).resolve(): sha(Path(__file__))}
    for path, expected in pins.items():
        require(sha(path) == expected, f"frozen source differs: {path}")
    setup, previous, overlay, receipt = map(read, (SETUP, RESULT, OVERLAY_SETUP, OVERLAY_RECEIPT))
    require(previous["producer_sha256"] == PINS[HELPER] and previous["setup_sha256"] == PINS[SETUP],
            "length receipt source binding differs")
    require(previous["geometry_rebuilt"] is False and previous["source_unchanged_after_run"] is True,
            "length receipt is not the unchanged saved scene")
    require(receipt["source_sha256"]["geometry_setup"] == PINS[OVERLAY_SETUP]
            and receipt["csv"]["sha256"] == PINS[OVERLAY_CSV], "overlay receipt binding differs")
    require(set(overlay["changed_axis_ids"]) == SCREWS
            and set(receipt["reconciliation"]["moved_axis_ids"]) == SCREWS,
            "relocated axis set differs")
    with OVERLAY_CSV.open(newline="") as stream:
        schedule = {row["axis_id"]: row for row in csv.DictReader(stream)}
    require(len(schedule) == 66, "overlay schedule does not contain 66 unique axes")

    # ponytail: import only the frozen stdlib box-distance helper; never its CAD run.
    sys.dont_write_bytecode = True
    spec = importlib.util.spec_from_file_location("frozen_length_box_helper", HELPER)
    require(spec is not None and spec.loader is not None, "saved box helper unavailable")
    helper = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(helper)
    queries = setup["queries"]
    require(len(queries) == len({query["id"] for query in queries}) == 48,
            "saved query census differs")
    require({query["axis_id"] for query in queries} == set(helper.TARGET_IDS),
            "saved twelve-route axis set differs")
    moves = {row["axis_id"]: row for row in overlay["before_after"]}
    obstacles = {row["id"]: row for row in setup["obstacles"]}
    relocated = []
    pairs = []
    for axis_id in sorted(SCREWS):
        move = moves[axis_id]
        before, after = move["before"], move["after"]
        same(move["translation_xyz_mm"], DELTA, f"{axis_id} translation differs")
        same(before["axis_direction_xyz"], after["axis_direction_xyz"], f"{axis_id} direction changed")
        same([after["axis_origin_xyz_mm"][i] - before["axis_origin_xyz_mm"][i] for i in range(3)],
             DELTA, f"{axis_id} datums differ from recorded translation")
        require(before["nominal_length_mm"] == after["nominal_length_mm"] == 63.5
                and before["nominal_diameter_mm"] == after["nominal_diameter_mm"] == 4.1402,
                f"{axis_id} nominal enclosure differs")
        row = schedule[axis_id]
        same([float(row[f"front_datum_{coordinate}_global_mm"]) for coordinate in "xyz"],
             after["axis_origin_xyz_mm"], f"{axis_id} CSV datum differs")
        same([float(row[f"direction_{coordinate}_global"]) for coordinate in "xyz"],
             after["axis_direction_xyz"], f"{axis_id} CSV direction differs")
        require(row["receiver_member"] == after["receiver_member"], f"{axis_id} CSV receiver differs")
        saved = obstacles["panel_screw/" + axis_id]
        require(saved["category"] == "panel_screw_envelope", f"{axis_id} source is not a screw enclosure")
        original = box(saved["bounds_xyz_mm"])
        translated = [value + DELTA[i // 2] for i, value in enumerate(original)]
        source_bounds = helper._inflate(helper._cylinder_bounds(
            before["axis_origin_xyz_mm"],
            [before["axis_origin_xyz_mm"][i] + 63.5 * before["axis_direction_xyz"][i] for i in range(3)],
            before["axis_direction_xyz"], 4.1402 / 2,
        ))
        same(original, source_bounds, f"{axis_id} saved enclosure does not bind before datum")
        relocated.append({
            "axis_id": axis_id, "source_obstacle_id": saved["id"],
            "before_bounds_xyz_mm": original, "translated_bounds_xyz_mm": translated,
            "translation_xyz_mm": DELTA, "before_front_datum_xyz_mm": before["axis_origin_xyz_mm"],
            "after_front_datum_xyz_mm": after["axis_origin_xyz_mm"],
            "direction_xyz": after["axis_direction_xyz"], "receiver_member": after["receiver_member"],
            "enclosure_scope": saved["geometry_limit"],
        })
        for query in queries:
            distance = helper._box_gap(box(query["bounds_xyz_mm"]), translated)
            pairs.append({
                "screw_axis_id": axis_id, "query_id": query["id"],
                "bolt_axis_id": query["axis_id"], "query_component": query["component"],
                "AABB_distance_lower_bound_mm": distance,
                "status": "clear_by_conservative_AABB_separation" if distance > 0
                else "overlapping_boxes_preserved_for_parent",
            })
    require(len(pairs) == 192, "four-by-forty-eight pair census differs")
    unresolved = [pair for pair in pairs if pair["status"] == "overlapping_boxes_preserved_for_parent"]
    for path, expected in pins.items():
        require(sha(path) == expected, f"source changed during bounded arithmetic: {path}")
    output.mkdir(parents=True, exist_ok=False)
    (output / "producer.py.snapshot").write_bytes(Path(__file__).read_bytes())
    with (output / "pairs.csv").open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(pairs[0]))
        writer.writeheader()
        writer.writerows(pairs)
    result = {
        "schema": "upper_screw_travel_overlay_AABB_delta/v1",
        "status": "completed_overlay_pair_screen" if not unresolved else "overlapping_boxes_preserved_for_parent",
        "counts": {"relocated_screws": 4, "saved_bolt_routes": 12, "saved_queries": 48,
                   "pairs": 192, "positive_box_separations": 192 - len(unresolved),
                   "overlapping_box_candidates": len(unresolved)},
        "relocated_screws": relocated, "pairs": pairs, "overlapping_box_candidates": unresolved,
        "minimum_pair_separation": min(pairs, key=lambda pair: pair["AABB_distance_lower_bound_mm"]),
        "source_sha256": {path.relative_to(ROOT).as_posix(): expected for path, expected in pins.items()},
        "output_sha256": {path.name: sha(path) for path in output.iterdir()},
        "source_unchanged_after_run": True, "geometry_rebuilt": False,
        "exact_geometry_intersections_performed": False, "software_tests_performed": False,
        "limits": [
            "Only the 192 changed screw-envelope/query pairs are evaluated; the prior full scene is not rerun.",
            "A strictly positive saved enclosure gap certifies separation for that pair; box overlap is undecided, not collision.",
            "Screw enclosures are nominal 63.5 mm by 4.1402 mm occupied cylinders with the saved 0.001 mm inflation; heads, tools and delivered profiles are not added.",
            "Queries retain the earlier proposed tip extensions and extra headward shaft/head/washer movement, not the entire installation or removal sequence.",
            "No source axis, STEP, mesh, hardware selection, physical operation or acceptance authority changes.",
        ],
        "complete_joint_acceptance": False, "physical_release": False,
    }
    (output / "result.json").write_text(json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n")
    for path, expected in pins.items():
        require(sha(path) == expected, f"source changed before final receipt: {path}")
    print(json.dumps({"status": result["status"], "counts": result["counts"],
                      "result_sha256": sha(output / "result.json")}))
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    build(parser.parse_args().output)


if __name__ == "__main__":
    main()
