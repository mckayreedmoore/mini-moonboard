"""Necessary gross tipping check from current CAD, masses and applied loads.

Run from the repository root with .venv/bin/python <this file>.
No deformation, connector force, friction qualification or capacity is computed.
"""
from pathlib import Path
import hashlib
import json

import cadquery as cq
import numpy as np
from scipy.spatial import ConvexHull


ROOT = Path(__file__).resolve().parents[4]
BASE = ROOT / "docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24"
MANIFEST = BASE / "current-full-frame-input-manifest-attempt04/current-full-frame-input-manifest.json"
MASS = BASE / "current-mass-centroids-attempt01/mass-centroids.json"
FLOOR_MEMBERS = {
    "base_floor_left", "base_floor_right", "base_post_center_left",
    "base_post_center_right", "base_post_outer_left", "base_post_outer_right",
    "lumber_leg_left", "lumber_leg_right",
}
GRAVITY = 9.80665


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def cop(force, moment):
    """Floor normal resultant and centre from global force/moment balance."""
    normal = -float(force[2])
    if normal <= 0:
        raise ValueError("Positive total downward load required")
    return normal, np.array([moment[1], -moment[0]]) / normal


def self_check():
    # An eccentric downward force and a horizontal force at height h give
    # x_cop = x_load + h*Fx/P, y_cop = y_load + h*Fy/P.
    point = np.array([20., 30., 100.])
    force = np.array([10., -5., -100.])
    normal, centre = cop(force, np.cross(point, force))
    assert normal == 100.
    np.testing.assert_allclose(centre, [30., 25.], atol=1e-12)
    # A vertical floor reaction at the computed point closes Mx and My.
    residual = np.cross(point, force) + np.cross([*centre, 0.], [0., 0., normal])
    np.testing.assert_allclose(residual[:2], 0., atol=1e-12)


def main():
    self_check()
    manifest = json.loads(MANIFEST.read_text())
    mass = json.loads(MASS.read_text())
    if manifest["geometry_revision_id"] != mass["revision_id"]:
        raise ValueError("Revision mismatch")
    pins = {str(p.relative_to(ROOT)): sha(p) for p in (MANIFEST, MASS, Path(__file__))}
    for name, expected in mass["source_sha256"].items():
        actual = sha(ROOT / name)
        if actual != expected:
            raise ValueError("Changed mass source: " + name)
        pins[name] = actual
    rows = mass["rows"]
    total_mass = sum(r["mass_kg"] for r in rows)
    centroid = sum(r["mass_kg"] * np.array(r["mass_center_global_xyz_mm"])
                   for r in rows) / total_mass
    np.testing.assert_allclose(total_mass, mass["modeled_mass_kg"], rtol=1e-12)
    np.testing.assert_allclose(centroid, mass["modeled_mass_center_global_xyz_mm"], atol=1e-8)
    gravity_force = np.array([0., 0., -GRAVITY * total_mass])
    gravity_moment = np.cross(centroid, gravity_force)
    np.testing.assert_allclose(gravity_force, mass["gravity_force_global_xyz_n"], atol=1e-7)
    np.testing.assert_allclose(gravity_moment, mass["gravity_moment_about_global_origin_nmm"], atol=1e-5)
    by_name = {m["member_id"]: m for m in manifest["physical_members"]}
    footprints = []
    points = []
    for name in sorted(FLOOR_MEMBERS):
        member = by_name[name]
        binding = member["current_finished_step_binding"]
        path = ROOT / binding["path"]
        actual = sha(path)
        if actual != binding["file_sha256"]:
            raise ValueError("Changed STEP: " + name)
        pins[binding["path"]] = actual
        shape = cq.importers.importStep(str(path)).val()
        np.testing.assert_allclose(shape.Volume(), member["graph_finished_geometry_summary"]["volume_mm3"], rtol=1e-7)
        floor_faces = [f for f in shape.Faces() if f.geomType() == "PLANE"
                       and abs(f.Center().z) < 1e-6
                       and abs(abs(f.normalAt().z) - 1.) < 1e-8]
        if not floor_faces:
            raise ValueError("No actual floor face: " + name)
        vertices = []
        for face in floor_faces:
            for vertex in face.Vertices():
                x, y, z = vertex.toTuple()
                if abs(z) > 1e-6:
                    raise ValueError("Non-floor vertex")
                vertices.append([float(x), float(y)])
        points.extend(vertices)
        footprints.append({"member_id": name, "planar_area_mm2": sum(f.Area() for f in floor_faces),
                           "floor_face_vertices_xy_mm": vertices})
    points = np.unique(np.round(points, 8), axis=0)
    hull = ConvexHull(points)
    equations = hull.equations  # unit outward normal a,b and offset c: a*x+b*y+c <= 0
    centroid_edges = equations[:, :2] @ centroid[:2] + equations[:, 2]
    if np.any(centroid_edges >= 0):
        raise ValueError("Mass centroid must lie strictly inside the support hull for this screen")
    cases = []
    for case in manifest["applied_load_cases"]["cases"]:
        force = np.array(case["applied_force_global_xyz_n"])
        point = np.array(case["force_application_point_global_xyz_mm"])
        moment = np.cross(point, force)
        reference = np.array(case["wrench_reference_point_global_xyz_mm"])
        np.testing.assert_allclose(moment, np.array(case["moment_global_xyz_nmm"]) + np.cross(reference, force), atol=1e-6)
        if force[2] >= 0:
            raise ValueError("This diagnostic expects the frozen downward climbing loads")
        live_edge = equations[:, :2] @ np.array([moment[1], -moment[0]]) + equations[:, 2] * -force[2]
        required_weight = max(0., float(np.max(live_edge / -centroid_edges)))
        required_mass = required_weight / GRAVITY
        # Check the analytic threshold by independently reconstructing its CoP.
        _, threshold_cop = cop(force + np.array([0., 0., -required_weight]),
                               moment + np.cross(centroid, [0., 0., -required_weight]))
        threshold_edges = equations[:, :2] @ threshold_cop + equations[:, 2]
        assert max(threshold_edges) < 1e-6
        if required_weight > 0:
            assert abs(max(threshold_edges)) < 1e-6
        scenarios = []
        for mass_scale in (0., 0.25, 0.5, 1.):
            total_force = force + mass_scale * gravity_force
            total_moment = moment + mass_scale * gravity_moment
            normal, centre = cop(total_force, total_moment)
            margins = -(equations[:, :2] @ centre + equations[:, 2])
            residual = total_moment + np.cross([*centre, 0.], [0., 0., normal])
            np.testing.assert_allclose(residual[:2], 0., atol=1e-6)
            scenarios.append({"modeled_mass_scale": mass_scale,
                              "mass_kg": total_mass * mass_scale,
                              "required_normal_reaction_n": normal,
                              "required_cop_xy_mm": centre.tolist(),
                              "minimum_support_hull_edge_margin_mm": float(min(margins)),
                              "necessary_normal_resultant_feasible": bool(min(margins) >= -1e-6),
                              "horizontal_reaction_n": (-total_force[:2]).tolist(),
                              "ground_yaw_moment_required_nmm": float(-total_moment[2])})
        cases.append({"case_id": case["case_id"], "minimum_mass_at_frozen_centroid_kg": required_mass,
                      "threshold_cop_xy_mm": threshold_cop.tolist(), "scenarios": scenarios})
    result = {
        "status": "NECESSARY_GLOBAL_EQUILIBRIUM_SCREEN_ONLY",
        "geometry_revision_id": manifest["geometry_revision_id"], "source_sha256": pins,
        "mass_kg": total_mass, "mass_center_xyz_mm": centroid.tolist(),
        "unlocated_equipment_allowance_kg_excluded": mass["equipment_allowance_kg_excluded_from_centroid"],
        "footprints": footprints, "support_hull_xy_mm": points[hull.vertices].tolist(),
        "cases": cases, "mechanical_acceptance": False, "native_solve_run": False,
        "limits": [
            "Whole-assembly necessary force/Mx/My equilibrium only; intact internal transfer is assumed, not demonstrated.",
            "Source modeled masses and centroids are conditional density/CAD estimates, not weighed parts.",
            "Floor remains the existing unverified no-slip analytical assumption; no floor test, anchorage or new connector support is added.",
            "No normal-reaction distribution, individual-foot lift, wood bearing pressure, sliding/friction/yaw capacity, stiffness or member/joint demand is established.",
            "Uniform mass-scale cases preserve this centroid; they are sensitivities, not guaranteed density or equipment-location bounds.",
            "The additional unlocated 25 kg equipment allowance is excluded, not assigned a favorable location.",
            "No criterion disposition or release flag is changed."
        ]}
    output = Path(__file__).with_name("global-equilibrium.json")
    output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({"modeled_mass_kg": total_mass,
                      "cases": [{"case_id": r["case_id"],
                                 "minimum_mass_kg": r["minimum_mass_at_frozen_centroid_kg"],
                                 "full_mass_margin_mm": r["scenarios"][-1]["minimum_support_hull_edge_margin_mm"]}
                                for r in cases]}, indent=2))


if __name__ == "__main__":
    main()
