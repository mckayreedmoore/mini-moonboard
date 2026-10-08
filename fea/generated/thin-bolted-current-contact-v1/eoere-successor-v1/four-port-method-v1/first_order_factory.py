"""Fresh successor reference-geometry assembly from reviewed source rows only.

This reuses the frozen timber/panel/common-shaft kernels and guarded four-port
element. It neither imports CAD nor fills missing candidate contact geometry.
"""
from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace

import numpy as np
from scipy.sparse import coo_matrix, csr_matrix, hstack, vstack

from scripts import thin_bolted_common_shaft as common
from scripts import thin_bolted_frame_mechanics as frame

OWN = Path(__file__).resolve()
GUARDED = OWN.with_name("guarded_assembly_interface.py")
GUARDED_SHA = "a2b5ef4f45d05f3a29c428583238c3ead927ac7ae259a6c4a8d7c63ded3d0ad8"
LOADED_SHA = frame.sha(OWN)
SPEC = importlib.util.spec_from_file_location("eoere_guarded_for_factory", GUARDED)
guarded = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(guarded)
SCHEMA = "eoere_first_order_mechanics_inputs/v1"
require = guarded.four.require
PRIMITIVES = {
    "scripts/thin_bolted_frame_mechanics.py": "05cdf6897645fe7ee1b72b5b5125c04c68d758108f4860f995cef6aa1b676448",
    "scripts/thin_bolted_common_shaft.py": "0ff8c52a36f168cba0bd3fed2d592daa9e5d9de5facbc650b151f64c2f23f4eb",
    "scripts/thin_bolted_panel_mechanics.py": "472eef63a8af59367533028008c68e4f7e32780e49891499154ba2950559a3aa",
}


def canonical(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()).hexdigest()


def source_pins(extra=None):
    pins = {**guarded.source_pins(), **PRIMITIVES, str(OWN.relative_to(frame.ROOT)): LOADED_SHA}
    frame_hashes = {str(GUARDED.relative_to(frame.ROOT)): GUARDED_SHA}
    for path, digest in {**frame_hashes, **(extra or {})}.items():
        require(path not in pins or pins[path] == digest, "source hash join conflict")
        pins[path] = digest
    require(all(frame.sha(frame.ROOT / path) == digest for path, digest in pins.items()), "assembly source bytes changed")
    return pins


def validate_contact_coefficients(rows):
    """Declared area priors, not a transferred corner or pressure stiffness."""
    for row in rows:
        area = row["reference_area_mm2"]
        require(np.isfinite(area) and area > 0., "positive source contact area required")
        if row["kind"] == "flange_contact":
            nominal = row["nominal_full_holed_flange_area_mm2"]
            require(np.isfinite(nominal) and nominal > 0., "source nominal holed flange area required")
            expected_k = 40000.*area/nominal
        else:
            require(row["kind"] in {"timber_face_contact", "panel_contact"}, "unknown first-order contact kind")
            density = 1. if row["kind"] == "timber_face_contact" else 2.
            require(row["bedding_n_mm3"] == density, "separate timber1/panel2 prior differs")
            expected_k = density*area
        require(row["stiffness"] is not None and np.isfinite(row["stiffness"])
                and abs(row["stiffness"]-expected_k) <= 32*np.finfo(float).eps*expected_k,
                "source area-weighted contact coefficient differs from declared scenario")


def validate_rows(data, *, synthetic=False):
    require(data["schema"] == SCHEMA and not data.get("missing_dependencies"), "complete successor source rows required")
    require(data.get("historical_q") is None and data.get("old_field") is None,
                  "predecessor coefficients or force fields prohibited")
    wood = [row["name"] for row in data["timber_rows"]]
    fittings = [row["id"] for row in data["fitting_poses"]]
    panels = data["panel_ids"]
    shafts = [row["body"] for row in data["shafts"]]
    owners = [*wood, *fittings, *panels, *shafts]
    require(len(set(owners)) == len(owners), "physical body identities overlap")
    base_ids = [row["id"] for row in data["base_bodies"]]
    require(len(base_ids) == len(set(base_ids)) and set(base_ids) == set(wood+fittings+panels),
                  "exact timber/fitting/panel base ownership required; shafts added once")
    if synthetic:
        require(0 < len(wood) <= 2 and 0 < len(fittings) <= 2 and len(panels) <= 2 and len(shafts) <= 2,
                      "synthetic escape is limited to tiny fixtures")
    else:
        require((len(wood), len(fittings), len(shafts), len(panels), len(owners)) == (22, 22, 100, 6, 150),
                      "fresh successor150-body census required")
        require(len(data["hillman_rows"]) == 66 and len(data["floor_footprints"]) == 8,
                      "exact66 Hillman axes and8 physical feet required")
        require(len(data["factory_holes"]) == 176 and sum(row["used"] for row in data["factory_holes"]) == 88,
                      "all176 own factory holes/88 used attachments required")
    require(data["scenario"]["timber_stiffness_basis"] == "declared-gross-stock-Timoshenko",
                  "changed-hole predecessor section stiffness may not transfer")
    require(data["scenario"]["fitting_gravity_route"] == guarded.ROUTE,
                  "explicit source centroid collector gravity route required")
    require(data["scenario"]["floor_kn_n_mm"] == 25000.
                  and data["scenario"]["floor_kt_n_mm"] == 100000.
                  and data["scenario"]["floor_activation_threshold_n"] == 1e-7,
                  "original whole-foot centroid floor law required")
    axis_ids = [row["axis_id"] for row in data["shafts"]]
    require(len(axis_ids) == len(set(axis_ids)), "one continuous shaft per unique physical axis")
    roles = [role for row in data["shafts"] for role in row["metal_roles"]]
    role_ids = [row["id"] for row in roles]
    require(len(role_ids) == len(set(role_ids)), "nominal metal role assigned to multiple shafts")
    if not synthetic:
        require(len(role_ids) == 500 and all(len(row["metal_roles"]) == 5 for row in data["shafts"]),
                "all500 nominal metal roles on100 physical shafts required")
        require(len(data["fitting_port_bindings"]) == 88
                and len({(row["angle_id"], row["model_port_id"]) for row in data["fitting_port_bindings"]}) == 88,
                "all88 distinct fitting ports must bind physical shafts once")
    require(data["scenario"]["metal_density_kg_mm3"] == 7850e-9,
            "source gravity density must match reused own-shaft body mass scenario")
    for shaft in data["shafts"]:
        for surface in shaft["surfaces"]:
            require(surface["bore_diameter_mm"] >= shaft["diameter_mm"]
                    and np.isfinite(surface["bore_diameter_mm"]), "finite nonnegative own surface gap required")
    loads = data["case"]["loads"]
    require(len({row["id"] for row in loads}) == len(loads)
                  and all(row["body"] in owners for row in loads), "physical load identity/owner missing or duplicated")
    shaft_role_loads = {"physical-bolt-metal/"+role["id"]: (shaft["body"], role)
                        for shaft in data["shafts"] for role in shaft["metal_roles"]}
    actual_roles = {row["id"]: row for row in loads if row["body"] in shafts}
    require(set(actual_roles) == set(shaft_role_loads), "all own shaft roles required once; no duplicated shaft selfweight")
    for load_id, (body, role) in shaft_role_loads.items():
        row = actual_roles[load_id]
        expected = [0., 0., -role["volume_mm3"]*data["scenario"]["metal_density_kg_mm3"]*frame.GRAVITY]
        require(row["body"] == body and row["point_xyz_mm"] == role["center_of_mass_xyz_mm"]
                      and np.allclose(row["force_xyz_n"], expected, rtol=0., atol=1e-12), "own role gravity differs")
    by_load = {row["id"]: row for row in loads}
    for body in data["base_bodies"]:
        own = by_load.get("self-weight/"+body["id"])
        require(own is not None and own["body"] == body["id"] and own["point_xyz_mm"] == body["center_xyz_mm"]
                and np.allclose(own["force_xyz_n"], [0., 0., -body["mass_kg"]*frame.GRAVITY], rtol=0., atol=1e-12),
                "own base-body centroid gravity missing or inconsistent")
    for host, points in data["floor_footprints"].items():
        tolerance = data["scenario"].get("floor_reference_plane_numerical_tolerance_mm", 1e-6)
        require(np.isfinite(tolerance) and 0. <= tolerance <= 1e-6, "bounded declared numerical floor-plane tolerance required")
        require(host in wood and np.asarray(points).shape == (4, 3)
                and np.isfinite(points).all() and np.max(abs(np.asarray(points)[:, 2])) <= tolerance,
                "four actual level-plane normal corners on own timber host required; no snapping")
    require(all(np.array_equal(row.get("moment_xyz_nmm", [0., 0., 0.]), np.zeros(3)) for row in loads),
                  "this load factory accepts physical point forces only")
    if not synthetic:
        validate_contact_coefficients(data["direct_contacts"])
    return {"timber": len(wood), "fitting": len(fittings), "shaft": len(shafts), "panel": len(panels), "physical_bodies": len(owners)}


def authenticate_source_review(record, data, pins):
    """Bind outer review without mutating immutable extraction readiness flags."""
    require(record is not None, "independent successor source-input review required before preparation")
    path = frame.ROOT/record["path"]
    require(frame.sha(path) == record["sha256"], "source-input review bytes differ")
    review = json.loads(path.read_bytes())
    require(review["schema"] == "eoere_first_order_mechanics_inputs_independent_review/v1"
            and review["success"] == "independent_eoere_successor_source_input_checks_pass"
            and review["complete_reference_contact_inventory"] is True, "source-input review did not pass complete joins")
    source = review["input"]
    raw_path = frame.ROOT/source["path"]
    require(pins.get(source["path"]) == source["sha256"] and frame.sha(raw_path) == source["sha256"]
            and review["source_sha256"].get(source["path"]) == source["sha256"]
            and canonical(json.loads(raw_path.read_bytes())) == canonical(data), "reviewed immutable input differs from prepared rows")
    joined = source_pins({**pins, **review["source_sha256"], record["path"]: record["sha256"]})
    return joined, {**record, "input": copy.deepcopy(source), "inputs_canonical_sha256": canonical(data)}


def read_inputs(path, expected_sha256):
    path = Path(path).resolve()
    require(frame.sha(path) == expected_sha256, "successor inputs raw SHA differs")
    data = json.loads(path.read_bytes())
    validate_rows(data)
    pins = source_pins(data["source_sha256"])
    pins[str(path.relative_to(frame.ROOT))] = expected_sha256
    for key in ("report", "scene"):
        record = data["geometry"][key]
        require(pins.get(record["path"]) == record["sha256"], "final geometry/source join missing")
    return data, pins


def prepare(data, panels, integrated, *, source_sha256, source_review=None):
    validate_rows(data)
    pins, review = authenticate_source_review(source_review, data, source_pins(source_sha256))
    result = _prepare(data, panels, integrated, pins, synthetic=False)
    result.source_review = review
    return result


def prepare_synthetic(data, panels, integrated):
    validate_rows(data, synthetic=True)
    return _prepare(data, panels, integrated, source_pins(), synthetic=True)


def _prepare(data, panels, integrated, pins, *, synthetic):
    counts = validate_rows(data, synthetic=synthetic)
    require(set(panels) == set(data["panel_ids"]), "panel operators must match source physical owners")
    scenario = data["scenario"]
    geo = {"members": copy.deepcopy(data["timber_rows"]), "bodies": copy.deepcopy(data["base_bodies"]),
           "floor_footprints": copy.deepcopy(data["floor_footprints"])}
    assembly = frame.ElasticAssembly({"raw_fittings": []}, geo, panels,
        beam_size=scenario["beam_size_mm"], timber_e=scenario["timber_e_mpa"], shear_ratio=scenario["timber_shear_ratio"])
    original_port, original_rigid = assembly.port, assembly.rigid_modes
    elements, blocks = {}, []
    for pose in data["fitting_poses"]:
        model, bindings = guarded.model_from_reference_pose(pose["origin_xyz_mm"], pose["u_xyz"], pose["v_xyz"], pose["w_xyz"])
        indices = np.arange(assembly.ndof, assembly.ndof+24)
        assembly.ndof += 24
        elements[pose["id"]] = (model, indices, bindings)
        blocks.append((indices, model.condensed_matrix(rotation_scale=frame.ROTATION_SCALE)))
    extra = assembly.ndof-assembly.K.shape[0]
    assembly.K = vstack([hstack([assembly.K, csr_matrix((assembly.K.shape[0], extra))]),
                         csr_matrix((extra, assembly.ndof))], format="csr")
    for indices, block in blocks:
        i, j = np.nonzero(block)
        assembly.K += coo_matrix((block[i, j], (indices[i], indices[j])), shape=assembly.K.shape).tocsr()
    fitting_elements = {body: guarded.GuardedFourPortAssemblyElement(model, body, indices, assembly.ndof)
                        for body, (model, indices, _) in elements.items()}

    def fitting_port(body, point, flange=None):
        if body not in fitting_elements:
            return original_port(body, point, flange)
        el = fitting_elements[body]
        port = (el.centroid_load_port(point, declared_route=guarded.ROUTE) if flange is None else el.point_port(flange, point))
        return hstack([port, csr_matrix((3, assembly.ndof-port.shape[1]))], format="csr")

    def fitting_rigid():
        result = original_rigid()
        for el in fitting_elements.values():
            result[el.indices] = el.rigid_modes(frame.REFERENCE)
        return result

    assembly.port, assembly.rigid_modes = fitting_port, fitting_rigid
    shaft_rows = copy.deepcopy(data["shafts"])
    for row in shaft_rows:
        row["point"], row["basis"] = np.asarray(row["point"]), np.asarray(row["basis"])
    system = common.CommonShaftSystem(assembly, shaft_rows, **scenario["common_shaft_parameters"])
    # Successor wood bores and factory steel holes have different diameters.
    # The frozen constructor's one-row diameter is not gap authority here.
    for group in system.bearing_groups:
        diameter = system.shafts[group["first"]]["diameter_mm"]
        group["clearance"] = .5*(group["surface"]["bore_diameter_mm"]-diameter)
        group["own_surface_bore_diameter_mm"] = group["surface"]["bore_diameter_mm"]
    case = copy.deepcopy(data["case"])
    total = sum((frame.wrench(row["force_xyz_n"], row["point_xyz_mm"]) for row in case["loads"]), np.zeros(6))
    case.update(applied_force_xyz_n=total[:3].tolist(), applied_moment_about_global_origin_xyz_nmm=total[3:].tolist())
    applied = frame.coupled_load_vector(assembly, case, integrated)
    rigid = assembly.rigid_modes()
    source_wrench = sum((frame.wrench(row["force_xyz_n"], row["point_xyz_mm"], frame.REFERENCE)
                        for row in case["loads"]), np.zeros(6))
    error = rigid.T @ applied-source_wrench
    require(np.linalg.norm(error[:3]) < 1e-8 and np.linalg.norm(error[3:]) < 1e-5,
                  "full source applied wrench differs from work-conjugate RHS")
    groups = copy.deepcopy(data["hillman_rows"])
    for row in groups:
        row.update(kind="panel_screw", axis_id=row["id"])
        row["basis"] = np.asarray(row["basis"])
        row["B"] = csr_matrix(row["basis"]) @ (assembly.port(row["first"], row["point_xyz_mm"])-
                                                assembly.port(row["second"], row["point_xyz_mm"]))
    contacts = []
    for source in data["direct_contacts"]:
        row = copy.deepcopy(source)
        normal = np.asarray(row["direction_xyz"])
        require(abs(np.linalg.norm(normal)-1.) < 1e-8 and row["stiffness"] > 0., "unit director/positive contact prior required")
        for side in ("first", "second"):
            if row[side] in fitting_elements:
                require(row.get(side+"_port_id") in {p["id"] for p in fitting_elements[row[side]].model.port_manifest},
                              "surface contact needs exact own fitting strip, never collector average")
        row["B"] = -csr_matrix(normal[None, :]) @ (assembly.port(row["first"], row["point_xyz_mm"], row.get("first_port_id"))-
                     assembly.port(row["second"], row["point_xyz_mm"], row.get("second_port_id")))
        if row["kind"] == "flange_contact":
            row.update(angle_id=row["first"], flange=row["first_port_id"])
        contacts.append(row)
    tangents = []
    for host, points in data["floor_footprints"].items():
        for i, point in enumerate(points):
            contacts.append({"id": host+f"/floor-{i}", "kind": "floor_normal", "first": host, "second": "floor",
                "point_xyz_mm": point, "direction_xyz": [0., 0., 1.], "stiffness": 25000.,
                "B": -assembly.scalar_port(host, point, [0., 0., 1.])})
        centroid = np.mean(points, axis=0).tolist()
        for i in (0, 1):
            direction = np.eye(3)[i]
            tangents.append({"id": host+f"/no-slip-{i}", "kind": "floor_tangent", "first": host,
                "point_xyz_mm": centroid, "direction_xyz": direction.tolist(), "stiffness": 100000.,
                "B": assembly.scalar_port(host, centroid, direction)})
    groups.extend(system.bearing_groups)
    contacts.extend(system.end_captures)
    ids = [row["id"] for row in [*groups, *contacts, *tangents]]
    require(len(ids) == len(set(ids)), "physical interaction ID duplicated")
    require(len(assembly.geo["bodies"]) == counts["physical_bodies"], "actual assembly physical-owner count differs")
    source_pins(pins)
    return SimpleNamespace(assembly=assembly, system=system, fittings=fitting_elements, case=case, applied=applied,
        groups=groups, contacts=contacts, tangents=tangents, source_sha256=pins, source_inputs=copy.deepcopy(data),
        counts={**counts, "dofs": assembly.ndof, "bearings": len(system.bearing_groups), "end_captures": len(system.end_captures),
                "contacts": len(contacts), "floor_normals": 4*len(data["floor_footprints"]), "floor_xy_components": len(tangents)},
        applied_wrench_work_error_n_nmm=error.tolist(), synthetic_only=synthetic)
