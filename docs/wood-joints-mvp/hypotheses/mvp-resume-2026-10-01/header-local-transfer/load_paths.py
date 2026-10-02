"""Attribute current header actions to their actual loading directions.

This reads saved nominal forces, without solving or assigning splitting
capacity. Moving a pure Z tie along its axis locates its own header seat
without changing its wrench. Gross beam normal stress is a sign diagnostic.
"""

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
BASE = HERE.parent
ROOT = HERE.parents[4]
CASES = ("a12-rear", "a12-forward", "a12-left", "k12-right", "k12-rear", "a1-rear")
PINS = {
    "../mvp-acceleration-2026-09-28/reduced-static-attempt01/model-inputs.json": "178ab4f9352c8b1f11525ffc6680efa5733ba74cedd609874e9a1966624740f9",
    "../right-corner-finished-sections-2026-10-01/source-plan.json": "6131d10c612aabb34bfcfb1872ccce73a57541dda4ffaa5c0bb9e4efb6e4a0b8",
    "corner-frame-attempt01/model.json": "d17dadd7c999e4a1634f53226cf63e131f547cd9cf5d46d87d75c935f2dc807e",
    "corner-frame-attempt01/row-identities.json": "bec1feb75be61b321220a047a652cc42f09c4c11d1d3c66377c4035bde4826d5",
    "corner-frame-attempt01/operators.npz": "f40bf53412afb400df23ff108e90bac66db3c493da26a19af5c05de329c165ad",
    "two-receiver-frame-attempt03/comparison.json": "0ff0dfc00c112a906910641141fd242f4a58295aa3324ca569132a3fa2d388a5",
    "two-receiver-frame-attempt03/response.npz": "774c3bbddf8061f6b9d1cfdd5f22efbeb1025bd57431a249912ae8e60a731f52",
    "member-screen-attempt02/all-two-receiver-clearance01/geometry.json": "ecfeee2627fc67d91ce89acd5253bf99a4d79b06451c94ced6b915a664009f9d",
    "member-screen-attempt02/all-two-receiver-clearance01/action-section-arrays.npz": "3f89ad4290e93a2fed4a2526ae2cafa143ac64f3bac7bf40d46c71cd646b23e9",
    "member-screen-attempt02/all-two-receiver-clearance01/member-results.json": "8828f6d258a770136deb6af7dca1b443ebd0459faaa6e71d111f4f7b9e1b3507",
    "header-joint-attempt02/final/joint-actions.json": "fcdd3e85f7856220504de79f818724dbf271f029f1066143ec8335f59ed966a4",
}
BOLT = "candidate_bolt_lateral_plane"
TIE = "physical_bolt_outer_seat_tension"
WITHDRAWAL = "non_qualifying_parametric_screw_withdrawal"
CONTACT = "timber_or_panel_contact"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    return json.loads(path.read_text())


def require(condition, message):
    if not condition:
        raise ValueError(message)


def run(output):
    require(output.parent == HERE / "results", "choose a direct child of owned results")
    require(not output.exists(), "preserve previous outputs")
    pins = {(BASE / name).resolve(): digest for name, digest in PINS.items()}
    pins[Path(__file__).resolve()] = sha(Path(__file__).resolve())
    for path, digest in pins.items():
        require(sha(path) == digest, f"changed source: {path}")
    model = read(BASE / "corner-frame-attempt01/model.json")
    rows = read(BASE / "corner-frame-attempt01/row-identities.json")
    comparison = read(BASE / "two-receiver-frame-attempt03/comparison.json")
    member_dir = BASE / "member-screen-attempt02/all-two-receiver-clearance01"
    report = read(member_dir / "member-results.json")
    member_geometry = read(member_dir / "geometry.json")
    record = member_geometry["members"]["base_header"]
    geometry = record["geometry"]
    require(
        report["source_sha256"][
            str((BASE / "two-receiver-frame-attempt03/response.npz").relative_to(ROOT))
        ]
        == PINS["two-receiver-frame-attempt03/response.npz"],
        "member actions have another response",
    )
    require(
        comparison["response_sha256"] == PINS["two-receiver-frame-attempt03/response.npz"],
        "comparison has another response",
    )
    require(geometry["axis"] == [1.0, 0.0, 0.0], "header grain changed")
    require(
        abs(geometry["width_mm"] - 139.7) < 1e-8 and abs(geometry["depth_mm"] - 38.1) < 1e-8,
        "header section changed",
    )
    coordinates = model["physical_node_coordinates_mm"]
    datum = np.mean([coordinates[str(n)] for n in model["body_nodes"]["base_header"]], axis=0)
    body_index = model["body_names"].index("base_header")
    role_counts = Counter(record["point_action_roles"])
    require(
        role_counts
        == {
            BOLT: 24,
            TIE: 12,
            WITHDRAWAL: 10,
            CONTACT: 116,
            "panel_screw_lateral_plane": 20,
            "discrete_body_load": 212,
        },
        "header action census changed",
    )
    center = np.array(geometry["start"])
    lower_z, upper_z = center[2] - 19.05, center[2] + 19.05
    summaries, ties, screws = [], [], []
    probe = None
    max_force_residual = max_moment_residual = max_operator_error = max_line_move_error = 0.0
    with (
        np.load(BASE / "corner-frame-attempt01/operators.npz", allow_pickle=False) as operators,
        np.load(BASE / "two-receiver-frame-attempt03/response.npz", allow_pickle=False) as response,
        np.load(member_dir / "action-section-arrays.npz", allow_pickle=False) as arrays,
    ):
        operator = operators["D"][:, 6 * body_index : 6 * body_index + 6]
        require(operator.shape == (1888, 6), "operator shape changed")
        points = arrays["base_header__point_xyz_mm"]
        point_rows = arrays["base_header__point_rows"]
        stations = arrays["base_header__point_stations_mm"]
        cut_stations = np.repeat(record["stations_mm"], 2)
        require(points.shape == (394, 3), "header point shape changed")
        for case in CASES:
            values = arrays[case + "__base_header__point_force_free_couple_xyz"]
            raw = response[case + "_gap_raw_force_n"]
            cuts = arrays[case + "__base_header__internal_negative_grain_u_v"]
            require(np.isfinite(values).all() and np.isfinite(raw).all(), "nonfinite actions")
            wrenches = values.copy()
            wrenches[:, 3:] += np.cross(points - datum, values[:, :3])
            total = wrenches.sum(axis=0)
            max_force_residual = max(max_force_residual, float(max(abs(total[:3]))))
            max_moment_residual = max(max_moment_residual, float(max(abs(total[3:]))))
            require(max(abs(total[:3])) < 0.1 and max(abs(total[3:])) < 2, "body imbalance")
            role_summary = {}
            for role in role_counts:
                mask = np.array([r == role for r in record["point_action_roles"]])
                role_summary[role] = {
                    "point_count": int(sum(mask)),
                    "wrench_about_body_datum_n_nmm": wrenches[mask].sum(axis=0).tolist(),
                    "maximum_absolute_point_force_xyz_n": abs(values[mask, :3])
                    .max(axis=0)
                    .tolist(),
                }
            summaries.append(
                {
                    "case_id": case,
                    "roles": role_summary,
                    "whole_body_residual_n_nmm": total.tolist(),
                }
            )
            for index, (identity, role, row) in enumerate(
                zip(
                    record["point_action_ids"],
                    record["point_action_roles"],
                    point_rows,
                    strict=True,
                )
            ):
                if row < 0:
                    continue
                expected = -operator[row] * raw[row]
                expected[3:] *= 1000
                error = max(abs(expected - wrenches[index]))
                max_operator_error = max(max_operator_error, float(error))
                require(error < 1e-5, "restored action disagrees with physical operator")
                require(rows[row]["row_id"] == identity, "row identity changed")
                if role == TIE:
                    direction = -operator[row, :3]
                    require(
                        max(abs(direction[:2])) < 1e-8 and abs(abs(direction[2]) - 1) < 1e-8,
                        "header tie is not pure Z",
                    )
                    own_seat = points[index].copy()
                    own_seat[2] = lower_z if direction[2] > 0 else upper_z
                    require(
                        -1219.2 <= own_seat[0] <= 1216.025 and -175.7 <= own_seat[1] <= -36.0,
                        "seat line outside header bounds",
                    )
                    delta = np.cross(own_seat - points[index], values[index, :3])
                    max_line_move_error = max(max_line_move_error, float(max(abs(delta))))
                    require(max(abs(delta)) < 1e-5, "seat relocation changes wrench")
                    ties.append(
                        {
                            "case_id": case,
                            "axis_id": identity.split("/")[0],
                            "row": int(row),
                            "saved_equivalent_point_xyz_mm": points[index].tolist(),
                            "own_header_seat_line_point_xyz_mm": own_seat.tolist(),
                            "force_on_header_xyz_n": values[index, :3].tolist(),
                            "free_moment_nmm": values[index, 3:].tolist(),
                            "inward_header_Z_compression_n": float(abs(values[index, 2])),
                            "actual_seat_and_metal_transfer_qualified": False,
                        }
                    )
                if role == WITHDRAWAL:
                    require(
                        abs(points[index, 1] + 36) < 1e-8 and abs(points[index, 2] - 257.95) < 1e-8,
                        "kicker screw station changed",
                    )
                    indices = np.flatnonzero(abs(cut_stations - stations[index]) < 1e-6)
                    require(len(indices) == 2, "missing before/after screw cuts")
                    # Conventional negative-half beam traction: sigma_X is
                    # N/A - M_Z*y/I_ZZ + M_Y*z/I_YY. Here z=0 at screw line.
                    normal = [
                        float(
                            cuts[k, 0] / (139.7 * 38.1)
                            - cuts[k, 5] * 69.85 / (38.1 * 139.7**3 / 12)
                        )
                        for k in indices
                    ]
                    screws.append(
                        {
                            "case_id": case,
                            "axis_id": identity.split("/")[0],
                            "row": int(row),
                            "point_xyz_mm": points[index].tolist(),
                            "force_on_header_xyz_n": values[index, :3].tolist(),
                            "gross_front_face_sigma_X_before_after_mpa": normal,
                            "both_gross_signs_tensile": min(normal) > 1e-8,
                            "actual_local_tension_perpendicular_resistance_established": False,
                        }
                    )
                    if (
                        case == "k12-rear"
                        and identity == "kicker_header_left_1/parametric-withdrawal"
                    ):
                        section = next(
                            s
                            for s in member_geometry["saved_matching_finished_sections"]
                            if s["member"] == "base_header"
                            and abs(s["station_mm"] - stations[index]) < 1e-6
                        )
                        props = section["properties"]
                        require(not props["disconnected_ligaments"], "probe section disconnected")
                        frame = next(
                            f
                            for f in read(
                                BASE.parent
                                / "right-corner-finished-sections-2026-10-01/source-plan.json"
                            )["member_frames_and_step_bindings"]
                            if f["member_id"] == "base_header"
                        )
                        require(
                            section["source_step_sha256"]
                            == frame["step_sha256"]
                            == record["current_finished_step_sha256"],
                            "probe section binding differs",
                        )
                        previous = np.array(
                            [frame["section_u_global_xyz"], frame["section_v_global_xyz"]]
                        )
                        transform = np.eye(3)[1:] @ previous.T
                        require(
                            np.max(abs(transform @ transform.T - np.eye(2))) < 1e-8,
                            "section frame mismatch",
                        )
                        q = props["area_covariance_integrals_mm4"]
                        covariance = (
                            transform
                            @ np.array([[q["uu"], q["uv"]], [q["uv"], q["vv"]]])
                            @ transform.T
                        )
                        centroid = np.array(props["centroid_global_xyz_mm"])
                        section_datum = center + np.array([stations[index], 0, 0])
                        offset = centroid - section_datum
                        connection = next(
                            c
                            for c in read(
                                BASE.parent
                                / "mvp-acceleration-2026-09-28/reduced-static-attempt01/model-inputs.json"
                            )["connections"]
                            if c.get("axis_id") == "kicker_header_left_1"
                        )
                        nominal = connection["source_record"]["purchased_nominal_length_mm"]
                        tip = np.array(connection["source_point_xyz_mm"]) + nominal * np.array(
                            connection["axis_xyz"]
                        )
                        require(
                            nominal == 63.5
                            and max(abs(tip[[0, 2]] - points[index, [0, 2]])) < 1e-8,
                            "nominal receiving segment differs",
                        )
                        neutral, endpoint_stress = [], []
                        for k in indices:
                            force, moment = cuts[k, :3], cuts[k, 3:].copy()
                            moment -= np.cross(offset, force)
                            slopes = np.linalg.solve(covariance, [-moment[2], moment[1]])
                            axial = force[0] / props["area_mm2"]
                            require(slopes[0] > 0, "probe bending side changed")
                            neutral.append(
                                float(
                                    centroid[1]
                                    - (axial + slopes[1] * (tip[2] - centroid[2])) / slopes[0]
                                )
                            )
                            endpoint_stress.append(
                                [
                                    float(axial + slopes @ (point[1:] - centroid[1:]))
                                    for point in (points[index], tip)
                                ]
                            )
                        probe = {
                            "case_id": case,
                            "axis_id": connection["axis_id"],
                            "source_section_plane_id": section["plane_id"],
                            "connected_area_mm2": props["area_mm2"],
                            "section_centroid_xyz_mm": centroid.tolist(),
                            "covariance_YZ_mm4": covariance.tolist(),
                            "front_to_nominal_tip_Y_interval_mm": [
                                float(points[index, 1]),
                                float(tip[1]),
                            ],
                            "normal_field_zero_Y_at_screw_Z_before_after_mm": neutral,
                            "front_and_nominal_tip_sigma_X_before_after_mpa": endpoint_stress,
                            "minimum_nominal_tip_to_zero_normal_plane_Y_mm": float(
                                tip[1] - max(neutral)
                            ),
                            "nominal_receiving_segment_on_tension_side": bool(
                                min(np.ravel(endpoint_stress)) > 0
                            ),
                            "medium_heavy_load_classification_established": False,
                            "Y_reinforcement_capacity_established": False,
                            "scope": "Linear normal field on a saved connected section; nominal full screw length includes tip/head uncertainties. No local perpendicular stress or actual thread/installation qualification.",
                        }
    joints = read(BASE / "header-joint-attempt02/final/joint-actions.json")["interfaces"]
    require(
        len(joints) == 36 and len(ties) == 72 and len(screws) == 60 and probe is not None,
        "state census changed",
    )
    for path, digest in pins.items():
        require(sha(path) == digest, f"source changed during arithmetic: {path}")
    result = {
        "schema": "current_header_load_paths/v1",
        "source_force_state_scope": report["source_force_state_scope"],
        "counts": {
            "cases": 6,
            "actions_per_case": 394,
            "physical_actions_checked": 1092,
            "header_tie_states": 72,
            "kicker_withdrawal_states": 60,
            "target_interfaces": 36,
        },
        "role_census": dict(role_counts),
        "body_datum_xyz_mm": datum.tolist(),
        "maximum_target_interface_absolute_FY_n": max(
            abs(j["interface_wrench_on_block_xyz_n_nmm"][1]) for j in joints
        ),
        "maximum_force_residual_n": max_force_residual,
        "maximum_moment_residual_nmm": max_moment_residual,
        "maximum_operator_wrench_error_n_or_nmm": max_operator_error,
        "maximum_Z_line_relocation_moment_error_nmm": max_line_move_error,
        "gross_front_face_sign_tensile_both_sides_count": sum(
            s["both_gross_signs_tensile"] for s in screws
        ),
        "peak_kicker_withdrawal_state": max(screws, key=lambda s: s["force_on_header_xyz_n"][1]),
        "case_role_wrenches": summaries,
        "Z_tie_states": ties,
        "Y_kicker_withdrawal_states": screws,
        "tension_side_receiving_segment_probe": probe,
        "source_sha256": {str(p.relative_to(ROOT)): h for p, h in pins.items()},
        "limits": [
            "No frame, native or CAD solve, geometry change, tests or review.",
            "72 header ties have inward Z force at their own opposite outer faces; this alone does not qualify seats, washers or local transfer.",
            "Gross beam axial normal stress is a bending-side sign diagnostic, not a local perpendicular stress or splitting capacity.",
            "Kicker Y withdrawal and same-face compression contacts remain actual cross-grain loading paths; target header bolt lateral FY is negligible.",
            "Point/free-moment loads, including self-equilibrated nodal dead-load terms, remain intact.",
        ],
        "complete_joint_acceptance": False,
        "physical_release": False,
    }
    serialized = json.dumps(result, indent=2, allow_nan=False) + "\n"
    output.mkdir(parents=True)
    (output / "result.json").write_text(serialized)
    (output / "producer.py.snapshot").write_bytes(Path(__file__).read_bytes())
    print(
        json.dumps(
            {
                "output": str(output.relative_to(ROOT)),
                "result_sha256": sha(output / "result.json"),
                "peak_kicker_Y_n": result["peak_kicker_withdrawal_state"]["force_on_header_xyz_n"][
                    1
                ],
                "tensile_gross_front_sign_count": result[
                    "gross_front_face_sign_tensile_both_sides_count"
                ],
                "maximum_target_interface_absolute_FY_n": result[
                    "maximum_target_interface_absolute_FY_n"
                ],
            }
        )
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=HERE / "results/attempt03")
    args = parser.parse_args()
    run(args.output.resolve())
