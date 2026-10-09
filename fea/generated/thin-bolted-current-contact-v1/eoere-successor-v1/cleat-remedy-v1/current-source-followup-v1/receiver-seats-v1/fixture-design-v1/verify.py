"""Independent decimal endpoint arithmetic and fresh-output guard controls."""
from __future__ import annotations

import argparse
import hashlib
import itertools
import json
import os
import runpy
import tempfile
from decimal import Decimal, localcontext
from pathlib import Path

OWN = Path(__file__).resolve()
HERE = OWN.parent
ROOT = next(p for p in OWN.parents if (p / "AGENTS.md").is_file())
EXPECTED = {
    "inputs.json": "b17a8f72f41ab2b8ce75ffaac15af075432a0ffe7111daead6597cb34eff86be",
    "design.py": "4c84897e42d4d32b1692bec8801a3c002b1c5684f984a907bde8e2cc73e4a3db",
    "result.json": "ec1c101da8f16f29cf0949c75086418e01e3b89268f55e27379fdb6a83a212f5",
    "result.svg": "60b5b105d42d35350bfe5a263f1c997974f7b3f9b1a27eea0317f88a84bd37c7",
}
D = Decimal


def require(ok, message):
    if not ok:
        raise ValueError(message)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def close(actual, exact, label):
    require(abs(D(str(actual))-exact) < D("1e-11"), label)


def decimal_checks(saved):
    b = saved["pointwise_error_and_reach_budget"]
    with localcontext() as context:
        context.prec = 55
        # Decimal Taylor series is independent of the producer's binary math.tan.
        pi = D("3.141592653589793238462643383279502884197169399375105820975")
        x = D("0.08")*pi/D(180)
        sin_term, cos_term = x, D(1)
        sine, cosine = sin_term, cos_term
        for n in range(1, 20):
            sin_term *= -x*x/D((2*n)*(2*n+1))
            cos_term *= -x*x/D((2*n-1)*(2*n))
            sine += sin_term
            cosine += cos_term
        tilt = D("111.825")*sine/cosine
        close(b["guide_tilt_max_mm"], tilt, "guide tilt independent Decimal")
        require(tilt < D("0.16"), "tilt allocation")
        endpoint_cases = []
        for entry, exit_ in itertools.product((D("-0.05"), D("0.05")), repeat=2):
            # Exit is the last constrained point in the sleeve. The entire
            # downstream line attains its maximum at a sleeve end or far end.
            far = exit_ + (exit_-entry)*D("83.05")/D("19.05")
            endpoint_cases.append({"entry_mm": str(entry), "exit_mm": str(exit_),
                                   "far_mm": str(far)})
        play = max(abs(D(r["far_mm"])) for r in endpoint_cases)
        close(b["insert_slop_max_mm"], play, "insert line endpoint Decimal")
        require(play < D("0.50"), "insert slop allocation")
        allocated = sum(D(s) for s in (".20", ".15", ".16", ".50", ".20", ".10", ".15"))
        close(b["allocated_sum_mm"], allocated, "sum of full-path terms")
        close(b["unallocated_reserve_mm"], D("1.50")-allocated, "reserve")
        # Nearest nominal screw body is at X=-1200.15, Z=192. Its Y segment
        # [-81.24375,-20.74375] contains Y=-80.45. The wood X segment contains
        # X=-1200.15, so its exact minimum finite-axis distance is 192-180=12.
        body_gap = D(12)-D("11.1125")/2-D("2.5")
        full_screw_gap = D(12)-D("11.1125")/2-D("4.7625")
        close(saved["nominal_primitive_clearance"]["cases"]["current_body"]["minimum"]["capsule_separation_lower_bound_mm"], body_gap, "body gap")
        close(b["minimum_declared_body_clearance_after_budget_mm"], body_gap-D("1.5"), "body residual")
        close(b["conditional_whole_screw9p525_clearance_after_budget_mm"], full_screw_gap-D("1.5"), "conditional whole-screw residual")
        reach = b["reach_requirements_mm"]
        expected_reach = {"nominal_wood_stack": "76.2", "nominal_guide_flange_cap_stack": "28.575",
                          "nominal_guide_to_point_breakout": "111.125", "nominal_free_projection_from_chuck": "113.125",
                          "worst_guide_to_point_breakout": "111.825", "worst_free_projection_from_chuck": "113.825",
                          "worst_wood_exposed_flute_lower_bound": "83.05", "full_chip_exit_path_reference": "111.825",
                          "increase_over_earlier_flush19p05_guide": "9.525"}
        for key, value in expected_reach.items():
            close(reach[key], D(value), "independent reach: " + key)
        for key, value in {"cleat_bottom": "38.7", "post_top": "57.3", "nearest_crossgrain_raw_edge": "42.85"}.items():
            close(b["geometric_tie_lower_bounds_mm"][key], D(value), "distance-only lower bound")
        clamps = saved["support_and_clamp_requirements"]
        for key, value in {"guide_clamps": "127", "cleat_clamp": "107.95", "post_clamp": "69.85"}.items():
            close(clamps["bare_opening_mm"][key], D(value), "bare clamp stack")
        lane_gap = (D("19.05")**2+D("29.55")**2).sqrt()-D("31.75")
        close(clamps["minimum_chuck_nose_to_clamp_lane_margin_mm"], lane_gap, "nearest lane rectangle corner")
    return {"independent_tilt_Decimal_mm": str(tilt), "independent_insert_endpoint_cases": endpoint_cases,
            "independent_insert_slop_mm": str(play), "nearest_nominal_axis_distance_mm": "12",
            "nearest_nominal_screw": "round_kicker_left_rim_2", "full_path_terms_and_reach_checked": True,
            "actual_tools_parts_or_tolerances_observed": False}


def guard_checks(function):
    outcomes = []

    def rejects(path, label):
        try:
            function(path)
        except ValueError:
            outcomes.append(label)
        else:
            raise ValueError("guard accepted: " + label)

    rejects(HERE / "result.json", "existing_result_rejected")
    rejects(HERE / "wrong.txt", "non_JSON_name_rejected")
    with tempfile.TemporaryDirectory(prefix="fixture-guard-", dir=HERE / "controls01") as temporary:
        temp = Path(temporary)
        rejects(temp / "outside.json", "nested_output_rejected")
        # Each control leaf belongs to this verifier and is removed after the
        # control. No source, saved output or other agent path is removed.
        stem = f"_fixture_verify_{os.getpid()}"
        json_leaf, svg_leaf = HERE / (stem+".json"), HERE / (stem+".svg")
        require(not os.path.lexists(json_leaf) and not os.path.lexists(svg_leaf), "fresh own control names")
        try:
            json_leaf.symlink_to(temp / "absent.json")
            rejects(json_leaf, "dangling_JSON_leaf_rejected")
            json_leaf.unlink()
            svg_leaf.symlink_to(temp / "absent.svg")
            rejects(json_leaf, "dangling_SVG_leaf_rejected")
            svg_leaf.unlink()
            svg_leaf.write_bytes(b"owned control")
            rejects(json_leaf, "existing_SVG_leaf_rejected")
            svg_leaf.unlink()
            alias = temp / "parent-alias"
            alias.symlink_to(HERE, target_is_directory=True)
            destination, image = function(alias / json_leaf.name)
            require(destination == json_leaf and image == svg_leaf, "canonical parent binding")
            alias.unlink()
            alias.symlink_to(temp, target_is_directory=True)
            require(destination.parent == HERE and image.parent == HERE, "retargeted alias redirected bound path")
            outcomes.append("parent_alias_retarget_inert_after_canonical_binding")
            json_leaf.write_bytes(b"owned late insertion")
            try:
                with destination.open("xb"):
                    raise ValueError("exclusive creation accepted existing late leaf")
            except FileExistsError:
                outcomes.append("late_canonical_leaf_rejected_by_exclusive_create")
        finally:
            for leaf in (json_leaf, svg_leaf):
                if os.path.lexists(leaf):
                    leaf.unlink()
    return outcomes


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    require(args.out.parent.resolve() == HERE and args.out.suffix == ".json", "fresh owned receipt required")
    destination = HERE / args.out.name
    require(not os.path.lexists(destination), "receipt leaf already exists")
    require(all(sha(HERE / name) == digest for name, digest in EXPECTED.items()), "frozen fixture packet differs")
    saved = json.loads((HERE / "result.json").read_bytes())
    require(all(sha(ROOT / path) == digest for path, digest in saved["source_sha256"].items()), "direct source pin differs")
    method = runpy.run_path(str(HERE / "design.py"))
    _, replay, _ = method["evaluate"]()
    without_drawing = {k: v for k, v in saved.items() if k != "drawing"}
    require(replay == without_drawing, "source-only result reproduction differs")
    checks = decimal_checks(saved)
    guards = guard_checks(method["output_paths"])
    require(all(v is False for v in saved["release"].values())
            and all(r["Actual"] == r["Disposition"] == "" for r in saved["actual_observations"]),
            "release or observation changed")
    require(all(sha(HERE / name) == digest for name, digest in EXPECTED.items()), "fixture packet changed during verification")
    require(all(sha(ROOT / path) == digest for path, digest in saved["source_sha256"].items()), "source changed during verification")
    result = {"schema": "eoere_Z180_fixture_source_arithmetic_and_output_verification/v1", "passed": True,
              "frozen_four_file_sha256": EXPECTED, "direct_source_pin_count": len(saved["source_sha256"]),
              "source_only_arithmetic_reproduction_exact": True, "independent_decimal_checks": checks,
              "output_guard_controls": guards, "before_after_frozen_packet_and_sources_unchanged": True,
              "verification_method_sha256": sha(OWN),
              "limits": ["This verifier checks source arithmetic and output protection. It does not independently repeat the native queries or all capsule pairs.",
                         "No tool, fixture, workholding, tolerance achievement, product fit, Z180 adoption, force transfer or complete-joint strength pass."],
              "release": saved["release"]}
    with destination.open("x") as stream:
        json.dump(result, stream, sort_keys=True, indent=2, allow_nan=False)
        stream.write("\n")
    print(json.dumps({"out": str(destination.relative_to(ROOT)), "sha256": sha(destination),
                      "bytes": destination.stat().st_size, "passed": True, "output_guard_controls": len(guards)}))


if __name__ == "__main__":
    main()
