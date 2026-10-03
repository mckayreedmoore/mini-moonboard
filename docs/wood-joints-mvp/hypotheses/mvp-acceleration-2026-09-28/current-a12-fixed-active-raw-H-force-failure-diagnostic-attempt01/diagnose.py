#!/usr/bin/env python3
"""Read-only classification of the frozen A12 raw-H force interval misses."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path

import numpy as np


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
BASE = ROOT / "docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28"
RAW = BASE / "current-a12-fixed-active-raw-H-comparison-attempt01"
KNOWN = BASE / "current-a12-fixed-episode-dual-qp-preparation-attempt01"
PROJECTION = BASE / "current-frame-physical-connector-projection-contract-attempt01"
ROWS = BASE / "current-frame-connector-compliance-attempt04"
CASE = BASE / "current-springa-selected-floor-a12-rear-attempt03"
COMPLIANCE = BASE / "current-frame-connector-compliance-attempt04"
OUT = HERE / "assessment.json"
PINS = HERE / "source-pins.json"
OUTPUT_PIN = HERE / "output-pin.json"

INPUTS = {
    "raw_assessment": RAW / "assessment.json",
    "raw_response": RAW / "response.npz",
    "raw_frozen_inputs": RAW / "frozen-inputs.json",
    "raw_producer": RAW / "prepare_raw.py",
    "native_known_answer": KNOWN / "known-answer.npz",
    "native_answer_producer": KNOWN / "prepare.py",
    "projection_contract": PROJECTION / "projection-contract.json",
    "row_identities": ROWS / "row-identities.json",
    "compliance_assessment": COMPLIANCE / "assessment.json",
    "compliance_inputs": COMPLIANCE / "inputs.json",
    "compliance_operators": COMPLIANCE / "operators.npz",
    "native_deck": CASE / "model.inp",
    "native_model": CASE / "model.json",
    "native_dat": CASE / "model.dat",
    "native_response": CASE / "response.json",
    "springa_source_audit": BASE / "current-springa-zero-u-token-response-audit-attempt01/stable_response_audit.py",
    "ghost_coordinate_prior_diagnostic": BASE / "current-springa-ghost-coordinate-translation-diagnostic-attempt01/audit.py",
}


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def read_json(path: Path):
    return json.loads(path.read_text())


def number(value):
    return float(value)


def parse_numeric_line(line: str) -> list[float]:
    return [float(part.strip().replace("D", "E")) for part in line.split(",") if part.strip()]


def parse_deck(deck_path: Path):
    lines = deck_path.read_text().splitlines()
    nodes: dict[int, np.ndarray] = {}
    elements: dict[int, tuple[str, int, int]] = {}
    springs: dict[str, list[tuple[float, float]]] = {}
    equations: dict[tuple[int, int], list[tuple[int, int, float]]] = {}

    i = 0
    while i < len(lines):
        line = lines[i].strip()
        upper = line.upper()
        if upper == "*NODE":
            i += 1
            while i < len(lines) and not lines[i].lstrip().startswith("*"):
                raw = lines[i].strip()
                if raw and not raw.startswith("**"):
                    vals = parse_numeric_line(raw)
                    if len(vals) >= 4:
                        nodes[int(vals[0])] = np.asarray(vals[1:4], dtype=float)
                i += 1
            continue

        element_match = re.match(r"\*ELEMENT\s*,\s*TYPE\s*=\s*SPRINGA\s*,\s*ELSET\s*=\s*(SPR\d+)", upper)
        if element_match:
            group = element_match.group(1)
            i += 1
            while i < len(lines) and (not lines[i].strip() or lines[i].lstrip().startswith("**")):
                i += 1
            vals = parse_numeric_line(lines[i].strip())
            if len(vals) < 3:
                raise ValueError(f"bad SPRINGA element record for {group}")
            elements[int(vals[0])] = (group, int(vals[1]), int(vals[2]))
            i += 1
            continue

        spring_match = re.match(r"\*SPRING\s*,\s*ELSET\s*=\s*(SPR\d+)", upper)
        if spring_match:
            group = spring_match.group(1)
            pairs = []
            i += 1
            while i < len(lines) and not lines[i].lstrip().startswith("*"):
                raw = lines[i].strip()
                if raw and not raw.startswith("**"):
                    vals = parse_numeric_line(raw)
                    if len(vals) >= 2:
                        pairs.append((float(vals[0]), float(vals[1])))
                i += 1
            springs[group] = pairs
            continue

        if upper.startswith("*EQUATION"):
            i += 1
            while i < len(lines) and not lines[i].strip():
                i += 1
            term_count = int(lines[i].strip())
            i += 1
            values: list[float] = []
            while i < len(lines) and len(values) < 3 * term_count:
                raw = lines[i].strip()
                if raw and not raw.startswith("**"):
                    values.extend(parse_numeric_line(raw))
                i += 1
            if len(values) != 3 * term_count:
                raise ValueError("incomplete *EQUATION in emitted deck")
            terms = [(int(values[j]), int(values[j + 1]), float(values[j + 2]))
                     for j in range(0, len(values), 3)]
            equations[(terms[0][0], terms[0][1])] = terms
            continue
        i += 1
    return nodes, elements, springs, equations


def max_abs(values):
    return max((abs(float(value)) for value in values), default=0.0)


def build_assessment():
    raw_assessment = read_json(INPUTS["raw_assessment"])
    identities = read_json(INPUTS["row_identities"])
    projection = read_json(INPUTS["projection_contract"])["rows"]
    native = read_json(INPUTS["native_response"])
    compliance = read_json(INPUTS["compliance_assessment"])
    body_audit = {str(row["body"]): row for row in compliance["bodies"]}
    if len(identities) != 1840 or len(projection) != 1840:
        raise AssertionError("source connector inventory length changed")

    with np.load(INPUTS["raw_response"], allow_pickle=False) as saved:
        forces = saved["f_full_N"].astype(float)
        q_raw = saved["q_raw_mm"].astype(float)
    with np.load(INPUTS["native_known_answer"], allow_pickle=False) as answer:
        native_force = answer["f_native_full_N"].astype(float)
        native_radius = answer["f_native_rounding_radius_full_N"].astype(float)
    if not (forces.shape == q_raw.shape == native_force.shape == native_radius.shape == (1840,)):
        raise AssertionError("source force vector shape changed")

    guard = 128.0 * np.finfo(float).eps * (np.abs(forces) + np.abs(native_force) + 1.0)
    difference = np.abs(forces - native_force)
    allowed = native_radius + guard
    ratios = difference / allowed
    failures = np.flatnonzero(difference > allowed)
    recorded_positions = [int(r["global_source_row_position"])
                          for r in raw_assessment["failed_source_intervals"]["forces"]]
    if recorded_positions != failures.tolist():
        raise AssertionError("recomputed force interval failures differ from frozen assessment")
    if len(failures) != 27:
        raise AssertionError(f"expected 27 unchanged force interval failures, got {len(failures)}")

    native_final = native["increments"][-1]
    springa = {str(row["source_group"]): row for row in native_final["springa_components"]}
    spring2 = {str(row["source_group"]): row
               for row in native_final["retained_bilateral_spring2_components"]}
    floor_t = {str(row["source_row_id"]): row
               for row in native_final["exact_floor_tangent_reactions"]}
    nodes, elements, springs, equations = parse_deck(INPUTS["native_deck"])

    output_rows = []
    for index in failures:
        i = int(index)
        row = identities[i]
        c = projection[i]
        family = row["family"]
        group = str(row.get("source_group", ""))
        source_element = int(row["source_element"])
        out = {
            "source_position": i,
            "row_id": row["row_id"],
            "source_group": group,
            "source_element": source_element,
            "family": family,
            "native_force_channel": None,
            "raw_H_force_N": float(forces[i]),
            "native_force_center_N": float(native_force[i]),
            "native_force_rounding_radius_N": float(native_radius[i]),
            "difference_N": float(difference[i]),
            "allowed_difference_N": float(allowed[i]),
            "interval_ratio": float(ratios[i]),
        }
        owner_record = row.get("ownership", {})
        owner_bodies = [owner_record[key] for key in ("first_body", "second_body")
                        if owner_record.get(key) in body_audit]
        out["owner_body_operator_audit_envelopes"] = {
            name: {
                "max_kkt_relative_residual_across_body_chunks": float(body_audit[name]["max_kkt_relative_residual"]),
                "max_original_Ku_minus_projected_load_N_across_body_chunks": float(body_audit[name]["max_original_Ku_minus_projected_load_N"]),
                "max_original_residual_body_force_N_across_body_chunks": float(body_audit[name]["max_original_residual_body_force_N"]),
                "max_original_residual_body_moment_N_mm_across_body_chunks": float(body_audit[name]["max_original_residual_body_moment_N_mm"]),
                "rigid_leakage_relative_numerical_screen": float(body_audit[name]["operator_audit"]["relative_KR_inf"]),
                "rigid_leakage_limit_is_only_a_numerical_screen": bool(
                    body_audit[name]["operator_audit"]["limit_is_numerical_screen_not_assembly_error_bound"]),
            }
            for name in owner_bodies
        }
        if family == "unilateral_springa":
            rec = springa[group]
            native_channel = float(rec["native_endpoint_internal_force_N"])
            if abs(native_channel - native_force[i]) > native_radius[i] + 1e-12:
                raise AssertionError(f"SPRINGA endpoint RF differs from pinned known answer at row {i}")
            out["native_force_channel"] = "SPRINGA endpoint internal RF projected on emitted axis"
            out["native_springa"] = {
                "native_q_relative_projection_mm": float(rec["q_relative_projection_mm"]),
                "native_qghost_mm": float(rec["q_from_qghost_mm"]),
                "native_geometric_elongation_mm": float(rec["geometric_spring_elongation_mm"]),
                "native_geometric_table_force_N": float(rec["native_table_force_N_from_actual_dd_minus_dd0"]),
                "native_linear_projection_force_N": float(rec["projected_q_force_law_N_diagnostic_only"]),
                "native_geometric_minus_linear_projection_force_N": float(
                    rec["native_table_force_N_from_actual_dd_minus_dd0"]
                    - rec["projected_q_force_law_N_diagnostic_only"]),
                "raw_H_scalar_linear_force_N": float(row["law"]["stiffness_N_per_mm"] * max(q_raw[i], 0.0)),
                "raw_H_force_minus_scalar_linear_force_N": float(
                    forces[i] - row["law"]["stiffness_N_per_mm"] * max(q_raw[i], 0.0)),
                "raw_H_force_minus_native_geometric_table_force_N": float(
                    forces[i] - rec["native_table_force_N_from_actual_dd_minus_dd0"]),
            }

            if source_element not in elements:
                raise AssertionError(f"emitted deck has no SPRINGA element {source_element}")
            deck_group, node1, node2 = elements[source_element]
            if deck_group != group or group not in springs:
                raise AssertionError(f"emitted SPRINGA group/table mapping changed for row {i}")
            table = springs[group]
            force0 = next((f for f, x in table if x == 0.0), None)
            force10 = next((f for f, x in table if x == 10.0), None)
            force_minus10 = next((f for f, x in table if x == -10.0), None)
            if force0 is None or force10 is None or force_minus10 is None:
                raise AssertionError(f"incomplete emitted force table for {group}")
            deck_k = (force10 - force0) / 10.0
            reduced_k = float(row["law"]["stiffness_N_per_mm"])
            x1, x2 = nodes[node1], nodes[node2]
            initial_vector = x1 - x2
            initial_length = float(np.linalg.norm(initial_vector))
            deck_axis = initial_vector / initial_length
            expected_axis = np.asarray(row["ownership"]["direction_global_xyz"], dtype=float)
            axis_delta = deck_axis - expected_axis

            expected_equations = c["source_projection"]["qghost_equations"]
            equation_deltas = []
            for expected in expected_equations:
                dependent = tuple(int(x) for x in expected["dependent_q_dof"])
                if dependent not in equations:
                    raise AssertionError(f"missing emitted MPC for {group} {dependent}")
                actual_terms = equations[dependent]
                expected_terms = [(int(t[0]), int(t[1]), float(t[2]))
                                  for t in expected["terms"]]
                actual_map = {(n, d): coeff for n, d, coeff in actual_terms}
                expected_map = {(n, d): coeff for n, d, coeff in expected_terms}
                if actual_map.keys() != expected_map.keys():
                    raise AssertionError(f"emitted MPC term identities differ for {group} {dependent}")
                equation_deltas.extend(actual_map[key] - expected_map[key] for key in actual_map)
            out["emitted_source_operator_check"] = {
                "deck_group_matches_source": deck_group == group,
                "endpoint_node_ids": [node1, node2],
                "positive_branch_table_slope_N_per_mm": deck_k,
                "reduced_row_stiffness_N_per_mm": reduced_k,
                "table_slope_absolute_difference_N_per_mm": abs(deck_k - reduced_k),
                "table_force_at_zero_N": force0,
                "table_force_at_minus10_N": force_minus10,
                "nominal_initial_length_mm": initial_length,
                "initial_length_minus_100mm": initial_length - 100.0,
                "deck_axis_global_xyz": deck_axis.tolist(),
                "reduced_source_axis_global_xyz": expected_axis.tolist(),
                "axis_coefficient_delta_xyz": axis_delta.tolist(),
                "axis_coefficient_delta_inf": max_abs(axis_delta),
                "emitted_MPC_vs_projection_contract_max_abs_coefficient": max_abs(equation_deltas),
            }
        elif family == "bilateral_spring2":
            rec = spring2[group]
            out["native_force_channel"] = "SPRING2 scalar force on first endpoint from native DAT"
            out["native_channel_matches_center_N"] = float(rec["force_on_first_local_N"] - native_force[i])
        elif family == "conditional_floor_tangent_constraint":
            rec = floor_t[str(row["row_id"])]
            out["native_force_channel"] = "recovered physical floor-T reaction projected on source axis"
            out["native_channel_matches_center_N"] = float(
                -float(rec["recovered_physical_tangent_reaction_N"]) - native_force[i])
        else:
            raise AssertionError(f"unexpected failed force family {family}")
        output_rows.append(out)

    by_family = {}
    for family in sorted({r["family"] for r in output_rows}):
        family_rows = [r for r in output_rows if r["family"] == family]
        radii = [r["native_force_rounding_radius_N"] for r in family_rows]
        by_family[family] = {
            "failed_rows": len(family_rows),
            "max_failed_absolute_difference_N": max(r["difference_N"] for r in family_rows),
            "max_failed_interval_ratio": max(r["interval_ratio"] for r in family_rows),
            "min_native_rounding_radius_N": min(radii),
            "max_native_rounding_radius_N": max(radii),
            "positions": [r["source_position"] for r in family_rows],
        }

    all_max_abs_i = int(np.argmax(difference))
    worst_ratio_i = int(np.argmax(ratios))
    max_failed_abs = max(output_rows, key=lambda r: r["difference_N"])
    worst_failed_ratio = max(output_rows, key=lambda r: r["interval_ratio"])
    spring_rows = [r for r in output_rows if r["family"] == "unilateral_springa"]
    spring_deltas = [r["native_springa"]["native_geometric_minus_linear_projection_force_N"]
                     for r in spring_rows]
    deck_checks = [r["emitted_source_operator_check"] for r in spring_rows]
    body_records = list(body_audit.values())
    failed_owner_names = sorted({name for row in output_rows
                                 for name in row["owner_body_operator_audit_envelopes"]})
    spring_table_deltas = [c["table_slope_absolute_difference_N_per_mm"] for c in deck_checks]
    spring_table_k = [c["reduced_row_stiffness_N_per_mm"] for c in deck_checks]
    raw_law_deltas = [r["native_springa"]["raw_H_force_minus_scalar_linear_force_N"]
                      for r in spring_rows]
    raw_table_deltas = [r["native_springa"]["raw_H_force_minus_native_geometric_table_force_N"]
                        for r in spring_rows]

    result = {
        "schema": "a12_raw_h_force_failure_diagnostic/v1",
        "status": "PASS_READ_ONLY_DIAGNOSIS",
        "scope": "Recompute force interval failures and classify source/output precision; no solve or native execution.",
        "input_sha256": {name: sha(path) for name, path in INPUTS.items()},
        "force_interval": {
            "row_count": int(len(forces)),
            "failure_count": int(len(failures)),
            "family_counts": {key: by_family[key]["failed_rows"] for key in by_family},
            "all_row_max_absolute_difference": {
                "source_position": all_max_abs_i,
                "row_id": identities[all_max_abs_i]["row_id"],
                "family": identities[all_max_abs_i]["family"],
                "difference_N": float(difference[all_max_abs_i]),
                "allowed_difference_N": float(allowed[all_max_abs_i]),
                "interval_ratio": float(ratios[all_max_abs_i]),
                "failed": bool(difference[all_max_abs_i] > allowed[all_max_abs_i]),
            },
            "all_row_worst_normalized_difference": {
                "source_position": worst_ratio_i,
                "row_id": identities[worst_ratio_i]["row_id"],
                "family": identities[worst_ratio_i]["family"],
                "difference_N": float(difference[worst_ratio_i]),
                "allowed_difference_N": float(allowed[worst_ratio_i]),
                "interval_ratio": float(ratios[worst_ratio_i]),
            },
            "largest_failed_absolute_difference": max_failed_abs,
            "worst_failed_normalized_difference": worst_failed_ratio,
            "by_family": by_family,
            "native_precision_interpretation": {
                "unilateral_springa": "Native endpoint internal RF center; interval radius is propagated through the emitted axis from the printed native RF component intervals.",
                "bilateral_spring2": "Native scalar first-endpoint force center with its native DAT rounding radius.",
                "conditional_floor_tangent_constraint": "Physical floor tangent reaction recovered from the support RF pair and projected along the source axis; interval radius propagates the printed RF components.",
            },
            "failed_rows": output_rows,
        },
        "springa_operator_and_finite_length": {
            "native_law": "CCX SPRINGA evaluates its nonlinear table from dd - dd0, where dd and dd0 are current and initial endpoint distances; the table has zero at zero elongation and positive-branch slope k.",
            "reduced_law": "The reduced connector relation uses scalar projected displacement q and f = k * max(q, 0).",
            "native_geometric_vs_projection_interpretation_limit": "The recorded comparison uses native output values derived from printed displacements and source projection data. It is a geometric-versus-projection diagnostic discrepancy; finite-length response, output rounding and mapping/projection arithmetic are not separated by this comparison.",
            "source_row_count": len(spring_rows),
            "max_emitted_table_slope_mismatch_N_per_mm": max(
                spring_table_deltas),
            "max_emitted_table_slope_relative_mismatch": max(
                delta / k for delta, k in zip(spring_table_deltas, spring_table_k)),
            "max_emitted_MPC_coefficient_mismatch": max(
                c["emitted_MPC_vs_projection_contract_max_abs_coefficient"] for c in deck_checks),
            "max_emitted_axis_component_mismatch": max(c["axis_coefficient_delta_inf"] for c in deck_checks),
            "max_initial_span_departure_from_100mm": max(
                abs(c["initial_length_minus_100mm"]) for c in deck_checks),
            "native_state_geometric_minus_scalar_projection_force_N": {
                "max_abs": max_abs(spring_deltas),
                "min_signed": min(spring_deltas),
                "max_signed": max(spring_deltas),
                "row_with_max_abs": max(spring_rows, key=lambda r: abs(
                    r["native_springa"]["native_geometric_minus_linear_projection_force_N"])),
            },
            "raw_H_scalar_linear_law_residual_N": {
                "max_abs": max_abs(raw_law_deltas),
                "row_with_max_abs": max(spring_rows, key=lambda r: abs(
                    r["native_springa"]["raw_H_force_minus_scalar_linear_force_N"])),
            },
            "raw_H_force_minus_native_state_geometric_table_force_N": {
                "max_abs": max_abs(raw_table_deltas),
                "row_with_max_abs": max(spring_rows, key=lambda r: abs(
                    r["native_springa"]["raw_H_force_minus_native_geometric_table_force_N"])),
            },
            "row_1586_source_check": next(r for r in spring_rows if r["source_position"] == 1586),
            "raw_state_endpoint_vector_availability": {
                "available_in_saved_raw_H_response": False,
                "saved_response_arrays": ["f_full_N", "q_raw_mm", "q_sym_mm", "a_mm", "lambda_eq_mm", "mu_active_bound_mm", "body_equilibrium_residuals_N_and_unscaled_moment", "raw_source_law_residuals_N_active_order", "raw_bordered_equation_residual", "fixed_bound_local_positions", "fixed_bound_global_source_positions"],
                "required_to_evaluate_raw_state_dd_minus_dd0": "The full physical endpoint displacement vectors for every SPRINGA, including their MPC-interpolated values; scalar q_raw alone is insufficient.",
            },
        },
        "owner_body_operator_accuracy": {
            "per_failed_row_owner_envelopes_included": True,
            "affected_owner_body_count": len(failed_owner_names),
            "affected_owner_bodies": failed_owner_names,
            "affected_owner_max_kkt_relative_residual": max(
                float(body_audit[name]["max_kkt_relative_residual"]) for name in failed_owner_names),
            "affected_owner_max_original_force_residual_N": max(
                float(body_audit[name]["max_original_residual_body_force_N"]) for name in failed_owner_names),
            "affected_owner_max_original_moment_residual_N_mm": max(
                float(body_audit[name]["max_original_residual_body_moment_N_mm"]) for name in failed_owner_names),
            "all_50_body_max_kkt_relative_residual_range": [
                min(float(b["max_kkt_relative_residual"]) for b in body_records),
                max(float(b["max_kkt_relative_residual"]) for b in body_records),
            ],
            "all_50_body_max_original_force_residual_N": max(
                float(b["max_original_residual_body_force_N"]) for b in body_records),
            "all_50_body_max_original_moment_residual_N_mm": max(
                float(b["max_original_residual_body_moment_N_mm"]) for b in body_records),
            "interpretation": "These are per-body maxima over the actual compliance RHS chunks. The KKT residual and original-K force/moment residuals diagnose operator construction/solve accuracy; they are not mapped to a force-error bound for any failed connector row.",
            "native_DAT_rounding_is_separate": "Each failed row's allowed interval uses its native center and native output-rounding radius. The KKT and body-equilibrium residuals do not enlarge that radius and are not included in the DAT comparison gate.",
            "current_uncertainty_limit": "No rowwise perturbation/sensitivity bound maps the measured H/e/operator residuals to the 27 source force errors. The reported residuals therefore do not establish their cause.",
        },
        "disposition": {
            "status": "STOP_FORCE_SOURCE_INTERVALS_REMAIN_FAILED",
            "raw_H_changed_failure_count_from_prior_symmetric_attempt": "25 to 27; raw-H improves the source spring-law residual but does not pass the force DAT intervals.",
            "emitted_coefficients_or_span_rounding_explanation": "Not supported as a cause by this check: emitted table slopes match reduced k, emitted MPC terms match the pinned projection contract to the measured tiny coefficient differences, and initial span departure from 100 mm is recorded with the existing dd0 subtraction. No force correction is inferred from these differences.",
            "nonlinear_geometry_scope": "Native-state geometric-versus-projection discrepancies are quantified row by row, but their finite-length, output-rounding and mapping/projection contributions are not isolated. They cannot be applied to the raw-H state because the frozen reduced response has no endpoint displacement vectors. A raw-state geometric SPRINGA evaluation requires a candidate endpoint displacement field and the unchanged emitted MPC map.",
            "next_dependency": "If continuing beyond this stop, prepare a source-bound method that reconstructs each candidate physical endpoint displacement from body rigid coordinates plus elastic connector-response terms, applies the exact emitted MPCs and SPRINGA dd-dd0 law, then evaluates the existing source intervals without widening them. This diagnostic does not authorize or execute that method.",
            "native_run": False,
            "frame_state_solve": False,
            "threshold_change": False,
        },
    }
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--write-pins", action="store_true")
    args = parser.parse_args()
    if args.write_pins:
        PINS.write_text(json.dumps({name: sha(path) for name, path in INPUTS.items()}, indent=2, sort_keys=True) + "\n")
    expected = read_json(PINS)
    actual = {name: sha(path) for name, path in INPUTS.items()}
    if actual != expected:
        raise SystemExit("input source hash mismatch")
    result = build_assessment()
    if args.verify:
        if not OUT.exists() or read_json(OUT) != result:
            raise SystemExit("diagnostic assessment mismatch")
        expected_output_pin = {
            "assessment_sha256": sha(OUT),
            "diagnose_py_sha256": sha(Path(__file__)),
            "source_pins_sha256": sha(PINS),
        }
        if not OUTPUT_PIN.exists() or read_json(OUTPUT_PIN) != expected_output_pin:
            raise SystemExit("diagnostic output pin mismatch")
        print("PASS_READ_ONLY_RAW_H_FORCE_DIAGNOSTIC")
    else:
        OUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
        OUTPUT_PIN.write_text(json.dumps({
            "assessment_sha256": sha(OUT),
            "diagnose_py_sha256": sha(Path(__file__)),
            "source_pins_sha256": sha(PINS),
        }, indent=2, sort_keys=True) + "\n")
        print(result["status"])


if __name__ == "__main__":
    main()
