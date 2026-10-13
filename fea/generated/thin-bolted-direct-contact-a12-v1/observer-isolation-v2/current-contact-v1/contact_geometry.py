"""Current mapped timber surface geometry, without a response or contact law.

The reference-coordinate Jacobian differentiates the frozen geodesic beam
point map. Closest points are local stationary points on its mapped, infinite
reference plane. Own-face bounding boxes supply exclusion only; curves, holes,
global closest-point uniqueness and current overlap remain unestablished.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.util
import json
import sys
from pathlib import Path

import numpy as np
from scipy.optimize import least_squares

ROOT = Path(__file__).resolve().parents[5]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts import thin_bolted_finite_mechanics as mechanics
from scripts.thin_bolted_corotational_methods import skew, so3_exp, so3_log

OWN = Path(__file__).resolve()
TEST = OWN.with_name("test_contact_geometry.py")
CURRENT = OWN.parent.parent
GATE = CURRENT / "admission.py"
GATE_SHA = "4b78722ab407a39d6e00fc9e16be0d370d0c837dea5880e45e7a2e277dd6efb6"
POSE = ROOT / "fea/generated/thin-bolted-joint-wrench-review/review-v4.py"
POSE_SHA = "c86cb3e84c0d16648e6a3d115da686afc6e2c97272cd06c4cbe3bfb93a15be55"
CONFIG = POSE.with_name("input-v4.json")
CONFIG_SHA = "a7ef7b7d82072b7f8898e34551661185f9108b8cca09179875f0f4fa5a005d7d"
FIELD_SHA = "29b25f11794a171a1364268ed676a24cee2882e47c3018b3648267d2707a0ddf"
RECEIPT_SHA = "e5bbf8c0ad2947f42f71819d61b03fcd260a0926b5f5429481e5523ff8e122a5"
ASSESSMENT_SHA = "fac5de9e745ed85331e9f7a5decd80d52935eb8f00872a343657ce628cfabe7b"
LOADED_SHA = hashlib.sha256(OWN.read_bytes()).hexdigest()
LOADED_TEST_SHA = hashlib.sha256(TEST.read_bytes()).hexdigest()


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def canonical(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()).hexdigest()


def vector(value):
    value = np.asarray(value, dtype=float)
    require(value.shape == (3,) and np.isfinite(value).all(), "finite three-vector required")
    return value


def plane_basis(normal):
    normal = vector(normal)
    require(abs(np.linalg.norm(normal) - 1.) < 1e-8, "unit reference own-face normal required")
    u = np.cross(normal, np.eye(3)[np.argmin(abs(normal))])
    u /= np.linalg.norm(u)
    return np.column_stack((u, np.cross(normal, u)))


def surface_state(row, q, reference_point, reference_normal):
    """Exact reference-coordinate derivative of the frozen point interpolation.

    A rigid endpoint extension reproduces the frozen provider outside its
    axial chart. It is flagged separately. At an internal station the frozen
    left-segment selection supplies one derivative, not a smooth cross-node
    surface. No rotation-vector averaging or shaft pose lift is used here.
    """
    require(row.get("kind") == "timber", "timber material chart required")
    q = np.asarray(q, dtype=float)
    require(q.ndim == 1 and np.isfinite(q).all(), "finite mapped coefficient vector required")
    point, normal = vector(reference_point), vector(reference_normal)
    plane_basis(normal)
    stations = np.asarray(row["reference_stations_mm"], dtype=float)
    centers = np.asarray(row["node_reference_centers_xyz_mm"], dtype=float)
    indices = np.asarray(row["node_dof_indices"], dtype=int)
    basis = np.asarray(row["storage_basis_columns_xyz"], dtype=float)
    axis, start = vector(row["reference_axis_xyz"]), vector(row["reference_start_xyz_mm"])
    require(stations.ndim == 1 and len(stations) >= 2 and np.all(np.diff(stations) > 0.)
            and centers.shape == (len(stations), 3) and indices.shape == (len(stations), 6)
            and np.all(indices >= 0) and np.all(indices < len(q))
            and abs(np.linalg.norm(axis) - 1.) < 1e-8
            and basis.shape == (3, 3) and np.linalg.norm(basis.T @ basis - np.eye(3)) < 1e-8
            and abs(np.linalg.det(basis) - 1.) < 1e-8
            and np.max(abs(centers - start - stations[:, None] * axis)) < 1e-7,
            "ordered proper finite timber chart required")
    station = float((point - start) @ axis)
    segment = int(np.clip(np.searchsorted(stations, station) - 1, 0, len(stations) - 2))
    length = float(stations[segment + 1] - stations[segment])
    raw_t = (station - stations[segment]) / length
    t = float(np.clip(raw_t, 0., 1.))
    state = q[indices[segment:segment + 2].ravel()].reshape(2, 6)
    local_centers = centers[segment:segment + 2]
    rotation = mechanics.interpolated_rotation(state.ravel(), t, basis)[0]
    position = mechanics.interpolated_point(point, local_centers, state.ravel(), t, basis)[0]
    center = (1. - t) * local_centers[0] + t * local_centers[1]
    arm = point - center
    # R(t)=R0 Exp(t omega). The term below also includes centerline shear.
    node_rotations = [so3_exp(basis @ node[3:] / 1000.) for node in state]
    omega = so3_log(node_rotations[0].T @ node_rotations[1])
    reference_chord = local_centers[1] - local_centers[0]
    current_chord = reference_chord + basis @ (state[1, :3] - state[0, :3])
    derivative = rotation.copy()
    clipped = bool(raw_t < 0. or raw_t > 1.)
    if not clipped:
        correction = current_chord - rotation @ reference_chord + rotation @ skew(omega) @ arm
        derivative += np.outer(correction, axis) / length
    determinant = float(np.linalg.det(derivative))
    require(determinant > 1e-10, "mapped local timber orientation is singular or inverted")
    geometric_normal = np.linalg.solve(derivative.T, normal)
    geometric_normal /= np.linalg.norm(geometric_normal)
    material_normal = rotation @ normal
    angle = float(np.arctan2(np.linalg.norm(np.cross(geometric_normal, material_normal)),
                             geometric_normal @ material_normal))
    return {"position": position, "reference_coordinate_jacobian": derivative,
            "geometric_normal": geometric_normal, "material_normal": material_normal,
            "geometric_vs_material_normal_angle_rad": angle, "jacobian_determinant": determinant,
            "reference_axial_station_mm": station, "segment_index": segment,
            "raw_segment_fraction": float(raw_t), "rigid_endpoint_extension_used": clipped,
            "at_internal_station_derivative_is_one_sided": bool(np.any(abs(stations[1:-1] - station) < 1e-8)),
            "at_any_station_derivative_is_one_sided": bool(np.any(abs(stations - station) < 1e-8))}


def closest_point(row, q, plane_origin, plane_normal, target, *, maximum_evaluations=100):
    """Local closest point on the mapped infinite own material plane.

    The second-order certificate tests this stationary point, not uniqueness
    over the entire face. A point outside the own reference-face bounding box
    is excluded from that face; an inside point still needs trimmed occupancy.
    """
    origin, target, normal = vector(plane_origin), vector(target), vector(plane_normal)
    directions = plane_basis(normal)
    initial = surface_state(row, q, origin, normal)
    seed = directions.T @ np.linalg.solve(initial["reference_coordinate_jacobian"], target - initial["position"])

    def state(uv):
        return surface_state(row, q, origin + directions @ uv, normal)

    def residual(uv):
        return state(uv)["position"] - target

    def jacobian(uv):
        return state(uv)["reference_coordinate_jacobian"] @ directions

    fit = least_squares(residual, seed, jac=jacobian, max_nfev=maximum_evaluations,
                        ftol=1e-12, xtol=1e-12, gtol=1e-12)
    observed = state(fit.x)
    delta, tangent = observed["position"] - target, jacobian(fit.x)
    stationarity = tangent.T @ delta
    step = 1e-3
    stencil = [observed] + [state(fit.x + sign * perturbation)
        for perturbation in np.eye(2) * step for sign in (-1., 1.)]
    smooth_stencil = bool(len({(value["segment_index"], value["rigid_endpoint_extension_used"])
                              for value in stencil}) == 1
                          and not any(value["at_any_station_derivative_is_one_sided"] for value in stencil))
    hessian = np.column_stack([
        (jacobian(fit.x + perturbation).T @ residual(fit.x + perturbation)
         - jacobian(fit.x - perturbation).T @ residual(fit.x - perturbation)) / (2. * step)
        for perturbation in np.eye(2) * step])
    asymmetry = float(np.max(abs(hessian - hessian.T)))
    minimum_eigenvalue = float(np.linalg.eigvalsh(.5 * (hessian + hessian.T))[0])
    certified = bool(fit.success and np.max(abs(stationarity)) < 1e-7
                     and minimum_eigenvalue > 1e-8 and asymmetry < 1e-5
                     and smooth_stencil)
    return {"reference_footpoint_xyz_mm": (origin + directions @ fit.x).tolist(),
            "current_footpoint_xyz_mm": observed["position"].tolist(),
            "current_geometric_normal_xyz": observed["geometric_normal"].tolist(),
            "gap_opening_positive_mm": float((target - observed["position"]) @ observed["geometric_normal"]),
            "distance_mm": float(np.linalg.norm(delta)), "stationarity_inf_mm": float(np.max(abs(stationarity))),
            "local_distance_hessian_minimum_eigenvalue": minimum_eigenvalue,
            "local_distance_hessian_asymmetry": asymmetry,
            "local_stationary_closest_point_certified": certified,
            "global_closest_point_unique": False, "reference_plane_uv_mm": fit.x.tolist(),
            "evaluations": int(fit.nfev), "termination": fit.message,
            "rigid_endpoint_extension_used": observed["rigid_endpoint_extension_used"],
            "at_internal_station_derivative_is_one_sided": observed["at_internal_station_derivative_is_one_sided"],
            "at_any_station_derivative_is_one_sided": observed["at_any_station_derivative_is_one_sided"],
            "distance_hessian_stencil_remains_in_one_smooth_branch": smooth_stencil}


def load(path, expected, name):
    require(sha(path) == expected, "contact geometry module source differs")
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    require(sha(path) == expected, "contact geometry module changed during loading")
    return module


def verify(pins):
    for path, expected in pins.items():
        require(sha(ROOT / path) == expected, "contact geometry source changed: " + path)


def observe_current(field, gate, method):
    config = json.loads(CONFIG.read_bytes())
    cold_paths = {row["path"] for row in config["cold_diagnostic_sources"]}
    pins = {path: value for path, value in config["source_sha256"].items() if path not in cold_paths}
    verify(pins)
    keys = ("layout", "timber_unit_geometry", "geometry_cache", "panel_metadata", "panel_assessment", "integrated_geometry")
    layout, unit, cache, metadata, assessment, integrated = [json.loads((ROOT / config[key]).read_bytes()) for key in keys]
    geometry = gate.read_complete_geometry()
    gate.linear.verify_timber_map(field, cache, geometry["grain_geometry"])
    view = {**field, "response": {"diagnostic_last_q": field["response"]["q"]}}
    mapping, q, _ = method.make_map(view, layout, method.shaft_inputs(layout, unit, cache), metadata, assessment, integrated)
    # Only timber rows are consumed; appended shaft gauge values are unused.
    actions = {row["id"]: row for row in field["timber_face_contact_actions"]}
    require(len(actions) == 584 and geometry["pair_count"] == 30 and geometry["cell_count"] == 584,
            "all30/584 current timber markers required")
    result = []
    for _, _, patch in geometry["patch_sources"]:
        for cell in patch["cells"]:
            point = vector(cell["point_xyz_mm"])
            first, second = patch["first"], patch["second"]
            normal = vector(patch["normal_from_second_to_first_xyz"])
            a = surface_state(mapping["mechanical_bodies"][first], q, point, -normal)
            b = surface_state(mapping["mechanical_bodies"][second], q, point, normal)
            foot = closest_point(mapping["mechanical_bodies"][second], q, point, normal, a["position"])
            own = patch["source_second_face"]["signature"]
            bounds = np.asarray(own["bounds_xyz_mm"]).reshape(3, 2)
            reference_foot = vector(foot["reference_footpoint_xyz_mm"])
            outside = float(np.max(np.maximum(bounds[:, 0] - reference_foot, reference_foot - bounds[:, 1])))
            action = actions[cell["id"]]
            require(action["first"] == first and action["second"] == second
                    and all(action[key] == field[key] for key in ("state_id", "case_id", "accessory_placement")),
                    "current timber marker action ownership/state differs")
            delta = a["position"] - b["position"]
            material_gap = float(b["material_normal"] @ delta)
            true_gap = float(b["geometric_normal"] @ delta)
            result.append({"id": cell["id"], "patch_id": patch["id"], "first": first, "second": second,
                "reference_cell_area_mm2": cell["area_mm2"], "reference_cell_point_xyz_mm": point.tolist(),
                "recorded_linear_compression_n": action["compression_n"],
                "first_geometric_vs_material_normal_angle_rad": a["geometric_vs_material_normal_angle_rad"],
                "second_geometric_vs_material_normal_angle_rad": b["geometric_vs_material_normal_angle_rad"],
                "first_reference_jacobian_determinant": a["jacobian_determinant"],
                "second_reference_jacobian_determinant": b["jacobian_determinant"],
                "first_rigid_endpoint_extension_used": a["rigid_endpoint_extension_used"],
                "second_rigid_endpoint_extension_used": b["rigid_endpoint_extension_used"],
                "fixed_material_point_gap_using_material_normal_mm": material_gap,
                "fixed_material_point_gap_using_geometric_normal_mm": true_gap,
                "geometric_normal_gap_correction_mm": true_gap - material_gap,
                "local_closest_point": foot, "reference_own_face_bbox_maximum_excess_mm": max(0., outside),
                "local_footpoint_definitely_outside_own_face_bbox": bool(outside > 1e-7),
                "trimmed_own_face_occupancy_established": False, "current_overlap_area_established": False})
    require(len(result) == len({row["id"] for row in result}) == 584 and set(actions) == {row["id"] for row in result},
            "complete current marker identity census required")
    return result, gate.linear.merge_pins(pins, geometry["source_sha256"]), method.canonical(mapping)


def consume(field_path, receipt_path, assessment_path):
    """Authenticate exact admitted current bytes before consuming any q."""
    paths = [(field_path, FIELD_SHA), (receipt_path, RECEIPT_SHA), (assessment_path, ASSESSMENT_SHA)]
    pins = {str(path.relative_to(ROOT)): expected for path, expected in
            ((OWN, LOADED_SHA), (TEST, LOADED_TEST_SHA), (GATE, GATE_SHA), (POSE, POSE_SHA), (CONFIG, CONFIG_SHA))}
    for path, expected in paths:
        require(sha(path) == expected, "exact current contact diagnostic input differs")
        pins[str(Path(path).resolve().relative_to(ROOT))] = expected
    verify(pins)
    gate = load(GATE, GATE_SHA, "current_contact_actual_gate")
    payload = Path(field_path).read_bytes()
    receipt = json.loads(Path(receipt_path).read_bytes())
    field, admitted = gate.require_admitted_payload(payload, receipt, admission_sha256=GATE_SHA)
    assessment = json.loads(Path(assessment_path).read_bytes())
    require(assessment["field_sha256"] == FIELD_SHA
            and all(assessment[key] == field[key] for key in ("state_id", "case_id", "accessory_placement"))
            and not any(field["release"].values()), "current assessment/source/state join required")
    method = load(POSE, POSE_SHA, "current_contact_frozen_pure_map")
    before, receipt_before = canonical(field), canonical(receipt)
    rows, observed_pins, map_sha = observe_current(field, gate, method)
    pins = gate.linear.merge_pins(pins, admitted, observed_pins, mechanics.source_pins())
    verify(pins)
    require(canonical(field) == before and canonical(receipt) == receipt_before,
            "current source payloads mutated during contact geometry observation")
    for path, expected in paths:
        require(sha(path) == expected, "current source bytes changed during observation")
    loaded = [row for row in rows if row["recorded_linear_compression_n"] > 0.]
    metrics = ("first_geometric_vs_material_normal_angle_rad", "second_geometric_vs_material_normal_angle_rad",
               "geometric_normal_gap_correction_mm", "reference_own_face_bbox_maximum_excess_mm")
    return {"schema": "thin_bolted_admitted_current_timber_surface_geometry/v1",
        **{key: field[key] for key in ("state_id", "case_id", "accessory_placement")},
        "field_sha256": FIELD_SHA, "assessment_sha256": ASSESSMENT_SHA, "actual_admission_sha256": GATE_SHA,
        "field_canonical_sha256": before, "q_canonical_sha256": canonical(field["response"]["q"]),
        "pure_map_sha256": map_sha, "source_sha256": pins, "counts": {"pairs": 30, "markers": 584,
            "recorded_linear_loaded_markers": len(loaded),
            "certified_local_closest_points": sum(row["local_closest_point"]["local_stationary_closest_point_certified"] for row in rows),
            "closest_footpoints_definitely_outside_own_reference_bbox": sum(row["local_footpoint_definitely_outside_own_face_bbox"] for row in rows),
            "recorded_loaded_footpoints_definitely_outside_own_reference_bbox": sum(row["local_footpoint_definitely_outside_own_face_bbox"] for row in loaded)},
        "governing_markers": {key: copy.deepcopy(max(rows, key=lambda row: abs(row[key]))) for key in metrics},
        "all584_markers": rows, "method": {"frozen_finite_point_map_reused": True,
            "actual_reference_coordinate_jacobian_derived": True, "transported_material_normal_and_geometric_normal_distinguished": True,
            "shaft_material_director_derived_from_zero_linear_roll": False,
            "K_response_force_tangent_or_global_solve_evaluated": False},
        "limits": ["Fixed admitted linear q is only a geometry diagnostic; no physical motion or new equilibrated demand is asserted.",
            "Local stationary projections onto infinite material planes are certified locally, not globally unique or constrained to occupied trimmed faces.",
            "Own-face reference bounding boxes exclude exterior pullbacks only. Curved edges, holes, exact surviving overlap and new pressure integration remain unresolved.",
            "Beam station surfaces are piecewise smooth; one-sided internal station and rigid endpoint-extension flags are retained.",
            "Full finite contact response still needs current overlap, consistent energy/gradient/geometric tangent, objective shaft quotient, dead-load mapping and body/global equilibrium with the newly declared finite8foot law."],
        "release": copy.deepcopy(field["release"])}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--field", type=Path, default=CURRENT / "a12-rear.json")
    parser.add_argument("--receipt", type=Path, default=CURRENT / "admission.json")
    parser.add_argument("--assessment", type=Path, default=CURRENT / "assessment.json")
    parser.add_argument("--out", type=Path, required=True)
    options = parser.parse_args()
    require(not options.out.exists(), "preserve existing current contact geometry output")
    result = consume(options.field, options.receipt, options.assessment)
    with options.out.open("x") as stream:
        stream.write(json.dumps(result, separators=(",", ":"), allow_nan=False) + "\n")
    print(json.dumps({"path": str(options.out), "sha256": sha(options.out), "counts": result["counts"]}))


if __name__ == "__main__":
    main()
