"""Independent current placement and scalar segment/capsule arithmetic review."""
from __future__ import annotations

import copy
import hashlib
import json
import math
import os
import subprocess
import sys
import tempfile
from pathlib import Path

OWN = Path(__file__).resolve()
ROOT = next(p for p in OWN.parents if (p / "AGENTS.md").is_file())
TARGET = OWN.parent.parent.parent
HASHES = {
    "inputs.json": "989a518a33f05c72c38613e9b8c53fc85458fc1aabc94948803ff5f9fe2bbb7f",
    "prepare.py": "9d12bcaa8d375153f4e93e4bfbc36c283ee3167bd614049e698d92ed067395c4",
    "placement.json": "5e131e9f58014b4a9426aa6a976338b930f471221e19b8e0e122ceff105f9b39",
    "result.json": "26d27f9c8f5e3c1d91e48143341a8e808d0ece99f316eaf789e2fcbe22e4252a",
    "verify.py": "267ff85c8fa87930a56f960f9c12c5a01329c546e117f012d1f16eae34b3d0d4",
    "verification.json": "ba4ed094c618cc71385754f6c4d06a05787f3706273a4faa4c6987f650c48acb",
}


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(path):
    return json.loads(Path(path).read_bytes())


def canonical(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()).hexdigest()


def dot(a, b):
    return math.fsum(x*y for x, y in zip(a, b, strict=True))


def subtract(a, b):
    return [x-y for x, y in zip(a, b, strict=True)]


def clip(x):
    return max(0., min(1., x))


def distance(first, second):
    """Closest segment pair by clamped first parameter and endpoint correction."""
    p, q, r, s = first[2], first[3], second[2], second[3]
    u, v, w = subtract(q, p), subtract(s, r), subtract(p, r)
    a, b, c, d, e = dot(u, u), dot(u, v), dot(v, v), dot(u, w), dot(v, w)
    if a == 0 and c == 0:
        return math.sqrt(dot(w, w))
    if a == 0:
        first_t, second_t = 0., clip(e/c)
    elif c == 0:
        first_t, second_t = clip(-d/a), 0.
    else:
        denominator = a*c-b*b
        first_t = clip((b*e-c*d)/denominator) if denominator > 1e-12*a*c else 0.
        second_t = (b*first_t+e)/c
        if second_t < 0:
            first_t, second_t = clip(-d/a), 0.
        elif second_t > 1:
            first_t, second_t = clip((b-d)/a), 1.
    error = [w[i]+first_t*u[i]-second_t*v[i] for i in range(3)]
    return math.sqrt(max(0., dot(error, error)))


def primitive(ident, role, point, direction, low, high, radius):
    norm = math.sqrt(dot(direction, direction))
    assert abs(norm-1) < 1e-8 and 0 <= radius and low < high
    direction = [v/norm for v in direction]
    return (ident, role, [p+low*d for p, d in zip(point, direction, strict=True)],
            [p+high*d for p, d in zip(point, direction, strict=True)], radius)


def hardware(axis, maximum=False):
    h, grip = axis["hardware_scenario"], axis["grip_mm"]
    head = -axis["before_plate_mm"]-h["washer_thickness_mm"]
    nut = grip+axis["after_plate_mm"]+h["washer_thickness_mm"]
    rows = [("shaft", head, head+axis["nominal_under_head_length_mm"], axis["diameter_mm"]/2),
        ("head", head-h["head_height_mm"], head, h["hex_across_flats_mm"]/math.sqrt(3)),
        ("head_washer", head, head+h["washer_thickness_mm"], h["washer_od_mm"]/2),
        ("nut_washer", nut-h["washer_thickness_mm"], nut, h["washer_od_mm"]/2),
        ("nut", nut, nut+h["nut_height_mm"], h["hex_across_flats_mm"]/math.sqrt(3)),
        ("wood_bore_cutter", -1., grip+1., (11.1125 if maximum else axis["bore_diameter_mm"])/2)]
    return [primitive(axis["id"], role, axis["point_xyz_mm"], axis["direction_xyz"], low, high, radius)
            for role, low, high, radius in rows]


def near(a, b, tolerance=1e-9):
    assert math.isfinite(a) and math.isfinite(b) and abs(a-b) <= tolerance, (a, b, tolerance)


def main():
    os.chdir(ROOT)
    assert {name: sha(TARGET / name) for name in HASHES} == HASHES
    spec, placement, result, verification = (read(TARGET / name) for name in ("inputs.json", "placement.json", "result.json", "verification.json"))
    assert len(result["source_sha256"]) == 13
    for path, digest in verification["source_sha256"].items():
        assert sha(ROOT / path) == digest
    current = read(ROOT / spec["current_geometry"])
    cache = read(ROOT / spec["current_cached_descriptors"])
    base_path = next(p for p in spec["sources"] if p.endswith("occupied-adjusted-base-v3.json"))
    base = read(ROOT / base_path)
    assert current["axes"] == base["axes"] and current["screw_axes"] == base["screw_axes"]
    axes = {a["id"]: a for a in current["axes"]}
    screws = {s["axis_id"]: s for s in current["screw_axes"]}
    assert len(axes) == 100 and len(screws) == 66
    assert axes == {s["axis_id"]: s["source_axis"] for s in cache["shafts"]}
    assert screws == {s["id"]: s["source_screw_descriptor"] for s in cache["hillman_rows"]}
    target_ids = {f"cleat_post_bolt_{side}_{number}" for side in ("left", "right") for number in (1, 2)}
    assert set(spec["target_axis_ids"]) == target_ids
    proposed = {a["id"]: a for a in placement["proposed_axes"]}
    assert set(proposed) == target_ids and len(placement["proposed_axes"]) == 4
    fixed = [a for a in current["axes"] if a["id"] not in target_ids]
    combined = []
    for row in current["axes"]:
        expected = copy.deepcopy(row)
        if row["id"] in target_ids:
            assert row["point_xyz_mm"][2] == 200
            expected["point_xyz_mm"][2] = 180.
            assert proposed[row["id"]] == expected
        combined.append(expected)
    for key, value in (("current_fixed_96_canonical_sha256", fixed), ("current_66_screws_canonical_sha256", current["screw_axes"]),
        ("current_100_axes_canonical_sha256", current["axes"]), ("proposed_100_axes_canonical_sha256", combined)):
        assert placement[key] == canonical(value)
    assert placement["geometry_adopted"] is False and placement["optional_2026_extra"] is False
    assert result["current_drilling_holds"] == sorted(target_ids)
    assert result["new_bore_wall_seat_tool_or_response_qualification"] is False
    assert result["release"] and not any(result["release"].values())
    assert result["placement"]["sha256"] == sha(TARGET / "placement.json")

    # Small independent exact-distance controls include degenerate points and
    # a skew pair; current primitives themselves all have positive axis lengths.
    def segment(start, end):
        return ("fixture", "axis", start, end, 0.)
    coupon = segment([0., 0., 0.], [10., 0., 0.])
    tests = [(segment([5., 3., 4.], [7., 3., 4.]), 5.),
        (segment([12., 3., 0.], [12., 7., 0.]), math.sqrt(13.)),
        (segment([5., 3., 4.], [5., -3., -4.]), 0.),
        (segment([5., 3., 4.], [5., 9., 12.]), 5.),
        (segment([5., -3., 1.], [5., 3., 1.]), 1.),
        (segment([15., 0., 0.], [15., 0., 0.]), 5.)]
    for other, expected in tests:
        near(distance(coupon, other), expected)
        near(distance(other, coupon), expected)

    screw_primitives = [primitive(s["axis_id"], role, s["origin_xyz_mm"], s["direction_xyz"], low, high, radius)
        for s in current["screw_axes"] for role, low, high, radius in (
            ("screw_body", 3., 63.5, 2.5), ("screw_head_containing_cylinder", 0., 3., 4.5))]
    fixed_primitives = [p for a in fixed for p in hardware(a)]
    comparisons, maximum_error, screens = 0, 0., []
    for screen_index, screen in enumerate(result["screens"]):
        lower = [axes[k] if screen_index == 0 else proposed[k] for k in sorted(target_ids)]
        nominal, maximum = ([p for a in lower for p in hardware(a, maximum=flag)] for flag in (False, True))
        for key, first, second, distinct in (
            ("nominal_bore_vs_66_current_screws", nominal, screw_primitives, False),
            ("maximum_bore_vs_66_current_screws", maximum, screw_primitives, False),
            ("maximum_bore_vs_96_current_fixed_bolts", maximum, fixed_primitives, False),
            ("maximum_bore_vs_other_lower_bolts", maximum, maximum, True)):
            observed, computed, positive, role_minimum, all_pairs = screen[key], math.inf, 0, {}, {}
            for a in first:
                for b in second:
                    if distinct and not a[0] < b[0]:
                        continue
                    axis_distance = distance(a, b)
                    gap = axis_distance-a[4]-b[4]
                    computed = min(computed, gap)
                    role_minimum[a[1]] = min(role_minimum.get(a[1], math.inf), gap)
                    positive += gap > 0
                    all_pairs[a[0], a[1], b[0], b[1]] = (axis_distance, gap)
            comparisons += len(all_pairs)
            assert len(all_pairs) == observed["count"] and positive == observed["positive_bound_count"]
            assert observed["all_bounds_positive"] == (positive == len(all_pairs))
            near(computed, observed["minimum"]["capsule_separation_lower_bound_mm"])
            maximum_error = max(maximum_error, abs(computed-observed["minimum"]["capsule_separation_lower_bound_mm"]))
            for witness in [observed["minimum"], *observed["minimum_by_lower_role"].values()]:
                value = all_pairs[witness["first"], witness["first_role"], witness["second"], witness["second_role"]]
                near(value[0], witness["finite_axis_distance_mm"])
                near(value[1], witness["capsule_separation_lower_bound_mm"])
            for role, value in role_minimum.items():
                near(value, observed["minimum_by_lower_role"][role]["capsule_separation_lower_bound_mm"])
            if key == "maximum_bore_vs_66_current_screws":
                near(computed, [-.05625, 3.94375][screen_index])
                screens.append({"id": screen["id"], "independent_maximum_bore_capsule_bound_mm": computed})
    assert comparisons == 40752

    # Reuse frozen verifier's independent general3D matrix, four method fixtures,
    # exact replay and7source/output controls in an exclusive temporary directory.
    with tempfile.TemporaryDirectory(prefix="source-controls-", dir=OWN.parent) as temp:
        process = subprocess.run([sys.executable, "-B", str(TARGET / "verify.py"), "--out", str(Path(temp) / "fresh")],
            cwd=ROOT, env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"}, capture_output=True, text=True, check=True)
        observed = json.loads(process.stdout)
        assert observed["passed"] is True and observed["controls"] == 7 and observed["general_segment_comparisons"] == 40752
    assert {name: sha(TARGET / name) for name in HASHES} == HASHES
    for path, digest in verification["source_sha256"].items():
        assert sha(ROOT / path) == digest
    return {"schema": "eoere_current_Z180_proposal_independent_correctness_review/v1", "findings": [],
        "target_source_sha256": HASHES, "review_helper_sha256": sha(OWN), "direct_source_pins_rehashed": 13,
        "independent_checks": {"current_geometry_cache_and_v3_axes": 100, "unchanged_current_screws": 66,
            "exact_proposed_Z_moves": 4, "unchanged_current_axes": 96, "canonical_list_bindings": 4,
            "scalar_segment_distance_and_reverse_controls": 12, "capsule_comparisons": comparisons,
            "maximum_saved_minimum_error_mm": maximum_error, "screens": screens},
        "reused_producer_known_answer_fixtures": 4, "reused_general3D_comparisons": 40752,
        "byte_replay_and_source_output_guard_controls": 7,
        "declared_current_geometry_recursive_pin_count_not_rehashed": len(current["source_sha256"]),
        "declared_cache_recursive_pin_count_not_rehashed": len(cache["source_sha256"]),
        "limits": ["Source-bound placement and finite nominal containing primitives only; no coordinate search, solid reconstruction/query, CAD, frame/K/native solve, browser or field consumption.",
            "Positive capsule bounds prove only nominal declared-primitive separation; negative values remain inconclusive.",
            "Allfour current drilling holds remain; Z180 remains unadopted. Bore walls/eight seats, current panel/service/angle intersections, screws, tools and mechanical resistance need their own disposition.",
            "13direct source pins rehashed; larger historical/current recursive closures are not independently admitted or rehashed here.",
            "Currentv3 moves,96other bolts and66screws retained; no old force/strength/clearance acceptance transferred.",
            "Frozen six files unchanged. Only exclusive helper/receipt retained; no shared edits, staging or publication."],
        "release": result["release"]}


if __name__ == "__main__":
    receipt = main()
    destination = OWN.with_name("receipt.json")
    with destination.open("x") as stream:
        json.dump(receipt, stream, indent=2, sort_keys=True, allow_nan=False)
        stream.write("\n")
    print(json.dumps({"passed": True, "findings": receipt["findings"], "receipt_sha256": sha(destination),
        "independent": receipt["independent_checks"]}))
