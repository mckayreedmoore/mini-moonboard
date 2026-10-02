"""Find explicit straight-shaft placement witnesses for saved knee-bolt poses.

This geometry calculation neither supplies bore-wall reactions nor changes
the frame's zero-clearance laws for its four continuous bolts.
"""

import argparse
import hashlib
import json
from pathlib import Path

import frame_state_contract
import knee_bore_source
import numpy as np
import remaining_joint_screen as screen

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
FRAME = HERE / "corner-frame-attempt01"
SOURCE = HERE / "two-receiver-frame-attempt03"
COMPARISON_SHA = "0ff0dfc00c112a906910641141fd242f4a58295aa3324ca569132a3fa2d388a5"
CONTRACT_SHA = "22e1f8b864c03469701010fc856a815b3604a4efde2748531e36d284050266e5"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require(condition, message):
    if not condition:
        raise ValueError(message)


def witness(bore, poses, datum):
    """Place one cylinder inside three straight, linearly posed bore segments.

    ponytail: a least-squares line supplies a sufficient placement witness;
    an unsuccessful witness is not proof that every possible line fails.
    """
    axis = np.array(bore["axis_xyz"])
    axis /= np.linalg.norm(axis)
    trial = np.eye(3)[np.argmin(np.abs(axis))]
    first = np.cross(axis, trial)
    first /= np.linalg.norm(first)
    basis = np.array([first, np.cross(axis, first)])
    head = np.array(bore["head_seat_point_mm"])
    points, normals, members, radii = [], [], [], []
    for receiver in bore["receivers"]:
        translation, rotation = poses[receiver["member"]]
        normal = axis + np.cross(rotation, axis)
        normal /= np.linalg.norm(normal)
        for key in ("start_point_mm", "end_point_mm"):
            original = np.array(receiver[key])
            points.append(original + translation + np.cross(rotation, original - datum))
            normals.append(normal)
            members.append(receiver["member"])
            radii.append(receiver["bore_diameter_mm"] / 2)
    points, normals = np.array(points), np.array(normals)
    longitudinal = (points - head) @ axis
    transverse = (points - head) @ basis.T
    mapping = np.c_[np.ones(6), longitudinal]
    coefficients, _, rank, _ = np.linalg.lstsq(mapping, transverse, rcond=None)
    require(rank == 2, "degenerate ordered bore stack")
    line_point = head + coefficients[0] @ basis
    line_axis = axis + coefficients[1] @ basis
    line_axis /= np.linalg.norm(line_axis)
    cosine = normals @ line_axis
    require(np.min(np.abs(cosine)) > 0.99, "shaft tilt exceeds placement scope")
    parameter = np.sum(normals * (points - line_point), axis=1) / cosine
    intersection = line_point + parameter[:, None] * line_axis
    center_error = np.linalg.norm(intersection - points, axis=1)
    # The tilted cylinder section is an ellipse. Its enclosing circle is a
    # conservative radius bound in each bore's own normal plane.
    effective_shaft_radius = bore["shaft_diameter_mm"] / (2 * np.abs(cosine))
    margin = np.array(radii) - effective_shaft_radius - center_error
    initial_margin = float(np.min(margin))
    shift = np.zeros(3)
    if initial_margin < 0:
        worst = int(np.argmin(margin))
        other_room = float(np.min(np.delete(margin, worst)))
        if other_room > -initial_margin and center_error[worst] > 0:
            # Shift toward the missed bore using half the available room.
            # Recheck every endpoint; this is a witness, not an optimal line.
            distance = (other_room - initial_margin) / 2
            shift = -(intersection[worst] - points[worst]) * (
                distance / center_error[worst]
            )
            line_point += shift
            parameter = np.sum(normals * (points - line_point), axis=1) / cosine
            intersection = line_point + parameter[:, None] * line_axis
            center_error = np.linalg.norm(intersection - points, axis=1)
            margin = np.array(radii) - effective_shaft_radius - center_error
    clearances = np.array(radii) - bore["shaft_diameter_mm"] / 2
    utilization = (
        center_error + effective_shaft_radius - bore["shaft_diameter_mm"] / 2
    ) / clearances
    return {
        "straight_shaft_placement_found": bool(np.min(margin) >= 0),
        "minimum_conservative_margin_mm": float(np.min(margin)),
        "maximum_radial_clearance_fraction": float(np.max(utilization)),
        "maximum_centerline_error_mm": float(np.max(center_error)),
        "initial_least_squares_minimum_margin_mm": initial_margin,
        "corrective_line_shift_xyz_mm": shift.tolist(),
        "shaft_line_point_mm": line_point.tolist(),
        "shaft_line_direction_xyz": line_axis.tolist(),
        "endpoints": [
            {
                "member": member,
                "posed_bore_center_mm": point.tolist(),
                "shaft_center_in_bore_plane_mm": hit.tolist(),
                "centerline_error_mm": float(error),
                "tilted_shaft_radius_mm": float(radius),
                "conservative_margin_mm": float(gap),
            }
            for member, point, hit, error, radius, gap in zip(
                members,
                points,
                intersection,
                center_error,
                effective_shaft_radius,
                margin,
                strict=True,
            )
        ],
    }


def run(output, *, frame_dir=FRAME, clearance=SOURCE, metadata_seed_dir=None):
    output = output.resolve()
    require(
        output.parent == HERE
        and output.name.startswith("knee-bore-fit-attempt")
        and not output.exists(),
        "use a fresh owned knee-bore-fit-attempt directory",
    )
    binding = screen.bind_frame_sources(frame_dir, clearance, metadata_seed_dir)
    frame, source = binding["frame_dir"], binding["clearance_dir"]
    comparison_path = source / "comparison.json"
    if source == SOURCE.resolve():
        require(sha(comparison_path) == COMPARISON_SHA, "current frame comparison changed")
    comparison, scope = binding["comparison"], binding["force_scope"]
    bores, pins = knee_bore_source.load_bores()
    pins.update(binding["pins"])
    pins.update(
        {
            comparison_path: sha(comparison_path),
            source / "response.npz": comparison["response_sha256"],
            source / "producer.py.snapshot": comparison["producer_sha256"],
            Path(frame_state_contract.__file__): CONTRACT_SHA,
            Path(knee_bore_source.__file__): sha(Path(knee_bore_source.__file__)),
            Path(__file__): sha(Path(__file__)),
        }
    )
    for name in ("model.json", "row-identities.json"):
        path = frame / name
        pins[path] = comparison["source_sha256"][str(path.relative_to(ROOT))]
    for path, digest in pins.items():
        require(sha(path) == digest, "changed source: " + str(path))
    model, rows = binding["model"], binding["rows"]
    retained = [row for row in rows if row["ownership"]["second_body"] != "floor"]
    centers = {
        body: np.mean(
            [model["physical_node_coordinates_mm"][str(n)] for n in nodes], axis=0
        )
        for body, nodes in model["body_nodes"].items()
    }
    records, fits = [], []
    with np.load(source / "response.npz", allow_pickle=False) as saved:
        for state in comparison["states"]:
            case, gap = state["case_id"], state["gap_scale"]
            tag = case + ("_gap" if gap else "_zero")
            rigid = saved[tag + "_rigid_coordinates"]
            q = saved[tag + "_lumped_q_mm"]
            require(
                rigid.shape == (6 * len(model["body_names"]),)
                and np.isfinite(rigid).all()
                and np.isfinite(q).all(),
                "invalid saved pose",
            )
            for axis_id, bore in bores.items():
                datum = np.array(bore["head_seat_point_mm"])
                middle = bore["receivers"][1]["member"]
                rigid_poses = {}
                for receiver in bore["receivers"]:
                    body = receiver["member"]
                    offset = 6 * model["body_names"].index(body)
                    rotation = rigid[offset + 3 : offset + 6] / 1000
                    translation = rigid[offset : offset + 3] + np.cross(
                        rotation, datum - centers[body]
                    )
                    rigid_poses[body] = (translation, rotation)
                middle_pose = rigid_poses[middle]
                rigid_poses = {
                    body: (t - middle_pose[0], r - middle_pose[1])
                    for body, (t, r) in rigid_poses.items()
                }
                total_fit = {middle: (np.zeros(3), np.zeros(3))}
                residuals = []
                for receiver in (bore["receivers"][0], bore["receivers"][2]):
                    body = receiver["member"]
                    ports = [
                        i
                        for i, row in enumerate(retained)
                        if {
                            row["ownership"]["first_body"],
                            row["ownership"]["second_body"],
                        }
                        == {body, middle}
                    ]
                    require(len(ports) == 8, "changed knee interface census")
                    mapping = []
                    for i in ports:
                        owner = retained[i]["ownership"]
                        direction = np.array(owner["direction_global_xyz"])
                        sign = 1 if owner["first_body"] == body else -1
                        arm = np.array(owner["point_mm"]) - datum
                        mapping.append(
                            sign * np.r_[direction, np.cross(arm, direction)]
                        )
                    mapping = np.array(mapping)
                    pose, _, rank, _ = np.linalg.lstsq(mapping, q[ports], rcond=None)
                    require(rank == 6, "incomplete local total-motion fit")
                    error = float(np.max(np.abs(mapping @ pose - q[ports])))
                    total_fit[body] = (pose[:3], pose[3:])
                    residuals.append(error)
                    fits.append(
                        {
                            "case_id": case,
                            "gap_scale": gap,
                            "axis_id": axis_id,
                            "body": body,
                            "raw_rows": [retained[i]["row"] for i in ports],
                            "translation_mm": pose[:3].tolist(),
                            "rotation_rad": pose[3:].tolist(),
                            "maximum_projection_residual_mm": error,
                        }
                    )
                for mode, poses in (
                    ("saved_rigid_components", rigid_poses),
                    ("interface_total_motion_fit", total_fit),
                ):
                    records.append(
                        {
                            "case_id": case,
                            "gap_scale": gap,
                            "axis_id": axis_id,
                            "motion_mode": mode,
                            "local_fit_maximum_residual_mm": max(residuals)
                            if mode == "interface_total_motion_fit"
                            else None,
                            **witness(bore, poses, datum),
                        }
                    )
    require(len(records) == 96 and len(fits) == 96, "incomplete placement census")
    for path, digest in pins.items():
        require(sha(path) == digest, "source changed during calculation: " + str(path))
    report = {
        "schema": "knee_straight_shaft_placement/v1",
        "source_scope": scope,
        "frame_operator_directory": str(frame.relative_to(ROOT)),
        "clearance_source_directory": str(source.relative_to(ROOT)),
        "metadata_seed_directory": str(binding["metadata_seed_dir"].relative_to(ROOT)),
        "bore_geometry": bores,
        "records": records,
        "interface_fits": fits,
        "placement_count": len(records),
        "placement_found_count": sum(
            r["straight_shaft_placement_found"] for r in records
        ),
        "maximum_local_projection_residual_mm": max(
            f["maximum_projection_residual_mm"] for f in fits
        ),
        "source_sha256": {str(p.relative_to(ROOT)): h for p, h in pins.items()},
        "complete_bore_deformation_reconstructed": False,
        "loaded_contact_compatibility_established": False,
        "frame_clearance_law_changed": False,
        "complete_joint_acceptance": False,
        "reviewed_geometry_changed": bool(model.get("owner_authorized_screw_movements")),
        "physical_release": False,
    }
    output.mkdir()
    (output / "fit.json").write_text(
        json.dumps(report, indent=2, allow_nan=False) + "\n"
    )
    (output / "producer.py.snapshot").write_bytes(Path(__file__).read_bytes())
    print(
        json.dumps(
            {
                "placement_found_count": report["placement_found_count"],
                "placement_count": len(records),
                "maximum_local_projection_residual_mm": report[
                    "maximum_local_projection_residual_mm"
                ],
                "fit_sha256": sha(output / "fit.json"),
            }
        )
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--frame", type=Path, default=FRAME)
    parser.add_argument("--clearance", type=Path, default=SOURCE)
    parser.add_argument("--metadata-seed", type=Path)
    args = parser.parse_args()
    run(args.output, frame_dir=args.frame, clearance=args.clearance,
        metadata_seed_dir=args.metadata_seed)
