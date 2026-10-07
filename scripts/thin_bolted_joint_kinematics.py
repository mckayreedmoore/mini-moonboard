"""Isolated-joint kinematic diagnostics for the frozen thin-frame proposal.

An ideal revolute connector constrains three point translations and two axis
rotations. It leaves rotation about the shaft free. This deliberately supplies
no torque/friction stiffness, allowable load or global frame acceptance.
Timber/steel flexibility, gaps and compression-only contact need later methods.
"""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path

import numpy as np

from mini_moonboard.bolted_joint_mechanics import cross
from scripts import hl35_candidate as shared

LAYOUT = shared.PACKET / "thin-frame-comparison/mixed-offset-rows-shallow-wires-v4.json"
LAYOUT_SHA = "8174841bf64914570397ee6d960c5602f74097e2e412e5910502811bc5b9405c"
OUTPUT = LAYOUT.parent / "isolated-joint-kinematics-v4.json"


def hinge_matrix(bodies: list[str], hinges: list[dict], ground: str,
                 reference_mm: list[float], rotation_scale_mm: float = 100.) -> np.ndarray:
    """A q = 0 for infinitesimal rigid bodies at one common reference point.

    Each body's q is (u_x,u_y,u_z,L*theta_x,L*theta_y,L*theta_z).
    Point velocity is u + theta cross (p-reference). Two transverse-axis
    projections set the relative rotation normal to the shaft to zero.
    Rotational rows are multiplied by L to retain consistent numerical units.
    """
    if not np.isfinite(rotation_scale_mm) or rotation_scale_mm <= 0:
        raise ValueError("rotation scale must be positive")
    if len(set(bodies)) != len(bodies) or ground in bodies:
        raise ValueError("moving bodies must be unique and exclude ground")
    indices = {name: i for i, name in enumerate(bodies)}
    reference = np.asarray(reference_mm, dtype=float)
    if reference.shape != (3,) or not np.isfinite(reference).all():
        raise ValueError("reference must be a finite point")
    blocks = []
    for hinge in hinges:
        point, axis = [np.asarray(hinge[k], dtype=float) for k in ("point_mm", "axis")]
        if point.shape != (3,) or axis.shape != (3,) or not np.isfinite([point, axis]).all() or np.linalg.norm(axis) < 1e-12:
            raise ValueError("hinge requires a finite point and nonzero axis")
        axis /= np.linalg.norm(axis)
        other = np.eye(3)[np.argmin(np.abs(axis))]
        e1 = np.cross(axis, other); e1 /= np.linalg.norm(e1)
        e2 = np.cross(axis, e1)
        r = point - reference
        skew = np.column_stack([cross(tuple(r), tuple(unit)) for unit in np.eye(3)])
        row = np.zeros((5, 6 * len(bodies)))
        block = np.vstack((np.hstack((np.eye(3), -skew / rotation_scale_mm)),
                           np.hstack((np.zeros((2, 3)), np.vstack((e1, e2))))))
        for name, sign in ((hinge["first"], 1.), (hinge["second"], -1.)):
            if name == ground:
                continue
            if name not in indices:
                raise ValueError(f"unknown hinge body: {name}")
            offset = 6 * indices[name]
            row[:, offset:offset + 6] += sign * block
        blocks.append(row)
    return np.vstack(blocks) if blocks else np.zeros((0, 6 * len(bodies)))


def rank_diagnostic(matrix: np.ndarray) -> dict:
    singular = np.linalg.svd(matrix, compute_uv=False)
    threshold = max(matrix.shape, default=1) * max(float(singular.max()), 1.) * 1e-10 if singular.size else 1e-10
    rank = int(np.count_nonzero(singular > threshold))
    return {"constraint_rows": matrix.shape[0], "moving_body_variables": matrix.shape[1],
            "rank": rank, "isolated_joint_free_motions": matrix.shape[1] - rank,
            "rank_threshold": threshold, "singular_values": singular.tolist()}


def evaluate() -> dict:
    if shared.sha(LAYOUT) != LAYOUT_SHA:
        raise ValueError("frozen occupied source differs")
    source = json.loads(LAYOUT.read_text())
    by_duty = defaultdict(list)
    for fitting in source["raw_fittings"]:
        by_duty[fitting["duty_id"]].append(fitting)
    results = []
    for duty, fittings in by_duty.items():
        beams, posts = {f["beam"] for f in fittings}, {f["post"] for f in fittings}
        if len(beams) != 1 or len(posts) != 1:
            raise ValueError("per-duty screen requires one beam and one post")
        beam, post = next(iter(beams)), next(iter(posts))
        bodies = [beam, *[f["angle_id"] for f in fittings]]
        hinges, outside = [], []
        for axis in source["installed_axes"]:
            for attachment in axis["attachments"]:
                if attachment["angle_id"] not in bodies:
                    continue
                hinges.append({"id": axis["id"], "first": attachment["receiver"],
                               "second": attachment["angle_id"],
                               "point_mm": axis["point"], "axis": axis["direction"]})
                outside.extend(a["angle_id"] for a in axis["attachments"]
                               if a["angle_id"] not in bodies)
        reference = np.mean([h["point_mm"] for h in hinges], axis=0).tolist()
        diagnostics = [rank_diagnostic(hinge_matrix(bodies, hinges, post, reference, scale))
                       for scale in (10., 100., 1000.)]
        if len({r["rank"] for r in diagnostics}) != 1:
            raise ValueError(f"rank depends on coordinate scaling: {duty}")
        results.append({"duty": duty, "beam": beam, "grounded_post_for_local_screen": post,
                        "rigid_fittings": [f["angle_id"] for f in fittings],
                        "unique_physical_axes": sorted({h["id"] for h in hinges}),
                        "hinges": hinges, "reference_xyz_mm": reference,
                        "excluded_shared_axis_other_duty_angles": sorted(set(outside)),
                        "scale_sensitivity_rank_agrees": True, **diagnostics[1],
                        "assembled_frame_mechanism": None,
                        "required_load_space_or_capacity_checked": False})
    if len(results) != 24:
        raise ValueError("expected twenty-four isolated source duties")
    return {"schema": "thin_bolted_isolated_joint_kinematics/v1", "candidate": source["candidate"],
            "revision": source["revision"], "question": "Which rotations remain free when each thin-frame duty is modeled with friction-free ideal bolt hinges?",
            "source_sha256": {str(LAYOUT.relative_to(shared.ROOT)): LAYOUT_SHA,
                              str(Path(__file__).relative_to(shared.ROOT)): shared.sha(Path(__file__)),
                              "mini_moonboard/bolted_joint_mechanics.py": shared.sha(shared.ROOT / "mini_moonboard/bolted_joint_mechanics.py"),
                              "uv.lock": shared.sha(shared.ROOT / "uv.lock")},
            "method": {"point_velocity": "u + theta cross (p-reference)",
                       "relative_axis_rotation": "two orthogonal projections perpendicular to shaft equal zero",
                       "shaft_axis_rotation_constrained": False, "bolt_or_contact_friction_credited": False,
                       "contact_included": False, "rigid_timber_and_steel": True,
                       "bilateral_no_gap_hinges": True, "numpy_version": np.__version__,
                       "native_finite_element_solve": False},
            "counts": {"isolated_duties": len(results),
                       "single_fitting_duties": sum(len(r["rigid_fittings"]) == 1 for r in results),
                       "paired_fitting_duties": sum(len(r["rigid_fittings"]) == 2 for r in results)},
            "duties": results, "release": shared.RELEASE,
            "limits": ["These are local rigid-body kinematics, not fresh frame demands or capacities.",
                       "Other duties, panel screws, bearing contact and floor constraints are excluded; local freedom is not an assembled-frame instability result.",
                       "Real bearing/clearance and steel/bolt/washer flexibility need separate stiffness/contact methods.",
                       "A shared shaft does not become two independent bolt axes or acquire torque about itself.",
                       "Use the complete assembled load path and signed wrenches before deciding whether any free local motion is acceptable."]}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=OUTPUT)
    args = parser.parse_args()
    if args.out.exists():
        raise FileExistsError("preserve prior kinematic evidence")
    report = evaluate()
    args.out.write_text(json.dumps(report, indent=2, allow_nan=False) + "\n")
    print(json.dumps({"counts": report["counts"], "isolated_free_motion_counts": {
        str(n): sum(r["isolated_joint_free_motions"] == n for r in report["duties"])
        for n in sorted({r["isolated_joint_free_motions"] for r in report["duties"]})}}, indent=2))


if __name__ == "__main__":
    main()
