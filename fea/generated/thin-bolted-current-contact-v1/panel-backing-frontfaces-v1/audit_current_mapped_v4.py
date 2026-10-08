"""Audit immutable current marker outputs with saved-data arithmetic only."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import platform
import sys
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np

OWN = Path(__file__).resolve()
ROOT, LEAF = OWN.parents[4], OWN.parent
ARTIFACT = LEAF / "current-mapped-markers-v4.json"
ARTIFACT_SHA = "8fbfb819e04978ccda2fcbbb934b145eb9447144854af78bc515cc143981b9d6"
HELPER = LEAF / "audit_v3_semantic_failure.py"
HELPER_SHA = "5d9efdc740a1a42f2eb147c4c83b4fec44b95bd9746c350bee3ee2fda98cad64"
REVIEW = LEAF / "independent-mapped-review-v4.json"
REVIEW_SHA = "2634506ceee3304c20cb7d3d43632e9f63db92dca08202b7179cd0bbd6f86ac9"


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def calculate():
    assert sha(ARTIFACT) == ARTIFACT_SHA and sha(HELPER) == HELPER_SHA and sha(REVIEW) == REVIEW_SHA
    spec = importlib.util.spec_from_file_location("frozen_source_audit_utilities_v3", HELPER)
    audit = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(audit)
    result = json.loads(ARTIFACT.read_bytes())
    pins = result["source_sha256"]
    assert len(pins) == 242 and all(pins[path] == expected for path, expected in audit.PINS.items())
    audit.verify(pins)
    before = audit.canonical(pins)
    receipt = json.loads((ROOT / audit.RECEIPT).read_bytes())
    assert receipt["field_sha256"] == audit.PINS[audit.FIELD]
    assert receipt["actual_complete_timber_execution"]["loaded_admission_sha256"] == audit.PINS[audit.GATE]
    assert receipt["independent_complete_timber_observer_isolation_face_source_map_original_gradient_and_equilibrium_checks_pass"] is True
    assert result["field_sha256"] == audit.PINS[audit.FIELD] and result["actual_admission_sha256"] == audit.PINS[audit.GATE]
    assert result["admission_receipt_sha256"] == audit.PINS[audit.RECEIPT]
    assert result["field_canonical_sha256"] == receipt["field_canonical_sha256"]
    field = json.loads((ROOT / audit.FIELD).read_bytes())
    assert all(result[key] == field[key] == receipt[key] for key in audit.IDENTITY)
    assert result["schema"] == "thin_bolted_admitted_current_panel_backing_mapped_markers/v4"
    previous = json.loads(audit.ARTIFACT.read_bytes())
    assert sha(audit.ARTIFACT) == audit.ARTIFACT_SHA
    assert all(result[key] == previous[key] for key in ("field_sha256", "field_canonical_sha256", "pure_pose_map_sha256", "source_q_canonical_sha256"))
    original = {row["id"]: row for row in field["contact_actions"] if row["kind"] == "panel_contact"}
    rows = result["mapped_backing_ports"]
    assert len(original) == len(rows) == len({row["id"] for row in rows}) == 530
    assert set(original) == {row["id"] for row in rows}
    packet = json.loads((LEAF / "frontfaces.json").read_bytes())
    owners = {row["receiver"]: {face["face_id"]: face for face in row["own_frontfaces"]}
              for row in packet["own_frontface_queries"]}
    metadata = json.loads((ROOT / "fea/generated/thin-bolted-panel/operators-intervals8.json").read_bytes())
    by_id = {row["id"]: row for row in rows}
    area_error = 0.
    for group in packet["original_source_plane_groups"]:
        selected = [by_id[identity] for identity in group["source_contact_ids"]]
        assert all((row["panel"], row["receiver"], row["original_reference_panel_outward_normal_xyz"]) ==
            (group["panel"], group["receiver"], group["source_panel_outward_normal_xyz"]) for row in selected)
        area_error = max(area_error, abs(sum(row["original_reference_area_weight_mm2"] for row in selected) - group["area_weight_sum_mm2"]))
    errors = defaultdict(float)
    panel_tables, loaded_exceptions, interior_uncertified = {}, [], []
    geometric = Counter()
    certified = Counter()
    metric_minimum = float("inf")
    projection_count = 0
    source_surface_normal_count = 0
    relative_witness = min(rows, key=lambda row: row["current_panel_marker"]["relative_rear_offset_chart_determinant"])
    for row in rows:
        action = original[row["id"]]
        assert all(action[key] == result[key] for key in audit.IDENTITY)
        assert (row["panel"], row["receiver"], row["original_reference_point_xyz_mm"]) == (action["first"], action["second"], action["point_xyz_mm"])
        assert row["recorded_linear_compression_n"] == action["compression_n"]
        assert row["recorded_linear_force_on_first_xyz_n"] == action["force_on_first_xyz_n"]
        assert np.array_equal(row["recorded_linear_force_on_second_xyz_n"], -np.asarray(action["force_on_first_xyz_n"]))
        provenance = row["second_force_metadata_provenance"]
        assert provenance["source_action_canonical_sha256"] == audit.canonical(action)
        assert provenance["same_original_point_xyz_mm"] == action["point_xyz_mm"]
        assert provenance["first"] == action["first"] and provenance["second"] == action["second"]
        assert provenance["actual_gate_sha256"] == audit.PINS[audit.GATE] and provenance["original_field_sha256"] == audit.PINS[audit.FIELD]
        assert provenance["genuine_current_gate_observed_before_bridge"] is True and provenance["admitted_action_mutated"] is False
        assert provenance["original_second_field_present"] is False and provenance["second_force_metadata_derived_from_original_paired_law"] is True
        assert all(pins[path] == digest for path, digest in provenance["source_sha256"].items())
        assert row["panel_marker_error"] is None and not row["current_contact_force_set_to_zero_or_port_dropped"]
        marker = row["current_panel_marker"]
        datum = metadata[row["panel"]]
        axes = np.asarray(datum["local_axes_columns_xyz"])
        source_det = float(np.linalg.det(axes))
        assert marker["source_axes_determinant"] == marker["reference_normal_offset_chart_determinant"] == source_det == -1.
        assert marker["world_isometry_facade_matrix"] == [[-1., 0., 0.], [0., 1., 0.], [0., 0., 1.]]
        assert marker["world_isometry_facade_used_only_for_panel_marker"] is True
        assert marker["source_axes_Gram_maximum_error"] == float(np.max(abs(axes.T @ axes - np.eye(3))))
        assert marker["source_axes_reorthonormalized"] is False and marker["admitted_mapping_or_q_mutated"] is False
        local = (np.asarray(action["point_xyz_mm"]) - datum["origin_xyz_mm"]) @ axes
        assert np.array_equal(local, marker["reference_panel_local_xyz_mm"])
        tangent = np.asarray(marker["rear_tangent_wrt_panel_local_xy"])
        director = np.asarray(marker["frozen_midsurface_front_normal_vector_xyz"])
        raw = float(np.linalg.det(np.column_stack((tangent, director))))
        relative = raw / source_det
        errors["raw_determinant"] = max(errors["raw_determinant"], abs(raw - marker["rear_offset_chart_determinant"]))
        errors["relative_determinant"] = max(errors["relative_determinant"], abs(relative - marker["relative_rear_offset_chart_determinant"]))
        cross = source_det * np.cross(tangent[:, 0], tangent[:, 1])
        front = cross / np.linalg.norm(cross)
        errors["front_normal_inf"] = max(errors["front_normal_inf"], float(np.max(abs(front - marker["current_front_geometric_normal_xyz"]))))
        errors["rear_normal_inf"] = max(errors["rear_normal_inf"], float(np.max(abs(-front - marker["current_rear_outward_geometric_normal_xyz"]))))
        angle = float(np.arctan2(np.linalg.norm(np.cross(front, director)), front @ director))
        errors["front_vs_frozen_angle_rad"] = max(errors["front_vs_frozen_angle_rad"], abs(angle - marker["rear_geometric_vs_frozen_normal_angle_rad"]))
        eigenvalue = float(np.linalg.eigvalsh(tangent.T @ tangent)[0])
        errors["rear_metric_eigenvalue"] = max(errors["rear_metric_eigenvalue"], abs(eigenvalue - marker["rear_surface_metric_minimum_eigenvalue"]))
        assert relative > 0. and eigenvalue > 0.
        metric_minimum = min(metric_minimum, eigenvalue)
        errors["maximum_source_Gram_error"] = max(errors["maximum_source_Gram_error"], marker["source_axes_Gram_maximum_error"])
        errors["maximum_panel_local_clipping_mm"] = max(errors["maximum_panel_local_clipping_mm"], max(abs(value) for value in marker["reference_panel_xy_clipping_mm"]))
        faces = {face["face_id"]: face for face in row["own_face_markers"]}
        assert set(faces) == set(owners[row["receiver"]])
        eligible, piece_notes = [], []
        for name, face in faces.items():
            saved = owners[row["receiver"]][name]
            assert face["signature_sha256"] == saved["signature_sha256"]
            assert face["exact_parameter_geometry_sha256"] == saved["exact_parameter_geometry_sha256"]
            exact = saved["exact_parameter_geometry"]
            assert face["actual_reference_plane_origin_xyz_mm"] == exact["plane_origin_xyz_mm"]
            assert face["actual_reference_plane_normal_xyz"] == exact["oriented_normal_xyz"]
            assert not face["source_reference_port_replaced_or_snapped"] and face["projection_error"] is None
            normal = np.asarray(exact["oriented_normal_xyz"])
            for key in ("current_initial_projected_receiver_marker", "current_original_source_receiver_point", "current_pullback_receiver_surface"):
                state = face[key]
                mapped_normal = np.linalg.solve(np.asarray(state["reference_coordinate_jacobian"]).T, normal)
                mapped_normal /= np.linalg.norm(mapped_normal)
                errors["receiving_inverse_transpose_normal_inf"] = max(errors["receiving_inverse_transpose_normal_inf"], float(np.max(abs(mapped_normal - state["geometric_normal"]))))
                source_surface_normal_count += 1
            foot, trimmed = face["local_closest_point"], face["current_reference_trim"]
            assert foot["current_footpoint_xyz_mm"] == face["current_pullback_receiver_surface"]["position"]
            assert foot["current_geometric_normal_xyz"] == face["current_pullback_receiver_surface"]["geometric_normal"]
            facing = float(np.asarray(marker["current_rear_outward_geometric_normal_xyz"]) @ face["current_pullback_receiver_surface"]["geometric_normal"])
            errors["opposed_normal_dot"] = max(errors["opposed_normal_dot"], abs(facing - face["opposed_current_outward_normal_dot"]))
            delta = np.asarray(marker["current_rear_point_xyz_mm"]) - foot["current_footpoint_xyz_mm"]
            errors["signed_gap_mm"] = max(errors["signed_gap_mm"], abs(float(delta @ foot["current_geometric_normal_xyz"]) - foot["gap_opening_positive_mm"]))
            classification = trimmed["classification"]
            unknown = classification is None or classification["location"] == "off_reference_plane"
            smooth = None if unknown and not trimmed["definitely_exterior"] else bool(classification
                and classification["eligible_for_smooth_own_face_projection"] and foot["local_stationary_closest_point_certified"] and facing < 0.)
            assert smooth is face["smooth_local_piece_projection_with_opposed_faces"]
            if smooth:
                eligible.append(name)
            piece_notes.append({"face_id": name, "classification": classification["location"] if classification else None,
                "definitely_exterior": trimmed["definitely_exterior"], "curve_types": face["exported_saved_curve_types"],
                "local_projection_certified": foot["local_stationary_closest_point_certified"],
                "stationarity_inf_mm": foot["stationarity_inf_mm"], "smooth_stencil": foot["distance_hessian_stencil_remains_in_one_smooth_branch"],
                "at_any_station_one_sided": foot["at_any_station_derivative_is_one_sided"], "opposed_normal_dot": facing})
            projection_count += 1
        all_exterior = bool(faces) and all(face["current_reference_trim"]["definitely_exterior"] is True for face in faces.values())
        available = True if eligible else False if all_exterior else None
        assert sorted(eligible) == sorted(row["union"]["certified_interior_opposed_piece_ids"])
        assert row["union"]["some_smooth_local_owned_piece_projection_available"] is available
        assert row["union"]["all_owned_pieces_proved_exterior"] is all_exterior
        location = row["union"]["local_pullback_union_location"]
        geometric[location] += 1
        certified[str(available)] += 1
        table = panel_tables.setdefault(row["panel"], {"all_location_counts": Counter(), "all_certified_tristate_counts": Counter(),
            "positive_location_counts": Counter(), "positive_certified_tristate_counts": Counter(), "old_compression_sums_by_location_n": defaultdict(float)})
        table["all_location_counts"][location] += 1
        table["all_certified_tristate_counts"][str(available)] += 1
        table["old_compression_sums_by_location_n"][location] += row["recorded_linear_compression_n"]
        if row["recorded_linear_compression_n"] > 0.:
            table["positive_location_counts"][location] += 1
            table["positive_certified_tristate_counts"][str(available)] += 1
            if available is not True:
                entry = {"id": row["id"], "panel": row["panel"], "receiver": row["receiver"], "location": location,
                    "certified_opposed_projection_available": available, "old_compression_n": row["recorded_linear_compression_n"],
                    "original_point_xyz_mm": row["original_reference_point_xyz_mm"], "original_area_weight_mm2": row["original_reference_area_weight_mm2"],
                    "old_first_force_xyz_n": row["recorded_linear_force_on_first_xyz_n"], "own_piece_markers": piece_notes}
                if location == "interior_on_supported_piece":
                    interior_uncertified.append(entry)
                else:
                    loaded_exceptions.append(entry)
    assert geometric == result["summary"]["all_ports"] and projection_count == 1540 and source_surface_normal_count == 4620
    assert sum(row["panel_marker_error"] is not None for row in rows) == result["summary"]["panel_marker_errors"] == 0
    assert result["summary"]["face_projection_errors"] == 0
    assert area_error < 1e-8
    arithmetic_errors = {key: value for key, value in errors.items() if not key.startswith("maximum_")}
    assert max(arithmetic_errors.values()) < 1e-10
    audit.verify(pins)
    assert sha(ARTIFACT) == ARTIFACT_SHA and sha(REVIEW) == REVIEW_SHA
    direct = {str(path.relative_to(ROOT)): digest for path, digest in ((ARTIFACT, ARTIFACT_SHA), (HELPER, HELPER_SHA), (REVIEW, REVIEW_SHA), (OWN, sha(OWN)))}
    return {"schema": "independent-admitted-current-panel-marker-output-review/v4", "status": "PASS_OUTPUT_AUDIT_DIAGNOSTIC_ONLY",
        **{key: result[key] for key in audit.IDENTITY}, "invocation_argv": list(sys.orig_argv),
        "source_sha256": direct, "tools": {"python": platform.python_version(), "numpy": np.__version__},
        "issued_artifact_bytes": ARTIFACT.stat().st_size, "source_closure": {"map_in_bound_issued_artifact": True,
            "verified_pin_count": len(pins), "before_canonical_sha256": before, "after_canonical_sha256": audit.canonical(pins), "all_bytes_unchanged": True},
        "raw_field_gate_receipt_before_metadata_audit": {key: result[key] for key in ("field_sha256", "actual_admission_sha256", "admission_receipt_sha256", "field_canonical_sha256")},
        "source_q_and_pose_map_digests_equal_frozen_v3": True, "all_530_original_ids_states_owners_points_forces_pair_hashes_provenance_unchanged": True,
        "all_22_area_group_sums_preserved_maximum_error_mm2": area_error,
        "all_57_original_owned_signature_exact_plane_sets_preserved_in_1540_piece_markers": True,
        "all_530_source_reflections_and_raw_reference_relative_determinants_checked": True,
        "arithmetic_errors": dict(errors), "receiving_F_inverse_transpose_normal_checks": source_surface_normal_count,
        "minimum_relative_rear_chart_determinant": {"value": relative_witness["current_panel_marker"]["relative_rear_offset_chart_determinant"], "id": relative_witness["id"]},
        "minimum_rear_metric_eigenvalue": metric_minimum,
        "all_port_geometric_location_counts": dict(geometric), "all_port_certified_opposed_tristate_counts": dict(certified),
        "per_panel_counts_and_old_force_sums": panel_tables, "every_positive_exterior_or_unknown_action": loaded_exceptions,
        "additional_positive_geometric_interior_but_uncertified_action": interior_uncertified,
        "qualification": "496 interior labels contain only479 certified opposed smooth projections;17 geometrically interior rows lack a local projection certificate, including one loaded70.44376832415512N row. Unknown/exterior/uncertified metadata are retained; no force is removed or reassigned.",
        "unchanged_method_limits": {"saved_LINE_CIRCLE_edge_plane_tolerance_mm": 2e-7, "unsupported_BSPLINE_own_pieces": 10,
            "panel_local_clipping_limit_mm": 1e-7, "local_stationarity_certificate_limit_mm_strict": 1e-7,
            "local_distance_hessian_minimum_eigenvalue_strict": 1e-8, "local_hessian_asymmetry_limit_strict": 1e-5,
            "local_Hessian_stencil_step_mm": 1e-3, "global_closest_point_unique": False,
            "whole_current_overlap_pressure_area_or_physical_response_established": False},
        "admitted_force_metadata_read_for_audit": True, "q_vector_evaluated_or_changed": False,
        "mapping_or_observer_or_projection_repeated": False, "CAD_K_native_or_response_solve_executed": False,
        "issued_result_preserved": True, "capacity_or_joint_or_fabrication_or_climbing_acceptance_established": False}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    encoded = (json.dumps(calculate(), sort_keys=True, indent=2, allow_nan=False) + "\n").encode()
    with args.out.open("xb") as stream:
        stream.write(encoded)
    print(json.dumps({"out": str(args.out), "bytes": len(encoded), "sha256": hashlib.sha256(encoded).hexdigest()}))


if __name__ == "__main__":
    main()
