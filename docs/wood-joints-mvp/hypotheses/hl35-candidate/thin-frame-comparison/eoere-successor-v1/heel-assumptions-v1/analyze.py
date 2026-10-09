"""Replay the issued heel screen, then vary section geometry at fixed actions.

This consumes closed same-case steel reports. It reuses the pinned analytical
kernel and known answers; it never prepares or solves a candidate response.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import math
import platform
import sys
from pathlib import Path

import numpy as np
import scipy
from scipy.optimize import brentq

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[6]


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical_sha(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"),
                                     allow_nan=False).encode()).hexdigest()


def merge(pins, additional):
    for path, digest in additional.items():
        require(path not in pins or pins[path] == digest, "conflicting source: " + path)
        pins[path] = digest


def verify(pins):
    for path, digest in pins.items():
        require(sha(ROOT / path) == digest, "changed source: " + path)


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    value = importlib.util.module_from_spec(spec)
    sys.modules[name] = value
    spec.loader.exec_module(value)
    return value


def run():
    inputs = json.loads((HERE / "inputs.json").read_bytes())
    require(inputs["schema"] == "eoere_heel_assumption_sensitivity_input/v1", "input schema")
    own = {str(p.relative_to(ROOT)): sha(p)
           for p in (HERE / "analyze.py", HERE / "inputs.json", HERE / "sources.json")}
    direct = {r["path"]: r["sha256"] for r in inputs["files"].values()}
    merge(own, direct)
    verify(own)
    envelope = json.loads((ROOT / inputs["files"]["envelope"]["path"]).read_bytes())
    require(envelope["geometry_sha256"] == inputs["geometry_sha256"], "geometry mismatch")
    require(envelope["primary_live_joint_case_coverage_complete"], "incomplete closed coverage")
    require(not any(envelope["release"].values()), "unreleased development scope required")
    pins = dict(own)
    merge(pins, envelope["source_sha256"])
    kernel_path = ROOT / inputs["files"]["kernel"]["path"]
    # The issued test imports core by its original name. Do not copy its code.
    sys.path.insert(0, str(kernel_path.parent))
    import core
    require(Path(core.__file__).resolve() == kernel_path.resolve(), "wrong kernel import")
    known = module("heel_sensitivity_issued_known_answers", ROOT / inputs["files"]["tests"]["path"])
    net = module("heel_sensitivity_issued_net", ROOT / inputs["files"]["net_helper"]["path"])
    known_answers = known.known_answers(net)
    rows = []
    cases = []
    replay_error = 0.
    expected_exceeding = []
    for case, reference in inputs["cases"].items():
        path, digest = reference["path"], reference["sha256"]
        require(envelope["source_sha256"].get(path) == digest, "report is not in closed envelope")
        blob = (ROOT / path).read_bytes()
        require(hashlib.sha256(blob).hexdigest() == digest, "changed case report")
        merge(pins, {path: digest})
        report = json.loads(blob)
        merge(pins, report["source_sha256"])
        require(report["case_id"] == case, "case mismatch")
        require(report["field_source_geometry"]["report"]["sha256"] == inputs["geometry_sha256"],
                "case geometry mismatch")
        require(report["source_pins_before_after_unchanged"]
                and report["actual_independent_admission_consumed_before_arithmetic"], "unadmitted source")
        require(not any(report["release"].values()), "case release mismatch")
        require(report["census"]["angles"] == 22 and report["census"]["half_bands"] == 88,
                "case angle census")
        require(report["comparison"] == inputs["issued_comparison"], "issued comparison mismatch")
        cases.append(case)
        start = len(rows)
        for angle in report["angles"]:
            for band in angle["bands"]:
                require((band["half_band_width_mm"], band["source_physical_thickness_mm"],
                         band["root"]["station_mm"], band["root"]["side"])
                        == (44.45, 6.35, 0., "left"), "different root/section scenario")
                name = {"case_id": case, "body": angle["body"], "port_id": band["port_id"]}
                parameters = dict(width=band["half_band_width_mm"], fy=235., factor=1.67,
                                  weight_n=angle["own_physical_source_weight_n"],
                                  bound_radius_mm=angle["gravity_bounding_radius_mm"])
                replay = core.heel_component(band["root"], thickness=6., inside_radius=6., **parameters)
                for key, saved in band["heel_component"].items():
                    if isinstance(saved, float):
                        replay_error = max(replay_error, abs(replay[key] - saved))
                    else:
                        require(replay[key] == saved, "issued heel metadata mismatch")
                rows.append((name, band["root"], parameters))
                if replay["conditional_combined_yield_reference_ratio"] > 1:
                    expected_exceeding.append(name)
        require(len(rows) - start == 88, "duplicate/missing band")
    require(set(cases) == set(envelope["completed_primary_case_ids"]) and len(rows) == 528, "six-case census")
    require(len({tuple(n.values()) for n, _, _ in rows}) == 528, "duplicate owned band")
    require(replay_error < 1e-9, "issued heel replay changed")
    require(len(expected_exceeding) == 7, "closed exceedance census changed")
    verify(pins)

    def evaluate(thickness, radius):
        values = [(name, core.heel_component(root, thickness=thickness, inside_radius=radius, **p))
                  for name, root, p in rows]
        name, worst = max(values, key=lambda pair: pair[1]["bounding_source_gravity_equivalent_mpa"])
        by_case = []
        for case in sorted(cases):
            subset = [(n, v) for n, v in values if n["case_id"] == case]
            n, v = max(subset, key=lambda pair: pair[1]["conditional_combined_yield_reference_ratio"])
            by_case.append({"case_id": case, "worst": n,
                            "max_reference_ratio": v["conditional_combined_yield_reference_ratio"],
                            "exceedance_count": sum(v["conditional_combined_yield_reference_ratio"] > 1
                                                    for _, v in subset)})
        return {"thickness_scenario_mm": thickness, "inside_radius_scenario_mm": radius,
                "comparison_count": len(values), "worst": name, "comparison": worst,
                "exceedance_count": sum(v["conditional_combined_yield_reference_ratio"] > 1 for _, v in values),
                "by_case": by_case}

    scenarios = [evaluate(t, r) for t in inputs["thickness_scenarios_mm"]
                 for r in inputs["inside_radius_scenarios_mm"]]
    # Small known-answer model: unholed pure bending at every used section.
    # Check traction-free surfaces, zero net force and recovered applied moment.
    z, weights = np.polynomial.legendre.leggauss(64)
    fixture_errors = []
    for scenario in scenarios:
        t, ri = scenario["thickness_scenario_mm"], scenario["inside_radius_scenario_mm"]
        radii = ri + (z + 1) * t / 2
        radial, hoop = core.curved_pure_bending(ri, t, 44.45, 25000., radii)
        boundary, _ = core.curved_pure_bending(ri, t, 44.45, 25000., np.array([ri, ri + t]))
        force_error = 44.45 * t / 2 * float(weights @ hoop)
        moment_error = 44.45 * t / 2 * float(weights @ (hoop * radii)) - 25000.
        require(max(abs(boundary)) < 1e-7 and abs(force_error) < 1e-7 and abs(moment_error) < 1e-5,
                "pure-bending known answer failed")
        fixture_errors.append((float(max(abs(boundary))), abs(force_error), abs(moment_error)))
    t_boundary = brentq(lambda t: evaluate(t, 6.)["comparison"]["conditional_combined_yield_reference_ratio"] - 1,
                       *inputs["thickness_boundary_bracket_mm"], xtol=1e-9)
    boundaries = [{"fixed_inside_radius_mm": 6., "reference_equal_thickness_mm": t_boundary,
                   "witness": evaluate(t_boundary, 6.)["worst"]}]
    for t in inputs["thickness_scenarios_mm"]:
        r_boundary = brentq(lambda r: evaluate(t, r)["comparison"]["conditional_combined_yield_reference_ratio"] - 1,
                           *inputs["radius_boundary_bracket_mm"], xtol=1e-9)
        boundaries.append({"fixed_thickness_mm": t, "reference_equal_inside_radius_mm": r_boundary,
                           "witness": evaluate(t, r_boundary)["worst"]})
    worst_name = scenarios[inputs["inside_radius_scenarios_mm"].index(6.)]["worst"]
    name, root, parameters = next(r for r in rows if r[0] == worst_name)
    verify(pins)
    return {"schema": "eoere_heel_assumption_sensitivity_result/v1",
            "question": inputs["question"], "status": "COMPLETE_FIXED_ACTION_ASSUMPTION_SENSITIVITY_PHYSICAL_HEEL_UNQUALIFIED",
            "geometry_sha256": inputs["geometry_sha256"], "completed_case_ids": sorted(cases),
            "source_binding": {"direct_source_sha256": own, "inherited_and_direct_source_pin_count": len(pins),
                               "source_union_canonical_sha256": canonical_sha(pins),
                               "all_source_pins_verified_before_after": True},
            "execution": {"python": platform.python_version(), "numpy": np.__version__, "scipy": scipy.__version__,
                          "command": ".venv/bin/python -B " + str((HERE / "analyze.py").relative_to(ROOT)) + " --out NEW_OUTPUT.json",
                          "global_native_CAD_or_new_local_response_solve": False},
            "baseline_replay": {"comparison_count": len(rows), "max_numeric_error": replay_error,
                                "exceeded_owned_case_rows": expected_exceeding},
            "reference": {"conditional_Fy_mpa": 235., "factor": 1.67,
                          "comparison_mpa": 235. / 1.67, "factor_changed": False},
            "issued_known_answers_reused": known_answers,
            "additional_pure_bending_known_answers": {
                "section_count": len(fixture_errors),
                "max_boundary_radial_error_mpa": max(e[0] for e in fixture_errors),
                "max_net_force_error_n": max(e[1] for e in fixture_errors),
                "max_moment_error_nmm": max(e[2] for e in fixture_errors)},
            "scenarios": scenarios, "reference_equal_boundaries": boundaries,
            "governing_issued_root": {**name, "force_N_V1_V2_n": root["force_N_V1_V2_n"],
                                     "moment_T_M1_M2_nmm": root["moment_T_M1_M2_nmm"],
                                     "parameters": parameters},
            "limits": [
                "Every source root wrench, half-band assignment, neutral datum and source selfweight stays fixed.",
                "The sampled geometry ranges are questions, not delivered tolerances or guaranteed product minima.",
                "Reference-equal boundaries are mathematical sensitivities, not receiving, purchasing or cutting limits.",
                "The pure-bending fixture verifies the ideal annular sector, not the formed angle under combined end forces.",
                "Actual 3D heel/holes, transverse continuity, bend thinning, residual stress, stiffness and full timber-joint behavior remain unqualified.",
                "No new compatible demand field or adopted resistance criterion is supplied; the closed six-case result is unchanged."],
            "release": {"product_conformance": False, "actual_heel_capacity": False,
                        "physical_test_performed": False, "candidate_acceptance": False,
                        "fabrication": False, "climbing": False}}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True, help="New output; existing files are never overwritten")
    args = parser.parse_args()
    require(not args.out.exists(), "output already exists")
    result = run()
    with args.out.open("x") as stream:
        stream.write(json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n")
    print(json.dumps({"status": result["status"], "source_pins": result["source_binding"]["inherited_and_direct_source_pin_count"],
                      "baseline_comparisons": result["baseline_replay"]["comparison_count"],
                      "scenarios": len(result["scenarios"]), "output": str(args.out), "sha256": sha(args.out)}, indent=2))
