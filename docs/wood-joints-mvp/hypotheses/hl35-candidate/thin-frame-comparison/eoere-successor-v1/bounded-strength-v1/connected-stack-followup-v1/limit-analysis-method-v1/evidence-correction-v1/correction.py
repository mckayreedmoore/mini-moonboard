"""Guard and validate the frozen synthetic method; no candidate calculations."""

import argparse
import hashlib
import json
import math
import sys
import types
from decimal import Decimal, localcontext
from pathlib import Path

HERE = Path(__file__).resolve().parent
FROZEN = HERE.parent
ROOT = next(p for p in HERE.parents if (p / "current-candidate.json").is_file())
FROZEN_MAP_SHA256 = "eb2b28728f53cc83964402bda7a6a602173e55ec60a654aac2729e328e563883"
MODES = ("Im", "Is", "II", "IIIm", "IIIs", "IV")
CLAIMS = ("candidate_inputs_used", "candidate_joint_capacity", "capacity_or_pass_claim")
RESULT_KEYS = [
    "analyze_sha256",
    "candidate_inputs_used",
    "candidate_joint_capacity",
    "capacity_or_pass_claim",
    "cases",
    "claim_limits",
    "disposition",
    "environment",
    "inputs_sha256",
    "schema",
    "solver_controls",
    "source_pins",
    "summary",
]
CASE_KEYS = [
    "analytic_all_raw_modes_lbf",
    "analytic_raw_yield_lbf",
    "grids",
    "id",
    "published_reference_max_rounding_error_lbf",
    "raw_governing_mode",
]
GRID_KEYS = [
    "cells_per_member",
    "end_moment_lb_in",
    "end_shear_lbf",
    "maximum_exact_moment_lb_in",
    "moment_constraint_locations",
    "moment_cut_rounds",
    "numerical_feasibility_scale",
    "raw_LP_load_lbf",
    "relative_shortfall_from_raw_analytic",
    "scaled_LP_certificate",
    "scaled_statics_load_lbf",
]
CERT_KEYS = [
    "bearing_bound_violation",
    "dual_sign_violation",
    "dual_stationarity_residual",
    "equality_residual",
    "inequality_violation",
    "primal_dual_objective_gap",
]
FIELD_KEYS = [
    "a_in",
    "b_in",
    "bearing_density_lb_in",
    "bearing_bounds_lb_in",
    "statics_load_lbf",
    "moment_bound_lb_in",
]
SUMMARY_KEYS = [
    "LP_benchmark_count",
    "case_count",
    "governing_modes_verified",
    "maximum_128_cell_relative_shortfall",
    "maximum_scaled_LP_certificate_residual",
]
CONTROL_KEYS = [
    "infeasible_status",
    "loose_bending_cap_load_ratio",
    "rejected_invalid_inputs",
    "signed_bound_known_answer",
    "symmetric_32_cell_load_lbf",
    "symmetric_rigid_dowel_exact_II_lbf",
    "unbounded_status",
    "wrong_unsigned_bounds_allow_zero_load_only",
]


def need(condition, message):
    if not condition:
        raise ValueError(message)


def digest(data):
    return hashlib.sha256(data).hexdigest()


def encoded(value):
    return (
        json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n"
    ).encode()


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        need(key not in result, f"Duplicate JSON key: {key}")
        result[key] = value
    return result


def read_json(data):
    def reject_constant(value):
        raise ValueError(f"Nonfinite JSON constant: {value}")

    return json.loads(
        data, object_pairs_hook=unique_object, parse_constant=reject_constant
    )


def finite(value):
    if isinstance(value, dict):
        for item in value.values():
            finite(item)
    elif isinstance(value, list):
        for item in value:
            finite(item)
    elif type(value) is float:
        need(math.isfinite(value), "Nonfinite evidence number")


def shape(value, keys, label):
    need(type(value) is dict and set(value) == set(keys), f"Bad {label} schema")


def number(value):
    need(
        type(value) in (float, int) and math.isfinite(value),
        "Expected finite numeric field",
    )
    return value


def close(value, expected, label, *, absolute=1e-9):
    need(
        math.isclose(number(value), expected, rel_tol=1e-11, abs_tol=absolute),
        f"Changed {label}",
    )


def unchanged(pins):
    for path, expected in pins.items():
        need(
            digest((ROOT / path).read_bytes()) == expected,
            f"Source/evidence drift: {path}",
        )


def snapshot():
    """Read the bytes we consume, then authenticate the complete source closure."""
    contents, pins = {}, {}

    def capture(path, expected=None):
        relative = str(path.relative_to(ROOT))
        data = path.read_bytes()
        actual = digest(data)
        need(
            expected is None or actual == expected, f"Changed pinned source: {relative}"
        )
        need(
            relative not in pins or pins[relative] == actual,
            f"Conflicting source: {relative}",
        )
        contents[relative], pins[relative] = data, actual
        return data

    metadata = read_json(capture(HERE / "inputs.json"))
    need(
        metadata["schema"] == "synthetic_limit_evidence_correction_inputs/v1",
        "Wrong correction inputs",
    )
    need(
        metadata["candidate_inputs_used"] is False
        and metadata["capacity_or_pass_claim"] is False,
        "Correction inputs exceed synthetic scope",
    )
    frozen = metadata["frozen_files"]
    need(
        digest(encoded(frozen)) == FROZEN_MAP_SHA256, "Unrecognized frozen six-file map"
    )
    need(
        {Path(p).name for p in frozen}
        == {
            "README.md",
            "analyze.py",
            "inputs.json",
            "result.json",
            "verification.json",
            "verify.py",
        },
        "Six original files required",
    )
    for path, pin in frozen.items():
        need(ROOT / path == FROZEN / Path(path).name, "Unexpected frozen packet path")
        data = capture(ROOT / path, pin["sha256"])
        need(len(data) == pin["bytes"], "Changed frozen byte count")
    for name in ("correction.py", "check.py"):
        capture(HERE / name)
    for pin in metadata["review_receipts"]:
        capture(ROOT / pin["path"], pin["sha256"])
    inputs = read_json(contents[str((FROZEN / "inputs.json").relative_to(ROOT))])
    for pin in inputs["references"]:
        capture(ROOT / pin["path"], pin["sha256"])
    unchanged(pins)
    return {"pins": pins, "contents": contents, "inputs": inputs}


def load_original(state, filename):
    """Execute the authenticated captured source, not a second path read."""
    path = FROZEN / filename
    module = types.ModuleType("frozen_synthetic_" + path.stem)
    module.__file__ = str(path)
    sys.modules[module.__name__] = module
    # Only the original source bytes authenticated by FROZEN_MAP_SHA256 execute.
    exec(  # noqa: S102
        compile(state["contents"][str(path.relative_to(ROOT))], str(path), "exec"),
        module.__dict__,
    )
    return module


def raw_modes(case):
    """Independent high-precision positive roots of TR12 Table 1-1."""
    with localcontext() as ctx:
        ctx.prec = 48
        lm, ls, qm, qs, moment, gap = (
            Decimal(str(case[k]))
            for k in (
                "main_length_in",
                "side_length_in",
                "main_bearing_lb_in",
                "side_bearing_lb_in",
                "yield_moment_lb_in",
                "gap_in",
            )
        )
        coefficients = (
            (
                1 / (4 * qs) + 1 / (4 * qm),
                (ls + lm) / 2 + gap,
                -qs * ls * ls / 4 - qm * lm * lm / 4,
            ),
            (1 / (2 * qs) + 1 / (4 * qm), gap + lm / 2, -moment - qm * lm * lm / 4),
            (1 / (4 * qs) + 1 / (2 * qm), ls / 2 + gap, -qs * ls * ls / 4 - moment),
            (1 / (2 * qs) + 1 / (2 * qm), gap, -2 * moment),
        )
        values = [qm * lm, qs * ls]
        values.extend(
            (-b + (b * b - 4 * a * c).sqrt()) / (2 * a) for a, b, c in coefficients
        )
        return dict(zip(MODES, map(float, values)))


def validate_compact(result, details, state, analysis):
    """Validate all reporting assertions before reusing dimensional integration."""
    finite(result)
    finite(details)
    shape(result, RESULT_KEYS, "compact result")
    need(
        result["schema"] == "synthetic_dowel_bearing_moment_limit_result/v1",
        "Wrong compact schema",
    )
    need(
        result["disposition"] == "verified_synthetic_known_answers_only",
        "Wrong synthetic disposition",
    )
    need(
        result["candidate_inputs_used"] is False
        and result["capacity_or_pass_claim"] is False
        and result["candidate_joint_capacity"] is None,
        "Forbidden candidate/capacity claim",
    )
    inputs, pins = state["inputs"], state["pins"]
    for filename, field in (
        ("analyze.py", "analyze_sha256"),
        ("inputs.json", "inputs_sha256"),
    ):
        need(
            result[field] == pins[str((FROZEN / filename).relative_to(ROOT))],
            "Result not bound to captured original bytes",
        )
    need(
        result["source_pins"] == inputs["references"], "Changed external source closure"
    )
    need(result["claim_limits"] == inputs["claim_limits"], "Changed method limits")
    need(
        result["environment"] == inputs["environment"] == analysis.environment(),
        "Changed pinned environment",
    )
    cases = inputs["published_cases"] + inputs["synthetic_cases"]
    need(
        type(result["cases"]) is list
        and [row["id"] for row in result["cases"]] == [case["id"] for case in cases],
        "Missing/extra/duplicate/reordered cases",
    )
    expected_fields = {
        f"{case['id']}/{n}" for case in cases for n in inputs["cells_per_member"]
    }
    need(
        type(details) is dict and set(details) == expected_fields, "Wrong field census"
    )
    limits = inputs["limits"]
    for case, row in zip(cases, result["cases"]):
        shape(row, CASE_KEYS, "case")
        modes = raw_modes(case)
        governing = min(modes, key=modes.get)
        raw = modes[governing]
        need(row["raw_governing_mode"] == governing, "Invented raw governing mode")
        need(
            case.get("expected_raw_governing_mode", governing) == governing,
            "Changed expected raw mode",
        )
        close(row["analytic_raw_yield_lbf"], raw, "raw analytical load")
        shape(row["analytic_all_raw_modes_lbf"], MODES, "six analytical modes")
        for mode in MODES:
            close(
                row["analytic_all_raw_modes_lbf"][mode],
                modes[mode],
                f"analytical {mode}",
            )
        if "published_reference_values_lbf" in case:
            k = case["k_theta"]
            rd = (4 * k, 4 * k, 3.6 * k, 3.2 * k, 3.2 * k, 3.2 * k)
            rounding = max(
                abs(modes[mode] / factor - expected)
                for mode, factor, expected in zip(
                    MODES, rd, case["published_reference_values_lbf"]
                )
            )
            need(rounding <= 0.51, "Frozen published benchmark no longer agrees")
            close(
                row["published_reference_max_rounding_error_lbf"],
                rounding,
                "published rounding",
            )
        else:
            need(
                row["published_reference_max_rounding_error_lbf"] is None,
                "Invented published benchmark",
            )
        need(
            type(row["grids"]) is list
            and [g["cells_per_member"] for g in row["grids"]]
            == inputs["cells_per_member"],
            "Missing/extra/duplicate/reordered grids",
        )
        previous = 0.0
        for grid in row["grids"]:
            shape(grid, GRID_KEYS, "grid")
            n = grid["cells_per_member"]
            need(type(n) is int, "Noninteger grid size")
            for key in set(GRID_KEYS) - {"scaled_LP_certificate"}:
                number(grid[key])
            need(
                type(grid["moment_cut_rounds"]) is int
                and 1 <= grid["moment_cut_rounds"] <= limits["maximum_cut_rounds"],
                "Invalid moment rounds",
            )
            need(
                type(grid["moment_constraint_locations"]) is int
                and 2 * n + 1
                <= grid["moment_constraint_locations"]
                <= 4 * n * limits["maximum_cut_rounds"],
                "Invalid moment constraint census",
            )
            need(
                0 < grid["numerical_feasibility_scale"] <= 1
                and grid["raw_LP_load_lbf"] > 0,
                "Invalid statics scaling/load",
            )
            load = grid["scaled_statics_load_lbf"]
            close(
                load,
                grid["raw_LP_load_lbf"] * grid["numerical_feasibility_scale"],
                "scaled load",
            )
            need(load > 0 and load >= previous - 1e-6 * raw, "Invalid grid refinement")
            previous = load
            close(
                grid["relative_shortfall_from_raw_analytic"],
                1 - load / raw,
                "benchmark shortfall",
            )
            need(
                grid["relative_shortfall_from_raw_analytic"] >= -1e-8,
                "Benchmark exceeds raw analytical bound",
            )
            need(
                0
                <= grid["maximum_exact_moment_lb_in"]
                <= case["yield_moment_lb_in"] * (1 + 1e-9),
                "Invalid compact moment peak",
            )
            shape(grid["scaled_LP_certificate"], CERT_KEYS, "LP certificate")
            need(
                all(
                    0 <= number(v) <= limits["scaled_LP_residual_tolerance"]
                    for v in grid["scaled_LP_certificate"].values()
                ),
                "Invalid LP certificate residual",
            )
            field = details[f"{case['id']}/{n}"]
            shape(field, FIELD_KEYS, "field")
            for key in (
                "a_in",
                "b_in",
                "bearing_density_lb_in",
                "bearing_bounds_lb_in",
            ):
                need(
                    type(field[key]) is list and len(field[key]) == 2 * n,
                    "Bad field array",
                )
                for value in field[key]:
                    number(value)
            close(field["statics_load_lbf"], load, "field/compact load")
            close(
                field["moment_bound_lb_in"],
                case["yield_moment_lb_in"],
                "field moment bound",
            )
            triples = list(
                zip(field["a_in"], field["b_in"], field["bearing_density_lb_in"])
            )
            length = case["side_length_in"] + case["gap_in"] + case["main_length_in"]
            close(
                grid["end_shear_lbf"],
                math.fsum(q * (b - a) for a, b, q in triples),
                "reported end shear",
                absolute=1e-8,
            )
            close(
                grid["end_moment_lb_in"],
                math.fsum(
                    q * ((length - a) ** 2 - (length - b) ** 2) / 2
                    for a, b, q in triples
                ),
                "reported end moment",
                absolute=1e-8,
            )
        need(
            row["grids"][-1]["relative_shortfall_from_raw_analytic"]
            <= limits["maximum_final_relative_error"],
            "Insufficient final benchmark agreement",
        )
    summary = result["summary"]
    shape(summary, SUMMARY_KEYS, "summary")
    for key, expected in (
        ("case_count", len(cases)),
        ("LP_benchmark_count", len(expected_fields)),
    ):
        need(
            type(summary[key]) is int and summary[key] == expected,
            "Wrong summary census",
        )
    need(
        summary["governing_modes_verified"]
        == sorted({row["raw_governing_mode"] for row in result["cases"]}),
        "Invented summary modes",
    )
    close(
        summary["maximum_128_cell_relative_shortfall"],
        max(
            row["grids"][-1]["relative_shortfall_from_raw_analytic"]
            for row in result["cases"]
        ),
        "summary benchmark maximum",
    )
    close(
        summary["maximum_scaled_LP_certificate_residual"],
        max(
            max(g["scaled_LP_certificate"].values())
            for row in result["cases"]
            for g in row["grids"]
        ),
        "summary certificate maximum",
        absolute=1e-15,
    )
    controls = result["solver_controls"]
    shape(controls, CONTROL_KEYS, "controls")
    for key, value in (
        ("signed_bound_known_answer", -2),
        ("wrong_unsigned_bounds_allow_zero_load_only", 0),
        ("infeasible_status", 2),
        ("unbounded_status", 3),
    ):
        close(controls[key], value, "solver control")
    need(
        controls["rejected_invalid_inputs"]
        == [
            "main_length_in",
            "side_length_in",
            "main_bearing_lb_in",
            "yield_moment_lb_in",
            "gap_in",
        ],
        "Changed rejection controls",
    )
    need(
        number(controls["loose_bending_cap_load_ratio"]) > 2, "Invalid bending control"
    )
    base = inputs["synthetic_cases"][0]
    exact = base["main_bearing_lb_in"] * base["main_length_in"] / (1 + math.sqrt(2))
    close(
        controls["symmetric_rigid_dowel_exact_II_lbf"],
        exact,
        "closed-form mode II control",
    )
    base_row = next(row for row in result["cases"] if row["id"] == base["id"])
    close(
        controls["symmetric_32_cell_load_lbf"],
        base_row["grids"][0]["scaled_statics_load_lbf"],
        "symmetric grid control",
    )
    return {key: result[key] for key in CLAIMS}


def new_file(path, data):
    with Path(path).open("xb") as stream:
        stream.write(data)


def produce(output):
    Path(output).mkdir(parents=True, exist_ok=False)
    state = snapshot()
    analysis = load_original(state, "analyze.py")
    checker = load_original(state, "verify.py")
    analysis.check_pins(state["inputs"])
    unchanged(state["pins"])
    try:
        result, details = analysis.run(state["inputs"])
    finally:
        unchanged(state["pins"])
    claims = validate_compact(result, details, state, analysis)
    independent = checker.check(result, details, state["inputs"])
    documents = {"result.json": encoded(result), "details.json": encoded(details)}
    provenance = {
        "schema": "synthetic_limit_guarded_production/v1",
        "status": "VERIFIED_SYNTHETIC_ONLY",
        "source_sha256": state["pins"],
        "captured_inputs_sha256": result["inputs_sha256"],
        "validated_claims": claims,
        "independent_checks": independent,
        "output_sha256": {name: digest(data) for name, data in documents.items()},
        "output_policy": "fresh directory; no success marker before post-serialization source check",
    }
    receipt = encoded(provenance)
    unchanged(state["pins"])
    for name, data in documents.items():
        new_file(Path(output) / name, data)
    unchanged(state["pins"])
    new_file(Path(output) / "run-provenance.json", receipt)
    return provenance


def verify(run, replay, output):
    need(
        not Path(output).exists() and not Path(output).is_symlink(),
        "Verification output must be new",
    )
    state = snapshot()
    analysis = load_original(state, "analyze.py")
    checker = load_original(state, "verify.py")
    analysis.check_pins(state["inputs"])
    evidence, evidence_pins = {}, {}
    for label, directory in (("run", Path(run)), ("replay", Path(replay))):
        for name in ("result.json", "details.json", "run-provenance.json"):
            path = directory / name
            data = path.read_bytes()
            evidence[label, name] = data
            evidence_pins[str(path.resolve())] = digest(data)
    need(
        all(
            evidence["run", name] == evidence["replay", name]
            for name in ("result.json", "details.json", "run-provenance.json")
        ),
        "Replay bytes differ",
    )
    result = read_json(evidence["run", "result.json"])
    details = read_json(evidence["run", "details.json"])
    claims = validate_compact(result, details, state, analysis)
    independent = checker.check(result, details, state["inputs"])
    provenance = read_json(evidence["run", "run-provenance.json"])
    finite(provenance)
    shape(
        provenance,
        (
            "schema",
            "status",
            "source_sha256",
            "captured_inputs_sha256",
            "validated_claims",
            "independent_checks",
            "output_sha256",
            "output_policy",
        ),
        "production provenance",
    )
    need(
        provenance["schema"] == "synthetic_limit_guarded_production/v1"
        and provenance["status"] == "VERIFIED_SYNTHETIC_ONLY",
        "Wrong production status",
    )
    need(
        provenance["source_sha256"] == state["pins"],
        "Production source snapshot differs",
    )
    need(
        provenance["captured_inputs_sha256"] == result["inputs_sha256"],
        "Production input snapshot differs",
    )
    need(provenance["validated_claims"] == claims, "Production claims differ")
    need(
        provenance["independent_checks"] == independent,
        "Production integration metrics differ",
    )
    need(
        provenance["output_sha256"]
        == {
            name: digest(evidence["run", name])
            for name in ("result.json", "details.json")
        },
        "Production evidence hashes differ",
    )
    need(
        provenance["output_policy"]
        == "fresh directory; no success marker before post-serialization source check",
        "Wrong production output policy",
    )
    receipt = {
        "schema": "synthetic_limit_corrected_verification/v1",
        "status": "VERIFIED_SYNTHETIC_ONLY",
        "validated_claims": claims,
        "source_sha256": state["pins"],
        "independent_checks": independent,
        "byte_identical_replay": True,
        "run_files_sha256": {
            name: digest(evidence["run", name])
            for name in ("result.json", "details.json", "run-provenance.json")
        },
        "validation": "strict finite schema/claims/census; independent raw-mode equations and summary/field ties; retained dimensional integration",
    }
    data = encoded(receipt)
    unchanged(state["pins"])
    for path, expected in evidence_pins.items():
        need(digest(Path(path).read_bytes()) == expected, "Run/replay evidence drift")
    new_file(output, data)
    return receipt


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("produce").add_argument("--out", type=Path, required=True)
    validation = commands.add_parser("verify")
    for name in ("run", "replay", "out"):
        validation.add_argument("--" + name, type=Path, required=True)
    args = parser.parse_args()
    try:
        result = (
            produce(args.out)
            if args.command == "produce"
            else verify(args.run, args.replay, args.out)
        )
    except (OSError, ValueError, TypeError, KeyError, StopIteration) as error:
        parser.exit(1, f"Evidence rejected: {error}\n")
    print(
        json.dumps(
            {
                "status": result["status"],
                "validated_claims": result["validated_claims"],
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
