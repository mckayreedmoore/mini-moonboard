"""Independent Decimal catalog-corner and full-path fixture checks."""
from __future__ import annotations

import argparse
import hashlib
import itertools
import json
import os
import runpy
from decimal import Decimal, localcontext
from pathlib import Path

OWN = Path(__file__).resolve()
HERE = OWN.parent
ROOT = next(p for p in OWN.parents if (p / "AGENTS.md").is_file())
D = Decimal
EXPECTED = {
    "inputs.json": "dd0df7d6b5eb30aab11184c4d4471333e545b270232333ba9577678c9155282d",
    "adapter.py": "f3831931d6c89330e07d76d1099cc4ecdf9a9a0c6e7be1b069413a7a1bc22a04",
    "result-v2.json": "e5e34e992365aedf30b56710efd9dcbb4d1a64e77e4ede29ff656d0479ff17de",
    "result-v2.svg": "4b52eaba8f98d5457b606061f5d51eace14bc222d38dc6bc0f873d91ff2e1b6b",
}


def require(ok, message):
    if not ok:
        raise ValueError(message)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def close(actual, exact, message):
    require(abs(D(str(actual))-exact) < D("1e-11"), message)


def decimal_corners(saved):
    with localcontext() as ctx:
        ctx.prec = 55
        L, F, G = D("19.05"), D("20.240625"), D("5.55625")
        t = D(".381")
        ranges = ((L-t, L+t), (F-t, F+t), (G-t, G+t), (D("-.2"), D(".2")),
                  (D("75.7"), D("76.7")), (D(0), D(".05")))
        paths, gaps, captures, slops = [], [], [], []
        count = 0
        for length, flange, head, jig_error, wood, capture_gap in itertools.product(*ranges):
            path = D("6.35")+D("19.05")+head+D("6.35")+jig_error+capture_gap+wood+D("6.35")
            gap = D("6.35")+D("19.05")+jig_error-length
            free_effective = D("6.35")+D("19.05")+jig_error-D(18)+wood+D("6.35")
            paths.append(path)
            gaps.append(gap)
            captures.append((flange-D("12.8"))/2-D(".15"))
            for start, end in itertools.product((D("-.05"), D(".05")), repeat=2):
                far = end+(end-start)*free_effective/D(18)
                slops.append(abs(far))
                count += 1
        require(count == 256, "catalog/height/wood/cap/line-endpoint corner census")
        reach = saved["reach_and_guidance"]
        close(reach["worst_cap_to_point_breakout_mm"], max(paths), "maximum full path")
        close(reach["worst_free_chuck_projection_mm"], max(paths)+2, "maximum free projection")
        close(reach["nominal_cap_to_point_breakout_mm"], D("119.85625"), "nominal path")
        close(reach["nominal_free_chuck_projection_mm"], D("121.85625"), "nominal projection")
        route = saved["chip_routes"]
        close(route["physical_bushing_exit_to_wood_gap_interval_mm"][0], min(gaps), "minimum physical exit gap")
        close(route["physical_bushing_exit_to_wood_gap_interval_mm"][1], max(gaps), "maximum physical exit gap")
        close(saved["cap_and_mounting"]["conditional_minimum_radial_capture_lip_mm"], min(captures), "minimum capture lip")
        close(route["gap_minimum_minus_general_reference_mm"], min(gaps)-D("11.1125")/2, "general gap comparison")
        # Independent Decimal Taylor sine/cosine versus producer binary tan.
        x = D(".08")*D("3.141592653589793238462643383279502884197169399375105820975")/180
        sine, cosine, a, b = x, D(1), x, D(1)
        for n in range(1, 20):
            a *= -x*x/D(2*n*(2*n+1))
            b *= -x*x/D((2*n-1)*2*n)
            sine += a
            cosine += b
        tilt = max(paths)*sine/cosine
        slop = max(slops)
        needed = D(".20")+D(".15")+D(".20")+D(".10")+D(".15")+tilt+slop
        comparisons = saved["generic_error_allowance_comparisons"]
        close(comparisons["guide_tilt"]["derived_bound_mm"], tilt, "full-path guide tilt")
        close(comparisons["insert_play"]["derived_bound_mm"], slop, "last constrained point slop")
        close(comparisons["relative_bore_screw"]["derived_bound_mm"], needed, "required relative bound")
        require(tilt > D(".16") and slop > D(".50") and needed > D("1.50"), "unmet generic allocations preserved")
        close(saved["minimum_body_capsule_separation_after_derived_bound_mm"], D("3.94375")-needed, "conditional body residual")
        close(saved["hypothetical_whole_screw9p525_separation_after_derived_bound_mm"], D("1.68125")-needed, "hypothetical full-screw residual")
        bit = saved["FISCH_nominal_comparison"]
        close(bit["NL_minus_full_cap_chip_path_reference_mm"], D(120)-max(paths), "retained full-path diagnostic deficit")
        close(bit["NL_minus_physical_lower_exit_reference_mm"], D(120)-max(gaps)-D("83.05"), "separate lower outlet comparison")
        close(bit["NL_minus_wood_exposure_reference_mm"], D(120)-D("83.05"), "wood exposure comparison")
        close(bit["GL_minus_worst_projection_mm"], D(150)-max(paths)-2, "available length not chuck engagement")
        for row in saved["configured_ID_cases"]:
            nominal = D(str(row["reference_ID_in"]))*D("25.4")
            for index, offset in enumerate((D(".00254"), D(".0127"))):
                close(row["catalog_ID_interval_mm"][index], nominal+offset, "ID interval")
                close(row["printed_nominal_diametral_gap_range_mm"][index], nominal+offset-D("10.32"), "printed diameter gap only")
            require(row["actual_bit_fit_established"] is False, "printed gap promoted to actual fit")
    return {"independent_decimal_endpoint_corners": count,
            "full_path_interval_mm": [str(min(paths)), str(max(paths))],
            "physical_gap_interval_mm": [str(min(gaps)), str(max(gaps))],
            "maximum_insert_line_slop_mm": str(slop), "maximum_guide_tilt_mm": str(tilt),
            "required_relative_bound_mm": str(needed), "all_three_generic_allocations_remain_unmet": True,
            "full_path_deficit_and_lower_outlet_comparisons_distinct": True,
            "printed_ID_gaps_do_not_establish_actual_fit": True}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    require(args.out.parent.resolve() == HERE and args.out.suffix == ".json", "owned canonical receipt required")
    destination = HERE / args.out.name
    require(not os.path.lexists(destination), "fresh receipt required")
    require(all(sha(HERE / n) == h for n, h in EXPECTED.items()), "frozen adapter files changed")
    saved = json.loads((HERE / "result-v2.json").read_bytes())
    require(all(sha(ROOT / n) == h for n, h in saved["source_sha256"].items()), "direct sources differ")
    method = runpy.run_path(str(HERE / "adapter.py"))
    require(method["calculate"]() == {k: v for k, v in saved.items() if k != "drawing"}, "exact source arithmetic replay")
    require(hashlib.sha256(method["drawing"](saved)).hexdigest() == saved["drawing"]["sha256"], "exact drawing replay")
    checks = decimal_corners(saved)
    # Reuse the previously reviewed guard controls with only a local directory
    # binding; its frozen source is already in this packet's source map.
    helper = runpy.run_path(str(HERE.parent / "verify.py"))["guard_checks"]
    helper.__globals__["HERE"] = HERE
    controls = HERE / "controls01"
    controls.mkdir(exist_ok=True)
    guards = helper(method["output_paths"])
    require(all(x is False for x in saved["release"].values())
            and all(x == "" for x in saved["actual_observations"].values()), "release or observations changed")
    require(all(sha(HERE / n) == h for n, h in EXPECTED.items()), "adapter packet changed during checks")
    require(all(sha(ROOT / n) == h for n, h in saved["source_sha256"].items()), "sources changed during checks")
    receipt = {"schema": "eoere_Z180_catalog_fixture_adapter_verification/v1", "passed": True,
        "meaning_of_pass": "Exact source arithmetic, declared conditional comparisons and output guards verified; not a fixture or machining acceptance.",
        "frozen_four_file_sha256": EXPECTED, "direct_source_pin_count": len(saved["source_sha256"]),
        "exact_scalar_and_drawing_reproduction": True, "independent_decimal_checks": checks,
        "output_guard_controls": guards, "sources_and_generic_six_files_unchanged_before_after": True,
        "verification_method_sha256": sha(OWN), "release": saved["release"],
        "limits": ["No independent source-diagram rerender, native topology query, product tolerance observation or physical fit.",
                   "The generic1.50-mm target and its tilt/play allocations remain unmet for this catalog adaptation under the retained conditions. No budget relaxation is adopted."]}
    with destination.open("x") as stream:
        json.dump(receipt, stream, sort_keys=True, indent=2, allow_nan=False)
        stream.write("\n")
    print(json.dumps({"out": str(destination.relative_to(ROOT)), "sha256": sha(destination),
                      "bytes": destination.stat().st_size, "independent_corners": 256,
                      "output_controls": len(guards), "generic_relative_error_target_met": False}))


if __name__ == "__main__":
    main()
