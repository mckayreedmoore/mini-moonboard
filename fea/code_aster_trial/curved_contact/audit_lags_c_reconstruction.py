#!/usr/bin/env python3
"""Audit an empirical LAGS_C surface-integral reconstruction.

This post-run audit is deliberately not an implementation of Code_Aster's
contact residual. It checks whether one transparent full-slave-face integral
is a useful diagnostic against the saved far-cut resultants for the frozen
curved crop and its exact slave-cell-order control.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import sys

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
EVIDENCE = ROOT / "docs/wood-joints-mvp/hypotheses/code-aster-candidate-checks-2026-09-27"
FLAT = EVIDENCE / "contact-3d-flat-attempt02"
DEFAULT_OUTPUT = EVIDENCE / "curved-contact-attempt03/parent-lags-c-reconstruction-audit.json"
SOURCE_TAG = "Code_Aster upstream 17.4.0 tag; pinned runtime binary identity not established"

sys.path.insert(0, str(HERE))
import audit_contact_samples as samples  # noqa: E402
import check_curved_contact as tables  # noqa: E402
from cell_order_reversal_control import compare_paired_attempts as paired  # noqa: E402


RUNS = {
    "baseline": EVIDENCE / "curved-contact-attempt03",
    "slave_cell_order_reversal": EVIDENCE / "curved-contact-cell-order-control-attempt01",
}
INSTS = (5.0, 6.0, 7.0, 11.0)
AUTO_WEIGHTS = (0.054975871827661,) * 3 + (0.111690794839005,) * 3
FLAT_FORCE_LIMIT_N = 0.1


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def expect(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def flat_known_answer() -> dict:
    """Integrate the flat all-active coupon, whose answer is exactly 3000 N."""
    attempt = FLAT
    freeze = json.loads((attempt / "input-freeze.json").read_text())
    execution = json.loads((attempt / "execution.json").read_text())
    expect(execution.get("returncode") == 0 and execution.get("timed_out") is False,
           "flat known-answer native run did not complete")
    for name, expected in freeze["input_sha256"].items():
        expect(sha256(attempt / name) == expected,
               f"flat known-answer frozen input changed: {name}")

    lines = (attempt / "contact_coupon.mail").read_text().splitlines()
    coords: dict[str, np.ndarray] = {}
    tria: dict[str, tuple[str, ...]] = {}
    groups: dict[str, list[str]] = {}
    i = 0
    while i < len(lines):
        section = lines[i].strip()
        if section not in {"COOR_3D", "TRIA6", "GROUP_MA"}:
            i += 1
            continue
        i += 1
        records = []
        while i < len(lines) and lines[i].strip() != "FINSF":
            records.append(lines[i].split())
            i += 1
        if section == "COOR_3D":
            coords = {row[0]: np.asarray([float(v) for v in row[1:]], dtype=float)
                      for row in records}
        elif section == "TRIA6":
            tria = {row[0]: tuple(row[1:]) for row in records}
        else:
            groups.update({row[0]: row[1:] for row in records})
        i += 1

    lag_rows = read_table(attempt / "lagrange.csv", ("INST", "NOEUD", "LAGS_C"))
    lam = {row["NOEUD"]: number(row, "LAGS_C") for row in lag_rows
           if abs(number(row, "INST") - 1.0) <= 1.0e-10}
    node_number = {label: str(int(label[1:])) for label in coords}
    slave_faces = groups["SLAVE"]
    master_faces = groups["MASTER"]
    master_normal = np.zeros(3)
    for face in master_faces:
        p = np.asarray([coords[node] for node in tria[face][:3]])
        area_vector = np.cross(p[1] - p[0], p[2] - p[0])
        expect(area_vector[2] > 0.0, f"flat master orientation changed at {face}")
        master_normal += area_vector
    master_normal /= np.linalg.norm(master_normal)

    total = np.zeros(3)
    rule = samples.quadrature_rule()
    for face in slave_faces:
        conn = tria[face]
        xyz = np.asarray([coords[node] for node in conn])
        lnode = np.asarray([lam[node_number[node]] for node in conn])
        face_total = np.zeros(3)
        for (u, v), weight in zip(rule, AUTO_WEIGHTS):
            l1 = 1.0 - u - v
            shape = samples.shape_values(u, v)
            du = np.asarray((-(4.0*l1-1.0), 4.0*u-1.0, 0.0,
                             4.0*(l1-u), 4.0*v, -4.0*v))
            dv = np.asarray((-(4.0*l1-1.0), 0.0, 4.0*v-1.0,
                             -4.0*u, 4.0*u, 4.0*(l1-v)))
            jac = float(np.linalg.norm(np.cross(du @ xyz, dv @ xyz)))
            face_total += float(shape @ lnode) * master_normal * jac * weight
        total += face_total

    cut = {}
    for name in ("slave_cut_force", "master_cut_force"):
        rows = read_table(attempt / f"{name}.csv", ("INST", "NOEUD", "DX", "DY", "DZ"))
        rows = [row for row in rows if abs(number(row, "INST") - 1.0) <= 1.0e-10]
        cut[name] = np.asarray([math.fsum(number(row, cmp) for row in rows)
                                for cmp in ("DX", "DY", "DZ")])

    errors = {
        "slave_cut_forc_noda": float(np.linalg.norm(total - cut["slave_cut_force"])),
        "opposite_master_cut_forc_noda": float(np.linalg.norm(total + cut["master_cut_force"])),
        "analytic_minus_3000z": float(np.linalg.norm(total - np.asarray((0.0, 0.0, -3000.0)))),
    }
    return {
        "scope": "Flat, fully active, conforming 3-D coupon only; pressure-integral known answer.",
        "attempt": "contact-3d-flat-attempt02",
        "attempt_input_freeze_sha256": sha256(attempt / "input-freeze.json"),
        "slave_face_count": len(slave_faces),
        "slave_reference_area_mm2": float(sum(
            0.5 * np.linalg.norm(np.cross(
                coords[tria[face][1]] - coords[tria[face][0]],
                coords[tria[face][2]] - coords[tria[face][0]]))
            for face in slave_faces)),
        "uniform_lags_c_mpa": sorted(set(round(value, 12) for value in lam.values())),
        "master_outward_normal": master_normal.tolist(),
        "integrated_vector_n": total.tolist(),
        "cut_forc_noda_vectors_n": {key: value.tolist() for key, value in cut.items()},
        "error_norms_n": errors,
        "frozen_flat_force_limit_n": FLAT_FORCE_LIMIT_N,
        "known_answer_checks": {key: value <= FLAT_FORCE_LIMIT_N for key, value in errors.items()},
        "known_answer_status": "PASS" if all(value <= FLAT_FORCE_LIMIT_N for value in errors.values()) else "FAIL",
    }


def read_table(path: Path, required: tuple[str, ...]) -> list[dict[str, str]]:
    return tables.parse_table(path, required)


def number(row: dict[str, str], name: str) -> float:
    return tables.number(row, name)


def cut_resultant(attempt: Path, oracle: dict, filename: str, instant: float) -> np.ndarray:
    rows = tables.canonicalize_nodes(
        read_table(attempt / filename, ("INST", "NOEUD", "DX", "DY", "DZ")),
        oracle, filename)
    selected = [row for row in rows if abs(number(row, "INST") - instant) <= 1.0e-8]
    expect(bool(selected), f"no cut force rows in {filename} at INST={instant:g}")
    return np.asarray([math.fsum(number(row, cmp) for row in selected)
                       for cmp in ("DX", "DY", "DZ")])


def med_lagrange(attempt: Path, mail_coordinates: dict[str, np.ndarray]):
    path = attempt / "parent-contact-med-displacements.json"
    med = json.loads(path.read_text())
    coordinate_labels = list(mail_coordinates)
    med_coordinates = np.asarray(med["coordinates"], dtype=float)
    source_coordinates = np.asarray([mail_coordinates[label] for label in coordinate_labels])
    expect(med_coordinates.shape == source_coordinates.shape,
           f"MED/source coordinate shape mismatch in {attempt.name}")
    max_coordinate_error = float(np.max(np.abs(med_coordinates - source_coordinates)))
    expect(max_coordinate_error == 0.0,
           f"MED/source node order and coordinates differ by {max_coordinate_error:g} mm")
    names = [name for name in med["fields"] if name.endswith("DEPL")]
    expect(len(names) == 1, f"expected one MED DEPL field in {attempt.name}")
    records = med["fields"][names[0]]
    state_by_time = {}
    for record in records:
        expect(record["components"] == ["DX", "DY", "DZ", "LAGS_C"],
               f"unexpected DEPL components in {attempt.name}")
        values = np.asarray(record["values"], dtype=float)
        expect(values.shape == (len(coordinate_labels), 4),
               f"unexpected DEPL field shape at t={record['time']}")
        state_by_time[float(record["time"])] = values
    return coordinate_labels, state_by_time, {
        "field": names[0],
        "state_count": len(state_by_time),
        "mesh_node_count": len(coordinate_labels),
        "max_med_source_coordinate_error_mm": max_coordinate_error,
        "max_med_sdisp_table_component_error": 0.0,
    }


def audit_run(name: str, attempt: Path) -> dict:
    oracle = json.loads((attempt / "geometry-oracle.json").read_text())
    coordinates, slave_faces, master_faces = samples.read_mesh(attempt / "curved_contact.mail")
    labels, state_values, med_info = med_lagrange(attempt, coordinates)
    node_index = {label: index for index, label in enumerate(labels)}

    # Verify all exported slave DEPL/LAGS_C rows against the corresponding
    # MED nodal field values before integrating the field.
    table_rows = tables.canonicalize_nodes(
        read_table(attempt / "SDISP.csv", ("INST", "NOEUD", "DX", "DY", "DZ", "LAGS_C")),
        oracle, "SDISP")
    table_by_time = tables.grouped(table_rows)
    tables.assert_times_with_initial(table_by_time, "SDISP")
    slave_nodes = {item["output_node"] for item in oracle["node_groups"]["SNODE"]}
    max_table_error = 0.0
    for instant in (-1.0, *tuple(float(value) for value in range(12))):
        rows = tables.keyed_rows(tables.rows_at(table_by_time, instant, "SDISP"),
                                 slave_nodes, "SDISP", instant)
        values = state_values[instant]
        for label, row in rows.items():
            i = node_index[label]
            for col, cmp in enumerate(("DX", "DY", "DZ", "LAGS_C")):
                max_table_error = max(max_table_error,
                    abs(number(row, cmp) - float(values[i, col])))
    med_info["max_med_sdisp_table_component_error"] = max_table_error
    expect(max_table_error <= 1.0e-11,
           f"MED/SDISP table identity error is too large: {max_table_error:g}")

    reference_slave = {projector.source_id: projector
                       for projector in samples.build_projectors(coordinates, slave_faces)}
    states = []
    for instant in INSTS:
        values = state_values[instant]
        current = {label: coordinates[label] + values[index, :3]
                   for index, label in enumerate(labels)}
        master_projectors = samples.build_projectors(current, master_faces)
        reconstructed = np.zeros(3)
        integrated_area = 0.0
        max_abs_lags = 0.0
        for face, connectivity in slave_faces:
            face_reference = reference_slave[face]
            xyz_current = np.asarray([current[label] for label in connectivity])
            nodal_lags = np.asarray([values[node_index[label], 3] for label in connectivity])
            max_abs_lags = max(max_abs_lags, float(np.max(np.abs(nodal_lags))))
            for (u, v), weight in zip(samples.quadrature_rule(), AUTO_WEIGHTS):
                bary = (1.0 - u - v, u, v)
                shape = samples.shape_values(u, v)
                point = shape @ xyz_current
                projection, _master_id, _evaluated, _total = samples.global_projection(
                    point, master_projectors)
                _normal, jacobian_reference = face_reference.normal_at_barycentric(bary)
                lags_q = float(shape @ nodal_lags)
                darea_reference = jacobian_reference * weight
                reconstructed += lags_q * projection["normal"] * darea_reference
                integrated_area += darea_reference

        scut = cut_resultant(attempt, oracle, "SCUT.csv", instant)
        mcut = cut_resultant(attempt, oracle, "MCUT.csv", instant)
        tolerance = max(0.05, 0.001 * max(float(np.linalg.norm(scut)),
                                         float(np.linalg.norm(mcut))))
        scut_error = float(np.linalg.norm(reconstructed - scut))
        mcut_error = float(np.linalg.norm(reconstructed + mcut))
        states.append({
            "inst": instant,
            "reconstructed_vector_n": reconstructed.tolist(),
            "scut_forc_noda_vector_n": scut.tolist(),
            "mcut_forc_noda_vector_n": mcut.tolist(),
            "error_to_scut_n": scut_error,
            "error_to_negative_mcut_n": mcut_error,
            "original_rn_to_cut_comparison_scale_n": tolerance,
            "error_below_original_scale_for_context_only": bool(
                scut_error <= tolerance and mcut_error <= tolerance),
            "scale_applied_as_lags_c_acceptance_limit": False,
            "reference_slave_area_mm2": integrated_area,
            "maximum_absolute_nodal_lags_c_mpa": max_abs_lags,
        })
    return {
        "run": name,
        "attempt_path": str(attempt.relative_to(ROOT)),
        "input_freeze_sha256": sha256(attempt / "input-freeze.json"),
        "output_sha256": {filename: sha256(attempt / filename) for filename in (
            "SDISP.csv", "SCUT.csv", "MCUT.csv", "parent-contact-med-displacements.json")},
        "med_identity": med_info,
        "states": states,
        "states_below_original_rn_to_cut_scale_for_context_only": all(
            state["error_below_original_scale_for_context_only"] for state in states),
    }


def pairwise_field_deltas() -> list[dict]:
    loaded = {}
    for name, attempt in RUNS.items():
        med = json.loads((attempt / "parent-contact-med-displacements.json").read_text())
        fields = [value for key, value in med["fields"].items() if key.endswith("DEPL")]
        expect(len(fields) == 1, f"expected one MED DEPL field for {name}")
        loaded[name] = {float(record["time"]): np.asarray(record["values"], dtype=float)
                        for record in fields[0]}
    comparison = []
    for instant in INSTS:
        baseline = loaded["baseline"][instant]
        control = loaded["slave_cell_order_reversal"][instant]
        expect(baseline.shape == control.shape, f"paired MED field shape changed at {instant:g}")
        comparison.append({
            "inst": instant,
            "maximum_absolute_lags_c_difference_mpa": float(
                np.max(np.abs(baseline[:, 3] - control[:, 3]))),
            "maximum_nodal_displacement_difference_mm": float(
                np.max(np.linalg.norm(baseline[:, :3] - control[:, :3], axis=1))),
        })
    return comparison


def audit() -> dict:
    pair_validation = paired.validate_inputs(RUNS["baseline"], RUNS["slave_cell_order_reversal"])
    flat = flat_known_answer()
    expect(flat["known_answer_status"] == "PASS", "flat LAGS_C known-answer control failed")
    run_results = [audit_run(name, path) for name, path in RUNS.items()]
    paired_fields = pairwise_field_deltas()
    return {
        "scope": "Output-only empirical resultant reconstruction on the frozen pair-021 curved crop; not solver residual reproduction or candidate acceptance.",
        "analysis_kind": "Offline post-run calculation. No Code_Aster invocation and no frozen input changes.",
        "source_basis": SOURCE_TAG,
        "provenance": pair_validation,
        "method": "At each frozen AUTO TRIA6 sample on all 95 slave faces, quadratically interpolate saved nodal LAGS_C, multiply by the independently projected deformed master outward normal and the reference slave surface Jacobian, then integrate with the six AUTO point weights. The resulting vector is compared with independently extracted SCUT/MCUT FORC_NODA.",
        "known_answer_control": flat,
        "curved_runs": run_results,
        "paired_curved_field_deltas": paired_fields,
        "source_semantics": {
            "official_manual": "LAGS_C is a contact-force density per unit area on the reference configuration; the v17 methodology recommends against using raw LAGS_C directly for solution-quality postprocessing.",
            "solver_residual": "Pinned-tag source review shows the STANDARD residual uses clipped contact-polygon quadrature, projected augmented traction with an active-set gate, and the ray-gap derivative. It does not equal a full-face six-point AUTO integration of raw LAGS_C times the selected master normal.",
            "active_set": "A geometric JEU threshold is not the solver's active-set rule. The exported node-indexed JEU/CONT slots do not retain the full pointwise augmented active set.",
            "interpretation": "The flat coupon calibrates the sign/area calculation for a uniform, fully active, conforming interface. Curved closure inside the frozen cut tolerance is empirical corroboration only; it does not validate contact pressure, recover the exact solver residual, or resolve the RN output discrepancy.",
            "runtime_identity": "The reviewed upstream v17.4.0 source tag is not byte-matched to the executable inside the pinned image.",
        },
        "source_references": {
            "official_contact_solution": "https://code-aster.org/doc/v17/manuals/man_u/u2/u2.04.04/R_solution.html",
            "official_contact_methodology": "https://code-aster.org/doc/v17/manuals/man_u/u2/u2.04.04/M_thodologies.html",
            "contact_point_lagrange_interpolation": "https://gitlab.com/codeaster/src/-/blob/17.4.0/bibfor/cont_algo/mmeval_prep.F90#L137",
            "active_augmented_pressure_and_residual": "https://gitlab.com/codeaster/src/-/blob/17.4.0/bibfor/cont_elem/laElemCont.F90#L123",
            "augmented_pressure_projection": "https://gitlab.com/codeaster/src/-/blob/17.4.0/bibfor/cont_elem/contact_algebra_module.F90#L59",
            "clipped_polygon_quadrature": "https://gitlab.com/codeaster/src/-/blob/17.4.0/bibfor/cont_elem/getQuadCont.F90#L86",
            "standard_contact_residual": "https://gitlab.com/codeaster/src/-/blob/17.4.0/bibfor/cont_elem/laVect_ct_std.F90#L101",
            "reference_slave_jacobian": "https://gitlab.com/codeaster/src/-/blob/17.4.0/bibfor/cont_elem/mmmjac.F90#L97",
            "ray_gap_derivative": "https://gitlab.com/codeaster/src/-/blob/17.4.0/bibfor/cont_elem/contact_module.F90#L1094",
        },
        "status": "EMPIRICAL_CLOSURE_ONLY",
        "mechanical_acceptance": "NOT_INFERRED",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    report = audit()
    report["audit_script_sha256"] = sha256(Path(__file__).resolve())
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({"status": report["status"],
                      "output": str(args.output),
                      "flat_known_answer": report["known_answer_control"]["known_answer_status"],
                      "curved_checks": [
                          {"run": item["run"], "states_below_original_scale_for_context_only": item["states_below_original_rn_to_cut_scale_for_context_only"],
                           "errors_n": [state["error_to_scut_n"] for state in item["states"]]}
                          for item in report["curved_runs"]]}, indent=2))


if __name__ == "__main__":
    main()
