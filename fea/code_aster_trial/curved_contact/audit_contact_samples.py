#!/usr/bin/env python3
"""Independently compare CONT_NOEU/JEU with its AUTO TRIA6 sample gaps.

This is a post-run audit. It does not invoke Code_Aster and does not use JEU
to select a contact sample. The source-defined AUTO rule and source write
order choose the sample associated with each output node slot; native PROJ is
used only as a separate check of that mapping.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys

import numpy as np


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(HERE))
import check_curved_contact as tables  # noqa: E402
import generate as geometry  # noqa: E402

DEFAULT_ATTEMPT = ROOT / "docs/wood-joints-mvp/hypotheses/code-aster-candidate-checks-2026-09-27/curved-contact-attempt03"
DEFAULT_OUTPUT = DEFAULT_ATTEMPT / "parent-contact-sample-gap-review.json"
DEFAULT_MED = DEFAULT_ATTEMPT / "parent-contact-med-displacements.json"
SOURCE_TAG = "Code_Aster upstream 17.4.0 source tag; runtime binary byte identity not established"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_mesh(path: Path):
    lines = path.read_text().splitlines()
    coordinates: dict[str, np.ndarray] = {}
    index = lines.index("COOR_3D") + 1
    while lines[index].strip() != "FINSF":
        fields = lines[index].split()
        if len(fields) != 4:
            raise ValueError(f"malformed coordinate record: {lines[index]}")
        coordinates[fields[0]] = np.asarray([float(value) for value in fields[1:]])
        index += 1

    index = lines.index("TRIA6") + 1
    faces: list[tuple[str, tuple[str, ...]]] = []
    while lines[index].strip() != "FINSF":
        fields = lines[index].split()
        if len(fields) != 7:
            raise ValueError(f"malformed TRIA6 record: {lines[index]}")
        faces.append((fields[0], tuple(fields[1:])))
        index += 1
    slave = [face for face in faces if face[0].startswith("CS")]
    master = [face for face in faces if face[0].startswith("CM")]
    if len(slave) != 95 or len(master) != 88:
        raise ValueError(f"unexpected crop face counts: slave={len(slave)}, master={len(master)}")
    return coordinates, slave, master


def rows_by_label(path: Path, required: tuple[str, ...], oracle, name: str):
    rows = tables.parse_table(path, required)
    return tables.canonicalize_nodes(rows, oracle, name)


def quadrature_rule():
    # mmgaus.F90 fpgtri(4), in its point order; mmnumn/mmpnoe associate
    # AUTO point iptm with the same local TRIA6 connectivity position.
    b = 0.091576213509771
    a = 0.445948490915965
    uv = ((b, b), (1.0 - 2.0 * b, b), (b, 1.0 - 2.0 * b),
          (a, 1.0 - 2.0 * a), (a, a), (1.0 - 2.0 * a, a))
    return uv


def shape_values(u: float, v: float) -> np.ndarray:
    l1 = 1.0 - u - v
    return np.asarray((l1 * (2.0 * l1 - 1.0),
                       u * (2.0 * u - 1.0),
                       v * (2.0 * v - 1.0),
                       4.0 * l1 * u, 4.0 * u * v, 4.0 * v * l1))


def build_projectors(coordinates, faces):
    projectors = []
    for face_id, connectivity in faces:
        xyz = [coordinates[label] for label in connectivity]
        # The crop writer orders both contact faces outward from their parent
        # C3D10 cell, so the corner cross product fixes the normal direction.
        parent_direction = np.cross(xyz[1] - xyz[0], xyz[2] - xyz[0])
        projectors.append(geometry.CurvedFace(face_id, 0, connectivity, xyz,
                                              parent_direction))
    return projectors


def read_med_displacements(path: Path, coordinate_labels, source_coordinates):
    """Read already-extracted MED nodal displacements in frozen mesh order."""
    med = json.loads(path.read_text())
    med_coordinates = np.asarray(med["coordinates"], dtype=float)
    mail_coordinates = np.asarray([source_coordinates[label] for label in coordinate_labels])
    if med_coordinates.shape != mail_coordinates.shape:
        raise ValueError("MED and frozen mesh coordinate arrays have different shapes")
    coordinate_error = float(np.max(np.abs(med_coordinates - mail_coordinates)))
    if coordinate_error != 0.0:
        raise ValueError(f"MED mesh node order/coordinates differ from .mail by {coordinate_error:g} mm")
    field_names = [name for name in med["fields"] if name.endswith("DEPL")]
    if len(field_names) != 1:
        raise ValueError(f"expected one saved DEPL field, found {field_names}")
    field_name = field_names[0]
    states = {}
    components = None
    for state in med["fields"][field_name]:
        components = state["components"]
        if components[:3] != ["DX", "DY", "DZ"]:
            raise ValueError(f"unexpected DEPL components: {components}")
        values = np.asarray(state["values"], dtype=float)
        if values.shape[0] != len(coordinate_labels) or values.shape[1] < 3:
            raise ValueError(f"malformed DEPL values at time {state['time']}")
        time = float(state["time"])
        states[time] = {label: values[index, :3]
                        for index, label in enumerate(coordinate_labels)}
    return states, {"field_name": field_name, "state_count": len(states),
                    "mesh_nodes": len(coordinate_labels),
                    "max_med_vs_mail_coordinate_error_mm": coordinate_error,
                    "components": components}


def global_projection(point: np.ndarray, projectors):
    candidates = sorted((projector.bezier_aabb_distance(point), index, projector)
                        for index, projector in enumerate(projectors))
    best = None
    evaluated = 0
    for lower_bound, _, projector in candidates:
        if best is not None and lower_bound >= best[0]["distance_mm"]:
            break
        projected = projector.project(point)
        evaluated += 1
        if best is None or projected["distance_mm"] < best[0]["distance_mm"]:
            best = (projected, projector)
    if best is None:
        raise RuntimeError("no master projection candidate converged")
    return best[0], best[1].source_id, evaluated, len(projectors)


def audit(attempt: Path, med_path: Path) -> dict:
    mail = attempt / "curved_contact.mail"
    oracle_path = attempt / "geometry-oracle.json"
    contact_path = attempt / "CONTACT.csv"
    displacement_path = attempt / "SDISP.csv"
    oracle = json.loads(oracle_path.read_text())
    coordinates, slave_faces, master_faces = read_mesh(mail)
    node_items = [item for values in oracle["node_groups"].values() for item in values]
    label_to_source = {item["output_node"]: int(item["source_node"]) for item in node_items}
    if len(label_to_source) != len(node_items):
        raise ValueError("duplicate output node labels in frozen oracle")

    contact = rows_by_label(contact_path,
        ("INST", "NOEUD", "JEU", "CONT", "PROJ_X", "PROJ_Y", "PROJ_Z"),
        oracle, "CONTACT")
    displacement = rows_by_label(displacement_path,
        ("INST", "NOEUD", "DX", "DY", "DZ"), oracle, "SDISP")
    contact_by_time: dict[float, dict[str, dict[str, str]]] = {}
    for row in contact:
        instant = tables.number(row, "INST")
        contact_by_time.setdefault(instant, {})[row["NOEUD"]] = row
    displacement_by_time: dict[float, dict[str, np.ndarray]] = {}
    for row in displacement:
        instant = tables.number(row, "INST")
        displacement_by_time.setdefault(instant, {})[row["NOEUD"]] = np.asarray(
            [tables.number(row, component) for component in ("DX", "DY", "DZ")])

    coordinate_labels = list(coordinates)
    med_displacements, med_identity = read_med_displacements(
        med_path, coordinate_labels, coordinates)
    rule = quadrature_rule()
    med_vs_table_errors = []
    for instant, table_nodes in displacement_by_time.items():
        if instant not in med_displacements:
            raise ValueError(f"SDISP time {instant:g} is absent from MED DEPL history")
        for node_label, table_vector in table_nodes.items():
            med_vs_table_errors.append(float(np.linalg.norm(
                med_displacements[instant][node_label] - table_vector)))
    if not med_vs_table_errors:
        raise ValueError("no SDISP/MED values available for displacement cross-check")

    report_states = []

    # mmmres writes each contact-sample value directly to its associated node
    # slot. Iteration through the frozen SLAVE mesh records and iptm order
    # reproduces the source's last-write rule for shared nodes. The saved MED
    # displacement field supplies deformed coordinates for both bodies.
    for instant in sorted(value for value in med_displacements if 0.0 <= value <= 11.0):
        if instant not in contact_by_time or instant not in displacement_by_time:
            raise ValueError(f"missing CONTACT or SDISP output at INST={instant:g}")
        nodal_displacements = med_displacements[instant]
        current_coordinates = {label: coordinates[label] + nodal_displacements[label]
                               for label in coordinate_labels}
        projectors = build_projectors(current_coordinates, master_faces)

        latest_by_node = {}
        visits_by_node: dict[str, list[dict]] = {}
        all_sample_rows = []
        projection_by_sample = {}
        for face_order, (face_id, connectivity) in enumerate(slave_faces, start=1):
            xyz = np.asarray([current_coordinates[label] for label in connectivity])
            for iptm, (u, v) in enumerate(rule, start=1):
                sample_xyz = shape_values(u, v) @ xyz
                node_label = connectivity[iptm - 1]
                visit = {
                    "mesh_face": face_id,
                    "face_order_1based": face_order,
                    "iptm_1based": iptm,
                    "quadrature_uv": [u, v],
                    "associated_node": node_label,
                    "sample_xyz_mm": sample_xyz,
                }
                latest_by_node[node_label] = visit
                visits_by_node.setdefault(node_label, []).append(visit)
                projected, master_id, evaluated, total = global_projection(sample_xyz, projectors)
                projection_by_sample[(face_id, iptm)] = (projected, master_id, evaluated, total)
                all_sample_rows.append({
                    "mesh_face": face_id,
                    "face_order_1based": face_order,
                    "iptm_1based": iptm,
                    "associated_node": node_label,
                    "independent_master_face": master_id,
                    "independent_signed_gap_mm": float(projected["signed_gap_mm"]),
                    "candidate_master_faces_evaluated": evaluated,
                    "candidate_master_faces_total": total,
                })

        output_nodes = set(contact_by_time[instant])
        if set(latest_by_node) != output_nodes:
            raise ValueError(f"source sample-node coverage differs at INST={instant:g}: "
                             f"source={len(latest_by_node)}, output={len(output_nodes)}")

        state_rows = []
        for node_label in sorted(output_nodes):
            row = contact_by_time[instant][node_label]
            visit = latest_by_node[node_label]
            point = visit["sample_xyz_mm"]
            projection, master_id, evaluated, total = projection_by_sample[
                (visit["mesh_face"], visit["iptm_1based"])]
            native_projection = np.asarray([tables.number(row, component)
                for component in ("PROJ_X", "PROJ_Y", "PROJ_Z")])
            projection_delta = projection["point"] - native_projection
            projection_error = float(np.linalg.norm(projection_delta))
            native_jeu = tables.number(row, "JEU")
            independent_gap = float(projection["signed_gap_mm"])
            gap_error = native_jeu - independent_gap
            visits = visits_by_node[node_label]
            state_rows.append({
                "output_node": node_label,
                "source_node": label_to_source[node_label],
                "mesh_face": visit["mesh_face"],
                "face_order_1based": visit["face_order_1based"],
                "iptm_1based": visit["iptm_1based"],
                "associated_sample_xyz_mm": [float(value) for value in point],
                "visit_count_for_slot": len(visits),
                "independent_master_face": master_id,
                "independent_master_projection_xyz_mm": [float(value) for value in projection["point"]],
                "native_master_projection_xyz_mm": [float(value) for value in native_projection],
                "projection_coordinate_difference_mm": projection_error,
                "independently_computed_signed_gap_mm": independent_gap,
                "native_jeu_mm": native_jeu,
                "native_minus_independent_gap_mm": gap_error,
                "status_cont": tables.number(row, "CONT"),
                "candidate_master_faces_evaluated": evaluated,
                "candidate_master_faces_total": total,
            })

        frozen_gap_limit = oracle["frozen_screen_thresholds"][
            "open_state_maximum_absolute_gap_error_mm"]
        max_gap = max(abs(item["native_minus_independent_gap_mm"]) for item in state_rows)
        min_gap = min(item["independently_computed_signed_gap_mm"] for item in state_rows)
        min_all_sample_gap = min(item["independent_signed_gap_mm"] for item in all_sample_rows)
        max_all_sample_penetration = max(0.0, -min_all_sample_gap)
        max_projection = max(item["projection_coordinate_difference_mm"] for item in state_rows)
        worst = max(state_rows, key=lambda item: abs(item["native_minus_independent_gap_mm"]))
        control_displacement = next(item["control_displacement_mm"]
            for item in oracle["frozen_motion"]["time_mm_control_displacement"]
            if int(item["time"]) == int(instant))
        active_rows = [item for item in state_rows if item["status_cont"] > 0.0]
        active_gap_limit = oracle["frozen_screen_thresholds"]["active_node_maximum_absolute_gap_mm"]
        active_slot_violations = [item["output_node"] for item in active_rows
                                  if abs(item["native_jeu_mm"]) > active_gap_limit]
        frozen_open_controls = [float(value) for value in oracle["frozen_motion"][
            "opening_and_separation_states"]]
        is_frozen_open_state = any(abs(control_displacement - value) <= 1.0e-12
                                   for value in frozen_open_controls)
        penetration_limit = oracle["frozen_screen_thresholds"][
            "all_slave_nodes_maximum_penetration_mm"]
        all_sample_penetration_pass = max_all_sample_penetration <= penetration_limit
        if is_frozen_open_state:
            state_gap_screen = (max_gap <= frozen_gap_limit and
                                min_all_sample_gap >= 0.0 and
                                all(item["status_cont"] == 0.0 for item in state_rows))
            state_gap_basis = "Open-state sample-to-JEU comparison, positive gaps at all 570 samples, and open status at all 218 selected slots."
        else:
            state_gap_screen = (bool(active_rows) and not active_slot_violations and
                                all_sample_penetration_pass)
            state_gap_basis = "Contact-state selected active slots satisfy the frozen |JEU| limit and every one of 570 sampled points satisfies the frozen penetration limit. JEU-to-independent-gap difference is also reported as an output consistency diagnostic."
        state_report = {
            "inst": instant,
            "control_displacement_mm": control_displacement,
            "frozen_state_classification": "open" if is_frozen_open_state else "contact",
            "gap_screen_basis": state_gap_basis,
            "source_selected_sample_slots": len(state_rows),
            "source_sample_visits": len(all_sample_rows),
            "shared_node_slots_with_multiple_contact_sample_visits": sum(
                len(values) > 1 for values in visits_by_node.values()),
            "all_sample_gap_count": len(all_sample_rows),
            "minimum_independent_gap_all_570_samples_mm": min_all_sample_gap,
            "maximum_penetration_all_570_samples_mm": max_all_sample_penetration,
            "frozen_all_slave_penetration_limit_mm": oracle["frozen_screen_thresholds"][
                "all_slave_nodes_maximum_penetration_mm"],
            "all_sample_penetration_screen_same_frozen_numeric_limit":
                "PASS" if all_sample_penetration_pass else "FAIL",
            "active_selected_output_slot_count": len(active_rows),
            "active_selected_slot_native_jeu_violations": active_slot_violations,
            "minimum_independent_gap_mm": min_gap,
            "maximum_absolute_native_projection_coordinate_difference_mm": max_projection,
            "maximum_absolute_sample_matched_gap_error_mm": max_gap,
            "maximum_absolute_active_native_jeu_mm": max(
                (abs(item["native_jeu_mm"]) for item in active_rows), default=0.0),
            "frozen_active_native_jeu_limit_mm": active_gap_limit,
            "worst_gap_row": worst,
            "frozen_open_gap_error_limit_mm": frozen_gap_limit,
            "sample_matched_gap_screen": "PASS" if state_gap_screen else "FAIL",
            "rows": state_rows,
            "all_570_sample_gaps": all_sample_rows,
        }
        report_states.append(state_report)
    return {
        "scope": "Post-run re-pairing audit of all saved curved-contact states; not a native rerun or joint acceptance.",
        "source_basis": SOURCE_TAG,
        "source_references": {
            "AUTO_TRIA6_six_point_rule": "https://gitlab.com/codeaster/src/-/blob/17.4.0/bibfor/cont_util/mmgaus.F90#L155",
            "AUTO_rule_selection_for_TR6": "https://gitlab.com/codeaster/src/-/blob/17.4.0/bibfor/algorith/mmelin.F90#L57",
            "integration_point_to_node_mapping": "https://gitlab.com/codeaster/src/-/blob/17.4.0/bibfor/cont_algo/mmapma.F90#L98",
            "AUTO_point_to_connectivity_mapping": "https://gitlab.com/codeaster/src/-/blob/17.4.0/bibfor/algorith/mmpnoe.F90#L65",
            "contact_result_writer": "https://gitlab.com/codeaster/src/-/blob/17.4.0/bibfor/cont_algo/mmmres.F90#L200",
            "continuous_gap_is_evaluated_at_surface_integration_points": "https://code-aster.org/doc/v17/manuals/man_u/u2/u2.04.04/Appariement.html",
            "contact_output_methodology": "https://code-aster.org/doc/v17/manuals/man_u/u2/u2.04.04/M_thodologies.html",
        },
        "source_runtime_identity_limit": "The official 17.4.0 source tag was inspected; it has not been verified byte-for-byte against the pinned container executable.",
        "method": "For each saved state, enumerate six Code_Aster AUTO TRIA6 contact samples on every frozen slave face. Interpolate each sample from deformed coordinates in the saved MED DEPL field, compute its nearest point on all 88 deformed master TRIA6 faces with the independent quadratic-Bezier-AABB/SLSQP projector, then map iptm to the same local face connectivity entry and replay source face/point write order for the 218 CONT_NOEU slots. JEU is not used to select sample locations.",
        "native_projection_use": "PROJ_X/Y/Z is compared after deterministic source-order sample selection as a mapping/geometry cross-check; it is not used to select a sample or calculate the independent signed gap.",
        "med_displacement_identity": med_identity,
        "maximum_saved_MED_vs_SDISP_displacement_difference_mm": max(med_vs_table_errors),
        "master_state_basis": "Deformed slave and master coordinates for every saved state come from the archived MED DEPL field. The MED coordinate order matches frozen .mail order exactly; SNODE DEPL values are cross-checked against SDISP.csv.",
        "sample_slot_rule": "AUTO TRIA6 uses six interior quadrature points. mmnumn/mmpnoe associate local contact point iptm with local TRIA6 connectivity entry iptm; mmmres writes the sample value directly to that associated node slot as it visits points, so later visits overwrite earlier visits.",
        "source_files": {
            str(path.relative_to(ROOT)): sha256(path)
            for path in (attempt / "curved_contact.mail", attempt / "geometry-oracle.json",
                         attempt / "CONTACT.csv", attempt / "SDISP.csv", med_path,
                         Path(__file__).resolve())
        },
        "states": report_states,
        "overall_sample_matched_gap_screen": "PASS" if all(
            state["sample_matched_gap_screen"] == "PASS" for state in report_states) else "FAIL",
        "overall_all_sample_penetration_screen": "PASS" if all(
            state["all_sample_penetration_screen_same_frozen_numeric_limit"] == "PASS"
            for state in report_states) else "FAIL",
        "full_contact_method_acceptance": "NOT_INFERRED; the source confirms a per-sample status/last-write path for CONT_NOEU force slots, but available output does not identify which duplicate sample statuses caused the RN/cut discrepancy in this run.",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--attempt", type=Path, default=DEFAULT_ATTEMPT)
    parser.add_argument("--med-json", type=Path, default=DEFAULT_MED,
                        help="read-only MED DEPL extraction made with the pinned image")
    parser.add_argument("--json", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    report = audit(args.attempt.resolve(), args.med_json.resolve())
    args.json.parent.mkdir(parents=True, exist_ok=True)
    args.json.write_text(json.dumps(report, indent=2) + "\n")
    for state in report["states"]:
        print(f"INST={state['inst']:g}: {state['sample_matched_gap_screen']}; "
              f"max |JEU-gap|={state['maximum_absolute_sample_matched_gap_error_mm']:.9g} mm; "
              f"max |PROJ delta|={state['maximum_absolute_native_projection_coordinate_difference_mm']:.9g} mm; "
              f"minimum selected gap={state['minimum_independent_gap_mm']:.9g} mm; "
              f"minimum all-sample gap={state['minimum_independent_gap_all_570_samples_mm']:.9g} mm; "
              f"max sample penetration={state['maximum_penetration_all_570_samples_mm']:.9g} mm")
    print(f"Overall sample-matched gap screen: {report['overall_sample_matched_gap_screen']}")
    print(f"Full contact method acceptance: {report['full_contact_method_acceptance']}")
    print(f"Wrote {args.json}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
