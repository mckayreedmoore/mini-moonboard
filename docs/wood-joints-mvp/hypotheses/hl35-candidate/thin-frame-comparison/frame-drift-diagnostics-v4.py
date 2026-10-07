"""Saved-field small-displacement applicability markers; no new solve."""

import json
from collections import defaultdict
from pathlib import Path

import numpy as np

from scripts import thin_bolted_frame_mechanics as mechanics


def main():
    field = mechanics.PACKET / "compatible-frame-a12-rear-v4.json"
    out = mechanics.PACKET / "frame-first-order-drift-v4.json"
    if out.exists():
        raise FileExistsError("preserve drift diagnostics")
    report = json.loads(field.read_text())
    layout = json.loads(mechanics.LAYOUT.read_text())
    q = np.array(report["response"]["q"])
    by_member = defaultdict(list)
    for row in report["member_element_actions"]:
        by_member[row["member"]].append(row)
    sections = {row["member"]: row["sampled_extrema"] for row in report["member_section_action_samples"]}
    members = {}
    offset = 0
    markers = []
    for name, rows in by_member.items():
        points = np.array([rows[0]["start_xyz_mm"], *[row["end_xyz_mm"] for row in rows]])
        nodal = q[offset:offset + 6 * len(points)].reshape(-1, 6)
        offset += 6 * len(points)
        grain = np.array(rows[0]["basis_grain_u_v_xyz"][0])
        s = (points - points[0]) @ grain
        chord = nodal[0, :3] + (s / s[-1])[:, None] * (nodal[-1, :3] - nodal[0, :3])
        bow = nodal[:, :3] - chord
        bow -= (bow @ grain)[:, None] * grain
        end_shift = nodal[-1, :3] - nodal[0, :3]
        end_shift -= (end_shift @ grain) * grain
        translation_norm = np.linalg.norm(nodal[:, :3], axis=1)
        rotation_norm = np.linalg.norm(nodal[:, 3:] / mechanics.ROTATION_SCALE, axis=1)
        j, k = int(translation_norm.argmax()), int(rotation_norm.argmax())
        axial_marker = abs(sections[name]["axial_n"]["signed_action"])
        bending_marker = np.hypot(sections[name]["bending_u_nmm"]["signed_action"], sections[name]["bending_v_nmm"]["signed_action"])
        marker = {"member": name, "maximum_node_translation_norm_mm": float(translation_norm[j]),
                  "translation_node_point_xyz_mm": points[j].tolist(),
                  "maximum_node_rotation_norm_rad": float(rotation_norm[k]),
                  "rotation_node_point_xyz_mm": points[k].tolist(),
                  "chord_relative_transverse_bow_mm": float(np.linalg.norm(bow, axis=1).max()),
                  "end_relative_transverse_shift_mm": float(np.linalg.norm(end_shift)),
                  "maximum_absolute_axial_component_marker_n": axial_marker,
                  "N_times_end_shift_scale_nmm": float(axial_marker * np.linalg.norm(end_shift)),
                  "N_times_bow_scale_nmm": float(axial_marker * np.linalg.norm(bow, axis=1).max()),
                  "separate_extrema_bending_norm_marker_nmm": float(bending_marker),
                  "is_a_second_order_solution_or_capacity_check": False}
        markers.append(marker)
        members[name] = {"points": points, "s": s, "q": nodal, "grain": grain}
    fittings = {}
    for fitting in layout["raw_fittings"]:
        fittings[fitting["angle_id"]] = {"q": q[offset:offset + 12].reshape(2, 6),
            "points": {h["flange"]: np.array(h["entry_xyz_mm"]) for h in fitting["holes"]}}
        offset += 12

    def arm_correction(body, point, flange=None):
        point = np.array(point)
        if body in members:
            member = members[body]
            s = float((point - member["points"][0]) @ member["grain"])
            i = int(np.clip(np.searchsorted(member["s"], s) - 1, 0, len(member["s"]) - 2))
            a, b = member["s"][i:i + 2]
            t = float(np.clip((s - a) / (b - a), 0., 1.))
            center = (1 - t) * member["points"][i] + t * member["points"][i + 1]
            nodal = (1 - t) * member["q"][i] + t * member["q"][i + 1]
        else:
            i = 0 if flange == "beam" else 1
            center, nodal = fittings[body]["points"][flange], fittings[body]["q"][i]
        rotation = nodal[3:] / mechanics.ROTATION_SCALE
        angle = float(np.linalg.norm(rotation))
        cross = mechanics.cross_matrix(rotation)
        R = (np.eye(3) + np.sin(angle) / angle * cross
             + (1 - np.cos(angle)) / angle**2 * cross @ cross) if angle > 1e-10 else np.eye(3) + cross + .5 * cross @ cross
        arm = point - center
        return nodal[:3] + cross @ arm, (R - np.eye(3) - cross) @ arm

    contacts = []
    for row in [*report["flange_contact_actions"], *[r for r in report["floor_actions"] if r["kind"] == "floor_normal"]]:
        if row["kind"] == "floor_normal":
            linear, correction = arm_correction(row["first"], row["point_xyz_mm"])
            gap, change, stiffness = -linear[2], -correction[2], report["parameters"]["floor_corner_contact_n_mm"]
        else:
            u1, c1 = arm_correction(row["first"], row["point_xyz_mm"], row["flange"])
            u2, c2 = arm_correction(row["second"], row["point_xyz_mm"])
            force = np.array(row["force_on_first_xyz_n"])
            if row["compression_n"] > 0:
                normal = force / row["compression_n"]
            else:
                fitting = next(f for f in layout["raw_fittings"] if f["angle_id"] == row["angle_id"])
                normal = np.array(fitting["v_xyz"] if row["flange"] == "beam" else fitting["u_xyz"])
            gap, change = float((u2 - u1) @ normal), float((c2 - c1) @ normal)
            stiffness = report["parameters"]["flange_corner_contact_n_mm"]
        recomputed = stiffness * max(gap, 0.)
        if abs(recomputed - row["compression_n"]) > 1e-5:
            raise ValueError("reconstructed linear contact force differs")
        contacts.append({"id": row["id"], "kind": row["kind"], "linear_closure_mm": float(gap),
                         "exact_rotation_arm_closure_change_mm": float(change),
                         "old_compression_n": row["compression_n"],
                         "unsolved_exact_arm_contact_force_change_n": float(stiffness * max(gap + change, 0.) - row["compression_n"]),
                         "active_side_would_change_at_fixed_field": bool((gap > 0.) != (gap + change > 0.))})
    result = {"schema": "thin_bolted_saved_field_drift_diagnostics/v1", "candidate": report["candidate"],
              "state_id": report["state_id"], "source_sha256": {
                  str(field.relative_to(mechanics.ROOT)): mechanics.sha(field),
                  str(Path(__file__).resolve().relative_to(mechanics.ROOT)): mechanics.sha(Path(__file__)),
                  "scripts/thin_bolted_frame_mechanics.py": mechanics.sha(Path(mechanics.__file__)),
                  str(mechanics.LAYOUT.relative_to(mechanics.ROOT)): mechanics.LAYOUT_SHA},
              "command": "OPENBLAS_NUM_THREADS=1 PYTHONPATH=. .venv/bin/python docs/wood-joints-mvp/hypotheses/hl35-candidate/thin-frame-comparison/frame-drift-diagnostics-v4.py",
              "member_drift_markers": markers,
              "maximum_exact_arm_contact_closure_change_mm": max(abs(r["exact_rotation_arm_closure_change_mm"]) for r in contacts),
              "maximum_unsolved_exact_arm_contact_force_change_n": max(abs(r["unsolved_exact_arm_contact_force_change_n"]) for r in contacts),
              "fixed_field_contact_active_side_changes": sum(r["active_side_would_change_at_fixed_field"] for r in contacts),
              "largest_contact_changes": sorted(contacts, key=lambda r: abs(r["unsolved_exact_arm_contact_force_change_n"]), reverse=True)[:12],
              "disposition": "FIRST_ORDER_APPLICABILITY_REQUIRES_RESOLUTION",
              "limits": ["The source field uses four absent raw-leg floor ports; the finished-floor correction must be solved separately.",
                         "N times displacement values are diagnostic scales using separate component extrema; they are neither same-cut second-order moments nor demand bounds.",
                         "Exact Rodrigues rigid-arm updates are evaluated at the unchanged first-order field. No equilibrium, material-axis, plate-kinematic, shaft-contact or load-location update is solved.",
                         "Changed contact forces cannot be added to the original actions as accepted demands. No instability or adopted drift-limit failure is concluded."],
              "release": mechanics.RELEASE, "second_order_demands_established": False}
    out.write_text(json.dumps(result, separators=(",", ":")) + "\n")
    print(json.dumps({"path": str(out), "sha256": mechanics.sha(out), "maximum_arm_closure_change_mm": result["maximum_exact_arm_contact_closure_change_mm"],
                      "maximum_unsolved_force_change_n": result["maximum_unsolved_exact_arm_contact_force_change_n"],
                      "active_side_changes": result["fixed_field_contact_active_side_changes"]}))


if __name__ == "__main__":
    main()
