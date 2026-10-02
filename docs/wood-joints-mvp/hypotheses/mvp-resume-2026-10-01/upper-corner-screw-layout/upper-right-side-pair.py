"""Evaluate six frozen side-interface wrenches with one compatible rigid host.

The frozen rail-pair implementation supplies the unchanged local mechanics in
a private imported module. This adapter supplies current side geometry, source
rows, a declared interface midpoint datum, and a separate receipt.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import math
import sys
from pathlib import Path

import numpy as np
import scipy

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
RAIL = HERE / "upper-right-rail-pair.py"
RAIL_SHA256 = "4243b53bbb7377753f0b1fdd73fa1aa6c80e1a96c99d428def88e82a899e6f96"
CASES = ["a12-rear", "a12-forward", "a12-left", "k12-right", "k12-rear", "a1-rear"]
AXES = [f"top_outer/clip_single_top_right_2/side_{number}" for number in (1, 2)]
HOST, CLEAT = "base_side_right", "top_outer_right_cleat"
DATUM = np.array([1127.1250000000005, 1405.0269362288576, 2125.1250400799])
LENGTH, DIAMETER, GAP = 177.8, 7.9375, 0.53125
KWOOD, KHEAD, EBOLT = 20.0, 10000.0, 200000.0
AREA = math.pi * DIAMETER**2 / 4
AXIAL_COMPLIANCE = LENGTH / (EBOLT * AREA)
FAMILY = {"host_length_mm": 88.9, "cleat_length_mm": 88.9, "diameter_mm": DIAMETER,
          "bore_mm": 9.0, "washer_ID_max_mm": 9.906, "washer_OD_min_mm": 22.0472,
          "flat_radius_mm": 6.0}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def import_frozen(path, module_name):
    sys.dont_write_bytecode = True
    spec = importlib.util.spec_from_file_location(module_name, path)
    require(spec is not None and spec.loader is not None, f"pure helper unavailable: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_sources():
    require(sha(RAIL) == RAIL_SHA256, "frozen rail-pair helper differs")
    mechanics = import_frozen(RAIL, "frozen_side_pair_mechanics")
    pins = {RAIL: RAIL_SHA256, **mechanics.PINS}
    for path, expected in pins.items():
        require(sha(path) == expected, f"frozen source differs: {path}")
    helper = import_frozen(mechanics.HELPER, "frozen_side_pair_contact")
    require((helper.LENGTH, helper.E_BOLT, helper.K_HEAD) == (LENGTH, EBOLT, KHEAD),
            "frozen contact helper constants differ")
    # Configure only this private module instance. Its source and the rail
    # packet remain unchanged; no source-loading or main function is called.
    for name, value in {"AXES": AXES, "HOST": HOST, "CLEAT": CLEAT, "DATUM": DATUM,
                        "LENGTH": LENGTH, "DIAMETER": DIAMETER, "GAP": GAP,
                        "KWOOD": KWOOD, "KHEAD": KHEAD, "EBOLT": EBOLT,
                        "AREA": AREA, "AXIAL_COMPLIANCE": AXIAL_COMPLIANCE,
                        "FAMILY": FAMILY}.items():
        setattr(mechanics, name, value)
    model = mechanics.read(mechanics.MODEL)
    identities = mechanics.read(mechanics.ROWS)
    comparison = mechanics.read(mechanics.COMPARISON)
    component = mechanics.read(mechanics.COMPONENT)
    by_row = {row["row"]: row for row in identities}
    require(comparison["response_sha256"] == pins[mechanics.RESPONSE], "response metadata binding differs")
    require([state["case_id"] for state in comparison["states"] if state["gap_scale"] == 1.0] == CASES,
            "nominal case order differs")
    require(not comparison["complete_joint_acceptance"] and not comparison["physical_release"],
            "source claims joint acceptance or release")
    require(component["source_comparison_sha256"] == pins[mechanics.COMPARISON]
            and component["source_response_sha256"] == pins[mechanics.RESPONSE], "component force binding differs")
    selected = sorted((row for row in identities if
                       {row["ownership"]["first_body"], row["ownership"]["second_body"]} == {HOST, CLEAT}),
                      key=lambda row: row["row"])
    require([row["row"] for row in selected] == list(range(1812, 1816)) + list(range(1852, 1870)),
            "side-interface row census differs")
    require(all(row["ownership"]["first_body"] == HOST for row in selected), "current side row ownership differs")
    face = [row for row in selected if row["ownership"]["role"] == "timber_or_panel_contact"]
    ties = [row for row in selected if row["ownership"]["role"] == "physical_bolt_outer_seat_tension"]
    require(len(face) == 16 and len(ties) == 2, "side face or tie census differs")
    n = np.array(ties[0]["ownership"]["direction_global_xyz"])
    require(np.allclose(n, [-1.0, 0.0, 0.0], atol=1e-12, rtol=0), "side bolt axis differs")
    basis = np.column_stack(([0.0, 0.0, 1.0], np.cross(n, [0.0, 0.0, 1.0])))
    require(np.allclose(basis.T @ basis, np.eye(2), atol=1e-12), "side basis is not orthonormal")
    finished_area = sum(row["contact_area_mm2"] for row in face)
    face_centroid = sum(row["contact_area_mm2"]*np.array(row["ownership"]["point_mm"])
                        for row in face) / finished_area
    require(math.isclose(finished_area, 16594.85549769336, abs_tol=1e-7, rel_tol=0), "finished side area differs")
    require(abs(float(n @ (face_centroid - DATUM))) <= 1e-7, "finished centroid leaves the declared interface plane")
    for row in face:
        require(np.allclose(row["ownership"]["direction_global_xyz"], -n, atol=1e-12), "side face normal differs")
        require(math.isclose(row["law"]["stiffness_N_per_mm"]/row["contact_area_mm2"], 100.0, rel_tol=1e-10),
                "existing face stiffness differs")
    revised = {record["axis_id"]: record for group in model["proposed_corner_axes"]
               if group["block"] == CLEAT for record in group["axes"]}
    bolts = []
    for number, axis_id in enumerate(AXES):
        record = revised[axis_id]
        require(record["wood_grip_mm"] == LENGTH and record["nominal_bolt_diameter_mm"] == DIAMETER
                and record["proposed_CAD_bore_envelope_mm"] == FAMILY["bore_mm"], "corrected side geometry differs")
        lateral = [row for row in selected if row["row_id"].rpartition("/")[0] == axis_id
                   and row["ownership"]["role"] == "candidate_bolt_lateral_plane"]
        tie = next(row for row in ties if row["row_id"] == axis_id + "/outer-seat-axial-tie")
        require(len(lateral) == 2 and np.allclose(tie["ownership"]["direction_global_xyz"], n, atol=1e-12),
                "side bolt rows differ")
        relative_gap = next(record["relative_radial_gap_mm"] for record in comparison["clearance_planes"]
                            if record["plane_id"] == lateral[0]["row_id"])
        require(math.isclose(relative_gap, 2*GAP, abs_tol=1e-10), "source gap differs from the two receiver gaps")
        bolts.append({"axis_id": axis_id, "number": number,
                      "interface_point_xyz_mm": lateral[0]["ownership"]["point_mm"],
                      "source_component_rows": [row["row"] for row in lateral], "source_tie_row": tie["row"]})
    midpoint = np.mean([bolt["interface_point_xyz_mm"] for bolt in bolts], axis=0)
    require(np.allclose(midpoint, DATUM, atol=1e-9, rtol=0), "source interface midpoint datum differs")
    body_index = model["body_names"].index(HOST)
    coordinates = model["physical_node_coordinates_mm"]
    body_datum = np.mean([coordinates[str(node)] for node in sorted(set(model["body_nodes"][HOST]))], axis=0)
    raw_rows = [row["row"] for row in selected]
    states = []
    with np.load(mechanics.OPERATORS, allow_pickle=False) as operators, np.load(mechanics.RESPONSE, allow_pickle=False) as response:
        dbody = operators["D"][raw_rows, 6*body_index:6*body_index + 6]
        for index, row in enumerate(selected):
            require(np.allclose(dbody[index, :3], -np.array(row["ownership"]["direction_global_xyz"]), atol=1e-12, rtol=0),
                    "D translation sign differs from row ownership")
        for case_id in CASES:
            raw = response[case_id + "_gap_raw_force_n"]
            force = -dbody[:, :3].T @ raw[raw_rows]
            moment = -1000*dbody[:, 3:6].T @ raw[raw_rows] + np.cross(body_datum - DATUM, force)
            actions = [np.array(row["ownership"]["direction_global_xyz"])*raw[row["row"]] for row in selected]
            point_force = np.sum(actions, axis=0)
            point_moment = sum(np.cross(np.array(row["ownership"]["point_mm"]) - DATUM, action)
                               for row, action in zip(selected, actions))
            require(np.max(np.abs(force - point_force)) <= 1e-7, "D and point-force sums differ")
            originals = []
            for bolt in bolts:
                witness = next(record for record in component["states"]
                               if record["case_id"] == case_id and record["axis_id"] == bolt["axis_id"])
                host_lateral = sum(np.array(by_row[row]["ownership"]["direction_global_xyz"])*raw[row]
                                   for row in bolt["source_component_rows"])
                tension = float(raw[bolt["source_tie_row"]])
                require(math.isclose(tension, witness["tension_n"], abs_tol=1e-8)
                        and math.isclose(float(np.linalg.norm(host_lateral)), witness["lateral_n"], abs_tol=1e-8),
                        "original side bolt comparison differs")
                originals.append({"axis_id": bolt["axis_id"], "signed_T_n": tension, "V_n": witness["lateral_n"],
                                  "signed_plane_components_n": raw[bolt["source_component_rows"]].tolist(),
                                  "force_on_host_xyz_n": host_lateral.tolist()})
            states.append({"case_id": case_id, "source_connector_wrench_on_host_n_nmm": np.r_[force, moment].tolist(),
                           "external_drive_wrench_n_nmm": (-np.r_[force, moment]).tolist(),
                           "D_point_force_residual_n": (force - point_force).tolist(),
                           "retained_source_free_couple_nmm": (moment - point_moment).tolist(),
                           "source_face_compression_n": float(sum(raw[row["row"]] for row in face)),
                           "source_face_cells": [{"row": row["row"], "compression_n": float(raw[row["row"]]),
                                                  "stiffness_n_per_mm": row["law"]["stiffness_N_per_mm"]} for row in face],
                           "source_individual_bolts": originals})
    pins[Path(__file__).resolve()] = sha(Path(__file__).resolve())
    return mechanics, helper, bolts, face, n, basis, states, body_datum, face_centroid, pins


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    output = parser.parse_args().output.resolve()
    require(not output.exists(), f"output already exists: {output}")
    mechanics, helper, source_bolts, face, n, basis, sources, body_datum, face_centroid, pins = load_sources()
    blocks, cells = mechanics.model_matrices(helper, source_bolts, face, n, basis)
    output.mkdir(parents=True, exist_ok=False)
    (output / ".gitignore").write_text("*\n")
    (output / "producer.py.snapshot").write_bytes(Path(__file__).read_bytes())
    states, beam_rows, failure = [], [], None
    try:
        for source in sources:
            debug = {}
            state, fields = mechanics.solve_case(helper, blocks, cells, n, basis, source, debug)
            states.append(state)
            beam_rows.extend({"case_id": source["case_id"], **field} for field in fields)
        for path, expected in pins.items():
            require(sha(path) == expected, f"source changed during side-pair calculation: {path}")
    except (ValueError, RuntimeError, OSError, np.linalg.LinAlgError) as error:
        failure = {"case_id": source["case_id"], "source_wrench": source["external_drive_wrench_n_nmm"],
                   "last_accepted_state": debug, "error": str(error), "incompatibility_proved": False}
    if states:
        mechanics.write_csv(output / "states.csv", [{"case_id": state["case_id"],
            "mixed_scaled_gradient_maximum_n": state["mixed_scaled_gradient_maximum_n"],
            "wrench_residual_n_nmm": state["interface_wrench_balance_residual_n_nmm"],
            "host_translation_xyz_mm": state["host_translation_at_face_datum_xyz_mm"],
            "host_rotation_xyz_rad": state["host_rotation_xyz_rad"],
            "tangent_nullity_at_relative_1e_12": state["tangent_nullity_at_relative_1e_12"],
            "elastic_bolt_hypothesis_exceeded": state["elastic_bolt_hypothesis_exceeded"]} for state in states])
        mechanics.write_csv(output / "bolt-states.csv", [{"case_id": state["case_id"], **{key: bolt[key] for key in (
            "axis_id", "compatible_T_n", "source_original_T_n", "source_original_V_n", "bore_V_resultant_n",
            "normal_opening_mm", "projected_shortening_mm", "axial_compatibility_residual_mm",
            "wrench_on_host_at_face_datum_n_nmm")}} for state in states for bolt in state["bolts"]])
        mechanics.write_csv(output / "beam-fields.csv", beam_rows)
        mechanics.write_csv(output / "bore-fields.csv", [{"case_id": state["case_id"], "axis_id": bolt["axis_id"], **field}
                                                       for state in states for bolt in state["bolts"] for field in bolt["bore_fields"]])
        mechanics.write_csv(output / "face-cells.csv", [{"case_id": state["case_id"], **field}
                                                      for state in states for field in state["face_cells"]])
    result = {"schema": "upper_right_common_host_side_pair_sensitivity/v1",
              "status": "STOP" if failure else "FINITE_SHARED_HOST_SIDE_PAIR_HYPOTHESIS",
              "counts": {"source_cases": 6, "completed_cases": len(states), "bolts": 2, "face_cells": 16, "scaled_unknowns": 142},
              "case_ids": CASES, "axis_ids": AXES, "states": states, "failure": failure,
              "model": {"geometry": FAMILY, "host": HOST, "fixed_cleat": CLEAT, "face_datum_xyz_mm": DATUM.tolist(),
                        "face_datum_definition": "Midpoint of the two current side interface points; fixed independently of finished contact-area weighting.",
                        "finished_contact_area_centroid_xyz_mm": face_centroid.tolist(),
                        "finished_contact_area_mm2": sum(row["contact_area_mm2"] for row in face),
                        "source_body_datum_xyz_mm": body_datum.tolist(), "bolt_axis_head_to_nut_xyz": n.tolist(),
                        "transverse_basis_xyz": basis.tolist(), "Kwood_mpa_per_mm_hypothesis": KWOOD,
                        "Khead_mpa_per_mm_hypothesis": KHEAD, "Ebolt_mpa_hypothesis": EBOLT,
                        "face_stiffness_mpa_per_mm": 100.0, "radial_gap_mm": GAP, "beam_elements_per_receiver": 8,
                        "bore_gauss_points_per_element": 3, "contact_gauss_radii": 8, "contact_uniform_azimuths": 32,
                        "mixed_scaled_gradient_tolerance_n": mechanics.GRADIENT_TOLERANCE,
                        "local_moment_tolerance_nmm": LENGTH*mechanics.GRADIENT_TOLERANCE,
                        "whole_host_force_component_tolerance_n": mechanics.FORCE_TOLERANCE,
                        "whole_host_moment_component_tolerance_nmm": mechanics.MOMENT_TOLERANCE,
                        "axial_compatibility_tolerance_mm": 1e-9, "conditional_Fyb_comparison_mpa": mechanics.FYB_SCENARIO,
                        "reused_mechanics": "Frozen rail-pair model_matrices and solve_case with their unchanged energy, derivatives, iteration bound, convergence checks and contact helpers.",
                        "contact_rotation_hypothesis": "The circular quadrature rotates with the two-component slope; fixed-T contact is explicitly isotropic.",
                        "axial_energy": "max_T>=0[T*(qnormal + .5 z.Kg_unit.z) - .5 T^2 L/(EA) + Whead + Wnut]",
                        "initialization_scope": "Transverse gap activation and a minimum-norm common-host fit to two source-T closure seeds and one existing face compression provide numerical seeds only."},
              "limits": ["This shared rigid side member and two bolts form one finite local model. The cleat is fixed; the rail interface and full frame are not solved.",
                         "The exact current 22-row connector wrench supplies the external drive. Gravity is not added again; individual frozen bolt forces may redistribute compatibly.",
                         "Face-cell points, areas and unilateral stiffnesses are unchanged. Wood, head-seat and smooth-bolt elastic laws remain hypotheses without preload or friction.",
                         "Rigid washers supply contact moments without washer bending stress, material resistance or an actual bearing-face profile.",
                         "The nominal smooth-section stress proxy compares sectional envelopes at the same axial location. Exceeding the conditional steel comparison invalidates the elasticity hypothesis, not an observed build.",
                         "Bore pressures and beam stresses are finite quadrature/element evaluations. Actual wood, threads, head/nut seats and delivered hardware remain unqualified.",
                         "The local numerical criteria do not change or close the adopted 47-criterion authority. A converged representative pose is not a full-frame motion envelope or complete joint pass.",
                         "A numerical STOP preserves the last accepted iterate and does not prove mechanical incompatibility. No relaxed retry or additional law sweep is performed.",
                         "Only frozen current forces are consumed. No frame solve, native solve, CAD operation or historical force/acceptance transfer occurs."],
              "source_sha256": {str(path.relative_to(ROOT)): expected for path, expected in sorted(pins.items())},
              "runtime": {"python": sys.version.split()[0], "numpy": np.__version__, "scipy": scipy.__version__},
              "actual_washer_stress_mpa": None, "actual_washer_capacity_n": None, "actual_hardware_capacity_n": None,
              "coupled_joint_resistance_n": None, "complete_joint_acceptance": False, "physical_release": False}
    hashes = {path.name: sha(path) for path in output.iterdir()}
    result["output_sha256"] = hashes.copy()
    mechanics.dump(output / "checks.json", result)
    hashes["checks.json"] = sha(output / "checks.json")
    mechanics.dump(output / "source-pins.json", {"source_sha256": result["source_sha256"], "output_sha256": hashes,
                                                "complete_joint_acceptance": False, "physical_release": False})
    for path, expected in pins.items():
        require(sha(path) == expected, f"source changed before final receipt: {path}")
    print(json.dumps({"status": result["status"], "completed_cases": len(states), "checks_sha256": hashes["checks.json"]}))
    if failure:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
