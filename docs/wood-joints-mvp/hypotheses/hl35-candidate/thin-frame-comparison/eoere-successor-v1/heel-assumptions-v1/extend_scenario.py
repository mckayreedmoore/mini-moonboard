"""Add one owner-requested fixed-action scenario without changing issued files."""
from __future__ import annotations

import argparse
import json
import platform
from pathlib import Path

import numpy as np
import scipy

import analyze as basis

HERE = Path(__file__).resolve().parent
ROOT = basis.ROOT


def run(input_path):
    inputs = json.loads(input_path.read_bytes())
    basis.require(inputs["schema"] == "eoere_heel_additional_nominal_scenario_input/v1", "input schema")
    direct = {r["path"]: r["sha256"] for r in inputs["files"].values()}
    basis.merge(direct, {str(input_path.relative_to(ROOT)): basis.sha(input_path),
                         str(Path(__file__).resolve().relative_to(ROOT)): basis.sha(Path(__file__))})
    basis.verify(direct)
    first = json.loads((ROOT / inputs["files"]["original_result"]["path"]).read_bytes())
    frozen = json.loads((ROOT / inputs["files"]["original_input"]["path"]).read_bytes())
    basis.require(first["baseline_replay"]["comparison_count"] == 528
                  and first["baseline_replay"]["max_numeric_error"] == 0., "original replay required")
    basis.require(not any(first["release"].values()), "original scope mismatch")
    pins = dict(first["source_binding"]["direct_source_sha256"])
    envelope = json.loads((ROOT / frozen["files"]["envelope"]["path"]).read_bytes())
    basis.require(envelope["geometry_sha256"] == first["geometry_sha256"], "geometry mismatch")
    basis.merge(pins, envelope["source_sha256"])
    reports = []
    for case, ref in frozen["cases"].items():
        basis.require(envelope["source_sha256"].get(ref["path"]) == ref["sha256"], "closed case binding")
        basis.merge(pins, {ref["path"]: ref["sha256"]})
        report = json.loads((ROOT / ref["path"]).read_bytes())
        basis.require(report["case_id"] == case, "case mismatch")
        basis.require(report["field_source_geometry"]["report"]["sha256"] == first["geometry_sha256"],
                      "case geometry mismatch")
        basis.require(report["actual_independent_admission_consumed_before_arithmetic"]
                      and report["source_pins_before_after_unchanged"]
                      and not any(report["release"].values()), "case admission/release mismatch")
        basis.merge(pins, report["source_sha256"])
        reports.append(report)
    binding = first["source_binding"]
    basis.require(len(pins) == binding["inherited_and_direct_source_pin_count"]
                  and basis.canonical_sha(pins) == binding["source_union_canonical_sha256"],
                  "original complete source union changed")
    basis.merge(pins, direct)
    basis.verify(pins)
    kernel_path = ROOT / frozen["files"]["kernel"]["path"]
    core = basis.module("heel_additional_scenario_pinned_kernel", kernel_path)
    t, radius = inputs["thickness_mm"], inputs["inside_radius_mm"]
    rows = []
    for report in reports:
        before = len(rows)
        for angle in report["angles"]:
            for band in angle["bands"]:
                basis.require(band["half_band_width_mm"] == 44.45
                              and band["source_physical_thickness_mm"] == 6.35, "different section")
                rows.append({"case_id": report["case_id"], "body": angle["body"], "port_id": band["port_id"],
                             "comparison": core.heel_component(band["root"], width=44.45,
                                 thickness=t, inside_radius=radius, fy=235., factor=1.67,
                                 weight_n=angle["own_physical_source_weight_n"],
                                 bound_radius_mm=angle["gravity_bounding_radius_mm"])})
        basis.require(len(rows) - before == 88, "case census")
    basis.require(len(rows) == 528 and len({(r["case_id"], r["body"], r["port_id"]) for r in rows}) == 528,
                  "six-case owned-row census")
    worst = max(rows, key=lambda r: r["comparison"]["conditional_combined_yield_reference_ratio"])
    by_case = []
    for case in first["completed_case_ids"]:
        owned = [r for r in rows if r["case_id"] == case]
        by_case.append({"case_id": case, "comparison_count": len(owned),
                        "worst": max(owned, key=lambda r: r["comparison"]["conditional_combined_yield_reference_ratio"]),
                        "exceedance_count": sum(r["comparison"]["conditional_combined_yield_reference_ratio"] > 1
                                                for r in owned)})
    z, weights = np.polynomial.legendre.leggauss(64)
    radii = radius + (z + 1) * t / 2
    _, hoop = core.curved_pure_bending(radius, t, 44.45, 25000., radii)
    radial_ends, _ = core.curved_pure_bending(radius, t, 44.45, 25000., np.array([radius, radius + t]))
    force_error = 44.45 * t / 2 * float(weights @ hoop)
    moment_error = 44.45 * t / 2 * float(weights @ (hoop * radii)) - 25000.
    basis.require(max(abs(radial_ends)) < 1e-7 and abs(force_error) < 1e-7 and abs(moment_error) < 1e-5,
                  "new section pure-bending known answer")
    basis.verify(pins)
    return {"schema": "eoere_heel_additional_nominal_scenario_result/v1",
            "status": "COMPLETE_OWNER_REQUESTED_NOMINAL_SCENARIO_ACTUAL_HEEL_UNQUALIFIED",
            "geometry_sha256": first["geometry_sha256"], "thickness_mm": t, "inside_radius_mm": radius,
            "conditional_yield_reference_mpa": 235. / 1.67,
            "comparison_count": len(rows), "worst": worst, "by_case": by_case,
            "exceedance_count": sum(r["comparison"]["conditional_combined_yield_reference_ratio"] > 1 for r in rows),
            "reference_margin_percent": 100 * (1 - worst["comparison"]["conditional_combined_yield_reference_ratio"]),
            "source_binding": {"direct_source_sha256": direct, "verified_complete_source_pin_count": len(pins),
                               "source_union_canonical_sha256": basis.canonical_sha(pins),
                               "all_source_pins_before_after_unchanged": True},
            "new_section_known_answer": {"prescribed_pure_bending_moment_nmm": 25000.,
                                         "net_force_error_n": force_error, "moment_error_nmm": moment_error,
                                         "max_boundary_radial_error_mpa": float(max(abs(radial_ends)))},
            "execution": {"python": platform.python_version(), "numpy": np.__version__, "scipy": scipy.__version__,
                          "command": ".venv/bin/python -B " + str(Path(__file__).resolve().relative_to(ROOT))
                          + " --input " + str(input_path.relative_to(ROOT)) + " --out NEW_OUTPUT.json",
                          "global_native_CAD_or_new_local_response_solve": False},
            "limits": ["Original reports, baseline scenario, source neutral datum and root wrenches are unchanged.",
                       "6.35mm is the owner-requested catalog nominal; inside radius equal to thickness is an assumption.",
                       "Zero screen exceedances do not supply manufacturing tolerance, a strength reserve or an actual 3D heel stress bound.",
                       "Actual material, metal thickness, radius, thinning, hole/heel datums, transverse continuity and complete-joint resistance remain unverified."],
            "release": {"minimum_dimensions_verified": False, "actual_heel_capacity": False,
                        "candidate_acceptance": False, "fabrication": False, "climbing": False}}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    basis.require(not args.out.exists(), "output already exists")
    result = run(args.input.resolve())
    with args.out.open("x") as stream:
        stream.write(json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n")
    print(json.dumps({"status": result["status"], "reference_ratio": result["worst"]["comparison"]["conditional_combined_yield_reference_ratio"],
                      "reference_margin_percent": result["reference_margin_percent"], "comparisons": result["comparison_count"],
                      "exceedances": result["exceedance_count"], "verified_source_pins": result["source_binding"]["verified_complete_source_pin_count"],
                      "output": str(args.out), "sha256": basis.sha(args.out)}, indent=2))
