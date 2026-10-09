"""Check saved summary projections against independently reviewed actual outputs.

Only direct frozen files and process logs are read. Reuse the completed coarse
and rich reviews for their source closures and scalar work; do not replay any
producer, summary generator, reducer, admission or giant source-closure scan.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.util
import json
import sys
from pathlib import Path

OWN = Path(__file__).resolve()
UTILITY = OWN.with_name("review.py")
UTILITY_SHA = "64dbd260245bbc6d349d0866cc882e7b811d0a97436c4caffebc9912fdb575a3"
if hashlib.sha256(UTILITY.read_bytes()).hexdigest() != UTILITY_SHA:
    raise ValueError("exact independent review utilities required")
spec = importlib.util.spec_from_file_location("independent_saved_summary_utilities", UTILITY)
u = importlib.util.module_from_spec(spec)
spec.loader.exec_module(u)
ROOT, MECH = u.ROOT, u.MECH
PACKET = OWN.parent.parent
FIXED = {
    PACKET / "summarize.py": "0547b984f150bb9bbd4dbe25b50825a12c047de70bcb1d86a267abd58a935735",
    PACKET / "summary-inputs.json": "ce2ebabc3d3311d77ae8aa00bc063fd7d6e380467fd5d85c7af9b898f636d9fb",
    PACKET / "summary.json": "0bd6001b81b2823bbc4e36145614f5b9cc857d47d59eec2b93a2d5e29bbdfd9f",
    PACKET / "verification.json": "0bcc638dbe220e07423f4898675b7c5c583ff6ce84d3a5e80d1ecc7f291543c6",
    OWN.with_name("receipt-six-cases.json"): "5973bb5c128a76fde59c3a6183cfd06ec3d42460f6be9921e2e7e1be80e0fec9",
    OWN.with_name("rich_review.py"): "f2741b10d15d4a3cb720b017ea13fc9bdbdf5adb4dd9f9b16e8a73e42a6ff352",
    OWN.with_name("receipt-rich-six-cases.json"): "71097dfa7d76449e5e46fc0307b53392c6fbd04645898b778fe104d1b20b832e",
    UTILITY: UTILITY_SHA,
}


class Checks:
    def __init__(self):
        self.count = 0

    def equal(self, actual, expected, label):
        self.count += 1
        u.require(actual == expected, "saved summary differs: " + label)

    def projection(self, saved, original, label):
        u.require(isinstance(saved, dict) and isinstance(original, dict), "saved dictionary projection required")
        for key, value in saved.items():
            u.require(key in original, "summary projection invented key: " + label + "/" + key)
            self.equal(value, original[key], label + "/" + key)


def coarse_findings(c, saved, original):
    r = original["component_reductions"]
    c.equal(saved["complete24_joint_resistances"], None, "coarse/null24")
    c.equal(saved["source_limits"], original["limits"], "coarse/limits")
    for witness, metric in (("fully_braced_normal", "fully_braced_component_normal_interaction"),
                            ("sufficient_shear_torsion", "equal_longitudinal_shear_moduli_rectangle_component_upper_bound_ratio")):
        values = [(m["member"], m["witnesses"][witness]) for m in r["fresh_gross_member_diagnostics"]]
        source = max(values, key=lambda p: p[1]["gross_CD1_comparison"][metric])
        item = saved["gross_raw_members"][metric]

        def verify(row, pair, selected_metric=metric):
            c.equal(row["member"], pair[0], "gross/member")
            c.equal(row["value"], pair[1]["gross_CD1_comparison"][selected_metric], "gross/reference")
            c.projection({k: v for k, v in row.items() if k not in ("member", "value")}, pair[1], "gross/witness")

        verify(item["worst"], source)
        exceed = [p for p in values if p[1]["gross_CD1_comparison"][metric] > 1]
        c.equal([p["member"] for p in item["saved_witness_exceedances"]], [p[0] for p in exceed], "gross/exceedances")
        for row, pair in zip(item["saved_witness_exceedances"], exceed, strict=True):
            verify(row, pair)
    panels = r["six_panel_reductions"]["panel_diagnostics"]
    p = saved["panels"]
    c.equal([x["panel"] for x in p["per_panel"]], [x["panel"] for x in panels], "panels/census")
    exceed = []
    for row, raw in zip(p["per_panel"], panels, strict=True):
        c.equal(row["section_components"], raw["resolved_section_diagnostics"]["components"], "panel/components")
        c.projection(row["deformation"], raw["deformation_diagnostics"], "panel/deformation")
        exceed.extend({"panel": raw["panel"], "component": k, **v} for k, v in row["section_components"].items() if v["sampled_ratio_CD1"] > 1)
    c.equal(p["sampled_section_exceedances_CD1"], exceed, "panel/exceedances")
    screws = r["simultaneous_Hillman_actions_and_generic_references"]
    s = saved["generic_screw_references"]
    c.equal(s["all66_own_axes"], len(screws) == 66, "screws/census")
    c.equal(s["generic_CD1_head_exceedance_axis_ids"], [x["axis_id"] for x in screws if x["generic_head_ratio_CD1"] > 1], "screws/exceedances")
    for metric in ("generic_head_ratio_CD1", "generic_withdrawal_required_effective_thread_mm_CD1", "same_axis_simultaneous_lateral_n"):
        c.projection(s[metric], max(screws, key=lambda x: x[metric]), "screws/worst-" + metric)


def steel_witness(c, saved, raw, label):
    metric = saved["saved_metric"]
    source = raw.get("comparison", raw)
    for key, value in saved.items():
        if key == "saved_metric":
            continue
        c.equal(value, raw[key] if key in ("body", "flange", "port_id", "axis_id") else source[key], label + "/" + key)
    u.require(metric in source, "selected steel reference metric absent")


def washer_witness(c, saved, raw):
    if raw is None:
        c.equal(saved, None, "washer/null-witness")
        return
    c.projection({k: v for k, v in saved.items() if k != "scenario"}, raw, "washer/witness")
    c.projection(saved["scenario"], raw["scenario"], "washer/scenario")


def rich_findings(c, saved, original):
    r = original["findings"]
    c.equal(saved["missing_current_inputs"], r["missing_current_inputs"], "rich/missing-inputs")
    c.equal(len(saved["steel_scenarios"]), len(r["rich_steel"]), "steel/scenario-count")
    for scenario, raw in zip(saved["steel_scenarios"], r["rich_steel"], strict=True):
        c.equal(scenario["comparison"], raw["comparison"], "steel/separate-scenario")
        c.equal([scenario["fixed_actions_only"], scenario["product_strength"]], [True, None], "steel/reference-boundary")
        c.equal(set(scenario["summary"]), set(raw["summary"]), "steel/all-categories")
        for key, category in scenario["summary"].items():
            actual = raw["summary"][key]
            for name in ("comparison_count", "exceedance_count"):
                c.equal(category[name], actual[name], "steel/" + key + "/" + name)
            steel_witness(c, category["worst"], actual["worst"], "steel/" + key + "/worst")
            c.equal(len(category["exceedances"]), len(actual["exceedances"]), "steel/exceedance-count")
            for row, source in zip(category["exceedances"], actual["exceedances"], strict=True):
                steel_witness(c, row, source, "steel/" + key + "/exceedance")
    timber, t = r["timber"], saved["timber"]
    c.equal(t["all24_complete_joint_resistances"], None, "timber/null24")
    c.equal(t["limits"], timber["unsupported_mechanisms"], "timber/limits")
    mixed = [x for x in timber["shaft_components"] if x["component"] is None]
    c.equal(len(t["mixed_stacks"]), len(mixed), "timber/mixed-count")
    for row, raw in zip(t["mixed_stacks"], mixed, strict=True):
        c.projection(row, raw, "timber/mixed-stack")
    ts = t["summary"]
    for key, value in timber["summary"].items():
        if key != "worst_components":
            c.equal(ts[key], value, "timber/summary-" + key)
    c.equal(ts["worst_component"], timber["summary"]["worst_components"][0], "timber/worst")
    for name, test in (("unadjusted_exceedance_axis_ids", lambda v: v["exceeds_unadjusted_component_reference"]),
                       ("Cdelta0p5_Cg1_CD1_sensitivity_exceedance_axis_ids", lambda v: v["Cdelta0p5_Cg1_CD1_sensitivity_ratio"] > 1)):
        c.equal(ts[name], [x["axis_id"] for x in timber["shaft_components"] if x["component"] is not None and test(x["component"])], "timber/" + name)
    shaft, s = r["shaft"], saved["shaft"]
    c.equal(s["worst"], max(shaft["all100"], key=lambda x: x["governing"]["specified_material_first_yield_index"]), "shaft/worst")
    c.equal(s["first_yield_reference_exceedances"], shaft["first_yield_reference_exceedances"], "shaft/exceedances")
    c.equal(s["complete_bolt_resistance"], None, "shaft/null-complete")
    washer, w = r["washers"], saved["washers"]
    for key in ("census", "exceeded_reference_diagnostics", "limits"):
        c.equal(w[key], washer[key], "washer/" + key)
    c.equal(w["nominal_seat_geometry"], washer["reviewed_nominal_seat_geometry"], "washer/seat-carry")
    c.equal(w["geometry_composition_canonical_sha256"], u.canonical(washer["geometry_composition"]), "washer/geometry-composition")
    c.equal(set(w["worsts"]), set(washer["worsts"]), "washer/all-worst-categories")
    for key, value in w["worsts"].items():
        if key == "by_diameter":
            c.equal(set(value), set(washer["worsts"][key]), "washer/all-diameters")
            for diameter, row in value.items():
                washer_witness(c, row, washer["worsts"][key][diameter])
        else:
            washer_witness(c, value, washer["worsts"][key])


def check_summary(summary, inputs, verification, actual, known, pins):
    c = Checks()
    c.equal(summary["schema"], "eoere_exact_current_six_case_component_summary/v1", "schema")
    c.equal(inputs["schema"], "eoere_exact_six_case_component_summary_inputs/v1", "inputs/schema")
    c.equal(verification["schema"], "eoere_current_six_case_component_reporting_verification/v1", "verification/schema")
    for rows in (summary["cases"], inputs["cases"], verification["actual_outputs"]):
        c.equal(tuple(x["case_id"] for x in rows), u.CASES, "six-ordered-cases")
    c.equal(summary["release"], u.RELEASE, "release")
    c.equal(verification["release"], u.RELEASE, "verification/release")
    c.equal(summary["complete_joint_resistance"], None, "complete-resistance-null")
    c.equal(summary["execution"], {"saved_JSON_and_source_bytes_only": True, "reducers_CAD_K_global_native_or_browser_called": False}, "execution-boundary")
    c.equal(summary["current_geometry"], inputs["geometry"], "current-geometry")
    c.equal(summary["source_sha256"], inputs["source_sha256"], "summary-sources")
    c.equal(summary["source_manifest"], {"path": u.relative(PACKET / "summary-inputs.json"), "sha256": FIXED[PACKET / "summary-inputs.json"]}, "source-manifest")
    union = dict(inputs["source_sha256"])
    u.merge(union, {summary["source_manifest"]["path"]: summary["source_manifest"]["sha256"]})
    total_bytes = 0
    for row, binding, evidence in zip(summary["cases"], inputs["cases"], verification["actual_outputs"], strict=True):
        case = row["case_id"]
        for name in ("field", "admission"):
            ref = binding[name]
            c.equal(row[name], ref, case + "/" + name)
            c.equal(evidence[name], ref, case + "/verification-" + name)
            c.equal(ref["sha256"], known[ref["path"]], case + "/reviewed-" + name)
            u.merge(union, {ref["path"]: ref["sha256"]})
        for kind, checker in (("coarse", coarse_findings), ("rich", rich_findings)):
            report = actual[case][kind]
            output = row[kind]
            c.equal([row[k] for k in ("state_id", "case_id", "accessory_placement")], [report[k] for k in ("state_id", "case_id", "accessory_placement")], case + "/identity")
            c.equal(output["bindings"], binding[kind], case + "/bindings")
            ref = binding[kind]["result"]
            c.equal(ref["sha256"], known[ref["path"]], case + "/reviewed-result")
            c.equal(output["source_map_count"], len(report["source_sha256"]), case + "/source-count")
            c.equal(output["source_map_canonical_sha256"], u.canonical(report["source_sha256"]), case + "/source-map")
            process_ref = binding[kind]["process"]
            process = u.read(ROOT / process_ref["path"], process_ref["sha256"])
            c.equal(process["exit_code"], 0, case + "/process-exit")
            c.equal(output["process_elapsed_seconds"], process["elapsed_seconds"], case + "/elapsed")
            c.equal(evidence[kind]["result"], ref, case + "/verification-result")
            c.equal(evidence[kind]["process"], process_ref, case + "/verification-process")
            c.equal(evidence[kind]["stderr_bytes"], (ROOT / binding[kind]["stderr"]["path"]).stat().st_size, case + "/stderr-size")
            c.equal(evidence[kind]["stderr_bytes"], 0, case + "/empty-stderr")
            u.merge(pins, {x["path"]: x["sha256"] for x in binding[kind].values()})
            u.merge(union, report["source_sha256"])
            u.merge(union, {x["path"]: x["sha256"] for x in binding[kind].values()})
            total_bytes += (ROOT / ref["path"]).stat().st_size
            checker(c, output["findings"], report)
    c.equal(summary["verified_source_union"], {"count": len(union), "canonical_sha256": u.canonical(union)}, "derived-source-union-no-rescan")
    c.equal(verification["verified_source_union"], summary["verified_source_union"], "verification/source-union")
    c.equal(verification["total_raw_twelve_result_bytes"], total_bytes, "raw-result-bytes")
    return c.count


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    u.require(args.out is None or args.out.resolve().parent == OWN.parent and not args.out.exists(), "fresh owned receipt required")
    pins = {u.relative(p): digest for p, digest in FIXED.items()}
    pins[u.relative(OWN)] = u.sha(OWN)
    u.verify(pins)
    coarse_review = u.read(OWN.with_name("receipt-six-cases.json"), FIXED[OWN.with_name("receipt-six-cases.json")])
    rich_review = u.read(OWN.with_name("receipt-rich-six-cases.json"), FIXED[OWN.with_name("receipt-rich-six-cases.json")])
    u.require(coarse_review["findings"] == rich_review["findings"] == [] and len(rich_review["cases"]) == 6, "completed six-case reviews required")
    known = dict(coarse_review["targets_and_direct_sources_sha256"])
    u.merge(known, rich_review["targets_and_direct_sources_sha256"])
    summary, inputs, verification = [u.read(PACKET / name, FIXED[PACKET / name]) for name in ("summary.json", "summary-inputs.json", "verification.json")]
    actual = {}
    for binding in inputs["cases"]:
        actual[binding["case_id"]] = {}
        for kind in ("coarse", "rich"):
            ref = binding[kind]["result"]
            u.require(known[ref["path"]] == ref["sha256"], "exact independently reviewed result required")
            actual[binding["case_id"]][kind] = u.read(ROOT / ref["path"], ref["sha256"])
    checks = check_summary(summary, inputs, verification, actual, known, pins)
    controls = []
    for label, mutate in (
        ("changed_case_identity", lambda s: s["cases"][0].update(state_id="wrong")),
        ("omitted_heel_exceedance", lambda s: s["cases"][0]["rich"]["findings"]["steel_scenarios"][0]["summary"]["radius_conditioned_heel_component_with_gravity"].update(exceedances=[])),
        ("omitted_mixed_stack", lambda s: s["cases"][0]["rich"]["findings"]["timber"]["mixed_stacks"].pop()),
        ("changed_gross_reference", lambda s: s["cases"][0]["coarse"]["findings"]["gross_raw_members"]["fully_braced_component_normal_interaction"]["worst"].update(value=0)),
    ):
        altered = copy.deepcopy(summary)
        mutate(altered)
        try:
            check_summary(altered, inputs, verification, actual, known, {})
        except (ValueError, KeyError):
            controls.append(label)
        else:
            raise ValueError("altered summary accepted: " + label)
    u.verify(pins)
    receipt = {
        "schema": "eoere_current_six_case_saved_summary_independent_review/v1",
        "status": "CLEAN_FROZEN_SUMMARY_MATCHES_TWELVE_INDEPENDENTLY_REVIEWED_ACTUAL_OUTPUTS", "findings": [],
        "targets_and_direct_files_sha256": dict(sorted(pins.items())), "saved_summary_comparisons": checks,
        "negative_controls_rejected": controls, "case_ids": list(u.CASES),
        "source_union_identity_derived_without_source_file_rescan": summary["verified_source_union"],
        "limits": ["Checks all six case pairs, process/log bindings, per-case gross/panel/screw/steel/timber/shaft/washer witnesses, all saved exceedance selections and retained nulls against the exact actual coarse/rich outputs.",
                   "Relies on the separate frozen six-case coarse and rich reviews for source-closure and scalar checks. Does not execute or import the summary generator, component methods, admissions, CAD, native or global models; no giant source closure is rescanned.",
                   "Confirms saved conditional reporting only. Reference exceedances and unknown complete resistance remain; actual product, geometry, tool and physical acceptance are not established."],
        "execution": {"saved_direct_JSON_and_source_files_only": True, "genuine_summary_generator_or_reducer_called": False, "large_source_union_rescanned": False, "shared_writes_staging_commits": False},
        "complete_joint_resistance": None, "release": dict(u.RELEASE), "command": list(sys.orig_argv), "python": sys.version,
    }
    payload = (json.dumps(receipt, indent=2, sort_keys=True, allow_nan=False)+"\n").encode()
    if args.out:
        with args.out.open("xb") as stream:
            stream.write(payload)
    u.verify(pins)
    print(json.dumps({"status": receipt["status"], "comparisons": checks, "negative_controls": len(controls), "direct_files": len(pins),
                      "helper_sha256": pins[u.relative(OWN)], "receipt_sha256": hashlib.sha256(payload).hexdigest() if args.out else None,
                      "receipt": u.relative(args.out) if args.out else None}, sort_keys=True))


if __name__ == "__main__":
    main()
