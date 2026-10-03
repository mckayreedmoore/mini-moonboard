"""N11 full-length member sensitivity from authenticated saved signed cuts.

Import is inert. prepare(output) authenticates and joins metadata only.
Only the parent calls build(output), a standard-library scalar calculation.
No producer pipeline, frame/native/CAD solve, new load or brace design runs.
"""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
import math
from collections import Counter
from pathlib import Path
from types import SimpleNamespace

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
PACKET = HERE.parent
RAW = HERE / "rawlocal/member-restraint-completion"
SAVED = HERE / "rawlocal/knee-bridge-members/attempt01"
CHECKS, RECEIPT, TRACES = (SAVED / name for name in
                         ("checks.json", "receipt.json", "same-cut-states.jsonl"))
GEOMETRY = PACKET / "member-screen-attempt02/knee-bridge-gravity01/geometry.json"
CLOSURE = HERE / "all-joint-splitting/closure.py"
LOADER = HERE / "panel-reference-completion.py"
STABILITY = PACKET / "member_stability.py"
TIMBER = ROOT / "fea/reinforced_timber_resistance.py"
MATERIALS = PACKET.parent / "hardware-material-specification-2026-09-30/material-inputs.json"
CH3 = HERE / "rawlocal/profile-method-completion/sources/nds2024-chapter3.pdf"
CH4 = HERE / "rawlocal/profile-method-completion/sources/nds2024-chapter4.pdf"
CH2 = PACKET.parent / "upper-block-strength-2026-10-01/source-cache/chapter2-2024-awc.pdf"
APPENDIX = CH2.with_name("appendix-2024-awc-20260911.pdf")
CASES = ("a12-rear", "a12-forward", "a12-left", "k12-right", "k12-rear", "a1-rear")
SCENARIOS = {"cd1": 1.0, "cd1_25": 1.25}
EXCLUDED = ("knee_outer_left_spine", "knee_outer_right_spine")
PINS = {
    CHECKS: "0d623eb62605ddac9aa5111e2469a1c63f4857e356fe607741fc425d5ea59e65",
    RECEIPT: "fa4d5f5568d53c0e4e62a74d31a814738b39a78951a4c27ae6e4c141ef5be794",
    TRACES: "b516e2f7e69699d5767d90563e697ca6b91f6fce1b32ecd13e0b447b1a80d7e7",
    GEOMETRY: "c61139087fac34e8094f2336f15dd6de5c0112d26d37b9535526f47332f453af",
    CLOSURE: "095cc122b4f0292fecd108446c24744a2671a703d156527afcd243eb8de9035d",
    LOADER: "1943198db40ed6729f6c93c3a1196e1642d3a3843fb2bbf5e826aa6b35a116b1",
    STABILITY: "eb70dbe72c1ed3b9518739915193083fd6a07ebd064ba17d0c07f299f6786b72",
    TIMBER: "d4e8302d39beb9f53c70fa264762c59c231f6e6b086cb866906ca39eeab9cfbc",
    MATERIALS: "0f33ad8fd517673a4ebbed36c4a30c1cfe07e0d8163165bdc804af91d958fc5a",
    CH3: "205df74e16f632dfe78211e99bfa5dfa8b9f8dd316e9c5fa1316493f795ec644",
    CH4: "52feedd07d3b672f0dd2666903cf8b481687d3da975cd3fccac545f66dfeb9ec",
    CH2: "6bb62f3560ab5bcdbed297cd03bba560f20882a638ee591c0c97013f7c075100",
    APPENDIX: "1fa2bcf52803b1bbed8ea30cf13551dd5f76c90bf110ac475b401f81d116ec31",
}
FLAGS = {
    "N11_accepted": False, "complete_member_acceptance": False,
    "whole_frame_stability_or_motion_qualified": False,
    "actual_endpoint_or_interior_restraints_qualified": False,
    "panel_screw_bracing_credited": False, "new_restraints_selected": False,
    "proposal_adopted": False, "historical_acceptance_transferred": False,
    "formal_criteria_updated": False, "physical_release": False,
    "fabrication_release": False, "geometry_hardware_load_or_stiffness_changed": False,
    "original_producer_pipelines_executed": False,
    "frame_native_CAD_or_coupon_run": False, "software_tests_or_review_loop_run": False,
}
LIMITS = [
    "K=1 full finished length in both column directions is a declared no-sway, end-translation-restraint sensitivity, not measured or qualified support.",
    "Beam Table 3.3.3 unspecified-loading length also assumes adequate lateral restraint and rotation prevention about grain at both ends. No interior or panel-screw brace is credited.",
    "Inclination to global axes is not oblique grain. A longitudinal material/section-axis mismatch refuses the parallel-grain formulas.",
    "The two rear-leg recess/taper profiles receive no new prismatic CL/CP comparison; the old reduced uniform rectangle is not transferred as taper qualification.",
    "The retained straight-member gross stiffness approximation excludes bores, passages and clipped end load-transfer fields. Saved unsupported local traces remain unsupported.",
    "Column le/d>50 and beam RB>50 are NDS formula-domain exclusions, not physical failures; unsupported ratios are never passes.",
    "CD=1 and existing CD=1.25 seven-day full-peak sensitivity use the same six saved actions. Emin and Euler references do not receive duration credit. Fresh permanent CD=.9 remains separate.",
    "Biaxial compression reuses 3.9-3/3.9-4. Tension uses the preserved conservative no-relief biaxial extension, identified separately from an exact uniaxial NDS equation.",
    "No local opening, shear/torsion, brace stiffness/capacity, receiver anchorage, unique pose or nonlinear frame stability is inferred from these normal/stability references.",
    "The reviewed 104 global axes remain separate from the unadopted 108 proposal; four internal spine ties supply no new global restraints here.",
    "No-slip floor support and saved representative motion remain separate source bounds. No friction, anchor, hardware addition or blanket three-dimensional member model is prescribed.",
]


def require(condition, message):
    if not condition:
        raise ValueError("STOP: " + message)


def sha(path):
    with Path(path).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def read(path):
    return json.loads(Path(path).read_text())


def pure(path, names, namespace):
    """Reuse the frozen inert AST loader; execute selected definitions only."""
    require(sha(LOADER) == PINS[LOADER], "AST loader changed")
    tree = ast.parse(LOADER.read_text(), filename=str(LOADER))
    nodes = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "definitions"]
    require(len(nodes) == 1 and not nodes[0].decorator_list, "AST loader definition differs")
    scope = {"ast": ast, "SimpleNamespace": SimpleNamespace, "require": require}
    module = ast.fix_missing_locations(ast.Module(body=nodes, type_ignores=[]))
    exec(compile(module, str(LOADER), "exec"), scope)  # noqa: S102
    return scope["definitions"](path, names, namespace)


def sources():
    require(sha(CLOSURE) == PINS[CLOSURE], "authentication helper changed")
    api = pure(CLOSURE, ("read", "key", "bind", "authenticate", "receipt_sources"),
               {"Path": Path, "json": json, "ROOT": ROOT, "require": require, "sha": sha})
    pins = {**PINS, Path(__file__).resolve(): sha(__file__)}
    api.authenticate(pins)
    api.receipt_sources(pins, RECEIPT)
    receipt, saved, geometry = map(read, (RECEIPT, CHECKS, GEOMETRY))
    for relative, digest in receipt["classifier_source_sha256"].items():
        api.bind(pins, ROOT / relative, digest)
    require(all(path.resolve().is_relative_to(ROOT) for path in pins), "source leaves repository")
    api.authenticate(pins)
    require(saved["source_sha256"] == receipt["source_sha256"]
            and saved["classifier_source_sha256"] == receipt["classifier_source_sha256"], "source closure differs")
    require(saved["case_ids"] == list(CASES) and saved["counts"] == receipt["counts"]
            and saved["counts"]["members"] == 42 and saved["counts"]["signed_cut_traces"] == 53784,
            "saved coverage differs")
    require(saved["source_comparison_sha256"] == "c3a8ff024fb494032d947aedfd6f00cda8698587b8751b2cec66e4b3af243729"
            and saved["source_response_sha256"] == "62bd4116cfb577a0846f4de0d43fbeec6bb704bac7feee530ee673ded1820f90"
            and saved["source_gravity_assessment_sha256"] == "ce69ba58e3c6265d31ab0dfdec1ffac4c019b93fc1106c8f9677ed9b5b2c3f95",
            "fresh force source differs")
    require(saved["modeled_mass_kg"] == 225.19791414318078
            and saved["same_state_dead_load_factor"] == 1.1110134616260479
            and saved["load_hypothesis"]["original_250_lb_times_2_signed_300_N_100_mm_lever"]
            and saved["load_hypothesis"]["wood_strength_CD_scenarios"] == SCENARIOS,
            "load or duration scenario differs")
    require(not saved["complete_member_acceptance"] and not saved["physical_release"]
            and set(saved["excluded_modified_bodies"]) == set(EXCLUDED), "saved claim boundary differs")
    members = {m["member"]: m for m in saved["members"]}
    require(len(members) == 42 and set(geometry["members"]) == set(members) | set(EXCLUDED), "member geometry join differs")
    return api, pins, saved, members, geometry["members"]


def member_map(members, geometry):
    """Geometry/source joins only; preparation does not evaluate resistance."""
    result = {}
    for name, member in members.items():
        record, g = geometry[name], member["source_geometry"]
        require(record["geometry"] == g and record["current_finished_step_sha256"] == member["finished_step_sha256"],
                "finished geometry differs: " + name)
        length = math.dist(g["start"], g["end"])
        require(abs(length-member["length_mm"]) < 1e-5, "finished full length differs: " + name)
        axis, grain = g["axis"], member["frozen_elastic_orientation"]["material_axes_global_xyz"]["L"]
        grain_aligned = abs(abs(sum(a*b for a, b in zip(axis, grain, strict=True)))-1) < 1e-8
        reasons = []
        if record["recess_source"] is not None:
            reasons.append("NONPRISMATIC_RECESS_OR_TAPER_NO_PRISMATIC_FORMULA_TRANSFER")
        if not grain_aligned:
            reasons.append("OBLIQUE_LONGITUDINAL_GRAIN_NO_PARALLEL_GRAIN_FORMULA")
        section = [g["width_mm"], g["depth_mm"]]
        require(all(math.isfinite(v) and v > 0 for v in section), "invalid finished section: " + name)
        old = member["stability_kernels"]["cd1"]["end_supported_only"]
        result[name] = {
            "member": name, "kind": member["kind"], "finished_length_mm": member["length_mm"],
            "finished_gross_section_u_v_mm": section, "section_axis_global_xyz": axis,
            "material_longitudinal_axis_global_xyz": grain, "longitudinal_grain_aligned": grain_aligned,
            "geometry_formula_status": "UNSUPPORTED_MEMBER_GEOMETRY" if reasons else "STRAIGHT_GROSS_PRISM_SENSITIVITY",
            "geometry_formula_limits": reasons, "finished_step": member["finished_step"],
            "finished_step_sha256": member["finished_step_sha256"],
            "column_effective_length_basis": "K=1 times full finished length in both directions; declared non-sway ends",
            "beam_effective_length_basis": "NDS Table 3.3.3 unspecified loading; full finished unbraced length",
            "actual_end_restraint_qualified": False, "credited_interior_restraint_stations": [],
            "source_only_weak_restraint_candidates": member["source_bolt_weak_restraint_candidates"],
            "candidate_limits": "Timber station/direction evidence only; no qualified receiver restraint, slack take-up, brace stiffness/capacity or end twist proof",
            "source_end_only_column_slenderness_strong_weak": old["column_slenderness_strong_weak"],
            "source_end_only_beam_slenderness": old["beam_slenderness"],
            "source_local_section_trace_counts": member["section_status_trace_counts"],
            "local_opening_or_taper_qualified": False,
        }
    return result


def scalar_helpers():
    timber = pure(TIMBER, ("adjusted_reference", "stability_factor", "member_check", "effective_beam_length"),
                  {"math": math})
    return timber, pure(STABILITY, ("stability_kernel", "normal_check"),
                        {"math": math, "member_check": timber.member_check,
                         "effective_beam_length": timber.effective_beam_length})


def known_answer_algebra(timber):
    """Parent-only reference algebra: each smaller root is exactly one half."""
    rows = []
    for label, ratio, c in (("CL", .525, .95), ("CP", .6, .8)):
        actual = timber.stability_factor(ratio, c)
        residual = c*actual**2-(1+ratio)*actual+ratio
        require(abs(actual-.5) < 1e-12 and abs(residual) < 1e-12, "known smaller-root algebra differs")
        rows.append({"factor": label, "Euler_to_strength_ratio": ratio, "c": c,
                     "known_smaller_root": .5, "returned": actual, "quadratic_residual": residual})
    return {"method": "c*y^2-(1+x)*y+x=0; substituted known y=1/2; no mechanical solve",
            "rows": rows, "software_test_suite": False}


def kernels(method, members, mapping):
    result = {}
    for name, member in members.items():
        result[name] = {}
        if mapping[name]["geometry_formula_limits"]:
            continue
        short, long = member["minimum_intact_rectangle_short_long_mm"]
        require(max(abs(a-b) for a, b in zip(sorted(mapping[name]["finished_gross_section_u_v_mm"]),
                                                            (short, long), strict=True)) < 1e-5,
                "straight-member rectangle varies: " + name)
        for scenario in SCENARIOS:
            ref = member["references"][scenario]
            kernel = method.stability_kernel(short, long, member["length_mm"], member["length_mm"], ref)
            old = member["stability_kernels"][scenario]["end_supported_only"]
            for key in ("CL", "Cp", "beam_slenderness", "FbE_mpa", "adjusted_Fc_mpa", "adjusted_Fb_strong_mpa"):
                require(math.isclose(kernel[key], old[key], rel_tol=1e-12, abs_tol=1e-12), "saved full-length kernel differs")
            result[name][scenario] = kernel
    return result


def compare_cut(trace, member, mapping, own_kernels, method):
    scenarios = {}
    reasons = list(mapping["geometry_formula_limits"])
    if trace["section_status"] != "BORE_FREE_FULL_RECTANGLE":
        reasons.append("UNSUPPORTED_SAVED_LOCAL_SECTION: " + trace["section_status"])
    if reasons:
        return {s: {"status": "UNSUPPORTED", "limits": reasons, "interaction_ratio": None} for s in SCENARIOS}
    width, depth = trace["rectangle_width_depth_mm"]
    require(max(abs(a-b) for a, b in zip((width, depth), mapping["finished_gross_section_u_v_mm"], strict=True)) < 1e-5,
            "trace section differs from full member")
    value = trace["signed_action_at_rectangle_centroid_n_nmm"]
    require(len(value) == 6 and all(math.isfinite(v) for v in value), "nonfinite saved signed action")
    for scenario in SCENARIOS:
        kernel = own_kernels[scenario]
        check = method.normal_check(value, width, depth, kernel, member["references"][scenario])
        saved = trace["scenarios"][scenario]["normal"]["end_supported_only"]
        require(check == saved, "saved full-length same-cut normal comparison differs")
        if not check["within_slenderness_limits"]:
            status = "UNSUPPORTED_NDS_SLENDERNESS_DOMAIN"
        elif not check["Euler_denominators_positive"] and value[0] < 0:
            status = "EXCEEDS_DECLARED_ELASTIC_STABILITY_BOUND"
        else:
            status = "EXCEEDS_DECLARED_REFERENCE" if check["ratio_exceeds_one"] else "WITHIN_DECLARED_REFERENCE"
        scenarios[scenario] = {
            "status": status, "interaction_ratio": check["interaction_ratio"] if check["within_slenderness_limits"] else None,
            "source_formula_diagnostic": check,
            "column_CP_required_at_this_cut": value[0] < 0,
            "column_CP": kernel["Cp"] if max(kernel["column_slenderness_strong_weak"]) <= 50 else None,
            "beam_CL": kernel["CL"] if kernel["beam_slenderness"] <= 50 else None,
            "actual_restraint_applicability": "DECLARED_END_SUPPORT_SENSITIVITY_ONLY",
        }
    return scenarios


def calculate(output, saved, members, mapping):
    timber, method = scalar_helpers()
    algebra = known_answer_algebra(timber)
    own_kernels = kernels(method, members, mapping)
    counts, by_member, peaks, local_counts = Counter(), {}, {}, {}
    seen = set()
    # ponytail: stream the existing JSONL; do not load arrays or rebuild forces.
    with TRACES.open() as source, (output / "same-cut-comparisons.jsonl").open("w") as stream:
        for line in source:
            trace = json.loads(line)
            name, case = trace["member"], trace["case_id"]
            require(name in members and case in CASES and trace["trace"] in ("before", "after"), "unexpected trace identity")
            identity = (name, case, trace["cut_array_index"])
            require(identity not in seen, "duplicate signed trace")
            seen.add(identity)
            local_counts.setdefault(name, Counter())[trace["section_status"]] += 1
            result = compare_cut(trace, members[name], mapping[name], own_kernels[name], method)
            witness = {k: trace[k] for k in ("member", "case_id", "cut_array_index", "station_mm", "trace",
                                           "section_status", "rectangle_width_depth_mm",
                                           "centroid_offset_grain_u_v_mm", "signed_action_at_source_cut_n_nmm",
                                           "signed_action_at_rectangle_centroid_n_nmm")}
            row = {**witness, "scenarios": result, "complete_member_acceptance": False}
            stream.write(json.dumps(row, allow_nan=False, separators=(",", ":")) + "\n")
            counts["source_traces"] += 1
            for scenario, comparison in result.items():
                status = comparison["status"]
                counts[scenario + "/" + status] += 1
                by_member.setdefault(name, {}).setdefault(scenario, Counter())[status] += 1
                if status.startswith("UNSUPPORTED"):
                    continue
                for metric in ("interaction_ratio", "stability_3_9_4_ratio"):
                    value = comparison["source_formula_diagnostic"][metric]
                    key = scenario + "/" + metric
                    if value is not None and (key not in peaks or value > peaks[key]["value"]):
                        peaks[key] = {**witness, "value": value, "status": status}
    require(counts["source_traces"] == saved["counts"]["signed_cut_traces"]
            and {identity[:2] for identity in seen} == {(n, c) for n in members for c in CASES}, "trace coverage incomplete")
    require(all(local_counts[n] == Counter(members[n]["section_status_trace_counts"]) for n in members), "saved section counts differ")
    return {"known_answer_algebra": algebra, "counts": dict(counts), "member_status_counts": by_member,
            "supported_domain_peaks": peaks, "full_length_kernels": own_kernels}


def execute(output, mechanics):
    output = Path(output).absolute()
    require(not RAW.is_symlink() and RAW.resolve().is_relative_to(HERE)
            and not output.is_symlink() and output.parent.resolve() == RAW.resolve() and not output.exists(),
            "use a fresh immediate child of rawlocal/member-restraint-completion")
    api, pins, saved, members, geometry = sources()
    mapping = member_map(members, geometry)
    output.mkdir(parents=True, exist_ok=False)
    (output / ".gitignore").write_text("*\n")
    (output / "producer.py.snapshot").write_bytes(Path(__file__).read_bytes())
    result = {}
    error = None
    try:
        if mechanics:
            result = calculate(output, saved, members, mapping)
        api.authenticate(pins)
    except Exception as caught:  # noqa: BLE001 -- preserve refusal evidence, then re-raise.
        error = caught
    status = "STOP" if error else ("CONDITIONAL_FULL_LENGTH_REFERENCE_SENSITIVITY" if mechanics
                                  else "PREPARED_NO_RESISTANCE_EVALUATED")
    source_map = {p.relative_to(ROOT).as_posix(): h for p, h in sorted(pins.items())}
    summary = {
        "schema": "member_restraint_completion/v1", "status": status,
        "mode": "build" if mechanics else "prepare", "error": str(error) if error else None,
        "scope": {"saved_members": 42, "frame_members": 20, "unchanged_blocks": 22,
                  "nominal_cases": list(CASES), "source_signed_traces": 53784,
                  "reviewed_global_bolt_axes": 104, "unadopted_proposal_axes": 108,
                  "excluded_modified_spines": list(EXCLUDED)},
        "member_restraint_map": mapping, "source_force_scope": saved["source_force_scope"],
        "source_load_hypothesis": saved["load_hypothesis"], "limits": LIMITS,
        "primary_source_sha256": {p.relative_to(ROOT).as_posix(): PINS[p] for p in (CH3, CH4, CH2, APPENDIX)},
        **result, **FLAGS,
    }
    (output / "summary.json").write_text(json.dumps(summary, indent=2, allow_nan=False) + "\n")
    (output / "sources.json").write_text(json.dumps(source_map, indent=2) + "\n")
    try:
        api.authenticate(pins)
    except Exception as caught:  # noqa: BLE001 -- an altered source must publish a STOP receipt.
        error = caught
        status = "STOP"
        summary.update(status=status, error=str(error))
        (output / "summary.json").write_text(json.dumps(summary, indent=2, allow_nan=False) + "\n")
    artifacts = {p.name: sha(p) for p in sorted(output.iterdir()) if p.is_file()}
    receipt = {"schema": "member_restraint_completion_receipt/v1", "status": status,
               "producer_sha256": sha(__file__), "source_sha256": source_map, "output_sha256": artifacts,
               "sources_authenticated_before_and_after": error is None, **FLAGS}
    (output / "receipt.json").write_text(json.dumps(receipt, indent=2, allow_nan=False) + "\n")
    if error:
        raise error
    return {"status": status, "output": str(output), "producer_sha256": sha(__file__),
            "source_files": len(pins), "summary_sha256": sha(output / "summary.json"),
            "receipt_sha256": sha(output / "receipt.json")}


def prepare(output):
    return execute(output, mechanics=False)


def build(output):
    """Parent-only scalar reference calculation; no frame/native/CAD execution."""
    return execute(output, mechanics=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--prepare", action="store_true")
    args = parser.parse_args()
    print(json.dumps((prepare if args.prepare else build)(args.output), indent=2))


if __name__ == "__main__":
    main()
