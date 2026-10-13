"""Current finite-coordinate ownership and circular-shaft gauge checks.

Reuse the frozen ownership and finite shaft methods on authenticated current
fields. Saved first-order poses are diagnostic inputs, not finite equilibria.
No frame potential, native solve, geometry change or resistance is supplied.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path

import numpy as np

from scripts import eoere_current_components as component
from scripts import eoere_current_response as current
from scripts import eoere_current_washer_lands as intake_source
from scripts import thin_bolted_isotropic_shaft as shaft
from scripts.summarize_eoere_current_response import SEQUENCE, canonical_sha

OWN = Path(__file__).resolve()
LOADED_SHA = current.sha(OWN)
INTAKE = {"path": "scripts/eoere_current_washer_lands.py",
          "sha256": "d759bcab2d92bcb709f24726c324d83426483e2fd650dff80775ec0aa17b74d9"}
PARTITION = {
    "path": "fea/generated/thin-bolted-current-contact-v1/eoere-successor-v1/finite-integration-v1/integration.py",
    "sha256": "e84c1d8fb2f9e2cee9324a89701c3e358662a7fc4453773a4ff72ba6387a5f24",
}
SHAFT = {"path": "scripts/thin_bolted_isotropic_shaft.py",
         "sha256": "be8e5277999aa2ce01b4a8d81c0e9124dad9dc6023712c13e91595600c1c027a"}
FAMILIES = {"timber": 22, "fitting": 22, "shaft": 100, "panel": 6}
LOAD_COUNTS = {"timber": 88, "fitting": 22, "shaft": 508, "panel": 217}
CONTACT_COUNTS = {"common_shaft_bearing": 416, "panel_screw": 66,
                  "flange_contact": 352, "panel_contact": 922,
                  "timber_face_contact": 332, "shaft_end_capture": 200,
                  "floor_normal": 32, "floor_tangent": 16}


def own_ref():
    current.require(current.sha(OWN) == LOADED_SHA, "loaded finite preflight producer changed")
    return {"path": str(OWN.relative_to(current.ROOT)), "sha256": LOADED_SHA}


def current_partition(method, chart, loads, sources):
    """Apply the unchanged pure partition to the current owned coordinate map."""
    result = method.ownership_partition(chart, loads, [s["body"] for s in sources],
                                        expected_counts=FAMILIES)
    current.require(result["first_order_ndof"] == result["prospective_quotient_ndof"] == 9350
                    and result["prospective_full_ndof"] == 9450,
                    "current 9350/9450 coordinates required; older map cannot transfer")
    current.require({k: len(v) for k, v in result["load_ids_by_family"].items()} == LOAD_COUNTS,
                    "current 835 loads including eight own spacer loads required")
    for source in sources:
        row = chart["shafts"][source["body"]]
        keys = ["axis_id", "basis", "diameter_mm", "point", "surfaces", "ends"]
        current.require(all(row[k] == source[k] for k in keys), "own current shaft source/map differs")
    fitting_loads = [load["body"] for load in loads if load["body"] in chart["four_port_fittings"]]
    current.require(Counter(fitting_loads) == Counter({body: 1 for body in chart["four_port_fittings"]}),
                    "exactly one own gravity load for every fitting required")
    return result


def current_contacts(bundle, field):
    descriptors = [r["descriptor"] for family in ["groups", "contacts", "tangents"]
                   for r in bundle["partitions"][family]]
    current.require(descriptors == field["reference_interaction_descriptors"]
                    and len({r["id"] for r in descriptors}) == len(descriptors)
                    and dict(Counter(r["kind"] for r in descriptors)) == CONTACT_COUNTS,
                    "exact current contact source identities and census required")
    enabled = [r for r in field["floor_actions"]
               if r["kind"] == "floor_tangent" and r["interaction_enabled"]]
    by_id = {r["id"]: r for r in descriptors}
    current.require(len(enabled) == 4 and Counter(r["first"] for r in enabled)
                    == Counter({"lumber_leg_left": 2, "lumber_leg_right": 2})
                    and all({tuple(by_id[r["id"]]["direction_xyz"]) for r in enabled if r["first"] == body}
                            == {(1., 0., 0.), (0., 1., 0.)} for body in ["lumber_leg_left", "lumber_leg_right"]),
                    "current two rear-leg centroid XY restraints required")
    return {"all_source_interaction_counts": CONTACT_COUNTS,
            "enabled_floor_tangent_ids": [r["id"] for r in enabled],
            "enabled_centroid_XY_groups": 2}


def roll_generator(nodes):
    """Common right material-roll generator in the shaft's stored local basis."""
    nodes = np.asarray(nodes, dtype=float)
    current.require(nodes.ndim == 2 and nodes.shape[1] == 6 and np.isfinite(nodes).all(),
                    "finite six-coordinate shaft nodes required")
    result = np.zeros_like(nodes)
    for i, theta in enumerate(nodes[:, 3:]/1000.):
        result[i, 3:] = 1000.*shaft.so3_left_jacobian_inverse(theta) @ shaft.so3_exp(theta)[:, 0]
    return result


def point_check(row, nodes, rolled, generator, point, force, couple, *, axial_extension=False):
    """Retain source precision offsets; reject torque or off-axis gauge work."""
    basis = shaft.check_rotation(np.asarray(row["basis"], dtype=float).T)
    start, point = shaft.vector(row["point"], 3), shaft.vector(point, 3)
    force, couple = shaft.vector(force, 3), shaft.vector(couple, 3)
    current.require(np.linalg.norm(couple) == 0., "shaft point couple requires a separately qualified rotation load law")
    stations = np.asarray(row["stations"], dtype=float)
    current.require(stations.ndim == 1 and len(stations) == len(nodes)
                    and np.isfinite(stations).all() and np.all(np.diff(stations) > 0),
                    "own strictly ordered current shaft stations required")
    axis = basis[:, 0]
    station = float((point-start) @ axis)
    current.require(stations[0]-1e-6 <= station <= stations[-1]+1e-6 or axial_extension,
                    "source point outside current shaft station domain")
    radial = float(np.linalg.norm(point-start-axis*station))
    i = int(np.clip(np.searchsorted(stations, station)-1, 0, len(stations)-2))
    t = float(np.clip((station-stations[i])/(stations[i+1]-stations[i]), 0., 1.))
    centers = start+stations[i:i+2, None]*axis
    state, changed, mode = nodes[i:i+2].ravel(), rolled[i:i+2].ravel(), generator[i:i+2].ravel()
    before, jacobian = shaft.mechanical.interpolated_point(point, centers, state, t, basis)
    after = shaft.mechanical.interpolated_point(point, centers, changed, t, basis)[0]
    director, director_j = shaft.mechanical.interpolated_director(axis, state, t, basis)
    changed_director = shaft.mechanical.interpolated_director(axis, changed, t, basis)[0]
    motion = float(np.linalg.norm(after-before))
    velocity = float(np.linalg.norm(jacobian @ mode))
    direction_error = max(float(np.linalg.norm(changed_director-director)),
                          float(np.linalg.norm(director_j @ mode)))
    work = float(force @ (jacobian @ mode))
    # These numerical gates accept only source-coordinate roundoff, not a
    # physical eccentricity allowance or a projection of a changed load.
    current.require(radial < 1e-8 and motion < 2e-9 and velocity < 2e-9
                    and direction_error < 2e-12 and abs(work) < 1e-5,
                    "current source violates on-axis point/axial-director gauge scope")
    return {"source_radial_offset_mm": radial, "roll_point_change_mm": motion,
            "endpoint_rigid_arm_axial_extension_mm": max(0., stations[0]-station, station-stations[-1]),
            "roll_point_velocity_mm_per_rad": velocity,
            "axial_director_roll_error": direction_error,
            "own_force_roll_virtual_work_nmm_per_rad": work}


def shaft_check(row, nodes, points, *, roll_rad=.37):
    """Current multi-element shaft elasticity and all its original source ports."""
    nodes = np.asarray(nodes, dtype=float)
    current.require(nodes.shape == (len(row["stations"]), 6) and np.isfinite(nodes).all()
                    and points and len({p["id"] for p in points}) == len(points),
                    "complete own shaft nodes and unique source ports required")
    rolled, generator = shaft.common_roll_local(nodes, roll_rad), roll_generator(nodes)
    metal_points = {tuple(r["center_of_mass_xyz_mm"]) for r in row.get("metal_roles", [])}
    current.require(all(p["kind"] != "own_metal_gravity" or tuple(p["point"]) in metal_points for p in points),
                    "own declared metal centroid required before endpoint rigid-arm extension")
    checks = [{"id": p["id"], "kind": p["kind"],
               **point_check(row, nodes, rolled, generator, p["point"], p["force"], p["couple"],
                             axial_extension=p["kind"] == "own_metal_gravity")}
              for p in points]
    basis = shaft.check_rotation(np.asarray(row["basis"], dtype=float).T)
    stations, start = np.asarray(row["stations"]), np.asarray(row["point"])
    original, changed, virtual_work = 0., 0., 0.
    for i in range(len(nodes)-1):
        centers = start+stations[i:i+2, None]*basis[:, 0]
        beam = shaft.IsotropicShaftBeam(centers, basis, row["diameter_mm"], 200000., 200000./2.6)
        state = (nodes[i:i+2].reshape(-1, 3) @ basis.T).ravel()
        altered = (rolled[i:i+2].reshape(-1, 3) @ basis.T).ravel()
        mode = (generator[i:i+2].reshape(-1, 3) @ basis.T).ravel()
        original += beam.energy(state)
        changed += beam.energy(altered)
        virtual_work += float(beam.residual(state) @ mode)
    energy_error = abs(changed-original)/max(abs(original), 1.)
    current.require(energy_error < 1e-10 and abs(virtual_work) < 1e-5,
                    "current declared circular-shaft energy/gauge work failed")
    return {"body": row["body"], "nodes": len(nodes), "source_ports": checks,
            "declared_energy_nmm": original, "scaled_energy_roll_error": energy_error,
            "internal_roll_virtual_work_nmm_per_rad": virtual_work,
            "sum_absolute_source_roll_work_nmm_per_rad": sum(abs(c["own_force_roll_virtual_work_nmm_per_rad"]) for c in checks)}


def owned_shaft_points(field):
    """Account for every current shaft load, bearing and end capture once."""
    result = {s["body"]: [] for s in field["source_inputs"]["shafts"]}
    for load in field["body_applied_loads"]:
        if load["body"] in result:
            result[load["body"]].append({"id": load["id"], "kind": "own_metal_gravity",
                "point": load["point_xyz_mm"], "force": load["force_xyz_n"],
                "couple": load.get("moment_xyz_nmm", [0., 0., 0.])})
    for action in field["common_shaft_bearing_actions"]+field["shaft_end_capture_actions"]:
        current.require(action["first"] in result and action["axis_id"] == action["first"].removeprefix("shaft/"),
                        "own shaft-side interaction required")
        result[action["first"]].append({"id": action["id"], "kind": action["kind"],
            "point": action["point_xyz_mm"], "force": action["force_on_first_xyz_n"],
            "couple": action["moment_on_first_at_point_xyz_nmm"]})
    current.require(Counter(p["kind"] for points in result.values() for p in points)
                    == Counter({"own_metal_gravity": 508, "common_shaft_bearing": 416, "shaft_end_capture": 200}),
                    "all 1124 current shaft source ports required")
    return result


def run():
    own_ref()
    current.require(current.ref(intake_source.OWN) == INTAKE, "exact authenticated intake helper required")
    cases, pins = intake_source.intake()
    method = component.load(PARTITION, "current_finite_source_partition")
    pins = current.join(pins, method.source_pins(), shaft.source_pins(),
                        {r["path"]: r["sha256"] for r in [INTAKE, PARTITION, SHAFT, own_ref(), current.ref(current.ROOT/"uv.lock")]})
    current.verify(pins)
    results = []
    for binding, field, _ in cases:
        bundle_ref = field["operator_bundle"]["manifest"]
        current.require(pins.get(bundle_ref["path"]) == bundle_ref["sha256"], "current operator manifest must be in authenticated source union")
        bundle = current.read(bundle_ref)
        current.require(bundle["original_operator_fingerprint_sha256"] == field["original_operator_fingerprint_sha256"]
                        and bundle["case"]["loads"] == field["body_applied_loads"], "own operator/load identity required")
        chart, old_q = bundle["coordinate_map"], np.asarray(field["response"]["q"], dtype=float)
        current.require(old_q.shape == (9350,) and canonical_sha(old_q.tolist()) == field["response"]["q_canonical_sha256"],
                        "exact current saved first-order diagnostic state required")
        split = current_partition(method, chart, bundle["case"]["loads"], field["source_inputs"]["shafts"])
        contacts = current_contacts(bundle, field)
        points = owned_shaft_points(field)
        rows = []
        for source in field["source_inputs"]["shafts"]:
            body = source["body"]
            row = {**chart["shafts"][body], "body": body, "metal_roles": source["metal_roles"]}
            indices = np.asarray(row["index"])
            nodes = np.zeros(indices.shape)
            nodes[indices >= 0] = old_q[indices[indices >= 0]]
            rows.append(shaft_check(row, nodes, points[body]))
        results.append({"case_id": binding["case_id"], "state_id": binding["state_id"],
                        "field": binding["field"], "operator_manifest": bundle_ref,
                        "coordinate_ownership": split, "contacts": contacts, "shafts": rows})
    current.verify(pins)
    return {"schema": "eoere_current_finite_ownership_and_shaft_gauge/v1", "producer": own_ref(),
            "source_sha256": pins, "all_sources_unchanged": True, "case_sequence": SEQUENCE,
            "geometry_revision": "eoere-raised-kicker-screws-v1", "hardware_revision": "eoere-selected-purchase-hardware-v1",
            "extra_grid": False, "cases": results, "roll_angle_rad": .37,
            "saved_first_order_q_is_only_a_diagnostic_initial_pose": True,
            "omitted_first_spin_restored_as_zero_initial_pose_not_a_finite_gauge_representative": True,
            "source_points_projected_or_physical_torque_constraints_added": 0,
            "scope": "Current ownership, exact load/contact census and circular-shaft symmetry at the six saved diagnostic poses; current material ports only.",
            "shaft_elastic_scenario": {"E_mpa": 200000., "nu": .3, "shear_factor": .9,
                "nominal_diameter": True, "measured_or_conservative_physical_stiffness_bound": False},
            "finite_frame_potential_or_equilibrium_or_native_solver_run": False,
            "remaining": ["Current 22-timber closed-solid contact domains, full slave-face measures and feature/inverse-map qualification.",
                          "Current four-port fitting, panel, floor and timber/shaft laws composed exactly once with their own gravity and full signed residual/work recovery.",
                          "Physical stiffness/contact demand applicability, movement criteria, joint/member resistance and stability."],
            "structural_acceptance": False, "release": current.manifest()["release"]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    with current.load("bridge").reserve(args.out) as output:
        output.write(run())
    print(json.dumps(current.ref(args.out)))


if __name__ == "__main__":
    main()
